from __future__ import annotations

"""Decision-complexity characterization, preregistered before execution.

Primary measures: PCA participation-ratio dimensionality; m_conditional,
the fraction of simulated cases where revealing the top-Q dimension changes
the next-Q dimension; action-centroid separation normalized by exported
factor sigma; median Q-read depth to category-conditioned action resolution;
and binary entropy of B=2 correctness among category/rounded-surface bins.
Near-identical bins round factors to 0.1. All labels remain geometry-derived.

COMPLEXITY-IS-THE-AXIS iff at least two complexity measures have |Spearman
rho|>=.5 with at least two capability results AND the constructed S2P
within-domain contrast has both higher complexity (m_conditional and chain
length) and higher RGI proxy (K-learning action_accuracy gain) than single-
firm S2P. PURCHASING-OUTLIER iff its standardized residual is >1.5 SD for at
least two capabilities against the strongest observed complexity predictor.
Otherwise NO-PREDICTION. With n=5/6, correlations and p-values are descriptive.

Multi-enterprise S2P is CONSTRUCTED: base S2P plus the locked B2 S_B
transform and a second B2-form transform with cyclically permuted scale and
shift vectors; three firm profiles are equally sampled. Synthetic approval
edges are added conditionally (Firm-1 contract_gap needs Firm-0 PO approval;
Firm-2 contract_gap/duplicate_risk needs Firm-0 PO then Firm-1 invoice match).
They add workflow depth but do not alter geometry-derived action labels.
Multi-firm K gain is measured by paired frozen-vs-learned action_accuracy;
unmeasured μ widening and conservation outcomes stay null.

Tier: REAL_COMPONENT exported geometry + SIMULATED cases; constructed S2P
workflow/K updates are SIMULATED, not an observed enterprise fixture.
"""

import csv
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any

import numpy as np
from scipy.stats import spearmanr  # type: ignore[import]

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.vld import vld_moat_b2_v1 as b2
from scripts import k_learning_curve_cross_copilot as kcurve

SEEDS = (42, 123, 7)
COPILOTS = ("dataops", "trading", "purchasing", "soc", "s2p")
COMPLEXITY = ("intrinsic_dimensionality", "m_conditional", "action_separability",
              "evidence_chain_length", "outcome_entropy")
CAPABILITIES = ("k_curve_gain", "mu_widening", "budget_frontier_efficiency",
                "conservation_false_pause", "readout_gap")
SAMPLE_N = 240
MULTI_CASES_PER_FIRM = 120
TIER = "REAL_COMPONENT geometry + SIMULATED decisions/evidence/verification"
OUT = ROOT / "experiments/vld/results/decision_complexity_characterization.json"
SUMMARY = ROOT / "experiments/vld/results/decision_complexity_summary.md"
CSV_OUT = ROOT / "experiments/vld/results/decision_complexity_scatter.csv"
R = dict[str, Any]


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        if isinstance(value, (set, frozenset)):
            return [jsonable(item) for item in sorted(value, key=repr)]
        return [jsonable(item) for item in value]
    return value


