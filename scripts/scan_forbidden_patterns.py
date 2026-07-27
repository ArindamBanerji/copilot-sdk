"""Classify graph-access patterns and fail only on production violations.

The scanner is intentionally lexical, but it understands the repository's
domain-scoping conventions and reports non-production findings separately.
Exceptions are explicit and rule-specific in the companion TOML allowlist.
"""

from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
import tomllib
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
ALLOWLIST_PATH = ROOT / "docs" / "design" / "age_unification_forbidden_patterns_allowlist.toml"
EXCLUDED_DIRECTORIES = {
    ".git", ".mypy_cache", ".pytest_cache", ".tox", ".venv", "__pycache__",
    "build", "dist", "node_modules", "venv", "graphify-out", "scratch",
}
SCRIPT_DIRECTORY_NAMES = {"scripts", "support"}
PRODUCTION_PATH_PARTS = {"app", "copilot_sdk", "ci_platform", "gae"}


@dataclass(frozen=True)
class PatternRule:
    key: str
    description: str
    pattern: re.Pattern[str]


PATTERN_RULES = (
    PatternRule("neo4j_driver", "direct GraphDatabase.driver", re.compile(r"\bGraphDatabase\.driver\s*\(")),
    PatternRule("psycopg_connect", "direct psycopg.connect", re.compile(r"\bpsycopg\.connect\s*\(")),
    PatternRule("sqlite_graph_store", "SQLiteGraphStore construction", re.compile(r"\bSQLiteGraphStore\s*\(")),
    PatternRule("in_memory_graph_store", "InMemoryGraphStore construction", re.compile(r"\bInMemoryGraphStore\s*\(")),
    PatternRule(
        "graph_environment",
        "direct GRAPH_* environment access",
        re.compile(
            r"\bos\.environ(?:\s*\[\s*['\"]GRAPH_[A-Za-z0-9_]+['\"]\s*\]|"
            r"\.get\s*\(\s*['\"]GRAPH_[A-Za-z0-9_]+['\"]\s*\))"
        ),
    ),
)
DECISION_MATCH = re.compile(r"\bMATCH\s*\(\s*[A-Za-z_]\w*\s*:\s*Decision\b", re.IGNORECASE)


@dataclass(frozen=True)
class AllowlistEntry:
    path: str
    reason: str
    line: int | None = None
    pattern: re.Pattern[str] | None = None


@dataclass(frozen=True)
class AllowlistRule:
    paths: tuple[str, ...] = ()
    files: tuple[AllowlistEntry, ...] = ()
    lines: tuple[AllowlistEntry, ...] = ()
    patterns: tuple[AllowlistEntry, ...] = ()


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    source: str
    category: str
    reason: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        help="Repository directory to scan, relative to the shared workspace (for example copilot-sdk).",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=8,
        metavar="N",
        help="Lines before and after a match used to recognize caller-provided domain scoping (default: 8).",
    )
    return parser.parse_args()


def _entries(raw: object, *, field: str) -> tuple[AllowlistEntry, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"allowlist field {field!r} must be an array")
    result: list[AllowlistEntry] = []
    for item in raw:
        if isinstance(item, str):
            result.append(AllowlistEntry(item, "legacy path allowlist"))
            continue
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError(f"allowlist field {field!r} entries need a path")
        line = item.get("line")
        if line is not None and (not isinstance(line, int) or line < 1):
            raise ValueError(f"allowlist field {field!r} line must be a positive integer")
        regex = item.get("pattern")
        compiled = re.compile(regex) if isinstance(regex, str) else None
        if regex is not None and compiled is None:
            raise ValueError(f"allowlist field {field!r} pattern must be a string")
        result.append(AllowlistEntry(item["path"], str(item.get("reason", "allowlisted exception")), line, compiled))
    return tuple(result)


