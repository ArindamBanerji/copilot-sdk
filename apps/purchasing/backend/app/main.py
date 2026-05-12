"""FastAPI entrypoint for the Purchasing Copilot backend."""

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

for path in (REPO_ROOT, GAE_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .context_router import router as context_router  # noqa: E402
from copilot_sdk.backend import create_conservation_router, create_evolution_router, create_scoring_router  # noqa: E402
from copilot_sdk.scoring import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.storage import DecisionStore  # noqa: E402


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / "purchasing.db"


class _StoreProxy:
    def __init__(self, db_path: str):
        self._db_path = db_path

    def get_decision(self, decision_id: str) -> dict:
        store = DecisionStore(self._db_path)
        try:
            return store.get_decision(decision_id)
        finally:
            store.close()

    def get_all_decisions(self) -> list[dict]:
        store = DecisionStore(self._db_path)
        try:
            return store.get_all_decisions()
        finally:
            store.close()

    def count_verified(self) -> int:
        store = DecisionStore(self._db_path)
        try:
            return store.count_verified()
        finally:
            store.close()

    def count_correct(self) -> int:
        store = DecisionStore(self._db_path)
        try:
            return store.count_correct()
        finally:
            store.close()


class _FreshScorerProxy:
    """Open scorers per call so FastAPI worker threads do not share SQLite handles."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self.store = _StoreProxy(db_path)

    def _scorer(self) -> CompoundingScorer:
        return CompoundingScorer.from_preset("purchasing", db_path=self._db_path)

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
        payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
        variants = payload["variants"]
        return _filter_variants_by_query(variants, query)


def _ledger_provider() -> _FixtureEvolutionLedger:
    return _FixtureEvolutionLedger(DATA_DIR / "evolution_fixtures.json")


def _conservation_state(db_path: str | Path | None = None) -> dict[str, float | int]:
    store = DecisionStore(str(db_path or DEFAULT_DB_PATH))
    try:
        verified_count = _count_verified(store)
        correct_count = _count_correct(store)
        total_decisions = len(store.get_all_decisions())
    finally:
        store.close()
    return {
        "verified_count": verified_count,
        "correct_count": correct_count,
        "total_decisions": total_decisions,
        "penalty_ratio": 3.0,
    }


def _count_verified(store: Any) -> int:
    count_verified = getattr(store, "count_verified", None)
    if callable(count_verified):
        return int(count_verified())
    return sum(1 for decision in store.get_all_decisions() if _is_verified_decision(decision))


def _count_correct(store: Any) -> int:
    count_correct = getattr(store, "count_correct", None)
    if callable(count_correct):
        return int(count_correct())
    return sum(1 for decision in store.get_all_decisions() if _is_correct_decision(decision))


def _is_verified_decision(decision: dict[str, Any]) -> bool:
    outcome = decision.get("outcome")
    if outcome is not None:
        return str(outcome).strip() != ""
    return decision.get("is_correct") is not None


def _is_correct_decision(decision: dict[str, Any]) -> bool:
    outcome = str(decision.get("outcome") or "").lower()
    return outcome == "confirmed" or bool(decision.get("is_correct"))


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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = str(db_path or DEFAULT_DB_PATH)
    app.include_router(
        create_scoring_router(
            "purchasing",
            db_path=scoring_db,
            scorer_factory=lambda: _FreshScorerProxy(scoring_db),
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
            state_provider=lambda: _conservation_state(scoring_db),
        ),
        prefix="/api",
    )
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
