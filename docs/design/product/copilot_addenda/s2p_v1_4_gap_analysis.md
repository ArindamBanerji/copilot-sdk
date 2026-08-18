# S2P Copilot v1.4 — Feature Gap Analysis

Date: 2026-08-17  
PD: `copilot-sdk/docs/design/product/s2p_copilot_unified_v1_4.md` (Part II product definition)  
Prior work: `copilot-sdk/docs/design/s2p_structural_diagnosis.md`  
Repos: `s2p-copilot` (backend), `copilot-sdk` (frontend/E2E/SDK), `gen-ai-roi-demo-v4-v50` (Preview only)

## Summary

- Features F1–F29: **16 LIVE, 11 PARTIAL, 2 GAP**.
- v1.4 additions F23–F29: **0 LIVE, 5 PARTIAL, 2 GAP**.
- P0 gaps: **F23 Decision-Change Proposal** and **F26 Frozen Twin**.
- P0 partial blockers: **F24 Compounding Ledger** and **F25 Promotion Workflow**.
- Auto-approve exists, but `s2p_auto_approve_gate.py` explicitly implements a **shadow-only** gate. It does not autonomously execute approvals.
- Live tensor: **5×5×8**. A scoped source/document scan found **96 stale 5×5×7 references**; the authoritative PD still specifies a 5×5×7 pilot in multiple places.
- Test inventory: **1,701 dedicated S2P backend tests collected** and **212 S2P E2E call sites** across 37 Playwright files.
- The MAP v5.228 Tier-5/R7–R17 entries cover older Purchasing/S2P work. No direct MAP item covers F23–F29.
- Product credibility risk: CLAIM-59/CLAIM-62 remain synthetic/modelled claims; the missing Frozen Twin is the mechanism intended to convert them to measured customer evidence.

The status labels below use the requested strict meaning: LIVE requires mounted backend behavior, backend tests, a frontend surface, and E2E coverage. PARTIAL identifies a concrete acceptance-contract gap. Related infrastructure is not counted as the feature itself.

## Feature Status Table (F1–F22)

