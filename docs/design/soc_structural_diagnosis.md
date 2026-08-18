# SOC Copilot — Structural Diagnosis

Date: 2026-08-17  
Scope: read-only structural discovery across the SOC application, shared SDK, GAE, and ci-platform repositories. The only file created by this discovery is this report.

## Repo layout

| Repository | Absolute path | Remote | Branch | Latest tag observed |
|---|---|---|---|---|
| SOC application | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50` | `git@github.com:ArindamBanerji/gen-ai-roi-demo.git` | `v5.0-dev` | `v5.122` in the local tag history |
| Shared SDK | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk` | `git@github.com:ArindamBanerji/copilot-sdk.git` | `main` | `v0.9.25` is present in the local tag set |
| Graph Attention Engine | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\graph-attention-engine` | `git@github.com:ArindamBanerji/graph-attention-engine.git` | `main` | local tag set inspected |
| CI platform | `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform` | `git@github.com:ArindamBanerji/ci-platform.git` | `main` | local tag set inspected |

All four repositories are separate checkouts. GAE and ci-platform are not merely vendored copies inside the SOC repository. The SOC repository guidance explicitly identifies `ci-platform/ci_platform/graph/age_client.py` as the AGE choke point consumed by the SOC backend.

Relevant top-level layout:

```text
gen-ai-roi-demo-v4-v50/
  backend/app/                 primary SOC FastAPI application
  backend/tests/               SOC backend tests
  backend/scripts/             AGE census, seed, graph and migration utilities
  backend/docs/                implementation/design diagnostics
  frontend/src/                SOC product frontend
  frontend/tests/e2e/          SOC Playwright suite

copilot-sdk/
  copilot_sdk/scoring/         shared scoring and compounding
  copilot_sdk/graph/           shared GraphStore/AGE abstractions
  copilot_sdk/situation/       shared SituationAnalyzer
  copilot_sdk/conservation/    shared conservation protocols/services
  copilot_sdk/evolution/       shared AgentEvolver/evolution primitives
  copilot_sdk/substantiation/  claims/evidence registry
  docs/design/product/         product and merged design artifacts

graph-attention-engine/
  gae/                          standalone attention/scoring primitives
  tests/                        GAE unit and contract tests

ci-platform/
  ci_platform/                  AGE, connectors, onboarding, PII/SAML services
  tests/                        platform tests
```

## SOC PD document audit (critical)

### All SOC documents found

The following are the important SOC-named artifacts in the product/design and SOC backend documentation trees:

| Path | Size | First-line/version evidence | Type |
|---|---:|---|---|
| `copilot-sdk/docs/design/product/soc_copilot_design_v5_11.md` | 382,919 bytes | `# SOC Copilot — Design Document v5.11`; version 5.11, dated Aug 16 2026 | **Merged engineering + product authority** |
| `copilot-sdk/docs/design/soc_copilot_design_v5_11.md` | 382,919 bytes | Same v5.11 document outside `product/` | Duplicate of merged authority; resolve duplicate ownership |
| `gen-ai-roi-demo-v4-v50/backend/docs/design/soc_copilot_design_v5_8.md` | 344,379 bytes | `# SOC Copilot — Design Document v5.8`; dated Apr 29 2026 | Older engineering design, superseded |
| `copilot-sdk/docs/design/ci_reviews_and_addenda/final_addenda/soc_copilot_addendum_FINAL_v1.md` | 11,974 bytes | FINAL consolidated addendum; base document says v5.9 | Addendum/merge instructions |
| `copilot-sdk/docs/design/ci_reviews_and_addenda/soc_copilot_doc_additions_v1.md` | 14,709 bytes | Additions to the SOC product spine and companion engineering document | Earlier addendum |
| `copilot-sdk/docs/design/ci_reviews_and_addenda/soc_review_consolidation_v1.md` | 21,907 bytes | SOC review consolidation | Review/design input |
| `copilot-sdk/docs/design/soc_factor0_reconciliation_pass_v1.md` | 12,108 bytes | Factor-0 naming reconciliation pass | Narrow change design |
| `gen-ai-roi-demo-v4-v50/backend/docs/design/soc_domain_scoping_v1_2.md` | 11,110 bytes | Shared-graph domain-scoping implementation contract | Runtime/graph contract |
| `gen-ai-roi-demo-v4-v50/backend/docs/soc_test_architecture_v1.md` | 30,492 bytes | Test architecture diagnostic | Test diagnostic, not PD |
| `gen-ai-roi-demo-v4-v50/backend/docs/implementation_plans/soc_seed_redesign.md` | 35,232 bytes | SOC seed redesign | Implementation plan |
| `gen-ai-roi-demo-v4-v50/docs/soc_copilot_design_v5_5_part1.md` | 207,680 bytes | Older v5.5 design part | Archived/older engineering |
| `gen-ai-roi-demo-v4-v50/docs/soc_copilot_design_v5_5_part2.md` | 62,853 bytes | Older v5.5 design part 2 | Archived/older engineering |
| `gen-ai-roi-demo-v4-v50/docs/soc_copilot_design_v5_5_part3.md` | 18,298 bytes | Older v5.5 design part 3 | Archived/older engineering |

