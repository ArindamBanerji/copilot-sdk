from pathlib import Path
import json
import sys

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments" / "vld" / "harnesses"))
import safety_layer_characterization as experiment  # type: ignore[import]


OUT = ROOT / "experiments" / "vld" / "charts" / "pub_safety_layers.png"


def main() -> None:
    geometry = experiment.load_geometry()
    rows_cold = experiment.threat_stream("soc", geometry, 42, "SUSTAINED-POISON")
    rows_steady = experiment.threat_stream("soc", geometry, 42, "SUDDEN-DROP")
    colors = {"G-ABS": "#2f6db0", "G-REL": "#e58b32", "G-BOTH": "#3f8f5f"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for ax, rows, indices, title in [(axes[0], rows_cold, range(100), "Cold-Start Regime"), (axes[1], rows_steady, range(400, 500), "Steady-State Regime")]:
        for config, color in colors.items():
            fired = experiment.trace(rows, config, experiment.FLOORS["soc"])
            values = [0 if fired[i] else 1 for i in indices]
            ax.plot(list(indices), values, color=color, linewidth=2.5 if config == "G-BOTH" else 1.8,
                    linestyle="--" if config == "G-REL" else "-", label=config)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Verified decisions")
        ax.set_ylabel("Gate allows (1=yes, 0=no)")
        ax.set_yticks([0, 0.5, 1], ["RED", "AMBER", "GREEN"])
        ax.set_ylim(-0.08, 1.08)
        ax.grid(axis="both", color="#dddddd", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axvspan(1, 100, color="#d96b6b", alpha=0.10) if title.startswith("Cold") else ax.axvspan(451, 500, color="#d96b6b", alpha=0.10)
        ax.legend(frameon=False, loc="lower right")
    axes[0].axvline(experiment.v_clear(rows_cold, experiment.FLOORS["soc"]), color="#555555", linestyle=":")
    axes[0].text(0.16, 0.10, "V_clear", transform=axes[0].transAxes, color="#555555")
    axes[1].text(0.49, 0.10, "drop injection", transform=axes[1].transAxes, color="#8b2222", ha="center")
    fig.suptitle("Safety-Layer Characterization: Two Regimes, Two Protectors", fontsize=12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
