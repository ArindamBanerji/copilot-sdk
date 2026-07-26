"""GraphStore factory with fail-closed configuration-driven AGE selection."""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Mapping, cast

from copilot_sdk.config import GraphConfig, GraphConfigError
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

logger = logging.getLogger(__name__)

_VALID_BACKENDS = {"sqlite", "age", "dual_write"}


def _env_value(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key)
    if value is None:
        return None
    return str(value)


def _normalize_backend(value: str | None) -> str:
    if value is None or not str(value).strip():
        raise GraphConfigError(
            "graph backend is required; pass backend explicitly or provide a domain "
            "for GraphConfig resolution"
        )
    backend = str(value).strip().lower()
    if backend not in _VALID_BACKENDS:
        raise ValueError(
            f"invalid graph backend {value!r}; expected one of {sorted(_VALID_BACKENDS)}"
        )
    return backend


def _resolve_aliased_env(
    env: Mapping[str, str],
    canonical_key: str,
    alias_key: str,
    explicit_value: str | None,
) -> str | None:
    if explicit_value is not None:
        return str(explicit_value)

    canonical = _env_value(env, canonical_key)
    alias = _env_value(env, alias_key)
    if canonical is not None and alias is not None and canonical != alias:
        raise ValueError(
            f"conflicting {canonical_key} and {alias_key} values; pass an explicit "
            "argument to override env"
        )
    return canonical if canonical is not None else alias


def _resolve_sqlite_path(
    *,
    db_path: str | Path | None,
    domain: str,
    env: Mapping[str, str],
) -> str | Path:
    if db_path is not None:
        return db_path
    ci_data_dir = _env_value(env, "CI_DATA_DIR")
    if ci_data_dir:
        return Path(ci_data_dir) / f"{domain}.db"
    return ":memory:"


def _validate_graph_domain(env: Mapping[str, str], domain: str) -> None:
    env_domain = _env_value(env, "GRAPH_DOMAIN")
    if env_domain is not None and env_domain != domain:
        raise ValueError(
            f"GRAPH_DOMAIN {env_domain!r} does not match requested domain {domain!r}"
        )


def _load_age_adapter():
    try:
        module = importlib.import_module("ci_platform.graph.age_sdk_adapter")
    except ImportError as exc:
        raise RuntimeError(
            "AGE graph backend requires ci-platform with "
            "ci_platform.graph.age_sdk_adapter importable"
        ) from exc
    try:
        return module.AGEGraphStoreAdapter
    except AttributeError as exc:
        raise RuntimeError(
            "AGE graph backend requires ci_platform.graph.age_sdk_adapter."
            "AGEGraphStoreAdapter"
        ) from exc


def _validate_age_graph_name(
    graph_name: str | None,
    *,
    test_mode: bool,
    read_only_soc_projection: bool,
    domain: str | None = None,
    shared_graph_authorization: str | None = None,
) -> str:
    graph = str(graph_name or "").strip()
    if not graph:
        raise ValueError("AGE graph backend requires explicit non-blank GRAPH_NAME")
    authorized_pair = f"{domain}:{graph}" if domain else ""
    authorized_pairs = {
        pair.strip()
        for pair in str(shared_graph_authorization or "").split(",")
        if pair.strip()
    }
    if graph == "soc_graph" and authorized_pair not in authorized_pairs:
        raise ValueError("soc_graph is forbidden for generic GraphStore factory contexts")
    if graph.startswith("protocol_v2_test") and not test_mode:
        raise ValueError("protocol_v2_test* AGE graphs require test_mode=True")
    return graph


