# Tab & Component Inventory — All 5 Copilots

**Generated:** 2026-09-17  
**Source:** repository source inspection, live local API shape probes, and E2E file inventory  
**Copilots:** SOC (8001 / 5173), Trading (8010 / 5174), Purchasing (8020 / 5175), DataOps (8030 / 5176), S2P (8002 / 5177)  
**Scope:** navigation screens, major panels, interactive controls, data bindings, badges, API paths, and E2E coverage.

> All five health endpoints returned HTTP 200 during inventory. Response shapes below are field-name inventories, not captured business data. Source-discovered routes are labeled where they were not included in the compact live probe.

## Summary

| Copilot | Tabs/screens | Major component files | API surface observed | E2E specs |
|---|---:|---:|---:|---:|
| SOC | 7 | 33 components + 7 tabs | 40+ | 64 |
| Trading | 6 | 70 components + 6 screens | 10+ | 55 |
| Purchasing | 5 | 57 components + 5 screens | 20+ | 41 |
| DataOps | 5 | 70 components + 5 screens | 15+ | 30 |
| S2P | 6 | 57 components + 6 screens | 15+ | 36 |
| **Total** | **29** | **250+** | **100+** | **226** |

## Verification and conventions

- Navigation is driven by `CopilotShell` in the SDK apps and a tab registry in the SOC app.
- Component names below are JSX imports or directly rendered JSX identifiers from the corresponding source file.
- `API_BASE`, `BASE`, `SOC_API`, `S2P_API`, and `VITE_API_URL` are environment/runtime base URLs; paths are listed without host prefixes.
- A control is marked clickable when source contains a button, link, `onClick`, `onSubmit`, `onChange`, tab callback, or an explicit download/writeback action.
- Badges include provenance, evidence tier, transfer, autonomy, conservation, and domain-specific trust indicators.
- E2E counts are file counts under the copilot directories, not pass counts.

## SDK shared components

| Component | Role | Main props/data | Interactive/API behavior | Used by |
|---|---|---|---|---|
| `CopilotShell` | Shared shell, tab rail, header, IKS display | `tabs`, `activeTab`, `onTabChange`, `iks` | Tab buttons call `onTabChange` | Trading, Purchasing, DataOps, S2P |
| `ScoreResultCard` | Shared score/action result | score response, decision id, centroid delta | Confirm action; expand/show centroid delta | Trading, Purchasing, DataOps, S2P |
| `ReasoningPanel` | Shared factor/reasoning explanation | reasoning, factors, similar evidence | Expand/collapse reasoning sections where exposed by the consuming screen | Trading, Purchasing, DataOps, S2P |
| `AccuracyAlertsPanel` | Accuracy and alert summary | accuracy series, alert state | usually presentation | multiple apps |
| `AuditTrailPanel` | Audit/event history | audit rows, verification state | row expansion/download in consumers | SOC, S2P |
| `CentroidTimelinePanel` | Learned centroid history | checkpoints, centroid values | timeline selection in consumers | DataOps/SOC |
| `ConservationProjection` | Conservation trajectory | baseline, threshold, projected state | presentation; consumers may expose controls | all SDK shells |
| `ConservationSlider` | Safety/threshold control | threshold value, callback | slider input | DataOps and shared demos |
| `DecisionExplorerPanel` | Decision-level inspection | decision list, selected decision | select/expand decision | Trading/Purchasing/DataOps |
| `DecisionHistory` | Historical decisions | decision rows and outcomes | row selection | Trading/Purchasing |
| `EvolutionPanel` | Rule/centroid evolution | variants, checkpoints | expand/select evolution records | all domains |
| `FactorContributionChart` | Factor contribution chart | factors, contributions | hover/chart interaction | shared analytical panels |
| `FingerprintPanel` | Domain fingerprint | factors, fingerprint values | presentation | Trading/Purchasing/DataOps |
| `GovernedVsUngovernedPanel` | Governance comparison | governed/ungoverned metrics | presentation | Trading |
| `IKSBadge` | IKS score badge | IKS value/status | presentation | shell/header |
| `DayZeroCard` | Day-zero readiness | readiness, coverage | presentation | Purchasing/S2P |
| `DayZeroPanel` | Readiness panel | readiness checks | expand/checklist | Trading/DataOps/SOC |
| `AuditTrailViewer` | Detailed audit viewer | trails, filters | filter/download in consumers | Trading/Purchasing/S2P |
| `DataTrustBadge` | Data-trust indicator | source/tier | presentation | Trading/Purchasing/DataOps |
| `ProvenanceBadge` | Provenance/tier badge | provenance label | presentation | SOC/Purchasing/S2P/DataOps |
| `TransferBadge` | Transfer-learning indicator | transfer status | presentation | all domain apps |
| `EvidenceTierBadge` | Evidence tier label | tier and source | presentation | Trading |
| `PaperBadge` | Paper/demo claim marker | claim text | presentation | Trading |
| `AEManagedBadge` | Autonomous-enrichment marker | managed state | presentation | Purchasing |
| `SAPDataBadge` | SAP/source-system marker | source | presentation | DataOps/SOC |

### Shared shell data contract

- `tabs[]`: tab id and display label.
- `activeTab`: current navigation state.
- `onTabChange(tabId)`: navigation callback.
- `iks`: current information/learning score shown in the shell.
- Shared shells do not own domain API requests; screens and panels own data loading.
- App-level callbacks open detail screens or move the user from a summary surface to a triage/order/detail surface.

## SOC copilot — port 8001 / frontend 5173

SOC has seven registered tabs. The default application tab is `evolution` (`Runtime Evolution`); the tab rail also exposes `SOC Analytics`, `Alert Triage`, `Compounding`, `Executive Narrative`, `S2P Preview`, and `Evidence Room`. This default is set by `useState<TabId>('evolution')` in `frontend/src/App.tsx`.

### Tab 1 — SOC Analytics (`SOCAnalyticsTab.tsx`)

**Purpose:** analytics, detection-engineering, campaign intelligence, and search-oriented SOC overview.

**Components and panels:**

- `CampaignIntelligencePanel` — campaign-level analytics and campaign metadata.
- `DayZeroReadinessPanel` — readiness/coverage state.
- `DetectionEngineering` — detection-engineering summary.
- Recharts primitives (`Bar`, `Line`, `Area`, axes, tooltip, responsive container) — metric charts.
- `BenchmarkingData`, `CategoryScore`, `NoiseMapEntry`, `F9ReportData`, `QueryResult` — response/domain types rendered by panels.
- `AlertTriangle`, `CheckCircle`, `Clock`, `Database`, `Search`, `Settings` — status and search affordances.

**API endpoints:**

- `GET /api/soc/detection-engineering` — detection-engineering payload; live field shape should be captured as the returned object keys.
- Search/query calls are represented by local query state and example-query buttons; inspect the adjacent helper/API module for deployment-specific route selection.

**Clickable elements:**

- Example query buttons call `handleExampleClick(example)`.
- Query submission calls `handleQuery()`.
- Search/filter controls change query/category state.
- Expand/collapse controls use chevrons for analytical sections.

**Data bindings and badges:**

- `CategoryScore` values feed category bars.
- `BenchmarkingData` and `NoiseMapEntry` feed chart series and tables.
- Detection-engineering response fields populate status cards and chart labels.
- Shared `ProvenanceBadge`/source labels identify data provenance where supplied by the response.

