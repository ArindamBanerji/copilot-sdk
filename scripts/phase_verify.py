"""Verify SQLite source counts against AGE topology for one domain."""
from __future__ import annotations
import argparse, sqlite3
import psycopg2
from phase_config import add_domain_argument, get_config

def _count(cursor, graph: str, cypher: str) -> int:
    cursor.execute(f"SELECT * FROM cypher('{graph}', $$ {cypher} $$) AS (c agtype)")
    return int(str(cursor.fetchone()[0]).strip('"'))

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); args = parser.parse_args(); cfg = get_config(args.domain)
    if not cfg["age_dsn"]: parser.error("set GRAPH_DSN or AGE_DSN")
    with sqlite3.connect(cfg["db_path"]) as source:
        active = source.execute("SELECT count(*) FROM decisions").fetchone()[0]
        outcomes = source.execute("SELECT count(*) FROM outcomes").fetchone()[0]
        archived = source.execute("SELECT count(*) FROM decisions_archive").fetchone()[0] if source.execute("SELECT 1 FROM sqlite_master WHERE name='decisions_archive'").fetchone() else 0
    conn = psycopg2.connect(cfg["age_dsn"]); conn.autocommit=True; cur=conn.cursor(); cur.execute("LOAD 'age'"); cur.execute('SET search_path = ag_catalog, "$user", public')
    domain = cfg["domain"]
    checks = {
        "active Decisions": (_count(cur,cfg["graph_name"],f"MATCH (d:Decision {{domain:'{domain}'}}) WHERE (d.archived IS NULL OR d.archived <> true) RETURN count(d)"), active),
        "Outcomes": (_count(cur,cfg["graph_name"],f"MATCH (o:Outcome {{domain:'{domain}'}}) RETURN count(o)"), outcomes),
        "archived Decisions": (_count(cur,cfg["graph_name"],f"MATCH (d:Decision {{domain:'{domain}'}}) WHERE d.archived = true RETURN count(d)"), archived),
    }
    conn.close(); passed=True
    for name,(actual,expected) in checks.items():
        ok=actual==expected; passed &= ok; print(f"{name}: {actual} expected {expected} {'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if passed else 1)
if __name__ == "__main__": main()
