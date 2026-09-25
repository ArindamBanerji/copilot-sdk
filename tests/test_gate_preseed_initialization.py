"""Explicit server initialization and normal gating share real persisted state."""
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.composite_gate import CompositeGate
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def degraded_store(path: Path) -> SQLiteGraphStore:
    store = SQLiteGraphStore(path, domain="trading")
    preset = TradingPreset()
    for index, correct in enumerate([True] * 80 + [False] * 20):
        identity = store.write_decision(
            "trading", preset.shape.category_names[index % 5], preset.shape.action_names[0],
            0.85, {name: 0.8 for name in preset.shape.factor_names},
            metadata={"planted": True, "provenance": "sample"},
        )
        store.write_outcome(identity, preset.shape.action_names[0 if correct else 1], correct, domain="trading")
    return store


def real_scorer(store: SQLiteGraphStore, path: Path, via_proxy: bool) -> Any:
    if via_proxy:
        proxy = FreshScorerProxy("trading", path, lambda _: store, profile="test")
        proxy._scorer()  # Capture server configuration before any later environment change.
        return proxy
    return CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)


@pytest.mark.parametrize("via_proxy", [False, True])
def test_explicit_preseed_commits_then_restart_enforces_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, via_proxy: bool,
) -> None:
    path = tmp_path / "initialization.db"
    store = degraded_store(path)
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
    reopened = SQLiteGraphStore(path, domain="trading")
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
    store = degraded_store(tmp_path / "normal.db")
    try:
        scorer = real_scorer(store, tmp_path / "normal.db", via_proxy)
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
