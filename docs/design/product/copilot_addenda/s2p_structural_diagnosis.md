# S2P Copilot — Structural Diagnosis

Date: 2026-08-17  
Scope: read-only structural discovery across the dedicated S2P repository, the shared SDK repository, and the SOC/AGE repository. The only file created by this discovery is this report.

## Executive summary

The S2P product is split across three repositories, but only two of them are on the live product path:

- `s2p-copilot` is the primary S2P backend and owns the scoring, graph reader, factor computers, learning/outcome flow, domain services, and backend tests.
- `copilot-sdk` owns the shared scoring/graph infrastructure, the S2P frontend on port 5177, and the S2P Playwright suite.
- `gen-ai-roi-demo-v4-v50` is the SOC application. It contains a legacy/duplicate supply-chain configuration and the frozen S2P Preview surface, but its `backend/app/main.py` does not mount the S2P backend. Its frontend proxies S2P Preview requests to port 8002.

The current dedicated backend is materially newer than several design and MAP snapshots. The executable S2P configuration and SDK preset are both 5×5×8, with eight concrete factor computers. The MAP v5.228 and several repository documents still describe 5×5×7. The dedicated backend test suite currently collects 1,701 tests; the old 926-test and 7-factor references are historical, not a reliable statement of current implementation.

The v1.4 features F23–F29 are not represented as a coherent feature program in MAP v5.228. There are useful partial building blocks—counterfactuals, evolution, novelty, financial impact, audit, and readiness—but no evidence of the required canonical Decision-Change Proposal, Compounding Ledger, Frozen Twin, or Day-0 product contract as named, end-to-end surfaces.

## Repo layout

| Repository | Absolute path | Remote | Branch | Latest tag observed | Files / scanned size |
|---|---|---|---|---|---|
| copilot-sdk | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk` | `git@github.com:ArindamBanerji/copilot-sdk.git` | `main` | `v0.9.23` by repository tag-date listing; `v0.9.25` is also present | 5,830 / 348,089,347 bytes, excluding generated/vendor directories |
| s2p-copilot | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot` | `git@github.com:ArindamBanerji/s2p-copilot.git` | `main` | `v0.7.34-s2p` | 662 / 153,252,953 bytes, excluding generated/vendor directories |
| gen-ai-roi-demo-v4-v50 | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50` | `git@github.com:ArindamBanerji/gen-ai-roi-demo.git` | `v5.0-dev` | `v5.122` | 4,046 / 451,796,809 bytes, excluding generated/vendor directories |

The top-level layout relevant to S2P is:

```text
copilot-sdk/
  apps/s2p/frontend/       product frontend, port 5177
  copilot_sdk/             shared Python SDK and graph/scoring infrastructure
  e2e/s2p/                 S2P Playwright suite
  docs/design/             PDs, addenda, MAP, implementation designs
  tests/                   shared SDK tests

s2p-copilot/
  backend/app/             primary S2P FastAPI backend
  backend/tests/           dedicated S2P backend tests
  backend/data/            runtime/demo state
  data/                    seed/demo data and centroid artifacts
  docs/                    S2P implementation and migration notes

gen-ai-roi-demo-v4-v50/
  backend/app/             SOC backend; no S2P backend router mount
  frontend/src/            SOC UI, including S2P Preview
  frontend/tests/e2e/      SOC and Preview Playwright tests
  backend/scripts/         SOC/AGE census and migration utilities
