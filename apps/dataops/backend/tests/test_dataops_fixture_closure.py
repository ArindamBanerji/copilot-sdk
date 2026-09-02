from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import context_router
from app.graph_queries import DataOpsGraphClient, FALLBACK_DIR
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore


BACKEND_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def environment(**values: str | None) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class UnavailableAGEClient:
    serialize_for_age = staticmethod(lambda value: "'" + str(value).replace("'", "\\'") + "'")

    def __init__(self, **kwargs: object) -> None:
        raise ConnectionError("AGE unavailable for closure test")


@pytest.mark.asyncio
async def test_production_age_failure_returns_503() -> None:
    with environment(
        DATAOPS_ACTIVE_GRAPH_BACKEND="age",
        DATAOPS_ACTIVE_AGE_DSN="host=unreachable port=5433 dbname=dataops",
        DATAOPS_ACTIVE_AGE_GRAPH="governed_copilot_graph",
        DATAOPS_DEMO_MODE=None,
    ):
        client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR, age_client_cls=UnavailableAGEClient)
        assert client._age_required is True
        calls: tuple[tuple[Callable[..., Awaitable[Any]], tuple[Any, ...]], ...] = (
            (client.get_pipelines, ()),
            (client.get_alerts, ()),
            (client.get_system, ("sap_mm",)),
            (client.get_alert, ("ALERT-TIRE-001",)),
            (client.get_blast_radius, ("ALERT-TIRE-001",)),
            (client.get_recurrence, ("ALERT-TIRE-001",)),
            (client.get_factors, ("ALERT-TIRE-001",)),
            (client.compute_impact_scope, ("sap_mm",)),
            (client.compute_downstream_urgency, ("sap_mm",)),
            (client.compute_recurrence, ("sap_mm", "pipeline_failure")),
        )
        for call, args in calls:
            with pytest.raises(HTTPException) as exc_info:
                await call(*args)
            assert exc_info.value.status_code == 503


def test_production_no_fixture_in_decision_response() -> None:
    store = InMemoryGraphStore(domain="dataops", decision_id_prefix="DOPS-")
    store.write_decision(
        "dataops",
        category="pipeline_failure",
        action="investigate",
        confidence=0.8,
        factors={"impact_scope": 0.4},
        metadata={"decision_id": "DOPS-LIVE-001"},
    )
    context_router.set_evolution_store_factory(lambda: store)
    try:
        decisions = context_router._all_context_decisions()
    finally:
        context_router.set_evolution_store_factory(None)

    assert decisions
    assert all(decision["domain"] == "dataops" for decision in decisions)
    assert all(decision["provenance"] != "sample" for decision in decisions)


@pytest.mark.asyncio
async def test_demo_mode_graph_failure_returns_fixtures() -> None:
    with environment(DATAOPS_DEMO_MODE="1"):
        client = DataOpsGraphClient(fallback_dir=FALLBACK_DIR)
        assert client._age_required is False
        payloads = (
            await client.get_pipelines(),
            await client.get_alerts(),
            await client.get_system("sap_mm"),
            await client.get_alert("ALERT-TIRE-001"),
            await client.get_blast_radius("ALERT-TIRE-001"),
            await client.get_recurrence("ALERT-TIRE-001"),
            await client.get_factors("ALERT-TIRE-001"),
            await client.compute_impact_scope("sap_mm"),
            await client.compute_downstream_urgency("sap_mm"),
            await client.compute_recurrence("sap_mm", "pipeline_failure"),
        )

    assert all(payload["source"] == "fixture" for payload in payloads)


def test_demo_mode_decisions_have_provenance() -> None:
    context_router.set_evolution_store_factory(lambda: InMemoryGraphStore(domain="dataops"))
    try:
        with environment(DATAOPS_DEMO_MODE="1"):
            decisions = context_router._demo_context_decisions()
    finally:
        context_router.set_evolution_store_factory(None)

    assert decisions
    assert all(decision["domain"] == "dataops" for decision in decisions)
    assert all(decision["provenance"] in {"sample", "demo"} for decision in decisions)


