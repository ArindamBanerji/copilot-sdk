"""
VLD Recurrence + Enrichment-Driven Graph Reasoning Experiments v2
==================================================================
Fixed: centroids built from ENRICHED vectors (not surface).
Added: dual-centroid option, 5 new recurrence experiments.

SECTION A — VLD Recurrence
  RNN-1: Depth-accuracy-confidence curve
  RNN-2: Per-hop ablation (leave-one-out + only-hop)
  RNN-3: Convergence (residual + entropy)
  RNN-4: Order dependence (sequential vs truly parallel)
  RNN-5: Routing quality per step (is each routing decision better than random?)
  RNN-6: State divergence (similar v_0, different evidence → different trajectories?)
  RNN-7: Long-range dependency (does hop 1 still matter at hop 3?)
  RNN-8: Intermediate state quality (can v_t predict ground truth at each depth?)
  RNN-9: Gating behavior (does update magnitude decrease for less-relevant hops?)

SECTION B — Graph Reasoning
  GR-1 through GR-5 (unchanged from v1)

Usage: python vld_graph_reasoning_experiments_v2.py [stage1_json] [output_dir]
"""

import json, sys, os
import numpy as np
from collections import defaultdict, Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.size': 11, 'axes.facecolor': '#FAFAFA',
    'figure.facecolor': '#FFFFFF', 'axes.grid': True,
    'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False,
})

C = {'vld': '#2563EB', 'breadth': '#F59E0B', 'random': '#DC2626',
     'single': '#6B7280', 'correct': '#059669', 'compound': '#7C3AED',
     'selective': '#059669', 'exhaustive': '#DC2626', 'depth_dim': '#9333EA',
     'routing': '#0891B2', 'surface': '#D97706'}


# ── Utilities ──

def load_stage1(path):
    with open(path) as f:
        return json.load(f)['scenarios']

def get_fv(s):
    f = s['alert']['surface_factors']
    keys = sorted(f.keys())
    return np.array([f[k] for k in keys]), keys

def apply_hop(v, hop, keys):
    ef = hop.get('factor_enriched')
    nv = hop.get('factor_new_value')
    if ef and nv is not None and ef in keys:
        out = v.copy(); out[keys.index(ef)] = nv; return out
    return v.copy()

def apply_all_hops(v, hops, keys):
    vt = v.copy()
    for h in hops:
        vt = apply_hop(vt, h, keys)
    return vt

def apply_parallel(v, hops, keys):
    enr = defaultdict(list)
    for h in hops:
        ef = h.get('factor_enriched'); nv = h.get('factor_new_value')
        if ef and nv is not None and ef in keys:
            enr[ef].append(nv)
    out = v.copy()
    for f, vals in enr.items():
        out[keys.index(f)] = np.mean(vals)
    return out

def multihop(scenarios, min_h=1):
    return [s for s in scenarios
            if not s.get('surface_only_resolvable')
            and len(s['decision_tree'].get('hops', [])) >= min_h]


# ── Centroid Building ──

def build_centroids(scenarios, keys, mode='enriched'):
    """
    mode='surface':  centroids from surface_factors (v1 — WRONG)
    mode='enriched': centroids from fully-enriched vectors (v2 — CORRECT)
    mode='dual':     returns BOTH (surface for routing, enriched for scoring)
    """
    av_surface = defaultdict(list)
    av_enriched = defaultdict(list)

    for s in scenarios:
        if s.get('surface_only_resolvable'):
            continue
        action = s['decision_tree']['ground_truth_action']
        v, _ = get_fv(s)
        av_surface[action].append(v)
        hops = s['decision_tree'].get('hops', [])
        v_enr = apply_all_hops(v, hops, keys)
        av_enriched[action].append(v_enr)

    actions = sorted(av_enriched.keys())
    ai = {a: i for i, a in enumerate(actions)}
    n_factors = len(keys)
    rng = np.random.default_rng(42)

    def _build(av):
        mu = np.zeros((len(actions), n_factors))
        for a in actions:
            vecs = av[a]
            if len(vecs) >= 2:
                mu[ai[a]] = np.mean(vecs, axis=0)
            else:
                mu[ai[a]] = rng.uniform(0.2, 0.8, n_factors)
        return mu

    if mode == 'surface':
        return _build(av_surface), actions, ai
    elif mode == 'enriched':
        return _build(av_enriched), actions, ai
    elif mode == 'dual':
        return _build(av_surface), _build(av_enriched), actions, ai
    else:
        raise ValueError(f"Unknown mode: {mode}")


def score_best(v, mu, actions):
    d = [np.linalg.norm(v - mu[i]) for i in range(len(actions))]
    b = int(np.argmin(d))
    return actions[b], d[b], d

def entropy(dists):
    d = np.array(dists)
    logits = -d / (np.mean(d) + 1e-8)
    e = np.exp(logits - np.max(logits))
    p = e / (np.sum(e) + 1e-8)
    return -np.sum(p * np.log(p + 1e-10))

