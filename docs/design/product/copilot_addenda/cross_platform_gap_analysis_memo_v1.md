# CI Platform — Cross-Copilot Gap Analysis Memo

**Date:** August 17, 2026
**Author:** Gap analysis program (Claude + Codex)
**Scope:** All 5 copilots — SOC, S2P, Trading, Purchasing, DataOps
**Status:** All 5 gap analyses complete. This memo synthesizes cross-platform findings.

---

## 1. Program overview

Between August 16-17 2026, a systematic feature gap analysis was completed for every copilot in the CI platform. Each copilot's codebase was scanned against its authoritative product definition, producing per-feature LIVE/PARTIAL/GAP status, cross-cutting compatibility findings, MAP coverage, and prioritized fix recommendations.

The program followed a two-step approach for the complex multi-repo copilots (S2P, SOC): a structural diagnosis prompt first discovered the directory layout, then an informed gap analysis prompt used confirmed paths. Simpler copilots (Purchasing, DataOps, Trading) went directly to gap analysis.

### Deliverables produced

All analysis documents are consolidated in a dedicated directory:
- **In-repo (Codex-accessible):** `copilot-sdk/docs/design/copilot_addenda/`
- **Google Drive:** product directory → `copilot_addenda/`

| Copilot | Structural Diagnosis | Gap Analysis |
|---|---|---|
| Purchasing | — (single repo) | `purchasing_copilot_v1_4_gap_analysis.md` |
| DataOps | — (single repo) | `dataops_feature_gap_analysis_v1_9.md` |
| Trading (v1.0) | — | `trading_copilot_v1_1_gap_analysis.md` |
| Trading (v1.1) | — | `trading_copilot_v1_1_corrected_gap_analysis.md` |
| S2P | `s2p_structural_diagnosis.md` | `s2p_v1_4_gap_analysis.md` |
| SOC | `soc_structural_diagnosis.md` | `soc_v5_11_gap_analysis.md` |

This memo is filed as `cross_platform_gap_analysis_memo_v1.md`. The execution plan is at `copilot-sdk/docs/design/copilot_addenda/cross_platform_execution_plan.md`; the plan is not duplicated under the product/copilot_addenda directory in this checkout.

### Execution plan

A cross-copilot execution plan was produced by reading all gap analyses, structural diagnoses, product definitions, demo scenarios, and the MAP end-to-end:

`copilot-sdk/docs/design/copilot_addenda/cross_platform_execution_plan.md`

It contains 21 Codex-sized work items totaling approximately 105-135 engineer-days. With two engineers working in parallel, the critical path is about 8-10 weeks; with one engineer, about 22-27 weeks. All work is additive and feature-flagged. Summary by phase:

| Phase | Scope | Work items | Effort |
|---|---|---|---|
| **Phase 0** — Safety & cleanup | Trading SAFE-2 quarantine, evidence-tier inventory, stale-contract cleanup, demo truth controls | P0-01 through P0-04 | 1-2 weeks |
| **Phase 1** — Shared infrastructure | Evidence/Claim Gate, Frozen Twin, Promotion state machine, Counterfactual inspector, Day-0 readiness, Verified-outcome protocol | SH-01 through SH-06 | 2-3 weeks |
| **Phase 2** — Per-copilot moat features | S2P F23-F26, SOC F16-F22, Purchasing F23-F29, Trading F16+promotion, DataOps evidence/abstain/holdout/value provenance | S2P-01, S2P-02, S2P-03, SOC-01..03, TRD-01, PUR-01, DI-01 | 3-5 weeks |
| **Phase 3** — Demo readiness | Hero-beat harness, loop closure, C-COUPLE integration | DEMO-01, DEMO-02 | 1-2 weeks |
| **Phase 4** — Pilot readiness | Day-0 qualification, frozen baseline, measured transfer and competence | PILOT-01, PILOT-02 | 2-4 weeks |

**Critical path:** P0-01 → SH-01 → SH-03 → S2P-01 → S2P-02 → S2P-03 → DEMO-01 → PILOT-01 → PILOT-02 (64-78 engineer-days). Phases SH-02, SH-04, SH-05, and SH-06 run in parallel.

**Highest schedule risk:** SH-02 (Frozen Twin, 8-12 days) — three copilots (S2P, SOC, Purchasing) depend on it. If it slips, the widest downstream impact.