def load_allowlist() -> dict[str, AllowlistRule]:
    with ALLOWLIST_PATH.open("rb") as handle:
        raw = tomllib.load(handle)
    rules = raw.get("rules")
    if not isinstance(rules, dict):
        raise ValueError(f"{ALLOWLIST_PATH} must contain a [rules] table")

    allowlist: dict[str, AllowlistRule] = {}
    for key, value in rules.items():
        # Preserve the original array-of-paths format for existing users.
        if isinstance(value, list):
            allowlist[key] = AllowlistRule(paths=tuple(value))
            continue
        if not isinstance(value, dict):
            raise ValueError(f"allowlist rule {key!r} must be an array or table")
        paths = value.get("paths", [])
        if not isinstance(paths, list) or not all(isinstance(entry, str) for entry in paths):
            raise ValueError(f"allowlist rule {key!r}.paths must be an array of paths")
        allowlist[key] = AllowlistRule(
            paths=tuple(paths),
            files=_entries(value.get("files"), field=f"{key}.files"),
            lines=_entries(value.get("lines"), field=f"{key}.lines"),
            patterns=_entries(value.get("patterns"), field=f"{key}.patterns"),
        )
    return allowlist


def resolve_scan_root(repo: str | None) -> Path:
    if repo is None:
        return WORKSPACE_ROOT
    candidate = (WORKSPACE_ROOT / repo).resolve()
    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("--repo must stay within the shared workspace") from exc
    if not candidate.is_dir():
        raise ValueError(f"repository does not exist: {candidate}")
    return candidate


def iter_python_files(scan_root: Path) -> Iterable[Path]:
    for directory, subdirectories, filenames in os.walk(scan_root):
        subdirectories[:] = [name for name in subdirectories if name not in EXCLUDED_DIRECTORIES]
        for filename in filenames:
            if filename.endswith(".py"):
                yield Path(directory) / filename


def normalized_path(path: Path) -> str:
    return path.resolve().as_posix()


def is_test_file(path: Path) -> bool:
    path_text = normalized_path(path)
    return path.name == "conftest.py" or path.name.startswith("test_") or "/tests/" in path_text


def is_script_file(path: Path) -> bool:
    path_text = normalized_path(path)
    return (
        any(part in SCRIPT_DIRECTORY_NAMES or part in {"migrate", "demo", "integrity"} for part in path.parts)
        or path.name.endswith("_experiments.py")
        or path.name.startswith("age_smoke")
        or path.name.startswith("demo")
        or path.name == "cli.py"
        or path.name.startswith(("check_", "clean_", "diagnose_", "backfill_", "repro_"))
        or path.name in {"property_audit.py", "exp7_merge.py"}
        or path.name.endswith("_preview.py")
    )


def path_matches(path: Path, entry: str) -> bool:
    path_text = normalized_path(path)
    normalized_entry = entry.strip("/").replace("\\", "/")
    return path_text.endswith(f"/{normalized_entry}") or (
        entry.endswith("/") and f"/{normalized_entry}/" in path_text
    )


def allowlist_match(
    path: Path,
    rule: str,
    line: int,
    source_line_text: str,
    allowlist: dict[str, AllowlistRule],
) -> str | None:
    config = allowlist.get(rule, AllowlistRule())
    if any(path_matches(path, entry) for entry in config.paths):
        return "legacy path allowlist"
    for entry in config.files:
        if path_matches(path, entry.path):
            return entry.reason
    for entry in config.lines:
        if path_matches(path, entry.path) and entry.line == line:
            return entry.reason
    for entry in config.patterns:
        if path_matches(path, entry.path) and entry.pattern and entry.pattern.search(source_line_text):
            return entry.reason
    return None


def classify_path(path: Path) -> str:
    if is_test_file(path):
        return "TEST"
    if is_script_file(path):
        return "SCRIPT"
    if any(part in PRODUCTION_PATH_PARTS for part in path.parts):
        return "PRODUCTION"
    return "SCRIPT"


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def source_line(source: str, line: int) -> str:
    lines = source.splitlines()
    return lines[line - 1].strip() if 0 < line <= len(lines) else ""


def code_only_source(source: str) -> str:
    """Mask comments and string literals while preserving offsets and lines."""
    offsets = [0]
    for match in re.finditer("\n", source):
        offsets.append(match.end())
    masked = list(source)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type not in {tokenize.COMMENT, tokenize.STRING}:
                continue
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            for index in range(start, end):
                if masked[index] != "\n":
                    masked[index] = " "
    except tokenize.TokenError:
        return source
    return "".join(masked)


