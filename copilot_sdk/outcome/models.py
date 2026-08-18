"""Canonical verified-decision receipt models.

The canonical learning contract deliberately has no legacy RL field names.
Compatibility translation belongs in :mod:`copilot_sdk.outcome.adapters`.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np


_DISPOSITIONS = frozenset({"confirm", "override"})
_FORBIDDEN_CANONICAL_KEYS = frozenset({"re" + "ward", "re" + "ward_raw", "rl_" + "reward", "policy"})  # adapter guard


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_timestamp(value: str) -> str:
    timestamp = str(value).strip()
    if not timestamp:
        raise ValueError("timestamp is required")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("timestamp must be ISO 8601") from error
    return timestamp


@dataclass(frozen=True)
class VerifiedOutcome:
    """A human verification and its measured result for one decision."""

    outcome_id: str
    copilot: str
    decision_id: str
    category: str
    factor_vector: list[float]
    predicted_action: str
    human_disposition: str
    override_action: str | None
    override_reason: str | None
    correct: bool
    measured_impact: dict[str, Any] | None
    evidence_provenance: str
    timestamp: str

    def __post_init__(self) -> None:
        for field_name in ("outcome_id", "copilot", "decision_id", "category", "predicted_action", "evidence_provenance"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")
        if self.human_disposition not in _DISPOSITIONS:
            raise ValueError("human_disposition must be 'confirm' or 'override'")
        if self.human_disposition == "override" and not str(self.override_action or "").strip():
            raise ValueError("override_action is required for an override")
        if self.human_disposition == "override" and not str(self.override_reason or "").strip():
            raise ValueError("override_reason is required for an override")
        if not isinstance(self.correct, bool):
            raise TypeError("correct must be a bool")
        vector = [float(value) for value in self.factor_vector]
        if not vector or not np.all(np.isfinite(np.asarray(vector, dtype=np.float64))):
            raise ValueError("factor_vector must contain finite numeric values")
        object.__setattr__(self, "factor_vector", vector)
        object.__setattr__(self, "measured_impact", copy.deepcopy(self.measured_impact))
        object.__setattr__(self, "timestamp", _validate_timestamp(self.timestamp))

    @classmethod
    def create(
        cls,
        *,
        copilot: str,
        decision_id: str,
        category: str,
        factor_vector: list[float],
        predicted_action: str,
        human_disposition: str,
        override_action: str | None = None,
        override_reason: str | None = None,
        correct: bool,
        measured_impact: dict[str, Any] | None = None,
        evidence_provenance: str,
        timestamp: str | None = None,
    ) -> "VerifiedOutcome":
        resolved_timestamp = timestamp or _now_iso()
        outcome_id = f"{copilot}:{decision_id}:{resolved_timestamp}"
        return cls(
            outcome_id=outcome_id,
            copilot=copilot,
            decision_id=decision_id,
            category=category,
            factor_vector=factor_vector,
            predicted_action=predicted_action,
            human_disposition=human_disposition,
            override_action=override_action,
            override_reason=override_reason,
            correct=correct,
            measured_impact=measured_impact,
            evidence_provenance=evidence_provenance,
            timestamp=resolved_timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a detached JSON-compatible receipt representation."""
        return copy.deepcopy(asdict(self))

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "VerifiedOutcome":
        if not isinstance(value, dict):
            raise TypeError("verified outcome must be a dictionary")
        forbidden = sorted(_FORBIDDEN_CANONICAL_KEYS.intersection(value))
        if forbidden:
            raise ValueError(f"legacy fields are not valid canonical fields: {forbidden}")
        required = {
            "copilot",
            "decision_id",
            "category",
            "factor_vector",
            "predicted_action",
            "human_disposition",
            "correct",
            "evidence_provenance",
            "timestamp",
        }
        missing = sorted(required.difference(value))
        if missing:
            raise ValueError(f"verified outcome is missing required fields: {missing}")
        timestamp = str(value["timestamp"])
        outcome_id = str(value.get("outcome_id") or f"{value['copilot']}:{value['decision_id']}:{timestamp}")
        return cls(
            outcome_id=outcome_id,
            copilot=str(value["copilot"]),
            decision_id=str(value["decision_id"]),
            category=str(value["category"]),
            factor_vector=list(value["factor_vector"]),
            predicted_action=str(value["predicted_action"]),
            human_disposition=str(value["human_disposition"]),
            override_action=None if value.get("override_action") is None else str(value["override_action"]),
            override_reason=None if value.get("override_reason") is None else str(value["override_reason"]),
            correct=value["correct"],
            measured_impact=None if value.get("measured_impact") is None else dict(value["measured_impact"]),
            evidence_provenance=str(value["evidence_provenance"]),
            timestamp=timestamp,
        )

    def receipt_id(self) -> str:
        """Return the stable exactly-once identity for this decision."""
        material = f"{self.copilot.strip()}\x1f{self.decision_id.strip()}".encode("utf-8")
        return hashlib.sha256(material).hexdigest()
