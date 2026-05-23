import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest


GAE_PATH = Path(__file__).resolve().parents[2] / "graph-attention-engine-v50"
if GAE_PATH.exists() and str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

pytest.importorskip("gae.profile_scorer")
from gae.profile_scorer import ProfileScorer

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.fingerprint import compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


PRESET_DIR = Path(__file__).resolve().parents[2] / "copilot_sdk" / "scoring" / "presets"
SEED_PATH = PRESET_DIR / "dataops_seed.json"
BOOTSTRAP_PATH = PRESET_DIR / "dataops_bootstrap.json"


def load_seed_events() -> list[dict]:
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return raw["events"] if isinstance(raw, dict) else raw


def build_verified_decisions(events: list[dict], preset: DataOpsPreset) -> list[dict]:
    return [
        {
            "category": event["category"],
            "factor_vector": [
                float(event["factors"][factor])
                for factor in preset.shape.factor_names
            ],
            "is_correct": bool(event["is_correct"]),
        }
        for event in events
    ]


def correct_rate(events: list[dict]) -> float:
    assert events
    return sum(1 for event in events if event["is_correct"]) / len(events)


def test_preset_loads():
    preset = DataOpsPreset()

    assert preset.name == "dataops"
    assert preset.shape.n_categories == 6
    assert preset.shape.n_actions == 5
    assert preset.shape.n_factors == 6
    assert len(preset.shape.category_names) == 6
    assert len(preset.shape.action_names) == 5
    assert len(preset.shape.factor_names) == 6
    assert preset.penalty_ratio == 10.0
    assert preset.eta_confirm == 0.05
    assert preset.eta_override == 0.01
    assert preset.temperature == 0.1


def test_preset_in_registry():
    assert "dataops" in PRESET_REGISTRY
    assert PRESET_REGISTRY["dataops"] is DataOpsPreset
    assert PRESET_REGISTRY["dataops"]().name == "dataops"
    assert "trading" in PRESET_REGISTRY
    assert "purchasing" in PRESET_REGISTRY


def test_from_preset_dataops_works(tmp_path):
    db_path = tmp_path / "dataops.db"

    scorer = CompoundingScorer.from_preset("dataops", db_path=str(db_path))

    assert scorer is not None
    scorer.graph_store.close()


def test_seed_data_loads():
    events = load_seed_events()

    assert len(events) == 20
    assert sum(1 for event in events if event["is_correct"]) == 14
    assert sum(1 for event in events if not event["is_correct"]) == 6


def test_seed_covers_all_categories():
    preset = DataOpsPreset()
    events = load_seed_events()

    assert {event["category"] for event in events} == set(preset.shape.category_names)


def test_seed_category_counts_are_as_expected():
    events = load_seed_events()

    assert Counter(event["category"] for event in events) == {
        "pipeline_failure": 4,
        "schema_change": 3,
        "volume_anomaly": 3,
        "quality_anomaly": 4,
        "freshness_violation": 3,
        "transform_drift": 3,
    }


def test_seed_action_counts_are_as_expected():
    preset = DataOpsPreset()
    events = load_seed_events()

    assert Counter(event["action_taken"] for event in events) == {
        "auto_approve": 12,
        "investigate": 3,
        "escalate_to_owner": 2,
        "pause_downstream": 2,
        "refer_to_specialist": 1,
    }
    assert "skip" not in preset.shape.action_names
    assert "skip" not in {event["action_taken"] for event in events}


def test_seed_factors_match_preset():
    preset = DataOpsPreset()
    events = load_seed_events()
    factor_names = set(preset.shape.factor_names)

    for event in events:
        assert event["category"] in preset.shape.category_names
        assert event["action_taken"] in preset.shape.action_names
        assert set(event["factors"]) == factor_names
        assert all(0.0 <= float(value) <= 1.0 for value in event["factors"].values())


def test_bootstrap_centroids_shape():
    assert DataOpsPreset().bootstrap_centroids.shape == (6, 5, 6)


def test_bootstrap_produces_target_correct_action_probability():
    preset = DataOpsPreset()
    events = load_seed_events()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids,
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    action_index = {
        action: index for index, action in enumerate(preset.shape.action_names)
    }
    category_index = {
        category: index for index, category in enumerate(preset.shape.category_names)
    }
    correct_action_probabilities = []

    for event in events:
        factors = np.array(
            [float(event["factors"][factor]) for factor in preset.shape.factor_names],
            dtype=float,
        )
        result = scorer.score(factors, category_index[event["category"]])
        correct_action_probabilities.append(
            float(result.probabilities[action_index[event["action_taken"]]])
        )

    mean_probability = sum(correct_action_probabilities) / len(
        correct_action_probabilities
    )
    assert 0.45 <= mean_probability <= 0.60

    metadata = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    if "mean_confidence" in metadata:
        assert 0.45 <= float(metadata["mean_confidence"]) <= 0.60


def test_recurring_auto_approved_events_are_correct():
    events = load_seed_events()
    subset = [
        event
        for event in events
        if event["action_taken"] == "auto_approve"
        and event["factors"]["recurrence_frequency"] >= 0.6
    ]

    assert len(subset) == 6
    assert sum(1 for event in subset if event["is_correct"]) == 6


def test_first_time_auto_approved_events_are_incorrect():
    events = load_seed_events()
    subset = [
        event
        for event in events
        if event["action_taken"] == "auto_approve"
        and event["factors"]["recurrence_frequency"] < 0.2
    ]

    assert len(subset) == 3
    assert sum(1 for event in subset if event["is_correct"]) == 0


def test_recurrence_frequency_more_predictive_than_source_reliability():
    events = load_seed_events()

    high_recurrence = [
        event for event in events if event["factors"]["recurrence_frequency"] >= 0.6
    ]
    low_recurrence = [
        event for event in events if event["factors"]["recurrence_frequency"] < 0.2
    ]
    high_reliability = [
        event for event in events if event["factors"]["source_reliability"] >= 0.6
    ]
    low_reliability = [
        event for event in events if event["factors"]["source_reliability"] < 0.4
    ]

    recurrence_separation = abs(
        correct_rate(high_recurrence) - correct_rate(low_recurrence)
    )
    reliability_separation = abs(
        correct_rate(high_reliability) - correct_rate(low_reliability)
    )

    assert recurrence_separation > reliability_separation


def test_fingerprint_shows_recurrence_signal_if_stable():
    preset = DataOpsPreset()
    events = load_seed_events()
    result = compute_fingerprint(
        build_verified_decisions(events, preset),
        list(preset.shape.factor_names),
    )
    factors = {factor.name: factor for factor in result.factors}

    assert set(factors) == set(preset.shape.factor_names)
    assert factors["recurrence_frequency"].weight >= factors["source_reliability"].weight
    assert factors["recurrence_frequency"].sigma <= factors["source_reliability"].sigma


def test_end_to_end_score_learn_fingerprint_smoke(tmp_path):
    db_path = tmp_path / "dataops_smoke.db"
    scorer = CompoundingScorer.from_preset("dataops", db_path=str(db_path))
    event = next(
        event for event in load_seed_events() if event["category"] == "pipeline_failure"
    )

    score = scorer.score(event["factors"], event["category"])
    learn = scorer.learn(score.decision_id, event["action_taken"], "confirmed")
    fingerprint = scorer.fingerprint()
    trajectory = scorer.trajectory()

    assert learn.decisions_total == 1
    assert fingerprint.decisions_analyzed == 1
    assert trajectory.decisions_total == 1
    scorer.graph_store.close()
