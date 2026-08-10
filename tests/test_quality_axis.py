from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _quality_payload(
    *,
    verified: int,
    correct: int,
    window_end: str = "2026-08-07T00:00:00+00:00",
) -> dict[str, Any]:
    return {
        "quality_window_size": 400,
        "quality_verified_count": verified,
        "quality_correct_count": correct,
        "rolling_accuracy": correct / verified if verified else None,
        "quality_window_end": window_end,
        "quality_policy_version": "quality.v1",
    }


def _write_v2(store: Any, checkpoint_id: str, **quality: Any) -> None:
    store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain="quality-test",
        category="learned",
        action="confirm",
        centroids=[[0.1, 0.2]],
        decisions_count=400,
        verified_count=quality.get("quality_verified_count", 0),
        iks=12.5,
        shape=[1, 2],
        factor_names_hash="quality-hash",
        **quality,
    )


def _history_client(store: Any) -> TestClient:
    app = FastAPI()
    mount_self_computation_router(app, store, domain="quality-test")
    return TestClient(app)


def test_checkpoint_carries_quality_fields() -> None:
    store = InMemoryGraphStore()
    _write_v2(store, "quality-1", **_quality_payload(verified=8, correct=6))

    checkpoint = store.get_centroid_checkpoints("quality-test", include_v2=True)[0]

    assert checkpoint["quality_window_size"] == 400
    assert checkpoint["quality_verified_count"] == 8
    assert checkpoint["quality_correct_count"] == 6
    assert checkpoint["rolling_accuracy"] == 0.75
    assert checkpoint["quality_window_end"] == "2026-08-07T00:00:00+00:00"
    assert checkpoint["quality_policy_version"] == "quality.v1"


def test_legacy_checkpoint_quality_is_null() -> None:
    store = InMemoryGraphStore()
    store.save_centroids("quality-test", "warm_start", [[0.1, 0.2]])

    response = _history_client(store).get("/api/self/centroid-history")

    assert response.status_code == 200
    assert response.json()["checkpoints"][0]["quality"] is None


def test_quality_zero_verified_is_null() -> None:
    store = InMemoryGraphStore()
    _write_v2(store, "quality-zero", **_quality_payload(verified=0, correct=0))

    checkpoint = store.get_centroid_checkpoints("quality-test", include_v2=True)[0]

    assert checkpoint["quality_verified_count"] == 0
    assert checkpoint["rolling_accuracy"] is None


def test_quality_exact_400_window() -> None:
    store = InMemoryGraphStore()
    for index in range(400):
        decision_id = store.write_decision(
            "test",
            category="category",
            action="confirm",
            confidence=0.9,
            factors={"factor": 1.0},
        )
        store.write_outcome(decision_id, "confirm", index < 300, domain="test")

    scorer = CompoundingScorer.from_preset(
        "s2p", graph_store=store, profile="test", enable_rl=False
    )
    quality = scorer._checkpoint_quality(None)

    assert quality["quality_window_size"] == 400
    assert quality["quality_verified_count"] == 400
    assert quality["quality_correct_count"] == 300
    assert quality["rolling_accuracy"] == 0.75


def test_quality_policy_version() -> None:
    store = InMemoryGraphStore()
    _write_v2(store, "quality-policy", **_quality_payload(verified=1, correct=1))

    checkpoint = store.get_centroid_checkpoints("quality-test", include_v2=True)[0]

    assert checkpoint["quality_policy_version"] == "quality.v1"


def test_quality_in_history_response() -> None:
    store = InMemoryGraphStore()
    store.save_centroids("quality-test", "warm_start", [[0.1, 0.2]])
    _write_v2(store, "quality-response", **_quality_payload(verified=4, correct=3))

    response = _history_client(store).get("/api/self/centroid-history")
    body = response.json()
    by_id = {item.get("checkpoint_id"): item for item in body["checkpoints"]}

    assert body["total"] == 2
    assert by_id[None]["quality"] is None
    assert by_id["quality-response"]["quality"] == {
        "window_size": 400,
        "verified_count": 4,
        "correct_count": 3,
        "rolling_accuracy": 0.75,
        "window_end": "2026-08-07T00:00:00+00:00",
        "policy_version": "quality.v1",
    }


def test_quality_cross_adapter_parity(tmp_path: Any) -> None:
    stores = [
        InMemoryGraphStore(),
        SQLiteGraphStore(str(tmp_path / "quality.db")),
    ]
    values = []
    for store in stores:
        _write_v2(store, "quality-parity", **_quality_payload(verified=20, correct=15))
        checkpoint = store.get_centroid_checkpoints("quality-test", include_v2=True)[0]
        values.append(
            (
                checkpoint["quality_window_size"],
                checkpoint["quality_verified_count"],
                checkpoint["quality_correct_count"],
                checkpoint["rolling_accuracy"],
                checkpoint["quality_window_end"],
                checkpoint["quality_policy_version"],
            )
        )

    assert values[0] == values[1]
