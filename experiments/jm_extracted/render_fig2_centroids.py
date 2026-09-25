"""Reproduce E-JM-6 centroid snapshots for the paper's FIGURE-2 diagnostic."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SEED = 42
N_FACTORS = 7
N_CATEGORIES = 6
N_ACTIONS = 4
N_DECISIONS = 3000
SNAPSHOTS = (250, 1500, 3000)
OUTPUT_DIR = Path(__file__).resolve().parent / "charts"


def silhouette(points: np.ndarray, labels: np.ndarray) -> float:
    """Return the mean Euclidean silhouette score without external dependencies."""
    scores: list[float] = []
    for index, point in enumerate(points):
        same = labels == labels[index]
        same[index] = False
        a = float(np.mean(np.linalg.norm(points[same] - point, axis=1)))
        other_means = [
            float(np.mean(np.linalg.norm(points[labels == label] - point, axis=1)))
            for label in np.unique(labels)
            if label != labels[index]
        ]
        b = min(other_means)
        scores.append((b - a) / max(a, b, 1e-12))
    return float(np.mean(scores))


def run_snapshots() -> dict[int, np.ndarray]:
    """Run the archived E-JM-6 compounding arm and capture centroid tensors."""
    rng = np.random.default_rng(SEED)
    raw = rng.exponential(1.0, N_FACTORS)
    true_w = raw / raw.sum()
    noise = 0.20 + 0.25 * (1.0 - true_w / true_w.max())

    centroids = np.zeros((N_CATEGORIES, N_ACTIONS, N_FACTORS))
    counts = np.zeros((N_CATEGORIES, N_ACTIONS), dtype=int)
    dk_weights = np.ones(N_FACTORS) / N_FACTORS
    all_values: list[np.ndarray] = []
    confirmed: list[np.ndarray] = []
    overridden: list[np.ndarray] = []
    person_accuracy = float(rng.uniform(0.60, 0.80))
    captured: dict[int, np.ndarray] = {}

    for decision in range(1, N_DECISIONS + 1):
        category = (decision - 1) % N_CATEGORIES
        action = int(rng.integers(0, N_ACTIONS))
        factors = rng.normal(0, 1, N_FACTORS) * noise + true_w * 1.5

        if counts[category, action] > 10 and len(all_values) > 30:
            weighted = centroids[category, action] * dk_weights
            alignment = float(np.dot(weighted, true_w))
            precision = float(np.dot(dk_weights, true_w))
            probability = person_accuracy * (
                0.50 + 0.35 * float(np.clip(alignment * precision * 5, 0, 1))
            )
        else:
            probability = person_accuracy * 0.50
        correct = bool(rng.random() < np.clip(probability, 0.10, 0.95))

        counts[category, action] += 1
        eta = 0.05 if correct else 0.01
        centroids[category, action] += eta * (factors - centroids[category, action])
        all_values.append(factors)
        (confirmed if correct else overridden).append(factors)

        if len(confirmed) >= 15 and len(overridden) >= 10:
            all_array = np.asarray(all_values)
            confirmed_array = np.asarray(confirmed)
            overridden_array = np.asarray(overridden)
            separation = np.abs(confirmed_array.mean(axis=0) - overridden_array.mean(axis=0))
            pooled = np.sqrt(
                (confirmed_array.var(axis=0, ddof=1) + overridden_array.var(axis=0, ddof=1))
                / 2
                + 1e-6
            )
            combined = separation / pooled / (np.sqrt(all_array.var(axis=0, ddof=1)) + 1e-6)
            dk_weights = combined / (combined.sum() + 1e-8)

        if decision in SNAPSHOTS:
            captured[decision] = centroids.copy()
    return captured


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = run_snapshots()
    late = snapshots[SNAPSHOTS[-1]].reshape(-1, N_FACTORS)
    late_center = late.mean(axis=0)
    _, _, right_vectors = np.linalg.svd(late - late_center, full_matrices=False)
    components = right_vectors[:2]
    action_labels = np.tile(np.arange(N_ACTIONS), N_CATEGORIES)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)
    scores: dict[str, float] = {}
    colors = ("#2563eb", "#f97316", "#16a34a", "#9333ea")
    for axis, decision in zip(axes, SNAPSHOTS):
        flat = snapshots[decision].reshape(-1, N_FACTORS)
        projected = (flat - late_center) @ components.T
        score = silhouette(projected, action_labels)
        scores[str(decision)] = score
        for action in range(N_ACTIONS):
            mask = action_labels == action
            axis.scatter(
                projected[mask, 0], projected[mask, 1], s=42,
                color=colors[action], edgecolor="white", linewidth=0.6,
                label=f"Action {action + 1}", alpha=0.88,
            )
        axis.set_title(f"{decision:,} decisions\nSilhouette = {score:.3f}", fontsize=12)
        axis.set_xlabel("Late-basis PC1")
        axis.grid(True, color="#d1d5db", linewidth=0.6, alpha=0.7)
    axes[0].set_ylabel("Late-basis PC2")
    axes[-1].legend(loc="best", fontsize=8)
    fig.suptitle(
        "FIGURE-2 — E-JM-6 Centroid Geometry Over Time\n"
        "Fixed PCA basis fitted to late centroids; seed 42",
        fontsize=14,
    )
    output = OUTPUT_DIR / "fig2_centroid_geometry.png"
    fig.savefig(output, dpi=300, facecolor="white")
    plt.close(fig)

    differentiated = bool(scores[str(SNAPSHOTS[-1])] >= 0.25)
    payload = {
        "provenance": "ADAPTED snapshot reproduction of archived E-JM-6 algorithm",
        "seed": SEED,
        "snapshots": list(SNAPSHOTS),
        "pca_basis": "fit on late snapshot and applied unchanged to all snapshots",
        "cluster_labels": "action index across six categories",
        "silhouette_scores": scores,
        "centroids_differentiate": differentiated,
    }
    (OUTPUT_DIR / "fig2_centroid_geometry.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
