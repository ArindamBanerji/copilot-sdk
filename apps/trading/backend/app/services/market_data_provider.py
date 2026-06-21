"""Market data provider with cache-first provenance tagging."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from apps.trading.backend.app.services.market_computations import compute_rsi, compute_vol_rank
from copilot_sdk.evidence.provenance import Provenanced

LIVE_TIMEOUT_SECONDS = 3
MAX_BACKOFF_SECONDS = 300


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


@dataclass
class CacheEntry:
    data: object
    as_of: str
    expires_at: datetime


class MarketDataProvider:
    """Cache-first cascade with mandatory provenance tagging.

    Cascade: cached -> live (3s timeout) -> stale cached -> fixture.
    Every public method returns Provenanced[T].
    No path can emit an untagged value.
    """

    def __init__(self, source: Any, fixture_data: dict[str, Any] | None = None):
        self._source = source
        self._cache: dict[str, CacheEntry] = {}
        self._backoff: dict[str, datetime] = {}
        self._backoff_delay: dict[str, int] = {}
        self._fixtures = fixture_data or {}

    def get_vix_current(self) -> Provenanced[float | None]:
        """Current VIX level."""
        return self._resolve("vix_current", lambda: self._source.fetch_vix())

    def get_ohlcv(self, ticker: str, period: str = "1mo") -> Provenanced[list[dict] | None]:
        """OHLCV bars for a ticker."""
        key = f"ohlcv:{ticker}:{period}"
        return self._resolve(key, lambda: self._source.fetch_ohlcv(ticker, period))

    def get_vix_history(self, start: str, end: str) -> Provenanced[dict[str, float] | None]:
        """Historical VIX as {date: close} dict. Used by vix_timing router."""
        key = f"vix_hist:{start}:{end}"

        def fetch() -> dict[str, float] | None:
            data = self._source.fetch_batch_history(["^VIX"], start, end)
            if data and "^VIX" in data:
                return {row["date"]: row["close"] for row in data["^VIX"]}
            return None

        return self._resolve(key, fetch)

    def get_batch_returns(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> Provenanced[dict[str, list[dict]] | None]:
        """Batch history for correlation computation."""
        key = f"batch:{','.join(sorted(tickers))}:{start}:{end}"
        return self._resolve(
            key,
            lambda: self._source.fetch_batch_history(tickers, start, end),
        )

    def get_market_snapshot(self) -> Provenanced[dict[str, Any] | None]:
        """Full market snapshot for dashboard context."""
        key = "market_snapshot"

        def fetch() -> dict[str, Any] | None:
            spy_ohlcv = self._source.fetch_ohlcv("SPY", "3mo")
            spy_info = self._source.fetch_info("SPY")
            vix = self._source.fetch_vix()
            return self._build_market_snapshot(spy_ohlcv, spy_info, vix)

        return self._resolve(key, fetch)

    def get_ticker_snapshot(self, ticker: str) -> Provenanced[dict[str, Any] | None]:
        """Enriched snapshot for a single ticker."""
        key = f"ticker:{ticker}"

        def fetch() -> dict[str, Any] | None:
            ohlcv = self._source.fetch_ohlcv(ticker, "3mo")
            info = self._source.fetch_info(ticker)
            return self._build_ticker_snapshot(ticker, ohlcv, info)

        return self._resolve(key, fetch)

    def refresh(self, key: str | None = None) -> Provenanced[bool]:
        """Force-expire cache for key (or all keys)."""
        if key:
            self._cache.pop(key, None)
            self._backoff.pop(key, None)
            self._backoff_delay.pop(key, None)
        else:
            self._cache.clear()
            self._backoff.clear()
            self._backoff_delay.clear()
        return Provenanced(value=True, source="local", label="cache refreshed", as_of=now_iso())

    def _resolve(self, key: str, fetch_fn: Callable[[], Any]) -> Provenanced:
        """Three-tier cascade. Every exit returns Provenanced."""
        entry = self._cache.get(key)
        if entry is not None and entry.expires_at > now_utc():
            return Provenanced(value=entry.data, source="cached", as_of=entry.as_of)

        if self._should_try_live(key):
            try:
                data = self._fetch_with_timeout(fetch_fn)
                if data is not None:
                    timestamp = now_iso()
                    self._cache[key] = CacheEntry(
                        data=data,
                        as_of=timestamp,
                        expires_at=now_utc() + self._ttl_duration(),
                    )
                    self._clear_backoff(key)
                    return Provenanced(
                        value=data,
                        source=self._source.provenance_tier,
                        as_of=timestamp,
                    )
            except Exception:
                pass
            self._enter_backoff(key)

        if entry is not None:
            return Provenanced(value=entry.data, source="cached", as_of=entry.as_of)

        fixture = self._fixture_for_key(key)
        if fixture is not None:
            return Provenanced(
                value=fixture,
                source="fixture",
                label="sample data",
                as_of=self._fixture_as_of(),
            )

        return Provenanced(value=None, source="fixture", label="no data available")

    def _fetch_with_timeout(self, fetch_fn: Callable[[], Any]) -> Any:
        executor = ThreadPoolExecutor(max_workers=1)
        future: Future = executor.submit(fetch_fn)
        try:
            return future.result(timeout=LIVE_TIMEOUT_SECONDS)
        except FutureTimeout:
            future.cancel()
            raise
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _should_try_live(self, key: str) -> bool:
        backoff_until = self._backoff.get(key)
        if backoff_until and now_utc() < backoff_until:
            return False
        return True

    def _enter_backoff(self, key: str) -> None:
        current = self._backoff_delay.get(key, 15)
        new_delay = min(current * 2, MAX_BACKOFF_SECONDS)
        self._backoff_delay[key] = new_delay
        self._backoff[key] = now_utc() + timedelta(seconds=new_delay)

    def _clear_backoff(self, key: str) -> None:
        self._backoff.pop(key, None)
        self._backoff_delay.pop(key, None)

    def _ttl_duration(self) -> timedelta:
        """15 min during market hours, longer otherwise."""
        now = now_utc()
        et_hour = (now.hour - 4) % 24
        if now.weekday() < 5 and 9 <= et_hour < 16:
            return timedelta(minutes=15)
        return timedelta(hours=4)

    def _fixture_as_of(self) -> str | None:
        value = self._fixtures.get("captured_at")
        return str(value) if value is not None else None

    def _fixture_for_key(self, key: str) -> Any:
        if key in self._fixtures:
            return self._fixtures[key]
        if key.startswith("ohlcv:"):
            parts = key.split(":")
            if len(parts) >= 2:
                return self._fixtures.get("ohlcv", {}).get(parts[1])
        if key == "market_snapshot":
            return self._build_market_snapshot(
                self._fixtures.get("ohlcv", {}).get("SPY"),
                self._fixtures.get("info", {}).get("SPY"),
                self._fixtures.get("vix_current"),
            )
        if key.startswith("ticker:"):
            ticker = key.split(":", 1)[1]
            return self._build_ticker_snapshot(
                ticker,
                self._fixtures.get("ohlcv", {}).get(ticker),
                self._fixtures.get("info", {}).get(ticker),
            )
        if key.startswith("vix_hist:"):
            rows = self._fixtures.get("ohlcv", {}).get("^VIX")
            if rows:
                return {row["date"]: row["close"] for row in rows}
        if key.startswith("batch:"):
            parts = key.split(":")
            if len(parts) >= 2:
                rows = {}
                for ticker in [ticker for ticker in parts[1].split(",") if ticker]:
                    data = self._fixtures.get("ohlcv", {}).get(ticker)
                    if data:
                        rows[ticker] = data
                return rows or None
        return None

    def _build_market_snapshot(
        self,
        spy_ohlcv: list[dict] | None,
        spy_info: dict | None,
        vix: float | None,
    ) -> dict[str, Any] | None:
        if not spy_ohlcv or not spy_info:
            return None
        closes = [row["close"] for row in spy_ohlcv]
        volumes = [row["volume"] for row in spy_ohlcv]
        return {
            "spy": {
                "price": closes[-1] if closes else None,
                "change_pct": round((closes[-1] - closes[0]) / closes[0] * 100, 2)
                if len(closes) >= 2
                else None,
            },
            "vix": vix,
            "rsi": compute_rsi(closes),
            "above_50ma": (spy_info.get("previousClose", 0) > spy_info.get("fiftyDayAverage", 0)),
            "volume_rank": compute_vol_rank(volumes),
            "sector": spy_info.get("sector"),
            "market_cap_b": round(spy_info.get("marketCap", 0) / 1e9, 1)
            if spy_info.get("marketCap")
            else None,
            "source_detail": "yfinance",
        }

    def _build_ticker_snapshot(
        self,
        ticker: str,
        ohlcv: list[dict] | None,
        info: dict | None,
    ) -> dict[str, Any] | None:
        if not ohlcv:
            return None
        closes = [row["close"] for row in ohlcv]
        volumes = [row["volume"] for row in ohlcv]
        result: dict[str, Any] = {
            "ticker": ticker,
            "price": closes[-1] if closes else None,
            "change_30d_pct": round((closes[-1] - closes[0]) / closes[0] * 100, 2)
            if len(closes) >= 2
            else None,
            "volume": volumes[-1] if volumes else None,
            "rsi": compute_rsi(closes),
            "vol_rank_pctl": compute_vol_rank(volumes),
        }
        if info:
            result.update(
                {
                    "name": info.get("shortName"),
                    "sector": info.get("sector"),
                    "market_cap_b": round(info.get("marketCap", 0) / 1e9, 1)
                    if info.get("marketCap")
                    else None,
                    "above_50ma": (info.get("previousClose", 0) > info.get("fiftyDayAverage", 0)),
                }
            )
        return result
