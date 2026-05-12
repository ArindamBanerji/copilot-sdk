from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
}

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
VALID_CATEGORIES = {"protein", "produce", "dairy", "dry_goods", "beverages"}
VALID_ACTIONS = {"order_as_planned", "order_more", "order_less", "skip"}
REQUIRED_SEED_FIELDS = {
    "order_id",
    "item",
    "display_name",
    "category",
    "quantity_lbs",
    "day_of_week",
    "date",
    "is_event_day",
    "event_type",
    "expected_demand",
    "day_of_week_factor",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "action_taken",
    "is_correct",
    "waste_pct",
    "waste_cost_dollars",
    "stockout_occurred",
    "stockout_cost_dollars",
    "total_cost_dollars",
}


def _score(client, category: str = "protein") -> dict:
    response = client.post(
        "/api/score",
        json={"category": category, "factors": PURCHASING_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client, decision_id: str, actual_action: str) -> dict:
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": actual_action},
    )
    assert response.status_code == 200
    return response.json()


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["domain"] == "purchasing"
    assert "copilot_sdk.scoring" in payload["engine"]
    assert "gae.profile_scorer" in payload["engine"]
    assert "gae.evolution" in payload["engine"]


def test_today_summary(client):
    response = client.get("/api/context/today-summary")

    assert response.status_code == 200
    payload = response.json()
    assert "date" in payload
    assert "day_of_week" in payload
    assert payload["weather"]["source"] == "cached"
    assert payload["events"] == []


def test_items_list(client):
    response = client.get("/api/context/items")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 20
    assert {item["category"] for item in items} == {
        "protein",
        "produce",
        "dairy",
        "dry_goods",
        "beverages",
    }


def test_items_enhanced_fields(client):
    response = client.get("/api/context/items")

    assert response.status_code == 200
    first_item = response.json()[0]
    for field in (
        "emoji",
        "on_hand_qty",
        "unit_price",
        "event_sensitivity",
        "display_name",
    ):
        assert field in first_item
    assert 0.0 <= first_item["event_sensitivity"] <= 1.0


def test_waste_history_known(client):
    response = client.get("/api/context/waste-history/mixed greens")

    assert response.status_code == 200
    payload = response.json()
    assert payload["item"] == "mixed_greens"
    assert payload["count"] == 5
    assert len(payload["waste_pct"]) == 5


def test_waste_history_unknown(client):
    response = client.get("/api/context/waste-history/dragonfruit")

    assert response.status_code == 200
    payload = response.json()
    assert payload["item"] == "dragonfruit"
    assert payload["waste_pct"] == []
    assert payload["count"] == 0


def test_weather(client):
    response = client.get("/api/context/weather")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "cached"
    assert 0.0 <= payload["weather_factor"] <= 1.0


def test_order_metadata_store_and_retrieve(client):
    payload = {
        "decision_id": "decision-1",
        "item": "chicken_breast",
        "quantity_lbs": 120,
        "day": "Monday",
        "events": ["weekday_service"],
    }

    created = client.post("/api/context/order-metadata", json=payload)
    assert created.status_code == 201
    assert created.json()["decision_id"] == "decision-1"

    response = client.get("/api/context/order-metadata")
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["decision-1"]["item"] == "chicken_breast"
    assert metadata["decision-1"]["quantity_lbs"] == 120


def test_order_metadata_v2_fields(client):
    payload = {
        "decision_id": "decision-v2",
        "item": "chicken_breast",
        "display_name": "Chicken Breast",
        "emoji": "🍗",
        "category": "protein",
        "quantity": 150,
        "unit": "lb",
        "day": "Monday",
        "events": ["banquet"],
        "cost": 577.5,
        "stockout_estimate": 0.12,
        "waste_estimate": 0.04,
        "risk_ratio": 0.31,
        "auto_computed_factors": {
            "expected_demand": 0.7,
            "event_flag": 0.7,
        },
    }

    created = client.post("/api/context/order-metadata", json=payload)
    assert created.status_code == 201
    assert created.json()["metadata"] == payload

    response = client.get("/api/context/order-metadata")
    assert response.status_code == 200
    assert response.json()["decision-v2"] == payload


