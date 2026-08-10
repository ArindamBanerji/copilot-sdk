"""Conservative confidence calculation for DI-3 answers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from copilot_sdk.di.query_models import SourceUsage


class ConfidenceResult(BaseModel):
    score: float | None
    label: str
    warnings: list[str] = Field(default_factory=list)
    adjustments: list[str] = Field(default_factory=list)


def tier_to_score(tier: int) -> float:
    """Convert the DI-1 ordinal trust tier to the query score scale."""

    return {1: 1.0, 2: 0.66, 3: 0.33}.get(int(tier), 0.5)


def compute_confidence(
    source_usage: list[SourceUsage],
    profiles: dict[str, Any],
    *,
    data_as_of: datetime | None = None,
    now: datetime | None = None,
    unmatched_records: int = 0,
    records_scanned: int = 0,
    disagreement_ratio: float | None = None,
    active_alerts: dict[str, Any] | list[Any] | None = None,
    minimum_sample: int = 10,
) -> ConfidenceResult:
    """Compute a bounded, trust-weighted confidence score.

    Missing trust uses a conservative evidence-only baseline rather than
    collapsing a governed result to zero confidence.
    """

    if not source_usage or records_scanned <= 0:
        return ConfidenceResult(
            score=None,
            label="insufficient",
            warnings=["No verified source evidence is available."],
        )

    total_weight = sum(max(float(item.contribution), 0.0) for item in source_usage)
    if total_weight <= 0:
        total_weight = float(sum(max(item.records_used, 0) for item in source_usage) or 1)

    available_trusts: list[float] = []
    for item in source_usage:
        value = _trust_value(profiles.get(item.source_id))
        if value is not None:
            available_trusts.append(max(0.0, min(1.0, value)))

    score = 0.0
    warnings: list[str] = []
    adjustments: list[str] = []
    if not available_trusts:
        evidence_baseline = min(1.0, records_scanned / 100.0) * 0.5
        score = evidence_baseline * 0.5
        adjustments.append("missing trust: conservative evidence baseline")
    for item in source_usage:
        profile = profiles.get(item.source_id)
        trust = _trust(profile)
        weight = max(float(item.contribution), 0.0) / total_weight
        if available_trusts:
            score += weight * trust
        if profile is None or _trust_value(profile) is None:
            warnings.append(f"Trust is unavailable for {item.source_id}.")
        freshness_hours = _freshness_hours(profile, data_as_of=data_as_of, now=now)
        if freshness_hours is not None and freshness_hours > 24:
            score -= 0.10 * weight
            adjustments.append(f"{item.source_id}: freshness penalty -10pp")
            warnings.append(f"{item.source_id} data is {freshness_hours:.0f} hours old.")

    if active_alerts:
        for source_id, alert in _alert_items(active_alerts):
            severity = str(_value(alert, "severity", "level", default=alert)).upper()
            if severity == "RED":
                score -= 0.15
                adjustments.append(f"{source_id}: RED alert penalty -15pp")
                warnings.append(f"{source_id} has an active RED quality alert.")
            elif severity == "AMBER":
                score -= 0.05
                adjustments.append(f"{source_id}: AMBER alert penalty -5pp")
                warnings.append(f"{source_id} has an active AMBER quality alert.")

    if disagreement_ratio is not None and float(disagreement_ratio) > 0.05:
        score -= 0.10
        adjustments.append("source disagreement penalty -10pp")
        warnings.append(f"Sources disagree by {float(disagreement_ratio):.1%}.")

    if unmatched_records > 0:
        penalty = min(0.25, unmatched_records / max(records_scanned, 1))
        score -= penalty
        adjustments.append(f"unmatched records penalty -{penalty:.0%}")
        warnings.append(f"{unmatched_records} records were unmatched.")

    if records_scanned < minimum_sample:
        score -= 0.10
        adjustments.append("small evidence set penalty -10pp")
        warnings.append(f"Only {records_scanned} records support this result.")

    bounded = max(0.0, min(1.0, score))
    label = confidence_label(bounded, records_scanned=records_scanned, minimum_sample=minimum_sample)
    return ConfidenceResult(score=bounded, label=label, warnings=_dedupe(warnings), adjustments=adjustments)


def confidence_label(score: float, *, records_scanned: int = 0, minimum_sample: int = 10) -> str:
    """Return the public confidence label using the DI-3 thresholds."""

    if records_scanned < minimum_sample:
        return "low" if score >= 0.2 else "insufficient"
    if score > 0.8:
        return "high"
    if score >= 0.5:
        return "moderate"
    if score >= 0.2:
        return "low"
    return "insufficient"


def _trust(profile: Any) -> float:
    value = _trust_value(profile)
    if value is None:
        return 0.0
    return max(0.0, min(1.0, value))


def _trust_value(profile: Any) -> float | None:
    if profile is None:
        return None
    value = _value(profile, "trust", "trust_score", "dk_weight", "overall_trust")
    try:
        if value is not None:
            return float(value)
        tier = _value(profile, "trust_tier")
        return tier_to_score(int(tier)) if tier is not None else None
    except (TypeError, ValueError):
        return None


def _freshness_hours(profile: Any, *, data_as_of: datetime | None, now: datetime | None) -> float | None:
    explicit = _value(profile, "freshness_hours", "age_hours")
    if explicit is not None:
        try:
            return max(0.0, float(explicit))
        except (TypeError, ValueError):
            pass
    if data_as_of is None:
        return None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    timestamp = data_as_of if data_as_of.tzinfo else data_as_of.replace(tzinfo=timezone.utc)
    return max(0.0, (current - timestamp).total_seconds() / 3600)


def _alert_items(alerts: dict[str, Any] | list[Any]) -> list[tuple[str, Any]]:
    if isinstance(alerts, dict):
        return [(str(key), value) for key, value in alerts.items()]
    return [(str(_value(item, "source_id", "source", default="source")), item) for item in alerts]


def _value(item: Any, *names: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        for name in names:
            if name in item:
                return item[name]
    else:
        for name in names:
            value = getattr(item, name, None)
            if value is not None:
                return value
    return default


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