def action_probs(dists):
    """Softmax probabilities from distances (closer = higher prob)."""
    d = np.array(dists)
    logits = -d / (np.mean(d) + 1e-8)
    e = np.exp(logits - np.max(logits))
    return e / (np.sum(e) + 1e-8)


# ═══════════════════════════════════════════════════════════════
# SECTION A: VLD Recurrence
# ═══════════════════════════════════════════════════════════════

def rnn1(scenarios, mu, actions, keys):
    """Depth-accuracy-confidence with enriched centroids."""
    print("=" * 65)
    print("RNN-1: Depth-accuracy-confidence (enriched centroids)")
    mh = multihop(scenarios)
    dd = defaultdict(lambda: {'correct': [], 'dist': [], 'entropy': []})
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hops = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)
        a0, d0, ds0 = score_best(v, mu, actions)
        dd[0]['correct'].append(int(a0 == gt))
        dd[0]['dist'].append(d0)
        dd[0]['entropy'].append(entropy(ds0))
        vt = v.copy()
        for depth, h in enumerate(hops, 1):
            vt = apply_hop(vt, h, keys)
            at, dt, dst = score_best(vt, mu, actions)
            dd[depth]['correct'].append(int(at == gt))
            dd[depth]['dist'].append(dt)
            dd[depth]['entropy'].append(entropy(dst))
    print(f"  n={len(mh)}")
    print(f"  {'Depth':<7} {'Acc':<8} {'Dist':<9} {'Entropy':<9} {'N':<5}")
    for d in sorted(dd.keys()):
        print(f"  {d:<7} {np.mean(dd[d]['correct']):<8.3f} "
              f"{np.mean(dd[d]['dist']):<9.4f} {np.mean(dd[d]['entropy']):<9.4f} "
              f"{len(dd[d]['correct']):<5}")
    return dd


def rnn1_compare(scenarios, mu_surface, mu_enriched, actions, keys):
    """Compare surface vs enriched centroids side by side."""
    print("\n" + "=" * 65)
    print("RNN-1b: Surface vs enriched centroid comparison")
    mh = multihop(scenarios)
    results = {'surface': defaultdict(list), 'enriched': defaultdict(list)}
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hops = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)
        vt = v.copy()
        # Surface centroid scoring
        results['surface'][0].append(int(score_best(v, mu_surface, actions)[0] == gt))
        # Enriched centroid scoring
        results['enriched'][0].append(int(score_best(v, mu_enriched, actions)[0] == gt))
        vt_s = v.copy()
        vt_e = v.copy()
        for depth, h in enumerate(hops, 1):
            vt_s = apply_hop(vt_s, h, keys)
            vt_e = apply_hop(vt_e, h, keys)
            results['surface'][depth].append(int(score_best(vt_s, mu_surface, actions)[0] == gt))
            results['enriched'][depth].append(int(score_best(vt_e, mu_enriched, actions)[0] == gt))
    print(f"  {'Depth':<7} {'Surface':<10} {'Enriched':<10} {'Δ':<8}")
    for d in sorted(set(list(results['surface'].keys()) + list(results['enriched'].keys()))):
        s_acc = np.mean(results['surface'][d]) if results['surface'][d] else 0
        e_acc = np.mean(results['enriched'][d]) if results['enriched'][d] else 0
        print(f"  {d:<7} {s_acc:<10.3f} {e_acc:<10.3f} {e_acc-s_acc:<+8.3f}")
    return results


def rnn2(scenarios, mu, actions, keys):
    """Per-hop ablation."""
    print("\n" + "=" * 65)
    print("RNN-2: Per-hop ablation")
    deep = multihop(scenarios, 2)
    if not deep:
        print("  No 2+ hop — skip"); return None
    res = {}
    fc = sum(1 for s in deep
             if score_best(apply_all_hops(get_fv(s)[0].copy(),
                s['decision_tree']['hops'], keys), mu, actions)[0]
             == s['decision_tree']['ground_truth_action'])
    res['all_hops'] = fc / len(deep)
    maxd = max(len(s['decision_tree']['hops']) for s in deep)
    for skip in range(maxd):
        c = 0; n = 0
        for s in deep:
            hs = s['decision_tree']['hops']
            if skip >= len(hs): continue
            n += 1; gt = s['decision_tree']['ground_truth_action']
            v, _ = get_fv(s); vt = v.copy()
            for i, h in enumerate(hs):
                if i != skip: vt = apply_hop(vt, h, keys)
            if score_best(vt, mu, actions)[0] == gt: c += 1
        if n: res[f'skip_hop_{skip+1}'] = c / n
    for only in range(maxd):
        c = 0; n = 0
        for s in deep:
            hs = s['decision_tree']['hops']
            if only >= len(hs): continue
            n += 1; gt = s['decision_tree']['ground_truth_action']
            v, _ = get_fv(s)
            vt = apply_hop(v.copy(), hs[only], keys)
            if score_best(vt, mu, actions)[0] == gt: c += 1
        if n: res[f'only_hop_{only+1}'] = c / n
    print(f"  All hops: {res['all_hops']:.3f}")
    for k in sorted(res):
        if k != 'all_hops':
            print(f"  {k}: {res[k]:.3f} (Δ={res[k]-res['all_hops']:+.3f})")
    return res


