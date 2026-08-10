# C-REGIME P4 — Verified Findings and Execution Plan

**Date:** 2026-08-10  
**Scope:** Diagnostic verification and implementation planning only. No
implementation changes were made by this review.

This document resolves the open verify-first gates from
`c_regime_p4_design_review_memo_v1.md`. The governing JM constraints remain
AGE-backed GraphStore writes, domain scoping, verified-only conservation V,
and the honesty gate: TRD-S7 remains ARCH until the experiment measures a
regime re-convergence ratio greater than one on the ground-truth-distance
basis.

## 1. Gate Resolutions

| Gate | Finding | Status | Evidence |
|---|---|---|---|
| G1 / V1 — regime detector | The production Trading path uses `ci_trading.quant.integrations.classify_regime()` through `app.factors.market_regime.classify_regime_context()` and `app.services.regime_scoring.build_regime_context()`. It is not `situation_analyzer.py`. | **CLOSED WITH CORRECTION** | `copilot-sdk/ci_trading/quant/integrations.py:33-50`; `copilot-sdk/apps/trading/backend/app/factors/market_regime.py:31-45`; `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:121-138` |
| V1 — label set | The classifier's headline regime set is `trending`, `ranging`, `volatile`. `calm` and `elevated` are `vol_state` values; Hurst also exposes `trending`, `mean_reverting`, `random_walk`, or `unknown` as a sublabel. The four-label `trending/choppy/volatile/calm` set is synthetic preseed vocabulary, not the production headline output. | **CONFIRMED CORRECTION** | `copilot-sdk/ci_trading/quant/integrations.py:45-50`; `copilot-sdk/ci_trading/quant/integrations.py:52-69`; `copilot-sdk/ci_trading/quant/regime.py:115-124`; `copilot-sdk/scripts/preseed_all_copilots.py:307-320` |
| V1 — decision metadata | Runtime Trading scoring tags `regime_metadata` before calling the scorer, and the active AGE writer persists the supplied metadata dictionary. | **CONFIRMED** | `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:61-70`; `copilot-sdk/apps/trading/backend/app/graph_status.py:246-306` |
| V1 — preseed tags | The preseed script annotates in-memory seed rows, but its `/api/score` body sends only seed identity context and factors; it does not send the annotated regime fields. The later metadata call is separate. Preseed-to-Decision regime tagging is therefore not proven. | **GAP** | `copilot-sdk/scripts/preseed_all_copilots.py:307-322`; `copilot-sdk/scripts/preseed_all_copilots.py:387-404`; `copilot-sdk/scripts/preseed_all_copilots.py:429-433` |
| G2 / V2 — DK and temperature persistence | Current V2 checkpoint payload metadata includes `dk_weights` and `temperature`; the existing checkpoint contract accepts metadata. Option C is therefore feasible for new checkpoints. | **CLOSED** | `copilot-sdk/copilot_sdk/scoring/scorer.py:2067-2075`; `ci-platform/ci_platform/graph/age_graph_store.py:1516-1536` |
| V3 — loader selection | JM authority records epoch-based checkpoint loading as shipped. The regime loader must call that corrected path rather than introduce a timestamp-only reader. | **CLOSED** | `copilot-sdk/docs/design/judgment_memory_v2_9.md:108-115`; `copilot-sdk/docs/design/judgment_memory_v2_9.md:152-154` |
| V4 — SNAPSHOT_AFTER reader | JM authority records B5 traversal/backfill and lineage endpoints as live. C-REGIME must reuse the shared lineage reader. | **CLOSED** | `copilot-sdk/docs/design/judgment_memory_v2_9.md:123-127`; `copilot-sdk/copilot_sdk/graph/protocol.py:104-114` |
| V5 — conservation reset | Conservation can report `CALIBRATING` during low evidence, but there is no explicit regime-reset API and no discounted-V overlay. Current V is read from GraphStore verified counts. | **OPEN GAP** | `copilot-sdk/copilot_sdk/scoring/scorer.py:1319-1355`; `copilot-sdk/copilot_sdk/scoring/scorer.py:719-728`; `copilot-sdk/copilot_sdk/backend/conservation_utils.py:275-297` |
| V6 — per-regime depth | The live Trading endpoint returned 20 checkpoints for `limit=20`, with 0 carrying `regime_tag`/`regime`. A `limit=50` request timed out, so total depth is not established; usable per-regime depth is zero. | **PARTIAL / DEMO BLOCKED** | Live `GET http://127.0.0.1:8010/api/self/centroid-history?limit=20`; checkpoint metadata currently has no `regime_tag` field in `copilot-sdk/copilot_sdk/scoring/scorer.py:2116-2129` |
| V7 — atomic re-init substrate | `AGEGraphStore.run_transaction()` delegates one operation to the AGE client's transaction path. It is available for the centroid swap, model-state application, and conservation-reset record. | **CLOSED** | `ci-platform/ci_platform/graph/age_graph_store.py:585-592` |

