"""Measure DataOps investigation routing rho against simple baselines."""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, cast

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from copilot_sdk.scoring.presets.dataops import DataOpsPreset

from app.services.investigation_comparators import expected_pattern_category
from app.services.investigation_patterns import FACTOR_NAMES, build_default_investigation_patterns
from app.services.investigation_router import InvestigationRouter


class StaticDataOpsScorer:
    def __init__(self) -> None:
        preset = DataOpsPreset()
        self.centroids = preset.bootstrap_centroids
        self.categories = list(preset.shape.category_names)
        self.actions = list(preset.shape.action_names)
        self.tau = 0.1


def load_alerts(data_dir: Path | None = None) -> list[dict[str, Any]]:
    root = data_dir or BACKEND_ROOT / "data"
    with (root / "fallback" / "alerts.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [dict(row) for row in payload.get("alerts", []) if isinstance(row, dict)]


def measure(data_dir: Path | None = None) -> dict[str, Any]:
    alerts = load_alerts(data_dir)
    patterns = build_default_investigation_patterns(data_dir or BACKEND_ROOT / "data")
    router = InvestigationRouter(patterns)
    scorer = StaticDataOpsScorer()
    expected = [expected_pattern_category(alert) for alert in alerts]
    majority = Counter(expected).most_common(1)[0][0] if expected else "source_failure"
    rng = random.Random(11)
    vld_hits = 0
    majority_hits = 0
    random_hits = 0
    margins: list[float] = []
    for alert, expected_category in zip(alerts, expected):
        vector = _factor_vector(alert)
        route = router.route_decision(vector, scorer, set(), alert_context=alert)
        predicted = route.pattern.category_name if route.pattern is not None else "none"
        vld_hits += int(predicted == expected_category)
        majority_hits += int(majority == expected_category)
        random_hits += int(rng.choice(patterns).category_name == expected_category)
        ordered = sorted(route.cat_distances.values())
        if len(ordered) >= 2:
            margins.append(float(ordered[1] - ordered[0]))
    count = len(alerts)
    return {
        "alerts": count,
        "rho_VLD": round(vld_hits / count, 4) if count else 0.0,
        "rho_majority": round(majority_hits / count, 4) if count else 0.0,
        "rho_random": round(random_hits / count, 4) if count else 0.0,
        "majority_category": majority,
        "rho_SOC_reference": 0.685,
        "margin_distribution": {
            "min": round(min(margins), 4) if margins else 0.0,
            "median": round(float(np.median(margins)), 4) if margins else 0.0,
            "max": round(max(margins), 4) if margins else 0.0,
        },
        "status": "INSUFFICIENT DATA" if count < 10 else "OK",
    }


def _factor_vector(alert: dict[str, Any]) -> np.ndarray:
    raw_factors = alert.get("factors")
    factors = raw_factors if isinstance(raw_factors, dict) else {}
    return cast(np.ndarray, np.asarray([float(factors.get(name, 0.0) or 0.0) for name in FACTOR_NAMES], dtype=np.float64))


if __name__ == "__main__":
    report = measure()
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "OK":
        raise SystemExit(2)
