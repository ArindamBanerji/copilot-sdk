import json
from pathlib import Path

import pandas as pd

from ci_trading.quant import CorrelationMonitor, classify_regime, yang_zhang_vol


FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_rows(name: str) -> list[dict]:
    data = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [row for row in data if "_comment" not in row]


def test_spy_yang_zhang_vol_real_fixture_plausible() -> None:
    rows = _fixture_rows("spy_ohlcv_2024q1.json")
    ohlc = pd.DataFrame(rows)

    vol = yang_zhang_vol(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"])

    assert 0.08 <= vol <= 0.35


def test_vix_regime_shift_real_fixture_plausible() -> None:
    rows = _fixture_rows("vix_2020q1.json")
    vix = pd.Series({row["date"]: row["close"] for row in rows}, dtype=float)

    calm = classify_regime(
        float(vix.loc["2020-01-10"]),
        trend_strength=20.0,
        vix_history=vix.loc[:"2020-01-10"],
    )["regime"]
    spike = classify_regime(
        float(vix.loc["2020-03-16"]),
        trend_strength=20.0,
        vix_history=vix.loc[:"2020-03-16"],
    )["regime"]
    recovery = classify_regime(
        float(vix.loc["2020-06-08"]),
        trend_strength=20.0,
        vix_history=vix.loc[:"2020-06-08"],
    )["regime"]

    assert calm in {"ranging", "trending"}
    assert spike == "volatile"
    assert recovery in {"ranging", "trending"}


def test_sector_correlation_real_fixture_detects_concentration() -> None:
    rows = _fixture_rows("sector_returns_60d.json")
    returns = pd.DataFrame(rows).set_index("date")
    tech_names = ["AAPL", "MSFT", "NVDA", "AMZN"]
    uncorrelated_name = "GLD"
    position_returns = returns[[*tech_names, uncorrelated_name]].astype(float)
    market_returns = position_returns.mean(axis=1)
    corr = position_returns.corr()

    for i, left in enumerate(tech_names):
        for right in tech_names[i + 1:]:
            assert corr.loc[left, right] > 0.5
        assert abs(corr.loc[left, uncorrelated_name]) < 0.3

    alert = CorrelationMonitor(alert_multiplier=1.5).check_correlation(
        position_returns,
        weights=[1, 1, 1, 1, 3],
        market_returns=market_returns,
    )

    assert alert is not None
    assert alert.effective_multiplier > 1.5
    assert alert.n_effective_bets < 3
    assert alert.n_effective_bets > 1.5
