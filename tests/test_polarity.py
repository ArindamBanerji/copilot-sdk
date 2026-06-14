from copilot_sdk.scoring.polarity import (
    Polarity,
    get_factor_polarities,
    interpret_factor,
)


def test_interpret_positive_high():
    assert interpret_factor("x", 0.85, Polarity.POSITIVE) == "high (favorable)"


def test_interpret_positive_low():
    assert interpret_factor("x", 0.15, Polarity.POSITIVE) == "low (concerning)"


def test_interpret_negative_high():
    assert interpret_factor("x", 0.85, Polarity.NEGATIVE) == "high (concerning)"


def test_interpret_negative_low():
    assert interpret_factor("x", 0.15, Polarity.NEGATIVE) == "low (favorable)"


def test_interpret_neutral_high():
    assert interpret_factor("x", 0.85, Polarity.NEUTRAL) == "high"


def test_interpret_neutral_low():
    assert interpret_factor("x", 0.15, Polarity.NEUTRAL) == "low"


def test_interpret_moderate():
    assert interpret_factor("x", 0.50, Polarity.POSITIVE) == "moderate"
    assert interpret_factor("x", 0.50, Polarity.NEGATIVE) == "moderate"
    assert interpret_factor("x", 0.50, Polarity.NEUTRAL) == "moderate"


def test_interpret_boundary_high():
    """Exactly 0.7 is high, not moderate."""
    assert "high" in interpret_factor("x", 0.7, Polarity.POSITIVE)


def test_interpret_boundary_low():
    """Exactly 0.3 is low, not moderate."""
    assert "low" in interpret_factor("x", 0.3, Polarity.POSITIVE)


def test_get_polarities_trading():
    pols = get_factor_polarities("trading")
    assert len(pols) == 10
    assert pols["signal_alignment"] == Polarity.POSITIVE
    assert pols["options_gamma_risk"] == Polarity.NEGATIVE
    assert pols["market_regime"] == Polarity.NEUTRAL


def test_get_polarities_purchasing():
    pols = get_factor_polarities("purchasing")
    assert len(pols) == 7
    assert pols["historical_waste"] == Polarity.NEGATIVE
    assert pols["day_of_week"] == Polarity.NEUTRAL
    assert pols["price_memory_index"] == Polarity.POSITIVE


def test_get_polarities_dataops():
    pols = get_factor_polarities("dataops")
    assert len(pols) == 6
    assert pols["source_reliability"] == Polarity.POSITIVE
    assert pols["impact_scope"] == Polarity.NEGATIVE


def test_get_polarities_s2p():
    pols = get_factor_polarities("s2p")
    assert len(pols) == 7
    assert pols["match_status"] == Polarity.POSITIVE
    assert pols["duplicate_score"] == Polarity.NEGATIVE


def test_unknown_domain_returns_empty():
    pols = get_factor_polarities("nonexistent")
    assert pols == {}


def test_polarity_keys_match_factor_names():
    """Every preset polarity dict exactly matches its factor names."""
    from copilot_sdk.scoring.presets import PRESET_REGISTRY

    for domain, preset_cls in PRESET_REGISTRY.items():
        preset = preset_cls()
        pols = get_factor_polarities(domain)
        factor_set = set(preset.shape.factor_names)
        polarity_set = set(pols.keys())
        assert polarity_set == factor_set, (
            f"{domain}: polarity keys {polarity_set - factor_set} extra, "
            f"{factor_set - polarity_set} missing"
        )


def test_polarity_does_not_affect_scoring(tmp_path):
    """Prove polarity is display-only: scoring is identical."""
    from copilot_sdk.scoring.scorer import CompoundingScorer

    scorer = CompoundingScorer.from_preset(
        "purchasing", db_path=str(tmp_path / "pol_test.db")
    )
    try:
        factors = {f: 0.5 for f in scorer._preset.shape.factor_names}
        r1 = scorer.score_read_only(factors, "protein")

        pols = get_factor_polarities("purchasing")
        assert len(pols) == 7
        r2 = scorer.score_read_only(factors, "protein")

        assert r1.action == r2.action
        assert r1.confidence == r2.confidence
        assert list(r1.probabilities) == list(r2.probabilities)
    finally:
        scorer.graph_store.close()
