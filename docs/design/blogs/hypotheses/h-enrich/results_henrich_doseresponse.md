# H-ENRICH dose-response results

## Design fixes applied

- **DF-DR1 — numerical tie handling:** at κ=0 the engineered separations are mathematically
  uniform; ranking uses 12-decimal separation quantization and lowest-factor tie break, preserving
  f*=0 without allowing floating-point noise to choose the factor.
- **DF-DR2 — shared targeted arm construction:** f* is computed once from shared GT per seed/κ and
  the same sigma vector assignment is used to compare both arms. No arm-specific factor selection
  or GT-dependent scorer state is used.

## Separation construction

| κ | Seed 42 f* | Seed 123 f* | Seed 777 f* |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| .5 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 |

At κ=0, all six measured separations are equal within the registered numerical tie rule. At
κ>0, factor 0 is strictly the most separated factor. The full separation vectors, rankings, and
boundary gaps are persisted for every seed/κ.

## Lift-vs-κ paired screen

Floor is aggregate accuracy over the first 10 decisions of each of all 24 cells. Values below are
`unenriched floor → enriched floor`, followed by the paired lift for seeds 42/123/777.

| κ | Floor U → E by seed 42 / 123 / 777 | Lift E−U by seed 42 / 123 / 777 | Sign-consistent positive? | Mean lift |
|---:|---|---|---|---:|
| 0 | .583→.608 / .579→.592 / .512→.542 | +2.50pp / +1.25pp / +2.92pp | Yes | +2.22pp |
| .5 | .562→.554 / .579→.562 / .617→.592 | −.83pp / −1.67pp / −2.50pp | No | −1.67pp |
| 1 | .550→.546 / .588→.558 / .592→.500 | −.42pp / −2.92pp / −9.17pp | No | −4.17pp |
| 2 | .567→.446 / .579→.517 / .521→.546 | −12.08pp / −6.25pp / +2.50pp | No | −5.28pp |
| 4 | .562→.538 / .512→.538 / .596→.542 | −2.50pp / +2.50pp / −5.42pp | No | −1.81pp |

## Rate and competence check

| κ | Seed | k U | k E | E/U ratio | Rate within ±20%? | N U → E |
|---:|---:|---:|---:|---:|---|---:|
| 0 | 42 | .00657 | .00636 | .969 | Yes | 36 → 36 |
| 0 | 123 | .00470 | .00492 | 1.047 | Yes | 36 → 56 |
| 0 | 777 | .00641 | .00549 | .858 | Yes | 89 → 85 |
| .5 | 42 | .00656 | .00529 | .806 | Yes | 51 → 57 |
| .5 | 123 | .00615 | .00677 | 1.101 | Yes | 26 → 24 |
| .5 | 777 | .00436 | .00480 | 1.100 | Yes | 40 → 36 |
| 1 | 42 | .00499 | .00678 | 1.359 | No | 53 → 45 |
| 1 | 123 | .00888 | .00692 | .780 | No | 46 → 53 |
| 1 | 777 | .00541 | .00524 | .968 | Yes | 61 → 112 |
| 2 | 42 | .00571 | .00624 | 1.093 | Yes | 61 → 55 |
| 2 | 123 | .00433 | .00488 | 1.128 | Yes | 31 → 49 |
| 2 | 777 | .00737 | .00709 | .963 | Yes | 101 → 54 |
| 4 | 42 | .00795 | .00518 | .651 | No | 39 → 33 |
| 4 | 123 | .00482 | .00514 | 1.067 | Yes | 40 → 70 |
| 4 | 777 | .00410 | .00609 | 1.487 | No | 73 → 32 |

All 30 arm/seed/κ fits were valid positive decay fits. Rate behavior is not uniformly invariant:
κ=0 and .5 pass all three seed ratios, κ=1 has two failures, κ=2 passes all three, and κ=4 has
two failures.

## Screen verdict against the pre-registered prediction

**FALSIFIED: the concentration prediction does not hold.** The κ=0 control is positive and
sign-consistent in all three seeds (+2.50pp, +1.25pp, +2.92pp), directly falsifying the prediction
that uniform relevance should be near-zero and sign-inconsistent. The curve then becomes negative
at κ=.5 and κ=1, remains mixed at κ=2 and κ=4, and is therefore strongly non-monotone. There is
no κ* threshold at which positive sign-consistent lift emerges.

The secondary rate check is also mixed and fails at κ=1 and κ=4 for some seeds. This is not a
clean leveling response. The result says the targeted concentration parameter is not the predictor
of enrichment lift in this engineered apparatus; the κ=0 positive result indicates the v3 null had
another cause, as required to be reported rather than reconciled away.

## Firewall invariant results

| Invariant | Result | Evidence |
|---|---|---|
| I-E1 GT identical | PASS | One engineered GT per seed/κ shared by both arms |
| I-E2 nearest-GT vector-only oracle | PASS | Same label rule, with no sigma input |
| I-E3 μ0 and d0 identical | PASS | Exact .5 prior; `||GT−μ0||F=.35` per cell |
| I-E4 learning rule identical | PASS | Both arms use η=.05 on the oracle-labeled cell |
| I-E5 only sigma differs | PASS | Same f*; .04 only enriched f*, .08 otherwise |
| I-E6 enrichment firewall | PASS | GT, f* choice, label rule, μ0, eta, and coverage unchanged |

Labels were not asserted equal; their distribution can differ under the intended sigma change.

## Artifacts and chart

Raw artifacts and scorer-free summary:
`graph-attention-engine-v50/experiments/h_enrich_dose_response/raw/`

Manifest:
`graph-attention-engine-v50/experiments/h_enrich_dose_response/raw/manifest.json`

Verification chart:

- `graph-attention-engine-v50/experiments/h_enrich_dose_response/figures/henrich_dose_response.png`
- `graph-attention-engine-v50/experiments/h_enrich_dose_response/figures/henrich_dose_response.pdf`
- `graph-attention-engine-v50/experiments/h_enrich_dose_response/figures/henrich_dose_response.caption.txt`

The manifest contains 170 hashed artifacts and passed byte-size and SHA-256 verification. It
contains per-seed/κ GT, separation vectors, f*, sigma assignments, shared random streams, vectors,
labels, accuracy, distance trajectories, final μ, floor/k/N metrics, invariant records, and chart
outputs. All reported values are scorer-free recomputable.
