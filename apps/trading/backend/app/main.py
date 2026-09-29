"""FastAPI entrypoint for the Trading Copilot backend."""

from __future__ import annotations

import json
import asyncio
import sys
import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
GAE_PATH = WORKSPACE_ROOT / "graph-attention-engine-v50"
CI_PLATFORM_PATH = WORKSPACE_ROOT / "ci-platform"

for path in (BACKEND_ROOT, REPO_ROOT, GAE_PATH, CI_PLATFORM_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .context_router import router as context_router  # noqa: E402
from .graph_status import (  # noqa: E402
    build_trading_graph_status,
    create_trading_active_graph_store,
    initialize_trading_active_graph_config,
    router as trading_graph_status_router,
)
from .routers.broker_router import create_broker_router  # noqa: E402
from .routers.analytics import create_analytics_router  # noqa: E402
from .routers.cohort_status_router import create_cohort_status_router  # noqa: E402
from .routers.correlation import create_correlation_router  # noqa: E402
from .routers.claim_gate_router import create_claim_gate_router  # noqa: E402
from .routers.data_import import router as data_import_router  # noqa: E402
from .routers.evidence import create_evidence_router  # noqa: E402
from .routers.evolution_router import (  # noqa: E402
    create_trading_evolution_router,
)
from .routers.execution_router import create_execution_router  # noqa: E402
from .evolution import get_trading_variants  # noqa: E402
from .routers.journal import _journal_records, create_journal_router  # noqa: E402
from .routers.pre_score_router import create_pre_score_router  # noqa: E402
from .routers.prescore import create_prescore_router  # noqa: E402
from .routers.promotion import create_promotion_router  # noqa: E402
from .routers.promotion_router import create_promotion_engine_router  # noqa: E402
from .routers.regime import create_regime_router  # noqa: E402
from .routers.regime_analytics import create_regime_analytics_router  # noqa: E402
from .routers.regime_router import create_regime_router as create_regime_classifier_router  # noqa: E402
from .routers.regime_status import create_regime_status_router  # noqa: E402
from .routers.regime_beats import create_regime_beats_router  # noqa: E402
from .routers.entrant_comparison import create_entrant_comparison_router  # noqa: E402
from .routers.situation_router import create_situation_router  # noqa: E402
from .routers.social import create_social_router  # noqa: E402
from .routers.vix_timing import create_vix_timing_router  # noqa: E402
from .routers.volatility_router import create_volatility_router  # noqa: E402
from .routers.volatility_beats import create_volatility_beats_router  # noqa: E402
from .routers.webhook import create_webhook_router  # noqa: E402
from .services.journal_query import JournalQueryService  # noqa: E402
from .services.trading_materialization import create_trading_materializer  # noqa: E402
from .services.regime_monitor import RegimeMonitor  # noqa: E402
from .services.regime_scoring import TradingRegimeScorerProxy, build_regime_context  # noqa: E402
from .services.trading_evolver import TradingAgentEvolver  # noqa: E402
from .services.claim_gate import (  # noqa: E402
    TradingClaimRegistry,
    TradingEvidenceMiddleware,
    TradingPromotionGuard,
)
from copilot_sdk.evolution import create_variant_store  # noqa: E402
from .state import create_trading_tab_state_cache  # noqa: E402
from .state.compute_helpers import compute_counterfactual_default  # noqa: E402
from copilot_sdk.backend.transfer_router import (  # noqa: E402
    create_self_transfer_router,
    create_transfer_router,
)
from copilot_sdk.backend.archetype_router import create_archetype_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_investigation_router,
    create_scoring_router,
    create_switching_cost_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS
from copilot_sdk.backend.health_builder import build_graph_health, health_status_code  # noqa: E402
from copilot_sdk.backend.traversal_router import create_traversal_router  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from copilot_sdk.backend.counterfactual_router import create_counterfactual_router  # noqa: E402
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.backend.platform_router import create_platform_router  # noqa: E402
from copilot_sdk.backend.cross_signal_router import create_cross_signal_router  # noqa: E402
from copilot_sdk.backend.signal_store import GraphSignalStore  # noqa: E402
from copilot_sdk.backend.concepts_router import create_concepts_router  # noqa: E402
from copilot_sdk.evolution import ScorerBackedProvider  # noqa: E402
from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph, resolve_profile  # noqa: E402
from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
from copilot_sdk.graph.factory import create_graph_store  # noqa: E402
from copilot_sdk.graph.memory_store import InMemoryGraphStore  # noqa: E402
from copilot_sdk.scoring.fingerprint import compute_fingerprint  # noqa: E402
from fastapi.encoders import jsonable_encoder  # noqa: E402
from copilot_sdk.graph.protocol import GraphStore  # noqa: E402
from copilot_sdk.tenant_middleware import TenantMiddleware  # noqa: E402
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.composite_gate import CompositeGate  # noqa: E402
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer  # noqa: E402
from copilot_sdk.scoring.investigation import KUtilityStore  # noqa: E402
from copilot_sdk.scoring.situation_classifier import SituationClassifier  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402
from copilot_sdk.demo.startup import startup_lock  # noqa: E402
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402
from copilot_sdk.state import cached_static, create_invalidation_header_middleware, create_tab_state_router  # noqa: E402
from ci_platform.copilot_core import EntityCache, EntityContextCacheAdapter  # noqa: E402
from .investigation_config import INVESTIGATION_CONFIG, create_evidence_provider  # noqa: E402
from .vld_preseed import seed_vld_trading_showcase  # noqa: E402


DOMAIN = "trading"


def _resolve_profile() -> str:
    """Select the graph profile from explicit configuration."""
    from copilot_sdk.config import resolve_profile

    return str(resolve_profile(domain="trading"))
logger = logging.getLogger(__name__)
DB_FILENAME = "trading.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / DB_FILENAME
SEED_FIXTURE_PATH = DATA_DIR / "trading_seed_v2.json"
FACTOR_NAMES = tuple(TradingPreset().shape.factor_names)


class _VLDKDecisionConnection:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path, check_same_thread=False)


