# Frontend wiring and monkeypatch/mock audit — SOC, Trading, Purchasing, DataOps and S2P

Model: gpt-6-astra — reasoning: high.

This document preserves the original SOC audit, the Trading/Purchasing continuation, and the completed DataOps/S2P continuation. Application code remains unchanged. All five copilots now have route/consumer inventories; broader SOC/SDK/CI mock-review limits are stated in the relevant sections.

**Latest continuation:** [DataOps and S2P findings, route inventories, and mock review](#continuation--dataops-and-s2p-2026-09-06), dated 2026-09-06. The SOC and Trading/Purchasing sections below are earlier source audits; their scope and counts are historical rather than a new verification.

## Combined report coverage and navigation

**All five copilots' findings are in this file.** The 2026-09-06 document-integrity check counted the actual inventory rows below: **944 route registrations across five applications**, representing 933 copilot-qualified unique method/path pairs. The document contains findings, evidence, route/consumer inventories, mock-review results and remediation recommendations; it is not only a summary.

| Copilot | Ranked frontend findings | Registered-route rows verified in this document | Findings | Route/consumer inventory | Mock review |
|---|---:|---:|---|---|---|
| SOC | 9 | 251 | [SOC findings](#soc-findings) | [SOC routes and representative consumers](#complete-soc-route-inventory) | [SOC/SDK focused review](#part-b--current-monkeypatch-and-mock-inventory) |
| Trading | 5 | 162 | [Trading findings](#trading-findings) | [Trading route diff](#trading--complete-registered-route--frontend-diff) | [Trading/Purchasing review](#part-b--trading-and-purchasing-patchmock-findings) |
| Purchasing | 9 | 162 | [Purchasing findings](#purchasing-findings) | [Purchasing route diff](#purchasing--complete-registered-route--frontend-diff) | [Trading/Purchasing review](#part-b--trading-and-purchasing-patchmock-findings) |
| DataOps | 7 | 145 | [DataOps findings](#dataops-findings) | [DataOps route diff](#dataops--every-registered-route-and-no-consumer-diff) | [DataOps/S2P review](#part-b--monkeypatch-mock-and-production-compatibility-inventory) |
| S2P | 9 | 224 | [S2P findings](#s2p-findings) | [S2P route diff](#s2p--every-registered-route-and-no-consumer-diff) | [DataOps/S2P review](#part-b--monkeypatch-mock-and-production-compatibility-inventory) |

**Completeness limit:** all five route/consumer audits and their reported findings are present, but this is not an exhaustive classification of every mock in SOC/SDK/CI. That broader semantic review remains incomplete. The SOC inventory gives representative frontend consumers per route, rather than a separate exhaustive call-site list. Trading, Purchasing, DataOps and S2P include explicit frontend call-site and patch-operation indexes. Routes with unproven product ownership are labelled accordingly instead of being declared UI bugs.

The sections preserve successive audit runs. Historical statements about work not yet performed are qualified below and superseded by the [consolidated completion state](#consolidated-completion-state).

---

**Original SOC run: route mapping and a focused SOC/SDK mock review.** That discovery run used no git commands and executed no applications or tests. This in-repo document was subsequently created and extended at the user's request. Findings establish source-level wiring; they do not establish runtime endpoint health.

The SOC inventory contains **251 route registrations representing 250 unique method/path pairs**. I found **no SOC frontend consumer for 139 unique endpoints**. That count includes legitimate operator APIs and unused parallel adapters—it is **not 139 confirmed UI bugs**.

Paths below are relative to the workspace containing `copilot-sdk`, `gen-ai-roi-demo-v4-v50`, `s2p-copilot`, and `ci-platform`:

- `R/` = `gen-ai-roi-demo-v4-v50/backend/app/routers/`
- `F/` = `gen-ai-roi-demo-v4-v50/frontend/src/`
- `T/` = `gen-ai-roi-demo-v4-v50/backend/tests/`
- `K/` = `copilot-sdk/copilot_sdk/backend/`

<a id="soc-findings"></a>

## Part A — ranked SOC findings

| Rank | Endpoint and backend evidence | Classification / severity | Frontend evidence and impact | Recommended fix approach |
|---|---|---|---|---|
| 1 | `GET /api/diagnostics/day-zero` — `R/soc_demo_beats.py:151`; `GET /api/graph/connectors` — `R/graph.py:239` | **NAME_MISMATCH, P1** | `F/components/DayZeroReadinessPanel.tsx:12` calls enrichment summary, graph summary, learning health and scorer profile instead. At lines 18–23 it expects readiness/connector fields absent from those response contracts. Enrichment returns indicators and severity counts (`R/graph.py:403`); graph summary returns node/relationship counts (`R/framework_router.py:678`). Successful requests can therefore produce “Unavailable” readiness fields. | Define one typed readiness contract, connect the panel to the dedicated readiness and connector data, and render only fields that contract supplies. |
| 2 | `GET /saml/login` — `K/auth_router.py:24`; mounted in SOC `backend/app/main.py:187` | **NAME_MISMATCH—proxy routing, P1 when authentication is enabled** | `F/lib/api.ts:23` redirects a 401 to `/saml/login` on the **frontend origin**. SOC `frontend/vite.config.ts:25` proxies `/api/s2p`, `/s2p-health` and `/api`, but not `/saml`. The backend route exists; this navigation does not reach it through the configured development proxy. | Route the SAML flow through the same origin as authenticated API calls, including login and callback handling. |
| 3 | `POST /api/soc/authority/{category}/advance` — `R/authority.py:38` | **MISSING_UI, P1** | `F/components/AutonomyLadderPanel.tsx:19` only fetches authority records. Its rendering at lines 34–45 presents earned promotion state without an advancement control. The only production call to `AuthorityManager.advance()` found is this endpoint (`R/authority.py:42`); no automatic advancement caller was found in SOC application code. | Add a governed advancement workflow that shows eligibility and evidence, or explicitly make advancement an operator-only operation and explain that in the panel. |
| 4 | `POST /api/soc/shadow/analyst-action` — `R/framework_router.py:460` | **MISSING_UI, P1** | `F/lib/api.ts:593` defines `recordShadowAction`, but nothing calls it. The UI **does** toggle shadow mode and fetch its report (`F/components/tabs/RuntimeEvolutionTab.tsx:971`). The report filters for decisions with analyst actions and aggregates `agreement` (`backend/app/framework/shadow_mode.py:75`); this endpoint writes those fields at lines 52–57. No alternative caller of that recording service was found. | Complete the shadow-decision/analyst-feedback/report lifecycle, verifying that scored decisions receive the shadow marker and analyst agreement fields. |
| 5 | `GET /api/soc/shadow/eligibility/{shadow_decision_id}` — `R/shadow.py:21`; `POST /api/soc/shadow/preview` — line 26; `POST /api/soc/shadow/promote` — line 31 | **MISSING_UI, P1** | No callers for these paths or their approval-token workflow exist in SOC frontend source. The current shadow controls use the separate toggle/report API at `F/lib/api.ts:590`. Consequently, the explicit preview-and-approve promotion workflow cannot be completed through this frontend. | Add eligibility → preview → explicit approval controls using the existing promotion token contract. |
| 6 | `POST /api/demo/reset` — `R/metrics.py:447` | **DEAD_CODE, P1 misleading contract** | `F/lib/api.ts:319` exports `resetDemoData`, with no caller. The handler performs no reset yet returns `"status": "success"` and claims events were cleared (`R/metrics.py:462`). The active frontend reset wrapper uses `/api/demo/reset-all` at `F/lib/api.ts:323`. | Retire the false-success endpoint and unused wrapper, or delegate to the real reset operation with its existing authorization semantics. |
| 7 | `GET /api/evolution/summary` — `R/evolution.py:733` and `K/evolution_router.py:141` | **DEAD_CODE—shadowed registration, P2** | SOC registers its router first (`backend/app/main.py:155`), then the SDK router at line 156. The installed Starlette router returns after the first full match (`site-packages/starlette/routing.py:729`). Thus the SDK summary handler is unreachable at this address in SOC. The two handlers return different contracts; neither has a native SOC frontend caller. | Assign one canonical summary contract and remove or rename the conflicting registration; test the assembled application’s route. |
| 8 | `GET /api/soc/benchmarking-level2` — `R/soc.py:1756` | **DEAD_CODE, P2** | No frontend caller. The handler explicitly constructs synthetic A/B results, including significance and promotion claims (`R/soc.py:1764`). Its own comment identifies it as an unused backlog stub at line 1760. | Remove the registered synthetic-results endpoint or confine it to an explicitly identified fixture/example surface. |
| 9 | `GET /api/soc/transparency` — `R/soc.py:1585` | **MISSING_UI, P2** | `F/lib/api.ts:551` defines `fetchTransparency`, but no component calls it. The backend provides analyst/CISO/auditor explanations and limitations, while no frontend consumer presents this response. | Add the transparency/limitations view or formally retire this presentation contract. |

The key files are [DayZeroReadinessPanel.tsx](../../../gen-ai-roi-demo-v4-v50/frontend/src/components/DayZeroReadinessPanel.tsx), [SOC API client](../../../gen-ai-roi-demo-v4-v50/frontend/src/lib/api.ts), [Vite configuration](../../../gen-ai-roi-demo-v4-v50/frontend/vite.config.ts), and [SOC router registration](../../../gen-ai-roi-demo-v4-v50/backend/app/main.py). Exact audit line references appear above.

### Reverse checks and excluded false positives

- **No active SOC frontend method/path call was confirmed to target an absent SOC route.** The SAML problem above is an origin/proxy mismatch.
- There is a **latent request-contract bug** in unused `runGraphQuery`: `F/lib/api.ts:637` sends `{cypher}`, but `R/framework_router.py:79` requires `{query_name}`. Using this wrapper would fail validation. The active graph explorer uses `/soc/graph/prebuilt/{query_name}` instead (`F/lib/api.ts:634`). Severity **P2**; remove or update the unused wrapper.
- `/api/soc/model-swap-trial` **is wired**: `F/lib/api.ts:502` → `F/components/tabs/RuntimeEvolutionTab.tsx:888`. A literal-only scan misses its nested URL template.
- `/api/governance/report` **is wired indirectly**: `F/lib/api.ts:556` → `downloadGovernanceReportJson` at line 564 → `F/components/tabs/ExecutiveNarrativeTab.tsx:486`.
- `/api/soc/learning/frozen-comparison` has no direct frontend caller, but **Frozen Twin has a UI**. The control-room response incorporates the comparison (`R/soc_learning.py:30`), consumed at `F/components/LearningControlRoom.tsx:35`. Calling this a missing Frozen Twin panel would be wrong.
- The 13 `soc_demo_beats` routes and 19 SDK self-computation routes have no direct SOC frontend consumers. Some duplicate information already shown through SOC-specific endpoints. **Their absence from frontend calls alone does not justify classifying every route as MISSING_UI or DEAD_CODE.**
- Health checks, SAML metadata/callbacks, ingestion and operational controls can legitimately have no frontend consumer. Those require API-owner disposition rather than automatic deletion.

### SOC → S2P cross-references

These calls resolve to the separate S2P backend, not SOC. They must not appear in SOC’s missing-route count.

| S2P endpoint, all GET | SOC frontend caller | S2P backend declaration |
|---|---|---|
| `/api/s2p/preview/queue` | `F/components/tabs/S2PPreviewTab.tsx:556` | `s2p-copilot/backend/app/routers/s2p_preview.py:508` |
| `/api/s2p/preview/conservation` | Same file:557 | Same backend file:514 |
| `/api/s2p/preview/suppliers` | Same file:558 | Same backend file:570 |
| `/api/s2p/suppliers/{supplier_id}/profile` | Same file:566 | `s2p_suppliers.py:363` |
| `/api/s2p/compliance/report` | `F/components/CompliancePanel.tsx:62` | `compliance_router.py:65` |
| `/api/s2p/simulation/scenarios` | `F/components/DisruptionSimPanel.tsx:44` | `s2p_simulation.py:203` |
| `/api/s2p/simulation/impact-summary` | Same frontend file:45 | Same backend file:263 |
| `/api/s2p/financial-impact` | `F/components/FinancialImpactPanel.tsx:57` | `financial_router.py:375` |
| `/api/s2p/novelty/status` | `F/components/NoveltyPanel.tsx:47` | `s2p_novelty.py:47` |
| `/api/s2p/insight/process-signals` | `F/components/ProcessFusionPanel.tsx:32` | `s2p_insight.py:278` |
| `/api/s2p/insight/cross-graph` | Same frontend file:33 | Same backend file:219 |
| `/api/s2p/suppliers/payment-strategy` | `F/components/WorkingCapitalPanel.tsx:55` | `s2p_payment.py:255` |
| `/api/s2p/suppliers/payment-portfolio` | Same frontend file:56 | Same backend file:278 |
| `/api/s2p/suppliers/trends` | `F/components/TrendCorrelationPanel.tsx:42` | `s2p_early_warning.py:224` |
| `/api/s2p/suppliers/early-warnings` | Same frontend file:43 | Same backend file:210 |

These are valid cross-copilot preview consumers. I have **not** labelled them exclusively `PREVIEW_ONLY`: the native S2P API client also references the preview queue, conservation and suppliers routes (`copilot-sdk/apps/s2p/frontend/src/api.ts:133`, `:150`, `:166`).

### Complete SOC route inventory

This combines the backend enumeration and frontend diff. Framework-generated documentation routes are excluded.

Notation:

- Every path below starts with **`/api`**, except the explicitly marked main and SAML routes.
- `G` = GET; `P` = POST.
- `@number` is the backend declaration line in the named file.
- `→` identifies a frontend consumer; **`—` means no SOC frontend consumer found**.
- Frontend `api:number` means `F/lib/api.ts:number`.
- Component names refer to `F/components/`; tab names refer to `F/components/tabs/`.
- A listed consumer is representative where several components call the same endpoint. Unused wrappers do not count as consumers.

```text
backend/app/main.py — paths shown in full
G /                         @96   —
G /health                   @104  —
G /api/health               @105  —

R/evaluation.py
G /soc/evaluation/run       @91   —
G /soc/evaluation/summary   @148  —

R/judgment.py
P /soc/judgment/explain             @101 —
G /soc/judgment/explain/{alert_id}  @150 → api:205

R/evolution.py
G /deployments                     @56  → api:92
P /alert/process                   @105 → api:96
P /alert/process-blocked           @434 → api:106
P /eval/simulate-failure            @583 → api:115
G /evolution/recent                @675 —
G /evolution/variant-history       @717 —
G /evolution/summary               @733 —
G /soc/evolution/rejection-summary @742 → PromotionRejectionTable.tsx:42
G /evolution/recent-events         @782 → GovernanceTab.tsx:528
G /evolution/weight-history        @796 —
G /evolution/trust-scores          @846 —
G /soc/graph-stats                 @893 → RuntimeEvolutionTab.tsx:819

K/evolution_router.py
G /evolution/variants       @79  —
G /evolution/history        @108 —
G /evolution/promoted       @124 —
G /evolution/summary        @141 — duplicate; shadowed in SOC
P /evolution/record-outcome @169 —
P /evolution/check-promotion @192 —

R/triage.py
G /alerts/queue                    @391  → api:165
P /alert/analyze                   @447  → api:171
P /action/execute                  @1480 → api:178
P /alerts/reset                    @1655 → api:186
P /alert/outcome                   @1711 → api:415
G /alert/outcome/status            @2775 → api:411
G /alert/policy-check              @2872 → api:430
G /alert/policy-history            @2919 —
G /soc/profile                    @2950 → api:148
G /rl/reward-summary               @3069 → api:143
G /triage/decision-factors/{alert_id} @3097 → api:192

R/framework_router.py
G /soc/centroid-evolution              @107  → api:153
G /soc/convergence-calendar            @179  —
G /soc/ols-status                      @255  —
G /soc/flywheel-comparison             @328  —
G /soc/iks-trend                       @409  → api:490
P /soc/shadow/toggle                   @452  → api:591
P /soc/shadow/analyst-action            @460  —
G /soc/shadow/report                   @472  → api:600
P /soc/checkpoint/create               @483  → api:607
G /soc/checkpoint/list                 @507  → api:610
P /soc/checkpoint/rollback             @515  → api:613
P /soc/scorer/freeze                   @541  —
P /soc/scorer/unfreeze                 @556  —
G /soc/auto-approve-stats              @575  → api:310
P /soc/graph/query                     @633  —
G /soc/graph/top-nodes                 @651  —
G /soc/graph/node/{node_id}/neighbors   @668  → api:629
G /soc/graph/summary                   @678  → api:623
G /soc/graph/prebuilt-queries          @694  → api:632
P /soc/graph/prebuilt/{query_name}      @705  → api:635
G /soc/learning-health                @723  → api:482
G /soc/learning-balance-sheet          @767  → api:313
G /soc/factor-analysis                @857  → api:494
G /soc/factor-analysis/summary         @867  → api:498
G /soc/factor-contribution             @903  → FactorContributionPanel.tsx:89
P /soc/interventions/freeze            @948  —
P /soc/interventions/unfreeze          @958  —
P /soc/interventions/rollback          @968  —
P /soc/interventions/threshold         @983  —
G /soc/interventions/state             @995  —
G /soc/interventions/history           @1005 → api:139
G /soc/frozen-roi                      @1020 —
G /triage/learning-state               @1036 → LearningStatePanel.tsx:31
G /compounding/channel-decomposition   @1125 → ThreeChannelPanel.tsx:54

R/soc_learning.py
G /soc/learning/control-room             @22 → api:119
G /soc/learning/frozen-comparison         @42 —
P /soc/learning/frozen-comparison/freeze  @60 → api:127
G /soc/learning/convergence               @85 —

R/authority.py
G /soc/authority                          @25 → api:131
G /soc/authority/{category}               @30 —
P /soc/authority/{category}/advance       @38 —
P /soc/authority/{category}/circuit-break @47 → api:135

R/soc_demo_beats.py
G /learning/control-room          @67  —
G /learning/autonomy-ladder        @87  —
G /learning/frozen-twin            @107 —
G /context/no-precedent            @121 —
G /context/what-if/{alert_id}      @145 —
G /diagnostics/day-zero            @151 —
G /diagnostics/frontier            @174 —
G /diagnostics/centroid-timeline   @197 —
G /diagnostics/accuracy-alerts     @204 —
G /evolution/rule-genealogy        @211 —
G /diagnostics/decision-explorer   @218 —
G /evolution/rule-lifecycle        @223 —
G /diagnostics/audit-trail         @230 —

R/explain.py
G /soc/explain/no-precedent @33 → api:196
G /soc/explain/what-if      @42 → api:201

R/soc.py
G /diagnostics                     @41   —
P /soc/query                       @541  → api:73
G /soc/detection-engineering        @644  → SOCAnalyticsTab.tsx:219
G /soc/metrics                     @731  —
G /soc/threat-landscape            @754  → api:80
G /soc/attack-tactic-breakdown      @884  → api:84
G /soc/analytics                   @918  —
G /soc/learning-state              @1016 → ContinuityPanel.tsx:18
G /soc/explain/{decision_id}       @1105 —
G /soc/provenance/{decision_id}    @1347 —
G /soc/threat-intel/{alert_id}     @1394 —
G /soc/onboarding-calendar         @1431 —
G /soc/attack-chains               @1467 —
G /soc/compliance                  @1507 → GovernanceTab.tsx:513
G /soc/transparency                @1585 —
G /soc/benchmarking-report         @1602 —
G /soc/executive-narrative          @1645 → ExecutiveNarrativeTab.tsx:428
G /soc/executive-narrative/pdf      @1652 → ExecutiveNarrativeTab.tsx:514
G /soc/model-swap-trial             @1730 → api:502
G /soc/three-claims                 @1745 —
G /soc/benchmarking-level2          @1756 —
G /soc/campaigns                   @1939 → CampaignIntelligencePanel.tsx:22
G /soc/campaign-timeline            @1985 → CampaignTimelinePanel.tsx:76
G /soc/campaigns/{campaign_id}     @2050 → AlertTriageTab.tsx:777
G /soc/accuracy-trajectory          @2070 → api:474
P /soc/campaigns/recorrelate        @2117 —
G /soc/analyst-benchmarking         @2151 → api:579
G /soc/f9-report                   @2347 → api:583
G /soc/enrichment-advisor           @2381 —
G /soc/enrichment-status           @2414 → RuntimeEvolutionTab.tsx:911
G /soc/reconvergence-log            @2584 —
G /soc/verification-health         @2612 —
P /soc/backup-centroid             @2630 —
P /soc/restore-centroid            @2651 —
G /soc/centroid-backups            @2677 —
G /soc/gate-config                 @2695 —
G /soc/tab/{n}/content             @3669 —
G /soc/industry-profiles           @3698 —
G /soc/industry-profile            @3716 —
G /soc/deployment-state            @3740 —
G /soc/analyst-eta-weights          @3762 —
G /soc/analyst-weights             @3841 —
G /soc/volume-baseline             @3937 —
G /soc/frozen-categories           @3960 —
G /soc/spike-cap-status            @3997 —
G /soc/centroid-export             @4034 → api:157
G /soc/centroid-heatmap             @4137 → RuntimeEvolutionTab.tsx:861
G /soc/centroid-support            @4232 → ContinuityPanel.tsx:19
G /soc/distance-log                @4364 —
G /sentinel/alerts                 @4414 —
P /sentinel/writeback-test         @4464 → GovernanceTab.tsx:633
G /soc/epistemic-state             @4501 —

R/metrics.py
G /metrics/compounding          @181 → api:244
G /metrics/compounding/headline @319 → CompoundingTab.tsx:706
P /demo/seed                    @337 —
P /demo/reset-all               @358 → api:325
P /demo/reseed                  @421 → api:332
P /demo/reset                   @447 —
G /metrics/evolution-events     @485 → api:316
G /metrics/weekly-trends        @540 —
G /metrics/decision-economics    @586 → CompoundingTab.tsx:897
G /demo/domains                 @672 —
G /soc/operational-metrics      @706 → CompoundingTab.tsx:911
G /soc/board-export             @810 → CompoundingTab.tsx:925
G /soc/economics                @868 → CompoundingTab.tsx:945
G /metrics/confidence-trajectory @968 —

R/roi.py
G /roi/defaults  @198 → ROICalculator.tsx:85
P /roi/calculate @231 → ROICalculator.tsx:92; api:400

R/graph.py
P /graph/threat-intel/refresh              @171 → api:446
G /graph/connectors                       @239 —
P /graph/connectors/refresh-all            @269 —
G /graph/enrichment/aggregate/{indicator}  @302 —
G /graph/enrichment/summary                @350 → api:454
G /graph/enrichment/by-alert/{alert_id}    @411 → api:458

R/audit.py
G /audit/decisions @36  → api:466; CompoundingTab.tsx:2366
G /audit/verify    @108 → api:470
G /audit/epochs    @149 —

R/governance_router.py
G /governance/report        @15 → api:556, indirectly through api:564
G /governance/report/csv    @20 → api:571
G /governance/summary       @38 → api:560
G /soc/evidence-room        @59 → CompoundingTab.tsx:814; GovernanceTab.tsx:471
G /soc/evidence-room/export @64 → CompoundingTab.tsx:845; GovernanceTab.tsx:605

R/gae.py
G /gae/weights               @49  —
G /gae/history               @78  —
G /gae/convergence           @135 → api:365
G /gae/confidence-trajectory @186 → api:369
G /gae/trust-curve           @227 → api:373
G /gae/before-after          @288 → api:377
G /gae/weight-evolution      @344 —

R/admin.py
P /admin/reset            @82  —
P /admin/ingest           @377 —
P /admin/evolution-scan   @419 —
P /admin/shadow-start     @437 —
P /admin/promote-evaluate @479 —
G /admin/sentinel-health  @516 —

R/simulation.py
P /simulation/start                          @208 → api:221
G /simulation/progress/{simulation_id}        @257 → api:228
G /simulation/result/{simulation_id}          @291 → api:232
G /simulation/experiment-log/{simulation_id}  @320 → api:236

R/whatif_router.py
P /whatif/project               @54 → api:509
G /whatif/presets               @63 → api:516
G /whatif/presets/{preset_name} @72 —

R/eval_router.py
P /eval/upload                         @29  → api:288
G /eval/templates                      @110 → api:306
G /eval/templates/{template_format}.csv @125 → CompoundingTab.tsx:1558

R/time_machine_router.py
G /time-machine/snapshots               @23 → api:524
G /time-machine/snapshots/{snapshot_id} @31 → api:528
G /time-machine/compare                 @43 → api:532
G /time-machine/compare-bootstrap       @55 → api:536
G /time-machine/timeline                @67 → api:540

R/discoveries_router.py
G /discoveries         @69  → discovery/DiscoveryBanner.tsx:48,195
P /discoveries/refresh @94  —
G /discoveries/summary @116 —

R/platform.py
G /platform/cross-signals        @231 —
G /platform/domain-applicability @250 → DomainApplicabilityPanel.tsx:40
G /platform/warm-start-evidence  @267 —
G /platform/chain-credit-demo    @278 —
G /platform/rl-reward-demo       @289 → GovernanceTab.tsx:548
G /platform/rl-exploration-demo  @299 → GovernanceTab.tsx:561

R/shadow.py
G /soc/shadow/eligibility/{shadow_decision_id} @21 —
P /soc/shadow/preview                          @26 —
P /soc/shadow/promote                          @31 —

R/cohort_status_router.py
G /campaign/cohort-status @17 → api:281

R/rl_router.py
G /rl/reward-ledger/summary      @36  —
G /rl/reward-ledger/entries      @48  —
G /rl/posteriors/summary         @60  —
G /rl/chain-credit/{decision_id} @127 —
G /rl/status                    @165 —

R/servicenow_router.py
P /servicenow/create-incident          @55 → GovernanceTab.tsx:632
G /servicenow/incidents                @69 —
G /servicenow/incident/{decision_id}   @74 —
P /servicenow/update-status            @82 —

R/enterprise.py
G /enterprise-health           @31 —
G /enterprise/process-timeline @37 → ProcessTimelinePanel.tsx:15

K/auth_router.py — paths shown in full
G /saml/metadata @19 —
G /saml/login    @24 → api:23; proxy gap described above
P /saml/acs      @31 —
G /saml/logout   @52 —
G /saml/status   @58 —

K/self_computation_router.py
G /self/centroid-history                              @107 —
G /self/centroid-timeline                             @154 —
P /self/regime-reinit                                 @163 —
G /self/evolution/summary                             @181 —
G /self/diagnostics                                   @189 —
G /self/centroid-history/{checkpoint_id}/counterfactual @221 —
G /self/centroid-history/{checkpoint_id}/lineage       @337 —
G /self/centroid-history/{checkpoint_id}/replay        @348 —
P /self/replay-score                                  @368 —
G /self/decisions/{decision_id}/checkpoints            @413 —
G /self/accuracy-by-category                          @422 —
G /self/accuracy-alerts                               @457 —
G /self/trust-traps                                   @465 —
P /self/rollback                                     @471 —
G /self/decisions                                    @481 —
G /self/rule-genealogy                               @508 —
G /self/rule-lifecycle/{rule_id}                     @514 —
G /self/audit-trail                                  @525 —
G /self/decision-flow                                @556 —
```

The remaining `—` entries are the complete **discovery inventory**, not individually confirmed defects. Their external consumers, intended ownership and adapter-retirement decisions remain unclassified where the evidence did not support one of the four requested labels.

## Part B — current monkeypatch and mock inventory

The following counts are complete static counts for the listed test directories. **Semantic classification of every patch is not complete.** “Mention lines” includes fixture parameters and comments, matching the earlier report’s line-based measure; it is not a count of mocked behaviors.

| Test directory | Lines containing `monkeypatch` | Files containing it | Explicit `monkeypatch.*` / `mp.*` calls |
|---|---:|---:|---:|
| `copilot-sdk/tests` | **502** | **40** | 287 |
| SOC `backend/tests` | **1,272** | **59** | 758 |
| Trading `backend/tests` | 368 | 24 | 177 |
| Purchasing `backend/tests` | 79 | 8 | 26 |
| DataOps `backend/tests` | 102 | 7 | 54 |
| `s2p-copilot/backend/tests` | 338 | 34 | 168 |
| `ci-platform/tests` | 88 | 7 | 52 |

These call counts exclude `unittest.mock.patch` calls, which were inspected separately for the findings below.

### B1. BLOCKING — factor computation has a production test-only branch. P1.

Production hook: [triage.py](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py):68, with behavior at **lines 540–552**.

The alias is not merely patchable. Production detects whether it has been replaced and takes a different execution path, synthesizing provenance with `"source": "test_override"`. Patched integration tests bypass the real factor/provenance orchestration.

All direct patch users found:

- `T/test_ae_integration.py:75`
- `T/test_d06_unmapped.py:76`
- `T/test_rl_triage_integration.py:407`
- `T/test_sentinel_integration.py:144`

Additional test files use the shared patched harness:

- `T/test_rl_full_pipeline.py:14`, `:33`
- `T/test_rl_feature_flags.py:52`, `:54`

**Injection replacement:** inject a `FactorVectorProvider` returning both vector and provenance; exercise the real orchestrator against injected external data sources in integration tests.

**Non-test removal impact:** no production consumer of the compatibility override was found outside its own branch. Preserve normal orchestration when removing the alias and branch. The prior report’s `test_cold_start_guards.py` reference is misleading here: its line 74 patches the separate **evolution** module’s ordinary factor-function binding.

### B2. BLOCKING — learning configuration reconciles test-mutated globals. P1.

Production hook: [triage.py](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py):338.

`_soc_learning_enabled()` compares the imported route constant with the configuration module’s constant. A discrepancy makes the route constant take precedence over `is_learning_enabled()`. The docstring explicitly identifies legacy monkeypatch support.

Direct route-global patch users:

- `T/test_dual_update_fix.py:130`
- `T/test_factor_validation.py:60`
- `T/test_rl_full_pipeline.py:26`
- `T/test_rl_triage_integration.py:359`, `:607`, `:740`, `:781`, `:821`
- `T/test_soc_c9b_l5_proof.py:187`
- `T/test_soc_dk_l5.py:364`
- `T/test_soc_learning_live.py:30`

`T/test_rl_feature_flags.py:34` also asserts the literal source spelling of this compatibility gate, making its implementation part of the test contract.

**Injection replacement:** inject one `LearningPolicy.enabled()` implementation that resolves configuration consistently.

**Non-test removal impact:** the outcome handler calls this gate at `R/triage.py:2107`, so it must be replaced rather than simply deleted. No production mutation of the route-level flag was found.

### B3. BLOCKING — persistence has a checkpoint-path-dependent test escape hatch. P2.

Production hook: [gae_state.py](../../../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py):606.

When no learning store exists, changing `_STATE_PATH` away from its default permits JSON persistence instead of raising the normal initialization error. Its comment explicitly says this branch exists for unit tests.

All current `_STATE_PATH` patching test files found:

- `T/test_gae_persistence.py:132`
- `T/test_l5_learning_store_init.py:73`
- `T/test_p77_migration.py:305`
- `T/test_scorer_adapter.py:201`

However, **none of those inspected uses proves it needs this save fallback**: the persistence test patches the path for loading an old checkpoint; the other three replace `save_learning_state()` itself. Current persistence round-trip tests use `InMemoryGraphStore`.

**Injection replacement:** make checkpoint serialization and learning-store persistence explicit dependencies; test legacy file loading independently.

**Non-test removal impact:** normal initialized AGE persistence uses lines 614–615 and is separate from this branch. No production reassignment of `_STATE_PATH` was found; preserve the legacy reader if still supported.

### B4–B6. CIRCULAR — assertions bypass the behavior their test names claim to cover.

| Test | Evidence | Severity | Replacement |
|---|---|---|---|
| `T/test_factor_validation.py:94`, `test_valid_factor_vector_scores_correctly` | `process_outcome` is replaced with `_OutcomeResult()` at line 57; that object supplies `"consequence": "stable"` at line 26. The test asserts `"stable"` at line 100. The live profile scorer is explicitly removed at line 65. This does not verify correct scoring. | **P1** | Keep input-validation tests separate; verify scoring with a real scorer and inspect the persisted decision/outcome. |
| `T/test_gae_persistence.py:140`, `test_chart_endpoints_return_data_after_reload` | After a real persistence round trip, the test locally reproduces trust-curve and before/after calculations instead of calling either endpoint. Those API handlers can break while these chart assertions remain green. | **P1** | Feed the restored store into the real chart handlers and assert their responses. |
| `T/test_cold_start_guards.py:165`, `test_simulation_start_graceful_with_none_scorer` | The test patches `_run_simulation_bg` itself, then checks that the start endpoint returns a running job. The simulated execution containing the missing-scorer behavior never runs. | **P2** | Retain a start-endpoint contract test, and separately execute the real simulation service with an explicitly absent scorer. |

The persistence test still provides useful serialization coverage; the circular portion is its claimed **chart endpoint** coverage.

### B7. STALE — two patches create a removed persistence symbol.

Test sites: [test_fix_05_06_07.py](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_fix_05_06_07.py):86 and **line 142**.

Both use:

```python
patch.object(sim_mod, "save_learning_state", create=True)
```

`backend/app/services/simulation.py` has no such imported or defined callable. Its remaining occurrences are documentation/comments. At test line 106, `assert_not_called()` therefore checks an invented attribute that the implementation never resolves.

- **Category:** STALE
- **Severity:** P1 for the isolation assertion at line 106; P2 for the unused second patch.
- **Replacement:** compare real production state before and after simulation and verify writes through the actual injected persistence boundary.

This is **two stale patch sites targeting one removed symbol**.

### ACCEPTABLE examples and corrections to the previous report

- Environment isolation such as `T/test_saml_auth_extended.py:233` and `copilot-sdk/tests/test_graph_config.py:31` is normal hermetic testing. `delenv(..., raising=False)` is **not** evidence of a stale patch.
- Wrapping `CompoundingScorer.from_preset()` to select a test profile while calling the original constructor—e.g. `T/test_soc_learning_live.py:14`—is **not automatically circular scoring**. It still constructs the real scorer, although explicit constructor configuration would avoid patching.
- **The five telemetry tests are no longer live-port tests.** `copilot-sdk/tests/test_evolution_telemetry.py:101` now constructs in-process applications and uses `TestClient` at line 134. The earlier finding should be retired. Its SOC branch builds a small SDK-router application rather than testing SOC’s assembled `main.py`, so it does not cover the duplicate route registration above.
- **The four Protocol-V2 placeholders are implemented.** `copilot-sdk/tests/graph/test_protocol_v2_service_layer.py:63`, `:84`, `:105`, `:125` exercise real SQLite/outbox behavior, including replay. They are no longer empty skipped tests.
- The global-state comments in `gae_state.py:94` and `state/graph_snapshot.py:163` explicitly mention test patchability. I did not count ordinary singleton accessors as additional BLOCKING hooks without identifying a separate test-specific behavior branch.

## Part C — scoped summary

| Measure | Confirmed in this run |
|---|---:|
| SOC unique registered method/path pairs | **250** |
| SOC endpoints with no native frontend consumer found | **139** |
| Unwired endpoints covered by the ranked actionable findings | **11** |
| Additional active authentication routing defect | **1** |
| BLOCKING production test hooks | **3** |
| CIRCULAR tests identified | **3** |
| STALE patch sites | **2**, targeting one removed symbol |
| Other copilots’ complete wiring audits | **Not performed in the original SOC run; all four continuations are now included below** |
| Full per-usage mock classification | **Not complete** |

### Top five by likelihood of hiding a bug or confusing a demo

1. **Factor/provenance compatibility branch:** integration tests exercise different production behavior from unpatched requests.
2. **Day-zero response-contract mismatch:** successful backend calls still produce unavailable readiness information.
3. **Learning-policy compatibility gate:** test-mutated globals create configuration behavior outside the normal policy path.
4. **Incomplete authority/shadow workflows:** visible promotion and shadow reporting surfaces lack the associated progression/feedback controls.
5. **SAML frontend-origin routing gap:** authentication-enabled development demos redirect to a path Vite does not forward.

### Recommended Codex prompt sequence

| Order | Group together | Scope and required proof |
|---|---|---|
| 1 | SOC factor provider and learning policy injection | Replace the two triage compatibility hooks together; migrate their shared test harnesses and verify real factor provenance plus enabled/disabled outcome behavior. |
| 2 | Day-zero frontend contract | Limit changes to the readiness adapter, connector response mapping, typed client and panel; verify populated and unavailable states against actual response contracts. |
| 3 | Authority and shadow workflows | Treat authority advancement, shadow decision marking, analyst feedback and explicit promotion as one lifecycle audit before adding controls. |
| 4 | Authentication routing | Verify login, callback, cookie and API origin behavior together in the SOC Vite deployment. |
| 5 | Route and test cleanup | Resolve duplicate evolution summary registration, false-success reset and synthetic benchmarking routes; remove stale patches and replace circular assertions with real handler/service tests. |
| 6 | Cross-copilot discovery — subsequently completed | Trading, Purchasing, DataOps and S2P inventories are included below; product ownership and remediation decisions remain follow-up work. |

**End of the original SOC run.** Its remaining-work list is superseded by the continuation below.

## Continuation — Trading and Purchasing (2026-09-06)

This continuation performs **source-only route/consumer mapping and a focused semantic patch/mock review for Trading, then Purchasing**, in that order. It does not re-run the SOC audit above. Application source and tests were not modified, no git commands were used, and no applications or tests were executed. Only this report is being updated, as subsequently authorized. Implemented handler code is evidence of an available code path, **not proof of runtime health**.

**Historical scope of this continuation:** this run audited Trading and Purchasing only. DataOps and S2P were subsequently audited in the [completed continuation below](#continuation--dataops-and-s2p-2026-09-06), which includes their detailed route and patch-operation inventories.

### Scope and counting method

- Followed registrations from each assembled `main.py`, including shared SDK router factories, prefixes, aliases and conditional inclusion. FastAPI's automatic documentation/OpenAPI endpoints are excluded.
- Followed the frontend import graph from `src/main.tsx`, screens and mounted child components into shared SDK components. Counted live wrappers and direct calls; listed unused API wrappers separately. A literal in an unmounted endpoint map is not a frontend caller.
- Resolved query strings, URL templates and parameter names. Purchasing's concatenated `centroid-history` URL and escaped export alias are live: `api.ts:654–661` → `components/CentroidTimelineChart.tsx:24`.
- Compared **method plus path** and checked shadowing. Trading's dynamic promotion-category route is not credited with the separate static dashboard route's consumer.
- Searched the other SDK frontends, SOC frontend, and shared SDK frontend for Trading/Purchasing preview consumers. None was found for their zero-consumer endpoints. SOC-to-S2P preview consumers were subsequently verified in the [S2P cross-reference](#soc-preview-cross-reference--s2p).
- “No native frontend consumer” does **not** establish dead code. Webhooks, health checks, administrative actions, external integrations and alternate projection APIs can legitimately lack a browser caller. The four requested finding classifications apply to substantiated findings below; other no-consumer rows retain an explicit API-only/alternate-adapter/product-disposition note rather than an invented UI bug.
- The call-site inventory counts source call sites in reachable code, **not requests per page load**. Dynamic user-selected identifiers are represented by `{}`.

| Measure | Trading | Purchasing |
|---|---:|---:|
| Registered application routes, including aliases/duplicates and demo-conditional routes | 162 | 162 |
| Unique method/path pairs | 160 | 161 |
| Unique endpoints with no native frontend consumer found | **81** | **75** |
| Frontend call sites enumerated, after resolving the Purchasing export alias | 86 | 91 |
| Unused wrapper call sites enumerated | 5 | 13 |
| Confirmed unconditional absent method/path calls in the inspected demo configuration | 0 | 0 |
| Active calls with a confirmed demo-off 404 condition | 0 established here | **6** |
| Shadowed route registrations | **2** | **1** |
| Ranked MISSING_UI endpoint pairs | **15** | **8** |
| Lines mentioning monkeypatch / files | 368 / 24 | 79 / 8 |
| Explicit patch operations reviewed | **177** | **26** |
| Confirmed additional CIRCULAR/fixed-output tests | **1** | **2** |
| Confirmed additional STALE patch sites | **0** | **0** |

Purchasing's route total includes five demo-conditional registrations: chain validate/sdk-transfer/status and discovery insights/digest. Without demo mode, those five registrations are absent (157 registrations, 156 unique pairs). The always-registered chain-seed and chain-transfer handlers also return 404 with demo disabled. Its reset handler is similarly demo-gated but has no active frontend caller. Evidence: `backend/app/main.py:723–733,825–829,923–925`; `routers/chain_router.py:58–70`; `routers/discovery_router.py:32–46`. **`demo.py:145` explicitly sets DEMO_MODE=1**, so this is not a claim that the normal demo launcher has missing chain/discovery routes.

<a id="trading-findings"></a>

### Part A — Trading findings

Reference prefixes in the continuation: **TB/PB** = Trading/Purchasing backend app; **TF/PF** = their frontend src; **TT/PT** = their backend tests; **K** = copilot-sdk/copilot_sdk. Each linked reference resolves to the full workspace path.

#### TRD-1 — MISSING_UI, P1

Copilot: **trading**.

- **POST /api/trading/journal/entry** — [TB/routers/journal.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L90)
- **PUT /api/trading/journal/entry/{entry_id}/reflection** — [TB/routers/journal.py:127](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L127)
- **PUT /api/trading/journal/entry/{entry_id}/tags** — [TB/routers/journal.py:143](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L143)

**Evidence and impact:** Journal entry creation, reflection editing, and tag editing are implemented in the backend but have no mounted frontend controls or API wrappers. The journal screen loads collections and detail only. Checked: [TF/screens/JournalScreen.tsx:65](../../../copilot-sdk/apps/trading/frontend/src/screens/JournalScreen.tsx#L65), [TF/screens/JournalScreen.tsx:96](../../../copilot-sdk/apps/trading/frontend/src/screens/JournalScreen.tsx#L96). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Add typed journal mutation calls and editing controls, then verify persistence by reloading through the assembled app.

#### TRD-2 — DEAD_CODE, P2

Copilot: **trading**.

- **GET /api/trading/trades** — [TB/routers/journal.py:40](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L40); [TB/routers/data_import.py:155](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L155)
- **GET /api/trading/trades/{trade_id}** — [TB/routers/journal.py:83](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L83); [TB/routers/data_import.py:163](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L163)

**Evidence and impact:** The journal router is mounted before data_import and claims both paths. data_import.py:155 and :163 are shadowed. The detail URL is actively consumed, but reaches journal.py:83. Journal's _journal_records also reads _trade_store_ref, so this is not evidence that imported trades vanish. Checked: [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532), [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613), [TF/api.ts:148](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L148). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Assign collection/detail to one router and test the assembled application; preserve the journal/import union before removing the shadowed handlers.

#### TRD-3 — MISSING_UI, P2

Copilot: **trading**.

- **GET /api/trading/traders** — [TB/routers/social.py:29](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L29)
- **GET /api/trading/traders/compare** — [TB/routers/social.py:34](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L34)
- **GET /api/trading/traders/{trader_id}/profile** — [TB/routers/social.py:41](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L41)
- **GET /api/trading/traders/{trader_id}/edge** — [TB/routers/social.py:45](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L45)
- **GET /api/trading/social/leaderboard** — [TB/routers/social.py:49](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L49)
- **GET /api/trading/social** — [TB/routers/social.py:54](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L54)
- **GET /api/trading/profiles** — [TB/routers/social.py:59](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L59)
- **GET /api/trading/trader/{trader_id}** — [TB/routers/social.py:65](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L65)
- **POST /api/trading/score-as** — [TB/routers/social.py:69](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L69)

**Evidence and impact:** The social/profile/comparison/score-as surface has no native frontend consumer. The mounted tabs are dashboard, log, analysis, performance, journal, and detail. No cross-copilot preview consumer was found. Checked: [TF/App.tsx:14](../../../copilot-sdk/apps/trading/frontend/src/App.tsx#L14), [TF/api.ts:137](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L137). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Decide whether social comparison belongs in the product; if retained, build one profile/compare flow and consolidate redundant aliases.

#### TRD-4 — MISSING_UI, P2

Copilot: **trading**.

- **POST /api/trading/evolution/generate** — [TB/routers/evolution_router.py:153](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L153)
- **POST /api/trading/evolution/shadow-test** — [TB/routers/evolution_router.py:158](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L158)
- **POST /api/trading/evolution/promote** — [TB/routers/evolution_router.py:173](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L173)

**Evidence and impact:** The existing evolution controls support parameter proposals, apply, and rollback. They do not expose this distinct variant generate → shadow-test → promote lifecycle. This is an additional workflow gap, not evidence that all evolution controls are missing. Checked: [TF/components/EvolutionControlsPanel.tsx:2](../../../copilot-sdk/apps/trading/frontend/src/components/EvolutionControlsPanel.tsx#L2), [TF/components/EvolutionControlsPanel.tsx:64](../../../copilot-sdk/apps/trading/frontend/src/components/EvolutionControlsPanel.tsx#L64). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Provide an explicitly approved variant lifecycle if it is in scope, or designate these routes as operator-only and document that boundary.

#### TRD-5 — DEAD_CODE, P3

Copilot: **trading**.

- **GET /api/trading/regime/reconvergenc** — [TB/routers/regime_beats.py:132](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L132)

**Evidence and impact:** The misspelled reconvergenc address is an extra alias beside reconvergence, with no frontend caller. This is a redundant compatibility surface, not a frontend 404. Checked: [TB/routers/regime_beats.py:133](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L133), [TF/components/DemoBeatPanels.tsx:85](../../../copilot-sdk/apps/trading/frontend/src/components/DemoBeatPanels.tsx#L85). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Check external clients before retiring the misspelled alias; retain a single documented reconvergence path.

**Trading reverse check:** no active native frontend method/path mismatch was confirmed. The unused `getPromotionDetail` wrapper at TF/api.ts:347 targets a real route; it is not a 404. The misspelled reconvergence alias is also a backend alias, not a frontend typo. Shared SelfComputationPanels is mounted at [TF/App.tsx:83](../../../copilot-sdk/apps/trading/frontend/src/App.tsx#L83), so its child requests count as Trading consumers. The unmounted [K/frontend/providers/tradingEndpointMap.ts:8](../../../copilot-sdk/copilot_sdk/frontend/providers/tradingEndpointMap.ts#L8) endpoint map is not credited as an active consumer.

**Excluded false positives:** RegimeMirror/Abstention/Throttle/Rejection panels at [TF/components/DemoBeatPanels.tsx:85](../../../copilot-sdk/apps/trading/frontend/src/components/DemoBeatPanels.tsx#L85) use the situation endpoints; volatility panels at [TF/components/DemoBeatPanels.tsx:114](../../../copilot-sdk/apps/trading/frontend/src/components/DemoBeatPanels.tsx#L114) use /volatility paths. Unused /regime/* beat and /vol/* adapters therefore do not prove those UI panels are missing. Trading's journal /trades collection alias and its shadowed registration are distinguished in the inventory.

### Trading — complete registered-route / frontend diff

| Registered route | Handler declaration | Registration in main | Live frontend call site(s) | Disposition |
|---|---|---|---|---|
| POST `/api/trading/journal/query` | [TB/main.py:535](../../../copilot-sdk/apps/trading/backend/app/main.py#L535) | direct main route | [TF/components/JournalQueryBar.tsx:49](../../../copilot-sdk/apps/trading/frontend/src/components/JournalQueryBar.tsx#L49) | WIRED |
| GET `/api/trading/score/counterfactual/default` | [TB/main.py:541](../../../copilot-sdk/apps/trading/backend/app/main.py#L541) | direct main route | [TF/components/CounterfactualCard.tsx:43](../../../copilot-sdk/apps/trading/frontend/src/components/CounterfactualCard.tsx#L43) | WIRED |
| GET `/api/trading/correlation/config` | [TB/main.py:546](../../../copilot-sdk/apps/trading/backend/app/main.py#L546) | direct main route | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/trading/iks` | [TB/main.py:551](../../../copilot-sdk/apps/trading/backend/app/main.py#L551) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/health` | [TB/main.py:627](../../../copilot-sdk/apps/trading/backend/app/main.py#L627) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/trading/fingerprint` | [TB/main.py:645](../../../copilot-sdk/apps/trading/backend/app/main.py#L645) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| POST `/api/score` | [K/backend/scoring_router.py:203](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L203) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [TF/api.ts:1038](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1038) | WIRED |
| POST `/api/learn` | [K/backend/scoring_router.py:243](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L243) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [TF/api.ts:1049](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1049) | WIRED |
| GET `/api/fingerprint` | [K/backend/scoring_router.py:345](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L345) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [TF/api.ts:1026](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1026); [K/frontend/DataTrustBadge.tsx:35](../../../copilot-sdk/copilot_sdk/frontend/DataTrustBadge.tsx#L35) | WIRED |
| GET `/api/trajectory` | [K/backend/scoring_router.py:353](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L353) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [TF/api.ts:980](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L980) | WIRED |
| GET `/api/health` | [K/backend/scoring_router.py:360](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L360) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [K/frontend/DayZeroPanel.tsx:89](../../../copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx#L89) | WIRED |
| GET `/api/diagnostics` | [K/backend/scoring_router.py:369](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L369) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/history` | [K/backend/scoring_router.py:387](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L387) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | [TF/api.ts:602](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L602) | WIRED |
| GET `/api/measurement-state` | [K/backend/scoring_router.py:402](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L402) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | None found | NO_UI: measurement API; unmounted adapter maps are not callers |
| GET `/api/{copilot}/measurement-state` | [K/backend/scoring_router.py:407](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L407) | [TB/main.py:475](../../../copilot-sdk/apps/trading/backend/app/main.py#L475) | None found | NO_UI: measurement API; unmounted adapter maps are not callers |
| POST `/api/trading/score/counterfactual` | [K/backend/counterfactual_router.py:54](../../../copilot-sdk/copilot_sdk/backend/counterfactual_router.py#L54) | [TB/main.py:487](../../../copilot-sdk/apps/trading/backend/app/main.py#L487) | [TF/api.ts:835](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L835) | WIRED |
| GET `/api/transfer/status` | [K/backend/transfer_router.py:52](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L52) | [TB/main.py:494](../../../copilot-sdk/apps/trading/backend/app/main.py#L494) | [TF/api.ts:904](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L904); [K/frontend/TransferBadge.tsx:23](../../../copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx#L23) | WIRED |
| GET `/api/transfer/opportunities` | [K/backend/transfer_router.py:58](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L58) | [TB/main.py:494](../../../copilot-sdk/apps/trading/backend/app/main.py#L494) | [TF/api.ts:900](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L900) | WIRED |
| GET `/api/transfer/demo` | [K/backend/transfer_router.py:85](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L85) | [TB/main.py:494](../../../copilot-sdk/apps/trading/backend/app/main.py#L494) | None found | NO_UI: demo/admin/cache API; no mounted caller |
| POST `/api/transfer/execute` | [K/backend/transfer_router.py:109](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L109) | [TB/main.py:494](../../../copilot-sdk/apps/trading/backend/app/main.py#L494) | [TF/api.ts:912](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L912) | WIRED |
| GET `/api/self/transfers` | [K/backend/transfer_router.py:237](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L237) | [TB/main.py:495](../../../copilot-sdk/apps/trading/backend/app/main.py#L495) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/transfer` | [K/backend/transfer_router.py:264](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L264) | [TB/main.py:495](../../../copilot-sdk/apps/trading/backend/app/main.py#L495) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/archetypes` | [K/backend/archetype_router.py:29](../../../copilot-sdk/copilot_sdk/backend/archetype_router.py#L29) | [TB/main.py:496](../../../copilot-sdk/apps/trading/backend/app/main.py#L496) | [TF/api.ts:952](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L952) | WIRED |
| GET `/api/archetypes/current` | [K/backend/archetype_router.py:37](../../../copilot-sdk/copilot_sdk/backend/archetype_router.py#L37) | [TB/main.py:496](../../../copilot-sdk/apps/trading/backend/app/main.py#L496) | [TF/api.ts:960](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L960) | WIRED |
| GET `/api/archetypes/{name}` | [K/backend/archetype_router.py:42](../../../copilot-sdk/copilot_sdk/backend/archetype_router.py#L42) | [TB/main.py:496](../../../copilot-sdk/apps/trading/backend/app/main.py#L496) | [TF/api.ts:956](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L956) | WIRED |
| POST `/api/archetypes/apply/{name}` | [K/backend/archetype_router.py:46](../../../copilot-sdk/copilot_sdk/backend/archetype_router.py#L46) | [TB/main.py:496](../../../copilot-sdk/apps/trading/backend/app/main.py#L496) | [TF/api.ts:964](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L964) | WIRED |
| GET `/api/evolution/variants` | [K/backend/evolution_router.py:79](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L79) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | [TF/api.ts:717](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L717) | WIRED |
| GET `/api/evolution/history` | [K/backend/evolution_router.py:108](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L108) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | [TF/api.ts:723](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L723) | WIRED |
| GET `/api/evolution/promoted` | [K/backend/evolution_router.py:124](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L124) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | [TF/api.ts:727](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L727) | WIRED |
| GET `/api/evolution/summary` | [K/backend/evolution_router.py:141](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L141) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/evolution/record-outcome` | [K/backend/evolution_router.py:169](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L169) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/evolution/check-promotion` | [K/backend/evolution_router.py:192](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L192) | [TB/main.py:497](../../../copilot-sdk/apps/trading/backend/app/main.py#L497) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/trading/evolution/log` | [TB/routers/evolution_router.py:74](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L74) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:732](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L732); [TF/api.ts:762](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L762) | WIRED |
| GET `/api/trading/evolution/rejection-summary` | [TB/routers/evolution_router.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L90) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:815](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L815) | WIRED |
| GET `/api/trading/evolution/active` | [TB/routers/evolution_router.py:126](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L126) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:736](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L736); [TF/api.ts:754](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L754) | WIRED |
| GET `/api/trading/evolution/proposals` | [TB/routers/evolution_router.py:136](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L136) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:750](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L750) | WIRED |
| POST `/api/trading/evolution/generate` | [TB/routers/evolution_router.py:153](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L153) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | None found | MISSING_UI / P2: TRD-4 |
| POST `/api/trading/evolution/shadow-test` | [TB/routers/evolution_router.py:158](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L158) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | None found | MISSING_UI / P2: TRD-4 |
| POST `/api/trading/evolution/promote` | [TB/routers/evolution_router.py:173](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L173) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | None found | MISSING_UI / P2: TRD-4 |
| POST `/api/trading/evolution/apply` | [TB/routers/evolution_router.py:178](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L178) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:767](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L767) | WIRED |
| POST `/api/trading/evolution/rollback` | [TB/routers/evolution_router.py:195](../../../copilot-sdk/apps/trading/backend/app/routers/evolution_router.py#L195) | [TB/main.py:505](../../../copilot-sdk/apps/trading/backend/app/main.py#L505) | [TF/api.ts:773](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L773) | WIRED |
| GET `/api/conservation/status` | [K/backend/conservation_router.py:42](../../../copilot-sdk/copilot_sdk/backend/conservation_router.py#L42) | [TB/main.py:516](../../../copilot-sdk/apps/trading/backend/app/main.py#L516) | [TF/api.ts:984](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L984); [K/frontend/DayZeroPanel.tsx:90](../../../copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx#L90) | WIRED |
| POST `/api/conservation/what-if` | [K/backend/conservation_router.py:56](../../../copilot-sdk/copilot_sdk/backend/conservation_router.py#L56) | [TB/main.py:516](../../../copilot-sdk/apps/trading/backend/app/main.py#L516) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history` | [K/backend/self_computation_router.py:107](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L107) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [TF/api.ts:993](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L993) | WIRED |
| GET `/api/self/centroid-timeline` | [K/backend/self_computation_router.py:154](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L154) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/CentroidTimelinePanel.tsx:12](../../../copilot-sdk/copilot_sdk/frontend/CentroidTimelinePanel.tsx#L12) | WIRED |
| POST `/api/self/regime-reinit` | [K/backend/self_computation_router.py:163](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L163) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/evolution/summary` | [K/backend/self_computation_router.py:181](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L181) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [TF/api.ts:819](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L819) | WIRED |
| GET `/api/self/diagnostics` | [K/backend/self_computation_router.py:189](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L189) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/self/centroid-history/{checkpoint_id}/counterfactual` | [K/backend/self_computation_router.py:221](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L221) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history/{checkpoint_id}/lineage` | [K/backend/self_computation_router.py:337](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L337) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history/{checkpoint_id}/replay` | [K/backend/self_computation_router.py:348](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L348) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/replay-score` | [K/backend/self_computation_router.py:368](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L368) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/decisions/{decision_id}/checkpoints` | [K/backend/self_computation_router.py:413](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L413) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/accuracy-by-category` | [K/backend/self_computation_router.py:422](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L422) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [TF/api.ts:998](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L998) | WIRED |
| GET `/api/self/accuracy-alerts` | [K/backend/self_computation_router.py:457](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L457) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/AccuracyAlertsPanel.tsx:10](../../../copilot-sdk/copilot_sdk/frontend/AccuracyAlertsPanel.tsx#L10) | WIRED |
| GET `/api/self/trust-traps` | [K/backend/self_computation_router.py:465](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L465) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/rollback` | [K/backend/self_computation_router.py:471](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L471) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/decisions` | [K/backend/self_computation_router.py:481](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L481) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/DecisionExplorerPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/DecisionExplorerPanel.tsx#L9); [TF/api.ts:1014](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1014) | WIRED |
| GET `/api/self/rule-genealogy` | [K/backend/self_computation_router.py:508](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L508) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/RuleGenealogyPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/RuleGenealogyPanel.tsx#L9) | WIRED |
| GET `/api/self/rule-lifecycle/{rule_id}` | [K/backend/self_computation_router.py:514](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L514) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/RuleLifecyclePanel.tsx:10](../../../copilot-sdk/copilot_sdk/frontend/RuleLifecyclePanel.tsx#L10) | WIRED |
| GET `/api/self/audit-trail` | [K/backend/self_computation_router.py:525](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L525) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | [K/frontend/AuditTrailPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/AuditTrailPanel.tsx#L9); [TF/api.ts:1022](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1022) | WIRED |
| GET `/api/self/decision-flow` | [K/backend/self_computation_router.py:556](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L556) | [TB/main.py:523](../../../copilot-sdk/apps/trading/backend/app/main.py#L523) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/context/market-snapshot` | [TB/context_router.py:296](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L296) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:972](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L972) | WIRED |
| GET `/api/context/ticker/{ticker}` | [TB/context_router.py:330](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L330) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:976](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L976) | WIRED |
| GET `/api/context/portfolio-summary` | [TB/context_router.py:365](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L365) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/context/analytics` | [TB/context_router.py:379](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L379) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:113](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L113) | WIRED |
| GET `/api/context/trust-analysis` | [TB/context_router.py:390](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L390) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:1030](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1030) | WIRED |
| GET `/api/context/patterns` | [TB/context_router.py:402](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L402) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:1034](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1034) | WIRED |
| GET `/api/context/conservation-breakdown` | [TB/context_router.py:424](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L424) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:988](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L988) | WIRED |
| GET `/api/context/similar` | [TB/context_router.py:462](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L462) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:1087](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1087) | WIRED |
| POST `/api/context/trade-metadata` | [TB/context_router.py:521](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L521) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:1059](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1059) | WIRED |
| GET `/api/context/trade-metadata` | [TB/context_router.py:536](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L536) | [TB/main.py:530](../../../copilot-sdk/apps/trading/backend/app/main.py#L530) | [TF/api.ts:968](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L968) | WIRED |
| GET `/api/trading/evidence/{trade_id}` | [TB/routers/evidence.py:28](../../../copilot-sdk/apps/trading/backend/app/routers/evidence.py#L28) | [TB/main.py:531](../../../copilot-sdk/apps/trading/backend/app/main.py#L531) | [TF/api.ts:165](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L165) | WIRED |
| GET `/api/trading/journal/trades` | [TB/routers/journal.py:39](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L39) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | [TF/api.ts:144](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L144) | WIRED |
| GET `/api/trading/trades` | [TB/routers/journal.py:40](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L40) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | None found | DEAD_CODE / P2: TRD-2 |
| GET `/api/trading/trades/{trade_id}` | [TB/routers/journal.py:83](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L83) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | [TF/api.ts:148](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L148) | WIRED; see TRD-2 |
| POST `/api/trading/journal/entry` | [TB/routers/journal.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L90) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | None found | MISSING_UI / P1: TRD-1 |
| PUT `/api/trading/journal/entry/{entry_id}/reflection` | [TB/routers/journal.py:127](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L127) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | None found | MISSING_UI / P1: TRD-1 |
| PUT `/api/trading/journal/entry/{entry_id}/tags` | [TB/routers/journal.py:143](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L143) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | None found | MISSING_UI / P1: TRD-1 |
| GET `/api/trading/analytics` | [TB/routers/journal.py:159](../../../copilot-sdk/apps/trading/backend/app/routers/journal.py#L159) | [TB/main.py:532](../../../copilot-sdk/apps/trading/backend/app/main.py#L532) | [TF/api.ts:157](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L157) | WIRED |
| GET `/api/trading/claim-gate` | [TB/routers/claim_gate_router.py:20](../../../copilot-sdk/apps/trading/backend/app/routers/claim_gate_router.py#L20) | [TB/main.py:533](../../../copilot-sdk/apps/trading/backend/app/main.py#L533) | [TF/api.ts:455](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L455) | WIRED |
| GET `/api/trading/execution-analysis` | [TB/routers/analytics.py:35](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L35) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/cross-insights` | [TB/routers/analytics.py:61](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L61) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/trading/analytics/vol-sharpe` | [TB/routers/analytics.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L90) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | [TF/api.ts:365](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L365) | WIRED |
| GET `/api/trading/analytics/vrp-attribution` | [TB/routers/analytics.py:96](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L96) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | [TF/api.ts:391](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L391) | WIRED |
| GET `/api/trading/analytics/regime-vrp` | [TB/routers/analytics.py:102](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L102) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | [TF/api.ts:395](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L395) | WIRED |
| GET `/api/trading/analytics/dispersion-follow` | [TB/routers/analytics.py:108](../../../copilot-sdk/apps/trading/backend/app/routers/analytics.py#L108) | [TB/main.py:559](../../../copilot-sdk/apps/trading/backend/app/main.py#L559) | [TF/api.ts:459](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L459) | WIRED |
| GET `/api/trading/correlation` | [TB/routers/correlation.py:34](../../../copilot-sdk/apps/trading/backend/app/routers/correlation.py#L34) | [TB/main.py:560](../../../copilot-sdk/apps/trading/backend/app/main.py#L560) | [TF/api.ts:361](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L361) | WIRED |
| GET `/api/trading/execution/analysis` | [TB/routers/execution_router.py:42](../../../copilot-sdk/apps/trading/backend/app/routers/execution_router.py#L42) | [TB/main.py:561](../../../copilot-sdk/apps/trading/backend/app/main.py#L561) | [TF/api.ts:494](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L494) | WIRED |
| GET `/api/trading/execution/summary` | [TB/routers/execution_router.py:47](../../../copilot-sdk/apps/trading/backend/app/routers/execution_router.py#L47) | [TB/main.py:561](../../../copilot-sdk/apps/trading/backend/app/main.py#L561) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| POST `/api/trading/pre-score` | [TB/routers/pre_score_router.py:48](../../../copilot-sdk/apps/trading/backend/app/routers/pre_score_router.py#L48) | [TB/main.py:562](../../../copilot-sdk/apps/trading/backend/app/main.py#L562) | [TF/api.ts:598](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L598) | WIRED |
| POST `/api/trading/prescore` | [TB/routers/prescore.py:43](../../../copilot-sdk/apps/trading/backend/app/routers/prescore.py#L43) | [TB/main.py:569](../../../copilot-sdk/apps/trading/backend/app/main.py#L569) | [TF/api.ts:559](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L559) | WIRED |
| GET `/api/trading/promotion/dashboard` | [TB/routers/promotion_router.py:64](../../../copilot-sdk/apps/trading/backend/app/routers/promotion_router.py#L64) | [TB/main.py:570](../../../copilot-sdk/apps/trading/backend/app/main.py#L570) | [TF/api.ts:343](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L343) | WIRED |
| GET `/api/trading/promotion/{category}` | [TB/routers/promotion_router.py:69](../../../copilot-sdk/apps/trading/backend/app/routers/promotion_router.py#L69) | [TB/main.py:570](../../../copilot-sdk/apps/trading/backend/app/main.py#L570) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| POST `/api/trading/promotion/{category}/promote` | [TB/routers/promotion_router.py:74](../../../copilot-sdk/apps/trading/backend/app/routers/promotion_router.py#L74) | [TB/main.py:570](../../../copilot-sdk/apps/trading/backend/app/main.py#L570) | [TF/api.ts:354](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L354) | WIRED |
| POST `/api/trading/promotion/{category}/demote` | [TB/routers/promotion_router.py:107](../../../copilot-sdk/apps/trading/backend/app/routers/promotion_router.py#L107) | [TB/main.py:570](../../../copilot-sdk/apps/trading/backend/app/main.py#L570) | None found | NO_UI: demo/admin/cache API; no mounted caller |
| GET `/api/trading/promotion` | [TB/routers/promotion.py:33](../../../copilot-sdk/apps/trading/backend/app/routers/promotion.py#L33) | [TB/main.py:577](../../../copilot-sdk/apps/trading/backend/app/main.py#L577) | [TF/api.ts:283](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L283) | WIRED |
| POST `/api/trading/promotion/evaluate` | [TB/routers/promotion.py:42](../../../copilot-sdk/apps/trading/backend/app/routers/promotion.py#L42) | [TB/main.py:577](../../../copilot-sdk/apps/trading/backend/app/main.py#L577) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/trading/regime` | [TB/routers/regime.py:41](../../../copilot-sdk/apps/trading/backend/app/routers/regime.py#L41) | [TB/main.py:584](../../../copilot-sdk/apps/trading/backend/app/main.py#L584) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/detail` | [TB/routers/regime.py:58](../../../copilot-sdk/apps/trading/backend/app/routers/regime.py#L58) | [TB/main.py:584](../../../copilot-sdk/apps/trading/backend/app/main.py#L584) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/current` | [TB/routers/regime_router.py:48](../../../copilot-sdk/apps/trading/backend/app/routers/regime_router.py#L48) | [TB/main.py:591](../../../copilot-sdk/apps/trading/backend/app/main.py#L591) | [TF/api.ts:228](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L228) | WIRED |
| GET `/api/trading/regime/history` | [TB/routers/regime_router.py:60](../../../copilot-sdk/apps/trading/backend/app/routers/regime_router.py#L60) | [TB/main.py:591](../../../copilot-sdk/apps/trading/backend/app/main.py#L591) | [TF/api.ts:232](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L232) | WIRED |
| GET `/api/trading/regime/performance` | [TB/routers/regime_router.py:64](../../../copilot-sdk/apps/trading/backend/app/routers/regime_router.py#L64) | [TB/main.py:591](../../../copilot-sdk/apps/trading/backend/app/main.py#L591) | [TF/api.ts:236](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L236) | WIRED |
| GET `/api/trading/regime/recommendation` | [TB/routers/regime_router.py:87](../../../copilot-sdk/apps/trading/backend/app/routers/regime_router.py#L87) | [TB/main.py:591](../../../copilot-sdk/apps/trading/backend/app/main.py#L591) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime-analytics` | [TB/routers/regime_analytics.py:27](../../../copilot-sdk/apps/trading/backend/app/routers/regime_analytics.py#L27) | [TB/main.py:592](../../../copilot-sdk/apps/trading/backend/app/main.py#L592) | [TF/components/RegimeAnalyticsPanel.tsx:73](../../../copilot-sdk/apps/trading/frontend/src/components/RegimeAnalyticsPanel.tsx#L73) | WIRED |
| GET `/api/trading/regime-analytics/summary` | [TB/routers/regime_analytics.py:32](../../../copilot-sdk/apps/trading/backend/app/routers/regime_analytics.py#L32) | [TB/main.py:592](../../../copilot-sdk/apps/trading/backend/app/main.py#L592) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime-status` | [TB/routers/regime_status.py:16](../../../copilot-sdk/apps/trading/backend/app/routers/regime_status.py#L16) | [TB/main.py:593](../../../copilot-sdk/apps/trading/backend/app/main.py#L593) | [TF/api.ts:244](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L244) | WIRED |
| GET `/api/trading/regime/mirror` | [TB/routers/regime_beats.py:34](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L34) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/abstention` | [TB/routers/regime_beats.py:64](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L64) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/throttle` | [TB/routers/regime_beats.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L90) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/rejection` | [TB/routers/regime_beats.py:113](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L113) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/regime/reconvergenc` | [TB/routers/regime_beats.py:132](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L132) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | DEAD_CODE / P3: TRD-5 |
| GET `/api/trading/regime/reconvergence` | [TB/routers/regime_beats.py:133](../../../copilot-sdk/apps/trading/backend/app/routers/regime_beats.py#L133) | [TB/main.py:594](../../../copilot-sdk/apps/trading/backend/app/main.py#L594) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/situation` | [TB/routers/situation_router.py:37](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L37) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:403](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L403) | WIRED |
| GET `/api/trading/situation/regime` | [TB/routers/situation_router.py:53](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L53) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:399](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L399) | WIRED |
| GET `/api/trading/situation/conditioned-stats` | [TB/routers/situation_router.py:76](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L76) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:407](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L407) | WIRED |
| GET `/api/trading/situation/sharpe-adjustment` | [TB/routers/situation_router.py:81](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L81) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:411](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L411) | WIRED |
| GET `/api/trading/situation/abstention` | [TB/routers/situation_router.py:85](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L85) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:415](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L415) | WIRED |
| GET `/api/trading/situation/regime-rejections` | [TB/routers/situation_router.py:90](../../../copilot-sdk/apps/trading/backend/app/routers/situation_router.py#L90) | [TB/main.py:601](../../../copilot-sdk/apps/trading/backend/app/main.py#L601) | [TF/api.ts:419](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L419) | WIRED |
| GET `/api/trading/traders` | [TB/routers/social.py:29](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L29) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/traders/compare` | [TB/routers/social.py:34](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L34) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/traders/{trader_id}/profile` | [TB/routers/social.py:41](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L41) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/traders/{trader_id}/edge` | [TB/routers/social.py:45](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L45) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/social/leaderboard` | [TB/routers/social.py:49](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L49) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/social` | [TB/routers/social.py:54](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L54) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/profiles` | [TB/routers/social.py:59](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L59) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/trader/{trader_id}` | [TB/routers/social.py:65](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L65) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| POST `/api/trading/score-as` | [TB/routers/social.py:69](../../../copilot-sdk/apps/trading/backend/app/routers/social.py#L69) | [TB/main.py:602](../../../copilot-sdk/apps/trading/backend/app/main.py#L602) | None found | MISSING_UI / P2: TRD-3 |
| GET `/api/trading/vix-timing` | [TB/routers/vix_timing.py:36](../../../copilot-sdk/apps/trading/backend/app/routers/vix_timing.py#L36) | [TB/main.py:603](../../../copilot-sdk/apps/trading/backend/app/main.py#L603) | [TF/api.ts:463](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L463) | WIRED |
| GET `/api/trading/volatility/sharpe` | [TB/routers/volatility_router.py:27](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_router.py#L27) | [TB/main.py:604](../../../copilot-sdk/apps/trading/backend/app/main.py#L604) | [TF/api.ts:370](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L370) | WIRED |
| GET `/api/trading/volatility/vrp` | [TB/routers/volatility_router.py:31](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_router.py#L31) | [TB/main.py:604](../../../copilot-sdk/apps/trading/backend/app/main.py#L604) | [TF/api.ts:374](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L374) | WIRED |
| GET `/api/trading/volatility/rich-cheap` | [TB/routers/volatility_router.py:35](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_router.py#L35) | [TB/main.py:604](../../../copilot-sdk/apps/trading/backend/app/main.py#L604) | [TF/api.ts:379](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L379) | WIRED |
| GET `/api/trading/volatility/dispersion` | [TB/routers/volatility_router.py:39](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_router.py#L39) | [TB/main.py:604](../../../copilot-sdk/apps/trading/backend/app/main.py#L604) | [TF/api.ts:383](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L383) | WIRED |
| GET `/api/trading/volatility/tail-bets` | [TB/routers/volatility_router.py:43](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_router.py#L43) | [TB/main.py:604](../../../copilot-sdk/apps/trading/backend/app/main.py#L604) | [TF/api.ts:387](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L387) | WIRED |
| GET `/api/trading/vol/short-vol-illusion` | [TB/routers/volatility_beats.py:34](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L34) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/vol/vrp-edge` | [TB/routers/volatility_beats.py:58](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L58) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/vol/situational-abstention` | [TB/routers/volatility_beats.py:70](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L70) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/vol/rich-cheap` | [TB/routers/volatility_beats.py:91](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L91) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/vol/dispersion-follow` | [TB/routers/volatility_beats.py:103](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L103) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/vol/effective-bets` | [TB/routers/volatility_beats.py:108](../../../copilot-sdk/apps/trading/backend/app/routers/volatility_beats.py#L108) | [TB/main.py:605](../../../copilot-sdk/apps/trading/backend/app/main.py#L605) | None found | NO_UI: alternate analytics/beat adapter; existing panels use other contracts |
| GET `/api/trading/cohort-status` | [TB/routers/cohort_status_router.py:20](../../../copilot-sdk/apps/trading/backend/app/routers/cohort_status_router.py#L20) | [TB/main.py:606](../../../copilot-sdk/apps/trading/backend/app/main.py#L606) | [TF/api.ts:279](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L279) | WIRED |
| POST `/api/trading/webhook/tradingview` | [TB/routers/webhook.py:83](../../../copilot-sdk/apps/trading/backend/app/routers/webhook.py#L83) | [TB/main.py:611](../../../copilot-sdk/apps/trading/backend/app/main.py#L611) | None found | NO_UI: external ingress/setup/test API (history panel uses another path) |
| GET `/api/trading/webhook/history` | [TB/routers/webhook.py:130](../../../copilot-sdk/apps/trading/backend/app/routers/webhook.py#L130) | [TB/main.py:611](../../../copilot-sdk/apps/trading/backend/app/main.py#L611) | [TF/api.ts:525](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L525) | WIRED |
| GET `/api/trading/webhook/config` | [TB/routers/webhook.py:135](../../../copilot-sdk/apps/trading/backend/app/routers/webhook.py#L135) | [TB/main.py:611](../../../copilot-sdk/apps/trading/backend/app/main.py#L611) | None found | NO_UI: external ingress/setup/test API (history panel uses another path) |
| POST `/api/trading/webhook/test` | [TB/routers/webhook.py:156](../../../copilot-sdk/apps/trading/backend/app/routers/webhook.py#L156) | [TB/main.py:611](../../../copilot-sdk/apps/trading/backend/app/main.py#L611) | None found | NO_UI: external ingress/setup/test API (history panel uses another path) |
| GET `/api/broker/status` | [TB/routers/broker_router.py:130](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L130) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/broker/account` | [TB/routers/broker_router.py:148](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L148) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| GET `/api/broker/positions` | [TB/routers/broker_router.py:165](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L165) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| GET `/api/broker/orders` | [TB/routers/broker_router.py:184](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L184) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| POST `/api/broker/orders` | [TB/routers/broker_router.py:207](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L207) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| GET `/api/broker/orders/{order_id}` | [TB/routers/broker_router.py:253](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L253) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| POST `/api/broker/sync` | [TB/routers/broker_router.py:270](../../../copilot-sdk/apps/trading/backend/app/routers/broker_router.py#L270) | [TB/main.py:612](../../../copilot-sdk/apps/trading/backend/app/main.py#L612) | None found | NO_UI: external broker/operator API; do not infer automatic execution UI |
| POST `/api/trading/import/csv` | [TB/routers/data_import.py:86](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L86) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | NO_UI: import API; native import UI absent, CLI/integration surface retained |
| POST `/api/trading/import/broker` | [TB/routers/data_import.py:117](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L117) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | NO_UI: import API; native import UI absent, CLI/integration surface retained |
| GET `/api/trading/trades` | [TB/routers/data_import.py:155](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L155) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | DEAD_CODE / P2: shadowed registration (TRD-2) |
| GET `/api/trading/trades/{trade_id}` | [TB/routers/data_import.py:163](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L163) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | DEAD_CODE / P2: shadowed registration (TRD-2) |
| GET `/api/trading/market/ohlcv` | [TB/routers/data_import.py:170](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L170) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/trading/market/vix` | [TB/routers/data_import.py:184](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L184) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| POST `/api/trading/market/refresh` | [TB/routers/data_import.py:199](../../../copilot-sdk/apps/trading/backend/app/routers/data_import.py#L199) | [TB/main.py:613](../../../copilot-sdk/apps/trading/backend/app/main.py#L613) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/trading/graph/status` | [TB/graph_status.py:458](../../../copilot-sdk/apps/trading/backend/app/graph_status.py#L458) | [TB/main.py:614](../../../copilot-sdk/apps/trading/backend/app/main.py#L614) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/trading/tab-state` | [K/state/tab_state_router.py:14](../../../copilot-sdk/copilot_sdk/state/tab_state_router.py#L14) | [TB/main.py:615](../../../copilot-sdk/apps/trading/backend/app/main.py#L615) | None found | NO_UI: demo/admin/cache API; no mounted caller |
| GET `/api/{copilot}/static-urls` | [K/state/tab_state_router.py:21](../../../copilot-sdk/copilot_sdk/state/tab_state_router.py#L21) | [TB/main.py:615](../../../copilot-sdk/apps/trading/backend/app/main.py#L615) | None found | NO_UI: demo/admin/cache API; no mounted caller |

### Trading — frontend call inventory

| Method / normalized path | Call site | Function/component |
|---|---|---|
| GET `/api/self/accuracy-alerts` | [K/frontend/AccuracyAlertsPanel.tsx:10](../../../copilot-sdk/copilot_sdk/frontend/AccuracyAlertsPanel.tsx#L10) | AccuracyAlertsPanel |
| GET `/api/self/audit-trail` | [K/frontend/AuditTrailPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/AuditTrailPanel.tsx#L9) | AuditTrailPanel |
| GET `/api/self/centroid-timeline` | [K/frontend/CentroidTimelinePanel.tsx:12](../../../copilot-sdk/copilot_sdk/frontend/CentroidTimelinePanel.tsx#L12) | CentroidTimelinePanel |
| GET `/api/self/decisions` | [K/frontend/DecisionExplorerPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/DecisionExplorerPanel.tsx#L9) | DecisionExplorerPanel |
| GET `/api/self/rule-genealogy` | [K/frontend/RuleGenealogyPanel.tsx:9](../../../copilot-sdk/copilot_sdk/frontend/RuleGenealogyPanel.tsx#L9) | RuleGenealogyPanel |
| GET `/api/self/rule-lifecycle/{}` | [K/frontend/RuleLifecyclePanel.tsx:10](../../../copilot-sdk/copilot_sdk/frontend/RuleLifecyclePanel.tsx#L10) | RuleLifecyclePanel |
| GET `/api/context/analytics` | [TF/api.ts:113](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L113) | getAnalytics |
| GET `/api/trading/journal/trades` | [TF/api.ts:144](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L144) | fetchTrades |
| GET `/api/trading/trades/{}` | [TF/api.ts:148](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L148) | fetchTradeDetail |
| GET `/api/trading/analytics` | [TF/api.ts:157](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L157) | fetchAnalytics |
| GET `/api/trading/evidence/{}` | [TF/api.ts:165](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L165) | fetchEvidence |
| GET `/api/trading/regime/current` | [TF/api.ts:228](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L228) | getRegimeCurrent |
| GET `/api/trading/regime/history` | [TF/api.ts:232](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L232) | getRegimeHistory |
| GET `/api/trading/regime/performance` | [TF/api.ts:236](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L236) | getRegimePerformance |
| GET `/api/trading/regime-status` | [TF/api.ts:244](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L244) | getRegimeStatus |
| GET `/api/trading/cohort-status` | [TF/api.ts:279](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L279) | getCohortStatus |
| GET `/api/trading/promotion` | [TF/api.ts:283](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L283) | fetchPromotion |
| GET `/api/trading/promotion/dashboard` | [TF/api.ts:343](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L343) | getPromotionDashboard |
| POST `/api/trading/promotion/{}/promote` | [TF/api.ts:354](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L354) | promoteCategory |
| GET `/api/trading/correlation` | [TF/api.ts:361](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L361) | fetchCorrelation |
| GET `/api/trading/analytics/vol-sharpe` | [TF/api.ts:365](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L365) | fetchVolSharpe |
| GET `/api/trading/volatility/sharpe` | [TF/api.ts:370](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L370) | fetchVolatilitySharpe |
| GET `/api/trading/volatility/vrp` | [TF/api.ts:374](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L374) | fetchVolatilityVrp |
| GET `/api/trading/volatility/rich-cheap` | [TF/api.ts:379](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L379) | fetchVolatilityRichCheap |
| GET `/api/trading/volatility/dispersion` | [TF/api.ts:383](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L383) | fetchVolatilityDispersion |
| GET `/api/trading/volatility/tail-bets` | [TF/api.ts:387](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L387) | fetchVolatilityTailBets |
| GET `/api/trading/analytics/vrp-attribution` | [TF/api.ts:391](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L391) | fetchVrpAttribution |
| GET `/api/trading/analytics/regime-vrp` | [TF/api.ts:395](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L395) | fetchRegimeVrp |
| GET `/api/trading/situation/regime` | [TF/api.ts:399](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L399) | fetchSituationRegime |
| GET `/api/trading/situation` | [TF/api.ts:403](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L403) | fetchSituationJudgment |
| GET `/api/trading/situation/conditioned-stats` | [TF/api.ts:407](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L407) | fetchSituationConditionedStats |
| GET `/api/trading/situation/sharpe-adjustment` | [TF/api.ts:411](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L411) | fetchSituationSharpeAdjustment |
| GET `/api/trading/situation/abstention` | [TF/api.ts:415](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L415) | fetchSituationAbstention |
| GET `/api/trading/situation/regime-rejections` | [TF/api.ts:419](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L419) | fetchSituationRejections |
| GET `/api/trading/claim-gate` | [TF/api.ts:455](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L455) | fetchClaimGate |
| GET `/api/trading/analytics/dispersion-follow` | [TF/api.ts:459](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L459) | fetchDispersionFollow |
| GET `/api/trading/vix-timing` | [TF/api.ts:463](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L463) | fetchVIXTiming |
| GET `/api/trading/execution/analysis` | [TF/api.ts:494](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L494) | fetchExecutionAnalysis |
| GET `/api/trading/webhook/history` | [TF/api.ts:525](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L525) | fetchWebhookHistory |
| POST `/api/trading/prescore` | [TF/api.ts:559](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L559) | prescoreTrade |
| POST `/api/trading/pre-score` | [TF/api.ts:598](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L598) | preScore |
| GET `/api/history` | [TF/api.ts:602](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L602) | getHistory |
| GET `/api/evolution/variants` | [TF/api.ts:717](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L717) | getEvolutionVariants |
| GET `/api/evolution/history` | [TF/api.ts:723](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L723) | getEvolutionHistory |
| GET `/api/evolution/promoted` | [TF/api.ts:727](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L727) | getPromotedEvolutionRules |
| GET `/api/trading/evolution/log` | [TF/api.ts:732](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L732) | fetchEvolutionLog |
| GET `/api/trading/evolution/active` | [TF/api.ts:736](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L736) | fetchActiveVariant |
| GET `/api/trading/evolution/proposals` | [TF/api.ts:750](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L750) | fetchEvolutionProposalResponse |
| GET `/api/trading/evolution/active` | [TF/api.ts:754](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L754) | fetchEvolutionActive |
| GET `/api/trading/evolution/log` | [TF/api.ts:762](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L762) | fetchParameterEvolutionLog |
| POST `/api/trading/evolution/apply` | [TF/api.ts:767](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L767) | applyEvolutionProposal |
| POST `/api/trading/evolution/rollback` | [TF/api.ts:773](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L773) | rollbackEvolution |
| GET `/api/trading/evolution/rejection-summary` | [TF/api.ts:815](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L815) | fetchRejectionSummary |
| GET `/api/self/evolution/summary` | [TF/api.ts:819](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L819) | fetchEvolutionSummary |
| POST `/api/trading/score/counterfactual` | [TF/api.ts:835](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L835) | postCounterfactual |
| GET `/api/transfer/opportunities` | [TF/api.ts:900](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L900) | fetchTransferOpportunities |
| GET `/api/transfer/status` | [TF/api.ts:904](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L904) | fetchTransferStatus |
| POST `/api/transfer/execute` | [TF/api.ts:912](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L912) | executeTransfer |
| GET `/api/archetypes` | [TF/api.ts:952](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L952) | fetchArchetypes |
| GET `/api/archetypes/{}` | [TF/api.ts:956](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L956) | fetchArchetype |
| GET `/api/archetypes/current` | [TF/api.ts:960](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L960) | fetchCurrentArchetype |
| POST `/api/archetypes/apply/{}` | [TF/api.ts:964](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L964) | applyArchetype |
| GET `/api/context/trade-metadata` | [TF/api.ts:968](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L968) | getTradeMetadata |
| GET `/api/context/market-snapshot` | [TF/api.ts:972](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L972) | getMarketSnapshot |
| GET `/api/context/ticker/{}` | [TF/api.ts:976](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L976) | getTicker |
| GET `/api/trajectory` | [TF/api.ts:980](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L980) | getTrajectory |
| GET `/api/conservation/status` | [TF/api.ts:984](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L984) | getConservationStatus |
| GET `/api/context/conservation-breakdown` | [TF/api.ts:988](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L988) | getConservationBreakdown |
| GET `/api/self/centroid-history` | [TF/api.ts:993](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L993) | fetchCentroidHistory |
| GET `/api/self/accuracy-by-category` | [TF/api.ts:998](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L998) | fetchAccuracyByCategory |
| GET `/api/self/decisions` | [TF/api.ts:1014](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1014) | fetchDecisions |
| GET `/api/self/audit-trail` | [TF/api.ts:1022](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1022) | fetchAuditTrail |
| GET `/api/fingerprint` | [TF/api.ts:1026](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1026) | getFingerprint |
| GET `/api/context/trust-analysis` | [TF/api.ts:1030](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1030) | getTrustAnalysis |
| GET `/api/context/patterns` | [TF/api.ts:1034](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1034) | getPatterns |
| POST `/api/score` | [TF/api.ts:1038](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1038) | scoreTrade |
| POST `/api/learn` | [TF/api.ts:1049](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1049) | learnTrade |
| POST `/api/context/trade-metadata` | [TF/api.ts:1059](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1059) | saveTradeMetadata |
| GET `/api/context/similar` | [TF/api.ts:1087](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L1087) | getSimilarTrades |
| GET `/api/trading/score/counterfactual/default` | [TF/components/CounterfactualCard.tsx:43](../../../copilot-sdk/apps/trading/frontend/src/components/CounterfactualCard.tsx#L43) | CounterfactualCard |
| GET `/api/fingerprint` | [K/frontend/DataTrustBadge.tsx:35](../../../copilot-sdk/copilot_sdk/frontend/DataTrustBadge.tsx#L35) | DataTrustBadge |
| GET `/api/health` | [K/frontend/DayZeroPanel.tsx:89](../../../copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx#L89) | DayZeroPanel |
| GET `/api/conservation/status` | [K/frontend/DayZeroPanel.tsx:90](../../../copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx#L90) | DayZeroPanel |
| GET `/api/transfer/status` | [K/frontend/TransferBadge.tsx:23](../../../copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx#L23) | TransferBadge |
| POST `/api/trading/journal/query` | [TF/components/JournalQueryBar.tsx:49](../../../copilot-sdk/apps/trading/frontend/src/components/JournalQueryBar.tsx#L49) | submit |
| GET `/api/trading/regime-analytics` | [TF/components/RegimeAnalyticsPanel.tsx:73](../../../copilot-sdk/apps/trading/frontend/src/components/RegimeAnalyticsPanel.tsx#L73) | RegimeAnalyticsPanel |

**Unused API wrappers (not counted as consumers):**

| Method / normalized path | Wrapper declaration/call | Unused function |
|---|---|---|
| GET `/api/trading/regime` | [TF/api.ts:169](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L169) | fetchRegime |
| GET `/api/trading/regime/detail` | [TF/api.ts:173](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L173) | fetchRegimeDetail |
| GET `/api/trading/regime/recommendation` | [TF/api.ts:240](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L240) | getRegimeRecommendation |
| GET `/api/trading/promotion/{}` | [TF/api.ts:347](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L347) | getPromotionDetail |
| GET `/api/trading/execution/summary` | [TF/api.ts:490](../../../copilot-sdk/apps/trading/frontend/src/api.ts#L490) | fetchExecutionSummary |

<a id="purchasing-findings"></a>

### Part A — Purchasing findings

#### PUR-1 — NAME_MISMATCH, P1

Copilot: **purchasing**.

- **GET /api/purchasing/proof-ledger** — [PB/routers/purchasing_control.py:23](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L23)
- **GET /api/purchasing/legal-exposure** — [PB/routers/purchasing_control.py:35](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L35)

**Evidence and impact:** This mounted panel bypasses api.ts normalization and reads raw snake_case JSON as proofCurve/competenceCurve/complianceStatus/evidenceTier. The backend emits proof_curve/competence_curve/compliance_status/evidence_tier; GET middleware returns the body unchanged. Populated counts therefore render as zero and legal status as the fallback. Evidence metadata is not consistently in GET bodies either, so normalizing keys alone does not solve that part. Checked: [PF/components/PurchasingProofPanel.tsx:6](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L6), [PF/components/PurchasingProofPanel.tsx:40](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L40), [PF/components/PurchasingProofPanel.tsx:55](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L55), [PB/services/purchasing_control.py:221](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L221), [PB/services/purchasing_control.py:247](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L247), [PF/api.ts:76](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L76), [PB/services/purchasing_control.py:107](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L107). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Use typed, normalized response contracts and explicitly source evidence metadata from supported fields or headers; verify populated and unavailable states.

#### PUR-2 — NAME_MISMATCH, P1

Copilot: **purchasing**.

- **GET /api/purchasing/competence/ramp** — [PB/routers/learning_beats.py:121](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L121)
- **GET /api/purchasing/economic/roi-summary** — [PB/routers/economic_router.py:25](../../../copilot-sdk/apps/purchasing/backend/app/routers/economic_router.py#L25)
- **GET /api/purchasing/day-0-readiness** — [PB/routers/purchasing_control.py:31](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L31)

**Evidence and impact:** TimeToCompetencePanel expects weeks/days fields, but RampResponse supplies verified counts, target, remaining, and state. NotYetPanel expects remaining-deliveries, weekly-incremental, and coverage-percentage fields absent from readiness/ROI responses, then displays '~60 more deliveries', '$0 incremental this week', and '94%'. Successful requests cannot populate these intended measurements. Checked: [PF/components/PurchasingBeatPanels.tsx:81](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx#L81), [PF/components/PurchasingBeatPanels.tsx:86](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx#L86), [PB/routers/learning_beats.py:53](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L53), [PB/routers/economic_router.py:25](../../../copilot-sdk/apps/purchasing/backend/app/routers/economic_router.py#L25), [PB/services/purchasing_control.py:227](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L227), [PF/api.ts:829](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L829). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Align panel labels and types with actual count-based contracts, and remove unsupported numeric fallbacks unless a separately labelled scenario explicitly supplies them.

#### PUR-3 — MISSING_UI, P1

Copilot: **purchasing**.

- **POST /api/purchasing/match** — [PB/routers/match.py:58](../../../copilot-sdk/apps/purchasing/backend/app/routers/match.py#L58)

**Evidence and impact:** postMatch has no caller; the panel only reads the match queue. Both the backend's empty-history branch and the frontend's empty-response branch substitute DEMO-MATCH-1, $1,000, FULL_MATCH, confidence 1.0. The row is named Demo Supplier, but occupies the normal results table and does not prove that matching was performed. The missing submission flow can therefore be concealed by successful-looking results. Checked: [PF/api.ts:644](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L644), [PF/components/MatchResultPanel.tsx:63](../../../copilot-sdk/apps/purchasing/frontend/src/components/MatchResultPanel.tsx#L63), [PF/components/MatchResultPanel.tsx:5](../../../copilot-sdk/apps/purchasing/frontend/src/components/MatchResultPanel.tsx#L5), [PF/components/MatchResultPanel.tsx:85](../../../copilot-sdk/apps/purchasing/frontend/src/components/MatchResultPanel.tsx#L85), [PB/routers/match.py:425](../../../copilot-sdk/apps/purchasing/backend/app/routers/match.py#L425). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Wire an order/receipt/invoice submission flow if intended, and render honest empty state or a separately gated example; verify results originate from the POST and subsequent queue read.

#### PUR-4 — MISSING_UI, P1

Copilot: **purchasing**.

- **POST /api/purchasing/auto-order/evaluate** — [PB/routers/auto_order_router.py:57](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L57)

**Evidence and impact:** The panel can enable/disable the gate and show status/audit, but evaluateAutoOrder has no frontend caller. The only application call to gate.evaluate found is this endpoint. Enabling the flag alone does not evaluate an order or create auto-order history. Checked: [PF/api.ts:626](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L626), [PF/components/AutoOrderPanel.tsx:2](../../../copilot-sdk/apps/purchasing/frontend/src/components/AutoOrderPanel.tsx#L2), [PF/components/AutoOrderPanel.tsx:76](../../../copilot-sdk/apps/purchasing/frontend/src/components/AutoOrderPanel.tsx#L76), [PB/routers/auto_order_router.py:60](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L60). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Connect the scored-order lifecycle to explicit, conservation-gated evaluation, or clearly present the UI as gate configuration awaiting an external scheduler.

#### PUR-5 — MISSING_UI, P1

Copilot: **purchasing**.

- **POST /api/purchasing/frozen-twin/freeze** — [PB/routers/purchasing_control.py:43](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L43)
- **GET /api/purchasing/frozen-twin/comparison** — [PB/routers/purchasing_control.py:50](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L50)

**Evidence and impact:** Panels display Frozen Twin status but never initialize it or request the comparison. Without an operator/script-created snapshot, status remains NOT_INITIALIZED and the implemented drift comparison cannot be reached through the UI. Checked: [PF/components/PurchasingProofPanel.tsx:28](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L28), [PF/components/PurchasingBeatPanels.tsx:95](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx#L95), [PB/services/purchasing_control.py:249](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L249), [PB/services/purchasing_control.py:273](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L273). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Add a governed freeze-once action and comparison display, including the not-initialized and already-frozen states.

#### PUR-6 — MISSING_UI, P2

Copilot: **purchasing**.

- **POST /api/purchasing/events/record** — [PB/routers/event_router.py:31](../../../copilot-sdk/apps/purchasing/backend/app/routers/event_router.py#L31)

**Evidence and impact:** The event planner requests plans and history but never calls recordEventOutcome. Users cannot submit actual usage/waste through this panel to extend the history it displays. Checked: [PF/api.ts:352](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L352), [PF/components/EventPlannerCard.tsx:2](../../../copilot-sdk/apps/purchasing/frontend/src/components/EventPlannerCard.tsx#L2), [PF/components/EventPlannerCard.tsx:23](../../../copilot-sdk/apps/purchasing/frontend/src/components/EventPlannerCard.tsx#L23). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Add an event completion form using the existing plan/actual-usage/actual-waste contract and refresh history after successful submission.

#### PUR-7 — NAME_MISMATCH, P1

Copilot: **purchasing**.

- **GET /api/purchasing/chain/status** — [PB/routers/chain_router.py:70](../../../copilot-sdk/apps/purchasing/backend/app/routers/chain_router.py#L70)
- **POST /api/purchasing/chain/validate** — [PB/routers/chain_router.py:58](../../../copilot-sdk/apps/purchasing/backend/app/routers/chain_router.py#L58)
- **GET /api/purchasing/discovery/insights** — [PB/routers/discovery_router.py:32](../../../copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py#L32)
- **GET /api/purchasing/discovery/digest** — [PB/routers/discovery_router.py:44](../../../copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py#L44)
- **POST /api/purchasing/demo/chain-seed** — [PB/main.py:723](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L723)
- **POST /api/purchasing/chain/transfer** — [PB/main.py:731](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L731)

**Evidence and impact:** Configuration-dependent reverse wiring gap: chain/discovery panels are mounted unconditionally, but four routes are registered only in demo mode and two always-registered POST handlers return 404 when demo mode is disabled. demo.py explicitly sets DEMO_MODE=1, so its normal demo launch avoids this gap. PYTEST_CURRENT_TEST also silently enables these surfaces, hiding the ordinary-app distinction. Checked: [PB/main.py:825](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L825), [PB/main.py:828](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L828), [PB/main.py:725](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L725), [PB/main.py:733](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L733), [PF/screens/AnalysisScreen.tsx:136](../../../copilot-sdk/apps/purchasing/frontend/src/screens/AnalysisScreen.tsx#L136), [PF/screens/PerformanceScreen.tsx:120](../../../copilot-sdk/apps/purchasing/frontend/src/screens/PerformanceScreen.tsx#L120), [copilot-sdk/demo.py:145](../../../copilot-sdk/demo.py#L145). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Expose capabilities/demo configuration to the frontend and condition these panels/actions on it; test explicit demo-on and demo-off assembled applications.

#### PUR-8 — MISSING_UI, P2

Copilot: **purchasing**.

- **GET /api/purchasing/handoff-pack** — [PB/routers/purchasing_control.py:27](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L27)

**Evidence and impact:** The proof panel says 'Handoff: evidence chain exportable', but has no handoff-pack caller or export action. The separate /audit/export routes are wired and provide a different audit contract. Checked: [PF/components/PurchasingProofPanel.tsx:57](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L57), [PB/services/purchasing_control.py:237](../../../copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py#L237). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Add a handoff-pack export action beside the claim or change the wording to explicitly describe an API-only capability.

#### PUR-9 — MISSING_UI, P2

Copilot: **purchasing**.

- **GET /api/purchasing/promotion** — [PB/routers/purchasing_control.py:64](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L64)
- **POST /api/purchasing/promotion/{decision_class}/advance** — [PB/routers/purchasing_control.py:68](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L68)

**Evidence and impact:** Neither authority records nor the gated advancement action has a mounted frontend consumer. The handler requires observed readiness evidence and GREEN conservation, so any future UI must preserve these controls. Checked: [PF/App.tsx:13](../../../copilot-sdk/apps/purchasing/frontend/src/App.tsx#L13), [PB/routers/purchasing_control.py:80](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L80). The route and frontend call inventories below include the paths and their live/unused wrappers.

**Recommended fix approach:** Provide an explicitly approved authority-status/advance flow if it belongs in the product, otherwise designate this as operator-only.

**Purchasing reverse check:** no unconditional missing native method/path was confirmed in demo mode. PUR-7 records the six demo-off 404 paths. PUR-1/PUR-2 are response-field mismatches at existing routes. The native score/verify flow is wired even though the generic /api/learn wrapper is unused. Both singular/plural supplier-detail adapters exist, while the mounted supplier panel uses the collection /api/purchasing/suppliers/scorecards; this is not a spelling-induced 404.

**Purchasing registration hygiene:** [PB/main.py:590](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L590) registers the custom /api/health before the SDK router is included at line 770; the SDK handler at [K/backend/scoring_router.py:360](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L360) is shadowed. The native frontend does not call either at this URL, but health-check tools can. Keep the richer custom contract and avoid duplicate registrations when cleaning up. This is one shadowed handler, not two different health endpoints.

### Purchasing — complete registered-route / frontend diff

| Registered route | Handler declaration | Registration in main | Live frontend call site(s) | Disposition |
|---|---|---|---|---|
| GET `/api/health` | [PB/main.py:590](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L590) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/waste/analysis` | [PB/main.py:655](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L655) | direct main route | [PF/api.ts:271](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L271) | WIRED |
| GET `/api/purchasing/waste/summary` | [PB/main.py:660](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L660) | direct main route | [PF/api.ts:275](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L275) | WIRED |
| GET `/api/purchasing/par/predict` | [PB/main.py:665](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L665) | direct main route | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/par/predict-week` | [PB/main.py:677](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L677) | direct main route | [PF/api.ts:751](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L751) | WIRED |
| GET `/api/purchasing/disruption/status` | [PB/main.py:695](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L695) | direct main route | [PF/components/DisruptionRecoveryPanel.tsx:32](../../../copilot-sdk/apps/purchasing/frontend/src/components/DisruptionRecoveryPanel.tsx#L32) | WIRED |
| GET `/api/purchasing/disruption/history` | [PB/main.py:699](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L699) | direct main route | [PF/components/DisruptionRecoveryPanel.tsx:33](../../../copilot-sdk/apps/purchasing/frontend/src/components/DisruptionRecoveryPanel.tsx#L33) | WIRED |
| GET `/api/purchasing/payment/timing` | [PB/main.py:703](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L703) | direct main route | [PF/components/PaymentTimingPanel.tsx:36](../../../copilot-sdk/apps/purchasing/frontend/src/components/PaymentTimingPanel.tsx#L36) | WIRED |
| GET `/api/purchasing/payment/summary` | [PB/main.py:707](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L707) | direct main route | [PF/components/PaymentTimingPanel.tsx:37](../../../copilot-sdk/apps/purchasing/frontend/src/components/PaymentTimingPanel.tsx#L37) | WIRED |
| GET `/api/purchasing/audit/pack` | [PB/main.py:711](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L711) | direct main route | [PF/components/AuditExportPanel.tsx:25](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L25) | WIRED |
| GET `/api/purchasing/audit/export/json` | [PB/main.py:715](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L715) | direct main route | [PF/components/AuditExportPanel.tsx:80](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L80) | WIRED |
| GET `/api/purchasing/audit/export/csv` | [PB/main.py:719](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L719) | direct main route | [PF/components/AuditExportPanel.tsx:81](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L81) | WIRED |
| POST `/api/purchasing/demo/chain-seed` | [PB/main.py:723](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L723) | direct main route | [PF/components/ChainTransferCard.tsx:50](../../../copilot-sdk/apps/purchasing/frontend/src/components/ChainTransferCard.tsx#L50) | WIRED; see PUR-7 |
| POST `/api/purchasing/chain/transfer` | [PB/main.py:731](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L731) | direct main route | [PF/api.ts:373](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L373); [PF/components/ChainTransferCard.tsx:51](../../../copilot-sdk/apps/purchasing/frontend/src/components/ChainTransferCard.tsx#L51) | WIRED; see PUR-7 |
| GET `/health` | [PB/main.py:888](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L888) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/fingerprint` | [PB/main.py:905](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L905) | direct main route | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| POST `/api/purchasing/demo/reset` | [PB/main.py:923](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L923) | direct main route | None found | NO_UI: demo/admin/cache API; no mounted caller |
| POST `/api/score` | [K/backend/scoring_router.py:203](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L203) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | [PF/api.ts:703](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L703) | WIRED |
| POST `/api/learn` | [K/backend/scoring_router.py:243](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L243) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | None found | NO_UI: generic learning API; native flow uses /api/purchasing/verify |
| GET `/api/fingerprint` | [K/backend/scoring_router.py:345](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L345) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | [PF/api.ts:463](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L463); [K/frontend/DataTrustBadge.tsx:35](../../../copilot-sdk/copilot_sdk/frontend/DataTrustBadge.tsx#L35) | WIRED |
| GET `/api/trajectory` | [K/backend/scoring_router.py:353](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L353) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | [PF/api.ts:467](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L467) | WIRED |
| GET `/api/health` | [K/backend/scoring_router.py:360](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L360) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | None found | DEAD_CODE / P2: custom main health registered first |
| GET `/api/diagnostics` | [K/backend/scoring_router.py:369](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L369) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/history` | [K/backend/scoring_router.py:387](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L387) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | [PF/api.ts:458](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L458) | WIRED |
| GET `/api/measurement-state` | [K/backend/scoring_router.py:402](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L402) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | None found | NO_UI: measurement API; unmounted adapter maps are not callers |
| GET `/api/{copilot}/measurement-state` | [K/backend/scoring_router.py:407](../../../copilot-sdk/copilot_sdk/backend/scoring_router.py#L407) | [PB/main.py:770](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L770) | [K/frontend/components/DayZeroCard.tsx:62](../../../copilot-sdk/copilot_sdk/frontend/components/DayZeroCard.tsx#L62) | WIRED |
| GET `/api/transfer/status` | [K/backend/transfer_router.py:52](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L52) | [PB/main.py:782](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L782) | [K/frontend/TransferBadge.tsx:23](../../../copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx#L23) | WIRED |
| GET `/api/transfer/opportunities` | [K/backend/transfer_router.py:58](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L58) | [PB/main.py:782](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L782) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/transfer/demo` | [K/backend/transfer_router.py:85](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L85) | [PB/main.py:782](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L782) | None found | NO_UI: demo/admin/cache API; no mounted caller |
| POST `/api/transfer/execute` | [K/backend/transfer_router.py:109](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L109) | [PB/main.py:782](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L782) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/transfers` | [K/backend/transfer_router.py:237](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L237) | [PB/main.py:783](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L783) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/transfer` | [K/backend/transfer_router.py:264](../../../copilot-sdk/copilot_sdk/backend/transfer_router.py#L264) | [PB/main.py:783](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L783) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/evolution/variants` | [K/backend/evolution_router.py:79](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L79) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | [PF/api.ts:428](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L428) | WIRED |
| GET `/api/evolution/history` | [K/backend/evolution_router.py:108](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L108) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | [PF/api.ts:449](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L449) | WIRED |
| GET `/api/evolution/promoted` | [K/backend/evolution_router.py:124](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L124) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | [PF/api.ts:453](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L453) | WIRED |
| GET `/api/evolution/summary` | [K/backend/evolution_router.py:141](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L141) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/evolution/record-outcome` | [K/backend/evolution_router.py:169](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L169) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/evolution/check-promotion` | [K/backend/evolution_router.py:192](../../../copilot-sdk/copilot_sdk/backend/evolution_router.py#L192) | [PB/main.py:784](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L784) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/conservation/status` | [K/backend/conservation_router.py:42](../../../copilot-sdk/copilot_sdk/backend/conservation_router.py#L42) | [PB/main.py:796](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L796) | [PF/api.ts:471](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L471) | WIRED |
| POST `/api/conservation/what-if` | [K/backend/conservation_router.py:56](../../../copilot-sdk/copilot_sdk/backend/conservation_router.py#L56) | [PB/main.py:796](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L796) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history` | [K/backend/self_computation_router.py:107](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L107) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | [PF/api.ts:656](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L656) | WIRED |
| GET `/api/self/centroid-timeline` | [K/backend/self_computation_router.py:154](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L154) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/regime-reinit` | [K/backend/self_computation_router.py:163](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L163) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/evolution/summary` | [K/backend/self_computation_router.py:181](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L181) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/diagnostics` | [K/backend/self_computation_router.py:189](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L189) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/self/centroid-history/{checkpoint_id}/counterfactual` | [K/backend/self_computation_router.py:221](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L221) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history/{checkpoint_id}/lineage` | [K/backend/self_computation_router.py:337](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L337) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/centroid-history/{checkpoint_id}/replay` | [K/backend/self_computation_router.py:348](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L348) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/replay-score` | [K/backend/self_computation_router.py:368](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L368) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/decisions/{decision_id}/checkpoints` | [K/backend/self_computation_router.py:413](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L413) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/accuracy-by-category` | [K/backend/self_computation_router.py:422](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L422) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | [PF/api.ts:664](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L664) | WIRED |
| GET `/api/self/accuracy-alerts` | [K/backend/self_computation_router.py:457](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L457) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/trust-traps` | [K/backend/self_computation_router.py:465](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L465) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| POST `/api/self/rollback` | [K/backend/self_computation_router.py:471](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L471) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/decisions` | [K/backend/self_computation_router.py:481](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L481) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | [PF/api.ts:673](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L673) | WIRED |
| GET `/api/self/rule-genealogy` | [K/backend/self_computation_router.py:508](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L508) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/rule-lifecycle/{rule_id}` | [K/backend/self_computation_router.py:514](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L514) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/self/audit-trail` | [K/backend/self_computation_router.py:525](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L525) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | [PF/api.ts:677](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L677) | WIRED |
| GET `/api/self/decision-flow` | [K/backend/self_computation_router.py:556](../../../copilot-sdk/copilot_sdk/backend/self_computation_router.py#L556) | [PB/main.py:803](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L803) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/context/today-summary` | [PB/context_router.py:242](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L242) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:174](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L174) | WIRED |
| GET `/api/context/items` | [PB/context_router.py:252](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L252) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:166](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L166) | WIRED |
| GET `/api/context/waste-history/{item}` | [PB/context_router.py:269](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L269) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:249](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L249) | WIRED |
| GET `/api/context/weather` | [PB/context_router.py:277](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L277) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:178](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L178) | WIRED |
| POST `/api/context/order-metadata` | [PB/context_router.py:282](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L282) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:424](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L424) | WIRED |
| GET `/api/context/order-metadata` | [PB/context_router.py:298](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L298) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/context/analytics` | [PB/context_router.py:303](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L303) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:162](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L162) | WIRED |
| GET `/api/context/similar` | [PB/context_router.py:321](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L321) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:689](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L689) | WIRED |
| GET `/api/context/item/{name}/profile` | [PB/context_router.py:375](../../../copilot-sdk/apps/purchasing/backend/app/context_router.py#L375) | [PB/main.py:811](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L811) | [PF/api.ts:409](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L409) | WIRED |
| GET `/api/dashboard/orders` | [PB/dashboard_router.py:36](../../../copilot-sdk/apps/purchasing/backend/app/dashboard_router.py#L36) | [PB/main.py:812](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L812) | [PF/api.ts:418](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L418) | WIRED |
| GET `/api/inventory/summary` | [PB/inventory_router.py:120](../../../copilot-sdk/apps/purchasing/backend/app/inventory_router.py#L120) | [PB/main.py:813](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L813) | [PF/api.ts:170](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L170) | WIRED |
| GET `/api/purchasing/evidence/summary` | [PB/routers/evidence.py:24](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L24) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/evidence/decisions` | [PB/routers/evidence.py:53](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L53) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/evidence/audit-trail` | [PB/routers/evidence.py:70](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L70) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/evidence/conservation-proof` | [PB/routers/evidence.py:96](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L96) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/health` | [PB/routers/evidence.py:125](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L125) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/status` | [PB/routers/evidence.py:141](../../../copilot-sdk/apps/purchasing/backend/app/routers/evidence.py#L141) | [PB/main.py:814](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L814) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/learning/hero` | [PB/routers/learning_beats.py:67](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L67) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/diagnostics/signal-gate` | [PB/routers/learning_beats.py:77](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L77) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/evidence/proof-ledger` | [PB/routers/learning_beats.py:92](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L92) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/learning/self-pause` | [PB/routers/learning_beats.py:107](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L107) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/diagnostics/ramp` | [PB/routers/learning_beats.py:120](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L120) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/competence/ramp` | [PB/routers/learning_beats.py:121](../../../copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py#L121) | [PB/main.py:815](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L815) | [PF/api.ts:829](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L829) | WIRED; see PUR-2 |
| GET `/api/purchasing/iks` | [PB/routers/iks.py:22](../../../copilot-sdk/apps/purchasing/backend/app/routers/iks.py#L22) | [PB/main.py:816](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L816) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/suppliers/{supplier_id}/scorecard` | [PB/routers/iks.py:38](../../../copilot-sdk/apps/purchasing/backend/app/routers/iks.py#L38) | [PB/main.py:816](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L816) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| POST `/api/purchasing/match` | [PB/routers/match.py:58](../../../copilot-sdk/apps/purchasing/backend/app/routers/match.py#L58) | [PB/main.py:817](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L817) | None found | MISSING_UI / P1: PUR-3 |
| GET `/api/purchasing/match/queue` | [PB/routers/match.py:159](../../../copilot-sdk/apps/purchasing/backend/app/routers/match.py#L159) | [PB/main.py:817](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L817) | [PF/api.ts:637](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L637) | WIRED |
| GET `/api/purchasing/auto-order/status` | [PB/routers/auto_order_router.py:35](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L35) | [PB/main.py:818](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L818) | [PF/api.ts:611](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L611) | WIRED |
| POST `/api/purchasing/auto-order/enable` | [PB/routers/auto_order_router.py:44](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L44) | [PB/main.py:818](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L818) | [PF/api.ts:615](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L615) | WIRED |
| POST `/api/purchasing/auto-order/disable` | [PB/routers/auto_order_router.py:49](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L49) | [PB/main.py:818](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L818) | [PF/api.ts:619](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L619) | WIRED |
| GET `/api/purchasing/auto-order/audit` | [PB/routers/auto_order_router.py:53](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L53) | [PB/main.py:818](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L818) | [PF/api.ts:623](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L623) | WIRED |
| POST `/api/purchasing/auto-order/evaluate` | [PB/routers/auto_order_router.py:57](../../../copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py#L57) | [PB/main.py:818](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L818) | None found | MISSING_UI / P1: PUR-4 |
| GET `/api/purchasing/alerts` | [PB/routers/alert_router.py:22](../../../copilot-sdk/apps/purchasing/backend/app/routers/alert_router.py#L22) | [PB/main.py:819](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L819) | [PF/api.ts:779](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L779) | WIRED |
| POST `/api/purchasing/chain/validate` | [PB/routers/chain_router.py:58](../../../copilot-sdk/apps/purchasing/backend/app/routers/chain_router.py#L58) | [PB/main.py:826](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L826) | [PF/api.ts:369](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L369) | WIRED; see PUR-7 |
| POST `/api/purchasing/chain/sdk-transfer` | [PB/routers/chain_router.py:64](../../../copilot-sdk/apps/purchasing/backend/app/routers/chain_router.py#L64) | [PB/main.py:826](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L826) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/purchasing/chain/status` | [PB/routers/chain_router.py:70](../../../copilot-sdk/apps/purchasing/backend/app/routers/chain_router.py#L70) | [PB/main.py:826](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L826) | [PF/api.ts:377](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L377) | WIRED; see PUR-7 |
| GET `/api/purchasing/delivery/today` | [PB/routers/delivery_router.py:17](../../../copilot-sdk/apps/purchasing/backend/app/routers/delivery_router.py#L17) | [PB/main.py:827](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L827) | [PF/api.ts:397](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L397) | WIRED |
| GET `/api/purchasing/delivery/week` | [PB/routers/delivery_router.py:22](../../../copilot-sdk/apps/purchasing/backend/app/routers/delivery_router.py#L22) | [PB/main.py:827](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L827) | [PF/api.ts:401](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L401) | WIRED |
| GET `/api/purchasing/delivery/consolidation` | [PB/routers/delivery_router.py:26](../../../copilot-sdk/apps/purchasing/backend/app/routers/delivery_router.py#L26) | [PB/main.py:827](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L827) | [PF/api.ts:405](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L405) | WIRED |
| GET `/api/purchasing/discovery/insights` | [PB/routers/discovery_router.py:32](../../../copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py#L32) | [PB/main.py:829](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L829) | [PF/api.ts:763](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L763) | WIRED; see PUR-7 |
| GET `/api/purchasing/discovery/digest` | [PB/routers/discovery_router.py:44](../../../copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py#L44) | [PB/main.py:829](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L829) | [PF/api.ts:767](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L767) | WIRED; see PUR-7 |
| GET `/api/purchasing/economic/model` | [PB/routers/economic_router.py:15](../../../copilot-sdk/apps/purchasing/backend/app/routers/economic_router.py#L15) | [PB/main.py:830](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L830) | [PF/api.ts:803](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L803) | WIRED |
| GET `/api/purchasing/economic/roi-summary` | [PB/routers/economic_router.py:25](../../../copilot-sdk/apps/purchasing/backend/app/routers/economic_router.py#L25) | [PB/main.py:830](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L830) | [PF/components/PurchasingBeatPanels.tsx:48](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx#L48) | WIRED; see PUR-2 |
| GET `/api/purchasing/events/plan` | [PB/routers/event_router.py:22](../../../copilot-sdk/apps/purchasing/backend/app/routers/event_router.py#L22) | [PB/main.py:831](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L831) | [PF/api.ts:345](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L345) | WIRED |
| GET `/api/purchasing/events/history` | [PB/routers/event_router.py:27](../../../copilot-sdk/apps/purchasing/backend/app/routers/event_router.py#L27) | [PB/main.py:831](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L831) | [PF/api.ts:349](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L349) | WIRED |
| POST `/api/purchasing/events/record` | [PB/routers/event_router.py:31](../../../copilot-sdk/apps/purchasing/backend/app/routers/event_router.py#L31) | [PB/main.py:831](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L831) | None found | MISSING_UI / P2: PUR-6 |
| GET `/api/purchasing/pos/today` | [PB/routers/pos_router.py:66](../../../copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py#L66) | [PB/main.py:832](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L832) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/pos/profile` | [PB/routers/pos_router.py:97](../../../copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py#L97) | [PB/main.py:832](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L832) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/qbo/vendors` | [PB/routers/qbo_router.py:53](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L53) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | [PF/api.ts:475](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L475) | WIRED |
| GET `/api/purchasing/qbo/bills` | [PB/routers/qbo_router.py:57](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L57) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | [PF/api.ts:479](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L479) | WIRED |
| GET `/api/purchasing/qbo/purchase-orders` | [PB/routers/qbo_router.py:61](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L61) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/qbo/payments` | [PB/routers/qbo_router.py:65](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L65) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/qbo/price-history/{vendor_id}/{item_name}` | [PB/routers/qbo_router.py:69](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L69) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | [PF/api.ts:488](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L488) | WIRED |
| GET `/api/purchasing/qbo/lead-times/{vendor_id}` | [PB/routers/qbo_router.py:73](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L73) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | [PF/api.ts:493](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L493) | WIRED |
| GET `/api/purchasing/qbo/status` | [PB/routers/qbo_router.py:77](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L77) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | [PF/api.ts:483](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L483) | WIRED |
| GET `/api/purchasing/qbo/profile` | [PB/routers/qbo_router.py:94](../../../copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py#L94) | [PB/main.py:833](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L833) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/signals/supplier/{supplier_name}` | [PB/routers/signal_router.py:15](../../../copilot-sdk/apps/purchasing/backend/app/routers/signal_router.py#L15) | [PB/main.py:834](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L834) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/signals/stats` | [PB/routers/signal_router.py:19](../../../copilot-sdk/apps/purchasing/backend/app/routers/signal_router.py#L19) | [PB/main.py:834](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L834) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/supplier/{supplier_id}/scorecard` | [PB/routers/scorecard_router.py:41](../../../copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py#L41) | [PB/main.py:835](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L835) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/suppliers/scorecards` | [PB/routers/scorecard_router.py:48](../../../copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py#L48) | [PB/main.py:835](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L835) | [PF/api.ts:588](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L588) | WIRED |
| GET `/api/purchasing/iks/summary` | [PB/routers/scorecard_router.py:52](../../../copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py#L52) | [PB/main.py:835](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L835) | [PF/api.ts:583](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L583) | WIRED |
| GET `/api/purchasing/spend/summary` | [PB/routers/spend_router.py:53](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L53) | [PB/main.py:839](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L839) | [PF/api.ts:497](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L497) | WIRED |
| GET `/api/purchasing/spend/by-category` | [PB/routers/spend_router.py:57](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L57) | [PB/main.py:839](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L839) | [PF/api.ts:501](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L501) | WIRED |
| GET `/api/purchasing/spend/by-supplier` | [PB/routers/spend_router.py:61](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L61) | [PB/main.py:839](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L839) | [PF/api.ts:509](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L509) | WIRED |
| GET `/api/purchasing/spend/alerts` | [PB/routers/spend_router.py:65](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L65) | [PB/main.py:839](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L839) | [PF/api.ts:505](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L505) | WIRED |
| GET `/api/purchasing/spend/cost-per-cover` | [PB/routers/spend_router.py:69](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L69) | [PB/main.py:839](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L839) | [PF/api.ts:513](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L513) | WIRED |
| GET `/api/purchasing/commodity/prices/{category}` | [PB/routers/commodity_router.py:21](../../../copilot-sdk/apps/purchasing/backend/app/routers/commodity_router.py#L21) | [PB/main.py:840](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L840) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/commodity/index/{category}` | [PB/routers/commodity_router.py:27](../../../copilot-sdk/apps/purchasing/backend/app/routers/commodity_router.py#L27) | [PB/main.py:840](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L840) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/commodity/indices` | [PB/routers/commodity_router.py:33](../../../copilot-sdk/apps/purchasing/backend/app/routers/commodity_router.py#L33) | [PB/main.py:840](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L840) | [PF/api.ts:517](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L517) | WIRED |
| GET `/api/purchasing/commodity/status` | [PB/routers/commodity_router.py:37](../../../copilot-sdk/apps/purchasing/backend/app/routers/commodity_router.py#L37) | [PB/main.py:840](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L840) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/menu/analysis` | [PB/routers/menu_router.py:16](../../../copilot-sdk/apps/purchasing/backend/app/routers/menu_router.py#L16) | [PB/main.py:841](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L841) | [PF/api.ts:320](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L320) | WIRED |
| GET `/api/purchasing/menu/alerts` | [PB/routers/menu_router.py:24](../../../copilot-sdk/apps/purchasing/backend/app/routers/menu_router.py#L24) | [PB/main.py:841](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L841) | [PF/api.ts:324](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L324) | WIRED |
| GET `/api/purchasing/menu/summary` | [PB/routers/menu_router.py:32](../../../copilot-sdk/apps/purchasing/backend/app/routers/menu_router.py#L32) | [PB/main.py:841](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L841) | [PF/api.ts:328](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L328) | WIRED |
| GET `/api/purchasing/multi-unit/dashboard` | [PB/routers/multi_unit_router.py:14](../../../copilot-sdk/apps/purchasing/backend/app/routers/multi_unit_router.py#L14) | [PB/main.py:842](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L842) | [PF/api.ts:844](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L844) | WIRED |
| GET `/api/purchasing/multi-unit/compare` | [PB/routers/multi_unit_router.py:18](../../../copilot-sdk/apps/purchasing/backend/app/routers/multi_unit_router.py#L18) | [PB/main.py:842](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L842) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/multi-unit/transfer-opportunities` | [PB/routers/multi_unit_router.py:22](../../../copilot-sdk/apps/purchasing/backend/app/routers/multi_unit_router.py#L22) | [PB/main.py:842](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L842) | None found | NO_UI: SDK/operator lifecycle surface; product UI disposition needed |
| GET `/api/purchasing/par/recommendations` | [PB/routers/par_router.py:63](../../../copilot-sdk/apps/purchasing/backend/app/routers/par_router.py#L63) | [PB/main.py:843](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L843) | [PF/api.ts:539](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L539) | WIRED |
| GET `/api/purchasing/par/recommendations/{category}` | [PB/routers/par_router.py:70](../../../copilot-sdk/apps/purchasing/backend/app/routers/par_router.py#L70) | [PB/main.py:843](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L843) | [PF/api.ts:535](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L535) | WIRED |
| GET `/api/purchasing/par/status` | [PB/routers/par_router.py:77](../../../copilot-sdk/apps/purchasing/backend/app/routers/par_router.py#L77) | [PB/main.py:843](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L843) | [PF/api.ts:544](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L544) | WIRED |
| GET `/api/purchasing/cohort-status` | [PB/routers/cohort_status_router.py:19](../../../copilot-sdk/apps/purchasing/backend/app/routers/cohort_status_router.py#L19) | [PB/main.py:844](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L844) | [PF/api.ts:579](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L579) | WIRED |
| GET `/api/purchasing/queue` | [PB/routers/queue.py:34](../../../copilot-sdk/apps/purchasing/backend/app/routers/queue.py#L34) | [PB/main.py:849](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L849) | [PF/api.ts:641](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L641) | WIRED |
| GET `/api/purchasing/queue/{order_id}` | [PB/routers/queue.py:51](../../../copilot-sdk/apps/purchasing/backend/app/routers/queue.py#L51) | [PB/main.py:849](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L849) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/verify/reason-codes` | [PB/routers/verify_router.py:64](../../../copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py#L64) | [PB/main.py:855](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L855) | [PF/api.ts:716](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L716) | WIRED |
| POST `/api/purchasing/verify` | [PB/routers/verify_router.py:74](../../../copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py#L74) | [PB/main.py:855](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L855) | [PF/api.ts:725](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L725) | WIRED |
| GET `/api/purchasing/proof-ledger` | [PB/routers/purchasing_control.py:23](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L23) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | [PF/api.ts:817](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L817); [PF/components/PurchasingProofPanel.tsx:25](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L25) | WIRED; see PUR-1 |
| GET `/api/purchasing/handoff-pack` | [PB/routers/purchasing_control.py:27](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L27) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | MISSING_UI / P2: PUR-8 |
| GET `/api/purchasing/day-0-readiness` | [PB/routers/purchasing_control.py:31](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L31) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | [PF/api.ts:821](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L821); [PF/components/PurchasingProofPanel.tsx:26](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L26) | WIRED; see PUR-2 |
| GET `/api/purchasing/legal-exposure` | [PB/routers/purchasing_control.py:35](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L35) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | [PF/components/PurchasingProofPanel.tsx:27](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L27) | WIRED; see PUR-1 |
| GET `/api/purchasing/frozen-twin` | [PB/routers/purchasing_control.py:39](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L39) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | [PF/api.ts:825](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L825); [PF/components/PurchasingProofPanel.tsx:28](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L28) | WIRED |
| POST `/api/purchasing/frozen-twin/freeze` | [PB/routers/purchasing_control.py:43](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L43) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | MISSING_UI / P1: PUR-5 |
| GET `/api/purchasing/frozen-twin/comparison` | [PB/routers/purchasing_control.py:50](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L50) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | MISSING_UI / P1: PUR-5 |
| POST `/api/purchasing/proof-ledger/outcome` | [PB/routers/purchasing_control.py:57](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L57) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | NO_UI: alternate outcome-ingestion API; verify workflow is wired |
| GET `/api/purchasing/promotion` | [PB/routers/purchasing_control.py:64](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L64) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | MISSING_UI / P2: PUR-9 |
| POST `/api/purchasing/promotion/{decision_class}/advance` | [PB/routers/purchasing_control.py:68](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L68) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | MISSING_UI / P2: PUR-9 |
| GET `/api/purchasing/discovery-gate` | [PB/routers/purchasing_control.py:83](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L83) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | NO_UI: implemented HTTP surface; external/product purpose requires owner disposition |
| GET `/api/purchasing/yield-quote-audit` | [PB/routers/purchasing_control.py:90](../../../copilot-sdk/apps/purchasing/backend/app/routers/purchasing_control.py#L90) | [PB/main.py:856](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L856) | None found | NO_UI: explicit NOT_YET placeholder; no implemented measurements/UI |
| GET `/api/purchasing/situation` | [PB/routers/regime_router.py:18](../../../copilot-sdk/apps/purchasing/backend/app/routers/regime_router.py#L18) | [PB/main.py:857](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L857) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/trust` | [PB/routers/trust.py:21](../../../copilot-sdk/apps/purchasing/backend/app/routers/trust.py#L21) | [PB/main.py:858](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L858) | None found | NO_UI: connector/detail/alternate projection; see native consumer inventory |
| GET `/api/purchasing/trust-weights` | [PB/routers/trust_router.py:34](../../../copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py#L34) | [PB/main.py:859](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L859) | [PF/api.ts:599](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L599) | WIRED |
| GET `/api/purchasing/trust-weights/expected` | [PB/routers/trust_router.py:55](../../../copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py#L55) | [PB/main.py:859](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L859) | [PF/api.ts:603](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L603) | WIRED |
| GET `/api/purchasing/trust-weights/insights` | [PB/routers/trust_router.py:63](../../../copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py#L63) | [PB/main.py:859](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L859) | [PF/api.ts:607](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L607) | WIRED |
| GET `/api/purchasing/graph/status` | [PB/graph_status.py:470](../../../copilot-sdk/apps/purchasing/backend/app/graph_status.py#L470) | [PB/main.py:860](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L860) | None found | NO_UI: diagnostics/status API; not evidence of a missing panel |
| GET `/api/purchasing/report/weekly` | [K/backend/report_router.py:62](../../../copilot-sdk/copilot_sdk/backend/report_router.py#L62) | [PB/main.py:861](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L861) | [PF/components/WeeklyReportPanel.tsx:54](../../../copilot-sdk/apps/purchasing/frontend/src/components/WeeklyReportPanel.tsx#L54) | WIRED |

### Purchasing — frontend call inventory

| Method / normalized path | Call site | Function/component |
|---|---|---|
| GET `/api/context/analytics` | [PF/api.ts:162](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L162) | getAnalytics |
| GET `/api/context/items` | [PF/api.ts:166](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L166) | getItems |
| GET `/api/inventory/summary` | [PF/api.ts:170](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L170) | getInventorySummary |
| GET `/api/context/today-summary` | [PF/api.ts:174](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L174) | getTodaySummary |
| GET `/api/context/weather` | [PF/api.ts:178](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L178) | getWeather |
| GET `/api/context/waste-history/{}` | [PF/api.ts:249](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L249) | getWasteHistory |
| GET `/api/purchasing/waste/analysis` | [PF/api.ts:271](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L271) | getWasteAnalysis |
| GET `/api/purchasing/waste/summary` | [PF/api.ts:275](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L275) | getWasteSummary |
| GET `/api/purchasing/menu/analysis` | [PF/api.ts:320](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L320) | getMenuAnalysis |
| GET `/api/purchasing/menu/alerts` | [PF/api.ts:324](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L324) | getMenuAlerts |
| GET `/api/purchasing/menu/summary` | [PF/api.ts:328](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L328) | getMenuSummary |
| GET `/api/purchasing/events/plan` | [PF/api.ts:345](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L345) | fetchEventPlan |
| GET `/api/purchasing/events/history` | [PF/api.ts:349](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L349) | fetchEventHistory |
| POST `/api/purchasing/chain/validate` | [PF/api.ts:369](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L369) | validateChainTransfer |
| POST `/api/purchasing/chain/transfer` | [PF/api.ts:373](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L373) | executeChainTransfer |
| GET `/api/purchasing/chain/status` | [PF/api.ts:377](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L377) | fetchChainStatus |
| GET `/api/purchasing/delivery/today` | [PF/api.ts:397](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L397) | fetchDeliveryToday |
| GET `/api/purchasing/delivery/week` | [PF/api.ts:401](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L401) | fetchDeliveryWeek |
| GET `/api/purchasing/delivery/consolidation` | [PF/api.ts:405](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L405) | fetchConsolidationSuggestions |
| GET `/api/context/item/{}/profile` | [PF/api.ts:409](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L409) | getItemProfile |
| GET `/api/dashboard/orders` | [PF/api.ts:418](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L418) | getDashboardOrders |
| POST `/api/context/order-metadata` | [PF/api.ts:424](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L424) | saveOrderMetadata |
| GET `/api/evolution/variants` | [PF/api.ts:428](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L428) | getEvolutionVariants |
| GET `/api/evolution/history` | [PF/api.ts:449](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L449) | getEvolutionHistory |
| GET `/api/evolution/promoted` | [PF/api.ts:453](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L453) | getPromotedEvolutionRules |
| GET `/api/history` | [PF/api.ts:458](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L458) | getHistory |
| GET `/api/fingerprint` | [PF/api.ts:463](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L463) | getFingerprint |
| GET `/api/trajectory` | [PF/api.ts:467](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L467) | getTrajectory |
| GET `/api/conservation/status` | [PF/api.ts:471](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L471) | getConservationStatus |
| GET `/api/purchasing/qbo/vendors` | [PF/api.ts:475](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L475) | getQBOVendors |
| GET `/api/purchasing/qbo/bills` | [PF/api.ts:479](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L479) | getQBOBills |
| GET `/api/purchasing/qbo/status` | [PF/api.ts:483](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L483) | getQBOStatus |
| GET `/api/purchasing/qbo/price-history/{}/{}` | [PF/api.ts:488](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L488) | getQBOPriceHistory |
| GET `/api/purchasing/qbo/lead-times/{}` | [PF/api.ts:493](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L493) | getQBOLeadTimes |
| GET `/api/purchasing/spend/summary` | [PF/api.ts:497](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L497) | getSpendSummary |
| GET `/api/purchasing/spend/by-category` | [PF/api.ts:501](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L501) | getSpendByCategory |
| GET `/api/purchasing/spend/alerts` | [PF/api.ts:505](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L505) | getSpendAlerts |
| GET `/api/purchasing/spend/by-supplier` | [PF/api.ts:509](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L509) | getSpendBySupplier |
| GET `/api/purchasing/spend/cost-per-cover` | [PF/api.ts:513](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L513) | getSpendCostPerCover |
| GET `/api/purchasing/commodity/indices` | [PF/api.ts:517](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L517) | getCommodityIndices |
| GET `/api/purchasing/par/recommendations/{}` | [PF/api.ts:535](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L535) | getParRecommendations |
| GET `/api/purchasing/par/recommendations` | [PF/api.ts:539](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L539) | getParRecommendations |
| GET `/api/purchasing/par/status` | [PF/api.ts:544](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L544) | getParStatus |
| GET `/api/purchasing/cohort-status` | [PF/api.ts:579](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L579) | getCohortStatus |
| GET `/api/purchasing/iks/summary` | [PF/api.ts:583](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L583) | getIKSSummary |
| GET `/api/purchasing/suppliers/scorecards` | [PF/api.ts:588](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L588) | getSupplierScorecards |
| GET `/api/purchasing/trust-weights` | [PF/api.ts:599](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L599) | getTrustWeights |
| GET `/api/purchasing/trust-weights/expected` | [PF/api.ts:603](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L603) | getExpectedTrustWeights |
| GET `/api/purchasing/trust-weights/insights` | [PF/api.ts:607](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L607) | getTrustInsights |
| GET `/api/purchasing/auto-order/status` | [PF/api.ts:611](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L611) | getAutoOrderStatus |
| POST `/api/purchasing/auto-order/enable` | [PF/api.ts:615](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L615) | enableAutoOrder |
| POST `/api/purchasing/auto-order/disable` | [PF/api.ts:619](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L619) | disableAutoOrder |
| GET `/api/purchasing/auto-order/audit` | [PF/api.ts:623](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L623) | getAutoOrderAudit |
| GET `/api/purchasing/match/queue` | [PF/api.ts:637](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L637) | getMatchQueue |
| GET `/api/purchasing/queue` | [PF/api.ts:641](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L641) | getOrderQueue |
| GET `/api/self/accuracy-by-category` | [PF/api.ts:664](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L664) | fetchAccuracyByCategory |
| GET `/api/self/decisions` | [PF/api.ts:673](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L673) | fetchDecisions |
| GET `/api/self/audit-trail` | [PF/api.ts:677](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L677) | fetchAuditTrail |
| GET `/api/context/similar` | [PF/api.ts:689](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L689) | getSimilarOrders |
| POST `/api/score` | [PF/api.ts:703](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L703) | scoreOrder |
| GET `/api/purchasing/verify/reason-codes` | [PF/api.ts:716](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L716) | getVerifyReasonCodes |
| POST `/api/purchasing/verify` | [PF/api.ts:725](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L725) | verifyOrder |
| GET `/api/purchasing/par/predict-week` | [PF/api.ts:751](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L751) | fetchPredictiveParWeek |
| GET `/api/purchasing/discovery/insights` | [PF/api.ts:763](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L763) | fetchDiscoveryInsights |
| GET `/api/purchasing/discovery/digest` | [PF/api.ts:767](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L767) | fetchDiscoveryDigest |
| GET `/api/purchasing/alerts` | [PF/api.ts:779](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L779) | fetchAlerts |
| GET `/api/purchasing/economic/model` | [PF/api.ts:803](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L803) | fetchEconomicModel |
| GET `/api/purchasing/proof-ledger` | [PF/api.ts:817](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L817) | fetchProofLedger |
| GET `/api/purchasing/day-0-readiness` | [PF/api.ts:821](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L821) | fetchDayZeroReadiness |
| GET `/api/purchasing/frozen-twin` | [PF/api.ts:825](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L825) | fetchFrozenTwin |
| GET `/api/purchasing/competence/ramp` | [PF/api.ts:829](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L829) | fetchKitchenRamp |
| GET `/api/purchasing/multi-unit/dashboard` | [PF/api.ts:844](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L844) | fetchGroupDashboard |
| GET `/api/fingerprint` | [K/frontend/DataTrustBadge.tsx:35](../../../copilot-sdk/copilot_sdk/frontend/DataTrustBadge.tsx#L35) | DataTrustBadge |
| GET `/api/{}/measurement-state` | [K/frontend/components/DayZeroCard.tsx:62](../../../copilot-sdk/copilot_sdk/frontend/components/DayZeroCard.tsx#L62) | DayZeroCard |
| GET `/api/transfer/status` | [K/frontend/TransferBadge.tsx:23](../../../copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx#L23) | TransferBadge |
| GET `/api/purchasing/economic/roi-summary` | [PF/components/PurchasingBeatPanels.tsx:48](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx#L48) | fetchRoiSummary |
| GET `/api/purchasing/audit/pack` | [PF/components/AuditExportPanel.tsx:25](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L25) | load |
| GET `/api/purchasing/audit/export/json` | [PF/components/AuditExportPanel.tsx:80](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L80) | AuditExportPanel |
| GET `/api/purchasing/audit/export/csv` | [PF/components/AuditExportPanel.tsx:81](../../../copilot-sdk/apps/purchasing/frontend/src/components/AuditExportPanel.tsx#L81) | AuditExportPanel |
| POST `/api/purchasing/demo/chain-seed` | [PF/components/ChainTransferCard.tsx:50](../../../copilot-sdk/apps/purchasing/frontend/src/components/ChainTransferCard.tsx#L50) | transferNow |
| POST `/api/purchasing/chain/transfer` | [PF/components/ChainTransferCard.tsx:51](../../../copilot-sdk/apps/purchasing/frontend/src/components/ChainTransferCard.tsx#L51) | transferNow |
| GET `/api/purchasing/disruption/status` | [PF/components/DisruptionRecoveryPanel.tsx:32](../../../copilot-sdk/apps/purchasing/frontend/src/components/DisruptionRecoveryPanel.tsx#L32) | load |
| GET `/api/purchasing/disruption/history` | [PF/components/DisruptionRecoveryPanel.tsx:33](../../../copilot-sdk/apps/purchasing/frontend/src/components/DisruptionRecoveryPanel.tsx#L33) | load |
| GET `/api/purchasing/payment/timing` | [PF/components/PaymentTimingPanel.tsx:36](../../../copilot-sdk/apps/purchasing/frontend/src/components/PaymentTimingPanel.tsx#L36) | load |
| GET `/api/purchasing/payment/summary` | [PF/components/PaymentTimingPanel.tsx:37](../../../copilot-sdk/apps/purchasing/frontend/src/components/PaymentTimingPanel.tsx#L37) | load |
| GET `/api/purchasing/proof-ledger` | [PF/components/PurchasingProofPanel.tsx:25](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L25) | PurchasingProofPanel |
| GET `/api/purchasing/day-0-readiness` | [PF/components/PurchasingProofPanel.tsx:26](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L26) | PurchasingProofPanel |
| GET `/api/purchasing/legal-exposure` | [PF/components/PurchasingProofPanel.tsx:27](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L27) | PurchasingProofPanel |
| GET `/api/purchasing/frozen-twin` | [PF/components/PurchasingProofPanel.tsx:28](../../../copilot-sdk/apps/purchasing/frontend/src/components/PurchasingProofPanel.tsx#L28) | PurchasingProofPanel |
| GET `/api/purchasing/report/weekly` | [PF/components/WeeklyReportPanel.tsx:54](../../../copilot-sdk/apps/purchasing/frontend/src/components/WeeklyReportPanel.tsx#L54) | WeeklyReportPanel |
| GET `/api/self/centroid-history` | [PF/api.ts:656](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L656) | fetchLearningHistory (exported as fetchCentroidHistory) |

**Unused API wrappers (not counted as consumers):**

| Method / normalized path | Wrapper declaration/call | Unused function |
|---|---|---|
| POST `/api/purchasing/events/record` | [PF/api.ts:357](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L357) | recordEventOutcome |
| GET `/api/context/order-metadata` | [PF/api.ts:413](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L413) | getOrderMetadata |
| GET `/api/purchasing/commodity/prices/{}` | [PF/api.ts:521](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L521) | getCommodityPrices |
| GET `/api/purchasing/commodity/status` | [PF/api.ts:525](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L525) | getCommodityStatus |
| GET `/api/purchasing/supplier/{}/scorecard` | [PF/api.ts:594](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L594) | getSupplierScorecard |
| POST `/api/purchasing/auto-order/evaluate` | [PF/api.ts:633](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L633) | evaluateAutoOrder |
| POST `/api/purchasing/match` | [PF/api.ts:649](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L649) | postMatch |
| POST `/api/learn` | [PF/api.ts:712](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L712) | learnOrder |
| GET `/api/purchasing/par/predict` | [PF/api.ts:747](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L747) | fetchPredictivePar |
| GET `/api/purchasing/alerts` | [PF/api.ts:783](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L783) | fetchAlertsBySeverity |
| GET `/api/purchasing/economic/roi-summary` | [PF/api.ts:807](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L807) | fetchROISummary |
| GET `/api/purchasing/multi-unit/compare` | [PF/api.ts:849](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L849) | fetchLocationComparison |
| GET `/api/purchasing/multi-unit/transfer-opportunities` | [PF/api.ts:855](../../../copilot-sdk/apps/purchasing/frontend/src/api.ts#L855) | fetchTransferOpportunities |

### Part B — Trading and Purchasing patch/mock findings

#### TP-B1 — BLOCKING ambient test-runtime hooks change configuration and available product behavior (P1)

These are **nine production test-awareness sites**, grouped below. They are not nine explicit monkeypatch calls and are not added to the direct-monkeypatch-hook count. Pytest supplies the ambient variable/module automatically; **no test was found directly monkeypatching these helper functions**. This extends the original inventory beyond compatibility aliases to an equally important test/production split.

| Copilot | Production hook (file:line) | Behavior hidden by the test context | Injection replacement |
|---|---|---|---|
| Trading | [main.py:107](../../../copilot-sdk/apps/trading/backend/app/main.py#L107) | `PYTEST_CURRENT_TEST` or imported `pytest` selects profile `test`. The value flows to graph configuration, scorer and variant-store creation at lines 143,370,411. | Accept an explicit runtime/GraphConfig object in the app factory; test fixtures must request isolated test settings explicitly. |
| Trading | [cli_sdk.py:33](../../../copilot-sdk/apps/trading/backend/app/cli_sdk.py#L33) | The CLI selects test profile before considering ordinary DSN/development configuration. | Pass explicit CLI runtime configuration through command construction, keeping the real scorer/store implementations. |
| Trading | [context_router.py:43](../../../copilot-sdk/apps/trading/backend/app/context_router.py#L43) | An unspecified demo flag becomes enabled solely because pytest is running; market/ticker/portfolio context takes different availability/fallback branches (lines 303,323,336,349,367). | Inject one immutable DemoSettings value into the context router/provider. |
| Purchasing | [main.py:118](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L118) | Selects test profile implicitly; graph/scorer/variant construction uses it at lines 190,507,522. | Accept explicit runtime/GraphConfig in create_app; migrate fixture construction together. |
| Purchasing | [main.py:129](../../../copilot-sdk/apps/purchasing/backend/app/main.py#L129) | Pytest enables demo routes when flags are absent, masking PUR-7. | Inject explicit DemoSettings and test the assembled app with both states. |
| Purchasing | [routers/discovery_router.py:16](../../../copilot-sdk/apps/purchasing/backend/app/routers/discovery_router.py#L16) | Discovery permits its demo fixture path under pytest even without an explicit demo setting. | Reuse the same injected DemoSettings in the router. |
| Purchasing | [routers/pos_router.py:24](../../../copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py#L24) | POS fixture/fallback availability depends on pytest; the route guards are at lines 46,70,101. | Inject demo policy and an explicit POS connector. |
| Purchasing | [routers/spend_router.py:23](../../../copilot-sdk/apps/purchasing/backend/app/routers/spend_router.py#L23) | Spend permits sample/default-connector behavior in the pytest context (lines 42,139). | Inject the shared demo policy plus the connector boundary. |
| Purchasing | [services/commodity_data_provider.py:23](../../../copilot-sdk/apps/purchasing/backend/app/services/commodity_data_provider.py#L23) | Fixture/mock fallback restrictions differ under pytest (lines 112,133,143,156). | Pass explicit provider policy and external source dependencies. |

**Test users and non-test impact:** the factory/fixture consumer index below lists all direct `create_app` and `client`-fixture entry points found in these two test trees. Trading CLI coverage imports the command interface in [test_cli_sdk.py:21](../../../copilot-sdk/apps/trading/backend/tests/test_cli_sdk.py#L21). Purchasing's concrete masking example is [test_cross_discovery.py:90](../../../copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py#L90) and [:97](../../../copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py#L97): create_app is called without a demo flag, yet 200/demo responses are asserted. Additional direct demo-provider tests are in `test_pos_router.py`, `test_spend_dashboard.py`, `test_commodity.py` and `test_commodity_provider.py`; they need explicit policy when migrating. The index is a list of construction/fixture references, not a claim that every listed test exercises every hook.

Removing ambient detection alone would break tests that rely on it and could cause them to use ordinary runtime configuration. **Migrate configuration and isolated real stores before removing the helpers.** Ordinary non-test callers with explicit demo/profile configuration do not need test detection; non-test processes that happen to import pytest currently also change profile. Search did not find a non-test caller intentionally relying on the helper being monkeypatched.

The explicit-env compatibility adapters in [Trading graph_status.py:79](../../../copilot-sdk/apps/trading/backend/app/graph_status.py#L79) and [Purchasing graph_status.py:82](../../../copilot-sdk/apps/purchasing/backend/app/graph_status.py#L82) deserve the same configuration cleanup: they temporarily mutate `os.environ` and infer SQLite/development for incomplete explicit mappings, while the None path uses fail-closed production loading. They are **P2 configuration debt**, not additional proven monkeypatch-only compatibility aliases. Preserve explicit-map callers or replace the input with a typed configuration object; do not silently remove their public configuration behavior.

#### TP-B2 — CIRCULAR missing-yfinance fallback test (P1)

- **Test:** [Trading test_regime.py:245](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L245), `test_regime_no_yfinance_uses_default`.
- **Patch:** [:248](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L248) replaces `RegimeService.get_current_regime` with a dictionary already containing `source="default"`; the assertion at line 252 checks that the CLI prints that value.
- **Production subject bypassed:** [services/regime.py:94](../../../copilot-sdk/apps/trading/backend/app/services/regime.py#L94), particularly the external-dependency fallback at line 109.
- **Why circular:** no missing-yfinance condition is established and the real fallback never executes. This proves CLI formatting of the stub, not the behavior named by the test.
- **Replacement:** force the external dependency to be unavailable, or inject a failing external provider, then call the real regime service through the CLI and assert its actual fallback.

This is **one confirmed circular monkeypatch test**. Two additional injected-double tests match the requested fixed-score/fixed-action pattern:

| Test | Replacement and assertion | Classification / replacement |
|---|---|---|
| [PT/test_purchasing_factors.py:399](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py#L399), `test_queue_has_confidence` | Supplies `FixedQueueScorer(confidence=0.42)` at line 400 and asserts 0.42 at line 403. The scorer ignores its factors/category in its implementation at line 248. | **CIRCULAR as evidence of score correctness, P2.** At most a queue projection assertion; use a real scorer for a scoring claim and name projection-only tests accordingly. |
| [PT/test_purchasing_factors.py:406](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py#L406), `test_queue_has_recommended_action` | Supplies fixed action `order_less` at line 407 and asserts that same action at line 410. | **CIRCULAR as evidence of recommendation correctness, P2.** Verify a real scorer's action on controlled state, or explicitly restrict the test to response-field forwarding. |

The continuation count is **3 tests: 1 circular fallback test plus 2 fixed-output scorer assertions**; only the first uses monkeypatch. These latter two can detect a dropped/renamed projection field, so they are not wholly worthless, but they do not validate scoring or recommendation logic. Genuine priority-formula, sorting and input-forwarding tests that use controlled dependency inputs are not added to this count.

#### TP-B3 — Internal scorer/store doubles remain; separate policy debt from tautology (P2)

These are real injected doubles, not additional monkeypatch calls:

| Test double / test evidence | What is and is not tested | Recommended replacement |
|---|---|---|
| [Purchasing test_verify.py:298](../../../copilot-sdk/apps/purchasing/backend/tests/test_verify.py#L298), used by `test_verify_calls_learn` at line 196 | The fake learn method mutates fake counters and returns a fixed reward. The test asserts delegation arguments, not reward correctness, so it is not counted as CIRCULAR. | Spy around a real scorer with an isolated real GraphStore and assert delegation plus persisted outcome. |
| [Purchasing test_verify.py:389](../../../copilot-sdk/apps/purchasing/backend/tests/test_verify.py#L389), used at line 138 | Fake paused scorer plus `_PausedStore` tests router idempotency behavior; it does not establish the real paused-learning persistence path. | Drive a real paused policy state and verify idempotency against the real store. |
| [Purchasing test_purchasing_factors.py:243](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py#L243), `FixedQueueScorer`, and line 252 counting subclass | Deterministic score results isolate queue priority, factor merging and routing. The two simple fixed-output assertions are separately listed in TP-B2; the other adapter tests are not evidence for real scoring behavior. | Use the real read-only scorer with explicit state and retain downstream priority assertions. |
| [Purchasing test_match_queue.py:24](../../../copilot-sdk/apps/purchasing/backend/tests/test_match_queue.py#L24), `RecordingStore` | Captures write payloads and returns fixed verified/correct counts (lines 50–54). A green response with this input does not prove persistence or whole-system conservation. | Use a real isolated GraphStore with actual decisions/outcomes; inspect its public read API. |
| [Trading test_trust_analysis.py:42](../../../copilot-sdk/apps/trading/backend/tests/test_trust_analysis.py#L42) and line 50 | FakeStore/FakeScorer explicitly serve read-only analyzer fixtures; no scorer method is the tested subject. | A narrow analyzer-input protocol or real stored decisions makes the boundary clearer. |
| [Purchasing test_cross_discovery.py:23](../../../copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py#L23) | FakeEngine is passed through an existing constructor seam. Language/digest tests still exercise the real adapter; lines 32–38 also use the real discovery engine. | Keep clear adapter-test naming and real-engine coverage; no production monkeypatch compatibility hook is needed. |

The SDK's no-fake-scorer/store rule in [CLAUDE.md:80](../../CLAUDE.md#L80) is stricter than “not circular.” Existing `MOCK-OK` comments do not by themselves establish compliance with that rule. This audit records the debt without changing tests or declaring every adapter test tautological.

#### TP-B4 — Per-operation classification and stale-patch result

**203 explicit operations: 202 ACCEPTABLE for their stated isolation/adapter scope, 1 CIRCULAR, 0 confirmed STALE.** No extra `unittest.mock.patch`/alternative MonkeyPatch alias sites were found in these two test trees. No new direct-monkeypatch-only production compatibility alias was established; TP-B1 separately records nine ambient test-runtime sites.

“ACCEPTABLE” means the patch supplies controlled inputs or a dependency boundary while leaving the asserted downstream behavior real. It does not mean the test covers that dependency's implementation or that all internal doubles comply with the stricter repository rule. Filesystem/env/network isolation is ordinary unit-test practice. Tests injecting failures into a factor registry or checking startup call order exercise behavior outside the replacement and are not circular merely because internal functions are patched.

The following operation index records **every counted site** and its classification. `delenv(..., raising=False)` is environment isolation, not evidence of a stale symbol. Targets were inspected statically; no tests were executed, so “0 confirmed stale” is not a runtime proof that every patch intercepts every branch.


#### trading — explicit patch operation index

| Site | Owning fixture/test | Operation / target excerpt | Classification and scope |
|---|---|---|---|
| [TT/conftest.py:91](../../../copilot-sdk/apps/trading/backend/tests/conftest.py#L91) | client | `monkeypatch.setattr(context_router, "_DATA_DIR", temp_data)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_broker_cli.py:62](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L62) | test_orders_command_with_shared_mock | `monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_cli.py:74](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L74) | test_positions_command_with_shared_mock | `monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_cli.py:95](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L95) | test_sync_writes_filled_orders_to_journal | `monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_cli.py:113](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L113) | test_sync_is_idempotent | `monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_cli.py:126](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L126) | test_sync_dry_run_writes_nothing | `monkeypatch.setattr(cli, "_get_broker", lambda _name: broker)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_cli.py:135](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L135) | test_order_without_credentials_returns_friendly_error | `monkeypatch.delenv("APCA_API_KEY_ID", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker_cli.py:136](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L136) | test_order_without_credentials_returns_friendly_error | `monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker_cli.py:151](../../../copilot-sdk/apps/trading/backend/tests/test_broker_cli.py#L151) | test_non_broker_command_does_not_call_get_broker | `monkeypatch.setattr(cli, "_get_broker", fail)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_router.py:9](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L9) | _clear_alpaca_env | `monkeypatch.delenv("APCA_API_KEY_ID", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker_router.py:10](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L10) | _clear_alpaca_env | `monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker_router.py:11](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L11) | _clear_alpaca_env | `monkeypatch.delenv("APCA_API_BASE_URL", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker_router.py:104](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L104) | test_broker_account_method_failure_returns_error_json | `monkeypatch.setattr(MockBroker, "get_account", fail)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_router.py:120](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L120) | test_broker_positions_method_failure_returns_error_json | `monkeypatch.setattr(MockBroker, "get_positions", fail)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_router.py:136](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L136) | test_broker_orders_method_failure_returns_error_json | `monkeypatch.setattr(MockBroker, "get_orders", fail)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker_router.py:232](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L232) | test_broker_post_order_connector_failure_returns_safe_error | `monkeypatch.setattr(MockBroker, "place_order", fail_place_order)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker.py:103](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L103) | test_alpaca_missing_key_raises | `monkeypatch.delenv("APCA_API_KEY_ID", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:104](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L104) | test_alpaca_missing_key_raises | `monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:111](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L111) | test_alpaca_missing_secret_raises | `monkeypatch.setenv("APCA_API_KEY_ID", "key")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:112](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L112) | test_alpaca_missing_secret_raises | `monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:119](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L119) | test_alpaca_default_base_url_without_network | `monkeypatch.setenv("APCA_API_KEY_ID", "key")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:120](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L120) | test_alpaca_default_base_url_without_network | `monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:121](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L121) | test_alpaca_default_base_url_without_network | `monkeypatch.delenv("APCA_API_BASE_URL", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:129](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L129) | test_alpaca_uses_env_base_url_without_network | `monkeypatch.setenv("APCA_API_KEY_ID", "key")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:130](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L130) | test_alpaca_uses_env_base_url_without_network | `monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:131](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L131) | test_alpaca_uses_env_base_url_without_network | `monkeypatch.setenv("APCA_API_BASE_URL", "https://broker.invalid")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_broker.py:146](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L146) | test_ibkr_factory_wiring | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_broker.py:147](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L147) | test_ibkr_factory_wiring | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker.py:204](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L204) | test_ibkr_import_endpoint | `monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker.py:223](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L223) | test_ibkr_import_connection_refused_returns_400 | `monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker.py:248](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L248) | test_ibkr_import_dedup | `monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_broker.py:286](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L286) | test_broker_import_dedup_different_direction | `monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:92](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L92) | test_ibkr_connect_failure_returns_false | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:93](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L93) | test_ibkr_connect_failure_returns_false | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:128](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L128) | test_ibkr_trade_id_format | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:129](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L129) | test_ibkr_trade_id_format | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:419](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L419) | test_ibkr_old_fill_ignored | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:420](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L420) | test_ibkr_old_fill_ignored | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:452](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L452) | test_ibkr_import_handles_timezone_aware_execution_time | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:453](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L453) | test_ibkr_import_handles_timezone_aware_execution_time | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:490](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L490) | test_ibkr_import_filters_old_timezone_aware_execution_time | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:491](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L491) | test_ibkr_import_filters_old_timezone_aware_execution_time | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:523](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L523) | test_ibkr_import_skips_unparseable_execution_time | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:524](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L524) | test_ibkr_import_skips_unparseable_execution_time | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_complete.py:556](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L556) | test_ibkr_import_parses_ibkr_execution_time_format | `monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_cli_complete.py:557](../../../copilot-sdk/apps/trading/backend/tests/test_cli_complete.py#L557) | test_ibkr_import_parses_ibkr_execution_time_format | `monkeypatch.setattr(ibkr_connector, "IB", FakeIB)` | ACCEPTABLE: External broker boundary; real router/CLI behavior retained |
| [TT/test_cli_sdk.py:306](../../../copilot-sdk/apps/trading/backend/tests/test_cli_sdk.py#L306) | test_db_path_relative | `monkeypatch.chdir(tmp_path)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_correlation.py:29](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L29) | _mock_fetch | `monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_correlation.py:30](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L30) | _mock_fetch | `monkeypatch.setattr(CorrelationService, "_fetch_returns", lambda self, tickers: payload or _returns())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_correlation.py:145](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L145) | test_yfinance_unavailable_returns_insufficient | `monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", False)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_correlation.py:154](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L154) | test_numpy_unavailable_returns_insufficient | `monkeypatch.setattr(correlation_module, "YFINANCE_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_correlation.py:155](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L155) | test_numpy_unavailable_returns_insufficient | `monkeypatch.setattr(correlation_module, "NUMPY_AVAILABLE", False)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_correlation.py:195](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L195) | test_correlation_endpoint_returns_200 | `monkeypatch.setattr(CorrelationService, "compute", lambda self, trades: {"source": "insufficient_data", "window_days": self.window_days, "tickers": ["AAPL", "MSFT"]})` | ACCEPTABLE: Route/CLI forwarding or rendering contract, not correlation math |
| [TT/test_correlation.py:216](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L216) | test_correlation_endpoint_window_param | `monkeypatch.setattr(CorrelationService, "compute", lambda self, trades: {"source": "insufficient_data", "window_days": self.window_days, "tickers": []})` | ACCEPTABLE: Route/CLI forwarding or rendering contract, not correlation math |
| [TT/test_correlation.py:227](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L227) | test_correlation_command_output | `monkeypatch.setattr( CorrelationService, "compute", lambda self, trades: { "source": "yfinance", "window_days": self.window_days, "tickers": ["AAPL", "MSFT"], "avg_correlation": 0.…` | ACCEPTABLE: Route/CLI forwarding or rendering contract, not correlation math |
| [TT/test_correlation.py:261](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L261) | test_correlation_command_insufficient_data | `monkeypatch.setattr( CorrelationService, "compute", lambda self, trades: {"source": "insufficient_data", "reason": "mock insufficient", "window_days": self.window_days}, )` | ACCEPTABLE: Route/CLI forwarding or rendering contract, not correlation math |
| [TT/test_csv_connector.py:255](../../../copilot-sdk/apps/trading/backend/tests/test_csv_connector.py#L255) | test_connection_fails_without_credentials | `monkeypatch.delenv("APCA_API_KEY_ID", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_csv_connector.py:256](../../../copilot-sdk/apps/trading/backend/tests/test_csv_connector.py#L256) | test_connection_fails_without_credentials | `monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_csv_connector.py:285](../../../copilot-sdk/apps/trading/backend/tests/test_csv_connector.py#L285) | test_provider_returns_empty_without_network_dependency | `monkeypatch.setattr(builtins, "__import__", fake_import)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_journal.py:485](../../../copilot-sdk/apps/trading/backend/tests/test_journal.py#L485) | test_write_permission_error_returns_500 | `monkeypatch.setattr(journal_router, "_write_json_atomic_unlocked", fail_write)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_market_refresh.py:41](../../../copilot-sdk/apps/trading/backend/tests/test_market_refresh.py#L41) | test_refresh_returns_200 | `monkeypatch.setattr(data_import, "_provider", provider)` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_market_refresh.py:56](../../../copilot-sdk/apps/trading/backend/tests/test_market_refresh.py#L56) | test_refresh_clears_cache_and_refetches | `monkeypatch.setattr(data_import, "_provider", provider)` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_market_refresh.py:57](../../../copilot-sdk/apps/trading/backend/tests/test_market_refresh.py#L57) | test_refresh_clears_cache_and_refetches | `monkeypatch.setattr(context_router, "_provider", provider)` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_market_refresh.py:73](../../../copilot-sdk/apps/trading/backend/tests/test_market_refresh.py#L73) | test_refresh_with_failed_source | `monkeypatch.setattr(data_import, "_provider", provider)` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_market_regime.py:185](../../../copilot-sdk/apps/trading/backend/tests/test_market_regime.py#L185) | test_registry_exception_in_factor_defaults_neutral | `monkeypatch.setitem(TRADING_FACTOR_COMPUTERS, "signal_alignment", FailingFactor())` | ACCEPTABLE: Injected input-provider failure; real registry error handling runs |
| [TT/test_market_source.py:80](../../../copilot-sdk/apps/trading/backend/tests/test_market_source.py#L80) | test_yfinance_source_graceful_without_network | `monkeypatch.setitem(sys.modules, "yfinance", fake_yfinance)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_options_factors.py:27](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L27) | no_yfinance | `monkeypatch.setattr(options, "YFINANCE_AVAILABLE", False)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_options_factors.py:40](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L40) | default_regime | `monkeypatch.setattr( RegimeService, "get_current_regime", lambda self: { "regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default", }, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_options_factors.py:51](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L51) | default_regime | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_options_factors.py:114](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L114) | test_iv_rv_fetch_failure_returns_neutral_or_partial_default | `monkeypatch.setattr(options, "YFINANCE_AVAILABLE", True)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_options_factors.py:115](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L115) | test_iv_rv_fetch_failure_returns_neutral_or_partial_default | `monkeypatch.setattr(options, "yf", BrokenYF)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_options_factors.py:178](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L178) | test_compute_handles_exception | `monkeypatch.setitem(OPTIONS_FACTOR_COMPUTERS, "iv_rv_ratio", Broken())` | ACCEPTABLE: Injected input-provider failure; real registry error handling runs |
| [TT/test_options_factors.py:215](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L215) | test_prescore_includes_options_for_income | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_options_factors.py:226](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L226) | test_prescore_options_has_analytics_only_flag | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_options_factors.py:237](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L237) | test_prescore_does_not_mix_options_into_core_factors | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _core_factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_p50_smoke.py:45](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L45) | test_smoke_market_snapshot_returns_provenance | `monkeypatch.setattr(context_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:58](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L58) | test_smoke_market_snapshot_spy_field | `monkeypatch.setattr(context_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:71](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L71) | test_smoke_ticker_returns_provenance | `monkeypatch.setattr(context_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:83](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L83) | test_smoke_ticker_camelcase_fields | `monkeypatch.setattr(context_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:95](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L95) | test_smoke_regime_still_works | `monkeypatch.setattr(regime_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:108](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L108) | test_smoke_correlation_still_works | `monkeypatch.setattr(correlation_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:122](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L122) | test_smoke_vix_timing_still_works | `monkeypatch.setattr(vix_timing_router, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:135](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L135) | test_smoke_market_ohlcv_still_works | `monkeypatch.setattr(data_import, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:148](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L148) | test_smoke_market_vix_still_works | `monkeypatch.setattr(data_import, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_p50_smoke.py:161](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L161) | test_smoke_refresh_returns_provenance | `monkeypatch.setattr(data_import, "_provider", _provider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_prescore.py:21](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L21) | default_regime | `monkeypatch.setattr( RegimeService, "get_current_regime", lambda self: { "regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default", }, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:32](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L32) | default_regime | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:79](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L79) | test_prescore_returns_recommendation | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:95](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L95) | test_prescore_skip_on_low_confidence | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(**{name: 0.35 for name in _factors()}))` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:104](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L104) | test_prescore_skip_on_low_regime_accuracy | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:105](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L105) | test_prescore_skip_on_low_regime_accuracy | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.35}})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:114](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L114) | test_prescore_reduce_on_decision_context_pattern | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.45))` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:123](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L123) | test_prescore_proceed_when_clear | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:124](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L124) | test_prescore_proceed_when_clear | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.7}})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:133](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L133) | test_prescore_includes_evidence_text | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:141](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L141) | test_prescore_includes_warnings_list | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.45))` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:149](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L149) | test_prescore_includes_regime_data | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:158](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L158) | test_prescore_auto_classifies_category | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:166](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L166) | test_prescore_no_historical_trades | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:175](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L175) | test_prescore_response_has_all_keys | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:194](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L194) | test_prescore_read_only_does_not_increment_decision_count | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:235](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L235) | test_prescore_skip_boundary_confidence_040 | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(**{name: 0.4 for name in _factors()}))` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:243](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L243) | test_prescore_skip_boundary_regime_acc_040 | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:244](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L244) | test_prescore_skip_boundary_regime_acc_040 | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"ranging": 0.4}})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:252](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L252) | test_prescore_reduce_boundary_emotional_050 | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors(emotional_indicator=0.5, signal_confidence=1.0))` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:261](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L261) | test_prescore_warns_on_quick_reentry_after_loss | `monkeypatch.setattr(prescore, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:269](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L269) | test_prescore_market_regime_uses_accuracy_dict | `monkeypatch.setattr( RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 32.0}, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:274](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L274) | test_prescore_market_regime_uses_accuracy_dict | `monkeypatch.setattr( RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"trending": 0.82}}, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:304](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L304) | test_prescore_signal_confidence_has_context_keys | `monkeypatch.setattr(prescore, "compute_factors", spy_compute_factors)` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:320](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L320) | test_prescore_all_10_factors_wired | `monkeypatch.setattr( RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 32.0}, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_prescore.py:325](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L325) | test_prescore_all_10_factors_wired | `monkeypatch.setattr( RegimeService, "get_regime_accuracy", lambda self, trades: {"trend_following": {"trending": 0.82}}, )` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender_p49.py:75](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L75) | test_p49_sample_counts_include_inferred_regime_from_vix | `monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_regime_recommender_p49.py:95](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L95) | test_p49_edge_summary_uses_same_regime_inference_as_regime_accuracy | `monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_regime_recommender_p49.py:96](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L96) | test_p49_edge_summary_uses_same_regime_inference_as_regime_accuracy | `monkeypatch.setattr(RegimeService, "_batch_vix_lookup", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_regime_recommender_p49.py:110](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L110) | test_p49_unknown_regime_rows_warn_without_fabricating_samples | `monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {})` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_regime_recommender_p49.py:245](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L245) | test_existing_regime_detail_response_compatible | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "volatile", "vix": 32.0, "adx": 15.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender_p49.py:246](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L246) | test_existing_regime_detail_response_compatible | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: _accuracy())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:167](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L167) | test_regime_detail_returns_recommendations | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:177](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L177) | test_regime_detail_includes_transitions | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:178](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L178) | test_regime_detail_includes_transitions | `monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: _accuracy())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:188](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L188) | test_regime_detail_conservation_unknown_still_200 | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:189](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L189) | test_regime_detail_conservation_unknown_still_200 | `monkeypatch.setattr(regime_router, "_conservation_status", lambda _factory: None)` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:199](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L199) | test_existing_regime_endpoint_shape_unchanged | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:210](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L210) | test_regime_detail_flag | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:220](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L220) | test_regime_no_detail_default | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime_recommender.py:232](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L232) | test_regime_detail_warns_when_conservation_unknown | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:55](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L55) | test_adx_import_failure_returns_default | `monkeypatch.setitem(sys.modules, "pandas_ta", None)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_regime.py:86](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L86) | test_service_caches_result | `monkeypatch.setattr(regime_module, "compute_adx", lambda *_args, **_kwargs: 30.0)` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:141](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L141) | test_regime_accuracy_with_retroactive_batch | `monkeypatch.setattr(service, "_batch_vix_lookup", lambda trades: {"2026-01-05": 18.0, "2026-01-06": 31.0})` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_regime.py:155](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L155) | test_regime_endpoint_returns_200 | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:164](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L164) | test_regime_endpoint_has_current | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:174](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L174) | test_regime_endpoint_includes_accuracy | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:187](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L187) | test_regime_endpoint_includes_recommendations | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:209](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L209) | test_regime_endpoint_cold_start_no_trades_200 | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "spy_price": 0.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:220](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L220) | test_regime_shows_current | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "trending", "vix": 18.0, "adx": 30.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:236](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L236) | test_regime_with_trades_shows_table | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_regime.py:248](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L248) | test_regime_no_yfinance_uses_default | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | CIRCULAR / P1: TP-B2 |
| [TT/test_regime.py:258](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L258) | test_regime_no_trades_still_shows_regime | `monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0, "adx": 20.0, "source": "default"})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_rejection_summary.py:114](../../../copilot-sdk/apps/trading/backend/tests/test_rejection_summary.py#L114) | test_rejection_summary_reads_persisted_preseed_log | `monkeypatch.setenv("TRADING_EVOLUTION_LOG_PATH", str(log_path))` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_signal_confidence.py:122](../../../copilot-sdk/apps/trading/backend/tests/test_signal_confidence.py#L122) | test_fallback_registry_uses_semantic_factor_mapping | `monkeypatch.setattr(builtins, "__import__", force_preset_import_failure)` | ACCEPTABLE: External dependency availability/failure |
| [TT/test_signal_confidence.py:178](../../../copilot-sdk/apps/trading/backend/tests/test_signal_confidence.py#L178) | test_unrelated_exception_still_defaults_factor_neutral | `monkeypatch.setitem(TRADING_FACTOR_COMPUTERS, "signal_confidence", FailingFactor())` | ACCEPTABLE: Injected input-provider failure; real registry error handling runs |
| [TT/test_subcategory.py:192](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L192) | test_prescore_event_driven_includes_subcategory | `monkeypatch.setattr(prescore_module.RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_subcategory.py:193](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L193) | test_prescore_event_driven_includes_subcategory | `monkeypatch.setattr(prescore_module.RegimeService, "get_regime_accuracy", lambda self, trades: {})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_subcategory.py:194](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L194) | test_prescore_event_driven_includes_subcategory | `monkeypatch.setattr(prescore_module, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_subcategory.py:206](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L206) | test_prescore_non_event_omits_subcategory | `monkeypatch.setattr(prescore_module.RegimeService, "get_current_regime", lambda self: {"regime": "ranging", "vix": 20.0})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_subcategory.py:207](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L207) | test_prescore_non_event_omits_subcategory | `monkeypatch.setattr(prescore_module.RegimeService, "get_regime_accuracy", lambda self, trades: {})` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_subcategory.py:208](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L208) | test_prescore_non_event_omits_subcategory | `monkeypatch.setattr(prescore_module, "compute_factors", lambda context: _factors())` | ACCEPTABLE: Controlled service/factor input for downstream adapter/policy test |
| [TT/test_trading_backend.py:157](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L157) | test_market_snapshot | `monkeypatch.setattr( context_router, "_provider", _FakeContextProvider( market_snapshot={ "spy": {"price": 555.2, "change_pct": 1.3}, "vix": 14.8, "rsi": 58.2, "above_50ma": True, …` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_trading_backend.py:185](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L185) | test_market_snapshot_missing_file_returns_default | `monkeypatch.setattr(context_router, "_provider", _FakeContextProvider(market_snapshot=None))` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_trading_backend.py:186](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L186) | test_market_snapshot_missing_file_returns_default | `monkeypatch.setattr(context_router, "_DATA_DIR", tmp_path / "missing-data")` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_trading_backend.py:187](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L187) | test_market_snapshot_missing_file_returns_default | `monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_trading_backend.py:201](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L201) | test_ticker_known | `monkeypatch.setattr( context_router, "_provider", _FakeContextProvider( tickers={ "NVDA": { "ticker": "NVDA", "price": 900.0, "change_30d_pct": 2.1, "volume": 30_000_000, } } ), )` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_trading_backend.py:226](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L226) | test_ticker_unknown | `monkeypatch.setattr(context_router, "_provider", _FakeContextProvider())` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_trading_backend.py:238](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L238) | test_ticker_enhanced_fields | `monkeypatch.setattr( context_router, "_provider", _FakeContextProvider( tickers={ "MSFT": { "ticker": "MSFT", "price": 430.0, "change_30d_pct": 1.4, "volume": 22_000_000, "sector":…` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_trading_backend.py:297](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L297) | test_trade_metadata_malformed_file_returns_empty | `monkeypatch.setattr(context_router, "_DATA_DIR", malformed_dir)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_trading_backend.py:298](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L298) | test_trade_metadata_malformed_file_returns_empty | `monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_trading_backend.py:396](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L396) | test_ci_data_dir_creates_db | `monkeypatch.setenv("CI_DATA_DIR", str(data_dir))` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_backend.py:411](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L411) | test_explicit_db_path_wins | `monkeypatch.setenv("CI_DATA_DIR", str(ci_dir))` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_backend.py:424](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L424) | test_no_env_uses_explicit_fallback | `monkeypatch.delenv("CI_DATA_DIR", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_backend.py:470](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L470) | test_l5_startup_restore_runs_after_seed_setup | `monkeypatch.setattr(app_main, "_auto_seed_if_needed", fake_seed)` | ACCEPTABLE: Startup sequencing test; asserts real orchestrator call order |
| [TT/test_trading_backend.py:471](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L471) | test_l5_startup_restore_runs_after_seed_setup | `monkeypatch.setattr(app_main, "restore_l5_runtime_state", fake_restore)` | ACCEPTABLE: Startup sequencing test; asserts real orchestrator call order |
| [TT/test_trading_backend.py:549](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L549) | test_v2_context_uses_temp_data_without_default_fallback | `monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [TT/test_trading_graph_status.py:56](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L56) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_BACKEND", "age")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:57](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L57) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_DSN", "postgresql://postgres:secret@example/db")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:58](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L58) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_NAME", "protocol_v2_test")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:223](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L223) | test_generic_graph_backend_age_still_downgrades_to_sqlite | `monkeypatch.setenv("GRAPH_BACKEND", "age")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:383](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L383) | test_direct_store_construction_rejects_shadow_conflict | `monkeypatch.setenv("TRADING_SHADOW_AGE", "1")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:461](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L461) | _configure_explicit_sqlite | `monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:462](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L462) | _configure_explicit_sqlite | `monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "sqlite")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:467](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L467) | _set_active_age_env | `monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "age")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:468](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L468) | _set_active_age_env | `monkeypatch.setenv("TRADING_ACTIVE_AGE_DSN", dsn)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:469](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L469) | _set_active_age_env | `monkeypatch.setenv("TRADING_ACTIVE_AGE_GRAPH", "protocol_v2_test")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:470](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L470) | _set_active_age_env | `monkeypatch.setenv("TRADING_ACTIVE_AGE_DOMAIN", "trading")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:471](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L471) | _set_active_age_env | `monkeypatch.setenv("TRADING_ACTIVE_AGE_TEST_MODE", "1")` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_trading_graph_status.py:490](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L490) | _clear_active_env | `monkeypatch.delenv(key, raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [TT/test_vix_timing.py:228](../../../copilot-sdk/apps/trading/backend/tests/test_vix_timing.py#L228) | test_vix_timing_returns_200 | `monkeypatch.setattr(vix_timing_router, "_provider", _FakeVixProvider({"2026-01-01": 18.0}))` | ACCEPTABLE: Market-data provider/history input boundary |
| [TT/test_vix_timing.py:250](../../../copilot-sdk/apps/trading/backend/tests/test_vix_timing.py#L250) | test_vix_timing_uses_provider_vix_mocked | `monkeypatch.setattr(vix_timing_router, "_provider", _FakeVixProvider({"2026-01-01": 31.0}, calls))` | ACCEPTABLE: Market-data provider/history input boundary |

#### purchasing — explicit patch operation index

| Site | Owning fixture/test | Operation / target excerpt | Classification and scope |
|---|---|---|---|
| [PT/conftest.py:87](../../../copilot-sdk/apps/purchasing/backend/tests/conftest.py#L87) | temp_data_dir | `monkeypatch.setattr(context_router, "_DATA_DIR", temp_data)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [PT/conftest.py:90](../../../copilot-sdk/apps/purchasing/backend/tests/conftest.py#L90) | temp_data_dir | `monkeypatch.setattr(main_module, "DATA_DIR", temp_data)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [PT/test_commodity.py:20](../../../copilot-sdk/apps/purchasing/backend/tests/test_commodity.py#L20) | _no_fred_env | `monkeypatch.delenv("FRED_API_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_commodity.py:183](../../../copilot-sdk/apps/purchasing/backend/tests/test_commodity.py#L183) | test_main_wires_fred_when_key_set | `monkeypatch.setenv("FRED_API_KEY", "test-key")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_commodity.py:195](../../../copilot-sdk/apps/purchasing/backend/tests/test_commodity.py#L195) | test_main_falls_back_without_key | `monkeypatch.delenv("FRED_API_KEY", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_dashboard_projection.py:28](../../../copilot-sdk/apps/purchasing/backend/tests/test_dashboard_projection.py#L28) | test_dashboard_orders_projects_only_order_card_fields | `monkeypatch.setattr(dashboard_router, "_ORDER_METADATA_PATH", metadata_path)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [PT/test_inventory_summary.py:50](../../../copilot-sdk/apps/purchasing/backend/tests/test_inventory_summary.py#L50) | test_inventory_summary_empty_waste_history_is_unknown | `monkeypatch.setattr(inventory_router, "_WASTE_HISTORY_PATH", empty_history)` | ACCEPTABLE: Filesystem location or write-failure boundary |
| [PT/test_match_queue.py:200](../../../copilot-sdk/apps/purchasing/backend/tests/test_match_queue.py#L200) | test_queue_empty_context_returns_empty_queue_without_crashing | `monkeypatch.setattr(queue_router, "_orders", lambda connector=None: [])` | ACCEPTABLE: Order-input boundary; real queue processing runs |
| [PT/test_purchasing_backend.py:279](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L279) | test_ci_data_dir_creates_db | `monkeypatch.setenv("CI_DATA_DIR", str(data_dir))` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_backend.py:294](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L294) | test_explicit_db_path_wins | `monkeypatch.setenv("CI_DATA_DIR", str(ci_dir))` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_backend.py:307](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L307) | test_no_env_uses_explicit_fallback | `monkeypatch.delenv("CI_DATA_DIR", raising=False)` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_backend.py:350](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L350) | test_l5_startup_restore_runs_after_seed_setup | `monkeypatch.setattr(app_main, "_auto_seed_if_needed", fake_seed)` | ACCEPTABLE: Startup sequencing test; asserts real orchestrator call order |
| [PT/test_purchasing_backend.py:351](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L351) | test_l5_startup_restore_runs_after_seed_setup | `monkeypatch.setattr(app_main, "restore_l5_runtime_state", fake_restore)` | ACCEPTABLE: Startup sequencing test; asserts real orchestrator call order |
| [PT/test_purchasing_factors.py:286](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py#L286) | queue_client | `monkeypatch.setattr(queue_router, "_orders", lambda connector=None: orders)` | ACCEPTABLE: Order-input boundary; real queue processing runs |
| [PT/test_purchasing_graph_status.py:52](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L52) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_BACKEND", "age")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:53](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L53) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_DSN", "postgresql://postgres:secret@example/db")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:54](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L54) | test_graph_status_ignores_generic_graph_env | `monkeypatch.setenv("GRAPH_NAME", "protocol_v2_test")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:315](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L315) | test_direct_store_construction_rejects_shadow_conflict | `monkeypatch.setenv("PURCHASING_SHADOW_AGE", "1")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:376](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L376) | _configure_explicit_sqlite | `monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:377](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L377) | _configure_explicit_sqlite | `monkeypatch.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "sqlite")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:382](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L382) | _set_active_age_env | `monkeypatch.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "age")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:383](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L383) | _set_active_age_env | `monkeypatch.setenv("PURCHASING_ACTIVE_AGE_DSN", dsn)` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:384](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L384) | _set_active_age_env | `monkeypatch.setenv("PURCHASING_ACTIVE_AGE_GRAPH", "protocol_v2_test")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:385](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L385) | _set_active_age_env | `monkeypatch.setenv("PURCHASING_ACTIVE_AGE_DOMAIN", "purchasing")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:386](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L386) | _set_active_age_env | `monkeypatch.setenv("PURCHASING_ACTIVE_AGE_TEST_MODE", "1")` | ACCEPTABLE: Environment/configuration isolation |
| [PT/test_purchasing_graph_status.py:406](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L406) | _clear_active_env | `monkeypatch.delenv(key, raising=False)` | ACCEPTABLE: Environment/configuration isolation |

#### App-factory / client-fixture test consumer index for TP-B1

The first listed line is an app construction or test receiving the client fixture. Remaining lines enumerate the other direct references found in that file. Locally defined client fixtures may select their own dependencies; these rows are a migration search index, not proof of identical setup across all tests.

**trading:**

| Test file / first reference | Other direct construction or client-fixture reference lines |
|---|---|
| [TT/conftest.py:92](../../../copilot-sdk/apps/trading/backend/tests/conftest.py#L92) | — |
| [TT/test_analytics.py:46](../../../copilot-sdk/apps/trading/backend/tests/test_analytics.py#L46) | — |
| [TT/test_broker.py:187](../../../copilot-sdk/apps/trading/backend/tests/test_broker.py#L187) | 216, 231, 260, 295 |
| [TT/test_broker_router.py:27](../../../copilot-sdk/apps/trading/backend/tests/test_broker_router.py#L27) | 40, 53, 65, 77, 89, 100, 116, 132, 148, 160, 170, 175, 188, 198, 216, 228, 244 |
| [TT/test_bundle_wiring.py:17](../../../copilot-sdk/apps/trading/backend/tests/test_bundle_wiring.py#L17) | 23 |
| [TT/test_cohort_status.py:178](../../../copilot-sdk/apps/trading/backend/tests/test_cohort_status.py#L178) | — |
| [TT/test_conservation_breakdown.py:38](../../../copilot-sdk/apps/trading/backend/tests/test_conservation_breakdown.py#L38) | 46, 54, 65, 74, 83, 90, 96, 103, 114, 125, 136 |
| [TT/test_correlation.py:192](../../../copilot-sdk/apps/trading/backend/tests/test_correlation.py#L192) | 203, 213 |
| [TT/test_csv_connector.py:178](../../../copilot-sdk/apps/trading/backend/tests/test_csv_connector.py#L178) | 196 |
| [TT/test_data_endpoints.py:13](../../../copilot-sdk/apps/trading/backend/tests/test_data_endpoints.py#L13) | 22, 37, 47, 63, 73, 81, 94, 102, 113 |
| [TT/test_evidence.py:375](../../../copilot-sdk/apps/trading/backend/tests/test_evidence.py#L375) | 385, 402, 430, 437, 446 |
| [TT/test_evolution_mount.py:4](../../../copilot-sdk/apps/trading/backend/tests/test_evolution_mount.py#L4) | 23, 31 |
| [TT/test_evolution_trading.py:189](../../../copilot-sdk/apps/trading/backend/tests/test_evolution_trading.py#L189) | — |
| [TT/test_journal.py:67](../../../copilot-sdk/apps/trading/backend/tests/test_journal.py#L67) | 72, 84, 94, 104, 114, 124, 134, 144, 158, 166, 174, 184, 191, 200, 211, 221, 231, 241, 251, 261, 268, 281, 291, 299, 314, 328, 341, 355, 368, 381, 391, 402, 435, 452, 469, 479 |
| [TT/test_journal_query.py:125](../../../copilot-sdk/apps/trading/backend/tests/test_journal_query.py#L125) | — |
| [TT/test_market_refresh.py:38](../../../copilot-sdk/apps/trading/backend/tests/test_market_refresh.py#L38) | 53, 70 |
| [TT/test_measurement_state.py:4](../../../copilot-sdk/apps/trading/backend/tests/test_measurement_state.py#L4) | 12 |
| [TT/test_multi_trader.py:113](../../../copilot-sdk/apps/trading/backend/tests/test_multi_trader.py#L113) | 135, 153, 170 |
| [TT/test_observation_only.py:28](../../../copilot-sdk/apps/trading/backend/tests/test_observation_only.py#L28) | 75 |
| [TT/test_options_factors.py:214](../../../copilot-sdk/apps/trading/backend/tests/test_options_factors.py#L214) | 225, 236, 260, 287 |
| [TT/test_p50_smoke.py:43](../../../copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py#L43) | 56, 69, 81, 93, 105, 119, 133, 146, 159 |
| [TT/test_pattern_detector.py:285](../../../copilot-sdk/apps/trading/backend/tests/test_pattern_detector.py#L285) | 296, 316 |
| [TT/test_prescore.py:78](../../../copilot-sdk/apps/trading/backend/tests/test_prescore.py#L78) | 87, 94, 103, 113, 122, 132, 140, 148, 157, 165, 174, 193, 234, 242, 251, 259, 268, 286, 314, 359 |
| [TT/test_promotion.py:229](../../../copilot-sdk/apps/trading/backend/tests/test_promotion.py#L229) | 235, 241, 248 |
| [TT/test_regime.py:153](../../../copilot-sdk/apps/trading/backend/tests/test_regime.py#L153) | 162, 171, 181, 207 |
| [TT/test_regime_analytics.py:102](../../../copilot-sdk/apps/trading/backend/tests/test_regime_analytics.py#L102) | — |
| [TT/test_regime_beats.py:6](../../../copilot-sdk/apps/trading/backend/tests/test_regime_beats.py#L6) | 15, 21, 27, 36, 42, 49, 58, 63, 69, 78, 85 |
| [TT/test_regime_conditioned_learning.py:21](../../../copilot-sdk/apps/trading/backend/tests/test_regime_conditioned_learning.py#L21) | 38 |
| [TT/test_regime_recommender.py:164](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender.py#L164) | 175, 186, 197 |
| [TT/test_regime_recommender_p49.py:242](../../../copilot-sdk/apps/trading/backend/tests/test_regime_recommender_p49.py#L242) | — |
| [TT/test_regime_throttle.py:56](../../../copilot-sdk/apps/trading/backend/tests/test_regime_throttle.py#L56) | 63, 69, 156, 163, 174, 184 |
| [TT/test_situation_analyzer.py:60](../../../copilot-sdk/apps/trading/backend/tests/test_situation_analyzer.py#L60) | — |
| [TT/test_situation_judgment.py:56](../../../copilot-sdk/apps/trading/backend/tests/test_situation_judgment.py#L56) | — |
| [TT/test_social.py:68](../../../copilot-sdk/apps/trading/backend/tests/test_social.py#L68) | 78, 93, 102, 113, 122, 137, 152, 158, 172, 187 |
| [TT/test_subcategory.py:127](../../../copilot-sdk/apps/trading/backend/tests/test_subcategory.py#L127) | 143, 155, 191, 205 |
| [TT/test_trading_active_age_live.py:36](../../../copilot-sdk/apps/trading/backend/tests/test_trading_active_age_live.py#L36) | — |
| [TT/test_trading_backend.py:112](../../../copilot-sdk/apps/trading/backend/tests/test_trading_backend.py#L112) | 123, 156, 184, 200, 225, 237, 271, 293, 306, 313, 346, 366, 386, 397, 413, 426, 436, 473, 481, 503, 523, 548, 571, 580, 591, 603, 630, 645, 654, 663, 672, 681, 739 |
| [TT/test_trading_config_migration.py:139](../../../copilot-sdk/apps/trading/backend/tests/test_trading_config_migration.py#L139) | — |
| [TT/test_trading_evolver.py:196](../../../copilot-sdk/apps/trading/backend/tests/test_trading_evolver.py#L196) | 220 |
| [TT/test_trading_graph_status.py:37](../../../copilot-sdk/apps/trading/backend/tests/test_trading_graph_status.py#L37) | 60, 237, 347, 403 |
| [TT/test_trust_analysis.py:130](../../../copilot-sdk/apps/trading/backend/tests/test_trust_analysis.py#L130) | 136, 145, 159, 175, 188, 194, 200, 213, 292, 300 |
| [TT/test_vix_timing.py:225](../../../copilot-sdk/apps/trading/backend/tests/test_vix_timing.py#L225) | 236, 245 |
| [TT/test_volatility_demo_beats.py:19](../../../copilot-sdk/apps/trading/backend/tests/test_volatility_demo_beats.py#L19) | 25, 31 |
| [TT/test_volatility_scenarios.py:67](../../../copilot-sdk/apps/trading/backend/tests/test_volatility_scenarios.py#L67) | — |
| [TT/test_vol_analytics.py:19](../../../copilot-sdk/apps/trading/backend/tests/test_vol_analytics.py#L19) | — |
| [TT/test_webhook.py:74](../../../copilot-sdk/apps/trading/backend/tests/test_webhook.py#L74) | 87, 93, 104, 114, 127, 141, 152, 171, 185 |

**purchasing:**

| Test file / first reference | Other direct construction or client-fixture reference lines |
|---|---|
| [PT/conftest.py:99](../../../copilot-sdk/apps/purchasing/backend/tests/conftest.py#L99) | — |
| [PT/test_alert_engine.py:137](../../../copilot-sdk/apps/purchasing/backend/tests/test_alert_engine.py#L137) | 144, 151, 158 |
| [PT/test_auto_order.py:154](../../../copilot-sdk/apps/purchasing/backend/tests/test_auto_order.py#L154) | 163 |
| [PT/test_bundle_wiring.py:17](../../../copilot-sdk/apps/purchasing/backend/tests/test_bundle_wiring.py#L17) | 23 |
| [PT/test_chain_demo.py:66](../../../copilot-sdk/apps/purchasing/backend/tests/test_chain_demo.py#L66) | 82 |
| [PT/test_cohort_status.py:196](../../../copilot-sdk/apps/purchasing/backend/tests/test_cohort_status.py#L196) | 240 |
| [PT/test_commodity.py:34](../../../copilot-sdk/apps/purchasing/backend/tests/test_commodity.py#L34) | — |
| [PT/test_control_reads.py:9](../../../copilot-sdk/apps/purchasing/backend/tests/test_control_reads.py#L9) | — |
| [PT/test_cross_discovery.py:91](../../../copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py#L91) | 98 |
| [PT/test_dashboard_projection.py:9](../../../copilot-sdk/apps/purchasing/backend/tests/test_dashboard_projection.py#L9) | 46 |
| [PT/test_delivery_coordinator.py:67](../../../copilot-sdk/apps/purchasing/backend/tests/test_delivery_coordinator.py#L67) | 74 |
| [PT/test_economic_model.py:87](../../../copilot-sdk/apps/purchasing/backend/tests/test_economic_model.py#L87) | — |
| [PT/test_event_planner.py:63](../../../copilot-sdk/apps/purchasing/backend/tests/test_event_planner.py#L63) | 70, 79, 87 |
| [PT/test_evidence.py:52](../../../copilot-sdk/apps/purchasing/backend/tests/test_evidence.py#L52) | 67, 78, 90, 103, 117, 137, 153 |
| [PT/test_evolution_purchasing.py:170](../../../copilot-sdk/apps/purchasing/backend/tests/test_evolution_purchasing.py#L170) | — |
| [PT/test_iks_trust.py:152](../../../copilot-sdk/apps/purchasing/backend/tests/test_iks_trust.py#L152) | — |
| [PT/test_inventory_summary.py:9](../../../copilot-sdk/apps/purchasing/backend/tests/test_inventory_summary.py#L9) | 37, 47, 59 |
| [PT/test_learning_beats.py:4](../../../copilot-sdk/apps/purchasing/backend/tests/test_learning_beats.py#L4) | 13, 22 |
| [PT/test_match_queue.py:186](../../../copilot-sdk/apps/purchasing/backend/tests/test_match_queue.py#L186) | 219 |
| [PT/test_menu_engineer.py:74](../../../copilot-sdk/apps/purchasing/backend/tests/test_menu_engineer.py#L74) | 83, 91 |
| [PT/test_multi_unit.py:100](../../../copilot-sdk/apps/purchasing/backend/tests/test_multi_unit.py#L100) | 107 |
| [PT/test_par_optimizer.py:13](../../../copilot-sdk/apps/purchasing/backend/tests/test_par_optimizer.py#L13) | — |
| [PT/test_pos_router.py:10](../../../copilot-sdk/apps/purchasing/backend/tests/test_pos_router.py#L10) | — |
| [PT/test_predictive_par.py:79](../../../copilot-sdk/apps/purchasing/backend/tests/test_predictive_par.py#L79) | 88, 153, 170 |
| [PT/test_purchasing_active_age_live.py:33](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_active_age_live.py#L33) | — |
| [PT/test_purchasing_backend.py:70](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_backend.py#L70) | 82, 93, 104, 119, 135, 145, 155, 164, 185, 216, 249, 269, 280, 296, 309, 319, 353, 361, 431, 468, 546, 559, 566, 585, 594, 605, 616, 643, 654, 663, 672, 681, 690, 748, 794, 814, 824, 834 |
| [PT/test_purchasing_config_migration.py:158](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_config_migration.py#L158) | — |
| [PT/test_purchasing_control.py:73](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_control.py#L73) | 89, 96, 105, 125 |
| [PT/test_purchasing_graph_status.py:33](../../../copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py#L33) | 56, 182, 209, 240, 267, 279 |
| [PT/test_qbo_connector.py:16](../../../copilot-sdk/apps/purchasing/backend/tests/test_qbo_connector.py#L16) | — |
| [PT/test_scorecard.py:77](../../../copilot-sdk/apps/purchasing/backend/tests/test_scorecard.py#L77) | 84, 91, 179, 186, 194 |
| [PT/test_spend_dashboard.py:130](../../../copilot-sdk/apps/purchasing/backend/tests/test_spend_dashboard.py#L130) | — |
| [PT/test_trust_analysis.py:150](../../../copilot-sdk/apps/purchasing/backend/tests/test_trust_analysis.py#L150) | 156, 162 |
| [PT/test_verify.py:58](../../../copilot-sdk/apps/purchasing/backend/tests/test_verify.py#L58) | 72, 85, 97, 106, 112, 120, 128, 154, 169, 187, 220, 232, 252 |
| [PT/test_weather_factor.py:55](../../../copilot-sdk/apps/purchasing/backend/tests/test_weather_factor.py#L55) | — |


### Part C — continuation summary and ranked remediation sequence

| Count | Trading/Purchasing continuation | Including the earlier SOC report |
|---|---:|---:|
| Unique registered endpoint identities (counted per copilot) | **321** | **571** |
| Endpoint identities with no native frontend consumer found | **156** (81 + 75) | **295** (139 + 81 + 75) |
| Newly ranked MISSING_UI endpoint pairs | **23** | Prior SOC actionable count uses a different mixed-category denominator; do not add it to this row |
| Additional direct-monkeypatch-only BLOCKING compatibility hooks | **0 established** | **3** previously reported in SOC |
| BLOCKING ambient pytest configuration/demo sites | **9**, grouped as TP-B1 | **9 newly reviewed**; do not describe these as nine explicit monkeypatch calls |
| CIRCULAR/fixed-output tests | **3** (1 patched fallback + 2 injected-score assertions) | **6** with the earlier 3 SOC tests carried forward |
| STALE patch sites | **0 confirmed** | **2** earlier SOC sites, not re-audited |
| Additional shadowed route registrations | **3** (Trading 2, Purchasing 1) | **4** with earlier SOC evolution-summary collision |
| Additional active paths with configuration-dependent 404 behavior | **6** Purchasing demo-off paths | SOC authentication-origin issue remains a separate kind of defect |
| PREVIEW_ONLY exceptions found for Trading/Purchasing no-consumer endpoints | **0 found** | Earlier SOC-to-S2P references still need S2P-side continuation verification |
| Explicit patch operations individually indexed in this continuation | **203** | SOC/SDK full per-operation semantic classification remains incomplete |
| Application/test files changed; tests executed | **0; 0** | Documentation-only continuation |

Counts are scoped observations, not a claim that 295 endpoints are bugs or that all mocks in all repositories have been semantically reviewed. A backend adapter without a browser caller may remain a useful integration API. The detailed inventories show those undecided/API-only surfaces explicitly.

#### Top five by likelihood of concealing a bug or confusing a demo

1. **PUR-3 — missing matching submission plus synthetic successful results.** Both backend and frontend manufacture a successful match in the absence of actual results; this can make the unwired POST look functional.
2. **PUR-1 — proof/legal response contract mismatch.** Real nonzero backend proof data renders as zero because the panel bypasses normalization; evidence metadata has a second header/body contract gap.
3. **TP-B1 and earlier SOC B1/B2 — test-dependent production behavior.** In Trading/Purchasing, pytest changes runtime profile and demo availability at nine production sites. SOC's earlier factor/learning compatibility branches are still outstanding. These splits limit what green test suites establish about an ordinary application launch.
4. **PUR-2 — unsupported time/coverage claims.** Mounted panels request existing endpoints but expect fields that those contracts do not contain, then show unavailable states or fixed numeric claims.
5. **PUR-4/PUR-5 — incomplete visible lifecycles.** The UI can enable auto-ordering without evaluating an order and can display a frozen-twin status without creating or comparing its baseline.

These rankings prioritize confirmed source behavior over raw numbers of unused routes. Trading journal editing (TRD-1), duplicate route ownership (TRD-2), and the circular fallback test (TP-B2) follow closely.

#### Recommended Codex prompt sequence (group by blast radius)

| Order | Fix together | Scope and required proof |
|---|---|---|
| 1 | Purchasing response contracts: PUR-1/PUR-2, plus honest match empty-state rendering from PUR-3 | Typed api.ts clients and the affected proof/competence/not-yet/match panels; use real response fixtures captured from defined contracts and assert populated, zero, unavailable, and explicitly labelled example states. Do not replace missing fields with invented measurements. |
| 2 | Explicit runtime/demo configuration: TP-B1 and PUR-7 | Trading/Purchasing app factories, Trading CLI/context, Purchasing discovery/POS/spend/commodity providers and their test fixtures. Supply real isolated stores and explicit settings before removing pytest detection; verify demo-on and demo-off assembled applications. Audit DataOps/S2P before extending this cross-copilot migration. |
| 3 | Purchasing matching, auto-order and event feedback: PUR-3/PUR-4/PUR-6 | Connect POSTs to concrete user workflows or an explicitly documented external scheduler; preserve conservation, evidence and approval controls. Replace fixed-output scoring assertions with real scorer/store coverage while preserving useful adapter checks. |
| 4 | Purchasing baseline/handoff/authority: PUR-5/PUR-8/PUR-9 | Treat freeze-once, compare, export and explicit advancement as separate user-authorized operations with typed contracts. Verify their complete read/write/read lifecycles. |
| 5 | Trading native workflow gaps: TRD-1, then TRD-3/TRD-4 if retained in product scope | Journal editing first; decide social/profile and variant workflows before adding panels. Keep parameter evolution distinct from variant generation/promotion. |
| 6 | Route ownership and test cleanup: TRD-2/TRD-5, Purchasing health shadowing, TP-B2, earlier SOC summary collision | Remove/rename duplicate or misspelled registrations only after confirming external clients and retaining the chosen contract. Assert registration uniqueness and exercise assembled-app routes; replace the missing-yfinance circular test with the real fallback. |
| 7 | DataOps and S2P discovery — subsequently completed | The continuation below includes both native inventories, the separate S2P backend, SOC preview cross-references and scoped mock findings. |

**Validation performed:** static Python/TypeScript source inspection; method/path comparison including dynamic paths, duplicate precedence and conditional registration; source-reference and Markdown-inventory checks. **No mypy, pytest, browser/load tests, live backend requests, or performance measurements were run.** This audit makes no “0 regressions” or live-endpoint-health claim.

**Files changed in this continuation:** only `copilot-sdk/docs/quality/frontend_wiring_and_mock_audit.md`. No fixes were implemented.

**Historical stopping point:** DataOps and S2P were pending at the end of the Trading/Purchasing run. Their completed continuation follows. Broader SOC/SDK/CI per-usage review and API-only ownership decisions remain separately scoped follow-up work.

---

## Continuation — DataOps and S2P (2026-09-06)

### Scope, method and completion

**DataOps and S2P source audits are complete for this continuation.** Work proceeded DataOps first, then S2P. Only this report is modified. No application/test files were changed; no git, test execution, application imports, live HTTP requests or database operations were used.

The audit followed each main.py router registration, resolved factory prefixes, inspected the native frontend import graph from main.tsx/App.tsx (including shared SDK components), separated unused api.ts exports, compared HTTP methods as well as dynamic paths, and checked the separate SOC preview origin. DataOps uses `copilot-sdk/apps/dataops/backend`; S2P uses `s2p-copilot/backend`, not an SDK backend folder. Both native frontends are under `copilot-sdk/apps/<copilot>/frontend`.

| Scope | Registered routes | Unique method/path pairs | Native call sites | Dormant frontend helpers | Unique endpoints without native callers | Preview-only exceptions |
|---|---:|---:|---:|---:|---:|---:|
| DataOps | 145 | 138 | 71 | 5 | 75 | 0 |
| S2P | 224 | 224 | 60 | 24 | 166 | 6 |
| This continuation | **369** | **362** | **131** | **29** | **241** | **6** |

S2P includes five SAML routes conditionally mounted when AUTH_ENABLED is enabled (`s2p-copilot/backend/app/main.py:288`). Without that option, it has 219 registrations. Framework-generated OpenAPI/docs routes are excluded. Counts are copilot-qualified: an SDK route mounted in two apps counts once for each app. The 241 no-native-consumer endpoints include six working cross-references to SOC preview and numerous operator/parallel adapters; **this is not a count of 241 UI bugs**. After preview exceptions, 235 endpoint identities have no browser consumer found in this scope.

DataOps has seven later shadowed registrations; S2P has no exact duplicate method/path registration. S2P's explicit trailing-slash supplier alias is a separate registration, not a duplicate. No active native method/path with no registered backend route was found. Two dormant S2P helpers would address absent routes if wired.

**Classification limits:** MISSING_UI, NAME_MISMATCH, DEAD_CODE and PREVIEW_ONLY are used where the source establishes them. API_ONLY means no browser consumer and no established product requirement: declaring a useful health, authentication, export, maintenance or integration API dead would be speculation. DEAD_CODE *candidate* identifies an unused browser alias/parallel adapter whose external clients still need an owner decision. Endpoint runtime health was not tested. The full route tables make these distinctions per endpoint rather than hiding them inside a single unused-endpoint count.

### Part A — ranked findings and complete inventories

<a id="dataops-findings"></a>

#### DOP-1 — P1 — NAME_MISMATCH / MISSING_UI

**Copilot:** DataOps. **Classification:** NAME_MISMATCH / MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/dataops/frozen-twin/status` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:75`.
- `POST /api/dataops/frozen-twin/freeze` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:79`.

**Finding:** The mounted Frozen Twin control reads cohort-status and labels instrument.validated as a pinned frozen checkpoint. That field validates an oracle experiment artifact; it does not read the governance FrozenTwin store. Neither the real status endpoint nor freeze action has a frontend caller.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/frontend/src/components/FrozenTwinControlPanel.tsx:7`; `copilot-sdk/apps/dataops/frontend/src/components/FrozenTwinControlPanel.tsx:8`; `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:65`.

**Recommended fix approach:** Use the governance snapshot status and add an explicit freeze action; keep cohort/instrument validation separate from frozen baseline state.

#### DOP-2 — P1 — MISSING_UI

**Copilot:** DataOps. **Classification:** MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `POST /api/dataops/holdout/register` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:42`.
- `POST /api/dataops/holdout/verify` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:50`.
- `GET /api/dataops/provenance/{decision_id}` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:57`.

**Finding:** The governance panel displays holdout entries and abstention, but never registers or verifies holdouts and has no decision-provenance drilldown. Abstention counts verified rows in the separate holdout table; normal score/learn calls do not populate it. No other application caller of register_holdout/verify_holdout was found beyond these router handlers.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/frontend/src/components/DataOpsGovernancePanel.tsx:10`; `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:73`; `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:107`.

**Recommended fix approach:** Connect score → holdout registration → expert verification → provenance review, or explicitly expose the separate operator ingestion workflow and its pending state.

#### DOP-3 — P2 — MISSING_UI

**Copilot:** DataOps. **Classification:** MISSING_UI. **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `POST /api/dataops/promotion` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:64`.
- `POST /api/dataops/promotion/{record_id}/advance` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:68`.

**Finding:** The governance API can create/read authority records and advance them, but no frontend reads or operates this lifecycle. The POST named promotion is stateful because it creates a missing record.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/frontend/src/components/DataOpsGovernancePanel.tsx:2`; `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:124`.

**Recommended fix approach:** Add typed authority-state and explicit advancement controls only if intended for users; preserve the observed-evidence and conservation gates.

#### DOP-4 — P2 — DEAD_CODE

**Copilot:** DataOps. **Classification:** DEAD_CODE. **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/health` — `copilot-sdk/copilot_sdk/backend/scoring_router.py:360`; `copilot-sdk/apps/dataops/backend/app/main.py:921`.
- `GET /api/di/profiles` — `copilot-sdk/apps/dataops/backend/app/main.py:783`; `copilot-sdk/copilot_sdk/backend/di_router.py:125`.
- `GET /api/dataops/di/profiles` — `copilot-sdk/apps/dataops/backend/app/main.py:787`; `copilot-sdk/copilot_sdk/backend/di_router.py:125`.
- `GET /api/di/intelligence-map` — `copilot-sdk/copilot_sdk/backend/di_router.py:220`; `copilot-sdk/apps/dataops/backend/app/main.py:880`.
- `GET /api/dataops/di/intelligence-map` — `copilot-sdk/copilot_sdk/backend/di_router.py:220`; `copilot-sdk/apps/dataops/backend/app/main.py:897`.
- `GET /api/dataops/di/acquisition-advice` — `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:54`; `copilot-sdk/copilot_sdk/backend/di_router.py:184`.
- `GET /api/dataops/enterprise-health` — `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:68`; `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:53`.

**Finding:** Seven exact method/path collisions shadow seven later registrations. Custom profiles win over SDK profiles; SDK intelligence maps win over the later custom cached/enriched handlers; DI demo-beat acquisition advice wins over the prefixed SDK version; status-router enterprise health wins over enterprise_router; SDK /api/health wins over the later custom alias. The app's getHealth uses /health, which remains reachable, so this is not an absent health API.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/backend/app/main.py:730`; `copilot-sdk/apps/dataops/backend/app/main.py:783`; `copilot-sdk/apps/dataops/backend/app/main.py:803`; `copilot-sdk/apps/dataops/backend/app/main.py:818`; `copilot-sdk/apps/dataops/backend/app/main.py:880`; `copilot-sdk/apps/dataops/frontend/src/api.ts:250`.

**Recommended fix approach:** Choose one owner/contract for each address and test the assembled application, including the custom enrichment/cache behavior that is currently unreachable by its intended URL.

#### DOP-5 — P1 — NAME_MISMATCH / MISSING_UI

**Copilot:** DataOps. **Classification:** NAME_MISMATCH / MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/di/sources` — `copilot-sdk/copilot_sdk/backend/di_router.py:140`.
- `POST /api/di/profile/{source_name}/refresh` — `copilot-sdk/copilot_sdk/backend/di_router.py:149`.
- `POST /api/dataops/di/profile/{source_name}/refresh` — `copilot-sdk/copilot_sdk/backend/di_router.py:149`.

**Finding:** Startup computes profiles into main.py's dataops_profiles, served by custom /api/di/profiles. The SourceCompounding panel instead calls /api/di/sources, whose SDK router owns an initially empty, separate cache. Only the unconsumed refresh POST fills that cache. Native-only usage therefore leaves source-profile quality pending despite available startup profiles; the second prefixed SDK router owns another independent cache.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/frontend/src/components/SourceCompoundingPanel.tsx:7`; `copilot-sdk/apps/dataops/backend/app/main.py:279`; `copilot-sdk/copilot_sdk/backend/di_router.py:74`; `copilot-sdk/copilot_sdk/backend/di_router.py:149`.

**Recommended fix approach:** Make profiles/sources share a single profile repository and expose refresh only if needed, then verify that both aliases and the source-compounding panel observe the same data.

#### DOP-6 — P1 — NAME_MISMATCH (failure-state contract)

**Copilot:** DataOps. **Classification:** NAME_MISMATCH (failure-state contract). **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/dataops/claims` — `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:34`.

**Finding:** The governance client converts request failure to null, and the panel converts null claims to zero failing claims, then displays 'Evidence gate clear'. This also happens initially before the request completes. Missing/unavailable evidence is conflated with a passing gate.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/frontend/src/components/DataOpsGovernancePanel.tsx:16`; `copilot-sdk/apps/dataops/frontend/src/components/DataOpsGovernancePanel.tsx:26`; `copilot-sdk/apps/dataops/frontend/src/api.ts:199`.

**Recommended fix approach:** Use explicit loading/unavailable/pass/fail states and only show a clear gate after a successful, validated claims response.

#### DOP-7 — P2 — DEAD_CODE (broken unused adapter)

**Copilot:** DataOps. **Classification:** DEAD_CODE (broken unused adapter). **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/dataops/di/frozen-twin` — `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:92`.

**Finding:** This unused adapter probes FrozenTwin.to_dict(), but the actual service provides is_frozen/get_snapshot and no to_dict method. Its frozen_state remains None, so even a frozen service is reported as not_frozen. Wiring the existing frontend to this similarly named adapter would introduce another incorrect status path.

**Frontend/service evidence checked:** `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:96`; `copilot-sdk/copilot_sdk/twin/service.py:17`; `copilot-sdk/copilot_sdk/twin/service.py:55`.

**Recommended fix approach:** Retire this adapter or implement it against the canonical snapshot contract before exposing it.

#### DataOps — every registered route and no-consumer diff

The table retains registration order and duplicate registrations. WIRED means a reachable native frontend call; PREVIEW_ONLY means only SOC preview consumes it. Every other row has no native consumer. For API_ONLY rows, the frontend evidence is the complete native call inventory below and the inspected screen import graph; no product requirement was found that justifies forcing the route into one of the four defect labels. DEAD_CODE candidates are browser cleanup candidates, not proof that an external integration is absent.

| Method/path | Backend file:line; main mount | Native/preview consumer evidence | Classification / severity | Recommended approach |
|---|---|---|---|---|
| `POST /api/score` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:203`; main.py:730 | `copilot-sdk/apps/dataops/frontend/src/api.ts:841` (scoreAlert) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/learn` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:243`; main.py:730 | `copilot-sdk/apps/dataops/frontend/src/api.ts:846` (learnAlert) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/fingerprint` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:345`; main.py:730 | `copilot-sdk/apps/dataops/frontend/src/api.ts:756` (getFingerprint) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/trajectory` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:353`; main.py:730 | `copilot-sdk/apps/dataops/frontend/src/api.ts:490` (getTrajectory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/health` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:360`; main.py:730 | `copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx:89` (DayZeroPanel) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/diagnostics` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:369`; main.py:730 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/history` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:387`; main.py:730 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/measurement-state` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:402`; main.py:730 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/{copilot}/measurement-state` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:407`; main.py:730 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/trust` | `copilot-sdk/apps/dataops/backend/app/routers/trust_router.py:22`; main.py:749 | `copilot-sdk/apps/dataops/frontend/src/api.ts:276` (fetchDataOpsTrust); `copilot-sdk/apps/dataops/frontend/src/api.ts:378` (getTrust) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/trust/verify` | `copilot-sdk/apps/dataops/backend/app/routers/di_gateway_router.py:22`; main.py:757 | `copilot-sdk/apps/dataops/frontend/src/api.ts:282` (fetchGatewayVerifications) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/dataops/di/earned-trust` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:42`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — parallel demo adapter, P2 | Native DI panels use profiles, sources, trust/verify and acquisitions; unify contracts before adding another caller. |
| `GET /api/dataops/di/acquisition-advice` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:54`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — parallel demo adapter, P2 | Native DI panels use profiles, sources, trust/verify and acquisitions; unify contracts before adding another caller. |
| `GET /api/dataops/di/abstention` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:72`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — parallel demo adapter, P2 | Native DI panels use profiles, sources, trust/verify and acquisitions; unify contracts before adding another caller. |
| `GET /api/dataops/di/trust-gateway` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:77`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — parallel demo adapter, P2 | Native DI panels use profiles, sources, trust/verify and acquisitions; unify contracts before adding another caller. |
| `GET /api/dataops/di/source-compounding` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:86`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — parallel demo adapter, P2 | Native DI panels use profiles, sources, trust/verify and acquisitions; unify contracts before adding another caller. |
| `GET /api/dataops/di/frozen-twin` | `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:92`; main.py:764 | None in native import graph; no cross-copilot preview found | DEAD_CODE (broken unused adapter) — P2 | DOP-7: Retire this adapter or implement it against the canonical snapshot contract before exposing it. |
| `GET /api/dataops/claims` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:34`; main.py:772 | `copilot-sdk/apps/dataops/frontend/src/api.ts:88` (fetchDataOpsGovernance) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/dataops/abstention-check` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:38`; main.py:772 | `copilot-sdk/apps/dataops/frontend/src/api.ts:96` (fetchDataOpsAbstention); `copilot-sdk/apps/dataops/frontend/src/api.ts:298` (fetchAbstentionState) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/dataops/holdout/register` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:42`; main.py:772 | None in native import graph; no cross-copilot preview found | MISSING_UI — P1 | DOP-2: Connect score → holdout registration → expert verification → provenance review, or explicitly expose the separate operator ingestion workflow and its pending state. |
| `GET /api/dataops/holdout/status` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:46`; main.py:772 | `copilot-sdk/apps/dataops/frontend/src/api.ts:92` (fetchDataOpsHoldout) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/dataops/holdout/verify` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:50`; main.py:772 | None in native import graph; no cross-copilot preview found | MISSING_UI — P1 | DOP-2: Connect score → holdout registration → expert verification → provenance review, or explicitly expose the separate operator ingestion workflow and its pending state. |
| `GET /api/dataops/provenance/{decision_id}` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:57`; main.py:772 | None in native import graph; no cross-copilot preview found | MISSING_UI — P1 | DOP-2: Connect score → holdout registration → expert verification → provenance review, or explicitly expose the separate operator ingestion workflow and its pending state. |
| `POST /api/dataops/promotion` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:64`; main.py:772 | None in native import graph; no cross-copilot preview found | MISSING_UI — P2 | DOP-3: Add typed authority-state and explicit advancement controls only if intended for users; preserve the observed-evidence and conservation gates. |
| `POST /api/dataops/promotion/{record_id}/advance` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:68`; main.py:772 | None in native import graph; no cross-copilot preview found | MISSING_UI — P2 | DOP-3: Add typed authority-state and explicit advancement controls only if intended for users; preserve the observed-evidence and conservation gates. |
| `GET /api/dataops/frozen-twin/status` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:75`; main.py:772 | None in native import graph; no cross-copilot preview found | NAME_MISMATCH / MISSING_UI — P1 | DOP-1: Use the governance snapshot status and add an explicit freeze action; keep cohort/instrument validation separate from frozen baseline state. |
| `POST /api/dataops/frozen-twin/freeze` | `copilot-sdk/apps/dataops/backend/app/routers/governance_router.py:79`; main.py:772 | None in native import graph; no cross-copilot preview found | NAME_MISMATCH / MISSING_UI — P1 | DOP-1: Use the governance snapshot status and add an explicit freeze action; keep cohort/instrument validation separate from frozen baseline state. |
| `GET /api/dataops/situation` | `copilot-sdk/apps/dataops/backend/app/routers/regime_router.py:18`; main.py:773 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/transfer/status` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:52`; main.py:774 | `copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx:23` (TransferBadge) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/transfer/opportunities` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:58`; main.py:774 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/transfer/demo` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:85`; main.py:774 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/transfer/execute` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:109`; main.py:774 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/transfers` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:237`; main.py:775 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/transfer` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:264`; main.py:775 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/conservation/status` | `copilot-sdk/copilot_sdk/backend/conservation_router.py:42`; main.py:776 | `copilot-sdk/apps/dataops/frontend/src/api.ts:470` (getConservationStatus); `copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx:90` (DayZeroPanel) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/conservation/what-if` | `copilot-sdk/copilot_sdk/backend/conservation_router.py:56`; main.py:776 | `copilot-sdk/apps/dataops/frontend/src/api.ts:481` (postConservationWhatIf) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/profiles` | `copilot-sdk/apps/dataops/backend/app/main.py:783` | `copilot-sdk/apps/dataops/frontend/src/api.ts:254` (fetchDIProfiles) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/dataops/di/profiles` | `copilot-sdk/apps/dataops/backend/app/main.py:787` | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/di/acquisitions` | `copilot-sdk/apps/dataops/backend/app/main.py:791` | `copilot-sdk/apps/dataops/frontend/src/components/AcquisitionPanel.tsx:42` (load) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/profiles` | `copilot-sdk/copilot_sdk/backend/di_router.py:125`; main.py:803 | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /api/di/sources` | `copilot-sdk/copilot_sdk/backend/di_router.py:140`; main.py:803 | `copilot-sdk/apps/dataops/frontend/src/api.ts:272` (fetchSourceCounts) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/profile/{source_name}` | `copilot-sdk/copilot_sdk/backend/di_router.py:145`; main.py:803 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/di/profile/{source_name}/refresh` | `copilot-sdk/copilot_sdk/backend/di_router.py:149`; main.py:803 | None in native import graph; no cross-copilot preview found | NAME_MISMATCH / MISSING_UI — P1 | DOP-5: Make profiles/sources share a single profile repository and expose refresh only if needed, then verify that both aliases and the source-compounding panel observe the same data. |
| `GET /api/di/combinations` | `copilot-sdk/copilot_sdk/backend/di_router.py:168`; main.py:803 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/di/acquisition-advice` | `copilot-sdk/copilot_sdk/backend/di_router.py:184`; main.py:803 | `copilot-sdk/apps/dataops/frontend/src/api.ts:268` (fetchAcquisitionAdvice); `copilot-sdk/apps/dataops/frontend/src/components/IntelligenceMapPanel.tsx:73` (fetchAcquisitionAdvice) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/valuation` | `copilot-sdk/copilot_sdk/backend/di_router.py:190`; main.py:803 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/di/intelligence-map` | `copilot-sdk/copilot_sdk/backend/di_router.py:220`; main.py:803 | `copilot-sdk/apps/dataops/frontend/src/api.ts:309` (fetchDIIntelligenceMap) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/di/query` | `copilot-sdk/copilot_sdk/backend/di_router.py:272`; main.py:803 | `copilot-sdk/apps/dataops/frontend/src/api.ts:302` (queryDataOps) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/search` | `copilot-sdk/copilot_sdk/backend/di_router.py:281`; main.py:803 | `copilot-sdk/apps/dataops/frontend/src/api.ts:260` (searchDIAssets) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/catalog` | `copilot-sdk/copilot_sdk/backend/di_router.py:303`; main.py:803 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/di/catalog/{provider_id}` | `copilot-sdk/copilot_sdk/backend/di_router.py:313`; main.py:803 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/di/profiles` | `copilot-sdk/copilot_sdk/backend/di_router.py:125`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /api/dataops/di/sources` | `copilot-sdk/copilot_sdk/backend/di_router.py:140`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — unused browser alias, P2 | Native UI uses GET /api/di/sources; confirm external compatibility needs before retiring this alias. |
| `GET /api/dataops/di/profile/{source_name}` | `copilot-sdk/copilot_sdk/backend/di_router.py:145`; main.py:818 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/dataops/di/profile/{source_name}/refresh` | `copilot-sdk/copilot_sdk/backend/di_router.py:149`; main.py:818 | None in native import graph; no cross-copilot preview found | NAME_MISMATCH / MISSING_UI — P1 | DOP-5: Make profiles/sources share a single profile repository and expose refresh only if needed, then verify that both aliases and the source-compounding panel observe the same data. |
| `GET /api/dataops/di/combinations` | `copilot-sdk/copilot_sdk/backend/di_router.py:168`; main.py:818 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/di/acquisition-advice` | `copilot-sdk/copilot_sdk/backend/di_router.py:184`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /api/dataops/di/valuation` | `copilot-sdk/copilot_sdk/backend/di_router.py:190`; main.py:818 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/di/intelligence-map` | `copilot-sdk/copilot_sdk/backend/di_router.py:220`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — unused browser alias, P2 | Native UI uses GET /api/di/intelligence-map; confirm external compatibility needs before retiring this alias. |
| `POST /api/dataops/di/query` | `copilot-sdk/copilot_sdk/backend/di_router.py:272`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — unused browser alias, P2 | Native UI uses POST /api/di/query; confirm external compatibility needs before retiring this alias. |
| `GET /api/dataops/di/search` | `copilot-sdk/copilot_sdk/backend/di_router.py:281`; main.py:818 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — unused browser alias, P2 | Native UI uses GET /api/di/search; confirm external compatibility needs before retiring this alias. |
| `GET /api/dataops/di/catalog` | `copilot-sdk/copilot_sdk/backend/di_router.py:303`; main.py:818 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/di/catalog/{provider_id}` | `copilot-sdk/copilot_sdk/backend/di_router.py:313`; main.py:818 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/di/sources/{source_id}/consumers` | `copilot-sdk/apps/dataops/backend/app/routers/di_enrichment_router.py:28`; main.py:831 | `copilot-sdk/apps/dataops/frontend/src/api.ts:318` (fetchDISourceConsumers) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/sources/{source_id}/trust` | `copilot-sdk/apps/dataops/backend/app/routers/di_enrichment_router.py:36`; main.py:831 | `copilot-sdk/apps/dataops/frontend/src/api.ts:314` (fetchDISourceTrust) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/products` | `copilot-sdk/apps/dataops/backend/app/routers/di_enrichment_router.py:62`; main.py:831 | `copilot-sdk/apps/dataops/frontend/src/api.ts:264` (fetchDIProducts) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/discovery/sweep` | `copilot-sdk/copilot_sdk/backend/discovery_router.py:23`; main.py:838 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/discovery/digest` | `copilot-sdk/copilot_sdk/backend/discovery_router.py:31`; main.py:838 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/discovery/alerts` | `copilot-sdk/copilot_sdk/backend/discovery_router.py:43`; main.py:838 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/discovery/cross-system` | `copilot-sdk/copilot_sdk/backend/discovery_router.py:51`; main.py:838 | `copilot-sdk/apps/dataops/frontend/src/api.ts:425` (getCrossSystemInsights); `copilot-sdk/apps/dataops/frontend/src/components/EnterpriseValueCard.tsx:85` (EnterpriseValueCard) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/perturb/status` | `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:29`; main.py:839 | `copilot-sdk/apps/dataops/frontend/src/api.ts:386` (getDIPerturbationStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/di/perturb` | `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:33`; main.py:839 | `copilot-sdk/apps/dataops/frontend/src/api.ts:395` (perturbDI) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/di/perturb/revert` | `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:49`; main.py:839 | `copilot-sdk/apps/dataops/frontend/src/api.ts:399` (revertDIPerturbation) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/evolution/variants` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:79`; main.py:846 | `copilot-sdk/apps/dataops/frontend/src/api.ts:760` (getEvolutionVariants) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/evolution/history` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:108`; main.py:846 | `copilot-sdk/apps/dataops/frontend/src/api.ts:812` (getEvolutionHistory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/evolution/promoted` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:124`; main.py:846 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — dormant helper/adapter, P2 | Remove unused wrapper/adapter only after checking other API clients; native panels use another contract. |
| `GET /api/evolution/summary` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:141`; main.py:846 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/evolution/record-outcome` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:169`; main.py:846 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/evolution/check-promotion` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:192`; main.py:846 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:107`; main.py:854 | `copilot-sdk/apps/dataops/frontend/src/api.ts:503` (getCentroidHistory); `copilot-sdk/apps/dataops/frontend/src/api.ts:579` (fetchCentroidHistory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/self/centroid-timeline` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:154`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/regime-reinit` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:163`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/evolution/summary` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:181`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/diagnostics` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:189`; main.py:854 | `copilot-sdk/apps/dataops/frontend/src/api.ts:382` (getSelfDiagnostics) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/self/centroid-history/{checkpoint_id}/counterfactual` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:221`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history/{checkpoint_id}/lineage` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:337`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history/{checkpoint_id}/replay` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:348`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/replay-score` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:368`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/decisions/{decision_id}/checkpoints` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:413`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/accuracy-by-category` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:422`; main.py:854 | `copilot-sdk/apps/dataops/frontend/src/api.ts:585` (fetchAccuracyByCategory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/self/accuracy-alerts` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:457`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/trust-traps` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:465`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/rollback` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:471`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/decisions` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:481`; main.py:854 | `copilot-sdk/apps/dataops/frontend/src/api.ts:740` (fetchDecisions) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/self/rule-genealogy` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:508`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/rule-lifecycle/{rule_id}` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:514`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/audit-trail` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:525`; main.py:854 | `copilot-sdk/apps/dataops/frontend/src/api.ts:619` (fetchAuditTrail) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/self/decision-flow` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:556`; main.py:854 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/context/pipelines` | `copilot-sdk/apps/dataops/backend/app/context_router.py:751`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:322` (getPipelines) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/enterprise-health` | `copilot-sdk/apps/dataops/backend/app/context_router.py:756`; main.py:862 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/context/sap/purchase-orders` | `copilot-sdk/apps/dataops/backend/app/context_router.py:775`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:679` (fetchSapPurchaseOrders) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/celonis/process-data` | `copilot-sdk/apps/dataops/backend/app/context_router.py:785`; main.py:862 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — dormant helper/adapter, P2 | Remove unused wrapper/adapter only after checking other API clients; native panels use another contract. |
| `GET /api/context/alerts` | `copilot-sdk/apps/dataops/backend/app/context_router.py:814`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:327` (getAlerts) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/alert-groups` | `copilot-sdk/apps/dataops/backend/app/context_router.py:825`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:332` (getAlertGroups); `copilot-sdk/apps/dataops/frontend/src/components/CrossGraphInsightCard.tsx:158` (loadDefaultInsight) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/system/{name}/history` | `copilot-sdk/apps/dataops/backend/app/context_router.py:912`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:689` (getSystemHistory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/decisions` | `copilot-sdk/apps/dataops/backend/app/context_router.py:970`; main.py:862 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — dormant helper/adapter, P2 | Remove unused wrapper/adapter only after checking other API clients; native panels use another contract. |
| `GET /api/context/accuracy-by-category` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1000`; main.py:862 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — dormant helper/adapter, P2 | Remove unused wrapper/adapter only after checking other API clients; native panels use another contract. |
| `GET /api/context/transformations/{system}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1042`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:589` (getTransformations) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/bottleneck/{system}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1053`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:593` (getBottleneck) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/schema-impact/{system}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1089`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:602` (getSchemaImpact) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/process-timeline` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1109`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/components/ProcessTimelinePanel.tsx:15` (ProcessTimelinePanel) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/cross-graph-insight/{alert_id}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1217`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:465` (getCrossGraphInsight); `copilot-sdk/apps/dataops/frontend/src/components/CrossGraphInsightCard.tsx:147` (loadInsight) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/context/apply-fix` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1318`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:854` (applyFix) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/system/{name}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1347`; main.py:862 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/context/alert/{id}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1352`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:606` (getAlert) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/alert/{id}/deps` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1372`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:623` (getAlertDeps) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/alert/{id}/recurrence` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1377`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:627` (getAlertRecurrence) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/alert/{id}/factors` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1382`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:632` (getAlertFactors) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/similar` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1387`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:646` (getSimilar) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/process-signals/{system}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1441`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:650` (getProcessSignals) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/audit-trail/{alert_id}` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1489`; main.py:862 | None in native import graph; no cross-copilot preview found | DEAD_CODE candidate — dormant helper/adapter, P2 | Remove unused wrapper/adapter only after checking other API clients; native panels use another contract. |
| `POST /api/context/alert-metadata` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1608`; main.py:862 | `copilot-sdk/apps/dataops/frontend/src/api.ts:850` (saveAlertMetadata) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/context/alert-metadata` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1625`; main.py:862 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/ae/recommendation/{alert_id}` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:388`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:744` (getAeRecommendation) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/impact` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:429`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:336` (getAeImpact) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/pattern-origin` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:433`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:748` (getPatternOrigin) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/rule-lifecycle` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:485`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:833` (getRuleLifecycle) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/operational-rules` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:509`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:837` (getOperationalRules) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/incident` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:537`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:752` (getIncident) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/conservation-history` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:550`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:340` (getConservationHistory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/ae/transfer-status` | `copilot-sdk/apps/dataops/backend/app/ae_router.py:554`; main.py:863 | `copilot-sdk/apps/dataops/frontend/src/api.ts:344` (getTransferStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/dataops/graph/status` | `copilot-sdk/apps/dataops/backend/app/graph_status.py:418`; main.py:870 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/health` | `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:22`; main.py:871 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/celonis/status` | `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:58`; main.py:871 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/sap/status` | `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:63`; main.py:871 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/enterprise-health` | `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:68`; main.py:871 | `copilot-sdk/apps/dataops/frontend/src/api.ts:655` (fetchEnterpriseHealth) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/dataops/enterprise-health` | `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:53`; main.py:872 | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /api/dataops/process-data` | `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:57`; main.py:872 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/sap-data` | `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:61`; main.py:872 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/dataops/query` | `copilot-sdk/apps/dataops/backend/app/routers/query.py:29`; main.py:873 | None in native import graph; no cross-copilot preview found | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/dataops/cohort-status` | `copilot-sdk/apps/dataops/backend/app/routers/cohort_status_router.py:19`; main.py:876 | `copilot-sdk/apps/dataops/frontend/src/api.ts:460` (getCohortStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/di/intelligence-map` | `copilot-sdk/apps/dataops/backend/app/main.py:880` | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /api/dataops/di/intelligence-map` | `copilot-sdk/apps/dataops/backend/app/main.py:897` | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |
| `GET /health` | `copilot-sdk/apps/dataops/backend/app/main.py:920` | `copilot-sdk/apps/dataops/frontend/src/api.ts:250` (getHealth) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/health` | `copilot-sdk/apps/dataops/backend/app/main.py:921` | None in native import graph; no cross-copilot preview found | DEAD_CODE — shadowed, P2 | DOP-4; choose one canonical registration. |

#### DataOps — every reachable frontend API call site

Entries are static call sites, not requests per page or test. Repeated calls to one URL and shared mounted SDK components are retained. Query strings are omitted for route identity; their source literals remain visible at the cited lines. Unused api.ts exports are excluded from the consumer count and listed separately.

| Method/path | Frontend file:line | Calling helper/component |
|---|---|---|
| `GET /api/dataops/claims` | `copilot-sdk/apps/dataops/frontend/src/api.ts:88` | `fetchDataOpsGovernance` |
| `GET /api/dataops/holdout/status` | `copilot-sdk/apps/dataops/frontend/src/api.ts:92` | `fetchDataOpsHoldout` |
| `GET /api/dataops/abstention-check` | `copilot-sdk/apps/dataops/frontend/src/api.ts:96` | `fetchDataOpsAbstention` |
| `GET /api/di/profiles` | `copilot-sdk/apps/dataops/frontend/src/api.ts:254` | `fetchDIProfiles` |
| `GET /api/di/search` | `copilot-sdk/apps/dataops/frontend/src/api.ts:260` | `searchDIAssets` |
| `GET /api/di/products` | `copilot-sdk/apps/dataops/frontend/src/api.ts:264` | `fetchDIProducts` |
| `GET /api/di/acquisition-advice` | `copilot-sdk/apps/dataops/frontend/src/api.ts:268` | `fetchAcquisitionAdvice` |
| `GET /api/di/sources` | `copilot-sdk/apps/dataops/frontend/src/api.ts:272` | `fetchSourceCounts` |
| `GET /api/dataops/trust` | `copilot-sdk/apps/dataops/frontend/src/api.ts:276` | `fetchDataOpsTrust` |
| `GET /api/di/trust/verify` | `copilot-sdk/apps/dataops/frontend/src/api.ts:282` | `fetchGatewayVerifications` |
| `GET /api/dataops/abstention-check` | `copilot-sdk/apps/dataops/frontend/src/api.ts:298` | `fetchAbstentionState` |
| `POST /api/di/query` | `copilot-sdk/apps/dataops/frontend/src/api.ts:302` | `queryDataOps` |
| `GET /api/di/intelligence-map` | `copilot-sdk/apps/dataops/frontend/src/api.ts:309` | `fetchDIIntelligenceMap` |
| `GET /api/di/sources/{}/trust` | `copilot-sdk/apps/dataops/frontend/src/api.ts:314` | `fetchDISourceTrust` |
| `GET /api/di/sources/{}/consumers` | `copilot-sdk/apps/dataops/frontend/src/api.ts:318` | `fetchDISourceConsumers` |
| `GET /api/context/pipelines` | `copilot-sdk/apps/dataops/frontend/src/api.ts:322` | `getPipelines` |
| `GET /api/context/alerts` | `copilot-sdk/apps/dataops/frontend/src/api.ts:327` | `getAlerts` |
| `GET /api/context/alert-groups` | `copilot-sdk/apps/dataops/frontend/src/api.ts:332` | `getAlertGroups` |
| `GET /api/ae/impact` | `copilot-sdk/apps/dataops/frontend/src/api.ts:336` | `getAeImpact` |
| `GET /api/ae/conservation-history` | `copilot-sdk/apps/dataops/frontend/src/api.ts:340` | `getConservationHistory` |
| `GET /api/ae/transfer-status` | `copilot-sdk/apps/dataops/frontend/src/api.ts:344` | `getTransferStatus` |
| `GET /api/dataops/trust` | `copilot-sdk/apps/dataops/frontend/src/api.ts:378` | `getTrust` |
| `GET /api/self/diagnostics` | `copilot-sdk/apps/dataops/frontend/src/api.ts:382` | `getSelfDiagnostics` |
| `GET /api/di/perturb/status` | `copilot-sdk/apps/dataops/frontend/src/api.ts:386` | `getDIPerturbationStatus` |
| `POST /api/di/perturb` | `copilot-sdk/apps/dataops/frontend/src/api.ts:395` | `perturbDI` |
| `POST /api/di/perturb/revert` | `copilot-sdk/apps/dataops/frontend/src/api.ts:399` | `revertDIPerturbation` |
| `GET /api/discovery/cross-system` | `copilot-sdk/apps/dataops/frontend/src/api.ts:425` | `getCrossSystemInsights` |
| `GET /api/dataops/cohort-status` | `copilot-sdk/apps/dataops/frontend/src/api.ts:460` | `getCohortStatus` |
| `GET /api/context/cross-graph-insight/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:465` | `getCrossGraphInsight` |
| `GET /api/conservation/status` | `copilot-sdk/apps/dataops/frontend/src/api.ts:470` | `getConservationStatus` |
| `POST /api/conservation/what-if` | `copilot-sdk/apps/dataops/frontend/src/api.ts:481` | `postConservationWhatIf` |
| `GET /api/trajectory` | `copilot-sdk/apps/dataops/frontend/src/api.ts:490` | `getTrajectory` |
| `GET /api/self/centroid-history` | `copilot-sdk/apps/dataops/frontend/src/api.ts:503` | `getCentroidHistory` |
| `GET /api/self/centroid-history` | `copilot-sdk/apps/dataops/frontend/src/api.ts:579` | `fetchCentroidHistory` |
| `GET /api/self/accuracy-by-category` | `copilot-sdk/apps/dataops/frontend/src/api.ts:585` | `fetchAccuracyByCategory` |
| `GET /api/context/transformations/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:589` | `getTransformations` |
| `GET /api/context/bottleneck/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:593` | `getBottleneck` |
| `GET /api/context/schema-impact/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:602` | `getSchemaImpact` |
| `GET /api/context/alert/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:606` | `getAlert` |
| `GET /api/self/audit-trail` | `copilot-sdk/apps/dataops/frontend/src/api.ts:619` | `fetchAuditTrail` |
| `GET /api/context/alert/{}/deps` | `copilot-sdk/apps/dataops/frontend/src/api.ts:623` | `getAlertDeps` |
| `GET /api/context/alert/{}/recurrence` | `copilot-sdk/apps/dataops/frontend/src/api.ts:627` | `getAlertRecurrence` |
| `GET /api/context/alert/{}/factors` | `copilot-sdk/apps/dataops/frontend/src/api.ts:632` | `getAlertFactors` |
| `GET /api/context/similar` | `copilot-sdk/apps/dataops/frontend/src/api.ts:646` | `getSimilar` |
| `GET /api/context/process-signals/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:650` | `getProcessSignals` |
| `GET /api/dataops/enterprise-health` | `copilot-sdk/apps/dataops/frontend/src/api.ts:655` | `fetchEnterpriseHealth` |
| `GET /api/context/sap/purchase-orders` | `copilot-sdk/apps/dataops/frontend/src/api.ts:679` | `fetchSapPurchaseOrders` |
| `GET /api/context/system/{}/history` | `copilot-sdk/apps/dataops/frontend/src/api.ts:689` | `getSystemHistory` |
| `GET /api/self/decisions` | `copilot-sdk/apps/dataops/frontend/src/api.ts:740` | `fetchDecisions` |
| `GET /api/ae/recommendation/{}` | `copilot-sdk/apps/dataops/frontend/src/api.ts:744` | `getAeRecommendation` |
| `GET /api/ae/pattern-origin` | `copilot-sdk/apps/dataops/frontend/src/api.ts:748` | `getPatternOrigin` |
| `GET /api/ae/incident` | `copilot-sdk/apps/dataops/frontend/src/api.ts:752` | `getIncident` |
| `GET /api/fingerprint` | `copilot-sdk/apps/dataops/frontend/src/api.ts:756` | `getFingerprint` |
| `GET /api/evolution/variants` | `copilot-sdk/apps/dataops/frontend/src/api.ts:760` | `getEvolutionVariants` |
| `GET /api/evolution/history` | `copilot-sdk/apps/dataops/frontend/src/api.ts:812` | `getEvolutionHistory` |
| `GET /api/ae/rule-lifecycle` | `copilot-sdk/apps/dataops/frontend/src/api.ts:833` | `getRuleLifecycle` |
| `GET /api/ae/operational-rules` | `copilot-sdk/apps/dataops/frontend/src/api.ts:837` | `getOperationalRules` |
| `POST /api/score` | `copilot-sdk/apps/dataops/frontend/src/api.ts:841` | `scoreAlert` |
| `POST /api/learn` | `copilot-sdk/apps/dataops/frontend/src/api.ts:846` | `learnAlert` |
| `POST /api/context/alert-metadata` | `copilot-sdk/apps/dataops/frontend/src/api.ts:850` | `saveAlertMetadata` |
| `POST /api/context/apply-fix` | `copilot-sdk/apps/dataops/frontend/src/api.ts:854` | `applyFix` |
| `GET /api/transfer/status` | `copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx:23` | `TransferBadge` |
| `GET /api/discovery/cross-system` | `copilot-sdk/apps/dataops/frontend/src/components/EnterpriseValueCard.tsx:85` | `EnterpriseValueCard` |
| `GET /api/context/process-timeline` | `copilot-sdk/apps/dataops/frontend/src/components/ProcessTimelinePanel.tsx:15` | `ProcessTimelinePanel` |
| `GET /api/di/acquisition-advice` | `copilot-sdk/apps/dataops/frontend/src/components/IntelligenceMapPanel.tsx:73` | `fetchAcquisitionAdvice` |
| `GET /api/health` | `copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx:89` | `DayZeroPanel` |
| `GET /api/conservation/status` | `copilot-sdk/copilot_sdk/frontend/DayZeroPanel.tsx:90` | `DayZeroPanel` |
| `GET /api/context/cross-graph-insight/{}` | `copilot-sdk/apps/dataops/frontend/src/components/CrossGraphInsightCard.tsx:147` | `loadInsight` |
| `GET /api/context/alert-groups` | `copilot-sdk/apps/dataops/frontend/src/components/CrossGraphInsightCard.tsx:158` | `loadDefaultInsight` |
| `GET /api/dataops/di/acquisitions` | `copilot-sdk/apps/dataops/frontend/src/components/AcquisitionPanel.tsx:42` | `load` |
| `GET /health` | `copilot-sdk/apps/dataops/frontend/src/api.ts:250` | `getHealth` |

#### DataOps — dormant frontend helpers and reverse check

| Method/path | Unused helper; file:line | Backend registration |
|---|---|---|
| `GET /api/context/accuracy-by-category` | `getAccuracyByCategory` — `copilot-sdk/apps/dataops/frontend/src/api.ts:494` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1000` |
| `GET /api/context/audit-trail/{}` | `getAuditTrail` — `copilot-sdk/apps/dataops/frontend/src/api.ts:610` | `copilot-sdk/apps/dataops/backend/app/context_router.py:1489` |
| `GET /api/context/celonis/process-data` | `fetchProcessData` — `copilot-sdk/apps/dataops/frontend/src/api.ts:663` | `copilot-sdk/apps/dataops/backend/app/context_router.py:785` |
| `GET /api/context/decisions` | `getDecisions` — `copilot-sdk/apps/dataops/frontend/src/api.ts:717` | `copilot-sdk/apps/dataops/backend/app/context_router.py:970` |
| `GET /api/evolution/promoted` | `getPromotedEvolutionRules` — `copilot-sdk/apps/dataops/frontend/src/api.ts:816` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:124` |

**Active reverse diff:** no absent method/path registration found after resolving dynamic IDs, API bases, query suffixes and router prefixes. This is a static route check; auth, validation, absent record IDs and backend failures can still return errors. All five dormant helper URLs exist. Seven duplicate registrations require selecting the first mounted handler; /health remains available and is the URL used by getHealth().

<a id="s2p-findings"></a>

#### S2P-1 — P1 — MISSING_UI

**Copilot:** S2P. **Classification:** MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `POST /api/s2p/proposal` — `s2p-copilot/backend/app/routers/s2p_proposals.py:28`.
- `GET /api/s2p/proposal/{proposal_id}` — `s2p-copilot/backend/app/routers/s2p_proposals.py:40`.
- `GET /api/s2p/proposals` — `s2p-copilot/backend/app/routers/s2p_proposals.py:50`.
- `POST /api/s2p/proposal/{proposal_id}/confirm` — `s2p-copilot/backend/app/routers/s2p_proposals.py:60`.
- `POST /api/s2p/proposal/{proposal_id}/override` — `s2p-copilot/backend/app/routers/s2p_proposals.py:69`.
- `GET /api/s2p/proposal/{proposal_id}/audit` — `s2p-copilot/backend/app/routers/s2p_proposals.py:81`.
- `GET /api/s2p/ledger/timeline` — `s2p-copilot/backend/app/routers/s2p_ledger.py:15`.
- `GET /api/s2p/ledger/summary` — `s2p-copilot/backend/app/routers/s2p_ledger.py:20`.
- `GET /api/s2p/ledger/iks-trajectory` — `s2p-copilot/backend/app/routers/s2p_ledger.py:25`.
- `GET /api/s2p/ledger/conservation-history` — `s2p-copilot/backend/app/routers/s2p_ledger.py:30`.

**Finding:** Scoring automatically persists a proposal and returns proposal_id. Native confirm/override sends only decision_id to /api/learn; that handler never resolves or links the proposal. All proposal-review/resolve and ledger endpoints have no native or preview caller. Thus the normal browser outcome workflow leaves a separate proposal pending; the ledger integration test manually invokes proposal_service.confirm(), a step the browser never performs.

**Frontend/service evidence checked:** `s2p-copilot/backend/app/routers/s2p.py:2271`; `s2p-copilot/backend/app/routers/s2p.py:2404`; `copilot-sdk/apps/s2p/frontend/src/screens/TriageScreen.tsx:223`; `s2p-copilot/backend/tests/test_compounding_ledger.py:243`.

**Recommended fix approach:** Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice.

#### S2P-2 — P1 — NAME_MISMATCH / MISSING_UI

**Copilot:** S2P. **Classification:** NAME_MISMATCH / MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/s2p/twin/drift` — `s2p-copilot/backend/app/routers/s2p_autonomy.py:82`.
- `POST /api/s2p/twin/freeze` — `s2p-copilot/backend/app/routers/s2p_autonomy.py:89`.

**Finding:** The mounted panel expects frozen/live accuracy or baseline/current scores, but /twin/drift returns centroid_drift, weight_drift, conservation_drift, iks_delta and decision_count_since_freeze. No returned field can populate its accuracy curves. No UI calls freeze; the empty-state text also says 'The twin exists' even when status says not frozen or the status request failed.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:21`; `copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:27`; `copilot-sdk/apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx:52`; `s2p-copilot/backend/app/services/s2p_autonomy.py:142`; `copilot-sdk/copilot_sdk/twin/service.py:106`.

**Recommended fix approach:** Render the actual drift contract, distinguish missing/unavailable snapshots, and expose an explicit freeze action; introduce paired outcome accuracy only with a defined measured-data API.

#### S2P-3 — P1 — MISSING_UI

**Copilot:** S2P. **Classification:** MISSING_UI. **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/s2p/iks` — `s2p-copilot/backend/app/routers/s2p.py:2694`.

**Finding:** The native shell receives iks={0} permanently while a dedicated live /s2p/iks endpoint exists with no browser consumer. Performance trajectory is separately consumed, so this is specifically a stale shell metric, not a missing Performance tab.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/App.tsx:59`; `s2p-copilot/backend/app/routers/s2p.py:2694`.

**Recommended fix approach:** Read and refresh the typed S2P IKS observation for the shell, with an unavailable state rather than a fabricated zero.

#### S2P-4 — P1 — NAME_MISMATCH (failure-state contract)

**Copilot:** S2P. **Classification:** NAME_MISMATCH (failure-state contract). **Severity:** P1.

**Endpoint(s) and backend evidence:**

- `GET /api/s2p/preview/queue` — `s2p-copilot/backend/app/routers/s2p_preview.py:508`.

**Finding:** The active fetchPreviewQueue wrapper calls getPreviewQueue, which converts every HTTP/network failure into a successful empty queue with zero totals/rates. Triage's error handler therefore cannot distinguish unavailable data from no invoices; the strict helper exists but has no caller.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/api.ts:133`; `copilot-sdk/apps/s2p/frontend/src/api.ts:145`; `copilot-sdk/apps/s2p/frontend/src/screens/TriageScreen.tsx:118`; `copilot-sdk/apps/s2p/frontend/src/screens/TriageScreen.tsx:273`.

**Recommended fix approach:** Use the strict queue contract in native screens and explicitly render loading, empty and unavailable states; retain optional fallback only in a labelled optional preview.

#### S2P-5 — P2 — MISSING_UI

**Copilot:** S2P. **Classification:** MISSING_UI. **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/s2p/auto-approve/status` — `s2p-copilot/backend/app/routers/s2p_auto_approve.py:59`.
- `POST /api/s2p/auto-approve/enable` — `s2p-copilot/backend/app/routers/s2p_auto_approve.py:70`.
- `POST /api/s2p/auto-approve/disable` — `s2p-copilot/backend/app/routers/s2p_auto_approve.py:96`.
- `GET /api/s2p/auto-approve/audit` — `s2p-copilot/backend/app/routers/s2p_auto_approve.py:109`.
- `POST /api/s2p/auto-approve/evaluate` — `s2p-copilot/backend/app/routers/s2p_auto_approve.py:122`.

**Finding:** The native auto-approve panel consumes legacy stats and expansion proof. The separate P40B shadow gate's status, enable/disable, evaluation and audit contracts have no caller. The existing panel therefore does not operate or report this newer gate; no claim of missing production execution is made because the router explicitly supports shadow mode only.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/components/AutoApprovePanel.tsx:72`; `copilot-sdk/apps/s2p/frontend/src/components/AutoApprovePanel.tsx:101`; `s2p-copilot/backend/app/routers/s2p_auto_approve.py:18`.

**Recommended fix approach:** Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry.

#### S2P-6 — P2 — MISSING_UI

**Copilot:** S2P. **Classification:** MISSING_UI. **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `POST /api/s2p/promotion/{category}/advance` — `s2p-copilot/backend/app/routers/s2p_autonomy.py:39`.
- `POST /api/s2p/promotion/{category}/rollback` — `s2p-copilot/backend/app/routers/s2p_autonomy.py:52`.
- `POST /api/s2p/promotion/{category}/transfer` — `s2p-copilot/backend/app/routers/s2p_autonomy.py:65`.

**Finding:** Native panels read promotion state but cannot advance, roll back or transfer category authority. This autonomy lifecycle is distinct from the separately mounted rule evolution promotion-check.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/components/ExceptionExtinctionTimeline.tsx:24`; `copilot-sdk/apps/s2p/frontend/src/components/ConfidenceBandPanel.tsx:22`; `s2p-copilot/backend/app/routers/s2p_autonomy.py:39`.

**Recommended fix approach:** Add evidence-aware operator controls if authority management is in native scope; preserve the server's conservation gates and make read-only monitoring explicit otherwise.

#### S2P-7 — P2 — DEAD_CODE (unused legacy browser surface; external disposition required)

**Copilot:** S2P. **Classification:** DEAD_CODE (unused legacy browser surface; external disposition required). **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/soc/centroid-evolution` — `s2p-copilot/backend/app/routers/framework_router.py:127`.
- `GET /api/soc/convergence-calendar` — `s2p-copilot/backend/app/routers/framework_router.py:178`.
- `GET /api/soc/ols-status` — `s2p-copilot/backend/app/routers/framework_router.py:249`.
- `GET /api/soc/flywheel-comparison` — `s2p-copilot/backend/app/routers/framework_router.py:324`.
- `GET /api/soc/iks-trend` — `s2p-copilot/backend/app/routers/framework_router.py:349`.
- `POST /api/soc/shadow/toggle` — `s2p-copilot/backend/app/routers/framework_router.py:388`.
- `POST /api/soc/shadow/analyst-action` — `s2p-copilot/backend/app/routers/framework_router.py:396`.
- `GET /api/soc/shadow/report` — `s2p-copilot/backend/app/routers/framework_router.py:408`.
- `POST /api/soc/checkpoint/create` — `s2p-copilot/backend/app/routers/framework_router.py:419`.
- `GET /api/soc/checkpoint/list` — `s2p-copilot/backend/app/routers/framework_router.py:426`.
- `POST /api/soc/checkpoint/rollback` — `s2p-copilot/backend/app/routers/framework_router.py:434`.
- `POST /api/soc/scorer/freeze` — `s2p-copilot/backend/app/routers/framework_router.py:445`.
- `POST /api/soc/scorer/unfreeze` — `s2p-copilot/backend/app/routers/framework_router.py:451`.
- `GET /api/soc/auto-approve-stats` — `s2p-copilot/backend/app/routers/framework_router.py:461`.
- `POST /api/soc/graph/query` — `s2p-copilot/backend/app/routers/framework_router.py:519`.
- `GET /api/soc/graph/top-nodes` — `s2p-copilot/backend/app/routers/framework_router.py:539`.
- `GET /api/soc/graph/node/{node_id}/neighbors` — `s2p-copilot/backend/app/routers/framework_router.py:552`.
- `GET /api/soc/graph/summary` — `s2p-copilot/backend/app/routers/framework_router.py:561`.
- `GET /api/soc/graph/prebuilt-queries` — `s2p-copilot/backend/app/routers/framework_router.py:576`.
- `POST /api/soc/graph/prebuilt/{query_name}` — `s2p-copilot/backend/app/routers/framework_router.py:589`.
- `GET /api/soc/learning-health` — `s2p-copilot/backend/app/routers/framework_router.py:611`.
- `POST /api/soc/interventions/freeze` — `s2p-copilot/backend/app/routers/framework_router.py:645`.
- `POST /api/soc/interventions/unfreeze` — `s2p-copilot/backend/app/routers/framework_router.py:655`.
- `POST /api/soc/interventions/rollback` — `s2p-copilot/backend/app/routers/framework_router.py:665`.
- `POST /api/soc/interventions/threshold` — `s2p-copilot/backend/app/routers/framework_router.py:680`.
- `GET /api/soc/interventions/state` — `s2p-copilot/backend/app/routers/framework_router.py:692`.
- `GET /api/soc/interventions/history` — `s2p-copilot/backend/app/routers/framework_router.py:702`.
- `GET /api/soc/frozen-roi` — `s2p-copilot/backend/app/routers/framework_router.py:717`.

**Finding:** S2P mounts a legacy framework router under /api/soc. None of those S2P-server routes has a native S2P caller. SOC calls at /api/soc go to the SOC server through the /api proxy, so matching SOC path strings are not S2P preview consumers.

**Frontend/service evidence checked:** `s2p-copilot/backend/app/main.py:294`; `s2p-copilot/backend/app/routers/framework_router.py:127`; `gen-ai-roi-demo-v4-v50/frontend/vite.config.ts:26`; `gen-ai-roi-demo-v4-v50/frontend/vite.config.ts:35`.

**Recommended fix approach:** Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients.

#### S2P-8 — P2 — NAME_MISMATCH (dormant 404 risk)

**Copilot:** S2P. **Classification:** NAME_MISMATCH (dormant 404 risk). **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/fingerprint` — no registration found; see dormant frontend helpers below.
- `GET /api/trajectory` — no registration found; see dormant frontend helpers below.

**Finding:** Two exported but unused helpers target paths absent from the assembled S2P backend. Active panels use /api/s2p/insight/fingerprint and /api/s2p/performance/trajectory instead. No active native 404 from these helpers is established.

**Frontend/service evidence checked:** `copilot-sdk/apps/s2p/frontend/src/api.ts:173`; `copilot-sdk/apps/s2p/frontend/src/api.ts:177`; `copilot-sdk/apps/s2p/frontend/src/api.ts:243`; `copilot-sdk/apps/s2p/frontend/src/api.ts:384`.

**Recommended fix approach:** Remove the dormant helpers or redirect them to correctly typed S2P-specific contracts before any component starts using them.

#### S2P-9 — P2 — MISSING_UI

**Copilot:** S2P. **Classification:** MISSING_UI. **Severity:** P2.

**Endpoint(s) and backend evidence:**

- `GET /api/s2p/lead-time/summary` — `s2p-copilot/backend/app/routers/lead_time_router.py:75`.
- `GET /api/s2p/lead-time/suppliers` — `s2p-copilot/backend/app/routers/lead_time_router.py:88`.
- `GET /api/s2p/lead-time/alerts` — `s2p-copilot/backend/app/routers/lead_time_router.py:103`.
- `GET /api/s2p/lead-time/suppliers/{supplier_id}` — `s2p-copilot/backend/app/routers/lead_time_router.py:116`.

**Finding:** All four lead-time analytics endpoints are registered, but neither native Suppliers/Performance nor SOC preview requests them. Supplier payment, clusters, early warnings and process cycle-time panels are different contracts and do not consume supplier lead-time distributions/alerts.

**Frontend/service evidence checked:** `s2p-copilot/backend/app/main.py:345`; `s2p-copilot/backend/app/routers/lead_time_router.py:75`; `copilot-sdk/apps/s2p/frontend/src/screens/SuppliersScreen.tsx:1`.

**Recommended fix approach:** Add supplier lead-time summary and drilldown if intended for the demo, or document the analytics as an external API with a named owner.

#### S2P — every registered route and no-consumer diff

The table retains registration order and duplicate registrations. WIRED means a reachable native frontend call; PREVIEW_ONLY means only SOC preview consumes it. Every other row has no native consumer. For API_ONLY rows, the frontend evidence is the complete native call inventory below and the inspected screen import graph; no product requirement was found that justifies forcing the route into one of the four defect labels. DEAD_CODE candidates are browser cleanup candidates, not proof that an external integration is absent.

| Method/path | Backend file:line; main mount | Native/preview consumer evidence | Classification / severity | Recommended approach |
|---|---|---|---|---|
| `GET /api/self/centroid-history` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:107`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-timeline` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:154`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/regime-reinit` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:163`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/evolution/summary` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:181`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/diagnostics` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:189`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history/{checkpoint_id}/counterfactual` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:221`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history/{checkpoint_id}/lineage` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:337`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/centroid-history/{checkpoint_id}/replay` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:348`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/replay-score` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:368`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/decisions/{decision_id}/checkpoints` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:413`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/accuracy-by-category` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:422`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/accuracy-alerts` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:457`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/trust-traps` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:465`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/self/rollback` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:471`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/decisions` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:481`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/rule-genealogy` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:508`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/rule-lifecycle/{rule_id}` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:514`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/audit-trail` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:525`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/self/decision-flow` | `copilot-sdk/copilot_sdk/backend/self_computation_router.py:556`; main.py:198 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /saml/metadata` | `copilot-sdk/copilot_sdk/backend/auth_router.py:19`; main.py:290 (conditional AUTH_ENABLED) | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /saml/login` | `copilot-sdk/copilot_sdk/backend/auth_router.py:24`; main.py:290 (conditional AUTH_ENABLED) | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /saml/acs` | `copilot-sdk/copilot_sdk/backend/auth_router.py:31`; main.py:290 (conditional AUTH_ENABLED) | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /saml/logout` | `copilot-sdk/copilot_sdk/backend/auth_router.py:52`; main.py:290 (conditional AUTH_ENABLED) | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /saml/status` | `copilot-sdk/copilot_sdk/backend/auth_router.py:58`; main.py:290 (conditional AUTH_ENABLED) | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/diagnostics` | `s2p-copilot/backend/app/routers/s2p.py:142`; main.py:293 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/learn` | `s2p-copilot/backend/app/routers/s2p.py:2404`; main.py:293 | `copilot-sdk/apps/s2p/frontend/src/api.ts:210` (learnDecision) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/soc/centroid-evolution` | `s2p-copilot/backend/app/routers/framework_router.py:127`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/convergence-calendar` | `s2p-copilot/backend/app/routers/framework_router.py:178`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/ols-status` | `s2p-copilot/backend/app/routers/framework_router.py:249`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/flywheel-comparison` | `s2p-copilot/backend/app/routers/framework_router.py:324`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/iks-trend` | `s2p-copilot/backend/app/routers/framework_router.py:349`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/shadow/toggle` | `s2p-copilot/backend/app/routers/framework_router.py:388`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/shadow/analyst-action` | `s2p-copilot/backend/app/routers/framework_router.py:396`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/shadow/report` | `s2p-copilot/backend/app/routers/framework_router.py:408`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/checkpoint/create` | `s2p-copilot/backend/app/routers/framework_router.py:419`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/checkpoint/list` | `s2p-copilot/backend/app/routers/framework_router.py:426`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/checkpoint/rollback` | `s2p-copilot/backend/app/routers/framework_router.py:434`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/scorer/freeze` | `s2p-copilot/backend/app/routers/framework_router.py:445`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/scorer/unfreeze` | `s2p-copilot/backend/app/routers/framework_router.py:451`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/auto-approve-stats` | `s2p-copilot/backend/app/routers/framework_router.py:461`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/graph/query` | `s2p-copilot/backend/app/routers/framework_router.py:519`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/graph/top-nodes` | `s2p-copilot/backend/app/routers/framework_router.py:539`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/graph/node/{node_id}/neighbors` | `s2p-copilot/backend/app/routers/framework_router.py:552`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/graph/summary` | `s2p-copilot/backend/app/routers/framework_router.py:561`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/graph/prebuilt-queries` | `s2p-copilot/backend/app/routers/framework_router.py:576`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/graph/prebuilt/{query_name}` | `s2p-copilot/backend/app/routers/framework_router.py:589`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/learning-health` | `s2p-copilot/backend/app/routers/framework_router.py:611`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/interventions/freeze` | `s2p-copilot/backend/app/routers/framework_router.py:645`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/interventions/unfreeze` | `s2p-copilot/backend/app/routers/framework_router.py:655`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/interventions/rollback` | `s2p-copilot/backend/app/routers/framework_router.py:665`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `POST /api/soc/interventions/threshold` | `s2p-copilot/backend/app/routers/framework_router.py:680`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/interventions/state` | `s2p-copilot/backend/app/routers/framework_router.py:692`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/interventions/history` | `s2p-copilot/backend/app/routers/framework_router.py:702`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/soc/frozen-roi` | `s2p-copilot/backend/app/routers/framework_router.py:717`; main.py:294 | None in native import graph or SOC preview | DEAD_CODE (unused legacy browser surface; external disposition required) — P2 | S2P-7: Separate required shared services from the copied SOC HTTP namespace and retire or explicitly own the unused S2P registrations after checking non-browser clients. |
| `GET /api/conservation/status` | `copilot-sdk/copilot_sdk/backend/conservation_router.py:42`; main.py:295 | `copilot-sdk/apps/s2p/frontend/src/api.ts:181` (getConservationStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/conservation/what-if` | `copilot-sdk/copilot_sdk/backend/conservation_router.py:56`; main.py:295 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/{copilot}/measurement-state` | `copilot-sdk/copilot_sdk/backend/scoring_router.py:438`; main.py:302 | `copilot-sdk/copilot_sdk/frontend/components/DayZeroCard.tsx:62` (DayZeroCard) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/score/counterfactual` | `copilot-sdk/copilot_sdk/backend/counterfactual_router.py:54`; main.py:309 | `copilot-sdk/apps/s2p/frontend/src/components/WhatIfInspectorPanel.tsx:18` (inspect); `copilot-sdk/apps/s2p/frontend/src/components/CounterfactualCard.tsx:37` (postCounterfactual) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/transfer/status` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:52`; main.py:316 | `copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx:23` (TransferBadge) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/transfer/opportunities` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:58`; main.py:316 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/transfer/demo` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:85`; main.py:316 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/transfer/execute` | `copilot-sdk/copilot_sdk/backend/transfer_router.py:109`; main.py:316 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/score` | `s2p-copilot/backend/app/routers/s2p.py:2119`; main.py:317 | `copilot-sdk/apps/s2p/frontend/src/api.ts:203` (scoreInvoice) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/auto-approve/stats` | `s2p-copilot/backend/app/routers/s2p.py:2349`; main.py:317 | `copilot-sdk/apps/s2p/frontend/src/api.ts:523` (fetchAutoApproveStats) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/auto-approve/expansion-proof` | `s2p-copilot/backend/app/routers/s2p.py:2355`; main.py:317 | `copilot-sdk/apps/s2p/frontend/src/api.ts:530` (fetchExpansionProof) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/outcome` | `s2p-copilot/backend/app/routers/s2p.py:2537`; main.py:317 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/iks` | `s2p-copilot/backend/app/routers/s2p.py:2694`; main.py:317 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-3: Read and refresh the typed S2P IKS observation for the shell, with an unavailable state rather than a fabricated zero. |
| `GET /api/s2p/learning-gate` | `s2p-copilot/backend/app/routers/s2p.py:2706`; main.py:317 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/proposal` | `s2p-copilot/backend/app/routers/s2p_proposals.py:28`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/proposal/{proposal_id}` | `s2p-copilot/backend/app/routers/s2p_proposals.py:40`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/proposals` | `s2p-copilot/backend/app/routers/s2p_proposals.py:50`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `POST /api/s2p/proposal/{proposal_id}/confirm` | `s2p-copilot/backend/app/routers/s2p_proposals.py:60`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `POST /api/s2p/proposal/{proposal_id}/override` | `s2p-copilot/backend/app/routers/s2p_proposals.py:69`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/proposal/{proposal_id}/audit` | `s2p-copilot/backend/app/routers/s2p_proposals.py:81`; main.py:318 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/ledger/timeline` | `s2p-copilot/backend/app/routers/s2p_ledger.py:15`; main.py:319 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/ledger/summary` | `s2p-copilot/backend/app/routers/s2p_ledger.py:20`; main.py:319 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/ledger/iks-trajectory` | `s2p-copilot/backend/app/routers/s2p_ledger.py:25`; main.py:319 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/ledger/conservation-history` | `s2p-copilot/backend/app/routers/s2p_ledger.py:30`; main.py:319 | None in native import graph or SOC preview | MISSING_UI — P1 | S2P-1: Unify proposal resolution and learning behind one idempotent service transaction, then display the returned proposal/receipt state; do not blindly call both existing resolution endpoints and risk applying an outcome twice. |
| `GET /api/s2p/promotion/status` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:35`; main.py:320 | `copilot-sdk/apps/s2p/frontend/src/api.ts:154` (fetchPromotionStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/promotion/{category}/advance` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:39`; main.py:320 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-6: Add evidence-aware operator controls if authority management is in native scope; preserve the server's conservation gates and make read-only monitoring explicit otherwise. |
| `POST /api/s2p/promotion/{category}/rollback` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:52`; main.py:320 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-6: Add evidence-aware operator controls if authority management is in native scope; preserve the server's conservation gates and make read-only monitoring explicit otherwise. |
| `POST /api/s2p/promotion/{category}/transfer` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:65`; main.py:320 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-6: Add evidence-aware operator controls if authority management is in native scope; preserve the server's conservation gates and make read-only monitoring explicit otherwise. |
| `GET /api/s2p/twin/status` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:78`; main.py:320 | `copilot-sdk/apps/s2p/frontend/src/api.ts:158` (fetchTwinStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/twin/drift` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:82`; main.py:320 | `copilot-sdk/apps/s2p/frontend/src/api.ts:162` (fetchTwinDrift) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/twin/freeze` | `s2p-copilot/backend/app/routers/s2p_autonomy.py:89`; main.py:320 | None in native import graph or SOC preview | NAME_MISMATCH / MISSING_UI — P1 | S2P-2: Render the actual drift contract, distinguish missing/unavailable snapshots, and expose an explicit freeze action; introduce paired outcome accuracy only with a defined measured-data API. |
| `GET /api/evolution/variants` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:79`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/evolution/history` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:108`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/evolution/promoted` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:124`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/evolution/summary` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:141`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/evolution/record-outcome` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:169`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/evolution/check-promotion` | `copilot-sdk/copilot_sdk/backend/evolution_router.py:192`; main.py:321 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/auto-approve/status` | `s2p-copilot/backend/app/routers/s2p_auto_approve.py:59`; main.py:327 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-5: Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry. |
| `POST /api/s2p/auto-approve/enable` | `s2p-copilot/backend/app/routers/s2p_auto_approve.py:70`; main.py:327 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-5: Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry. |
| `POST /api/s2p/auto-approve/disable` | `s2p-copilot/backend/app/routers/s2p_auto_approve.py:96`; main.py:327 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-5: Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry. |
| `GET /api/s2p/auto-approve/audit` | `s2p-copilot/backend/app/routers/s2p_auto_approve.py:109`; main.py:327 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-5: Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry. |
| `POST /api/s2p/auto-approve/evaluate` | `s2p-copilot/backend/app/routers/s2p_auto_approve.py:122`; main.py:327 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-5: Either add a clearly labelled shadow-gate workflow or document it as operator-only and separate it from legacy expansion telemetry. |
| `GET /api/s2p/audit/export` | `s2p-copilot/backend/app/routers/s2p_audit_export.py:315`; main.py:328 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/audit/export/csv` | `s2p-copilot/backend/app/routers/s2p_audit_export.py:323`; main.py:328 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evolution/rules` | `s2p-copilot/backend/app/routers/s2p_evolution.py:39`; main.py:329 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evolution/variants` | `s2p-copilot/backend/app/routers/s2p_evolution.py:43`; main.py:329 | `copilot-sdk/apps/s2p/frontend/src/api.ts:348` (fetchS2PEvolutionVariants) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evolution/dimensions` | `s2p-copilot/backend/app/routers/s2p_evolution.py:48`; main.py:329 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/evolution/propose` | `s2p-copilot/backend/app/routers/s2p_evolution.py:52`; main.py:329 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evolution/promotion-check` | `s2p-copilot/backend/app/routers/s2p_evolution.py:64`; main.py:329 | `copilot-sdk/apps/s2p/frontend/src/api.ts:356` (getS2PPromotionCheck) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/evolution/reset` | `s2p-copilot/backend/app/routers/s2p_evolution.py:82`; main.py:329 | None in native import graph or SOC preview | DEAD_CODE — unsupported reset, P1 | DS-B1: retain append-only history and replace reset tests with real contract checks before exposing this dormant control. |
| `GET /api/s2p/evolution/shadow-results` | `s2p-copilot/backend/app/routers/s2p_evolution.py:92`; main.py:329 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evolution/promoted` | `s2p-copilot/backend/app/routers/s2p_evolution.py:96`; main.py:329 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evolution/extinction` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:115`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/learning/frozen-twin` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:151`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/context/what-if/{invoice_id}` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:222`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/diagnostics/day-zero` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:253`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/diagnostics/confidence` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:264`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/context/rule-vs-reasoning` | `s2p-copilot/backend/app/routers/s2p_demo_beats.py:307`; main.py:330 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/export/centroids` | `s2p-copilot/backend/app/routers/s2p_explorer.py:381`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/export/csv` | `s2p-copilot/backend/app/routers/s2p_explorer.py:398`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/explorer/import/centroids` | `s2p-copilot/backend/app/routers/s2p_explorer.py:410`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/centroid/{category}/{action}` | `s2p-copilot/backend/app/routers/s2p_explorer.py:480`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/drift/{category}` | `s2p-copilot/backend/app/routers/s2p_explorer.py:495`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/dk-weights` | `s2p-copilot/backend/app/routers/s2p_explorer.py:512`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/ranking` | `s2p-copilot/backend/app/routers/s2p_explorer.py:522`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/explorer/contribution` | `s2p-copilot/backend/app/routers/s2p_explorer.py:566`; main.py:331 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/factors/analysis` | `s2p-copilot/backend/app/routers/factor_proposer_router.py:30`; main.py:332 | `copilot-sdk/apps/s2p/frontend/src/api.ts:475` (getFactorAnalysis) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/factors/recommendations` | `s2p-copilot/backend/app/routers/factor_proposer_router.py:36`; main.py:332 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/factors/propose` | `s2p-copilot/backend/app/routers/factor_proposer_router.py:42`; main.py:332 | `copilot-sdk/apps/s2p/frontend/src/api.ts:483` (proposeFactorReplacement) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/centroid/all` | `s2p-copilot/backend/app/routers/centroid_router.py:17`; main.py:333 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/centroid/explain/{decision_id}` | `s2p-copilot/backend/app/routers/centroid_router.py:38`; main.py:333 | `copilot-sdk/apps/s2p/frontend/src/api.ts:424` (getCentroidExplanation) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/centroid/drift/{category}/{action}` | `s2p-copilot/backend/app/routers/centroid_router.py:46`; main.py:333 | `copilot-sdk/apps/s2p/frontend/src/api.ts:429` (getCentroidDrift) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/centroid/{category}/{action}` | `s2p-copilot/backend/app/routers/centroid_router.py:54`; main.py:333 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/control-tower/intents` | `s2p-copilot/backend/app/routers/s2p_control_tower.py:155`; main.py:334 | `copilot-sdk/apps/s2p/frontend/src/api.ts:538` (fetchIntents) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/control-tower/classify` | `s2p-copilot/backend/app/routers/s2p_control_tower.py:191`; main.py:334 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/control-tower/classify` | `s2p-copilot/backend/app/routers/s2p_control_tower.py:199`; main.py:334 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/control-tower/queue` | `s2p-copilot/backend/app/routers/s2p_control_tower.py:204`; main.py:334 | `copilot-sdk/apps/s2p/frontend/src/api.ts:551` (fetchCTQueue) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/discovery/alerts` | `s2p-copilot/backend/app/routers/s2p_discovery.py:220`; main.py:335 | `copilot-sdk/apps/s2p/frontend/src/api.ts:376` (getDiscoveryAlerts) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/discovery/disruptions` | `s2p-copilot/backend/app/routers/s2p_discovery.py:238`; main.py:335 | `copilot-sdk/apps/s2p/frontend/src/api.ts:380` (getDisruptionRecovery) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/discovery/extended` | `s2p-copilot/backend/app/routers/s2p_discovery.py:305`; main.py:335 | `copilot-sdk/apps/s2p/frontend/src/api.ts:511` (getExtendedDiscoveries) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/discovery/supplier/{supplier_id}` | `s2p-copilot/backend/app/routers/s2p_discovery.py:321`; main.py:335 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/discovery/propagation/{discovery_id}` | `s2p-copilot/backend/app/routers/s2p_discovery.py:338`; main.py:335 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/simulation/scenarios` | `s2p-copilot/backend/app/routers/s2p_simulation.py:203`; main.py:336 | `copilot-sdk/apps/s2p/frontend/src/api.ts:503` (getSimulationScenarios) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/simulation/scenarios/{scenario_id}` | `s2p-copilot/backend/app/routers/s2p_simulation.py:213`; main.py:336 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/simulation/what-if/{scenario_id}` | `s2p-copilot/backend/app/routers/s2p_simulation.py:223`; main.py:336 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/simulation/impact-summary` | `s2p-copilot/backend/app/routers/s2p_simulation.py:263`; main.py:336 | `copilot-sdk/apps/s2p/frontend/src/api.ts:507` (getImpactSummary) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/simulation/simulate` | `s2p-copilot/backend/app/routers/s2p_simulation.py:281`; main.py:336 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/simulation/batch-simulate` | `s2p-copilot/backend/app/routers/s2p_simulation.py:287`; main.py:336 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/insight/fingerprint` | `s2p-copilot/backend/app/routers/s2p_insight.py:129`; main.py:337 | `copilot-sdk/apps/s2p/frontend/src/api.ts:243` (fetchS2PFingerprint) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/insight/similar` | `s2p-copilot/backend/app/routers/s2p_insight.py:148`; main.py:337 | `copilot-sdk/apps/s2p/frontend/src/api.ts:249` (fetchS2PSimilar) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/insight/process-context/{invoice_id}` | `s2p-copilot/backend/app/routers/s2p_insight.py:194`; main.py:337 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/insight/cross-graph` | `s2p-copilot/backend/app/routers/s2p_insight.py:219`; main.py:337 | `copilot-sdk/apps/s2p/frontend/src/api.ts:299` (fetchS2PCrossGraph) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/insight/process-signals` | `s2p-copilot/backend/app/routers/s2p_insight.py:278`; main.py:337 | `copilot-sdk/apps/s2p/frontend/src/api.ts:306` (fetchS2PProcessSignals) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/audit-trail/{invoice_id}` | `s2p-copilot/backend/app/routers/s2p_evidence.py:287`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:331` (fetchS2PAuditTrail) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/receipts` | `s2p-copilot/backend/app/routers/s2p_evidence.py:303`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:491` (getReceipts) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/receipts/{invoice_id}` | `s2p-copilot/backend/app/routers/s2p_evidence.py:309`; main.py:338 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evidence/receipts/decision/{decision_id}` | `s2p-copilot/backend/app/routers/s2p_evidence.py:318`; main.py:338 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/evidence/chain-integrity` | `s2p-copilot/backend/app/routers/s2p_evidence.py:327`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:495` (getChainIntegrity) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/audit-pack` | `s2p-copilot/backend/app/routers/s2p_evidence.py:333`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:499` (getAuditPack) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/template` | `s2p-copilot/backend/app/routers/s2p_evidence.py:353`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:234` (getEvidenceTemplate) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/rules` | `s2p-copilot/backend/app/routers/s2p_evidence.py:444`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:340` (fetchS2PRules) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/evidence/compliance` | `s2p-copilot/backend/app/routers/s2p_evidence.py:485`; main.py:338 | `copilot-sdk/apps/s2p/frontend/src/api.ts:372` (fetchS2PCompliance) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/situation/{decision_id}` | `s2p-copilot/backend/app/routers/s2p_situation.py:27`; main.py:339 | `copilot-sdk/apps/s2p/frontend/src/api.ts:263` (fetchSituation) | WIRED | Retain; see ranked contract findings where applicable. |
| `POST /api/s2p/enrichment/run` | `s2p-copilot/backend/app/routers/s2p_enrichment.py:41`; main.py:340 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/enrichment/summary` | `s2p-copilot/backend/app/routers/s2p_enrichment.py:51`; main.py:340 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/enrichment/alerts` | `s2p-copilot/backend/app/routers/s2p_enrichment.py:62`; main.py:340 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/enrichment/supplier/{supplier_id}` | `s2p-copilot/backend/app/routers/s2p_enrichment.py:76`; main.py:340 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/enrich-context/{invoice_id}` | `s2p-copilot/backend/app/routers/s2p_enrichment_context.py:28`; main.py:341 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/governance/compliance-screening` | `s2p-copilot/backend/app/routers/s2p_governance.py:121`; main.py:342 | `copilot-sdk/apps/s2p/frontend/src/api.ts:515` (getComplianceScreening) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/governance/compliance-gaps` | `s2p-copilot/backend/app/routers/s2p_governance.py:126`; main.py:342 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/governance/conservation-proof` | `s2p-copilot/backend/app/routers/s2p_governance.py:134`; main.py:342 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/governance/sox-readiness` | `s2p-copilot/backend/app/routers/s2p_governance.py:153`; main.py:342 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/governance/rationalization` | `s2p-copilot/backend/app/routers/s2p_governance.py:326`; main.py:342 | `copilot-sdk/apps/s2p/frontend/src/api.ts:519` (getRationalizationRecs) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/governance/rationalization/overlap` | `s2p-copilot/backend/app/routers/s2p_governance.py:347`; main.py:342 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/governance/rationalization/supplier/{supplier_id}` | `s2p-copilot/backend/app/routers/s2p_governance.py:376`; main.py:342 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/performance/trajectory` | `s2p-copilot/backend/app/routers/s2p_performance.py:171`; main.py:343 | `copilot-sdk/apps/s2p/frontend/src/api.ts:384` (fetchS2PTrajectory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/performance/what-if` | `s2p-copilot/backend/app/routers/s2p_performance.py:191`; main.py:343 | `copilot-sdk/apps/s2p/frontend/src/api.ts:392` (fetchS2PWhatIf) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/performance/summary` | `s2p-copilot/backend/app/routers/s2p_performance.py:231`; main.py:343 | `copilot-sdk/apps/s2p/frontend/src/api.ts:396` (fetchS2PSummary) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/financial-impact` | `s2p-copilot/backend/app/routers/financial_router.py:375`; main.py:344 | `copilot-sdk/apps/s2p/frontend/src/api.ts:564` (fetchFinancialImpact) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/financial-impact/trend` | `s2p-copilot/backend/app/routers/financial_router.py:381`; main.py:344 | `copilot-sdk/apps/s2p/frontend/src/api.ts:568` (fetchFinancialImpactTrend) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/financial-impact/{category}` | `s2p-copilot/backend/app/routers/financial_router.py:387`; main.py:344 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/lead-time/summary` | `s2p-copilot/backend/app/routers/lead_time_router.py:75`; main.py:345 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-9: Add supplier lead-time summary and drilldown if intended for the demo, or document the analytics as an external API with a named owner. |
| `GET /api/s2p/lead-time/suppliers` | `s2p-copilot/backend/app/routers/lead_time_router.py:88`; main.py:345 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-9: Add supplier lead-time summary and drilldown if intended for the demo, or document the analytics as an external API with a named owner. |
| `GET /api/s2p/lead-time/alerts` | `s2p-copilot/backend/app/routers/lead_time_router.py:103`; main.py:345 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-9: Add supplier lead-time summary and drilldown if intended for the demo, or document the analytics as an external API with a named owner. |
| `GET /api/s2p/lead-time/suppliers/{supplier_id}` | `s2p-copilot/backend/app/routers/lead_time_router.py:116`; main.py:345 | None in native import graph or SOC preview | MISSING_UI — P2 | S2P-9: Add supplier lead-time summary and drilldown if intended for the demo, or document the analytics as an external API with a named owner. |
| `GET /api/s2p/pvg/variants` | `s2p-copilot/backend/app/routers/s2p_pvg.py:129`; main.py:346 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/pvg/impact` | `s2p-copilot/backend/app/routers/s2p_pvg.py:170`; main.py:346 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/pvg/leakage` | `s2p-copilot/backend/app/routers/s2p_pvg.py:188`; main.py:346 | `copilot-sdk/apps/s2p/frontend/src/api.ts:578` (fetchLeakage) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/pvg/cycle-time` | `s2p-copilot/backend/app/routers/s2p_pvg.py:223`; main.py:346 | `copilot-sdk/apps/s2p/frontend/src/api.ts:582` (fetchCycleTime) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/novelty/status` | `s2p-copilot/backend/app/routers/s2p_novelty.py:47`; main.py:347 | `copilot-sdk/apps/s2p/frontend/src/api.ts:400` (getNoveltyStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/novelty/history` | `s2p-copilot/backend/app/routers/s2p_novelty.py:69`; main.py:347 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/novelty/rate` | `s2p-copilot/backend/app/routers/s2p_novelty.py:79`; main.py:347 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/novelty/auto-pause` | `s2p-copilot/backend/app/routers/s2p_novelty.py:93`; main.py:347 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/novelty/triggered-decisions` | `s2p-copilot/backend/app/routers/s2p_novelty.py:111`; main.py:347 | `copilot-sdk/apps/s2p/frontend/src/api.ts:410` (getNoveltyTriggeredDecisions) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/clusters` | `s2p-copilot/backend/app/routers/s2p_clustering.py:164`; main.py:348 | `copilot-sdk/apps/s2p/frontend/src/api.ts:629` (getSupplierClusters) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/similarity` | `s2p-copilot/backend/app/routers/s2p_clustering.py:205`; main.py:348 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/compliance/screen` | `s2p-copilot/backend/app/routers/compliance_router.py:41`; main.py:349 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/compliance/batch` | `s2p-copilot/backend/app/routers/compliance_router.py:50`; main.py:349 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/compliance/report` | `s2p-copilot/backend/app/routers/compliance_router.py:65`; main.py:349 | `gen-ai-roi-demo-v4-v50/frontend/src/components/CompliancePanel.tsx:62` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/s2p/suppliers/early-warnings/patterns` | `s2p-copilot/backend/app/routers/s2p_early_warning.py:194`; main.py:350 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers/early-warnings` | `s2p-copilot/backend/app/routers/s2p_early_warning.py:210`; main.py:350 | `copilot-sdk/apps/s2p/frontend/src/api.ts:317` (getEarlyWarnings) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/trends` | `s2p-copilot/backend/app/routers/s2p_early_warning.py:224`; main.py:350 | `gen-ai-roi-demo-v4-v50/frontend/src/components/TrendCorrelationPanel.tsx:42` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/s2p/suppliers/trend-signals` | `s2p-copilot/backend/app/routers/s2p_early_warning.py:276`; main.py:350 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers/payment-strategy` | `s2p-copilot/backend/app/routers/s2p_payment.py:255`; main.py:351 | `copilot-sdk/apps/s2p/frontend/src/api.ts:616` (getPaymentStrategy) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/payment-portfolio` | `s2p-copilot/backend/app/routers/s2p_payment.py:278`; main.py:351 | `gen-ai-roi-demo-v4-v50/frontend/src/components/WorkingCapitalPanel.tsx:56` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/s2p/suppliers/payment-behavior` | `s2p-copilot/backend/app/routers/s2p_payment.py:297`; main.py:351 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/optimizer/export` | `s2p-copilot/backend/app/routers/optimizer_router.py:32`; main.py:352 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/optimizer/schema` | `s2p-copilot/backend/app/routers/optimizer_router.py:45`; main.py:352 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/optimizer/validate` | `s2p-copilot/backend/app/routers/optimizer_router.py:50`; main.py:352 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:202`; main.py:353 | `copilot-sdk/apps/s2p/frontend/src/api.ts:590` (fetchSupplierProfiles) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:203`; main.py:353 | None in native import graph or SOC preview | DEAD_CODE candidate — unused browser alias, P2 | Native UI uses GET /api/s2p/suppliers; confirm external compatibility needs before retiring this alias. |
| `GET /api/s2p/suppliers/clustering` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:213`; main.py:353 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers/declining` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:242`; main.py:353 | `copilot-sdk/apps/s2p/frontend/src/api.ts:594` (fetchDecliningSuppliers) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/heatmap` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:248`; main.py:353 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers/correlations` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:305`; main.py:353 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/suppliers/{supplier_id}/profile` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:363`; main.py:353 | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:566` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/s2p/suppliers/{supplier_id}/history` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:377`; main.py:353 | `copilot-sdk/apps/s2p/frontend/src/api.ts:607` (fetchSupplierHistory) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/suppliers/{supplier_id}/heatmap` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:386`; main.py:353 | `copilot-sdk/apps/s2p/frontend/src/api.ts:612` (fetchSupplierHeatmap) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/preview/queue` | `s2p-copilot/backend/app/routers/s2p_preview.py:508`; main.py:354 | `copilot-sdk/apps/s2p/frontend/src/api.ts:133` (getPreviewQueue) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/preview/conservation` | `s2p-copilot/backend/app/routers/s2p_preview.py:514`; main.py:354 | `copilot-sdk/apps/s2p/frontend/src/api.ts:150` (getPreviewConservation); `copilot-sdk/apps/s2p/frontend/src/api.ts:182` (getConservationStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/preview/compounding` | `s2p-copilot/backend/app/routers/s2p_preview.py:551`; main.py:354 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/preview/suppliers` | `s2p-copilot/backend/app/routers/s2p_preview.py:570`; main.py:354 | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:558` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/s2p/preview/config` | `s2p-copilot/backend/app/routers/s2p_preview.py:587`; main.py:354 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `POST /api/s2p/enterprise/process-fusion` | `s2p-copilot/backend/app/routers/s2p_process_fusion.py:15`; main.py:355 | `copilot-sdk/apps/s2p/frontend/src/api.ts:310` (fetchProcessFusion) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/cohort-status` | `s2p-copilot/backend/app/routers/cohort_status_router.py:21`; main.py:356 | `copilot-sdk/apps/s2p/frontend/src/api.ts:129` (getCohortStatus) | WIRED | Retain; see ranked contract findings where applicable. |
| `GET /api/s2p/graph/status` | `s2p-copilot/backend/app/s2p_graph_status.py:486`; main.py:357 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/s2p/tab-state` | `copilot-sdk/copilot_sdk/state/tab_state_router.py:14`; main.py:358 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /api/{copilot}/static-urls` | `copilot-sdk/copilot_sdk/state/tab_state_router.py:21`; main.py:358 | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |
| `GET /health` | `s2p-copilot/backend/app/main.py:399` | `gen-ai-roi-demo-v4-v50/frontend/src/components/DomainApplicabilityPanel.tsx:44` | PREVIEW_ONLY — P3/no defect | Retain; SOC preview is the consumer. |
| `GET /api/health` | `s2p-copilot/backend/app/main.py:400` | None in native import graph or SOC preview | API_ONLY — disposition unproven | No reachable native or SOC-preview caller found; document an operator/integration owner or decide UI scope. No removal or UI defect inferred. |

#### S2P — every reachable frontend API call site

Entries are static call sites, not requests per page or test. Repeated calls to one URL and shared mounted SDK components are retained. Query strings are omitted for route identity; their source literals remain visible at the cited lines. Unused api.ts exports are excluded from the consumer count and listed separately.

| Method/path | Frontend file:line | Calling helper/component |
|---|---|---|
| `GET /api/s2p/measurement-state` | `copilot-sdk/copilot_sdk/frontend/components/DayZeroCard.tsx:62` | `DayZeroCard` |
| `GET /api/transfer/status` | `copilot-sdk/copilot_sdk/frontend/TransferBadge.tsx:23` | `TransferBadge` |
| `GET /api/s2p/cohort-status` | `copilot-sdk/apps/s2p/frontend/src/api.ts:129` | `getCohortStatus` |
| `GET /api/s2p/preview/queue` | `copilot-sdk/apps/s2p/frontend/src/api.ts:133` | `getPreviewQueue` |
| `GET /api/s2p/preview/conservation` | `copilot-sdk/apps/s2p/frontend/src/api.ts:150` | `getPreviewConservation` |
| `GET /api/s2p/promotion/status` | `copilot-sdk/apps/s2p/frontend/src/api.ts:154` | `fetchPromotionStatus` |
| `GET /api/s2p/twin/status` | `copilot-sdk/apps/s2p/frontend/src/api.ts:158` | `fetchTwinStatus` |
| `GET /api/s2p/twin/drift` | `copilot-sdk/apps/s2p/frontend/src/api.ts:162` | `fetchTwinDrift` |
| `GET /api/conservation/status` | `copilot-sdk/apps/s2p/frontend/src/api.ts:181` | `getConservationStatus` |
| `GET /api/s2p/preview/conservation` | `copilot-sdk/apps/s2p/frontend/src/api.ts:182` | `getConservationStatus` |
| `POST /api/s2p/score` | `copilot-sdk/apps/s2p/frontend/src/api.ts:203` | `scoreInvoice` |
| `POST /api/learn` | `copilot-sdk/apps/s2p/frontend/src/api.ts:210` | `learnDecision` |
| `GET /api/s2p/evidence/template` | `copilot-sdk/apps/s2p/frontend/src/api.ts:234` | `getEvidenceTemplate` |
| `GET /api/s2p/insight/fingerprint` | `copilot-sdk/apps/s2p/frontend/src/api.ts:243` | `fetchS2PFingerprint` |
| `GET /api/s2p/insight/similar` | `copilot-sdk/apps/s2p/frontend/src/api.ts:249` | `fetchS2PSimilar` |
| `GET /api/s2p/situation/{}` | `copilot-sdk/apps/s2p/frontend/src/api.ts:263` | `fetchSituation` |
| `GET /api/s2p/insight/cross-graph` | `copilot-sdk/apps/s2p/frontend/src/api.ts:299` | `fetchS2PCrossGraph` |
| `GET /api/s2p/insight/process-signals` | `copilot-sdk/apps/s2p/frontend/src/api.ts:306` | `fetchS2PProcessSignals` |
| `POST /api/s2p/enterprise/process-fusion` | `copilot-sdk/apps/s2p/frontend/src/api.ts:310` | `fetchProcessFusion` |
| `GET /api/s2p/suppliers/early-warnings` | `copilot-sdk/apps/s2p/frontend/src/api.ts:317` | `getEarlyWarnings` |
| `GET /api/s2p/evidence/audit-trail/{}` | `copilot-sdk/apps/s2p/frontend/src/api.ts:331` | `fetchS2PAuditTrail` |
| `GET /api/s2p/evidence/rules` | `copilot-sdk/apps/s2p/frontend/src/api.ts:340` | `fetchS2PRules` |
| `GET /api/s2p/evolution/variants` | `copilot-sdk/apps/s2p/frontend/src/api.ts:348` | `fetchS2PEvolutionVariants` |
| `GET /api/s2p/evolution/promotion-check` | `copilot-sdk/apps/s2p/frontend/src/api.ts:356` | `getS2PPromotionCheck` |
| `GET /api/s2p/evidence/compliance` | `copilot-sdk/apps/s2p/frontend/src/api.ts:372` | `fetchS2PCompliance` |
| `GET /api/s2p/discovery/alerts` | `copilot-sdk/apps/s2p/frontend/src/api.ts:376` | `getDiscoveryAlerts` |
| `GET /api/s2p/discovery/disruptions` | `copilot-sdk/apps/s2p/frontend/src/api.ts:380` | `getDisruptionRecovery` |
| `GET /api/s2p/performance/trajectory` | `copilot-sdk/apps/s2p/frontend/src/api.ts:384` | `fetchS2PTrajectory` |
| `GET /api/s2p/performance/what-if` | `copilot-sdk/apps/s2p/frontend/src/api.ts:392` | `fetchS2PWhatIf` |
| `GET /api/s2p/performance/summary` | `copilot-sdk/apps/s2p/frontend/src/api.ts:396` | `fetchS2PSummary` |
| `GET /api/s2p/novelty/status` | `copilot-sdk/apps/s2p/frontend/src/api.ts:400` | `getNoveltyStatus` |
| `GET /api/s2p/novelty/triggered-decisions` | `copilot-sdk/apps/s2p/frontend/src/api.ts:410` | `getNoveltyTriggeredDecisions` |
| `GET /api/s2p/centroid/explain/{}` | `copilot-sdk/apps/s2p/frontend/src/api.ts:424` | `getCentroidExplanation` |
| `GET /api/s2p/centroid/drift/{}/{}` | `copilot-sdk/apps/s2p/frontend/src/api.ts:429` | `getCentroidDrift` |
| `GET /api/s2p/factors/analysis` | `copilot-sdk/apps/s2p/frontend/src/api.ts:475` | `getFactorAnalysis` |
| `POST /api/s2p/factors/propose` | `copilot-sdk/apps/s2p/frontend/src/api.ts:483` | `proposeFactorReplacement` |
| `GET /api/s2p/evidence/receipts` | `copilot-sdk/apps/s2p/frontend/src/api.ts:491` | `getReceipts` |
| `GET /api/s2p/evidence/chain-integrity` | `copilot-sdk/apps/s2p/frontend/src/api.ts:495` | `getChainIntegrity` |
| `GET /api/s2p/evidence/audit-pack` | `copilot-sdk/apps/s2p/frontend/src/api.ts:499` | `getAuditPack` |
| `GET /api/s2p/simulation/scenarios` | `copilot-sdk/apps/s2p/frontend/src/api.ts:503` | `getSimulationScenarios` |
| `GET /api/s2p/simulation/impact-summary` | `copilot-sdk/apps/s2p/frontend/src/api.ts:507` | `getImpactSummary` |
| `GET /api/s2p/discovery/extended` | `copilot-sdk/apps/s2p/frontend/src/api.ts:511` | `getExtendedDiscoveries` |
| `GET /api/s2p/governance/compliance-screening` | `copilot-sdk/apps/s2p/frontend/src/api.ts:515` | `getComplianceScreening` |
| `GET /api/s2p/governance/rationalization` | `copilot-sdk/apps/s2p/frontend/src/api.ts:519` | `getRationalizationRecs` |
| `GET /api/s2p/auto-approve/stats` | `copilot-sdk/apps/s2p/frontend/src/api.ts:523` | `fetchAutoApproveStats` |
| `GET /api/s2p/auto-approve/expansion-proof` | `copilot-sdk/apps/s2p/frontend/src/api.ts:530` | `fetchExpansionProof` |
| `GET /api/s2p/control-tower/intents` | `copilot-sdk/apps/s2p/frontend/src/api.ts:538` | `fetchIntents` |
| `GET /api/s2p/control-tower/queue` | `copilot-sdk/apps/s2p/frontend/src/api.ts:551` | `fetchCTQueue` |
| `GET /api/s2p/financial-impact` | `copilot-sdk/apps/s2p/frontend/src/api.ts:564` | `fetchFinancialImpact` |
| `GET /api/s2p/financial-impact/trend` | `copilot-sdk/apps/s2p/frontend/src/api.ts:568` | `fetchFinancialImpactTrend` |
| `GET /api/s2p/pvg/leakage` | `copilot-sdk/apps/s2p/frontend/src/api.ts:578` | `fetchLeakage` |
| `GET /api/s2p/pvg/cycle-time` | `copilot-sdk/apps/s2p/frontend/src/api.ts:582` | `fetchCycleTime` |
| `GET /api/s2p/suppliers` | `copilot-sdk/apps/s2p/frontend/src/api.ts:590` | `fetchSupplierProfiles` |
| `GET /api/s2p/suppliers/declining` | `copilot-sdk/apps/s2p/frontend/src/api.ts:594` | `fetchDecliningSuppliers` |
| `GET /api/s2p/suppliers/{}/history` | `copilot-sdk/apps/s2p/frontend/src/api.ts:607` | `fetchSupplierHistory` |
| `GET /api/s2p/suppliers/{}/heatmap` | `copilot-sdk/apps/s2p/frontend/src/api.ts:612` | `fetchSupplierHeatmap` |
| `GET /api/s2p/suppliers/payment-strategy` | `copilot-sdk/apps/s2p/frontend/src/api.ts:616` | `getPaymentStrategy` |
| `GET /api/s2p/suppliers/clusters` | `copilot-sdk/apps/s2p/frontend/src/api.ts:629` | `getSupplierClusters` |
| `POST /api/s2p/score/counterfactual` | `copilot-sdk/apps/s2p/frontend/src/components/WhatIfInspectorPanel.tsx:18` | `inspect` |
| `POST /api/s2p/score/counterfactual` | `copilot-sdk/apps/s2p/frontend/src/components/CounterfactualCard.tsx:37` | `postCounterfactual` |

#### S2P — dormant frontend helpers and reverse check

| Method/path | Unused helper; file:line | Backend registration |
|---|---|---|
| `GET /api/s2p/preview/queue` | `getPreviewQueueStrict` — `copilot-sdk/apps/s2p/frontend/src/api.ts:142` | `s2p-copilot/backend/app/routers/s2p_preview.py:508` |
| `GET /api/s2p/preview/suppliers` | `getPreviewSuppliers` — `copilot-sdk/apps/s2p/frontend/src/api.ts:166` | `s2p-copilot/backend/app/routers/s2p_preview.py:570` |
| `GET /api/fingerprint` | `getFingerprint` — `copilot-sdk/apps/s2p/frontend/src/api.ts:173` | **ABSENT — dormant 404 risk; S2P-8** |
| `GET /api/trajectory` | `getTrajectory` — `copilot-sdk/apps/s2p/frontend/src/api.ts:177` | **ABSENT — dormant 404 risk; S2P-8** |
| `POST /api/s2p/score` | `scoreException` — `copilot-sdk/apps/s2p/frontend/src/api.ts:195` | `s2p-copilot/backend/app/routers/s2p.py:2119` |
| `POST /api/s2p/outcome` | `verifyDecision` — `copilot-sdk/apps/s2p/frontend/src/api.ts:199` | `s2p-copilot/backend/app/routers/s2p.py:2537` |
| `GET /api/s2p/suppliers/trend-signals` | `getTrendSignals` — `copilot-sdk/apps/s2p/frontend/src/api.ts:325` | `s2p-copilot/backend/app/routers/s2p_early_warning.py:276` |
| `GET /api/s2p/evolution/rules` | `fetchS2PEvolutionRules` — `copilot-sdk/apps/s2p/frontend/src/api.ts:344` | `s2p-copilot/backend/app/routers/s2p_evolution.py:39` |
| `POST /api/s2p/evolution/reset` | `resetS2PEvolution` — `copilot-sdk/apps/s2p/frontend/src/api.ts:360` | `s2p-copilot/backend/app/routers/s2p_evolution.py:82` |
| `GET /api/s2p/evolution/shadow-results` | `fetchS2PShadowResults` — `copilot-sdk/apps/s2p/frontend/src/api.ts:364` | `s2p-copilot/backend/app/routers/s2p_evolution.py:92` |
| `GET /api/s2p/evolution/promoted` | `fetchS2PPromotedRules` — `copilot-sdk/apps/s2p/frontend/src/api.ts:368` | `s2p-copilot/backend/app/routers/s2p_evolution.py:96` |
| `GET /api/s2p/novelty/history` | `getNoveltyHistory` — `copilot-sdk/apps/s2p/frontend/src/api.ts:405` | `s2p-copilot/backend/app/routers/s2p_novelty.py:69` |
| `GET /api/s2p/centroid/all` | `getAllCentroids` — `copilot-sdk/apps/s2p/frontend/src/api.ts:414` | `s2p-copilot/backend/app/routers/centroid_router.py:17` |
| `GET /api/s2p/centroid/{}/{}` | `getCentroid` — `copilot-sdk/apps/s2p/frontend/src/api.ts:419` | `s2p-copilot/backend/app/routers/centroid_router.py:54` |
| `GET /api/s2p/explorer/dk-weights` | `getDKWeights` — `copilot-sdk/apps/s2p/frontend/src/api.ts:434` | `s2p-copilot/backend/app/routers/s2p_explorer.py:512` |
| `GET /api/s2p/factors/recommendations` | `getFactorRecommendations` — `copilot-sdk/apps/s2p/frontend/src/api.ts:479` | `s2p-copilot/backend/app/routers/factor_proposer_router.py:36` |
| `GET /api/s2p/control-tower/classify` | `classifyInvoice` — `copilot-sdk/apps/s2p/frontend/src/api.ts:546` | `s2p-copilot/backend/app/routers/s2p_control_tower.py:191` |
| `GET /api/s2p/pvg/variants` | `fetchVariants` — `copilot-sdk/apps/s2p/frontend/src/api.ts:555` | `s2p-copilot/backend/app/routers/s2p_pvg.py:129` |
| `GET /api/s2p/pvg/impact` | `fetchImpact` — `copilot-sdk/apps/s2p/frontend/src/api.ts:560` | `s2p-copilot/backend/app/routers/s2p_pvg.py:170` |
| `GET /api/s2p/financial-impact/{}` | `fetchFinancialImpactCategory` — `copilot-sdk/apps/s2p/frontend/src/api.ts:573` | `s2p-copilot/backend/app/routers/financial_router.py:387` |
| `GET /api/s2p/suppliers/{}/profile` | `fetchSupplierProfile` — `copilot-sdk/apps/s2p/frontend/src/api.ts:598` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:363` |
| `GET /api/s2p/suppliers/payment-behavior` | `getPaymentBehavior` — `copilot-sdk/apps/s2p/frontend/src/api.ts:621` | `s2p-copilot/backend/app/routers/s2p_payment.py:297` |
| `GET /api/s2p/suppliers/clustering` | `fetchSupplierClustering` — `copilot-sdk/apps/s2p/frontend/src/api.ts:625` | `s2p-copilot/backend/app/routers/s2p_suppliers.py:213` |
| `GET /api/s2p/suppliers/similarity` | `getSupplierSimilarity` — `copilot-sdk/apps/s2p/frontend/src/api.ts:634` | `s2p-copilot/backend/app/routers/s2p_clustering.py:205` |

**Active reverse diff:** no absent method/path registration found after resolving dynamic IDs, API bases, query suffixes and router prefixes. This is a static route check; auth, validation, absent record IDs and backend failures can still return errors. Two dormant helpers target absent generic fingerprint/trajectory routes (S2P-8). The registered /suppliers/ trailing-slash alias is counted separately from the /suppliers URL used by the UI.

### SOC preview cross-reference — S2P

SOC mounts S2PPreviewTab at `gen-ai-roi-demo-v4-v50/frontend/src/App.tsx:94`. Its child panels are rendered at `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:752` and following; DomainApplicabilityPanel is mounted at line 608/617. The parent uses the /api/s2p Vite proxy; child panels generally default to the explicit S2P origin on port 8002. `gen-ai-roi-demo-v4-v50/frontend/vite.config.ts:26` targets S2P, while line 35 sends other /api calls to SOC. The /s2p-health probe at line 30 rewrites to S2P /health.

| S2P backend method/path | SOC preview consumer file:line | Native S2P consumer? |
|---|---|---|
| `GET /api/s2p/preview/queue` | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:556` | Yes — shared native/preview use |
| `GET /api/s2p/preview/conservation` | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:557` | Yes — shared native/preview use |
| `GET /api/s2p/preview/suppliers` | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:558` | **No — PREVIEW_ONLY** |
| `GET /api/s2p/suppliers/{supplier_id}/profile` | `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/S2PPreviewTab.tsx:566` | **No — PREVIEW_ONLY** |
| `GET /api/s2p/compliance/report` | `gen-ai-roi-demo-v4-v50/frontend/src/components/CompliancePanel.tsx:62` | **No — PREVIEW_ONLY** |
| `GET /api/s2p/financial-impact` | `gen-ai-roi-demo-v4-v50/frontend/src/components/FinancialImpactPanel.tsx:57` | Yes — shared native/preview use |
| `GET /api/s2p/novelty/status` | `gen-ai-roi-demo-v4-v50/frontend/src/components/NoveltyPanel.tsx:47` | Yes — shared native/preview use |
| `GET /api/s2p/simulation/scenarios` | `gen-ai-roi-demo-v4-v50/frontend/src/components/DisruptionSimPanel.tsx:44` | Yes — shared native/preview use |
| `GET /api/s2p/simulation/impact-summary` | `gen-ai-roi-demo-v4-v50/frontend/src/components/DisruptionSimPanel.tsx:45` | Yes — shared native/preview use |
| `GET /api/s2p/suppliers/payment-strategy` | `gen-ai-roi-demo-v4-v50/frontend/src/components/WorkingCapitalPanel.tsx:55` | Yes — shared native/preview use |
| `GET /api/s2p/suppliers/payment-portfolio` | `gen-ai-roi-demo-v4-v50/frontend/src/components/WorkingCapitalPanel.tsx:56` | **No — PREVIEW_ONLY** |
| `GET /api/s2p/suppliers/trends` | `gen-ai-roi-demo-v4-v50/frontend/src/components/TrendCorrelationPanel.tsx:42` | **No — PREVIEW_ONLY** |
| `GET /api/s2p/suppliers/early-warnings` | `gen-ai-roi-demo-v4-v50/frontend/src/components/TrendCorrelationPanel.tsx:43` | Yes — shared native/preview use |
| `GET /api/s2p/insight/process-signals` | `gen-ai-roi-demo-v4-v50/frontend/src/components/ProcessFusionPanel.tsx:32` | Yes — shared native/preview use |
| `GET /api/s2p/insight/cross-graph` | `gen-ai-roi-demo-v4-v50/frontend/src/components/ProcessFusionPanel.tsx:33` | Yes — shared native/preview use |
| `GET /health` | `gen-ai-roi-demo-v4-v50/frontend/src/components/DomainApplicabilityPanel.tsx:44` | **No — PREVIEW_ONLY** |

There are 15 API call sites plus one health probe; six target endpoints have no native S2P caller. These six are retained as PREVIEW_ONLY, not missing native UI. /preview/compounding and /preview/config are **not** among current SOC preview calls. No DataOps preview consumer was found in the other four native frontends or SOC.

### Part B — monkeypatch, mock and production compatibility inventory

The DataOps scan found **54 explicit patch operations**, 102 lines mentioning monkeypatch across 7 files. S2P has **168 explicit patch operations**, 338 mention lines across 34 files; explicit operations occur in 33 files. These are different denominators: fixture declarations/comments add mention lines, while a patch inside a loop is one source operation, not one runtime application.

All **222 explicit operations** are individually indexed below. One S2P patch changes the very reset behavior asserted by four tests; the other 221 are acceptable at their stated unit-test boundary. This does not mean 221 full production/integration proofs: some deliberately replace scorer, persistence, graph or conservation dependencies. Those limitations are called out below. No stale target was confirmed among the 222 explicit patch operations. One additional ignored injected factory is a stale test double and is counted separately.

#### DS-B1 — CIRCULAR, P1: global reset patch conceals the append-only contract

**Production behavior:** `copilot-sdk/copilot_sdk/evolution/graph_store.py:186` raises RuntimeError for reset because AGE evolution history is append-only. `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:197` delegates reset to that store. S2P binds GraphVariantStore at `s2p-copilot/backend/app/services/s2p_evolver.py:31`; its reset service calls the same method at line 223. The registered `POST /api/s2p/evolution/reset` invokes it at `s2p-copilot/backend/app/routers/s2p_evolution.py:89`.

**Patch:** the autouse fixture replaces GraphVariantStore.reset for every test at `s2p-copilot/backend/tests/conftest.py:184`; its substitute clears the in-memory store at line 180.

**Tests asserting the substituted reset behavior:**

- `s2p-copilot/backend/tests/test_s2p_evolution_router.py:112` — expects HTTP 200 and status reset.
- `s2p-copilot/backend/tests/test_s2p_evolution_router.py:123` — expects variant statistics reset.
- `s2p-copilot/backend/tests/test_s2p_evolver.py:246` — expects reset to re-register variants and clear totals.
- `s2p-copilot/backend/tests/test_s2p_evolution_dimensions.py:102` — includes reset in its all-endpoints-return-200 loop.

**Classification:** one CIRCULAR patch site, four affected test functions, three test files plus conftest. The tests exercise surrounding router/evolver code, but their central success premise is supplied by replacing a production rejection with a clearing implementation. This is not a production hook added for tests; it is a test replacing an actual product method. In an ordinary GraphVariantStore-backed run, a reset that reaches the store raises instead. No runtime request was made to demonstrate that exception.

**Injection replacement / fix approach:** test the append-only rejection with the real adapter; initialize a new isolated store per test rather than patching its methods. If a user-visible reset is required, specify an append-only epoch/baseline transition before exposing it. Do not make the real store destructive just to match these tests.

#### DS-B2 — BLOCKING, P1/P2: four production branches select behavior from pytest

| Copilot | Production hook | What changes | Test users | Explicit replacement and non-test impact |
|---|---|---|---|---|
| DataOps | `copilot-sdk/apps/dataops/backend/app/main.py:103` | _resolve_profile chooses the test profile from PYTEST_CURRENT_TEST or imported pytest; the derived _is_demo_or_test_mode at line 111 also influences setup/fallbacks. | Shared client construction at `copilot-sdk/apps/dataops/backend/tests/conftest.py:85`; all direct factory/client-fixture users are indexed below. | Inject RuntimeSettings/profile into create_app and pass an explicit isolated test store; retain current production defaults. Removing detection without explicit fixture configuration changes existing tests. |
| DataOps | `copilot-sdk/apps/dataops/backend/app/context_router.py:125` | Demo mode is true whenever pytest's current-test environment variable exists, even without DATAOPS_DEMO_MODE=1. | Tests reaching context/demo routes via that shared client; all fixture users indexed below are potentially affected by this ambient condition. | Inject a demo-data/provider policy independently of the test runner; test both explicit demo-on and demo-off modes. An ordinary process without pytest keeps its current demo flag semantics. |
| S2P | `s2p-copilot/backend/app/main.py:113` | Runtime/store profile automatically becomes test when pytest is present. | Import-time app creation via `s2p-copilot/backend/tests/conftest.py:82` and isolated scorer setup at line 194; all suite tests inherit the autouse fixture. Direct factory users are indexed below. | Supply an explicit profile/store through an app factory; ordinary callers keep the production profile. No non-test caller specifically requiring imported pytest was found. |
| S2P | `s2p-copilot/backend/app/framework/audit.py:66` | An unconfigured audit store returns None under pytest and uses the legacy in-memory EvidenceLedger; an ordinary process raises. Graph-backed writes and the legacy path diverge at lines 177 and 208. | `s2p-copilot/backend/tests/test_audit.py:6`, fixture clearing private ledger state at line 15, and nine behavior tests at lines 24, 43, 64, 90, 98, 121, 148, 169 and 191. No other direct audit-module test import was found. | Inject an AuditRepository/GraphStore explicitly into the audit service, including tests. Startup already configures the store at `s2p-copilot/backend/app/main.py:363`; properly initialized non-test use should not need the pytest fallback. An unconfigured service should fail consistently. |

**Severity:** P1 for the audit-storage split because it can hide missing startup/storage wiring; P2 for ambient profile/demo selection as test-to-product coupling. These are **four BLOCKING production test-dependent sites, not four monkeypatch calls**. No new production factor-alias/override hook specifically invoked by monkeypatch was established in these two copilots.

The S2P audit fixture edits legacy ledger internals while startup can bind a separate graph store. This is also a test-order/lifespan coverage risk: tests without startup exercise a different persistence path from a lifespan-enabled client. The read-only audit does not claim a currently failing test.

#### DS-B3 — BLOCKING/obsolete compatibility helper, P2: DataOps reset does nothing

**Production hook:** `copilot-sdk/apps/dataops/backend/app/ae_router.py:26`, reset_ae_fixtures(), is explicitly a backward-compatible no-op retained for tests. **All users:** `copilot-sdk/apps/dataops/backend/tests/conftest.py:69`, line 75 and line 81.

**Injection replacement / fix approach:** remove the no-op and its three setup/teardown calls, or give a real fixture-owned cache an explicit lifecycle if one is introduced. No application caller was found, so removing this hook should not affect non-test code. This is one obsolete production compatibility helper and three ineffective setup calls, **not three stale monkeypatch operations**.

#### DS-B4 — STALE, P2: injected shadow factory is discarded

**Production evidence:** initialize_s2p_shadow_state accepts store_factory at `s2p-copilot/backend/app/s2p_shadow.py:255` and unconditionally deletes it at line 263.

**Test:** `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:200` passes a factory at line 210 and asserts at line 214 that it was not called when shadow is disabled. That factory cannot be called in any mode; the negative assertion no longer distinguishes disabled from enabled construction. The state assertions retain value.

**Injection replacement / fix approach:** remove the obsolete parameter and assert the real construction boundary using an explicitly supplied store/factory in the owner responsible for construction. Current startup passes store= at `s2p-copilot/backend/app/main.py:257`; the sole store_factory= caller of this initializer found is this test. Count: **one stale injected test double, zero stale explicit monkeypatch sites**.

#### DS-B5 — ACCEPTABLE doubles with important proof limits, P2

These are not classified as circular merely because they return fixed values: the assertions test a distinct adapter, orchestration, failure or cache boundary.

- **S2P projection/delegation:** `tests/test_financial_router.py:290` substitutes compute_financial_impact and checks delegation; `tests/test_s2p_iks.py:112` checks the app-state scorer is used; `tests/test_s2p_preview.py:284` explicitly rejects the write-capable score method and checks score_read_only output. They do not validate financial arithmetic, IKS calculation or scorer accuracy. Keep those boundaries and pair them with real scorer/store tests instead of citing them as mathematical correctness evidence.
- **S2P cache behavior:** `tests/test_s2p_preview.py:310` changes its sentinel between requests and asserts fresh calls/output; `tests/test_s2p_performance.py:304` expires a cached timestamp and asserts another source read. The thing under test is invalidation, not the fixed backend values; these are useful non-tautological tests.
- **S2P partial learning flow:** `tests/test_l5_full_flow_s2p.py:73` uses a real scorer but bypasses conservation snapshots, evidence receipts, supplier updates, evolution and shadow writes at lines 82–87. Its three L5 state assertions remain meaningful; “full flow” does not establish the complete evidence/governance workflow. `tests/test_l5_dk_s2p_hook.py:143` additionally substitutes learning for a targeted DK persistence hook test.
- **S2P synthetic latency tests:** `tests/test_s2p_score_endpoint.py:155` replaces the scorer, context, conservation and side effects. The concurrent test at line 170 proves scheduling under controlled sleeps, not AGE/persistence/browser latency. Failure-injection and coalescing tests around the same helpers remain appropriate for their local contracts.
- **S2P global bootstrap substitutions:** `tests/conftest.py:80` directly assigns a factory replacement and line 99 replaces build_s2p_scorer for the module lifetime. These are two manual substitutions outside the 168-call count. They support isolation but should become factory inputs to avoid globally altering bootstrap for every collected test.
- **DataOps graph doubles:** `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:9` uses canned graph responses for adapter mapping. `tests/test_dataops_graph_status.py:244` patches graph reads for a no-write assertion; neither establishes Cypher/AGE behavior. The injected FakeAGEStore at line 436 is a separate store-selection/protocol boundary, not proof of live persistence.
- **DataOps bundle naming:** `tests/test_bundle_wiring.py:46` and line 55 set GRAPH_BACKEND=age while using SQLite storage. The variable is still read by `copilot-sdk/copilot_sdk/demo/bundle.py:153`, so these are not stale environment patches. Their claims are limited to bundle compatibility/logging, not AGE restoration.

Paths beginning `tests/` in the S2P bullets mean `s2p-copilot/backend/tests/`; DataOps `tests/` means `copilot-sdk/apps/dataops/backend/tests/`.

A further test-shaped production condition exists at `s2p-copilot/backend/app/routers/s2p.py:2434`: one duplicate-resolution guard depends on shadow test_mode and the private store attribute _store. No direct monkeypatch consumer for that condition was found. It is recorded as a contract-review concern rather than counted as another proven test-only monkeypatch hook. The current shadow test at `s2p-copilot/backend/tests/test_s2p_shadow_phase2.py:389` expects identical repeated outcomes to return 200, so it would be inaccurate to report that test as proving a universal 409 contract.

#### Explicit patch operations — complete source-site index

ACCEPTABLE means the stated unit boundary remains under test; it does not certify production integration. CIRCULAR is reserved here for the reset replacement in DS-B1. No patch is labelled stale merely because it uses raising=False. All rows give the exact operation location and enclosing test/fixture, so a shared fixture is counted once even when many tests use it.

##### DataOps patch sites

| Operation file:line | Enclosing test/fixture | Patch target | Category | Reason / scope |
|---|---|---|---|---|
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:27` | `dataops_data_dir` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:28` | `dataops_data_dir` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:35` | `dataops_data_dir` | `key` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:70` | `dataops_data_dir` | `context_router.DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:71` | `dataops_data_dir` | `context_router.METADATA_PATH` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:72` | `dataops_data_dir` | `ae_router.DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:73` | `dataops_data_dir` | `main.DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:74` | `dataops_data_dir` | `main.DEFAULT_DB_PATH` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:191` | `no_graph` | `"GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:192` | `no_graph` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:193` | `no_graph` | `"DATABASE_URL"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/conftest.py:194` | `no_graph` | `"AGE_GRAPH_NAME"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py:46` | `test_bundle_restore_returns_true_for_age_backend` | `"GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py:55` | `test_bundle_restore_still_writes_sqlite_for_age_backend` | `"GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:128` | `test_ci_data_dir_creates_db` | `"CI_DATA_DIR"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:143` | `test_explicit_db_path_wins` | `"CI_DATA_DIR"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:156` | `test_no_env_uses_explicit_fallback` | `"CI_DATA_DIR"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:202` | `test_l5_startup_restore_runs_after_seed_setup` | `app_main._auto_seed_if_needed` | ACCEPTABLE | Startup sequencing spies verify order, not the replaced seed/restore implementations. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:203` | `test_l5_startup_restore_runs_after_seed_setup` | `app_main._seed_demo_evolution_events_if_needed` | ACCEPTABLE | Startup sequencing spies verify order, not the replaced seed/restore implementations. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:204` | `test_l5_startup_restore_runs_after_seed_setup` | `app_main.restore_l5_runtime_state` | ACCEPTABLE | Startup sequencing spies verify order, not the replaced seed/restore implementations. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:52` | `test_graph_status_ignores_generic_graph_env` | `"GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:53` | `test_graph_status_ignores_generic_graph_env` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:54` | `test_graph_status_ignores_generic_graph_env` | `"GRAPH_NAME"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:244` | `test_read_and_operational_routes_do_not_create_scorer_decisions_under_active_age` | `DataOpsGraphClient._run_graph` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:393` | `_configure_explicit_sqlite` | `"GRAPH_CONFIG_PATH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:394` | `_configure_explicit_sqlite` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:399` | `_set_active_age_env` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:400` | `_set_active_age_env` | `"DATAOPS_ACTIVE_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:401` | `_set_active_age_env` | `"DATAOPS_ACTIVE_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:402` | `_set_active_age_env` | `"DATAOPS_ACTIVE_AGE_DOMAIN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:403` | `_set_active_age_env` | `"DATAOPS_ACTIVE_AGE_TEST_MODE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:423` | `_clear_active_env` | `key` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:22` | `test_celonis_status_alias_is_offline_safe` | `"CELONIS_URL"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:37` | `test_sap_status_alias_is_offline_safe` | `"SAP_API_KEY"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:77` | `test_enterprise_health_alias_handles_subsystem_failure` | `dataops_status._sap_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:294` | `_patch_context_connectors` | `context_router._sap_connector` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:295` | `_patch_context_connectors` | `context_router._celonis_connector` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:112` | `test_age_client_constructor_receives_graph_name` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:113` | `test_age_client_constructor_receives_graph_name` | `"DATAOPS_ACTIVE_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:114` | `test_age_client_constructor_receives_graph_name` | `"DATAOPS_ACTIVE_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:139` | `test_dataops_graph_client_uses_active_config` | `"DATAOPS_ACTIVE_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:140` | `test_dataops_graph_client_uses_active_config` | `"DATAOPS_ACTIVE_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:141` | `test_dataops_graph_client_uses_active_config` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:157` | `test_dataops_graph_client_uses_generic_age_config` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:158` | `test_dataops_graph_client_uses_generic_age_config` | `"DATAOPS_ACTIVE_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:159` | `test_dataops_graph_client_uses_generic_age_config` | `"DATAOPS_ACTIVE_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:160` | `test_dataops_graph_client_uses_generic_age_config` | `"GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:161` | `test_dataops_graph_client_uses_generic_age_config` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:162` | `test_dataops_graph_client_uses_generic_age_config` | `"AGE_GRAPH_NAME"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:179` | `test_dataops_graph_client_rejects_missing_dataops_config` | `"DATAOPS_ACTIVE_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:180` | `test_dataops_graph_client_rejects_missing_dataops_config` | `"DATAOPS_ACTIVE_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:181` | `test_dataops_graph_client_rejects_missing_dataops_config` | `"DATAOPS_ACTIVE_GRAPH_BACKEND"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:182` | `test_dataops_graph_client_rejects_missing_dataops_config` | `"GRAPH_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `copilot-sdk/apps/dataops/backend/tests/test_graph_queries.py:183` | `test_dataops_graph_client_rejects_missing_dataops_config` | `"AGE_GRAPH_NAME"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |

##### S2P patch sites

| Operation file:line | Enclosing test/fixture | Patch target | Category | Reason / scope |
|---|---|---|---|---|
| `s2p-copilot/backend/tests/conftest.py:184` | `isolated_age_compatible_evolver` | `GraphVariantStore.reset` | CIRCULAR | DS-B1: replaces forbidden reset with clearing; four tests assert the replacement behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:103` | `test_invalid_values_return_400` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:124` | `test_boundaries_pass_validation_but_gate_can_reject` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:136` | `test_non_green_conservation_returns_409` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:145` | `test_green_conservation_import_updates_isolated_centroids` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:179` | `test_export_reads_imported_centroids` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:192` | `test_checkpoint_failure_rolls_back` | `s2p_explorer._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_centroid_import.py:197` | `test_checkpoint_failure_rolls_back` | `s2p_explorer._checkpoint_imported_centroids` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:43` | `test_consumer_returns_signals_from_valid_endpoint` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:55` | `test_consumer_matches_supplier_case_insensitively` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:67` | `test_consumer_filters_mismatched_supplier` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:79` | `test_consumer_returns_empty_when_purchasing_offline` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:85` | `test_consumer_filters_expired_signals` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:94` | `test_consumer_returns_empty_for_no_signal_supplier` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_cross_copilot_signals.py:103` | `test_consumer_does_not_crash_on_malformed_response` | `monkeypatch.setattr` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:111` | `test_learn_appends_evidence_receipt_before_outcome_write` | `store.append_evidence_receipt` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:112` | `test_learn_appends_evidence_receipt_before_outcome_write` | `store.write_outcome` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:159` | `test_append_failure_without_outbox_prevents_outcome` | `store.append_evidence_receipt` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:160` | `test_append_failure_without_outbox_prevents_outcome` | `store.enqueue_to_outbox` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:196` | `test_append_failure_enqueues_outbox_then_writes_outcome` | `store.append_evidence_receipt` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:197` | `test_append_failure_enqueues_outbox_then_writes_outcome` | `store.enqueue_to_outbox` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:198` | `test_append_failure_enqueues_outbox_then_writes_outcome` | `store.write_outcome` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:313` | `test_outcome_route_receipt_failure_blocks_outcome_write` | `store.append_evidence_receipt` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:314` | `test_outcome_route_receipt_failure_blocks_outcome_write` | `store.enqueue_to_outbox` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:348` | `test_outcome_route_outbox_fallback_precedes_outcome_write` | `store.append_evidence_receipt` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:349` | `test_outcome_route_outbox_fallback_precedes_outcome_write` | `store.enqueue_to_outbox` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_evolver_conservation.py:86` | `test_provider_returns_live_state` | `s2p_evolution_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_factor_proposer.py:124` | `test_proposer_uses_live_dk_weights` | `factor_proposer_router._read_dk_weights` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_factors.py:179` | `test_compute_all_factors_catches_factor_errors` | `factors.ALL_FACTORS` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_financial_router.py:80` | `_set_financial_state` | `financial_router.get_receipt_store` | ACCEPTABLE | DS-B5: delegation/projection boundary, not computation or live storage correctness. |
| `s2p-copilot/backend/tests/test_financial_router.py:298` | `test_financial_impact_uses_p28_compute_function` | `financial_router.compute_financial_impact` | ACCEPTABLE | DS-B5: delegation/projection boundary, not computation or live storage correctness. |
| `s2p-copilot/backend/tests/test_graph_links.py:126` | `test_score_endpoint_still_returns_200_when_linking_fails` | `app.state.graph_store.link_decision_to_entity` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_graph_links.py:141` | `test_outcome_still_returns_200_when_learn_linking_fails` | `app.state.graph_store.link_decision_to_entity` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_graphstore_consolidation.py:127` | `test_find_invoice_by_invoice_id` | `s2p_data_helpers._DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `s2p-copilot/backend/tests/test_graphstore_consolidation.py:145` | `test_find_invoice_by_event_id` | `s2p_data_helpers._DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:139` | `_reset_tracker` | `s2p_router._S2P_DK_WELFORD_TRACKER` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:149` | `_install_endpoint_state` | `app.state.scorer` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:150` | `_install_endpoint_state` | `app.state.graph_store` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:155` | `_install_endpoint_state` | `app.state.learning_store` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:156` | `_install_endpoint_state` | `s2p_router._receipt_conservation_snapshot` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:157` | `_install_endpoint_state` | ` s2p_router._append_evidence_receipt_before_outcome` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:163` | `_install_endpoint_state` | `s2p_router._record_outcome_receipt` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:164` | `_install_endpoint_state` | `s2p_router._record_supplier_profile` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:165` | `_install_endpoint_state` | `s2p_router._record_evolver_outcome_if_allowed` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:166` | `_install_endpoint_state` | `s2p_router._record_outcome_shadow` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:179` | `_install_endpoint_state` | ` s2p_router._learn_with_scorer` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:78` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `app.state.scorer` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:79` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `app.state.graph_store` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:80` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `app.state.learning_store` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:81` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._S2P_DK_WELFORD_TRACKER` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:82` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._receipt_conservation_snapshot` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:83` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._append_evidence_receipt_before_outcome` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:84` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._record_outcome_receipt` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:85` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._record_supplier_profile` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:86` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._record_evolver_outcome_if_allowed` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:87` | `test_s2p_full_learn_flow_writes_all_three_l5_state_types` | `s2p_router._record_outcome_shadow` | ACCEPTABLE | DS-B5: isolated L5 persistence boundary; evidence/full learning workflow is not established. |
| `s2p-copilot/backend/tests/test_lead_time.py:345` | `test_supplier_endpoint_known_supplier_no_valid_samples_safe_if_constructible` | `lead_time_router.load_suppliers` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_lead_time.py:346` | `test_supplier_endpoint_known_supplier_no_valid_samples_safe_if_constructible` | `lead_time_router.load_invoices` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:71` | `test_learn_returns_200_when_conservation_not_green` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:82` | `test_learn_without_variant_id_never_returns_422` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:95` | `test_learn_records_outcome_when_paused` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:109` | `test_evolver_not_called_when_paused` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:114` | `test_evolver_not_called_when_paused` | `s2p_router.record_triage_outcome` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:131` | `test_evolver_called_when_not_paused_and_variant_id_present` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_learn_conservation_guard.py:136` | `test_evolver_called_when_not_paused_and_variant_id_present` | `s2p_router.record_triage_outcome` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_novelty.py:300` | `test_score_novelty_score_json_safe_inf_to_null` | ` s2p_router.compute_nearest_distance` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:398` | `test_chain_grows_with_multiple_learns` | `s2p_router._receipt_conservation_snapshot` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:399` | `test_chain_grows_with_multiple_learns` | `s2p_router._learn_with_scorer` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:413` | `test_learn_receipt_contains_conservation_before_after` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:467` | `test_paused_learning_without_variant_still_creates_receipt` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:490` | `test_receipt_not_created_when_scorer_pauses_before_outcome_write` | `s2p_router._learn_with_scorer` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:522` | `test_receipt_created_when_learn_result_proves_outcome_recorded` | `s2p_router._receipt_conservation_snapshot` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:523` | `test_receipt_created_when_learn_result_proves_outcome_recorded` | `s2p_router._learn_with_scorer` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:538` | `test_receipt_weight_updated_tracks_verified_delta` | `s2p_router._receipt_conservation_snapshot` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:539` | `test_receipt_weight_updated_tracks_verified_delta` | ` s2p_router._learn_with_scorer` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:559` | `test_receipt_exportable_false_when_evidence_receipt_queued` | ` s2p_router._append_evidence_receipt_before_outcome` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_outcome_receipt.py:578` | `test_paused_learning_without_variant_still_does_not_422` | ` s2p_router._learn_with_scorer` | ACCEPTABLE | Receipt/DK orchestration boundary; injected learning/conservation is not itself verified. |
| `s2p-copilot/backend/tests/test_preview.py:40` | `test_preview_queue_includes_process_context_when_celonis_cache_available` | ` s2p_preview._load_celonis_cache` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py:487` | `test_active_age_shadow_lifecycle_allows_shared_store_construction` | `"S2P_SHADOW_AGE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:85` | `reset_gate` | `p40_router.gate` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:90` | `reset_gate` | `p40_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:275` | `test_conservation_red_blocks` | `p40_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:293` | `test_conservation_amber_blocks` | `p40_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:310` | `test_conservation_green_required` | `p40_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:171` | `test_expansion_proof_safe_to_expand` | `s2p_router._graph_verified_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:172` | `test_expansion_proof_safe_to_expand` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:184` | `test_expansion_proof_insufficient_data` | `s2p_router._graph_verified_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:185` | `test_expansion_proof_insufficient_data` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:195` | `test_expansion_proof_low_accuracy` | `s2p_router._graph_verified_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:196` | `test_expansion_proof_low_accuracy` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:206` | `test_expansion_proof_includes_evidence` | `s2p_router._graph_verified_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:207` | `test_expansion_proof_includes_evidence` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:218` | `test_expansion_proof_category_filter` | `s2p_router._graph_verified_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_auto_approve.py:219` | `test_expansion_proof_category_filter` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_control_tower.py:154` | `test_control_tower_does_not_call_compounding_scorer` | `app.state.scorer.score` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_data_helpers.py:41` | `test_missing_invoice_file_returns_empty_list` | `s2p_data_helpers._DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `s2p-copilot/backend/tests/test_s2p_data_helpers.py:47` | `test_missing_supplier_file_returns_empty_list` | `s2p_data_helpers._DATA_DIR` | ACCEPTABLE | Isolated filesystem path; real file behavior remains under test. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:471` | `test_run_endpoint_dry_run_returns_receipt_without_persisting` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:490` | `test_run_endpoint_persist_returns_persisted_receipts` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:504` | `test_supplier_endpoint_returns_enriched_supplier` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:514` | `test_supplier_endpoint_unknown_supplier_safe` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:526` | `test_summary_endpoint_sorted_by_exception_rate_desc` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:539` | `test_alerts_endpoint_flags_only_verified_measured_metrics` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_enrichment.py:550` | `test_zero_data_summary_safe` | `app.state.graph_store` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_evidence.py:515` | `test_evidence_template_missing_variable_renders_na` | ` s2p_evidence._load_invoices` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_evidence.py:649` | `test_compliance_empty_invoice_list` | `s2p_evidence._load_invoices` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py:86` | `test_production_config_fails_closed_when_age_dsn_is_missing` | `name` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_iks.py:117` | `test_iks_endpoint_uses_app_state_scorer` | `app.state.scorer` | ACCEPTABLE | DS-B5: delegation/projection boundary, not computation or live storage correctness. |
| `s2p-copilot/backend/tests/test_s2p_insight.py:116` | `test_cross_graph_empty_when_no_data` | `s2p_insight._load_suppliers` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_insight.py:117` | `test_cross_graph_empty_when_no_data` | `s2p_insight._load_celonis` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_performance.py:310` | `test_summary_cache_expires` | `s2p_performance.SUMMARY_CACHE_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_preview.py:301` | `test_preview_queue_uses_app_state_scorer` | `app.state.scorer` | ACCEPTABLE | DS-B5: delegation/projection boundary, not computation or live storage correctness. |
| `s2p-copilot/backend/tests/test_s2p_preview.py:334` | `test_preview_queue_recomputes_after_live_scorer_state_changes` | `app.state.scorer` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_preview.py:374` | `test_preview_queue_limit_does_not_score_full_fixture` | `app.state.scorer` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_pvg.py:60` | `test_variants_uses_true_median_for_even_activity_counts` | ` s2p_pvg._load_process_data` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:157` | `_install_fast_score_dependencies` | `app.state.scorer` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:158` | `_install_fast_score_dependencies` | `app.state.graph_store` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:159` | `_install_fast_score_dependencies` | `s2p_router._resolve_graph_context` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:160` | `_install_fast_score_dependencies` | `s2p_router._apply_cross_copilot_signal` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:161` | `_install_fast_score_dependencies` | `s2p_router._score_conservation_status` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:162` | `_install_fast_score_dependencies` | `s2p_router.get_active_variant` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:163` | `_install_fast_score_dependencies` | `s2p_router._link_decision_to_invoice` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:165` | `_install_fast_score_dependencies` | `s2p_router._submit_side_effect` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:166` | `_install_fast_score_dependencies` | `s2p_router.apply_cache_invalidation_event` | ACCEPTABLE | DS-B5: controlled scoring latency/orchestration; persistence and real scorer are bypassed. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:177` | `test_score_concurrent_not_serialized_on_enrichment` | `s2p_router._score_process_context_with_signal` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:198` | `test_fire_and_forget_failure_logged` | `s2p_router._record_score_shadow` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:239` | `test_enrichment_failure_doesnt_break_score` | `s2p_router._score_process_context_with_signal` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:263` | `test_score_response_includes_cached_conservation_status` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:280` | `test_score_conservation_status_cache_expires` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:281` | `test_score_conservation_status_cache_expires` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:307` | `test_concurrent_score_requests_coalesce_conservation_status` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:340` | `test_concurrent_full_conservation_requests_do_not_serialize_counts` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:373` | `test_browser_like_conservation_and_score_waterfall_shares_counts_cache` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:501` | `test_full_conservation_counts_cache_expires` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:502` | `test_full_conservation_counts_cache_expires` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:533` | `test_conservation_cache_returns_value_within_ttl` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:534` | `test_conservation_cache_returns_value_within_ttl` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:557` | `test_conservation_cache_recomputes_after_ttl` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:558` | `test_conservation_cache_recomputes_after_ttl` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:582` | `test_conservation_cache_cleared_on_learn` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:583` | `test_conservation_cache_cleared_on_learn` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:596` | `test_conservation_cache_readers_do_not_block_on_miss` | `s2p_router._SCORE_CONSERVATION_STATUS_TTL_SECONDS` | ACCEPTABLE | Controlled cache lifetime; cache expiry/coalescing is the asserted behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:620` | `test_conservation_cache_readers_do_not_block_on_miss` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:649` | `test_conservation_cache_miss_is_idempotent` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:664` | `test_current_conservation_status_failure_remains_unknown` | `s2p_router._read_conservation_counts` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:709` | `test_score_endpoint_uses_compute_all_factors` | `s2p_router.compute_all_factors` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:738` | `test_score_endpoint_uses_graph_context_when_available` | `s2p_router.compute_all_factors` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:767` | `test_score_endpoint_graph_context_failure_degrades_gracefully` | `s2p_router.compute_all_factors` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:802` | `test_score_endpoint_graph_context_timeout_degrades_gracefully` | `s2p_router.compute_all_factors` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:929` | `test_learn_with_variant_id_records_outcome` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:954` | `test_learn_with_variant_id_records_evolver_outcome` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1019` | `test_accumulator_failure_does_not_break_learn` | `s2p_router.supplier_profile_accumulator.on_decision_verified` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1052` | `test_positive_reward_records_success` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1075` | `test_negative_reward_records_failure` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1105` | `test_score_includes_process_context_when_available` | `s2p_router._SCORE_PROCESS_CONTEXT_CACHE` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1106` | `test_score_includes_process_context_when_available` | ` s2p_router._load_celonis_cache` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1133` | `test_score_omits_process_context_when_unavailable` | `s2p_router._SCORE_PROCESS_CONTEXT_CACHE` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1134` | `test_score_omits_process_context_when_unavailable` | `s2p_router._load_celonis_cache` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:1169` | `test_outcome_with_variant_id_records_evolver_outcome` | `s2p_router._current_conservation_status` | ACCEPTABLE | Dependency/failure/adapter boundary; assert the unpatched enclosing behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:43` | `test_shadow_config_no_arg_reads_os_environ` | `"S2P_SHADOW_AGE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:44` | `test_shadow_config_no_arg_reads_os_environ` | ` "S2P_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:48` | `test_shadow_config_no_arg_reads_os_environ` | `"S2P_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:49` | `test_shadow_config_no_arg_reads_os_environ` | `"S2P_AGE_TEST_MODE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:60` | `test_shadow_config_explicit_mapping_ignores_os_environ` | `"S2P_SHADOW_AGE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:61` | `test_shadow_config_explicit_mapping_ignores_os_environ` | `"S2P_AGE_DSN"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:62` | `test_shadow_config_explicit_mapping_ignores_os_environ` | `"S2P_AGE_GRAPH"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:63` | `test_shadow_config_explicit_mapping_ignores_os_environ` | `"S2P_AGE_TEST_MODE"` | ACCEPTABLE | Isolated environment/configuration input; does not claim live backend behavior. |
| `s2p-copilot/backend/tests/test_supplier_intel_cascade.py:136` | `test_sec_user_agent_set` | `urllib.request.urlopen` | ACCEPTABLE | External HTTP/graph/connector response or failure is controlled for hermetic unit coverage. |

#### Direct app-factory and shared-client users of ambient profile selection

These are the complete static direct create_app/build_s2p_scorer callers and DataOps client-fixture users found in backend test files. Transitive helpers can affect additional tests; the S2P autouse fixture applies to the entire suite. None of these rows is an explicit monkeypatch of _resolve_profile; the coupling is ambient pytest detection, as distinguished in DS-B2.

| Copilot | Test file and source locations | Kind |
|---|---|---|
| dataops | `copilot-sdk/apps/dataops/backend/tests/conftest.py:88` | create_app |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py:17`; `copilot-sdk/apps/dataops/backend/tests/test_bundle_wiring.py:23` | create_app |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_cohort_status.py:178` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:22`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:31`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:44`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:56`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:66`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:77`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:86`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:98`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:118`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:129`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:145`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:158`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:168`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:206`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:214`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:222`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:234`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:243`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:252`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:261`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:270`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:279`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:290`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:300`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:310`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:333`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:353`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:365`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:375`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:385`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:393`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:424`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:444`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:456`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:465`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:474`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:487`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:501`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:511`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:521`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:534`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:544`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:555`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:563`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:572`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:579`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:589`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:599`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:607`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:620`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:633`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:643`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:650`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:662`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:673`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:681`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:689`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:700`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:723`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:743`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:751`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:759`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:767`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:775`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:785`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:793`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:804`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:812`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:821`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:828`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:839`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:850`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:864`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:871`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:881`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:889`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:900`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:910`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:918`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:935`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:944`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:956`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:971`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:983`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:994`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1001`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1008`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1033`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1046`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1067`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1077`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1087`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1097`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1107`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1117`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1133`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1142`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1155`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1163`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1190`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1205`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1215`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1245`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1257`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1267`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1276`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1293`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:1300` | client fixture; create_app; app_main.create_app |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_dataops_fixture_closure.py:131`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_fixture_closure.py:141` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:6`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:11`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:16`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:21`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:27`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:31`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:38`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:43`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:47`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:53`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:60`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:64`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:69`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:74`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:81`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:85`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:93`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:98`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:104`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:109` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:34`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:56`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:182`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:271`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:336`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:345`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_graph_status.py:354` | create_app; client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:9`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:21`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:36`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:51`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:71`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_status.py:89` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_di.py:114`; `copilot-sdk/apps/dataops/backend/tests/test_di.py:121` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_di_demo_beats.py:18`; `copilot-sdk/apps/dataops/backend/tests/test_di_demo_beats.py:24`; `copilot-sdk/apps/dataops/backend/tests/test_di_demo_beats.py:30` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:6`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:11`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:17`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:25`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:31`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:36`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:41`; `copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:48` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:170`; `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:181`; `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:190`; `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:200`; `copilot-sdk/apps/dataops/backend/tests/test_enterprise_connectors.py:211` | client fixture |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_evolution_dataops.py:82`; `copilot-sdk/apps/dataops/backend/tests/test_evolution_dataops.py:104` | client fixture; create_app |
| dataops | `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:7`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:13`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:19`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:27`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:37`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:46`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:62`; `copilot-sdk/apps/dataops/backend/tests/test_transfer_status.py:69` | client fixture |
| s2p | `s2p-copilot/backend/tests/conftest.py:96`; `s2p-copilot/backend/tests/conftest.py:194` | _build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_centroid_explorer.py:285`; `s2p-copilot/backend/tests/test_centroid_explorer.py:299`; `s2p-copilot/backend/tests/test_centroid_explorer.py:316`; `s2p-copilot/backend/tests/test_centroid_explorer.py:343`; `s2p-copilot/backend/tests/test_centroid_explorer.py:352`; `s2p-copilot/backend/tests/test_centroid_explorer.py:378`; `s2p-copilot/backend/tests/test_centroid_explorer.py:395` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_centroid_import.py:20` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_context_bridge_removed.py:18` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_domain_isolation.py:180`; `s2p-copilot/backend/tests/test_domain_isolation.py:199` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_evidence_graph_query.py:21` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:28` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_explorer.py:29` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_factor_ranking.py:24` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_financial_impact.py:17` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_financial_router.py:21` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_graphstore_consolidation.py:23`; `s2p-copilot/backend/tests/test_graphstore_consolidation.py:59` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_graph_links.py:19` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_jm_rl_verification.py:37`; `s2p-copilot/backend/tests/test_jm_rl_verification.py:142` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:172` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:75` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_l5_startup_s2p.py:31`; `s2p-copilot/backend/tests/test_l5_startup_s2p.py:53`; `s2p-copilot/backend/tests/test_l5_startup_s2p.py:65` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_learn_conservation_guard.py:36` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_novelty.py:40` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_observation_wiring.py:65`; `s2p-copilot/backend/tests/test_observation_wiring.py:115` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_optimizer_export.py:20` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_outcome_receipt.py:81` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_pydantic_responses.py:34` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_receipt_audit_fields.py:26` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_rule_vs_reasoning.py:10` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_active_age_live.py:44`; `s2p-copilot/backend/tests/test_s2p_active_age_live.py:54` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_active_age_parallel.py:44` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py:330` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_audit_export.py:69` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_auto_approve.py:38` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:87` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_core_router.py:55` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_demo.py:17` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_evidence.py:107`; `s2p-copilot/backend/tests/test_s2p_evidence.py:470` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_explorer_router.py:54` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py:36` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_iks.py:40` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_outcome.py:30` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_performance.py:143` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_preset_and_invoice_link.py:20` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_preview.py:390`; `s2p-copilot/backend/tests/test_s2p_preview.py:413` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_product_like_phase_c2.py:31` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_scorer.py:24`; `s2p-copilot/backend/tests/test_s2p_scorer.py:29`; `s2p-copilot/backend/tests/test_s2p_scorer.py:39` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:62`; `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:735`; `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:764`; `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:799`; `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:850` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_shadow_live_age.py:38` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_shadow_phase1.py:221` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_shadow_phase2.py:144` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_track2_graph_reader_and_factors.py:54` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_s2p_worked_example.py:38` | build_s2p_scorer |
| s2p | `s2p-copilot/backend/tests/test_shadow_retirement.py:17`; `s2p-copilot/backend/tests/test_shadow_retirement.py:73` | build_s2p_scorer |

### Part C — counts, priorities and grouped follow-up prompts

| Count | DataOps | S2P | This continuation |
|---|---:|---:|---:|
| Unique backend endpoints with no native frontend caller | 75 | 166 | **241** |
| PREVIEW_ONLY endpoints within that count | 0 | 6 | **6** |
| Unique endpoints with neither native nor SOC-preview browser caller | 75 | 160 | **235** |
| Active native calls to an absent backend method/path | 0 found | 0 found | **0 found** |
| Dormant helpers targeting absent backend paths | 0 | 2 | **2** |
| Later exact duplicate route registrations shadowed | 7 | 0 | **7** |
| Explicit patch operations indexed | 54 | 168 | **222** |
| ACCEPTABLE explicit operations for their stated unit boundary | 54 | 167 | **221** |
| CIRCULAR explicit patch sites | 0 | 1 | **1** |
| Tests asserting the circular reset substitution | 0 | 4 | **4** |
| STALE explicit patch operations | 0 confirmed | 0 confirmed | **0 confirmed** |
| Additional stale injected test doubles | 0 | 1 | **1** |
| BLOCKING production ambient test branches (not patch calls) | 2 | 2 | **4** |
| Additional obsolete production compatibility helpers | 1 | 0 | **1** |
| New direct factor-alias-style monkeypatch-only production hooks | 0 established | 0 established | **0 established** |

Thus the short requested count summary is **241 endpoints without native consumers, four BLOCKING ambient production branches plus one obsolete test helper, four circular reset tests through one patch, and one stale injected factory**. There are no newly confirmed stale explicit monkeypatch sites. Keeping these denominators separate avoids describing fixture calls, production hooks and test functions as interchangeable “monkeypatches.”

The continuation contains 16 ranked frontend findings (seven DataOps, nine S2P) and five grouped mock/test findings. Not every no-consumer row is a defect. The endpoint tables explicitly identify parallel adapters, preview consumers and APIs whose product ownership remains undecided.

#### Top five findings in this continuation

1. **DS-B1 — a global patch makes an unsupported reset look implemented.** Four tests assert successful reset while the real append-only store raises; this is direct evidence of test substitution concealing a product contract.
2. **DOP-1/DOP-6 — governance can display confidence unsupported by its data.** A validated experiment is labelled a frozen checkpoint, and failed/pending claims can be labelled “Evidence gate clear.” Both occur in mounted native panels.
3. **S2P-1 — the browser and proposal ledger use different outcome lifecycles.** Score creates a proposal; native confirm/override learns without resolving it. A service-level test manually performs the missing step.
4. **S2P-2 — Frozen Twin UI expects fields the server never supplies.** The native panel cannot populate its accuracy curves from the drift report and has no freeze control.
5. **DS-B2 — tests select different production configuration and audit storage.** Four production branches inspect pytest; S2P audit tests can exercise legacy memory storage while ordinary unconfigured use fails.

Next are DataOps' split DI profile caches (DOP-5), S2P's swallowed queue errors and permanently zero shell IKS (S2P-4/S2P-3), and the seven DataOps route collisions (DOP-4).

#### Recommended Codex prompt sequence

| Order | Fix together | Blast radius and required evidence |
|---|---|---|
| 1 | S2P append-only reset contract and DS-B1 tests | S2P evolver/router/conftest plus the SDK variant-store interface. Remove test-wide method replacement; exercise the real rejection contract. Design an epoch transition separately if reset is a product requirement. Do not delete production history. |
| 2 | DataOps governance truthfulness: DOP-1, DOP-2, DOP-6, DOP-7 | Canonical frozen status, holdout/provenance workflow and explicit unavailable states in native governance panels. Verify validation, snapshot existence and evidence approval as separate states. |
| 3 | S2P proposal/outcome/ledger lifecycle: S2P-1 | One idempotent resolution service spanning scorer, proposal and receipt/ledger projections, then typed native controls. Test score → browser confirm/override → proposal/ledger reread with real isolated stores and no substituted outcome path. Avoid two outcome writes from calling both current APIs. |
| 4 | S2P native contract corrections: S2P-2, S2P-3, S2P-4, S2P-8 | Twin drift schema and truthful unavailable state, live shell IKS, strict native queue errors and removal/redirection of dormant generic helpers. Verify both populated and unavailable responses; keep SOC preview optionality separate. |
| 5 | Explicit configuration and audit injection: DS-B2/DS-B3/DS-B4 plus prior TP-B1 | Start with DataOps/S2P app factories and fixtures, then migrate Trading/Purchasing using the prior findings. Preserve production defaults, remove ambient pytest detection and obsolete hooks, and verify ordinary-startup and lifespan-enabled test paths against the same service interfaces. |
| 6 | DataOps route ownership and profiles: DOP-4/DOP-5 | Consolidate DI source/profile state, select one handler per duplicate address and verify the assembled app, not only direct router functions. Check that native source quality agrees with startup profiles and refresh results. |
| 7 | Product-scope decisions for unwired controls/analytics: DOP-3, S2P-5/S2P-6/S2P-9 and API_ONLY rows | Separate native user workflows from documented operator/integration APIs. Wire only retained product features; keep P40B shadow-only semantics and conservation gates. No blanket endpoint deletion based on browser absence. |
| 8 | Legacy adapters and cross-reference cleanup: S2P-7 and unused aliases | Confirm non-browser owners before removing the S2P /api/soc namespace or duplicate adapters. Preserve the six SOC-preview-only endpoints and verify both frontend origins. |

#### Consolidated completion state

| Copilot | Frontend route/consumer audit | Monkeypatch/mock review | Report section |
|---|---|---|---|
| SOC | Earlier completed inventory, not re-run here | Earlier focused findings; exhaustive SDK/SOC/CI semantic inventory remains broader follow-up | Original Part A / Part B above |
| Trading | Completed in earlier continuation | Explicit operations indexed in earlier continuation | Trading/Purchasing continuation |
| Purchasing | Completed in earlier continuation | Explicit operations indexed in earlier continuation | Trading/Purchasing continuation |
| DataOps | **Completed in this continuation** | **54 operations indexed; production hooks reviewed** | DOP-1 through DOP-7 and DS-B sections |
| S2P | **Completed in this continuation, including SOC preview** | **168 operations indexed; reset substitution and stale factory identified** | S2P-1 through S2P-9 and DS-B sections |

Carrying forward the earlier source inventories yields **933 copilot-qualified unique route identities** and **536 without native callers** across five copilots: SOC 139, Trading 81, Purchasing 75, DataOps 75, S2P 166. These include intentional APIs and cross-preview exceptions. SOC/Trading/Purchasing numbers are historical observations, not new verification. The four non-SOC backends now have **425 explicit patch operations** indexed (203 earlier + 222 here). Previous SOC/Trading/Purchasing “circular/fixed-output” classifications used a broader definition than the strict reset substitution established here; they have not been silently added to the new four-test count.

The requested DataOps/S2P discovery is complete. Remaining work is remediation/product ownership, runtime confirmation of source findings, and any separately commissioned exhaustive SOC/SDK/CI mock review. This audit does not claim all repository tests or all endpoints were executed.

**Validation performed:** static source/AST enumeration, method/path matching with mounted component reachability, duplicate precedence, conditional SAML registration, SOC preview origin cross-reference, per-operation patch indexing and report-reference/count checks. No mypy, pytest, browser, live backend or performance gates were run because the task is discovery-only.

**Files changed:** only `copilot-sdk/docs/quality/frontend_wiring_and_mock_audit.md`. No source/test fixes were implemented and no “zero regressions” claim is made.
