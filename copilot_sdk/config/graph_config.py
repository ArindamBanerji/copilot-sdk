"""Fail-closed, source-aware graph configuration loading."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any, Literal, Mapping, cast

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only embedded Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

Source = Literal["env", "file", "default", "argument"]
Backend = Literal["sqlite", "memory", "age", "dual_write"]
Profile = Literal["production", "test", "offline"]
DOMAINS = ("soc", "trading", "purchasing", "dataops", "s2p")


class GraphConfigError(ValueError):
    """Raised when graph configuration is incomplete or unsafe."""


def resolve_profile(
    profile: str | None = None, *, domain: str = "", env: Mapping[str, str] | None = None,
) -> Profile:
    """Resolve only explicit profile settings; flags/store types never select a profile."""
    source = os.environ if env is None else env
    value = profile if profile is not None else source.get(
        f"{domain.upper()}_PROFILE", source.get("GRAPH_PROFILE", source.get("COPILOT_PROFILE", "production"))
    )
    normalized = value.strip().lower()
    # Backward-compatible spelling, not an inferred fallback permission.
    if normalized == "development":
        normalized = "offline"
    if normalized not in {"production", "test", "offline"}:
        raise GraphConfigError("profile must be 'production', 'test', or 'offline'")
    return cast(Profile, normalized)


@dataclass(frozen=True)
class GraphIdentity:
    """Opaque server/database identity plus graph identity; contains no DSN secrets."""

    database_id: str
    graph_name: str
    graph_oid: int

    def same_destination(self, other: "GraphIdentity") -> bool:
        return self == other


def require_shared_graph(
    *,
    backend: str,
    graph: str | None,
    domain: str,
    profile: str = "production",
    test_mode: bool = False,
) -> None:
    """Static compatibility guard; GraphConfig.require_shared_graph also probes AGE."""
    selected_profile = resolve_profile(profile, domain=domain)
    normalized_backend = str(backend).strip().lower()
    if selected_profile != "production":
        return
    if test_mode:
        raise GraphConfigError("production profile conflicts with AGE test_mode")
    if normalized_backend != "age":
        raise GraphConfigError("production requires AGE primary; SQLite/InMemory/dual_write are test/offline only")
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
    dsn: str | None = dataclass_field(repr=False)
    graph: str
    prefix: str
    active_test_mode: bool
    shadow_age: bool
    live_age_test: bool
    port: int | None
    sources: tuple[tuple[str, Source], ...]
    narrative_provider: str | None = None
    profile: Profile = "production"
    source_keys: tuple[tuple[str, str], ...] = ()
    shared_dsn: str | None = dataclass_field(default=None, repr=False)
    shared_graph: str = "soc_graph"

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile", resolve_profile(self.profile, domain=self.domain))

    @property
    def authorized(self) -> str:
        """Return the non-configurable domain/graph authorization pair."""
        return f"{self.domain}:{self.graph}"

    @classmethod
    def load(
        cls, domain: str = "trading", *, profile: str | None = None,
        env: Mapping[str, str] | None = None, overrides: Mapping[str, Any] | None = None,
    ) -> "GraphConfig":
        domain = domain.strip().lower()
        source = os.environ if env is None else env
        selected_profile = resolve_profile(profile, domain=domain, env=source)
        if not domain or (selected_profile == "production" and domain not in DOMAINS):
            raise GraphConfigError(f"unknown graph config domain '{domain}'")

        raw, _file_values = cls._read_file(domain, env=source)
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
        source_keys: dict[str, str] = {}
        values: dict[str, Any] = {}
        fields = (
            "domain", "backend", "expected_backend", "dsn", "graph", "prefix",
            "active_test_mode", "shadow_age", "live_age_test", "port",
            "narrative_provider",
        )
        for field in fields:
            names = env_specs.get(field, ())
            env_key, env_value = cls._first_env(names, env=source)
            file_has = field in merged
            file_value = merged.get(field)
            if overrides is not None and field in overrides:
                values[field] = overrides[field]
                sources[field] = "argument"
                source_keys[field] = f"argument:{field}"
            elif _present(env_value):
                assert env_value is not None
                if file_has and str(file_value) != env_value:
                    logger.warning(
                        "graph config collision field=%s file=%s env=%s winner=env",
                        field, _redacted(field, file_value), _redacted(field, env_value),
                    )
                values[field] = cls._coerce(field, env_value)
                sources[field] = "env"
                source_keys[field] = str(env_key)
            elif file_has:
                values[field] = file_value
                sources[field] = "file"
                table = "soc" if domain == "soc" and field in raw.get("soc", {}) else (
                    f"copilot.{domain}" if field in section else "defaults"
                )
                source_keys[field] = f"toml:{table}.{field}"
            else:
                values[field] = cls._default(field, domain)
                sources[field] = "default"
                source_keys[field] = f"default:{field}"

        # Domain is a fixed policy value for non-SOC sections; do not permit a
        # generic GRAPH_DOMAIN to silently change a copilot identity.
        resolved_domain = str(values["domain"] or domain).strip().lower()
        if resolved_domain != domain:
            raise GraphConfigError(
                f"Domain mismatch: requested '{domain}' but resolved '{resolved_domain}'. "
                f"Check {domain.upper()}_ACTIVE_AGE_DOMAIN env var."
            )
        values["domain"] = resolved_domain
        canonical = {**defaults, **dict(raw.get("copilot", {}).get("soc", {})), **raw.get("soc", {})}
        _, shared_dsn = cls._first_env(("GRAPH_DSN", "AGE_DSN"), env=source)
        _, shared_graph = cls._first_env(("GRAPH_NAME", "AGE_GRAPH_NAME"), env=source)
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
            profile=selected_profile,
            shared_dsn=_optional_text(shared_dsn or canonical.get("dsn")),
            shared_graph=str(shared_graph or canonical.get("graph", "soc_graph")),
            source_keys=tuple(sorted(source_keys.items())) + (("profile", (
                "argument:profile" if profile is not None else
                f"{domain.upper()}_PROFILE" if f"{domain.upper()}_PROFILE" in source else
                "GRAPH_PROFILE" if "GRAPH_PROFILE" in source else
                "COPILOT_PROFILE" if "COPILOT_PROFILE" in source else "default:profile"
            )),),
        )
        config.validate()
        return config

    @classmethod
    def _read_file(cls, domain: str, *, env: Mapping[str, str] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        package_root = Path(__file__).resolve().parents[2]
        candidates: list[Path] = []
        configured = (os.environ if env is None else env).get("GRAPH_CONFIG_PATH")
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
    def _first_env(names: tuple[str, ...], *, env: Mapping[str, str] | None = None) -> tuple[str | None, str | None]:
        source = os.environ if env is None else env
        for name in names:
            value = source.get(name)
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

    def validate(self, *, profile: str | None = None) -> None:
        selected_profile = resolve_profile(self.profile if profile is None else profile)
        if self.backend not in {"sqlite", "memory", "age", "dual_write"}:
            raise GraphConfigError(f"invalid backend '{self.backend}'")
        if self.expected_backend not in {"sqlite", "memory", "age", "dual_write"}:
            raise GraphConfigError(f"invalid expected backend '{self.expected_backend}'")
        if selected_profile == "production" and self.domain not in DOMAINS:
            raise GraphConfigError(f"unknown graph config domain '{self.domain}'")
        if self.expected_backend == "age" and self.backend == "sqlite":
            if selected_profile == "production":
                raise GraphConfigError(
                    f"expected backend age but resolved sqlite for domain '{self.domain}'"
                )
        if self.backend in {"age", "dual_write"}:
            if not self.dsn:
                raise GraphConfigError(f"missing AGE DSN for domain '{self.domain}'")
            if not self.graph:
                raise GraphConfigError(f"missing AGE graph for domain '{self.domain}'")
        if not self.domain or not self.graph:
            raise GraphConfigError("domain and graph must be non-empty")
        expected = f"{self.domain}:{self.graph}"
        if self.authorized != expected:
            raise GraphConfigError(f"domain/graph authorization mismatch: expected '{expected}'")
        require_shared_graph(
            backend=self.backend, graph=self.graph, domain=self.domain,
            profile=selected_profile, test_mode=self.active_test_mode or self.live_age_test,
        )

    def redacted_identity(self) -> GraphIdentity:
        """Probe the actual server, database and AGE graph, never a DSN-string hash."""
        from copilot_sdk.graph.production import probe_graph_identity

        if self.backend != "age" or not self.dsn:
            raise GraphConfigError("AGE DSN is required for a graph identity probe")
        return cast(GraphIdentity, probe_graph_identity(self.dsn, self.graph))

    def same_destination(self, other: "GraphConfig") -> bool:
        return self.redacted_identity().same_destination(other.redacted_identity())

    def require_shared_graph(self) -> GraphIdentity | None:
        """Validate policy and a real AGE connection against the canonical SOC destination."""
        self.validate()
        if self.profile != "production":
            return None
        identity = self.redacted_identity()
        if not self.shared_dsn or self.shared_graph != "soc_graph":
            raise GraphConfigError("canonical SOC AGE DSN + soc_graph must be configured")
        if self.dsn != self.shared_dsn or self.graph != self.shared_graph:
            from copilot_sdk.graph.production import probe_graph_identity

            if not identity.same_destination(probe_graph_identity(self.shared_dsn, self.shared_graph)):
                raise GraphConfigError("graph destination differs from canonical SOC database + soc_graph")
        return identity


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


__all__ = ["GraphConfig", "GraphConfigError", "GraphIdentity", "Profile", "resolve_profile", "require_shared_graph"]
