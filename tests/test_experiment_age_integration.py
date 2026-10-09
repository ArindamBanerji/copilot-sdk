"""Live AGE proof for DataOps app wiring and evolution-event persistence."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import psycopg
import pytest

from copilot_sdk.testing.fixtures import age_available


ROOT = Path(__file__).resolve().parents[1]
AGE_DSN = os.environ.get("GRAPH_DSN", "").strip()


def _age_available() -> tuple[bool, str]:
    if not AGE_DSN:
        return False, "GRAPH_DSN is not configured"
    if not age_available(AGE_DSN):
        return False, "bounded AGE probe failed"
    return True, "AGE reachable"


AGE_AVAILABLE, AGE_SKIP_REASON = _age_available()
pytestmark = pytest.mark.skipif(not AGE_AVAILABLE, reason=AGE_SKIP_REASON)


CHILD_SCRIPT = r'''from __future__ import annotations
import asyncio
import json
import os
import re
import sys
from pathlib import Path

mode, graph_name = sys.argv[1:3]
dsn = os.environ["GRAPH_DSN"]
if not re.fullmatch(r"protocol_v2_test_[A-Za-z0-9_]+", graph_name):
    raise SystemExit("unsafe or non-test graph name")

import psycopg

admin = None
module = None
app = None
fresh_store = None
error = None
try:
    admin = psycopg.connect(dsn, connect_timeout=5, autocommit=True)
    admin.execute("LOAD 'age'")
    admin.execute('SET search_path = ag_catalog, "$user", public')
    admin.execute(f"SELECT create_graph('{graph_name}')")
    print("GRAPH_CREATED", graph_name, flush=True)

    os.environ.update({
        "GRAPH_BACKEND": "age",
        "GRAPH_DSN": dsn,
        "GRAPH_NAME": graph_name,
        "GRAPH_PROFILE": "test",
        "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
        "DATAOPS_ACTIVE_AGE_DSN": dsn,
        "DATAOPS_ACTIVE_AGE_GRAPH": graph_name,
        "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
        "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
        "DEMO_NO_RESEED": "1",
    })
    repo = Path.cwd()
    for path in (repo, repo.parent / "ci-platform", repo / "apps" / "dataops" / "backend"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    import app.main as module
    from fastapi.testclient import TestClient

    # In-memory scorer-side stores avoid local persistence; AGE remains the
    # selected graph backend under test.
    app = module.create_app(db_path=":memory:", demo_bundle_path=False)
    with TestClient(app) as client:
        if mode == "composition":
            response = client.get("/api/self/evolution/summary")
            body = response.json()
            print("COMPOSITION", json.dumps({
                "status": response.status_code,
                "domain": body.get("domain"),
                "schema_version": body.get("schema_version"),
                "evolution_enabled": body.get("evolution_enabled"),
                "conservation_state": body.get("conservation_state"),
            }, sort_keys=True), flush=True)
            if response.status_code != 200 or body.get("domain") != "dataops" or body.get("schema_version") != 1:
                raise RuntimeError("app composition summary contract failed")
        elif mode == "ledger":
            from copilot_sdk.evolution import PromptVariantEvolver, VariantSpec
            from copilot_sdk.evolution.graph_store import create_variant_store

            variant_id = "experiment-shadow-" + graph_name[-12:]
            evolver = app.state.evolver
            spec = VariantSpec(
                id=variant_id,
                family="integration-experiment",
                version=1,
                template="disposable AGE shadow experiment",
                status="shadow",
            )
            evolver.register_variants([spec])
            evolver.record_shadow_result(
                variant_id, success=True, batch_id="shadow-test-batch"
            )

            # Read through a newly constructed variant-store adapter to prove
            # the event came back from AGE rather than an in-memory cache.
            fresh_store = create_variant_store(
                app.state.dataops_selected_graph_store, "dataops", test_mode=False
            )
            fresh_evolver = PromptVariantEvolver(
                config=evolver.config, store=fresh_store
            )
            persisted = next(
                (row for row in fresh_evolver.get_summary()["variants"]
                 if row["id"] == variant_id),
                None,
            )
            response = client.get("/api/self/evolution/summary")
            body = response.json()
            api_row = next(
                (row for row in body.get("variant_stats", [])
                 if row.get("variant_id") == variant_id),
                None,
            )
            print("LEDGER", json.dumps({
                "status": response.status_code,
                "variant_id": variant_id,
                "persisted_variant": persisted,
                "summary_variant": api_row,
                "schema_version": body.get("schema_version"),
            }, sort_keys=True), flush=True)
            if (response.status_code != 200 or persisted is None
                    or persisted.get("status") != "shadow"
                    or persisted.get("successes") != 1
                    or persisted.get("total") != 1
                    or api_row is None
                    or api_row.get("successes") != 1
                    or api_row.get("total") != 1):
                raise RuntimeError("evolution event was not durable in summary")
        else:
            raise ValueError("unknown experiment mode")
except BaseException as exc:
    error = exc
    print("CHILD_ERROR", type(exc).__name__, flush=True)
finally:
    for candidate in (
        fresh_store,
        getattr(getattr(module, "app", None), "state", None) and getattr(module.app.state, "graph_store", None),
        getattr(getattr(app, "state", None), "graph_store", None),
    ):
        close = getattr(candidate, "close", None)
        if callable(close):
            try:
                result = close()
                if hasattr(result, "__await__"):
                    asyncio.run(result)
            except Exception as exc:
                print("STORE_CLOSE_ERROR", type(exc).__name__, flush=True)
    if admin is not None:
        try:
            admin.execute("LOAD 'age'")
            admin.execute('SET search_path = ag_catalog, "$user", public')
            admin.execute(f"SELECT drop_graph('{graph_name}', true)")
            print("GRAPH_DROPPED", graph_name, flush=True)
        except Exception as exc:
            print("GRAPH_DROP_ERROR", type(exc).__name__, flush=True)
        finally:
            admin.close()
if error is not None:
    raise SystemExit(1)
'''


def _graph_name() -> str:
    return f"protocol_v2_test_dataops_{os.getpid()}_{time.time_ns()}_{uuid.uuid4().hex[:6]}"


def _drop_if_present(graph_name: str) -> None:
    """Parent-side cleanup in case a timed-out child could not run finally."""
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


def _run_child(mode: str) -> subprocess.CompletedProcess[str]:
    graph_name = _graph_name()
    env = os.environ.copy()
    env.update({
        "GRAPH_BACKEND": "age",
        "GRAPH_DSN": AGE_DSN,
        "GRAPH_NAME": graph_name,
        "GRAPH_PROFILE": "test",
        "DATAOPS_ACTIVE_GRAPH_BACKEND": "age",
        "DATAOPS_ACTIVE_AGE_DSN": AGE_DSN,
        "DATAOPS_ACTIVE_AGE_GRAPH": graph_name,
        "DATAOPS_ACTIVE_AGE_DOMAIN": "dataops",
        "DATAOPS_ACTIVE_AGE_TEST_MODE": "1",
        "DEMO_NO_RESEED": "1",
    })
    try:
        try:
            started = time.monotonic()
            result = subprocess.run(
                [sys.executable, "-c", CHILD_SCRIPT, mode, graph_name],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(f"{mode} subprocess exceeded 30 seconds: {exc}")
        safe_stdout = result.stdout.replace(AGE_DSN, "<redacted>")
        safe_stderr = result.stderr.replace(AGE_DSN, "<redacted>")
        assert result.returncode == 0, (
            f"{mode} child exited {result.returncode}\n"
            f"stdout:\n{safe_stdout}\nstderr:\n{safe_stderr}"
        )
        assert "GRAPH_CREATED" in result.stdout
        assert "GRAPH_DROPPED" in result.stdout
        print(f"SUBPROCESS_RUNTIME mode={mode} seconds={time.monotonic() - started:.2f}")
        print(result.stdout)
        return result
    finally:
        _drop_if_present(graph_name)


def test_dataops_app_composition_on_disposable_age() -> None:
    result = _run_child("composition")
    assert '"status": 200' in result.stdout
    assert '"domain": "dataops"' in result.stdout
    assert '"schema_version": 1' in result.stdout


def test_evolution_shadow_event_persists_to_age_and_summary() -> None:
    result = _run_child("ledger")
    assert "LEDGER" in result.stdout
    assert '"successes": 1' in result.stdout
    assert '"total": 1' in result.stdout
