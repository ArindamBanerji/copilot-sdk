#!/usr/bin/env python3
"""
tab_inventory.py — Capture frontend tab structure and API state for all copilots.

Produces:
  docs/tab_inventory.json   (machine-readable)
  docs/tab_inventory.md     (human-readable, for code analysis sessions)
  docs/screenshots/         (optional, with --screenshots flag)

Three modes:
  1. STATIC (default):  Reads frontend .tsx source to extract tab names,
                        screen files, component imports. No execution needed.

  2. API:               Adds endpoint smoke tests (curl each backend).
     --api              Requires backends running.

  3. SCREENSHOTS:       Adds Playwright screenshots of each tab.
     --screenshots      Requires full stack running (demo.py).

Usage:
  cd $CLAUDE_SDK
  python scripts/tab_inventory.py
  python scripts/tab_inventory.py --soc "$env:CLAUDE_SOC"
  python scripts/tab_inventory.py --api
  python scripts/tab_inventory.py --api --screenshots
  python scripts/tab_inventory.py --verbose
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Safety — P1 fix: sanitize names before JS/path interpolation
# ---------------------------------------------------------------------------
_SAFE_NAME_RE = re.compile(r"[^a-z0-9_]")


def _safe_name(s: str) -> str:
    """Sanitize a string for use in file paths and JS interpolation."""
    return _SAFE_NAME_RE.sub("_", s.lower())


# ---------------------------------------------------------------------------
# Copilot definitions — ports match demo.py
# P3 fix: smoke_ids per copilot for parameterized endpoint testing
# ---------------------------------------------------------------------------
COPILOTS = {
    "trading": {
        "accent": "red",
        "backend_port": 8010,
        "frontend_port": 5174,
        "frontend_path": "apps/trading/frontend/src",
        "backend_path": "apps/trading/backend/app",
        "expected_tabs": [
            "Dashboard", "Log Trade", "Analysis",
            "Performance", "Journal", "Trade Detail",
        ],
        "smoke_ids": {"id": "TRD-001", "ticker": "AAPL"},
    },
    "purchasing": {
        "accent": "green",
        "backend_port": 8020,
        "frontend_port": 5175,
        "frontend_path": "apps/purchasing/frontend/src",
        "backend_path": "apps/purchasing/backend/app",
        "expected_tabs": [
            "Dashboard", "Order", "Analysis",
            "Inventory", "Performance",
        ],
        "smoke_ids": {"id": "PUR-001"},
    },
    "dataops": {
        "accent": "purple",
        "backend_port": 8030,
        "frontend_port": 5176,
        "frontend_path": "apps/dataops/frontend/src",
        "backend_path": "apps/dataops/backend/app",
        "expected_tabs": [
            "Dashboard", "Triage", "Insight", "Evidence", "Curve",
        ],
        "smoke_ids": {"id": "DOPS-ALERT-001", "sys": "sap_s4"},
    },
    "s2p": {
        "accent": "amber",
        "backend_port": 8002,
        "frontend_port": 5177,
        "frontend_path": "apps/s2p/frontend/src",
        "backend_path": None,  # separate repo
        "expected_tabs": [
            "Dashboard", "Exception Triage", "Insight",
            "Evidence", "Suppliers", "Performance",
        ],
        "smoke_ids": {"id": "S2P-INV-0001", "invoice_id": "S2P-INV-0001"},
    },
}

# P4 fix: SOC expected_tabs updated — removed "Governance" (not a real tab)
SOC_CONFIG = {
    "accent": "blue",
    "backend_port": 8001,
    "frontend_port": 5173,
    "frontend_path": "frontend/src",
    "backend_path": "backend/app",
    "expected_tabs": [
        "SOC Analytics", "Runtime Evolution", "Alert Triage",
        "Compounding", "Executive Narrative", "S2P Preview",
        "Evidence Room",
    ],
    "smoke_ids": {"id": "SOC-ALERT-001"},
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
TAB_LABEL_RE = re.compile(
    r"""(?:label|title)\s*[:=]\s*['"]([^'"]{2,30})['"]""", re.IGNORECASE
)

SHELL_SCREEN_RE = re.compile(
    r"""name\s*:\s*['"]([^'"]{2,30})['"]""",
)

SCREEN_IMPORT_RE = re.compile(
    r"""import\s+(?:\{\s*)?(\w+)\s*\}?\s+from\s+['"][^'"]*(?:screens|components\/tabs)\/""",
    re.IGNORECASE,
)

