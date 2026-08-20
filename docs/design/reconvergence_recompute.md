## Task 1 — vector-to-centroid distances

**VERDICT: NOT FOUND — neither [CLUSTERED] nor [DISPERSED] can be established from the available outputs.**

The implementation paths were located, but the persisted inputs required for this post-processing are absent:

| Required artifact | Located implementation/evidence | Exact output used | Result |
|---|---|---|---|
| LLM-generated factor vectors, grouped by regime | `graph-attention-engine-v50/gae/synthetic.py:FactorVectorSampler.sample` returns `FactorVectorSample.f` (lines 31–39, 68–100) | Oracle-separation result archive / vector file | **NOT FOUND** |
| GT centroids (`canonical_mu`/canonical GT) | `graph-attention-engine-v50/gae/synthetic.py:CanonicalCentroid` and `OracleSeparationExperiment.__init__` (lines 102–114, 182–220) | Oracle-separation centroid snapshot | **NOT FOUND** |
| Scorer learned centroids μ | `graph-attention-engine-v50/gae/synthetic.py:OracleSeparationExperiment._run_phase` reads `self.scorer.centroids` (lines 238–266) | Per-seed scorer snapshot | **NOT FOUND** |
| Inter-centroid spacing | Would be computed from the GT centroid snapshot and regime labels | GT/vector output bundle | **NOT FOUND** |

No stored LLM vector file, GT-centroid file, or scorer-centroid snapshot for the cited oracle-separation run was found under the accessible project tree. The experiment code confirms the oracle separates canonical GT from scorer state, but code alone cannot supply the missing sample distribution. Consequently, no mean, median, spread, or normalized distance can be reported without regenerating data, which is prohibited here.

## Task 2 — θ-free γ recomputation

**VERDICT: NOT FOUND — θ-free γ cannot be recomputed from the available trajectory outputs.**

The relevant logging paths were located:

| Required artifact | Located implementation/evidence | Exact output used | Result |
|---|---|---|---|
| Per-seed, per-phase centroid-distance trajectory | `graph-attention-engine-v50/gae/synthetic.py:OracleSeparationExperiment._run_phase` appends `canonical.distance_from(self.scorer.centroids)` to `distances` (lines 238–266) | Gamma-audit trajectory output | **NOT FOUND** |
| Distance definition | `graph-attention-engine-v50/gae/convergence.py:centroid_distance_to_canonical` computes the Frobenius/L2 norm (lines 1210–1230) | N/A — implementation only | Located, no persisted trace |
| Production graph distance log | `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:log_decision_distance` writes `centroid_distance_to_canonical`, and `read_decision_distance_log` reads it (lines 142–191) | Exported graph log for the oracle audit | **NOT FOUND** |
| Phase-1/Phase-2 ε=0.05 and ε=0.20 traces | `OracleSeparationExperiment.run_phase1`, `run_phase2`, and `compute_gamma` are present (synthetic.py:291–356) | Gamma-audit output files | **NOT FOUND** |

The available code would support a θ-free calculation, for example decisions to the first fixed fraction of each trajectory’s initial distance, followed by `gamma_distance = rate_phase_1 / rate_phase_2`. But the required per-seed distance arrays are not in the accessible tree, so no ε-specific rate, γ, confidence interval, or comparison with the reported N-half values can be honestly produced. The documented external `G:\` location could not be read in this environment, and no local copy of the gamma-audit output was found.

Therefore the binary prediction (γ<1 below ε★ and γ>1 above ε★) and agreement with the reported N-half γ remain **UNDETERMINED**, not confirmed or contradicted.

## One-line finding

**H-CURVE data circularity NOT cleared — Task 1 failed because the stored LLM vectors and centroid snapshots were not found, and Task 2 failed because the logged per-seed centroid-distance trajectories were not found; only model validity (EXP-G1) remains out of scope once those artifacts are supplied.**