def rnn3(scenarios, mu, actions, keys):
    """Convergence."""
    print("\n" + "=" * 65)
    print("RNN-3: Convergence")
    mh = multihop(scenarios)
    residuals = defaultdict(list); entropies = defaultdict(list)
    mono_d = 0; mono_e = 0
    for s in mh:
        hs = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)
        _, d0, ds0 = score_best(v, mu, actions)
        residuals[0].append(d0); entropies[0].append(entropy(ds0))
        dseq = [d0]; eseq = [entropy(ds0)]; vt = v.copy()
        for depth, h in enumerate(hs, 1):
            vt = apply_hop(vt, h, keys)
            _, dt, dst = score_best(vt, mu, actions)
            residuals[depth].append(dt); entropies[depth].append(entropy(dst))
            dseq.append(dt); eseq.append(entropy(dst))
        if all(dseq[i] >= dseq[i+1] - 0.01 for i in range(len(dseq)-1)): mono_d += 1
        if all(eseq[i] >= eseq[i+1] - 0.01 for i in range(len(eseq)-1)): mono_e += 1
    n = len(mh)
    print(f"  n={n}")
    for d in sorted(residuals):
        print(f"  Depth {d}: dist={np.mean(residuals[d]):.4f}  ent={np.mean(entropies[d]):.4f}")
    print(f"  Monotonic dist: {mono_d}/{n} ({mono_d/n:.0%})  ent: {mono_e}/{n} ({mono_e/n:.0%})")
    return residuals, entropies


def rnn4(scenarios, mu, actions, keys):
    """Order dependence."""
    print("\n" + "=" * 65)
    print("RNN-4: Order dependence")
    mh = multihop(scenarios, 2)
    if not mh: print("  No 2+ hop — skip"); return None
    rng = np.random.default_rng(42)
    res = {'sequential': 0, 'parallel': 0, 'reverse': 0, 'random': 0}
    overlap = 0; n = len(mh)
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hs = s['decision_tree']['hops']; v, _ = get_fv(s)
        ef = [h.get('factor_enriched') for h in hs if h.get('factor_enriched')]
        if len(ef) != len(set(ef)): overlap += 1
        vt = v.copy()
        for h in hs: vt = apply_hop(vt, h, keys)
        if score_best(vt, mu, actions)[0] == gt: res['sequential'] += 1
        vp = apply_parallel(v.copy(), hs, keys)
        if score_best(vp, mu, actions)[0] == gt: res['parallel'] += 1
        vr = v.copy()
        for h in reversed(hs): vr = apply_hop(vr, h, keys)
        if score_best(vr, mu, actions)[0] == gt: res['reverse'] += 1
        votes = []
        for _ in range(5):
            sh = list(hs); rng.shuffle(sh); vx = v.copy()
            for h in sh: vx = apply_hop(vx, h, keys)
            votes.append(score_best(vx, mu, actions)[0])
        if Counter(votes).most_common(1)[0][0] == gt: res['random'] += 1
    for k in ['sequential','parallel','reverse','random']: res[k] /= n
    print(f"  n={n}, overlap={overlap}")
    for k in ['sequential', 'parallel', 'reverse', 'random']:
        print(f"  {k}: {res[k]:.3f}")
    res['overlap_count'] = overlap; res['n'] = n
    return res


def rnn5(scenarios, mu, actions, keys):
    """RNN-5: Routing quality per step.
    At each hop, is the routing decision (which factor to investigate)
    better than random? Measure: does the chosen factor have the
    LARGEST error relative to the correct centroid?"""
    print("\n" + "=" * 65)
    print("RNN-5: Routing quality per step")
    mh = multihop(scenarios)
    step_quality = defaultdict(lambda: {'optimal': 0, 'top2': 0, 'total': 0})

    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        gi = actions.index(gt) if gt in actions else -1
        if gi < 0: continue
        hops = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)
        vt = v.copy()

        for depth, h in enumerate(hops):
            # What factor did this hop enrich?
            chosen = h.get('factor_enriched')
            if not chosen or chosen not in keys: continue

            # What SHOULD have been chosen? (largest error to correct centroid)
            target = mu[gi]
            errors = np.abs(vt - target)
            ranked = np.argsort(-errors)  # highest error first
            chosen_idx = keys.index(chosen)

            step_quality[depth]['total'] += 1
            if chosen_idx == ranked[0]:
                step_quality[depth]['optimal'] += 1
            if chosen_idx in ranked[:2]:
                step_quality[depth]['top2'] += 1

            vt = apply_hop(vt, h, keys)

    print(f"  {'Step':<7} {'Optimal':<10} {'Top-2':<10} {'N':<6}")
    for d in sorted(step_quality.keys()):
        sq = step_quality[d]
        opt = sq['optimal'] / sq['total'] if sq['total'] else 0
        t2 = sq['top2'] / sq['total'] if sq['total'] else 0
        chance = 1.0 / len(keys)
        print(f"  {d:<7} {opt:<10.3f} {t2:<10.3f} {sq['total']:<6}  (chance={chance:.3f})")

    return step_quality


