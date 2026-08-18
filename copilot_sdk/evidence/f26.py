"""F-26 protection for sample values in computed responses."""

from __future__ import annotations

from typing import Any


_METRIC_KEYS = {
    "accuracy",
    "amount",
    "confidence",
    "metric",
    "magnitude",
    "roi",
    "savings",
    "score",
    "value",
}


def _is_sample_marker(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() in {
        "sample",
        "demo_fixture",
        "k3",
    }


def scan_for_sample(response_dict: dict[str, Any]) -> list[str]:
    """Find paths where a sample-scoped response contains a metric value.

    Structural fields such as ``treatment_n`` remain allowed.  A response is
    a violation only when a sample marker scopes a metric-like value, or when
    a metric itself is literally assigned a sample marker.
    """

    violations: list[str] = []

    def visit(value: Any, path: str, sample_scope: bool = False) -> None:
        if isinstance(value, dict):
            local_scope = sample_scope or bool(
                value.get("is_sample_data") is True
                or _is_sample_marker(value.get("provenance"))
                or _is_sample_marker(value.get("source"))
            )
            for key, child in value.items():
                key_text = str(key)
                key_lower = key_text.lower()
                child_path = f"{path}.{key_text}" if path else key_text
                if (
                    local_scope
                    and child is not None
                    and (
                        key_lower in _METRIC_KEYS
                        or key_lower.endswith("_score")
                        or key_lower.endswith("_metric")
                        or key_lower.endswith("_amount")
                        or key_lower.endswith("_value")
                    )
                ):
                    violations.append(child_path)
                elif _is_sample_marker(child) and (
                    key_lower in _METRIC_KEYS
                    or key_lower.endswith("_score")
                    or key_lower.endswith("_metric")
                    or key_lower.endswith("_amount")
                    or key_lower.endswith("_value")
                ):
                    violations.append(child_path)
                visit(child, child_path, local_scope)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]", sample_scope)

    visit(response_dict, "")
    return violations


def assert_no_sample(response_dict: dict[str, Any]) -> None:
    """Raise when F-26 finds a sample value in a computed metric."""

    violations = scan_for_sample(response_dict)
    if violations:
        joined = ", ".join(violations)
        raise ValueError(f"F-26: sample value in computed metric(s): {joined}")