Each work item in the execution plan includes repo, dependencies, effort estimate, acceptance criteria, gap analysis reference, and Codex prompt notes sufficient for a follow-up Codex session to execute directly.

---

## 2. Platform-wide scorecard

### Feature status by copilot

| Copilot | PD Version | Features | LIVE | PARTIAL | GAP | BE Tests | E2E Tests |
|---|---|---|---|---|---|---|---|
| Purchasing | v1.4 | 29 (F1-F29) | 20 | 4 | 5 | 168* | E2E not aggregated |
| DataOps | v1.9 | No single F-numbered manifest; 6 H capabilities + 22 PD scenarios + named DI/SC requirements | Not reducible to one F-table | Not reducible to one F-table | Named GAP/PARTIAL items below | 278 current / 176 MAP snapshot* | 242 |
| Trading | v1.1 | 16 (F1-F16) | 11 | 4 | 1 | 1,226 | 286 |
| S2P | v1.4 | 29 (F1-F29) | 16 | 11 | 2 | 1,701 | 212 |
| SOC | v5.11 | 22 (F1-F22) | 10 | 9 | 3 | 1,896 | 444 |
| **Numbered-feature subtotal** | | **96** (Purchasing + Trading + S2P + SOC; DataOps is not an F-numbered manifest) | **57** | **28** | **11** | **4,991** | **942** |

*Counts are source inventories, not executed-suite results. Purchasing 168 and DataOps 176 are the older MAP/v0.7 snapshot; the current DataOps gap-analysis checkout reports 278 backend definitions and 242 E2E call sites. The numbered-feature subtotal excludes DataOps because its current PD exposes H1-H6, 22 scenarios, and named build requirements rather than one non-overlapping feature list; its 942 E2E subtotal also excludes DataOps and the unaggregated Purchasing E2E surface. It excludes GAE and ci-platform.*

### P0 blockers by copilot

| Copilot | P0 Blockers | Severity |
|---|---|---|
| **Trading** | SAFE-2 FAIL (directive strings + /api/broker/orders reachable), F16 Claim Gate GAP, SAFE-4 (counsel sign-off unverifiable) | Release-blocking |
| **S2P** | F23 Decision-Change Proposal GAP, F26 Frozen Twin GAP, F24 Compounding Ledger PARTIAL, F25 Promotion Workflow PARTIAL | Pilot-blocking |
| **SOC** | F18 Frozen Twin GAP, F19 No-Precedent GAP, F17 Earned Autonomy PARTIAL, F16 Learning Control Room PARTIAL, C-COUPLE not proven | Pilot-blocking |
| **Purchasing** | F23 Proof Ledger PARTIAL; F24 Handoff Pack GAP; F26 Discovery Gate GAP; §7.3 later-score proof PARTIAL; F27 Frozen Twin PARTIAL; legal-exposure framework GAP | Pilot-blocking; not a minor operational concern |
| **DataOps** | DI-ABSTAIN/GATEWAY/MCP GAP/PARTIAL; FDR/30-day holdout GAP; Value Provenance Ledger GAP; H1/H3 loop liveness PARTIAL; H4/H5/H6 governance/trust PARTIAL | Pilot/demo-blocking for evidence-backed claims |

---

## 3. Cross-copilot patterns

Six patterns were independently discovered across multiple gap analyses. These are platform-level concerns, not per-copilot bugs.

### 3.1 `reward` / `reward_raw` production fields

**Scope:** All 5 copilots
**Finding:** Production code contains `reward` and `reward_raw` field names wired into scoring, learning, outcome, and evolution contracts.

| Copilot | Occurrences | Files |
|---|---|---|
| Trading app | 6 | 3 |
| S2P app | 38 | 8 |
| S2P tests | 126 | 42 |
| Shared SDK (all copilots) | 57+ | 27+ |
| DataOps | 4 production compatibility hits in `context_router.py` (the gap analysis identifies three read locations) | 1 |
| Purchasing | 4 production hits in the current app scan; the gap analysis treats the field as a legacy wire concern | 1 |
| SOC | Present in shared paths; no dominant SOC-specific canonical triage contract | — |

**Impact:** These fields are load-bearing in learning/outcome contracts. They cannot be deleted without a protocol migration plan. A platform-wide decision is needed: rename, version, or accept.

