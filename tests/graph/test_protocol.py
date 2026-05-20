from __future__ import annotations

import inspect

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, SQLiteGraphStore


def test_graph_store_protocol_is_runtime_checkable(tmp_path):
    assert isinstance(InMemoryGraphStore(), GraphStore)
    assert isinstance(SQLiteGraphStore(tmp_path / "graph.sqlite"), GraphStore)


def test_graph_store_protocol_required_methods_exist():
    required = [
        "write_decision",
        "write_outcome",
        "get_decision",
        "get_decisions",
        "get_verified_decisions",
        "count_verified",
        "count_correct",
        "get_all_decisions",
        "save_centroids",
        "get_centroid_checkpoints",
        "save_evolution_event",
        "close",
    ]

    for method in required:
        assert hasattr(GraphStore, method)


def test_graphstore_protocol_has_save_centroids():
    assert hasattr(GraphStore, "save_centroids")


def test_graphstore_protocol_has_get_centroid_checkpoints():
    assert hasattr(GraphStore, "get_centroid_checkpoints")


def test_protocol_save_centroids_accepts_bitemporal_keywords():
    signature = inspect.signature(GraphStore.save_centroids)

    assert list(signature.parameters)[:5] == [
        "self",
        "decision_id",
        "category",
        "centroids",
        "metadata",
    ]
    for name in ("decision_time_start", "decision_time_end", "checkpoint_time"):
        parameter = signature.parameters[name]
        assert parameter.default is None
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_protocol_get_checkpoints_accepts_filter_keywords():
    signature = inspect.signature(GraphStore.get_centroid_checkpoints)

    assert list(signature.parameters)[:2] == ["self", "limit"]
    for name in (
        "checkpoint_time_start",
        "checkpoint_time_end",
        "decision_time_start",
        "decision_time_end",
        "category",
    ):
        parameter = signature.parameters[name]
        assert parameter.default is None
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_graphstore_protocol_has_save_evolution_event():
    assert hasattr(GraphStore, "save_evolution_event")
