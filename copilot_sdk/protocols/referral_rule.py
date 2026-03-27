"""
ReferralRule Protocol — domain-specific VETO rules.
REFER is a hard VETO — cannot be overridden by confidence gate.
Rules are deterministic, configurable, auditable.
"""
from typing import Protocol, Literal


class ReferralRule(Protocol):
    rule_id:  str
    priority: int

    def evaluate(self, context: dict) -> dict:
        """
        Returns {"decision": "REFER" | "PASS", "reason": str}.
        REFER is a hard VETO.
        """
        ...
