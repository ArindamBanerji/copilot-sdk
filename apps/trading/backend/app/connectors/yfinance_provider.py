"""Optional yfinance market-data provider."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class YFinanceProvider:
    def get_ohlcv(self, ticker: str, period: str = "1mo", interval: str = "1d") -> list[dict[str, Any]]:
        try:
            import yfinance as yf

            frame = yf.Ticker(ticker).history(period=period, interval=interval)
        except Exception:
            return []
        rows: list[dict[str, Any]] = []
        for index, row in frame.iterrows():
            rows.append(
                {
                    "date": index.isoformat() if hasattr(index, "isoformat") else str(index),
                    "open": float(row.get("Open", 0.0)),
                    "high": float(row.get("High", 0.0)),
                    "low": float(row.get("Low", 0.0)),
                    "close": float(row.get("Close", 0.0)),
                    "volume": float(row.get("Volume", 0.0)),
                }
            )
        return rows

    def get_vix(self, period: str = "1mo", interval: str = "1d") -> list[dict[str, Any]]:
        return self.get_ohlcv("^VIX", period=period, interval=interval)

    def get_current_vix(self) -> float | None:
        rows = self.get_vix(period="5d", interval="1d")
        if not rows:
            return None
        return float(rows[-1]["close"])

    @staticmethod
    def mock_ohlcv(ticker: str = "SPY", days: int = 5) -> list[dict[str, Any]]:
        start = datetime(2026, 1, 1)
        rows: list[dict[str, Any]] = []
        for offset in range(days):
            close = 100.0 + offset
            rows.append(
                {
                    "ticker": ticker.upper(),
                    "date": (start + timedelta(days=offset)).date().isoformat(),
                    "open": close - 0.5,
                    "high": close + 1.0,
                    "low": close - 1.0,
                    "close": close,
                    "volume": 1_000_000 + offset,
                }
            )
        return rows
