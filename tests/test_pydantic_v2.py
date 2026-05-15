"""Guards for Pydantic v2-compatible SDK source."""

from __future__ import annotations

import re
from pathlib import Path


SDK_DIR = Path(__file__).resolve().parents[1] / "copilot_sdk"


def _python_sources() -> list[Path]:
    return sorted(SDK_DIR.rglob("*.py"))


def _source_hits(pattern: str) -> list[str]:
    regex = re.compile(pattern)
    hits: list[str] = []

    for path in _python_sources():
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if regex.search(line):
                hits.append(
                    f"{path.relative_to(SDK_DIR.parent)}:{line_number}: {stripped}"
                )

    return hits


def test_sdk_source_has_no_pydantic_v1_validator_api() -> None:
    hits = _source_hits(
        r"@\s*validator\b|\bfrom\s+pydantic\s+import\s+.*\bvalidator\b"
    )

    assert hits == []


def test_sdk_source_has_no_pydantic_v1_dict_serialization() -> None:
    hits = _source_hits(r"\.dict\(")

    assert hits == []


def test_sdk_source_has_no_pydantic_v1_schema_introspection() -> None:
    hits = _source_hits(r"\.schema\(|\.schema_json\(|__fields__|orm_mode")

    assert hits == []


def test_sdk_source_has_no_inner_config_classes() -> None:
    hits = _source_hits(r"^\s+class\s+Config\s*:")

    assert hits == []
