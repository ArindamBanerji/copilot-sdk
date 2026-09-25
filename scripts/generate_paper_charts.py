"""Render the eight RGI paper figures from existing evidence; no experiment runs.

Run with the project's Python environment from any working directory.
Dependencies: matplotlib, seaborn, numpy, Pillow.

Provenance exceptions to the prompt's input list:
* The K summary has endpoints only; per-copilot JSONs supply measured curves.
  No N=0 observation is present, so curves begin at N=50 without extrapolation.
* final_d_min is named d_min inside post_investigation_diagnostic/signals.
* The frontier CSV contains accuracy/reads, not saves/hurts. Figure 7 parses
  the separate constructed-scenario table in ci_rgi_impact_core_v6.md, section
  4.1; it does not infer counts from the frontier's different cohort.
* R5 has a mixed verdict: rejected decay and supported regime indexing.

PNG dimensions are exact (no tight cropping); SVG text stays editable.
Only this script's sixteen named chart outputs are written.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle
from matplotlib.ticker import PercentFormatter
import numpy as np
from PIL import Image
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "experiments/vld"
OUT = DATA / "paper_charts"
PAPER = ROOT / "docs/design/ci_rgi_impact_core_v6.md"
ORDER = ("soc", "trading", "purchasing", "dataops", "s2p")
NAMES = dict(zip(ORDER, ("SOC", "Trading", "Purchasing", "DataOps", "S2P")))
COLORS = dict(zip(ORDER, ("#2563EB", "#DC2626", "#059669", "#7C3AED", "#D97706")))
BG, INK, GRAY, PALE = "#FAFAFA", "#172033", "#64748B", "#CBD5E1"
SOURCES = (
    "copilot_sdk/scoring/investigation.py",
    "copilot_sdk/backend/investigation_router.py",
    "copilot_sdk/scoring/scorer.py",
)
INPUT_HASHES: dict[Path, str] = {}
GENERATED: list[Path] = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path):
    raw = path.read_bytes()
    INPUT_HASHES[path] = hashlib.sha256(raw).hexdigest()
    return raw.decode("utf-8-sig")


def read_json(name):
    path = DATA / name
    print(f"Input: {name} ({path.stat().st_size:,} bytes)", flush=True)
    return json.loads(read_text(path))


def style():
    sns.set_theme(style="whitegrid", font="DejaVu Sans", rc={
        "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG, "font.size": 11,
        "axes.labelsize": 11, "axes.titlesize": 14,
        "figure.titlesize": 14, "xtick.labelsize": 11,
        "ytick.labelsize": 11, "legend.fontsize": 11,
        "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": GRAY, "ytick.color": GRAY,
        "axes.edgecolor": PALE, "grid.color": "#E5E7EB",
        "grid.linewidth": 0.65, "axes.spines.top": False,
        "axes.spines.right": False, "svg.fonttype": "none",
        "svg.hashsalt": "rgi-paper-charts-v1", "lines.linewidth": 2.4,
    })


def heading(fig, title, subtitle):
    fig.text(.09, .95, title, fontsize=14, weight="bold", va="top")
    fig.text(.09, .899, subtitle, fontsize=11, color=GRAY, va="top")


def footnote(fig, text):
    fig.text(.09, .035, text, fontsize=11, color=GRAY, va="bottom")


def save(fig, stem, provenance):
    fig.canvas.draw()
    # Catch cropped text without changing the required physical dimensions.
    renderer = fig.canvas.get_renderer()
    frame = fig.bbox
    for artist in fig.findobj(matplotlib.text.Text):
        if artist.get_visible() and artist.get_text():
            box = artist.get_window_extent(renderer)
            if box.x0 < -1 or box.y0 < -1 or box.x1 > frame.x1 + 1 or box.y1 > frame.y1 + 1:
                raise ValueError(f"Text outside {stem}: {artist.get_text()!r}")
    for ext in ("png", "svg"):
        path = OUT / f"{stem}.{ext}"
        metadata = {"Title": stem, "Description": provenance}
        if ext == "svg":
            metadata["Date"] = None
        fig.savefig(path, dpi=300, metadata=metadata)
        GENERATED.append(path)
    plt.close(fig)
    print(f"Rendered: {stem} [PNG + SVG]", flush=True)


def load_k(summary):
    curves = {}
    endpoints = {c["name"]: c for c in summary["copilots"]}
    for name in ORDER:
        filename = "k_learning_curve_results.json" if name == "dataops" else f"k_learning_curve_{name}.json"
        d = read_json(filename)
        rows = sorted((r for r in d["checkpoints"] if r["decision_count"] <= 500), key=lambda r: r["decision_count"])
        x = np.array([r["decision_count"] for r in rows])
        learn = np.array([r["learning_arm"]["routing_quality"] for r in rows])
        frozen = np.array([r["control_arm"]["routing_quality"] for r in rows])
        assert list(x) == list(range(50, 501, 50)), name
        assert np.isclose(learn[-1], endpoints[name]["final_routing_learning"]), name
        assert np.isclose(frozen[-1], endpoints[name]["final_routing_control"]), name
        curves[name] = x, learn, frozen
    return curves


def k_figures(curves):
    x, learn, frozen = curves["dataops"]
    purple = COLORS["dataops"]
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=.09, right=.955, bottom=.18, top=.80)
    heading(fig, "K-learning divergence, DataOps (production geometry)", "Verified-outcome routing · B=2 · measured checkpoints")
    ax.fill_between(x, frozen, learn, color=purple, alpha=.09)
    ax.plot(x, learn, color=purple, marker="o", ms=4, label="Learned K")
    ax.plot(x, frozen, color=GRAY, ls="--", marker="o", ms=3, label="Frozen K")
    ax.set(xlim=(0, 500), ylim=(0, 1), xlabel="Decisions", ylabel="Routing quality")
    ax.set_xticks(range(0, 501, 50))
    ax.set_yticks(np.linspace(0, 1, 6))
    delta = 100 * (learn[-1] / frozen[-1] - 1)
    ax.annotate(f"Δ = +{delta:.0f}%", xy=(500, learn[-1]), xytext=(350, .85),
                fontsize=14, weight="bold", color=purple,
                arrowprops={"arrowstyle": "->", "color": purple, "lw": 1.6})
    ax.legend(loc="upper left", frameon=False)
    footnote(fig, "REAL_COMPONENT · synthetic verification · first observation: N=50")
    save(fig, "fig_1_k_divergence", "k_learning_curve_results.json; endpoints verified against cross-copilot summary; relative delta at N=500")

    fig, axes = plt.subplots(1, 5, figsize=(10, 6), sharey=True)
    fig.subplots_adjust(left=.09, right=.98, bottom=.23, top=.71, wspace=.20)
    gains = [100 * (curves[n][1][-1] / curves[n][2][-1] - 1) for n in ORDER]
    positive = sum(g > 0 for g in gains)
    heading(fig, "K-learning across five copilots", f"{positive} of 5 improved · {sum(g < 0 for g in gains)} regressions · relative routing Δ at N=500")
    for ax, name, gain in zip(axes, ORDER, gains):
        x, learn, frozen = curves[name]
        ax.plot(x, learn, color=COLORS[name])
        ax.plot(x, frozen, color=GRAY, ls="--", lw=1.8)
        ax.set_title(NAMES[name], color=COLORS[name], pad=34)
        ax.text(.5, 1.06, f"Δ +{gain:.0f}%", transform=ax.transAxes, ha="center", color=COLORS[name])
        ax.set(xlim=(0, 500), ylim=(0, 1), xticks=[0, 250, 500])
        ax.get_xticklabels()[0].set_ha("left")
        ax.get_xticklabels()[-1].set_ha("right")
        ax.set_yticks(np.linspace(0, 1, 6))
    axes[0].set_ylabel("Routing quality")
    fig.supxlabel("Decisions", y=.135, fontsize=11)
    fig.legend(handles=[Line2D([], [], color=INK, label="Learned K"), Line2D([], [], color=GRAY, ls="--", label="Frozen K")],
               loc="lower center", bbox_to_anchor=(.5, .06), ncol=2, frameon=False)
    footnote(fig, "REAL_COMPONENT · synthetic verification · first observation: N=50")
    save(fig, "fig_2_cross_copilot_k", "Per-copilot k_learning_curve JSON checkpoints; cross-copilot summary endpoint checks")


def budget_frontier(data, csv_rows):
    rows = {(r["copilot"], str(r["budget"]), r["policy"]): r for r in data["rows"]}
    assert len(rows) == len(csv_rows) == 90
    for r in csv_rows:
        ref = rows[r["copilot"], r["budget"], r["policy"]]
        for key in ("accuracy_mean", "accuracy_std", "reads_mean"):
            assert np.isclose(float(r[key]), ref[key]), (r, key)
    budgets = ("0", "1", "2", "3", "4", "exhaustive")
    fig, axes = plt.subplots(1, 5, figsize=(10, 6), sharey=True)
    fig.subplots_adjust(left=.09, right=.98, bottom=.27, top=.70, wspace=.20)
    acc = [rows[n, "2", "vld"]["accuracy_mean"] * 100 for n in ORDER]
    reads = [rows[n, "2", "vld"]["reads_mean"] / data["copilots"][n]["ndim"] * 100 for n in ORDER]
    heading(fig, "Budget–accuracy frontier", f"B=2: {min(acc):.0f}–{max(acc):.0f}% accuracy · {min(reads):.0f}–{max(reads):.0f}% of exhaustive reads")
    for ax, name, a, r in zip(axes, ORDER, acc, reads):
        ax.axvline(2, color=COLORS[name], alpha=.25, lw=6, zorder=0)
        for policy, ls, color in (("vld", "-", COLORS[name]), ("random", "--", GRAY), ("single_pass", ":", "#94A3B8")):
            ax.plot(range(6), [rows[name, b, policy]["accuracy_mean"] for b in budgets], ls=ls, color=color, marker="o", ms=3)
        ax.set_title(NAMES[name], color=COLORS[name], pad=34)
        ax.text(.5, 1.07, f"{a:.0f}% / {r:.0f}%", ha="center", transform=ax.transAxes, fontsize=11)
        ax.set(xlim=(-.15, 5.15), ylim=(0, 1.025))
        ax.set_xticks(range(6), ["0", "1", "2", "3", "4", "Exh."], rotation=90)
        ax.set_yticks(np.linspace(0, 1, 6))
    axes[0].set_ylabel("Accuracy")
    fig.supxlabel("Read budget · Exh. = exhaustive", y=.15, fontsize=11)
    fig.legend(handles=[Line2D([], [], color=c, ls=ls, label=label) for label, ls, c in
                        (("VLD", "-", INK), ("Random", "--", GRAY), ("Single-pass", ":", "#94A3B8"))],
               loc="lower center", bbox_to_anchor=(.5, .065), ncol=3, frameon=False)
    footnote(fig, "5-seed means · synthetic verification · exhaustive accuracy: 100% by construction")
    save(fig, "fig_3_budget_frontier", "budget_accuracy_frontier.json rows; CSV parity verified; categorical exhaustive endpoint")


def risk_coverage(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=.10, right=.965, bottom=.25, top=.78)
    heading(fig, "Governed autonomy: risk–coverage", "Post-investigation confidence · final_d_min · lift at 75% coverage")
    ax.axvline(.75, color=PALE, ls=":", lw=1.7)
    labels_y = {"dataops": .845, "purchasing": .892, "soc": .945}
    for c in data["copilots"]:
        name = c["copilot"]
        signal = next(s for s in c["post_investigation_diagnostic"]["signals"] if s["signal"] == "d_min")
        curve = sorted(signal["curve"], key=lambda p: -p["coverage"])
        x = np.array([p["coverage"] for p in curve])
        y = np.array([p["accuracy_on_acted"] for p in curve])
        assert np.all(np.diff(y) >= -1e-12)
        ax.plot(x, y, color=COLORS[name], marker="o", ms=4, label=NAMES[name], zorder=3)
        ax.axhline(signal["baseline_accuracy"], color=COLORS[name], ls="--", alpha=.6, lw=1.3)
        p = next(p for p in curve if p["coverage"] == .75)
        lift = 100 * p["accuracy_lift_vs_baseline"]
        ax.annotate(f"{NAMES[name]}  +{lift:.1f} pp", xy=(.75, p["accuracy_on_acted"]), xytext=(.44, labels_y[name]),
                    color=COLORS[name], fontsize=11, weight="bold",
                    arrowprops={"arrowstyle": "-", "color": COLORS[name], "lw": 1.2})
    ax.set(xlim=(1, .10), ylim=(.74, 1.025), xlabel="Coverage", ylabel="Accuracy on acted")
    ax.set_xticks([1, .9, .75, .6, .5, .4, .3, .2, .1])
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([], [], color=GRAY, ls="--", label="Act-on-all baseline"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.53, .075), ncol=4, frameon=False)
    footnote(fig, "5-seed means · synthetic labels · post-read selection · unchanged investigation cost")
    save(fig, "fig_4_risk_coverage", "gap2_abstention_curve.json: copilots/post_investigation_diagnostic/signals[d_min]; unmodified measured curves")


def recurrence(data):
    variants = ("static", "rnn", "gru", "lstm")
    values = np.array([[data["results"][f"{v}_{k}"]["final_routing_mean"] for k in ("fixed", "learning")] for v in variants])
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.subplots_adjust(left=.16, right=.68, bottom=.18, top=.73)
    heading(fig, "Graph memory: routing × K interaction", "RI-1 · DataOps · 10-seed means · N=500")
    sns.heatmap(values, ax=ax, annot=True, fmt=".3f", cmap=sns.light_palette(COLORS["dataops"], as_cmap=True),
                vmin=.4, vmax=.65, cbar=False, linewidths=3, linecolor=BG,
                xticklabels=["K-Fixed", "K-Learning"], yticklabels=["Static", "RNN", "GRU", "LSTM"],
                annot_kws={"fontsize": 14, "weight": "bold"})
    ax.tick_params(axis="both", rotation=0, length=0)
    ax.add_patch(Rectangle((1.02, .02), .96, .96, fill=False, ec=COLORS["purchasing"], lw=3))
    ax.text(2.16, -.22, "K lift", fontsize=11, weight="bold")
    for i, (fixed, learned) in enumerate(values):
        ax.text(2.16, i+.5, f"+{100*(learned-fixed):.1f} pp", va="center", fontsize=11, color=INK)
    cax = fig.add_axes([.84, .26, .025, .40])
    colorbar = fig.colorbar(ax.collections[0], cax=cax, ticks=[.4, .5, .6, .65])
    colorbar.set_label("Routing quality", fontsize=11)
    footnote(fig, "Green outline: Static + K · production geometry · synthetic verification")
    save(fig, "fig_5_recurrence_heatmap", "ri1_routing_k_interaction.json results/final_routing_mean; absolute K lifts in percentage points")


def q_ablation(norm, raw):
    variants = ("PRECISION-ONLY", "DISCRIMINATIVE-ONLY", "LEVERAGE-ONLY", "PREC+DISC", "PREC+LEV", "DISC+LEV", "ALL-THREE")
    labels = ("P", "D", "L", "P+D", "P+L", "D+L", "P+D+L")
    raw_lookup = {(r["copilot"], r["variant"]): r["routing_mean"] for r in raw["rows"]}
    for r in norm["rows"]:
        if r["normalization"] in ("RAW", "SHARED"):
            assert np.isclose(r["routing_mean"], raw_lookup[r["copilot"], r["variant"]])
    refs = {v: np.mean([raw_lookup[n, v] for n in ORDER]) for v in ("RANDOM", "NO-K")}
    fig, axes = plt.subplots(1, 3, figsize=(10, 6), sharex=True)
    fig.subplots_adjust(left=.11, right=.97, bottom=.25, top=.70, wspace=.44)
    heading(fig, "Q term ablation: normalization", "Routing quality · equal-weight mean across five copilots · B=2")
    for ax, method in zip(axes, ("RAW", "Z-NORM", "MINMAX")):
        vals = []
        for v in variants:
            rows = [r for r in norm["rows"] if r["normalization"] == method and r["variant"] == v]
            assert {r["copilot"] for r in rows} == set(ORDER) and len(rows) == 5
            vals.append(np.mean([r["routing_mean"] for r in rows]))
        ax.barh(range(7), vals, color=[PALE]*6+[INK], height=.64)
        for y, value in enumerate(vals):
            ax.text(value+.018, y, f"{value:.3f}", va="center", fontsize=11, zorder=5,
                    bbox={"facecolor": BG, "edgecolor": "none", "pad": .3})
        ax.axvline(refs["RANDOM"], color=GRAY, ls="--", lw=1.4)
        ax.axvline(refs["NO-K"], color=GRAY, ls=":", lw=1.6)
        ax.set(yticks=range(7), yticklabels=labels, xlim=(0, 1), xticks=[0, .5, 1])
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_title(method, pad=34)
        ax.text(.5, 1.07, f"P+L Δ: {100*(vals[4]-vals[6]):+.1f} pp", transform=ax.transAxes, ha="center", fontsize=11)
    fig.supxlabel("Routing quality", y=.16, fontsize=11)
    fig.legend(handles=[Patch(color=INK, label="All three"), Line2D([], [], color=GRAY, ls="--", label="RANDOM"),
                        Line2D([], [], color=GRAY, ls=":", label="NO-K (raw)")],
               loc="lower center", bbox_to_anchor=(.5, .08), ncol=3, frameon=False)
    footnote(fig, "P: precision · D: discriminative · L: leverage · Δ vs all three · shared raw controls")
    save(fig, "fig_6_q_ablation_normalized", "q_term_ablation_normalized.json rows; raw/control parity with q_term_ablation.json; macro mean over five copilots")


def sensitivity(paper):
    # Read the authorized paper's distinct cohort, never frontier accuracy counts.
    section = paper.split("| Copilot | B=2 | B=3 | B=4 |", 1)[1].split("**The compounding rate", 1)[0]
    counts = {}
    for line in section.splitlines():
        cells = [s.strip() for s in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] in NAMES.values():
            parsed = [re.fullmatch(r"(\d+):(\d+)", c) for c in cells[1:]]
            assert all(parsed), cells
            counts[cells[0]] = [(int(m[1]), int(m[2])) for m in parsed]
    assert set(counts) == set(NAMES.values())
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=.09, right=.975, bottom=.22, top=.76)
    heading(fig, "Budget sensitivity: domain structure", "SOC: depth · Trading: discrimination · Purchasing: plateau")
    width = .23
    hatches = ("", "//", "xx")
    for i, name in enumerate(ORDER):
        for j, (saves, hurts) in enumerate(counts[NAMES[name]]):
            x = i+(j-1)*width
            ax.bar(x, saves, width=.20, color=COLORS[name], hatch=hatches[j], edgecolor=BG, linewidth=1.1)
            ax.text(x, saves+.55, f"{saves}:{hurts}", ha="center", va="bottom", fontsize=11)
    ax.set(xticks=range(5), xticklabels=[NAMES[n] for n in ORDER], ylabel="Saves", ylim=(0, 26))
    ax.set_yticks(range(0, 26, 5))
    ax.grid(axis="x", visible=False)
    fig.legend(handles=[Patch(facecolor=GRAY, edgecolor=BG, hatch=h, label=f"B={b}") for b, h in zip((2, 3, 4), hatches)],
               loc="lower center", bbox_to_anchor=(.5, .105), ncol=3, frameon=False)
    footnote(fig, "SIMULATED · 50 scenarios / copilot · labels: saves:hurts · paper v6, §4.1")
    save(fig, "fig_7_budget_sensitivity", "ci_rgi_impact_core_v6.md section 4.1 saves:hurts table; constructed 50-scenario cohorts, separate from budget frontier")


def taxonomy(paper):
    for level in range(6):
        assert f"| R{level} " in paper
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_position([.06, .12, .9, .69])
    ax.set(xlim=(0, 1), ylim=(0, 6))
    ax.axis("off")
    heading(fig, "Recurrence taxonomy: R0–R5", "State location · mechanism · experimental verdict")
    entries = (
        ("R0", "Static", "Fixed plan · no recurrence", "✓", "Leads routing", COLORS["purchasing"]),
        ("R1", "Within-episode", "Hidden state per read", "✗", "Below static", COLORS["trading"]),
        ("R2", "Between-decision", "K utility weights", "✓", "Dominant effect", COLORS["purchasing"]),
        ("R3", "Cross-episode", "Trajectory patterns", "?", "Untested", GRAY),
        ("R4", "Cross-copilot", "K transfer across domains", "∅", "Zero factor overlap", GRAY),
        ("R5", "Temporal / regime", "Time-weighted / indexed K", "✗ / ✓", "Decay / regime", INK),
    )
    ax.plot([.037, .037], [.5, 5.5], color=PALE, lw=2, zorder=0)
    for i, (level, name, state, icon, verdict, color) in enumerate(entries):
        y = 5.5-i
        highlight = level == "R2"
        ax.add_patch(FancyBboxPatch((.075, y-.39), .91, .78, boxstyle="round,pad=0.01,rounding_size=0.035",
                                   fc="#E9F7EF" if highlight else "#F1F4F8", ec=COLORS["purchasing"] if highlight else "none", lw=1.5))
        ax.text(.037, y, level, ha="center", va="center", weight="bold", fontsize=11,
                bbox={"boxstyle": "circle,pad=.42", "fc": COLORS["purchasing"] if highlight else INK, "ec": BG}, color="white")
        ax.text(.105, y+.13, name, va="center", fontsize=11, weight="bold")
        ax.text(.105, y-.17, state, va="center", fontsize=11, color=GRAY)
        ax.text(.64, y, icon, ha="center", va="center", fontsize=17, color=color)
        ax.text(.72, y, verdict, va="center", fontsize=11, color=color, weight="bold" if highlight else "normal")
    footnote(fig, "✓ works     ✗ rejected     ? untested     ∅ untestable     ·     paper v6, §4.4")
    save(fig, "fig_8_taxonomy", "Conceptual diagram from ci_rgi_impact_core_v6.md section 4.4; R5 mixed decay/regime verdict retained")


def verify_outputs():
    assert len(GENERATED) == 16
    for path in GENERATED:
        assert path.stat().st_size > 0
        if path.suffix == ".png":
            assert path.stat().st_size > 50_000, path
            with Image.open(path) as im:
                assert im.size in ((3000, 1800), (2400, 1500)), (path, im.size)
                assert abs(im.info["dpi"][0]-300) < .1
                assert np.asarray(im)[10:20, 10:20, :3].mean() > 240
    with Image.open(OUT / "fig_1_k_divergence.png") as im:
        pixels = np.asarray(im)[..., :3]
        assert np.any(np.all(pixels == (124, 58, 237), axis=-1)), "DataOps palette"
    for path, before in INPUT_HASHES.items():
        assert digest(path) == before, f"Input changed: {path}"


def main():
    source_hashes = {ROOT / p: digest(ROOT / p) for p in SOURCES}
    required = ("k_learning_curve_cross_copilot_summary.json", "budget_accuracy_frontier.json", "gap2_abstention_curve.json",
                "ri1_routing_k_interaction.json", "q_term_ablation_normalized.json", "q_term_ablation.json", "budget_accuracy_frontier.csv")
    for name in required:
        if not (DATA / name).is_file():
            raise FileNotFoundError(DATA / name)
    paper = read_text(PAPER)
    curves = load_k(read_json(required[0]))
    frontier = read_json(required[1])
    gap = read_json(required[2])
    ri1 = read_json(required[3])
    norm = read_json(required[4])
    raw = read_json(required[5])
    csv_rows = list(csv.DictReader(read_text(DATA / required[6]).splitlines()))
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    k_figures(curves)
    budget_frontier(frontier, csv_rows)
    risk_coverage(gap)
    recurrence(ri1)
    q_ablation(norm, raw)
    sensitivity(paper)
    taxonomy(paper)
    verify_outputs()
    for path, before in source_hashes.items():
        after = digest(path)
        assert before == after, f"Source changed: {path}"
        print(f"Source unchanged: {path.relative_to(ROOT)} {after[:16]}...")
    print(f"\nGenerated {len(GENERATED)} files in {OUT}")
    for path in GENERATED:
        print(f"  {path.name}: {path.stat().st_size:,} bytes")
    print("PASS: 8 PNG + 8 SVG; PNG >50 KB; 300 dpi; exact dimensions; light backgrounds; DataOps purple; unchanged inputs/sources")
    print("Provenance: K checkpoint JSONs; final_d_min from post-investigation d_min; Figure 7 from paper v6 table (CSV lacks counts)")


if __name__ == "__main__":
    main()
