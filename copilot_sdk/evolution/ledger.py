"""Evolution event ledgers."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionStore

logger = logging.getLogger(__name__)


class InMemoryEvolutionLedger:
    """Append-only event ledger with optional evolution-store persistence."""

    def __init__(
        self,
        evolution_store: EvolutionStore | None = None,
        domain: str = "unknown",
    ) -> None:
        self._events: list[EvolutionEvent] = []
        self.domain = str(domain or "unknown")
        self._evolution_store = evolution_store

    @property
    def event_count(self) -> int:
        return len(self._events)

    def append(self, event: EvolutionEvent) -> None:
        self._events.append(event)
        if self._evolution_store is None:
            return
        try:
            self._evolution_store.save_evolution_event(
                domain=self.domain,
                event_type=event.event_type,
                rule_name=event.rule_name,
                variant_id=event.variant_id,
                metadata={
                    **event.metadata,
                    "timestamp": event.timestamp,
                },
            )
        except Exception as exc:  # pragma: no cover - warning path is tested with caplog
            logger.warning("Failed to persist evolution event: %s", exc)

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
