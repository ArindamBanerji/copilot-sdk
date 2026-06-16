"""Market data source implementations for Trading."""

from __future__ import annotations

from typing import Any, Protocol


class MarketSource(Protocol):
    """Swappable upstream feed. yfinance now; Alpaca/Polygon later.

    Returns None on ANY failure (rate-limit, down, missing).
    The provider above owns the cascade and provenance tagging.
    """

    def fetch_ohlcv(self, ticker: str, period: str = "1mo") -> list[dict] | None: ...
    def fetch_vix(self) -> float | None: ...
    def fetch_info(self, ticker: str) -> dict | None: ...
    def fetch_batch_history(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> dict[str, list[dict]] | None: ...


class YFinanceSource:
    """yfinance implementation. Dev/demo source.

    All methods return None on any exception (rate limit, network, etc).
    yfinance is imported inside each method to preserve the optional
    dependency pattern.
    """

    def fetch_ohlcv(self, ticker: str, period: str = "1mo") -> list[dict] | None:
        try:
            import yfinance as yf

            df = yf.Ticker(ticker).history(period=period)
            if df.empty:
                return None
            records = []
            for idx, row in df.iterrows():
                records.append(
                    {
                        "date": idx.strftime("%Y-%m-%d"),
                        "open": round(float(row["Open"]), 2),
                        "high": round(float(row["High"]), 2),
                        "low": round(float(row["Low"]), 2),
                        "close": round(float(row["Close"]), 2),
                        "volume": int(row["Volume"]),
                    }
                )
            return records
        except Exception:
            return None

    def fetch_vix(self) -> float | None:
        try:
            import yfinance as yf

            df = yf.Ticker("^VIX").history(period="5d")
            if df.empty:
                return None
            return round(float(df["Close"].iloc[-1]), 2)
        except Exception:
            return None

    def fetch_info(self, ticker: str) -> dict | None:
        try:
            import yfinance as yf

            info = yf.Ticker(ticker).info
            return info if info else None
        except Exception:
            return None

    def fetch_batch_history(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> dict[str, list[dict]] | None:
        try:
            import yfinance as yf

            result = {}
            for ticker in tickers:
                df = yf.Ticker(ticker).history(start=start, end=end)
                if not df.empty:
                    result[ticker] = [
                        {
                            "date": idx.strftime("%Y-%m-%d"),
                            "close": round(float(row["Close"]), 2),
                        }
                        for idx, row in df.iterrows()
                    ]
            return result if result else None
        except Exception:
            return None


class MockMarketSource:
    """Test double. Deterministic fixture data. No network calls.

    Returns realistic data for SPY, QQQ, and ^VIX.
    """

    def __init__(self, fixture_data: dict[str, Any] | None = None):
        self._data = fixture_data or self._defaults()

    def fetch_ohlcv(self, ticker: str, period: str = "1mo") -> list[dict] | None:
        return self._data.get("ohlcv", {}).get(ticker)

    def fetch_vix(self) -> float | None:
        return self._data.get("vix_current", 18.5)

    def fetch_info(self, ticker: str) -> dict | None:
        return self._data.get("info", {}).get(ticker)

    def fetch_batch_history(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> dict[str, list[dict]] | None:
        result = {}
        for ticker in tickers:
            data = self._data.get("ohlcv", {}).get(ticker)
            if data:
                result[ticker] = data
        return result if result else None

    @staticmethod
    def _defaults() -> dict[str, Any]:
        """Generate 30 days of realistic SPY/QQQ/VIX data."""
        import math

        base_spy, base_qqq = 540.0, 480.0
        days = 30
        ohlcv: dict[str, list[dict[str, Any]]] = {"SPY": [], "QQQ": [], "^VIX": []}
        for i in range(days):
            date = f"2026-06-{(i % 28) + 1:02d}"
            spy_close = base_spy + i * 0.5 + math.sin(i) * 3
            qqq_close = base_qqq + i * 0.6 + math.sin(i + 1) * 4
            vix_close = 18.0 + math.sin(i * 0.5) * 4
            for ticker, close in [
                ("SPY", spy_close),
                ("QQQ", qqq_close),
                ("^VIX", vix_close),
            ]:
                ohlcv[ticker].append(
                    {
                        "date": date,
                        "open": round(close - 1.5, 2),
                        "high": round(close + 2.0, 2),
                        "low": round(close - 2.5, 2),
                        "close": round(close, 2),
                        "volume": 50_000_000 + i * 100_000,
                    }
                )
        return {
            "ohlcv": ohlcv,
            "vix_current": 18.5,
            "info": {
                "SPY": {
                    "shortName": "SPDR S&P 500 ETF",
                    "sector": "Financial Services",
                    "marketCap": 550_000_000_000,
                    "previousClose": 555.0,
                    "fiftyDayAverage": 548.0,
                    "twoHundredDayAverage": 530.0,
                    "averageVolume": 75_000_000,
                },
                "QQQ": {
                    "shortName": "Invesco QQQ Trust",
                    "sector": "Technology",
                    "marketCap": 250_000_000_000,
                    "previousClose": 495.0,
                    "fiftyDayAverage": 488.0,
                    "twoHundredDayAverage": 470.0,
                    "averageVolume": 50_000_000,
                },
            },
        }
