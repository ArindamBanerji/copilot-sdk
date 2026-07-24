"""Run resumable, domain-aware score/learn dual-write validation cycles."""
from __future__ import annotations
import argparse, json, os, time
import httpx, psycopg2
from phase_config import add_domain_argument, get_config, scoring_shape

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__); add_domain_argument(parser); parser.add_argument("--cycles",type=int,default=int(os.environ.get("PHASE_TARGET_CYCLES","40"))); args=parser.parse_args(); cfg=get_config(args.domain)
    if not cfg['age_dsn']: parser.error('set GRAPH_DSN or AGE_DSN')
    categories,factors=scoring_shape(cfg['domain']); checkpoint=cfg['checkpoint_path']; state=json.load(open(checkpoint)) if os.path.exists(checkpoint) else {"completed":0,"history":[]}
    conn=psycopg2.connect(cfg['age_dsn']); conn.autocommit=True; cur=conn.cursor(); cur.execute("LOAD 'age'"); cur.execute('SET search_path = ag_catalog, "$user", public')
    try:
        while state['completed'] < args.cycles:
            scored=[]
            for offset in range(3):
                response=httpx.post(f"{cfg['api_base']}/api/score",json={"category":categories[(state['completed']*3+offset)%len(categories)],"factors":factors},timeout=10); response.raise_for_status(); data=response.json()
                if not data['decision_id'].startswith(cfg['prefix']): raise RuntimeError(f"unexpected ID prefix: {data['decision_id']}")
                scored.append((data['decision_id'],data['action']))
            for index,(decision_id,action) in enumerate(scored[:2]):
                response=httpx.post(f"{cfg['api_base']}/api/learn",json={"decision_id":decision_id,"actual_action":action,"outcome":"confirmed" if index==0 else "overridden"},timeout=10); response.raise_for_status()
            time.sleep(.25)
            for decision_id,_ in scored:
                cur.execute(f"SELECT * FROM cypher('{cfg['graph_name']}', $$ MATCH (d:Decision {{domain:'{cfg['domain']}', decision_id:'{decision_id}'}}) RETURN count(d) $$) AS (c agtype)")
                if int(str(cur.fetchone()[0]).strip('"')) != 1: raise RuntimeError(f"missing AGE decision {decision_id}")
            state['completed'] += 1; state['history'].append({"cycle":state['completed'],"ids":[value[0] for value in scored],"timestamp":time.time()})
            temporary=checkpoint+'.tmp'; json.dump(state,open(temporary,'w'),indent=2); os.replace(temporary,checkpoint); print(f"cycle {state['completed']}/{args.cycles}: PASS")
    finally: conn.close()
if __name__ == '__main__': main()
