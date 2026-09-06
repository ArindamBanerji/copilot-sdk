from __future__ import annotations

import json
from pathlib import Path

from app import dashboard_router


def test_dashboard_orders_projects_only_order_card_fields(client, tmp_path: Path, monkeypatch) -> None:
    metadata_path = tmp_path / "order_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "decision-1": {
                    "item": "chicken_breast",
                    "display_name": "Chicken Breast",
                    "category": "protein",
                    "action": "order_as_planned",
                    "reward": 0.8,
                    "created_at": "2026-01-01T00:00:00Z",
                    "total_cost": 177.1,
                    "unused_detail": "not returned",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dashboard_router, "_ORDER_METADATA_PATH", metadata_path)

    response = client.get("/api/dashboard/orders")

    assert response.status_code == 200
    assert response.json() == {
        "decision-1": {
            "item": "chicken_breast",
            "display_name": "Chicken Breast",
            "category": "protein",
            "action": "order_as_planned",
            "reward": 0.8,
            "created_at": "2026-01-01T00:00:00Z",
            "total_cost": 177.1,
        }
    }


def test_dashboard_orders_projection_is_compact(client) -> None:
    response = client.get("/api/dashboard/orders")

    assert response.status_code == 200
    assert len(response.content) < 100_000
