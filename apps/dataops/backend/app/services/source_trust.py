"""Read-only presentation of factor DK trust; unmapped pipelines stay neutral."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer

FACTOR_TO_SOURCE = {
    "impact_scope": "cross_system",
    "source_reliability": "source_direct",
    "recurrence_frequency": "monitoring",
    "downstream_urgency": "consumer_systems",
    "data_freshness": "ingestion_pipeline",
    "business_criticality": "business_context",
}

PIPELINE_SYSTEMS = (
    "sap_mm_api", "erp_connector", "sftp_daily", "salesforce_api",
    "warehouse_etl", "data_lake_ingestion", "api_gateway",
    "batch_processor", "streaming_pipeline",
)


@dataclass
class SourceTrust:
    source: str
    trust: float
    status: str
    verified: int
    trend: str
    dk_contribution: dict[str, float] = field(default_factory=dict)
    total_verified: int = 0


def compute_source_trust(
    scorer: CompoundingScorer, graph_store: GraphStore, domain: str,
) -> list[SourceTrust]:
    """Average category DK weights and normalize by the strongest factor.

    This is relative factor precision, not a calibrated reliability probability.
    Normalization follows scoring.fingerprint. Pipeline IDs have no established
    factor mapping, so they retain neutral trust even when they have outcomes.
    Trends compare current and earlier *fingerprints*, using the same estimator
    on both sides; fingerprint weights are not interchangeable with DK tensors.
    No fingerprint or graph artifact is persisted by this read.
    """
    decisions = graph_store.get_verified_decisions(domain)
    total = len(decisions)
    fingerprint = scorer.fingerprint(persist=False)
    names = [factor.name for factor in fingerprint.factors]
    normalized = _normalized_weights(scorer.get_dk_weights(), names) if total else {}
    baseline = _previous_factors(graph_store, domain, fingerprint.decisions_analyzed) if normalized else {}
    current = {factor.name: factor.weight for factor in fingerprint.factors}
    decision_factors = [_decision_factors(decision, names) for decision in decisions]
    results: list[SourceTrust] = []
    for factor, source in FACTOR_TO_SOURCE.items():
        verified = sum(factor in present for present in decision_factors)
        available = factor in normalized and verified > 0
        trust = round(normalized[factor], 3) if available else 0.5
        trend = "stable"
        if available and factor in baseline and fingerprint.decisions_analyzed >= 5:
            delta = round(current[factor] - baseline[factor], 3)
            trend = "improving" if delta > 0 else "declining" if delta < 0 else "stable"
        results.append(SourceTrust(
            source=source, trust=trust, status=_status(trust), verified=verified,
            trend=trend, dk_contribution={factor: trust} if available else {},
            total_verified=total,
        ))
    for source in PIPELINE_SYSTEMS:
        verified = sum(1 for decision in decisions if source in _decision_sources(decision))
        results.append(SourceTrust(source, 0.5, "AMBER", verified, "stable", total_verified=total))
    return sorted(results, key=lambda row: (-row.trust, row.source))


def _decision_factors(decision: dict[str, Any], names: list[str]) -> set[str]:
    """Recognize both named in-memory factors and canonical AGE factor vectors."""
    factors = decision.get("factors")
    if isinstance(factors, dict) and factors:
        return set(factors) & set(names)
    vector = decision.get("factor_vector")
    if not isinstance(vector, (list, tuple)) or len(vector) != len(names):
        return set()
    metadata = decision.get("metadata")
    recorded_names = decision.get("factor_names")
    if recorded_names is None and isinstance(metadata, dict):
        recorded_names = metadata.get("factor_names")
    if recorded_names is not None:
        if (not isinstance(recorded_names, (list, tuple))
                or len(recorded_names) != len(vector)
                or not all(isinstance(name, str) for name in recorded_names)):
            return set()
        return set(recorded_names) & set(names)
    # Legacy vectors use preset order, as in the scorer's fingerprint reader.
    return set(names)


def _normalized_weights(raw: object, names: list[str]) -> dict[str, float]:
    if raw is None or not names:
        return {}
    try:
        weights = np.asarray(raw, dtype=float)
    except (TypeError, ValueError):
        return {}
    if (weights.ndim != 2 or weights.shape[0] == 0 or weights.shape[1] != len(names)
            or not np.isfinite(weights).all() or (weights < 0).any()):
        return {}
    # Scale before averaging to avoid overflow for finite large weights.
    maximum = float(weights.max())
    if maximum <= 0:
        return {}
    means = (weights / maximum).mean(axis=0)
    normalized = means / float(means.max())
    return {name: float(value) for name, value in zip(names, normalized)}


def _previous_factors(store: GraphStore, domain: str, count: int) -> dict[str, float]:
    list_history = getattr(store, "list_fingerprints", None)
    if not callable(list_history):
        return {}
    eligible: list[tuple[int, dict[str, float]]] = []
    for row in list_history(domain=domain):
        stats = row.get("factor_stats") or row.get("fingerprint") or {}
        if not isinstance(stats, dict) or row.get("domain", domain) != domain:
            continue
        old_count = stats.get("decisions_analyzed", row.get("window"))
        if not isinstance(old_count, int) or not 5 <= old_count < count:
            continue
        factors = stats.get("factors", [])
        if not isinstance(factors, list):
            continue
        values: dict[str, float] = {}
        for item in factors:
            if not isinstance(item, dict):
                continue
            name, value = item.get("name"), item.get("weight")
            if (isinstance(name, str) and isinstance(value, (int, float))
                    and not isinstance(value, bool) and np.isfinite(value) and 0 <= value <= 1):
                values[name] = float(value)
        eligible.append((old_count, values))
    return max(eligible, key=lambda item: item[0])[1] if eligible else {}


def _decision_sources(decision: dict[str, Any]) -> set[str]:
    sources: set[str] = set()
    for container in (decision, decision.get("metadata"), decision.get("context")):
        if not isinstance(container, dict):
            continue
        for key in ("system", "system_name", "source_system", "system_id"):
            value = container.get(key)
            if isinstance(value, str):
                sources.add(value)
    return sources


def _status(trust: float) -> str:
    return "GREEN" if trust >= 0.7 else "AMBER" if trust >= 0.4 else "RED"
