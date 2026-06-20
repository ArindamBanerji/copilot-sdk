from __future__ import annotations

from datetime import date, timedelta

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import context_router
from app.data_helpers import assert_no_sample_in_metric
from app.factors import ALL_FACTOR_NAMES, PURCHASING_FACTOR_COMPUTERS, compute_factors
from app.factors.day_of_week import compute as compute_day_of_week
from app.factors.event_flag import compute as compute_event_flag
from app.factors.expected_demand import compute as compute_expected_demand
from app.factors.historical_waste import compute as compute_historical_waste
from app.factors.price_memory_index import compute as compute_price_memory_index
from app.factors.supplier_lead_time import compute as compute_supplier_lead_time
from app.factors.weather_forecast import compute as compute_weather_forecast
from app.graph_status import PurchasingActiveAGEGraphStore
from app.routers import evidence as evidence_router
from app.routers import queue as queue_router
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


def rich_context() -> dict:
    return {
        "forecast_demand": 80,
        "par_level": 100,
        "day_of_week": 5,
        "weather_score": 0.8,
        "event_covers": 30,
        "normal_covers": 100,
        "waste_pct": 0.08,
        "lead_time_days": 2,
        "price_change_count": 1,
        "months_tracked": 6,
    }


def assert_bounded(value: float) -> None:
    assert 0.0 <= value <= 1.0


def test_expected_demand_nominal():
    value = compute_expected_demand({"forecast_demand": 80, "par_level": 100})
    assert value == pytest.approx(0.8)
    assert_bounded(value)


def test_expected_demand_missing_context():
    assert compute_expected_demand({}) == 0.5


def test_expected_demand_boundary():
    assert compute_expected_demand({"forecast_demand": 0, "par_level": 100}) == 0.0
    assert compute_expected_demand({"forecast_demand": 150, "par_level": 100}) == 1.0


def test_day_of_week_nominal():
    value = compute_day_of_week({"day_of_week": 4})
    assert value == pytest.approx(0.7)
    assert_bounded(value)


def test_day_of_week_missing_context():
    assert compute_day_of_week({}) == 0.5


def test_day_of_week_boundary():
    assert compute_day_of_week({"day_of_week": 0}) == pytest.approx(0.3)
    assert compute_day_of_week({"day_of_week": 5}) == 1.0


def test_weather_forecast_nominal():
    value = compute_weather_forecast({"weather": "sunny"})
    assert value == pytest.approx(0.9)
    assert_bounded(value)


def test_weather_forecast_missing_context():
    assert compute_weather_forecast({}) == 0.5


def test_weather_forecast_boundary():
    assert compute_weather_forecast({"weather_score": -0.2}) == 0.0
    assert compute_weather_forecast({"weather_score": 1.5}) == 1.0


def test_event_flag_nominal():
    value = compute_event_flag({"event_covers": 30, "normal_covers": 100})
    assert value == pytest.approx(0.3)
    assert_bounded(value)


def test_event_flag_missing_context():
    assert compute_event_flag({}) == 0.5


def test_event_flag_boundary():
    assert compute_event_flag({"event_flag": False}) == 0.0
    assert compute_event_flag({"event_flag": True}) == 1.0
    assert compute_event_flag({"event_covers": 200, "normal_covers": 100}) == 1.0


def test_historical_waste_nominal():
    value = compute_historical_waste({"waste_pct": 0.10})
    assert value == pytest.approx(0.5)
    assert_bounded(value)


def test_historical_waste_missing_context():
    assert compute_historical_waste({}) == 0.5


def test_historical_waste_boundary():
    assert compute_historical_waste({"waste_pct": 0.0}) == 0.0
    assert compute_historical_waste({"waste_pct": 0.25}) == 1.0


def test_supplier_lead_time_nominal():
    value = compute_supplier_lead_time({"lead_time_days": 3.5})
    assert value == pytest.approx(0.5)
    assert_bounded(value)


def test_supplier_lead_time_missing_context():
    assert compute_supplier_lead_time({}) == 0.5


def test_supplier_lead_time_boundary():
    assert compute_supplier_lead_time({"lead_time_days": 0}) == 1.0
    assert compute_supplier_lead_time({"lead_time_days": 9}) == 0.0


def test_price_memory_index_nominal():
    value = compute_price_memory_index({"price_change_count": 1, "months_tracked": 4})
    assert value == pytest.approx(0.75)
    assert_bounded(value)


def test_price_memory_index_missing_context():
    assert compute_price_memory_index({}) == 0.5


