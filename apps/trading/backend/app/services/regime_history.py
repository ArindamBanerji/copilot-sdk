"""In-memory market regime history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class RegimeHistory:
    """Bounded in-memory regime history with a persistence hook shape."""

    def __init__(self, max_entries: int = 365):
        self._max_entries = max(1, int(max_entries))
        self._entries: list[dict[str, Any]] = []

    def record(
        self,
        regime: str,
        vix: float,
        adx: float,
        timestamp: str | None = None,
    ) -> None:
        stamp = timestamp or datetime.now(timezone.utc).isoformat()
        self._entries.append(
            {
                "date": stamp,
                "regime": str(regime),
                "vix": float(vix),
                "adx": float(adx),
            }
        )
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

    def history(self, days: int = 90) -> list[dict[str, Any]]:
        """Return recent history, most recent first."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(0, int(days)))
        rows = [entry for entry in self._entries if _parse_timestamp(entry["date"]) >= cutoff]
        return sorted(rows, key=lambda entry: _parse_timestamp(entry["date"]), reverse=True)

    def regime_distribution(self, days: int = 90) -> dict[str, int]:
        """Return counts by regime for the requested window."""
        counts = {"trending": 0, "ranging": 0, "volatile": 0}
        for entry in self.history(days):
            regime = str(entry.get("regime") or "ranging")
            if regime in counts:
                counts[regime] += 1
        return counts


def _parse_timestamp(value: Any) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
