from __future__ import annotations

import sys
import json
import subprocess
from pathlib import Path

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.presets.soc import SOCPreset
from copilot_sdk.scoring.scorer import CompoundingScorer, LearnResult, ScoreResult


EXPECTED_CATEGORIES = (
    "credential_access",
    "malware_execution",
    "lateral_movement",
    "data_exfiltration",
    "insider_threat",
    "cloud_infrastructure",
)
EXPECTED_ACTIONS = (
    "escalate",
    "investigate",
    "suppress",
    "monitor",
)
EXPECTED_FACTORS = (
    "privileged_identity_context",
    "asset_criticality",
    "threat_intel_enrichment",
    "pattern_history",
    "time_anomaly",
    "device_trust",
)


def _soc_config_data() -> dict:
    backend = Path(__file__).resolve().parents[2] / "gen-ai-roi-demo-v4-v50" / "backend"
    code = """
import json
import sys
sys.path.insert(0, r'{backend}')
from app.domains.soc import config
print(json.dumps({{
    'categories': config.SOC_CATEGORIES,
    'actions': config.SCORER_ACTIONS,
    'factors': config.SOC_FACTORS,
    'centroids': config.SCORER_PROFILE_CENTROIDS.tolist(),
}}))
""".format(backend=str(backend))
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    return dict(json.loads(result.stdout))


def _soc_scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "soc",
        graph_store=InMemoryGraphStore(domain="soc"),
        enable_rl=False,
        profile="test",
    )


def _factor_payload(value: float = 0.5) -> dict[str, float]:
    return {factor: value for factor in EXPECTED_FACTORS}


def test_soc_preset_exists() -> None:
    assert PRESET_REGISTRY["soc"] is SOCPreset


def test_soc_preset_domain() -> None:
    assert SOCPreset().name == "soc"


def test_soc_preset_penalty_ratio() -> None:
    assert SOCPreset().penalty_ratio == 20.0


def test_soc_preset_categories() -> None:
    preset = SOCPreset()

    assert preset.shape.n_categories == 6
    assert preset.shape.category_names == EXPECTED_CATEGORIES


def test_soc_preset_actions() -> None:
    preset = SOCPreset()

    assert preset.shape.n_actions == 4
    assert preset.shape.action_names == EXPECTED_ACTIONS


def test_soc_preset_factors() -> None:
    preset = SOCPreset()

    assert preset.shape.n_factors == 6
    assert preset.shape.factor_names == EXPECTED_FACTORS


def test_soc_preset_tensor_shape() -> None:
    preset = SOCPreset()

    assert preset.shape.tensor_shape == (6, 4, 6)
    assert preset.shape.tensor_size == 144
    assert preset.bootstrap_centroids.shape == (6, 4, 6)


def test_soc_preset_categories_match_config() -> None:
    config = _soc_config_data()

    assert SOCPreset().shape.category_names == tuple(config["categories"])


def test_soc_preset_actions_match_config() -> None:
    config = _soc_config_data()

    assert SOCPreset().shape.action_names == tuple(config["actions"])


def test_soc_preset_factors_match_config() -> None:
    config = _soc_config_data()

    assert SOCPreset().shape.factor_names == tuple(config["factors"])


def test_soc_preset_tensor_size_matches_config() -> None:
    config = _soc_config_data()

    assert SOCPreset().shape.tensor_size == (
        len(config["categories"])
        * len(config["actions"])
        * len(config["factors"])
    )


def test_soc_preset_centroids_match_config() -> None:
    config = _soc_config_data()

    np.testing.assert_allclose(
        SOCPreset().bootstrap_centroids,
        np.asarray(config["centroids"], dtype=np.float64),
    )


def test_from_preset_soc_works() -> None:
    scorer = _soc_scorer()

    assert scorer._preset.name == "soc"
    assert scorer._scorer.centroids.shape == (6, 4, 6)


def test_from_preset_soc_score_works() -> None:
    result = _soc_scorer().score(
        category="credential_access",
        factors=_factor_payload(),
    )

    assert isinstance(result, ScoreResult)
    assert result.action in EXPECTED_ACTIONS
    assert result.category == "credential_access"
    assert len(result.probabilities) == 4


def test_from_preset_soc_learn_works() -> None:
    scorer = _soc_scorer()
    score = scorer.score(
        category="credential_access",
        factors=_factor_payload(),
    )

    result = scorer.learn(
        decision_id=score.decision_id,
        actual_action=score.action,
        outcome="correct",
    )

    assert isinstance(result, LearnResult)
    assert result.decision_id == score.decision_id
    assert result.decisions_total >= 1


def test_from_preset_soc_dk_phase_transition() -> None:
    scorer = _soc_scorer()
    category = "credential_access"

    for index in range(230):
        value = 0.85 if index % 2 == 0 else 0.15
        factors = _factor_payload(value)
        score = scorer.score(category=category, factors=factors)
        scorer.learn(score.decision_id, score.action)

    assert scorer.get_category_phase(category) == "VARIANCE_LEARNING"
    assert scorer.reestimate_dk_if_due() is True
    assert scorer.get_dk_weights() is not None


def test_all_five_presets_in_registry() -> None:
    assert set(PRESET_REGISTRY) == {
        "dataops",
        "purchasing",
        "s2p",
        "soc",
        "trading",
    }
