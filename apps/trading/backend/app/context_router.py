"""Cached trading context endpoints."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.routers.data_import import _trade_store_ref
from app.services.pattern_detector import detect_patterns
from app.services.trust_analysis import TrustAnalyzer
from copilot_sdk.state.cached_static import cached_static
from copilot_sdk.scoring.mutation_lock import serialize_mutation
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


router = APIRouter(tags=["context"])
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DATA_DIR = _DEFAULT_DATA_DIR
_provider: Any | None = None
_FACTOR_NAMES = (
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
)


def _demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("TRADING_DEMO_MODE"))
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _explicit_demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("TRADING_DEMO_MODE"))
    return configured is not None and configured.strip().lower() in {"1", "true", "yes", "on"}


def _load_json(filename: str) -> Any:
    path = _DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(filename: str) -> Any | None:
    path = _DATA_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    fallback = _DEFAULT_DATA_DIR / filename
    if fallback.exists():
        try:
            return json.loads(fallback.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
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


def _default_market_snapshot() -> dict[str, Any]:
    return {"regime": "ranging", "vix": 20.0, "adx": 25.0, "source": "default"}


def _market_provider() -> Any:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return _provider


def _provenance_payload(result: Any) -> dict[str, Any]:
    return {"source": result.source, "as_of": result.as_of}


def _fallback_provenance(source: str = "fixture") -> dict[str, Any]:
    explicit_demo = _explicit_demo_mode()
    return {
        "source": "demo_fixture" if explicit_demo else source,
        "as_of": None,
        **({"label": source} if explicit_demo else {}),
    }


def _ticker_response(value: dict[str, Any], provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(value)
    if "change30dPct" not in payload and "change_30d_pct" in payload:
        payload["change30dPct"] = payload.get("change_30d_pct")
    if "change_30d_pct" not in payload and "change30dPct" in payload:
        payload["change_30d_pct"] = payload.get("change30dPct")
    if "marketCapB" not in payload and "market_cap_b" in payload:
        payload["marketCapB"] = payload.get("market_cap_b")
    if "market_cap_b" not in payload and "marketCapB" in payload:
        payload["market_cap_b"] = payload.get("marketCapB")
    if "above50ma" not in payload and "above_50ma" in payload:
        payload["above50ma"] = payload.get("above_50ma")
    if "above_50ma" not in payload and "above50ma" in payload:
        payload["above_50ma"] = payload.get("above50ma")
    if "volRankPctl" not in payload and "vol_rank_pctl" in payload:
        payload["volRankPctl"] = payload.get("vol_rank_pctl")
    if "vol_rank_pctl" not in payload and "volRankPctl" in payload:
        payload["vol_rank_pctl"] = payload.get("volRankPctl")
    if provenance is not None:
        payload.setdefault("source", provenance["source"])
        payload["provenance"] = provenance
    return payload


def _market_snapshot_response(value: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    spy = payload.get("spy")
    if isinstance(spy, dict):
        spy_payload = {"ticker": "SPY", **spy}
        if "change30dPct" not in spy_payload:
            spy_payload["change30dPct"] = spy_payload.get("change_pct") or spy_payload.get("change_30d_pct")
        if "change_30d_pct" not in spy_payload and "change30dPct" in spy_payload:
            spy_payload["change_30d_pct"] = spy_payload.get("change30dPct")
        payload["spy"] = spy_payload
    vix = payload.get("vix")
    if isinstance(vix, (int, float)):
        payload["vix"] = {"ticker": "VIX", "price": float(vix), "value": float(vix)}
    elif isinstance(vix, dict):
        vix_payload = {"ticker": "VIX", **vix}
        if "price" not in vix_payload and "value" in vix_payload:
            vix_payload["price"] = vix_payload.get("value")
        if "change30dPct" not in vix_payload and "change_30d_pct" in vix_payload:
            vix_payload["change30dPct"] = vix_payload.get("change_30d_pct")
        payload["vix"] = vix_payload
    payload.setdefault("source", provenance["source"])
    payload["asOf"] = provenance.get("as_of")
    payload["provenance"] = provenance
    return payload


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _trade_vector(trade: dict[str, Any]) -> list[float]:
    return [float(trade.get(name, 0.0) or 0.0) for name in _FACTOR_NAMES]


def _as_trade_dict(trade: Any) -> dict[str, Any]:
    if isinstance(trade, dict):
        return trade
    if hasattr(trade, "to_dict"):
        return trade.to_dict()
    return {}


def _unwrap_shared_scorer(candidate: Any) -> Any:
    scorer_factory = getattr(candidate, "_scorer", None)
    return scorer_factory() if callable(scorer_factory) else candidate


def _scoring_route_scorer(request: Request) -> Any | None:
    for route in getattr(request.app, "routes", []):
        if getattr(route, "path", None) != "/api/score":
            continue
        endpoint = getattr(route, "endpoint", None)
        code = getattr(endpoint, "__code__", None)
        closure = getattr(endpoint, "__closure__", None)
        if code is None or not closure:
            continue
        for name, cell in zip(code.co_freevars, closure):
            if name != "get_scorer":
                continue
            get_scorer = cell.cell_contents
            if callable(get_scorer):
                return _unwrap_shared_scorer(get_scorer())
    return None


def _trust_scorer(request: Request) -> Any:
    shared_scorer = _scoring_route_scorer(request)
    if shared_scorer is not None:
        return shared_scorer

    store = getattr(request.app.state, "trading_selected_graph_store", None)
    if store is not None:
        return CompoundingScorer.from_preset("trading", graph_store=store)
    return CompoundingScorer.from_preset("trading")


def _trading_conservation_config() -> dict[str, Any]:
    try:
        preset = TradingPreset()
        shape = preset.shape
        return {
            "categories": list(shape.category_names),
            "penalty_ratio": float(preset.penalty_ratio),
            "n_actions": int(shape.n_actions),
            "n_factors": int(shape.n_factors),
        }
    except Exception:
        return {
            "categories": ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"],
            "penalty_ratio": 3.0,
            "n_actions": 4,
            "n_factors": 7,
        }


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _was_correct(trade: dict[str, Any]) -> bool:
    pnl = _safe_float(trade.get("pnl"))
    if pnl is not None:
        return pnl > 0

    verification_score = _safe_float(trade.get("verification_score"))
    if verification_score is not None:
        return verification_score >= 0.5

    return False


def _category_for_trade(trade: dict[str, Any]) -> str | None:
    value = trade.get("category") or trade.get("strategy_tag")
    return str(value) if value is not None else None


def _conservation_category_row(
    category: str,
    trades: list[dict[str, Any]],
    *,
    penalty_ratio: float,
    n_actions: int,
    n_factors: int,
) -> dict[str, Any]:
    category_trades = [trade for trade in trades if _category_for_trade(trade) == category]
    verified = [trade for trade in category_trades if bool(trade.get("verified", False))]
    correct = [trade for trade in verified if _was_correct(trade)]
    accuracy = len(correct) / len(verified) if verified else 0.0

    v_cat = n_actions * n_factors
    effective_alpha = penalty_ratio * max(accuracy, 0.01) if verified else 0.01
    theta_min_proxy = 23.53 / (effective_alpha * v_cat) if v_cat > 0 else 1.0

    if len(verified) < 10:
        status_value = "BOOTSTRAP"
    elif accuracy >= theta_min_proxy:
        status_value = "GREEN"
    elif accuracy >= theta_min_proxy * 0.8:
        status_value = "AMBER"
    else:
        status_value = "RED"

    note = None
    if status_value in {"AMBER", "RED"}:
        note = "Simplified proxy. Full conservation at /api/conservation/status."

    return {
        "category": category,
        "total_trades": len(category_trades),
        "verified": len(verified),
        "correct": len(correct),
        "accuracy": round(accuracy, 6),
        "theta_min_proxy": round(theta_min_proxy, 6),
        "status": status_value,
        "can_trade": status_value != "RED",
        "note": note,
    }


@router.get("/market-snapshot")
@cached_static("market-snapshot")
def market_snapshot(request: Request) -> dict[str, Any]:
    provider = _market_provider()
    try:
        result = provider.get_market_snapshot()
    except Exception as exc:
        if not _demo_mode():
            raise HTTPException(status_code=503, detail="Market data provider unavailable") from exc
        result = None
    if isinstance(result.value, dict):
        if not _demo_mode() and str(result.source).lower() in {
            "sample",
            "fixture",
            "demo_fixture",
        }:
            raise HTTPException(status_code=503, detail="Market data provider unavailable")
        origin_provenance = getattr(provider, "origin_provenance", None)
        provenance_result = (
            origin_provenance("market_snapshot", result)
            if callable(origin_provenance)
            else result
        )
        return _market_snapshot_response(result.value, _provenance_payload(provenance_result))

    # JSON cache remains as the fixture fallback reference when live/provider data is unavailable.
    payload = _load_json_optional("market_snapshot.json")
    if not _demo_mode():
        raise HTTPException(status_code=503, detail="Market data provider unavailable")
    if isinstance(payload, dict):
        return _market_snapshot_response(payload, _fallback_provenance())
    return _market_snapshot_response(_default_market_snapshot(), _fallback_provenance())


@router.get("/ticker/{ticker}")
def ticker_detail(ticker: str) -> dict[str, Any]:
    normalized = ticker.upper()
    try:
        result = _market_provider().get_ticker_snapshot(normalized)
    except Exception as exc:
        if not _demo_mode():
            raise HTTPException(status_code=503, detail="Market data provider unavailable") from exc
        result = None
    if isinstance(result.value, dict):
        if not _demo_mode() and str(result.source).lower() in {
            "sample",
            "fixture",
            "demo_fixture",
        }:
            raise HTTPException(status_code=503, detail="Market data provider unavailable")
        return _ticker_response(result.value, _provenance_payload(result))

    # JSON cache remains as the fixture fallback reference when live/provider data is unavailable.
    if not _demo_mode():
        raise HTTPException(status_code=503, detail="Market data provider unavailable")
    cache = _load_json("ticker_cache.json")
    if normalized not in cache:
        return {
            "ticker": normalized,
            "price": None,
            "change_30d_pct": None,
            "change30dPct": None,
            "volume": None,
            "source": "unknown",
            "provenance": _fallback_provenance(),
        }
    return _ticker_response(cache[normalized], _fallback_provenance(str(cache[normalized].get("source") or "fixture")))


@router.get("/portfolio-summary")
def portfolio_summary() -> dict[str, Any]:
    if not _demo_mode():
        raise HTTPException(status_code=503, detail="Portfolio analytics provider unavailable")
    analytics = _load_json_optional("analytics_cache.json")
    if isinstance(analytics, dict) and isinstance(analytics.get("portfolio_summary"), dict):
        summary = analytics["portfolio_summary"]
    else:
        summary = _load_json("portfolio_summary.json")
    if _explicit_demo_mode():
        return {**summary, "source": "demo_fixture", "provenance": "demo_fixture"}
    return summary


@router.get("/analytics")
@cached_static("analytics")
def analytics(request: Request) -> dict[str, Any]:
    if not _demo_mode():
        raise HTTPException(status_code=503, detail="Trading analytics provider unavailable")
    payload = _load_json_optional("analytics_cache.json")
    if isinstance(payload, dict):
        if _explicit_demo_mode():
            return {**payload, "provenance": "demo_fixture"}
        return payload
    return {**_empty_analytics(), "provenance": "demo_fixture"}


@router.get("/trust-analysis")
def trust_analysis(request: Request, category: str | None = None) -> dict[str, Any]:
    trades = [_as_trade_dict(trade) for trade in list(_trade_store_ref)]
    trades = [trade for trade in trades if trade]
    result = TrustAnalyzer().analyze(_trust_scorer(request), trades, category=category)
    factor_details = list(result["factors"])
    result["factor_details"] = factor_details
    result["factors"] = list(result["factor_names"])
    result["trust_scores"] = {factor["name"]: factor for factor in factor_details}
    return result


@router.get("/patterns")
@cached_static("patterns")
def behavioral_patterns(request: Request) -> dict[str, Any]:
    trades = [_as_trade_dict(trade) for trade in list(_trade_store_ref)]
    trades = [trade for trade in trades if trade]
    if not trades:
        return {
            "patterns": [],
            "total_trades": 0,
            "message": "Import trades to detect patterns.",
        }

    patterns = detect_patterns(trades)
    most_severe = max(patterns, key=lambda pattern: pattern["severity"])["name"] if patterns else None
    return {
        "patterns": patterns,
        "total_patterns_detected": len(patterns),
        "total_trades_analyzed": len(trades),
        "most_severe": most_severe,
    }


@router.get("/conservation-breakdown")
def conservation_breakdown() -> dict[str, Any]:
    """Return a simplified proxy breakdown; /api/conservation/status remains authoritative."""
    config = _trading_conservation_config()
    trades = [_as_trade_dict(trade) for trade in list(_trade_store_ref)]
    trades = [trade for trade in trades if trade]

    categories = [
        _conservation_category_row(
            category,
            trades,
            penalty_ratio=config["penalty_ratio"],
            n_actions=config["n_actions"],
            n_factors=config["n_factors"],
        )
        for category in config["categories"]
    ]
    red_categories = sum(1 for category in categories if category["status"] == "RED")
    amber_categories = sum(1 for category in categories if category["status"] == "AMBER")
    green_categories = sum(1 for category in categories if category["status"] == "GREEN")

    return {
        "categories": categories,
        "total_categories": len(categories),
        "red_categories": red_categories,
        "amber_categories": amber_categories,
        "green_categories": green_categories,
        "total_verified": sum(category["verified"] for category in categories),
        "overall_safe": red_categories == 0,
        "penalty_ratio": config["penalty_ratio"],
        "methodology": (
            "Simplified per-category proxy using theta_min_proxy = "
            "23.53 / (penalty * accuracy * V_cat). "
            "Global conservation at /api/conservation/status remains authoritative."
        ),
    }


@router.get("/similar")
def similar_trades(
    category: str,
    signal_alignment: float,
    market_regime: float,
    position_sizing: float,
    timing_quality: float,
    risk_reward_actual: float,
    emotional_indicator: float,
    signal_confidence: float = 0.5,
    n: int = 5,
) -> dict[str, Any]:
    if not _demo_mode():
        raise HTTPException(status_code=503, detail="Trading similarity provider unavailable")
    seed = _load_json_optional("trading_seed_v2.json")
    if not isinstance(seed, list):
        return {"similar": [], "count": 0, "source": "demo_fixture", "provenance": "demo_fixture"}

    query = [
        signal_alignment,
        market_regime,
        position_sizing,
        timing_quality,
        risk_reward_actual,
        emotional_indicator,
        signal_confidence,
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
                "market_regime": trade.get("market_regime"),
                "pnl_pct": trade.get("pnl_pct"),
                "outcome": trade.get("outcome"),
                "is_correct": trade.get("is_correct"),
                "similarity": round(similarity, 4),
            }
        )

    matches.sort(key=lambda item: item["similarity"], reverse=True)
    limit = max(n, 0)
    return {
        "similar": matches[:limit],
        "count": len(matches),
        "source": "demo_fixture",
        "provenance": "demo_fixture",
    }


@router.post("/trade-metadata", status_code=status.HTTP_201_CREATED)
@serialize_mutation("trading", event="metadata_update")
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
@cached_static("trade-metadata")
def get_trade_metadata(request: Request) -> dict[str, Any]:
    return _load_json_optional("trade_metadata.json") or {}
