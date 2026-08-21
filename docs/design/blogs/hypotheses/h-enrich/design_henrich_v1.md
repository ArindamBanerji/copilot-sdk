# H-ENRICH design v1

## Question and operating point

This experiment tests whether enrichment changes the first-curve floor without changing its
learning rate. It uses the existing H-CURVE parametric geometry at the single operating point
`epsilon_firm=0.20`, with `C=6`, `A=4`, `d=6`, canonical `mu0=0.5`, seeds 42/123/777, and 720
round-robin decisions per arm and seed (30 per `(category, action)` cell).

## Two arms

UNENRICHED uses `sigma_f=[.08,.08,.08,.08,.08,.08]`. ENRICHED uses
`sigma_f=[.04,.04,.08,.08,.08,.08]`. For each seed and decision, both arms use the same
standard-normal draw `z`; the vector is `clip(GT[c,a] + sigma_f*z, 0, 1)`. Thus only the
factor-vector noise scale differs. GT, `mu0`, coverage, the learning rule, and the oracle rule are
shared.

The oracle labels the chosen action by nearest GT centroid for the category, using the vector as
input. Labels may differ between arms: that distributional change is the intended enrichment
mechanism and is not a firewall violation.

## Metrics and predictions

- **FLOOR (primary):** mean accuracy over decisions 1–10 before material learning movement.
  Prediction: ENRICHED > UNENRICHED.
- **RATE INVARIANCE (primary):** exponential decay constant `k` from active-cell centroid
  distance, using H-CURVE's ten-decision block means and median pairwise log-slopes. Rate holds if
  `k_enriched/k_unenriched` is within `[.80,1.20]`.
- **SECONDARY:** first decision at which rolling ten-decision accuracy reaches `.70`; lower is
  better. Missing crossings are reported as censored.
- `d0=||mu0-GT||_F` is reported for both arms and must be equal.

## Invariants I-E1..I-E6

1. **I-E1:** GT is identical across arms for each seed.
2. **I-E2:** the nearest-GT oracle labeling rule is identical across arms; it receives the vector,
   not sigma.
3. **I-E3:** `mu0` is the identical exact 0.5 prior and distance to GT is equal.
4. **I-E4:** both arms use `mu <- mu + .05*(f-mu)` on the labeled `(c,a)` cell.
5. **I-E5:** only `sigma_f` differs, with the enriched pair [0,1] at .04.
6. **I-E6:** enrichment never changes GT, labels' rule, mu0, eta, coverage, or learning code.

## Persistence and falsification

Each seed × arm persists GT, mu0, mu_final, every vector's per-factor sigma and shared normal draw,
oracle label, prediction, correctness, distance trajectory, accuracy trajectory, floor, k, N, and
invariant assertions. A manifest is written atomically with SHA-256 for every artifact; all metrics
are scorer-free recomputable.

F-FLOOR fires if enriched does not lift the day-1 floor. F-RATE fires if enrichment changes k by
more than ±20%; in that case the result is not pure leveling. The split is supported only when the
floor lifts and rate invariance holds. No scorer is imported or modified.

## Apparatus correction

The distance trajectory begins with the exact pre-learning distance `||mu0-GT||` before decision
1, followed by one value after each update. This prevents the first update from redefining `d0` and
ensures the invariant comparison is identical across arms. The H-CURVE block-fit convention is
otherwise unchanged.

## Design fix and variant

**DF-E1 / V1:** exact μ₀ creates an all-action tie at the first decisions, and raw `argmin`
tie-breaking selects action 0. The run therefore adds a shared, independent tie-break stream used
only when the current centroid distances are exactly tied. It is identical across arms and is not
derived from GT, labels, sigma, or the scorer. This removes an action-0 floor artifact while
preserving every I-E1..I-E6. The default and neutral-tie results are both retained in the raw
exploratory values are recorded in `results_henrich_v1.md`; the final raw tree is the trusted
neutral-tie run.

## Ratified v2 settings and reading

The headroom run uses `epsilon_firm=0.35` and `0.50`, single-phase cold-start convergence, 1200
round-robin decisions per seed and arm, and seeds 42/123/777. The primary floor is the mean of the
first 10 decisions **per each of the 24 cells**, not the first 10 global decisions. The baseline
must first have a valid positive k at each operating point; otherwise the setup is reported as
non-converging. The v2 output is stored separately under `experiments/h_enrich_v1/raw_v2/`.

## Variants tried

- **V0 / action-0 tie break:** exploratory only; exact μ0 ties selected action 0 and contaminated
  the floor. Rejected in favor of the shared neutral tie stream.
- **V1 / shared neutral tie stream:** retained. It is arm-identical and independent of GT, labels,
  sigma, and learning state, so it removes the tie artifact without changing I-E1..I-E6.
- **V2 / ratified headroom grid:** retained as the trusted run: ε=.35 and .50 with per-cell first-10
  floor and 1200 decisions. It tests whether leveling is stable or regime-dependent.
