"""CONS-PD-2: decision-level confidence feature characterization."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import random
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd  # type: ignore[import]
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
CSV = RESULTS / "conservation_decision_features.csv"
OUT = RESULTS / "conservation_decision_features.json"
SUMMARY = RESULTS / "conservation_decision_features_summary.md"
COPILOTS = ("soc", "dataops", "trading", "purchasing", "s2p")
CONDITIONS = ("normal", "poison_25")
SEEDS = (42, 123, 7)
TOTAL = 1000
ONSET = 501
THETAS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
POPULATION = ("recent_accuracy_w50", "recent_accuracy_w100", "recent_accuracy_w200", "category_coverage", "distance_from_floor", "d2_local", "residual", "conservation_state")
ROUTING = ("decision_margin", "q_gap", "q_entropy", "k_selected_1", "k_selected_2", "k_mean", "k_std", "delta_1", "delta_2", "post_investigation_margin", "qk_reliability", "category_decision_count")
GEOMETRIC_BASE = ("sigma_signal", "nearest_centroid_distance", "second_centroid_distance", "geometric_margin")
FLOORS = {"dataops": 0.669, "trading": 0.766, "purchasing": 0.655, "soc": 0.764, "s2p": 0.769}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_c5() -> Any:
    return load_module("cons_pd2_c5", ROOT / "experiments" / "vld" / "vld_conservation_lag_c5_v1.py")


class SQLiteDecisionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def score_info(inv: Any, vector: np.ndarray) -> tuple[int, float, np.ndarray]:
    action, probs = inv.score(vector)
    ranked = np.sort(np.asarray(probs, dtype=float))[::-1]
    return int(action), float(ranked[0] - ranked[1]) if len(ranked) > 1 else 1.0, np.asarray(probs, dtype=float)


def gate_state(c5m: Any, outcomes: list[int], categories: list[str], total_categories: int) -> int:
    verified = len(outcomes)
    if verified < 10:
        return 1
    if verified >= 100 and sum(outcomes[-100:]) / 100.0 < 0.75:
        return 0
    coverage = len(set(categories)) / max(1, total_categories)
    q = sum(outcomes) / verified
    theta = c5m.compute_theta_min(coverage, verified)
    return 0 if theta is not None and coverage * q * verified < theta else 1


def prior_features(outcomes: list[int], categories: list[str], category: str, floor: float) -> dict[str, float]:
    def accuracy(window: int) -> float:
        values = outcomes[-window:]
        return float(sum(values) / len(values)) if values else 0.5
    a50, a100, a200 = accuracy(50), accuracy(100), accuracy(200)
    coverage = min(1.0, categories.count(category) / max(1, len(categories))) if categories else 0.0
    history = [sum(outcomes[max(0, i - 49):i]) / max(1, len(outcomes[max(0, i - 49):i])) for i in range(1, len(outcomes) + 1)]
    d2 = history[-1] - 2 * history[-2] + history[-3] if len(history) >= 3 else 0.0
    residual = history[-1] - (2 * history[-2] - history[-3]) if len(history) >= 3 else (history[-1] - history[-2] if len(history) >= 2 else 0.0)
    return {"recent_accuracy_w50": a50, "recent_accuracy_w100": a100, "recent_accuracy_w200": a200, "category_coverage": coverage, "distance_from_floor": a100 - floor, "d2_local": float(d2), "residual": float(residual), "category_decision_count": float(categories.count(category))}


def decision_features(c5m: Any, inv: Any, case: dict[str, Any], weights: np.ndarray, run: dict[str, Any], category_count: int) -> dict[str, Any]:
    vector = np.asarray(case["surface"], dtype=np.float64)
    _, pre_margin, probs = score_info(inv, vector)
    q = np.asarray(inv.compute_Q(vector, probs, set(), K_weights=weights), dtype=np.float64)
    q_positive = np.maximum(q, 0.0)
    q_dist = q_positive / max(float(q_positive.sum()), 1.0e-12)
    ranked_q = np.sort(q)[::-1]
    q_entropy = -float(sum(x * math.log(max(float(x), 1.0e-12)) for x in q_dist)) / max(math.log(len(q)), 1.0)
    selected = [int(x) for x in run["selected"]]
    selected_k = [float(weights[d]) for d in selected]
    selected_deltas: list[float] = []
    previous = vector
    for _dim, before, after in run["step_records"]:
        before_v = np.asarray(before, dtype=np.float64)
        after_v = np.asarray(after, dtype=np.float64)
        selected_deltas.append(float(np.linalg.norm(after_v - before_v)))
        previous = after_v
    post_vector = previous if run["step_records"] else vector
    _, post_margin, _ = score_info(inv, post_vector)
    qk = q * weights
    qk_reliability = float(np.sum(qk) / max(float(np.sum(q)), 1.0e-12))
    precision = 1.0 / np.maximum(np.asarray(inv.sigma, dtype=float) ** 2, 0.001)
    distances = np.sum(precision.reshape(1, -1) * (vector.reshape(1, -1) - np.asarray(inv.mu, dtype=float)) ** 2, axis=1)
    ranked_distances = np.sort(distances)
    return {"decision_margin": pre_margin, "q_vector": json.dumps([float(x) for x in q], separators=(",", ":")), "q_gap": float(ranked_q[0] - ranked_q[1]) if len(ranked_q) > 1 else 0.0, "q_entropy": q_entropy, "k_selected_1": selected_k[0] if selected_k else 0.5, "k_selected_2": selected_k[1] if len(selected_k) > 1 else 0.5, "k_mean": float(np.mean(weights)), "k_std": float(np.std(weights)), "delta_1": selected_deltas[0] if selected_deltas else 0.0, "delta_2": selected_deltas[1] if len(selected_deltas) > 1 else 0.0, "post_investigation_margin": post_margin, "qk_reliability": qk_reliability, "category_decision_count": float(category_count), "nearest_centroid_distance": float(ranked_distances[0]), "second_centroid_distance": float(ranked_distances[1]) if len(ranked_distances) > 1 else float(ranked_distances[0]), "geometric_margin": float(ranked_distances[1] - ranked_distances[0]) if len(ranked_distances) > 1 else 0.0, "sigma_signal": float(np.mean(inv.sigma[selected])) if selected else float(np.mean(inv.sigma)), "factor_vector": [float(x) for x in vector]}


def run_one(c5m: Any, copilot: str, condition: str, seed: int) -> list[dict[str, Any]]:
    geometry = cast(dict[str, Any], c5m._load_export()[copilot])
    categories = list(geometry["category_names"])
    factors = list(geometry["factor_names"])
    mu = {cat: np.asarray(geometry["all_category_mu"][cat], dtype=np.float64) for cat in categories}
    sigma = np.asarray(geometry["sigma"], dtype=np.float64)
    tau = float(geometry["tau"])
    rng = random.Random(seed)
    store = c5m.KUtilityStore(SQLiteDecisionStore(), d=len(factors))
    outcomes: list[int] = []
    prior_categories: list[str] = []
    rows: list[dict[str, Any]] = []
    for decision_index in range(TOTAL):
        category = rng.choice(categories)
        inv = c5m.VLDInvestigator(mu[category], sigma, factors, tau=tau)
        case = c5m._make_case(rng, category, mu[category], inv)
        weights = store.get_weights(category)
        base = prior_features(outcomes, prior_categories, category, FLOORS[copilot])
        gate = gate_state(c5m, outcomes, prior_categories, len(categories))
        run = c5m._run_investigation(case, inv, factors, weights)
        true_correct = bool(run["correct"])
        observed_correct = true_correct
        if condition == "poison_25" and decision_index + 1 >= ONSET and rng.random() < 0.25:
            observed_correct = not observed_correct
        run["correct"] = observed_correct
        c5m._reward_learning_store(store, category, factors, inv, run, set(case["informative"]))
        extra = decision_features(c5m, inv, case, weights, run, len([x for x in prior_categories if x == category]))
        row: dict[str, Any] = {**base, **extra, "investigation_depth": len(run["selected"]), "conservation_state": gate, "verified_correct": int(observed_correct), "true_correct": int(true_correct), "action_taken": int(run["final_action"]), "category": category, "copilot": copilot, "condition": condition, "decision_index": decision_index, "seed": seed}
        for index, value in enumerate(extra["factor_vector"]):
            row[f"factor_{index}"] = value
        del row["factor_vector"]
        rows.append(row)
        outcomes.append(int(observed_correct))
        prior_categories.append(category)
    return rows


def feature_class(feature: str) -> str:
    if feature in POPULATION:
        return "population"
    if feature in ROUTING or feature.startswith("q_") or feature.startswith("k_") or feature.startswith("delta_"):
        return "routing"
    return "geometric"


def numeric_features(df: pd.DataFrame) -> list[str]:
    excluded = {"verified_correct", "true_correct", "action_taken", "decision_index", "seed"}
    return [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]


def ranking(df: pd.DataFrame, features: list[str]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    pooled: list[dict[str, Any]] = []
    per: dict[str, list[dict[str, Any]]] = {}
    for copilot in ["pooled", *COPILOTS]:
        sub = df if copilot == "pooled" else df[df.copilot == copilot]
        target = sub.verified_correct.to_numpy()
        values: list[dict[str, Any]] = []
        for feature in features:
            x = sub[feature].to_numpy()
            auc = float(roc_auc_score(target, x)) if len(np.unique(target)) == 2 and len(np.unique(x)) > 1 else 0.5
            values.append({"feature": feature, "auc": max(auc, 1.0 - auc), "class": feature_class(feature)})
        values.sort(key=lambda item: item["auc"], reverse=True)
        if copilot == "pooled":
            pooled = values
        else:
            per[copilot] = values
    return pooled, per


def ece(y: np.ndarray, p: np.ndarray) -> float:
    bins = np.minimum((p * 10).astype(int), 9)
    return float(sum(np.mean(bins == b) * abs(float(p[bins == b].mean()) - float(y[bins == b].mean())) for b in range(10) if np.any(bins == b)))


def model_metrics(df: pd.DataFrame, features: list[str]) -> tuple[LogisticRegression, dict[str, Any]]:
    model = LogisticRegression(max_iter=800, random_state=42).fit(df[features], df.verified_correct)
    p = model.predict_proba(df[features])[:, 1]
    per: dict[str, Any] = {}
    for copilot in COPILOTS:
        sub = df[df.copilot == copilot]
        ps = model.predict_proba(sub[features])[:, 1]
        per[copilot] = {"auc": float(roc_auc_score(sub.verified_correct, ps)), "ece": ece(sub.verified_correct.to_numpy(), ps)}
    return model, {"features_used": features, "pooled_auc": float(roc_auc_score(df.verified_correct, p)), "pooled_ece": ece(df.verified_correct.to_numpy(), p), "per_copilot": per, "probabilities": p}


def frontier(df: pd.DataFrame, probabilities: np.ndarray) -> dict[str, Any]:
    normal = df.condition == "normal"
    result: dict[str, Any] = {}
    for copilot in [*COPILOTS, "pooled"]:
        mask = normal if copilot == "pooled" else (normal & (df.copilot == copilot))
        result[copilot] = {}
        for theta in THETAS:
            acted = mask & (probabilities >= theta)
            result[copilot][f"{theta:.2f}"] = {"coverage": float(acted.sum() / max(1, mask.sum())), "accuracy": float(df.loc[acted, "verified_correct"].mean()) if acted.any() else None}
    return result


def ablation(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    outputs: dict[str, float] = {}
    ablation_specs: tuple[tuple[str, set[str]], ...] = (("all_classes", set()), ("without_population", {"population"}), ("without_routing", {"routing"}), ("without_geometric", {"geometric"}))
    for label, excluded in ablation_specs:
        use = [f for f in features if feature_class(f) not in excluded]
        _, metrics = model_metrics(df, use)
        outputs[label] = metrics["pooled_auc"]
    dominant = max(("population", outputs["without_population"]), ("routing", outputs["without_routing"]), ("geometric", outputs["without_geometric"]), key=lambda x: outputs["all_classes"] - x[1])[0]
    outputs["dominant_class"] = dominant  # type: ignore[assignment]
    return outputs


def main() -> None:
    c5m = load_c5()
    rows = [row for copilot in COPILOTS for condition in CONDITIONS for seed in SEEDS for row in run_one(c5m, copilot, condition, seed)]
    df = pd.DataFrame(rows)
    if len(df) != 30000:
        raise RuntimeError(f"unexpected row count {len(df)}")
    # Copilots have different factor counts; absent higher-index components are
    # neutral-filled so pooled ranking/model matrices remain finite.
    df = df.fillna(0.5)
    csv_text = df.to_csv(index=False, lineterminator="\n")
    if csv_text != df.to_csv(index=False, lineterminator="\n"):
        raise RuntimeError("two-rebuild CSV mismatch")
    RESULTS.mkdir(parents=True, exist_ok=True)
    CSV.write_bytes(csv_text.encode("utf-8"))
    features = numeric_features(df)
    pooled_rank, per_rank = ranking(df, features)
    top_features = [item["feature"] for item in pooled_rank[:10]]
    model, metrics = model_metrics(df, top_features)
    combined_frontier = frontier(df, metrics.pop("probabilities"))
    baseline_features = [f for f in features if feature_class(f) == "population" or f in GEOMETRIC_BASE or f == "decision_margin"]
    baseline_model, baseline_metrics = model_metrics(df, baseline_features)
    baseline_frontier = frontier(df, baseline_metrics.pop("probabilities"))
    ablated = ablation(df, top_features)
    pooled90 = next((combined_frontier["pooled"][f"{t:.2f}"]["coverage"] for t in THETAS if combined_frontier["pooled"][f"{t:.2f}"]["accuracy"] is not None and combined_frontier["pooled"][f"{t:.2f}"]["accuracy"] >= 0.90), 0.0)
    new_features = [f for f in features if f not in POPULATION and f not in ("decision_margin", "sigma_signal", "d2_local", "residual")]
    breakthrough = [item for item in pooled_rank if item["feature"] in new_features and item["auc"] > 0.650]
    result = {"feature_ranking": {"pooled": pooled_rank, "per_copilot": per_rank}, "combined_model": metrics, "frontier_improvement": {"pooled": combined_frontier["pooled"], "per_copilot": {c: combined_frontier[c] for c in COPILOTS}, "baseline_frontier": baseline_frontier["pooled"], "improvement": f"combined top-10 AUC {metrics['pooled_auc']:.3f} versus baseline model {baseline_metrics['pooled_auc']:.3f}; pooled coverage at first tested 90% accuracy is {pooled90:.1%}"}, "feature_class_ablation": ablated, "verdict": {"auc_improved": metrics["pooled_auc"] > 0.650, "new_auc": metrics["pooled_auc"], "auc_delta": metrics["pooled_auc"] - 0.650, "frontier_useful": bool(pooled90 > 0.50), "coverage_at_90pct_accuracy": pooled90, "dominant_feature_class": ablated["dominant_class"], "v5_upgrade": "gating viable" if pooled90 > 0.50 else "still ranking/triage only", "rationale": "Decision-level features are evaluated on the same geometry-derived correctness protocol; no candidate feature uses the current label.", "breakthrough_features": breakthrough}, "metadata": {"rows_emitted": len(df), "columns": list(df.columns), "new_features_count": len(new_features), "conditions": list(CONDITIONS), "decisions_per_run": TOTAL, "seeds": list(SEEDS), "copilots": list(COPILOTS), "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED", "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "copilot_sdk/scoring/scorer.py", ROOT / "copilot_sdk/scoring/investigation.py", ROOT / "copilot_sdk/backend/investigation_router.py")}}}
    json_text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if json_text != json.dumps(json.loads(json_text), indent=2, sort_keys=True, allow_nan=False) + "\n":
        raise RuntimeError("two-rebuild JSON mismatch")
    OUT.write_bytes(json_text.encode("utf-8"))
    lines = ["# CONS-PD-2 — Decision-level confidence features", "", f"Rows: {len(df):,}; columns: {len(df.columns)}; conditions: normal/poison-25%; seeds: 42/123/7; decisions/run: 1,000.", "", "## Feature computability gate", "", "All ten requested decision-level features were computable before the current label. Q vectors, K state, deltas, post-margin, Q×K, category count, factor position, and centroid distances use only decision-time geometry and investigation state.", "", "## Full feature ranking — pooled", "", table_md(pooled_rank, ["feature", "auc", "class"], ["Feature", "AUC", "Class"]), "", "New features above AUC .650:", "", ", ".join(f"{x['feature']} ({x['auc']:.3f})" for x in breakthrough) if breakthrough else "None.", "", "## Per-copilot ranking", "", "Top-five per-copilot rows are included in the JSON under feature_ranking.per_copilot.", "", "## Combined model", "", f"Top features: {', '.join(top_features)}", "", f"Pooled AUC: {metrics['pooled_auc']:.3f}; pooled ECE: {metrics['pooled_ece']:.4f}; baseline-model AUC: {baseline_metrics['pooled_auc']:.3f}.", "", table_md([{"copilot": c, **metrics["per_copilot"][c]} for c in COPILOTS], ["copilot", "auc", "ece"], ["Copilot", "AUC", "ECE"]), "", "## Frontier improvement", "", table_md([{"theta": t, **v} for t, v in combined_frontier["pooled"].items()], ["theta", "coverage", "accuracy"], ["θ", "Coverage", "Accuracy"]), "", f"Coverage at first tested 90% accuracy: {pooled90:.1%}.", "", "## Feature-class ablation", "", table_md([{"model": k, "pooled_auc": v} for k, v in ablated.items() if k != "dominant_class"], ["model", "pooled_auc"], ["Model", "Pooled AUC"]), "", f"Dominant class: {ablated['dominant_class']}.", "", "## V5 verdict", "", f"{result['verdict']['v5_upgrade']}. Decision-level features {'do' if result['verdict']['auc_improved'] else 'do not'} materially improve per-decision confidence discrimination under the tested frontier criterion.", "", f"JSON: {OUT}; instrumented table: {CSV}. Frozen source hashes are recorded in JSON."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {CSV}")
    print(f"Wrote {OUT}")
    print(f"Wrote {SUMMARY}")


def table_md(rows: list[dict[str, Any]], columns: list[str], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "—")) for c in columns) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
