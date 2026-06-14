"""Safe template rendering for situation evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Formatter
from typing import Any


def _json_safe(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class TemplateRenderResult:
    """Result from safe situation template rendering."""

    rendered: str
    variables: dict[str, Any]
    missing_variables: list[str] = field(default_factory=list)
    used_variables: list[str] = field(default_factory=list)
    audience: str = "L1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rendered": self.rendered,
            "variables": _json_safe(self.variables),
            "missing_variables": list(self.missing_variables),
            "used_variables": list(self.used_variables),
            "audience": self.audience,
        }


class _SafeFormatMap(dict):
    def __init__(self, values: dict[str, Any], numeric_fields: set[str], missing: set[str]) -> None:
        super().__init__(values)
        self._numeric_fields = numeric_fields
        self._missing = missing

    def __missing__(self, key: str) -> Any:
        self._missing.add(key)
        return 0.0 if key in self._numeric_fields else "unknown"


class SafeTemplateRenderer:
    """Render templates without raising on missing fields or formatting errors."""

    def render(
        self,
        template: str,
        variables: dict[str, Any],
        *,
        defaults: dict[str, Any] | None = None,
        audience: str = "L1",
    ) -> TemplateRenderResult:
        source_variables = dict(variables or {})
        render_variables = dict(defaults or {})
        render_variables.update(source_variables)
        try:
            used_variables, numeric_fields = self._template_fields(template)
            parse_error = None
        except ValueError:
            used_variables, numeric_fields = [], set()
            parse_error = "template_parse_error"
        missing: set[str] = {
            name for name in used_variables if name not in render_variables
        }
        if parse_error is not None:
            missing.add(parse_error)

        try:
            rendered = template.format_map(
                _SafeFormatMap(render_variables, numeric_fields, missing)
            )
        except Exception:
            coerced = {
                name: self._coerce_value(render_variables.get(name), name in numeric_fields)
                for name in used_variables
            }
            missing.update(name for name in used_variables if name not in render_variables)
            try:
                rendered = template.format_map(_SafeFormatMap(coerced, numeric_fields, missing))
            except Exception:
                rendered = self._fallback_render(template, used_variables, missing)

        return TemplateRenderResult(
            rendered=str(rendered),
            variables=dict(render_variables),
            missing_variables=sorted(missing),
            used_variables=used_variables,
            audience=audience,
        )

    @staticmethod
    def _template_fields(template: str) -> tuple[list[str], set[str]]:
        used: list[str] = []
        numeric: set[str] = set()
        formatter = Formatter()
        for _literal, field_name, format_spec, _conversion in formatter.parse(template):
            if not field_name:
                continue
            root = field_name.split(".", 1)[0].split("[", 1)[0]
            if root not in used:
                used.append(root)
            if format_spec and any(token in format_spec for token in "bcdoxXneEfFgG%"):
                numeric.add(root)
        return used, numeric

    @staticmethod
    def _coerce_value(value: Any, numeric: bool) -> Any:
        if numeric:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        if value is None:
            return "unknown"
        return value

    @staticmethod
    def _fallback_render(template: str, used_variables: list[str], missing: set[str]) -> str:
        rendered = template
        for name in used_variables:
            missing.add(name)
            rendered = rendered.replace("{" + name + "}", "unknown")
        return rendered
