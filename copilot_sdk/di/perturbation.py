"""Memory-only, demo-gated trust perturbations for the DI proof moment."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from time import monotonic
from typing import Any


SOURCE_FACTOR_MAP = {
    "airflow": "data_freshness",
    "dbt": "downstream_urgency",
    "snowflake": "source_reliability",
}
EXPIRY_SECONDS = 5 * 60


@dataclass
class _ActivePerturbation:
    source_name: str
    factor_name: str
    before_factors: dict[str, float]
    before_overall: float
    after_factors: dict[str, float]
    after_overall: float
    decisions_injected: int
    expires_at: float


class PerturbationError(ValueError):
    """A safe, user-correctable perturbation request error."""


class PerturbationActiveError(PerturbationError):
    """Raised when a second perturbation is requested before revert/expiry."""


class PerturbationService:
    """Apply a reversible trust overlay without mutating decision history."""

    def __init__(self, expiry_seconds: float = EXPIRY_SECONDS) -> None:
        self._expiry_seconds = expiry_seconds
        self._active: _ActivePerturbation | None = None

    def perturb(
        self,
        scorer: Any,
        *,
        source_name: str,
        perturbation: str,
        magnitude: float,
        decisions: int,
    ) -> dict[str, Any]:
        self._expire_if_needed()
        if self._active is not None:
            raise PerturbationActiveError("A perturbation is already active; revert it first")
        if perturbation != "degrade":
            raise PerturbationError("Only the degrade perturbation is supported")
        if not 0.1 <= magnitude <= 0.9:
            raise PerturbationError("magnitude must be between 0.1 and 0.9")
        if not 1 <= decisions <= 100:
            raise PerturbationError("decisions must be between 1 and 100")

        current = _fingerprint_factors(scorer)
        factor_name = _factor_for_source(source_name, current)
        before_factors = deepcopy(current)
        before_overall = _overall(before_factors)
        after_factors = deepcopy(before_factors)
        after_factors[factor_name] = round(
            max(0.0, before_factors[factor_name] * (1.0 - magnitude)), 6
        )
        after_overall = _overall(after_factors)
        self._active = _ActivePerturbation(
            source_name=source_name,
            factor_name=factor_name,
            before_factors=before_factors,
            before_overall=before_overall,
            after_factors=after_factors,
            after_overall=after_overall,
            decisions_injected=decisions,
            expires_at=monotonic() + self._expiry_seconds,
        )
        return self._result(self._active)

    def revert(self) -> dict[str, Any]:
        self._expire_if_needed()
        active = self._active
        if active is None:
            return {"restored": True, "active": False, "trust": {"overall": None, "factors": {}}}
        self._active = None
        return {
            "restored": True,
            "active": False,
            "trust": {"overall": active.before_overall, "factors": deepcopy(active.before_factors)},
        }

    def overlay(self, factors: list[dict[str, Any]]) -> dict[str, Any] | None:
        self._expire_if_needed()
        active = self._active
        if active is None:
            return None
        return {
            "overall": active.after_overall,
            "factors": deepcopy(active.after_factors),
            "source_name": active.source_name,
            "factor_name": active.factor_name,
            "decisions_injected": active.decisions_injected,
            "expires_in_seconds": max(0, round(active.expires_at - monotonic(), 2)),
        }

    def status(self) -> dict[str, Any]:
        self._expire_if_needed()
        active = self._active
        return {
            "enabled": True,
            "active": active is not None,
            "source_name": active.source_name if active else None,
            "factor_name": active.factor_name if active else None,
            "decisions_injected": active.decisions_injected if active else 0,
            "expires_in_seconds": max(0, round(active.expires_at - monotonic(), 2)) if active else None,
        }

    def _expire_if_needed(self) -> None:
        if self._active is not None and monotonic() >= self._active.expires_at:
            self._active = None

    @staticmethod
    def _result(active: _ActivePerturbation) -> dict[str, Any]:
        target_before = active.before_factors[active.factor_name]
        target_after = active.after_factors[active.factor_name]
        return {
            "before": {**active.before_factors, "overall": active.before_overall},
            "after": {**active.after_factors, "overall": active.after_overall},
            "delta": {
                active.factor_name: round(target_after - target_before, 6),
                "overall": round(active.after_overall - active.before_overall, 6),
            },
            "source_name": active.source_name,
            "factor_name": active.factor_name,
            "decisions_injected": active.decisions_injected,
            "revertable": True,
        }


def _factor_for_source(source_name: str, factors: dict[str, float]) -> str:
    normalized = source_name.strip().lower()
    factor_name = SOURCE_FACTOR_MAP.get(normalized, normalized)
    if factor_name not in factors:
        raise PerturbationError(f"Unknown perturbation source: {source_name}")
    return factor_name


def _fingerprint_factors(scorer: Any) -> dict[str, float]:
    try:
        fingerprint = scorer.fingerprint(persist=False)
    except TypeError:
        fingerprint = scorer.fingerprint()
    raw_factors = fingerprint.get("factors", []) if isinstance(fingerprint, dict) else getattr(fingerprint, "factors", [])
    factors: dict[str, float] = {}
    for raw in raw_factors or []:
        if isinstance(raw, dict):
            name = raw.get("name")
            weight = raw.get("weight", raw.get("dk_weight", 0.0))
        else:
            name = getattr(raw, "name", None)
            weight = getattr(raw, "weight", getattr(raw, "dk_weight", 0.0))
        if name:
            factors[str(name)] = max(0.0, min(1.0, float(weight)))
    if not factors:
        raise PerturbationError("scorer fingerprint has no factors")
    return factors


def _overall(factors: dict[str, float]) -> float:
    return round(sum(factors.values()) / len(factors), 6) if factors else 0.0
