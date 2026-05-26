# Frontend Tab Inventory
**Generated:** 2026-05-26T02:36:50.742058+00:00
**Mode:** static

---

## TRADING (port 5174/8010)
**Accent:** red | **TSX files:** 46

**Tabs (4):** Dashboard, Analysis, Performance, Journal

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AnalysisScreen.tsx` | 132 | AuditTrailViewer, ContrastCard, CorrelationPanel, CounterfactualCard, DayOfWeekChart +9 |  |
| `DashboardScreen.tsx` | 221 | AccuracyAlertPanel, CalendarHeatmap, MarketContext, PortfolioConcentration, PortfolioSummary +3 |  |
| `JournalScreen.tsx` | 368 | EvidencePanel, OptionsFactorPanel |  |
| `LogTradeScreen.tsx` | 434 | EngineAssessment, EvidencePanel, OptionsFactorPanel, PreScorePanel, ResearchChecklist +2 |  |
| `PerformanceScreen.tsx` | 140 | CategoryPerformance, CentroidTimelineChart, PromotionPanel, RiskManagementCard, RollingMetrics +2 |  |
| `TradeDetailScreen.tsx` | 267 |  |  |

### Component Files (38)
- `components\AccuracyAlertPanel.tsx`
- `components\AuditTrailViewer.tsx`
- `components\CalendarHeatmap.tsx`
- `components\CategoryPerformance.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\ContrastCard.tsx`
- `components\CorrelationPanel.tsx`
- `components\CounterfactualCard.tsx`
- `components\DayOfWeekChart.tsx`
- `components\DecisionExplorerPanel.tsx`
- `components\EngineAssessment.tsx`
- `components\EvidencePanel.tsx`
- `components\MarketContext.tsx`
- `components\OptionsFactorPanel.tsx`
- `components\PaperBadge.tsx`
- `components\PatternDetectionPanel.tsx`
- `components\PortfolioConcentration.tsx`
- `components\PortfolioSummary.tsx`
- `components\PositionSizer.tsx`
- `components\PreScorePanel.tsx`
- `components\PriceSparkline.tsx`
- `components\ProfileArchetype.tsx`
- `components\PromotionPanel.tsx`
- `components\RegimeChart.tsx`
- `components\RegimePanel.tsx`
- `components\ResearchChecklist.tsx`
- `components\ResearchImpactChart.tsx`
- `components\RiskManagementCard.tsx`
- `components\RollingMetrics.tsx`
- `components\RuleGenealogyTree.tsx`
- ... +8 more

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

### Component Files (28)
- `components\AccuracyAlertPanel.tsx`
- `components\AEManagedBadge.tsx`
- `components\AEStatusBar.tsx`
- `components\AuditTrailViewer.tsx`
- `components\CategoryAccuracyChart.tsx`
- `components\CategoryEmoji.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\ContrastCard.tsx`
- `components\CostAnalysis.tsx`
- `components\CounterfactualCard.tsx`
- `components\DayOfWeekChart.tsx`
- `components\DecisionExplorerPanel.tsx`
- `components\EngineAssessment.tsx`
- `components\EventBadge.tsx`
- `components\EventImpactCard.tsx`
- `components\IgnoringCostCard.tsx`
- `components\ItemProfile.tsx`
- `components\OrderCard.tsx`
- `components\OrderContext.tsx`
- `components\ParLevelBar.tsx`
- `components\ParLevelMonitor.tsx`
- `components\ProfileArchetype.tsx`
- `components\RuleGenealogyTree.tsx`
- `components\RuleLifecyclePanel.tsx`
- `components\SimilarOrdersPanel.tsx`
- `components\WasteCostCard.tsx`
- `components\WasteSparkline.tsx`
- `components\WeatherWidget.tsx`

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
| `DashboardScreen.tsx` | 276 | AEImpactPanel, AccuracyAlertPanel, AlertGroupCard, AlertQueue, ConservationProjection +4 |  |
| `EvidenceScreen.tsx` | 75 | AEImpactPanel, AuditTrailViewer, OperationalRulesPanel, PatternOriginCard, RuleGenealogyTree +3 |  |
| `InsightScreen.tsx` | 114 | BottleneckPanel, CrossGraphInsightCard, DecisionExplorerPanel, IncidentReplayCard, ProcessTimelinePanel +2 |  |
| `TriageScreen.tsx` | 546 | ApplyFixModal, CrossGraphInsightCard, DependencyTree, ProcessSignalsPanel, RecurrenceBadge +4 |  |

### Component Files (43)
- `components\AccuracyAlertPanel.tsx`
- `components\AccuracyAlerts.tsx`
- `components\ActionPicker.tsx`
- `components\AEImpactPanel.tsx`
- `components\AERecommendationBadge.tsx`
- `components\AlertCard.tsx`
- `components\AlertGroupCard.tsx`
- `components\AlertQueue.tsx`
- `components\ApplyFixModal.tsx`
- `components\AuditTrailViewer.tsx`
- `components\BottleneckPanel.tsx`
- `components\CelonisBadge.tsx`
- `components\CentroidTimeline.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\ConservationProjection.tsx`
- `components\ConservationTimeline.tsx`
- `components\CrossGraphInsightCard.tsx`
- `components\DecisionExplorer.tsx`
- `components\DecisionExplorerPanel.tsx`
- `components\DependencyTree.tsx`
- `components\DisruptionAnnotation.tsx`
- `components\EnterpriseHealthBar.tsx`
- `components\FactorAutoFill.tsx`
- `components\IncidentReplayCard.tsx`
- `components\OperationalRulesPanel.tsx`
- `components\PatternOriginCard.tsx`
- `components\PipelineGrid.tsx`
- `components\ProcessSignalsPanel.tsx`
- `components\ProcessTimelinePanel.tsx`
- `components\ProfileArchetype.tsx`
- ... +13 more

### API Calls Referenced (21)
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
- `/api/context/enterprise-health`
- `/api/context/pipelines`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/learn`
- `/api/score`
- `/api/trajectory`

