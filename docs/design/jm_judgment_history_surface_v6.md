# Judgment-History Surface — Context, Design & Execution Plan
### v6 · single consolidated document · supersedes design v5 + the separate findings doc

**Date:** 2026-08-06
**Purpose:** one self-contained document — the context (verified findings + review consensus), the design (executable change specs), and the execution plan — for building consistent, credible centroid-history across all 5 CI copilots.
**Basis:** my full source reads of `scorer.py` and `age_graph_store.py`; Codex's 6 verification scans (A+B, C+E, D+F) + 2 solution designs; 4 external LLM reviews (Grok, GPT, Opus, Gemini).

---

# PART A — CONTEXT

## A.1 The problem and the reframe
Centroid history is inconsistent across the 5 copilots. Trigger symptoms: SOC `/api/soc/centroid-evolution` empty/503, S2P 404, DataOps custom route timing out. Underneath sit **three different data models** for "centroid history" and an **AGE-vs-SQLite store split**. But the defect that actually matters for the business is **credibility, not consistency**: five identical endpoints showing unlabeled geometric drift are consistent and still don't prove the compounding moat. So this work delivers a consistent history surface **and** a quality axis that shows centroids *improve*, not merely move.

**Scope + stop line:** build the history surface + quality axis (P0–P2). **Stop at P2.** The fleet store migration, full `SNAPSHOT_AFTER` lineage traversal, and cross-artifact atomicity are **Program B** (`/areas/age-migration.md`), which this design hands three confirmed gap-fixes and one depth requirement.

## A.2 Provenance legend (so nothing load-bearing rests on inference)
- `[SRC]` — read at source this cycle; the actual behavior is quoted.
- `[RMAP]` — from Codex's scans/solutions with a cited file:line; **confirm in P-1** before editing.
- `[MATH]` — depends on `math_synopsis_v18` / `scan_df`; **confirm in P-1**.

## A.3 Verified architecture `[SRC]` (the facts the design stands on)
- **The loader hides learned centroids.** Current `age_graph_store.load_latest_centroids(domain)` filters `checkpoint_id IS NULL` and orders `created_at` at `../ci-platform/ci_platform/graph/age_graph_store.py:2661-2670`; learn writes **V2 non-null** checkpoints (`write_centroid_checkpoint`, id `f"{domain}:checkpoint:{uuid}"`) while warm-start writes **legacy null-id** rows (`save_centroids(category="warm_start")`). C1 adds canonical numeric `created_at_epoch` and selects the newest row regardless of ID; the warm-start method returns before blending when any non-warm row exists (`copilot_sdk/scoring/scorer.py:1514-1527`).
- **History default hides learned checkpoints too.** `get_centroid_checkpoints(domain, include_v2=False)` returns null-id only by default; `include_v2=True` returns all. `scorer.trajectory()` calls it without `include_v2` → sees only warm-start today.
- **`SNAPSHOT_AFTER` writer exists; no reader.** `write_centroid_checkpoint` → `_link_checkpoint_edges` idempotently creates `(d)-[:SNAPSHOT_AFTER]->(c)` and `(c)-[:DERIVED_FROM]->(d)`. Nothing traverses them; they're cleaned on domain reset.
- **Quality data is half-present.** Every V2 checkpoint stores `iks` = a 4-component quality composite `min(V/500,1)·25 + accuracy·25 + fingerprint·25 + coverage·25`. But rolling prediction accuracy `q=Σcorrect/N_v` over a window (the clean "it improved" signal) is **not** persisted — `verified_count/decisions_count` is a verification *rate*. The scorer already computes rolling quality (`_recent_quality(window)`); it just isn't written to the checkpoint.
- **Learning is non-atomic; but AGE has transactions.** `learn()` writes outcome→evidence→checkpoint→conservation→fingerprint as separate calls under an app lock, no DB transaction (`_l5_upsert_current` is documented non-atomic). But `append_evidence_receipt` uses `self._client.run_transaction(...)` with a `FOR UPDATE` lock → **the atomic primitive exists.**
- **Conservation math** (conformance basis): `theta_min = 23.53/(α·V)`; signal `= α·q·V`; **GREEN if signal ≥ theta_min else RED**; `α` = categories-with-≥1-verified / all categories; `q` = correct/verified; `V<10` → CALIBRATING; recent-100 `q<0.75` → RED pause.
- **Drift** = `centroid_delta = ‖centroids_after − before‖₂` (L2). AGE-canonical is already enforced at `from_preset(profile="production")` (rejects SQLite/InMemory). `get_iks_trajectory` already returns a time-ordered per-checkpoint iks series. `update_centroid` = S2P's L5 current-state write (not a checkpoint series). The `TransferPattern` writer already exists (`write_transfer_pattern`).

