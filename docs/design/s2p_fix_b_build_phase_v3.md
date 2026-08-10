# S2P FIX-B — Build Phase Plan & Prompts v3 (STEP 0 resolved; build→D)

**Date:** 2026-08-05
**Supersedes:** v2 (STEP 0 persistence scan is DONE — Commit 3 now has the concrete `save_centroids` mechanism + guards folded in; V2 writer ruled out). Self-contained build→D. File in `copilot-sdk/docs/design/`.
**Where we are:** every ladder unknown closed by spikes (S3 factors, G2 calibration, Phase B read) + STEP 0 persistence scan done. **Nothing is built.** NEXT ACTION: **Commit 1**. Phase is BUILD + VALIDATE.
**Rules:** IMPLEMENT commits are S2P-scoped, committed, with tests; never write live `soc_graph`; verify each commit on a disposable `protocol_v2_test_s2p_active_*` graph; AGE DSN `172.22.74.149:5433` (fallback `localhost:5433`).

## The fixes needed (what actually gets implemented)
1. **Track 1 seed writer** — seed the S2P entity subgraph with the full property-completeness contract + stamps + index + orphan reconcile; move the decision→invoice link off the response path.
2. **Track 2 reader** — `query_direct_context` + `query_duplicate_context` + `_resolve_graph_context` accepting normalized rows (shared `query_context` untouched).
3. **The 2 real factors** — `RealMatchStatus` + `RealTaxRegulatoryCompliance` (S3 formulas) with explicit provenance.
4. **Calibration** — persist the re-seeded `(5,5,8)` tensor as the latest S2P checkpoint, load via `load_latest_centroids("s2p")`, log checkpoint identity, use the ACTIVE gate.

## Sequence
STEP 0 scan ✅ DONE → **Commit 1 (Track 1 seed) ← NEXT** → Commit 2 (Track 2 + real factors) → Commit 3 (calibration persist) → **F** → **B2** → **C** → migrate → **D**. Each commit has a verify gate; a failed gate stops before the next.

---

## STEP 0 — SCAN: centroid persistence API — ✅ DONE (`s2p_step0_persistence_scan_v1.md`)
FINDING: persist the re-seed via **`save_centroids(domain="s2p", category="g2_reseed", centroids, metadata)`** — the legacy wholesale writer, which creates a `CentroidCheckpoint` with **no `checkpoint_id`**, so `load_latest_centroids("s2p")` selects it (that loader filters `checkpoint_id IS NULL`, newest `created_at`, domain-scoped). **Do NOT use `write_centroid_checkpoint` (V2)** — its non-null `checkpoint_id` makes it INVISIBLE to the startup loader, silently leaving startup on the bootstrap tensor. No new store method needed. Precedence (scorer.py:266-268): checkpoint > bootstrap, with **no factor-name/shape/hash validation** in that branch → Commit 3 must add the guard. Active gate confirmed = `_should_auto_approve` in `s2p-copilot/backend/app/domains/s2p/auto_approve.py` (called `s2p.py:2005-2010`), thresholds hardcoded — NOT the P40B shadow gate. Folded into Commit 3 below.

## COMMIT 1 — Track 1 seed writer
```
TASK: IMPLEMENT the hardened Track-1 S2P seed/migration writer (S2P-scoped, committed, tests). Never write live soc_graph; unit-test on a disposable graph.
BUILD: a hardened wrapper over app/seed_graph.py:seed_s2p_graph() that per invoice creates Invoice/PurchaseOrder/GoodsReceipt/Supplier/Commodity/Contract with the FULL property-completeness contract:
  Invoice.amount/quantity/payment_days (numeric); PurchaseOrder.amount/quantity (numeric); GoodsReceipt.qty_received/amount (numeric); Supplier.exception_rate (numeric[0,1])/payment_terms (parseable string); Commodity.volatility (numeric[0,1]); Contract.max_amount (numeric)/tax_compliant (boolean-like)/regulatory_status (enum string).
  NOTE: the committed seed creates only Contract identity/linkage → ADD max_amount/tax_compliant/regulatory_status + the numeric fields above.
  Stamp every node domain='s2p'/provenance='seed'/domain_source='migration'/entity_id=natural key. NON-force (natural-key CREATE-if-absent, idempotent). Create the Invoice.invoice_id AGE index (CREATE INDEX ... agtype_access_operator(... '"invoice_id"' ...)). Orphan reconciliation for the 84 DecisionEntityLink. Move _link_decision_to_invoice off the response path → _SIDE_EFFECT_EXECUTOR.
TESTS: idempotency (2nd run 0 new); every node stamped; every contract property present + correctly typed.
INCLUDE the S3 sample invoices (e.g. S2P-INV-0003 with the S3 property values) in the seed set, so Commit 2's integration check has a known target vector.
VERIFY: seed a disposable graph; confirm every property in the contract is present and numeric where required (no missing / mis-typed).
NOTE: this commit BUILDS + unit-tests the migration writer only. Running it against live soc_graph is the separate "migrate" step below, AFTER Phase C passes — do NOT run it against soc_graph here.
```

