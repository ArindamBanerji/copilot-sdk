"""Behavioral pattern detection for imported Trading trades."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import math
from typing import Any

from scipy import stats


SIGNIFICANCE_THRESHOLD = 0.05
MIN_STAT_GROUP = 5


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
        _detect_tod_degradation,
        _detect_regime_dependency,
        _detect_sizing_drift,
    )
    patterns = [pattern for detector in detectors if (pattern := detector(ordered))]
    patterns.sort(key=_pattern_sort_key)
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
        if value.tzinfo is None:
            return value
        parsed = value
    elif not value:
        return None
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


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


def _accuracy(trades: list[dict[str, Any]]) -> float | None:
    outcomes = [_outcome(trade) for trade in trades]
    verified = [outcome for outcome in outcomes if outcome is not None]
    if not verified:
        return None
    return sum(1 for outcome in verified if outcome) / len(verified)


def _is_loss(trade: dict[str, Any]) -> bool:
    value = _pnl(trade)
    return value is not None and value < 0


def _is_win(trade: dict[str, Any]) -> bool:
    value = _pnl(trade)
    return value is not None and value > 0


def _size(trade: dict[str, Any]) -> float | None:
    return _number(trade.get("size"))


def _outcome(trade: dict[str, Any]) -> bool | None:
    if trade.get("is_correct") is not None:
        return bool(trade.get("is_correct"))
    value = _pnl(trade)
    if value is None:
        return None
    if value > 0:
        return True
    if value < 0:
        return False
    return None


def _outcome_counts(trades: list[dict[str, Any]]) -> tuple[int, int]:
    correct = 0
    incorrect = 0
    for trade in trades:
        outcome = _outcome(trade)
        if outcome is True:
            correct += 1
        elif outcome is False:
            incorrect += 1
    return correct, incorrect


def _pattern_sort_key(pattern: dict[str, Any]) -> tuple[int, float, float]:
    p_value = pattern.get("p_value")
    if p_value is not None:
        return (0, float(p_value), -float(pattern.get("severity") or 0.0))
    return (1, 1.0, -float(pattern.get("severity") or 0.0))


def _fisher_comparison(
    affected: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
) -> dict[str, Any] | None:
    affected_correct, affected_incorrect = _outcome_counts(affected)
    baseline_correct, baseline_incorrect = _outcome_counts(baseline)
    affected_total = affected_correct + affected_incorrect
    baseline_total = baseline_correct + baseline_incorrect
    if affected_total < MIN_STAT_GROUP or baseline_total < MIN_STAT_GROUP:
        return None

    affected_acc = affected_correct / affected_total
    baseline_acc = baseline_correct / baseline_total
    _, p_value = stats.fisher_exact(
        [
            [affected_correct, affected_incorrect],
            [baseline_correct, baseline_incorrect],
        ],
        alternative="less",
    )
    return {
        "affected_acc": affected_acc,
        "baseline_acc": baseline_acc,
        "p_value": float(p_value),
        "accuracy_delta": max(0.0, baseline_acc - affected_acc),
    }


def _chi_squared(rows: list[list[int]]) -> float | None:
    try:
        _, p_value, _, _ = stats.chi2_contingency(rows)
    except ValueError:
        return None
    return float(p_value)


def _avg_trade_size(trades: list[dict[str, Any]]) -> float:
    pnl_values = [abs(value) for trade in trades if (value := _pnl(trade)) is not None]
    if pnl_values:
        return sum(pnl_values) / len(pnl_values)
    size_values = [abs(value) for trade in trades if (value := _size(trade)) is not None]
    return sum(size_values) / len(size_values) if size_values else 0.0


def _avg_loss(trades: list[dict[str, Any]]) -> float | None:
    losses = [
        abs(value)
        for trade in trades
        if (value := _pnl(trade)) is not None and value < 0
    ]
    return sum(losses) / len(losses) if losses else None


def _annualized_count(trades: list[dict[str, Any]]) -> float:
    parsed = [
        timestamp
        for trade in trades
        if (timestamp := _parse_time(trade.get("entry_time"))) is not None
    ]
    if len(parsed) < 2:
        return float(len(trades))
    span_days = max((max(parsed) - min(parsed)).total_seconds() / 86400.0, 1.0)
    return len(trades) / span_days * 252.0


def _cost_payload(
    *,
    accuracy_delta: float,
    affected_count: int,
    total: int,
    trades: list[dict[str, Any]],
) -> tuple[float | None, dict[str, float]]:
    trades_per_year_fraction = affected_count / total if total else 0.0
    avg_loss = _avg_loss(trades)
    avg_trade_size = _avg_trade_size(trades)
    cost = (
        max(0.0, accuracy_delta) * affected_count * avg_loss
        if avg_loss is not None
        else None
    )
    return round(cost, 2) if cost is not None else None, {
        "accuracy_delta": round(max(0.0, accuracy_delta), 4),
        "affected_count": affected_count,
        "avg_loss": round(avg_loss, 4) if avg_loss is not None else None,
        "trades_per_year_fraction": round(trades_per_year_fraction, 4),
        "affected_frequency": round(trades_per_year_fraction, 4),
        "avg_trade_size": round(avg_trade_size, 4),
    }


def _pattern(
    *,
    name: str,
    display_name: str,
    description: str,
    affected: list[dict[str, Any]],
    severity: float,
    recommendation: str,
    total: int,
    p_value: float | None = None,
    estimated_annual_cost: float | None = None,
    cost_components: dict[str, float] | None = None,
    statistical_test: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    affected_ids = [_trade_id(trade) for trade in affected]
    significant = p_value is not None and p_value < SIGNIFICANCE_THRESHOLD
    pattern = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "frequency": round(len(affected) / total, 4) if total else 0.0,
        "severity": round(_clamp(severity), 4),
        "affected_trade_count": len(affected),
        "affected_trades": affected_ids[:10],
        "recommendation": recommendation,
        "p_value": round(float(p_value), 6) if p_value is not None else None,
        "significant": significant,
        "estimated_annual_cost": estimated_annual_cost,
        "cost_components": cost_components,
        "statistical_test": statistical_test,
    }
    if extra:
        pattern.update(extra)
    return pattern


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

    affected_ids = {id(trade) for trade in affected}
    baseline = [trade for trade in trades if id(trade) not in affected_ids]
    comparison = _fisher_comparison(affected, baseline)
    p_value = None
    estimated_cost = None
    cost_components = None
    if comparison is not None:
        if comparison["accuracy_delta"] <= 0 or comparison["p_value"] >= SIGNIFICANCE_THRESHOLD:
            return None
        p_value = comparison["p_value"]
        estimated_cost, cost_components = _cost_payload(
            accuracy_delta=comparison["accuracy_delta"],
            affected_count=len(affected),
            total=len(trades),
            trades=trades,
        )

    return _pattern(
        name="revenge_trading",
        display_name="Revenge Trading",
        description="New trades were opened shortly after closed losses.",
        affected=affected,
        severity=min(1.0, 0.35 + len(affected) / 5),
        recommendation="Add a cooldown after realized losses before opening the next trade.",
        total=len(trades),
        p_value=p_value,
        estimated_annual_cost=estimated_cost,
        cost_components=cost_components,
        statistical_test="fisher_exact" if p_value is not None else None,
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

    affected_ids = {id(trade) for trade in affected}
    baseline = [trade for trade in trades if id(trade) not in affected_ids]
    comparison = _fisher_comparison(affected, baseline)
    p_value = None
    estimated_cost = None
    cost_components = None
    if comparison is not None:
        if comparison["accuracy_delta"] <= 0 or comparison["p_value"] >= SIGNIFICANCE_THRESHOLD:
            return None
        p_value = comparison["p_value"]
        estimated_cost, cost_components = _cost_payload(
            accuracy_delta=comparison["accuracy_delta"],
            affected_count=len(affected),
            total=len(trades),
            trades=trades,
        )

    return _pattern(
        name="overconfidence",
        display_name="Overconfidence",
        description="Trade size increased after a winning streak.",
        affected=affected,
        severity=min(1.0, 0.3 + len(affected) / 4),
        recommendation="Cap size increases after winning streaks until the setup quality is independently confirmed.",
        total=len(trades),
        p_value=p_value,
        estimated_annual_cost=estimated_cost,
        cost_components=cost_components,
        statistical_test="fisher_exact" if p_value is not None else None,
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


def _detect_tod_degradation(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(trades) < 10:
        return None

    baseline_acc = _accuracy(trades)
    if baseline_acc is None:
        return None

    session_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        if _outcome(trade) is None:
            continue
        session = _market_session(trade)
        if session is not None:
            session_buckets[session].append(trade)

    qualified = {
        session: rows
        for session, rows in session_buckets.items()
        if len(rows) >= 10
    }
    if len(qualified) >= 2:
        table: list[list[int]] = []
        for rows in qualified.values():
            correct, incorrect = _outcome_counts(rows)
            table.append([correct, incorrect])
        p_value = _chi_squared(table)
        if p_value is None or p_value >= SIGNIFICANCE_THRESHOLD:
            return None

        worst_session = min(
            qualified,
            key=lambda session: _accuracy(qualified[session]) or 1.0,
        )
        worst_trades = qualified[worst_session]
        worst_acc = _accuracy(worst_trades) or 0.0
        worst_gap = baseline_acc - worst_acc
        if worst_gap <= 0:
            return None

        estimated_cost, cost_components = _cost_payload(
            accuracy_delta=worst_gap,
            affected_count=len(worst_trades),
            total=len(trades),
            trades=trades,
        )
        return _pattern(
            name="tod_degradation",
            display_name="Time-of-Day Degradation",
            description=(
                f"{worst_session.title()} session accuracy is {worst_acc:.0%}, below the "
                f"{baseline_acc:.0%} verified baseline by {worst_gap:.0%}."
            ),
            affected=worst_trades,
            severity=min(1.0, 0.3 + worst_gap * 2),
            recommendation=(
                f"Review {worst_session} session setups and reduce size or skip that "
                "window until accuracy recovers."
            ),
            total=len(trades),
            p_value=p_value,
            estimated_annual_cost=estimated_cost,
            cost_components=cost_components,
            statistical_test="chi_squared",
            extra={"worst_session": worst_session},
        )

    return _detect_tod_degradation_heuristic(trades, baseline_acc)


def _detect_tod_degradation_heuristic(
    trades: list[dict[str, Any]],
    baseline_acc: float,
) -> dict[str, Any] | None:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        if _outcome(trade) is None:
            continue
        parsed = _parse_time(trade.get("entry_time"))
        if parsed is None:
            continue
        key = f"{parsed.strftime('%A')}_{parsed.hour:02d}"
        buckets[key].append(trade)

    worst_key: str | None = None
    worst_trades: list[dict[str, Any]] = []
    worst_gap = 0.0
    worst_acc = 0.0

    for key, bucket_trades in buckets.items():
        if len(bucket_trades) < 8:
            continue
        bucket_acc = _accuracy(bucket_trades)
        if bucket_acc is None:
            continue
        gap = baseline_acc - bucket_acc
        if gap > worst_gap:
            worst_key = key
            worst_trades = bucket_trades
            worst_gap = gap
            worst_acc = bucket_acc

    if worst_key is None or worst_gap < 0.12:
        return None

    day_name, hour_text = worst_key.rsplit("_", 1)
    hour = int(hour_text)
    next_hour = (hour + 1) % 24
    window = f"{hour:02d}:00-{next_hour:02d}:00"
    gap_text = f"{worst_gap:.0%}"

    return _pattern(
        name="tod_degradation",
        display_name="Time-of-Day Degradation",
        description=(
            f"{day_name} {window} accuracy is {worst_acc:.0%}, below the "
            f"{baseline_acc:.0%} verified baseline by {gap_text}."
        ),
        affected=worst_trades,
        severity=min(1.0, 0.3 + worst_gap * 2),
        recommendation=(
            f"Review {day_name} {window} setups and reduce size or skip that window "
            "until accuracy recovers."
        ),
        total=len(trades),
    )


def _market_session(trade: dict[str, Any]) -> str | None:
    parsed = _parse_time(trade.get("entry_time"))
    if parsed is None:
        return None
    value = parsed.hour + parsed.minute / 60.0
    if 9.5 <= value < 12.0:
        return "morning"
    if 12.0 <= value < 14.0:
        return "afternoon"
    if 14.0 <= value < 16.0:
        return "late"
    return None


def _detect_regime_dependency(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        if _outcome(trade) is None:
            continue
        regime = _regime(trade)
        if regime:
            buckets[regime].append(trade)

    qualified = {
        regime: rows
        for regime, rows in buckets.items()
        if len(rows) >= MIN_STAT_GROUP
    }
    if len(qualified) < 2:
        return None

    table: list[list[int]] = []
    for rows in qualified.values():
        correct, incorrect = _outcome_counts(rows)
        table.append([correct, incorrect])
    p_value = _chi_squared(table)
    if p_value is None or p_value >= SIGNIFICANCE_THRESHOLD:
        return None

    baseline_acc = _accuracy([trade for rows in qualified.values() for trade in rows])
    if baseline_acc is None:
        return None
    worst_regime = min(
        qualified,
        key=lambda regime: _accuracy(qualified[regime]) or 1.0,
    )
    worst_trades = qualified[worst_regime]
    worst_acc = _accuracy(worst_trades) or 0.0
    gap = baseline_acc - worst_acc
    if gap <= 0:
        return None

    estimated_cost, cost_components = _cost_payload(
        accuracy_delta=gap,
        affected_count=len(worst_trades),
        total=len(trades),
        trades=trades,
    )
    return _pattern(
        name="regime_dependency",
        display_name="Regime Dependency",
        description=(
            f"{worst_regime} regime accuracy is {worst_acc:.0%}, below the "
            f"{baseline_acc:.0%} regime-tagged baseline by {gap:.0%}."
        ),
        affected=worst_trades,
        severity=min(1.0, 0.3 + gap * 2),
        recommendation=f"Reduce size or require confirmation in {worst_regime} regimes until the edge recovers.",
        total=len(trades),
        p_value=p_value,
        estimated_annual_cost=estimated_cost,
        cost_components=cost_components,
        statistical_test="chi_squared",
        extra={"worst_regime": worst_regime},
    )


def _regime(trade: dict[str, Any]) -> str | None:
    value = (
        trade.get("current_regime")
        or trade.get("regime")
        or trade.get("market_regime")
    )
    text = str(value or "").strip().lower()
    return text or None


def _detect_sizing_drift(trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows: list[tuple[dict[str, Any], float, int]] = []
    for trade in trades:
        size = _size(trade)
        outcome = _outcome(trade)
        if size is not None and outcome is not None:
            rows.append((trade, size, 1 if outcome else 0))
    if len(rows) < 20:
        return None

    indexes = list(range(len(rows)))
    sizes = [row[1] for row in rows]
    outcomes = [row[2] for row in rows]
    if len(set(sizes)) < 2:
        return None
    size_corr, p_value = stats.spearmanr(indexes, sizes)
    if not math.isfinite(float(size_corr)) or not math.isfinite(float(p_value)):
        return None
    if size_corr <= 0 or p_value >= SIGNIFICANCE_THRESHOLD:
        return None

    if len(set(outcomes)) < 2:
        accuracy_corr = 0.0
        accuracy_p = 1.0
    else:
        accuracy_corr, accuracy_p = stats.spearmanr(indexes, outcomes)
        if not math.isfinite(float(accuracy_corr)):
            accuracy_corr = 0.0
        if not math.isfinite(float(accuracy_p)):
            accuracy_p = 1.0

    window = max(5, len(rows) // 3)
    early_acc = sum(outcomes[:window]) / window
    late_acc = sum(outcomes[-window:]) / window
    improving = late_acc > early_acc + 0.05 or (
        accuracy_corr > 0.1 and accuracy_p < 0.1
    )
    if improving:
        return None

    early_size = sum(sizes[:window]) / window
    late_size = sum(sizes[-window:]) / window
    if early_size <= 0:
        return None
    excess_size = max(0.0, (late_size - early_size) / early_size)
    if excess_size <= 0:
        return None

    accuracy = sum(outcomes) / len(outcomes)
    trades_per_year = _annualized_count([row[0] for row in rows])
    estimated_cost = round(excess_size * (1.0 - accuracy) * trades_per_year, 2)
    affected = [row[0] for row in rows[-window:]]
    return _pattern(
        name="sizing_drift",
        display_name="Sizing Drift",
        description=(
            "Position size is increasing over time without a matching accuracy improvement."
        ),
        affected=affected,
        severity=min(1.0, 0.3 + min(excess_size, 1.0) * 0.7),
        recommendation="Cap size until the larger positions show a verified accuracy improvement.",
        total=len(trades),
        p_value=float(p_value),
        estimated_annual_cost=estimated_cost,
        cost_components={
            "accuracy_delta": round(max(0.0, early_acc - late_acc), 4),
            "affected_frequency": round(len(affected) / len(trades), 4),
            "avg_trade_size": round(sum(sizes) / len(sizes), 4),
            "excess_size": round(excess_size, 4),
            "trades_per_year": round(trades_per_year, 4),
        },
        statistical_test="spearman",
    )
