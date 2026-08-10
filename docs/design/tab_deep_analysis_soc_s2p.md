# Deep Tab-by-Tab Analysis — SOC + S2P

**Inspection date:** 2026-08-10; live verification rerun after copilot restart  
**Scope:** read-only source and route diagnostic for the SOC frontend (`5173`, backend `8001`) and SDK S2P frontend (`5177`, backend `8002`).  
**Artifact:** this report is the only file created for this investigation. No application source, configuration, test, or backend file was changed.

## Method and status legend

The inventory was built from the tab/screen entry points, their imported components, `lib/api.ts`/`api.ts`, JSX event handlers, and the endpoint list in the task. The demo-beat cross-reference is against `docs/design/demo_scenarios_and_usecases_v2_4.md`.

- **WIRED:** source imports/mounts the component or calls the endpoint.
- **PARTIAL:** a surface or client function exists, but the route is optional, fallback-backed, method-sensitive, or the complete demo path is not proven.
- **STUB/DEMO:** source explicitly uses fixture/sample/demo data or a placeholder path.
- **MISSING:** no source path was found for the requested surface.
- **LIVE VERIFIED:** the restarted service returned the recorded HTTP status and response keys.
- **LIVE UNKNOWN:** no runtime probe was performed for the route, or the source path is indirect.

## 1. Executive summary

| Metric | SOC | S2P |
|---|---:|---:|
| Tabs/screens | 7 tabs | 6 screens |
| Tab/screen entry files | 7 | 6 |
| Component `.tsx` files in component directory | 20 total under `components/` (including the 7 tab files) | 51 |
| Shared API service | `src/lib/api.ts` | `src/api.ts` |
| Primary navigation | `App.tsx` local state and tab buttons | `CopilotShell` with `onTabChange` |
| Static API wiring | Broad; tab APIs and nested panels are wired | Broad; screen APIs and nested panels are wired |
| Live endpoint verification | verified on `8001`; 5 tab-content routes return 200, 2 return 404, method-sensitive routes return 405 | verified on `8002`; core preview, diagnostics, conservation, history, and trust-trap routes return 200 |
| Main gap pattern | Several source calls are legacy aliases or method-sensitive; some tab content is not `/api/soc/tab/N/content` driven | Many components use API helper fallbacks; supplier/profile and evidence paths need populated data to become visibly interactive |

## 2. SOC — shell and navigation

### Routing and clickable navigation

`gen-ai-roi-demo-v4-v50/frontend/src/App.tsx` defines all seven tabs in one `tabs` array. `activeTab` starts at `evolution`; each navigation item is a `<button>` whose `onClick` calls `setActiveTab(tab.id)`. The active component is selected by ID and wrapped in `ErrorBoundary`.

| Tab id | Visible label | Entry component | Description | Initial state |
|---|---|---|---|---|
| `soc` | SOC Analytics | `components/tabs/SOCAnalyticsTab.tsx` | Governed security metrics with provenance | reachable by tab click |
| `evolution` | Runtime Evolution | `RuntimeEvolutionTab.tsx` | Runtime learning/evolution; marked `KEY` | initial tab |
| `triage` | Alert Triage | `AlertTriageTab.tsx` | Graph-based reasoning and execution | reachable by tab click |
| `compounding` | Compounding | `CompoundingTab.tsx` | Two-loop architecture and simulation | reachable by tab click |
| `executive` | Executive Narrative | `ExecutiveNarrativeTab.tsx` | CISO weekly narrative | reachable by tab click |
| `s2p` | S2P Preview | `S2PPreviewTab.tsx` | Invoice-exception preview | reachable by tab click |
| `governance` | Evidence Room | `GovernanceTab.tsx` | Governance, audit chain, conservation, evolution trail | reachable by tab click |

The shell also has a footer and tab description area. `OutcomeFeedback` can dispatch the custom `vis2:navigate` event to move to a target tab; `App.tsx` listens for this event and updates `activeTab`.

## 3. SOC — SOC Analytics tab

**Source:** `gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/SOCAnalyticsTab.tsx` (1,294 lines).  
**Primary purpose:** detection-engineering analytics, natural-language metric query, graph exploration, campaign intelligence.

### Components mounted

| Component | Source | API calls / data path | Data? | Demo beat |
|---|---|---|---|---|
| `SOCAnalyticsTab` | `components/tabs/SOCAnalyticsTab.tsx` | query, threat landscape, ATT&CK breakdown, benchmarking, F9, graph summary, prebuilt queries, node neighbors | WIRED | SOC-D1/D3/D6; analytics portion of VC/enterprise cuts |
| `CampaignIntelligencePanel` | `components/CampaignIntelligencePanel.tsx` | `/api/soc/campaigns` | WIRED in source | SOC-D6 |
| graph/query result views | inline in tab | `queryMetric`, `fetchGraphSummary`, `fetchPrebuiltQueries`, `runPrebuiltQuery`, `fetchNodeNeighbors` | WIRED | analyst graph exploration |
| guards/domain config | `lib/guards.ts`, `lib/domain.ts` | no route | support code | no direct beat |

### API calls

| Endpoint/function | Called from | Response/use | Status |
|---|---|---|---|
| `POST /api/soc/query` (`queryMetric`) | natural-language query form | metric/query result | LIVE UNKNOWN |
| `GET /api/soc/threat-landscape` | tab load | threat landscape | LIVE UNKNOWN |
| `GET /api/soc/attack-tactic-breakdown` | tab load | tactic breakdown | LIVE UNKNOWN |
| `GET /api/soc/analyst-benchmarking` | analytics load | analyst benchmark | LIVE UNKNOWN |
| `GET /api/soc/f9-report` | analytics load | F9 report | LIVE UNKNOWN |
| `GET /api/soc/graph-summary` | graph view | graph summary | LIVE UNKNOWN |
| `GET /api/soc/prebuilt-queries` | prebuilt query selector | query definitions | LIVE UNKNOWN |
| `POST/GET` prebuilt query route via `runPrebuiltQuery` | prebuilt query action | query rows/pagination | LIVE UNKNOWN |
| node-neighbor route via `fetchNodeNeighbors` | graph node click | neighboring nodes | LIVE UNKNOWN |
| `GET /api/soc/campaigns` | `CampaignIntelligencePanel` | campaign intelligence | LIVE UNKNOWN |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Query input | `onChange` | edits analyst question | source-wired |
| Query submit | `handleQuery` | sends natural-language metric query | source-wired; live unknown |
| Example query buttons | `handleExampleClick` | populate/run example query | source-wired |
| Orange/red action buttons | inline handlers | demo/query actions | source-wired; exact backend action depends on selected flow |
| Graph expand/collapse | `setGraphExpanded` | changes graph view | source-wired |
| Prebuilt query rows | `handleRunPrebuilt` | runs selected prebuilt query | source-wired |
| Pagination controls | `setQueryPage` | moves result page | source-wired |
| Graph node | `handleNodeClick` | loads neighbors | source-wired; live unknown |
| Close selection | inline state reset | clears selected node/neighbors | source-wired |

