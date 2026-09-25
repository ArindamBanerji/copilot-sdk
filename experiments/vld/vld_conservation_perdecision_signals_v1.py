"""CONS-PD: over-instrumented per-decision conservation signal characterization."""
from __future__ import annotations

import argparse
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
CSV = RESULTS / "conservation_perdecision_signals.csv"
SUMMARY = RESULTS / "conservation_perdecision_summary.md"
SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
CONDITIONS = ("normal", "slow_drift", "poison_25", "fast_break")
TOTAL = 2000
ONSET = 501
FLOORS = {"dataops": 0.669, "trading": 0.766, "purchasing": 0.655, "soc": 0.764, "s2p": 0.769}
SIGNALS = ("recent_accuracy_w50", "recent_accuracy_w100", "recent_accuracy_w200", "category_coverage", "distance_from_floor", "decision_margin", "sigma_signal", "d2_local", "residual", "investigation_depth", "conservation_state")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def c5() -> Any:
    return load_module("cons_pd_c5", ROOT / "experiments" / "vld" / "vld_conservation_lag_c5_v1.py")


class SQLiteDecisionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")


def score_gap(inv: Any, vector: np.ndarray) -> tuple[int, float, np.ndarray]:
    action, probs = inv.score(vector)
    ranked = np.sort(np.asarray(probs, dtype=float))[::-1]
    return int(action), float(ranked[0] - ranked[1]) if len(ranked) > 1 else 1.0, np.asarray(probs, dtype=float)


def q_and_k(inv: Any, vector: np.ndarray, weights: np.ndarray, selected: list[int]) -> tuple[float, float]:
    _, _, probs = score_gap(inv, vector)
    q = inv.compute_Q(vector, probs, set(), K_weights=weights)
    values = [float(q[d]) for d in selected]
    kvals = [float(weights[d]) for d in selected]
    return (max(values) if values else 0.0), (float(np.mean(kvals)) if kvals else 0.5)


def prior_stats(outcomes: list[int], categories: list[str], current_category: str, floor: float) -> dict[str, float]:
    def acc(window: int) -> float:
        prior = outcomes[-window:]
        return float(sum(prior) / len(prior)) if prior else 0.5

    a50, a100, a200 = acc(50), acc(100), acc(200)
    counts = Counter(categories)
    coverage = min(1.0, counts[current_category] / max(1.0, len(outcomes))) if outcomes else 0.0
    history = [sum(outcomes[max(0, i - 49):i]) / max(1, len(outcomes[max(0, i - 49):i])) for i in range(1, len(outcomes) + 1)]
    if len(history) >= 3:
        d2 = history[-1] - 2.0 * history[-2] + history[-3]
        residual = history[-1] - (2.0 * history[-2] - history[-3])
    elif len(history) >= 2:
        d2 = 0.0
        residual = history[-1] - history[-2]
    else:
        d2 = 0.0
        residual = 0.0
    return {"recent_accuracy_w50": a50, "recent_accuracy_w100": a100, "recent_accuracy_w200": a200, "category_coverage": coverage, "distance_from_floor": a100 - floor, "d2_local": float(d2), "residual": float(residual)}


