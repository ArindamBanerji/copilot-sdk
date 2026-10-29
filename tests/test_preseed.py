from __future__ import annotations

import sys
import os
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from copilot_sdk.demo.connector_freeze import ConnectorFreeze
from copilot_sdk.demo.preseed import DemoPreseed, MIN_DEMO_IKS
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.verification.weather import get_weather_factor


@pytest.fixture(autouse=True)
def _test_profile_for_preseed_scorers(monkeypatch):
    monkeypatch.setenv("COPILOT_PRESEED_MODE", "true")
    for domain in ("TRADING", "PURCHASING", "DATAOPS", "S2P", "SOC"):
        monkeypatch.setenv(f"{domain}_PROFILE", "test")
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", from_preset)


@pytest.fixture(scope="session")
def _shared_preseed_result(tmp_path_factory):
    # Seed once under a temporary environment, restored before any test runs.
    original = CompoundingScorer.from_preset

    def from_preset(*args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original(*args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("COPILOT_PRESEED_MODE", "true")
        for domain in ("TRADING", "PURCHASING", "DATAOPS", "S2P", "SOC"):
            patch.setenv(f"{domain}_PROFILE", "test")
        patch.setattr(CompoundingScorer, "from_preset", from_preset)
        return DemoPreseed(seed=20260711).preseed_all()


@pytest.fixture
def preseed_result(_shared_preseed_result):
    # Consumers get independent data, never a shared mutable scorer/result.
    return deepcopy(_shared_preseed_result)


def test_preseed_deterministic() -> None:
    first = DemoPreseed(seed=20260711, fast_mode=True).preseed_all()
    second = DemoPreseed(seed=20260711, fast_mode=True).preseed_all()

    assert first.stable_json() == second.stable_json()
    for name in first.copilots:
        assert first.copilots[name].iks == second.copilots[name].iks
        assert first.copilots[name].conservation == second.copilots[name].conservation
        assert first.copilots[name].decisions == second.copilots[name].decisions


def test_preseed_dataops_cycles_sample_system_metadata() -> None:
    preseed = DemoPreseed(seed=20260711)

    result = preseed.preseed_dataops()
    decisions = preseed.graph_store.get_all_decisions("dataops")
    decisions.sort(key=lambda decision: decision["metadata"]["preseed_index"])

    assert len(decisions) == result.decisions == 150
    assert [
        decision["metadata"]["pipeline_system_id"] for decision in decisions[:9]
    ] == DemoPreseed._DATAOPS_SYSTEMS
    assert all(decision["metadata"]["provenance"] == "sample" for decision in decisions)


def test_preseed_nonflat_iks(preseed_result) -> None:
    assert {name: copilot.iks for name, copilot in preseed_result.copilots.items()}
    assert all(copilot.iks > MIN_DEMO_IKS for copilot in preseed_result.copilots.values())


def test_preseed_conservation_from_live_state(monkeypatch) -> None:
    preseed = DemoPreseed(seed=20260711, fast_mode=True)
    result = preseed.preseed_all()
    for name, copilot in result.copilots.items():
        state = preseed._scorers[name].get_conservation_state()
        status = state.get("status") or state.get("state")
        assert status == copilot.conservation
        assert copilot.headline_metrics["conservation"]["value"] == status
        assert isinstance(status, str) and status


def test_preseed_verify_uses_live_conservation(monkeypatch) -> None:
    preseed = DemoPreseed(seed=20260711, fast_mode=True)
    result = preseed.preseed_all()
    scorer = preseed._scorers["trading"]
    calls = []

    def changed_state():
        calls.append(True)
        return {"status": "changed", "passed": False}

    monkeypatch.setattr(scorer, "get_conservation_state", changed_state)
    with pytest.raises(ValueError, match="conservation changed during verification"):
        preseed.verify(result)
    assert calls


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


def test_preseed_result_copy_isolates_nested_mutation(preseed_result, _shared_preseed_result) -> None:
    baseline = _shared_preseed_result.stable_json()
    preseed_result.cross_copilot_signal["payload"]["supplier_name"] = "mutated"
    preseed_result.copilots.clear()
    assert _shared_preseed_result.stable_json() == baseline


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
    """Verify freeze_fred captures data and freeze/thaw is self-consistent."""
    monkeypatch.delenv("FRED_FREEZE", raising=False)
    freeze = ConnectorFreeze(tmp_path)
    fred_path = freeze.freeze_fred()
    try:
        assert fred_path
        assert os.environ.get("FRED_FREEZE") == fred_path
        assert Path(fred_path).exists()

        with open(fred_path, encoding="utf-8") as handle:
            frozen_data = json.load(handle)
        expected_categories = {"protein", "produce", "dairy", "dry_goods", "beverages"}
        assert frozen_data["provenance"] in ("scraped_external", "synthetic_fallback")
        if frozen_data["provenance"] == "synthetic_fallback":
            # Synthetic captures generate all five categories.
            assert expected_categories.issubset(frozen_data.keys()), (
                "Synthetic fallback missing categories: "
                f"{expected_categories - frozen_data.keys()}"
            )
            categories_to_check = expected_categories
        else:
            # Live captures may contain only the categories FRED returned.
            actual_categories = expected_categories & frozen_data.keys()
            assert len(actual_categories) >= 1, "Live FRED capture returned zero categories"
            categories_to_check = actual_categories
        if not os.environ.get("FRED_API_KEY", "").strip():
            assert frozen_data["provenance"] == "synthetic_fallback", (
                "No FRED_API_KEY set — provenance must be synthetic_fallback, "
                f"got {frozen_data['provenance']!r}"
            )
        for category in categories_to_check:
            rows = frozen_data[category]
            assert isinstance(rows, list) and rows, f"Empty rows for {category}"
            assert {"date", "item", "price"}.issubset(rows[0])

        source_path = (
            Path(__file__).resolve().parents[1]
            / "apps"
            / "purchasing"
            / "backend"
            / "app"
            / "connectors"
            / "commodity_source.py"
        )
        assert source_path.exists(), f"Consumer module not found: {source_path}"
        spec = importlib.util.spec_from_file_location("test_fred_commodity_source", source_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, "test_fred_commodity_source", module)
        spec.loader.exec_module(module)
        source = module.FREDCommoditySource(api_key=os.environ.get("FRED_API_KEY", "demo_key"))
        frozen_protein = source.fetch_category_prices("protein")
        assert frozen_protein is not None
        assert frozen_protein == frozen_data["protein"]
    finally:
        freeze.unfreeze()
    assert os.environ.get("FRED_FREEZE") is None
