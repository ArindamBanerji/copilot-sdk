from __future__ import annotations

import json

from app.graph_contract import PURCHASING_GRAPH_CONTRACT
from app.seed_graph import seed_purchasing_graph


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


def test_purchasing_contract_validates_cleanly():
    assert PURCHASING_GRAPH_CONTRACT.validate() == []


def test_purchasing_contract_required_decision_and_edge():
    assert any(node.label == "Decision" for node in PURCHASING_GRAPH_CONTRACT.node_types)
    assert any(edge.label == "DECIDED_ON" for edge in PURCHASING_GRAPH_CONTRACT.edge_types)


def test_purchasing_contract_graph_name():
    assert PURCHASING_GRAPH_CONTRACT.graph_name == "purchasing_graph"


def test_purchasing_seed_returns_lists_and_is_deterministic():
    first = seed_purchasing_graph(seed=42)
    second = seed_purchasing_graph(seed=42)

    assert isinstance(first[0], list)
    assert isinstance(first[1], list)
    assert first == second


def test_purchasing_seed_integrity():
    nodes, edges = seed_purchasing_graph()

    _assert_seed_integrity(nodes, edges)


def test_purchasing_seed_includes_all_contract_labels():
    nodes, edges = seed_purchasing_graph()

    assert {node.label for node in PURCHASING_GRAPH_CONTRACT.node_types} <= {node["label"] for node in nodes}
    assert {edge.label for edge in PURCHASING_GRAPH_CONTRACT.edge_types} <= {edge["label"] for edge in edges}


def test_purchasing_seed_has_no_forbidden_vocabulary():
    payload = json.dumps(
        {
            "contract_nodes": [node.label for node in PURCHASING_GRAPH_CONTRACT.node_types],
            "contract_edges": [edge.label for edge in PURCHASING_GRAPH_CONTRACT.edge_types],
            "seed": seed_purchasing_graph(),
        },
        sort_keys=True,
    ).lower()

    assert not any(term in payload for term in FORBIDDEN)
