from dataclasses import FrozenInstanceError
import importlib.util
from pathlib import Path

from copilot_sdk.domains.base import (
    BaseDomainConfig,
    DomainAction,
    DomainCategory,
    DomainFactor,
    DomainSituationType,
)


def _trading_config_cls():
    path = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "trading"
        / "backend"
        / "app"
        / "domains"
        / "trading_config.py"
    )
    spec = importlib.util.spec_from_file_location("trading_domain_config_for_test", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.TradingDomainConfig


def test_domain_action_frozen():
    action = DomainAction(id="x", label="X")
    try:
        action.id = "y"
        assert False, "DomainAction should be frozen"
    except FrozenInstanceError:
        pass


def test_domain_factor_frozen():
    factor = DomainFactor(id="x", label="X")
    try:
        factor.id = "y"
        assert False, "DomainFactor should be frozen"
    except FrozenInstanceError:
        pass


def test_domain_action_defaults():
    action = DomainAction(id="x", label="X")
    assert action.time_saved_min == 0.0
    assert action.cost_dollars == 0.0
    assert action.risk_level == "low"


def test_domain_factor_defaults():
    factor = DomainFactor(id="x", label="X")
    assert factor.description == ""


def test_domain_situation_defaults():
    situation = DomainSituationType(id="x", label="X")
    assert situation.color == "#6B7280"


def test_base_config_lookup_helpers():
    class TestConfig(BaseDomainConfig):
        actions = [DomainAction(id="a1", label="A1")]
        factors = [DomainFactor(id="f1", label="F1")]
        categories = [
            DomainCategory(id="c1", label="C1"),
            DomainCategory(id="c2", label="C2"),
        ]

    config = TestConfig()
    assert config.get_action("a1").label == "A1"
    assert config.get_action("missing") is None
    assert config.get_factor("f1").label == "F1"
    assert config.get_categories() == ["c1", "c2"]
    assert config.get_category_index("c2") == 1
    assert config.get_category_index("missing") is None


def test_trading_config_has_4_actions():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    assert len(config.actions) == 4
    assert config.get_action_ids() == [
        "strong_execution",
        "partial_execution",
        "poor_execution",
        "skip_recommended",
    ]


def test_trading_config_has_10_factors():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    assert len(config.factors) == 10
    assert config.get_factor_ids() == [
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


def test_trading_config_has_5_categories():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    assert len(config.categories) == 5
    assert config.get_categories() == [
        "trend_following",
        "mean_reversion",
        "event_driven",
        "income_strategy",
        "scalp_intraday",
    ]


def test_trading_config_has_7_situation_types():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    assert len(config.situation_types) == 7
    assert config.get_situation_type("REVENGE_TRADING") is not None
    assert config.get_situation_type("UNKNOWN") is not None


def test_trading_actions_have_cost_models():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    poor = config.get_action("poor_execution")
    assert poor is not None
    assert poor.cost_dollars > 0
    assert poor.risk_level == "high"
    skip = config.get_action("skip_recommended")
    assert skip is not None
    assert skip.cost_dollars == 0.0
    assert skip.risk_level == "low"


def test_trading_factors_have_descriptions():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    for factor in config.factors:
        assert factor.description, f"{factor.id} has no description"
        assert factor.label, f"{factor.id} has no label"


def test_trading_situations_have_colors():
    TradingDomainConfig = _trading_config_cls()

    config = TradingDomainConfig()
    for situation in config.situation_types:
        assert situation.color.startswith("#"), f"{situation.id} color not hex"
    revenge = config.get_situation_type("REVENGE_TRADING")
    assert revenge is not None
    assert revenge.color != "#6B7280"


def test_trading_factor_ids_match_preset():
    """DomainConfig factor IDs must match TradingPreset factor_names."""
    from copilot_sdk.scoring.presets.trading import TradingPreset

    TradingDomainConfig = _trading_config_cls()
    config_ids = TradingDomainConfig().get_factor_ids()
    preset_names = list(TradingPreset().shape.factor_names)
    assert config_ids == preset_names


def test_trading_action_ids_match_preset():
    """DomainConfig action IDs must match TradingPreset action_names."""
    from copilot_sdk.scoring.presets.trading import TradingPreset

    TradingDomainConfig = _trading_config_cls()
    config_ids = TradingDomainConfig().get_action_ids()
    preset_names = list(TradingPreset().shape.action_names)
    assert config_ids == preset_names


def test_trading_category_ids_match_preset():
    """DomainConfig category IDs must match TradingPreset category_names."""
    from copilot_sdk.scoring.presets.trading import TradingPreset

    TradingDomainConfig = _trading_config_cls()
    config_ids = TradingDomainConfig().get_categories()
    preset_names = list(TradingPreset().shape.category_names)
    assert config_ids == preset_names


def test_config_does_not_affect_scoring(tmp_path):
    """DomainConfig is metadata only - scoring unchanged."""
    from copilot_sdk.scoring.scorer import CompoundingScorer

    scorer = CompoundingScorer.from_preset(
        "trading", db_path=str(tmp_path / "p48_test.db")
    )
    try:
        factors = {factor: 0.5 for factor in scorer._preset.shape.factor_names}
        r1 = scorer.score_read_only(factors, "trend_following")

        TradingDomainConfig = _trading_config_cls()
        _ = TradingDomainConfig()
        r2 = scorer.score_read_only(factors, "trend_following")
        assert r1.action == r2.action
        assert r1.confidence == r2.confidence
    finally:
        scorer.graph_store.close()