def rnn6(scenarios, mu, actions, keys):
    """RNN-6: State divergence.
    Find pairs of scenarios with similar v_0 but different ground truth.
    After applying evidence, do their trajectories diverge?
    This is the key recurrence property: same initial state +
    different inputs = different final states."""
    print("\n" + "=" * 65)
    print("RNN-6: State divergence (similar start, different trajectories)")
    mh = multihop(scenarios)
    if len(mh) < 4: print("  Too few scenarios — skip"); return None

    # Find pairs with similar v_0
    pairs_found = 0
    diverged = 0
    converged = 0

    for i in range(len(mh)):
        for j in range(i+1, len(mh)):
            vi, _ = get_fv(mh[i])
            vj, _ = get_fv(mh[j])
            d0 = np.linalg.norm(vi - vj)
            if d0 > 0.3: continue  # too different at start

            gt_i = mh[i]['decision_tree']['ground_truth_action']
            gt_j = mh[j]['decision_tree']['ground_truth_action']
            if gt_i == gt_j: continue  # same target — not interesting

            pairs_found += 1
            # Apply all hops
            vi_final = apply_all_hops(vi, mh[i]['decision_tree']['hops'], keys)
            vj_final = apply_all_hops(vj, mh[j]['decision_tree']['hops'], keys)
            d_final = np.linalg.norm(vi_final - vj_final)

            if d_final > d0:
                diverged += 1
            else:
                converged += 1

    print(f"  Similar-start pairs with different GT: {pairs_found}")
    if pairs_found > 0:
        print(f"  Diverged (d_final > d_start): {diverged}/{pairs_found} ({diverged/pairs_found:.0%})")
        print(f"  Converged: {converged}/{pairs_found}")
        print(f"  → {'DIVERGES' if diverged > converged else 'DOES NOT DIVERGE'}: "
              f"evidence creates distinct trajectories {'✓' if diverged > converged else '✗'}")
    else:
        print("  No similar-start pairs found — scenarios are too spread in factor space")

    return {'pairs': pairs_found, 'diverged': diverged, 'converged': converged}


def rnn7(scenarios, mu, actions, keys):
    """RNN-7: Long-range dependency.
    For 3-hop scenarios: does hop 1 evidence still influence the final
    action? Compare: (a) all 3 hops, (b) hops 2+3 only, (c) hop 1+3 only.
    If (a) > (b), hop 1 has long-range influence through the hidden state."""
    print("\n" + "=" * 65)
    print("RNN-7: Long-range dependency (3-hop)")
    deep = multihop(scenarios, 3)
    if not deep: print("  No 3-hop — skip"); return None
    if len(deep) < 10:
        print(f"  WARNING: only {len(deep)} 3-hop scenarios — results will be noisy")

    configs = {
        'all_3':    lambda hs: [0, 1, 2],
        'hop_2_3':  lambda hs: [1, 2],
        'hop_1_3':  lambda hs: [0, 2],
        'hop_1_2':  lambda hs: [0, 1],
        'hop_3_only': lambda hs: [2],
        'hop_1_only': lambda hs: [0],
    }
    results = {}
    for name, selector in configs.items():
        correct = 0
        for s in deep:
            gt = s['decision_tree']['ground_truth_action']
            hs = s['decision_tree']['hops']
            v, _ = get_fv(s); vt = v.copy()
            for idx in selector(hs):
                if idx < len(hs):
                    vt = apply_hop(vt, hs[idx], keys)
            if score_best(vt, mu, actions)[0] == gt:
                correct += 1
        results[name] = correct / len(deep)

    print(f"  n={len(deep)}")
    for k in ['all_3', 'hop_2_3', 'hop_1_3', 'hop_1_2', 'hop_3_only', 'hop_1_only']:
        delta = results[k] - results['all_3']
        print(f"  {k:<14} {results[k]:.3f} (Δ={delta:+.3f} vs all)")
    if results['all_3'] > results['hop_2_3']:
        print(f"  → LONG-RANGE: hop 1 adds {results['all_3']-results['hop_2_3']:+.3f} on top of hops 2+3")
    else:
        print(f"  → NO long-range: hop 1 doesn't help when hops 2+3 present")

    return results


