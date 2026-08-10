# SDK Copilot Tab Deep Analysis

**Diagnostic date:** 2026-08-10  
**Scope:** `copilot-sdk` Trading, Purchasing, and DataOps frontends only.  
**Method:** Read-only source inspection plus attempted live endpoint verification.  
**Live-verification result:** ports `8010`, `8020`, and `8030` refused connections during this run. Therefore endpoint statuses below distinguish **route wired in source** from **live response not verified**. No endpoint is marked live-healthy without a successful request.

## Executive findings

The three applications have complete tab shells and extensive component mounting. The main gaps are data/readiness gaps rather than absent screen structure:

- Trading has the richest surface area. Most panels are wired to API helpers, but the TRD-S7 re-convergence curve is explicitly illustrative and pending an experiment result (`apps/trading/frontend/src/components/ReConvergencePanel.tsx:93-108`). Several volatility panels intentionally render “awaiting enough decisions” states when the fixture lacks depth.
- Purchasing has all five tabs and a broad operational surface. Its write actions (order confirmation, verification, auto-order, chain transfer) are present in the UI, but require live endpoint verification and should be tested as side-effecting flows separately.
- DataOps has all five tabs and the strongest cross-graph/data-intelligence coverage. The dashboard includes the ENT-1 value card and DI controls, while Insight contains the Intelligence Map and acquisition path. The app itself warns when the graph source is fixture data (`apps/dataops/frontend/src/App.tsx:82-92`).
- The demo document says the core Trading, Purchasing, and DataOps catalogs are largely ready (`demo_scenarios_and_usecases_v2_4.md:304-327`), but it also records known frontend qualification gaps for DI-GOLD and DI-PRODUCT (`demo_scenarios_and_usecases_v2_4.md:896-901`). Current source contains those surfaces; live data could not be confirmed in this run.

## Live verification record

| Copilot | Frontend | Backend | Attempted result |
|---|---:|---:|---|
| Trading | 5174 | 8010 | `ConnectionRefusedError` for `/openapi.json`; no live endpoint calls possible |
| Purchasing | 5175 | 8020 | `ConnectionRefusedError` for `/openapi.json`; no live endpoint calls possible |
| DataOps | 5176 | 8030 | `ConnectionRefusedError` for `/openapi.json`; no live endpoint calls possible |

The endpoint tables therefore use these classifications:

- **WIRED / live unverified:** frontend calls a named helper or path, and the helper is present in the app API module. The route still needs a healthy service to prove it returns data.
- **STUB:** mounted UI explicitly identifies itself as illustrative, pending, awaiting evidence, or empty by design.
- **MISSING:** a requested/demo surface has no mounted implementation found in the inspected screen.

## Trading — screen and tab inventory

The shell defines six navigable tabs: Dashboard, Log Trade, Analysis, Performance, Journal, and Trade Detail (`apps/trading/frontend/src/App.tsx:12-20`). Routing/mounting is conditional in the same file (`apps/trading/frontend/src/App.tsx:67-82`). The application also loads the trajectory at startup to populate IKS (`apps/trading/frontend/src/App.tsx:28-48`).

### Trading — Dashboard

Source: `apps/trading/frontend/src/screens/DashboardScreen.tsx`.

#### Components mounted

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `TransferBadge` | `DashboardScreen.tsx:219` | `/api/transfer/status` through shared transfer badge | WIRED / live unverified | Cross-copilot transfer |
| `ArchetypeSelector` | `DashboardScreen.tsx:239` | archetype helpers in `api.ts:870-885` | WIRED / live unverified | Trader personalization |
| `DayZeroCard` | `DashboardScreen.tsx:240` | shared honesty/measurement props | WIRED | Day-zero honesty |
| `ProvenanceBadge` | `DashboardScreen.tsx:244` | local source/provenance props | WIRED | Grounded proof |
| `MarketContext` | `DashboardScreen.tsx:246` | dashboard market state from `getMarketSnapshot` | WIRED / live unverified | Market context |
| `TickerPanel` | `DashboardScreen.tsx:247` | `getTicker` calls from `DashboardScreen.tsx:115`; helper `api.ts:895` | WIRED / live unverified | Trading context |
| `RegimePanel` | `DashboardScreen.tsx:248` | situation/regime helpers; details below | WIRED / live unverified | TRD-S3 |
| `PortfolioSummary` | `DashboardScreen.tsx:249` | `getAnalytics` state | WIRED / live unverified | Portfolio mirror |
| `PatternBadge` | `DashboardScreen.tsx:250` | `getPatterns`, `api.ts:953` | WIRED / live unverified | Pattern signal |
| `AccuracyByCategory` | `DashboardScreen.tsx:251` | `fetchAccuracyByCategory`, `api.ts:916` | WIRED / live unverified | Accuracy/provenance |
| `PortfolioConcentration` | `DashboardScreen.tsx:254` | analytics props | WIRED | Risk view |
| `ThesisBreakdown` | `DashboardScreen.tsx:258` | analytics props | WIRED | Thesis analysis |
| `CalendarHeatmap` | `DashboardScreen.tsx:278` | analytics/calendar state | WIRED / live unverified | Journal history |
| `DecisionHistory` | `DashboardScreen.tsx:280` | history state from `getHistory`, `api.ts:521` | WIRED / live unverified | Decision trace |
| `TradeCard` | `DashboardScreen.tsx:286-288` | joined history; click selects a trade | WIRED | Drill-down |
| `DataTrustBadge` | `DashboardScreen.tsx:293` | shared `/api/fingerprint` call | WIRED / live unverified | Trust/provenance |

Dashboard data loading is a `Promise.all` over analytics, history, metadata, and market snapshot (`DashboardScreen.tsx:100-120`, `DashboardScreen.tsx:173-178`). A trade card click calls `onSelectTrade` and moves to Trade Detail through the app shell (`DashboardScreen.tsx:286-288`; `App.tsx:50-53`). “Log Trade” and “scroll to archetypes” buttons are at `DashboardScreen.tsx:222` and `DashboardScreen.tsx:233`.

#### Clickable items

| Element | Handler | Action | Working? |
|---|---|---|---|
| Log Trade button | `DashboardScreen.tsx:222` | switches shell to `log` via parent callback | YES in source |
| Archetype call-to-action | `DashboardScreen.tsx:233` | scrolls to `archetype-select` | YES in source |
| Ticker panel selection | `DashboardScreen.tsx:247` | updates open ticker metadata | YES in source |
| Trade card | `DashboardScreen.tsx:286-288` | opens Trade Detail | YES in source |
| Shell tabs | `App.tsx:56-62` | changes active tab | YES in source |

### Trading — Log Trade

