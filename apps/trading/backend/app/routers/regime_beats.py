"""Observation-only endpoints for the four Trading situational demo beats."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, cast

from fastapi import APIRouter

from app.routers.regime_analytics import _read_decisions
from app.services.regime_analytics import RegimeAnalytics
from app.services.regime_monitor import RegimeMonitor
from app.services.situation_analyzer import (
    check_regime_data_sufficiency,
    compute_regime_conditioned_stats,
    compute_regime_rejections,
    detect_regime,
)

GraphStoreFactory = Callable[[], Any]


def create_regime_beats_router(
    graph_store_factory: GraphStoreFactory,
    *,
    domain: str = "trading",
    regime_monitor: RegimeMonitor,
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/regime", tags=["trading-situational-beats"])

    def decisions() -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], _read_decisions(graph_store_factory, domain))

    @router.get("/mirror")
    def regime_mirror() -> dict[str, Any]:
        rows = decisions()
        current = detect_regime(rows)
        analytics = RegimeAnalytics().compute(rows)
        observations = []
        for regime, stats in analytics["regimes"].items():
            observations.append(
                {
                    "regime": regime,
                    "decision_count": stats["decision_count"],
                    "verified_count": stats["verified_count"],
                    "accuracy": stats["accuracy"],
                    "measurement_state": stats["measurement_state"],
                    "observation": (
                        f"Observed {stats['verified_count']} verified decisions in {regime} conditions."
                        if stats["verified_count"]
                        else f"No verified decisions are recorded for {regime} conditions yet."
                    ),
                }
            )
        return {
            "current_regime": current,
            "regimes": observations,
            "behavior_change": analytics,
            "observation_only": True,
            "evidence_tier": "T_O" if any(item["verified_count"] for item in observations) else "T_S",
            "observation": "Regime-scoped scorer behavior is shown as measured history where verified evidence exists.",
        }

    @router.get("/abstention")
    def situational_abstention() -> dict[str, Any]:
        rows = decisions()
        current = detect_regime(rows)
        result = dict(check_regime_data_sufficiency(rows, current))
        conditioned = compute_regime_conditioned_stats(rows, current)
        result.update(
            {
                "per_regime_day_zero": {
                    str(regime): {
                        "decision_count": int(stats.get("decision_count", 0)),
                        "verified_count": int(stats.get("verified_count", 0)),
                        "abstention": stats.get("verified_count", 0) < stats.get("minimum_decisions", 20),
                    }
                    for regime, stats in conditioned.get("regimes", {}).items()
                    if isinstance(stats, dict)
                },
                "abstention_reasons": ["regime-specific verified history is below the evidence floor"]
                if result.get("abstention_recommended")
                else [],
                "observation_only": True,
                "evidence_tier": "INSUFFICIENT" if result.get("abstention_recommended") else "T_O",
            }
        )
        return result

    @router.get("/throttle")
    def autonomy_throttle() -> dict[str, Any]:
        status = regime_monitor.status()
        current = status.current_regime or "unknown"
        previous = status.previous_regime or "unknown"
        return {
            "current_regime": current,
            "previous_regime": status.previous_regime,
            "regime_break_active": status.regime_break_active,
            "authority_level_by_regime": {
                current: "restricted" if status.regime_break_active else "normal",
                previous: "review" if status.regime_break_active and previous != current else "normal",
            },
            "reconvergence_timeline": {
                "decisions_in_new_regime": status.decisions_in_new_regime,
                "decisions_to_stabilize": status.decisions_to_stabilize,
                "remaining": max(0, status.decisions_to_stabilize - status.decisions_in_new_regime),
            },
            "observation_only": True,
            "observation": "Authority state reflects the live regime monitor; a break is surfaced as reduced autonomy.",
            "evidence_tier": "T_O" if status.current_regime is not None else "T_S",
        }

    @router.get("/rejection")
    def regime_scoped_rejection() -> dict[str, Any]:
        rows = decisions()
        result = dict(compute_regime_rejections(rows))
        counts: defaultdict[str, int] = defaultdict(int)
        for row in rows:
            if row.get("regime_rejected") is True or row.get("rejected") is True:
                regime = row.get("regime") or row.get("current_regime") or "unknown"
                counts[str(regime)] += 1
        result.update(
            {
                "rejections_by_regime": dict(counts),
                "regime_context": "Rules are retained only where their measured behavior remains supported across the observed regime history.",
                "observation_only": True,
                "evidence_tier": "T_O" if counts else "T_S",
            }
        )
        return result

    @router.get("/reconvergenc")
    @router.get("/reconvergence")
    def regime_reconvergence() -> dict[str, Any]:
        rows = decisions()
        status = regime_monitor.status()
        analytics = RegimeAnalytics().compute(rows)
        return {
            "current_regime": status.current_regime,
            "previous_regime": status.previous_regime,
            "regime_break_active": status.regime_break_active,
            "decisions_in_new_regime": status.decisions_in_new_regime,
            "decisions_to_stabilize": status.decisions_to_stabilize,
            "remaining": max(0, status.decisions_to_stabilize - status.decisions_in_new_regime),
            "historical_regime_breaks": analytics.get("regimes", {}),
            "cold_start_curves": {
                "reset": status.regime_break_active,
                "observed_decisions": len(rows),
            },
            "observation_only": True,
            "evidence_tier": "T_O" if rows else "T_S",
        }

    return router