## COMMIT 2 — Track 2 reader + the 2 real factors
```
TASK: IMPLEMENT Track-2 reader/normalization + the 2 real factors (S2P-scoped, committed, tests). Shared AGEGraphStore.query_context UNCHANGED.
BUILD:
  - S2PGraphReader.query_direct_context(invoice_id, limit=100): directed MATCH (e:Invoice {invoice_id})-[]->(n) WHERE n.domain='s2p' RETURN n LIMIT 100; normalize AGE vertices via properties(n) → {"node":{props}}.
  - S2PGraphReader.query_duplicate_context(invoice_id, supplier_id, amount, limit=20).
  - _resolve_graph_context (s2p.py:138-161): call the above + accept the normalized rows.
  - RealMatchStatus (replace factors.py:141-159): 1 - min(max normalized discrepancy) over Invoice/PO/GR amount+qty pairs; provenance computed/no_match_data/partial_data. Exact formula = s2p_s3_path_a_spike_results_v1.md Step 0.
  - RealTaxRegulatoryCompliance (replace :289-302): checks_passed/checks_total over Contract max_amount(invoice<=)/tax_compliant/regulatory_status; provenance computed/no_contract/no_compliance_fields.
  - Numeric-coercion contract (DataOps _safe_get_float pattern).
  - The other 5 factors (amount_variance, duplicate, supplier_exception, payment_terms, commodity) are UNCHANGED. Note: once Commit 1 seeds Invoice.payment_days, payment_terms stops silently defaulting and computes for real (the audit's silent-default fix); duplicate needs siblings in context (exercised in Phase F).
TESTS: direct-context normalization; Decision-hub exclusion; bounded duplicate; per-factor perturbation (RealMatch moves on PO.amount; RealTax on tax_compliant).
VERIFY (INTEGRATION — the REAL score path, not scratch): on a Commit-1-seeded disposable graph, run the active score path (score_read_only or /api/s2p/score) for the perfect invoice → confirm the 8-factor vector matches S3 ([1,0,0,.033,0,.35,1,.5]) and perturbing PO.amount / tax_compliant moves the corresponding factor. This proves the pieces compose in production code, not just in the spike.
```