Source: `apps/trading/frontend/src/screens/LogTradeScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `TickerLookup` | `LogTradeScreen.tsx:319-322` | `getTicker`, helper `api.ts:895` | WIRED / live unverified |
| `OptionsFactorPanel` | `LogTradeScreen.tsx:325` | local form context | WIRED |
| `Select` direction/category/thesis/timeframe | `LogTradeScreen.tsx:330-333` | local form state | WIRED |
| `ResearchChecklist` | `LogTradeScreen.tsx:359` | local form state | WIRED |
| `PositionSizer` | `LogTradeScreen.tsx:360` | local form state | WIRED |
| `PreScorePanel` | `LogTradeScreen.tsx:386` | `/api/trading/pre-score` and `/api/trading/prescore`, `api.ts:477-518` | WIRED / live unverified |
| `EngineAssessment` | `LogTradeScreen.tsx:405` | scored/fingerprint/analytics props | WIRED |
| `SimilarTradesPanel` | `LogTradeScreen.tsx:406` | `getSimilarTrades`, `api.ts:985` | WIRED / live unverified |
| `ScoreResultCard` | `LogTradeScreen.tsx:407-410` | `scoreTrade` `/api/score`, `learnTrade` `/api/learn`, `api.ts:957-972` | WIRED / live unverified |
| `EvidencePanel` | `LogTradeScreen.tsx:414` | `/api/trading/evidence/{id}`, `api.ts:146` | WIRED / live unverified |
| `ReasoningPanel` | `LogTradeScreen.tsx:415-426` | score result props | WIRED |

The initial form context loads market snapshot, fingerprint, and analytics (`LogTradeScreen.tsx:152-172`). Scoring assembles current regime context (`LogTradeScreen.tsx:216-233`), calls the score path (`LogTradeScreen.tsx:227-233`), then loads similar trades (`LogTradeScreen.tsx:268`) and learns on confirmation (`LogTradeScreen.tsx:293`). Direction, category, thesis, timeframe, signal alignment, entry price, checklist, sizing, factor fields, and score confirmation/override are all interactive (`LogTradeScreen.tsx:321-410`). Evidence is conditional on a returned decision id and readiness (`LogTradeScreen.tsx:414`).

### Trading — Analysis

Source: `apps/trading/frontend/src/screens/AnalysisScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `TrustRadarPanel` | `AnalysisScreen.tsx:108` | `/api/context/trust-analysis`, `api.ts:949` | WIRED / live unverified | V1 cold mirror |
| `RegimePanel` | `AnalysisScreen.tsx:109` | regime and situation endpoints | WIRED / live unverified | TRD-S3 |
| `VolatilityPanel` | `AnalysisScreen.tsx:110` | situation Sharpe adjustment | WIRED / live unverified | TRD-V1 |
| `PatternDetectionPanel` | `AnalysisScreen.tsx:111` | `/api/context/patterns`, `api.ts:953` | WIRED / live unverified | Pattern mirror |
| `ContrastCard` | `AnalysisScreen.tsx:112` | analytics props | WIRED |
| `ProfileArchetype` | `AnalysisScreen.tsx:113` | fingerprint props | WIRED |
| `FingerprintPanel` | `AnalysisScreen.tsx:114-118` | shared fingerprint data | WIRED / live unverified | V1 |
| `DecisionExplorer` | `AnalysisScreen.tsx:121` | `/api/self/decisions`, `api.ts:921` | WIRED / live unverified | Evidence exploration |
| `VolSharpeCard` | `AnalysisScreen.tsx:123` | `/api/trading/analytics/vol-sharpe`, `api.ts:346` | WIRED / live unverified | TRD-V1 |
| `VRPAttributionCard` | `AnalysisScreen.tsx:124` | `/api/trading/analytics/vrp-attribution`, `api.ts:350` | WIRED / live unverified | VRP attribution |
| `RegimeVRPCard` | `AnalysisScreen.tsx:125` | `/api/trading/analytics/regime-vrp`, `api.ts:354` | WIRED / live unverified; may be empty | TRD-V5 |
| `DispersionFollowCard` | `AnalysisScreen.tsx:126` | `/api/trading/analytics/dispersion-follow`, `api.ts:378` | WIRED / live unverified; depth-gated | TRD-V6 |
| `TailBetsCard` | `AnalysisScreen.tsx:127` | correlation/tail data through `fetchCorrelation`, `api.ts:341` | WIRED / live unverified; depth-gated | TRD-V7 |
| `CorrelationPanel` | `AnalysisScreen.tsx:129` | `/api/trading/correlation`, `api.ts:341` | WIRED / live unverified |
| `CounterfactualCard` | `AnalysisScreen.tsx:130` | default and perturbation calls; component `CounterfactualCard.tsx:43-75` | WIRED / live unverified | V4 |
| `DayOfWeekChart` | `AnalysisScreen.tsx:131` | analytics props | WIRED |
| `ResearchImpactChart` | `AnalysisScreen.tsx:132` | analytics props | WIRED |
| `RegimeChart` | `AnalysisScreen.tsx:133` | analytics props | WIRED |
| `RiskManagementCard` | `AnalysisScreen.tsx:134` | analytics props | WIRED |
| `RuleGenealogyTree` | `AnalysisScreen.tsx:135` | evolution variants/history | WIRED / live unverified |
| `RuleLifecyclePanel` | `AnalysisScreen.tsx:136` | evolution history/variants/promoted rules | WIRED / live unverified |

The screen itself loads analytics and fingerprint (`AnalysisScreen.tsx:63-72`) and has loading/error conditional states (`AnalysisScreen.tsx:74-97`). The principal user controls are inside `TrustRadarPanel` category selection (`TrustRadarPanel.tsx:167`) and `DecisionExplorer` category/verified filters (`DecisionExplorer.tsx:57-67`), plus counterfactual slider/rescore/sample controls (`CounterfactualCard.tsx:118-132`).

### Trading — Performance

