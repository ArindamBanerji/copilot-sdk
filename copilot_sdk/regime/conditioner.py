"""Shared regime-conditioned scoring context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from copilot_sdk.regime.models import RegimeState
from copilot_sdk.regime.policy import RegimePolicy


@dataclass(frozen=True)
class ConditionedContext:
    """Observation-only regime context returned to a scoring consumer."""

    regime: str
    confidence: float
    indicators: dict[str, float]
    regime_scoped_accuracy: float | None
    abstention: bool
    rejection_count: int
    decision_count: int
    verified_count: int
    conditioning_enabled: bool

    @property
    def regime_accuracy(self) -> float | None:
        return self.regime_scoped_accuracy

    @property
    def abstention_recommended(self) -> bool:
        return self.abstention

    @property
    def regime_rejection_count(self) -> int:
        return self.rejection_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime,
            "confidence": self.confidence,
            "indicators": dict(self.indicators),
            "regime_scoped_accuracy": self.regime_scoped_accuracy,
            "regime_accuracy": self.regime_scoped_accuracy,
            "abstention": self.abstention,
            "abstention_recommended": self.abstention,
            "rejection_count": self.rejection_count,
            "regime_rejection_count": self.rejection_count,
            "decision_count": self.decision_count,
            "verified_count": self.verified_count,
            "conditioning_enabled": self.conditioning_enabled,
        }


class RegimeConditioner:
    """Attach verified, regime-scoped evidence to any scoring context."""

    def __init__(self, policy: RegimePolicy | None = None, *, domain: str | None = None):
        self.policy = policy or RegimePolicy()
        self.domain = _canonical_domain(domain) if domain else None

    def condition(
        self,
        scoring_context: Mapping[str, Any],
        regime_state: RegimeState,
        *,
        domain: str | None = None,
    ) -> ConditionedContext:
        decisions = (
            scoring_context.get("decisions")
            or scoring_context.get("verified_decisions")
            or scoring_context.get("history")
            or []
        )
        rows = decisions if isinstance(decisions, list) else []
        requested_domain = _canonical_domain(domain) if domain else self.domain
        matching = [
            row
            for row in rows
            if isinstance(row, dict)
            and (requested_domain is None or _row_domain(row) == requested_domain)
            and _row_regime(row) == regime_state.regime
        ]
        verified = [row for row in matching if _verified(row)]
        correct = sum(1 for row in verified if _correct(row))
        minimum = max(0, int(self.policy.abstention_minimum))
        enough = len(verified) >= minimum
        accuracy = round(correct / len(verified), 4) if enough and verified else None
        rejected = sum(1 for row in matching if _rejected(row))
        return ConditionedContext(
            regime=regime_state.regime,
            confidence=regime_state.confidence,
            indicators=dict(regime_state.indicators),
            regime_scoped_accuracy=accuracy,
            abstention=not self.policy.conditioning_enabled or not enough,
            rejection_count=rejected,
            decision_count=len(matching),
            verified_count=len(verified),
            conditioning_enabled=self.policy.conditioning_enabled,
        )


def _row_regime(row: dict[str, Any]) -> str:
    for key in ("regime", "current_regime"):
        if row.get(key):
            return _canonical(str(row[key]))
    for key in ("metadata", "context", "regime_metadata"):
        value = row.get(key)
        if isinstance(value, dict):
            for candidate in ("regime", "current_regime"):
                if value.get(candidate):
                    return _canonical(str(value[candidate]))
    return "unknown"


def _row_domain(row: dict[str, Any]) -> str:
    """Return the explicitly stored copilot domain for a decision row."""
    for key in ("domain", "copilot", "copilot_domain"):
        value = row.get(key)
        if value:
            return _canonical_domain(str(value))
    for key in ("metadata", "context", "regime_metadata"):
        value = row.get(key)
        if isinstance(value, dict):
            for candidate in ("domain", "copilot", "copilot_domain"):
                if value.get(candidate):
                    return _canonical_domain(str(value[candidate]))
    return "unknown"


def _canonical(value: str) -> str:
    value = value.strip().lower()
    return "ranging" if value in {"choppy", "range"} else value


def _canonical_domain(value: str) -> str:
    return value.strip().lower()


def _verified(row: dict[str, Any]) -> bool:
    return bool(row.get("verified") or row.get("verified_at") or row.get("outcome_correct") is not None or row.get("is_correct") is not None)


def _correct(row: dict[str, Any]) -> bool:
    return bool(row.get("outcome_correct", row.get("is_correct", False)))


def _rejected(row: dict[str, Any]) -> bool:
    return bool(row.get("rejected") or row.get("regime_rejected") or row.get("abstained"))
