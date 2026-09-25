from __future__ import annotations

"""Render the Round 2 three-layer safety diagnostic figure."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
VLD = ROOT / "experiments" / "vld"
sys.path.insert(0, str(VLD / "harnesses"))
import safety_layer_characterization_r2 as r2  # type: ignore[import]  # noqa: E402


OUT = VLD / "charts" / "pub_safety_layers_r2.png"
COLORS = {"G-ABS": "#2f6db0", "G-REL": "#e28b2c", "G-RATE": "#c43d3d", "G-THREE": "#2f8f5b"}
STYLES = {"G-ABS": ":", "G-REL": "--", "G-RATE": "-", "G-THREE": "-"}


def draw_panel(ax: plt.Axes, rows: list[dict[str, object]], title: str, threat_start: int, threat_end: int, annotation: str) -> None:
    for config in ("G-ABS", "G-REL", "G-RATE", "G-THREE"):
        fired, _ = r2.trace(rows, config, r2.r1.FLOORS["soc"])
        x = list(range(1, len(fired) + 1))
        y = [0.0 if value else 1.0 for value in fired]
        ax.plot(x, y, label=config, color=COLORS[config], linestyle=STYLES[config], linewidth=2.4 if config == "G-THREE" else 1.7)
    ax.axvspan(threat_start, threat_end, color="#efc2c2", alpha=0.35, label="injection" if threat_start > 400 else None)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel("Verified decision")
    ax.set_ylabel("Gate allows (1) / pauses (0)")
    ax.set_ylim(-0.08, 1.08)
    ax.set_yticks([0, 1], ["PAUSE", "ALLOW"])
    ax.grid(True, axis="both", color="#dddddd", linewidth=0.7)
    ax.text(0.02, 0.05, annotation, transform=ax.transAxes, fontsize=9, va="bottom", bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})


def main() -> None:
    geometry = r2.r1.load_geometry()
    clean = r2.r1.threat_stream("soc", geometry, 42, "CLEAN")
    poison = r2.r1.threat_stream("soc", geometry, 42, "SUSTAINED-POISON")
    drop = r2.r1.threat_stream("soc", geometry, 42, "SUDDEN-DROP")
    figure, axes = plt.subplots(1, 3, figsize=(16, 5), constrained_layout=True, facecolor="white")
    draw_panel(axes[0], poison[:100], "Cold-start: sustained poison", 1, 100, "G-ABS protects the first decisions")
    draw_panel(axes[1], drop[400:500], "Steady-state: sudden drop", 51, 100, "G-RATE is the short-window detector")
    draw_panel(axes[2], poison[400:500], "Steady-state: sustained poison", 1, 100, "G-THREE inherits rate sensitivity")
    axes[0].legend(loc="upper right", fontsize=8, frameon=True)
    figure.suptitle("Three-Layer Safety Architecture: Measured Gap and Fix", fontsize=14)
    figure.savefig(OUT, dpi=200, facecolor="white")
    plt.close(figure)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
