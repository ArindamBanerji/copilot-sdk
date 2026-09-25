"""Render four publication charts from existing JSON/CSV artifacts only.

No experiment is run and no values are recomputed beyond plotting transforms.
The third additive Q term is preregistered as ``discriminative``:
abs(mu[a1,k] - mu[a2,k]), the separation of the top two action centroids.
Tier captions are included in every figure.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import seaborn as sns  # type: ignore[import]

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/vld"
CHARTS = DATA / "charts"
COLORS = {"soc": "#2563EB", "trading": "#DC2626", "purchasing": "#059669",
          "dataops": "#7C3AED", "s2p": "#D97706"}
DISPLAY = {"soc": "SOC", "trading": "Trading", "purchasing": "Purchasing",
           "dataops": "DataOps", "s2p": "S2P"}
R = dict[str, Any]


def setup() -> None:
    sns.set_theme(style="whitegrid", rc={"figure.facecolor": "#FAFAFA",
                                          "axes.facecolor": "#FAFAFA",
                                          "font.family": "sans-serif",
                                          "font.size": 11,
                                          "axes.titlesize": 14,
                                          "axes.labelsize": 11})
    CHARTS.mkdir(parents=True, exist_ok=True)


def save(fig: plt.Figure, name: str) -> None:
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(CHARTS / name, dpi=300, facecolor="#FAFAFA", bbox_inches="tight")
    plt.close(fig)


def caption(fig: plt.Figure, text: str) -> None:
    fig.text(0.5, 0.015, text, ha="center", va="bottom", fontsize=9, color="#4B5563")


def load_scatter() -> dict[str, R]:
    path = DATA / "results/decision_complexity_scatter.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    selected: dict[str, R] = {}
    for row in rows:
        if row["capability_result"] != "k_curve_gain" or row["complexity_measure"] != "intrinsic_dimensionality":
            continue
        key = row["copilot_or_config"]
        selected[key] = {"x": float(row["complexity_value"]),
                         "y": float(row["capability_value"])}
    return selected


def chart_complexity() -> None:
    points = load_scatter()
    fig, ax = plt.subplots(figsize=(10, 6))
    for key in ("soc", "dataops", "trading", "purchasing", "s2p", "s2p_multi_enterprise"):
        if key not in points:
            continue
        color_key = "s2p" if key.startswith("s2p") else key
        marker = "o" if key != "s2p_multi_enterprise" else "D"
        label = "S2P multi-enterprise" if key == "s2p_multi_enterprise" else DISPLAY.get(key, key)
        p = points[key]
        ax.scatter(p["x"], p["y"], s=105, color=COLORS[color_key], marker=marker,
                   edgecolor="white", linewidth=1.2, zorder=3)
        ax.annotate(label, (p["x"], p["y"]), xytext=(7, 7), textcoords="offset points",
                    fontsize=10, color="#111827")
    if "s2p" in points and "s2p_multi_enterprise" in points:
        a, b = points["s2p"], points["s2p_multi_enterprise"]
        ax.add_patch(FancyArrowPatch((a["x"], a["y"]), (b["x"], b["y"]),
                                     arrowstyle="-|>", mutation_scale=16,
                                     color=COLORS["s2p"], linewidth=1.8,
                                     connectionstyle="arc3,rad=-.15", zorder=2))
        ax.text((a["x"] + b["x"]) / 2 + .05, (a["y"] + b["y"]) / 2 - 2,
                "same-domain contrast", color=COLORS["s2p"], fontsize=9)
    ax.set_title("Applicability is characterized")
    ax.set_xlabel("Intrinsic dimensionality (PCA participation ratio)")
    ax.set_ylabel("K-learning gain in action_accuracy (pp)")
    ax.text(0.03, 0.96, "Spearman ρ = +0.90", transform=ax.transAxes, va="top",
            fontsize=11, color="#111827", bbox={"boxstyle": "round,pad=.3", "fc": "white", "ec": "#D1D5DB"})
    caption(fig, "Tier: geometry-derived synthetic. S2P multi-enterprise is constructed (3 firm profiles). n=5–6, exploratory.")
    save(fig, "pub_complexity_scatter.png")


def chart_recurrence() -> None:
    ri = json.loads((DATA / "ri1_routing_k_interaction.json").read_text(encoding="utf-8"))
    rv0 = json.loads((DATA / "rv0_gru_ablation_results.json").read_text(encoding="utf-8"))
    rv8 = json.loads((DATA / "rv8_adaptive_q.json").read_text(encoding="utf-8"))
    vals = [float(ri["results"][k]["final_routing_mean"]) * 100 for k in
            ("static_learning", "rnn_learning", "gru_learning", "lstm_learning")]
    labels = ["Static+K", "RNN+K", "GRU+K", "LSTM+K"]
    colors = ["#2563EB", "#6B7280", "#9CA3AF", "#D1D5DB"]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, vals, color=colors, edgecolor="#374151", linewidth=.6)
    for bar, value in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, value + .8, f"{value:.1f}%",
                ha="center", va="bottom", fontsize=10)
    headroom = float(rv8["verdict"]["headroom_pp"])
    static = vals[0]
    ax.annotate(f"learned-Q headroom +{headroom:.1f}pp", xy=(0, static),
                xytext=(1.0, static + 7), arrowprops={"arrowstyle": "->", "color": "#D97706"},
                color="#92400E", fontsize=9)
    ax.set_ylim(0, max(vals) + 13)
    ax.set_ylabel("routing_quality (%)")
    ax.set_title("Depth and recurrence do not improve acquisition")
    ax.text(0.98, 0.03, "RI-1 state×K; RV-0 cross-check: " +
            f"static {rv0['results']['static']['final_routing_mean']*100:.1f}%",
            transform=ax.transAxes, ha="right", fontsize=8, color="#6B7280")
    caption(fig, "Tier: geometry-derived synthetic.")
    save(fig, "pub_recurrence_ladder_state_k.png")


def chart_oracle() -> None:
    data = json.loads((DATA / "results/oracle_ceiling_diagnostic.json").read_text(encoding="utf-8"))
    best = {"soc": "trained", "dataops": "default", "trading": "default",
            "purchasing": "default", "s2p": "default"}
    labels = list(best)
    vld, evidence, action, gaps = [], [], [], []
    for cop in labels:
        a = data[cop][best[cop]]["aggregate"]
        vld.append(float(a["vld_b2_mean"]) * 100)
        evidence.append(float(a["evidence_oracle_mean"]) * 100)
        action.append(float(a["action_oracle_mean"]) * 100)
        gaps.append(float(a["readout_gap_mean"]) * 100)
    x = np.arange(len(labels))
    width = .25
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = []
    for offset, values, alpha in [(-width, vld, 1.0), (0, evidence, .78), (width, action, .58)]:
        bars.extend(ax.bar(x + offset, values, width, color=[COLORS[k] for k in labels],
                           alpha=alpha, edgecolor="white", label=None))
    for i, bar in enumerate(bars[:len(labels)]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"gap {gaps[i]:.0f}pp", ha="center", fontsize=8, color="#111827")
    ax.set_xticks(x, [DISPLAY[k] for k in labels])
    ax.set_ylim(0, 122)
    ax.set_ylabel("action_accuracy (%)")
    ax.set_title("Action is readout-limited, not architecture-limited")
    handles = [plt.Rectangle((0, 0), 1, 1, color="#374151", alpha=a) for a in (1.0, .78, .58)]
    ax.legend(handles, ["VLD (B=2)", "Evidence oracle", "Action oracle"], loc="lower right")
    ax.text(0.01, 0.98, "Best available geometry: trained SOC; default otherwise",
            transform=ax.transAxes, va="top", fontsize=9, color="#4B5563")
    caption(fig, "Tier: geometry-derived synthetic. Near-perfect oracle scores characterize the geometry/readout pipeline.")
    save(fig, "pub_oracle_ceiling_gaps.png")


def box(ax: Any, xy: tuple[float, float], wh: tuple[float, float], text: str,
        color: str, fontsize: int = 11) -> None:
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                           transform=ax.transAxes, facecolor="white", edgecolor=color,
                           linewidth=2)
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=fontsize, color="#111827", wrap=True)


def arrow(ax: Any, start: tuple[float, float], end: tuple[float, float], color: str,
          rad: float = 0.0) -> None:
    ax.add_patch(FancyArrowPatch(start, end, transform=ax.transAxes, arrowstyle="-|>",
                                 mutation_scale=15, linewidth=2, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))


def chart_mechanism() -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("The RGI loop: acquire, act, verify, reshape", pad=18)
    inner = "#2563EB"
    outer = "#D97706"
    box(ax, (.04, .56), (.15, .12), "Decision v0", inner)
    box(ax, (.26, .56), (.18, .12), "Score A\nnearest prototype over Θ", inner, 10)
    box(ax, (.51, .56), (.22, .12), "Insufficient? Ψ acquires\nQ = K·(precision + leverage + discriminative)", inner, 9)
    box(ax, (.80, .56), (.15, .12), "Re-score A", inner)
    box(ax, (.60, .28), (.16, .12), "Conservation\ngate", outer)
    box(ax, (.82, .28), (.14, .12), "Emit", outer)
    box(ax, (.35, .06), (.22, .12), "Verified outcome", outer)
    box(ax, (.06, .06), (.20, .12), "Update μ and K", outer)
    arrow(ax, (.19, .62), (.26, .62), inner)
    arrow(ax, (.44, .62), (.51, .62), inner)
    arrow(ax, (.73, .62), (.80, .62), inner)
    arrow(ax, (.875, .56), (.69, .40), outer, -.18)
    arrow(ax, (.76, .34), (.82, .34), outer)
    arrow(ax, (.82, .28), (.57, .16), outer, .15)
    arrow(ax, (.35, .12), (.26, .12), outer)
    arrow(ax, (.16, .18), (.16, .56), outer, .25)
    ax.text(.05, .76, "INNER CLOCK · within-decision trajectory", transform=ax.transAxes,
            color=inner, fontsize=10, weight="bold")
    ax.text(.05, .005, "OUTER CLOCK · across-decision learning from verified outcomes",
            transform=ax.transAxes, color=outer, fontsize=10, weight="bold")
    caption(fig, "Tier: geometry-derived mechanism schematic with simulated evidence/verification semantics.")
    save(fig, "pub_rgi_mechanism_schematic.png")


def main() -> None:
    setup()
    chart_complexity()
    chart_recurrence()
    chart_oracle()
    chart_mechanism()
    print("Rendered four publication figures")


if __name__ == "__main__":
    main()
