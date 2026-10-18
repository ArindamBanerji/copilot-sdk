"""Reusable behavioral contracts for bounded projections over a real store.

The fixture currently selects InMemoryGraphStore. Future implementations must
pass these contracts, with equivalent historical-data fixtures where noted.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from typing import Any

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.graph.protocol import BoundedProjectionStore, GraphStore, ProtocolV2GraphStore
from copilot_sdk.graph.query import (
    DecisionAggregate, DecisionCursor, DecisionFilter, DecisionGenerationChanged,
    DecisionOrder, DecisionPageRequest, DecisionProjection, ProjectionCardinalityExceeded,
)


@pytest.fixture
def store() -> InMemoryGraphStore:
    return InMemoryGraphStore(domain="test")


def write(
    store: InMemoryGraphStore, index: int = 0, *, domain: str = "test",
    category: str = "a", action: str = "buy", confidence: float = 0.75,
    metadata: dict[str, Any] | None = None,
) -> str:
    decision_id = f"{domain}-{index:04d}"
    store.write_governed_decision(
        decision_id=decision_id, domain=domain, category=category,
        category_index=1, recommended_action=action, recommended_index=0,
        confidence=confidence, probabilities=[0.75, 0.25],
        factor_vector=[float(index), 0.2], factor_names=["risk", "size"],
        source="feed", scorer_version="s1", preset_version="p1",
        factor_schema_version="f1", metadata={"created_at": 10.0 + index, **(metadata or {})},
    )
    return decision_id


def verify(store: InMemoryGraphStore, decision_id: str, correct: bool = True, when: float = 100.0) -> None:
    store.write_outcome(
        decision_id, "hold", correct,
        {"verified_at": when, "actual_index": 2, "note": ["original"]},
        domain="test", verified_at_epoch=when + 1, quality_signal=0.9,
    )


@pytest.fixture
def seeded(store: InMemoryGraphStore) -> InMemoryGraphStore:
    for i in range(6):
        metadata: dict[str, Any] = {
            "tenant_id": "alpha" if i % 2 == 0 else "beta",
            "ticker": "aapl" if i % 2 == 0 else "MSFT",
            "regime": "calm" if i < 3 else "volatile",
        }
        if i == 0:
            metadata.update(signal_detail=None, signal_timestamp=False)
        decision_id = write(store, i, category="a" if i % 2 == 0 else "b",
                            action="buy" if i % 2 == 0 else "sell",
                            confidence=0.5 + i * 0.1, metadata=metadata)
        if i < 4:
            verify(store, decision_id, i % 2 == 0, 103.0 - i)
    return store


def request_page(**kwargs: Any) -> DecisionPageRequest:
    return DecisionPageRequest(**kwargs)


def ids(store: InMemoryGraphStore, filters: DecisionFilter | None = None) -> set[str]:
    return {row["decision_id"] for row in store.query_decisions("test", filters=filters).items}


def test_protocol_membership(store: InMemoryGraphStore) -> None:
    assert isinstance(store, BoundedProjectionStore)
    assert isinstance(store, GraphStore)
    assert isinstance(store, ProtocolV2GraphStore)


def test_empty_and_single_summary(store: InMemoryGraphStore) -> None:
    empty = store.query_decisions("test")
    assert (empty.items, empty.next_cursor, empty.has_more) == ((), None, False)
    decision_id = write(store)
    row, = store.query_decisions("test").items
    assert row == {
        "decision_id": decision_id, "domain": "test", "category": "a",
        "recommended_action": "buy", "status": "pending", "confidence": 0.75,
        "created_at": 10.0, "verified_at": None, "is_correct": None, "correct": None,
    }


@pytest.mark.parametrize(("kwargs", "indices"), [
    ({"categories": ("a",)}, [0, 2, 4]),
    ({"categories": ("a", "b"), "verified": True}, [0, 1, 2, 3]),
    ({"categories": ("a",), "statuses": ("pending",)}, [4]),
    ({"actions": ("buy",)}, [0, 2, 4]),
    ({"actions": ("hold",)}, []),
    ({"statuses": ("confirmed",)}, [0, 2]),
    ({"sources": ("feed",)}, [0, 1, 2, 3, 4, 5]),
    ({"sources": ("missing",)}, []),
    ({"regimes": ("calm",)}, [0, 1, 2]),
    ({"verified": True}, [0, 1, 2, 3]),
    ({"verified": False}, [4, 5]),
    ({"correct": True}, [0, 2]),
    ({"correct": False}, [1, 3]),
    ({"correct": False, "verified": False}, []),
    ({"confidence_min": 0.6, "confidence_max": 0.8}, [1, 2, 3]),
    ({"created_from": 11.0, "created_to": 14.0}, [1, 2, 3]),
    ({"verified_from": 101.0, "verified_to": 103.0}, [1, 2]),
    ({"decision_ids": ("test-0000", "test-0005")}, [0, 5]),
    ({"exclude_decision_ids": ("test-0000", "test-0005")}, [1, 2, 3, 4]),
    ({"decision_ids": ("test-0000",), "exclude_decision_ids": ("test-0000",)}, []),
    ({"ticker": "AaPl"}, [0, 2, 4]),
    ({"tenant_id": "beta"}, [1, 3, 5]),
    ({"exclude_legacy_signals": True}, [1, 2, 3, 4, 5]),
    ({"categories": (), "decision_ids": (), "sources": ()}, [0, 1, 2, 3, 4, 5]),
])
def test_shared_filter_contract(seeded: InMemoryGraphStore, kwargs: dict[str, Any], indices: list[int]) -> None:
    filters = DecisionFilter(**kwargs)
    expected = {f"test-{i:04d}" for i in indices}
    assert ids(seeded, filters) == expected
    assert seeded.count_decisions("test", filters=filters) == len(expected)
    aggregate, = seeded.aggregate_decisions("test", filters=filters)
    assert aggregate.values == {"count": float(len(expected))}


def test_default_tenant_and_legacy_presence(store: InMemoryGraphStore) -> None:
    write(store, 0)
    write(store, 1, metadata={"signal_detail": ""})
    write(store, 2, metadata={"signal_detail": "", "signal_timestamp": None})
    assert store.count_decisions("test", filters=DecisionFilter(tenant_id="default")) == 3
    assert ids(store, DecisionFilter(exclude_legacy_signals=True)) == {"test-0000", "test-0001"}
    assert store.count_decisions("other") == 0
    assert store.count_decisions("test") == 3


@pytest.mark.parametrize("order_by", ["created_at", "verified_at"])
@pytest.mark.parametrize("descending", [False, True])
@pytest.mark.parametrize("limit", [1, 2, 3])
def test_cursor_visits_every_row_once(
    seeded: InMemoryGraphStore, order_by: DecisionOrder, descending: bool, limit: int,
) -> None:
    expected = list(range(6)) if order_by == "created_at" else [3, 2, 1, 0]
    if descending:
        expected.reverse()
    cursor = None
    seen: list[str] = []
    for _ in range(8):
        page = seeded.query_decisions("test", page=DecisionPageRequest(
            limit=limit, after=cursor, order_by=order_by, descending=descending))
        seen.extend(row["decision_id"] for row in page.items)
        if not page.has_more:
            assert page.next_cursor is None
            break
        assert page.next_cursor is not None
        cursor = page.next_cursor
    assert seen == [f"test-{i:04d}" for i in expected]
    assert len(seen) == len(set(seen))


def test_offset_and_default_descending(seeded: InMemoryGraphStore) -> None:
    page = seeded.query_decisions("test", page=DecisionPageRequest(limit=2, offset=2))
    assert [row["decision_id"] for row in page.items] == ["test-0003", "test-0002"]
    assert page.has_more
    assert seeded.query_decisions("test", page=DecisionPageRequest(offset=99)).items == ()


def test_cursor_offset_and_order_validation(seeded: InMemoryGraphStore) -> None:
    cursor = seeded.query_decisions("test", page=DecisionPageRequest(limit=1)).next_cursor
    assert cursor is not None
    with pytest.raises(ValueError, match="mutually exclusive"):
        DecisionPageRequest(after=cursor, offset=1)
    with pytest.raises(ValueError, match="does not match"):
        DecisionPageRequest(after=cursor, order_by="verified_at")


@pytest.mark.parametrize("descending", [False, True])
def test_tied_creation_keys_use_id_not_insertion_sequence(store: InMemoryGraphStore, descending: bool) -> None:
    for i in [2, 0, 1]:
        write(store, i, metadata={"created_at": 10.0})
    cursor = None
    result = []
    for _ in range(3):
        page = store.query_decisions("test", page=DecisionPageRequest(
            limit=1, after=cursor, descending=descending))
        result.append(page.items[0]["decision_id"])
        cursor = page.next_cursor
    expected = ["test-0000", "test-0001", "test-0002"]
    assert result == (list(reversed(expected)) if descending else expected)


@pytest.mark.parametrize("descending", [False, True])
def test_historical_missing_timestamps_have_resumable_ids(store: InMemoryGraphStore, descending: bool) -> None:
    for i in [2, 0, 1, 3]:
        write(store, i, metadata={"created_at": -1.0 if i == 3 else 0.0})
    # Historical representation fixture: public writers reject null timestamps.
    # The query still runs against the real store, without mocking store methods.
    store._decisions["test-0002"]["created_at"] = None
    store._decisions["test-0000"].pop("created_at")
    missing = store.query_decisions("test", filters=DecisionFilter(decision_ids=("test-0000", "test-0002")))
    assert all(row["created_at"] is None for row in missing.items)
    cursor = None
    result = []
    for _ in range(4):
        page = store.query_decisions("test", page=DecisionPageRequest(
            limit=1, after=cursor, descending=descending))
        result.append(page.items[0]["decision_id"])
        cursor = page.next_cursor
    expected = ["test-0003", "test-0000", "test-0001", "test-0002"]
    assert result == (list(reversed(expected)) if descending else expected)


def test_verified_missing_timestamp_is_integrity_error(store: InMemoryGraphStore) -> None:
    decision_id = write(store)
    verify(store, decision_id)
    store._outcomes[decision_id]["verified_at"] = None
    with pytest.raises(ValueError, match="missing verified_at"):
        store.query_decisions("test", page=DecisionPageRequest(order_by="verified_at"))


def test_generation_fence_and_cursor(seeded: InMemoryGraphStore) -> None:
    generation = seeded.get_decision_changes("test", after_generation=0).current_generation
    first = seeded.query_decisions("test", as_of_generation=generation, page=DecisionPageRequest(limit=2))
    second = seeded.query_decisions("test", as_of_generation=generation,
                                   page=DecisionPageRequest(limit=2, after=first.next_cursor))
    assert len(second.items) == 2
    verify(seeded, "test-0004")
    with pytest.raises(DecisionGenerationChanged) as error:
        seeded.query_decisions("test", as_of_generation=generation,
                               page=DecisionPageRequest(after=second.next_cursor))
    assert (error.value.expected, error.value.actual) == (generation, generation + 1)
    with pytest.raises(DecisionGenerationChanged):
        seeded.query_decisions("test", as_of_generation=0)


@pytest.mark.parametrize("projection", ["summary", "scoring", "journal", "full"])
def test_projection_normalization_and_copy_isolation(store: InMemoryGraphStore, projection: DecisionProjection) -> None:
    decision_id = write(store, metadata={
        "ticker": "aapl", "tags": ["one"], "secret": "must not leak",
        "entry_time": "2026-01-01", "options_factors": {"delta": [0.2]},
        "learning_metadata": {"reward": 0.4, "verifier": {"name": "one"}, "secret": "strip"},
    })
    verify(store, decision_id)
    row = store.query_decisions("test", projection=projection).items[0]
    assert row["is_correct"] is row["correct"] is True
    assert row["verified_at"] == 100.0
    assert "_sequence" not in row and "_generation" not in row
    if projection != "full":
        assert "metadata" not in row and "secret" not in row
    if projection == "summary":
        assert len(row) == 10 and "factor_vector" not in row
    if projection == "scoring":
        assert row["factor_vector"] == [0.0, 0.2]
        assert row["factor_names"] == ["risk", "size"]
        assert row["actual_action"] == "hold" and row["actual_index"] == 2
        assert row["verified_at_epoch"] == 101.0
        assert row["learning_metadata"] == {"reward": 0.4, "verifier": {"name": "one"}}
        row["learning_metadata"]["verifier"]["name"] = "mutated"
        row["factor_vector"].append(99)
    if projection == "journal":
        assert "factor_vector" not in row and row["ticker"] == "AAPL"
        assert row["exit_time"] is None
        row["options_factors"]["delta"].append(99)
        row["tags"].append("mutated")
    if projection == "full":
        assert row["metadata"]["secret"] == "must not leak"
        row["metadata"]["tags"].append("mutated")
        row["outcome_metadata"]["note"].append("mutated")
    again = store.query_decisions("test", projection=projection).items[0]
    assert "mutated" not in repr(again)
    assert "99" not in repr(again)


def test_metadata_normalization_and_regime_grouping(store: InMemoryGraphStore) -> None:
    write(store, metadata={"market_regime": "bear", "date": "2026-01-01", "shares": 2, "pnl_dollars": 3})
    row = store.query_decisions("test", projection="journal").items[0]
    assert (row["regime"], row["entry_time"], row["size"], row["pnl"]) == ("bear", "2026-01-01", 2, 3)
    assert store.count_decisions("test", filters=DecisionFilter(regimes=("bear",))) == 1
    assert store.aggregate_decisions("test", group_by=("regime",))[0].dimensions == {"regime": "bear"}


def test_historical_top_level_normalization_precedes_metadata(store: InMemoryGraphStore) -> None:
    decision_id = write(store, metadata={"ticker": "msft", "regime": "calm", "tenant_id": "alpha"})
    # Older records can carry canonical fields directly, unlike today's writer.
    store._decisions[decision_id].update(ticker="aapl", regime="volatile", source="import", tenant_id="beta")
    filters = DecisionFilter(ticker="AaPl", regimes=("volatile",), sources=("import",), tenant_id="beta")
    row, = store.query_decisions("test", projection="journal", filters=filters).items
    assert (row["ticker"], row["regime"], row["source"]) == ("AAPL", "volatile", "import")
    assert store.count_decisions("test", filters=filters) == 1


def test_empty_aggregates(store: InMemoryGraphStore) -> None:
    result, = store.aggregate_decisions("test", metrics=("count", "correct_count", "avg_confidence"))
    assert result == DecisionAggregate({}, {"count": 0.0, "correct_count": 0.0})
    assert store.aggregate_decisions("test", group_by=("category",)) == ()


def test_aggregate_metrics_and_dimensions(seeded: InMemoryGraphStore) -> None:
    result, = seeded.aggregate_decisions("test", metrics=("count", "correct_count", "avg_confidence"))
    assert result.values == {"count": 6.0, "correct_count": 2.0, "avg_confidence": pytest.approx(0.75)}
    assert seeded.aggregate_decisions("test", metrics=())[0].values == {}
    assert seeded.aggregate_decisions("test", metrics=("avg_confidence",))[0].values == {"avg_confidence": pytest.approx(0.75)}
    for dimension, expected in [
        ("category", {"a": 3, "b": 3}), ("action", {"buy": 3, "sell": 3}),
        ("status", {"pending": 2, "confirmed": 2, "overridden": 2}),
    ]:
        kwargs: dict[str, Any] = {"group_by": (dimension,)}
        rows = seeded.aggregate_decisions("test", **kwargs)
        assert {row.dimensions[dimension]: row.values["count"] for row in rows} == expected
    rows = seeded.aggregate_decisions("test", group_by=("category", "status"))
    assert [(row.dimensions, row.values["count"]) for row in rows] == [
        ({"category": "a", "status": "confirmed"}, 2), ({"category": "a", "status": "pending"}, 1),
        ({"category": "b", "status": "overridden"}, 2), ({"category": "b", "status": "pending"}, 1),
    ]


def test_missing_group_distinct_from_empty_string(store: InMemoryGraphStore) -> None:
    write(store, 0)
    write(store, 1, metadata={"regime": ""})
    write(store, 2, metadata={"regime": "a"})
    rows = store.aggregate_decisions("test", group_by=("regime",))
    assert [row.dimensions for row in rows] == [{}, {"regime": ""}, {"regime": "a"}]


@pytest.mark.parametrize("kwargs", [
    {"group_by": ("category", "category")}, {"metrics": ("count", "count")},
    {"group_by": ("actual_action",)}, {"metrics": ("median",)},
])
def test_invalid_aggregate_request(store: InMemoryGraphStore, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        store.aggregate_decisions("test", **kwargs)


def test_aggregate_cardinality_ceiling(store: InMemoryGraphStore) -> None:
    for i in range(1000):
        write(store, i, category=f"c{i:04d}")
    assert len(store.aggregate_decisions("test", group_by=("category",))) == 1000
    write(store, 1000, category="overflow")
    with pytest.raises(ProjectionCardinalityExceeded) as error:
        store.aggregate_decisions("test", group_by=("category",))
    assert (error.value.count, error.value.limit) == (1001, 1000)


def test_feed_event_time_snapshots_and_tombstone(store: InMemoryGraphStore) -> None:
    decision_id = write(store, metadata={"tenant_id": "alpha", "signal_detail": None, "signal_timestamp": ""})
    verify(store, decision_id)
    assert store.archive_old_decisions("test", keep_recent=0) == 1
    page = store.get_decision_changes("test", after_generation=0)
    assert [event["generation"] for event in page.events] == [1, 2, 3]
    assert [event["event_type"] for event in page.events] == ["upsert", "upsert", "delete"]
    assert page.events[0]["payload"]["status"] == "pending"
    assert page.events[0]["payload"]["is_correct"] is None
    assert page.events[1]["payload"]["is_correct"] is True
    tombstone = {"decision_id": decision_id, "domain": "test", "tenant_id": "alpha",
                 "exclude_legacy_signals": True, "_removed": True}
    assert page.events[2]["payload"] == tombstone
    assert all(event["tenant_id"] == "alpha" and event["exclude_legacy_signals"] is True for event in page.events)
    assert store.query_decisions("test").items == ()
    page.events[1]["payload"]["outcome_metadata"]["note"].append("mutated")
    page.events[2]["payload"]["tenant_id"] = "mutated"
    again = store.get_decision_changes("test", after_generation=0)
    assert "mutated" not in repr(again)
    scoring = store.get_decision_changes("test", after_generation=0, projection="scoring")
    assert "metadata" not in scoring.events[0]["payload"]
    assert scoring.events[1]["payload"]["actual_action"] == "hold"
    assert scoring.events[2]["payload"] == tombstone


def test_idempotent_and_rejected_writes_do_not_emit(store: InMemoryGraphStore) -> None:
    decision_id = write(store)
    write(store)
    verify(store, decision_id)
    verify(store, decision_id)
    with pytest.raises(ValueError):
        verify(store, decision_id, False)
    with pytest.raises(ValueError):
        write(store, confidence=0.1)
    with pytest.raises(ValueError):
        write(store, 1, metadata={"created_at": "invalid"})
    page = store.get_decision_changes("test", after_generation=0)
    assert page.current_generation == 2 and len(page.events) == 2
    assert store.count_decisions("test") == 1


def test_raw_update_preserves_routing_and_records_event(store: InMemoryGraphStore) -> None:
    store.write_decision("test", "a", "buy", 0.5, {}, {"decision_id": "raw", "tenant_id": "alpha"})
    store.write_decision("test", "b", "buy", 0.6, {}, {"decision_id": "raw", "tenant_id": "alpha"})
    with pytest.raises(ValueError, match="routing"):
        store.write_decision("test", "b", "buy", 0.6, {}, {"decision_id": "raw", "tenant_id": "beta"})
    page = store.get_decision_changes("test", after_generation=0)
    assert page.current_generation == 2
    assert [event["payload"]["category"] for event in page.events] == ["a", "b"]


@pytest.mark.parametrize("archive_method", ["archive_old_decisions", "archive_decisions"])
def test_archive_retains_legacy_behavior_and_emits(store: InMemoryGraphStore, archive_method: str) -> None:
    for i in range(3):
        write(store, i)
    if archive_method == "archive_old_decisions":
        assert store.archive_old_decisions("test", keep_recent=1) == 2
    else:
        assert store.archive_decisions("test", before=12.0) == 2
    assert store.count_archived("test") == 2 and store.count_decisions("test") == 1
    assert store.get_decision_changes("test", after_generation=3).current_generation == 5


def test_domain_reset_preserves_feed_and_other_domain(store: InMemoryGraphStore) -> None:
    write(store, 0)
    write(store, 1)
    write(store, domain="other")
    store.domain_scoped_reset("test")
    deleted = store.get_decision_changes("test", after_generation=2)
    assert len(deleted.events) == 2 and all(event["event_type"] == "delete" for event in deleted.events)
    assert deleted.current_generation == deleted.next_generation == 4
    assert store.count_decisions("test") == 0 and store.count_decisions("other") == 1
    store.domain_scoped_reset("test")
    write(store, 2)
    assert store.get_decision_changes("test", after_generation=4).current_generation == 5
    assert store.get_decision_changes("other", after_generation=0).current_generation == 1
    store.reset()
    assert store.get_decision_changes("test", after_generation=0).events == ()
    assert store.get_decision_changes("other", after_generation=0).current_generation == 0
    with pytest.raises(ValueError):
        store.get_decision_changes("test", after_generation=5)


def test_feed_paging_and_invisible_watermark(seeded: InMemoryGraphStore) -> None:
    first = seeded.get_decision_changes("test", after_generation=0, limit=3)
    assert len(first.events) == 3 and first.has_more
    assert first.next_generation == first.events[-1]["generation"] == 3
    second = seeded.get_decision_changes("test", after_generation=first.next_generation)
    assert [event["generation"] for event in first.events + second.events] == list(range(1, 11))
    assert second.current_generation == second.next_generation == 10 and not second.has_more
    invisible = seeded.get_decision_changes("test", after_generation=0, filters=DecisionFilter(tenant_id="absent"))
    assert invisible.events == () and invisible.next_generation == 10
    assert not invisible.has_more
    assert seeded.get_decision_changes("empty", after_generation=0).next_generation == 0


def test_feed_routing_filters_apply_to_deletes(seeded: InMemoryGraphStore) -> None:
    seeded.domain_scoped_reset("test")
    after = 0
    events = []
    while True:
        page = seeded.get_decision_changes("test", after_generation=after, limit=1,
            filters=DecisionFilter(tenant_id="alpha", exclude_legacy_signals=True))
        events.extend(page.events)
        if not page.has_more:
            assert page.next_generation == page.current_generation == 16
            break
        after = page.next_generation
    assert {event["decision_id"] for event in events} == {"test-0002", "test-0004"}
    assert sum(event["event_type"] == "delete" for event in events) == 2


@pytest.mark.parametrize("field_name", [
    field.name for field in fields(DecisionFilter)
    if field.name not in {"tenant_id", "exclude_legacy_signals"}
])
def test_feed_rejects_every_nonrouting_filter(store: InMemoryGraphStore, field_name: str) -> None:
    default = getattr(DecisionFilter(), field_name)
    value: Any = ("x",) if isinstance(default, tuple) else (
        False if field_name in {"verified", "correct"} else "ABC" if field_name == "ticker" else 1.0)
    with pytest.raises(ValueError, match="routing"):
        store.get_decision_changes("test", after_generation=0, filters=DecisionFilter(**{field_name: value}))


@pytest.mark.parametrize("kwargs", [
    {"after_generation": -1}, {"after_generation": True}, {"after_generation": 0.5},
    {"after_generation": 1}, {"after_generation": 0, "limit": 0},
    {"after_generation": 0, "limit": 1001}, {"after_generation": 0, "limit": True},
    {"after_generation": 0, "limit": 1.5}, {"after_generation": 0, "projection": "invalid"},
])
def test_invalid_feed_request(store: InMemoryGraphStore, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        store.get_decision_changes("test", **kwargs)


@pytest.mark.parametrize("kwargs", [
    {"projection": "invalid"}, {"as_of_generation": -1}, {"as_of_generation": True},
    {"as_of_generation": 1.5}, {"page": DecisionPageRequest(limit=True)},
    {"page": request_page(limit=1.5)}, {"page": request_page(offset=0.5)},
])
def test_invalid_query_request(store: InMemoryGraphStore, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        store.query_decisions("test", **kwargs)


@pytest.mark.parametrize("field_name", ["created_from", "created_to", "verified_from", "verified_to"])
def test_nonfinite_filter_bound_rejected(store: InMemoryGraphStore, field_name: str) -> None:
    kwargs: dict[str, Any] = {field_name: float("nan")}
    filters = DecisionFilter(**kwargs)
    with pytest.raises(ValueError, match="finite"):
        store.query_decisions("test", filters=filters)
    with pytest.raises(ValueError, match="finite"):
        store.count_decisions("test", filters=filters)
    with pytest.raises(ValueError, match="finite"):
        store.aggregate_decisions("test", filters=filters)


def test_legacy_reads_and_ordering_unchanged(store: InMemoryGraphStore) -> None:
    for i in [2, 0, 1]:
        write(store, i, metadata={"created_at": 10.0})
    verify(store, "test-0000")
    assert [row["decision_id"] for row in store.get_decisions("test")] == ["test-0000", "test-0001", "test-0002"]
    assert [row["decision_id"] for row in store._decision_page("test")] == ["test-0002", "test-0000", "test-0001"]
    assert store.count_verified("test") == 1 and store.count_correct("test") == 1
    assert store.count_decisions("test") == 3
    verified, = store.get_verified_decisions("test")
    assert verified["decision_id"] == "test-0000" and verified["is_correct"] is True
    assert "_generation" not in verified and "_sequence" not in verified


def test_concurrent_idempotent_writes_commit_once(store: InMemoryGraphStore) -> None:
    with ThreadPoolExecutor(max_workers=8) as workers:
        assert set(workers.map(lambda _: write(store), range(32))) == {"test-0000"}
        list(workers.map(lambda _: verify(store, "test-0000"), range(32)))
    page = store.get_decision_changes("test", after_generation=0)
    assert page.current_generation == 2
    assert [event["payload"]["status"] for event in page.events] == ["pending", "confirmed"]


def test_rejected_verification_is_atomic(store: InMemoryGraphStore) -> None:
    decision_id = write(store)
    with pytest.raises(ValueError):
        store.write_outcome(decision_id, "hold", True, {"verified_at": "bad"}, domain="test")
    assert store.get_decision_changes("test", after_generation=0).current_generation == 1
    assert store.query_decisions("test").items[0]["status"] == "pending"
    verify(store, decision_id)
    assert store.get_decision_changes("test", after_generation=0).current_generation == 2


def test_domain_fence_ignores_other_domain_writes(store: InMemoryGraphStore) -> None:
    write(store)
    write(store, domain="other")
    page = store.query_decisions("test", as_of_generation=1)
    assert len(page.items) == 1
    assert store.get_decision_changes("other", after_generation=0).current_generation == 1


def test_feed_scoring_metadata_allowlist_and_mutation_safety(store: InMemoryGraphStore) -> None:
    write(store, metadata={"learning_metadata": {"reward": [1], "secret": 2}})
    page = store.get_decision_changes("test", after_generation=0, projection="scoring")
    assert page.events[0]["payload"]["learning_metadata"] == {"reward": [1]}
    page.events[0]["payload"]["learning_metadata"]["reward"].append(2)
    again = store.get_decision_changes("test", after_generation=0, projection="scoring")
    assert again.events[0]["payload"]["learning_metadata"] == {"reward": [1]}


def test_verified_timestamp_ties_resume_by_id(store: InMemoryGraphStore) -> None:
    for i in [2, 0, 1]:
        verify(store, write(store, i), when=0.0)
    page = store.query_decisions("test", page=DecisionPageRequest(
        order_by="verified_at", descending=False, limit=2))
    assert [row["decision_id"] for row in page.items] == ["test-0000", "test-0001"]
    assert page.items[0]["verified_at"] == 0.0
    last = store.query_decisions("test", page=DecisionPageRequest(
        order_by="verified_at", descending=False, after=page.next_cursor, limit=2))
    assert [row["decision_id"] for row in last.items] == ["test-0002"]


def test_concurrent_read_watermark_never_leads_committed_events(store: InMemoryGraphStore) -> None:
    def mutate() -> None:
        for i in range(100):
            verify(store, write(store, i))
    with ThreadPoolExecutor(max_workers=1) as workers:
        pending = workers.submit(mutate)
        while True:
            page = store.get_decision_changes("test", after_generation=0)
            assert [event["generation"] for event in page.events] == list(range(1, page.current_generation + 1))
            if pending.done():
                break
        pending.result()
    assert store.get_decision_changes("test", after_generation=0).current_generation == 200


@pytest.mark.parametrize("writer", ["raw", "governed"])
@pytest.mark.parametrize(("pnl", "size", "expected_pnl", "expected_size"), [
    ("12.50", "2", 12.5, 2),
    (12, 2.9, 12.0, 2),
    (None, None, 0.0, 0),
    ("bad", "bad", 0.0, 0),
    (-3.5, "-2", -3.5, -2),
    ("0", 0, 0.0, 0),
])
def test_journal_numeric_normalization_on_writes_and_feed(
    store: InMemoryGraphStore, writer: str, pnl: Any, size: Any,
    expected_pnl: float, expected_size: int,
) -> None:
    metadata = {"pnl": pnl, "size": size}
    if writer == "raw":
        decision_id = store.write_decision("test", "a", "buy", 0.75, {}, metadata)
    else:
        decision_id = write(store, metadata=metadata)
    for generation in (1, 2):
        if generation == 2:
            verify(store, decision_id)
        direct = store.query_decisions("test", projection="journal").items[0]
        event = store.get_decision_changes(
            "test", after_generation=generation - 1, projection="journal",
        ).events[0]
        assert event["payload"] == direct
        assert type(direct["pnl"]) is float and direct["pnl"] == expected_pnl
        assert type(direct["size"]) is int and direct["size"] == expected_size
        assert event["generation"] == generation
    # Coercion must not destroy the original evidence in full projections.
    original = store.query_decisions("test", projection="full").items[0]["metadata"]
    assert original["pnl"] == pnl and original["size"] == size


@pytest.mark.parametrize(("metadata", "reflection", "strategy"), [
    ({"reflection": "ref", "strategy": "value"}, "ref", "value"),
    ({"notes": "review", "thesis_type": "momentum"}, "review", "momentum"),
    ({"reflection": "ref", "notes": "notes", "strategy_tag": "canonical", "strategy": "alias"},
     "ref", "canonical"),
])
def test_journal_text_aliases_and_sorted_tags(
    store: InMemoryGraphStore, metadata: dict[str, Any], reflection: str, strategy: str,
) -> None:
    write(store, metadata={**metadata, "tags": [" z ", "a", "", " z", "a ", "A"]})
    direct = store.query_decisions("test", projection="journal").items[0]
    assert direct["reflection"] == reflection
    assert direct["strategy_tag"] == strategy
    assert direct["tags"] == ["A", "a", "z"]
    assert store.get_decision_changes("test", after_generation=0, projection="journal").events[0]["payload"] == direct


def test_journal_invalid_pnl_falls_back_and_normalizes_other_fields(store: InMemoryGraphStore) -> None:
    decision_id = write(store, metadata={
        "pnl": "invalid", "pnl_dollars": "12.5", "shares": "3",
        "entry_price": "4.25", "exit_price": "5.5", "date": "2026-01-01",
        "entry_id": 42,
    })
    direct = store.query_decisions("test", projection="journal").items[0]
    assert (direct["pnl"], direct["size"], direct["entry_price"], direct["exit_price"]) == (12.5, 3, 4.25, 5.5)
    assert (direct["trade_id"], direct["entry_id"], direct["entry_time"]) == (decision_id, "42", "2026-01-01")
    assert direct["tags"] == []
    assert store.get_decision_changes("test", after_generation=0, projection="journal").events[0]["payload"] == direct


@pytest.mark.parametrize(("bounds", "expected"), [
    ({"confidence_min": 0.0, "confidence_max": 1.0}, {0, 1, 2}),
    ({"confidence_min": 0.0}, {0, 1, 2, 4}),
    ({"confidence_max": 1.0}, {0, 1, 2, 5}),
])
def test_nonfinite_confidence_range_parity(
    store: InMemoryGraphStore, bounds: dict[str, float], expected: set[int],
) -> None:
    for index, confidence in enumerate([0.0, 0.5, 1.0, float("nan"), float("inf"), float("-inf")]):
        store.write_decision("test", "a", "buy", confidence, {}, {"decision_id": str(index)})
    filters = DecisionFilter(**bounds)
    assert ids(store, filters) == {str(index) for index in expected}
    assert store.count_decisions("test", filters=filters) == len(expected)
    aggregate, = store.aggregate_decisions("test", filters=filters, metrics=("count", "avg_confidence"))
    assert aggregate.values["count"] == len(expected)
    # One-sided inclusive ranges legitimately admit the matching infinity;
    # a two-sided finite range admits neither infinity nor NaN.
    expected_average = 0.5 if len(expected) == 3 else float("inf") if 4 in expected else float("-inf")
    assert aggregate.values["avg_confidence"] == expected_average
