"""Market data computation helpers. Validated against known values."""


def _manual_wilder_rsi(closes: list[float], period: int) -> float:
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute_rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder 14-period RSI.

    Uses pandas_ta if available, falls back to manual implementation.
    Returns None if insufficient data (< period + 1 closes).
    """
    if len(closes) < period + 1:
        return None
    try:
        import pandas as pd
        import pandas_ta as ta

        series = pd.Series(closes)
        rsi = ta.rsi(series, length=period)
        value = rsi.iloc[-1]
        if pd.notna(value):
            return round(float(value), 2)
    except ImportError:
        pass
    return _manual_wilder_rsi(closes, period)


def compute_vol_rank(volumes: list[float], window: int = 252) -> int | None:
    """Volume percentile rank over trailing window.

    Returns percentile (0-100) of latest volume vs trailing window.
    Returns None if insufficient data.
    """
    if len(volumes) < 2:
        return None
    lookback = volumes[-window:] if len(volumes) >= window else volumes
    latest = volumes[-1]
    below = sum(1 for volume in lookback if volume < latest)
    return round(100 * below / len(lookback))
