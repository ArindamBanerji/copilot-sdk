"""Read-only pre-trade decision support endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.evidence import TradingTemplateEngine
from app.factors.options import compute_options_factors
from app.factors.registry import compute_factors
from app.routers.journal import _journal_records
from app.services.regime import RegimeService
from app.services.subcategory import get_subcategory


GraphStoreFactory = Callable[[], Any]
ServiceFactory = Callable[[], RegimeService]


class PreScoreRequest(BaseModel):
    ticker: str | None = None
    direction: str = "long"
    strategy_tag: str | None = None
    category: str | None = None
    notes: str | None = None
    size_pct: float = Field(default=0.0)


def create_prescore_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
    service_factory: ServiceFactory = RegimeService,
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-prescore"])
    engine = TradingTemplateEngine()

    @router.post("/prescore")
    def prescore(request: PreScoreRequest) -> dict[str, Any]:
        ticker = str(request.ticker or "").strip().upper()
        if not ticker:
            raise HTTPException(status_code=400, detail="ticker is required")

        trades = _journal_records(graph_store_factory, domain)
        service = service_factory()
        regime = service.get_current_regime()
        current_regime = str(regime.get("regime") or "ranging")
        category = request.category or _auto_classify(request, trades)
        subcategory = get_subcategory({
            "category": category,
            "strategy_tag": request.strategy_tag,
            "direction": request.direction,
            "notes": request.notes,
        })
        accuracy = service.get_regime_accuracy(trades)
        regime_accuracy = float(accuracy.get(category, {}).get(current_regime, 0.5))
        context = _context_for(
            request=request,
            ticker=ticker,
            category=category,
            trades=trades,
            regime=regime,
            regime_accuracy=regime_accuracy,
        )
        if subcategory:
            context["subcategory"] = subcategory
        factors = compute_factors(context)
        options_factors = compute_options_factors(context) if _is_options_like(context) else None
        if options_factors:
            context["options_factors"] = options_factors
            context["options_analytics_only"] = True
        action, confidence = _local_action_confidence(factors)
        recommendation = _recommendation(confidence, regime_accuracy, factors)
        warnings = _warnings(
            category=category,
            regime=current_regime,
            regime_accuracy=regime_accuracy,
            confidence=confidence,
            context=context,
            factors=factors,
        )
        trade_dict = {
            "ticker": ticker,
            "direction": request.direction,
            "category": category,
            "strategy_tag": request.strategy_tag,
        }
        if subcategory:
            trade_dict["subcategory"] = subcategory

        response = {
            "recommendation": recommendation,
            "confidence": confidence,
            "action": action,
            "factors": factors,
            "regime": regime,
            "regime_accuracy": regime_accuracy,
            "warnings": warnings,
            "evidence": engine.render(trade_dict, factors, action, confidence, context),
            "category": category,
        }
        if subcategory:
            response["subcategory"] = subcategory
        if options_factors:
            response["options_factors"] = options_factors
            response["options_analytics_only"] = True
        return response

    return router


def _local_action_confidence(factors: dict[str, Any]) -> tuple[str, float]:
    # Pre-score evaluates hypotheticals, so it deliberately avoids scorer.score(),
    # which persists normal executed-trade decisions to GraphStore.
    values = [_clamp(value) for value in factors.values()]
    confidence = round(sum(values) / len(values), 4) if values else 0.5
    if confidence >= 0.75:
        action = "strong_execution"
    elif confidence >= 0.50:
        action = "partial_execution"
    elif confidence >= 0.30:
        action = "poor_execution"
    else:
        action = "skip_recommended"
    return action, confidence


def _recommendation(
    confidence: float,
    regime_accuracy: float,
    factors: dict[str, Any],
) -> str:
    if confidence <= 0.40 or regime_accuracy <= 0.40:
        return "skip"
    if _clamp(factors.get("emotional_indicator")) <= 0.50:
        return "reduce"
    return "proceed"


def _warnings(
    *,
    category: str,
    regime: str,
    regime_accuracy: float,
    confidence: float,
    context: dict[str, Any],
    factors: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if regime_accuracy <= 0.50:
        warnings.append(f"Your {category} accuracy in {regime}: {_percent(regime_accuracy)}")
    if _clamp(factors.get("emotional_indicator")) <= 0.50:
        warnings.append("Decision context: elevated pattern detected")
    if confidence < 0.50:
        warnings.append(f"Low confidence: {_percent(confidence)}")
    if (
        float(context.get("minutes_since_last_trade", 999.0)) < 30
        and bool(context.get("last_trade_was_loss"))
    ):
        warnings.append("Quick re-entry after loss detected")
    return warnings


def _context_for(
    *,
    request: PreScoreRequest,
    ticker: str,
    category: str,
    trades: list[dict[str, Any]],
    regime: dict[str, Any],
    regime_accuracy: float,
) -> dict[str, Any]:
    avg_size = _avg_size(trades)
    size_pct = _number(request.size_pct) or 0.0
    return {
        "trade_id": f"prescore-{ticker}-{datetime.now(timezone.utc).isoformat()}",
        "ticker": ticker,
        "direction": request.direction,
        "category": category,
        "strategy_tag": request.strategy_tag,
        "notes": request.notes,
        "current_regime": regime.get("regime") or "ranging",
        "regime_accuracy": regime_accuracy,
        "vix_at_entry": _number(regime.get("vix")) or 20.0,
        "position_size_pct": size_pct,
        "avg_position_size_pct": avg_size,
        "max_position_size_pct": 5.0,
        "minutes_since_last_trade": _minutes_since_last(trades),
        "last_trade_was_loss": _last_was_loss(trades),
        "consecutive_wins": _consecutive_wins(trades),
        "size_vs_rolling_avg": size_pct / avg_size if avg_size > 0 else 1.0,
        "entry_at_day_extreme": False,
    }


def _auto_classify(body: PreScoreRequest | dict[str, Any], trades: list[dict[str, Any]] | None = None) -> str:
    if isinstance(body, dict):
        strategy = str(body.get("strategy_tag") or body.get("strategy") or "")
        ticker = str(body.get("ticker") or "")
    else:
        strategy = str(body.strategy_tag or "")
        ticker = str(body.ticker or "")
    text = f"{strategy} {ticker}".lower()
    if any(token in text for token in ("rsi", "oversold", "overbought", "mean", "reversion")):
        return "mean_reversion"
    if any(token in text for token in ("earnings", "event", "news", "catalyst")):
        return "event_driven"
    if any(token in text for token in ("premium", "sell", "iron", "condor", "credit")):
        return "income_strategy"
    if any(token in text for token in ("scalp", "quick", "intraday")):
        return "scalp_intraday"
    return "trend_following"


def _is_options_like(context: dict[str, Any]) -> bool:
    if str(context.get("category") or "") == "income_strategy":
        return True
    text = " ".join(
        str(context.get(key) or "")
        for key in ("strategy_tag", "notes", "subcategory", "direction")
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


def _avg_size(trades: list[dict[str, Any]]) -> float:
    values = [
        value
        for trade in trades
        if (value := _trade_size_pct(trade)) is not None
    ]
    return round(sum(values) / len(values), 4) if values else 1.0


def _minutes_since_last(trades: list[dict[str, Any]]) -> float:
    latest = _latest_trade(trades)
    if latest is None:
        return 999.0
    timestamp = _parse_time(latest.get("entry_time") or latest.get("metadata", {}).get("entry_time"))
    if timestamp is None:
        return 999.0
    delta = datetime.now(timezone.utc) - timestamp
    return max(0.0, round(delta.total_seconds() / 60.0, 2))


def _last_was_loss(trades: list[dict[str, Any]]) -> bool:
    latest = _latest_trade(trades)
    if latest is None:
        return False
    pnl = _trade_pnl(latest)
    return pnl is not None and pnl <= 0


def _consecutive_wins(trades: list[dict[str, Any]]) -> int:
    count = 0
    for trade in sorted(trades, key=_trade_sort_key, reverse=True):
        pnl = _trade_pnl(trade)
        if pnl is None or pnl <= 0:
            break
        count += 1
    return count


def _latest_trade(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not trades:
        return None
    return sorted(trades, key=_trade_sort_key, reverse=True)[0]


def _trade_sort_key(trade: dict[str, Any]) -> str:
    timestamp = _parse_time(trade.get("entry_time") or trade.get("metadata", {}).get("entry_time"))
    return timestamp.isoformat() if timestamp else ""


def _trade_size_pct(trade: dict[str, Any]) -> float | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    for key in ("size_pct", "position_size_pct", "exposure_pct", "size"):
        value = trade.get(key) if key in trade else metadata.get(key)
        number = _number(value)
        if number is not None:
            return number
    return None


def _trade_pnl(trade: dict[str, Any]) -> float | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    for key in ("pnl", "pnl_dollars"):
        value = trade.get(key) if key in trade else metadata.get(key)
        number = _number(value)
        if number is not None:
            return number
    return None


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _clamp(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return max(0.0, min(number, 1.0))


def _percent(value: float) -> str:
    return f"{round(float(value) * 100)}%"
