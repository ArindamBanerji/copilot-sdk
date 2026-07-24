"""Interactively remove one domain's Decision topology from AGE."""
from __future__ import annotations
import argparse
import psycopg2
from phase_config import add_domain_argument, get_config

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); parser.add_argument("--yes", action="store_true", help="confirm deletion"); args=parser.parse_args(); cfg=get_config(args.domain)
    if not cfg["age_dsn"]: parser.error("set GRAPH_DSN or AGE_DSN")
    if not args.yes and input(f"Delete all AGE topology for {cfg['domain']}? Type YES: ").strip() != "YES": raise SystemExit("Aborted.")
    conn=psycopg2.connect(cfg["age_dsn"]); conn.autocommit=True; cur=conn.cursor(); cur.execute("LOAD 'age'"); cur.execute('SET search_path = ag_catalog, "$user", public')
    for label in ("Outcome", "CentroidCheckpoint", "EvidenceReceipt", "Decision"):
        cur.execute(f"SELECT * FROM cypher('{cfg['graph_name']}', $$ MATCH (n:{label} {{domain:'{cfg['domain']}'}}) DETACH DELETE n RETURN count(*) $$) AS (c agtype)")
        print(f"{label}: {cur.fetchone()[0]} deleted")
    conn.close()
if __name__ == "__main__": main()
