from __future__ import annotations

import json
from pathlib import Path

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from copilot_sdk.backend.gap_closure import GAP_CLOSURE_RECORDS, closure_count, open_production_candidates
from copilot_sdk.backend.health_builder import build_graph_health
from copilot_sdk.migration.rehearsal import apply, dry_run, rollback_proof, verify


class Config:
    domain = "trading"
    graph_store = None
    backend = "age"
    graph = "soc_graph"
    dsn = "opaque"


def _target(store):
    config = Config()
    config.graph_store = store
    return config


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "source.json"
    path.write_text(json.dumps({"decisions": [{"decision_id": "D1", "domain": "trading", "category": "risk"}]}), encoding="utf-8")
    return path


@pytest.mark.age
def test_g065_dry_run_no_mutation(tmp_path: Path, disposable_age):
    store = disposable_age.store("trading"); target = _target(store)
    report = dry_run(_source(tmp_path), target)
    assert report["imported_count"] == 0 and store.get_all_decisions("trading") == []


@pytest.mark.age
def test_g065_apply_idempotent(tmp_path: Path, disposable_age):
    store = disposable_age.store("trading"); target = _target(store); source = _source(tmp_path)
    first = apply(source, target); second = apply(source, target)
    assert first["imported_count"] == 1 and second["imported_count"] == 0
    assert disposable_age.store("trading").count_decisions("trading") == 1


def test_g065_foreign_domain_rejected(tmp_path: Path):
    source = tmp_path / "foreign.json"
    source.write_text(json.dumps({"decisions": [{"decision_id": "D1", "domain": "s2p"}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        apply(source, _target(InMemoryGraphStore(domain="trading")))


@pytest.mark.age
def test_g065_verify_receipt_parity(tmp_path: Path, disposable_age):
    store = disposable_age.store("trading"); target = _target(store); source = _source(tmp_path)
    apply(source, target)
    assert verify(target, source)["parity_verified"] is True


def test_g065_rollback_requires_snapshot_capability():
    store = InMemoryGraphStore(domain="trading")
    store.write_decision("trading", "risk", "hold", 0.8, {"signal": 0.5}, metadata={"decision_id": "D0"})
    before = store.get_all_decisions("trading")
    with pytest.raises(RuntimeError, match="snapshot_state/restore_state"):
        rollback_proof(_target(store))
    assert store.get_all_decisions("trading") == before


@pytest.mark.age
def test_g066_cutover_ready_computed_not_hardcoded(shared_age_readonly):
    evidence = {"migration_parity_verified": True, "gap_closure_records": 66, "open_production_candidates": 0}
    ready = build_graph_health(*shared_age_readonly, "trading", evidence=evidence)["cutover_ready"]
    blocked = build_graph_health(*shared_age_readonly, "trading", evidence={})["cutover_ready"]
    assert ready is True and blocked is False


def test_g066_cutover_requires_all_components():
    evidence = {"migration_parity_verified": True, "gap_closure_records": 66, "open_production_candidates": 0}
    assert build_graph_health(None, Config(), "trading", evidence=evidence)["cutover_ready"] is False


@pytest.mark.age
def test_g066_product_claim_requires_live_verification(shared_age_readonly):
    evidence = {"migration_parity_verified": True, "gap_closure_records": 66, "open_production_candidates": 0}
    assert build_graph_health(*shared_age_readonly, "trading", evidence=evidence)["product_claim_allowed"] is False
    evidence.update({"live_verification_passed": True, "live_verification_authorized": True})
    assert build_graph_health(*shared_age_readonly, "trading", evidence=evidence)["product_claim_allowed"] is True


def test_g066_all_66_gaps_have_closure_records():
    assert closure_count() == 66
    assert set(GAP_CLOSURE_RECORDS) == {f"G{i:03d}" for i in range(1, 67)}


def test_g066_zero_open_candidates():
    assert open_production_candidates() == 0
