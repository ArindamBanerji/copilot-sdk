from __future__ import annotations

import ast
from pathlib import Path


def test_no_literal_green_in_sdk_apps():
    root = Path(__file__).parents[1] / "apps"
    violations: list[str] = []
    for path in root.rglob("*.py"):
        if any(part in {"__pycache__", "tests", "test"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg != "conservation_state":
                    continue
                if isinstance(keyword.value, ast.Constant) and str(keyword.value.value).upper() in {"GREEN", "AMBER", "RED"}:
                    violations.append(f"{path}:{node.lineno}")
    assert violations == [], "literal conservation states: " + ", ".join(violations)