Source: `apps/trading/frontend/src/screens/PerformanceScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `TrajectoryChart` | `PerformanceScreen.tsx:112` | `/api/trajectory`, `api.ts:899` | WIRED / live unverified | Compounding |
| `CentroidTimeline` | `PerformanceScreen.tsx:121` | centroid history helper | WIRED / live unverified | Learning timeline |
| `ReConvergencePanel` | `PerformanceScreen.tsx:122` | centroid history + situation regime, `ReConvergencePanel.tsx:2,25` | STUB for proof curve | TRD-S7 |
| `AuditTrail` | `PerformanceScreen.tsx:123` | `/api/self/audit-trail`, `api.ts:937` | WIRED / live unverified | Evidence |
| `ConservationProjection` | `PerformanceScreen.tsx:124` | conservation/trajectory props | WIRED |
| `RegimeStatusPanel` | `PerformanceScreen.tsx:125` | `/api/trading/regime-status`, `api.ts:225` | WIRED / live unverified | TRD-S3 |
| `RegimeAnalyticsPanel` | `PerformanceScreen.tsx:126` | `/api/trading/regime-analytics`, component `RegimeAnalyticsPanel.tsx:73` | WIRED / live unverified | TRD-S1/S2 |
| `StrategySafetyBreakdownPanel` | `PerformanceScreen.tsx:127` | conservation breakdown | WIRED / live unverified |
| `PromotionDashboard` | `PerformanceScreen.tsx:128` | promotion dashboard, `api.ts:324-336` | WIRED / live unverified | Governance |
| `RejectionMomentPanel` | `PerformanceScreen.tsx:129` | evolution summary + rejection summary, component `RejectionMomentPanel.tsx:26` | WIRED / live unverified; empty state possible | V2/E3 |
| `TransferPanel` | `PerformanceScreen.tsx:130` | transfer opportunities/status/execute, `api.ts:819-827` | WIRED / live unverified |
| `EvolutionPanel` | `PerformanceScreen.tsx:131` | evolution log/active variant | WIRED / live unverified |
| `EvolutionControlsPanel` | `PerformanceScreen.tsx:132` | apply/rollback proposal controls, `EvolutionControlsPanel.tsx:137-185` | WIRED / live unverified |
| `ExecutionQualityCard` | `PerformanceScreen.tsx:133` | execution analysis | WIRED / live unverified |
| `WebhookStatusCard` | `PerformanceScreen.tsx:134` | webhook history/status | WIRED / live unverified |
| `CohortStatusPanel` | `PerformanceScreen.tsx:135` | cohort status | WIRED / live unverified |
| `VIXTimingPanel` | `PerformanceScreen.tsx:136` | VIX timing | WIRED / live unverified |
| `RollingMetrics` | `PerformanceScreen.tsx:137` | analytics props | WIRED |
| `CategoryPerformance` | `PerformanceScreen.tsx:138` | analytics props | WIRED |
| `RiskManagementCard` | `PerformanceScreen.tsx:139` | analytics props | WIRED |

Performance loads analytics, trajectory, and conservation (`PerformanceScreen.tsx:44-66`). ReConvergence is the clear honesty gap: it renders an SVG labelled “Illustrative ARCH curves — experiment pending” (`ReConvergencePanel.tsx:93-108`), so TRD-S7 is a mounted visual placeholder rather than measured evidence. Rejection and promotion panels are structurally wired but render explicit empty states until evolution events exist (`RejectionMomentPanel.tsx:70-90`).

### Trading — Journal

Source: `apps/trading/frontend/src/screens/JournalScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `JournalQueryBar` | `JournalScreen.tsx:191` | journal query POST in `JournalQueryBar.tsx:49` | WIRED / live unverified |
| `AggregateCards` | `JournalScreen.tsx:203` | `fetchAnalytics` | WIRED / live unverified |
| `EarningsInsightCard` | `JournalScreen.tsx:204` | subcategory analytics props | WIRED; empty event state possible |
| `EventDrivenSubcategorySplit` | `JournalScreen.tsx:263` | subcategory analytics | WIRED |
| `TradeDetailPanel` | `JournalScreen.tsx:272` | selected trade data | WIRED |
| `EvidencePanel` | `JournalScreen.tsx:273` | `/api/trading/evidence/{id}` | WIRED / live unverified |
| `OptionsFactorPanel` | `JournalScreen.tsx:364` | selected trade options metadata | WIRED |

The screen loads trades, category analytics, and subcategory analytics (`JournalScreen.tsx:58-67`), then loads selected trade detail (`JournalScreen.tsx:89-113`). Filters for ticker, category, strategy tag, outcome, and limit are interactive at `JournalScreen.tsx:136-185`; selecting a row opens the detail panel at `JournalScreen.tsx:231`.

### Trading — Trade Detail

Source: `apps/trading/frontend/src/screens/TradeDetailScreen.tsx`. This is a shell tab and a drill-down destination, not a standalone scoring workflow.

| Component/element | Source line | API/data path | Classification |
|---|---:|---|---|
| `EmptyState` (no selection) | `TradeDetailScreen.tsx:135` | none | WIRED empty state |
| Back button | `TradeDetailScreen.tsx:145` | parent `onBack` | WIRED |
| `EmptyState` (missing trade) | `TradeDetailScreen.tsx:155` | none | WIRED empty state |
| Factor bars | `TradeDetailScreen.tsx:224` | selected history/metadata | WIRED |
| Back buttons | `TradeDetailScreen.tsx:165,235` | parent `onBack` | WIRED |

Data loading is `getHistory`, `getTradeMetadata`, and conditional `getTicker` (`TradeDetailScreen.tsx:90-106`; helpers `api.ts:521,887,895`).

### Trading API surface

The API module centralizes GET/POST transport (`apps/trading/frontend/src/api.ts:66-92`). The screen/component call graph includes:

| Functional group | Helper/path evidence | Status |
|---|---|---|
| Core score/learn | `api.ts:957-976` → `/api/score`, `/api/learn`, metadata save | WIRED / live unverified |
| Core context | `api.ts:887-899` → trade metadata, market snapshot, ticker, trajectory | WIRED / live unverified |
| Trust/fingerprint | `api.ts:945-953` → fingerprint, trust analysis, patterns | WIRED / live unverified |
| Learning/conservation | `api.ts:903-937` → conservation, breakdown, centroid history, accuracy, decisions, audit | WIRED / live unverified |
| Regime/situation | `api.ts:150-225,346-382` | WIRED / live unverified |
| Evolution/promotion | `api.ts:636-738` | WIRED / live unverified |
| Transfer | `api.ts:819-827` | WIRED / live unverified |
| Journal/evidence | `api.ts:124-147` plus `JournalQueryBar.tsx:49` | WIRED / live unverified |
| Counterfactual | `CounterfactualCard.tsx:43-75` | WIRED / live unverified |

The requested user-facing routes `/api/trading/situation/*`, `/api/trading/regime*`, and `/api/trading/analytics/*` are also represented by backend route modules (`apps/trading/backend/app/routers/situation_router.py:32,67`; `regime.py:41,58`; `regime_analytics.py:27,32`; `regime_status.py:16`; `analytics.py:102`). Their live response data could not be checked because port 8010 was down.

### Trading gaps

- TRD-S7 is **STUB**, not measured: the panel labels its curves illustrative and says the experiment is pending (`ReConvergencePanel.tsx:93-108`). This directly affects the demo requirement for a cold-start versus regime-indexed convergence curve (`demo_scenarios_and_usecases_v2_4.md:486-497`).
- V2/Rejection Moment is mounted and API-wired, but an empty fixture produces “No rejected variants yet”/“No promoted variants yet” (`RejectionMomentPanel.tsx:70-90`); demo counts are not proven in this environment.
- Several TRD-V panels are depth-gated by “awaiting more decisions” copy (`RegimeVRPCard.tsx:55-58`, `DispersionFollowCard.tsx:57`, `VRPAttributionCard.tsx:91`, `TailBetsCard.tsx:51,81`). These are intentional measurement states, but they are not a populated demo beat until preseed depth exists.
- The demo catalog marks T17 deferred and P10 deferred, while TRD-S7 is a near/experimental surface (`demo_scenarios_and_usecases_v2_4.md:304-320`, `:472-480`).

### Trading summary

| Metric | Count |
|---|---:|
| Screens/tabs | 6 |
| Mounted screen component occurrences | 75+ (including shared cards and charts) |
| API helper/path families | 50+ |
| Direct screen-level interaction sites | 23 |
| WIRED | majority of mounted components; live data unverified |
| STUB | 1 clear proof stub (ReConvergence), plus depth-gated empty states |
| MISSING | no missing primary tab surface found |
| Demo beats covered | core V1/V4, TRD-S3/V1/V2 surfaces mounted; TRD-S7 remains illustrative |

## Purchasing — screen and tab inventory

The shell defines Dashboard, Order, Analysis, Inventory, and Performance (`apps/purchasing/frontend/src/App.tsx:11-19`) and switches among them at `App.tsx:59-63`. The startup shell fetches trajectory for IKS (`App.tsx:26-43`).

### Purchasing — Dashboard

