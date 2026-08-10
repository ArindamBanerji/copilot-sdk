"""DataOps enterprise data routes backed by the shared ci-platform connectors."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import APIRouter


CI_PLATFORM_ROOT = Path(__file__).resolve().parents[5] / "ci-platform"
if CI_PLATFORM_ROOT.exists() and str(CI_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(CI_PLATFORM_ROOT))

from ci_platform.connectors.celonis import (  # noqa: E402
    CelonisConfig,
    CelonisProcessConnector,
    ProcessFixture,
    ProcessManifestBuilder,
)
from ci_platform.connectors.sap import (  # noqa: E402
    SAPConfig,
    SAPFixture,
    SAPManifestBuilder,
    SAPODataConnector,
)


FIXTURE_ROOT = CI_PLATFORM_ROOT / "tests" / "fixtures"
CELONIS_FIXTURE = FIXTURE_ROOT / "celonis" / "process_fixture.json"
SAP_FIXTURE = FIXTURE_ROOT / "sap"
DATAOPS_FALLBACK = Path(__file__).resolve().parents[1] / "data" / "fallback" / "pipelines.json"
LIVE_TIMEOUT_SECONDS = 2.0

ConnectorFactory = Callable[[], Any]
Operation = Callable[[Any], Awaitable[Any]]


def create_enterprise_router(
    *,
    celonis_factory: ConnectorFactory | None = None,
    sap_factory: ConnectorFactory | None = None,
) -> APIRouter:
    """Create routes with injectable connector factories for isolated tests."""

    router = APIRouter()
    make_celonis = celonis_factory or _celonis_connector
    make_sap = sap_factory or _sap_connector

    @router.get("/enterprise-health")
    async def enterprise_health() -> dict[str, Any]:
        return await build_enterprise_health(make_celonis, make_sap)

    @router.get("/process-data")
    async def process_data() -> dict[str, Any]:
        return await _load_process(make_celonis, _celonis_fixture_connector)

    @router.get("/sap-data")
    async def sap_data() -> dict[str, Any]:
        return await _load_sap(make_sap, _sap_fixture_connector)

    return router


async def build_enterprise_health(
    celonis_factory: ConnectorFactory | None = None,
    sap_factory: ConnectorFactory | None = None,
) -> dict[str, Any]:
    make_celonis = celonis_factory or _celonis_connector
    make_sap = sap_factory or _sap_connector
    celonis_health, celonis_source = await _health_with_fallback(make_celonis, _celonis_fixture_connector)
    sap_health, sap_source = await _health_with_fallback(make_sap, _sap_fixture_connector)
    process = await _load_process(make_celonis, _celonis_fixture_connector)
    sap_data = await _load_sap(make_sap, _sap_fixture_connector)
    graph = _graph_health()
    sap_metrics = _sap_metrics(sap_data)
    process_metrics = _process_metrics(process)
    sap = {
        **sap_health,
        "source": sap_source,
        "live": sap_source == "live",
        "connected": sap_source == "live",
        "last_sync": None,
        "record_count": len(sap_data["purchase_orders"]),
        **sap_metrics,
    }
    celonis = {
        **celonis_health,
        "source": celonis_source,
        "live": celonis_source == "live",
        "connected": celonis_source == "live",
        "last_sync": None,
        "kpi_count": len(process.get("variants", [])),
        **process_metrics,
    }
    connected = [sap["connected"], celonis["connected"], graph["connected"]]
    overall = "healthy" if all(connected) else "degraded" if any(connected) else "disconnected"
    return {
        "sap": sap,
        "celonis": celonis,
        "graph": graph,
        "overall": overall,
        "combined_impact": {
            "open_purchase_order_value": sap_metrics["open_purchase_order_value"],
            "exception_invoice_count": sap_metrics["exception_invoice_count"],
            "bottleneck_activity": process_metrics["bottleneck_activity"],
            "bottleneck_duration_seconds": process_metrics["bottleneck_duration_seconds"],
        },
        "engine_version": "ci-platform-connectors",
    }


async def _health_with_fallback(
    live_factory: ConnectorFactory,
    fixture_factory: ConnectorFactory,
) -> tuple[dict[str, Any], str]:
    try:
        connector = live_factory()
        result = await asyncio.wait_for(connector.health_check(), timeout=LIVE_TIMEOUT_SECONDS)
        source = "live" if _is_live(connector, result) else "fixture"
        return (result if isinstance(result, dict) else {"status": "unknown"}), source
    except Exception:
        connector = fixture_factory()
        result = await connector.health_check()
        return (result if isinstance(result, dict) else {"status": "degraded"}), "fixture"


async def _load_process(live_factory: ConnectorFactory, fixture_factory: ConnectorFactory) -> dict[str, Any]:
    try:
        connector = live_factory()
        manifest = await asyncio.wait_for(connector.to_process_manifest(), timeout=LIVE_TIMEOUT_SECONDS)
        source = "live" if _is_live(connector, {}) else "fixture"
    except Exception:
        connector = fixture_factory()
        fixture = ProcessFixture.from_json(CELONIS_FIXTURE)
        manifest = ProcessManifestBuilder(fixture).build()
        source = "fixture"

    nodes = manifest.get("nodes", []) if isinstance(manifest, dict) else []
    activities = [node for node in nodes if node.get("type") == "Activity"]
    variants = [node for node in nodes if node.get("type") == "ProcessVariant"]
    transitions = [node for node in nodes if node.get("type") == "Transition"]
    bottleneck: dict[str, Any] = max(activities, key=lambda item: float(item.get("rework_rate", 0)), default={})
    return {
        "source": source,
        "activities": activities,
        "variants": variants,
        "transitions": transitions,
        "bottleneck": {
            "activity": bottleneck.get("name"),
            "duration_seconds": bottleneck.get("avg_duration", 0),
            "rework_rate": bottleneck.get("rework_rate", 0),
        },
        "manifest_stats": manifest.get("stats", {}) if isinstance(manifest, dict) else {},
    }


async def _load_sap(live_factory: ConnectorFactory, fixture_factory: ConnectorFactory) -> dict[str, Any]:
    try:
        connector = live_factory()
        purchase_orders, invoices, suppliers = await asyncio.wait_for(
            asyncio.gather(
                connector.fetch_purchase_orders(),
                connector.fetch_invoices(),
                connector.fetch_suppliers(),
            ),
            timeout=LIVE_TIMEOUT_SECONDS,
        )
        source = "live" if _is_live(connector, {}) else "fixture"
    except Exception:
        connector = fixture_factory()
        purchase_orders = await connector.fetch_purchase_orders()
        invoices = await connector.fetch_invoices()
        suppliers = await connector.fetch_suppliers()
        source = "fixture"

    fixture = SAPFixture(
        purchase_orders=list(purchase_orders),
        invoices=list(invoices),
        suppliers=list(suppliers),
        write_response_cache={"d": {}},
    )
    manifest = SAPManifestBuilder(fixture).build()
    return {
        "source": source,
        "purchase_orders": list(purchase_orders),
        "invoices": list(invoices),
        "suppliers": list(suppliers),
        "backlog": _sap_metrics({"purchase_orders": purchase_orders, "invoices": invoices}),
        "manifest_stats": manifest.get("stats", {}),
    }


def _celonis_connector() -> CelonisProcessConnector:
    return CelonisProcessConnector(CelonisConfig.from_env(), fixture_path=CELONIS_FIXTURE)


def _celonis_fixture_connector() -> CelonisProcessConnector:
    config = CelonisConfig(use_fixture_fallback=True)
    return CelonisProcessConnector(config, fixture_path=CELONIS_FIXTURE)


def _sap_connector() -> SAPODataConnector:
    return SAPODataConnector(SAPConfig.from_env(), fixture_dir=SAP_FIXTURE)


def _sap_fixture_connector() -> SAPODataConnector:
    return SAPODataConnector(SAPConfig(use_fixture_fallback=True), fixture_dir=SAP_FIXTURE)


def _is_live(connector: Any, result: dict[str, Any]) -> bool:
    return str(result.get("source") or "").lower() in {"rest", "pycelonis", "live"} or getattr(connector, "_source", "") in {"rest", "pycelonis"}


def _sap_metrics(data: dict[str, Any]) -> dict[str, Any]:
    orders = data.get("purchase_orders", [])
    invoices = data.get("invoices", [])
    return {
        "open_purchase_order_value": sum(float(order.get("NetAmount", 0) or 0) for order in orders if str(order.get("Status", "")).lower() in {"open", "approved"}),
        "exception_invoice_count": sum(1 for invoice in invoices if str(invoice.get("MatchStatus", "")).lower() == "exception"),
    }


def _process_metrics(data: dict[str, Any]) -> dict[str, Any]:
    bottleneck = data.get("bottleneck", {})
    return {
        "bottleneck_activity": bottleneck.get("activity"),
        "bottleneck_duration_seconds": bottleneck.get("duration_seconds", 0),
    }


def _graph_health() -> dict[str, Any]:
    try:
        payload = json.loads(DATAOPS_FALLBACK.read_text(encoding="utf-8"))
        pipelines = payload.get("pipelines", []) if isinstance(payload, dict) else []
        count = len(pipelines) if isinstance(pipelines, list) else 0
    except (OSError, json.JSONDecodeError):
        count = 0
    return {"status": "ok" if count else "degraded", "source": "dataops_graph", "connected": bool(count), "node_count": count, "pipeline_count": count}


router = create_enterprise_router()
