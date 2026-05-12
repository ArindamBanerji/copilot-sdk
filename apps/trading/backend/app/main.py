"""FastAPI entrypoint for the Trading Copilot backend."""

from __future__ import annotations

import sys
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
from copilot_sdk.backend import create_conservation_router, create_scoring_router  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring import CompoundingScorer  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / "trading.db"


def _graph_store(db_path: str | Path):
    store = SQLiteGraphStore(str(db_path), domain="trading")
    store.penalty_ratio = 2.0
    return store


class _FreshScorerProxy:
    """Open scorers per call so FastAPI worker threads do not share SQLite handles."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self.store = _graph_store(db_path)

    def _scorer(self) -> CompoundingScorer:
        return CompoundingScorer.from_preset("trading", db_path=self._db_path)

    def score(self, factors: dict[str, float], category: str):
        scorer = self._scorer()
        try:
            return scorer.score(factors, category)
        finally:
            scorer._store.close()

    def learn(self, decision_id: str, actual_action: str, outcome: str = "confirmed"):
        scorer = self._scorer()
        try:
            return scorer.learn(decision_id, actual_action, outcome)
        finally:
            scorer._store.close()

    def fingerprint(self):
        scorer = self._scorer()
        try:
            return scorer.fingerprint()
        finally:
            scorer._store.close()

    def trajectory(self):
        scorer = self._scorer()
        try:
            return scorer.trajectory()
        finally:
            scorer._store.close()

def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Trading Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = str(db_path or DEFAULT_DB_PATH)
    app.include_router(
        create_scoring_router(
            "trading",
            db_path=scoring_db,
            scorer_factory=lambda: _FreshScorerProxy(scoring_db),
        ),
        prefix="/api",
    )

    # Conservation router
    app.include_router(
        create_conservation_router(
            "trading",
            state_provider=lambda: _graph_store(scoring_db),
        ),
        prefix="/api",
    )
    app.include_router(context_router, prefix="/api/context")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "domain": "trading",
            "engine": "copilot_sdk.scoring + gae.profile_scorer",
        }

    return app


app = create_app()
