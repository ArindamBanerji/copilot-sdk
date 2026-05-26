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
                        Code analysis sessions can read the output.

  2. API:               Adds endpoint smoke tests (curl each backend).
     --api              Requires backends running.

  3. SCREENSHOTS:       Adds Playwright screenshots of each tab.
     --screenshots      Requires full stack running (demo.py).

Usage:
  cd $CLAUDE_SDK

  # Static only (safe, no running servers needed)
  python scripts/tab_inventory.py

  # With SOC (separate repo)
  python scripts/tab_inventory.py --soc "$env:CLAUDE_SOC"

  # Static + API smoke
  python scripts/tab_inventory.py --api

  # Full capture (requires demo.py running)
  python scripts/tab_inventory.py --api --screenshots
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Copilot definitions — ports match demo.py
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
    },
}

# SOC is added dynamically when --soc is provided (separate repo)
SOC_CONFIG = {
    "accent": "blue",
    "backend_port": 8001,
    "frontend_port": 5173,
    "frontend_path": "frontend/src",  # relative to SOC repo root
    "backend_path": "backend/app",
    "expected_tabs": [
        "Analytics", "Evolution", "Triage", "Compounding",
        "Executive", "S2P Preview", "Governance",
    ],
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Screen-level patterns in App.tsx / CopilotShell configuration
# Matches: label: "Dashboard", name: "Log Trade", title: 'Analysis'
TAB_LABEL_RE = re.compile(
    r"""(?:label|title)\s*[:=]\s*['"]([^'"]{2,30})['"]""", re.IGNORECASE
)

# CopilotShell screen config: { name: "...", component: ... }
SHELL_SCREEN_RE = re.compile(
    r"""name\s*:\s*['"]([^'"]{2,30})['"]""",
)

# Import screens: import XScreen from './screens/XScreen'
SCREEN_IMPORT_RE = re.compile(
    r"""import\s+(\w+)\s+from\s+['"]\.?\/?screens\/""", re.IGNORECASE
)

# Component imports — multiple patterns:
#   import { Foo, Bar } from '../components/...'
#   import { Foo } from '@/components/...'
#   import Foo from '../components/...'
COMPONENT_IMPORT_RE = re.compile(
    r"""import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['"](?:\.\.?\/)*components\/""",
    re.IGNORECASE,
)

# API paths: '/api/...', "/api/...", `/api/...`, or fetch("/api/...")
API_CALL_RE = re.compile(r"""['"`](/api/[a-zA-Z0-9_/\-${}.]+)['"`]""")

# Fetch/axios wrapper patterns to find API base URLs
FETCH_PATTERN_RE = re.compile(
    r"""(?:fetch|get|post|put|delete|axios)\s*\(\s*[`'"]([^'"`\s]+)""",
    re.IGNORECASE,
)

# Noise filters — strings that look like tabs but aren't
TAB_NOISE = {
    # CSS classes
    "mb-4", "px-4", "py-3", "text-sm", "rounded-md", "flex",
    "justify-end", "border", "items-center", "gap-2", "w-full",
    # Generic React/HTML
    "button", "div", "span", "input", "select", "form",
    # App titles (not tabs)
    "Trading Copilot", "Purchasing Copilot", "DataOps Copilot",
    "S2P Copilot", "SOC Copilot",
}


def _is_tab_noise(s: str) -> bool:
    """Filter out CSS classes, HTML tags, and app titles."""
    s_lower = s.lower().strip()
    if s_lower in {n.lower() for n in TAB_NOISE}:
        return True
    # CSS class patterns: contains spaces with CSS-like tokens
    if re.match(r'^[a-z0-9\-]+\s+[a-z0-9\-]', s_lower):
        return True
    # Too short or too long
    if len(s.strip()) < 2 or len(s.strip()) > 30:
        return True
    # Pure CSS tokens (all lowercase with hyphens, no spaces)
    if re.match(r'^[a-z\-]+$', s) and '-' in s:
        return True
    return False


def _extract_tabs_from_source(text: str) -> list[str]:
    """Extract tab names from App.tsx or similar, with noise filtering."""
    candidates = []

    # Strategy 1: CopilotShell screen configs — most reliable
    # Look for patterns like: screens={[ { name: "Dashboard", ... }, ... ]}
    shell_matches = SHELL_SCREEN_RE.findall(text)
    if shell_matches:
        candidates.extend(shell_matches)

    # Strategy 2: label/title attributes
    label_matches = TAB_LABEL_RE.findall(text)
    if label_matches:
        candidates.extend(label_matches)

    # Strategy 3: screen imports (fallback)
    screen_imports = SCREEN_IMPORT_RE.findall(text)
    if screen_imports and not candidates:
        candidates.extend(
            # "DashboardScreen" -> "Dashboard"
            re.sub(r'Screen$', '', s) for s in screen_imports
        )

    # Deduplicate preserving order, filter noise
    seen = set()
    result = []
    for c in candidates:
        c = c.strip()
        if c not in seen and not _is_tab_noise(c):
            seen.add(c)
            result.append(c)

    return result


def _extract_components(text: str) -> list[str]:
    """Extract imported component names from a TSX file."""
    components = []
    for m in COMPONENT_IMPORT_RE.finditer(text):
        # Group 1: destructured { Foo, Bar }
        if m.group(1):
            components.extend(
                c.strip() for c in m.group(1).split(",") if c.strip()
            )
        # Group 2: default import
        if m.group(2):
            components.append(m.group(2).strip())
    return components


def _extract_api_calls(text: str) -> set[str]:
    """Extract API endpoint paths from source text."""
    apis = set()
    # Direct string literals: '/api/...'
    apis.update(API_CALL_RE.findall(text))
    # Fetch/axios patterns
    for m in FETCH_PATTERN_RE.finditer(text):
        path = m.group(1)
        if path.startswith("/api/"):
            apis.add(path)
    # Clean up template literal fragments
    cleaned = set()
    for api in apis:
        # Remove trailing template syntax: /api/foo/${id} -> /api/foo/
        clean = re.sub(r'\$\{[^}]*\}', '{id}', api)
        cleaned.add(clean)
    return cleaned


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
    }

    if not fe_base.exists():
        result["error"] = f"Frontend path not found: {fe_base}"
        return result

    # Count TSX files (excluding node_modules)
    tsx_files = [
        f for f in fe_base.rglob("*.tsx")
        if "node_modules" not in str(f)
    ]
    result["tsx_file_count"] = len(tsx_files)

    # Find screen/tab files — SDK uses screens/, SOC uses components/tabs/
    screen_dirs = [
        fe_base / "screens",           # SDK copilots: DashboardScreen.tsx, etc.
        fe_base / "components" / "tabs",  # SOC: RuntimeEvolutionTab.tsx, etc.
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
            s["file"]
            .replace("Screen.tsx", "")   # SDK: DashboardScreen.tsx → Dashboard
            .replace("Tab.tsx", "")       # SOC: RuntimeEvolutionTab.tsx → RuntimeEvolution
            .replace(".tsx", "")
            for s in result["screens"]
        ]

    # Find shared component files
    components_dir = fe_base / "components"
    if components_dir.exists():
        for f in sorted(components_dir.rglob("*.tsx")):
            rel = str(f.relative_to(fe_base))
            if "node_modules" not in rel:
                result["components"].append(rel)

    # Collect ALL API paths referenced across all frontend files
    all_apis = set()
    for tsx in tsx_files:
        try:
            text = tsx.read_text(encoding="utf-8", errors="replace")
            all_apis.update(_extract_api_calls(text))
        except Exception:
            pass

    # Also scan .ts files (api.ts, constants.ts, config.ts)
    for ts in fe_base.rglob("*.ts"):
        if "node_modules" in str(ts) or ts.suffix == ".tsx":
            continue
        try:
            text = ts.read_text(encoding="utf-8", errors="replace")
            all_apis.update(_extract_api_calls(text))
        except Exception:
            pass

    result["api_calls"] = sorted(all_apis)

    return result