### Gaps

- The task-required `/api/soc/tab/1/content` abstraction is not the dominant implementation path; this tab uses dedicated analytics routes.
- Endpoint response schemas are consumed through guards and inferred values rather than a single typed response contract.
- The live rerun verified the shared endpoint family; the dedicated analytics routes above were not part of the requested runtime probe set and remain LIVE UNKNOWN.

## 4. SOC — Runtime Evolution tab

**Source:** `RuntimeEvolutionTab.tsx` (3,602 lines). It is the largest SOC surface and starts selected by default.

### Components mounted

| Component | Source | API calls / data path | Data? | Demo beat |
|---|---|---|---|---|
| `RuntimeEvolutionTab` | tab source | alerts, deployment/evolution, centroid, learning, governance routes | WIRED | V2, E1, E3, SOC-D1/D2/D8, SOC-V4 |
| `CampaignTimelinePanel` | `components/CampaignTimelinePanel.tsx` | `/api/soc/campaign-timeline`; callback into Alert Triage | WIRED | SOC-D8 |
| `RejectionMomentPanel` | `components/RejectionMomentPanel.tsx` | `/api/soc/evolution/rejection-summary` | WIRED | V2/E3 rejection moment |
| inline checkpoint/rollback controls | tab source | checkpoint/rollback API helpers | WIRED | governance/evolution control |
| inline what-if/convergence charts | tab source | GAE/convergence and local projection state | PARTIAL where server route is optional | compounding/evolution story |

### API calls

The tab imports the broad `lib/api` namespace. The source explicitly references:

| Endpoint/function | Use | Status |
|---|---|---|
| `GET /api/soc/centroid-evolution?n=200` | centroid trajectory | LIVE UNKNOWN; source includes “not yet built” fallback text |
| `GET /api/soc/centroid-heatmap` | heatmap | LIVE UNKNOWN |
| `GET /api/soc/centroid-support` | support/continuity | LIVE UNKNOWN |
| `GET /api/soc/enrichment-status` | enrichment status | LIVE UNKNOWN |
| `GET /api/soc/graph-stats` | graph statistics | LIVE UNKNOWN |
| `GET /api/soc/learning-state` | learning state | LIVE UNKNOWN |
| `GET /api/alerts/queue` | alert inventory | LIVE UNKNOWN |
| `POST /api/alert/process` and blocked variant | processes selected alert | LIVE UNKNOWN; action is method-sensitive |
| `POST /api/eval/simulate-failure` | red-team/conservation failure | LIVE UNKNOWN |
| intervention history and reward/profile helpers | evolution panels | LIVE UNKNOWN |
| checkpoint create / rollback helpers | checkpoint management | source-wired; live unknown |
| `GET /api/self/evolution/summary` or rejection summary | rejection/promotions | source-wired via rejection panel; live unknown |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Alert selector | `onChange` | chooses alert | source-wired |
| Process/analysis controls | inline handlers | process selected alert | source-wired; live unknown |
| Simulate failure | `handleSimulateFailure` / `simulateFailedGate` | exercises refusal/AMBER path | source-wired; live unknown |
| Category filter | `onChange` | filters evolution data | source-wired |
| Shadow toggle | `handleShadowToggle` | starts/stops shadow flow | source-wired; route method/status unknown |
| Create checkpoint | `handleCreateCheckpoint` | writes checkpoint | source-wired |
| Rollback per checkpoint | `handleRollback(cp.id)` | requests rollback | source-wired; backend method/status unknown |
| What-if expand | `setWhatIfExpanded` | reveals projection controls | source-wired |
| What-if sliders | `onChange` | changes q, horizon, alpha, volume projections | source-wired; local projection |
| Chart reload buttons | `loadGAECharts`, `loadConvergenceData`, `loadAuditData` | reloads data | source-wired |
| Learning-balance expand/load | state/load handlers | displays balance sheet | source-wired |

### Gaps

- Several controls are exposed in a large monolithic component, making per-feature error isolation difficult.
- Source contains an explicit fallback indicating `/api/soc/centroid-evolution` may not be built; this is a visible STUB/DEMO boundary even though the UI is present.
- Exact checkpoint, shadow, promotion, and rollback methods are not visible from the tab alone and need route-level verification.

## 5. SOC — Alert Triage tab

**Source:** `AlertTriageTab.tsx` (1,689 lines).

### Components mounted

| Component | Source | API calls / data path | Data? | Demo beat |
|---|---|---|---|---|
| `AlertTriageTab` | tab source | alert queue, analyze, action, reset, enrichment, factors, explanation | WIRED | E2; triage portion of governed-action demo |
| `DiscoveryBanner` | `components/discovery/DiscoveryBanner.tsx` | discoveries route | WIRED | discovery/supporting surface |
| `OutcomeFeedback` | `components/OutcomeFeedback.tsx` | outcome/report path and custom tab navigation | WIRED | learning loop |
| `PolicyConflict` | `components/PolicyConflict.tsx` | policy conflict result passed from tab | WIRED | safety explanation |
| `LearningStatePanel` | `components/LearningStatePanel.tsx` | learning-state-by-category | WIRED | SOC-D2/D3 |
| `ClusterHistoryPanel` | `components/ClusterHistoryPanel.tsx` | data passed from analysis | WIRED | triage context |
| `FactorContributionPanel` | `components/FactorContributionPanel.tsx` | factor contribution route | WIRED | explanation |
| `ProvenanceBadge` | `components/ProvenanceBadge.tsx` | provenance in response | WIRED | grounded decision |

### API calls

| Endpoint/function | Use | Status |
|---|---|---|
| `GET /api/alerts/queue` | queue load | LIVE UNKNOWN |
| `POST /api/alert/analyze` | analyze selected alert | LIVE UNKNOWN |
| `POST /api/action/execute` | execute selected action | LIVE UNKNOWN; side-effecting route |
| `POST /api/alerts/reset` | reset demo alerts | LIVE UNKNOWN; side-effecting route |
| `GET /api/triage/decision-factors/{alertId}` | factor panel | LIVE UNKNOWN |
| `GET /api/soc/judgment/explain/{alertId}` | cited explanation | LIVE UNKNOWN |
| discoveries, policy conflict, enrichment, and outcome helpers | nested panels | LIVE UNKNOWN |
| `GET /api/soc/campaigns/{campaign_id}` | campaign detail/new tab | LIVE UNKNOWN |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Reset alerts | `handleResetAlerts` | resets queue | source-wired; side effect |
| Severity and sort selectors | `onChange` | filters/order alerts | source-wired |
| Alert row | `handleAlertSelect` | selects and analyzes alert | source-wired |
| Refresh threat intel | `handleRefreshThreatIntel` | refreshes enrichment | source-wired |
| Campaign link | `window.open` | opens campaign JSON/detail | source-wired; route unknown |
| Enrichment/factor/explanation/narrative toggles | state handlers | expand/collapse evidence | source-wired |
| Execute action | `executeActionHandler` | sends action to backend | source-wired; side effect |
| Outcome feedback buttons | `handleOutcome('correct'|'incorrect')` | records verification | source-wired |