```

## S2P code map

### In `s2p-copilot`

This is the primary S2P backend, not a historical fork. It has its own `backend/app`, its own 141-file backend test tree, and a current collection result of 1,701 tests.

Key paths:

| Concern | Path | Finding |
|---|---|---|
| Application factory/startup | `s2p-copilot/backend/app/main.py` | Builds the S2P scorer, graph store, evolver provider, state restoration, and mounts shared plus S2P-specific routers. |
| Score/learn/outcome API | `s2p-copilot/backend/app/routers/s2p.py` | `/api/s2p/score`, `/api/learn`, `/api/s2p/outcome`; score and mutation paths use the shared per-domain mutation lock. |
| Domain configuration | `s2p-copilot/backend/app/domains/s2p/config.py` | Executable 5 categories × 5 actions × 8 factors configuration. |
| Factor computers | `s2p-copilot/backend/app/domains/s2p/factors.py` | Eight concrete factor classes, including `MatchStatus` and `TaxRegulatoryCompliance`; graph/metadata/fixture fallbacks are explicit. |
| Scoring preset | `copilot-sdk/copilot_sdk/scoring/presets/s2p.py` | Shared `S2PPreset`, 5×5×8 bootstrap tensor and legacy 7→8 migration padding. |
| Directed graph reader | `s2p-copilot/backend/app/graph/s2p_graph_reader.py` | `S2PGraphReader` wraps the shared `GraphStore`; `query_direct_context` performs bounded directed Invoice/entity reads when AGE is available. |
| Traversal pattern | `s2p-copilot/backend/app/services/s2p_situation_pattern.py` | `S2PInvoiceTraversalPattern` and situation context assembly. |
| Entity migration | `s2p-copilot/backend/app/migration/s2p_entity_migration.py` | Non-destructive AGE writer for disposable/test graphs; explicitly refuses direct writes to production `soc_graph`. |
| Auto-approve | `s2p-copilot/backend/app/services/s2p_auto_approve_gate.py` and `app/domains/s2p/auto_approve.py` | Gate and API exist, but the service is explicitly shadow-only; it does not execute autonomous approval. |
| Learning gate | `s2p-copilot/backend/app/services/s2p_learning_gate.py` | Controls when centroid updates are allowed; requires minimum decisions and quality checks. |
| Evolution | `s2p-copilot/backend/app/services/s2p_evolver.py`, `app/domains/s2p/evolution/service.py` | Variant storage, triage outcome recording, shadow batches, and promotion evaluation. |
| Evidence/situation | `app/routers/s2p_evidence.py`, `app/routers/s2p_situation.py`, `app/services/s2p_evidence_templates.py` | Mounted in `main.py`; evidence and directed-context paths are implemented. |
| Product services | `app/routers/financial_router.py`, `lead_time_router.py`, `s2p_suppliers.py`, `s2p_early_warning.py`, `s2p_clustering.py`, `s2p_discovery.py`, `s2p_payment.py`, `optimizer_router.py`, `s2p_simulation.py`, `compliance_router.py`, `s2p_process_fusion.py` | Broad feature surface exists in backend routes and services. |
| Runtime graph selection | `s2p-copilot/backend/app/s2p_graph_status.py` | AGE is supported with explicit environment/configuration and authorization; absent active AGE configuration defaults to SQLite. |
| Repository guidance | `s2p-copilot/CLAUDE.md` | Useful ownership and contract guidance, but its 5×5×7 and old test-count statements are stale against executable code. |

There is no `s2p-copilot/frontend/` directory. The frontend is not duplicated in this repository.

### In `copilot-sdk`

The SDK repository contains the shared platform and the S2P product frontend.

| Concern | Path | Finding |
|---|---|---|
| Shared scoring | `copilot-sdk/copilot_sdk/scoring/` | Shared `CompoundingScorer`, profile scoring, learning, presets, and evolution primitives. |
| Shared graph | `copilot-sdk/copilot_sdk/graph/` | Shared GraphStore protocol/factory, SQLite implementation, AGE implementations and transaction/locking support. |
| Shared situation analysis | `copilot-sdk/copilot_sdk/situation/analyzer.py` | Domain-agnostic `SituationAnalyzer` used by S2P services. |
| S2P preset | `copilot-sdk/copilot_sdk/scoring/presets/s2p.py` | `S2PPreset`; executable shape is 5×5×8, not 5×5×7. |
| S2P frontend | `copilot-sdk/apps/s2p/frontend/` | 69 files, 62 TypeScript/TSX files; Vite port 5177 and API default port 8002. |
| S2P E2E | `copilot-sdk/e2e/s2p/` | 37 files and 212 `test`/`it` call sites in the local source scan. |
| Shared E2E/API contract | `copilot-sdk/e2e/s2p/active-age-smoke.spec.ts`, `score-path`, `situation-analyzer`, `counterfactual-c3`, `day-zero`, `process-fusion`, `auto-approve` suites | Exercises the product surface against port 8002. |
| Configuration declaration | `copilot-sdk/graph_config.toml` | Declares S2P as AGE-backed on `soc_graph`, port 8002; runtime active-backend selection still requires explicit S2P AGE configuration. |

Important frontend evidence includes `ProcessFusionPanel.tsx`, `CounterfactualCard.tsx`, `SituationPanel.tsx`, `NoveltyStatusPanel.tsx`, `S2PConservationProjection.tsx`, `AutoApprovePanel.tsx`, supplier panels, payment strategy, evidence, compliance, audit, and financial-impact panels.

### In `gen-ai-roi-demo-v4-v50`

This repository is not the primary S2P backend.

- `backend/app/main.py` mounts SOC routers and does not mount the S2P backend router.
- `frontend/src/components/tabs/S2PPreviewTab.tsx` is the frozen/investor Preview surface.
- The SOC frontend proxies `/api/s2p/preview/*` to port 8002 when the SOC backend has no matching route. `backend/CODEBASE.md` documents this boundary.
- `backend/app/domains/supply_chain/config.py` contains a duplicate/legacy `S2PDomainConfig`, but its situation/factor implementation comments contain TODO/not-implemented language. It must not be mistaken for the live dedicated S2P domain configuration.
- `backend/scripts/soc_domain_census.py` and related SOC documentation inspect the shared `soc_graph` and report S2P entity/decision counts. These are census/diagnostic utilities, not the S2P score service.
- The SOC frontend E2E tree has 21 S2P-named files and 104 `test`/`it` call sites in the local scan, primarily covering Preview and proxy contracts.
- `backend/tests/test_s2p_sdk_validation.py` is a small cross-domain validation file; it does not make the SOC backend the S2P runtime.

The shared surface is therefore the graph namespace/census and shared SDK contracts, not a duplicated live S2P API.

## Dependency diagram

```text
Invoice / S2P score request
  → s2p-copilot/backend/app/routers/s2p.py
  → s2p-copilot/backend/app/domains/s2p/factors.py
       MatchStatus, AmountVarianceRatio, DuplicateScore,
       SupplierExceptionHistory, PaymentTermsImpact,
       CommodityIndexCorrelation, TaxRegulatoryCompliance,
       EnvironmentalRisk
  → s2p-copilot/backend/app/main.py::build_s2p_scorer
  → copilot-sdk/copilot_sdk/scoring/scorer.py::CompoundingScorer
       S2PPreset 5×5×8, profile centroids, diagonal kernel,
       learn/outcome and conservation integration
  → copilot-sdk/copilot_sdk/graph/factory.py::create_graph_store
       default runtime: SQLite unless explicit S2P AGE config is enabled
       AGE option: shared AGEGraphStore → soc_graph
  → S2PGraphReader
       query_context / query_direct_context for Invoice/entity evidence
  → s2p_auto_approve_gate
       shadow-only gate; no autonomous production execution
  → response and frontend
       copilot-sdk/apps/s2p/frontend, port 5177
```

The SOC Preview path is separate:

```text
SOC frontend S2PPreviewTab
  → /api/s2p/preview/* proxy
  → port 8002 s2p-copilot backend
```

The S2P backend imports the shared SDK through normal Python imports from the environment/package path, not by copying the SDK source into `s2p-copilot`.

## Test inventory

Counts are source/collection counts, not claims that every suite was executed in this discovery session.

| Repo/surface | Backend test files | Backend tests | E2E files | E2E call sites | Integration/contract evidence |
|---|---:|---:|---:|---:|---|
| `s2p-copilot/backend` | 141 total | 1,701 collected | — | — | Dedicated active-AGE, graph-contract, score-path, learning, outcome, and worked-example tests are present. |
| `copilot-sdk` S2P surface | shared tests plus S2P-specific SDK tests | not isolated without executing a marker-specific collection | 37 | 212 | S2P preset, graph, router, and cross-copilot contract tests exist under `copilot-sdk/tests/`. |
| `gen-ai-roi-demo-v4-v50` S2P-related surface | 8 broadly S2P-referencing files; `test_s2p_sdk_validation.py` has 5 direct tests | 66 broad S2P-referencing definitions in source scan | 21 | 104 | Preview/proxy and SDK validation tests; not the primary backend suite. |

The dedicated repository also contains `backend/test_results_s2p.txt` and older planning documents reporting much smaller historical runs (for example 58 or 701 tests). Those are not current collection results. The current authoritative local collection result is 1,701.

## Feature component table

The current PD file is `copilot-sdk/docs/design/product/s2p_copilot_unified_v1_4.md`. The names and priorities below follow its F1–F29 manifest. “Original” means present before the final addendum; “NEW” means introduced by the v1.4 addendum. MAP coverage refers specifically to v5.228 Tier 5 (P64–P75) and Purchasing supplements R7–R17.

| Feature | Name | Priority | Section / dependency | Origin | Evidence | Status | MAP item |
|---|---|---|---|---|---|---|---|
| F1 | Exception Triage Dashboard | P0 | PD feature surface | Original | `/api/s2p/score`, queue/triage frontend, backend and E2E coverage | LIVE | P70/P71 are related legacy queue/verify entries |
| F2 | Situation-Aware Evidence Panel | P0 | S14; evidence/context | Original | `S2PGraphReader`, `S2PInvoiceTraversalPattern`, situation/evidence routers, `SituationPanel`, E2E | LIVE for current bounded scope | No direct v1.4 item; older evidence work is elsewhere in MAP |
| F3 | One-Click Verification Console | P0 | verification/outcome loop | Original | `/api/s2p/outcome`, `/api/learn`, outcome receipts, verification UI and tests | LIVE | P71 PUR-VERIFY |
| F4 | Conservation Dashboard | P0 | conservation | Original | shared conservation routers, S2P conservation projection/gauges, tests | LIVE | P72 PUR-CONSERVATION-FULL |
| F5 | Auto-Approve Engine | P0 | gate/conservation/novelty | Original | auto-approve routes, `AutoApproveGate`, `AutoApprovePanel`, tests | PARTIAL — explicitly shadow-only; no autonomous execution | P72 related, but not a complete live approval engine |
| F6 | Novelty Detection & Auto-Pause | P1 | novelty and pause controls | Original | novelty router/tracker, novelty UI, gate controls and tests | PARTIAL — novelty is present; complete product-level auto-pause contract is not proven | No direct P64–P75/R7–R17 item |
| F7 | Centroid Explorer | P1 | centroid inspection | Original | centroid router, explorer components, E2E/API tests | LIVE | P65 is an old tensor-migration item, not this feature |
| F8 | Factor Proposer | P1 | advisory factor proposal | Original | `factor_proposer_router.py`, factor proposer service/UI/tests | PARTIAL — advisory proposal exists; accepted replacement/requalification workflow is not shown | No direct item |
| F9 | IKS Tracker | P0 | IKS | Original | S2P IKS endpoint/tests and frontend IKS/conservation surfaces | LIVE | P74 PUR-IKS-SCORECARD is related legacy work |
| F10 | Financial Impact Ledger | P1 | economics/impact | Original | `financial_router.py`, financial impact service/panels/tests | PARTIAL — financial impact exists; canonical autonomy/compounding ledger is absent | R16 PUR-ECON is related, not the v1.4 ledger contract |
| F11 | Audit & Export Pack | P0 | audit/evidence | Original | audit export router, audit framework, audit panels, receipts/tests | LIVE | No exact Tier-5 item; audit was a platform capability |
| F12 | AgentEvolver — Self-Tuning Operations | P1 | evolution | Original | `s2p_evolver.py`, evolution service/router, SQLite variant store, UI/tests | LIVE for variant/evolution primitives | R11 includes transfer/evolution-adjacent work, but not F12’s complete contract |
| F13 | Supplier Behavioral Profile Builder | P1 | supplier intelligence | Original | supplier profile accumulator, supplier routers/services/UI/tests | LIVE | R10/R17 are adjacent supplements |
| F14 | Lead Time Intelligence | P1 | lead time | Original | lead-time router/service/UI/tests | LIVE | R13 PUR-PREDICTIVE-PAR is adjacent, not full F14 |
| F15 | Supplier Trend Correlation & Early Warning | P1 | trend/early warning | Original | early-warning router/service/UI/tests | LIVE | No exact Tier-5/R7–R17 item |
| F16 | Behavioral Clustering | P1 | clustering | Original | clustering router/service/UI/tests | LIVE | R14 PUR-CROSS-DISCOVERY is adjacent |
| F17 | Cross-System Discovery Alerts | P1 | discovery | Original | discovery routers/services/UI/tests | LIVE/shadow-scoped | R14/R15 are adjacent historical entries |
| F18 | Process-Tech Fusion Loop | P1 | process fusion | Original | process-fusion router/service/panel/tests | PARTIAL — UI/API surface exists; real Celonis connector/cache and closed fusion-learning loop are not evidenced in S2P |
| F19 | Payment Timing Optimization | P2 | payment optimization | Original | payment router/service/UI/tests | LIVE/PARTIAL — advisory surface exists; production optimizer authority needs contract verification | No direct Tier-5/R7–R17 item |
| F20 | Centroid-to-Optimizer API | P2 | optimizer export | Original | optimizer router/export service/tests | LIVE for API/export surface | R17 is related multi-unit work, not this API |
| F21 | Disruption Simulation Sandbox | P2 | simulation | Original | simulation router/service/UI/tests | LIVE for sandbox surface | No direct item |
| F22 | Compliance Screening with Conservation Proof | P2 | compliance | Original | compliance router/screener, governance/SOX readiness, UI/tests | PARTIAL — screening/proof pieces exist; end-to-end legal/compliance evidence contract needs product verification | No direct item |
| F23 | Decision-Change Proposal | P0 | F2 + F5 | NEW | No `DecisionChange`/`ProposalBuilder` or canonical proposal endpoint found; generic evolution/factor proposals are not the same object | GAP | MAP-MISSING |
| F24 | Autonomy / Compounding Ledger | P0 | F9 + F10 | NEW | Financial, IKS, conservation, audit and evolution pieces exist, but no `CompoundingLedger`/`autonomy_ledger` canonical aggregation found | PARTIAL | MAP-MISSING |
| F25 | Decision-Class Promotion Workflow | P0 | F12 | NEW | Shadow batches and promotion evaluation exist in S2P evolution; no named end-to-end Discover→Shadow→Promote→Measure→Keep/Rollback→Transfer workflow found | PARTIAL | MAP-MISSING |
| F26 | Frozen Twin | P0 | New | NEW | No `FrozenTwin` or `frozen_baseline` implementation found; checkpoints/shadow state are not a frozen twin contract | GAP | MAP-MISSING |
| F27 | Counterfactual Inspector | P1 | F2 + F7 | NEW | Shared counterfactual router is mounted; `CounterfactualCard.tsx` and E2E exist | PARTIAL — functional counterfactual exists, exact “what would change my mind” inspection contract is not established | MAP-MISSING |
| F28 | Confidence Panel | P1 | F6 | NEW | Confidence is present in score/queue data and novelty panels; no dedicated `ConfidencePanel`/`novelty_visible` contract found | PARTIAL | MAP-MISSING |
| F29 | Day-0 Data-Readiness Assessment | P1 | New | NEW | Shared readiness/substantiation modules and S2P SOX-readiness endpoint exist; no dedicated `DataReadiness`/Day-0 S2P product workflow found | PARTIAL | MAP-MISSING |

### Manifest scope anomaly

The checked-in v1.4 PD also contains F30, F31, and DIFF-1 in its later summary/roadmap sections. The requested inventory stops at F29, but this is itself a manifest inconsistency: the addendum lists F23–F31 and DIFF-1, while the task’s feature scope names F23–F29. F30/F31 should be explicitly included or excluded in the next gap-analysis authority document; they should not silently enter implementation scope.

## Dependency map and graph status

### Graph ownership

S2P uses the shared SDK `GraphStore` protocol and factory. The S2P reader is an S2P-specific adapter over that shared interface. AGE support exists, and `copilot-sdk/graph_config.toml` declares `soc_graph`, but the dedicated S2P active configuration defaults to SQLite unless `S2P_ACTIVE_GRAPH_BACKEND=age` and the corresponding DSN/graph settings are supplied. The migration writer intentionally restricts writes to disposable/test AGE graphs and refuses direct production `soc_graph` writes.

Therefore the statement “S2P uses AGE `soc_graph`” is configuration-dependent, not universally true for every local startup. The structural contract is shared GraphStore; the active persistence backend must be recorded per deployment.

### Scoring path

The factor path is real rather than a stub in the dedicated backend. `MatchStatus` and `TaxRegulatoryCompliance` have graph/metadata computations with explicit fallback behavior, and the remaining six factor classes are also present in `ALL_FACTORS`. The scorer receives an eight-dimensional vector from `compute_all_factors`/`compute_factor_vector`, then scores against `S2PPreset`’s 5×5×8 tensor.

The current score path has a per-domain mutation lock with a bounded three-second acquisition timeout and SQLite write transactions with commit/rollback and retry handling. This addresses the known lock-stall/atomic-write concern structurally, although a production concurrency test is still required before treating it as a measured SLO guarantee.

## Known issue status

### 1. Tensor shape

**Live answer: 5×5×8.**

Evidence:

- `s2p-copilot/backend/app/domains/s2p/config.py` defines eight factors and dimensions `(5, 5, 8)`.
- `copilot-sdk/copilot_sdk/scoring/presets/s2p.py` defines eight factor names and an 8-wide bootstrap tensor.
- `s2p-copilot/backend/app/main.py` contains explicit legacy 7→8 runtime padding.
- `copilot-sdk/tests/test_s2p_preset.py` asserts the eight-factor preset.

The 5×5×7 statements in `s2p-copilot/CLAUDE.md`, `backend/docs/s2p_phase2_scan.md`, the MAP v5.228 overview, and parts of the PD are stale documentation. P65’s historical “5×4×7” wording is not the live S2P shape.

### 2. Historical 55-test failure claim

The current local collection is 1,701 tests, not 926. The repository contains historical plans/results describing smaller baselines (701, 58, and related migration notes), but the discovery scan found no current authoritative artifact proving that 55 failures remain. The 7→8 migration is represented in runtime padding and current tests. Treat “55 failures” as a historical work-package statement until a dated executed run is supplied.

### 3. Stub versus real factors

The dedicated S2P factor module has eight concrete classes and an `ALL_FACTORS` registry. No `pass`/`NotImplementedError` stub was found in the factor registry. Several factors intentionally degrade to deterministic fallback values when graph/context evidence is unavailable; that is an evidence-availability behavior, not proof that the factor is a stub.

The SOC repository’s duplicate `backend/app/domains/supply_chain/config.py` still contains TODO/not-implemented language and is not the live S2P factor path.

### 4. `reward` and `reward_raw`

These fields are present in S2P production-related code:

- `s2p-copilot/backend/app/domains/s2p/reward.py` and `main.py` wire `S2PRewardFunction` into the scorer.
- `s2p-copilot/backend/app/routers/s2p.py` accepts/propagates reward fields in outcome/evolution payloads.
- `backend/app/models/outcome_receipt.py` stores reward fields.
- The shared SDK scorer also has reward-related fields.

This is a cross-copilot compatibility/policy concern to carry into gap analysis. It is not absent, and it should not be “fixed” by deleting fields without an explicit protocol migration.

### 5. Score-path lock and atomic write

The dedicated score, learn, and outcome paths use `get_mutation_lock("s2p")`; the shared SDK has a process-wide per-domain lock. SQLite graph writes are guarded by per-database locks and transactional commit/rollback with retry handling. The path is therefore structurally protected against the previously identified concurrent overwrite/lock-stall class, with the caveat that the bounded acquire timeout can return a failure under sustained contention.

## Product directory audit

| Artifact | Result |
|---|---|
| Merged S2P PD | `copilot-sdk/docs/design/product/s2p_copilot_unified_v1_4.md` exists; it is a combined engineering + product document, with engineering sections §1–§20 and product sections §PD1–§PD14. |
| Duplicate PD | `copilot-sdk/docs/design/s2p_copilot_unified_v1_4.md` also exists outside `product/`; authority should be clarified. |
| S2P addendum | `copilot-sdk/docs/design/ci_reviews_and_addenda/final_addenda/s2p_copilot_addendum_FINAL_v1.md` exists. It describes F23–F31 and DIFF-1 and still contains wording that the base v1.3 was untouched/no addenda merged, which conflicts with the checked-in merged v1.4 PD. |
| Purchasing addendum | `copilot-sdk/docs/design/ci_reviews_and_addenda/final_addenda/purchasing_copilot_addendum_FINAL_v1.md` exists but is not the S2P authority. |
| MAP | `copilot-sdk/docs/design/master_action_plan_v5.228 (1).md` exists. Tier 5 P64–P75 and R7–R17 are marked closed/pass historical Purchasing work, not F23–F29 S2P work. |
| Preview | SOC frontend `S2PPreviewTab.tsx` and S2P Preview E2E files exist; the SOC backend delegates missing Preview routes to port 8002. |

## MAP coverage and gap interpretation

Tier 5 P64–P75 covers synthetic data, tensor migration, QBO, factors, spend dashboard, match engine, order queue, verification, conservation, par intelligence, IKS scorecard, and trust analysis. R7–R17 covers weather, prep waste, menu engineering, event catering, chain transfer, delivery, predictive par, cross-discovery, alerts, economics, and multi-unit work.

Those entries explain why the older S2P/Purchasing surface is represented as “closed/pass,” but they do not provide MAP work items for the v1.4 F23–F29 contracts. In particular, no item was found for Decision-Change Proposal, Compounding Ledger, Promotion Workflow, Frozen Twin, Counterfactual Inspector, Confidence Panel, or Day-0 Readiness Assessment.

## Recommended MAP additions

The following should be added as new, dependency-ordered S2P MAP items rather than retroactively relabeling old P64–P75 work:

| Proposed item | Scope | Depends on | Acceptance evidence |
|---|---|---|---|
| S2P-V14-01 / F23 | Canonical Decision-Change Proposal schema, builder, endpoint, persistence, UI, and audit receipt | F2, F5, outcome contract | API/schema contract, UI E2E, persisted proposal linked to decision and evidence |
| S2P-V14-02 / F24 | Unified autonomy/compounding ledger combining decision, outcome, IKS, conservation, financial impact, and provenance | F9, F10, F23 | Ledger reconciliation against graph/scorer state; no fabricated customer-facing values |
| S2P-V14-03 / F25 | Discover→Shadow→Promote→Measure→Keep/Rollback→Transfer workflow with gates | F12, F23, F24 | State-machine tests, rollback test, promotion audit, transfer isolation test |
| S2P-V14-04 / F26 | Immutable frozen twin/baseline and comparison API | F24, F25 | Baseline immutability, restart test, drift report, rollback comparison |
| S2P-V14-05 / F27 | Named counterfactual inspector with evidence-linked “what would change my mind” output | F2, F7, F23 | Counterfactual response schema, factor-delta explanation, E2E |
| S2P-V14-06 / F28 | Dedicated confidence/novelty panel and routing explanation | F6, F25 | Threshold/geometry contract, low-confidence route test, UI E2E |
| S2P-V14-07 / F29 | Day-0 readiness assessment with data coverage, freshness, identity, graph, and safe-mode gates | new; shared readiness primitives | Empty/partial/full data scenarios, readiness API, UI and safe-mode evidence |
| S2P-V14-00 | Reconcile 5×5×8 as the authoritative tensor and update stale MAP/PD/CLAUDE references | all feature work | One canonical shape declaration and synchronized contract tests |

F5’s shadow-only status and the AGE/SQLite deployment choice should be explicit acceptance dimensions in the new items.

## Priority queue

### Demo-blocking

1. Keep the port/proxy boundary explicit: product frontend 5177, backend 8002, SOC Preview proxy separate.
2. Reconcile the authoritative 5×5×8 tensor statement across PD, MAP, CLAUDE, and phase docs.
3. Do not present shadow-only auto-approve as autonomous approval.
4. Mark the active graph backend and evidence fallback state in demo diagnostics.

### Pilot-blocking

1. F23 canonical Decision-Change Proposal.
2. F24 unified autonomy/compounding ledger.
3. F25 promotion state machine with rollback and transfer isolation.
4. F26 frozen twin and immutable baseline.
5. F29 Day-0 readiness gates, especially for AGE availability and graph coverage.

### v1.1 / next implementation tranche

1. F27 named counterfactual inspector.
2. F28 confidence panel with threshold and routing explanations.
3. Complete F18 Celonis/process-fusion connector and closed learning loop.
4. Complete F5 auto-approve execution only after the conservation, novelty, proposal, and rollback gates are real.

### Roadmap / clarification

1. Decide whether F30/F31/DIFF-1 are in the v1.4 manifest or a subsequent release.
2. Retire or label the duplicate SOC `supply_chain` configuration as legacy.
3. Decide whether `reward`/`reward_raw` are permitted protocol fields and document the cross-copilot contract.
4. Replace historical test-result claims with dated collection/execution artifacts.

## Directory context block (for the gap-analysis prompt)

```text
S2P backend:        C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend
S2P frontend:       C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\s2p\frontend
S2P E2E tests:      C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\e2e\s2p
Shared SDK:         C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk
S2P domain config:  C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\domains\s2p\config.py
S2P factor code:    C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\domains\s2p\factors.py
S2P graph reader:   C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\graph\s2p_graph_reader.py
AGE graph setup:    C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\migration\s2p_entity_migration.py
AGE/runtime config: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\s2p_graph_status.py
Shared graph config:C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\graph_config.toml
S2P PD:             C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\product\s2p_copilot_unified_v1_4.md
S2P PD duplicate:   C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\s2p_copilot_unified_v1_4.md
S2P addenda:        C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\ci_reviews_and_addenda\final_addenda\s2p_copilot_addendum_FINAL_v1.md
MAP:                C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\master_action_plan_v5.228 (1).md
SOC/Preview repo:   C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50
SOC Preview tab:    C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend\src\components\tabs\S2PPreviewTab.tsx
```

## Discovery boundary

This report did not run the full S2P, SDK, or Playwright suites and did not inspect a live AGE DSN. Counts and statuses are based on checked-in source, collection metadata where available, route mounts, and named test evidence. Runtime claims about `soc_graph` population, port availability, and deployed backend selection require a separate environment-level verification.
