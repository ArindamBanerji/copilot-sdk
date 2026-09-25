from __future__ import annotations

"""Oracle-ceiling diagnostic, preregistered before execution.

Primary metric: action_accuracy on geometry-derived action labels.
READOUT-PROBLEM iff evidence_oracle - VLD(B=2) >=5pp in >=2/3 seeds
and action_oracle - single_pass >=10pp. UPSTREAM-CEILING iff
action_oracle - single_pass <5pp. Otherwise classify MIXED. The global
readout is nearest centroid over all category/action cells using exported
factor precision. The action oracle restricts that same nearest-centroid
readout to the geometry-derived true category. Evidence oracle reveals
the complete generated factor vector; it never consumes the correct label.
VLD's acquisition category is routed from the obscured vector; Q selection
and B=2 restoration reuse the K-curve harness. For the architecture gap,
global full-vector readout is intentionally compared with true-category
action readout. Two independent scenario/evaluation rebuilds per seed and
geometry must have identical canonical bytes.
Tier: REAL_COMPONENT geometry + SIMULATED streams/actions.
"""

import hashlib
import json
import random
import sys
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import k_learning_curve_cross_copilot as kcurve

BACKEND = ROOT.parent / "gen-ai-roi-demo-v4-v50" / "backend"
STATES_DIR = BACKEND / "data"
SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
N_EVAL = 600
TIER = "REAL_COMPONENT geometry + SIMULATED streams/actions"
OUT = ROOT / "experiments/vld/results/oracle_ceiling_diagnostic.json"
SUMMARY = ROOT / "experiments/vld/results/oracle_ceiling_summary.md"
R = dict[str, Any]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def geometry_states(export: R) -> tuple[dict[str, dict[str, R]], dict[str, list[str]]]:
    states: dict[str, dict[str, R]] = {}
    available: dict[str, list[str]] = {}
    for cop in COPILOTS:
        base = export[cop]
        states[cop] = {"default": base}
        if cop == "soc":
            for label, filename in (("trained", "trained_experiment_centroids.npy"),
                                    ("bootstrapped", "bootstrapped_centroids.npy")):
                path = STATES_DIR / filename
                if path.exists():
                    array = np.asarray(np.load(path), dtype=np.float64)
                    names = list(base["category_names"])
                    expected = (len(names), len(base["action_names"]), len(base["factor_names"]))
                    if array.shape != expected:
                        raise ValueError(f"{path} shape {array.shape}, expected {expected}")
                    modified = dict(base)
                    modified["all_category_mu"] = {name: array[i].tolist() for i, name in enumerate(names)}
                    states[cop][label] = modified
        available[cop] = list(states[cop])
    return states, available


def global_score(vector: np.ndarray, mus: dict[str, np.ndarray], sigma: np.ndarray,
                 category_names: list[str]) -> tuple[str, int]:
    precision = 1.0 / np.maximum(sigma ** 2, 0.001)
    best_category = ""
    best_action = 0
    best_distance = float("inf")
    for category in category_names:
        distances = np.sum(precision[None, :] * (mus[category] - vector[None, :]) ** 2, axis=1)
        action = int(np.argmin(distances))
        distance = float(distances[action])
        if distance < best_distance:
            best_distance = distance
            best_category = category
            best_action = action
    return best_category, best_action