**E2E coverage:** analytics, search/query, campaign, benchmarking, and dashboard-oriented SOC specs under the SOC E2E directory.

### Tab 2 — Runtime Evolution (`RuntimeEvolutionTab.tsx`)

**Purpose:** inspect runtime learning, centroids, enrichment, graph state, shadow mode, checkpoints, and what-if projections.

**Components and panels:**

- `AccuracyTrajectoryPanel`, `LearningControlRoom`, `CampaignTimelinePanel` — learning and trajectory views.
- `GraphStats`, `CentroidEvolutionEntry`, `Deployment`, `EvalCheck` — evolution data renderers.
- `AreaChart`, `BarChart2`, `ComposedChart`, `Legend`, `CartesianGrid` — trajectory and state plots.
- `CheckCircle`, `AlertTriangle`, `Clock`, `Eye`, `Lightbulb`, `Database` — state markers and explanatory affordances.

**API endpoints:**

- `GET /api/soc/centroid-evolution?n=200` — array of centroid evolution entries.
- `GET /api/soc/centroid-heatmap` — heatmap payload.
- `GET /api/soc/centroid-support` — support/coverage payload.
- `GET /api/soc/enrichment-status` — enrichment status.
- `GET /api/soc/graph-stats` — graph statistics.
- `GET /api/soc/learning-state` — live keys: `frozen`, `decision_count`, `verified_decisions`, `last_verified_at`, `checkpoint_id`, `iks_v2`, `iks_components`, `iks_interpretation`, `total_decisions`, `categories_active`, `bootstrap_category_weights`.
- API helper methods include accuracy trajectory, learning health, IKS trend, shadow report, checkpoints, what-if presets, factor analysis, deployments, reward summary, profile state, centroid export, model-swap trial, and shadow promotion operations.

**Clickable elements:**

- Learning/evolution section toggles.
- Checkpoint create, list, rollback, and time-machine compare controls.
- Shadow-mode toggle, shadow report refresh, eligibility check, preview promotion, and promote action.
- What-if projection/run controls.
- Alert processing control, including blocked/default alert processing.

**Data bindings and badges:**

- Accuracy points bind to `AccuracyTrajectoryPanel`.
- Centroid entries bind to evolution charts and timeline labels.
- `learning-state` fields bind to learning state cards and IKS components.
- Graph stats bind to graph summary panels.
- Deployment and evaluation fields bind to deployment/checkpoint status.

### Tab 3 — Alert Triage (`AlertTriageTab.tsx`)

**Purpose:** select an alert, inspect enrichment and evidence, score/triage it, and submit outcome feedback.

**Components and panels:**

- `InvestigationPanel` — investigation trajectory and acquired evidence.
- `FactorContributionPanel` — factor-level explanation.
- `LearningStatePanel` — learning state after a decision.
- `OutcomeFeedback` — verified outcome/feedback control.
- `ClusterHistoryPanel`, `NoPrecedentSidebar`, `DiscoveryBanner` — context and no-precedent states.
- `DecisionFactors`, `AlertEnrichmentData`, `AnalysisResult`, `ClosedLoopResult`, `JudgmentExplain` — data structures rendered in cards.

**API endpoints:**

- `POST /api/alert/analyze` — primary decision pipeline; request contains alert id/factors and response contains action, confidence, factors, enrichment, investigation trajectory, and conservation status.
- `GET/POST /api/soc/campaigns` — campaign/alert context.
- `GET /api/soc/campaigns/{id}` — campaign detail opened by the campaign link.
- Additional scoring/enrichment calls are defined in the screen’s API helper and backend route modules; preserve method/body from those helpers when writing E2E fixtures.

**Clickable elements:**

- Reset alerts (`handleResetAlerts`).
- Alert row selection (`handleAlertSelect(alert)`).
- Threat-intelligence refresh (`handleRefreshThreatIntel`).
- Alert/campaign detail links open `/api/soc/campaigns/{campaign_id}` in a new tab.
- Evidence/factor panels expand and collapse.
- Outcome feedback submits the verified result.

**Data bindings and badges:**

- Alert id, category, severity, description, factors, and enrichment fields.
- Investigation reads, evidence status, trajectory, action, and confidence.
- Learning state, recurrence/cluster history, and no-precedent state.
- Provenance and source-tier badges appear with evidence panels.

### Tab 4 — Compounding (`CompoundingTab.tsx`)

**Purpose:** decision economics, compounding curves, evidence room, autonomy, and exportable proof.

**Components and panels:**

- `CohortStatusPanel`, `CoverageAtSafetyBarPanel`, `AutonomyLadderPanel` — coverage and safety.
- `DecisionEconomics`, `BusinessImpact`, `CompoundingData`, `ConvergenceData` — headline data.
- Recharts `Area`, `Bar`, `ComposedChart` and chart primitives — curves and economics.
- `AutoApproveStats`, `AuditDecision`, `AuditVerification`, `CentroidEvolutionEntry` — verification and learning details.

**API endpoints:**

- `GET /api/metrics/compounding/headline` — live keys depend on headline response; used for compounding cards.
- `GET /api/metrics/decision-economics` — economics payload.
- `GET /api/soc/evidence-room` — live keys: `generated_at`, `audit_trail`, `conservation`, `override_analysis`, `hash_chain`.
- `GET /api/soc/evidence-room/export` — export response/file.
- `GET /api/soc/operational-metrics` — live keys: `mttd`, `mttr`, `fp_rate`, `source`.
- `GET /api/soc/centroid-evolution` — evolution entries.
- `GET /api/soc/economics` — economics detail.
- `GET /api/soc/board-export` — board export.
- `GET /api/audit/decisions?format=csv` — CSV audit export.
- `GET /api/eval/templates/{format}.csv` — evaluation template download.

**Clickable elements:**

- ROI modal open/close.
- Failure simulation trigger.
- Evidence-room export/download.
- Board/audit/template export links.
- Chart range/filter and cohort controls.

**Badges:** provenance, verification, conservation, autonomy, and evidence-tier labels.

### Tab 5 — Executive Narrative (`ExecutiveNarrativeTab.tsx`)

**Purpose:** executive narrative, governance summary, domain applicability, evidence value, and report downloads.

**Components:** `ContinuityPanel`, `DomainApplicabilityPanel`, `DomainApplicabilityTable`, `MetricCard`, `NarrativeSection`, `NarrativeSectionCards`, `EvidenceValue`, `NarrativeRecommendationItem`.

**API endpoints:**

- `GET /api/soc/executive-narrative` — narrative payload.
- `GET /api/platform/domain-applicability` — live applicability payload.
- `GET /api/soc/executive-narrative/pdf` — PDF report download.

**Clickable elements:** governance section expand/collapse; JSON download; CSV download; PDF download; search/filter controls.

**Data bindings:** narrative categories, recommendation items, section text, metric values, applicability rows, continuity/evidence value.

### Tab 6 — S2P Preview (`S2PPreviewTab.tsx`)

**Purpose:** embedded S2P preview showing queue, conservation, suppliers, financial impact, novelty, process fusion, and supplier detail.