### Gaps

- The task’s direct `GET /api/soc/judgment/explain` probe is not equivalent to the actual frontend route, which is parameterized by alert ID and likely method-sensitive.
- The tab has execution controls; a read-only deployment audit must distinguish rendering from safe demo execution.

## 6. SOC — Compounding tab

**Source:** `CompoundingTab.tsx` (2,949 lines).

### Components mounted

| Component | Source | API/data path | Data? | Demo beat |
|---|---|---|---|---|
| `CompoundingTab` | tab source | learning health, intervention, evidence, metrics/economics, simulation, eval | WIRED | V5, E3/E4, SOC-C1..C5, SOC-V4 |
| `ROICalculatorModal` | `components/ROICalculator.tsx` | local calculation | WIRED; local | ROI framing |
| `SimulationPanel` | `components/SimulationPanel.tsx` | simulation start/progress/result/log | WIRED | SOC-C5/V5 |
| `ThreeChannelPanel` | `components/ThreeChannelPanel.tsx` | channel decomposition | WIRED | SOC-C4 |
| `CohortStatusPanel` | `components/CohortStatusPanel.tsx` | cohort status | WIRED | learning proof |
| `ProvenanceBadge` | shared component | returned provenance | WIRED | groundedness |

### API calls

| Endpoint/function | Use | Status |
|---|---|---|
| learning health / conservation | health, alpha, q, V, theta | LIVE UNKNOWN |
| `/api/soc/interventions` and history | interventions | LIVE UNKNOWN |
| `/api/eval/simulate-failure` | red-team gate | LIVE UNKNOWN |
| `/api/soc/evidence-room` and export | audit/evidence | LIVE UNKNOWN |
| `/api/metrics/decision-economics`, `/api/soc/economics` | economic impact | LIVE UNKNOWN |
| `/api/soc/operational-metrics` | operating metrics | LIVE UNKNOWN |
| `/api/soc/board-export` | board export | LIVE UNKNOWN; download/side effect |
| `/api/audit/decisions?format=csv` | decision export | LIVE UNKNOWN; download |
| `/api/eval/templates/{format}.csv`, `/api/eval/upload` | evaluation template/upload | LIVE UNKNOWN; side effect |
| simulation helpers | decision simulation | LIVE UNKNOWN; side effect |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Simulate failure | `handleSimulateFailure` | injects failure | source-wired; side effect |
| ROI open/close | `setShowROI` | opens calculator | source-wired |
| Eval template toggle | `handleTemplateToggle` | shows templates | source-wired |
| Eval file input | `handleEvalFileChange` | chooses file | source-wired |
| Eval upload | `handleEvalUpload` | uploads evaluation data | source-wired; side effect |
| Cross-tab learning link | `vis2:navigate` dispatch | moves to Runtime Evolution | source-wired |
| Learning-balance expand/reload | state/load handlers | displays/reloads balance | source-wired |
| GAE chart/convergence/audit reloads | load handlers | fetches charts | source-wired |
| Export buttons | board/evidence/download handlers | downloads artifacts | source-wired; side effect |
| Simulation controls | `SimulationPanel` handlers | sets decision count/speed and starts/downloads | source-wired; side effect |

### Gaps

- A large amount of data is optional and some source text explicitly labels missing chart data as mock/not-yet-built.
- Several downloads and uploads are clickable but cannot be validated safely in a read-only diagnostic.

## 7. SOC — Executive Narrative tab

**Source:** `ExecutiveNarrativeTab.tsx` (809 lines).

### Components and API calls

| Component | API calls | Data? | Demo beat |
|---|---|---|---|
| `ExecutiveNarrativeTab` | `/api/platform/domain-applicability`, `/api/soc/executive-narrative`, `/api/soc/executive-narrative/pdf` | WIRED in source; live unknown | E6/SOC-E1/E2 |
| inline governance summary | `fetchGovernanceSummary`/governance helpers | WIRED | executive governance |
| narrative article sections | response-derived | WIRED | weekly CISO narrative |

### Clickable items

- Governance expansion toggle (`setGovExpanded`).
- JSON governance download (`handleGovernanceJsonDownload`).
- CSV governance download (`handleGovernanceCsvDownload`).
- Article expand/collapse (`setExpandedArticle`).
- PDF route is a direct/download path and is method/content sensitive.

### Gaps

- Narrative content is response-dependent; no fallback proof was available while backend `8001` was offline.
- The required E6 continuity path references `/api/soc/centroid-support` and `/learning-state`, but this tab’s primary source also depends on executive-narrative routes; the full stitched beat requires both surfaces.

## 8. SOC — S2P Preview tab

**Source:** `S2PPreviewTab.tsx` (719 lines).

### Components mounted

| Component | API/data path | Data? | Demo beat |
|---|---|---|---|
| `S2PPreviewTab` | preview queue/conservation/suppliers and supplier profile | WIRED | SOC-P1 |
| `CompliancePanel` | `/api/s2p/compliance/report` | WIRED | procurement governance |
| `DisruptionSimPanel` | `/api/s2p/simulation/impact-summary`, `/api/s2p/simulation/scenarios` | WIRED | disruption preview |
| `FinancialImpactPanel` | `/api/s2p/financial-impact` | WIRED | financial impact |
| `NoveltyPanel` | `/api/s2p/novelty/status` | WIRED | novelty |
| `ProcessFusionPanel` | cross-graph/process signals | WIRED | E5 fusion preview |
| `TrendCorrelationPanel` | supplier early-warnings/trends | WIRED | supplier intelligence |
| `WorkingCapitalPanel` | payment portfolio/strategy | WIRED | working capital |

### Clickable items and gaps

The tab source has no direct JSX `onClick`/`Button` handlers in the static scan; most interaction is delegated to nested panels or selection state. Supplier selection drives `GET /api/s2p/suppliers/{supplier_id}/profile`. This is a preview surface rather than the canonical S2P shell, so it duplicates some API domains with the SDK S2P app.

## 9. SOC — Evidence Room / Governance tab

**Source:** `GovernanceTab.tsx` (907 lines).

### Components/data

| Component | API calls | Data? | Demo beat |
|---|---|---|---|
| `GovernanceTab` | `/api/soc/evidence-room`, `/api/soc/compliance`, `/api/governance/summary`, `/api/evolution/recent-events?limit=20` | WIRED in source; live unknown | E7/E8, SOC-V1/V4 |
| RL reward demo | `/api/platform/rl-reward-demo` | WIRED but demo-only | governance explanation |
| RL exploration demo | `/api/platform/rl-exploration-demo` | WIRED but demo-only | bounded exploration explanation |
| evidence export | `/api/soc/evidence-room/export` | WIRED; download | E8 |

### Clickable items

- Evidence/export button (`handleExport`).
- The tab includes evidence, compliance, event, and demo panels whose expand/collapse controls are local to the component tree.

### Gaps

