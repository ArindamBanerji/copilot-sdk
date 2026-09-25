import sys,json,numpy as np,random
sys.path.insert(0,'apps/trading/backend')
from copilot_sdk.scoring.investigation import VLDInvestigator
from app.vld_preseed import SHOWCASE_TRADES, seed_vld_trading_showcase
from app.evidence_provider import TradingEvidenceProvider

data=json.load(open('real_centroids_v1.json'))['copilots']['trading']
factors=data['factor_names']; actions=data['action_names']
seed_vld_trading_showcase({})
trades={t['trade_id']:t for t in SHOWCASE_TRADES}
for tid in ['VLD-TRD-1','VLD-TRD-2','VLD-TRD-S1']:
 trade=trades[tid]
 mu=np.array(data['all_category_mu'][trade['category']],float); inv=VLDInvestigator(mu,np.ones(len(factors)),factors,tau=0.1)
 v=np.array(trade['surface_factors'],float)
 class P:
  def __init__(s): s.reads=[]
  def read_evidence(s,d,dim,name): s.reads.append(dim); return TradingEvidenceProvider({},tid).read_evidence(d,dim,name)
 p=P(); tr=inv.investigate(tid,trade['category'],v,p,budget=2,gated_sources={'correlation_engine','portfolio_engine'})
 a0,P0=inv.score(v); print('\nCUR',tid,trade['category'],actions[a0],round(inv.margin(P0),4),'->',actions[tr.final_action],round(tr.final_margin,4),'attempts',p.reads)

GATED={'correlation_engine','portfolio_engine'}
class EP:
 def __init__(s,ev): s.ev=ev; s.reads=[]
 def read_evidence(s,d,dim,name): s.reads.append(dim); return s.ev.get(dim)

def try_search(label, required, evidence, src_action='strong_execution', dst_action='partial_execution', maxn=200000):
 print('\nSEARCH',label,required)
 rng=random.Random(42+sum(required)+len(label))
 for cat in data['all_category_mu']:
  inv=VLDInvestigator(np.array(data['all_category_mu'][cat],float),np.ones(len(factors)),factors,tau=0.1)
  mu=np.array(data['all_category_mu'][cat],float)
  for mode in ['mix01','mix02','random']:
   for n in range(maxn):
    if mode=='mix01':
     alpha=rng.uniform(.45,.92); v=alpha*mu[0]+(1-alpha)*mu[1]+np.array([rng.uniform(-.2,.2) for _ in factors]); v=np.clip(v,0,1)
    elif mode=='mix02':
     alpha=rng.uniform(.45,.92); v=alpha*mu[0]+(1-alpha)*mu[2]+np.array([rng.uniform(-.2,.2) for _ in factors]); v=np.clip(v,0,1)
    else:
     v=np.array([rng.random() for _ in factors])
    a0,P0=inv.score(v)
    if actions[a0]!=src_action or inv.margin(P0)<0.05: continue
    p=EP(evidence); tr=inv.investigate('x',cat,v,p,budget=2,gated_sources=GATED)
    dims=p.reads
    if actions[tr.final_action]==dst_action and tr.final_margin>0.05 and set(required)<=set(dims):
     print('FOUND',cat,'v',np.round(v,4).tolist(),'surf',round(inv.margin(P0),4),'final',round(tr.final_margin,4),'dims',dims)
     for st in tr.steps: print(' step',st.dimension,factors[st.dimension], actions[st.action_before],'->',actions[st.action_after],st.evidence_value,st.evidence_confidence,st.evidence_source)
     return cat,v,dims,tr
 print('NONE')
try_search('TRD1 accept real dims 3,5',[3,5], {3:{'value':0.25,'confidence':0.85,'source':'momentum_tracker'}})
try_search('TRD1 corr route 2,1',[2,1], {1:{'value':0.88,'confidence':0.9,'source':'correlation_engine'},3:{'value':0.25,'confidence':0.85,'source':'momentum_tracker'}})
try_search('TRD2 real dims 3,5 no ev',[3,5], {2:{'value':0.85,'confidence':0.92,'source':'portfolio_engine'},1:{'value':0.78,'confidence':0.88,'source':'correlation_engine'}})
try_search('TRD2 portfolio route 2,3',[2,3], {2:{'value':0.85,'confidence':0.92,'source':'portfolio_engine'},3:{'value':0.25,'confidence':0.85,'source':'momentum_tracker'}})
try_search('TRD2 portfolio corr 2,1',[2,1], {2:{'value':0.85,'confidence':0.92,'source':'portfolio_engine'},1:{'value':0.78,'confidence':0.88,'source':'correlation_engine'}})