The search did **not** find a standalone `soc_copilot_product_definition_v1.md`, `v1_1`, or `v1_2` in the checked-in product/design directories. The product-definition content has been folded into v5.11’s later sections.

### Authoritative PD identification

Use:

```text
copilot-sdk/docs/design/product/soc_copilot_design_v5_11.md
```

It is the correct gap-analysis authority because:

- The header states v5.11 and says it absorbs and supersedes prior SOC design versions.
- It contains the engineering design in Part I-style sections and product-facing sections later in the file.
- Section 30 is a feature-gap table with F1–F22.
- The v5.5 product requirements are enumerated as R1–R13.
- Referral routing is separately enumerated as R1–R7 under the referral architecture.
- Later appended material includes the judgment-memory, moat, governance, and monitoring additions from the merged review/addenda.

The standalone v1.2 product-definition filename assumed by the prompt is absent. The old v5.8 engineering file is not the right authority by itself because it predates the v5.11 merge and later addendum material.

### Wrong-file check

The known mislabel is present:

```text
copilot-sdk/docs/design/product/trading_copilot_product_definition_v1_1.md
```

Its first line is:

```text
# SOC Copilot — Design Document v5.8
```

Therefore it is SOC content under a Trading filename and must not be used for Trading or SOC gap analysis without correction/explicit archival labelling. The correctly named product-directory file is `trading_copilot_product_definition_v1_1_corrected.md`, whose first line is `# Trading Copilot — Product Definition`.

No checked-in SOC-named product file was found that is actually another copilot. The duplicate v5.11 location is a duplicate, not a cross-copilot mislabel.

### Feature manifest and numbering scheme

The authoritative v5.11 document has multiple numbering layers:

1. **Product/roadmap feature gaps F1–F22**, in §30. These are the main feature manifest for the SOC gap analysis.
2. **v5.5 shipping requirements R1–R13**, in §10.6 and the product flow. These are implementation requirements, not the same namespace as F1–F22.
3. **Referral rules R1–R7**, in §22.6 and the referral policy implementation. These are routing rules and intentionally separate from the v5.5 R1–R13 requirement numbering.
4. **Later feature surfaces F16–F22**, including Learning Control Room, Earned Autonomy Ladder, Frozen Twin, No-Precedent, Counterfactual Inspector, Day-0 Readiness, and Cold-Start/Transfer Measurement.

The key §30 feature list is:

| ID | Feature | Target/status context in v5.11 |
|---|---|---|
| F1 | Shadow Mode | v5.5/R8; fully specified |
| F2 | Detection Engineering Feedback | v5.0 primitive/complete claim |
| F3 | EU AI Act Compliance Evidence | v5.5/v6.0; partially shipped |
| F4 | Operational Outcome Metrics | v5.0 primitive/complete claim |
| F5 | Multi-SIEM Abstraction | v6.0 |
| F6 | Attack Chain Correlation | v6.0 |
| F7 | NHI Behavioral Baseline | v6.5 |
| F8 | Cross-Tenant Meta-Intelligence | v7.0 |
| F9 | Analyst Benchmarking Report | v5.6; documented as done |
| F10 | A2A/MCP Protocol | v7.0+ |
| F12 | INTSUM-Quality Threat Briefing | v5.5 proposal |
| F13 | ContextConnectors (email/Slack/docs) | v6.0 proposal/gated |
| F14 | Ask the Graph | v5.5; specified/partially surfaced |
| F15 | SynthesisNode Artifact | v6.0 proposal/gated |
| F16 | Learning Control Room | v5.9 |
| F17 | Earned Autonomy Ladder | v5.9 |
| F18 | Frozen Twin | v5.9 |
| F19 | No-Precedent Surface | v5.9 |
| F20 | Counterfactual “What Would Flip This” Inspector | v5.9 |
| F21 | Day-0 Readiness Assessment | v5.9 |
| F22 | Cold-Start / Transfer Measurement | v5.9 |

The numbering skips F11 in the §30 table. That is a document-level numbering anomaly and must be preserved as a finding until the authority owner resolves it; it should not be silently renumbered in a future gap analysis.

## SOC code map

### In `gen-ai-roi-demo-v4-v50` (primary)

The backend contains the primary SOC app and currently has 236 Python test files with 1,896 `def test_` definitions in the local source scan. The repository’s own v5.11 header reports an older 900-backend/183-E2E snapshot; the current source count should be treated as the latest local inventory, not as a claim that the full suite was executed during this discovery.

Key files:

| Area | Path | Finding |
|---|---|---|
| App and mounts | `gen-ai-roi-demo-v4-v50/backend/app/main.py` | Mounts evaluation, judgment, evolution, triage, SOC analytics, framework, metrics, graph, audit, governance, GAE, simulation, discoveries, shadow, cohort, and related routers. No live S2P backend is mounted. |
| Domain config | `backend/app/domains/soc/config.py` | `SOCDomainConfig`, 6×4×6 SOC centroid tensor, factor names and penalty/configuration values. |
| Factor computers | `backend/app/domains/soc/factors.py` | Six-factor SOC computation, including canonical `privileged_identity_context`; factor-0 is weighted/renormalized in the current implementation. |
| Scorer adapter | `backend/app/domains/soc/scorer_adapter.py` | Bridges SOC configuration/state to the shared scorer. |
| Triage | `backend/app/routers/triage.py`, `backend/app/services/triage.py` | Alert scoring, decision path, feedback, conservation health and evidence fields. |
| SOC analytics | `backend/app/routers/soc.py` | Profile/diagnostics/IKS/centroid and SOC analytics endpoints. |
| Referral | `backend/app/services/referral_policy.py`, `referral_rules.py` | Post-score fifth-action routing (`refer_to_analyst`) through deterministic rules, not an additional centroid action. |
| Situation | `backend/app/services/situation.py`, `backend/app/domains/soc/situations.py`, `soc_situation_pattern.py` | SOC situation/context and alert routing support. |
| Evolution | `backend/app/services/evolver.py`, `variant_generator.py`, `variant_registry.py`, `backend/app/routers/evolution.py` | SOC variant/evolution and promotion-related paths. |
| IKS | `backend/app/services/iks.py`, `backend/app/framework/iks_base.py` | IKS trajectory/score support. |
| NL evidence | `backend/app/services/nl_templates.py` | Category/action-oriented natural-language evidence and explanations. |
| Threat intelligence | `backend/app/services/threat_intel.py`, `threat_indicator.py`, `backend/app/connectors/pulsedive.py`, `greynoise.py`, `sentinel_real.py` | Threat-intel computation and connector/provider surfaces. |
| Discovery | `backend/app/services/cross_graph_discovery.py`, `backend/app/routers/discoveries_router.py` | Cross-system discovery/correlation, advisory in posture. |
| Seed/census | `backend/scripts/`, especially `soc_domain_census.py`, `preseed_all_copilots.py` | AGE/domain census, preseed and migration utilities. |
| Frontend | `gen-ai-roi-demo-v4-v50/frontend/src/` | SOC product UI plus S2P Preview proxy surface. |

