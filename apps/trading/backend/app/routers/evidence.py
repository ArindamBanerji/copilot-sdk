"""Trading evidence endpoint."""

from __future__ import annotations

from math import isfinite
from typing import Any, Callable, cast

from fastapi import APIRouter, HTTPException

from app import context_router
from app.evidence import TradingTemplateEngine
from app.factors.options import compute_options_factors
from app.factors.registry import ALL_FACTOR_NAMES, compute_factors
from app.routers.journal import _journal_records
from copilot_sdk.scoring.presets.trading import TradingPreset


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
        trade = _find_trade(trade_id, graph_store_factory, domain, include_outcome=True)
        if trade is None:
            return {
                "trade_id": trade_id,
                "evidence_text": "",
                "factor_breakdown": [],
                "factors": [],
                "factor_scores": {},
                "similar_trades": [],
                "counterfactual": None,
                "options_factors": {},
                "options_analytics_only": False,
                "action": "unknown",
                "confidence": 0.0,
            }
        trade = _with_saved_metadata(trade)

        context = _context_for(trade)
        factor_scores = _factors_for(trade, context)
        options_factors = _options_factors_for(trade, context)
        if options_factors:
            context["options_factors"] = options_factors
            context["options_analytics_only"] = True
        action = _action_for(trade)
        confidence = _confidence_for(trade)
        evidence_text = engine.render(trade, factor_scores, action, confidence, context)
        factor_breakdown = engine.render_factor_breakdown(factor_scores)
        factors = _factor_evidence(factor_scores, trade)

        response = {
            "trade_id": str(trade.get("trade_id")),
            "tradeId": str(trade.get("trade_id")),
            "evidence_text": evidence_text,
            "evidenceText": evidence_text,
            "factor_breakdown": factor_breakdown,
            "factorBreakdown": factor_breakdown,
            "factors": factors,
            "factor_scores": factor_scores,
            "action": action,
            "confidence": confidence,
            "similar_trades": _similar_trades(
                trade_id,
                trade,
                graph_store_factory,
                domain,
            ),
            "counterfactual": _counterfactual(trade, action),
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
    *,
    include_outcome: bool = False,
) -> dict[str, Any] | None:
    if graph_store_factory is not None:
        try:
            decision = graph_store_factory().get_decision(
                trade_id,
                domain,
                include_outcome=include_outcome,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Trading graph unavailable") from exc
        if isinstance(decision, dict):
            return cast(
                dict[str, Any],
                context_router._trade_detail_payload(
                    decision,
                    saved_metadata=context_router._saved_trade_metadata(trade_id),
                ),
            )
    for trade in _journal_records(graph_store_factory, domain):
        if str(trade.get("trade_id")) == str(trade_id):
            return cast(
                dict[str, Any],
                context_router._trade_detail_payload(
                    dict(trade),
                    saved_metadata=context_router._saved_trade_metadata(trade_id),
                ),
            )
    return None


def _factor_evidence(
    factor_scores: dict[str, float],
    trade: dict[str, Any],
) -> list[dict[str, float | str]]:
    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_configured = metadata.get("factor_weights")
    configured: dict[str, Any] = raw_configured if isinstance(raw_configured, dict) else {}
    names = [name for name in TradingPreset().shape.factor_names if name in factor_scores]
    names.extend(name for name in factor_scores if name not in names)
    default_weight = 1.0 / len(names) if names else 0.0
    weights = {
        name: _coerce_factor(configured.get(name)) if name in configured else default_weight
        for name in names
    }
    total = sum(weights.values())
    if total > 0:
        weights = {name: value / total for name, value in weights.items()}
    return [
        {"name": name, "score": float(factor_scores[name]), "weight": float(weights[name])}
        for name in names
    ]


def _similar_trades(
    trade_id: str,
    trade: dict[str, Any],
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if graph_store_factory is None:
        return []
    try:
        store = graph_store_factory()
        decisions = store.get_decisions(domain, category=str(trade.get("category") or ""), limit=400)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Trading graph unavailable") from exc

    source_factors = context_router._decision_factors(trade)
    matches: list[dict[str, Any]] = []
    for candidate in decisions:
        candidate_id = str(candidate.get("decision_id") or candidate.get("trade_id") or "")
        if not candidate_id or candidate_id == str(trade_id):
            continue
        candidate_factors = context_router._decision_factors(candidate)
        names = [name for name in source_factors if name in candidate_factors]
        if not names:
            continue
        similarity = context_router._cosine_similarity(
            [source_factors[name] for name in names],
            [candidate_factors[name] for name in names],
        )
        try:
            with_outcome = store.get_decision(candidate_id, domain, include_outcome=True)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Trading graph unavailable") from exc
        resolved = with_outcome if isinstance(with_outcome, dict) else candidate
        matches.append(
            {
                "trade_id": candidate_id,
                "category": str(resolved.get("category") or ""),
                "action": str(
                    resolved.get("recommended_action")
                    or resolved.get("action")
                    or "unknown"
                ),
                "score": round(float(similarity), 6),
                "outcome": context_router._decision_outcome(resolved),
            }
        )
    matches.sort(key=lambda item: float(item["score"]), reverse=True)
    return matches[:limit]


def _counterfactual(
    trade: dict[str, Any],
    action: str,
) -> dict[str, Any] | None:
    actions = list(TradingPreset().shape.action_names)
    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    probabilities = trade.get("probabilities") or metadata.get("probabilities")
    raw_scores: dict[str, Any]
    if isinstance(probabilities, dict):
        raw_scores = {name: probabilities.get(name) for name in actions if name in probabilities}
    elif isinstance(probabilities, (list, tuple)):
        raw_scores = {
            name: probabilities[index]
            for index, name in enumerate(actions)
            if index < len(probabilities)
        }
    else:
        return None

    scores: dict[str, float] = {}
    for name, value in raw_scores.items():
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        if isfinite(score):
            scores[name] = score
    alternates = [name for name in actions if name != action and name in scores]
    if action not in scores or not alternates:
        return None

    alternate_action = max(alternates, key=scores.__getitem__)
    baseline = scores[action]
    projected = scores[alternate_action]
    return {
        "alternate_action": alternate_action,
        "projected_score": round(projected, 6),
        "delta": round(projected - baseline, 6),
    }


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

    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
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
    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_context = metadata.get("context")
    context: dict[str, Any] = raw_context if isinstance(raw_context, dict) else {}
    merged = {**trade, **metadata, **context}
    factors = trade.get("factors")
    if isinstance(factors, dict):
        nested_metadata = factors.get("metadata")
        if isinstance(nested_metadata, dict):
            merged.update(nested_metadata)
    return merged


def _factors_for(trade: dict[str, Any], context: dict[str, Any]) -> dict[str, float]:
    raw_factor_value = trade.get("factors")
    raw_factors: dict[str, Any] = raw_factor_value if isinstance(raw_factor_value, dict) else {}
    factors = {
        name: _coerce_factor(raw_factors.get(name))
        for name in ALL_FACTOR_NAMES
        if name in raw_factors
    }

    if len(factors) < len(ALL_FACTOR_NAMES):
        raw_metadata = trade.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
        raw_scored = metadata.get("scored_factors")
        scored: dict[str, Any] = raw_scored if isinstance(raw_scored, dict) else {}
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
    return cast(dict[str, float], compute_options_factors(context))


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
    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    return str(
        trade.get("action")
        or trade.get("recommended_action")
        or metadata.get("score_action")
        or metadata.get("action")
        or "unknown"
    )


def _confidence_for(trade: dict[str, Any]) -> float:
    raw_metadata = trade.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
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
