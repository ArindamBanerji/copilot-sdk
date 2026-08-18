from __future__ import annotations

import json
import threading

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.twin import FrozenSnapshot, FrozenTwin, FrozenTwinStore, create_frozen_twin_router


def _scorer() -> ProfileScorer:
    centroids = np.full((2, 3, 4), 0.5, dtype=np.float64)
    centroids[0, 0] = [0.1, 0.2, 0.3, 0.4]
    centroids[0, 1] = [0.8, 0.7, 0.6, 0.5]
    return ProfileScorer(mu=centroids, actions=["a", "b", "c"], categories=["one", "two"])


def _frozen(tmp_path) -> tuple[FrozenTwin, ProfileScorer, FrozenSnapshot]:
    scorer = _scorer()
    twin = FrozenTwin(FrozenTwinStore(tmp_path))
    snapshot = twin.freeze(scorer, {"phase": "GREEN", "alpha": 0.05, "q": 1.0, "V": 0}, 42.0, "test")
    return twin, scorer, snapshot


def test_ft_01_freeze_creates_snapshot_with_correct_state(tmp_path):
    twin, scorer, snapshot = _frozen(tmp_path)

    assert twin.is_frozen()
    assert snapshot.verify_integrity()
    assert np.array_equal(np.asarray(snapshot.scorer_state["centroids"]), scorer.mu)
    assert snapshot.metadata["copilot"] == "test"


def test_ft_02_freeze_twice_raises(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)

    with pytest.raises(FileExistsError):
        twin.freeze(scorer, {}, 0.0, "test")


def test_ft_03_frozen_score_matches_live_at_freeze_time(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)
    factor_vector = np.array([0.15, 0.25, 0.35, 0.45])

    live = scorer.score(factor_vector, 0)
    frozen = twin.score_frozen(factor_vector, 0)

    assert live.action_index == frozen.action_index
    assert np.allclose(live.probabilities, frozen.probabilities)
    assert np.allclose(live.distances, frozen.distances)


def test_ft_04_frozen_score_differs_after_live_learning(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)
    factor_vector = np.zeros(4, dtype=np.float64)
    before = twin.score_frozen(factor_vector, 0)

    scorer.update(factor_vector, 0, 0, True)
    live = scorer.score(factor_vector, 0)
    frozen = twin.score_frozen(factor_vector, 0)

    assert not np.allclose(live.probabilities, frozen.probabilities)
    assert np.allclose(before.probabilities, frozen.probabilities)


def test_ft_05_parallel_score_returns_both_results_and_delta(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)

    result = twin.score_parallel([0.2, 0.3, 0.4, 0.5], 0, scorer)

    assert result.live_result.action_index == result.frozen_result.action_index
    assert result.delta == pytest.approx(0.0)


def test_ft_06_drift_is_zero_at_freeze_time(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)

    report = twin.get_drift_report(scorer)

    assert report.centroid_drift == pytest.approx(0.0)
    assert report.weight_drift == pytest.approx(0.0)
    assert report.decision_count_since_freeze == 0


def test_ft_07_drift_is_nonzero_after_learning(tmp_path):
    twin, scorer, _ = _frozen(tmp_path)
    scorer.update(np.zeros(4, dtype=np.float64), 0, 0, True)

    report = twin.get_drift_report(scorer)

    assert report.centroid_drift > 0
    assert report.decision_count_since_freeze == 1


def test_ft_08_snapshot_survives_twin_reinstantiation(tmp_path):
    _, scorer, original = _frozen(tmp_path)
    restarted = FrozenTwin(FrozenTwinStore(tmp_path))
    loaded = restarted.load("test")

    assert loaded.checksum == original.checksum
    assert restarted.score_frozen([0.2, 0.3, 0.4, 0.5], 0).action_index == scorer.score([0.2, 0.3, 0.4, 0.5], 0).action_index


def test_ft_09_checksum_detects_corruption(tmp_path):
    _, _, snapshot = _frozen(tmp_path)
    path = tmp_path / "test.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["iks_value"] = 99.0
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        FrozenTwinStore(tmp_path).load("test")


