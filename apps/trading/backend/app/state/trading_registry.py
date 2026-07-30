"""Trading materialized tab-state registry."""

from __future__ import annotations

from typing import Any, Callable

from app import context_router
from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.regime_vrp import compute_regime_vrp
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution
from app.routers.evolution_router import _load_persisted_rejection_summary
from app.routers.journal import _journal_records
from app.routers.regime_analytics import _read_decisions
from app.routers.webhook import compute_webhook_status
from app.services.cohort_status import CohortStatusService
from app.services.execution_analysis import ExecutionAnalyzer
from app.services.regime_analytics import RegimeAnalytics
from app.services.regime_monitor import RegimeMonitor
from app.services.trust_analysis import TrustAnalyzer
from app.state.compute_helpers import (
    compute_accuracy_summary,
    compute_all_decisions,
    compute_archetypes_summary,
    compute_counterfactual_default,
    compute_decisions_summary,
    compute_evolution_summary,
    compute_history_summary,
    compute_journal_analytics,
    compute_journal_trades_summary,
    compute_promotion_dashboard,
    compute_verified_decisions,
    json_safe,
    safe_call,
)
from app.state.key_manifest import TRADING_STATIC_KEYS, TradingKey
from app.state.schemas.trading import TRADING_SCHEMA_BY_KEY
from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.backend.transfer_router import _normalize_transfer_status
from copilot_sdk.scoring.measurement_state import compute_measurement_state
from copilot_sdk.state import TabStateCache, register_tab_state_cache


GraphStoreFactory = Callable[[], Any]
ScorerProvider = Callable[[], Any]

