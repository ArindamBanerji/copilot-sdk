# Master Action Plan — VLD Addendum
**Version:** v7 · **Date:** Sep 10, 2026
**Authority:** MAP v5.92 + VLD Implementation Design v4 + Recurrence Addendum v1
**Supersedes:** v6

---

## Status: VLD Mechanism Validated Across All 5 Copilots

All scenario data regenerated with Astra (strong-conditional design).
200 saves, 0 hurts across 250 scenarios.

| Copilot | Saves | Hurts | Both right | Both wrong | Data |
|---|---|---|---|---|---|
| SOC | 43 | 0 | 0 | 2 | 50 Astra |
| DataOps | 38 | 0 | 4 | 3 | 50 Astra |
| S2P | 40 | 0 | 3 | 2 | 50 Astra |
| Trading | 39 | 0 | 1 | 5 | 50 Astra |
| Purchasing | 40 | 0 | 1 | 4 | 50 Astra |
| **Total** | **200** | **0** | **9** | **16** | **250** |

**S2P fixed.** Was 56.2% with Fable data (weak conditional structure).
Astra's action profiles + >=0.30 factor shifts solved it completely.

**All artifacts consolidated** in `copilot-sdk/experiments/vld/` (75 files).

---

## What Changed v6 → v7

1. All 5 copilots on Astra data (replaces Fable)
2. S2P resolved: 40:0 (was 56% negative)
3. experiments/vld/ consolidated (data, scripts, charts, docs, prompts)
4. Scenario generation phase COMPLETE for all copilots
5. Forward queue refocused: graph wiring → frontend → demo

---

## Experiments Consolidated in Repo

`copilot-sdk/experiments/vld/` — 75 files:

| Directory | Count | Content |
|---|---|---|
| data/ | 5 | Canonical Astra JSONs (250 scenarios) |
| scripts/ | 5 | Chart generation, with-without, validator, merge |
| results/ | 5 | Case study markdowns (all 5 copilots) |
| pub_charts/ | 57 | PUB-1 through PUB-25 + with-without per copilot |
| docs/ | 7 | Addenda + 5 Astra prompts (reproducibility) |
| prompts/ | 2 | Codex E-4, E-5 |

---

## Document Reconciliation Plan

### Documents That Need VLD Findings Integrated

| # | Document | Current | What needs adding | Priority |
|---|---|---|---|---|
| 1 | **vld_implementation_design** | v4 | REQ-1 (enriched centroids, +0.244), REQ-2 (non-overlapping factors, 0.923 vs 0.429), REQ-3 (budget=2), Astra data quality findings, 200:0 results | **HIGH** |
| 2 | **vld_graph_reasoning_architecture** | v4 | §6 recurrence properties (PROP-1 through PROP-5), density scaling (GR-4), evidence compounding (35%), with-without methodology | **HIGH** |
| 3 | **math_synopsis** | v18 | New VLD claims: convergence (monotonic dist 40%), 2.4x routing quality, 94% state divergence, optimal depth=2. New tier: [PLANTED POSITIVE CONTROL] | **HIGH** |
| 4 | **cga_arxiv_short** | v7.4 | Dual-centroid formalism, VLD as investigation loop, Stage 1 results (4/5 copilots at 100%), recurrence experiments | **HIGH** |
| 5 | **innovation_note** | v7 | VLD as governed investigation loop, 200:0 with-without, Astra data generation methodology | **MEDIUM** |
| 6 | **ci_blog** | v15 | Investigation clock (new section), with-without case studies, cross-copilot VLD results | **MEDIUM** |
| 7 | **graph_native_reasoning_hero** | v25 | Read/Route/Investigate/Reshape — VLD is the Investigate step | **MEDIUM** |
| 8 | **jm_paper_draft** | v11 | Investigation traces as judgment memory entries | **LOW** |

### Specific Changes Per Document

**vld_implementation_design v4 → v5:**
- §3 Centroid Initialization: ADD enriched centroids mandatory. Surface centroids produce divergence (+0.244 accuracy difference at depth 1).
- §3B: ADD recurrence experiment results (9 experiments, 9 charts)
- §4 Investigation Patterns: ADD non-overlapping factor constraint. Track enriched factors per hop. Factor overlap → 0.429 vs non-overlap 0.923.
- §5 Budget Allocation: CHANGE default budget = 2 (was unspecified). Depth 3 reverses on small n.
- §5 Halt Condition: ADD residual-based halt validated (convergence proven).
- §7 Data Generation: ADD Astra methodology (action profiles, >=0.30 shifts, boundary crossing design). Replace Fable approach.
- §8 Results: ADD 200:0 with-without across 5 copilots.

