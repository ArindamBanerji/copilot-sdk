"""
Factor-0 Margin Contribution Analysis v2

The naive L2 share measurement (scenario vs own centroid) is circular
when centroids are derived from the same scenarios — n=1 cells get
0% by construction. This script measures what actually matters:

  1. MARGIN CONTRIBUTION: How much does factor-0 contribute to the
     classification margin between correct and second-best action?

  2. BETWEEN-ACTION DISCRIMINATION: How much of the distance to
     WRONG actions comes from factor-0? (Not circular — wrong-action
     centroids were not derived from this scenario.)

Run from: gen-ai-roi-demo-v4-v50/backend/
Usage: python ../../copilot-sdk/scripts/factor0_margin_contribution_v2.py
"""

import json
import sys
import os
import numpy as np

# ── Proposed centroids (factor-0 column only, from panel analysis) ──
PROPOSED_F0_CENTROIDS = np.array([
    [0.649, 0.400, 0.140, 0.188],  # credential_access
    [0.263, 0.177, 0.142, 0.168],  # malware_execution
    [0.812, 0.212, 0.150, 0.155],  # lateral_movement
    [0.358, 0.212, 0.337, 0.175],  # data_exfiltration
    [0.413, 0.225, 0.141, 0.188],  # insider_threat
    [0.825, 0.483, 0.367, 0.333],  # cloud_infrastructure
])

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

CATS = [
    "credential_access", "malware_execution", "lateral_movement",
    "data_exfiltration", "insider_threat", "cloud_infrastructure",
]
ACTS = ["escalate", "investigate", "suppress", "monitor"]


def build_proposed_tensor(current_centroids):
    """Current tensor with factor-0 column replaced by proposed values."""
    mu = current_centroids.copy()
    for c in range(6):
        for a in range(4):
            mu[c, a, 0] = PROPOSED_F0_CENTROIDS[c, a]
    return mu


def l2_distance(vec, centroid):
    return float(np.sqrt(np.sum((vec - centroid) ** 2)))


def l2_distance_without_factor(vec, centroid, factor_idx):
    """L2 excluding one factor (set both sides to 0 so contribution = 0)."""
    v = vec.copy()
    c = centroid.copy()
    v[factor_idx] = 0.0
    c[factor_idx] = 0.0
    return float(np.sqrt(np.sum((v - c) ** 2)))


def build_factor_vector(scenario):
    """Build 6-element factor vector from scenario dict."""
    f = scenario["factors"]
    f0 = f.get("travel_match", f.get("privileged_identity_context", 0.5))
    return np.array([
        f0,
        f["asset_criticality"],
        f["threat_intel_enrichment"],
        f["pattern_history"],
        f["time_anomaly"],
        f["device_trust"],
    ])