| Feature | Status | Backend evidence | Frontend evidence | Test evidence | Gap, if any |
|---|---|---|---|---|---|
| F1 Exception Triage Dashboard | LIVE | `s2p-copilot/backend/app/routers/s2p.py` score/queue path, mounted by `main.py` | `apps/s2p/frontend/src/screens/TriageScreen.tsx`, queue/triage components | `test_s2p_score_endpoint.py`, triage/flows E2E | Core contract is present. |
| F2 Situation-Aware Evidence Panel | LIVE | `s2p_graph_reader.py`, `s2p_situation_pattern.py`, `s2p_situation.py`, `s2p_evidence.py`, all mounted | `SituationPanel.tsx`, evidence screens/templates | evidence/situation backend tests and `situation-analyzer.spec.ts`, evidence-chain E2E | The implementation is bounded by available graph context; missing AGE data degrades evidence quality, but the feature path exists. |
| F3 One-Click Verification Console | LIVE | `/api/s2p/outcome`, `/api/learn`, outcome receipt and idempotency logic | triage verification controls and receipt panels | `test_s2p_outcome.py`, score/outcome tests, triage E2E | No identified surface-level gap. |
| F4 Conservation Dashboard | LIVE | shared conservation routers plus S2P conservation/threshold services | `S2PConservationProjection.tsx`, gauges and dashboard surfaces | conservation, threshold, and learning-gate tests; relevant E2E | No identified surface-level gap. |
| F5 Auto-Approve Engine | PARTIAL | `AutoApproveGate`, `s2p_auto_approve.py`, `s2p_auto_approve_gate.py` | `AutoApprovePanel.tsx` | `test_s2p_auto_approve.py`, `auto-approve.spec.ts` | The PD’s earned-authority story is not live: the implementation is explicitly shadow-only and records `learning_applied=False`/`outcome_written=False`; no ERP approval execution exists. |
| F6 Novelty Detection & Auto-Pause | PARTIAL | novelty router/tracker and gate controls | `NoveltyStatusPanel.tsx`, alert/banner components | novelty and governance tests plus E2E coverage | Novelty is implemented, but a complete always-reliable auto-pause contract tied to every relevant operational path is not demonstrated as a single acceptance surface. |
| F7 Centroid Explorer | LIVE | explorer router/service and centroid import/checkpoint paths | `CentroidExplorer.tsx`, explorer panels | explorer/import tests and E2E coverage | Explorer is mounted and exercised. |
| F8 Factor Proposer | PARTIAL | `factor_proposer_router.py`, proposer service and request model | factor insight/proposal UI | factor proposer tests | Proposals are advisory. The PD-level accepted replacement, requalification, and governed rollout path is not the same as emitting a proposal. |
| F9 IKS Tracker | LIVE | S2P IKS endpoint/service and scorer trajectory integration | IKS/trajectory/conservation views | `test_s2p_iks.py` and related E2E | IKS surface is present; its value remains dependent on the active persistence/runtime configuration. |
| F10 Financial Impact Ledger | PARTIAL | `financial_router.py`, `financial_impact.py`, financial calculations | `FinancialImpactCard.tsx`, trend panel | optimizer/financial backend tests and UI coverage | Financial impact exists, but it is not the unified F24 autonomy/compounding ledger and does not reconcile all required IKS, promotion, baseline, and rollback streams. |
| F11 Audit & Export Pack | LIVE | audit framework and `s2p_audit_export.py` | `AuditExportPanel.tsx`, `AuditTrailPanel.tsx`, receipts | audit/export/receipt tests and E2E | The audit/export path is mounted and tested. |
| F12 AgentEvolver — Self-Tuning Operations | LIVE | `s2p_evolver.py`, S2P evolution service/router, variant store and shadow batch | `EvolutionPanel.tsx`/S2P evolution surfaces | `test_s2p_evolver.py`, evolution/shadow E2E | The evolution primitive is live; its product promotion workflow remains separately incomplete under F25. |
| F13 Supplier Behavioral Profile Builder | LIVE | supplier profile accumulator/intelligence services and supplier routers | supplier profile/heatmap/clustering panels | supplier accumulator/intelligence tests and E2E | No identified surface-level gap. |
| F14 Lead Time Intelligence | LIVE | `lead_time_router.py`, lead-time service | lead-time views/cards | lead-time backend and E2E coverage | No identified surface-level gap. |
| F15 Supplier Trend Correlation & Early Warning | LIVE | `s2p_early_warning.py` and trend services | early-warning/novelty panels | early-warning tests and E2E | No identified surface-level gap. |
| F16 Behavioral Clustering | LIVE | clustering router/service | clustering panels and supplier views | clustering backend/E2E coverage | No identified surface-level gap. |
| F17 Cross-System Discovery Alerts | LIVE | discovery routers/services and graph discovery paths | discovery panels | discovery backend/E2E coverage | Current scope is largely shadow/advisory; production authority is intentionally constrained, but the feature surface is present. |
| F18 Process-Tech Fusion Loop | PARTIAL | `s2p_process_fusion.py`, `process_fusion.py` | `ProcessFusionPanel.tsx` | process-fusion tests/E2E | The S2P API/UI surface exists, but a verified real Celonis connector/cache ingestion and closed WHERE→WHY→WHICH→LEARN→TRANSFER loop were not found. |
| F19 Payment Timing Optimization | LIVE | payment router/service and behavior calculations | `PaymentStrategyPanel.tsx` | payment router tests and E2E | The advisory optimization surface is present; execution authority remains outside S2P. |
| F20 Centroid-to-Optimizer API | LIVE | `optimizer_router.py`, optimizer export service | optimizer/export UI surfaces | optimizer export tests and E2E | API/export contract is present. |
| F21 Disruption Simulation Sandbox | LIVE | `s2p_simulation.py`, disruption simulation service | simulation panels | simulation tests and E2E | Sandbox behavior is present; it is not evidence of real disruption outcomes. |
| F22 Compliance Screening with Conservation Proof | LIVE | `compliance_router.py`, compliance screener, governance/SOX readiness | `CompliancePanel.tsx`, `ComplianceScreeningPanel.tsx` | compliance/governance/receipt tests and E2E | Screening and proof surfaces are present. Legal/regulatory deployment evidence still requires customer data and is not implied by tests. |

