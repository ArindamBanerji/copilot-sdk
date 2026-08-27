"""DataOps active graph config, AGE adapter, and status endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import os
import re

from fastapi import APIRouter, Request

from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


DOMAIN = "dataops"
ENV_PREFIX = "DATAOPS"
ALLOWED_PRODUCT_AGE_GRAPHS = frozenset({"soc_graph"})
HISTORICAL_VISIBILITY_WARNING = (
    "Historical SQLite records are not visible in AGE-active mode unless migrated."
)
GENERIC_GRAPH_ENV_KEYS = (
    "GRAPH_BACKEND",
    "GRAPH_DSN",
    "GRAPH_NAME",
    "GRAPH_DOMAIN",
    "AGE_DSN",
    "AGE_GRAPH_NAME",
)

router = APIRouter(prefix="/api/dataops/graph", tags=["dataops-graph"])


class DataOpsActiveGraphConfigError(ValueError):
    """Raised when DataOps active graph config is unsafe."""


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise DataOpsActiveGraphConfigError(f"Invalid boolean value: {value!r}")


def _redact_secret(text: str | None) -> str | None:
    if text is None:
        return None
    redacted = str(text)
    redacted = re.sub(r"://([^:/?#]+):([^@/?#]+)@", r"://\1:***@", redacted)
    redacted = re.sub(
        r"(?i)(password|passwd|pwd|token|secret)=([^&\s]+)",
        r"\1=***",
        redacted,
    )
    return redacted


def _generic_graph_env_present(source: Mapping[str, str]) -> bool:
    return any(source.get(key) not in (None, "") for key in GENERIC_GRAPH_ENV_KEYS)


def _shared_graph_is_authorized(authorization: str | None, *, domain: str, graph: str) -> bool:
    """Require the exact writer-domain/shared-graph authorization pair."""
    return str(authorization or "").strip() == f"{domain}:{graph}"


_GRAPH_CONFIG_ENV_KEYS = (
    "GRAPH_BACKEND", "GRAPH_DSN", "AGE_DSN", "GRAPH_NAME", "AGE_GRAPH_NAME",
    "GRAPH_DOMAIN", "DATAOPS_ACTIVE_GRAPH_BACKEND", "DATAOPS_ACTIVE_AGE_DSN",
    "DATAOPS_ACTIVE_AGE_GRAPH", "DATAOPS_ACTIVE_AGE_DOMAIN",
    "DATAOPS_ACTIVE_AGE_TEST_MODE", "DATAOPS_ACTIVE_LIVE_AGE_TEST",
    "DATAOPS_SHARED_GRAPH_AUTHORIZED", "CI_ALLOW_SQLITE_FALLBACK",
)


def _load_dataops_graph_config(env: Mapping[str, str] | None) -> GraphConfig:
    """Load production config fail-closed, or an isolated compatibility mapping for tests."""
    if env is None:
        return GraphConfig.load("dataops")

    previous = {key: os.environ.get(key) for key in _GRAPH_CONFIG_ENV_KEYS}
    try:
        for key in _GRAPH_CONFIG_ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update(env)
        profile = "production"
        if "DATAOPS_ACTIVE_GRAPH_BACKEND" not in env:
            os.environ["DATAOPS_ACTIVE_GRAPH_BACKEND"] = "sqlite"
            os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
            profile = "development"
        if os.environ.get("DATAOPS_ACTIVE_GRAPH_BACKEND", "").strip().lower() == "age":
            if not os.environ.get("DATAOPS_ACTIVE_AGE_DSN", "").strip():
                raise GraphConfigError(
                    "DATAOPS_ACTIVE_AGE_DSN is required when DATAOPS_ACTIVE_GRAPH_BACKEND=age"
                )
            if not os.environ.get("DATAOPS_ACTIVE_AGE_GRAPH", "").strip():
                raise GraphConfigError(
                    "DATAOPS_ACTIVE_AGE_GRAPH is required when DATAOPS_ACTIVE_GRAPH_BACKEND=age"
                )
            if "DATAOPS_ACTIVE_AGE_DOMAIN" in env and not env.get("DATAOPS_ACTIVE_AGE_DOMAIN", "").strip():
                raise GraphConfigError("DATAOPS_ACTIVE_AGE_DOMAIN must not be blank")
        return GraphConfig.load("dataops", profile=profile)
    finally:
        for key in _GRAPH_CONFIG_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in previous.items():
            if value is not None:
                os.environ[key] = value


@dataclass(frozen=True)
class DataOpsActiveGraphConfig:
    requested_backend: str = "sqlite"
    dsn: str | None = None
    graph: str | None = None
    domain: str = DOMAIN
    test_mode: bool = False
    live_age_test: bool = False
    shared_graph_authorization: str | None = None
    ignored_generic_graph_env: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "DataOpsActiveGraphConfig":
        source = os.environ if env is None else env
        try:
            graph_config = _load_dataops_graph_config(env)
        except GraphConfigError as exc:
            message = str(exc)
            if message.startswith("invalid backend"):
                message = "DATAOPS_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
            raise DataOpsActiveGraphConfigError(message) from exc
        config = cls(
            requested_backend=graph_config.backend,
            dsn=graph_config.dsn,
            graph=graph_config.graph,
            domain=graph_config.domain,
            test_mode=graph_config.active_test_mode,
            live_age_test=graph_config.live_age_test,
            shared_graph_authorization=(
                graph_config.authorized if graph_config.graph.strip() == "soc_graph" else None
            ),
            ignored_generic_graph_env=_generic_graph_env_present(source),
        )
        config.validate(source)
        return config

    def validate(self, source: Mapping[str, str] | None = None) -> None:
        if self.requested_backend not in {"sqlite", "age"}:
            raise DataOpsActiveGraphConfigError(
                "DATAOPS_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
            )
        if self.requested_backend == "sqlite":
            return

        source = source or {}
        if not self.domain or not self.domain.strip():
            raise DataOpsActiveGraphConfigError("DATAOPS_ACTIVE_AGE_DOMAIN must not be blank")
        if self.domain != DOMAIN:
            raise DataOpsActiveGraphConfigError("DATAOPS_ACTIVE_AGE_DOMAIN must be 'dataops'")
        if not self.dsn or not self.dsn.strip():
            raise DataOpsActiveGraphConfigError(
                "DATAOPS_ACTIVE_AGE_DSN is required when DATAOPS_ACTIVE_GRAPH_BACKEND=age"
            )
        if not self.graph or not self.graph.strip():
            raise DataOpsActiveGraphConfigError(
                "DATAOPS_ACTIVE_AGE_GRAPH is required when DATAOPS_ACTIVE_GRAPH_BACKEND=age"
            )

        graph = self.graph.strip()
        soc_graph_authorized = _shared_graph_is_authorized(
            self.shared_graph_authorization, domain=self.domain, graph=graph
        )
        if graph == "soc_graph" and not soc_graph_authorized:
            raise DataOpsActiveGraphConfigError(
                "soc_graph authorization is derived from the dataops domain and graph"
            )
        if self.test_mode:
            if not graph.startswith("protocol_v2_test"):
                raise DataOpsActiveGraphConfigError(
                    "DataOps active AGE test mode is allowed only for protocol_v2_test* graphs"
                )
            return
        if graph.startswith("protocol_v2_test"):
            raise DataOpsActiveGraphConfigError(
                "protocol_v2_test* graphs require DATAOPS_ACTIVE_AGE_TEST_MODE=1"
            )
        if graph not in ALLOWED_PRODUCT_AGE_GRAPHS and not soc_graph_authorized:
            raise DataOpsActiveGraphConfigError(
                "DataOps active AGE product graph must be reviewed and allow-listed"
            )
        if not self.live_age_test and not soc_graph_authorized:
            raise DataOpsActiveGraphConfigError(
                "DataOps product AGE writes remain blocked; use protocol_v2_test* test mode"
            )

    def graph_kind(self) -> str:
        if self.requested_backend != "age" or not self.graph:
            return "none"
        return "test" if self.graph.strip().startswith("protocol_v2_test") else "product"

    def safe_summary(self) -> dict[str, Any]:
        return {
            "requested_backend": self.requested_backend,
            "dsn": _redact_secret(self.dsn),
            "graph": self.graph,
            "domain": self.domain,
            "test_mode": self.test_mode,
            "live_age_test": self.live_age_test,
            "shared_graph_authorization": self.shared_graph_authorization,
            "ignored_generic_graph_env": self.ignored_generic_graph_env,
        }


class DataOpsActiveAGEGraphStore:
    """Active AGE adapter preserving governed Decision write semantics."""

    domain = DOMAIN

    def __init__(self, store: Any, *, active_phase: str = "test_mode") -> None:
        self._store = store
        self.active_phase = active_phase

    def generate_decision_id(self, domain: str) -> str:
        """DataOps active AGE IDs use the DOPS- prefix."""
        import uuid
        return f"DOPS-{uuid.uuid4().hex[:12]}"

    def write_decision(
        self,
        domain: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if domain != DOMAIN:
            raise ValueError("DataOps active AGE store only accepts domain 'dataops'")
        preset = DataOpsPreset()
        decision_metadata = dict(metadata or {})
        decision_id = str(decision_metadata.get("decision_id") or "").strip()
        if not decision_id:
            raise ValueError("DataOps active AGE write_decision requires metadata.decision_id")

        factor_names = list(preset.shape.factor_names)
        if isinstance(decision_metadata.get("factor_vector"), list):
            factor_vector = [float(value) for value in decision_metadata["factor_vector"]]
        else:
            factor_vector = [float(factors.get(name, 0.5)) for name in factor_names]
        recommended_index = int(
            decision_metadata.get(
                "recommended_index",
                preset.shape.action_names.index(action),
            )
        )
        category_index = int(
            decision_metadata.get(
                "category_index",
                preset.shape.category_names.index(category),
            )
        )
        probabilities = decision_metadata.get("probabilities")
        if not isinstance(probabilities, list):
            probabilities = [
                1.0 if index == recommended_index else 0.0
                for index in range(preset.shape.n_actions)
            ]

        self._store.write_governed_decision(
            decision_id=decision_id,
            domain=DOMAIN,
            category=category,
            category_index=category_index,
            recommended_action=action,
            recommended_index=recommended_index,
            confidence=confidence,
            probabilities=[float(value) for value in probabilities],
            factor_vector=factor_vector,
            factor_names=factor_names,
            source="dataops_active_age_score",
            scorer_version=f"dataops_active_age_{self.active_phase}",
            preset_version="dataops",
            factor_schema_version="dataops_factor_schema_v1",
            metadata={
                **decision_metadata,
                "active_age": True,
                "active_age_phase": self.active_phase,
            },
        )
        return decision_id

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)


def initialize_dataops_active_graph_config(
    env: Mapping[str, str] | None = None,
) -> DataOpsActiveGraphConfig:
    return DataOpsActiveGraphConfig.from_env(env)


def create_dataops_active_graph_store(
    config: DataOpsActiveGraphConfig,
    *,
    store_factory: Any | None = None,
) -> Any | None:
    if config.requested_backend != "age":
        return None
    config.validate({"DATAOPS_ACTIVE_GRAPH_BACKEND": "age"})
    try:
        require_shared_graph(
            backend=config.requested_backend,
            graph=config.graph,
            domain=DOMAIN,
            profile="test" if (config.test_mode or config.live_age_test) else "production",
            test_mode=config.test_mode or config.live_age_test,
        )
    except GraphConfigError as exc:
        raise DataOpsActiveGraphConfigError(str(exc)) from exc
    shared_soc_graph = (
        config.graph is not None
        and _shared_graph_is_authorized(
            config.shared_graph_authorization, domain=config.domain, graph=config.graph.strip()
        )
    )
    if config.graph_kind() != "test" and not config.live_age_test and not shared_soc_graph:
        raise DataOpsActiveGraphConfigError(
            "DataOps product AGE writes remain blocked; use protocol_v2_test* test mode"
        )
    factory = store_factory
    if factory is None:
        from copilot_sdk.graph.factory import create_graph_store

        factory = create_graph_store
    factory_args: dict[str, Any] = {
        "backend": "age", "domain": config.domain, "dsn": config.dsn,
        "graph_name": config.graph, "env": {}, "test_mode": config.test_mode,
    }
    if shared_soc_graph:
        factory_args["shared_graph_authorization"] = config.shared_graph_authorization
    store = factory(**factory_args)
    phase = "shared_graph" if shared_soc_graph else ("test_mode" if config.graph_kind() == "test" else "live_age_test")
    return DataOpsActiveAGEGraphStore(store, active_phase=phase)


def build_dataops_graph_status(app_state: Any) -> dict[str, Any]:
    config = getattr(app_state, "dataops_active_graph_config", None)
    if not isinstance(config, DataOpsActiveGraphConfig):
        config = DataOpsActiveGraphConfig.from_env({})
    active_store = getattr(app_state, "dataops_selected_graph_store", None)
    age_active = bool(
        config.requested_backend == "age" and isinstance(active_store, DataOpsActiveAGEGraphStore)
    )
    requested_age = config.requested_backend == "age"
    graph_kind = config.graph_kind()
    product_graph_allowed = (
        None
        if not requested_age or graph_kind != "product"
        else str(config.graph).strip() in ALLOWED_PRODUCT_AGE_GRAPHS
    )
    return {
        "active_backend": "age" if age_active else "sqlite",
        "requested_backend": config.requested_backend,
        "sqlite_authoritative": not age_active,
        "age_active": age_active,
        "active_graph_name": config.graph if requested_age else None,
        "graph_kind": "sqlite" if not requested_age else graph_kind,
        "active_domain": config.domain,
        "active_test_mode": config.test_mode,
        "active_live_age_test": config.live_age_test,
        "ignored_generic_graph_env": config.ignored_generic_graph_env,
        "product_graph_allow_list": sorted(ALLOWED_PRODUCT_AGE_GRAPHS),
        "product_graph_allowed": product_graph_allowed,
        "migration_backfill_status": "not_in_scope",
        "receipt_mapping_status": "excluded_first_cutover",
        "evidence_receipt_mapping_status": "design_required",
        "operational_graph_client_status": "separate_dataops_graph_client",
        "historical_visibility_warning": HISTORICAL_VISIBILITY_WARNING,
        "rollback_instructions": [
            "Unset DATAOPS_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
            "Restart DataOps.",
            "Rollback routes new scorer writes to SQLite; it does not reconcile AGE data.",
        ],
        "cutover_ready": bool(age_active and graph_kind == "test"),
        "new_decision_outcome_writes_ready": bool(age_active and graph_kind == "test"),
        "full_audit_memory_ready": False,
        "migration_complete": False,
        "evidence_receipt_ready": False,
        "warnings": [
            "DataOps active AGE test mode is enabled for new scorer Decision/Outcome writes."
            if age_active
            else "DataOps SQLite remains authoritative for scorer decisions.",
            "Operational DataOpsGraphClient queries are configured separately.",
            "Historical SQLite migration/backfill is not in scope.",
            HISTORICAL_VISIBILITY_WARNING,
            "EvidenceReceipt mapping is excluded from first cutover.",
        ],
        "cutover_ready_flags": {
            "backend_guard_valid": True,
            "graph_guard_valid": True,
            "test_mode_active": bool(age_active and graph_kind == "test"),
            "product_graph_allow_listed": bool(product_graph_allowed),
            "operational_graph_separated": True,
            "rollback_proof_complete": bool(age_active and graph_kind == "test"),
            "evidence_receipt_mapping_complete": False,
            "migration_backfill_in_scope": False,
            "active_age_writes_enabled": age_active,
            "product_claim_allowed": False,
        },
        "last_error": None,
    }


@router.get("/status")
def graph_status(request: Request) -> dict[str, Any]:
    return build_dataops_graph_status(request.app.state)


__all__ = [
    "ALLOWED_PRODUCT_AGE_GRAPHS",
    "DataOpsActiveAGEGraphStore",
    "DataOpsActiveGraphConfig",
    "DataOpsActiveGraphConfigError",
    "build_dataops_graph_status",
    "create_dataops_active_graph_store",
    "initialize_dataops_active_graph_config",
    "router",
]
