"""Trust-trap detection for self-computation surfaces.

These checks are diagnostics over verified decision history. They do not alter
scorer state and deliberately return evidence for every alert.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TrustTrap:
    trap_type: str
    severity: str
    description: str
    evidence: dict[str, Any]
    recommended_action: str


class TrustTrapDetector:
    def __init__(self, scorer: Any | None, store: Any, domain: str):
        self._scorer = scorer
        self._store = store
        self._domain = domain

    def scan(self) -> list[TrustTrap]:
        decisions = self._verified_decisions()
        traps: list[TrustTrap] = []
        traps.extend(self._check_category_divergence(decisions))
        traps.extend(self._check_volume_skew(decisions))
        traps.extend(self._check_recency_bias(decisions))
        traps.extend(self._check_conservation_gaming(decisions))
        return traps

    def _check_category_divergence(self, decisions: list[dict[str, Any]]) -> list[TrustTrap]:
        midpoint = len(decisions) // 2
        if len(decisions) < 20 or midpoint < 2:
            return []
        early, recent = decisions[:midpoint], decisions[midpoint:]
        overall_early = _accuracy(early)
        overall_recent = _accuracy(recent)
        if overall_recent - overall_early <= 0.02:
            return []

        drops: list[dict[str, Any]] = []
        categories = sorted({str(row.get("category") or "uncategorized") for row in decisions})
        for category in categories:
            before = [row for row in early if _category(row) == category]
            after = [row for row in recent if _category(row) == category]
            if len(before) < 4 or len(after) < 4:
                continue
            before_accuracy = _accuracy(before)
            after_accuracy = _accuracy(after)
            if before_accuracy - after_accuracy > 0.10:
                drops.append({
                    "category": category,
                    "early_accuracy": round(before_accuracy, 4),
                    "recent_accuracy": round(after_accuracy, 4),
                    "delta": round(after_accuracy - before_accuracy, 4),
                })
        if not drops:
            return []
        return [TrustTrap(
            "CATEGORY_DIVERGENCE",
            "ALERT" if any(item["delta"] < -0.20 for item in drops) else "WARNING",
            "Overall accuracy is rising while one or more categories are quietly degrading.",
            {"overall_early_accuracy": round(overall_early, 4), "overall_recent_accuracy": round(overall_recent, 4), "categories": drops},
            "Inspect the degrading category before increasing autonomy.",
        )]

    def _check_volume_skew(self, decisions: list[dict[str, Any]]) -> list[TrustTrap]:
        counts = _category_counts(decisions)
        if len(decisions) < 20 or len(counts) < 2:
            return []
        gini = _gini(list(counts.values()))
        if gini <= 0.60:
            return []
        return [TrustTrap(
            "VOLUME_SKEW",
            "ALERT" if gini > 0.75 else "WARNING",
            "Decision volume is concentrated in a small number of categories, which can inflate aggregate accuracy.",
            {"gini": round(gini, 4), "category_counts": counts, "total_decisions": len(decisions)},
            "Require coverage of under-sampled categories before trusting the aggregate metric.",
        )]

    def _check_recency_bias(self, decisions: list[dict[str, Any]]) -> list[TrustTrap]:
        if len(decisions) < 50:
            return []
        recent = decisions[-50:]
        window = decisions[-200:]
        recent_accuracy = _accuracy(recent)
        window_accuracy = _accuracy(window)
        delta = recent_accuracy - window_accuracy
        if delta <= 0.15:
            return []
        return [TrustTrap(
            "RECENCY_BIAS",
            "WARNING",
            "Recent accuracy is materially higher than the longer window and may be masking decay outside the latest streak.",
            {"recent_window": 50, "long_window": len(window), "recent_accuracy": round(recent_accuracy, 4), "long_window_accuracy": round(window_accuracy, 4), "delta": round(delta, 4)},
            "Keep the longer evaluation window visible and delay claims based only on the recent streak.",
        )]

    def _check_conservation_gaming(self, decisions: list[dict[str, Any]]) -> list[TrustTrap]:
        counts = _category_counts(decisions)
        if len(decisions) < 20 or len(counts) < 2:
            return []
        accuracy_by_category = {
            category: _accuracy([row for row in decisions if _category(row) == category])
            for category in counts
        }
        hard = [category for category, accuracy in accuracy_by_category.items() if accuracy < 0.60]
        easy = [category for category, accuracy in accuracy_by_category.items() if accuracy >= 0.80]
        hard_volume = sum(counts[category] for category in hard)
        easy_volume = sum(counts[category] for category in easy)
        if not hard or hard_volume == 0 or easy_volume < 3 * hard_volume:
            return []
        return [TrustTrap(
            "CONSERVATION_GAMING",
            "ALERT",
            "The conservation signal stays healthy while difficult categories are being avoided.",
            {"easy_categories": easy, "hard_categories": hard, "easy_volume": easy_volume, "hard_volume": hard_volume, "volume_ratio": round(easy_volume / hard_volume, 2)},
            "Route representative hard cases into the measured window before permitting more autonomy.",
        )]

    def _verified_decisions(self) -> list[dict[str, Any]]:
        reader = getattr(self._store, "get_verified_decisions", None)
        if not callable(reader):
            return []
        return [dict(row) for row in reader(self._domain) if isinstance(row, dict)]


def trap_asdict(trap: TrustTrap) -> dict[str, Any]:
    return asdict(trap)


def _category(row: dict[str, Any]) -> str:
    return str(row.get("category") or "uncategorized")


def _accuracy(rows: list[dict[str, Any]]) -> float:
    return sum(1 for row in rows if _is_correct(row)) / len(rows) if rows else 0.0


def _is_correct(row: dict[str, Any]) -> bool:
    if "is_correct" in row:
        return bool(row.get("is_correct"))
    if "outcome_correct" in row:
        return bool(row.get("outcome_correct"))
    return str(row.get("outcome") or "").lower() in {"confirmed", "correct", "success"}


def _category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        category = _category(row)
        counts[category] = counts.get(category, 0) + 1
    return counts


def _gini(values: list[int]) -> float:
    ordered = sorted(values)
    total = sum(ordered)
    if not ordered or total == 0:
        return 0.0
    weighted = sum((index + 1) * value for index, value in enumerate(ordered))
    return (2 * weighted) / (len(ordered) * total) - (len(ordered) + 1) / len(ordered)
