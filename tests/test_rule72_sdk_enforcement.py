"""Rule #72 enforcement for SDK Decision graph access."""

from __future__ import annotations

import ast
from pathlib import Path


DECISION_METHODS = {
    "get_decision",
    "get_all_decisions",
    "get_verified_decisions",
    "get_decisions",
    "count_verified",
    "count_verified_decisions",
    "count_correct",
    "count_decisions",
    "count_recommended_action",
    "get_decision_links",
    "query_context",
}

# These methods have an optional domain for compatibility, so the required
# domain argument applies to the enumeration/count methods below.
DOMAIN_REQUIRED = DECISION_METHODS - {"get_decision", "get_decision_links"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative(path: Path) -> str:
    return path.relative_to(_repo_root()).as_posix()


def _has_domain_argument(call: ast.Call, method: str) -> bool:
    if any(keyword.arg == "domain" for keyword in call.keywords):
        return True
    if method == "query_context":
        return len(call.args) >= 3
    return bool(call.args)


def _is_allowed_getattr(path: Path, line: int) -> bool:
    return _relative(path) == "copilot_sdk/migrate/shadow_scorer.py" and 345 <= line <= 360


def _is_allowed_type_error(path: Path, line: int) -> bool:
    relative = _relative(path)
    if relative == "copilot_sdk/migrate/shadow_scorer.py":
        return 345 <= line <= 360
    if relative in {
        "copilot_sdk/scoring/startup_restore.py",
        "copilot_sdk/state/tab_state_cache.py",
    }:
        return True
    return False


def test_sdk_rule72_decision_access_is_explicitly_domain_aware() -> None:
    violations: list[str] = []
    for path in sorted((_repo_root() / "copilot_sdk").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            violations.append(f"{_relative(path)}: syntax error: {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"getattr", "hasattr"} and len(node.args) >= 2:
                    method_arg = node.args[1]
                    if isinstance(method_arg, ast.Constant) and method_arg.value in DECISION_METHODS:
                        if not _is_allowed_getattr(path, node.lineno):
                            violations.append(
                                f"{_relative(path)}:{node.lineno}: "
                                f"{node.func.id}({method_arg.value!r})"
                            )

            if isinstance(node, ast.Try):
                decision_call = any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr in DECISION_METHODS
                    for child in ast.walk(node)
                )
                if decision_call:
                    for handler in node.handlers:
                        catches_type_error = (
                            isinstance(handler.type, ast.Name)
                            and handler.type.id == "TypeError"
                        )
                        if catches_type_error and not _is_allowed_type_error(path, handler.lineno):
                            violations.append(
                                f"{_relative(path)}:{handler.lineno}: "
                                "TypeError compatibility fallback around Decision access"
                            )

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in DOMAIN_REQUIRED
                and not _has_domain_argument(node, node.func.attr)
                and not (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                )
            ):
                violations.append(
                    f"{_relative(path)}:{node.lineno}: "
                    f"{node.func.attr} call has no domain argument"
                )

    assert not violations, "Rule #72 violations:\n" + "\n".join(violations)
