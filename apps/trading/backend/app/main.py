"""FastAPI entrypoint for the Trading Copilot backend."""

from __future__ import annotations

import json
import sys
import os
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
from .graph_status import (  # noqa: E402
    create_trading_active_graph_store,
    initialize_trading_active_graph_config,
    router as trading_graph_status_router,
)
from .routers.broker_router import create_broker_router  # noqa: E402
from .routers.analytics import create_analytics_router  # noqa: E402
from .routers.correlation import create_correlation_router  # noqa: E402
from .routers.data_import import router as data_import_router  # noqa: E402
from .routers.evidence import create_evidence_router  # noqa: E402
from .evolution import get_trading_variants  # noqa: E402
from .routers.journal import create_journal_router  # noqa: E402
from .routers.prescore import create_prescore_router  # noqa: E402
from .routers.promotion import create_promotion_router  # noqa: E402
from .routers.regime import create_regime_router  # noqa: E402
from .routers.social import create_social_router  # noqa: E402
from .routers.vix_timing import create_vix_timing_router  # noqa: E402
from .routers.webhook import create_webhook_router  # noqa: E402
from copilot_sdk.backend.transfer_router import create_transfer_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


DOMAIN = "trading"
DB_FILENAME = "trading.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / DB_FILENAME
SEED_FIXTURE_PATH = DATA_DIR / "trading_seed_v2.json"
FACTOR_NAMES = tuple(TradingPreset().shape.factor_names)
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
    store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="TRD-")
    store.penalty_ratio = TradingPreset().penalty_ratio
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


def _promotion_config_dir(scoring_db: str) -> Path:
    if scoring_db == ":memory:":
        return DATA_DIR
    return Path(scoring_db).parent


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
        if isinstance(nested_factors, dict) and factor in nested_factors:
            value = nested_factors.get(factor)
        else:
            value = entry.get(factor)
        factors[factor] = _coerce_factor(value)
    return factors


def _seed_metadata(entry: dict[str, Any], sequence: int, scored_factors: dict[str, float]) -> dict[str, Any]:
    metadata = {key: value for key, value in entry.items() if key != "factors"}
    metadata.update({
        "seed_domain": DOMAIN,
        "seed_index": sequence,
        "seed_id": entry.get("trade_id") or entry.get("ticker") or str(sequence),
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
                or entry.get("direction")
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
                            "seed_id": entry.get("trade_id") or entry.get("ticker") or str(sequence),
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
    scorer = CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=graph_store,
        evolve=True,
        consolidation_enabled=True,
    )
    seeded = _seed_from_fixtures(scorer, graph_store)
    print(
        f"[{DOMAIN}] auto-seeded {seeded['decisions_seeded']} decisions "
        f"and {seeded['outcomes_seeded']} outcomes"
    )
    return seeded["decisions_seeded"]


def create_app(
    db_path: str | Path | None = None,
    demo_bundle_path: str | Path | bool | None = None,
    active_store_factory: Any | None = None,
) -> FastAPI:
    app = FastAPI(title="Trading Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = _resolve_scoring_db(db_path)
    active_graph_config = initialize_trading_active_graph_config()
    active_graph_store = create_trading_active_graph_store(
        active_graph_config,
        store_factory=active_store_factory,
    )

    def selected_graph_store_factory(path: str | Path):
        if active_graph_store is not None:
            return active_graph_store
        return _graph_store(path)

    if demo_bundle_path is None:
        _bundle_path = REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"
    elif demo_bundle_path is False:
        _bundle_path = False
    else:
        _bundle_path = Path(demo_bundle_path)
    seed_graph_store = _graph_store(scoring_db)
    startup_state = {"seeded": False, "restored": False}
    scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, selected_graph_store_factory)
    dk_welford_tracker = DKWelfordTracker()
    l5_startup_status = {
        "dk_source": "cold-start",
        "welford_source": "cold-start",
        "centroid_source": "cold-start",
        "conservation_source": "cold-start",
        "dk_weights_loaded": False,
        "centroids_loaded": False,
        "conservation_state": None,
    }

    def _run_startup_seed_once() -> None:
        if not startup_state["seeded"]:
            startup_state["seeded"] = True
            if active_graph_store is not None:
                print(f"[{DOMAIN}] auto-seed skipped while active AGE is enabled")
            else:
                if _bundle_path is not False:
                    _restore_demo_bundle(seed_graph_store, _bundle_path, domain=DOMAIN)
                _auto_seed_if_needed(seed_graph_store)
        if not startup_state["restored"]:
            startup_state["restored"] = True
            status = restore_l5_runtime_state(
                domain=DOMAIN,
                scorer=scorer_proxy._scorer(),
                learning_store=scorer_proxy.graph_store,
                welford_tracker=dk_welford_tracker,
            )
            status.pop("welford_tracker", None)
            app.state.l5_startup_status = status

    app.state.trading_active_graph_config = active_graph_config
    app.state.trading_selected_graph_store = scorer_proxy.graph_store
    app.state.l5_startup_status = l5_startup_status
    app.include_router(
        create_scoring_router(
            DOMAIN,
            db_path=scoring_db,
            scorer_factory=lambda: scorer_proxy,
            dk_welford_tracker=dk_welford_tracker,
        ),
        prefix="/api",
    )
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            variant_provider=get_trading_variants,
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
    mount_self_computation_router(app, selected_graph_store_factory(scoring_db))
    app.include_router(context_router, prefix="/api/context")
    app.include_router(create_evidence_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_journal_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_analytics_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_correlation_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_prescore_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(
        create_promotion_router(
            lambda: selected_graph_store_factory(scoring_db),
            config_dir=_promotion_config_dir(scoring_db),
            domain=DOMAIN,
        )
    )
    app.include_router(create_regime_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_social_router(scorer_proxy))
    app.include_router(create_vix_timing_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_webhook_router(scorer_proxy))
    app.include_router(create_broker_router(), prefix="/api/broker", tags=["broker"])
    app.include_router(data_import_router)
    app.include_router(trading_graph_status_router)

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
            "engine": "copilot_sdk.scoring + gae.profile_scorer",
        }

    return app


app = create_app()
