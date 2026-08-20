"""FastAPI entrypoint for the DataOps Copilot backend."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import warnings
from dataclasses import replace
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
from .evolution import (  # noqa: E402
    get_dataops_variant_specs,
    get_dataops_variants,
)
from .enterprise_router import router as enterprise_router  # noqa: E402
from .graph_status import (  # noqa: E402
    DataOpsActiveGraphConfig,
    create_dataops_active_graph_store,
    router as dataops_graph_status_router,
)
from .graph_queries import DataOpsGraphClient  # noqa: E402
from .routers.cohort_status_router import create_cohort_status_router  # noqa: E402
from .routers.dataops_status import router as dataops_status_router  # noqa: E402
from .routers.query import create_query_router  # noqa: E402
from .routers.di_enrichment_router import create_dataops_di_enrichment_router  # noqa: E402
from .routers.perturbation_router import create_perturbation_router  # noqa: E402
from .routers.trust_router import create_trust_router  # noqa: E402
from .routers.di_gateway_router import create_di_gateway_router  # noqa: E402
from .routers.regime_router import create_regime_router  # noqa: E402
from .dataops_governance import DataOpsGovernance  # noqa: E402
from .routers.governance_router import create_governance_router  # noqa: E402
from copilot_sdk.backend.transfer_router import (  # noqa: E402
    create_self_transfer_router,
    create_transfer_router,
)
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_di_router,
    create_evolution_router,
    create_scoring_router,
    mount_self_computation_router,
)
from copilot_sdk.backend.discovery_router import create_discovery_router  # noqa: E402
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.evolution import PromptVariantEvolver, ScorerBackedProvider, SQLiteVariantStore  # noqa: E402
from .evolution.evolver_config import DATAOPS_EVOLVER_CONFIG  # noqa: E402
from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph  # noqa: E402
from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
from copilot_sdk.di import (  # noqa: E402
    AcquisitionAdvisor,
    BaseSourceProfiler,
    ClaudeQueryParser,
    DataOpsEnterpriseProvider,
    DIQueryService,
    IntelligenceMapBuilder,
)
from copilot_sdk.di.intelligence_map import enrich_payload_with_suggestions  # noqa: E402
from copilot_sdk.di.perturbation import PerturbationService  # noqa: E402
from copilot_sdk.di.catalog import ExternalDataCatalog  # noqa: E402
from copilot_sdk.di.search_service import DISearchService  # noqa: E402
from copilot_sdk.graph.factory import create_graph_store  # noqa: E402
from copilot_sdk.graph.protocol import GraphStore  # noqa: E402
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402
from ci_platform.copilot_core import EntityCache, EntityContextCacheAdapter  # noqa: E402


DOMAIN = "dataops"

DATAOPS_QUERY_SOURCE_ID_MAP = {
    "compounding_scorer": "snowflake",
    "dataops_active_age_score": "airflow",
    "migration": "dbt",
}
logger = logging.getLogger(__name__)


def _resolve_profile() -> str:
    """Select an explicit isolated profile for pytest app construction."""
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        return "test"
    if os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1":
        return "development"
    return "production"


def _is_demo_or_test_mode() -> bool:
    return os.environ.get("DATAOPS_DEMO_MODE") == "1" or _resolve_profile() == "test"


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


def _graph_store(db_path: str | Path):
    # Active AGE configuration is owned by DATAOPS_ACTIVE_*; generic AGE
    # settings remain deliberately ignored by the graph-status contract.
    profile = _resolve_profile()
    graph_config = None
    try:
        graph_config = GraphConfig.load(DOMAIN, profile=profile)
        backend = graph_config.backend
    except GraphConfigError:
        if profile != "test":
            raise
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
        decision_id_prefix="DOPS-",
        dsn=graph_config.dsn if graph_config is not None else None,
        graph_name=graph_config.graph if graph_config is not None else None,
        test_mode=graph_config.active_test_mode if graph_config is not None else False,
        profile=profile,
    )
    setattr(store, "penalty_ratio", 10.0)
    return store


def _snowflake_connector():
    if os.environ.get("SNOWFLAKE_ACCOUNT"):
        try:
            import snowflake.connector  # type: ignore[import-not-found]  # noqa: F401
            from copilot_sdk.connectors.snowflake_meta import SnowflakeMetaConnector

            if not all((os.environ.get("SNOWFLAKE_ACCOUNT"), os.environ.get("SNOWFLAKE_USER"), os.environ.get("SNOWFLAKE_PASSWORD"))):
                raise ValueError("Incomplete Snowflake credentials")
            return SnowflakeMetaConnector(
                account=os.environ["SNOWFLAKE_ACCOUNT"],
                user=os.environ.get("SNOWFLAKE_USER", ""),
                password=os.environ.get("SNOWFLAKE_PASSWORD", ""),
                database=os.environ.get("SNOWFLAKE_DATABASE", ""),
                warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", ""),
                schema=os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
            )
        except ImportError:
            warnings.warn("SNOWFLAKE_ACCOUNT set but client library not installed. Using mock.")
        except Exception as exc:
            warnings.warn(f"Snowflake connector failed to initialize: {exc}. Using mock.")
    from copilot_sdk.connectors.mock_snowflake import MockSnowflakeConnector

    return MockSnowflakeConnector()


def _dbt_connector():
    if os.environ.get("DBT_API_TOKEN"):
        try:
            from copilot_sdk.connectors.dbt_connector import DBTConnector

            if not os.environ.get("DBT_ACCOUNT_ID") and not os.environ.get("DBT_ARTIFACTS_PATH"):
                raise ValueError("Incomplete dbt configuration")
            return DBTConnector(
                api_token=os.environ["DBT_API_TOKEN"],
                account_id=os.environ.get("DBT_ACCOUNT_ID", ""),
                artifacts_path=os.environ.get("DBT_ARTIFACTS_PATH"),
            )
        except ImportError:
            warnings.warn("DBT_API_TOKEN set but client library not installed. Using mock.")
        except Exception as exc:
            warnings.warn(f"dbt connector failed to initialize: {exc}. Using mock.")
    from copilot_sdk.connectors.mock_dbt import MockDBTConnector

    return MockDBTConnector()


def _airflow_connector():
    if os.environ.get("AIRFLOW_BASE_URL"):
        try:
            from copilot_sdk.connectors.airflow_connector import AirflowConnector

            if not (os.environ.get("AIRFLOW_USER") or os.environ.get("AIRFLOW_TOKEN")):
                raise ValueError("Incomplete Airflow credentials")
            return AirflowConnector(
                base_url=os.environ["AIRFLOW_BASE_URL"],
                username=os.environ.get("AIRFLOW_USER", ""),
                password=os.environ.get("AIRFLOW_PASSWORD", ""),
                token=os.environ.get("AIRFLOW_TOKEN", ""),
            )
        except ImportError:
            warnings.warn("AIRFLOW_BASE_URL set but client library not installed. Using mock.")
        except Exception as exc:
            warnings.warn(f"Airflow connector failed to initialize: {exc}. Using mock.")
    from copilot_sdk.connectors.mock_airflow import MockAirflowConnector

    return MockAirflowConnector()


def _dataops_profiler_registry() -> dict[str, BaseSourceProfiler]:
    return {
        "airflow": BaseSourceProfiler(_airflow_connector()),
        "dbt": BaseSourceProfiler(_dbt_connector()),
        "snowflake": BaseSourceProfiler(_snowflake_connector()),
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
            profile = profiler.profile(_dataops_profile_entity_ids(source_name)).to_dict()
            profile.setdefault("source_name", source_name)
            profile["trust_tier"] = int(getattr(profiler.connector, "trust_tier", 3))
            profiles[source_name] = profile
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


def _dataops_acquisition_recommendations() -> dict[str, Any]:
    advisor = AcquisitionAdvisor(external_catalog=ExternalDataCatalog())
    payload = advisor.recommend(
        "dataops",
        current_sources=["snowflake", "dbt", "airflow"],
        decisions_per_year=12000,
    )
    recommendations = advisor.free_first(list(payload.get("recommendations", [])))
    for recommendation in recommendations:
        recommendation["provenance"] = "demo"
    monetization = advisor.discover_monetization(12000, ["dataops"])
    monetization["provenance"] = "demo"
    return {
        **payload,
        "recommendations": recommendations,
        "monetization": monetization,
        "provenance": "demo",
    }


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
        "domain": DOMAIN,
        "provenance": "sample",
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


def _auto_seed_if_needed(graph_store: GraphStore) -> int:
    try:
        count = int(graph_store.count_decisions(DOMAIN))
    except Exception as exc:
        logger.warning("[%s] auto-seed count failed", DOMAIN, exc_info=True)
        raise RuntimeError(f"[{DOMAIN}] auto-seed count failed") from exc
    if count > 0:
        print(f"[{DOMAIN}] resuming with {count} persisted decisions")
        return 0
    scorer = CompoundingScorer.from_preset(
        DOMAIN,
        graph_store=graph_store,
        evolve=True,
        consolidation_enabled=True,
        profile=_resolve_profile(),
    )
    seeded = _seed_from_fixtures(scorer, graph_store)
    print(
        f"[{DOMAIN}] auto-seeded {seeded['decisions_seeded']} decisions "
        f"and {seeded['outcomes_seeded']} outcomes"
    )
    return seeded["decisions_seeded"]


def _seed_demo_evolution_events_if_needed(graph_store: GraphStore) -> None:
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
    except Exception as exc:
        raise RuntimeError(f"[{DOMAIN}] evolution graph read failed") from exc
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
    # Stable pipeline/system metadata only; mutable decisions and conservation
    # authority remain graph-backed and are intentionally excluded.
    entity_cache = EntityCache(
        max_size=200,
        ttl_seconds=300,
        source="dataops.entity_context_cache",
    )
    entity_context_cache = EntityContextCacheAdapter(entity_cache, enabled=True)
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
    di_query_profiles = {
        **dataops_profiles,
        "sap_s4hana": {
            "source_name": "SAP S/4HANA",
            "trust": 0.99,
            "trust_tier": 1,
            "freshness_hours": 2.0,
        },
        "celonis_p2p": {
            "source_name": "Celonis P2P",
            "trust": 0.87,
            "trust_tier": 2,
            "freshness_hours": 2.0,
        },
    }
    di_query_provider = DataOpsEnterpriseProvider(
        selected_graph_store,
        invoice_path=DATA_DIR / "sap_supplier_invoices.json",
        source_profiles=di_query_profiles,
    )
    di_query_service = DIQueryService(
        di_query_provider,
        allowed_domains={DOMAIN},
        source_id_map=DATAOPS_QUERY_SOURCE_ID_MAP,
        claude_parser=ClaudeQueryParser() if os.environ.get("ANTHROPIC_API_KEY") else None,
    )
    app.state.di_query_service = di_query_service
    scorer_proxy = FreshScorerProxy(
        DOMAIN, scoring_db, graph_store_factory, profile=_resolve_profile()
    )

    conservation_provider = ScorerBackedProvider(scorer_proxy, DOMAIN)
    governance_db = ":memory:" if scoring_db == ":memory:" else str(DATA_DIR / "dataops_governance.sqlite3")
    app.state.dataops_governance = DataOpsGovernance(
        governance_db, selected_graph_store, scorer_proxy, conservation_provider
    )
    evolver_config = replace(
        DATAOPS_EVOLVER_CONFIG,
        conservation_state_provider=conservation_provider,
    )
    evolution_db = ":memory:" if scoring_db == ":memory:" else str(Path(scoring_db).with_name(f"{DOMAIN}_evolution.sqlite3"))
    evolver = PromptVariantEvolver(config=evolver_config, store=SQLiteVariantStore(evolution_db))
    evolver.register_variants(get_dataops_variant_specs())
    app.state.evolver = evolver

    def record_dataops_outcome(decision: dict[str, Any], success: bool) -> None:
        variant_id = decision.get("variant_id") or decision.get("selected_variant_id")
        if not variant_id:
            return
        try:
            evolver.record_outcome(
                str(variant_id),
                bool(success),
                category=decision.get("category"),
            )
        except (KeyError, ValueError):
            return

    def select_dataops_variant(category: str) -> str | None:
        selected = evolver.get_variant(category=category)
        return str(selected.id) if selected is not None else None
    perturbation_service = PerturbationService()
    app.state.di_perturbation_service = perturbation_service
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
            if os.environ.get("DEMO_NO_RESEED") == "1":
                print("DEMO_NO_RESEED=1: skipping bundle restore and fixture seeding")
            elif _is_demo_or_test_mode() and scoring_db != ":memory:":
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
    app.state.entity_cache = entity_cache
    app.state.entity_context_cache = entity_context_cache
    app.include_router(
        create_scoring_router(
            DOMAIN,
            db_path=scoring_db,
            scorer_factory=lambda: scorer_proxy,
            dk_welford_tracker=dk_welford_tracker,
            outcome_recorder=record_dataops_outcome,
            variant_selector=select_dataops_variant,
            query_cache_invalidator=di_query_service.invalidate_cache,
            entity_context_cache=entity_context_cache,
        ),
        prefix="/api",
    )
    app.include_router(
        create_trust_router(
            DOMAIN,
            scorer_provider=lambda: scorer_proxy,
            perturbation_provider=lambda: perturbation_service,
        ),
        prefix="/api",
    )
    app.include_router(
        create_di_gateway_router(
            scorer_provider=lambda: scorer_proxy,
            graph_store_provider=lambda: selected_graph_store,
        ),
        prefix="/api/di",
    )
    app.include_router(create_governance_router(app.state.dataops_governance))
    app.include_router(create_regime_router(lambda: scorer_proxy))
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(create_self_transfer_router(scorer_proxy))
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

    @app.get("/api/dataops/di/acquisitions")
    def dataops_acquisitions_response() -> dict[str, Any]:
        return _dataops_acquisition_recommendations()

    dataops_map_builder = IntelligenceMapBuilder()
    dataops_catalog = ExternalDataCatalog()
    dataops_map_builder.enrich_from_connectors(
        [profiler.connector for profiler in dataops_profiler_registry.values()]
    )
    app.state.dataops_map_builder = dataops_map_builder
    app.state.dataops_intelligence_map_cache = None
    app.state.dataops_intelligence_map_cached_at = 0.0
    app.include_router(
        create_di_router(
            dataops_profiler_registry,
            map_builder=dataops_map_builder,
            map_sources=_dataops_intelligence_map_sources(dataops_profiler_registry),
            advisor=AcquisitionAdvisor(external_catalog=dataops_catalog),
            catalog=dataops_catalog,
            query_service=di_query_service,
            search_service=DISearchService(
                [profiler.connector for profiler in dataops_profiler_registry.values()],
                dataops_profiler_registry,
            ),
        ),
        prefix="/api",
    )
    app.include_router(
        create_di_router(
            dataops_profiler_registry,
            advisor=AcquisitionAdvisor(external_catalog=dataops_catalog),
            catalog=dataops_catalog,
            query_service=di_query_service,
            search_service=DISearchService(
                [profiler.connector for profiler in dataops_profiler_registry.values()],
                dataops_profiler_registry,
            ),
        ),
        prefix="/api/dataops",
    )
    app.include_router(
        create_dataops_di_enrichment_router(scorer_provider=lambda: scorer_proxy),
        prefix="/api/di",
    )
    # ENT-1 uses the shared advisory discovery contract.  DataOps has no
    # multi-domain decision engine of its own, so the router's explicit demo
    # fallback is used until cross-copilot decision rows are available.
    app.include_router(create_discovery_router(object()))
    app.include_router(
        create_perturbation_router(
            scorer_provider=lambda: scorer_proxy,
            service=perturbation_service,
        ),
        prefix="/api/di",
    )
    app.include_router(
        create_evolution_router(
            graph_store_factory=lambda: selected_graph_store,
            domain=DOMAIN,
            evolver_factory=lambda: app.state.evolver,
            variant_provider=lambda: _dataops_variants_with_config(selected_graph_store),
        )
    )
    mount_self_computation_router(
        app,
        selected_graph_store,
        domain=DOMAIN,
        scorer_provider=lambda: scorer_proxy,
        evolver_provider=lambda: app.state.evolver,
    )
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
    app.include_router(enterprise_router, prefix="/api/dataops")
    app.include_router(
        create_query_router(lambda: selected_graph_store, query_service=di_query_service)
    )
    app.include_router(
        create_cohort_status_router(graph_store_factory=lambda: selected_graph_store)
    )

    @app.get("/api/di/intelligence-map")
    def dataops_intelligence_map() -> dict[str, Any]:
        now = time.time()
        cached = app.state.dataops_intelligence_map_cache
        if cached is not None and now - app.state.dataops_intelligence_map_cached_at < 300:
            return cached
        sources = _dataops_intelligence_map_sources(dataops_profiler_registry)
        payload = dataops_map_builder.build(sources=sources).to_dict()
        if not payload.get("gold_lines"):
            enrich_payload_with_suggestions(
                payload,
                _dataops_acquisition_recommendations().get("recommendations", []),
            )
        app.state.dataops_intelligence_map_cache = payload
        app.state.dataops_intelligence_map_cached_at = now
        return payload

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

    @app.middleware("http")
    async def evidence_headers_and_abstention(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith(("/api/dataops", "/api/context", "/api/ae", "/api/di", "/api/score")):
            response.headers.setdefault("X-Evidence-Tier", "synthetic")
            response.headers.setdefault("X-Evidence-Label", "synthetic / modelled - not measured")
        if path == "/api/score" and response.status_code < 400:
            body = b"".join([chunk async for chunk in response.body_iterator])
            try:
                payload = json.loads(body.decode("utf-8"))
                if isinstance(payload, dict):
                    payload["abstention_warning"] = app.state.dataops_governance.abstention("unknown")
                    from starlette.responses import JSONResponse
                    return JSONResponse(payload, status_code=response.status_code, headers=dict(response.headers))
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                pass
        return response

    @app.get("/health")
    def health() -> dict[str, Any]:
        graph = DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")
        graph_source = graph.graph_source
        cache_stats = entity_cache.stats()
        return {
            "status": "ok" if graph_source == "graph" else "error",
            "domain": DOMAIN,
            "graph_connected": graph.is_graph_connected,
            "graph_source": graph_source,
            "engine": (
                "copilot_sdk.scoring + gae.profile_scorer + gae.calibration + "
                "gae.evolution + ci_platform.graph"
            ),
            "cache_hits": cache_stats.hits,
            "cache_misses": cache_stats.misses,
            "cache_size": cache_stats.size,
        }

    return app


app = create_app()
