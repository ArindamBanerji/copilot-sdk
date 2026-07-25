"""Read-only smoke validation for the shared AGE migration.

The smoke runner deliberately never writes to AGE.  Standard and comprehensive
levels are reserved for a future implementation and require a disposable graph
name so they cannot accidentally target the production graph.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:  # Works both as ``python scripts/...`` and as a package import.
    from scripts.phase_config import get_config
except ModuleNotFoundError:  # pragma: no cover - exercised by script invocation
    from phase_config import get_config


LEVELS = ("smoke", "standard", "comprehensive")
DEFAULT_DOMAINS = ("soc", "trading", "purchasing", "dataops", "s2p")
DEFAULT_GRAPH = "soc_graph"
GRAPH_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _redact_dsn(dsn: str | None) -> str:
    """Redact password values in keyword and URI-style DSNs."""
    if not dsn:
        return "<unset>"
    value = re.sub(r"(?i)(password\s*=\s*)([^\s]+)", r"\1<redacted>", dsn)
    value = re.sub(r"(://[^:/@]+:)[^@]+(@)", r"\1<redacted>\2", value)
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _area(area_id: str, status: str, **details: Any) -> dict[str, Any]:
    return {"id": area_id, "status": status, "details": details}


def _parse_domains(raw: str) -> list[str]:
    domains = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not domains:
        raise ValueError("--domains must contain at least one domain")
    unknown = sorted(set(domains) - set(DEFAULT_DOMAINS))
    if unknown:
        raise ValueError(f"unknown domain(s): {', '.join(unknown)}")
    return domains


@contextmanager
def _temporary_graph_dsn(dsn: str | None) -> Iterator[None]:
    """Make an explicit CLI DSN visible to phase_config without leaking it."""
    old = os.environ.get("GRAPH_DSN")
    if dsn:
        os.environ["GRAPH_DSN"] = dsn
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("GRAPH_DSN", None)
        else:
            os.environ["GRAPH_DSN"] = old


class AGEReadOnly:
    """Small direct AGE reader used only by smoke census checks."""

    def __init__(self, dsn: str, graph: str) -> None:
        if not GRAPH_NAME_RE.fullmatch(graph):
            raise ValueError("graph name must contain only letters, digits, and underscores")
        try:
            import psycopg2
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("psycopg2 is required for AGE checks") from exc
        self.graph = graph
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("LOAD 'age'")
        self.cur.execute('SET search_path = ag_catalog, "$user", public')

    def close(self) -> None:
        self.conn.close()

    def rows(self, query: str, columns: str = "value agtype") -> list[tuple[Any, ...]]:
        self.cur.execute(
            f"SELECT * FROM cypher('{self.graph}', $$ {query} $$) AS ({columns})"
        )
        return list(self.cur.fetchall())

    def integer(self, query: str) -> int:
        rows = self.rows(query)
        if not rows:
            return 0
        value = rows[0][0]
        return int(str(value).strip('"'))


def _health(domains: list[str], dsn: str) -> dict[str, Any]:
    areas: dict[str, Any] = {"status": "PASS", "domains": {}}
    with _temporary_graph_dsn(dsn):
        for domain in domains:
            try:
                try:
                    cfg = get_config(domain)
                    base_url = cfg["api_base"]
                except SystemExit:
                    # phase_config intentionally contains product migration
                    # domains; SOC's launcher-owned health port is 8001.
                    if domain != "soc":
                        raise
                    from copilot_sdk.config import GraphConfig

                    soc_config = GraphConfig.load("soc")
                    soc_port = soc_config.port
                    if soc_port is None:
                        raise RuntimeError("SOC GraphConfig has no port")
                    base_url = os.environ.get("SOC_API_BASE", f"http://127.0.0.1:{soc_port}")
                request = Request(f"{base_url}/health", method="GET")
                with urlopen(request, timeout=10) as response:
                    body = response.read().decode("utf-8")
                    status = response.status
                payload = json.loads(body)
                details = {
                    "http_status": status,
                    "backend": payload.get("backend", payload.get("graph_backend")),
                    "graph": payload.get("graph", payload.get("graph_name")),
                }
                if status != 200:
                    raise RuntimeError(f"HTTP {status}")
                areas["domains"][domain] = details
            except (OSError, HTTPError, URLError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                areas["domains"][domain] = {"error": _redact_dsn(str(exc))}
                areas["status"] = "FAIL"
    return areas


def _census(reader: AGEReadOnly) -> tuple[dict[str, Any], int]:
    counts: dict[str, int] = {
        "NULL": reader.integer("MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(d)"),
    }
    for domain in DEFAULT_DOMAINS:
        counts[domain] = reader.integer(
            f"MATCH (d:Decision) WHERE d.domain = '{domain}' RETURN count(d)"
        )
    verified = reader.integer(
        "MATCH (d:Decision) WHERE d.domain = 'soc' "
        "AND (d.archived IS NULL OR d.archived <> true) "
        "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
        "OR (d.status IS NULL AND d.outcome IS NOT NULL)) RETURN count(d)"
    )
    counts["total"] = reader.integer("MATCH (d:Decision) RETURN count(d)")
    return {
        "counts": counts,
        "sum_check": sum(counts[domain] for domain in DEFAULT_DOMAINS) + counts["NULL"],
        "v_soc": verified,
        "null_domain_zero": counts["NULL"] == 0,
    }, verified


def _integrity(reader: AGEReadOnly) -> dict[str, Any]:
    decision_rows = reader.rows(
        "MATCH (d:Decision) RETURN d.domain, d.decision_id",
        "domain agtype, decision_id agtype",
    )
    keys = [tuple(str(value).strip('"') for value in row) for row in decision_rows]
    duplicate_count = sum(count - 1 for count in Counter(keys).values() if count > 1)
    orphan_count = reader.integer(
        "MATCH (o:Outcome) OPTIONAL MATCH (d:Decision)-[:HAS_OUTCOME]->(o) "
        "WHERE d IS NULL RETURN count(o)"
    )
    return {
        "duplicate_decisions": duplicate_count,
        "orphan_outcomes": orphan_count,
        "duplicate_pass": duplicate_count == 0,
        "orphan_pass": orphan_count == 0,
    }


def _soc_isolation() -> dict[str, Any]:
    test_root = Path(__file__).resolve().parents[1] / ".." / "gen-ai-roi-demo-v4-v50" / "backend"
    test_file = test_root / "tests" / "test_soc_domain_isolation.py"
    if not test_file.exists():
        return {"status": "FAIL", "error": f"missing test file: {test_file}"}
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "--timeout=60"],
        cwd=str(test_root), capture_output=True, text=True, check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    passed = int(re.search(r"(\d+) passed", output).group(1)) if re.search(r"(\d+) passed", output) else 0
    failed = int(re.search(r"(\d+) failed", output).group(1)) if re.search(r"(\d+) failed", output) else 0
    skipped = int(re.search(r"(\d+) skipped", output).group(1)) if re.search(r"(\d+) skipped", output) else 0
    return {"status": "PASS" if completed.returncode == 0 and passed == 10 and failed == 0 and skipped == 0 else "FAIL",
            "passed": passed, "failed": failed, "skipped": skipped, "returncode": completed.returncode,
            "stdout_tail": output[-2000:]}


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = _now()
    domains = _parse_domains(args.domains)
    dsn = args.age_dsn or os.environ.get("AGE_TEST_DSN") or os.environ.get("GRAPH_DSN") or os.environ.get("AGE_DSN")
    if not dsn:
        raise ValueError("AGE DSN is required; pass --age-dsn or set AGE_TEST_DSN")
    if not GRAPH_NAME_RE.fullmatch(args.graph):
        raise ValueError("--graph must contain only letters, digits, and underscores")
    if args.level in {"standard", "comprehensive"} and not args.test_graph:
        raise ValueError(f"--test-graph is required for --level {args.level}")
    if args.test_graph == DEFAULT_GRAPH:
        raise ValueError("--test-graph must not be soc_graph")

    reader = AGEReadOnly(dsn, args.graph)
    try:
        health = _health(domains, dsn)
        census, baseline = _census(reader)
        integrity = _integrity(reader)
    finally:
        reader.close()
    isolation = _soc_isolation()
    areas = [
        _area("health", health["status"], **{k: v for k, v in health.items() if k != "status"}),
        _area("census", "PASS" if census["null_domain_zero"] else "FAIL", **census),
        _area("v_soc_baseline", "PASS", v_soc=baseline, captured=True),
        _area("soc_isolation", isolation["status"], **{k: v for k, v in isolation.items() if k != "status"}),
        _area("integrity", "PASS" if integrity["duplicate_pass"] and integrity["orphan_pass"] else "FAIL", **integrity),
    ]
    counts = {"passed": sum(a["status"] == "PASS" for a in areas), "failed": sum(a["status"] == "FAIL" for a in areas), "skipped": 0}
    return {"schema_version": "1.0", "run_id": str(uuid.uuid4()), "level": args.level,
            "started_at": started, "completed_at": _now(), "domains": domains,
            "age_dsn_redacted": _redact_dsn(dsn), "graph_name": args.graph,
            "v_soc_baseline": baseline, "areas": areas, "counts": counts,
            "overall_status": "PASS" if counts["failed"] == 0 else "FAIL"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=LEVELS, required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--domains", default=",".join(DEFAULT_DOMAINS))
    parser.add_argument("--age-dsn")
    parser.add_argument("--graph", default=DEFAULT_GRAPH)
    parser.add_argument("--test-graph")
    args = parser.parse_args()
    try:
        report = run(args)
    except Exception as exc:
        report = {"schema_version": "1.0", "run_id": str(uuid.uuid4()), "level": args.level,
                  "started_at": _now(), "completed_at": _now(), "domains": [],
                  "age_dsn_redacted": _redact_dsn(args.age_dsn or os.environ.get("AGE_TEST_DSN")),
                  "graph_name": args.graph, "v_soc_baseline": None, "areas": [],
                  "counts": {"passed": 0, "failed": 1, "skipped": 0}, "overall_status": "FAIL",
                  "refusal": _redact_dsn(str(exc))}
        print(f"REFUSED/FAILED: {_redact_dsn(str(exc))}")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"AGE migration validation ({report['level']}): {report['overall_status']}")
    print(f"Graph: {report['graph_name']} | DSN: {report['age_dsn_redacted']}")
    for area in report["areas"]:
        print(f"  {area['id']}: {area['status']}")
    print(f"Passed={report['counts']['passed']} Failed={report['counts']['failed']} Skipped={report['counts']['skipped']}")
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