- The UI is labeled Evidence Room while App uses ID `governance`; this is clear to users but can complicate automation selectors.
- Demo routes for RL reward/exploration should not be mistaken for action-selection authority; the G1 memo says reward is learning-path only.

## 10. SOC endpoint verification matrix

The requested probe set was rerun after the copilots were restarted. The service was healthy. `GET` probes returning `405` are route-existence evidence for POST-only endpoints; `404` means the exact requested path was not present.

| Endpoint | Static source relationship | HTTP/status | Response keys observed |
|---|---|---|---|
| `/health` | shell/runtime probe | **200** | `status, components` (`status=healthy`) |
| `/api/soc/tab/1/content` | task-probe abstraction; Alert Triage aggregate | **200** | `tab, tab_name, content, generated_at_epoch`; content: `alert_count, top_alert_types, pending_count, verified_decisions` |
| `/api/soc/tab/2/content` | Institutional Intelligence aggregate | **200** | `tab, tab_name, content, generated_at_epoch`; content includes `iks_score, category_accuracy_summary, drift_alert_summary, trust_coverage_summary` |
| `/api/soc/tab/3/content` | Alert Detail aggregate | **200** | `tab, tab_name, content, generated_at_epoch`; content includes `factor_names, factor_breakdown, decision_method, graph_context, recommendation` |
| `/api/soc/tab/4/content` | Decision Economics aggregate | **200** | `tab, tab_name, content, generated_at_epoch`; content includes `roi_annual_usd, decisions_per_day, learning_events_count, roi_methodology` |
| `/api/soc/tab/5/content` | Executive Narrative aggregate | **200** | `tab, tab_name, content, generated_at_epoch`; content includes `headline, sections, what_changed, what_discovered, what_system_knows` |
| `/api/soc/tab/6/content` | no valid aggregate route | **404** | `detail`: valid range is 1–5 |
| `/api/soc/tab/7/content` | no valid aggregate route | **404** | `detail`: valid range is 1–5 |
| `/api/soc/evidence-room` | Governance + Compounding | **200** | `generated_at, audit_trail, conservation, override_analysis, hash_chain` |
| `/api/governance/summary` | Governance | **200** | `title, generated_at, overall_assessment, legal_disclaimer, sections` |
| `/api/evolution/summary` | legacy/summary probe | **200** | `variants_generated, variants_promoted, variants_rejected, variants_rolled_back, shadow_batches, by_artifact_type` |
| `/api/evolution/recent-events?limit=5` | Governance/evolution | **200** | `events, count, limit` |
| `/api/self/diagnostics` | shared diagnostics contract | **200** | `centroid_distance_to_canonical, epsilon_firm, iks, measurement_state, domain` |
| `/api/self/evolution/summary` | shared evolution contract | **200** | `domain, evolution_enabled, schema_version, conservation_state, inventory, variant_stats, recent_events, active_variant` |
| `/api/self/centroid-history?limit=5` | shared checkpoint contract | **200** | `checkpoints, total` |
| `/api/soc/learning-health` | Compounding/evolution | **200** | `status, signal, theta_min, conservation, components, baseline, auto_pause_active, interpretation` |
| `/api/soc/alerts`, `/api/soc/alerts/pending` | probe set; source primarily uses `/api/alerts/queue` | **404** | `detail=Not Found` |
| `/api/soc/triage`, `/api/soc/score` | probe set; frontend uses `/api/alert/analyze` and shared score paths | **404** | `detail=Not Found` |
| `/api/soc/interventions` | Compounding probe | **404** | `detail=Not Found` |
| `/api/eval/simulate-failure` | Compounding/Runtime Evolution | **405** | `detail=Method Not Allowed`; POST route exists |
| `/api/soc/judgment/explain` | task probe; frontend uses parameterized route | **405** | `detail=Method Not Allowed`; method/parameters required |
| `/api/servicenow/create-incident` | demo/E7 route; no direct tab call found in static tab scan | **405** | `detail=Method Not Allowed`; route exists with another method |
| `/api/sentinel/writeback-test` | demo/E7 route; no direct tab call found in static tab scan | **405** | `detail=Method Not Allowed`; route exists with another method |
| `/api/admin/shadow-start` | demo/E1/V2 route; evolution controls use helpers/other paths | **405** | `detail=Method Not Allowed`; route exists with another method |

## 11. S2P — shell and navigation

`copilot-sdk/apps/s2p/frontend/src/App.tsx` defines a typed six-item `tabs` array and renders each screen through `renderScreen`. `CopilotShell` owns the visible navigation; `onTabChange` calls `setActiveTab`.

| Tab id | Visible label | Screen | Primary purpose |
|---|---|---|---|
| `dashboard` | Dashboard | `DashboardScreen.tsx` | queue, conservation, recent decisions, operating context |
| `triage` | Exception Triage | `TriageScreen.tsx` | score, reason, learn, situation, counterfactual |
| `insight` | Insight | `InsightScreen.tsx` | invoice intelligence and cross-graph signals |
| `evidence` | Evidence | `EvidenceScreen.tsx` | audit, compliance, evolution, receipts |
| `suppliers` | Suppliers | `SuppliersScreen.tsx` | supplier memory and history |
| `performance` | Performance | `PerformanceScreen.tsx` | trajectory, what-if, operational/financial metrics |

## 12. S2P — Dashboard screen

**Source:** `apps/s2p/frontend/src/screens/DashboardScreen.tsx`.

### Components mounted

| Component | API calls/data | Data? | Demo beat |
|---|---|---|---|
| `CopilotShell`/`TransferBadge` | shared shell/transfer data | WIRED | cross-copilot continuity |
| `DayZeroCard` | shared day-zero state | WIRED | V6 |
| `Exception Queue` inline card | `getPreviewQueue` → `/api/s2p/preview/queue` | WIRED | S1/S2 |
| `Conservation Status` inline card | `getPreviewConservation` → `/api/s2p/preview/conservation` | WIRED | S2/S15 |
| recent decision rows | queue response | WIRED | triage handoff |
| `ConservationMiniGauge` | conservation prop | WIRED | safety status |
| `NoveltyStatusPanel` | `getNoveltyStatus` → `/api/s2p/novelty/status` | WIRED | S9/S13 |
| `DisruptionSimPanel` | scenarios/impact summary | WIRED | S3 |
| `AutoApprovePanel` | auto-approve stats/expansion proof | WIRED | S2 |
| `ProcessContextCard` | selected first invoice context | WIRED | S16 |
| `ControlTowerPanel` | intents/queue | WIRED | operating control |
| `FinancialImpactCard` | financial impact | WIRED | dollar impact |

### Clickable items

- The shell tab buttons navigate to all six screens.
- Queue/decision rows are rendered as selectable handoff data; direct Dashboard click handlers are minimal.
- Nested `AutoApprovePanel` has category select plus **Load proof** (`loadProof`).
- Nested financial/control-tower panels expose expand/details controls where their components define them.

### Gaps