**Components:** `QueueResponse`, `ConservationResponse`, `SuppliersResponse`, `MetricCard`, `CurveChart`, `SupplierProfile`, `SupplierIntelligenceProfilePanel`, `FinancialImpactPanel`, `NoveltyPanel`, `CompliancePanel`, `DisruptionSimPanel`, `ProcessFusionPanel`, `ProcessTimelinePanel`, `TrendCorrelationPanel`, `WorkingCapitalPanel`.

**API endpoints:**

- `GET /api/s2p/preview/queue` — live keys: `status`, `engine_version`, `total`, `showing`, `exceptions`, `invoices`, `auto_approve_rate`, `confidence_avg`, `scorer`.
- `GET /api/s2p/preview/conservation` — live keys include `engine_version`, `source`, `status`, `auto_approve_rate`, `accuracy`, `verified_decisions`, `penalty_ratio`, `passed`, `curve`, `computed_status`, `auto_approve_pct`, `fixture_decisions`, `copilot`, `conservation_product`, `conservation_threshold`.
- `GET /api/s2p/preview/suppliers` — live keys: `engine_version`, `total`, `showing`, `suppliers`, `source`.
- `GET /api/s2p/suppliers/{supplier_id}/profile` — selected supplier detail.

**Clickable elements:** supplier selection; queue/exception selection; preview sections; curve and metric controls; simulation controls.

**Badges:** `Badge`, conservation status, provenance, source, and preview/engine-version labels.

### Tab 7 — Evidence Room (`GovernanceTab.tsx`)

**Purpose:** governance evidence, compliance, RL reward/exploration demonstrations, recent evolution, and connector writeback.

**Components:** `GovernanceSection`, `PanelShell`, `PanelStatus`, `RLExplorationAutoPausePanel`, `RLRewardBreakdownPanel`, `AuditEntry`, `EvidenceRoomData`, `GovernanceSummary`, `SocComplianceResponse`, `EvolutionEvent`.

**API endpoints:**

- `GET /api/soc/evidence-room` — evidence-room payload.
- `GET /api/governance/summary` — live keys: `title`, `generated_at`, `overall_assessment`, `legal_disclaimer`, `sections`.
- `GET /api/soc/compliance` — compliance response.
- `GET /api/evolution/recent-events?limit=20` — event list.
- `GET /api/platform/rl-reward-demo` — reward demonstration.
- `GET /api/platform/rl-exploration-demo` — exploration/auto-pause demonstration.
- `GET /api/soc/evidence-room/export` — evidence export.
- `POST /api/servicenow/create-incident` — connector writeback.
- `POST /api/sentinel/writeback-test` — connector writeback test.

**Clickable elements:** export; ServiceNow incident action; Sentinel writeback action; governance section expand/collapse; refresh/status controls.

## Trading copilot — port 8010 / frontend 5174

Navigation labels are `Dashboard`, `Log Trade`, `Analysis`, `Performance`, `Journal`, and `Trade Detail`. `Trade Detail` is opened by selecting a dashboard/history trade and can return to Dashboard.

### Dashboard (`DashboardScreen.tsx`)

- **Purpose:** portfolio snapshot, market context, trade history, accuracy, regimes, and day-zero state.
- **Components:** `PortfolioSummary`, `MarketContext`, `MarketSnapshot`, `TradeCard`, `TradeHistoryDecision`, `DecisionHistory`, `AccuracyByCategory`, `CalendarHeatmap`, `PortfolioConcentration`, `RegimePanel`, `ThesisBreakdown`, `ArchetypeSelector`, `DayZeroPanel`, `PatternBadge`, `TransferBadge`, `DataTrustBadge`.
- **Clickable:** `Log Trade` button; scroll-to-archetype button; trade-row selection opens Trade Detail.
- **Bindings:** selected trade id, current archetype, market/ticker values, portfolio values, decision history, category accuracy, regime and thesis summaries.
- **Badges:** data trust, pattern, transfer, and day-zero status.
- **API:** screen obtains dashboard/trade data through `apps/trading/frontend/src/api`; route names are shared by the listed panels and backend API module.

### Log Trade (`LogTradeScreen.tsx`)

- **Purpose:** enter/select a trade, pre-score it, run scoring, inspect evidence, and receive an action result.
- **Components:** `TickerLookup`, `MarketSnapshot`, `PositionSizer`, `PreScorePanel`, `EngineAssessment`, `ReasoningPanel`, `EvidencePanel`, `OptionsFactorPanel`, `ResearchChecklist`, `SimilarTradesPanel`, `ScoreResultCard`, `SituationalAbstentionBanner`.
- **Clickable:** form controls; ticker lookup; submit/score button; dropdowns and factor inputs; similar-trade selection.
- **Bindings:** `TradeFormState`, ticker data, market snapshot, score response, fingerprint, analytics, evidence, reasoning, reward line.
- **Badges/status:** score result, engine assessment, abstention, evidence/provenance, and reward status.
- **API:** scoring and ticker/query calls are routed through the local Trading API helper; the score submit is the primary mutation.
- **Primary score endpoint:** `POST /api/score` from the SDK `scoring_router.py`; request is the domain score request and response is `ScoreResponse`.

### Analysis (`AnalysisScreen.tsx`)

- **Purpose:** analytical views of regimes, counterfactuals, correlations, patterns, risk, and profile archetypes.
- **Components:** `DecisionExplorer`, `CounterfactualCard`, `FingerprintPanel`, `CorrelationPanel`, `PatternDetectionPanel`, `RegimePanel`, `RegimeChart`, `RegimeMirrorPanel`, `RegimeVRPCard`, `RiskManagementCard`, `TrustRadarPanel`, `RuleLifecyclePanel`, `RuleGenealogyTree`, `ClaimGateBadge`, `ResearchImpactChart`, `TailBetsCard`, `VolSharpeCard`, `VRPAttributionCard`, `ContrastCard`, `DispersionFollowCard`.
- **Clickable:** decision explorer rows; counterfactual controls; regime/profile selectors; expandable evidence and rule panels.
- **Bindings:** fingerprint, category/regime metrics, correlation data, counterfactual response, lifecycle/genealogy, research impact, risk and volatility series.
- **Badges:** claim gate and trust/evidence badges.

### Performance (`PerformanceScreen.tsx`)

- **Purpose:** performance, audit, conservation, cohort, regime, evolution, promotion, and rejection telemetry.
- **Components:** `RollingMetrics`, `ExecutionQualityCard`, `CategoryPerformance`, `CentroidTimeline`, `CentroidTimelineChart`, `ConservationProjection`, `ConservationState`, `CohortStatusPanel`, `AuditTrail`, `RegimeAnalyticsPanel`, `RegimeStatusPanel`, `RegimePanel`, `EvolutionPanel`, `EvolutionControlsPanel`, `PromotionDashboard`, `AutonomyThrottlePanel`, `ReConvergencePanel`, `RejectionMomentPanel`, `RejectionMomentTable`, `RichCheapPanel`, `GateDividendPanel`, `DispersionPanel`, `RiskManagementCard`, `CertificatePanel`, `RegimeRejectionPanel`.
- **Clickable:** timeline/checkpoint selectors; evolution controls; promotion/rejection actions; audit expansion; regime filters.
- **Bindings:** rolling metrics, centroid checkpoints, conservation state, cohort metrics, audit rows, promotion state, rejection moments.
- **Badges:** conservation, autonomy, cohort, certification, promotion, and evidence status.