def _create_vld_k_store(path: Path, dimensions: int) -> KUtilityStore:
    return KUtilityStore(_VLDKDecisionConnection(path), dimensions)


def _vld_k_router_kwargs(path: Path, dimensions: int) -> dict[str, KUtilityStore]:
    return {"k_store": _create_vld_k_store(path, dimensions)}


def _vld_classifier_router_kwargs() -> dict[str, SituationClassifier]:
    return {"classifier": SituationClassifier()}


async def _materializer_refresh_loop(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(5)
        materializer = getattr(app.state, "materializer", None)
        refresh = getattr(materializer, "refresh", None)
        if callable(refresh):
            try:
                await asyncio.to_thread(refresh)
            except Exception:
                logger.exception("Trading materializer background refresh failed")


def _invalidate_materializer(app: FastAPI) -> None:
    materializer = getattr(app.state, "materializer", None)
    if materializer is not None:
        materializer.invalidate()


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://localhost:5174,"
    "http://localhost:5175,"
    "http://localhost:5176,"
    "http://localhost:5177,"
    "http://127.0.0.1:5173,"
    "http://127.0.0.1:5174,"
    "http://127.0.0.1:5175,"
    "http://127.0.0.1:5176,"
    "http://127.0.0.1:5177"
)


def _cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    ]