## v1.4 New Features (F23–F29)

### F23 — Decision-Change Proposal (P0): GAP

The PD makes this the canonical “one object”: evidence chain, expected KPI delta, confidence/conservation state, proposed action, rollback path, persistence, decision/evidence links, customer approval-queue serialization, and audit receipt.

Searches for `DecisionChange`, `ProposalBuilder`, `decision_change`, `change_proposal`, and the named proposal object found no S2P model or endpoint returning this object. Existing pieces are related but insufficient:

- S2P evolution variants and `s2p_evolver.py` describe changes to variants.
- `factor_proposer_router.py` emits factor proposals.
- Evidence templates, outcome receipts, financial impact, and confidence fields exist independently.
- None is the canonical persisted proposal that composes all of these and enters SAP/Coupa/custom approval workflow.

Required build: schema/model, builder, persistence/linkage, API response, approval-queue adapter, UI card, and audit receipt. This is the first dependency for F24–F26.

### F24 — Autonomy / Compounding Ledger (P0): PARTIAL

Existing sources:

- IKS trajectory and score endpoint.
- Conservation status/threshold history.
- Financial impact service and panels.
- Outcome receipts and audit export.
- Evolution/promotion-adjacent events.
- Cohort/measurement readiness services.

Missing contract:

- No `CompoundingLedger`, `autonomy_ledger`, or `LedgerAggregator` implementation was found.
- No single time-series endpoint reconciles decisions, verified outcomes, IKS, conservation, financial impact, provenance, promotions/rollbacks, abstention, bad-auto-approval, and frozen-baseline delta.
- No single always-visible dashboard answers the PD’s “is it getting better, and can I prove it?” question from one reconciled object.

Required build: aggregation schema with source identifiers and timestamps, reconciliation tests against graph/scorer state, and a UI that refuses to display fabricated or merely modelled values.

### F25 — Decision-Class Promotion Workflow (P0): PARTIAL

The current S2P evolution code has meaningful pieces:

| PD stage | Current evidence | Assessment |
|---|---|---|
| Discover | evolution proposals/variant dimensions and process-fusion discovery | Partial |
| Shadow | `run_shadow_batch`, shadow routes/tests, shadow E2E | Present |
| Promote | `evaluate_promotion`/promotion checks | Partial; evaluation exists, authority transition is not a full state machine |
| Measure | financial/measurement/cohort services | Partial; not bound to a promotion record |
| Keep | no canonical promotion state transition found | Missing as workflow state |
| Rollback | generic checkpoint/intervention/auto-approve rollback-related primitives | Partial and not promotion-linked |
| Transfer | transfer badges/process-fusion references exist | Partial; no governed promotion transfer record across categories/plants/tenants |

There is no `PromotionWorkflow` state machine with conservation-gated transitions, an audit trail per transition, automatic rollback based on measured KPI degradation, and transfer isolation. Existing AgentEvolver infrastructure is a dependency, not the completed product workflow.

### F26 — Frozen Twin (P0): GAP

The PD requires a permanent parallel scorer pinned to day-one centroids and DK weights, immutable across restarts, with live-vs-frozen-vs-outcome comparisons and a drift report.

The codebase has generic checkpoints, centroid explorer/import, intervention controls, and runtime state restoration. Searches found no `FrozenTwin`, `frozen_twin`, `frozen_baseline`, `FrozenTwinRunner`, `baseline_snapshot`, or immutable checkpoint contract. Existing checkpoints are not proven to be immutable day-zero twins and do not provide the required parallel scoring comparison.