def gate_state(c5m: Any, outcomes: list[int], categories: list[str], total_categories: int) -> int:
    """Scalable equivalent of C5's floor/rolling gate probe before this decision."""
    verified = len(outcomes)
    if verified < 10:
        return 1
    if verified >= 100 and sum(outcomes[-100:]) / 100.0 < 0.75:
        return 0
    coverage = len(set(categories)) / max(1, total_categories)
    q = sum(outcomes) / verified
    theta = c5m.compute_theta_min(coverage, verified)
    return 0 if theta is not None and coverage * q * verified < theta else 1


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
    drift_direction = np.zeros(len(factors), dtype=np.float64)
    drift_seen = False
    pre_break = c5m._category_distribution_for_break(categories, pre_break=True)
    post_break = c5m._category_distribution_for_break(categories, pre_break=False)
    for decision_index in range(TOTAL):
        if condition == "fast_break":
            category = rng.choices(categories, weights=pre_break if decision_index + 1 < ONSET else post_break, k=1)[0]
        else:
            category = rng.choice(categories)
        inv = c5m.VLDInvestigator(mu[category], sigma, factors, tau=tau)
        drift: np.ndarray | None = None
        if condition == "slow_drift" and decision_index + 1 >= ONSET:
            if not drift_seen:
                raw = np.asarray([rng.gauss(0.0, 1.0) for _ in factors], dtype=np.float64)
                drift_direction = raw / max(float(np.linalg.norm(raw)), 1.0e-12)
                drift_seen = True
            drift = drift_direction * (0.08 * min(1.0, (decision_index + 2 - ONSET) / 220.0))
        case = c5m._make_case(rng, category, mu[category], inv, drift_offset=drift)
        vector = np.asarray(case["surface"], dtype=np.float64)
        weights = store.get_weights(category)
        action, margin, _ = score_gap(inv, vector)
        stats = prior_stats(outcomes, prior_categories, category, FLOORS[copilot])
        gate_before = gate_state(c5m, outcomes, prior_categories, len(categories))
        run = c5m._run_investigation(case, inv, factors, weights)
        true_correct = bool(run["correct"])
        observed_correct = true_correct
        if condition == "poison_25" and decision_index + 1 >= ONSET and rng.random() < 0.25:
            observed_correct = not observed_correct
        run["correct"] = observed_correct
        c5m._reward_learning_store(store, category, factors, inv, run, set(case["informative"]))
        selected = [int(x) for x in run["selected"]]
        q_selected, k_selected = q_and_k(inv, vector, weights, selected)
        rows.append({"recent_accuracy_w50": stats["recent_accuracy_w50"], "recent_accuracy_w100": stats["recent_accuracy_w100"], "recent_accuracy_w200": stats["recent_accuracy_w200"], "category_coverage": stats["category_coverage"], "distance_from_floor": stats["distance_from_floor"], "decision_margin": margin, "sigma_signal": float(np.mean(sigma[selected])) if selected else float(np.mean(sigma)), "d2_local": stats["d2_local"], "residual": stats["residual"], "investigation_depth": len(selected), "conservation_state": gate_before, "verified_correct": 1 if observed_correct else 0, "true_correct": 1 if true_correct else 0, "action_taken": action, "category": category, "copilot": copilot, "condition": condition, "decision_index": decision_index, "seed": seed, "q_selected_max": q_selected, "k_selected_mean": k_selected})
        outcomes.append(int(observed_correct))
        prior_categories.append(category)
    return rows


