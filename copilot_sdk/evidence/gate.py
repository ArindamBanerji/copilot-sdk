"""Context-aware evidence and claim gating.

This module is deliberately independent of any copilot domain.  Domain
adapters register claims; display and API layers ask whether a claim is
substantiated for a particular context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Mapping


class EvidenceTier(str, Enum):
    """Evidence quality used by the cross-copilot claim gate."""

    T_A = "analytical"
    T_S = "synthetic"
    T_O = "observed"
    T_R = "reproduced"


# Synthetic/modelled output is acceptable for a demo, while pilot and
# publication claims require operational or independently reproduced evidence.
DEFAULT_CONTEXT_MINIMUMS: dict[str, EvidenceTier] = {
    "demo": EvidenceTier.T_S,
    "pilot": EvidenceTier.T_O,
    "publication": EvidenceTier.T_R,
}

# T-A is a stronger analytical statement than an unverified simulation, but it
# is not an operational measurement.  This ordering lets analytical claims be
# shown in a demo without allowing them to pass a pilot gate.
_TIER_RANK: dict[EvidenceTier, int] = {
    EvidenceTier.T_S: 0,
    EvidenceTier.T_A: 1,
    EvidenceTier.T_O: 2,
    EvidenceTier.T_R: 3,
}

TIER_LABELS: dict[EvidenceTier, str] = {
    EvidenceTier.T_A: "analytical",
    EvidenceTier.T_S: "synthetic / modelled — not measured",
    EvidenceTier.T_O: "measured",
    EvidenceTier.T_R: "independently reproduced",
}


def _coerce_tier(value: EvidenceTier | str) -> EvidenceTier:
    if isinstance(value, EvidenceTier):
        return value
    try:
        return EvidenceTier(value)
    except ValueError as exc:
        raise ValueError(f"Unknown evidence tier: {value!r}") from exc


@dataclass(frozen=True)
class ClaimRecord:
    """A registered claim and the minimum tier for each presentation context."""

    claim_id: str
    description: str
    tier: EvidenceTier
    evidence_basis: str
    copilot: str
    context_minimum: Mapping[str, EvidenceTier | str] = field(
        default_factory=lambda: dict(DEFAULT_CONTEXT_MINIMUMS)
    )

    def __post_init__(self) -> None:
        for name, value in (
            ("claim_id", self.claim_id),
            ("description", self.description),
            ("evidence_basis", self.evidence_basis),
            ("copilot", self.copilot),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        object.__setattr__(self, "tier", _coerce_tier(self.tier))
        normalized: dict[str, EvidenceTier] = {}
        for context, minimum in dict(self.context_minimum).items():
            if not isinstance(context, str) or not context.strip():
                raise ValueError("context_minimum keys must be non-empty strings")
            normalized[context] = _coerce_tier(minimum)
        if not normalized:
            raise ValueError("context_minimum must contain at least one context")
        object.__setattr__(self, "context_minimum", normalized)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""

        return {
            "claim_id": self.claim_id,
            "description": self.description,
            "tier": self.tier.value,
            "evidence_basis": self.evidence_basis,
            "copilot": self.copilot,
            "context_minimum": {
                context: _coerce_tier(minimum).value
                for context, minimum in self.context_minimum.items()
            },
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ClaimRecord":
        """Build a record from :meth:`to_dict` output."""

        return cls(
            claim_id=str(value["claim_id"]),
            description=str(value["description"]),
            tier=_coerce_tier(value["tier"]),
            evidence_basis=str(value["evidence_basis"]),
            copilot=str(value["copilot"]),
            context_minimum=value.get("context_minimum", DEFAULT_CONTEXT_MINIMUMS),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, value: str) -> "ClaimRecord":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class GateResult:
    """The auditable result of evaluating one claim in one context."""

    passed: bool
    tier: EvidenceTier
    minimum: EvidenceTier
    label: str
    claim_id: str | None = None
    context: str | None = None
    error: str | None = None


class EvidenceGate:
    """Thread-safe registry and fail-closed context gate for claims."""

    def __init__(self) -> None:
        self._claims: dict[str, ClaimRecord] = {}
        self._lock = RLock()

    def register(self, claim: ClaimRecord) -> None:
        """Register or replace a claim with the same ID."""

        if not isinstance(claim, ClaimRecord):
            raise TypeError("claim must be a ClaimRecord")
        with self._lock:
            self._claims[claim.claim_id] = claim

    def check(self, claim_id: str, context: str) -> GateResult:
        """Evaluate a claim; unknown claims are denied rather than guessed."""

        with self._lock:
            claim = self._claims.get(claim_id)
        if claim is None:
            return GateResult(
                passed=False,
                tier=EvidenceTier.T_S,
                minimum=EvidenceTier.T_R,
                label="unregistered claim — blocked",
                claim_id=claim_id,
                context=context,
                error=f"Unknown claim_id: {claim_id}",
            )

        if context not in claim.context_minimum:
            raise ValueError(
                f"Unknown evidence context {context!r} for claim {claim_id!r}"
            )
        minimum = _coerce_tier(claim.context_minimum[context])
        passed = _TIER_RANK[claim.tier] >= _TIER_RANK[minimum]
        return GateResult(
            passed=passed,
            tier=claim.tier,
            minimum=minimum,
            label=TIER_LABELS[claim.tier],
            claim_id=claim_id,
            context=context,
        )

    def scan_all(self, context: str) -> list[GateResult]:
        """Return only claims that fail the requested context gate."""

        with self._lock:
            claim_ids = list(self._claims)
        return [
            result
            for claim_id in claim_ids
            if not (result := self.check(claim_id, context)).passed
        ]

    def get_label(self, claim_id: str) -> str:
        """Return the honest tier label, raising clearly for unknown claims."""

        with self._lock:
            claim = self._claims.get(claim_id)
        if claim is None:
            raise KeyError(f"Unknown claim_id: {claim_id}")
        return TIER_LABELS[claim.tier]