Required build: tenant-scoped immutable snapshot, restart-safe storage, parallel scoring path, outcome join, drift/report endpoint, and immutability tests.

### F27 — Counterfactual Inspector (P1): PARTIAL

The shared counterfactual router is mounted by the S2P backend, `CounterfactualCard.tsx` exists, and `counterfactual-c3.spec.ts` exercises the path. This is real counterfactual infrastructure.

The PD contract is narrower and more explanatory: for a particular decision, identify the factor(s), direction, and magnitude that would cross the action boundary, with an evidence-linked explanation such as “factor X from 0.3 to 0.7 changes hold_for_review to auto_approve.” Existing evidence establishes a counterfactual score, but not a complete per-factor boundary/delta explanation contract tied to the decision’s evidence chain. Status is PARTIAL until that response and UI acceptance test exists.

### F28 — Confidence Panel (P1): PARTIAL

Confidence, novelty, conservation, and decision counts are available in different APIs/components. `NoveltyStatusPanel.tsx`, triage score data, and conservation views provide ingredients.

Missing contract:

- No dedicated `ConfidencePanel` or `novelty_visible` implementation was found.
- Nearest-centroid distance, category verified-decision count, novelty score, and self-pause mode are not proven to be one always-visible panel with one stable response schema.
- The current UI can expose confidence-related values, but the PD explicitly requires a permanent trust state rather than a hidden/conditional detail view.

### F29 — Day-0 Data-Readiness Assessment (P1): PARTIAL

Reusable infrastructure exists:

- `copilot_sdk/substantiation/readiness.py` and `populate_readiness.py` provide generic readiness/substantiation primitives.
- `s2p-copilot/backend/app/services/cohort_status.py` and `cohort_status_router.py` expose cohort/readiness state.
- `s2p_governance.py` exposes SOX-readiness information.
- `CohortStatusPanel.tsx`, evidence, and compliance screens expose portions of the story.

Missing contract:

- No S2P `DataReadinessAssessor` or `DataReadiness` report was found.
- Coverage, freshness, identity resolution, graph connectivity/AGE availability, and safe-mode gates are not assembled into the paid Day-0 deliverable specified by the PD.
- The existing readiness endpoints are governance/cohort oriented, not a pre-scoring onboarding assessment that clearly states what the data cannot support.

## F30/F31/DIFF-1 manifest anomaly

The authoritative PD contains all three beyond the requested F1–F29 scope:

| Item | PD status | Current evidence | Gap status |
|---|---|---|---|
| F30 Cold-Start / Transfer Measurement | P1, new | Cohort status, transfer badges, and measurement primitives exist; no explicit cold-start/transfer measurement contract found | PARTIAL |
| F31 Rollback + Degradation Detection | P1, depends on F25 | Intervention/checkpoint/novelty and rollback-related fields exist; no F25-linked degradation state machine with measured rollback was found | PARTIAL |
| DIFF-1 / APP-4 Governed-vs-Ungoverned | P0, new | Governance/SOX and auto-approve gate surfaces exist | PARTIAL; the complete governed-vs-ungoverned contract and scenario acceptance should be separately reconciled |

The addendum lists F23–F31 and DIFF-1, while the task scope says F23–F29. MAP and release planning must explicitly resolve this rather than silently treating F30/F31 as either shipped or deferred.

## Cross-cutting findings

### Observation-only / auto-approve boundary

The auto-approve implementation is not an autonomous approval path:

- `s2p_auto_approve_gate.py` describes itself as a shadow-only gate.
- Gate responses include `learning_applied=False` and `outcome_written=False` in the inspected path.
- The PD itself says S2P proposes and the ERP executes; the approval queue is the write-back boundary.
- No S2P router evidence was found that silently executes an ERP purchase approval without human/ERP confirmation.

