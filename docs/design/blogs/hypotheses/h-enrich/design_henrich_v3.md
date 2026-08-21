# H-ENRICH design v3

## Ratified manipulation

For each shared `(seed, epsilon)` GT, compute
`sep[f] = mean_{c,a1<a2}|GT[c,a1,f]-GT[c,a2,f]|` over all category/action pairs. Rank by
descending separation with lowest-index tie break and enrich exactly the top two factors. Both arms
use that same selected pair: UNENRICHED has sigma=.08 on all factors; ENRICHED has sigma=.04 on
the selected pair and .08 elsewhere. The pair is selected from GT before vectors are drawn and is
persisted. This is targeted external observability, not a scorer-dependent choice; GT is never
derived from μ.

## Settings and apparatus

Operating points are ε_firm=.35 and .50, single-phase cold-start convergence, seeds 42/123/777,
and 1200 round-robin decisions per cell schedule. Each arm receives the same standard-normal and
exact-tie streams, GT, μ0=.5, nearest-GT vector-only oracle labeling rule, and update
`mu <- mu + .05*(f-mu)`. The vector is `clip(GT[c,a]+sigma_f*z,0,1)`. The aggregate floor is
the mean accuracy over the first 10 observations of each of all 24 cells; it is never narrowed to
enriched factors. Rate is H-CURVE's positive-k block fit with the ±20% tolerance. N is decisions
to rolling accuracy .70. Baseline positive-k validity is checked first at each epsilon.

## Invariants I-E1..I-E6

GT, the nearest-GT oracle rule, μ0/d0, eta, coverage, and update rule are identical between arms.
Only sigma differs on the identical top-two factor set. Labels may differ because noise reduction
changes the label distribution; equality of labels is not an invariant.

## Reading gate

This is an n=3 screen. A positive floor difference in every seed recommends a 20-seed magnitude
extension. Sign-inconsistent differences, or a sign-consistent negative difference, are NULL for
this apparatus. The real-production +5pp observation remains a Tier-2 claim if the screen is null.
Rate is a separate primary: k must remain within ±20%; a floor lift accompanied by a k change is
not pure leveling.

## Variants tried and fixes

- V0 used arbitrary factors [0,1]; superseded by this decision-relevant top-2 ranking.
- V1 used the same neutral exact-tie stream and per-cell first-10 floor as the v2 apparatus.
- V3 is the trusted targeted screen; it persists separation vectors, ranking, tie gap, and the
  shared enriched set for every seed/epsilon.
- The v2 exact pre-learning d0 trace and neutral-tie correction are retained unchanged.
