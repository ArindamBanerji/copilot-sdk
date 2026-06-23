from __future__ import annotations

from typing import Any


def test_no_copilot_returns_sample_in_metrics() -> None:
    """F-26: sample payloads must not carry non-null magnitude/score/metric."""

    payloads = [
        {
            "copilot": "purchasing",
            "provenance": "sample",
            "structure": {"present": True, "treatment_n": 10, "control_n": 10},
        },
        {
            "copilot": "dataops",
            "provenance": "sample",
            "structure": {"present": True, "treatment_n": 10, "control_n": 10},
        },
        {
            "copilot": "s2p",
            "provenance": "sample",
            "structure": {"present": True, "treatment_n": 10, "control_n": 10},
        },
    ]

    for payload in payloads:
        assert _sample_metric_violations(payload) == []


def _sample_metric_violations(value: Any, *, sample_scope: bool = False) -> list[str]:
    if isinstance(value, dict):
        in_sample = sample_scope or value.get("provenance") == "sample"
        violations: list[str] = []
        for key, child in value.items():
            key_lower = str(key).lower()
            if in_sample and child is not None and (
                "magnitude" in key_lower
                or key_lower in {"score", "metric"}
                or key_lower.endswith("_score")
                or key_lower.endswith("_metric")
            ):
                violations.append(key)
            violations.extend(_sample_metric_violations(child, sample_scope=in_sample))
        return violations
    if isinstance(value, list):
        violations = []
        for child in value:
            violations.extend(_sample_metric_violations(child, sample_scope=sample_scope))
        return violations
    return []