Source: `apps/purchasing/frontend/src/screens/DashboardScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `ProvenanceBadge` | `DashboardScreen.tsx:179` | today/weather source | WIRED |
| `DayZeroCard` | `DashboardScreen.tsx:181` | shared measurement state | WIRED |
| `SpendSummaryPanel` | `DashboardScreen.tsx:182` | spend summary/category/alerts/supplier | WIRED / live unverified |
| `WeatherImpactCard` | `DashboardScreen.tsx:183` | weather risk helper | WIRED / live unverified |
| `CommodityPricePanel` | `DashboardScreen.tsx:184` | commodity helpers | WIRED / live unverified |
| `ParLevelPanel` | `DashboardScreen.tsx:185` | par recommendation/status | WIRED / live unverified |
| `AutoOrderPanel` | `DashboardScreen.tsx:186` | auto-order status/audit/enable/disable | WIRED / live unverified; side effects |
| `WeatherWidget` | `DashboardScreen.tsx:189` | dashboard state | WIRED |
| `EventBadge` | `DashboardScreen.tsx:190` | today events | WIRED |
| `TransferBadge` | `DashboardScreen.tsx:198` | transfer status | WIRED / live unverified |
| `ParLevelMonitor` | `DashboardScreen.tsx:203-207` | item selection | WIRED |
| `IgnoringCostCard` | `DashboardScreen.tsx:210` | analytics props | WIRED |
| `AEStatusBar` | `DashboardScreen.tsx:211` | analytics/variants props | WIRED |
| `AccuracyAlertPanel` | `DashboardScreen.tsx:212` | category accuracy | WIRED / live unverified |
| `DecisionHistory` | `DashboardScreen.tsx:224` | history helper | WIRED / live unverified |
| `OrderCard` | `DashboardScreen.tsx:228` | click selects item/order | WIRED |
| `DataTrustBadge` | `DashboardScreen.tsx:232` | shared fingerprint | WIRED / live unverified |

Dashboard initial loading fans out to items, today summary, history, order metadata, analytics, evolution variants, and per-item waste history (`DashboardScreen.tsx:102-121`). The “Create purchase order” button clears/changes the selected item through `DashboardScreen.tsx:220`; item selection from `ParLevelMonitor` moves into the Order tab through `App.tsx:45-48`.

### Purchasing — Order

Source: `apps/purchasing/frontend/src/screens/OrderScreen.tsx`.

| Component/element | Source line | API/data path | Classification |
|---|---:|---|---|
| `OrderQueuePanel` | `OrderScreen.tsx:471` | `/api/purchasing/queue`, `api.ts:613` | WIRED / live unverified |
| `AEManagedBadge` | `OrderScreen.tsx:480` | item profile/rules | WIRED |
| Item/demand/quantity selects | `OrderScreen.tsx:486-514` | local order state | WIRED |
| `MatchResultPanel` | `OrderScreen.tsx:524` | match queue | WIRED / live unverified |
| `OrderContext` | `OrderScreen.tsx:528` | item/weather/today/waste context | WIRED |
| `WeatherWidget` / `EventBadge` | `OrderScreen.tsx:538-539` | weather/events helpers | WIRED / live unverified |
| `CostAnalysis` | `OrderScreen.tsx:540` | local calculated factors | WIRED |
| Score button | `OrderScreen.tsx:549` | calls `scoreOrder` | WIRED / live unverified |
| `EngineAssessment` | `OrderScreen.tsx:576` | factor/fingerprint/analytics props | WIRED |
| `SimilarOrdersPanel` | `OrderScreen.tsx:577` | `/api/context/similar`, `api.ts:650` | WIRED / live unverified |
| Verification reason/notes controls | `OrderScreen.tsx:591-607` | local state | WIRED |
| `ScoreResultCard` | `OrderScreen.tsx:614-617` | `/api/score`, `/api/learn`, `api.ts:672-685` | WIRED / live unverified |
| `ReasoningPanel` | `OrderScreen.tsx:620-638` | score result props | WIRED |

The screen loads items, today summary, weather, analytics, fingerprint, then item-specific profile and waste history (`OrderScreen.tsx:246-328`). It scores through `scoreOrder` and gets similar orders (`OrderScreen.tsx:379-391`). Confirm/override callbacks and verification fields are mounted at `OrderScreen.tsx:614-620`; these are write/learning flows and were not exercised because the backend was unavailable.

### Purchasing — Analysis

Source: `apps/purchasing/frontend/src/screens/AnalysisScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `ProvenanceBadge` | `AnalysisScreen.tsx:103` | static/source state | WIRED |
| `TrustRadarPanel` | `AnalysisScreen.tsx:111` | purchasing trust-weight endpoints | WIRED / live unverified |
| `ContrastCard` | `AnalysisScreen.tsx:112` | analytics props | WIRED |
| `ProfileArchetype` | `AnalysisScreen.tsx:113` | fingerprint props | WIRED |
| `FingerprintPanel` | `AnalysisScreen.tsx:114` | fingerprint helper | WIRED / live unverified |
| `DecisionExplorerPanel` | `AnalysisScreen.tsx:120` | decisions helper | WIRED / live unverified |
| `CounterfactualCard` | `AnalysisScreen.tsx:121` | counterfactual/score path | WIRED / live unverified |
| `CategoryAccuracyChart` | `AnalysisScreen.tsx:122` | accuracy endpoint | WIRED / live unverified |
| `DayOfWeekChart` | `AnalysisScreen.tsx:123` | analytics props | WIRED |
| `EventImpactCard` | `AnalysisScreen.tsx:124` | event helpers | WIRED / live unverified |
| `DiscoveryDigestCard` | `AnalysisScreen.tsx:125` | discovery digest, `api.ts:736` | WIRED / live unverified |
| `WasteCostCard` | `AnalysisScreen.tsx:126` | waste analysis/summary | WIRED / live unverified |
| `MenuMatrixCard` | `AnalysisScreen.tsx:127` | menu analysis/alerts/summary | WIRED / live unverified |

Analytics/fingerprint loading and loading/error states are in `AnalysisScreen.tsx:53-68`. The trust radar category is clickable (`TrustRadarPanel.tsx:144`); counterfactual controls are analogous to Trading but require live score support.

### Purchasing — Inventory

