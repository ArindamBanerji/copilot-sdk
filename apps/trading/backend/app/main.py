"""FastAPI entrypoint for the Trading Copilot backend."""

from __future__ import annotations

import sys
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
GAE_PATH = WORKSPACE_ROOT / "graph-attention-engine-v50"

for path in (REPO_ROOT, GAE_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .context_router import router as context_router  # noqa: E402
from .routers.data_import import router as data_import_router  # noqa: E402
from copilot_sdk.backend.transfer_router import create_transfer_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / "trading.db"
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
    store = SQLiteGraphStore(str(db_path), domain="trading")
    store.penalty_ratio = TradingPreset().penalty_ratio
    return store


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Trading Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = str(db_path or DEFAULT_DB_PATH)
    scorer_proxy = FreshScorerProxy("trading", scoring_db, _graph_store)
    app.include_router(
        create_scoring_router(
            "trading",
            db_path=scoring_db,
            scorer_factory=lambda: FreshScorerProxy("trading", scoring_db, _graph_store),
        ),
        prefix="/api",
    )
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: _graph_store(scoring_db),
            domain="trading",
            variant_provider=lambda: [],
        )
    )

    # Conservation router
    app.include_router(
        create_conservation_router(
            "trading",
            state_provider=lambda: _graph_store(scoring_db),
        ),
        prefix="/api",
    )
    mount_self_computation_router(app, _graph_store(scoring_db))
    app.include_router(context_router, prefix="/api/context")
    app.include_router(data_import_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "domain": "trading",
            "engine": "copilot_sdk.scoring + gae.profile_scorer",
        }

    return app


app = create_app()
