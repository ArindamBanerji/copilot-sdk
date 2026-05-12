from __future__ import annotations

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
        "close",
    ]

    for method in required:
        assert hasattr(GraphStore, method)


def test_graphstore_protocol_has_save_centroids():
    assert hasattr(GraphStore, "save_centroids")


def test_graphstore_protocol_has_get_centroid_checkpoints():
    assert hasattr(GraphStore, "get_centroid_checkpoints")
