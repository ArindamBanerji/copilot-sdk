"""FastAPI entrypoint for the Purchasing Copilot backend."""

from __future__ import annotations

import json
import asyncio
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Request, Response
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
from .dashboard_router import router as dashboard_router  # noqa: E402
from .inventory_router import router as inventory_router  # noqa: E402
from .graph_status import (  # noqa: E402
    build_purchasing_graph_status,
    create_purchasing_active_graph_store,
    initialize_purchasing_active_graph_config,
    router as purchasing_graph_status_router,
)
from .evolution import (  # noqa: E402
    get_purchasing_variant_specs,
    get_purchasing_variants,
)
from .routers.auto_order_router import create_auto_order_router  # noqa: E402
from .routers.alert_router import create_alert_router  # noqa: E402
from .routers.chain_router import create_chain_router, reset_chain_state  # noqa: E402
from .routers.cohort_status_router import create_cohort_status_router  # noqa: E402
from .routers.commodity_router import create_commodity_router  # noqa: E402
from .routers.delivery_router import create_delivery_router  # noqa: E402
from .routers.discovery_router import create_discovery_router  # noqa: E402
from .routers.economic_router import create_economic_router  # noqa: E402
from .routers.evidence import create_evidence_router  # noqa: E402
from .routers.learning_beats import create_learning_beats_router  # noqa: E402
from .routers.event_router import create_event_router, reset_event_state  # noqa: E402
from .routers.iks import create_iks_router  # noqa: E402
from .routers.match import create_match_router  # noqa: E402
from .routers.menu_router import create_menu_router  # noqa: E402
from .routers.multi_unit_router import create_multi_unit_router  # noqa: E402
from .routers.pos_router import create_pos_router  # noqa: E402
from .routers.qbo_router import create_qbo_router  # noqa: E402
from .routers.par_router import create_par_router  # noqa: E402
from .routers.queue import create_queue_router  # noqa: E402
from .routers.scorecard_router import build_iks_summary, create_scorecard_router  # noqa: E402
from .routers.signal_router import create_signal_router  # noqa: E402
from .routers.spend_router import create_spend_router  # noqa: E402
from .routers.trust import create_trust_router  # noqa: E402
from .routers.trust_router import create_trust_router as create_trust_weights_router  # noqa: E402
from .routers.verify_router import create_verify_router  # noqa: E402
from .routers.purchasing_control import create_purchasing_control_router  # noqa: E402
from .routers.regime_router import create_regime_router  # noqa: E402
from .services.auto_order import AutoOrderGate  # noqa: E402
from .services.audit_export import AuditExportService  # noqa: E402
from .services.chain_demo_seed import ChainLearningDemo  # noqa: E402
from .services.disruption_recovery import DisruptionRecoveryService  # noqa: E402
from .services.par_optimizer import ParLevelOptimizer  # noqa: E402
from .services.payment_timing import PaymentTimingService  # noqa: E402
from .services.waste_tracker import WasteTracker  # noqa: E402
from .services.predictive_par import PredictivePar  # noqa: E402
from .services.purchasing_control import PurchasingClaimRegistry, PurchasingControlService, PurchasingEvidenceMiddleware  # noqa: E402
from .connectors.commodity_provider import CommodityDataProvider  # noqa: E402
from .investigation_config import INVESTIGATION_CONFIG, create_evidence_provider  # noqa: E402
from .vld_preseed import seed_vld_purchasing_showcase  # noqa: E402
from copilot_sdk.backend.investigation_router import create_investigation_router  # noqa: E402
from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS
from copilot_sdk.backend.health_builder import build_graph_health, health_status_code  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from copilot_sdk.backend.report_router import create_report_router  # noqa: E402
from copilot_sdk.backend.transfer_router import (  # noqa: E402
    create_self_transfer_router,
    create_transfer_router,
)
from copilot_sdk.backend import (  # noqa: E402
    create_conservation_router,
    create_evolution_router,
    create_scoring_router,
    create_switching_cost_router,
    mount_self_computation_router,
)
from copilot_sdk.outbox import OutboxStore  # noqa: E402
from copilot_sdk.evolution import PromptVariantEvolver, ScorerBackedProvider, create_variant_store  # noqa: E402
from .evolution.evolver_config import PURCHASING_EVOLVER_CONFIG  # noqa: E402
from copilot_sdk.backend.conservation_router import build_conservation_status  # noqa: E402
from copilot_sdk.backend.response_materializer import ResponseMaterializer  # noqa: E402
from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
from copilot_sdk.backend.platform_router import create_platform_router  # noqa: E402
from copilot_sdk.backend.cross_signal_router import create_cross_signal_router  # noqa: E402
from copilot_sdk.backend.signal_store import GraphSignalStore  # noqa: E402
from copilot_sdk.backend.modeled_projection import modeled_projection  # noqa: E402
from copilot_sdk.backend.concepts_router import create_concepts_router  # noqa: E402
from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph, resolve_profile  # noqa: E402
from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
from copilot_sdk.graph.factory import create_graph_store  # noqa: E402
from copilot_sdk.graph.protocol import GraphStore  # noqa: E402
from copilot_sdk.tenant_middleware import TenantMiddleware  # noqa: E402
from copilot_sdk.reporting.weekly import (  # noqa: E402
    WeeklyReportGenerator,
    purchasing_cost_extractor,
)
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.composite_gate import CompositeGate  # noqa: E402
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer  # noqa: E402
from copilot_sdk.scoring.investigation import KUtilityStore  # noqa: E402
from copilot_sdk.scoring.situation_classifier import SituationClassifier  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402
from copilot_sdk.demo.startup import startup_lock  # noqa: E402
from copilot_sdk.transfer.chain_transfer import ChainTransfer  # noqa: E402
from ci_platform.copilot_core import EntityCache, EntityContextCacheAdapter  # noqa: E402


