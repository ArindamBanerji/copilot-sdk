"""Shared-graph namespace integration for the S2P differentiation engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from apps.s2p_differentiation import engine
from apps.s2p_differentiation.config import S2P_GENERATOR, S2P_ORACLE
from copilot_sdk.graph import GraphStoreNamespace, InMemoryGraphStore
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


class TrackingMemoryStore(InMemoryGraphStore):
    """In-memory store that exposes physical lifecycle calls to tests."""

    def __init__(self) -> None:
        super().__init__(domain="s2p")
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


def _write(store: ProtocolV2GraphStore, action: str) -> str:
    return cast(str, store.write_decision(
        "s2p",
        "price_variance",
        action,
        0.8,
        {"match_status": 0.5},
        {"created_at": 1.0},
    ))


def test_make_scorer_wraps_shared_store_with_namespace() -> None:
    shared = TrackingMemoryStore()
    scorer = engine._make_scorer(
        enable_rl=False,
        graph_store=shared,
        graph_namespace="s2p:run:ci",
    )
    try:
        assert isinstance(scorer.graph_store, GraphStoreNamespace)
        _write(scorer.graph_store, "auto_approve")
        assert shared.count_decisions(scorer.graph_store._domain("s2p")) == 1
    finally:
        scorer.close()
        shared.close()


def test_namespaced_scorer_uses_governed_write_and_logical_domain() -> None:
    shared = TrackingMemoryStore()
    scorer = engine._make_scorer(
        enable_rl=False,
        graph_store=shared,
        graph_namespace="s2p:run:ci",
    )
    try:
        category, factors = engine.SyntheticGenerator(S2P_GENERATOR).generate()
        score = scorer.score(factors, category)
        scorer.learn(score.decision_id, score.action, context={"benchmark": True})
        assert scorer.domain == "s2p"
        assert scorer.graph_store.count_decisions("s2p") == 1
        assert shared.count_decisions(scorer.graph_store._domain("s2p")) == 1
    finally:
        scorer.close()
        shared.close()


@pytest.mark.parametrize("missing", ["store", "namespace", "enable_rl"])
def test_make_scorer_requires_shared_store_namespace_and_rl_flag(missing: str) -> None:
    with pytest.raises(TypeError):
        if missing == "store":
            engine._make_scorer(  # type: ignore[call-arg]
                graph_namespace="s2p:run:ci",
                enable_rl=False,
            )
        elif missing == "namespace":
            engine._make_scorer(  # type: ignore[call-arg]
                TrackingMemoryStore(),
                enable_rl=False,
            )
        else:
            engine._make_scorer(  # type: ignore[call-arg]
                TrackingMemoryStore(),
                graph_namespace="s2p:run:ci",
            )


def test_ci_write_is_invisible_to_hand_namespace() -> None:
    shared = TrackingMemoryStore()
    ci = GraphStoreNamespace(shared, "s2p:run:ci")
    hand = GraphStoreNamespace(shared, "s2p:run:hand")
    _write(ci, "auto_approve")
    assert ci.count_decisions("s2p") == 1
    assert hand.count_decisions("s2p") == 0


def test_hand_write_is_invisible_to_ci_namespace() -> None:
    shared = TrackingMemoryStore()
    ci = GraphStoreNamespace(shared, "s2p:run:ci")
    hand = GraphStoreNamespace(shared, "s2p:run:hand")
    _write(hand, "hold_for_review")
    assert hand.count_decisions("s2p") == 1
    assert ci.count_decisions("s2p") == 0


def test_arms_share_logical_domain_without_collision() -> None:
    shared = TrackingMemoryStore()
    ci = GraphStoreNamespace(shared, "s2p:run:ci")
    hand = GraphStoreNamespace(shared, "s2p:run:hand")
    _write(ci, "auto_approve")
    _write(hand, "hold_for_review")
    assert ci.count_decisions("s2p") == 1
    assert hand.count_decisions("s2p") == 1
    assert shared.count_decisions(ci._domain("s2p")) == 1
    assert shared.count_decisions(hand._domain("s2p")) == 1


def test_run_three_arms_uses_one_store_and_three_namespaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shared = TrackingMemoryStore()
    factory_calls = 0
    calls: list[tuple[ProtocolV2GraphStore | None, str | None]] = []
    real_make_scorer = engine._make_scorer

    def fake_factory(*_: Any, **__: Any) -> TrackingMemoryStore:
        nonlocal factory_calls
        factory_calls += 1
        return shared

    def recording_make_scorer(
        graph_store: ProtocolV2GraphStore,
        *,
        enable_rl: bool,
        graph_namespace: str,
    ) -> Any:
        calls.append((graph_store, graph_namespace))
        return real_make_scorer(
            graph_store,
            graph_namespace=graph_namespace,
            enable_rl=enable_rl,
        )

    monkeypatch.setattr(engine, "InMemoryGraphStore", fake_factory)
    monkeypatch.setattr(engine, "_make_scorer", recording_make_scorer)
    result = engine.run_three_arms(
        S2P_GENERATOR,
        S2P_ORACLE,
        n_decisions=0,
        output_dir=tmp_path,
        profile="test",
    )

    run_id = result["metadata"]["run_id"]
    assert factory_calls == 1
    assert len(calls) == 3
    assert all(store is shared for store, _ in calls)
    assert {namespace for _, namespace in calls} == {
        f"s2p:{run_id}:ci",
        f"s2p:{run_id}:hand",
        f"s2p:{run_id}:tg1",
    }


def test_closing_namespace_scorer_does_not_close_shared_store() -> None:
    shared = TrackingMemoryStore()
    scorer = engine._make_scorer(
        enable_rl=False,
        graph_store=shared,
        graph_namespace="s2p:run:ci",
    )
    engine._close_scorer(scorer)
    assert shared.close_calls == 0
    _write(shared, "auto_approve")
    assert shared.count_decisions("s2p") == 1


def test_run_three_arms_closes_shared_store_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shared = TrackingMemoryStore()
    monkeypatch.setattr(engine, "InMemoryGraphStore", lambda **_: shared)
    engine.run_three_arms(
        S2P_GENERATOR,
        S2P_ORACLE,
        n_decisions=0,
        output_dir=tmp_path,
        profile="development",
    )
    assert shared.close_calls == 1


def test_production_profile_fails_closed_for_shared_memory_backend(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="profile='production' is unsupported"):
        engine.run_three_arms(
            S2P_GENERATOR,
            S2P_ORACLE,
            n_decisions=0,
            output_dir=tmp_path,
            profile="production",
        )


@pytest.mark.parametrize("profile", ["test", "development"])
def test_nonproduction_profiles_run_with_shared_memory_store(
    profile: str,
    tmp_path: Path,
) -> None:
    result = engine.run_three_arms(
        S2P_GENERATOR,
        S2P_ORACLE,
        n_decisions=0,
        output_dir=tmp_path / profile,
        profile=profile,
    )
    assert result["metadata"]["n_decisions"] == 0
    assert len(result["metadata"]["run_id"]) == 8
