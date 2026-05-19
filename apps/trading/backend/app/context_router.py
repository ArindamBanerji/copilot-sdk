"""Cached trading context endpoints."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status


router = APIRouter(tags=["context"])
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DATA_DIR = _DEFAULT_DATA_DIR
_FACTOR_NAMES = (
    "conviction",
    "research_depth",
    "technical_signal",
    "position_size",
    "time_horizon",
    "market_regime",
)


def _load_json(filename: str) -> Any:
    path = _DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(filename: str) -> Any | None:
    path = _DATA_DIR / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    fallback = _DEFAULT_DATA_DIR / filename
    if fallback.exists():
        return json.loads(fallback.read_text(encoding="utf-8"))
    return None


def _write_json(filename: str, payload: Any) -> None:
    path = _DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _empty_analytics() -> dict[str, Any]:
    return {
        "source": "default",
        "contrast_card": {},
        "counterfactual": {},
        "calendar_heatmap": {},
        "thesis_breakdown": {},
        "regime_analysis": {},
        "research_impact": {},
        "portfolio_concentration": {},
        "rolling_10": [],
        "risk_management": {},
        "portfolio_summary": {},
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _trade_vector(trade: dict[str, Any]) -> list[float]:
    return [float(trade.get(name, 0.0) or 0.0) for name in _FACTOR_NAMES]


@router.get("/market-snapshot")
def market_snapshot() -> dict[str, Any]:
    return _load_json("market_snapshot.json")


@router.get("/ticker/{ticker}")
def ticker_detail(ticker: str) -> dict[str, Any]:
    normalized = ticker.upper()
    cache = _load_json("ticker_cache.json")
    if normalized not in cache:
        return {
            "ticker": normalized,
            "price": None,
            "change_30d_pct": None,
            "volume": None,
            "source": "unknown",
        }
    return cache[normalized]


@router.get("/portfolio-summary")
def portfolio_summary() -> dict[str, Any]:
    analytics = _load_json_optional("analytics_cache.json")
    if isinstance(analytics, dict) and isinstance(analytics.get("portfolio_summary"), dict):
        return analytics["portfolio_summary"]
    return _load_json("portfolio_summary.json")


@router.get("/analytics")
def analytics() -> dict[str, Any]:
    payload = _load_json_optional("analytics_cache.json")
    if isinstance(payload, dict):
        return payload
    return _empty_analytics()


@router.get("/similar")
def similar_trades(
    category: str,
    conviction: float,
    research_depth: float,
    technical_signal: float,
    position_size: float,
    time_horizon: float,
    market_regime: float,
    n: int = 5,
) -> dict[str, Any]:
    seed = _load_json_optional("trading_seed_v2.json")
    if not isinstance(seed, list):
        return {"similar": [], "count": 0}

    query = [
        conviction,
        research_depth,
        technical_signal,
        position_size,
        time_horizon,
        market_regime,
    ]
    matches = []
    for trade in seed:
        # Similarity is scoped to the requested Trading category so the result set is behaviorally comparable.
        if not isinstance(trade, dict) or trade.get("category") != category:
            continue
        similarity = _cosine_similarity(query, _trade_vector(trade))
        if similarity <= 0.85:
            continue
        matches.append(
            {
                "trade_id": trade.get("trade_id"),
                "ticker": trade.get("ticker"),
                "thesis_type": trade.get("thesis_type"),
                "timeframe": trade.get("timeframe"),
                "research_depth": trade.get("research_depth"),
                "pnl_pct": trade.get("pnl_pct"),
                "outcome": trade.get("outcome"),
                "is_correct": trade.get("is_correct"),
                "similarity": round(similarity, 4),
            }
        )

    matches.sort(key=lambda item: item["similarity"], reverse=True)
    limit = max(n, 0)
    return {"similar": matches[:limit], "count": len(matches)}


@router.post("/trade-metadata", status_code=status.HTTP_201_CREATED)
def save_trade_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    decision_id = payload.get("decision_id")
    if not decision_id:
        raise HTTPException(status_code=400, detail="decision_id is required")

    metadata = _load_json_optional("trade_metadata.json") or {}
    record = dict(payload)
    metadata[str(decision_id)] = record
    _write_json("trade_metadata.json", metadata)
    return {"decision_id": str(decision_id), "metadata": record}


@router.get("/trade-metadata")
def get_trade_metadata() -> dict[str, Any]:
    return _load_json_optional("trade_metadata.json") or {}

