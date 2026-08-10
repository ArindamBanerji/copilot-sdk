# S2P FIX-B — Next What-If Experiments & Execution Order v5

**Date:** 2026-08-04
**Companion to:** `s2p_fix_b_two_track_implementation_v2.md` (the spec) and `s2p_fix_b_whatif_experiments_v4.md` (prompts C/D). This doc keeps the spike-first discipline going *in addition to* implementation: it targets what we have **not** yet figured out, and gives the coding session the execution order + near-executable prompts.
**Rule unchanged:** report-only on committed source except where a step says IMPLEMENT; scratch patches reverted; never write live `soc_graph`; sandboxes/clones dropped after.

## Status — proven vs NOT figured out
**Proven (Phase A/A′/B):** the directed-outgoing label-anchored query is fast and hub-immune; the S2P-scoped runtime patch makes the endpoint genuinely graph-backed (perturbation moved `commodity_index_correlation`). Track 2's shape is settled.
**NOT figured out (this is why we keep experimenting):**
1. **FAITHFULNESS — the make-or-break.** Graph-backed S2P-INV-0003 returned `refer_to_specialist@0.72`, but ground truth is `auto_approve@0.947`. `match_status` 0.1 vs 0.953 and `tax_reg` 0.15 vs 0.938 diverge hard. We *assume* "incomplete seed properties" — unproven. It could also be **fixture values ≠ the SQLite source** (e.g. seeded `exception_rate=0.04` vs baseline 0.033), which would mean the migration must replay from `s2p.db`, not the JSON fixtures. Cause unknown → must be diagnosed empirically.
2. **Population faithfulness** — one invoice proves nothing about the population across categories/actions.
3. **Density at TRUE scale** — Phase B used 500 synthetic hubs on one invoice; the real `soc_graph` has 25,892 S2P Decisions and every invoice is a hub. Query speed + index necessity unproven at that scale.
4. **Duplicate correctness** — Phase B's duplicate lookup returned 0 (no siblings). The positive case (siblings present → correct non-zero DuplicateScore) is untested.
5. **Migration safety on a real clone** (Phase C) and **full PW** (Phase D) — not yet run.

---

## EXECUTION ORDER (interleaved experiment + implement — the roadmap)
1. **IMPLEMENT Track 2** (proven, S2P-scoped, independent of faithfulness). Ship the reader methods + normalization + tests per the spec. Safe now; does not touch other copilots.
2. **EXPERIMENT — Phase E (faithfulness): CRITICAL, gates the migration.** Diagnose why factors diverge, iterate to faithful, prove it across the population, and settle the authoritative source (fixtures vs SQLite). **If E can't reach faithfulness, stop and rethink FIX-B — do not build the migration.**
3. **EXPERIMENT — Phase B2 (true-scale density)** on a `soc_graph` clone: confirm the directed query stays fast and the index earns its place at 25,892 Decisions.
4. **EXPERIMENT — Phase F (duplicate correctness):** seed siblings, confirm DuplicateScore fires a correct non-zero.
5. **IMPLEMENT Track 1** migration — built around E's proven property set + authoritative source.
6. **EXPERIMENT — Phase C (migration safety)** on a `soc_graph` clone (v4 PROMPT C).
7. **IMPLEMENT — migrate `soc_graph`** (dry-run → apply → verify).
8. **VALIDATE — Phase D (full PW)**: green + graph-backed + faithful + off-path link (v4 PROMPT D + the faithfulness gate).
Any experiment failing short-circuits the rest — iterate in-sandbox, never advance on red. Steps 1 and 2 can run in parallel (different surfaces).

---