- Preview endpoints are deliberately fallback-backed in `api.ts`; a successful UI render can show empty/placeholder data without proving backend population.
- The task’s `/api/s2p/preview/config` probe is not used by this screen’s API helpers.

## 13. S2P — Exception Triage screen

**Source:** `TriageScreen.tsx`.

### Components mounted

| Component | API/data | Data? | Demo beat |
|---|---|---|---|
| invoice selector and score card (inline) | `fetchPreviewQueue`, `scoreInvoice` → `/api/s2p/score` | WIRED | S1/S2 |
| `SituationPanel` | `fetchSituation` → `/api/s2p/situation/{decisionId}` | WIRED | S14/E2 |
| `RuleVsReasoningPanel` | import alias to `RuleVsReasoningContrast` | source import exists, target file is a 1-line stub; effective surface is **MISSING/STUB** | S14-CONTRAST |
| `CounterfactualCard` | direct `POST /api/s2p/score/counterfactual` | WIRED | V4 |
| `EvidenceTemplatePanel` | `/api/s2p/evidence/template` | WIRED | cited evidence |
| `NoveltyAlertBanner` | novelty status/triggered decisions | WIRED | S9 |
| `ProvenanceBadge` | score provenance | WIRED | V4/V6 |
| `ProcessContextPanel` | score context object | WIRED | S16 |
| `S2PReasoningPanel` | score factor map | WIRED | S14 |
| `CentroidExplorer` | explanation/drift routes | WIRED | judgment inspection |
| `S2PConservationProjection` | conservation prop | WIRED | safety |
| learning result and override form (inline) | `learnDecision` → `/api/learn` | WIRED | S13/S15 |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Invoice row | selection callback | chooses invoice | source-wired |
| Score/re-score | score handler | scores selected invoice | source-wired; side effect-free scoring intent |
| Situation changes | `onSituationChange` | updates situation state | source-wired |
| Counterfactual expand / sample | `setExpanded`, `trySample` | invokes perturb/sample gate | source-wired; live unknown |
| Evidence template | selected invoice/category effect | loads template | source-wired |
| Override action select | `setOverrideAction` | chooses action | source-wired |
| Override reason select | `setOverrideReason` | chooses reason code | source-wired |
| Submit override/learn | learn handler | records outcome | source-wired; side effect |
| Centroid explorer | decision/category/action controls | loads explanation/drift | source-wired |

### Gaps

- **S14 is not complete at the component-file level:** `RuleVsReasoningContrast.tsx` is currently only a one-line stub, while `TriageScreen` imports it under the name `RuleVsReasoningPanel`. The neighboring `RuleVsReasoningPanel.tsx` is a separate file but is not the imported target shown by the screen import.
- The S14 requested computed false-rejection dollar impact therefore cannot be counted as fully rendered from this source snapshot.

## 14. S2P — Insight screen

**Source:** `InsightScreen.tsx`.

| Component | API helper / endpoint | Data? | Demo beat |
|---|---|---|---|
| invoice selector (inline) | `fetchPreviewQueue` | WIRED | invoice context |
| `FactorFingerprintPanel` | `/api/s2p/insight/fingerprint?invoice_id=...` | WIRED | explanation |
| `SimilarInvoicesPanel` | `/api/s2p/insight/similar` | WIRED | S5/S7 |
| `CrossGraphInsightCard` | `/api/s2p/insight/cross-graph` | WIRED | E5/S16 |
| `ProcessFusionPanel` | process-fusion route | WIRED; uses sample event constants in component source | PARTIAL/STUB risk |
| `EarlyWarningPanel` | `/api/s2p/suppliers/early-warnings` | WIRED | S11 |
| `LeakageDetectionPanel` | `/api/s2p/pvg/leakage` | WIRED | S12 |
| `ProcessSignalsPanel` | `/api/s2p/insight/process-signals` | WIRED | S8/S16 |
| `CentroidExplorerPanel` | centroid all/explain/drift/DK routes | WIRED | judgment memory |
| `DiscoveryExtendedPanel` | `/api/s2p/discovery/extended` | WIRED | S5 |

### Clickable items and gaps

- Invoice selector `<select>` changes the selected invoice and reloads all invoice-dependent panels.
- Nested financial/insight panels expose details or recommendation controls as defined in their components.
- `ProcessFusionPanel` contains a `SAMPLE_EVENTS` constant and posts it through the fusion helper; this is a demo-data boundary that should be labeled when presenting as live enterprise data.

## 15. S2P — Evidence screen

**Source:** `EvidenceScreen.tsx`.

| Component | API helper / endpoint | Data? | Demo beat |
|---|---|---|---|
| invoice selector (inline) | `fetchPreviewQueue` | WIRED | evidence selection |
| `AuditTrailPanel` | `/api/s2p/evidence/audit-trail/{invoice}` | WIRED | E8 |
| `CohortStatusPanel` | `/api/s2p/cohort-status` | WIRED | learning cohorts |
| `FactorInsightPanel` | `/api/s2p/factors/analysis`; proposal route | WIRED | factor improvement |
| `EvolutionPanel` | variants/promotion-check | WIRED | S13 |
| `DiscoveryPanel` | `/api/s2p/discovery/alerts` | WIRED | discoveries |
| `DisruptionRecoveryPanel` | `/api/s2p/discovery/disruptions` | WIRED | S3 |
| `RuleLifecyclePanel` | `/api/s2p/evidence/rules` | WIRED | rule lifecycle |
| `CompliancePanel` | `/api/s2p/evidence/compliance` | WIRED | governance |
| `ReceiptChainPanel` | receipts/chain-integrity | WIRED | audit chain |
| `AuditExportPanel` | audit pack route | WIRED; download action |
| `ComplianceScreeningPanel` | `/api/s2p/governance/compliance-screening` | WIRED | compliance |

### Clickable items and gaps

- Invoice `<select>` chooses the evidence subject.
- Factor insight has proposal buttons; `AuditExportPanel` has an audit-pack button.
- Other panels are predominantly read-only renderers with expand/details controls.
- Evidence routes are numerous and independent; a green screen does not prove chain integrity unless both receipts and integrity routes succeed.

## 16. S2P — Suppliers screen

**Source:** `SuppliersScreen.tsx`; also contains local supplier detail/chart/history subcomponents.

| Component | API helper / endpoint | Data? | Demo beat |
|---|---|---|---|
| `ClusteringPanel` | `/api/s2p/suppliers/clusters` | WIRED | supplier rationalization |
| `PaymentStrategyPanel` | `/api/s2p/suppliers/payment-strategy` | WIRED | S12 |
| `RationalizationPanel` | `/api/s2p/governance/rationalization` | WIRED | supplier portfolio |
| `SupplierHeatmap` | `/api/s2p/suppliers/{id}/heatmap` | WIRED | supplier memory |
| `Supplier list` (inline) | profiles + declining suppliers | WIRED | S11 |
| `SupplierCard` (inline) | selected profile | WIRED | supplier selection |
| `SupplierDetailPanel` (inline) | selected profile | WIRED | profile drill-down |
| `SupplierSeasonalChart` (inline) | profile seasonal fields | WIRED; local chart |
| `SupplierHistoryPanel` (inline) | `/api/s2p/suppliers/{id}/history` | WIRED | verified history |

### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Retry supplier profiles | `loadSuppliers` | retries profile/declining loads | source-wired |
| Supplier card | selection callback | changes selected supplier | source-wired |
| Supplier history/heatmap | selected supplier effect | loads detail data | source-wired |
| Chart mode/details controls | local state where present | changes supplier visualization | source-wired |

### Gaps

- `api.ts` returns fallback empty supplier structures for some failures, so “no supplier data” is not equivalent to a confirmed empty backend.
- Supplier list may include fixture-backed source labels; the UI exposes the source but the report should not treat fixture data as production evidence.

## 17. S2P — Performance screen

**Source:** `PerformanceScreen.tsx`.

| Component | API helper / endpoint | Data? | Demo beat |
|---|---|---|---|
| `TrajectoryChart` | `/api/s2p/performance/trajectory` | WIRED | compounding curve |
| `ConservationMiniGauge` | `fetchConservation` → `/api/conservation/status` with preview fallback | WIRED/fallback | safety |
| `WhatIfSimulator` | `/api/s2p/performance/what-if` | WIRED | counterfactual/projection |
| `OperationalSummary` | `/api/s2p/performance/summary` | WIRED | operating results |
| `FinancialImpactTrendPanel` | `/api/s2p/financial-impact/trend` | WIRED | dollar value |
| `CycleTimePanel` | `/api/s2p/pvg/cycle-time` | WIRED | process performance |

### Clickable items and gaps

- What-if numeric inputs (`additionalCorrect`, `additionalIncorrect`) are controlled by `onChange` and cause a what-if reload.
- Financial impact cards expose expansion/detail controls.
- The performance page is read-side; it does not itself record outcomes.

## 18. S2P component inventory not otherwise mounted directly

The following files exist under `apps/s2p/frontend/src/components` and were inspected. They are either mounted by one of the six screens, imported transitively, or are reusable/presentational support. The API helper used by each is listed where applicable.

| Component file | Role / API or interaction | Classification |
|---|---|---|
| `AuditExportPanel` | audit pack; button | WIRED |
| `AuditTrailPanel` | invoice audit trail | WIRED |
| `AutoApprovePanel` | stats/proof; category select/load | WIRED |
| `CentroidExplorer` / `CentroidExplorerPanel` | centroid explanation/drift | WIRED |
| `ClusteringPanel` / `SupplierClusteringPanel` | supplier clusters/clustering | WIRED |
| `CohortStatusPanel` | cohort status | WIRED |
| `CompliancePanel` / `ComplianceScreeningPanel` | compliance/report/screening | WIRED |
| `ConservationMiniGauge` / `S2PConservationProjection` | presentational conservation | WIRED |
| `ControlTowerPanel` | intents/classification/queue | WIRED |
| `CounterfactualCard` | `/api/s2p/score/counterfactual`; sample button | WIRED |
| `CrossGraphInsightCard` | cross-graph insight | WIRED |
| `CycleTimePanel` | cycle-time metrics | WIRED |
| `DiscoveryPanel` / `DiscoveryExtendedPanel` | discovery alerts/extended data | WIRED |
| `DisruptionRecoveryPanel` / `DisruptionSimPanel` | disruption data/scenarios | WIRED |
| `EarlyWarningPanel` | supplier early warnings | WIRED |
| `EvidenceTemplatePanel` | evidence template by invoice/category | WIRED |
| `EvolutionPanel` / `S2PEvolutionPanel` | variants, promotion, shadow, promoted rules | WIRED |
| `FactorFingerprintPanel` / `FactorInsightPanel` / `FactorRadar` | factor analysis/fingerprint/proposal | WIRED |
| `FinancialImpactCard` / `FinancialImpactTrendPanel` | impact/trend; expandable | WIRED |
| `LeakageDetectionPanel` | PVG leakage | WIRED |
| `NoveltyAlertBanner` / `NoveltyStatusPanel` | novelty status/triggered decisions; expand | WIRED |
| `OperationalSummary` | performance summary | WIRED |
| `PaymentStrategyPanel` | payment strategy | WIRED |
| `ProcessContextCard` / `ProcessContextPanel` | contextual display | WIRED/presentational |
| `ProcessFusionPanel` | process fusion; sample event payload | PARTIAL/STUB risk |
| `ProcessSignalsPanel` | process signals | WIRED |
| `ProvenanceBadge` | provenance display | WIRED/presentational |
| `RationalizationPanel` | supplier recommendations | WIRED |
| `ReceiptChainPanel` | receipts + chain integrity | WIRED |
| `RuleLifecyclePanel` | rule lifecycle | WIRED |
| `RuleVsReasoningContrast.tsx` | intended S14 contrast; file is one-line stub | **MISSING/STUB** |
| `RuleVsReasoningPanel.tsx` | separate rule/reasoning implementation exists but is not the imported target in `TriageScreen` | ORPHAN/PARTIAL |
| `S2PReasoningPanel` | factor reasoning display | WIRED |
| `SimilarInvoicesPanel` | similar invoices | WIRED |
| `SituationPanel` | situation endpoint | WIRED |
| `SupplierHeatmap` / `SupplierProfileCard` | supplier heatmap/profile | WIRED |
| `TrajectoryChart` | trajectory | WIRED |
| `WhatIfSimulator` | what-if input controls | WIRED |

## 19. S2P API helper inventory

`apps/s2p/frontend/src/api.ts` centralizes `apiGet`, `apiPost`, and nullable/fallback wrappers. The full declared route families are:

| Family | Declared paths |
|---|---|
| Preview/score | `/api/s2p/preview/queue`, `/preview/conservation`, `/preview/suppliers`, `/api/s2p/score`, `/api/s2p/outcome`, `/api/learn` |
| Evidence/insight | `/api/s2p/evidence/template`, `/insight/fingerprint`, `/insight/similar`, `/insight/cross-graph`, `/insight/process-signals`, `/evidence/audit-trail`, `/evidence/rules`, `/evidence/compliance`, `/evidence/receipts`, `/evidence/chain-integrity`, `/evidence/audit-pack` |
| Situation/centroid | `/api/s2p/situation/{decisionId}`, `/centroid/all`, `/centroid/{category}/{action}`, `/centroid/explain/{decisionId}`, `/centroid/drift/{category}/{action}`, `/explorer/dk-weights` |
| Evolution | `/evolution/rules`, `/evolution/variants`, `/evolution/promotion-check`, `/evolution/reset`, `/evolution/shadow-results`, `/evolution/promoted` |
| Discovery/novelty | `/discovery/alerts`, `/discovery/disruptions`, `/discovery/extended`, `/novelty/status`, `/novelty/history`, `/novelty/triggered-decisions` |
| Performance | `/performance/trajectory`, `/performance/what-if`, `/performance/summary` |
| Factors/governance | `/factors/analysis`, `/factors/recommendations`, `/factors/propose`, `/governance/compliance-screening`, `/governance/rationalization` |
| Simulation/control tower | `/simulation/scenarios`, `/simulation/impact-summary`, `/control-tower/intents`, `/control-tower/classify`, `/control-tower/queue` |
| Auto-approve/PVG/finance | `/auto-approve/stats`, `/auto-approve/expansion-proof`, `/pvg/variants`, `/pvg/impact`, `/pvg/leakage`, `/pvg/cycle-time`, `/financial-impact`, `/financial-impact/trend`, `/financial-impact/{category}` |
| Suppliers | `/suppliers`, `/suppliers/declining`, `/suppliers/{id}/profile`, `/suppliers/{id}/history`, `/suppliers/{id}/heatmap`, `/suppliers/similarity`, `/suppliers/clustering`, `/suppliers/clusters`, `/suppliers/payment-strategy`, `/suppliers/payment-behavior`, `/suppliers/early-warnings`, `/suppliers/trend-signals` |

