"""Governed cross-domain transfer edges and provenance traversal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from copilot_sdk.conservation.global_gate import GlobalConservationGate
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


@dataclass(frozen=True)
class CrossCopilotFinding:
    amount: float
    currency: str
    source_domain: str
    target_domain: str
    source_decision_ids: tuple[str, ...]
    target_decision_ids: tuple[str, ...]
    provenance: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "financial_impact": self.amount,
            "currency": self.currency,
            "source_domain": self.source_domain,
            "target_domain": self.target_domain,
            "source_decision_ids": list(self.source_decision_ids),
            "target_decision_ids": list(self.target_decision_ids),
            "provenance": list(self.provenance),
        }


def create_transfer_pattern_edge(
    store: ProtocolV2GraphStore,
    *,
    pattern_id: str,
    source_domain: str,
    target_domain: str,
    similarity_score: float,
    factor_mapping: dict[str, Any] | None = None,
    source_decision_id: str | None = None,
    target_decision_id: str | None = None,
    pattern_type: str = "transfer_pattern",
    gate: GlobalConservationGate | None = None,
) -> dict[str, Any]:
    """Persist one governed TransferPattern edge through GraphStore."""
    if source_domain == target_domain:
        raise ValueError("TransferPattern edges require distinct domains")
    score = max(0.0, min(1.0, float(similarity_score)))
    conservation = (gate or GlobalConservationGate(store)).check_transfer(source_domain, target_domain)
    if not conservation["allowed"]:
        return {
            "status": "blocked",
            "source_domain": source_domain,
            "target_domain": target_domain,
            "similarity_score": score,
            "conservation": conservation,
        }
    metadata = {
        "similarity_score": score,
        "source_decision_id": source_decision_id,
        "target_decision_id": target_decision_id,
        "provenance": "live_graph_traversal",
        "global_conservation": conservation["global_conservation"],
    }
    store.write_transfer_pattern(
        pattern_id=pattern_id,
        source_domain=source_domain,
        target_domain=target_domain,
        pattern_type=pattern_type,
        factor_mapping=dict(factor_mapping or {}),
        confidence=score,
        validation_status="validated",
        conservation_status="GREEN",
        metadata=metadata,
    )
    return {
        "status": "created",
        "pattern_id": pattern_id,
        "source_domain": source_domain,
        "target_domain": target_domain,
        "similarity_score": score,
        "conservation": conservation,
    }


class CrossDomainTraversal:
    """Follow persisted transfer edges and return decision-level provenance."""

    def __init__(self, store: ProtocolV2GraphStore) -> None:
        self.store = store

    def insights(
        self,
        *,
        source_domain: str | None = None,
        target_domain: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        patterns = self.store.get_transfer_patterns(
            source_domain=source_domain,
            target_domain=target_domain,
        )[: max(0, int(limit))]
        result: list[dict[str, Any]] = []
        for pattern in patterns:
            metadata = pattern.get("metadata") if isinstance(pattern, dict) else {}
            metadata = metadata if isinstance(metadata, dict) else {}
            source = str(pattern.get("source_domain") or "")
            target = str(pattern.get("target_domain") or "")
            source_rows = self.store.get_all_decisions(source)
            target_rows = self.store.get_all_decisions(target)
            source_id = metadata.get("source_decision_id")
            target_id = metadata.get("target_decision_id")
            source_rows = [row for row in source_rows if not source_id or row.get("decision_id") == source_id]
            target_rows = [row for row in target_rows if not target_id or row.get("decision_id") == target_id]
            result.append(
                {
                    "transfer_pattern": dict(pattern),
                    "source_domain": source,
                    "target_domain": target,
                    "source_decisions": source_rows,
                    "target_decisions": target_rows,
                    "provenance": [
                        {"copilot": source, "decision_id": row.get("decision_id")} for row in source_rows
                    ]
                    + [
                        {"copilot": target, "decision_id": row.get("decision_id")} for row in target_rows
                    ],
                }
            )
        return result

    def traverse(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Compatibility alias for callers describing the operation as traversal."""
        return self.insights(**kwargs)

    def dollar_finding(self, *, pattern_id: str | None = None) -> CrossCopilotFinding | None:
        patterns = self.store.get_transfer_patterns()
        if pattern_id is not None:
            patterns = [pattern for pattern in patterns if pattern.get("pattern_id") == pattern_id]
        if not patterns:
            return None
        pattern = patterns[0]
        insights = self.insights(
            source_domain=str(pattern.get("source_domain")),
            target_domain=str(pattern.get("target_domain")),
            limit=1,
        )
        if not insights:
            return None
        insight = insights[0]
        source_rows = insight["source_decisions"]
        target_rows = insight["target_decisions"]
        rows = source_rows + target_rows
        amount = sum(_decision_impact(row) for row in rows)
        source_ids = tuple(str(row.get("decision_id")) for row in source_rows if row.get("decision_id"))
        target_ids = tuple(str(row.get("decision_id")) for row in target_rows if row.get("decision_id"))
        return CrossCopilotFinding(
            amount=float(amount),
            currency="USD",
            source_domain=str(pattern.get("source_domain")),
            target_domain=str(pattern.get("target_domain")),
            source_decision_ids=source_ids,
            target_decision_ids=target_ids,
            provenance=list(insight["provenance"]),
        )


def _decision_impact(decision: dict[str, Any]) -> float:
    for key in ("financial_impact", "dollar_impact", "impact", "value"):
        value = decision.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    metadata = decision.get("metadata")
    if isinstance(metadata, dict):
        return _decision_impact(metadata)
    return 0.0


def find_dollar_impact(
    store: ProtocolV2GraphStore,
    *,
    pattern_id: str | None = None,
) -> dict[str, Any] | None:
    finding = CrossDomainTraversal(store).dollar_finding(pattern_id=pattern_id)
    return None if finding is None else finding.to_dict()


# Descriptive aliases keep the public API discoverable without duplicating the
# governed implementation.
create_transfer_pattern = create_transfer_pattern_edge


def traverse_cross_domain(
    store: ProtocolV2GraphStore,
    *,
    source_domain: str | None = None,
    target_domain: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return CrossDomainTraversal(store).insights(
        source_domain=source_domain,
        target_domain=target_domain,
        limit=limit,
    )
