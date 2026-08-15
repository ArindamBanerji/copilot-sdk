from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.evolution_router import create_trading_evolution_router
from app.services.trading_evolver import TRADING_FACTOR_NAMES, TradingAgentEvolver


class BaselineScorer:
    graph_store = object()

    def predict(self, decision):
        return decision.get("recommended_action")


class StoreFactory:
    def __call__(self):
        return object()


def _decisions(improvement_pp=0.0, count=50):
    variant_correct_count = int(count * 0.70)
    baseline_correct_count = int(count * (0.70 - improvement_pp / 100.0))
    return [
        {
            "actual_action": "strong_execution",
            "recommended_action": "strong_execution" if index < baseline_correct_count else "partial_execution",
            "baseline_correct": index < baseline_correct_count,
            "variant_correct": index < variant_correct_count,
        }
        for index in range(count)
    ]


def _client(evolver: TradingAgentEvolver) -> TestClient:
    app = FastAPI()
    app.include_router(create_trading_evolution_router(evolver=evolver))
    return TestClient(app)


def _evolver(conservation="GREEN") -> TradingAgentEvolver:
    return TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=StoreFactory(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=lambda: {"status": conservation},
    )


def _add_rejected_variant(evolver: TradingAgentEvolver):
    variant = evolver.generate_variant()
    for _ in range(3):
        evolver.shadow_test(variant, _decisions(improvement_pp=0.0), batch_size=50)
    return variant


def test_rejection_summary_returns_200():
    response = _client(_evolver()).get("/api/trading/evolution/rejection-summary")
    assert response.status_code == 200


def test_rejection_summary_has_breakdown():
    evolver = _evolver()
    _add_rejected_variant(evolver)
    body = _client(evolver).get("/api/trading/evolution/rejection-summary").json()
    assert set(body["rejection_breakdown"]) == {"correctness_floor", "conservation", "variance_stability"}


def test_rejection_summary_counts_match_log():
    evolver = _evolver()
    _add_rejected_variant(evolver)
    body = _client(evolver).get("/api/trading/evolution/rejection-summary").json()
    assert body["total_tested"] == 1
    assert body["total_rejected"] == 1
    assert body["rejected_variants"][0]["reason"] == "correctness_floor"


def test_rejection_summary_empty_when_no_rejections():
    body = _client(_evolver()).get("/api/trading/evolution/rejection-summary").json()
    assert body["total_rejected"] == 0
    assert body["rejected_variants"] == []


def test_rejection_summary_reads_persisted_preseed_log(tmp_path, monkeypatch):
    log_path = tmp_path / "evolution_log.json"
    log_path.write_text(
        json.dumps(
            {
                "total_tested": 5,
                "total_promoted": 0,
                "total_rejected": 5,
                "rejection_breakdown": {
                    "correctness_floor": 0,
                    "conservation": 5,
                    "variance_stability": 0,
                },
                "rejected_variants": [
                    {
                        "variant_id": f"TRADING_AE_v{index}",
                        "reason": "conservation",
                        "detail": "conservation gate not GREEN",
                        "tested_at": f"2026-07-11T00:0{index}:00Z",
                    }
                    for index in range(1, 6)
                ],
                "provenance": "learned",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TRADING_EVOLUTION_LOG_PATH", str(log_path))
    app = FastAPI()
    app.include_router(
        create_trading_evolution_router(
            conservation_provider=lambda: {"status": "UNKNOWN"},
        )
    )

    body = TestClient(app).get("/api/trading/evolution/rejection-summary").json()

    assert body["total_tested"] == 5
    assert body["total_rejected"] == 5
    assert body["rejection_breakdown"]["conservation"] == 5
    assert body["rejected_variants"][0]["variant_id"] == "TRADING_AE_v1"
