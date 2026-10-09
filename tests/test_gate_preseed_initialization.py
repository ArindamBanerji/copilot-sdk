"""Explicit server initialization and normal gating share real persisted state."""
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.composite_gate import CompositeGate
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def degraded_store(store: Any) -> Any:
    preset = TradingPreset()
    for index, correct in enumerate([True] * 80 + [False] * 20):
        # Governed writes preserve chronology on both memory and AGE.
        # AGE's basic writer currently omits the native created_at property.
        identity = store.generate_decision_id("trading")
        store.write_governed_decision(
            decision_id=identity,
            domain="trading",
            category=preset.shape.category_names[index % 5], category_index=index % 5,
            recommended_action=preset.shape.action_names[0], recommended_index=0,
            confidence=0.85, probabilities=[0.85] + [0.0] * (preset.shape.n_actions - 1),
            factor_vector=[0.8] * preset.shape.n_factors,
            factor_names=list(preset.shape.factor_names),
            metadata={"planted": True, "provenance": "sample", "created_at": float(index + 1)},
        )
        store.write_outcome(identity, preset.shape.action_names[0 if correct else 1], correct, domain="trading")
    # Assert the seeded degradation timeline independently of read presentation.
    chronology = sorted(store.get_verified_decisions("trading"), key=lambda row: row["created_at"])
    assert [row["is_correct"] for row in chronology] == [True] * 80 + [False] * 20
    return store


def real_scorer(store: Any, path: Path, via_proxy: bool) -> Any:
    if via_proxy:
        proxy = FreshScorerProxy("trading", path, lambda _: store, profile="test")
        proxy._scorer()  # Capture server configuration before any later environment change.
        return proxy
    return CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)


@pytest.mark.parametrize("via_proxy", [False, True])
def test_explicit_preseed_commits_then_restart_enforces_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, via_proxy: bool, disposable_age,
) -> None:
    path = tmp_path / "initialization"
    store = degraded_store(disposable_age.store("trading"))
    try:
        monkeypatch.setenv("COPILOT_PRESEED_MODE", "true")
        scorer = real_scorer(store, path, via_proxy)
        wrapper = GateEnforcedScorer(scorer, CompositeGate())
        decision = scorer.score({}, "trend_following")
        before = store.count_verified("trading")
        wrapper.learn(decision.decision_id, decision.action, context={"planted": True, "provenance": "sample"})
        assert store.count_verified("trading") == before + 1
        status = wrapper.gate_status()
        assert status is not None
        assert status["g_rate"]["active"] is True  # Do not manufacture a GREEN result.
        assert status["enforcement_mode"] == "preseed"
        assert not wrapper._outcome_buffer
    finally:
        store.close()

    monkeypatch.delenv("COPILOT_PRESEED_MODE")
    reopened = disposable_age.store("trading")
    try:
        normal = real_scorer(reopened, path, via_proxy)
        wrapper = GateEnforcedScorer(normal, CompositeGate())
        decision = normal.score({}, "trend_following")
        result = wrapper.learn(decision.decision_id, decision.action)
        assert result["blocked_by_gate"] is True
        assert result["gate_status"]["g_rate"]["active"] is True
        assert reopened.count_verified("trading") == before + 1
    finally:
        reopened.close()


@pytest.mark.parametrize("late_environment", [False, True])
@pytest.mark.parametrize("via_proxy", [False, True])
def test_client_context_cannot_enable_initialization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                   late_environment: bool, via_proxy: bool) -> None:
    monkeypatch.delenv("COPILOT_PRESEED_MODE", raising=False)
    store = degraded_store(create_graph_store(backend="memory", domain="trading", profile="test", env={}))
    try:
        scorer = real_scorer(store, tmp_path / "normal", via_proxy)
        if late_environment:
            monkeypatch.setenv("COPILOT_PRESEED_MODE", "true")
        wrapper = GateEnforcedScorer(scorer, CompositeGate())
        decision = scorer.score({}, "trend_following")
        before = store.count_verified("trading")
        result = wrapper.learn(decision.decision_id, decision.action,
                               context={"preseed": True, "planted": True})
        assert result["blocked_by_gate"] is True
        assert "enforcement_mode" not in result["gate_status"]
        assert store.count_verified("trading") == before
    finally:
        store.close()
