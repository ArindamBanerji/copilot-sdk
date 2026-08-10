# S2P FIX-B What-If — Phase A′ (Corrected Correctness Spike) v1

**Date:** 2026-08-04
**Type:** Experimental spike in a disposable AGE graph. **Report-only** on source; never write `soc_graph`; drop sandboxes after.
**Follows:** `s2p_fix_b_whatif_phase_a_results_v1.md` (A1 = FAIL). This is the re-test that patches the five blockers A1 surfaced. A2 and Phases B/C/D remain gated on A′ passing.

## Why A′ (A1 failed — and the spike worked)
A1 proved the premise was *not* validated: seeding the standalone plan left `query_context` returning 0 rows, so the score fell back to fixtures. That failure is the payoff of spiking first — it caught, in a throwaway graph, five things that would have made a production migration silently wrong. A′ fixes each and re-asks: with the entities present *in the shape the runtime actually reads*, does the score compute real factors?

## The five blockers → what A′ changes
1. **Anchor mismatch.** Runtime reads `MATCH (e {entity_id:'S2P-INV-0003'})`; the seed writes `Invoice {invoice_id:…}` with no `entity_id`. → A′ tests **both** fixes and reports which to adopt: (a) stamp `entity_id = invoice_id` on entity nodes so the current generic query matches; (b) a **label-anchored** read `MATCH (e:Invoice {invoice_id:…})-[]-(n)` (the split-read — also the perf fix). Recommend (b), but prove both.
2. **No domain stamp.** `query_context` filters `WHERE n.domain='s2p'`; the seed stamps none → neighbors filtered out. → A′ stamps `domain='s2p'` on every node and edge (non-negotiable).
3. **Legacy vs active model.** The standalone `scripts/seed_s2p_graph.py` writes legacy edges (`INVOICED_BY`/`REFERENCES`/…) and links the invoice only to Supplier/PO/GR — **not** Commodity/Contract — so `CommodityIndexCorrelation` and `TaxRegulatoryCompliance` would fall back even after fixes 1–2. → A′ sources the **active-contract model** with **full invoice→{Supplier, PurchaseOrder, GoodsReceipt, Commodity, Contract} edge coverage**.
4. **No Decision/`DECIDED_ON`.** The score creates its own Decision, so this isn't the context-read blocker — but A′ notes whether the linked-Decision path needs it for the endpoint trial.
5. **Endpoint guard.** S2P active-AGE test mode only accepts `protocol_v2_test*` graph names (`s2p_graph_status.py:178-212`) — `whatif_*` was rejected. → A′ names its sandbox `protocol_v2_test_s2p_active_<uuid>` so the endpoint trial can run.

## A′ step 0 — resolve the model source (quick scan)
Two builders exist. Confirm which produces the **active** model (active-contract edges `DECIDED_ON`/`SUPPLIED_BY`/`HAS_COMMODITY_INDEX`/`GOVERNED_BY`/`RECEIVED_AS`, invoice linked to all six entity types):
- `scripts/seed_s2p_graph.py` → A1 proved this is **legacy** (wrong edges, no Commodity/Contract link).
- `app/seed_graph.py` → likely the **active** builder (its edge labels are the active set). **Confirm:** does it emit the active edges + link the invoice to Commodity and Contract + is its output domain-stampable?

