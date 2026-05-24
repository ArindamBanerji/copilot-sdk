"""Market regime classification service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


try:
    import yfinance as yf  # type: ignore

    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None  # type: ignore[assignment]
    YFINANCE_AVAILABLE = False


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
    def __init__(self, cache_minutes: int = 15):
        self.cache_minutes = int(cache_minutes)
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    def get_current_regime(self, ticker: str = "SPY") -> dict[str, Any]:
        cache_key = ticker.upper()
        now = datetime.now(timezone.utc)
        cached = self._cache.get(cache_key)
        if cached is not None:
            cached_at, payload = cached
            if now - cached_at < timedelta(minutes=self.cache_minutes):
                return {**payload, "source": "cached"}

        if not YFINANCE_AVAILABLE or yf is None:
            payload = self._default()
            self._cache[cache_key] = (now, payload)
            return dict(payload)

        try:
            vix_history = yf.Ticker("^VIX").history(period="5d")
            ticker_history = yf.Ticker(cache_key).history(period="30d")
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

    def _batch_vix_lookup(self, trades: list[dict[str, Any]]) -> dict[str, float]:
        dates = sorted({_trade_date(trade) for trade in trades if _trade_date(trade)})
        if not dates or not YFINANCE_AVAILABLE or yf is None:
            return {}
        try:
            start = datetime.fromisoformat(dates[0]).date() - timedelta(days=7)
            end = datetime.fromisoformat(dates[-1]).date() + timedelta(days=1)
            history = yf.Ticker("^VIX").history(start=start.isoformat(), end=end.isoformat())
            if history is None or history.empty:
                return {}
            closes: dict[str, float] = {}
            for index, row in history.iterrows():
                key = index.date().isoformat() if hasattr(index, "date") else str(index)[:10]
                closes[key] = float(row["Close"])
            output: dict[str, float] = {}
            last_value: float | None = None
            for date in sorted({*closes.keys(), *dates}):
                if date in closes:
                    last_value = closes[date]
                if date in dates and last_value is not None:
                    output[date] = last_value
            return output
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
