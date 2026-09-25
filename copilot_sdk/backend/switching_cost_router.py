"""Switching-cost metrics for the shared copilot backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter


def _timestamp(value: Any) -> datetime | None:
    """Parse the timestamp formats used by graph-store decision records."""

    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _decision_records(scorer: Any, domain: str | None) -> list[dict[str, Any]]:
    """Read decisions from a proxy/scorer or a small test double."""

    store = getattr(scorer, "graph_store", None)
    if store is not None and domain is not None:
        records = store.get_all_decisions(domain)
        return list(records) if isinstance(records, list) else []
    records = getattr(scorer, "decisions", [])
    return list(records) if isinstance(records, list) else []


def _decision_count(scorer: Any, domain: str | None, records: list[dict[str, Any]]) -> int:
    store = getattr(scorer, "graph_store", None)
    if store is not None and domain is not None:
        try:
            return max(int(store.count_decisions(domain)), 0)
        except (TypeError, ValueError):
            return len(records)
    try:
        return max(int(scorer.get_decision_count()), 0)
    except (AttributeError, TypeError, ValueError):
        pass
    return len(records)


def _days_since_first(records: list[dict[str, Any]], now: Callable[[], datetime]) -> float:
    timestamps = [
        parsed
        for record in records
        for value in (record.get("created_at"), record.get("timestamp"), record.get("createdAt"))
        for parsed in [_timestamp(value)]
        if parsed is not None
    ]
    if not timestamps:
        return 0.0
    current = now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    elapsed = (current.astimezone(timezone.utc) - min(timestamps)).total_seconds() / 86_400.0
    return max(elapsed, 0.0)


def create_switching_cost_router(
    scorer: Any,
    *,
    domain: str | None = None,
    labeled_stream_to_close_pct: float = 50.0,
    now: Callable[[], datetime] | None = None,
) -> APIRouter:
    """Create the domain-scoped switching-cost metrics router.

    ``scorer`` is normally a ``FreshScorerProxy``.  ``domain`` is supplied by
    applications so the shared graph store can remain domain-scoped.
    """

    router = APIRouter(tags=["metrics"])
    clock = now or (lambda: datetime.now(timezone.utc))

    @router.get("/metrics/switching-cost")
    def switching_cost() -> dict[str, int | float]:
        records = _decision_records(scorer, domain)
        decisions = _decision_count(scorer, domain, records)
        if decisions <= 0:
            return {
                "decisions_accumulated": 0,
                "equivalent_calendar_days": 0.0,
                "labeled_stream_to_close_pct": 0.0,
            }
        days = _days_since_first(records, clock)
        return {
            "decisions_accumulated": decisions,
            "equivalent_calendar_days": round(days, 3),
            "labeled_stream_to_close_pct": float(labeled_stream_to_close_pct),
        }

    return router