COMPONENT_IMPORT_RE = re.compile(
    r"""import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['"](?:\.\.?\/)*components\/""",
    re.IGNORECASE,
)

API_CALL_RE = re.compile(r"""['"`](/api/[a-zA-Z0-9_/\-${}.]+)['"`]""")

FETCH_PATTERN_RE = re.compile(
    r"""(?:fetch|get|post|put|delete|axios)\s*\(\s*[`'"]([^'"`\s]+)""",
    re.IGNORECASE,
)

# P6 fix: context markers — a line must contain one of these to be treated
# as an actual API call site (not a comment, error message, or doc string)
_API_CONTEXT_MARKERS = re.compile(
    r"""fetch|axios|\.get\(|\.post\(|\.put\(|\.delete\(|"""
    r"""request\.|baseUrl|BASE_URL|apiUrl|endpoint|url\s*[=:]""",
    re.IGNORECASE,
)

TAB_NOISE = {
    "mb-4", "px-4", "py-3", "text-sm", "rounded-md", "flex",
    "justify-end", "border", "items-center", "gap-2", "w-full",
    "button", "div", "span", "input", "select", "form",
    "Trading Copilot", "Purchasing Copilot", "DataOps Copilot",
    "S2P Copilot", "SOC Copilot",
}

# Config-array nav (SOC-style)
TAB_ENTRY_RE = re.compile(
    r"""\{[^{}]*?\bid\s*:\s*['"]([a-zA-Z0-9_\-]+)['"][^{}]*?\}""", re.DOTALL
)
TAB_ENTRY_COMPONENT_RE = re.compile(
    r"""\b(?:component|element|screen|Component)\s*:""", re.IGNORECASE
)
TAB_ENTRY_LABEL_RE = re.compile(
    r"""\b(?:label|title|name)\s*:\s*['"]([^'"]{2,40})['"]""", re.IGNORECASE
)
_ACRONYMS = {"s2p", "soc", "roi", "ae", "dk", "vix", "pii", "saml", "kpi", "sap"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_tab_noise(s: str) -> bool:
    """Filter out CSS classes, HTML tags, and app titles."""
    s_stripped = s.strip()
    s_lower = s_stripped.lower()
    if s_lower in {n.lower() for n in TAB_NOISE}:
        return True
    if len(s_stripped) < 2 or len(s_stripped) > 30:
        return True
    # CSS-class heuristics apply ONLY to all-lowercase strings
    if s_stripped == s_lower:
        if re.match(r'^[a-z0-9\-]+\s+[a-z0-9\-]', s_lower):
            return True
        if re.match(r'^[a-z\-]+$', s_stripped) and '-' in s_stripped:
            return True
    return False


def _prettify_id(tab_id: str) -> str:
    """'s2p-preview' -> 'S2P Preview'; 'runtimeEvolution' -> 'Runtime Evolution'."""
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', tab_id)
    s = re.sub(r'[-_]+', ' ', s).strip()
    return ' '.join(
        w.upper() if w.lower() in _ACRONYMS else w.capitalize()
        for w in s.split()
    )


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def _extract_tabs_from_source(text: str) -> list[str]:
    """Extract tab names from App.tsx or similar, with noise filtering.

    P2 fix: merges all strategies instead of returning early from Strategy 0.
    """
    all_candidates: list[str] = []

    # Strategy 0: config-array nav (SOC-style)
    cfg = []
    for m in TAB_ENTRY_RE.finditer(text):
        obj = m.group(0)
        if not TAB_ENTRY_COMPONENT_RE.search(obj):
            continue
        lbl = TAB_ENTRY_LABEL_RE.search(obj)
        cfg.append(lbl.group(1).strip() if lbl else _prettify_id(m.group(1)))
    cfg = [c for c in dict.fromkeys(cfg) if not _is_tab_noise(c)]
    if cfg:
        all_candidates.extend(cfg)

    # Strategy 1: CopilotShell screen configs
    shell_matches = SHELL_SCREEN_RE.findall(text)
    if shell_matches:
        all_candidates.extend(shell_matches)

    # Strategy 2: label/title attributes
    label_matches = TAB_LABEL_RE.findall(text)
    if label_matches:
        all_candidates.extend(label_matches)

    # Strategy 3: screen imports (only if nothing else found)
    if not all_candidates:
        screen_imports = SCREEN_IMPORT_RE.findall(text)
        all_candidates.extend(
            _prettify_id(re.sub(r'(Screen|Tab)$', '', s)) for s in screen_imports
        )

    # Deduplicate preserving order, filter noise
    seen: set[str] = set()
    result: list[str] = []
    for c in all_candidates:
        c = c.strip()
        if c not in seen and not _is_tab_noise(c):
            seen.add(c)
            result.append(c)
    return result


def _extract_components(text: str) -> list[str]:
    """Extract imported component names from a TSX file."""
    components = []
    for m in COMPONENT_IMPORT_RE.finditer(text):
        if m.group(1):
            components.extend(c.strip() for c in m.group(1).split(",") if c.strip())
        if m.group(2):
            components.append(m.group(2).strip())
    return components


def _extract_api_calls(text: str, context_filter: bool = True) -> set[str]:
    """Extract API endpoint paths from source text.

    P6 fix: when context_filter=True (default), only includes paths from
    lines that also contain a fetch/axios/request marker — filters out
    comments, error messages, and documentation strings.
    """
    apis: set[str] = set()
    lines = text.splitlines()

    for line in lines:
        line_apis = API_CALL_RE.findall(line)
        if not line_apis:
            continue

        if context_filter and not _API_CONTEXT_MARKERS.search(line):
            # Also accept const/let/var assignments (URL definitions)
            if not re.match(r'^\s*(?:const|let|var|export)\s+\w+\s*=', line):
                continue

        apis.update(line_apis)

    # Fetch/axios patterns
    for m in FETCH_PATTERN_RE.finditer(text):
        path = m.group(1)
        if path.startswith("/api/"):
            apis.add(path)

    # Clean up template literal fragments
    cleaned: set[str] = set()
    for api in apis:
        clean = re.sub(r'\$\{[^}]*\}', '{id}', api)
        cleaned.add(clean)
    return cleaned


# ---------------------------------------------------------------------------
# P5 fix: tab validation — expected vs detected
# ---------------------------------------------------------------------------
def _validate_tabs(
    detected: list[str], expected: list[str]
) -> list[dict[str, str]]:
    """Compare detected tabs against expected tabs. Returns list of warnings."""
    warnings: list[dict[str, str]] = []
    expected_set = {t.lower() for t in expected}
    detected_set = {t.lower() for t in detected}

    for t in expected:
        if t.lower() not in detected_set:
            warnings.append({
                "level": "WARN",
                "message": f"Expected tab not detected: '{t}'",
            })
    for t in detected:
        if t.lower() not in expected_set:
            warnings.append({
                "level": "INFO",
                "message": f"Detected tab not in expected list: '{t}'",
            })
    return warnings


# ---------------------------------------------------------------------------
# Static scan
# ---------------------------------------------------------------------------
def scan_frontend_static(fe_base: Path, copilot: str, config: dict) -> dict:
    """Static analysis of frontend source files."""
    result = {
        "copilot": copilot,
        "accent": config["accent"],
        "frontend_port": config["frontend_port"],
        "backend_port": config["backend_port"],
        "screens": [],
        "components": [],
        "api_calls": [],
        "tab_names": [],
        "tsx_file_count": 0,
        "warnings": [],
    }

    if not fe_base.exists():
        result["error"] = f"Frontend path not found: {fe_base}"
        return result

    tsx_files = [
        f for f in fe_base.rglob("*.tsx")
        if "node_modules" not in str(f)
    ]
    result["tsx_file_count"] = len(tsx_files)

    # Find screen/tab files
    screen_dirs = [
        fe_base / "screens",
        fe_base / "components" / "tabs",
    ]
    for screens_dir in screen_dirs:
        if not screens_dir.exists():
            continue
        for f in sorted(screens_dir.iterdir()):
            if f.suffix == ".tsx":
                text = f.read_text(encoding="utf-8", errors="replace")
                components = _extract_components(text)
                apis = _extract_api_calls(text)
                result["screens"].append({
                    "file": f.name,
                    "lines": text.count("\n") + 1,
                    "components": components[:15],
                    "api_calls": sorted(apis),
                })

    # Extract tab names from App.tsx or main entry
    for app_file_name in ["App.tsx", "app.tsx", "main.tsx", "index.tsx"]:
        app_file = fe_base / app_file_name
        if app_file.exists():
            text = app_file.read_text(encoding="utf-8", errors="replace")
            tabs = _extract_tabs_from_source(text)
            if tabs:
                result["tab_names"] = tabs
                break

    # Fallback: derive from screen/tab file names
    if not result["tab_names"] and result["screens"]:
        result["tab_names"] = [
            _prettify_id(
                s["file"]
                .replace("Screen.tsx", "")
                .replace("Tab.tsx", "")
                .replace(".tsx", "")
            )
            for s in result["screens"]
        ]

    # P5: Validate detected vs expected
    expected = config.get("expected_tabs", [])
    if expected:
        result["warnings"] = _validate_tabs(result["tab_names"], expected)

    # Component files
    components_dir = fe_base / "components"
    if components_dir.exists():
        for f in sorted(components_dir.rglob("*.tsx")):
            rel = str(f.relative_to(fe_base))
            if "node_modules" not in rel:
                result["components"].append(rel)

    # Collect ALL API paths
    all_apis: set[str] = set()
    for tsx in tsx_files:
        try:
            text = tsx.read_text(encoding="utf-8", errors="replace")
            all_apis.update(_extract_api_calls(text))
        except Exception:
            pass

    # .ts config files get relaxed filtering (they ARE the URL definitions)
    for ts in fe_base.rglob("*.ts"):
        if "node_modules" in str(ts) or ts.suffix == ".tsx":
            continue
        try:
            text = ts.read_text(encoding="utf-8", errors="replace")
            all_apis.update(_extract_api_calls(text, context_filter=False))
        except Exception:
            pass

    result["api_calls"] = sorted(all_apis)
    return result


# ---------------------------------------------------------------------------
# P3 fix: smoke ID substitution for parameterized paths
# ---------------------------------------------------------------------------
def _substitute_smoke_ids(path: str, smoke_ids: dict[str, str]) -> str | None:
    """Replace template placeholders with default smoke IDs.

    Returns substituted path, or None if a required placeholder has no mapping.
    """
    if "{" not in path:
        return path

    result = path
    for placeholder in re.findall(r'\{(\w+)\}', path):
        value = smoke_ids.get(placeholder)
        if value:
            result = result.replace(f"{{{placeholder}}}", value)

    if "{" in result:
        return None
    return result


def smoke_test_api(
    port: int, paths: list[str], smoke_ids: dict[str, str] | None = None
) -> dict:
    """Hit backend endpoints and record status codes."""
    import urllib.request
    import urllib.error

    smoke_ids = smoke_ids or {}
    results = {}

    for path in paths:
        actual_path = _substitute_smoke_ids(path, smoke_ids)
        if actual_path is None:
            results[path] = "SKIP (no ID mapping)"
            continue

        url = f"http://127.0.0.1:{port}{actual_path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                results[path] = resp.status
        except urllib.error.HTTPError as e:
            results[path] = e.code
        except Exception as e:
            results[path] = f"ERR: {type(e).__name__}"

    return results


# ---------------------------------------------------------------------------
# P7 fix: improved timeout message
# ---------------------------------------------------------------------------
def check_playwright_available() -> tuple[bool, str]:
    """Preflight: is 'playwright' npm package resolvable?"""
    try:
        r = subprocess.run(
            ["node", "-e", "require.resolve('playwright')"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return True, ""
        return False, (r.stderr or r.stdout or "").strip()
    except FileNotFoundError:
        return False, "'node' not found on PATH (install Node.js)."
    except subprocess.TimeoutExpired:
        return False, (
            "node preflight timed out (30s). This can happen on first run "
            "if antivirus is scanning node_modules. Try running again."
        )


# ---------------------------------------------------------------------------
# Screenshots — P1 fix: all names sanitized before JS interpolation
# ---------------------------------------------------------------------------
def take_screenshots(copilot: str, port: int, tabs: list[str], out_dir: Path):
    """Use Playwright to screenshot each tab. Returns list of saved paths."""
    saved = []
    copilot_safe = _safe_name(copilot)
    out_posix = out_dir.resolve().as_posix()

    # Pre-compute tab filenames in Python — no raw string interpolation in JS
    tab_entries = []
    for tab in tabs:
        safe_tab = _safe_name(tab)
        tab_entries.append({
            "label": tab,
            "filename": f"{copilot_safe}_{safe_tab}.png",
        })

    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const OUT = {json.dumps(out_posix)};
    const browser = await chromium.launch();
    const page = await browser.newPage({{ viewport: {{ width: 1280, height: 900 }} }});
    await page.goto('http://127.0.0.1:{port}', {{ waitUntil: 'networkidle', timeout: 15000 }});
    await page.waitForTimeout(2000);

    // Screenshot initial state
    await page.screenshot({{ path: OUT + '/{copilot_safe}_initial.png', fullPage: false }});

    // Click each tab and screenshot
    const tabs = {json.dumps(tab_entries)};
    for (const tab of tabs) {{
        try {{
            const el = await page.getByRole('tab', {{ name: tab.label }}).or(
                page.getByText(tab.label, {{ exact: false }})
            ).first();
            if (el) {{
                await el.click();
                await page.waitForTimeout(1500);
                await page.screenshot({{ path: OUT + '/' + tab.filename, fullPage: false }});
            }}
        }} catch (e) {{
            console.error('Tab not found:', tab.label, e.message);
        }}
    }}
    await browser.close();
}})();
"""
    script_path = out_dir / f"_capture_{copilot_safe}.js"
    script_path.write_text(script)

    env = dict(os.environ)
    node_modules = os.path.join(os.getcwd(), "node_modules")
    env["NODE_PATH"] = node_modules + os.pathsep + env.get("NODE_PATH", "")

    try:
        r = subprocess.run(
            ["node", str(script_path)],
            capture_output=True, text=True, timeout=60, env=env,
        )
        if r.returncode != 0:
            print(f"  Screenshot node exited {r.returncode} for {copilot}:")
            print("   ", (r.stderr or r.stdout or "").strip()[:600])
        for png in sorted(out_dir.glob(f"{copilot_safe}_*.png")):
            saved.append(str(png))
        if not saved:
            err = (r.stderr or "").strip()
            print(f"  No screenshots written for {copilot}.")
            if err:
                print("    node stderr:", err[:600])
            else:
                print(
                    "    (node exited 0, no error — check the page actually loaded; "
                    "PNGs target: " + out_posix + ")"
                )
    except FileNotFoundError:
        print("  'node' not on PATH — install Node.js or omit --screenshots.")
    except subprocess.TimeoutExpired:
        print(f"  Screenshot timed out for {copilot} (page never reached networkidle).")
    finally:
        script_path.unlink(missing_ok=True)
    return saved


# ---------------------------------------------------------------------------
# Markdown output — P7 fix: --verbose flag controls component detail
# ---------------------------------------------------------------------------
def generate_markdown(inventory: dict, verbose: bool = False) -> str:
    """Generate human-readable markdown."""
    lines = [
        "# Frontend Tab Inventory",
        f"**Generated:** {inventory['generated']}",
        f"**Mode:** {inventory['mode']}",
        "",
        "---",
        "",
    ]

    for cop in inventory["copilots"]:
        name = cop["copilot"].upper()
        lines.append(f"## {name} (port {cop['frontend_port']}/{cop['backend_port']})")
        lines.append(f"**Accent:** {cop['accent']} | **TSX files:** {cop['tsx_file_count']}")
        lines.append("")

        if cop.get("error"):
            lines.append(f"**ERROR:** {cop['error']}")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Tabs
        if cop["tab_names"]:
            lines.append(f"**Tabs ({len(cop['tab_names'])}):** {', '.join(cop['tab_names'])}")
        else:
            lines.append("**Tabs:** Could not detect (check App.tsx manually)")
        lines.append("")

        # P5: Warnings
        if cop.get("warnings"):
            lines.append("### Tab Validation")
            for w in cop["warnings"]:
                icon = "\u26a0\ufe0f" if w["level"] == "WARN" else "\u2139\ufe0f"
                lines.append(f"- {icon} {w['message']}")
            lines.append("")

        # Screens
        if cop["screens"]:
            lines.append("### Screens")
            lines.append("| File | Lines | Components | API Calls |")
            lines.append("|---|---:|---|---|")
            for s in cop["screens"]:
                comps = ", ".join(s["components"][:5])
                if len(s["components"]) > 5:
                    comps += f" +{len(s['components']) - 5}"
                apis = ", ".join(s["api_calls"][:3])
                if len(s["api_calls"]) > 3:
                    apis += f" +{len(s['api_calls']) - 3}"
                lines.append(
                    f"| `{s['file']}` | {s['lines']} | {comps} | {apis} |"
                )
            lines.append("")

        # Components — verbose shows file list, compact shows count only
        if cop["components"]:
            if verbose:
                lines.append(f"### Component Files ({len(cop['components'])})")
                for c in cop["components"][:30]:
                    lines.append(f"- `{c}`")
                if len(cop["components"]) > 30:
                    lines.append(f"- ... +{len(cop['components']) - 30} more")
            else:
                lines.append(f"**Components:** {len(cop['components'])} files")
            lines.append("")

        # API calls
        if cop["api_calls"]:
            lines.append(f"### API Calls Referenced ({len(cop['api_calls'])})")
            for api in cop["api_calls"]:
                lines.append(f"- `{api}`")
            lines.append("")

        # Smoke results
        if cop.get("smoke_results"):
            lines.append("### Endpoint Smoke")
            ok = sum(1 for s in cop["smoke_results"].values() if s == 200)
            total = len(cop["smoke_results"])
            lines.append(f"**{ok}/{total} returned 200**")
            lines.append("")
            lines.append("| Path | Status |")
            lines.append("|---|---|")
            for path, status in sorted(cop["smoke_results"].items()):
                icon = (
                    "pass" if status == 200
                    else "FAIL" if isinstance(status, int)
                    else "SKIP"
                )
                lines.append(f"| `{path}` | {icon} {status} |")
            lines.append("")

        # Screenshots
        if cop.get("screenshots"):
            lines.append("### Screenshots")
            for ss in cop["screenshots"]:
                lines.append(f"- `{ss}`")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Frontend tab inventory")
    parser.add_argument("--sdk", default=os.environ.get("CLAUDE_SDK", "."))
    parser.add_argument(
        "--soc", default=os.environ.get("CLAUDE_SOC", ""),
        help="Path to SOC repo (gen-ai-roi-demo-v4-v50)",
    )
    parser.add_argument("--api", action="store_true", help="Smoke test backend APIs")
    parser.add_argument(
        "--screenshots", action="store_true", help="Playwright screenshots"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Include full component file lists in markdown output",
    )
    parser.add_argument("--output", default="docs", help="Output directory")
    args = parser.parse_args()

    sdk_path = Path(args.sdk)
    out_dir = Path(args.output)
    out_dir.mkdir(exist_ok=True)

    mode_parts = ["static"]
    if args.api:
        mode_parts.append("api")
    if args.screenshots:
        mode_parts.append("screenshots")
        ok, msg = check_playwright_available()
        if not ok:
            print("WARNING: Screenshots requested but Playwright is not ready — skipping.")
            print(f"  Reason: {msg[:300]}")
            print("  Fix (from repo root): npm install playwright; "
                  "npx playwright install chromium")
            args.screenshots = False
            if "screenshots" in mode_parts:
                mode_parts.remove("screenshots")

    copilot_results = []

    # --- SDK copilots ---
    for name, config in COPILOTS.items():
        print(f"Scanning {name}...")
        fe_base = sdk_path / config["frontend_path"]
        result = scan_frontend_static(fe_base, name, config)

        if args.api and result["api_calls"]:
            print(f"  Smoke testing {len(result['api_calls'])} endpoints...")
            result["smoke_results"] = smoke_test_api(
                config["backend_port"],
                result["api_calls"],
                config.get("smoke_ids"),
            )

        if args.screenshots:
            ss_dir = out_dir / "screenshots"
            ss_dir.mkdir(exist_ok=True)
            tabs = list(dict.fromkeys(
                [*result["tab_names"], *config.get("expected_tabs", [])]
            )) or config["expected_tabs"]
            print(f"  Screenshotting {len(tabs)} tabs...")
            result["screenshots"] = take_screenshots(
                name, config["frontend_port"], tabs, ss_dir
            )

        # Print warnings to console
        for w in result.get("warnings", []):
            print(f"  {w['level']}: {w['message']}")

        copilot_results.append(result)

    # --- SOC copilot ---
    if args.soc:
        soc_path = Path(args.soc)
        if soc_path.exists():
            print("Scanning soc...")
            fe_base = soc_path / SOC_CONFIG["frontend_path"]
            result = scan_frontend_static(fe_base, "soc", SOC_CONFIG)

            if args.api and result["api_calls"]:
                print(f"  Smoke testing {len(result['api_calls'])} endpoints...")
                result["smoke_results"] = smoke_test_api(
                    SOC_CONFIG["backend_port"],
                    result["api_calls"],
                    SOC_CONFIG.get("smoke_ids"),
                )

            if args.screenshots:
                ss_dir = out_dir / "screenshots"
                ss_dir.mkdir(exist_ok=True)
                tabs = list(dict.fromkeys(
                    [*result["tab_names"], *SOC_CONFIG.get("expected_tabs", [])]
                )) or SOC_CONFIG["expected_tabs"]
                print(f"  Screenshotting {len(tabs)} tabs...")
                result["screenshots"] = take_screenshots(
                    "soc", SOC_CONFIG["frontend_port"], tabs, ss_dir
                )

            for w in result.get("warnings", []):
                print(f"  {w['level']}: {w['message']}")

            copilot_results.append(result)
        else:
            print(f"SOC path not found: {soc_path} — skipping")

    inventory = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": "+".join(mode_parts),
        "copilots": copilot_results,
    }

    json_path = out_dir / "tab_inventory.json"
    json_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"\nWritten: {json_path}")

    md_path = out_dir / "tab_inventory.md"
    md_path.write_text(generate_markdown(inventory, verbose=args.verbose), encoding="utf-8")
    print(f"Written: {md_path}")


if __name__ == "__main__":
    main()