def test_price_memory_index_boundary():
    assert compute_price_memory_index({"price_change_count": 0, "months_tracked": 6}) == 1.0
    assert compute_price_memory_index({"price_change_count": 10, "months_tracked": 2}) == 0.0


def test_compute_factors_all_7():
    values = compute_factors(rich_context())
    assert set(values) == set(ALL_FACTOR_NAMES)
    assert len(values) == 7


def test_compute_factors_empty():
    values = compute_factors({})
    assert set(values) == set(ALL_FACTOR_NAMES)
    assert all(value == 0.5 for value in values.values())


def test_registry_matches_preset():
    assert ALL_FACTOR_NAMES == list(PurchasingPreset().shape.factor_names)


def test_all_factors_bounded():
    contexts = [
        rich_context(),
        {
            "forecast_demand": 10_000,
            "par_level": 1,
            "day_of_week": 99,
            "weather_score": 10,
            "event_covers": 10_000,
            "normal_covers": 1,
            "waste_pct": 10,
            "lead_time_days": -10,
            "price_change_count": -10,
            "months_tracked": 1,
        },
        {},
    ]
    for context in contexts:
        for name, computer in PURCHASING_FACTOR_COMPUTERS.items():
            value = computer(context)
            assert_bounded(value), name


class CapturingAGEStore:
    def __init__(self) -> None:
        self.decision: dict | None = None

    def write_governed_decision(self, **kwargs) -> None:
        self.decision = kwargs


class FixedQueueScore:
    def __init__(self, action: str = "order_more", confidence: float = 0.5) -> None:
        self.action = action
        self.confidence = confidence


class FixedQueueScorer:
    def __init__(self, action: str = "order_more", confidence: float = 0.5) -> None:
        self.action = action
        self.confidence = confidence

    def score_read_only(self, *, factors: dict, category: str) -> FixedQueueScore:
        return FixedQueueScore(action=self.action, confidence=self.confidence)


class CountingQueueScorer(FixedQueueScorer):
    def __init__(self, action: str = "order_more", confidence: float = 0.5) -> None:
        super().__init__(action=action, confidence=confidence)
        self.calls = 0

    def score_read_only(self, *, factors: dict, category: str) -> FixedQueueScore:
        self.calls += 1
        return super().score_read_only(factors=factors, category=category)


def queue_order(**overrides: object) -> dict:
    order = {
        "order_id": "Q-ORDER",
        "category": "produce",
        "supplier_id": "SUP-1",
        "supplier_name": "Fresh Supplier",
        "items": [{"name": "romaine", "quantity": 10, "unit": "lb"}],
        "total_value": 100.0,
        "par_compliance": 0.5,
        "factors": {
            "expected_demand": 0.8,
            "day_of_week": 0.7,
            "weather_forecast": 0.6,
            "event_flag": 0.2,
            "historical_waste": 0.75,
            "supplier_lead_time": 0.3,
            "price_memory_index": 0.9,
        },
    }
    order.update(overrides)
    return order


def queue_client(monkeypatch: pytest.MonkeyPatch, orders: list[dict], scorer: FixedQueueScorer | None = None) -> TestClient:
    monkeypatch.setattr(queue_router, "_orders", lambda connector=None: orders)
    app = FastAPI()
    app.include_router(queue_router.create_queue_router(scorer_factory=lambda: scorer or FixedQueueScorer()))
    return TestClient(app)


def _write_graph_status_decision(metadata: dict, factors: dict | None = None) -> dict[str, float]:
    store = CapturingAGEStore()
    adapter = PurchasingActiveAGEGraphStore(store)
    adapter.write_decision(
        "purchasing",
        "protein",
        "order_as_planned",
        0.8,
        factors or {},
        metadata={"decision_id": "PUR-WIRE-1", **metadata},
    )
    assert store.decision is not None
    return dict(zip(store.decision["factor_names"], store.decision["factor_vector"]))


def test_graph_status_uses_computed_factors():
    values = _write_graph_status_decision({"waste_pct": 0.15, "lead_time_days": 2})

    assert values["historical_waste"] == pytest.approx(0.75)
    assert values["supplier_lead_time"] == pytest.approx(1 - (2 / 7))


def test_graph_status_request_factors_override_computed():
    values = _write_graph_status_decision(
        {"waste_pct": 0.15},
        factors={"historical_waste": 0.9},
    )

    assert values["historical_waste"] == pytest.approx(0.9)


