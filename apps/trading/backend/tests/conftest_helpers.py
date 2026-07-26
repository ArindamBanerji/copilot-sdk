from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def _shape(scorer: CompoundingScorer):
    return scorer._preset.shape


def _default_factors(scorer: CompoundingScorer, value: float = 0.6) -> dict[str, float]:
    return {name: value for name in _shape(scorer).factor_names}


def _different_action(scorer: CompoundingScorer, action: str) -> str:
    for candidate in _shape(scorer).action_names:
        if candidate != action:
            return str(candidate)
    raise AssertionError("preset must expose at least two actions")


def seed_green_scorer(
    tmp_path: str | Path,
    domain: str = "trading",
    n_decisions: int = 50,
) -> CompoundingScorer:
    """Create a real scorer seeded to conservation GREEN."""
    db = os.path.join(str(tmp_path), f"{domain}_green.db")
    store = SQLiteGraphStore(db, domain=domain)
    scorer = CompoundingScorer.from_preset(domain, db_path=db, graph_store=store, profile="test")
    factors = _default_factors(scorer)
    category = str(_shape(scorer).category_names[0])

    for _ in range(n_decisions):
        result = scorer.score(category=category, factors=factors)
        learn_result = scorer.learn(
            decision_id=result.decision_id,
            actual_action=result.action,
        )
        if isinstance(learn_result, dict):
            raise AssertionError(f"expected GREEN seed learn to apply, got {learn_result}")

    return scorer


def seed_green_client(client: Any, n_decisions: int = 50) -> dict[str, Any]:
    """Seed a TestClient app through real score and learn endpoints."""
    preset = TradingPreset()
    factors = {name: 0.6 for name in preset.shape.factor_names}
    category = str(preset.shape.category_names[0])

    for _ in range(n_decisions):
        score_response = client.post(
            "/api/score",
            json={"category": category, "factors": factors},
        )
        assert score_response.status_code == 200, score_response.json()
        score_payload = score_response.json()
        learn_response = client.post(
            "/api/learn",
            json={
                "decision_id": score_payload["decision_id"],
                "actual_action": score_payload["action"],
            },
        )
        assert learn_response.status_code == 200, learn_response.json()
        assert learn_response.json().get("paused") is False

    status_response = client.get("/api/conservation/status")
    assert status_response.status_code == 200, status_response.json()
    status = status_response.json()
    assert status["status"] == "GREEN"
    return status


def seed_paused_scorer(
    tmp_path: str | Path,
    domain: str = "trading",
) -> tuple[str, str, str]:
    """Create real scorer state where the next learn call pauses."""
    db = os.path.join(str(tmp_path), f"{domain}_paused.db")
    store = SQLiteGraphStore(db, domain=domain)
    scorer = CompoundingScorer.from_preset(domain, db_path=db, graph_store=store, profile="test")
    factors = _default_factors(scorer)
    category = str(_shape(scorer).category_names[0])

    first = scorer.score(category=category, factors=factors)
    first_result = scorer.learn(
        decision_id=first.decision_id,
        actual_action=_different_action(scorer, first.action),
    )
    if isinstance(first_result, dict):
        raise AssertionError(f"first override should seed state, got {first_result}")

    pending = scorer.score(category=category, factors=factors)
    action = str(pending.action)
    scorer.graph_store.close()
    return db, str(pending.decision_id), action