### G1 conclusion

The exact detector seam is:

`ci_trading.quant.integrations.classify_regime()` →
`apps/trading/backend/app/factors/market_regime.py:31-45` →
`apps/trading/backend/app/services/regime_scoring.py:121-138`.

The implementation plan must use the three canonical headline labels
`trending`, `ranging`, and `volatile`. It must not silently promote the
four synthetic preseed labels into production regime semantics.

## 2. Corrected Premises

| Original premise | Corrected premise | Evidence |
|---|---|---|
| `situation_analyzer.py` is the market-regime detector. | The market-regime detector is the Trading quant classifier. `situation_analyzer.py` consumes explicit tags or deterministic demo fallbacks and is not the authoritative Hurst/VIX classifier. | `copilot-sdk/ci_trading/quant/integrations.py:33-50`; `copilot-sdk/apps/trading/backend/app/services/situation_analyzer.py:13-21`; `copilot-sdk/apps/trading/backend/app/services/situation_analyzer.py:127-154` |
| There are four production labels: trending, choppy, volatile, calm. | The production headline labels are trending, ranging, and volatile. Calm/elevated belong to `vol_state`; choppy/calm in preseed are synthetic aliases that require an explicit mapping or must be removed from the experiment. | `copilot-sdk/ci_trading/quant/integrations.py:78-91`; `copilot-sdk/ci_trading/quant/regime.py:115-124`; `copilot-sdk/scripts/preseed_all_copilots.py:309-319` |
| Preseed decisions already carry regime tags. | Preseed rows are annotated, but the score request omits those fields. The production score path can persist tags when supplied; the preseed path needs to pass them through before it can seed regime-tagged Decisions. | `copilot-sdk/scripts/preseed_all_copilots.py:307-322`; `copilot-sdk/scripts/preseed_all_copilots.py:395-404`; `copilot-sdk/apps/trading/backend/app/graph_status.py:258-306` |
| Checkpoint metadata needs a schema migration for `regime_tag`. | V2 checkpoint metadata is a dictionary and already carries DK weights and temperature. `regime_tag` can be an additive metadata key, subject to adapter parity tests. | `copilot-sdk/copilot_sdk/scoring/scorer.py:2067-2075`; `ci-platform/ci_platform/graph/age_graph_store.py:1528-1536` |
| Option C was only a speculative strategy. | Option C is buildable for new checkpoints because DK weights and temperature are persisted in checkpoint metadata. Legacy checkpoints without those keys must fall back to A or B and be labeled accordingly. | `copilot-sdk/copilot_sdk/scoring/scorer.py:2069-2074`; `copilot-sdk/docs/design/judgment_memory_v2_9.md:1292-1296` |
| The demo has enough per-regime checkpoint depth. | No usable regime-tagged checkpoints were observed: 20 returned Trading checkpoints had zero regime tags, and the larger history request timed out. Depth must be created and measured before the demo is called meaningful. | Live Trading history check; `copilot-sdk/copilot_sdk/scoring/scorer.py:2116-2129` |
| A conservation reset means changing or deleting historical V. | V remains the GraphStore count of verified decisions. Re-initialization needs a domain/regime-scoped calibration overlay with an effective evidence value; it must not mutate or delete historical Decisions. | `copilot-sdk/copilot_sdk/backend/conservation_utils.py:261-297`; `copilot-sdk/docs/design/judgment_memory_v2_9.md:142-145` |

## 3. Updated Design Decisions

### D1 — Granularity and labels

Use a fixed three-label production regime vocabulary for P4:

1. `trending`
2. `ranging`
3. `volatile`

Persist `vol_state` and Hurst sublabels as explanatory metadata, not as a
second regime taxonomy. If the product requires a four-arm visual, the fourth
arm must be an explicitly labeled `unknown`/insufficient-evidence state; it
must not be called `calm` unless the quant classifier is changed and verified.

