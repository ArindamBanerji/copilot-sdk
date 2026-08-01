from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.report_router import create_report_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.reporting.weekly import WeeklyReportGenerator, purchasing_cost_extractor
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


DOMAIN = "purchasing"
DAY = 86400.0
FACTOR_NAMES = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)


@pytest.fixture()
def store() -> InMemoryGraphStore:
    return InMemoryGraphStore(domain=DOMAIN)


@pytest.fixture()
def scorer(tmp_path, store: InMemoryGraphStore) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        DOMAIN,
        db_path=str(tmp_path / "weekly.db"),
        profile="test",
        graph_store=store,
        enable_rl=False,
    )


def _factors(price_memory_index: float = 0.5, historical_waste: float = 0.2) -> dict[str, float]:
    return {
        "expected_demand": 0.7,
        "day_of_week": 0.5,
        "weather_forecast": 0.5,
        "event_flag": 0.0,
        "historical_waste": historical_waste,
        "supplier_lead_time": 0.4,
        "price_memory_index": price_memory_index,
    }


def _write_decision(
    store: InMemoryGraphStore,
    *,
    decision_id: str,
    category: str = "protein",
    action: str = "order_less",
    created_at: float = 1_000_000_000.0,
    is_correct: bool | None = True,
    actual_action: str | None = None,
    context: dict[str, Any] | None = None,
    price_memory_index: float = 0.5,
) -> str:
    factors = _factors(price_memory_index=price_memory_index)
    factor_vector = [factors[name] for name in FACTOR_NAMES]
    action_index = {
        "order_as_planned": 0,
        "order_more": 1,
        "order_less": 2,
        "skip": 3,
    }[action]
    stored_id = store.write_decision(
        DOMAIN,
        category,
        action,
        0.65,
        factors,
        metadata={
            "decision_id": decision_id,
            "domain": DOMAIN,
            "category_index": 0,
            "factor_vector": factor_vector,
            "recommended_index": action_index,
            "probabilities": [0.1, 0.15, 0.65, 0.1],
            "created_at": created_at,
        },
    )
    if is_correct is not None:
        store.write_outcome(
            stored_id,
            actual_action=actual_action or action,
            is_correct=is_correct,
            metadata={
                "actual_index": action_index,
                "verified_at": created_at + 1.0,
                "context": dict(context or {}),
            },
            domain=DOMAIN,
        )
    return stored_id


def _generator(
    store: InMemoryGraphStore,
    scorer: CompoundingScorer,
    *,
    cost_extractor=purchasing_cost_extractor,
    waste_provider=None,
) -> WeeklyReportGenerator:
    return WeeklyReportGenerator(
        graph_store=store,
        scorer=scorer,
        domain=DOMAIN,
        cost_extractor=cost_extractor,
        preset=PurchasingPreset(),
        waste_provider=waste_provider,
    )


def _client(generator: WeeklyReportGenerator) -> TestClient:
    app = FastAPI()
    app.include_router(create_report_router(DOMAIN, report_factory=lambda: generator, prefix="/api/purchasing"))
    return TestClient(app)


def test_empty_week(store: InMemoryGraphStore, scorer: CompoundingScorer):
    report = _generator(store, scorer).generate()

    assert report.total_decisions == 0
    assert report.total_verified == 0
    assert report.overall_accuracy == 0.0
    assert report.conservation_status
    assert report.cost_impact.dollars_found == 0.0


