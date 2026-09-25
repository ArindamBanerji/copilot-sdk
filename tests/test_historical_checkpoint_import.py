"""Historical demo imports retain a distinct ingestion clock and provenance."""
from pathlib import Path
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from copilot_sdk.backend.historical_checkpoint import normalize_historical_checkpoint
from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def test_real_store_historical_gap_roundtrip(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "history.db", domain="purchasing")
    now = time.time()
    try:
        for index, days in enumerate((14, 6)):
            store.write_centroid_checkpoint(checkpoint_id=f"import-{index}", domain="purchasing",
                category="produce", action="approve", centroids=[[[0.5]]], decisions_count=3,
                verified_count=3, iks=0.0, shape=[1, 1, 1], factor_names_hash="example",
                metadata={"historical_import": {"observed_at": now - days * 86400,
                    "planted": True, "provenance": "synthetic", "evidence_tier": "T-sim",
                    "description": "Synthetic demonstration"}})
        app = FastAPI()
        app.include_router(create_self_computation_router(store, domain="purchasing"))
        with TestClient(app) as client:
            response = client.get("/api/self/centroid-history")
            assert response.status_code == 200
            rows = sorted(response.json()["checkpoints"], key=lambda row: row["created_at"])
        assert rows[1]["created_at"] - rows[0]["created_at"] == 8 * 86400
        assert rows[0]["verified_count"] == rows[1]["verified_count"] == 3
        assert all(row["ingested_at"] >= now for row in rows)
        assert all(row["provenance"] == "synthetic" and row["planted"] for row in rows)
        assert all(row["created_at"] >= now for row in store.get_centroid_checkpoints("purchasing", include_v2=True))
        assert store.count_decisions("purchasing") == 0
    finally:
        store.close()


def test_ordinary_checkpoint_timestamp_unchanged() -> None:
    row = {"created_at": 123, "metadata": {}}
    assert normalize_historical_checkpoint(row) == row


@pytest.mark.parametrize("value", [float("nan"), -1, float("inf")])
def test_invalid_historical_time_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        normalize_historical_checkpoint({"created_at": 123, "metadata": {"historical_import": {
            "observed_at": value, "planted": True, "provenance": "synthetic", "evidence_tier": "T-sim",
            "description": "Demo"}}})
