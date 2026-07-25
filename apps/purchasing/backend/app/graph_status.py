"""Purchasing active graph config, AGE adapter, and status endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import os
import re

from fastapi import APIRouter, Request

from copilot_sdk.config import GraphConfig, GraphConfigError
from app.factors import compute_factors
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


DOMAIN = "purchasing"
ENV_PREFIX = "PURCHASING"
ALLOWED_PRODUCT_AGE_GRAPHS = frozenset({"governed_copilot_graph"})
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

router = APIRouter(prefix="/api/purchasing/graph", tags=["purchasing-graph"])


class PurchasingActiveGraphConfigError(ValueError):
    """Raised when Purchasing active graph config is unsafe."""


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise PurchasingActiveGraphConfigError(f"Invalid boolean value: {value!r}")


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
    "GRAPH_DOMAIN", "PURCHASING_ACTIVE_GRAPH_BACKEND", "PURCHASING_ACTIVE_AGE_DSN",
    "PURCHASING_ACTIVE_AGE_GRAPH", "PURCHASING_ACTIVE_AGE_DOMAIN",
    "PURCHASING_ACTIVE_AGE_TEST_MODE", "PURCHASING_SHADOW_AGE",
    "PURCHASING_SHARED_GRAPH_AUTHORIZED",
    "CI_ALLOW_SQLITE_FALLBACK",
)


def _load_purchasing_graph_config(env: Mapping[str, str] | None) -> GraphConfig:
    """Load production config fail-closed, or an isolated compatibility mapping for tests."""
    if env is None:
        return GraphConfig.load("purchasing")

    previous = {key: os.environ.get(key) for key in _GRAPH_CONFIG_ENV_KEYS}
    try:
        for key in _GRAPH_CONFIG_ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update(env)
        profile = "production"
        if "PURCHASING_ACTIVE_GRAPH_BACKEND" not in env:
            os.environ["PURCHASING_ACTIVE_GRAPH_BACKEND"] = "sqlite"
            os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
            profile = "development"
        if os.environ.get("PURCHASING_ACTIVE_GRAPH_BACKEND", "").strip().lower() == "age":
            if not os.environ.get("PURCHASING_ACTIVE_AGE_DSN", "").strip():
                raise GraphConfigError(
                    "PURCHASING_ACTIVE_AGE_DSN is required when PURCHASING_ACTIVE_GRAPH_BACKEND=age"
                )
            if not os.environ.get("PURCHASING_ACTIVE_AGE_GRAPH", "").strip():
                raise GraphConfigError(
                    "PURCHASING_ACTIVE_AGE_GRAPH is required when PURCHASING_ACTIVE_GRAPH_BACKEND=age"
                )
            if "PURCHASING_ACTIVE_AGE_DOMAIN" in env and not env.get("PURCHASING_ACTIVE_AGE_DOMAIN", "").strip():
                raise GraphConfigError("PURCHASING_ACTIVE_AGE_DOMAIN must not be blank")
        return GraphConfig.load("purchasing", profile=profile)
    finally:
        for key in _GRAPH_CONFIG_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in previous.items():
            if value is not None:
                os.environ[key] = value


@dataclass(frozen=True)
class PurchasingActiveGraphConfig:
    requested_backend: str = "sqlite"
    dsn: str | None = None
    graph: str | None = None
    domain: str = DOMAIN
    test_mode: bool = False
    shared_graph_authorization: str | None = None
    ignored_generic_graph_env: bool = False

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "PurchasingActiveGraphConfig":
        source = os.environ if env is None else env
        try:
            graph_config = _load_purchasing_graph_config(env)
        except GraphConfigError as exc:
            message = str(exc)
            if message.startswith("invalid backend"):
                message = "PURCHASING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
            raise PurchasingActiveGraphConfigError(message) from exc
        config = cls(
            requested_backend=graph_config.backend,
            dsn=graph_config.dsn,
            graph=graph_config.graph,
            domain=graph_config.domain,
            test_mode=graph_config.active_test_mode,
            shared_graph_authorization=(
                graph_config.authorized if graph_config.graph.strip() == "soc_graph" else None
            ),
            ignored_generic_graph_env=_generic_graph_env_present(source),
        )
        config.validate(source)
        return config

    def validate(self, source: Mapping[str, str] | None = None) -> None:
        if self.requested_backend not in {"sqlite", "age"}:
            raise PurchasingActiveGraphConfigError(
                "PURCHASING_ACTIVE_GRAPH_BACKEND must be 'sqlite' or 'age'"
            )
        if self.requested_backend == "sqlite":
            return

        source = source or {}
        if _parse_bool(source.get("PURCHASING_SHADOW_AGE"), default=False):
            raise PurchasingActiveGraphConfigError(
                "PURCHASING_SHADOW_AGE=1 conflicts with active AGE"
            )
        if not self.domain or not self.domain.strip():
            raise PurchasingActiveGraphConfigError("PURCHASING_ACTIVE_AGE_DOMAIN must not be blank")
        if self.domain != DOMAIN:
            raise PurchasingActiveGraphConfigError(
                "PURCHASING_ACTIVE_AGE_DOMAIN must be 'purchasing'"
            )
        if not self.dsn or not self.dsn.strip():
            raise PurchasingActiveGraphConfigError(
                "PURCHASING_ACTIVE_AGE_DSN is required when PURCHASING_ACTIVE_GRAPH_BACKEND=age"
            )
        if not self.graph or not self.graph.strip():
            raise PurchasingActiveGraphConfigError(
                "PURCHASING_ACTIVE_AGE_GRAPH is required when PURCHASING_ACTIVE_GRAPH_BACKEND=age"
            )

        graph = self.graph.strip()
        soc_graph_authorized = _shared_graph_is_authorized(
            self.shared_graph_authorization, domain=self.domain, graph=graph
        )
        if graph == "soc_graph" and not soc_graph_authorized:
            raise PurchasingActiveGraphConfigError(
                "soc_graph authorization is derived from the purchasing domain and graph"
            )
        if self.test_mode:
            if not graph.startswith("protocol_v2_test"):
                raise PurchasingActiveGraphConfigError(
                    "Purchasing active AGE test mode is allowed only for protocol_v2_test* graphs"
                )
            return
        if graph.startswith("protocol_v2_test"):
            raise PurchasingActiveGraphConfigError(
                "protocol_v2_test* graphs require PURCHASING_ACTIVE_AGE_TEST_MODE=1"
            )
        if graph not in ALLOWED_PRODUCT_AGE_GRAPHS and not soc_graph_authorized:
            raise PurchasingActiveGraphConfigError(
                "Purchasing active AGE product graph must be reviewed and allow-listed"
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
            "shared_graph_authorization": self.shared_graph_authorization,
            "ignored_generic_graph_env": self.ignored_generic_graph_env,
        }


class PurchasingActiveAGEGraphStore:
    """Active AGE adapter preserving governed Decision write semantics."""

    domain = DOMAIN

    def __init__(self, store: Any, *, active_phase: str = "test_mode") -> None:
        self._store = store
        self.active_phase = active_phase

    def generate_decision_id(self, domain: str) -> str:
        """Purchasing active AGE IDs use the PUR- prefix."""
        import uuid
        return f"PUR-{uuid.uuid4().hex[:12]}"

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
            raise ValueError("Purchasing active AGE store only accepts domain 'purchasing'")
        preset = PurchasingPreset()
        decision_metadata = dict(metadata or {})
        decision_id = str(decision_metadata.get("decision_id") or "").strip()
        if not decision_id:
            raise ValueError("Purchasing active AGE write_decision requires metadata.decision_id")

        factor_names = list(preset.shape.factor_names)
        if isinstance(decision_metadata.get("factor_vector"), list):
            factor_vector = [float(value) for value in decision_metadata["factor_vector"]]
        else:
            computed = compute_factors(_factor_context(decision_metadata))
            merged = {**computed, **_request_factor_overrides(factors)}
            factor_vector = [float(merged.get(name, 0.5)) for name in factor_names]
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
            source="purchasing_active_age_score",
            scorer_version=f"purchasing_active_age_{self.active_phase}",
            preset_version="purchasing",
            factor_schema_version="purchasing_factor_schema_v1",
            metadata={
                **decision_metadata,
                "active_age": True,
                "active_age_phase": self.active_phase,
            },
        )
        return decision_id

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)


def _factor_context(order: dict[str, Any]) -> dict[str, Any]:
    context = {
        "forecast_demand": order.get("forecast_demand") or order.get("expected_demand"),
        "par_level": order.get("par_level"),
        "day_of_week": _day_index(order.get("day_of_week")),
        "weather_score": order.get("weather_score") or order.get("weather_forecast"),
        "weather": order.get("weather"),
        "event_flag": order.get("event_flag"),
        "event_covers": order.get("event_covers"),
        "normal_covers": order.get("normal_covers"),
        "waste_pct": order.get("waste_pct") or order.get("historical_waste"),
        "lead_time_days": order.get("lead_time_days") or order.get("supplier_lead_time"),
        "price_change_count": order.get("price_change_count"),
        "months_tracked": order.get("months_tracked"),
    }
    return {key: value for key, value in context.items() if value is not None}


def _request_factor_overrides(factors: dict[str, Any]) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for key, value in factors.items():
        if value is not None:
            overrides[key] = float(value)
    return overrides


def _day_index(value: Any) -> Any:
    if isinstance(value, str):
        lookup = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return lookup.get(value.strip().lower())
    return value


def initialize_purchasing_active_graph_config(
    env: Mapping[str, str] | None = None,
) -> PurchasingActiveGraphConfig:
    return PurchasingActiveGraphConfig.from_env(env)


def create_purchasing_active_graph_store(
    config: PurchasingActiveGraphConfig,
    *,
    store_factory: Any | None = None,
) -> Any | None:
    if config.requested_backend != "age":
        return None
    if _parse_bool(os.environ.get("PURCHASING_SHADOW_AGE"), default=False):
        raise PurchasingActiveGraphConfigError(
            "PURCHASING_SHADOW_AGE=1 conflicts with active AGE"
        )
    config.validate({"PURCHASING_ACTIVE_GRAPH_BACKEND": "age"})
    shared_soc_graph = (
        config.graph is not None
        and _shared_graph_is_authorized(
            config.shared_graph_authorization, domain=config.domain, graph=config.graph.strip()
        )
    )
    if config.graph_kind() != "test" and not shared_soc_graph:
        raise PurchasingActiveGraphConfigError(
            "Purchasing product AGE writes remain blocked; use protocol_v2_test* test mode"
        )
    factory = store_factory
    if factory is None:
        from copilot_sdk.graph.factory import create_graph_store

        factory = create_graph_store
    factory_args = {
        "backend": "age", "domain": config.domain, "dsn": config.dsn,
        "graph_name": config.graph, "env": {}, "test_mode": config.test_mode,
    }
    if shared_soc_graph:
        factory_args["shared_graph_authorization"] = config.shared_graph_authorization
    store = factory(**factory_args)
    return PurchasingActiveAGEGraphStore(store, active_phase="shared_graph" if shared_soc_graph else "test_mode")


def build_purchasing_graph_status(app_state: Any) -> dict[str, Any]:
    config = getattr(app_state, "purchasing_active_graph_config", None)
    if not isinstance(config, PurchasingActiveGraphConfig):
        config = PurchasingActiveGraphConfig.from_env({})
    active_store = getattr(app_state, "purchasing_selected_graph_store", None)
    age_active = bool(
        config.requested_backend == "age"
        and isinstance(active_store, PurchasingActiveAGEGraphStore)
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
        "shadow_enabled": False,
        "shadow_allowed": not requested_age,
        "active_graph_name": config.graph if requested_age else None,
        "graph_kind": "sqlite" if not requested_age else graph_kind,
        "active_domain": config.domain,
        "active_test_mode": config.test_mode,
        "ignored_generic_graph_env": config.ignored_generic_graph_env,
        "product_graph_allow_list": sorted(ALLOWED_PRODUCT_AGE_GRAPHS),
        "product_graph_allowed": product_graph_allowed,
        "migration_backfill_status": "not_in_scope",
        "receipt_mapping_status": "excluded_first_cutover",
        "evidence_receipt_mapping_status": "design_required",
        "historical_visibility_warning": HISTORICAL_VISIBILITY_WARNING,
        "rollback_instructions": [
            "Unset PURCHASING_ACTIVE_GRAPH_BACKEND or set it to sqlite.",
            "Restart Purchasing.",
            "Rollback routes new writes to SQLite; it does not reconcile AGE data.",
        ],
        "cutover_ready": bool(age_active and graph_kind == "test"),
        "new_decision_outcome_writes_ready": bool(age_active and graph_kind == "test"),
        "full_audit_memory_ready": False,
        "migration_complete": False,
        "evidence_receipt_ready": False,
        "warnings": [
            "Purchasing active AGE test mode is enabled for new Decision/Outcome writes."
            if age_active
            else "Purchasing SQLite remains authoritative.",
            "Historical SQLite migration/backfill is not in scope.",
            HISTORICAL_VISIBILITY_WARNING,
            "EvidenceReceipt mapping is excluded from first cutover.",
        ],
        "cutover_ready_flags": {
            "backend_guard_valid": True,
            "graph_guard_valid": True,
            "test_mode_active": bool(age_active and graph_kind == "test"),
            "product_graph_allow_listed": bool(product_graph_allowed),
            "true_parallel_gate_complete": False,
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
    return build_purchasing_graph_status(request.app.state)


__all__ = [
    "ALLOWED_PRODUCT_AGE_GRAPHS",
    "PurchasingActiveAGEGraphStore",
    "PurchasingActiveGraphConfig",
    "PurchasingActiveGraphConfigError",
    "build_purchasing_graph_status",
    "create_purchasing_active_graph_store",
    "initialize_purchasing_active_graph_config",
    "router",
]
