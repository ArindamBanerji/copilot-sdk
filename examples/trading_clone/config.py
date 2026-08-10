"""Trading-specific oracle-separated synthetic configurations."""

from copilot_sdk.scoring.presets.trading import TradingPreset

from .generator import GeneratorConfig
from .oracle import OracleConfig


_SHAPE = TradingPreset().shape
CATEGORY_NAMES = list(_SHAPE.category_names)
ACTION_NAMES = list(_SHAPE.action_names)
FACTOR_NAMES = list(_SHAPE.factor_names)


RUN_A_GENERATOR = GeneratorConfig(
    seed=142,
    n_decisions=500,
    n_categories=len(CATEGORY_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    factor_names=FACTOR_NAMES,
    disruption_decision=300,
    disruption_categories=[0, 1],
)
RUN_A_ORACLE = OracleConfig(
    seed=199,
    n_categories=len(CATEGORY_NAMES),
    n_actions=len(ACTION_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    action_names=ACTION_NAMES,
    factor_names=FACTOR_NAMES,
    epsilon_firm=0.20,
)

RUN_B_GENERATOR = GeneratorConfig(
    seed=142,
    n_decisions=500,
    n_categories=len(CATEGORY_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    factor_names=FACTOR_NAMES,
    disruption_decision=300,
    disruption_categories=[0, 1],
)
RUN_B_ORACLE = OracleConfig(
    seed=199,
    n_categories=len(CATEGORY_NAMES),
    n_actions=len(ACTION_NAMES),
    n_factors=len(FACTOR_NAMES),
    category_names=CATEGORY_NAMES,
    action_names=ACTION_NAMES,
    factor_names=FACTOR_NAMES,
    epsilon_firm=0.05,
)
