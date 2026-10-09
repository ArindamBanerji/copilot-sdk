"""Live app-composition checks isolated on disposable AGE graphs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any, cast

import psycopg
import pytest

from copilot_sdk.testing.fixtures import age_available


ROOT = Path(__file__).resolve().parents[1]
AGE_DSN = os.environ.get("GRAPH_DSN", "").strip()
pytestmark = pytest.mark.skipif(not AGE_DSN, reason="AGE integration: GRAPH_DSN not set")
COPILOTS_WITH_APPS = ["trading", "purchasing", "dataops"]


def _check_age_available() -> bool:
    """Check PostgreSQL and the AGE extension with a bounded connection."""
    return bool(AGE_DSN) and age_available(AGE_DSN)


@pytest.fixture(scope="module", autouse=True)
def _require_age() -> None:
    if not _check_age_available():
        pytest.skip("AGE server unreachable")


WORKER = r'''from __future__ import annotations
import asyncio
import json
import os
import re
import sys
import traceback
from pathlib import Path

domain, graph_name = sys.argv[1:3]
dsn = os.environ["GRAPH_DSN"]
if not re.fullmatch(r"protocol_v2_test_[A-Za-z0-9_]+", graph_name):
    raise SystemExit("unsafe test graph name")

import psycopg

admin = None
app_module = None
test_app = None
graph_created = False
failure = None
try:
    admin = psycopg.connect(dsn, connect_timeout=5, autocommit=True)
    admin.execute("LOAD 'age'")
    admin.execute('SET search_path = ag_catalog, "$user", public')
    admin.execute(f"SELECT create_graph('{graph_name}')")
    # Purchasing prunes evolution events during startup using the AGE label table.
    # Materialize that empty label on the disposable graph before app construction.
    admin.execute(
        f"SELECT * FROM cypher('{graph_name}', "
        "$$ CREATE (e:EvolutionEvent {event_id: 'telemetry-bootstrap'}) RETURN e $$) "
        "AS (e agtype)"
    )
    graph_created = True
    print("GRAPH_CREATED", graph_name, flush=True)

    prefix = domain.upper()
    os.environ.update({
        "GRAPH_BACKEND": "age",
        "GRAPH_DSN": dsn,
        "GRAPH_NAME": graph_name,
        "GRAPH_PROFILE": "test",
        "GRAPH_TEST_MODE": "true",
        f"{prefix}_PROFILE": "test",
        f"{prefix}_ACTIVE_GRAPH_BACKEND": "age",
        f"{prefix}_ACTIVE_AGE_DSN": dsn,
        f"{prefix}_ACTIVE_AGE_GRAPH": graph_name,
        f"{prefix}_ACTIVE_AGE_DOMAIN": domain,
        f"{prefix}_ACTIVE_AGE_TEST_MODE": "1",
        "DEMO_NO_RESEED": "1",
    })
    repo = Path.cwd()
    backend = repo / "apps" / domain / "backend"
    for path in (repo, repo.parent / "ci-platform", backend):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    import app.main as app_module
    from fastapi.testclient import TestClient

    test_app = app_module.create_app(db_path=":memory:", demo_bundle_path=False)
    with TestClient(test_app) as client:
        response = client.get("/api/self/evolution/summary")
        payload = response.json()
        output = {
            "status": response.status_code,
            "body": {
                "domain": payload.get("domain"),
                "evolution_enabled": payload.get("evolution_enabled"),
                "schema_version": payload.get("schema_version"),
                "keys": sorted(payload),
            },
        }
        print("EXPERIMENT_RESULT " + json.dumps(output, sort_keys=True), flush=True)
        if response.status_code != 200 or payload.get("domain") != domain or payload.get("schema_version") != 1:
            raise RuntimeError("app telemetry summary contract failed")
except BaseException as exc:
    failure = exc
    print("WORKER_ERROR", type(exc).__name__, flush=True)
    traceback.print_exc()
finally:
    seen = set()
    for candidate_app in (test_app, getattr(app_module, "app", None)):
        state = getattr(candidate_app, "state", None)
        if state is None:
            continue
        for attribute in (
            "graph_store", "trading_selected_graph_store",
            "purchasing_selected_graph_store", "dataops_selected_graph_store",
        ):
            store = getattr(state, attribute, None)
            if store is None or id(store) in seen:
                continue
            seen.add(id(store))
            close = getattr(store, "close", None)
            if callable(close):
                try:
                    result = close()
                    if hasattr(result, "__await__"):
                        asyncio.run(result)
                except Exception as exc:
                    failure = failure or exc
                    print("STORE_CLOSE_ERROR", type(exc).__name__, flush=True)
    if admin is not None:
        try:
            if graph_created:
                admin.execute("LOAD 'age'")
                admin.execute('SET search_path = ag_catalog, "$user", public')
                admin.execute(f"SELECT drop_graph('{graph_name}', true)")
                print("GRAPH_DROPPED", graph_name, flush=True)
        except Exception as exc:
            failure = failure or exc
            print("GRAPH_DROP_ERROR", type(exc).__name__, flush=True)
        finally:
            admin.close()
if failure is not None:
    raise SystemExit(1)
'''


def _new_graph_name(domain: str) -> str:
    return f"protocol_v2_test_{domain}_telemetry_{uuid.uuid4().hex[:12]}"


def _drop_if_present(graph_name: str) -> None:
    """Parent-side cleanup if a timed-out worker cannot execute its finally."""
    if not AGE_DSN:
        return
    with psycopg.connect(AGE_DSN, connect_timeout=5, autocommit=True) as conn:
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        found = conn.execute(
            "SELECT name FROM ag_catalog.ag_graph WHERE name = %s", (graph_name,)
        ).fetchone()
        if found:
            conn.execute(f"SELECT drop_graph('{graph_name}', true)")


def _run_app_worker(domain: str) -> dict[str, Any]:
    graph_name = _new_graph_name(domain)
    env = os.environ.copy()
    prefix = domain.upper()
    env.update({
        "GRAPH_BACKEND": "age",
        "GRAPH_DSN": AGE_DSN,
        "GRAPH_NAME": graph_name,
        "GRAPH_PROFILE": "test",
        "GRAPH_TEST_MODE": "true",
        f"{prefix}_PROFILE": "test",
        f"{prefix}_ACTIVE_GRAPH_BACKEND": "age",
        f"{prefix}_ACTIVE_AGE_DSN": AGE_DSN,
        f"{prefix}_ACTIVE_AGE_GRAPH": graph_name,
        f"{prefix}_ACTIVE_AGE_DOMAIN": domain,
        f"{prefix}_ACTIVE_AGE_TEST_MODE": "1",
        "DEMO_NO_RESEED": "1",
    })
    try:
        try:
            result = subprocess.run(
                [sys.executable, "-c", WORKER, domain, graph_name],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(f"{domain} AGE app worker exceeded 30 seconds: {exc}")

        stdout = result.stdout.replace(AGE_DSN, "<redacted>")
        stderr = result.stderr.replace(AGE_DSN, "<redacted>")
        assert result.returncode == 0, f"{domain} worker failed\n{stdout}\n{stderr}"
        assert "GRAPH_CREATED" in result.stdout
        assert "GRAPH_DROPPED" in result.stdout
        result_line = next(
            (line.removeprefix("EXPERIMENT_RESULT ")
             for line in result.stdout.splitlines()
             if line.startswith("EXPERIMENT_RESULT ")),
            None,
        )
        assert result_line is not None, f"{domain} worker emitted no result\n{stdout}"
        return cast(dict[str, Any], json.loads(result_line))
    finally:
        _drop_if_present(graph_name)


@pytest.mark.parametrize("domain", COPILOTS_WITH_APPS)
def test_age_app_telemetry(domain: str) -> None:
    result = _run_app_worker(domain)
    assert result["status"] == 200
    payload = result["body"]
    assert payload["schema_version"] == 1
    assert {"domain", "evolution_enabled", "schema_version"} <= set(payload["keys"])
    assert payload["domain"] == domain
