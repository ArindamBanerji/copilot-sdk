"""
Factor-0 Debiased Test Battery v4

Removes confirmation bias from the experiment by adding:

1. NULL TEST: What does d'/margin look like for the CURRENT uniform
   ladder? If current d' is also low, proposed values aren't worse.

2. RANDOM BASELINE: What do random centroid values produce? If random
   values also pass d' >= 0.5, the gate is too easy.

3. SIMPLE HEURISTIC: A naive "escalate=0.8, suppress=0.15" heuristic.
   If it performs comparably, the panel added no value.

4. PERTURBATION: Jitter proposed values within inter-model IQR.
   Do results hold across 100 random perturbations?

5. ADVERSARIAL BOUNDARY: How far can each centroid move before an
   action flips? This measures robustness, not fit.

6. CURRENT d': The d' metric on the CURRENT centroids — the fair
   comparison Opus's gate should have included.

Run from: gen-ai-roi-demo-v4-v50/backend/
"""

import json
import sys
import os
import numpy as np

PROPOSED_SCENARIO_F0 = {
    "SOC-CA-01": 0.847, "SOC-CA-02": 0.450, "SOC-CA-03": 0.400,
    "SOC-CA-04": 0.145, "SOC-CA-05": 0.135, "SOC-CA-06": 0.188,
    "SOC-TI-01": 0.163, "SOC-TI-02": 0.363, "SOC-TI-03": 0.177,
    "SOC-TI-04": 0.137, "SOC-TI-05": 0.147, "SOC-TI-06": 0.168,
    "SOC-LM-01": 0.825, "SOC-LM-02": 0.800, "SOC-LM-03": 0.212,
    "SOC-LM-04": 0.150, "SOC-LM-05": 0.150, "SOC-LM-06": 0.155,
    "SOC-DE-01": 0.267, "SOC-DE-02": 0.450, "SOC-DE-03": 0.212,
    "SOC-DE-04": 0.373, "SOC-DE-05": 0.300, "SOC-DE-06": 0.175,
    "SOC-IT-01": 0.475, "SOC-IT-02": 0.350, "SOC-IT-03": 0.225,
    "SOC-IT-04": 0.147, "SOC-IT-05": 0.135, "SOC-IT-06": 0.188,
    "SOC-CI-01": 0.838, "SOC-CI-02": 0.812, "SOC-CI-03": 0.483,
    "SOC-CI-04": 0.367, "SOC-CI-05": 0.367, "SOC-CI-06": 0.333,
}

PROPOSED_F0_CENTROIDS = np.array([
    [0.649, 0.400, 0.140, 0.188],  # credential_access
    [0.263, 0.177, 0.142, 0.168],  # malware_execution
    [0.812, 0.212, 0.150, 0.155],  # lateral_movement
    [0.358, 0.212, 0.337, 0.175],  # data_exfiltration
    [0.413, 0.225, 0.141, 0.188],  # insider_threat
    [0.825, 0.483, 0.367, 0.333],  # cloud_infrastructure
])

# Inter-model IQR per scenario (from panel analysis)
SCENARIO_IQR = {
    "SOC-CA-01": 0.025, "SOC-CA-02": 0.165, "SOC-CA-03": 0.010,
    "SOC-CA-04": 0.025, "SOC-CA-05": 0.025, "SOC-CA-06": 0.005,
    "SOC-TI-01": 0.040, "SOC-TI-02": 0.130, "SOC-TI-03": 0.100,
    "SOC-TI-04": 0.005, "SOC-TI-05": 0.050, "SOC-TI-06": 0.025,
    "SOC-LM-01": 0.150, "SOC-LM-02": 0.225, "SOC-LM-03": 0.030,
    "SOC-LM-04": 0.025, "SOC-LM-05": 0.060, "SOC-LM-06": 0.015,
    "SOC-DE-01": 0.235, "SOC-DE-02": 0.090, "SOC-DE-03": 0.070,
    "SOC-DE-04": 0.025, "SOC-DE-05": 0.025, "SOC-DE-06": 0.015,
    "SOC-IT-01": 0.065, "SOC-IT-02": 0.160, "SOC-IT-03": 0.020,
    "SOC-IT-04": 0.025, "SOC-IT-05": 0.025, "SOC-IT-06": 0.020,
    "SOC-CI-01": 0.170, "SOC-CI-02": 0.260, "SOC-CI-03": 0.030,
    "SOC-CI-04": 0.005, "SOC-CI-05": 0.000, "SOC-CI-06": 0.025,
}

