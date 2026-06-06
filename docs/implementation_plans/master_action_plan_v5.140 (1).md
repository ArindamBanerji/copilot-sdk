# MAP v5.140 — Comprehensive Queue (June 1, 2026)
**From:** v5.139 + Batch 11 Code Analysis + Governed Graph Exec Plan v1.0 + L5 Design Spec v5.0
**Change (v5.140):** 2 DROPs (#55, #98), 9 new active items (#111-#119), conservation ghost fix discovered (CONS-V-FIX #111 is new P0). L3→L5 graph execution plan integrated as tracked items. Batch 11 prompts 1-7 WRITTEN. 6 standing rules (#48 replaced persist-before-cache, #49-#53 added). Cumulative DONE: 42. Active: 55. Standing rules: 53. Forward 40-prompt sequence defined.

---

## Platform State (Post Batch 11 Analysis)

| Repo | Tests | Status |
|---|---|---|
| SDK root | **915** | ✅ (4 failing — BUG-003/004/005) |
| Trading BE | **727** | ✅ |
| Purchasing BE | **168** | ✅ |
| DataOps BE | **176** | ✅ |
| S2P BE | **926** | ✅ (2 collection errors — BUG-006) |
| SOC BE | **~1,742** | ✅ |
| ci-platform | **350** | ✅ |
| **Total** | **~6,241** | **98.9% healthy** |

### Playwright Status
**⚠️ PRE-Batch-10 FE baseline.** Rerun needed after B10 FE + B11 conservation fix.

| Suite | Pass | Fail | Flaky | Status |
|---|---|---|---|---|
| Trading | 106 | 1 | 4 | ⚠️ Pre-B10 FE |
| DataOps | 96 | 1 | 1+1skip | ✅ |
| Purchasing | 47 | 0 | 0 | ✅ |
| S2P Preview | 11 | 0 | 0 | ✅ |
| **Total** | **260** | **2** | **5+1skip** | **99.2%** |

### Conservation Ghost Problem (CRITICAL — discovered in Batch 11)

Live scan reveals ALL SDK copilots permanently RED due to pending ghost decisions:

| Copilot | total_decisions | verified | pending ghosts | Status |
|---|---|---|---|---|
| Trading | 642 | 40 | 602 (94%) | 🔴 RED |
| DataOps | 575 | 20 | 555 (97%) | 🔴 RED |
| Purchasing | 520 | 20 | 500 (96%) | 🔴 RED |
| S2P | 39 | 27 | 12 (31%) | 🔴 RED |

Root cause chain: Bundle shape mismatch (Trading d=7 vs d=10) → cold start → live demo scoring accumulates unverified decisions → conservation V inflated by pending ghosts → θ_min impossibly high → permanently RED.

**Fix: #111 CONS-V-FIX (P0) + #102 BUNDLE-REGEN (P0). Together they fix both symptom (wrong V) and cause (bundle mismatch).**

### Canonical Tensor Reference (unchanged)

| Copilot | Tensor | C | A | D | Values | penalty_ratio |
|---|---|---|---|---|---|---|
| SOC | (6,4,6) | 6 | 4 | 6 | 144 | 20.0 |
| S2P | (5,5,7) | 5 | 5 | 7 | 175 | 5.0 |
| **Trading** | **(5,4,10)** | 5 | 4 | **10** | **200** | 3.0 |
| Purchasing | (5,4,7) | 5 | 4 | 7 | 140 | 3.0 |
| DataOps | (6,5,6) | 6 | 5 | 6 | 180 | 10.0 |

---

## v5.140 Changes — DROPs (2 items → DONE)

| MAP# | ID | Was | Evidence |
|---|---|---|---|
| **#55** | **SOC-TAB5** | 2d | Batch 11 F8: headline, metrics, what_changed all live. Full endpoint + frontend confirmed. |
| **#98** | **PW-DATAOPS-FLOWS332** | 15min | Batch 11 F3: `source_copilot: "SOC"` already present in startup seed metadata at main.py:247. |

## v5.140 Changes — New Items (9 items)

| MAP# | ID | Effort | Repo | What | Source |
|---|---|---|---|---|---|
| — | **BUGFIX-PRELUDE** | 20min | SDK+S2P | BUG-003 (sqlite_store return type) + BUG-004 (factory cast) + BUG-006 (S2P supplier path). 3 bugs, 3 files, ~5 lines total. Must ship before P1. | **WRITTEN** |
| **#111** | **CONS-V-FIX** | 0.5d | SDK+S2P | V = verified only. Replace count_decisions with count_verified_decisions in conservation paths. | Batch 11 F7 |
| **#112** | **PUR-AE-VARIANTS** | 0.5d | SDK | Purchasing VariantSpec: waste_threshold + lead_time_buffer families. | PD v1.3 + gap analysis |
| **#113** | **GP-MYPY-FIX** | 2h | SDK | Fix 4 GraphStore broad failures: sqlite_store.py:904 return type, factory.py:175 return type, 2 structural protocol tests. | Exec plan A1 |
| **#114** | **OUTBOX-QUARANTINE** | 1.5d | SDK | Outbox + quarantine tables per L5 Design Spec v5.0 §2.2. Full schema incl. domain, causal_decision_id, attempt_count, last_error_redacted, schema_version. 3 idempotency classes (A/B/C). Replay ordering: Class B before Class A. Unblocks 4 OUTBOX_PENDING conformance tests. | Exec plan B4 |
| **#115** | **OBSERVATION-WIRING** | 0.5d | S2P | Preview score → write_observation (not write_decision). Eliminates ghost decisions from preview scoring. | Exec plan B1 |
| **#116** | **EVIDENCE-RECEIPT-WIRING** | 1d | S2P | Learn/outcome → append_evidence_receipt. Hash chain audit trail. Receipt BEFORE outcome write. | Exec plan B2 |
| **#117** | **DATAOPS-AGE-ACTIVE** | 1.5d | SDK | DataOps scorer AGE adoption. graph_status.py. Operational separation guard. ~30 new tests. | Exec plan A2 |
| **#118** | **DEMO-AGE-OPS** | 1d | SDK | Per-copilot `--{app}-graph-backend` flags in demo.py. Status output. DSN redaction. | Exec plan A5 |
| **#119** | **L5-JM-GRAPH** | 8d | SDK+CI+S2P | Centroid + DKWeight + ConservationState as AGE nodes via **L5LearningStore protocol**. **18** conformance tests (42-59). Score/learn → persist-before-cache model. Decision identity (domain, decision_id). complacency_flag as TEXT. Full spec: L5 Design Spec v5.0 + Governed Graph Exec Plan v1.0 (C1-C9). | Exec plan C1-C9 |

---

## Cumulative DONE — All Versions (42 items)

| Version | Items | MAP Numbers |
|---|---|---|
| v5.136 | 13 | #12, #14, #18, #20, #25, #26, #28, #29, #31, #35, #45, #53, #54 |
| v5.137 | 4 | #16, #90, #91, #93 |
| v5.138 Batch 10 | 11 | #19, #21, #22, #30, #40, #42, #44, #46, #51, #89, #97 |
| v5.138 DEMO-BUNDLE | 3 | #99, #100, #101 |
| v5.139 DROPs | 8 | #47, #48, #50, #58, #59, #60, #61, #92 |
| v5.139 immediate | 1 | #108 |
| **v5.140 DROPs** | **2** | **#55, #98** |
| **Total** | **42** | |

---

## Forward Queue — 55 Active Items

### Graph Storage Critical Path (L3 → L5)

These items — and ONLY these items — are required for Level 5 graph-storage completion. All other queue items are parallel feature backlog.

| Phase | MAP# | ID | Effort | Dep |
|---|---|---|---|---|
| **P0** | 111 | CONS-V-FIX | 0.5d | — |
| **P0** | 102 | DEMO-BUNDLE-REGEN-D10 | 15min | — |
| **L3** | 113 | GP-MYPY-FIX | 2h | — |
| **L3** | 117 | DATAOPS-AGE-ACTIVE | 1.5d | #113 |
| **L3** | 118 | DEMO-AGE-OPS | 1d | #117 |
| **L4** | 114 | OUTBOX-QUARANTINE | 1.5d | #113 |
| **L4** | 115 | OBSERVATION-WIRING | 0.5d | L3 complete |
| **L4** | 116 | EVIDENCE-RECEIPT-WIRING | 1d | #115 |
| **L5** | 119 | L5-JM-GRAPH | 8d | L4 complete |
| | | **Total graph-storage critical path** | **~14.5d** | |

Items NOT on this path (AE variants #104/#105/#107/#112, Trading TOD #106, S2P ranking #38, optimizer #49, receipt fields #103, contribution FE #56, multi-trader #27, S2P depth #39/#41/#43/#52, DI #62-#69, connectors, hardening) are parallel feature backlog. They can run simultaneously in separate Codex windows but MUST NOT block the graph-storage critical path.

### ⚡ Tier 0 — P0 Blockers (2 items — ship FIRST)

| # | ID | Effort | What | Why P0 | Prompt |
|---|---|---|---|---|---|
| **111** | **CONS-V-FIX** | 0.5d | Conservation V = verified only. Add count_verified_decisions to SQLiteGraphStore + InMemoryGraphStore. Update conservation_router.py + s2p.py. | ALL SDK copilots permanently RED (92-97% pending ghosts) | **P1 WRITTEN** |
| **102** | **DEMO-BUNDLE-REGEN-D10** | 15 min | Regenerate Trading bundle for d=10 factors | Trading d=7 bundle vs d=10 preset → flat centroids | **P2 WRITTEN** |

**Gate after P0:** Re-check live conservation across all 4 SDK copilots. Expect total_decisions to drop 90%+ and conservation to recover toward GREEN.

**P0 EXECUTION RULE:** No non-P0 Codex feature work (Tier 2+) may be sent to Codex until #111 and #102 are BOTH implemented and verified. Verification means: `curl http://localhost:{port}/api/conservation/status` for all 4 SDK copilots shows total_decisions matching verified count (not inflated by pending ghosts), and Trading cold-start restores d=10 centroids from bundle. This rule is absolute — not waivable for schedule pressure.

### Tier 1 — PW Gates (2 items)

| # | ID | Effort | Status |
|---|---|---|---|
| 15 | **SOC-PW-RERUN** | 0.5d | PENDING — run with S2P on port 8002 |
| 17 | **S2P-PW-RUN** | 0.5d | PENDING |

### Tier 2 — Quick Wins: AE Variants + Polish (8 items) · PARALLEL FEATURE BACKLOG
*Not required for Level 5 graph-storage completion. Can run in parallel Codex windows alongside graph-storage critical path.*

Platform-wide: every copilot has AgentEvolver pipeline but zero/partial domain-specific VariantSpec. Prompts 3-7 fix this across ALL copilots in 3d. Zero file overlap → parallel Codex windows.

| # | ID | Effort | What | Prompt |
|---|---|---|---|---|
| 105 | **TRD-AE-VARIANTS** | 0.5d | Trading AE: execution_threshold + revenge_cooldown families | **P3 WRITTEN** |
| 107 | **DOPS-AE-VARIANTS** | 0.5d | DataOps AE: auto_approve_threshold + scheduling_criteria | **P4 WRITTEN** |
| 112 | **PUR-AE-VARIANTS** | 0.5d | Purchasing AE: waste_threshold + lead_time_buffer | **P5 WRITTEN** |
| 104 | **S2P-AE-SUPPLEMENT** | 0.5d | S2P AE: add escalation_criteria + triage_weights, raise promotion_min_samples 10→50 | **P6 WRITTEN** |
| 27 | **TRD-MULTI-TRADER** | 0.5d | trader_id on NormalizedTrade + CSV aliases + metadata flow | **P7 WRITTEN** |
| 106 | **TRD-T3-TOD** | 1d | _detect_time_of_day pattern detector | P8 queued |
| 38 | **S2P-F8-RANKING** | 1d | Factor ranking endpoint + swap candidate | P9 queued |
| 49 | **S2P-F20-OPTIMIZER** | 1d | Centroid import endpoint + conservation gate | P10 queued |

### Tier 3 — S2P Features + Platform Polish (4 items) · PARALLEL FEATURE BACKLOG
*Not required for Level 5 graph-storage completion.*

| # | ID | Effort | What | Prompt |
|---|---|---|---|---|
| 103 | **S2P-RECEIPT-FIELDS** | 0.5d | OutcomeReceipt: 4 missing PD fields | P11 queued |
| 56 | **BACKLOG-CONTRIBUTION-FE** | 1d | FactorContributionChart shared component (backend done) | P12 queued |
| 113 | **GP-MYPY-FIX** | 2h | 4 GraphStore broad failures: return types + structural tests | P13 queued |
| 114 | **OUTBOX-QUARANTINE** | 1.5d | Outbox + quarantine per L5 v5.0 §2.2. Full schema + replay ordering (Class B before A). 3 idempotency classes. Unblocks 4 conformance tests. | P14 queued |

### Tier 4 — L3/L4 Graph Infrastructure (4 items)

These are the Governed Graph Execution Plan Phase A + B items. They enable L5 judgment memory.

| # | ID | Effort | What | Exec Plan | Prompt |
|---|---|---|---|---|---|
| 115 | **OBSERVATION-WIRING** | 0.5d | Preview → write_observation. Eliminate ghost decisions. | B1 | P15 queued |
| 116 | **EVIDENCE-RECEIPT-WIRING** | 1d | Learn → append_evidence_receipt. Hash chain audit. | B2 | P16 queued |
| 117 | **DATAOPS-AGE-ACTIVE** | 1.5d | DataOps scorer AGE adoption. graph_status.py. 30 tests. | A2 | P17 queued |
| 118 | **DEMO-AGE-OPS** | 1d | Per-copilot AGE flags in demo.py. | A5 | P18 queued |

**Manual gates embedded:** A3 (DataOps milestone review), A6-A8 (product smoke + PW + L3 proof) run between prompts as verification gates. Not tracked as separate MAP items.

### Tier 5 — L5 Judgment Memory (1 consolidated item)

| # | ID | Effort | What | Exec Plan | Prompt |
|---|---|---|---|---|---|
| 119 | **L5-JM-GRAPH** | 8d | Centroid + DKWeight + ConservationState as AGE nodes via **L5LearningStore protocol**. 18 conformance tests (tests 42-59). persist-before-cache model. Decision identity (domain, decision_id). complacency_flag TEXT. Full spec: L5 Design Spec v5.0 + Governed Graph Exec Plan v1.0 (C1-C9). | C1-C9 | P20-P28 |

**Sub-steps (from Governed Graph Execution Plan):**
- C1: Centroid node implementation (4-6h)
- C2: DKWeight node implementation, Welford state REQUIRED (3-4h)
- C3: ConservationState node + Option C (4-6h)
- C4a: SDK centroid integration — one change covers 4 copilots (1-2h)
- C4b: SOC centroid integration — separate due to triage.py complexity (3-4h)
- C5: DK + Conservation integration — explicit 5-step ordering (4-6h)
- C6: Startup read from AGE with fallback (3-4h)
- C7: Full learn flow integration test — edge assertions mandatory (2-3h)
- C8: L5 Playwright validation (2-3h)
- C9: Cross-copilot proof report (manual)

**Milestone: L5 COMPLETE. All 5 copilots with judgment memory in the graph.**

### Tier 6 — S2P Depth (4 items — unchanged)

| # | ID | Effort | What |
|---|---|---|---|
| 39 | **S2P-F10 FINANCIAL-IMPACT** | 1-2wk | Redesign: fixture → OutcomeReceipt source |
| 41 | **S2P-F14 LEAD-TIME** | 1-2wk | Per-supplier GR/PO lead time intelligence |
| 43 | **S2P-G12 SITUATION-ANALYZER** | 3-4wk | 47-node graph traversal — THE critical gap (S14) |
| 52 | **SP-12 S2P-NL-TRUST** | 2wk | Quality-aware NL for S2P |

### Tier 7 — DI Phase A (2 items — unchanged)

| # | ID | Effort | What |
|---|---|---|---|
| 62 | **DI-1 SOURCE-PROFILER** | 2wk | Data source profiling — closes 4 DataOps gaps |
| 63 | **DI-2 INTELLIGENCE-MAP-V1** | 2wk | Intelligence map visualization |

### Tier 8 — DI Phase B-C (6 items — unchanged)

| # | ID | Effort | What |
|---|---|---|---|
| 64 | DI-3 NL-QUERY-ENGINE | 3wk | Natural language query |
| 65 | DI-4 PROMPT-INTEGRATOR | 1wk | Prompt integration layer |
| 66 | DI-5 COMBINATION-DISCOVERY | 2wk | Cross-source pattern discovery |
| 67 | DI-6 IMPACT-ESTIMATOR | 2wk | Business impact estimation |
| 68 | DI-7 RECOMMENDATION-ENGINE | 2wk | Data acquisition recommendations |
| 69 | DI-8 ACQUISITION-ADVISOR | 2wk | Advisory dashboard |

### Tier 9 — DI Phase D (3 items — unchanged)

| # | ID | Effort |
|---|---|---|
| 70 | SNOWFLAKE-META | 1wk |
| 71 | DBT-CONNECTOR | 1wk |
| 72 | AIRFLOW-CONNECTOR | 1wk |

### Tier 10 — Connectors+Ops (6 items — unchanged)

| # | ID | Effort |
|---|---|---|
| 73 | PYCELONIS | 2wk |
| 74 | ENT-CMDB | 2wk |
| 75 | ENT-LDAP | 2wk |
| 76 | DO-8 | 2wk |
| 77 | DO-9 | 2wk |
| 78 | DO-10 | 2wk |

### Tier 11 — Hardening (6 items — unchanged)

| # | ID | Effort |
|---|---|---|
| 79 | POLARITY-FIX | 1wk |
| 80 | CONSERVATION-DISPLAY-FIX | 2d |
| 81 | PROMOTION-GATE-AMBER | 1d |
| 82 | EVOLUTION-DOMAIN-PARAM | 1d |
| 83 | DK-STALE-GUARD | 1wk |
| 84 | PLATEAU-DETECTION | 1wk |

### Tier 12 — Infrastructure (3 items)

| # | ID | Effort |
|---|---|---|
| 57 | CA-PROTO-4 (broader mypy) | 2d |
| 85 | DOCKER-COMPOSE | 2d |
| 86 | VPS-DEPLOY | 1wk |
| 87 | SDK-DOCS | 0.5d |

### Tier 13 — Purchasing Expansion (2 items — unchanged)

| # | ID | Effort |
|---|---|---|
| 109 | PUR-TOAST-CONNECTOR | 1wk |
| 110 | PUR-WEEKLY-REPORT | 3d |

### Tier 14 — Demo (1 item — LAST)

| # | ID | Effort | Dep |
|---|---|---|---|
| 88 | **LOOM-V1** | 1d | **ALL above** |

---

## Batch 11 Prompt Status (18 prompts)

| # | ID | MAP | Status | Tests |
|---|---|---|---|---|
| P1 | CONS-V-FIX | #111 | **✅ WRITTEN** | 11 unit + 2 SQLite + 2 PW = 15 |
| P2 | BUNDLE-REGEN | #102 | **✅ WRITTEN** | verification only |
| P3 | TRD-AE-VARIANTS | #105 | **✅ WRITTEN** | 21 unit + 4 PW = 25 |
| P4 | DOPS-AE-VARIANTS | #107 | **✅ WRITTEN** | 27 unit + 5 PW = 32 |
| P5 | PUR-AE-VARIANTS | #112 | **✅ WRITTEN** | 25 unit + 4 PW = 29 |
| P6 | S2P-AE-SUPPLEMENT | #104 | **✅ WRITTEN** | 21 unit + 5 PW = 26 |
| P7 | TRD-MULTI-TRADER | #27 | **✅ WRITTEN** | 14 unit + 5 PW = 19 |
| P8 | TRD-T3-TOD | #106 | queued | ~4 unit + ~4 PW |
| P9 | S2P-F8-RANKING | #38 | queued | ~4 unit + ~3 PW |
| P10 | S2P-F20-OPTIMIZER | #49 | queued | ~4 unit + ~3 PW |
| P11 | S2P-RECEIPT-FIELDS | #103 | queued | ~4 unit + ~3 PW |
| P12 | CONTRIBUTION-FE | #56 | queued | ~5 PW |
| P13 | GP-MYPY-FIX | #113 | queued | 0 (fix existing) |
| P14 | OUTBOX-QUARANTINE | #114 | queued | ~6 unit |
| P15 | OBSERVATION-WIRING | #115 | queued | ~4 unit + ~3 PW |
| P16 | EVIDENCE-RECEIPT-WIRING | #116 | queued | ~3 unit + ~3 PW |
| P17 | DATAOPS-AGE | #117 | queued | ~30 unit + ~5 PW |
| P18 | DEMO-AGE-OPS | #118 | queued | ~10 unit |

**Prompts 1-7: 3,602 lines. 119 unit tests + 25 PW tests = 144 total.**

---

## Forward 40-Prompt Sequence (Sprints 0-7)

Reference document: `forward_prompt_sequence_40.md`
Covers: 24 of 55 active MAP items through 40 Codex prompts across ~35 working days.

| Sprint | Days | Prompts | Milestone |
|---|---|---|---|
| 0 | 0.5 | P1-P2 | Demo fixed, conservation fixed |
| 1 | 3 | P3-P7 | All 4 copilots have AE variants |
| 2 | 3 | P8-P10 | Trading TOD, S2P ranking + optimizer |
| 3 | 2 | P11-P14 | S2P receipt, contribution FE, mypy, outbox |
| 4 | 4 | P15-P18 | L3 complete (all 5 copilots in AGE) |
| 5 | 3 | P20-P22 | L5 nodes defined |
| 6 | 4 | P23-P28 | **L5 COMPLETE (conditional — see gate criteria)** |

### L5 Completion Gate Criteria (Day 20 forecast is conditional on ALL passing)

L5 is complete ONLY after every gate in this list passes:

1. ✅ #111 CONS-V-FIX shipped + live conservation verified (not RED from ghosts)
2. ✅ #102 DEMO-BUNDLE-REGEN shipped + Trading cold-start restores d=10 centroids
3. ✅ #113 GP-MYPY-FIX: 4 GraphStore failures → 0
4. ✅ #117 DATAOPS-AGE: DataOps writes Decisions to AGE (milestone review ACCEPTED)
5. ✅ #118 DEMO-AGE-OPS: `demo.py status` shows per-app graph backend
6. ✅ A6-A8 manual gates: product graph smoke, product PW, L3 cross-copilot proof (all 5 domains)
7. ✅ #114 OUTBOX-QUARANTINE: 4 OUTBOX_PENDING conformance tests pass (88→0 skipped)
8. ✅ #115 OBSERVATION-WIRING: preview scores write Observation (not Decision)
9. ✅ #116 EVIDENCE-RECEIPT-WIRING: learn/outcome appends EvidenceReceipt with hash chain
10. ✅ B5 manual gate: 41/41 L4 conformance tests passing
11. ✅ #119 L5-JM-GRAPH sub-gates: C1-C3 (18 conformance tests), C4a+C4b (SDK+SOC integration), C5 (persist-before-cache), C6 (startup AGE read), C7 (full learn flow), C8 (PW L5 status)
12. ✅ C9 manual gate: L5 cross-copilot proof report — 5 domains × 3 node types = 15 cells populated

Day 20 is a forecast. If any gate fails, L5 is not complete regardless of calendar.
| 7 | 12 | P29-P40 | G12 + DI-1 + DI-2 + financial + docs |

### L5 Milestone (Day 20): Judgment Memory in Graph
After Sprint 6, all 5 copilots write Centroid, DKWeight, and ConservationState
to AGE as part of the learn flow. In-memory state is cache; AGE is persistence.
Restart preserves judgment. Cross-copilot dashboard query returns all 5 domains.

---

## Critical Path

```
Day 1:    P1 CONS-V-FIX + P2 BUNDLE-REGEN (P0 blockers)
Day 1-4:  P3-P7 (AE variants, parallel windows)
Day 5-8:  P8-P10 (Trading TOD + S2P features)
Day 9-11: P11-P14 (S2P receipt + mypy + outbox)
          [Manual gates: A3 DataOps milestone, A6-A8 product smoke+PW+proof]
Day 12-15: P15-P18 (Observation + EvidenceReceipt + DataOps AGE + demo.py ops)
          [Manual gate: B5 41/41 conformance → L4 COMPLETE]
Day 16-20: P20-P28 (L5 nodes + integration + startup + proof)
          [Manual gate: C9 L5 cross-copilot proof → L5 COMPLETE]
Day 20-35: P29-P40 (S2P Financial, DI-1, G12, DI-2, docs)

Parallel tracks:
  SOC: P13 → P24 (SOC centroid integration)
  S2P: P6 → P9 → P10 → P11 → P15 → P16 → P29 → P31 → P33
  SDK: P1 → P3 → P12 → P14 → P17 → P18 → P20-P28 → P30 → P34
```

---

## Test Count Projections

| After | +Tests | Running Total |
|---|---|---|
| Baseline (now) | — | **~6,159** |
| Sprint 0 (P1-P2) | +15 | ~6,174 |
| Sprint 1 (P3-P7) | +131 | ~6,305 |
| Sprint 2 (P8-P10) | +22 | ~6,327 |
| Sprint 3 (P11-P14) | +25 | ~6,352 |
| Sprint 4 (P15-P18) | +48 | ~6,400 |
| Sprint 5-6 (L5, P20-P28) | +48 | ~6,448 |
| Sprint 7 (P29-P40) | +70 | **~6,518** |

---

## L3→L5 Graph Execution Summary

Reference: Governed Graph Execution Plan v1.0 + L5 Design Spec v5.0

| Phase | Steps | Prompts | Tests | Status |
|---|---|---|---|---|
| L3 (A1-A8) | 8 | 4 Codex + 4 manual | ~45 | Prompts 13, 17, 18 in batch. A4 SOC separate. |
| L4 (B1-B6) | 7 | 5 Codex + 1 design spike + 1 manual | ~56 | Prompts 14, 15, 16 in batch. B3 schema + B5-B6 in Sprint 4. |
| L5 (C1-C9) | 10 | 9 Codex + 1 manual | ~48 | Sprint 5-6 (P20-P28). Consolidated as MAP #119. |
| **Total** | **25** | **18 Codex** | **~149** | **~62-89h (8-11 working days)** |

---

## Standing Rules (53)

Rules 1-47 unchanged from v5.139. Added v5.140:

| # | Rule |
|---|---|
| **48** | **Persist-before-cache for L5 writes.** Compute candidate → persist to AGE or durable outbox (MUST succeed) → update cache. If BOTH fail, RAISE — no state accepted. Scoring continues on cached state until outbox replays. |
| **49** | **Every L5 node write has a causal Decision.** SHAPED_BY (Centroid→Decision) and TRIGGERED_BY (ConservationState→Decision) edges are mandatory. Nodes without causal edges are incomplete. |
| **50** | **All Cypher uses AGE two-step pattern.** MERGE, ON CREATE SET, ON MATCH SET are forbidden in AGE. Read-then-write-or-create logic lives in Python GraphStore methods. Use `_S()` for serialization. |
| **51** | **L5LearningStore is a separate protocol.** L5 operations (update_centroid, update_dk_weights, update_conservation_state + getters) are on L5LearningStore, NOT on narrow GraphStore. Minimal stores need NOT implement L5 methods. |
| **52** | **Decision identity is (domain, decision_id).** All Cypher MATCH/CREATE for Decision uses {domain: ..., decision_id: ...}, not bare {id: ...}. |
| **53** | **complacency_flag is TEXT.** Stored as 'true'/'false' in AGE. Normalize on read: str(val).lower() == 'true'. |

---

## Cross-Reference Audit (v5.139 → v5.140)

| Source | Items | Accounted? |
|---|---|---|
| **MAP v5.139 (48 active)** | All 48 items | ✅ 46 retained + 2 DROPs (#55, #98) |
| **Batch 11 Analysis (18 prompts)** | CONS-V-FIX, PUR-AE-VARIANTS, GP-MYPY, OUTBOX-QUARANTINE, OBSERVATION-WIRING, EVIDENCE-RECEIPT-WIRING, DATAOPS-AGE, DEMO-AGE-OPS | ✅ #111-#118 |
| **Governed Graph Exec Plan** | L3 (A1-A8), L4 (B1-B6), L5 (C1-C9) | ✅ L3/L4 items in #113-#118. L5 consolidated as #119. |
| **L5 Design Spec v5.0** | 3 node types, 6 new L5LearningStore ops, 18 conformance tests, persist-before-cache model, Decision identity = (domain, decision_id) | ✅ Tracked under #119 |
| **6 Batch 11 DROPs** | 4 were PW fixes (not MAP items). 2 were MAP items (#55, #98). | ✅ Both MAP DROPs tracked |
| **Forward 40-prompt sequence** | 40 prompts, 7 sprints, 24 MAP items covered | ✅ Aligned with queue tiers |

**ZERO dropped. All items from all source documents accounted for.**

---

## Sequencing Constraints (updated)

**BUG-003 (BUGFIX-PRELUDE) before P16:** P16 unpacks `chain_index, payload_hash = append_evidence_receipt(...)` — wrong return type crashes at runtime. BUGFIX-PRELUDE is a hard prerequisite.

| Constraint | Reason |
|---|---|
| #111 + #102 before ALL Codex | Conservation ghost fix + bundle regen are P0 |
| PW gates (#15, #17) before new Codex | Validate B10 FE baseline |
| P3-P6 (AE variants) can parallel | Different repos/directories, zero file overlap |
| #113 GP-MYPY before #114 OUTBOX | mypy fix unblocks conformance test infrastructure |
| #114 OUTBOX before #115-#116 | Outbox is the reliability layer for receipt/observation writes |
| #117 DATAOPS-AGE before L5 (#119) | DataOps must write Decisions to AGE for L5 SHAPED_BY edges |
| #116 EVIDENCE-RECEIPT before L5 | Receipt chain must exist before L5 adds Welford audit state |
| S2P PW Fix 1 before exec plan A6 | Without it, S2P PW fails on conservation timeouts |
| #119 L5 sub-steps: C1 → C4 → C7 | Centroid nodes before integration before proof |
| #119 C5 requires explicit Step 2 | Recompute conservation in-memory BEFORE AGE writes |

---

## Opus / Level 5 Graph-Storage Review Boundary

For architectural review of the graph-storage path, evaluate ONLY:

| Scope | Documents |
|---|---|
| P0 fixes | #111 CONS-V-FIX, #102 DEMO-BUNDLE-REGEN |
| Graph infrastructure | #113–#118 (L3/L4 items) |
| L5 judgment memory | #119 L5-JM-GRAPH |
| Design specs | L5 Design Spec v5.0, Governed Graph Exec Plan v1.0 |
| Conformance | 18 L5 conformance tests (42-59), L4 41-test mapping |
| Standing rules | #48-#53 (graph-specific rules) |

**Do NOT treat the following as required for graph-storage architecture acceptance:** Tier 2 AE variant configurations (#104, #105, #107, #112), Tier 2-3 feature items (#27, #38, #49, #103, #106, #56), Tier 6+ items (S2P depth, DI phases, connectors, hardening, infrastructure), Forward prompt sequence items P29-P40 (post-L5 feature depth). These are product feature backlog running in parallel.

## Resolved Decisions (June 1, 2026)

| # | Decision | Resolution | Impact |
|---|---|---|---|
| D1 | Outbox worker mechanism | **Hybrid (push + CLI) with opt-in push.** Push loop requires `L5_OUTBOX_REPLAY_ENABLED=1` env. CLI is safe default. Cold start must NOT auto-replay stale entries. | New exec plan step B4.5. ~1d + 4 tests. |
| D2 | SOC α alignment timing | **After L5, before Loom (~Day 25).** SOC α jumps ~0.08→~1.0 — 12× θ_min drop. Ships as C4b + C5, timed to Sprint 7. | No separate item. |
| D3 | SOC total_decisions Cypher | **Bundle with D2.** One sprint: fix α + fix V + fix Cypher. | Falls into D2 sprint. |
| D4 | P13 scope | **Manual fix BUG-003/004/006 (20 min). Codex P13 for BUG-005 only (2h).** | BUGFIX-PRELUDE prompt created. |
| D5 | DomainConfig nodes | **Not needed for L5.** C from Python config. Deferred to L6. | Bug Synopsis §8 resolved. |

**DataOps C=6 Note:** P17 pre-check runs `DataOpsPreset().shape.category_names` — if count ≠ 6, update canonical tensor + all downstream docs.

## Summary

| Metric | v5.139 | v5.140 | Delta |
|---|---|---|---|
| Items tracked | 88 | **97** | +9 (#111-#119) |
| Cumulative ✅ DONE | 40 | **42** | +2 (#55, #98 DROPs) |
| Active items | 48 | **55** | +7 (-2 DROPs + 9 new) |
| Standing rules | 47 | **53** | +6 (#48 replaced + #49-#53 added) |
| P0 blockers | 1 | **2** | +1 (#111 CONS-V-FIX) |
| Prompts written | 0 | **7** | P1-P7 (3,602 lines, 144 tests) |
| Prompts queued | 0 | **11** | P8-P18 |
| Forward sequence | — | **40 prompts** | 7 sprints, ~35 days |
| L5 milestone | — | **Day 20** | All 5 copilots with judgment memory in graph |
| S2P critical gap | G12 (S14) | **G12 (S14)** | unchanged — still THE differentiator |
| DI-1 status | UNBLOCKED | **UNBLOCKED** | Sprint 7 (P30-P32) |
| Conservation status | 🔴 ALL RED | **Fix shipping** | #111 + #102 fix root cause |

---

*MAP v5.140 · June 1, 2026 · Post Batch 11 Analysis + L3→L5 Exec Plan*
*97 items tracked: 42 ✅ DONE + 55 active.*
*SDK 788, Trading 704, Purchasing 147, DataOps 175, S2P 854.*
*Trading tensor: (5,4,10). Standing rules: 53.*
*P0: #111 CONS-V-FIX + #102 BUNDLE-REGEN (conservation ghost fix).*
*Prompts 1-7 WRITTEN (3,602 lines, 144 tests). Prompts 8-18 queued.*
*L5 milestone: Day 20 (all 5 copilots with judgment memory in graph).*
*Forward: 40 prompts, 7 sprints, ~35 working days.*
*Single critical gap: G12 Situation Analyzer (S14 — 3-4wk).*
