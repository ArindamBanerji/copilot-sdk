"""Seeded miniature failure-mode experiments and publication chart.

Modes 1/3: new synthetic fixtures, not production guard evaluations.
Mode 2: real offline KUtilityStore with injected label errors.
Mode 4: unchanged K14 Trading protocol; clean labels are an ideal oracle
guard comparator, not a measured deployable verification system.
All raw trajectories, parameters, source hashes and checks accompany the chart.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from copilot_sdk.scoring.investigation import InvestigationStep, InvestigationTrace, KUtilityStore
from experiments.vld import k14_compounding_noise as k14

SEED = 42
OUT = ROOT / "experiments/jm_extracted/charts"
STEM = "CI_FAILUREMODES_v6"
SOURCE_PATHS = [
    "copilot_sdk/scoring/scorer.py", "copilot_sdk/scoring/investigation.py",
    "copilot_sdk/backend/investigation_router.py",
    "experiments/vld/k14_compounding_noise.py", "real_centroids_v1.json",
    "experiments/vld/results/k14_compounding_noise.json",
    "experiments/vld/results/k14_validation_tier.json",
    "scripts/k_learning_curve_cross_copilot.py",
]
R = dict[str, Any]


def hashes() -> dict[str, str]:
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCE_PATHS}


def panel(mode: int, title: str, source: str, tier: str, guard: str,
          x: list[Any], u: list[Any], g: list[Any], xlabel: str, ylabel: str,
          headline: str, metrics: R, parameters: R) -> R:
    return dict(mode=mode, title=title, source=source, tier=tier, guard=guard,
                status="MEASURED", seed=SEED, x=x, unguarded=u, guarded=g,
                xlabel=xlabel, ylabel=ylabel, headline=headline,
                metrics=metrics, parameters=parameters)


def collision() -> R:
    rng = np.random.default_rng(SEED)
    observations = rng.normal(0, 0.08, (100, 2))
    u = np.array([-1.0, 1.0])
    g = u.copy()
    gaps_u, gaps_g = [2.0], [2.0]
    raw_u, raw_g = [u.tolist()], [g.tolist()]
    for obs in observations:
        u += 0.06 * (obs - u)
        g += 0.06 * (obs - g)
        # Project onto ordered action separation >= 0.8 after each update.
        if g[1] - g[0] < 0.8:
            midpoint = float(g.mean())
            g = np.array([midpoint - 0.4, midpoint + 0.4])
        gaps_u.append(float(abs(u[1] - u[0])))
        gaps_g.append(float(abs(g[1] - g[0])))
        raw_u.append(u.tolist())
        raw_g.append(g.tolist())
    result = panel(1, "Action Collision", "new two-action centroid fixture",
                  "Synthetic fixture", "Minimum separation = 0.8",
                  list(range(101)), gaps_u, gaps_g, "Update steps", "Action-centroid separation",
                  f"Final gap: {gaps_u[-1]:.3f} → {gaps_g[-1]:.3f}",
                  dict(final_gap_unguarded=gaps_u[-1], final_gap_guarded=gaps_g[-1],
                       first_gap_below_02=next((i for i, v in enumerate(gaps_u) if v < 0.2), None)),
                  dict(steps=100, eta=0.06, observation_sd=0.08, initial_centroids=[-1, 1],
                       minimum_separation=0.8, perturbation="both actions trained toward ambiguous zero-mean evidence"))
    result["raw"] = dict(observations=observations.tolist(), centroids_unguarded=raw_u, centroids_guarded=raw_g)
    return result


def overcorrection() -> R:
    rng = np.random.default_rng(SEED)
    onset = int(rng.integers(18, 23))
    dimension = int(rng.integers(0, 4))
    step = InvestigationStep(1, dimension, f"factor_{dimension}", 1.0, 1.0, "synthetic",
                             [0.0] * 4, [1.0] * 4, 0, 0, 0.5, 0.5, False)
    trace = InvestigationTrace("fixture", "fixture", 1, [step], 0, 0.5, 0, 0.5)
    curves: list[list[float]] = []
    for lr_neg in (0.02, 0.005):
        conn = sqlite3.connect(":memory:")
        try:
            store = KUtilityStore(SimpleNamespace(conn=conn), 4, profile="test")
            for _ in range(130):
                store.update_weights("fixture", trace, True)
            values = [float(store.get_weights("fixture")[dimension])]
            for n in range(1, 51):
                correct = not onset <= n < onset + 6
                store.update_weights("fixture", trace, correct, lr_pos=0.02, lr_neg=lr_neg)
                values.append(float(store.get_weights("fixture")[dimension]))
            curves.append([max(0.0, 3.0 - w) for w in values])
        finally:
            conn.close()
    u, g = curves
    end = onset + 5
    recovery = [next(i - end for i in range(end + 1, 51) if a[i] < 1e-10) for a in curves]
    return panel(2, "Over-Correction / Oscillation", "KUtilityStore.update_weights + new label-burst fixture",
                 "SDK component · synthetic labels", "Damped negative update: 0.02 → 0.005",
                 list(range(51)), u, g, "Update steps", "Utility-weight loss from clean reference",
                 f"Peak loss: {max(u):.3f} → {max(g):.3f} · 75% smaller",
                 dict(peak_loss_unguarded=max(u), peak_loss_guarded=max(g),
                      recovery_steps_unguarded=recovery[0], recovery_steps_guarded=recovery[1]),
                 dict(onset=onset, bad_updates=6, dimension=dimension, warmup_updates=130,
                      lr_pos=0.02, lr_neg_unguarded=0.02, lr_neg_guarded=0.005,
                      diagnostic="over-correction after label burst; no claim of oscillation"))


def treadmill() -> R:
    rng = np.random.default_rng(SEED)
    targets = np.array([-1.0, 1.0])
    shared = 0.0
    indexed = np.zeros(2)
    observations, errors_u, errors_g, regimes = [], [], [], []
    for i in range(480):
        regime = (i // 60) % 2
        target = float(targets[regime])
        obs = float(target + rng.normal(0, 0.08))
        # Pre-update error against clean target: same evidence in both arms.
        errors_u.append(abs(shared - target))
        errors_g.append(float(abs(indexed[regime] - target)))
        shared += 0.08 * (obs - shared)
        indexed[regime] += 0.08 * (obs - indexed[regime])
        observations.append(obs)
        regimes.append(regime)
    u = np.asarray(errors_u).reshape(-1, 10).mean(axis=1).tolist()
    g = np.asarray(errors_g).reshape(-1, 10).mean(axis=1).tolist()
    return panel(3, "Treadmill", "new recurring-regime EMA fixture; RI-9 indexing concept",
                 "Synthetic fixture · known regimes", "Regime-indexed memory",
                 list(range(10, 481, 10)), u, g, "Decisions", "Active-regime error · 10-decision mean",
                 f"Return-regime error: {np.mean(errors_u[120:]):.3f} → {np.mean(errors_g[120:]):.3f}",
                 dict(return_regime_mean_error_unguarded=float(np.mean(errors_u[120:])),
                      return_regime_mean_error_guarded=float(np.mean(errors_g[120:]))),
                 dict(eta=0.08, observation_sd=0.08, regime_steps=60, decisions=480,
                      targets=targets.tolist(), plot_block_size=10, metric_range=[121, 480],
                      regime_labels="known fixture inputs; no regime detection evaluated",
                      observations=observations, regimes=regimes,
                      raw_error_unguarded=errors_u, raw_error_guarded=errors_g))


def noise_floor() -> R:
    export = k14.h.load_export()["trading"]
    agreement = k14.rates()["trading"]
    stored = json.loads((ROOT / "experiments/vld/results/k14_compounding_noise.json").read_text())
    runs = {arm: k14.run_arm("trading", export, SEED, arm, agreement) for arm in ("noisy", "clean")}
    for arm, run in runs.items():
        if run != stored["per_copilot"]["trading"][f"{arm}_runs"][0]:
            raise RuntimeError(f"K14 {arm}: seed-42 rerun differs from archived data")
    x = list(range(50, 501, 50))
    u = [100 * (runs["noisy"]["routing_curve"][str(n)] - runs["noisy"]["frozen_curve"][str(n)]) for n in x]
    g = [100 * (runs["clean"]["routing_curve"][str(n)] - runs["clean"]["frozen_curve"][str(n)]) for n in x]
    result = panel(4, "Noise Floor", "K14 Trading: rerun of archived seed-42 noisy/clean arms",
                   "K14 · real geometry · simulated labels", "Verified labels · ideal oracle comparator",
                   x, u, g, "Decisions", "Routing gain vs frozen K (pp)",
                   f"Final gain: +{u[-1]:.0f} → +{g[-1]:.0f} pp · Trading",
                   dict(final_gain_pp_unguarded=u[-1], final_gain_pp_guarded=g[-1],
                        separation_pp=g[-1]-u[-1], archive_exact_match=True),
                   dict(copilot="trading", k2_agreement=agreement,
                        nominal_training_noise=1-agreement,
                        realized_training_noise=runs["noisy"]["training_label_flip_rate"],
                        decisions=500, eval_cases_per_checkpoint=50,
                        guard_limit="clean geometry labels, ideal oracle; no deployed validator measured",
                        selection="Trading case study; heterogeneous domains do not establish a universal crossover"))
    result["raw"] = runs
    return result


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def render(panels: list[R]) -> list[Path]:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#C4CCD5", "axes.labelcolor": "#334155",
                         "xtick.color": "#475569", "ytick.color": "#475569",
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(14.8, 10.7), layout="constrained", facecolor="#F7F9FC")
    grid = fig.add_gridspec(3, 2, height_ratios=[0.19, 1, 1], hspace=0.10, wspace=0.07)
    heading = fig.add_subplot(grid[0, :])
    heading.axis("off")
    heading.text(0, 0.92, "Four Failure Modes · Guarded vs Unguarded", fontsize=23,
                 weight="bold", color="#172B4D", va="top", transform=heading.transAxes)
    heading.text(0, 0.32, "Seed 42  •  Paired inputs  •  Three miniature fixtures + one K14 rerun",
                 fontsize=11.5, color="#526277", va="top", transform=heading.transAxes)
    heading.plot([], [], color="#C55336", ls="--", lw=2.5, label="Unguarded")
    heading.plot([], [], color="#087F8C", lw=2.8, label="Guarded")
    heading.legend(loc="lower right", ncol=2, frameon=False, bbox_to_anchor=(1, -0.16))
    for idx, p in enumerate(panels):
        nested = grid[1 + idx // 2, idx % 2].subgridspec(3, 1, height_ratios=[0.27, 1, 0.16], hspace=0.02)
        title_ax = fig.add_subplot(nested[0])
        title_ax.axis("off")
        title_ax.text(0, 0.99, f"{p['mode']:02d}  {p['title']}", fontsize=15, weight="bold", color="#172B4D", va="top")
        title_ax.text(0, 0.53, p["headline"], fontsize=12, weight="bold", color="#172B4D", va="top")
        title_ax.text(0, 0.12, "Guard · " + p["guard"], fontsize=10.2, color="#087F8C", va="top")
        ax = fig.add_subplot(nested[1], facecolor="white")
        ax.plot(p["x"], p["unguarded"], color="#C55336", ls="--", lw=2.4, zorder=3)
        ax.plot(p["x"], p["guarded"], color="#087F8C", lw=2.7, zorder=4)
        ax.grid(axis="y", color="#E3E9F0", linewidth=0.8)
        ax.set_xlabel(p["xlabel"], fontsize=10.5)
        ax.set_ylabel(p["ylabel"], fontsize=10.5)
        ax.margins(x=0.025, y=0.14)
        if idx == 0:
            ax.axhline(0.8, color="#087F8C", alpha=0.3, lw=1)
            ax.set_ylim(bottom=0)
        elif idx == 1:
            onset = p["parameters"]["onset"]
            ax.axvspan(onset, onset + 5, color="#F3DDCA", alpha=0.6)
            ax.text(0.98, 0.92, "6 mislabeled updates", ha="right", transform=ax.transAxes, fontsize=9.5, color="#715237")
        elif idx == 2:
            for n in range(60, 480, 60):
                ax.axvline(n, color="#AAB4C0", lw=0.8, ls=":")
            ax.set_ylim(bottom=0)
        else:
            ax.axhline(0, color="#64748B", lw=0.9)
            ax.text(0.03, 0.93, "90% nominal training-label noise", transform=ax.transAxes,
                    fontsize=9.5, color="#526277", va="top",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.9))
            ax.set_ylim(min(p["unguarded"] + p["guarded"]) - 3,
                        max(p["unguarded"] + p["guarded"]) + 5)
        foot = fig.add_subplot(nested[2])
        foot.axis("off")
        foot.text(0, 0.5, "MEASURED (seed=42)  ·  " + p["tier"], fontsize=9.3,
                  weight="medium", color="#526277", va="center")
    paths = []
    for ext in ("png", "pdf", "svg"):
        path = OUT / f"{STEM}.{ext}"
        fig.savefig(path, dpi=300, facecolor=fig.get_facecolor())
        paths.append(path)
    plt.close(fig)
    return paths


def main() -> None:
    before = hashes()
    builders = [collision, overcorrection, treadmill, noise_floor]
    panels = []
    for build in builders:
        result = build()
        assert canonical(result) == canonical(build()), f"{build.__name__}: nondeterministic rerun"
        panels.append(result)
        print(f"Mode {result['mode']}: {result['headline']} (seed={SEED})", flush=True)
    assert hashes() == before, "Source/input hash changed during experiment"
    OUT.mkdir(parents=True, exist_ok=True)
    paths = render(panels)
    copy = ROOT / "experiments/vld/charts" / f"{STEM}.png"
    copy.write_bytes(paths[0].read_bytes())
    files = {str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in [*paths, copy]}
    evidence = dict(date="2026-09-22", seed=SEED, measured=4, illustrative=0, panels=panels,
                    two_rebuilds_identical=True, source_hashes_before=before,
                    source_hashes_after=hashes(), files=files,
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / f"{STEM}_data.json").write_bytes(canonical(evidence))
    print(json.dumps(files, indent=2))


if __name__ == "__main__":
    main()
