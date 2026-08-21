# H-ENRICH results v2

## Design fixes applied

- **DF-E2 — ratified floor window:** v2 computes accuracy over the first 10 observations of each
  `(category, action)` cell, then averages the 24 cell floors. This implements the ratified
  starting-geometry metric and avoids confusing the global round-robin prefix with 10 observations
  per cell.
- **DF-E3 — headroom grid:** v2 runs the ratified ε=.35 and ε=.50 points at 1200 decisions per
  cell schedule, retaining the same GT, oracle, μ0, η, sigma assignment, and neutral tie stream.

## Baseline convergence gate

The UNENRICHED baseline has a valid positive H-CURVE k fit for every seed at both operating points:
6/6 baseline cells pass the positive-k and retained-block gate. The setup therefore did not trigger
the non-converging-baseline stop.

## Per-seed metrics

Floor is the mean of 24 per-cell ten-decision windows. N is the first global decision whose rolling
ten-decision accuracy reaches .70.

| ε | Seed | Arm | Floor (1–10/cell) | N to .70 | d0 | k | Fit valid |
|---:|---:|---|---:|---:|---:|---:|---|
| .35 | 42 | Unenriched | .642 | 13 | .350 | .004253 | Yes |
| .35 | 42 | Enriched | .596 | 46 | .350 | .006289 | Yes |
| .35 | 123 | Unenriched | .612 | 64 | .350 | .002181 | Yes |
| .35 | 123 | Enriched | .638 | 50 | .350 | .002301 | Yes |
| .35 | 777 | Unenriched | .612 | 38 | .350 | .005743 | Yes |
| .35 | 777 | Enriched | .658 | 56 | .350 | .006067 | Yes |
| .50 | 42 | Unenriched | .692 | 51 | .500 | .005563 | Yes |
| .50 | 42 | Enriched | .679 | 51 | .500 | .004682 | Yes |
| .50 | 123 | Unenriched | .712 | 35 | .500 | .005304 | Yes |
| .50 | 123 | Enriched | .696 | 32 | .500 | .005489 | Yes |
| .50 | 777 | Unenriched | .696 | 40 | .500 | .005464 | Yes |
| .50 | 777 | Enriched | .692 | 32 | .500 | .004775 | Yes |

## Split verdict by operating point

| ε | Mean floor unenriched → enriched | Floor lift | Mean k unenriched → enriched | k ratio | Mean N unenriched → enriched | Reading |
|---:|---:|---:|---:|---:|---:|---|
| .35 | .622 → .631 | +0.83pp | .004059 → .004886 | 1.204 | 38.3 → 50.7 | Floor lifts, but k exceeds the +20% invariance bound |
| .50 | .700 → .689 | −1.11pp | .005444 → .004982 | .915 | 42.0 → 38.3 | Rate invariant, but floor does not lift |

At ε=.35, F-FLOOR does not fire, but F-RATE fires narrowly because the k ratio is 1.204,
outside the ratified [0.80, 1.20] interval. At ε=.50, F-RATE does not fire, but F-FLOOR fires.
The leveling split is therefore **ε-dependent**: neither operating point satisfies both primary
conditions simultaneously. The secondary N agrees with neither a uniform rule: enrichment is
worse at .35 and better at .50.

## F-verdicts

- **F-FLOOR:** not fired at .35; fired at .50.
- **F-RATE:** fired at .35; not fired at .50.
- **Baseline setup gate:** passed at both epsilons for all three seeds.

## Invariant assertions

| Invariant | Result | Evidence |
|---|---|---|
| I-E1 GT identical | PASS | One GT snapshot per seed/epsilon is shared by both arms |
| I-E2 nearest-GT oracle rule | PASS | Same oracle construction and vector-only label input |
| I-E3 μ0 and d0 identical | PASS | Exact .5 prior; d0=.35 or .50 identically by arm |
| I-E4 learning rule identical | PASS | Both arms use η=.05 on the oracle-labeled cell |
| I-E5 only sigma differs | PASS | .08 baseline; .04 only on factors [0,1] enriched |
| I-E6 enrichment firewall | PASS | GT, labeling rule, μ0, η, coverage unchanged |

Labels are not asserted equal: sigma reduction changes the oracle-label distribution as intended.
The persisted shared normal draws and per-factor sigma vectors make that mechanism auditable.

## Overall reading and roadmap

The ratified HEADROOM reading is **not uniformly supported**. The experiment finds a regime boundary:
at ε=.35 enrichment produces a small floor lift but also measurably changes the fitted rate; at
ε=.50 the rate remains within tolerance but the floor lift disappears. The roadmap item is to
identify whether this boundary is caused by factor-specific label separation, the fixed [0,1]
enrichment subset, or the accuracy threshold/window—not to collapse the two points into a single
leveling claim. Rescue of a non-converging baseline remains out of scope.

## Artifacts and chart

Raw v2 artifacts and scorer-free summary:

`graph-attention-engine-v50/experiments/h_enrich_v1/raw_v2/`

Manifest:

`graph-attention-engine-v50/experiments/h_enrich_v1/raw_v2/manifest.json`

Verification chart:

- `graph-attention-engine-v50/experiments/h_enrich_v1/figures_v2/henrich_v2_floor_rate.png`
- `graph-attention-engine-v50/experiments/h_enrich_v1/figures_v2/henrich_v2_floor_rate.pdf`
- `graph-attention-engine-v50/experiments/h_enrich_v1/figures_v2/henrich_v2_floor_rate.caption.txt`

The v2 manifest contains 65 hashed artifacts and passed byte-size and SHA-256 verification. It
includes per-seed/epsilon GT and μ0, shared normal and tie streams, per-arm vectors with sigma,
labels, predictions, correctness, trajectories, final μ, floor/N/k metrics, invariant records, and
the chart outputs. All reported metrics are scorer-free recomputable.
