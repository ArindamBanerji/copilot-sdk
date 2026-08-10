# S2P FIX-B — Next Experiments (Solution-Ladder Structured) v2

**Date:** 2026-08-04
**Supersedes:** `s2p_fix_b_next_experiments_dataops_audit_pathA_v1.md` (adds the solution-ladder structure + gating + pre-staged S4/S5/S6 fallbacks).
**Type:** Spike-first. Report-only on committed source except where a step says IMPLEMENT; scratch patches reverted; never write live `soc_graph`; sandboxes/clones dropped after; all perturbation/faithfulness work targets the ACTIVE compute path (not legacy/template/fixture modes).

## Where we are on the solution ladder
S2P scoring should be graph-driven. Candidate solutions, ordered cheap→expensive and aligned→retreat:
| Rung | Solution | Status |
|---|---|---|
| S1 | Data-only (migrate entities) | **FAILED** (read rejects rows; stubs remain) |
| S2 | + bespoke read fix (Track 2: directed query + normalization + duplicate) | **PARTIAL** — genuinely graph-backed, but 2 stub factors → wrong decisions |
| **S3** | + real graph-native MatchStatus/Tax + correct data-contract shapes | **NEXT — DECISIVE** (Exp 3) |
| S4 | Hybrid: graph factors + the 2 stub factors from event fields | pre-staged fallback |
| S5 | Event-field S2P (all factors from request fields) | pre-staged fallback |
| S6 | Passthrough materialized vectors (Path B) | last resort |
S1/S2 done. **S3 is the decisive rung** — the only one delivering "the graph genuinely drives correct S2P decisions." S4/S5/S6 are pre-defined so a failed S3 drops deliberately, not improvised.

## Execution order & gate
1. **Exp 1 — DataOps perturbation** (platform data point; alongside).
2. **Exp 2 — Platform faithfulness audit** (validate/kill the platform-wide silent-default hypothesis; alongside; Exp 1 feeds it).
3. **Exp 3 = S3 — Path A solution spike** (critical path, decisive).
   - **S3 PASS** → commit Path A: build Track 1 migration with S3's property-shape contract + Track 2 (already proven) → then Phases C/D validation.
   - **S3 FAIL** → run **S4**; if S4 fails → **S5**; if S5 fails → **S6**.
Exp 1/2 run in parallel with Exp 3; they tell us whether the data-contract work is S2P-only or a platform program, but they don't block the S3 gate.

---

## PROMPT — Exp 1: DataOps perturbation (+ baseline faithfulness)
```
TASK: DataOps perturbation + baseline faithfulness, analogous to the SOC experiment. Report-only on committed source; disposable/scoped DataOps graph or clone; never write production; drop after.
CONTEXT: DataOps scores via bespoke typed graph (DataOpsGraphClient): impact_scope reads PipelineSystem FEEDS topology; downstream_urgency reads PipelineSystem.sla_minutes across FEEDS; business_criticality/source_reliability read PipelineSystem props; recurrence reads DataQualityAlert AFFECTS history (graph_queries.py:313-599). It has an explicit fixture mode.
1. Pick a target alert whose factors read graph props/topology. Record whether the run is in GRAPH mode or FIXTURE mode (a fixture-mode run proves nothing).
2. Baseline score; record the factor vector + action + confidence + per-factor provenance.
3. BASELINE FAITHFULNESS CHECK: for each graph-factor, does the baseline value reflect the REAL stored property, or a default? Read the stored value+shape (e.g. PipelineSystem.business_criticality) and check whether the factor reflects it. Note any silent default + shape mismatch (the SOC lesson).
4. PERTURB one graph input in the sandbox (PipelineSystem.business_criticality or sla_minutes, or add/remove a FEEDS edge). Re-score.
5. Confirm the corresponding factor MOVES and unrelated factors don't. Revert; drop the sandbox.
REPORT: graph-vs-fixture mode; both scores; which factor moved; per-factor baseline faithfulness with shape mismatches. VERDICT: DataOps graph-backed YES/NO; any silent-default factors.
```

## PROMPT — Exp 2: Platform faithfulness audit (validate the hypothesis)
```
TASK: Platform faithfulness audit across graph-consuming copilots (SOC, DataOps, S2P). Read-only + disposable-graph reads; no production writes. GOAL: test "real stored graph values silently default before reaching factors, platform-wide."
FOR EACH graph-factor in SOC (asset_criticality, threat_intel_enrichment, pattern_history), DataOps (impact_scope, source_reliability, recurrence_frequency, downstream_urgency, business_criticality), S2P (match_status, amount_variance, duplicate, supplier_exception, payment_terms, commodity, tax):
1. EXPECTED SHAPE: what property does the factor read + what shape/type does it expect (categorical string / numeric range / presence)?
2. ACTUAL SHAPE: what shape/type is the property actually stored as? Match or mismatch?
3. FAITHFULNESS PROBE: on a real target, does the factor output reflect the real stored value or a default? (read + expected-mapping comparison, like SOC's 0.8→0.5; perturb where needed.)
4. CLASSIFY: FAITHFUL / SILENT-DEFAULT / STUB.
REPORT: per-copilot × per-factor table + classification + the mismatch. SUMMARY: count of silent-default/stub of N graph-factors, per copilot + overall → validates or refutes the platform-wide hypothesis. Flag each silent-default as a data-contract fix.
```

