"""FastAPI entrypoint for the Purchasing Copilot backend."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
GAE_PATH = WORKSPACE_ROOT / "graph-attention-engine-v50"

for path in (REPO_ROOT, GAE_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .context_router import router as context_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / "purchasing.db"
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://localhost:5174,"
    "http://localhost:5175,"
    "http://localhost:5176,"
    "http://localhost:5177"
)


def _cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    ]


def _graph_store(db_path: str | Path):
    store = SQLiteGraphStore(str(db_path), domain="purchasing")
    store.penalty_ratio = 3.0
    return store


class _FixtureEvolutionLedger:
    def __init__(self, fixture_path: Path):
        self._fixture_path = fixture_path

    async def run_query(self, query: str) -> list[dict[str, Any]]:
        payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        variants = payload["variants"]
        return _filter_variants_by_query(variants, query)


def _ledger_provider() -> _FixtureEvolutionLedger:
    return _FixtureEvolutionLedger(DATA_DIR / "evolution_fixtures.json")


def _filter_variants_by_query(
    variants: list[dict[str, Any]],
    query: str | None,
) -> list[dict[str, Any]]:
    query_lower = query.lower() if query else ""
    wants_promoted = "promoted" in query_lower or "promotion_approved" in query_lower
    wants_rejected = "rejected" in query_lower or "promotion_rejected" in query_lower
    wants_shadow = "shadow" in query_lower
    if sum([wants_promoted, wants_rejected, wants_shadow]) != 1:
        return variants
    if wants_promoted:
        return [
            variant
            for variant in variants
            if _variant_status(variant) in {"promoted", "approved", "promotion_approved"}
        ]
    if wants_rejected:
        return [
            variant
            for variant in variants
            if _variant_status(variant) in {"rejected", "promotion_rejected"}
        ]
    return [
        variant
        for variant in variants
        if _variant_status(variant) in {"shadow", "shadow_testing"}
    ]


def _variant_status(variant: dict[str, Any]) -> str:
    return str(
        variant.get("status")
        or variant.get("event_type")
        or variant.get("eventType")
        or ""
    ).lower()


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Purchasing Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = str(db_path or DEFAULT_DB_PATH)
    app.include_router(
        create_scoring_router(
            "purchasing",
            db_path=scoring_db,
            scorer_factory=lambda: FreshScorerProxy("purchasing", scoring_db, _graph_store),
        ),
        prefix="/api",
    )
    app.include_router(
        create_evolution_router("purchasing", ledger_provider=_ledger_provider),
        prefix="/api",
    )

    # Conservation router
    app.include_router(
        create_conservation_router(
            "purchasing",
            state_provider=lambda: _graph_store(scoring_db),
        ),
        prefix="/api",
    )
    mount_self_computation_router(app, _graph_store(scoring_db))
    app.include_router(context_router, prefix="/api/context")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "domain": "purchasing",
            "engine": "copilot_sdk.scoring + gae.profile_scorer + gae.evolution",
        }

    return app


app = create_app()