This is honest relative to the current implementation, but it means S2/S15’s “auto-approve expands” story is not yet a measured autonomous product behavior. The UI and narrative must preserve the shadow/proposal label until F23/F25 are implemented.

### `reward` / `reward_raw` occurrences

Lexical source scan counts, excluding caches and generated/vendor directories:

| Scope | Occurrences | Files | Interpretation |
|---|---:|---:|---|
| `s2p-copilot/backend/app` | 38 | 8 | Production S2P reward function, scorer wiring, outcome/evolver/audit payloads |
| `s2p-copilot/backend/tests` | 126 | 42 | S2P backend tests and fixtures |
| `copilot-sdk` S2P production surface (`copilot_sdk`, `apps/s2p`, `e2e/s2p`) | 153 | 27 | Shared scorer/types and S2P UI/E2E references |
| `copilot-sdk/tests` | 198 | 26 | Shared/S2P tests |

The production-side S2P/shared-S2P total is 191 lexical occurrences. This is a compatibility/policy concern, not evidence that the fields can simply be removed: they are wired into learning/outcome contracts and receipts. Any cross-copilot naming transition needs an explicit schema/version plan.

### Tensor shape consistency

Executable state is 5×5×8:

- `s2p-copilot/backend/app/domains/s2p/config.py`
- `copilot-sdk/copilot_sdk/scoring/presets/s2p.py`
- S2P runtime migration padding in `backend/app/main.py`
- current preset/domain tests

A scoped scan of S2P source, tests, SDK S2P surfaces, and design documentation found **96 references** to 5×5×7/seven-factor terminology. The most important stale references are:

- `s2p-copilot/CLAUDE.md` lines 32, 46, 49.
- `s2p-copilot/backend/docs/c1_c2_d1_implementation_notes.md` lines 9 and 93.
- `s2p-copilot/backend/docs/g5_g6_g7_implementation_notes.md` line 157.
- `s2p-copilot/backend/docs/implementation_plans/p41_s2p_centroid_explorer_plan.md` line 55.
- `s2p-copilot/backend/docs/implementation_plans/s2p_preset_unified_scorer_plan.md` line 20 and related passages.
- `s2p-copilot/backend/tests/test_domain_isolation.py` docstring line 170.
- `copilot-sdk/apps/s2p/frontend/src/screens/TriageScreen.tsx` and several E2E assertions label the UI “7-Factor Reasoning.”
- `copilot-sdk/docs/design/master_action_plan_v5.228 (1).md` lines 41, 269, 394, and 504.
- The authoritative PD at lines 2158, 2735, 2796, 2844, 3014–3023, 3116, 3149, 3264, and 3279.

The seven-factor references in migration tests that deliberately exercise legacy 7→8 padding are valid compatibility fixtures. The runtime, UI labels, and normative documentation must be separated from those fixtures.

### Graph backend dependency map

| Capability | SQLite/default behavior | AGE-required or AGE-enhanced behavior |
|---|---|---|
| Scoring and basic factor fallback | Works through shared GraphStore/SQLite and deterministic fallbacks | Not inherently AGE-required |
| Decisions/outcomes/learning persistence | SQLite path is available | AGE provides shared graph persistence and richer cross-domain context |
| Directed Invoice/entity context | Fallback/context bridge can degrade | `S2PGraphReader.query_direct_context` requires AGE capabilities for the intended directed query |
| Entity migration into `soc_graph` | Not applicable as an AGE graph migration | Explicit AGE DSN/graph and authorization required; migration tool refuses production `soc_graph` direct writes |
| Cross-system/process fusion | Can expose degraded/no-source state | Real graph/Celonis/entity context requires configured external/AGE sources |
| Day-0 readiness | Should report SQLite safe mode and missing graph enrichment | Must report AGE availability, graph connectivity, and migration coverage |

