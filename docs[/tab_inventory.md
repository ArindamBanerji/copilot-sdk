# Frontend Tab Inventory
**Generated:** 2026-06-04T22:43:40.268143+00:00
**Mode:** static

---

## TRADING (port 5174/8010)
**Accent:** red | **TSX files:** 50

**Tabs (6):** Dashboard, Log Trade, Analysis, Performance, Journal, Trade Detail

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AnalysisScreen.tsx` | 130 | ContrastCard, CorrelationPanel, CounterfactualCard, DayOfWeekChart, DecisionExplorer +8 |  |
| `DashboardScreen.tsx` | 221 | AccuracyByCategory, CalendarHeatmap, MarketContext, PortfolioConcentration, PortfolioSummary +3 |  |
| `JournalScreen.tsx` | 368 | EvidencePanel, OptionsFactorPanel |  |
| `LogTradeScreen.tsx` | 434 | EngineAssessment, EvidencePanel, OptionsFactorPanel, PreScorePanel, ResearchChecklist +2 |  |
| `PerformanceScreen.tsx` | 142 | AuditTrail, CategoryPerformance, CentroidTimeline, PromotionPanel, RiskManagementCard +3 |  |
| `TradeDetailScreen.tsx` | 267 |  |  |

**Components:** 42 files

### API Calls Referenced (20)
- `/api/conservation/status`
- `/api/context/analytics`
- `/api/context/conservation-breakdown`
- `/api/context/market-snapshot`
- `/api/context/patterns`
- `/api/context/trade-metadata`
- `/api/context/trust-analysis`
- `/api/evolution/history`
- `/api/evolution/promoted`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/history`
- `/api/learn`
- `/api/score`
- `/api/trading/prescore`
- `/api/trading/promotion`
- `/api/trading/regime`
- `/api/trading/regime/detail`
- `/api/trading/vix-timing`
- `/api/trajectory`

---

## PURCHASING (port 5175/8020)
**Accent:** green | **TSX files:** 35

**Tabs (5):** Dashboard, Order, Analysis, Inventory, Performance

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AnalysisScreen.tsx` | 123 | CategoryAccuracyChart, ContrastCard, CounterfactualCard, DayOfWeekChart, DecisionExplorerPanel +3 |  |
| `DashboardScreen.tsx` | 208 | AccuracyAlertPanel, AEStatusBar, EventBadge, IgnoringCostCard, OrderCard +2 |  |
| `InventoryScreen.tsx` | 219 | AuditTrailViewer, CategoryEmoji, ItemProfile, RuleGenealogyTree, RuleLifecyclePanel |  |
| `OrderScreen.tsx` | 593 | AEManagedBadge, CostAnalysis, EngineAssessment, EventBadge, OrderContext +2 |  |
| `PerformanceScreen.tsx` | 137 | CategoryAccuracyChart, CentroidTimelineChart, WasteCostCard |  |

**Components:** 28 files

### API Calls Referenced (19)
- `/api/conservation/status`
- `/api/context/analytics`
- `/api/context/items`
- `/api/context/order-metadata`
- `/api/context/similar`
- `/api/context/today-summary`
- `/api/context/weather`
- `/api/evolution/history`
- `/api/evolution/promoted`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/history`
- `/api/learn`
- `/api/score`
- `/api/self/accuracy-by-category`
- `/api/self/audit-trail`
- `/api/self/centroid-history`
- `/api/self/decisions`
- `/api/trajectory`

---

## DATAOPS (port 5176/8030)
**Accent:** purple | **TSX files:** 50

**Tabs (5):** Dashboard, Triage, Insight, Evidence, Curve

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `CurveScreen.tsx` | 84 | CentroidTimelineChart, CentroidTimeline, DisruptionAnnotation |  |
| `DashboardScreen.tsx` | 282 | AEImpactPanel, AccuracyAlertPanel, AlertGroupCard, AlertQueue, ConservationProjection +6 |  |
| `EvidenceScreen.tsx` | 75 | AEImpactPanel, AuditTrailViewer, OperationalRulesPanel, PatternOriginCard, RuleGenealogyTree +3 |  |
| `InsightScreen.tsx` | 114 | BottleneckPanel, CrossGraphInsightCard, DecisionExplorerPanel, IncidentReplayCard, ProcessTimelinePanel +2 |  |
| `TriageScreen.tsx` | 546 | ApplyFixModal, CrossGraphInsightCard, DependencyTree, ProcessSignalsPanel, RecurrenceBadge +4 |  |

**Components:** 43 files

### API Calls Referenced (23)
- `/api/ae/conservation-history`
- `/api/ae/impact`
- `/api/ae/incident`
- `/api/ae/operational-rules`
- `/api/ae/pattern-origin`
- `/api/ae/transfer-status`
- `/api/conservation/status`
- `/api/conservation/what-if`
- `/api/context/accuracy-by-category`
- `/api/context/alert-groups`
- `/api/context/alert-metadata`
- `/api/context/alerts`
- `/api/context/apply-fix`
- `/api/context/celonis/process-data`
- `/api/context/pipelines`
- `/api/dataops/enterprise-health`
- `/api/evolution/history`
- `/api/evolution/promoted`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/learn`
- `/api/score`
- `/api/trajectory`

---

## S2P (port 5177/8002)
**Accent:** amber | **TSX files:** 47

**Tabs (6):** Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `DashboardScreen.tsx` | 153 | AutoApprovePanel, ConservationMiniGauge, ControlTowerPanel, DisruptionSimPanel, FinancialImpactCard +2 |  |
| `EvidenceScreen.tsx` | 81 | AuditTrailPanel, AuditExportPanel, CompliancePanel, ComplianceScreeningPanel, DiscoveryPanel +4 |  |
| `InsightScreen.tsx` | 85 | CentroidExplorerPanel, CrossGraphInsightCard, DiscoveryExtendedPanel, EarlyWarningPanel, FactorFingerprintPanel +3 |  |
| `PerformanceScreen.tsx` | 46 | ConservationMiniGauge, CycleTimePanel, OperationalSummary, TrajectoryChart, WhatIfSimulator |  |
| `SuppliersScreen.tsx` | 439 | ClusteringPanel, PaymentStrategyPanel, RationalizationPanel, SupplierHeatmap |  |
| `TriageScreen.tsx` | 433 | EvidenceTemplatePanel, ProcessContextPanel, S2PConservationProjection, S2PReasoningPanel |  |

**Components:** 39 files

### API Calls Referenced (45)
- `/api/conservation/status`
- `/api/fingerprint`
- `/api/learn`
- `/api/s2p/auto-approve/expansion-proof{id}`
- `/api/s2p/auto-approve/stats`
- `/api/s2p/control-tower/classify{id}`
- `/api/s2p/control-tower/intents`
- `/api/s2p/discovery/alerts`
- `/api/s2p/discovery/disruptions`
- `/api/s2p/discovery/extended`
- `/api/s2p/evidence/audit-pack`
- `/api/s2p/evidence/chain-integrity`
- `/api/s2p/evidence/compliance`
- `/api/s2p/evidence/rules`
- `/api/s2p/evolution/promoted`
- `/api/s2p/evolution/promotion-check`
- `/api/s2p/evolution/reset`
- `/api/s2p/evolution/rules`
- `/api/s2p/evolution/shadow-results`
- `/api/s2p/evolution/variants`
- `/api/s2p/explorer/dk-weights`
- `/api/s2p/governance/compliance-screening`
- `/api/s2p/governance/rationalization`
- `/api/s2p/insight/cross-graph`
- `/api/s2p/insight/process-signals{id}`
- `/api/s2p/novelty/status`
- `/api/s2p/outcome`
- `/api/s2p/performance/summary`
- `/api/s2p/performance/trajectory`
- `/api/s2p/preview/conservation`
- `/api/s2p/preview/queue`
- `/api/s2p/preview/suppliers`
- `/api/s2p/pvg/cycle-time`
- `/api/s2p/pvg/leakage`
- `/api/s2p/pvg/variants`
- `/api/s2p/score`
- `/api/s2p/simulation/impact-summary`
- `/api/s2p/simulation/scenarios`
- `/api/s2p/suppliers`
- `/api/s2p/suppliers/clustering`
- `/api/s2p/suppliers/clusters`
- `/api/s2p/suppliers/declining`
- `/api/s2p/suppliers/early-warnings`
- `/api/s2p/suppliers/payment-strategy`
- `/api/trajectory`

---

## SOC (port 5173/8001)
**Accent:** blue | **TSX files:** 19

**Tabs (7):** SOC Analytics, Runtime Evolution, Alert Triage, Compounding, Executive Narrative, S2P Preview, Evidence Room

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AlertTriageTab.tsx` | 1670 |  |  |
| `CompoundingTab.tsx` | 2846 |  | /api/metrics/decision-economics, /api/soc/board-export, /api/soc/economics +3 |
| `ExecutiveNarrativeTab.tsx` | 808 |  | /api/platform/domain-applicability, /api/soc/executive-narrative |
| `GovernanceTab.tsx` | 899 |  | /api/governance/summary, /api/platform/rl-exploration-demo, /api/platform/rl-reward-demo +3 |
| `RuntimeEvolutionTab.tsx` | 3596 |  | /api/soc/centroid-evolution?n=200, /api/soc/centroid-heatmap, /api/soc/centroid-support +3 |
| `S2PPreviewTab.tsx` | 354 |  | /api/s2p/preview/conservation, /api/s2p/preview/queue, /api/s2p/preview/suppliers |
| `SOCAnalyticsTab.tsx` | 1293 |  | /api/soc/detection-engineering |

**Components:** 17 files

### API Calls Referenced (26)
- `/api/compounding/channel-decomposition`
- `/api/governance/summary`
- `/api/metrics/decision-economics`
- `/api/platform/domain-applicability`
- `/api/platform/rl-exploration-demo`
- `/api/platform/rl-reward-demo`
- `/api/s2p/preview/conservation`
- `/api/s2p/preview/queue`
- `/api/s2p/preview/suppliers`
- `/api/soc/board-export`
- `/api/soc/campaigns`
- `/api/soc/centroid-evolution?n=200`
- `/api/soc/centroid-heatmap`
- `/api/soc/centroid-support`
- `/api/soc/compliance`
- `/api/soc/detection-engineering`
- `/api/soc/economics`
- `/api/soc/enrichment-status`
- `/api/soc/evidence-room`
- `/api/soc/evidence-room/export`
- `/api/soc/executive-narrative`
- `/api/soc/factor-contribution`
- `/api/soc/graph-stats`
- `/api/soc/learning-state`
- `/api/soc/operational-metrics`
- `/api/triage/learning-state?category={id}`

---