CATS = [
    "credential_access", "malware_execution", "lateral_movement",
    "data_exfiltration", "insider_threat", "cloud_infrastructure",
]
ACTS = ["escalate", "investigate", "suppress", "monitor"]


def build_factor_vector(scenario):
    f = scenario["factors"]
    f0 = f.get("travel_match", f.get("privileged_identity_context", 0.5))
    return np.array([
        f0, f["asset_criticality"], f["threat_intel_enrichment"],
        f["pattern_history"], f["time_anomaly"], f["device_trust"],
    ])


def build_tensor_with_f0(base_tensor, f0_column):
    """Replace factor-0 column in base tensor with given 6x4 values."""
    mu = base_tensor.copy()
    for c in range(6):
        for a in range(4):
            mu[c, a, 0] = f0_column[c, a]
    return mu


def score_all(scenarios, factor_vectors, centroids):
    """Score all scenarios, return (n_correct, per_scenario_results)."""
    results = []
    correct = 0
    for s in scenarios:
        sid = s["scenario_id"]
        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        fv = factor_vectors[sid]

        dists = [float(np.sum((fv - centroids[cat_idx, a]) ** 2))
                 for a in range(4)]
        winner = int(np.argmin(dists))
        sorted_d = sorted(dists)
        margin = sorted_d[1] - sorted_d[0]

        if winner == act_idx:
            correct += 1

        # Softmax confidence
        tau = 0.1
        neg_d = [-d / tau for d in dists]
        max_nd = max(neg_d)
        exp_vals = [np.exp(nd - max_nd) for nd in neg_d]
        total_exp = sum(exp_vals)
        # Confidence for the WINNER (what routing policy sees)
        conf_winner = exp_vals[winner] / total_exp
        # Confidence for the EXPECTED action (what correctness needs)
        conf_expected = exp_vals[act_idx] / total_exp

        results.append({
            "sid": sid, "cat_idx": cat_idx, "act_idx": act_idx,
            "winner": winner, "margin": margin,
            "confidence": conf_expected,
            "conf_winner": conf_winner,
            "correct": winner == act_idx,
        })
    return correct, results


def compute_d_prime(scenarios, scenario_f0_values, centroids_f0):
    """Compute d' per category for given scenario values and centroid f0 column."""
    scenario_map = {s["scenario_id"]: s for s in scenarios}
    results = {}

    for c, cat in enumerate(CATS):
        esc_vals = [scenario_f0_values[s["scenario_id"]]
                    for s in scenarios
                    if s["category_index"] == c and s["expected_action_index"] == 0]
        sup_vals = [scenario_f0_values[s["scenario_id"]]
                    for s in scenarios
                    if s["category_index"] == c and s["expected_action_index"] == 2]

        esc_sd = np.std(esc_vals, ddof=0) if len(esc_vals) > 1 else 0.0
        sup_sd = np.std(sup_vals, ddof=0) if len(sup_vals) > 1 else 0.0

        if esc_sd > 0 or sup_sd > 0:
            pooled_sd = np.sqrt((esc_sd ** 2 + sup_sd ** 2) / 2)
        else:
            pooled_sd = 0.0

        separation = centroids_f0[c, 0] - centroids_f0[c, 2]

        if pooled_sd < 0.001:
            d_prime = float("inf") if abs(separation) > 0.001 else 0.0
        else:
            d_prime = abs(separation) / pooled_sd

        results[cat] = {
            "separation": separation,
            "pooled_sd": pooled_sd,
            "d_prime": d_prime,
            "esc_sd": esc_sd,
            "sup_sd": sup_sd,
        }
    return results


def compute_min_confidence(results):
    """Return minimum confidence margin vs 0.62 threshold."""
    margins = [r["confidence"] - 0.62 for r in results]
    return min(margins) if margins else 0.0