There is no single universal “AGE active” truth in local startup: `graph_config.toml` declares the intended AGE topology, while `s2p_graph_status.py` defaults the active S2P backend to SQLite unless explicit environment configuration enables AGE. This boundary must be visible in readiness, evidence, and product claims.

### FIX-B Commit 3 status

| Commit-3 requirement | Finding | Status |
|---|---|---|
| Save S2P centroids with `graph_store.save_centroids(domain="s2p")` | No confirmed S2P call to `save_centroids` was found in the inspected app/runtime paths | NOT STARTED / unverified |
| Startup centroid shape/hash validation | Runtime has legacy 7→8 padding and config shape checks, but no confirmed startup persisted-centroid shape/hash guard equivalent to the requested commit | PARTIAL |
| Fix 55 pre-existing 7-vs-8 failures | Current collection is 1,701, and current executable preset/tests use 8; historical docs/results remain | PARTIAL/HISTORICAL — clean current collection is evidence of migration progress, not a dated full execution artifact |
| G2 domain-labelled re-seed corpus | `s2p_initial_centroids.json` and demo data exist, but no confirmed G2 labelled calibration corpus/reseed protocol was found | NOT STARTED / unverified |

Commit 1 and Commit 2 artifacts are present. Commit 3 should not be marked DONE until persisted centroid save, startup validation, and a dated clean test run are all evidenced.

### CLAIM-59 / CLAIM-62: synthetic versus measured

The codebase does not broadly expose the numeric claims in customer-facing S2P UI/API text. The direct production-code hit found was `s2p-copilot/backend/demo/s2p_demo.py:309`, which prints a CLAIM-62 B0 validation statement. Documentation and differentiation artifacts also reference the claims, but the PD labels them synthetic/modelled or LLM-judge-derived rather than measured deployment results.

The principal risk is structural, not just wording: F26 is absent, so there is no frozen-twin mechanism that can convert the claims into measured customer-data results. The safe current position is:

- CLAIM-59 and CLAIM-62 remain synthetic/modelled evidence.
- They must not be presented as measured pilot outcomes.
- A measured conversion requires F26, actual outcomes, a defined cohort, and an auditable comparison against the day-zero baseline.

## Scenario coverage (S1–S16)

“Can demo?” means the current code can show a meaningful surface, not that every PD numeric claim is measured or that AGE-backed evidence is guaranteed.

