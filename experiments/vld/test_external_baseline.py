"""External baseline checks, including the original fixture identity control."""
import asyncio
from copy import deepcopy
import json

import numpy as np
import pytest

from experiments.vld import external_baseline as experiment


@pytest.fixture(scope="module")
def result():
    return asyncio.run(experiment.run_experiment())


def test_majority_baseline(result):
    # 30% belongs to the full fixture, not the held-out tail (32.17%).
    historical = result["historical_reproduction"]
    assert abs(historical["majority_category_accuracy"] - .30) <= .02
    assert historical["majority_category_accuracy"] == 163 / 543
    assert historical["vld_category_accuracy"] == 372 / 543
    assert historical["matches_saved_report"] is True
    assert result["majority"]["category_accuracy"] == 46 / 143
    assert result["majority"]["category_accuracy"] < .35


def check_metrics(row):
    for key in ("category_accuracy", "action_accuracy", "fixture_action_accuracy"):
        assert np.isfinite(row[key])
        assert 0 <= row[key] <= 1
    assert row["n"] == 143
    assert 0 <= row["saves"] <= 143
    assert 0 <= row["hurts"] <= 143


def test_linucb_runs(result):
    check_metrics(result["linucb"])


def test_rf_runs(result):
    check_metrics(result["rf"])


def test_svm_runs(result):
    check_metrics(result["svm"])


def test_fi_routing_quality_bounded(result):
    row = result["fi_routing"]
    check_metrics(row)
    assert 0 <= row["routing_quality"] <= 1
    assert row["actual_reads"] == 286
    assert row["routing_quality"] == row["informative_reads"] / row["actual_reads"]
    assert len(set(row["selected_dimensions"])) == 2
    assert sum(row["feature_importances"].values()) == pytest.approx(1)
    assert "structural proxy" in row["routing_quality_definition"]


def test_all_baselines_deterministic(result):
    repeated = asyncio.run(experiment.run_experiment())
    assert json.dumps(result, sort_keys=True, allow_nan=False) == json.dumps(repeated, sort_keys=True, allow_nan=False)


def test_disjoint_ordered_split(result):
    data = experiment.load_data()
    assert (result["fixture_size"], result["train_size"], result["test_size"]) == (543, 400, 143)
    train_ids = result["train_alert_ids"]
    test_ids = [row["alert_id"] for row in result["test_decisions"]]
    assert not set(train_ids) & set(test_ids)
    assert train_ids + test_ids == [a["alert_id"] for a in data.alerts]
    assert all(not {"category", "alert_type", "category_index"} & set(a) for a in data.alerts)


def test_heldout_labels_do_not_affect_predictions(result, monkeypatch):
    # Changing evaluation truth must affect metrics only, never policy choices.
    original = experiment.load_data
    def changed_labels():
        data = original()
        data.y_category[400:] = (data.y_category[400:] + 1) % 6
        data.y_action[400:] = (data.y_action[400:] + 1) % 4
        data.y_fixture[400:] = (data.y_fixture[400:] + 1) % 4
        return data
    monkeypatch.setattr(experiment, "load_data", changed_labels)
    modified = asyncio.run(experiment.run_experiment())
    assert [row["predictions"] for row in result["test_decisions"]] == [row["predictions"] for row in modified["test_decisions"]]
    assert modified["fi_routing"]["feature_importances"] == result["fi_routing"]["feature_importances"]


def test_saved_predictions_recompute_metrics(result):
    rows = result["test_decisions"]
    for name in experiment.METHODS:
        check_metrics(result[name])
        correct = [row["predictions"][name]["action"] == row["action_teacher"] for row in rows]
        before = [row["single_pass_action"] == row["action_teacher"] for row in rows]
        fixture = [row["predictions"][name]["action"] == row["action_fixture"] for row in rows]
        categories = [row["predictions"][name]["category"] == row["category_truth"] for row in rows]
        assert result[name]["action_accuracy"] == sum(correct) / 143
        assert result[name]["fixture_action_accuracy"] == sum(fixture) / 143
        assert result[name]["category_accuracy"] == sum(categories) / 143
        assert result[name]["saves"] == sum(c and not b for c,b in zip(correct,before))
        assert result[name]["hurts"] == sum(not c and b for c,b in zip(correct,before))


def test_linucb_only_selected_arm_updates_and_eval_frozen():
    learner = experiment.LinUCB(4)
    x = np.ones(6)
    arm = learner.select(x)
    learner.fit(np.asarray([x]), np.asarray([arm]))
    assert np.array_equal(learner.a[arm], np.eye(6) + np.outer(x,x))
    assert np.array_equal(learner.b[arm], x)
    for other in set(range(4)) - {arm}:
        assert np.array_equal(learner.a[other], np.eye(6))
        assert not learner.b[other].any()
    before = deepcopy((learner.a, learner.b))
    learner.predict(np.asarray([x, x / 2]))
    assert np.array_equal(learner.a, before[0])
    assert np.array_equal(learner.b, before[1])


def test_fixture_sources_unchanged(result):
    for path, expected in result["sources"].items():
        assert experiment.sha(experiment.ROOT / path) == expected
