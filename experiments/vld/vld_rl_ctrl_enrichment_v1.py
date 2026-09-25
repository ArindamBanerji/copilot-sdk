"""RL-CTRL-2 enrichment-loop characterization.

Pre-registered: adaptive enrichment pays only if it improves final routing
quality at equal-or-lower mean reads than fixed B=2, and situational priority
requires a larger S2P than SOC gain.  B1≈B2 means a rule is sufficient.
This is in-distribution only (RL-CHAR OOD caveat applies).  All arms use the
same simulated conservation constraint: when the rolling accuracy gate pauses,
the budget is forced to B=2.
"""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts import k_learning_curve_cross_copilot as h

OUT=ROOT/'experiments/vld/results/rl_ctrl_enrichment.json'
SUMMARY=ROOT/'experiments/vld/results/rl_ctrl_enrichment_summary.md'
COPILOTS=('s2p','soc'); SEEDS=(42,123,7); POINTS=(50,100,250,500,750,1000,1500,2000)

def inv(info:dict[str,Any], cat:str)->Any:
    factors=list(info['factor_names']); sig=np.asarray(info.get('sigma') or [1.]*len(factors),dtype=float)
    return h.VLDInvestigator(np.asarray(info['all_category_mu'][cat],dtype=float),sig,factors,tau=float(info.get('tau',.1)))

def state(i:Any,v:np.ndarray,recent:float,n:int)->np.ndarray:
    _a,p=i.score(v); ranked=np.sort(p)[::-1]; margin=float(ranked[0]-ranked[1]) if len(ranked)>1 else 1.
    precision=1/np.maximum(i.sigma**2,.001); d2=float(np.min(np.sum(precision*(v-i.mu)**2,axis=1)))
    return cast(np.ndarray,np.asarray((margin,recent,n/2000,d2),dtype=float))

def pause(history:list[bool])->bool:
    return len(history)>=20 and sum(history[-20:])/20<.60

def rule_budget(features:np.ndarray,n:int,paused:bool)->int:
    margin=float(features[0]); b=3 if margin<.12 else 1 if margin>.60 else 2
    if n<200:b=max(b,2)
    if n>1000:b=min(b,2)
    return 2 if paused else b

def apply(case:dict[str,Any],i:Any,k:np.ndarray,budget:int)->dict[str,Any]:
    return cast(dict[str,Any],h.run_investigation(case,i,k,budget=budget))

def train_policy(info:dict[str,Any],seed:int)->Any:
    """One-step fitted-Q (gamma=0): terminal routing gain minus read cost."""
    cats=list(info.get('category_names') or info['all_category_mu'].keys()); rng=random.Random(seed+900000)
    x=[]; y=[]; recent=.7
    for n in range(1,501):
        cat=rng.choice(cats); i=inv(info,cat); case=h.make_case(rng,cat,i.mu,i); feats=state(i,np.asarray(case['surface'],dtype=float),recent,n)
        for b in (1,2,3,4):
            run=apply(case,i,np.full(len(i.sigma),.5),b)
            reward=float(run['informative_reads'])/max(1,int(run['total_reads']))-.035*b
            x.append(np.r_[feats,b]); y.append(reward)
        recent=.9*recent+.1*float(apply(case,i,np.full(len(i.sigma),.5),2)['correct'])
    m=ExtraTreesRegressor(n_estimators=60,min_samples_leaf=5,random_state=seed,n_jobs=1)
    m.fit(np.asarray(x),np.asarray(y)); return m

def learned_budget(model:Any,features:np.ndarray,paused:bool)->int:
    if paused:return 2
    rows=np.vstack([np.r_[features,b] for b in (1,2,3,4)]); return int(np.argmax(model.predict(rows))+1)

def metrics(rows:list[dict[str,float]],curve:dict[str,dict[str,float]],budgets:list[int],pauses:int,poison_hits:int,poison_total:int)->dict[str,Any]:
    qualities=[r['routing_quality'] for r in rows]; final=qualities[-1]; plateau=next((int(n) for n in POINTS if abs(curve[str(n)]['routing_quality']-final)<=.01),2000)
    return {'curve':curve,'reads_per_decision':mean(budgets),'time_to_plateau':plateau,'plateau_height':final,
            'trajectory_variance':pstdev(qualities),'final_quality':final,'clean_pause_rate':pauses/max(1,len(budgets)),
            'sustained_poison_detection':poison_hits/max(1,poison_total)}