`gen-ai-roi-demo-v4-v50/backend/app/domains/supply_chain/config.py` is a legacy/duplicate supply-chain configuration and is not the live SOC scoring path.

### Frontend tabs and product surface

The assumption of five tabs is stale. `frontend/src/App.tsx` currently registers seven tab IDs/components:

- `SOCAnalyticsTab.tsx` — SOC Analytics
- `RuntimeEvolutionTab.tsx` — Runtime Evolution
- `AlertTriageTab.tsx` — Alert Triage
- `CompoundingTab.tsx` — Compounding
- `ExecutiveNarrativeTab.tsx` — Executive Narrative
- `S2PPreviewTab.tsx` — S2P Preview
- `GovernanceTab.tsx` — Governance

The SOC-specific E2E tree contains 64 TypeScript files and 444 `test`/`it` call sites in the local scan. The S2P-named tests in that tree are Preview/proxy tests, not evidence that SOC owns the live S2P backend.

### In `copilot-sdk` (shared)

| Area | Path | Finding |
|---|---|---|
| Shared scoring | `copilot-sdk/copilot_sdk/scoring/scorer.py`, `scoring/config.py` | `ProfileScorer`, `CompoundingScorer`, scoring state and learning. |
| SOC preset | `copilot-sdk/copilot_sdk/scoring/presets/soc.py` | `SOC_BOOTSTRAP_CENTROIDS`; shape 6×4×6 and SOC factor names. |
| Shared graph | `copilot-sdk/copilot_sdk/graph/` | GraphStore protocols/factory, SQLite/AGE implementations and graph persistence abstractions. |
| Shared situation | `copilot-sdk/copilot_sdk/situation/analyzer.py` | Domain-agnostic SituationAnalyzer. SOC-specific integration remains in SOC code. |
| Conservation | `copilot-sdk/copilot_sdk/backend/conservation_router.py`, `conservation_utils.py`, `copilot_sdk/conservation/` | Shared conservation status/metrics/contracts. |
| Evolution | `copilot-sdk/copilot_sdk/evolution/evolver.py`, `evolution_router.py` | Shared AgentEvolver primitives. |
| Substantiation | `copilot-sdk/copilot_sdk/substantiation/` | ClaimRegistry, readiness, evidence/substantiation tier support. |
| Discovery | `copilot-sdk/copilot_sdk/discovery/cross_system.py`, `discovery_router.py` | Shared CrossSystemCorrelator/discovery primitives. |

The SDK’s own CLAUDE.md says it is domain-agnostic and must not import SOC application internals. SOC uses these shared interfaces; it does not make the SDK a SOC-specific repository.

### In `graph-attention-engine`

GAE is a separate Apache-2.0, pip-installable library under `graph-attention-engine/gae`. It provides the mathematical attention/scoring primitives and has 10 test files with 177 `def test_` definitions in the local scan. The SOC application consumes the scoring framework through the shared/application integration rather than containing a second GAE implementation.

GAE is not the home of `SOCDomainConfig`, referral policy, NL templates, or SOC routers. It has no SOC-specific factor names or travel/identity naming references in its source scan.

### In `ci-platform`

ci-platform is a separate Apache-2.0 infrastructure repository under `ci-platform/ci_platform` with 46 test files and 476 `def test_` definitions in the local scan.

Relevant services:

- `ci_platform/graph/age_client.py` — AGEClient single choke point for Cypher execution.
- onboarding/deployment qualification — data readiness, entity resolution, PII and qualification services.
- connectors and SAML/identity-related infrastructure.
- evidence ledger and centroid convergence helpers.

The SOC backend architecture imports/uses the AGEClient boundary through its database switcher. ci-platform does not contain SOC factors or referral policy. Its CLAUDE.md warns that changing AGEClient affects 290+ SOC call sites.

## Dependency diagram

