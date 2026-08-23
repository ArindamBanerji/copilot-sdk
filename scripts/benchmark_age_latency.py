"""Benchmark AGE-backed score latency and verify the migration performance gate."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from copilot_sdk.config import GraphConfig
from phase_config import get_config, scoring_shape


DEFAULT_DOMAIN = "soc"
DEFAULT_REQUESTS = 250
DEFAULT_P95_THRESHOLD_MS = 193.0
REQUIRED_INDEXES = ("decision_domain_idx", "decision_archived_idx")


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except (urllib.error.URLError, ConnectionRefusedError) as exc:
        print(
            f"ERROR: Backend not reachable at {url}. "
            "Start platform first: python demo.py --no-browser",
            file=sys.stderr,
        )
        print(f"  reason: {exc}", file=sys.stderr)
        return 0, None


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, int((percentile / 100.0) * len(ordered) + 0.999999))
    return ordered[min(rank, len(ordered)) - 1]


def _age_connection(dsn: str, graph: str):
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("psycopg2 is required for AGE benchmark checks") from exc
    connection = psycopg2.connect(dsn)
    connection.autocommit = True
    cursor = connection.cursor()
    cursor.execute("LOAD 'age'")
    cursor.execute('SET search_path = ag_catalog, "$user", public')
    return connection, cursor


def _age_scalar(cursor, graph: str, query: str) -> int:
    cursor.execute(
        f"SELECT * FROM cypher('{graph}', $$ {query} $$) AS (value agtype)"
    )
    row = cursor.fetchone()
    if not row:
        return 0
    return int(str(row[0]).strip('"'))


def _verify_indexes(cursor) -> list[str]:
    cursor.execute(
        "SELECT indexname FROM pg_indexes "
        "WHERE indexname IN (%s, %s)",
        REQUIRED_INDEXES,
    )
    found = {str(row[0]) for row in cursor.fetchall()}
    missing = [name for name in REQUIRED_INDEXES if name not in found]
    if missing:
        print(f"WARNING: missing AGE indexes: {', '.join(missing)}")
    else:
        print("AGE indexes: PASS (decision_domain_idx, decision_archived_idx)")
    return missing


def _resolve_soc_base(port: int | None, config: GraphConfig) -> str:
    base = os.environ.get("SOC_API_BASE")
    if base:
        return base.rstrip("/")
    selected_port = port or config.port
    if selected_port is None:
        raise RuntimeError("SOC GraphConfig has no port")
    return f"http://127.0.0.1:{selected_port}"


def _soc_alert_ids(base_url: str, requested: int) -> list[str]:
    status, body = _http_json("GET", f"{base_url}/api/alerts/queue")
    if status < 200 or status >= 300:
        raise RuntimeError(f"SOC alert queue returned HTTP {status}")
    alerts = body.get("alerts", []) if isinstance(body, dict) else []
    alert_ids = [
        str(alert.get("id") or alert.get("alert_id"))
        for alert in alerts
        if isinstance(alert, dict) and (alert.get("id") or alert.get("alert_id"))
    ]
    if len(alert_ids) < requested:
        raise RuntimeError(
            f"SOC alert queue has {len(alert_ids)} alerts; {requested} required"
        )
    return alert_ids[:requested]


def _request_plan(domain: str, requested: int, port: int | None) -> tuple[str, list[tuple[str, dict[str, Any]]], dict[str, Any]]:
    if domain == DEFAULT_DOMAIN:
        soc_config = GraphConfig.load("soc")
        base = _resolve_soc_base(port, soc_config)
        ids = _soc_alert_ids(base, requested)
        return (
            "/api/alert/analyze",
            [(f"{base}/api/alert/analyze", {"alert_id": alert_id}) for alert_id in ids],
            {"api_base": base, "graph": soc_config.graph, "age_dsn": soc_config.dsn},
        )

    cfg = get_config(domain)
    if port is not None:
        cfg["api_base"] = f"http://127.0.0.1:{port}"
    if not cfg.get("api_base") or not cfg.get("score_path"):
        raise RuntimeError(f"No score endpoint configured for {domain}")
    categories, factors = scoring_shape(domain)
    requests = []
    for index in range(requested):
        payload = cfg["score_payload_fn"](
            category=categories[index % len(categories)],
            factors=factors,
            cycle_num=index + 1,
        )
        requests.append((f"{cfg['api_base']}{cfg['score_path']}", payload))
    return cfg["score_path"], requests, cfg


def _run_requests(requests: list[tuple[str, dict[str, Any]]]) -> tuple[list[float], int]:
    latencies: list[float] = []
    errors = 0
    for url, payload in requests:
        started = time.perf_counter()
        try:
            status, body = _http_json("POST", url, payload)
            if status < 200 or status >= 300 or not isinstance(body, dict):
                errors += 1
        except (OSError, ValueError, urllib.error.URLError) as exc:
            errors += 1
            print(f"WARNING: request failed: {exc}", file=sys.stderr)
        finally:
            latencies.append((time.perf_counter() - started) * 1000.0)
    return latencies, errors


def _explain_domain_query(cursor, graph: str, domain: str) -> str:
    """Capture the PostgreSQL/AGE plan for a representative scoped read."""
    cursor.execute(
        "EXPLAIN SELECT * FROM cypher(%s, %s) AS (decision_id agtype)",
        (graph, f"MATCH (d:Decision) WHERE d.domain = '{domain}' RETURN d.decision_id LIMIT 1"),
    )
    return "\n".join(str(row[0]) for row in cursor.fetchall())


def _build_report(domain: str, requested: int, latencies: list[float], errors: int, graph_size: int, threshold: float, endpoint: str, query_plan: str) -> dict[str, Any]:
    measured = [value for value in latencies if value >= 0]
    p95 = _percentile(measured, 95)
    return {
        "domain": domain,
        "requests": requested,
        "p50_ms": _percentile(measured, 50),
        "p95_ms": p95,
        "p99_ms": _percentile(measured, 99),
        "mean_ms": statistics.fmean(measured) if measured else 0.0,
        "min_ms": min(measured) if measured else 0.0,
        "max_ms": max(measured) if measured else 0.0,
        "error_count": errors,
        "total_requests": len(latencies),
        "graph_decision_count": graph_size,
        "gate_p95_threshold_ms": threshold,
        "gate_status": "PASS" if errors == 0 and p95 <= threshold else "FAIL",
        "score_endpoint": endpoint,
        "query_plan": query_plan,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN, choices=("soc", "trading", "purchasing", "dataops", "s2p"))
    parser.add_argument("--requests", type=int, default=None, help="Run one benchmark size")
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[500, 1000, 2000],
        help="Decision volumes for the scaling benchmark",
    )
    parser.add_argument("--port", type=int, default=None, help="Override the configured API port")
    parser.add_argument("--output", type=Path, default=None, help="Write the JSON report to this path")
    parser.add_argument("--threshold", type=float, default=DEFAULT_P95_THRESHOLD_MS, help="p95 gate in milliseconds")
    args = parser.parse_args()
    sizes = [args.requests] if args.requests is not None else list(args.sizes)
    if not sizes or any(size <= 0 for size in sizes):
        parser.error("benchmark sizes must be positive")
    if args.threshold <= 0:
        parser.error("--threshold must be positive")

    try:
        endpoint, request_plan, config = _request_plan(args.domain, sizes[0], args.port)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: Could not prepare benchmark: {exc}", file=sys.stderr)
        return 1
    dsn = config.get("age_dsn") or os.environ.get("GRAPH_DSN") or os.environ.get("AGE_DSN")
    graph = str(
        config.get("graph")
        or config.get("graph_name")
        or os.environ.get("GRAPH_NAME", "soc_graph")
    )
    if not dsn:
        parser.error("set GRAPH_DSN or AGE_DSN for graph-size and index checks")

    connection, cursor = _age_connection(dsn, graph)
    try:
        _verify_indexes(cursor)
        query_plan = _explain_domain_query(cursor, graph, args.domain)
        reports: list[dict[str, Any]] = []
        for size in sizes:
            _, requests, _ = _request_plan(args.domain, size, args.port)
            latencies, errors = _run_requests(requests)
            graph_size = _age_scalar(
                cursor,
                graph,
                f"MATCH (d:Decision) WHERE d.domain = '{args.domain}' RETURN count(d)",
            )
            reports.append(
                _build_report(
                    args.domain,
                    size,
                    latencies,
                    errors,
                    graph_size,
                    args.threshold,
                    endpoint,
                    query_plan,
                )
            )
    finally:
        connection.close()

    first = reports[0]
    p95_by_size = {str(item["requests"]): item["p95_ms"] for item in reports}
    p95_500 = p95_by_size.get("500")
    p95_2000 = p95_by_size.get("2000")
    scaling_ratio = None
    if p95_500 and p95_2000 is not None:
        scaling_ratio = float(p95_2000) / float(p95_500)
    report = {
        **first,
        "benchmarks": reports,
        "requested_sizes": sizes,
        "p95_by_size": p95_by_size,
        "scaling_ratio_2000_to_500": scaling_ratio,
        "no_on_resurgence": scaling_ratio is None or scaling_ratio <= 4.0,
        "gate_status": "PASS"
        if all(item["gate_status"] == "PASS" for item in reports)
        and (scaling_ratio is None or scaling_ratio <= 4.0)
        else "FAIL",
    }
    print("AGE latency benchmark")
    print(f"  domain       {report['domain']}")
    print(f"  endpoint     {report['score_endpoint']}")
    print(f"  sizes        {', '.join(str(size) for size in sizes)}")
    print(f"  graph size   {report['graph_decision_count']}")
    print(f"  p50          {report['p50_ms']:.3f} ms")
    print(f"  p95          {report['p95_ms']:.3f} ms (threshold {args.threshold:.3f} ms)")
    print(f"  p99          {report['p99_ms']:.3f} ms")
    print(f"  mean         {report['mean_ms']:.3f} ms")
    print(f"  min/max      {report['min_ms']:.3f}/{report['max_ms']:.3f} ms")
    print(f"  errors       {report['error_count']}")
    print(f"  gate         {report['gate_status']}")
    print(f"  O(N) check   {'PASS' if report['no_on_resurgence'] else 'FAIL'}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  report       {args.output}")
    return 0 if report["gate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
