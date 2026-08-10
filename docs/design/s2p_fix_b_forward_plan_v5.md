# S2P FIX-B — Forward Execution Plan v5 (post-S3, calibration as a scan-first ladder)

**Date:** 2026-08-04
**Supersedes:** v4 (expands the single "Phase G" into a scan-first calibration sub-problem: deep-scan the scorer mechanism → design the calibration ladder → spike the decisive rung). Copy into `copilot-sdk/docs/design/` replacing v3/v4.
**Rules:** spike-first; report-only on committed source except where a step says IMPLEMENT; scratch reverted; never write live `soc_graph`; sandboxes/clones dropped after; every perturbation/faithfulness step targets the ACTIVE compute path. Sandbox `protocol_v2_test_s2p_active_*`. AGE DSN `host=172.22.74.149 port=5433` (fallback `localhost:5433`).

## Status
**S3 PASSED — Path A is viable and committed.** The two real factors compute faithful continuous values from graph properties, perturbation-proven and isolated; decisions are directionally defensible (mismatch/non-compliant never auto-approved). **New finding from S3:** the scorer's action centroids / auto-approve gate were calibrated on the OLD stub semantics, so a perfect NEW-factor vector currently maps to `hold_for_review`, not `auto_approve` — a calibration follow-up, now its own **scan-first Phase G** (the recalibration lever is unknown until scanned), NOT a blind build step. Ladder rungs S4/S5/S6 are RETIRED (only needed on an S3 failure). Fixture vector is NOT an oracle; "correct" = domain logic + stored data.

## FULL ORDERED SEQUENCE
1. ~~S3 (gate)~~ **DONE — PASS.**
2. **IMPLEMENT — build** (4 components, below).
3. **F — EXPERIMENT — duplicate correctness** (parallel).
4. **B2 — EXPERIMENT — density at true scale** (parallel).
5. **G — CALIBRATION sub-problem (scan-first):** Codex deep-scans the scorer/centroid/gate mechanism → design the calibration ladder → spike the decisive rung (parallel with build; prerequisite for D).
6. **C — EXPERIMENT — migration safety** on a soc_graph clone.
7. **IMPLEMENT — migrate `soc_graph`** (dry-run → apply → verify). Gates on C.
8. **D — VALIDATE — full end-to-end** (sharded PW green + graph-backed + faithful + off-path link). Gates on G + migrate.

## IMPLEMENT — build (Path A committed)
S2P-scoped, permanent, with unit tests. **Three components here; scorer recalibration is deferred to Phase G — its lever is unknown until the G-scan, so it is not built blindly.**
1. **Track 2 (proven):** `S2PGraphReader.query_direct_context(invoice_id, limit=100)` — directed `(e:Invoice {invoice_id})-[]->(n) WHERE n.domain='s2p' RETURN n`, normalize AGE vertices via `properties(n)` to `{"node":{props}}`; `query_duplicate_context(invoice_id, supplier_id, amount, limit=20)`; `_resolve_graph_context` calls them + accepts normalized rows. Shared `AGEGraphStore.query_context` UNCHANGED.
2. **The 2 real factors** (exact formulas from S3 report Step 0): `RealMatchStatus` = `1 - min(max normalized discrepancy)` over Invoice/PO/GR amount+qty pairs; `RealTaxRegulatoryCompliance` = `checks_passed/checks_total` over Contract `max_amount`(invoice≤)/`tax_compliant`/`regulatory_status`. Numeric-coercion contract (DataOps `_safe_get_float` pattern) + explicit provenance (`computed`/`no_match_data`/`partial_data`/`no_contract`/`no_compliance_fields`).
3. **Track 1 writer:** hardened wrapper over `app/seed_graph.py:seed_s2p_graph()` writing the property-shape contract (below); stamp `domain='s2p'`/`provenance='seed'`/`domain_source='migration'`/`entity_id`; NON-force; `Invoice.invoice_id` index (`CREATE INDEX ON "<graph>"."Invoice" USING btree (agtype_access_operator(VARIADIC ARRAY[properties,'"invoice_id"'::agtype]))`). Move `_link_decision_to_invoice` off the response path (→ `_SIDE_EFFECT_EXECUTOR`).
4. **Scorer recalibration — deferred to Phase G, NOT built here.** The recalibration lever is unknown until the G-scan; implement it only after the G-spike proves the chosen calibration rung (perfect vector → auto_approve; mismatches escalate; never calibrate to the old fixture vector).

