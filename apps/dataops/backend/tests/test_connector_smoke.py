"""Offline D-CEL smoke tests against the requested integration contracts.

All caches and app databases use pytest temporary directories. The existing
``client`` fixture builds the real DataOps app via ``app.main.create_app``.
No test installs routes, supplies fake endpoint responses, or fabricates
connector evidence.

The investigation contract checks connector provenance on the mounted scorer's
canonical factors. Schema/transform names from the separate multihop experiment
must not rename those model dimensions. Only an absent investigation route
permits a skip.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import httpx
import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_PACKAGE = "apps.dataops.backend.app"


@pytest.fixture(autouse=True)
def offline_connectors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Remove ambient credentials and detect even swallowed HTTP attempts."""
    for name in (
        "SAP_API_KEY", "SAP_BASE_URL", "CELONIS_TOKEN", "CELONIS_URL",
        "CELONIS_LIVE", "SNOWFLAKE_ACCOUNT", "DBT_API_TOKEN", "AIRFLOW_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(tmp_path / "outbox.db"))
    send = AsyncMock(side_effect=AssertionError("Offline smoke test attempted HTTP"))
    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    yield
    # ConnectorCache catches Exception, including AssertionError. Check outside
    # that fallback handler so an accidental live request cannot silently pass.
    send.assert_not_called()


@pytest.fixture()
def connector_samples(tmp_path: Path) -> Path:
    target = tmp_path / "connector_samples"
    target.mkdir()
    for name in ("sap_purchase_orders.json", "celonis_knowledge_models.json"):
        shutil.copyfile(BACKEND_ROOT / "data" / name, target / name)
    return target


@pytest.fixture()
def smoke_client(client: TestClient):
    # Enter lifespan for the production app's startup/teardown, with the
    # existing conftest's isolated database and copied DataOps fixtures.
    with client:
        yield client


def test_sap_connector_cached_fallback(connector_samples: Path) -> None:
    module = importlib.import_module(f"{CONNECTOR_PACKAGE}.sap_connector")
    connector = module.SAPConnector(api_key="", cache_dir=connector_samples)

    payload = asyncio.run(connector.get_purchase_orders())

    assert isinstance(payload, dict)
    assert payload["source"] == "sap_cache"
    assert payload["provenance"] == "sample"
    assert payload["total"] == len(payload["purchase_orders"]) > 0
    assert all(isinstance(row, dict) and row.get("PurchaseOrder") for row in payload["purchase_orders"])
    # A successful repeated read still uses the copied fixture, not HTTP.
    assert asyncio.run(connector.get_purchase_orders()) == payload


def test_celonis_connector_cached_fallback(connector_samples: Path) -> None:
    module = importlib.import_module(f"{CONNECTOR_PACKAGE}.celonis_connector")
    connector = module.CelonisConnector(token="", cache_dir=connector_samples)

    payload = asyncio.run(connector.get_knowledge_models())

    assert isinstance(payload, dict)
    assert payload["source"] == "celonis_cache"
    assert payload["provenance"] == "sample"
    assert payload["knowledge_models"]
    assert all(isinstance(row, dict) and row.get("id") for row in payload["knowledge_models"])
    assert asyncio.run(connector.get_knowledge_models()) == payload


def test_connector_cache_roundtrip(tmp_path: Path) -> None:
    module = importlib.import_module(f"{CONNECTOR_PACKAGE}.connector_cache")
    cache = module.ConnectorCache(tmp_path, "connector-smoke")
    endpoint, params = "/purchase-orders", {"$top": "2", "$skip": "0"}
    key = cache.key(endpoint, params)
    payload = {"d": {"results": [{"PurchaseOrder": "smoke-001", "items": [1, 2], "note": None}]}}

    cache.save(key, payload)

    assert cache.load(key) == payload
    restarted = module.ConnectorCache(tmp_path, "connector-smoke")
    assert restarted.load(restarted.key(endpoint, params)) == payload
    assert restarted.load(restarted.key(endpoint, {"$top": "2", "$skip": "2"})) is None
    loaded = restarted.load(key)
    loaded["d"]["results"][0]["items"].append(3)
    assert restarted.load(key) == payload


def test_enterprise_health_endpoint(smoke_client: TestClient) -> None:
    response = smoke_client.get("/api/enterprise-health")

    assert response.status_code == 200, (
        f"Requested /api/enterprise-health returned {response.status_code}: {response.text}; "
        "current D-CEL health route: /api/context/enterprise-health"
    )
    payload = response.json()
    assert {"status", "connectors", "last_refresh"} <= payload.keys()
    assert isinstance(payload["status"], str) and payload["status"]
    assert isinstance(payload["connectors"], list) and payload["connectors"]


def test_dashboard_includes_connector_data(smoke_client: TestClient) -> None:
    response = smoke_client.get("/api/context/pipelines")

    assert response.status_code == 200, response.text
    payload = response.json()
    pipelines = payload["pipelines"]
    assert isinstance(pipelines, list) and pipelines
    assert payload["source"] == "graph"
    assert all(
        isinstance(row, dict)
        and row.get("name")
        and row.get("domain") == "dataops"
        and int(row.get("decision_count", 0)) > 0
        for row in pipelines
    )


def test_connector_absolute_imports() -> None:
    cache_module = importlib.import_module(f"{CONNECTOR_PACKAGE}.connector_cache")
    for stem, class_name in (("celonis_connector", "CelonisConnector"), ("sap_connector", "SAPConnector")):
        module = importlib.import_module(f"{CONNECTOR_PACKAGE}.{stem}")
        assert getattr(module, class_name).__module__ == module.__name__
        assert module.ConnectorCache is cache_module.ConnectorCache

        # Package imports alone also accept relative imports and may be cached
        # by other tests. Execute a fresh standalone module without a package:
        # reverting `from apps...connector_cache` to `.connector_cache` fails.
        spec = importlib.util.spec_from_file_location(f"_smoke_{stem}", BACKEND_ROOT / "app" / f"{stem}.py")
        assert spec is not None and spec.loader is not None
        standalone = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(standalone)
        assert standalone.ConnectorCache is cache_module.ConnectorCache
        assert getattr(standalone, class_name)


def test_investigation_with_connector_evidence(smoke_client: TestClient, dataops_data_dir: Path) -> None:
    path = "/api/investigation/investigate"
    if not any(
        getattr(route, "path", None) == path and "POST" in (getattr(route, "methods", None) or ())
        for route in smoke_client.app.routes
    ):
        pytest.skip("investigation endpoint not mounted")

    request = {
        "decision_id": "ALERT-TIRE-001",
        "category": "schema_change",
        "factor_vector": [0.55, 0.55, 0.30, 0.35, 0.55, 0.70],
        "budget": 6,
        "use_K": False,
    }
    response = smoke_client.post(path, json=request)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["decision_id"] == "ALERT-TIRE-001"
    assert payload["category"] == "schema_change"
    steps = payload["steps"]
    assert isinstance(steps, list) and steps
    expected = {("impact_scope", "schema_registry+sap_cache:sample"),
                ("source_reliability", "pipeline_monitor+celonis_cache:sample")}
    sourced = {
        (step["factor_name"], step["evidence_source"])
        for step in steps
        if any(name in str(step.get("evidence_source", "")).lower() for name in ("sap", "celonis"))
        and step.get("status") == "acquired"
        and step.get("evidence_value") is not None
    }
    observed = [(step.get("factor_name"), step.get("evidence_source")) for step in steps]
    assert expected <= sourced, (
        f"Missing canonical factor/connector pairs: {sorted(expected - sourced)}; "
        f"actual trace factor/source pairs: {json.dumps(observed)}"
    )
    names = payload["snapshot"]["factor_names"]
    assert names == ["impact_scope", "source_reliability", "recurrence_frequency",
                     "downstream_urgency", "data_freshness", "business_criticality"]
    assert all(step["factor_name"] == names[step["dimension"]] for step in steps)
    by_factor = {step["factor_name"]: step for step in steps if step["status"] == "acquired"}
    assert by_factor["source_reliability"]["evidence_value"] == pytest.approx(252 / (0.7 * 3600))
    schema = by_factor["impact_scope"]
    dim = schema["dimension"]
    assert schema["v_after"][dim] == pytest.approx(
        schema["evidence_confidence"] * schema["evidence_value"]
        + (1 - schema["evidence_confidence"]) * schema["v_before"][dim]
    ), "Connector provenance must preserve the schema confidence gate"

    # Perturb only this test's copied cache records. The real route must read
    # them again for the next investigation and use the changed numbers.
    sap_path = dataops_data_dir / "sap_purchase_orders.json"
    orders = json.loads(sap_path.read_text(encoding="utf-8"))
    supplier_orders = [row for row in orders if row.get("SupplierName") == "Aster Rubber"]
    assert supplier_orders and len(supplier_orders) < len(orders)
    sap_path.write_text(json.dumps(supplier_orders), encoding="utf-8")
    celonis_path = dataops_data_dir / "celonis_process_data.json"
    process = json.loads(celonis_path.read_text(encoding="utf-8"))
    activity = next(row for row in process["activities"] if row["name"] == "Match Invoice to GR")
    activity["avg_duration_hours"] = 252 / 3600
    celonis_path.write_text(json.dumps(process), encoding="utf-8")
    changed = smoke_client.post(path, json=request)
    assert changed.status_code == 200, changed.text
    changed_steps = {step["factor_name"]: step for step in changed.json()["steps"] if step["status"] == "acquired"}
    assert changed_steps["impact_scope"]["evidence_value"] == 1.0
    assert changed_steps["impact_scope"]["evidence_value"] > schema["evidence_value"]
    assert changed_steps["source_reliability"]["evidence_value"] > by_factor["source_reliability"]["evidence_value"]
    assert changed.json()["snapshot"]["geometry_hash"] == payload["snapshot"]["geometry_hash"]

    # Missing SAP and malformed Celonis caches must restore the original
    # providers, with no connector provenance claimed for unavailable evidence.
    sap_path.unlink()
    celonis_path.write_text("{invalid", encoding="utf-8")
    fallback = smoke_client.post(path, json=request)
    assert fallback.status_code == 200, fallback.text
    fallback_steps = {step["factor_name"]: step for step in fallback.json()["steps"] if step["status"] == "acquired"}
    assert fallback_steps["impact_scope"]["evidence_source"] == "schema_registry"
    assert fallback_steps["source_reliability"]["evidence_source"] == "pipeline_monitor"
    assert fallback_steps["impact_scope"]["evidence_value"] == schema["evidence_value"]
    assert fallback.json()["snapshot"]["geometry_hash"] == payload["snapshot"]["geometry_hash"]
