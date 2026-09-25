"""C7: paired B=2 flat-read versus post-read correlated-evidence refinement.

Pre-registration (before running): primary metric is routing_quality
(informative acquired dimensions / actual acquired dimensions); the secondary
metric is action_accuracy (geometry-derived correct action / held-out cases).
The B=2 flat-read claim holds iff no refinement arm improves routing_quality
over A0 by more than 0.02 at two or more of the three seeds for any copilot.
All arms read exactly two dimensions. Evaluation uses 50 fixed held-out cases
per seed/copoly/curve at each checkpoint, learning uses shared generated
geometry-derived cases, and training stops after three consecutive checkpoint
increments with <=1pp movement in both metrics, or at 2,000 decisions.

Refine operator (designed for this experiment; not present in production):
retain the base posterior from the same B=2 read vector and add the correlated-
Gaussian log-likelihood correction for the two read residuals, with fixed
rho=0.25. Scale that correction by the geometric mean of the two selected
dimensions' Q*K reliabilities divided by their sum. A depth step moves logits
halfway from the previous logits toward (base logits + this evidence-derived
correction); depths 1/2/3 therefore apply one/two/three damped updates. It
re-scores only the same two already-read coordinates and uses no oracle labels
or unrevealed values to choose an action. K learning reuses the existing
K-curve harness update helper; only the final action feedback differs by arm.

Tier: REAL_COMPONENT exported geometry + SIMULATED streams/verification.
Labels are nearest-centroid geometry-derived, not LLM-derived.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
from statistics import mean, stdev
from typing import Any, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
_HARNESS_PATH = ROOT / "scripts" / "k_learning_curve_cross_copilot.py"
_HARNESS_SPEC = importlib.util.spec_from_file_location("c7_kcurve_harness", _HARNESS_PATH)
if _HARNESS_SPEC is None or _HARNESS_SPEC.loader is None:
    raise ImportError(f"Could not load K-curve harness at {_HARNESS_PATH}")
kcurve = importlib.util.module_from_spec(_HARNESS_SPEC)
_HARNESS_SPEC.loader.exec_module(kcurve)
kcurve = cast(Any, kcurve)
from copilot_sdk.scoring.investigation import KUtilityStore, VLDInvestigator


OUT_DIR = ROOT / "experiments" / "vld" / "results"
COPILOTS = ("soc", "dataops", "trading")
SEEDS = (42, 123, 7)
ARMS = {"A0_flat": 0, "A1_depth1": 1, "A2_depth2": 2, "A3_depth3": 3}
MAX_DECISIONS = 2000
CHECKPOINT_INTERVAL = 50
EVAL_CASES = 50
MIN_CONVERGENCE_DECISION = 200
RHO = 0.25
DAMPING = 0.5
MATERIALITY = 0.02
FLAT_TOLERANCE = 0.01


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - float(np.max(logits))
    exp = np.exp(shifted)
    result: np.ndarray = exp / float(np.sum(exp))
    return result


def _run_episode(
    case: dict[str, Any],
    investigator: VLDInvestigator,
    k_weights: np.ndarray,
    depth: int,
) -> dict[str, Any]:
    """Run the harness's sequential Q-ranked B=2 reads and optional refine."""
    vector = np.asarray(case["surface"], dtype=np.float64).copy()
    full = np.asarray(case["full"], dtype=np.float64)
    informative = set(case["informative"])
    selected: list[int] = []
    selected_q: list[float] = []
    records: list[tuple[int, np.ndarray, np.ndarray]] = []
    enriched: set[int] = set()

    for _ in range(2):
        _action, probs, _margin = kcurve.score(investigator, vector)
        q = investigator.compute_Q(vector, probs, enriched, K_weights=k_weights)
        dim = int(np.argmax(q))
        if float(q[dim]) <= 0.0:
            break
        selected.append(dim)
        selected_q.append(float(q[dim]))
        enriched.add(dim)
        before = vector.copy()
        if dim in informative:
            vector[dim] = full[dim]
        records.append((dim, before, vector.copy()))

    _base_action, base_probs, _margin = kcurve.score(investigator, vector)
    final_probs = base_probs.copy()
    if depth > 0 and len(selected) == 2:
        # Reliability combines the actual Q rank with the learned K weight.
        reliabilities = [
            max(selected_q[i], 0.0) * max(float(k_weights[selected[i]]), 0.1)
            for i in range(2)
        ]
        qk_scale = math.sqrt(reliabilities[0] * reliabilities[1]) / (
            reliabilities[0] + reliabilities[1] + 1e-12
        )
        mu = investigator.mu
        sigmas = np.maximum(investigator.sigma, math.sqrt(0.001))
        residuals = np.column_stack(
            [
                (vector[dim] - mu[:, dim]) / sigmas[dim]
                for dim in selected
            ]
        )
        # Difference between correlated and independent 2-D Gaussian terms.
        z1 = residuals[:, 0]
        z2 = residuals[:, 1]
        correlated_delta = (
            2.0 * RHO * z1 * z2 - (RHO**2) * (z1**2 + z2**2)
        ) / (1.0 - RHO**2) / investigator.tau
        correction = qk_scale * correlated_delta
        base_logits = np.log(np.maximum(base_probs, 1e-300))
        target_logits = base_logits + correction
        logits = base_logits.copy()
        for _ in range(depth):
            logits = (1.0 - DAMPING) * logits + DAMPING * target_logits
        final_probs = _softmax(logits)

    final_action = int(np.argmax(final_probs))
    surface_action = int(kcurve.score(investigator, np.asarray(case["surface"]))[0])
    correct = final_action == int(case["correct_action"])
    return {
        "selected": selected,
        "selected_q": selected_q,
        "step_records": records,
        "final_action": final_action,
        "final_probs": final_probs,
        "correct": bool(correct),
        "saved": bool(surface_action != int(case["correct_action"]) and correct),
        "hurt": bool(surface_action == int(case["correct_action"]) and not correct),
        "informative_reads": sum(dim in informative for dim in selected),
        "total_reads": len(selected),
    }


