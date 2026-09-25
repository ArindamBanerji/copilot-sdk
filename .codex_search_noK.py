import json, numpy as np, random
from copilot_sdk.scoring.investigation import VLDInvestigator

data=json.load(open('real_centroids_v1.json'))['copilots']['purchasing']
factors=data['factor_names']; actions=data['action_names']
GATED={'vendor_tracker','lead_time_tracker'}
class P:
 def __init__(s,ev): s.ev=ev; s.reads=[]
 def read_evidence(s,d,dim,name): s.reads.append(dim); return {'value':s.ev[dim][0],'confidence':s.ev[dim][1],'source':s.ev[dim][2]} if dim in s.ev else None

def run(cat,v,ev):
 inv=VLDInvestigator(np.array(data['all_category_mu'][cat],float),np.ones(7),factors,tau=0.1)
 a0,P0=inv.score(v); pr=P(ev); tr=inv.investigate('x',cat,v,pr,budget=2,gated_sources=GATED)
 return inv,a0,P0,pr,tr
rng=random.Random(13)
print('DEMAND no K [5,6]')
for cat in data['all_category_mu']:
 mu=np.array(data['all_category_mu'][cat],float); found=False
 for _ in range(80000):
  # sample broadly, require custom compatibility later
  v=np.array([rng.random() for _ in range(7)])
  lead=rng.choice([0.05,0.1,0.15,0.2,0.25,0.3,0.8])
  price=rng.choice([0.81,0.85,0.9,0.95,1.0])
  ev={5:(lead,0.95,'lead_time_tracker'),6:(price,1.0,'vendor_catalog')}
  inv,a0,P0,pr,tr=run(cat,v,ev)
  if actions[a0]=='order_more' and actions[tr.final_action]=='order_less' and pr.reads[:2]==[5,6] and tr.final_margin>0.05:
   print(cat, np.round(v,4).tolist(), 'lead',lead,'price',price,'m',round(inv.margin(P0),3),'->',round(tr.final_margin,3))
   found=True; break
 if found: break
print('VENDOR no K [4,5]')
for cat in data['all_category_mu']:
 found=False
 for _ in range(80000):
  v=np.array([rng.random() for _ in range(7)])
  waste=rng.choice([0.72,0.78,0.82,0.88,0.92,1.0])
  lead=rng.choice([0.72,0.8,0.86,0.92,1.0])
  ev={4:(waste,0.95,'vendor_tracker'),5:(lead,0.95,'lead_time_tracker')}
  inv,a0,P0,pr,tr=run(cat,v,ev)
  if actions[a0]=='order_as_planned' and actions[tr.final_action]=='skip' and pr.reads[:2]==[4,5] and tr.final_margin>0.05:
   print(cat, np.round(v,4).tolist(), 'waste',waste,'lead',lead,'m',round(inv.margin(P0),3),'->',round(tr.final_margin,3))
   found=True; break
 if found: break
