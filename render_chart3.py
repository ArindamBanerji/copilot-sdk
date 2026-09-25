"""Render calibrated-vs-baseline confidence discrimination from CONS-PD-2."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
DATA = ROOT / "experiments" / "vld" / "results" / "conservation_decision_features.json"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_confidence_ablation.png"


def main() -> None:
    payload = json.loads(DATA.read_text())
    per_copilot = payload["combined_model"]["per_copilot"]
    names = ["SOC", "DataOps", "Trading", "Purchasing", "S2P"]
    keys = ["soc", "dataops", "trading", "purchasing", "s2p"]
    calibrated = np.array([per_copilot[k]["auc"] for k in keys]) * 100
    # The source records the uncalibrated/baseline pooled AUC in its summary.
    baseline = 65.6
    lifts = calibrated - baseline

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.titlesize": 12})
    fig, ax = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    positions = np.arange(len(names))
    bars = ax.bar(positions, calibrated, color="#2166ac", width=0.62, label="Calibrated (combined features)")
    ax.axhline(baseline, color="#777777", lw=2, ls="--", label="Uncalibrated baseline (pooled)")
    for bar, lift in zip(bars, lifts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2, f"+{lift:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("Confidence Calibration Ablation")
    ax.set_xlabel("Copilot")
    ax.set_ylabel("Confidence discrimination (AUC, %)")
    ax.set_xticks(positions, names)
    ax.set_ylim(55, 95)
    ax.grid(axis="y", which="major", color="#d9d9d9", lw=0.8)
    ax.legend(loc="upper left", frameon=True, framealpha=0.95)
    ax.text(0.99, 0.02, "Δ labels show lift over the recorded pooled baseline", transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#555555")
    ax.spines[["top", "right"]].set_visible(False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
