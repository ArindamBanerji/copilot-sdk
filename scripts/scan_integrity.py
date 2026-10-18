#!/usr/bin/env python3
"""
scan_integrity.py — Static + Live integrity scanner for copilot-sdk ecosystem.

Catches mismatches, stale references, standing-rule violations, and live
Catches mismatches, stale references, standing-rule violations, live
copilot health issues, and frontend<>backend endpoint alignment
WITHOUT running pytest. ~10s static, ~5s live, ~3s alignment.

Usage:
    python scan_integrity.py --repo sdk --scope all --check all
    python scan_integrity.py --repo all --check standing-rules
    python scan_integrity.py --repo sdk --check live --ports 8010,8020,8030
    python scan_integrity.py --format json  # for Codex prompt injection

Exit codes: 0 = clean, 1 = findings, 2 = scanner error
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import socket
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, TypedDict, cast


# ─────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    category: str       # paths | imports | routers | standing-rules | parity | e2e | live
    severity: str       # P1 | P2 | P3
    file: str
    line: int
    message: str
    check: str = ""     # which specific check triggered


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    scan_time_ms: int = 0

    @property
    def p1_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "P1")

    @property
    def p2_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "P2")

    @property
    def p3_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "P3")

    @property
    def clean(self) -> bool:
        return len(self.findings) == 0


class StandingRuleCheck(TypedDict):
    name: str
    pattern: str
    files: list[Path]
    severity: str
    message: str


# ─────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────

def find_files(root: Path, pattern: str, exclude_dirs: set[str] | None = None) -> list[Path]:
    """Glob for files, excluding common junk directories."""
    if exclude_dirs is None:
        exclude_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv",
                        ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
                        ".codex_tmp"}
    results = []
    for p in root.rglob(pattern):
        if any(ex in p.parts for ex in exclude_dirs):
            continue
        if p.is_file():
            results.append(p)
    return sorted(results)


def read_lines(path: Path) -> list[str]:
    """Read file lines, return empty list on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def grep_in_file(path: Path, pattern: str, flags: int = 0) -> list[tuple[int, str]]:
    """Return (1-indexed line number, line text) for every match."""
    compiled = re.compile(pattern, flags)
    hits = []
    for i, line in enumerate(read_lines(path), 1):
        if compiled.search(line):
            hits.append((i, line.strip()))
    return hits


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick TCP check."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def http_get_json(url: str, timeout: float = 3.0, retries: int = 3) -> dict[str, Any] | list[Any] | None:
    """GET JSON with retry. Returns parsed JSON (dict or list) or None."""
    import time as _time
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, (dict, list)):
                    return payload
                return None
        except Exception as exc:
            last_err = exc
            if attempt < retries - 1:
                _time.sleep(0.5 * (attempt + 1))
    return None


HTTP_ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


@dataclass
class PythonModuleRoutes:
    path: Path
    tree: ast.Module
    constants: dict[str, str]
    imports: dict[str, tuple[Path, str | None]]
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef]


def _join_url_paths(prefix: str, path: str) -> str:
    """Compose FastAPI mount/router prefixes without changing root semantics."""
    if not prefix:
        return path or "/"
    if not path or path == "/":
        return prefix.rstrip("/") or "/"
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _static_string(node: ast.AST | None, names: dict[str, str]) -> str | None:
    """Resolve strings used in route declarations; retain unknown f-string slots."""
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_string(node.left, names)
        right = _static_string(node.right, names)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                resolved = _static_string(value.value, names)
                parts.append(resolved if resolved is not None else "{param}")
            else:
                return None
        return "".join(parts)
    return None


def _module_name_to_path(root: Path, current: Path, module: str | None, level: int) -> Path:
    if level:
        base = current.parent
        for _ in range(level - 1):
            base = base.parent
        target = base.joinpath(*(module or "").split("."))
    else:
        target = root.joinpath(*(module or "").split("."))
    py_target = target.with_suffix(".py")
    return py_target if py_target.exists() else target / "__init__.py"


def _parse_python_module(root: Path, path: Path) -> PythonModuleRoutes | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return None

    constants: dict[str, str] = {}
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            value_node = node.value
            value = _static_string(value_node, constants)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if value is not None:
                for assignment_target in targets:
                    if isinstance(assignment_target, ast.Name):
                        constants[assignment_target.id] = value

    imports: dict[str, tuple[Path, str | None]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        import_target = _module_name_to_path(root, path, node.module, node.level)
        for alias in node.names:
            local_name = alias.asname or alias.name
            if node.module is None:
                imports[local_name] = (
                    _module_name_to_path(root, path, alias.name, node.level),
                    None,
                )
            else:
                imports[local_name] = (import_target, alias.name)

    return PythonModuleRoutes(path, tree, constants, imports, functions)


def _function_defaults(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    base_names: dict[str, str],
) -> dict[str, str]:
    names = dict(base_names)
    positional = list(function.args.posonlyargs) + list(function.args.args)
    if function.args.defaults:
        for argument, default in zip(positional[-len(function.args.defaults):], function.args.defaults):
            value = _static_string(default, names)
            if value is not None:
                names[argument.arg] = value
    for argument, kw_default in zip(function.args.kwonlyargs, function.args.kw_defaults):
        value = _static_string(kw_default, names) if kw_default is not None else None
        if value is not None:
            names[argument.arg] = value
    return names


def _call_bindings(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
    caller_names: dict[str, str],
) -> dict[str, str]:
    bindings: dict[str, str] = {}
    positional = list(function.args.posonlyargs) + list(function.args.args)
    for argument, value_node in zip(positional, call.args):
        value = _static_string(value_node, caller_names)
        if value is not None:
            bindings[argument.arg] = value
    for keyword in call.keywords:
        if keyword.arg:
            value = _static_string(keyword.value, caller_names)
            if value is not None:
                bindings[keyword.arg] = value
    return bindings


def _router_prefixes(node: ast.AST, names: dict[str, str]) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for child in ast.walk(node):
        if not isinstance(child, (ast.Assign, ast.AnnAssign)):
            continue
        value_node = child.value
        if not isinstance(value_node, ast.Call):
            continue
        func_name = ""
        if isinstance(value_node.func, ast.Name):
            func_name = value_node.func.id
        elif isinstance(value_node.func, ast.Attribute):
            func_name = value_node.func.attr
        if func_name != "APIRouter":
            continue
        prefix = ""
        for keyword in value_node.keywords:
            if keyword.arg == "prefix":
                prefix = _static_string(keyword.value, names) or ""
        targets = child.targets if isinstance(child, ast.Assign) else [child.target]
        for target in targets:
            if isinstance(target, ast.Name):
                prefixes[target.id] = prefix
    return prefixes


def _decorated_routes(node: ast.AST, names: dict[str, str]) -> list[tuple[str, str, int]]:
    prefixes = _router_prefixes(node, names)
    routes: list[tuple[str, str, int]] = []
    for child in ast.walk(node):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in child.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr in HTTP_ROUTE_METHODS
                and decorator.args
            ):
                continue
            path = _static_string(decorator.args[0], names)
            if path is None:
                continue
            receiver = decorator.func.value.id if isinstance(decorator.func.value, ast.Name) else ""
            routes.append((receiver, _join_url_paths(prefixes.get(receiver, ""), path), decorator.lineno))
    return routes


