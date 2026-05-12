"""FastAPI entrypoint for the DataOps Copilot backend."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
GAE_PATH = WORKSPACE_ROOT / "graph-attention-engine-v50"
CI_PLATFORM_PATH = WORKSPACE_ROOT / "ci-platform"

for path in (REPO_ROOT, GAE_PATH, CI_PLATFORM_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .ae_router import router as ae_router  # noqa: E402
from .context_router import router as context_router  # noqa: E402
from .graph_queries import DataOpsGraphClient  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring import CompoundingScorer  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / "dataops.db"


def _graph_store(db_path: str | Path):
    store = SQLiteGraphStore(str(db_path), domain="dataops")
    store.penalty_ratio = 10.0
    return store


class _FreshScorerProxy:
    """Open scorers per call so FastAPI worker threads do not share SQLite handles."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self.store = _graph_store(db_path)

    def _scorer(self) -> CompoundingScorer:
        return CompoundingScorer.from_preset("dataops", db_path=self._db_path)

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


class _FixtureEvolutionLedger:
    def __init__(self, fixture_path: Path):
        self._fixture_path = fixture_path

    async def run_query(self, query: str) -> list[dict[str, Any]]:
        if not self._fixture_path.exists():
            return []
        payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        variants = payload.get("variants", [])
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
    app = FastAPI(title="DataOps Copilot", version="0.1.0")
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
            "dataops",
            db_path=scoring_db,
            scorer_factory=lambda: _FreshScorerProxy(scoring_db),
        ),
        prefix="/api",
    )
    app.include_router(
        create_conservation_router(
            "dataops",
            state_provider=lambda: _graph_store(scoring_db),
        ),
        prefix="/api",
    )
    app.include_router(
        create_evolution_router("dataops", ledger_provider=_ledger_provider),
        prefix="/api",
    )
    mount_self_computation_router(app, _graph_store(scoring_db))
    app.include_router(context_router, prefix="/api/context")
    app.include_router(ae_router, prefix="/api/ae")

    @app.get("/health")
    def health() -> dict[str, Any]:
        graph = DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")
        return {
            "status": "ok",
            "domain": "dataops",
            "graph_connected": graph.is_graph_connected,
            "graph_source": graph.graph_source,
            "engine": (
                "copilot_sdk.scoring + gae.profile_scorer + gae.calibration + "
                "gae.evolution + ci_platform.graph"
            ),
        }

    return app


app = create_app()
