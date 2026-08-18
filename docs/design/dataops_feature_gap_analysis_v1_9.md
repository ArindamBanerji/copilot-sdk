# DataOps Copilot v1.9 Feature Gap Analysis

**Review date:** 2026-08-17  
**PD baseline:** `docs/design/dataops_copilot_design_v1_9.md`  
**Addendum:** `docs/design/ci_reviews_and_addenda/final_addenda/dataops_copilot_addendum_FINAL_v1.md`  
**MAP baseline:** `docs/design/master_action_plan_v5.228 (1).md`

## Executive conclusion

The v1.9 PD is not represented by the old MAP's “zero gaps” conclusion. The old audit covers the first implementation wave—P30/P32/P34, P42-P44, and R27-R30—but not the four SC reification surfaces, the final addendum's evidence-gated contracts, or the newly named DI-* demo controls.

The most important correction is nuanced. The previously suspected DataOps outcome loop is now structurally wired: `create_app()` constructs a production `PromptVariantEvolver`, the scoring router calls `scorer.learn()`, and then invokes the DataOps outcome recorder (`apps/dataops/backend/app/main.py:641-666`, `copilot_sdk/backend/scoring_router.py:238-260`). That proves the scorer path is connected, but it does not prove every verified decision carries a variant ID, that variant statistics are updated for every decision, or that the resulting trust movement has been demonstrated end to end. The addendum's “proof of learning” and earned-trust claims therefore remain `NEAR`, not universally `LIVE`.

Highest-priority findings:

1. The addendum's SC-IKS-ATTR, SC-FORECAST, and SC-DIGEST services and panels are not present.
2. DI-ABSTAIN, DI-FIRSTVS6TH, DI-TWIN, and the thin MCP trust gateway are not implemented as specified.
3. DI-4's `SourceIntegrator` exists in the SDK, but DataOps has no route or product surface that wires it.
4. The Intelligence Map's WebSocket learning pulse is explicitly deferred in the SDK model (`copilot_sdk/di/intelligence_map.py:63-71`), and the map builder does not provide the addendum's FDR, holdout, and value-provenance gates.
5. Production DataOps code contains `reward` metadata compatibility reads at `apps/dataops/backend/app/context_router.py:571,1521,1531`; no `rl_`, `policy_`, or `reinforcement` production hits were found.

## 1. Feature/Capability Manifest

The manifest below is extracted from the current PD's own vocabulary. The PD says §1-§28 are unchanged from v1.5 and refers to that older document as authoritative; that v1.5 document is not present in this checkout. I therefore record the inherited surface at the level the v1.9 document exposes it, rather than inventing individual v1.5 feature IDs.

### 1.1 Inherited engineering surface

| PD reference | Manifest item | PD contract / dependency |
|---|---|---|
| §1-§28 summary, lines 19-27 | Process-Tech Fusion | WHERE → WHY → WHAT → LEARN → TRANSFER; 26-endpoint engineering surface; SAP + Celonis; depends on the inherited v1.5 design. |
| §1-§28 summary, lines 22-27 | DomainConfig and graph schema | Domain tensor `(6,5,6)=180`; SAP, Celonis, and transformation graph; depends on ONE GraphStore. |
| §1-§28 summary, lines 23-27 | Preseed/storyboard/evolution foundation | IKS 19.0 preseed, five-act storyboard, ONE Store with 13 capabilities, self-computation, enterprise connectors, SDK architecture, and standing rules. |

### 1.2 Category capabilities

| ID | Name | PD meaning | Section / tier |
|---|---|---|---|
| H1 | Self-Aware Data | Per-source and per-column reliability learned from verified outcomes and DiagonalKernel weights. | §36 H1; Level 3-5; depends on the verified-outcome loop and DI-1. |
| H2 | Self-Combining Data | Cross-graph discovery of value-creating source combinations. | §36 H2; Level 6; depends on DI-5 and evidence gates. |
| H3 | Self-Correcting Data | Centroid learning plus conservation enables recurring fixes and safe expansion. | §36 H3; Level 3-4; depends on scorer, AgentEvolver, and conservation. |
| H4 | Self-Governing Data | Conservation and per-consumer quality routing govern automation. | §36 H4; Level 4; depends on conservation and consumer-quality evidence. |
| H5 | Self-Valuating Data | Economic valuation identifies what additional data would create value. | §36 H5; Level 6; depends on DI-5/6/8 and the addendum's value-provenance gate. |
| H6 | Agent-Ready Trust Infrastructure | External agents query source trust and receive policy-aware trust/read-only/abstain decisions. | §36 H6 / §40 L.5; Level 4-5; depends on DI-1, conservation, and the corrected gateway contract. |

### 1.3 PD scenarios

