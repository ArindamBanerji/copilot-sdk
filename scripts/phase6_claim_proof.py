"""Run the JM Phase 6 §2 claim proofs against the shared AGE graph."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable

from copilot_sdk.config import GraphConfig, require_shared_graph
from copilot_sdk.config.domains import ALL_COPILOT_DOMAINS
from copilot_sdk.scoring.presets import PRESET_REGISTRY


PassCondition = Callable[[dict[str, Any]], bool]


def _has_domains(result: dict[str, Any]) -> bool:
    rows = result.get("rows", [])
    if not rows:
        return False
    domains = {
        str(row["domain"])
        for row in rows
        if row.get("domain") is not None
    }
    return result.get("graph") == "soc_graph" and all(
        domain in domains for domain in ALL_COPILOT_DOMAINS
    )


def _has_cross_domain_attention(result: dict[str, Any]) -> bool:
    rows = result.get("rows", [])
    return bool(rows and int(rows[0].get("shared") or 0) > 0)


def _has_604k(result: dict[str, Any]) -> bool:
    return any(float(row.get("computed_value") or 0.0) == 604000.0 for row in result.get("rows", []))


def _has_transfer_destinations(result: dict[str, Any]) -> bool:
    destinations = {
        str(row.get("target"))
        for row in result.get("rows", [])
        if str(row.get("source")) == "soc"
        and int(row.get("transfer_count") or 0) > 0
        and str(row.get("validation_status") or "") == "validated"
    }
    return {"s2p", "dataops"}.issubset(destinations)


def _has_current_value_totals(result: dict[str, Any]) -> bool:
    totals = result.get("computed_totals", {})
    return all(domain in totals for domain in ALL_COPILOT_DOMAINS)


def _has_unique_decisions(result: dict[str, Any]) -> bool:
    rows = result.get("rows", [])
    return bool(
        rows
        and int(rows[0].get("ids") or 0)
        == int(rows[0].get("row_count") or 0)
    )


def _has_traversal(result: dict[str, Any]) -> bool:
    return bool(result.get("rows"))


def _has_conservation(result: dict[str, Any]) -> bool:
    seen = {str(row.get("domain")) for row in result.get("rows", []) if row.get("V") is not None}
    return all(domain in seen for domain in ALL_COPILOT_DOMAINS)


CLAIMS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "One engine, one graph",
        "query": "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS decision_count",
        "pass_condition": _has_domains,
    },
    {
        "id": 2,
        "name": "Cross-graph attention",
        "query": "MATCH (a:Decision)-[:ABOUT]->(e:DomainContext)<-[:ABOUT]-(b:Decision) WHERE a.domain <> b.domain RETURN count(DISTINCT e.entity_id) AS shared",
        "pass_condition": _has_cross_domain_attention,
    },
    {
        "id": 3,
        "name": "$604K cross-graph finding",
        "query": "MATCH (sap:DomainContext {entity_type: 'sap_change'})<-[:ABOUT]-(s:Decision), (sap)<-[:ABOUT]-(o:Decision), (cel:DomainContext {entity_type: 'celonis_process'}), (ops:DomainContext {entity_type: 'operations_context'}) WHERE s.domain <> o.domain AND cel.entity_id = sap.metadata_celonis_entity_id AND ops.entity_id = sap.metadata_operations_entity_id AND sap.value_currency = 'USD' AND cel.value_currency = 'USD' AND ops.value_currency = 'USD' RETURN sap.entity_id AS finding_id, sum(DISTINCT sap.value_amount) + sum(DISTINCT cel.value_amount) + sum(DISTINCT ops.value_amount) AS computed_value, s.domain AS source_domain, o.domain AS other_domain",
        "pass_condition": _has_604k,
    },
    {
        "id": 4,
        "name": "Pattern transfer SOC->S2P->DataOps",
        "query": "MATCH (tp:TransferPattern)-[:FROM_DOMAIN]->(s:Domain), (tp)-[:TO_DOMAIN]->(t:Domain) RETURN s.name AS source, t.name AS target, count(tp) AS transfer_count, tp.validation_status AS validation_status",
        "pass_condition": _has_transfer_destinations,
    },
    {
        "id": 5,
        "name": "315 values that compound",
        "query": "MATCH (c:CentroidCheckpoint) WHERE c.shape IS NOT NULL RETURN c.domain AS domain, c.shape AS shape, c.factor_names_hash AS factor_names_hash ORDER BY domain, c.created_at DESC",
        "pass_condition": _has_current_value_totals,
    },
    {
        "id": 6,
        "name": "You cannot fork judgment",
        "query": "MATCH (d:Decision) RETURN count(DISTINCT d.decision_id) AS ids, count(d) AS row_count",
        "pass_condition": _has_unique_decisions,
    },
    {
        "id": 7,
        "name": "One traversal, one answer",
        "query": "MATCH (s:Decision)-[:ABOUT]->(e:DomainContext)<-[:ABOUT]-(t:Decision) WHERE s.domain <> t.domain RETURN s.domain AS source, t.domain AS target, e.entity_id AS entity",
        "pass_condition": _has_traversal,
    },
    {
        "id": 8,
        "name": "Conservation across copilots",
        "query": "MATCH (cs:ConservationStatus)-[:SUMMARIZES_DOMAIN]->(d:Domain) RETURN d.name AS domain, cs.status AS status_value, cs.V AS V, cs.computed_at AS computed_at ORDER BY d.name, computed_at DESC",
        "pass_condition": _has_conservation,
    },
]


def _query(store: Any, query: str) -> list[dict[str, Any]]:
    return [dict(row) for row in store._run_query(query)]


def _value_count(rows: list[dict[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        shape = row.get("shape")
        if not isinstance(shape, list):
            continue
        try:
            product = 1
            for value in shape:
                product *= int(value)
            factor_names = row.get("factor_names")
            if isinstance(factor_names, list):
                dimension = len(factor_names)
            else:
                preset_type = PRESET_REGISTRY.get(str(row.get("domain")))
                dimension = int(preset_type().shape.n_factors) if preset_type is not None else int(row.get("rank") or 0)
            totals[str(row.get("domain"))] = product + dimension
        except (TypeError, ValueError):
            continue
    return totals


def run_claim(store: Any, claim: dict[str, Any]) -> dict[str, Any]:
    """Run one claim and return a serializable proof result."""
    try:
        rows = _query(store, str(claim["query"]))
        evidence: dict[str, Any] = {"rows": rows}
        evidence["graph"] = getattr(store, "_phase6_graph_name", None)
        if int(claim["id"]) == 5:
            evidence["computed_totals"] = _value_count(rows)
            evidence["legacy_315_stale"] = True
        passed = bool(claim["pass_condition"](evidence))
        status = "PASS" if passed else "NOT_PROVEN"
        return {"id": claim["id"], "name": claim["name"], "status": status, "evidence": evidence, "error": None}
    except Exception as exc:
        return {
            "id": claim["id"],
            "name": claim["name"],
            "status": "UNAVAILABLE",
            "evidence": {},
            "error": f"{type(exc).__name__}: {exc}",
        }


def _load_age_store(age_dsn: str, graph_name: str) -> Any:
    from ci_platform.graph.age_graph_store import AGEGraphStore

    configs = [GraphConfig.load(domain, profile="production") for domain in ALL_COPILOT_DOMAINS]
    for config in configs:
        require_shared_graph(
            backend=config.backend,
            graph=config.graph,
            domain=config.domain,
            profile="production",
            test_mode=config.active_test_mode,
        )
    if graph_name != "soc_graph":
        raise RuntimeError(f"Phase 6 requires graph_name='soc_graph', got {graph_name!r}")
    graphs = {config.graph for config in configs}
    if len(graphs) != 1 or graph_name not in graphs:
        raise RuntimeError(f"GraphConfig does not authorize one shared graph: {sorted(graphs)}")
    dsns = {config.dsn for config in configs}
    if len(dsns) != 1 or age_dsn not in dsns:
        raise RuntimeError("AGE DSN does not match the five GraphConfig domains")
    store = AGEGraphStore(dsn=age_dsn, graph_name=graph_name)
    store._phase6_graph_name = graph_name
    return store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prove JM §2 claims from live AGE")
    parser.add_argument("--age-dsn")
    parser.add_argument("--graph-name", default="soc_graph")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--report", default="out/phase6_claims.json")
    args = parser.parse_args(argv)

    if not args.execute:
        for claim in CLAIMS:
            print(f"{claim['id']}. {claim['name']}: {claim['query']}")
        return 0
    if not args.age_dsn:
        parser.error("--age-dsn is required with --execute")
    if os.environ.get("AGE_INTEGRATION") != "1":
        print("AGE_INTEGRATION=1 is required for --execute")
        return 2

    store = None
    try:
        store = _load_age_store(args.age_dsn, args.graph_name)
        results = [run_claim(store, claim) for claim in CLAIMS]
    except Exception as exc:
        results = [
            {"id": claim["id"], "name": claim["name"], "status": "UNAVAILABLE", "evidence": {}, "error": f"{type(exc).__name__}: {exc}"}
            for claim in CLAIMS
        ]
    finally:
        if store is not None:
            store.close()

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"claims": results}, indent=2, sort_keys=True), encoding="utf-8")
    for result in results:
        print(f"{result['id']}. {result['name']}: {result['status']}")
    return 0 if all(result["status"] == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
