# S2P FIX-B What-If — Adapted Experiment Plan v4

**Date:** 2026-08-04
**Supersedes:** v3 (Phase B was written for a data-only fix and is now stale) and folds in the Phase B′ runtime-shape spike. Phases A/A′ are complete; their results reshape everything below.
**Type:** Spike-first. Report-only on committed source; scratch/branch patches allowed and reverted after; never write the live `soc_graph`; sandboxes/clones dropped after.

---

## What we've learned (the diagnosis changed — read this first)
- **A1 (FAIL):** the standalone `scripts/seed_s2p_graph.py` writes a *legacy* model (wrong edges, no Commodity/Contract link, no domain stamp, no `entity_id`); the endpoint also rejects non-`protocol_v2_test*` sandbox graphs.
- **A′ (half-pass):** the *active* builder `app/seed_graph.py:seed_s2p_graph()` + a stamping wrapper + a **label-anchored** read produces **all 7 factors from the graph**. But the live endpoint still runs the generic label-less **path** query and a normalization (`_resolve_graph_context`, `s2p.py:138-161`) that only accepts `row['node']` — so it **rejects the graph rows and falls back to fixtures**. The endpoint's correct-looking `auto_approve@0.947` was a fixture coincidence, not graph-backed.
- **THE FIX IS TWO TRACKS:**
  - **Track 1 (DATA):** migrate the S2P entity subgraph into `soc_graph` — active-builder model + wrapper (per-invoice GoodsReceipt/Commodity/Contract, `domain`/`provenance`/`entity_id` stamps, PO `amount`).
  - **Track 2 (CODE):** change the S2P runtime so it actually consumes the graph — label-anchored **directed** direct-context query + a normalization that accepts `RETURN n` rows + a bounded duplicate-candidate lookup for DuplicateScore.
  - **"Migration only" is not a shortcut:** at production density each invoice is a ~500-Decision hub, so the old variable-length query would fan out and likely stall even with entities present; and without the Track-2 normalization the score stays fixture-fallback — hollow, since the graph wouldn't drive S2P at all.
- **Latent-bug flag (out of scope, worth noting):** if S2P's path/normalization mismatch means graph context was never consumed, check whether other copilots share the same generic-query/normalization gap. Not part of these experiments.

## Locked-in answers from A′ (bake into all phases — do not re-derive)
- **Builder:** `app/seed_graph.py:seed_s2p_graph()`. **Anchor:** label-anchored `MATCH (e:Invoice {invoice_id:…})`.
- **Labels:** Decision, Invoice, Supplier, PurchaseOrder, GoodsReceipt, Commodity, Contract. **Edges:** DECIDED_ON, SUPPLIED_BY, MATCHED_TO, RECEIVED_AS, HAS_COMMODITY_INDEX, GOVERNED_BY — all `domain='s2p'`.
- **Directionality (the density fix):** factor edges are **outgoing** from the invoice; `DECIDED_ON` is incoming (`Decision→Invoice`). A directed-outgoing 1-hop read returns exactly the entities and ignores the Decision hub.
- **Wrapper stamps** `provenance='seed'`; the **migration** must additionally stamp `domain_source='migration'` as the rollback key (distinct from existing seed data).

---

## Execution order & gating
1. **Phase B** (below) — spike Track 2 + the density query; prove the endpoint is graph-backed. **Gates everything.**
2. On B pass → **implement Track 2 for real** (committed source) and Claude drafts the Track-1 migration spec around the wrapper model.
3. **Phase C** — migration safety on a `soc_graph` clone.
4. **Phase D** — end-to-end: real Track-2 + applied Track-1 on a seeded graph → full sharded PW green **and** graph-backed.
- **A2 (label competition)** is largely **resolved**: A′ used Commodity/Contract successfully, so those are canonical for the score path. Run A2 **only if** Phase D surfaces a situation/preview test that needs the contract labels (CommodityIndex/ContractClause/ComplianceHistory); otherwise defer.
- Any phase failing short-circuits the rest — iterate in-sandbox, never advance on red.

