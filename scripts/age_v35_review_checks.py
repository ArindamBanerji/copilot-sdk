"""Read-only checks for the AGE v3.5 migration-plan review findings."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import psycopg


DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"
V35_VERTEX_LABELS = {
    "Decision", "Alert", "Campaign", "CampaignSeed", "Asset", "User",
    "ShadowDecision", "AttackPattern", "ThreatIndicator", "ThreatIntel",
    "PipelineSystem", "DataQualityAlert", "DeploymentState", "ProfileSnapshot",
    "Outcome", "EvidenceReceipt", "CentroidCheckpoint",
    "DecisionDistanceLog", "DecisionEntityLink", "EvolutionEvent",
    "L5Centroid", "L5ConservationState", "L5DKWeight", "L5DKWeightArchive",
}
DOMAINS = ("trading", "purchasing", "dataops", "s2p")


def section(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def scalar(conn: Any, cypher: str, columns: str) -> int:
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {cypher} $$) AS ({columns})"
    row = conn.execute(sql).fetchone()
    return int(str(row[0])) if row else 0


def age_labels(conn: Any, kind: str) -> list[str]:
    graph_oid = conn.execute(
        "SELECT graphid FROM ag_graph WHERE name = %s", (GRAPH,)
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT name FROM ag_label "
        f"WHERE graph = {int(graph_oid)}::oid AND kind = %s ORDER BY name",
        (kind,),
    ).fetchall()
    return [str(row[0]) for row in rows if not str(row[0]).startswith("_")]


def db_path(domain: str) -> Path:
    base = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".ci-platform"
    primary = base / domain / f"{domain}.db"
    if primary.exists():
        return primary
    if domain == "s2p":
        fallback = (
            Path(__file__).resolve().parents[2].parent / "s2p-copilot"
            / "backend" / "app" / "data" / "s2p.db"
        )
        if fallback.exists():
            return fallback
    raise FileNotFoundError(f"No SQLite DB for {domain}: {primary}")


def open_sqlite(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def nonempty_json(column: str, empty: tuple[str, ...]) -> str:
    quoted = ", ".join("?" for _ in empty)
    return f"{column} IS NOT NULL AND trim({column}) <> '' AND trim({column}) NOT IN ({quoted})"


def sqlite_inventory(domain: str) -> dict[str, Any]:
    path = db_path(domain)
    with open_sqlite(path) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(decisions)")}
        required = {
            "status", "factor_vector_json", "confidence", "probabilities_json",
            "factors_json", "recommended_action", "category_index", "category",
            "created_at",
        }
        missing = sorted(required - columns)
        if missing:
            raise RuntimeError(f"{domain} decisions schema missing: {missing}")

        where = "(status = 'pending' OR status IS NULL)"
        def count(predicate: str = "1=1", params: tuple[Any, ...] = ()) -> int:
            return int(conn.execute(
                f"SELECT count(*) FROM decisions WHERE {where} AND ({predicate})", params
            ).fetchone()[0])

        factor = nonempty_json("factor_vector_json", ("[]", "null"))
        probability = nonempty_json("probabilities_json", ("[]", "null"))
        factors = nonempty_json("factors_json", ("{}", "null"))
        metrics = {
            "unverified": count(),
            "factor_vector": count(factor, ("[]", "null")),
            "confidence_positive": count("confidence > 0"),
            "probabilities": count(probability, ("[]", "null")),
            "factors": count(factors, ("{}", "null")),
            "recommended_action": count("recommended_action IS NOT NULL AND trim(recommended_action) <> ''"),
            "category_index": count("category_index IS NOT NULL"),
        }
        categories = conn.execute(
            f"SELECT coalesce(category, 'NULL') AS category, count(*) AS n "
            f"FROM decisions WHERE {where} GROUP BY category ORDER BY n DESC, category LIMIT 10"
        ).fetchall()
        times = conn.execute(
            f"SELECT min(created_at) AS min_created, max(created_at) AS max_created "
            f"FROM decisions WHERE {where}"
        ).fetchone()
        small_columns = (
            "decision_id, domain, category, category_index, recommended_action, "
            "confidence, status, created_at"
        )
        samples_pending = conn.execute(
            f"SELECT {small_columns} FROM decisions WHERE {where} ORDER BY created_at LIMIT 3"
        ).fetchall()
        samples_verified = conn.execute(
            f"SELECT {small_columns} FROM decisions "
            "WHERE status IN ('confirmed', 'overridden') ORDER BY created_at LIMIT 3"
        ).fetchall()
        return {
            "path": path, "metrics": metrics, "categories": categories, "times": times,
            "pending": samples_pending, "verified": samples_verified,
        }


def print_rows(rows: list[sqlite3.Row]) -> None:
    for row in rows:
        print(f"    {dict(row)}")


def finding_one() -> dict[str, dict[str, Any]]:
    section("FINDING 1 - UNVERIFIED SQLITE DECISIONS")
    results: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        result = sqlite_inventory(domain)
        results[domain] = result
        m = result["metrics"]
        print(f"\n{domain}: {result['path']}")
        print(
            "  unverified={unverified} factor_vector={factor_vector} confidence_gt_0="
            "{confidence_positive} probabilities={probabilities} factors={factors} "
            "action={recommended_action} category_index={category_index}".format(**m)
        )
        print("  categories:", [(row["category"], row["n"]) for row in result["categories"]])
        print(f"  created_at_range=({result['times']['min_created']}, {result['times']['max_created']})")
        print("  unverified samples:")
        print_rows(result["pending"])
        print("  verified samples:")
        print_rows(result["verified"])
    return results


def finding_two(conn: Any) -> tuple[list[str], list[str]]:
    section("FINDING 2 - COMPLETE LIVE AGE CATALOG")
    vertices = age_labels(conn, "v")
    edges = age_labels(conn, "e")
    print(f"VERTEX_LABELS={len(vertices)} EDGE_LABELS={len(edges)}")
    print("\nVERTICES:")
    for label in vertices:
        count = scalar(conn, f"MATCH (n:{label}) RETURN count(n)", "cnt agtype")
        flag = "MISSING_FROM_V35" if label not in V35_VERTEX_LABELS else "IN_V35"
        print(f"  {label}: {count} {flag}")
    print("\nEDGES:")
    for label in edges:
        count = scalar(conn, f"MATCH ()-[r:{label}]->() RETURN count(r)", "cnt agtype")
        print(f"  {label}: {count}")
    return vertices, edges


def finding_three(conn: Any) -> dict[str, Any]:
    section("FINDING 3 - EVOLUTIONEVENT TOPOLOGY")
    domains = conn.execute(
        f"SELECT * FROM cypher('{GRAPH}', $$ "
        "MATCH (e:EvolutionEvent) RETURN e.domain AS domain, count(e) AS cnt "
        "$$) AS (domain agtype, cnt agtype)"
    ).fetchall()
    incoming = scalar(conn, "MATCH ()-[r]->(e:EvolutionEvent) RETURN count(r)", "cnt agtype")
    outgoing = scalar(conn, "MATCH (e:EvolutionEvent)-[r]->() RETURN count(r)", "cnt agtype")
    # Compute the cross-label identifier overlap in Python because AGE joins
    # on agtype properties are not needed for this read-only discriminator.
    decision_rows = conn.execute(
        f"SELECT * FROM cypher('{GRAPH}', $$ MATCH (d:Decision) RETURN d.decision_id $$) "
        "AS (did agtype)"
    ).fetchall()
    event_rows = conn.execute(
        f"SELECT * FROM cypher('{GRAPH}', $$ MATCH (e:EvolutionEvent) RETURN e.triggered_by $$) "
        "AS (triggered_by agtype)"
    ).fetchall()
    decision_ids = {str(row[0]).strip('"') for row in decision_rows}
    triggers = [str(row[0]).strip('"') for row in event_rows if str(row[0]).strip('"') not in {"null", ""}]
    trigger_overlap = sum(1 for value in triggers if value in decision_ids)
    decision_to_event = scalar(
        conn,
        "MATCH (d:Decision)-[r:TRIGGERED_EVOLUTION]->(e:EvolutionEvent) RETURN count(r)",
        "cnt agtype",
    )
    alert_to_entity = scalar(
        conn,
        "MATCH (a:Alert)-[r:TRIGGERED_EVOLUTION]->(e:Entity) RETURN count(r)",
        "cnt agtype",
    )
    triggered_total = scalar(conn, "MATCH ()-[r:TRIGGERED_EVOLUTION]->() RETURN count(r)", "cnt agtype")
    samples = conn.execute(
        f"SELECT * FROM cypher('{GRAPH}', $$ MATCH (e:EvolutionEvent) RETURN properties(e) LIMIT 3 $$) "
        "AS (props agtype)"
    ).fetchall()
    print("  domains:", [(str(row[0]), int(str(row[1]))) for row in domains])
    print(f"  edges_into={incoming} edges_from={outgoing}")
    print(f"  triggered_by_with_decision_overlap={trigger_overlap}/{len(triggers)}")
    print(f"  Decision->EvolutionEvent={decision_to_event}")
    print(f"  Alert->Entity={alert_to_entity}")
    print(f"  TRIGGERED_EVOLUTION_total={triggered_total}")
    for row in samples:
        print(f"  sample={str(row[0])[:500]}")
    return {
        "incoming": incoming, "outgoing": outgoing, "trigger_overlap": trigger_overlap,
        "trigger_total": triggered_total, "decision_to_event": decision_to_event,
        "alert_to_entity": alert_to_entity,
    }


def ghost_classification(result: dict[str, Any]) -> str:
    m = result["metrics"]
    if m["unverified"] == 0:
        return "no unverified rows"
    if m["factor_vector"] == 0:
        return "ghost candidate: no unverified factor_vector_json"
    if m["factor_vector"] == m["unverified"]:
        return "pending work: every unverified row has factor_vector_json"
    return f"mixed: {m['factor_vector']}/{m['unverified']} have factor_vector_json"


def main() -> None:
    sqlite_results = finding_one()
    with psycopg.connect(DSN) as conn:
        conn.autocommit = True
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        vertices, _edges = finding_two(conn)
        evolution = finding_three(conn)

    missing = [label for label in vertices if label not in V35_VERTEX_LABELS]
    section("SUMMARY")
    print("GHOST_DISCRIMINATOR: no factor_vector_json")
    for domain in DOMAINS:
        print(f"{domain.upper()}: {ghost_classification(sqlite_results[domain])}")
    print("MISSING_LABELS:", ", ".join(missing))
    if evolution["incoming"] == 0 and evolution["outgoing"] == 0 and evolution["trigger_overlap"] == 0:
        evolution_verdict = "stale SDK artifact"
    elif evolution["trigger_overlap"] > 0:
        evolution_verdict = "mixed"
    else:
        evolution_verdict = "live SOC data without canonical graph links"
    print(f"EVOLUTION_EVENT: {evolution_verdict}")
    print(f"EVOLUTION_EVENT_EDGES: {evolution['incoming']} in, {evolution['outgoing']} out")
    print(
        "TRIGGERED_EVOLUTION_TOPOLOGY: "
        f"Decision->EvolutionEvent={evolution['decision_to_event']}; "
        f"Alert->Entity={evolution['alert_to_entity']}; total={evolution['trigger_total']}"
    )


if __name__ == "__main__":
    main()
