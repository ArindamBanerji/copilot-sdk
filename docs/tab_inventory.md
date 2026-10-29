# Frontend Tab Inventory
**Generated:** 2026-10-20T01:21:29.228501+00:00
**Mode:** static+api+screenshots

---

## TRADING (port 5174/8010)
**Accent:** red | **TSX files:** 78

**Tabs (6):** Dashboard, Log Trade, Analysis, Performance, Journal, Trade Detail

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AnalysisScreen.tsx` | 191 | ContrastCard, CorrelationPanel, CounterfactualCard, DayOfWeekChart, DecisionExplorer +10 |  |
| `DashboardScreen.tsx` | 302 | AccuracyByCategory, ArchetypeSelector, CalendarHeatmap, MarketContext, PatternBadge +5 |  |
| `JournalScreen.tsx` | 376 | EarningsInsightCard, EvidencePanel, JournalQueryBar, OptionsFactorPanel |  |
| `LogTradeScreen.tsx` | 466 | EngineAssessment, EvidencePanel, OptionsFactorPanel, PreScorePanel, ResearchChecklist +3 |  |
| `PerformanceScreen.tsx` | 201 | AuditTrail, CategoryPerformance, CentroidTimeline, CohortStatusPanel, EvolutionControlsPanel +10 |  |
| `TradeDetailScreen.tsx` | 267 |  |  |

### Component Files (70)
- `components\AccuracyAlertPanel.tsx`
- `components\AccuracyByCategory.tsx`
- `components\ArchetypeComparisonCard.tsx`
- `components\ArchetypeSelector.tsx`
- `components\AuditTrail.tsx`
- `components\AuditTrailViewer.tsx`
- `components\CalendarHeatmap.tsx`
- `components\CategoryPerformance.tsx`
- `components\CentroidTimeline.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\CohortStatusPanel.tsx`
- `components\ContrastCard.tsx`
- `components\CorrelationPanel.tsx`
- `components\CounterfactualCard.tsx`
- `components\CounterfactualPanel.tsx`
- `components\DayOfWeekChart.tsx`
- `components\DecisionExplorer.tsx`
- `components\DecisionExplorerPanel.tsx`
- `components\DemoBeatPanels.tsx`
- `components\DispersionFollowCard.tsx`
- `components\EarningsInsightCard.tsx`
- `components\EngineAssessment.tsx`
- `components\EvidencePanel.tsx`
- `components\EvidenceTierBadge.tsx`
- `components\EvolutionControlsPanel.tsx`
- `components\EvolutionPanel.tsx`
- `components\ExecutionQualityCard.tsx`
- `components\JournalQueryBar.tsx`
- `components\MarketContext.tsx`
- `components\OptionsFactorPanel.tsx`
- ... +40 more

### API Calls Referenced (57)
- `/api/archetypes/current`
- `/api/archetypes{id}`
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
- `/api/self/evolution/summary`
- `/api/trading/analytics/dispersion-follow`
- `/api/trading/analytics/regime-vrp`
- `/api/trading/analytics/vol-sharpe`
- `/api/trading/analytics/vrp-attribution`
- `/api/trading/claim-gate`
- `/api/trading/cohort-status`
- `/api/trading/evolution/active`
- `/api/trading/evolution/apply`
- `/api/trading/evolution/proposals`
- `/api/trading/evolution/rejection-summary`
- `/api/trading/evolution/rollback`
- `/api/trading/execution/analysis`
- `/api/trading/execution/summary`
- `/api/trading/pre-score`
- `/api/trading/prescore`
- `/api/trading/promotion`
- `/api/trading/promotion/dashboard`
- `/api/trading/regime`
- `/api/trading/regime-status`
- `/api/trading/regime/current`
- `/api/trading/regime/detail`
- `/api/trading/regime/performance`
- `/api/trading/regime/recommendation`
- `/api/trading/situation`
- `/api/trading/situation/abstention`
- `/api/trading/situation/conditioned-stats`
- `/api/trading/situation/regime`
- `/api/trading/situation/regime-rejections`
- `/api/trading/situation/sharpe-adjustment`
- `/api/trading/vix-timing`
- `/api/trading/volatility/dispersion`
- `/api/trading/volatility/rich-cheap{id}`
- `/api/trading/volatility/sharpe{id}`
- `/api/trading/volatility/tail-bets`
- `/api/trading/volatility/vrp`
- `/api/trading/webhook/history`
- `/api/trajectory`
- `/api/transfer/execute`
- `/api/transfer/opportunities`
- `/api/transfer/status`

### Endpoint Smoke
**46/57 returned 200**

| Path | Status |
|---|---|
| `/api/archetypes/current` | pass 200 |
| `/api/archetypes{id}` | FAIL 404 |
| `/api/conservation/status` | pass 200 |
| `/api/context/analytics` | pass 200 |
| `/api/context/conservation-breakdown` | pass 200 |
| `/api/context/market-snapshot` | pass 200 |
| `/api/context/patterns` | pass 200 |
| `/api/context/trade-metadata` | pass 200 |
| `/api/context/trust-analysis` | pass 200 |
| `/api/evolution/history` | pass 200 |
| `/api/evolution/promoted` | pass 200 |
| `/api/evolution/variants` | pass 200 |
| `/api/fingerprint` | pass 200 |
| `/api/history` | pass 200 |
| `/api/learn` | FAIL 405 |
| `/api/score` | FAIL 405 |
| `/api/self/evolution/summary` | pass 200 |
| `/api/trading/analytics/dispersion-follow` | pass 200 |
| `/api/trading/analytics/regime-vrp` | pass 200 |
| `/api/trading/analytics/vol-sharpe` | pass 200 |
| `/api/trading/analytics/vrp-attribution` | pass 200 |
| `/api/trading/claim-gate` | pass 200 |
| `/api/trading/cohort-status` | pass 200 |
| `/api/trading/evolution/active` | pass 200 |
| `/api/trading/evolution/apply` | FAIL 405 |
| `/api/trading/evolution/proposals` | pass 200 |
| `/api/trading/evolution/rejection-summary` | SKIP ERR: TimeoutError |
| `/api/trading/evolution/rollback` | FAIL 405 |
| `/api/trading/execution/analysis` | pass 200 |
| `/api/trading/execution/summary` | pass 200 |
| `/api/trading/pre-score` | FAIL 405 |
| `/api/trading/prescore` | FAIL 405 |
| `/api/trading/promotion` | pass 200 |
| `/api/trading/promotion/dashboard` | pass 200 |
| `/api/trading/regime` | pass 200 |
| `/api/trading/regime-status` | pass 200 |
| `/api/trading/regime/current` | pass 200 |
| `/api/trading/regime/detail` | pass 200 |
| `/api/trading/regime/performance` | pass 200 |
| `/api/trading/regime/recommendation` | pass 200 |
| `/api/trading/situation` | pass 200 |
| `/api/trading/situation/abstention` | pass 200 |
| `/api/trading/situation/conditioned-stats` | pass 200 |
| `/api/trading/situation/regime` | pass 200 |
| `/api/trading/situation/regime-rejections` | pass 200 |
| `/api/trading/situation/sharpe-adjustment` | pass 200 |
| `/api/trading/vix-timing` | pass 200 |
| `/api/trading/volatility/dispersion` | pass 200 |
| `/api/trading/volatility/rich-cheap{id}` | FAIL 404 |
| `/api/trading/volatility/sharpe{id}` | FAIL 404 |
| `/api/trading/volatility/tail-bets` | pass 200 |
| `/api/trading/volatility/vrp` | pass 200 |
| `/api/trading/webhook/history` | pass 200 |
| `/api/trajectory` | pass 200 |
| `/api/transfer/execute` | FAIL 405 |
| `/api/transfer/opportunities` | pass 200 |
| `/api/transfer/status` | pass 200 |

### Screenshots
- `docs\screenshots\trading_analysis.png`
- `docs\screenshots\trading_dashboard.png`
- `docs\screenshots\trading_initial.png`
- `docs\screenshots\trading_journal.png`
- `docs\screenshots\trading_log_trade.png`
- `docs\screenshots\trading_performance.png`
- `docs\screenshots\trading_trade_detail.png`

---

## PURCHASING (port 5175/8020)
**Accent:** green | **TSX files:** 64

**Tabs (5):** Dashboard, Order, Analysis, Inventory, Performance

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AnalysisScreen.tsx` | 142 | CategoryAccuracyChart, ContrastCard, CounterfactualCard, DayOfWeekChart, DecisionExplorerPanel +9 |  |
| `DashboardScreen.tsx` | 251 | AccuracyAlertPanel, AEStatusBar, AutoOrderPanel, CommodityPricePanel, EventBadge +9 |  |
| `InventoryScreen.tsx` | 218 | AuditTrailViewer, CategoryEmoji, DeliveryScheduleCard, EventPlannerCard, ItemProfile +4 |  |
| `OrderScreen.tsx` | 665 | AEManagedBadge, CostAnalysis, EngineAssessment, EventBadge, MatchResultPanel +4 |  |
| `PerformanceScreen.tsx` | 174 | AlertDashboardCard, AuditExportPanel, CategoryAccuracyChart, CentroidTimelineChart, ChainTransferCard +10 |  |

