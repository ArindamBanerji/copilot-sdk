"""Substantiation tiers for commercial claims."""

from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    ANALYTIC = "analytic"
    SCRAPED = "scraped_external"
    ORACLE = "oracle_synthetic"
    REAL = "real_measured"


_MAGNITUDE_OK = {Tier.REAL}


@dataclass(frozen=True)
class ClaimProvenance:
    """Every commercial claim tagged with its evidence tier."""

    claim_id: str
    text: str
    tier: Tier
    evidence_ref: str
    is_magnitude_claim: bool
    copilot: str
    feature: str

    def is_valid(self) -> tuple[bool, str]:
        """META-4 line: magnitude claims require REAL tier."""
        if self.is_magnitude_claim and self.tier not in _MAGNITUDE_OK:
            return False, (
                f"Magnitude claim substantiated only by {self.tier.value}; "
                "customer-specific magnitude requires REAL (META-4 line)."
            )
        return True, "ok"