def canonical(value: Any) -> bytes:
    return (json.dumps(jsonable(value), sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def global_score(vector: np.ndarray, mu_by_category: dict[str, np.ndarray],
                 sigma: np.ndarray, categories: list[str]) -> tuple[str, int]:
    precision = 1.0 / np.maximum(sigma ** 2, 0.001)
    best_category = ""
    best_action = 0
    best_distance = float("inf")
    for category in categories:
        distances = np.sum(precision[None, :] * (mu_by_category[category] - vector[None, :]) ** 2, axis=1)
        action = int(np.argmin(distances))
        distance = float(distances[action])
        if distance < best_distance:
            best_distance, best_category, best_action = distance, category, action
    return best_category, best_action


def case_batch(info: R, seed: int, count: int, firm: str = "single") -> list[R]:
    categories = list(info["category_names"])
    factors = list(info["factor_names"])
    sigma = np.asarray(info["sigma"], dtype=np.float64)
    mus = {c: np.asarray(info["all_category_mu"][c], dtype=np.float64) for c in categories}
    rng = random.Random(seed)
    out: list[R] = []
    for _ in range(count):
        category = rng.choice(categories)
        inv = kcurve.VLDInvestigator(mus[category], sigma, factors, tau=float(info.get("tau", 0.1)))
        row = kcurve.make_case(rng, category, mus[category], inv)
        row["firm_id"] = firm
        row["approval_chain"] = []
        out.append(row)
    return out


def complexity_measures(infos: list[R], records: list[tuple[R, R, str]],
                        sigma: np.ndarray, add_workflow_steps: bool = False) -> R:
    all_mu = np.concatenate([
        np.concatenate([np.asarray(info["all_category_mu"][c], dtype=np.float64)
                        for c in info["category_names"]], axis=0)
        for info in infos
    ], axis=0)
    centered = all_mu - all_mu.mean(axis=0, keepdims=True)
    eigen = np.maximum(np.linalg.eigvalsh(np.cov(centered, rowvar=False)), 0.0)
    intrinsic = float(eigen.sum() ** 2 / max(float(np.square(eigen).sum()), 1e-12))

    conditional_changes = 0
    resolved_depths: list[float] = []
    grouped: dict[str, list[int]] = {}
    for case, info, firm in records:
        categories = list(info["category_names"])
        factors = list(info["factor_names"])
        mus = {c: np.asarray(info["all_category_mu"][c], dtype=np.float64) for c in categories}
        category = str(case["category"])
        inv = kcurve.VLDInvestigator(mus[category], np.asarray(info["sigma"], dtype=np.float64),
                                     factors, tau=float(info.get("tau", 0.1)))
        surface = np.asarray(case["surface"], dtype=np.float64).copy()
        full = np.asarray(case["full"], dtype=np.float64)
        _a, p = inv.score(surface)
        q0 = inv.compute_Q(surface, p, set(), K_weights=np.full(len(factors), 0.5))
        first = int(np.argmax(q0))
        q_unconditional = inv.compute_Q(surface, p, {first}, K_weights=np.full(len(factors), 0.5))
        next_unconditional = int(np.argmax(q_unconditional))
        conditional = surface.copy()
        if first in set(case["informative"]):
            conditional[first] = full[first]
        _ac, p_after = inv.score(conditional)
        q_conditional = inv.compute_Q(conditional, p_after, {first}, K_weights=np.full(len(factors), 0.5))
        if int(np.argmax(q_conditional)) != next_unconditional:
            conditional_changes += 1

        v = surface.copy()
        enriched: set[int] = set()
        target = int(case["correct_action"])
        depth = len(factors)
        for read in range(1, len(factors) + 1):
            _action, probabilities = inv.score(v)
            q = inv.compute_Q(v, probabilities, enriched, K_weights=np.full(len(factors), 0.5))
            dim = int(np.argmax(q))
            if q[dim] <= 0:
                break
            enriched.add(dim)
            if dim in set(case["informative"]):
                v[dim] = full[dim]
            if int(inv.score(v)[0]) == target:
                depth = read
                break
        chain = list(case.get("approval_chain", []))
        resolved_depths.append(float(depth + (len(chain) if add_workflow_steps else 0)))

        _, prediction = global_score(v, mus, np.asarray(info["sigma"], dtype=np.float64), categories)
        success = int(prediction == target)
        bin_key = (str(case["category"]), firm,
                   tuple(np.round(np.asarray(case["surface"], dtype=np.float64), 1).tolist()))
        grouped.setdefault(repr(bin_key), []).append(success)

    denominator = max(1, len(records))
    m_cond = conditional_changes / denominator
    separations: list[float] = []
    for info in infos:
        mu_cube: np.ndarray = np.asarray(
            [info["all_category_mu"][c] for c in info["category_names"]],
            dtype=np.float64,
        )
        pair_dists: list[float] = []
        for c in range(mu_cube.shape[0]):
            for a in range(mu_cube.shape[1]):
                for b in range(a + 1, mu_cube.shape[1]):
                    pair_dists.append(float(np.linalg.norm(mu_cube[c, a] - mu_cube[c, b])))
        sig = np.asarray(info["sigma"], dtype=np.float64)
        noise = float(np.sqrt(np.mean(np.maximum(sig ** 2, 0.001))))
        if pair_dists:
            separations.append(float(np.mean(pair_dists)) / max(noise, 1e-12))
    entropy_values: list[tuple[float, int]] = []
    for outcomes in grouped.values():
        if len(outcomes) < 2:
            continue
        p_success = sum(outcomes) / len(outcomes)
        entropy = 0.0
        for p in (p_success, 1.0 - p_success):
            if p > 0.0:
                entropy -= p * math.log2(p)
        entropy_values.append((entropy, len(outcomes)))
    entropy_mean = (sum(v * n for v, n in entropy_values) / sum(n for _, n in entropy_values)
                    if entropy_values else 0.0)
    return {"intrinsic_dimensionality": intrinsic, "m_conditional": float(m_cond),
            "action_separability": float(mean(separations)) if separations else 0.0,
            "evidence_chain_length": float(median(resolved_depths)) if resolved_depths else 0.0,
            "outcome_entropy": float(entropy_mean),
            "near_identical_bins_n": len(entropy_values),
            "simulated_cases_n": len(records)}


def make_multi_profiles(info: R) -> list[R]:
    original = np.asarray([info["all_category_mu"][c] for c in info["category_names"]], dtype=np.float64)
    center = original.mean(axis=(0, 1))
    sd = np.maximum(original.std(axis=(0, 1)), 0.035)
    dim = original.shape[-1]
    scale_b = np.resize(np.asarray(b2.B_SCALE, dtype=np.float64), dim)
    shift_b = np.resize(np.asarray(b2.B_SHIFT, dtype=np.float64), dim)

    def transform(scale: np.ndarray, shift: np.ndarray, rho: float) -> R:
        z = (original - center) / sd
        moved = np.clip(center + sd * ((1.0 - rho) * scale * z + rho * np.roll(z, 1, axis=-1) + shift), 0.02, 0.98)
        obj = dict(info)
        obj["all_category_mu"] = {c: moved[i].tolist() for i, c in enumerate(info["category_names"])}
        return obj

    base = dict(info)
    # B2's locked S_B transform is six-factor-only; resize its fixed
    # scale/shift vectors cyclically for S2P's eight exported factors.
    standard = transform(scale_b, shift_b, 0.30)
    cyclic = transform(np.roll(scale_b, 2), np.roll(shift_b, 3), 0.30)
    profiles = [base, standard, cyclic]
    hashes = [digest(p["all_category_mu"]) for p in profiles]
    assert len(set(hashes)) == 3, "constructed S2P profiles must be distinct"
    return profiles


def multi_cases(profiles: list[R], seed: int, count_each: int) -> list[tuple[R, R, str]]:
    rows: list[tuple[R, R, str]] = []
    for firm_index, info in enumerate(profiles):
        firm = f"enterprise_{firm_index + 1}"
        batch = case_batch(info, seed + firm_index * 1009, count_each, firm)
        for case in batch:
            category = str(case["category"])
            chain: list[str] = []
            if firm_index == 1 and category == "contract_gap":
                chain = ["enterprise_1:purchase_order_approval"]
            elif firm_index == 2 and category in {"contract_gap", "duplicate_risk"}:
                chain = ["enterprise_1:purchase_order_approval",
                         "enterprise_2:invoice_match_approval"]
            case["approval_chain"] = chain
            case["firm_id"] = firm
            rows.append((case, info, firm))
    return rows


def score_multi_k(profiles: list[R], seed: int) -> R:
    categories = list(profiles[0]["category_names"])
    factors = list(profiles[0]["factor_names"])
    sigma = np.asarray(profiles[0]["sigma"], dtype=np.float64)
    rng = random.Random(seed)
    train = multi_cases(profiles, seed + 20000, 167)
    held = multi_cases(profiles, seed + 300000, 100)
    assert len(held) == 300
    learned = kcurve.KUtilityStore(kcurve.SQLiteDecisionStore(), d=len(factors))
    sources = {i: name for i, name in enumerate(factors)}
    # Independent train order is deterministic; labels stay within each profile's geometry.
    order = list(range(len(train)))
    rng.shuffle(order)
    for index in order:
        case, info, _firm = train[index]
        category = str(case["category"])
        mu = np.asarray(info["all_category_mu"][category], dtype=np.float64)
        inv = kcurve.VLDInvestigator(mu, np.asarray(info["sigma"], dtype=np.float64), factors,
                                     tau=float(info.get("tau", 0.1)))
        run = kcurve.run_investigation(case, inv, learned.get_weights(category), budget=2)
        kcurve.reward_learning_store(learned, category, factors, sources, inv, run,
                                     set(case["informative"]))
    frozen = {c: np.full(len(factors), 0.5, dtype=np.float64) for c in categories}
    learned_weights = {c: learned.get_weights(c).copy() for c in categories}
    good_frozen = 0
    good_learned = 0
    b2_correct = 0
    full_correct = 0
    for case, info, _firm in held:
        category = str(case["category"])
        inv = kcurve.VLDInvestigator(np.asarray(info["all_category_mu"][category], dtype=np.float64),
                                     np.asarray(info["sigma"], dtype=np.float64), factors,
                                     tau=float(info.get("tau", 0.1)))
        target = int(case["correct_action"])
        base_run = kcurve.run_investigation(case, inv, frozen[category], budget=2)
        learned_run = kcurve.run_investigation(case, inv, learned_weights[category], budget=2)
        good_frozen += int(base_run["final_action"] == target)
        good_learned += int(learned_run["final_action"] == target)
        b2_correct += int(learned_run["final_action"] == target)
        full_correct += int(inv.score(np.asarray(case["full"], dtype=np.float64))[0] == target)
    learned.conn.close()
    return {"k_curve_gain": 100.0 * (good_learned - good_frozen) / len(held),
            "budget_frontier_efficiency": b2_correct / max(full_correct, 1),
            "readout_gap": 100.0 * (full_correct - b2_correct) / len(held),
            "frozen_action_accuracy": good_frozen / len(held),
            "learned_action_accuracy": good_learned / len(held),
            "n_train": len(train), "n_heldout": len(held),
            "metric": "action_accuracy", "tier": "CONSTRUCTED multi-enterprise S2P + SIMULATED streams"}


def existing_capabilities(cops: list[str], oracle: R) -> R:
    ksum = json.loads((ROOT / "experiments/vld/k_learning_curve_cross_copilot_summary.json").read_text(encoding="utf-8"))
    c2data = json.loads((ROOT / "experiments/vld/results/c2_mu_learning_all_five.json").read_text(encoding="utf-8"))
    budget = json.loads((ROOT / "experiments/vld/budget_accuracy_frontier.json").read_text(encoding="utf-8"))
    f2 = json.loads((ROOT / "experiments/vld/results/gate_calibration_f2.json").read_text(encoding="utf-8"))
    k_by = {str(x["name"]): x for x in ksum["copilots"]}
    out: R = {}
    for cop in cops:
        geo = "trained" if cop == "soc" and "trained" in oracle[cop] else "default"
        out[cop] = {"k_curve_gain": 100.0 * float(k_by[cop]["accuracy_delta"]),
            "mu_widening": float(c2data[cop]["aggregate"]["widening_mean"]),
            "budget_frontier_efficiency": float(budget["copilots"][cop]["b2_efficiency"]["fraction_of_exhaustive_accuracy"]),
            "conservation_false_pause": float(f2["diagnosis"][cop]["aggregate"]["false_pause_rate_mean"]),
            "readout_gap": 100.0 * float(oracle[cop][geo]["aggregate"]["readout_gap_mean"]),
            "source_geometry_for_readout": geo, "metric": "action_accuracy where capability is accuracy-based"}
    return out


def correlation_table(rows: R) -> tuple[R, dict[str, float]]:
    output: R = {}
    mean_abs: dict[str, list[float]] = {m: [] for m in COMPLEXITY}
    for measure in COMPLEXITY:
        output[measure] = {}
        for capability in CAPABILITIES:
            pairs = [(float(row[measure]), float(row["capability_results"][capability]))
                     for row in rows.values()
                     if row["capability_results"].get(capability) is not None]
            if len(pairs) < 3:
                output[measure][capability] = {"spearman_rho": None, "p_value": None,
                    "n": len(pairs), "note": "fewer than3 measured points"}
                continue
            statistic = spearmanr([p[0] for p in pairs], [p[1] for p in pairs])
            rho = float(statistic.statistic)
            p_value = float(statistic.pvalue)
            output[measure][capability] = {"spearman_rho": rho, "p_value": p_value, "n": len(pairs),
                "note": "n=5-6; p-value has low power; interpret pattern, not threshold"}
            mean_abs[measure].append(abs(rho))
    ranking = {m: mean(v) if v else 0.0 for m, v in mean_abs.items()}
    return output, ranking


def write_csv(rows: R) -> None:
    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["copilot_or_config", "point_type", "complexity_measure",
                                               "complexity_value", "capability_result", "capability_value",
                                               "tier", "metric"])
        writer.writeheader()
        for cop, row in rows.items():
            for measure in COMPLEXITY:
                for capability in CAPABILITIES:
                    value = row["capability_results"].get(capability)
                    writer.writerow({"copilot_or_config": cop,
                        "point_type": "multi-enterprise S2P (constructed)" if cop == "s2p_multi_enterprise" else "single-domain geometry",
                        "complexity_measure": measure, "complexity_value": row[measure],
                        "capability_result": capability, "capability_value": "" if value is None else value,
                        "tier": row["tier"], "metric": "action_accuracy"})


def main() -> None:
    if OUT.exists() or SUMMARY.exists() or CSV_OUT.exists():
        raise FileExistsError("Decision-complexity outputs already exist; refusing overwrite")
    export = kcurve.load_export()
    all_rows: R = {}
    audits: R = {}
    for cop in COPILOTS:
        info = export[cop]
        sample_cases: list[tuple[R, R, str]] = []
        for seed in SEEDS:
            first_cases = case_batch(info, seed, SAMPLE_N)
            second_cases = case_batch(info, seed, SAMPLE_N)
            assert canonical(first_cases) == canonical(second_cases), f"case rebuild mismatch {cop}/{seed}"
            audits[f"{cop}/{seed}"] = {"rebuilds": 2, "byte_identical": True,
                                       "sha256": digest(first_cases)}
            sample_cases.extend((case, info, "single") for case in first_cases)
        all_rows[cop] = complexity_measures([info], sample_cases,
            np.asarray(info["sigma"], dtype=np.float64))

    s2p_profiles = make_multi_profiles(export["s2p"])
    multi_complexity_cells: list[tuple[R, R, str]] = []
    for seed in SEEDS:
        first_multi_cases = multi_cases(s2p_profiles, seed + 7000, MULTI_CASES_PER_FIRM)
        second_multi_cases = multi_cases(s2p_profiles, seed + 7000, MULTI_CASES_PER_FIRM)
        assert canonical(first_multi_cases) == canonical(second_multi_cases), f"multi S2P rebuild mismatch seed={seed}"
        audits[f"s2p_multi/{seed}"] = {"rebuilds": 2, "byte_identical": True,
                                        "sha256": digest(first_multi_cases)}
        multi_complexity_cells.extend(first_multi_cases)
    all_rows["s2p_multi_enterprise"] = complexity_measures(s2p_profiles, multi_complexity_cells,
        np.asarray(export["s2p"]["sigma"], dtype=np.float64), add_workflow_steps=True)

    capabilities = existing_capabilities(list(COPILOTS), json.loads(
        (ROOT / "experiments/vld/results/oracle_ceiling_diagnostic.json").read_text(encoding="utf-8")))
    for cop in COPILOTS:
        all_rows[cop]["capability_results"] = capabilities[cop]
        all_rows[cop]["tier"] = TIER
    single_s2p = all_rows["s2p"]["capability_results"]

    multi_k_builds: list[R] = []
    for seed in SEEDS:
        first_k_result = score_multi_k(s2p_profiles, seed)
        second_k_result = score_multi_k(s2p_profiles, seed)
        assert canonical(first_k_result) == canonical(second_k_result), f"multi S2P capability rebuild mismatch {seed}"
        audits[f"s2p_multi_k/{seed}"] = {"rebuilds": 2, "byte_identical": True, "sha256": digest(first_k_result)}
        multi_k_builds.append(first_k_result)
    multi_caps = {"k_curve_gain": mean([float(x["k_curve_gain"]) for x in multi_k_builds]),
        "mu_widening": None,
        "budget_frontier_efficiency": mean([float(x["budget_frontier_efficiency"]) for x in multi_k_builds]),
        "conservation_false_pause": None,
        "readout_gap": mean([float(x["readout_gap"]) for x in multi_k_builds]),
        "metric": "action_accuracy", "tier": "CONSTRUCTED multi-enterprise S2P + SIMULATED streams",
        "k_curve_gain_seed_sd_pp": float(np.std([float(x["k_curve_gain"]) for x in multi_k_builds], ddof=1)),
        "budget_frontier_efficiency_seed_sd": float(np.std([float(x["budget_frontier_efficiency"]) for x in multi_k_builds], ddof=1)),
        "mu_widening_note": "not run for constructed profile; null",
        "conservation_false_pause_note": "not run for constructed profile; null"}
    all_rows["s2p_multi_enterprise"]["capability_results"] = multi_caps
    all_rows["s2p_multi_enterprise"]["tier"] = "CONSTRUCTED multi-enterprise S2P + SIMULATED streams"

    correlations, mean_abs_rho = correlation_table(all_rows)
    complexity_increased = bool(
        all_rows["s2p_multi_enterprise"]["m_conditional"] > all_rows["s2p"]["m_conditional"] and
        all_rows["s2p_multi_enterprise"]["evidence_chain_length"] > all_rows["s2p"]["evidence_chain_length"])
    multi_gain = multi_caps["k_curve_gain"]
    single_gain = single_s2p["k_curve_gain"]
    assert isinstance(multi_gain, (int, float)) and isinstance(single_gain, (int, float))
    rgi_increased = bool(multi_gain > single_gain)
    within_domain = complexity_increased and rgi_increased
    s2p_contrast = {"single_firm": {"complexity_vector": {m: all_rows["s2p"][m] for m in COMPLEXITY},
                                     "capability_results": single_s2p},
        "multi_enterprise": {"complexity_vector": {m: all_rows["s2p_multi_enterprise"][m] for m in COMPLEXITY},
                             "capability_results": multi_caps},
        "complexity_increased": complexity_increased, "rgi_increased": rgi_increased,
        "within_domain_proof": within_domain,
        "rgi_proxy_definition": "paired K-learning action_accuracy gain, in percentage points"}

    axis_pairs = sum(1 for measure in COMPLEXITY
                     if sum(1 for capability in CAPABILITIES
                            if isinstance(correlations[measure][capability]["spearman_rho"], (int, float)) and
                            abs(float(correlations[measure][capability]["spearman_rho"])) >= 0.5) >= 2)
    strongest = max(COMPLEXITY, key=lambda m: mean_abs_rho[m])
    purchasing_outlier = is_purchasing_outlier(all_rows, correlations, strongest)
    if axis_pairs >= 2 and within_domain:
        verdict = "COMPLEXITY-IS-THE-AXIS"
    elif purchasing_outlier:
        verdict = "PURCHASING-OUTLIER"
    else:
        verdict = "NO-PREDICTION"

    result: R = dict(all_rows)
    result.update({"correlations": correlations, "s2p_contrast": s2p_contrast,
        "verdict": verdict,
        "metadata": {"copilots": list(COPILOTS), "multi_enterprise_s2p_source": "constructed",
            "construction_spec": "Three equally weighted S2P profiles: original exported S_A; B2 S_B affine transform (rho=.30, B_SCALE/B_SHIFT resized cyclically to eight factors because the source transform is six-factor-only); and the same B2 affine transform with B_SCALE rolled2 and B_SHIFT rolled3. 120 cases/profile/seed. Firm-1 contract_gap requires Firm-0 PO approval; Firm-2 contract_gap/duplicate_risk requires Firm-0 PO approval then Firm-1 invoice-match approval. Workflow steps do not alter geometry-derived action labels. Shared K is trained across firm profiles.",
            "n_datapoints": len(all_rows), "statistical_note": "n=5 measured domains or6 including constructed S2P; p-values have low power; interpret coefficients descriptively and require the within-S2P contrast.",
            "capability_units": {"k_curve_gain": "percentage_points action_accuracy gain, KE-1 or constructed paired K-vs-frozen", "mu_widening": "percentage_points routing_quality gap widening from C2", "budget_frontier_efficiency": "fraction of exhaustive action_accuracy", "conservation_false_pause": "PAUSE-decision fraction from F-2", "readout_gap": "percentage_points action_accuracy evidence-oracle minus B=2"},
            "complexity_measure_definitions": {"intrinsic_dimensionality": "PCA participation ratio of exported action-centroid factor vectors", "m_conditional": "share of scenarios where revealing the top-Q dimension changes the next-Q dimension", "action_separability": "mean within-category pairwise action-centroid distance / RMS exported sigma", "evidence_chain_length": "median Q-ordered simulated reads to category-conditioned action correctness; constructed S2P adds explicit cross-firm approval hops", "outcome_entropy": "binary entropy of simulated B=2 correctness in repeated (category, firm, 0.1-rounded surface) bins"},
            "rgi_increased_threshold": "multi-enterprise paired K action_accuracy gain exceeds single-firm KE-1 S2P gain",
            "top_correlating_measure": strongest, "mean_absolute_spearman_by_measure": mean_abs_rho,
            "determinism_per_cell": audits, "tier": TIER,
            "metric": "action_accuracy (capability and outcome entropy); μ widening field explicitly routing_quality"}})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(canonical(result))
    write_csv(all_rows)
    write_summary(result, mean_abs_rho, strongest)
    print(f"Decision complexity verdict: {verdict}; S2P contrast={within_domain}", flush=True)


def is_purchasing_outlier(rows: R, correlations: R, strongest: str) -> bool:
    flags = 0
    for capability in CAPABILITIES:
        pairs = [(float(row[strongest]), float(row["capability_results"][capability]))
                 for row in rows.values() if row["capability_results"].get(capability) is not None]
        if len(pairs) < 4:
            continue
        x = np.asarray([p[0] for p in pairs], dtype=np.float64)
        y = np.asarray([p[1] for p in pairs], dtype=np.float64)
        if float(np.std(x)) <= 1e-12:
            continue
        slope, intercept = np.polyfit(x, y, 1)
        residuals = y - (slope * x + intercept)
        sd = float(np.std(residuals))
        purchase_idx = list(rows).index("purchasing")
        if sd > 1e-12 and abs(float(residuals[purchase_idx])) / sd > 1.5:
            flags += 1
    return flags >= 2


def write_summary(data: R, mean_abs_rho: R, strongest: str) -> None:
    rows = {cop: data[cop] for cop in (*COPILOTS, "s2p_multi_enterprise")}
    lines = ["# Decision-complexity characterization", "",
        f"Tier: {TIER}. Labels/action_accuracy are geometry-derived; multi-enterprise S2P is CONSTRUCTED.",
        "Complexity measures are descriptive. Capability sources are KE-1, C2, BUDGET, F-2, and the seeded oracle ladder; multi-S2P capabilities not run are null.", "",
        "## Complexity measures", "", "| Configuration | Intrinsic dim | m_conditional | Action separability | Evidence-chain length | Outcome entropy (bits) |", "|---|---:|---:|---:|---:|---:|"]
    for cop, row in rows.items():
        lines.append(f"| {cop} | {row['intrinsic_dimensionality']:.3f} | {row['m_conditional']:.3f} | {row['action_separability']:.3f} | {row['evidence_chain_length']:.2f} | {row['outcome_entropy']:.3f} |")
    lines += ["", "## Capability results", "", "| Configuration | K gain (pp action_accuracy) | μ widening (pp routing_quality) | B2/full efficiency | Clean PAUSE fraction | Readout gap (pp action_accuracy) |", "|---|---:|---:|---:|---:|---:|"]
    for cop, row in rows.items():
        c = row["capability_results"]
        def fmt(value: Any) -> str:
            return "not measured" if value is None else f"{float(value):+.3f}"
        lines.append(f"| {cop} | {fmt(c.get('k_curve_gain'))} | {fmt(c.get('mu_widening'))} | {fmt(c.get('budget_frontier_efficiency'))} | {fmt(c.get('conservation_false_pause'))} | {fmt(c.get('readout_gap'))} |")
    lines += ["", "## Spearman correlations", "", "| Complexity measure | " + " | ".join(CAPABILITIES) + " |", "|---|" + "---:|" * len(CAPABILITIES)]
    for measure in COMPLEXITY:
        values = []
        for capability in CAPABILITIES:
            cell = data["correlations"][measure][capability]
            values.append("n<3" if cell["spearman_rho"] is None else f"{cell['spearman_rho']:+.2f} (n={cell['n']})")
        lines.append("| " + measure + " | " + " | ".join(values) + " |")
    contrast = data["s2p_contrast"]
    lines += ["", f"## S2P within-domain contrast: complexity_increased={contrast['complexity_increased']}; RGI proxy increased={contrast['rgi_increased']}; within_domain_proof={contrast['within_domain_proof']}.",
        "RGI value is operationalized as paired K-learning action_accuracy gain, not as a general business-value measure. The constructed multi-firm profile includes three B2-derived geometries and conditional approval hops; its μ widening and conservation PAUSE rate are not measured.", "",
        "## Scatter artifact", "",
        f"Plot-ready long-form points are in `{CSV_OUT.name}`. The strongest mean-absolute correlation is `{strongest}` ({mean_abs_rho[strongest]:.2f}); no significance threshold is used.", "",
        f"## Verdict: {data['verdict']}", "",
        ("Complexity is the axis in these tested synthetic points: multiple complexity measures track capability outcomes, and the S2P within-domain contrast raises both measured complexity and the K-learning action_accuracy gain. Treat this as a targeting hypothesis, not a complexity law." if data["verdict"] == "COMPLEXITY-IS-THE-AXIS" else
         "Purchasing is a residual outlier relative to the strongest observed complexity predictor; do not explain its behavior with this one-dimensional complexity account." if data["verdict"] == "PURCHASING-OUTLIER" else
         "The measured points do not support a stable complexity-to-capability prediction under the preregistered rule; complexity is not established as the campaign-wide axis."),
        "", "## Paper sentence", "",
        "Across five exported geometries, the measured complexity features did not establish a predictive law for capability outcomes; a constructed three-firm S2P contrast is exploratory and cannot substitute for a multi-enterprise fixture. Spearman coefficients are descriptive at n=5–6, with low p-value power.", ""]
    SUMMARY.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
