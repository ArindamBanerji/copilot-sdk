from __future__ import annotations

from pathlib import Path

import pytest

import cli
from app.evidence import TradingTemplateEngine
from app.factors import options
from app.factors.options import (
    OPTIONS_FACTOR_COMPUTERS,
    OPTIONS_FACTOR_NAMES,
    GreeksExposureFactor,
    IVRVRatioFactor,
    ThetaEfficiencyFactor,
    compute_options_factors,
)
from app.factors.registry import ALL_FACTOR_NAMES, compute_factors
from app.routers import prescore
from app.routers.data_import import _trade_store_ref
from app.services.regime import RegimeService
from copilot_sdk.scoring.presets.trading import TradingPreset


@pytest.fixture(autouse=True)
def no_yfinance(monkeypatch):
    monkeypatch.setattr(options, "YFINANCE_AVAILABLE", False)
    yield


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


@pytest.fixture(autouse=True)
def default_regime(monkeypatch):
    monkeypatch.setattr(
        RegimeService,
        "get_current_regime",
        lambda self: {
            "regime": "ranging",
            "vix": 20.0,
            "adx": 20.0,
            "spy_price": 0.0,
            "source": "default",
        },
    )
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {})


def _context(**overrides):
    payload = {
        "ticker": "SPY",
        "category": "income_strategy",
        "strategy_tag": "premium_credit",
        "implied_volatility": 0.60,
        "realized_volatility": 0.30,
        "delta": 0.20,
        "gamma": 0.01,
        "vega": 0.10,
        "theta_daily": -0.04,
        "premium_collected": 1.00,
        "premium_paid": 1.00,
        "hold_days": 5,
    }
    payload.update(overrides)
    return payload


def _core_factors(value: float = 0.8) -> dict[str, float]:
    return {name: value for name in ALL_FACTOR_NAMES}


def test_iv_rv_neutral_when_no_data():
    assert IVRVRatioFactor().compute({"strategy_tag": "premium_credit"}) == 0.5


def test_iv_rv_high_ratio_selling_is_good():
    assert IVRVRatioFactor().compute(_context(implied_volatility=0.60, realized_volatility=0.30)) > 0.9


def test_iv_rv_low_ratio_buying_is_good():
    score = IVRVRatioFactor().compute(_context(strategy_tag="long_debit", implied_volatility=0.20, realized_volatility=0.30))
    assert score > 0.8


def test_iv_rv_mismatched_selling_low_iv():
    score = IVRVRatioFactor().compute(_context(strategy_tag="premium_credit", implied_volatility=0.20, realized_volatility=0.30))
    assert score < 0.2


def test_iv_rv_unknown_strategy_scores_moderate():
    score = IVRVRatioFactor().compute(_context(strategy_tag="custom_options", implied_volatility=0.45, realized_volatility=0.30))
    assert 0.6 < score < 0.8


def test_iv_rv_zero_rv_returns_neutral():
    assert IVRVRatioFactor().compute(_context(realized_volatility=0.0)) == 0.5


def test_iv_rv_yfinance_unavailable_returns_neutral():
    assert IVRVRatioFactor().compute({"ticker": "SPY", "strategy_tag": "premium_credit"}) == 0.5


def test_iv_rv_fetch_failure_returns_neutral_or_partial_default(monkeypatch):
    class BrokenYF:
        @staticmethod
        def Ticker(ticker):
            raise RuntimeError("offline")

    monkeypatch.setattr(options, "YFINANCE_AVAILABLE", True)
    monkeypatch.setattr(options, "yf", BrokenYF)

    assert IVRVRatioFactor().compute({"ticker": "SPY", "strategy_tag": "premium_credit"}) == 0.5


def test_greeks_neutral_no_data():
    assert GreeksExposureFactor().compute({}) == 0.5


def test_greeks_directional_high_delta_good():
    assert GreeksExposureFactor().compute(_context(strategy_tag="long_call", delta=0.70)) > 0.9


def test_greeks_directional_low_delta_poor():
    assert GreeksExposureFactor().compute(_context(strategy_tag="long_call", delta=0.05)) < 0.2


def test_greeks_neutral_strategy_low_delta_good():
    assert GreeksExposureFactor().compute(_context(strategy_tag="iron_condor", delta=0.05)) > 0.8


def test_greeks_neutral_strategy_high_delta_poor():
    assert GreeksExposureFactor().compute(_context(strategy_tag="iron_condor", delta=0.60)) < 0.1


def test_theta_neutral_no_data():
    assert ThetaEfficiencyFactor().compute({}) == 0.5


def test_theta_seller_capturing_decay():
    assert ThetaEfficiencyFactor().compute(_context(theta_daily=-0.20, premium_collected=1.0, hold_days=5)) == 1.0


def test_theta_seller_not_capturing():
    assert ThetaEfficiencyFactor().compute(_context(theta_daily=-0.01, premium_collected=1.0, hold_days=5)) < 0.1


def test_theta_buyer_low_cost():
    assert ThetaEfficiencyFactor().compute(_context(strategy_tag="long_debit", theta_daily=-0.01, premium_paid=1.0, hold_days=5)) > 0.9


def test_theta_buyer_high_cost():
    assert ThetaEfficiencyFactor().compute(_context(strategy_tag="long_debit", theta_daily=-0.30, premium_paid=1.0, hold_days=5)) == 0.0


def test_theta_zero_hold_days():
    assert ThetaEfficiencyFactor().compute(_context(hold_days=0)) == 0.5


def test_compute_returns_3_keys():
    assert set(compute_options_factors(_context())) == set(OPTIONS_FACTOR_NAMES)


