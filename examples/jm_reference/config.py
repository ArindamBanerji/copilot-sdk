"""Default oracle-separated configurations for the JM Reference App.

Run A uses ``epsilon_firm > 0.128``; Run B uses ``epsilon_firm < 0.128``.
The names below are the current Trading preset names, keeping this sample
compatible with a real SDK scorer.
"""

from .generator import GeneratorConfig
from .oracle import OracleConfig


CATEGORY_NAMES = [
    "trend_following",
    "mean_reversion",
    "event_driven",
    "income_strategy",
    "scalp_intraday",
]
ACTION_NAMES = [
    "strong_execution",
    "partial_execution",
    "poor_execution",
    "skip_recommended",
]
FACTOR_NAMES = [
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
    "options_delta_exposure",
    "options_iv_percentile",
    "options_gamma_risk",
]


RUN_A_GENERATOR = GeneratorConfig(
    seed=42,
    n_decisions=500,
    n_categories=len(CATEGORY_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    factor_names=FACTOR_NAMES,
    disruption_decision=300,
    disruption_categories=[0, 1],
)
RUN_A_ORACLE = OracleConfig(
    seed=99,
    n_categories=len(CATEGORY_NAMES),
    n_actions=len(ACTION_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    action_names=ACTION_NAMES,
    factor_names=FACTOR_NAMES,
    epsilon_firm=0.20,
)

RUN_B_GENERATOR = GeneratorConfig(
    seed=42,
    n_decisions=500,
    n_categories=len(CATEGORY_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    factor_names=FACTOR_NAMES,
    disruption_decision=300,
    disruption_categories=[0, 1],
)
RUN_B_ORACLE = OracleConfig(
    seed=99,
    n_categories=len(CATEGORY_NAMES),
    n_actions=len(ACTION_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    action_names=ACTION_NAMES,
    factor_names=FACTOR_NAMES,
    epsilon_firm=0.05,
)
