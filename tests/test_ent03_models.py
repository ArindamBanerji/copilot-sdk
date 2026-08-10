"""ENT-03 response-model and B2 naming contract checks."""

from __future__ import annotations

from pathlib import Path
import re

from copilot_sdk.backend.models import (
    ConservationResponse,
    DiagnosticsResponse,
    EvolutionSummaryResponse,
    TransferListResponse,
)


def test_diagnostics_response_model() -> None:
    response = DiagnosticsResponse.model_validate(
        {
            "centroid_distance_to_canonical": 0.12,
            "epsilon_firm": {"status": "GREEN"},
            "iks": 0.91,
            "measurement_state": {"state": "MEASURED", "provenance": "real_measured"},
            "domain": "trading",
        }
    )
    assert response.domain == "trading"


def test_conservation_response_model() -> None:
    response = ConservationResponse.model_validate(
        {
            "status": "GREEN",
            "alpha": 0.8,
            "q": 0.95,
            "verified_count": 20,
            "theta_min": 0.2,
            "signal": 0.7,
            "headroom": 0.5,
            "domain": "dataops",
        }
    )
    assert response.V == 20


def test_evolution_and_transfer_response_models() -> None:
    evolution = EvolutionSummaryResponse.model_validate(
        {
            "domain": "purchasing",
            "evolution_enabled": True,
            "schema_version": 1,
            "inventory": {"active": [], "shadow": []},
            "recent_events": [],
        }
    )
    transfers = TransferListResponse.model_validate({"transfers": [], "total": 0})
    assert evolution.schema_version == 1
    assert transfers.total == 0


def test_no_incorrect_rl_naming() -> None:
    root = Path(__file__).resolve().parents[1]
    patterns = (
        re.compile("no " + "reward function", re.IGNORECASE),
        re.compile("RL-based " + "decision", re.IGNORECASE),
    )
    matches: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".md", ".tsx"}:
            continue
        if any(part in {".git", "__pycache__", "node_modules"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in patterns):
                matches.append(f"{path}:{line_number}: {line.strip()}")
    assert not matches, "Incorrect RL naming remains:\n" + "\n".join(matches)
