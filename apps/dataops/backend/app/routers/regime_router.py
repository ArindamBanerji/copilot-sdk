"""DataOps situation endpoint backed by the shared regime architecture."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from copilot_sdk.regime import DataOpsRegimePolicy, RegimeConditioner, RegimeDetector, RegimeState


def create_regime_router(scorer_provider: Callable[[], Any]) -> APIRouter:
    router = APIRouter(prefix="/api/dataops", tags=["dataops-regime"])
    policy = DataOpsRegimePolicy()
    detector = RegimeDetector(policy)
    conditioner = RegimeConditioner(policy)

    @router.get("/situation")
    def situation(
        pipeline_success_rate: float = 1.0,
        alert_volume: float = 0.0,
        failure_rate: float = 0.0,
        latency_p95: float = 0.0,
    ) -> dict[str, Any]:
        state = detector.detect({
            "pipeline_success_rate": pipeline_success_rate,
            "alert_volume": alert_volume,
            "failure_rate": failure_rate,
            "latency_p95": latency_p95,
        })
        return _payload(state.to_dict(), conditioner, scorer_provider)

    return router


def _payload(
    state: dict[str, Any],
    conditioner: RegimeConditioner,
    scorer_provider: Callable[[], Any],
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    try:
        store = getattr(scorer_provider(), "graph_store", None)
        getter = getattr(store, "get_verified_decisions", None)
        if callable(getter):
            decisions = list(getter("dataops"))
    except (AttributeError, TypeError, ValueError):
        decisions = []
    conditioned = conditioner.condition(
        {"verified_decisions": decisions},
        RegimeState(**state),
    )
    return {
        **state,
        "conditioned_context": conditioned.to_dict(),
        "observation_only": True,
    }
