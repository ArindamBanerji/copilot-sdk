"""Phase 6 projection and fixture-boundary contracts."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore
import sys
from pathlib import Path

from copilot_sdk.demo.preseed import DemoPreseed
from copilot_sdk.backend.evolution_router import _evolver_variants
from apps.purchasing.backend.app.services.audit_export import AuditExportService
from apps.purchasing.backend.app.services.payment_timing import PaymentTimingService
from apps.purchasing.backend.app.services.disruption_recovery import DisruptionRecoveryService


def test_g023_synthetic_preseed_tagged() -> None:
    os.environ["COPILOT_PROFILE"] = "test"
    result = DemoPreseed(fast_mode=True).preseed_trading()
    assert result.rejected_variants
    assert all(item.get("provenance") == "synthetic" for item in result.rejected_variants)


def test_g023_synthetic_excluded_from_learned_count() -> None:
    os.environ["COPILOT_PROFILE"] = "test"
    result = DemoPreseed(fast_mode=True).preseed_trading()
    learned = [item for item in result.rejected_variants if item.get("provenance") != "synthetic"]
    assert learned == []


def test_g023_production_variants_exclude_synthetic() -> None:
    class Evolver:
        def registered_variants(self):
            return [{"id": "demo", "provenance": "synthetic"}, {"id": "live", "provenance": "graph"}]
    assert [item["id"] for item in _evolver_variants(Evolver())] == ["live"]


@pytest.mark.age
@pytest.mark.parametrize("profile", ["production", "test"])
def test_g032_analytics_reads_graph_mutations(monkeypatch, profile, disposable_age) -> None:
    monkeypatch.setenv("TRADING_PROFILE", profile)
    sys.path.insert(0, str(Path(__file__).parents[2] / "apps" / "trading" / "backend"))
    import importlib
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    context_router = importlib.import_module("app.context_router")
    store = disposable_age.store("trading")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(graph_store=store, trading_selected_graph_store=store)))
    first = store.write_decision("trading", "trend_following", "buy", 0.8, {"x": 0.5})
    initial = context_router.analytics(request)
    assert initial["total_trades"] == 1
    assert initial["contrast_card"]["neutral"]["count"] == 1
    store.write_outcome(first, "buy", True, domain="trading")
    store.write_decision("trading", "risk", "hold", 0.7, {"x": 0.2})
    updated = context_router.analytics(request)
    assert updated["total_trades"] == 2
    assert updated["contrast_card"]["aligned"]["count"] == 1
    assert updated["category_counts"] == {"trend_following": 1, "risk": 1}


def test_g033_production_rejects_fixture_orders(monkeypatch) -> None:
    monkeypatch.setenv("PURCHASING_PROFILE", "production")
    from apps.purchasing.backend.app.data_helpers import is_sample_data
    # This is the production queue's sample-data policy, not a source-string assertion.
    assert is_sample_data({"provenance": "sample"})
    assert not is_sample_data({"provenance": "scraped_external", "order_id": "LIVE-1"})


def test_g033_audit_no_hardcoded_verified(monkeypatch) -> None:
    monkeypatch.setenv("PURCHASING_PROFILE", "production")
    payload = AuditExportService().generate_pack()
    assert payload["status"] == "unavailable"


def test_g033_demo_preserves_fixture_services(monkeypatch) -> None:
    monkeypatch.setenv("PURCHASING_PROFILE", "test")
    assert PaymentTimingService(profile="test").analyze()
    assert DisruptionRecoveryService(profile="test").recovery_status()["provenance"] == "demo"


def test_g034_production_rejects_local_transformations(monkeypatch) -> None:
    monkeypatch.setenv("DATAOPS_PROFILE", "production")
    from apps.dataops.backend.app.context_router import _load_transformations
    assert _load_transformations() == {}


def test_g034_production_audit_trail_graph_backed(monkeypatch) -> None:
    monkeypatch.setenv("DATAOPS_PROFILE", "production")
    from apps.dataops.backend.app import context_router
    audit_trail = context_router.audit_trail
    store = InMemoryGraphStore(domain="dataops")
    monkeypatch.setattr(context_router, "_evolution_store_factory", lambda: store)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(graph_store=store)))
    assert audit_trail("D1", request)["chain"] == []
    store.write_decision("dataops", "freshness", "rerun", 0.8, {"freshness": 0.5}, metadata={"decision_id": "D1", "system": "warehouse"})
    result = audit_trail("D1", request)
    assert result["source"] == "graph"
    assert result["system"] == "warehouse"
    assert result["chain"][0]["data"]["category"] == "freshness"
    store.write_decision("dataops", "schema", "review", 0.7, {"schema": 0.8}, metadata={"decision_id": "D2", "system": "billing"})
    assert audit_trail("D2", request)["system"] == "billing"


def test_g034_demo_preserves_process_context(monkeypatch) -> None:
    monkeypatch.setenv("DATAOPS_PROFILE", "test")
    from apps.dataops.backend.app.context_router import _load_transformations, _load_schema_changes
    assert isinstance(_load_transformations(), dict)
    assert isinstance(_load_schema_changes(), dict)


def test_g034_production_schema_changes_are_not_fixture_data(monkeypatch) -> None:
    monkeypatch.setenv("DATAOPS_PROFILE", "production")
    from apps.dataops.backend.app.context_router import _load_schema_changes
    assert _load_schema_changes() == {}