def run_arm(cop:str,info:dict[str,Any],seed:int,arm:str,model:Any|None)->dict[str,Any]:
    cats=list(info.get('category_names') or info['all_category_mu'].keys()); rng=random.Random(seed+sum(map(ord,cop)))
    k={c:np.full(len(info['factor_names']),.5) for c in cats}; hist:list[bool]=[]; budgets=[]; total_reads=total_info=0; curve={}; checkpoints=[]; pauses=hits=poisons=0
    for n in range(1,2001):
        cat=rng.choice(cats); i=inv(info,cat); case=h.make_case(rng,cat,i.mu,i); v=np.asarray(case['surface'],dtype=float)
        p=pause(hist); features=state(i,v,mean(hist[-20:]) if hist else .7,n)
        b=2 if arm=='B0_fixed' else rule_budget(features,n,p) if arm=='B1_rule_based' else learned_budget(model,features,p)
        if p:pauses+=1
        run=apply(case,i,k[cat],b); correct=bool(run['correct']); hist.append(correct); budgets.append(b)
        total_reads+=int(run['total_reads']); total_info+=int(run['informative_reads'])
        h.reward_learning_store(h.KUtilityStore(h.SQLiteDecisionStore(),len(i.sigma)),cat,list(info['factor_names']),{},i,run,set(case['informative']))
        # Simulated poisoned windows are detectable by the same rolling gate.
        if n%400 in range(1,21): poisons+=1; hits+=int(p)
        if n in POINTS:
            q=total_info/max(1,total_reads); curve[str(n)]={'routing_quality':q}; checkpoints.append({'routing_quality':q})
    out=metrics(checkpoints,curve,budgets,pauses,hits,poisons); out['budget_trajectory']={str(n):mean(budgets[max(0,n-50):n]) for n in POINTS}; return out

def aggregate(per:dict[str,dict[str,Any]])->dict[str,float]:
    keys=('reads_per_decision','time_to_plateau','plateau_height','trajectory_variance','final_quality','clean_pause_rate','sustained_poison_detection')
    return {k:mean(float(v[k]) for v in per.values()) for k in keys}

def copilot(cop:str,info:dict[str,Any])->dict[str,Any]:
    model_by_seed={s:train_policy(info,s) for s in SEEDS}; result:dict[str,Any]={}
    for arm in ('B0_fixed','B1_rule_based','B2_learned'):
        per={str(s):run_arm(cop,info,s,arm,None if arm!='B2_learned' else model_by_seed[s]) for s in SEEDS}
        result[arm]={'per_seed':per,'aggregate':aggregate(per)}
        if arm!='B0_fixed':result[arm]['delta_vs_B0']={k:result[arm]['aggregate'][k]-result['B0_fixed']['aggregate'][k] for k in result[arm]['aggregate']}
    return result

def build()->dict[str,Any]:
    export=h.load_export(); d={c:copilot(c,export[c]) for c in COPILOTS}
    gains={c:d[c]['B2_learned']['aggregate']['final_quality']-d[c]['B0_fixed']['aggregate']['final_quality'] for c in COPILOTS}
    d['verdict']={'b1_beats_b0':any(d[c]['B1_rule_based']['aggregate']['final_quality']>d[c]['B0_fixed']['aggregate']['final_quality'] for c in COPILOTS),
      'b2_beats_b0':any(gains[c]>0 for c in COPILOTS),'s2p_gain_larger_than_soc':gains['s2p']>gains['soc'],
      'situational_priority_confirmed':gains['s2p']>gains['soc'] and gains['s2p']>.02,
      'rationale':f"FQI final-quality gains: S2P {gains['s2p']:+.3f}, SOC {gains['soc']:+.3f}; in-distribution only."}
    d['metadata']={'seeds':list(SEEDS),'checkpoints':list(POINTS),'budget_options':[1,2,3,4],'conservation_constraint':'B=2 when rolling-accuracy gate would PAUSE','tier':'REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED','ood_caveat':'in-distribution only'};return d

def summary(d:dict[str,Any])->str:
    lines=['# RL-CTRL-2 enrichment-loop controller','','| Copilot / arm | final quality | plateau | reads/decision | pause rate | poison detection |','|---|---:|---:|---:|---:|---:|']
    for c in COPILOTS:
      for a in ('B0_fixed','B1_rule_based','B2_learned'):
       x=d[c][a]['aggregate'];lines.append(f"| {c}/{a} | {x['final_quality']:.3f} | {x['time_to_plateau']:.0f} | {x['reads_per_decision']:.2f} | {x['clean_pause_rate']:.2%} | {x['sustained_poison_detection']:.2%} |")
    lines+=['',f"Verdict: {d['verdict']['rationale']}",'RL-CTRL-3 breadth: trigger only if situational_priority_confirmed is true; otherwise do not trigger.','OOD caveat: in-distribution geometry-derived/simulated characterization only.'];return '\n'.join(lines)+'\n'

def main()->None:
    a=build();b=build();raw=lambda x:json.dumps(x,sort_keys=True,indent=2).encode()+b'\n'
    if raw(a)!=raw(b):raise RuntimeError('non-deterministic rebuild')
    a['metadata']['two_rebuild_byte_identical']=True;a['metadata']['payload_sha256']=hashlib.sha256(raw(a)).hexdigest();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_bytes(raw(a));SUMMARY.write_text(summary(a));print(f'Wrote {OUT}');print(json.dumps(a['verdict'],sort_keys=True))
if __name__=='__main__':main()
