# S2P FIX-B — Forward Execution Plan & Experiments v3

**Date:** 2026-08-04
**Supersedes for execution:** v2 (adds the forward validation set F/B2/C/D as current prompts + the interleaved build/migrate steps; keeps S3 and the S4/S5/S6 fallbacks). Pulls the once-scattered C/D (from v4) and B2/F (from v5) into one current, ordered doc. This is the doc the coding session runs.
**Rules:** spike-first; report-only on committed source except where a step says IMPLEMENT; scratch reverted; never write live `soc_graph`; sandboxes/clones dropped after; every perturbation/faithfulness step targets the ACTIVE compute path (not legacy/template/fixture modes). Sandbox name must match `protocol_v2_test_s2p_active_*` (S2P active-AGE guard). AGE DSN `host=172.22.74.149 port=5433` (fallback `host=localhost port=5433`).

## Status
Ladder: S1 (data-only) FAILED · S2 (bespoke read fix) PARTIAL/proven · **S3 (real factors + data contract) = the decisive gate, next** · S4/S5/S6 = pre-staged fallbacks. Done and feeding forward: SOC + DataOps perturbations (both graph-backed) and the platform faithfulness audit (11 faithful / 5 silent-default / 2 stub — the 2 stubs are S2P's; enumerated the missing seed properties). Fixture vector is NOT an oracle; "correct" = domain logic + stored data.

---

## FULL ORDERED SEQUENCE (the roadmap)
1. **S3 — EXPERIMENT (gate).** Design + prove the 2 real factors. PASS → step 2. FAIL → S4→S5→S6.
2. **IMPLEMENT — build the fix** (permanent): Track 2 (proven reader/normalization/duplicate) + Track 1 migration writer + the 2 real factors + the property-completeness contract.
3. **F — EXPERIMENT — duplicate correctness** (positive case the audit/Phase B never exercised).
4. **B2 — EXPERIMENT — density at true scale** (soc_graph clone, ~25,892 Decisions).
5. **C — EXPERIMENT — migration safety** (soc_graph clone: 0 Decisions deleted, idempotent, rollback, orphan reconcile).
6. **IMPLEMENT — migrate `soc_graph`** (dry-run → apply → verify).
7. **D — VALIDATE — full end-to-end** (sharded PW green + graph-backed + faithful + off-path link).
Steps 3–5 can run in parallel after step 2. Step 6 gates on C passing. Step 7 is the final gate.

---

## PROMPT — S3 (decisive gate)
```
TASK: S3 — design + prove real graph-native MatchStatus + TaxRegulatoryCompliance, modeled on the working bespoke pattern (SOC/DataOps: typed read of concrete props → continuous value), using DataOps's clean numeric contract and avoiding SOC's numeric/string gap. Report-only on committed source; scratch factor code + disposable graph; drop/revert after.
DESIGN (define "correct" from procurement domain logic; the fixture vector is NOT an oracle):
- MatchStatus (real 3-way match): read Invoice.amount, PurchaseOrder.amount, GoodsReceipt receipt-qty/amount → continuous match score (e.g. 1 - normalized max discrepancy), high when aligned. Specify required property shapes (numeric).
- TaxRegulatoryCompliance (real compliance): read Contract compliance/clause/threshold fields (define which) → continuous compliance score from actual terms vs invoice. Specify shapes (numeric).
SPIKE (disposable protocol_v2_test_s2p_active_<uuid>):
1. Seed Invoice/PO/GR/Contract with CORRECT shapes + realistic values. The audit found seed_s2p_graph.py:165-218 does NOT populate these — they MUST be added (the property-completeness contract): PurchaseOrder.amount (numeric), GoodsReceipt receipt-qty (numeric), Commodity.volatility (numeric), Invoice.payment_days (numeric). Use a numeric-coercion contract (stored numeric == factor-read numeric) AND emit explicit provenance so any fallback is visible, not silent.
2. Patch the 2 factors (scratch) to the new formulas; compute all 8 factors via the Track-2 directed query.
3. PERTURB each new factor's input (change PO.amount to create a mismatch; change a compliance field); confirm the factor moves continuously + in isolation.
4. SOFT SANITY (not oracle): for a sample across categories, are decisions DEFENSIBLE (well-matched compliant → auto_approve-ish; mismatch/non-compliant → refer/reject)? ground_truth_action directional only.
REPORT: the 2 factor formulas + required property shapes; perturbation results; sample decisions. VERDICT: is faithful graph-native S2P scoring ACHIEVABLE? Revert; drop.
```

## IMPLEMENT — build (on S3 PASS)
Permanent, committed, S2P-scoped:
- **Track 2:** `S2PGraphReader.query_direct_context(invoice_id, limit=100)` (directed `(e:Invoice {invoice_id})-[]->(n) WHERE n.domain='s2p' RETURN n`, normalized to `{"node":{props}}`) + `query_duplicate_context(invoice_id, supplier_id, amount, limit=20)`; `_resolve_graph_context` calls them + accepts the normalized rows. Shared `AGEGraphStore.query_context` UNCHANGED.
- **The 2 real factors** from S3 (with provenance flags).
- **Track 1 writer:** hardened wrapper over `app/seed_graph.py:seed_s2p_graph()` — per-invoice GoodsReceipt/Commodity/Contract; the property-completeness contract (PO.amount, GR receipt-qty, Commodity.volatility, Invoice.payment_days, Supplier.exception_rate/payment_terms); stamp `domain='s2p'`/`provenance='seed'`/`domain_source='migration'`/`entity_id`; NON-force; `Invoice.invoice_id` index (DDL: `CREATE INDEX ON "<graph>"."Invoice" USING btree (agtype_access_operator(VARIADIC ARRAY[properties,'"invoice_id"'::agtype]))`).
- Move `_link_decision_to_invoice` off the response path (→ `_SIDE_EFFECT_EXECUTOR`).
Add unit tests: direct-context normalization, Decision-hub exclusion, bounded duplicate, and a perturbation test per new factor.

## PROMPT — F: duplicate correctness
```
TASK: F — validate DuplicateScore fires a correct non-zero when siblings exist (the audit/Phase B only saw the 0 case). Report-only on committed source; disposable graph; drop after.
SETUP: protocol_v2_test_s2p_active_<uuid> seeded with the faithful entity set + a Supplier with 2-3 near-duplicate invoices (amounts within the duplicate window) and a clear non-duplicate.
1. Run query_duplicate_context(target, supplier_id, amount, limit=20); confirm siblings returned, bounded, fast.
2. Feed to DuplicateScore; confirm a correct NON-zero for the near-duplicate and ~0 for the non-duplicate.
3. PERTURB a sibling amount out of the window; confirm the score drops (in-window fires, out-of-window doesn't).
REPORT: siblings returned, duplicate_score for duplicate vs non-duplicate, perturbation effect, latency. VERDICT: duplicate factor correct + bounded? Drop.
```

## PROMPT — B2: density at true scale
```
TASK: B2 — confirm the directed query stays fast + returns the entities at production density. Report-only; sandbox = a CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph (all ~25,892 S2P Decisions) [resolve clone mechanism]; seed the faithful entity set + DECIDED_ON links so every invoice is a real hub; create the Invoice.invoice_id index.
TRIALS: for >=5 invoices, time the directed query MATCH (e:Invoice {invoice_id:'…'})-[]->(n) WHERE n.domain='s2p' RETURN n LIMIT 100 (cold+warm) WITH and WITHOUT the index; EXPLAIN for index use; confirm each returns exactly its entity neighbors (no Decision-hub crowding).
REPORT: latencies, index-used, whether the index is necessary at 25,892 Decisions, any crowded invoice. Drop the clone.
```

## PROMPT — C: migration safety (soc_graph clone)
```
TASK: C — prove the Track-1 migration is non-destructive, idempotent, reversible. Report-only on committed source; sandbox = a CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph into SB_C incl. its S2P Decisions (a representative few-thousand is fine) + all 84 DecisionEntityLink orphans. Record pre-counts.
MIGRATION UNDER TEST = the built Track-1 writer (active builder + hardened wrapper, property-completeness contract, stamps domain='s2p'/provenance='seed'/domain_source='migration', entity_id; NON-force; force delete FORBIDDEN — assert off).
C1 ASSERT + REPORT: S2P Decision count before==after (zero deleted); every migrated node/edge carries the stamps; idempotent (2nd run 0 new); rollback `MATCH (n {domain_source:'migration'}) DETACH DELETE n` returns exact pre-counts.
C2 ORPHAN RECONCILE: reconcile the 84 orphan DecisionEntityLink into real DECIDED_ON where Decision+Invoice both exist; count reconciled vs residual; no Decision touched, no force-delete. REPORT policy + counts.
Drop SB_C.
```

## IMPLEMENT — migrate `soc_graph` (on C PASS)
Dry-run (report counts) → apply (`ALLOW_PRODUCTION_SEED=1`, stamped, non-force) + indexes → verify on live soc_graph (entity labels + counts present; index used by the anchored query; S2P-INV-0003 returns its neighbors in ms; orphans reconciled). Rollback ready: `MATCH (n {domain_source:'migration'}) DETACH DELETE n`.

## PROMPT — D: full end-to-end (final gate)
```
TASK: D — end-to-end validation in AGE mode. Report-only beyond the committed build; sandbox = disposable graph seeded via the migration; never write real soc_graph; drop after.
SETUP: With Track 2 + real factors committed and Track 1 applied to a protocol_v2_test_s2p_active_<uuid> graph, point the S2P PW backend at it.
D1 FULL SUITE: sharded S2P suite in AGE mode — cd copilot-sdk/e2e; npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=line, workers=1 backend-heavy, per-test 90/180s, --global-timeout 600/900s. REPORT pass/fail per shard, residual timeouts/empty-context.
D2 GRAPH-BACKED: perturb a Commodity.volatility (or a new-factor input), confirm the score's factor moves. REPORT both scores.
D3 FAITHFULNESS GATE: for a sample across categories, assert decisions are DOMAIN-CORRECT (not a fixture match) — well-matched compliant → auto_approve-ish, etc. REPORT the sample.
D4 OFF-PATH LINK: confirm _link_decision_to_invoice off the response path — latency drops, real DECIDED_ON edges, no new orphans.
Drop the sandbox.
```

---

## FALLBACKS — run ONLY if S3 fails (then in order)
- **S4 (hybrid):** move ONLY the failing factor(s) to event-field inputs (request supplies match/compliance data), keep the rest on the graph. Spike: patch moved factor(s) to read the request; score a sample; confirm faithful + operationally sane. If yes → S4 is the fix. If no → S5.
- **S5 (event-field):** compute ALL 8 factors from request fields (Trading/Purchasing pattern); entity graph = context/audit only. Spike: patch the registry; score without traversal; confirm decisions + fast. If no → S6.
- **S6 (passthrough, last resort):** persist materialized factor vectors as decision props with provenance='materialized, not recomputed'; document that the graph does not drive S2P scoring under S6.

## Gate logic
S3 PASS → build → F/B2/C → migrate → D. S3 FAIL → S4 → S5 → S6. Any forward experiment failing → fix in-sandbox before advancing; C failing blocks the migrate step.

## Separate track (not on the S2P critical path)
Platform provenance hygiene (motivated by the audit): fail-visible contracts + per-factor perturbation-provenance tests across the graph-consuming copilots, and fix SOC's asset_criticality numeric/string mismatch. Own program; do not block S2P.

## Provenance
S3 property list + the 2 stubs from `platform_faithfulness_audit_v1.md`; Track-2 directed query + index DDL from `s2p_fix_b_whatif_phase_b_results_v1.md`; migration writer + orphans + force-delete danger from `s2p_entity_model_scan_v1.md`; numeric-contract template from `dataops_perturbation_experiment_v1.md`; fixture-not-oracle from `phase_e`; ladder from `s2p_solution_ladder_v1.md`.
