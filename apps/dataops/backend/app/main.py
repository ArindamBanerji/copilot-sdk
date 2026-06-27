"""FastAPI entrypoint for the DataOps Copilot backend."""

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
CI_PLATFORM_PATH = WORKSPACE_ROOT / "ci-platform"

for path in (BACKEND_ROOT, REPO_ROOT, GAE_PATH, CI_PLATFORM_PATH):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

from . import context_router as context_router_module  # noqa: E402
from .ae_router import create_ae_router  # noqa: E402
from .evolution import get_dataops_variants  # noqa: E402
from .graph_status import (  # noqa: E402
    DataOpsActiveGraphConfig,
    create_dataops_active_graph_store,
    router as dataops_graph_status_router,
)
from .graph_queries import DataOpsGraphClient  # noqa: E402
from .routers.cohort_status_router import create_cohort_status_router  # noqa: E402
from .routers.dataops_status import router as dataops_status_router  # noqa: E402
from .routers.query import create_query_router  # noqa: E402
from copilot_sdk.backend.transfer_router import create_transfer_router  # noqa: E402
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_di_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.connectors.mock_airflow import MockAirflowConnector  # noqa: E402
from copilot_sdk.connectors.mock_dbt import MockDBTConnector  # noqa: E402
from copilot_sdk.connectors.mock_snowflake import MockSnowflakeConnector  # noqa: E402
from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
from copilot_sdk.di import BaseSourceProfiler, IntelligenceMapBuilder  # noqa: E402
from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402


DOMAIN = "dataops"
DB_FILENAME = "dataops.db"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB_PATH = DATA_DIR / DB_FILENAME
SEED_FIXTURE_PATH = REPO_ROOT / "copilot_sdk" / "scoring" / "presets" / "dataops_seed.json"
FACTOR_NAMES = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)
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
    store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="DOPS-")
    store.penalty_ratio = 10.0
    return store


def _dataops_profiler_registry() -> dict[str, BaseSourceProfiler]:
    return {
        "airflow": BaseSourceProfiler(MockAirflowConnector()),
        "dbt": BaseSourceProfiler(MockDBTConnector()),
        "snowflake": BaseSourceProfiler(MockSnowflakeConnector()),
    }