## 20. S2P endpoint verification matrix

The requested probe set was rerun after restart. The service was healthy and returned the following statuses and response keys.

| Endpoint | Static source relationship | HTTP/status | Response keys observed |
|---|---|---|---|
| `/health` | runtime probe | **200** | `status, service, version`; `status=ok`, service `s2p-copilot` |
| `/api/s2p/preview/queue` | Dashboard/Triage | **200** | `engine_version, total, showing, exceptions, invoices, auto_approve_rate, confidence_avg, scorer` |
| `/api/s2p/preview/conservation` | Dashboard fallback/conservation | **200** | `engine_version, source, status, auto_approve_rate, accuracy, verified_decisions, penalty_ratio, passed, curve, computed_status` |
| `/api/s2p/preview/suppliers` | preview surface | **200** | `engine_version, total, showing, suppliers, source` |
| `/api/s2p/preview/config` | probe only; no API helper found | **200** | `engine_version, domain, tensor_shape, categories, actions, factors, canonical_factors, penalty_ratio, platform_comparison, cross_copilot_signals` |
| `/api/s2p/score` | Triage score helper | **405** | `detail=Method Not Allowed`; POST route exists |
| `/api/s2p/insight/fingerprint?invoice_id=...` | FactorFingerprintPanel | **200** | `invoice_id, category, factors, dominant_factor, narrative` |
| `/api/s2p/evidence/compliance` | CompliancePanel | **200** | `total, compliant, compliant_pct, flagged_count, flagged_invoices, factor` |
| `/api/s2p/performance/summary` | OperationalSummary | **200** | `total_scored, total_verified, accuracy, auto_approve_rate, savings_estimate_usd, annual_target_usd, penalty_ratio` |
| `/api/self/diagnostics` | shared shell/diagnostic contract | **200** | `centroid_distance_to_canonical, epsilon_firm, iks, measurement_state, domain` |
| `/api/self/evolution/summary` | shared evolution contract | **200** | `domain, evolution_enabled, schema_version, conservation_state, inventory, variant_stats, recent_events, active_variant` |
| `/api/conservation/status` | Performance/Conservation fallback | **200** | `engine, domain, verified_count, correct_count, total_decisions, penalty_ratio, alpha, q, V, baseline, reason, signal, theta_min, status, passed` |
| `/api/self/centroid-history?limit=5` | shared checkpoint contract | **200** | `checkpoints, total` |
| `/api/self/trust-traps` | probe only; no direct S2P API helper found | **200** | `traps, total` |

## 21. Runtime observations from the healthy restart

### SOC

- `/health` returned `200` with `status=healthy`; the posterior store was healthy and the entity-cache adapter was enabled but empty.
- The aggregate SOC content service exposes **five** valid tab payloads, not seven. They are named `Alert Triage`, `Institutional Intelligence`, `Alert Detail`, `Decision Economics`, and `Executive Narrative`. `/api/soc/tab/6/content` and `/api/soc/tab/7/content` returned `404` with a valid-range message.
- The seven frontend tabs therefore do not map directly to seven `/api/soc/tab/N/content` responses. Runtime Evolution, Compounding, S2P Preview, and Evidence Room use their own endpoint families or aggregated routes.
- Shared diagnostics, evolution summary, checkpoint history, evidence room, governance summary, evolution events, and learning health all returned `200`.
- The requested SOC alert/triage/score/interventions aliases returned `404`; the frontend’s `/api/alerts/queue` and parameterized/action routes remain the relevant source paths.
- `simulate-failure`, judgment explanation, ServiceNow, Sentinel, and shadow-start returned `405` to GET, confirming method-sensitive routes rather than absent routes.

### S2P

- `/health` returned `200` with `status=ok`, service `s2p-copilot`, version `0.1.0`.
- Preview queue, conservation, suppliers, and config all returned `200` with populated schemas. The queue reported `total=50`, `showing=5`; the config reported tensor shape `(5, 5, 8)` and eight factors.
- The live S2P diagnostics payload reported `measurement_state.state=accumulating`, `decisions_verified=191`, `decisions_needed=30`, `arms_measured=2`, `arms_total=25`, and provenance `accumulating`.
- Conservation returned `status=RED`, `verified_count=191`, `correct_count=178`, `alpha=0.0`, and a reason stating that no verified decisions were available for conservation evidence. This is a real payload and should be shown as a guarded state, not treated as an endpoint failure.
- Trust traps returned one `VOLUME_SKEW` warning with category-count evidence.
- `/api/s2p/score` returned `405` to GET, confirming the expected POST-only score route.

## 22. Demo-beat cross-reference

### SOC / shared flagship beats

| Beat | Intended surface/API | Source finding | Coverage |
|---|---|---|---|
| V1 cold mirror | Trading Analysis in scenario doc; SOC analog is analytics/graph surface | SOC has query/graph analytics, but V1’s Trading surface is outside this report | PARTIAL for SOC |
| V2 rejection moment | Runtime Evolution; rejection summary | `RejectionMomentPanel` mounted | WIRED; live unknown |
| V3 cross-domain compounding | Purchasing/DataOps genealogy | not a primary SOC tab path | OUT OF SCOPE/PARTIAL |
| V4 counterfactual | scoring surface and F-26 gate | SOC has simulation/what-if controls; S2P has explicit counterfactual but is separate app | PARTIAL |
| V5 red-team refusal | Compounding + `/api/eval/simulate-failure` | button/helper path mounted | WIRED source; live unknown |
| V6 day-zero | shared card/state | S2P has `DayZeroCard`; SOC source has learning/health surfaces but no matching `DayZeroCard` in tab imports | PARTIAL |
| V7 close | presenter close | no API/component requirement | narrative only |
| E1 authored rule/shadow | Runtime Evolution | shadow/checkpoint controls | WIRED source; route verification pending |
| E2 cited situation explanation | Alert Triage | parameterized judgment explain + triage panels | WIRED source; probe path differs |
| E3 refusal/rejection | Compounding + Runtime Evolution | interventions and rejection panel | WIRED source |
| E4 red-team | Compounding | simulate-failure control | WIRED source |
| E5 process fusion | SOC S2P Preview / DataOps | S2P preview process-fusion panel | WIRED source; live unknown |
| E6 continuity | Executive Narrative / centroid support | executive narrative plus runtime support helpers | PARTIAL; endpoint unverified |
| E7 ServiceNow/Sentinel | Evidence Room | routes are in demo contract but no direct source call identified in the SOC tab inventory | PARTIAL/MISSING direct click path |
| E8 hash-chain evidence | Evidence Room | evidence-room and export controls | WIRED source; live unknown |
| SOC-D1..D8 | Analytics, Evolution, Compounding, Executive, Preview | corresponding tab/components exist; D8 Campaign Timeline is explicitly mounted | WIRED source, live unknown |
| SOC-V1..V4 | Evidence, compounding, governance | evidence and safety surfaces exist | WIRED source, live unknown |

