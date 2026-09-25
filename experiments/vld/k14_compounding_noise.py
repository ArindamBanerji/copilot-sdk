"""K14 Part 2: KE-1-style compounding under measured training-label noise.

Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED.  Training labels
are clean, measured-K2-corrupted, or 50/50 random; every checkpoint evaluates
only against clean generated geometry labels.  Q2 is established when noisy and
clean gain differ by >3pp on at least 3/5 copilots.
"""
from __future__ import annotations
import argparse, hashlib, json, random, sys
from pathlib import Path
from statistics import mean
from typing import Any
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts import k_learning_curve_cross_copilot as h

COPILOTS=('soc','dataops','s2p','trading','purchasing');SEEDS=(42,123,7);N=500;EVAL=50
DEFAULT=ROOT/'experiments/vld/results/k14_compounding_noise.json'

def rates()->dict[str,float]:
 r=json.loads((ROOT/'experiments/vld/results/k14_validation_tier.json').read_text())['per_copilot']
 return {c:float(r[c]['k2_anchor_agreement']) for c in COPILOTS}

def info(export:dict[str,Any],cat:str)->Any:
 f=list(export['factor_names']);s=np.asarray(export.get('sigma') or [1.]*len(f),dtype=float)
 return h.VLDInvestigator(np.asarray(export['all_category_mu'][cat],dtype=float),s,f,tau=float(export.get('tau',.1)))

def evaluate(export:dict[str,Any],weights:dict[str,np.ndarray],seed:int,checkpoint:int)->float:
 cats=list(export.get('category_names') or export['all_category_mu'].keys());rng=random.Random(seed+100000+checkpoint);reads=good=0
 for _ in range(EVAL):
  c=rng.choice(cats);i=info(export,c);case=h.make_case(rng,c,i.mu,i);run=h.run_investigation(case,i,weights[c],budget=2)
  reads+=int(run['total_reads']);good+=int(run['informative_reads'])
 return good/max(1,reads)

def flip(clean:bool,regime:str,agreement:float,rng:random.Random)->bool:
 if regime=='clean':return clean
 if regime=='random':return bool(rng.randrange(2))
 return clean if rng.random()<agreement else not clean

def run_arm(copilot:str,export:dict[str,Any],seed:int,regime:str,agreement:float)->dict[str,Any]:
 cats=list(export.get('category_names') or export['all_category_mu'].keys())
 # All regimes see the identical decision stream.  Only this independent
 # generator changes the label presented to the K update.
 rng=random.Random(seed+sum(map(ord,copilot)))
 label_rng=random.Random(seed+sum(map(ord,copilot))+{'clean':0,'noisy':10_000,'random':20_000}[regime])
 weights={c:np.full(len(export['factor_names']),.5,dtype=float) for c in cats};frozen={c:x.copy() for c,x in weights.items()};curve={};frozen_curve={}
 flips=0
 for n in range(1,N+1):
  c=rng.choice(cats);i=info(export,c);case=h.make_case(rng,c,i.mu,i);run=h.run_investigation(case,i,weights[c],budget=2);clean=bool(run['correct']);label=flip(clean,regime,agreement,label_rng);flips+=int(label!=clean)
  for dim in run['selected']:
   weights[c][dim]=min(3.,weights[c][dim]+.02) if label and dim in case['informative'] else max(.1,weights[c][dim]-.005)
  if n%50==0:
   curve[str(n)]=evaluate(export,weights,seed,n);frozen_curve[str(n)]=evaluate(export,frozen,seed,n)
 return {'routing_curve':curve,'frozen_curve':frozen_curve,'gain':curve['500']-frozen_curve['500'],'final_routing_quality':curve['500'],'training_label_flip_rate':flips/N}

def build_payload()->dict[str,Any]:
 noise=rates();export=h.load_export();per={}
 for c in COPILOTS:
  arms={a:[run_arm(c,export[c],s,a,noise[c]) for s in SEEDS] for a in ('clean','noisy','random')}
  pack:dict[str,Any]={}
  for a,runs in arms.items():
   pack[f'{a}_gain']={'mean':mean(x['gain'] for x in runs),'seeds':[x['gain'] for x in runs]};pack[f'{a}_curve']=[x['routing_curve'] for x in runs];pack[f'{a}_runs']=runs
  # ``noise_rate`` is retained for the requested result shape; it is the
  # measured K2 agreement rate.  The explicit fields prevent confusing an
  # agreement of 0.86 with a 0.86 label-flip probability.
  pack['noise_rate']=noise[c];pack['k2_agreement_rate']=noise[c];pack['training_label_noise_rate']=1-noise[c];pack['q2_established']=abs(pack['noisy_gain']['mean']-pack['clean_gain']['mean'])>.03;per[c]=pack
 count=sum(bool(per[c]['q2_established']) for c in COPILOTS);diffs=[per[c]['clean_gain']['mean']-per[c]['noisy_gain']['mean'] for c in COPILOTS]
 weak=[c for c in COPILOTS if per[c]['noisy_gain']['mean']<=.03]
 retained=[c for c in COPILOTS if per[c]['noisy_gain']['mean']>.03]
 crossover=(f"At the measured points, noisy compounding is <=3pp for {', '.join(weak)} "
            f"and remains >3pp for {', '.join(retained)}. Heterogeneous production "
            "geometries prevent identifying one continuous cross-copilot collapse threshold.")
 return {'metadata':{'noise_rates':noise,'k2_agreement_rates':noise,'training_label_noise_rates':{c:1-noise[c] for c in COPILOTS},'seeds':list(SEEDS),'decisions_per_arm':N,'tier':'REAL_COMPONENT geometry + GEOMETRY-DERIVED + SIMULATED'},'per_copilot':per,'q2_verdict':f"Q2 {'ESTABLISHED' if count>=3 else 'NOT ESTABLISHED'}: noisy-clean gain differs >3pp for {count}/5 copilots; mean clean-minus-noisy={mean(diffs):+.3f}.",'crossover_analysis':crossover}

def canonical(d:dict[str,Any])->bytes:return json.dumps(d,sort_keys=True,indent=2).encode()+b'\n'
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=DEFAULT);a=p.parse_args();x=build_payload();y=build_payload();
 if canonical(x)!=canonical(y):raise RuntimeError('two rebuilds differ')
 x['metadata']['two_rebuild_byte_identical']=True;x['metadata']['payload_sha256']=hashlib.sha256(canonical(x)).hexdigest();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(canonical(x));print(f'Wrote {a.output}')
if __name__=='__main__':main()
