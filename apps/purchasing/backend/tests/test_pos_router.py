from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.purchasing.backend.app.connectors.mock_toast import MockToastConnector
from apps.purchasing.backend.app.main import create_app
from apps.purchasing.backend.app.routers.pos_router import create_pos_router


def _client() -> TestClient:
    return TestClient(create_app(db_path=":memory:", demo_bundle_path=False))


def test_pos_today_returns_200():
    """GET /api/purchasing/pos/today returns 200."""
    response = _client().get("/api/purchasing/pos/today")
    assert response.status_code == 200


def test_pos_today_has_covers():
    """Response includes 'covers' field."""
    payload = _client().get("/api/purchasing/pos/today").json()
    assert "covers" in payload
    assert isinstance(payload["covers"], int)


def test_pos_today_has_revenue():
    """Response includes 'total_revenue'."""
    payload = _client().get("/api/purchasing/pos/today").json()
    assert "total_revenue" in payload
    assert isinstance(payload["total_revenue"], float)


def test_pos_today_has_items():
    """Response includes 'items' list with kitchen categories."""
    payload = _client().get("/api/purchasing/pos/today").json()
    assert isinstance(payload["items"], list)
    assert payload["items"]


def test_pos_today_has_dayparts():
    """Response includes dayparts."""
    payload = _client().get("/api/purchasing/pos/today").json()
    assert set(payload["dayparts"]) == {"lunch", "dinner", "late_night"}


def test_pos_today_item_categories_match_purchasing():
    """Item categories are Purchasing categories."""
    valid = {"protein", "produce", "dairy", "dry_goods", "beverages"}
    payload = _client().get("/api/purchasing/pos/today").json()
    for item in payload["items"]:
        assert item["category"] in valid


def test_pos_profile_returns_200():
    """GET /api/purchasing/pos/profile returns 200."""
    response = _client().get("/api/purchasing/pos/profile")
    assert response.status_code == 200


def test_pos_profile_has_source_name():
    """Profile response includes source_name = 'toast_pos_mock'."""
    payload = _client().get("/api/purchasing/pos/profile").json()
    assert payload["source_name"] == "toast_pos_mock"


def test_pos_profile_has_freshness():
    """Profile response includes freshness metrics."""
    payload = _client().get("/api/purchasing/pos/profile").json()
    assert "freshness_score" in payload
    assert 0.0 <= payload["freshness_score"] <= 1.0


def test_pos_profile_has_record_count():
    """Profile response shows records profiled."""
    payload = _client().get("/api/purchasing/pos/profile").json()
    assert payload["record_count"] == 7


def test_profiler_wired_to_mock_connector():
    """The profiler instance uses MockToastConnector, not a stub."""
    payload = _client().get("/api/purchasing/pos/profile").json()
    assert payload["source_name"] == MockToastConnector.source_name
    assert payload["entity_type"] == MockToastConnector.entity_type


def test_pos_today_no_crash_on_empty_data():
    """If mock has no data for today's date, returns empty/graceful."""
    connector = MockToastConnector()
    connector._data = {}

    app = FastAPI()
    app.include_router(create_pos_router(lambda: connector))
    response = TestClient(app).get("/api/purchasing/pos/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["covers"] == 0
    assert payload["items"] == []
    assert payload["records"] == []