def docstring_spans(source: str) -> set[tuple[int, int]]:
    """Return line spans occupied by module/class/function docstrings."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    spans: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, (list, tuple)) or not body:
            continue
        first = body[0]
        value = getattr(first, "value", None)
        if isinstance(first, ast.Expr) and isinstance(value, ast.Constant) and isinstance(value.value, str):
            spans.add((first.lineno, getattr(first, "end_lineno", first.lineno)))
    return spans


def line_in_spans(line: int, spans: set[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in spans)


def context_text(source: str, line: int, context_lines: int) -> str:
    lines = source.splitlines()
    start = max(0, line - 1 - context_lines)
    end = min(len(lines), line + context_lines)
    return "\n".join(lines[start:end])


def token_offsets(source: str) -> tuple[list[tokenize.TokenInfo], list[int]]:
    offsets = [0]
    for match in re.finditer("\n", source):
        offsets.append(match.end())
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    return tokens, offsets


def token_offset(token: tokenize.TokenInfo, offsets: list[int]) -> int:
    return offsets[token.start[0] - 1] + token.start[1]


def forward_query_context(source: str, offset: int, max_lines: int = 15) -> str:
    """Read the query continuation after a code-level ``MATCH`` token.

    ``code_only_source`` deliberately masks string literals, so a code-level
    match only contains the leading ``MATCH`` text.  Query clauses commonly
    follow on the next lines; retain those continuation lines for scope
    analysis without reverting to the old broad before/after window.
    """
    lines = source.splitlines(keepends=True)
    line_index = source.count("\n", 0, offset)
    if line_index >= len(lines):
        return source[offset:]

    first_line = source[offset:]
    first_line = first_line[: first_line.find("\n")] if "\n" in first_line else first_line
    result = [first_line]
    base_indent = len(lines[line_index]) - len(lines[line_index].lstrip())
    query_clause = re.compile(
        r"^(?:WHERE|AND|OR|OPTIONAL|MATCH|WITH|RETURN|LIMIT|SET|CREATE|DELETE|"
        r"UNWIND|ORDER|GROUP|HAVING|ON|CALL|YIELD|\)|\}|\]|d\d*\s*\.)\b",
        re.IGNORECASE,
    )
    for candidate in lines[line_index + 1 : line_index + 1 + max_lines]:
        stripped = candidate.strip()
        if not stripped:
            break
        indent = len(candidate) - len(candidate.lstrip())
        if (
            indent > base_indent
            or query_clause.search(stripped)
            or re.search(r"\b(?:d|d1|d2)\s*\.\s*domain\s*=", stripped, re.IGNORECASE)
        ):
            result.append(stripped)
            continue
        break
    return "\n".join(result)


def executable_query_expressions(source: str) -> list[tuple[int, str]]:
    """Extract executable string expressions containing Decision MATCH text.

    Adjacent literals and ``+`` concatenations are kept together. Docstrings
    are excluded using the AST, so prose examples do not become findings.
    """
    tokens, offsets = token_offsets(source)
    docstrings = docstring_spans(source)
    string_token_types = {tokenize.STRING}
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    if fstring_middle is not None:
        string_token_types.add(fstring_middle)
    expressions: list[tuple[int, str]] = []
    for index, token in enumerate(tokens):
        if token.type not in string_token_types or line_in_spans(token.start[0], docstrings):
            continue
        start = token_offset(token, offsets)
        end = token_offset(token, offsets) + len(token.string)
        cursor = index + 1
        while cursor < len(tokens):
            next_token = tokens[cursor]
            if next_token.type in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.DEDENT, tokenize.INDENT}:
                break
            if next_token.type == tokenize.COMMENT:
                cursor += 1
                continue
            between = source[end:token_offset(next_token, offsets)]
            if next_token.type == tokenize.STRING or (next_token.type == tokenize.OP and next_token.string in {"+", "(", ")", "."}) or next_token.type == tokenize.NAME:
                end = token_offset(next_token, offsets) + len(next_token.string)
                cursor += 1
                continue
            if next_token.type == tokenize.NL:
                lookahead = cursor + 1
                while lookahead < len(tokens) and tokens[lookahead].type in {
                    tokenize.NL,
                    tokenize.COMMENT,
                }:
                    lookahead += 1
                if lookahead < len(tokens) and tokens[lookahead].type in string_token_types:
                    cursor += 1
                    continue
            break
        expressions.append((start, source[start:end]))
    return expressions


def enclosing_function_accepts_domain(source: str, line: int) -> bool:
    lines = source.splitlines()
    function_start = line - 1
    while function_start >= 0 and not re.match(r"\s*(?:async\s+)?def\s+", lines[function_start]):
        function_start -= 1
    if function_start >= 0:
        signature_lines: list[str] = []
        for candidate in lines[function_start:min(len(lines), function_start + 32)]:
            signature_lines.append(candidate)
            if re.search(r"\)\s*(?:->[^:]*)?:\s*$", candidate):
                break
        if re.search(r"\bdomain\b", "\n".join(signature_lines)):
            return True
    return False


def function_domain_tainted_names(source: str, line: int) -> set[str]:
    """Track local names derived from a ``domain`` parameter.

    Propagation is AST-based, function-local, and forward-only. This handles
    chains such as ``domain -> clauses -> where_clause -> {where_clause}``
    without treating nearby domain assignments as query scoping.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.lineno <= line <= getattr(node, "end_lineno", node.lineno)
    ]
    if not functions:
        return set()
    function = min(
        functions,
        key=lambda node: getattr(node, "end_lineno", node.lineno) - node.lineno,
    )
    tainted = {"domain"}

    def depends_on_domain(node: ast.AST) -> bool:
        return any(
            isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
            and child.id in tainted
            for child in ast.walk(node)
        )

    nodes = sorted(
        ast.walk(function),
        key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
    )
    for node in nodes:
        if getattr(node, "lineno", 0) > line:
            continue
        if isinstance(node, ast.Assign) and depends_on_domain(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    tainted.add(target.id)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if depends_on_domain(node.value) and isinstance(node.target, ast.Name):
                tainted.add(node.target.id)
        elif isinstance(node, ast.AugAssign) and depends_on_domain(node.value):
            if isinstance(node.target, ast.Name):
                tainted.add(node.target.id)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and isinstance(node.func.value, ast.Name)
            and any(depends_on_domain(arg) for arg in node.args)
        ):
            tainted.add(node.func.value.id)
    return tainted