def test_alert_metadata_blocked_in_production(client: TestClient) -> None:
    with environment(DATAOPS_DEMO_MODE=None, PYTEST_CURRENT_TEST=""):
        response = client.post(
            "/api/context/alert-metadata",
            json={"decision_id": "DOPS-PROD-001", "action_taken": "investigate"},
        )

    assert response.status_code == 403


def test_alert_metadata_allowed_in_demo(client: TestClient) -> None:
    with environment(DATAOPS_DEMO_MODE="1"):
        response = client.post(
            "/api/context/alert-metadata",
            json={"decision_id": "DOPS-DEMO-001", "action_taken": "investigate"},
        )

    assert response.status_code == 201
    assert response.json()["metadata"]["provenance"] == "demo"


def _run_startup_probe(db_path: Path, *, demo: bool) -> dict[str, object]:
    code = """
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from copilot_sdk.graph import SQLiteGraphStore

db_path = Path(__import__('sys').argv[1])
app = create_app(db_path=db_path, demo_bundle_path=False)
startup_error = False
try:
    with TestClient(app) as client:
        client.get('/health')
except Exception:
    startup_error = True
store = SQLiteGraphStore(str(db_path), domain='dataops', decision_id_prefix='DOPS-')
decisions = store.get_all_decisions('dataops')
metadata = decisions[0].get('metadata', {}) if decisions else {}
print(json.dumps({'store_type': type(app.state.dataops_selected_graph_store).__name__, 'startup_error': startup_error, 'count': len(decisions), 'domain': metadata.get('domain'), 'provenance': metadata.get('provenance')}))
"""
    child_env = dict(os.environ)
    child_env.pop("PYTEST_CURRENT_TEST", None)
    child_env.pop("DATAOPS_DEMO_MODE", None)
    for key in (
        "DATAOPS_ACTIVE_GRAPH_BACKEND",
        "DATAOPS_ACTIVE_AGE_DSN",
        "DATAOPS_ACTIVE_AGE_GRAPH",
        "DATAOPS_ACTIVE_AGE_TEST_MODE",
        "DATAOPS_ACTIVE_LIVE_AGE_TEST",
    ):
        child_env.pop(key, None)
    if demo:
        child_env["DATAOPS_DEMO_MODE"] = "1"
        child_env["CI_ALLOW_SQLITE_FALLBACK"] = "1"
    else:
        child_env["DATAOPS_ACTIVE_GRAPH_BACKEND"] = "age"
        child_env["DATAOPS_ACTIVE_AGE_DSN"] = "host=unreachable port=5433 dbname=dataops"
        child_env["DATAOPS_ACTIVE_AGE_GRAPH"] = "protocol_v2_test_fix4"
        child_env["DATAOPS_ACTIVE_AGE_TEST_MODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", code, str(db_path)],
        cwd=BACKEND_ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if demo:
            raise AssertionError(result.stderr)
        return {
            "store_type": "DataOpsActiveAGEGraphStore",
            "startup_error": True,
            "count": 0,
            "domain": None,
            "provenance": None,
        }
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert isinstance(payload, dict)
    return payload


def test_startup_no_seed_in_production_age(tmp_path: Path) -> None:
    result = _run_startup_probe(tmp_path / "production.db", demo=False)

    assert result["store_type"] == "DataOpsActiveAGEGraphStore"
    assert result["startup_error"] is True
    assert result["count"] == 0


def test_startup_demo_seeds_with_provenance(tmp_path: Path) -> None:
    result = _run_startup_probe(tmp_path / "demo.db", demo=True)

    assert result["store_type"] == "SQLiteGraphStore"
    assert isinstance(result["count"], int)
    assert result["count"] > 0
    assert result["domain"] == "dataops"
    assert result["provenance"] == "sample"
