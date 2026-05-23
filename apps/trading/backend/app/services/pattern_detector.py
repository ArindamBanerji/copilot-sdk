"""Behavioral pattern detection for imported Trading trades."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def detect_patterns(trades: list[dict]) -> list[dict]:
    normalized = [_as_trade_dict(trade) for trade in trades]
    normalized = [trade for trade in normalized if trade]
    if len(normalized) < 5:
        return []

    ordered = sorted(
        normalized,
        key=lambda trade: _parse_time(trade.get("entry_time")) or datetime.max,
    )
    detectors = (
        _detect_revenge,
        _detect_overconfidence,
        _detect_fomo,
        _detect_tilt,
        _detect_drawdown_chase,
    )
    patterns = [pattern for detector in detectors if (pattern := detector(ordered))]
    patterns.sort(key=lambda pattern: pattern["severity"], reverse=True)
    return patterns


def _as_trade_dict(trade: Any) -> dict[str, Any]:
    if isinstance(trade, dict):
        return trade
    if hasattr(trade, "to_dict"):
        candidate = trade.to_dict()
        return candidate if isinstance(candidate, dict) else {}
    return {}


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _minutes_between(t1: dict[str, Any], t2: dict[str, Any]) -> float | None:
    left = _parse_time(t1.get("exit_time"))
    right = _parse_time(t2.get("entry_time"))
    if left is None or right is None:
        return None
    return (right - left).total_seconds() / 60.0


def _clamp(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def _trade_id(trade: dict[str, Any]) -> str:
    return str(trade.get("trade_id") or trade.get("id") or "unknown")


def _number(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric


def _pnl(trade: dict[str, Any]) -> float | None:
    value = _number(trade.get("pnl"))
    if value is not None:
        return value
    return _number(trade.get("computed_pnl"))


def _is_loss(trade: dict[str, Any]) -> bool:
    value = _pnl(trade)
    return value is not None and value < 0


def _is_win(trade: dict[str, Any]) -> bool:
    value = _pnl(trade)
    return value is not None and value > 0


def _size(trade: dict[str, Any]) -> float | None:
    return _number(trade.get("size"))


def _pattern(
    *,
    name: str,
    display_name: str,
    description: str,
    affected: list[dict[str, Any]],
    severity: float,
    recommendation: str,
    total: int,
) -> dict[str, Any]:
    affected_ids = [_trade_id(trade) for trade in affected]
    return {
        "name": name,
        "display_name": display_name,
        "description": description,
        "frequency": round(len(affected) / total, 4) if total else 0.0,
        "severity": round(_clamp(severity), 4),
        "affected_trade_count": len(affected),
        "affected_trades": affected_ids[:10],
        "recommendation": recommendation,
    }


def _detect_revenge(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    affected: list[dict[str, Any]] = []
    for previous, current in zip(trades, trades[1:]):
        if previous.get("exit_time") is None:
            continue
        if not _is_loss(previous):
            continue
        minutes = _minutes_between(previous, current)
        if minutes is None or minutes < 0 or minutes > 30:
            continue
        affected.append(current)

    if not affected:
        return None
    return _pattern(
        name="revenge_trading",
        display_name="Revenge Trading",
        description="New trades were opened shortly after closed losses.",
        affected=affected,
        severity=min(1.0, 0.35 + len(affected) / 5),
        recommendation="Add a cooldown after realized losses before opening the next trade.",
        total=len(trades),
    )


def _detect_overconfidence(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    affected: list[dict[str, Any]] = []
    win_streak = 0
    prior_sizes: list[float] = []

    for trade in trades:
        size = _size(trade)
        if win_streak >= 3 and _is_oversized_after_streak(trade, prior_sizes):
            affected.append(trade)

        if _is_win(trade):
            win_streak += 1
        elif _is_loss(trade):
            win_streak = 0

        if size is not None:
            prior_sizes.append(size)

    if not affected:
        return None
    return _pattern(
        name="overconfidence",
        display_name="Overconfidence",
        description="Trade size increased after a winning streak.",
        affected=affected,
        severity=min(1.0, 0.3 + len(affected) / 4),
        recommendation="Cap size increases after winning streaks until the setup quality is independently confirmed.",
        total=len(trades),
    )


def _is_oversized_after_streak(trade: dict[str, Any], prior_sizes: list[float]) -> bool:
    ratio = _number(trade.get("size_vs_rolling_avg"))
    if ratio is not None:
        return ratio > 1.3
    size = _size(trade)
    if size is None or not prior_sizes:
        return False
    rolling_average = sum(prior_sizes[-5:]) / len(prior_sizes[-5:])
    return rolling_average > 0 and size / rolling_average > 1.3


def _detect_fomo(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    affected = [trade for trade in trades if bool(trade.get("entry_at_day_extreme"))]
    if not affected:
        return None
    return _pattern(
        name="fomo",
        display_name="FOMO",
        description="Entries cluster at day extremes.",
        affected=affected,
        severity=min(1.0, len(affected) / max(len(trades), 1) + 0.2),
        recommendation="Require a pre-defined pullback or breakout rule before entering at day extremes.",
        total=len(trades),
    )


def _detect_tilt(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        parsed = _parse_time(trade.get("entry_time"))
        if parsed is not None:
            key = parsed.strftime("%Y-%m-%dT%H")
        else:
            raw = str(trade.get("entry_time") or "")
            key = raw[:13] if len(raw) >= 13 else ""
        if not key:
            continue
        buckets.setdefault(key, []).append(trade)

    affected = [
        trade
        for bucket in buckets.values()
        if len(bucket) >= 3
        for trade in bucket
    ]
    if not affected:
        return None
    return _pattern(
        name="tilt",
        display_name="Tilt",
        description="Three or more trades occurred within the same hour.",
        affected=affected,
        severity=min(1.0, 0.25 + len(affected) / max(len(trades), 1)),
        recommendation="Pause after rapid-fire trade clusters and review whether the next setup is independent.",
        total=len(trades),
    )


def _detect_drawdown_chase(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    affected: list[dict[str, Any]] = []
    for previous, current in zip(trades, trades[1:]):
        if not bool(current.get("in_drawdown")):
            continue
        size_ratio = _number(current.get("size_vs_rolling_avg"))
        if size_ratio is not None and size_ratio > 1.2:
            affected.append(current)
            continue
        previous_size = _size(previous)
        current_size = _size(current)
        if previous_size is None or current_size is None or previous_size <= 0:
            continue
        if current_size / previous_size > 1.2:
            affected.append(current)

    if not affected:
        return None
    return _pattern(
        name="drawdown_chase",
        display_name="Drawdown Chase",
        description="Position size increased while the account was in drawdown.",
        affected=affected,
        severity=min(1.0, 0.35 + len(affected) / 5),
        recommendation="Use fixed or reduced size during drawdowns until the equity curve stabilizes.",
        total=len(trades),
    )
