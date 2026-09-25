"""Seed Trading VLD showcase trades."""
from __future__ import annotations

from typing import Any

from .evidence_provider import register_showcase_evidence

SHOWCASE_TRADES: list[dict[str, Any]] = [
    {
        "trade_id": "VLD-TRD-1",
        "title": "Long NVDA — AI infrastructure thesis",
        "category": "trend_following",
        "surface_factors": [0.6996, 0.4763, 0.5676, 0.0093, 0.2692, 0.8598, 0.3994, 0.3360, 0.4916, 0.4091],
        "surface_action": "strong_execution",
        "expected_action": "partial_execution",
        "narrative": (
            "Q first selects position sizing and finds manageable-but-not-full-size capacity. "
            "The second read finds regime/correlation data that reduces confidence in full execution. "
            "Recommendation shifts from strong to partial execution."
        ),
        "attempted_dimensions": [2, 1],
        "evidence": {
            2: {"value": 0.55, "confidence": 0.90, "source": "portfolio_engine"},
            1: {"value": 0.88, "confidence": 0.90, "source": "correlation_engine"},
        },
    },
    {
        "trade_id": "VLD-TRD-2",
        "title": "Add to AAPL — strong earnings beat",
        "category": "trend_following",
        "surface_factors": [0.6555, 0.4529, 0.2436, 0.0000, 0.5810, 0.5336, 0.6255, 0.5352, 0.6721, 0.6543],
        "surface_action": "strong_execution",
        "expected_action": "partial_execution",
        "narrative": (
            "Q first selects portfolio concentration and finds the position is too large for full execution. "
            "The second read checks market-regime correlation and reinforces the partial execution decision. "
            "The portfolio read alone is sufficient to shift the recommendation to partial execution."
        ),
        "attempted_dimensions": [2, 1],
        "evidence": {
            2: {"value": 0.85, "confidence": 0.92, "source": "portfolio_engine"},
            1: {"value": 0.78, "confidence": 0.88, "source": "correlation_engine"},
        },
    },
    {
        "trade_id": "VLD-TRD-S1",
        "title": "Close small loss per stop-loss",
        "category": "trend_following",
        "surface_factors": [0.6000, 0.2197, 0.2417, 0.0245, 0.4000, 0.6566, 0.5000, 0.5000, 0.5000, 0.5000],
        "surface_action": "strong_execution",
        "expected_action": "strong_execution",
        "budget": 0,
        "narrative": "Clear high-margin strong execution case; no investigation budget is needed.",
        "evidence": {},
    },
]


def seed_vld_trading_showcase(data_source: Any) -> dict[str, Any]:
    """Register deterministic VLD showcase evidence for Trading."""
    if data_source is not None and not hasattr(data_source, "vld_evidence"):
        try:
            data_source.vld_evidence = {}
        except Exception:
            pass

    trade_ids: list[str] = []
    evidence_count = 0
    for trade in SHOWCASE_TRADES:
        trade_id = str(trade["trade_id"])
        evidence = {int(k): dict(v) for k, v in trade.get("evidence", {}).items()}
        register_showcase_evidence(trade_id, evidence)
        if data_source is not None and isinstance(getattr(data_source, "vld_evidence", None), dict):
            data_source.vld_evidence[trade_id] = evidence
        trade_ids.append(trade_id)
        evidence_count += len(evidence)
    return {
        "trades": trade_ids,
        "trade_count": len(trade_ids),
        "evidence_records": evidence_count,
        "status": "registered",
    }
