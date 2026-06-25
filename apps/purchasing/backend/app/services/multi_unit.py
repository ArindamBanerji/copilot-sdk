"""Multi-location purchasing intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from app.services.economic_model import PurchasingEconomicModel
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.transfer.chain_transfer import ChainTransfer, LocationStore


@dataclass
class GroupDashboard:
    locations: list[dict[str, Any]]
    weighted_accuracy: float
    best_location: str | None
    needs_help_location: str | None
    economic: dict[str, Any]
    purchasing_power: dict[str, Any]
    transfer_opportunities: list[dict[str, Any]]
    provenance: str = "demo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MultiUnitManager:
    """Group dashboard across restaurant locations."""

    def __init__(
        self,
        chain_transfer: ChainTransfer | None = None,
        economic_model: PurchasingEconomicModel | None = None,
    ) -> None:
        self.chain_transfer = chain_transfer or ChainTransfer()
        self.economic_model = economic_model or PurchasingEconomicModel()

    def dashboard(self, locations: list[dict[str, Any]]) -> GroupDashboard:
        rows = [dict(location) for location in locations]
        weighted_accuracy = _weighted_accuracy(rows)
        best = max(rows, key=lambda row: float(row.get("accuracy") or 0.0), default=None)
        worst = min(rows, key=lambda row: float(row.get("accuracy") or 1.0), default=None)
        decisions = sum(int(row.get("decisions") or 0) for row in rows)
        economic = self.economic_model.compute(decisions).to_dict()
        return GroupDashboard(
            locations=rows,
            weighted_accuracy=round(weighted_accuracy, 4),
            best_location=str(best.get("name")) if best else None,
            needs_help_location=str(worst.get("name")) if worst else None,
            economic=economic,
            purchasing_power={
                **self.group_purchasing_power(rows),
                "price_benchmark": self.cross_location_price(rows),
                "waste_benchmark": self.cross_location_waste(rows),
                "supplier_benchmark": self.cross_location_supplier(rows),
            },
            transfer_opportunities=self.find_transfer_opportunities(rows),
        )

    def find_transfer_opportunities(self, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        opportunities: list[dict[str, Any]] = []
        stores = [_location_store(row) for row in locations]
        for source in stores:
            for target in stores:
                if source.location_id == target.location_id:
                    continue
                valid = self.chain_transfer.validate(source, target)
                target_needs_help = target.decisions < 50 or target.accuracy < 0.65
                if valid.get("valid") and source.accuracy > 0.80 and target_needs_help:
                    opportunities.append({
                        "source": source.location_id,
                        "target": target.location_id,
                        "estimated_accuracy": self.chain_transfer.estimate_accuracy(source.accuracy),
                        "message": f"{source.location_id} can help {target.location_id} on day one.",
                    })
        return opportunities

    def group_purchasing_power(self, locations: list[dict[str, Any]]) -> dict[str, Any]:
        supplier_totals: dict[str, float] = {}
        for location in locations:
            spend = location.get("supplier_spend") if isinstance(location.get("supplier_spend"), dict) else {}
            for supplier, amount in spend.items():
                supplier_totals[str(supplier)] = supplier_totals.get(str(supplier), 0.0) + float(amount or 0.0)
        best_supplier, total = max(supplier_totals.items(), key=lambda item: item[1], default=("Sysco", 0.0))
        return {
            "supplier": best_supplier,
            "monthly_spend": round(total, 2),
            "threshold": 50000.0,
            "callout": f"${total:,.0f}/month from {best_supplier} across {len(locations)} locations. Volume discount opportunity at $50K.",
        }

    def compare(self, locations: list[dict[str, Any]], metric: str = "accuracy") -> list[dict[str, Any]]:
        return sorted(
            [dict(location) for location in locations],
            key=lambda row: float(row.get(metric) or 0.0),
            reverse=True,
        )

    def cross_location_price(self, locations: list[dict[str, Any]], item: str | None = "salmon") -> dict[str, Any]:
        prices = []
        for location in locations:
            price_map = location.get("item_prices") if isinstance(location.get("item_prices"), dict) else {}
            price = price_map.get(item or "") or location.get("salmon_price")
            if price is not None:
                prices.append({"location": location.get("name"), "price": float(price)})
        if len(prices) < 2:
            return {"item": item, "price_spread_pct": 0.0, "recommendation": "Not enough location price history yet."}
        low = min(prices, key=lambda row: row["price"])
        high = max(prices, key=lambda row: row["price"])
        spread = ((high["price"] - low["price"]) / low["price"]) * 100.0 if low["price"] else 0.0
        return {
            "item": item,
            "low_location": low["location"],
            "high_location": high["location"],
            "price_spread_pct": round(spread, 1),
            "recommendation": f"{item.title()}: {low['location']} is cheaper. Review {high['location']} supplier pricing.",
        }

    def cross_location_waste(self, locations: list[dict[str, Any]]) -> dict[str, Any]:
        rows = [
            {"location": row.get("name"), "waste_rate": float(row.get("waste_rate") or 0.0)}
            for row in locations
            if row.get("waste_rate") is not None
        ]
        if len(rows) < 2:
            return {"waste_spread_pct": 0.0, "recommendation": "Not enough waste history yet."}
        low = min(rows, key=lambda row: row["waste_rate"])
        high = max(rows, key=lambda row: row["waste_rate"])
        return {
            "best_location": low["location"],
            "needs_help_location": high["location"],
            "waste_spread_pct": round((high["waste_rate"] - low["waste_rate"]) * 100.0, 1),
            "recommendation": f"{high['location']} should adopt {low['location']}'s par levels.",
        }

    def cross_location_supplier(self, locations: list[dict[str, Any]], supplier: str | None = "Sysco") -> dict[str, Any]:
        rows = []
        for location in locations:
            supplier_perf = location.get("supplier_otif") if isinstance(location.get("supplier_otif"), dict) else {}
            otif = supplier_perf.get(supplier or "")
            if otif is not None:
                rows.append({"location": location.get("name"), "otif": float(otif)})
        if len(rows) < 2:
            return {"supplier": supplier, "otif_spread_pct": 0.0, "recommendation": "Not enough supplier history yet."}
        best = max(rows, key=lambda row: row["otif"])
        worst = min(rows, key=lambda row: row["otif"])
        return {
            "supplier": supplier,
            "best_location": best["location"],
            "needs_help_location": worst["location"],
            "otif_spread_pct": round((best["otif"] - worst["otif"]) * 100.0, 1),
            "recommendation": f"{supplier} performs better in {best['location']}. Review {worst['location']} receiving process.",
        }


def demo_locations() -> list[dict[str, Any]]:
    return [
        {"id": "chicago", "name": "Chicago", "decisions": 500, "accuracy": 0.84, "food_cost_pct": 0.29, "conservation": "GREEN", "supplier_spend": {"Sysco": 22000, "Fresh Produce": 9000}, "waste_cost": 410, "waste_rate": 0.08, "item_prices": {"salmon": 14.20}, "supplier_otif": {"Sysco": 0.96}},
        {"id": "miami", "name": "Miami", "decisions": 20, "accuracy": 0.58, "food_cost_pct": 0.35, "conservation": "GREEN", "supplier_spend": {"Sysco": 16000, "Fresh Produce": 6000}, "waste_cost": 690, "waste_rate": 0.14, "item_prices": {"salmon": 15.80}, "supplier_otif": {"Sysco": 0.82}},
        {"id": "austin", "name": "Austin", "decisions": 180, "accuracy": 0.72, "food_cost_pct": 0.31, "conservation": "AMBER", "supplier_spend": {"Sysco": 7000, "Fresh Produce": 5000}, "waste_cost": 520, "waste_rate": 0.11, "item_prices": {"salmon": 14.90}, "supplier_otif": {"Sysco": 0.90}},
    ]


def _weighted_accuracy(locations: list[dict[str, Any]]) -> float:
    total = sum(int(row.get("decisions") or 0) for row in locations)
    if total <= 0:
        return 0.0
    weighted = sum(float(row.get("accuracy") or 0.0) * int(row.get("decisions") or 0) for row in locations)
    return weighted / total


def _location_store(row: dict[str, Any]) -> LocationStore:
    preset = PurchasingPreset()
    shape = (preset.shape.n_categories, preset.shape.n_actions, preset.shape.n_factors)
    accuracy = float(row.get("accuracy") or 0.5)
    return LocationStore(
        location_id=str(row.get("name") or row.get("id") or "Location"),
        decisions=int(row.get("decisions") or 0),
        accuracy=accuracy,
        conservation=str(row.get("conservation") or "GREEN"),
        categories=list(preset.shape.category_names),
        actions=list(preset.shape.action_names),
        pattern_grid=np.ones(shape, dtype=float) * max(0.5, min(0.9, accuracy)),
        dk_weights={"supplier": 0.5},
    )
