"""Trading evidence endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import context_router
from app.evidence import TradingTemplateEngine
from app.factors.options import compute_options_factors
from app.factors.registry import ALL_FACTOR_NAMES, compute_factors
from app.routers.journal import _journal_records


GraphStoreFactory = Callable[[], Any]


def create_evidence_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-evidence"])
    engine = TradingTemplateEngine()

    @router.get("/evidence/{trade_id}")
    def get_evidence(trade_id: str):
        trade = _find_trade(trade_id, graph_store_factory, domain)
        if trade is None:
            return JSONResponse(status_code=404, content={"error": "Trade not found"})
        trade = _with_saved_metadata(trade)

        context = _context_for(trade)
        factors = _factors_for(trade, context)
        options_factors = _options_factors_for(trade, context)
        if options_factors:
            context["options_factors"] = options_factors
            context["options_analytics_only"] = True
        action = _action_for(trade)
        confidence = _confidence_for(trade)
        evidence_text = engine.render(trade, factors, action, confidence, context)

        response = {
            "trade_id": str(trade.get("trade_id")),
            "evidence_text": evidence_text,
            "factor_breakdown": engine.render_factor_breakdown(factors),
            "factors": factors,
            "action": action,
            "confidence": confidence,
        }
        if options_factors:
            response["options_factors"] = options_factors
            response["options_analytics_only"] = True
        return response

    return router


def _find_trade(
    trade_id: str,
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> dict[str, Any] | None:
    for trade in _journal_records(graph_store_factory, domain):
        if str(trade.get("trade_id")) == str(trade_id):
            return dict(trade)
    return None


def _with_saved_metadata(trade: dict[str, Any]) -> dict[str, Any]:
    trade_id = str(trade.get("trade_id") or "")
    if not trade_id:
        return trade
    try:
        metadata_cache = context_router._load_json_optional("trade_metadata.json") or {}
    except Exception:
        metadata_cache = {}
    saved = metadata_cache.get(trade_id) if isinstance(metadata_cache, dict) else None
    if not isinstance(saved, dict):
        return trade

    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    merged = dict(trade)
    merged["metadata"] = {**saved, **metadata}
    for key in (
        "ticker",
        "direction",
        "category",
        "strategy_tag",
        "entry_price",
        "exit_price",
        "size",
        "entry_time",
        "exit_time",
        "pnl",
    ):
        camel_key = _camel_key(key)
        saved_value = saved.get(key) if key in saved else saved.get(camel_key)
        if saved_value not in {None, ""}:
            merged[key] = saved_value
    return merged


def _context_for(trade: dict[str, Any]) -> dict[str, Any]:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    context = metadata.get("context") if isinstance(metadata.get("context"), dict) else {}
    merged = {**trade, **metadata, **context}
    factors = trade.get("factors")
    if isinstance(factors, dict):
        nested_metadata = factors.get("metadata")
        if isinstance(nested_metadata, dict):
            merged.update(nested_metadata)
    return merged


def _factors_for(trade: dict[str, Any], context: dict[str, Any]) -> dict[str, float]:
    raw_factors = trade.get("factors") if isinstance(trade.get("factors"), dict) else {}
    factors = {
        name: _coerce_factor(raw_factors.get(name))
        for name in ALL_FACTOR_NAMES
        if name in raw_factors
    }

    if len(factors) < len(ALL_FACTOR_NAMES):
        metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
        scored = metadata.get("scored_factors") if isinstance(metadata.get("scored_factors"), dict) else {}
        factors.update({
            name: _coerce_factor(scored.get(name))
            for name in ALL_FACTOR_NAMES
            if name not in factors and name in scored
        })

    if len(factors) < len(ALL_FACTOR_NAMES):
        vector = context.get("factor_vector")
        if isinstance(vector, list):
            for name, value in zip(ALL_FACTOR_NAMES, vector):
                factors.setdefault(name, _coerce_factor(value))

    if len(factors) < len(ALL_FACTOR_NAMES):
        recomputed = compute_factors(context)
        for name in ALL_FACTOR_NAMES:
            if name not in factors and name in recomputed:
                factors[name] = _coerce_factor(recomputed.get(name))

    for name in ALL_FACTOR_NAMES:
        factors.setdefault(name, 0.5)
    return {name: factors[name] for name in ALL_FACTOR_NAMES}


def _options_factors_for(trade: dict[str, Any], context: dict[str, Any]) -> dict[str, float] | None:
    raw = trade.get("options_factors") if isinstance(trade.get("options_factors"), dict) else None
    if raw is None and isinstance(context.get("options_factors"), dict):
        raw = context["options_factors"]
    if raw is not None:
        return {
            "iv_rv_ratio": _coerce_factor(raw.get("iv_rv_ratio")),
            "greeks_exposure": _coerce_factor(raw.get("greeks_exposure")),
            "theta_efficiency": _coerce_factor(raw.get("theta_efficiency")),
        }
    if not _is_options_like(context):
        return None
    return compute_options_factors(context)


def _is_options_like(context: dict[str, Any]) -> bool:
    if str(context.get("category") or "") == "income_strategy":
        return True
    text = " ".join(
        str(context.get(key) or "")
        for key in ("strategy_tag", "thesis_type", "notes", "subcategory", "direction")
    ).lower().replace("-", "_").replace(" ", "_")
    return any(
        token in text
        for token in (
            "option",
            "straddle",
            "strangle",
            "iron_condor",
            "credit",
            "debit",
            "covered",
            "wheel",
            "calendar",
            "butterfly",
            "premium",
            "iv",
        )
    )


def _action_for(trade: dict[str, Any]) -> str:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    return str(
        trade.get("action")
        or trade.get("recommended_action")
        or metadata.get("score_action")
        or metadata.get("action")
        or "unknown"
    )


def _confidence_for(trade: dict[str, Any]) -> float:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    return _coerce_factor(
        trade.get("confidence")
        if trade.get("confidence") is not None
        else metadata.get("score_confidence")
    )


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5
    if number != number or number in (float("inf"), float("-inf")):
        return 0.5
    return max(0.0, min(number, 1.0))


def _camel_key(key: str) -> str:
    parts = key.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])
