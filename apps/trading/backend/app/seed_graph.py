"""Deterministic Trading graph seed plan."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FACTOR_NAMES = (
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
)


def _load_json(filename: str, default: Any) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return "_".join("".join(ch if ch.isalnum() else "_" for ch in text).split("_")) or "unknown"


def _node_id(label: str, natural_key: Any) -> str:
    return f"{label}:{_slug(natural_key)}"


def _add_node(
    nodes: list[dict[str, Any]],
    seen: dict[str, dict[str, Any]],
    label: str,
    natural_key: Any,
    properties: dict[str, Any],
) -> str:
    node_id = _node_id(label, natural_key)
    if node_id not in seen:
        node = {"id": node_id, "label": label, "properties": dict(properties)}
        nodes.append(node)
        seen[node_id] = node
    return node_id


def _add_edge(
    edges: list[dict[str, Any]],
    seen: set[tuple[str, str, str]],
    label: str,
    from_id: str,
    to_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    token = (label, from_id, to_id)
    if token in seen:
        return
    seen.add(token)
    edges.append(
        {
            "id": f"{label}:{len(edges) + 1}",
            "label": label,
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {},
        }
    )


def seed_trading_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    trades = _load_json("trading_seed_v2.json", [])
    if not isinstance(trades, list):
        trades = []
    portfolio = _load_json("portfolio_summary.json", {})
    market = _load_json("market_snapshot.json", {})
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: dict[str, dict[str, Any]] = {}
    seen_edges: set[tuple[str, str, str]] = set()

    portfolio_id = _add_node(
        nodes,
        seen_nodes,
        "Portfolio",
        "primary",
        {
            "portfolio_id": "primary",
            "name": "Primary Trading Portfolio",
            "total_value": portfolio.get("open_exposure_dollars"),
            "cash_buffer": portfolio.get("cash_buffer"),
        },
    )
    market_event_id = _add_node(
        nodes,
        seen_nodes,
        "MarketEvent",
        "current_regime",
        {
            "event_id": "current_regime",
            "date": "current",
            "vix_at_entry": (market.get("vix") or {}).get("value"),
            "emotional_indicator": (market.get("vix") or {}).get("regime"),
        },
    )
    factor_ids = {
        factor: _add_node(
            nodes,
            seen_nodes,
            "RiskFactor",
            factor,
            {"factor_id": factor, "name": factor, "value": 0.0},
        )
        for factor in FACTOR_NAMES
    }

    for index, trade in enumerate(trades):
        if not isinstance(trade, dict):
            continue
        trade_id = str(trade.get("trade_id") or f"trade-{index}")
        ticker = str(trade.get("ticker") or "UNKNOWN")
        category = str(trade.get("category") or "unknown")
        instrument_id = _add_node(
            nodes,
            seen_nodes,
            "Instrument",
            ticker,
            {
                "ticker": ticker,
                "asset_class": category.split("_")[0],
                "category": category,
                "sector": (market.get("sector") or {}).get("leader"),
            },
        )
        position_id = _add_node(
            nodes,
            seen_nodes,
            "Position",
            trade_id,
            {
                "position_id": trade_id,
                "ticker": ticker,
                "shares": trade.get("shares"),
                "entry_price": trade.get("entry_price"),
                "timing_quality": trade.get("timing_quality"),
            },
        )
        signal_id = _add_node(
            nodes,
            seen_nodes,
            "TradeSignal",
            trade_id,
            {
                "signal_id": trade_id,
                "thesis_type": trade.get("thesis_type"),
                "timeframe": trade.get("timeframe"),
                "position_sizing": trade.get("position_sizing"),
                "signal_alignment": trade.get("signal_alignment"),
            },
        )
        event_id = _add_node(
            nodes,
            seen_nodes,
            "MarketEvent",
            trade.get("date") or trade_id,
            {
                "event_id": trade.get("date") or trade_id,
                "date": trade.get("date"),
                "vix_at_entry": trade.get("vix_at_entry"),
                "emotional_indicator": trade.get("emotional_indicator", (market.get("vix") or {}).get("regime")),
            },
        )
        decision_id = _add_node(
            nodes,
            seen_nodes,
            "Decision",
            trade_id,
            {
                "decision_id": f"decision-{trade_id}",
                "domain": "trading",
                "category": category,
                "recommended_action": trade.get("action_taken") or trade.get("direction"),
                "confidence": round(0.55 + rng.random() * 0.4, 4),
                "created_at": trade.get("date"),
            },
        )
        _add_edge(edges, seen_edges, "DECIDED_ON", decision_id, instrument_id, {"trade_id": trade_id})
        _add_edge(edges, seen_edges, "HOLDS", portfolio_id, position_id)
        _add_edge(edges, seen_edges, "POSITION_IN", position_id, instrument_id)
        _add_edge(edges, seen_edges, "TRIGGERED_BY", decision_id, signal_id)
        _add_edge(edges, seen_edges, "OCCURRED_DURING", signal_id, event_id)
        _add_edge(edges, seen_edges, "OCCURRED_DURING", signal_id, market_event_id)
        for factor, factor_id in factor_ids.items():
            value = trade.get(factor)
            _add_edge(edges, seen_edges, "EVALUATED_WITH", decision_id, factor_id, {"value": value})
            if factor in {"timing_quality", "emotional_indicator"}:
                _add_edge(edges, seen_edges, "RISK_EXPOSURE", position_id, factor_id, {"value": value})

    return nodes, edges
