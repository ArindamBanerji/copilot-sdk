from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import evidence_providers
from app.factors import options, registry
from app.routers import data_import, promotion, social
from app.services.cohort_status import CohortStatusService
from app.services.claim_gate import TradingClaimRegistry
from app.services.trader_profiles import TraderProfileService
from app.services.trust_analysis import TrustAnalyzer


@pytest.mark.parametrize("value", [None, "malformed"])
def test_market_fallback_exposes_provider_unavailability(monkeypatch: pytest.MonkeyPatch, value: object) -> None:
    provider = MagicMock()
    result = MagicMock(value=value, source="fixture")
    provider.get_ohlcv.return_value = result
    provider.get_vix_current.return_value = MagicMock(value=None, source="fixture")
    monkeypatch.setattr(data_import, "_provider", provider)
    router, _store = data_import.create_data_import_router()
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/trading/market/ohlcv?ticker=SPY").json()["provider_available"] is False
    assert client.get("/api/trading/market/vix").json()["provider_source"] == "fallback"


@pytest.mark.parametrize("failure", [RuntimeError("down"), None])
def test_factor_failures_are_listed_as_degraded(monkeypatch: pytest.MonkeyPatch, failure: Exception | None) -> None:
    computer = MagicMock()
    if failure is None:
        computer.compute.return_value = None
    else:
        computer.compute.side_effect = failure
    monkeypatch.setitem(registry.TRADING_FACTOR_COMPUTERS, "signal_alignment", computer)
    result = registry.compute_factors({})
    assert result["signal_alignment"] == 0.5
    assert "signal_alignment" in result.degraded_factors
    assert result.factor_availability["signal_alignment"] is False


@pytest.mark.parametrize("ticker", [None, "SPY"])
def test_options_source_unavailability_is_explicit(monkeypatch: pytest.MonkeyPatch, ticker: object) -> None:
    monkeypatch.setattr(options, "YFINANCE_AVAILABLE", False)
    factor = options._IVRVRatioFactorLegacy()
    implied, realized, available = factor._fetch_iv_rv(ticker)
    assert (implied, realized) == (None, None)
    assert available is False


@pytest.mark.parametrize("rows", [RuntimeError("down"), None])
def test_dk_readiness_distinguishes_failure_from_zero(rows: object) -> None:
    scorer = MagicMock()
    if isinstance(rows, Exception):
        scorer.graph_store.get_decisions.side_effect = rows
    else:
        scorer.graph_store.get_decisions.return_value = rows
    remaining, available = TrustAnalyzer()._decisions_until_dk(scorer)
    assert remaining is None
    assert available is False


def test_dk_readiness_threshold_reached_is_available() -> None:
    scorer = MagicMock()
    scorer._dk_transition_threshold = 2
    scorer.graph_store.get_decisions.return_value = [{}, {}]
    assert TrustAnalyzer()._decisions_until_dk(scorer) == (0, True)


@pytest.mark.parametrize("result", [ConnectionError("down"), []])
def test_domain_context_reports_graph_availability(result: object) -> None:
    source = MagicMock()
    if isinstance(result, Exception):
        source.get_vld_context.side_effect = result
    else:
        source.get_vld_context.return_value = result
    context, sample, graph_available = evidence_providers._domain_context("T1", source, None)
    assert context == {}
    assert sample is False
    assert graph_available is (not isinstance(result, Exception))


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_trader_profiles_mark_history_unavailable(result: object) -> None:
    store = MagicMock()
    if isinstance(result, Exception):
        store.get_verified_decisions.side_effect = result
    else:
        store.get_verified_decisions.return_value = result
    service = TraderProfileService(store)
    assert service.list_traders() == []
    assert service.data_available is False


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_cohort_status_marks_decision_source_unavailable(tmp_path, result: object) -> None:
    store = MagicMock()
    store.get_all_decisions = None
    store.get_decisions = None
    if isinstance(result, Exception):
        store.get_verified_decisions.side_effect = result
    else:
        store.get_verified_decisions.return_value = result
    payload = CohortStatusService(graph_store=store, oracle_artifact_path=tmp_path / "missing.json").get_status()
    assert payload["data_available"] is False


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_promotion_conservation_failure_is_fail_closed_and_flagged(result: object) -> None:
    store = MagicMock()
    if isinstance(result, Exception):
        store.count_verified_decisions.side_effect = result
    else:
        store.count_verified_decisions.return_value = result
    payload = promotion._conservation_status(lambda: store)
    assert payload["status"] == "RED"
    assert payload["passed"] is False
    assert payload["conservation_available"] is False


def test_social_endpoint_propagates_profile_availability(monkeypatch: pytest.MonkeyPatch) -> None:
    store = MagicMock()
    store.get_verified_decisions.return_value = None
    proxy = MagicMock(graph_store=store)
    app = FastAPI()
    app.include_router(social.create_social_router(proxy))
    payload = TestClient(app).get("/api/trading/traders").json()
    assert payload["traders"] == []
    assert payload["data_available"] is False


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_trading_claim_refresh_tracks_staleness(result: object) -> None:
    graph = MagicMock()
    if isinstance(result, Exception):
        graph.get_verified_decisions.side_effect = result
    else:
        graph.get_verified_decisions.return_value = result
    registry = TradingClaimRegistry()
    registry.refresh_from_store(graph)
    assert registry.last_refresh_available is False
    assert registry.stale is True