### Property-shape contract for Track 1 (from S3 — all must be seeded)
| Label | Property | Type | Used by |
|---|---|---|---|
| Invoice | amount / quantity / payment_days | numeric | MatchStatus, AmountVariance / MatchStatus / PaymentTerms |
| PurchaseOrder | amount / quantity | numeric | MatchStatus, AmountVariance / MatchStatus |
| GoodsReceipt | qty_received / amount | numeric | MatchStatus |
| Supplier | exception_rate / payment_terms | numeric[0,1] / parseable string | SupplierException / PaymentTerms |
| Commodity | volatility | numeric[0,1] | CommodityIndex |
| Contract | max_amount / tax_compliant / regulatory_status | numeric / boolean-like / enum string | TaxRegulatoryCompliance |
(The committed seed creates only Contract identity/linkage — the migration MUST add `max_amount`/`tax_compliant`/`regulatory_status` and the numeric fields above.)

## PHASE G — Calibration sub-problem (scan-first, then ladder, then spike)
S3 surfaced this: a perfect NEW-factor vector maps to `hold_for_review`, not `auto_approve`, because the scorer's action centroids / gate were calibrated on the OLD stub semantics. This is its own sub-problem — so scan the mechanism, enumerate the solution ladder, then spike the decisive rung (same discipline that got us here). **Do NOT recalibrate to the old fixture vector — target DOMAIN-CORRECT actions.**

### G-scan — Codex deep scan (read-only; parallel with build)
```
TASK: Deep scan the S2P scorer calibration mechanism. Read-only; no source/test edits; no graph writes. GOAL: understand exactly how a factor vector becomes an action so we can choose the right recalibration lever.
REPORT:
1. VECTOR→ACTION: how does the S2P scorer (CompoundingScorer) turn a factor vector into an action + confidence? Nearest-centroid? thresholds? distance/softmax? a gate? Cite the code path.
2. CENTROIDS/GATE: where are the S2P action centroids and the auto_approve gate defined, and how are they computed or learned (seeded corpus? RL score→outcome→learn loop? static config?)? Cite.
3. RECALIBRATION LEVER: what would actually change the mapping for the new factor semantics — re-seed a corpus, re-run learning, or adjust config thresholds? Which are supported without code surgery?
4. CORPUS PROVENANCE: are the calibration targets/corpus FIXTURE-derived (same no-oracle risk as the factor "ground truth"), or real labeled outcomes? Cite the source.
5. ISOLATION: is calibration per-copilot (S2P-specific centroids/config) or shared? Would recalibrating S2P disturb SOC/Trading/etc.?
6. GATE INTERACTION: how does the SR-1 conservation-GREEN gate combine with the action decision?
VERDICT: the recalibration lever(s) available, and which calibration-ladder rungs (below) the mechanism supports.
```

### Calibration ladder (refine after G-scan; pick the decisive rung to spike)
| Rung | What-if solution | Applies if… |
|---|---|---|
| G1 | Gate/threshold retune (config only) | the auto_approve decision is thresholds on confidence/factors |
| G2 | Centroid re-seed from new-factor exemplars | actions come from nearest-centroid over a recomputable exemplar set |
| G3 | Relearn via the compounding score→outcome→learn loop | centroids are RL-learned (most aligned with the platform thesis) |
| G4 | Analytic action regions from procurement domain logic | we choose to specify boundaries rather than learn them |
| G5 (retreat) | Keep old centroids + accept conservative holds, or a thin correction layer | full recalibration proves infeasible now |
Decisive rung ≈ G2 or G3 (the G-scan decides which). Cheap→expensive; the aligned target is a learned/re-seeded mapping, not hand thresholds.

### G-spike — decisive rung (after the ladder is chosen; uses the 2 new factors — scratch factors OK as in S3, so it is not blocked on the committed build)
```
TASK: G-spike — apply the chosen calibration rung and prove decisions are domain-correct under the new factor semantics. Report-only on committed source; scratch calibration + disposable graph; revert/drop.
1. Generate new-factor vectors for a labeled sample across domain conditions (perfect / price-off / qty-off / non-compliant / both-bad) via the Track-2 directed read + the 2 real factors.
2. Apply the chosen rung (re-seed centroids / re-run learning / retune gate) against DOMAIN-CORRECT target actions (perfect+compliant → auto_approve; mismatch/non-compliant → refer/reject) — NOT the fixture vector.
3. Verify: perfect → auto_approve; escalations behave; no mismatched/non-compliant auto_approve; SR-1 GREEN gate still holds; S2P-only (no disturbance to other copilots).
REPORT: the rung applied, sample decisions before/after, isolation check. VERDICT: decisions correct under the new semantics? If the rung fails, drop to the next ladder rung. Revert; drop.
```