**Recommended action:** Define a cross-copilot reward-field protocol. If renaming, do it as a single coordinated schema migration with backward-compatible aliases, not per-copilot opportunistic deletion.

### 3.2 Frozen Twin — absent in both enterprise copilots

**Scope:** S2P (F26 GAP) + SOC (F18 GAP)
**Finding:** Neither copilot has an immutable day-0 scorer snapshot, parallel scoring path, restart-safe storage, or live-vs-frozen comparison. Both copilots carry synthetic/modelled claims (CLAIM-59/62 for S2P; frozen-scorer 80.4%/92.9% for SOC) that require Frozen Twin to convert to measured customer evidence.

**Impact:** This is the single biggest credibility exposure across the platform. Without Frozen Twin, every compounding claim remains "we modelled it" not "we measured it." The 90-day shadow pilot — the platform's primary sales mechanism — cannot produce a measured improvement curve without this infrastructure.

**Recommended action:** Build Frozen Twin ONCE as a shared SDK capability. Both S2P and SOC consume the same interface: snapshot scorer state at day 0, run parallel scoring on every real decision, compare outcomes, produce drift report. The execution plan estimates SH-02 at **8–12 engineer-days**. This is the highest-leverage single implementation decision in the platform.

### 3.3 Earned Autonomy / Promotion state machine

**Scope:** S2P (F25 PARTIAL) + SOC (F17 PARTIAL)
**Finding:** Both copilots have evolution/shadow/promotion primitives, but neither has a persisted, audited state machine with the full lifecycle: Discover → Shadow → Promote → Measure → Keep/Rollback → Transfer (S2P) or Observed → Assisted → Shadow-qualified → Auto-approved → Circuit-broken (SOC).

**Impact:** Without this, the "earned autonomy" product story is narrative, not a measurable product state. The auto-approve expansion story (S2P S2, SOC shadow→authority) cannot be demonstrated as a tracked progression.

**Recommended action:** Build a shared promotion/autonomy state machine in the SDK with per-copilot configuration. S2P has 7 stages, SOC has 5 rungs — the underlying state-machine pattern is the same.

### 3.4 Counterfactual Inspector — infrastructure exists, product contract incomplete

**Scope:** S2P (F27 PARTIAL) + SOC (F20 PARTIAL) + Trading (related to F16)
**Finding:** The shared SDK has `self_computation_router.py` and `counterfactual_router.py` with replay-oriented infrastructure. Neither S2P nor SOC has the PD-specified product contract: per-factor boundary search showing direction, magnitude, and evidence-linked "what would flip this decision."

**Recommended action:** Extend the shared counterfactual infrastructure with a factor-delta explanation service. Each copilot adds its domain-specific factor boundary search on top.

### 3.5 Day-0 Readiness Assessment — primitives exist, product missing

**Scope:** S2P (F29 PARTIAL) + SOC (F21 PARTIAL)
**Finding:** ci-platform has onboarding/qualification primitives. copilot-sdk has readiness/substantiation modules. Neither copilot assembles these into the specified Day-0 onboarding report: source coverage, connector health, graph state, identity resolution, and safe-mode capability boundaries.

**Recommended action:** Build a shared readiness assessment framework in the SDK, with per-copilot data-source and connector checks. This is the paid discovery → pilot conversion tool.

### 3.6 Documentation hygiene — stale tensor/naming references

**Scope:** S2P (96 stale 5×5×7 references) + SOC (84 travel_match vs 33 privileged_identity_context)
**Finding:** Both enterprise copilots have significant documentation drift from their live code state. S2P's live tensor is 5×5×8 but 96 references still say 5×5×7. SOC's factor-0 is `privileged_identity_context` in config but `travel_match` in 84 backend locations.

**Recommended action:** These are documentation/fixture cleanup sprints, not permission to change scoring geometry. They can be parallelized with feature development. For SOC factor-0, the panel re-authoring work is complete but runtime fixture/provenance migration is still needed.

### 3.7 Evidence-gated compounding is a shared P0 pattern

