# H-ENRICH results v3

## Design fixes applied

- **DF-E4 — decision-relevant targeting:** v3 computes mean pairwise GT separation per factor and
  selects the top two once per seed/epsilon. Both arms use the identical selected set; only sigma
  differs. This implements the ratified manipulation without touching GT, labels, μ0, or eta.
- **DF-E5 — persistence of targeting:** every seed/epsilon persists the full separation vector,
  deterministic ranking, top-two set, and top-two boundary gap. The vectors and invariant records
  retain per-factor sigma for every decision.

## Separation-ranked enriched factors

| ε | Seed 42 | Seed 123 | Seed 777 |
|---:|---|---|---|
| .35 | factors [0,2], sep [.04187,.03580,.03703,.02954,.03286,.03039] | factors [0,2], sep [.04016,.03284,.03566,.03454,.03193,.03048] | factors [0,1], sep [.04147,.03918,.02827,.03120,.03751,.03471] |
| .50 | factors [0,2], sep [.05982,.05115,.05290,.04220,.04695,.04341] | factors [0,2], sep [.05738,.04692,.05094,.04934,.04561,.04355] | factors [0,1], sep [.05924,.05598,.04039,.04457,.05358,.04958] |

The selected pair is shared by both arms for each cell. Ties are ordered by factor index; all
persisted top-two boundary gaps were positive.

## Per-seed metrics

The floor is aggregate accuracy over the first 10 decisions of each of the 24 cells. N is the
first global decision whose rolling ten-decision accuracy reaches .70.

| ε | Seed | Arm | Floor | Floor diff E−U | N | d0 | k | Fit |
|---:|---:|---|---:|---:|---:|---:|---:|---|
| .35 | 42 | Unenriched | .642 | — | 13 | .350 | .004253 | Yes |
| .35 | 42 | Enriched | .654 | +1.25pp | 32 | .350 | .006032 | Yes |
| .35 | 123 | Unenriched | .612 | — | 64 | .350 | .002181 | Yes |
| .35 | 123 | Enriched | .608 | −0.42pp | 61 | .350 | .003321 | Yes |
| .35 | 777 | Unenriched | .612 | — | 38 | .350 | .005743 | Yes |
| .35 | 777 | Enriched | .658 | +4.58pp | 56 | .350 | .006067 | Yes |
| .50 | 42 | Unenriched | .692 | — | 51 | .500 | .005563 | Yes |
| .50 | 42 | Enriched | .679 | −1.25pp | 52 | .500 | .004819 | Yes |
| .50 | 123 | Unenriched | .712 | — | 35 | .500 | .005304 | Yes |
| .50 | 123 | Enriched | .692 | −2.08pp | 32 | .500 | .005022 | Yes |
| .50 | 777 | Unenriched | .696 | — | 40 | .500 | .005464 | Yes |
| .50 | 777 | Enriched | .692 | −0.42pp | 32 | .500 | .004775 | Yes |

## Paired screen and aggregate result

| ε | Floor mean U → E | Mean floor diff | Sign pattern | k mean U → E | k ratio | N mean U → E |
|---:|---:|---:|---|---:|---:|---:|
| .35 | .622 → .640 | +1.81pp | +, −, + | .004059 → .005140 | 1.266 | 38.3 → 49.7 |
| .50 | .700 → .688 | −1.25pp | −, −, − | .005444 → .004872 | .895 | 42.0 → 38.7 |

The .35 floor is sign-inconsistent across seeds, so it is not a directional success despite its
positive mean. The .50 floor is consistently negative, not a positive lift. The v3 screen is
therefore **NULL for targeted enrichment at n=3**. The honest fallback is the V-CGA-FROZEN real-
production result (+5.0pp, 23–46% sigma reduction) as Tier-2 observed-in-production evidence,
not yet replicated in this de-circularized apparatus. Recommend a 20-seed extension only after
the apparatus/targeting regime is reviewed; do not claim the v3 screen quantified the production
magnitude.

## Rate and F-verdicts

The unenriched baseline converged at all six operating cells (valid positive k). At ε=.35 the
enriched/un-enriched k ratio is 1.266, outside the ±20% rate-invariance band, so F-RATE fires. At
ε=.50 the ratio is .895 and rate invariance holds. Thus the rate result is also ε-dependent.

- **F-FLOOR:** fired as a positive screen failure overall: no epsilon has a positive floor lift
  with sign-consistency across all three seeds; ε=.50 is consistently negative and ε=.35 is mixed.
- **F-RATE:** fired at ε=.35; not fired at ε=.50.
- **Baseline convergence gate:** passed at both epsilons for all seeds.

## Invariant assertions

| Invariant | Result | Evidence |
|---|---|---|
| I-E1 GT identical | PASS | Shared per-seed/epsilon GT snapshots |
| I-E2 nearest-GT vector-only oracle | PASS | Same oracle rule and construction in both arms |
| I-E3 μ0/d0 identical | PASS | Exact .5 prior; equal .35/.50 d0 values |
| I-E4 learning rule identical | PASS | η=.05 update on the oracle-labeled cell in both arms |
| I-E5 only sigma differs | PASS | Same top-two set; enriched only changes those factors to .04 |
| I-E6 enrichment firewall | PASS | No GT, labeling rule, μ0, eta, or coverage changes |

Labels were not asserted equal; their distribution may differ under sigma reduction as intended.

## Artifacts and verification chart

Raw v3 artifacts and scorer-free summary:
`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw_v3/`

Manifest:
`graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw_v3/manifest.json`

Chart:

- `graph-attention-engine-v50/experiments/h_curve_parametric_regen/figures_v3/henrich_v3_floor_rate.png`
- `graph-attention-engine-v50/experiments/h_curve_parametric_regen/figures_v3/henrich_v3_floor_rate.pdf`
- `graph-attention-engine-v50/experiments/h_curve_parametric_regen/figures_v3/henrich_v3_floor_rate.caption.txt`

The manifest contains 71 artifacts with valid byte sizes and SHA-256 hashes. It includes GT, μ0,
separation/ranking/top-two records, shared random streams, per-factor sigma vectors, decisions,
accuracy and distance trajectories, final μ, k/floor/N metrics, invariant assertions, and chart
outputs. All reported values are scorer-free recomputable.