def rnn8(scenarios, mu, actions, keys):
    """RNN-8: Intermediate state quality.
    At each depth, what is the probability assigned to the correct action?
    Even if the argmax is wrong, the probability should increase with depth."""
    print("\n" + "=" * 65)
    print("RNN-8: Intermediate state quality (P(correct) per depth)")
    mh = multihop(scenarios)
    depth_probs = defaultdict(list)

    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        gi = actions.index(gt) if gt in actions else -1
        if gi < 0: continue
        hops = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)

        _, _, dists_0 = score_best(v, mu, actions)
        probs_0 = action_probs(dists_0)
        depth_probs[0].append(probs_0[gi])

        vt = v.copy()
        for depth, h in enumerate(hops, 1):
            vt = apply_hop(vt, h, keys)
            _, _, dists_t = score_best(vt, mu, actions)
            probs_t = action_probs(dists_t)
            depth_probs[depth].append(probs_t[gi])

    print(f"  {'Depth':<7} {'Mean P(correct)':<18} {'Median':<10} {'N':<5}")
    for d in sorted(depth_probs.keys()):
        vals = depth_probs[d]
        print(f"  {d:<7} {np.mean(vals):<18.4f} {np.median(vals):<10.4f} {len(vals):<5}")
    # Check monotonic increase
    means = [np.mean(depth_probs[d]) for d in sorted(depth_probs.keys())]
    if all(means[i] <= means[i+1] + 0.01 for i in range(len(means)-1)):
        print("  → P(correct) monotonically increases with depth ✓")
    else:
        print("  → P(correct) non-monotonic — intermediate states noisy")

    return depth_probs


def rnn9(scenarios, mu, actions, keys):
    """RNN-9: Gating behavior.
    Does the magnitude of each hop's update decrease for later hops?
    (Like LSTM — early hops make large updates, later hops make smaller refinements.)
    Measure: ||v_{t} - v_{t-1}|| per step."""
    print("\n" + "=" * 65)
    print("RNN-9: Gating behavior (update magnitude per step)")
    mh = multihop(scenarios)
    step_magnitudes = defaultdict(list)

    for s in mh:
        hops = s['decision_tree'].get('hops', [])
        v, _ = get_fv(s)
        vt = v.copy()
        for depth, h in enumerate(hops):
            vt_prev = vt.copy()
            vt = apply_hop(vt, h, keys)
            mag = np.linalg.norm(vt - vt_prev)
            step_magnitudes[depth].append(mag)

    print(f"  {'Step':<7} {'Mean |Δv|':<12} {'Std':<10} {'N':<5}")
    for d in sorted(step_magnitudes.keys()):
        vals = step_magnitudes[d]
        print(f"  {d:<7} {np.mean(vals):<12.4f} {np.std(vals):<10.4f} {len(vals):<5}")

    means = [np.mean(step_magnitudes[d]) for d in sorted(step_magnitudes.keys())]
    if len(means) >= 2 and means[-1] < means[0]:
        print("  → Updates decrease — early hops make big changes, later hops refine")
    elif len(means) >= 2:
        print("  → Updates don't decrease — each hop changes by similar magnitude")
    print("  NOTE: with selective replacement, |Δv| = |Δ one factor|. Measures evidence strength, not learned gating.")

    return step_magnitudes


# ═══════════════════════════════════════════════════════════════
# SECTION B: Graph Reasoning (unchanged from v1)
# ═══════════════════════════════════════════════════════════════

def gr1(scenarios, mu, actions, keys):
    print("\n" + "=" * 65)
    print("GR-1: Evidence compounding")
    deep = multihop(scenarios, 2)
    if not deep: print("  No 2+ hop — skip"); return None
    improved = 0; n = 0
    for s in deep:
        gt = s['decision_tree']['ground_truth_action']
        gi = actions.index(gt) if gt in actions else -1
        if gi < 0: continue
        n += 1; v, _ = get_fv(s)
        d_before = np.linalg.norm(v - mu[gi])
        v1 = apply_hop(v.copy(), s['decision_tree']['hops'][0], keys)
        d_after = np.linalg.norm(v1 - mu[gi])
        if d_after < d_before: improved += 1
    rate = improved / n if n else 0
    print(f"  n={n}, compounding rate: {rate:.0%} ({improved}/{n})")
    return {'compounding_rate': rate, 'n': n}

def gr2(scenarios, mu, actions, keys):
    print("\n" + "=" * 65)
    print("GR-2: Selective vs exhaustive")
    mh = multihop(scenarios)
    sc = 0; ec = 0; sr = 0; er = 0
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hs = s['decision_tree']['hops']; v, _ = get_fv(s)
        na = len(s.get('available_branches', hs))
        vs = apply_all_hops(v.copy(), hs, keys)
        if score_best(vs, mu, actions)[0] == gt: sc += 1
        sr += len(hs)
        ve = apply_parallel(v.copy(), hs, keys)
        if score_best(ve, mu, actions)[0] == gt: ec += 1
        er += na
    n = len(mh)
    sa = sc/n; ea = ec/n
    print(f"  Selective: {sa:.3f} ({sr/n:.1f} reads)  Exhaustive: {ea:.3f} ({er/n:.1f} reads)")
    return {'sel_acc': sa, 'exh_acc': ea, 'n': n}

