from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fastapi.testclient import TestClient

from app import context_router


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
    "price_memory_index": 0.50,
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


def test_api_health_returns_phase_alpha_and_engine(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] in {"A", "B"}
    assert isinstance(payload["alpha"], (int, float))
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


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


def test_auto_seed_empty_db(tmp_path):
    from app.main import create_app

    db_path = tmp_path / "purchasing_seeded.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    expected_verified, expected_correct = _fixture_outcome_counts(DATA_DIR / "purchasing_seed_v2.json")
    assert _count_decisions(db_path, "purchasing") == 20
    assert _count_verified(db_path, "purchasing") == expected_verified
    assert _count_correct(db_path, "purchasing") == expected_correct


def test_auto_seed_skips_populated(tmp_path):
    from app.main import create_app
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "purchasing_populated.db"
    store = SQLiteGraphStore(db_path, domain="purchasing")
    try:
        _save_proxy_decision(store, "existing")
    finally:
        store.close()

    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert _count_decisions(db_path, "purchasing") == 1


def test_ci_data_dir_creates_db(tmp_path, monkeypatch):
    from app.main import create_app

    data_dir = tmp_path / "ci-data"
    monkeypatch.setenv("CI_DATA_DIR", str(data_dir))
    with TestClient(create_app(demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    db_path = data_dir / "purchasing.db"
    assert db_path.exists()
    assert _count_decisions(db_path, "purchasing") == 20
    assert _count_verified(db_path, "purchasing") == _fixture_outcome_counts(DATA_DIR / "purchasing_seed_v2.json")[0]


def test_explicit_db_path_wins(tmp_path, monkeypatch):
    from app.main import create_app

    ci_dir = tmp_path / "ci-data"
    explicit_db = tmp_path / "explicit.db"
    monkeypatch.setenv("CI_DATA_DIR", str(ci_dir))

    with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert explicit_db.exists()
    assert not (ci_dir / "purchasing.db").exists()
    assert _count_decisions(explicit_db, "purchasing") == 20


def test_no_env_uses_explicit_fallback(tmp_path, monkeypatch):
    from app.main import create_app

    monkeypatch.delenv("CI_DATA_DIR", raising=False)
    db_path = tmp_path / "fallback.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert db_path.exists()
    assert _count_decisions(db_path, "purchasing") == 20


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


def test_context_similarity_factor_order_includes_price_memory_index():
    assert context_router._FACTOR_NAMES == (
        "expected_demand",
        "day_of_week",
        "weather_forecast",
        "event_flag",
        "historical_waste",
        "supplier_lead_time",
        "price_memory_index",
    )
    assert len(context_router._FACTOR_NAMES) == 7


def test_context_similarity_order_vector_defaults_price_memory_index():
    vector = context_router._order_vector(
        {
            "expected_demand": 0.7,
            "day_of_week_factor": 0.71,
            "weather_forecast": 0.2,
            "event_flag": 0.7,
            "historical_waste": 0.04,
            "supplier_lead_time": 0.45,
        }
    )

    assert vector == [0.7, 0.71, 0.2, 0.7, 0.04, 0.45, 0.5]


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
            "price_memory_index": 0.5,
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

    explicit_response = client.get(
        "/api/context/similar",
        params={
            "category": "protein",
            "expected_demand": 0.7,
            "day_of_week": 0.71,
            "weather_forecast": 0.2,
            "event_flag": 0.7,
            "historical_waste": 0.04,
            "supplier_lead_time": 0.45,
            "price_memory_index": 0.5,
            "n": 10,
        },
    )
    assert explicit_response.status_code == 200
    assert "TEMP-SIMILAR-001" in {
        row["order_id"] for row in explicit_response.json()["similar"]
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


def test_item_profile_fresh_store_has_no_ae_rules(tmp_path: Path, temp_data_dir: Path):
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "fresh_purchasing.db", demo_bundle_path=False))
    response = client.get("/api/context/item/chicken_breast/profile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ae_rules"] == []
    assert payload["ae_managed"] is False


def test_score_via_sdk_router(client):
    payload = _score(client)

    assert payload["category"] == "protein"
    assert payload["action"] in {"order_as_planned", "order_more", "order_less", "skip"}
    assert payload["decision_id"].startswith("PUR-")
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
    # Conservation V is verified-only; pending score writes are audit/store
    # activity but do not increase total_decisions.
    assert after_score["total_decisions"] == 0
    assert after_score["verified_count"] == 0
    assert after_score["correct_count"] == 0

    _learn(client, score["decision_id"], score["action"])
    payload = client.get("/api/conservation/status").json()
    assert payload["domain"] == "purchasing"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1
    assert payload["correct_count"] == 1
    assert payload["penalty_ratio"] == 3.0


def test_in_memory_scoring_and_conservation_share_proxy_store(temp_data_dir):
    from app.main import create_app

    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client:
        score = _score(memory_client)
        _learn(memory_client, score["decision_id"], score["action"])
        payload = memory_client.get("/api/conservation/status").json()

    assert score["decision_id"].startswith("PUR-")
    assert payload["domain"] == "purchasing"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1


def test_self_computation_centroid_history_available(client):
    response = client.get("/api/self/centroid-history")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"checkpoints", "total"}
    assert isinstance(payload["checkpoints"], list)


def test_self_computation_accuracy_available(client):
    response = client.get("/api/self/accuracy-by-category")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"categories", "threshold", "overall_verified"}
    assert isinstance(payload["categories"], list)


