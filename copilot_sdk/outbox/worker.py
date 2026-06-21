"""Outbox event replay worker."""

from __future__ import annotations

import logging
from typing import Callable

from .models import OutboxEvent
from .store import OutboxStore

logger = logging.getLogger(__name__)

EventHandler = Callable[[OutboxEvent], None]


class OutboxWorker:
    """Dispatch outbox events to registered idempotent handlers."""

    def __init__(
        self,
        store: OutboxStore,
        *,
        max_retries: int = 0,
        batch_size: int = 100,
    ):
        self._store = store
        self._handlers: dict[str, list[EventHandler]] = {}
        self._max_retries = max_retries
        # TODO: max_retries is accepted but not yet implemented.
        # Current behavior: immediate dead-letter on first failure.
        # Future: retry up to max_retries before dead-lettering.
        self._batch_size = batch_size
        self._running = True

    def register(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type."""

        self._handlers.setdefault(event_type, []).append(handler)

    def process_batch(self) -> int:
        """Process up to batch_size pending events."""

        events = self._store.get_unprocessed(self._batch_size)
        processed = 0
        for event in events:
            if not self._running:
                break
            handlers = self._handlers.get(event.event_type, [])
            if not handlers:
                logger.debug(
                    "No handler registered for %s, skipping event %d",
                    event.event_type,
                    event.event_id,
                )
                continue
            try:
                for handler in handlers:
                    handler(event)
                self._store.mark_processed(event.event_id)
            except Exception as exc:
                logger.error("Handler failed for event %d: %s", event.event_id, exc)
                self._store.mark_dead_letter(event.event_id, str(exc))
            processed += 1
        return processed

    def run_until_empty(self) -> int:
        """Process all currently pending events."""

        total = 0
        while self._running:
            processed = self.process_batch()
            if processed == 0:
                break
            total += processed
        return total

    def replay(self, from_offset: int = 0) -> int:
        """Replay all events from an event id offset."""

        replayed = 0
        for event in self._store.replay_from(from_offset):
            if not self._running:
                break
            handlers = self._handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as exc:
                    logger.warning(
                        "Replay handler failed for event %d: %s",
                        event.event_id,
                        exc,
                    )
            replayed += 1
        return replayed

    def stop(self) -> None:
        """Stop processing after the current handler/event finishes."""

        self._running = False

    @property
    def pending(self) -> int:
        """Return the number of pending events."""

        return self._store.count_unprocessed()