def caller_injects_domain(source: str, line: int, query_expression: str) -> bool:
    """Return whether this function passes a domain-derived value to its query.

    This is deliberately function-local.  A nearby ``domain = ...`` assignment
    is not enough; the query must interpolate/concatenate ``domain`` itself or
    a local value derived from it (for example ``decision_domain_where``).
    """
    if not enclosing_function_accepts_domain(source, line):
        return False

    lines = source.splitlines()
    function_start = line - 1
    while function_start >= 0 and not re.match(r"\s*(?:async\s+)?def\s+", lines[function_start]):
        function_start -= 1
    if function_start < 0:
        return False

    prior_body = "\n".join(lines[function_start:line])
    derived_names = {
        name
        for name, rhs in re.findall(
            r"\b([A-Za-z_]\w*)\s*=\s*([^\n]+)", prior_body
        )
        if re.search(r"\bdomain\b", rhs, re.IGNORECASE)
    }
    query_names = set(re.findall(r"\{\s*([A-Za-z_]\w*)\s*\}", query_expression))
    if "domain" in query_names or query_names.intersection(derived_names):
        return True
    if re.search(
        r"(?:\+\s*domain\b|\bdomain\s*\+|(?:serialize_for_age|_S)\s*\(\s*domain\b|"
        r"\b(?:domain|domain_literal|domain_where|decision_domain_where)\b)",
        query_expression,
        re.IGNORECASE,
    ):
        return True

    tainted = function_domain_tainted_names(source, line)
    return bool(query_names.intersection(tainted))


def query_scope_reason(query: str) -> str | None:
    if re.search(r"soc_decision_where\s*\(", query, re.IGNORECASE):
        return "SOC domain injected by soc_decision_where()"
    if re.search(r"_d2_where\s*\(\)|<d2(?:-correct)?>", query, re.IGNORECASE):
        return "domain injected by projection predicate"
    if re.search(r"\b(?:d|d1|d2)\s*\.\s*domain\s*=", query, re.IGNORECASE):
        return "literal domain predicate"
    if re.search(
        r"\b[A-Za-z_]\w*\s*\.\s*domain\s*=\s*"
        r"[A-Za-z_]\w*\s*\.\s*domain\b",
        query,
        re.IGNORECASE,
    ):
        return "relational domain equality between Decision aliases"
    if re.search(r"\b(?:d|d1|d2)\s*:\s*Decision\s*\{[^}]*\bdomain\s*:", query, re.IGNORECASE):
        return "domain property on Decision match"
    if re.search(r"\{\s*(?:domain|FRAMEWORK_DOMAIN)\s*\}|\$domain\b", query, re.IGNORECASE):
        return "parameterized domain predicate"
    return None


