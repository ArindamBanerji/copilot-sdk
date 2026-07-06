from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from copilot_sdk.graph import SQLiteGraphStore


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app import context_router  # noqa: E402
from app.data_helpers import write_purchasing_fixture  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch) -> Path:
    source_data = BACKEND_ROOT / "data"
    temp_data = tmp_path / "data"
    temp_data.mkdir()
    for filename in (
        "waste_history.json",
        "weather_cache.json",
        "evolution_fixtures.json",
        "purchasing_seed_v2.json",
        "analytics_cache.json",
    ):
        (temp_data / filename).write_text(
            (source_data / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    write_purchasing_fixture(temp_data / "order_metadata.json", {})

    monkeypatch.setattr(context_router, "_DATA_DIR", temp_data)
    import app.main as main_module

    monkeypatch.setattr(main_module, "DATA_DIR", temp_data)
    return temp_data


@pytest.fixture
def client(tmp_path, temp_data_dir) -> TestClient:
    db_path = tmp_path / "purchasing_test.db"
    store = SQLiteGraphStore(str(db_path), domain="purchasing", decision_id_prefix="PUR-")
    _seed_ae_events(store)
    app = create_app(db_path=db_path, demo_bundle_path=False)
    return TestClient(app)


def _seed_ae_events(store: SQLiteGraphStore) -> None:
    store.save_evolution_event(
        domain="purchasing",
        event_type="promotion_approved",
        rule_name="produce_weather_waste_signal",
        variant_id="purchasing-produce-weather-v1",
        metadata={
            "id": "V-PUR-FRIDAY-001",
            "artifact_type": "ordering_rule",
            "description": "Reduce produce over-ordering before rainy Friday demand dips.",
            "impact": "waste_reduction",
            "magnitude": 0.18,
            "timestamp": "2026-05-08T11:20:00Z",
            "wins": 22,
            "total": 31,
            "source_copilot": "purchasing",
            "source_rule": "produce_weather_waste_signal",
            "match": {
                "categories": ["produce"],
                "weather": "rain",
                "day_of_week": "Friday",
            },
        },
    )
    store.save_evolution_event(
        domain="purchasing",
        event_type="promotion_approved",
        rule_name="event_stockout_signal",
        variant_id="purchasing-event-stockout-v1",
        metadata={
            "id": "V-PUR-EVENT-001",
            "artifact_type": "context_policy",
            "description": "Increase protein replenishment when event calendars create stockout pressure.",
            "impact": "stockout_prevention",
            "magnitude": 0.21,
            "timestamp": "2026-05-08T11:35:00Z",
            "wins": 16,
            "total": 22,
            "source_copilot": "dataops",
            "source_rule": "recurrence_frequency_signal",
            "match": {
                "categories": ["protein"],
                "event_required": True,
            },
        },
    )
    store.save_evolution_event(
        domain="purchasing",
        event_type="promotion_rejected",
        rule_name="skip_dairy_rule",
        variant_id="purchasing-skip-dairy-v1",
        metadata={
            "id": "V-PUR-DAIRY-001",
            "artifact_type": "ordering_rule",
            "description": "Reject blanket dairy skips after spoilage improvements.",
            "impact": "risk_control",
            "magnitude": 0.08,
            "timestamp": "2026-05-08T11:50:00Z",
            "wins": 4,
            "total": 15,
            "reject_reason": "Reduced stock led to service-level failures",
            "match": {
                "categories": ["dairy"],
            },
        },
    )
