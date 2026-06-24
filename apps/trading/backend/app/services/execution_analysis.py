"""Execution quality analysis for broker fills."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median
from typing import Any


@dataclass(frozen=True)
class BrokerStats:
    broker: str
    trade_count: int
    avg_slippage: float
    median_slippage: float
    total_slippage_cost: float
    fill_rate: float
    avg_fill_time_seconds: float | None


@dataclass(frozen=True)
class ExecutionComparison:
    brokers: list[BrokerStats]
    best_broker: str
    annual_savings_estimate: float
    recommendation: str


class ExecutionAnalyzer:
    """Compare broker fill quality using realized slippage."""

    def analyze(self, trades: list[dict[str, Any]]) -> ExecutionComparison:
        groups: dict[str, list[dict[str, Any]]] = {}
        for trade in trades:
            broker = _text(_pick(trade, "broker", "execution_broker", "source")) or "unknown"
            groups.setdefault(broker, []).append(trade)

        brokers = [
            self._compute_broker_stats(broker, rows)
            for broker, rows in sorted(groups.items(), key=lambda item: item[0])
        ]
        if not brokers:
            return ExecutionComparison(
                brokers=[],
                best_broker="",
                annual_savings_estimate=0.0,
                recommendation="No execution data yet",
            )

        ranked = sorted(brokers, key=lambda stat: (stat.avg_slippage, -stat.fill_rate, stat.broker))
        best = ranked[0]
        worst = ranked[-1]
        annual_savings = self._annual_savings(trades, best.avg_slippage, worst.avg_slippage)
        if len(brokers) < 2 or annual_savings <= 0:
            recommendation = f"{best.broker} currently has the best fill quality."
        else:
            recommendation = (
                f"Switching to {best.broker} could save about ${annual_savings:,.0f}/year "
                f"(estimated from {len(trades)} trades over sample period)."
            )
        return ExecutionComparison(
            brokers=brokers,
            best_broker=best.broker,
            annual_savings_estimate=annual_savings,
            recommendation=recommendation,
        )

    def _compute_broker_stats(self, broker: str, trades: list[dict[str, Any]]) -> BrokerStats:
        slippages: list[float] = []
        slippage_costs: list[float] = []
        fill_times: list[float] = []
        filled = 0

        for trade in trades:
            fill_price = _number(_pick(trade, "fill_price", "filled_avg_price", "avg_fill_price", "entry_price"))
            if fill_price is not None and _is_filled(trade):
                filled += 1

            reference = _number(_pick(trade, "mid_price", "market_mid_price"))
            if reference is None:
                reference = _number(_pick(trade, "limit_price", "order_limit_price", "expected_entry_price"))
            if fill_price is not None and reference is not None:
                slippage = abs(fill_price - reference)
                slippages.append(slippage)
                slippage_costs.append(slippage * _quantity(trade))

            fill_time = _fill_time_seconds(trade)
            if fill_time is not None:
                fill_times.append(fill_time)

        trade_count = len(trades)
        return BrokerStats(
            broker=broker,
            trade_count=trade_count,
            avg_slippage=mean(slippages) if slippages else 0.0,
            median_slippage=median(slippages) if slippages else 0.0,
            total_slippage_cost=sum(slippage_costs),
            fill_rate=filled / trade_count if trade_count else 0.0,
            avg_fill_time_seconds=mean(fill_times) if fill_times else None,
        )

    def _annual_savings(self, trades: list[dict[str, Any]], best: float, worst: float) -> float:
        delta = max(0.0, worst - best)
        if delta <= 0:
            return 0.0
        avg_qty = mean([_quantity(trade) for trade in trades]) if trades else 1.0
        trades_per_year = max(len(trades), 1) * 12
        return delta * avg_qty * trades_per_year


def _pick(trade: dict[str, Any], *keys: str) -> Any:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    nested_metadata = [
        metadata.get("order"),
        metadata.get("alpaca_order"),
        metadata.get("raw"),
        metadata.get("execution"),
    ]
    for key in keys:
        if trade.get(key) is not None:
            return trade.get(key)
        if metadata.get(key) is not None:
            return metadata.get(key)
        for nested in nested_metadata:
            if isinstance(nested, dict) and nested.get(key) is not None:
                return nested.get(key)
    return None


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quantity(trade: dict[str, Any]) -> float:
    value = _number(_pick(trade, "quantity", "qty", "filled_qty", "size", "shares"))
    return value if value is not None and value > 0 else 1.0


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _is_filled(trade: dict[str, Any]) -> bool:
    status = str(_pick(trade, "status") or "").lower()
    if status:
        return status in {"filled", "closed", "executed", "complete", "completed"}
    return _pick(trade, "fill_price", "filled_avg_price", "avg_fill_price", "entry_price") is not None


def _fill_time_seconds(trade: dict[str, Any]) -> float | None:
    explicit = _number(_pick(trade, "fill_time_seconds", "latency_seconds"))
    if explicit is not None:
        return explicit
    submitted = _parse_time(_pick(trade, "submitted_at", "created_at", "signal_time"))
    filled = _parse_time(_pick(trade, "filled_at", "executed_at", "entry_time"))
    if submitted is None or filled is None:
        return None
    return max(0.0, (filled - submitted).total_seconds())


def _parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
