from __future__ import annotations

from typing import Any

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


DOMAIN = "trading"
ARCHIVE_FIELDS = {
    "decision_id",
    "domain",
    "category",
    "category_index",
    "recommended_action",
    "recommended_index",
    "confidence",
    "factor_vector",
    "probabilities",
    "created_at",
    "actual_action",
    "actual_index",
    "is_correct",
    "verified_at",
    "archived_at",
    "archive_reason",
}


def _write_decision(store: Any, index: int) -> str:
    decision_id = f"DEC-{index}"
    store.write_governed_decision(
        decision_id=decision_id,
        domain=DOMAIN,
        category="trend",
        category_index=0,
        recommended_action="buy",
        recommended_index=0,
        confidence=0.5 + index / 100,
        probabilities=[0.75, 0.25],
        factor_vector=[float(index), 0.5],
        factor_names=["signal", "risk"],
        metadata={"created_at": float(index)},
    )
    return decision_id


def _seed_and_archive(store: Any) -> list[str]:
    ids = [_write_decision(store, index) for index in range(5)]
    store.write_outcome(
        ids[0],
        "buy",
        True,
        metadata={"actual_index": 0, "verified_at": 10.0},
        domain=DOMAIN,
    )
    assert store.archive_old_decisions(DOMAIN, keep_recent=2) == 3
    return ids


def test_sqlite_archive_reader_returns_normalized_records_in_archive_order(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "archive.db"), domain=DOMAIN)
    try:
        ids = _seed_and_archive(store)
        archived = store.get_archived_decisions(DOMAIN)
    finally:
        store.close()

    assert [record["decision_id"] for record in archived] == ids[:3]
    assert all(ARCHIVE_FIELDS <= record.keys() for record in archived)
    assert [record["created_at"] for record in archived] == [0.0, 1.0, 2.0]


def test_sqlite_archive_reader_returns_empty_when_nothing_is_archived(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "empty.db"), domain=DOMAIN)
    try:
        _write_decision(store, 1)
        assert store.get_archived_decisions(DOMAIN) == []
    finally:
        store.close()


def test_sqlite_archive_reader_preserves_denormalized_outcome_fields(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "outcome.db"), domain=DOMAIN)
    try:
        _seed_and_archive(store)
        archived = store.get_archived_decisions(DOMAIN)
    finally:
        store.close()

    first = archived[0]
    assert first["actual_action"] == "buy"
    assert first["actual_index"] == 0
    assert first["is_correct"] is True
    assert first["verified_at"] == 10.0


def test_in_memory_archive_reader_matches_normalized_contract() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    ids = _seed_and_archive(store)

    archived = store.get_archived_decisions(DOMAIN)

    assert [record["decision_id"] for record in archived] == ids[:3]
    assert all(ARCHIVE_FIELDS <= record.keys() for record in archived)
    assert archived[0]["actual_action"] == "buy"
    assert archived[0]["is_correct"] is True


def test_dual_write_archive_reader_delegates_to_primary(tmp_path) -> None:
    primary = SQLiteGraphStore(str(tmp_path / "primary.db"), domain=DOMAIN)
    secondary = InMemoryGraphStore(domain=DOMAIN)
    store = DualWriteStore(primary, secondary)
    try:
        _seed_and_archive(store)
        assert store.get_archived_decisions(DOMAIN) == primary.get_archived_decisions(DOMAIN)
    finally:
        store.close()


def test_archive_reader_decodes_numeric_json_fields_to_lists(tmp_path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "normalized.db"), domain=DOMAIN)
    try:
        _seed_and_archive(store)
        record = store.get_archived_decisions(DOMAIN)[0]
    finally:
        store.close()

    assert record["factor_vector"] == [0.0, 0.5]
    assert record["probabilities"] == [0.75, 0.25]
    assert isinstance(record["confidence"], float)