def test_order_metadata_requires_decision_id(client):
    response = client.post("/api/context/order-metadata", json={"item": "chicken_breast"})

    assert response.status_code == 400
    assert "decision_id" in response.json()["detail"]


def test_seed_v2_exists():
    path = DATA_DIR / "purchasing_seed_v2.json"

    assert path.exists()
    seed = json.loads(path.read_text(encoding="utf-8"))
    assert len(seed) == 20
    assert {order["category"] for order in seed} == VALID_CATEGORIES
    for order in seed:
        assert REQUIRED_SEED_FIELDS <= set(order)
        assert order["category"] in VALID_CATEGORIES
        assert order["action_taken"] in VALID_ACTIONS
        for factor in (
            "expected_demand",
            "day_of_week_factor",
            "weather_forecast",
            "event_flag",
            "historical_waste",
            "supplier_lead_time",
        ):
            assert 0.0 <= order[factor] <= 1.0


def test_analytics(client):
    response = client.get("/api/context/analytics")

    assert response.status_code == 200
    payload = response.json()
    for section in (
        "contrast_card",
        "counterfactual",
        "category_accuracy",
        "day_of_week",
        "event_impact",
        "waste_cost_analysis",
        "ae_impact",
        "portfolio_summary",
    ):
        assert section in payload
    assert "aligned" in payload["contrast_card"]
    assert "misaligned" in payload["contrast_card"]
    assert payload["counterfactual"]["dollars_saved"] > 0


def test_analytics_consistent_with_seed_v2(temp_data_dir):
    seed = json.loads((temp_data_dir / "purchasing_seed_v2.json").read_text(encoding="utf-8"))
    analytics = json.loads((temp_data_dir / "analytics_cache.json").read_text(encoding="utf-8"))

    assert len(seed) == 20
    computed_accuracy = round(sum(1 for order in seed if order["is_correct"]) / len(seed), 4)
    assert analytics["portfolio_summary"]["total_orders"] == len(seed)
    assert analytics["portfolio_summary"]["accuracy"] == computed_accuracy
    category_counts = Counter(order["category"] for order in seed)
    for category, count in category_counts.items():
        assert analytics["category_accuracy"][category]["count"] == count
        correct = sum(1 for order in seed if order["category"] == category and order["is_correct"])
        assert analytics["category_accuracy"][category]["correct"] == correct
    assert round(sum(order["waste_cost_dollars"] for order in seed), 2) == analytics[
        "portfolio_summary"
    ]["total_waste_cost"]
    assert round(sum(order["stockout_cost_dollars"] for order in seed), 2) == analytics[
        "portfolio_summary"
    ]["total_stockout_cost"]


