"""Cross-copilot fact delivery projected from immutable graph events.

The graph owns persistence. Each read reconstructs the bounded, expiring inbox;
evicted facts remain graph history and never become domain decisions.
"""
from __future__ import annotations

from base64 import urlsafe_b64encode
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import time
from typing import Any
import uuid

from copilot_sdk.config.tenant import current_tenant_id
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore

MAX_SIGNALS = 1000
EVICTION_BATCH = 100
SIGNAL_TTL = timedelta(hours=24)
SIGNAL_EVENT_TYPE = "cross_signal"


class GraphSignalEvents:
    """Deliver facts across routers sharing a graph and tenant.

    Publication is one immutable event write, with no read-modify-write inbox.
    Replay orders publications by epoch time, monotonic tick, then opaque ID.
    The tick preserves sequential publication order on coarse system clocks;
    equal ticks across hosts still resolve deterministically by ID.
    Retention applies globally before recipient filtering and pagination.
    """

    def __init__(self, graph_store: GraphStore) -> None:
        if not isinstance(graph_store, ProtocolV2GraphStore):
            raise TypeError("Cross-copilot signals require graph evolution-event support")
        self._graph = graph_store

    @staticmethod
    def _domain() -> str:
        # Reversible encoding preserves tenant identity within graph domain syntax
        # (letters, digits, underscores, hyphens; at most 200 characters).
        tenant = urlsafe_b64encode(current_tenant_id().encode("ascii")).decode("ascii").rstrip("=")
        return f"cross_signals_{tenant}"

    def publish(self, signal: dict[str, Any]) -> str:
        record = deepcopy(signal)
        published = datetime.now(timezone.utc)
        stamp = record.get("timestamp") or published.isoformat()
        parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        record["timestamp"] = parsed.isoformat()
        signal_id = f"sig-{uuid.uuid4().hex}"
        record["signal_id"] = signal_id
        self._graph.write_evolution_event(
            event_id=signal_id,
            domain=self._domain(),
            event_type=SIGNAL_EVENT_TYPE,
            rule_name=str(record["signal_type"]),
            variant_id="",
            source_copilot=str(record["source_copilot"]),
            metadata={
                "timestamp": published.isoformat(),
                "published_at": published.timestamp(),
                "publication_order": time.perf_counter_ns(),
                "signal_timestamp": parsed.timestamp(),
                "payload": record,
            },
        )
        return signal_id

    def _active(self) -> list[dict[str, Any]]:
        events = self._graph.get_evolution_events(
            self._domain(), event_type=SIGNAL_EVENT_TYPE, limit=None,
        )
        events.sort(key=lambda event: (
            float(event["metadata"]["published_at"]),
            int(event["metadata"]["publication_order"]), str(event["event_id"]),
        ))
        active: list[tuple[float, dict[str, Any]]] = []
        ttl = SIGNAL_TTL.total_seconds()
        for event in events:
            metadata = event["metadata"]
            cutoff = float(metadata["published_at"]) - ttl
            active = [(stamp, record) for stamp, record in active if stamp >= cutoff]
            if len(active) >= MAX_SIGNALS:
                del active[:EVICTION_BATCH]
            active.append((float(metadata["signal_timestamp"]), metadata["payload"]))
        cutoff = datetime.now(timezone.utc).timestamp() - ttl
        return [deepcopy(record) for stamp, record in active if stamp >= cutoff]

    def page(
        self, limit: int = 50, offset: int = 0,
        source_copilot: str | None = None, target_copilot: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        if not 1 <= limit <= MAX_SIGNALS or offset < 0:
            raise ValueError("invalid pagination")
        records = [
            record for record in self._active()
            if (source_copilot is None or record["source_copilot"] == source_copilot)
            and (target_copilot is None or record.get("target_copilot") in (None, target_copilot))
        ]
        return records[offset:offset + limit], len(records)

    def list(
        self, limit: int = 50, offset: int = 0, source_copilot: str | None = None,
        target_copilot: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.page(limit, offset, source_copilot, target_copilot)[0]

    def count(self) -> int:
        return self.page(limit=1)[1]

    def get(self, signal_id: str) -> dict[str, Any] | None:
        return next((record for record in self._active() if record["signal_id"] == signal_id), None)