Purchasing and DataOps are not “mature with minor issues” under their current v1.4/v1.9 contracts. Purchasing has five new GAP features or contract-level partials (F23–F29, especially F24/F26 and §7.3), and DataOps has missing abstention, FDR/holdout, value-provenance, prompt-integration, and corrected trust-gateway surfaces. The execution plan therefore assigns PUR-01 and DI-01 **10–15 engineer-days each**, with SH-01, SH-05, and SH-06 as shared dependencies. Existing dashboards and generic audit routes are useful foundations but do not close these contracts.

---

## 4. Per-copilot detail

### 4.1 Trading — release-blocked on safety

**PD:** `trading_copilot_product_definition_v1_1_corrected.md` (107KB)
**Repo:** copilot-sdk (single repo, apps/trading/)
**Feature count:** 16 (F1-F16) → 11 LIVE, 4 PARTIAL, 1 GAP

The Trading copilot has a solid v1.0 operational surface. The v1.1 addendum introduced observation-only requirements that the codebase currently violates:

| Blocker | Detail | Fix estimate |
|---|---|---|
| **SAFE-2 FAIL** | `pattern_detector.py` emits "reduce size or skip"; `regime_recommender.py` emits `avoid/reduce/hold/increase` actions; `regime_classifier.py` emits "Hold sizing…"; `/api/broker/orders` is reachable | **P0-01: 4–6 days** for the observation-only quarantine; TRD-01 completes claim/promotion safety integration |
| **F16 Claim Gate GAP** | No EvidenceGate service, no `/api/trading/gate/{claim_type}` endpoint. Infrastructure exists: ClaimRegistry, conservation, substantiation | **SH-01: 6–8 days** shared gate plus **TRD-01: 7–10 days** Trading wiring |
| **SAFE-4** | Counsel sign-off is external; no code evidence can establish it | External gate |
| **StrategyStatus** | Old directive-shaped recommendation/action fields remain; v1.1's observation-only StrategyStatus model not implemented | Part of SAFE-2 cleanup |

**Note:** The Trading v1.1 merge itself was completed in this session. The original v1.1 file on Drive was SOC v5.8 (348KB, mislabeled). The correct v1.1 was produced by merging v1.0 base + FINAL addendum and verified on Drive as `trading_copilot_product_definition_v1_1_corrected.md`.

### 4.2 S2P — broad surface, moat features incomplete

**PD:** `s2p_copilot_unified_v1_4.md` (136KB, Part I engineering + Part II product)
**Repos:** s2p-copilot (backend), copilot-sdk (frontend/E2E/SDK), gen-ai-roi-demo (Preview only)
**Feature count:** 29 (F1-F29) → 16 LIVE, 11 PARTIAL, 2 GAP

The original S2P operational surface (F1-F22) is substantially implemented: scoring, triage, verification, conservation, evidence, supplier intelligence, optimization, simulation, and audit all have real code. The v1.4 moat features (F23-F29) form a dependency chain:

```
F23 Decision-Change Proposal (GAP) ← the "one object" everything depends on
  → F24 Compounding Ledger (PARTIAL) ← needs F23 as its unit
    → F25 Promotion Workflow (PARTIAL) ← needs F23 + F24
      → F26 Frozen Twin (GAP) ← converts synthetic→measured
```

Additional findings:
- Auto-approve is explicitly shadow-only (honest, not a gap per se)
- FIX-B Commit 3 (calibration persist + test cleanup) is **PARTIAL/HISTORICAL**: current executable S2P code/tests use 5×5×8 and collect 1,701 tests, but no dated artifact proves the historical “55 failures” remain resolved by a fresh full run.
- CLAIM-59/62 remain synthetic until Frozen Twin exists
- Manifest scope anomaly: PD also contains F30, F31, DIFF-1 beyond the F29 boundary

### 4.3 SOC — strongest operational surface, proof layer incomplete

**PD:** `soc_copilot_design_v5_11.md` (383KB, merged engineering + product)
**Repos:** gen-ai-roi-demo-v4-v50 (primary), copilot-sdk, GAE, ci-platform
**Feature count:** 22 (F1-F22, F11 skipped) → 10 LIVE, 9 PARTIAL, 3 GAP

SOC has the most tests (1,896 BE + 444 E2E) and the broadest operational surface: six-factor scoring, triage, provenance, NL evidence, IKS, conservation, shadow mode, referral rules, threat intelligence, analytics, graph exploration, and audit/export.

The v5.9 "proof of compounding" features are not complete:

