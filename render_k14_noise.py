from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parent
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_k14_compounding_noise.png"


def main() -> None:
    data = json.loads((RESULTS / "k14_compounding_noise.json").read_text())
    order = ["soc", "purchasing", "dataops", "trading", "s2p"]
    labels = ["SOC", "Purchasing", "DataOps", "Trading", "S2P"]
    meta = data["metadata"]["training_label_noise_rates"]
    clean = [data["per_copilot"][key]["clean_gain"]["mean"] * 100 for key in order]
    noisy = [data["per_copilot"][key]["noisy_gain"]["mean"] * 100 for key in order]
    random = [data["per_copilot"][key]["random_gain"]["mean"] * 100 for key in order]
    noise = [meta[key] * 100 for key in order]

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})
    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    x = np.arange(len(labels))
    width = 0.25
    bars_clean = ax.bar(x - width, clean, width, color="#4b9b63", label="Clean labels")
    bars_noisy = ax.bar(x, noisy, width, color="#e58b32", label="Noisy labels")
    bars_random = ax.bar(x + width, random, width, color="#c95353", label="Random labels")
    ax.axhline(0, color="#555555", linewidth=1)
    ax.set_title("Compounding Under Label Noise", fontsize=12)
    ax.set_ylabel("Accuracy improvement (pp)")
    ax.set_xticks(x, [f"{label}\n{rate:.0f}% noise" for label, rate in zip(labels, noise)])
    ax.grid(axis="y", color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for bars in (bars_clean, bars_noisy, bars_random):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f}", (bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4 if height >= 0 else -12), textcoords="offset points",
                        ha="center", fontsize=8)
    s2p_noisy_x = x[-1]
    ax.annotate("learning reverses", xy=(s2p_noisy_x, noisy[-1]), xytext=(s2p_noisy_x - 0.65, -8),
                arrowprops={"arrowstyle": "->", "lw": 1.1, "color": "#8b2222"},
                color="#8b2222", fontsize=9, ha="center")
    for idx, text in [(2, "+5.3pp"), (3, "+10.0pp"), (4, "+7.7pp")]:
        ax.annotate(text, xy=(x[idx], noisy[idx]), xytext=(x[idx], max(clean[idx], noisy[idx]) + 4),
                    ha="center", fontsize=8, color="#555555")
    ax.text(0.5, -0.19, "Crossover between 60% and 88% noise. Mean clean–noisy: +4.5pp",
            transform=ax.transAxes, ha="center", fontsize=9, color="#555555")
    ax.legend(frameon=False, loc="upper right")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