def gr3(scenarios, mu, actions, keys):
    print("\n" + "=" * 65)
    print("GR-3: Diminishing returns")
    mh = multihop(scenarios)
    da = defaultdict(list)
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hs = s['decision_tree'].get('hops', []); v, _ = get_fv(s)
        da[0].append(int(score_best(v, mu, actions)[0] == gt))
        vt = v.copy()
        for d, h in enumerate(hs, 1):
            vt = apply_hop(vt, h, keys)
            da[d].append(int(score_best(vt, mu, actions)[0] == gt))
    prev = 0
    print(f"  {'Depth':<7} {'Acc':<10} {'Marginal':<10} {'N':<5}")
    for d in sorted(da):
        a = np.mean(da[d]); g = a - prev
        print(f"  {d:<7} {a:<10.3f} {g:<+10.3f} {len(da[d]):<5}")
        prev = a
    return da

def gr4(scenarios, mu, actions, keys):
    print("\n" + "=" * 65)
    print("GR-4: Graph density")
    mh = multihop(scenarios)
    dg = defaultdict(lambda: {'sp': 0, 'vld': 0, 'n': 0})
    for s in mh:
        gt = s['decision_tree']['ground_truth_action']
        hs = s['decision_tree']['hops']; v, _ = get_fv(s)
        nb = len(s.get('available_branches', [])) or len(hs)
        bk = 'low (1-2)' if nb <= 2 else ('med (3-4)' if nb <= 4 else 'high (5+)')
        dg[bk]['n'] += 1
        if score_best(v, mu, actions)[0] == gt: dg[bk]['sp'] += 1
        vt = apply_all_hops(v.copy(), hs, keys)
        if score_best(vt, mu, actions)[0] == gt: dg[bk]['vld'] += 1
    for b in ['low (1-2)', 'med (3-4)', 'high (5+)']:
        g = dg[b]
        if g['n']: print(f"  {b}: SP={g['sp']/g['n']:.3f} VLD={g['vld']/g['n']:.3f} Δ={g['vld']/g['n']-g['sp']/g['n']:+.3f} n={g['n']}")
    return dg

def gr5(scenarios, mu, actions, keys):
    print("\n" + "=" * 65)
    print("GR-5: Evidence redundancy")
    mh = multihop(scenarios, 2)
    if not mh: print("  No 2+ hop — skip"); return None
    ov = []; no = []
    for s in mh:
        ef = [h.get('factor_enriched') for h in s['decision_tree']['hops'] if h.get('factor_enriched')]
        (ov if len(ef) != len(set(ef)) else no).append(s)
    for label, grp in [('Overlap', ov), ('No overlap', no)]:
        if not grp: continue
        c = sum(1 for s in grp if score_best(apply_all_hops(get_fv(s)[0].copy(),
            s['decision_tree']['hops'], keys), mu, actions)[0] == s['decision_tree']['ground_truth_action'])
        print(f"  {label}: acc={c/len(grp):.3f} ({c}/{len(grp)})")
    return {'overlap': len(ov), 'no_overlap': len(no)}


# ═══════════════════════════════════════════════════════════════
# Charts
# ═══════════════════════════════════════════════════════════════