def test_ft_10_frozen_score_never_changes_snapshot(tmp_path):
    twin, _, snapshot = _frozen(tmp_path)
    before = snapshot.to_json()

    for _ in range(10):
        twin.score_frozen([0.2, 0.3, 0.4, 0.5], 0)

    assert snapshot.to_json() == before
    assert snapshot.verify_integrity()


def test_ft_11_delete_requires_explicit_confirmation(tmp_path):
    _, _, _ = _frozen(tmp_path)
    store = FrozenTwinStore(tmp_path)

    with pytest.raises(PermissionError):
        store.delete("test")
    store.delete("test", confirmation="test")
    assert not store.exists("test")


def test_ft_12_uses_in_memory_graph_store(tmp_path):
    twin, _, _ = _frozen(tmp_path)

    assert isinstance(twin.graph_store, InMemoryGraphStore)


def test_ft_13_production_scale_round_trip(tmp_path):
    scorer = ProfileScorer(mu=np.random.default_rng(7).random((6, 4, 6)), actions=[f"a{i}" for i in range(4)])
    twin = FrozenTwin(FrozenTwinStore(tmp_path))
    snapshot = twin.freeze(
        scorer,
        {"alpha": 0.05, "q": 0.9, "V": 12, "theta_min": 0.2, "phase": "GREEN"},
        0.75,
        "scale",
    )
    restored = FrozenSnapshot.from_json(snapshot.to_json())

    assert np.linalg.norm(np.asarray(restored.scorer_state["centroids"]) - scorer.mu) == pytest.approx(0.0)
    assert restored.conservation_state["phase"] == "GREEN"


def _router_client(tmp_path) -> tuple[TestClient, ProfileScorer]:
    scorer = _scorer()
    twin = FrozenTwin(FrozenTwinStore(tmp_path))
    app = FastAPI()
    app.include_router(create_frozen_twin_router(twin, scorer))
    return TestClient(app), scorer


def test_ft_14_router_status_unfrozen_and_frozen(tmp_path):
    client, scorer = _router_client(tmp_path)

    assert client.get("/api/twin/status").json()["frozen"] is False
    response = client.post("/api/twin/freeze", json={"copilot": "router", "iks": 1.0, "conservation_state": {"phase": "GREEN"}})
    assert response.status_code == 201
    assert client.get("/api/twin/status").json()["frozen"] is True
    assert scorer.decision_count == 0


def test_ft_15_router_drift_reports_learning(tmp_path):
    client, scorer = _router_client(tmp_path)
    client.post("/api/twin/freeze", json={"copilot": "router", "iks": 1.0})
    scorer.update(np.zeros(4, dtype=np.float64), 0, 0, True)

    response = client.get("/api/twin/drift")

    assert response.status_code == 200
    assert response.json()["centroid_drift"] > 0


def test_ft_16_router_freeze_creates_snapshot(tmp_path):
    client, _ = _router_client(tmp_path)

    response = client.post("/api/twin/freeze", json={"copilot": "router", "iks": 1.0})

    assert response.status_code == 201
    assert response.json()["frozen"] is True


def test_ft_17_router_second_freeze_returns_409(tmp_path):
    client, _ = _router_client(tmp_path)
    body = {"copilot": "router", "iks": 1.0}

    assert client.post("/api/twin/freeze", json=body).status_code == 201
    assert client.post("/api/twin/freeze", json=body).status_code == 409


def test_ft_18_concurrent_freeze_attempts_only_one_succeeds(tmp_path):
    scorer = _scorer()
    store = FrozenTwinStore(tmp_path)
    results: list[str] = []
    lock = threading.Lock()

    def attempt() -> None:
        try:
            FrozenTwin(store).freeze(scorer, {}, 0.0, "concurrent")
            outcome = "success"
        except FileExistsError:
            outcome = "exists"
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count("success") == 1
    assert results.count("exists") == 7


def test_ft_19_iks_is_separate_from_snapshot_state(tmp_path):
    twin, _, snapshot = _frozen(tmp_path)
    original_checksum = snapshot.checksum

    external_iks = 999.0
    assert external_iks != snapshot.iks_value
    assert snapshot.checksum == original_checksum
    assert twin.get_snapshot().iks_value == 42.0