def test_single_verified_decision(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", is_correct=True)

    report = _generator(store, scorer).generate()

    assert report.total_decisions == 1
    assert report.total_verified == 1
    assert report.overall_accuracy == 1.0


def test_multiple_categories(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", category="protein", is_correct=True)
    _write_decision(store, decision_id="d-002", category="produce", is_correct=False)
    _write_decision(store, decision_id="d-003", category="dairy", is_correct=True)

    report = _generator(store, scorer).generate()

    by_category = {category.category: category for category in report.categories}
    assert by_category["protein"].accuracy == 1.0
    assert by_category["produce"].accuracy == 0.0
    assert by_category["dairy"].accuracy == 1.0


def test_accuracy_computation(store: InMemoryGraphStore, scorer: CompoundingScorer):
    for index in range(7):
        _write_decision(store, decision_id=f"good-{index}", is_correct=True)
    for index in range(3):
        _write_decision(store, decision_id=f"bad-{index}", is_correct=False)

    report = _generator(store, scorer).generate()

    assert report.overall_accuracy == 0.7


def test_unverified_excluded_from_accuracy(store: InMemoryGraphStore, scorer: CompoundingScorer):
    for index in range(4):
        _write_decision(store, decision_id=f"good-{index}", is_correct=True)
    _write_decision(store, decision_id="bad-0", is_correct=False)
    for index in range(3):
        _write_decision(store, decision_id=f"pending-{index}", is_correct=None)

    report = _generator(store, scorer).generate()

    assert report.total_decisions == 8
    assert report.total_verified == 5
    assert report.overall_accuracy == 0.8


def test_top_action_per_category(store: InMemoryGraphStore, scorer: CompoundingScorer):
    for index in range(3):
        _write_decision(store, decision_id=f"planned-{index}", action="order_as_planned")
    for index in range(2):
        _write_decision(store, decision_id=f"less-{index}", action="order_less")

    report = _generator(store, scorer).generate()

    assert report.categories[0].top_action == "order_as_planned"


def test_graph_clock_not_wall_clock(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="old-clock", created_at=1_000_000_000.0)
    _write_decision(store, decision_id="max-clock", created_at=1_000_000_100.0)

    report = _generator(store, scorer).generate()

    assert report.period_end == 1_000_000_100.0


def test_period_windowing_7_days(store: InMemoryGraphStore, scorer: CompoundingScorer):
    base = 1_000_000_000.0
    _write_decision(store, decision_id="day-3", created_at=base)
    _write_decision(store, decision_id="day-8", created_at=base - (8 * DAY))
    _write_decision(store, decision_id="day-15", created_at=base - (15 * DAY))

    report = _generator(store, scorer).generate(period_days=7)

    assert report.total_decisions == 1


def test_period_windowing_30_days(store: InMemoryGraphStore, scorer: CompoundingScorer):
    base = 1_000_000_000.0
    _write_decision(store, decision_id="day-3", created_at=base)
    _write_decision(store, decision_id="day-8", created_at=base - (8 * DAY))
    _write_decision(store, decision_id="day-15", created_at=base - (15 * DAY))
    _write_decision(store, decision_id="day-31", created_at=base - (31 * DAY))

    report = _generator(store, scorer).generate(period_days=30)

    assert report.total_decisions == 3


def test_cost_extractor_waste_prevented(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", action="order_less", is_correct=True)

    report = _generator(store, scorer).generate()

    assert report.cost_impact.waste_prevented > 0.0


def test_cost_extractor_historical_waste_proxy():
    decision = {
        "recommended_action": "order_as_planned",
        "is_correct": True,
        "factors": {"historical_waste": 0.8},
        "factor_vector": [],
        "context": {},
        "outcome_metadata": {},
    }

    result = purchasing_cost_extractor(decision, decision, PurchasingPreset())

    assert result["waste_prevented"] == 20.0


def test_cost_extractor_price_variance_uses_preset_index():
    decision = {
        "recommended_action": "order_as_planned",
        "is_correct": True,
        "factors": {"expected_demand": 0.5},
        "factor_vector": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.2],
        "context": {},
        "outcome_metadata": {},
    }

    result = purchasing_cost_extractor(decision, decision, PurchasingPreset())

    assert result["price_variance_flagged"] == 15.0


def test_report_includes_price_memory_index_flags(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(
        store,
        decision_id="d-price-memory",
        action="order_as_planned",
        price_memory_index=0.2,
        is_correct=True,
    )

    report = _generator(store, scorer).generate()

    assert report.cost_impact.price_variance_flagged == 15.0
    assert report.cost_impact.dollars_found == 15.0


def test_report_includes_price_delta_flags(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(
        store,
        decision_id="d-price-delta",
        action="order_as_planned",
        is_correct=True,
        context={
            "supplier_id": "SUP-1",
            "supplier_name": "Pacific Seafood",
            "previous_unit_price": 10.0,
            "current_unit_price": 12.0,
        },
    )

    report = _generator(store, scorer).generate()

    assert report.cost_impact.price_variance_flagged == 2.0
    assert report.cost_impact.dollars_found == 2.0


def test_waste_tracker_prevented_value_feeds_weekly_report(store: InMemoryGraphStore, scorer: CompoundingScorer):
    calls = {"count": 0}

    def waste_provider() -> dict[str, float]:
        calls["count"] += 1
        return {"prevented_this_week": 20.0}

    _write_decision(
        store,
        decision_id="d-waste",
        action="order_as_planned",
        is_correct=True,
    )

    report = _generator(store, scorer, waste_provider=waste_provider).generate()

    assert calls["count"] == 1
    assert report.cost_impact.waste_prevented == 20.0
    assert report.cost_impact.net_found_period == report.cost_impact.net_recovered_period


def test_cost_extractor_missing_context(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", action="skip", is_correct=True, context=None)

    report = _generator(store, scorer).generate()

    assert report.cost_impact.waste_prevented == 50.0


def test_no_cost_extractor(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", action="skip", is_correct=True)

    report = _generator(store, scorer, cost_extractor=None).generate()

    assert report.cost_impact.dollars_found == 0.0
    assert report.cost_impact.waste_prevented == 0.0
    assert report.cost_impact.price_variance_flagged == 0.0


def test_conservation_status_included(store: InMemoryGraphStore, scorer: CompoundingScorer):
    store.update_conservation_state(
        DOMAIN,
        status="GREEN",
        alpha=0.8,
        q=0.75,
        V=10,
        theta_min=0.1,
        product=0.6,
        categories_total=5,
        categories_with_data=3,
        baseline_product=0.5,
        relative_threshold=0.8,
        complacency_flag="false",
    )
    _write_decision(store, decision_id="d-001", is_correct=True)

    report = _generator(store, scorer).generate()

    assert isinstance(report.conservation_status, str)
    assert report.conservation_q == 0.75
    assert report.conservation_alpha >= 0.0


def test_iks_delta(store: InMemoryGraphStore):
    class Point:
        def __init__(self, timestamp: float, iks: float) -> None:
            self.timestamp = timestamp
            self.iks = iks

    class Trajectory:
        current_iks = 30.0
        points = [
            Point(1_000_000.0, 10.0),
            Point(1_000_000.0 + (30 * DAY), 30.0),
        ]

    class Scorer:
        def get_phase(self) -> str:
            return "B"

        def get_alpha(self) -> float:
            return 0.5

        def trajectory(self):
            return Trajectory()

    _write_decision(store, decision_id="old", created_at=1_000_000.0, is_correct=True)
    _write_decision(store, decision_id="recent", created_at=1_000_000.0 + (30 * DAY), is_correct=True)

    report = _generator(store, Scorer()).generate(period_days=7)

    assert report.iks_current == 30.0
    assert report.iks_delta == 20.0


def test_period_days_zero_rejected(store: InMemoryGraphStore, scorer: CompoundingScorer):
    client = _client(_generator(store, scorer))

    response = client.get("/api/purchasing/report/weekly?period_days=0")

    assert response.status_code == 400


def test_report_response_uses_kitchen_net_found_language(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-found", action="order_less", is_correct=True)
    client = _client(_generator(store, scorer))

    payload = client.get("/api/purchasing/report/weekly").json()

    assert "net_found_period" in payload["cost_impact"]
    assert "net_recovered_period" not in payload["cost_impact"]


def test_supplier_changes_empty(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(store, decision_id="d-001", is_correct=True)

    report = _generator(store, scorer).generate()

    # requires supplier delta tracking
    assert report.supplier_changes == []


def test_supplier_changes_from_verified_price_delta(store: InMemoryGraphStore, scorer: CompoundingScorer):
    _write_decision(
        store,
        decision_id="d-supplier-delta",
        action="order_as_planned",
        is_correct=True,
        context={
            "supplier_id": "SUP-1",
            "supplier_name": "Pacific Seafood",
            "previous_unit_price": 10.0,
            "current_unit_price": 11.2,
        },
    )

    report = _generator(store, scorer).generate()

    assert len(report.supplier_changes) == 1
    change = report.supplier_changes[0]
    assert change.supplier == "Pacific Seafood"
    assert change.issue == "price_increase"
    assert change.pct == pytest.approx(12.0)


def test_non_purchasing_report_shape_preserved(tmp_path):
    store = InMemoryGraphStore(domain="dataops")

    class Scorer:
        def get_phase(self) -> str:
            return "B"

        def get_alpha(self) -> float:
            return 0.5

        def trajectory(self):
            class Trajectory:
                current_iks = 0.0
                points = []

            return Trajectory()

    generator = WeeklyReportGenerator(
        graph_store=store,
        scorer=Scorer(),
        domain="dataops",
        cost_extractor=None,
    )
    report = generator.generate()

    assert report.domain == "dataops"
    assert report.cost_impact.waste_prevented == 0.0
    assert report.cost_impact.price_variance_flagged == 0.0
    assert report.supplier_changes == []
