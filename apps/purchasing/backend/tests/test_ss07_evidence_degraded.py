from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.evidence_providers import _domain_context
from app.routers.evidence import create_evidence_router


class BrokenGraph:
    def get_all_decisions(self, _domain: str):
        raise RuntimeError("offline")

    def get_verified_decisions(self, _domain: str):
        raise RuntimeError("offline")

    def get_centroid_checkpoints(self, _domain: str, *, limit: int):
        raise RuntimeError("offline")

    def count_verified(self, _domain: str):
        raise RuntimeError("offline")

    def count_correct(self, _domain: str):
        raise RuntimeError("offline")


def _client() -> TestClient:
    app = FastAPI()
    state = SimpleNamespace(graph_store=BrokenGraph(), trajectory=lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    app.include_router(create_evidence_router(state))
    return TestClient(app)


def test_summary_marks_each_failed_population_read() -> None:
    payload = _client().get("/api/purchasing/evidence/summary").json()

    assert payload["decision_count"] == 0
    assert payload["verified_count"] == 0
    assert payload["decisions_available"] is False
    assert payload["verified_available"] is False
    assert payload["trajectory_available"] is False
    assert payload["conservation_status"] == "UNAVAILABLE"


def test_proof_marks_failed_counts_and_checkpoints() -> None:
    payload = _client().get("/api/purchasing/evidence/conservation-proof").json()

    assert payload["q"] == 0.0
    assert payload["q_available"] is False
    assert payload["trajectory"] == []
    assert payload["count_verified_available"] is False
    assert payload["count_correct_available"] is False
    assert payload["checkpoints_available"] is False
    assert payload["days_in_green"] == 0
    assert payload["days_in_green_available"] is False
    assert all(value is not None for value in payload.values())


def test_evidence_decisions_preserves_empty_array_on_failure() -> None:
    payload = _client().get("/api/purchasing/evidence/decisions").json()

    assert payload["decisions"] == []
    assert payload["verified_available"] is False
    assert payload["data_available"] is False


def test_domain_context_failure_marks_provider_payload() -> None:
    class BrokenSource:
        def get_vld_context(self, _entity_id: str):
            raise RuntimeError("offline")

    payload = _domain_context("order-1", BrokenSource(), None)

    assert payload is None


def test_evidence_summary_happy_path_marks_reads_available() -> None:
    from copilot_sdk.graph import InMemoryGraphStore

    store = InMemoryGraphStore(domain="purchasing")
    decision_id = store.write_decision("purchasing", "protein", "accept", 0.8, {})
    store.write_outcome(decision_id, "accept", True, domain="purchasing")

    app = FastAPI()
    state = SimpleNamespace(
        graph_store=store,
        trajectory=lambda: {"current_iks": 1.0},
    )
    app.include_router(create_evidence_router(state))
    payload = TestClient(app).get("/api/purchasing/evidence/summary").json()

    assert payload["decisions_available"] is True
    assert payload["verified_available"] is True
    assert payload["trajectory_available"] is True