def test_similar_orders(client):
    response = client.get(
        "/api/context/similar",
        params={
            "category": "protein",
            "expected_demand": 0.7,
            "day_of_week": 0.71,
            "weather_forecast": 0.2,
            "event_flag": 0.7,
            "historical_waste": 0.04,
            "supplier_lead_time": 0.45,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 3
    assert payload["similar"]
    similarities = [row["similarity"] for row in payload["similar"]]
    assert similarities == sorted(similarities, reverse=True)
    for row in payload["similar"]:
        assert row["similarity"] > 0.85
        assert {
            "order_id",
            "item",
            "category",
            "day_of_week",
            "is_event_day",
            "quantity_lbs",
            "waste_pct",
            "stockout_occurred",
            "is_correct",
            "similarity",
        } <= set(row)


def test_v2_endpoints_use_temp_data(client, temp_data_dir):
    analytics_path = temp_data_dir / "analytics_cache.json"
    analytics = json.loads(analytics_path.read_text(encoding="utf-8"))
    analytics["test_marker"] = "temp-analytics"
    analytics_path.write_text(json.dumps(analytics, indent=2), encoding="utf-8")

    analytics_response = client.get("/api/context/analytics")
    assert analytics_response.status_code == 200
    assert analytics_response.json()["test_marker"] == "temp-analytics"

    seed_path = temp_data_dir / "purchasing_seed_v2.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    seed.append(
        {
            "order_id": "TEMP-SIMILAR-001",
            "item": "chicken_breast",
            "display_name": "Chicken Breast",
            "category": "protein",
            "quantity_lbs": 151,
            "day_of_week": "Monday",
            "date": "2026-05-30",
            "is_event_day": True,
            "event_type": "temp_fixture",
            "expected_demand": 0.7,
            "day_of_week_factor": 0.71,
            "weather_forecast": 0.2,
            "event_flag": 0.7,
            "historical_waste": 0.04,
            "supplier_lead_time": 0.45,
            "action_taken": "order_more",
            "is_correct": True,
            "waste_pct": 0.03,
            "waste_cost_dollars": 17.44,
            "stockout_occurred": False,
            "stockout_cost_dollars": 0.0,
            "total_cost_dollars": 17.44,
        }
    )
    seed_path.write_text(json.dumps(seed, indent=2), encoding="utf-8")

    similar_response = client.get(
        "/api/context/similar",
        params={
            "category": "protein",
            "expected_demand": 0.7,
            "day_of_week": 0.71,
            "weather_forecast": 0.2,
            "event_flag": 0.7,
            "historical_waste": 0.04,
            "supplier_lead_time": 0.45,
            "n": 10,
        },
    )
    assert similar_response.status_code == 200
    assert "TEMP-SIMILAR-001" in {
        row["order_id"] for row in similar_response.json()["similar"]
    }


def test_item_profile(client):
    response = client.get("/api/context/item/chicken_breast/profile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["item"]["name"] == "chicken_breast"
    assert len(payload["waste_history"]) == 5
    assert payload["waste_avg"] is not None
    assert payload["waste_trend"] in {"up", "down", "flat", "unknown"}
    assert isinstance(payload["ae_rules"], list)
    assert isinstance(payload["ae_managed"], bool)


def test_item_profile_unknown(client):
    response = client.get("/api/context/item/unicorn_meat/profile")

    assert response.status_code == 200
    assert response.json() == {"error": "Item not found", "name": "unicorn_meat"}


def test_item_profile_ae_rule_matching(client):
    protein_response = client.get("/api/context/item/chicken_breast/profile")
    produce_response = client.get("/api/context/item/mixed_greens/profile")
    dairy_response = client.get("/api/context/item/whole_milk/profile")

    assert protein_response.status_code == 200
    assert produce_response.status_code == 200
    assert dairy_response.status_code == 200
    protein_rules = {rule["id"] for rule in protein_response.json()["ae_rules"]}
    produce_rules = {rule["id"] for rule in produce_response.json()["ae_rules"]}
    dairy_rules = {rule["id"] for rule in dairy_response.json()["ae_rules"]}
    assert "V-PUR-EVENT-001" in protein_rules
    assert "V-PUR-FRIDAY-001" in produce_rules
    assert "V-PUR-DAIRY-001" not in dairy_rules


def test_score_via_sdk_router(client):
    payload = _score(client)

    assert payload["category"] == "protein"
    assert payload["action"] in {"order_as_planned", "order_more", "order_less", "skip"}
    assert 0.0 <= payload["confidence"] <= 1.0
    assert len(payload["probabilities"]) == 4
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"


def test_learn_returns_reward(client):
    score = _score(client)
    learn = _learn(client, score["decision_id"], score["action"])

    assert learn["decision_id"] == score["decision_id"]
    assert isinstance(learn["reward"], (int, float))
    assert "previous_reward" in learn
    assert "reward_multiplier" in learn
    assert learn["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_conservation_status_returns_live_counts(client):
    before = client.get("/api/conservation/status").json()
    assert before["total_decisions"] == 0
    assert before["verified_count"] == 0
    assert before["correct_count"] == 0
    assert before["penalty_ratio"] == 3.0

    score = _score(client)
    after_score = client.get("/api/conservation/status").json()
    assert after_score["total_decisions"] == 1
    assert after_score["verified_count"] == 0
    assert after_score["correct_count"] == 0

    _learn(client, score["decision_id"], score["action"])
    payload = client.get("/api/conservation/status").json()
    assert payload["domain"] == "purchasing"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1
    assert payload["correct_count"] == 1
    assert payload["penalty_ratio"] == 3.0


def test_graph_store_count_verified(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.scoring.storage import DecisionStore

    db_path = tmp_path / "graph.sqlite"
    store = DecisionStore(db_path)
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.save_outcome(
            decision_id="d-1",
            actual_action="order_as_planned",
            actual_index=0,
            is_correct=True,
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_verified() == 1


def test_graph_store_count_correct(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.scoring.storage import DecisionStore

    db_path = tmp_path / "graph.sqlite"
    store = DecisionStore(db_path)
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.save_outcome(
            decision_id="d-1",
            actual_action="order_as_planned",
            actual_index=0,
            is_correct=True,
        )
        store.save_outcome(
            decision_id="d-2",
            actual_action="order_more",
            actual_index=1,
            is_correct=False,
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_correct() == 1


def test_evolution_variants(client):
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["engine"]["gae"] == "gae.evolution"
    assert len(payload["variants"]) == 3
    assert {variant["event_type"] for variant in payload["variants"]} == {
        "promotion_approved",
        "promotion_rejected",
    }


def test_evolution_ledger_filters_promoted(temp_data_dir: Path):
    from app.main import _FixtureEvolutionLedger

    ledger = _FixtureEvolutionLedger(temp_data_dir / "evolution_fixtures.json")
    variants = asyncio.run(ledger.run_query("MATCH promoted variants"))

    assert variants
    assert {variant["event_type"] for variant in variants} == {"promotion_approved"}


def test_evolution_ledger_filters_rejected(temp_data_dir: Path):
    from app.main import _FixtureEvolutionLedger

    ledger = _FixtureEvolutionLedger(temp_data_dir / "evolution_fixtures.json")
    variants = asyncio.run(ledger.run_query("MATCH rejected variants"))

    assert variants
    assert {variant["event_type"] for variant in variants} == {"promotion_rejected"}


def test_fingerprint(client, temp_data_dir: Path):
    # Strict conservation requires enough verified/correct history before
    # additional learns mutate centroids. Purchasing threshold is ~8 verified at q=1.
    _seed_verified_history(temp_data_dir.parent / "purchasing_test.db", total=9)

    for _ in range(3):
        score = _score(client)
        learn = _learn(client, score["decision_id"], score["action"])
        assert learn.get("status") != "paused"

    response = client.get("/api/fingerprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["decisions_analyzed"] >= 12
    assert {factor["name"] for factor in payload["factors"]} == set(PURCHASING_FACTORS)


def _save_proxy_decision(store, decision_id: str) -> None:
    store.save_decision(
        decision_id=decision_id,
        domain="purchasing",
        category="protein",
        category_index=0,
        factors=PURCHASING_FACTORS,
        factor_vector=list(PURCHASING_FACTORS.values()),
        recommended_action="order_as_planned",
        recommended_index=0,
        confidence=0.8,
        probabilities=[0.8, 0.1, 0.05, 0.05],
    )


def _seed_verified_history(db_path: Path, total: int) -> None:
    from copilot_sdk.scoring.storage import DecisionStore

    store = DecisionStore(db_path)
    try:
        for index in range(total):
            decision_id = f"seed-{index}"
            _save_proxy_decision(store, decision_id)
            store.save_outcome(
                decision_id=decision_id,
                actual_action="order_as_planned",
                actual_index=0,
                is_correct=True,
            )
    finally:
        store.close()