def _graph_store(db_path: str | Path, *, profile: str | None = None):
    # Active AGE configuration is owned by TRADING_ACTIVE_*; generic AGE
    # settings remain deliberately ignored by the graph-status contract.
    profile = profile or _resolve_profile()
    graph_config = None
    try:
        graph_config = GraphConfig.load(DOMAIN, profile=profile)
        backend = graph_config.backend
    except GraphConfigError:
        if profile != "test":
            raise
        # A generic AGE value without complete AGE config is intentionally not
        # an active Trading-store selection in isolated tests.
        backend = "sqlite"
    if graph_config is not None:
        require_shared_graph(
            backend=graph_config.backend,
            graph=graph_config.graph,
            domain=DOMAIN,
            profile=profile,
            test_mode=graph_config.active_test_mode,
        )
    store = create_graph_store(
        backend=backend,
        domain=DOMAIN,
        db_path=str(db_path),
        decision_id_prefix="TRD-",
        dsn=graph_config.dsn if graph_config is not None else None,
        graph_name=graph_config.graph if graph_config is not None else None,
        test_mode=graph_config.active_test_mode if graph_config is not None else False,
        profile=profile,
    )
    setattr(store, "penalty_ratio", TradingPreset().penalty_ratio)
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
    regime_context = build_regime_context(scored_factors, metadata)
    metadata.update({
        "seed_domain": DOMAIN,
        "seed_index": sequence,
        "seed_id": entry.get("trade_id") or entry.get("ticker") or str(sequence),
        "source_seed_index": sequence,
        "scored_factors": dict(scored_factors),
        "regime_metadata": {
            **regime_context,
            "tagged_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
    })
    return metadata


def _result_value(result: Any, key: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _seed_from_fixtures(scorer: CompoundingScorer, graph_store: GraphStore) -> dict[str, int]:
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
                    domain=DOMAIN,
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


def _auto_seed_if_needed(graph_store: GraphStore, *, profile: str | None = None) -> int:
    try:
        count = int(graph_store.count_decisions(DOMAIN))
    except Exception as exc:
        raise RuntimeError(f"[{DOMAIN}] auto-seed count failed") from exc
    if count > 0:
        print(f"[{DOMAIN}] resuming with {count} persisted decisions")
        return 0
    scorer = CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=graph_store,
        evolve=True,
        consolidation_enabled=True,
        profile=profile or _resolve_profile(),
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
    profile: str | None = None,
) -> FastAPI:
    resolved_profile = _resolve_profile() if profile is None else profile.strip().lower()
    app = FastAPI(title="Trading Copilot", version="0.1.0")
    app.add_middleware(TenantMiddleware)

    claim_registry = TradingClaimRegistry()
    app.state.trading_claim_registry = claim_registry
    app.add_middleware(
        TradingEvidenceMiddleware,
        registry=claim_registry,
        context=os.environ.get("TRADING_EVIDENCE_CONTEXT", "demo"),
    )

    scoring_db = _resolve_scoring_db(db_path)
    # Stable instrument/market context only; decisions and learning authority
    # remain in the graph store and are never cached.
    entity_cache = EntityCache(
        max_size=200,
        ttl_seconds=300,
        source="trading.entity_context_cache",
    )
    entity_context_cache = EntityContextCacheAdapter(entity_cache, enabled=True)
    active_graph_config = initialize_trading_active_graph_config()
    active_graph_store = create_trading_active_graph_store(
        active_graph_config,
        store_factory=active_store_factory,
    )

    def selected_graph_store_factory(path: str | Path):
        if active_graph_store is not None:
            return active_graph_store
        return _graph_store(path, profile=resolved_profile)

    _bundle_path: Path | bool
    if demo_bundle_path is None:
        _bundle_path = REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"
    elif demo_bundle_path is False:
        _bundle_path = False
    else:
        _bundle_path = Path(cast(str | Path, demo_bundle_path))
    seed_graph_store = active_graph_store or _graph_store(scoring_db, profile=resolved_profile)
    startup_state = {"seeded": False, "restored": False}
    base_scorer_proxy = FreshScorerProxy(
        DOMAIN, scoring_db, selected_graph_store_factory, profile=resolved_profile
    )
    store = base_scorer_proxy.graph_store
    logger.info("STORE_TYPE: %s", type(store).__name__)
    if hasattr(store, "primary"):
        primary = store.primary
        logger.info("PRIMARY: %s", type(primary).__name__)
        logger.info("PRIMARY_PATH: %s", getattr(primary, "_db_path", getattr(primary, "db_path", None)))
    if hasattr(store, "secondary"):
        logger.info("SECONDARY: %s", type(store.secondary).__name__)
    if hasattr(store, "_outbox"):
        outbox = store._outbox
        logger.info("OUTBOX: %s", outbox is not None)
        logger.info("OUTBOX_PATH: %s", getattr(outbox, "path", None))
    trading_preset = TradingPreset()
    regime_monitor = RegimeMonitor(config=trading_preset)
    regime_scorer_proxy = TradingRegimeScorerProxy(base_scorer_proxy, regime_monitor)
    scorer_proxy: Any = GateEnforcedScorer(regime_scorer_proxy, CompositeGate())
    tab_state_cache = create_trading_tab_state_cache(
        scorer_provider=lambda: scorer_proxy,
        graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
        regime_monitor=regime_monitor,
        materializer_provider=lambda: app.state.materializer,
    )
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

    trading_store_factory = lambda: selected_graph_store_factory(scoring_db)
    try:
        vld_seed = seed_vld_trading_showcase(trading_store_factory())
        app.state.trading_vld_showcase = vld_seed
        print(
            f"[{DOMAIN}] VLD showcase registered: "
            f"{vld_seed['trade_count']} trades, {vld_seed['evidence_records']} evidence records"
        )
    except Exception as exc:
        app.state.trading_vld_showcase = {"status": "unavailable", "error": str(exc)}
        print(f"[{DOMAIN}] VLD showcase preseed failed (non-blocking): {exc}")

    trading_promotion_guard = TradingPromotionGuard(
        claim_registry,
        graph_store=selected_graph_store_factory(scoring_db),
    )
    app.state.trading_promotion_guard = trading_promotion_guard
    claim_registry.refresh_from_store(selected_graph_store_factory(scoring_db))
    conservation_provider = ScorerBackedProvider(scorer_proxy, DOMAIN)
    variant_store = create_variant_store(store, DOMAIN, test_mode=resolved_profile == "test")
    trading_evolver = TradingAgentEvolver(
        baseline_scorer=scorer_proxy,
        store_factory=trading_store_factory,
        conservation_provider=conservation_provider,
        regime_break_provider=lambda: regime_monitor.is_regime_break,
        variant_store=variant_store,
    )
    trading_evolver.register_variants(get_trading_variants())
    app.state.trading_evolver = trading_evolver
    app.state.evolver = trading_evolver

    def record_trading_outcome(decision: dict[str, Any], success: bool) -> None:
        trading_evolver.record_verified_outcome(
            decision.get("variant_id") or decision.get("selected_variant_id"),
            success,
            category=decision.get("category"),
        )

    def select_trading_variant(category: str) -> str | None:
        active = trading_evolver.active_variant()
        if active and active.get("variant_id"):
            return str(active["variant_id"])
        for variant in trading_evolver.registered_variants:
            if str(variant.get("status") or "active") == "active":
                return str(variant.get("variant_id") or variant.get("id"))
        return None

    def _run_startup_seed_once() -> None:
        with startup_lock(scoring_db):
            _run_startup_locked()

    def _run_startup_locked() -> None:
        if not startup_state["seeded"]:
            startup_state["seeded"] = True
            if os.environ.get("DEMO_NO_RESEED") == "1":
                print("DEMO_NO_RESEED=1: skipping bundle restore and fixture seeding")
            elif active_graph_store is not None:
                print(f"[{DOMAIN}] auto-seed skipped while active AGE is enabled")
            else:
                if isinstance(_bundle_path, Path):
                    _restore_demo_bundle(seed_graph_store, _bundle_path, domain=DOMAIN)
                _auto_seed_if_needed(seed_graph_store, profile=resolved_profile)
            claim_registry.refresh_from_store(selected_graph_store_factory(scoring_db))
        if not startup_state["restored"]:
            startup_state["restored"] = True
            status = restore_l5_runtime_state(
                domain=DOMAIN,
                scorer=scorer_proxy._scorer(),
                learning_store=scorer_proxy.graph_store,
                welford_tracker=dk_welford_tracker,
            )
            status.pop("welford_tracker", None)
            replayed = regime_monitor.restore(scorer_proxy.graph_store.get_all_decisions(DOMAIN))
            status["regime_source"] = "persisted_decision_tags"
            status["regime_decisions_replayed"] = replayed
            app.state.l5_startup_status = status

    app.state.trading_active_graph_config = active_graph_config
    app.state.trading_selected_graph_store = scorer_proxy.graph_store
    app.state.graph_store = scorer_proxy.graph_store
    app.state.domain = DOMAIN
    app.state.trading_regime_monitor = regime_monitor
    app.state.trading_regime_conditioning = regime_scorer_proxy
    app.state.trading_tab_state_cache = tab_state_cache
    app.state.l5_startup_status = l5_startup_status
    app.state.entity_cache = entity_cache
    app.state.entity_context_cache = entity_context_cache

    app.state.materializer = create_trading_materializer(
        scorer_proxy, trading_store_factory, regime_monitor,
    )
    app.middleware("http")(create_invalidation_header_middleware(DOMAIN))
    app.include_router(
        create_scoring_router(
            DOMAIN,
            db_path=scoring_db,
            scorer_factory=lambda: scorer_proxy,
            dk_welford_tracker=dk_welford_tracker,
            outcome_recorder=record_trading_outcome,
            variant_selector=select_trading_variant,
            entity_context_cache=entity_context_cache,
            query_cache_invalidator=lambda: _invalidate_materializer(app),
        ),
        prefix="/api",
    )
    app.include_router(
        create_counterfactual_router(
            DOMAIN,
            prefix="/api/trading/score",
            scorer_provider=lambda: scorer_proxy,
        )
    )
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(create_self_transfer_router(scorer_proxy))
    app.include_router(create_archetype_router())
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            evolver_factory=lambda: trading_evolver,
            variant_provider=get_trading_variants,
        )
    )
    app.include_router(
        create_trading_evolution_router(
            evolver=trading_evolver,
            graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            regime_break_provider=lambda: regime_monitor.is_regime_break,
            include_persisted_rejections=True,
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
    app.include_router(
        create_switching_cost_router(scorer_proxy, domain=DOMAIN),
        prefix="/api",
    )
    app.include_router(
        create_platform_router(scorer_proxy, current_domain=DOMAIN),
        prefix="/api",
    )
    app.include_router(
        create_cross_signal_router(GraphSignalStore(app.state.graph_store, DOMAIN)), prefix="/api"
    )
    app.include_router(create_concepts_router())
    app.include_router(create_entrant_comparison_router(lambda: scorer_proxy))
    app.include_router(
        create_investigation_router(
            scorer_provider=lambda: scorer_proxy._scorer(),
            evidence_provider_factory=lambda decision_id: create_evidence_provider(
                trading_store_factory(),
                decision_id,
            ),
            **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", len(FACTOR_NAMES)),
            **_vld_classifier_router_kwargs(),
            factor_names=INVESTIGATION_CONFIG["factor_names"],
            default_budget=2,
            # Literal set retained for the existing VLD validation sweep.
            gated_sources={
                "correlation_engine",
                "portfolio_engine",
                "SYNTHETIC:fixture:correlation_engine",
                "SYNTHETIC:fixture:portfolio_engine",
                "SYNTHETIC:PLACEHOLDER:Tier5D:correlation_engine",
                "SYNTHETIC:PLACEHOLDER:Tier5D:portfolio_engine",
            },
        )
    )
    mount_self_computation_router(
        app,
        selected_graph_store_factory(scoring_db),
        domain=DOMAIN,
        scorer_provider=lambda: scorer_proxy,
        evolver_provider=lambda: app.state.evolver,
    )
    app.include_router(context_router, prefix="/api/context")
    app.include_router(create_evidence_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_journal_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_claim_gate_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))

    @app.post("/api/trading/journal/query")
    def query_journal(payload: dict[str, Any]) -> dict[str, Any]:
        question = str(payload.get("question") or "")
        trades = _journal_records(lambda: selected_graph_store_factory(scoring_db), DOMAIN)
        return cast(dict[str, Any], JournalQueryService().query(question, trades))

    @app.get("/api/trading/score/counterfactual/default")
    @cached_static("counterfactual-default")
    def default_counterfactual(request: Request) -> dict[str, Any]:
        return cast(dict[str, Any], compute_counterfactual_default(scorer_proxy))

    @app.get("/api/trading/correlation/config")
    @cached_static("correlation-config")
    def correlation_config(request: Request) -> dict[str, int]:
        return {"window": 20}

    @app.get("/api/trading/iks")
    def trading_iks(request: Request) -> dict[str, float]:
        compute_iks = getattr(scorer_proxy, "_compute_iks", None)
        if callable(compute_iks):
            return {"iks": float(compute_iks())}
        return {"iks": 0.0}

    app.include_router(create_analytics_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_correlation_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_execution_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(
        create_pre_score_router(
            scorer_proxy,
            lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
        )
    )
    app.include_router(create_prescore_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(
        create_promotion_engine_router(
            lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            promotion_guard=trading_promotion_guard,
        )
    )
    app.include_router(
        create_promotion_router(
            lambda: selected_graph_store_factory(scoring_db),
            config_dir=_promotion_config_dir(scoring_db),
            domain=DOMAIN,
        )
    )
    app.include_router(
        create_regime_router(
            lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            regime_break_provider=lambda: regime_monitor.is_regime_break,
        )
    )
    app.include_router(create_regime_classifier_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_regime_analytics_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_regime_status_router(regime_monitor))
    app.include_router(
        create_regime_beats_router(
            lambda: selected_graph_store_factory(scoring_db),
            domain=DOMAIN,
            regime_monitor=regime_monitor,
        )
    )
    app.include_router(create_situation_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_social_router(scorer_proxy))
    app.include_router(create_vix_timing_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_volatility_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(create_volatility_beats_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
    app.include_router(
        create_cohort_status_router(
            graph_store_factory=lambda: selected_graph_store_factory(scoring_db)
        )
    )
    app.include_router(create_webhook_router(scorer_proxy))
    app.include_router(create_broker_router(), prefix="/api/broker", tags=["broker"])
    app.include_router(data_import_router)
    app.include_router(trading_graph_status_router)
    app.include_router(create_tab_state_router(tab_state_cache))
    app.include_router(create_traversal_router())

    @app.on_event("startup")
    async def auto_seed_on_startup() -> None:
        _run_startup_seed_once()
        await asyncio.to_thread(app.state.materializer.refresh)
        asyncio.create_task(_materializer_refresh_loop(app))

    @app.middleware("http")
    async def direct_testclient_autoseed(request, call_next):
        return await call_next(request)

    # The shared scoring router also exposes /health under the /api prefix.
    # Keep one canonical graph-health handler per public alias.
    app.router.routes[:] = [
        route for route in app.router.routes
        if not (getattr(route, "path", None) == "/api/health"
                and "GET" in (getattr(route, "methods", None) or set()))
    ]

    @app.get("/health")
    @app.get("/api/health")
    def health(request: Request) -> Any:
        payload = build_graph_health(app.state.trading_selected_graph_store, app.state.trading_active_graph_config, DOMAIN)
        if request.url.path == "/api/health":
            payload.update(
                phase=None, alpha=None,
                engine={"scoring": "copilot_sdk.scoring.CompoundingScorer",
                        "gae": "gae.profile_scorer.ProfileScorer"},
            )
            if payload["graph_connected"]:
                try:
                    payload.update(phase=scorer_proxy.get_phase(), alpha=scorer_proxy.get_alpha())
                except GRAPH_CONNECTION_ERRORS:
                    logger.exception("Trading health scoring read failed")
                    payload.update(build_graph_health(None, app.state.trading_active_graph_config, DOMAIN))
                    payload.update(phase=None, alpha=None, engine={
                        "scoring": "copilot_sdk.scoring.CompoundingScorer",
                        "gae": "gae.profile_scorer.ProfileScorer",
                    })
        cache_stats = entity_cache.stats()
        payload.update(
            cache_hits=cache_stats.hits,
            cache_misses=cache_stats.misses,
            cache_size=cache_stats.size,
        )
        return JSONResponse(payload, status_code=health_status_code(payload))

    @app.get("/api/self/clone-fingerprint")
    def clone_fingerprint() -> dict[str, Any]:
        # Run the scorer's canonical fingerprint calculation on an isolated
        # empty store. Do not construct a CompoundingScorer here: its startup
        # drains the domain's persistence outbox, which belongs to the live app.
        store = InMemoryGraphStore(domain=DOMAIN)
        try:
            fingerprint = compute_fingerprint(store.get_verified_decisions(DOMAIN), list(TradingPreset().shape.factor_names))
            return {**jsonable_encoder(fingerprint),
                    "instance_kind": "disposable_clean_clone", "persistent": False}
        finally:
            store.close()

    @app.get("/api/trading/fingerprint")
    def trading_fingerprint() -> dict[str, Any]:
        fingerprint = scorer_proxy.fingerprint()
        factors = [
            {
                "name": str(getattr(factor, "name", "")),
                "weight": float(getattr(factor, "weight", 0.0)),
            }
            for factor in getattr(fingerprint, "factors", [])
        ]
        dominant = max(factors, key=lambda item: float(cast(Any, item["weight"])), default=None)
        return {
            "domain": DOMAIN,
            "factors": factors,
            "dominant_factor": dominant["name"] if dominant else None,
            "provenance": "learned",
        }

    # Register CORS last so it is the outermost middleware. This preserves
    # CORS headers even when an endpoint raises an unhandled error, preventing
    # browser clients from misreporting the response as a cross-origin failure.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Invalidated-Urls"],
    )

    return app


app = create_app()
