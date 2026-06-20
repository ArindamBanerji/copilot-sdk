"""Conservation-gated auto-ordering for purchasing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import random
from typing import Any
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class AutoOrderEvent:
    event_id: str
    order_id: str | None
    decision_id: str | None
    category: str
    action: str
    confidence: float
    threshold: float
    auto_order: bool
    spot_check: bool
    reason: str
    source: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutoOrderGate:
    """Conservation-gated auto-ordering.

    Kitchen language: use auto-ordering for order flow, not approval language.

    Safety invariants:
    1. OFF by default.
    2. Conservation GREEN required per category.
    3. Threshold ratchets toward more caution after errors.
    4. Any executed learning must use the same learn() path as manual verify.
    5. Audit entries use source="auto_order".
    """

    def __init__(
        self,
        initial_threshold: float = 0.90,
        min_threshold: float = 0.75,
        spot_check_rate: float = 0.02,
        min_verified: int = 50,
    ) -> None:
        if not 0.0 <= min_threshold <= initial_threshold <= 1.0:
            raise ValueError("thresholds must satisfy 0 <= min <= initial <= 1")
        if not 0.0 <= spot_check_rate <= 1.0:
            raise ValueError("spot_check_rate must be between 0 and 1")
        if min_verified < 0:
            raise ValueError("min_verified must be non-negative")
        self._enabled = False
        self._threshold = float(initial_threshold)
        self._initial_threshold = float(initial_threshold)
        self._min_threshold = float(min_threshold)
        self._spot_check_rate = float(spot_check_rate)
        self._min_verified = int(min_verified)
        self._auto_ordered_count = 0
        self._spot_check_count = 0
        self._error_count = 0
        self._evaluation_count = 0
        self._audit: list[AutoOrderEvent] = []
        self._rng = random.Random(0)

    def evaluate(
        self,
        category: str,
        confidence: float,
        conservation_status: str,
        verified_count: int,
        *,
        order_id: str | None = None,
        decision_id: str | None = None,
        action: str = "order_as_planned",
    ) -> dict[str, Any]:
        """Return whether an order should be auto-ordered."""
        safe_confidence = _clamp(confidence)
        verified = max(int(verified_count), 0)
        status = str(conservation_status or "UNKNOWN").upper()
        reason = self._blocked_reason(safe_confidence, status, verified)
        auto_order = reason == "accepted"
        spot_check = False
        if auto_order:
            spot_check = self._rng.random() < self._spot_check_rate
            if spot_check:
                self._spot_check_count += 1
                reason = "spot_check"
            self._auto_ordered_count += 1
        self._evaluation_count += 1
        event = self._record_event(
            category=category,
            confidence=safe_confidence,
            order_id=order_id,
            decision_id=decision_id,
            action=action,
            auto_order=auto_order,
            spot_check=spot_check,
            reason=reason,
        )
        return {
            "auto_order": auto_order,
            "reason": reason,
            "spot_check": spot_check,
            "threshold": self._threshold,
            "event": event.to_dict(),
        }

    def enable(self, conservation_status: str) -> dict[str, Any]:
        """Enable auto-ordering only when conservation is GREEN."""
        status = str(conservation_status or "UNKNOWN").upper()
        if status != "GREEN":
            self._enabled = False
            return {
                **self.status,
                "reason": "conservation_not_green",
                "conservation_status": status,
            }
        self._enabled = True
        return {
            **self.status,
            "reason": "enabled",
            "conservation_status": status,
        }

    def disable(self) -> dict[str, Any]:
        """Disable auto-ordering."""
        self._enabled = False
        return {**self.status, "reason": "disabled"}

    def contract_threshold(self, error_rate: float) -> dict[str, Any]:
        """Ratchet threshold up after errors."""
        rate = max(float(error_rate), 0.0)
        if rate <= 0:
            return {"changed": False, "threshold": self._threshold}
        previous = self._threshold
        self._threshold = min(1.0, round(self._threshold + min(rate, 0.10), 4))
        self._error_count += 1
        return {"changed": self._threshold != previous, "threshold": self._threshold}

    def expand_threshold(self, accuracy: float) -> dict[str, Any]:
        """Ratchet threshold down after sustained accuracy, never below the floor."""
        safe_accuracy = _clamp(accuracy)
        if safe_accuracy < 0.95:
            return {"changed": False, "threshold": self._threshold}
        previous = self._threshold
        self._threshold = max(self._min_threshold, round(self._threshold - 0.01, 4))
        return {"changed": self._threshold != previous, "threshold": self._threshold}

    @property
    def status(self) -> dict[str, Any]:
        evaluations = max(self._evaluation_count, 1)
        return {
            "enabled": self._enabled,
            "threshold": self._threshold,
            "initial_threshold": self._initial_threshold,
            "min_threshold": self._min_threshold,
            "spot_check_rate": self._spot_check_rate,
            "min_verified": self._min_verified,
            "auto_ordered_count": self._auto_ordered_count,
            "spot_check_count": self._spot_check_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / evaluations,
            "audit_count": len(self._audit),
        }

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        count = max(int(limit), 0)
        return [event.to_dict() for event in self._audit[-count:]]

    def _blocked_reason(self, confidence: float, conservation_status: str, verified_count: int) -> str:
        if not self._enabled:
            return "disabled"
        if conservation_status != "GREEN":
            return "conservation_not_green"
        if verified_count < self._min_verified:
            return "insufficient_verified_count"
        if confidence < self._threshold:
            return "below_threshold"
        return "accepted"

    def _record_event(
        self,
        *,
        category: str,
        confidence: float,
        order_id: str | None,
        decision_id: str | None,
        action: str,
        auto_order: bool,
        spot_check: bool,
        reason: str,
    ) -> AutoOrderEvent:
        event = AutoOrderEvent(
            event_id=f"AUTO-ORDER-{uuid4().hex}",
            order_id=order_id,
            decision_id=decision_id,
            category=str(category),
            action=str(action),
            confidence=float(confidence),
            threshold=float(self._threshold),
            auto_order=bool(auto_order),
            spot_check=bool(spot_check),
            reason=str(reason),
            source="auto_order",
            created_at=_now_iso(),
        )
        self._audit.append(event)
        self._audit = self._audit[-200:]
        return event


def _clamp(value: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(parsed, 0.0), 1.0)
