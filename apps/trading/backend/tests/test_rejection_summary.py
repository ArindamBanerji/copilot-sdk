from __future__ import annotations

from typing import Any, cast
from unittest.mock import Mock

import pytest

from copilot_sdk.graph import InMemoryGraphStore

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.evolution_router import (
    MAX_REJECTION_SCAN,
    create_trading_evolution_router,
)
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


def test_rejection_summary_reads_persisted_preseed_log():
    graph = InMemoryGraphStore()
    graph.save_evolution("trading", "preseed_rejection_summary",
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
                "provenance": "synthetic",
            }
    )
    app = FastAPI()
    app.include_router(
        create_trading_evolution_router(
            conservation_provider=lambda: {"status": "UNKNOWN"},
            graph_store_factory=lambda: graph,
        )
    )

    body = TestClient(app).get("/api/trading/evolution/rejection-summary").json()

    assert body["total_tested"] == 5
    assert body["total_rejected"] == 5
    assert body["rejection_breakdown"]["conservation"] == 5
    assert body["rejected_variants"][0]["variant_id"] == "TRADING_AE_v1"
    assert body["provenance"] == "synthetic"
    assert all(entry["provenance"] == "synthetic" for entry in body["rejected_variants"])


def test_rejection_summary_graph_failure_returns_valid() -> None:
    class UnavailableStore:
        def get_evolution(self, domain: str, variant_id: str) -> None:
            raise RuntimeError("graph unavailable")

    app = FastAPI()
    app.include_router(create_trading_evolution_router(
        evolver=_evolver(),
        graph_store_factory=UnavailableStore,
        include_persisted_rejections=True,
    ))

    response = TestClient(app).get("/api/trading/evolution/rejection-summary")

    assert response.status_code == 200
    assert "total_rejected" in response.json()


def test_rejection_summary_conservation_called_once() -> None:
    conservation_provider = Mock(return_value={"status": "RED"})
    evolver = TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=StoreFactory(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=conservation_provider,
    )
    for _ in range(12):
        variant = evolver.generate_variant()
        evolver._results[str(variant["variant_id"])] = [
            {
                "improvement_pp": 3.0,
                "decisions_tested": 50,
                "variant_accuracy": 0.73,
                "baseline_accuracy": 0.70,
            }
            for _batch in range(3)
        ]

    response = _client(evolver).get("/api/trading/evolution/rejection-summary")

    assert response.status_code == 200
    assert response.json()["total_rejected"] == 12
    conservation_provider.assert_called_once_with()


def test_rejection_summary_caps_scan() -> None:
    class CountingEvolver:
        def __init__(self) -> None:
            self.checks = 0

        def _conservation_safety(self) -> dict[str, str]:
            return {"status": "RED"}

        def evolution_log(self) -> list[dict[str, Any]]:
            return [
                {
                    "variant_id": f"variant-{index}",
                    "status": "evaluating",
                    "batches": 3,
                }
                for index in range(MAX_REJECTION_SCAN + 25)
            ]

        def check_promotion(
            self,
            variant_id: str,
            conservation_state: object,
        ) -> dict[str, Any]:
            self.checks += 1
            return {"promotable": False, "reason": "conservation_not_green"}

    evolver = CountingEvolver()
    app = FastAPI()
    app.include_router(create_trading_evolution_router(
        evolver=cast(Any, evolver),
    ))

    response = TestClient(app).get("/api/trading/evolution/rejection-summary")

    assert response.status_code == 200
    assert evolver.checks == MAX_REJECTION_SCAN
    assert response.json()["total_rejected"] == MAX_REJECTION_SCAN


@pytest.mark.parametrize(
    ("origins", "expected"),
    [(("synthetic",), "synthetic"), (("learned",), "learned"),
     (("synthetic", "learned"), "mixed")],
)
def test_rejection_summary_preserves_evidence_origins(tmp_path, origins, expected) -> None:
    from copilot_sdk.backend.scorer_proxy import FreshScorerProxy

    graph = InMemoryGraphStore(domain="trading")
    proxy = FreshScorerProxy(
        "trading", tmp_path / "unused.db", lambda path: graph, profile="test",
    )
    evolver = TradingAgentEvolver(
        baseline_scorer=proxy, store_factory=lambda: graph,
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=proxy.get_conservation_state,
    )
    entries = [
        {"variant_id": f"evidence-{index}", "reason": "conservation",
         "detail": "conservation gate not passed", "provenance": origin}
        for index, origin in enumerate(origins)
    ]
    graph.save_evolution("trading", "preseed_rejection_summary", {
        "total_tested": len(entries), "total_promoted": 0,
        # Entry origins override a stale summary-level label.
        "rejected_variants": entries, "provenance": "learned",
    })
    app = FastAPI()
    app.include_router(create_trading_evolution_router(
        evolver=evolver, graph_store_factory=lambda: graph,
        include_persisted_rejections=True,
    ))
    with TestClient(app) as client:
        response = client.get("/api/trading/evolution/rejection-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["provenance"] == expected
    assert [entry["provenance"] for entry in body["rejected_variants"]] == list(origins)
    assert body["total_rejected"] == len(origins)