| Feature | Status | What's missing |
|---|---|---|
| F16 Learning Control Room | PARTIAL | Unified panel with summary, convergence, and Tab-3 bridge |
| F17 Earned Autonomy Ladder | PARTIAL | Persisted 5-rung per-class authority state |
| F18 Frozen Twin | **GAP** | No immutable day-0 snapshot or parallel scorer |
| F19 No-Precedent Surface | **GAP** | No explicit epistemic disclosure linked to decision evidence |
| F20 Counterfactual Inspector | PARTIAL | Per-factor boundary/magnitude explanation |
| F21 Day-0 Readiness | PARTIAL | SOC onboarding assessment product |
| F22 Cold-Start Measurement | PARTIAL | Per-category crossover metric |

Additional findings:
- Factor-0 naming: live scoring canonical (`privileged_identity_context`), 84 residual `travel_match` refs
- C-COUPLE: conservation gates evolution (LIVE) but universal decision-path veto NOT PROVEN
- Referral R1-R7: implementation rule names differ from v5.11 prose labels
- Canonical numbers (71.7%, 78.9%, IKS 43→82, $523K-$2.8M) remain controlled/synthetic
- Acceleration/second-derivative: instrumentation only, no live loop
- 7 frontend tabs, not 5 (stale assumption corrected)
- Three-Signal Monitoring: Circuit Breaker LIVE, Flywheel PARTIAL, Analyst Contribution NEAR

### 4.4 Purchasing — operationally mature, v1.4 proof layer incomplete

**PD:** `purchasing_copilot_pd_v1_4.md`
**Repo:** copilot-sdk (apps/purchasing/)
**Feature status:** **20 LIVE, 4 PARTIAL, 5 GAP out of 29**. The original F1–F22 surface is strong, but F11 remains partial because the v1.4 Discovery Gate dependency is absent, and F17 is only adjacent delivery/consolidation plumbing. The new features are:

| Feature | Status | Implementation gap | Action / work item |
|---|---|---|---|
| F23 Proof Ledger | PARTIAL | Generic evidence/audit/conservation proof exists, but no two-curve ledger, attribution hierarchy, or honest-$0 computation | Build domain ledger and receipt UI/API; PUR-01, SH-01 |
| F24 Handoff Pack | GAP | No builder, schema, endpoint, tests, panel, or E2E | Define versioned handoff contract and provenance export; PUR-01 |
| F25 Time-to-Competence | GAP | No re-convergence metric or time-series panel | Add event anchors, convergence detector, persisted metric; PUR-01, PILOT-02 |
| F26 Discovery Gate / Not Yet | GAP | No evidence floor, OOS confirmation, selection-adjusted statistic, or explicit abstention outcome | Implement before F11 claims; SH-01, PUR-01 |
| F27 Frozen Twin | PARTIAL | Generic counterfactual plumbing but no immutable checkpoint/replay baseline | Consume SH-02 through PUR-01 |
| F28 Pre-Order Belief Capture | GAP | No schema, prompt flow, or causal storage | Architecture/privacy decision, then PUR-01 |
| F29 Yield-Adjusted Quote Audit | GAP | No yield, depletion, trim/waste, net plate-cost, or quote-audit computation | Add source contracts and audit calculations; PUR-01 |

**§7.3 and §12.0:** The score→verify→learn path is wired, but a controlled later comparable score with measurable improvement is not proven. The legal-exposure framework is also GAP at framework level; current graph-status fields honestly report incomplete receipt mapping. `reward_raw` is a compatibility concern, not the only Purchasing gap.

**Implementation readiness:** PUR-01 is **10–15 engineer-days**, depends on SH-01, SH-02, SH-05, and SH-06, and must close the F23/F24/F26/F27 evidence chain before a compounding or financial claim is presented as measured. Acceptance criteria are in the execution plan: persisted schemas, mounted endpoints, UI/E2E coverage, source-derived quote values, §7.3 later-score proof, legal/evidence-floor tests, and no fabricated savings.

### 4.5 DataOps — real foundation, evidence and trust gates incomplete

**PD:** `dataops_copilot_design_v1_9.md`
**Repo:** copilot-sdk (apps/dataops/)
**Status:** The DataOps loop is structurally wired: production constructs a PromptVariantEvolver, the scoring router calls learn(), and the outcome recorder is invoked. The stronger claim—every verified decision updates the correct variant and a later trust/score measurably moves—is **NEAR/PARTIAL**, not proven. The feature/capability manifest is not a single F-numbered list: it exposes H1–H6, seven market scenarios, fifteen innovation scenarios, and named SC/DI requirements.

