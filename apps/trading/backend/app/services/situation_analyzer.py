"""Trading situation analyzer for provenance-labeled demo analytics.

The situation story is a product demo surface, not a measured trading claim.
Every returned magnitude is therefore marked illustrative/T-O.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


REGIMES = ("trending", "choppy", "volatile", "calm")
MIN_DECISIONS = 10
PROVENANCE = "illustrative"
SUBSTANTIATION = "T-O"


def detect_regime(decisions: list[dict[str, Any]]) -> str:
    """Return the latest explicit regime, or a deterministic demo regime."""
    tagged = [_regime(decision) for decision in decisions]
    explicit = [value for value in tagged if value is not None]
    if explicit:
        return explicit[-1]

    if not decisions:
        return "choppy"
    # Untagged legacy seeds remain useful in the demo without pretending that
    # a missing tag is a measured market classification.
    return ("trending", "choppy", "volatile")[len(decisions) % 3]


def compute_regime_conditioned_stats(
    decisions: list[dict[str, Any]],
    regime: str | None = None,
) -> dict[str, Any]:
    """Compute illustrative regime-conditioned trade outcomes."""
    rows = _tagged_rows(decisions)
    counts: Counter[str] = Counter(row["regime"] for row in rows)
    stats: dict[str, dict[str, Any]] = {}
    for name in REGIMES:
        group = [row for row in rows if row["regime"] == name]
        verified = [row for row in group if row["verified"]]
        correct = sum(1 for row in verified if row["correct"])
        accuracy = correct / len(verified) if verified else None
        stats[name] = {
            "regime": name,
            "decision_count": len(group),
            "verified_count": len(verified),
            "accuracy": round(accuracy, 3) if accuracy is not None else None,
            "trade_frequency_multiplier": 2.1 if name == "choppy" else 1.0,
            "loss_delta_pct": -12 if name == "choppy" else 0,
            "measurement_state": "illustrative_demo",
            "provenance": PROVENANCE,
            "substantiation": SUBSTANTIATION,
        }

    current = _normalize(regime) if regime else detect_regime(decisions)
    return {
        "current_regime": current,
        "regimes": stats,
        "mirror_message": "Your discipline holds when trends persist; in choppy regimes you trade 2.1x more and lose 12%.",
        "provenance": PROVENANCE,
        "substantiation": SUBSTANTIATION,
    }


def compute_sharpe_adjustment(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the illustrative short-vol clustering adjustment."""
    n = len(decisions)
    return {
        "raw_sharpe": 2.1,
        "clustering_adjusted_sharpe": 1.2,
        "adjustment_factor": 1.2 / 2.1,
        "n_decisions": n,
        "vrp_capture_low_tail_pct": 78,
        "vrp_message": "78% of your VRP capture came in low-tail-dependence windows.",
        "message": "Your calm-regime Sharpe of 2.1 is 1.2 after clustering adjustment.",
        "provenance": PROVENANCE,
        "substantiation": SUBSTANTIATION,
    }


def check_regime_data_sufficiency(
    decisions: list[dict[str, Any]],
    regime: str | None = None,
    min_decisions: int = MIN_DECISIONS,
) -> dict[str, Any]:
    """Tell the UI whether the current regime has enough history to score."""
    current = _normalize(regime) if regime else detect_regime(decisions)
    count = sum(1 for row in _tagged_rows(decisions) if row["regime"] == current)
    return {
        "regime": current,
        "decision_count": count,
        "minimum_decisions": min_decisions,
        "abstention_recommended": count < min_decisions,
        "message": (
            f"I've seen only {count} of your decisions in this regime — I won't score this trade yet."
            if count < min_decisions
            else f"I've seen {count} decisions in this regime; situation-conditioned scoring is available."
        ),
        "provenance": PROVENANCE,
        "substantiation": SUBSTANTIATION,
    }


def compute_regime_rejections(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the illustrative regime-scoped rejection explanation."""
    variants = max(35, len(decisions) // 6 if decisions else 35)
    single_regime = min(11, variants)
    return {
        "variants_tested": variants,
        "variants_rejected": variants,
        "rejections": [
            {"reason": "single_regime_only", "count": single_regime, "label": "Worked in one regime only"},
            {"reason": "conservation_guard", "count": variants - single_regime, "label": "Conservation guard"},
        ],
        "message": f"{variants} variants rejected — {single_regime} because they only worked in one regime.",
        "provenance": PROVENANCE,
        "substantiation": SUBSTANTIATION,
    }


def _tagged_rows(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, decision in enumerate(decisions):
        explicit = _regime(decision)
        regime = explicit or ("trending", "choppy", "volatile")[index % 3]
        rows.append({
            "regime": regime,
            "verified": _verified(decision),
            "correct": _correct(decision),
        })
    return rows


def _regime(decision: dict[str, Any]) -> str | None:
    candidates: list[Any] = [decision.get("regime"), decision.get("current_regime")]
    for key in ("regime_context", "regime_metadata", "metadata", "context"):
        value = decision.get(key)
        if isinstance(value, dict):
            candidates.extend([value.get("regime"), value.get("current_regime")])
            nested = value.get("regime_context") or value.get("regime_metadata")
            if isinstance(nested, dict):
                candidates.append(nested.get("regime"))
    for candidate in candidates:
        if candidate:
            return _normalize(str(candidate))
    return None


def _normalize(value: str) -> str:
    normalized = value.strip().lower()
    return "choppy" if normalized in {"ranging", "range", "chop"} else normalized if normalized in REGIMES else "choppy"


def _verified(decision: dict[str, Any]) -> bool:
    return bool(decision.get("verified") or decision.get("verified_at") or decision.get("outcome_correct") is not None or decision.get("is_correct") is not None)


def _correct(decision: dict[str, Any]) -> bool:
    if "outcome_correct" in decision:
        return bool(decision["outcome_correct"])
    return bool(decision.get("is_correct"))
