"""Domain-aware entity links discovered through the shared GraphStore."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from copilot_sdk.graph.protocol import ProtocolV2GraphStore


@dataclass(frozen=True)
class EntityEdge:
    """A persisted cross-domain relationship with decision provenance."""

    edge_id: str
    source_domain: str
    source_entity_id: str
    source_entity_type: str
    target_domain: str
    target_entity_id: str
    target_entity_type: str
    source_decision_id: str
    target_decision_id: str
    relation: str = "ENTITY_LINK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_domain": self.source_domain,
            "source_entity_id": self.source_entity_id,
            "source_entity_type": self.source_entity_type,
            "target_domain": self.target_domain,
            "target_entity_id": self.target_entity_id,
            "target_entity_type": self.target_entity_type,
            "source_decision_id": self.source_decision_id,
            "target_decision_id": self.target_decision_id,
            "relation": self.relation,
            "provenance": "live_graph_store",
        }


def create_entity_edge(
    store: ProtocolV2GraphStore,
    *,
    edge_id: str,
    source_domain: str,
    source_entity_id: str,
    source_entity_type: str,
    source_decision_id: str,
    target_domain: str,
    target_entity_id: str,
    target_entity_type: str,
    target_decision_id: str,
    relation: str = "ENTITY_LINK",
) -> EntityEdge:
    """Link supplier/threat entities through domain-scoped GraphStore writes.

    The two native ``link_entity`` writes preserve each decision's domain. The
    entity-edge record is persisted as a graph TransferPattern metadata record,
    which keeps the shared AGE/SQLite/Memory contract identical.
    """
    if source_domain == target_domain:
        raise ValueError("entity edges require distinct source and target domains")
    edge = EntityEdge(
        edge_id=edge_id,
        source_domain=source_domain,
        source_entity_id=source_entity_id,
        source_entity_type=source_entity_type,
        target_domain=target_domain,
        target_entity_id=target_entity_id,
        target_entity_type=target_entity_type,
        source_decision_id=source_decision_id,
        target_decision_id=target_decision_id,
        relation=relation,
    )
    store.link_entity(source_decision_id, source_entity_id, source_entity_type, source_domain)
    store.link_entity(target_decision_id, target_entity_id, target_entity_type, target_domain)
    store.write_transfer_pattern(
        pattern_id=edge_id,
        source_domain=source_domain,
        target_domain=target_domain,
        pattern_type="entity_edge",
        factor_mapping={
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
        },
        confidence=1.0,
        validation_status="validated",
        conservation_status="GREEN",
        metadata={"entity_edge": edge.to_dict()},
    )
    return edge


def discover_entity_edges(
    store: ProtocolV2GraphStore,
    *,
    source_domain: str,
    target_domain: str,
    source_entity_id: str | None = None,
    target_entity_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Discover persisted supplier-to-threat edges with provenance."""
    rows = store.get_transfer_patterns(source_domain=source_domain, target_domain=target_domain)
    result: list[dict[str, Any]] = []
    for row in rows:
        if row.get("pattern_type") != "entity_edge":
            continue
        metadata = row.get("metadata")
        entity_edge = metadata.get("entity_edge") if isinstance(metadata, dict) else None
        if not isinstance(entity_edge, dict):
            continue
        if source_entity_id and entity_edge.get("source_entity_id") != source_entity_id:
            continue
        if target_entity_id and entity_edge.get("target_entity_id") != target_entity_id:
            continue
        result.append(
            {
                **entity_edge,
                "transfer_pattern_id": row.get("pattern_id"),
                "provenance": "live_graph_store",
            }
        )
        if len(result) >= max(0, int(limit)):
            break
    return result


def cross_graph_discovery(
    store: ProtocolV2GraphStore,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return discover_entity_edges(store, **kwargs)
