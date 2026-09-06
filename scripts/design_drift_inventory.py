"""Source-only route, screen, test, and local-database inventory for the audit."""
from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"node_modules", ".git", ".venv", "__pycache__", "logs", "graphify-out", "dist", "build", ".mypy_cache", ".pytest_cache", "test-results", "playwright-report"}


def files() -> list[Path]:
    paths: list[Path] = []
    for base, directories, names in os.walk(ROOT):
        directories[:] = [name for name in directories if name not in SKIP]
        paths.extend(Path(base) / name for name in names)
    return paths


def main() -> None:
    routes: list[dict[str, Any]] = []
    screens: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    databases: list[dict[str, Any]] = []
    for path in files():
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix in {".db", ".sqlite", ".sqlite3"}:
            databases.append({"path": relative, "bytes": path.stat().st_size})
        if path.suffix == ".py" and relative.startswith(("apps/", "copilot_sdk/backend/")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            except (SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                decorators = [decorator for decorator in node.decorator_list if isinstance(decorator, ast.Call)
                              and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in {"get", "post", "put", "patch", "delete"}]
                for decorator in decorators:
                    assert isinstance(decorator.func, ast.Attribute)
                    calls = sorted({ast.unparse(call.func) for call in ast.walk(node) if isinstance(call, ast.Call)})
                    routes.append({"file": relative, "line": node.lineno, "handler": node.name,
                                   "async": isinstance(node, ast.AsyncFunctionDef), "method": decorator.func.attr,
                                   "route": ast.unparse(decorator.args[0]) if decorator.args else "?", "calls": calls})
        if path.suffix == ".tsx" and "/src/screens/" in relative and relative.startswith("apps/"):
            source = path.read_text(encoding="utf-8-sig")
            imported = re.findall(r"\b(?:get|fetch)[A-Z]\w*(?=\s*[,}(])", source)
            screen_calls = [(match.group(1), source[:match.start()].count("\n") + 1)
                     for match in re.finditer(r"\b((?:get|fetch)[A-Z]\w*|apiGet|safeApiGet|fetch)\s*\(", source)]
            screens.append({"file": relative, "lexical_api_sites": len(screen_calls), "calls": screen_calls,
                            "imported_loaders": sorted(set(imported)),
                            "effects": source.count("useEffect("), "children": sorted(set(re.findall(r"<([A-Z]\w*)\b", source)))})
        if relative.startswith("e2e/") and path.name.endswith(".spec.ts"):
            source = path.read_text(encoding="utf-8-sig")
            names = re.findall(r'\btest\(\s*["\x27]([^"\x27]+)["\x27]', source)
            patterns = {name: source.count(name) for name in ("waitForResponse", "waitForTimeout", "scoreOrder", "scoreTrade", "scoreAlert", "confirm", "learn")}
            tests.append({"file": relative, "test_count": len(names), "names": names, "patterns": patterns,
                          "timeout_lines": [{"line": index, "text": line.strip()} for index, line in enumerate(source.splitlines(), 1)
                                            if re.search(r"waitForResponse|waitForTimeout|timeout:|setTimeout", line)]})
    result = {"routes": routes, "screens": screens, "tests": tests, "databases": databases}
    destination = ROOT / "logs/design_drift_inventory.json"
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"routes": len(routes), "async_routes": sum(row["async"] for row in routes),
                      "screens": len(screens), "test_files": len(tests), "db_files": len(databases),
                      "db_bytes": sum(row["bytes"] for row in databases)}))


if __name__ == "__main__":
    main()
