"""Market regime classification service."""

from __future__ import annotations

import importlib
import importlib.util
from datetime import datetime, timedelta, timezone
from typing import Any


YFINANCE_AVAILABLE = importlib.util.find_spec("yfinance") is not None
yf: Any | None = None


DEFAULT_VIX_VOLATILE = 30.0
DEFAULT_VIX_RANGING = 20.0
DEFAULT_ADX_TRENDING = 25.0
DEFAULT_VIX = DEFAULT_VIX_RANGING
DEFAULT_ADX = 20.0


def classify_regime(vix: float, trend_strength: float) -> str:
    if float(vix) > DEFAULT_VIX_VOLATILE:
        return "volatile"
    if float(vix) > DEFAULT_VIX_RANGING:
        return "ranging"
    if float(trend_strength) > DEFAULT_ADX_TRENDING:
        return "trending"
    return "ranging"


def compute_adx(highs: Any, lows: Any, closes: Any, period: int = 14) -> float:
    try:
        if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
            return DEFAULT_ADX
        import pandas as pd  # type: ignore
        import pandas_ta as ta  # type: ignore

        frame = pd.DataFrame({"high": list(highs), "low": list(lows), "close": list(closes)})
        adx = ta.adx(frame["high"], frame["low"], frame["close"], length=period)
        if adx is None or adx.empty:
            return DEFAULT_ADX
        column = f"ADX_{period}"
        value = adx[column].dropna().iloc[-1] if column in adx else adx.dropna().iloc[-1, 0]
        return float(value)
    except Exception:
        return DEFAULT_ADX