def _evaluate(
    cases: list[dict[str, Any]],
    categories: list[str],
    mu_by_category: dict[str, np.ndarray],
    sigma: np.ndarray,
    factor_names: list[str],
    tau: float,
    store: KUtilityStore,
    depth: int,
) -> dict[str, float]:
    weights = {c: store.get_weights(c).copy() for c in categories}
    reads = informative = correct = 0
    for case in cases:
        investigator = VLDInvestigator(
            mu_by_category[case["category"]], sigma, factor_names, tau=tau
        )
        run = _run_episode(case, investigator, weights[case["category"]], depth)
        reads += int(run["total_reads"])
        informative += int(run["informative_reads"])
        correct += int(run["correct"])
    return {
        "routing_quality": informative / reads if reads else 0.0,
        "action_accuracy": correct / len(cases),
    }


def _run_curve(
    copilot: str,
    seed: int,
    arm: str,
    depth: int,
    info: dict[str, Any],
    train_cases: list[dict[str, Any]],
    eval_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factors = list(info["factor_names"])
    sources = {int(k): v for k, v in kcurve.DIMENSION_SOURCES.get(copilot, {}).items()}
    for idx, factor in enumerate(factors):
        sources.setdefault(idx, factor)
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64)
    if len(sigma) != len(factors):
        sigma = np.ones(len(factors), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mu_by_category = {
        category: np.asarray(info["all_category_mu"][category], dtype=np.float64)
        for category in categories
    }
    memory = kcurve.SQLiteDecisionStore()
    store = KUtilityStore(memory, d=len(factors))
    checkpoints: list[dict[str, Any]] = []
    stable_steps = 0
    try:
        for index, case in enumerate(train_cases, start=1):
            category = str(case["category"])
            investigator = VLDInvestigator(
                mu_by_category[category], sigma, factors, tau=tau
            )
            run = _run_episode(case, investigator, store.get_weights(category), depth)
            kcurve.reward_learning_store(
                store,
                category,
                factors,
                sources,
                investigator,
                run,
                set(case["informative"]),
            )
            if index % CHECKPOINT_INTERVAL == 0:
                metrics = _evaluate(
                    eval_cases,
                    categories,
                    mu_by_category,
                    sigma,
                    factors,
                    tau,
                    store,
                    depth,
                )
                point = {"decision_count": index, **metrics}
                checkpoints.append(point)
                if len(checkpoints) > 1:
                    prev = checkpoints[-2]
                    flat = all(
                        abs(float(point[key]) - float(prev[key])) <= FLAT_TOLERANCE
                        for key in ("routing_quality", "action_accuracy")
                    )
                    stable_steps = stable_steps + 1 if flat else 0
                if (
                    index >= MIN_CONVERGENCE_DECISION
                    and stable_steps >= 3
                ):
                    break
        final = checkpoints[-1]
        return {
            "seed": seed,
            "final_routing": float(final["routing_quality"]),
            "final_action": float(final["action_accuracy"]),
            "convergence_point": int(final["decision_count"]),
            "converged": stable_steps >= 3,
            "checkpoints": checkpoints,
            "k_by_category": {
                category: [float(value) for value in store.get_weights(category)]
                for category in categories
            },
        }
    finally:
        memory.conn.close()


def _std(values: list[float]) -> float:
    return stdev(values) if len(values) > 1 else 0.0


def _seed_build(copilot: str, seed: int, info: dict[str, Any]) -> dict[str, Any]:
    categories = list(info.get("category_names") or info["all_category_mu"].keys())
    factors = list(info["factor_names"])
    sigma = np.asarray(info.get("sigma") or [1.0] * len(factors), dtype=np.float64)
    if len(sigma) != len(factors):
        sigma = np.ones(len(factors), dtype=np.float64)
    tau = float(info.get("tau", 0.1))
    mu_by_category = {
        category: np.asarray(info["all_category_mu"][category], dtype=np.float64)
        for category in categories
    }
    generation_rng = random.Random(seed + sum(ord(ch) for ch in copilot))
    train_cases: list[dict[str, Any]] = []
    for _ in range(MAX_DECISIONS):
        category = generation_rng.choice(categories)
        inv = VLDInvestigator(mu_by_category[category], sigma, factors, tau=tau)
        train_cases.append(kcurve.make_case(generation_rng, category, mu_by_category[category], inv))
    eval_rng = random.Random(seed + 1_000_003 + sum(ord(ch) for ch in copilot))
    eval_cases: list[dict[str, Any]] = []
    for _ in range(EVAL_CASES):
        category = eval_rng.choice(categories)
        inv = VLDInvestigator(mu_by_category[category], sigma, factors, tau=tau)
        eval_cases.append(kcurve.make_case(eval_rng, category, mu_by_category[category], inv))

    return {
        arm: _run_curve(copilot, seed, arm, depth, info, train_cases, eval_cases)
        for arm, depth in ARMS.items()
    }


def _arm_aggregate(per_seed: dict[str, dict[str, Any]]) -> dict[str, float]:
    routing = [float(row["final_routing"]) for row in per_seed.values()]
    action = [float(row["final_action"]) for row in per_seed.values()]
    return {
        "routing_mean": mean(routing),
        "routing_std": _std(routing),
        "action_mean": mean(action),
        "action_std": _std(action),
    }


def _build_result() -> tuple[dict[str, Any], dict[str, str]]:
    exports = kcurve.load_export()
    output: dict[str, Any] = {}
    seed_hashes: dict[str, str] = {}
    for copilot in COPILOTS:
        info = exports[copilot]
        arm_rows: dict[str, dict[str, Any]] = {
            arm: {"per_seed": {}} for arm in ARMS
        }
        for seed in SEEDS:
            # Two complete independent rebuilds per seed; compare canonical
            # bytes before retaining the first rebuild's rows.
            first = _seed_build(copilot, seed, info)
            second = _seed_build(copilot, seed, info)
            first_bytes = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
            second_bytes = json.dumps(second, sort_keys=True, separators=(",", ":")).encode()
            if first_bytes != second_bytes:
                raise RuntimeError(f"determinism failure: {copilot} seed={seed}")
            digest = hashlib.sha256(first_bytes).hexdigest()
            seed_hashes[f"{copilot}:{seed}"] = digest
            for arm, run in first.items():
                arm_rows[arm]["per_seed"][str(seed)] = run
        for arm in ARMS:
            arm_rows[arm]["aggregate"] = _arm_aggregate(arm_rows[arm]["per_seed"])
        baseline = arm_rows["A0_flat"]["per_seed"]
        for arm in ("A1_depth1", "A2_depth2", "A3_depth3"):
            per_seed = arm_rows[arm]["per_seed"]
            routing_delta = [
                float(per_seed[str(seed)]["final_routing"])
                - float(baseline[str(seed)]["final_routing"])
                for seed in SEEDS
            ]
            action_delta = [
                float(per_seed[str(seed)]["final_action"])
                - float(baseline[str(seed)]["final_action"])
                for seed in SEEDS
            ]
            arm_rows[arm]["delta_vs_A0"] = {
                "routing_mean": mean(routing_delta),
                "routing_std": _std(routing_delta),
                "routing_per_seed": {
                    str(seed): routing_delta[i] for i, seed in enumerate(SEEDS)
                },
                "action_mean": mean(action_delta),
                "action_std": _std(action_delta),
                "action_per_seed": {
                    str(seed): action_delta[i] for i, seed in enumerate(SEEDS)
                },
                "beats_A0_by_2pp": sum(value > MATERIALITY for value in routing_delta),
            }
        output[copilot] = arm_rows
    output["metadata"] = {
        "seeds": list(SEEDS),
        "refine_operator": (
            "rho=.25 correlated-Gaussian log-likelihood correction on the same two read residuals; "
            "Q*K reliability scaling; repeated half-damped logits update"
        ),
        "refine_operator_source": "designed for this experiment; production source unchanged",
        "pre_registered_rule": "B=2 holds iff no refine arm beats A0 by >2pp routing_quality at >=2/3 seeds for every copilot",
        "acquisition_budget": 2,
        "max_decisions": MAX_DECISIONS,
        "checkpoint_interval": CHECKPOINT_INTERVAL,
        "evaluation_cases_per_checkpoint": EVAL_CASES,
        "convergence_rule": "three consecutive checkpoint-to-checkpoint increments <=1pp in both routing_quality and action_accuracy; minimum 200 decisions; maximum 2000",
        "metric_definitions": {
            "routing_quality": "informative acquired dimensions / actual acquired dimensions",
            "action_accuracy": "geometry-derived correct action / held-out scenarios",
            "category_accuracy": "not measured; category is supplied by the scenario generator",
        },
        "tier": "REAL_COMPONENT geometry + SIMULATED streams/verification",
        "label_source": "nearest-centroid exported geometry",
        "paired_cases": "same generated train cases and fixed held-out cases across A0-A3 within copilot/seed",
        "determinism_two_rebuild_sha256_per_seed": seed_hashes,
        "contextual_budget_frontier_routing_quality": {
            "soc": 0.789,
            "dataops": 0.595,
            "trading": 0.7255,
            "comparability_note": "BUDGET five-seed/500-train/200-eval protocol; not a matched C7 control",
        },
    }
    return output, seed_hashes


def _summary(payload: dict[str, Any]) -> str:
    rows: list[str] = []
    delta_rows: list[str] = []
    material_breaks: list[str] = []
    for copilot in COPILOTS:
        data = payload[copilot]
        for arm in ARMS:
            agg = data[arm]["aggregate"]
            rows.append(
                f"| {copilot} | {arm} | {agg['routing_mean']:.3f} ± {agg['routing_std']:.3f} | "
                f"{agg['action_mean']:.3f} ± {agg['action_std']:.3f} |"
            )
            if arm == "A0_flat":
                continue
            delta = data[arm]["delta_vs_A0"]
            per_seed = ", ".join(
                f"{seed}: {100*delta['routing_per_seed'][str(seed)]:+.1f}pp"
                for seed in SEEDS
            )
            delta_rows.append(
                f"| {copilot} | {arm} | {100*delta['routing_mean']:+.2f}pp ± "
                f"{100*delta['routing_std']:.2f}pp | {per_seed} | "
                f"{delta['beats_A0_by_2pp']}/3 |"
            )
            if delta["beats_A0_by_2pp"] >= 2:
                material_breaks.append(f"{copilot}/{arm}")
    all_rows = [
        "# C7 — Looped-Operator Depth",
        "",
        "Tier: REAL_COMPONENT exported geometry + SIMULATED streams/verification. Truth labels are nearest-centroid geometry-derived. Metrics: routing_quality (informative reads / actual reads) and action_accuracy (correct geometry-derived action / held-out cases); category_accuracy is not measured because category is supplied.",
        "",
        "## Operator and protocol",
        "",
        "GATE-B1: no existing iterative post-read refine hook was found. This experiment adds a script-only operator: correlated-Gaussian correction (rho=0.25) to the action logits using residuals of the same two acquired dimensions, scaled by their selected Q×K reliability. Each iteration damps halfway toward the corrected logits. No third read or oracle label enters scoring. A0-A3 share per-seed training/evaluation cases; K updates reuse the K-curve harness helper. Convergence means three successive checkpoint-to-checkpoint movements no larger than 1pp in both metrics, after at least 200 decisions; cap 2,000.",
        "",
        "Pre-registered rule: B=2 holds iff no refine arm beats A0 by >2pp routing_quality at at least 2/3 seeds for any copilot.",
        "",
        "## Results by copilot and arm",
        "",
        "| Copilot | Arm | routing_quality mean ± SD | action_accuracy mean ± SD |",
        "|---|---|---:|---:|",
        *rows,
        "",
        "## Delta versus A0",
        "",
        "| Copilot | Arm | routing_quality delta mean ± SD | Per-seed routing_quality delta | Seeds >2pp |",
        "|---|---|---:|---|---:|",
        *delta_rows,
        "",
        "## Depth pattern and verdict",
        "",
        "Depth comparisons are paired within each copilot/seed. The tables report both positive and negative changes; action_accuracy is not substituted for routing_quality in the registered decision rule.",
        "",
    ]
    if material_breaks:
        all_rows.extend([
            f"The registered threshold is crossed by: {', '.join(material_breaks)}. **B=2 sufficiency is weakened** for those copilot/arm comparisons.",
            "",
            "Paper sentence: ‘On the tested geometry and simulated streams, same-evidence iterative refinement changed routing_quality by the amounts shown; where the gain exceeded 2pp at two or more seeds, the architecture should acknowledge a potentially useful refine step. This designed operator requires independent replication before being treated as a production recommendation.’",
        ])
    else:
        all_rows.extend([
            "No refine arm exceeded +2pp routing_quality over A0 at two or more of three seeds for any copilot. **B=2 holds under the preregistered materiality rule for this tested operator and these streams.**",
            "",
            "Paper sentence: ‘For a script-only correlated-evidence refine operator operating on the same two acquired dimensions, B=2 flat reads remained sufficient under a 2pp routing_quality materiality threshold; iterative refinement added no material routing_quality gain in the tested geometry-derived simulations.’",
        ])
    all_rows.extend([
        "",
        "## Baseline context and null-stakes",
        "",
        "The separate BUDGET experiment reported B=2 routing_quality of SOC 78.9%, DataOps 59.5%, and Trading 72.55%. It used five different seeds and a 500-training/200-evaluation protocol, so it is context rather than a matched comparator; A0 here is the proper paired baseline.",
        "",
        "Null-stakes: a failure to beat A0 does not establish that all possible refinement mechanisms are useless; it only bounds this preregistered correlated-evidence operator at this depth and evaluation design. Any negative deltas remain evidence against adding this operator, not proof about every alternative.",
        "",
        "Convergence status by seed and arm is available in the JSON (`converged`, `convergence_point`, full checkpoints). A max-cap run is reported as not converged rather than relabeled as convergence.",
        "",
    ])
    return "\n".join(all_rows)


def main() -> None:
    payload, _seed_hashes = _build_result()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "c7_looped_depth.json"
    summary_path = OUT_DIR / "c7_looped_depth_summary.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(_summary(payload), encoding="utf-8")
    for copilot in COPILOTS:
        print(copilot)
        for arm in ARMS:
            aggregate = payload[copilot][arm]["aggregate"]
            print(
                f"  {arm}: routing_quality={aggregate['routing_mean']:.4f} "
                f"±{aggregate['routing_std']:.4f}, action_accuracy="
                f"{aggregate['action_mean']:.4f}±{aggregate['action_std']:.4f}"
            )
    print(f"Wrote {json_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
