# Verification Scan D+F — Math, Quality, and Program B

**Date:** 2026-08-06  
**Type:** Read-only diagnostic. No source, graph, or database modified.

## Executive status

| Item | Status | Finding |
|---|---|---|
| V2 SOC drift formula | CONFIRMED, with two layers | The scorer computes Euclidean L2 update magnitude. The SOC persistence helper also computes pre/post Euclidean L2. The framework route documents a different cumulative mean-over-actions drift when it must reconstruct history. |
| V3 math invariant inventory | CONFIRMED | The synopsis defines the scoring, learning, conservation, convergence, novelty, promotion, IKS, and quality equations listed below. |
| V3b `SNAPSHOT_AFTER` | GAP / not specified by math | The synopsis does not require or define `SNAPSHOT_AFTER` traversal. It is a graph/JM lineage structure, not a stated numerical invariant. |
| V12 quality axis | GAP | `verified_count / decisions_count` is a verification rate, not rolling prediction accuracy. Checkpoints do not contain the correct-count/window data required by the synopsis. |
| V12b factor consistency | GAP | The synopsis requires factor-version drift detection/reset behavior, but the startup loader does not validate `factor_names_hash`. |
| V9 Program B | PARTIAL / GAP | The AGE migration and resumable batch machinery exist, but learned L5/DK/conservation state is intentionally excluded and legacy null-id checkpoint preservation is not demonstrated. |

## SCAN D — Math

### V2: SOC drift formula

**Status: CONFIRMED for the underlying metric; GAP for one canonical semantic.**

The authoritative scorer computes the update vector and then its ordinary Euclidean norm:

```python
# graph-attention-engine-v50/gae/profile_scorer.py:943-950
delta_vector = eta_eff * self._compute_gradient(f, self.mu[c, a, :])
...
centroid_delta_norm = float(np.linalg.norm(delta_vector))
self.mu[c, a, :] += delta_vector

# :967-972 and :976-981 perform the same norm for override paths.
```

Therefore `centroid_delta_norm = ||delta_applied||₂`; it is not cosine distance and not a Frobenius norm of the whole tensor. There is no normalization in this calculation beyond the learning-rate, factor-mask, and per-coordinate clip applied before the norm (`profile_scorer.py:945-949`, `:967-971`, `:976-980`). The `CentroidUpdate` field documents the same meaning at `profile_scorer.py:56`.

SOC’s L5 persistence helper independently computes a pre/post vector L2 norm at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437`: if no prior centroid exists it norms the post vector; otherwise it norms `post - pre`. The triage path writes the resulting value to `Decision.centroid_delta_norm` at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2322-2332`.

The framework route describes its fallback as cumulative drift from bootstrap, averaged over actions, at `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:115-122`; it reads persisted Decision values at `:132-158`. Thus the implementation has two related but distinct quantities:

1. per-decision applied-update L2;
2. cumulative centroid-from-bootstrap L2, averaged over actions when reconstructed.

The math synopsis defines cumulative mean centroid drift for IKS as an average of per-cell L2 distances at `math_synopsis_v18.md:1138-1155`. It does not define the Decision property’s per-update field or require one canonical field name. This is a semantic **GAP** even though the primitive metric is Euclidean.

### V3: Complete math-invariant list

The list below extracts the mathematical abstractions and operational constraints from `math_synopsis_v18.md:406-432`, the equation sections, and the equation index at `:2178-2203`. “Store method” means the current persistence surface that carries or exercises the state; “none” means no direct implementation assertion was found.