DOMAIN = "purchasing"


def _resolve_profile() -> str:
    """Select the graph profile from explicit configuration."""
    from copilot_sdk.config import resolve_profile

    return str(resolve_profile(domain="purchasing"))


def _demo_mode() -> bool:
    configured = os.environ.get("DEMO_MODE", os.environ.get("PURCHASING_DEMO_MODE"))
    if configured is not None:
        return configured.strip().lower() in {"1", "true", "yes", "on"}
    if os.environ.get("PURCHASING_SAMPLE_DATA", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return False
DB_FILENAME = "purchasing.db"


class _VLDKDecisionConnection:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path, check_same_thread=False)


def _create_vld_k_store(path: Path, dimensions: int) -> KUtilityStore:
    return KUtilityStore(_VLDKDecisionConnection(path), dimensions)


def _vld_k_router_kwargs(path: Path, dimensions: int) -> dict[str, KUtilityStore]:
    return {"k_store": _create_vld_k_store(path, dimensions)}


async def _materializer_refresh_loop(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(5)
        materializer = getattr(app.state, "materializer", None)
        refresh = getattr(materializer, "refresh", None)
        if callable(refresh):
            try:
                await asyncio.to_thread(refresh)
            except Exception:
                logger.exception("Purchasing materializer background refresh failed")


def _invalidate_materializer(app: FastAPI) -> None:
    materializer = getattr(app.state, "materializer", None)
    if materializer is not None:
        materializer.invalidate()


def _accuracy_by_category_payload(verified: list[dict[str, Any]], threshold: float = 0.70) -> dict[str, Any]:
    grouped: dict[str, dict[str, int]] = {}
    for decision in verified:
        category = str(decision.get("category") or "uncategorized")
        bucket = grouped.setdefault(category, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if decision.get("is_correct") is True:
            bucket["correct"] += 1
    categories = []
    for category in sorted(grouped):
        total = grouped[category]["total"]
        correct = grouped[category]["correct"]
        accuracy = round(correct / total, 4) if total else 0.0
        categories.append({
            "category": category,
            "accuracy": accuracy,
            "total": total,
            "correct": correct,
            "alert": accuracy < threshold,
        })
    return {"categories": categories, "threshold": threshold, "overall_verified": len(verified)}
OUTBOX_DB_FILENAME = "purchasing_outbox.db"
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


@dataclass(frozen=True)
class PurchasingPathConfig:
    """Typed local-path configuration; it never selects the graph backend."""

    scoring_db: str

    @classmethod
    def from_environment(cls, db_path: str | Path | None) -> "PurchasingPathConfig":
        if db_path is not None:
            resolved: str | Path = db_path
        elif os.environ.get("CI_DATA_DIR"):
            resolved = Path(os.environ["CI_DATA_DIR"]) / DB_FILENAME
        else:
            resolved = DEFAULT_DB_PATH

        if str(resolved) != ":memory:":
            Path(resolved).parent.mkdir(parents=True, exist_ok=True)
        return cls(scoring_db=str(resolved))
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


def _graph_store(db_path: str | Path, *, backend: str | None = None, profile: str | None = None):
    # Active AGE configuration is owned by PURCHASING_ACTIVE_*; generic AGE
    # settings remain deliberately ignored by the graph-status contract.
    profile = profile or _resolve_profile()
    graph_config = None
    if backend is None:
        try:
            graph_config = GraphConfig.load(DOMAIN, profile=profile)
            backend = graph_config.backend
        except GraphConfigError:
            if profile != "test":
                raise
            backend = "sqlite"
    backend = backend.strip().lower()
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
        decision_id_prefix="PUR-",
        dsn=graph_config.dsn if graph_config is not None else None,
        graph_name=graph_config.graph if graph_config is not None else None,
        test_mode=graph_config.active_test_mode if graph_config is not None else False,
        profile=profile,
    )
    setattr(store, "penalty_ratio", 3.0)
    return store


def _fred_commodity_source() -> Any | None:
    if os.environ.get("FRED_API_KEY"):
        try:
            from .connectors.commodity_source import FREDCommoditySource

            return FREDCommoditySource(api_key=os.environ["FRED_API_KEY"])
        except ImportError:
            logger.info("CONNECTOR: FRED = DEMO (client library unavailable)")
        except Exception as exc:
            logger.info("CONNECTOR: FRED = DEMO (initialization unavailable: %s)", exc)
    logger.info("CONNECTOR: FRED = DEMO (no credentials; sample provider retained)")
    return None


def _resolve_scoring_db(db_path: str | Path | None) -> str:
    return PurchasingPathConfig.from_environment(db_path).scoring_db


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


def _seed_from_fixtures(scorer: CompoundingScorer, graph_store: GraphStore) -> dict[str, int]:
    try:
        entries = json.loads(SEED_FIXTURE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[{DOMAIN}] auto-seed fixture unavailable: {exc}")
        return {"total": 0, "decisions_seeded": 0, "outcomes_seeded": 0, "failed": 0}
    if not isinstance(entries, list):
        print(f"[{DOMAIN}] auto-seed fixture is not a list")
        return {"total": 0, "decisions_seeded": 0, "outcomes_seeded": 0, "failed": 0}

    decisions_seeded = 0
    outcomes_seeded = 0
    failed = 0
    for sequence, entry in enumerate(entries):
        if not isinstance(entry, dict):
            failed += 1
            continue
        category = entry.get("category")
        if not category:
            failed += 1
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
                            "seed_id": entry.get("order_id") or entry.get("item") or str(sequence),
                            "source_seed_index": sequence,
                        },
                    },
                )
                outcomes_seeded += 1
        except Exception as exc:
            failed += 1
            print(f"[{DOMAIN}] auto-seed skipped entry {sequence}: {exc}")
    if entries and decisions_seeded == 0:
        print(f"[{DOMAIN}] warning: auto-seed wrote no decisions")
    expected_outcomes = sum(1 for entry in entries if isinstance(entry, dict) and "is_correct" in entry)
    if expected_outcomes > 0 and outcomes_seeded == 0:
        print(f"[{DOMAIN}] warning: auto-seed wrote no fixture outcomes")
    return {
        "total": len(entries),
        "decisions_seeded": decisions_seeded,
        "outcomes_seeded": outcomes_seeded,
        "failed": failed,
    }


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
    total = int(seeded.get("total", seeded["decisions_seeded"] + seeded.get("failed", 0)))
    failed = int(seeded.get("failed", 0))
    print(
        f"[{DOMAIN}] Seeded {seeded['decisions_seeded']} of {total} "
        f"decisions ({failed} failed); outcomes seeded: {seeded['outcomes_seeded']}"
    )
    if total and failed / total > 0.5:
        logger.warning("[%s] auto-seed failure rate is high: %d of %d entries failed", DOMAIN, failed, total)
    return seeded["decisions_seeded"]


