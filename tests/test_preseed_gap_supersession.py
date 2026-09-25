"""Real-store coverage for inactive intervals and non-destructive import revisions."""
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from copilot_sdk.backend.historical_checkpoint import HISTORY_IMPORT_KEY, project_historical_checkpoints
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from scripts.preseed_demo_fixtures import persist_historical_gap, plan_historical_gap

DAY = 86400


def history() -> list[dict[str, Any]]:
    common = {"centroids": [[[0.5]]], "shape": [1, 1, 1], "iks": 1.0,
              "factor_names_hash": "fixture", "category": "produce", "action": "approve",
              "domain": "purchasing", "metadata": {}}
    return [{**common, "checkpoint_id": "before", "created_at": 10 * DAY, "verified_count": 485, "decisions_count": 485},
            {**common, "checkpoint_id": "after", "created_at": 24 * DAY, "verified_count": 499, "decisions_count": 499}]


def test_gap_uses_pre_gap_count_not_current_count() -> None:
    plan = plan_historical_gap(history(), [{"created_at": 24 * DAY, "verified_at": 24 * DAY}])
    assert plan["source"]["verified_count"] == 485
    assert plan["end"] - plan["start"] == 8 * DAY


@pytest.mark.parametrize("field", ["created_at", "verified_at"])
def test_activity_inside_gap_refused(field: str) -> None:
    with pytest.raises(RuntimeError, match="No observed"):
        plan_historical_gap(history(), [{field: 14 * DAY}])


def test_revision_roundtrip_preserves_audit_and_restore_history(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "gap.db", domain="purchasing")
    try:
        rows = history()
        for row in rows:
            store.write_centroid_checkpoint(**{key: value for key, value in row.items() if key != "created_at"})
            # Reproduce a persisted historical database in this disposable file.
            store.connection.execute("UPDATE centroid_checkpoints SET created_at=? WHERE checkpoint_id=?",
                                     (row["created_at"], row["checkpoint_id"]))
        store.connection.commit()
        old = {**rows[-1], "checkpoint_id": "SDK-PRESEED-PILOT02-v2-1", "metadata": {
            "historical_import": {"observed_at": 18 * DAY, "planted": True,
                "provenance": "synthetic", "evidence_tier": "T-sim", "description": "Old mismatched import"}}}
        store.write_centroid_checkpoint(**{key: value for key, value in old.items() if key != "created_at"})
        before = store.get_centroid_checkpoints("purchasing", include_v2=True, limit=None)
        result = persist_historical_gap(store)
        expected_verified = rows[-1]["verified_count"]
        assert result["verified_count"] == expected_verified
        assert result["superseded_imports"] == 0
        assert store.get_centroid_checkpoints("purchasing", include_v2=True, limit=None) == before
        assert store.count_decisions("purchasing") == 0
        manifest = store.get_governance("purchasing", HISTORY_IMPORT_KEY)
        assert manifest["revision"] == result["revision"]
        assert manifest["supersessions"] == {}
        app = FastAPI()
        app.include_router(create_self_computation_router(store, domain="purchasing"))
        with TestClient(app) as client:
            active_response = client.get("/api/self/centroid-history")
            assert active_response.status_code == 200
            active = active_response.json()["checkpoints"]
            full = client.get("/api/self/centroid-history?include_superseded=true").json()["checkpoints"]
        assert old["checkpoint_id"] in {row["checkpoint_id"] for row in active}
        retained = next(row for row in full if row["checkpoint_id"] == old["checkpoint_id"])
        assert retained.get("superseded") is not True
        assert retained["verified_count"] == 499  # Audit evidence is not rewritten.
        planted = sorted(
            (
                row
                for row in active
                if (row.get("metadata") or {}).get("origin") == "demo_reseed"
            ),
            key=lambda row: row["created_at"],
        )
        assert len(planted) == 2
        assert planted[1]["created_at"] - planted[0]["created_at"] == 8 * DAY
        assert all(row["verified_count"] == expected_verified for row in planted)
    finally:
        store.close()


def test_supersession_cannot_hide_ordinary_checkpoints() -> None:
    rows = history()
    manifest = {"supersessions": {"before": {"superseded": True, "superseded_by": "demo_reseed_1"}}}
    assert project_historical_checkpoints(rows, manifest) == rows