## A.4 Codex verification results (6 scans)
| V-item | Status | Finding |
|---|---|---|
| V1 restart/null-id | GAP | 229 null-id rows, warm-start actively writes them → **loader fix required (C1)** |
| V2 SOC drift | CONFIRMED | Euclidean L2; two "drift/IKS" semantics coexist |
| V3 invariants | CONFIRMED | 17 extracted; exactly 9 gaps: #6, #7, #9, #10, #11, #13, #15, #16, #17 |
| V3b SNAPSHOT_AFTER | NOT REQUIRED | math doesn't need it; JM lineage only → **defer (C4)** |
| V4 schema | CONFIRMED | AGE V2 creates edges; no reader |
| V5 atomic txn | GAP | app locks only, no DB txn |
| V6 outbox | CONFIRMED | outcome non-deferrable (fail-closed) |
| V7 DI-TIMELINE | CONFIRMED | panel uses the shared route; custom route has API/test callers and is deleted only after migration → **compatibility window (C2)** |
| V8 DataOps timeout | GAP | not the 219 rows (bounded query); external cause |
| V9 Program B | PARTIAL | 3 migration gaps → **handoff (Part D)** |
| V10 consumers | CONFIRMED | 34 total (10 checkpoint readers / 5 writers / 9 L5 / 4 delta / 6 FE) |
| V11 pool | CONFIRMED | `AGE_USE_POOL` off, max 5, no PgBouncer, ~80/100 under load |
| V12 quality | GAP | rolling accuracy not derivable from checkpoints → **C3** |
| V12b factors | GAP | `factor_names_hash` written, never validated → **C5** |
| V13 InMemory | CONTRADICTED | 4 history-method divergences from AGE/SQLite; L5 `update_centroid` remains intentionally separate |

## A.5 The 4/4 review consensus (the design spine)
Endorse P0–P2; **defer the fleet migration**; keep SQLite + a minimal InMemory unit fake (the "delete SQLite everywhere" idea is off); per-domain feature flags; PgBouncer + pool limits before AGE traffic; preserve the DI-TIMELINE demo; **add a quality axis (credibility > consistency)**; close the math-invariant list before building; do **not** route learn/outcome through the outbox (§12b fail-closed). Heavy machinery (event journal, full atomic txn, HA) belongs to the migration, not P0–P2.

## A.6 The three solution decisions
- **A — SNAPSHOT_AFTER:** defer. Writer exists; P2 adds only an edge-creation test; the traversal/reader/SQLite-parity go to Program B.
- **B — Quality axis:** add rolling-accuracy fields to new checkpoints at write time (`_recent_quality` already computes them); `quality:null` for legacy; never fabricate.
- **C — Program B migration gaps:** deterministic legacy IDs + loader precedence; learned-state snapshot + shadow replay; warm-start as first-class records.

---

# PART B — DESIGN (executable change specs)

