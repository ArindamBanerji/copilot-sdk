from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_dataops_celonis = _load_module(
    "dataops_celonis_for_f26_tests",
    ROOT / "apps" / "dataops" / "backend" / "app" / "celonis_connector.py",
)
_dataops_dq = _load_module(
    "dataops_dq_benchmark_for_f26_tests",
    ROOT
    / "apps"
    / "dataops"
    / "backend"
    / "app"
    / "connectors"
    / "dq_benchmark_provider.py",
)
_dataops_data_helpers = _load_module(
    "dataops_data_helpers_for_f26_tests",
    ROOT / "apps" / "dataops" / "backend" / "app" / "data_helpers.py",
)
_dataops_sap = _load_module(
    "dataops_sap_for_f26_tests",
    ROOT / "apps" / "dataops" / "backend" / "app" / "sap_connector.py",
)
_purchasing_data_helpers = _load_module(
    "purchasing_data_helpers_for_f26_tests",
    ROOT / "apps" / "purchasing" / "backend" / "app" / "data_helpers.py",
)
_purchasing_par = _load_module(
    "purchasing_par_optimizer_for_f26_tests",
    ROOT / "apps" / "purchasing" / "backend" / "app" / "services" / "par_optimizer.py",
)
_purchasing_spend = _load_module(
    "purchasing_spend_dashboard_for_f26_tests",
    ROOT / "apps" / "purchasing" / "backend" / "app" / "services" / "spend_dashboard.py",
)
_purchasing_scorecard = _load_module(
    "purchasing_supplier_scorecard_for_f26_tests",
    ROOT
    / "apps"
    / "purchasing"
    / "backend"
    / "app"
    / "services"
    / "supplier_scorecard.py",
)
_trading_market_source = _load_module(
    "trading_market_source_for_f26_tests",
    ROOT / "apps" / "trading" / "backend" / "app" / "connectors" / "market_source.py",
)
_trading_data_helpers = _load_module(
    "trading_data_helpers_for_f26_tests",
    ROOT / "apps" / "trading" / "backend" / "app" / "data_helpers.py",
)
CelonisConnector = _dataops_celonis.CelonisConnector
DQBenchmarkProvider = _dataops_dq.DQBenchmarkProvider
MockDQBenchmarkProvider = _dataops_dq.MockDQBenchmarkProvider
dataops_gate = _dataops_data_helpers.assert_no_sample_in_metric
SAPConnector = _dataops_sap.SAPConnector
purchasing_gate = _purchasing_data_helpers.assert_no_sample_in_metric
ParLevelOptimizer = _purchasing_par.ParLevelOptimizer
SpendDashboardService = _purchasing_spend.SpendDashboardService
SupplierScorecardService = _purchasing_scorecard.SupplierScorecardService
MockMarketSource = _trading_market_source.MockMarketSource
YFinanceSource = _trading_market_source.YFinanceSource
trading_gate = _trading_data_helpers.assert_no_sample_in_metric


class _ErrorSchemaSource:
    provenance_tier = "scraped_external"

    def __init__(self, error: Exception):
        self.error = error

    def fetch_schema(self, entity_type: str) -> dict:
        raise self.error


class _EmptySchemaSource:
    provenance_tier = "scraped_external"

    def fetch_schema(self, entity_type: str) -> None:
        return None


def test_f26_spend_dashboard_rejects_sample():
    records = [_spend_order("sample")]
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        purchasing_gate(records, "spend_dashboard")


def test_f26_par_optimizer_rejects_sample():
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        ParLevelOptimizer().recommend(
            "flour",
            "dry_goods",
            _par_orders("sample"),
            current_par=20,
            unit_cost=4,
        )


def test_f26_scorecard_rejects_sample():
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        SupplierScorecardService(_scorecard_orders("sample"), [_vendor("sample")])


def test_f26_clean_data_passes():
    records = [_spend_order("scraped_external")]
    purchasing_gate(records, "spend_dashboard")
    assert SpendDashboardService(records).summary()["total_spend"] > 0

    rec = ParLevelOptimizer().recommend(
        "flour",
        "dry_goods",
        _par_orders("scraped_external"),
        current_par=20,
        unit_cost=4,
    )
    assert rec.provenance == "scraped_external"

    service = SupplierScorecardService(
        _scorecard_orders("scraped_external"),
        [_vendor("scraped_external")],
    )
    assert service.build_scorecard("SUP-1") is not None