Source: `apps/purchasing/frontend/src/screens/InventoryScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `EvolutionPanel` | `InventoryScreen.tsx:157` | variants/evolution | WIRED / live unverified |
| `RuleGenealogyTree` | `InventoryScreen.tsx:158` | evolution history/variants | WIRED / live unverified |
| `RuleLifecyclePanel` | `InventoryScreen.tsx:159` | lifecycle helpers | WIRED / live unverified |
| `AuditTrailViewer` | `InventoryScreen.tsx:160` | audit trail | WIRED / live unverified |
| `SupplierIntelligencePanel` | `InventoryScreen.tsx:161` | QBO status/vendors/bills/price/lead-time, `api.ts:447-469` | WIRED / live unverified |
| `PredictiveParCard` | `InventoryScreen.tsx:162` | predictive par, `api.ts:716-720` | WIRED / live unverified |
| `EventPlannerCard` | `InventoryScreen.tsx:163` | event plan/history | WIRED / live unverified |
| `DeliveryScheduleCard` | `InventoryScreen.tsx:164` | delivery today/week/consolidation | WIRED / live unverified |
| Item cards/profile | `InventoryScreen.tsx:186-213` | item/waste state | WIRED |

Initial item, variant, and waste data loads at `InventoryScreen.tsx:89-108`. Category filter/empty states are conditional at `InventoryScreen.tsx:186-213`. `ItemProfile` exposes a collapsible summary (`ItemProfile.tsx:40`).

### Purchasing — Performance

Source: `apps/purchasing/frontend/src/screens/PerformanceScreen.tsx`.

| Component | Source line | API/data path | Classification |
|---|---:|---|---|
| `ChainTransferCard` | `PerformanceScreen.tsx:109` | chain status/validate/transfer | WIRED / live unverified; side effects |
| `WeeklyReportPanel` | `PerformanceScreen.tsx:110` | weekly report endpoint | WIRED / live unverified |
| `EconomicDashboardCard` | `PerformanceScreen.tsx:111` | economic model/ROI | WIRED / live unverified |
| `DisruptionRecoveryPanel` | `PerformanceScreen.tsx:112` | disruption analytics | WIRED / live unverified |
| `PaymentTimingPanel` | `PerformanceScreen.tsx:113` | payment timing/summary | WIRED / live unverified |
| `AuditExportPanel` | `PerformanceScreen.tsx:114` | audit pack/export links (`AuditExportPanel.tsx:25,80-81`) | WIRED / live unverified |
| `GroupDashboardCard` | `PerformanceScreen.tsx:115` | multi-unit dashboard | WIRED / live unverified |
| `AlertDashboardCard` | `PerformanceScreen.tsx:116` | purchasing alerts | WIRED / live unverified |
| `IKSTrackerPanel` | `PerformanceScreen.tsx:117` | IKS summary | WIRED / live unverified |
| `CohortStatusPanel` | `PerformanceScreen.tsx:118` | cohort | WIRED / live unverified |
| `SupplierScorecardPanel` | `PerformanceScreen.tsx:119` | supplier scorecards | WIRED / live unverified |
| `TrajectoryChart` | `PerformanceScreen.tsx:121` | `/api/trajectory`, `api.ts:439` | WIRED / live unverified |
| `ConservationProjection` | `PerformanceScreen.tsx:130` | conservation/trajectory props | WIRED |
| `CentroidTimelineChart` | `PerformanceScreen.tsx:131` | centroid history | WIRED / live unverified |
| `WasteCostCard` | `PerformanceScreen.tsx:156` | analytics props | WIRED |
| `WasteAlertCard` | `PerformanceScreen.tsx:157` | waste analysis/summary | WIRED / live unverified |
| `CategoryAccuracyChart` | `PerformanceScreen.tsx:158` | accuracy helper | WIRED / live unverified |

Performance loads trajectory, analytics, and conservation (`PerformanceScreen.tsx:37-52`). Export links and transfer buttons are real interaction paths but were intentionally not POSTed/downloaded in this read-only diagnostic.

### Purchasing API surface and gaps

The API module exposes core score/learn at `apps/purchasing/frontend/src/api.ts:672-689`, context at `:142-225,385-389`, learning/measurement at `:430-646`, and domain-specific families throughout `:247-801` (waste, menus, events, chain transfer, delivery, QBO, spend, commodity, par, suppliers, auto-order, matching, economics, multi-unit, discovery, and alerts).

The five tabs are mounted and no primary tab is missing. The principal uncertainty is live data: no route could be checked because port 8020 refused the OpenAPI connection. Empty/fixture states are explicitly supported, for example no par recommendations (`ParLevelPanel.tsx:127`), no audit trails (`AuditTrailViewer.tsx:39`), and no waste data (`WasteAlertCard.tsx:49`). These should be treated as valid empty-data states, not missing components.

### Purchasing summary

| Metric | Count |
|---|---:|
| Screens/tabs | 5 |
| Mounted screen component occurrences | 50+ |
| API helper/path families | 60+ |
| Direct screen-level interaction sites | 7+ plus component-level controls |
| WIRED | all primary tabs and major operational cards in source |
| STUB | no clear structural stub; several legitimate empty-data messages |
| MISSING | no missing primary tab surface found |
| Demo beats covered | operational purchasing, learning, waste, supplier, transfer, and performance surfaces mounted; live data unverified |

## DataOps — screen and tab inventory

The shell defines Dashboard, Triage, Insight, Evidence, and Curve (`apps/dataops/frontend/src/App.tsx:11-19`) and mounts them in `App.tsx:45-70`. Startup loads health and trajectory (`App.tsx:27-43`). If health reports fixture graph mode, the shell visibly warns “Live graph data is not connected” (`App.tsx:82-92`).

### DataOps — Dashboard

Source: `apps/dataops/frontend/src/screens/DashboardScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `EnterpriseHealthBar` | `DashboardScreen.tsx:191` | `/api/dataops/enterprise-health`, `api.ts:487` | WIRED / live unverified | ENT-1 |
| `EnterpriseValueCard` | `DashboardScreen.tsx:192` | enterprise health + cross-system link; component `EnterpriseValueCard.tsx:39,85` | WIRED / live unverified | ENT-1 |
| `TransferBadge` | `DashboardScreen.tsx:194` | transfer status | WIRED / live unverified |
| `ProvenanceBadge` | `DashboardScreen.tsx:195` | source state | WIRED |
| `DayZeroPanel` | `DashboardScreen.tsx:198` | measurement state | WIRED |
| `SAPDataBadge` | `DashboardScreen.tsx:205` | enterprise health, `SAPDataBadge.tsx:28` | WIRED / live unverified |
| `CelonisBadge` | `DashboardScreen.tsx:206` | enterprise health, `CelonisBadge.tsx:30` | WIRED / live unverified |
| `PipelineGrid` | `DashboardScreen.tsx:210` | `/api/context/pipelines`, `api.ts:237` | WIRED / live unverified |
| `AEImpactPanel` | `DashboardScreen.tsx:212` | `/api/ae/impact`, `api.ts:251` | WIRED / live unverified |
| `TrustCard` | `DashboardScreen.tsx:215` | trust + perturb/revert, `api.ts:293-314` | WIRED / live unverified; mutating what-if |
| `DataProductsCard` | `DashboardScreen.tsx:217` | `/api/di/products`, component docstring | WIRED / live unverified |
| `ProcessTimelinePanel` | `DashboardScreen.tsx:219` | `/api/context/process-timeline`, component line 15 | WIRED / live unverified |
| `AlertGroupCard` | `DashboardScreen.tsx:234-238` | alert-group data | WIRED / live unverified |
| `UngroupedAlerts` | `DashboardScreen.tsx:242` | alert-group data | WIRED |
| `AlertQueue` | `DashboardScreen.tsx:246` | alerts and click path | WIRED / live unverified |
| `ConservationSlider` | `DashboardScreen.tsx:251-257` | local what-if POST, `api.ts:388` | WIRED / live unverified; mutating/what-if |
| `ConservationProjection` | `DashboardScreen.tsx:267` | conservation/trajectory props | WIRED |
| `ConservationTimeline` | `DashboardScreen.tsx:268` | conservation history | WIRED / live unverified |
| `AccuracyAlertPanel` | `DashboardScreen.tsx:269` | category accuracy | WIRED / live unverified |
| `NLQueryPanel` | `DashboardScreen.tsx:273` | query form path in component | WIRED / live unverified |

