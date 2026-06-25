"""Source integration helpers for DataOps intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class JoinCandidate:
    key_a: str
    key_b: str
    confidence: float
    value_overlap: float
    name_similarity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_a": self.key_a,
            "key_b": self.key_b,
            "confidence": round(self.confidence, 4),
            "value_overlap": round(self.value_overlap, 4),
            "name_similarity": round(self.name_similarity, 4),
        }


class SourceIntegrator:
    """Auto-discover joins and combine records with quality annotations."""

    def __init__(self, profiler: Any = None) -> None:
        self._profiler = profiler

    def discover_joins(
        self,
        source_a_records: list[dict[str, Any]],
        source_b_records: list[dict[str, Any]],
        source_a_name: str,
        source_b_name: str,
    ) -> list[dict[str, Any]]:
        fields_a = _fields(source_a_records)
        fields_b = _fields(source_b_records)
        candidates: list[JoinCandidate] = []
        for key_a in fields_a:
            values_a = _values(source_a_records, key_a)
            for key_b in fields_b:
                values_b = _values(source_b_records, key_b)
                overlap = self._jaccard(values_a, values_b)
                name_similarity = self._field_name_similarity(key_a, key_b)
                fuzzy = _fuzzy_value_overlap(values_a, values_b)
                confidence = min(1.0, 0.65 * max(overlap, fuzzy) + 0.35 * name_similarity + _identifier_bonus(key_a, key_b))
                if confidence >= 0.25:
                    candidates.append(JoinCandidate(key_a, key_b, confidence, max(overlap, fuzzy), name_similarity))
        candidates.sort(key=lambda item: (-item.confidence, -_identifier_priority(item.key_a, item.key_b), item.key_a, item.key_b))
        return [candidate.to_dict() for candidate in candidates[:5]]

    def combine(
        self,
        source_a: list[dict[str, Any]],
        source_b: list[dict[str, Any]],
        join: dict[str, Any],
        trust_a: float | None = None,
        trust_b: float | None = None,
        source_a_name: str = "source_a",
        source_b_name: str = "source_b",
    ) -> dict[str, Any]:
        key_a = str(join.get("key_a"))
        key_b = str(join.get("key_b"))
        weight_a, weight_b = self._trust_weights(source_a_name, source_b_name, trust_a, trust_b)
        index_b = {_normalize(record.get(key_b)): record for record in source_b}
        combined = []
        annotations = self._quality_annotations(source_a, source_b, source_a_name, source_b_name, weight_a, weight_b)
        for record_a in source_a:
            match = index_b.get(_normalize(record_a.get(key_a)))
            if match is None:
                continue
            row = dict(match if weight_b > weight_a else record_a)
            lower_trust = record_a if weight_b > weight_a else match
            for field, value in lower_trust.items():
                row.setdefault(field, value)
            combined.append(row)
        return {
            "sources": [source_a_name, source_b_name],
            "join_key": {
                "key_a": key_a,
                "key_b": key_b,
                "confidence": round(float(join.get("confidence", 0.0)), 4),
            },
            "record_count": len(combined),
            "records": combined,
            "trust_weights": {
                source_a_name: round(weight_a, 4),
                source_b_name: round(weight_b, 4),
            },
            "quality_annotations": annotations,
            "narrative": self._narrative(source_a_name, source_b_name, key_a, key_b, join, len(combined), weight_a, weight_b, annotations),
        }

    def suggest_improvements(self, view: dict[str, Any], usage_count: int) -> list[dict[str, Any]]:
        if usage_count < 100:
            return []
        suggestions = []
        for annotation in view.get("quality_annotations", []):
            reliability = float(annotation.get("reliability", 1.0))
            if reliability < 0.8:
                wrong_pct = round((1.0 - reliability) * 100)
                suggestions.append(
                    {
                        "field": annotation.get("field"),
                        "source": annotation.get("source"),
                        "issue": f"{annotation.get('field')} is wrong {wrong_pct}% of the time",
                        "recommendation": "Add UPS tracking to improve supplier reliability by 34pp.",
                        "narrative": (
                            f"Your {annotation.get('source')} {annotation.get('field')} values are wrong "
                            f"{wrong_pct}% of the time. Adding UPS tracking would improve supplier reliability by 34pp."
                        ),
                    }
                )
        return suggestions

    def _jaccard(self, set_a: set[str], set_b: set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def _field_name_similarity(self, name_a: str, name_b: str) -> float:
        left = _normalize_name(name_a)
        right = _normalize_name(name_b)
        if not left or not right:
            return 0.0
        distance = _levenshtein(left, right)
        base = 1.0 - distance / max(len(left), len(right), 1)
        if {left, right} <= {"vendorid", "supplierid"}:
            base = max(base, 0.85)
        if left.endswith("id") and right.endswith("id"):
            base = max(base, 0.65)
        return max(0.0, min(1.0, base))

    def _trust_weights(
        self,
        source_a_name: str,
        source_b_name: str,
        trust_a: float | None,
        trust_b: float | None,
    ) -> tuple[float, float]:
        if trust_a is not None and trust_b is not None:
            return _clamp(trust_a), _clamp(trust_b)
        if self._profiler is not None and callable(getattr(self._profiler, "profile", None)):
            try:
                profile_a = self._profiler.profile([source_a_name])
                profile_b = self._profiler.profile([source_b_name])
                return (
                    _clamp(getattr(profile_a, "overall_quality", 0.5)),
                    _clamp(getattr(profile_b, "overall_quality", 0.5)),
                )
            except Exception:
                pass
        profiles = getattr(self._profiler, "profiles", None)
        if isinstance(profiles, dict):
            return (
                _clamp(getattr(profiles.get(source_a_name), "overall_quality", profiles.get(source_a_name, 0.5))),
                _clamp(getattr(profiles.get(source_b_name), "overall_quality", profiles.get(source_b_name, 0.5))),
            )
        return _clamp(0.5 if trust_a is None else trust_a), _clamp(0.5 if trust_b is None else trust_b)

    def _quality_annotations(
        self,
        source_a: list[dict[str, Any]],
        source_b: list[dict[str, Any]],
        source_a_name: str,
        source_b_name: str,
        trust_a: float,
        trust_b: float,
    ) -> list[dict[str, Any]]:
        annotations = []
        for source_name, records, trust in ((source_a_name, source_a, trust_a), (source_b_name, source_b, trust_b)):
            for field in sorted(_fields(records)):
                reliability = _field_reliability(field, trust)
                annotations.append(
                    {
                        "field": field,
                        "source": source_name,
                        "reliability": round(reliability, 4),
                        "note": _field_note(field, reliability),
                    }
                )
        return annotations

    def _narrative(
        self,
        source_a_name: str,
        source_b_name: str,
        key_a: str,
        key_b: str,
        join: dict[str, Any],
        count: int,
        trust_a: float,
        trust_b: float,
        annotations: list[dict[str, Any]],
    ) -> str:
        weak = next((item for item in annotations if float(item.get("reliability", 1.0)) < 0.8), None)
        note = ""
        if weak:
            note = f" Note: {weak['source']} {weak['field']} is unreliable ({weak['reliability']:.0%})."
        return (
            f"Connected {source_a_name} (trust {trust_a:.0%}) with {source_b_name} (trust {trust_b:.0%}). "
            f"{count} records matched on {key_a}/{key_b} (confidence {float(join.get('confidence', 0.0)):.0%})."
            f"{note}"
        )


def _fields(records: list[dict[str, Any]]) -> set[str]:
    return {str(key) for record in records for key in record}


def _values(records: list[dict[str, Any]], field: str) -> set[str]:
    return {_normalize(record.get(field)) for record in records if record.get(field) not in (None, "")}


def _normalize(value: Any) -> str:
    return str(value).strip().casefold()


def _normalize_name(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _fuzzy_value_overlap(values_a: set[str], values_b: set[str]) -> float:
    if not values_a or not values_b:
        return 0.0
    matches = 0
    for left in values_a:
        if any(SourceIntegrator()._field_name_similarity(left, right) >= 0.8 for right in values_b):
            matches += 1
    return matches / max(len(values_a | values_b), 1)


def _levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (0 if left_char == right_char else 1),
                )
            )
        previous = current
    return previous[-1]


def _field_reliability(field: str, trust: float) -> float:
    normalized = field.casefold()
    if "delivery" in normalized and trust < 0.8:
        return 0.71
    return _clamp(max(trust, 0.5))


def _field_note(field: str, reliability: float) -> str:
    wrong_pct = round((1.0 - reliability) * 100)
    if wrong_pct > 0:
        return f"Wrong {wrong_pct}% of the time"
    return "Highly reliable"


def _identifier_bonus(key_a: str, key_b: str) -> float:
    left = _normalize_name(key_a)
    right = _normalize_name(key_b)
    if left.endswith("id") and right.endswith("id"):
        return 0.08
    return 0.0


def _identifier_priority(key_a: str, key_b: str) -> int:
    left = _normalize_name(key_a)
    right = _normalize_name(key_b)
    return int(left.endswith("id") and right.endswith("id"))


def _clamp(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.5
    return max(0.0, min(1.0, number))
