"""D-CEL regression checks: offline demo, HTTP contracts and cache isolation."""
import asyncio
import json
from pathlib import Path
import ssl
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.sap_connector import SAPConnector
from app.celonis_connector import CelonisConnector, DEFAULT_CELONIS_URL, DEMO_KM_ID
from app import context_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore

DATA = Path(__file__).resolve().parents[1] / "data"


def run(awaitable):
    return asyncio.run(awaitable)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for name in ("SAP_API_KEY", "SAP_BASE_URL", "CELONIS_TOKEN", "CELONIS_URL", "CELONIS_LIVE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def cache_dir(tmp_path):
    for pattern in ("sap_*.json", "celonis_*.json"):
        for source in DATA.glob(pattern):
            (tmp_path / source.name).write_bytes(source.read_bytes())
    return tmp_path


def test_offline_collections_never_use_http(cache_dir, monkeypatch):
    def no_http(*args, **kwargs):
        raise AssertionError("Offline connector attempted HTTP")
    monkeypatch.setattr(httpx, "AsyncClient", no_http)
    sap, cel = SAPConnector(cache_dir=cache_dir), CelonisConnector(cache_dir=cache_dir)
    assert run(sap.get_purchase_orders())["total"] == 12
    assert run(sap.get_supplier_invoices())["total"] == 10
    assert run(sap.get_suppliers())["total"] == 10
    assert len(run(cel.get_knowledge_models())["knowledge_models"]) == 2
    assert run(cel.get_kpis("km-p2p-dataops"))["kpis"]
    assert run(cel.get_process_data("km-p2p-dataops"))["process_data"]["activities"]
    assert run(sap.health())["cached"] is True
    assert run(cel.health())["cached"] is True


def test_sap_explicit_key_and_env_fallback(monkeypatch):
    monkeypatch.setenv("SAP_API_KEY", "env-key")
    assert SAPConnector().api_key == "env-key"
    assert SAPConnector(api_key="explicit").api_key == "explicit"
    assert not SAPConnector(api_key="")._live_enabled


@pytest.mark.parametrize("method,entity", [
    ("get_purchase_orders", "API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"),
    ("get_supplier_invoices", "API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice"),
    ("get_suppliers", "API_BUSINESS_PARTNER/A_BusinessPartner"),
])
def test_sap_http_contract(cache_dir, monkeypatch, method, entity):
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"d": {"results": [{"id": "live"}]}})
    client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: client(transport=httpx.MockTransport(handler), **kw))
    sap = SAPConnector(api_key="test-key", cache_dir=cache_dir)
    payload = run(getattr(sap, method)(top=3, skip=2))
    assert payload["source"] == "sap_live"
    assert seen[0].url.path.endswith(entity)
    assert seen[0].headers["APIKey"] == "test-key"
    assert dict(seen[0].url.params) == {"$top": "3", "$skip": "2", "$format": "json"}
    assert run(getattr(sap, method)(top=3, skip=2))["source"] == "sap_cache"
    assert len(seen) == 1


def test_sap_offline_pagination(cache_dir):
    sap = SAPConnector(cache_dir=cache_dir)
    all_rows = run(sap.get_purchase_orders())["purchase_orders"]
    assert run(sap.get_purchase_orders(top=3, skip=2))["purchase_orders"] == all_rows[2:5]


def test_celonis_http_contract_and_paged_response(cache_dir, monkeypatch):
    seen = []
    def handler(request):
        seen.append(request)
        if request.url.path.endswith("/knowledge-models"):
            return httpx.Response(200, json={"content": [{"id": DEMO_KM_ID}]})
        if request.url.path.endswith("/kpis"):
            return httpx.Response(200, json=[{"id": "AVG_EVENTS_PER_CASE"}])
        return httpx.Response(200, json={"content": {"headers": [], "rows": []}, "total": 0})
    client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: client(transport=httpx.MockTransport(handler), **kw))
    cel = CelonisConnector(base_url=DEFAULT_CELONIS_URL, cache_dir=cache_dir)
    assert run(cel.get_knowledge_models())["knowledge_models"][0]["id"] == DEMO_KM_ID
    assert run(cel.get_kpis(DEMO_KM_ID))["kpis"]
    data = run(cel.get_process_data(DEMO_KM_ID))
    assert data["provenance"] == "sandbox"
    assert data["source"] == "celonis_live"
    assert "activities" not in data["process_data"]  # no invented duration data
    assert seen[-1].url.path.endswith(f"/{DEMO_KM_ID}/data")
    assert seen[-1].url.params["fields"] == "MATERIALS.ACTIVITY"
    assert seen[-1].url.params["kpis"] == "AVG_EVENTS_PER_CASE,FILTERED_COUNT"
    assert seen[-1].headers["Authorization"] == "Bearer demo-token"


