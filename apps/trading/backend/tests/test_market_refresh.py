from __future__ import annotations

from app import context_router
from app.routers import data_import
from copilot_sdk.evidence.provenance import Provenanced


class _RefreshProvider:
    def __init__(self, *, failed: bool = False) -> None:
        self.refresh_calls = 0
        self.snapshot_calls = 0
        self.failed = failed

    def refresh(self) -> Provenanced[bool]:
        self.refresh_calls += 1
        return Provenanced(value=True, source="local", as_of="2026-06-14T15:59:00Z")

    def get_market_snapshot(self) -> Provenanced[dict | None]:
        self.snapshot_calls += 1
        if self.failed:
            return Provenanced(value=None, source="fixture", label="no data available")
        suffix = "fresh" if self.refresh_calls else "initial"
        return Provenanced(
            value={
                "spy": {"price": 555.2, "change_pct": 1.3},
                "vix": 18.5,
                "rsi": 58.0,
                "above_50ma": True,
                "volume_rank": 67,
                "sector": "Financial Services",
                "market_cap_b": 550.0,
            },
            source="live",
            as_of=f"2026-06-14T16:00:00Z-{suffix}",
        )


def test_refresh_returns_200(client, monkeypatch):
    """POST /api/trading/market/refresh returns 200 with provenance."""
    provider = _RefreshProvider()
    monkeypatch.setattr(data_import, "_provider", provider)

    response = client.post("/api/trading/market/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["refreshed"] is True
    assert payload["provenance"]["source"] == "live"
    assert payload["provenance"]["as_of"] == "2026-06-14T16:00:00Z-fresh"
    assert provider.refresh_calls == 1


def test_refresh_clears_cache_and_refetches(client, monkeypatch):
    """After refresh, next market-snapshot call returns fresh data."""
    provider = _RefreshProvider()
    monkeypatch.setattr(data_import, "_provider", provider)
    monkeypatch.setattr(context_router, "_provider", provider)

    before = client.get("/api/context/market-snapshot").json()
    refresh = client.post("/api/trading/market/refresh").json()
    after = client.get("/api/context/market-snapshot").json()

    assert before["provenance"]["as_of"] == "2026-06-14T16:00:00Z-initial"
    assert refresh["provenance"]["as_of"] == "2026-06-14T16:00:00Z-fresh"
    assert after["provenance"]["as_of"] == "2026-06-14T16:00:00Z-fresh"
    assert provider.refresh_calls == 1
    assert provider.snapshot_calls == 3


def test_refresh_with_failed_source(client, monkeypatch):
    """Refresh when source is down returns fixture provenance."""
    provider = _RefreshProvider(failed=True)
    monkeypatch.setattr(data_import, "_provider", provider)

    response = client.post("/api/trading/market/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["refreshed"] is True
    assert payload["provenance"]["source"] == "fixture"
