"""Real scorer mutations must not prevent the event loop from serving reads."""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.scoring.mutation_lock import mutation_lock_scope
from copilot_sdk.scoring.scorer import CompoundingScorer


@pytest.mark.parametrize("domain", ["purchasing", "trading", "dataops"])
def test_waiting_score_does_not_block_reads(tmp_path: Path, domain: str) -> None:
    scorer = CompoundingScorer.from_preset(domain, db_path=str(tmp_path / "score.db"), profile="test")
    app = FastAPI()
    app.include_router(create_scoring_router(domain, scorer_factory=lambda: scorer))

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    acquired = threading.Event()

    def occupy_mutation_lock() -> None:
        with mutation_lock_scope(domain):
            acquired.set()
            time.sleep(0.6)

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            holder = threading.Thread(target=occupy_mutation_lock)
            holder.start()
            assert acquired.wait(2)
            started = time.perf_counter()
            score = asyncio.create_task(client.post("/score", json={
                "category": scorer._preset.shape.category_names[0], "factors": {},
            }))
            await asyncio.sleep(0.03)
            response = await client.get("/ping")
            ping_seconds = time.perf_counter() - started
            scored = await score
            holder.join()
            assert response.status_code == 200
            assert scored.status_code == 200, scored.text
            assert scorer.graph_store.get_decision(scored.json()["decision_id"], domain=domain)
            assert ping_seconds < 0.3, f"event loop blocked for {ping_seconds:.3f}s"

    try:
        asyncio.run(exercise())
    finally:
        scorer.graph_store.close()
