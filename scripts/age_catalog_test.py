"""Diagnose AGE catalog label filtering for soc_graph."""

from __future__ import annotations

import psycopg


DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"


def _report(name: str, rows: list[tuple[object, ...]]) -> None:
    vertices = sum(1 for row in rows if str(row[1]) == "v")
    edges = sum(1 for row in rows if str(row[1]) == "e")
    print(f"{name}: {len(rows)} labels ({vertices} vertex, {edges} edge)")


def _user_labels(rows: list[tuple[object, ...]]) -> list[tuple[object, ...]]:
    return [row for row in rows if not str(row[0]).startswith("_")]


def main() -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute("SET search_path = ag_catalog, public")
        graphid = conn.execute(
            "SELECT graphid FROM ag_graph WHERE name = %s", (GRAPH,)
        ).fetchone()[0]
        print(f"graphid: {graphid}")

        attempts: list[tuple[str, list[tuple[object, ...]]]] = []
        attempts.append((
            "literal_oid_cast",
            _user_labels(conn.execute(
                "SELECT name, kind FROM ag_label "
                f"WHERE graph = {int(graphid)}::oid "
                "ORDER BY kind, name"
            ).fetchall()),
        ))
        attempts.append((
            "graphid_subquery",
            _user_labels(conn.execute(
                "SELECT name, kind FROM ag_label "
                "WHERE graph = (SELECT graphid FROM ag_graph WHERE name = %s) "
                "ORDER BY kind, name",
                (GRAPH,),
            ).fetchall()),
        ))
        all_rows = conn.execute(
            "SELECT name, kind, graph FROM ag_label"
        ).fetchall()
        attempts.append((
            "python_filter",
            _user_labels([
                (name, kind)
                for name, kind, graph in all_rows
                if int(graph) == int(graphid)
            ]),
        ))

        for name, rows in attempts:
            _report(name, rows)

        for name, rows in attempts:
            if len(rows) == 73:
                print(f"CATALOG_FIX={name}")
                return
        raise RuntimeError("No catalog strategy returned the expected label set")


if __name__ == "__main__":
    main()