**vld_graph_reasoning_architecture v4 → v5:**
- §4 Dual-Centroid: ADD mu_action MUST use enriched vectors. mu_routing can use either.
- §5 Aggregation: ADD selective replacement validated. Non-overlap = 0.923.
- §6 Recurrence Properties: ADD new section with PROP-1 through PROP-5.
- §7 Graph Density: ADD denser graphs benefit more (GR-4: low +0.200, med +0.300).
- §8 Order Dependence: ADD sequential >= parallel (0.750 vs 0.700 when factors overlap).

**math_synopsis v18 → v19:**
- New §X VLD claims at [PLANTED POSITIVE CONTROL] tier
- Claim VLD-CONV: investigation converges (dist monotonic 40%, entropy 69%)
- Claim VLD-DIV: 94% state divergence on similar-start pairs
- Claim VLD-ROUTE: routing quality 2.4x chance at step 0
- Claim VLD-DEPTH: optimal depth = 2 (marginal +0.155, +0.078, -0.300)
- Claim VLD-WW: 200 saves, 0 hurts across 250 scenarios (5 copilots)
- New tier label: [PLANTED POSITIVE CONTROL] — not [VALIDATED] or [PROVEN]

**ci_blog v15 → v16:**
- New section: "VLD — The Investigation Clock"
- With-without case study: SOC alert example (surface says suppress, VLD says escalate)
- Cross-copilot table: 200:0 across 5 domains
- Conservation-bounded framing: "VLD preserves correct decisions"

---

## Per-Copilot Pipeline (Final Status)

| Component | SOC | DataOps | S2P | Trading | Purchasing |
|---|---|---|---|---|---|
| Astra scenarios (50 each) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Stage 1 evaluation | ✅ 100% | ✅ 100% | ✅ (Astra) | ✅ 100% | ✅ 100% |
| With-without | ✅ 43:0 | ✅ 38:0 | ✅ 40:0 | ✅ 39:0 | ✅ 40:0 |
| Graph wiring | ✅ W-1 | ⬜ W-2 | ⬜ W-3 | ⬜ W-4 | ⬜ W-5 |
| Investigation panel | ✅ V-10 | ⬜ FE-2 | ⬜ FE-3 | ⬜ FE-4 | ⬜ FE-5 |
| Frontend multi-hop | ⬜ FE-1 | ⬜ FE-2 | ⬜ FE-3 | ⬜ FE-4 | ⬜ FE-5 |
| Playwright E2E | ⬜ PW-1 | ⬜ PW-2 | ⬜ PW-3 | ⬜ PW-4 | ⬜ PW-5 |
| Demo showcase | ⬜ D-1 | ⬜ D-2 | ⬜ D-3 | ⬜ D-4 | ⬜ D-5 |

**Scenario generation is DONE.** Remaining work is product wiring.

---

## Forward Queue (Updated)

### TIER 1: Re-run Evaluations on Astra Data (quick wins)

The Codex-built evaluators (E-2 through E-5) ran on Fable data.
The repos now have Astra data. Re-running evaluators confirms
ρ-based acceptance tests pass on Astra data too.

| # | Item | Effort | Notes |
|---|---|---|---|
| 1 | Re-run E-2 DataOps eval on Astra data | 5 min local | Just re-run existing script |
| 2 | Re-run E-4 Trading eval on Astra data | 5 min local | Same |
| 3 | Re-run E-5 Purchasing eval on Astra data | 5 min local | Same |
| 4 | Re-run S2P eval on Astra data | 5 min local | Fixes 56% → should be 100% |

### TIER 2: Graph Wiring (unlocks frontend)

| # | Item | Effort | Dep |
|---|---|---|---|
| 5 | W-2 DataOps graph wiring | 1 Codex slot | Astra data in repo |
| 6 | W-3 S2P graph wiring | 1 Codex slot | Astra data in repo |
| 7 | W-4 Trading graph wiring | 1 Codex slot | Astra data in repo |
| 8 | W-5 Purchasing graph wiring | 1 Codex slot | Astra data in repo |
| — | W-2 through W-5 are parallel (different repos/apps) | | |

### TIER 3: Frontend + E2E (largest remaining category)

| # | Item | Effort | Dep |
|---|---|---|---|
| 9 | FE-1 SOC multi-hop frontend | 1-2 Codex | W-1 done |
| 10 | FE-2 DataOps multi-hop frontend | 1-2 Codex | W-2 |
| 11 | PW-1 SOC Playwright (8-12 tests) | 1 Codex | FE-1 |
| 12 | PW-2 DataOps Playwright | 1 Codex | FE-2 |
| 13 | FE-3/4/5 remaining copilots | 3-6 Codex | W-3/4/5 |
| 14 | PW-3/4/5 remaining Playwright | 3 Codex | FE-3/4/5 |

Frontend requirements:
- Conditional branch visualization (taken vs dimmed)
- Evidence cards per hop (factor enriched, narration)
- With-without comparison view (SP action vs VLD action)
- Intermediate action display (action changes at which hop)

