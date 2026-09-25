import json,numpy as np,random
from copilot_sdk.scoring.investigation import VLDInvestigator

data=json.load(open('real_centroids_v1.json'))['copilots']['purchasing']; factors=data['factor_names']; actions=data['action_names']
rng=random.Random(21)
for cat in data['all_category_mu']:
 inv=VLDInvestigator(np.array(data['all_category_mu'][cat],float),np.ones(7),factors,tau=0.1)
 print('cat',cat)
 for _ in range(200000):
  v=np.array([rng.random() for _ in range(7)])
  a0,P0=inv.score(v)
  if actions[a0] != 'order_more' or inv.margin(P0) < 0.03: continue
  Q0=inv.compute_Q(v,P0)
  if int(np.argmax(Q0)) != 5: continue
  for lead,conf in [(0.0,.2),(0.1,.3),(0.2,.5),(0.2,.9),(0.8,.9),(1.0,.9)]:
   v1=v.copy(); v1[5]=conf*lead+(1-conf)*v1[5]
   a1,P1=inv.score(v1); Q1=inv.compute_Q(v1,P1,{5})
   if int(np.argmax(Q1)) != 6: continue
   for price in [0.81,0.85,0.9,0.95,1.0]:
    v2=v1.copy(); v2[6]=price
    a2,P2=inv.score(v2)
    if actions[a2]=='order_less' and inv.margin(P2)>0.05:
     print('FOUND',cat,'v',np.round(v,4).tolist(),'lead',lead,'conf',conf,'price',price,'m',round(inv.margin(P0),3),'final',round(inv.margin(P2),3),'q0',np.argsort(-Q0)[:3].tolist(),'q1',np.argsort(-Q1)[:3].tolist(), 'a1', actions[a1])
     raise SystemExit
 print('none')
