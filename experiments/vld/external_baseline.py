"""External baselines on the exact 543-alert SOC paper fixture.

Usage: python -B -m experiments.vld.external_baseline --output experiments/vld/results/external_baseline.json

No app startup, graph connection, source modification, or fixture generation.
All policies see six surface factors. Category and action prediction are separate
supervised tasks; action targets are the nearest exported centroid within the
fixture's true category. Historical vote-label action accuracy is also reported.
The ordered 400/143 split is intentionally not shuffled or tuned.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

sys.dont_write_bytecode = True
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
SOC_ROOT = ROOT.parent / "gen-ai-roi-demo-v4-v50" / "backend"
FIXTURE = SOC_ROOT / "support/setup/zero_day_decisions_v5.json"
GEOMETRY = ROOT / "real_centroids_v1.json"
HISTORICAL = SOC_ROOT / "data/rho_measurement_report.json"
DEFAULT_OUTPUT = ROOT / "experiments/vld/results/external_baseline.json"
SEED, TRAIN_SIZE = 42, 400
METHODS = ("majority", "linucb", "rf", "svm", "fi_routing", "vld")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def soc_runtime():
    """Import the original read-only fixture adapters and investigation pipeline.

    Do not call measure_rho.run_measurement: it regenerates existing output files.
    """
    backend = str(SOC_ROOT)
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from app.domains.soc.config import SOCDomainConfig, SOC_CATEGORIES, SCORER_ACTIONS
    from app.services.investigation_loop import InvestigationLoop
    from app.services.investigation_router import InvestigationRouter
    from app.services.investigation_patterns import PATTERN_REGISTRY
    spec = importlib.util.spec_from_file_location("external_soc_measure", SOC_ROOT / "scripts/measure_rho.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return SimpleNamespace(measure=module, config=SOCDomainConfig, categories=SOC_CATEGORIES,
                           actions=SCORER_ACTIONS, loop=InvestigationLoop,
                           router=InvestigationRouter, patterns=PATTERN_REGISTRY)


def load_data():
    runtime = soc_runtime()
    fixture = runtime.measure.load_fixture(FIXTURE)
    vectors = runtime.measure.vectors_by_alert(fixture["decisions"])
    votes = runtime.measure.action_truth_by_alert(fixture["decisions"])
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))["copilots"]["soc"]
    categories, actions = geometry["category_names"], geometry["action_names"]
    if categories != runtime.categories or actions != runtime.actions:
        raise ValueError("SOC geometry order differs from the historical pipeline")
    mu = np.asarray([geometry["all_category_mu"][category] for category in categories], dtype=float)
    alerts = [a for a in fixture["alerts"] if a.get("category") in categories and a.get("alert_id") in vectors]
    if len(alerts) != 543 or len({a["alert_id"] for a in alerts}) != 543:
        raise ValueError("Expected exactly 543 distinct eligible fixture alerts")
    x = np.asarray([vectors[a["alert_id"]] for a in alerts], dtype=float)
    if x.shape != (543, 6) or not np.isfinite(x).all() or mu.shape != (6, 4, 6):
        raise ValueError("Invalid fixture vectors or exported SOC geometry")
    y_category = np.asarray([categories.index(a["category"]) for a in alerts])
    # Teacher receives the category label only to define targets, never as a feature.
    y_action = np.argmin(np.linalg.norm(mu[y_category] - x[:, None, :], axis=2), axis=1)
    y_fixture = np.asarray([actions.index(votes[a["alert_id"]]) for a in alerts])
    stripped = [{k: v for k, v in a.items() if k not in {"category", "alert_type", "category_index"}} for a in alerts]
    scorer = SimpleNamespace(centroids=mu.copy(), mu=mu.copy(), categories=categories,
                             actions=actions, tau=float(geometry["tau"]))
    return SimpleNamespace(runtime=runtime, fixture=fixture, alerts=stripped, x=x,
                           y_category=y_category, y_action=y_action, y_fixture=y_fixture,
                           geometry=geometry, scorer=scorer, vectors=vectors)


class LinUCB:
    """Disjoint LinUCB: ridge=1, alpha=1; update only the selected arm.

    Training rewards are simulated 0/1 correctness, not logged bandit feedback.
    Evaluation freezes parameters and retains the requested UCB selection rule.
    Li et al. (2010): https://arxiv.org/abs/1003.0146
    """
    def __init__(self, n_actions: int, n_features: int = 6, alpha: float = 1.0):
        self.a = np.repeat(np.eye(n_features)[None, :, :], n_actions, axis=0)
        self.b = np.zeros((n_actions, n_features))
        self.alpha = alpha

    def select(self, x):
        theta = np.linalg.solve(self.a, self.b[..., None])[..., 0]
        uncertainty = np.linalg.solve(self.a, np.broadcast_to(x, self.b.shape)[..., None])[..., 0]
        scores = theta @ x + self.alpha * np.sqrt(np.maximum(uncertainty @ x, 0.0))
        return int(np.argmax(scores))  # stable index-order tie breaking

    def fit(self, x, y):
        for vector, target in zip(x, y):
            arm = self.select(vector)
            reward = float(arm == int(target))
            self.a[arm] += np.outer(vector, vector)
            self.b[arm] += reward * vector
        return self

    def predict(self, x):
        return np.asarray([self.select(vector) for vector in x])


def classification_metrics(categories, actions, data, indices, single):
    ycat, yact, yfixture = data.y_category[indices], data.y_action[indices], data.y_fixture[indices]
    correct, base = np.asarray(actions) == yact, np.asarray(single) == yact
    fixture_correct, fixture_base = np.asarray(actions) == yfixture, np.asarray(single) == yfixture
    return {"category_accuracy": float(np.mean(np.asarray(categories) == ycat)),
            "action_accuracy": float(np.mean(correct)),
            "fixture_action_accuracy": float(np.mean(fixture_correct)),
            "saves": int(np.sum(correct & ~base)), "hurts": int(np.sum(~correct & base)),
            "fixture_saves": int(np.sum(fixture_correct & ~fixture_base)),
            "fixture_hurts": int(np.sum(~fixture_correct & fixture_base)),
            "n": len(indices)}


def mode(values):
    counts = Counter(int(v) for v in values)
    return min(counts, key=lambda key: (-counts[key], key))


async def run_experiment() -> dict[str, Any]:
    data = load_data()
    rt = data.runtime
    categories, actions = data.scorer.categories, data.scorer.actions
    train, test = np.arange(TRAIN_SIZE), np.arange(TRAIN_SIZE, len(data.alerts))
    router = rt.router(rt.patterns, L_max=3)
    provider = rt.measure.FixtureFactorProvider(data.vectors)
    graph = rt.measure.FixtureGraphStore({a["alert_id"]: a for a in data.alerts})
    distances = np.linalg.norm(data.scorer.centroids[None, :, :, :] - data.x[:, None, None, :], axis=3)
    flat = distances.reshape(len(data.x), -1).argmin(axis=1)
    single_cat, single_action = flat // len(actions), flat % len(actions)
    predictions = {}
    majority_cat = mode(data.y_category[train])
    per_category_action = {c: mode(data.y_action[train][data.y_category[train] == c]) for c in range(len(categories))}
    predictions["majority"] = (np.full(len(test), majority_cat), np.full(len(test), per_category_action[majority_cat]))
    predictions["linucb"] = (LinUCB(6).fit(data.x[train], data.y_category[train]).predict(data.x[test]),
                              LinUCB(4).fit(data.x[train], data.y_action[train]).predict(data.x[test]))
    fitted = {}
    for name, factory in (
        ("rf", lambda: RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=1)),
        ("svm", lambda: LinearSVC(random_state=SEED, dual="auto", max_iter=10000)),
    ):
        category_model = factory().fit(data.x[train], data.y_category[train])
        action_model = factory().fit(data.x[train], data.y_action[train])
        fitted[name] = action_model
        predictions[name] = (category_model.predict(data.x[test]), action_model.predict(data.x[test]))

    importances = fitted["rf"].feature_importances_
    dims = sorted(range(6), key=lambda d: (-float(importances[d]), d))[:2]
    factor_names = data.geometry["factor_names"]
    # This fixture has category-pattern evidence, not independent dimension reads.
    # Resolve each dimension to the most common TRAINING category whose registered
    # pattern enriches it. Project only that coordinate from the returned vector.
    category_counts = Counter(data.y_category[train].tolist())
    dimension_patterns = {}
    for dimension in dims:
        eligible = [c for c, name in enumerate(categories) if factor_names[dimension] in rt.patterns[name].enriched_factors]
        dimension_patterns[dimension] = min(eligible, key=lambda c: (-category_counts[c], c))
    fi_categories, fi_actions, fi_rows = [], [], []
    informative = 0
    for i in test:
        vector = data.x[i].copy()
        reads = []
        for dimension in dims:
            category = categories[dimension_patterns[dimension]]
            evidence = await rt.patterns[category].execute(data.alerts[i], graph)
            vector[dimension] = np.clip((data.x[i, dimension] + evidence["vld_factor_vector"][dimension]) / 2.0, 0., 1.)
            relevant = factor_names[dimension] in rt.patterns[categories[data.y_category[i]]].enriched_factors
            informative += int(relevant)
            reads.append({"dimension": factor_names[dimension], "pattern": category,
                          "structurally_relevant": bool(relevant)})
        score = router.score_best_from_centroids(vector, data.scorer)
        fi_categories.append(score.category_index)
        fi_actions.append(score.action_index)
        fi_rows.append(reads)
    predictions["fi_routing"] = (np.asarray(fi_categories), np.asarray(fi_actions))

    vld_cat, vld_actions, b2_actions, b2_final_cat, traces, history_actions = [], [], [], [], [], []
    # Run original L_max=3 on all alerts to independently reproduce the paper.
    for i, alert in enumerate(data.alerts):
        result = await rt.loop(data.scorer, router, provider, L_max=3, residual_threshold=0.0).investigate(alert, graph)
        history_actions.append(actions.index(result.action))
        if i < TRAIN_SIZE:
            continue
        route = router.route_decision(data.x[i], data.scorer, set(), alert_context=alert)
        vld_cat.append(categories.index(route.selected_category))
        vld_actions.append(actions.index(result.action))
        # Matched two-read reference supplements, not replaces, original §9 policy.
        b2 = await rt.loop(data.scorer, rt.router(rt.patterns, L_max=2), provider,
                           L_max=2, residual_threshold=0.0).investigate(alert, graph)
        b2_actions.append(actions.index(b2.action))
        b2_final_cat.append(categories.index(b2.category))
        traces.append({"patterns": [step.pattern for step in result.trace], "steps": result.steps,
                       "b2_steps": b2.steps, "final_category": result.category,
                       "halt_reason": result.halt_reason})
    predictions["vld"] = (np.asarray(vld_cat), np.asarray(vld_actions))
    result = {"fixture_size": len(data.alerts), "train_size": len(train), "test_size": len(test)}
    for name, (cp, ap) in predictions.items():
        result[name] = classification_metrics(cp, ap, data, test, single_action[test])
    result["single_pass"] = classification_metrics(single_cat[test], single_action[test], data, test, single_action[test])
    result["vld_b2"] = classification_metrics(vld_cat, b2_actions, data, test, single_action[test])
    result["vld_b2"]["final_category_accuracy"] = float(np.mean(np.asarray(b2_final_cat) == data.y_category[test]))
    result["vld"]["final_category_accuracy"] = float(np.mean([trace["final_category"] == categories[data.y_category[i]] for trace, i in zip(traces, test)]))
    result["vld"]["actual_reads"] = sum(row["steps"] for row in traces)
    result["vld_b2"]["actual_reads"] = sum(row["b2_steps"] for row in traces)
    for key in ("vld", "vld_b2"):
        limit = 3 if key == "vld" else 2
        relevant_reads = sum(sum(pattern == categories[data.y_category[i]] for pattern in row["patterns"][:limit]) for i, row in zip(test, traces))
        result[key]["routing_quality"] = relevant_reads / result[key]["actual_reads"]
        result[key]["routing_quality_definition"] = "category-matching branch reads / actual branch reads; structural proxy"
    result["fi_routing"].update({"routing_quality": informative / (len(test) * 2),
        "informative_reads": informative, "actual_reads": len(test) * 2,
        "feature_importances": dict(zip(factor_names, map(float, importances))),
        "selected_dimensions": [factor_names[d] for d in dims],
        "dimension_pattern_mapping": {factor_names[d]: categories[c] for d, c in dimension_patterns.items()},
        "routing_quality_definition": "selected dimensions present in the true-category pattern enriched_factors / actual dimension reads; structural proxy, not measured action utility"})
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    original_scorer = rt.config().build_profile_scorer()
    original_mu = np.asarray(original_scorer.centroids)
    recovery = float(np.mean(single_cat == data.y_category))
    history_acc = float(np.mean(np.asarray(history_actions) == data.y_fixture))
    prior_accuracy = float(np.mean(single_action == data.y_fixture))
    full_majority = float(np.mean(data.y_category == mode(data.y_category)))
    result["historical_reproduction"] = {
        "n": len(data.alerts), "category_counts": dict(sorted(Counter(categories[c] for c in data.y_category).items())),
        "majority_category": categories[mode(data.y_category)], "majority_category_accuracy": full_majority,
        "vld_category_accuracy": recovery, "single_pass_fixture_action_accuracy": prior_accuracy,
        "vld_fixture_action_accuracy": history_acc,
        "export_vs_original_centroids_max_abs_difference": float(np.max(np.abs(data.scorer.centroids - original_mu))),
        "matches_saved_report": all(abs(a-b) < 1e-12 for a,b in [(full_majority,historical["rho_majority"]),
            (recovery,historical["rho_vld"]),(prior_accuracy,historical["single_pass_accuracy"]),(history_acc,historical["vld_action_accuracy"])])}
    result["label_diagnostics"] = {
        "teacher_vs_single_pass_agreement_test": float(np.mean(data.y_action[test] == single_action[test])),
        "teacher_vs_fixture_agreement_test": float(np.mean(data.y_action[test] == data.y_fixture[test])),
        "teacher_vs_fixture_agreement_all": float(np.mean(data.y_action == data.y_fixture)),
    }
    result["recommended_paper_claim"] = (
        f"On the ordered 400/143 split of the synthetic SOC fixture, RF recovered categories at "
        f"{result['rf']['category_accuracy']:.2%}, versus {result['vld']['category_accuracy']:.2%} for the "
        f"unchanged CI-VLD router and {result['majority']['category_accuracy']:.2%} for training-majority routing; "
        f"against historical fixture action labels, RF and CI-VLD scored "
        f"{result['rf']['fixture_action_accuracy']:.2%} and {result['vld']['fixture_action_accuracy']:.2%}, "
        "respectively; these single-split point estimates do not establish statistical superiority or production utility."
    )
    result["protocol"] = {
        "seed": SEED, "split": "first 400 eligible alerts train; last 143 test; original fixture order; no shuffle",
        "category_target": "fixture alert category; never supplied as a prediction feature",
        "action_target": "nearest exported action centroid within the fixture true category, L2 distance; model-derived pseudo-label, not verified truth",
        "fixture_action_target": "majority action vote among correct fixture decision rows, exactly as measure_rho.py",
        "majority": "training-majority category; training-majority action within that predicted category; no gold test category access",
        "category_vs_action_models": "independent 6-arm category and 4-arm action LinUCB; independent RF/SVM classifiers per task",
        "linucb": "alpha=1; ridge=1; six raw factors; sequential one-pass training with selected-arm simulated binary feedback; frozen evaluation with UCB; index-order ties",
        "rf": "100 trees, random_state=42, n_jobs=1; default remaining hyperparameters",
        "svm": "LinearSVC random_state=42, dual=auto, max_iter=10000; raw [0,1] factors; no tuning",
        "fi_routing": "top-2 action-RF dimensions; fixed train-majority eligible pattern mapping; execute real fixture pattern and average selected coordinate with surface; unused coordinates remain surface",
        "vld": "original SOC InvestigationLoop, L_max=3, residual_threshold=0, default reextract and max_flips=2; initial route used for category accuracy",
        "vld_b2": "same SOC pipeline, L_max=2; matched read-count sensitivity, branch and dimension reads still differ in contents",
        "evaluation_updates": False, "evidence_tier": "REAL_COMPONENT; exported preset geometry plus deterministic synthetic fixture",
        "geometry_provenance": data.geometry["provenance"],
        "caveats": [
            "The locally available paper is ci_rgi_impact_core_v6.md; requested v7_3 was not found.",
            "Original 30.02% is a full-fixture majority selected on that same fixture; held-out majority is 46/143=32.17%, outside 30% +/-2pp.",
            "Classifier action accuracy measures agreement with scorer-derived targets; fixture_action_accuracy uses the historical paper labels.",
            "All action learners train on the requested scorer-derived labels, not historical fixture votes; fixture_action_accuracy is a separate evaluation of those same predictions.",
            "On this test split the teacher labels coincide with single-pass actions, making positive teacher-label saves impossible; use fixture_action_accuracy for the paper's action-outcome comparison.",
            "External classifiers learn from 400 alerts; the original VLD category-routing pipeline has fixed geometry and no K-training interface, and is preserved unchanged.",
            "Fixture evidence vectors are hand-set per registered category pattern; no independent operational informative-read labels exist.",
            "FI dimension routing uses an explicit new projection adapter; routing-quality proxies and read contents differ from the original VLD branch loop.",
            "Single split, single seed; no hyperparameter tuning or external customer outcome generalization claim."
        ],
        "references": ["https://arxiv.org/abs/1003.0146", "https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.RandomForestClassifier.html",
                       "https://scikit-learn.org/1.5/modules/generated/sklearn.svm.LinearSVC.html"],
        "versions": {"numpy": np.__version__, "sklearn": sklearn.__version__}}
    result["sources"] = {str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else Path("..") / path.relative_to(ROOT.parent)): sha(path)
        for path in [FIXTURE, GEOMETRY, HISTORICAL, SOC_ROOT / "scripts/measure_rho.py",
                     SOC_ROOT / "app/services/investigation_loop.py", SOC_ROOT / "app/services/investigation_router.py",
                     SOC_ROOT / "app/services/investigation_patterns.py", ROOT / "copilot_sdk/scoring/investigation.py",
                     ROOT / "copilot_sdk/backend/investigation_router.py", ROOT / "copilot_sdk/scoring/scorer.py"]}
    result["train_category_counts"] = dict(sorted(Counter(categories[c] for c in data.y_category[train]).items()))
    result["test_category_counts"] = dict(sorted(Counter(categories[c] for c in data.y_category[test]).items()))
    result["train_alert_ids"] = [data.alerts[i]["alert_id"] for i in train]
    result["test_decisions"] = [{"alert_id": data.alerts[i]["alert_id"],
        "category_truth": categories[data.y_category[i]], "action_teacher": actions[data.y_action[i]],
        "action_fixture": actions[data.y_fixture[i]], "single_pass_action": actions[single_action[i]],
        "predictions": {name: {"category": categories[int(cp[j])], "action": actions[int(ap[j])]}
                        for name,(cp,ap) in predictions.items()},
        "fi_reads": fi_rows[j], "vld_trace": traces[j]} for j,i in enumerate(test)]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = asyncio.run(run_experiment())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    for name in ("single_pass", *METHODS, "vld_b2"):
        row = result[name]
        print(f"{name:12s} category={row['category_accuracy']:.4%} teacher-action={row['action_accuracy']:.4%} fixture-action={row['fixture_action_accuracy']:.4%} saves/hurts={row['saves']}/{row['hurts']}")
    print("Historical reproduction:", result["historical_reproduction"])
    print("Held-out majority is 32.17%; the original full-fixture control is 30.02%.")
    print("Output:", args.output)


if __name__ == "__main__":
    main()