def main():
    scenario_path = "app/data/soc_eval_scenarios.json"
    if not os.path.exists(scenario_path):
        print("ERROR: Run from gen-ai-roi-demo-v4-v50/backend/")
        sys.exit(1)

    sys.path.insert(0, os.getcwd())
    from app.domains.soc.config import SOC_PROFILE_CENTROIDS

    data = json.load(open(scenario_path))
    scenarios = data if isinstance(data, list) else data.get("scenarios", [])

    rng = np.random.RandomState(42)

    # Build factor vectors for current and proposed
    fv_current = {}
    fv_proposed = {}
    for s in scenarios:
        sid = s["scenario_id"]
        fv_current[sid] = build_factor_vector(s)
        fv_p = build_factor_vector(s).copy()
        fv_p[0] = PROPOSED_SCENARIO_F0[sid]
        fv_proposed[sid] = fv_p

    # Current scenario f0 values (for d' computation)
    current_scenario_f0 = {}
    for s in scenarios:
        sid = s["scenario_id"]
        f = s["factors"]
        current_scenario_f0[sid] = f.get("travel_match",
                                          f.get("privileged_identity_context", 0.5))

    mu_curr = SOC_PROFILE_CENTROIDS
    mu_prop = build_tensor_with_f0(mu_curr, PROPOSED_F0_CENTROIDS)

    # Current f0 column for d' computation
    current_f0_centroids = np.array([
        [mu_curr[c, a, 0] for a in range(4)] for c in range(6)
    ])

    # ══════════════════════════════════════════════════════════════
    # TEST 1: CURRENT SYSTEM BASELINE
    # ══════════════════════════════════════════════════════════════
    print("=" * 100)
    print("TEST 1: CURRENT SYSTEM (uniform ladder 0.75/0.60/0.30/0.20)")
    print("  This is the baseline everything else must beat.")
    print("=" * 100)
    print()

    n_curr, res_curr = score_all(scenarios, fv_current, mu_curr)
    d_curr = compute_d_prime(scenarios, current_scenario_f0, current_f0_centroids)
    min_conf_curr = compute_min_confidence(res_curr)

    print("  Action accuracy: %d/36" % n_curr)
    print("  Min confidence margin: %+.4f" % min_conf_curr)
    print()
    print("  %-22s %8s %8s %8s" % ("Category", "esc-sup", "pooled_SD", "d'"))
    print("  " + "-" * 52)
    for cat in CATS:
        d = d_curr[cat]
        print("  %-22s %8.3f %8.4f %8.2f" % (
            cat, d["separation"], d["pooled_sd"], d["d_prime"]))

    # ══════════════════════════════════════════════════════════════
    # TEST 1B: CURRENT SCENARIOS + PROPOSED CENTROIDS
    #   This is the actual migration path — change centroids but
    #   real alerts still arrive with travel-match f0 values.
    #   The prior migration attempt failed here.
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 1B: CURRENT SCENARIOS + PROPOSED CENTROIDS")
    print("  Real alerts have travel-match f0 values. If we change only")
    print("  centroids, does scoring still work? (Prior attempt failed here.)")
    print("=" * 100)
    print()

    n_cross, res_cross = score_all(scenarios, fv_current, mu_prop)
    d_cross = compute_d_prime(scenarios, current_scenario_f0, PROPOSED_F0_CENTROIDS)
    min_conf_cross = compute_min_confidence(res_cross)

    print("  Action accuracy: %d/36" % n_cross)
    print("  Min confidence margin: %+.4f" % min_conf_cross)
    if n_cross < 36:
        print("  FLIPPED scenarios:")
        for r in res_cross:
            if not r["correct"]:
                print("    %s: expected=%s, got=%s, conf=%+.4f" % (
                    r["sid"], ACTS[r["act_idx"]], ACTS[r["winner"]],
                    r["confidence"]))

    # ══════════════════════════════════════════════════════════════
    # TEST 2: PROPOSED VALUES
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 2: PROPOSED VALUES (from panel analysis)")
    print("=" * 100)
    print()

    n_prop, res_prop = score_all(scenarios, fv_proposed, mu_prop)
    d_prop = compute_d_prime(scenarios, PROPOSED_SCENARIO_F0, PROPOSED_F0_CENTROIDS)
    min_conf_prop = compute_min_confidence(res_prop)

    print("  Action accuracy: %d/36" % n_prop)
    print("  Min confidence margin: %+.4f" % min_conf_prop)
    print()
    print("  %-22s %8s %8s %8s" % ("Category", "esc-sup", "pooled_SD", "d'"))
    print("  " + "-" * 52)
    for cat in CATS:
        d = d_prop[cat]
        print("  %-22s %8.3f %8.4f %8.2f" % (
            cat, d["separation"], d["pooled_sd"], d["d_prime"]))

    # ══════════════════════════════════════════════════════════════
    # TEST 3: SIMPLE HEURISTIC (no panel needed)
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 3: SIMPLE HEURISTIC (esc=0.70, inv=0.45, sup=0.15, mon=0.25)")
    print("  If this performs comparably, the panel added no value.")
    print("=" * 100)
    print()

    heuristic_f0 = np.array([
        [0.70, 0.45, 0.15, 0.25],  # same for all categories
        [0.70, 0.45, 0.15, 0.25],
        [0.70, 0.45, 0.15, 0.25],
        [0.70, 0.45, 0.15, 0.25],
        [0.70, 0.45, 0.15, 0.25],
        [0.70, 0.45, 0.15, 0.25],
    ])
    mu_heur = build_tensor_with_f0(mu_curr, heuristic_f0)

    # Use proposed scenario values (the panel's contribution is the centroids)
    n_heur, res_heur = score_all(scenarios, fv_proposed, mu_heur)
    d_heur = compute_d_prime(scenarios, PROPOSED_SCENARIO_F0, heuristic_f0)
    min_conf_heur = compute_min_confidence(res_heur)

    print("  Action accuracy: %d/36" % n_heur)
    print("  Min confidence margin: %+.4f" % min_conf_heur)
    print()
    print("  %-22s %8s %8s %8s" % ("Category", "esc-sup", "pooled_SD", "d'"))
    print("  " + "-" * 52)
    for cat in CATS:
        d = d_heur[cat]
        print("  %-22s %8.3f %8.4f %8.2f" % (
            cat, d["separation"], d["pooled_sd"], d["d_prime"]))

    # ══════════════════════════════════════════════════════════════
    # TEST 4: RANDOM BASELINES (100 random centroid sets)
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 4: RANDOM BASELINES (100 random centroid sets, uniform [0, 1])")
    print("  How often do random centroids pass d' >= 0.5 in all 6 categories?")
    print("  How often do they get 36/36 action accuracy?")
    print("=" * 100)
    print()

    random_36_count = 0
    random_d_all_pass = 0
    random_accuracies = []
    random_min_confs = []
    random_d_pass_counts = []

    for trial in range(100):
        rand_f0 = rng.uniform(0, 1, size=(6, 4))
        # Sort within each category so escalate > investigate > suppress > monitor
        # (giving random values their best chance)
        for c in range(6):
            rand_f0[c] = np.sort(rand_f0[c])[::-1]

        mu_rand = build_tensor_with_f0(mu_curr, rand_f0)
        n_rand, res_rand = score_all(scenarios, fv_proposed, mu_rand)
        d_rand = compute_d_prime(scenarios, PROPOSED_SCENARIO_F0, rand_f0)
        min_conf_rand = compute_min_confidence(res_rand)

        random_accuracies.append(n_rand)
        random_min_confs.append(min_conf_rand)

        d_passes = sum(1 for cat in CATS if d_rand[cat]["d_prime"] >= 0.5)
        random_d_pass_counts.append(d_passes)

        if n_rand == 36:
            random_36_count += 1
        if d_passes == 6:
            random_d_all_pass += 1

    print("  Random 36/36 accuracy: %d/100 trials" % random_36_count)
    print("  Random d' all-pass (6/6): %d/100 trials" % random_d_all_pass)
    print("  Random accuracy: mean=%.1f, min=%d, max=%d" % (
        np.mean(random_accuracies), min(random_accuracies), max(random_accuracies)))
    print("  Random min confidence margin: mean=%+.4f, min=%+.4f" % (
        np.mean(random_min_confs), min(random_min_confs)))
    print("  Random d' pass count: mean=%.1f/6" % np.mean(random_d_pass_counts))

    # ══════════════════════════════════════════════════════════════
    # TEST 5: PERTURBATION ROBUSTNESS
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 5: PERTURBATION (100 trials, jitter within inter-model IQR)")
    print("  Tests whether results are sensitive to the specific panel values")
    print("  or robust within the range of model disagreement.")
    print("=" * 100)
    print()

    perturb_36_count = 0
    perturb_min_confs = []
    perturb_flips = []
    perturb_d_fail_cats = {cat: 0 for cat in CATS}

    for trial in range(100):
        # Jitter each scenario's f0 within its IQR
        fv_perturbed = {}
        perturbed_f0_values = {}
        for s in scenarios:
            sid = s["scenario_id"]
            base = PROPOSED_SCENARIO_F0[sid]
            iqr = SCENARIO_IQR.get(sid, 0.05)
            jitter = rng.uniform(-iqr / 2, iqr / 2)
            perturbed = np.clip(base + jitter, 0.0, 1.0)
            perturbed_f0_values[sid] = perturbed
            fv = build_factor_vector(s).copy()
            fv[0] = perturbed
            fv_perturbed[sid] = fv

        # Recompute centroids from perturbed scenarios
        cell_values = {}
        for s in scenarios:
            sid = s["scenario_id"]
            key = (s["category_index"], s["expected_action_index"])
            cell_values.setdefault(key, []).append(perturbed_f0_values[sid])

        perturbed_centroids = np.zeros((6, 4))
        for (c, a), vals in cell_values.items():
            perturbed_centroids[c, a] = np.mean(vals)

        mu_pert = build_tensor_with_f0(mu_curr, perturbed_centroids)
        n_pert, res_pert = score_all(scenarios, fv_perturbed, mu_pert)
        min_conf_pert = compute_min_confidence(res_pert)
        d_pert = compute_d_prime(scenarios, perturbed_f0_values, perturbed_centroids)

        perturb_min_confs.append(min_conf_pert)
        n_flips = 36 - n_pert
        perturb_flips.append(n_flips)
        if n_pert == 36:
            perturb_36_count += 1

        for cat in CATS:
            if d_pert[cat]["d_prime"] < 0.5:
                perturb_d_fail_cats[cat] += 1

    print("  Perturbation 36/36 accuracy: %d/100 trials" % perturb_36_count)
    print("  Perturbation flips: mean=%.2f, max=%d" % (
        np.mean(perturb_flips), max(perturb_flips)))
    print("  Min confidence margin: mean=%+.4f, min=%+.4f, max=%+.4f" % (
        np.mean(perturb_min_confs), min(perturb_min_confs), max(perturb_min_confs)))
    print()
    print("  d' < 0.5 failure rate per category:")
    for cat in CATS:
        rate = perturb_d_fail_cats[cat]
        print("    %-22s %d/100%s" % (cat, rate, " *** FRAGILE" if rate > 20 else ""))

    # Test 5B: Fixed centroids, jittered scenarios only
    print()
    print("  --- Test 5B: FIXED CENTROIDS, jittered scenarios ---")
    print("  (Removes circular centroid derivation — accuracy here is honest)")
    print()

    perturb5b_36 = 0
    perturb5b_flips = []
    perturb5b_min_confs = []

    for trial in range(100):
        fv_perturbed = {}
        for s in scenarios:
            sid = s["scenario_id"]
            base = PROPOSED_SCENARIO_F0[sid]
            iqr = SCENARIO_IQR.get(sid, 0.05)
            jitter = rng.uniform(-iqr / 2, iqr / 2)
            perturbed = np.clip(base + jitter, 0.0, 1.0)
            fv = build_factor_vector(s).copy()
            fv[0] = perturbed
            fv_perturbed[sid] = fv

        # Use FIXED proposed centroids (not recomputed)
        n_5b, res_5b = score_all(scenarios, fv_perturbed, mu_prop)
        min_conf_5b = compute_min_confidence(res_5b)

        perturb5b_min_confs.append(min_conf_5b)
        perturb5b_flips.append(36 - n_5b)
        if n_5b == 36:
            perturb5b_36 += 1

    print("  5B accuracy 36/36: %d/100 trials" % perturb5b_36)
    print("  5B flips: mean=%.2f, max=%d" % (
        np.mean(perturb5b_flips), max(perturb5b_flips)))
    print("  5B min confidence margin: mean=%+.4f, min=%+.4f" % (
        np.mean(perturb5b_min_confs), min(perturb5b_min_confs)))

    # ══════════════════════════════════════════════════════════════
    # TEST 6: ADVERSARIAL BOUNDARY
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("TEST 6: ADVERSARIAL BOUNDARY")
    print("  For each scenario, how far can the centroid f0 move before")
    print("  the expected action flips? Measures robustness, not fit.")
    print("=" * 100)
    print()

    print("%-12s %-22s %-8s %10s %10s" % (
        "Scenario", "Category", "Action", "Flip_dist", "Direction"))
    print("-" * 65)

    flip_distances = []
    for s in scenarios:
        sid = s["scenario_id"]
        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        cat_name = CATS[cat_idx]
        act_name = ACTS[act_idx]

        fv = fv_proposed[sid]

        # Binary search for the flip point
        # Try moving the correct action's centroid TOWARD the scenario f0
        # (making it easier) and AWAY (making it harder)
        base_centroid_f0 = PROPOSED_F0_CENTROIDS[cat_idx, act_idx]
        scenario_f0 = PROPOSED_SCENARIO_F0[sid]

        # Search in the "harder" direction (away from scenario)
        best_flip = None
        for delta in np.linspace(0, 1.5, 300):
            # Move correct action centroid away from scenario
            if scenario_f0 > base_centroid_f0:
                test_f0 = base_centroid_f0 - delta
            else:
                test_f0 = base_centroid_f0 + delta

            test_f0 = np.clip(test_f0, 0.0, 1.0)

            mu_test = mu_prop.copy()
            mu_test[cat_idx, act_idx, 0] = test_f0

            dists = [float(np.sum((fv - mu_test[cat_idx, a]) ** 2))
                     for a in range(4)]
            winner = int(np.argmin(dists))
            if winner != act_idx:
                best_flip = delta
                break

        if best_flip is not None:
            direction = "away"
            print("%-12s %-22s %-8s %10.4f %10s" % (
                sid, cat_name, act_name, best_flip, direction))
            flip_distances.append(best_flip)
        else:
            print("%-12s %-22s %-8s %10s %10s" % (
                sid, cat_name, act_name, ">1.50", "robust"))
            flip_distances.append(1.5)

    print()
    print("  Min flip distance: %.4f" % min(flip_distances))
    print("  Mean flip distance: %.4f" % np.mean(flip_distances))
    print("  Scenarios with flip < 0.1: %d" % sum(1 for d in flip_distances if d < 0.1))
    print("  Scenarios with flip < 0.05: %d" % sum(1 for d in flip_distances if d < 0.05))

    # ══════════════════════════════════════════════════════════════
    # SUMMARY COMPARISON
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("SUMMARY: HEAD-TO-HEAD COMPARISON")
    print("=" * 100)
    print()
    print("%-32s %8s %10s %8s %8s" % (
        "Configuration", "Acc/36", "MinConf", "d'>0.5", "Notes"))
    print("-" * 72)

    d_pass_curr = sum(1 for cat in CATS if d_curr[cat]["d_prime"] >= 0.5)
    d_pass_prop = sum(1 for cat in CATS if d_prop[cat]["d_prime"] >= 0.5)
    d_pass_heur = sum(1 for cat in CATS if d_heur[cat]["d_prime"] >= 0.5)
    d_pass_cross = sum(1 for cat in CATS if d_cross[cat]["d_prime"] >= 0.5)

    print("%-32s %8d %+10.4f %8s %8s" % (
        "1: Current (baseline)", n_curr, min_conf_curr,
        "%d/6" % d_pass_curr, "unfitted"))
    print("%-32s %8d %+10.4f %8s %8s" % (
        "1B: Curr scen + Prop centroids", n_cross, min_conf_cross,
        "%d/6" % d_pass_cross, "MIGRATION"))
    print("%-32s %8d %+10.4f %8s %8s" % (
        "2: Proposed (panel)", n_prop, min_conf_prop,
        "%d/6" % d_pass_prop, "fitted"))
    print("%-32s %8d %+10.4f %8s %8s" % (
        "3: Simple heuristic", n_heur, min_conf_heur,
        "%d/6" % d_pass_heur, "unfitted"))
    print("%-32s %8s %+10.4f %8s %8s" % (
        "4: Random (mean/100)", "%.1f" % np.mean(random_accuracies),
        np.mean(random_min_confs),
        "%.1f/6" % np.mean(random_d_pass_counts), ""))
    print("%-32s %8s %+10.4f %8s %8s" % (
        "5: Perturb refit (mean)", "%.1f" % (36 - np.mean(perturb_flips)),
        np.mean(perturb_min_confs), "—", "CIRC ACC"))
    print("%-32s %8s %+10.4f %8s %8s" % (
        "5B: Perturb fixed-cent (mean)", "%.1f" % (36 - np.mean(perturb5b_flips)),
        np.mean(perturb5b_min_confs), "—", "HONEST"))


if __name__ == "__main__":
    main()