The PD explicitly defines seven market scenarios (§32) and fifteen innovation scenarios (§33). The descriptions are abbreviated here, but each row is a separate manifest item.

| ID | Scenario name / capability | PD section | Dependencies |
|---|---|---|---|
| D-M1 | Alert Fatigue — 400/Day, 45% Noise | §32 | Verified triage outcomes, AgentEvolver, measurable noise resolution. |
| D-M2 | Data Quality Metrics That Don't Improve | §32 | Longitudinal score/quality movement and attribution. |
| D-M3 | The Engineer Who Quit — All Her Patterns Left | §32 | Centroid geometry, DiagonalKernel, persistent judgment memory. |
| D-M4 | Quarterly Close: 14 Days, Same 5 Root Causes | §32 | Process graph, recurring root-cause detection, safe automation. |
| D-M5 | Can't Hire Enough Data Engineers | §32 | Conservation-proven automation and realized capacity evidence. |
| D-M6 | Business Users Locked Out of Their Own Data | §32 | DI-3, DI-1, source attribution, confidence, freshness and anomaly context. |
| D-M7 | We Spent $400K on a Data Quality Project — It's Stale | §32 | Persistent learned trust and IKS trajectory. |
| D-I1 | Every Data Asset Knows Its Own Reliability | §33 | DI-1, verified outcomes, per-column DK weights. |
| D-I2 | Metadata Trust — The Catalog That Knows It's Wrong | §33 | DI-1, metadata/source provenance and trust. |
| D-I3 | Combinations Nobody Queried | §33 | DI-5, cross-graph data, statistical testing and later validation. |
| D-I4 | Cross-Pipeline Dependency Nobody Mapped | §33 | Cross-graph execution history, schema events and incident correlation. |
| D-I5 | Auto-Approval That Expands Safely | §33 | Conservation, verified-load evidence, AMBER pause behavior. |
| D-I6 | Per-Consumer Quality Routing | §33 | Learned consumer-specific quality outcomes and routing. |
| D-I7 | What Should I Buy Next? | §33 | DI-5, DI-6, DI-8, verified improvement and economic model. |
| D-I8 | Data Monetization Discovery | §33 | Learned-data value evidence, licensing rights and IKS. |
| D-I9 | Connect My Data — No Engineering Required | §33 | DI-4/source integration, fuzzy join discovery, trust annotations. |
| D-I10 | Quality-Aware Answers for Non-Technical Users | §33 | DI-3, source trust, confidence, provenance, freshness and disagreement context. |
| D-I11 | The Fix That Transferred to 6 Pipelines | §33 | AgentEvolver promotion gate, transfer registry and conservation. |
| D-I12 | One Decision, Three Improvements | §33 | Atomic scorer, graph-enrichment and DK update from one verified decision. |
| D-I13 | Shadow-Tested, Measured, Rejected | §33 | Shadow evaluation, promotion/rejection evidence and governed rollout. |
| D-I14 | The Trust Layer Every Agent Needs | §33 | H6 gateway, customer policy, evidence and abstention. |
| D-I15 | Every Data Product Gets an IQ Score | §33 | Per-product IKS, verified outcomes and product-level maturity. |

### 1.4 Explicit build requirements and named surfaces