def _resolve_imported_provider(
    module: PythonModuleRoutes,
    expression: ast.AST,
) -> tuple[Path | None, str | None]:
    if isinstance(expression, ast.Name):
        imported = module.imports.get(expression.id)
        if imported:
            return imported
        if expression.id in module.functions:
            return module.path, expression.id
        return None, expression.id
    if isinstance(expression, ast.Attribute) and isinstance(expression.value, ast.Name):
        imported = module.imports.get(expression.value.id)
        if imported:
            return imported[0], expression.attr
    return None, None


def _collect_effective_backend_paths(
    root: Path,
    app_name: str,
    result: ScanResult,
    *,
    max_depth: int = 3,
    composed_routes: list[tuple[str, int | None, Path, int]] | None = None,
) -> set[str]:
    app_backend = root / "apps" / app_name / "backend" / "app"
    source_files = find_files(app_backend, "*.py") + find_files(root / "copilot_sdk" / "backend", "*.py")
    modules: dict[Path, PythonModuleRoutes] = {}
    function_index: dict[str, list[tuple[PythonModuleRoutes, ast.FunctionDef | ast.AsyncFunctionDef]]] = {}
    for source_path in source_files:
        parsed = _parse_python_module(root, source_path)
        if parsed is None:
            continue
        modules[source_path.resolve()] = parsed
        for name, function in parsed.functions.items():
            function_index.setdefault(name, []).append((parsed, function))

    main_path = (app_backend / "main.py").resolve()
    main_module = modules.get(main_path)
    if main_module is None:
        return set()

    endpoints: set[str] = set()
    result.scanned_files += len(find_files(app_backend, "*.py"))

    # Routes declared directly on the FastAPI app live inside create_app.
    for function in main_module.functions.values():
        names = _function_defaults(function, main_module.constants)
        for receiver, route_path, lineno in _decorated_routes(function, names):
            if receiver == "app":
                endpoints.add(route_path)
                if composed_routes is not None:
                    composed_routes.append((route_path, None, main_module.path, lineno))

    def mounted_paths(
        mount_prefix: str,
        route_paths: list[str],
        source_path: Path,
        lineno: int,
    ) -> list[str]:
        prefix = mount_prefix.rstrip("/")
        paths: list[str] = []
        for route_path in route_paths:
            effective_path = _join_url_paths(prefix, route_path)
            paths.append(effective_path)
            if composed_routes is not None:
                boundary_pos = len(prefix) if prefix else None
                composed_routes.append((effective_path, boundary_pos, source_path, lineno))
        return paths

    def provider_routes(
        caller_module: PythonModuleRoutes,
        expression: ast.AST,
        caller_names: dict[str, str],
        depth: int,
        ancestors: frozenset[tuple[Path, str | None]],
    ) -> list[str]:
        if depth > max_depth:
            return []
        call = expression if isinstance(expression, ast.Call) else None
        provider_expr = call.func if call is not None else expression
        target_path, symbol = _resolve_imported_provider(caller_module, provider_expr)
        candidates: list[
            tuple[
                PythonModuleRoutes,
                ast.AST,
                dict[str, str],
                str | None,
            ]
        ] = []
        if target_path is not None:
            target_module = modules.get(target_path.resolve())
            if target_module is not None and symbol in target_module.functions:
                function = target_module.functions[cast(str, symbol)]
                names = _function_defaults(function, target_module.constants)
                if call is not None:
                    names.update(_call_bindings(function, call, caller_names))
                candidates.append((target_module, function, names, None))
            elif target_module is not None and symbol in ("router", None):
                candidates.append((target_module, target_module.tree, target_module.constants, "router"))
        if not candidates and symbol:
            for provider_module, function in function_index.get(symbol, []):
                names = _function_defaults(function, provider_module.constants)
                if call is not None:
                    names.update(_call_bindings(function, call, caller_names))
                candidates.append((provider_module, function, names, None))

        paths: list[str] = []
        for provider_module, scope, names, receiver_filter in candidates:
            candidate_key = (provider_module.path.resolve(), symbol)
            if candidate_key in ancestors:
                continue
            next_ancestors = ancestors | {candidate_key}
            router_prefixes = _router_prefixes(scope, names)
            paths.extend(
                path
                for receiver, path, _ in _decorated_routes(scope, names)
                if receiver_filter is None or receiver == receiver_filter
            )
            if depth >= max_depth:
                continue
            for child in ast.walk(scope):
                if not (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "include_router"
                    and child.args
                ):
                    continue
                child_prefix = ""
                for keyword in child.keywords:
                    if keyword.arg == "prefix":
                        child_prefix = _static_string(keyword.value, names) or ""
                owner = child.func.value.id if isinstance(child.func.value, ast.Name) else ""
                child_prefix = _join_url_paths(router_prefixes.get(owner, ""), child_prefix)
                child_paths = provider_routes(
                    provider_module,
                    child.args[0],
                    names,
                    depth + 1,
                    next_ancestors,
                )
                paths.extend(
                    mounted_paths(child_prefix, child_paths, provider_module.path, child.lineno)
                )
        return paths

    for node in ast.walk(main_module.tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "include_router" and node.args:
            mount_prefix = ""
            for keyword in node.keywords:
                if keyword.arg == "prefix":
                    mount_prefix = _static_string(keyword.value, main_module.constants) or ""
            route_paths = provider_routes(
                main_module,
                node.args[0],
                main_module.constants,
                0,
                frozenset(),
            )
            endpoints.update(mounted_paths(mount_prefix, route_paths, main_module.path, node.lineno))
        func_name = node.func.id if isinstance(node.func, ast.Name) else ""
        if func_name == "mount_self_computation_router":
            for provider_module, function in function_index.get("create_self_computation_router", []):
                names = _function_defaults(function, provider_module.constants)
                for _, route_path, _ in _decorated_routes(function, names):
                    endpoints.add(route_path)

    return endpoints


def _frontend_api_paths(path: Path) -> list[tuple[int, str]]:
    """Extract complete API expressions, including templates and literal concatenation."""
    paths: list[tuple[int, str]] = []
    quote_pattern = re.compile(r'([`"\'])([^`"\']*/api/.*?)\1')
    for lineno, line in enumerate(read_lines(path), 1):
        if "/api/" not in line:
            continue
        match = quote_pattern.search(line)
        if not match:
            continue
        value = match.group(2)
        api_index = value.find("/api/")
        prefix_text = value[:api_index]
        if prefix_text and not re.fullmatch(r"\$\{[^}]+\}", prefix_text):
            continue
        value = value[api_index:]
        remainder = line[match.end():]
        if match.group(1) in ('"', "'") and re.match(r"\s*\+", remainder):
            pieces = [value]
            for piece in re.findall(r'["\']([^"\']*)["\']', remainder):
                pieces.append(piece)
            value = "".join(pieces)
        paths.append((lineno, value))
    return paths


def _normalize_api_path(path: str) -> str:
    path = path.split("?", 1)[0].split("#", 1)[0]
    # Interpolations following a slash are path parameters. Appended
    # interpolations are optional query-string fragments and add no segment.
    path = re.sub(
        r"\$\{[^}]+\}",
        lambda match: "{param}" if match.start() > 0 and path[match.start() - 1] == "/" else "",
        path,
    )
    path = re.sub(r"\$\{.*$", "", path)
    path = re.sub(r"\{[^}]+\}", "{param}", path)
    path = re.sub(r"/{2,}", "/", path)
    return path.rstrip("/") or "/"


def _has_doubled_path_segment(path: str, boundary_pos: int | None = None) -> bool:
    search_pos = 0
    while match := re.search(r"/(api|[A-Za-z0-9_-]+)/\1(?:/|$)", path[search_pos:]):
        match_start = search_pos + match.start()
        match_end = search_pos + match.end()
        repeated_segments_end = match_end - 1 if path[match_end - 1:match_end] == "/" else match_end
        if boundary_pos is None or not (match_start < boundary_pos < repeated_segments_end):
            return True
        search_pos = match_start + 1
    return False


# ─────────────────────────────────────────────────────────────────────
# Category 1: Path / Reference Integrity
# ─────────────────────────────────────────────────────────────────────

def check_paths(root: Path, result: ScanResult) -> None:
    """Detect stale file path references in docs, session state, and test configs."""

    # Stale test paths — known problem patterns
    stale_patterns = {
        r"test_scorer_" r"conservation\.py": "tests/scoring/test_conservation.py",
        r"test_conservation_utils\.py(?!\s*$)": None,  # just flag if file doesn't exist
    }

    # Scan docs/ and tests/ for stale path references
    noisy_dirs = {"docs", ".codex_tmp", "node_modules", "__pycache__"}
    doc_files = find_files(root, "*.md") + find_files(root, "*.txt") + find_files(root, "*.toml")
    doc_files = [
        file_path
        for file_path in doc_files
        if not any(part in noisy_dirs for part in file_path.parts)
    ]
    for doc in doc_files:
        result.scanned_files += 1
        for pattern, correct_path in stale_patterns.items():
            hits = grep_in_file(doc, pattern)
            for lineno, line_text in hits:
                # Skip if this is a comment about the stale path
                if correct_path and correct_path in line_text:
                    continue
                msg = f"Stale path reference: {pattern}"
                if correct_path:
                    msg += f" → should be {correct_path}"
                result.findings.append(Finding(
                    category="paths", severity="P2", file=str(doc.relative_to(root)),
                    line=lineno, message=msg, check="stale-path"
                ))

    # Check that test files referenced in pytest.ini / pyproject.toml exist
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        result.scanned_files += 1
        lines = read_lines(pyproject)
        for i, line in enumerate(lines, 1):
            # Look for testpaths or explicit test file references
            m = re.search(r'tests/\S+\.py', line)
            if m:
                ref_path = root / m.group(0)
                if not ref_path.exists():
                    result.findings.append(Finding(
                        category="paths", severity="P2", file="pyproject.toml",
                        line=i, message=f"Referenced test path does not exist: {m.group(0)}",
                        check="missing-test-path"
                    ))


# ─────────────────────────────────────────────────────────────────────
# Category 2: Import Validation
# ─────────────────────────────────────────────────────────────────────

def check_imports(root: Path, result: ScanResult) -> None:
    """Detect imports of deleted/nonexistent modules and functions."""

    # Known deleted functions/classes — add as refactoring progresses
    deleted_symbols = {
        "_rolling_q_from_counts",  # P1-B: must be removed by F-02 fix
        "_StoreProxy",             # Standing rule: must not exist
    }

    py_files = find_files(root / "copilot_sdk", "*.py") + \
               find_files(root / "tests", "*.py") + \
               find_files(root / "apps", "*.py")

    for py_file in py_files:
        result.scanned_files += 1
        lines = read_lines(py_file)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Strip inline comments before checking
            code_part = stripped.split("#")[0] if "#" in stripped else stripped
            for sym in deleted_symbols:
                if sym in code_part and ("import" in code_part or f"{sym}(" in code_part or f"{sym}." in code_part):
                    result.findings.append(Finding(
                        category="imports", severity="P1",
                        file=str(py_file.relative_to(root)),
                        line=i, message=f"Reference to deleted/forbidden symbol: {sym}",
                        check="deleted-symbol"
                    ))

    # Check for broken relative imports using AST
    for py_file in find_files(root / "copilot_sdk", "*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # Check if the module path resolves relative to root
                if node.module.startswith("copilot_sdk."):
                    mod_path = root / node.module.replace(".", "/")
                    if not (mod_path.with_suffix(".py").exists() or
                            (mod_path / "__init__.py").exists()):
                        result.findings.append(Finding(
                            category="imports", severity="P1",
                            file=str(py_file.relative_to(root)),
                            line=node.lineno,
                            message=f"Import from nonexistent module: {node.module}",
                            check="broken-import"
                        ))


# ─────────────────────────────────────────────────────────────────────
# Category 3: Router Mounting
# ─────────────────────────────────────────────────────────────────────

def check_routers(root: Path, result: ScanResult) -> None:
    """Verify all SDK routers are mounted in every app's main.py."""

    # Required routers for each app (based on session continuation doc)
    required_routers = {
        "trading": ["scoring_router", "conservation_router"],
        "purchasing": ["scoring_router", "conservation_router"],
        "dataops": ["scoring_router", "conservation_router", "evolution_router"],
    }

    for app_name, routers in required_routers.items():
        main_py = root / "apps" / app_name / "backend" / "app" / "main.py"
        if not main_py.exists():
            result.findings.append(Finding(
                category="routers", severity="P1", file=f"apps/{app_name}/backend/app/main.py",
                line=0, message=f"main.py not found for {app_name}",
                check="missing-main"
            ))
            continue

        result.scanned_files += 1
        content = main_py.read_text(encoding="utf-8", errors="replace")

        for router in routers:
            # Check import exists
            has_import = re.search(rf"from\s+.*\s+import\s+.*{router}", content) or \
                         re.search(rf"import\s+.*{router}", content) or \
                         re.search(rf"create_{router}", content)
            # Check mount: include_router or app.mount on a line that references this router
            has_mount = bool(re.search(
                rf"include_router\s*\(.*{router}|app\.mount\s*\(.*{router}|{router}.*include_router|{router}.*app\.mount",
                content, re.DOTALL
            ))

            if not has_import:
                result.findings.append(Finding(
                    category="routers", severity="P1",
                    file=f"apps/{app_name}/backend/app/main.py",
                    line=0, message=f"Router not imported: {router}",
                    check="router-not-imported"
                ))
            elif not has_mount:
                result.findings.append(Finding(
                    category="routers", severity="P1",
                    file=f"apps/{app_name}/backend/app/main.py",
                    line=0, message=f"Router imported but not mounted: {router}",
                    check="router-not-mounted"
                ))

    # Check effective mounted paths while excluding repetition created only by
    # the boundary between an include_router prefix and its child route.
    for app_name in required_routers:
        composed_routes: list[tuple[str, int | None, Path, int]] = []
        _collect_effective_backend_paths(
            root,
            app_name,
            result,
            max_depth=3,
            composed_routes=composed_routes,
        )
        seen: set[tuple[str, int | None, Path, int]] = set()
        for route_path, boundary_pos, source_path, lineno in composed_routes:
            finding_key = (route_path, boundary_pos, source_path, lineno)
            if finding_key in seen:
                continue
            seen.add(finding_key)
            if _has_doubled_path_segment(route_path, boundary_pos):
                try:
                    finding_file = source_path.resolve().relative_to(root.resolve()).as_posix()
                except ValueError:
                    finding_file = source_path.as_posix()
                result.findings.append(Finding(
                    category="routers", severity="P1",
                    file=finding_file,
                    line=lineno, message=f"Possible double-prefix in route: {route_path}",
                    check="double-prefix"
                ))


# ─────────────────────────────────────────────────────────────────────
# Category 4: Standing Rules
# ─────────────────────────────────────────────────────────────────────

def check_standing_rules(root: Path, result: ScanResult) -> None:
    """Enforce architectural standing rules via static grep."""

    checks: list[StandingRuleCheck] = [
        # Rule: No DecisionStore in conservation/SC routers
        {
            "name": "no-decisionstore-in-routers",
            "pattern": r"DecisionStore",
            "files": [
                root / "copilot_sdk" / "backend" / "conservation_router.py",
                root / "copilot_sdk" / "backend" / "self_computation_router.py",
            ],
            "severity": "P1",
            "message": "DecisionStore reference in router (deprecated — use GraphStore)",
        },
        # Rule: No _StoreProxy anywhere
        {
            "name": "no-store-proxy",
            "pattern": r"_StoreProxy",
            "files": find_files(root / "apps", "main.py"),
            "severity": "P1",
            "message": "_StoreProxy must not exist in app main.py",
        },
        # Rule: No module-global _store in SC router
        {
            "name": "no-global-store-sc",
            "pattern": r"^_store\s*=",
            "files": [root / "copilot_sdk" / "backend" / "self_computation_router.py"],
            "severity": "P1",
            "message": "Module-global mutable _store in SC router",
        },
        # Rule: Scorer uses _graph_store exclusively
        {
            "name": "scorer-no-legacy-store",
            "pattern": r"self\._store\.(save_decision|save_outcome|save_centroids|get_decision|count_verified|count_correct)",
            "files": [root / "copilot_sdk" / "scoring" / "scorer.py"],
            "severity": "P1",
            "message": "Scorer uses legacy _store methods instead of _graph_store",
        },
        # Rule: No static JSON for conservation
        {
            "name": "no-static-conservation-json",
            "pattern": r"(open|load|read).*conservation.*\.json|conservation.*static|static.*conservation",
            "files": find_files(root / "copilot_sdk", "*.py"),
            "severity": "P1",
            "message": "Static JSON for conservation data (rule #33: live data only)",
        },
    ]

    for check in checks:
        for fpath in check["files"]:
            if not fpath.exists():
                continue
            result.scanned_files += 1
            hits = grep_in_file(fpath, check["pattern"])
            for lineno, line_text in hits:
                # Skip comments
                if line_text.strip().startswith("#"):
                    continue
                result.findings.append(Finding(
                    category="standing-rules",
                    severity=check["severity"],
                    file=str(fpath.relative_to(root)),
                    line=lineno,
                    message=check["message"],
                    check=check["name"]
                ))

    # S2P-specific: No SOC imports in S2P
    s2p_root = None
    env_s2p = os.environ.get("CLAUDE_S2P")
    if env_s2p and Path(env_s2p).exists():
        s2p_root = Path(env_s2p)
    elif (root.parent / "s2p-copilot").exists():
        s2p_root = root.parent / "s2p-copilot"
    if s2p_root is not None:
        s2p_routers = find_files(s2p_root / "backend" / "app" / "routers", "*.py")
        for fpath in s2p_routers:
            result.scanned_files += 1
            hits = grep_in_file(fpath, r"from\s+app\.domains\.soc|import\s+soc")
            for lineno, line_text in hits:
                if line_text.strip().startswith("#"):
                    continue
                result.findings.append(Finding(
                    category="standing-rules", severity="P1",
                    file=str(fpath.relative_to(s2p_root)),
                    line=lineno,
                    message="SOC import in S2P code (standing rule: no SOC vocab in S2P)",
                    check="no-soc-in-s2p"
                ))


# ─────────────────────────────────────────────────────────────────────
# Category 5: Frontend ↔ Backend Parity
# ─────────────────────────────────────────────────────────────────────

def check_parity(root: Path, result: ScanResult) -> None:
    """Check that frontend API calls match backend route definitions."""

    backend_endpoints: dict[str, set[str]] = {}
    for app_name in ("trading", "purchasing", "dataops"):
        app_backend = root / "apps" / app_name / "backend" / "app"
        if not app_backend.exists():
            continue
        backend_endpoints[app_name] = {
            _normalize_api_path(path)
            for path in _collect_effective_backend_paths(root, app_name, result)
        }

    # Collect frontend API calls from api.ts files
    for app_name in ("trading", "purchasing", "dataops"):
        api_ts = root / "apps" / app_name / "frontend" / "src" / "api.ts"
        if not api_ts.exists():
            continue

        result.scanned_files += 1
        known_endpoints = backend_endpoints.get(app_name, set())
        for lineno, path in _frontend_api_paths(api_ts):
            if _normalize_api_path(path) not in known_endpoints and known_endpoints:
                result.findings.append(Finding(
                    category="parity", severity="P2",
                    file=f"apps/{app_name}/frontend/src/api.ts",
                    line=lineno,
                    message=f"Frontend API path may not match any backend route: {path}",
                    check="api-path-mismatch"
                ))

    # Check port consistency between demo.py and frontend configs
    demo_py = root / "demo.py"
    if demo_py.exists():
        result.scanned_files += 1
        demo_content = demo_py.read_text(encoding="utf-8", errors="replace")

        expected_ports = {
            "trading": {"backend": "8010", "frontend": "5174"},
            "purchasing": {"backend": "8020", "frontend": "5175"},
            "dataops": {"backend": "8030", "frontend": "5176"},
            "s2p": {"backend": "8002", "frontend": "5177"},
        }

        for app_name, ports in expected_ports.items():
            for role, port in ports.items():
                if not re.search(rf"\b{port}\b", demo_content):
                    result.findings.append(Finding(
                        category="parity", severity="P2",
                        file="demo.py",
                        line=0,
                        message=f"Expected {app_name} {role} port {port} not found in demo.py",
                        check="port-mismatch"
                    ))


# ─────────────────────────────────────────────────────────────────────
# Category 6: E2E ↔ Frontend Parity
# ─────────────────────────────────────────────────────────────────────

def check_e2e(root: Path, result: ScanResult) -> None:
    """Check E2E test references match actual frontend structure."""

    e2e_dir = root / "e2e"
    if not e2e_dir.exists():
        return

    # Collect tab names from E2E tests (clickTab calls)
    e2e_tabs: dict[str, list[tuple[Path, int, str]]] = {}  # app -> [(file, line, tab_name)]

    for spec_file in find_files(e2e_dir, "*.spec.ts"):
        result.scanned_files += 1
        app_name = None
        for part in spec_file.parts:
            if part in ("trading", "purchasing", "dataops", "s2p"):
                app_name = part
                break

        if not app_name:
            continue

        for lineno, line_text in grep_in_file(spec_file, r"clickTab\s*\("):
            m = re.search(r'clickTab\s*\(\s*\w+\s*,\s*["\']([^"\']+)["\']', line_text)
            if m:
                tab_name = m.group(1)
                e2e_tabs.setdefault(app_name, []).append((spec_file, lineno, tab_name))

    # Check that tab names appear somewhere in frontend screen files
    for app_name, tabs in e2e_tabs.items():
        screens_dir = root / "apps" / app_name / "frontend" / "src" / "screens"
        if not screens_dir.exists():
            continue

        # Collect all string literals from screen files
        screen_content = ""
        for screen_file in find_files(screens_dir, "*.tsx"):
            result.scanned_files += 1
            screen_content += screen_file.read_text(encoding="utf-8", errors="replace")

        # Also check CopilotShell.tsx for tab definitions
        shell_file = root / "copilot_sdk" / "frontend" / "CopilotShell.tsx"
        if shell_file.exists():
            screen_content += shell_file.read_text(encoding="utf-8", errors="replace")

        for spec_file, lineno, tab_name in tabs:
            if tab_name not in screen_content:
                result.findings.append(Finding(
                    category="e2e", severity="P2",
                    file=str(spec_file.relative_to(root)),
                    line=lineno,
                    message=f"E2E clickTab(\"{tab_name}\") not found in {app_name} frontend",
                    check="tab-name-mismatch"
                ))

    # Check Playwright config port references
    pw_config = e2e_dir / "playwright.config.ts"
    if pw_config.exists():
        result.scanned_files += 1
        pw_content = pw_config.read_text(encoding="utf-8", errors="replace")
        expected_ports = {"5174": "trading", "5175": "purchasing", "5176": "dataops", "5177": "s2p"}
        for port, app_name in expected_ports.items():
            if app_name in pw_content and port not in pw_content:
                result.findings.append(Finding(
                    category="e2e", severity="P2",
                    file="e2e/playwright.config.ts",
                    line=0,
                    message=f"Playwright config references {app_name} but port {port} not found",
                    check="pw-port-mismatch"
                ))



# ─────────────────────────────────────────────────────────────────
# Category 7b: Live Frontend<>Backend Endpoint Alignment
# ─────────────────────────────────────────────────────────────────

def _probe_url_status(url: str, timeout: float = 3.0) -> int | None:
    """Return HTTP status code, or None on connection failure."""
    try:
        req = urllib.request.Request(url, method="GET",
                                    headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


# POST-only paths excluded from GET probing (405 expected, not a finding).
POST_ONLY_PATHS: dict[str, set[str]] = {
    "trading":    {"/api/score", "/api/learn"},
    "purchasing": {"/api/score", "/api/learn"},
    "dataops":    {"/api/score", "/api/learn"},
    "s2p":        {"/api/s2p/score", "/api/s2p/learn"},
}


def check_endpoint_alignment(
    root: Path,
    result: ScanResult,
    ports: list[str] | None = None,
) -> None:
    """Probe every frontend api.ts URL against the live backend.

    For each running copilot:
      1. Extract all /api/... paths from apps/{name}/frontend/src/api.ts
      2. Normalize (strip query params, replace interpolations)
      3. GET each path against localhost:{backend_port}
      4. Report 404s as P2 findings (endpoint missing on backend)

    A 405 (Method Not Allowed) means the route EXISTS but rejects GET.
    That is expected for POST-only endpoints and is NOT a finding.
    """
    copilots_to_check = COPILOT_PORTS
    if ports:
        port_set = {int(p) for p in ports}
        copilots_to_check = {
            name: p for name, p in COPILOT_PORTS.items()
            if p["backend"] in port_set
        }

    for name, port_info in copilots_to_check.items():
        backend_port = port_info["backend"]

        # Skip if backend not running -- check_live already reports this
        if not is_port_open("localhost", backend_port):
            continue

        # Locate api.ts
        api_ts = root / "apps" / name / "frontend" / "src" / "api.ts"
        if not api_ts.exists():
            continue

        result.scanned_files += 1
        base_url = f"http://localhost:{backend_port}"
        post_only = POST_ONLY_PATHS.get(name, set())

        # Extract and deduplicate frontend paths
        raw_paths = _frontend_api_paths(api_ts)
        seen_normalized: dict[str, tuple[int, str]] = {}
        for lineno, raw_path in raw_paths:
            norm = _normalize_api_path(raw_path)
            if norm not in seen_normalized:
                seen_normalized[norm] = (lineno, raw_path)

        for norm_path, (lineno, raw_path) in seen_normalized.items():
            # Skip known POST-only endpoints
            if norm_path in post_only:
                continue

            # Replace {param} placeholders with a safe probe value
            probe_path = norm_path.replace("{param}", "__test__")
            url = f"{base_url}{probe_path}"

            status = _probe_url_status(url)

            if status == 404:
                result.findings.append(Finding(
                    category="live-alignment",
                    severity="P2",
                    file=f"apps/{name}/frontend/src/api.ts",
                    line=lineno,
                    message=(
                        f"{name} frontend calls {raw_path} but backend "
                        f"returns 404 on port {backend_port}"
                    ),
                    check="frontend-backend-404",
                ))
            elif status is None:
                result.findings.append(Finding(
                    category="live-alignment",
                    severity="P3",
                    file=f"apps/{name}/frontend/src/api.ts",
                    line=lineno,
                    message=(
                        f"{name} endpoint probe failed (connection error): "
                        f"{raw_path} on port {backend_port}"
                    ),
                    check="endpoint-probe-error",
                ))
            # 200, 405, 422, 401, 500 = route exists, no finding


# ─────────────────────────────────────────────────────────────────────
# Category 7: Live Copilot Probing
# ─────────────────────────────────────────────────────────────────────

COPILOT_PORTS = {
    "trading":    {"backend": 8010, "frontend": 5174},
    "purchasing": {"backend": 8020, "frontend": 5175},
    "dataops":    {"backend": 8030, "frontend": 5176},
    "s2p":        {"backend": 8002, "frontend": 5177},
}

HEALTH_CHECKS = {
    # endpoint -> (required_fields, severity_if_missing)
    "/api/health": (["phase"], "P2"),
    "/api/conservation/status": (["status"], "P2"),
}

S2P_CHECKS = {
    "/api/s2p/preview/queue": (["exceptions"], "P2"),
    "/api/conservation/status": (["status"], "P2"),
}


def check_live(root: Path, result: ScanResult, ports: list[str] | None = None) -> None:
    """Probe running copilots for health, conservation, and API consistency."""

    copilots_to_check = COPILOT_PORTS
    if ports:
        # Filter to only specified ports
        port_set = {int(p) for p in ports}
        copilots_to_check = {
            name: p for name, p in COPILOT_PORTS.items()
            if p["backend"] in port_set
        }

    for name, port_info in copilots_to_check.items():
        backend_port = port_info["backend"]
        frontend_port = port_info["frontend"]

        # --- Backend liveness ---
        if not is_port_open("localhost", backend_port):
            result.findings.append(Finding(
                category="live", severity="P3",
                file=f"{name}:backend:{backend_port}",
                line=0,
                message=f"{name} backend not running on port {backend_port}",
                check="backend-not-live"
            ))
            continue  # skip further checks for this copilot

        # --- Frontend liveness ---
        if not is_port_open("localhost", frontend_port):
            result.findings.append(Finding(
                category="live", severity="P3",
                file=f"{name}:frontend:{frontend_port}",
                line=0,
                message=f"{name} frontend not running on port {frontend_port}",
                check="frontend-not-live"
            ))

        # --- Health + conservation endpoints ---
        checks = S2P_CHECKS if name == "s2p" else HEALTH_CHECKS
        base_url = f"http://localhost:{backend_port}"

        for endpoint, (required_fields, severity) in checks.items():
            url = f"{base_url}{endpoint}"
            data = http_get_json(url)

            if data is None:
                result.findings.append(Finding(
                    category="live", severity="P2",
                    file=f"{name}:{endpoint}",
                    line=0,
                    message=(
                        f"{name} {endpoint} unreachable after 3 retries — "
                        f"verify server is running on port {backend_port}"
                    ),
                    check="endpoint-failed"
                ))
                continue

            if isinstance(data, dict):
                for field_name in required_fields:
                    if field_name in data:
                        continue
                    result.findings.append(Finding(
                        category="live", severity="P1",
                        file=f"{name}:{endpoint}",
                        line=0,
                        message=(
                            f"{endpoint} responded but missing required key '{field_name}' — "
                            "check router mount"
                        ),
                        check="missing-response-field"
                    ))

        # --- Conservation-specific deep checks ---
        conservation_url = f"{base_url}/api/conservation/status"
        conservation_data = http_get_json(conservation_url)
        if isinstance(conservation_data, dict):
            # Check q is present and not None (rolling-400 must be computed)
            q = conservation_data.get("q")
            if q is None and conservation_data.get("verified_count", 0) > 0:
                result.findings.append(Finding(
                    category="live", severity="P1",
                    file=f"{name}:/api/conservation/status",
                    line=0,
                    message=f"Conservation q is None despite verified_count > 0 (rolling-400 not computed?)",
                    check="conservation-q-null"
                ))

            # Check V (lifetime verified count)
            v = conservation_data.get("verified_count") or conservation_data.get("V")
            if v is not None and v < 0:
                result.findings.append(Finding(
                    category="live", severity="P1",
                    file=f"{name}:/api/conservation/status",
                    line=0,
                    message=f"Conservation V is negative: {v}",
                    check="conservation-v-negative"
                ))

            # Check alpha (category coverage)
            alpha = conservation_data.get("alpha") or conservation_data.get("category_coverage")
            if alpha is not None and not (0.0 <= alpha <= 1.0):
                result.findings.append(Finding(
                    category="live", severity="P1",
                    file=f"{name}:/api/conservation/status",
                    line=0,
                    message=f"Conservation alpha out of range [0,1]: {alpha}",
                    check="conservation-alpha-range"
                ))

            # Check status is a known value
            status = conservation_data.get("status")
            if status and status.upper() not in (
                "GREEN", "AMBER", "YELLOW", "RED", "BOOTSTRAP", "COLD_START",
                "UNAVAILABLE",
            ):
                result.findings.append(Finding(
                    category="live", severity="P2",
                    file=f"{name}:/api/conservation/status",
                    line=0,
                    message=f"Unknown conservation status value: {status}",
                    check="conservation-unknown-status"
                ))

            # Parity: check alpha * q * V >= theta_min when GREEN
            if status and status.upper() == "GREEN" and q is not None and v is not None and alpha is not None:
                signal = alpha * q * v
                theta_min = conservation_data.get("theta_min") or conservation_data.get("threshold")
                if theta_min is not None and signal < theta_min:
                    result.findings.append(Finding(
                        category="live", severity="P1",
                        file=f"{name}:/api/conservation/status",
                        line=0,
                        message=f"Conservation law violation: alpha*q*V={signal:.4f} < theta_min={theta_min:.4f} but status is GREEN",
                        check="conservation-law-violation"
                    ))

        # Health alpha = learning coefficient; conservation alpha = category coverage.
        # Verify each independently.
        health_data = http_get_json(f"{base_url}/api/health")
        if isinstance(health_data, dict):
            h_alpha = health_data.get("alpha")
            if h_alpha is not None and not (0.0 <= h_alpha <= 1.0):
                result.findings.append(Finding(
                    category="live", severity="P1",
                    file=f"{name}:/api/health",
                    line=0,
                    message=f"Health alpha out of range [0,1]: {h_alpha}",
                    check="health-alpha-range"
                ))

        if isinstance(conservation_data, dict):
            c_alpha = conservation_data.get("alpha")
            categories_with_data = conservation_data.get("categories_with_data")
            categories_total = conservation_data.get("categories_total")
            if (
                c_alpha is not None
                and categories_with_data is not None
                and categories_total is not None
                and categories_total > 0
            ):
                expected_alpha = categories_with_data / categories_total
                if abs(c_alpha - expected_alpha) > 0.001:
                    result.findings.append(Finding(
                        category="live", severity="P1",
                        file=f"{name}:/api/conservation/status",
                        line=0,
                        message=(
                            f"Conservation alpha mismatch: alpha={c_alpha}, "
                            f"categories_with_data/categories_total={expected_alpha}"
                        ),
                        check="conservation-alpha-consistency"
                    ))


# ─────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────

CHECK_FUNCTIONS = {
    "paths": check_paths,
    "imports": check_imports,
    "routers": check_routers,
    "standing-rules": check_standing_rules,
    "parity": check_parity,
    "e2e": check_e2e,
}

STATIC_CHECKS = set(CHECK_FUNCTIONS.keys())


def run_scan(
    root: Path,
    checks: set[str],
    ports: list[str] | None = None,
) -> ScanResult:
    """Run selected checks against root directory."""
    import time
    start = time.monotonic()
    result = ScanResult()

    for check_name, check_fn in CHECK_FUNCTIONS.items():
        if check_name in checks or "all" in checks:
            check_fn(root, result)

    if "live" in checks or "all" in checks:
        check_live(root, result, ports)

    if "live" in checks or "alignment" in checks or "all" in checks:
        check_endpoint_alignment(root, result, ports)

    result.scan_time_ms = int((time.monotonic() - start) * 1000)
    return result


def format_text(result: ScanResult) -> str:
    """Human-readable output."""
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"  SCAN INTEGRITY REPORT")
    lines.append(f"  Files scanned: {result.scanned_files}")
    lines.append(f"  Scan time: {result.scan_time_ms}ms")
    lines.append(f"  Findings: {len(result.findings)} "
                 f"(P1={result.p1_count}, P2={result.p2_count}, P3={result.p3_count})")
    lines.append(f"{'='*70}\n")

    if result.clean:
        lines.append("  ✓ CLEAN — no findings.\n")
        return "\n".join(lines)

    # Group by category
    by_category: dict[str, list[Finding]] = {}
    for f in result.findings:
        by_category.setdefault(f.category, []).append(f)

    for cat, findings in sorted(by_category.items()):
        lines.append(f"  [{cat.upper()}]")
        for f in findings:
            marker = {"P1": "✗", "P2": "⚠", "P3": "·"}.get(f.severity, "?")
            loc = f"{f.file}:{f.line}" if f.line > 0 else f.file
            lines.append(f"    {marker} {f.severity} {loc}")
            lines.append(f"      {f.message}")
            if f.check:
                lines.append(f"      check: {f.check}")
        lines.append("")

    verdict = "FAIL" if result.p1_count > 0 else "WARN" if result.p2_count > 0 else "INFO"
    lines.append(f"  VERDICT: {verdict}")
    lines.append(f"{'='*70}\n")
    return "\n".join(lines)


def format_json(result: ScanResult) -> str:
    """JSON output for Codex prompt injection."""
    return json.dumps({
        "scanned_files": result.scanned_files,
        "scan_time_ms": result.scan_time_ms,
        "findings_count": len(result.findings),
        "p1": result.p1_count,
        "p2": result.p2_count,
        "p3": result.p3_count,
        "findings": [asdict(f) for f in result.findings],
        "verdict": "FAIL" if result.p1_count > 0 else
                   "WARN" if result.p2_count > 0 else
                   "CLEAN"
    }, indent=2)


def resolve_repo_root(repo: str, cwd: Path) -> Path:
    """Resolve repo name to directory path."""
    repo_map = {
        "sdk": "copilot-sdk",
        "s2p": "s2p-copilot",
        "ci": "ci-platform",
        "soc": "gen-ai-roi-demo-v4-v50",
        "gae": "graph-attention-engine-v50",
    }

    # Check if cwd is already the repo
    if cwd.name == repo_map.get(repo, repo):
        return cwd

    # Check parent directory
    candidate = cwd.parent / repo_map.get(repo, repo)
    if candidate.exists():
        return candidate

    # Check if we're inside the repo
    if repo_map.get(repo, repo) in str(cwd):
        # Walk up to find it
        p = cwd
        while p != p.parent:
            if p.name == repo_map.get(repo, repo):
                return p
            p = p.parent

    # Check environment variables first (most reliable)
    env_map = {
        "sdk": "CLAUDE_SDK",
        "s2p": "CLAUDE_S2P",
        "ci": "CLAUDE_CI",
        "soc": "CLAUDE_SOC",
        "gae": "CLAUDE_GAE",
    }
    env_var = env_map.get(repo)
    if env_var and os.environ.get(env_var):
        return Path(os.environ[env_var])

    # Windows drive scan (only on Windows)
    if sys.platform == "win32":
        for drive in ("G:", "C:", "D:"):
            for base in ("My Drive/public-files/gen-ai-roi", "repos", "src", "projects"):
                candidate = Path(drive) / base / repo_map.get(repo, repo)
                if candidate.exists():
                    return candidate

    return cwd / repo_map.get(repo, repo)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Static + live integrity scanner for copilot-sdk ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python scan_integrity.py --repo sdk --check all
          python scan_integrity.py --repo sdk --check standing-rules,imports
          python scan_integrity.py --repo all --check paths
          python scan_integrity.py --check live --ports 8010,8020,8030
          python scan_integrity.py --format json > findings.json
        """)
    )
    parser.add_argument("--repo", default="sdk",
                        choices=["sdk", "s2p", "ci", "soc", "gae", "all"],
                        help="Which repo to scan (default: sdk)")
    # --scope reserved for future use (backend/frontend/e2e filtering)
    parser.add_argument("--check", default="all",
                        help="Comma-separated checks: paths,imports,routers,"
                             "standing-rules,parity,e2e,live,alignment,all (default: all)")
    parser.add_argument("--ports", default=None,
                        help="Comma-separated backend ports for live checks "
                             "(default: all known ports)")
    parser.add_argument("--format", default="text", choices=["text", "json"],
                        help="Output format (default: text)")
    parser.add_argument("--root", default=None,
                        help="Explicit repo root path (overrides --repo resolution)")

    args = parser.parse_args()

    checks = set(args.check.split(","))
    ports = args.ports.split(",") if args.ports else None

    # Determine repo roots to scan
    cwd = Path.cwd()
    repos_to_scan = []

    if args.root:
        repos_to_scan.append(Path(args.root))
    elif args.repo == "all":
        for repo_name in ("sdk", "s2p", "ci"):
            root = resolve_repo_root(repo_name, cwd)
            if root.exists():
                repos_to_scan.append(root)
            else:
                print(f"  [SKIP] {repo_name}: root not found at {root}", file=sys.stderr)
    else:
        root = resolve_repo_root(args.repo, cwd)
        repos_to_scan.append(root)

    if not repos_to_scan:
        print("ERROR: No repo roots found. Use --root to specify explicitly.", file=sys.stderr)
        return 2

    # Run scans
    combined = ScanResult()
    for repo_root in repos_to_scan:
        if not repo_root.exists():
            print(f"  [SKIP] {repo_root}: directory not found", file=sys.stderr)
            continue
        print(f"  Scanning {repo_root}...", file=sys.stderr)
        r = run_scan(repo_root, checks, ports)
        combined.findings.extend(r.findings)
        combined.scanned_files += r.scanned_files
        combined.scan_time_ms += r.scan_time_ms

    # Output
    if args.format == "json":
        print(format_json(combined))
    else:
        print(format_text(combined))

    return 1 if combined.findings else 0


if __name__ == "__main__":
    sys.exit(main())
