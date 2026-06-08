from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "c9_live_age_smoke.py"


def load_script():
    spec = importlib.util.spec_from_file_location("c9_live_age_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_domains_supports_single_and_list():
    smoke = load_script()

    assert smoke.parse_domains(None, "dataops") == ["dataops"]
    assert smoke.parse_domains("trading,purchasing,dataops", None) == [
        "trading",
        "purchasing",
        "dataops",
    ]
    assert smoke.parse_domains("trading", "trading") == ["trading"]


def test_parse_domains_rejects_soc_for_non_soc_c9_target():
    smoke = load_script()

    try:
        smoke.parse_domains("soc", None)
    except ValueError as exc:
        assert "unsupported domain" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_argument_parser_defaults_and_readback_only():
    smoke = load_script()
    parser = smoke.build_parser()

    args = parser.parse_args(["--readback-only", "--json"])

    assert args.readback_only is True
    assert args.json is True
    assert args.loops == 1


def test_domain_plan_rejects_non_positive_loops():
    smoke = load_script()

    with pytest.raises(ValueError, match="positive"):
        smoke.domain_plan(["dataops"], 0)
    with pytest.raises(ValueError, match="positive"):
        smoke.domain_plan(["dataops"], -1)


def test_redact_dsn_url_and_key_value_password():
    smoke = load_script()

    assert (
        smoke.redact_dsn("postgresql://postgres:secret@localhost:5433/soc")
        == "postgresql://postgres:***@localhost:5433/soc"
    )
    assert (
        smoke.redact_dsn("host=localhost password=secret user=postgres")
        == "host=localhost password=*** user=postgres"
    )


def test_database_url_preferred_over_passwordless_graph_dsn():
    smoke = load_script()

    dsn, source = smoke.choose_database_url(
        "postgresql://postgres:secret@localhost:5433/soc",
        "host=localhost port=5433 dbname=postgres user=postgres",
    )

    assert dsn == "postgresql://postgres:secret@localhost:5433/soc"
    assert "DATABASE_URL" in source
    assert "ignored passwordless GRAPH_DSN" in source
    assert smoke.graph_dsn_is_passwordless("host=localhost port=5433 dbname=postgres user=postgres")


def test_readiness_ready_from_complete_synthetic_counts():
    smoke = load_script()
    readback = {
        "L5Centroid": {"trading": 1},
        "L5DKWeight": {"trading": 1},
        "L5ConservationState": {"trading": {"count": 1}},
        "Welford": {"trading": {"present": True}},
        "SHAPED_BY": {"trading": 1},
        "TRIGGERED_BY": {},
    }

    verdict, missing, notes = smoke.classify_readiness(readback, ["trading"], {})

    assert verdict == smoke.READINESS_READY
    assert missing == []
    assert notes == {"trading": "transition not exercised"}


def test_soc_gap_does_not_block_non_soc_readiness():
    smoke = load_script()
    readback = {
        "L5Centroid": {"trading": 1},
        "L5DKWeight": {"trading": 1},
        "L5ConservationState": {"trading": {"count": 1}},
        "Welford": {"trading": {"present": True}},
        "SHAPED_BY": {"trading": 1},
        "TRIGGERED_BY": {},
    }

    verdict, missing, notes = smoke.classify_readiness(readback, ["trading"], {})

    assert verdict == smoke.READINESS_READY
    assert missing == []
    assert notes == {"trading": "transition not exercised"}


def test_missing_conservation_state_is_partial_not_failure():
    smoke = load_script()
    readback = {
        "L5Centroid": {"dataops": 1},
        "L5DKWeight": {"dataops": 1},
        "L5ConservationState": {},
        "Welford": {"dataops": {"present": True}},
        "SHAPED_BY": {"dataops": 1},
        "TRIGGERED_BY": {},
    }

    verdict, missing, notes = smoke.classify_readiness(readback, ["dataops"], {})

    assert verdict == smoke.READINESS_PARTIAL
    assert missing == [{"domain": "dataops", "cell": "L5ConservationState", "reason": "count is zero"}]
    assert notes == {"dataops": "transition not exercised"}


def test_route_failure_is_fail_needs_fixer():
    smoke = load_script()
    readback = {
        "L5Centroid": {"dataops": 1},
        "L5DKWeight": {"dataops": 1},
        "L5ConservationState": {"dataops": {"count": 1}},
        "Welford": {"dataops": {"present": True}},
        "SHAPED_BY": {"dataops": 1},
        "TRIGGERED_BY": {},
    }
    route_results = {
        "dataops": smoke.DomainRunResult(
            domain="dataops",
            method="SDK TestClient /score -> /learn",
            attempted=1,
            failed=1,
            failures=["loop 0: /learn 400"],
        )
    }

    verdict, missing, _notes = smoke.classify_readiness(readback, ["dataops"], route_results)

    assert verdict == smoke.READINESS_FAIL
    assert missing == [{"domain": "dataops", "cell": "route", "reason": "1 route loop(s) failed"}]


def test_s2p_unsupported_is_partial_not_ready():
    smoke = load_script()
    readback = {
        "L5Centroid": {"s2p": 1},
        "L5DKWeight": {"s2p": 1},
        "L5ConservationState": {"s2p": {"count": 1}},
        "Welford": {"s2p": {"present": True}},
        "SHAPED_BY": {"s2p": 1},
        "TRIGGERED_BY": {},
    }
    route_results = {
        "s2p": smoke.DomainRunResult(
            domain="s2p",
            method="S2P TestClient",
            unsupported_reason="S2P imports unavailable",
        )
    }

    verdict, missing, _notes = smoke.classify_readiness(readback, ["s2p"], route_results)

    assert verdict == smoke.READINESS_PARTIAL
    assert missing == [{"domain": "s2p", "cell": "route", "reason": "S2P imports unavailable"}]


def test_missing_cell_classification_lists_each_missing_requirement():
    smoke = load_script()
    readback = {
        "L5Centroid": {"trading": 1},
        "L5DKWeight": {},
        "L5ConservationState": {},
        "Welford": {"trading": {"present": False}},
        "SHAPED_BY": {},
        "TRIGGERED_BY": {},
    }

    verdict, missing, _notes = smoke.classify_readiness(readback, ["trading"], {})

    assert verdict == smoke.READINESS_PARTIAL
    assert {item["cell"] for item in missing} == {
        "L5DKWeight",
        "L5ConservationState",
        "DKWeight Welford",
        "SHAPED_BY",
    }


class FakeReadbackStore:
    def _run_query(self, query: str):
        if "L5Centroid)-[:SHAPED_BY]" in query:
            return [{"domain": "dataops", "cnt": 2}]
        if "L5ConservationState)-[:TRIGGERED_BY]" in query:
            return []
        if "MATCH (c:L5Centroid)" in query and "RETURN c.domain AS domain, count(c)" in query:
            return [{"domain": "dataops", "cnt": 2}]
        if "MATCH (w:L5DKWeight)" in query and "count(w.confirmed_mean_json)" in query:
            return [
                {
                    "domain": "dataops",
                    "cnt": 1,
                    "confirmed_mean": 1,
                    "confirmed_m2": 1,
                    "overridden_mean": 1,
                    "overridden_m2": 1,
                    "all_mean": 1,
                    "all_m2": 1,
                }
            ]
        if "MATCH (w:L5DKWeight)" in query and "RETURN w.domain AS domain, count(w)" in query:
            return [{"domain": "dataops", "cnt": 1}]
        if "MATCH (cs:L5ConservationState)" in query and "count(cs)" in query:
            return [{"domain": "dataops", "status": "GREEN", "cnt": 1}]
        return []


def test_readback_summary_handles_synthetic_rows():
    smoke = load_script()

    summary = smoke.readback_from_store(FakeReadbackStore(), ["dataops"])

    assert summary["L5Centroid"] == {"dataops": 2}
    assert summary["L5DKWeight"] == {"dataops": 1}
    assert summary["L5ConservationState"]["dataops"]["statuses"] == {"GREEN": 1}
    assert summary["Welford"]["dataops"]["present"] is True


def test_dry_run_json_shape(capsys):
    smoke = load_script()
    args = Namespace(
        domain=None,
        domains="trading,dataops",
        loops=1,
        readback=False,
        readback_only=False,
        graph_name="soc_graph",
        database_url="postgresql://postgres:secret@localhost:5433/soc",
        json=True,
        verbose=False,
        dry_run=True,
    )

    summary = smoke.run(args)

    assert summary.verdict == smoke.READINESS_PARTIAL
    assert summary.domains_requested == ["trading", "dataops"]
    payload = json.dumps(smoke.asdict(summary), sort_keys=True)
    assert "postgres:secret" not in payload
    assert "postgres:***" in payload


def test_main_json_output_is_parseable_and_redacted(capsys):
    smoke = load_script()

    exit_code = smoke.main(
        [
            "--dry-run",
            "--domain",
            "dataops",
            "--database-url",
            "postgresql://postgres:secret@localhost:5433/soc",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == smoke.READINESS_PARTIAL
    assert payload["domains_requested"] == ["dataops"]
    assert payload["dsn_redacted"] == "postgresql://postgres:***@localhost:5433/soc"
    assert "secret" not in json.dumps(payload)


def test_run_classifies_store_unavailable_as_blocked(monkeypatch):
    smoke = load_script()

    def fail_store(_database_url, _graph_name):
        raise RuntimeError("cannot connect")

    monkeypatch.setattr(smoke, "make_age_store", fail_store)
    args = Namespace(
        domain="dataops",
        domains=None,
        loops=1,
        readback=True,
        readback_only=False,
        graph_name="soc_graph",
        database_url="postgresql://postgres:secret@localhost:5433/soc",
        json=False,
        verbose=False,
        dry_run=False,
    )

    summary = smoke.run(args)

    assert summary.verdict == smoke.READINESS_BLOCKED
    assert summary.missing_cells[0]["cell"] == "environment"
    assert summary.dsn_redacted == "postgresql://postgres:***@localhost:5433/soc"


def test_source_does_not_call_l5_write_methods_directly():
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert ".update_centroid(" not in source
    assert ".update_dk_weights(" not in source
    assert ".update_conservation_state(" not in source
    assert "CREATE (c:L5Centroid" not in source
    assert "CREATE (w:L5DKWeight" not in source
    assert "CREATE (cs:L5ConservationState" not in source