| ID / name | PD requirement | Priority / dependency |
|---|---|---|
| SC-TRUST | Source Trust Card with per-source trust, status, verified count, trend, factor drill-down. | §39B, Tier 5.1, 1-2d, before DI-1. |
| SC-IKS-ATTR | Causal attribution for IKS changes with evidence links. | §39B, Tier 5.1, 2-3d. |
| SC-FORECAST | Learning forecast: time to GREEN, bottleneck category and acceleration tip. | §39B, Tier 5.1, 1-2d. |
| SC-DIGEST | Period-based learning digest: verified decisions, factor changes, trust changes, promoted/rejected rules and IKS delta. | §39B, Tier 5.1, 2d; depends on SC-TRUST. |
| DI-1 SOURCE-PROFILER | `SourceProfile`, `ColumnProfile`, `ConsumerProfile`; six source/product/consumer/trust endpoints and trust API. | §39 / §40 L.1, 2w; unblocks Level 5-6 and SC-TRUST. |
| DI-2 INTELLIGENCE-MAP-V1 | D3 force graph; trust-weighted node brightness, correlations, static Day 1→Month 12 animation, learning WebSocket. | §39 / §40 L.4, 2w; depends on DI-1. |
| DI-3 NL-QUERY-ENGINE | Classify → query/execute → enrich with source attribution, reliability, confidence, freshness, anomaly and comparison context. | §39 / §40 L.2, P1; depends on DI-1. |
| DI-4 PROMPT-INTEGRATOR | Natural-language source connection with fuzzy join-key discovery and trust-annotated combined view. | §39; depends on DI-1 and source integration. |
| DI-5 COMBINATION-DISCOVERY | Internal and external combinations, statistical thresholds, residual reduction and ranked candidate output. | §39 / §40 L.3, P2; depends on verified decision data. |
| DI-6 DATA-VALUATION | Economic value per combination. | §39, P2; depends on DI-5 and observed decision value. |
| DI-7 INTELLIGENCE-MAP-V2 | Gold lines, dollar labels, pulsing centroid updates and per-cluster IKS. | §39 / §40 L.4, later; depends on DI-1/5/6. |
| DI-8 ACQUISITION-ADVISOR | Ranked external data catalog and ROI recommendations. | §39, P2; depends on DI-5/6 and catalog. |
| DI-9 SNOWFLAKE-META | Snowflake metadata/query-history connector feeding Source Profiler. | §39, connector phase. |
| DI-10 DBT-CONNECTOR | dbt run history/test results/freshness/errors as graph intelligence. | §39, connector phase. |
| DI-11 AIRFLOW-CONNECTOR | DAG history, duration, failures, schedule and task metrics as graph intelligence. | §39, connector phase. |
| Trust API | `GET /api/dataops/trust/{source_id}` and batch trust profile in §40 L.5. | H6; corrected by final addendum to return HTTP 200 with a decision body. |
| Integration specifications | NL Query Engine, Source Profiler, Combination Discovery, Data Valuation, External Data Catalog, Snowflake/Databricks, dbt and Airflow. | §38 J.2; P1/P2 as listed there. |

## 2. Feature Status Table

Evidence labels use the requested meanings: `LIVE` means the reviewed contract has backend, endpoint, tests and frontend support; `PARTIAL` means real implementation exists but the PD contract or maturity claim is incomplete; `GAP` means no matching product implementation was found. MAP coverage is shown separately so a partial implementation can still be MAP-missing.

Test totals used below: **278** DataOps backend `def test_` definitions and **242** DataOps Playwright `it()`/`test()` definitions across 27 `copilot-sdk/e2e/dataops/*.spec.ts` files. These are repository counts, not the MAP's August 8 snapshot of 261 backend tests.

### 2.1 Named build items

