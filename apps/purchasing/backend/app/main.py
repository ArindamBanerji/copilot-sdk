"""FastAPI entrypoint for the Purchasing Copilot backend."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
GAE_PATH = WORKSPACE_ROOT / "graph-attention-engine-v50"

for path in (BACKEND_ROOT, REPO_ROOT, GAE_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .context_router import router as context_router  # noqa: E402
from .routers.evidence import create_evidence_router  # noqa: E402
from copilot_sdk.backend.transfer_router import create_transfer_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402


DOMAIN = "purchasing"
DB_FILENAME = "purchasing.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / DB_FILENAME
SEED_FIXTURE_PATH = DATA_DIR / "purchasing_seed_v2.json"
FACTOR_NAMES = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)
FIELD_MAP = {"day_of_week": "day_of_week_factor"}
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
    store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="PUR-")
    store.penalty_ratio = 3.0
    return store


def _resolve_scoring_db(db_path: str | Path | None) -> str:
    if db_path is not None:
        resolved = Path(db_path)
    elif os.environ.get("CI_DATA_DIR"):
        resolved = Path(os.environ["CI_DATA_DIR"]) / DB_FILENAME
    else:
        resolved = DEFAULT_DB_PATH
    if str(resolved) != ":memory:":
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return str(resolved)


def _coerce_factor(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.5
    return max(0.0, min(score, 1.0))


def _build_seed_context(entry: dict[str, Any]) -> dict[str, float]:
    nested_factors = entry.get("factors")
    factors: dict[str, float] = {}
    for factor in FACTOR_NAMES:
        source_key = FIELD_MAP.get(factor, factor)
        if isinstance(nested_factors, dict) and factor in nested_factors:
            value = nested_factors.get(factor)
        else:
            value = entry.get(source_key)
        factors[factor] = _coerce_factor(value)
    return factors


def _seed_metadata(entry: dict[str, Any], sequence: int, scored_factors: dict[str, float]) -> dict[str, Any]:
    metadata = {key: value for key, value in entry.items() if key != "factors"}
    metadata.update({
        "seed_domain": DOMAIN,
        "seed_index": sequence,
        "seed_id": entry.get("order_id") or entry.get("item") or str(sequence),
        "source_seed_index": sequence,
        "scored_factors": dict(scored_factors),
    })
    return metadata


def _result_value(result: Any, key: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _seed_from_fixtures(scorer: CompoundingScorer, graph_store: SQLiteGraphStore) -> dict[str, int]:
    try:
        entries = json.loads(SEED_FIXTURE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[{DOMAIN}] auto-seed fixture unavailable: {exc}")
        return {"decisions_seeded": 0, "outcomes_seeded": 0}
    if not isinstance(entries, list):
        print(f"[{DOMAIN}] auto-seed fixture is not a list")
        return {"decisions_seeded": 0, "outcomes_seeded": 0}

    decisions_seeded = 0
    outcomes_seeded = 0
    for sequence, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        category = entry.get("category")
        if not category:
            continue
        try:
            factors = _build_seed_context(entry)
            result = scorer.score(
                factors,
                str(category),
                metadata=_seed_metadata(entry, sequence, factors),
            )
            decision_id = _result_value(result, "decision_id")
            action = (
                entry.get("action_taken")
                or entry.get("actual_action")
                or entry.get("recommended_action")
                or _result_value(result, "action")
            )
            if not decision_id:
                raise ValueError("score result missing decision_id")
            decisions_seeded += 1
            if "is_correct" in entry and action:
                graph_store.write_outcome(
                    str(decision_id),
                    actual_action=str(action),
                    is_correct=bool(entry["is_correct"]),
                    metadata={
                        "actual_index": 0,
                        "context": {
                            "source": "auto_seed",
                            "seed_domain": DOMAIN,
                            "seed_index": sequence,
                            "seed_id": entry.get("order_id") or entry.get("item") or str(sequence),
                            "source_seed_index": sequence,
                        },
                    },
                )
                outcomes_seeded += 1
        except Exception as exc:
            print(f"[{DOMAIN}] auto-seed skipped entry {sequence}: {exc}")
    if entries and decisions_seeded == 0:
        print(f"[{DOMAIN}] warning: auto-seed wrote no decisions")
    expected_outcomes = sum(1 for entry in entries if isinstance(entry, dict) and "is_correct" in entry)
    if expected_outcomes > 0 and outcomes_seeded == 0:
        print(f"[{DOMAIN}] warning: auto-seed wrote no fixture outcomes")
    return {"decisions_seeded": decisions_seeded, "outcomes_seeded": outcomes_seeded}


def _auto_seed_if_needed(graph_store: SQLiteGraphStore) -> int:
    try:
        count = int(graph_store.count_decisions(DOMAIN))
    except Exception as exc:
        print(f"[{DOMAIN}] auto-seed count failed: {exc}")
        return 0
    if count > 0:
        print(f"[{DOMAIN}] resuming with {count} persisted decisions")
        return 0
    scorer = CompoundingScorer.from_preset(DOMAIN, graph_store=graph_store)
    seeded = _seed_from_fixtures(scorer, graph_store)
    print(
        f"[{DOMAIN}] auto-seeded {seeded['decisions_seeded']} decisions "
        f"and {seeded['outcomes_seeded']} outcomes"
    )
    return seeded["decisions_seeded"]


def _evolution_variants() -> list[dict[str, Any]]:
    fixture_path = DATA_DIR / "evolution_fixtures.json"
    if not fixture_path.exists():
        return []
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    variants = payload.get("variants")
    if not isinstance(variants, list):
        return []
    return _filter_variants_by_query(variants, None)


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

    scoring_db = _resolve_scoring_db(db_path)
    seed_graph_store = _graph_store(scoring_db)
    startup_state = {"seeded": False}
    scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, _graph_store)
    app.include_router(
        create_scoring_router(
            DOMAIN,
            db_path=scoring_db,
            scorer_factory=lambda: scorer_proxy,
        ),
        prefix="/api",
    )
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: _graph_store(scoring_db),
            domain=DOMAIN,
            variant_provider=_evolution_variants,
        )
    )

    # Conservation router
    app.include_router(
        create_conservation_router(
            DOMAIN,
            state_provider=scorer_proxy,
        ),
        prefix="/api",
    )
    mount_self_computation_router(app, _graph_store(scoring_db))
    app.include_router(context_router, prefix="/api/context")
    app.include_router(create_evidence_router(scorer_proxy))

    def _run_startup_seed_once() -> None:
        if startup_state["seeded"]:
            return
        startup_state["seeded"] = True
        _auto_seed_if_needed(seed_graph_store)

    @app.on_event("startup")
    async def auto_seed_on_startup() -> None:
        _run_startup_seed_once()

    @app.middleware("http")
    async def direct_testclient_autoseed(request, call_next):
        if request.url.path == "/api/health":
            _run_startup_seed_once()
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "domain": DOMAIN,
            "engine": "copilot_sdk.scoring + gae.profile_scorer + gae.evolution",
        }

    return app


app = create_app()
