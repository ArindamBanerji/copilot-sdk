"""Trading-owned evidence and promotion safety adapter.

The SDK owns the evidence and promotion primitives.  This module owns only
Trading's claim vocabulary, route mapping, and observation-only policy.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

from starlette.datastructures import MutableHeaders

from copilot_sdk.evidence import ClaimRecord, EvidenceGate, EvidenceTier
from copilot_sdk.promotion import (
    PromotionEngine,
    PromotionStage,
    PromotionStore,
    TradingPromotionPolicy,
)
from copilot_sdk.evolution import GraphPromotionStore

from app.settings import settings


CLAIM_TRD_SHARPE = "CLAIM-TRD-SHARPE"
CLAIM_TRD_PATTERN = "CLAIM-TRD-PATTERN"
CLAIM_TRD_REGIME = "CLAIM-TRD-REGIME"
CLAIM_TRD_ROI = "CLAIM-TRD-ROI"
CLAIM_TRD_VERIFIED_ACCURACY = "CLAIM-TRD-VERIFIED-ACCURACY"
CLAIM_TRD_PROMOTION = "CLAIM-TRD-PROMOTION"
CLAIM_TRD_GENERAL = "CLAIM-TRD-GENERAL"


_CLAIMS: tuple[ClaimRecord, ...] = (
    ClaimRecord(CLAIM_TRD_SHARPE, "Risk-adjusted return metric", EvidenceTier.T_S, "Trading verified ledger pending sufficient observations", "trading"),
    ClaimRecord(CLAIM_TRD_PATTERN, "Pattern detection accuracy", EvidenceTier.T_S, "Trading verified ledger pending sufficient observations", "trading"),
    ClaimRecord(CLAIM_TRD_REGIME, "Regime classification accuracy", EvidenceTier.T_S, "Trading verified ledger pending sufficient observations", "trading"),
    ClaimRecord(CLAIM_TRD_ROI, "Portfolio improvement attribution", EvidenceTier.T_S, "Trading verified ledger pending sufficient observations", "trading"),
    ClaimRecord(CLAIM_TRD_VERIFIED_ACCURACY, "Verified Trading accuracy", EvidenceTier.T_O, "Trading verified outcome ledger", "trading"),
    ClaimRecord(CLAIM_TRD_PROMOTION, "Trading strategy promotion authority", EvidenceTier.T_S, "Promotion requires observed Trading evidence", "trading"),
    ClaimRecord(CLAIM_TRD_GENERAL, "Trading observation output", EvidenceTier.T_S, "Trading observation surface", "trading"),
)


ROUTE_CLAIMS: tuple[tuple[str, str], ...] = (
    ("/api/trading/analytics/vol-sharpe", CLAIM_TRD_SHARPE),
    ("/api/trading/analytics/vrp-attribution", CLAIM_TRD_ROI),
    ("/api/trading/analytics/regime-vrp", CLAIM_TRD_REGIME),
    ("/api/trading/analytics/dispersion-follow", CLAIM_TRD_PATTERN),
    ("/api/trading/volatility/sharpe", CLAIM_TRD_SHARPE),
    ("/api/trading/volatility/vrp", CLAIM_TRD_ROI),
    ("/api/trading/volatility/rich-cheap", CLAIM_TRD_REGIME),
    ("/api/trading/volatility/dispersion", CLAIM_TRD_PATTERN),
    ("/api/trading/volatility/tail-bets", CLAIM_TRD_REGIME),
    ("/api/trading/execution-analysis", CLAIM_TRD_VERIFIED_ACCURACY),
    ("/api/trading/regime/performance", CLAIM_TRD_REGIME),
    ("/api/trading/iks", CLAIM_TRD_VERIFIED_ACCURACY),
    ("/api/self/accuracy-by-category", CLAIM_TRD_VERIFIED_ACCURACY),
)


class TradingClaimRegistry:
    """Trading claim registration plus explicit observed-tier promotion."""

    def __init__(self) -> None:
        self.gate = EvidenceGate()
        self._claims = {claim.claim_id: claim for claim in _CLAIMS}
        self.register_all()
        self.last_refresh_available = False
        self.stale = True

    def register_all(self) -> None:
        for claim in self._claims.values():
            self.gate.register(claim)

    def mark_observed(self, claim_ids: tuple[str, ...]) -> None:
        for claim_id in claim_ids:
            current = self._claims[claim_id]
            observed = ClaimRecord(
                claim_id=current.claim_id,
                description=current.description,
                tier=EvidenceTier.T_O,
                evidence_basis="Trading verified outcome ledger with observed decisions",
                copilot=current.copilot,
                context_minimum=current.context_minimum,
            )
            self._claims[claim_id] = observed
            self.gate.register(observed)

    def refresh_from_store(self, graph_store: Any) -> None:
        """Upgrade only claims backed by at least one verified observation."""
        try:
            verified = graph_store.get_verified_decisions(domain="trading")
        except (ConnectionError, TimeoutError, OSError, RuntimeError):
            self.last_refresh_available = False
            self.stale = True
            return
        if not isinstance(verified, list):
            self.last_refresh_available = False
            self.stale = True
            return
        self.last_refresh_available = True
        self.stale = False
        if not verified:
            return
        self.mark_observed(
            (CLAIM_TRD_PATTERN, CLAIM_TRD_REGIME, CLAIM_TRD_VERIFIED_ACCURACY, CLAIM_TRD_PROMOTION)
        )

    def claim_for_path(self, path: str) -> str | None:
        for prefix, claim_id in ROUTE_CLAIMS:
            if path.startswith(prefix):
                return claim_id
        return None


@dataclass(frozen=True)
class PromotionDecision:
    allowed: bool
    reason: str
    evidence_tier: str
    evidence_label: str


class TradingPromotionGuard:
    """Fail-closed claim and safety gate around promotion authority."""

    def __init__(self, registry: TradingClaimRegistry, store_path: str = ":memory:", graph_store: Any = None) -> None:
        self.registry = registry
        promotion_store = (
            GraphPromotionStore(graph_store, "trading")
            if graph_store is not None
            else PromotionStore(store_path)
        )
        self.engine = PromotionEngine(TradingPromotionPolicy(), promotion_store)

    def authorize(self, category: str, conservation: Mapping[str, Any] | None = None) -> PromotionDecision:
        result = self.registry.gate.check(CLAIM_TRD_PROMOTION, "pilot")
        if not result.passed:
            return PromotionDecision(False, "promotion_requires_observed_evidence", result.tier.name, result.label)
        if settings.TRADING_EXECUTION_ENABLED:
            return PromotionDecision(False, "observation_only_execution_guard", result.tier.name, result.label)
        status = str((conservation or {}).get("status") or (conservation or {}).get("conservation_status") or "UNKNOWN").upper()
        if status != "GREEN":
            return PromotionDecision(False, f"conservation_{status.lower()}", result.tier.name, result.label)
        if not category.strip():
            return PromotionDecision(False, "decision_class_required", result.tier.name, result.label)
        return PromotionDecision(True, "promotion_gates_passed", result.tier.name, result.label)

    def advance_observed(self, category: str, conservation: Mapping[str, Any], *, shadow_decisions: int = 1, measurement_decisions: int = 1, improvement: float = 0.0) -> dict[str, Any]:
        decision = self.authorize(category, conservation)
        if not decision.allowed:
            return {"advanced": False, "reason": decision.reason, "evidence_tier": decision.evidence_tier, "evidence_label": decision.evidence_label}
        record = self.engine.store.load_by_class("trading", category) or self.engine.create("trading", category, record_id=f"trading-{category}")
        result = self.engine.advance(record.record_id, {"conservation_state": "GREEN", "shadow_decisions": shadow_decisions, "measurement_decisions": measurement_decisions, "improvement": improvement})
        return {"advanced": result.advanced, "new_stage": result.new_stage.value, "reason": result.reason, "evidence_tier": decision.evidence_tier, "evidence_label": decision.evidence_label}


def _route_claim(registry: TradingClaimRegistry, path: str) -> str | None:
    return registry.claim_for_path(path)


class TradingEvidenceMiddleware:
    """Attach evidence headers and annotate successful JSON claim responses."""

    def __init__(self, app: Any, registry: TradingClaimRegistry, context: str = "demo") -> None:
        self.app = app
        self.registry = registry
        self.context = context

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        claim_id = _route_claim(self.registry, str(scope.get("path", "")))
        effective_claim = claim_id or CLAIM_TRD_GENERAL
        result = self.registry.gate.check(effective_claim, self.context)
        messages: list[dict[str, Any]] = []

        async def capture(message: dict[str, Any]) -> None:
            messages.append(message)

        await self.app(scope, receive, capture)
        if not messages:
            return
        start = messages[0]
        headers = MutableHeaders(scope=start)
        headers["X-Evidence-Tier"] = result.tier.name
        headers["X-Evidence-Label"] = result.label.replace("—", "-")
        headers["X-Evidence-Gate"] = "passed" if result.passed else "blocked"
        should_annotate = (
            claim_id is not None
            and int(start.get("status", 500)) < 400
            and "application/json" in headers.get("content-type", "")
        )
        if not should_annotate:
            for message in messages:
                await send(message)
            return
        body = b"".join(bytes(message.get("body", b"")) for message in messages[1:] if message["type"] == "http.response.body")
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            for message in messages:
                await send(message)
            return
        metadata = {
            "evidence_tier": result.tier.name,
            "evidence_label": result.label,
            "evidence_gate": "passed" if result.passed else "blocked",
            "claim_id": effective_claim,
        }
        if isinstance(payload, dict):
            payload = {**payload, **metadata}
        elif isinstance(payload, list):
            payload = [{**item, **metadata} if isinstance(item, dict) else item for item in payload]
        else:
            for message in messages:
                await send(message)
            return
        encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
        headers["content-length"] = str(len(encoded))
        await send(start)
        await send({"type": "http.response.body", "body": encoded})