Key gaps requiring implementation:

- **GAP/MAP-missing:** SC-IKS-ATTR, SC-FORECAST, SC-DIGEST, DI-4 Prompt Integrator, D-I8 monetization discovery, D-I9 SourceIntegrator wiring, DI-ABSTAIN, DI-FIRSTVS6TH, DI-TWIN, FDR/30-day holdout/expert verification, and Value Provenance Ledger.
- **PARTIAL/P0:** H1/H3 loop proof, H4 self-governing quality routing, H5 self-valuating claims, H6 corrected Agent Trust Gateway/MCP, DI-5/6/7 evidence gates, and D-I12 atomic three-channel receipt.
- **Honesty boundary:** DI-GOLD and valuation outputs are modeled/derived until FDR, holdout, expert verification, and observed-dollar provenance exist. The current trust routes do not establish safe-for-autonomous-use under the corrected gateway contract.

**Implementation readiness:** DI-01 is **10–15 engineer-days**, depends on SH-01, SH-05, and SH-06, and must deliver an abstain/read-only gateway, FDR/30-day holdout, expert verification, and Value Provenance Ledger. Acceptance criteria are in the execution plan: gateway/MCP audit evidence, no insufficient-data automation, evidence-gated labels, and source→transformation→decision→economic attribution. SH-02 is required later for DI-TWIN and PILOT-01, while SH-05 supplies the Day-0 readiness protocol.

---

## 5. Wrong-file incidents

The gap analysis program uncovered a systematic file-labeling problem:

| File | Claims to be | Actually contains | Location |
|---|---|---|---|
| `trading_copilot_product_definition_v1_1.md` (348KB) | Trading PD v1.1 | SOC v5.8 engineering design | 3 copies across Drive + product directory |
| `trading_copilot_product_definition_v1_1_corrected.md` (107KB) | Trading PD v1.1 | Correct Trading v1.1 (merged this session) | Product directory (verified) |

The first Trading gap analysis ran against the wrong file and had to be re-run. The three mislabeled copies should be deleted or renamed.

---

## 6. MAP coverage gaps

| Copilot | MAP items present | MAP-MISSING | Inconsistencies |
|---|---|---|---|
| Trading | P48-P86, R1-R6 | T16b (Claim Gate), SAFE-2, SAFE-4 | R2/R3/R5 DROP_CONFIRMED but #171/#173/#176 in forward queue; 27-vs-32 item count discrepancy |
| S2P | P64-P75, R7-R17 (older Purchasing/S2P work) | F23-F29 (all 7 v1.4 features) | Tier 5 items cover historical work, not v1.4 moat features |
| SOC | Historical platform/SOC items and v5.9 continuation/design references | F16-F22 are tracked by design references, but strict acceptance items are incomplete; F18/F19 remain GAP | MAP status language is ahead of strict LIVE definitions |

**Recommended MAP additions:**
- Trading: 3 items (TRD-F16-EVIDENCE-GATE, TRD-SAFE-2-OBS-ONLY, TRD-SAFE-4-COUNSEL-GATE)
- S2P: 8 items (S2P-V14-00 through S2P-V14-07, covering shape reconciliation + F23-F29)
- SOC: 7 acceptance items are recommended in the memo/gap-analysis reconciliation; the gap analysis itself says F16-F22 have design/MAP references but require explicit acceptance items rather than calling all seven MAP-MISSING.
- Purchasing: the gap analysis recommends 10 additions covering proof ledger, handoff, discovery gate, compounding loop, legal exposure, time-to-competence, yield audit, Frozen Twin, and belief capture.
- DataOps: the gap analysis recommends 11 additions covering loop regression, IKS attribution/forecast/digest, proof drawer, gateway/abstain, Frozen Twin, first-vs-sixth measurement, FDR/holdout, value ledger, DI-4, and connector validation.

---

## 7. Implementation plan

The full execution plan with 21 work-item cards, dependency DAG, acceptance criteria, and Codex prompt notes is in:
`copilot-sdk/docs/design/copilot_addenda/cross_platform_execution_plan.md`

