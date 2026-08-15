from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.predictive_par import PredictivePar, demo_par_items


def test_friday_higher():
    service = PredictivePar()
    friday = service.predict("salmon", "protein", "2026-06-26", 40, conservation_status="GREEN")
    assert friday.adjusted_par > 40


def test_monday_lower():
    service = PredictivePar()
    monday = service.predict("salmon", "protein", "2026-06-22", 40, conservation_status="GREEN")
    assert monday.adjusted_par < 40


def test_storm_reduces_produce():
    service = PredictivePar()
    normal = service.predict("romaine", "produce", "2026-06-25", 40, conservation_status="GREEN")
    storm = service.predict("romaine", "produce", "2026-06-25", 40, conservation_status="GREEN", weather={"condition": "storm"})
    assert storm.adjusted_par < normal.adjusted_par


def test_event_buffer():
    service = PredictivePar()
    base = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN")
    event = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN", event=True)
    assert event.adjusted_par > base.adjusted_par


def test_cover_forecast():
    service = PredictivePar()
    low = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN", cover_forecast=80)
    high = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN", cover_forecast=140)
    assert high.adjusted_par > low.adjusted_par


def test_stacking():
    service = PredictivePar()
    result = service.predict("salmon", "protein", "2026-06-26", 40, conservation_status="GREEN", cover_forecast=140, event=True)
    assert result.adjusted_par > 56


def test_safety_floor():
    service = PredictivePar()
    result = service.predict("romaine", "produce", "2026-06-22", 40, conservation_status="GREEN", weather={"condition": "storm"}, cover_forecast=10)
    assert result.adjusted_par >= 20


def test_safety_ceiling():
    service = PredictivePar()
    result = service.predict("salmon", "protein", "2026-06-27", 40, conservation_status="GREEN", cover_forecast=300, event=True)
    assert result.adjusted_par <= 80


def test_no_signals():
    service = PredictivePar()
    result = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN")
    assert result.adjusted_par == 40


def test_predict_week():
    data = PredictivePar().predict_week(demo_par_items())
    assert len(data["items"]) == 14


def test_confidence():
    result = PredictivePar().predict("salmon", "protein", "2026-06-26", 40, conservation_status="GREEN", cover_forecast=120, event=True)
    assert result.confidence == "high"


def test_router_predict():
    app = create_app(db_path=":memory:", demo_bundle_path=False)
    app.state.purchasing_conservation_status = "GREEN"
    client = TestClient(app)
    response = client.get("/api/purchasing/par/predict?item=salmon&category=protein&date=2026-06-26")
    assert response.status_code == 200
    assert response.json()["adjusted_par"] > 40


def test_router_predict_blocks_malformed_conservation_override():
    app = create_app(db_path=":memory:", demo_bundle_path=False)
    app.state.purchasing_conservation_status = {}
    client = TestClient(app)

    response = client.get("/api/purchasing/par/predict?item=salmon&category=protein&date=2026-06-26")

    assert response.status_code == 200
    assert response.json()["confidence"] == "blocked"


def test_integrates_with_par_optimizer():
    class Optimizer:
        def recommend(self, *args, **kwargs):
            return SimpleNamespace(recommended_par=33)

    assert PredictivePar(optimizer=Optimizer()).base_from_optimizer("salmon", "protein", []) == 33


def test_adjusted_differs_when_signals():
    service = PredictivePar()
    base = service.predict("salmon", "protein", "2026-06-25", 40, conservation_status="GREEN")
    adjusted = service.predict("salmon", "protein", "2026-06-26", 40, conservation_status="GREEN", event=True)
    assert adjusted.adjusted_par != base.adjusted_par


def test_predict_blocked_when_not_green():
    result = PredictivePar().predict(
        "salmon",
        "protein",
        "2026-06-26",
        40,
        conservation_status="AMBER",
    )
    assert result.adjusted_par == 40
    assert result.confidence == "blocked"
    assert "GREEN" in result.explanation


def test_predict_blocked_when_conservation_missing():
    result = PredictivePar().predict("salmon", "protein", "2026-06-26", 40)

    assert result.adjusted_par == 40
    assert result.confidence == "blocked"


def test_predict_allowed_when_green():
    result = PredictivePar().predict(
        "salmon",
        "protein",
        "2026-06-26",
        40,
        conservation_status="GREEN",
    )
    assert result.adjusted_par > 40
    assert result.confidence != "blocked"


def test_endpoint_uses_par_optimizer():
    class Optimizer:
        called = False

        def recommend(self, *args, **kwargs):
            Optimizer.called = True
            return SimpleNamespace(recommended_par=33)

    app = create_app(db_path=":memory:", demo_bundle_path=False)
    app.state.purchasing_par_optimizer = Optimizer()
    app.state.purchasing_conservation_status = "GREEN"
    client = TestClient(app)
    response = client.get("/api/purchasing/par/predict?item=salmon&category=protein&date=2026-06-25")
    assert response.status_code == 200
    assert Optimizer.called is True
    assert response.json()["base_par"] == 33


def test_endpoint_base_par_varies_by_item():
    class Optimizer:
        def recommend(self, item, *args, **kwargs):
            if item == "salmon":
                return SimpleNamespace(recommended_par=44)
            return SimpleNamespace(recommended_par=22)

    app = create_app(db_path=":memory:", demo_bundle_path=False)
    app.state.purchasing_par_optimizer = Optimizer()
    app.state.purchasing_conservation_status = "GREEN"
    client = TestClient(app)
    salmon = client.get("/api/purchasing/par/predict?item=salmon&category=protein&date=2026-06-25").json()
    romaine = client.get("/api/purchasing/par/predict?item=romaine&category=produce&date=2026-06-25").json()
    assert salmon["base_par"] == 44
    assert romaine["base_par"] == 22
