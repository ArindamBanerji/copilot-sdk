"""
Factor-0 Leave-One-Out Margin Contribution v3

Fixes the circularity in v2's margin measure: for n=1 cells the
scenario's own f0 IS the centroid, so margin contribution is positive
by construction. For n=2 cells the centroid is the mean of the
scenario and one sibling — still biased.

LOO fix: for each n=2 scenario, use the SIBLING's value as the
centroid (exclude the scenario being evaluated). Drop n=1 scenarios
entirely — they cannot contribute evidence.

Also includes:
- d' computation (between-action separation / within-cell SD)
- Centroid update source check (analyst-confirmed vs self-predicted)
- Kernel sigma indexing and refresh cadence check

Run from: gen-ai-roi-demo-v4-v50/backend/
"""

import json
import sys
import os
import numpy as np

# ── Proposed scenario factor-0 values (from panel Arm A aggregation) ──
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

# n=2 cell sibling pairs (scenario_id -> sibling_id)
SIBLINGS = {
    # escalate pairs
    "SOC-CA-01": "SOC-CA-02", "SOC-CA-02": "SOC-CA-01",
    "SOC-TI-01": "SOC-TI-02", "SOC-TI-02": "SOC-TI-01",
    "SOC-LM-01": "SOC-LM-02", "SOC-LM-02": "SOC-LM-01",
    "SOC-DE-01": "SOC-DE-02", "SOC-DE-02": "SOC-DE-01",
    "SOC-IT-01": "SOC-IT-02", "SOC-IT-02": "SOC-IT-01",
    "SOC-CI-01": "SOC-CI-02", "SOC-CI-02": "SOC-CI-01",
    # suppress pairs
    "SOC-CA-04": "SOC-CA-05", "SOC-CA-05": "SOC-CA-04",
    "SOC-TI-04": "SOC-TI-05", "SOC-TI-05": "SOC-TI-04",
    "SOC-LM-04": "SOC-LM-05", "SOC-LM-05": "SOC-LM-04",
    "SOC-DE-04": "SOC-DE-05", "SOC-DE-05": "SOC-DE-04",
    "SOC-IT-04": "SOC-IT-05", "SOC-IT-05": "SOC-IT-04",
    "SOC-CI-04": "SOC-CI-05", "SOC-CI-05": "SOC-CI-04",
}

# n=1 scenarios (investigate + monitor) — excluded from LOO
N1_SCENARIOS = {
    "SOC-CA-03", "SOC-CA-06", "SOC-TI-03", "SOC-TI-06",
    "SOC-LM-03", "SOC-LM-06", "SOC-DE-03", "SOC-DE-06",
    "SOC-IT-03", "SOC-IT-06", "SOC-CI-03", "SOC-CI-06",
}

CATS = [
    "credential_access", "malware_execution", "lateral_movement",
    "data_exfiltration", "insider_threat", "cloud_infrastructure",
]
ACTS = ["escalate", "investigate", "suppress", "monitor"]

# Proposed centroid f0 values (full, for non-LOO actions)
PROPOSED_F0_CENTROIDS = np.array([
    [0.649, 0.400, 0.140, 0.188],
    [0.263, 0.177, 0.142, 0.168],
    [0.812, 0.212, 0.150, 0.155],
    [0.358, 0.212, 0.337, 0.175],
    [0.413, 0.225, 0.141, 0.188],
    [0.825, 0.483, 0.367, 0.333],
])


def build_factor_vector(scenario):
    f = scenario["factors"]
    f0 = f.get("travel_match", f.get("privileged_identity_context", 0.5))
    return np.array([
        f0, f["asset_criticality"], f["threat_intel_enrichment"],
        f["pattern_history"], f["time_anomaly"], f["device_trust"],
    ])


def l2(vec, centroid):
    return float(np.sqrt(np.sum((vec - centroid) ** 2)))


