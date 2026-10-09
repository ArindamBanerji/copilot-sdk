"""Verified receipt persistence through the injected graph store."""
from __future__ import annotations

import json
from threading import RLock
from copilot_sdk.graph.protocol import ProtocolV2GraphStore
from copilot_sdk.timestamps import normalize_timestamp
from .models import VerifiedOutcome


class OutcomeLedger:
    """Read receipts from graph events; never maintain a second authority."""

    def __init__(self, graph_store: ProtocolV2GraphStore, domain: str) -> None:
        self.graph_store = graph_store
        self.domain = domain
        self._lock = RLock()

    def append(self, outcome: VerifiedOutcome) -> bool:
        receipt_id = outcome.receipt_id()
        with self._lock:
            if self.exists(receipt_id):
                return False
            self.graph_store.write_evolution_event(
                event_id=f"verified-outcome:{self.domain}:{receipt_id}",
                domain=self.domain, event_type="verified_outcome",
                rule_name=outcome.category, variant_id=outcome.decision_id,
                metadata={"receipt": outcome.to_dict()},
            )
            return True

    def _receipts(self) -> list[VerifiedOutcome]:
        receipts = []
        for event in self.graph_store.get_evolution_events(
            self.domain, event_type="verified_outcome", limit=None
        ):
            metadata = event.get("metadata") or event.get("metadata_json") or {}
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            receipts.append(VerifiedOutcome.from_dict(metadata["receipt"]))
        return receipts

    def get(self, receipt_id: str) -> VerifiedOutcome | None:
        return next((row for row in self._receipts() if row.receipt_id() == receipt_id), None)

    def exists(self, receipt_id: str) -> bool:
        return self.get(receipt_id) is not None

    def count(self, copilot: str, category: str | None = None) -> int:
        return sum(row.copilot == copilot and (category is None or row.category == category)
                   for row in self._receipts())

    def list_recent(self, copilot: str, limit: int = 100) -> list[VerifiedOutcome]:
        rows = [row for row in self._receipts() if row.copilot == copilot]
        rows.sort(key=lambda row: (-normalize_timestamp(row.timestamp), row.receipt_id()))
        return rows[:max(0, min(int(limit), 10_000))]

    def close(self) -> None:
        """The caller owns the injected graph's lifetime."""
