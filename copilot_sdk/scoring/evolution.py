"""Scorer parameter evolution without mutating scorer internals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from copilot_sdk.scoring.evolution_config import EvolutionBounds, bounds_for_domain


EVOLVABLE_PARAMETERS = {
    "eta_confirm",
    "eta_override",
    "penalty_ratio",
    "temperature",
}


@dataclass
class EvolutionProposal:
    """One auditable scorer parameter proposal."""

    parameter: str
    current_value: float
    proposed_value: float
    evidence: str
    conservation_state: str
    approved: bool
    applied: bool = False
    rolled_back: bool = False
    proposal_id: str = ""
    created_at: str = ""
    applied_at: str | None = None
    original_value: float | None = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = f"proposal-{uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = _now()
        if self.original_value is None:
            self.original_value = float(self.current_value)


class ScorerEvolution:
    """Propose bounded scorer config changes from verified evidence."""

    def __init__(
        self,
        domain_preset: str,
        bounds: EvolutionBounds | None = None,
        min_decisions: int = 500,
    ):
        self._domain = str(domain_preset)
        self._bounds = bounds or bounds_for_domain(self._domain)
        self._min_decisions = int(min_decisions)
        self._log: list[EvolutionProposal] = []
        self._applied: dict[str, EvolutionProposal] = {}

    @property
    def bounds(self) -> EvolutionBounds:
        return self._bounds

    def evaluate(
        self,
        decisions: list[dict[str, Any]],
        current_params: dict[str, Any],
        conservation_state: str,
    ) -> list[EvolutionProposal]:
        """Return proposals when conservation is GREEN and evidence is sufficient."""

        state = _normalize_state(conservation_state)
        if state != "GREEN":
            return []
        verified = [_normalize_decision(decision) for decision in decisions]
        if len(verified) < self._min_decisions:
            return []

        proposals: list[EvolutionProposal] = []
        accuracy = _accuracy(verified)
        recent_accuracy = _accuracy(verified[-200:])
        previous_accuracy = _accuracy(verified[-400:-200]) if len(verified) >= 400 else accuracy
        override_rate = _override_rate(verified)

        if accuracy >= 0.85:
            current = _param(current_params, "eta_confirm", 0.05)
            proposed = self._clamp("eta_confirm", current * 0.90)
            proposals.append(self._proposal(
                "eta_confirm",
                current,
                proposed,
                f"accuracy stable at {accuracy:.1%} for {len(verified)} decisions",
                state,
            ))
        if recent_accuracy < previous_accuracy - 0.05:
            current = _param(current_params, "eta_confirm", 0.05)
            proposed = self._clamp("eta_confirm", current * 1.20)
            proposals.append(self._proposal(
                "eta_confirm",
                current,
                proposed,
                f"accuracy declined from {previous_accuracy:.1%} to {recent_accuracy:.1%}",
                state,
            ))
        if override_rate > 0.30:
            current = _param(current_params, "penalty_ratio", 10.0)
            proposed = self._clamp("penalty_ratio", current * 0.90)
            proposals.append(self._proposal(
                "penalty_ratio",
                current,
                proposed,
                f"override rate {override_rate:.1%} exceeds 30%",
                state,
            ))
        if override_rate < 0.10 and accuracy > 0.90:
            current = _param(current_params, "penalty_ratio", 10.0)
            proposed = self._clamp("penalty_ratio", current * 1.10)
            proposals.append(self._proposal(
                "penalty_ratio",
                current,
                proposed,
                f"override rate {override_rate:.1%} with accuracy {accuracy:.1%}",
                state,
            ))

        self._log.extend(proposals)
        return proposals

    def apply(
        self,
        proposal: EvolutionProposal,
        config: dict[str, Any],
        current_conservation_state: str,
    ) -> bool:
        """Apply an approved bounded proposal to a config dict only."""

        if _normalize_state(current_conservation_state) != "GREEN":
            proposal.approved = False
            self._remember(proposal)
            return False
        if proposal.parameter not in EVOLVABLE_PARAMETERS:
            raise ValueError(f"Unsupported evolution parameter: {proposal.parameter}")
        bounded_value = self._clamp(proposal.parameter, float(proposal.proposed_value))
        proposal.proposed_value = bounded_value
        proposal.original_value = _param(config, proposal.parameter, proposal.current_value)
        proposal.current_value = float(proposal.original_value)
        proposal.approved = True
        proposal.applied = True
        proposal.applied_at = _now()
        config[proposal.parameter] = bounded_value
        self._applied[proposal.parameter] = proposal
        self._remember(proposal)
        return True

    def apply_by_id(
        self,
        proposal_id: str,
        config: dict[str, Any],
        current_conservation_state: str,
    ) -> bool:
        proposal = self.find_proposal(proposal_id)
        if proposal is None:
            return False
        return self.apply(proposal, config, current_conservation_state)

    def rollback(self, parameter: str, config: dict[str, Any]) -> bool:
        """Restore the last applied value for a parameter."""

        proposal = self._applied.get(parameter)
        if proposal is None or proposal.original_value is None:
            return False
        config[parameter] = float(proposal.original_value)
        proposal.rolled_back = True
        proposal.applied = False
        self._applied.pop(parameter, None)
        self._remember(proposal)
        return True

    def rollback_on_conservation(self, conservation_state: str, config: dict[str, Any]) -> list[str]:
        """Rollback all active adjustments when conservation is not GREEN."""

        if _normalize_state(conservation_state) == "GREEN":
            return []
        rolled_back: list[str] = []
        for parameter in list(self._applied):
            if self.rollback(parameter, config):
                rolled_back.append(parameter)
        return rolled_back

    def evolution_log(self) -> list[dict[str, Any]]:
        return [asdict(proposal) for proposal in self._log]

    def active_adjustments(self) -> dict[str, dict[str, Any]]:
        active: dict[str, dict[str, Any]] = {}
        for parameter, proposal in self._applied.items():
            active[parameter] = {
                "original": proposal.original_value,
                "adjusted": proposal.proposed_value,
                "evidence": proposal.evidence,
                "applied_at": proposal.applied_at,
                "proposal_id": proposal.proposal_id,
            }
        return active

    def bounds_dict(self) -> dict[str, Any]:
        return asdict(self._bounds)

    def find_proposal(self, proposal_id: str) -> EvolutionProposal | None:
        return self._find(proposal_id)

    def _proposal(
        self,
        parameter: str,
        current_value: float,
        proposed_value: float,
        evidence: str,
        conservation_state: str,
    ) -> EvolutionProposal:
        return EvolutionProposal(
            parameter=parameter,
            current_value=float(current_value),
            proposed_value=float(proposed_value),
            evidence=evidence,
            conservation_state=conservation_state,
            approved=True,
        )

    def _clamp(self, parameter: str, value: float) -> float:
        low, high = _bounds_for_parameter(self._bounds, parameter)
        return max(low, min(float(value), high))

    def _find(self, proposal_id: str) -> EvolutionProposal | None:
        for proposal in reversed(self._log):
            if proposal.proposal_id == proposal_id:
                return proposal
        return None

    def _remember(self, proposal: EvolutionProposal) -> None:
        if proposal not in self._log:
            self._log.append(proposal)


def _bounds_for_parameter(bounds: EvolutionBounds, parameter: str) -> tuple[float, float]:
    if parameter == "penalty_ratio":
        return bounds.penalty_ratio_range
    if parameter == "eta_confirm":
        return bounds.eta_confirm
    if parameter == "eta_override":
        return bounds.eta_override
    if parameter == "temperature":
        return bounds.temperature
    raise ValueError(f"Unsupported evolution parameter: {parameter}")


def _normalize_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return dict(decision)


def _accuracy(decisions: list[dict[str, Any]]) -> float:
    if not decisions:
        return 0.0
    correct = sum(1 for decision in decisions if _is_correct(decision))
    return correct / len(decisions)


def _override_rate(decisions: list[dict[str, Any]]) -> float:
    if not decisions:
        return 0.0
    overrides = sum(1 for decision in decisions if _is_override(decision))
    return overrides / len(decisions)


def _is_correct(decision: dict[str, Any]) -> bool:
    if "correct" in decision:
        return bool(decision["correct"])
    if "is_correct" in decision:
        return bool(decision["is_correct"])
    outcome = str(decision.get("outcome") or "").lower()
    return outcome == "confirmed"


def _is_override(decision: dict[str, Any]) -> bool:
    if "was_override" in decision:
        return bool(decision["was_override"])
    actual = decision.get("actual_action")
    recommended = decision.get("recommended_action") or decision.get("action")
    if actual is None or recommended is None:
        return False
    return str(actual) != str(recommended)


def _param(config: dict[str, Any], parameter: str, default: float) -> float:
    try:
        return float(config.get(parameter, default))
    except (TypeError, ValueError):
        return float(default)


def _normalize_state(conservation_state: str) -> str:
    return str(conservation_state or "").strip().upper()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
