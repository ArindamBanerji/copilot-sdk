"""FastAPI discovery router factory."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Query

from copilot_sdk.backend.models import (
    DiscoveryAlertsResponse,
    DiscoverySweepResponse,
    FlexibleResponse,
)
from copilot_sdk.discovery.cross_system import CrossSystemCorrelator


def create_discovery_router(engine: Any) -> APIRouter:
    """Create advisory discovery endpoints for a DiscoveryEngine."""

    router = APIRouter(prefix="/api/discovery", tags=["Discovery"])

    @router.post("/sweep", response_model=DiscoverySweepResponse)
    def sweep() -> dict[str, Any]:
        alerts = list(engine.sweep())
        return {
            "new_alerts": len(alerts),
            "alerts": [_alert_payload(alert) for alert in alerts],
        }

    @router.get("/digest", response_model=FlexibleResponse)
    def digest(min_confidence: float = Query(0.5, ge=0.0, le=1.0)) -> dict[str, Any]:
        get_digest = getattr(engine, "get_digest", None)
        digest_alerts = get_digest(min_confidence=min_confidence) if callable(get_digest) else []
        return {
            "alerts": [
                _alert_payload(alert)
                for alert in digest_alerts
            ],
            "cross_system": _cross_system_alerts(engine, min_confidence),
        }

    @router.get("/alerts", response_model=DiscoveryAlertsResponse)
    def alerts() -> dict[str, Any]:
        all_alerts = list(getattr(engine, "_alerts", []))
        return {
            "total": len(all_alerts),
            "alerts": [_alert_payload(alert) for alert in all_alerts],
        }

    @router.get("/cross-system", response_model=FlexibleResponse)
    def cross_system(min_correlation: float = Query(0.5, ge=0.0, le=1.0)) -> dict[str, Any]:
        decisions, used_demo = _domain_decisions(engine)
        return {
            "alerts": CrossSystemCorrelator().scan(decisions, min_correlation=float(min_correlation)),
            "provenance": _cross_system_provenance(decisions, used_demo),
        }

    return router


def _alert_payload(alert: Any) -> dict[str, Any]:
    return asdict(alert)


def _cross_system_alerts(engine: Any, min_correlation: float) -> list[dict[str, Any]]:
    decisions, _used_demo = _domain_decisions(engine)
    return CrossSystemCorrelator().scan(decisions, min_correlation=float(min_correlation))


def _domain_decisions(engine: Any) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    decisions = getattr(engine, "domain_decisions", None)
    if decisions is None:
        decisions = getattr(engine, "_domain_decisions", None)
    if not isinstance(decisions, dict):
        return _demo_domain_decisions(), True
    normalized: dict[str, list[dict[str, Any]]] = {}
    for domain, rows in decisions.items():
        if isinstance(rows, list):
            normalized[str(domain)] = [dict(row) for row in rows if isinstance(row, dict)]
    return normalized, False


def _cross_system_provenance(decisions: dict[str, list[dict[str, Any]]], used_demo: bool) -> str:
    if used_demo or _is_demo_data(decisions):
        return "demo"
    has_real = any(len(rows) > 0 for rows in decisions.values())
    return "real" if has_real else "demo"


def _is_demo_data(decisions: dict[str, list[dict[str, Any]]]) -> bool:
    rows = [row for domain_rows in decisions.values() for row in domain_rows]
    if not rows:
        return True
    return all(str(row.get("provenance") or "").lower() in {"sample", "demo"} for row in rows)


def _demo_domain_decisions() -> dict[str, list[dict[str, Any]]]:
    return {
        "soc": [
            {
                "entity_id": "supplier-acme",
                "category": "credential_access",
                "score": 0.82,
                "timestamp": "2026-06-01T09:00:00Z",
            }
        ],
        "s2p": [
            {
                "entity_id": "supplier-acme",
                "category": "otif_drop",
                "score": 0.76,
                "timestamp": "2026-06-01T11:00:00Z",
            }
        ],
    }
