"""Evolution event ledgers."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Any

from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionStore
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox

logger = logging.getLogger(__name__)


class InMemoryEvolutionLedger:
    """Append-only event ledger with optional evolution-store persistence."""

    def __init__(
        self,
        evolution_store: EvolutionStore | None = None,
        domain: str = "unknown",
        outbox: PersistenceOutbox | None = None,
    ) -> None:
        self._events: list[EvolutionEvent] = []
        self.domain = str(domain or "unknown")
        self._evolution_store = evolution_store
        self._outbox = outbox

    @property
    def event_count(self) -> int:
        return len(self._events)

    def append(self, event: EvolutionEvent, *, decision_id: str | None = None) -> None:
        self._events.append(event)
        if self._evolution_store is None:
            return
        event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{self.domain}|{event.event_type}|{event.rule_name}|{event.variant_id}|{event.timestamp}",
            )
        )
        resolved_decision_id = decision_id
        if resolved_decision_id is None:
            candidate = event.metadata.get("decision_id")
            if candidate is not None:
                resolved_decision_id = str(candidate)
        event_metadata = {**event.metadata, "timestamp": event.timestamp}
        if resolved_decision_id is not None:
            event_metadata["decision_id"] = resolved_decision_id
        payload: dict[str, Any] = {
            "event_id": event_id,
            "domain": self.domain,
            "event_type": event.event_type,
            "rule_name": event.rule_name,
            "variant_id": event.variant_id,
            "metadata": event_metadata,
        }
        if resolved_decision_id is not None:
            payload["decision_id"] = resolved_decision_id
        try:
            if hasattr(self._evolution_store, "write_evolution_event"):
                self._evolution_store.write_evolution_event(**payload)
            else:
                self._evolution_store.save_evolution_event(
                    domain=self.domain,
                    event_type=event.event_type,
                    rule_name=event.rule_name,
                    variant_id=event.variant_id,
                    metadata=event_metadata,
                )
        except Exception as exc:  # pragma: no cover - warning path is tested with caplog
            logger.warning("Failed to persist evolution event: %s", exc)
            if self._outbox is not None:
                try:
                    self._outbox.record_failure(event_id, "evolution", payload, str(exc))
                except Exception as outbox_exc:
                    logger.warning("Persistence outbox record failed: %s", outbox_exc)

    def get_events(
        self,
        rule_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        events = [
            event
            for event in self._events
            if rule_name is None or event.rule_name == rule_name
        ]
        limit_value = max(int(limit), 0)
        if limit_value:
            events = events[-limit_value:]
        else:
            events = []
        return [asdict(event) for event in events]

    def get_promoted_rules(self) -> list[str]:
        promoted: list[str] = []
        seen: set[str] = set()
        for event in self._events:
            if event.event_type != "promoted" or event.rule_name in seen:
                continue
            promoted.append(event.rule_name)
            seen.add(event.rule_name)
        return promoted

    def reset(self) -> None:
        self._events.clear()