### C1 — Loader precedence and warm-start safety (fixes V1/GAP1; the correctness fix that gates value)
- `[SRC]` **`age_graph_store.load_latest_centroids`**: remove `AND c.checkpoint_id IS NULL`, but do not order mixed timestamp representations directly. Add canonical numeric `created_at_epoch` at `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2620-2670`, then load the row with greatest `created_at_epoch`, regardless of null/non-null `checkpoint_id`.
- `[RMAP]` mirror in `sqlite_store.load_latest_centroids` and `memory_store.load_latest_centroids` at `copilot_sdk/graph/sqlite_store.py:2626-2637` and `memory_store.py:1370-1378`. Memory must merge legacy and V2 stores before selecting.
- **Warm-start guard:** at `copilot_sdk/scoring/scorer.py:1514-1527`, inspect `get_centroid_checkpoints(self._domain, limit=None, include_v2=True)` before mutating `self._scorer.mu`. If any row has `category != "warm_start"`, return before blending and before saving. `limit=None` is required so a newer stale warm-start cannot hide an older learned row. If no learned row exists, blend and save the warm-start row.
- **Test:** learn → new-scorer restart → assert loaded centroids equal the post-learn tensor; invoke warm-start and assert it neither mutates the live tensor nor writes a new warm-start row when a learned checkpoint exists.

### C2 — History endpoint shows learned checkpoints
- `[RMAP]` the shared `/api/self/centroid-history` handler must call `get_centroid_checkpoints(domain, include_v2=True, limit=N)`; wire SOC + S2P to it with back-compat aliases.
- `[RMAP]` **`models.py` `CentroidHistoryResponse`**: one envelope; per-checkpoint a nested `quality` object (C3), `quality:null` for legacy. S2P per-cell views may derive from the shared series; SOC's legacy drift route remains a separate Decision projection for compatibility.
- **SOC compatibility semantics:** keep `/api/soc/centroid-evolution` in `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171` as a projection of its existing Decision query at `:129-153`, reading `Decision.centroid_delta_norm`. P0 changes only the empty branch to HTTP 200 `[]`; it must not read checkpoint rows for drift. The canonical `/api/self/centroid-history` is mounted separately and reads `CentroidCheckpoint` rows.
- `[SRC]` migrate DataOps callers/tests from `/api/context/centroid-history` at `apps/dataops/backend/app/context_router.py:1037-1068`, `apps/dataops/frontend/src/api.ts:401-408`, and `apps/dataops/backend/tests/test_dataops_backend.py:817-848`; retain a compatibility response during migration, then delete only after a zero-caller search and visual snapshot of `CentroidTimelinePanel`.

