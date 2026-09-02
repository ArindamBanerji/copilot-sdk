"""Domain-specific RL component wiring for scorer presets."""

from __future__ import annotations

from typing import Any, Callable

from copilot_sdk.rl.credit import CreditAssigner
from copilot_sdk.rl.domains.dataops import DataOpsReward
from copilot_sdk.rl.domains.purchasing import PurchasingReward
from copilot_sdk.rl.domains.trading import TradingReward
from copilot_sdk.rl.exploration import ConservationBoundedThompson
from copilot_sdk.rl.reward_functions import (
    BinaryRewardFunction,
    GradedFinancialRewardFunction,
    PnLRewardFunction,
    WasteReductionRewardFunction,
)


RL_PRESET_REGISTRY: dict[str, dict[str, Any]] = {
    "soc": {
        "reward_function": BinaryRewardFunction,
        "penalty_ratio": 20.0,
    },
    "trading": {
        "reward_function": TradingReward,
        "penalty_ratio": 3.0,
    },
    "purchasing": {
        "reward_function": PurchasingReward,
        "penalty_ratio": 3.0,
    },
    "dataops": {
        "reward_function": DataOpsReward,
        "penalty_ratio": 10.0,
    },
    "s2p": {
        "reward_function": GradedFinancialRewardFunction,
        "penalty_ratio": 5.0,
    },
}


def get_rl_components(
    domain: str,
    preset: Any,
    graph_store: Any | None = None,
) -> dict[str, Any] | None:
    """Build default RL components for a known scorer preset domain."""

    config = RL_PRESET_REGISTRY.get(str(domain).lower())
    if config is None:
        return None

    reward_factory = config["reward_function"]
    n_actions = _preset_n_actions(preset)
    return {
        "reward_function": _construct(reward_factory),
        "credit_assigner": CreditAssigner(graph_store=graph_store),
        "exploration_policy": ConservationBoundedThompson(n_actions=n_actions, graph_store=graph_store),
        "penalty_ratio": _preset_penalty_ratio(preset, float(config["penalty_ratio"])),
    }


def _construct(factory: Callable[[], Any]) -> Any:
    return factory()


def _preset_n_actions(preset: Any) -> int:
    shape = getattr(preset, "shape", None)
    if shape is not None and hasattr(shape, "n_actions"):
        return int(shape.n_actions)
    if hasattr(preset, "n_actions"):
        return int(preset.n_actions)
    actions = getattr(preset, "actions", None)
    if actions is not None:
        return len(actions)
    raise AttributeError("preset does not expose an action count for RL exploration")


def _preset_penalty_ratio(preset: Any, default: float) -> float:
    try:
        value = float(getattr(preset, "penalty_ratio"))
    except (TypeError, ValueError, AttributeError):
        return default
    return value if value > 0.0 else default
