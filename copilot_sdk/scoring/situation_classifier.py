"""Situation classification for VLD investigation budgets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

SITUATION_BUDGETS = {
    "S1": 0,
    "S2": 3,
    "S3": 1,
    "S4": 2,
    "S5": 3,
    "S6": 4,
}

FEATURE_NAMES = [
    "margin",
    "entropy",
    "q_spread",
    "q_entropy",
    "p_max",
    "p_second",
    "q_max",
    "q_mean",
    "d_min",
    "d_gap",
]


def extract_features(v: Any, mu: Any, sigma: Any, P: Any, Q: Any) -> np.ndarray:
    vector = np.asarray(v, dtype=np.float64)
    centroids = np.asarray(mu, dtype=np.float64)
    sig = np.asarray(sigma, dtype=np.float64)
    probs = np.asarray(P, dtype=np.float64)
    q = np.asarray(Q, dtype=np.float64)
    if centroids.ndim != 2:
        raise ValueError("mu must have shape (actions, factors)")
    if vector.shape != (centroids.shape[1],):
        raise ValueError("v shape must match centroid factor dimension")
    if sig.shape != vector.shape:
        raise ValueError("sigma shape must match v")
    p_sorted = np.sort(probs)[::-1]
    margin = float(p_sorted[0] - p_sorted[1]) if p_sorted.size >= 2 else 1.0
    entropy = -float(np.sum(probs * np.log(np.maximum(probs, 1e-12))))
    q_pos = q[q > 0]
    q_max = float(np.max(q_pos)) if q_pos.size else 0.0
    q_mean = float(np.mean(q_pos)) if q_pos.size else 0.0
    q_spread = float(q_max / max(q_mean, 1e-12)) if q_pos.size else 0.0
    if q_pos.size and float(np.sum(q_pos)) > 0:
        q_norm = q_pos / np.sum(q_pos)
        q_entropy = -float(np.sum(q_norm * np.log(np.maximum(q_norm, 1e-12))))
    else:
        q_entropy = 0.0
    precision = 1.0 / np.maximum(sig**2, 0.001)
    dists = np.sum(precision.reshape(1, -1) * (vector.reshape(1, -1) - centroids) ** 2, axis=1)
    d_sorted = np.sort(dists)
    d_min = float(d_sorted[0]) if d_sorted.size else 0.0
    d_gap = float(d_sorted[1] - d_sorted[0]) if d_sorted.size >= 2 else 0.0
    features: np.ndarray = np.asarray(
        [
            margin,
            entropy,
            q_spread,
            q_entropy,
            float(p_sorted[0]) if p_sorted.size else 0.0,
            float(p_sorted[1]) if p_sorted.size >= 2 else 0.0,
            q_max,
            q_mean,
            d_min,
            d_gap,
        ],
        dtype=np.float64,
    )
    if not np.all(np.isfinite(features)):
        raise ValueError("situation features must be finite")
    return features


@dataclass
class SituationAssessment:
    situation: str
    confidence: float
    recommended_budget: int
    features: dict[str, float]


class SituationClassifier:
    def __init__(self, model_path: str | Path | None = None):
        self._model = None
        self._model_path = Path(model_path) if model_path is not None else None
        if self._model_path is not None and self._model_path.exists():
            import joblib

            self._model = joblib.load(self._model_path)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def classify(
        self,
        v: Any,
        mu: Any,
        sigma: Any,
        P: Any,
        Q: Any,
        default_budget: int = 2,
    ) -> SituationAssessment:
        features_array = extract_features(v, mu, sigma, P, Q)
        feature_map = {name: float(value) for name, value in zip(FEATURE_NAMES, features_array)}
        if self._model is not None:
            pred = str(self._model.predict(features_array.reshape(1, -1))[0])
            confidence = 1.0
            proba = getattr(self._model, "predict_proba", None)
            if callable(proba):
                confidence = float(np.max(proba(features_array.reshape(1, -1))[0]))
            return SituationAssessment(pred, confidence, SITUATION_BUDGETS.get(pred, int(default_budget)), feature_map)
        d_min = feature_map["d_min"]
        if d_min < 0.05:
            situation = "S1"
        elif d_min > 0.5:
            situation = "S6"
        else:
            situation = "S3"
        return SituationAssessment(situation, 0.5, SITUATION_BUDGETS.get(situation, int(default_budget)), feature_map)


__all__ = ["FEATURE_NAMES", "SITUATION_BUDGETS", "SituationAssessment", "SituationClassifier", "extract_features"]
