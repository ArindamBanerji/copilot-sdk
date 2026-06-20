"""Commodity data provider with cache-first provenance tagging."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.connectors.mock_commodity import MockCommoditySource
from copilot_sdk.evidence.provenance import Provenanced

LIVE_TIMEOUT_SECONDS = 3
MAX_BACKOFF_SECONDS = 300
COMMODITY_CATEGORIES = ("protein", "produce", "dairy", "dry_goods", "beverages")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


@dataclass
class CacheEntry:
    data: object
    as_of: str
    expires_at: datetime


class CommodityDataProvider:
    """Cache-first cascade with mandatory provenance tagging.

    Cascade: cached -> live (3s timeout) -> stale cached -> fixture.
    Every public method returns Provenanced[T].
    Copy of Trading's MarketDataProvider for Purchasing domain.
    """

    def __init__(self, source: Any | None = None, fixture_data: dict | None = None):
        if source is None:
            source = MockCommoditySource()
        self._source = source
        self._cache: dict[str, CacheEntry] = {}
        self._backoff: dict[str, datetime] = {}
        self._backoff_delay: dict[str, int] = {}
        self._fixture = fixture_data or MockCommoditySource.MOCK_PRICES

    def get_category_prices(self, category: str) -> Provenanced[list[dict] | None]:
        """Commodity prices for a food category."""
        return self._resolve(f"prices:{category}", lambda: self._source.fetch_category_prices(category))

    def get_price_index(self, category: str) -> Provenanced[float | None]:
        """Current price versus 12-month average."""
        return self._resolve(f"index:{category}", lambda: self._source.fetch_price_index(category))

    def get_all_indices(self) -> Provenanced[dict[str, float] | None]:
        """Price indices for all five categories."""

        def fetch() -> dict[str, float] | None:
            indices = {}
            for category in COMMODITY_CATEGORIES:
                value = self._source.fetch_price_index(category)
                if value is not None:
                    indices[category] = value
            return indices or None

        return self._resolve("indices", fetch)

    def refresh(self, category: str | None = None) -> Provenanced[bool]:
        """Force cache refresh for a category or all categories."""
        if category:
            for key in (f"prices:{category}", f"index:{category}", "indices"):
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
                        source=self._source_provenance_tier(),
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
                source="sample",
                label="sample data",
                as_of=self._fixture_as_of(),
            )

        return Provenanced(value=None, source="sample", label="no data available")

    def _source_provenance_tier(self) -> str:
        return str(getattr(self._source, "provenance_tier", "sample"))

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
        return timedelta(hours=24)

    def _fixture_as_of(self) -> str | None:
        value = self._fixture.get("captured_at") if isinstance(self._fixture, dict) else None
        return str(value) if value is not None else None

    def _fixture_for_key(self, key: str) -> Any:
        if key.startswith("prices:"):
            category = key.split(":", 1)[1]
            rows = self._fixture.get(category)
            return [dict(row) for row in rows] if rows else None
        if key.startswith("index:"):
            category = key.split(":", 1)[1]
            return self._fixture_index(category)
        if key == "indices":
            values = {
                category: value
                for category in COMMODITY_CATEGORIES
                if (value := self._fixture_index(category)) is not None
            }
            return values or None
        return None

    def _fixture_index(self, category: str) -> float | None:
        rows = self._fixture.get(category) if isinstance(self._fixture, dict) else None
        if not rows:
            return None
        prices = [float(row["price"]) for row in rows if row.get("price") is not None]
        if not prices:
            return None
        avg = sum(prices) / len(prices)
        return round(prices[-1] / avg, 3) if avg else None
