"""Platform-wide applicability metrics for the copilot demo surface."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS


_DOMAIN_METRICS: tuple[dict[str, float | str], ...] = (
    {"name": "soc", "conditional_fraction": 0.341, "chain_length": 1.2},
    {"name": "dataops", "conditional_fraction": 0.213, "chain_length": 1.8},
    {"name": "s2p", "conditional_fraction": 0.279, "chain_length": 1.6},
    {"name": "trading", "conditional_fraction": 0.195, "chain_length": 1.4},
    {"name": "purchasing", "conditional_fraction": 0.167, "chain_length": 1.1},
)

TENSOR_SHAPES: dict[str, tuple[int, int, int]] = {
    "trading": (5, 4, 10),
    "purchasing": (5, 4, 7),
    "dataops": (6, 5, 6),
    "s2p": (5, 5, 8),
    "soc": (6, 4, 6),
}


_READ_ERRORS = (*GRAPH_CONNECTION_ERRORS, RuntimeError)


def _verified_decisions(scorer: Any) -> tuple[int, bool]:
    for method_name in (
        "get_verified_count",
        "count_verified_decisions",
        "count_verified",
        "get_decision_count",
    ):
        method = getattr(scorer, method_name, None)
        if callable(method):
            try:
                raw = method()
            except _READ_ERRORS:
                return 0, False
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                return 0, False
            return max(int(raw), 0), True
    return 0, False


def _compounding_gain_pp(scorer: Any) -> tuple[float, bool]:
    trajectory = getattr(scorer, "trajectory", None)
    if not callable(trajectory):
        return 0.0, False
    try:
        result = trajectory()
    except _READ_ERRORS:
        return 0.0, False
    if result is None:
        return 0.0, False
    try:
        current = _result_value(result, "current_win_rate")
        points = _result_value(result, "points")
        if current is None or not isinstance(points, (list, tuple)) or not points:
            return 0.0, False
        baseline = _result_value(points[0], "win_rate")
        if baseline is None:
            return 0.0, False
        if not isinstance(current, (int, float)) or not isinstance(baseline, (int, float)):
            return 0.0, False
        return round((float(current) - float(baseline)) * 100.0, 3), True
    except (TypeError, ValueError):
        raise


def _result_value(result: Any, name: str) -> Any:
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


def create_platform_router(scorer: Any, *, current_domain: str | None = None) -> APIRouter:
    """Create the read-only platform applicability router."""

    router = APIRouter(tags=["platform"])

    @router.get("/platform/domain-applicability")
    def domain_applicability() -> dict[str, Any]:
        verified, verified_available = _verified_decisions(scorer)
        gain, gain_available = _compounding_gain_pp(scorer)
        data_available = verified_available and gain_available
        domains: list[dict[str, Any]] = []
        for metric in _DOMAIN_METRICS:
            name = str(metric["name"])
            tensor_shape = TENSOR_SHAPES[name]
            domains.append(
                {
                    **metric,
                    "tensor_shape": list(tensor_shape),
                    "tensor_size": tensor_shape[0] * tensor_shape[1] * tensor_shape[2],
                    "verified_decisions": verified if name == current_domain else 0,
                    "compounding_gain_pp": gain if name == current_domain else 0.0,
                    "metric_tier": "EXPLORATORY",
                    "data_available": data_available if name == current_domain else True,
                }
            )
        return {
            "domains": domains,
            "platform_summary": {
                "total_domains": len(domains),
                "total_decisions": verified,
                "mean_compounding_gain_pp": round(
                    sum(float(item["compounding_gain_pp"]) for item in domains) / len(domains),
                    3,
                ),
            },
            "metric_tier": "EXPLORATORY",
            "data_available": data_available,
        }

    return router
