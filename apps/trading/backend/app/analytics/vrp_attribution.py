"""Variance risk premium attribution by tail state."""

from __future__ import annotations

import math
from typing import Any

from ci_trading.quant import variance_risk_premium


MIN_DECISIONS = 30
TAIL_THRESHOLD = 0.35
VRP_EDGE_THRESHOLD = 0.01


def compute_vrp_attribution(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute IV-RV VRP while retaining tail-attribution diagnostics."""
    tail_attribution = _tail_attribution(decisions)
    eligible = [_analytics_vrp_row(decision) for decision in decisions]
    rows = [row for row in eligible if row is not None]
    n = len(rows)
    excluded = len(decisions) - n
    if n == 0:
        return {
            "tail_attribution": tail_attribution,
            "status": "instrument_validated",
            "provenance": "instrument_validated",
            "substantiation": "T-O",
            "day_zero": True,
            "decisions_until_measured": MIN_DECISIONS,
            "vrp_spread_mean": None,
            "vrp_spread_current": None,
            "classification": None,
            "iv_mean": None,
            "rv_mean": None,
            "n_eligible": 0,
            "n_excluded_missing_iv_rv": excluded,
            "min_observations": MIN_DECISIONS,
            "source": "live",
            "analytics_provenance": "instrument_validated",
        }

    mean_spread = sum(row["vrp"] for row in rows) / n
    current_spread = rows[-1]["vrp"]
    measured = n >= MIN_DECISIONS
    status = "measured" if measured else "accumulating"
    return {
        "tail_attribution": tail_attribution,
        "status": status,
        "provenance": "real_measured" if measured else "accumulating",
        "substantiation": "T-R" if measured else "T-O",
        "day_zero": not measured,
        "decisions_until_measured": max(0, MIN_DECISIONS - n),
        "vrp_spread_mean": round(mean_spread, 6) if measured else None,
        "vrp_spread_current": round(current_spread, 6) if measured else None,
        "classification": _classification(mean_spread) if measured else None,
        "iv_mean": round(sum(row["iv"] for row in rows) / n, 6) if measured else None,
        "rv_mean": round(sum(row["rv"] for row in rows) / n, 6) if measured else None,
        "n_eligible": n,
        "n_excluded_missing_iv_rv": excluded,
        "min_observations": MIN_DECISIONS,
        "source": "live",
        "analytics_provenance": status,
    }


def _tail_attribution(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [_vrp_row(decision) for decision in decisions]
    rows = [row for row in rows if row is not None]
    n = len(rows)
    low_tail = [row for row in rows if row["tail_dependence"] <= TAIL_THRESHOLD]
    high_tail = [row for row in rows if row["tail_dependence"] > TAIL_THRESHOLD]
    total_capture = sum(max(0.0, row["capture"]) for row in rows)
    low_capture = sum(max(0.0, row["capture"]) for row in low_tail)
    high_losses = sum(abs(min(0.0, row["capture"])) for row in high_tail)
    high_gains = sum(max(0.0, row["capture"]) for row in high_tail)
    low_tail_capture_pct = low_capture / total_capture if total_capture > 0 else 0.0
    high_tail_loss_ratio = high_losses / high_gains if high_gains > 0 else (1.0 if high_losses > 0 else 0.0)
    day_zero = n < MIN_DECISIONS

    return {
        "low_tail_capture_pct": round(low_tail_capture_pct, 3),
        "high_tail_loss_ratio": round(high_tail_loss_ratio, 3),
        "total_vrp_decisions": n,
        "high_tail_decisions": len(high_tail),
        "low_tail_decisions": len(low_tail),
        "provenance": "real_measured" if not day_zero else "accumulating",
        "substantiation": "T-R" if not day_zero else "T-O",
        "day_zero": day_zero,
        "decisions_until_measured": max(0, MIN_DECISIONS - n),
    }


def _analytics_vrp_row(decision: dict[str, Any]) -> dict[str, float] | None:
    metadata = decision.get("metadata")
    analytics = metadata.get("analytics") if isinstance(metadata, dict) else None
    if not isinstance(analytics, dict):
        return None
    iv = _finite(analytics.get("implied_vol"))
    rv = _finite(analytics.get("realized_vol"))
    if iv is None or rv is None:
        return None
    return {"iv": iv, "rv": rv, "vrp": variance_risk_premium(iv * iv, rv * rv)}


def _classification(vrp: float) -> str:
    if vrp > VRP_EDGE_THRESHOLD:
        return "edge"
    if vrp < -VRP_EDGE_THRESHOLD:
        return "insurance"
    return "neutral"


def _vrp_row(decision: dict[str, Any]) -> dict[str, float] | None:
    if not bool(decision.get("vrp_harvest") or decision.get("vrp_decision") or decision.get("options_analytics_only")):
        return None
    implied = _finite(decision.get("implied_variance"))
    realized = _finite(decision.get("realized_variance"))
    if implied is None:
        iv = _finite(decision.get("iv"))
        implied = iv * iv if iv is not None else None
    if realized is None:
        rv = _finite(decision.get("rv"))
        realized = rv * rv if rv is not None else None
    if implied is None or realized is None:
        return None
    capture = _finite(decision.get("vrp_capture") or decision.get("pnl") or decision.get("pnl_pct"))
    if capture is None:
        capture = variance_risk_premium(implied, realized)
    tail = _finite(decision.get("tail_dependence") or decision.get("tail_dep") or decision.get("tail_gap"))
    if tail is None:
        tail = 0.0
    return {"capture": capture, "tail_dependence": tail}


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
