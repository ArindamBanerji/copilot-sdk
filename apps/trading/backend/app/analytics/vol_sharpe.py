"""Risk-adjusted decision-quality analytics by market regime."""

from __future__ import annotations

import math
from statistics import mean, stdev
from typing import Any

from ci_trading.quant import block_bootstrap_mean_se


MIN_DECISIONS = 30
MIN_DECISIONS_PER_CLUSTER = 10
EPS = 1e-12


def compute_clustering_adjusted_sharpe(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute raw and bootstrap-adjusted quality ratios from decision outcomes."""
    quality = [_quality_value(decision) for decision in decisions]
    q = [value for value in quality if value is not None]
    n = len(q)
    if n < 2:
        return {
            "naive_quality_score": None,
            "quality_adjusted_score": None,
            "inflation": None,
            "n_decisions": n,
            "provenance": "accumulating",
            "substantiation": "T-R" if n >= MIN_DECISIONS else "T-O",
            "day_zero": True,
            "decisions_until_measured": max(0, MIN_DECISIONS - n),
            **_cluster_payload(decisions),
            "status": "accumulating",
            "overall_quality_score": None,
            "overall_quality_adjusted": None,
            "source": "live",
            "analytics_provenance": "accumulating",
        }

    sigma = stdev(q)
    naive = mean(q) / sigma if sigma > EPS else 0.0
    diagnostic = block_bootstrap_mean_se(q, block=20, n_boot=300, seed=0)
    iid_se = diagnostic.iid_se if math.isfinite(diagnostic.iid_se) else 0.0
    block_se = diagnostic.block_se if math.isfinite(diagnostic.block_se) else iid_se
    scale = iid_se / max(block_se, EPS) if iid_se > 0 else 1.0
    adjusted = naive * min(1.0, scale)
    day_zero = n < MIN_DECISIONS

    status = "measured" if not day_zero else "accumulating"
    return {
        "naive_quality_score": round(float(naive), 3),
        "quality_adjusted_score": round(float(adjusted), 3),
        "inflation": round(float(diagnostic.inflation), 3) if math.isfinite(diagnostic.inflation) else None,
        "n_decisions": n,
        "provenance": "real_measured" if not day_zero else "accumulating",
        "substantiation": "T-R" if not day_zero else "T-O",
        "day_zero": day_zero,
        "decisions_until_measured": max(0, MIN_DECISIONS - n),
        **_cluster_payload(decisions),
        "status": status,
        "overall_quality_score": round(float(naive), 3) if not day_zero else None,
        "overall_quality_adjusted": round(float(adjusted), 3) if not day_zero else None,
        "source": "live",
        "analytics_provenance": status,
    }


def _cluster_payload(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = {}
    for decision in decisions:
        cluster_id = _cluster_id(decision)
        value = _quality_value(decision)
        if value is not None:
            grouped.setdefault(cluster_id, []).append(value)

    clusters = []
    for cluster_id in sorted(grouped):
        values = grouped[cluster_id]
        n = len(values)
        average = mean(values) if values else None
        sigma = stdev(values) if n >= 2 else 0.0
        measured = n >= MIN_DECISIONS_PER_CLUSTER
        risk_adjusted_quality = 0.0 if sigma <= EPS else average / sigma
        clusters.append(
            {
                "cluster_id": cluster_id,
                "n_decisions": n,
                "mean_return": round(float(average), 6) if measured and average is not None else None,
                "std_return": round(float(sigma), 6) if measured else None,
                "risk_adjusted_quality": round(float(risk_adjusted_quality), 3) if measured else None,
                "status": "measured" if measured else "accumulating",
            }
        )
    return {
        "clusters": clusters,
        "min_decisions_per_cluster": MIN_DECISIONS_PER_CLUSTER,
    }


def _cluster_id(decision: dict[str, Any]) -> str:
    metadata = decision.get("metadata")
    analytics = metadata.get("analytics") if isinstance(metadata, dict) else None
    cluster_id = analytics.get("cluster_id") if isinstance(analytics, dict) else None
    return str(cluster_id) if cluster_id else "unclassified"


def _quality_value(decision: dict[str, Any]) -> float | None:
    for key in ("quality", "outcome_quality", "decision_quality"):
        value = _finite(decision.get(key))
        if value is not None:
            return value

    if "is_correct" in decision:
        return 1.0 if bool(decision.get("is_correct")) else 0.0

    action = str(decision.get("actual_action") or decision.get("action") or "").lower()
    if action == "strong_execution":
        return 1.0
    if action == "partial_execution":
        return 0.5
    if action == "poor_execution":
        return 0.0

    pnl = _finite(decision.get("pnl") or decision.get("pnl_pct") or decision.get("pnlPct"))
    if pnl is not None:
        return max(0.0, min(1.0, 0.5 + pnl))
    return None


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
