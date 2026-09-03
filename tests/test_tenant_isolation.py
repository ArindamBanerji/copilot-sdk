"""Tests for opt-in tenant context and GraphStore scoping."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from copilot_sdk.config.tenant import TenantConfig, current_tenant_id, tenant_context, validate_tenant_id
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.tenant_store import TenantScopedGraphStore
from copilot_sdk.tenant_middleware import TenantMiddleware


def _store() -> TenantScopedGraphStore:
    return TenantScopedGraphStore(InMemoryGraphStore(domain="trading"))


def _write(store: TenantScopedGraphStore, action: str) -> str:
    return store.write_decision("trading", "market", action, 0.9, {"signal": 0.8})


def test_tenant_config_defaults_to_single_tenant() -> None:
    config = TenantConfig.load({})
    assert config.enabled is False
    assert config.default_tenant == "default"
    assert config.tenant_from_headers({"X-Tenant-Id": "other"}) == "default"


def test_tenant_config_enables_header_resolution() -> None:
    config = TenantConfig.load({"TENANT_ISOLATION_ENABLED": "true"})
    assert config.enabled is True
    assert config.tenant_from_headers({"X-Tenant-Id": "tenant-a"}) == "tenant-a"


def test_missing_header_uses_configured_default() -> None:
    config = TenantConfig.load({"TENANT_ISOLATION_ENABLED": "true", "DEFAULT_TENANT_ID": "acme"})
    assert config.tenant_from_headers({}) == "acme"


def test_invalid_tenant_id_is_rejected() -> None:
    for value in ("", "tenant with spaces", "../escape"):
        try:
            validate_tenant_id(value)
        except ValueError:
            continue
        raise AssertionError(f"invalid tenant accepted: {value!r}")


def test_context_manager_restores_previous_tenant() -> None:
    assert current_tenant_id() == "default"
    with tenant_context("tenant-a"):
        assert current_tenant_id() == "tenant-a"
    assert current_tenant_id() == "default"


def test_writes_stamp_tenant_id() -> None:
    store = _store()
    with tenant_context("tenant-a"):
        decision_id = _write(store, "buy")
        row = store.get_decision(decision_id, "trading")
    assert row is not None
    assert row["metadata"]["tenant_id"] == "tenant-a"


def test_same_domain_has_isolated_decisions() -> None:
    store = _store()
    with tenant_context("tenant-a"):
        _write(store, "buy")
    with tenant_context("tenant-b"):
        _write(store, "sell")
    with tenant_context("tenant-a"):
        assert [row["recommended_action"] for row in store.get_all_decisions("trading")] == ["buy"]
    with tenant_context("tenant-b"):
        assert [row["recommended_action"] for row in store.get_all_decisions("trading")] == ["sell"]


def test_cross_tenant_direct_read_is_hidden() -> None:
    store = _store()
    with tenant_context("tenant-a"):
        decision_id = _write(store, "buy")
    with tenant_context("tenant-b"):
        assert store.get_decision(decision_id, "trading") is None


def test_control_plane_state_isolated() -> None:
    store = _store()
    with tenant_context("tenant-a"):
        store.save_evolution("trading", "v1", {"status": "active"})
        store.save_promotion("trading", "rule-1", {"status": "candidate"})
    with tenant_context("tenant-b"):
        assert store.get_evolution("trading", "v1") is None
        assert store.get_promotion("trading", "rule-1") is None


def test_ledger_and_posterior_are_isolated() -> None:
    store = _store()
    with tenant_context("tenant-a"):
        store.save_ledger("trading", "r1", {"reward": 1.0})
        store.save_posterior("trading", "p1", {"alpha": [2.0]})
    with tenant_context("tenant-b"):
        assert store.get_ledger("trading", "r1") is None
        assert store.get_posterior("trading", "p1") is None


def test_middleware_sets_request_state_and_context() -> None:
    app = FastAPI()
    app.add_middleware(TenantMiddleware, config=TenantConfig(enabled=True))

    @app.get("/tenant")
    async def tenant(request: Request) -> dict[str, str]:
        return {"state": request.state.tenant_id, "context": current_tenant_id()}

    with TestClient(app) as client:
        response = client.get("/tenant", headers={"X-Tenant-Id": "tenant-a"})
    assert response.json() == {"state": "tenant-a", "context": "tenant-a"}


def test_middleware_uses_default_when_header_missing() -> None:
    app = FastAPI()
    app.add_middleware(TenantMiddleware, config=TenantConfig(enabled=True, default_tenant="default-org"))

    @app.get("/tenant")
    async def tenant() -> dict[str, str]:
        return {"tenant": current_tenant_id()}

    with TestClient(app) as client:
        response = client.get("/tenant")
    assert response.json() == {"tenant": "default-org"}