## Safety rules (every phase)
Never `create_graph`/`drop_graph`/write `soc_graph`. Sandboxes are `protocol_v2_test_s2p_active_<uuid>` (required by the S2P active-AGE test-mode guard) or a `soc_graph` clone. Track-2 patches are scratch/branch only until a phase passes; revert after. Delete scratch scripts. Health route is `/health` (not `/api/health`). AGE DSN: `host=172.22.74.149 port=5433 sslmode=disable`, fallback `host=localhost port=5433 …`.

---

## PROMPT B — Runtime-shape & density (the decisive spike)
```
TASK: S2P FIX-B — Phase B (runtime-shape + density). Report-only on committed source; scratch patch + disposable sandbox/clone only; never write soc_graph; revert patch + drop sandboxes after.
CONTEXT & LOCKED ANSWERS: see "Locked-in answers" (builder app/seed_graph.py:seed_s2p_graph + wrapper; anchor label-anchored Invoice.invoice_id; labels/edges as listed; factor edges outgoing, DECIDED_ON incoming). Reuse the A′ wrapper for seeding.

PART 1 — density query (find the shape that's fast AND returns the 6 entities without Decision-hub crowding):
1. Build a density graph: clone soc_graph [resolve clone mechanism] + seed the wrapper model, OR a protocol_v2_test_s2p_active_<uuid> sandbox seeded with the wrapper model + ~500 synthetic Decision nodes, EACH stamped domain='s2p' with a DECIDED_ON->S2P-INV-0003 edge (so the invoice has production-like incoming density). Create an Invoice.invoice_id index [resolve AGE DDL; confirm it exists].
2. Time (cold+warm, >=3 reps) for S2P-INV-0003; report latency, neighbor labels returned, whether all of Supplier/PO/GR/Commodity/Contract are present, and EXPLAIN index-use:
   (1) (e:Invoice {invoice_id:'S2P-INV-0003'})-[]-(n)  WHERE n.domain='s2p' RETURN n LIMIT 100   [does the hub crowd entities out of LIMIT?]
   (2) (e:Invoice {invoice_id:'S2P-INV-0003'})-[]->(n) WHERE n.domain='s2p' RETURN n              [expected: exactly the 5 entities]
   (3) (2) + WHERE n:Supplier OR n:PurchaseOrder OR n:GoodsReceipt OR n:Commodity OR n:Contract
   (4) (2)/(3) with vs without the index
3. Bounded duplicate lookup for DuplicateScore [resolve the exact amount tolerance from DuplicateScore in factors.py]:
   MATCH (:Supplier {supplier_id:'SUP-003'})<-[:SUPPLIED_BY]-(sib:Invoice) WHERE sib.amount BETWEEN <lo> AND <hi> AND sib.invoice_id <> 'S2P-INV-0003' RETURN sib LIMIT k  — time + confirm bounded.
REPORT the winning direct-context shape (expected directed-outgoing, indexed) + the duplicate query.

PART 2 — runtime patch, prove the endpoint is graph-backed:
4. In a SCRATCH/branch build (no committed edit), and SCOPED TO S2P ONLY (do NOT change the shared generic AGEGraphStore.query_context used by other copilots — add an S2P-specific direct-context method or branch): (a) S2P reader emits the Part-1 winning direct query returning normalized n rows (each {"_label":…, props}); (b) _resolve_graph_context accepts those normalized rows, not path strings; (c) add the bounded duplicate lookup feeding DuplicateScore.
5. Seed a protocol_v2_test_s2p_active_<uuid> sandbox with the wrapper model. Start S2P on a spare port: S2P_ACTIVE_GRAPH_BACKEND=age, S2P_ACTIVE_AGE_DSN=<DSN>, S2P_ACTIVE_AGE_GRAPH=<sandbox>, S2P_ACTIVE_AGE_DOMAIN=s2p, S2P_ACTIVE_AGE_TEST_MODE=1. Health=/health.
6. POST /api/s2p/score {event_id:'S2P-INV-0003', category:'price_variance', amount:3781.7, supplier_id:'SUP-003', supplier_name:'Northstar Packaging'}. Record status, action, confidence, factor vector, latency.
7. DECISIVE graph-backed proof (fixture values coincidentally equal the baseline, so a matching vector is NOT proof): the seeded Commodity.volatility gives commodity_index_correlation≈0.822; set that Commodity's volatility to a distinctly different value in the sandbox, re-score, and confirm commodity_index_correlation CHANGES. Report both scores.
REPORT per trial: commands/Cypher, latency, factor values, PASS/FAIL, "what surprised us." Verdict: is the endpoint genuinely graph-backed (perturbation moved the factor) and is the query fast at density? Revert scratch patch; drop sandboxes; confirm soc_graph untouched.
```

