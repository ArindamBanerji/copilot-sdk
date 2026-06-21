"""Outbox event models."""

from dataclasses import dataclass
from typing import Any


@dataclass
class OutboxEvent:
    """A persisted event pending handler dispatch or replay."""

    event_id: int
    event_type: str
    domain: str
    payload: dict[str, Any]
    created_at: float
    processed: bool = False
    processed_at: float | None = None
    error: str | None = None


EVENT_TYPES = frozenset(
    {
        "decision_created",
        "outcome_recorded",
        "centroid_updated",
        "dk_reestimated",
        "conservation_changed",
        "promotion_event",
    }
)
