"""Trading evidence-gate and promotion-safety contracts."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.claim_gate import (
    CLAIM_TRD_PATTERN,
    CLAIM_TRD_PROMOTION,
    TradingClaimRegistry,
    TradingEvidenceMiddleware,
    TradingPromotionGuard,
)


def test_claim_registry_initialized_with_trading_claims() -> None:
    registry = TradingClaimRegistry()
    assert registry.gate.check(CLAIM_TRD_PATTERN, "demo").tier.name == "T_S"
    assert registry.gate.check(CLAIM_TRD_PROMOTION, "pilot").passed is False


def test_middleware_adds_tier_and_honest_label() -> None:
    registry = TradingClaimRegistry()
    app = FastAPI()
    app.add_middleware(TradingEvidenceMiddleware, registry=registry)

    @app.get("/api/trading/analytics/vol-sharpe")
    def metric() -> dict[str, str]:
        return {"value": "demo"}

    response = TestClient(app).get("/api/trading/analytics/vol-sharpe")
    assert response.status_code == 200
    assert response.headers["X-Evidence-Tier"] == "T_S"
    assert response.json()["evidence_tier"] == "T_S"
    assert "not measured" in response.json()["evidence_label"]


def test_measured_claim_gets_measured_label() -> None:
    registry = TradingClaimRegistry()
    registry.mark_observed((CLAIM_TRD_PATTERN,))
    result = registry.gate.check(CLAIM_TRD_PATTERN, "pilot")
    assert result.passed is True
    assert result.tier.name == "T_O"
    assert result.label == "measured"


def test_promotion_guard_blocks_without_observed_evidence() -> None:
    guard = TradingPromotionGuard(TradingClaimRegistry())
    decision = guard.authorize("trend_following", {"status": "GREEN"})
    assert decision.allowed is False
    assert decision.reason == "promotion_requires_observed_evidence"


def test_promotion_guard_blocks_non_green_even_when_observed() -> None:
    registry = TradingClaimRegistry()
    registry.mark_observed((CLAIM_TRD_PROMOTION,))
    decision = TradingPromotionGuard(registry).authorize("trend_following", {"status": "AMBER"})
    assert decision.allowed is False
    assert decision.reason == "conservation_amber"


def test_promotion_state_machine_advances_only_after_all_gates() -> None:
    registry = TradingClaimRegistry()
    registry.mark_observed((CLAIM_TRD_PROMOTION,))
    result = TradingPromotionGuard(registry).advance_observed(
        "trend_following", {"status": "GREEN"}, shadow_decisions=10
    )
    assert result["advanced"] is True
    assert result["new_stage"] == "shadowing"