---

## S2P (port 5177/8002)
**Accent:** amber | **TSX files:** 47

**Tabs (5):** Dashboard, Insight, Evidence, Suppliers, Performance

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `DashboardScreen.tsx` | 153 | AutoApprovePanel, ConservationMiniGauge, ControlTowerPanel, DisruptionSimPanel, FinancialImpactCard +2 |  |
| `EvidenceScreen.tsx` | 81 | AuditTrailPanel, AuditExportPanel, CompliancePanel, ComplianceScreeningPanel, DiscoveryPanel +4 |  |
| `InsightScreen.tsx` | 85 | CentroidExplorerPanel, CrossGraphInsightCard, DiscoveryExtendedPanel, EarlyWarningPanel, FactorFingerprintPanel +3 |  |
| `PerformanceScreen.tsx` | 46 | ConservationMiniGauge, CycleTimePanel, OperationalSummary, TrajectoryChart, WhatIfSimulator |  |
| `SuppliersScreen.tsx` | 439 | ClusteringPanel, PaymentStrategyPanel, RationalizationPanel, SupplierHeatmap |  |
| `TriageScreen.tsx` | 433 | EvidenceTemplatePanel, ProcessContextPanel, S2PConservationProjection, S2PReasoningPanel |  |

### Component Files (39)
- `components\AuditExportPanel.tsx`
- `components\AuditTrailPanel.tsx`
- `components\AutoApprovePanel.tsx`
- `components\CentroidExplorerPanel.tsx`
- `components\ClusteringPanel.tsx`
- `components\CompliancePanel.tsx`
- `components\ComplianceScreeningPanel.tsx`
- `components\ConservationMiniGauge.tsx`
- `components\ControlTowerPanel.tsx`
- `components\CrossGraphInsightCard.tsx`
- `components\CycleTimePanel.tsx`
- `components\DiscoveryExtendedPanel.tsx`
- `components\DiscoveryPanel.tsx`
- `components\DisruptionRecoveryPanel.tsx`
- `components\DisruptionSimPanel.tsx`
- `components\EarlyWarningPanel.tsx`
- `components\EvidenceTemplatePanel.tsx`
- `components\EvolutionPanel.tsx`
- `components\FactorFingerprintPanel.tsx`
- `components\FinancialImpactCard.tsx`
- `components\LeakageDetectionPanel.tsx`
- `components\NoveltyStatusPanel.tsx`
- `components\OperationalSummary.tsx`
- `components\PaymentStrategyPanel.tsx`
- `components\ProcessContextCard.tsx`
- `components\ProcessContextPanel.tsx`
- `components\ProcessSignalsPanel.tsx`
- `components\RationalizationPanel.tsx`
- `components\ReceiptChainPanel.tsx`
- `components\RuleLifecyclePanel.tsx`
- ... +9 more

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

**Tabs (1):** Compounding

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AlertTriageTab.tsx` | 1670 |  | /api/soc/campaigns/{id} |
| `CompoundingTab.tsx` | 2818 |  | /api/eval/templates/{id}.csv, /api/metrics/decision-economics, /api/soc/board-export +4 |
| `ExecutiveNarrativeTab.tsx` | 808 |  | /api/platform/domain-applicability, /api/soc/executive-narrative, /api/soc/executive-narrative/pdf |
| `GovernanceTab.tsx` | 899 |  | /api/governance/summary, /api/platform/rl-exploration-demo, /api/platform/rl-reward-demo +3 |
| `RuntimeEvolutionTab.tsx` | 3596 |  | /api/soc/centroid-evolution?n=200, /api/soc/centroid-heatmap, /api/soc/centroid-support +3 |
| `S2PPreviewTab.tsx` | 354 |  | /api/s2p/preview/conservation, /api/s2p/preview/queue, /api/s2p/preview/suppliers |
| `SOCAnalyticsTab.tsx` | 1293 |  | /api/soc/detection-engineering |

### Component Files (17)
- `components\CampaignIntelligencePanel.tsx`
- `components\ClusterHistoryPanel.tsx`
- `components\discovery\DiscoveryBanner.tsx`
- `components\FactorContributionPanel.tsx`
- `components\LearningStatePanel.tsx`
- `components\OutcomeFeedback.tsx`
- `components\PolicyConflict.tsx`
- `components\ROICalculator.tsx`
- `components\SimulationPanel.tsx`
- `components\tabs\AlertTriageTab.tsx`
- `components\tabs\CompoundingTab.tsx`
- `components\tabs\ExecutiveNarrativeTab.tsx`
- `components\tabs\GovernanceTab.tsx`
- `components\tabs\RuntimeEvolutionTab.tsx`
- `components\tabs\S2PPreviewTab.tsx`
- `components\tabs\SOCAnalyticsTab.tsx`
- `components\ThreeChannelPanel.tsx`

### API Calls Referenced (29)
- `/api/compounding/channel-decomposition`
- `/api/eval/templates/{id}.csv`
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
- `/api/soc/campaigns/{id}`
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
- `/api/soc/executive-narrative/pdf`
- `/api/soc/factor-contribution`
- `/api/soc/graph-stats`
- `/api/soc/learning-state`
- `/api/soc/operational-metrics`
- `/api/triage/learning-state?category={id}`

---
