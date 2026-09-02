from __future__ import annotations

from types import SimpleNamespace

from copilot_sdk.rl import (
    ConservationBoundedThompson,
    CreditAssigner,
    GradedFinancialRewardFunction,
    PnLRewardFunction,
    WasteReductionRewardFunction,
)
from copilot_sdk.rl.presets import RL_PRESET_REGISTRY, get_rl_components
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.s2p import S2PPreset
from copilot_sdk.scoring.presets.soc import SOCPreset
from copilot_sdk.scoring.presets.trading import TradingPreset


def test_rl_preset_registry_has_expected_domains():
    assert set(RL_PRESET_REGISTRY) == {"soc", "trading", "purchasing", "dataops", "s2p"}


def test_get_rl_components_returns_components_for_supported_domains():
    assert get_rl_components("trading", TradingPreset()) is not None
    assert get_rl_components("purchasing", PurchasingPreset()) is not None
    assert get_rl_components("dataops", DataOpsPreset()) is not None
    assert get_rl_components("s2p", S2PPreset()) is not None
    assert get_rl_components("soc", SOCPreset()) is not None


def test_get_rl_components_unknown_domain_returns_none():
    preset = SimpleNamespace(shape=SimpleNamespace(n_actions=2), penalty_ratio=1.0)

    assert get_rl_components("unknown_domain", preset) is None


def test_get_rl_components_maps_reward_function_classes():
    assert isinstance(get_rl_components("trading", TradingPreset())["reward_function"], PnLRewardFunction)
    assert isinstance(
        get_rl_components("purchasing", PurchasingPreset())["reward_function"],
        WasteReductionRewardFunction,
    )
    assert isinstance(
        get_rl_components("dataops", DataOpsPreset())["reward_function"],
        GradedFinancialRewardFunction,
    )
    assert isinstance(
        get_rl_components("s2p", S2PPreset())["reward_function"],
        GradedFinancialRewardFunction,
    )


def test_get_rl_components_wires_exploration_and_credit():
    components = get_rl_components("trading", TradingPreset())

    assert isinstance(components["exploration_policy"], ConservationBoundedThompson)
    assert isinstance(components["credit_assigner"], CreditAssigner)


def test_exploration_policy_uses_preset_action_count():
    preset = TradingPreset()
    components = get_rl_components("trading", preset)

    assert components["exploration_policy"].n_actions == preset.shape.n_actions