def _dataops_intelligence_map_sources(profiler_registry: dict[str, BaseSourceProfiler]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for source_name in sorted(profiler_registry):
        connector = profiler_registry[source_name].connector
        to_map_nodes = getattr(connector, "to_map_nodes", None)
        if callable(to_map_nodes):
            sources.extend(to_map_nodes())
    return sources


def _dataops_profile_entity_ids(source_name: str) -> list[str]:
    if source_name == "dbt":
        return ["latest"]
    return ["all"]


def _profile_dataops_sources(profiler_registry: dict[str, BaseSourceProfiler]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for source_name, profiler in profiler_registry.items():
        try:
            profiles[source_name] = profiler.profile(_dataops_profile_entity_ids(source_name)).to_dict()
        except Exception:
            continue
    return profiles


def _dataops_profile_summaries(
    profiler_registry: dict[str, BaseSourceProfiler],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    sources = []
    for source_name in sorted(profiler_registry):
        profiler = profiler_registry[source_name]
        connector = profiler.connector
        profile = profiles.get(source_name)
        sources.append(
            {
                "source_name": str(getattr(connector, "source_name", source_name)),
                "entity_type": str(getattr(connector, "entity_type", "")),
                "trust_tier": int(getattr(connector, "trust_tier", 3)),
                "has_profile": profile is not None,
                "cache_status": "fresh" if profile is not None else "not_profiled",
                "age_seconds": 0.0 if profile is not None else None,
                "is_stale": False,
                "latest_profile": profile,
            }
        )
    return {"sources": sources, "total": len(sources)}


def _selected_graph_store_factory(
    db_path: str | Path,
    *,
    active_config: DataOpsActiveGraphConfig,
    active_store_factory: Any | None = None,
):
    active_store = create_dataops_active_graph_store(
        active_config,
        store_factory=active_store_factory,
    )
    if active_store is not None:
        return active_store
    return _graph_store(db_path)


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
        if isinstance(nested_factors, dict) and factor in nested_factors:
            value = nested_factors.get(factor)
        else:
            value = entry.get(factor)
        factors[factor] = _coerce_factor(value)
    return factors


def _seed_metadata(entry: dict[str, Any], sequence: int, scored_factors: dict[str, float]) -> dict[str, Any]:
    metadata = {key: value for key, value in entry.items() if key != "factors"}
    source_factors = entry.get("factors")
    if isinstance(source_factors, dict):
        metadata["seed_factors"] = dict(source_factors)
    metadata.update({
        "seed_domain": DOMAIN,
        "seed_index": sequence,
        "seed_id": entry.get("alert_id")
        or entry.get("event_id")
        or entry.get("dataset")
        or str(sequence),
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
                            "seed_id": entry.get("alert_id")
                            or entry.get("event_id")
                            or entry.get("dataset")
                            or str(sequence),
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


def _seed_demo_evolution_events_if_needed(graph_store: SQLiteGraphStore) -> None:
    try:
        existing = graph_store.get_evolution_events(domain=DOMAIN, rule_name="resource_quality_scheduling_signal", limit=1)
    except Exception as exc:
        print(f"[{DOMAIN}] demo evolution seed check failed: {exc}")
        return
    if existing:
        return
    try:
        graph_store.save_evolution_event(
            domain=DOMAIN,
            event_type="shadow_started",
            rule_name="resource_quality_scheduling_signal",
            variant_id="dataops-off-peak-scheduling-v1",
            metadata={
                "id": "V-DO-SCHED-001",
                "artifact_type": "scheduling_rule",
                "description": "Schedule resource-intensive quality checks during off-peak windows.",
                "impact": "quality_scheduling",
                "magnitude": 0.17,
                "timestamp": "2026-05-08T11:15:00Z",
                "system": "celonis_transform",
                "trigger": "resource contention during quality validation",
                "recommendation": "Move data quality checks to off-peak scheduling windows when resource pressure is high.",
                "expected_impact": "Reduce resource contention while preserving data quality checks.",
                "source_copilot": "S2P",
                "source_rule": "s2p_invoice_quality_scheduling_signal",
                "match": {
                    "categories": ["quality_anomaly", "transform_drift"],
                    "min_downstream_urgency": 0.4,
                },
            },
        )
    except Exception as exc:
        print(f"[{DOMAIN}] demo evolution seed failed: {exc}")


def _variant_from_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    variant = dict(metadata)
    event_type = str(variant.get("event_type") or event.get("event_type") or "")
    rule_name = str(event.get("rule_name") or variant.get("rule_name") or "")
    variant_id = str(
        event.get("variant_id")
        or variant.get("variant_id")
        or variant.get("variantId")
        or rule_name
    )
    variant["event_type"] = event_type
    variant.setdefault("rule_name", rule_name)
    variant.setdefault("variant_id", variant_id)
    variant.setdefault("id", variant_id or rule_name)
    variant.setdefault("description", rule_name or variant_id)
    variant.setdefault("timestamp", event.get("timestamp"))
    return variant


def _evolution_variants(store: Any) -> list[dict[str, Any]]:
    try:
        events = store.get_evolution_events(domain=DOMAIN, limit=500)
    except Exception:
        return []
    return [_variant_from_event(event) for event in events if isinstance(event, dict)]


def _dataops_variants_with_config(store: Any) -> list[dict[str, Any]]:
    configured = get_dataops_variants()
    persisted = _evolution_variants(store)
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for variant in configured + persisted:
        variant_id = variant.get("id") or variant.get("variant_id")
        if variant_id:
            normalized_id = str(variant_id)
            if normalized_id in seen:
                continue
            seen.add(normalized_id)
        merged.append(dict(variant))
    return merged


def create_app(
    db_path: str | Path | None = None,
    demo_bundle_path: str | Path | bool | None = None,
    active_store_factory: Any | None = None,
) -> FastAPI:
    app = FastAPI(title="DataOps Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = _resolve_scoring_db(db_path)
    if demo_bundle_path is None:
        _bundle_path = REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"
    elif demo_bundle_path is False:
        _bundle_path = False
    else:
        _bundle_path = Path(demo_bundle_path)
    active_config = DataOpsActiveGraphConfig.from_env()
    selected_graph_store = _selected_graph_store_factory(
        scoring_db,
        active_config=active_config,
        active_store_factory=active_store_factory,
    )
    graph_store_factory = lambda _db_path=scoring_db: selected_graph_store
    seed_graph_store = selected_graph_store
    startup_state = {"seeded": False, "restored": False}
    app.state.dataops_active_graph_config = active_config
    app.state.dataops_selected_graph_store = selected_graph_store
    app.state.graph_store = selected_graph_store
    dataops_profiler_registry = _dataops_profiler_registry()
    app.state.dataops_profiler_registry = dataops_profiler_registry
    dataops_profiles = _profile_dataops_sources(dataops_profiler_registry)
    app.state.dataops_profiles = dataops_profiles
    scorer_proxy = FreshScorerProxy(DOMAIN, scoring_db, graph_store_factory)
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
            if scoring_db != ":memory:":
                if _bundle_path is not False:
                    _restore_demo_bundle(seed_graph_store, _bundle_path, domain=DOMAIN)
                _auto_seed_if_needed(seed_graph_store)
                _seed_demo_evolution_events_if_needed(seed_graph_store)
        if not startup_state["restored"]:
            startup_state["restored"] = True
            status = restore_l5_runtime_state(
                domain=DOMAIN,
                scorer=scorer_proxy._scorer(),
                learning_store=selected_graph_store,
                welford_tracker=dk_welford_tracker,
            )
            status.pop("welford_tracker", None)
            app.state.l5_startup_status = status

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
        create_conservation_router(
            DOMAIN,
            state_provider=scorer_proxy,
        ),
        prefix="/api",
    )
    @app.get("/api/di/profiles")
    def dataops_profiles_response() -> dict[str, Any]:
        return _dataops_profile_summaries(dataops_profiler_registry, dataops_profiles)

    @app.get("/api/dataops/di/profiles")
    def dataops_prefixed_profiles_response() -> dict[str, Any]:
        return dataops_profiles_response()

    app.include_router(create_di_router(dataops_profiler_registry), prefix="/api")
    app.include_router(create_di_router(dataops_profiler_registry), prefix="/api/dataops")
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: selected_graph_store,
            domain=DOMAIN,
            variant_provider=lambda: _dataops_variants_with_config(selected_graph_store),
        )
    )
    mount_self_computation_router(app, selected_graph_store)
    context_router_module.set_evolution_store_factory(lambda: selected_graph_store)
    app.include_router(context_router_module.router, prefix="/api/context")
    app.include_router(
        create_ae_router(
            evolution_store_factory=lambda: selected_graph_store,
            domain=DOMAIN,
        ),
        prefix="/api/ae",
    )
    app.include_router(dataops_graph_status_router)
    app.include_router(dataops_status_router)
    app.include_router(create_query_router(lambda: selected_graph_store))
    app.include_router(
        create_cohort_status_router(graph_store_factory=lambda: selected_graph_store)
    )

    @app.get("/api/di/intelligence-map")
    def dataops_intelligence_map() -> dict[str, Any]:
        sources = _dataops_intelligence_map_sources(dataops_profiler_registry)
        return IntelligenceMapBuilder().build(sources=sources).to_dict()

    @app.get("/api/dataops/di/intelligence-map")
    def dataops_prefixed_intelligence_map() -> dict[str, Any]:
        return dataops_intelligence_map()

    @app.on_event("startup")
    async def auto_seed_on_startup() -> None:
        _run_startup_seed_once()

    @app.middleware("http")
    async def direct_testclient_autoseed(request, call_next):
        if request.url.path == "/api/health":
            _run_startup_seed_once()
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, Any]:
        graph = DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")
        return {
            "status": "ok",
            "domain": DOMAIN,
            "graph_connected": graph.is_graph_connected,
            "graph_source": graph.graph_source,
            "engine": (
                "copilot_sdk.scoring + gae.profile_scorer + gae.calibration + "
                "gae.evolution + ci_platform.graph"
            ),
        }

    return app


app = create_app()