Dashboard data loading covers conservation, pipelines, alerts, AE impact, history, groups, trajectory, trust, diagnostics, and related state (`DashboardScreen.tsx:80-151`). Alert group/queue selection handlers are at `DashboardScreen.tsx:234-246`; the slider calls `handleConservationDrag` (`DashboardScreen.tsx:251-257`); alert click navigation is at `DashboardScreen.tsx:307`.

### DataOps — Triage

Source: `apps/dataops/frontend/src/screens/TriageScreen.tsx`.

| Component/element | Source line | API/data path | Classification |
|---|---:|---|---|
| Back buttons | `TriageScreen.tsx:330,349,484` | parent navigation | WIRED |
| `RecurrenceBadge` | `TriageScreen.tsx:368` | alert recurrence | WIRED / live unverified |
| `SLACountdown` | `TriageScreen.tsx:378` | alert timestamps | WIRED |
| `DependencyTree` | `TriageScreen.tsx:390` | alert dependencies | WIRED / live unverified |
| `CrossGraphInsightCard` | `TriageScreen.tsx:391` | cross-graph insight | WIRED / live unverified |
| `ResolutionTimeline` | `TriageScreen.tsx:392` | system history | WIRED / live unverified |
| `ProcessSignalsPanel` | `TriageScreen.tsx:393` | process signals | WIRED / live unverified |
| `FactorAutoFill` | `TriageScreen.tsx:394` | alert factors | WIRED / live unverified |
| `SimilarAlertsPanel` | `TriageScreen.tsx:395` | similar alerts | WIRED / live unverified |
| `ActionPicker` | `TriageScreen.tsx:398-402` | selected action local state | WIRED |
| `ScoreResultCard` | `TriageScreen.tsx:406-409` | `/api/score`, `/api/learn` | WIRED / live unverified |
| `ReasoningPanel` | `TriageScreen.tsx:447-452` | score result props | WIRED |
| Apply-fix button/modal | `TriageScreen.tsx:441,462-475` | `ApplyFixModal` apply callback | WIRED / live unverified; side effect |

The screen loads alert, dependencies, factors, recurrence, AE recommendation, conservation, process signals, system history, similar alerts, and fingerprint (`TriageScreen.tsx:104-214`). Scoring and learning are invoked in `TriageScreen.tsx:258-294`; confirmation and override callbacks are `TriageScreen.tsx:406-409`.

### DataOps — Insight

Source: `apps/dataops/frontend/src/screens/InsightScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `ProfileArchetype` | `InsightScreen.tsx:99` | fingerprint props | WIRED |
| `FingerprintPanel` | `InsightScreen.tsx:100` | `/api/fingerprint` | WIRED / live unverified |
| `IncidentReplayCard` | `InsightScreen.tsx:107` | `/api/ae/incident`, `api.ts:585` | WIRED / live unverified |
| `BottleneckPanel` | `InsightScreen.tsx:108` | bottleneck helper | WIRED / live unverified |
| `ProcessTimelinePanel` | `InsightScreen.tsx:109` | process timeline | WIRED / live unverified |
| `AcquisitionPanel` | `InsightScreen.tsx:110` | `/api/dataops/di/acquisitions`, `AcquisitionPanel.tsx:42` | WIRED / live unverified |
| `IntelligenceMapPanel` | `InsightScreen.tsx:111` | profiles + intelligence map + acquisition advice, `IntelligenceMapPanel.tsx:94` | WIRED / live unverified |
| `CrossGraphInsightCard` | `InsightScreen.tsx:112` | cross-graph insight/groups, `CrossGraphInsightCard.tsx:147-158` | WIRED / live unverified | E5 |
| `WhatIfReordering` | `InsightScreen.tsx:113` | transformations, `api.ts:428` | WIRED / live unverified |
| `CentroidTimelinePanel` | `InsightScreen.tsx:114` | centroid history | WIRED / live unverified | DI-TIMELINE |
| `SourceProfilePanel` | `InsightScreen.tsx:115` | profiles/source trust/consumers | WIRED / live unverified | DI-SOURCE |
| `SearchPanel` | `InsightScreen.tsx:116` | local search/filter UI | WIRED |
| `DecisionExplorerPanel` | `InsightScreen.tsx:117` | decisions endpoint | WIRED / live unverified |

The screen loads fingerprint and incident (`InsightScreen.tsx:46-57`) and has loading/error conditions (`InsightScreen.tsx:91-98`). Intelligence Map’s acquisition recommendation and graph rendering are source-wired, but the demo document still records the historical frontend gap for gold-line rendering (`demo_scenarios_and_usecases_v2_4.md:616-624,896-901`); current component source contains gold-line normalization/rendering paths (`IntelligenceMapPanel.tsx:393-469`).

### DataOps — Evidence

Source: `apps/dataops/frontend/src/screens/EvidenceScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `CohortStatusPanel` | `EvidenceScreen.tsx:65` | cohort status | WIRED / live unverified |
| `CrossSystemPanel` | `EvidenceScreen.tsx:66` | cross-system insights | WIRED / live unverified |
| `AEImpactPanel` | `EvidenceScreen.tsx:67` | AE impact | WIRED / live unverified |
| `EvolutionPanel` | `EvidenceScreen.tsx:68` | evolution variants | WIRED / live unverified |
| `RuleGenealogyTree` | `EvidenceScreen.tsx:69` | evolution history | WIRED / live unverified |
| `AuditTrailViewer` | `EvidenceScreen.tsx:70` | audit trail | WIRED / live unverified |
| `SchemaImpactPanel` | `EvidenceScreen.tsx:71` | schema impact + SAP POs | WIRED / live unverified |
| `OperationalRulesPanel` | `EvidenceScreen.tsx:72` | operational rules | WIRED / live unverified |
| `AccuracyAlertsPanel` | `EvidenceScreen.tsx:73` | accuracy by category | WIRED / live unverified |
| `RuleGenealogyPanel` | `EvidenceScreen.tsx:74` | rule lifecycle | WIRED / live unverified |
| `RuleLifecyclePanel` | `EvidenceScreen.tsx:75` | lifecycle | WIRED / live unverified |
| `PatternOriginCard` | `EvidenceScreen.tsx:76` | `/api/ae/pattern-origin`, `api.ts:581` | WIRED / live unverified |
| `TransferStatusPanel` | `EvidenceScreen.tsx:77` | AE transfer status | WIRED / live unverified |
| `AuditTrailPanel` | `EvidenceScreen.tsx:78` | audit trail/filter/search | WIRED / live unverified |

Evidence data loads variants, pattern origin, and AE impact (`EvidenceScreen.tsx:20-32`). Audit filtering/search controls are mounted in `AuditTrailPanel.tsx:56-63`; audit rows can be expanded in `AuditTrailViewer.tsx:67-83`.

### DataOps — Curve

Source: `apps/dataops/frontend/src/screens/CurveScreen.tsx`.

| Component | Source line | API/data path | Classification | Demo beat |
|---|---:|---|---|---|
| `TrajectoryChart` | `CurveScreen.tsx:60` | `/api/trajectory`, `api.ts:399` | WIRED / live unverified | Compounding |
| `CentroidTimelineChart` | `CurveScreen.tsx:77` | centroid history | WIRED / live unverified | DI-TIMELINE |
| `DisruptionAnnotation` | `CurveScreen.tsx:78` | trajectory/disruption props | WIRED |
| `CentroidTimeline` | `CurveScreen.tsx:79` | loaded centroid history | WIRED / live unverified |