### Component Files (57)
- `components\AccuracyAlertPanel.tsx`
- `components\AEManagedBadge.tsx`
- `components\AEStatusBar.tsx`
- `components\AlertDashboardCard.tsx`
- `components\AuditExportPanel.tsx`
- `components\AuditTrailViewer.tsx`
- `components\AutoOrderPanel.tsx`
- `components\CategoryAccuracyChart.tsx`
- `components\CategoryEmoji.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\ChainTransferCard.tsx`
- `components\CohortStatusPanel.tsx`
- `components\CommodityPricePanel.tsx`
- `components\ContrastCard.tsx`
- `components\CostAnalysis.tsx`
- `components\CounterfactualCard.tsx`
- `components\DayOfWeekChart.tsx`
- `components\DecisionExplorerPanel.tsx`
- `components\DeliveryScheduleCard.tsx`
- `components\DiscoveryDigestCard.tsx`
- `components\DisruptionRecoveryPanel.tsx`
- `components\EconomicDashboardCard.tsx`
- `components\EngineAssessment.tsx`
- `components\EventBadge.tsx`
- `components\EventImpactCard.tsx`
- `components\EventPlannerCard.tsx`
- `components\GroupDashboardCard.tsx`
- `components\IgnoringCostCard.tsx`
- `components\IKSTrackerPanel.tsx`
- `components\ItemProfile.tsx`
- ... +27 more

