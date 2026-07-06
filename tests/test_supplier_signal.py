from __future__ import annotations

from dataclasses import dataclass
import sys
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
PURCHASING_BACKEND = ROOT / "apps" / "purchasing" / "backend"

from copilot_sdk.outbox import EVENT_TYPES, OutboxEventType, OutboxStore


@pytest.fixture(autouse=True)
def isolated_app_imports():
    original_path = list(sys.path)
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    if str(PURCHASING_BACKEND) not in sys.path:
        sys.path.insert(0, str(PURCHASING_BACKEND))
    yield
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)
    sys.path[:] = original_path


def _publisher_class():
    from app.services.supplier_signal_publisher import SupplierSignalPublisher

    return SupplierSignalPublisher


def _alert_engine_class():
    from app.services.alert_engine import PurchasingAlertEngine

    return PurchasingAlertEngine


def _signal_router_factory():
    from app.routers.signal_router import create_signal_router

    return create_signal_router


@dataclass
class Card:
    supplier_name: str = "Sysco"
    reliability_pct: float = 74.0
    previous_reliability_pct: float = 93.0
    trend: str = "declining"


@dataclass
class CardWithoutPrevious:
    supplier_name: str = "Sysco"
    reliability_pct: float = 74.0
    trend: str = "declining"


class ScorecardService:
    def __init__(self, card: Card):
        self.card = card

    def build_all(self, min_orders=1):
        return [self.card]


class NoMenuAlerts:
    def analyze(self, rows):
        return []

    def margin_alerts(self, rows):
        return []


def test_supplier_reliability_signal_event_type_registered():
    assert OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL in EVENT_TYPES


def test_publisher_publishes_when_reliability_below_threshold(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    published = _publisher_class()(store).check_and_publish(Card(reliability_pct=79.0, trend="stable"))
    events = store.replay_from(0)

    assert published is True
    assert events[0].event_type == OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL


def test_publisher_does_not_publish_when_supplier_stable(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    published = _publisher_class()(store).check_and_publish(Card(reliability_pct=91.0, trend="stable"))

    assert published is False
    assert store.replay_from(0) == []


def test_publisher_does_not_publish_at_reliability_boundary(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    published = _publisher_class()(store).check_and_publish(Card(reliability_pct=80.0, trend="stable"))

    assert published is False
    assert store.replay_from(0) == []


def test_publisher_publishes_just_below_reliability_boundary(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    published = _publisher_class()(store).check_and_publish(Card(reliability_pct=79.9, trend="stable"))

    assert published is True
    assert len(store.replay_from(0)) == 1


def test_publisher_is_idempotent_for_active_supplier_signal(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    publisher = _publisher_class()(store)

    first = publisher.check_and_publish(Card())
    second = publisher.check_and_publish(Card(reliability_pct=70.0, previous_reliability_pct=90.0))

    assert first is True
    assert second is False
    assert len(store.replay_from(0)) == 1


def test_signal_payload_has_provenance_supplier_and_delta(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())
    payload = store.replay_from(0)[0].payload

    assert payload["provenance"] == "signal"
    assert payload["supplier_name"] == "Sysco"
    assert payload["delta"] == -19.0
    assert payload["ttl_days"] == 7


def test_signal_payload_has_null_delta_when_no_previous_reliability(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(CardWithoutPrevious())
    payload = store.replay_from(0)[0].payload

    assert payload["previous_pct"] is None
    assert payload["delta"] is None


def test_signal_payload_uses_previous_signal_for_delta_when_available(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    store.append(
        OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
        "purchasing",
        {
            "supplier_name": "Sysco",
            "reliability_pct": 88.0,
            "previous_pct": None,
            "delta": None,
            "trend": "declining",
            "source_copilot": "purchasing",
            "target_copilot": "s2p",
            "timestamp": time.time() - 8 * 86400,
            "ttl_days": 7,
            "provenance": "signal",
        },
    )

    _publisher_class()(store).check_and_publish(CardWithoutPrevious(reliability_pct=74.0))
    payload = store.replay_from(0)[-1].payload

    assert payload["previous_pct"] == 88.0
    assert payload["delta"] == -14.0


def test_outbox_store_clear_removes_signal_events(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())

    store.clear()

    assert store.replay_from(0) == []


def test_alert_engine_publishes_signal_when_trend_declining(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    publisher = _publisher_class()(store)
    engine = _alert_engine_class()(
        menu_engineer=NoMenuAlerts(),
        scorecard_service=ScorecardService(Card(trend="declining")),
        signal_publisher=publisher,
    )

    alerts = engine.evaluate(orders=[], suppliers=[], conservation_status={"state": "GREEN"})

    assert any(alert["alert_type"] == "supplier_degradation" for alert in alerts)
    assert len(store.replay_from(0)) == 1


def test_alert_engine_does_not_publish_signal_when_stable(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    publisher = _publisher_class()(store)
    engine = _alert_engine_class()(
        menu_engineer=NoMenuAlerts(),
        scorecard_service=ScorecardService(Card(reliability_pct=91.0, trend="stable")),
        signal_publisher=publisher,
    )

    alerts = engine.evaluate(orders=[], suppliers=[], conservation_status={"state": "GREEN"})

    assert not any(alert["alert_type"] == "supplier_degradation" for alert in alerts)
    assert store.replay_from(0) == []


def test_signal_endpoint_returns_published_signals(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())
    app = FastAPI()
    app.include_router(_signal_router_factory()(store))

    response = TestClient(app).get("/api/purchasing/signals/supplier/Sysco")

    assert response.status_code == 200
    assert response.json()[0]["supplier_name"] == "Sysco"


def test_signal_endpoint_returns_empty_for_unknown_supplier(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())
    app = FastAPI()
    app.include_router(_signal_router_factory()(store))

    response = TestClient(app).get("/api/purchasing/signals/supplier/Unknown")

    assert response.status_code == 200
    assert response.json() == []


def test_signal_stats_endpoint_counts_active_and_expired(tmp_path):
    store = OutboxStore(tmp_path / "outbox.db")
    _publisher_class()(store).check_and_publish(Card())
    store.append(
        OutboxEventType.SUPPLIER_RELIABILITY_SIGNAL,
        "purchasing",
        {
            "supplier_name": "Old Supplier",
            "reliability_pct": 70.0,
            "previous_pct": 90.0,
            "delta": -20.0,
            "trend": "declining",
            "source_copilot": "purchasing",
            "target_copilot": "s2p",
            "timestamp": time.time() - 8 * 86400,
            "ttl_days": 7,
            "provenance": "signal",
        },
    )
    app = FastAPI()
    app.include_router(_signal_router_factory()(store))

    response = TestClient(app).get("/api/purchasing/signals/stats")

    assert response.status_code == 200
    assert response.json() == {"total_published": 2, "active": 1, "expired": 1}
