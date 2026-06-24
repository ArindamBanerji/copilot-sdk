"""Cross-system entity correlation for advisory discovery.

CrossSystemCorrelator is separate from CombinationDiscoveryEngine (P43).
P43 discovers factor-pair combinations within a single domain. This module
discovers entity-level correlations across domains. Different granularity:
P43 = factor pairs, P90 = entity signals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class CrossSystemCorrelator:
    """Find shared entities across copilot decision histories.

    Advisory only. This module never mutates scorer, graph, or workflow state.
    """

    def scan(
        self,
        domain_decisions: dict[str, list[dict[str, Any]]],
        min_correlation: float = 0.5,
    ) -> list[dict[str, Any]]:
        threshold = max(0.0, min(float(min_correlation), 1.0))
        by_entity: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for domain, decisions in dict(domain_decisions or {}).items():
            for decision in list(decisions or []):
                entity_id = _entity_id(decision)
                if entity_id:
                    by_entity[entity_id].append((str(domain), dict(decision)))

        alerts: list[dict[str, Any]] = []
        for entity_id, rows in sorted(by_entity.items()):
            domains = sorted({domain for domain, _decision in rows})
            if len(domains) < 2:
                continue
            for left_index, domain_a in enumerate(domains):
                for domain_b in domains[left_index + 1 :]:
                    left = [decision for domain, decision in rows if domain == domain_a]
                    right = [decision for domain, decision in rows if domain == domain_b]
                    correlation = _correlation(left, right)
                    if correlation < threshold:
                        continue
                    alerts.append(
                        self.generate_alert(
                            entity_id,
                            domain_a,
                            domain_b,
                            _signal(left[0]),
                            _signal(right[0]),
                            correlation,
                        )
                    )
        return alerts

    def generate_alert(
        self,
        entity_id: str,
        domain_a: str,
        domain_b: str,
        signal_a: str,
        signal_b: str,
        correlation: float,
    ) -> dict[str, Any]:
        return {
            "alert_id": f"XS-{_slug(entity_id)}-{_slug(domain_a)}-{_slug(domain_b)}",
            "entity_id": str(entity_id),
            "domains": [str(domain_a), str(domain_b)],
            "source_signal": str(signal_a),
            "related_signal": str(signal_b),
            "correlation": round(max(0.0, min(float(correlation), 1.0)), 3),
            "advisory": True,
            "timeline": [
                {"domain": str(domain_a), "signal": str(signal_a)},
                {"domain": str(domain_b), "signal": str(signal_b)},
            ],
            "title": f"{domain_a} and {domain_b} share entity {entity_id}",
            "description": (
                f"{domain_a} detected {signal_a}. "
                f"{domain_b} detected {signal_b}. Advisory only."
            ),
        }


def _entity_id(decision: dict[str, Any]) -> str:
    for key in ("entity_id", "supplier_id", "asset_id", "user_id", "entity"):
        value = decision.get(key)
        if value:
            return str(value)
    metadata = decision.get("metadata")
    if isinstance(metadata, dict):
        for key in ("entity_id", "supplier_id", "asset_id", "user_id", "entity"):
            value = metadata.get(key)
            if value:
                return str(value)
    return ""


def _signal(decision: dict[str, Any]) -> str:
    for key in ("signal", "category", "alert_type", "reason"):
        value = decision.get(key)
        if value:
            return str(value)
    return "related_signal"


def _score(decision: dict[str, Any]) -> float:
    for key in ("score", "confidence", "severity", "novelty_rate", "risk"):
        value = decision.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.5


def _correlation(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> float:
    left_score = sum(_score(item) for item in left) / max(len(left), 1)
    right_score = sum(_score(item) for item in right) / max(len(right), 1)
    return 1.0 - min(abs(left_score - right_score), 1.0)


def _slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value)).strip("-") or "x"
