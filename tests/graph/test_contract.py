from __future__ import annotations

from copilot_sdk.graph import EdgeType, GraphContract, NodeType


def _clean_contract() -> GraphContract:
    return GraphContract(
        graph_name="demo_graph",
        node_types=[
            NodeType("Decision", ["decision_id"]),
            NodeType("Entity", ["entity_id"]),
        ],
        edge_types=[EdgeType("DECIDED_ON", "Decision", "Entity")],
    )


def test_graph_contract_validate_clean_contract():
    assert _clean_contract().validate() == []


def test_graph_contract_missing_from_label():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Decision", ["decision_id"]), NodeType("Entity", ["entity_id"])],
        edge_types=[EdgeType("DECIDED_ON", "Missing", "Entity")],
    )

    assert "unknown from_label: Missing" in " ".join(contract.validate())


def test_graph_contract_missing_to_label():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Decision", ["decision_id"]), NodeType("Entity", ["entity_id"])],
        edge_types=[EdgeType("DECIDED_ON", "Decision", "Missing")],
    )

    assert "unknown to_label: Missing" in " ".join(contract.validate())


def test_graph_contract_duplicate_node_label():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Decision", ["decision_id"]), NodeType("Decision", ["id"])],
        edge_types=[EdgeType("DECIDED_ON", "Decision", "Decision")],
    )

    assert "duplicate node label: Decision" in contract.validate()


def test_graph_contract_duplicate_edge_triple():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Decision", ["decision_id"]), NodeType("Entity", ["entity_id"])],
        edge_types=[
            EdgeType("DECIDED_ON", "Decision", "Entity"),
            EdgeType("DECIDED_ON", "Decision", "Entity"),
        ],
    )

    assert "duplicate edge triple: DECIDED_ON/Decision/Entity" in contract.validate()


def test_graph_contract_missing_graph_name():
    contract = _clean_contract()
    contract.graph_name = " "

    assert "graph_name must be non-empty" in contract.validate()


def test_graph_contract_missing_decision_node():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Entity", ["entity_id"])],
        edge_types=[EdgeType("DECIDED_ON", "Entity", "Entity")],
    )

    assert "required node label missing: Decision" in contract.validate()


def test_graph_contract_missing_decided_on_edge():
    contract = GraphContract(
        graph_name="demo_graph",
        node_types=[NodeType("Decision", ["decision_id"]), NodeType("Entity", ["entity_id"])],
        edge_types=[EdgeType("RELATED_TO", "Decision", "Entity")],
    )

    assert "required edge label missing: DECIDED_ON" in contract.validate()


def test_node_type_fields():
    node = NodeType("Decision", ["decision_id"], description="Decision node")

    assert node.label == "Decision"
    assert node.properties == ["decision_id"]
    assert node.description == "Decision node"


def test_edge_type_fields():
    edge = EdgeType("DECIDED_ON", "Decision", "Entity", ["source"], "Decision target")

    assert edge.label == "DECIDED_ON"
    assert edge.from_label == "Decision"
    assert edge.to_label == "Entity"
    assert edge.properties == ["source"]
    assert edge.description == "Decision target"


def test_graph_contract_counts():
    contract = _clean_contract()

    assert contract.node_count == 2
    assert contract.edge_count == 1


def test_empty_contract_invalid():
    errors = GraphContract("", [], []).validate()

    assert "graph_name must be non-empty" in errors
    assert "required node label missing: Decision" in errors
    assert "required edge label missing: DECIDED_ON" in errors


def test_contract_exports_from_graph_package():
    assert GraphContract.__name__ == "GraphContract"
    assert NodeType.__name__ == "NodeType"
    assert EdgeType.__name__ == "EdgeType"
