"""Calibrate DataOpsPreset bootstrap centroids."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SEED = 42
TARGET = 0.52
TOLERANCE = 0.03
MAX_TRIALS = 300

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = REPO_ROOT.parent
GAE_PATH = WORKSPACE / "graph-attention-engine-v50"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if GAE_PATH.exists() and str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

from gae.profile_scorer import ProfileScorer  # noqa: E402
from copilot_sdk.scoring.presets.dataops import DataOpsPreset  # noqa: E402


def load_seed_events() -> list[dict]:
    path = REPO_ROOT / "copilot_sdk.scoring" / "presets" / "dataops_seed.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_base_centroids(preset: DataOpsPreset, events: list[dict]) -> np.ndarray:
    shape = preset.shape
    centroids = np.full(shape.tensor_shape, 0.5, dtype=np.float64)
    grouped: dict[tuple[int, int], list[np.ndarray]] = {}
    for event in events:
        category_index = shape.category_names.index(event["category"])
        action_index = shape.action_names.index(event["action_taken"])
        vector = np.asarray(
            [event["factors"][name] for name in shape.factor_names],
            dtype=np.float64,
        )
        grouped.setdefault((category_index, action_index), []).append(vector)

    for (category_index, action_index), vectors in grouped.items():
        centroids[category_index, action_index, :] = np.mean(vectors, axis=0)
    return centroids


def mean_correct_probability(
    preset: DataOpsPreset,
    centroids: np.ndarray,
    events: list[dict],
) -> float:
    scorer = ProfileScorer(
        mu=centroids,
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    probabilities = []
    for event in events:
        category_index = preset.shape.category_names.index(event["category"])
        action_index = preset.shape.action_names.index(event["action_taken"])
        vector = np.asarray(
            [event["factors"][name] for name in preset.shape.factor_names],
            dtype=np.float64,
        )
        result = scorer.score(vector, category_index)
        probabilities.append(float(result.probabilities[action_index]))
    return float(np.mean(probabilities))


def calibrate() -> dict:
    rng = np.random.default_rng(SEED)
    preset = DataOpsPreset()
    events = load_seed_events()
    base = build_base_centroids(preset, events)
    best_centroids = None
    best_mean = -1.0
    best_scale = 0.0
    best_error = float("inf")

    for trial in range(MAX_TRIALS):
        blend = 0.02 + 0.45 * (trial / max(MAX_TRIALS - 1, 1))
        noise_scale = 0.01 + 0.30 * (trial / max(MAX_TRIALS - 1, 1))
        noise = rng.normal(0.0, noise_scale, size=preset.shape.tensor_shape)
        candidate = np.clip(0.5 + blend * (base - 0.5) + noise, 0.0, 1.0)
        mean_conf = mean_correct_probability(preset, candidate, events)
        error = abs(mean_conf - TARGET)
        if error < best_error:
            best_error = error
            best_centroids = candidate
            best_mean = mean_conf
            best_scale = noise_scale
        if TARGET - TOLERANCE <= mean_conf <= TARGET + TOLERANCE:
            best_centroids = candidate
            best_mean = mean_conf
            best_scale = noise_scale
            break

    if best_centroids is None:
        raise RuntimeError("calibration produced no candidate")

    correct_count = sum(1 for event in events if event["is_correct"])
    return {
        "centroids": best_centroids.tolist(),
        "shape": list(preset.shape.tensor_shape),
        "mean_confidence": round(best_mean, 6),
        "noise_scale": round(best_scale, 6),
        "seed": SEED,
        "pool_size": len(events),
        "event_count": len(events),
        "correct_count": correct_count,
        "incorrect_count": len(events) - correct_count,
    }


def main() -> None:
    result = calibrate()
    output = REPO_ROOT / "copilot_sdk.scoring" / "presets" / "dataops_bootstrap.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "DataOps bootstrap calibrated:",
        f"mean_confidence={result['mean_confidence']}",
        f"noise_scale={result['noise_scale']}",
        f"pool_size={result['pool_size']}",
    )


if __name__ == "__main__":
    main()
