"""Trading response computations shared by HTTP and tab-state readers."""
from __future__ import annotations

from typing import Any, Callable, cast

from fastapi.encoders import jsonable_encoder

from app.context_router import _analytics_from_decisions
from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution
from app.routers.journal import _journal_records
from app.services.regime import RegimeService
from app.services.regime_monitor import RegimeMonitor
from app.services.regime_recommender import RegimeRecommender
from copilot_sdk.backend.conservation_router import build_conservation_status
from copilot_sdk.backend.response_materializer import ResponseMaterializer
from copilot_sdk.scoring.measurement_state import compute_measurement_state

DOMAIN = "trading"


class _StaticDecisionStore:
    def __init__(self, decisions: list[dict[str, Any]]) -> None:
        self._decisions = decisions

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [dict(decision) for decision in self._decisions]


def _accuracy_by_category_payload(verified: list[dict[str, Any]], threshold: float = 0.70) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for decision in verified:
        category = str(decision.get("category") or "uncategorized")
        bucket = grouped.setdefault(category, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if decision.get("is_correct") is True:
            bucket["correct"] += 1
    categories = []
    for category in sorted(grouped):
        total = grouped[category]["total"]
        correct = grouped[category]["correct"]
        accuracy = round(correct / total, 4) if total else 0.0
        categories.append({
            "category": category,
            "accuracy": accuracy,
            "total": total,
            "correct": correct,
            "alert": accuracy < threshold,
        })
    return {"categories": categories, "threshold": threshold, "overall_verified": len(verified)}


def _engine_payload() -> dict[str, str]:
    return {
        "scoring": "copilot_sdk.scoring.CompoundingScorer",
        "gae": "gae.profile_scorer.ProfileScorer",
    }


def create_trading_materializer(
    scorer_proxy: Any,
    store_provider: Callable[[], Any],
    regime_monitor: RegimeMonitor,
) -> ResponseMaterializer:
    def _trading_regime_detail(shared: dict[str, Any]) -> dict[str, Any]:
        service = RegimeService()
        decisions = cast(list[dict[str, Any]], shared["decisions"])
        trades = _journal_records(lambda: _StaticDecisionStore(decisions), DOMAIN)
        current = service.get_current_regime()
        accuracy = service.get_regime_accuracy(trades)
        conservation = build_conservation_status(DOMAIN, scorer_proxy)
        payload = RegimeRecommender().recommend(
            str(current.get("regime") or "ranging"),
            accuracy,
            conservation_status=conservation,
            trades=trades,
            current=current,
            previous_regime=None,
        )
        if regime_monitor.is_regime_break:
            payload = dict(payload)
            sizing = payload.get("sizing_recommendation")
            if isinstance(sizing, dict):
                payload["sizing_recommendation"] = {
                    **sizing,
                    "action": "paused",
                    "suggested_size_multiplier": 0.0,
                    "max_size_multiplier": 0.0,
                    "paused": True,
                    "reason": "regime_break_active",
                }
        return cast(dict[str, Any], payload)

    def _trading_fingerprint_payload(_: dict[str, Any]) -> dict[str, Any]:
        payload = jsonable_encoder(scorer_proxy.fingerprint())
        payload["engine"] = _engine_payload()
        return cast(dict[str, Any], payload)

    def _trading_trajectory_payload(_: dict[str, Any]) -> dict[str, Any]:
        payload = jsonable_encoder(scorer_proxy.trajectory())
        payload["engine"] = _engine_payload()
        return cast(dict[str, Any], payload)

    def _trading_measurement_payload(_: dict[str, Any]) -> dict[str, Any]:
        payload = compute_measurement_state(scorer_proxy).to_dict()
        payload["engine"] = _engine_payload()
        return cast(dict[str, Any], payload)

    return ResponseMaterializer(
        domain=DOMAIN,
        store_provider=store_provider,
        computations={
            "analytics": lambda s: _analytics_from_decisions(cast(list[dict[str, Any]], s["decisions"])),
            "conservation": lambda s: build_conservation_status(DOMAIN, scorer_proxy),
            "accuracy_by_category": lambda s: _accuracy_by_category_payload(cast(list[dict[str, Any]], s["verified"])),
            "fingerprint": _trading_fingerprint_payload,
            "trajectory": _trading_trajectory_payload,
            "measurement_state": _trading_measurement_payload,
            "regime_detail": _trading_regime_detail,
            "vol_sharpe": lambda s: compute_clustering_adjusted_sharpe(cast(list[dict[str, Any]], s["verified"])),
            "vrp_attribution": lambda s: compute_vrp_attribution(cast(list[dict[str, Any]], s["verified"])),
            "dispersion_follow": lambda s: compute_dispersion_follow_rate(cast(list[dict[str, Any]], s["verified"])),
        },
        ttl=5.0,
    )
