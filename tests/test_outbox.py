from __future__ import annotations

import hashlib
import json
from datetime import datetime

import pytest

from copilot_sdk.graph import InMemoryGraphStore


class NonJsonValue:
    def __str__(self) -> str:
        return "non-json-value"


def _canonical_hash(payload: dict) -> tuple[str, str]:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_in_memory_enqueue_creates_pending_outbox_entry() -> None:
    store = InMemoryGraphStore(domain="test")
    payload = {"b": 2, "a": 1}
    payload_json, payload_hash = _canonical_hash(payload)

    outbox_id = store.enqueue_to_outbox(
        "test",
        "write_governed_decision",
        "DEC-1",
        payload,
        causal_decision_id="DEC-1",
    )

    assert outbox_id == 1
    assert len(store._outbox) == 1
    row = store._outbox[0]
    assert row["outbox_id"] == outbox_id
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


def test_in_memory_enqueue_is_canonical_and_idempotent() -> None:
    store = InMemoryGraphStore(domain="test")
    first = store.enqueue_to_outbox("test", "operation", "KEY-1", {"a": 1, "b": 2})
    replay = store.enqueue_to_outbox("test", "operation", "KEY-1", {"b": 2, "a": 1})

    assert replay == first
    assert len(store._outbox) == 1


def test_in_memory_non_json_native_payload_uses_default_str() -> None:
    store = InMemoryGraphStore(domain="test")
    payload = {"value": NonJsonValue()}
    payload_json, payload_hash = _canonical_hash(payload)

    first = store.enqueue_to_outbox("s2p", "centroid", "key-nonjson", payload)
    replay = store.enqueue_to_outbox("s2p", "centroid", "key-nonjson", payload)

    assert replay == first
    assert len(store._outbox) == 1
    assert store._outbox[0]["payload_json"] == payload_json
    assert store._outbox[0]["payload_hash"] == payload_hash
    assert "non-json-value" in store._outbox[0]["payload_json"]


def test_in_memory_identity_includes_domain_key_and_operation() -> None:
    store = InMemoryGraphStore(domain="test")

    base = store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1})
    other_domain = store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 1})
    other_key = store.enqueue_to_outbox("test", "operation", "KEY-2", {"value": 1})
    other_operation = store.enqueue_to_outbox("test", "other_operation", "KEY-1", {"value": 1})

    assert [base, other_domain, other_key, other_operation] == [1, 2, 3, 4]
    assert len(store._outbox) == 4


def test_in_memory_conflict_quarantines_new_payload_and_preserves_original() -> None:
    store = InMemoryGraphStore(domain="test")
    original_payload = {"value": "original"}
    new_payload = {"value": "new"}
    _, original_hash = _canonical_hash(original_payload)
    new_payload_json, new_hash = _canonical_hash(new_payload)

    original_id = store.enqueue_to_outbox("test", "operation", "KEY-1", original_payload)
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        store.enqueue_to_outbox("test", "operation", "KEY-1", new_payload)

    assert len(store._outbox) == 1
    assert store._outbox[0]["outbox_id"] == original_id
    assert store._outbox[0]["payload_hash"] == original_hash
    assert len(store._outbox_quarantine) == 1
    quarantine = store._outbox_quarantine[0]
    assert quarantine["domain"] == "test"
    assert quarantine["outbox_id"] == original_id
    assert quarantine["existing_payload_hash"] == original_hash
    assert quarantine["new_payload_hash"] == new_hash
    assert quarantine["new_payload_json"] == new_payload_json
    assert quarantine["reason"] == "payload_hash_conflict"


def test_in_memory_domain_reset_clears_only_matching_outbox_and_quarantine() -> None:
    store = InMemoryGraphStore(domain="test")
    store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1})
    store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 1})
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 2})
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        store.enqueue_to_outbox("other", "operation", "KEY-1", {"value": 2})

    store.domain_scoped_reset("test")

    assert [row["domain"] for row in store._outbox] == ["other"]
    assert [row["domain"] for row in store._outbox_quarantine] == ["other"]


def test_in_memory_global_reset_clears_outbox_and_quarantine() -> None:
    store = InMemoryGraphStore(domain="test")
    store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1})
    with pytest.raises(ValueError, match="payload_hash_conflict"):
        store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 2})

    store.reset()

    assert store._outbox == []
    assert store._outbox_quarantine == []
    assert store.enqueue_to_outbox("test", "operation", "KEY-1", {"value": 1}) == 1
