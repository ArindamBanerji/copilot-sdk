from __future__ import annotations

from copilot_sdk.graph import InMemoryGraphStore

from copilot_sdk import IKSService


class Shape:
    category_names = ("protein", "produce")


class Store(InMemoryGraphStore):
    def __init__(self, decisions=None) -> None:
        super().__init__(domain="purchasing")
        for row in decisions or []:
            metadata = {**row.get("metadata", {}), "decision_id": row["decision_id"],
                        "created_at": row["created_at"]}
            decision_id = self.write_decision("purchasing", row["category"], "accept", 0.8, {}, metadata=metadata)
            self.write_outcome(decision_id, "accept", row["is_correct"], domain="purchasing")


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