| Item | Status | Implementation evidence | Tests | MAP coverage |
|---|---|---|---|---|
| SC-TRUST | PARTIAL | Trust endpoint and `TrustCard` with perturb/revert are wired (`apps/dataops/backend/app/routers/trust_router.py:22-60`, `frontend/src/components/TrustCard.tsx:15-107`). The PD's dedicated source-trust endpoint, factor-to-source mapping and 50-decision trend are not all present. | 6 focused backend trust tests; 4 trust-card E2E tests. | MAP notes SC-TRUST shipped (`v5.228:1014-1015`); the full PD contract is not separately tracked. |
| SC-IKS-ATTR | GAP | No `iks_attribution.py`, attribution router, or `IKSAttributionPanel` found. | No dedicated tests found. | MAP-MISSING. |
| SC-FORECAST | GAP | No learning-forecast service, endpoint or panel found. | No dedicated tests found. | MAP-MISSING. |
| SC-DIGEST | GAP | No learning-digest service, endpoint or panel found. | No dedicated tests found. | MAP-MISSING. |
| DI-1 Source Profiler | PARTIAL | `BaseSourceProfiler`, `SourceProfile`, DataOps profiler registry and profile routes are wired (`copilot_sdk/di/profiler.py`, `apps/dataops/backend/app/main.py:244-248,758-785`, `copilot_sdk/backend/di_router.py:124-165`). Routes are `/api/dataops/di/...`, not the exact `/api/dataops/sources...` contract, and connector profiles are not demonstrated as per-column DK-derived production trust. | DI backend registration/profile tests in `test_di.py`; 2 profile E2E tests plus shared DI/map coverage. | P30 and P32 CLOSED; MAP says P32 SDK+DataOps, 13 tests. |
| DI-2 Intelligence Map v1 | PARTIAL | `IntelligenceMapBuilder`, `/api/di/intelligence-map`, `/api/dataops/di/intelligence-map`, and `IntelligenceMapPanel` exist (`main.py:750-855`, `copilot_sdk/di/intelligence_map.py:86-116`). WebSocket pulsing is explicitly deferred and the map uses connector-derived rows in one path. | 5 v1 E2E + 5 v2 E2E map tests. | P34 CLOSED; DataOps frontend only. |
| DI-3 NL Query Engine | PARTIAL | `DIQueryService`, deterministic `NLQueryRouter`, governed providers, `/api/dataops/di/query`, and `NLQueryPanel` exist. The PD's general SQL/LLM executor and full source/freshness/anomaly/comparison contract is not proven; current implementation is bounded deterministic query patterns. | 12 focused backend query/enterprise tests; 8 NL-query E2E tests. | P42 CLOSED (`DI-3-NL-QUERY`, 43 SDK tests). |
| DI-4 Prompt Integrator | GAP | SDK `SourceIntegrator` and fuzzy/Levenshtein helpers exist (`copilot_sdk/di/integrator.py:27-90,227-237`), but no DataOps route, handler, or frontend surface calls them. | No dedicated DataOps integration tests found. | MAP-MISSING; no P/R item found for DI-4. |
| DI-5 Combination Discovery | PARTIAL | SDK `CombinationDiscoveryEngine` performs pair testing with p-value/lift thresholds (`copilot_sdk/di/combination_discovery.py:54-171`); map and `/api/dataops/di/combinations` are wired. The PD's external residual-reduction and later holdout/verification contract is absent. | DI/map tests plus shared SDK tests; no separate DataOps holdout gate. | P43 and P44 CLOSED; R27-R30 also CLOSED for adjacent integrator/valuation/map/advisor work. |
| DI-6 Data Valuation | PARTIAL | `DataValuationEngine/Model`, `/api/dataops/di/valuation`, acquisition recommendations and `AcquisitionPanel` exist. Values are derived/demo-modeled and lack the final Value Provenance Ledger. | Acquisition/DI E2E coverage; no final ledger tests. | R28 CLOSED. |
| DI-7 Intelligence Map v2 | PARTIAL | Gold-line data and rendering helpers exist in the builder/map panel; IKS badges are modeled. Learning pulse is deferred and dollars are not FDR/holdout-gated. | 5 v2 map E2E tests. | R29 CLOSED, but final evidence-gate requirements are MAP-MISSING. |
| DI-8 Acquisition Advisor | PARTIAL | `AcquisitionAdvisor`, external catalog, `/api/dataops/di/acquisitions`, `/api/dataops/di/acquisition-advice`, and `AcquisitionPanel` are wired (`main.py:305-321,746-748`; `di_router.py:183-187`). Output includes demo/derived provenance and no observed-value ledger. | 3 acquisition E2E tests. | R30 CLOSED. |
| DI-9 Snowflake metadata | PARTIAL | `SnowflakeMetaConnector` is registered in the DataOps profiler registry and feeds map/profile routes. No evidence of a live Snowflake configuration in the reviewed default path or a full query-history implementation. | Covered by shared DI/profile/map tests; no dedicated connector E2E. | MAP-MISSING as a named DI-9 item. |
| DI-10 dbt connector | PARTIAL | SDK `DBTConnector` is registered and exposed through profile/map machinery. Full dbt run/test-history semantics and live verification were not found. | Covered by shared DI/profile/map tests; no dedicated connector E2E. | MAP-MISSING as a named DI-10 item. |
| DI-11 Airflow connector | PARTIAL | SDK `AirflowConnector` is registered and exposed through profile/map machinery. Full DAG/task-history semantics and learning event feed were not found. | Covered by shared DI/profile/map tests; no dedicated connector E2E. | MAP-MISSING as a named DI-11 item. |
| H1/H3 core loop | PARTIAL | Scoring learn, conservation and variant evolution are mounted (`main.py:641-718`; `scoring_router.py:211-260`). A variant update is conditional on a decision variant ID; no reviewed evidence establishes complete coverage for every verified DataOps decision. | Broad DataOps backend/e2e totals above; no single end-to-end “verify then later trust changes” test identified in the named DataOps suite. | Core/legacy coverage; addendum OD-1 is not a MAP item. |
| H4 self-governing | PARTIAL | Conservation router/provider and perturbation controls are live, but the PD's per-consumer learned quality routing and proven 15%→55% expansion are not. | Conservation, cohort and trust coverage; no expansion proof. | P40C auto-approve is DEFERRED. |
| H5 self-valuating | PARTIAL | Valuation and acquisition surfaces exist, but gold-line claims remain modeled and ungated. | Acquisition/map coverage; no value ledger. | R28-R30 CLOSED; evidence-gate work MAP-MISSING. |
| H6 trust infrastructure | PARTIAL | Trust profiles and source trust routes exist. The corrected `decision/evidence/conservation_status/basis/safe_for_autonomous_use/conditions` contract and thin MCP server do not. | 6 trust backend tests, trust E2E coverage. | Existing DI-1/R30 coverage; gateway contract MAP-MISSING. |

### 2.2 Scenario status

