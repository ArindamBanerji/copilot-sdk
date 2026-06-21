"""Detailed regime-context allocation readiness recommendations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.regime import DEFAULT_ADX, RegimeService, classify_regime


REGIMES = ("trending", "ranging", "volatile")
ACTION_ORDER = {"avoid": 0, "reduce": 1, "hold": 2, "increase": 3}
MIN_EDGE_SAMPLE = 5
MIN_FACTOR_SAMPLE = 5


class RegimeRecommender:
    def recommend(
        self,
        current_regime: str,
        accuracy: dict[str, dict[str, float]],
        conservation_status: Any = None,
        *,
        trades: list[dict[str, Any]] | None = None,
        current: dict[str, Any] | None = None,
        previous_regime: str | None = None,
    ) -> dict[str, Any]:
        regime = str(current_regime or "ranging")
        conservation_safe = _is_conservation_safe(conservation_status)
        conservation_label = _conservation_label(conservation_status, conservation_safe)
        sample_report = _regime_sample_report(trades or [])
        samples = sample_report["samples"]
        recommendations = [
            _category_recommendation(category, regime, regimes, samples.get(category, {}))
            for category, regimes in sorted(accuracy.items())
        ]
        recommendations = sorted(
            recommendations,
            key=lambda item: (
                ACTION_ORDER.get(str(item["action"]), 99),
                -abs(float(item["delta_pp"])),
                str(item["category"]),
            ),
        )
        transitions = _regime_transitions(accuracy)
        edge_summary = _regime_edge_summary(regime, accuracy, samples, current or {})
        sizing = _sizing_recommendation(regime, edge_summary, recommendations, current or {})
        factor_influence = _factor_influence(regime, trades or [])
        factor_weights = _regime_factor_weights(regime, factor_influence)
        transition_alert = _transition_alert(previous_regime, regime, accuracy, samples)
        data_quality = _data_quality(sample_report, trades or [])
        return {
            "regime": regime,
            "recommendations": recommendations,
            "regime_transitions": transitions,
            "conservation_safe": conservation_safe,
            "conservation_status": conservation_label,
            "summary": _summary(recommendations, conservation_safe),
            "regime_edge_summary": edge_summary,
            "sizing_recommendation": sizing,
            "transition_alert": transition_alert,
            "regime_factor_weights": factor_weights,
            "regime_factor_influence": factor_influence,
            "data_quality": data_quality,
            "product_honesty_warnings": _product_honesty_warnings(edge_summary, factor_weights, data_quality),
        }


def _category_recommendation(
    category: str,
    current_regime: str,
    regimes: dict[str, float],
    samples: dict[str, int] | None = None,
) -> dict[str, Any]:
    values = [_to_float(value) for value in regimes.values()]
    values = [value for value in values if value is not None]
    baseline = sum(values) / len(values) if values else 0.5
    current_accuracy = _to_float(regimes.get(current_regime))
    if current_accuracy is None:
        current_accuracy = 0.5
    delta_pp = round((current_accuracy - baseline) * 100, 1)
    spread_pp = round((max(values) - min(values)) * 100, 1) if values else 0.0
    regime_neutral = spread_pp < 5.0

    if current_accuracy < 0.40:
        action = "avoid"
        shift_pct = -100
    elif delta_pp <= -10.0:
        action = "reduce"
        shift_pct = max(-50, int(delta_pp * 2))
    elif delta_pp >= 5.0:
        action = "increase"
        shift_pct = min(30, int(delta_pp * 2))
    else:
        action = "hold"
        shift_pct = 0

    return {
        "category": category,
        "current_regime": current_regime,
        "current_accuracy": round(current_accuracy, 4),
        "baseline_accuracy": round(baseline, 4),
        "delta_pp": delta_pp,
        "action": action,
        "shift_pct": shift_pct,
        "regime_neutral": regime_neutral,
        "sample_size": int((samples or {}).get(current_regime, 0)),
        "min_sample_size_met": int((samples or {}).get(current_regime, 0)) >= MIN_EDGE_SAMPLE,
        "source": "journal_trades" if samples else "unknown",
        "rationale": _rationale(category, current_regime, current_accuracy, baseline, delta_pp, action),
    }


def _rationale(
    category: str,
    regime: str,
    current_accuracy: float,
    baseline: float,
    delta_pp: float,
    action: str,
) -> str:
    return (
        f"{category} has {current_accuracy:.0%} observed historical accuracy in {regime} "
        f"versus {baseline:.0%} baseline; allocation shift action is {action} "
        f"with {delta_pp:+.1f}pp regime context."
    )


def _regime_samples(trades: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return _regime_sample_report(trades)["samples"]


def _regime_sample_report(trades: list[dict[str, Any]]) -> dict[str, Any]:
    samples: dict[str, dict[str, int]] = {}
    unknown_regime_rows = 0
    inferred_regime_rows = 0
    vix_by_date = _historical_vix(trades)
    for trade in trades:
        category = str(trade.get("category") or "").strip()
        regime, inferred = _trade_regime_for_sample(trade, vix_by_date)
        if not category:
            continue
        if _pnl_value(trade) is None:
            continue
        if not regime:
            unknown_regime_rows += 1
            continue
        if inferred:
            inferred_regime_rows += 1
        samples.setdefault(category, {}).setdefault(regime, 0)
        samples[category][regime] += 1
    return {
        "samples": samples,
        "unknown_regime_rows": unknown_regime_rows,
        "inferred_regime_rows": inferred_regime_rows,
    }


def _historical_vix(trades: list[dict[str, Any]]) -> dict[str, float]:
    if not trades:
        return {}
    try:
        return RegimeService().get_historical_vix(trades)
    except Exception:
        return {}


def _trade_regime_for_sample(trade: dict[str, Any], vix_by_date: dict[str, float]) -> tuple[str | None, bool]:
    metadata = _metadata(trade)
    explicit = str(trade.get("regime") or metadata.get("regime") or "").strip()
    if explicit:
        return explicit, False
    vix = _to_float(trade.get("vix_at_entry"))
    if vix is None:
        vix = _to_float(metadata.get("vix_at_entry"))
    if vix is not None:
        return classify_regime(vix, DEFAULT_ADX), True
    date_key = _trade_date(trade)
    if date_key and date_key in vix_by_date:
        return classify_regime(vix_by_date[date_key], DEFAULT_ADX), True
    return None, False


def _regime_edge_summary(
    current_regime: str,
    accuracy: dict[str, dict[str, float]],
    samples: dict[str, dict[str, int]],
    current: dict[str, Any],
) -> dict[str, Any]:
    category, regimes = _preferred_category(accuracy)
    if not category or not regimes:
        return {
            "current_regime": current_regime,
            "comparison_regime": None,
            "current_accuracy": None,
            "comparison_accuracy": None,
            "edge_delta_pp": None,
            "sample_size_current": 0,
            "sample_size_comparison": 0,
            "source": "journal_trades" if samples else "unknown",
            "status": "unavailable",
            "message": "Score more trades to build sample-backed regime edge comparisons.",
        }

    comparison_regime = _comparison_regime(current_regime, regimes)
    current_accuracy = _to_float(regimes.get(current_regime))
    comparison_accuracy = _to_float(regimes.get(comparison_regime)) if comparison_regime else None
    sample_current = int(samples.get(category, {}).get(current_regime, 0))
    sample_comparison = int(samples.get(category, {}).get(str(comparison_regime), 0)) if comparison_regime else 0
    source = "journal_trades" if samples else "unknown"
    status = "available"
    edge_delta_pp: float | None = None
    if current_accuracy is None or comparison_accuracy is None:
        status = "unavailable"
    else:
        edge_delta_pp = round((current_accuracy - comparison_accuracy) * 100, 1)
        if sample_current < MIN_EDGE_SAMPLE or sample_comparison < MIN_EDGE_SAMPLE:
            status = "insufficient_data"

    return {
        "category": category,
        "current_regime": current_regime,
        "comparison_regime": comparison_regime,
        "current_accuracy": round(current_accuracy, 4) if current_accuracy is not None else None,
        "comparison_accuracy": round(comparison_accuracy, 4) if comparison_accuracy is not None else None,
        "edge_delta_pp": edge_delta_pp,
        "sample_size_current": sample_current,
        "sample_size_comparison": sample_comparison,
        "source": source,
        "status": status,
        "message": _edge_message(
            category,
            current_regime,
            comparison_regime,
            edge_delta_pp,
            status,
            sample_current,
            sample_comparison,
            current,
        ),
    }


def _preferred_category(accuracy: dict[str, dict[str, float]]) -> tuple[str | None, dict[str, float]]:
    if "income_strategy" in accuracy:
        return "income_strategy", accuracy["income_strategy"]
    if not accuracy:
        return None, {}
    category = sorted(accuracy)[0]
    return category, accuracy[category]


def _comparison_regime(current_regime: str, regimes: dict[str, float]) -> str | None:
    preferred = {
        "volatile": ("trending", "ranging"),
        "ranging": ("volatile", "trending"),
        "trending": ("volatile", "ranging"),
    }.get(current_regime, tuple(regime for regime in REGIMES if regime != current_regime))
    for regime in preferred:
        if regime in regimes and regime != current_regime:
            return regime
    for regime in sorted(regimes):
        if regime != current_regime:
            return regime
    return None


def _edge_message(
    category: str,
    current_regime: str,
    comparison_regime: str | None,
    edge_delta_pp: float | None,
    status: str,
    sample_current: int,
    sample_comparison: int,
    current: dict[str, Any],
) -> str:
    if status == "unavailable" or comparison_regime is None or edge_delta_pp is None:
        return "Observed edge comparison is unavailable until at least two regimes have outcome history."
    if status == "insufficient_data":
        return (
            f"Observed {category} edge in {current_regime} is based on {sample_current} trades versus "
            f"{sample_comparison} in {comparison_regime}; treat the comparison as insufficient data."
        )
    direction = "larger" if edge_delta_pp > 0 else "smaller" if edge_delta_pp < 0 else "similar"
    vix = _to_float(current.get("vix"))
    vix_text = f" at VIX {vix:.0f}" if vix is not None and current_regime == "volatile" else ""
    return (
        f"Your observed {category} edge is {direction}{vix_text} than in {comparison_regime} "
        f"by {edge_delta_pp:+.1f}pp over {sample_current}+{sample_comparison} journal trades. "
        "This is historical context, not a guarantee."
    )


def _sizing_recommendation(
    current_regime: str,
    edge_summary: dict[str, Any],
    recommendations: list[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any]:
    current_accuracy = _to_float(edge_summary.get("current_accuracy"))
    edge_delta = _to_float(edge_summary.get("edge_delta_pp"))
    sample_size = int(edge_summary.get("sample_size_current") or 0)
    min_sample_met = edge_summary.get("status") == "available" and sample_size >= MIN_EDGE_SAMPLE
    vix = _to_float(current.get("vix"))
    top_action = str(recommendations[0].get("action")) if recommendations else "hold"

    action = "normal"
    suggested = 1.0
    max_size = 1.0
    confidence_status = "sample_backed" if min_sample_met else "insufficient_data"
    reasons: list[str] = [f"current regime is {current_regime}", f"sample size {sample_size}"]

    if not min_sample_met:
        action = "reduce"
        suggested = 0.75
        max_size = 1.0
        reasons.append("insufficient regime-specific history")
    elif current_regime == "volatile" or (vix is not None and vix >= 30.0):
        max_size = 0.75
        if current_accuracy is not None and current_accuracy >= 0.65 and edge_delta is not None and edge_delta >= 10.0:
            action = "normal"
            suggested = 0.75
            reasons.append("observed edge is stronger but volatility cap applies")
        else:
            action = "reduce"
            suggested = 0.5
            reasons.append("high-volatility caution")
    elif top_action == "avoid" or (current_accuracy is not None and current_accuracy < 0.40):
        action = "avoid"
        suggested = 0.0
        max_size = 0.0
        reasons.append("observed regime accuracy is weak")
    elif edge_delta is not None and edge_delta >= 10.0 and current_accuracy is not None and current_accuracy >= 0.60:
        action = "increase_small"
        suggested = 1.1
        max_size = 1.25
        reasons.append("sample-backed observed edge is stronger than comparison regime")

    return {
        "action": action,
        "suggested_size_multiplier": round(suggested, 2),
        "max_size_multiplier": round(max_size, 2),
        "reason": "; ".join(reasons),
        "regime": current_regime,
        "sample_size": sample_size,
        "min_sample_size_met": bool(min_sample_met),
        "confidence_status": confidence_status,
        "advisory_only": True,
    }


def _transition_alert(
    previous_regime: str | None,
    current_regime: str,
    accuracy: dict[str, dict[str, float]],
    samples: dict[str, dict[str, int]],
) -> dict[str, Any]:
    previous = str(previous_regime or "").strip()
    if not previous:
        return {
            "active": False,
            "previous_regime": None,
            "current_regime": current_regime,
            "edge_delta_pp": None,
            "old_recommendation": None,
            "new_recommendation": None,
            "message": "",
            "severity": "info",
            "reason": "previous_regime_unavailable",
        }
    if previous == current_regime:
        return {
            "active": False,
            "previous_regime": previous,
            "current_regime": current_regime,
            "edge_delta_pp": 0.0,
            "old_recommendation": None,
            "new_recommendation": None,
            "message": "",
            "severity": "info",
            "reason": "regime_unchanged",
        }

    deltas: list[float] = []
    old_recommendations: list[dict[str, Any]] = []
    new_recommendations: list[dict[str, Any]] = []
    for category, regimes in sorted(accuracy.items()):
        old_value = _to_float(regimes.get(previous))
        new_value = _to_float(regimes.get(current_regime))
        category_samples = samples.get(category, {})
        old_sample = int(category_samples.get(previous, 0))
        new_sample = int(category_samples.get(current_regime, 0))
        if old_value is None or new_value is None or old_sample <= 0 or new_sample <= 0:
            continue
        deltas.append((new_value - old_value) * 100)
        old_recommendations.append(_category_recommendation(category, previous, regimes, category_samples))
        new_recommendations.append(_category_recommendation(category, current_regime, regimes, category_samples))

    if not deltas:
        return {
            "active": False,
            "previous_regime": previous,
            "current_regime": current_regime,
            "edge_delta_pp": None,
            "old_recommendation": None,
            "new_recommendation": None,
            "message": "Regime changed, but previous-regime sample data is unavailable.",
            "severity": "info",
            "reason": "previous_regime_data_unavailable",
        }

    delta = round(sum(deltas) / len(deltas), 1) if deltas else None
    severity = "warning" if delta is None or delta < -5.0 else "info"
    return {
        "active": True,
        "previous_regime": previous,
        "current_regime": current_regime,
        "edge_delta_pp": delta,
        "old_recommendation": _top_action(old_recommendations),
        "new_recommendation": _top_action(new_recommendations),
        "message": "Regime changed; observed edge shifted.",
        "severity": severity,
        "reason": "regime_changed",
    }


def _top_action(recommendations: list[dict[str, Any]]) -> str | None:
    if not recommendations:
        return None
    ordered = sorted(
        recommendations,
        key=lambda item: (
            ACTION_ORDER.get(str(item.get("action")), 99),
            -abs(float(item.get("delta_pp") or 0.0)),
            str(item.get("category") or ""),
        ),
    )
    return str(ordered[0].get("action"))


def _factor_influence(current_regime: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    factor_rows: dict[str, dict[str, list[float]]] = {}
    sample_size = 0
    for trade in trades:
        regime = str(trade.get("regime") or _metadata(trade).get("regime") or "").strip()
        if regime != current_regime:
            continue
        factors = trade.get("factors")
        if not isinstance(factors, dict):
            factors = _metadata(trade).get("factors")
        if not isinstance(factors, dict):
            continue
        pnl = _pnl_value(trade)
        if pnl is None:
            continue
        sample_size += 1
        bucket = "wins" if pnl > 0 else "losses"
        for name, value in factors.items():
            number = _to_float(value)
            if number is None:
                continue
            factor_rows.setdefault(str(name), {"wins": [], "losses": []})[bucket].append(number)

    if sample_size < MIN_FACTOR_SAMPLE:
        return {
            "status": "learning" if sample_size else "unavailable",
            "regime": current_regime,
            "factors": [],
            "source": "journal_trades",
            "sample_size": sample_size,
            "warning": "insufficient factor outcome samples for regime-specific influence",
        }

    factors: list[dict[str, Any]] = []
    for name, groups in sorted(factor_rows.items()):
        wins = groups["wins"]
        losses = groups["losses"]
        if not wins or not losses:
            continue
        win_avg = sum(wins) / len(wins)
        loss_avg = sum(losses) / len(losses)
        factors.append({
            "factor": name,
            "influence_pp": round((win_avg - loss_avg) * 100, 1),
            "win_average": round(win_avg, 4),
            "loss_average": round(loss_avg, 4),
            "sample_size": len(wins) + len(losses),
        })
    factors = sorted(factors, key=lambda item: (-abs(float(item["influence_pp"])), str(item["factor"])))
    return {
        "status": "available" if factors else "learning",
        "regime": current_regime,
        "factors": factors,
        "source": "journal_trades_observed_influence",
        "sample_size": sample_size,
        "warning": None if factors else "factor samples lack win/loss contrast",
    }


def _regime_factor_weights(current_regime: str, influence: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "regime": current_regime,
        "factor_weights": [],
        "source": "per_regime_dk_unavailable",
        "sample_size": int(influence.get("sample_size") or 0),
        "reason": "Per-regime DK/factor trust weights are not available; observed factor influence is reported separately when sample-backed.",
    }


def _data_quality(sample_report: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    samples = sample_report["samples"]
    total_samples = sum(sum(regimes.values()) for regimes in samples.values())
    unknown_regime_rows = int(sample_report.get("unknown_regime_rows") or 0)
    inferred_regime_rows = int(sample_report.get("inferred_regime_rows") or 0)
    warnings = [
        "Regime edge uses journal/PnL outcomes unless an upstream verified-outcome source is provided.",
        "Recommendations are advisory context and do not guarantee future profit.",
    ]
    if unknown_regime_rows:
        warnings.append(f"{unknown_regime_rows} outcome rows lacked explicit or inferable regime and were excluded from P49 sample counts.")
    return {
        "source": "journal_trades" if trades else "unknown",
        "total_trades": len(trades),
        "sampled_outcome_trades": total_samples,
        "inferred_regime_rows": inferred_regime_rows,
        "unknown_regime_rows": unknown_regime_rows,
        "min_edge_sample": MIN_EDGE_SAMPLE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings,
    }


def _product_honesty_warnings(
    edge_summary: dict[str, Any],
    factor_weights: dict[str, Any],
    data_quality: dict[str, Any],
) -> list[str]:
    warnings = list(data_quality.get("warnings") or [])
    if edge_summary.get("status") != "available":
        warnings.append("Regime edge comparison is not fully sample-backed.")
    if factor_weights.get("status") != "available":
        warnings.append("Per-regime DK weights are unavailable and were not fabricated.")
    return warnings


def _regime_transitions(accuracy: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    pairs = (("trending", "ranging"), ("trending", "volatile"), ("ranging", "volatile"))
    transitions: list[dict[str, Any]] = []
    for source, target in pairs:
        deltas: list[float] = []
        categories: list[str] = []
        for category, regimes in sorted(accuracy.items()):
            source_value = _to_float(regimes.get(source))
            target_value = _to_float(regimes.get(target))
            if source_value is None or target_value is None:
                continue
            deltas.append((target_value - source_value) * 100)
            categories.append(category)
        avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else 0.0
        transitions.append({
            "from_regime": source,
            "to_regime": target,
            "avg_accuracy_delta_pp": avg_delta,
            "categories_affected": categories,
            "count": len(categories),
        })
    return transitions


def _summary(recommendations: list[dict[str, Any]], conservation_safe: bool) -> str:
    counts = {action: 0 for action in ACTION_ORDER}
    neutral = 0
    for item in recommendations:
        counts[str(item.get("action"))] = counts.get(str(item.get("action")), 0) + 1
        if item.get("regime_neutral") is True:
            neutral += 1
    message = (
        f"{counts['avoid']} avoid, {counts['reduce']} reduce, "
        f"{counts['increase']} increase, {neutral} regime-neutral."
    )
    if not conservation_safe:
        message = f"{message} Conservation not confirmed; treat shifts as informational."
    return message


def _is_conservation_safe(status: Any) -> bool:
    if status is None:
        return False
    if isinstance(status, str):
        return status.strip().upper() == "GREEN"
    if not isinstance(status, dict):
        return False
    status_value = status.get("status")
    if isinstance(status_value, str) and status_value.strip().upper() == "GREEN":
        return True
    state_value = status.get("state")
    if isinstance(state_value, str) and state_value.strip().upper() == "GREEN":
        return True
    phase_value = status.get("phase")
    if isinstance(phase_value, str) and phase_value.strip().lower() in {"green", "verified", "active"}:
        return True
    return status.get("overall_safe") is True or status.get("overallSafe") is True


def _conservation_label(status: Any, safe: bool) -> str:
    if safe:
        return "safe"
    if status is None:
        return "unknown"
    return "unsafe"


def _metadata(trade: dict[str, Any]) -> dict[str, Any]:
    metadata = trade.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _pnl_value(trade: dict[str, Any]) -> float | None:
    metadata = _metadata(trade)
    value = trade.get("pnl")
    if value is None:
        value = trade.get("pnl_dollars")
    if value is None:
        value = metadata.get("pnl")
    if value is None:
        value = metadata.get("pnl_dollars")
    return _to_float(value)


def _trade_date(trade: dict[str, Any]) -> str | None:
    metadata = _metadata(trade)
    value = trade.get("entry_time") or trade.get("date") or metadata.get("entry_time") or metadata.get("date")
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else None


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number
