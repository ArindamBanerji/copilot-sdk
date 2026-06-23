"""Claim registry and promotion gate."""

from dataclasses import asdict, dataclass

from .tiers import ClaimProvenance, Tier


TIER_LANGUAGE = {
    Tier.ANALYTIC: (
        "Proven mathematically that the mechanism holds (conditions stated); "
        "magnitude measured on your data at pilot."
    ),
    Tier.SCRAPED: (
        "Populated day-zero with real external data, labeled context "
        "(\u2591\u2591) vs learned (\u2588\u2588) - it becomes yours as your team operates."
    ),
    Tier.ORACLE: (
        "The capability runs and the measurement instrument is validated to "
        "detect the effect - wired in and visible today."
    ),
    Tier.REAL: "Measured on your operations: <magnitude> (verified decisions).",
}


@dataclass
class PromotionEvent:
    claim_id: str
    from_tier: Tier
    to_tier: Tier
    evidence_ref: str
    approved_by: str
    date: str


class ClaimRegistry:
    """Gate: no claim silently migrates to REAL."""

    def __init__(self) -> None:
        self._claims: dict[str, ClaimProvenance] = {}
        self._history: list[PromotionEvent] = []

    def register(self, claim: ClaimProvenance) -> None:
        ok, why = claim.is_valid()
        if not ok:
            raise ValueError(f"FORBIDDEN (F-24): {why}  [{claim.claim_id}]")
        if claim.claim_id in self._claims:
            existing = self._claims[claim.claim_id]
            if existing != claim:
                raise ValueError(
                    f"CONFLICT: claim {claim.claim_id} already registered "
                    f"with tier={existing.tier.value}, cannot re-register "
                    f"with tier={claim.tier.value} without promote()"
                )
        self._claims[claim.claim_id] = claim

    def promote(self, ev: PromotionEvent) -> None:
        cur = self._claims[ev.claim_id]
        if ev.to_tier == Tier.REAL and not ev.evidence_ref:
            raise ValueError(
                "Promotion to REAL requires pilot evidence_ref "
                "(no silent migration)."
            )
        self._claims[ev.claim_id] = ClaimProvenance(
            **{**asdict(cur), "tier": ev.to_tier, "evidence_ref": ev.evidence_ref}
        )
        self._history.append(ev)

    def get(self, claim_id: str) -> ClaimProvenance | None:
        return self._claims.get(claim_id)

    def all_claims(self) -> list[ClaimProvenance]:
        return list(self._claims.values())

    def history(self) -> list[PromotionEvent]:
        return list(self._history)

    def sales_safe(self, claim_id: str) -> str:
        """What a claim may honestly say, given its tier."""
        return TIER_LANGUAGE[self._claims[claim_id].tier]
