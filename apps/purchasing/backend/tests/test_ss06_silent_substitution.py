from __future__ import annotations

import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main
from app.context_router import _evolution_variants as context_evolution_variants
from app.evidence_providers import HistoricalWasteProvider
from app.routers.cohort_status_router import create_cohort_status_router
from app.routers.scorecard_router import create_scorecard_router
from app.routers.trust_router import create_trust_router
from app.services.cohort_status import CohortReadError, CohortStatusService
from app.services.purchasing_control import PurchasingClaimRegistry


class BrokenGraph:
    def get_vld_context(self, entity_id):
        raise RuntimeError("context unavailable")

    def get_evolution_events(self, **kwargs):
        raise RuntimeError("graph unavailable")

    def get_verified_decisions(self, domain):
        raise RuntimeError("history unavailable")

    def get_all_decisions(self, domain):
        raise RuntimeError("history unavailable")

    def get_decisions(self, domain, limit):
        raise RuntimeError("history unavailable")

    def count_verified(self, domain):
        raise RuntimeError("counter unavailable")


def test_context_and_main_variant_reads_distinguish_graph_failure() -> None:
    from app import context_router

    context_router.set_evolution_store_factory(lambda: BrokenGraph())
    try:
        assert context_evolution_variants() is None
    finally:
        context_router.set_evolution_store_factory(None)
    assert main._evolution_variants(BrokenGraph()) is None


def test_item_profile_marks_evolution_failure() -> None:
    from app import context_router

    item = context_router.items()[0]["name"]
    app = FastAPI()
    app.include_router(context_router.router)
    context_router.set_evolution_store_factory(lambda: BrokenGraph())
    try:
        payload = TestClient(app).get(f"/item/{item}/profile").json()
    finally:
        context_router.set_evolution_store_factory(None)
    assert payload["ae_rules"] == []
    assert payload["ae_rules_available"] is False
    assert payload["degraded"] is True


def test_domain_context_failure_is_marked_unavailable() -> None:
    payload = HistoricalWasteProvider().read_payload("ORDER-1", BrokenGraph())
    assert payload["value"] == 0.5
    assert payload["data_available"] is False
    assert payload["degraded"] is True


def test_alert_conservation_failure_is_explicit() -> None:
    materializer = SimpleNamespace(get=lambda key: (_ for _ in ()).throw(RuntimeError("graph unavailable")))
    payload = main._alert_conservation_status_payload(materializer, object())
    assert payload["status"] == "UNAVAILABLE"
    assert payload["state"] == "conservation_unavailable"


def test_iks_failure_includes_graph_cause() -> None:
    app = FastAPI()
    app.include_router(create_scorecard_router(lambda: (_ for _ in ()).throw(RuntimeError("AGE down"))))
    payload = TestClient(app).get("/api/purchasing/iks/summary").json()
    assert payload["available"] is False
    assert payload["degraded"] is True
    assert "graph_unavailable" in payload["unavailable_reason"]


def test_trust_counter_failure_is_unavailable() -> None:
    class BrokenScorer:
        def get_dk_weights(self):
            return []

        def get_verified_count(self):
            raise RuntimeError("counter unavailable")

    app = FastAPI()
    app.include_router(create_trust_router(lambda: BrokenScorer()))
    payload = TestClient(app).get("/api/purchasing/trust-weights").json()
    assert payload["phase"] == "UNAVAILABLE"
    assert payload["decisions_total"] == 0
    assert payload["degraded"] is True


def test_cohort_history_failure_is_not_empty_cohort() -> None:
    try:
        CohortStatusService(graph_store=BrokenGraph()).get_status()
    except CohortReadError:
        pass
    else:
        raise AssertionError("failed cohort history must remain unavailable")

    app = FastAPI()
    app.include_router(create_cohort_status_router(graph_store_factory=BrokenGraph))
    payload = TestClient(app).get("/api/purchasing/cohort-status").json()
    assert payload["data_available"] is False
    assert payload["degraded"] is True
    assert payload["real"]["status"] == "unavailable"


def test_claim_refresh_logs_failed_history(caplog) -> None:
    registry = PurchasingClaimRegistry()
    with caplog.at_level("WARNING"):
        registry.refresh(BrokenGraph())
    assert "claim qualification remains unmeasured" in caplog.text


def test_seed_reports_partial_failure(tmp_path, monkeypatch, capsys) -> None:
    fixture = tmp_path / "seed.json"
    fixture.write_text(json.dumps([
        {"category": "protein", "is_correct": True, "action_taken": "order_more"},
        {"category": "protein", "is_correct": True, "action_taken": "order_more"},
    ]), encoding="utf-8")
    monkeypatch.setattr(main, "SEED_FIXTURE_PATH", fixture)

    class Scorer:
        calls = 0

        def score(self, factors, category, metadata):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("seed failed")
            return {"decision_id": "PUR-SEED-1", "action": "order_more"}

    class Store:
        def write_outcome(self, *args, **kwargs):
            return None

    result = main._seed_from_fixtures(Scorer(), Store())
    assert result["total"] == 2
    assert result["failed"] == 1
    assert "auto-seed skipped entry 1" in capsys.readouterr().out