## COMMIT 3 — Calibration persistence (STEP 0 resolved: use `save_centroids`)
```
TASK: IMPLEMENT persistence of the re-seeded (5,5,8) S2P calibration tensor (S2P-scoped, committed, tests).
MECHANISM (from STEP 0): graph_store.save_centroids(domain="s2p", category="g2_reseed", centroids=<(5,5,8) np.ndarray>, metadata=<manifest>) — legacy wholesale writer, no checkpoint_id → load_latest_centroids("s2p") selects it. Do NOT use write_centroid_checkpoint (V2): its non-null checkpoint_id is invisible to the loader → would silently leave startup on the bootstrap. No new store method needed.
BUILD:
  1. Build the corpus (NOT from synthetic_invoices.json ground_truth_action): ANCHOR the auto_approve (perfect+compliant) exemplar to a REAL-factor vector (seed the S3 perfect invoice, run the Commit-2 real factors, confirm [1,0,0,.033,0,.35,1,.5]); for the other 24 cells use the G2 Step-2 domain-authored vectors (validate each achievable: [0,1], right shape). Use the real S2PPreset.shape category/action/factor names (confirm the G2 labels match).
  2. Compute the (5,5,8) tensor (means); validate shape (5,5,8), finite, [0,1].
  3. Persist via save_centroids with a MANIFEST metadata: {checkpoint_id, source:"s2p_g2_domain_labeled_reseed", calibration_rung:"G2", shape:[5,5,8], categories, actions, factors, factor_names_hash=sha256(canonical factor-name list)}.
  4. GUARD (net-new — the loader discards metadata + logs nothing + does NO factor-order validation): at startup read get_centroid_checkpoints("s2p", include_v2=False, limit=1), LOG checkpoint_id/created_at/shape/factor_names_hash/source, and VALIDATE shape==(5,5,8) + factor_names_hash matches the current preset → reject/loudly warn on mismatch.
  5. Keep the ACTIVE gate: _should_auto_approve (auto_approve.py, called s2p.py:2005-2010), thresholds hardcoded (price .90/qty .85/dup .92/contract .88/format .80). Do NOT touch the P40B shadow gate (s2p_auto_approve_gate.py, disabled/shadow-only).
SUCCESS CRITERION = DOMAIN-CORRECT DECISIONS + persistence proven:
  - Readback: load_latest_centroids("s2p") == saved tensor (zero-tolerance); a FRESH AGE-backed scorer's active tensor == saved (proves NO bootstrap fallback); identity logged.
  - Decisions (re-run G2 Step-4 through the loaded scorer): perfect→auto_approve (clears gate, GREEN); price/qty mismatch→hold_for_review; tax-only→escalate_to_buyer; duplicate→flag_leakage; both-bad→refer_to_specialist. Fix a wrong case's exemplar + recompute.
  - S2P-only (domain="s2p"; no other domain's centroids changed).
```

---

## VALIDATION — Phase F: duplicate correctness
```
TASK: F — validate DuplicateScore fires a correct non-zero when siblings exist. Report-only; disposable graph; drop after.
SETUP: protocol_v2_test_s2p_active_<uuid> seeded (Commit-1 writer) with a Supplier having 2-3 near-duplicate invoices (within the duplicate window) + a clear non-duplicate.
1. query_duplicate_context(target, supplier_id, amount, limit=20) → siblings returned, bounded, fast.
2. Feed to DuplicateScore → correct NON-zero for near-duplicate, ~0 for non-duplicate.
3. Perturb a sibling amount out of window → score drops.
REPORT: siblings, duplicate_score dup vs non-dup, perturbation, latency. VERDICT: correct + bounded? Drop.
```

## VALIDATION — Phase B2: density at true scale
```
TASK: B2 — directed query stays fast + returns entities at production density. Report-only; sandbox = CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph (~25,892 S2P Decisions) [resolve clone mechanism]; seed the faithful entity set + DECIDED_ON links (every invoice a hub); create the Invoice.invoice_id index.
TRIALS: for >=5 invoices, time the directed query cold+warm WITH/WITHOUT index; EXPLAIN for index use; confirm exactly the entity neighbors (no Decision-hub crowding).
REPORT: latencies, index necessity at 25,892, any crowded invoice. Drop.
```

## VALIDATION — Phase C: migration safety (soc_graph clone)
```
TASK: C — Track-1 migration non-destructive, idempotent, reversible. Report-only on committed source; sandbox = CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph into SB_C incl. S2P Decisions (a few-thousand ok) + all 84 DecisionEntityLink orphans; record pre-counts.
MIGRATION UNDER TEST = the Commit-1 Track-1 writer (property contract, stamps domain='s2p'/provenance='seed'/domain_source='migration'/entity_id; NON-force; force-delete FORBIDDEN — assert off).
C1: S2P Decision count before==after (0 deleted); every migrated node/edge stamped; idempotent (2nd run 0 new); rollback `MATCH (n {domain_source:'migration'}) DETACH DELETE n` returns exact pre-counts.
C2: reconcile 84 orphan DecisionEntityLink into real DECIDED_ON where Decision+Invoice exist; count reconciled vs residual; no Decision touched, no force-delete.
REPORT counts + policy. Drop SB_C.
```

