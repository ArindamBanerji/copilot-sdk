"""Production-profile graph contract tests for JM Phase 01A/01B."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import uuid4

import pytest

from copilot_sdk.config import GraphConfig, GraphConfigError


def _local_config(backend: str, *, profile: str = "production") -> GraphConfig:
    config = GraphConfig.load(
        "trading",
        profile="test",
        env={},
        overrides={"backend": "sqlite", "expected_backend": "sqlite"},
    )
    return replace(
        config,
        backend=backend,
        expected_backend=backend,
        dsn=None,
        profile=profile,
    )


def test_production_rejects_sqlite_primary() -> None:
    with pytest.raises(GraphConfigError, match="production requires AGE primary"):
        _local_config("sqlite").validate()


def test_production_rejects_inmemory() -> None:
    with pytest.raises(GraphConfigError, match="production requires AGE primary"):
        _local_config("memory").validate()


def test_production_requires_soc_graph() -> None:
    config = _local_config("sqlite")
    invalid = replace(
        config,
        backend="age",
        expected_backend="age",
        dsn="host=placeholder dbname=placeholder",
        graph="private_graph",
        profile="production",
    )
    with pytest.raises(GraphConfigError, match="soc_graph"):
        invalid.validate()


def test_test_profile_allows_sqlite() -> None:
    config = replace(
        _local_config("sqlite", profile="test"),
        backend="sqlite",
        expected_backend="sqlite",
        dsn=None,
    )
    config.validate()
    assert config.profile == "test"
    assert config.backend == "sqlite"


@pytest.mark.age_required
def test_domain_collision_isolation(age_contract_store: Any) -> None:
    decision_id = f"jm-contract-{uuid4().hex}"
    for domain, category in (("trading", "trading_only"), ("dataops", "dataops_only")):
        age_contract_store.write_decision(
            domain=domain,
            category=category,
            action="review",
            confidence=0.8,
            factors={"signal": 0.7},
            metadata={"decision_id": decision_id},
        )

    trading = age_contract_store.get_decision(decision_id, domain="trading")
    dataops = age_contract_store.get_decision(decision_id, domain="dataops")
    assert trading is not None and trading["category"] == "trading_only"
    assert dataops is not None and dataops["category"] == "dataops_only"


@pytest.mark.age_required
def test_write_requires_domain(age_contract_store: Any) -> None:
    from ci_platform.graph.age_graph_store import AGEGraphStore

    with pytest.raises(TypeError, match="domain"):
        AGEGraphStore.write_decision(
            object.__new__(AGEGraphStore),  # type: ignore[arg-type]
            category="trading_only",
            action="review",
            confidence=0.8,
            factors={},
        )  # type: ignore[call-arg]


@pytest.mark.age_required
def test_cross_domain_requires_authorization(age_contract_store: Any) -> None:
    with pytest.raises(PermissionError, match="not authorized"):
        age_contract_store._store.query_cross_domain_context(
            "missing-entity",
            source_domain="trading",
            target_domain="dataops",
            principal="contract-test",
        )