### Shared SDK builds (Phase 1 — highest leverage)

Six capabilities are built once in the SDK and consumed by multiple copilots:

| ID | Capability | Copilots served | Effort | Risk |
|---|---|---|---|---|
| SH-01 | Evidence/Claim Gate | Trading F16, S2P, SOC, DataOps, Purchasing | 6-8 days | Low |
| SH-02 | Frozen Twin | S2P F26, SOC F18, Purchasing F27 | 8-12 days | **Highest schedule risk** — 3 copilots blocked if it slips |
| SH-03 | Promotion/autonomy state machine | S2P F25, SOC F17, Trading F11/F12 | 7-10 days | Medium — per-copilot policy injection needed |
| SH-04 | Counterfactual inspector | S2P F27, SOC F20, Purchasing | 5-7 days | Low |
| SH-05 | Day-0 readiness | S2P F29, SOC F21, DataOps | 6-9 days | Low |
| SH-06 | Verified-outcome protocol | All 5 (reward migration) | 4-6 days | Low |

### P0 blocker-to-work-item mapping

Every P0 blocker in §2 has an actionable execution-plan owner:

| Blocker | Work item(s) | Immediate deliverable |
|---|---|---|
| Trading SAFE-2 | P0-01, TRD-01 | Observation-only negative scan/tests, broker-write isolation, then claim/promotion safety wiring |
| Trading F16 / SAFE-4 | SH-01, TRD-01 | Shared evidence gate, claim endpoint, measured/synthetic gate; SAFE-4 remains an external approval artifact |
| S2P F23–F26 | S2P-01, S2P-02, S2P-03, SH-02/SH-03 | Persisted proposal, reconciled ledger, seven-stage promotion, immutable twin |
| SOC F16–F19 / C-COUPLE | SOC-01, SOC-02, SOC-03, SH-02/SH-03 | Control room, ladder, Frozen Twin/no-precedent surfaces, RED veto/referral tests |
| Purchasing F23/F24/F26/F27 and §7.3/§12.0 | PUR-01, SH-01/SH-02/SH-05/SH-06 | Proof ledger, handoff, discovery gate, twin adapter, legal/evidence and later-score tests |
| DataOps DI gates and H1/H3/H4/H5/H6 | DI-01, SH-01/SH-05/SH-06 | Abstain/read-only gateway, FDR/holdout, value provenance, trust and loop-closure tests |

### Per-copilot work (Phase 2)

| ID | Copilot | Scope | Effort |
|---|---|---|---|
| S2P-01 | S2P | F23 Decision-Change Proposal (the canonical object) | 6-8 days |
| S2P-02 | S2P | F24 Compounding Ledger | 7-10 days |
| S2P-03 | S2P | F25 Promotion + F26 Frozen Twin wiring | 9-12 days |
| SOC-01 | SOC | F16 Control Room + F18 Frozen Twin wiring | 8-12 days |
| SOC-02 | SOC | F17 Earned Autonomy Ladder + C-COUPLE veto | 6-9 days |
| SOC-03 | SOC | F19 No-Precedent + F20 Counterfactual | 6-9 days |
| TRD-01 | Trading | F16 Claim Gate + promotion observation-only | 7-10 days |
| PUR-01 | Purchasing | F23-F29 proof/discovery/legal/handoff | 10-15 days |
| DI-01 | DataOps | Evidence/abstain/holdout/value provenance | 10-15 days |

### Critical path

```
P0-01 (SAFE-2) → SH-01 (evidence gate) → SH-03 (promotion) →
S2P-01 (proposal) → S2P-02 (ledger) → S2P-03 (promotion+twin) →
DEMO-01 (hero beats) → PILOT-01 (day-0 + baseline) → PILOT-02 (measured transfer)
```

Total critical path: **64-78 engineer-days**. SH-02, SH-04, SH-05, SH-06 run in parallel off the critical path.

### MAP reconciliation (from execution plan)

The execution plan proposes 12 new MAP item groups (XPLAT-01 through XPLAT-07, TRD-01/02, S2P-V14-00..07, SOC-V59-00/01, PUR-V14-00, DI-V19-00) mapped to specific work items. See the full plan for the reconciliation table.

---

## 8. Repo structure summary (confirmed)

