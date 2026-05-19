from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.celonis_connector import CelonisConnector
from app.sap_connector import SAPConnector


async def _raise_live_failure(*_args, **_kwargs):
    raise RuntimeError("live disabled in tests")


def test_sap_connector_cache_fallback(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    payload = _run(connector.get_purchase_orders())

    assert payload["source"] == "sap_cache"
    assert payload["total"] == 12


def test_sap_purchase_orders_cached(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    orders = _run(connector.get_purchase_orders(top=5))["purchase_orders"]

    assert len(orders) == 5
    assert {"PurchaseOrder", "CompanyCode", "Supplier", "DocumentCurrency"} <= set(orders[0])


def test_sap_supplier_invoices_cached(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    invoices = _run(connector.get_supplier_invoices())["supplier_invoices"]

    assert len(invoices) == 10
    assert invoices[0]["SupplierInvoice"]


def test_sap_suppliers_cached(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    suppliers = _run(connector.get_suppliers())["suppliers"]

    assert len(suppliers) == 10
    assert suppliers[0]["BusinessPartnerName"]


def test_sap_health_cache_connected(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    health = _run(connector.health())

    assert health["status"] == "cache"
    assert health["live"] is False
    assert health["cached_records"] == 12


def test_sap_cache_missing_returns_empty(tmp_path: Path) -> None:
    connector = SAPConnector(cache_dir=tmp_path)

    payload = _run(connector.get_purchase_orders())

    assert payload["source"] == "sap_cache"
    assert payload["total"] == 0
    assert payload["purchase_orders"] == []


def test_sap_cache_invalid_json_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "sap_purchase_orders.json").write_text("{invalid", encoding="utf-8")
    connector = SAPConnector(cache_dir=tmp_path)

    payload = _run(connector.get_purchase_orders())

    assert payload["source"] == "sap_cache"
    assert payload["total"] == 0
    assert payload["purchase_orders"] == []


def test_celonis_connector_cache_fallback(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    payload = _run(connector.get_process_data("km-p2p-dataops"))

    assert payload["source"] == "celonis_cache"
    assert payload["process_data"]["process_model"] == "Continental Tire Procure-to-Pay"


def test_celonis_knowledge_models_cached(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    models = _run(connector.get_knowledge_models())["knowledge_models"]

    assert models[0]["id"] == "km-p2p-dataops"


def test_celonis_kpis_cached(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    kpis = _run(connector.get_kpis("km-p2p-dataops"))["kpis"]

    assert any(kpi["id"] == "invoice_rework_rate" for kpi in kpis)


def test_celonis_process_data_cached(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    process_data = _run(connector.get_process_data("km-p2p-dataops"))["process_data"]

    assert process_data["variant"] == "Supplier Catalog Expansion with Invoice Rework"
    assert process_data["variant_frequency"] == 340


def test_celonis_health_cache_connected(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)
    connector._request_json = _raise_live_failure

    health = _run(connector.health())

    assert health["status"] == "cache"
    assert health["live"] is False
    assert health["cached_models"] == 2


def test_celonis_cache_missing_returns_empty_list(tmp_path: Path) -> None:
    connector = CelonisConnector(cache_dir=tmp_path)

    payload = _run(connector.get_knowledge_models())

    assert payload["source"] == "celonis_cache"
    assert payload["knowledge_models"] == []


def test_celonis_cache_missing_returns_empty_dict(tmp_path: Path) -> None:
    connector = CelonisConnector(cache_dir=tmp_path)

    payload = _run(connector.get_process_data("km-p2p-dataops"))

    assert payload["source"] == "celonis_cache"
    assert payload["process_data"] == {}


def test_celonis_cache_invalid_json_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "celonis_process_data.json").write_text("{invalid", encoding="utf-8")
    (tmp_path / "celonis_knowledge_models.json").write_text("{invalid", encoding="utf-8")
    connector = CelonisConnector(cache_dir=tmp_path)

    process_data = _run(connector.get_process_data("km-p2p-dataops"))
    models = _run(connector.get_knowledge_models())

    assert process_data["source"] == "celonis_cache"
    assert process_data["process_data"] == {}
    assert models["source"] == "celonis_cache"
    assert models["knowledge_models"] == []


def test_enterprise_health_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_connectors(monkeypatch)

    response = client.get("/api/context/enterprise-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine_version"] == "v0.7.23"
    assert payload["sap"]["source"] == "sap_cache"


def test_enterprise_health_returns_three_systems(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_connectors(monkeypatch)

    payload = client.get("/api/context/enterprise-health").json()

    assert {"sap", "celonis", "graph"} <= set(payload)
    assert payload["graph"]["pipeline_count"] > 0


def test_sap_purchase_orders_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_connectors(monkeypatch)

    payload = client.get("/api/context/sap/purchase-orders?top=3").json()

    assert payload["source"] == "sap_cache"
    assert payload["total"] == 3
    assert len(payload["purchase_orders"]) == 3


def test_celonis_process_data_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_connectors(monkeypatch)

    payload = client.get("/api/context/celonis/process-data").json()

    assert payload["source"] == "celonis_cache"
    assert payload["knowledge_models"]
    assert payload["kpis"]
    assert payload["process_data"]["process_model"] == "Continental Tire Procure-to-Pay"


def test_process_signals_includes_celonis_live(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_connectors(monkeypatch)

    payload = client.get("/api/context/process-signals/sap_mm").json()

    assert payload["celonis_live"] is False
    assert payload["sap_po_count"] == 12
    assert payload["source"] == "celonis_ems"


def test_cache_fixtures_exist(dataops_data_dir: Path) -> None:
    for name in (
        "sap_purchase_orders.json",
        "sap_supplier_invoices.json",
        "sap_suppliers.json",
        "celonis_knowledge_models.json",
        "celonis_kpis.json",
        "celonis_process_data.json",
    ):
        assert (dataops_data_dir / name).exists()


def test_celonis_process_data_has_activities(dataops_data_dir: Path) -> None:
    payload = _load_json(dataops_data_dir / "celonis_process_data.json")

    assert any(activity.get("name") == "Match Invoice to GR" for activity in payload["activities"])
    assert any(activity.get("bottleneck_cause") == "MATKL_V2" for activity in payload["activities"])


def test_celonis_process_data_has_cross_graph_insights(dataops_data_dir: Path) -> None:
    payload = _load_json(dataops_data_dir / "celonis_process_data.json")
    titles = {insight["title"] for insight in payload["cross_graph_insights"]}

    assert "Aster Rubber 9x fanout" in titles
    assert "MATKL_V2 downstream impact" in titles
    assert "$8,400/day active bottleneck" in titles
    assert any(insight.get("monthly_impact_usd") == 1449000 for insight in payload["cross_graph_insights"])


def test_celonis_process_data_has_compounding_trajectory(dataops_data_dir: Path) -> None:
    payload = _load_json(dataops_data_dir / "celonis_process_data.json")

    assert payload["compounding_trajectory"]["annual_savings_usd"] == 1620000


def test_sap_connector_live_response_parsing(dataops_data_dir: Path) -> None:
    connector = SAPConnector(cache_dir=dataops_data_dir)

    async def live_payload(*_args, **_kwargs):
        return {"d": {"results": [{"PurchaseOrder": "4500009999", "Supplier": "SUP-LIVE"}]}}

    connector._request_json = live_payload

    payload = _run(connector.get_purchase_orders())

    assert payload["source"] == "sap_live"
    assert payload["purchase_orders"] == [{"PurchaseOrder": "4500009999", "Supplier": "SUP-LIVE"}]


def test_celonis_connector_live_response_parsing(dataops_data_dir: Path) -> None:
    connector = CelonisConnector(cache_dir=dataops_data_dir)

    async def live_payload(endpoint: str, **_kwargs):
        if endpoint == "/knowledge-models":
            return {"knowledge_models": [{"id": "km-live", "name": "Live KM"}]}
        if endpoint == "/knowledge-models/km-live/kpis":
            return {"kpis": [{"id": "live-kpi", "name": "Live KPI"}]}
        return {"process_data": {"process_model": "Live Process"}}

    connector._request_json = live_payload

    assert _run(connector.get_knowledge_models())["source"] == "celonis_live"
    assert _run(connector.get_kpis("km-live"))["kpis"][0]["id"] == "live-kpi"
    assert _run(connector.get_process_data("km-live"))["process_data"]["process_model"] == "Live Process"


def _patch_context_connectors(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import context_router

    sap = SAPConnector(cache_dir=context_router.DATA_DIR)
    sap._request_json = _raise_live_failure
    celonis = CelonisConnector(cache_dir=context_router.DATA_DIR)
    celonis._request_json = _raise_live_failure
    monkeypatch.setattr(context_router, "_sap_connector", lambda: sap)
    monkeypatch.setattr(context_router, "_celonis_connector", lambda: celonis)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run(awaitable):
    import asyncio

    return asyncio.run(awaitable)