### API Calls Referenced (77)
- `/api/conservation/status`
- `/api/context/analytics`
- `/api/context/items`
- `/api/context/order-metadata`
- `/api/context/similar`
- `/api/context/today-summary`
- `/api/context/weather`
- `/api/dashboard/orders`
- `/api/evolution/history`
- `/api/evolution/promoted`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/history`
- `/api/inventory/summary`
- `/api/learn`
- `/api/purchasing/alerts`
- `/api/purchasing/auto-order/audit`
- `/api/purchasing/auto-order/disable`
- `/api/purchasing/auto-order/enable`
- `/api/purchasing/auto-order/evaluate`
- `/api/purchasing/auto-order/status`
- `/api/purchasing/chain/status`
- `/api/purchasing/chain/transfer`
- `/api/purchasing/chain/validate`
- `/api/purchasing/cohort-status`
- `/api/purchasing/commodity/indices`
- `/api/purchasing/commodity/status`
- `/api/purchasing/competence/ramp`
- `/api/purchasing/day-0-readiness`
- `/api/purchasing/delivery/consolidation`
- `/api/purchasing/delivery/today`
- `/api/purchasing/delivery/week`
- `/api/purchasing/discovery/digest`
- `/api/purchasing/discovery/insights`
- `/api/purchasing/economic/model`
- `/api/purchasing/economic/roi-summary`
- `/api/purchasing/events/history`
- `/api/purchasing/events/plan`
- `/api/purchasing/events/record`
- `/api/purchasing/frozen-twin`
- `/api/purchasing/iks/summary`
- `/api/purchasing/match`
- `/api/purchasing/match/queue`
- `/api/purchasing/menu/alerts`
- `/api/purchasing/menu/analysis`
- `/api/purchasing/menu/summary`
- `/api/purchasing/multi-unit/compare`
- `/api/purchasing/multi-unit/dashboard`
- `/api/purchasing/multi-unit/transfer-opportunities`
- `/api/purchasing/par/predict`
- `/api/purchasing/par/predict-week`
- `/api/purchasing/par/recommendations`
- `/api/purchasing/par/status`
- `/api/purchasing/proof-ledger`
- `/api/purchasing/qbo/bills`
- `/api/purchasing/qbo/status`
- `/api/purchasing/qbo/vendors`
- `/api/purchasing/queue`
- `/api/purchasing/spend/alerts`
- `/api/purchasing/spend/by-category`
- `/api/purchasing/spend/by-supplier`
- `/api/purchasing/spend/cost-per-cover`
- `/api/purchasing/spend/summary`
- `/api/purchasing/suppliers/scorecards`
- `/api/purchasing/trust-weights`
- `/api/purchasing/trust-weights/expected`
- `/api/purchasing/trust-weights/insights`
- `/api/purchasing/verify`
- `/api/purchasing/verify/reason-codes`
- `/api/purchasing/waste/analysis`
- `/api/purchasing/waste/summary`
- `/api/score`
- `/api/self/`
- `/api/self/accuracy-by-category`
- `/api/self/audit-trail`
- `/api/self/decisions`
- `/api/trajectory`

### Endpoint Smoke
**65/77 returned 200**

| Path | Status |
|---|---|
| `/api/conservation/status` | pass 200 |
| `/api/context/analytics` | pass 200 |
| `/api/context/items` | pass 200 |
| `/api/context/order-metadata` | pass 200 |
| `/api/context/similar` | FAIL 422 |
| `/api/context/today-summary` | pass 200 |
| `/api/context/weather` | pass 200 |
| `/api/dashboard/orders` | pass 200 |
| `/api/evolution/history` | pass 200 |
| `/api/evolution/promoted` | pass 200 |
| `/api/evolution/variants` | pass 200 |
| `/api/fingerprint` | pass 200 |
| `/api/history` | pass 200 |
| `/api/inventory/summary` | pass 200 |
| `/api/learn` | FAIL 405 |
| `/api/purchasing/alerts` | pass 200 |
| `/api/purchasing/auto-order/audit` | pass 200 |
| `/api/purchasing/auto-order/disable` | FAIL 405 |
| `/api/purchasing/auto-order/enable` | FAIL 405 |
| `/api/purchasing/auto-order/evaluate` | FAIL 405 |
| `/api/purchasing/auto-order/status` | pass 200 |
| `/api/purchasing/chain/status` | pass 200 |
| `/api/purchasing/chain/transfer` | FAIL 405 |
| `/api/purchasing/chain/validate` | FAIL 405 |
| `/api/purchasing/cohort-status` | pass 200 |
| `/api/purchasing/commodity/indices` | pass 200 |
| `/api/purchasing/commodity/status` | pass 200 |
| `/api/purchasing/competence/ramp` | pass 200 |
| `/api/purchasing/day-0-readiness` | pass 200 |
| `/api/purchasing/delivery/consolidation` | pass 200 |
| `/api/purchasing/delivery/today` | pass 200 |
| `/api/purchasing/delivery/week` | pass 200 |
| `/api/purchasing/discovery/digest` | pass 200 |
| `/api/purchasing/discovery/insights` | pass 200 |
| `/api/purchasing/economic/model` | pass 200 |
| `/api/purchasing/economic/roi-summary` | pass 200 |
| `/api/purchasing/events/history` | pass 200 |
| `/api/purchasing/events/plan` | pass 200 |
| `/api/purchasing/events/record` | FAIL 405 |
| `/api/purchasing/frozen-twin` | pass 200 |
| `/api/purchasing/iks/summary` | pass 200 |
| `/api/purchasing/match` | FAIL 405 |
| `/api/purchasing/match/queue` | pass 200 |
| `/api/purchasing/menu/alerts` | pass 200 |
| `/api/purchasing/menu/analysis` | pass 200 |
| `/api/purchasing/menu/summary` | pass 200 |
| `/api/purchasing/multi-unit/compare` | pass 200 |
| `/api/purchasing/multi-unit/dashboard` | pass 200 |
| `/api/purchasing/multi-unit/transfer-opportunities` | pass 200 |
| `/api/purchasing/par/predict` | pass 200 |
| `/api/purchasing/par/predict-week` | pass 200 |
| `/api/purchasing/par/recommendations` | pass 200 |
| `/api/purchasing/par/status` | pass 200 |
| `/api/purchasing/proof-ledger` | pass 200 |
| `/api/purchasing/qbo/bills` | pass 200 |
| `/api/purchasing/qbo/status` | pass 200 |
| `/api/purchasing/qbo/vendors` | pass 200 |
| `/api/purchasing/queue` | pass 200 |
| `/api/purchasing/spend/alerts` | pass 200 |
| `/api/purchasing/spend/by-category` | pass 200 |
| `/api/purchasing/spend/by-supplier` | pass 200 |
| `/api/purchasing/spend/cost-per-cover` | pass 200 |
| `/api/purchasing/spend/summary` | pass 200 |
| `/api/purchasing/suppliers/scorecards` | pass 200 |
| `/api/purchasing/trust-weights` | pass 200 |
| `/api/purchasing/trust-weights/expected` | pass 200 |
| `/api/purchasing/trust-weights/insights` | pass 200 |
| `/api/purchasing/verify` | FAIL 405 |
| `/api/purchasing/verify/reason-codes` | pass 200 |
| `/api/purchasing/waste/analysis` | pass 200 |
| `/api/purchasing/waste/summary` | pass 200 |
| `/api/score` | FAIL 405 |
| `/api/self/` | FAIL 404 |
| `/api/self/accuracy-by-category` | pass 200 |
| `/api/self/audit-trail` | pass 200 |
| `/api/self/decisions` | pass 200 |
| `/api/trajectory` | pass 200 |

### Screenshots
- `docs\screenshots\purchasing_analysis.png`
- `docs\screenshots\purchasing_dashboard.png`
- `docs\screenshots\purchasing_initial.png`
- `docs\screenshots\purchasing_inventory.png`
- `docs\screenshots\purchasing_order.png`
- `docs\screenshots\purchasing_performance.png`

---

## DATAOPS (port 5176/8030)
**Accent:** purple | **TSX files:** 79

**Tabs (5):** Dashboard, Triage, Insight, Evidence, Curve

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `CurveScreen.tsx` | 91 | CentroidTimelineChart, CentroidTimeline, DisruptionAnnotation |  |
| `DashboardScreen.tsx` | 367 | AEImpactPanel, AccuracyAlertPanel, AlertGroupCard, AlertQueue, ConservationProjection +10 |  |
| `EvidenceScreen.tsx` | 98 | AEImpactPanel, AuditTrailPanel, AuditTrailViewer, AccuracyAlertsPanel, CohortStatusPanel +10 |  |
| `InsightScreen.tsx` | 139 | AcquisitionPanel, AcquisitionAdvisorPanel, BottleneckPanel, CrossGraphInsightCard, CompoundingCurveOverlay +10 |  |
| `TriageScreen.tsx` | 583 | AbstentionBanner, ApplyFixModal, CrossGraphInsightCard, DependencyTree, ProcessSignalsPanel +5 |  |

### Component Files (72)
- `components\AbstentionBanner.tsx`
- `components\AccuracyAlertPanel.tsx`
- `components\AccuracyAlerts.tsx`
- `components\AccuracyAlertsPanel.tsx`
- `components\AcquisitionAdvisorPanel.tsx`
- `components\AcquisitionPanel.tsx`
- `components\ActionPicker.tsx`
- `components\AEImpactPanel.tsx`
- `components\AERecommendationBadge.tsx`
- `components\AgentTrustGatewayPanel.tsx`
- `components\AlertCard.tsx`
- `components\AlertGroupCard.tsx`
- `components\AlertQueue.tsx`
- `components\ApplyFixModal.tsx`
- `components\AuditTrailPanel.tsx`
- `components\AuditTrailViewer.tsx`
- `components\BottleneckPanel.tsx`
- `components\CelonisBadge.tsx`
- `components\CentroidTimeline.tsx`
- `components\CentroidTimelineChart.tsx`
- `components\CentroidTimelinePanel.tsx`
- `components\CohortStatusPanel.tsx`
- `components\CompoundingCurveOverlay.tsx`
- `components\ConservationProjection.tsx`
- `components\ConservationTimeline.tsx`
- `components\CrossGraphInsightCard.tsx`
- `components\CrossSystemPanel.tsx`
- `components\DataOpsGovernancePanel.tsx`
- `components\DataProductsCard.tsx`
- `components\DecisionExplorer.tsx`
- ... +42 more

### API Calls Referenced (46)
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
- `/api/dataops/cohort-status`
- `/api/dataops/frozen-twin/freeze`
- `/api/dataops/frozen-twin/status`
- `/api/dataops/holdout/register`
- `/api/dataops/holdout/status`
- `/api/dataops/holdout/verify`
- `/api/dataops/intelligence/source-trust`
- `/api/dataops/promotion`
- `/api/dataops/trust`
- `/api/dataops/trust/perturb`
- `/api/dataops/trust/reset`
- `/api/di/acquisition-advice`
- `/api/di/intelligence-map`
- `/api/di/perturb`
- `/api/di/perturb/revert`
- `/api/di/perturb/status`
- `/api/di/products`
- `/api/di/profiles`
- `/api/di/query`
- `/api/di/sources`
- `/api/di/trust/verify`
- `/api/discovery/cross-system`
- `/api/evolution/history`
- `/api/evolution/promoted`
- `/api/evolution/variants`
- `/api/fingerprint`
- `/api/learn`
- `/api/score`
- `/api/self/diagnostics`
- `/api/trajectory`

### Endpoint Smoke
**33/46 returned 200**

| Path | Status |
|---|---|
| `/api/ae/conservation-history` | pass 200 |
| `/api/ae/impact` | pass 200 |
| `/api/ae/incident` | pass 200 |
| `/api/ae/operational-rules` | pass 200 |
| `/api/ae/pattern-origin` | pass 200 |
| `/api/ae/transfer-status` | pass 200 |
| `/api/conservation/status` | pass 200 |
| `/api/conservation/what-if` | FAIL 405 |
| `/api/context/accuracy-by-category` | pass 200 |
| `/api/context/alert-groups` | pass 200 |
| `/api/context/alert-metadata` | pass 200 |
| `/api/context/alerts` | pass 200 |
| `/api/context/apply-fix` | FAIL 405 |
| `/api/context/celonis/process-data` | pass 200 |
| `/api/context/enterprise-health` | pass 200 |
| `/api/context/pipelines` | pass 200 |
| `/api/dataops/cohort-status` | pass 200 |
| `/api/dataops/frozen-twin/freeze` | FAIL 405 |
| `/api/dataops/frozen-twin/status` | pass 200 |
| `/api/dataops/holdout/register` | FAIL 405 |
| `/api/dataops/holdout/status` | pass 200 |
| `/api/dataops/holdout/verify` | FAIL 405 |
| `/api/dataops/intelligence/source-trust` | pass 200 |
| `/api/dataops/promotion` | FAIL 405 |
| `/api/dataops/trust` | pass 200 |
| `/api/dataops/trust/perturb` | FAIL 405 |
| `/api/dataops/trust/reset` | FAIL 405 |
| `/api/di/acquisition-advice` | pass 200 |
| `/api/di/intelligence-map` | pass 200 |
| `/api/di/perturb` | FAIL 405 |
| `/api/di/perturb/revert` | FAIL 405 |
| `/api/di/perturb/status` | pass 200 |
| `/api/di/products` | pass 200 |
| `/api/di/profiles` | pass 200 |
| `/api/di/query` | FAIL 405 |
| `/api/di/sources` | pass 200 |
| `/api/di/trust/verify` | pass 200 |
| `/api/discovery/cross-system` | pass 200 |
| `/api/evolution/history` | pass 200 |
| `/api/evolution/promoted` | pass 200 |
| `/api/evolution/variants` | pass 200 |
| `/api/fingerprint` | pass 200 |
| `/api/learn` | FAIL 405 |
| `/api/score` | FAIL 405 |
| `/api/self/diagnostics` | pass 200 |
| `/api/trajectory` | pass 200 |

### Screenshots
- `docs\screenshots\dataops_curve.png`
- `docs\screenshots\dataops_dashboard.png`
- `docs\screenshots\dataops_evidence.png`
- `docs\screenshots\dataops_initial.png`
- `docs\screenshots\dataops_insight.png`
- `docs\screenshots\dataops_triage.png`

---

## S2P (port 5177/8002)
**Accent:** amber | **TSX files:** 65

**Tabs (6):** Dashboard, Exception Triage, Insight, Evidence, Suppliers, Performance

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `DashboardScreen.tsx` | 157 | AutoApprovePanel, ConservationMiniGauge, ControlTowerPanel, DisruptionSimPanel, FinancialImpactCard +3 |  |
| `EvidenceScreen.tsx` | 87 | AuditTrailPanel, AuditExportPanel, CompliancePanel, ComplianceScreeningPanel, CohortStatusPanel +7 |  |
| `InsightScreen.tsx` | 107 | CentroidExplorerPanel, CrossGraphInsightCard, DiscoveryExtendedPanel, EarlyWarningPanel, FactorFingerprintPanel +6 |  |
| `PerformanceScreen.tsx` | 54 | ConservationMiniGauge, AuthorityPanel, CycleTimePanel, FinancialImpactTrendPanel, OperationalSummary +4 |  |
| `SuppliersScreen.tsx` | 526 | ClusteringPanel, PaymentStrategyPanel, RationalizationPanel, SupplierHeatmap |  |
| `TriageScreen.tsx` | 562 | CentroidExplorer, CounterfactualCard, EvidenceTemplatePanel, NoveltyAlertBanner, ProvenanceBadge +5 |  |

### Component Files (57)
- `components\AuditExportPanel.tsx`
- `components\AuditTrailPanel.tsx`
- `components\AuthorityPanel.tsx`
- `components\AutoApprovePanel.tsx`
- `components\CentroidExplorer.tsx`
- `components\CentroidExplorerPanel.tsx`
- `components\ClusteringPanel.tsx`
- `components\CohortStatusPanel.tsx`
- `components\CompliancePanel.tsx`
- `components\ComplianceScreeningPanel.tsx`
- `components\ConfidenceBandPanel.tsx`
- `components\ConservationMiniGauge.tsx`
- `components\ControlTowerPanel.tsx`
- `components\CounterfactualCard.tsx`
- `components\CrossGraphInsightCard.tsx`
- `components\CycleTimePanel.tsx`
- `components\DayZeroReadinessPanel.tsx`
- `components\DiscoveryExtendedPanel.tsx`
- `components\DiscoveryPanel.tsx`
- `components\DisruptionRecoveryPanel.tsx`
- `components\DisruptionSimPanel.tsx`
- `components\EarlyWarningPanel.tsx`
- `components\EvidenceTemplatePanel.tsx`
- `components\EvolutionPanel.tsx`
- `components\ExceptionExtinctionTimeline.tsx`
- `components\FactorFingerprintPanel.tsx`
- `components\FactorInsightPanel.tsx`
- `components\FactorRadar.tsx`
- `components\FinancialImpactCard.tsx`
- `components\FinancialImpactTrendPanel.tsx`
- ... +27 more

### API Calls Referenced (56)
- `/api/conservation/status`
- `/api/learn`
- `/api/s2p/auto-approve/expansion-proof{id}`
- `/api/s2p/auto-approve/stats`
- `/api/s2p/centroid/all`
- `/api/s2p/cohort-status`
- `/api/s2p/confidence/thresholds`
- `/api/s2p/control-tower/classify{id}`
- `/api/s2p/control-tower/intents`
- `/api/s2p/discovery/alerts`
- `/api/s2p/discovery/disruptions`
- `/api/s2p/discovery/extended`
- `/api/s2p/enterprise/process-fusion`
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
- `/api/s2p/factors/analysis`
- `/api/s2p/factors/propose`
- `/api/s2p/factors/recommendations`
- `/api/s2p/financial-impact`
- `/api/s2p/financial-impact/trend`
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
- `/api/s2p/promotion/status`
- `/api/s2p/pvg/cycle-time`
- `/api/s2p/pvg/leakage`
- `/api/s2p/pvg/variants`
- `/api/s2p/score`
- `/api/s2p/score/counterfactual`
- `/api/s2p/simulation/impact-summary`
- `/api/s2p/simulation/scenarios`
- `/api/s2p/suppliers`
- `/api/s2p/suppliers/clustering`
- `/api/s2p/suppliers/clusters`
- `/api/s2p/suppliers/declining`
- `/api/s2p/suppliers/early-warnings`
- `/api/s2p/suppliers/payment-strategy`
- `/api/s2p/twin/drift`
- `/api/s2p/twin/status`

### Endpoint Smoke
**44/56 returned 200**

| Path | Status |
|---|---|
| `/api/conservation/status` | pass 200 |
| `/api/learn` | FAIL 405 |
| `/api/s2p/auto-approve/expansion-proof{id}` | FAIL 404 |
| `/api/s2p/auto-approve/stats` | pass 200 |
| `/api/s2p/centroid/all` | pass 200 |
| `/api/s2p/cohort-status` | pass 200 |
| `/api/s2p/confidence/thresholds` | pass 200 |
| `/api/s2p/control-tower/classify{id}` | FAIL 404 |
| `/api/s2p/control-tower/intents` | pass 200 |
| `/api/s2p/discovery/alerts` | pass 200 |
| `/api/s2p/discovery/disruptions` | pass 200 |
| `/api/s2p/discovery/extended` | pass 200 |
| `/api/s2p/enterprise/process-fusion` | FAIL 405 |
| `/api/s2p/evidence/audit-pack` | pass 200 |
| `/api/s2p/evidence/chain-integrity` | pass 200 |
| `/api/s2p/evidence/compliance` | pass 200 |
| `/api/s2p/evidence/rules` | pass 200 |
| `/api/s2p/evolution/promoted` | pass 200 |
| `/api/s2p/evolution/promotion-check` | SKIP ERR: TimeoutError |
| `/api/s2p/evolution/reset` | FAIL 405 |
| `/api/s2p/evolution/rules` | pass 200 |
| `/api/s2p/evolution/shadow-results` | pass 200 |
| `/api/s2p/evolution/variants` | pass 200 |
| `/api/s2p/explorer/dk-weights` | pass 200 |
| `/api/s2p/factors/analysis` | pass 200 |
| `/api/s2p/factors/propose` | FAIL 405 |
| `/api/s2p/factors/recommendations` | pass 200 |
| `/api/s2p/financial-impact` | pass 200 |
| `/api/s2p/financial-impact/trend` | pass 200 |
| `/api/s2p/governance/compliance-screening` | pass 200 |
| `/api/s2p/governance/rationalization` | pass 200 |
| `/api/s2p/insight/cross-graph` | pass 200 |
| `/api/s2p/insight/process-signals{id}` | FAIL 404 |
| `/api/s2p/novelty/status` | pass 200 |
| `/api/s2p/outcome` | FAIL 405 |
| `/api/s2p/performance/summary` | pass 200 |
| `/api/s2p/performance/trajectory` | pass 200 |
| `/api/s2p/preview/conservation` | pass 200 |
| `/api/s2p/preview/queue` | pass 200 |
| `/api/s2p/preview/suppliers` | pass 200 |
| `/api/s2p/promotion/status` | pass 200 |
| `/api/s2p/pvg/cycle-time` | pass 200 |
| `/api/s2p/pvg/leakage` | pass 200 |
| `/api/s2p/pvg/variants` | pass 200 |
| `/api/s2p/score` | FAIL 405 |
| `/api/s2p/score/counterfactual` | FAIL 405 |
| `/api/s2p/simulation/impact-summary` | pass 200 |
| `/api/s2p/simulation/scenarios` | pass 200 |
| `/api/s2p/suppliers` | pass 200 |
| `/api/s2p/suppliers/clustering` | pass 200 |
| `/api/s2p/suppliers/clusters` | pass 200 |
| `/api/s2p/suppliers/declining` | pass 200 |
| `/api/s2p/suppliers/early-warnings` | pass 200 |
| `/api/s2p/suppliers/payment-strategy` | pass 200 |
| `/api/s2p/twin/drift` | FAIL 409 |
| `/api/s2p/twin/status` | pass 200 |

### Screenshots
- `docs\screenshots\s2p_dashboard.png`
- `docs\screenshots\s2p_evidence.png`
- `docs\screenshots\s2p_exception_triage.png`
- `docs\screenshots\s2p_initial.png`
- `docs\screenshots\s2p_insight.png`
- `docs\screenshots\s2p_performance.png`
- `docs\screenshots\s2p_suppliers.png`

---

## SOC (port 5173/8001)
**Accent:** blue | **TSX files:** 43

**Tabs (7):** SOC Analytics, Runtime Evolution, Alert Triage, Compounding, Executive Narrative, S2P Preview, Evidence Room

### Screens
| File | Lines | Components | API Calls |
|---|---:|---|---|
| `AlertTriageTab.tsx` | 1763 |  |  |
| `CompoundingTab.tsx` | 3014 |  |  |
| `ExecutiveNarrativeTab.tsx` | 856 |  |  |
| `GovernanceTab.tsx` | 972 |  | /api/governance/summary, /api/platform/rl-exploration-demo, /api/platform/rl-reward-demo +2 |
| `RuntimeEvolutionTab.tsx` | 3895 |  |  |
| `S2PPreviewTab.tsx` | 772 |  | /api/s2p/preview/conservation, /api/s2p/preview/queue, /api/s2p/preview/suppliers |
| `SOCAnalyticsTab.tsx` | 1298 |  |  |

### Component Files (41)
- `components\AutonomyLadderPanel.tsx`
- `components\CampaignIntelligencePanel.tsx`
- `components\CampaignTimelinePanel.tsx`
- `components\CelonisBadge.tsx`
- `components\ClusterHistoryPanel.tsx`
- `components\CohortStatusPanel.tsx`
- `components\CompliancePanel.tsx`
- `components\ContinuityPanel.tsx`
- `components\CoverageAtSafetyBarPanel.tsx`
- `components\DayZeroReadinessPanel.tsx`
- `components\discovery\DiscoveryBanner.tsx`
- `components\DisruptionSimPanel.tsx`
- `components\DomainApplicabilityPanel.tsx`
- `components\FactorContributionPanel.tsx`
- `components\FinancialImpactPanel.tsx`
- `components\InvestigationPanel.tsx`
- `components\LearningControlRoom.tsx`
- `components\LearningStatePanel.tsx`
- `components\NoPrecedentSidebar.tsx`
- `components\NoveltyPanel.tsx`
- `components\OutcomeFeedback.tsx`
- `components\PolicyConflict.tsx`
- `components\ProcessFusionPanel.tsx`
- `components\ProcessTimelinePanel.tsx`
- `components\PromotionRejectionTable.tsx`
- `components\ProvenanceBadge.tsx`
- `components\RejectionMomentPanel.tsx`
- `components\ROICalculator.tsx`
- `components\SAPDataBadge.tsx`
- `components\SimulationPanel.tsx`
- ... +11 more

### API Calls Referenced (14)
- `/api/compounding/channel-decomposition`
- `/api/enterprise/process-timeline`
- `/api/governance/summary`
- `/api/platform/domain-applicability`
- `/api/platform/rl-exploration-demo`
- `/api/platform/rl-reward-demo`
- `/api/s2p/preview/conservation`
- `/api/s2p/preview/queue`
- `/api/s2p/preview/suppliers`
- `/api/soc/campaign-timeline`
- `/api/soc/campaigns`
- `/api/soc/compliance`
- `/api/soc/evidence-room`
- `/api/soc/factor-contribution`

### Endpoint Smoke
**9/14 returned 200**

| Path | Status |
|---|---|
| `/api/compounding/channel-decomposition` | pass 200 |
| `/api/enterprise/process-timeline` | pass 200 |
| `/api/governance/summary` | pass 200 |
| `/api/platform/domain-applicability` | pass 200 |
| `/api/platform/rl-exploration-demo` | FAIL 404 |
| `/api/platform/rl-reward-demo` | FAIL 404 |
| `/api/s2p/preview/conservation` | FAIL 404 |
| `/api/s2p/preview/queue` | FAIL 404 |
| `/api/s2p/preview/suppliers` | FAIL 404 |
| `/api/soc/campaign-timeline` | pass 200 |
| `/api/soc/campaigns` | pass 200 |
| `/api/soc/compliance` | pass 200 |
| `/api/soc/evidence-room` | pass 200 |
| `/api/soc/factor-contribution` | pass 200 |

### Screenshots
- `docs\screenshots\soc_alert_triage.png`
- `docs\screenshots\soc_compounding.png`
- `docs\screenshots\soc_evidence_room.png`
- `docs\screenshots\soc_executive_narrative.png`
- `docs\screenshots\soc_initial.png`
- `docs\screenshots\soc_runtime_evolution.png`
- `docs\screenshots\soc_s2p_preview.png`
- `docs\screenshots\soc_soc_analytics.png`

---