def scan_pattern_rules(path: Path, source: str, allowlist: dict[str, AllowlistRule]) -> list[Finding]:
    findings: list[Finding] = []
    code_source = code_only_source(source)
    base_category = classify_path(path)
    for rule in PATTERN_RULES:
        search_source = source if rule.key == "graph_environment" else code_source
        for match in rule.pattern.finditer(search_source):
            line = line_number(search_source, match.start())
            text = source_line(source, line)
            reason = allowlist_match(path, rule.key, line, text, allowlist)
            category = base_category if base_category in {"TEST", "SCRIPT"} else ("ALLOWLISTED" if reason else base_category)
            findings.append(Finding(path, line, rule.description, text, category, reason or ""))
    return findings


def scan_unscoped_decision_queries(
    path: Path,
    source: str,
    allowlist: dict[str, AllowlistRule],
    context_lines: int,
) -> list[Finding]:
    findings: list[Finding] = []
    base_category = classify_path(path)
    seen: set[tuple[int, str]] = set()

    # Code-level matches are read from the comment/string-masked source.
    matches: list[tuple[int, str]] = [
        (match.start(), forward_query_context(source, match.start()))
        for match in DECISION_MATCH.finditer(code_only_source(source))
    ]
    # Query strings are separately extracted so executable Cypher is retained
    # while docstrings and prose examples remain excluded.
    for expression_start, expression in executable_query_expressions(source):
        matches.extend(
            (expression_start + match.start(), expression)
            for match in DECISION_MATCH.finditer(expression)
        )

    for offset, query_expression in matches:
        line = line_number(source, offset)
        if source_line(source, line).lstrip().startswith("#"):
            continue
        key = (line, "unscoped Decision query")
        if key in seen:
            continue
        seen.add(key)
        text = source_line(source, line)
        allow_reason = allowlist_match(path, "unscoped_decision_match", line, text, allowlist)
        if allow_reason:
            category = base_category if base_category in {"TEST", "SCRIPT"} else "ALLOWLISTED"
            findings.append(Finding(path, line, key[1], text, category, allow_reason))
            continue
        scope_reason = query_scope_reason(query_expression)
        if scope_reason is None:
            context = context_text(source, line, context_lines)
            if re.search(r"soc_decision_where\s*\(", context, re.IGNORECASE):
                scope_reason = "SOC domain injected by soc_decision_where() in reliable helper context"
            elif re.search(r"_d2_where\s*\(\)", context, re.IGNORECASE):
                scope_reason = "domain injected by _d2_where() in reliable helper context"
        if scope_reason:
            category = "SCOPED"
            findings.append(Finding(path, line, key[1], text, category, scope_reason))
        elif caller_injects_domain(source, line, query_expression):
            findings.append(Finding(path, line, key[1], text, "CALLER_SCOPED", "domain parameter interpolated into query expression"))
        else:
            findings.append(Finding(path, line, key[1], text, base_category))
    return findings


def scan_file(
    path: Path,
    allowlist: dict[str, AllowlistRule],
    context_lines: int,
) -> list[Finding]:
    source = read_source(path)
    return scan_pattern_rules(path, source, allowlist) + scan_unscoped_decision_queries(
        path, source, allowlist, context_lines
    )


def display_path(path: Path) -> str:
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    try:
        args = parse_args()
        if args.context_lines < 0:
            raise ValueError("--context-lines must be non-negative")
        scan_root = resolve_scan_root(args.repo)
        allowlist = load_allowlist()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    findings = [
        finding
        for path in sorted(iter_python_files(scan_root))
        for finding in scan_file(path, allowlist, args.context_lines)
    ]
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
        suffix = f" [{finding.reason}]" if finding.reason else ""
        print(
            f"{finding.category}: {display_path(finding.path)}:{finding.line}: "
            f"{finding.rule}: {finding.source}{suffix}"
        )

    print("SUMMARY:")
    for category in ("PRODUCTION", "TEST", "SCRIPT", "ALLOWLISTED", "SCOPED", "CALLER_SCOPED"):
        print(f"  {category}: {counts.get(category, 0)}")
    production = counts.get("PRODUCTION", 0)
    if production:
        print(f"FAIL: {production} production forbidden graph-access pattern(s) found")
        return 1
    print("PASS: no production forbidden graph-access patterns found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