def gen_charts(dd, compare, abl, res, ent, order, compound,
               routing, diverge, longrange, intermediate, gating, out):

    # PUB-17: depth-accuracy-confidence (3 panels)
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(16, 5))
    ds = sorted(dd.keys())
    ac = [np.mean(dd[d]['correct']) for d in ds]
    di = [np.mean(dd[d]['dist']) for d in ds]
    en = [np.mean(dd[d]['entropy']) for d in ds]
    a1.plot(ds, ac, '-o', color=C['vld'], lw=2.5, ms=8); a1.set_ylabel('Accuracy'); a1.set_title('Accuracy'); a1.set_ylim(0,1.1)
    for d, a in zip(ds, ac): a1.text(d, a+0.03, f'{a:.3f}', ha='center', fontsize=9, fontweight='bold')
    a2.plot(ds, di, '-s', color=C['compound'], lw=2.5, ms=8); a2.set_ylabel('Distance'); a2.set_title('Centroid distance')
    a3.plot(ds, en, '-^', color=C['depth_dim'], lw=2.5, ms=8); a3.set_ylabel('Entropy'); a3.set_title('Entropy')
    for ax in [a1,a2,a3]: ax.set_xlabel('Depth'); ax.set_xticks(ds)
    fig.suptitle('Depth-accuracy-confidence (enriched centroids)', y=1.02)
    plt.tight_layout(); plt.savefig(os.path.join(out, 'pub17_depth_accuracy_confidence.png'), dpi=200, bbox_inches='tight'); plt.close()
    print("  PUB-17")

    # PUB-17b: surface vs enriched comparison
    if compare:
        fig, ax = plt.subplots(figsize=(8, 5))
        ds_s = sorted(compare['surface'].keys())
        ds_e = sorted(compare['enriched'].keys())
        ds_all = sorted(set(ds_s + ds_e))
        s_acc = [np.mean(compare['surface'][d]) if compare['surface'][d] else 0 for d in ds_all]
        e_acc = [np.mean(compare['enriched'][d]) if compare['enriched'][d] else 0 for d in ds_all]
        ax.plot(ds_all, s_acc, '-s', color=C['surface'], lw=2.5, ms=7, label='Surface centroids (v1)')
        ax.plot(ds_all, e_acc, '-o', color=C['vld'], lw=2.5, ms=7, label='Enriched centroids (v2)')
        ax.set_xlabel('Depth'); ax.set_ylabel('Accuracy')
        ax.set_title('Centroid initialization matters: enriched > surface')
        ax.legend(); ax.set_ylim(0, 1.1); ax.set_xticks(ds_all)
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub17b_centroid_comparison.png'), dpi=200); plt.close()
        print("  PUB-17b")

    # PUB-18: ablation
    if abl:
        fig, ax = plt.subplots(figsize=(10, 5))
        ks = sorted(abl.keys()); vs = [abl[k] for k in ks]
        cols = [C['vld'] if k=='all_hops' else C['random'] if 'skip' in k else C['selective'] for k in ks]
        ax.bar([k.replace('_',' ').title() for k in ks], vs, color=cols, edgecolor='white', width=0.6)
        ax.axhline(y=abl['all_hops'], color=C['vld'], ls='--', alpha=0.4)
        ax.set_ylabel('Accuracy'); ax.set_title('Hop ablation'); ax.set_ylim(0,1.1)
        plt.xticks(rotation=30, ha='right'); plt.tight_layout()
        plt.savefig(os.path.join(out, 'pub18_hop_ablation.png'), dpi=200); plt.close()
        print("  PUB-18")

    # PUB-19: convergence
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    dr = sorted(res.keys()); mr = [np.mean(res[d]) for d in dr]; sr = [np.std(res[d]) for d in dr]
    a1.plot(dr, mr, '-o', color=C['vld'], lw=2.5, ms=8)
    a1.fill_between(dr, [m-s for m,s in zip(mr,sr)], [m+s for m,s in zip(mr,sr)], alpha=0.15, color='blue')
    a1.set_xlabel('Depth'); a1.set_ylabel('Distance'); a1.set_title('Residual')
    de = sorted(ent.keys()); me = [np.mean(ent[d]) for d in de]; se = [np.std(ent[d]) for d in de]
    a2.plot(de, me, '-s', color=C['compound'], lw=2.5, ms=8)
    a2.fill_between(de, [m-s for m,s in zip(me,se)], [m+s for m,s in zip(me,se)], alpha=0.15, color='purple')
    a2.set_xlabel('Depth'); a2.set_ylabel('Entropy'); a2.set_title('Entropy')
    plt.tight_layout(); plt.savefig(os.path.join(out, 'pub19_convergence.png'), dpi=200); plt.close()
    print("  PUB-19")

    # PUB-20: order
    if order:
        fig, ax = plt.subplots(figsize=(8, 5))
        ls = ['Sequential\n(VLD)', 'TRUE parallel\n(avg)', 'Reverse', 'Random\n(5-vote)']
        vs = [order[k] for k in ['sequential','parallel','reverse','random']]
        ax.bar(ls, vs, color=[C['vld'],C['breadth'],C['random'],C['single']], edgecolor='white', width=0.6)
        ax.set_ylabel('Accuracy'); ax.set_title(f'Order (n={order["n"]}, {order["overlap_count"]} overlap)'); ax.set_ylim(0,1.1)
        for b, v in zip(ax.patches, vs): ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{v:.3f}', ha='center', fontsize=10, fontweight='bold')
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub20_order_dependence.png'), dpi=200); plt.close()
        print("  PUB-20")

    # PUB-21: compounding
    if compound:
        r = compound['compounding_rate']
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.bar(['Compounds\n(closer)', 'Dilutes\n(farther)'], [r, 1-r], color=[C['compound'],C['single']], edgecolor='white', width=0.5)
        ax.set_ylabel('Fraction'); ax.set_title(f'Evidence compounding: {r:.0%}'); ax.set_ylim(0,1.1)
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub21_evidence_compounding.png'), dpi=200); plt.close()
        print("  PUB-21")

    # PUB-22: intermediate state quality
    if intermediate:
        fig, ax = plt.subplots(figsize=(8, 5))
        ds = sorted(intermediate.keys())
        means = [np.mean(intermediate[d]) for d in ds]
        ax.plot(ds, means, '-o', color=C['routing'], lw=2.5, ms=8)
        ax.set_xlabel('Depth'); ax.set_ylabel('P(correct action)')
        ax.set_title('Intermediate state quality: P(correct) per depth')
        ax.set_ylim(0, 1.0); ax.set_xticks(ds)
        for d, m in zip(ds, means): ax.text(d, m+0.02, f'{m:.3f}', ha='center', fontsize=9, fontweight='bold')
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub22_intermediate_state.png'), dpi=200); plt.close()
        print("  PUB-22")

    # PUB-23: gating behavior
    if gating:
        fig, ax = plt.subplots(figsize=(8, 5))
        steps = sorted(gating.keys())
        means = [np.mean(gating[s]) for s in steps]
        stds = [np.std(gating[s]) for s in steps]
        ax.bar(steps, means, yerr=stds, color=C['compound'], edgecolor='white', width=0.5, capsize=4)
        ax.set_xlabel('Hop index'); ax.set_ylabel('|Δv| (update magnitude)')
        ax.set_title('Update magnitude per hop (selective replacement = single factor Δ)')
        ax.set_xticks(steps)
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub23_gating.png'), dpi=200); plt.close()
        print("  PUB-23")

    # PUB-24: routing quality per step (RNN-5)
    if routing:
        fig, ax = plt.subplots(figsize=(8, 5))
        steps = sorted(routing.keys())
        opt_rates = [routing[s]['optimal']/routing[s]['total'] if routing[s]['total'] else 0 for s in steps]
        top2_rates = [routing[s]['top2']/routing[s]['total'] if routing[s]['total'] else 0 for s in steps]
        chance = 1.0 / len(keys) if keys else 0.167
        x = np.arange(len(steps))
        ax.bar(x - 0.15, opt_rates, 0.3, color=C['vld'], label='Optimal (rank 1)', edgecolor='white')
        ax.bar(x + 0.15, top2_rates, 0.3, color=C['routing'], label='Top-2', edgecolor='white')
        ax.axhline(y=chance, color='gray', ls='--', alpha=0.5, label=f'Chance ({chance:.2f})')
        ax.set_xlabel('Hop index'); ax.set_ylabel('Fraction choosing best factor')
        ax.set_title('Routing quality: does each hop pick the most uncertain factor?')
        ax.set_xticks(x); ax.set_xticklabels([f'Hop {s}' for s in steps])
        ax.legend(); ax.set_ylim(0, 1.1)
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub24_routing_quality.png'), dpi=200); plt.close()
        print("  PUB-24")

    # PUB-25: long-range dependency (RNN-7)
    if longrange:
        fig, ax = plt.subplots(figsize=(10, 5))
        configs = ['all_3', 'hop_2_3', 'hop_1_3', 'hop_1_2', 'hop_3_only', 'hop_1_only']
        labels = ['All 3\nhops', 'Hops\n2+3', 'Hops\n1+3', 'Hops\n1+2', 'Hop 3\nonly', 'Hop 1\nonly']
        vals = [longrange.get(k, 0) for k in configs]
        colors_l = [C['vld']] + [C['single']]*5
        bars = ax.bar(labels, vals, color=colors_l, edgecolor='white', width=0.6)
        ax.axhline(y=longrange.get('all_3', 0), color=C['vld'], ls='--', alpha=0.4)
        ax.set_ylabel('Accuracy'); ax.set_title('Long-range dependency: which hops matter? (3-hop scenarios)')
        ax.set_ylim(0, 1.1)
        for b, v in zip(bars, vals): ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')
        plt.tight_layout(); plt.savefig(os.path.join(out, 'pub25_long_range.png'), dpi=200); plt.close()
        print("  PUB-25")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/soc_multihop_stage1.json'
    out = sys.argv[2] if len(sys.argv) > 2 else './pub_charts'
    os.makedirs(out, exist_ok=True)

    print(f"Loading: {path}")
    S = load_stage1(path)
    _, keys = get_fv(S[0])

    # Build BOTH centroid sets
    mu_surface, mu_enriched, actions, ai = build_centroids(S, keys, mode='dual')
    # Use enriched as primary (the v2 fix)
    mu = mu_enriched

    print(f"Scenarios: {len(S)}, Actions: {actions}, Factors: {keys}")
    print(f"Centroid diff (surface vs enriched): {np.linalg.norm(mu_surface - mu_enriched):.4f}\n")

    # Section A: VLD Recurrence
    dd = rnn1(S, mu, actions, keys)
    compare = rnn1_compare(S, mu_surface, mu_enriched, actions, keys)
    abl = rnn2(S, mu, actions, keys)
    res, ent = rnn3(S, mu, actions, keys)
    order = rnn4(S, mu, actions, keys)
    routing = rnn5(S, mu, actions, keys)
    diverge = rnn6(S, mu, actions, keys)
    longrange = rnn7(S, mu, actions, keys)
    intermediate = rnn8(S, mu, actions, keys)
    gating = rnn9(S, mu, actions, keys)

    # Section B: Graph Reasoning
    comp = gr1(S, mu, actions, keys)
    gr2(S, mu, actions, keys)
    gr3(S, mu, actions, keys)
    gr4(S, mu, actions, keys)
    gr5(S, mu, actions, keys)

    # Charts
    print(f"\nCharts → {out}/")
    gen_charts(dd, compare, abl, res, ent, order, comp,
               routing, diverge, longrange, intermediate, gating, out)
    print("Done. PUB-17 through PUB-25 (9 charts).")
