from __future__ import annotations

import json
from pathlib import Path
from copilot_sdk.demo.bundle import restore_bundle_if_empty

import pytest

from copilot_sdk.backend.health_builder import build_graph_health


@pytest.fixture
def seeded_bundle(tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({"domain": "trading", "min_decisions_to_skip": 1, "decisions": [
        {"decision_id": "BUNDLE-1", "category": "risk", "recommended_action": "hold", "confidence": 0.8,
         "factor_vector": [0.5], "factor_names": ["x"], "probabilities": [1.0]}
    ]}), encoding="utf-8")
    return path


class _Config:
    backend = "age"
    graph = "soc_graph"
    dsn = "postgresql://opaque"
    source_keys = (("dsn", "GRAPH_DSN"),)


def test_g056_preseed_requires_readiness() -> None:
    payload = build_graph_health(None, _Config(), "trading")
    assert payload["ready"] is False


@pytest.mark.age
def test_g056_seeded_decisions_visible_in_graph(disposable_age, seeded_bundle) -> None:
    assert restore_bundle_if_empty(disposable_age.store("trading"), seeded_bundle, domain="trading")
    assert disposable_age.store("trading").get_decision("BUNDLE-1", "trading") is not None


@pytest.mark.age
def test_g056_idempotent_rerun(disposable_age, seeded_bundle) -> None:
    store = disposable_age.store("trading")
    assert restore_bundle_if_empty(store, seeded_bundle, domain="trading")
    store.write_decision("trading", "risk", "buy", 0.9, {"x": 0.7}, metadata={"decision_id": "LIVE-1"})
    assert not restore_bundle_if_empty(store, seeded_bundle, domain="trading")
    assert disposable_age.store("trading").count_decisions("trading") == 2


def test_g057_legacy_preseed_rejected_in_production() -> None:
    source = Path("copilot_sdk/demo/preseed.py").read_text(encoding="utf-8")
    assert "InMemory demo preseed is restricted" in source


@pytest.mark.age
def test_g058_bundle_restore_marks_synthetic(disposable_age, seeded_bundle) -> None:
    store = disposable_age.store("trading")
    assert restore_bundle_if_empty(store, seeded_bundle, domain="trading")
    row = disposable_age.store("trading").get_decision("BUNDLE-1", "trading")
    assert row["metadata"]["provenance"] == "synthetic"
    assert store.count_verified("trading") == 0


def test_g059_jm_reference_has_age_mode() -> None:
    source = Path("examples/jm_reference/run.py").read_text(encoding="utf-8")
    assert 'choices=("age", "offline")' in source
    assert "GraphConfig.load" in source


def test_g059_trading_clone_has_age_mode() -> None:
    source = Path("examples/trading_clone/run.py").read_text(encoding="utf-8")
    assert 'choices=("age", "offline")' in source


def test_g061_age_required_tests_fail_without_age() -> None:
    source = Path("integration/age_jm/conftest.py").read_text(encoding="utf-8")
    assert "pytest.fail" in source and "AGE_REQUIRED" in source


def test_g062_validator_covers_all_roots() -> None:
    source = Path("scripts/validate_age_unification.py").read_text(encoding="utf-8")
    for root in ("copilot_sdk", "apps", "s2p-copilot/backend/app", "gen-ai-roi-demo-v4-v50/backend/app"):
        assert root in source


def test_g063_e2e_graph_project_exists() -> None:
    source = Path("e2e/playwright.config.ts").read_text(encoding="utf-8")
    assert 'name: "graph-integration"' in source


@pytest.mark.age
def test_g064_health_contract_schema(shared_age_readonly) -> None:
    payload = build_graph_health(*shared_age_readonly, "trading")
    assert {"ready", "graph_backend", "graph_connected", "graph_name", "graph_status"} <= payload.keys()
    assert {"connected", "storage_identity", "dsn_source", "checked_at", "components"} <= payload["graph_status"].keys()


@pytest.mark.age
def test_g064_health_components_are_explicit(shared_age_readonly) -> None:
    payload = build_graph_health(*shared_age_readonly, "soc")
    assert set(payload["graph_status"]["components"]) == {"decisions", "topology", "learning_restore"}