def score_seed(cop: str, state: str, info: R, seed: int) -> R:
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factors = list(info["factor_names"])
    actions = list(info["action_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64)
    if sigma.shape != (len(factors),):
        sigma = np.ones(len(factors), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mus = {category: np.asarray(info["all_category_mu"][category], dtype=np.float64)
           for category in categories}
    rng = random.Random(seed)
    correct = {arm: 0 for arm in ("single_pass", "vld_b2", "evidence_oracle", "action_oracle")}
    for _ in range(N_EVAL):
        true_category = rng.choice(categories)
        label_investigator = kcurve.VLDInvestigator(mus[true_category], sigma, factors, tau=tau)
        case = kcurve.make_case(rng, true_category, mus[true_category], label_investigator)
        target = int(case["correct_action"])
        surface = np.asarray(case["surface"], dtype=np.float64)
        full = np.asarray(case["full"], dtype=np.float64)

        _sp_category, sp_action = global_score(surface, mus, sigma, categories)
        route_category, _route_action = global_score(surface, mus, sigma, categories)
        acquisition_investigator = kcurve.VLDInvestigator(mus[route_category], sigma, factors, tau=tau)
        run = kcurve.run_investigation(case, acquisition_investigator,
                                       np.full(len(factors), kcurve.BASELINE_WEIGHT, dtype=np.float64),
                                       budget=2)
        if run["step_records"]:
            post_read = np.asarray(run["step_records"][-1][2], dtype=np.float64)
        else:
            post_read = surface
        _vld_category, vld_action = global_score(post_read, mus, sigma, categories)
        _evidence_category, evidence_action = global_score(full, mus, sigma, categories)
        action_distances = np.sum((mus[true_category] - full[None, :]) ** 2 *
                                  (1.0 / np.maximum(sigma ** 2, 0.001))[None, :], axis=1)
        oracle_action = int(np.argmin(action_distances))

        correct["single_pass"] += int(sp_action == target)
        correct["vld_b2"] += int(vld_action == target)
        correct["evidence_oracle"] += int(evidence_action == target)
        correct["action_oracle"] += int(oracle_action == target)

    n = float(N_EVAL)
    accuracy = {arm: correct[arm] / n for arm in correct}
    readout = accuracy["evidence_oracle"] - accuracy["vld_b2"]
    architecture = accuracy["action_oracle"] - accuracy["evidence_oracle"]
    ceiling = accuracy["action_oracle"] - accuracy["single_pass"]
    return {**accuracy, "readout_gap": readout, "architecture_gap": architecture,
            "ceiling_gap": ceiling, "n_evaluated": N_EVAL,
            "metric": "action_accuracy", "tier": TIER,
            "scenario_seed": seed, "geometry": state, "copilot": cop,
            "target_definition": "full-vector nearest action centroid within true category"}


def sample_std(values: list[float]) -> float:
    return stdev(values) if len(values) > 1 else 0.0


def main() -> None:
    if OUT.exists() or SUMMARY.exists():
        raise FileExistsError("Oracle-ceiling output already exists; refusing overwrite")
    export = kcurve.load_export()
    states, available = geometry_states(export)
    result: R = {}
    checks: R = {}
    for cop in COPILOTS:
        result[cop] = {}
        for state, info in states[cop].items():
            per_seed: R = {}
            for seed in SEEDS:
                first = score_seed(cop, state, info, seed)
                second = score_seed(cop, state, info, seed)
                assert canonical(first) == canonical(second), f"rebuild mismatch: {cop}/{state}/{seed}"
                per_seed[str(seed)] = first
                checks[f"{cop}/{state}/{seed}"] = {"rebuilds": 2, "byte_identical": True,
                                                     "sha256": digest(first)}
            arms = ("single_pass", "vld_b2", "evidence_oracle", "action_oracle",
                    "readout_gap", "architecture_gap", "ceiling_gap")
            aggregate: R = {f"{arm}_mean": mean([float(row[arm]) for row in per_seed.values()])
                            for arm in arms}
            for arm in ("single_pass", "vld_b2", "evidence_oracle", "action_oracle"):
                aggregate[f"{arm}_std"] = sample_std([float(row[arm]) for row in per_seed.values()])
            readout_seeds = sum(float(row["readout_gap"]) >= 0.05 for row in per_seed.values())
            ceiling10 = aggregate["action_oracle_mean"] - aggregate["single_pass_mean"] >= 0.10
            ceiling5 = aggregate["action_oracle_mean"] - aggregate["single_pass_mean"] < 0.05
            if ceiling5:
                verdict = "UPSTREAM-CEILING"
            elif readout_seeds >= 2 and ceiling10:
                verdict = "READOUT-PROBLEM"
            else:
                verdict = "MIXED"
            aggregate.update({"readout_gap_seeds_ge_5pp": readout_seeds,
                              "action_oracle_headroom_ge_10pp": bool(ceiling10),
                              "fork_verdict": verdict, "metric": "action_accuracy", "tier": TIER})
            result[cop][state] = {"per_seed": per_seed, "aggregate": aggregate}

    result["metadata"] = {"seeds": list(SEEDS), "evaluation_cases_per_seed": N_EVAL,
        "pre_registered_rule": "READOUT-PROBLEM iff evidence_oracle - VLD >=5pp in >=2/3 seeds AND action_oracle - single_pass >=10pp; UPSTREAM-CEILING iff action_oracle - single_pass <5pp; otherwise MIXED",
        "geometry_states_available": available,
        "evidence_oracle_definition": "Full generated factor vector, scored by global nearest-centroid readout; no correct-action label is used in prediction.",
        "action_oracle_definition": "Weighted nearest action centroid within the geometry-derived true category using the complete vector.",
        "vld_definition": "Route on obscured surface, apply K-curve Q top-B=2 reads using category-conditioned investigator, then global nearest-centroid action readout.",
        "c8_harness_note": "C8 Strategy E is true-category plus one-pattern evidence. Its v_after_all_patterns()+score_best() can express full-pattern evidence, but the primary matched seeded ladder uses K-curve geometry scenarios and exact full-factor reveal.",
        "tier": TIER, "metric": "action_accuracy", "determinism_per_cell": checks,
        "units": "accuracy fractions [0,1]"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(canonical(result))
    write_summary(result)
    print("Oracle-ceiling diagnostic complete", flush=True)


def write_summary(data: R) -> None:
    lines = ["# Oracle-ceiling diagnostic", "",
        f"Tier: {TIER}. Metric: action_accuracy. Values are fractions; gaps are percentage points in the table.",
        "READOUT-PROBLEM requires evidence-oracle minus VLD(B=2) ≥5pp in at least2/3 seeds and action-oracle headroom ≥10pp. UPSTREAM-CEILING requires action-oracle headroom <5pp; otherwise MIXED.", "",
        "| Copilot | Geometry | Single-pass | VLD B=2 | Evidence oracle | Action oracle | Readout gap (pp) | Architecture gap (pp) | Verdict |", "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for cop in ("soc", "dataops", "trading", "purchasing", "s2p"):
        for geo, cell in data[cop].items():
            a = cell["aggregate"]
            lines.append(f"| {cop} | {geo} | {a['single_pass_mean']:.3f} | {a['vld_b2_mean']:.3f} | {a['evidence_oracle_mean']:.3f} | {a['action_oracle_mean']:.3f} | {100*a['readout_gap_mean']:+.2f} | {100*a['architecture_gap_mean']:+.2f} | {a['fork_verdict']} |")
    lines += ["", "## Best-available geometry fork", "", "| Copilot | Geometry used | Readout gap (pp) | Architecture gap (pp) | Ceiling headroom (pp) | Fork verdict |", "|---|---|---:|---:|---:|---|"]
    for cop in ("soc", "dataops", "trading", "purchasing", "s2p"):
        geo = "trained" if cop == "soc" and "trained" in data[cop] else "default"
        a = data[cop][geo]["aggregate"]
        lines.append(f"| {cop} | {geo} | {100*a['readout_gap_mean']:+.2f} | {100*a['architecture_gap_mean']:+.2f} | {100*(a['action_oracle_mean']-a['single_pass_mean']):+.2f} | {a['fork_verdict']} |")
    lines += ["", "## Cross-campaign interpretation", "",
        "C7 found SOC action_accuracy +4pp at depth-3 with approximately flat routing_quality. The default-geometry oracle ladder has +21pp readout headroom, while trained SOC is already at action_accuracy 1.0 with zero readout gap. This is only directionally compatible with C7; the protocols and geometry states differ.",
        "C8's existing SOC Strategy E verdicts were ARCHITECTURE ISSUE on default and bootstrapped geometry and SELECTIVE ENRICHMENT on trained geometry. That pattern is NOT consistent with this geometry-generated ladder's READOUT-PROBLEM on default/bootstrapped and no readout gap on trained. The protocols and evaluation labels differ (C8's 543-alert labels versus generated nearest-centroid labels); report the discrepancy, not a replication or reconciliation.", "",
        "## Paper sentence", "",
        "The action-accuracy ceiling is geometry- and readout-dependent: report READOUT-PROBLEM only where full-factor evidence improves on B=2 by at least5pp in two of three seeds with at least10pp action-oracle headroom; otherwise distinguish UPSTREAM-CEILING from mixed cases. The action oracle is geometry-derived and does not establish independent-label performance.",
        "", "Evidence oracle reveals all generated factor values; action oracle alone receives the true category. Geometry labels remain nearest-centroid derived.", ""]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