def smoke_test_api(port: int, paths: list[str]) -> dict:
    """Hit backend endpoints and record status codes."""
    import urllib.request
    import urllib.error

    results = {}
    for path in paths:
        # Skip paths with template placeholders
        if "{" in path:
            results[path] = "SKIP (template)"
            continue
        url = f"http://localhost:{port}{path}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                results[path] = resp.status
        except urllib.error.HTTPError as e:
            results[path] = e.code
        except Exception as e:
            results[path] = f"ERR: {type(e).__name__}"
    return results


def take_screenshots(copilot: str, port: int, tabs: list[str], out_dir: Path):
    """Use Playwright to screenshot each tab. Returns list of saved paths."""
    saved = []
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage({{ viewport: {{ width: 1280, height: 900 }} }});
    await page.goto('http://localhost:{port}', {{ waitUntil: 'networkidle', timeout: 15000 }});
    await page.waitForTimeout(2000);

    // Screenshot initial state
    await page.screenshot({{ path: '{out_dir}/{copilot}_initial.png', fullPage: false }});

    // Click each tab and screenshot
    const tabs = {json.dumps(tabs)};
    for (const tab of tabs) {{
        try {{
            const el = await page.getByRole('tab', {{ name: tab }}).or(
                page.getByText(tab, {{ exact: false }})
            ).first();
            if (el) {{
                await el.click();
                await page.waitForTimeout(1500);
                const safeName = tab.toLowerCase().replace(/[^a-z0-9]/g, '_');
                await page.screenshot({{ path: '{out_dir}/{copilot}_' + safeName + '.png', fullPage: false }});
            }}
        }} catch (e) {{
            console.error('Tab not found:', tab, e.message);
        }}
    }}
    await browser.close();
}})();
"""
    script_path = out_dir / f"_capture_{copilot}.js"
    script_path.write_text(script)
    try:
        subprocess.run(
            ["node", str(script_path)],
            capture_output=True, text=True, timeout=60,
        )
        for png in sorted(out_dir.glob(f"{copilot}_*.png")):
            saved.append(str(png))
    except Exception as e:
        print(f"  Screenshot failed for {copilot}: {e}")
    finally:
        script_path.unlink(missing_ok=True)
    return saved


def generate_markdown(inventory: dict) -> str:
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

        # Components (file list)
        if cop["components"]:
            lines.append(f"### Component Files ({len(cop['components'])})")
            for c in cop["components"][:30]:
                lines.append(f"- `{c}`")
            if len(cop["components"]) > 30:
                lines.append(f"- ... +{len(cop['components']) - 30} more")
            lines.append("")

        # API calls (full list)
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

    copilot_results = []

    # --- SDK copilots (Trading, Purchasing, DataOps, S2P frontend) ---
    for name, config in COPILOTS.items():
        print(f"Scanning {name}...")
        fe_base = sdk_path / config["frontend_path"]
        result = scan_frontend_static(fe_base, name, config)

        # API smoke test
        if args.api and result["api_calls"]:
            print(f"  Smoke testing {len(result['api_calls'])} endpoints...")
            result["smoke_results"] = smoke_test_api(
                config["backend_port"], result["api_calls"]
            )

        # Screenshots
        if args.screenshots:
            ss_dir = out_dir / "screenshots"
            ss_dir.mkdir(exist_ok=True)
            tabs = result["tab_names"] or config["expected_tabs"]
            print(f"  Screenshotting {len(tabs)} tabs...")
            result["screenshots"] = take_screenshots(
                name, config["frontend_port"], tabs, ss_dir
            )

        copilot_results.append(result)

    # --- SOC copilot (separate repo) ---
    if args.soc:
        soc_path = Path(args.soc)
        if soc_path.exists():
            print("Scanning soc...")
            fe_base = soc_path / SOC_CONFIG["frontend_path"]
            result = scan_frontend_static(fe_base, "soc", SOC_CONFIG)

            if args.api and result["api_calls"]:
                print(f"  Smoke testing {len(result['api_calls'])} endpoints...")
                result["smoke_results"] = smoke_test_api(
                    SOC_CONFIG["backend_port"], result["api_calls"]
                )

            if args.screenshots:
                ss_dir = out_dir / "screenshots"
                ss_dir.mkdir(exist_ok=True)
                tabs = result["tab_names"] or SOC_CONFIG["expected_tabs"]
                print(f"  Screenshotting {len(tabs)} tabs...")
                result["screenshots"] = take_screenshots(
                    "soc", SOC_CONFIG["frontend_port"], tabs, ss_dir
                )

            copilot_results.append(result)
        else:
            print(f"SOC path not found: {soc_path} — skipping")

    inventory = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": "+".join(mode_parts),
        "copilots": copilot_results,
    }

    # Write JSON
    json_path = out_dir / "tab_inventory.json"
    json_path.write_text(json.dumps(inventory, indent=2))
    print(f"\nWritten: {json_path}")

    # Write markdown
    md_path = out_dir / "tab_inventory.md"
    md_path.write_text(generate_markdown(inventory))
    print(f"Written: {md_path}")


if __name__ == "__main__":
    main()
