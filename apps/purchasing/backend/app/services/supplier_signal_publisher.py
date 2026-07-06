"""Supplier reliability signal publisher for cross-copilot propagation."""

from __future__ import annotations

from dataclasses import asdict
import time
from typing import Any

from copilot_sdk.outbox import OutboxEventType, SupplierReliabilitySignal

DOMAIN = "purchasing"
SIGNAL_TTL_DAYS = 7


class SupplierSignalPublisher:
    def __init__(self, outbox_store: Any):
        self._outbox = outbox_store

    def check_and_publish(self, scorecard: Any) -> bool:
        """Publish a signal when supplier reliability has crossed the drop threshold."""

        reliability = _float(getattr(scorecard, "reliability_pct", 100.0), 100.0)
        trend = str(getattr(scorecard, "trend", "") or "").lower()
        if trend != "declining" and reliability >= 80.0:
            return False

        supplier_name = str(getattr(scorecard, "supplier_name", "") or getattr(scorecard, "supplier_id", ""))
        if not supplier_name:
            return False
        current = time.time()
        existing = active_supplier_signals(self._outbox, supplier_name, now=current)
        if existing:
            return False

        previous_signal = _latest_supplier_signal(self._outbox, supplier_name)
        previous_value = getattr(scorecard, "previous_reliability_pct", None)
        if previous_value is None and previous_signal is not None:
            previous_value = previous_signal.get("reliability_pct")
        previous = _float_or_none(previous_value)
        delta = reliability - previous if previous is not None else None
        signal = SupplierReliabilitySignal(
            supplier_name=supplier_name,
            reliability_pct=reliability,
            previous_pct=previous,
            delta=delta,
            trend=trend or "declining",
            source_copilot=DOMAIN,
            target_copilot="s2p",
            timestamp=current,
            ttl_days=SIGNAL_TTL_DAYS,
            provenance="signal",
        )
        self._outbox.append(
            OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
            DOMAIN,
            asdict(signal),
        )
        return True


def active_supplier_signals(outbox_store: Any, supplier_name: str, now: float | None = None) -> list[dict[str, Any]]:
    """Return active signal payloads for a supplier name."""

    current = time.time() if now is None else float(now)
    target = _supplier_key(supplier_name)
    # NOTE: Full scan is acceptable for demo-scale outbox (< 1000 events).
    # Production would use indexed DB query with TTL filter.
    rows = getattr(outbox_store, "replay_from", lambda _offset=0: [])(0)
    signals: list[dict[str, Any]] = []
    for row in rows or []:
        if getattr(row, "event_type", None) != OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL:
            continue
        payload = dict(getattr(row, "payload", {}) or {})
        if _supplier_key(payload.get("supplier_name")) != target:
            continue
        if signal_expired(payload, now=current):
            continue
        signals.append(payload)
    signals.sort(key=lambda item: float(item.get("timestamp") or 0.0), reverse=True)
    return signals


def signal_stats(outbox_store: Any, now: float | None = None) -> dict[str, int]:
    current = time.time() if now is None else float(now)
    # NOTE: Full scan is acceptable for demo-scale outbox (< 1000 events).
    # Production would use indexed DB query with TTL filter.
    rows = getattr(outbox_store, "replay_from", lambda _offset=0: [])(0)
    total = 0
    expired = 0
    for row in rows or []:
        if getattr(row, "event_type", None) != OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL:
            continue
        total += 1
        if signal_expired(dict(getattr(row, "payload", {}) or {}), now=current):
            expired += 1
    return {"total_published": total, "active": total - expired, "expired": expired}


def signal_expired(signal: dict[str, Any], now: float | None = None) -> bool:
    current = time.time() if now is None else float(now)
    timestamp = _float(signal.get("timestamp"), 0.0)
    ttl_days = int(_float(signal.get("ttl_days"), SIGNAL_TTL_DAYS))
    return current - timestamp >= ttl_days * 86400


def _supplier_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _latest_supplier_signal(outbox_store: Any, supplier_name: str) -> dict[str, Any] | None:
    target = _supplier_key(supplier_name)
    rows = getattr(outbox_store, "replay_from", lambda _offset=0: [])(0)
    matches: list[dict[str, Any]] = []
    for row in rows or []:
        if getattr(row, "event_type", None) != OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL:
            continue
        payload = dict(getattr(row, "payload", {}) or {})
        if _supplier_key(payload.get("supplier_name")) == target:
            matches.append(payload)
    if not matches:
        return None
    return max(matches, key=lambda item: _float(item.get("timestamp"), 0.0))


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