Evidence: `ci_trading/quant/integrations.py:45-50` documents the compatible
three-way headline contract; `ci_trading/quant/integrations.py:52-69` shows
the separate volatility states.

### D2 — Tagging

Use additive `regime_tag` metadata on Decisions and V2 CentroidCheckpoints.
No graph schema migration is required because the checkpoint and decision
writers already accept metadata dictionaries. The tag must be copied from the
same classifier result that produced `regime_metadata`; it must not be
recomputed later from a different data source.

Evidence: `regime_scoring.py:61-70` constructs runtime metadata;
`graph_status.py:258-306` forwards decision metadata; `scorer.py:2116-2129`
constructs checkpoint metadata.

### D3 — Re-initialization strategy

Implement and measure all three strategies behind one experiment interface:

- **A — centroid restore:** load the newest valid checkpoint for the target
  regime and replace the active centroid tensor.
- **B — centroid blend:** blend the current tensor with the target-regime
  checkpoint using a declared, logged blend weight.
- **C — model-state restore:** restore the target checkpoint's centroids plus
  its persisted DK weights and temperature.

Option C is buildable for new V2 checkpoints. A legacy checkpoint lacking DK
or temperature must not be treated as a valid C candidate; it falls back to A
or B and reports the fallback in the experiment result. Strategy selection is
an EXP-REGIME result, not a design intuition.

Evidence: `scorer.py:2067-2075` persists DK and temperature; the V2 writer
accepts metadata at `age_graph_store.py:1516-1536`.

### D4 — Measurement

Reuse APP-1's generator and oracle separation. The generator already supports
controlled disruption decisions, categories, and magnitude, but it does not
emit regime labels. Add regime-break sequencing in the experiment harness,
not in the production generator. Measure:

`gamma_regime = cold_start_convergence_time /
regime_indexed_convergence_time`.

Convergence time is the first post-break point meeting the predeclared
ground-truth-distance threshold. Do not use canonical distance as the proof
metric. Do not conflate this gamma with any epsilon-firm or other
re-convergence quantity.

Evidence: `examples/jm_reference/generator.py:19-28` exposes disruption
configuration; `examples/jm_reference/generator.py:51-72` applies the
disruption; `docs/design/judgment_memory_v2_9.md:1277-1296` distinguishes
centroid ablation from point-in-time model replay.

### D5 — Conservation reset

Build an explicit, domain-scoped calibration overlay. It must contain:

- `phase = CALIBRATING`;
- `regime_tag` and reset timestamp;
- actual GraphStore `V` (unchanged historical count);
- effective calibration evidence used by the gate;
- a conservative discount policy, initially `effective_prior_V =
  floor(discount * prior_regime_V)` with the discount tuned by EXP-REGIME;
- new-regime verified count and the rule for leaving CALIBRATING.

The status payload should expose actual V and effective V separately. The
overlay must not rewrite the authoritative verified-only count, delete
historical decisions, or let a discounted value promote a variant before the
new regime has enough verified evidence. The existing `CALIBRATING` branch is
only an automatic low-volume status calculation; it is not a reset seam.

Evidence: `scorer.py:1340-1355` computes CALIBRATING only from current count;
`conservation_utils.py:275-297` reads V from the store; the only reset-like
scorer method, `scorer.py:719-728`, performs a destructive domain reset.

## 4. Implementation Readiness

| Prerequisite | Available? | Evidence / consequence |
|---|---:|---|
| Authoritative regime classifier | Yes | `ci_trading/quant/integrations.py:33-91` |
| Canonical label decision | Yes, corrected to 3 labels | `ci_trading/quant/integrations.py:78-91` |
| Runtime Decision metadata seam | Yes | `regime_scoring.py:61-70`; `graph_status.py:287-306` |
| Checkpoint metadata seam | Yes | `scorer.py:2067-2075`; `age_graph_store.py:1528-1536` |
| DK/temperature persistence for new V2 checkpoints | Yes | `scorer.py:2069-2074` |
| Epoch-based base loader / shared lineage substrate | Yes, per closed JM gates | `judgment_memory_v2_9.md:108-127` |
| Atomic transaction substrate | Yes | `age_graph_store.py:585-592` |
| Explicit calibration reset with discounted effective V | **No** | Build overlay; do not use destructive `domain_scoped_reset` |
| Regime-tagged preseed Decisions | **No / unproven** | Preseed annotation is not included in score body: `preseed_all_copilots.py:307-322`, `:395-404` |
| ≥3 checkpoints per canonical regime | **No** | Live sample: 20 Trading checkpoints, 0 tagged; full count request timed out |
| APP-1 controlled disruption | Yes, regime tagging extension needed | `generator.py:19-28`, `:58-72` |

