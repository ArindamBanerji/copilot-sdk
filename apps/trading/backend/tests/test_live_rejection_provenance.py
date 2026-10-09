"""Live rejection summaries retain evidence origins from their source variants."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from copilot_sdk.demo.preseed import DemoPreseed
from copilot_sdk.evolution import GraphVariantStore
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer

from app.routers.evolution_router import create_trading_evolution_router
from app.services.trading_evolver import TradingAgentEvolver


@pytest.mark.parametrize(
    ("seed_synthetic", "add_learned", "expected"),
    [(True, False, "synthetic"), (False, True, "learned"), (True, True, "mixed")],
    ids=["live-preseed", "live-learned", "live-and-persisted-mixed"],
)
def test_live_rejection_provenance_survives_the_evolver_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    seed_synthetic: bool, add_learned: bool, expected: str,
) -> None:
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(tmp_path / "outbox.db"))
    graph = InMemoryGraphStore(domain="trading")
    seeded: list[dict[str, Any]] = []
    if seed_synthetic:
        result = DemoPreseed(
            fast_mode=True, graph_store=graph, profile="test",
        ).preseed_trading()
        seeded = [result.rejected_variants[0]]
        assert seeded[0]["provenance"] == "synthetic"

    baseline = CompoundingScorer.from_preset("trading", graph_store=graph, profile="test")
    evolver = TradingAgentEvolver(
        baseline_scorer=baseline,
        store_factory=lambda: InMemoryGraphStore(domain="trading"),
        conservation_provider=baseline.get_conservation_state,
        variant_store=GraphVariantStore(graph, "trading"),
    )
    evolver.register_variants(seeded)
    variants = list(seeded)
    origins = {str(variant["variant_id"]): "synthetic" for variant in seeded}
    if add_learned:
        variant = {"variant_id": "verified-variant", "provenance": "learned", "adjustments": {}}
        evolver.register_variants([variant])
        evolver.record_verified_outcome("verified-variant", True, "trend_following")
        variants.append(variant)
        origins["verified-variant"] = "learned"

    for variant in variants:
        decisions = [
            {"actual_action": "strong_execution",
             "baseline_correct": True, "variant_correct": True}
            for _ in range(50)
        ]
        for _ in range(3):
            evolver.shadow_test(variant, decisions)
        stored = GraphVariantStore(graph, "trading").get_variant(str(variant["variant_id"]))
        assert stored is not None
        assert stored.metadata["provenance"] == origins[stored.id]

    app = FastAPI()
    app.include_router(create_trading_evolution_router(
        evolver=evolver, graph_store_factory=lambda: graph,
        include_persisted_rejections=True,
    ))
    with TestClient(app) as client:
        response = client.get("/api/trading/evolution/rejection-summary")
        log_response = client.get("/api/trading/evolution/log", params={"kind": "variant"})
    assert response.status_code == log_response.status_code == 200
    body = response.json()
    assert body["provenance"] == expected
    entries = {entry["variant_id"]: entry for entry in body["rejected_variants"]}
    live_log = {entry["variant_id"]: entry for entry in log_response.json()}
    for variant_id, origin in origins.items():
        assert entries[variant_id]["provenance"] == origin
        assert entries[variant_id]["reason"] == "correctness_floor"
        assert live_log[variant_id]["provenance"] == origin
    if seed_synthetic:
        # The live row overrides the same preseed ID without changing its origin.
        assert entries["TRADING_AE_v1"]["provenance"] == "synthetic"