| # | Invariant / formula | Plain-English constraint | Current code/test evidence | Store method |
|---:|---|---|---|---|
| 1 | `P(a\|f,c)=softmax(-K(f,μ[c,a,:])/τ)`; `a*=argmax P` (`:436-448`) | Action probabilities come from factor-to-centroid distance and the selected action is the maximum. | `graph-attention-engine-v50/gae/profile_scorer.py:408-511`; scorer tests exercise scoring. | `load_latest_centroids`, `save_centroids` |
| 2 | `K_L2=Σ_j(f_j-μ_j)^2`; diagonal kernel `K=(f-μ)^T W(f-μ)` (`:450-?`) | Distance is nonnegative and factor dimensions are weighted independently in the diagonal kernel. | `gae/profile_scorer.py` scoring path; `gae/tests/test_profile_scorer.py`. | Centroid tensor / DK state |
| 3 | `μ←μ+η(f-μ)` and Eq. 4b push/pull update (`:498-527`) | Correct predictions pull the selected centroid toward the vector; wrong predictions push the wrong centroid and pull the ground-truth centroid. | `gae/profile_scorer.py:943-985`; `gae/tests/test_learning.py`. | `update_centroid` |
| 4 | `η_confirm=.05`, `η_override=.01`, effective `η/(1+n·decay_rate)` (`:498-527`, `:1592-1603`) | Confirmation and override use distinct learning rates, with decay. | `gae/profile_scorer.py` learning paths; tests cover override-rate behavior. | `update_centroid` |
| 5 | `0≤μ_j≤1` after every update; masked dimensions do not update (`:526-527`) | Centroids remain in factor space and masked dimensions are invariant. | `gae/profile_scorer.py:946-950`, factor-mask branches. | `update_centroid` |
| 6 | `E[e_n]≈(1-η_eff)^n e_0`; `N_half≈14` at `.05`, `≈69` at `.01` (`:634-641`) | Constant-step convergence has the stated exponential half-life. | No dedicated production assertion for the numeric half-life found. | none; **GAP** |
| 7 | `w~=αw_DK+(1-α)w_0`, `p≥3` (`:406-432`) | DK weights are shrunk toward a stable prior. | `scorer.py:270-279` configures DK estimator; no complete shrinkage assertion located. | DK weight state; **GAP** |
| 8 | DK `W=diag(w_j)`, positive diagonal; coordinate-descent objective (`:1039-1118`) | Learned weights remain diagonal/positive and are promoted only after validation. | `graph-attention-engine-v50/gae/dk_estimator.py:34-180`; `tests/test_dk_estimator.py`. | `update_dk_weights` |
| 9 | Novelty `min_{f'∈H(c,a)}||f-f'||₂`, `H` last 300 same-cell decisions (`:1124-1134`) | New samples trigger calibration only when sufficiently novel. | Batch-pipeline code/tests exist, but a universal store-level assertion was not found. | decision/history store; **GAP** |
| 10 | Composition trigger: novel fraction `≥.10`, coverage `≥3/C`, count `≥50` (`:1101-1118`) | DK estimation requires enough novel, category-covered data. | `scorer.py` re-estimation path and batch tests. | decision history |
| 11 | Holdout validation: overall loss ≤1.0pp, category loss ≤2.0pp, active cell count `≥20`, 20% stratified holdout (`:1101-1118`) | New weights cannot materially regress validated performance. | Batch pipeline tests cover estimator behavior; end-to-end promotion coverage is incomplete. | checkpoint/DK promotion; **GAP** |
| 12 | Conservation `α·q·V≥θ_min`; `α=cumulative category coverage`, `q=rolling verified accuracy`, `θ_min=23.53/(αV)` (`:406-432`, `:1647-1655`) | Automation is allowed only when category coverage, verified quality, and verified volume support it. | `copilot-sdk/copilot_sdk/scoring/scorer.py:1626-1690`, `:1970-1989`. | `update_conservation_state` |
| 13 | `q(t)=Σ verified-correct / N_v` over the last 400 decisions (`:1605-1641`) | Quality is verified prediction accuracy, not raw decision count or verification rate. | The shared scorer has conservation statistics, but its exact rolling-window parity with the synopsis is not established. | Outcome/decision history; **GAP** |
| 14 | IKS `100·min(D(t)/κ*,1)`, `D=mean_{c,a}||μ[c,a](t)-μ[c,a](0)||₂`, `κ*=.20` (`:1138-1155`) | IKS measures normalized centroid evolution from the bootstrap state. | SOC `framework/iks_base.py:49-96` implements drift-based IKS; shared SDK `scorer.py:1570-1615` uses a different composite. | centroid/L5 state |
| 15 | Re-convergence `γ=N_half,1/N_half,2`; disruption threshold `ε_firm*=α_disrupt||Δ||/(1-α_disrupt)≈.125` (`:648-?`, `:811-814`) | Recovery speed and disruption magnitude obey the stated threshold relationships. | No direct conformance assertion found. | learning state; **GAP** |
| 16 | Auto-pause: rolling `q` below baseline×.9 or floor `.70/.60`; resume after 100 qualifying decisions (`:1542-1566`) | Learning pauses when verified quality degrades and resumes only after recovery. | `scorer.py` conservation/pause code; direct threshold parity with synopsis is not proven. | `update_conservation_state`; **GAP** |
| 17 | Factor-version drift requires alpha reduction/reset behavior (`:2321-2345`) | A changed factor schema cannot silently continue in the old coordinate system. | `factor_names_hash` is persisted by V2, but startup validation was not found. | checkpoint metadata; **GAP** |

The synopsis also lists Fisher-information motivation and Judgment Memory positioning (`:406-432`); those are explanatory architecture statements, not executable invariants, so they are not counted above.