def create_trading_tab_state_cache(
    *,
    scorer_provider: ScorerProvider,
    graph_store_factory: GraphStoreFactory,
    regime_monitor: RegimeMonitor,
) -> TabStateCache:
    cache = TabStateCache("trading")

    def scorer() -> Any:
        return scorer_provider()

    def graph_store() -> Any:
        return graph_store_factory()

    def verified() -> list[dict[str, Any]]:
        return compute_verified_decisions(graph_store_factory)

    def centroid_history_summary() -> dict[str, Any]:
        store = graph_store()
        rows = store.get_centroid_checkpoints("trading", limit=50)
        return {"checkpoints": json_safe(list(rows)), "total": len(rows)}

    def audit_trail_summary() -> dict[str, Any]:
        rows = verified()[:20]
        return {"trails": json_safe(rows), "total": len(rows)}

    def measurement_state() -> dict[str, Any]:
        payload = compute_measurement_state(scorer()).to_dict()
        payload["engine"] = "copilot_sdk.scoring.CompoundingScorer"
        return payload

    def regime_status() -> dict[str, Any]:
        status = regime_monitor.status()
        restrictions = []
        if status.regime_break_active:
            restrictions = [f"theta_min tightened {regime_monitor.tightening_percent}%", "AE promotions deferred"]
        return {
            "current_regime": status.current_regime,
            "previous_regime": status.previous_regime,
            "regime_break_active": status.regime_break_active,
            "decisions_in_new_regime": status.decisions_in_new_regime,
            "decisions_to_stabilize": status.decisions_to_stabilize,
            "autonomy_level": "restricted" if status.regime_break_active else "normal",
            "restrictions": restrictions,
        }

    def regime_analytics() -> dict[str, Any]:
        return RegimeAnalytics().compute(_read_decisions(graph_store_factory, "trading"))

    def transfer_status() -> dict[str, Any]:
        info = getattr(scorer(), "_warm_start_info", None)
        return _normalize_transfer_status(info if isinstance(info, dict) else None)

    def trust_analysis() -> dict[str, Any]:
        trades = [row for row in (context_router._as_trade_dict(trade) for trade in list(context_router._trade_store_ref)) if row]
        result = TrustAnalyzer().analyze(scorer(), trades, category=None)
        factor_details = list(result["factors"])
        result["factor_details"] = factor_details
        result["factors"] = list(result["factor_names"])
        result["trust_scores"] = {factor["name"]: factor for factor in factor_details}
        return result

    def correlation() -> dict[str, Any]:
        from app.routers.correlation import _correlation_service

        return _correlation_service(20).compute(_journal_records(graph_store_factory, "trading"))

    def rejection_summary() -> dict[str, Any]:
        persisted = _load_persisted_rejection_summary()
        if isinstance(persisted, dict):
            return persisted
        return {
            "total_tested": 0,
            "total_promoted": 0,
            "total_rejected": 0,
            "rejection_breakdown": {},
            "rejected_variants": [],
            "provenance": "learned",
        }

    def execution() -> dict[str, Any]:
        return json_safe(ExecutionAnalyzer().analyze(_journal_records(graph_store_factory, "trading")))

    compute: dict[TradingKey, Callable[[], Any]] = {
        TradingKey.ANALYTICS: context_router.analytics,
        TradingKey.HISTORY_SUMMARY: lambda: compute_history_summary(graph_store_factory),
        TradingKey.TRADE_METADATA: context_router.get_trade_metadata,
        TradingKey.MARKET_SNAPSHOT: context_router.market_snapshot,
        TradingKey.TRANSFER_STATUS: transfer_status,
        TradingKey.ARCHETYPES: compute_archetypes_summary,
        TradingKey.MEASUREMENT_STATE: measurement_state,
        TradingKey.REGIME: regime_status,
        TradingKey.PATTERNS: context_router.behavioral_patterns,
        TradingKey.ACCURACY: lambda: compute_accuracy_summary(graph_store_factory),
        TradingKey.FINGERPRINT: lambda: json_safe(scorer().fingerprint()),
        TradingKey.TRUST_ANALYSIS: trust_analysis,
        TradingKey.DECISIONS_SUMMARY: lambda: compute_decisions_summary(graph_store_factory),
        TradingKey.VOL_SHARPE: lambda: compute_clustering_adjusted_sharpe(verified()),
        TradingKey.VRP_ATTRIBUTION: lambda: compute_vrp_attribution(verified()),
        TradingKey.REGIME_VRP: lambda: compute_regime_vrp(verified()),
        TradingKey.DISPERSION_FOLLOW: lambda: compute_dispersion_follow_rate(verified()),
        TradingKey.CORRELATION: correlation,
        TradingKey.COUNTERFACTUAL_DEFAULT: lambda: compute_counterfactual_default(scorer()),
        TradingKey.EVOLUTION: lambda: compute_evolution_summary(rejection_summary),
        TradingKey.TRAJECTORY: lambda: json_safe(scorer().trajectory()),
        TradingKey.CONSERVATION: lambda: compute_conservation_status_payload("trading", scorer()),
        TradingKey.CENTROID_HISTORY_SUMMARY: centroid_history_summary,
        TradingKey.AUDIT_TRAIL_SUMMARY: audit_trail_summary,
        TradingKey.REGIME_STATUS: regime_status,
        TradingKey.REGIME_ANALYTICS: regime_analytics,
        TradingKey.PROMOTION: lambda: compute_promotion_dashboard(graph_store_factory),
        TradingKey.REJECTION_SUMMARY: rejection_summary,
        TradingKey.TRANSFER: transfer_status,
        TradingKey.EXECUTION: execution,
        TradingKey.WEBHOOK_HISTORY: compute_webhook_status,
        TradingKey.COHORT_STATUS: lambda: CohortStatusService(graph_store=graph_store()).get_status(),
        TradingKey.VIX: lambda: {"status": "not_computed"},
        TradingKey.JOURNAL_TRADES_SUMMARY: lambda: compute_journal_trades_summary(graph_store_factory),
        TradingKey.ANALYTICS_BY_CATEGORY: lambda: compute_journal_analytics(graph_store_factory, "category"),
        TradingKey.ANALYTICS_BY_SUBCATEGORY: lambda: compute_journal_analytics(graph_store_factory, "subcategory"),
        TradingKey.REGIME_HISTORY: lambda: {"history": [], "bounded": True},
        TradingKey.CORRELATION_CONFIG: lambda: {"window": 20},
        TradingKey.REGIME_ANALYTICS_SUMMARY: regime_analytics,
        TradingKey.IKS: lambda: {"iks": safe_call(lambda: scorer()._compute_iks(), 0.0)},
        TradingKey.REGIME_CURRENT: regime_status,
        TradingKey.REGIME_PERFORMANCE: regime_analytics,
        TradingKey.EVOLUTION_PROMOTED: lambda: {"promoted": []},
    }
    service_fns: dict[TradingKey, Callable[..., Any]] = {
        TradingKey.ANALYTICS: context_router.analytics,
        TradingKey.HISTORY_SUMMARY: lambda: compute_history_summary(graph_store_factory),
        TradingKey.TRADE_METADATA: context_router.get_trade_metadata,
        TradingKey.MARKET_SNAPSHOT: context_router.market_snapshot,
        TradingKey.TRANSFER_STATUS: transfer_status,
        TradingKey.ARCHETYPES: compute_archetypes_summary,
        TradingKey.MEASUREMENT_STATE: measurement_state,
        TradingKey.REGIME: regime_status,
        TradingKey.PATTERNS: context_router.behavioral_patterns,
        TradingKey.ACCURACY: lambda: compute_accuracy_summary(graph_store_factory),
        TradingKey.FINGERPRINT: lambda: json_safe(scorer().fingerprint()),
        TradingKey.TRUST_ANALYSIS: trust_analysis,
        TradingKey.DECISIONS_SUMMARY: lambda: compute_decisions_summary(graph_store_factory),
        TradingKey.VOL_SHARPE: lambda: compute_clustering_adjusted_sharpe(verified()),
        TradingKey.VRP_ATTRIBUTION: lambda: compute_vrp_attribution(verified()),
        TradingKey.REGIME_VRP: lambda: compute_regime_vrp(verified()),
        TradingKey.DISPERSION_FOLLOW: lambda: compute_dispersion_follow_rate(verified()),
        TradingKey.CORRELATION: correlation,
        TradingKey.COUNTERFACTUAL_DEFAULT: lambda: compute_counterfactual_default(scorer()),
        TradingKey.EVOLUTION: lambda: compute_evolution_summary(rejection_summary),
        TradingKey.TRAJECTORY: lambda: json_safe(scorer().trajectory()),
        TradingKey.CONSERVATION: lambda: compute_conservation_status_payload("trading", scorer()),
        TradingKey.CENTROID_HISTORY_SUMMARY: centroid_history_summary,
        TradingKey.AUDIT_TRAIL_SUMMARY: audit_trail_summary,
        TradingKey.REGIME_STATUS: regime_status,
        TradingKey.REGIME_ANALYTICS: regime_analytics,
        TradingKey.PROMOTION: lambda: compute_promotion_dashboard(graph_store_factory),
        TradingKey.REJECTION_SUMMARY: rejection_summary,
        TradingKey.TRANSFER: transfer_status,
        TradingKey.EXECUTION: execution,
        TradingKey.WEBHOOK_HISTORY: compute_webhook_status,
        TradingKey.COHORT_STATUS: lambda: CohortStatusService(graph_store=graph_store()).get_status(),
        TradingKey.VIX: lambda: {"status": "not_computed"},
        TradingKey.JOURNAL_TRADES_SUMMARY: lambda: compute_journal_trades_summary(graph_store_factory),
        TradingKey.ANALYTICS_BY_CATEGORY: lambda: compute_journal_analytics(graph_store_factory, "category"),
        TradingKey.ANALYTICS_BY_SUBCATEGORY: lambda: compute_journal_analytics(graph_store_factory, "subcategory"),
        TradingKey.REGIME_HISTORY: lambda: {"history": [], "bounded": True},
        TradingKey.CORRELATION_CONFIG: lambda: {"window": 20},
        TradingKey.REGIME_ANALYTICS_SUMMARY: regime_analytics,
        TradingKey.IKS: lambda: {"iks": safe_call(lambda: scorer()._compute_iks(), 0.0)},
        TradingKey.REGIME_CURRENT: regime_status,
        TradingKey.REGIME_PERFORMANCE: regime_analytics,
        TradingKey.EVOLUTION_PROMOTED: lambda: {"promoted": []},
    }
    urls: dict[TradingKey, str] = {
        TradingKey.ANALYTICS: "/api/context/analytics",
        TradingKey.HISTORY_SUMMARY: "/api/history",
        TradingKey.TRADE_METADATA: "/api/context/trade-metadata",
        TradingKey.MARKET_SNAPSHOT: "/api/context/market-snapshot",
        TradingKey.TRANSFER_STATUS: "/api/transfer/status",
        TradingKey.ARCHETYPES: "/api/archetypes?domain=trading",
        TradingKey.MEASUREMENT_STATE: "/api/measurement-state",
        TradingKey.REGIME: "/api/trading/regime",
        TradingKey.PATTERNS: "/api/context/patterns",
        TradingKey.ACCURACY: "/api/self/accuracy-by-category",
        TradingKey.FINGERPRINT: "/api/fingerprint",
        TradingKey.TRUST_ANALYSIS: "/api/context/trust-analysis",
        TradingKey.DECISIONS_SUMMARY: "/api/self/decisions?limit=50",
        TradingKey.VOL_SHARPE: "/api/trading/analytics/vol-sharpe",
        TradingKey.VRP_ATTRIBUTION: "/api/trading/analytics/vrp-attribution",
        TradingKey.REGIME_VRP: "/api/trading/analytics/regime-vrp",
        TradingKey.DISPERSION_FOLLOW: "/api/trading/analytics/dispersion-follow",
        TradingKey.CORRELATION: "/api/trading/correlation",
        TradingKey.COUNTERFACTUAL_DEFAULT: "/api/trading/score/counterfactual/default",
        TradingKey.EVOLUTION: "/api/trading/evolution/log",
        TradingKey.TRAJECTORY: "/api/trajectory",
        TradingKey.CONSERVATION: "/api/conservation/status",
        TradingKey.CENTROID_HISTORY_SUMMARY: "/api/self/centroid-history?limit=50",
        TradingKey.AUDIT_TRAIL_SUMMARY: "/api/self/audit-trail?limit=20",
        TradingKey.REGIME_STATUS: "/api/trading/regime-status",
        TradingKey.REGIME_ANALYTICS: "/api/trading/regime-analytics",
        TradingKey.PROMOTION: "/api/trading/promotion/dashboard",
        TradingKey.REJECTION_SUMMARY: "/api/trading/evolution/rejection-summary",
        TradingKey.TRANSFER: "/api/transfer/opportunities",
        TradingKey.EXECUTION: "/api/trading/execution/analysis",
        TradingKey.WEBHOOK_HISTORY: "/api/trading/webhook/history",
        TradingKey.COHORT_STATUS: "/api/trading/cohort-status",
        TradingKey.VIX: "/api/trading/vix-timing",
        TradingKey.JOURNAL_TRADES_SUMMARY: "/api/trading/journal/trades?limit=50",
        TradingKey.ANALYTICS_BY_CATEGORY: "/api/trading/analytics?group_by=category",
        TradingKey.ANALYTICS_BY_SUBCATEGORY: "/api/trading/analytics?group_by=subcategory",
        TradingKey.REGIME_HISTORY: "/api/trading/regime/history",
        TradingKey.CORRELATION_CONFIG: "/api/trading/correlation/config",
        TradingKey.REGIME_ANALYTICS_SUMMARY: "/api/trading/regime-analytics/summary",
        TradingKey.IKS: "/api/trading/iks",
        TradingKey.REGIME_CURRENT: "/api/trading/regime/current",
        TradingKey.REGIME_PERFORMANCE: "/api/trading/regime/performance",
        TradingKey.EVOLUTION_PROMOTED: "/api/evolution/promoted",
    }

    wave_by_key = _wave_assignments()
    invalidations = _invalidations()
    cold_keys = _cold_keys()
    critical_keys = _critical_keys()
    scorer_read_keys = _scorer_read_keys()
    for manifest_key in TradingKey:
        cache.register(
            manifest_key.value,
            compute[manifest_key],
            invalidated_by=invalidations.get(manifest_key, ()),
            critical=any(wave == 1 for wave in wave_by_key.get(manifest_key, {}).values()),
            wave_by_event=wave_by_key.get(manifest_key, {}),
            schema=TRADING_SCHEMA_BY_KEY[manifest_key],
            service_fn=service_fns[manifest_key],
            url=urls[manifest_key],
            reads_scorer=manifest_key in scorer_read_keys,
            tier=(
                "COLD"
                if manifest_key in cold_keys
                else "CRITICAL"
                if manifest_key in critical_keys
                else "STANDARD"
            ),
        )

    cache.register_dynamic("ticker/{ticker}")
    cache.register_dynamic("archetypes/{name}")
    cache.register_dynamic("counterfactual-custom")
    register_tab_state_cache(cache)
    return cache