| Scenario | Cluster | Key features needed | Can demo? | Missing pieces / qualification |
|---|---|---|---|---|
| S1 “The Exception Rate That Never Drops” | Invoice/AP | F1, F4 | Yes, surface-level | Trend can be shown, but measured quarter-over-quarter improvement needs real outcome history. |
| S2 “The Autopilot Nobody Trusts to Expand” | Earned autonomy | F5, F4, F24, F25 | Partial | Shadow gate and conservation exist; ledger, promotion state machine, and frozen baseline are missing. |
| S3 “The Same Tariff Shock, The Same 3-Month Recovery” | Disruption/strategic | F19, F20, F21 | Partial | Simulation/optimization surfaces exist; real disruption recovery evidence is modelled, not measured. |
| S4 “The Data Cleanup Project That Never Ends” | Day-0 onboarding | F29, F2 | Partial | Generic/governance readiness exists; dedicated Day-0 coverage/freshness/identity/graph report is missing. |
| S5 “The Pattern Nobody Queried” | Cross-system discovery | F17, F18, F20 | Partial | Discovery and process-fusion surfaces exist; real Celonis/source connectivity is unverified. |
| S6 “The Expertise That Walks Out the Door” | Judgment memory | F9, F12, F24, F26 | Partial | IKS/evolution exist; frozen twin and unified ledger are missing. |
| S7 “47 Suppliers Doing the Same Job” | Supplier intelligence | F13, F16, F17 | Yes, surface-level | Supplier/profile/clustering views exist; the PD count and savings are not measured evidence. |
| S8 “The ERP Lead Time That’s Always Wrong in November” | Supplier reliability | F13, F14, F15 | Yes, surface-level | Lead-time/trend paths exist; seasonal customer validation is absent. |
| S9 “The Automation That Broke Silently” | Safety/degradation | F4, F6, F12, F24, F26, F28, F31 | Partial | Novelty/conservation/evolution pieces exist; confidence panel, frozen twin, ledger, and F31 workflow are missing. |
| S10 “The Consultant’s Findings That Evaporate” | Cross-system memory | F17, F18, F24, F25 | Partial | Discovery/process-fusion UI exists; durable proposal/promotion/ledger chain is missing. |
| S11 “The Supplier That Was Fine Until It Wasn’t” | Supplier early warning | F13, F15, F16, F22 | Yes, surface-level | Early warning/compliance surfaces exist; live supplier outcome validation is absent. |
| S12 “The Working Capital Trap” | Payment/working capital | F19, F20, F21 | Yes, sandbox/advisory | Payment/optimizer/simulation surfaces exist; no production execution authority or measured financial result. |
| S13 “The System That Tunes Itself While You Sleep” | Evolution | F12, F25 | Partial | AgentEvolver/shadow batches exist; the seven-stage governed promotion workflow is missing. |
| S14 “Not a Script — A Decision” | **SPINE / situation reasoning** | F1, F2, evidence templates, traversal, F27 | Partial | Situation and evidence paths exist; graph-backed context is deployment-dependent and F27 per-factor explanation is incomplete. |
| S15 “The System That Values Caution” | **SPINE / safety** | F4, F5, DIFF-1 | Partial | Penalty/conservation/gate behavior exists; auto-approve remains shadow-only and governed-vs-ungoverned contract needs completion. |
| S16 “Where Celonis Stops, We Start” | **SPINE / process fusion** | F18, F2, F25, transfer | Partial | Process-fusion route/panel and transfer references exist; real Celonis connector/cache and closed learning/promotion/transfer loop are missing. |

### SPINE conclusions

- **S14** is the strongest current demo candidate: the bounded traversal, evidence templates, situation route, and UI are present. It must disclose when AGE/entity context is unavailable.
- **S2, S9, and S16** are not complete product proofs because their central “compounding/earned authority” story depends on F24–F26 and, for S16, a real connector/closed promotion loop.
- **S15** can demonstrate caution/hold behavior, but not autonomous approval expansion. The shadow-only boundary must remain visible.

## MAP coverage

### Existing MAP reconciliation

| MAP group | Historical scope | v1.4 relationship | Finding |
|---|---|---|---|
| P64 | Synthetic Purchasing data | Supports older fixture/demo foundations | Closed historical work; not F23–F29 |
| P65 | Purchasing tensor migration | States older 5×4×7 shape | Stale against live 5×5×8; requires documentation reconciliation |
| P66 | QBO connector | Purchasing integration | Not a v1.4 S2P moat-feature item |
| P67 | Seven factors | Older factor wiring | Historical/stale shape reference |
| P68 | Spend dashboard | Adjacent product surface | Does not implement F24 |
| P69 | Match engine | F1-adjacent | Does not implement F23 |
| P70 | Order queue | F1-adjacent | Does not implement F23 |
| P71 | Verify | F3-adjacent | Does not implement F23’s canonical proposal |
| P72 | Conservation full | F4/F5 foundation | Does not implement F25/F24 |
| P73 | Par intelligence | Not a direct S2P v1.4 feature | Historical Purchasing supplement |
| P74 | IKS scorecard | F9 foundation | Does not implement F24 |
| P75 | Trust analysis | Adjacent trust surface | Does not implement F28 |
| R7–R17 | Weather, waste, menu, event, transfer, delivery, predictive par, discovery, alerts, economics, multi-unit | Adjacent Purchasing supplements | No F23–F29 acceptance item |

### F23–F29 MAP result

