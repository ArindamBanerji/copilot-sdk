"""Seed and verify the approved JM $604K cross-domain scenario."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping


SCENARIO_ENTITIES: tuple[dict[str, Any], ...] = (
    {
        "entity_id": "phase6-604k-sap-change",
        "entity_type": "sap_change",
        "domain": "soc",
        "source_system": "SAP",
        "value_amount": 287000.0,
        "value_currency": "USD",
        "value_basis": "approved_phase6_scenario",
        "metadata": {
            "celonis_entity_id": "phase6-604k-celonis-process",
            "operations_entity_id": "phase6-604k-operations-context",
        },
    },
    {
        "entity_id": "phase6-604k-celonis-process",
        "entity_type": "celonis_process",
        "domain": "s2p",
        "source_system": "Celonis",
        "value_amount": 198000.0,
        "value_currency": "USD",
        "value_basis": "approved_phase6_scenario",
        "metadata": {},
    },
    {
        "entity_id": "phase6-604k-operations-context",
        "entity_type": "operations_context",
        "domain": "dataops",
        "source_system": "Operations",
        "value_amount": 119000.0,
        "value_currency": "USD",
        "value_basis": "approved_phase6_scenario",
        "metadata": {},
    },
)

SCENARIO_LINKS: tuple[tuple[str, str], ...] = (
    ("phase6-604k-sap-change", "soc"),
    ("phase6-604k-sap-change", "trading"),
    ("phase6-604k-celonis-process", "s2p"),
    ("phase6-604k-operations-context", "dataops"),
)

TOTAL_VALUE = sum(float(entity["value_amount"]) for entity in SCENARIO_ENTITIES)


def _claim_604k_query() -> str:
    """Return the exact §8.2.1 proof query."""
    return """
    MATCH (sap:DomainContext {entity_type: 'sap_change'})<-[:ABOUT]-(s:Decision),
          (sap)<-[:ABOUT]-(o:Decision),
          (cel:DomainContext {entity_type: 'celonis_process'}),
          (ops:DomainContext {entity_type: 'operations_context'})
    WHERE s.domain <> o.domain
      AND cel.entity_id = sap.metadata_celonis_entity_id
      AND ops.entity_id = sap.metadata_operations_entity_id
      AND sap.value_currency = 'USD'
      AND cel.value_currency = 'USD'
      AND ops.value_currency = 'USD'
    RETURN sap.entity_id AS finding_id,
           sum(DISTINCT sap.value_amount)
           + sum(DISTINCT cel.value_amount)
           + sum(DISTINCT ops.value_amount) AS computed_value,
           s.domain AS source_domain,
           o.domain AS other_domain
    """


def _query(store: Any, query: str) -> list[dict[str, Any]]:
    return [dict(row) for row in store._run_query(query)]


def _context_exists(store: Any, entity: Mapping[str, Any]) -> bool:
    entity_id = store._S(str(entity["entity_id"]))
    entity_type = store._S(str(entity["entity_type"]))
    rows = _query(
        store,
        f"""
        MATCH (ctx:DomainContext)
        WHERE ctx.entity_id = {entity_id}
          AND ctx.entity_type = {entity_type}
        RETURN ctx
        LIMIT 1
        """,
    )
    return bool(rows)


def _create_context(store: Any, entity: Mapping[str, Any]) -> bool:
    if _context_exists(store, entity):
        return False
    metadata = dict(entity.get("metadata") or {})
    properties = {
        "entity_id": str(entity["entity_id"]),
        "entity_type": str(entity["entity_type"]),
        "domain": str(entity["domain"]),
        "source_system": str(entity["source_system"]),
        "value_amount": float(entity["value_amount"]),
        "value_currency": str(entity["value_currency"]),
        "value_basis": str(entity["value_basis"]),
        "metadata": json.dumps(metadata, sort_keys=True, separators=(",", ":")),
    }
    if "celonis_entity_id" in metadata:
        properties["metadata_celonis_entity_id"] = str(metadata["celonis_entity_id"])
    if "operations_entity_id" in metadata:
        properties["metadata_operations_entity_id"] = str(metadata["operations_entity_id"])
    literal = ", ".join(
        f"{key}: {store._S(value) if not isinstance(value, (int, float)) else value}"
        for key, value in properties.items()
    )
    store._run_query(f"CREATE (ctx:DomainContext {{{literal}}}) RETURN ctx")
    return True


def _decision_for_domain(store: Any, domain: str) -> str | None:
    rows = _query(
        store,
        f"""
        MATCH (decision:Decision)
        WHERE decision.domain = {store._S(domain)}
        RETURN decision.decision_id AS decision_id
        ORDER BY decision.created_at ASC
        LIMIT 1
        """,
    )
    if not rows:
        return None
    value = rows[0].get("decision_id")
    return None if value is None else str(value)


def _about_edge_exists(store: Any, entity_id: str, decision_id: str, domain: str) -> bool:
    entity = next(item for item in SCENARIO_ENTITIES if item["entity_id"] == entity_id)
    rows = _query(
        store,
        f"""
        MATCH (decision:Decision {{decision_id: {store._S(decision_id)}}})
        MATCH (ctx:DomainContext {{entity_id: {store._S(entity_id)}}})
        WHERE decision.domain = {store._S(domain)}
          AND ctx.domain = {store._S(str(entity['domain']))}
        OPTIONAL MATCH (decision)-[existing_rel:ABOUT]->(ctx)
        RETURN existing_rel
        LIMIT 1
        """,
    )
    return bool(rows and rows[0].get("existing_rel") is not None)


def _create_about_edge(store: Any, entity_id: str, decision_id: str, domain: str) -> bool:
    entity = next(item for item in SCENARIO_ENTITIES if item["entity_id"] == entity_id)
    if _about_edge_exists(store, entity_id, decision_id, domain):
        return False
    store._run_query(
        f"""
        MATCH (decision:Decision {{decision_id: {store._S(decision_id)}}})
        MATCH (ctx:DomainContext {{entity_id: {store._S(entity_id)}}})
        WHERE decision.domain = {store._S(domain)}
          AND ctx.domain = {store._S(str(entity['domain']))}
        CREATE (decision)-[:ABOUT]->(ctx)
        RETURN ctx
        """,
    )
    return True


def apply_seed(store: Any) -> dict[str, int]:
    """Materialize entities and available Decision ABOUT edges."""
    created_entities = sum(_create_context(store, entity) for entity in SCENARIO_ENTITIES)
    created_edges = 0
    missing_decisions = 0
    for entity_id, domain in SCENARIO_LINKS:
        decision_id = _decision_for_domain(store, domain)
        if decision_id is None:
            print(
                f"FAIL: no Decision found in domain '{domain}' — "
                "run learn cycles first (P6.3a)"
            )
            sys.exit(1)
        created_edges += _create_about_edge(store, entity_id, decision_id, domain)
    return {
        "created_entities": created_entities,
        "created_edges": created_edges,
        "missing_decisions": missing_decisions,
    }


def verify_seed(store: Any) -> list[dict[str, Any]]:
    return _query(store, _claim_604k_query())


def _load_age_store(age_dsn: str, graph_name: str) -> Any:
    from scripts.phase6_claim_proof import _load_age_store as load_store

    return load_store(age_dsn, graph_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the JM $604K scenario")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without writing")
    parser.add_argument("--apply", action="store_true", help="write the scenario to AGE")
    parser.add_argument("--verify", action="store_true", help="run the §8.2.1 proof query")
    parser.add_argument("--age-dsn")
    parser.add_argument("--graph-name", default="soc_graph")
    args = parser.parse_args(argv)

    if not args.apply and not args.verify:
        print("Dry-run: no graph writes")
        print(f"DomainContext entities: {len(SCENARIO_ENTITIES)}")
        print(f"Computed scenario value: {TOTAL_VALUE:.1f}")
        print(f"ABOUT links planned: {len(SCENARIO_LINKS)}")
        return 0
    if not args.age_dsn:
        parser.error("--age-dsn is required with --apply or --verify")
    store = _load_age_store(args.age_dsn, args.graph_name)
    try:
        if args.apply:
            print(json.dumps(apply_seed(store), sort_keys=True))
        if args.verify:
            rows = verify_seed(store)
            print(json.dumps(rows, sort_keys=True, default=str))
            if not rows:
                print("FAIL: §8.2.1 query returned no rows")
                sys.exit(1)
            computed_values: list[float] = []
            domains: set[str] = set()
            for result in rows:
                computed_raw = result.get("computed_value")
                try:
                    if computed_raw is not None:
                        computed_values.append(float(computed_raw))
                except (TypeError, ValueError):
                    continue
                for field in ("source_domain", "other_domain"):
                    domain = result.get(field)
                    if domain is not None:
                        domains.add(str(domain))
                for field in ("source_domains", "other_domains"):
                    values = result.get(field)
                    if isinstance(values, (list, tuple, set)):
                        domains.update(str(domain) for domain in values)
            matching_value = next(
                (value for value in computed_values if value == 604000.0),
                None,
            )
            if matching_value is not None and len(domains) >= 2:
                print(
                    f"PASS: computed_value={matching_value:.1f}, "
                    f"distinct_domains={len(domains)}"
                )
                sys.exit(0)
            displayed_value = computed_values[0] if computed_values else float("nan")
            print(
                f"FAIL: computed_value={displayed_value!r}, "
                f"distinct_domains={len(domains)} (expected 604000.0 and >= 2)"
            )
            sys.exit(1)
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
