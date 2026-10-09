"""Legacy graph-published signals stay outside the decision inventory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.legacy_signal_filter import (
    LegacySignalFilteringGraphStore,
    is_legacy_signal_decision,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from tests.graph_store_test_helpers import make_memory_store


def _store(kind: str, path: Path) -> Any:
    raw: Any
    if kind == "sqlite":
        raw = make_memory_store(path, domain="trading")
    else:
        raw = InMemoryGraphStore(domain="trading")
    return LegacySignalFilteringGraphStore(raw)


@pytest.mark.parametrize("backend", ["memory"])
def test_iso_metadata_is_normalized_at_existing_store_boundaries(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "iso.db")
    iso = "2024-01-15T10:30:00Z"
    epoch = 1705314600.0
    try:
        decision_id = store.write_decision(
            "trading", "supplier_risk", "review", 0.8, {"risk": 0.5},
            metadata={"created_at": iso},
        )
        store.write_outcome(decision_id, "review", True,
                            metadata={"verified_at": iso}, domain="trading")
        row = store.get_decision(decision_id, domain="trading", include_outcome=True)
        assert row["created_at"] == row["verified_at"] == epoch
        store.write_governed_decision(
            "governed", "trading", "supplier_risk", 0, "review", 0, 0.8,
            [0.8, 0.2], [0.5], ["risk"], metadata={"created_at": iso},
        )
        assert store.get_decision("governed", domain="trading")["created_at"] == epoch
        store.write_observation(
            "obs", "trading", "supplier_risk", "review", 0.8, "preview", "v1", "v1",
            metadata={"created_at": iso},
        )
        # Observation writes have no protocol read method.
        raw = store.graph_primary
        observation = (raw.connection.execute(
            "SELECT created_at FROM observations WHERE observation_id = ?", ("obs",),
        ).fetchone() if backend == "sqlite" else raw._observations["obs"])
        assert observation["created_at"] == epoch
    finally:
        store.close()


def _write(store: Any, *, legacy: bool, category: str = "supplier_risk") -> str:
    raw = getattr(store, "graph_primary", store)
    metadata: dict[str, Any] = {"entity_id": "vendor-7", "created_at": float(raw.count_decisions("trading"))}
    if legacy:
        # Exact marker pair emitted by the removed GraphSignalStore.publish().
        metadata.update(signal_detail="legacy signal", signal_timestamp="2026-09-01T00:00:00+00:00")
    return str(store.write_decision(
        domain="trading", category=category, action="review", confidence=0.8,
        factors={"risk": 0.8}, metadata=metadata,
    ))


@pytest.mark.parametrize("backend", ["memory"])
def test_legacy_signal_excluded_from_count(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "decisions.db")
    try:
        ordinary_id = _write(store, legacy=False)
        legacy_id = _write(store, legacy=True)
        store.write_outcome(ordinary_id, actual_action="review", is_correct=True, domain="trading")

        assert store.count_decisions("trading") == 1
        assert store.count_verified_decisions("trading") == 1
        assert store.get_decision(legacy_id, "trading") is None
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_ordinary_decision_with_signal_category_included(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "decisions.db")
    try:
        decision_id = _write(store, legacy=False, category="supplier_risk")
        assert store.count_decisions("trading") == 1
        assert [row["decision_id"] for row in store.get_decisions("trading")] == [decision_id]
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_incomplete_legacy_marker_preserves_decision(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "decisions.db")
    try:
        decision_id = str(store.write_decision(
            domain="trading", category="supplier_risk", action="review", confidence=0.8,
            factors={"risk": 0.8}, metadata={"signal_detail": "not sufficient by itself"},
        ))
        assert store.count_decisions("trading") == 1
        assert [row["decision_id"] for row in store.get_all_decisions("trading")] == [decision_id]
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_legacy_signal_excluded_from_listing(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "decisions.db")
    try:
        legacy_id = _write(store, legacy=True)
        assert store.count_decisions("trading") == 0
        assert store.get_all_decisions("trading") == []
        assert store.get_decisions("trading") == []
        assert store.get_decision(legacy_id, "trading") is None
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_legacy_marker_distinguishable(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "decisions.db")
    try:
        legacy_id = _write(store, legacy=True)
        ordinary_id = _write(store, legacy=False)
        rows = store.get_all_decisions("trading")
        assert [row["decision_id"] for row in rows] == [ordinary_id]
        assert store.count_decisions("trading") == 1
        assert store.get_decision(legacy_id, "trading") is None
    finally:
        store.close()


def test_age_adapter_filter_wrapper_excludes_legacy_rows(tmp_path: Path) -> None:
    # AGE uses this SDK wrapper at the factory boundary; exercise it over an
    # actual GraphStore implementation without requiring a live AGE service.
    store = InMemoryGraphStore(domain="trading")
    filtered = LegacySignalFilteringGraphStore(store)
    try:
        legacy_id = _write(store, legacy=True)
        ordinary_id = _write(store, legacy=False)
        assert store.count_decisions("trading") == 2
        assert {row["decision_id"] for row in store.get_all_decisions("trading")} == {ordinary_id, legacy_id}
        assert filtered.count_decisions("trading") == 1
        assert [row["decision_id"] for row in filtered.get_all_decisions("trading")] == [ordinary_id]
        assert filtered.get_decision(legacy_id, "trading") is None
    finally:
        filtered.close()


@pytest.mark.parametrize("backend", ["memory", "sqlite", "age", "unsupported_backend"])
def test_factory_wraps_every_backend(tmp_path: Path, backend: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from copilot_sdk.graph import factory

    class Adapter(InMemoryGraphStore):
        def __init__(self, dsn: str, graph_name: str) -> None:
            super().__init__(domain="trading")

    monkeypatch.setattr(factory, "_load_age_adapter", lambda: Adapter)
    if backend in {"sqlite", "unsupported_backend"}:
        with pytest.raises(ValueError, match="invalid graph backend"):
            factory.create_graph_store(backend=backend, domain="trading", profile="test", env={})
        return
    store = factory.create_graph_store(backend=backend, domain="trading", profile="test",
                                       dsn="postgres://test",
                                       graph_name="test_graph", env={})
    try:
        identifier = _write(store, legacy=True)
        assert store.graph_primary.get_decision(identifier, "trading") is not None
        assert store.get_decisions("trading") == []
        assert store.count_decisions("trading") == 0
        assert store.domain == "trading"
    finally:
        store.close()


def test_filter_uses_graph_inventory_protocol_for_decisions() -> None:
    raw = InMemoryGraphStore(domain="trading")
    filtered = LegacySignalFilteringGraphStore(raw, domain="trading")
    try:
        visible = [_write(raw, legacy=False, category="selected") for _ in range(3)]
        _write(raw, legacy=True, category="selected")
        assert [row["decision_id"] for row in filtered.get_decisions("trading", "selected", 3)] == visible
        assert filtered.count_decisions("trading") == 3
    finally:
        filtered.close()


@pytest.mark.parametrize("backend", ["memory"])
@pytest.mark.parametrize("value", [None, False, 0, "", []])
def test_falsy_markers_are_excluded(tmp_path: Path, backend: str, value: Any) -> None:
    store = _store(backend, tmp_path / "edge.db")
    try:
        identifier = store.write_decision("trading", "ordinary_category", "review", .8, {},
                                          metadata={"signal_detail": value, "signal_timestamp": value})
        assert store.graph_primary.get_decision(identifier, "trading") is not None
        assert store.get_decision(identifier, "trading") is None
        assert store.get_decisions("trading") == []
        assert store.count_decisions("trading") == 0
        store.archive_old_decisions("trading", keep_recent=0)
        assert len(store.graph_primary.get_archived_decisions("trading")) == 1
        assert store.get_archived_decisions("trading") == []
        assert store.count_archived("trading") == 0
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
@pytest.mark.parametrize("metadata", [None, {}, {"signal_detail": None}, {"signal_timestamp": None}])
def test_unmarked_decisions_survive_every_read(tmp_path: Path, backend: str, metadata: Any) -> None:
    store = _store(backend, tmp_path / "ordinary.db")
    try:
        identifier = store.write_decision("trading", "supplier_risk", "review", .8, {}, metadata=metadata)
        _write(store, legacy=True)
        assert store.graph_primary.count_decisions("trading") == 2
        assert [row["decision_id"] for row in store.get_decisions("trading")] == [identifier]
        assert store.get_decision(identifier, "trading") is not None
        assert store.count_decisions("trading") == 1
        store.archive_old_decisions("trading", keep_recent=0)
        assert [row["decision_id"] for row in store.get_archived_decisions("trading")] == [identifier]
        assert store.count_archived("trading") == 1
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_pages_stop_before_loading_entire_domain(tmp_path: Path, backend: str, monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store(backend, tmp_path / "pages.db")
    raw = store.graph_primary
    try:
        for _ in range(100):
            _write(raw, legacy=True)
        identifiers = [_write(raw, legacy=False) for _ in range(5)]
        def forbidden(*args: Any, **kwargs: Any) -> Any:
            pytest.fail("legacy filter must not call backend-private paging")
        monkeypatch.setattr(raw, "_decision_page", forbidden)
        assert [row["decision_id"] for row in store.get_decisions("trading", limit=3)] == identifiers[:3]
        assert store.count_decisions("trading") == 5
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
@pytest.mark.parametrize("offset,limit", [(0, 0), (0, 1), (1, 2), (3, 3), (5, 2), (8, 2)])
def test_category_and_visible_offset_page_boundaries(tmp_path: Path, backend: str, offset: int, limit: int) -> None:
    store = _store(backend, tmp_path / "boundaries.db")
    try:
        identifiers = []
        for _ in range(5):
            _write(store, legacy=True, category="selected")
            _write(store, legacy=False, category="other")
            identifiers.append(_write(store, legacy=False, category="selected"))
        result = store.get_decisions("trading", category="selected", limit=limit, offset=offset)
        assert [row["decision_id"] for row in result] == identifiers[offset:offset + limit]
        assert store.get_decisions("purchasing", limit=3) == []
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_counts_project_metadata_without_decoding_payloads(tmp_path: Path, backend: str, monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store(backend, tmp_path / "projection.db")
    try:
        ordinary = _write(store, legacy=False)
        legacy = _write(store, legacy=True)
        for identifier in (ordinary, legacy):
            store.write_outcome(identifier, "review", True, domain="trading")
        assert store.count_verified("trading") == 2
        assert store.count_correct("trading") == 2
        assert store.count_decisions("trading") == 1
        store.archive_old_decisions("trading", keep_recent=0)
        assert store.count_archived("trading") == 1
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_factory_disabled_wrapper_exposes_legacy_decision(backend: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from copilot_sdk.graph import factory

    if backend == "sqlite":
        with pytest.raises(ValueError, match="invalid graph backend"):
            factory.create_graph_store(backend=backend, domain="trading", profile="test", env={})
        return

    with monkeypatch.context() as patch:
        patch.setattr(factory, "LegacySignalFilteringGraphStore", lambda store, **_kwargs: store)
        raw = factory.create_graph_store(backend=backend, domain="trading", profile="test", env={})
        try:
            identifier = _write(raw, legacy=True)
            assert [row["decision_id"] for row in raw.get_decisions("trading")] == [identifier]
        finally:
            raw.close()
    filtered = factory.create_graph_store(backend=backend, domain="trading", profile="test", env={})
    try:
        _write(filtered, legacy=True)
        assert filtered.get_decisions("trading") == []
    finally:
        filtered.close()


def _mixed_linked_decisions(raw: Any) -> tuple[list[str], list[str]]:
    visible: list[str] = []
    hidden: list[str] = []
    markers: list[dict[str, Any]] = [
        {"signal_detail": None, "signal_timestamp": False},
        {"signal_detail": [], "signal_timestamp": ""},
        {}, {}, {"signal_detail": 0}, {"signal_timestamp": None},
    ]
    for index, marker in enumerate(markers):
        identifier = raw.write_decision(
            "trading", "supplier_risk", "review", .8, {"risk": .5},
            metadata={"entity_id": "vendor-7", "created_at": index, **marker},
        )
        raw.link_decision_to_entity(identifier, "vendor-7", domain="trading")
        (hidden if index < 2 else visible).append(identifier)
    return visible, hidden


@pytest.mark.parametrize("backend", ["memory"])
@pytest.mark.parametrize("method", ["query_context", "decision_movement", "contextual_judgment", "query_similar"])
def test_composite_views_exclude_only_legacy_decisions(tmp_path: Path, backend: str, method: str) -> None:
    store = _store(backend, tmp_path / "composite.db")
    raw = store.graph_primary
    try:
        visible, hidden = _mixed_linked_decisions(raw)

        def read(view: Any) -> set[str]:
            if method == "query_context":
                rows = view.query_context("vendor-7", 1, domain="trading")
            elif method == "decision_movement":
                rows = view.decision_movement("trading", visible[0])
            elif method == "contextual_judgment":
                return {r["decision"]["decision_id"] for r in view.contextual_judgment("trading", "vendor-7", "supplier_risk")}
            else:
                return {r["decision_id"] for r in view.query_similar(visible[0], 100, domain="trading")}
            return {r["properties"]["decision_id"] for r in rows if r["node"] == "decision"}

        excluded_source = {visible[0]} if method == "query_similar" else set()
        assert read(raw) == set(visible + hidden) - excluded_source
        assert read(store) == set(visible) - excluded_source
        assert len(read(store)) + len(excluded_source) == store.count_decisions("trading") == 4
        assert store.decision_movement("trading", hidden[0]) == []
        assert store.query_similar(hidden[0], 2, domain="trading") == []
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_checkpoint_lineage_filters_single_decision(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "lineage.db")
    try:
        visible, hidden = _mixed_linked_decisions(store.graph_primary)
        for index, identifier in enumerate(visible + hidden):
            checkpoint_id = f"checkpoint-{index}"
            store.write_centroid_checkpoint(checkpoint_id, "trading", "supplier_risk", "review",
                                            [[.5]], 6, 0, .1, [1, 1], "hash", decision_id=identifier)
            assert store.graph_primary.get_checkpoint_lineage("trading", checkpoint_id)["decision_id"] == identifier
            result = store.get_checkpoint_lineage("trading", checkpoint_id)
            if identifier in hidden:
                assert result is None
            else:
                assert result is not None and result["decision_id"] == identifier
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_composite_limits_apply_after_exclusion(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "limits.db")
    raw = store.graph_primary
    try:
        for _ in range(105):
            identifier = _write(raw, legacy=True)
            raw.link_decision_to_entity(identifier, "vendor-7", domain="trading")
        visible = [_write(raw, legacy=False) for _ in range(4)]
        for identifier in visible:
            raw.link_decision_to_entity(identifier, "vendor-7", domain="trading")
        assert len(raw.query_similar(visible[0], 2, domain="trading")) == 2
        # Memory's protocol reads are newest-first; the retired backend retains
        # its old chronology. Both must apply the limit after excluding signals.
        similar = store.query_similar(visible[0], 2, domain="trading")
        assert len(similar) <= 2
        assert all(not is_legacy_signal_decision(row) for row in similar)
        assert all(row["decision_id"] != visible[0] for row in similar)
        assert store.query_similar(visible[0], 0, domain="trading") == []
        context = store.query_context("vendor-7", 1, domain="trading")
        assert not any(is_legacy_signal_decision(r) for r in context)
        judgment = store.contextual_judgment("trading", "vendor-7", "supplier_risk")
        assert not any(is_legacy_signal_decision(r) for r in judgment)
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_new_checkpoint_counts_preserve_history_and_verified_statistics(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "counts.db")
    raw = store.graph_primary
    try:
        identifiers = [_write(raw, legacy=legacy) for legacy in [False, False, False, True, True]]
        for identifier in identifiers:
            raw.write_outcome(identifier, "review", True, domain="trading")
        verified_before = raw.get_verified_decisions("trading")
        raw.save_centroids("trading", "supplier_risk", [[.5]], {"name": "old"}, decision_id=identifiers[0])
        store.save_centroids("trading", "supplier_risk", [[.6]], {"name": "first"}, decision_id=identifiers[1])
        assert store.count_decisions("trading") == 3
        new_id = _write(raw, legacy=False)
        store.save_centroids("trading", "supplier_risk", [[.7]], {"name": "second"}, decision_id=new_id)
        checkpoints = {r["metadata"]["name"]: r["decisions_count"] for r in store.get_centroid_checkpoints("trading")}
        assert checkpoints == {"old": 5, "first": 3, "second": 4}
        trajectory = {r["metadata"]["name"]: r["decisions_count"] for r in store.get_iks_trajectory(["trading"])}
        assert trajectory == checkpoints
        assert store.count_verified("trading") == raw.count_verified("trading") == 5
        assert store.count_correct("trading") == raw.count_correct("trading") == 5
        assert store.get_verified_decisions("trading") == verified_before
    finally:
        store.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_scorer_regime_fallback_uses_filtered_checkpoint_count(tmp_path: Path, backend: str) -> None:
    from copilot_sdk.scoring.scorer import CompoundingScorer

    store = _store(backend, tmp_path / "recovery.db")
    try:
        for legacy in [False, False, False, True, True]:
            identifier = _write(store.graph_primary, legacy=legacy)
            store.write_outcome(identifier, "review", True, domain="trading")
        scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test")
        store.save_centroids("trading", "supplier_risk", scorer._scorer.centroids.copy(), {"regime_tag": "test"})
        checkpoint = store.load_latest_checkpoint_for_regime("trading", "test")
        assert not checkpoint.get("verified_count")
        assert checkpoint["decisions_count"] == 3
        result = scorer.reinitialize_from_regime("test", v_discount=1.0)
        assert result["success"] is True
        assert scorer._calibration_overlay is not None
        assert scorer._calibration_overlay["effective_V_base"] == 3
        assert scorer._calibration_overlay["actual_V"] == 5
    finally:
        store.close()




class _GraphStoreWithoutTraversal:
    """Structural GraphStore view used to verify optional traversal gating."""

    _UNSUPPORTED_METHODS = {
        "get_decision_links", "query_context", "query_similar",
        "decision_movement", "contextual_judgment", "promotion_basis",
        "write_governed_decision",
    }

    def __init__(self, delegate: InMemoryGraphStore) -> None:
        self._delegate = delegate

    def __getattr__(self, name: str) -> Any:
        if name in self._UNSUPPORTED_METHODS:
            raise AttributeError(name)
        return getattr(self._delegate, name)


def test_graphstore_only_stub_filters_inventory_and_skips_traversal(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from copilot_sdk.graph.protocol import GraphStore, GraphTraversalStore

    raw = InMemoryGraphStore(domain="trading")
    ordinary_id = _write(raw, legacy=False)
    _write(raw, legacy=True)
    graph_only = _GraphStoreWithoutTraversal(raw)
    assert isinstance(graph_only, GraphStore)
    assert not isinstance(graph_only, GraphTraversalStore)

    wrapper = LegacySignalFilteringGraphStore(graph_only, domain="trading")
    assert [row["decision_id"] for row in wrapper.get_decisions("trading")] == [ordinary_id]
    assert wrapper.count_decisions("trading") == 1
    with caplog.at_level("WARNING", logger="copilot_sdk.graph.legacy_signal_filter"):
        assert wrapper.query_context("vendor-7", 1, domain="trading") == []
    assert any("lacks GraphTraversalStore" in record.message for record in caplog.records)
    raw.close()


def test_graphtraversal_store_filters_composite_rows() -> None:
    from copilot_sdk.graph.protocol import GraphTraversalStore

    raw = InMemoryGraphStore(domain="trading")
    visible, hidden = _mixed_linked_decisions(raw)
    wrapper = LegacySignalFilteringGraphStore(raw, domain="trading")
    assert isinstance(raw, GraphTraversalStore)
    context = wrapper.query_context("vendor-7", 1, domain="trading")
    decision_ids = {
        row["properties"]["decision_id"]
        for row in context
        if row.get("node") == "decision"
    }
    assert decision_ids == set(visible)
    assert not (set(hidden) & decision_ids)
    raw.close()


@pytest.mark.parametrize("encoded", [False, True])
def test_protocol_traversal_filters_nested_composite_shapes(
    monkeypatch: pytest.MonkeyPatch, encoded: bool,
) -> None:
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    adapter = object.__new__(AGEGraphStoreAdapter)
    adapter.domain = "trading"
    visible = {"decision_id": "ordinary", "metadata": {"signal_detail": None}}
    hidden = {
        "decision_id": "legacy",
        "metadata": json.dumps({"signal_detail": None, "signal_timestamp": False}),
    }
    visible["description"] = "literal ::vertex text"
    nodes: list[Any] = [visible, hidden]
    if encoded:
        nodes = [json.dumps({"properties": row}) + "::vertex" for row in nodes]
    rows = [{"p": [{"properties": node}]} for node in nodes]
    if encoded:
        rows = [{"p": [node]} for node in nodes]
    monkeypatch.setattr(adapter, "query_context", lambda *args, **kwargs: rows)
    monkeypatch.setattr(adapter, "get_decision", lambda *args, **kwargs: visible)
    wrapper = LegacySignalFilteringGraphStore(adapter, domain="trading")
    result = wrapper.query_context("vendor-7", 2, domain="trading")
    assert result == rows[:1]
    assert len(rows) == 2


def test_protocol_similarity_filters_returned_legacy_records(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = InMemoryGraphStore(domain="trading")
    wrapper = LegacySignalFilteringGraphStore(raw, domain="trading")
    source_id = _write(raw, legacy=False)
    rows = [
        {"decision_id": "legacy", "metadata": {"signal_detail": None, "signal_timestamp": False}},
        {"decision_id": "visible", "metadata": {}},
    ]
    monkeypatch.setattr(raw, "query_similar", lambda *_args, **_kwargs: rows)
    result = wrapper.query_similar(source_id, 2, domain="trading")
    assert result == [rows[1]]
    raw.close()


def test_protocol_similarity_reports_underfilled_page(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    raw = InMemoryGraphStore(domain="trading")
    wrapper = LegacySignalFilteringGraphStore(raw, domain="trading")
    source_id = _write(raw, legacy=False)
    monkeypatch.setattr(raw, "query_similar", lambda *_args, **_kwargs: [
        {"decision_id": "legacy", "metadata": {
            "signal_detail": None, "signal_timestamp": False,
        }},
        {"decision_id": "visible", "metadata": {}},
    ])
    with caplog.at_level("WARNING", logger="copilot_sdk.graph.legacy_signal_filter"):
        assert [
            row["decision_id"]
            for row in wrapper.query_similar(source_id, 2, domain="trading")
        ] == ["visible"]
    assert any("does not expose offset paging" in record.message for record in caplog.records)
    raw.close()


def test_protocol_movement_filters_legacy_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = InMemoryGraphStore(domain="trading")
    source_id = _write(raw, legacy=False)
    wrapper = LegacySignalFilteringGraphStore(raw, domain="trading")
    mixed = [
        {"direction": "outbound", "decision": {
            "decision_id": "ordinary", "metadata": {},
        }},
        {"direction": "inbound", "decision": {
            "decision_id": "legacy", "metadata": {
                "signal_detail": None, "signal_timestamp": False,
            },
        }},
    ]
    monkeypatch.setattr(raw, "decision_movement", lambda *_args, **_kwargs: mixed)
    assert wrapper.decision_movement("trading", source_id) == mixed[:1]
    raw.close()


def test_protocol_promotion_basis_filters_nested_decisions(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = InMemoryGraphStore(domain="trading")
    wrapper = LegacySignalFilteringGraphStore(raw, domain="trading")
    rows = [
        {"evidence": {"decision_id": "ordinary", "metadata": {}}},
        {"evidence": {"decision_id": "legacy", "metadata": {
            "signal_detail": None, "signal_timestamp": False,
        }}},
    ]
    monkeypatch.setattr(raw, "promotion_basis", lambda *_args, **_kwargs: rows)
    assert wrapper.promotion_basis("trading", "rule-1") == rows[:1]
    raw.close()


@pytest.mark.parametrize("backend", ["memory"])
def test_local_promotion_basis_preserves_event_shape(tmp_path: Path, backend: str) -> None:
    store = _store(backend, tmp_path / "promotion.db")
    try:
        store.save_evolution_event(
            "trading", "promoted", "rule-1", metadata={"evidence": "verified"}
        )
        raw = store.graph_primary.promotion_basis("trading", "rule-1")
        assert len(raw) == 1 and "evolution_event" in raw[0]
        assert store.promotion_basis("trading", "rule-1") == raw
    finally:
        store.close()


def test_optional_protocol_v2_reads_are_skipped_for_graphstore_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    raw = InMemoryGraphStore(domain="trading")
    decision_id = _write(raw, legacy=False)
    graph_only = _GraphStoreWithoutTraversal(raw)
    wrapper = LegacySignalFilteringGraphStore(graph_only, domain="trading")
    with caplog.at_level("WARNING", logger="copilot_sdk.graph.legacy_signal_filter"):
        assert wrapper.decision_movement("trading", decision_id) == []
        assert wrapper.contextual_judgment("trading", "vendor-7", "risk") == []
        assert wrapper.promotion_basis("trading", "rule-1") == []
    assert len([record for record in caplog.records if "lacks ProtocolV2GraphStore" in record.message]) == 3
    raw.close()

def test_wrapper_public_signatures_unchanged() -> None:
    import inspect
    from copilot_sdk.graph.protocol import GraphTraversalStore, ProtocolV2GraphStore

    protocol_methods = {
        "query_context": GraphTraversalStore.query_context,
        "decision_movement": ProtocolV2GraphStore.decision_movement,
        "contextual_judgment": ProtocolV2GraphStore.contextual_judgment,
        "promotion_basis": ProtocolV2GraphStore.promotion_basis,
    }
    for name, protocol_method in protocol_methods.items():
        assert list(inspect.signature(getattr(LegacySignalFilteringGraphStore, name)).parameters) == list(
            inspect.signature(protocol_method).parameters
        )