The screen fetches trajectory and centroid history in `CurveScreen.tsx:16-38`, and conditionally renders loading/error frames at `CurveScreen.tsx:51-60`.

### DataOps API surface and gaps

The DataOps API module centralizes DI, process, alert, AE, conservation, transfer, score/learn, enterprise-health, SAP/Celonis, evolution, and source-profile calls (`apps/dataops/frontend/src/api.ts:199-687`). Specific call families are:

| Functional group | Evidence | Status |
|---|---|---|
| DI profiles/products/search/query/map/acquisition | `api.ts:203-229`, `IntelligenceMapPanel.tsx:73-94` | WIRED / live unverified |
| Process/pipeline/alerts | `api.ts:237-247`, `DashboardScreen.tsx:80-151` | WIRED / live unverified |
| Trust/perturb/revert | `api.ts:293-314`, `TrustCard.tsx:29-107` | WIRED / live unverified |
| Cross-system fusion | `api.ts:340`, `CrossGraphInsightCard.tsx:147-158` | WIRED / live unverified |
| Conservation/what-if/trajectory/history | `api.ts:379-416` | WIRED / live unverified |
| Enterprise health and source systems | `api.ts:487-519`; backend route `apps/dataops/backend/app/enterprise_router.py:53` | WIRED / live unverified |
| Score/learn/fix | `api.ts:674-687`, `TriageScreen.tsx:258-294`, `ApplyFixModal.tsx:150-153` | WIRED / live unverified |

Known demo cross-reference:

- ENT-1 is mounted on Dashboard through `EnterpriseHealthBar`, `EnterpriseValueCard`, and SAP/Celonis badges (`DashboardScreen.tsx:191-206`), matching the buyer framing in `demo_scenarios_and_usecases_v2_4.md:504-516`.
- E5 is mounted through Insight’s `CrossGraphInsightCard` and apply-fix path (`InsightScreen.tsx:107-113`; `CrossGraphInsightCard.tsx:147-158`), matching `demo_scenarios_and_usecases_v2_4.md:198-205`.
- DI-TRUST/DI-PROOF use `TrustCard`’s perturbation controls (`TrustCard.tsx:29-107`), matching the documented Dashboard TrustCard surface (`demo_scenarios_and_usecases_v2_4.md:539-557`).
- DI-GOLD/DI-PRODUCT/DI-TIMELINE have source-mounted components (`DashboardScreen.tsx:217`; `InsightScreen.tsx:110-114`; `IntelligenceMapPanel.tsx:393-469`), but the document’s frontend qualification note remains relevant until a live response proves gold lines and products are populated (`demo_scenarios_and_usecases_v2_4.md:896-901`).
- The graph fixture warning is an explicit honesty guard, not a hidden failure (`App.tsx:82-92`).

### DataOps summary

| Metric | Count |
|---|---:|
| Screens/tabs | 5 |
| Mounted screen component occurrences | 50+ |
| API helper/path families | 35+ |
| Direct screen-level interaction sites | 5+ plus component-level controls |
| WIRED | all five screens and primary DI/E5 surfaces in source |
| STUB | no clear structural stub; fixture mode is explicitly disclosed |
| MISSING | no primary screen missing; live population unverified |
| Demo beats covered | E5, ENT-1, DI-TRUST, DI-PROOF, DI-PRODUCT, DI-GOLD, DI-TIMELINE structurally covered |

## Shared SDK components

The three apps use shared shell and measurement components from `copilot-sdk/copilot_sdk/frontend`:

| Shared component | Evidence | Interaction/data |
|---|---|---|
| `CopilotShell` | `copilot_sdk/frontend/CopilotShell.tsx:69` | tab buttons invoke `onTabChange` |
| `TrajectoryChart` | `copilot_sdk/frontend/TrajectoryChart.tsx:84-120` | renders IKS/quality curve and disruption reference line |
| `FingerprintPanel` | `copilot_sdk/frontend/FingerprintPanel.tsx:103-157` | renders factor signal/moderate/noise sections |
| `DataTrustBadge` | `copilot_sdk/frontend/DataTrustBadge.tsx:35` | fetches `/api/fingerprint` against app base |
| `TransferBadge` | `copilot_sdk/frontend/TransferBadge.tsx:23` | fetches `/api/transfer/status` |
| `ScoreResultCard` | `copilot_sdk/frontend/ScoreResultCard.tsx:113-158` | confirmation, action selection, centroid expansion |
| `ConservationSlider` | `copilot_sdk/frontend/ConservationSlider.tsx:71-80` | slider invokes parent drag callback |
| `ConservationProjection` | `copilot_sdk/frontend/ConservationProjection.tsx:87-105` | renders status/alpha/q/V projection |

These shared components are presentation/transport adapters; they do not create separate tab routes. Their real-data status inherits the service availability of each copilot.

## Cross-copilot endpoint/click conclusions

1. **Primary navigation is complete in source.** Trading has six tabs (`App.tsx:14-20`), Purchasing five (`App.tsx:13-19`), and DataOps five (`App.tsx:13-19`).
2. **Core scoring flows are wired.** Trading uses `/api/score` and `/api/learn` (`trading/api.ts:957-972`), Purchasing does the same (`purchasing/api.ts:672-685`), and DataOps does the same (`dataops/api.ts:674-681`).
3. **Every app exposes explicit loading/error/empty states.** This prevents an empty fixture from being mistaken for a rendered data claim, but it also means a browser pass must use preseeded data to validate the demo beats.
4. **The requested live assertion could not be completed.** All three backend connection attempts refused; this report does not infer 200/data from frontend source alone.
5. **The most concrete current product gap is Trading TRD-S7.** Its mounted component is visibly a labeled illustration pending the experiment (`ReConvergencePanel.tsx:93-108`), while the demo spec calls for an evidence-backed re-convergence moment (`demo_scenarios_and_usecases_v2_4.md:486-497`).

## Recommended follow-up verification run

After restarting the three services, run a browser pass in this order:

1. Trading: Dashboard → Log Trade score/confirm → Analysis V1/V4 → Performance rejection/re-convergence → Journal filter/detail.
2. Purchasing: Dashboard item selection → Order score/verify/confirm → Analysis counterfactual → Inventory supplier/evolution → Performance transfer/export.
3. DataOps: Dashboard TrustCard perturb/revert → Triage score/learn/apply-fix → Insight E5/DI-GOLD → Evidence audit/lifecycle → Curve trajectory/timeline.
4. For each route, capture HTTP status and response keys for every helper in the API tables above. Do not POST transfer, rollback, apply-fix, auto-order, or export actions in a read-only health pass; use dedicated fixture/reset tests for those.

## Live verification update — 2026-08-10

The copilots were restarted and the endpoint probe was rerun. The following results supersede the earlier “connection refused” snapshot.

### Trading live results — port 8010

Representative UI/API paths returned data:

| Endpoint family | Result | Response evidence |
|---|---:|---|
| `/health` | 200 | `status, domain, engine, cache_hits, cache_misses, cache_size` |
| `/api/fingerprint` | 200 | `factors, overall_win_rate, per_category_precision` |
| `/api/self/diagnostics` | 200 | `centroid_distance_to_canonical, epsilon_firm, iks, measurement_state` |
| `/api/conservation/status` | 200 | `verified_count, correct_count, alpha, q` |
| `/api/self/evolution/summary` | 200 | `schema_version, conservation_state, inventory, recent_events` |
| `/api/self/decisions`, `/api/self/audit-trail`, `/api/self/trust-traps` | 200 | decision, trail, and trap payloads returned |
| `/api/trajectory` | 200 | `points, current_iks, current_win_rate, decisions_total` |
| `/api/trading/regime*` | 200 | current/detail/history/performance/recommendation/status payloads returned |
| `/api/trading/situation/*` | 200 | regime, conditioned stats, abstention, rejection, Sharpe payloads returned |
| `/api/trading/analytics/*` | 200 | dispersion, regime-VRP, vol-Sharpe, VRP attribution payloads returned |
| `/api/trading/score/counterfactual/default` | 200 | base/perturbed score, delta, actions, provenance |
| `/api/trading/evolution/rejection-summary` | 200 | tested/promoted/rejected counts and breakdown |
| `/api/transfer/status`, `/api/transfer/opportunities` | 200 | transfer state/opportunity payloads returned |

Expected parameter-dependent results were observed for `/api/context/similar` (422 without required query/body), `/api/trading/market/ohlcv` (422 without required parameters), and template paths such as `/api/trading/evidence/{trade_id}` (404 when the literal placeholder is used). `/api/context/trade-metadata`, `/api/history`, `/api/self/centroid-history`, `/api/trading/profiles`, and `/api/trading/trades` exceeded the short diagnostic timeout; these are **not classified as missing** and need a longer or fixture-aware probe.

**Trading conclusion:** core Dashboard, Analysis, Performance, scoring, regime, conservation, evolution, and transfer data paths are live-wired. TRD-S7 remains a product stub because the UI itself still says “Illustrative ARCH curves — experiment pending” (`apps/trading/frontend/src/components/ReConvergencePanel.tsx:93-108`), despite the surrounding regime endpoints returning 200.

### Purchasing live results — port 8020

| Endpoint family | Result | Response evidence |
|---|---:|---|
| `/health` | 200 | cache stats and IKS fields returned |
| `/api/fingerprint`, `/api/self/diagnostics`, `/api/conservation/status` | 200 | measurement/conservation payloads returned |
| `/api/self/evolution/summary`, `/api/evolution/*` | 200 | schema v1/evolution payloads returned |
| `/api/context/items`, `/api/context/today-summary`, `/api/context/weather` | 200 | 20 items and context payloads returned |
| `/api/purchasing/spend/*` | 200 | summary, category, supplier, alert, cost-per-cover payloads returned |
| `/api/purchasing/waste/*` | 200 | analysis and summary payloads returned |
| `/api/purchasing/par/*` | 200 | predictive/status/recommendation payloads returned; recommendation list is empty |
| `/api/purchasing/auto-order/*` | 200 | status/audit payloads returned |
| `/api/purchasing/qbo/*` | 200 | status, vendors, purchase orders, payments, lead-times, price history routes returned |
| `/api/purchasing/menu/*`, `/events/*`, `/delivery/*` | 200 | menu, event, delivery/consolidation payloads returned |
| `/api/purchasing/chain/status` | 200 | chain status payload returned |
| `/api/purchasing/match/queue`, `/api/purchasing/queue` | 200 | match/order queues returned |
| `/api/purchasing/economic/*`, `/multi-unit/*`, `/iks/*`, `/trust-weights/*` | 200 | economic, multi-unit, IKS, and trust payloads returned |
| `/api/purchasing/audit/pack`, `/audit/export/json`, `/audit/export/csv` | 200 | audit pack/export responses returned |

Expected parameter-dependent results were observed for `/api/context/similar` (422) and literal template routes such as `/api/purchasing/queue/{order_id}` or `/api/purchasing/supplier/{supplier_id}/scorecard` (404). `/api/context/order-metadata`, `/api/history`, `/api/self/centroid-history`, and `/api/purchasing/qbo/bills` exceeded the short diagnostic timeout and remain unclassified.

**Purchasing conclusion:** all five screens are not only mounted but have live responses for their main operational, learning, supplier, spend, waste, transfer, and performance data families. Empty par recommendations and empty spend/supplier subsets are data-state results, not missing routes.

### DataOps live results — port 8030

| Endpoint family | Result | Response evidence |
|---|---:|---|
| `/health` | 200 | graph source, engine, and cache stats returned |
| `/api/fingerprint`, `/api/self/diagnostics`, `/api/conservation/status` | 200 | measurement and conservation payloads returned |
| `/api/self/evolution/summary`, `/api/evolution/*` | 200 | evolution schema/payloads returned |
| `/api/self/centroid-history?limit=5`, `/api/self/transfers`, `/api/self/trust-traps` | 200 | checkpoints/transfers/traps returned |
| `/api/dataops/enterprise-health` | 200 | `sap, celonis, graph, overall, combined_impact, engine_version` |
| `/api/dataops/trust` | 200 | trust factors, overall trust, conservation, IKS |
| `/api/di/products` | 200 | products payload returned |
| `/api/di/acquisition-advice` | 200 | recommendations payload returned |
| `/api/di/combinations` | 200 | combinations and total value returned |
| `/api/context/pipelines`, `/api/context/alerts`, `/api/context/alert-groups` | 200 | pipeline/alert/group payloads returned |
| `/api/ae/impact`, `/api/ae/conservation-history`, `/api/ae/transfer-status` | 200 | AE impact, conservation, transfer payloads returned |
| `/api/context/process-timeline` | 200 | process/bottleneck/dollar-calibration payload returned |
| `/api/ae/pattern-origin`, `/api/ae/incident`, `/api/ae/operational-rules` | 200 | evidence/incident/rule payloads returned |
| `/api/di/intelligence-map` | timeout | no response within the diagnostic timeout |
| `/api/di/sources` | 404 | frontend/API helper expects this family (`apps/dataops/frontend/src/api.ts:203-229`) |
| `/api/discovery/cross-system` | 404 | ENT-1 card links to this exact path (`apps/dataops/frontend/src/components/EnterpriseValueCard.tsx:85`) |

**DataOps conclusion:** the primary Dashboard/Insight/Evidence/Curve data families are live. Two concrete gaps need follow-up: the source-profiler path used by the frontend/API family does not match a live `/api/di/sources` route, and the ENT-1 cross-system link is currently a dead 404. The Intelligence Map route exists in the frontend call path (`api.ts:224`) but timed out and needs an isolated performance/fixture probe.

### Updated classification after live checks

| Copilot | Previously live-unverified | Confirmed live 200 families | Concrete gaps found |
|---|---:|---:|---|
| Trading | broad majority | core scoring, diagnostics, conservation, regime, situation, analytics, evolution, transfer | TRD-S7 remains illustrative; several parameterized/slow reads need targeted probes |
| Purchasing | broad majority | core context, scoring substrate, spend/waste/par/QBO/events/delivery/economic/IKS/trust | parameterized/slow reads need targeted probes; no structural tab gap |
| DataOps | broad majority | core health/measurement, enterprise health, products, acquisition, combinations, process, evidence | `/api/di/sources` 404; `/api/discovery/cross-system` 404; Intelligence Map timeout |