def test_f26_trading_market_mock_labeled_sample():
    source = MockMarketSource()
    assert source.provenance_tier == "sample"
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        trading_gate([{"provenance": source.provenance_tier}], "market_data")


def test_f26_trading_real_passes():
    source = YFinanceSource()
    assert source.provenance_tier == "scraped_external"
    trading_gate([{"provenance": source.provenance_tier}], "market_data")


def test_f26_dataops_sap_labeled_sample():
    assert SAPConnector().provenance_tier == "sample"


def test_f26_dataops_celonis_labeled_sample():
    assert CelonisConnector().provenance_tier == "sample"


def test_f26_dataops_dq_mock_labeled_sample():
    provider = MockDQBenchmarkProvider()
    assert provider.provenance_tier == "sample"
    with pytest.raises(ValueError, match="F-26 VIOLATION"):
        dataops_gate(provider.quality_dimensions().value, "dq_benchmark")


def test_f26_dataops_dq_real_labeled_external():
    provider = DQBenchmarkProvider()
    assert provider.provenance_tier == "scraped_external"
    dataops_gate(provider.quality_dimensions().value, "dq_benchmark")


def test_dq_network_error_falls_to_cache(tmp_path: Path):
    _write_schema_cache(tmp_path, "Person", {"name": "Person", "properties": ["name"]})
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=_ErrorSchemaSource(ConnectionError("offline")),
    )
    result = provider.schema_for_entity("Person")
    assert result.source == "cached"


def test_dq_malformed_json_falls_to_cache(tmp_path: Path):
    provider = DQBenchmarkProvider(
        cache_dir=tmp_path,
        source=_ErrorSchemaSource(ValueError("malformed json")),
    )
    result = provider.schema_for_entity("Person")
    assert result.source == "sample"
    assert result.value["provenance"] == "sample"


def test_dq_empty_response_not_cached(tmp_path: Path):
    provider = DQBenchmarkProvider(cache_dir=tmp_path, source=_EmptySchemaSource())
    result = provider.schema_for_entity("Person")
    assert result.source == "sample"
    assert not (tmp_path / "person.json").exists()


def _spend_order(provenance: str) -> dict:
    return {
        "order_id": "ORD-1",
        "order_date": "2026-01-01",
        "category": "dry_goods",
        "supplier_id": "SUP-1",
        "supplier_name": "Flour House",
        "amount": 100.0,
        "covers": 25,
        "provenance": provenance,
        "items": [{"item_name": "flour", "quantity": 10, "unit_price": 10.0}],
    }


def _par_orders(provenance: str) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "order_id": f"QBO-{idx}",
            "order_date": (start + timedelta(days=idx)).date().isoformat(),
            "provenance": provenance,
            "items": [
                {
                    "item_name": "flour",
                    "category": "dry_goods",
                    "quantity": 12 + (idx % 3),
                    "unit_price": 4.0,
                }
            ],
        }
        for idx in range(40)
    ]


def _scorecard_orders(provenance: str) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "order_id": f"ORD-{idx}",
            "supplier_id": "SUP-1",
            "supplier_name": "Flour House",
            "order_date": (start + timedelta(days=idx)).date().isoformat(),
            "purchase_order_date": (start + timedelta(days=idx)).date().isoformat(),
            "expected_delivery_date": (start + timedelta(days=idx + 2)).date().isoformat(),
            "invoice_date": (start + timedelta(days=idx + 2)).date().isoformat(),
            "amount": 100 + idx,
            "provenance": provenance,
            "items": [{"item_name": "flour", "quantity": 10, "unit_price": 10 + idx}],
        }
        for idx in range(8)
    ]


def _vendor(provenance: str) -> dict:
    return {
        "supplier_id": "SUP-1",
        "supplier_name": "Flour House",
        "provenance": provenance,
    }


def _write_schema_cache(tmp_path: Path, entity_type: str, value: dict) -> None:
    payload = {"as_of": datetime.now(timezone.utc).isoformat(), "value": value}
    (tmp_path / f"{entity_type.lower()}.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
