# H-CURVE parametric regen — design v3 (corrected, run-ready)

This design supersedes the earlier H-CURVE chain for execution. The implementation location is
graph-attention-engine-v50/experiments/h_curve_parametric_regen/; paper-facing artifacts remain under
copilot-sdk/docs/design/blogs/hypotheses/h-curve/. No product scorer is reused for analysis, and EXP-G1
model validity remains out of scope.

## Ratified edits (C2, C3)

- **C2 — independent firm-deviation geometries:** use `oracle_seed = 99 + run_seed`,
  producing 141 for run seed 42, 222 for run seed 123, and 876 for run seed 777. The μ₀
  RNG and vector RNG remain separate. Geometry gates are evaluated independently for each
  seed.
- **C3 — honest ε=0.05 scope:** retain σ_noise=0.08. If the below-threshold arm censors,
  report it as INCONCLUSIVE using the exact scope statement in the falsification section;
  do not lower noise or add rescue seeds.

## Defect resolution

### The theorem definition

The authoritative theorem states:

> “Let ε_firm = ‖μ_0 − GT_1‖ denote the firm-specific initial mismatch (Phase 1).”
> — cga_arxiv_short_v7_6.md:404-408

The centroid-distance proof path repeats this interpretation: D1 = ε_firm, the Phase-1
starting distance to ground truth in centroid space (cga_arxiv_short_v7_6.md:416-422).
The math synopsis calls ε_firm the firm-specific deviation from the canonical centroid
(math_synopsis_v18.md:699-725). Therefore v3 treats ε_firm as the actual raw Frobenius
distance between the scorer’s Phase-1 starting tensor and GT1; it is not merely an oracle
displacement label.

### Chosen construction: option (a), exact canonical cold start

Use option (a):

- canonical_prior: fixed tensor np.full((C,A,d), 0.5).
- scorer_mu0: exact copy of canonical_prior; no jitter and no expert initialization.
- GT1: the oracle’s displacement from that same fixed canonical_prior, using independent
  per-cell oracle RNG seed `oracle_seed = 99 + run_seed`.
- Configured theorem epsilon_firm values are the desired raw ||scorer_mu0 − GT1||_F.

This is the construction that follows both the theorem’s distance definition and the actual
oracle’s documented base without adding an uncontrolled jitter term. The realistic-jitter
intent in v2 is retired because jitter would add an uncontrolled component to the theorem’s
Phase-1 mismatch. The target is still non-circular: FactorVectorSampler samples around a
generic 0.5 distribution and never receives scorer centroids or GT tensors
(graph-attention-engine-v50/gae/synthetic.py:39-98).

### Required oracle-parameter conversion

GroundTruthOracle._build_ground_truth starts from self._canonical, defaults that canonical
tensor to 0.5, draws a unit direction per category/action cell, adds
config.epsilon_firm * sqrt(C*A) * direction, and clips to [0,1]
(copilot-sdk/examples/jm_reference/oracle.py:53-80). With C=6 and A=4, an unclipped oracle
parameter e produces raw tensor displacement e*(C*A), because there are C*A cells each with
norm e*sqrt(C*A).

Therefore the run parameter names are frozen:

- epsilon_firm: theorem/raw mismatch target: 0.05, 0.20, 0.35.
- oracle_epsilon: internal oracle parameter: epsilon_firm / (C*A).
- scorer_mu0 = canonical_prior: exact fixed 0.5 tensor.
- GT1 = GroundTruthOracle(OracleConfig(seed=oracle_seed, canonical_prior=canonical_prior,
  epsilon_firm=oracle_epsilon)).ground_truth_centroids.

The runner must persist both epsilon names. Before running a cell it must assert that
||GT1 − scorer_mu0||_F equals configured epsilon_firm within absolute tolerance 1e-10 and
that no GT1 element was clipped. If either assertion fails, STOP; do not reinterpret the
result. This makes the theorem quantity explicit rather than relying on the oracle’s
measured_epsilon_firm convenience property, which reports a normalized distance from its
canonical tensor (oracle.py:133-138).

## Run design

Run one independent OracleSeparationExperiment per seed × epsilon cell.

| Parameter | Frozen value |
|---|---|
| Seeds | 42, 123, 777 |
| theorem epsilon_firm | 0.05, 0.20, 0.35 |
| oracle_epsilon | epsilon_firm / 24 |
| Tensor | C=6, A=4, d=6; shape (6,4,6) |
| scorer_mu0 | exact fixed 0.5 tensor for every seed and epsilon |
| Oracle RNG | `oracle_seed = 99 + run_seed`: 141, 222, 876; independent from vector RNG |
| max decisions | 300 for 0.05 and 0.20; 600 for 0.35 |
| Phase vectors | cold_start for both phases; never post_disruption |
| factor noise | sigma_noise=0.08 |
| rolling window | w=10 |
| theta | 0.85, used only for secondary N_half |
| disruption | categories [0,1], alpha_disrupt=2/6, ||Delta||=0.25 |