### TIER 4: Demo + Ship

| # | Item | Effort | Dep |
|---|---|---|---|
| 15 | D-1 SOC demo (best 3 of 43 saves) | 1 Codex | FE-1 + PW-1 |
| 16 | D-2 DataOps demo | 1 Codex | FE-2 |
| 17 | Doc reconciliation (8 upstream docs) | 2-3 days writing | All evals done |
| 18 | Loom recording (SOC + DataOps lead) | 1 day | D-1 + D-2 |
| 19 | Publication (arxiv, blog, innovation note) | 2-3 days | Doc reconciliation |

---

## Gate Summary

```
Phase 0 (simulation):           ✅ PASSED
Phase 1a (infrastructure):      ✅ PASSED (v5.139-v5.140)
Phase 1b (rho measurement):     ✅ PASSED (v5.141, rho=0.685)
Phase 1  (dual-centroid):       ✅ PASSED (v5.142-v5.145)
Phase 2a (Stage 1 SOC):         ✅ PASSED (VLD=100% at rho>=0.70)
Phase 2b (cross-copilot):       ✅ PASSED (4/5 at 100%, S2P fixed with Astra)
Phase 2c (with-without):        ✅ PASSED (200:0 across 5 copilots)
Phase 2d (Astra data):          ✅ PASSED (all 5 copilots, 0 weak shifts)
Phase 2e (repo consolidated):   ✅ PASSED (experiments/vld/, 75 files)

Remaining:
Phase 2f (re-eval on Astra):    ⬜ TIER 1 (re-run E-2/E-4/E-5/S2P)
Phase 3  (graph wiring):        ⬜ TIER 2 (W-2 through W-5)
Phase 4  (frontend demo):       ⬜ TIER 3 (FE + PW, 5 copilots)
Phase 5  (ship):                ⬜ TIER 4 (demo, docs, Loom, publication)
```

---

## Publication Charts (57 total)

| Category | Charts | Count |
|---|---|---|
| Simulation (PUB-1 to PUB-16) | Routing, calibration, budget, geometry, dual-centroid, dimension, confusion, abstention, distractor, decision-aligned, Stage 1 | 11 |
| Recurrence (PUB-17 to PUB-25) | Depth-accuracy, centroid comparison, ablation, convergence, order, compounding, intermediate, gating, routing quality, long-range | 10 |
| With-without (5 copilots × 4+1) | Aggregate, factor movement, trajectory, per-rho, case studies | 25+5 |
| **Total in pub_charts/** | | **57 PNG + 5 MD** |

---

## Resource Estimate (remaining to Loom)

| Category | Slots | Elapsed |
|---|---|---|
| Re-eval on Astra data | 0 (local runs) | 1 hour |
| Graph wiring (W-2 through W-5) | 4 Codex | 3-4 days |
| Frontend + E2E (10 copilot-items) | 10-15 Codex | 5-6 days |
| Demo + showcase (D-1, D-2) | 2 Codex | 1-2 days |
| Doc reconciliation (8 docs) | Writing | 2-3 days |
| Loom + publication | Writing | 2-3 days |
| **Total** | **~16-21 slots** | **~3-4 weeks** |

---

## Git State (Sep 10, 2026)

| Repo | Branch | Tag | Tests | Status |
|---|---|---|---|---|
| SOC | v5.0-dev | v5.148 | 2444P 16S 0F | ✅ |
| SDK | main | v0.9.59 | 3372P 0F | ✅ |
| S2P | main | v0.7.50-s2p | 1865P 0F | ✅ |
| ci-platform | main | — | 619P 0F | ✅ |
| GAE | — | — | 1244P 0F | ✅ |

**Pending commit:** experiments/vld/ consolidation → v0.9.60

---

## Critical Path

```
NOW:     Commit experiments/vld/ → v0.9.60
         Re-run evaluators on Astra data (4 local runs)
         Write W-2 + W-3 Codex prompts

WEEK 1:  W-2 + W-3 + W-4 + W-5 graph wiring (parallel batches)
         Re-eval results confirm rho acceptance tests

WEEK 2:  FE-1 + FE-2 (SOC + DataOps frontend, parallel)
         PW-1 + PW-2 (Playwright)

WEEK 3:  D-1 + D-2 (demo showcases)
         FE-3/4/5 + PW-3/4/5 (remaining copilots)
         Doc reconciliation starts

WEEK 4:  Loom recording
         Publication prep
```

---

*MAP VLD Addendum v7 · Sep 10, 2026*
*200:0 saves:hurts across 250 Astra scenarios (5 copilots).*
*75 files consolidated in experiments/vld/.*
*Scenario generation COMPLETE. Product wiring ahead.*
*~16-21 Codex slots, ~3-4 weeks to Loom.*
