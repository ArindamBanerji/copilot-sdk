from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from copilot_sdk.backend.conservation_utils import compute_conservation_metrics
from copilot_sdk.graph.enrichment import ProvenancedValue
from copilot_sdk.scoring.measurement_state import MeasurementState
from copilot_sdk.scoring.scorer import compute_theta_min


class _Shape:
    n_categories = 4


class _Preset:
    shape = _Shape()
    penalty_ratio = 1.0


class _MetricStore:
    domain = "test"

    def count_verified(self, domain: str) -> int:
        return 20

    def count_correct(self, domain: str) -> int:
        return 15

    def count_verified_decisions(self, domain: str) -> int:
        return 20

    def count_categories_with_n(self, domain: str, n: int) -> int:
        return 2


class _MetricState:
    _preset = _Preset()
    graph_store = _MetricStore()


def test_reference_theta_min_is_not_067() -> None:
    theta = compute_theta_min(0.25, 200)

    assert theta is not None
    assert theta == pytest.approx(0.4706, abs=0.001)
    assert abs(theta - 0.67) > 0.05


def test_theta_min_is_lifecycle_dependent() -> None:
    assert compute_theta_min(0.25, 200) != compute_theta_min(0.10, 200)
    assert compute_theta_min(0.25, 200) != compute_theta_min(0.25, 100)


def test_theta_min_formula_matches_published() -> None:
    assert compute_theta_min(1.0, 1) == pytest.approx(23.53, abs=0.01)
    assert compute_theta_min(0.5, 100) == pytest.approx(23.53 / 50, abs=0.001)


def test_no_hardcoded_theta_floor_in_frontend() -> None:
    hits: list[str] = []
    for path in Path("apps").rglob("*.tsx"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if "0.67" in line and re.search(r"theta|floor|min|conservation", line, re.I):
                hits.append(f"{path}:{line_number}")
    for path in Path("apps").rglob("*.ts"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if "0.67" in line and re.search(r"theta|floor|min|conservation", line, re.I):
                hits.append(f"{path}:{line_number}")

    assert not hits, f"Hardcoded theta floor: {hits}"


def test_conservation_payload_includes_theta_min() -> None:
    payload = compute_conservation_metrics(_MetricState(), domain="test")

    assert "theta_min" in payload
    assert payload["theta_min"] == pytest.approx(compute_theta_min(payload["alpha"], payload["V"]))


def test_measurement_state_has_three_phases() -> None:
    states = {state.value for state in MeasurementState}

    assert {"instrument_validated", "accumulating", "measured"} <= states


def test_enrichment_fixture_cannot_claim_measured() -> None:
    with pytest.raises(ValueError, match="fixture values cannot claim measured=True"):
        ProvenancedValue(
            value=1.0,
            source="fixture",
            provenance_tier="context",
            measured=True,
        )


def test_soc_learning_default_is_true() -> None:
    soc_backend = Path("..") / "gen-ai-roi-demo-v4-v50" / "backend"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.domains.soc.config import LEARNING_ENABLED, is_learning_enabled; "
            "print(LEARNING_ENABLED); print(is_learning_enabled())",
        ],
        cwd=soc_backend,
        env={"PATH": str(Path(sys.executable).parent), "PYTHONPATH": str(soc_backend)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["True", "True"]
    launcher = Path("demo.py").read_text(encoding="utf-8")
    assert "--soc-learning" in launcher
    assert 'env.setdefault("SOC_LEARNING_ENABLED", "true")' in launcher
    assert "/api/soc/learning-health" in launcher


def test_no_user_visible_rl_label_in_frontend() -> None:
    # These are known legacy SOC governance labels; they remain explicitly
    # tracked until the separate naming cleanup removes them from the UI.
    known_legacy_files = {
        "CompoundingTab.tsx",
        "GovernanceTab.tsx",
        "RuntimeEvolutionTab.tsx",
    }
    hits: list[str] = []
    roots = [Path("apps"), Path("..") / "gen-ai-roi-demo-v4-v50" / "frontend"]
    for root in roots:
        for path in root.rglob("*.tsx"):
            for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if re.search(r"\bRL\b|reinforcement learning", line, re.I) and not re.search(
                    r"comment|//|/\*|\*/", line
                ) and path.name not in known_legacy_files:
                    hits.append(f"{path}:{line_number}")

    assert not hits, f"Unallowlisted user-visible RL labels: {hits}"
