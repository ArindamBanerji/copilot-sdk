from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "vld" / "results" / "safety_layer_characterization.json"
OUT = ROOT / "experiments" / "vld" / "charts" / "pub_safety_multiplier_sensitivity.png"


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    multipliers = [0.6, 0.7, 0.8]
    false_pause = []
    lags = []
    for multiplier in multipliers:
        entries = [data["multiplier_sensitivity"][copilot][str(multiplier)] for copilot in data["metadata"]["copilots"]]
        false_pause.append(100 * float(np.mean([entry["CLEAN"]["false_pause_rate_mean"] for entry in entries])))
        observed = [entry["SUDDEN-DROP"]["detection_lag_mean"] for entry in entries if entry["SUDDEN-DROP"]["detection_lag_mean"] is not None]
        lags.append(float(np.mean(observed)) if observed else 0.0)
    fig, left = plt.subplots(figsize=(7.5, 4.5), constrained_layout=True)
    x = np.arange(len(multipliers))
    left.bar(x, false_pause, color="#6f9fce", width=0.55, label="False-pause rate")
    left.set_ylabel("False-pause rate (%)")
    left.set_xlabel("Relative-trigger multiplier")
    left.set_xticks(x, [f"{value:.1f}" for value in multipliers])
    left.grid(axis="y", color="#dddddd", linewidth=0.7)
    left.spines[["top", "right"]].set_visible(False)
    right = left.twinx()
    right.plot(x, lags, color="#d96b43", marker="o", linewidth=2, label="Sudden-drop detection lag")
    right.set_ylabel("Detection lag (decisions)")
    right.spines["top"].set_visible(False)
    left.axvline(1, color="#444444", linestyle="--", linewidth=1)
    left.text(1.04, max(false_pause + [1]) * 0.85, "deployed", color="#444444")
    left.set_title("Relative-Trigger Multiplier Sensitivity", fontsize=12)
    handles, labels = left.get_legend_handles_labels()
    handles2, labels2 = right.get_legend_handles_labels()
    left.legend(handles + handles2, labels + labels2, frameon=False, loc="upper left")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