def test_graph_status_empty_order_defaults():
    values = _write_graph_status_decision({})

    assert set(values) == set(ALL_FACTOR_NAMES)
    assert all(value == 0.5 for value in values.values())


def test_graph_status_all_7_wired():
    values = _write_graph_status_decision(
        {
            "forecast_demand": 80,
            "par_level": 100,
            "day_of_week": "Saturday",
            "weather_score": 0.8,
            "event_covers": 30,
            "normal_covers": 100,
            "waste_pct": 0.08,
            "lead_time_days": 2,
            "price_change_count": 1,
            "months_tracked": 6,
        }
    )

    assert set(values) == set(ALL_FACTOR_NAMES)
    assert all(value != 0.5 for value in values.values())


def test_queue_uses_computed_factors():
    row = queue_router._recommendation(
        {
            "order_id": "Q-COMPUTED",
            "category": "produce",
            "supplier_id": "SUP-1",
            "supplier_name": "Fresh Supplier",
            "items": [{"name": "romaine", "quantity": 10, "unit": "lb"}],
            "forecast_demand": 80,
            "par_level": 100,
            "waste_pct": 0.15,
            "lead_time_days": 2,
        }
    )

    assert row is not None
    assert set(row["factors"]) == set(ALL_FACTOR_NAMES)
    assert row["factors"]["historical_waste"] == pytest.approx(0.75)
    assert row["factors"]["historical_waste"] != 0.5


def test_queue_priority_formula():
    row = queue_router._recommendation(
        queue_order(par_compliance=0.0, total_value=50.0),
        scorer=FixedQueueScorer(confidence=0.5),
        max_amount=100.0,
    )

    assert row is not None
    assert row["stockout_risk"] == pytest.approx(1.0)
    assert row["financial_impact"] == pytest.approx(0.5)
    assert row["priority_score"] == pytest.approx(0.7)


def test_queue_sorted_descending(monkeypatch):
    client = queue_client(
        monkeypatch,
        [
            queue_order(order_id="LOW", total_value=10, par_compliance=1.0),
            queue_order(order_id="HIGH", total_value=100, par_compliance=0.0),
        ],
        scorer=FixedQueueScorer(confidence=0.5),
    )

    payload = client.get("/api/purchasing/queue").json()

    assert [row["order_id"] for row in payload["queue"]] == ["HIGH", "LOW"]


def test_queue_has_confidence():
    row = queue_router._recommendation(queue_order(), scorer=FixedQueueScorer(confidence=0.42), max_amount=100)

    assert row is not None
    assert row["confidence"] == pytest.approx(0.42)


def test_queue_has_recommended_action():
    row = queue_router._recommendation(queue_order(), scorer=FixedQueueScorer(action="order_less"), max_amount=100)

    assert row is not None
    assert row["recommended_action"] == "order_less"


def test_queue_top_factors_max_3():
    row = queue_router._recommendation(queue_order(), scorer=FixedQueueScorer(), max_amount=100)

    assert row is not None
    assert 1 <= len(row["top_factors"]) <= 3
    assert all("interpretation" in factor for factor in row["top_factors"])


def test_queue_stockout_high_priority():
    row = queue_router._recommendation(
        queue_order(par_compliance=0.0, total_value=100.0),
        scorer=FixedQueueScorer(confidence=0.5),
        max_amount=100.0,
    )

    assert row is not None
    assert row["priority_score"] > 0.7


def test_queue_low_confidence_high_priority():
    row = queue_router._recommendation(
        queue_order(par_compliance=0.5, total_value=100.0),
        scorer=FixedQueueScorer(confidence=0.3),
        max_amount=100.0,
    )

    assert row is not None
    assert row["priority_score"] > 0.7


def test_queue_empty(monkeypatch):
    client = queue_client(monkeypatch, [])

    response = client.get("/api/purchasing/queue")

    assert response.status_code == 200
    assert response.json()["queue"] == []


def test_queue_limit(monkeypatch):
    client = queue_client(
        monkeypatch,
        [queue_order(order_id=f"Q-{index}", total_value=100 - index) for index in range(8)],
    )

    payload = client.get("/api/purchasing/queue?limit=5").json()

    assert payload["count"] == 5
    assert len(payload["queue"]) == 5


def test_queue_endpoint_200(monkeypatch):
    client = queue_client(monkeypatch, [queue_order()])

    response = client.get("/api/purchasing/queue")

    assert response.status_code == 200