def test_self_computation_decisions_available(client):
    response = client.get("/api/self/decisions")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"decisions", "total"}
    assert isinstance(payload["decisions"], list)


def test_self_computation_audit_trail_available(client):
    response = client.get("/api/self/audit-trail")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"trails", "total"}
    assert isinstance(payload["trails"], list)


def test_self_computation_mounted_at_api_self(client):
    response = client.get("/api/self/decisions?limit=1")

    assert response.status_code == 200
    assert "decisions" in response.json()


def test_graph_store_count_verified(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path, domain="purchasing")
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.write_outcome(
            decision_id="d-1",
            actual_action="order_as_planned",
            is_correct=True,
            metadata={"actual_index": 0},
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_verified("purchasing") == 1


def test_graph_store_count_correct(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path, domain="purchasing")
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.write_outcome(
            decision_id="d-1",
            actual_action="order_as_planned",
            is_correct=True,
            metadata={"actual_index": 0},
        )
        store.write_outcome(
            decision_id="d-2",
            actual_action="order_more",
            is_correct=False,
            metadata={"actual_index": 1},
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_correct("purchasing") == 1


def test_evolution_variants(client):
    response = client.get("/api/evolution/variants")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "purchasing"
    assert payload["active_rules"] == []
    assert payload["promoted_rules"] == []
    assert len(payload["variants"]) == 7
    event_variants = [variant for variant in payload["variants"] if "event_type" in variant]
    configured_variants = [variant for variant in payload["variants"] if "family" in variant]
    assert {variant["event_type"] for variant in event_variants} == {
        "promotion_approved",
        "promotion_rejected",
    }
    assert {variant["id"] for variant in payload["variants"]} >= {
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
        "V-PUR-FRIDAY-001",
        "V-PUR-EVENT-001",
        "V-PUR-DAIRY-001",
    }
    assert {variant["family"] for variant in configured_variants} == {
        "waste_threshold",
        "lead_time_buffer",
    }
    assert all(variant.get("triggered_by") != "fixture" for variant in payload["variants"])


def test_evolution_variants_fresh_store_is_empty(tmp_path: Path, temp_data_dir: Path):
    from app.main import create_app

    client = TestClient(create_app(db_path=tmp_path / "fresh_variants_purchasing.db", demo_bundle_path=False))
    payload = client.get("/api/evolution/variants").json()

    assert payload["domain"] == "purchasing"
    assert [variant["id"] for variant in payload["variants"]] == [
        "WASTE_THRESHOLD_v1",
        "WASTE_THRESHOLD_v2",
        "LEAD_TIME_BUFFER_v1",
        "LEAD_TIME_BUFFER_v2",
    ]


def test_evolution_ledger_filters_promoted(client):
    from app.main import _filter_variants_by_query

    payload = client.get("/api/evolution/variants").json()
    variants = _filter_variants_by_query(payload["variants"], "MATCH promoted variants")

    assert variants
    assert {variant["event_type"] for variant in variants} == {"promotion_approved"}


def test_evolution_ledger_filters_rejected(client):
    from app.main import _filter_variants_by_query

    payload = client.get("/api/evolution/variants").json()
    variants = _filter_variants_by_query(payload["variants"], "MATCH rejected variants")

    assert variants
    assert {variant["event_type"] for variant in variants} == {"promotion_rejected"}


def test_fingerprint(client, temp_data_dir: Path):
    # Strict conservation requires enough verified/correct history before
    # additional learns mutate centroids. theta_min = 23.53 / override_count;
    # at q=1, >=24 correct overrides are required. Seed 30 for margin.
    _seed_verified_history(temp_data_dir.parent / "purchasing_test.db", total=50)

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
    store.write_decision(
        "purchasing",
        category="protein",
        action="order_as_planned",
        confidence=0.8,
        factors=PURCHASING_FACTORS,
        metadata={
            "decision_id": decision_id,
            "category_index": 0,
            "factor_vector": list(PURCHASING_FACTORS.values()),
            "recommended_index": 0,
            "probabilities": [0.8, 0.1, 0.05, 0.05],
        },
    )


def _seed_verified_history(db_path: Path, total: int) -> None:
    from copilot_sdk.graph import SQLiteGraphStore

    override_count = 30
    alternate_actions = [("order_more", 1), ("order_less", 2), ("skip", 3)]
    assert total >= override_count

    store = SQLiteGraphStore(db_path, domain="purchasing")
    try:
        for index in range(total):
            decision_id = f"seed-{index}"
            _save_proxy_decision(store, decision_id)
            if index < override_count:
                actual_action, actual_index = alternate_actions[
                    index % len(alternate_actions)
                ]
            else:
                actual_action, actual_index = "order_as_planned", 0
            store.write_outcome(
                decision_id=decision_id,
                actual_action=actual_action,
                is_correct=True,
                metadata={"actual_index": actual_index},
            )
    finally:
        store.close()


def _count_decisions(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_decisions(domain)
    finally:
        store.close()


def _count_verified(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_verified(domain)
    finally:
        store.close()


def _count_correct(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_correct(domain)
    finally:
        store.close()


def _fixture_outcome_counts(path: Path) -> tuple[int, int]:
    seed = json.loads(path.read_text(encoding="utf-8"))
    verified = sum(1 for entry in seed if "is_correct" in entry)
    correct = sum(1 for entry in seed if bool(entry.get("is_correct")))
    return verified, correct
