"""
VLD Stage 1 Universal Evaluator v2
====================================
Works with BOTH Fable (dict branches) and Astra (list branches) formats.
Replaces per-copilot Codex evaluators for re-evaluation on new data.

Usage: python vld_universal_eval_v2.py [stage1_json] [output_dir]
"""

import json, sys, os
import numpy as np
from collections import defaultdict

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_fv(s):
    f = s["alert"]["surface_factors"]
    keys = sorted(f.keys())
    return np.array([f[k] for k in keys]), keys

def apply_hop(v, hop, keys):
    ef = hop.get("factor_enriched")
    nv = hop.get("factor_new_value")
    if ef and nv is not None and ef in keys:
        out = v.copy()
        out[keys.index(ef)] = nv
        return out
    return v.copy()

def normalize_branches(branches):
    """Convert branches to list of dicts regardless of input format."""
    if isinstance(branches, list):
        return branches
    if isinstance(branches, dict):
        return list(branches.values())
    return []

def build_enriched_centroids(scenarios, keys):
    av = defaultdict(list)
    for s in scenarios:
        if s.get("surface_only_resolvable"):
            continue
        a = s["decision_tree"]["ground_truth_action"]
        v, _ = get_fv(s)
        for h in s["decision_tree"].get("hops", []):
            v = apply_hop(v, h, keys)
        av[a].append(v)
    actions = sorted(av.keys())
    rng = np.random.default_rng(42)
    mu = np.zeros((len(actions), len(keys)))
    for i, a in enumerate(actions):
        vecs = av[a]
        mu[i] = np.mean(vecs, axis=0) if len(vecs) >= 2 else rng.uniform(0.2, 0.8, len(keys))
    return mu, actions

def score_best(v, mu, actions):
    d = [np.linalg.norm(v - mu[i]) for i in range(len(actions))]
    return actions[int(np.argmin(d))]

def run_4_arms(s, mu, actions, keys):
    gt = s["decision_tree"]["ground_truth_action"]
    hops = s["decision_tree"].get("hops", [])
    v, _ = get_fv(s)
    budget = s.get("budget", len(hops))
    avail = normalize_branches(s.get("available_branches", []))
    correct = normalize_branches(s.get("correct_branches", []))

    # ARM 1: single_pass
    sp = score_best(v, mu, actions)

    # ARM 2: breadth — read all available up to budget
    vb = v.copy()
    for br in avail[:budget]:
        if isinstance(br, dict):
            vb = apply_hop(vb, br, keys)
    br_act = score_best(vb, mu, actions)

    # ARM 3: content_rule — use correct branches
    vc = v.copy()
    for br in correct:
        if isinstance(br, dict):
            vc = apply_hop(vc, br, keys)
        elif isinstance(br, str):
            for h in hops:
                if h.get("branch_id") == br or h.get("evidence_source") == br:
                    vc = apply_hop(vc, h, keys)
    cr_act = score_best(vc, mu, actions)

    # ARM 4: VLD — sequential hops up to budget
    vv = v.copy()
    for h in hops[:budget]:
        vv = apply_hop(vv, h, keys)
    vld_act = score_best(vv, mu, actions)

    return {
        "scenario_id": s["scenario_id"],
        "branching_kind": s["branching_kind"],
        "rho_planted": s["rho_planted"],
        "gt": gt,
        "flat": s.get("surface_only_resolvable", False),
        "sp": sp, "sp_correct": sp == gt,
        "breadth": br_act, "breadth_correct": br_act == gt,
        "content_rule": cr_act, "cr_correct": cr_act == gt,
        "vld": vld_act, "vld_correct": vld_act == gt,
    }

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "stage1.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    d = load(path)
    S = d["scenarios"]
    if not S:
        print("FAIL: 0 scenarios")
        sys.exit(1)
    _, keys = get_fv(S[0])
    mu, actions = build_enriched_centroids(S, keys)
    n_actions = len(actions)
    chance = 1.0 / n_actions

    copilot = S[0].get("copilot", "unknown")
    print("Copilot: " + copilot)
    print("Scenarios: " + str(len(S)))
    print("Actions: " + str(actions) + " (chance = " + str(round(chance, 3)) + ")")
    print("Factors: " + str(keys))

    rows = [run_4_arms(s, mu, actions, keys) for s in S]

    # Save results
    out_path = os.path.join(out_dir, copilot + "_astra_eval_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print("\nResults: " + out_path + " (" + str(len(rows)) + " rows)")

    # Per-rho on score_keyed
    rho_groups = defaultdict(lambda: {"sp": [], "br": [], "cr": [], "vld": []})
    for r in rows:
        if r["branching_kind"] != "score_keyed":
            continue
        rho = r["rho_planted"]
        rho_groups[rho]["sp"].append(r["sp_correct"])
        rho_groups[rho]["br"].append(r["breadth_correct"])
        rho_groups[rho]["cr"].append(r["cr_correct"])
        rho_groups[rho]["vld"].append(r["vld_correct"])

    print("\nPer-rho (score_keyed):")
    print("  rho     SP      breadth  content  VLD     D(VLD-br)")
    print("  " + "-" * 52)
    for rho in sorted(rho_groups.keys()):
        g = rho_groups[rho]
        sp = np.mean(g["sp"])
        br = np.mean(g["br"])
        cr = np.mean(g["cr"])
        vl = np.mean(g["vld"])
        print("  " + str(round(rho, 2)).ljust(8) +
              str(round(sp, 3)).ljust(8) +
              str(round(br, 3)).ljust(9) +
              str(round(cr, 3)).ljust(9) +
              str(round(vl, 3)).ljust(8) +
              ("+" if vl - br >= 0 else "") + str(round(vl - br, 3)))

    # High-rho VLD
    high = [r for r in rows if r["branching_kind"] == "score_keyed" and r["rho_planted"] >= 0.70]
    if high:
        vld_high = np.mean([r["vld_correct"] for r in high])
        sp_high = np.mean([r["sp_correct"] for r in high])
        print("\nVLD at rho>=0.70: " + str(round(vld_high, 3)) +
              " (" + str(sum(r["vld_correct"] for r in high)) + "/" + str(len(high)) + ")")
        print("SP  at rho>=0.70: " + str(round(sp_high, 3)))

    # Controls
    flat = [r for r in rows if r["flat"]]
    if flat:
        fv = np.mean([r["vld_correct"] for r in flat])
        fs = np.mean([r["sp_correct"] for r in flat])
        print("\nFlat: VLD=" + str(round(fv, 3)) + " SP=" + str(round(fs, 3)) +
              " " + ("PASS" if fv <= fs + 0.01 else "FAIL"))

    rho50 = [r for r in rows if r["branching_kind"] == "score_keyed"
             and r["rho_planted"] == 0.50 and not r["flat"]]
    if rho50:
        v50 = np.mean([r["vld_correct"] for r in rho50])
        print("rho=0.50: VLD=" + str(round(v50, 3)) + " chance=" + str(round(chance, 3)) +
              " " + ("PASS" if abs(v50 - chance) <= 0.25 else "FAIL"))

    print("\nDone.")
