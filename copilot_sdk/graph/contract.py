"""Domain graph contract dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NodeType:
    label: str
    properties: list[str]
    description: str = ""


@dataclass
class EdgeType:
    label: str
    from_label: str
    to_label: str
    properties: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class GraphContract:
    graph_name: str
    node_types: list[NodeType]
    edge_types: list[EdgeType]
    expected_nodes: int = 0
    expected_edges: int = 0

    @property
    def node_count(self) -> int:
        return len(self.node_types)

    @property
    def edge_count(self) -> int:
        return len(self.edge_types)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.graph_name.strip():
            errors.append("graph_name must be non-empty")

        labels = [node.label for node in self.node_types]
        label_set = set(labels)
        for label in sorted({label for label in labels if labels.count(label) > 1}):
            errors.append(f"duplicate node label: {label}")

        if "Decision" not in label_set:
            errors.append("required node label missing: Decision")

        edge_triples = [
            (edge.label, edge.from_label, edge.to_label)
            for edge in self.edge_types
        ]
        for label, from_label, to_label in sorted(
            {triple for triple in edge_triples if edge_triples.count(triple) > 1}
        ):
            errors.append(
                f"duplicate edge triple: {label}/{from_label}/{to_label}"
            )

        if not any(edge.label == "DECIDED_ON" for edge in self.edge_types):
            errors.append("required edge label missing: DECIDED_ON")

        for edge in self.edge_types:
            if edge.from_label not in label_set:
                errors.append(
                    f"edge {edge.label} has unknown from_label: {edge.from_label}"
                )
            if edge.to_label not in label_set:
                errors.append(
                    f"edge {edge.label} has unknown to_label: {edge.to_label}"
                )

        return errors