def create_graph_store(
    *,
    backend: str | None = None,
    domain: str | None = None,
    db_path: str | Path | None = None,
    decision_id_prefix: str = "",
    dsn: str | None = None,
    graph_name: str | None = None,
    env: Mapping[str, str] | None = None,
    test_mode: bool = False,
    read_only_soc_projection: bool = False,
    shared_graph_authorization: str | None = None,
    profile: str = "production",
) -> GraphStore:
    """Create a GraphStore.

    With no explicit backend, DSN, or graph, the domain's typed GraphConfig is
    authoritative. Explicit arguments remain available for tests and migration
    tooling. AGE and dual-write configurations fail before store construction
    when their required connection settings are absent.
    """

    env_map: Mapping[str, str] = os.environ if env is None else env
    config: GraphConfig | None = None
    config_driven = backend is None and dsn is None and graph_name is None
    if config_driven:
        if not domain:
            raise GraphConfigError(
                "create_graph_store requires domain when backend, dsn, and graph "
                "are not explicitly provided"
            )
        config = GraphConfig.load(domain, profile=profile)
        selected_backend = _normalize_backend(config.backend)
        selected_domain = config.domain
        if (
            profile == "production"
            and config.expected_backend == "age"
            and selected_backend == "sqlite"
        ):
            raise GraphConfigError(
                f"production domain '{domain}' resolved SQLite while AGE is expected"
            )
        dsn = config.dsn
        graph_name = config.graph
        if shared_graph_authorization is None:
            shared_graph_authorization = config.authorized
        test_mode = test_mode or config.active_test_mode
    else:
        selected_backend = _normalize_backend(
            backend if backend is not None else _env_value(env_map, "GRAPH_BACKEND")
        )
        selected_domain = str(domain or "graph")
    _validate_graph_domain(env_map, selected_domain)

    if selected_backend == "sqlite":
        sqlite_path = _resolve_sqlite_path(
            db_path=db_path,
            domain=selected_domain,
            env=env_map,
        )
        logger.info(
            "creating SQLite GraphStore for domain=%s path=%s",
            selected_domain,
            sqlite_path,
        )
        return SQLiteGraphStore(
            sqlite_path,
            domain=selected_domain,
            decision_id_prefix=decision_id_prefix,
        )

    if selected_backend == "dual_write":
        sqlite_path = _resolve_sqlite_path(
            db_path=db_path,
            domain=selected_domain,
            env=env_map,
        )
        primary = SQLiteGraphStore(
            sqlite_path,
            domain=selected_domain,
            decision_id_prefix=decision_id_prefix,
        )
        selected_dsn = _resolve_aliased_env(env_map, "GRAPH_DSN", "AGE_DSN", dsn)
        if not selected_dsn or not str(selected_dsn).strip():
            primary.close()
            raise GraphConfigError(
                "dual_write backend requires an AGE DSN; set GRAPH_DSN or "
                f"{selected_domain.upper()}_ACTIVE_AGE_DSN"
            )
        selected_graph = _resolve_aliased_env(
            env_map,
            "GRAPH_NAME",
            "AGE_GRAPH_NAME",
            graph_name,
        )
        if selected_graph is None:
            selected_graph = _env_value(env_map, "GRAPH_DOMAIN")
        dual_write_authorization = (
            shared_graph_authorization
            if shared_graph_authorization is not None
            else _env_value(env_map, "SHARED_GRAPH_AUTHORIZED")
        )
        if str(selected_graph or "").strip() == "soc_graph":
            required_pair = f"{selected_domain}:soc_graph"
            authorized_pairs = {
                pair.strip()
                for pair in str(dual_write_authorization or "").split(",")
                if pair.strip()
            }
            if required_pair not in authorized_pairs:
                primary.close()
                raise ValueError(
                    f"soc_graph requires SHARED_GRAPH_AUTHORIZED={required_pair}"
                )
        selected_graph = _validate_age_graph_name(
            selected_graph,
            test_mode=test_mode,
            read_only_soc_projection=read_only_soc_projection,
            domain=selected_domain,
            shared_graph_authorization=dual_write_authorization,
        )
        from copilot_sdk.graph.dual_write_store import DualWriteStore

        adapter_cls = _load_age_adapter()
        secondary = cast(GraphStore, adapter_cls(dsn=str(selected_dsn), graph_name=selected_graph))
        logger.info(
            "creating dual-write GraphStore for domain=%s path=%s graph_name=%s",
            selected_domain,
            sqlite_path,
            selected_graph,
        )
        outbox_path = Path(sqlite_path).parent / f"{selected_domain}_dual_write_outbox.db"
        return DualWriteStore(primary, secondary, outbox_path=str(outbox_path))

    if not selected_domain.strip():
        raise ValueError("AGE graph backend requires explicit non-blank domain")

    selected_dsn = _resolve_aliased_env(env_map, "GRAPH_DSN", "AGE_DSN", dsn)
    if not selected_dsn or not str(selected_dsn).strip():
        raise ValueError("AGE graph backend requires explicit GRAPH_DSN")

    selected_graph = _resolve_aliased_env(
        env_map,
        "GRAPH_NAME",
        "AGE_GRAPH_NAME",
        graph_name,
    )
    selected_graph = _validate_age_graph_name(
        selected_graph,
        test_mode=test_mode,
        read_only_soc_projection=read_only_soc_projection,
        domain=selected_domain,
        shared_graph_authorization=shared_graph_authorization,
    )

    adapter_cls = _load_age_adapter()
    logger.info(
        "creating AGE GraphStore for domain=%s graph_name=%s read_only_soc_projection=%s",
        selected_domain,
        selected_graph,
        read_only_soc_projection,
    )
    return cast(GraphStore, adapter_cls(dsn=str(selected_dsn), graph_name=selected_graph))
