from __future__ import annotations

import sys
import os
import importlib.util
from pathlib import Path

import pytest

from copilot_sdk.demo.connector_freeze import ConnectorFreeze
from copilot_sdk.demo.preseed import DemoPreseed, MIN_DEMO_IKS
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.verification.weather import get_weather_factor


@pytest.fixture(autouse=True)
def _test_profile_for_preseed_scorers(monkeypatch):
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)


@pytest.fixture
def preseed_result(tmp_path_factory, monkeypatch):
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)
    previous_path = os.environ.get("TRADING_EVOLUTION_LOG_PATH")
    os.environ["TRADING_EVOLUTION_LOG_PATH"] = str(
        tmp_path_factory.mktemp("preseed") / "evolution_log.json"
    )
    try:
        return DemoPreseed(seed=20260711).preseed_all()
    finally:
        if previous_path is None:
            os.environ.pop("TRADING_EVOLUTION_LOG_PATH", None)
        else:
            os.environ["TRADING_EVOLUTION_LOG_PATH"] = previous_path


def test_preseed_deterministic() -> None:
    first = DemoPreseed(seed=20260711, fast_mode=True).preseed_all()
    second = DemoPreseed(seed=20260711, fast_mode=True).preseed_all()

    assert first.stable_json() == second.stable_json()
    for name in first.copilots:
        assert first.copilots[name].iks == second.copilots[name].iks
        assert first.copilots[name].conservation == second.copilots[name].conservation
        assert first.copilots[name].decisions == second.copilots[name].decisions


def test_preseed_nonflat_iks(preseed_result) -> None:
    assert {name: copilot.iks for name, copilot in preseed_result.copilots.items()}
    assert all(copilot.iks > MIN_DEMO_IKS for copilot in preseed_result.copilots.values())


def test_preseed_pending_items(preseed_result) -> None:
    assert preseed_result.copilots["soc"].pending_alerts >= 1
    assert preseed_result.copilots["purchasing"].pending_orders >= 1


def test_preseed_f26_clean(preseed_result) -> None:
    result = preseed_result
    expected_copilots = {"trading", "purchasing", "dataops", "s2p", "soc"}
    assert set(result.copilots) == expected_copilots
    for copilot_name, copilot in result.copilots.items():
        assert copilot.raw_factor_values
        for metric_name, metric in copilot.headline_metrics.items():
            assert metric.get("provenance") != "sample", (
                f"F-26: {copilot_name} headline {metric_name} has sample provenance"
            )


def test_preseed_cross_copilot_signal(preseed_result) -> None:
    signal = preseed_result.cross_copilot_signal

    assert signal["active"] is True
    assert signal["event_type"] == "supplier_reliability_signal"
    assert signal["payload"]["provenance"] == "signal"
    assert signal["banner"]["supplier"] == signal["payload"]["supplier_name"]


def test_connector_freeze(tmp_path, monkeypatch) -> None:
    freeze = ConnectorFreeze(tmp_path)
    paths = freeze.freeze()

    assert Path(paths["fred"]).exists()
    assert Path(paths["openmeteo"]).exists()
    first_weather = get_weather_factor(use_live=True)
    second_weather = get_weather_factor(use_live=True)
    assert first_weather == second_weather

    source_path = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "purchasing"
        / "backend"
        / "app"
        / "connectors"
        / "commodity_source.py"
    )
    spec = importlib.util.spec_from_file_location("test_frozen_commodity_source", source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_frozen_commodity_source"] = module
    spec.loader.exec_module(module)
    FREDCommoditySource = module.FREDCommoditySource

    fred = FREDCommoditySource(api_key="")
    first_prices = fred.fetch_category_prices("protein")
    if first_prices is None:
        pytest.skip("FRED freeze data unavailable")
    second_prices = fred.fetch_category_prices("protein")
    assert first_prices == second_prices
    assert first_prices

    freeze.unfreeze()
    assert "FRED_FREEZE" not in os.environ
    assert "OPENMETEO_FREEZE" not in os.environ


def test_fred_freeze_integration_matches_live_baseline(tmp_path, monkeypatch) -> None:
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        pytest.skip("FRED_API_KEY not set — integration test skipped")

    source_path = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "purchasing"
        / "backend"
        / "app"
        / "connectors"
        / "commodity_source.py"
    )
    spec = importlib.util.spec_from_file_location("test_live_commodity_source", source_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_live_commodity_source"] = module
    spec.loader.exec_module(module)
    FREDCommoditySource = module.FREDCommoditySource

    monkeypatch.delenv("FRED_FREEZE", raising=False)
    live = FREDCommoditySource(api_key=api_key)
    baseline = live.fetch_category_prices("protein")
    if baseline is None:
        pytest.skip("FRED API unavailable or rejected the configured API key")
    assert baseline

    freeze = ConnectorFreeze(tmp_path)
    freeze.freeze_fred()
    frozen = FREDCommoditySource(api_key=api_key).fetch_category_prices("protein")
    assert frozen == baseline

    freeze.unfreeze()
    after_unfreeze = FREDCommoditySource(api_key=api_key).fetch_category_prices("protein")
    if after_unfreeze is None:
        pytest.skip("FRED API unavailable after unfreezing")
    assert after_unfreeze