def _alert_conservation_status_payload(
    materializer: Any, scorer_proxy: Any, override: Any = None
) -> dict[str, Any]:
    if override is not None:
        return override if isinstance(override, dict) else {"state": str(override)}
    try:
        payload = materializer.get("conservation")
        if not isinstance(payload, dict):
            payload = build_conservation_status(DOMAIN, scorer_proxy)
    except Exception as exc:
        logger.warning("Purchasing alert conservation read unavailable: %s", exc)
        return {"state": "conservation_unavailable", "status": "UNAVAILABLE", "category": "all"}
    status = payload.get("status") or payload.get("state")
    if not status:
        logger.warning("Purchasing alert conservation payload had no status")
        return {"state": "conservation_unavailable", "status": "UNAVAILABLE", "category": "all"}
    return {"state": str(status), "category": "all"}


def _variant_from_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata")
    variant = dict(metadata) if isinstance(metadata, dict) else {}
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


def _evolution_variants(store: Any) -> list[dict[str, Any]] | None:
    if store is None:
        return []
    try:
        events = store.get_evolution_events(domain=DOMAIN, limit=500)
    except Exception:
        return None
    variants = [_variant_from_event(event) for event in events if isinstance(event, dict)]
    return _filter_variants_by_query(variants, None)


def _purchasing_variants_with_config(store: Any) -> list[dict[str, Any]] | None:
    configured = get_purchasing_variants()
    persisted = _evolution_variants(store)
    if persisted is None:
        return None
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for variant in configured + persisted:
        variant_id = variant.get("id") or variant.get("variant_id")
        if variant_id:
            variant_key = str(variant_id)
            if variant_key in seen:
                continue
            seen.add(variant_key)
        merged.append(dict(variant))
    return merged


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


