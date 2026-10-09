#!/usr/bin/env python3
"""
scan_integrity.py — Static + Live integrity scanner for copilot-sdk ecosystem.

Catches mismatches, stale references, standing-rule violations, and live
copilot health issues WITHOUT running pytest. ~10s static, ~5s live.

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
                        ".mypy_cache", ".pytest_cache", "dist", "build", ".next"}
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


def http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any] | None:
    """GET JSON from a local endpoint. Returns None on any error."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return cast(dict[str, Any], payload) if isinstance(payload, dict) else None
    except Exception:
        return None


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
    doc_files = find_files(root, "*.md") + find_files(root, "*.txt") + find_files(root, "*.toml")
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

    # Check for double-prefix bug pattern (conservation/conservation)
    for app_name in required_routers:
        main_py = root / "apps" / app_name / "backend" / "app" / "main.py"
        if main_py.exists():
            hits = grep_in_file(main_py, r"conservation.*conservation|/api/.*api/")
            for lineno, line_text in hits:
                result.findings.append(Finding(
                    category="routers", severity="P1",
                    file=f"apps/{app_name}/backend/app/main.py",
                    line=lineno, message=f"Possible double-prefix in route: {line_text}",
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

    # Collect backend endpoint paths from router files
    backend_endpoints: dict[str, set[str]] = {}  # app_name -> set of paths

    for app_name in ("trading", "purchasing", "dataops"):
        endpoints: set[str] = set()
        app_backend = root / "apps" / app_name / "backend" / "app"
        if not app_backend.exists():
            continue

        for py_file in find_files(app_backend, "*.py"):
            result.scanned_files += 1
            for lineno, line_text in grep_in_file(py_file, r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']'):
                m = re.search(r'["\']([^"\']+)["\']', line_text)
                if m:
                    endpoints.add(m.group(1))

        # Also check SDK routers
        for router_file in find_files(root / "copilot_sdk" / "backend", "*.py"):
            for lineno, line_text in grep_in_file(router_file, r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']'):
                m = re.search(r'["\']([^"\']+)["\']', line_text)
                if m:
                    endpoints.add(m.group(1))

        backend_endpoints[app_name] = endpoints

    # Collect frontend API calls from api.ts files
    for app_name in ("trading", "purchasing", "dataops"):
        api_ts = root / "apps" / app_name / "frontend" / "src" / "api.ts"
        if not api_ts.exists():
            continue

        result.scanned_files += 1
        lines = read_lines(api_ts)
        known_endpoints = backend_endpoints.get(app_name, set())

        for i, line in enumerate(lines, 1):
            # Look for fetch/axios calls with endpoint paths
            m = re.search(r'[`"\'](/api/[^`"\'$]+)[`"\']', line)
            if m:
                path = m.group(1)
                # Strip template literal expressions
                path = re.sub(r'\$\{[^}]+\}', '{param}', path)
                # Normalize path parameters
                path_pattern = re.sub(r'\{[^}]+\}', '{param}', path)

                # Check if any backend endpoint matches
                matched = False
                for ep in known_endpoints:
                    ep_pattern = re.sub(r'\{[^}]+\}', '{param}', ep)
                    if ep_pattern == path_pattern or path_pattern.startswith(ep_pattern):
                        matched = True
                        break

                if not matched and known_endpoints:
                    result.findings.append(Finding(
                        category="parity", severity="P2",
                        file=f"apps/{app_name}/frontend/src/api.ts",
                        line=i,
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
                    category="live", severity="P1",
                    file=f"{name}:{endpoint}",
                    line=0,
                    message=f"{name} endpoint failed: GET {endpoint} returned no data",
                    check="endpoint-failed"
                ))
                continue

            for field_name in required_fields:
                if field_name not in data:
                    result.findings.append(Finding(
                        category="live", severity=severity,
                        file=f"{name}:{endpoint}",
                        line=0,
                        message=f"Missing field '{field_name}' in {endpoint} response",
                        check="missing-response-field"
                    ))

        # --- Conservation-specific deep checks ---
        conservation_url = f"{base_url}/api/conservation/status"
        conservation_data = http_get_json(conservation_url)
        if conservation_data:
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
            if status and status.upper() not in ("GREEN", "YELLOW", "RED", "BOOTSTRAP",
                                                   "UNAVAILABLE"):
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

        # --- Cross-endpoint parity: health vs conservation ---
        health_data = http_get_json(f"{base_url}/api/health")
        if health_data and conservation_data:
            # Both should report consistent phase/alpha
            h_alpha = health_data.get("alpha")
            c_alpha = conservation_data.get("alpha") or conservation_data.get("category_coverage")
            if h_alpha is not None and c_alpha is not None:
                if abs(h_alpha - c_alpha) > 0.001:
                    result.findings.append(Finding(
                        category="live", severity="P1",
                        file=f"{name}:health-vs-conservation",
                        line=0,
                        message=f"Alpha mismatch: /health={h_alpha}, /conservation/status={c_alpha}",
                        check="alpha-parity"
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
                             "standing-rules,parity,e2e,live,all (default: all)")
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
