from __future__ import annotations

from pathlib import Path
import pytest

from fastapi.testclient import TestClient

from app.main import DOMAIN, REPO_ROOT, create_app
from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.graph import InMemoryGraphStore


def _bundle_path() -> Path:
    return Path(REPO_ROOT) / "demo" / f"{DOMAIN}_demo_bundle.json"


def test_create_app_can_disable_demo_bundle_restore(tmp_path: Path) -> None:
    with TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code in {200, 503}


def test_create_app_default_demo_bundle_restores_on_startup(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "startup_bundle")
    with TestClient(app) as client:
        assert client.get("/health").status_code in {200, 503}
        store = app.state.graph_store
        assert store.count_decisions(DOMAIN) == 200
        assert len(store.get_verified_decisions(DOMAIN)) == 150
        assert all(row["metadata"]["provenance"] == "synthetic"
                   for row in store.get_all_decisions(DOMAIN))


def test_domain_demo_bundle_restores_into_memory_store(tmp_path: Path) -> None:
    store = InMemoryGraphStore(domain=DOMAIN, decision_id_prefix="DOPS-")
    try:
        assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN).success is True
        assert store.count_decisions(DOMAIN) == 200
        assert len(store.get_verified_decisions(DOMAIN)) == 150
        assert len(store.get_centroid_checkpoints(DOMAIN, limit=10)) == 5
        assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN).success is False
    finally:
        store.close()


@pytest.mark.age
def test_bundle_restore_returns_true_for_age_backend(disposable_age) -> None:
    store = disposable_age.store(DOMAIN)
    assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN).success is True
    reopened = disposable_age.store(DOMAIN)
    assert reopened.count_decisions(DOMAIN) == 200
    rows = reopened.get_all_decisions(DOMAIN)
    assert all(row["metadata"]["provenance"] == "synthetic" for row in rows)
    assert len(reopened.get_verified_decisions(DOMAIN)) == 150


@pytest.mark.age
def test_bundle_restore_preserves_later_age_decisions(disposable_age) -> None:
    store = disposable_age.store(DOMAIN)
    assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN).success is True
    decision_id = store.write_decision(DOMAIN, "pipeline_failure", "investigate", 0.8, {"impact_scope": 0.5})
    reopened = disposable_age.store(DOMAIN)
    assert restore_bundle_if_empty(reopened, _bundle_path(), domain=DOMAIN).success is False
    assert reopened.count_decisions(DOMAIN) == 201
    assert reopened.get_decision(decision_id, domain=DOMAIN) is not None


def test_demo_bundle_restore_reports_unsupported_rl_state() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    report = restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN)
    assert report.success and not report.fully_restored
    assert report.stores_failed == 0
    assert report.section_counts["decisions"] == 200
    assert report.section_counts["outcomes"] == 150
    assert report.section_counts["centroid_checkpoints"] == 5
    assert report.section_counts["rl_state"] == 0
    assert report.skipped_stores == ["rl_state"]
    assert report.skipped_count == 1
    assert report.skipped_reasons == {"rl_state": "no protocol method for RL state (REV-P4a)"}
    assert store.count_decisions(DOMAIN) == 200