The runner imports FactorVectorSampler, CanonicalCentroid, and OracleSeparationExperiment
from graph-attention-engine-v50/gae/synthetic.py. The experiment consumes the supplied
CanonicalCentroid(GT1); Phase 1 scores and updates the scorer against GT1, and Phase 2
resets to the Phase-1 final scorer tensor and applies disruption only to GT1
(synthetic.py:182-220 and 238-325). Oracle labels are nearest-action distances to the
supplied target, not the scorer’s current answer (synthetic.py:222-236).

## Geometry and non-centroidality gates

Before any Phase-1 decision, persist and assert:

1. canonical_prior and scorer_mu0 are elementwise identical.
2. GT1 was produced from that canonical tensor with the cell’s persisted
   `oracle_seed = 99 + run_seed` and oracle_epsilon=epsilon_firm/24.
3. ||GT1−scorer_mu0||_F = epsilon_firm within 1e-10.
4. The displacement direction is unit norm per cell before scaling, and the post-construction
   tensor contains no clipped coordinate. If clipping occurs, STOP; do not substitute a
   post-clip epsilon.
5. For each run seed independently, the measured raw starting mismatches are strictly
   ordered 0.05 < 0.20 < 0.35 within tolerance.

Persist per cell: epsilon_firm_configured, oracle_epsilon, starting_mismatch_raw,
starting_mismatch_normalized, base_label=canonical_prior, scorer_mu0_label=exact_canonical_prior,
and gt1_label=oracle_displacement.

Parametric samples are non-centroidal by construction. FactorVectorSampler.sample draws
clipped Gaussian vectors around generic base mean 0.5 using only its factor-noise profile
and RNG; it receives neither scorer_mu0 nor GT1 (synthetic.py:39-98). For every vector,
persist distances to the relevant GT action centroids and scorer_mu0 action centroids, plus
inter-action and inter-regime spacings. Report mean, median, SD, and IQR by regime and the
ratio to nearest-centroid distance. DISPERSED means vectors are not concentrated relative
to centroid spacing; CLUSTERED means they are. Missing measurements fail closed.

## epsilon_star computation and straddle gate

Before constructing or running any gamma cell, compute:

epsilon_star = (alpha_disrupt * delta_norm) / (1 - alpha_disrupt).

With alpha_disrupt=2/6 and delta_norm=0.25, assert epsilon_star=0.125 and assert
0.05 < epsilon_star < 0.20 < 0.35. This is the theta-cancelled theorem form
(cga_arxiv_short_v7_6.md:408-422; math_synopsis_v18.md:699-720). STOP before any gamma
cell if the calculation or straddle assertion fails.

## theta-free gamma: primary measure

For each phase, let d_t be the raw Frobenius distance between the current scorer tensor
and that phase’s target. The runner uses the trajectory emitted by
CanonicalCentroid.distance_from and centroid_distance_to_canonical
(synthetic.py:137-139; convergence.py:1210-1230).

Define the primary fixed-fraction crossing:
N_half_dist = min { t >= 1 : d_t <= 0.5*d_0 }.

Define gamma_dist = N_half_dist_phase1 / N_half_dist_phase2. A missing crossing is right-censored
and the cell is INCONCLUSIVE; never replace it with max_decisions or zero. A log-distance
exponential fit is exploratory only. Check raw monotonicity directly; any increase
d_t > d_(t-1) is an F3 violation, with no smoothing.

For F2 only, report secondary GammaResult.gamma, the theta-dependent N_half,1/N_half,2
(synthetic.py:159-175 and 333-370). Compare directions of gamma_dist−1 and gamma_nhalf−1
per seed and epsilon. Missing or DNF values remain missing.

## Falsification and analysis plan

The binary prediction is:

- below threshold: epsilon_firm < epsilon_star implies gamma_dist < 1;
- above threshold: epsilon_firm > epsilon_star implies gamma_dist > 1.

Report F1 if either side fails. Report F2 if theta-free and theta-dependent gamma disagree in
direction. Report F3 if any required raw distance trajectory is non-monotone. A censored cell
is INCONCLUSIVE, not a favorable result. For a censored below-threshold cell, report exactly:

