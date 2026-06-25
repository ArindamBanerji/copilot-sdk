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

from . import context_router as context_router_module  # noqa: E402
from .graph_status import (  # noqa: E402
    create_purchasing_active_graph_store,
    initialize_purchasing_active_graph_config,
    router as purchasing_graph_status_router,
)
from .evolution import get_purchasing_variants  # noqa: E402
from .connectors.commodity_source import FREDCommoditySource  # noqa: E402
from .routers.auto_order_router import create_auto_order_router  # noqa: E402
from .routers.chain_router import create_chain_router, reset_chain_state  # noqa: E402
from .routers.cohort_status_router import create_cohort_status_router  # noqa: E402
from .routers.commodity_router import create_commodity_router  # noqa: E402
from .routers.delivery_router import create_delivery_router  # noqa: E402
from .routers.evidence import create_evidence_router  # noqa: E402
from .routers.event_router import create_event_router, reset_event_state  # noqa: E402
from .routers.iks import create_iks_router  # noqa: E402
from .routers.match import create_match_router  # noqa: E402
from .routers.menu_router import create_menu_router  # noqa: E402
from .routers.pos_router import create_pos_router  # noqa: E402
from .routers.qbo_router import create_qbo_router  # noqa: E402
from .routers.par_router import create_par_router  # noqa: E402
from .routers.queue import create_queue_router  # noqa: E402
from .routers.scorecard_router import build_iks_summary, create_scorecard_router  # noqa: E402
from .routers.spend_router import create_spend_router  # noqa: E402
from .routers.trust import create_trust_router  # noqa: E402
from .routers.trust_router import create_trust_router as create_trust_weights_router  # noqa: E402
from .routers.verify_router import create_verify_router  # noqa: E402
from .services.auto_order import AutoOrderGate  # noqa: E402
from .services.waste_tracker import WasteTracker  # noqa: E402
from .connectors.commodity_provider import CommodityDataProvider  # noqa: E402
from copilot_sdk.backend.report_router import create_report_router  # noqa: E402
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
from copilot_sdk.reporting.weekly import (  # noqa: E402
    WeeklyReportGenerator,
    purchasing_cost_extractor,
)
from copilot_sdk.scoring.dk_persistence import DKWelfordTracker  # noqa: E402
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset  # noqa: E402
from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state  # noqa: E402


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
    variants = [_variant_from_event(event) for event in events if isinstance(event, dict)]
    return _filter_variants_by_query(variants, None)


def _purchasing_variants_with_config(store: Any) -> list[dict[str, Any]]:
    configured = get_purchasing_variants()
    persisted = _evolution_variants(store)
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
) -> FastAPI:
    app = FastAPI(title="Purchasing Copilot", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    scoring_db = _resolve_scoring_db(db_path)
    active_graph_config = initialize_purchasing_active_graph_config()
    active_graph_store = create_purchasing_active_graph_store(
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

    app.state.purchasing_active_graph_config = active_graph_config
    app.state.purchasing_selected_graph_store = scorer_proxy.graph_store
    app.state.l5_startup_status = l5_startup_status
    auto_order_gate = AutoOrderGate()

    @app.get("/api/health")
    def api_health() -> dict[str, Any]:
        iks = build_iks_summary(lambda: selected_graph_store_factory(scoring_db))
        return {
            "phase": scorer_proxy.get_phase(),
            "alpha": scorer_proxy.get_alpha(),
            "engine": {
                "scoring": "copilot_sdk.scoring.CompoundingScorer",
                "gae": "gae.profile_scorer.ProfileScorer",
            },
            "iks_score": iks["iks_score"],
            "iks_available": iks["available"],
            "iks_verified_count": iks["verified_count"],
        }

    def _load_order_rows() -> list[dict[str, Any]]:
        path = DATA_DIR / "purchasing_orders.json"
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return payload if isinstance(payload, list) else []

    @app.get("/api/purchasing/waste/analysis")
    def waste_analysis() -> list[dict[str, Any]]:
        tracker = WasteTracker(_load_order_rows())
        return [profile.to_dict() for profile in tracker.analyze_all()]

    @app.get("/api/purchasing/waste/summary")
    def waste_summary() -> dict[str, Any]:
        tracker = WasteTracker(_load_order_rows())
        return tracker.weekly_waste_cost()

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
        ),
        prefix="/api",
    )
    mount_self_computation_router(app, selected_graph_store_factory(scoring_db))
    context_router_module.set_evolution_store_factory(lambda: selected_graph_store_factory(scoring_db))
    app.include_router(context_router_module.router, prefix="/api/context")
    app.include_router(create_evidence_router(scorer_proxy))
    app.include_router(create_iks_router(lambda: selected_graph_store_factory(scoring_db)))
    app.include_router(create_match_router(lambda: selected_graph_store_factory(scoring_db)))
    app.include_router(create_auto_order_router(auto_order_gate, scorer_proxy))
    app.include_router(create_chain_router())
    app.include_router(create_delivery_router())
    app.include_router(create_event_router())
    app.include_router(create_pos_router())
    app.include_router(create_qbo_router())
    app.include_router(create_scorecard_router(lambda: selected_graph_store_factory(scoring_db)))
    fred_key = os.environ.get("FRED_API_KEY", "")
    commodity_source = FREDCommoditySource(api_key=fred_key) if fred_key else None
    commodity_provider = CommodityDataProvider(source=commodity_source)
    app.include_router(create_spend_router(commodity_provider=commodity_provider))
    app.include_router(create_commodity_router(provider=commodity_provider))
    app.include_router(create_menu_router())
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
            ),
            prefix="/api/purchasing",
        )
    )

    @app.on_event("startup")
    async def auto_seed_on_startup() -> None:
        _run_startup_seed_once()
        reset_chain_state(app.state)
        reset_event_state(app.state)

    @app.middleware("http")
    async def direct_testclient_autoseed(request, call_next):
        if request.url.path == "/api/health":
            _run_startup_seed_once()
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, Any]:
        iks = build_iks_summary(lambda: selected_graph_store_factory(scoring_db))
        return {
            "status": "ok",
            "domain": DOMAIN,
            "engine": "copilot_sdk.scoring + gae.profile_scorer + gae.evolution",
            "iks_score": iks["iks_score"],
            "iks_available": iks["available"],
            "iks_verified_count": iks["verified_count"],
        }

    @app.post("/api/purchasing/demo/reset")
    def reset_demo_state() -> dict[str, Any]:
        reset_chain_state(app.state)
        reset_event_state(app.state)
        return {"reset": True, "state": ["chain", "events"]}

    return app


app = create_app()