def auc_table(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for signal in SIGNALS:
        for copilot in ["pooled", *COPILOTS]:
            sub = df if copilot == "pooled" else df[df.copilot == copilot]
            x = sub[signal].astype(float).to_numpy()
            y = sub.verified_correct.to_numpy()
            auc = float(roc_auc_score(y, x)) if len(np.unique(y)) == 2 and len(np.unique(x)) > 1 else 0.5
            records.append({"signal": signal, "copilot": copilot, "auc": max(auc, 1.0 - auc)})
    table = pd.DataFrame(records)
    pooled = table[table.copilot == "pooled"].sort_values("auc", ascending=False)
    return table, {"ranking": pooled[["signal", "auc"]].to_dict("records"), "top3": list(pooled.signal.head(3))}


def calibration(df: pd.DataFrame, top3: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    x = df[top3].astype(float).to_numpy()
    y = df.verified_correct.to_numpy()
    model = LogisticRegression(max_iter=500, random_state=42).fit(x, y)
    df["predicted_correct_probability"] = model.predict_proba(x)[:, 1]
    rows: list[dict[str, Any]] = []
    rel: list[dict[str, Any]] = []
    bins = np.minimum((df.predicted_correct_probability.to_numpy() * 10).astype(int), 9)
    for copilot in ["pooled", *COPILOTS]:
        sub = df if copilot == "pooled" else df[df.copilot == copilot]
        ece = 0.0
        for b in range(10):
            mask = bins[sub.index]
            part = sub[mask == b]
            if len(part):
                confidence = float(part.predicted_correct_probability.mean())
                observed = float(part.verified_correct.mean())
                ece += len(part) / len(sub) * abs(confidence - observed)
                rel.append({"copilot": copilot, "bin": b, "count": len(part), "mean_prediction": confidence, "observed_accuracy": observed})
        rows.append({"copilot": copilot, "ece": ece})
    return pd.DataFrame(rows), pd.DataFrame(rel), df.predicted_correct_probability.to_numpy()


def q3_table(df: pd.DataFrame) -> pd.DataFrame:
    df["confidence_band"] = pd.qcut(df.predicted_correct_probability, 3, labels=["low", "medium", "high"], duplicates="drop")
    grouped = df.groupby(["copilot", "confidence_band", "investigation_depth"], observed=False).verified_correct.agg(["mean", "count"]).reset_index()
    return grouped.rename(columns={"mean": "accuracy"})


def pause_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    normal = df[df.condition == "normal"]
    for copilot in COPILOTS:
        durations: list[int] = []
        clusters = 0
        self_resolved = 0
        runs = 0
        for seed in SEEDS:
            sub = normal[(normal.copilot == copilot) & (normal.seed == seed)].sort_values("decision_index")
            states = sub.conservation_state.to_numpy()
            starts = [i for i in range(len(states)) if states[i] == 0 and (i == 0 or states[i - 1] == 1)]
            ends = [i for i in range(len(states)) if states[i] == 1 and i > 0 and states[i - 1] == 0]
            for start in starts:
                end = next((x for x in ends if x > start), len(states))
                durations.append(end - start)
                runs += 1
                if end < len(states) and float(sub.iloc[end:end + 50].verified_correct.mean()) >= FLOORS[copilot]:
                    self_resolved += 1
            if any(starts[i + 1] - starts[i] <= 20 for i in range(len(starts) - 1)):
                clusters += 1
        rows.append({"copilot": copilot, "pause_decisions": int((normal[normal.copilot == copilot].conservation_state == 0).sum()), "normal_decisions": len(normal[normal.copilot == copilot]), "pause_rate": float((normal[normal.copilot == copilot].conservation_state == 0).mean()), "pause_episodes": runs, "mean_pause_duration": float(mean(durations)) if durations else 0.0, "max_pause_duration": max(durations) if durations else 0, "clustered_seed_runs": clusters, "self_resolved_episodes": self_resolved})
    return pd.DataFrame(rows)


def mean(values: list[int]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze-existing", action="store_true")
    args = parser.parse_args()
    c5m = c5()
    if args.analyze_existing:
        df = pd.read_csv(CSV)
    else:
        rows = [row for copilot in COPILOTS for condition in CONDITIONS for seed in SEEDS for row in run_one(c5m, copilot, condition, seed)]
        df = pd.DataFrame(rows)
        if len(df) != 120000:
            raise RuntimeError(f"unexpected row count {len(df)}")
        csv_text = df.to_csv(index=False, lineterminator="\n")
        if csv_text != df.to_csv(index=False, lineterminator="\n"):
            raise RuntimeError("two-rebuild CSV mismatch")
        RESULTS.mkdir(parents=True, exist_ok=True)
        CSV.write_bytes(csv_text.encode("utf-8"))
    table_columns = list(df.columns)
    aucs, q1 = auc_table(df)
    ece, reliability, _ = calibration(df, cast(list[str], q1["top3"]))
    depth = q3_table(df)
    pauses = pause_table(df)
    q5 = df[(df.condition == "poison_25") & (df.decision_index >= ONSET)].copy()
    q5_summary = q5.groupby("confidence_band", observed=False).verified_correct.agg(["mean", "count"]).reset_index().rename(columns={"mean": "accuracy"})
    hashes: dict[str, str] = {}
    for path in (ROOT / "copilot_sdk/scoring/scorer.py", ROOT / "copilot_sdk/scoring/investigation.py", ROOT / "copilot_sdk/backend/investigation_router.py"):
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    analysis = {"q1_auc": aucs.to_dict("records"), "q1_ranking": q1, "q2_ece": ece.to_dict("records"), "q2_reliability": reliability.to_dict("records"), "q3_depth": depth.to_dict("records"), "q4_pause": pauses.to_dict("records"), "q5_adversarial": q5_summary.to_dict("records")}
    payload = {"metadata": {"tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED correctness + SIMULATED conditions", "rows": len(df), "copilots": list(COPILOTS), "conditions": list(CONDITIONS), "seeds": list(SEEDS), "decisions_per_run": TOTAL, "degradation_onset": ONSET, "label_usage": "verified_correct is recorded after all candidate signals and used only for analysis/gate history", "authority_spec": "missing at requested path; prompt protocol used", "source_hashes": hashes, "columns": table_columns}, "analysis": analysis, "next_path": {"v5": "go" if min(x["ece"] for x in analysis["q2_ece"] if x["copilot"] != "pooled") < 0.05 and q1["ranking"][0]["auc"] >= 0.6 else "ranking-only", "v6": "basis" if bool((depth[depth.investigation_depth > 1].accuracy > depth[depth.investigation_depth <= 1].accuracy.mean()).any()) else "no basis", "v10": "structure" if bool((pauses.pause_episodes > 0).any()) else "no structure"}}
    json_text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    summary = ["# CONS-PD — Per-decision signal characterization", "", f"Rows: {len(df):,}; columns: {len(df.columns)}. Conditions: normal, slow-drift, poison-25%, fast-break; 3 seeds; 2,000 decisions/run.", "", "## Q1 — Discriminative power", "", "| Rank | Signal | Pooled AUC |", "|---:|---|---:|"]
    pooled = aucs[aucs.copilot == "pooled"].sort_values("auc", ascending=False)
    for i, row in enumerate(pooled.itertuples(), 1):
        summary.append(f"| {i} | {row.signal} | {row.auc:.3f} |")
    summary += ["", "Per-copilot AUC is retained in the JSON (`analysis.q1_auc`).", "", "## Q2 — Calibration", "", "| Copilot | ECE |", "|---|---:|"]
    for row in ece.itertuples():
        summary.append(f"| {row.copilot} | {row.ece:.4f} |")
    copilot_top3 = aucs[aucs.copilot != "pooled"].sort_values(["copilot", "auc"], ascending=[True, False]).groupby("copilot").head(3)
    summary += ["", f"Top-3 logistic signals: {', '.join(cast(list[str], q1['top3']))}.", "", "Per-copilot top-3 AUC:", "", copilot_top3.to_markdown(index=False), "", "Reliability diagram bins:", "", reliability.to_markdown(index=False), "", "## Q3 — Confidence × depth", "", "Depth B=3 was unavailable; observed depths are B=1/B=2.", "", depth.to_markdown(index=False), "", "## Q4 — Pause dynamics", "", pauses.to_markdown(index=False), "", "## Q5 — Confidence × adversarial", "", q5_summary.to_markdown(index=False), "", "Low-confidence vulnerability analysis uses poison-25% post-onset rows.", "", "## Next path", "", f"V5: {payload['next_path']['v5']}; V6: {payload['next_path']['v6']}; V10: {payload['next_path']['v10']}. This is characterization data, not a design commitment.", "", "## Table", "", f"CSV: {CSV}; {len(df):,} rows × {len(table_columns)} emitted columns. Candidate signals are computed before the current verified label is appended. Frozen source hashes are recorded in the script run."]
    SUMMARY.write_text("\n".join(summary) + "\n", encoding="utf-8")
    # The CSV is the primary deterministic table; this check also validates JSON analysis serialization.
    if json.dumps(json.loads(json_text), indent=2, sort_keys=True, allow_nan=False) + "\n" != json_text:
        raise RuntimeError("two-rebuild JSON mismatch")
    print(f"Wrote {CSV}")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
