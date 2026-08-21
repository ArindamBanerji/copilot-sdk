# H-ENRICH results v1

## Design fixes applied

- **DF-E0 — exact d0 trace:** the first exploratory run recorded the post-update distance as d0.
  The runner was corrected to persist `||mu0-GT||` before decision 1, followed by post-update
  distances. This is required by I-E3 and leaves the learning rule unchanged.
- **DF-E1 / V1 — neutral exact-tie handling:** exact 0.5 μ₀ makes all actions tied initially;
  raw `argmin` selected action 0 and contaminated the day-1 floor. The trusted run uses a shared
  independent tie-break stream only on exact ties. It is identical across arms and is independent
  of GT, labels, sigma, and learning state. This preserves I-E1..I-E6 and removes the action-0
  artifact. The exploratory action-0 floor was 0.367 unenriched versus 0.300 enriched; the trusted
  neutral-tie run is reported below.

## Metrics per seed

The operating point is `epsilon_firm=0.20`, with 720 round-robin decisions per arm and seed.
`k` uses the H-CURVE ten-decision block means and median pairwise log-slopes. A rate fit is valid
only for positive k with at least five retained blocks.

| Seed | Arm | Day-1 floor | N to rolling accuracy ≥ .70 | d0 | k estimate | Positive-decay fit |
|---:|---|---:|---:|---:|---:|---|
| 42 | Unenriched | 0.500 | 44 | 0.200 | -0.0281 | No |
| 42 | Enriched | 0.300 | 46 | 0.200 | -0.0294 | No |
| 123 | Unenriched | 0.300 | 16 | 0.200 | -0.0303 | No |
| 123 | Enriched | 0.200 | 55 | 0.200 | -0.0184 | No |
| 777 | Unenriched | 0.300 | 56 | 0.200 | -0.0381 | No |
| 777 | Enriched | 0.400 | 13 | 0.200 | -0.0298 | No |

Means: day-1 floor is **0.367 unenriched versus 0.300 enriched**; N-to-competence is **38.7
unenriched versus 38.0 enriched**. The d0 values are equal to floating-point precision. Lower
sigma changes the oracle-label distribution as permitted by the design: paired enriched-versus-
unenriched oracle labels differ on 123, 99, and 109 of the 720 decisions for seeds 42, 123, and
777 respectively. This is the intended cleaner/noisier label distribution, not a labeling-rule
change.

## Rate result

All six trajectories have negative k estimates and therefore fail the positive-decay validity gate.
The mean estimates are -0.0322 unenriched and -0.0259 enriched, but these are not valid fitted
convergence rates: the distance trajectories rise to a noise/label-mismatch floor above d0. A
`k_enriched/k_unenriched` rate-invariance claim is consequently **NOT ESTIMABLE**, not accepted
from the raw negative estimates. The ±20% equality tolerance is shown in the verification chart
only as a reference around the unenriched estimate; it cannot convert invalid fits into a rate
result.

## Invariant assertions

| Invariant | Result | Evidence |
|---|---|---|
| I-E1 GT identical | PASS | One per-seed GT snapshot is shared by both arms |
| I-E2 nearest-GT oracle rule | PASS | Same oracle construction/rule; vector is the only label input |
| I-E3 μ0 and d0 identical | PASS | Exact 0.5 prior; d0=0.200 for both arms per seed |
| I-E4 learning rule identical | PASS | Both arms use `mu[c,label] += .05*(f-mu[c,label])` |
| I-E5 only sigma differs | PASS | `.08` all factors vs `.04` on factors [0,1] only |
| I-E6 enrichment firewall | PASS | GT, oracle, μ0, eta, coverage, and update are unchanged |

## F-verdicts and split verdict

- **F-FLOOR: FIRED.** Enrichment did not lift the day-1 accuracy floor; it was lower by 6.7
  percentage points on the trusted three-seed mean.
- **F-RATE: NOT ESTIMABLE / apparatus convergence failure.** Both arms failed the positive-decay
  fit-validity gate, so the experiment cannot establish pure leveling or a change in k. The
  negative estimates indicate distance expansion rather than a valid first-curve decay.
- **Secondary N:** enriched is marginally lower on the three-seed mean (38.0 vs 38.7), but this
  secondary result does not rescue the failed primary floor and is not promoted.

**Split verdict: INVALIDATED for the preregistered H-ENRICH claim at this operating point.** The
floor did not lift, and rate invariance was not estimable because neither arm produced a valid
positive distance decay. The result is a roadmap signal: before claiming enrichment as a clean
second engine, the production/theorem apparatus needs a class-separation regime in which the first
curve actually converges under the fixed oracle and learning rule. No scorer was imported or
modified.

## Artifacts and verification chart

Raw artifacts and scorer-free summary:

`graph-attention-engine-v50/experiments/h_enrich_v1/raw/`

Manifest:

`graph-attention-engine-v50/experiments/h_enrich_v1/raw/manifest.json`

Verification chart:

- `graph-attention-engine-v50/experiments/h_enrich_v1/figures/henrich_floor_rate.png`
- `graph-attention-engine-v50/experiments/h_enrich_v1/figures/henrich_floor_rate.pdf`
- `graph-attention-engine-v50/experiments/h_enrich_v1/figures/henrich_floor_rate.caption.txt`

The manifest contains 35 hashed artifacts and was verified after chart registration. It includes
per-seed GT and μ0, shared standard-normal and tie-break streams, per-arm vectors with per-factor
sigma, oracle labels, predictions, correctness, trajectories, final μ, metrics, invariant records,
and chart outputs. All results are recomputable without importing a scorer.
