"""Cross-position correlation monitoring for Trading."""

from __future__ import annotations

import importlib
import importlib.util
from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Any


try:
    import numpy as np  # type: ignore

    NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore[assignment]
    NUMPY_AVAILABLE = False

YFINANCE_AVAILABLE = importlib.util.find_spec("yfinance") is not None
yf: Any | None = None


ALERT_WARNING = 0.6
ALERT_CRITICAL = 0.8
DEFAULT_WINDOW = 20
MAX_TICKERS = 20


class CorrelationService:
    def __init__(self, window_days: int = DEFAULT_WINDOW, provider: Any | None = None) -> None:
        self.window_days = max(2, int(window_days or DEFAULT_WINDOW))
        self._provider = provider

    def compute(self, trades: list[dict[str, Any]]) -> dict[str, Any]:
        tickers = _extract_tickers(trades)
        if len(tickers) < 2:
            return self._insufficient(tickers, "At least two tickers are required for correlation monitoring.")
        if self._provider is None and (not YFINANCE_AVAILABLE or _yfinance_module() is None):
            return self._insufficient(tickers, "yfinance is unavailable.")
        if not NUMPY_AVAILABLE or np is None:
            return self._insufficient(tickers, "numpy is unavailable.")

        returns = self._fetch_returns(tickers)
        if not returns or len(returns) < 2:
            return self._insufficient(tickers, "Insufficient price history for correlation monitoring.")

        valid_tickers = [ticker for ticker in tickers if ticker in returns]
        if len(valid_tickers) < 2:
            return self._insufficient(valid_tickers, "Fewer than two tickers have valid return history.")

        matrix = self._compute_matrix(valid_tickers, returns)
        pairs = _pairs(valid_tickers, matrix)
        avg_correlation = round(sum(pair["correlation"] for pair in pairs) / len(pairs), 4) if pairs else 0.0
        max_pair = pairs[0] if pairs else None
        alerts = _alerts(avg_correlation, pairs)
        return {
            "tickers": valid_tickers,
            "matrix": matrix,
            "pairs": pairs,
            "avg_correlation": avg_correlation,
            "max_pair": max_pair,
            "alerts": alerts,
            "window_days": self.window_days,
            "source": "yfinance",
        }

    def _fetch_returns(self, tickers: list[str]) -> dict[str, list[float]] | None:
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=self.window_days * 2)
        if self._provider is not None:
            result = self._provider.get_batch_returns(tickers, start.isoformat(), end.isoformat())
            history = result.value if result is not None else None
            return self._returns_from_history(tickers, history if isinstance(history, dict) else None)

        yf_module = _yfinance_module()
        if not YFINANCE_AVAILABLE or yf_module is None:
            return None
        try:
            data = yf_module.download(
                tickers,
                start=start.isoformat(),
                end=end.isoformat(),
                progress=False,
                auto_adjust=True,
            )
            if data is None or getattr(data, "empty", False):
                return None
            close = data["Close"] if "Close" in data else data
            output: dict[str, list[float]] = {}
            if len(tickers) == 1:
                series = close.dropna()
                values = _pct_change(list(series))
                if len(values) >= self.window_days - 2:
                    output[tickers[0]] = values[-self.window_days :]
                return output
            for ticker in tickers:
                if ticker not in close:
                    continue
                series = close[ticker].dropna()
                values = _pct_change(list(series))
                if len(values) >= self.window_days - 2:
                    output[ticker] = values[-self.window_days :]
            return output
        except Exception:
            return None

    def _returns_from_history(
        self,
        tickers: list[str],
        history: dict[str, list[dict]] | None,
    ) -> dict[str, list[float]] | None:
        if not history:
            return None
        output: dict[str, list[float]] = {}
        for ticker in tickers:
            rows = history.get(ticker)
            if not rows:
                continue
            values = _pct_change([row.get("close") for row in rows])
            if len(values) >= self.window_days - 2:
                output[ticker] = values[-self.window_days :]
        return output

    def _compute_matrix(
        self,
        tickers: list[str],
        returns: dict[str, list[float]],
    ) -> list[list[float]]:
        if np is None:
            return []
        min_len = min(len(returns[ticker]) for ticker in tickers)
        aligned = [returns[ticker][-min_len:] for ticker in tickers]
        raw = np.corrcoef(aligned)
        matrix: list[list[float]] = []
        for row_index, row in enumerate(raw):
            values: list[float] = []
            for col_index, value in enumerate(row):
                number = float(value)
                if isnan(number):
                    number = 1.0 if row_index == col_index else 0.0
                values.append(round(number, 4))
            matrix.append(values)
        return matrix

    def _insufficient(self, tickers: list[str], reason: str) -> dict[str, Any]:
        return {
            "tickers": tickers,
            "matrix": [],
            "pairs": [],
            "avg_correlation": 0.0,
            "max_pair": None,
            "alerts": [],
            "window_days": self.window_days,
            "source": "insufficient_data",
            "reason": reason,
        }


def _extract_tickers(trades: list[dict[str, Any]]) -> list[str]:
    tickers: list[str] = []
    seen: set[str] = set()
    for trade in trades:
        ticker = str(trade.get("ticker") or "").strip().upper()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        tickers.append(ticker)
        if len(tickers) >= MAX_TICKERS:
            break
    return tickers


def _pairs(tickers: list[str], matrix: list[list[float]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for row_index, ticker_a in enumerate(tickers):
        for col_index in range(row_index + 1, len(tickers)):
            ticker_b = tickers[col_index]
            pairs.append({
                "ticker_a": ticker_a,
                "ticker_b": ticker_b,
                "correlation": matrix[row_index][col_index],
            })
    return sorted(pairs, key=lambda item: abs(float(item["correlation"])), reverse=True)


def _alerts(avg_correlation: float, pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if avg_correlation > ALERT_CRITICAL:
        alerts.append({
            "level": "critical",
            "message": "Average position correlation is above the critical concentration threshold.",
            "value": avg_correlation,
        })
    elif avg_correlation > ALERT_WARNING:
        alerts.append({
            "level": "warning",
            "message": "Average position correlation is above the warning concentration threshold.",
            "value": avg_correlation,
        })
    for pair in pairs:
        value = float(pair["correlation"])
        if abs(value) > ALERT_CRITICAL:
            alerts.append({
                "level": "critical",
                "message": f"{pair['ticker_a']} and {pair['ticker_b']} have high absolute correlation concentration.",
                "ticker_a": pair["ticker_a"],
                "ticker_b": pair["ticker_b"],
                "value": round(value, 4),
            })
    return alerts


def _pct_change(values: list[Any]) -> list[float]:
    output: list[float] = []
    previous: float | None = None
    for value in values:
        try:
            current = float(value)
        except (TypeError, ValueError):
            previous = None
            continue
        if previous not in {None, 0.0}:
            output.append((current - previous) / previous)
        previous = current
    return output


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
