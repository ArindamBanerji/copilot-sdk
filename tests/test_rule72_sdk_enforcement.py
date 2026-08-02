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

# Capability checks are intentionally allowed when a component is probing for
# an optional store feature rather than accessing Decision data.  Match the
# checked method, not a source line that will move as files evolve.
ALLOWED_CAPABILITY_CHECKS = frozenset(
    {
        ("copilot_sdk/evolution/ledger.py", "write_evolution_event"),
        ("copilot_sdk/migrate/shadow_scorer.py", "get_verified_decisions"),
        ("copilot_sdk/scoring/persistence_outbox.py", "write_evolution_event"),
        ("copilot_sdk/scoring/scorer.py", "domain_scoped_reset"),
    }
)

# The migration fallback uses the same stable file/method identity.  There
# are currently no active TypeError fallbacks around Decision calls outside
# this migration path, but keeping this separate makes that policy explicit.
ALLOWED_TYPE_ERROR_FALLBACKS = frozenset(
    {
        ("copilot_sdk/migrate/shadow_scorer.py", "get_verified_decisions"),
    }
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _relative(path: Path) -> str:
    try:
        return path.relative_to(_repo_root()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


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


def _is_allowed_getattr(path: Path, method: str) -> bool:
    return (_relative(path), method) in ALLOWED_CAPABILITY_CHECKS


def _is_allowed_type_error(path: Path, methods: set[str]) -> bool:
    relative = _relative(path)
    return any((relative, method) in ALLOWED_TYPE_ERROR_FALLBACKS for method in methods)


def _scan_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in sorted(paths):
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
                        method_name = str(method_arg.value)
                        if not _is_allowed_getattr(path, method_name):
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
                decision_methods = {
                    child.func.attr
                    for child in ast.walk(node)
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr in DECISION_METHODS
                    )
                }
                if decision_methods:
                    for handler in node.handlers:
                        catches_type_error = (
                            isinstance(handler.type, ast.Name)
                            and handler.type.id == "TypeError"
                        )
                        if catches_type_error and not _is_allowed_type_error(path, decision_methods):
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

    return violations


def test_sdk_rule72_decision_access_is_explicitly_domain_aware() -> None:
    violations = _scan_paths(list((_repo_root() / "copilot_sdk").rglob("*.py")))
    assert not violations, "Rule #72 violations:\n" + "\n".join(violations)


def test_allowlist_entries_exist_in_source() -> None:
    entries = ALLOWED_CAPABILITY_CHECKS | ALLOWED_TYPE_ERROR_FALLBACKS
    for relative, method in entries:
        path = _repo_root() / relative
        assert path.is_file(), f"stale Rule #72 allowlist path: {relative}"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        assert any(
            isinstance(node, ast.Constant) and node.value == method
            for node in ast.walk(tree)
        ), f"stale Rule #72 allowlist method: {relative}:{method}"


def test_unallowlisted_capability_check_fails(tmp_path: Path) -> None:
    source_path = tmp_path / "unallowlisted.py"
    source_path.write_text(
        "def check(store):\n    return hasattr(store, 'write_decision')\n",
        encoding="utf-8",
    )

    violations = _scan_paths([source_path])

    assert any("hasattr('write_decision')" in violation for violation in violations)
