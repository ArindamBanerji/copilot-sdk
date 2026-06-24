from __future__ import annotations

from app.services.waste_tracker import WasteTracker


def _orders(wastes: list[float], category: str = "protein"):
    return [
        {
            "category": category,
            "items": [{"name": "salmon", "quantity": 10, "unit_cost": 12}],
            "outcome": {"waste_pct": waste},
        }
        for waste in wastes
    ]


def test_analyze_basic():
    profiles = WasteTracker(_orders([0.1, 0.12, 0.13, 0.14, 0.15])).analyze_all()
    assert profiles[0].item == "salmon"
    assert profiles[0].order_count == 5


def test_analyze_insufficient():
    assert WasteTracker(_orders([0.1, 0.2, 0.3])).analyze_all() == []


def test_above_benchmark():
    profile = WasteTracker(_orders([0.18, 0.19, 0.2, 0.18, 0.19])).analyze_all()[0]
    assert profile.flagged is True


def test_below_benchmark():
    profile = WasteTracker(_orders([0.08, 0.09, 0.1, 0.08, 0.09])).analyze_all()[0]
    assert profile.flagged is False


def test_trend_improving():
    profile = WasteTracker(_orders([0.2, 0.2, 0.2, 0.08, 0.08, 0.08])).analyze_all()[0]
    assert profile.trend == "improving"


def test_trend_worsening():
    profile = WasteTracker(_orders([0.08, 0.08, 0.08, 0.2, 0.2, 0.2])).analyze_all()[0]
    assert profile.trend == "worsening"


def test_weekly_cost():
    summary = WasteTracker(_orders([0.1, 0.1, 0.1, 0.1, 0.1])).weekly_waste_cost()
    assert summary["weekly_waste_cost"] == 60


def test_recommendation_protein():
    profile = WasteTracker(_orders([0.2, 0.2, 0.2, 0.2, 0.2])).analyze_all()[0]
    assert "pre-portioned" in profile.recommendation


def test_recommendation_produce():
    profile = WasteTracker(_orders([0.3, 0.3, 0.3, 0.3, 0.3], "produce")).analyze_all()[0]
    assert "Reduce par" in profile.recommendation


def test_top_waste_sorted():
    orders = _orders([0.2, 0.2, 0.2, 0.2, 0.2])
    orders += [
        {
            "category": "produce",
            "items": [{"name": "greens", "quantity": 5, "unit_cost": 4}],
            "outcome": {"waste_pct": 0.1},
        }
        for _ in range(5)
    ]
    top = WasteTracker(orders).top_waste_items()
    assert top[0].item == "salmon"
