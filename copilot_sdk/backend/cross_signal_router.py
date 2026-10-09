"""Cross-copilot fact signals.

Signals transfer facts; judgment remains per-copilot. A receiving copilot
must re-score the fact as context using its own domain-specific policy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator


from copilot_sdk.backend.graph_signals import (
    EVICTION_BATCH as EVICTION_BATCH,
    MAX_SIGNALS as MAX_SIGNALS,
    SIGNAL_TTL as SIGNAL_TTL,
    GraphSignalEvents,
)
from copilot_sdk.graph.protocol import GraphStore


class CrossCopilotSignal(BaseModel):
    source_copilot: str = Field(..., min_length=1)
    signal_type: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    detail: str | None = Field(default=None, min_length=1)
    timestamp: datetime | None = None
    target_copilot: str | None = None

    @field_validator("source_copilot", "signal_type", "entity_id", "detail")
    @classmethod
    def non_blank_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("text fields must not be blank")
        return normalized

    @field_validator("timestamp", mode="before")
    @classmethod
    def valid_iso_timestamp(cls, value: object) -> object:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("timestamp must be valid ISO 8601") from exc
            return value
        raise ValueError("timestamp must be valid ISO 8601")


def create_cross_signal_router(
    graph_store: GraphStore,
) -> APIRouter:
    """Create signal routes over the application's configured graph."""

    router = APIRouter(tags=["platform"])
    signals = GraphSignalEvents(graph_store)

    @router.post("/platform/cross-signals", status_code=201)
    def publish_signal(signal: CrossCopilotSignal) -> dict[str, Any]:
        signal_id = signals.publish(signal.model_dump(mode="json"))
        return {
            "signal_id": signal_id,
            "status": "published",
            "honesty_note": "Signals transfer facts; judgment is per-copilot.",
        }

    @router.get("/platform/cross-signals")
    def get_signals(
        target_copilot: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=MAX_SIGNALS),
        offset: int = Query(default=0, ge=0),
        source_copilot: str | None = Query(default=None),
    ) -> dict[str, Any]:
        active, count = signals.page(limit, offset, source_copilot, target_copilot)
        return {
            "signals": active,
            "count": count,
            "limit": limit,
            "offset": offset,
            "honesty_note": "Signals transfer facts; judgment is per-copilot.",
        }

    @router.get("/platform/cross-signals/{signal_id}")
    def get_signal(signal_id: str) -> dict[str, Any]:
        record = signals.get(signal_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Signal not found")
        return {
            **record,
            "honesty_note": "Signals transfer facts; judgment is per-copilot.",
        }

    return router
