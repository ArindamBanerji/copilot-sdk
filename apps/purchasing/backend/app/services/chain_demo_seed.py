"""Demo data and transfer story for chain learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


@dataclass(frozen=True)
class ChainLocationSpec:
    location_id: str
    name: str
    decisions: int
    iks: int
    conservation: str
    waste_pct: float
    supplier_reliability: float


LOCATIONS = (
    ChainLocationSpec("downtown", "Downtown", 200, 58, "GREEN", 0.04, 0.92),
    ChainLocationSpec("airport", "Airport", 120, 31, "AMBER", 0.11, 0.78),
    ChainLocationSpec("suburb", "Suburb", 80, 18, "AMBER", 0.14, 0.71),
    ChainLocationSpec("new", "New", 15, 3, "RED", 0.22, 0.60),
)

class ChainLearningDemo:
    """Creates a four-location purchasing learning demo."""

    def seed(self) -> dict[str, Any]:
        locations = {spec.location_id: _location(spec) for spec in LOCATIONS}
        decisions = [
            decision
            for spec in LOCATIONS
            for decision in _decisions_for(spec)
        ]
        return {
            "locations": locations,
            "decisions": decisions,
            "provenance": "demo",
        }

    def seed_response(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "locations_seeded": len(state["locations"]),
            "total_decisions": len(state["decisions"]),
            "provenance": "demo",
        }

    def transfer(
        self,
        state: dict[str, Any],
        source_location: str = "downtown",
        target_locations: list[str] | None = None,
    ) -> dict[str, Any]:
        source_key = source_location.strip().lower()
        locations = state["locations"]
        if source_key not in locations:
            raise KeyError(source_location)
        source = locations[source_key]
        targets = target_locations or [key for key in locations if key != source_key]
        before: dict[str, dict[str, Any]] = {}
        after: dict[str, dict[str, Any]] = {}
        copied: list[str] = []
        skipped: list[dict[str, str]] = []

        for target_key in [target.strip().lower() for target in targets]:
            if target_key not in locations:
                skipped.append({"location": target_key, "reason": "unknown_location"})
                continue
            target = locations[target_key]
            before[target_key] = {"iks": target["iks"], "conservation": target["conservation"]}
            if target["conservation"] not in {"AMBER", "RED"}:
                skipped.append({"location": target_key, "reason": "target_not_amber_or_red"})
                after[target_key] = {"iks": target["iks"], "conservation": target["conservation"]}
                continue
            target["dk_weights"] = dict(source["dk_weights"])
            target["patterns"] = list(source["patterns"])
            target["iks"] = _transferred_iks(int(source["iks"]), int(target["iks"]), str(target["conservation"]))
            target["baseline_from"] = source["name"]
            copied.append(target_key)
            after[target_key] = {"iks": target["iks"], "conservation": target["conservation"]}

        return {
            "transferred": {
                "dk_weights": len(source["dk_weights"]) * len(copied),
                "patterns": ["weather_sensitivity", "event_lead_time"],
            },
            "before": before,
            "after": after,
            "locations_updated": copied,
            "skipped": skipped,
            "narrative": _narrative(before, after),
            "provenance": "demo",
        }


def _location(spec: ChainLocationSpec) -> dict[str, Any]:
    preset = PurchasingPreset()
    return {
        "location_id": spec.location_id,
        "name": spec.name,
        "decisions": spec.decisions,
        "iks": spec.iks,
        "conservation": spec.conservation,
        "waste_pct": spec.waste_pct,
        "supplier_reliability": spec.supplier_reliability,
        "categories": list(preset.shape.category_names),
        "dk_weights": _dk_weights(spec),
        "patterns": ["weather_sensitivity", "event_lead_time"],
        "provenance": "demo",
    }


def _dk_weights(spec: ChainLocationSpec) -> dict[str, float]:
    return {
        "expected_demand": round(0.42 + spec.iks / 200, 3),
        "day_of_week": 0.12,
        "weather_forecast": 0.13,
        "event_flag": 0.11,
        "historical_waste": round(max(0.06, 0.20 - spec.waste_pct), 3),
        "supplier_lead_time": round(spec.supplier_reliability / 5, 3),
        "price_memory_index": 0.10,
    }


def _decisions_for(spec: ChainLocationSpec) -> list[dict[str, Any]]:
    categories = list(PurchasingPreset().shape.category_names)
    rows: list[dict[str, Any]] = []
    for index in range(spec.decisions):
        category = categories[index % len(categories)]
        rows.append({
            "decision_id": f"{spec.location_id.upper()}-{index + 1:04d}",
            "location_id": spec.location_id,
            "location_name": spec.name,
            "category": category,
            "action": "order_as_planned" if index % 7 else "order_less",
            "is_correct": index % 100 < spec.iks,
            "factors": {
                "expected_demand": 0.68,
                "day_of_week": 0.45,
                "weather_forecast": 0.52,
                "event_flag": 0.22,
                "historical_waste": min(0.95, spec.waste_pct * 5),
                "supplier_lead_time": spec.supplier_reliability,
                "price_memory_index": 0.74,
            },
            "metadata": {"provenance": "demo", "source": "chain_learning_demo"},
            "provenance": "demo",
        })
    return rows


def _transferred_iks(source_iks: int, target_iks: int, conservation: str) -> int:
    if source_iks <= target_iks:
        return target_iks
    factor = 0.60 if conservation == "AMBER" else 0.45
    improvement = (source_iks - target_iks) * factor
    return min(source_iks, int(round(target_iks + improvement)))


def _narrative(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> str:
    parts = []
    for key in ("airport", "suburb", "new"):
        if key in before and key in after and after[key]["iks"] != before[key]["iks"]:
            parts.append(f"{key.title()}: IKS {before[key]['iks']}->{after[key]['iks']}")
    detail = ". ".join(parts)
    return f"Downtown's purchasing discipline transferred. {detail}."
