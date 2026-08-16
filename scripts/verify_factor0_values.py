"""Compare SOC bootstrap scoring before and after factor-0 proposals.

This is a verification-only tool. It does not import or mutate application
state; the proposed tensor is an in-memory copy of the live bootstrap tensor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

import numpy as np


ACTION_NAMES = ["escalate", "investigate", "suppress", "monitor"]
CATEGORY_NAMES = [
    "credential_access",
    "malware_execution",
    "lateral_movement",
    "data_exfiltration",
    "insider_threat",
    "cloud_infrastructure",
]
FACTOR_NAMES = [
    "privileged_identity_context",
    "asset_criticality",
    "threat_intel_enrichment",
    "pattern_history",
    "time_anomaly",
    "device_trust",
]

SCENARIO_IDENTITY_VALUES = {
    "SOC-CA-01": 0.71, "SOC-CA-02": 0.76, "SOC-CA-03": 0.50,
    "SOC-CA-04": 0.15, "SOC-CA-05": 0.15, "SOC-CA-06": 0.36,
    "SOC-TI-01": 0.50, "SOC-TI-02": 0.76, "SOC-TI-03": 0.50,
    "SOC-TI-04": 0.15, "SOC-TI-05": 0.15, "SOC-TI-06": 0.50,
    "SOC-LM-01": 0.51, "SOC-LM-02": 0.71, "SOC-LM-03": 0.50,
    "SOC-LM-04": 0.15, "SOC-LM-05": 0.15, "SOC-LM-06": 0.36,
    "SOC-DE-01": 0.69, "SOC-DE-02": 0.71, "SOC-DE-03": 0.49,
    "SOC-DE-04": 0.15, "SOC-DE-05": 0.15, "SOC-DE-06": 0.39,
    "SOC-IT-01": 0.61, "SOC-IT-02": 0.49, "SOC-IT-03": 0.50,
    "SOC-IT-04": 0.15, "SOC-IT-05": 0.15, "SOC-IT-06": 0.36,
    "SOC-CI-01": 0.60, "SOC-CI-02": 0.79, "SOC-CI-03": 0.49,
    "SOC-CI-04": 0.55, "SOC-CI-05": 0.50, "SOC-CI-06": 0.34,
}

CENTROID_PRIORS = {
    ("credential_access", "escalate"): 0.75,
    ("credential_access", "investigate"): 0.55,
    ("credential_access", "suppress"): 0.15,
    ("credential_access", "monitor"): 0.35,
    ("malware_execution", "escalate"): 0.70,
    ("malware_execution", "investigate"): 0.50,
    ("malware_execution", "suppress"): 0.15,
    ("malware_execution", "monitor"): 0.35,
    ("lateral_movement", "escalate"): 0.70,
    ("lateral_movement", "investigate"): 0.50,
    ("lateral_movement", "suppress"): 0.15,
    ("lateral_movement", "monitor"): 0.35,
    ("data_exfiltration", "escalate"): 0.70,
    ("data_exfiltration", "investigate"): 0.50,
    ("data_exfiltration", "suppress"): 0.15,
    ("data_exfiltration", "monitor"): 0.35,
    ("insider_threat", "escalate"): 0.75,
    ("insider_threat", "investigate"): 0.55,
    ("insider_threat", "suppress"): 0.15,
    ("insider_threat", "monitor"): 0.35,
    ("cloud_infrastructure", "escalate"): 0.60,
    ("cloud_infrastructure", "investigate"): 0.45,
    ("cloud_infrastructure", "suppress"): 0.30,
    ("cloud_infrastructure", "monitor"): 0.30,
}


def load_inputs() -> tuple[list[dict], np.ndarray]:
    repo_root = Path(__file__).resolve().parents[2]
    scenarios_path = (
        repo_root / "gen-ai-roi-demo-v4-v50" / "backend" / "app" / "data"
        / "soc_eval_scenarios.json"
    )
    backend_path = repo_root / "gen-ai-roi-demo-v4-v50" / "backend"
    sys.path.insert(0, str(backend_path))
    from app.domains.soc.config import SOC_PROFILE_CENTROIDS

    raw = json.loads(scenarios_path.read_text(encoding="utf-8"))
    scenarios = raw if isinstance(raw, list) else raw.get("scenarios", [])
    centroids = np.asarray(SOC_PROFILE_CENTROIDS, dtype=np.float64)
    if len(scenarios) != 36:
        raise ValueError(f"Expected 36 scenarios, got {len(scenarios)}")
    if centroids.shape != (6, 4, 6):
        raise ValueError(f"Expected centroid shape (6, 4, 6), got {centroids.shape}")
    if set(SCENARIO_IDENTITY_VALUES) != {s["scenario_id"] for s in scenarios}:
        raise ValueError("Scenario identity-value map does not match scenario IDs")
    if set(CENTROID_PRIORS) != {
        (category, action)
        for category in CATEGORY_NAMES
        for action in ACTION_NAMES
    }:
        raise ValueError("Centroid prior map is incomplete")
    return scenarios, centroids


def scenario_vector(scenario: dict, factor_zero: float) -> np.ndarray:
    factors = scenario["factors"]
    return cast(
        np.ndarray,
        np.asarray(
        [
            factor_zero,
            factors["asset_criticality"],
            factors["threat_intel_enrichment"],
            factors["pattern_history"],
            factors["time_anomaly"],
            factors["device_trust"],
        ],
            dtype=np.float64,
        ),
    )


def score_scenario(
    factor_vector: np.ndarray,
    centroids: np.ndarray,
    category_index: int,
) -> tuple[int, np.ndarray, float]:
    """Return winner, squared L2 distances, and winner margin."""
    category_centroids = centroids[category_index]
    distances = np.sum((category_centroids - factor_vector) ** 2, axis=1)
    winner = int(np.argmin(distances))
    sorted_distances = np.sort(distances)
    margin = float(sorted_distances[1] - sorted_distances[0])
    return winner, distances, margin


def proposed_centroids(current: np.ndarray) -> np.ndarray:
    result = current.copy()
    for category_index, category in enumerate(CATEGORY_NAMES):
        for action_index, action in enumerate(ACTION_NAMES):
            result[category_index, action_index, 0] = CENTROID_PRIORS[(category, action)]
    return result


def main() -> None:
    scenarios, current = load_inputs()
    proposed = proposed_centroids(current)
    rows: list[dict] = []
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        category_index = int(scenario["category_index"])
        factors = scenario["factors"]
        old_f0 = float(
            factors["privileged_identity_context"]
            if "privileged_identity_context" in factors
            else factors["travel_match"]
        )
        new_f0 = SCENARIO_IDENTITY_VALUES[scenario_id]
        current_result = score_scenario(
            scenario_vector(scenario, old_f0), current, category_index
        )
        proposed_result = score_scenario(
            scenario_vector(scenario, new_f0), proposed, category_index
        )
        current_winner, current_distances, current_margin = current_result
        proposed_winner, proposed_distances, proposed_margin = proposed_result
        expected = int(scenario["expected_action_index"])
        rows.append(
            {
                "scenario_id": scenario_id,
                "category": scenario["category"],
                "expected": ACTION_NAMES[expected],
                "current": ACTION_NAMES[current_winner],
                "proposed": ACTION_NAMES[proposed_winner],
                "status": "FLIP" if current_winner != proposed_winner else "SAME",
                "current_margin": current_margin,
                "proposed_margin": proposed_margin,
                "current_distances": current_distances,
                "proposed_distances": proposed_distances,
                "current_matches_expected": current_winner == expected,
                "proposed_matches_expected": proposed_winner == expected,
                "old_f0": old_f0,
                "new_f0": new_f0,
            }
        )

    lines = [
        "# Factor-0 scorer verification output",
        "",
        "Bootstrap squared-L2 scoring; no application state is mutated.",
        "",
        "| # | Scenario | Category | Expected | Current winner | Proposed winner | Status | Margin (curr) | Margin (prop) |",
        "|---:|---|---|---|---|---|---|---:|---:|",
    ]
    for number, row in enumerate(rows, 1):
        lines.append(
            f"| {number} | {row['scenario_id']} | {row['category']} | "
            f"{row['expected']} | {row['current']} | {row['proposed']} | "
            f"{row['status']} | {row['current_margin']:.6f} | "
            f"{row['proposed_margin']:.6f} |"
        )

    same = sum(row["status"] == "SAME" for row in rows)
    flips = [row for row in rows if row["status"] == "FLIP"]
    to_expected = sum(
        not row["current_matches_expected"] and row["proposed_matches_expected"]
        for row in flips
    )
    from_expected = sum(
        row["current_matches_expected"] and not row["proposed_matches_expected"]
        for row in flips
    )
    neutral = len(flips) - to_expected - from_expected
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"Total: {len(rows)}",
            f"MATCH: {same}",
            f"FLIP: {len(flips)}",
            f"Flips TO expected: {to_expected}",
            f"Flips FROM expected: {from_expected}",
            f"Flips between non-expected: {neutral}",
        ]
    )
    output = "\n".join(lines) + "\n"
    print(output, end="")
    output_path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "design" / "factor0_scorer_verification_v1.md"
    )
    existing_suffix = ""
    if output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        marker = existing.find("\n## Flip analysis")
        if marker >= 0:
            existing_suffix = existing[marker:]
    output_path.write_text(output.rstrip() + existing_suffix + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
