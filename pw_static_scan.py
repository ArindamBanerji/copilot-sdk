"""Playwright static selector scan.

Cross-references getByText/getByRole strings in E2E spec files
against strings found in frontend source code.
Mismatches = stale selectors that will cause test failures.

Run from: copilot-sdk/
Usage: python pw_static_scan.py
"""

import os
import re


def collect_selectors(e2e_dir):
    """Extract getByText and role name strings from spec files."""
    selectors = []
    for root, dirs, files in os.walk(e2e_dir):
        dirs[:] = [d for d in dirs if d != "node_modules"]
        for f in files:
            if not f.endswith(".spec.ts"):
                continue
            path = os.path.join(root, f)
            src = open(path, encoding="utf-8").read()
            # getByText("Xxx") or getByText('Xxx')
            for m in re.finditer(r"""getByText\s*\(\s*['"]([^'"]+)['"]""", src):
                selectors.append({"file": path, "type": "text", "value": m.group(1)})
            # getByRole('xxx', { name: 'Yyy' })
            for m in re.finditer(r"""name:\s*['"]([^'"]+)['"]""", src):
                selectors.append({"file": path, "type": "role-name", "value": m.group(1)})
            # getByTestId("xxx")
            for m in re.finditer(r"""getByTestId\s*\(\s*['"]([^'"]+)['"]""", src):
                selectors.append({"file": path, "type": "testid", "value": m.group(1)})
    return selectors


def collect_frontend_strings(apps_dir):
    """Extract visible strings from frontend source."""
    strings = set()
    test_ids = set()
    for copilot in ["trading", "purchasing", "dataops", "s2p"]:
        fe_dir = os.path.join(apps_dir, copilot, "frontend", "src")
        if not os.path.isdir(fe_dir):
            continue
        for root, dirs, files in os.walk(fe_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "dist")]
            for f in files:
                if not f.endswith((".tsx", ".ts")):
                    continue
                src = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                # Strings in JSX: >Text< or "Text" or 'Text'
                for m in re.finditer(r"""[>"']([A-Z][A-Za-z0-9 &\-]{2,50})[<"']""", src):
                    strings.add(m.group(1).strip())
                # Template literals with text
                for m in re.finditer(r"""`([^`]{3,50})`""", src):
                    strings.add(m.group(1).strip())
                # data-testid="xxx"
                for m in re.finditer(r"""data-testid=["']([^"']+)["']""", src):
                    test_ids.add(m.group(1))
                # testId prop
                for m in re.finditer(r"""testId=["']([^"']+)["']""", src):
                    test_ids.add(m.group(1))
    return strings, test_ids


def main():
    selectors = collect_selectors("e2e")
    fe_strings, fe_test_ids = collect_frontend_strings("apps")

    # Also check shared SDK frontend
    shared_dir = os.path.join("copilot_sdk", "frontend")
    if os.path.isdir(shared_dir):
        for root, dirs, files in os.walk(shared_dir):
            for f in files:
                if not f.endswith((".tsx", ".ts")):
                    continue
                src = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r"""[>"']([A-Z][A-Za-z0-9 &\-]{2,50})[<"']""", src):
                    fe_strings.add(m.group(1).strip())
                for m in re.finditer(r"""data-testid=["']([^"']+)["']""", src):
                    fe_test_ids.add(m.group(1))

    missing = []
    found = []
    for s in selectors:
        val = s["value"]
        if s["type"] == "testid":
            if val in fe_test_ids:
                found.append(s)
            else:
                missing.append(s)
        else:
            # Check exact match or case-insensitive substring
            if val in fe_strings or any(val.lower() in fs.lower() for fs in fe_strings):
                found.append(s)
            else:
                missing.append(s)

    print(f"Total selectors scanned: {len(selectors)}")
    print(f"  text:      {sum(1 for s in selectors if s['type'] == 'text')}")
    print(f"  role-name: {sum(1 for s in selectors if s['type'] == 'role-name')}")
    print(f"  testid:    {sum(1 for s in selectors if s['type'] == 'testid')}")
    print(f"Found in frontend: {len(found)}")
    print(f"MISSING from frontend: {len(missing)}")
    print()

    if missing:
        by_file = {}
        for m in missing:
            by_file.setdefault(m["file"], []).append((m["type"], m["value"]))
        for f in sorted(by_file):
            relpath = os.path.relpath(f)
            print(f"{relpath}:")
            for typ, val in by_file[f]:
                print(f'  STALE [{typ}]: "{val}"')
            print()

    # Summary by copilot
    print("=" * 60)
    print("PER-COPILOT SUMMARY")
    print("=" * 60)
    copilots = {"trading": [], "purchasing": [], "dataops": [], "s2p": [], "demo-cuts": [], "diagnostics": []}
    for m in missing:
        for cop in copilots:
            if cop in m["file"]:
                copilots[cop].append(m)
                break
    for cop, items in sorted(copilots.items()):
        if items:
            print(f"  {cop}: {len(items)} stale selectors")
        else:
            print(f"  {cop}: clean")


if __name__ == "__main__":
    main()
