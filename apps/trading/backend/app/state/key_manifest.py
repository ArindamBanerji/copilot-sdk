"""Typed manifest for Trading materialized tab-state keys."""

from __future__ import annotations

from enum import Enum


class TradingKey(str, Enum):
    ANALYTICS = "analytics"
    HISTORY_SUMMARY = "history-summary"
    TRADE_METADATA = "trade-metadata"
    MARKET_SNAPSHOT = "market-snapshot"
    TRANSFER_STATUS = "transfer-status"
    ARCHETYPES = "archetypes"
    MEASUREMENT_STATE = "measurement-state"
    REGIME = "regime"
    PATTERNS = "patterns"
    ACCURACY = "accuracy"
    FINGERPRINT = "fingerprint"
    TRUST_ANALYSIS = "trust-analysis"
    DECISIONS_SUMMARY = "decisions-summary"
    VOL_SHARPE = "vol-sharpe"
    VRP_ATTRIBUTION = "vrp-attribution"
    REGIME_VRP = "regime-vrp"
    DISPERSION_FOLLOW = "dispersion-follow"
    CORRELATION = "correlation"
    COUNTERFACTUAL_DEFAULT = "counterfactual-default"
    EVOLUTION = "evolution"
    TRAJECTORY = "trajectory"
    CONSERVATION = "conservation"
    CENTROID_HISTORY_SUMMARY = "centroid-history-summary"
    AUDIT_TRAIL_SUMMARY = "audit-trail-summary"
    REGIME_STATUS = "regime-status"
    REGIME_ANALYTICS = "regime-analytics"
    PROMOTION = "promotion"
    REJECTION_SUMMARY = "rejection-summary"
    TRANSFER = "transfer"
    EXECUTION = "execution"
    WEBHOOK_HISTORY = "webhook-history"
    COHORT_STATUS = "cohort-status"
    VIX = "vix"
    JOURNAL_TRADES_SUMMARY = "journal-trades-summary"
    ANALYTICS_BY_CATEGORY = "analytics-by-category"
    ANALYTICS_BY_SUBCATEGORY = "analytics-by-subcategory"
    REGIME_HISTORY = "regime-history"
    CORRELATION_CONFIG = "correlation-config"
    REGIME_ANALYTICS_SUMMARY = "regime-analytics-summary"
    IKS = "iks"
    REGIME_CURRENT = "regime-current"
    REGIME_PERFORMANCE = "regime-performance"
    EVOLUTION_PROMOTED = "evolution-promoted"

    @property
    def critical(self) -> bool:
        return self in _CRITICAL_KEYS


_CRITICAL_KEYS = {
    TradingKey.TRAJECTORY,
    TradingKey.ANALYTICS,
    TradingKey.CONSERVATION,
}

TRADING_STATIC_KEYS: tuple[str, ...] = tuple(key.value for key in TradingKey)
