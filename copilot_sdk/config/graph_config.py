"""Fail-closed, source-aware graph configuration loading."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only embedded Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

Source = Literal["env", "file", "default"]
Backend = Literal["sqlite", "age", "dual_write"]


class GraphConfigError(ValueError):
    """Raised when graph configuration is incomplete or unsafe."""


def require_shared_graph(
    *,
    backend: str,
    graph: str | None,
    domain: str,
    profile: str = "production",
    test_mode: bool = False,
) -> None:
    """Require the JM shared graph at a production AGE startup boundary.

    The low-level factory intentionally remains usable by migration and
    disposable-test callers.  Copilot startup paths call this explicit guard
    after resolving their typed configuration.
    """
    normalized_backend = str(backend).strip().lower()
    if normalized_backend not in {"age", "dual_write"}:
        return
    if profile != "production" or test_mode:
        return
    normalized_graph = str(graph or "").strip()
    if normalized_graph != "soc_graph":
        raise GraphConfigError(
            f"production AGE startup for domain '{domain}' requires graph "
            f"'soc_graph', got {normalized_graph or '<blank>'!r}"
        )


def _env_name(domain: str) -> str:
    return domain.upper()


def _present(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def _redacted(field: str, value: Any) -> str:
    text = str(value)
    if any(token in field.lower() for token in ("dsn", "password", "uri")):
        return "<redacted>" if text else "<empty>"
    return text


@dataclass(frozen=True)
class GraphConfig:
    domain: str
    backend: Backend
    expected_backend: Backend
    dsn: str | None
    graph: str
    prefix: str
    active_test_mode: bool
    shadow_age: bool
    live_age_test: bool
    port: int | None
    sources: tuple[tuple[str, Source], ...]
    narrative_provider: str | None = None

    @property
    def authorized(self) -> str:
        """Return the non-configurable domain/graph authorization pair."""
        return f"{self.domain}:{self.graph}"

    @classmethod
    def load(cls, domain: str = "trading", *, profile: str = "production") -> "GraphConfig":
        domain = domain.strip().lower()
        if domain not in {"soc", "trading", "purchasing", "dataops", "s2p"}:
            raise GraphConfigError(f"unknown graph config domain '{domain}'")

        raw, _file_values = cls._read_file(domain)
        defaults = dict(raw.get("defaults", {}))
        section = dict(raw.get("copilot", {}).get(domain, {}))
        merged: dict[str, Any] = {**defaults, **section}
        if domain == "soc":
            merged.update(raw.get("soc", {}))
        env_prefix = _env_name(domain)
        env_specs: dict[str, tuple[str, ...]]
        if domain == "soc":
            env_specs = {
                "backend": ("GRAPH_BACKEND",),
                "dsn": ("GRAPH_DSN", "AGE_DSN"),
                "graph": ("GRAPH_NAME", "AGE_GRAPH_NAME"),
                "domain": ("GRAPH_DOMAIN",),
                "narrative_provider": ("NARRATIVE_PROVIDER",),
            }
        else:
            env_specs = {
                "backend": (f"{env_prefix}_ACTIVE_GRAPH_BACKEND", "GRAPH_BACKEND"),
                "dsn": (f"{env_prefix}_ACTIVE_AGE_DSN", "GRAPH_DSN", "AGE_DSN"),
                "graph": (f"{env_prefix}_ACTIVE_AGE_GRAPH", "GRAPH_NAME", "AGE_GRAPH_NAME"),
                "domain": (f"{env_prefix}_ACTIVE_AGE_DOMAIN",),
                "active_test_mode": (f"{env_prefix}_ACTIVE_AGE_TEST_MODE",),
                "shadow_age": (f"{env_prefix}_SHADOW_AGE",),
                "live_age_test": (f"{env_prefix}_ACTIVE_LIVE_AGE_TEST",),
            }

        # Prefix, expected backend, and ports are file policy unless explicitly
        # extended later; graph connection values are environment-overridable.
        sources: dict[str, Source] = {}
        values: dict[str, Any] = {}
        fields = (
            "domain", "backend", "expected_backend", "dsn", "graph", "prefix",
            "active_test_mode", "shadow_age", "live_age_test", "port",
            "narrative_provider",
        )
        for field in fields:
            names = env_specs.get(field, ())
            env_key, env_value = cls._first_env(names)
            file_has = field in merged
            file_value = merged.get(field)
            if _present(env_value):
                assert env_value is not None
                if file_has and str(file_value) != env_value:
                    logger.warning(
                        "graph config collision field=%s file=%s env=%s winner=env",
                        field, _redacted(field, file_value), _redacted(field, env_value),
                    )
                values[field] = cls._coerce(field, env_value)
                sources[field] = "env"
            elif file_has:
                values[field] = file_value
                sources[field] = "file"
            else:
                values[field] = cls._default(field, domain)
                sources[field] = "default"

        # Domain is a fixed policy value for non-SOC sections; do not permit a
        # generic GRAPH_DOMAIN to silently change a copilot identity.
        resolved_domain = str(values["domain"] or domain).strip().lower()
        if resolved_domain != domain:
            raise GraphConfigError(
                f"Domain mismatch: requested '{domain}' but resolved '{resolved_domain}'. "
                f"Check {domain.upper()}_ACTIVE_AGE_DOMAIN env var."
            )
        values["domain"] = resolved_domain
        config = cls(
            domain=values["domain"],
            backend=cast(Backend, str(values["backend"]).strip().lower()),
            expected_backend=cast(Backend, str(values["expected_backend"]).strip().lower()),
            dsn=(str(values["dsn"]).strip() if _present(values["dsn"]) else None),
            graph=str(values["graph"]).strip(),
            prefix=str(values["prefix"]).strip(),
            active_test_mode=_as_bool(values["active_test_mode"]),
            shadow_age=_as_bool(values["shadow_age"]),
            live_age_test=_as_bool(values["live_age_test"]),
            port=_as_int(values["port"]),
            sources=tuple(sorted(sources.items())),
            narrative_provider=_optional_text(values.get("narrative_provider")),
        )
        config.validate(profile=profile)
        return config

    @classmethod
    def _read_file(cls, domain: str) -> tuple[dict[str, Any], dict[str, Any]]:
        package_root = Path(__file__).resolve().parents[2]
        candidates: list[Path] = []
        configured = os.environ.get("GRAPH_CONFIG_PATH")
        if _present(configured):
            assert configured is not None
            candidates.append(Path(configured).expanduser())
        candidates.append(package_root / "graph_config.toml")
        candidates.append(Path(__file__).resolve().parent / "graph_config.toml")
        configured_path = (
            Path(configured).expanduser()
            if configured is not None and _present(configured)
            else None
        )
        if configured_path is not None and not configured_path.is_file():
            raise GraphConfigError(f"GRAPH_CONFIG_PATH does not exist: {configured_path}")
        for path in candidates:
            if path.is_file():
                try:
                    with path.open("rb") as handle:
                        parsed = tomllib.load(handle)
                except tomllib.TOMLDecodeError as exc:
                    raise GraphConfigError(f"Malformed TOML at {path}: {exc}") from exc
                return parsed, dict(parsed.get("copilot", {}).get(domain, {}))
        return {}, {}

    @staticmethod
    def _first_env(names: tuple[str, ...]) -> tuple[str | None, str | None]:
        for name in names:
            value = os.environ.get(name)
            if _present(value):
                return name, value
        return None, None

    @staticmethod
    def _default(field: str, domain: str) -> Any:
        return {
            "domain": domain,
            "backend": "age",
            "expected_backend": "age",
            "dsn": "",
            "graph": "soc_graph",
            "prefix": f"{domain.upper()}-",
            "active_test_mode": False,
            "shadow_age": False,
            "live_age_test": False,
            "port": None,
            "narrative_provider": None,
        }[field]

    @staticmethod
    def _coerce(field: str, value: str) -> Any:
        if field in {"active_test_mode", "shadow_age", "live_age_test"}:
            return _as_bool(value)
        if field == "port":
            return _as_int(value)
        return value

    def validate(self, *, profile: str = "production") -> None:
        if self.backend not in {"sqlite", "age", "dual_write"}:
            raise GraphConfigError(f"invalid backend '{self.backend}'")
        if self.expected_backend not in {"sqlite", "age", "dual_write"}:
            raise GraphConfigError(f"invalid expected backend '{self.expected_backend}'")
        if self.domain not in {"soc", "trading", "purchasing", "dataops", "s2p"}:
            raise GraphConfigError(f"unknown graph config domain '{self.domain}'")
        if self.expected_backend == "age" and self.backend == "sqlite":
            allowed = profile == "development" and os.environ.get("CI_ALLOW_SQLITE_FALLBACK") == "1"
            if not allowed:
                raise GraphConfigError(
                    f"expected backend age but resolved sqlite for domain '{self.domain}'"
                )
        if self.backend == "age":
            if not self.dsn:
                raise GraphConfigError(f"missing AGE DSN for domain '{self.domain}'")
            if not self.graph:
                raise GraphConfigError(f"missing AGE graph for domain '{self.domain}'")
        if not self.domain or not self.graph:
            raise GraphConfigError("domain and graph must be non-empty")
        expected = f"{self.domain}:{self.graph}"
        if self.authorized != expected:
            raise GraphConfigError(f"domain/graph authorization mismatch: expected '{expected}'")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise GraphConfigError(f"invalid port value '{value}'") from exc


def _optional_text(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


__all__ = ["GraphConfig", "GraphConfigError", "require_shared_graph"]