```text
SOC alert score request
  → gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py
  → backend/app/services/triage.py
  → backend/app/domains/soc/factors.py
       six factor computers / provenance-bearing factor results
  → backend/app/domains/soc/config.py::SOCDomainConfig
  → backend/app/domains/soc/scorer_adapter.py
  → shared scorer interfaces
       copilot-sdk/copilot_sdk/scoring/scorer.py
       ProfileScorer / CompoundingScorer / DiagonalKernel
  → shared GraphStore and AGE boundary
       copilot_sdk/graph → ci-platform/ci_platform/graph/age_client.py
       PostgreSQL + AGE graph, normally soc_graph
  → conservation/evolution gate
       shared conservation services + app/services/evolver.py
  → referral_policy.py / referral_rules.py
       fifth action refer_to_analyst, layered after 4-action geometry
  → situation and evidence
       services/situation.py, domains/soc/situations.py,
       services/nl_templates.py, provenance/evidence services
  → response
       SOC frontend port 5173
```

The S2P Preview route is a separate proxy surface in the SOC frontend; it delegates `/api/s2p/preview/*` to the live S2P backend on port 8002 when the SOC backend has no matching route. It is not part of the SOC score dependency chain.

## SOC-specific component table

| Component | Expected | Found in repo | File path | Status |
|---|---|---|---|---|
| SOCDomainConfig | 6×4×6 tensor, SOC penalty/config | gen-ai-roi-demo-v4-v50 | `backend/app/domains/soc/config.py` | LIVE; executable tensor/config exists |
| Six factor computers | canonical six factor names | gen-ai-roi-demo-v4-v50 | `backend/app/domains/soc/factors.py` | LIVE; factor-0 canonical rename is still in reconciliation |
| referral_policy.py | fifth action `refer_to_analyst` | gen-ai-roi-demo-v4-v50 | `backend/app/services/referral_policy.py`, `referral_rules.py` | LIVE; layered post-score VETO/routing, not a centroid action |
| SituationAnalyzer SOC wiring | situation context for alerts | SDK + SOC repo | `copilot_sdk/situation/analyzer.py`, `backend/app/services/situation.py`, `domains/soc/situations.py` | PARTIAL/NEAR; shared analyzer exists and SOC paths exist, but deployment/data-backed routing evidence must be verified per route |
| AgentEvolver SOC | shadow → promote → rollback | gen-ai-roi-demo-v4-v50 + SDK | `backend/app/services/evolver.py`, `routers/evolution.py`, SDK `evolution/evolver.py` | PARTIAL; evolution/promotion primitives exist, complete per-class earned-autonomy state machine is not established |
| conservation_contract | GREEN/AMBER/RED gates | SDK + SOC | `copilot_sdk/backend/conservation_router.py`, `backend/app/routers/evolution.py`, `framework_router.py` | LIVE for evolution/monitoring; decision-path coupling is separate and incomplete |
| self_computation_router | counterfactual replay, centroid history | copilot-sdk + SOC mounts | `copilot_sdk/backend/self_computation_router.py`, shared router mounts in SOC | LIVE shared infrastructure; SOC endpoint integration should be tested as a product contract |
| discovery/cross_system.py | advisory CrossSystemCorrelator | copilot-sdk + SOC | `copilot_sdk/discovery/cross_system.py`, `backend/app/services/cross_graph_discovery.py`, `discoveries_router.py` | LIVE/ADVISORY; does not grant autonomous authority |
| IKSService SOC wiring | IKS trajectory | gen-ai-roi-demo-v4-v50 | `backend/app/services/iks.py`, `framework/iks_base.py`, SOC routers | LIVE |
| UI tabs | Dashboard/Triage/Analysis/Performance/Settings assumption | gen-ai-roi-demo-v4-v50 | `frontend/src/App.tsx`, `components/tabs/` | LIVE surface, but actual current count is 7 tabs: Analytics, Evolution, Triage, Compounding, Executive, S2P Preview, Governance |
| shadow mode | shadow scoring/evaluation | gen-ai-roi-demo-v4-v50 | `backend/app/routers/shadow.py`, `services/evolver.py`, config | LIVE/partially integrated; shadow is the intended cold-start safety boundary |
| NL evidence templates | category evidence generation | gen-ai-roi-demo-v4-v50 | `backend/app/services/nl_templates.py` | LIVE |
| threat-intel connectors | Pulsedive, GreyNoise, ISAC-like providers | gen-ai-roi-demo-v4-v50 | `backend/app/connectors/pulsedive.py`, `greynoise.py`, `threat_intel_provider.py`, `sentinel_real.py` | LIVE/connector-dependent; external availability is deployment-specific |
| S2P Preview proxy | `/api/s2p/preview` → port 8002 | SOC frontend | `frontend/src/components/tabs/S2PPreviewTab.tsx`, frontend proxy config | LIVE as Preview/proxy; not SOC backend ownership |
| Three-Signal Monitoring | Circuit Breaker, Flywheel Health, Analyst Contribution | gen-ai-roi-demo-v4-v50 | SOC monitoring/analytics services and v5.11 design | PARTIAL; monitoring primitives and narrative exist, Analyst Contribution is data-gated/production-milestone rather than fully active for all analysts |

