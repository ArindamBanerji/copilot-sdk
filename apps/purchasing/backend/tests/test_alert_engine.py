from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.alert_engine import PurchasingAlertEngine, demo_orders


class NoMenuAlerts:
    def analyze(self, rows):
        return []

    def margin_alerts(self, rows):
        return []


def _engine() -> PurchasingAlertEngine:
    return PurchasingAlertEngine(menu_engineer=NoMenuAlerts())


def test_price_spike_detected():
    alerts = _engine().evaluate(orders=[{"item": "salmon", "current_price": 7.2, "average_price": 6.0}], suppliers=[], conservation_status={"state": "GREEN"})
    assert any(alert["alert_type"] == "price_spike" for alert in alerts)


def test_price_spike_below():
    alerts = _engine().evaluate(orders=[{"item": "salmon", "current_price": 6.6, "average_price": 6.0}], suppliers=[], conservation_status={"state": "GREEN"})
    assert not any(alert["alert_type"] == "price_spike" for alert in alerts)


def test_supplier_degradation():
    alerts = _engine().evaluate(orders=[], suppliers=[{"name": "Sysco", "previous_otif": 0.93, "current_otif": 0.74}], conservation_status={"state": "GREEN"})
    assert any(alert["alert_type"] == "supplier_degradation" for alert in alerts)


def test_supplier_stable():
    alerts = _engine().evaluate(orders=[], suppliers=[{"name": "Sysco", "previous_otif": 0.93, "current_otif": 0.90}], conservation_status={"state": "GREEN"})
    assert not any(alert["alert_type"] == "supplier_degradation" for alert in alerts)


def test_waste_threshold():
    alerts = _engine().evaluate(orders=demo_orders(), suppliers=[], conservation_status={"state": "GREEN"})
    assert any(alert["alert_type"] == "waste_threshold" for alert in alerts)


def test_stockout_risk():
    @dataclass
    class Rec:
        item_name: str = "salmon"
        current_par: float = 10
        recommended_par: float = 40

    class ParOptimizer:
        def recommend_all(self, items, orders):
            return [Rec()]

    alerts = PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), par_optimizer=ParOptimizer()).evaluate(
        orders=[{"item": "salmon", "category": "protein", "current_par": 10}],
        suppliers=[],
        conservation_status={"state": "GREEN"},
    )
    assert any(alert["alert_type"] == "stockout_risk" and alert["severity"] == "critical" for alert in alerts)


def test_conservation_amber():
    alerts = _engine().evaluate(orders=[], suppliers=[], conservation_status={"state": "AMBER", "category": "protein"})
    assert any(alert["alert_type"] == "conservation_amber" for alert in alerts)


def test_delivery_conflict():
    class BusyDelivery:
        def schedule_day(self, day):
            return {"deliveries": [{}, {}, {}, {}]}

    alerts = PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), delivery=BusyDelivery()).evaluate(orders=[], suppliers=[], conservation_status={"state": "GREEN"})
    assert any(alert["alert_type"] == "delivery_conflict" for alert in alerts)


def test_margin_erosion():
    alerts = PurchasingAlertEngine().evaluate(orders=[], suppliers=[], conservation_status={"state": "GREEN"})
    assert any(alert["alert_type"] == "margin_erosion" for alert in alerts)


def test_no_alerts():
    alerts = _engine().evaluate(orders=[], suppliers=[], conservation_status={"state": "GREEN"})
    assert alerts == []


def test_severity_sorting():
    @dataclass
    class Rec:
        item_name: str = "salmon"
        current_par: float = 10
        recommended_par: float = 40

    class ParOptimizer:
        def recommend_all(self, items, orders):
            return [Rec()]

    alerts = PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), par_optimizer=ParOptimizer()).evaluate(
        orders=[{"item": "salmon", "current_price": 7.2, "average_price": 6.0, "category": "protein", "current_par": 10}],
        suppliers=[],
        conservation_status={"state": "GREEN"},
    )
    assert alerts[0]["severity"] == "critical"


def test_alert_fields():
    alert = _engine().evaluate(orders=[{"item": "salmon", "current_price": 7.2, "average_price": 6.0}], suppliers=[], conservation_status={"state": "GREEN"})[0]
    assert {"alert_type", "severity", "title", "recommendation", "scenario"}.issubset(alert)