Readiness verdict: the shared substrate is ready, but implementation must not
start until the label mapping, preseed transport, and calibration-overlay
contract are frozen. The demo acceptance gate is blocked by V6 until at least
three valid checkpoints exist for each selected regime.

## 5. Execution Plan

### Phase 0 — Prerequisites and contract freeze

**Files to inspect/update in the implementation phase:**

- `copilot-sdk/ci_trading/quant/integrations.py:33-91` — treat the existing
  classifier output as the source contract.
- `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:121-138` —
  define the single tag-generation seam.
- `copilot-sdk/copilot_sdk/backend/conservation_utils.py:61-140` — define the
  actual/effective conservation payload contract.
- `copilot-sdk/copilot_sdk/graph/protocol.py:96-114,279-295` — extend the
  checkpoint read/write contract additively if required.

**Acceptance gate:** written contract names exactly three headline regimes,
defines legacy-checkpoint fallback, and distinguishes actual V from effective
calibration evidence. No implementation begins while `choppy` and `calm`
remain ambiguous.

### Day 1 — Schema metadata, Decision tagging, and preseed

**Files:**

- `copilot-sdk/copilot_sdk/scoring/scorer.py:2049-2129` — carry
  `regime_tag` into checkpoint metadata without changing centroid math.
- `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:49-70` —
  pass the canonical tag through the score metadata.
- `copilot-sdk/apps/trading/backend/app/graph_status.py:246-306` — preserve
  the tag in the active AGE Decision write.
- `copilot-sdk/scripts/preseed_all_copilots.py:292-322,387-433` — send the
  canonical regime metadata in the score request and retain it in verification
  metadata.
- `ci-platform/ci_platform/graph/age_graph_store.py:1516-1560` — verify AGE
  serialization and read-back of the additive metadata key.

**Tests:** real SQLite protocol parity for metadata shape; AGE integration
test for one Trading Decision and checkpoint; preseed dry-run and live-read
assertions. Do not use scorer/store mocks under the SDK standing rules.

**Acceptance gate:** every newly seeded Trading Decision and checkpoint has
`regime_tag` in the canonical three-label set, and the raw AGE read-back
matches the classifier output.

### Day 2 — Regime-indexed retrieval, re-initialization, and calibration

**Files:**

- `copilot-sdk/copilot_sdk/graph/protocol.py:93-114,279-295` — add the
  regime-filtered checkpoint contract.
- `ci-platform/ci_platform/graph/age_graph_store.py:585-592` and the existing
  checkpoint readers — implement domain-scoped, epoch-ordered regime lookup
  using the shared lineage/loader behavior.
- `copilot-sdk/copilot_sdk/scoring/scorer.py:719-728,1319-1355` — add the
  non-destructive calibration overlay and A/B/C re-init seam.
- `copilot-sdk/copilot_sdk/backend/conservation_utils.py:61-140,261-297` —
  calculate and expose actual V, effective V, phase, and reset reason.

**Atomicity:** the re-init operation must run through
`AGEGraphStore.run_transaction()` and record the checkpoint selection,
centroid/model-state application, and calibration-state transition together.

**Tests:** regime-filtered latest selection; no cross-domain results; A/B/C
  state changes; missing DK/temperature fallback; rollback on failed reset;
  CALIBRATING status; actual V unchanged; effective V conservative; promotion
  blocked during calibration.

**Acceptance gate:** a failed re-init leaves the prior scorer state and
  calibration state intact; a successful re-init is auditable and cannot
  silently promote while CALIBRATING.

### Day 3 — TRD-S7 frontend surface

**Files:**

- `copilot-sdk/apps/trading/frontend/src/components/CentroidTimeline.tsx:1-52`
  or `CentroidTimelineChart.tsx:1-34` — reuse the existing checkpoint
  timeline surface.
- `copilot-sdk/apps/trading/frontend/src/screens/PerformanceScreen.tsx` and
  `AnalysisScreen.tsx` — mount the new regime re-convergence panel in the
  selected screen.
- `copilot-sdk/apps/trading/frontend/src/api.ts` and `types.ts` — add typed
  calls for regime history and experiment results.