```
copilot-sdk/                          Shared SDK + Trading + Purchasing + DataOps + S2P frontend
  copilot_sdk/                        Shared scoring, graph, conservation, evolution, situation
  apps/trading/                       Trading copilot (port 8010/5174)
  apps/purchasing/                    Purchasing copilot (port 8020/5175)
  apps/dataops/                       DataOps copilot (port 8030/5176)
  apps/s2p/frontend/                  S2P frontend only (port 5177)
  e2e/                                Playwright suites for all copilots
  docs/design/                        All PDs, design docs, MAP
  docs/design/copilot_addenda/        Gap analyses, structural diagnoses, this memo

s2p-copilot/                          S2P dedicated backend (port 8002)
  backend/app/                        S2P FastAPI application
  backend/tests/                      1,701 tests

gen-ai-roi-demo-v4-v50/               SOC primary (port 8001/5173)
  backend/app/                        SOC FastAPI application
  backend/tests/                      1,896 tests
  frontend/                           SOC frontend (7 tabs) + S2P Preview proxy

graph-attention-engine/               GAE library (Apache 2.0)
  gae/                                Scoring/attention primitives (177 tests)

ci-platform/                          Platform services (Apache 2.0)
  ci_platform/                        AGE client, connectors, onboarding (476 tests)
```

**Test inventory arithmetic:** The memo’s former 6,584 total was incorrect. The old MAP snapshot arithmetic was 168 + 176 + 1,226 + 1,701 + 1,896 = **5,167 BE**, with 942 E2E from Trading + S2P + SOC only. The current DataOps gap analysis reports **278 BE + 242 E2E**, so current five-copilot app inventories are **5,269 BE** if the 168 Purchasing snapshot is retained, and **1,184 E2E** before any Purchasing E2E count. Adding GAE (177) and ci-platform (476) yields **5,922 BE-side definitions** under that mixed source-inventory denominator. These are not executed-suite totals and must not be presented as one homogeneous platform test count.

---

## 9. Key observations

**The platform has two tiers of maturity.** The operational surfaces (scoring, triage, conservation, evidence, import/export, IKS, audit) are substantially implemented, but Purchasing and DataOps also have material v1.4/v1.9 evidence-gate gaps. The "proof of compounding" surfaces (Frozen Twin, Earned Autonomy, Counterfactual Inspector, Day-0 Readiness, Cold-Start Measurement, abstention, holdout, and value provenance) are incomplete across the enterprise copilots. These are composition and contract gaps, with several features—such as S2P F23/F26, SOC F18/F19, Purchasing F24/F26/F28/F29, and DataOps DI-4/DI-ABSTAIN/FDR/value ledger—being genuine GAPs.

**Trading has a different problem class.** Its issue is safety compliance (observation-only violations), not feature completeness. The fix is surgical (replace directive strings, unmount write endpoints), not architectural.

**The shared SDK is the right build target.** Frozen Twin, promotion state machine, counterfactual inspector, and Day-0 readiness are all cross-copilot needs. Building them once in the SDK and consuming per-copilot is the correct architecture.

**Synthetic-vs-measured is the single biggest credibility risk.** CLAIM-59/62 (S2P), frozen-scorer numbers (SOC), and the $41-71M/$523K-$2.8M value models are all synthetic/modelled. The Frozen Twin is the mechanism to convert them. Until it ships, every compounding claim carries a "modelled, not measured" qualifier.

---

*Cross-Platform Gap Analysis Memo · CI Platform · August 17, 2026*
*5 copilots · 96 numbered features plus a non-numbered DataOps capability/scenario manifest · 5,269 current app BE definitions (mixed Purchasing snapshot) · 1,184 current app E2E call sites before Purchasing E2E*

*9 Codex prompts · 2 structural diagnoses · 6 gap analyses*

---
## Change log
- August 18, 2026: Reviewed against all cited gap analyses, structural diagnoses, and `copilot-sdk/docs/design/copilot_addenda/cross_platform_execution_plan.md`. **20 factual corrections** and **9 implementation-readiness improvements**. Corrected Purchasing/DataOps feature status and scope, replaced the invalid 99-feature/6,584-test totals, clarified current versus historical test inventories, corrected SOC MAP wording, added Purchasing/DataOps MAP additions, expanded F23–F29 and DI gap detail, aligned the phase/work-item references and critical path, and corrected the execution-plan file location.
