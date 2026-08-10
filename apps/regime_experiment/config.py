"""Controls for the EXP-REGIME A/B/C bake-off.

The experiment uses the real Trading preset shape and the APP-1 synthetic
generator/oracle pair.  The generator is shared by every arm; only the model
state at the regime break differs.
"""

from __future__ import annotations

from dataclasses import replace

from copilot_sdk.scoring.presets.trading import TradingPreset
from examples.jm_reference.generator import GeneratorConfig
from examples.jm_reference.oracle import OracleConfig


_TRADING = TradingPreset()
_SHAPE = _TRADING.shape

REGIME_1 = "trending"
REGIME_2 = "volatile"
BREAK_POINT = 250
TOTAL_DECISIONS = 500
CONVERGENCE_THRESHOLD = 0.15
CHECKPOINT_INTERVAL = 25

TRADING_CATEGORIES = list(_SHAPE.category_names)
TRADING_ACTIONS = list(_SHAPE.action_names)
TRADING_FACTORS = list(_SHAPE.factor_names)

EXPERIMENT_GENERATOR = GeneratorConfig(
    seed=42,
    n_decisions=TOTAL_DECISIONS,
    n_categories=_SHAPE.n_categories,
    n_factors=_SHAPE.n_factors,
    category_names=TRADING_CATEGORIES,
    factor_names=TRADING_FACTORS,
    disruption_decision=BREAK_POINT,
    disruption_categories=[0, 1],
    disruption_magnitude=0.3,
)

PHASE_1_ORACLE = OracleConfig(
    seed=99,
    n_categories=_SHAPE.n_categories,
    n_actions=_SHAPE.n_actions,
    n_factors=_SHAPE.n_factors,
    category_names=TRADING_CATEGORIES,
    action_names=TRADING_ACTIONS,
    factor_names=TRADING_FACTORS,
    epsilon_firm=0.20,
)

PHASE_2_ORACLE = OracleConfig(
    seed=77,
    n_categories=_SHAPE.n_categories,
    n_actions=_SHAPE.n_actions,
    n_factors=_SHAPE.n_factors,
    category_names=TRADING_CATEGORIES,
    action_names=TRADING_ACTIONS,
    factor_names=TRADING_FACTORS,
    epsilon_firm=0.20,
)


def experiment_configs(
    total_decisions: int = TOTAL_DECISIONS,
    break_point: int | None = None,
) -> tuple[GeneratorConfig, OracleConfig, OracleConfig, int]:
    """Return independent configs for tests without mutating module globals."""

    actual_break = break_point if break_point is not None else min(
        BREAK_POINT, max(1, total_decisions // 2)
    )
    generator = replace(
        EXPERIMENT_GENERATOR,
        n_decisions=total_decisions,
        disruption_decision=actual_break,
    )
    return generator, replace(PHASE_1_ORACLE), replace(PHASE_2_ORACLE), actual_break