def create_app(
    db_path: str | Path | None = None,
    demo_bundle_path: str | Path | bool | None = None,
    active_store_factory: Any | None = None,
    profile: str | None = None,
) -> FastAPI:
    resolved_profile = _resolve_profile() if profile is None else profile.strip().lower()
    app = FastAPI(title="Purchasing Copilot", version="0.1.0")
    app.add_middleware(TenantMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    purchasing_claim_registry = PurchasingClaimRegistry()
    app.add_middleware(
        PurchasingEvidenceMiddleware,
        registry=purchasing_claim_registry,
        context=os.environ.get("PURCHASING_EVIDENCE_CONTEXT", "demo"),
    )

    scoring_db = _resolve_scoring_db(db_path)
    # Stable supplier/item context only; mutable decisions and conservation
    # authority remain graph-backed and are intentionally excluded.
    entity_cache = EntityCache(
        max_size=200,
        ttl_seconds=300,
        source="purchasing.entity_context_cache",
    )
    entity_context_cache = EntityContextCacheAdapter(entity_cache, enabled=True)
    outbox_store = OutboxStore(DATA_DIR / OUTBOX_DB_FILENAME)
    active_graph_config = initialize_purchasing_active_graph_config()
    active_graph_store = create_purchasing_active_graph_store(
        active_graph_config,
        store_factory=active_store_factory,
    )

    def selected_graph_store_factory(path: str | Path):
        if active_graph_store is not None:
            return active_graph_store
        return _graph_store(path, backend=active_graph_config.requested_backend, profile=resolved_profile)

    _bundle_path: Path | bool
    if demo_bundle_path is None:
        _bundle_path = REPO_ROOT / "demo" / f"{DOMAIN}_demo_bundle.json"
    elif demo_bundle_path is False:
        _bundle_path = False
    else:
        _bundle_path = Path(cast(str | Path, demo_bundle_path))
    # Active AGE owns the selected store; no separate generic factory call is
    # needed for startup seeding (seeding is skipped while AGE is active).
    seed_graph_store = (
        active_graph_store
        if active_graph_store is not None
        else _graph_store(scoring_db, backend=active_graph_config.requested_backend, profile=resolved_profile)
    )
    startup_state = {"seeded": False, "restored": False}
    raw_scorer_proxy = FreshScorerProxy(
        DOMAIN, scoring_db, selected_graph_store_factory, profile=resolved_profile
    )
    scorer_proxy: Any = GateEnforcedScorer(raw_scorer_proxy, CompositeGate())
    purchasing_control = PurchasingControlService(
        lambda: selected_graph_store_factory(scoring_db),
        lambda: scorer_proxy,
        DATA_DIR,
    )
    app.state.purchasing_claim_registry = purchasing_claim_registry
    app.state.purchasing_control = purchasing_control

    conservation_provider = ScorerBackedProvider(scorer_proxy, DOMAIN)
    evolver_config = replace(
        PURCHASING_EVOLVER_CONFIG,
        conservation_state_provider=conservation_provider,
    )
    evolver = PromptVariantEvolver(config=evolver_config, store=create_variant_store(active_graph_store or seed_graph_store, DOMAIN, test_mode=resolved_profile == "test"))
    evolver.register_variants(get_purchasing_variant_specs())
    app.state.evolver = evolver

    def record_purchasing_outcome(decision: dict[str, Any], success: bool) -> None:
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
            # A legacy decision may predate the registered variant inventory.
            # Learning remains authoritative; stale evolution metadata is ignored.
            return

    def select_purchasing_variant(category: str) -> str | None:
        selected = evolver.get_variant(category=category)
        return str(selected.id) if selected is not None else None
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
        purchasing_claim_registry.refresh(selected_graph_store_factory(scoring_db))

    app.state.purchasing_active_graph_config = active_graph_config
    app.state.purchasing_selected_graph_store = scorer_proxy.graph_store
    app.state.graph_store = scorer_proxy.graph_store
    app.state.purchasing_vld_showcase = seed_vld_purchasing_showcase()
    app.state.outbox_store = outbox_store
    app.state.l5_startup_status = l5_startup_status
    app.state.entity_cache = entity_cache
    app.state.entity_context_cache = entity_context_cache
    auto_order_gate = AutoOrderGate()

    app.state.materializer = ResponseMaterializer(
        domain=DOMAIN,
        store_provider=lambda: selected_graph_store_factory(scoring_db),
        computations={
            "order_rows": lambda s: list(cast(list[dict[str, Any]], s["decisions"])),
            "waste_analysis": lambda s: [
                profile.to_dict()
                for profile in WasteTracker(cast(list[dict[str, Any]], s["decisions"])).analyze_all()
            ],
            "waste_summary": lambda s: WasteTracker(cast(list[dict[str, Any]], s["decisions"])).weekly_waste_cost(),
            "conservation": lambda s: build_conservation_status(
                DOMAIN,
                scorer_proxy,
                lambda count: modeled_projection(
                    selected_graph_store_factory(scoring_db).get_governance(DOMAIN, "demo:roi_projection"),
                    count,
                ),
            ),
            "accuracy_by_category": lambda s: _accuracy_by_category_payload(cast(list[dict[str, Any]], s["verified"])),
        },
        ttl=5.0,
    )

    @app.get("/api/health")
    def api_health() -> Any:
        payload = build_graph_health(app.state.purchasing_selected_graph_store, app.state.purchasing_active_graph_config, DOMAIN)
        phase, alpha = None, None
        if payload["graph_connected"]:
            try:
                phase, alpha = scorer_proxy.get_phase(), scorer_proxy.get_alpha()
            except GRAPH_CONNECTION_ERRORS:
                logger.exception("Purchasing health scoring read failed")
                payload = build_graph_health(None, app.state.purchasing_active_graph_config, DOMAIN)
        cache_stats = entity_cache.stats()
        payload.update(
            phase=phase,
            alpha=alpha,
            engine={
                "scoring": "copilot_sdk.scoring.CompoundingScorer",
                "gae": "gae.profile_scorer.ProfileScorer",
            },
            cache_hits=cache_stats.hits,
            cache_misses=cache_stats.misses,
            cache_size=cache_stats.size,
        )
        return JSONResponse(payload, status_code=health_status_code(payload))

    def _graph_order_rows() -> list[dict[str, Any]]:
        materialized = app.state.materializer.get("order_rows")
        if isinstance(materialized, list):
            return cast(list[dict[str, Any]], materialized)
        return list(app.state.purchasing_selected_graph_store.get_all_decisions(domain=DOMAIN))

    def _graph_par_items() -> list[dict[str, Any]]:
        decisions = _graph_order_rows()
        grouped: dict[tuple[str, str], int] = {}
        for decision in decisions:
            category = str(decision.get("category") or "unknown")
            raw_metadata = decision.get("metadata")
            metadata: dict[str, Any] = cast(dict[str, Any], raw_metadata) if isinstance(raw_metadata, dict) else {}
            item = str(metadata.get("item") or decision.get("item") or category)
            grouped[(item, category)] = grouped.get((item, category), 0) + 1
        return [
            {"item": item, "category": category, "base_par": max(1, count)}
            for (item, category), count in grouped.items()
        ]

    def _par_optimizer() -> Any:
        return getattr(app.state, "purchasing_par_optimizer", None) or ParLevelOptimizer()

    def _conservation_status(category: str | None = None) -> str:
        override = getattr(app.state, "purchasing_conservation_status", None)
        if isinstance(override, dict):
            state = override.get(str(category)) or override.get("state") or override.get("default")
            return str(state or "UNKNOWN").upper()
        if override:
            return str(override).upper()
        try:
            payload = app.state.materializer.get("conservation")
            if not isinstance(payload, dict):
                payload = build_conservation_status(DOMAIN, scorer_proxy)
        except Exception:
            return "UNKNOWN"
        return str(payload.get("status") or payload.get("state") or "UNKNOWN").upper()

    def _alert_conservation_status() -> dict[str, Any]:
        override = getattr(app.state, "purchasing_alert_conservation_status", None)
        return _alert_conservation_status_payload(app.state.materializer, scorer_proxy, override)

    @app.get("/api/purchasing/waste/analysis")
    def waste_analysis(request: Request) -> list[dict[str, Any]]:
        materialized = request.app.state.materializer.get("waste_analysis")
        if isinstance(materialized, list):
            return cast(list[dict[str, Any]], materialized)
        decisions = _graph_order_rows()
        tracker = WasteTracker(decisions)
        return [profile.to_dict() for profile in tracker.analyze_all()]

    @app.get("/api/purchasing/waste/summary")
    def waste_summary(request: Request) -> dict[str, Any]:
        materialized = request.app.state.materializer.get("waste_summary")
        if isinstance(materialized, dict):
            return cast(dict[str, Any], materialized)
        tracker = WasteTracker(_graph_order_rows())
        return cast(dict[str, Any], tracker.weekly_waste_cost())

    @app.get("/api/purchasing/par/predict")
    def predictive_par(request: Request, item: str = "salmon", category: str = "protein", date: str = "2026-06-26") -> dict[str, Any]:
        service = PredictivePar(optimizer=_par_optimizer())
        base, par_available = service.base_from_optimizer(item, category, request.app.state.graph_store.get_all_decisions(domain=DOMAIN))
        payload = service.predict(
            item,
            category,
            date,
            base_par=base,
            conservation_status=_conservation_status(category),
        ).to_dict()
        payload["par_available"] = par_available
        return cast(dict[str, Any], payload)

    @app.get("/api/purchasing/par/predict-week")
    def predictive_par_week(request: Request) -> dict[str, Any]:
        service = PredictivePar(optimizer=_par_optimizer())
        items = []
        for row in _graph_par_items():
            item = str(row.get("item") or "salmon")
            category = str(row.get("category") or "protein")
            with_base = dict(row)
            base_par, par_available = service.base_from_optimizer(item, category, request.app.state.graph_store.get_all_decisions(domain=DOMAIN))
            with_base["base_par"] = base_par
            with_base["par_available"] = par_available
            with_base["conservation_status"] = _conservation_status(category)
            items.append(with_base)
        return cast(dict[str, Any], service.predict_week(items))

    disruption_recovery_service = DisruptionRecoveryService()
    payment_timing_service = PaymentTimingService()
    audit_export_service = AuditExportService()
    chain_demo = ChainLearningDemo()

    @app.get("/api/purchasing/disruption/status")
    def disruption_status() -> dict[str, Any]:
        return cast(dict[str, Any], disruption_recovery_service.recovery_status())

    @app.get("/api/purchasing/disruption/history")
    def disruption_history() -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], disruption_recovery_service.recovery_history())

    @app.get("/api/purchasing/payment/timing")
    def payment_timing(supplier_id: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        return cast(dict[str, Any] | list[dict[str, Any]], payment_timing_service.analyze(supplier_id))

    @app.get("/api/purchasing/payment/summary")
    def payment_summary() -> dict[str, Any]:
        return cast(dict[str, Any], payment_timing_service.portfolio_summary())

    @app.get("/api/purchasing/audit/pack")
    def audit_pack(period: str = "last_quarter") -> dict[str, Any]:
        return cast(dict[str, Any], audit_export_service.generate_pack(period))

    @app.get("/api/purchasing/audit/export/json")
    def audit_export_json(period: str = "last_quarter") -> Response:
        return Response(audit_export_service.export_json(period), media_type="application/json")

    @app.get("/api/purchasing/audit/export/csv")
    def audit_export_csv(period: str = "last_quarter") -> Response:
        return Response(audit_export_service.export_csv_summary(period), media_type="text/csv")

    @app.post("/api/purchasing/demo/chain-seed")
    def chain_demo_seed() -> dict[str, Any]:
        if not _demo_mode():
            raise HTTPException(status_code=404, detail="Purchasing demo route is disabled")
        state = chain_demo.seed()
        app.state.purchasing_chain_demo = state
        return cast(dict[str, Any], chain_demo.seed_response(state))

    @app.post("/api/purchasing/chain/transfer")
    def chain_demo_transfer(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        if not _demo_mode():
            raise HTTPException(status_code=404, detail="Purchasing demo route is disabled")
        if "source_location" in payload or "target_locations" in payload:
            state = getattr(app.state, "purchasing_chain_demo", None)
            if not isinstance(state, dict):
                state = chain_demo.seed()
                app.state.purchasing_chain_demo = state
            try:
                return cast(dict[str, Any], chain_demo.transfer(
                    state,
                    source_location=str(payload.get("source_location") or "downtown"),
                    target_locations=[
                        str(target)
                        for target in payload.get("target_locations", ["airport", "suburb", "new"])
                    ],
                ))
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=f"Unknown location: {exc.args[0]}") from exc

        stores = getattr(request.app.state, "purchasing_chain_stores", None)
        if stores is None:
            reset_chain_state(request.app.state)
            stores = request.app.state.purchasing_chain_stores
        source_key = str(payload.get("source") or "chicago").strip().lower()
        target_key = str(payload.get("target") or "miami").strip().lower()
        if source_key not in stores:
            raise HTTPException(status_code=404, detail=f"Unknown source location: {payload.get('source')}")
        if target_key not in stores:
            raise HTTPException(status_code=404, detail=f"Unknown target location: {payload.get('target')}")
        dry_run = bool(payload.get("dry_run", payload.get("dryRun", True)))
        result = ChainTransfer().transfer(stores[source_key], stores[target_key], dry_run=dry_run)
        return {
            **result,
            "source_location": stores[source_key].location_id,
            "target_location": stores[target_key].location_id,
        }

    app.include_router(
        create_scoring_router(
            DOMAIN,
            db_path=scoring_db,
            scorer_factory=lambda: scorer_proxy,
            dk_welford_tracker=dk_welford_tracker,
            outcome_recorder=record_purchasing_outcome,
            variant_selector=select_purchasing_variant,
            entity_context_cache=entity_context_cache,
            query_cache_invalidator=lambda: _invalidate_materializer(app),
        ),
        prefix="/api",
    )
    app.include_router(create_transfer_router(scorer_proxy))
    app.include_router(create_self_transfer_router(scorer_proxy))
    app.include_router(
          create_evolution_router(
              graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
              domain=DOMAIN,
              evolver_factory=lambda: app.state.evolver,
              variant_provider=lambda: _purchasing_variants_with_config(
                  selected_graph_store_factory(scoring_db)
              ),
          )
      )

    # Conservation router
    app.include_router(
        create_conservation_router(
            DOMAIN,
            state_provider=scorer_proxy,
            projection_provider=lambda count: modeled_projection(
                selected_graph_store_factory(scoring_db).get_governance(DOMAIN, "demo:roi_projection"), count,
            ),
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
    mount_self_computation_router(
        app,
        selected_graph_store_factory(scoring_db),
        domain=DOMAIN,
        scorer_provider=lambda: scorer_proxy,
        evolver_provider=lambda: app.state.evolver,
    )
    context_router_module.set_evolution_store_factory(lambda: selected_graph_store_factory(scoring_db))
    app.include_router(context_router_module.router, prefix="/api/context")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(inventory_router, prefix="/api")
    app.include_router(create_evidence_router(scorer_proxy))
    app.include_router(
        create_investigation_router(
            scorer_provider=lambda: scorer_proxy._scorer(),
            evidence_provider_factory=lambda decision_id: create_evidence_provider(
                selected_graph_store_factory(scoring_db),
                decision_id,
                fixture_data=app.state.purchasing_vld_showcase,
            ),
            **_vld_k_router_kwargs(DATA_DIR / "k_utility.db", PurchasingPreset().shape.n_factors),
            classifier=SituationClassifier(),
            factor_names=INVESTIGATION_CONFIG["factor_names"],
            default_budget=2,
            # Literal set retained for the existing VLD validation sweep.
            gated_sources={
                "vendor_tracker",
                "lead_time_tracker",
                "SYNTHETIC:fixture:vendor_tracker",
                "SYNTHETIC:fixture:lead_time_tracker",
                "SYNTHETIC:PLACEHOLDER:Tier5D:vendor_tracker",
                "SYNTHETIC:PLACEHOLDER:Tier5D:lead_time_tracker",
            },
        )
    )
    app.include_router(create_learning_beats_router(scorer_proxy))
    app.include_router(create_iks_router(lambda: selected_graph_store_factory(scoring_db)))
    app.include_router(create_match_router(lambda: selected_graph_store_factory(scoring_db)))
    app.include_router(create_auto_order_router(auto_order_gate, scorer_proxy))
    app.include_router(
        create_alert_router(
            conservation_provider=_alert_conservation_status,
            outbox_store=outbox_store,
        )
    )
    if _demo_mode():
        app.include_router(create_chain_router())
    app.include_router(create_delivery_router())
    if _demo_mode():
        app.include_router(create_discovery_router())
    app.include_router(create_economic_router())
    app.include_router(create_event_router())
    app.include_router(create_pos_router())
    app.include_router(create_qbo_router())
    app.include_router(create_signal_router(outbox_store))
    app.include_router(create_scorecard_router(lambda: selected_graph_store_factory(scoring_db)))
    commodity_source = _fred_commodity_source()
    commodity_provider = CommodityDataProvider(source=commodity_source)
    commodity_provider.warm_cache()
    app.include_router(create_spend_router(commodity_provider=commodity_provider))
    app.include_router(create_commodity_router(provider=commodity_provider))
    app.include_router(create_menu_router())
    app.include_router(create_multi_unit_router())
    app.include_router(create_par_router())
    app.include_router(
        create_cohort_status_router(
            graph_store_factory=lambda: selected_graph_store_factory(scoring_db)
        )
    )
    app.include_router(
        create_queue_router(
            lambda: selected_graph_store_factory(scoring_db),
            lambda: scorer_proxy,
        )
    )
    app.include_router(create_verify_router(scorer_proxy))
    app.include_router(create_purchasing_control_router(purchasing_control, purchasing_claim_registry))
    app.include_router(create_regime_router(lambda: scorer_proxy))
    app.include_router(create_trust_router(scorer_proxy))
    app.include_router(create_trust_weights_router(lambda: scorer_proxy))
    app.include_router(purchasing_graph_status_router)
    app.include_router(
        create_report_router(
            "purchasing",
            report_factory=lambda: WeeklyReportGenerator(
                graph_store=selected_graph_store_factory(scoring_db),
                scorer=scorer_proxy,
                domain="purchasing",
                cost_extractor=purchasing_cost_extractor,
                preset=PurchasingPreset(),
                waste_provider=lambda: WasteTracker(_graph_order_rows()).weekly_waste_cost(),
            ),
            prefix="/api/purchasing",
        )
    )

    @app.on_event("startup")
    async def auto_seed_on_startup() -> None:
        _run_startup_seed_once()
        reset_chain_state(app.state)
        reset_event_state(app.state)
        await asyncio.to_thread(app.state.materializer.refresh)
        asyncio.create_task(_materializer_refresh_loop(app))

    @app.middleware("http")
    async def direct_testclient_autoseed(request, call_next):
        return await call_next(request)

    @app.get("/health")
    def health() -> Any:
        payload = build_graph_health(app.state.purchasing_selected_graph_store, app.state.purchasing_active_graph_config, DOMAIN)
        cache_stats = entity_cache.stats()
        payload.update(
            cache_hits=cache_stats.hits,
            cache_misses=cache_stats.misses,
            cache_size=cache_stats.size,
        )
        return JSONResponse(payload, status_code=health_status_code(payload))

    @app.get("/api/purchasing/fingerprint")
    def purchasing_fingerprint() -> dict[str, Any]:
        fingerprint = scorer_proxy.fingerprint()
        factors = [
            {
                "name": str(getattr(factor, "name", "")),
                "weight": float(getattr(factor, "weight", 0.0)),
            }
            for factor in getattr(fingerprint, "factors", [])
        ]
        dominant = max(factors, key=lambda item: cast(float, item["weight"]), default=None)
        return {
            "domain": DOMAIN,
            "factors": factors,
            "dominant_factor": dominant["name"] if dominant else None,
            "provenance": "learned",
        }

    @app.post("/api/purchasing/demo/reset")
    def reset_demo_state() -> dict[str, Any]:
        if not _demo_mode():
            raise HTTPException(status_code=404, detail="Purchasing demo route is disabled")
        reset_chain_state(app.state)
        reset_event_state(app.state)
        if hasattr(app.state, "outbox_store"):
            app.state.outbox_store.clear()
        app.state.purchasing_chain_demo = chain_demo.seed()
        return {"reset": True, "state": ["chain", "chain_demo", "events", "outbox"]}

    return app


app = create_app()