> Below-threshold cell inconclusive due to noise dominance at ε_firm < σ_noise (0.05 < 0.08);
> consistent with the theorem's prediction of negligible advantage below ε★, but NOT a confirmed
> γ < 1. The above-threshold arms (ε=0.20, 0.35) carry the binary test and the paper's spine.

Do not lower σ_noise or add seeds to rescue ε=0.05; changing conditions to chase a commercially
irrelevant result is out of scope. The cell runs at σ_noise=0.08 like the others. Report every
seed, per-epsilon summaries, two-sided 95% small-sample intervals, and censored/DNF counts.

The theorem prerequisites must be reported: category-sparse disruption, a Phase-1 cold start,
and the epsilon mismatch condition (cga_arxiv_short_v7_6.md:424-428). EXP-G1 model validity
is explicitly out of scope.

## Persistence and scorer-free recomputation

Write fresh artifacts under
graph-attention-engine-v50/experiments/h_curve_parametric_regen/raw/:

    raw/manifest.json
    raw/runs/seed-042/epsilon-0.05/
      vectors_phase1.jsonl
      vectors_phase2.jsonl
      centroids_canonical_prior.npy
      centroids_mu0.npy
      centroids_gt1.npy
      centroids_gt2.npy
      centroids_mu_phase1_final.npy
      centroids_mu_phase2_final.npy
      distance_trajectories.json
      gamma.json
      vector_distance_summary.json

Use one directory per cell. Every vector record includes seed, configured epsilon,
oracle epsilon, oracle_seed, phase, regime, generation seed, values, and sigma profile. Every centroid
snapshot includes shape, dtype, construction label, and SHA-256. Trajectories include raw
distances, phase target identity, monotonicity, N_half_dist, theta-dependent N_half,
censoring, and starting mismatch. gamma.json includes both gamma values, rates, threshold,
prediction, and F1/F2/F3 status.

Write manifest.json only after all cells complete. It contains schema version, UTC time,
source repo and runner entry point, all frozen config, the theorem-to-oracle epsilon
conversion, canonical/GT construction statement, epsilon_star computation and straddle
result, per-file relative path/size/SHA-256/role, per-cell run_seed, oracle_seed,
epsilon_firm, geometry assertions, completion, and censoring status,
runtime versions, and config hash. Write atomically and fail if any expected artifact or hash
is absent. A scorer-free recompute utility must reconstruct both gamma measures and all
distance summaries from persisted arrays/JSON alone.

## Power and reading

Use the documented three seeds per epsilon. Because C2 varies the oracle seed with the run
seed, these are three independent firm-deviation geometries: oracle_seed values 141, 222,
and 876. Report every geometry, seed, median, mean, and two-sided 95% small-sample interval
for gamma_dist and log-scale distance-rate differences. Label n=3 as thin. A consistent
direction across all three independent geometries is evidence of geometric robustness of
this parametric mechanism, not a high-powered universal estimate and not merely
sampling-noise robustness at one fixed geometry. If geometries disagree, an interval
spans the boundary, or a required cell is censored, classify the relevant claim
INCONCLUSIVE. The pre-registered extension is at least 20 seeds per epsilon with the same
code and manifest; never silently substitute it.

## Self-check

No. Below-threshold cells can produce gamma_dist<1, above-threshold cells can fail the
prediction, raw monotonicity can fail, gamma can be censored, and theta-free and N_half
directions can disagree. The geometry gate can also stop the run instead of accepting an
ambiguous target.

## Open questions for reviewer

1. No physics choice remains unresolved by the theorem/code for the base: v3 chooses the
   theorem-supported exact canonical prior and removes jitter.
2. C2 intentionally varies the firm-deviation geometry through oracle_seed = 99 + run_seed;
   the vector RNG and μ₀ construction remain unchanged.
3. The only implementation stop condition is intentional: if clipping is triggered or raw
   mismatch does not equal configured epsilon after the epsilon_firm/24 conversion, the
   run stops and requires a new design rather than silently changing epsilon semantics.
4. The requested filename design_v2.md is absent in this repository snapshot; the frozen v2
   content is present as design_v2_hcurve.md. This is a document-naming issue, not a physics
   decision.

## Freeze statement

D1: exact canonical scorer cold start; D2: GT1 from the same canonical tensor; D3: raw epsilon
conversion through the oracle’s cell-scaled parameter; D4: epsilon_star computed and
straddle-gated. All-cold init, theta-free primary gamma, secondary N_half F2 check,
persistence, honest n=3 reading, F1/F2/F3, and EXP-G1 scope wall are frozen for Stage 4.
