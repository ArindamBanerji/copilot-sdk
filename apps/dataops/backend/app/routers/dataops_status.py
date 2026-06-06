"""Domain-prefixed DataOps status aliases."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DOMAIN = "dataops"

router = APIRouter(prefix="/api/dataops", tags=["dataops-status"])


@router.get("/health")
def dataops_health() -> dict[str, Any]:
    connectors = {
        "celonis": _celonis_status(),
        "sap": _sap_status(),
    }
    connector_states = {state["status"] for state in connectors.values()}
    status = "healthy" if connector_states <= {"available", "configured", "fixture"} else "degraded"
    return {
        "status": status,
        "domain": DOMAIN,
        "scorer": {
            "status": "available",
            "source": "generic_api",
            "path": "/api/health",
        },
        "conservation": {
            "status": "available",
            "source": "generic_api",
            "path": "/api/conservation/status",
        },
        "connectors": connectors,
    }


@router.get("/celonis/status")
def celonis_status() -> dict[str, Any]:
    return _celonis_status()


@router.get("/sap/status")
def sap_status() -> dict[str, Any]:
    return _sap_status()


@router.get("/enterprise-health")
def enterprise_health_alias() -> dict[str, Any]:
    sap = _enterprise_sap_health()
    celonis = _enterprise_celonis_health()
    graph = _enterprise_graph_health()
    connected = [sap["connected"], celonis["connected"], graph["connected"]]
    if all(connected):
        overall = "healthy"
    elif any(connected):
        overall = "degraded"
    else:
        overall = "disconnected"
    return {
        "sap": sap,
        "celonis": celonis,
        "graph": graph,
        "overall": overall,
    }


def _enterprise_sap_health() -> dict[str, Any]:
    try:
        status = _sap_status()
    except Exception:
        status = {}
    return {
        "connected": _is_status_connected(status),
        "record_count": _safe_int(status.get("cached_records")),
        "last_sync": _safe_timestamp(status),
    }


def _enterprise_celonis_health() -> dict[str, Any]:
    try:
        status = _celonis_status()
    except Exception:
        status = {}
    return {
        "connected": _is_status_connected(status),
        "kpi_count": _safe_int(status.get("cached_models")),
        "last_sync": _safe_timestamp(status),
    }


def _enterprise_graph_health() -> dict[str, Any]:
    try:
        node_count = _pipeline_count()
    except Exception:
        node_count = 0
    return {
        "connected": node_count > 0,
        "node_count": node_count,
    }


def _is_status_connected(status: dict[str, Any]) -> bool:
    if status.get("connected") is not None:
        return bool(status.get("connected"))
    if status.get("live") is True:
        return True
    return str(status.get("status") or "").lower() in {"available", "configured", "fixture", "cache", "ok"}


def _safe_int(value: Any) -> int:
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _safe_timestamp(status: dict[str, Any]) -> str | None:
    for key in ("last_sync", "lastSync", "updated_at", "updatedAt", "timestamp"):
        value = status.get(key)
        if isinstance(value, str):
            return value
    return None


def _celonis_status() -> dict[str, Any]:
    configured = bool(os.getenv("CELONIS_URL") or os.getenv("CELONIS_TOKEN"))
    models = _fixture_list("celonis_knowledge_models.json")
    process_data = _fixture_dict("celonis_process_data.json")
    if models or process_data:
        status = "configured" if configured else "fixture"
        source = "config" if configured else "fixture"
        connection_state = "configured_with_fixture_fallback" if configured else "fixture_available"
    else:
        status = "configured" if configured else "unconfigured"
        source = "config" if configured else "unknown"
        connection_state = "configured_no_fixture" if configured else "missing_fixture"
    return {
        "connector": "celonis",
        "status": status,
        "connection_state": connection_state,
        "source": source,
        "live": False,
        "configured": configured,
        "cached_models": len(models),
        "process_fixture": bool(process_data),
    }


def _sap_status() -> dict[str, Any]:
    configured = bool(os.getenv("SAP_BASE_URL") or os.getenv("SAP_API_KEY"))
    orders = _fixture_list("sap_purchase_orders.json")
    if orders:
        status = "configured" if configured else "fixture"
        source = "config" if configured else "fixture"
        connection_state = "configured_with_fixture_fallback" if configured else "fixture_available"
    else:
        status = "configured" if configured else "unconfigured"
        source = "config" if configured else "unknown"
        connection_state = "configured_no_fixture" if configured else "missing_fixture"
    return {
        "connector": "sap",
        "status": status,
        "connection_state": connection_state,
        "source": source,
        "live": False,
        "configured": configured,
        "cached_records": len(orders),
    }


def _pipeline_count() -> int:
    payload = _fixture_dict("fallback/pipelines.json")
    pipelines = payload.get("pipelines") if isinstance(payload, dict) else None
    return len(pipelines) if isinstance(pipelines, list) else 0


def _fixture_list(name: str) -> list[dict[str, Any]]:
    payload = _load_fixture(name)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _fixture_dict(name: str) -> dict[str, Any]:
    payload = _load_fixture(name)
    return payload if isinstance(payload, dict) else {}


def _load_fixture(name: str) -> Any:
    path = DATA_DIR / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
