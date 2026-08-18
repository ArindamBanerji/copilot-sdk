"""TradingDomainConfig - full domain specification for Trading copilot.

Imports base classes from copilot_sdk.domains.base (SDK level).
Contains Trading-specific actions, factors, situations, categories
with cost models, descriptions, and display metadata.

Does NOT affect scoring - this is UI/evidence/reporting metadata.
The scorer reads from TradingPreset, not TradingDomainConfig.
"""

from __future__ import annotations

from copilot_sdk.domains.base import (
    BaseDomainConfig,
    DomainAction,
    DomainCategory,
    DomainFactor,
    DomainSituationType,
)


class TradingDomainConfig(BaseDomainConfig):
    actions = [
        DomainAction(
            id="strong_execution",
            label="Strong Execution",
            time_saved_min=8.0,
            cost_dollars=0.0,
            risk_level="medium",
        ),
        DomainAction(
            id="partial_execution",
            label="Partial Execution",
            time_saved_min=5.0,
            cost_dollars=5.0,
            risk_level="low",
        ),
        DomainAction(
            id="poor_execution",
            label="Poor Execution",
            time_saved_min=0.0,
            cost_dollars=50.0,
            risk_level="high",
        ),
        DomainAction(
            id="skip_recommended",
            label="Low-confidence observation",
            time_saved_min=3.0,
            cost_dollars=0.0,
            risk_level="low",
        ),
    ]

    factors = [
        DomainFactor(
            id="signal_alignment",
            label="Signal Alignment",
            description="How well the trade thesis aligns with technical and fundamental signals",
        ),
        DomainFactor(
            id="market_regime",
            label="Market Regime",
            description="Current market state - trending, mean-reverting, or volatile",
        ),
        DomainFactor(
            id="position_sizing",
            label="Position Sizing",
            description="Whether the position size matches the conviction level and account risk budget",
        ),
        DomainFactor(
            id="timing_quality",
            label="Timing Quality",
            description="Entry timing relative to key levels, volume, and intraday patterns",
        ),
        DomainFactor(
            id="risk_reward_actual",
            label="Risk/Reward Actual",
            description="Realized risk-to-reward ratio based on stop and target placement",
        ),
        DomainFactor(
            id="emotional_indicator",
            label="Emotional Indicator",
            description="Detected emotional bias - revenge, FOMO, tilt, or overconfidence signals",
        ),
        DomainFactor(
            id="signal_confidence",
            label="Signal Confidence",
            description="Strength and confluence of the trading signal across timeframes",
        ),
        DomainFactor(
            id="options_delta_exposure",
            label="Options Delta Exposure",
            description="Net delta exposure from options positions - directional risk measure",
        ),
        DomainFactor(
            id="options_iv_percentile",
            label="Options IV Percentile",
            description="Implied volatility percentile rank - indicates whether options are cheap or expensive",
        ),
        DomainFactor(
            id="options_gamma_risk",
            label="Options Gamma Risk",
            description="Gamma exposure risk - how quickly delta changes near expiration or strikes",
        ),
    ]

    situation_types = [
        DomainSituationType(
            id="REVENGE_TRADING",
            label="Revenge Trading",
            description="Trading to recover losses immediately after a losing trade - high emotional bias",
            color="#EF4444",
        ),
        DomainSituationType(
            id="OVERCONFIDENCE",
            label="Overconfidence",
            description="Excessive position sizing or frequency after a winning streak",
            color="#F97316",
        ),
        DomainSituationType(
            id="FOMO",
            label="Fear of Missing Out",
            description="Chasing entries after a move has already extended - poor timing signal",
            color="#EAB308",
        ),
        DomainSituationType(
            id="TILT",
            label="Tilt",
            description="Emotional deviation from the trading plan - impulsive decisions",
            color="#DC2626",
        ),
        DomainSituationType(
            id="DRAWDOWN_CHASE",
            label="Drawdown Chase",
            description="Increasing position size during a drawdown to accelerate recovery",
            color="#7C3AED",
        ),
        DomainSituationType(
            id="TIME_OF_DAY_DEGRADATION",
            label="Time of Day Degradation",
            description="Performance decline during specific market hours - fatigue or low-liquidity effect",
            color="#3B82F6",
        ),
        DomainSituationType(
            id="UNKNOWN",
            label="Unknown",
            description="Insufficient context for automated classification - manual review recommended",
            color="#6B7280",
        ),
    ]

    categories = [
        DomainCategory(
            id="trend_following",
            label="Trend Following",
            description="Trades aligned with the prevailing market direction",
        ),
        DomainCategory(
            id="mean_reversion",
            label="Mean Reversion",
            description="Trades betting on price returning to a statistical mean",
        ),
        DomainCategory(
            id="event_driven",
            label="Event Driven",
            description="Trades around earnings, news, or macro events",
        ),
        DomainCategory(
            id="income_strategy",
            label="Income Strategy",
            description="Options premium collection and yield-focused strategies",
        ),
        DomainCategory(
            id="scalp_intraday",
            label="Scalp / Intraday",
            description="Short-duration trades within a single session",
        ),
    ]
