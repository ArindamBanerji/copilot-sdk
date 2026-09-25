from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_k14_agreement.png"


def main() -> None:
    data = json.loads((RESULTS / "k14_validation_tier.json").read_text())
    order = ["soc", "dataops", "s2p", "trading", "purchasing"]
    labels = ["SOC", "DataOps", "S2P", "Trading", "Purchasing"]
    k2 = [data["per_copilot"][key]["k2_anchor_agreement"] * 100 for key in order]
    k3 = [data["per_copilot"][key]["k3_anchor_agreement"] * 100 for key in order]

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})
    fig, ax = plt.subplots(figsize=(8.2, 5.0), constrained_layout=True)
    x = np.arange(len(labels))
    width = 0.36
    bars_k2 = ax.bar(x - width / 2, k2, width, color="#8c8c8c", label="Surface/LLM labels (K2)")
    bars_k3 = ax.bar(x + width / 2, k3, width, color="#2f6db0", label="Geometry-derived (K3)")
    ax.axhline(50, color="#777777", linestyle="--", linewidth=1, label="Random baseline")
    ax.set_title("Validation-Tier Effect: Surface vs Geometry-Derived Labels", fontsize=12)
    ax.set_ylabel("Agreement with ground truth (%)")
    ax.set_ylim(0, 108)
    ax.set_xticks(x, labels)
    ax.grid(axis="y", color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for bars in (bars_k2, bars_k3):
        for bar in bars:
            ax.annotate(f"{bar.get_height():.0f}%", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9)
    dataops_x = x[1]
    ax.annotate("64pp gap", xy=(dataops_x + width / 2, k3[1]), xytext=(dataops_x + 0.75, 91),
                arrowprops={"arrowstyle": "-[,widthB=2.4", "lw": 1.2, "color": "#333333"},
                ha="center", va="center", fontsize=9, color="#333333")
    ax.text(0.5, -0.17, "240 real Claude Sonnet judgments (n=43–50 per copilot)",
            transform=ax.transAxes, ha="center", fontsize=9, color="#555555")
    ax.legend(frameon=False, loc="upper right")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