## IMPLEMENT — migrate soc_graph (on C PASS)
Dry-run (report counts) → apply (`ALLOW_PRODUCTION_SEED=1`, stamped, non-force) + index → verify on live soc_graph (entity labels + counts present; index used by the anchored query; S2P-INV-0003 returns its neighbors in ms; orphans reconciled). Rollback ready: `MATCH (n {domain_source:'migration'}) DETACH DELETE n`.

## VALIDATION — Phase D: full end-to-end (final gate)
```
TASK: D — end-to-end in AGE mode. Report-only beyond the committed build; sandbox = disposable graph seeded via the migration; never write real soc_graph; drop after.
SETUP: Commits 1-3 committed (Track 2 + real factors + persisted calibration tensor); Track 1 applied to a protocol_v2_test_s2p_active_<uuid> graph; point the S2P PW backend at it.
D1 FULL SUITE: sharded S2P suite in AGE mode — cd copilot-sdk/e2e; npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=line, workers=1 backend-heavy, per-test 90/180s, --global-timeout 600/900s. REPORT pass/fail per shard, residual timeouts/empty-context.
D2 GRAPH-BACKED: perturb a Commodity.volatility (or new-factor input); confirm the factor moves.
D3 FAITHFULNESS GATE: for a sample across categories, decisions are DOMAIN-CORRECT — the 5-WAY action (auto_approve / hold_for_review / escalate_to_buyer / flag_leakage / refer_to_specialist), not a fixture match. Also record the auto_approve RATE (the thin-margin check — see caveats).
D4 OFF-PATH LINK: _link_decision_to_invoice off the response path — latency drops, real DECIDED_ON, no new orphans.
Drop the sandbox.
```

## Gate logic
STEP 0 (read-only) can run anytime before Commit 3. Commit 1 → Commit 2 → Commit 3, each blocked by its verify gate. F/B2 can run once Commit 1 (+ Commit 2 for F) lands. C gates the migrate step. D is the final green-and-faithful gate, after migrate.

## Caveats from S3/G2, folded into the build
- **Corpus through the real factor path** (Commit 3.1) — not the hand-authored G2 vectors; verify it reproduces the G2 tensor.
- **Category-invariance:** the G2 tensor is near-identical across the 5 categories (the factors are category-agnostic). Ship as-is; note it. Only revisit with category-specific exemplars if a real category needs to score differently.
- **Thin auto-approve margins** (perfect conf .900092 vs .90; one exemplar tuned to clear .92): don't tune the gate to force it — **measure the auto-approve rate on real invoices in D**, and add threshold/centroid headroom only if D shows over-conservatism.
- **Active gate, not shadow; log checkpoint identity + factor-name hash** (silent-override guard).

## The next "what-if" experiments (honest)
- **Solution what-ifs: DONE.** The ladder (S1–S6) resolved to S3 + G2; there is no remaining solution to explore.
- **New, small:** STEP 0 persistence scan ✅ DONE (found: use `save_centroids`; V2 writer is invisible to the loader). Remaining: each commit's integration-verify (does it compose in the real path?).
- **Validation experiments:** F, B2, C, D (already specified).
- **Future what-if (post-live, not now):** **G3** — relearn the centroid geometry from *real verified analyst outcomes* once the fix is live. This is the operational maintenance path the G-scan named; it's what turns the domain-bootstrap (G2) into empirically-learned calibration. Its own what-if when there's a real outcome corpus.

## Provenance
Mechanism facts from `s2p_g_scorer_calibration_scan_v1.md` (nearest-centroid (5,5,8), active-vs-shadow gate, no batch-rebuild op, checkpoint override) + `s2p_g_spike_calibration_results_v1.md` (the (5,5,8) tensor, domain policy, per-category thresholds, the Step-2 exemplar vectors). Factor formulas + property contract from `s2p_s3_path_a_spike_results_v1.md`. Track-2 query from the Phase B results. F/B2/C/D carried in-doc (were in `s2p_fix_b_forward_plan_v5.md`).