def test_queue_uses_app_scorer(monkeypatch):
    scorer = CountingQueueScorer(confidence=0.17)
    client = queue_client(monkeypatch, [queue_order()], scorer=scorer)

    payload = client.get("/api/purchasing/queue").json()

    assert scorer.calls > 0
    assert payload["queue"][0]["confidence"] == pytest.approx(0.17)


def test_queue_no_sample_data():
    app = FastAPI()
    app.include_router(queue_router.create_queue_router(scorer_factory=lambda: FixedQueueScorer()))
    client = TestClient(app)

    payload = client.get("/api/purchasing/queue?limit=5").json()

    assert payload["queue"]
    assert all(item.get("provenance") != "sample" for item in payload["queue"])
    assert_no_sample_in_metric(payload["queue"], "order_queue")


def test_queue_from_qbo_has_provenance():
    app = FastAPI()
    app.include_router(queue_router.create_queue_router(scorer_factory=lambda: FixedQueueScorer()))
    client = TestClient(app)

    payload = client.get("/api/purchasing/queue?limit=5").json()

    assert payload["source"] == "quickbooks_online"
    assert payload["queue"]
    assert all(item.get("provenance") == "scraped_external" for item in payload["queue"])
    assert all(item.get("data_source") == "quickbooks_online" for item in payload["queue"])


def test_queue_detail_endpoint(monkeypatch):
    client = queue_client(monkeypatch, [queue_order(order_id="DETAIL-1")])

    response = client.get("/api/purchasing/queue/DETAIL-1")

    assert response.status_code == 200
    assert response.json()["order_id"] == "DETAIL-1"


def test_queue_detail_not_found(monkeypatch):
    client = queue_client(monkeypatch, [queue_order(order_id="DETAIL-1")])

    response = client.get("/api/purchasing/queue/NONEXISTENT")

    assert response.status_code == 404


def test_queue_aging_days(monkeypatch):
    old_date = (date.today() - timedelta(days=5)).isoformat()
    client = queue_client(monkeypatch, [queue_order(order_id="AGED-1", order_date=old_date)])

    payload = client.get("/api/purchasing/queue/AGED-1").json()

    assert payload["aging_days"] >= 5


def test_queue_limit_param(monkeypatch):
    client = queue_client(
        monkeypatch,
        [queue_order(order_id=f"LIMIT-{index}", total_value=100 - index) for index in range(8)],
    )

    payload = client.get("/api/purchasing/queue?limit=3").json()

    assert len(payload["queue"]) <= 3
    assert payload["count"] <= 3


def test_queue_priority_bounded(monkeypatch):
    client = queue_client(
        monkeypatch,
        [
            queue_order(order_id="LOW", total_value=0, par_compliance=1.0),
            queue_order(order_id="HIGH", total_value=100, par_compliance=0.0),
        ],
    )

    payload = client.get("/api/purchasing/queue").json()

    assert payload["queue"]
    for item in payload["queue"]:
        assert 0.0 <= item["priority_score"] <= 1.0


def test_evidence_recomputes_missing_factors():
    factors = evidence_router._decision_factors(
        {
            "decision_id": "D-EVIDENCE",
            "category": "produce",
            "action": "order_as_planned",
            "confidence": 0.8,
            "factors": {
                "expected_demand": 0.8,
                "day_of_week": 0.7,
                "weather_forecast": 0.8,
            },
            "metadata": {
                "waste_pct": 0.15,
                "lead_time_days": 2,
                "price_change_count": 1,
                "months_tracked": 6,
                "event_covers": 30,
                "normal_covers": 100,
            },
        }
    )

    assert set(factors) == set(ALL_FACTOR_NAMES)
    assert factors["historical_waste"] == pytest.approx(0.75)
    assert factors["supplier_lead_time"] == pytest.approx(1 - (2 / 7))


def test_context_router_uses_computed_factors():
    vector = context_router._order_vector(
        {
            "forecast_demand": 80,
            "par_level": 100,
            "day_of_week": "Saturday",
            "weather_score": 0.8,
            "event_covers": 30,
            "normal_covers": 100,
            "waste_pct": 0.15,
            "lead_time_days": 2,
            "price_change_count": 1,
            "months_tracked": 6,
        }
    )
    values = dict(zip(context_router._FACTOR_NAMES, vector))

    assert set(values) == set(ALL_FACTOR_NAMES)
    assert values["historical_waste"] == pytest.approx(0.75)
    assert values["supplier_lead_time"] == pytest.approx(1 - (2 / 7))
    assert all(value != 0.5 for value in values.values())
