"""TradingView webhook intake for execution-quality scoring."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import math
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from copilot_sdk.scoring.mutation_lock import serialize_mutation
from copilot_sdk.state.cached_static import cached_static


TRADING_CATEGORIES = (
    "trend_following",
    "mean_reversion",
    "event_driven",
    "income_strategy",
    "scalp_intraday",
)
TRADING_ACTIONS = (
    "strong_execution",
    "partial_execution",
    "poor_execution",
    "skip_recommended",
)
TRADING_FACTORS = (
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
)
DEFAULT_CATEGORY = "trend_following"
HISTORY_LIMIT = 100
_WEBHOOK_HISTORY: deque[dict[str, Any]] = deque(maxlen=HISTORY_LIMIT)


class TradingViewWebhookRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    action: str | None = None
    price: float | None = None
    time: str | None = None
    interval: str | None = None
    exchange: str | None = None
    strategy: str | None = None
    category: str | None = None
    auto_score: bool = False
    indicators: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ticker")
    def ticker_required(cls, value: str) -> str:
        ticker = str(value or "").strip().upper()
        if not ticker:
            raise ValueError("ticker is required")
        return ticker

    @field_validator("price")
    def price_must_be_finite(cls, value: float | None) -> float | None:
        if value is None:
            return None
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("price must be finite")
        return number

    @field_validator("action")
    def normalize_action(cls, value: str | None) -> str | None:
        text = str(value or "").strip().lower()
        return text or None


def create_webhook_router(scorer_proxy: Any) -> APIRouter:
    router = APIRouter(prefix="/api/trading/webhook", tags=["trading-webhook"])
    history = _WEBHOOK_HISTORY

    @router.post("/tradingview")
    @serialize_mutation("trading", event="score")
    def tradingview_webhook(request: TradingViewWebhookRequest) -> dict[str, Any]:
        received_at = _now()
        category = _normalize_category(request.category, request.strategy)
        mapped_factors = map_tradingview_factors(request.indicators)
        event_id = _event_id(request, received_at, category, mapped_factors)
        response: dict[str, Any] = {
            "received": True,
            "event_id": event_id,
            "scored": False,
            "ticker": request.ticker,
            "mapped_factors": mapped_factors,
        }
        history_item: dict[str, Any] = {
            "event_id": event_id,
            "received_at": received_at,
            "ticker": request.ticker,
            "action": request.action,
            "category": category,
            "auto_score": bool(request.auto_score),
            "scored": False,
            "mapped_factors": mapped_factors,
        }

        if request.auto_score:
            scored = _score_event(
                scorer_proxy=scorer_proxy,
                factors=mapped_factors,
                category=category,
                request=request,
                event_id=event_id,
                received_at=received_at,
            )
            response.update(scored)
            history_item.update({
                "scored": bool(scored.get("scored")),
                "decision_id": scored.get("decision_id"),
                "recommendation": scored.get("recommendation"),
                "confidence": scored.get("confidence"),
                "auto_score_status": scored.get("auto_score_status"),
            })

        history.appendleft(_json_safe(history_item))
        return _json_safe(response)

    @router.get("/history")
    @cached_static("webhook-history")
    def webhook_history(request: Request) -> list[dict[str, Any]]:
        return list(history)

    @router.get("/config")
    def webhook_config() -> dict[str, Any]:
        return {
            "auto_score": False,
            "default_category": DEFAULT_CATEGORY,
            "factor_mapping": {
                "rsi": "signal_alignment",
                "macd": "signal_confidence",
                "atr": "position_sizing",
                "volume": "timing_quality",
                "vix": "market_regime",
                "risk_reward": "risk_reward_actual",
                "emotional_indicator": "emotional_indicator",
            },
            "valid_categories": list(TRADING_CATEGORIES),
            "valid_actions": list(TRADING_ACTIONS),
            "valid_factors": list(TRADING_FACTORS),
            "history_limit": HISTORY_LIMIT,
            "source": "app-local",
        }

    @router.post("/test")
    def test_webhook(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = dict(payload or {})
        sample = {
            "ticker": body.get("ticker") or "AAPL",
            "action": body.get("action") or "buy",
            "price": body.get("price") or 150.25,
            "time": body.get("time") or "2026-05-27T10:30:00Z",
            "interval": body.get("interval") or "1h",
            "exchange": body.get("exchange") or "NASDAQ",
            "strategy": body.get("strategy") or "RSI_Oversold",
            "category": body.get("category") or "mean_reversion",
            "auto_score": bool(body.get("auto_score", False)),
            "indicators": body.get("indicators")
            or {"rsi": 28.5, "macd": -0.3, "atr": 2.1, "volume": 1_500_000, "vix": 18.2},
        }
        request = TradingViewWebhookRequest(**sample)
        return tradingview_webhook(request)

    return router


def compute_webhook_status() -> dict[str, Any]:
    history = list(_WEBHOOK_HISTORY)
    last_alert = history[0] if history else None
    fast = [
        alert for alert in history
        if _number(alert.get("time_to_trade_seconds") or alert.get("timeToTradeSeconds")) is not None
        and _number(alert.get("time_to_trade_seconds") or alert.get("timeToTradeSeconds")) < 300
    ]
    slow = [
        alert for alert in history
        if _number(alert.get("time_to_trade_seconds") or alert.get("timeToTradeSeconds")) is not None
        and _number(alert.get("time_to_trade_seconds") or alert.get("timeToTradeSeconds")) > 1800
    ]
    return {
        "total_alerts": len(history),
        "correlated_trades": len([alert for alert in history if alert.get("scored")]),
        "last_alert": last_alert,
        "last_received": last_alert.get("received_at") if isinstance(last_alert, dict) else None,
        "fast_accuracy": _speed_accuracy(fast),
        "slow_accuracy": _speed_accuracy(slow),
        "health": "active" if history else "waiting",
    }


def _speed_accuracy(alerts: list[dict[str, Any]]) -> float | None:
    labeled = [
        alert for alert in alerts
        if isinstance(alert.get("is_correct", alert.get("isCorrect")), bool)
    ]
    if not labeled:
        return None
    correct = len([alert for alert in labeled if bool(alert.get("is_correct", alert.get("isCorrect")))])
    return round(correct / len(labeled), 4)


def map_tradingview_factors(indicators: dict[str, Any] | None) -> dict[str, float]:
    values = indicators or {}
    factors = {factor: 0.5 for factor in TRADING_FACTORS}
    factors["signal_alignment"] = _rsi_signal(values.get("rsi"))
    factors["signal_confidence"] = _macd_confidence(values.get("macd"))
    factors["position_sizing"] = _atr_sizing(values.get("atr"))
    factors["timing_quality"] = _volume_timing(values.get("volume"))
    factors["market_regime"] = _vix_regime(values.get("vix"))
    factors["risk_reward_actual"] = _bounded_number(
        values.get("risk_reward") or values.get("risk_reward_actual") or values.get("rr")
    )
    factors["emotional_indicator"] = _bounded_number(values.get("emotional_indicator"))
    return {factor: _clamp(score) for factor, score in factors.items()}


def _score_event(
    *,
    scorer_proxy: Any,
    factors: dict[str, float],
    category: str,
    request: TradingViewWebhookRequest,
    event_id: str,
    received_at: str,
) -> dict[str, Any]:
    current_regime = _current_regime_from_indicators(request.indicators)
    try:
        result = scorer_proxy.score(
            factors,
            category,
            metadata={
                "source": "tradingview_webhook",
                "webhook_event_id": event_id,
                "ticker": request.ticker,
                "exchange": request.exchange,
                "interval": request.interval,
                "strategy": request.strategy,
                "alert_action": request.action,
                "received_at": received_at,
                "current_regime": current_regime,
            },
        )
    except (AssertionError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        return {"scored": False, "auto_score_status": "auto_score_unavailable"}

    payload = _json_safe(result)
    if not isinstance(payload, dict):
        payload = {}
    recommendation = str(payload.get("action") or "")
    if recommendation not in TRADING_ACTIONS:
        recommendation = "partial_execution"
    return {
        "scored": True,
        "decision_id": payload.get("decision_id"),
        "recommendation": recommendation,
        "confidence": _clamp(payload.get("confidence")),
        "auto_score_status": "scored",
    }


def _current_regime_from_indicators(indicators: dict[str, Any] | None) -> str | None:
    try:
        from app.services.regime_classifier import RegimeClassifier

        values = indicators or {}
        vix = _number(values.get("vix"))
        adx = _number(values.get("adx"))
        if vix is None or adx is None:
            return None
        return RegimeClassifier().classify(vix, adx)
    except Exception:
        return None


def _normalize_category(category: str | None, strategy: str | None) -> str:
    text = str(category or "").strip()
    if text in TRADING_CATEGORIES:
        return text
    strategy_text = str(strategy or "").lower()
    if any(token in strategy_text for token in ("rsi", "mean", "oversold", "overbought")):
        return "mean_reversion"
    if any(token in strategy_text for token in ("event", "earnings", "news")):
        return "event_driven"
    if any(token in strategy_text for token in ("income", "premium", "credit", "option")):
        return "income_strategy"
    if any(token in strategy_text for token in ("scalp", "intraday")):
        return "scalp_intraday"
    return DEFAULT_CATEGORY


def _event_id(
    request: TradingViewWebhookRequest,
    received_at: str,
    category: str,
    mapped_factors: dict[str, float],
) -> str:
    seed = {
        "ticker": request.ticker,
        "time": request.time,
        "received_at": received_at,
        "category": category,
        "factors": mapped_factors,
    }
    digest = hashlib.sha256(repr(sorted(seed.items())).encode("utf-8")).hexdigest()[:16]
    return f"tv-{digest}"


def _rsi_signal(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return 1.0 - min(abs(number - 50.0), 50.0) / 50.0


def _macd_confidence(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return 0.5 + math.tanh(number) / 2.0


def _atr_sizing(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return 1.0 / (1.0 + max(number, 0.0) / 5.0)


def _volume_timing(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return min(math.log10(max(number, 1.0)) / 7.0, 1.0)


def _vix_regime(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return 1.0 - min(max(number, 0.0), 50.0) / 50.0


def _bounded_number(value: Any) -> float:
    number = _number(value)
    return 0.5 if number is None else number


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _clamp(value: Any) -> float:
    number = _number(value)
    if number is None:
        return 0.5
    return round(max(0.0, min(number, 1.0)), 6)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, deque)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            pass
    return value
