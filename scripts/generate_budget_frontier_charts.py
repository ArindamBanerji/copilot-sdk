"""Plot the measured budget frontier; never overwrite existing artifacts."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "experiments/vld/budget_accuracy_frontier.json"
CHARTS = ROOT / "experiments/vld/charts"
OUTPUTS = (CHARTS / "pub_budget_frontier_all_copilots.png",
           CHARTS / "pub_budget_efficiency.png")
NAMES = {"soc": "SOC", "dataops": "DataOps", "s2p": "S2P",
         "purchasing": "Purchasing", "trading": "Trading"}
LABELS = {"vld": "VLD + K", "single_pass": "Single-pass", "random": "Random"}
COLORS = {"vld": "#1769aa", "single_pass": "#666666", "random": "#d87916"}


def style():
    plt.rcParams.update({
        "figure.facecolor": "#fbfcfe", "axes.facecolor": "#ffffff",
        "savefig.facecolor": "#fbfcfe", "font.size": 11, "axes.titlesize": 14,
        "axes.labelcolor": "#293442", "text.color": "#293442",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#bac4cf", "grid.color": "#dce2e9",
        "grid.linewidth": .7, "axes.axisbelow": True,
        "savefig.dpi": 180})


def main():
    for path in OUTPUTS:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert data["checks"]["aggregate_rows"] == 90
    style()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.8), sharey=True)
    handles = None
    for ax, (copilot, result) in zip(axes.flat, data["copilots"].items()):
        labels = ["0", "1", "2", "3", "4", "exhaustive"]
        x = np.array([0, 1, 2, 3, 4, result["ndim"]])
        for policy in ("vld", "single_pass", "random"):
            means = np.array([result["results"][b][policy]["accuracy_mean"] for b in labels])
            sds = np.array([result["results"][b][policy]["accuracy_std"] for b in labels])
            ax.plot(x, means, marker="o" if policy != "single_pass" else None,
                    linestyle="--" if policy == "single_pass" else "-",
                    linewidth=2, markersize=4.5, color=COLORS[policy], label=LABELS[policy])
            ax.fill_between(x, np.maximum(0, means-sds), np.minimum(1, means+sds),
                            color=COLORS[policy], alpha=.09)
        ax.set_title(f"{NAMES[copilot]} · {result['ndim']} dimensions", loc="left", pad=12)
        ax.set_xticks(x, ["0", "1", "2", "3", "4", f"Exh.\n({result['ndim']})"])
        ax.set_ylim(0, 1.04)
        ax.set_yticks(np.linspace(0, 1, 6))
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_xlabel("Budget (reads)")
        ax.set_ylabel("Action accuracy")
        ax.grid(axis="y")
        handles = ax.get_legend_handles_labels()
    notes = axes.flat[-1]
    notes.axis("off")
    notes.legend(*handles, loc="upper left", frameon=False, fontsize=13)
    notes.text(.03, .55,
               "500 training · 200 evaluation\n5 seeds · bands: ±1 SD\n"
               "Frozen evaluation K\nSingle-pass: zero reads\n"
               "Exhaustive: all dimensions\nProduction geometry · synthetic evidence",
               transform=notes.transAxes, fontsize=12, linespacing=1.8, va="top")
    fig.suptitle("Budget–accuracy frontier", fontsize=21, x=.065, ha="left", y=.985)
    fig.subplots_adjust(left=.065, right=.985, bottom=.09, top=.9, wspace=.25, hspace=.43)
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUTS[0])
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    copilots = list(data["copilots"])
    ratios = [data["copilots"][c]["b2_efficiency"]["fraction_of_exhaustive_accuracy"]
              for c in copilots]
    sds = [data["copilots"][c]["b2_efficiency"]["per_seed_ratio_std"] for c in copilots]
    bars = ax.bar(range(5), ratios, width=.6, color=COLORS["vld"],
                  yerr=sds, capsize=4, error_kw={"color": "#344456", "linewidth": 1.1})
    for bar, value, sd in zip(bars, ratios, sds):
        ax.text(bar.get_x()+bar.get_width()/2, value+sd+.018,
                f"{value:.1%}", ha="center", fontsize=13, weight="bold")
    ax.axhline(1, color="#7d8896", linestyle="--", linewidth=1)
    ax.set_xticks(range(5), [NAMES[c] for c in copilots])
    ax.set_ylim(0, 1.1)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_ylabel("B=2 / exhaustive accuracy")
    ax.grid(axis="y")
    ax.set_title("VLD accuracy retained at two reads", loc="left", pad=25, fontsize=20)
    fig.text(.105, .855, "Full-vector oracle · 5 seeds · error bars: ±1 SD",
             fontsize=11, color="#5a6675")
    fig.text(.105, .035, "Production geometry · synthetic evidence · exhaustive accuracy: 100%",
             fontsize=10, color="#5a6675")
    fig.subplots_adjust(left=.105, right=.975, bottom=.12, top=.84)
    fig.savefig(OUTPUTS[1])
    plt.close(fig)
    for path in OUTPUTS:
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