### S2P beats S1–S16 / S14 contrast

| Beat | Expected surface | Source finding | Coverage |
|---|---|---|---|
| S1 Exception Rate Drops | Dashboard / queue | queue, metrics, recent decision rows | WIRED source |
| S2 Autopilot Nobody Trusts | Dashboard / AutoApprove | stats/proof panel with category control | WIRED source |
| S3 Same Tariff, Same Recovery | Dashboard/Insight disruption | disruption simulation and recovery panels | WIRED source |
| S4 Cleanup Never Ends | Triage/Evidence | queue, learning, evidence surfaces | PARTIAL scenario composition |
| S5 Pattern Nobody Queried | Insight | similar/discovery/centroid panels | WIRED source |
| S6 Expertise Walks Out | Performance/Suppliers | trajectory, supplier history | WIRED source |
| S7 47 Duplicates | Insight | similar invoices | WIRED source |
| S8 ERP Lead Time Wrong | Insight | process signals/fusion | WIRED source; fusion sample-data caveat |
| S9 Automation Broke Silently | Dashboard/Evidence | novelty status and alert banner | WIRED source |
| S10 Consultant Findings Evaporate | Evidence | discovery/rule/audit panels | WIRED source |
| S11 Supplier Fine Until It Wasn’t | Insight/Suppliers | early warning + supplier profiles/history | WIRED source |
| S12 Working Capital Trap | Suppliers/Dashboard | payment strategy and financial panels | WIRED source |
| S13 System Tunes Itself | Evidence/Triage | evolution and learn path | WIRED source |
| S14 Not a Script — A Decision | Exception Triage | SituationPanel is mounted; imported `RuleVsReasoningContrast.tsx` is a one-line stub | **PARTIAL / critical gap** |
| S15 Caution Over Speed | Triage/conservation | conservation projection and override reasons | WIRED source |
| S16 Where Celonis Stops | Insight | cross-graph/process-fusion panels | WIRED source; sample event caveat |

## 23. Gaps and diagnostic conclusions

1. **SOC aggregate tab count differs from the frontend tab count.** The frontend has seven tabs, while the live `/api/soc/tab/N/content` service accepts only N=1..5. N=6 and N=7 are confirmed 404s. The two structures must not be described as a one-to-one seven-tab API.
2. **SOC tab endpoints and source tabs are not one-to-one.** The actual tab components use dedicated API helpers and nested routes. The tab endpoint family is a separate compatibility/aggregation contract.
3. **SOC route naming has legacy aliases.** The task probe names `/api/soc/judgment/explain`; frontend source calls `/api/soc/judgment/explain/{alertId}`. Similar differences exist between `/api/soc/alerts` probes and `/api/alerts/queue` source usage.
4. **SOC Runtime Evolution has explicit not-built/mock fallback text** for at least centroid-evolution charting, despite the surrounding UI being present.
5. **S2P S14 is not fully mounted.** `TriageScreen.tsx` imports `RuleVsReasoningContrast` as `RuleVsReasoningPanel`, but `RuleVsReasoningContrast.tsx` is a one-line stub. A separate `RuleVsReasoningPanel.tsx` exists but is not the imported target in this screen.
6. **Fallback API helpers mask availability.** Several S2P helpers catch errors and return `null` or empty structures. Empty UI states must not be interpreted as confirmed backend empty data.
7. **Fixture/sample boundaries exist.** `ProcessFusionPanel` uses sample event constants; supplier views expose fixture-backed source labels. These are useful demo scaffolds but should be labeled when used as production proof.
8. **Side-effecting controls are present.** Alert action execution, reset, simulation, shadow start, checkpoint/rollback, uploads, downloads, proposals, and learning/outcome recording require separate safe-flow testing; this report did not invoke them.
9. **S2P has a broad typed API layer and the core runtime contract is live.** Preview, diagnostics, conservation, checkpoint history, and trust-trap routes are verified. Many secondary helper routes remain unprobed in this pass.

## 23. Summary

| Metric | SOC | S2P |
|---|---|---|
| Tabs/Screens | 7: SOC Analytics, Runtime Evolution, Alert Triage, Compounding, Executive Narrative, S2P Preview, Evidence Room | 6: Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance |
| Components | 7 tab entry components plus nested analytics/evolution/triage/preview/evidence components; 20 `.tsx` files under SOC `components/` | 51 `.tsx` component files plus 6 screen entry files |
| API calls | Dedicated `lib/api.ts` methods across analytics, evolution, triage, compounding, narrative, preview, governance | Centralized `api.ts` with preview, scoring, learning, situation, evidence, evolution, discovery, performance, finance, PVG, suppliers |
| WIRED | Most primary tabs and major demo surfaces; rejection panel and campaign timeline explicitly mounted | Most screens and panels; score/learn/counterfactual/situation/evidence/supplier/performance paths mounted |
| STUB | Centroid-evolution fallback/mock text; some demo-only RL/preview paths | Process-fusion sample event payload; fallback/fixture-backed data; S14 contrast target is stub |
| MISSING | Direct source path for some task-probe aliases and direct ServiceNow/Sentinel click path not found | Effective S14 rule-vs-reasoning contrast is missing because imported target is one-line stub |
| Demo beats covered | D1–D8, V2/V5, E1–E5/E8 have source surfaces; E6/E7 and V1/V4/V6 are partial from this SOC-only inspection | S1–S13, S15–S16 broadly surfaced; S14 is partial/critical gap; V4 counterfactual is wired |
| Live status | Healthy; requested aggregate routes 1–5 return 200, 6–7 return 404, method-sensitive routes return 405 | Healthy; core preview/diagnostic/conservation/history/trust-trap routes return 200; score GET returns 405 as expected |

**Final finding:** the two frontends have broad, traceable surface wiring, and the restarted services now confirm the principal SOC/S2P contracts are reachable. The highest-confidence product gap remains the S2P S14 import-to-stub mismatch. The most important integration finding is that the frontend has seven SOC tabs while the aggregate `/api/soc/tab/N/content` API intentionally exposes only five valid tab numbers; the remaining surfaces are independently wired.
