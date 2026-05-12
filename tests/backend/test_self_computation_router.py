from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore


def _client(store: InMemoryGraphStore | None = None) -> TestClient:
    app = FastAPI()
    mount_self_computation_router(app, store or InMemoryGraphStore())
    return TestClient(app)


def _seed_store() -> tuple[InMemoryGraphStore, dict[str, str]]:
    store = InMemoryGraphStore()
    d1 = store.write_decision(
        entity_id="entity-1",
        category="schema",
        action="investigate",
        confidence=0.91,
        factors={"severity": 0.8},
        metadata={"decision_id": "d1"},
    )
    d2 = store.write_decision(
        entity_id="entity-2",
        category="quality",
        action="suppress",
        confidence=0.62,
        factors={"severity": 0.5},
        metadata={"decision_id": "d2"},
    )
    d3 = store.write_decision(
        entity_id="entity-3",
        category="schema",
        action="escalate",
        confidence=0.73,
        factors={"severity": 0.7},
        metadata={"decision_id": "d3"},
    )
    store.write_outcome(d1, actual_action="investigate", is_correct=True)
    store.write_outcome(d2, actual_action="escalate", is_correct=False)
    store.save_centroids(d1, "schema", {"schema": [0.1, 0.2]}, metadata={"iks": 10.0})
    store.save_centroids(d2, "quality", {"quality": [0.3, 0.4]}, metadata={"iks": 12.0})
    return store, {"d1": d1, "d2": d2, "d3": d3}


def test_centroid_history_returns_checkpoints() -> None:
    store, _ = _seed_store()
    response = _client(store).get("/api/self/centroid-history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["decision_id"] for item in payload["checkpoints"]] == ["d1", "d2"]


def test_centroid_history_limit_works() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/centroid-history?limit=1").json()

    assert payload["total"] == 1
    assert payload["checkpoints"][0]["decision_id"] == "d2"


def test_centroid_history_empty_store() -> None:
    payload = _client().get("/api/self/centroid-history").json()

    assert payload == {"checkpoints": [], "total": 0}


def test_centroid_history_normalizes_numpy_like_centroids() -> None:
    class ArrayLike:
        def tolist(self) -> list[list[float]]:
            return [[0.1, 0.2], [0.3, 0.4]]

    class ScalarLike:
        def item(self) -> float:
            return 0.75

    class GraphStoreWithArrayCheckpoint(InMemoryGraphStore):
        def get_centroid_checkpoints(self, limit: int = 50) -> list[dict]:
            return [
                {
                    "decision_id": "d-array",
                    "category": "schema",
                    "centroids": ArrayLike(),
                    "metadata": {"iks": ScalarLike()},
                }
            ]

    response = _client(GraphStoreWithArrayCheckpoint()).get("/api/self/centroid-history")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    checkpoint = payload["checkpoints"][0]
    assert checkpoint["centroids"] == [[0.1, 0.2], [0.3, 0.4]]
    assert checkpoint["metadata"]["iks"] == 0.75


def test_accuracy_by_category_computes_accuracy() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/accuracy-by-category").json()

    assert payload["overall_verified"] == 2
    categories = {item["category"]: item for item in payload["categories"]}
    assert categories["schema"] == {
        "category": "schema",
        "accuracy": 1.0,
        "total": 1,
        "correct": 1,
        "alert": False,
    }
    assert categories["quality"]["accuracy"] == 0.0
    assert categories["quality"]["alert"] is True


def test_accuracy_by_category_custom_threshold() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/accuracy-by-category?threshold=1.0").json()

    categories = {item["category"]: item for item in payload["categories"]}
    assert categories["schema"]["alert"] is False
    assert payload["threshold"] == 1.0


def test_accuracy_by_category_empty_store() -> None:
    payload = _client().get("/api/self/accuracy-by-category").json()

    assert payload == {"categories": [], "threshold": 0.7, "overall_verified": 0}


def test_decisions_returns_all() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decisions").json()

    assert payload["total"] == 3
    assert [item["decision_id"] for item in payload["decisions"]] == ["d1", "d2", "d3"]


def test_decisions_category_filter() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decisions?category=schema").json()

    assert payload["total"] == 2
    assert all(item["category"] == "schema" for item in payload["decisions"])


def test_decisions_action_filter_matches_recommended_or_actual() -> None:
    store, _ = _seed_store()
    client = _client(store)

    recommended = client.get("/api/self/decisions?action=suppress").json()
    actual = client.get("/api/self/decisions?action=escalate").json()

    assert [item["decision_id"] for item in recommended["decisions"]] == ["d2"]
    assert {item["decision_id"] for item in actual["decisions"]} == {"d2", "d3"}


def test_decisions_verified_only() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decisions?verified_only=true").json()

    assert payload["total"] == 2
    assert all("actual_action" in item for item in payload["decisions"])


def test_decisions_limit_is_applied_after_total() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decisions?limit=2").json()

    assert payload["total"] == 3
    assert len(payload["decisions"]) == 2


def test_audit_trail_returns_verified_trails() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/audit-trail").json()

    assert payload["total"] == 2
    assert [item["decision_id"] for item in payload["trails"]] == ["d1", "d2"]


def test_audit_trail_limit_works() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/audit-trail?limit=1").json()

    assert payload["total"] == 1
    assert [item["decision_id"] for item in payload["trails"]] == ["d1"]


def test_audit_trail_single_decision_hit() -> None:
    store, ids = _seed_store()
    payload = _client(store).get(f"/api/self/audit-trail?decision_id={ids['d1']}").json()

    assert payload["decision"]["decision_id"] == "d1"
    assert payload["outcome"]["decision_id"] == "d1"
    assert payload["chain_complete"] is True


def test_audit_trail_single_unverified_decision() -> None:
    store, ids = _seed_store()
    payload = _client(store).get(f"/api/self/audit-trail?decision_id={ids['d3']}").json()

    assert payload["decision"]["decision_id"] == "d3"
    assert payload["outcome"] is None
    assert payload["chain_complete"] is False


def test_audit_trail_missing_decision() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/audit-trail?decision_id=missing").json()

    assert payload == {"error": "Decision missing not found"}