class RegimeService:
    def __init__(self, cache_minutes: int = 15, provider: Any | None = None):
        self.cache_minutes = int(cache_minutes)
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}
        self._provider = provider

    def get_current_regime(self, ticker: str = "SPY") -> dict[str, Any]:
        cache_key = ticker.upper()
        now = datetime.now(timezone.utc)
        cached = self._cache.get(cache_key)
        if cached is not None:
            cached_at, payload = cached
            if now - cached_at < timedelta(minutes=self.cache_minutes):
                return {**payload, "source": "cached"}

        if self._provider is not None:
            payload = self._current_regime_from_provider(cache_key, now)
            self._cache[cache_key] = (now, payload)
            return dict(payload)

        yf_module = _yfinance_module()
        if not YFINANCE_AVAILABLE or yf_module is None:
            payload = self._default()
            self._cache[cache_key] = (now, payload)
            return dict(payload)

        try:
            vix_history = yf_module.Ticker("^VIX").history(period="5d")
            ticker_history = yf_module.Ticker(cache_key).history(period="30d")
            if vix_history is None or ticker_history is None or vix_history.empty or ticker_history.empty:
                payload = self._default()
                self._cache[cache_key] = (now, payload)
                return dict(payload)

            vix = float(vix_history["Close"].dropna().iloc[-1])
            highs = list(ticker_history["High"].dropna())
            lows = list(ticker_history["Low"].dropna())
            closes = list(ticker_history["Close"].dropna())
            adx = compute_adx(highs, lows, closes)
            spy_price = float(closes[-1]) if closes else 0.0
            payload = {
                "regime": classify_regime(vix, adx),
                "vix": round(vix, 4),
                "adx": round(float(adx), 4),
                "spy_price": round(spy_price, 4),
                "source": "yfinance",
                "as_of": now.isoformat(),
            }
            self._cache[cache_key] = (now, payload)
            return dict(payload)
        except Exception:
            payload = self._default()
            self._cache[cache_key] = (now, payload)
            return dict(payload)

    def get_regime_accuracy(self, trades: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
        if not trades:
            return {}
        vix_by_date = self._batch_vix_lookup(trades)
        buckets: dict[str, dict[str, list[bool]]] = {}
        for trade in trades:
            category = str(trade.get("category") or "").strip()
            if not category:
                continue
            regime = self._trade_regime(trade, vix_by_date)
            if not regime:
                continue
            buckets.setdefault(category, {}).setdefault(regime, []).append(_is_win(trade))

        return {
            category: {
                regime: round(sum(1 for value in outcomes if value) / len(outcomes), 4)
                for regime, outcomes in sorted(regimes.items())
                if outcomes
            }
            for category, regimes in sorted(buckets.items())
        }

    def get_historical_vix(self, trades: list[dict[str, Any]]) -> dict[str, float]:
        return self._batch_vix_lookup(trades)

    def _batch_vix_lookup(self, trades: list[dict[str, Any]]) -> dict[str, float]:
        dates = sorted({_trade_date(trade) for trade in trades if _trade_date(trade)})
        if not dates:
            return {}
        start = datetime.fromisoformat(dates[0]).date() - timedelta(days=7)
        end = datetime.fromisoformat(dates[-1]).date() + timedelta(days=1)
        if self._provider is not None:
            result = self._provider.get_vix_history(start.isoformat(), end.isoformat())
            values = result.value if result is not None else None
            return _fill_trade_dates(dates, values if isinstance(values, dict) else {})

        yf_module = _yfinance_module()
        if not YFINANCE_AVAILABLE or yf_module is None:
            return {}
        try:
            history = yf_module.Ticker("^VIX").history(start=start.isoformat(), end=end.isoformat())
            if history is None or history.empty:
                return {}
            closes: dict[str, float] = {}
            for index, row in history.iterrows():
                key = index.date().isoformat() if hasattr(index, "date") else str(index)[:10]
                closes[key] = float(row["Close"])
            return _fill_trade_dates(dates, closes)
        except Exception:
            return {}

    def _default(self) -> dict[str, Any]:
        return {
            "regime": "ranging",
            "vix": DEFAULT_VIX,
            "adx": DEFAULT_ADX,
            "spy_price": 0.0,
            "source": "default",
        }

    def _trade_regime(self, trade: dict[str, Any], vix_by_date: dict[str, float]) -> str | None:
        metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
        regime = trade.get("regime") or metadata.get("regime")
        if regime:
            return str(regime)
        date_key = _trade_date(trade)
        if not date_key or date_key not in vix_by_date:
            return None
        return classify_regime(vix_by_date[date_key], DEFAULT_ADX)

    def _current_regime_from_provider(self, cache_key: str, now: datetime) -> dict[str, Any]:
        try:
            vix_result = self._provider.get_vix_current()
            ohlcv_result = self._provider.get_ohlcv(cache_key, "1mo")
            vix = vix_result.value if vix_result is not None else None
            rows = ohlcv_result.value if ohlcv_result is not None else None
            if vix is None or not rows:
                return self._default()
            highs = [row["high"] for row in rows if "high" in row]
            lows = [row["low"] for row in rows if "low" in row]
            closes = [row["close"] for row in rows if "close" in row]
            adx = compute_adx(highs, lows, closes)
            spy_price = float(closes[-1]) if closes else 0.0
            return {
                "regime": classify_regime(float(vix), adx),
                "vix": round(float(vix), 4),
                "adx": round(float(adx), 4),
                "spy_price": round(spy_price, 4),
                "source": str(getattr(vix_result, "source", "provider")),
                "as_of": getattr(vix_result, "as_of", None) or now.isoformat(),
            }
        except Exception:
            return self._default()


def _trade_date(trade: dict[str, Any]) -> str | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = trade.get("entry_time") or trade.get("date") or metadata.get("entry_time") or metadata.get("date")
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else None


def _is_win(trade: dict[str, Any]) -> bool:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = trade.get("pnl")
    if value is None:
        value = trade.get("pnl_dollars")
    if value is None:
        value = metadata.get("pnl")
    if value is None:
        value = metadata.get("pnl_dollars")
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _yfinance_module() -> Any | None:
    global yf
    if yf is not None:
        return yf
    if not YFINANCE_AVAILABLE:
        return None
    try:
        yf = importlib.import_module("yfinance")
        return yf
    except ImportError:
        return None


def _fill_trade_dates(dates: list[str], closes: dict[str, float]) -> dict[str, float]:
    output: dict[str, float] = {}
    last_value: float | None = None
    for date in sorted({*closes.keys(), *dates}):
        if date in closes:
            last_value = float(closes[date])
        if date in dates and last_value is not None:
            output[date] = last_value
    return output