### Journal (`JournalScreen.tsx`)

- **Purpose:** query/filter trade journal and inspect selected trade details, earnings, event-driven categories, and options factors.
- **Components:** `JournalQueryBar`, `TradeDetailPanel`, `EvidencePanel`, `EarningsInsightCard`, `EventDrivenSubcategorySplit`, `OptionsFactorPanel`, aggregate/stat cards.
- **Clickable:** query submit; journal filters; trade-row selection; selected-trade detail.
- **Bindings:** `TradesResponse`, journal entries, selected id, aggregate cards, earnings and event split, options factors.
- **API:** journal query is `POST /api/trading/journal/query` with query/filter body.

### Trade Detail (`TradeDetailScreen.tsx`)

- **Purpose:** focused detail view for a selected trade.
- **Components:** `TradeHistoryDecision`, `FactorBar`, `Stat`, `EmptyState`.
- **Clickable:** back buttons return to Dashboard; detail history controls if populated.
- **Bindings:** `tradeId`, ticker data, decision, factor values, historical action/result.
- **Conditional:** empty state when no active trade id or no matching record.

### Trading live API shape probe

| Path | Observed top-level keys |
|---|---|
| `/api/health` | `phase`, `alpha`, `engine` |
| `/api/fingerprint` | `factors`, `overall_win_rate`, `per_category_precision`, `decisions_analyzed`, `engine`, `skipped_decisions` |
| `/api/trajectory` | `points`, `current_iks`, `current_win_rate`, `decisions_total`, `days_active`, `engine` |
| `/api/conservation/status` | `engine`, `domain`, `verified_count`, `correct_count`, `total_decisions`, `penalty_ratio`, `alpha`, `q`, `V`, `baseline`, `baseline_q`, `relative_trigger`, `relative_trigger_ratio`, category counts, `theta_min`, `headroom`, `status`, `passed`, `conservation_mode`, `conservation_applicable` |
| `/api/self/accuracy-by-category` | `categories`, `threshold`, `overall_verified`, `evidence_tier`, `evidence_label`, `evidence_gate`, `claim_id` |
| `/api/self/decisions` | `decisions`, `total` |
| `/api/self/centroid-history` | `checkpoints`, `total` |
| `/api/self/rule-genealogy` | `domain`, `rules`, `total` |
| `/api/self/audit-trail` | `trails`, `total` |
| `/api/evolution/variants` | `domain`, `variants`, `active_rules`, `promoted_rules`, totals |
| `/api/self/rule-lifecycle` | 404 — planned, awaiting SC-PORT (MAP #16). Not available until self-computation endpoints are ported to Trading/Purchasing. |

## Purchasing copilot — port 8020 / frontend 5175

Navigation labels are `Dashboard`, `Order`, `Analysis`, `Inventory`, and `Performance`.

### Dashboard (`DashboardScreen.tsx`)

- **Purpose:** procurement overview, alerts, spend, weather/commodity context, par levels, auto-order, and day-zero readiness.
- **Components:** `AEStatusBar`, `AlertDashboardCard`, `AccuracyAlertPanel`, `AutoOrderPanel`, `CommodityPricePanel`, `DayZeroCard`, `DecisionHistory`, `IgnoringCostCard`, `OrderCard`, `ParLevelMonitor`, `ParLevelPanel`, `SpendSummaryPanel`, `WeatherImpactCard`, `WeatherWidget`, `EventBadge`, `ProvenanceBadge`, `TransferBadge`, `DataTrustBadge`, `NotYetPanel`.
- **Clickable:** select item; open order flow; auto-order actions; dashboard cards; weather/commodity drilldowns.
- **Bindings:** dashboard state, selected item, inventory/par levels, alerts, spend, weather, event impact, readiness, data trust.
- **Badges:** AE-managed, provenance, transfer, event, and data-trust badges.

### Order (`OrderScreen.tsx`)

- **Purpose:** score an order, inspect cost/demand/weather context, compare similar orders, and verify a procurement action.
- **Components:** `OrderContext`, `ItemProfile`, `CostAnalysis`, `ExpectedDemandChoice`, `WeatherWidget`, `WasteHistory`, `SimilarOrdersPanel`, `OrderQueuePanel`, `TodaySummary`, `EngineAssessment`, `ReasoningPanel`, `MatchResultPanel`, `ScoreResultCard`, `VerifyReasonCode`, `VerifyReasonOption`, `AEManagedBadge`, `EventBadge`.
- **Clickable:** score button; disabled while scoring or when no current item; reason-code selection; verify/confirm action; expected-demand choice; similar-order selection.
- **Bindings:** selected item, scoring state, score response, analytics, demand, weather, waste history, match result, verification response.
- **API:** scoring/verification/order queue calls are routed through the Purchasing API helper.
- **Primary score endpoint:** `POST /api/score` from the SDK `scoring_router.py`; the response is the shared `ScoreResponse` consumed by `ScoreResultCard`.

### Analysis (`AnalysisScreen.tsx`)

- **Purpose:** category accuracy, discovery digest, event impact, counterfactuals, waste, menu matrix, fingerprints, and trust.
- **Components:** `CategoryAccuracyChart`, `DecisionExplorerPanel`, `DiscoveryDigestCard`, `EventImpactCard`, `CounterfactualCard`, `WasteCostCard`, `MenuMatrixCard`, `MirrorOpenPanel`, `GatedSignalReliabilityPanel`, `FingerprintPanel`, `ProfileArchetype`, `TrustRadarPanel`, `ContrastCard`, `ProvenanceBadge`.
- **Clickable:** decision rows; counterfactual controls; profile/archetype selectors; event/discovery expansion; category filters.
- **Bindings:** analytics, category accuracy, fingerprints, discovery, event, waste, counterfactual, trust and archetype fields.

### Inventory (`InventoryScreen.tsx`)

- **Purpose:** item profiles, supplier intelligence, delivery schedules, predictive par, event planning, and rule evolution.
- **Components:** `ItemProfile`, `SupplierIntelligencePanel`, `DeliveryScheduleCard`, `PredictiveParCard`, `EventPlannerCard`, `EvolutionPanel`, `RuleLifecyclePanel`, `RuleGenealogyTree`, `AuditTrailViewer`, `CategoryEmoji`.
- **Clickable:** item selection; supplier/detail expansion; event-planner controls; evolution/rule tree expansion; audit filters.
- **Bindings:** `Item`, inventory quantities, supplier records, par predictions, delivery schedule, event state, variant/rule history.

### Performance (`PerformanceScreen.tsx`)

- **Purpose:** procurement performance, conservation, proof ledger, economic impact, chain transfer, disruption recovery, and reporting.
- **Components:** `AlertDashboardCard`, `AuditExportPanel`, `CategoryAccuracyChart`, `CentroidTimelineChart`, `ChainTransferCard`, `CohortStatusPanel`, `ConservationProjection`, `ConservationState`, `ContinuityClosePanel`, `DisruptionRecoveryPanel`, `EconomicDashboardCard`, `GroupDashboardCard`, `IKSTrackerPanel`, `PaymentTimingPanel`, `ProofLedgerPanel`, `PurchasingProofPanel`, `SelfPausePanel`, `SupplierScorecardPanel`, `TimeToCompetencePanel`, `TrajectoryChart`, `WasteAlertCard`, `WasteCostCard`, `WeeklyReportPanel`.
- **Clickable:** audit export; report download; proof/evidence expansion; disruption controls; supplier and cohort filters; timeline controls.
- **Bindings:** proof curves, competence curves, ledger entries, attribution, honest dollars, conservation status, payment timing, trajectory, waste, weekly report.

### Purchasing endpoint registry and live shapes

| Path | Method/use | Live top-level shape or source role |
|---|---|---|
| `/api/health` | GET | `phase`, `alpha`, `graph_backend`, `graph_status`, `engine`, `iks_score`, availability/counts, cache, connectors |
| `/api/purchasing/proof-ledger` | GET | `proof_curve`, `competence_curve`, `entries`, `attribution`, `honest_dollars`, `source` |
| `/api/purchasing/day-0-readiness` | GET | `ready`, `day_zero`, `coverage`, `conservation_status`, `evidence_floor`, `not_yet` |
| `/api/purchasing/legal-exposure` | GET | `compliance_status`, `flagged_orders`, `controls`, `separation_of_duties` |
| `/api/purchasing/frozen-twin` | GET | `available`, `status`, `evidence_tier` |
| `/api/purchasing/payment/summary` | GET | supplier count, DPO, discount totals, capture rate, opportunity, narrative, provenance |
| `/api/purchasing/payment/timing` | GET | payment-timing payload |
| `/api/purchasing/report/weekly` | GET | weekly report payload |
| `/api/purchasing/economic/roi-summary` | GET | ROI summary payload |
| `/api/purchasing/proof-ledger` | GET | proof/competence curve and ledger data |
| `/api/purchasing/audit/export/csv` | GET | CSV download |
| `/api/purchasing/audit/export/json` | GET | JSON export |
| `/api/purchasing/audit/pack` | GET/POST | audit pack generation/download |
| `/api/purchasing/chain/transfer` | POST | chain-transfer action/result |
| `/api/purchasing/demo/chain-seed` | POST | demo seed action |
| `/api/purchasing/disruption/history` | GET | disruption history |
| `/api/purchasing/disruption/status` | GET | disruption status |

## DataOps copilot — port 8030 / frontend 5176

Navigation labels are `Dashboard`, `Triage`, `Insight`, `Evidence`, and `Curve`.

### Dashboard (`DashboardScreen.tsx`)

- **Purpose:** enterprise health, alert queue, process timeline, data-intelligence wiring, compounding overlay, and conservation readiness.
- **Components:** `DashboardFrame`, `EnterpriseHealthBar`, `PipelineGrid`, `AlertQueue`, `AlertGroupCard`, `UngroupedAlerts`, `ProcessTimelinePanel`, `EnterpriseValueCard`, `NLQueryPanel`, `DIWiringPanel`, `AEImpactPanel`, `AccuracyAlertPanel`, `CompoundingCurveOverlay`, `ConservationProjection`, `ConservationSlider`, `ConservationTimeline`, `DayZeroPanel`, `ProvenanceBadge`, `SAPDataBadge`, `TransferBadge`, `CelonisBadge`.
- `CelonisBadge` is domain-specific, not an SDK shared component: it is used by DataOps `DashboardScreen` and the SOC process-timeline surface.
- **Clickable:** alert selection switches to Triage; NL query submit; conservation slider; alert group expansion; process/enterprise drilldown.
- **Bindings:** dashboard state, alert groups, ungrouped alerts, process timeline, enterprise value, DI recommendations, conservation and readiness.
- **Badges:** SAP data, provenance, transfer, Celonis, and conservation status.

### Triage (`TriageScreen.tsx`)

- **Purpose:** select an alert, score it, inspect similar alerts/process signals, apply a fix, and view resolution/recurrence context.
- **Components:** `TriageFrame`, `ScoreResultCard`, `ReasoningPanel`, `ActionPicker`, `FactorAutoFill`, `SimilarAlertsPanel`, `ProcessSignalsPanel`, `DependencyTree`, `ResolutionTimeline`, `SLACountdown`, `AbstentionBanner`, `RecurrenceBadge`, `CrossGraphInsightCard`, `ApplyFixModal`, `SystemHistoryResponse`.
- **Clickable:** back; alert/action selection; score; apply-fix modal open/confirm; reason/action controls.
- **Bindings:** selected alert id, triage data, score response, fingerprint, similar alerts, process signals, SLA, dependency graph, fix response.
- **Primary score endpoint:** `POST /api/score` from the SDK `scoring_router.py`; the triage request carries domain factors and the response drives `ScoreResultCard`, reasoning, and action controls.

### Insight (`InsightScreen.tsx`)

- **Purpose:** acquisition advice, source profile, bottlenecks, cross-graph insight, search, reordering what-if, and earned proof.
- **Components:** `AcquisitionAdvisorPanel`, `AcquisitionPanel`, `BottleneckPanel`, `CrossGraphInsightCard`, `DecisionExplorerPanel`, `EarnedProofPanel`, `FingerprintPanel`, `FusionClimaxPanel`, `IncidentReplayCard`, `IntelligenceMapPanel`, `ProcessTimelinePanel`, `SearchPanel`, `SourceCompoundingPanel`, `SourceProfilePanel`, `WhatIfReordering`, `ProfileArchetype`.
- **Clickable:** search; acquisition/what-if controls; decision selection; incident replay; source/profile expansion.
- **Bindings:** incidents, fingerprint, process timeline, bottleneck, acquisition advice, source profile, cross-graph insight, proof and fusion metrics.

### Evidence (`EvidenceScreen.tsx`)

- **Purpose:** governance, audit, frozen twin, schema impact, operational rules, variants, and promotion/lifecycle evidence.
- **Components:** `AuditTrailPanel`, `AuditTrailViewer`, `DataOpsGovernancePanel`, `AgentTrustGatewayPanel`, `FrozenTwinControlPanel`, `SchemaImpactPanel`, `OperationalRulesPanel`, `RuleLifecyclePanel`, `RuleGenealogyPanel`, `RuleGenealogyTree`, `PromotionPanel`, `EvolutionPanel`, `TransferStatusPanel`, `CohortStatusPanel`, `CrossSystemPanel`, `AEImpactPanel`.
- **Clickable:** audit filters/export; frozen-twin controls; rule/variant expansion; promotion controls; schema/evidence drilldowns.
- **Bindings:** audit rows, rule genealogy/lifecycle, variants, promotion state, frozen-twin status, schema impact, transfer and cohort status.

### Curve (`CurveScreen.tsx`)

- **Purpose:** centroid/trajectory and disruption annotation view.
- **Components:** `CentroidTimeline`, `CentroidTimelineChart`, `TrajectoryChart`, `DisruptionAnnotation`.
- **Clickable:** timeline/checkpoint selection; chart hover/range controls.
- **Bindings:** `CentroidHistoryResponse`, `TrajectoryResponse`, frames, and disruption annotations.

### DataOps endpoint registry and live shapes

| Path | Method/use | Live top-level shape or source role |
|---|---|---|
| `/api/health` | GET | `status`, `domain`, `phase`, `alpha`, graph connection/source, engine, cache, connectors |
| `/api/context/process-timeline` | GET | `source`, `provenance`, `process_models`, `activities`, `bottleneck_id`, durations, slowdown, dollar calibration, cross-graph refs |
| `/api/context/alert-groups` | GET | `groups`, `ungrouped`, `total_alerts`, `total_groups` |
| `/api/dataops/di/acquisitions` | GET | `recommendations`, `narrative`, `provenance`, `monetization` |
| `/api/context/cross-graph-insight/{alertId}` | GET | cross-graph insight for selected alert |
| `/api/discovery/cross-system` | GET | `alerts`, `provenance` |
| `/api/di/acquisition-advice` | GET | acquisition advice |
| `/api/di/products` | GET | data-intelligence products; source comment documents route |
| `/api/context/process-timeline` | GET | process/timeline response |
| `/api/dataops/di/acquisitions` | GET | acquisition recommendations |

## S2P standalone copilot — port 8002 / frontend 5177

Navigation labels are `Dashboard`, `Exception Triage`, `Insight`, `Evidence`, `Suppliers`, and `Performance`.

### Dashboard (`DashboardScreen.tsx`)

- **Purpose:** exception queue, conservation, control tower, day-zero, novelty, disruption, process context, financial impact, and transfer state.
- **Components:** `ControlTowerPanel`, `AutoApprovePanel`, `ConservationMiniGauge`, `ConservationStatus`, `DayZeroCard`, `DayZeroReadinessPanel`, `DecisionRow`, `DisruptionSimPanel`, `FinancialImpactCard`, `NoveltyStatusPanel`, `ProcessContextCard`, `TransferBadge`, `Metric`.
- **Clickable:** decision/exception row; control tower/drilldown; disruption simulation; dashboard card links.
- **Bindings:** queue response, auto-approve, conservation status, readiness, process context, novelty, financial impact, decision rows.

### Exception Triage (`TriageScreen.tsx`)

- **Purpose:** score an invoice exception, inspect evidence/reasoning, compare rule vs reasoning, learn/confirm an action, and view counterfactuals.
- **Components:** `ScoreResultCard`, `SituationPanel`, `ProcessContextPanel`, `S2PReasoningPanel`, `RuleVsReasoningPanel`, `CounterfactualCard`, `FactorMap`, `CentroidExplorer`, `EvidenceTemplatePanel`, `CrossCopilotSignalBanner`, `NoveltyAlertBanner`, `ConservationStatus`, `S2PConservationProjection`, `ProvenanceBadge`, `Metric`.
- **Clickable:** score; action picker; confirm/learn; counterfactual controls; evidence/centroid expansion; back/navigation.
- **Bindings:** `InvoiceException`, `S2PAction`, reason code, score response, situation response, process context, conservation and novelty state.
- **Primary score endpoint:** `POST /api/s2p/score` from the S2P router; response is `S2PScoreResponse` and feeds score, reasoning, evidence, conservation, and learn/confirm surfaces.

### Insight (`InsightScreen.tsx`)

- **Purpose:** supplier/invoice insight, process fusion, early warnings, factor fingerprint, leakage, discovery, and what-if inspection.
- **Components:** `CentroidExplorerPanel`, `CrossGraphInsightCard`, `DiscoveryExtendedPanel`, `EarlyWarningPanel`, `FactorFingerprintPanel`, `LeakageDetectionPanel`, `ProcessContextPanel`, `ProcessFusionPanel`, `ProcessSignalsPanel`, `SimilarInvoicesPanel`, `WhatIfInspectorPanel`.
- **Clickable:** supplier/invoice selection; what-if inspector; similar invoice selection; discovery/early-warning expansion; factor explorer controls.
- **Bindings:** preview queue, supplier/profile, cross-graph, process signals, factor fingerprint, leakage, early warnings, what-if response.

### Evidence (`EvidenceScreen.tsx`)

- **Purpose:** compliance, audit, receipt chain, discovery, disruption recovery, exception extinction, evolution, and lifecycle evidence.
- **Components:** `AuditExportPanel`, `AuditTrailPanel`, `CohortStatusPanel`, `CompliancePanel`, `ComplianceScreeningPanel`, `DiscoveryPanel`, `DisruptionRecoveryPanel`, `EvolutionPanel`, `ExceptionExtinctionTimeline`, `FactorInsightPanel`, `ReceiptChainPanel`, `RuleLifecyclePanel`.
- **Clickable:** audit export; compliance/evidence expansion; receipt-chain inspection; rule/evolution controls; disruption recovery controls.
- **Bindings:** audit rows, compliance status, receipt chain, cohort, discovery, evolution, exception extinction, rule lifecycle.

### Suppliers (`SuppliersScreen.tsx`)

- **Purpose:** supplier list, supplier detail, clustering, heatmap, payment strategy, rationalization, and supplier history.
- **Components:** `SupplierCard`, `SupplierDetailPanel`, `SupplierHistoryPanel`, `SupplierProfileDetail`, `SupplierHeatmap`, `SupplierSeasonalChart`, `ClusteringPanel`, `PaymentStrategyPanel`, `RationalizationPanel`, Recharts `BarChart`/`LineChart`.
- **Clickable:** load suppliers; supplier row/card selection; chart and cluster filters; history/detail expansion.
- **Bindings:** supplier list, selected supplier, profile, history events, trends, payment strategy, clustering and heatmap series.

### Performance (`PerformanceScreen.tsx`)

- **Purpose:** authority, confidence, conservation, cycle time, financial impact, frozen twin, operational summary, trajectory, and what-if simulation.
- **Components:** `AuthorityPanel`, `ConfidenceBandPanel`, `ConservationMiniGauge`, `ConservationStatus`, `CycleTimePanel`, `FinancialImpactTrendPanel`, `FrozenTwinComparisonPanel`, `OperationalSummary`, `TrajectoryChart`, `WhatIfSimulator`.
- **Clickable:** authority/confidence drilldowns; what-if simulator; frozen-twin comparison; trajectory range controls.
- **Bindings:** authority state, confidence bands, conservation status, cycle-time series, financial trend, frozen twin, operational summary and trajectory.

### S2P endpoint registry and live shapes

| Path | Method/use | Live top-level shape or source role |
|---|---|---|
| `/api/health` | GET | `status`, `service`, `version` |
| `/api/s2p/preview/queue` | GET | queue status, engine version, counts, exceptions, invoices, auto-approve rate, confidence, scorer |
| `/api/s2p/preview/conservation` | GET | engine/source/status, auto-approve, accuracy, verified decisions, penalty, passed, curve, thresholds |
| `/api/s2p/preview/suppliers` | GET | engine version, total/showing, suppliers, source |
| `/api/s2p/suppliers/{supplier_id}/profile` | GET | supplier profile/detail |
| `/api/s2p/score/counterfactual` | POST | score/counterfactual response; request contains factors and perturbations |
| `/api/s2p/suppliers/early-warnings` | GET | early-warning supplier data |
| `/api/s2p/suppliers/payment-portfolio` | GET | payment portfolio |
| `/api/s2p/suppliers/payment-strategy` | GET | payment strategy |
| `/api/s2p/suppliers/trends` | GET | supplier trends |
| `/api/s2p/insight/cross-graph` | GET | cross-graph insight |
| `/api/s2p/insight/process-signals` | GET | process signals |
| `/api/s2p/compliance/report` | GET | compliance report |
| `/api/s2p/financial-impact` | GET | financial-impact payload |
| `/api/s2p/novelty/status` | GET | novelty state |
| `/api/s2p/simulation/scenarios` | GET | simulation scenario list |
| `/api/s2p/simulation/impact-summary` | GET | simulation impact summary |

### SDK shared routers (mounted by all SDK copilots)

These endpoints are provided by `copilot-sdk` backend routers and mounted in each SDK copilot's `main.py`; they are not copilot-specific.

- `GET /api/health` — scoring/app health.
- `GET /api/fingerprint` — scoring-router fingerprint state.
- `GET /api/trajectory` — scoring-router trajectory state.
- `POST /api/score` — scoring-router primary scoring mutation.
- `POST /api/learn` — scoring-router verified learning mutation.
- `GET /api/conservation/status` — conservation-router status.
- `POST /api/conservation/what-if` — conservation what-if calculation.
- `GET /api/self/*` — self-computation routes where mounted.
- `GET /api/evolution/variants` — evolution-router variants where mounted.

### SDK component file counts

The exact source counts used for this inventory are: Trading 70 component files plus 6 screen files; Purchasing 57 plus 5; DataOps 70 plus 5; S2P 57 plus 6; SOC 33 general component files plus 7 tab files. These are file counts, not unique imported JSX symbols.

## Cross-copilot shared patterns

### Score → evidence → confirm → reward

- Trading: Log Trade scoring, evidence/reasoning, result, and reward/feedback components.
- Purchasing: Order scoring, evidence/reasoning, verify reason code, and outcome components.
- DataOps: Triage score, process/evidence panels, apply-fix path, and resolution state.
- S2P: Exception score, evidence/reasoning, confirm/learn action, and conservation projection.
- SOC: Alert triage, investigation, outcome feedback, and learning-state update.

### Safety and provenance

- Conservation surfaces display status, threshold/baseline, pass/fail, and pause/coverage concepts.
- Provenance/data-trust badges identify source tier or evidence quality.
- Transfer badges identify cross-domain or learned-transfer state.
- Domain-specific markers include `AEManagedBadge`, `SAPDataBadge`, `PaperBadge`, and `EvidenceTierBadge`; `CelonisBadge` is used specifically by DataOps and SOC.

### Common interaction contracts

- Shell tab click changes `activeTab` without a full page reload.
- Summary row/card click stores a selected id and routes to a detail/triage screen.
- Score/analysis controls expose loading and error states.
- Expand/collapse uses chevrons or section buttons.
- Export controls produce CSV, JSON, PDF, audit pack, or evidence-room artifacts.
- Simulation/what-if controls should be treated as mutations or long-running operations in E2E tests.

## API endpoint registry — consolidated

The following registry consolidates paths found in screen/component source. Exact request bodies should be taken from the named component/helper before writing contract tests.

| Copilot | Method | Path | Primary consumer |
|---|---|---|---|
| SOC | GET | `/api/health` | shell/bootstrap |
| SOC | POST | `/api/alert/analyze` | Alert Triage primary decision pipeline |
| SOC | GET | `/api/soc/detection-engineering` | SOC Analytics |
| SOC | GET | `/api/soc/learning-state` | Runtime Evolution |
| SOC | GET | `/api/soc/centroid-evolution` | Runtime/Compounding |
| SOC | GET | `/api/soc/centroid-heatmap` | Runtime Evolution |
| SOC | GET | `/api/soc/graph-stats` | Runtime Evolution |
| SOC | GET | `/api/soc/enrichment-status` | Runtime Evolution |
| SOC | GET | `/api/soc/centroid-support` | Runtime Evolution |
| SOC | GET | `/api/soc/evidence-room` | Compounding/Governance |
| SOC | GET | `/api/soc/evidence-room/export` | Compounding/Governance |
| SOC | GET | `/api/metrics/compounding/headline` | Compounding |
| SOC | GET | `/api/metrics/decision-economics` | Compounding |
| SOC | GET | `/api/soc/operational-metrics` | Compounding |
| SOC | GET | `/api/soc/economics` | Compounding |
| SOC | GET | `/api/soc/board-export` | Compounding |
| SOC | GET | `/api/governance/summary` | Governance |
| SOC | GET | `/api/soc/compliance` | Governance |
| SOC | GET | `/api/evolution/recent-events?limit=20` | Governance |
| SOC | GET | `/api/platform/rl-reward-demo` | Governance |
| SOC | GET | `/api/platform/rl-exploration-demo` | Governance |
| SOC | POST | `/api/servicenow/create-incident` | Governance |
| SOC | POST | `/api/sentinel/writeback-test` | Governance |
| SOC | GET | `/api/soc/executive-narrative` | Executive Narrative |
| SOC | GET | `/api/soc/executive-narrative/pdf` | Executive Narrative |
| SOC | GET | `/api/platform/domain-applicability` | Executive Narrative |
| SOC | GET | `/api/s2p/preview/queue` | S2P Preview |
| SOC | GET | `/api/s2p/preview/conservation` | S2P Preview |
| SOC | GET | `/api/s2p/preview/suppliers` | S2P Preview |
| SOC | GET | `/api/s2p/suppliers/{id}/profile` | S2P Preview |
| Trading | GET | `/api/health` | shell/bootstrap |
| Trading | POST | `/api/score` | Log Trade primary scoring mutation |
| Trading | GET | `/api/fingerprint` | dashboard/analysis |
| Trading | GET | `/api/trajectory` | dashboard/performance |
| Trading | GET | `/api/conservation/status` | performance |
| Trading | GET | `/api/self/accuracy-by-category` | dashboard/performance |
| Trading | GET | `/api/self/decisions` | dashboard/journal |
| Trading | GET | `/api/self/centroid-history` | performance |
| Trading | GET | `/api/self/rule-genealogy` | analysis/performance |
| Trading | GET | `/api/self/audit-trail` | performance |
| Trading | GET | `/api/evolution/variants` | performance |
| Trading | POST | `/api/trading/journal/query` | Journal |
| Trading | GET | `/api/trading/regime-analytics` | Analysis/Performance |
| Trading | GET | `/api/trading/score/counterfactual/default` | Analysis |
| Purchasing | GET | `/api/health` | shell/bootstrap |
| Purchasing | POST | `/api/score` | Order primary scoring mutation |
| Purchasing | GET | `/api/purchasing/proof-ledger` | Performance |
| Purchasing | GET | `/api/purchasing/day-0-readiness` | Dashboard/Performance |
| Purchasing | GET | `/api/purchasing/legal-exposure` | Performance |
| Purchasing | GET | `/api/purchasing/frozen-twin` | Performance |
| Purchasing | GET | `/api/purchasing/payment/summary` | Performance |
| Purchasing | GET | `/api/purchasing/payment/timing` | Performance |
| Purchasing | GET | `/api/purchasing/report/weekly` | Performance |
| Purchasing | GET | `/api/purchasing/economic/roi-summary` | Dashboard/Performance |
| Purchasing | GET | `/api/purchasing/audit/export/csv` | Performance |
| Purchasing | GET | `/api/purchasing/audit/export/json` | Performance |
| Purchasing | POST | `/api/purchasing/chain/transfer` | Performance |
| Purchasing | GET | `/api/purchasing/disruption/history` | Performance |
| Purchasing | GET | `/api/purchasing/disruption/status` | Performance |
| DataOps | GET | `/api/health` | shell/bootstrap |
| DataOps | POST | `/api/score` | Triage primary scoring mutation |
| DataOps | GET | `/api/context/process-timeline` | Dashboard/Insight/Curve |
| DataOps | GET | `/api/context/alert-groups` | Dashboard/Triage |
| DataOps | GET | `/api/context/cross-graph-insight/{alertId}` | Triage/Insight |
| DataOps | GET | `/api/dataops/di/acquisitions` | Dashboard/Insight |
| DataOps | GET | `/api/di/acquisition-advice` | Insight |
| DataOps | GET | `/api/di/products` | Dashboard/Insight |
| DataOps | GET | `/api/discovery/cross-system` | Insight/Evidence |
| S2P | GET | `/api/health` | shell/bootstrap |
| S2P | POST | `/api/s2p/score` | Exception Triage primary scoring mutation |
| S2P | GET | `/api/s2p/preview/queue` | Dashboard |
| S2P | GET | `/api/s2p/preview/conservation` | Dashboard/Performance |
| S2P | GET | `/api/s2p/preview/suppliers` | Suppliers |
| S2P | GET | `/api/s2p/suppliers/{supplier_id}/profile` | Suppliers/Insight |
| S2P | POST | `/api/s2p/score/counterfactual` | Triage/Insight |
| S2P | GET | `/api/s2p/suppliers/early-warnings` | Insight |
| S2P | GET | `/api/s2p/suppliers/payment-portfolio` | Suppliers |
| S2P | GET | `/api/s2p/suppliers/payment-strategy` | Suppliers |
| S2P | GET | `/api/s2p/suppliers/trends` | Suppliers |
| S2P | GET | `/api/s2p/insight/cross-graph` | Insight |
| S2P | GET | `/api/s2p/insight/process-signals` | Insight |
| S2P | GET | `/api/s2p/compliance/report` | Evidence |
| S2P | GET | `/api/s2p/financial-impact` | Dashboard/Performance |
| S2P | GET | `/api/s2p/novelty/status` | Dashboard/Insight |
| S2P | GET | `/api/s2p/simulation/scenarios` | Dashboard/Performance |
| S2P | GET | `/api/s2p/simulation/impact-summary` | Dashboard/Performance |

## Component cross-reference

| Component family | Copilots | Screens/tabs | Clickable/API behavior |
|---|---|---|---|
| `CopilotShell` | Trading, Purchasing, DataOps, S2P | every SDK screen | tab navigation |
| `ProvenanceBadge` | SOC, Purchasing, DataOps, S2P | evidence/summary/triage | visual only; binds provenance |
| `TransferBadge` | all five | shell/summary | visual transfer state |
| `Conservation*` | all five | performance/governance/preview | threshold/status/safety display |
| `DecisionExplorer*` | Trading, Purchasing, DataOps | analysis/insight | row selection and detail |
| `AuditTrail*` | all five | evidence/performance | expand/filter/export |
| `Evolution*` | all five | runtime/performance/evidence | checkpoints/rules/promotion |
| `ReasoningPanel` family | Trading, Purchasing, DataOps, S2P | score/triage/order | evidence/reasoning display |
| `Counterfactual*` | Trading, Purchasing, S2P | analysis/triage | perturbation/score controls |
| `TrajectoryChart` family | Trading, Purchasing, DataOps, S2P | performance/curve | time-range/hover |
| `DayZero*` | SOC, Trading, Purchasing, DataOps, S2P | dashboard/readiness | readiness state |
| `CohortStatusPanel` | Trading, Purchasing, DataOps, S2P | performance/evidence | cohort filter/details |
| `FingerprintPanel` | Trading, Purchasing, DataOps | analysis/insight | factor view |
| `Supplier*` panels | SOC Preview, Purchasing, S2P | preview/inventory/suppliers | supplier selection/details |
| `EvidencePanel` family | SOC, Trading, Purchasing | triage/order/log/journal | evidence expansion |
| `OutcomeFeedback` / verify | SOC, Trading, Purchasing, S2P | triage/score/order | verified outcome mutation |

## E2E coverage cross-reference

| Copilot | E2E directory | Spec files | Main coverage themes |
|---|---|---:|---|
| SOC | SOC frontend E2E | 64 | tabs, triage, compounding, governance, runtime evolution, S2P preview, exports |
| Trading | `e2e/trading` | 55 | dashboard, analysis, journal, scoring, evidence, regimes, conservation, evolution |
| Purchasing | `e2e/purchasing` | 41 | dashboard, order, analysis, inventory, performance, audit, proof, transfers |
| DataOps | `e2e/dataops` | 30 | dashboard, triage, insight, evidence, curve, data products, acquisition |
| S2P | `e2e/s2p` | 36 | tabs, triage, evidence chains, suppliers, performance, simulations, governance |

### E2E locator targets to preserve

- Shell tab labels: `Dashboard`, `Log Trade`, `Analysis`, `Performance`, `Journal`, `Trade Detail`.
- Purchasing tab labels: `Dashboard`, `Order`, `Analysis`, `Inventory`, `Performance`.
- DataOps tab labels: `Dashboard`, `Triage`, `Insight`, `Evidence`, `Curve`.
- S2P tab labels: `Dashboard`, `Exception Triage`, `Insight`, `Evidence`, `Suppliers`, `Performance`.
- SOC tab labels: `SOC Analytics`, `Runtime Evolution`, `Alert Triage`, `Compounding`, `Executive Narrative`, `S2P Preview`, `Evidence Room`.
- Primary action locators: Score, Verify, Confirm, Learn, Apply Fix, Export, Download, Run What-If, Simulate, Promote, Rollback, and connector writeback buttons.
- Primary state assertions: loading, empty/no-data, error, conservation status, provenance label, evidence tier, confidence, and selected-detail panels.

## Demo preparation checklist

- Run `python scripts/preseed_all_copilots.py` before demo to seed 80 decisions across Trading, Purchasing, and DataOps. Without this prerequisite, self-computation panels such as accuracy-by-category, centroid-history, and decisions show empty state.
- Verify all five `/api/health` endpoints before a demo.
- Verify shell navigation labels match the E2E locator contract.
- Seed or reset selected-item state before demonstrating Dashboard → Detail/Triage transitions.
- Demonstrate one score/verify flow per copilot and capture the response shape.
- Demonstrate at least one evidence or audit export per domain.
- Demonstrate conservation status and provenance badges before showing headline quality claims.
- For SOC, show Runtime Evolution, Alert Triage, Compounding, and Governance in that order when explaining the learning loop.
- For SOC S2P Preview, verify queue, conservation, suppliers, and selected supplier profile all load.
- For S2P standalone, verify the six-tab navigation and the distinction between Exception Triage and Evidence.
- For Trading, verify the `Trade Detail` return path and the live `/api/self/rule-lifecycle` 404 is either fixed or excluded from demo claims.

## Limitations and follow-up

- This is a source inventory, not a generated TypeScript schema. Request and response bodies should be confirmed in the API helper/backend route before contract-test authoring.
- Some screens delegate API calls to imported helpers, so the screen’s direct source does not contain literal `/api/` strings.
- Live probes recorded top-level keys only; nested field types and cardinalities are intentionally not copied from live business data.
- SOC source is in the configured sibling repository `gen-ai-roi-demo-v4-v50`; the inventory assumes `CLAUDE_SOC` points there.
- No source file was modified by this inventory task.