def main():
    scenario_path = "app/data/soc_eval_scenarios.json"
    if not os.path.exists(scenario_path):
        print("ERROR: Cannot find %s" % scenario_path)
        print("Run this script from gen-ai-roi-demo-v4-v50/backend/")
        sys.exit(1)

    # Import SOC config here (after directory check) so the error
    # message is clear if run from the wrong directory.
    sys.path.insert(0, os.getcwd())
    from app.domains.soc.config import SOC_PROFILE_CENTROIDS

    data = json.load(open(scenario_path))
    scenarios = data if isinstance(data, list) else data.get("scenarios", [])

    mu_curr = SOC_PROFILE_CENTROIDS
    mu_prop = build_proposed_tensor(SOC_PROFILE_CENTROIDS)

    # ══════════════════════════════════════════════════════════════
    # SECTION 1: MARGIN CONTRIBUTION
    # ══════════════════════════════════════════════════════════════
    print("=" * 110)
    print("SECTION 1: FACTOR-0 MARGIN CONTRIBUTION")
    print("=" * 110)
    print()
    print("Margin = L2(scenario, 2nd-best centroid) - L2(scenario, best centroid)")
    print("Margin_noF0 = same with factor-0 zeroed out")
    print("F0 contribution = Margin - Margin_noF0")
    print("  Positive = factor-0 HELPS classification (widens the gap)")
    print("  Negative = factor-0 HURTS classification (narrows the gap)")
    print("  ~Zero    = factor-0 is INERT for this scenario")
    print()

    header = "%-12s %-22s %-8s %8s %8s %8s %8s %8s %8s" % (
        "Scenario", "Category", "Action",
        "Marg_C", "Marg_P", "MnoF0_C", "MnoF0_P",
        "F0cont_C", "F0cont_P",
    )
    print(header)
    print("-" * len(header))

    cat_contributions_curr = {}
    cat_contributions_prop = {}
    cat_margins_curr = {}
    cat_margins_prop = {}
    results = []

    for s in scenarios:
        sid = s["scenario_id"]
        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        cat_name = CATS[cat_idx]
        act_name = ACTS[act_idx]

        fv_curr = build_factor_vector(s)
        fv_prop = fv_curr.copy()
        fv_prop[0] = PROPOSED_SCENARIO_F0[sid]

        for label, fv, mu in [("curr", fv_curr, mu_curr), ("prop", fv_prop, mu_prop)]:
            dists = [l2_distance(fv, mu[cat_idx, a]) for a in range(4)]
            dists_nof0 = [l2_distance_without_factor(fv, mu[cat_idx, a], 0) for a in range(4)]

            sorted_idx = np.argsort(dists)
            margin = dists[sorted_idx[1]] - dists[sorted_idx[0]]

            sorted_nof0 = np.argsort(dists_nof0)
            margin_nof0 = dists_nof0[sorted_nof0[1]] - dists_nof0[sorted_nof0[0]]

            f0_contribution = margin - margin_nof0

            if label == "curr":
                m_c, mnf_c, f0c_c = margin, margin_nof0, f0_contribution
            else:
                m_p, mnf_p, f0c_p = margin, margin_nof0, f0_contribution

        print("%-12s %-22s %-8s %8.4f %8.4f %8.4f %8.4f %8.4f %8.4f" % (
            sid, cat_name, act_name, m_c, m_p, mnf_c, mnf_p, f0c_c, f0c_p,
        ))

        cat_contributions_curr.setdefault(cat_name, []).append(f0c_c)
        cat_contributions_prop.setdefault(cat_name, []).append(f0c_p)
        cat_margins_curr.setdefault(cat_name, []).append(m_c)
        cat_margins_prop.setdefault(cat_name, []).append(m_p)
        results.append({
            "sid": sid, "cat": cat_name, "act": act_name,
            "margin_curr": m_c, "margin_prop": m_p,
            "f0_contrib_curr": f0c_c, "f0_contrib_prop": f0c_p,
        })

    print()
    print("%-22s %10s %10s %10s %10s %10s" % (
        "Category", "AvgMarg_C", "AvgMarg_P", "AvgF0c_C", "AvgF0c_P", "F0c_Delta",
    ))
    print("-" * 72)
    for cat in CATS:
        mc = np.mean(cat_margins_curr[cat])
        mp = np.mean(cat_margins_prop[cat])
        fc = np.mean(cat_contributions_curr[cat])
        fp = np.mean(cat_contributions_prop[cat])
        flag = ""
        if fp < 0:
            flag = " *** NEGATIVE"
        elif fp < 0.01:
            flag = " *** NEAR-ZERO"
        print("%-22s %10.4f %10.4f %10.4f %10.4f %+10.4f%s" % (
            cat, mc, mp, fc, fp, fp - fc, flag,
        ))

    # ══════════════════════════════════════════════════════════════
    # SECTION 2: SIGN FLIPS AND HURT SCENARIOS
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 90)
    print("SECTION 2A: SCENARIOS WHERE F0 CONTRIBUTION CHANGES SIGN (curr -> prop)")
    print("=" * 90)
    print()
    flip_count = 0
    for r in results:
        if (r["f0_contrib_curr"] > 0.005 and r["f0_contrib_prop"] < -0.005) or \
           (r["f0_contrib_curr"] < -0.005 and r["f0_contrib_prop"] > 0.005):
            print("  %s (%s/%s): curr=%+.4f -> prop=%+.4f" % (
                r["sid"], r["cat"], r["act"], r["f0_contrib_curr"], r["f0_contrib_prop"],
            ))
            flip_count += 1
    if flip_count == 0:
        print("  (none)")

    print()
    print("=" * 90)
    print("SECTION 2B: SCENARIOS WHERE PROPOSED F0 HURTS CLASSIFICATION (contribution < -0.005)")
    print("=" * 90)
    print()
    hurt_count = 0
    for r in results:
        if r["f0_contrib_prop"] < -0.005:
            print("  %s (%s/%s): margin=%.4f, margin_noF0=%.4f, f0_contrib=%+.4f" % (
                r["sid"], r["cat"], r["act"],
                r["margin_prop"], r["margin_prop"] - r["f0_contrib_prop"],
                r["f0_contrib_prop"],
            ))
            hurt_count += 1
    if hurt_count == 0:
        print("  (none)")

    # ══════════════════════════════════════════════════════════════
    # SECTION 3: BETWEEN-ACTION CENTROID SEPARATION ON F0
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 90)
    print("SECTION 3: BETWEEN-ACTION CENTROID SEPARATION ON FACTOR-0 (proposed)")
    print("  = Opus W5 table")
    print("=" * 90)
    print()
    print("%-22s %8s %8s %8s %8s  %10s %10s" % (
        "Category", "esc", "inv", "sup", "mon", "esc-sup", "sup-mon",
    ))
    print("-" * 82)
    for c, cat in enumerate(CATS):
        vals = [PROPOSED_F0_CENTROIDS[c, a] for a in range(4)]
        esc_sup = vals[0] - vals[2]
        sup_mon = vals[2] - vals[3]
        flag = ""
        if abs(esc_sup) < 0.05:
            flag = " *** COLLAPSED"
        if sup_mon < -0.01:
            flag += " [sup<mon]"
        print("%-22s %8.3f %8.3f %8.3f %8.3f  %+10.3f %+10.3f%s" % (
            cat, vals[0], vals[1], vals[2], vals[3], esc_sup, sup_mon, flag,
        ))

    print()
    print("%-22s %10s %10s %10s" % ("Category", "esc-sup_C", "esc-sup_P", "Delta"))
    print("-" * 55)
    for c, cat in enumerate(CATS):
        curr_sep = float(mu_curr[c, 0, 0] - mu_curr[c, 2, 0])
        prop_sep = float(PROPOSED_F0_CENTROIDS[c, 0] - PROPOSED_F0_CENTROIDS[c, 2])
        print("%-22s %10.3f %10.3f %+10.3f" % (cat, curr_sep, prop_sep, prop_sep - curr_sep))

    # ══════════════════════════════════════════════════════════════
    # SECTION 4: F0 SHARE OF BETWEEN-ACTION DISCRIMINATION
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("SECTION 4: FACTOR-0 SHARE OF BETWEEN-ACTION DISCRIMINATION (proposed)")
    print("  = f0's share of distance from scenario to WRONG action centroids")
    print("  NOT circular: wrong-action centroids were not derived from this scenario.")
    print("=" * 100)
    print()
    print("%-12s %-22s %-8s %10s %10s %10s" % (
        "Scenario", "Category", "Action", "TotalD2_wr", "F0_D2_wr", "F0_pct_wr",
    ))
    print("-" * 74)

    cat_between_shares = {}

    for s in scenarios:
        sid = s["scenario_id"]
        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        cat_name = CATS[cat_idx]
        act_name = ACTS[act_idx]

        fv = build_factor_vector(s).copy()
        fv[0] = PROPOSED_SCENARIO_F0[sid]

        total_wrong_d2 = 0.0
        f0_wrong_d2 = 0.0
        for a in range(4):
            if a == act_idx:
                continue
            diff = fv - mu_prop[cat_idx, a]
            total_wrong_d2 += float(np.sum(diff ** 2))
            f0_wrong_d2 += float(diff[0] ** 2)

        pct = (f0_wrong_d2 / total_wrong_d2 * 100) if total_wrong_d2 > 0 else 0
        print("%-12s %-22s %-8s %10.4f %10.4f %9.1f%%" % (
            sid, cat_name, act_name, total_wrong_d2, f0_wrong_d2, pct,
        ))
        cat_between_shares.setdefault(cat_name, []).append(pct)

    print()
    print("%-22s %10s %8s" % ("Category", "AvgF0_pct", "Status"))
    print("-" * 42)
    for cat in CATS:
        mean_pct = np.mean(cat_between_shares[cat])
        flag = " *** BELOW 20%" if mean_pct < 20 else ""
        print("%-22s %9.1f%%%s" % (cat, mean_pct, flag))

    # ══════════════════════════════════════════════════════════════
    # SECTION 5: CONFIDENCE MARGIN ANALYSIS
    # ══════════════════════════════════════════════════════════════
    print()
    print("=" * 90)
    print("SECTION 5: CONFIDENCE MARGIN ANALYSIS (per-row, against 0.62 threshold)")
    print("  Uses softmax: p(a) = exp(-d^2/tau) / sum(exp(-d^2/tau)), tau=0.1")
    print("=" * 90)
    print()

    tau = 0.1
    min_margin = float("inf")
    min_scenario = ""
    worst_rows = []

    for s in scenarios:
        sid = s["scenario_id"]
        cat_idx = s["category_index"]
        act_idx = s["expected_action_index"]
        cat_name = CATS[cat_idx]

        fv = build_factor_vector(s).copy()
        fv[0] = PROPOSED_SCENARIO_F0[sid]

        dists = []
        for a in range(4):
            d = float(np.sum((fv - mu_prop[cat_idx, a]) ** 2))
            dists.append(d)

        neg_d = [-d / tau for d in dists]
        max_nd = max(neg_d)
        exp_vals = [np.exp(nd - max_nd) for nd in neg_d]
        total_exp = sum(exp_vals)
        probs = [e / total_exp for e in exp_vals]

        conf = probs[act_idx]
        margin = conf - 0.62

        worst_rows.append((margin, conf, sid, cat_name))
        if margin < min_margin:
            min_margin = margin
            min_scenario = sid

    worst_rows.sort()

    print("Worst-case margin: %s at %+.6f (confidence %.6f vs 0.62)" % (
        min_scenario, min_margin, min_margin + 0.62,
    ))
    print()
    print("Bottom 5 rows by margin:")
    for margin, conf, sid, cat in worst_rows[:5]:
        print("  %s (%s): confidence=%.4f, margin=%+.4f" % (sid, cat, conf, margin))
    print()
    if min_margin > 0:
        print("ALL scenarios above 0.62 threshold.")
    else:
        print("*** SOME scenarios BELOW 0.62 threshold.")


if __name__ == "__main__":
    main()