## PROMPT — F: duplicate correctness
```
TASK: F — validate DuplicateScore fires a correct non-zero when siblings exist. Report-only; disposable graph; drop after.
SETUP: protocol_v2_test_s2p_active_<uuid> seeded with the faithful entity set + a Supplier with 2-3 near-duplicate invoices (within the duplicate window) and a clear non-duplicate.
1. query_duplicate_context(target, supplier_id, amount, limit=20) → confirm siblings returned, bounded, fast.
2. Feed to DuplicateScore → correct NON-zero for near-duplicate, ~0 for non-duplicate.
3. Perturb a sibling amount out of window → score drops.
REPORT: siblings, duplicate_score dup vs non-dup, perturbation, latency. VERDICT: correct + bounded? Drop.
```

## PROMPT — B2: density at true scale
```
TASK: B2 — directed query stays fast + returns entities at production density. Report-only; sandbox = CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph (~25,892 S2P Decisions) [resolve clone mechanism]; seed the faithful entity set + DECIDED_ON links (every invoice a hub); create the Invoice.invoice_id index.
TRIALS: for >=5 invoices, time the directed query cold+warm WITH/WITHOUT index; EXPLAIN for index use; confirm exactly the entity neighbors (no Decision-hub crowding).
REPORT: latencies, index necessity at 25,892, any crowded invoice. Drop.
```

## PROMPT — C: migration safety (soc_graph clone)
```
TASK: C — Track-1 migration non-destructive, idempotent, reversible. Report-only on committed source; sandbox = CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph into SB_C incl. S2P Decisions (a few-thousand ok) + all 84 DecisionEntityLink orphans; record pre-counts.
MIGRATION UNDER TEST = the built Track-1 writer (property-shape contract, stamps domain='s2p'/provenance='seed'/domain_source='migration'/entity_id; NON-force; force-delete FORBIDDEN — assert off).
C1: S2P Decision count before==after (0 deleted); every migrated node/edge stamped; idempotent (2nd run 0 new); rollback `MATCH (n {domain_source:'migration'}) DETACH DELETE n` returns exact pre-counts.
C2: reconcile 84 orphan DecisionEntityLink into real DECIDED_ON where Decision+Invoice exist; count reconciled vs residual; no Decision touched, no force-delete.
REPORT counts + policy. Drop SB_C.
```

## IMPLEMENT — migrate `soc_graph` (on C PASS)
Dry-run (counts) → apply (`ALLOW_PRODUCTION_SEED=1`, stamped, non-force) + index → verify on live soc_graph (labels+counts present; index used by the anchored query; S2P-INV-0003 returns neighbors in ms; orphans reconciled). Rollback ready.

## PROMPT — D: full end-to-end (final gate)
```
TASK: D — end-to-end in AGE mode. Report-only beyond the committed build; sandbox = disposable graph seeded via the migration; never write real soc_graph; drop after.
SETUP: Track 2 + real factors + recalibration (G) committed; Track 1 applied to a protocol_v2_test_s2p_active_<uuid> graph; point the S2P PW backend at it.
D1 FULL SUITE: sharded S2P suite in AGE mode — cd copilot-sdk/e2e; npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=line, workers=1 backend-heavy, per-test 90/180s, --global-timeout 600/900s. REPORT pass/fail per shard, residual timeouts/empty-context.
D2 GRAPH-BACKED: perturb a Commodity.volatility (or new-factor input); confirm the factor moves.
D3 FAITHFULNESS GATE: for a sample across categories, decisions DOMAIN-CORRECT (perfect+compliant → auto_approve; mismatch/non-compliant → refer/reject) — not a fixture match.
D4 OFF-PATH LINK: _link_decision_to_invoice off the response path — latency drops, real DECIDED_ON, no new orphans.
Drop the sandbox.
```

## Gate logic
Build → F/B2/G parallel → C → migrate → D. C failing blocks migrate. G is scan → ladder → spike; if the chosen rung can't produce domain-correct decisions, descend to the next calibration rung (G1…G5). G must reach domain-correct decisions before D's faithfulness gate. D is the final green-and-faithful gate.

## Separate track (not on the S2P critical path)
Platform provenance hygiene: fail-visible contracts + per-factor perturbation-provenance tests across graph-consuming copilots; fix SOC's asset_criticality numeric/string mismatch. Own program.

## Open items (minor)
- **environmental_risk (S2P's 8th factor):** data source unverified — S3 saw the default 0.5 with no live value. Confirm during build/D whether it needs a seeded property or the 0.5 default is acceptable; not a blocker.
- **Clone mechanism** (B2 + C both need it, marked `[resolve]`): resolve the `soc_graph` clone approach once and reuse for both.

## Provenance
Factor formulas + property contract + calibration finding from `s2p_s3_path_a_spike_results_v1.md`; Track-2 query + index DDL from `phase_b`; migration/orphans/force-delete from `s2p_entity_model_scan_v1`; numeric-contract from `dataops_perturbation_experiment_v1`; fixture-not-oracle from `phase_e`.
