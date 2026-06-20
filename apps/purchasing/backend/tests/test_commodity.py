from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.purchasing.backend.app.connectors.commodity_source import FREDCommoditySource
from apps.purchasing.backend.app.connectors.mock_commodity import MockCommoditySource
from apps.purchasing.backend.app.main import create_app
from apps.purchasing.backend.app.services.commodity_data_provider import (
    COMMODITY_CATEGORIES,
    CommodityDataProvider,
)
from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.substantiation import Tier, populate_default_registry


@pytest.fixture(autouse=True)
def _no_fred_env(monkeypatch):
    """Tests must be deterministic: strip FRED key unless a test sets it."""
    monkeypatch.delenv("FRED_API_KEY", raising=False)


class FailCommoditySource:
    provenance_tier = "sample"

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        return None

    def fetch_price_index(self, category: str) -> float | None:
        return None


def _client() -> TestClient:
    return TestClient(create_app(db_path=":memory:", demo_bundle_path=False))


def test_mock_prices_all_5_categories():
    source = MockCommoditySource()

    for category in COMMODITY_CATEGORIES:
        rows = source.fetch_category_prices(category)
        assert rows is not None
        assert len(rows) == 12
        assert {"date", "item", "price", "unit"}.issubset(rows[0])


def test_mock_price_index_reasonable():
    source = MockCommoditySource()

    for category in COMMODITY_CATEGORIES:
        index = source.fetch_price_index(category)
        assert index is not None
        assert 0.8 <= index <= 1.2


def test_mock_source_provenance_is_sample():
    assert MockCommoditySource().provenance_tier == "sample"


def test_fred_source_provenance_is_scraped():
    assert FREDCommoditySource().provenance_tier == "scraped_external"


def test_provider_cascade_mock():
    result = CommodityDataProvider(source=MockCommoditySource()).get_category_prices("protein")

    assert isinstance(result, Provenanced)
    assert result.source == "sample"
    assert result.value


def test_provider_cache_hit():
    provider = CommodityDataProvider(source=MockCommoditySource())

    first = provider.get_price_index("protein")
    second = provider.get_price_index("protein")

    assert first.source == "sample"
    assert second.source == "cached"
    assert second.value == first.value


def test_provider_fixture_fallback():
    provider = CommodityDataProvider(source=FailCommoditySource())

    result = provider.get_category_prices("protein")

    assert result.source == "sample"
    assert result.label == "sample data"
    assert result.value


def test_provider_refresh_clears_cache():
    provider = CommodityDataProvider(source=MockCommoditySource())

    first = provider.get_price_index("protein")
    second = provider.get_price_index("protein")
    refresh = provider.refresh("protein")
    third = provider.get_price_index("protein")

    assert first.source == "sample"
    assert second.source == "cached"
    assert refresh.value is True
    assert third.source == "sample"


def test_router_prices_200():
    response = _client().get("/api/purchasing/commodity/prices/protein")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "sample"
    assert payload["value"]


def test_router_indices_200():
    response = _client().get("/api/purchasing/commodity/indices")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "sample"
    assert len(payload["value"]) == 5


def test_router_unknown_category():
    response = _client().get("/api/purchasing/commodity/prices/unknown")

    assert response.status_code == 404


def test_fred_source_no_key():
    source = FREDCommoditySource()

    assert source.fetch_category_prices("protein") is None
    assert source.fetch_price_index("protein") is None


def test_provider_mock_returns_sample_provenance():
    result = CommodityDataProvider(source=MockCommoditySource()).get_price_index("protein")

    assert result.source == "sample"


def test_provider_fred_returns_scraped_provenance():
    result = CommodityDataProvider(source=FREDCommoditySource(api_key="")).get_price_index("protein")

    assert result.source == "sample"
    assert result.label == "sample data"


def test_f25_no_mock_labeled_live():
    provider = CommodityDataProvider(source=MockCommoditySource())
    results = [
        provider.get_category_prices("protein"),
        provider.get_price_index("protein"),
        provider.get_all_indices(),
    ]

    assert all(result.source != "live" for result in results)
    assert all(result.source in {"sample", "cached"} for result in results)


def test_all_indices_5_categories():
    result = CommodityDataProvider(source=MockCommoditySource()).get_all_indices()

    assert result.source == "sample"
    assert result.value is not None
    assert set(result.value) == set(COMMODITY_CATEGORIES)


def test_commodity_status_200():
    response = _client().get("/api/purchasing/commodity/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "MockCommoditySource"
    assert payload["provenance_tier"] == "sample"
    assert payload["fred_active"] is False
    assert payload["categories"] == list(COMMODITY_CATEGORIES)


def test_main_wires_fred_when_key_set(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "test-key")

    response = _client().get("/api/purchasing/commodity/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "FREDCommoditySource"
    assert payload["provenance_tier"] == "scraped_external"
    assert payload["fred_active"] is True


def test_main_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    response = _client().get("/api/purchasing/commodity/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "MockCommoditySource"
    assert payload["provenance_tier"] == "sample"
    assert payload["fred_active"] is False


def test_commodity_claim_registered():
    registry = populate_default_registry()
    claim = registry.get("P-PUR-COMMODITY-K4")

    assert claim is not None
    assert claim.tier == Tier.SCRAPED
    assert claim.evidence_ref
