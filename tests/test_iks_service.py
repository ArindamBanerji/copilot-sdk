from __future__ import annotations

from copilot_sdk import IKSService


class Shape:
    category_names = ("protein", "produce")


class Store:
    def __init__(self, decisions):
        self._decisions = decisions

    def get_verified_decisions(self, domain):
        return list(self._decisions)


def test_iks_service_importable_from_sdk_root():
    assert IKSService is not None


def test_iks_service_returns_zero_for_no_verified_decisions():
    service = IKSService(Store([]), domain="purchasing", shape=Shape(), categories=Shape.category_names)

    payload = service.summary()

    assert payload["iks"] == 0.0
    assert payload["per_category"] == {"protein": 0.0, "produce": 0.0}
    assert payload["available"] is False


def test_iks_service_uses_trajectory_for_per_category_breakdown():
    decisions = [
        {"decision_id": "p-1", "category": "protein", "created_at": 1.0, "is_correct": True},
        {"decision_id": "p-2", "category": "protein", "created_at": 2.0, "is_correct": True},
        {"decision_id": "r-1", "category": "produce", "created_at": 3.0, "is_correct": False},
    ]
    service = IKSService(Store(decisions), domain="purchasing", shape=Shape(), categories=Shape.category_names)

    payload = service.summary()

    assert payload["iks"] > 0.0
    assert payload["per_category"]["protein"] > 0.0
    assert payload["per_category"]["produce"] > 0.0
    assert payload["verified_count"] == 3
