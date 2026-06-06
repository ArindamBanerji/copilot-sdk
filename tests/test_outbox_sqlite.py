from __future__ import annotations

import hashlib
import json
from datetime import datetime

import pytest

from copilot_sdk.graph import SQLiteGraphStore


class NonJsonValue:
    def __str__(self) -> str:
        return "non-json-value"


def _canonical_hash(payload: dict) -> tuple[str, str]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@pytest.fixture()
def sqlite_store(tmp_path):
    store = SQLiteGraphStore(tmp_path / "outbox.sqlite", domain="test")
    try:
        yield store
    finally:
        store.close()


def test_sqlite_outbox_tables_and_columns_exist(sqlite_store) -> None:
    tables = {
        row["name"]
        for row in sqlite_store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "outbox" in tables
    assert "outbox_quarantine" in tables

    outbox_columns = {
        row["name"]
        for row in sqlite_store.connection.execute("PRAGMA table_info(outbox)").fetchall()
    }
    assert {
        "outbox_id",
        "domain",
        "operation_type",
        "target_key",
        "payload_json",
        "payload_hash",
        "causal_decision_id",
        "status",
        "attempt_count",
        "last_error_redacted",
        "schema_version",
        "created_at",
        "updated_at",
        "replayed_at",
    } <= outbox_columns

    quarantine_columns = {
        row["name"]
        for row in sqlite_store.connection.execute(
            "PRAGMA table_info(outbox_quarantine)"
        ).fetchall()
    }
    assert {
        "quarantine_id",
        "domain",
        "outbox_id",
        "operation_type",
        "target_key",
        "existing_payload_hash",
        "new_payload_hash",
        "new_payload_json",
        "reason",
        "quarantined_at",
        "resolved_at",
        "resolution",
    } <= quarantine_columns


def test_sqlite_unique_identity_is_functionally_enforced(sqlite_store) -> None:
    first = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"a": 1})
    second = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"a": 1})

    assert second == first
    count = sqlite_store.connection.execute(
        "SELECT COUNT(*) AS n FROM outbox WHERE domain = ?",
        ("test",),
    ).fetchone()["n"]
    assert int(count) == 1


def test_sqlite_create_tables_is_idempotent(sqlite_store) -> None:
    sqlite_store._create_tables()
    sqlite_store._ensure_migrations()

    outbox_id = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"a": 1})
    assert outbox_id == 1


def test_sqlite_enqueue_creates_pending_outbox_entry(sqlite_store) -> None:
    payload = {"b": 2, "a": 1}
    payload_json, payload_hash = _canonical_hash(payload)

    outbox_id = sqlite_store.enqueue_to_outbox(
        "test",
        "write_governed_decision",
        "DEC-1",
        payload,
        causal_decision_id="DEC-1",
    )

    row = sqlite_store.connection.execute(
        "SELECT * FROM outbox WHERE outbox_id = ?",
        (outbox_id,),
    ).fetchone()
    assert row["domain"] == "test"
    assert row["causal_decision_id"] == "DEC-1"
    assert row["payload_json"] == payload_json
    assert row["payload_hash"] == payload_hash
    assert row["schema_version"] == 1
    assert row["status"] == "pending"
    assert row["attempt_count"] == 0
    assert row["replayed_at"] is None
    datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))


def test_sqlite_non_json_native_payload_uses_default_str(sqlite_store) -> None:
    payload = {"value": NonJsonValue()}
    payload_json, payload_hash = _canonical_hash(payload)

    first = sqlite_store.enqueue_to_outbox("s2p", "centroid", "key-nonjson", payload)
    replay = sqlite_store.enqueue_to_outbox("s2p", "centroid", "key-nonjson", payload)

    row = sqlite_store.connection.execute(
        "SELECT payload_json, payload_hash FROM outbox WHERE outbox_id = ?",
        (first,),
    ).fetchone()
    assert replay == first
    assert row["payload_json"] == payload_json
    assert row["payload_hash"] == payload_hash
    assert "non-json-value" in row["payload_json"]


def test_sqlite_identity_includes_domain_key_and_operation(sqlite_store) -> None:
    base = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1})
    other_domain = sqlite_store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 1})
    other_key = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-2", {"value": 1})
    other_operation = sqlite_store.enqueue_to_outbox(
        "test",
        "other_operation",
        "KEY-1",
        {"value": 1},
    )

    assert [base, other_domain, other_key, other_operation] == [1, 2, 3, 4]


def test_sqlite_conflict_quarantines_new_payload_and_preserves_original(sqlite_store) -> None:
    original_payload = {"value": "original"}
    new_payload = {"value": "new"}
    _, original_hash = _canonical_hash(original_payload)
    new_payload_json, new_hash = _canonical_hash(new_payload)

    original_id = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", original_payload)
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", new_payload)

    outbox_rows = sqlite_store.connection.execute(
        "SELECT * FROM outbox WHERE domain = ? AND operation_type = ? AND target_key = ?",
        ("test", "operation", "KEY-1"),
    ).fetchall()
    assert len(outbox_rows) == 1
    assert outbox_rows[0]["outbox_id"] == original_id
    assert outbox_rows[0]["payload_hash"] == original_hash

    quarantine = sqlite_store.connection.execute(
        "SELECT * FROM outbox_quarantine WHERE domain = ?",
        ("test",),
    ).fetchone()
    assert quarantine["outbox_id"] == original_id
    assert quarantine["existing_payload_hash"] == original_hash
    assert quarantine["new_payload_hash"] == new_hash
    assert quarantine["new_payload_json"] == new_payload_json
    assert quarantine["reason"] == "payload_hash_conflict"


def test_sqlite_domain_reset_clears_only_matching_outbox_and_quarantine(sqlite_store) -> None:
    sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1})
    sqlite_store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 1})
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 2})
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        sqlite_store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 2})

    sqlite_store.domain_scoped_reset("test")

    outbox_domains = [
        row["domain"]
        for row in sqlite_store.connection.execute(
            "SELECT domain FROM outbox ORDER BY outbox_id"
        ).fetchall()
    ]
    quarantine_domains = [
        row["domain"]
        for row in sqlite_store.connection.execute(
            "SELECT domain FROM outbox_quarantine ORDER BY quarantine_id"
        ).fetchall()
    ]
    assert outbox_domains == ["other"]
    assert quarantine_domains == ["other"]


def test_sqlite_same_payload_different_domain_creates_different_id(sqlite_store) -> None:
    first = sqlite_store.enqueue_to_outbox("test", "operation", "KEY-1", {"a": 1})
    second = sqlite_store.enqueue_to_outbox("other", "operation", "KEY-1", {"a": 1})

    assert second != first
