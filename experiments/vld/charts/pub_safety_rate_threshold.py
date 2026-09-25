from __future__ import annotations

"""Render rate-detector threshold sensitivity."""

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
VLD = ROOT / "experiments" / "vld"
RESULT = VLD / "results" / "safety_layer_characterization_r2.json"
OUT = VLD / "charts" / "pub_safety_rate_threshold.png"


def main() -> None:
    data = json.loads(RESULT.read_text(encoding="utf-8"))
    thresholds = [float(value) for value in data["metadata"]["rate_thresholds"]]
    copilots = data["metadata"]["copilots"]
    pauses: list[float] = []
    lags: list[float] = []
    for threshold in thresholds:
        clean = [data["rate_threshold_sensitivity"][copilot][str(threshold)]["CLEAN"]["aggregate"]["false_pause_rate_mean"] for copilot in copilots]
        drop = [data["rate_threshold_sensitivity"][copilot][str(threshold)]["SUDDEN-DROP"]["aggregate"]["detection_lag_mean"] for copilot in copilots]
        pauses.append(sum(float(value) for value in clean) / len(clean))
        lags.append(sum(float(value) for value in drop) / len(drop))
    figure, left = plt.subplots(figsize=(8, 5), constrained_layout=True, facecolor="white")
    x = list(range(len(thresholds)))
    bars = left.bar(x, [value * 100 for value in pauses], color="#7aa6d8", width=0.55, label="Clean false-pause rate")
    left.set_xlabel("Rate threshold")
    left.set_ylabel("False-pause rate (%)")
    left.set_xticks(x, [f"{value:.2f}" for value in thresholds])
    left.grid(True, axis="y", color="#dddddd", linewidth=0.7)
    right = left.twinx()
    right.plot(x, lags, color="#c43d3d", marker="o", linewidth=2, label="Sudden-drop detection lag")
    right.set_ylabel("Detection lag (decisions)")
    left.axvline(1, color="#2f8f5b", linestyle="--", linewidth=1.4)
    left.text(1.04, max(value * 100 for value in pauses) * 0.92, "deployed", color="#2f8f5b", fontsize=9)
    for bar, value in zip(bars, pauses):
        left.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{value:.1%}", ha="center", fontsize=9)
    figure.suptitle("Short-Window Rate Detector: Threshold Sensitivity", fontsize=12)
    figure.savefig(OUT, dpi=200, facecolor="white")
    plt.close(figure)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