**Critical mismatch to resolve here (this is why A′ needs a wrapper, not just "run the seed"):** `app/seed_graph.py` *builds* data (`seed_s2p_graph()` returns `(nodes, edges)`) but does **not** write to a graph; `scripts/seed_s2p_graph.py` has the AGE *writer* (`write_seed_plan`, `_props_literal`) but the legacy model. So no single tool both builds the active model AND writes it. A′'s wrapper (a scratch script, deleted after) closes the gap: take the **active builder's** `(nodes, edges)`, add `domain='s2p'` (and `entity_id=invoice_id`) to each, add any missing `invoice→Commodity`/`invoice→Contract` edges, and write them into the sandbox with `cypher()` CREATE (or by reusing `write_seed_plan`'s serialization). Report the exact builder chosen and which of {edges, Commodity/Contract link, domain, entity_id} the wrapper had to add.

---

## Codex prompt — Phase A′
```
TASK: S2P FIX-B what-if — Phase A′ (corrected correctness spike). Report-only; no source edits; never write soc_graph; drop sandbox after.
CONTEXT: A1 (s2p_fix_b_whatif_phase_a_results_v1.md) FAILED for 5 reasons: entity_id-vs-invoice_id anchor; no domain stamp; the standalone seed is the LEGACY model missing invoice→Commodity/Contract; no Decision/DECIDED_ON; and the endpoint rejects non-protocol_v2_test* graphs. Fix all five and re-test whether the score computes REAL factors.

STEP 0 — model source: Determine whether app/seed_graph.py (vs scripts/seed_s2p_graph.py) produces the ACTIVE-contract model — active edges (DECIDED_ON/SUPPLIED_BY/HAS_COMMODITY_INDEX/GOVERNED_BY/RECEIVED_AS) with the invoice linked to Supplier, PurchaseOrder, GoodsReceipt, Commodity, AND Contract. NOTE the build/write split: app/seed_graph.py BUILDS (returns nodes/edges) but does not write; scripts/seed_s2p_graph.py WRITES but is legacy. So you will write a scratch wrapper (deleted after) that takes the active builder's output and writes it stamped. Report the builder chosen + which of {active edges, Commodity/Contract link, domain stamp, entity_id} the wrapper had to add.

SETUP (scratch wrapper, deleted after):
1. Create sandbox named protocol_v2_test_s2p_active_<uuid12> (create_graph). [Satisfies the active-AGE test-mode guard.]
2. In the wrapper: (i) call the active builder to get (nodes, edges); (ii) add domain='s2p' to every node and edge; (iii) add entity_id=<the node's natural key value> to entity nodes (so Invoice gets entity_id='S2P-INV-0003') — this is anchor variant (a); (iv) if the builder does not already link the invoice to Commodity and Contract, add HAS_COMMODITY_INDEX(invoice→Commodity) and GOVERNED_BY(invoice→Contract) edges; (v) write all nodes+edges into the sandbox via cypher() CREATE (reuse write_seed_plan serialization if convenient).
3. Verify per-label node counts and that S2P-INV-0003 links to Supplier+PurchaseOrder+GoodsReceipt+Commodity+Contract (all domain-stamped).

TRIALS (for S2P-INV-0003):
T1 (anchor variant a — current generic query): with entity_id stamped, run the runtime path — instantiate the AGE store/S2PGraphReader pointed at the sandbox and call query_context('S2P-INV-0003', 2, domain='s2p') (this returns the normalized neighbor shape the factors expect). Equivalent raw Cypher: MATCH p=(e {entity_id:'S2P-INV-0003'})-[*1..2]-(n) WHERE n.domain='s2p' RETURN p LIMIT 100. Report row count + the neighbor labels returned.
T2 (anchor variant b — label-anchored): run MATCH (e:Invoice {invoice_id:'S2P-INV-0003'})-[]-(n) WHERE n.domain='s2p' RETURN n LIMIT 100 (wrap AS (n agtype)). Report rows + labels.
T3 (factors): load the S2P-INV-0003 invoice dict from data/synthetic_invoices.json (or the preview queue). For whichever of T1/T2 returns neighbors, call compute_all_factors(invoice_dict, {"neighbors": rows}) — pass the rows in the reader's normalized form (each entry {"node": {"_label": …, …props}}); if you used raw Cypher, shape the vertices into that form first. Report all 7 factor values and classify each REAL vs fixture-fallback. PASS = all 7 real, matching (or explainably differing from) the SQLite baseline (auto_approve@0.947; match_status .953 / amount_variance .04 / duplicate .007 / supplier_exception .033 / payment_terms .515 / commodity_index .822 / tax_reg .938).
T4 (endpoint): start the S2P backend on a spare port with env: S2P_ACTIVE_GRAPH_BACKEND=age, S2P_ACTIVE_AGE_DSN=<the AGE DSN>, S2P_ACTIVE_AGE_GRAPH=<sandbox>, S2P_ACTIVE_AGE_DOMAIN=s2p, S2P_ACTIVE_AGE_TEST_MODE=1. POST /api/s2p/score with a valid body for S2P-INV-0003 (shape per tests/test_s2p_score_endpoint.py VALID_REQUEST: event_id, category='price_variance', amount=3781.7, supplier_id='SUP-003', plus the factor inputs). Report HTTP status, action, confidence, factors, latency, any startup error.

REPORT: per trial — commands/Cypher, counts, factor values + REAL/fallback classification, latency, PASS/FAIL, and "what surprised us." Then: does A′ validate the FIX-B premise? Which anchor fix (a or b) to adopt? Which builder is the canonical active-model source? Any remaining gap before A2/B/C/D.

Drop the sandbox. No soc_graph writes. Delete scratch scripts.
```

## Gating & next-step prompts
- **A′ PASS** (all 7 factors real via T1 or T2, endpoint scores) → the premise holds. Proceed to **A2 → B → C → D**, whose prompt blocks live in `s2p_fix_b_whatif_experiments_v3.md`. **Before running them, bake in A′'s answers:** the chosen anchor fix (variant a `entity_id` vs variant b label-anchored) determines B1's query variants and the migration's stamping; the confirmed builder + the wrapper's added-edge/stamp list becomes the migration's node/edge contract in C. Update those two prompts with A′'s results, then run in order. (A2 will likely just confirm the label set, since the active model uses `Commodity`/`Contract` and the factors read those — but run it.)
- **A′ FAIL** → report which of T1–T4 broke and why (empty context? wrong labels? a factor still falling back? endpoint startup error?). The FIX-B source/query model is still wrong; iterate A′ again before any migration design. Do not advance to A2/B/C/D.

## Provenance
The five blockers and the seed counts are from `s2p_fix_b_whatif_phase_a_results_v1.md`. The active-contract labels/edges are from `s2p_entity_model_scan_v1.md` (`graph_contract.py`). The anchor/domain filter facts are from that scan + `age_graph_store.py:3143-3164`. The endpoint guard is `s2p_graph_status.py:178-212`. The factor→label mapping and SQLite baseline are from `test_factors.py`/`factors.py` and `s2p_diag`.
