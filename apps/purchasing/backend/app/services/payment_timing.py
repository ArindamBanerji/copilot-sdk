"""Demo per-supplier payment timing analysis."""

from __future__ import annotations

from typing import Any


class PaymentTimingService:
    """Per-supplier payment behavior analysis."""

    def __init__(self) -> None:
        self._suppliers = [
            {
                "supplier_id": "sysco",
                "supplier": "Sysco",
                "avg_payment_days": 28,
                "early_pay_discount_pct": 2.0,
                "discount_capture_rate": 0.3,
                "annual_discount_value": 4200.0,
                "recommendation": "Pay Sysco by day 10 when cash is clear; 7 more discounts are on the table.",
            },
            {
                "supplier_id": "freshpoint",
                "supplier": "FreshPoint",
                "avg_payment_days": 18,
                "early_pay_discount_pct": 1.5,
                "discount_capture_rate": 0.65,
                "annual_discount_value": 2600.0,
                "recommendation": "Keep FreshPoint on the early-pay run for produce weeks.",
            },
            {
                "supplier_id": "chen-lin",
                "supplier": "Chen-Lin Foods",
                "avg_payment_days": 35,
                "early_pay_discount_pct": 0.0,
                "discount_capture_rate": 0.0,
                "annual_discount_value": 0.0,
                "recommendation": "No early-pay discount. Hold payment until terms unless delivery slips.",
            },
        ]

    def analyze(self, supplier_id: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        rows = [self._with_provenance(row) for row in self._suppliers]
        if supplier_id is None:
            return rows
        normalized = supplier_id.strip().casefold()
        for row in rows:
            if row["supplier_id"].casefold() == normalized or row["supplier"].casefold() == normalized:
                return row
        return {
            "supplier_id": supplier_id,
            "supplier": supplier_id,
            "avg_payment_days": 0,
            "early_pay_discount_pct": 0.0,
            "discount_capture_rate": 0.0,
            "annual_discount_value": 0.0,
            "recommendation": "No payment history yet. Keep this supplier on standard terms.",
            "provenance": "demo",
        }

    def portfolio_summary(self) -> dict[str, Any]:
        rows = self._suppliers
        total_available = sum(float(row["annual_discount_value"]) / max(float(row["discount_capture_rate"]), 0.01) for row in rows if row["annual_discount_value"])
        total_captured = sum(float(row["annual_discount_value"]) for row in rows)
        avg_dpo = sum(float(row["avg_payment_days"]) for row in rows) / len(rows)
        capture_rate = total_captured / total_available if total_available else 0.0
        return {
            "total_suppliers": len(rows),
            "avg_dpo": round(avg_dpo, 1),
            "total_discount_available": round(total_available, 2),
            "total_captured": round(total_captured, 2),
            "capture_rate_pct": round(capture_rate * 100, 1),
            "annual_opportunity": round(total_available - total_captured, 2),
            "narrative": "Supplier Sysco: pays in 28 days. 2% discount if paid in 10. You captured 3 of 10 discounts. Annual opportunity: $4,200.",
            "provenance": "demo",
        }

    def _with_provenance(self, row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "provenance": "demo"}