No direct MAP item was found for any of F23, F24, F25, F26, F27, F28, or F29 in Tier 5 P64–P75 or supplements R7–R17. They are **MAP-MISSING**, even where implementation fragments exist.

Recommended additions:

| Proposed item | Feature | Scope | Dependencies | Minimum acceptance evidence |
|---|---|---|---|---|
| S2P-V14-00 | Shape/contract reconciliation | Make 5×5×8 authoritative across executable code, UI labels, PD, MAP, and tests | Before all v1.4 work | One canonical shape declaration, synchronized tests, legacy fixtures explicitly labelled |
| S2P-V14-01 | F23 | Proposal schema, builder, persistence, approval-queue serialization, UI, receipt | F2, F3/F5 | Decision/evidence-linked proposal API and E2E |
| S2P-V14-02 | F24 | Reconciled autonomy/compounding ledger and time-series dashboard | F9, F10, F23 | Ledger reconciles graph/scorer/outcomes without fabricated values |
| S2P-V14-03 | F25 | Discover→Shadow→Promote→Measure→Keep/Rollback→Transfer state machine | F12, F23, F24 | Conservation-gated transitions, audit trail, rollback and transfer tests |
| S2P-V14-04 | F26 | Immutable day-zero twin, parallel scorer, restart-safe storage, drift report | F24, F25 | Immutability, restart, live-vs-frozen-vs-outcome comparison |
| S2P-V14-05 | F27 | Per-factor boundary/delta counterfactual inspector | F2, F7, F23 | Evidence-linked “what would change my mind” response/UI/E2E |
| S2P-V14-06 | F28 | Always-visible confidence/novelty/self-pause panel | F6 | Stable response schema and low-confidence routing E2E |
| S2P-V14-07 | F29 | Day-0 source coverage/freshness/identity/graph/safe-mode assessment | New; shared readiness primitives | Onboarding report and partial-data safety tests |

F30, F31, and DIFF-1 require separate MAP disposition because they are in the checked-in PD/addendum but outside the requested F23–F29 scope.

## Recommendations

### Demo-blocking

1. Preserve the shadow-only label for auto-approve; do not narrate it as autonomous ERP execution.
2. Add an explicit runtime badge for SQLite safe mode versus AGE-enriched mode.
3. Reconcile the 5×5×8 executable shape and remove/label stale seven-factor UI/document references.
4. Use S14 as the primary hero demo, with explicit evidence degradation when graph context is unavailable.

### Pilot-blocking

1. Build F23 first. F24–F26 depend on its canonical decision-change identity.
2. Build F24 as a reconciled ledger, not another independent dashboard with copied metrics.
3. Implement F25 as a persisted, audited state machine; connect it to conservation and measured KPI outcomes.
4. Implement F26 before presenting CLAIM-59/CLAIM-62 as anything other than synthetic/modelled.
5. Complete F29 before claiming Day-0 deployment on dirty data.

### Next tranche / roadmap

1. Complete F27’s per-factor flip explanation and evidence linkage.
2. Complete F28’s always-visible confidence panel.
3. Close F18 with a verified Celonis/cache ingestion path and process-fusion learning loop.
4. Resolve F30/F31/DIFF-1 scope and add them to the authoritative MAP.
5. Decide and document the cross-copilot `reward`/`reward_raw` protocol policy rather than removing fields opportunistically.

## Final assessment

The original S2P operational product surface is substantially implemented: scoring, triage, verification, conservation, evidence, supplier intelligence, optimization, simulation, and audit paths have real backend/frontend/test evidence. The v1.4 moat surface is not equivalently complete. The missing canonical proposal and frozen twin are architectural gaps, not missing cosmetic panels; they are the objects required to make ledger, promotion, and measured-improvement claims honest and composable.

The correct next action is a P0 implementation program for F23–F26 with a shape/contract reconciliation item first. No v1.4 claim of measured compounding or earned autonomous authority should ship until those dependencies have persisted, restart-safe, graph/scorer-reconciled acceptance tests.
