"""C3 -- PREREGISTERED before execution, 2026-09-14.
Metric: residual routing_quality AND action_accuracy gaps on frozen SA test.
Decision rule: labels-are-the-asset strengthens within tested sources iff NONE
reaches sustained joint parity without incumbent verified data. If ANY does,
weaken to labels costly to acquire, naming source and measured label/read cost.
This finite synthetic study cannot establish universal un-acquirability.

SOC/DataOps; seeds42,123,7; import B2 streams/learner/evaluation/stopping/parity.
Reuse EXP1 incumbents at matching seed (seed42 matches B2). NO old Arm3 reruns.
Actual B2 split2000/400/600, convergence .005 BOTH development metrics over3
checkpoints, min500/max2000, checkpoint50; parity .01 BOTH test metrics over3.
All SA test sets freeze BEFORE any SB generation via e.build_streams.
Test labels never affect labeling, credit, stopping, source design, or tuning.

WS-1 LOCKED: fit per-factor mean/population SD (floor1e-10) to SB TRAIN
SURFACE inputs ONLY. Equal-weight mean standardized factor score; SB-train
quantile bins at j/A, j=1..A-1. Map low-to-high scores to domain action order:
SOC suppress,monitor,investigate,escalate.
DataOps auto_approve,investigate,refer_to_specialist,escalate_to_owner,pause_downstream.
No oracle or SA input is used to fit the heuristic; no parameter search.
FM-1/2: SIMULATED oracle-label proxy, exact20%/10% wrong labels in shuffled
blocks of10, wrong action uniform among remaining actions. No actual LLM.
Common corruption ordering, FM-2 flipped subset of FM-1; independent train/dev
streams use domainseed+700000 / +800000, wrong action rng offset1.
This uses the SB generating-geometry oracle, not incumbent test labels.

Adapt ONLY credit to existing b.observed_credit(), the received-label path
already used by B2 noisy-label arms. Train evidence providers retain inherited
oracle-coupled synthetic availability (a limitation, not oracle separation).
Development informative tags recomputed from received pseudo-labels using
existing b.noisy_dev(epsilon=0), exactly its label-conditioned methodology.
No clean development correctness controls stopping. Evaluation uses unchanged
fixed SA oracle labels and evidence tags for EVERY condition.
K and scoring unchanged; mu fixed. Label sources differ, no tuning.

Two independent full stream/learner/cache rebuilds per seed; compare bytes.
Gap output units pp; checkpoint accuracy/routing/label accuracy are fractions.
Category is supplied, category_accuracy not measured.
Tier REAL_COMPONENT geometry + SIMULATED streams/verification/label sources.
Do not interpolate a label-quality crossing unless 80/90% bracket parity.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, cast
import numpy as np
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.vld import vld_moat_b2_seeds_v1 as e
from experiments.vld import vld_moat_b2_v1 as b
R = dict[str, Any]
SEEDS = [42, 123, 7]
COPS = ("soc", "dataops")
CONDITIONS = ("WS-1", "FM-1", "FM-2")
TIER = "REAL_COMPONENT geometry + SIMULATED streams/verification/label sources"
RULE = "tested labels-are-the-asset claim strengthens iff no new source reaches sustained joint parity"
OUT = ROOT/"experiments/vld/results/c3_label_breadth.json"
ORDERS = {"soc": ["suppress", "monitor", "investigate", "escalate"],
          "dataops": ["auto_approve", "investigate", "refer_to_specialist",
                      "escalate_to_owner", "pause_downstream"]}


class ReceivedLabelLearner(b.Learner):
    def credit(self, case: R, run: R, informative: set[int] | None = None) -> None:
        credited, allowed = b.observed_credit(self, case, run, int(case["correct_action"]))
        super().credit(case, credited, allowed)


def heuristic_model(surfaces: list[Any], action_names: list[str], cop: str) -> R:
    x = np.asarray(surfaces)
    mean, sd = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-10)
    risk = ((x-mean)/sd).mean(axis=1)
    return {"mean": mean.tolist(), "population_sd": sd.tolist(),
            "cuts": np.quantile(risk, np.arange(1, len(action_names))/len(action_names)).tolist(),
            "action_indices": [action_names.index(a) for a in ORDERS[cop]],
            "action_order": ORDERS[cop], "fitted_on": "SB training surface inputs ONLY",
            "factor_weights": [1/len(mean)]*len(mean), "tier": TIER}


def heuristic_label(surface: Any, model: R) -> int:
    score = float(((np.asarray(surface)-np.asarray(model["mean"]))/np.asarray(model["population_sd"])).mean())
    index = int(np.searchsorted(model["cuts"], score, side="right"))
    return int(model["action_indices"][index])


def labeled(cohort: Any, condition: str, model: R, n_actions: int,
            seed: int) -> tuple[Any, list[bool]]:
    take = 2 if condition == "FM-1" else 1
    mask = b.shuffled_mask(len(cohort.cases), 10, take, seed)
    rng = random.Random(seed+1)
    wrong_offsets = [rng.randrange(1, n_actions) for _ in cohort.cases]
    cases: list[R] = []
    agreements: list[bool] = []
    for i, original in enumerate(cohort.cases):
        if condition == "WS-1":
            label = heuristic_label(original["surface"], model)
        else:
            label = int(original["correct_action"])
            if mask[i]:
                label = (label+wrong_offsets[i]) % n_actions
        # Oracle value below is audit-only; neither WS fitting nor credit sees it.
        agreements.append(label == int(original["correct_action"]))
        case = dict(original)
        case["correct_action"] = label
        cases.append(case)
    return b.Cohort(cases), agreements


def run_seed(seed: int, controls: R) -> R:
    streams = e.build_streams(seed)
    result: R = {}
    for cop in COPS:
        s = streams[cop]
        control = controls[cop]["per_seed"][str(seed)]
        assert s["audit"] == control["stream_audit"]
        assert s["spec"] == control["S_B_perturbation_spec"]
        ref = control["arm1_converged_reference"]
        model = heuristic_model([c["surface"] for c in s["sb_train"].cases],
                                s["info"]["action_names"], cop)
        result[cop] = {}
        for condition in CONDITIONS:
            train, agreements = labeled(s["sb_train"], condition, model,
                                        len(s["info"]["action_names"]), s["seed"]+700000)
            dev, dev_agreements = labeled(s["sb_dev"], condition, model,
                                         len(s["info"]["action_names"]), s["seed"]+800000)
            learner = ReceivedLabelLearner(cop, s["info"])
            try:
                # This recomputes development informative tags from pseudo-labels,
                # with zero ADDITIONAL corruption. Clean labels are not supplied.
                development = b.noisy_dev(dev, learner, 0., s["seed"]+900000)
                arm = b.run_arm(condition, learner, train, development, s["sa"]["test"],
                                {}, TIER, seed=s["seed"])
            finally:
                learner.close()
            arm.update(b.parity_summary(arm["checkpoints_on_SA_heldout"], ref,
                                        control["arm1_converged"]))
            assert arm["primary_evaluation_sha256"] == s["sa"]["test"].fingerprint
            assert arm["SA_verified_labels_received"] == 0
            n = arm["processed_decisions"]
            # Correct generic harness counter wording for the pseudo-label campaign.
            for record in [arm, *arm["checkpoints_on_SA_heldout"]]:
                record["SB_pseudo_labels_received"] = record.pop("SB_verified_labels_received")
                record["tier"] = TIER
                record["training_label_source"] = condition
            for record in arm["development_checkpoints"]:
                record["label_source"] = condition
                record["tier"] = TIER
                record["informative_tag_source"] = "received pseudo-label; b.noisy_dev epsilon=0"
            at_horizon = e.at_horizon(arm, control["arm1"]["processed_decisions"])
            result[cop][condition] = {
                "tier": TIER, "seed": seed, "gap_units": "percentage_points",
                "residual_routing_gap": 100*arm["residual_gap_routing"],
                "residual_action_gap": 100*arm["residual_gap_action"],
                "decisions_to_sustained_parity": arm["decisions_to_sustained_parity"],
                "parity_lost_after_confirmation": arm["parity_lost_after_confirmation"],
                "label_accuracy_vs_oracle": float(np.mean(agreements[:n])),
                "label_accuracy_all_training": float(np.mean(agreements)),
                "label_accuracy_development": float(np.mean(dev_agreements)),
                "correct_pseudo_labels_used": sum(agreements[:n]),
                "pseudo_labels_used": n, "training_evidence_reads": arm["training_evidence_reads"],
                "at_incumbent_horizon": {
                    "routing_gap_pp": 100*(ref["routing_quality"]-at_horizon["routing_quality"]),
                    "action_gap_pp": 100*(ref["action_accuracy"]-at_horizon["action_accuracy"]),
                    "competitor": at_horizon},
                "incumbent_reference": ref, "incumbent_converged": control["arm1_converged"],
                "stream_audit": s["audit"], "S_B_perturbation_spec": s["spec"],
                "pseudo_training_sha256": train.fingerprint,
                "pseudo_development_sha256": development.fingerprint,
                "ws1_model": model if condition == "WS-1" else None,
                "arm": arm}
    return result


def aggregate(rows: R) -> R:
    values = list(rows.values())
    r = np.asarray([v["residual_routing_gap"] for v in values])
    a = np.asarray([v["residual_action_gap"] for v in values])
    count = sum(isinstance(v["decisions_to_sustained_parity"], int) for v in values)
    return {"tier": TIER, "gap_units": "percentage_points",
            "routing_gap_mean": float(r.mean()), "routing_gap_std": float(r.std(ddof=1)),
            "routing_gap_min": float(r.min()), "routing_gap_max": float(r.max()),
            "action_gap_mean": float(a.mean()), "action_gap_std": float(a.std(ddof=1)),
            "seeds_reaching_parity": count,
            "label_accuracy": float(np.mean([v["label_accuracy_vs_oracle"] for v in values])),
            "pseudo_labels_used_mean": float(np.mean([v["pseudo_labels_used"] for v in values])),
            "training_evidence_reads_mean": float(np.mean([v["training_evidence_reads"] for v in values]))}


def references() -> R:
    old = json.loads((OUT.parent/"vld_moat_b2_v1.json").read_text(encoding="utf-8"))
    mapping = {"3a": "arm3a_inputs_no_labels", "3b_10": "arm3b_10pct",
               "3b_50": "arm3b_50pct", "3c_eps10": "arm3c_eps10", "3c_eps25": "arm3c_eps25"}
    result: R = {}
    for cop in COPS:
        result[cop] = {}
        for short, key in mapping.items():
            arm = old[cop][key]
            delivered = arm["labels_received"]
            accuracy = ((delivered-arm["corrupted_labels_received"])/delivered
                        if short.startswith("3c") and delivered else
                        1.0 if short.startswith("3b") else None)
            result[cop][short] = {"tier": TIER, "seed": 42, "source_arm": key,
                "rerun": False, "routing_gap_pp": 100*arm["residual_gap_routing"],
                "action_gap_pp": 100*arm["residual_gap_action"],
                "parity": arm["decisions_to_sustained_parity"],
                "label_accuracy": accuracy, "processed_decisions": arm["processed_decisions"],
                "labels_received": delivered,
                "note": "self-labeled SA surface; K NOT held fixed" if short == "3a" else
                        "SA labels delayed 50 decisions plus corruption" if short.startswith("3c") else
                        "mixed SA/SB with synthetic verified labels"}
    return result


def write_summary(result: R) -> None:
    lines = ["# C3: label-acquisition breadth", "",
             f"Evidence tier: {TIER}. All gaps are percentage points.",
             "Residual gaps use incumbent final-three mean minus competitor endpoint, matching B2 access tables. "
             "JSON also reports incumbent-horizon comparisons, both metrics at every checkpoint, label counts and costs.",
             "B2 rows are seed42 references, NOT reruns. C3 rows are means ± sample SD over seeds42/123/7.", "",
             "| Copilot | Source/access | Routing gap | Action gap | Label accuracy | Joint parity |",
             "|---|---|---:|---:|---:|---|"]
    refs = result["metadata"]["b2_reference_results"]
    for cop in COPS:
        for name, row in refs[cop].items():
            acc = "unmeasured" if row["label_accuracy"] is None else f"{row['label_accuracy']:.1%}"
            lines.append(f"| {cop} | B2 {name} (seed42) | {row['routing_gap_pp']:.2f} | "
                         f"{row['action_gap_pp']:.2f} | {acc} | {row['parity']} |")
        for condition in CONDITIONS:
            a = result[cop][condition]["aggregate"]
            lines.append(f"| {cop} | {condition} (3 seeds) | {a['routing_gap_mean']:.2f} ± {a['routing_gap_std']:.2f} | "
                         f"{a['action_gap_mean']:.2f} ± {a['action_gap_std']:.2f} | "
                         f"{a['label_accuracy']:.1%} | {a['seeds_reaching_parity']}/3 |")
    reached = [(c, name) for c in COPS for name in CONDITIONS
               if result[c][name]["aggregate"]["seeds_reaching_parity"]]
    lines += ["", "## Source definitions and access boundaries",
              "WS-1 uses only S_B training surface statistics: equally weighted standardized factor scores "
              "binned at action-count quantiles. Fixed low-to-high action orders are SOC suppress/monitor/"
              "investigate/escalate and DataOps auto_approve/investigate/refer_to_specialist/escalate_to_owner/"
              "pause_downstream. Means, SDs and cutpoints are exported per seed. No oracle labels fit this heuristic.",
              "FM-1/FM-2 are simulated noisy proxies, not measured foundation-model performance: exactly 20%/10% "
              "labels flipped in blocks of ten to another action. They label S_B, not S_A.",
              "Credit uses the existing received-label helper. Development correctness and informative tags "
              "come from the pseudo-labels; no clean-label stopping. All conditions evaluate the identical "
              "frozen S_A held-out set and use unchanged B2 joint parity/convergence rules.",
              "The inherited training evidence availability is oracle-coupled. This experiment is not oracle-separated; "
              "it isolates label-source access conditional on that synthetic evidence model.",
              "B2 3a updates K using its own predictions and surface-only evidence; it is not a frozen-K control. "
              "B2 3c also delays labels by 50 decisions. These distinctions matter for comparing conditions.",
              "", "## Verdict and acquisition cost"]
    if reached:
        lines.append("At least one new condition reaches sustained joint parity: "+", ".join(f"{c}/{n}" for c,n in reached)+
                     ". The preregistered strong labels-as-exclusive-asset claim weakens to labels being costly to acquire.")
    else:
        lines.append("No tested new source reaches sustained joint parity. The preregistered claim strengthens "
                     "within these profiles and horizons. This does NOT establish that verified labels are universally "
                     "un-acquirable: source accuracy, firm distribution and access are distinct axes.")
    lines += ["", "| Copilot | Source | Pseudo-labels used (mean) | Evidence reads (mean) |",
              "|---|---|---:|---:|"]
    for cop in COPS:
        for condition in CONDITIONS:
            a = result[cop][condition]["aggregate"]
            lines.append(f"| {cop} | {condition} | {a['pseudo_labels_used_mean']:.1f} | {a['training_evidence_reads_mean']:.1f} |")
    lines += ["", "No dollar/API acquisition cost is measured; the labelers are local simulations.",
              "", "## Quality threshold and plot-ready access data",
              "The JSON stores every B2 reference and C3 condition with label accuracy, access, routing gap, "
              "action gap, parity and costs. Do not collapse access-to-S_A and accuracy-on-S_B into one causal scale."]
    for cop in COPS:
        f1, f2 = (result[cop][f"FM-{i}"]["aggregate"] for i in (1,2))
        if not f1["seeds_reaching_parity"] and not f2["seeds_reaching_parity"]:
            lines.append(f"{cop}: neither 80% nor 90% S_B pseudo-label accuracy reaches parity. "
                         "No sufficient label-quality threshold is identified or bracketed; interpolation is unjustified.")
        else:
            lines.append(f"{cop}: FM-1 reaches parity in {f1['seeds_reaching_parity']}/3 seeds; FM-2 in "
                         f"{f2['seeds_reaching_parity']}/3. Report these tested levels; a discrete multi-metric "
                         "three-checkpoint gate does not justify a precise interpolated threshold from two means.")
    lines += ["", "## Null stakes and limitations",
              "Parity uses routing_quality AND action_accuracy within 1pp over three checkpoints. Later loss "
              "is recorded. Non-parity is censored at the arm's actual development-convergence stop, at most 2000.",
              "One heuristic and two noise proxies cannot exhaust realistic label acquisition. No causal claim "
              "that labels alone explain the moat follows when the competitor also has a different distribution.",
              "Two independent complete stream/learner/cache rebuilds per seed must match byte for byte.",
              ""]
    (OUT.parent/"c3_label_breadth_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    assert not OUT.exists(), "Do not overwrite an existing campaign output"
    before = e.source_hashes()
    controls = json.loads((OUT.parent/"moat_b2_seeds.json").read_text(encoding="utf-8"))
    result: R = {c: {condition: {"per_seed": {}} for condition in CONDITIONS} for c in COPS}
    checks: R = {}
    for seed in SEEDS:
        print(f"C3 seed={seed} rebuild 1/2", flush=True)
        first = run_seed(seed, controls)
        print(f"C3 seed={seed} rebuild 2/2", flush=True)
        second = run_seed(seed, controls)
        assert b.canonical(first) == b.canonical(second)
        checks[str(seed)] = {"passed": True, "independent_rebuilds": 2, "sha256": b.digest(first)}
        for cop in COPS:
            for condition in CONDITIONS:
                result[cop][condition]["per_seed"][str(seed)] = first[cop][condition]
    for cop in COPS:
        for condition in CONDITIONS:
            result[cop][condition]["aggregate"] = aggregate(result[cop][condition]["per_seed"])
    assert e.source_hashes() == before
    result["metadata"] = {"seeds": SEEDS, "pre_registered_rule": RULE,
        "b2_reference_conditions": ["3a", "3b_10", "3b_50", "3c_eps10", "3c_eps25"],
        "b2_reference_results": references(), "new_conditions": list(CONDITIONS),
        "ws1_heuristic_definition": __doc__, "fm1_flip_rate": .20, "fm2_flip_rate": .10,
        "tier": TIER, "gap_units": "percentage_points", "checkpoint_metric_units": "fractions",
        "category_accuracy": "not measured; category supplied",
        "determinism_per_seed": checks, "source_sha256": before,
        "new_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "incumbent_source_sha256": hashlib.sha256((OUT.parent/"moat_b2_seeds.json").read_bytes()).hexdigest()}
    result["metadata"]["determinism_hash"] = b.digest(result)
    OUT.write_bytes(b.canonical(result))
    write_summary(result)
    for cop in COPS:
        for condition in CONDITIONS:
            print(cop, condition, json.dumps(result[cop][condition]["aggregate"]), flush=True)


if __name__ == "__main__":
    main()

