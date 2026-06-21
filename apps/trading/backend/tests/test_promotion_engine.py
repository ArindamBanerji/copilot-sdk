from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.promotion_router import create_promotion_engine_router
from app.services.promotion_engine import PromotionEngine
from app.services.promotion_state import PromotionStage, PromotionStateStore
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


CATEGORY = "trend_following"


def test_paper_ready() -> None:
    engine, _store, _states = _engine(correct=28, incorrect=22)

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is True
    assert result["next_stage"] == "small_live"


def test_paper_not_ready_decisions() -> None:
    engine, _store, _states = _engine(correct=20, incorrect=10)

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is False
    assert any("20 more decisions" in blocker for blocker in result["blockers"])


def test_paper_not_ready_accuracy() -> None:
    engine, _store, _states = _engine(correct=25, incorrect=25)

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is False
    assert any("accuracy" in blocker for blocker in result["blockers"])


def test_small_live_needs_conservation() -> None:
    engine, _store, states = _engine(correct=60, incorrect=40, conservation={"status": "AMBER"})
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is False
    assert "Conservation AMBER." in result["blockers"]


def test_small_live_ready() -> None:
    engine, _store, states = _engine(correct=60, incorrect=40, conservation={"status": "GREEN"})
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is True
    assert result["next_stage"] == "full_live"


def test_full_live_already() -> None:
    engine, _store, states = _engine(correct=120, incorrect=80, conservation={"status": "GREEN"})
    states.get(CATEGORY).current_stage = PromotionStage.FULL_LIVE

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is False
    assert result["next_stage"] is None
    assert result["recommendation"] == "Fully promoted."


def test_promote_records_history() -> None:
    engine, _store, states = _engine(correct=30, incorrect=20)

    result = engine.promote(CATEGORY, confirmed_by="trader")

    history = states.get(CATEGORY).promotion_history
    assert result["promoted"] is True
    assert history[0]["action"] == "promote"
    assert history[0]["confirmed_by"] == "trader"


def test_promote_changes_stage() -> None:
    engine, _store, states = _engine(correct=30, incorrect=20)

    engine.promote(CATEGORY)

    assert states.get(CATEGORY).current_stage == PromotionStage.SMALL_LIVE


def test_promote_rejects_not_ready() -> None:
    engine, _store, _states = _engine(correct=10, incorrect=10)

    with pytest.raises(ValueError):
        engine.promote(CATEGORY)


def test_promote_resets_counters() -> None:
    engine, _store, states = _engine(correct=30, incorrect=20)

    engine.promote(CATEGORY)
    state = states.get(CATEGORY)

    assert state.decisions_in_stage == 0
    assert state.accuracy_in_stage == 0.0


def test_promote_persists_state(tmp_path) -> None:
    store, _scorer = _seed_store(correct=30, incorrect=20)
    persist_path = tmp_path / "promotion_state.json"
    states = PromotionStateStore(persist_path)
    engine = PromotionEngine(
        store,
        TradingPreset(),
        {"status": "GREEN"},
        state_store=states,
    )

    engine.promote(CATEGORY)

    restored = PromotionStateStore(persist_path).get(CATEGORY)
    assert restored.current_stage == PromotionStage.SMALL_LIVE
    assert restored.stage_start_count == 50
    assert restored.promotion_history[0]["action"] == "promote"


def test_demote_conservation_red() -> None:
    engine, _store, states = _engine(correct=80, incorrect=20, conservation={"status": "RED"})
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    engine.evaluate(CATEGORY)

    assert states.get(CATEGORY).current_stage == PromotionStage.PAPER


def test_demote_records_reason() -> None:
    engine, _store, states = _engine(correct=80, incorrect=20)
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    result = engine.demote(CATEGORY, "conservation RED")

    assert result["reason"] == "conservation RED"
    assert states.get(CATEGORY).promotion_history[-1]["reason"] == "conservation RED"


def test_demote_from_paper() -> None:
    engine, _store, states = _engine()

    result = engine.demote(CATEGORY, "manual")

    assert result["demoted"] is False
    assert result["reason"] == "already at lowest stage"
    assert states.get(CATEGORY).current_stage == PromotionStage.PAPER
    assert states.get(CATEGORY).promotion_history == []


def test_state_store_persists_to_disk(tmp_path) -> None:
    persist_path = tmp_path / "promotion_state.json"
    states = PromotionStateStore(persist_path)
    state = states.get(CATEGORY)
    state.current_stage = PromotionStage.SMALL_LIVE
    state.decisions_in_stage = 12
    state.accuracy_in_stage = 0.75
    state.promoted_at = "2026-06-21T00:00:00+00:00"
    state.promotion_history.append({"action": "promote", "category": CATEGORY})
    state.stage_start_count = 50
    states.save()

    restored = PromotionStateStore(persist_path).get(CATEGORY)
    assert restored.current_stage == PromotionStage.SMALL_LIVE
    assert restored.decisions_in_stage == 12
    assert restored.accuracy_in_stage == 0.75
    assert restored.promoted_at == "2026-06-21T00:00:00+00:00"
    assert restored.promotion_history == [{"action": "promote", "category": CATEGORY}]
    assert restored.stage_start_count == 50


def test_demote_accuracy_drop() -> None:
    engine, _store, states = _engine(correct=8, incorrect=12, conservation={"status": "GREEN"})
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    engine.evaluate(CATEGORY)

    assert states.get(CATEGORY).current_stage == PromotionStage.PAPER
    assert states.get(CATEGORY).promotion_history[-1]["reason"] == "accuracy below sustained floor"