## PROMPT E — Faithfulness diagnosis & achievement (run first among experiments)
```
TASK: S2P FIX-B — Phase E (faithfulness). Report-only on committed source; disposable AGE graphs only; never write soc_graph; drop after.
GOAL: prove the graph-backed score can reproduce GROUND TRUTH, and find exactly what data achieves it. Phase B showed graph-backed S2P-INV-0003 = refer_to_specialist@0.72 (match_status 0.1, tax_reg 0.15) vs ground_truth_action='auto_approve' and SQLite baseline auto_approve@0.947. Use the Phase B winning directed query + the A′ wrapper to seed a protocol_v2_test_s2p_active_<uuid> sandbox.

E1 — per-factor divergence diagnosis (for match_status, amount_variance_ratio, duplicate_score, supplier_exception_history, tax_regulatory_compliance):
  a. Read the factor in factors.py; list the EXACT neighbor label + property keys it reads.
  b. Query the seeded node for those keys; record present/absent/value.
  c. Get the SQLite path's value for the same factor + invoice (run the SQLite score for S2P-INV-0003, or read s2p.db).
  d. Classify each divergence: MISSING property | WRONG/absent value | SOURCE MISMATCH (fixture value != SQLite value).
  REPORT the per-factor cause table. This decides whether the fix is "add properties" or "seed from s2p.db instead of the JSON fixtures."

E2 — iterate to faithful (S2P-INV-0003):
  Apply the E1 fix (add the missing properties from the authoritative source; if E1 shows source mismatch, seed the entities' factor properties from s2p.db, not the fixtures). Re-run the directed query + compute_all_factors. Repeat until all 7 factors match the SQLite baseline within tolerance (auto_approve@~0.947; match_status~0.953, tax_reg~0.938, etc.).
  REPORT: the COMPLETE per-label property set + the authoritative source that achieves faithfulness, and how many iterations it took.

E3 — population faithfulness:
  Sample >=15 invoices spanning categories and ground-truth actions (auto_approve / refer_to_specialist / reject / hold as available). Seed them with the E2 recipe. Graph-backed score each; compare action to ground_truth_action and the factor vector to the SQLite path.
  REPORT: faithfulness rate (% action-match), any systematic misses by category/factor, and whether the E2 property set generalizes. GATE: >=95% action-match, or diagnose the misses.

VERDICT: is faithful graph-backed scoring achievable, with what property set and source? Drop sandboxes; revert any scratch; soc_graph untouched.
```

## PROMPT B2 — True-scale density (soc_graph clone)
```
TASK: S2P FIX-B — Phase B2 (density at production scale). Report-only; sandbox = a CLONE of soc_graph; never write real soc_graph; drop after.
SETUP: Clone soc_graph (all ~25,892 S2P Decisions) [resolve clone mechanism]; seed the E2 faithful entity set into it so every invoice is a real DECIDED_ON hub; create the Invoice.invoice_id AGE index (DDL: CREATE INDEX ON "<graph>"."Invoice" USING btree (agtype_access_operator(VARIADIC ARRAY[properties,'"invoice_id"'::agtype]))).
TRIALS: for >=5 invoices, time the directed query MATCH (e:Invoice {invoice_id:'…'})-[]->(n) WHERE n.domain='s2p' RETURN n LIMIT 100 (cold+warm) WITH and WITHOUT the index; EXPLAIN to confirm index use. Confirm each returns exactly its entity neighbors (no Decision-hub crowding) at full scale.
REPORT: latencies, index-used yes/no, whether the index is necessary at 25,892 Decisions, any invoice whose neighbors are crowded. Drop the clone.
```

## PROMPT F — Duplicate correctness (positive case)
```
TASK: S2P FIX-B — Phase F (duplicate correctness). Report-only; disposable graph; never write soc_graph; drop after.
SETUP: In a protocol_v2_test_s2p_active_<uuid> sandbox seeded with the E2 faithful set, ensure a supplier has 2-3 near-duplicate invoices (similar amounts within the duplicate window).
TRIALS: run query_duplicate_context(target_invoice, supplier_id, amount, limit=20); confirm it returns the sibling(s). Feed the result to DuplicateScore; confirm a correct NON-zero value (compare to the SQLite path's duplicate_score for the same invoice).
REPORT: siblings returned, the duplicate_score graph vs SQLite, and the chosen window's effect. Confirm bounded. Drop the sandbox.
```

*(Phase C and Phase D prompts: `s2p_fix_b_whatif_experiments_v4.md`. D adds the faithfulness gate from the spec.)*

## After the experiments
E fixes the migration's data contract (property set + source) and B2/F fix the query/duplicate policy; fold those into Track 1 before building it. C proves safety on a clone; then migrate; D is the final green-and-faithful gate. Keep the loop: if any phase surprises us, spike the fix in a sandbox before changing the plan.

## Provenance
The faithfulness divergence (baseline vector vs ground truth) is from `s2p_fix_b_whatif_phase_b_results_v1.md`; the fixture-vs-SQLite source suspicion is Claude's read of the divergent values (exception_rate 0.04 vs 0.033) — E1 confirms or refutes it. Query shape, index DDL, and store chain are from Phase B. Live scale (25,892 Decisions) is from `s2p_entity_model_scan_v1.md`. Ground truth (`ground_truth_action`) is a seeded Invoice property observed in A′/B.