def l2_no_f0(vec, centroid):
    v, c = vec.copy(), centroid.copy()
    v[0] = 0.0
    c[0] = 0.0
    return float(np.sqrt(np.sum((v - c) ** 2)))


def main():
    scenario_path = "app/data/soc_eval_scenarios.json"
    if not os.path.exists(scenario_path):
        print("ERROR: Run from gen-ai-roi-demo-v4-v50/backend/")
        sys.exit(1)

    sys.path.insert(0, os.getcwd())
    from app.domains.soc.config import SOC_PROFILE_CENTROIDS

    data = json.load(open(scenario_path))
    scenarios = data if isinstance(data, list) else data.get("scenarios", [])
    scenario_map = {s["scenario_id"]: s for s in scenarios}

    mu_curr = SOC_PROFILE_CENTROIDS

    # ══════════════════════════════════════════════════════════════
    # SECTION 1: LOO MARGIN CONTRIBUTION (n=2 scenarios only)
    # ══════════════════════════════════════════════════════════════
    print("=" * 100)
    print("SECTION 1: LEAVE-ONE-OUT MARGIN CONTRIBUTION (n=2 scenarios only)")
    print("  For each scenario, the LOO centroid uses the SIBLING's f0 value,")
    print("  not the cell mean. n=1 scenarios are excluded — they have no LOO estimate.")
    print("=" * 100)
    print()

    print("%-12s %-22s %-8s %10s %10s %10s %10s" % (
        "Scenario", "Category", "Action",
        "Marg_curr", "Marg_LOO", "F0c_curr", "F0c_LOO",
    ))
    print("-" * 82)

    cat_f0c_curr = {}
    cat_f0c_loo = {}
    all_results = []

    for s in scenarios:
        sid = s["scenario_id"]
        if sid in N1_SCENARIOS:
            continue

        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        cat_name = CATS[cat_idx]
        act_name = ACTS[act_idx]
        sibling_id = SIBLINGS[sid]

        # Build proposed factor vector for this scenario
        fv_prop = build_factor_vector(s).copy()
        fv_prop[0] = PROPOSED_SCENARIO_F0[sid]

        # Build current factor vector
        fv_curr = build_factor_vector(s)

        # Build LOO centroid: use sibling's f0 for this action's centroid
        mu_loo = SOC_PROFILE_CENTROIDS.copy()
        for c in range(6):
            for a in range(4):
                mu_loo[c, a, 0] = PROPOSED_F0_CENTROIDS[c, a]
        # Override the correct action's centroid with sibling's f0
        mu_loo[cat_idx, act_idx, 0] = PROPOSED_SCENARIO_F0[sibling_id]

        # Current margin contribution (unfitted baseline)
        dists_c = [l2(fv_curr, mu_curr[cat_idx, a]) for a in range(4)]
        dists_c_nof0 = [l2_no_f0(fv_curr, mu_curr[cat_idx, a]) for a in range(4)]
        sorted_c = np.argsort(dists_c)
        margin_c = dists_c[sorted_c[1]] - dists_c[sorted_c[0]]
        sorted_c_nof0 = np.argsort(dists_c_nof0)
        margin_c_nof0 = dists_c_nof0[sorted_c_nof0[1]] - dists_c_nof0[sorted_c_nof0[0]]
        f0c_curr = margin_c - margin_c_nof0

        # LOO margin contribution (proposed, sibling centroid)
        dists_l = [l2(fv_prop, mu_loo[cat_idx, a]) for a in range(4)]
        dists_l_nof0 = [l2_no_f0(fv_prop, mu_loo[cat_idx, a]) for a in range(4)]
        sorted_l = np.argsort(dists_l)
        margin_l = dists_l[sorted_l[1]] - dists_l[sorted_l[0]]
        sorted_l_nof0 = np.argsort(dists_l_nof0)
        margin_l_nof0 = dists_l_nof0[sorted_l_nof0[1]] - dists_l_nof0[sorted_l_nof0[0]]
        f0c_loo = margin_l - margin_l_nof0

        print("%-12s %-22s %-8s %10.4f %10.4f %10.4f %10.4f" % (
            sid, cat_name, act_name, margin_c, margin_l, f0c_curr, f0c_loo,
        ))

        cat_f0c_curr.setdefault(cat_name, []).append(f0c_curr)
        cat_f0c_loo.setdefault(cat_name, []).append(f0c_loo)
        all_results.append({
            "sid": sid, "cat": cat_name, "act": act_name,
            "f0c_curr": f0c_curr, "f0c_loo": f0c_loo,
        })

    print()
    print("%-22s %10s %10s %10s %8s" % (
        "Category", "AvgF0c_C", "AvgF0c_LOO", "Delta", "Status",
    ))
    print("-" * 62)
    pass_count = 0
    for cat in CATS:
        fc = np.mean(cat_f0c_curr[cat])
        fl = np.mean(cat_f0c_loo[cat])
        status = "PASS" if fl >= 0 else "NEGATIVE"
        if fl >= 0:
            pass_count += 1
        print("%-22s %10.4f %10.4f %+10.4f %8s" % (cat, fc, fl, fl - fc, status))

    print()
    print("Categories with non-negative LOO f0 contribution: %d/6" % pass_count)
    print("Gate (Opus): accept if >= 4/6 non-negative AND no category worsens vs current")
    print()

    # Check if any category worsened
    worsened = []
    for cat in CATS:
        fc = np.mean(cat_f0c_curr[cat])
        fl = np.mean(cat_f0c_loo[cat])
        if fl < fc - 0.001:
            worsened.append((cat, fc, fl))
    if worsened:
        print("Categories where LOO is WORSE than current:")
        for cat, fc, fl in worsened:
            print("  %s: curr=%.4f -> LOO=%.4f (delta=%+.4f)" % (cat, fc, fl, fl - fc))
    else:
        print("No category worsened vs current.")

    # ══════════════════════════════════════════════════════════════
    # SECTION 2: d' COMPUTATION (Opus's replacement for 20% gate)
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("SECTION 2: d' = (esc_centroid - sup_centroid) / pooled_within_cell_SD")
    print("  Opus prescribed d' >= 0.5 means factor-0 carries usable signal.")
    print("  Below 0.5: accept only with domain reason + non-negative LOO margin.")
    print("=" * 100)
    print()

    # Compute within-cell SD from n=2 pairs (escalate and suppress)
    print("%-22s %8s %8s %10s %10s %8s %8s" % (
        "Category", "esc_sep", "esc_SD", "sup_sep", "sup_SD", "d'", "Status",
    ))
    print("-" * 80)

    for c, cat in enumerate(CATS):
        # Escalate pair
        esc_ids = [sid for sid, s in scenario_map.items()
                   if s["category_index"] == c and s["expected_action_index"] == 0]
        esc_vals = [PROPOSED_SCENARIO_F0[sid] for sid in esc_ids]
        esc_centroid = PROPOSED_F0_CENTROIDS[c, 0]
        esc_sd = np.std(esc_vals, ddof=0) if len(esc_vals) > 1 else 0.0

        # Suppress pair
        sup_ids = [sid for sid, s in scenario_map.items()
                   if s["category_index"] == c and s["expected_action_index"] == 2]
        sup_vals = [PROPOSED_SCENARIO_F0[sid] for sid in sup_ids]
        sup_centroid = PROPOSED_F0_CENTROIDS[c, 2]
        sup_sd = np.std(sup_vals, ddof=0) if len(sup_vals) > 1 else 0.0

        # Pooled SD
        if esc_sd > 0 or sup_sd > 0:
            pooled_sd = np.sqrt((esc_sd ** 2 + sup_sd ** 2) / 2)
        else:
            pooled_sd = 0.0

        separation = esc_centroid - sup_centroid
        if pooled_sd < 0.001:
            d_prime = float("inf")
            status = "SD=0"
        else:
            d_prime = abs(separation) / pooled_sd
            status = "PASS" if d_prime >= 0.5 else "BELOW"

        # Flag if either pair has identical values (SD=0)
        sd_note = ""
        if esc_sd == 0:
            sd_note += " [esc pair identical]"
        if sup_sd == 0:
            sd_note += " [sup pair identical]"

        print("%-22s %8.3f %8.4f %10.3f %10.4f %8.2f %8s%s" % (
            cat, separation, esc_sd, sup_centroid, sup_sd, d_prime, status, sd_note,
        ))

    # ══════════════════════════════════════════════════════════════
    # SECTION 3: CENTROID UPDATE SOURCE CHECK
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("SECTION 3: CENTROID UPDATE SOURCE — analyst-confirmed or self-predicted?")
    print("  Opus: if self-predicted, the learning trap is real. If analyst-confirmed, it's open.")
    print("=" * 100)
    print()

    # Search for update calls in triage.py and learning.py
    for fname in [
        "app/services/triage.py",
        "app/services/learning.py",
        "app/domains/soc/scorer_adapter.py",
    ]:
        if not os.path.exists(fname):
            print("  %s: NOT FOUND" % fname)
            continue
        src = open(fname, encoding="utf-8").read()
        lines = src.splitlines()
        print("  === %s ===" % fname)
        for i, line in enumerate(lines, 1):
            low = line.lower()
            if any(kw in low for kw in [
                ".update(", "correct=", "gt_action",
                "confirmed", "analyst", "outcome", "learn(",
                "centroid", "η",
            ]) or (" eta " in low) or ("eta=" in low) or ("=eta" in low):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print("    %d: %s" % (i, stripped[:100]))
        print()

    # ══════════════════════════════════════════════════════════════
    # SECTION 4: KERNEL SIGMA INDEXING AND REFRESH
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("SECTION 4: DiagonalKernel sigma indexing — [factor] or [action, factor]?")
    print("  Opus W3b: if global per-factor, suppress variance leaks into escalate.")
    print("  Also: refresh cadence — should be >= ~40 decisions (3 centroid half-lives).")
    print("=" * 100)
    print()

    # Search GAE scorer and kernel code
    gae_files = []
    gae_root = "../../graph-attention-engine-v50"
    if os.path.exists(gae_root):
        for dirpath, dirnames, filenames in os.walk(os.path.join(gae_root, "gae")):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for f in filenames:
                if f.endswith(".py"):
                    gae_files.append(os.path.join(dirpath, f))

    if not gae_files:
        print("  GAE repo not found at %s — check path" % gae_root)
        print("  Run: grep -rn 'sigma\\|weights\\|diagonal' in GAE gae/ directory")
    else:
        for fpath in sorted(gae_files):
            src = open(fpath, encoding="utf-8").read()
            lines = src.splitlines()
            hits = []
            for i, line in enumerate(lines, 1):
                low = line.lower()
                if any(kw in low for kw in [
                    "class diagonal", "sigma", "weights",
                    "per_action", "per_factor", "refresh",
                    "update_weights", "recompute", "reliability",
                    "1/sigma", "inv_var", "precision",
                ]):
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        hits.append((i, stripped[:100]))
            if hits:
                print("  === %s ===" % os.path.basename(fpath))
                for lineno, text in hits:
                    print("    %d: %s" % (lineno, text))
                print()

    # Also check SOC config for sigma
    print("  === SOC sigma config ===")
    soc_config = open("app/domains/soc/config.py", encoding="utf-8").read()
    for i, line in enumerate(soc_config.splitlines(), 1):
        if "sigma" in line.lower() or "FACTOR_SIGMA" in line:
            print("    %d: %s" % (i, line.strip()[:100]))


if __name__ == "__main__":
    main()