### C3 — Quality axis and centroid ablation (the credibility half)
Add rolling-accuracy fields to **new** checkpoints; `quality:null` for legacy; never fabricate.
- `[SRC]` **`scorer._save_centroids_checkpoint`**: `_recent_quality(window=400)` → add `quality_window_size`, `quality_verified_count`, `quality_correct_count`, `rolling_accuracy` (correct/verified, null if N_v=0), `quality_window_end`, `quality_policy_version="quality.v1"`.
- `[SRC]` **`age_graph_store.write_centroid_checkpoint`**: add the 6 fields to `payload`, the Cypher `props`, and the `_get_centroid_checkpoint_payload` read.
- `[RMAP]` **`sqlite_store`** 6 nullable columns + migration; **`memory_store`** accept/return; **`protocol.py`** contract; **`models.py`** typed `quality` object.
- **Headline metric = `rolling_accuracy`** (invariant #13). `iks` stays a supporting composite. Read-time recompute from the outcome store is an audit fallback only (`source:"outcome_recompute"`).
- **Counterfactual framing:** this is a **centroid ablation**, not point-in-time replay. Checkpoints store centroids but not DK weights or temperature. Score the last N verified decisions with checkpoint *k*'s μ and with latest μ, holding current kernel weights W and temperature τ fixed. The honest claim is: "Rolling centroids back to checkpoint k (kernel and temperature held at today) would change action on X% of the last N verified decisions." The response must include `analysis_type: "centroid_ablation"` and `held_fixed: ["dk_weights", "temperature"]` as contract fields. See `docs/design/counterfactual_framing_design_v1.md`.
- **Helper:** add `CompoundingScorer.score_with_centroids(centroids, factors, category)` beside `score_read_only` at `copilot_sdk/scoring/scorer.py:404-427`. `ProfileScorer` accepts injected `mu` at `../graph-attention-engine-v50/gae/profile_scorer.py:156-170`; the helper must copy the live scorer's current W and τ, not rely on defaults. It must not mutate `self._scorer` or write the store.
- `[confirm in P-1]` Exact live ProfileScorer attribute names for DK weights and temperature, and the exact GraphStore method for verified decisions. If direct construction cannot preserve W/τ, compute `K=(f-μ)ᵀW(f-μ)` and `P=softmax(-K/τ)` directly with current values.

### C4 — SNAPSHOT_AFTER (defer)
- `[SRC]` writer + edges exist. **P2 adds one edge-creation test.** No SQLite equivalent, no traversal API — Program B.
- **Product tradeoff to decide:** deferring the reader means "which decision moved this centroid" lineage can't appear in the P2 UI. Acceptable if lineage isn't a P0–P2 demo beat — name it explicitly.

### C5 — Factor-hash validation (V12b / invariant #17; cheap)
- `[SRC]` `factor_names_hash` is written but never validated on read. Add read-time validation: compare stored hash to the current preset's; on mismatch, refuse stale-schema centroids (reset to bootstrap) and flag.

### C6 — Atomicity (scope decision)
- `[SRC]` the primitive (`run_transaction`) exists. **Full cross-artifact atomicity → Program B** (per the consensus). P2 commits to wrapping only the SOC outcome+checkpoint pair in one `run_transaction`; this is not optional. Never route learn/outcome through the outbox (§12b fail-closed).

---

# PART C — EXECUTION PLAN
Order: **P-1 → P0 → P1 → P2**, then STOP. Gates are hard; a failed gate stops the next phase.

### P-1 — Verify & freeze (1d, no product code)
- Confirm the `[RMAP]`/`[MATH]` items: SQLite/InMemory loader methods (C1); the shared-route handler file (C2); `models.py` `CentroidHistoryResponse` (C2/C3); `protocol.py`/`sqlite_store`/`memory_store` quality write points (C3); the InMemory 4 divergences (V13); **the IKS #14 second implementation** (`scan_df`/`math_synopsis`) to fix the quality-vs-drift naming.
- Confirm the exact verified-decision read method before implementing C3: `get_verified_decisions` may differ by adapter. Search `copilot_sdk/graph` for `def get_verified`, `def get_decisions`, and `def get_outcome`; tag the chosen protocol method `[confirm in P-1]`.
- Confirm ProfileScorer's live DK-weight and temperature attributes at `../graph-attention-engine-v50/gae/profile_scorer.py:156-239`; do not assume `_dk_weights` or `temperature` names until read.
- Freeze contracts: checkpoint schema incl. the 6 quality fields; the loader-precedence rule; warm-start early-return guard; `CentroidHistoryResponse` (incl. `quality` object, `quality:null` legacy, provenance); SOC Decision drift formula; counterfactual `analysis_type` and `held_fixed` fields.
- **Gate:** no `[RMAP]` item contradicted; IKS naming, verified-decision method, and live W/τ attributes resolved.

### P0 — Fix all broken surfaces (1–2d, independent)
- SOC 503→empty-state contract; S2P 404→route wired to the shared handler; DataOps timeout → confirm not reproducible (bounded query; no code fix owed unless it recurs); a 5-copilot smoke matrix (empty/disabled/frozen/populated).
- **Deliverable:** all 5 return 200 with the empty-state contract. **Gate:** smoke green, no 503/404/timeout. **Rollback:** per-surface.

### P1 — Foundation on current stores (3–4d)
- **C1 loader fix** (all 3 stores) + restart test; **C2** shared handler + `CentroidHistoryResponse` reading `include_v2=True`, wire SOC+S2P; **permanent conformance suite** over AGE/SQLite/InMemory asserting **surface invariants #12, #13, #14, #17** + restart/idempotency; make InMemory conformant (V13); **PgBouncer + pool limits** benchmarked under concurrent load (`AGE_USE_POOL` on); domain feature flags at the factory seam + a thin **read/write-splitting wrapper** for `JM_READ_STORE`/`JM_WRITE_STORE` (scorer holds one `_graph_store`).
- **Deliverable:** one endpoint + shape live on all 5 over current stores; conformance green on 3 stores; pool gate passed; flags in place. **Gate:** conformance green; pool benchmark passes; 5-copilot regression green. **Rollback:** flags revert reads to the prior handler.

### P2 — Model + quality axis (1wk)
- **C3 quality axis** (6 fields across the write path + response `quality` object + centroid-ablation endpoint with explicit `analysis_type`/`held_fixed` + `source` provenance + tests); **SOC checkpoint writer** (SOC has none) writing null-id-compatible rows the fixed loader + history both see, while SOC drift remains the Decision projection at `framework_router.py:129-153`; **C4** SNAPSHOT_AFTER edge-creation test; **C5** factor-hash validation; delete the DataOps custom route behind a visual-snapshot and zero-caller gate; one canonical frontend model + shared client + presentation adapters; JM v2.8 writeback + dedupe the two authority copies.
- **Deliverable:** all 5 on one model/shape; rolling-accuracy quality axis + honest centroid-ablation analysis live; DI-TIMELINE visually unchanged. **Gate:** quality metric + ablation identity/flip tests correct on seeded verified decisions; visual snapshot matches; 5-copilot regression green. **Rollback:** quality fields are additive/nullable; SOC writer behind a flag.

### STOP
Surface + quality complete. No migration, no SQLite deletion, no fleet cutover.

---

# PART D — HANDOFF TO PROGRAM B (`/areas/age-migration.md`)
- **GAP1 (null-id preservation):** migration generates deterministic `legacy_{domain}_{id}` ids + `legacy_source_id`; dedicated import path for unassociated warm-start rows. The **loader precedence** shipped in C1 is the rule Program B needs.
- **GAP2 (learned-state replay):** snapshot L5/DK/conservation + shadow-replay verified decisions (`verify_state.replay_decisions`, `migrate/shadow_scorer.py`); counts ~255/500/417.
- **GAP3 (warm-start as first-class records):** preserve `category="warm_start"` + metadata; no Decision node required; transfer router keeps finding them.
- **Depth requirement:** history must survive migration with depth preserved — backfill existing checkpoints; the parity gate asserts row-count + earliest sequence, not only new-write equivalence. **SNAPSHOT_AFTER traversal/backfill + full cross-artifact atomicity land here too.**

# PART E — CONFORMANCE SCOPE (surface only)
Assert **#12** conservation (`α·q·V≥θ_min`, `theta_min=23.53/(α·V)`), **#13** rolling accuracy (`q=Σcorrect/N_v` over 400 — enabled by C3), **#14** drift/quality after the naming reconciliation, **#17/#12b** factor-version via C5. Hand the GAE-internal gaps (#6, 7, 9, 10, 11, 15, 16) to the GAE/math conformance effort — they do **not** block P0–P2.

# PART F — OPEN RECONCILIATIONS (close in P-1)
1. **IKS #14 quality-vs-drift naming** — the stored value is a quality composite; the math name is drift. Pick canonical names before any UI label. `[MATH]`
2. **`[RMAP]` line cites** — `sqlite_store`, `memory_store`, `protocol.py`, `models.py`, the route handler, `verify_state`/`shadow_scorer` — confirm before editing.
3. **Invariant-gap count** — resolved: 9 total; #13 and #17 are P0–P2, #6, #7, #9, #10, #11, #15, #16 are deferred.
4. **SNAPSHOT_AFTER reader deferral** — resolved: writer/edge creation is P2; traversal, SQLite parity, and lineage UI are Program B.
5. **Counterfactual data honesty** — resolved by `docs/design/counterfactual_framing_design_v1.md`: centroid ablation only; current W/τ held fixed; no point-in-time replay claim.

## PART G — CORRECTION LOCKS

1. `warm_start()` must return before blending or saving when any non-warm checkpoint exists. The query is `limit=None, include_v2=True` at `copilot_sdk/scoring/scorer.py:1514-1527`.
2. SOC's legacy alias continues reading `Decision.centroid_delta_norm` through the existing query at `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:129-153`; only its empty response changes from 503 to 200 `[]`.
3. Counterfactual responses must contain `analysis_type="centroid_ablation"` and `held_fixed=["dk_weights","temperature"]`; the current W/τ attribute names and verified-decision method are `[confirm in P-1]`.
