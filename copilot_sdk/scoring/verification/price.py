"""Cached price verification for trading decisions."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    ticker: str
    entry_price: float
    current_price: float
    direction: str
    is_correct: bool
    source: str
    days_elapsed: int
    price_source_available: bool = True


_SEED_CACHE: dict[str, tuple[float, int]] = {
    "NVDA": (168.0, 30),
    "AAPL": (188.0, 30),
    "MSFT": (411.0, 30),
    "TSLA": (182.0, 30),
    "META": (521.0, 30),
    "BTC": (69000.0, 14),
    "ETH": (3300.0, 14),
    "COIN": (248.0, 21),
    "QQQ": (443.0, 30),
    "SPY": (515.0, 30),
    "IWM": (199.0, 30),
    "TLT": (91.0, 30),
}


def verify_trade(
    ticker: str,
    entry_price: float,
    direction: str,
    use_live: bool = False,
) -> VerificationResult:
    normalized = ticker.upper()
    entry = float(entry_price)
    if use_live:
        current, live_available = _fetch_live_price(normalized)
        source = "live" if live_available else ("cached_seed" if current > 0.0 else "unknown_ticker")
        days_elapsed = 0
    elif normalized in _SEED_CACHE:
        current, days_elapsed = _SEED_CACHE[normalized]
        source = "cached_seed"
    else:
        return VerificationResult(
            ticker=normalized,
            entry_price=entry,
            current_price=entry,
            direction=direction,
            is_correct=False,
            source="unknown_ticker",
            days_elapsed=0,
            price_source_available=False,
        )

    return VerificationResult(
        ticker=normalized,
        entry_price=entry,
        current_price=float(current),
        direction=direction,
        is_correct=_is_correct(entry, float(current), direction),
        source=source,
        days_elapsed=days_elapsed,
        price_source_available=live_available if use_live else True,
    )


def _is_correct(entry: float, current: float, direction: str) -> bool:
    if direction == "buy":
        return current > entry
    if direction == "sell":
        return current < entry
    if direction == "hold":
        return abs(current - entry) / entry < 0.05
    return False


def _fetch_live_price(ticker: str) -> tuple[float, bool]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1d"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = payload["chart"]["result"][0]
        return float(result["meta"]["regularMarketPrice"]), True
    except (OSError, TimeoutError, ConnectionError):
        cached = _SEED_CACHE.get(ticker)
        return (float(cached[0]), False) if cached else (0.0, False)
