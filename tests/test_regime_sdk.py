from __future__ import annotations

from copilot_sdk.regime import RegimeConditioner, RegimeDetector, RegimePolicy


def test_detector_classifies_trending() -> None:
    state = RegimeDetector().detect({"vix": 12.0, "adx": 35.0})
    assert state.regime == "trending"
    assert state.confidence > 0


def test_detector_classifies_ranging() -> None:
    assert RegimeDetector().detect({"vix": 22.0, "adx": 20.0}).regime == "ranging"


def test_detector_classifies_volatile() -> None:
    assert RegimeDetector().detect({"vix": 35.0, "adx": 20.0}).regime == "volatile"


def test_detector_classifies_calm() -> None:
    assert RegimeDetector().detect({"vix": 12.0, "adx": 15.0}).regime == "calm"


def test_detector_reports_unknown_without_indicators() -> None:
    state = RegimeDetector().detect({})
    assert state.regime == "unknown"
    assert state.confidence == 0.0
    assert state.indicators == {}


def test_policy_is_configurable_for_an_operational_copilot() -> None:
    policy = RegimePolicy(
        thresholds={"volatile": 0.8, "ranging": 0.4, "trending": 0.7, "calm_vix": 0.2, "calm_adx": 0.2},
        abstention_minimum=3,
        conditioning_enabled=True,
    )
    state = RegimeDetector(policy).detect({"vix": 0.9, "adx": 0.1})
    assert state.regime == "volatile"
    assert policy.abstention_minimum == 3


def test_conditioner_reports_verified_regime_accuracy() -> None:
    rows = [
        {"regime": "trending", "verified": True, "outcome_correct": True},
        {"regime": "trending", "verified": True, "outcome_correct": False},
        {"regime": "ranging", "verified": True, "outcome_correct": True},
    ]
    policy = RegimePolicy(abstention_minimum=2)
    state = RegimeDetector(policy).detect({"vix": 12.0, "adx": 35.0})
    result = RegimeConditioner(policy).condition({"decisions": rows}, state)
    assert result.regime_scoped_accuracy == 0.5
    assert result.abstention is False
    assert result.verified_count == 2


def test_conditioner_abstains_below_regime_minimum_and_counts_rejections() -> None:
    policy = RegimePolicy(abstention_minimum=3)
    state = RegimeDetector(policy).detect({"vix": 35.0, "adx": 20.0})
    result = RegimeConditioner(policy).condition(
        {"decisions": [
            {"regime": "volatile", "verified": True, "outcome_correct": True, "rejected": True},
        ]},
        state,
    )
    assert result.abstention is True
    assert result.regime_scoped_accuracy is None
    assert result.rejection_count == 1


def test_conditioned_context_is_json_safe() -> None:
    state = RegimeDetector().detect({"vix": 22.0, "adx": 20.0})
    payload = RegimeConditioner().condition({"decisions": []}, state).to_dict()
    assert isinstance(payload["confidence"], float)
    assert payload["indicators"]["vix"] == 22.0


def test_detector_does_not_depend_on_trading_modules() -> None:
    import copilot_sdk.regime as regime

    assert hasattr(regime, "RegimeDetector")
    assert not any(name.startswith("app") for name in regime.__dict__)
