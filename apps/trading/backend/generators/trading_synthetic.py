"""Deterministic synthetic trade generator for Trading backend fixtures."""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.verification import (  # noqa: E402
    compute_execution_quality,
    compute_r_multiple,
    compute_verification_score,
)


DEFAULT_OUTPUT_PATH = BACKEND_ROOT / "data" / "synthetic_trades_2000.json"
FALLBACK_CATEGORIES = (
    "trend_following",
    "mean_reversion",
    "event_driven",
    "income_strategy",
    "scalp_intraday",
)
FALLBACK_ACTIONS = (
    "strong_execution",
    "partial_execution",
    "poor_execution",
    "skip_recommended",
)
FALLBACK_FACTORS = (
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
)
PATTERNS = (
    "clean_breakout",
    "late_chase",
    "failed_reversal",
    "volatility_squeeze",
    "news_gap",
    "range_scalp",
)
TICKERS = (
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "META",
    "SPY",
    "QQQ",
    "IWM",
    "COIN",
    "TLT",
)


def generate_trades(n: int = 2000, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    categories, actions, factors = _preset_terms()
    start = datetime(2024, 1, 2, 9, 30)
    trades: list[dict[str, Any]] = []

    for index in range(n):
        category = categories[index % len(categories)]
        action = actions[index % len(actions)]
        pattern = PATTERNS[index % len(PATTERNS)]
        side = "short" if (index + categories.index(category)) % 5 == 0 else "long"
        entry_price = round(rng.uniform(25.0, 650.0), 2)
        risk_pct = rng.uniform(0.006, 0.035)
        expected_r = _expected_r_for_action(action, rng)
        stop_loss = _stop_loss(entry_price, risk_pct, side)
        expected_exit = _exit_for_r(entry_price, stop_loss, expected_r, side)
        actual_entry = _slip(entry_price, rng, max_pct=0.012)
        actual_exit = _slip(expected_exit, rng, max_pct=0.018)
        fill_rate = round(rng.uniform(0.65, 1.0), 4)
        r_multiple = compute_r_multiple(actual_entry, actual_exit, stop_loss, side)
        execution_quality = compute_execution_quality(
            entry_price,
            actual_entry,
            expected_exit,
            actual_exit,
            fill_rate,
        )
        outcome_correct = r_multiple > 0.0 and action in {
            "strong_execution",
            "partial_execution",
        }
        verification = compute_verification_score(
            r_multiple,
            execution_quality,
            outcome_correct,
        )
        entry_time = start + timedelta(hours=6 * index)
        hold_hours = _hold_hours(category, rng)
        exit_time = entry_time + timedelta(hours=hold_hours)
        factor_values = _factor_values(factors, category, action, pattern, rng)

        trades.append(
            {
                "trade_id": f"SYN-TRD-{index + 1:04d}",
                "ticker": TICKERS[index % len(TICKERS)],
                "category": category,
                "pattern": pattern,
                "side": side,
                "direction": action,
                "entry_price": entry_price,
                "exit_price": round(expected_exit, 2),
                "stop_loss": stop_loss,
                "actual_entry_price": actual_entry,
                "actual_exit_price": actual_exit,
                "quantity": rng.randint(1, 250),
                "fill_rate": fill_rate,
                "entry_time": entry_time.isoformat(),
                "exit_time": exit_time.isoformat(),
                "hold_hours": hold_hours,
                "r_multiple": r_multiple,
                "execution_quality": execution_quality,
                "verification_score": verification.verification_score,
                "action": action,
                "action_taken": action,
                "is_correct": outcome_correct,
                "provenance": "sample",
                "factors": factor_values,
                "metadata": {
                    "generator": "trading_synthetic",
                    "seed": seed,
                    "index": index,
                    "verification_components": verification.components,
                },
            }
        )
    return trades


def main() -> None:
    trades = generate_trades()
    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_PATH.write_text(
        json.dumps(trades, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(trades)} synthetic trades to "
        f"{DEFAULT_OUTPUT_PATH.as_posix()}"
    )


def _preset_terms() -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    try:
        from copilot_sdk.scoring.presets.trading import TradingPreset

        shape = TradingPreset().shape
        return (
            tuple(shape.category_names),
            tuple(shape.action_names),
            tuple(shape.factor_names),
        )
    except Exception:
        return FALLBACK_CATEGORIES, FALLBACK_ACTIONS, FALLBACK_FACTORS


def _expected_r_for_action(action: str, rng: random.Random) -> float:
    if action == "strong_execution":
        return rng.uniform(1.2, 3.0)
    if action == "partial_execution":
        return rng.uniform(0.1, 1.4)
    if action == "poor_execution":
        return rng.uniform(-1.8, 0.2)
    return rng.uniform(-0.4, 0.4)


def _stop_loss(entry: float, risk_pct: float, side: str) -> float:
    if side == "short":
        return round(entry * (1.0 + risk_pct), 2)
    return round(entry * (1.0 - risk_pct), 2)


def _exit_for_r(entry: float, stop: float, r_multiple: float, side: str) -> float:
    risk = abs(entry - stop)
    if side == "short":
        return round(entry - r_multiple * risk, 2)
    return round(entry + r_multiple * risk, 2)


def _slip(price: float, rng: random.Random, max_pct: float) -> float:
    return round(price * (1.0 + rng.uniform(-max_pct, max_pct)), 2)


def _hold_hours(category: str, rng: random.Random) -> int:
    if category == "scalp_intraday":
        return rng.randint(1, 6)
    if category == "income_strategy":
        return rng.randint(72, 720)
    return rng.randint(8, 240)


def _factor_values(
    factors: tuple[str, ...],
    category: str,
    action: str,
    pattern: str,
    rng: random.Random,
) -> dict[str, float]:
    action_base = {
        "strong_execution": 0.78,
        "partial_execution": 0.58,
        "poor_execution": 0.34,
        "skip_recommended": 0.46,
    }.get(action, 0.5)
    category_bias = (FALLBACK_CATEGORIES.index(category) + 1) * 0.015 if category in FALLBACK_CATEGORIES else 0.0
    pattern_bias = (PATTERNS.index(pattern) - 2) * 0.025
    values: dict[str, float] = {}
    for factor_index, factor in enumerate(factors):
        noise = rng.uniform(-0.16, 0.16)
        factor_bias = (factor_index - 3) * 0.015
        values[factor] = round(_clamp(action_base + category_bias + pattern_bias + factor_bias + noise), 4)
    return values


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


if __name__ == "__main__":
    main()
