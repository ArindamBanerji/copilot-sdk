"""Dependency-free YAML-configured copilot scaffold generation."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CopilotConfig:
    name: str
    domain: str
    categories: int
    actions: int
    factors: int
    penalty_ratio: float
    accent_color: str
    backend_port: int
    frontend_port: int
    eta_confirm: float
    eta_override: float
    q_window: int
    factor_specs: tuple[dict[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "CopilotConfig":
        required = ("name", "domain", "tensor")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Missing required config field(s): {', '.join(missing)}")
        tensor = _mapping(raw["tensor"], "tensor")
        categories = _positive_int(tensor.get("categories"), "tensor.categories")
        actions = _positive_int(tensor.get("actions"), "tensor.actions")
        factors = _positive_int(tensor.get("factors"), "tensor.factors")
        factors_raw = raw.get("factors", [])
        if not isinstance(factors_raw, list):
            raise ValueError("factors must be a YAML list")
        factor_specs: list[dict[str, Any]] = []
        for index, item in enumerate(factors_raw):
            factor = _mapping(item, f"factors[{index}]")
            if not isinstance(factor.get("name"), str) or not factor["name"].strip():
                raise ValueError(f"factors[{index}].name must be a non-empty string")
            factor_specs.append({"name": factor["name"], "type": str(factor.get("type", "numeric"))})
        if factor_specs and len(factor_specs) != factors:
            raise ValueError("tensor.factors must equal the number of factor definitions")
        ports = _mapping(raw.get("ports", {}), "ports")
        conservation = _mapping(raw.get("conservation", {}), "conservation")
        name = _identifier(str(raw["name"]), "name")
        domain = _identifier(str(raw["domain"]), "domain")
        return cls(
            name=name,
            domain=domain,
            categories=categories,
            actions=actions,
            factors=factors,
            penalty_ratio=_positive_float(raw.get("penalty_ratio", 3.0), "penalty_ratio"),
            accent_color=str(raw.get("accent_color", "#4CAF50")),
            backend_port=_positive_int(ports.get("backend", 8040), "ports.backend"),
            frontend_port=_positive_int(ports.get("frontend", 5178), "ports.frontend"),
            eta_confirm=_unit_float(conservation.get("eta_confirm", 0.05), "conservation.eta_confirm"),
            eta_override=_unit_float(conservation.get("eta_override", 0.01), "conservation.eta_override"),
            q_window=_positive_int(conservation.get("q_window", 400), "conservation.q_window"),
            factor_specs=tuple(factor_specs),
        )


class CopilotScaffold:
    """Parse a copilot.yaml and generate a minimal runnable developer cut."""

    def __init__(self, config: CopilotConfig) -> None:
        self.config = config

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CopilotScaffold":
        source = Path(path).read_text(encoding="utf-8")
        return cls(CopilotConfig.from_mapping(parse_yaml(source)))

    def generate(self, output_dir: str | Path) -> list[Path]:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        replacements = {
            "__COPILOT_NAME__": self.config.name,
            "__DOMAIN__": self.config.domain,
            "__BACKEND_PORT__": str(self.config.backend_port),
            "__FRONTEND_PORT__": str(self.config.frontend_port),
            "__CATEGORIES__": str(self.config.categories),
            "__ACTIONS__": str(self.config.actions),
            "__FACTORS__": str(self.config.factors),
            "__PENALTY_RATIO__": repr(self.config.penalty_ratio),
            "__ACCENT_COLOR__": self.config.accent_color,
            "__ETA_CONFIRM__": repr(self.config.eta_confirm),
            "__ETA_OVERRIDE__": repr(self.config.eta_override),
            "__Q_WINDOW__": str(self.config.q_window),
        }
        files = {
            "backend/app/__init__.py": "",
            "backend/app/main.py": _template("main.py.tmpl"),
            "backend/app/config.py": _template("config.py.tmpl"),
            "backend/tests/test_smoke.py": _template("test_smoke.py.tmpl"),
            "frontend/src/CopilotShell.tsx": _template("CopilotShell.tsx.tmpl"),
            "frontend/src/screens/DashboardScreen.tsx": _template("DashboardScreen.tsx.tmpl"),
            "frontend/src/screens/AnalysisScreen.tsx": _template("AnalysisScreen.tsx.tmpl"),
            "frontend/src/screens/PerformanceScreen.tsx": _template("PerformanceScreen.tsx.tmpl"),
            "frontend/src/screens/LogDecisionScreen.tsx": _template("LogDecisionScreen.tsx.tmpl"),
            "copilot.yaml": _render_config(self.config),
        }
        written: list[Path] = []
        for relative, template in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_replace(template, replacements), encoding="utf-8")
            written.append(target)
        return written


def parse_yaml(source: str) -> dict[str, Any]:
    """Parse the intentionally small, documented copilot.yaml subset."""

    rows = [(len(line) - len(line.lstrip(" ")), line.strip()) for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, (indent, text) in enumerate(rows):
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if text.startswith("-"):
            if not isinstance(parent, list):
                raise ValueError(f"YAML list item has no list parent: {text}")
            item_text = text[1:].strip()
            item: dict[str, Any] = {}
            parent.append(item)
            if item_text:
                key, raw = _split_pair(item_text)
                item[key] = _scalar(raw)
            stack.append((indent, item))
            continue
        key, raw = _split_pair(text)
        if raw == "":
            next_indent = rows[index + 1][0] if index + 1 < len(rows) else indent
            next_text = rows[index + 1][1] if index + 1 < len(rows) else ""
            value: Any = [] if next_text.startswith("-") and next_indent > indent else {}
            parent[key] = value
            stack.append((indent, value))
        else:
            if not isinstance(parent, dict):
                raise ValueError(f"YAML mapping has no object parent: {text}")
            parent[key] = _scalar(raw)
    return root


def _split_pair(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"Expected key: value in YAML, got {text!r}")
    key, raw = text.split(":", 1)
    return key.strip(), raw.strip()


def _scalar(raw: str) -> Any:
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    if raw.lower() in {"null", "none"}:
        return None
    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        if re.fullmatch(r"[-+]?\d+", raw):
            return int(raw)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+)", raw):
            return float(raw)
        return raw


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _positive_int(value: Any, field: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if result <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return result


def _positive_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be positive") from exc
    if result <= 0:
        raise ValueError(f"{field} must be positive")
    return result


def _unit_float(value: Any, field: str) -> float:
    result = _positive_float(value, field)
    if result > 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return result


def _identifier(value: str, field: str) -> str:
    normalized = value.strip().lower().replace(" ", "-")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", normalized):
        raise ValueError(f"{field} must be a lowercase identifier")
    return normalized


def _replace(template: str, replacements: dict[str, str]) -> str:
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def _template(name: str) -> str:
    path = Path(__file__).parent / "templates" / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return _BUILTIN_TEMPLATES[name]


def _render_config(config: CopilotConfig) -> str:
    factors = "\n".join(f'  - name: "{item["name"]}"\n    type: "{item["type"]}"' for item in config.factor_specs)
    return f'''name: "{config.name}"\ndomain: "{config.domain}"\ntensor:\n  categories: {config.categories}\n  actions: {config.actions}\n  factors: {config.factors}\npenalty_ratio: {config.penalty_ratio}\naccent_color: "{config.accent_color}"\nports:\n  backend: {config.backend_port}\n  frontend: {config.frontend_port}\nconservation:\n  eta_confirm: {config.eta_confirm}\n  eta_override: {config.eta_override}\n  q_window: {config.q_window}\nfactors:\n{factors}\n'''


_BUILTIN_TEMPLATES = {
    "main.py.tmpl": '''from fastapi import FastAPI\nfrom .config import CONFIG\n\napp = FastAPI(title="__COPILOT_NAME__")\n\n@app.get("/health")\ndef health() -> dict[str, object]:\n    return {"status": "ok", "copilot": CONFIG["name"], "domain": CONFIG["domain"]}\n\n@app.get("/api/score")\ndef score() -> dict[str, object]:\n    return {"observation_only": True, "message": "Decision evidence is accumulating."}\n''',
    "config.py.tmpl": '''CONFIG = {"name": "__COPILOT_NAME__", "domain": "__DOMAIN__", "tensor": {"categories": __CATEGORIES__, "actions": __ACTIONS__, "factors": __FACTORS__}, "penalty_ratio": __PENALTY_RATIO__, "accent_color": "__ACCENT_COLOR__", "ports": {"backend": __BACKEND_PORT__, "frontend": __FRONTEND_PORT__}, "conservation": {"eta_confirm": __ETA_CONFIRM__, "eta_override": __ETA_OVERRIDE__, "q_window": __Q_WINDOW__}}\n''',
    "test_smoke.py.tmpl": '''from pathlib import Path\nimport ast\n\ndef test_generated_config_exists() -> None:\n    source = Path(__file__).parents[1] / "app" / "config.py"\n    ast.parse(source.read_text(encoding="utf-8"))\n''',
    "CopilotShell.tsx.tmpl": '''export default function CopilotShell() {\n  return <main data-testid="copilot-shell" style={{ color: "__ACCENT_COLOR__" }}><h1>__COPILOT_NAME__</h1><p>Observation workspace for __DOMAIN__.</p></main>;\n}\n''',
    "DashboardScreen.tsx.tmpl": '''export default function DashboardScreen() { return <section data-testid="dashboard-screen"><h2>__COPILOT_NAME__ dashboard</h2><p>Evidence is accumulating.</p></section>; }\n''',
    "AnalysisScreen.tsx.tmpl": '''export default function AnalysisScreen() { return <section data-testid="analysis-screen"><h2>Analysis</h2><p>Observed factors: __FACTORS__.</p></section>; }\n''',
    "PerformanceScreen.tsx.tmpl": '''export default function PerformanceScreen() { return <section data-testid="performance-screen"><h2>Performance</h2><p>Verified outcomes shape the learning curve.</p></section>; }\n''',
    "LogDecisionScreen.tsx.tmpl": '''export default function LogDecisionScreen() { return <section data-testid="log-decision-screen"><h2>Log a decision</h2><p>Record the evidence and human outcome.</p></section>; }\n''',
}
