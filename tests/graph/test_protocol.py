from __future__ import annotations

import inspect
from typing import get_type_hints

from copilot_sdk.evolution.protocol import EvolutionStore
from copilot_sdk.graph import (
    GraphStore,
    InMemoryGraphStore,
    ProtocolV2GraphStore,
    SQLiteGraphStore,
)


def test_graph_store_protocol_is_runtime_checkable(tmp_path):
    assert isinstance(InMemoryGraphStore(), GraphStore)
    assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), GraphStore)


def test_graph_store_protocol_required_methods_exist():
    required = [
        "write_decision",
        "write_outcome",
        "get_decision",
        "get_decisions",
        "get_all_decisions",
        "get_verified_decisions",
        "count_verified",
        "count_correct",
        "count_decisions",
        "save_centroids",
        "load_latest_centroids",
        "get_centroid_checkpoints",
        "archive_old_decisions",
        "count_archived",
        "close",
    ]

    for method in required:
        assert hasattr(GraphStore, method)


def test_protocol_v2_graph_store_required_methods_exist():
    required = [
        "write_governed_decision",
        "write_observation",
        "append_evidence_receipt",
        "write_conservation_status",
        "write_fingerprint",
        "write_centroid_checkpoint",
        "write_evolution_event",
        "link_entity",
        "archive_decisions",
        "domain_scoped_reset",
        "count_verified_decisions",
    ]

    for method in required:
        assert hasattr(ProtocolV2GraphStore, method)


def test_protocol_write_decision_is_domain_first():
    signature = inspect.signature(GraphStore.write_decision)

    assert list(signature.parameters)[:7] == [
        "self",
        "domain",
        "category",
        "action",
        "confidence",
        "factors",
        "metadata",
    ]


def test_protocol_write_outcome_has_no_domain_parameter():
    signature = inspect.signature(GraphStore.write_outcome)

    assert list(signature.parameters) == [
        "self",
        "decision_id",
        "actual_action",
        "is_correct",
        "metadata",
    ]


def test_protocol_queries_are_domain_scoped():
    for method_name in (
        "get_decisions",
        "get_all_decisions",
        "get_verified_decisions",
        "count_verified",
        "count_correct",
        "count_decisions",
        "get_centroid_checkpoints",
        "archive_old_decisions",
        "count_archived",
    ):
        signature = inspect.signature(getattr(GraphStore, method_name))
        assert list(signature.parameters)[1] == "domain"


def test_protocol_v2_count_verified_decisions_is_domain_scoped():
    signature = inspect.signature(ProtocolV2GraphStore.count_verified_decisions)

    assert list(signature.parameters)[1] == "domain"


def test_protocol_save_centroids_is_domain_first_and_flexible():
    signature = inspect.signature(GraphStore.save_centroids)

    assert list(signature.parameters)[:5] == [
        "self",
        "domain",
        "category",
        "centroids",
        "metadata",
    ]
    assert any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )


def test_protocol_load_latest_centroids_returns_raw_object_type():
    hints = get_type_hints(GraphStore.load_latest_centroids)

    assert str(hints["return"]) in {"typing.Any | None", "typing.Optional[typing.Any]"} or hints["return"] is object | None


def test_graph_store_protocol_does_not_require_evolution_methods():
    assert not hasattr(GraphStore, "save_evolution_event")
    assert not hasattr(GraphStore, "get_evolution_events")


def test_evolution_store_protocol_owns_evolution_methods():
    assert hasattr(EvolutionStore, "save_evolution_event")
    assert hasattr(EvolutionStore, "get_evolution_events")

    signature = inspect.signature(EvolutionStore.save_evolution_event)

    assert list(signature.parameters)[:6] == [
        "self",
        "domain",
        "event_type",
        "rule_name",
        "variant_id",
        "metadata",
    ]
    assert signature.parameters["variant_id"].default is None


def test_concrete_graph_stores_structurally_satisfy_evolution_store(tmp_path):
    assert isinstance(InMemoryGraphStore(), EvolutionStore)
    assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), EvolutionStore)


def test_entity_link_helpers_are_not_protocol_required():
    assert not hasattr(GraphStore, "link_decision_to_entity")
    assert not hasattr(GraphStore, "get_decision_links")
