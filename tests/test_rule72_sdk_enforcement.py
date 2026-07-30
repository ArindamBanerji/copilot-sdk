"""Rule #72 enforcement for SDK Decision graph access."""

from __future__ import annotations

import ast
from pathlib import Path


PROTOCOL_METHODS = frozenset(
    {
        "write_decision",
        "write_outcome",
        "get_decision",
        "get_decisions",
        "get_all_decisions",
        "get_archived_decisions",
        "get_verified_decisions",
        "count_verified",
        "count_verified_decisions",
        "count_correct",
        "count_decisions",
        "save_centroids",
        "load_latest_centroids",
        "get_centroid_checkpoints",
        "archive_old_decisions",
        "count_archived",
        "close",
        "write_entity_enrichment",
        "read_entity_enrichment",
        "list_entity_enrichments",
        "get_decision_links",
        "query_context",
        "query_similar",
        "generate_decision_id",
        "write_governed_decision",
        "write_observation",
        "append_evidence_receipt",
        "write_conservation_status",
        "write_fingerprint",
        "write_centroid_checkpoint",
        "write_evolution_event",
        "write_transfer_pattern",
        "get_transfer_patterns",
        "get_latest_conservation_statuses",
        "get_iks_trajectory",
        "link_entity",
        "archive_decisions",
        "domain_scoped_reset",
    }
)

# Kept as a named alias for compatibility with callers of this test module.
DECISION_METHODS = PROTOCOL_METHODS | {
    "count_recommended_action",
}

# These methods have an optional domain for compatibility, so the required
# domain argument applies to the enumeration/count methods below.
DOMAIN_REQUIRED = {
    "get_decisions",
    "get_all_decisions",
    "get_verified_decisions",
    "count_verified",
    "count_verified_decisions",
    "count_correct",
    "count_decisions",
    "query_context",
}

DOMAIN_POSITION = {
    "get_decisions": 0,
    "get_all_decisions": 0,
    "get_verified_decisions": 0,
    "count_verified": 0,
    "count_verified_decisions": 0,
    "count_correct": 0,
    "count_decisions": 0,
    "query_context": 2,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative(path: Path) -> str:
    return path.relative_to(_repo_root()).as_posix()


def _has_domain_argument(call: ast.Call, method: str) -> bool:
    if any(keyword.arg == "domain" for keyword in call.keywords):
        return True
    position = DOMAIN_POSITION.get(method)
    return position is not None and len(call.args) > position


def _raw_unscoped_decision_query(call: ast.Call) -> bool:
    if not isinstance(call, ast.Call):
        return False
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "run_query":
        return False
    literals = [
        node.value
        for node in ast.walk(call)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    query_text = " ".join(literals)
    if "Decision" not in query_text:
        return False
    has_scope_expression = "d.domain" in query_text or any(
        isinstance(node, ast.Name) and node.id == "domain_clause"
        for node in ast.walk(call)
    )
    return not has_scope_expression


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

            if isinstance(node, ast.Call) and _raw_unscoped_decision_query(node):
                violations.append(
                    f"{_relative(path)}:{node.lineno}: raw run_query for an "
                    "Decision query has no domain predicate"
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