## PROMPT — Exp 3 = S3: Path A solution spike (DECISIVE)
```
TASK: S3 — design + prove real graph-native MatchStatus + TaxRegulatoryCompliance, modeled on SOC's pattern (bespoke typed read of concrete props → continuous value), avoiding SOC's numeric/string data-contract gap. Report-only on committed source; scratch factor code + disposable graph; drop/revert after.
DESIGN (define "correct" from procurement domain logic; the fixture vector is NOT an oracle):
- MatchStatus (real 3-way match): read Invoice.amount, PurchaseOrder.amount, GoodsReceipt.qty_received/amount → continuous match score (e.g. 1 - normalized max discrepancy), high when aligned. Specify required property shapes.
- TaxRegulatoryCompliance (real compliance): read Contract compliance/clause/threshold fields (define which) → continuous compliance score from actual terms vs invoice. Specify shapes.
SPIKE (disposable protocol_v2_test_s2p_active_<uuid>):
1. Seed Invoice/PO/GR/Contract with CORRECT property shapes + realistic values; verify shapes match what the new factors read (no silent default).
2. Patch the 2 factors (scratch) to the new formulas; compute all 8 factors via the Track-2 directed query.
3. PERTURB each new factor's input (change PO.amount to create a mismatch; change a compliance field); confirm the factor moves continuously + in isolation.
4. SOFT SANITY (not oracle): for a sample across categories, are decisions DEFENSIBLE (well-matched compliant → auto_approve-ish; mismatch/non-compliant → refer/reject)? Use ground_truth_action as directional only.
REPORT: the 2 factor formulas + required property shapes; perturbation results; sample decisions vs directional expectation. VERDICT: is faithful graph-native S2P scoring ACHIEVABLE (Path A viable)? Revert; drop.
```

---

## PRE-STAGED FALLBACKS — run ONLY if the prior rung fails

### PROMPT — S4: Hybrid (trigger only if S3 fails)
```
TRIGGER: S3 could not make MatchStatus and/or Tax faithful from graph data.
TASK: S4 spike — keep the working graph factors; move ONLY the failing factor(s) to EVENT-FIELD inputs (the score request/metadata supplies the match and/or compliance data), like Trading/Purchasing. Report-only; scratch + disposable graph; revert/drop.
1. Define the request fields the caller would supply for the moved factor(s) (e.g. match_status inputs: po_amount, gr_qty; compliance inputs: tax_terms) — and where they'd come from operationally.
2. Patch the moved factor(s) to compute from request fields; keep commodity/supplier/amount/duplicate/payment on the Track-2 graph read.
3. Score a sample; confirm the moved factors compute correctly from the request AND the graph factors still work; decisions defensible.
REPORT: which factors moved to event-field, the request contract, sample decisions. VERDICT: is hybrid faithful + operationally sane? If yes → S4 is the fix (partial graph value). If no → S5.
```

### PROMPT — S5: Event-field S2P (trigger only if S4 fails)
```
TRIGGER: hybrid still can't produce faithful decisions, or graph data is broadly unreliable.
TASK: S5 spike — compute ALL S2P factors from request fields (Trading/Purchasing pattern); entity graph becomes context/audit only, not scoring. Report-only; scratch + disposable; revert/drop.
1. Define the full request-field contract for all 8 factors (what the caller supplies).
2. Patch the S2P factor registry to compute from the request (no graph traversal for scoring).
3. Score a sample; confirm decisions defensible without graph reads; measure latency (should be fast, no traversal).
REPORT: the request contract, sample decisions, latency. VERDICT: is event-field S2P faithful + acceptable (concedes graph-as-scoring-source)? If no → S6.
```

### SPEC — S6: Passthrough materialized vectors (last resort)
```
TRIGGER: genuine graph-native and event-field scoring both infeasible.
TASK (spec, not spike): persist the materialized factor vectors as decision-level properties; the score path reads them with explicit provenance='materialized, not recomputed'. The entity migration (Track 1) becomes context/audit only. Document honestly that the graph does not drive S2P scoring under S6.
```

## What each decides
- Exp 1: DataOps graph-backed or not; silent-default present? (3rd data point.)
- Exp 2: is the silent-default gap S2P-only or platform-wide (a count)? → S2P fix vs platform program.
- Exp 3 (S3): is Path A achievable? Produces the real factor formulas + property-shape contract for Track 1. **The gate.**
- S4/S5/S6: the ordered retreat if S3 fails — hybrid, then event-field, then passthrough.

## After the gate
- **S3 PASS** → Claude writes the finished two-track FIX-B spec: Track 1 migration with S3's property-shape contract + orphan reconcile + index; Track 2 (proven); the 2 real factors. Then Phases C (migration safety on clone) + D (full PW green + graph-backed + faithful). Put the spec in `copilot-sdk/docs/design/`.
- **S3 FAIL** → the surviving fallback (S4/S5/S6) defines a smaller spec.

## Provenance
Ladder + rung verdicts from `s2p_solution_ladder_v1.md`. S1/S2 from `phase_a_prime`/`phase_b` results; stub/no-oracle from `phase_e`; event-field pattern (S4/S5) from `platform_factor_architecture_scan_v1.md`; data-contract trap from `soc_perturbation_experiment_v1.md`; directed Track-2 query from `phase_b`.
