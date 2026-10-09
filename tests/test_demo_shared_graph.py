"""Shared demo composition using real graph writes, scorers and conservation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from copilot_sdk.config import GraphConfigError
from copilot_sdk.demo.preseed import (
    CROSS_COPILOT_DOMAIN, CROSS_COPILOT_SIGNAL_KEY, DEMO_DOMAINS,
    DemoPreseed, build_demo_scorers, create_demo_graph, seed_cross_copilot_signal,
)
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from scripts.preseed_all_copilots import main, parse_args, preseed_offline


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("COPILOT_PROFILE", "test")
    monkeypatch.setenv("GRAPH_PROFILE", "test")
    monkeypatch.setenv("COPILOT_PRESEED_MODE", "true")
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(tmp_path / "outbox.db"))
    for domain in DEMO_DOMAINS:
        monkeypatch.setenv(f"{domain.upper()}_PROFILE", "test")


def test_create_demo_graph_has_demo_domain() -> None:
    graph = create_demo_graph()
    assert isinstance(graph, InMemoryGraphStore)
    assert graph.domain == "demo"


def test_create_demo_graph_is_not_singleton() -> None:
    first, second = create_demo_graph(), create_demo_graph()
    first.save_governance("demo", "one", {"value": 1})
    assert first is not second
    assert second.get_governance("demo", "one") is None


def test_signal_governance_roundtrip() -> None:
    graph = create_demo_graph()
    signal_id = seed_cross_copilot_signal(graph)
    assert signal_id == CROSS_COPILOT_SIGNAL_KEY
    state = graph.get_governance(CROSS_COPILOT_DOMAIN, signal_id)
    assert state is not None
    assert state["event_type"] == "supplier_reliability_signal"
    assert state["payload"]["source_copilot"] == "purchasing"
    assert state["payload"]["target_copilot"] == "s2p"
    assert state["synthetic"] is True and state["evidence_tier"] == "T-sim"
    assert graph.get_governance("purchasing", signal_id) is None


def test_signal_seed_is_idempotent_and_detached() -> None:
    graph = create_demo_graph()
    first = seed_cross_copilot_signal(graph)
    before = graph.get_governance(CROSS_COPILOT_DOMAIN, first)
    assert seed_cross_copilot_signal(graph) == first
    assert graph.get_governance(CROSS_COPILOT_DOMAIN, first) == before
    assert len(graph.list_governance(CROSS_COPILOT_DOMAIN)) == 1
    assert before is not None
    before["payload"]["supplier_name"] = "changed"
    assert graph.get_governance(CROSS_COPILOT_DOMAIN, first)["payload"]["supplier_name"] == "Northstar Foods"


def test_signal_missing_readback_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = create_demo_graph()
    with monkeypatch.context() as fault:
        fault.setattr(graph, "get_governance", lambda domain, key: None)  # MOCK-OK: user-requested missing-readback fault; real write retained.
        with pytest.raises(RuntimeError, match="readback failed"):
            seed_cross_copilot_signal(graph)
    assert graph.get_governance(CROSS_COPILOT_DOMAIN, CROSS_COPILOT_SIGNAL_KEY) is not None


def test_default_builder_uses_one_shared_offline_graph() -> None:
    scorers = build_demo_scorers()
    assert set(scorers) == set(DEMO_DOMAINS)
    graph = scorers["trading"].graph_store
    assert isinstance(graph, InMemoryGraphStore) and graph.domain == "demo"
    assert all(scorer.graph_store is graph for scorer in scorers.values())
    assert all(scorer._profile == "offline" for scorer in scorers.values())
    assert {scorer._domain for scorer in scorers.values()} == set(DEMO_DOMAINS)


def test_external_graph_is_used_verbatim_by_all_scorers() -> None:
    graph = InMemoryGraphStore(domain="composition")
    graph.save_governance("other", "keep", {"value": 1})
    scorers = build_demo_scorers(graph_store=graph)
    assert all(scorer.graph_store is graph for scorer in scorers.values())
    assert graph.domain == "composition"
    assert graph.get_governance("other", "keep") == {"value": 1}


def test_cross_copilot_visibility_preserves_domain_counts() -> None:
    graph = create_demo_graph()
    scorers = build_demo_scorers(graph, profile="test")
    identities: list[str] = []
    for domain, scorer in scorers.items():
        result = scorer.score({}, scorer._preset.shape.category_names[0])
        identities.append(result.decision_id)
        scorer._learn_preseed(result.decision_id, result.action, "confirmed", context={"preseed": True})
        # Another scorer sees this row through the SAME graph and explicit source domain.
        reader = scorers["purchasing" if domain == "trading" else "trading"]
        row = reader.graph_store.get_decision(result.decision_id, domain, include_outcome=True)
        assert row is not None and row["domain"] == domain
        assert row["actual_action"] == result.action
    assert len(set(identities)) == len(DEMO_DOMAINS)
    assert graph.count_decisions("demo") == 0
    for domain, scorer in scorers.items():
        assert graph.count_decisions(domain) == graph.count_verified(domain) == 1
        assert scorer.get_verified_count() == 1
        state = scorer.get_conservation_state()
        assert state["verified_count"] == 1


def test_checkpoint_reload_uses_explicit_storage_domain() -> None:
    graph = create_demo_graph()
    initial = build_demo_scorers(graph, profile="test")["trading"]
    expected = np.asarray(initial._scorer.centroids) + 0.01
    graph.save_centroids("trading", "checkpoint", expected)
    graph.save_centroids("demo", "unrelated", [[99.0]])
    rebuilt = build_demo_scorers(graph, profile="test")["trading"]
    np.testing.assert_array_equal(rebuilt._scorer.centroids, expected)
    assert rebuilt._domain == "trading"


def test_legacy_scorer_default_domain_is_unchanged() -> None:
    graph = InMemoryGraphStore(domain="legacy")
    scorer = CompoundingScorer.from_preset("trading", graph_store=graph, enable_rl=False, profile="test")
    result = scorer.score({}, scorer._preset.shape.category_names[0])
    assert graph.get_decision(result.decision_id, "legacy") is not None
    assert graph.count_decisions("trading") == 0


@pytest.mark.parametrize("domain", ["", " "])
def test_empty_storage_domain_rejected(domain: str) -> None:
    with pytest.raises(ValueError, match="storage_domain"):
        CompoundingScorer.from_preset("trading", graph_store=create_demo_graph(), storage_domain=domain, profile="test")


def test_explicit_storage_domain_controls_reload_and_writes() -> None:
    graph = create_demo_graph()
    scorer = CompoundingScorer.from_preset("trading", graph_store=graph, storage_domain="experiment", profile="test", enable_rl=False)
    expected = np.asarray(scorer._scorer.centroids) + 0.02
    graph.save_centroids("experiment", "checkpoint", expected)
    rebuilt = CompoundingScorer.from_preset("trading", graph_store=graph, storage_domain="experiment", profile="test", enable_rl=False)
    np.testing.assert_array_equal(rebuilt._scorer.centroids, expected)
    result = rebuilt.score({}, rebuilt._preset.shape.category_names[0])
    assert graph.get_decision(result.decision_id, "experiment") is not None


def test_preseed_writes_only_into_provided_shared_graph() -> None:
    graph = create_demo_graph()
    foreign = graph.write_decision("unrelated", "keep", "accept", 0.9, {})
    runner = DemoPreseed(fast_mode=True, graph_store=graph, profile="test")
    result = runner.preseed_all()
    assert all(scorer.graph_store is graph for scorer in runner._scorers.values())
    assert runner.preseed_all() is result
    assert graph.get_decision(foreign, "unrelated") is not None
    for domain in ("trading", "purchasing"):
        assert graph.count_verified(domain) == result.copilots[domain].decisions == 20
        assert result.copilots[domain].conservation == runner._scorers[domain].get_conservation_state()["status"]
    assert graph.count_decisions("demo") == 0
    assert result.cross_copilot_signal == graph.get_governance(CROSS_COPILOT_DOMAIN, CROSS_COPILOT_SIGNAL_KEY)


def test_offline_script_injection_uses_provided_graph() -> None:
    graph = create_demo_graph()
    result = preseed_offline(graph, fast_mode=True, profile="test")
    assert graph.count_verified("trading") == result.copilots["trading"].decisions == 20
    assert graph.count_verified("purchasing") == 20
    assert graph.get_governance(CROSS_COPILOT_DOMAIN, CROSS_COPILOT_SIGNAL_KEY) == result.cross_copilot_signal


def test_offline_cli_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--offline", "--dry-run"]) == 0
    assert "no writes" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--trading-only", "--purchasing-only", "--dataops-only", "--s2p-only", "--force", "--heroes", "--demo-fixtures"])
def test_offline_cli_rejects_http_only_options(flag: str) -> None:
    with pytest.raises(SystemExit, match="2"):
        parse_args(["--offline", flag])


def test_production_builder_does_not_accept_memory() -> None:
    graph = create_demo_graph()
    with pytest.raises(RuntimeError):
        build_demo_scorers(graph, profile="production")
    assert all(graph.count_decisions(domain) == 0 for domain in DEMO_DOMAINS)


def test_production_domain_override_fails_before_store_access() -> None:
    with pytest.raises(GraphConfigError, match="storage_domain"):
        CompoundingScorer.from_preset("trading", graph_store=create_demo_graph(), storage_domain="other", profile="production")