#### V3b: `SNAPSHOT_AFTER`

**Status: CONFIRMED as a storage/JM requirement; NOT SPECIFIED as a math traversal requirement.**

The math synopsis contains no `SNAPSHOT_AFTER` equation or traversal invariant. Its history references are mathematical windows (`H(c,a)` and the last-400 quality window), not graph-edge traversal. Consequently, none of invariants 1–17 requires a `Decision -[:SNAPSHOT_AFTER]-> CentroidCheckpoint` traversal for numerical correctness. The edge remains important for provenance and lineage under the separate JM graph plan. The AGE writer creates it at `ci-platform/ci_platform/graph/age_graph_store.py:1103-1125` and `:1421-1426`, but no reader traversal was found.

### V12: Quality-axis feasibility

**Status: GAP.**

`verified_count / decisions_count` is mathematically a verification/coverage ratio. It cannot equal the synopsis’ rolling accuracy `q` unless the numerator is a correct-count, which it is not. The checkpoint schema stores `verified_count`, `decisions_count`, and `iks` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:441-458`), but no rolling window membership, correct count, or per-decision outcome sequence. Therefore rolling accuracy is not reconstructible from one checkpoint row alone.

Per-checkpoint IKS is representable because `iks` is stored, but the stored value’s semantic parity is not guaranteed: the synopsis’ drift-based formula differs from the shared scorer’s composite `_compute_iks` at `scorer.py:1570-1615`.

Counterfactual infrastructure exists, but it is not yet a generic math-conformance replay engine:

- DataOps DI perturbation endpoints: `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:17-63`, mounted by `main.py:624-625` and `:736-738`.
- S2P counterfactual router: `s2p-copilot/backend/app/main.py:11`, `:240`; S2P performance what-if: `s2p-copilot/backend/app/routers/s2p_performance.py:192`.
- SOC what-if projection is a scenario simulation, not graph replay: `gen-ai-roi-demo-v4-v50/backend/app/services/whatif_service.py:36-202` and `routers/whatif_router.py:54-73`.
- DataOps `WhatIfReordering` is a UI/feature consumer (`copilot-sdk/apps/dataops/frontend/src/screens/InsightScreen.tsx:15,113`).

These surfaces can support a replay experiment, but no common cross-adapter replay contract was found: **GAP**.

### V12b: Factor-name consistency

**Status: GAP.** The synopsis requires factor-version drift detection/reset (`math_synopsis_v18.md:2321-2345`), but it does not prescribe the exact `factor_names_hash` field. V2 writes that metadata, while the startup loader does not validate factor order/hash. A changed factor order or dimension can therefore make historical centroids numerically incompatible without a loader rejection. This is a conformance gap against the factor-version safety intent.

### DK weight formula

The deployed DK estimator is discriminative coordinate descent, not Welford inverse variance:

- `graph-attention-engine-v50/gae/dk_estimator.py:34-80` defines `CoordinateDescentEstimator`; `:129-180` initializes weights and searches candidate values per coordinate.
- `:180` onward evaluates the accuracy objective for each candidate and retains improving values.
- The shared scorer configures it at `copilot-sdk/copilot_sdk/scoring/scorer.py:270-279`, invokes estimation at `:441`, and refreshes it after verified learning at `:1621-1624`.

SOC additionally maintains a Welford audit tracker, updated under a process lock at `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:318-365`, and persists its state with DK weights at `:350-371`. That Welford state is an accumulator/audit statistic; it is not the synopsis’ discriminative DK formula. **Status: CONFIRMED for coordinate descent; GAP if Welford is treated as the production DK estimator.**

## SCAN F — Program B

### V9: Program B state

**Status: PARTIAL.** The design exists at `copilot-sdk/docs/implementation_plans/shared_judgment_memory_graph_plan.md`:

- canonical shared AGE direction and SQLite local/test distinction: `:5-14`, `:83-95`;
- canonical `CentroidCheckpoint` properties: `:123-125`;
- required `SNAPSHOT_AFTER` relationship: `:170-175`;
- SQLite-to-AGE migration and S2P-first rollout steps: `:231-263`;
- checkpoint parity, protocol, and cross-domain validation: `:472-490`.

The executable migration is `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py`. Its module contract says verified decisions are the default, pending work is optional, and learned L5/DK/conservation state is intentionally not migrated (`:1-5`). It reads all domain rows from `centroid_checkpoints` and groups them by decision (`:174-193`), then creates `CentroidCheckpoint` nodes and `HAS_CENTROID_CHECKPOINT` edges (`:622-640`). It does **not** create `SNAPSHOT_AFTER` edges.

#### Backfill and depth

- Verified decisions are included by default; pending decisions require `all_decisions=True` (`sqlite_to_age.py:203-233`).
- Active/archive migration is supported by `include_archived` (`:239-245`, `:1014-1029`).
- Batches commit and publish a resumable migration checkpoint only after successful graph commit (`:1131-1165` and `:1165-1180`).
- The migration rejects a checkpoint without a unique identifier (`:623-626`). This is a material risk for legacy null-id rows.
- Current observed SQLite checkpoint depths are Trading=5, Purchasing=5, DataOps=219, S2P=0; these counts are from the prior read-only store scan. The script can preserve identifiable rows, but the 219-row DataOps history and null-id legacy rows are not proven migratable as-is.

#### Learned state and warm-start

Learned L5/DK/conservation state is expressly excluded and expected to be re-derived from the ordered decision log (`sqlite_to_age.py:1-5`). This means the migration does not preserve current learned centroids, DK weights, conservation state, or their warm-start lineage.

Warm-start metadata is written by `copilot-sdk/copilot_sdk/scoring/scorer.py:1514-1527` through the legacy centroid save path. The transfer router reads recent checkpoint rows and looks for warm-start metadata at `copilot-sdk/copilot_sdk/backend/transfer_router.py:181-203`. The migration copies checkpoint properties wholesale (`sqlite_to_age.py:622-633`), so metadata can survive only when the source checkpoint has a usable identifier. The null-id rejection creates a preservation gap.

The warm-start writer is not called unconditionally by scorer construction; it is part of the warm-start operation. Therefore the evidence does **not** establish “one new row on every restart.” It establishes row growth when warm-start is performed, while startup itself reads state.

#### Migration scripts

The repository contains executable migration/verification tooling:

- `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py`
- `copilot-sdk/copilot_sdk/migrate/verify_state.py`
- `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py`
- `copilot-sdk/copilot_sdk/migrate/scratch_graph.py`
- `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py`
- `copilot-sdk/copilot_sdk/migrate/__main__.py`

This confirms implementation exists, but the stated Program B scope is broader than the current state-preserving behavior: **GAP** for learned-state and legacy-checkpoint completeness.

### Warm-start + transfer risk

**Status: GAP.** Transfer depends on checkpoint metadata (`transfer_router.py:181-203`), while migration excludes learned state and rejects checkpoint rows lacking identifiers (`sqlite_to_age.py:1-5`, `:623-626`). A migration can therefore leave transfer unable to discover the source warm-start record even if the decision/outcome history itself migrated.

### Demo bundle

**Status: CONFIRMED SQLite-only.** `copilot-sdk/copilot_sdk/demo/bundle.py:1` describes restoring bundles into a cold SQLite graph store; `:58-69` requires direct SQLite access and reads SQLite checkpoint tables; `:145-155` commits SQLite state and warns that AGE migration is required for graph parity. It does not provide an AGE restore path. Under AGE, bundle restoration does not directly populate checkpoint nodes or lineage edges.

## Math-to-implementation gaps requiring conformance assertions

1. Assert whether a reported SOC drift value is per-update L2 or cumulative bootstrap drift; the current surfaces expose both semantics.
2. Assert rolling verified accuracy from the last 400 verified outcomes, rather than `verified_count / decisions_count`.
3. Assert IKS formula/version, because SOC drift-based IKS and shared SDK composite IKS are different.
4. Assert factor-schema identity before loading a checkpoint; `factor_names_hash` is currently metadata, not an enforced compatibility check.
5. Assert checkpoint lineage independently from numerical correctness: the math does not require `SNAPSHOT_AFTER`, but JM graph conformance may.
6. Assert migration preservation of identifiable checkpoint rows, warm-start metadata, and the explicit policy for null-id legacy rows.
7. Assert that L5/DK/conservation state is either migrated or intentionally rebuilt and verified before startup.

## Final verdict

- **V2:** CONFIRMED for Euclidean L2 update magnitude; **GAP** on one canonical drift semantic.
- **V3:** CONFIRMED; the numbered invariant inventory above is the conformance-suite basis.
- **V3b:** **GAP / not specified by the math**; no invariant requires `SNAPSHOT_AFTER` traversal.
- **V12:** **GAP**; checkpoint counts are insufficient to compute rolling accuracy.
- **V12b:** **GAP**; factor-version safety is specified conceptually but not enforced by hash validation.
- **V9:** **PARTIAL**; Program B migration/backfill tooling exists, but learned-state, null-id checkpoint, warm-start, and lineage preservation require explicit verification.

## Cleanup

No scripts, source files, graphs, or databases were modified. No scratch files were created.
