from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from copilot_sdk.graph import EdgeType, GraphContract, NodeType


REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAINS = {
    "trading": {
        "backend_path": REPO_ROOT / "apps" / "trading" / "backend",
        "contract_path": REPO_ROOT / "apps" / "trading" / "backend" / "app" / "graph_contract.py",
        "seed_path": REPO_ROOT / "apps" / "trading" / "backend" / "app" / "seed_graph.py",
        "contract_name": "TRADING_GRAPH_CONTRACT",
        "seed_name": "seed_trading_graph",
    },
    "purchasing": {
        "backend_path": REPO_ROOT / "apps" / "purchasing" / "backend",
        "contract_path": REPO_ROOT / "apps" / "purchasing" / "backend" / "app" / "graph_contract.py",
        "seed_path": REPO_ROOT / "apps" / "purchasing" / "backend" / "app" / "seed_graph.py",
        "contract_name": "PURCHASING_GRAPH_CONTRACT",
        "seed_name": "seed_purchasing_graph",
    },
    "dataops": {
        "backend_path": REPO_ROOT / "apps" / "dataops" / "backend",
        "contract_path": REPO_ROOT / "apps" / "dataops" / "backend" / "app" / "graph_contract.py",
        "seed_path": REPO_ROOT / "apps" / "dataops" / "backend" / "app" / "seed_graph.py",
        "contract_name": "DATAOPS_GRAPH_CONTRACT",
        "seed_name": "seed_dataops_graph",
    },
}

# The app backend suites expose a top-level `app` package and should be run as
# separate pytest invocations. These cross-domain tests intentionally use
# file-path imports, plus a subprocess guard below, to avoid `sys.modules["app"]`
# collisions in the shared SDK test process.
FORBIDDEN = {
    "credential" + "_access",
    "lateral" + "_movement",
    "threat" + "_intel",
    "insider" + "_threat",
    "data" + "_exfiltration",
    "cloud" + "_infrastructure",
    "refer" + "_to" + "_analyst",
}


def _load_module(name: str, path: Path) -> ModuleType:
    original_sys_path = list(sys.path)
    original_app_module = sys.modules.get("app")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert sys.path == original_sys_path
    assert sys.modules.get("app") is original_app_module
    return module


def _contracts() -> dict[str, GraphContract]:
    contracts: dict[str, GraphContract] = {}
    for domain, info in DOMAINS.items():
        module = _load_module(f"graph_tpc_{domain}_contract", info["contract_path"])
        contracts[domain] = getattr(module, info["contract_name"])
    return contracts


def _seeds() -> dict[str, tuple[list[dict], list[dict]]]:
    seeds: dict[str, tuple[list[dict], list[dict]]] = {}
    for domain, info in DOMAINS.items():
        module = _load_module(f"graph_tpc_{domain}_seed", info["seed_path"])
        seeds[domain] = getattr(module, info["seed_name"])()
    return seeds


def test_contract_protocol_importable_from_graph_package():
    assert GraphContract.__name__ == "GraphContract"
    assert NodeType.__name__ == "NodeType"
    assert EdgeType.__name__ == "EdgeType"


def test_all_contract_names_unique():
    graph_names = [contract.graph_name for contract in _contracts().values()]

    assert len(graph_names) == len(set(graph_names))


def test_all_contracts_validate():
    for contract in _contracts().values():
        assert contract.validate() == []


def test_all_contracts_have_decision_and_decided_on():
    for contract in _contracts().values():
        assert any(node.label == "Decision" for node in contract.node_types)
        assert any(edge.label == "DECIDED_ON" for edge in contract.edge_types)


def test_no_forbidden_vocabulary_in_contracts_or_seeds():
    payload = json.dumps(
        {
            "contracts": {
                domain: {
                    "nodes": [node.label for node in contract.node_types],
                    "edges": [edge.label for edge in contract.edge_types],
                }
                for domain, contract in _contracts().items()
            },
            "seeds": _seeds(),
        },
        sort_keys=True,
    ).lower()

    assert not any(term in payload for term in FORBIDDEN)


def test_all_seeds_deterministic():
    for domain, info in DOMAINS.items():
        module = _load_module(f"graph_tpc_{domain}_seed_determinism", info["seed_path"])
        seed_fn = getattr(module, info["seed_name"])

        assert seed_fn(seed=42) == seed_fn(seed=42)


def test_all_seed_edges_reference_seeded_node_ids():
    for nodes, edges in _seeds().values():
        node_ids = {node["id"] for node in nodes}
        assert node_ids
        for edge in edges:
            assert edge["from_id"] in node_ids
            assert edge["to_id"] in node_ids


def test_all_seed_outputs_cover_contract_labels():
    contracts = _contracts()
    seeds = _seeds()
    for domain, contract in contracts.items():
        nodes, edges = seeds[domain]
        assert {node.label for node in contract.node_types} <= {node["label"] for node in nodes}
        assert {edge.label for edge in contract.edge_types} <= {edge["label"] for edge in edges}


def test_app_package_imports_work_in_domain_isolated_subprocesses():
    script = r"""
import importlib
import sys
from pathlib import Path

backend = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
contract_name = sys.argv[3]
seed_name = sys.argv[4]
domain = sys.argv[5]

sys.path = [str(backend), str(repo_root)] + [
    path for path in sys.path if path not in {str(backend), str(repo_root)}
]
contract_module = importlib.import_module("app.graph_contract")
seed_module = importlib.import_module("app.seed_graph")
contract = getattr(contract_module, contract_name)
errors = contract.validate()
assert errors == [], errors
nodes, edges = getattr(seed_module, seed_name)(seed=42)
assert isinstance(nodes, list)
assert isinstance(edges, list)
assert len(nodes) > 0
assert len(edges) > 0
print(f"OK:{domain}")
"""
    for domain, info in DOMAINS.items():
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(info["backend_path"]),
                str(REPO_ROOT),
                info["contract_name"],
                info["seed_name"],
                domain,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"{domain} subprocess import failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert f"OK:{domain}" in result.stdout