| Scenario group | Status | Evidence-based reason | MAP coverage |
|---|---|---|---|
| D-M1, D-M2, D-M3, D-M4, D-M5, D-M7 | PARTIAL | Alert, decision, centroid, process, conservation and evolution surfaces exist, but the PD's numeric after-state claims (1,500 outcomes, 78→89 quality, 7/12 auto-approval, realized capacity, permanent gains) are not measured by the reviewed code. | MAP has general core items and demo work, but no scenario-specific item for these PD contracts. |
| D-M6 and D-I10 | PARTIAL | Governed deterministic query service returns evidence/confidence-shaped responses and has a frontend panel; it is not the full PD architecture of arbitrary NL → SQL/execute plus all enrichment. | P42 CLOSED; remaining contract MAP-MISSING. |
| D-I1 and D-I2 | PARTIAL | Source profiles, trust weights, connector metadata and per-product responses exist; DK-to-column/source causal lineage and learned metadata trust are incomplete. | P30/P32 CLOSED; remaining contract not separately tracked. |
| D-I3 | PARTIAL | Combination engine and map candidates exist; addendum evidence gates and out-of-sample validation are absent. | P43/P44 CLOSED; evidence gate MAP-MISSING. |
| D-I4 | PARTIAL | `CrossSystemCorrelator` and `CrossSystemPanel` exist, but the complete schema-change → delayed pipeline incident correlation described by the PD is not demonstrated. | P90 is CLOSED for cross-system surface; full scenario proof is not separately tracked. |
| D-I5 and D-I6 | PARTIAL | Conservation and static consumer profiles exist; learned per-consumer standards and safe expansion history are absent. | P40C is DEFERRED; D-I6 MAP-MISSING. |
| D-I7 | PARTIAL | Acquisition advisor and catalog are live as derived/demo surfaces; observed-dollar verification and holdout gate are absent. | R28/R30 CLOSED; ledger/gate MAP-MISSING. |
| D-I8 | GAP | Monetization appears in demo/derived recommendation payloads, but no learned-data monetization discovery with rights/provenance was found. | MAP-MISSING (the old R27-R30 set does not cover D-I8's rights/valuation contract). |
| D-I9 | GAP | `SourceIntegrator` is not wired into DataOps. | MAP-MISSING. |
| D-I11 | PARTIAL | Transfer/evolution services exist, but six-pipeline verified transfer and measured decreasing resolution time are not evidenced. | Cross-copilot Phase 6 queue; no closed scenario item. |
| D-I12 | PARTIAL | Separate scorer, graph enrichment and DK machinery exists, but no atomic verified-decision receipt proves all three channels changed from one click. | MAP-MISSING. |
| D-I13 | PARTIAL | AgentEvolver routes expose shadow/rejected/promoted lifecycle data, but the MAP's promotion engine is deferred and no full reject/promote experiment was verified here. | P83 promotion engine DEFERRED. |
| D-I14 | PARTIAL | Trust endpoints exist, but no abstain/read-only policy gateway or MCP server. | MAP-MISSING. |
| D-I15 | PARTIAL | `/api/di/products`/product cards return IKS-like maturity values; a product-level verified history and honest threshold behavior are not established. | MAP-MISSING as a distinct product-IKS item. |

## 3. Addendum Delta

The addendum says it folds three pending addenda and that nothing is removed. Its one explicit supersession is the trust API: keep HTTP 200 with a decision body and drop the prior 403 (`dataops_copilot_addendum_FINAL_v1.md:1-4,21-29`).

| Addendum item | Net-new or correction | Code result |
|---|---|---|
| OD-1 verified-decision → trust/score build gate | Net-new gate correcting the PD's unconditional “Built? YES” | **Structurally satisfied for scorer learning:** `scorer.learn()` precedes `outcome_recorder`; the scorer reads GraphStore verified counts and fingerprint later. **Not fully closed:** variant ID is optional and no runtime evidence was collected in this review. |
| Proof of Learning drawer / receipts | Net-new product surface | **GAP/PARTIAL.** Audit/provenance panels and perturbation exist, but no single clickable drawer on every trust/IKS/gold-line number with cause, confidence, rejection and automation eligibility. |
| DI-PROOF perturbation + clean revert + provenance | Strengthening of existing trust beat | **PARTIAL.** `PerturbationService`, `/api/di/perturb*`, and `TrustCard` exist. The requested resolution receipt/provenance log is missing. |
| Corrected Agent-Trust Gateway | Correction plus net-new gateway surface | **PARTIAL.** Trust routes exist, but they return factor/profile shapes rather than the required `decision`/`evidence`/`basis`/`conditions` contract; no MCP server found. |
| Acceleration-under-control and time-to-competence | Framing correction plus new metric | **GAP.** No first-vs-sixth-source instrumentation or frozen control. |
| FDR + 30-day holdout + expert verification | Net-new evidence gate | **GAP.** Combination discovery has approximate p-values and warns that it is discovery evidence, not causal proof; no BH/holdout/evaluator gate found. |
| Value Provenance Ledger | Net-new roadmap capability | **GAP.** No ledger linking dollars to observed transactions, counterfactual, range, confidence and verifier. |
| DI-ABSTAIN | New scenario | **GAP.** No gateway decision field or insufficient-evidence abstention route. |
| DI-GATEWAY / DI-MCP | New scenario and interface | **GAP/PARTIAL.** Existing HTTP trust profile is not the corrected gateway and no MCP implementation was found. |
| DI-FIRSTVS6TH | New scenario/metric | **GAP.** No ramp-pair measurement. |
| DI-TWIN | New control | **GAP.** No frozen centroid checkpoint/replay evaluator in DataOps. |
| D-I1-EXT, D-I3-EXT, D-I11-EXT, D-I5-EXT | New extensions | **GAP/PARTIAL.** Existing profiler/discovery/transfer/conservation primitives are present, but the specified extension scenarios and evidence gates are not. |
| Judgment Memory four properties | Naming/positioning requirement | **PARTIAL.** Audit trails, centroid checkpoints and persistence primitives exist; a unified hash-chained evidence ledger plus governed/versioned counterfactual surface was not found. |
| Compliance/pricing/open decisions | Product governance requirements | **Not code features.** The code has provenance and live/fixture distinctions, but these remain documentation and policy gates. |

## 4. Verify-in-Code Results

### 4.1 Compounding loop

**Result: wired at the scorer level; not proven for the whole DataOps product contract.**

- `apps/dataops/backend/app/main.py:641-653` creates `FreshScorerProxy`, `ScorerBackedProvider`, `PromptVariantEvolver`, and `SQLiteVariantStore` in the app factory.
- `apps/dataops/backend/app/main.py:655-666` extracts a decision's variant ID and records the outcome, but returns without updating variant stats when no variant ID is present.
- `copilot_sdk/backend/scoring_router.py:238-260` calls `scorer.learn()` and only then invokes the outcome recorder.
- The trust routes read scorer fingerprint/trajectory/conservation data (`apps/dataops/backend/app/routers/trust_router.py:22-60`), so a later read can observe scorer state.

This is enough to retire the old claim “no production evolver instantiation” for this checkout. It is not enough to claim the PD's stronger “every verified decision measurably improves later trust” statement: the review found no named DataOps test that performs a real learn, then a later score/trust read, and asserts movement. The optional-variant branch is a concrete coverage risk.

### 4.2 Banned vocabulary

Search scope: `copilot-sdk/apps/dataops/backend/app/**/*.py`, excluding tests. Hits:

- `context_router.py:571` checks `metadata.get("reward")`.
- `context_router.py:1521` checks `metadata.get("reward")`.
- `context_router.py:1531` preserves a `"reward"` metadata field.

These are compatibility field names, not an RL implementation. No production hits for `rl_`, `policy_`, or `reinforcement` were found. If the platform rule bans the token `reward` anywhere in production, these three reads should be renamed or isolated; under the narrower requested vocabulary check, they are the only hits and should be flagged rather than hidden.

### 4.3 Honesty/maturity tiers

The final addendum requires `LIVE/NEAR/ARCH × MEASURED/VALIDATED/SIMULATED/MODELED/PILOT-TARGET` (`addendum:59-60`). The demo document itself still labels DI-TRUST and DI-PRODUCT LIVE, DI-GATEWAY NEAR, and DI-GOLD LIVE endpoints/NEAR gold rendering (`demo_scenarios_and_usecases_v2_7.md:67-69,625-633`), while its later addendum section says DI-ABSTAIN, DI-GATEWAY, DI-FIRSTVS6TH and DI-TWIN are NEAR/NEAR-HEAVY (`:832-844`).

Code supports a more conservative tier:

- **LIVE-ish measured computation:** existing trust, source/profile, query, map, acquisition and perturbation endpoints run against real injected services and distinguish fixture/demo provenance in several paths.
- **NEAR:** earned-trust/DI-PROOF, DI-GOLD rendering, H6 gateway, and cross-pipeline transfer. They have surfaces or primitives but not the final evidence contract.
- **ARCH/GAP:** DI-TWIN, DI-FIRSTVS6TH, DI-ABSTAIN, MCP gateway, IKS attribution, forecast and digest.
- **MODELED, not measured:** dollar values from acquisition/valuation and the PD's illustrative trajectories. `copilot_sdk/di/acquisition.py:76-117` explicitly emits `demo` provenance and an assumed annual decision count in the demo path.

### 4.4 Cross-copilot and SDK dependencies

Satisfied or substantially satisfied:

- DataOps imports and mounts SDK GraphStore/scorer/conservation/evolution services (`main.py:52-82,708-832`).
- SDK DI services are constructed with DataOps connector registries (`main.py:244-248,758-785`).
- `ci_platform.copilot_core.EntityCache` and `EntityContextCacheAdapter` are importable from the sibling `ci-platform` checkout (`main.py:82`) and injected into the app.
- Cross-system discovery and transfer routers are mounted, and the frontend has `CrossSystemPanel`/transfer surfaces.

Unsatisfied or incomplete:

- `SourceIntegrator` is not wired to a DataOps endpoint.
- No DataOps learning-event WebSocket is mounted; the map model says pulsing is deferred.
- No shared evidence-gate SDK component for FDR/holdout/value provenance was found.
- No MCP server or portable trust-gateway contract was found.
- Per-product IKS is a response surface, not yet a persisted, outcome-conditioned product judgment history.

### 4.5 Demo scenario coverage

The current demo document defines a seven-beat DataOps arc (§4.9.0): DI-PROOF, self-computation/receipts, DI-ADMITS-FAILURE, DI-ABSTAIN + DI-GATEWAY, DI-FIRSTVS6TH + DI-TWIN, Intelligence Map, and de-risked DI-GOLD (`demo_scenarios_and_usecases_v2_7.md:532-544`).

- DI-PROOF can run as a perturb/revert trust interaction, but the requested receipt is missing.
- Existing trust, source profile, product, NL query, acquisition and map panels can support the older feature-tour beats.
- DI-ADMITS-FAILURE has lifecycle/shadow-rule surfaces, but the MAP says the promotion engine is deferred (P83), so do not present the numeric rejected/promoted story as measured without a fixture receipt.
- DI-ABSTAIN, DI-GATEWAY, DI-FIRSTVS6TH and DI-TWIN cannot run as specified today.
- DI-GOLD has endpoint and panel support, but the current value output must be presented as a modeled/ranked hypothesis, not a verified dollar claim; FDR/holdout evidence is absent.

This agrees with the MAP's own audit note: “Demo-readiness: 4/8 beats PASS today” and a queue containing DI-GOLD-FE, DI-PRODUCT-FE, DI-SOURCE-FE, DI-DIRTY-DATA-FE, DI-CROSS-COPILOT and DEMO-V22-BEATS (`master_action_plan_v5.228 (1).md:1019-1023`).

## 5. MAP Reconciliation

### Closed coverage that does map to the PD

| MAP item | Status in MAP | PD coverage |
|---|---|---|
| P30 DI-1 Source Profiler P1 | CLOSED/DONE | DI-1 foundation. |
| P32 DI-1 Source Profiler P2 | CLOSED/DONE | SDK + DataOps profiler endpoints. |
| P34 DI-2 Intelligence Map | CLOSED/DONE | DataOps frontend map v1. |
| P42 DI-3 NL Query | CLOSED/DONE | DI-3 deterministic query foundation. |
| P43 DI-5 Combination Discovery | CLOSED/DONE | DI-5 discovery engine. |
| P44 DI-5 Graph Enrichment | CLOSED/DONE | Adjacent graph enrichment substrate. |
| R27 DI Prompt Integrator | CLOSED/PASS | The MAP calls this a shipped first DataOps DI, but the current DataOps code scan found only the SDK `SourceIntegrator` and no product route. Recheck the claimed implementation boundary. |
| R28 DI Data Valuation | CLOSED/PASS | DI-6. |
| R29 DI Intelligence Map v2 | CLOSED/PASS | DI-7 gold-line/IKS extension. |
| R30 DI Acquisition Advisor | CLOSED/PASS | DI-8. |
| P40C | DEFERRED | D-I5's automatic expansion safety is not fully delivered. |
| P83 | DEFERRED | D-I13 promotion/rejection engine remains a risk. |

The MAP explicitly records P30/P32/P34 as done (`master_action_plan_v5.228 (1).md:79-85`), P42-P44 as done (`:158-164`), and R27-R30 as closed (`:275-278`). Its DataOps audit snapshot reports 261 backend tests (`:1036-1042`), whereas this checkout currently contains 278 definitions.

### MAP-missing additions required

No distinct MAP item was found for SC-IKS-ATTR, SC-FORECAST, SC-DIGEST, DI-ABSTAIN, DI-FIRSTVS6TH, DI-TWIN, the corrected DI-GATEWAY/MCP contract, the Proof-of-Learning drawer, the Value Provenance Ledger, or the FDR/holdout/evidence gate. DI-4 also needs a new item unless R27's claimed closure is extended with a DataOps route and UI proof.

## 6. Recommended MAP Additions

| Proposed item | Scope / done definition | Priority | Dependencies | Effort |
|---|---|---:|---|---:|
| DOPS-OD1 | Real learn → later score/trust regression using a real GraphStore; assert variant-ID coverage and outcome stats for verified decisions. | P0 / demo gate | Existing scorer/evolver; test fixtures. | 1-2d |
| DOPS-SC-ATTR | IKS attribution service, endpoint, Insight panel, evidence links and bounded unattributed delta. | P1 | Checkpoint history, evolution ledger, schema-impact data. | 2-3d |
| DOPS-SC-FORECAST | Learning forecast service/endpoint/panel with honest unknown/empty state. | P1 | Trajectory, conservation, verified timestamps. | 1-2d |
| DOPS-SC-DIGEST | Daily/weekly/monthly digest service/endpoint/panel with factor/source/rule/IKS deltas. | P1 | SC-TRUST, fingerprint history, evolution events. | 2d |
| DOPS-PROOF | One receipt drawer on trust/IKS/gold values; perturb/revert provenance, named causes, uncertainty and rejection evidence. | P0 / demo | Existing perturbation, audit trail, checkpoints. | 3-5d |
| DOPS-GATEWAY | Correct 200 trust decision contract, policy evaluation, insufficient-evidence abstain/read-only behavior, batch endpoint and thin MCP adapter. | P0 / pilot | DI-1, conservation policy, portable schema/security review. | 4-7d |
| DOPS-TWIN | Persist frozen centroid checkpoints and replay current decisions against frozen state with a comparison report. | P1 | Checkpoint persistence and replay/idempotency. | 2-3w |
| DOPS-FIRST6 | Instrument first-vs-sixth new-source/schema time-to-competence with same-schema controls. | P1 | DOPS-TWIN, source onboarding timestamps, GREEN definition. | 1-2w |
| DOPS-EVIDENCE-GATE | Shared BH/FDR, 30-day holdout and expert-verification gate; expose N tested/M survived. | P0 for gold / pilot | DI-5, outcome history, gate SDK. | 1-2w |
| DOPS-VALUE-LEDGER | Link each dollar to observed transactions, counterfactual baseline, range, confidence and verifier; honest empty state. | P1 | DOPS-EVIDENCE-GATE, DI-6/8. | 1-2w |
| DOPS-DI4 | Wire `SourceIntegrator` to a DataOps API/UI with fuzzy join suggestions and quality annotations. | P1 | DI-1 profiles, connector payloads. | 3-5d |
| DOPS-DI9-11 | Validate live Snowflake/dbt/Airflow connector contracts and provenance; add connector-specific routes/tests. | P2 | Connector credentials/fixtures, DI-1. | 1-2w |
| DOPS-CROSS | Atomic three-channel receipt and verified cross-pipeline transfer evidence. | P2 | Graph enrichment, transfer registry, DOPS-OD1. | 1-2w |

## 7. Priority Queue

### Demo-blocking

1. **DOPS-OD1:** close the verified outcome → later trust/score proof and address missing variant IDs.
2. **DOPS-PROOF:** make perturbation produce a receipt, not only a changed number.
3. **DOPS-GATEWAY:** implement the corrected trust/abstain/read-only contract before staging agent claims.
4. **DOPS-EVIDENCE-GATE + DOPS-VALUE-LEDGER:** keep gold lines as ranked hypotheses and remove unsupported dollar certainty.
5. **DOPS-TWIN / DOPS-FIRST6:** required for the addendum's falsifiable compounding story.

### Pilot-blocking

1. SC-IKS-ATTR, SC-FORECAST and SC-DIGEST for explainable operating use.
2. DI-4 route/UI wiring and connector-specific DI-9/10/11 validation.
3. Persistent per-product and per-consumer quality evidence rather than static/demo-derived values.
4. Security, policy and tenant isolation review for the external trust gateway/MCP surface.

### v1.1

1. Atomic three-channel improvement receipt (D-I12).
2. Verified cross-pipeline transfer and measured improvement on recurrence (D-I11).
3. DI-13 governed promotion/rejection closure after P83's deferral is resolved.
4. Real connector onboarding and time-to-competence instrumentation.

### Roadmap

1. D-I8 monetization discovery with explicit rights and licensing evidence.
2. Cross-customer priors, subject to opt-in data rights and privacy review.
3. Full WebSocket learning pulse and richer Intelligence Map v2 animation.
4. General SQL/LLM query execution beyond the deterministic governed query patterns.

## Bottom line

The old MAP was accurate for the implementation slice it audited, but it was not a complete audit of PD v1.9. The current checkout has a credible DI foundation and real endpoint/UI/test coverage. It does not yet support the final PD as a fully LIVE product: the addendum's evidence, abstention, frozen-control, ledger and maturity claims require new implementation and explicit MAP tracking.