def test_recommendation_ready() -> None:
    engine, _store, _states = _engine(correct=39, incorrect=23, conservation={"status": "GREEN"})

    result = engine.evaluate(CATEGORY)

    assert "Ready to promote" in result["recommendation"]
    assert "62 trades" in result["recommendation"]
    assert "GREEN" in result["recommendation"]


def test_recommendation_blocked() -> None:
    engine, _store, _states = _engine(correct=12, incorrect=0, conservation={"status": "AMBER"})

    result = engine.evaluate(CATEGORY)

    assert "Need 38 more decisions." in result["recommendation"]


def test_recommendation_full() -> None:
    engine, _store, states = _engine()
    states.get(CATEGORY).current_stage = PromotionStage.FULL_LIVE

    assert engine.evaluate(CATEGORY)["recommendation"] == "Fully promoted."


def test_recommendation_kitchen_language() -> None:
    engine, _store, _states = _engine(correct=30, incorrect=20, conservation={"status": "GREEN"})

    recommendation = engine.evaluate(CATEGORY)["recommendation"]

    assert "PAPER" not in recommendation
    assert "SMALL_LIVE" not in recommendation
    assert "FULL_LIVE" not in recommendation
    assert "small position" in recommendation


def test_dashboard_all_categories() -> None:
    engine, _store, _states = _engine()

    rows = engine.dashboard()

    assert {row["category"] for row in rows} == set(TradingPreset().shape.category_names)


def test_dashboard_sizing_cap() -> None:
    engine, _store, states = _engine()
    states.get(CATEGORY).current_stage = PromotionStage.SMALL_LIVE

    row = next(item for item in engine.dashboard() if item["category"] == CATEGORY)

    assert row["max_sizing_pct"] == 2.0


def test_dashboard_endpoint() -> None:
    client = _client()

    response = client.get("/api/trading/promotion/dashboard")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_category_endpoint() -> None:
    client = _client()

    response = client.get(f"/api/trading/promotion/{CATEGORY}")

    assert response.status_code == 200
    assert response.json()["category"] == CATEGORY


def test_promote_endpoint() -> None:
    client = _client(correct=30, incorrect=20)

    response = client.post(f"/api/trading/promotion/{CATEGORY}/promote", json={"confirmed_by": "trader"})

    assert response.status_code == 200
    assert response.json()["promoted"] is True


def test_demote_endpoint() -> None:
    client = _client(correct=30, incorrect=20, stage=PromotionStage.SMALL_LIVE)

    response = client.post(f"/api/trading/promotion/{CATEGORY}/demote", json={"reason": "conservation RED"})

    assert response.status_code == 200
    assert response.json()["current_stage"] == "paper"


def test_new_category_starts_paper() -> None:
    engine, _store, states = _engine()

    state = engine.get_state("custom_category")

    assert state.current_stage == PromotionStage.PAPER
    assert states.get("custom_category").current_stage == PromotionStage.PAPER


def test_conservation_gate_paper_exempt() -> None:
    engine, _store, _states = _engine(correct=30, incorrect=20, conservation={"status": "RED"})

    result = engine.evaluate(CATEGORY)

    assert result["ready"] is True


def _client(
    *,
    correct: int = 0,
    incorrect: int = 0,
    stage: PromotionStage = PromotionStage.PAPER,
) -> TestClient:
    store, _scorer = _seed_store(correct=correct, incorrect=incorrect)
    states = PromotionStateStore()
    states.get(CATEGORY).current_stage = stage
    app = FastAPI()
    app.include_router(
        create_promotion_engine_router(
            lambda: store,
            conservation_status_factory=lambda: {"status": "GREEN"},
            state_store=states,
        )
    )
    return TestClient(app)


def _engine(
    *,
    correct: int = 0,
    incorrect: int = 0,
    conservation: dict | None = None,
) -> tuple[PromotionEngine, InMemoryGraphStore, PromotionStateStore]:
    store, _scorer = _seed_store(correct=correct, incorrect=incorrect)
    states = PromotionStateStore()
    engine = PromotionEngine(
        store,
        TradingPreset(),
        conservation or {"status": "GREEN"},
        state_store=states,
    )
    return engine, store, states


def _seed_store(
    *,
    correct: int,
    incorrect: int,
    category: str = CATEGORY,
) -> tuple[InMemoryGraphStore, CompoundingScorer]:
    store = InMemoryGraphStore("trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store)
    for index in range(correct + incorrect):
        _seed_verified(scorer, category, is_correct=index < correct)
    return store, scorer


def _seed_verified(
    scorer: CompoundingScorer,
    category: str,
    *,
    is_correct: bool,
) -> None:
    preset = TradingPreset()
    factors = {
        name: 0.4 + ((index % 5) / 20)
        for index, name in enumerate(preset.shape.factor_names)
    }
    result = scorer.score(factors, category)
    actual_action = result.action if is_correct else _different_action(result.action)
    scorer.learn(result.decision_id, actual_action)
    store = getattr(scorer, "_graph_store")
    if not any(
        decision.get("decision_id") == result.decision_id
        for decision in store.get_verified_decisions("trading")
    ):
        store.write_outcome(
            result.decision_id,
            actual_action,
            is_correct=is_correct,
        )


def _different_action(action: str) -> str:
    for candidate in TradingPreset().shape.action_names:
        if candidate != action:
            return candidate
    return action
