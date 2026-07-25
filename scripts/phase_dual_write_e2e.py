"""Score and learn decisions, then prove SQLite/AGE dual-write for one domain."""
from __future__ import annotations
import argparse, sqlite3, time
import httpx, psycopg2
from phase_config import add_domain_argument, get_config, scoring_shape
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); parser.add_argument("--count", type=int, default=5); args=parser.parse_args(); cfg=get_config(args.domain)
    if not cfg["age_dsn"]: parser.error("set GRAPH_DSN or AGE_DSN")
    categories, factors=scoring_shape(cfg["domain"])
    if not categories: raise SystemExit("Preset has no score categories")
    store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); baseline=store.count_decisions(cfg["domain"]); store.close()
    scored=[]
    for index in range(args.count):
        score_payload=cfg['score_payload_fn'](category=categories[index%len(categories)], factors=factors, cycle_num=index + 1)
        response=httpx.post(f"{cfg['api_base']}{cfg['score_path']}", json=score_payload, timeout=10)
        response.raise_for_status(); data=response.json(); scored.append((data["decision_id"], data["action"]))
    for index,(decision_id,action) in enumerate(scored[:2]):
        response=httpx.post(f"{cfg['api_base']}{cfg['learn_path']}",json={"decision_id":decision_id,"actual_action":action,"outcome":"confirmed" if index==0 else "overridden"},timeout=10)
        response.raise_for_status()
    time.sleep(.5)
    store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); delta=store.count_decisions(cfg["domain"])-baseline; store.close()
    conn=psycopg2.connect(cfg["age_dsn"]); conn.autocommit=True; cur=conn.cursor(); cur.execute("LOAD 'age'"); cur.execute('SET search_path = ag_catalog, "$user", public')
    found=0
    for decision_id,_ in scored:
        cur.execute(f"SELECT * FROM cypher('{cfg['graph_name']}', $$ MATCH (d:Decision {{domain:'{cfg['domain']}', decision_id:'{decision_id}'}}) RETURN count(d) $$) AS (c agtype)")
        found += int(str(cur.fetchone()[0]).strip('"')) > 0
    conn.close()
    outbox_clean=True
    if __import__('os').path.exists(cfg['outbox_path']):
        with sqlite3.connect(cfg['outbox_path']) as outbox:
            pending,failed=outbox.execute("SELECT count(*) FILTER (WHERE status='pending'), count(*) FILTER (WHERE status='failed') FROM secondary_outbox").fetchone()
            outbox_clean = pending == failed == 0
    passed=delta >= len(scored) and found == len(scored) and outbox_clean and all(decision_id.startswith(cfg['prefix']) for decision_id,_ in scored)
    print(f"domain={cfg['domain']} sqlite_delta={delta} age={found}/{len(scored)} outbox_clean={outbox_clean}")
    raise SystemExit(0 if passed else 1)
if __name__ == "__main__": main()