## Test inventory

Counts are source counts and collection-oriented inventories; this session did not execute the full suites.

| Repo | Backend tests | E2E tests | Stress/contract evidence | Total inventory |
|---|---:|---:|---|---:|
| gen-ai-roi-demo-v4-v50 | 236 files / 1,896 `def test_` definitions | 64 files / 444 `test`/`it` call sites | contract/diagnostic files and stress-oriented tests are included in backend tree; exact stress subset is not separately labelled | 2,340 call sites/definitions plus files |
| copilot-sdk SOC/shared surface | shared SDK tests, SOC preset/framework tests | SOC-specific E2E is not in SDK; shared copilot E2E lives under `e2e/` | shared protocol, scorer, conservation, graph, provenance contracts | not isolated without a marker-specific collection |
| graph-attention-engine | 10 files / 177 `def test_` definitions | — | mathematical/library tests | 177 |
| ci-platform | 46 files / 476 `def test_` definitions | — | AGE/interface parity, onboarding and connector contracts | 476 |

The v5.11 header reports an older snapshot of 900 SOC backend and 183 E2E tests. That document claim is not the current source inventory; the 1,896/444 counts above are the local scan results.

## Known issue status

### Factor-0 naming: `travel_match` versus `privileged_identity_context`

Scoped source counts (excluding caches/generated/vendor directories):

| Scope | `travel_match` | `privileged_identity_context` | Finding |
|---|---:|---:|---|
| SOC backend/app | 84 | 33 | Mixed migration state; legacy scenario/provenance/alias/NL references remain while config/factor code is canonical |
| SDK shared SOC-relevant code | 1 | 5 | Shared provenance/preset residuals; no SOC application import is permitted by SDK guidance |
| ci-platform | 3 | 2 | Dual mapping in evidence-ledger/deployment-qualification compatibility paths |
| GAE | 0 | 0 | No SOC factor naming in GAE library |

Within the SOC backend, the legacy name is concentrated in `app/data/soc_eval_scenarios.json`, `app/domains/soc/factors.py`, `framework/provenance.py`, `routers/evaluation.py`, and `routers/judgment.py`. The canonical name appears in `config.py`, factor code, orchestrator/context paths, alert-pool data, and provenance/route compatibility code.

Interpretation:

- **Config/preset:** canonical `privileged_identity_context` is the live factor name and the tensor remains 6×4×6.
- **Eval fixtures:** legacy `travel_match` remains intentionally quarantined/legacy-labelled in the scenario corpus.
- **Router inputs:** aliases accept the old name for compatibility and canonicalize output.
- **NL/provenance:** dual mapping remains and needs a bounded deprecation/migration policy; it must not silently launder legacy semantics into current identity semantics.

The panel re-authoring work is therefore not equivalent to complete runtime migration. The live factor computer is canonical, but fixture/provenance/compatibility references remain by design.

### Conservation coupling (C-COUPLE)

Conservation is live in the evolution/monitoring path: shared conservation services and SOC evolution/framework routers expose health, status, headroom, and gate state. The SOC triage path also reads conservation health and carries conservation fields through analysis/decision responses; `triage.py` has an effective-conservation helper and updates the SOC conservation provider from health.

However, this is not the same as proving that every scoring decision is directly vetoed by conservation before action routing. The current evidence supports:

- **Evolution/promotion coupling:** LIVE.
- **Triage observability and gate inputs:** PRESENT.
- **Universal decision-path veto coupling:** NOT PROVEN / NEAR.

The gap analysis should test a real alert through triage under GREEN, AMBER, and RED and verify the action/referral behavior, rather than infer C-COUPLE from conservation fields in responses.

### `reward` / `reward_raw`

The SOC-specific production source scan did not identify a dominant SOC `reward`/`reward_raw` contract comparable to S2P. Reward fields do exist in the shared SDK and in cross-domain/framework paths, but the SOC application’s canonical factor/triage route is outcome/conservation oriented.

This remains a compatibility concern: count and classify shared occurrences before any protocol cleanup. Do not remove shared reward fields based solely on the SOC scan; S2P and common evolution/scorer paths consume them.

### Acceleration and second derivative

No live SOC production implementation of `second_derivative`, `dA_dt`, or `meta_learn` was found. `acceleration` appears in a transparency/instrumentation context, and `reconvergence_logger.py` is present and referenced by SOC routers/services. These are observability/experiment instrumentation, not a demonstrated second-derivative production learning loop.

Conclusion: **instrumentation/measurement exists; a live acceleration/meta-learning control loop does not.** Any claim about second-derivative compounding must remain experimental or observational until a production update path and acceptance test are identified.

### Frozen twin / frozen scorer

No `FrozenTwin`, `frozen_twin`, `frozen_scorer`, or `frozen_baseline` implementation was found in the SOC application, shared SDK, GAE, or ci-platform source scopes. Checkpoint and centroid-state infrastructure exists, but it is not a permanent immutable parallel scorer with same-alert comparison.

The v5.11 design/blog values such as frozen-scorer percentages and CLAIM-62 therefore describe design/experiment evidence, not a live Frozen Twin product capability. This is a high-priority gap because it is the credibility mechanism for separating synthetic/experimental claims from measured customer improvement.

## SOC PD authority conclusion

Before a SOC feature gap analysis begins, use:

```text
copilot-sdk/docs/design/product/soc_copilot_design_v5_11.md
```

Use its §30 F1–F22 table as the feature-gap manifest, its v5.5 R1–R13 table as the shipped-requirement checklist, and its separate referral R1–R7 table only for post-score routing. Treat `soc_copilot_addendum_FINAL_v1.md` as merge rationale/acceptance input, not as a replacement for the merged v5.11 authority. Treat the old v5.8 backend design and the mislabelled Trading filename as superseded or incorrectly named artifacts.

## Directory context block (for the gap-analysis prompt)

```text
SOC backend:          C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend
SOC frontend:         C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend
SOC E2E tests:        C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend\tests\e2e
SOC domain config:    C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\domains\soc\config.py
SOC factor computers: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\domains\soc\factors.py
SOC referral policy:  C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\services\referral_policy.py
SOC referral rules:   C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\services\referral_rules.py
SOC evolver:          C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\services\evolver.py
SOC self-computation: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk\backend\self_computation_router.py
SOC discovery:        C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\services\cross_graph_discovery.py
SOC NL templates:     C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\app\services\nl_templates.py
Shared SDK:           C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk
SOC preset:           C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk\scoring\presets\soc.py
Shared graph:         C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk\graph
Shared scoring:      C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\copilot_sdk\scoring
GAE library:          C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\graph-attention-engine
ci-platform:          C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform
SOC PD (authority):   C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\product\soc_copilot_design_v5_11.md (v5.11 merged)
SOC old engineering:  C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend\docs\design\soc_copilot_design_v5_8.md
SOC addenda:          C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\ci_reviews_and_addenda\final_addenda\soc_copilot_addendum_FINAL_v1.md
MAP:                  C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\master_action_plan_v5.228 (1).md
SOC wrong-file warning:C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\product\trading_copilot_product_definition_v1_1.md (actually SOC v5.8)
```

## Discovery boundary

This report did not run the complete SOC, SDK, GAE, ci-platform, or Playwright suites and did not connect to a live AGE DSN. Counts are source inventories. Runtime claims about deployed graph state, connector availability, and live endpoint behavior require a separate environment verification ladder.
