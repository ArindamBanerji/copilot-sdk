from pathlib import Path

import pytest

pytest.importorskip("gae.profile_scorer")

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.presets.s2p import S2PPreset


def test_s2p_preset_registered():
    assert "s2p" in PRESET_REGISTRY
    assert PRESET_REGISTRY["s2p"] is S2PPreset


def test_s2p_preset_shape_and_penalty_ratio():
    preset = S2PPreset()

    assert preset.name == "s2p"
    assert preset.shape.n_categories == 5
    assert preset.shape.n_actions == 5
    assert preset.shape.n_factors == 7
    assert preset.penalty_ratio == 5.0
    assert preset.shape.category_names == (
        "price_variance",
        "quantity_mismatch",
        "duplicate_risk",
        "contract_gap",
        "format_compliance",
    )
    assert preset.shape.action_names == (
        "auto_approve",
        "hold_for_review",
        "escalate_to_buyer",
        "flag_leakage",
        "refer_to_specialist",
    )
    assert preset.shape.factor_names == (
        "match_status",
        "amount_variance_ratio",
        "duplicate_score",
        "supplier_exception_history",
        "payment_terms_impact",
        "commodity_index_correlation",
        "tax_regulatory_compliance",
    )
    assert preset.bootstrap_centroids.shape == (5, 5, 7)


def test_from_preset_s2p_works(tmp_path):
    scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.db"))

    assert scorer._preset.name == "s2p"
    assert scorer._preset.shape.tensor_shape == (5, 5, 7)
    scorer.graph_store.close()


def test_s2p_scoring_returns_valid_action(tmp_path):
    scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.db"))
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}

    result = scorer.score(factors, "price_variance")

    assert result.action in scorer._preset.shape.action_names
    assert result.category == "price_variance"
    assert len(result.probabilities) == 5
    scorer.graph_store.close()


def test_s2p_preset_contains_no_soc_vocabulary():
    text = Path("copilot_sdk/scoring/presets/s2p.py").read_text(encoding="utf-8").lower()

    for forbidden in (
        "credential_access",
        "lateral_movement",
        "malware",
        "brute_force",
        "insider_threat",
    ):
        assert forbidden not in text