**Tests:** stable `data-testid` root; cold-start and regime-indexed lines both
  render; selected regime and evidence depth are visible; insufficient-depth
  state is explicit; no K1/K2 oracle values are surfaced.

**Acceptance gate:** the UI labels the result as an experiment, shows evidence
  depth, and does not call TRD-S7 LIVE merely because a curve is rendered.

### Days 4–5 — EXP-REGIME A/B/C bake-off

**Files:**

- `copilot-sdk/examples/jm_reference/generator.py:19-72` — extend the
  harness configuration for regime sequences while preserving oracle
  separation.
- `copilot-sdk/examples/jm_reference/oracle.py` and the new experiment module
  under `copilot-sdk/apps/` — run identical decision streams for cold start,
  A, B, and C.
- New report/test artifacts under `copilot-sdk/apps/` and `copilot-sdk/tests/`
  — record ground-truth distance, convergence time, effective evidence,
  fallback reason, and gamma.

**Experiment controls:** same seed, same oracle, same regime break schedule,
same number of verified outcomes, predeclared convergence threshold, and at
least three tagged checkpoints per regime. Legacy checkpoints must be excluded
from Option C claims.

**Acceptance gate:** report `gamma_regime` for all three strategies on the
  ground-truth-distance basis. TRD-S7 can move from ARCH to NEAR only if the
  winning strategy has `gamma_regime > 1` with sufficient per-regime evidence
  and no conservation safety violation.

## 6. Codex Prompt Grouping

1. **Prompt 1 — contract, tagging, and preseed.** Depends on Phase 0. Touches
   Trading metadata paths, scorer checkpoint metadata, AGE serialization, and
   preseed. Must finish the three-label decision and produce tagged data.
2. **Prompt 2 — retrieval, A/B/C re-init, and conservation overlay.** Depends
   on Prompt 1 and the already-closed loader/lineage/transaction gates. This is
   the highest-risk prompt and must land before the experiment.
3. **Prompt 3 — TRD-S7 frontend.** Can run in parallel with Prompt 2 after the
   response schema is frozen. It must remain a labeled ARCH/experiment surface.
4. **Prompt 4 — EXP-REGIME bake-off and final report.** Depends on Prompts 1–2
   and at least three tagged checkpoints per selected regime. It can consume
   the frontend contract from Prompt 3 but does not depend on frontend
   completion to measure gamma.

## 7. Risk Register

| Risk | Mitigation |
|---|---|
| Synthetic four-label vocabulary is mistaken for production truth. | Freeze the three-label quant contract; display `vol_state` and Hurst sublabels separately. |
| Preseed rows are annotated but Decision metadata is missing. | Add the regime object to the score request and assert raw Decision read-back before generating checkpoints. |
| Zero regime-tagged checkpoints make re-init a no-op. | Block the demo; seed at least three checkpoints per canonical regime and verify their metadata. |
| `limit=50` history times out under the live backend. | Measure with bounded per-regime queries after indexing/tagging; record timeout as an operational gap, not as evidence of depth. |
| Legacy checkpoints lack DK/temperature. | Permit A/B fallback only; label the checkpoint non-replayable for C. |
| Discounted V accidentally rewrites authoritative conservation history. | Keep actual GraphStore V immutable; use an explicit effective-V calibration overlay with audit fields. |
| Re-init partially applies centroids or calibration. | Put model-state swap and calibration transition in one AGE transaction and test rollback. |
| Regime loader selects the wrong checkpoint. | Reuse epoch-based selection and domain/regime predicates; add reversed-insertion-order tests. |
| A visually persuasive curve is mistaken for proof. | Require predeclared GT-distance threshold, gamma calculation, evidence-depth disclosure, and ARCH label until gamma > 1. |

## 8. Honesty Gate

- TRD-S7 remains **ARCH** until EXP-REGIME measures `gamma_regime > 1`.
- `gamma_regime` must be measured using decreasing distance to oracle ground
  truth, not distance to the canonical prior.
- `gamma_regime` is not `epsilon_firm` re-convergence gamma; they are distinct
  quantities with separate names, thresholds, and reports.
- The demo must disclose the number of regime-tagged checkpoints and the
  number of verified outcomes per regime.
- No `calm`, `choppy`, or other synthetic label may be presented as a
  production detector output without a separately verified classifier change.
- Missing or legacy DK/temperature metadata cannot support a point-in-time
  replay claim. The honest fallback is centroid restore/ablation with its
  limitations stated.