def _invalidations() -> dict[TradingKey, tuple[str, ...]]:
    result: dict[TradingKey, list[str]] = {key: [] for key in TradingKey}
    maps = {
        "score": [
            TradingKey.TRAJECTORY,
            TradingKey.ANALYTICS,
            TradingKey.CONSERVATION,
            TradingKey.REGIME_ANALYTICS,
            TradingKey.REGIME_CURRENT,
            TradingKey.REGIME_PERFORMANCE,
            TradingKey.VOL_SHARPE,
            TradingKey.VRP_ATTRIBUTION,
            TradingKey.DISPERSION_FOLLOW,
            TradingKey.MEASUREMENT_STATE,
            TradingKey.COHORT_STATUS,
            TradingKey.PROMOTION,
            TradingKey.TRUST_ANALYSIS,
            TradingKey.DECISIONS_SUMMARY,
            TradingKey.REGIME_VRP,
            TradingKey.CENTROID_HISTORY_SUMMARY,
            TradingKey.AUDIT_TRAIL_SUMMARY,
            TradingKey.EXECUTION,
            TradingKey.WEBHOOK_HISTORY,
            TradingKey.JOURNAL_TRADES_SUMMARY,
            TradingKey.ANALYTICS_BY_CATEGORY,
            TradingKey.ANALYTICS_BY_SUBCATEGORY,
            TradingKey.REGIME_HISTORY,
            TradingKey.REGIME_ANALYTICS_SUMMARY,
        ],
        "verify": [
            TradingKey.TRAJECTORY,
            TradingKey.ANALYTICS,
            TradingKey.CONSERVATION,
            TradingKey.VOL_SHARPE,
            TradingKey.VRP_ATTRIBUTION,
            TradingKey.MEASUREMENT_STATE,
            TradingKey.REGIME_ANALYTICS,
            TradingKey.IKS,
        ],
        "learn": [
            TradingKey.TRAJECTORY,
            TradingKey.CONSERVATION,
            TradingKey.VOL_SHARPE,
            TradingKey.VRP_ATTRIBUTION,
        ],
        "regime_break": [
            TradingKey.REGIME_STATUS,
            TradingKey.REGIME_ANALYTICS,
            TradingKey.REGIME_CURRENT,
            TradingKey.REGIME_PERFORMANCE,
        ],
        "reset": [
            TradingKey.ARCHETYPES,
            TradingKey.MEASUREMENT_STATE,
            TradingKey.MARKET_SNAPSHOT,
            TradingKey.ANALYTICS,
            TradingKey.HISTORY_SUMMARY,
            TradingKey.TRADE_METADATA,
            TradingKey.TRANSFER_STATUS,
            TradingKey.REGIME,
            TradingKey.PATTERNS,
            TradingKey.ACCURACY,
            TradingKey.FINGERPRINT,
            TradingKey.TRAJECTORY,
            TradingKey.CONSERVATION,
            TradingKey.VOL_SHARPE,
            TradingKey.VRP_ATTRIBUTION,
            TradingKey.DISPERSION_FOLLOW,
            TradingKey.COHORT_STATUS,
            TradingKey.COUNTERFACTUAL_DEFAULT,
            TradingKey.EVOLUTION,
        ],
        "evolution": [TradingKey.EVOLUTION, TradingKey.REJECTION_SUMMARY, TradingKey.EVOLUTION_PROMOTED],
        "transfer": [TradingKey.TRANSFER_STATUS, TradingKey.TRANSFER, TradingKey.CONSERVATION, TradingKey.TRAJECTORY],
        "market_data_refresh": [TradingKey.MARKET_SNAPSHOT, TradingKey.CORRELATION, TradingKey.VIX],
        "metadata_update": [
            TradingKey.TRADE_METADATA,
            TradingKey.ANALYTICS,
            TradingKey.HISTORY_SUMMARY,
        ],
    }
    for event, keys in maps.items():
        for key in keys:
            if key in result:
                result[key].append(event)
    return {key: tuple(events) for key, events in result.items()}


