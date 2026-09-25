import random
import pytest
from experiments.vld import k14_compounding_noise as k


@pytest.fixture(scope='module')
def payload():
 return k.build_payload()

def test_noise_injection():
 assert sum(k.flip(True,'noisy',.0,random.Random(i)) for i in range(20))==0
 assert sum(not k.flip(False,'noisy',1.0,random.Random(i)) for i in range(20))==20


def test_clean_matches_ke1(payload):
 # The clean arm is the unmodified KE-1 generator/update protocol.
 assert all(abs(d['training_label_flip_rate']) == 0.0 for p in payload['per_copilot'].values() for d in p['clean_runs'])


def test_random_near_zero(payload):
 # With 50 evaluation scenarios per checkpoint, finite samples can move a
 # routing estimate.  A random-label arm must not produce a material (>3pp)
 # advantage over the corresponding clean-label arm.
 assert all(
  payload['per_copilot'][c]['random_gain']['mean']
  <= payload['per_copilot'][c]['clean_gain']['mean'] + .03
  for c in k.COPILOTS
 )


def test_noisy_between(payload):
 for p in payload['per_copilot'].values():
  clean=p['clean_gain']['mean'];noisy=p['noisy_gain']['mean'];random_gain=p['random_gain']['mean']
  if p['noise_rate'] >= .5:
   # Better-than-chance labels should remain in the clean/random band.
   assert min(clean,random_gain)-.03 <= noisy <= max(clean,random_gain)+.03
  else:
   # The measured DataOps/S2P/Trading labels are worse than chance after
   # inversion, so they may be more damaging than a random-label control.
   assert noisy <= clean + .03


def test_deterministic():
 assert k.canonical(k.build_payload())==k.canonical(k.build_payload())


def test_all_copilots(payload):
 assert set(payload['per_copilot'])==set(k.COPILOTS)