def test_recommendation_kitchen():
    @dataclass
    class Rec:
        item_name: str = "salmon"
        current_par: float = 10
        recommended_par: float = 40

    class ParOptimizer:
        def recommend_all(self, items, orders):
            return [Rec()]

    text = PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), par_optimizer=ParOptimizer()).evaluate(
        orders=[{"item": "salmon", "category": "protein", "current_par": 10}],
        suppliers=[],
        conservation_status={"state": "GREEN"},
    )[0]["recommendation"].lower()
    assert "centroid" not in text
    assert "sigma" not in text
    assert "order" in text


def test_router_filtered():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/alerts?severity=critical")
    assert response.status_code == 200
    assert all(alert["severity"] == "critical" for alert in response.json()["alerts"])


def test_router_filter_warning():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/alerts?severity=warning")
    assert response.status_code == 200
    assert all(alert["severity"] == "warning" for alert in response.json()["alerts"])


def test_router_filter_info():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/alerts?severity=info")
    assert response.status_code == 200
    assert all(alert["severity"] == "info" for alert in response.json()["alerts"])


def test_router_filter_all():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/purchasing/alerts")
    assert response.status_code == 200
    severities = {alert["severity"] for alert in response.json()["alerts"]}
    assert "critical" in severities
    assert "warning" in severities


def test_multiple_same_type():
    orders = [
        {"item": "salmon", "current_price": 7.2, "average_price": 6.0},
        {"item": "beef", "current_price": 12.0, "average_price": 9.0},
        {"item": "tuna", "current_price": 10.0, "average_price": 8.0},
    ]
    alerts = _engine().evaluate(orders=orders, suppliers=[], conservation_status={"state": "GREEN"})
    assert sum(1 for alert in alerts if alert["alert_type"] == "price_spike") == 3


def test_deduplication():
    orders = [
        {"item": "salmon", "current_price": 7.2, "average_price": 6.0},
        {"item": "salmon", "current_price": 7.2, "average_price": 6.0},
    ]
    alerts = _engine().evaluate(orders=orders, suppliers=[], conservation_status={"state": "GREEN"})
    assert sum(1 for alert in alerts if alert["alert_type"] == "price_spike") == 1


def test_consumes_existing_services():
    @dataclass
    class Profile:
        item: str = "salmon"
        average_waste_pct: float = 0.30
        benchmark_pct: float = 0.10

    class Tracker:
        called = False

        def __init__(self, orders):
            pass

        def analyze_all(self):
            Tracker.called = True
            return [Profile()]

    engine = PurchasingAlertEngine(waste_tracker_cls=Tracker, menu_engineer=NoMenuAlerts())
    engine.evaluate(orders=[{"item": "salmon"}], suppliers=[], conservation_status={"state": "GREEN"})
    assert Tracker.called is True


def test_no_conservation_skips_alert():
    alerts = _engine().evaluate(orders=[], suppliers=[], conservation_status=None)
    assert not any(alert["alert_type"] == "conservation_amber" for alert in alerts)


def test_amber_conservation_alerts():
    alerts = _engine().evaluate(orders=[], suppliers=[], conservation_status="AMBER")
    assert any(alert["alert_type"] == "conservation_amber" for alert in alerts)


def test_stockout_uses_par_optimizer():
    @dataclass
    class Rec:
        item_name: str = "salmon"
        current_par: float = 10
        recommended_par: float = 40

    class ParOptimizer:
        called = False

        def recommend_all(self, items, orders):
            ParOptimizer.called = True
            return [Rec()]

    PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), par_optimizer=ParOptimizer()).evaluate(
        orders=[{"item": "salmon", "category": "protein", "current_par": 10}],
        suppliers=[],
        conservation_status={"state": "GREEN"},
    )
    assert ParOptimizer.called is True


def test_supplier_uses_scorecard():
    @dataclass
    class Card:
        supplier_name: str = "Sysco"
        reliability_pct: float = 74.0
        trend: str = "declining"

    class Scorecard:
        called = False

        def build_all(self, min_orders=1):
            Scorecard.called = True
            return [Card()]

    alerts = PurchasingAlertEngine(menu_engineer=NoMenuAlerts(), scorecard_service=Scorecard()).evaluate(
        orders=[],
        suppliers=[{"name": "Sysco"}],
        conservation_status={"state": "GREEN"},
    )
    assert Scorecard.called is True
    assert any(alert["alert_type"] == "supplier_degradation" for alert in alerts)