def _cold_keys() -> set[TradingKey]:
    return {
        TradingKey.ARCHETYPES,
        TradingKey.FINGERPRINT,
        TradingKey.CORRELATION_CONFIG,
    }


def _critical_keys() -> set[TradingKey]:
    return {
        TradingKey.TRAJECTORY,
        TradingKey.CONSERVATION,
        TradingKey.ANALYTICS,
    }


def _scorer_read_keys() -> set[TradingKey]:
    return {
        TradingKey.MEASUREMENT_STATE,
        TradingKey.TRANSFER_STATUS,
        TradingKey.FINGERPRINT,
        TradingKey.TRUST_ANALYSIS,
        TradingKey.COUNTERFACTUAL_DEFAULT,
        TradingKey.TRAJECTORY,
        TradingKey.CONSERVATION,
        TradingKey.TRANSFER,
        TradingKey.IKS,
    }


def _wave_assignments() -> dict[TradingKey, dict[str, int]]:
    wave1 = {
        "score": {TradingKey.TRAJECTORY, TradingKey.ANALYTICS, TradingKey.CONSERVATION},
        "verify": {TradingKey.TRAJECTORY, TradingKey.ANALYTICS, TradingKey.CONSERVATION},
        "learn": {TradingKey.TRAJECTORY, TradingKey.CONSERVATION},
        "regime_break": {TradingKey.REGIME_STATUS},
        "reset": {TradingKey.ARCHETYPES, TradingKey.MEASUREMENT_STATE, TradingKey.MARKET_SNAPSHOT},
        "evolution": {TradingKey.EVOLUTION},
        "transfer": {TradingKey.TRANSFER_STATUS, TradingKey.CONSERVATION, TradingKey.TRAJECTORY},
        "market_data_refresh": {TradingKey.MARKET_SNAPSHOT},
    }
    result: dict[TradingKey, dict[str, int]] = {}
    for key, events in _invalidations().items():
        for event in events:
            result.setdefault(key, {})[event] = 1 if key in wave1.get(event, set()) else 2
    return result
