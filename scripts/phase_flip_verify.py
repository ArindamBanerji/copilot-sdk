"""Verify score → learn → AGE Outcome topology after a domain AGE flip."""
from __future__ import annotations
import argparse, time
import httpx, psycopg2
from phase_config import add_domain_argument, get_config, scoring_shape

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); args=parser.parse_args(); cfg=get_config(args.domain)
    if not cfg['age_dsn']: parser.error('set GRAPH_DSN or AGE_DSN')
    categories,factors=scoring_shape(cfg['domain'])
    score=httpx.post(f"{cfg['api_base']}/api/score",json={"category":categories[0],"factors":factors},timeout=10); score.raise_for_status(); payload=score.json(); decision_id,action=payload['decision_id'],payload['action']
    learn=httpx.post(f"{cfg['api_base']}/api/learn",json={"decision_id":decision_id,"actual_action":action,"outcome":"confirmed"},timeout=10); learn.raise_for_status(); time.sleep(.25)
    conn=psycopg2.connect(cfg['age_dsn']); conn.autocommit=True; cur=conn.cursor(); cur.execute("LOAD 'age'"); cur.execute('SET search_path = ag_catalog, "$user", public')
    cur.execute(f"SELECT * FROM cypher('{cfg['graph_name']}', $$ MATCH (d:Decision {{domain:'{cfg['domain']}', decision_id:'{decision_id}'}})-[:HAS_OUTCOME]->(o:Outcome) RETURN d.status, o.actual_action $$) AS (status agtype, action agtype)")
    row=cur.fetchone(); conn.close(); passed=bool(row) and str(row[0]).strip('"') == 'confirmed' and decision_id.startswith(cfg['prefix'])
    print(f"domain={cfg['domain']} id={decision_id} topology={'PASS' if passed else 'FAIL'}"); raise SystemExit(0 if passed else 1)
if __name__ == '__main__': main()