## PROMPT C — Migration safety (soc_graph clone) — run after B passes + Track 2 is implemented
```
TASK: S2P FIX-B — Phase C (migration safety). Report-only on committed source; sandbox = a CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph into SB_C including its S2P Decisions (a representative few-thousand subset is fine) + all 84 DecisionEntityLink orphans. Record pre-counts (S2P Decision count, orphan count, per-label counts).
MIGRATION UNDER TEST = the active-builder model written by a hardened wrapper: source app/seed_graph.py:seed_s2p_graph(); add per-invoice GoodsReceipt/Commodity(volatility)/Contract + edges; stamp EVERY node/edge domain='s2p', provenance='seed', domain_source='migration'; set entity_id; add PO amount; NON-force (natural-key CREATE-if-absent); the legacy force delete MATCH (n) WHERE n.domain='s2p' DETACH DELETE n is FORBIDDEN (assert off).
C1 assert + REPORT: S2P Decision count before==after (zero deleted); every migrated node/edge carries the three stamps; idempotent (2nd run creates 0 new); rollback MATCH (n {domain_source:'migration'}) DETACH DELETE n returns SB_C to exact pre-counts.
C2 orphan reconciliation: reconcile the 84 orphan DecisionEntityLink into real DECIDED_ON edges where Decision+Invoice both now exist; count reconciled vs residual; assert no Decision touched, no force-delete. REPORT the retain/reconcile/delete policy with counts.
Drop SB_C.
```

## PROMPT D — End-to-end (seeded sandbox + real Track-2) — the final gate
```
TASK: S2P FIX-B — Phase D (end-to-end, AGE mode). Report-only beyond the committed Track-2 change; sandbox = disposable graph; never write soc_graph; drop after.
SETUP: With Track 2 implemented (committed), create protocol_v2_test_s2p_active_<uuid>, apply the Track-1 migration (wrapper model + indexes) into it, point the S2P PW backend at it (env as in B).
D1 full suite: run the sharded S2P suite in AGE mode — cd copilot-sdk/e2e; npx playwright test --config=s2p/playwright.config.ts s2p/ --reporter=line, workers=1 backend-heavy, per-test 90/180s, --global-timeout 600/900s. REPORT pass/fail per shard, any residual timeouts/empty-context.
D2 graph-backed under the real endpoint: repeat the Part-2 perturbation (change a Commodity.volatility, confirm the score's commodity factor moves) against the committed build. REPORT both scores.
D3 off-path link: confirm _link_decision_to_invoice moved off the response path — score latency drops, real DECIDED_ON edges created, no new orphan DecisionEntityLink. REPORT counts.
Drop the sandbox.
```

## After the spikes
On B pass, Claude writes the FIX-B spec as **two tracks**: (1) the migration (active-builder + hardened wrapper into `soc_graph`, stamped, non-force, indexed, rollback-tagged, orphan policy from C2) and (2) the runtime change (S2P-scoped directed direct-context query + normalization + bounded duplicate lookup, from B). D is the integration gate. Place the spec in `copilot-sdk/docs/design/` for design-verify.

## Provenance
Two-track diagnosis, locked answers, edge directionality, and the fixture-coincidence finding are from `s2p_fix_b_whatif_phase_a_prime_results_v1.md`. Density (~500 Decisions/invoice) from `s2p_entity_model_scan_v1.md`. Migration writer dangers (force delete) from the entity-model scan. The perturbation test remedies A′'s fixture-coincidence finding. Duplicate tolerance + factor→edge mapping from `factors.py`.
