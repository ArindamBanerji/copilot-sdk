from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import DOMAIN, REPO_ROOT, create_app
from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore


def _bundle_path() -> Path:
    return REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"


def test_create_app_can_disable_demo_bundle_restore(tmp_path: Path) -> None:
    with TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code == 200


def test_create_app_default_demo_bundle_restores_on_startup(tmp_path: Path) -> None:
    db_path = tmp_path / "startup_bundle.db"
    with TestClient(create_app(db_path=db_path)) as client:
        assert client.get("/health").status_code == 200

    store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="TRD-")
    try:
        assert store.count_decisions(DOMAIN) == 200
    finally:
        store.close()


def test_domain_demo_bundle_restores_into_tmp_sqlite_store(tmp_path: Path) -> None:
    store = SQLiteGraphStore(str(tmp_path / "bundle.db"), domain=DOMAIN, decision_id_prefix="TRD-")
    try:
        assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN) is True
        assert store.count_decisions(DOMAIN) == 200
        assert len(store.get_verified_decisions(DOMAIN)) >= 140
        assert len(store.get_centroid_checkpoints(DOMAIN, limit=10)) == 5
        assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN) is False
    finally:
        store.close()


def test_demo_bundle_restore_skips_in_memory_store() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    assert restore_bundle_if_empty(store, _bundle_path(), domain=DOMAIN) is False
