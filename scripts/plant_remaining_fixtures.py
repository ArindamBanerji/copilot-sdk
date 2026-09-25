"""Place the remaining demo fixtures as explicit, reviewable PLANT inputs.

This script deliberately performs file placement only. The current demo
services do not expose stable write APIs for all six scenarios, so it does not
pretend that writing a fixture automatically mutates a running backend.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURES: dict[str, dict[str, Any]] = {
    "purchasing_drift_pause.json": {
        "fixture_id": "PL-PUR-1",
        "copilot": "purchasing",
        "scenario": "PUR-03",
        "planted": True,
        "injection_mode": "file_placement",
        "decisions": [{"decision": i + 1, "verified_correct": i < 20} for i in range(30)],
        "expected": {"conservation_status": "AMBER", "auto_pause_active": True},
    },
    "purchasing_twin_init.json": {
        "fixture_id": "PL-PUR-2",
        "copilot": "purchasing",
        "scenario": "PUR-05",
        "planted": True,
        "injection_mode": "file_placement",
        "twin": {"initialized": True, "source": "day_zero_profile"},
    },
    "trading_regime_break.json": {
        "fixture_id": "PL-TRD-1",
        "copilot": "trading",
        "scenario": "TRD-02",
        "planted": True,
        "injection_mode": "file_placement",
        "regime_break": {
            "before": "trend",
            "after": "mean_reversion",
            "local_hurst_before": 0.71,
            "local_hurst_after": 0.43,
            "tail_dependence_before": 0.18,
            "tail_dependence_after": 0.39,
        },
    },
    "soc_decision_trace.json": {
        "fixture_id": "PL-MACH-1",
        "copilot": "soc",
        "scenario": "MACH-01",
        "planted": True,
        "injection_mode": "file_placement",
        "alert_id": "demo-fixed-alert",
        "decision_trace": {"read_sequence": ["severity", "identity", "origin"], "confidence": 0.91},
    },
    "soc_recursion_k_delta.json": {
        "fixture_id": "PL-MACH-3",
        "copilot": "soc",
        "scenario": "MACH-03",
        "planted": True,
        "injection_mode": "file_placement",
        "decisions": [
            {"n": 1, "verified": True, "k_entry_changed": True, "first_factor": "identity"},
            {"n": 2, "verified": False, "k_entry_changed": False, "first_factor": "origin"},
        ],
        "expected": {"delta_mu": 0.0, "routing_changed": True},
    },
    "dataops_k14_divergence.json": {
        "fixture_id": "PL-DO-5",
        "copilot": "dataops",
        "scenario": "DO-05",
        "planted": True,
        "injection_mode": "file_placement",
        "surface_assessment": "APPROVE",
        "investigation_assessment": "REJECT",
        "evidence": "Source freshness and lineage checks contradict the surface summary.",
        "k14_note": "Surface labels and investigation labels diverge; judgment requires evidence.",
    },
}


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "data" / "demo_fixtures"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, fixture in FIXTURES.items():
        (destination / filename).write_text(
            json.dumps(fixture, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(f"Placed {len(FIXTURES)} tagged fixtures in {destination}")
    print("Injection mode: file_placement; backend mutation requires a supported API.")


if __name__ == "__main__":
    main()
