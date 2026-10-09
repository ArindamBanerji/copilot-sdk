"""Endpoint regression for canonical fingerprint publication ordering."""
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time

from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
from copilot_sdk.backend.transfer_router import create_transfer_router
from copilot_sdk.graph import InMemoryGraphStore


@pytest.mark.parametrize("export_order", [("old", "new"), ("new", "old")])
def test_opportunities_use_latest_publication_when_epochs_and_ids_disagree(
    tmp_path: Path, export_order: tuple[str, str],
) -> None:
    graph = InMemoryGraphStore(domain="purchasing")
    revisions = {"old": ("z-old", 1, 0.10), "new": ("a-new", 2, 0.12)}
    with freeze_time("2026-01-01"):
        for name in export_order:
            identifier, tick, sigma = revisions[name]
            graph.write_fingerprint(
                identifier, "trading", ["shared"],
                {"factors": [{"name": "shared", "sigma": sigma}]}, 0, 0,
                metadata={"exported_at": 1000.0, "export_tick": tick},
            )
        graph.write_fingerprint(
            "target", "purchasing", ["shared"],
            {"factors": [{"name": "shared", "sigma": 0.5}]}, 0, 0,
            metadata={"exported_at": 1000.0, "export_tick": 3},
        )
    proxy = FreshScorerProxy(
        "purchasing", tmp_path / "unused.db", lambda path: graph, profile="test",
    )
    app = FastAPI()
    app.include_router(create_transfer_router(proxy))
    with TestClient(app) as client:
        response = client.get("/api/transfer/opportunities")
    assert response.status_code == 200
    opportunities = response.json()["opportunities"]
    assert len(opportunities) == 1
    assert opportunities[0]["direction"] == "trading->purchasing"
    assert opportunities[0]["source_sigma"] == 0.12