@pytest.mark.parametrize("kind", ["sap", "celonis"])
def test_cache_roundtrip_and_failure_after_restart(cache_dir, kind):
    factory = SAPConnector if kind == "sap" else CelonisConnector
    first = factory(cache_dir=cache_dir)
    data = {"d": {"results": [{"PurchaseOrder": "captured"}]}} if kind == "sap" else {"content": [{"id": "captured"}]}
    first._request_json = AsyncMock(return_value=data)
    method = "get_purchase_orders" if kind == "sap" else "get_knowledge_models"
    key = "purchase_orders" if kind == "sap" else "knowledge_models"
    initial = run(getattr(first, method)())
    assert initial["source"] == f"{kind}_live"
    # Returned data cannot mutate the stored snapshot.
    initial[key][0]["mutated"] = True
    second = factory(cache_dir=cache_dir)
    second._request_json = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
    cached = run(getattr(second, method)())
    assert cached["source"] == f"{kind}_cache"
    assert "mutated" not in cached[key][0]
    assert "captured" in str(cached[key])
    assert json.loads(next((cache_dir / "connector_snapshots").glob("*.json")).read_text()) == data


def test_cache_isolated_by_page_and_credentials(cache_dir):
    sap = SAPConnector(api_key="one", cache_dir=cache_dir)
    sap._request_json = AsyncMock(return_value={"d": {"results": [{"PurchaseOrder": "captured"}]}})
    run(sap.get_purchase_orders(top=1))
    other = SAPConnector(api_key="two", cache_dir=cache_dir)
    other._request_json = AsyncMock(side_effect=httpx.ConnectError("offline"))
    assert "captured" not in str(run(other.get_purchase_orders(top=1)))
    sap._request_json = AsyncMock(side_effect=httpx.ConnectError("offline"))
    assert "captured" not in str(run(sap.get_purchase_orders(top=1, skip=1)))


@pytest.mark.parametrize("error", [httpx.ConnectError("TLS verification failed"), httpx.ReadTimeout("timeout"), ssl.SSLCertVerificationError("certificate")])
def test_celonis_tls_and_timeout_fallback(cache_dir, error, caplog):
    cel = CelonisConnector(base_url=DEFAULT_CELONIS_URL, cache_dir=cache_dir)
    cel._request_json = AsyncMock(side_effect=error)
    assert run(cel.get_knowledge_models())["source"] == "celonis_cache"
    assert run(cel.get_knowledge_models())["knowledge_models"]
    assert cel._request_json.await_count == 1
    assert "cached fallback" in caplog.text


def test_bad_response_does_not_replace_good_cache(cache_dir):
    sap = SAPConnector(cache_dir=cache_dir)
    good = {"d": {"results": [{"PurchaseOrder": "good"}]}}
    sap._request_json = AsyncMock(return_value=good)
    run(sap.get_purchase_orders())
    second = SAPConnector(cache_dir=cache_dir)
    second._request_json = AsyncMock(return_value={"error": "bad data"})
    assert run(second.get_purchase_orders())["purchase_orders"] == good["d"]["results"]


def test_unknown_km_never_uses_p2p_sample(cache_dir):
    cel = CelonisConnector(cache_dir=cache_dir)
    assert run(cel.get_kpis("customer-km"))["kpis"] == []
    assert run(cel.get_process_data("customer-km"))["process_data"] == {}


def test_missing_cache_health_unavailable(tmp_path):
    assert run(SAPConnector(cache_dir=tmp_path).health())["status"] == "unavailable"
    assert run(CelonisConnector(cache_dir=tmp_path).health())["status"] == "unavailable"


def test_corrupt_cache_health_unavailable(tmp_path):
    (tmp_path / "sap_purchase_orders.json").write_text("{bad")
    (tmp_path / "celonis_knowledge_models.json").write_text("{bad")
    assert run(SAPConnector(cache_dir=tmp_path).health())["status"] == "unavailable"
    assert run(CelonisConnector(cache_dir=tmp_path).health())["status"] == "unavailable"


def test_context_health_shape_and_graph_failure(cache_dir, monkeypatch):
    monkeypatch.setattr(context_router, "_sap_connector", lambda: SAPConnector(cache_dir=cache_dir))
    monkeypatch.setattr(context_router, "_celonis_connector", lambda: CelonisConnector(cache_dir=cache_dir))
    class Graph:
        graph_source = "fixture"
        async def get_pipelines(self):
            return {"pipelines": [{"name": "sap_mm"}]}
    monkeypatch.setattr(context_router, "_graph_client", Graph)
    app = FastAPI()
    app.include_router(context_router.router, prefix="/api/context")
    client = TestClient(app)
    response = client.get("/api/context/enterprise-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sap"]["record_count"] == 12
    assert payload["celonis"]["kpi_count"] > 0
    assert payload["graph"]["pipeline_count"] == 1
    assert payload["graph"]["connected"] is False
    assert payload["fusion_ready"] is True
    assert payload["overall"] == "degraded"
    async def failed(self):
        raise RuntimeError("Graph unavailable")
    monkeypatch.setattr(Graph, "get_pipelines", failed)
    assert client.get("/api/context/enterprise-health").json()["fusion_ready"] is False


def test_timeline_graph_empty_shape():
    app = FastAPI()
    app.state.graph_store = InMemoryGraphStore(domain="dataops")
    app.include_router(context_router.router, prefix="/api/context")
    payload = TestClient(app).get("/api/context/process-timeline").json()
    assert payload["source"] == "graph"
    assert payload["activities"] == []
    assert payload["total"] == 0
