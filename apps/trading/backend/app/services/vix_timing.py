"""VIX-aware hold period analysis for Trading."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


HOLD_BUCKETS = ("intraday", "1_3_days", "1_2_weeks", "2_plus_weeks")
VIX_BUCKETS = ("low", "medium", "high")
HOLD_DISPLAY = {
    "intraday": "Intraday",
    "1_3_days": "1-3 days",
    "1_2_weeks": "1-2 weeks",
    "2_plus_weeks": "2+ weeks",
}
VIX_DISPLAY = {
    "low": "Low VIX",
    "medium": "Medium VIX",
    "high": "High VIX",
}


def _bucket_hold_period(entry_time: Any, exit_time: Any) -> str | None:
    entry = _parse_datetime(entry_time)
    exit_ = _parse_datetime(exit_time)
    if entry is None or exit_ is None:
        return None
    hours = (exit_ - entry).total_seconds() / 3600.0
    if hours < 0:
        return None
    if hours < 8:
        return "intraday"
    if hours < 72:
        return "1_3_days"
    if hours < 336:
        return "1_2_weeks"
    return "2_plus_weeks"


def _bucket_vix(vix: float) -> str:
    value = float(vix)
    if value < 20.0:
        return "low"
    if value < 30.0:
        return "medium"
    return "high"


class VIXTimingService:
    def analyze(
        self,
        trades: list[dict[str, Any]],
        vix_data: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        vix_by_date = vix_data or {}
        matrix = _empty_matrix()
        total_analyzed = 0
        total_skipped = 0

        for trade in trades:
            hold_bucket = _bucket_hold_period(trade.get("entry_time"), trade.get("exit_time"))
            entry_date = _entry_date_key(trade.get("entry_time"))
            vix = _vix_for_trade(trade, entry_date, vix_by_date)
            if hold_bucket is None or vix is None:
                total_skipped += 1
                continue

            vix_bucket = _bucket_vix(vix)
            cell = matrix[hold_bucket][vix_bucket]
            cell["count"] += 1
            if _is_win(trade):
                cell["wins"] += 1
            total_analyzed += 1

        populated: list[dict[str, Any]] = []
        for hold_bucket in HOLD_BUCKETS:
            for vix_bucket in VIX_BUCKETS:
                cell = matrix[hold_bucket][vix_bucket]
                if cell["count"] > 0:
                    cell["accuracy"] = round(cell["wins"] / cell["count"], 4)
                    populated.append({
                        "hold_bucket": hold_bucket,
                        "vix_bucket": vix_bucket,
                        "accuracy": cell["accuracy"],
                        "count": cell["count"],
                    })
                else:
                    cell["accuracy"] = None

        best_bucket = max(populated, key=lambda row: (row["accuracy"], row["count"]), default=None)
        worst_bucket = min(populated, key=lambda row: (row["accuracy"], -row["count"]), default=None)
        return {
            "matrix": matrix,
            "best_bucket": best_bucket,
            "worst_bucket": worst_bucket,
            "total_analyzed": total_analyzed,
            "total_skipped": total_skipped,
            "hold_labels": HOLD_DISPLAY,
            "vix_labels": VIX_DISPLAY,
            "recommendations": _generate_recommendations(matrix),
        }


def _generate_recommendations(matrix: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    recommendations: list[str] = []
    high_intraday = matrix["intraday"]["high"]
    high_swing = matrix["1_2_weeks"]["high"]
    if high_intraday["count"] >= 5 and high_swing["count"] >= 5:
        delta = float(high_swing["accuracy"]) - float(high_intraday["accuracy"])
        if delta > 0.10:
            recommendations.append(
                "High-VIX 1-2 week holds have outperformed intraday holds by "
                f"{delta:.0%}; review whether longer holds have been part of the edge."
            )
        elif delta < -0.10:
            recommendations.append(
                "High-VIX intraday holds have outperformed 1-2 week holds by "
                f"{abs(delta):.0%}; quick exits may be where past results concentrated."
            )

    for hold_bucket in HOLD_BUCKETS:
        low = matrix[hold_bucket]["low"]
        high = matrix[hold_bucket]["high"]
        if low["count"] < 5 or high["count"] < 5:
            continue
        delta = float(high["accuracy"]) - float(low["accuracy"])
        if abs(delta) > 0.15:
            direction = "better" if delta > 0 else "worse"
            recommendations.append(
                f"{HOLD_DISPLAY[hold_bucket]} trades performed {abs(delta):.0%} {direction} "
                "in high VIX than low VIX conditions."
            )

    if not recommendations:
        recommendations.append("Insufficient VIX timing history for a reliable hold-period observation.")
    return recommendations


def _empty_matrix() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        hold_bucket: {
            vix_bucket: {"count": 0, "wins": 0, "accuracy": None}
            for vix_bucket in VIX_BUCKETS
        }
        for hold_bucket in HOLD_BUCKETS
    }


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _entry_date_key(value: Any) -> str | None:
    # Match RegimeService historical VIX keys: preserve the trade's local
    # calendar date instead of converting aware timestamps to UTC.
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else None


def _vix_for_trade(
    trade: dict[str, Any],
    entry_date: str | None,
    vix_data: dict[str, float],
) -> float | None:
    if entry_date and entry_date in vix_data:
        return _number(vix_data[entry_date])
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = _number(trade.get("vix_at_entry"))
    if value is not None:
        return value
    return _number(metadata.get("vix_at_entry"))


def _is_win(trade: dict[str, Any]) -> bool:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = trade.get("pnl")
    if value is None:
        value = trade.get("pnl_dollars")
    if value is None:
        value = metadata.get("pnl")
    if value is None:
        value = metadata.get("pnl_dollars")
    pnl = _number(value)
    return bool(pnl is not None and pnl > 0)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