def test_compute_all_clamped_0_1():
    values = compute_options_factors(_context(implied_volatility=99, realized_volatility=0.01, delta=9, theta_daily=-99))
    assert all(0.0 <= value <= 1.0 for value in values.values())


def test_compute_handles_exception(monkeypatch):
    class Broken:
        def compute(self, context):
            raise RuntimeError("boom")

    monkeypatch.setitem(OPTIONS_FACTOR_COMPUTERS, "iv_rv_ratio", Broken())
    assert compute_options_factors(_context())["iv_rv_ratio"] == 0.5


def test_compute_empty_context_all_neutral():
    assert compute_options_factors({}) == {
        "iv_rv_ratio": 0.5,
        "greeks_exposure": 0.5,
        "theta_efficiency": 0.5,
    }


def test_options_factor_names_length():
    assert len(OPTIONS_FACTOR_NAMES) == 3


def test_options_computers_all_have_compute():
    assert set(OPTIONS_FACTOR_COMPUTERS) == set(OPTIONS_FACTOR_NAMES)
    assert all(hasattr(computer, "compute") for computer in OPTIONS_FACTOR_COMPUTERS.values())


def test_trading_preset_shape_is_5_4_10():
    shape = TradingPreset().shape
    assert (shape.n_categories, shape.n_actions, shape.n_factors) == (5, 4, 10)


def test_core_factor_registry_has_10_scored_keys():
    assert len(ALL_FACTOR_NAMES) == 10
    assert set(OPTIONS_FACTOR_NAMES).isdisjoint(set(ALL_FACTOR_NAMES))


def test_compute_factors_still_returns_only_scored_keys():
    values = compute_factors(_context())
    assert set(values) == set(ALL_FACTOR_NAMES)


def test_prescore_includes_options_for_income(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())

    payload = client.post(
        "/api/trading/prescore",
        json={"ticker": "SPY", "category": "income_strategy", "strategy_tag": "premium_credit", "size_pct": 1.0},
    ).json()

    assert set(payload["options_factors"]) == set(OPTIONS_FACTOR_NAMES)


def test_prescore_options_has_analytics_only_flag(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())

    payload = client.post(
        "/api/trading/prescore",
        json={"ticker": "SPY", "category": "income_strategy", "strategy_tag": "premium_credit", "size_pct": 1.0},
    ).json()

    assert payload["options_analytics_only"] is True


def test_prescore_does_not_mix_options_into_core_factors(client, monkeypatch):
    monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())

    payload = client.post(
        "/api/trading/prescore",
        json={"ticker": "SPY", "category": "income_strategy", "strategy_tag": "premium_credit", "size_pct": 1.0},
    ).json()

    assert set(payload["factors"]) == set(ALL_FACTOR_NAMES)
    assert set(OPTIONS_FACTOR_NAMES).isdisjoint(payload["factors"])


def test_evidence_includes_options_text_for_income():
    text = TradingTemplateEngine().render(
        {"ticker": "SPY", "direction": "short", "category": "income_strategy"},
        _core_factors(),
        "partial_execution",
        0.7,
        {"options_factors": {"iv_rv_ratio": 0.82, "greeks_exposure": 0.9, "theta_efficiency": 0.78}},
    )

    assert "Options analytics-only: IV/RV 0.82, Greeks 0.90, Theta 0.78." in text


def test_evidence_endpoint_returns_options_separately_for_income(client):
    _trade_store_ref.append(
        {
            "trade_id": "opt-1",
            "ticker": "SPY",
            "direction": "short",
            "category": "income_strategy",
            "strategy_tag": "premium_credit",
            "pnl": 10,
            "factors": _core_factors(),
            "metadata": {
                "options_factors": {
                    "iv_rv_ratio": 0.82,
                    "greeks_exposure": 0.90,
                    "theta_efficiency": 0.78,
                }
            },
        }
    )

    payload = client.get("/api/trading/evidence/opt-1").json()

    assert set(payload["factors"]) == set(ALL_FACTOR_NAMES)
    assert payload["options_analytics_only"] is True
    assert payload["options_factors"]["iv_rv_ratio"] == 0.82


def test_journal_detail_exposes_options_factors(client):
    _trade_store_ref.append(
        {
            "trade_id": "opt-2",
            "ticker": "SPY",
            "category": "income_strategy",
            "metadata": {"options_factors": {"iv_rv_ratio": 0.7}},
        }
    )

    payload = client.get("/api/trading/trades/opt-2").json()

    assert payload["options_factors"] == {"iv_rv_ratio": 0.7}
    assert payload["factors"] == {}


def test_cli_score_shows_options_analytics_only(tmp_path: Path, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([{"trade_id": "c-1", **_context()}], config_dir)

    assert cli.main(["--config-dir", str(config_dir), "score", "--trade-id", "c-1"]) == 0
    output = capsys.readouterr().out

    assert "Factor scores" in output
    assert "Options Factors (analytics-only):" in output
    assert "iv_rv_ratio" in output


def test_cli_journal_shows_options_analytics_only(tmp_path: Path, capsys):
    config_dir = tmp_path / "ci-trading"
    assert cli.main(["--config-dir", str(config_dir), "init"]) == 0
    cli._save_trades([{"trade_id": "j-1", "pnl": 10, **_context()}], config_dir)

    assert cli.main(["--config-dir", str(config_dir), "journal"]) == 0
    output = capsys.readouterr().out

    assert "Options Factors (analytics-only):" in output
    assert "theta_efficiency" in output
