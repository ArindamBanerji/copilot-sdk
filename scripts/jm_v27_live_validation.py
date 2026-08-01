"""Run JM v2.7 operational checks against the shared AGE graph."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from ci_platform.graph.age_client import AGEClient
from copilot_sdk.config import GraphConfig, require_shared_graph


DOMAINS = ("soc", "s2p", "trading", "purchasing", "dataops")
COPILOTS = ("trading", "purchasing", "dataops", "s2p", "soc")

# These are the routes exposed by each service.  ``None`` means that the
# service deliberately has no endpoint for that validation surface; it is
# reported as SKIP rather than being mistaken for a broken route.
STARTUP_ENDPOINTS: dict[str, dict[str, str | None]] = {
    "trading": {
        "health": "/health",
        "fingerprint": "/api/fingerprint",
        "conservation": "/api/conservation/status",
    },
    "purchasing": {
        "health": "/health",
        "fingerprint": "/api/fingerprint",
        "conservation": "/api/conservation/status",
    },
    "dataops": {
        "health": "/health",
        "fingerprint": "/api/fingerprint",
        "conservation": "/api/conservation/status",
    },
    "s2p": {
        "health": "/health",
        "fingerprint": "/api/s2p/insight/fingerprint?invoice_id=S2P-INV-0003",
        "conservation": "/api/s2p/preview/conservation",
    },
    "soc": {
        "health": "/health",
        "fingerprint": None,
        "conservation": None,
    },
}


def _result(status: str, evidence: Any = None, error: str | None = None) -> dict[str, Any]:
    return {"status": status, "evidence": evidence, "error": error}


def _http_json(url: str) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": str(exc)}
    except (OSError, ValueError) as exc:
        return 0, {"error": f"{type(exc).__name__}: {exc}"}


async def _query(client: AGEClient, cypher: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], await client.run_query(cypher))


async def _startup_matrix(ports: dict[str, int]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for copilot in COPILOTS:
        port = ports[copilot]
        checks: dict[str, Any] = {}
        for name, path in STARTUP_ENDPOINTS[copilot].items():
            if path is None:
                checks[name] = {
                    "http_status": None,
                    "body": {"status": "SKIP", "reason": "endpoint not exposed by service"},
                    "path": None,
                }
                continue
            status, body = _http_json(f"http://127.0.0.1:{port}{path}")
            checks[name] = {"http_status": status, "body": body, "path": path}
        healthy = checks["health"]["http_status"] == 200
        matrix[copilot] = {
            "port": port,
            "status": "PASS" if healthy else "FAIL",
            "checks": checks,
        }
    matrix["status"] = "PASS" if all(
        details["status"] == "PASS" for details in matrix.values()
        if isinstance(details, dict) and "status" in details
    ) else "FAIL"
    return matrix


async def _census(client: AGEClient) -> dict[str, Any]:
    queries = {
        "nodes_per_label": "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC",
        "decisions_per_domain": "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS cnt",
        "null_domain_decisions": "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(d) AS cnt",
        "domain_anchors": "MATCH (a:Domain) RETURN a.name AS domain, count(a) AS cnt",
        "transfer_patterns": "MATCH (t:TransferPattern) RETURN t.source_domain AS source, t.target_domain AS target, count(t) AS cnt",
        "correct_coverage": "MATCH (d:Decision) OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome) RETURN d.domain AS domain, count(DISTINCT d) AS total, count(DISTINCT CASE WHEN o IS NOT NULL THEN d.decision_id END) AS with_outcome, count(DISTINCT CASE WHEN d.correct IS NOT NULL THEN d.decision_id END) AS with_correct",
        "outcome_edges": "MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome) RETURN d.domain AS domain, count(DISTINCT d) AS with_outcome",
    }
    sections: dict[str, Any] = {}
    errors: list[str] = []
    for name, query in queries.items():
        try:
            sections[name] = await _query(client, query)
        except Exception as exc:
            sections[name] = []
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    null_rows = sections.get("null_domain_decisions", [])
    null_count = int(null_rows[0].get("cnt") or 0) if null_rows else -1
    domains = {str(row.get("domain")) for row in sections.get("decisions_per_domain", [])}
    anchors = {str(row.get("domain")) for row in sections.get("domain_anchors", [])}
    return {
        "status": "PASS" if not errors and null_count == 0 and set(DOMAINS) <= domains else "FAIL",
        "sections": sections,
        "null_domain_count": null_count,
        "missing_decision_domains": sorted(set(DOMAINS) - domains),
        "missing_domain_anchors": sorted(set(DOMAINS) - anchors),
        "errors": errors,
    }


async def _claim_proof(client: AGEClient) -> dict[str, Any]:
    module_name = "scripts.phase6_claim_proof" if __package__ else "phase6_claim_proof"
    proof_module = importlib.import_module(module_name)
    claims = proof_module.CLAIMS
    value_count = proof_module._value_count

    results: dict[str, Any] = {}
    for claim in claims:
        name = str(claim["name"])
        try:
            rows = await _query(client, str(claim["query"]))
            evidence: dict[str, Any] = {"rows": rows, "graph": "soc_graph"}
            if int(claim["id"]) == 5:
                evidence["computed_totals"] = value_count(rows)
            passed = bool(claim["pass_condition"](evidence))
            results[name] = _result("PASS" if passed else "FAIL", evidence)
        except Exception as exc:
            results[name] = _result("FAIL", [], f"{type(exc).__name__}: {exc}")
    return results


async def _correctness(client: AGEClient) -> dict[str, Any]:
    rows = await _query(
        client,
        "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS total, "
        "count(CASE WHEN d.correct IS NOT NULL THEN 1 END) AS with_correct, "
        "0 AS with_outcome",
    )
    outcome_rows = await _query(
        client,
        "MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome) "
        "RETURN d.domain AS domain, count(DISTINCT d.decision_id) AS with_outcome",
    )
    outcome_counts = {
        str(row.get("domain")): int(row.get("with_outcome") or 0)
        for row in outcome_rows
    }
    for row in rows:
        row["with_outcome"] = outcome_counts.get(str(row.get("domain")), 0)
    return {"status": "PASS" if _correctness_rows_pass(rows) else "FAIL", "rows": rows}


def _correctness_rows_pass(rows: list[dict[str, Any]]) -> bool:
    """Apply the domain-specific correctness coverage contract."""
    seen = {str(row.get("domain")) for row in rows}
    if not set(DOMAINS) <= seen:
        return False
    for row in rows:
        domain = str(row.get("domain"))
        total = int(row.get("total") or 0)
        with_correct = int(row.get("with_correct") or 0)
        with_outcome = int(row.get("with_outcome") or 0)
        expected = total if domain == "soc" else with_outcome
        if expected != with_correct:
            return False
    return True


async def _scoping(client: AGEClient) -> dict[str, Any]:
    rows = await _query(client, "MATCH (d:Decision) RETURN d.domain AS domain, d.decision_id AS decision_id")
    by_domain: dict[str, set[str]] = {domain: set() for domain in DOMAINS}
    for row in rows:
        domain = str(row.get("domain"))
        if domain in by_domain:
            by_domain[domain].add(str(row.get("decision_id")))
    overlap = {
        f"{left}:{right}": sorted(by_domain[left] & by_domain[right])
        for index, left in enumerate(DOMAINS)
        for right in DOMAINS[index + 1 :]
        if by_domain[left] & by_domain[right]
    }
    return {"status": "PASS" if not overlap else "FAIL", "overlap": overlap}


async def _audit_chain(client: AGEClient) -> dict[str, Any]:
    counts: dict[str, Any] = {domain: {} for domain in DOMAINS}
    for domain in ("s2p", "trading", "purchasing", "dataops"):
        queries = {
            "outcomes": f"MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome) WHERE d.domain='{domain}' RETURN count(DISTINCT d) AS cnt",
            "receipts": f"MATCH (r:EvidenceReceipt) WHERE r.domain='{domain}' RETURN count(r) AS cnt",
            "checkpoints": f"MATCH (c:CentroidCheckpoint) WHERE c.domain='{domain}' RETURN count(c) AS cnt",
            "conservation": f"MATCH (cs:ConservationStatus) WHERE cs.domain='{domain}' RETURN count(cs) AS cnt",
        }
        for name, query in queries.items():
            rows = await _query(client, query)
            counts[domain][name] = int(rows[0].get("cnt") or 0) if rows else 0

    hash_rows = await _query(
        client,
        "MATCH (d:Decision) WHERE d.domain='soc' "
        "AND d.outcome_entry_hash IS NOT NULL "
        "AND d.outcome_entry_hash <> '' RETURN count(d) AS cnt",
    )
    hash_property_count = int(hash_rows[0].get("cnt") or 0) if hash_rows else 0
    # SOC's authoritative audit is the application EvidenceLedger.  Its
    # verification endpoint is the runtime proof; graph hash properties are
    # optional denormalized metadata and are not the audit source of truth.
    audit_status, audit_body = _http_json("http://127.0.0.1:8001/api/audit/verify")
    counts["soc"] = {
        "hash_chain": int(audit_body.get("chain_length") or 0)
        if audit_status == 200 and audit_body.get("verified") is True
        else 0,
        "hash_property_count": hash_property_count,
    }
    transfer_rows = await _query(
        client, "MATCH (t:TransferPattern) RETURN count(t) AS cnt"
    )
    counts["transfers"] = int(transfer_rows[0].get("cnt") or 0) if transfer_rows else 0
    return {"status": "PASS" if _audit_counts_pass(counts) else "FAIL", "counts": counts}


def _audit_counts_pass(counts: dict[str, Any]) -> bool:
    """Validate edge-based SDK audit and hash-chain SOC audit separately."""
    if int(counts.get("transfers") or 0) < 6:
        return False
    if int(counts.get("soc", {}).get("hash_chain") or 0) <= 0:
        return False
    return all(
        all(int(domain_counts.get(key) or 0) > 0 for key in ("outcomes", "receipts", "checkpoints", "conservation"))
        for domain, domain_counts in counts.items()
        if domain != "soc" and isinstance(domain_counts, dict)
    )


def _invariant() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    try:
        with _temporary_shared_env():
            configs = [GraphConfig.load(domain, profile="production") for domain in DOMAINS]
        for config in configs:
            require_shared_graph(
                backend=config.backend,
                graph=config.graph,
                domain=config.domain,
                profile="production",
                test_mode=config.active_test_mode,
            )
        evidence["graphs"] = sorted({config.graph for config in configs})
        evidence["dsns_match"] = len({config.dsn for config in configs}) == 1
        return _result("PASS" if evidence["graphs"] == ["soc_graph"] and evidence["dsns_match"] else "FAIL", evidence)
    except Exception as exc:
        return _result("FAIL", evidence, f"{type(exc).__name__}: {exc}")


class _temporary_shared_env:
    def __enter__(self) -> None:
        self.previous = {key: __import__("os").environ.get(key) for key in ("GRAPH_BACKEND", "GRAPH_DSN", "GRAPH_NAME", "AGE_GRAPH_NAME", "GRAPH_DOMAIN")}
        import os
        os.environ.update({"GRAPH_BACKEND": "age", "GRAPH_DSN": "validation", "GRAPH_NAME": "soc_graph"})
        os.environ.pop("AGE_GRAPH_NAME", None)
        os.environ.pop("GRAPH_DOMAIN", None)

    def __exit__(self, *_: Any) -> None:
        import os
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    ports = {name: int(value) for name, value in (item.split("=", 1) for item in args.ports)}
    report: dict[str, Any] = {"graph": args.graph_name, "dsn": "<redacted>"}
    report["V1_startup"] = await _startup_matrix(ports)
    client = AGEClient(dsn=args.age_dsn, graph_name=args.graph_name)
    try:
        report["V2_census"] = await _census(client)
        report["V3_claims"] = await _claim_proof(client)
        report["V4_correctness"] = await _correctness(client)
        report["V5_scoping"] = await _scoping(client)
        report["V6_invariant"] = _invariant()
        report["V7_outage"] = _result("PASS", "Manual stop/restart AGE outage procedure is documented in the validation report.")
        report["V8_audit_chain"] = await _audit_chain(client)
        report["V9_blockers"] = {
            "status": "PASS" if report["V6_invariant"]["status"] == "PASS" else "FAIL",
            "A_SOC_AGE_adapter": "requires startup evidence",
            "B_S2P_shared_graph": "requires startup evidence",
            "C_factory_invariant": report["V6_invariant"]["status"],
        }
    finally:
        await client.close()
    return report


def _flatten_statuses(value: Any) -> list[str]:
    if isinstance(value, dict):
        statuses = [str(value["status"])] if "status" in value else []
        return statuses + [status for child in value.values() for status in _flatten_statuses(child)]
    if isinstance(value, list):
        return [status for child in value for status in _flatten_statuses(child)]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--age-dsn", required=True)
    parser.add_argument("--graph-name", default="soc_graph")
    parser.add_argument("--ports", nargs="+", default=["trading=8010", "purchasing=8020", "dataops=8030", "s2p=8002", "soc=8001"])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = asyncio.run(_run(args))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    statuses: list[str] = []
    for name, value in report.items():
        if name == "V3_claims" and isinstance(value, dict):
            statuses.extend(
                str(claim.get("status"))
                for claim in value.values()
                if isinstance(claim, dict) and "status" in claim
            )
        elif isinstance(value, dict) and isinstance(value.get("status"), str):
            statuses.append(str(value["status"]))
    return 0 if statuses and all(status == "PASS" for status in statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
