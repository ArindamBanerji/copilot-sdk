"""Outbox event models."""

from dataclasses import dataclass
from typing import Any


class OutboxEventType:
    """String constants for persisted outbox event types."""

    DECISION_CREATED = "decision_created"
    OUTCOME_RECORDED = "outcome_recorded"
    CENTROID_UPDATED = "centroid_updated"
    DK_REESTIMATED = "dk_reestimated"
    CONSERVATION_CHANGED = "conservation_changed"
    PROMOTION_EVENT = "promotion_event"
    SUPPLIER_RELIABILITY_SIGNAL = "supplier_reliability_signal"


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


@dataclass
class SupplierReliabilitySignal:
    supplier_name: str
    reliability_pct: float
    previous_pct: float
    delta: float
    trend: str
    source_copilot: str
    target_copilot: str
    timestamp: float
    ttl_days: int = 7
    provenance: str = "signal"


EVENT_TYPES = frozenset(
    {
        OutboxEventType.DECISION_CREATED,
        OutboxEventType.OUTCOME_RECORDED,
        OutboxEventType.CENTROID_UPDATED,
        OutboxEventType.DK_REESTIMATED,
        OutboxEventType.CONSERVATION_CHANGED,
        OutboxEventType.PROMOTION_EVENT,
        OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
    }
)
