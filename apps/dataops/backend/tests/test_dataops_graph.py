from __future__ import annotations

import json
from pathlib import Path

from app.graph_contract import DATAOPS_GRAPH_CONTRACT
from app.seed_graph import DATA_DIR, seed_dataops_graph


FORBIDDEN = {
    "credential" + "_access",
    "lateral" + "_movement",
    "threat" + "_intel",
    "insider" + "_threat",
    "data" + "_exfiltration",
    "cloud" + "_infrastructure",
    "refer" + "_to" + "_analyst",
}


def _assert_seed_integrity(nodes, edges):
    node_ids = {node["id"] for node in nodes}
    for node in nodes:
        assert node["label"]
        assert isinstance(node["properties"], dict)
    for edge in edges:
        assert edge["label"]
        assert edge["from_id"] in node_ids
        assert edge["to_id"] in node_ids
        assert isinstance(edge.get("properties", {}), dict)


def test_dataops_contract_validates_cleanly():
    assert DATAOPS_GRAPH_CONTRACT.validate() == []


def test_dataops_contract_required_decision_and_edge():
    assert any(node.label == "Decision" for node in DATAOPS_GRAPH_CONTRACT.node_types)
    assert any(edge.label == "DECIDED_ON" for edge in DATAOPS_GRAPH_CONTRACT.edge_types)


def test_dataops_contract_graph_name():
    assert DATAOPS_GRAPH_CONTRACT.graph_name == "dataops_graph"


def test_dataops_contract_process_labels():
    assert any(node.label == "ProcessModel" for node in DATAOPS_GRAPH_CONTRACT.node_types)
    assert any(node.label == "Activity" for node in DATAOPS_GRAPH_CONTRACT.node_types)


def test_dataops_seed_returns_lists_and_is_deterministic():
    first = seed_dataops_graph(seed=42)
    second = seed_dataops_graph(seed=42)

    assert isinstance(first[0], list)
    assert isinstance(first[1], list)
    assert first == second


def test_dataops_seed_integrity():
    nodes, edges = seed_dataops_graph()

    _assert_seed_integrity(nodes, edges)


def test_dataops_seed_includes_all_contract_labels():
    nodes, edges = seed_dataops_graph()

    assert {node.label for node in DATAOPS_GRAPH_CONTRACT.node_types} <= {node["label"] for node in nodes}
    assert {edge.label for edge in DATAOPS_GRAPH_CONTRACT.edge_types} <= {edge["label"] for edge in edges}


def test_dataops_seed_uses_celonis_process_data():
    nodes, edges = seed_dataops_graph()
    celonis = json.loads((Path(DATA_DIR) / "celonis_process_data.json").read_text(encoding="utf-8"))
    process_nodes = [node for node in nodes if node["label"] == "ProcessModel"]
    activity_nodes = [node for node in nodes if node["label"] == "Activity"]
    activity_names = {node["properties"].get("name") for node in activity_nodes}

    assert process_nodes
    assert process_nodes[0]["properties"]["name"] == celonis["process_model"]
    assert activity_names >= {activity["name"] for activity in celonis["activities"]}
    assert any(node["properties"].get("bottleneck") is True for node in activity_nodes)
    assert any(edge["label"] == "CONTAINS" for edge in edges)
    assert any(edge["label"] == "FOLLOWS" for edge in edges)


def test_dataops_seed_has_no_forbidden_vocabulary():
    payload = json.dumps(
        {
            "contract_nodes": [node.label for node in DATAOPS_GRAPH_CONTRACT.node_types],
            "contract_edges": [edge.label for edge in DATAOPS_GRAPH_CONTRACT.edge_types],
            "seed": seed_dataops_graph(),
        },
        sort_keys=True,
    ).lower()

    assert not any(term in payload for term in FORBIDDEN)
