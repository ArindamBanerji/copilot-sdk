"""Global conservation for cross-copilot transfers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from copilot_sdk.config.domains import ALL_COPILOT_DOMAINS
from copilot_sdk.evolution.conservation_contract import evaluate_conservation_safety
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


@dataclass(frozen=True)
class GlobalConservationSnapshot:
    status: str
    domains: tuple[str, ...]
    statuses: dict[str, str]
    theta_min_total: float
    theta_min_average: float
    verified_count_total: int
    computed_at: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "domains": list(self.domains),
            "statuses": dict(self.statuses),
            "theta_min_total": self.theta_min_total,
            "theta_min": self.theta_min_total,
            "theta_min_average": self.theta_min_average,
            "verified_count_total": self.verified_count_total,
            "computed_at": self.computed_at,
        }


class GlobalConservationGate:
    """Read live conservation snapshots and gate only cross-domain writes."""

    def __init__(self, store: ProtocolV2GraphStore, domains: Iterable[str] | None = None) -> None:
        self.store = store
        self.domains = tuple(dict.fromkeys(str(domain) for domain in (domains or ALL_COPILOT_DOMAINS)))

    def snapshot(self) -> GlobalConservationSnapshot:
        rows = self.store.get_latest_conservation_statuses(domains=list(self.domains))
        by_domain = {
            str(row.get("domain")): row
            for row in rows
            if isinstance(row, dict) and row.get("domain")
        }
        statuses = {
            domain: str(by_domain.get(domain, {}).get("status") or "UNKNOWN").upper()
            for domain in self.domains
        }
        decisions = [evaluate_conservation_safety(value) for value in statuses.values()]
        if decisions and all(decision.promotion_allowed for decision in decisions):
            status = "GREEN"
        elif any(not decision.available for decision in decisions):
            status = "CONSERVATION_UNAVAILABLE"
        elif any(decision.status == "RED" for decision in decisions):
            status = "RED"
        else:
            status = "AMBER"
        thresholds = [float(str(by_domain[domain].get("theta_min") or 0.0)) for domain in by_domain]
        return GlobalConservationSnapshot(
            status=status,
            domains=self.domains,
            statuses=statuses,
            theta_min_total=sum(thresholds),
            theta_min_average=sum(thresholds) / len(thresholds) if thresholds else 0.0,
            verified_count_total=sum(int(by_domain[domain].get("verified_count") or 0) for domain in by_domain),
            computed_at=max(
                (
                    float(str(row.get("computed_at")))
                    for row in by_domain.values()
                    if row.get("computed_at") is not None
                ),
                default=None,
            ),
        )

    def transfer_allowed(self, source_domain: str, target_domain: str) -> bool:
        snapshot = self.snapshot()
        return self._transfer_allowed_from_snapshot(
            source_domain,
            target_domain,
            snapshot,
        )

    @staticmethod
    def _transfer_allowed_from_snapshot(
        source_domain: str,
        target_domain: str,
        snapshot: GlobalConservationSnapshot,
    ) -> bool:
        if source_domain == target_domain:
            return False
        return bool(
            evaluate_conservation_safety(snapshot.to_dict()).promotion_allowed
            and evaluate_conservation_safety(
                snapshot.statuses.get(str(source_domain))
            ).promotion_allowed
            and evaluate_conservation_safety(
                snapshot.statuses.get(str(target_domain))
            ).promotion_allowed
        )

    def status(self) -> str:
        """Return the current aggregate status from live graph snapshots."""
        return self.snapshot().status

    def global_status(self) -> str:
        """Compatibility name for callers asking for the global gate state."""
        return self.status()

    def global_theta_min(self) -> float:
        """Return the aggregate live threshold across configured domains."""
        return self.snapshot().theta_min_total

    def check_transfer(self, source_domain: str, target_domain: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        allowed = self._transfer_allowed_from_snapshot(
            source_domain,
            target_domain,
            snapshot,
        )
        return {
            "allowed": allowed,
            "source_domain": str(source_domain),
            "target_domain": str(target_domain),
            "global_conservation": snapshot.to_dict(),
            "reason": "global_conservation_green" if allowed else "global_conservation_not_green",
        }


GlobalConservation = GlobalConservationGate
