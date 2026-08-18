"""Compatibility adapters for legacy outcome payloads."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from .models import VerifiedOutcome


def reward_to_outcome(legacy_payload: dict[str, Any], copilot: str) -> VerifiedOutcome:  # adapter
    """Translate a legacy feedback mapping into the canonical receipt.

    Legacy numeric fields are retained only inside ``measured_impact``.  They
    are never part of the canonical receipt schema or processor API.
    """
    if not isinstance(legacy_payload, dict):
        raise TypeError("legacy outcome must be a dictionary")
    decision_id = str(legacy_payload.get("decision_id") or legacy_payload.get("id") or "")
    predicted_action = str(
        legacy_payload.get("predicted_action")
        or legacy_payload.get("recommended_action")
        or legacy_payload.get("action")
        or ""
    )
    actual_action = legacy_payload.get("actual_action") or legacy_payload.get("final_action")
    disposition = str(legacy_payload.get("human_disposition") or legacy_payload.get("disposition") or "").lower()
    if not disposition:
        disposition = "override" if actual_action and str(actual_action) != predicted_action else "confirm"
    correct_value = legacy_payload.get("correct", legacy_payload.get("is_correct"))
    correct = bool(correct_value) if correct_value is not None else disposition == "confirm"
    timestamp = _timestamp(legacy_payload.get("timestamp", legacy_payload.get("verified_at", legacy_payload.get("verified_at_epoch"))))
    impact = copy.deepcopy(legacy_payload.get("measured_impact") or {})
    if not isinstance(impact, dict):
        raise TypeError("measured_impact must be a dictionary when supplied")
    for key, value in legacy_payload.items():
        if key in {"reward", "reward_raw", "impact", "pnl", "pnl_bps", "recovered", "at_risk"}:  # adapter
            impact.setdefault(key, copy.deepcopy(value))
    return VerifiedOutcome.create(
        copilot=copilot,
        decision_id=decision_id,
        category=str(legacy_payload.get("category") or "unknown"),
        factor_vector=_factor_vector(legacy_payload.get("factor_vector", legacy_payload.get("factors", []))),
        predicted_action=predicted_action,
        human_disposition=disposition,
        override_action=None if disposition == "confirm" else str(actual_action or ""),
        override_reason=None if disposition == "confirm" else str(legacy_payload.get("override_reason") or legacy_payload.get("override_comment") or "legacy override"),
        correct=correct,
        measured_impact=impact or None,
        evidence_provenance=str(legacy_payload.get("evidence_provenance") or legacy_payload.get("provenance") or "legacy_adapter"),
        timestamp=timestamp,
    )


def outcome_to_reward(outcome: VerifiedOutcome) -> dict[str, Any]:
    """Provide a bounded legacy view without changing the canonical receipt."""
    impact = copy.deepcopy(outcome.measured_impact or {})
    result: dict[str, Any] = {
        "outcome_id": outcome.outcome_id,
        "decision_id": outcome.decision_id,
        "copilot": outcome.copilot,
        "category": outcome.category,
        "factor_vector": list(outcome.factor_vector),
        "predicted_action": outcome.predicted_action,
        "actual_action": outcome.override_action if outcome.human_disposition == "override" else outcome.predicted_action,
        "human_disposition": outcome.human_disposition,
        "override_reason": outcome.override_reason,
        "correct": outcome.correct,
        "is_correct": outcome.correct,
        "evidence_provenance": outcome.evidence_provenance,
        "timestamp": outcome.timestamp,
    }
    result.update(impact)
    return result


def _factor_vector(value: Any) -> list[float]:
    if isinstance(value, dict):
        return [float(item) for _, item in sorted(value.items())]
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value]
    return []


def _timestamp(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)
