# Purchasing Frontend v2 Rebuild Implementation Plan

## 1. Executive Summary

Rebuild `apps/purchasing/frontend/src` from scratch as Purchasing Copilot Frontend v2. The rebuild replaces the existing Purchasing frontend source surface with a focused operational UI for ordering, inventory, analysis, and performance.

The implementation should keep frontend package/config files stable unless a minimal compatibility fix is proven necessary. Current discovery found a blocker: `apps/purchasing/frontend/package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, and `postcss.config.js` are absent. A compileable frontend will require either creating these files with explicit approval or intentionally reusing another package boundary. Do not silently assume they exist.

The app should use shared SDK frontend components through relative imports from `copilot_sdk/frontend`. Purchasing-specific screens, API normalization, types, theme, and visual components must live only under `apps/purchasing/frontend/src`.

No backend, SDK, Trading, DataOps, GAE, SOC, S2P, or ci-platform files are in scope for implementation.

Core thesis:

> You think weather and events drive ordering. They don't. Your historical waste pattern is the only signal. And the system auto-manages the items you're consistent on.

Design anchors:

- Contrast Card: `89% accuracy WITH fingerprint, 38% WITHOUT. Same owner.`
- Par Level Monitor: real inventory with waste sparklines and AE badges.
- Cost Analysis: `Stockout costs 53x more than waste. The math is obvious.`

## 2. Source Contracts From Prompt 0

### SDK Frontend Components

`copilot_sdk/frontend/index.ts` exports:

- `IKSBadge` and `IKSBadgeProps`
- `CopilotShell`, `CopilotShellProps`, `CopilotShellTab`
- `DecisionHistory`, `DecisionHistoryProps`
- `FingerprintPanel`, `FactorItem`, `FingerprintCategory`, `FingerprintPanelProps`
- `TrajectoryChart`, `Annotation`, `TrajectoryChartProps`, `TrajectoryPoint`
- `ScoreResultCard`, `CentroidDelta`, `RewardLine`, `ScoreResult`, `ScoreResultCardProps`
- `EvolutionPanel`, `EvolutionPanelProps`, `EvolutionStatus`, `EvolutionVariant`
- `ConservationSlider`

Important prop contracts:

- `CopilotShell`: `name`, `icon`, `tabs`, `activeTab`, `onTabChange`, `iks`, optional `iksDelta`, and `children`.
- `DecisionHistory`: `decisions`, `renderCard`, optional `title`, `emptyMessage`, `maxVisible`.
- `ScoreResultCard`: `result`, `onConfirm`, `onOverride`, optional `iksDelta`, `rewardLine`, `centroidDelta`.
- `ScoreResult`: `decisionId`, `action`, `actionIndex`, `confidence`, `probabilities`, `category`, optional `factors`, `actionNames`.
- `FingerprintPanel`: `factors`, optional `signalLabel`, `noiseLabel`, `perCategoryPrecision`, `decisionsAnalyzed`.
- `FactorItem`: `name`, `displayName`, `weight`, `sigma`, `interpretation`, optional `category`.
- `TrajectoryChart`: `points`, `currentIks`, `currentWinRate`, optional `switchingCostLine`, optional `annotations`, `narrative`, `decisionsTotal`, `daysActive`.
- `EvolutionPanel`: `variants`, optional `title`.
- `EvolutionVariant`: `id`, `name`, `status`, `description`, optional `shadowCount`, `shadowWinRate`, `conservationAtPromotion`, `rejectReason`, `sourceCopilot`, `sourceRule`.
- `IKSBadge`: `value`, optional `delta`, optional `size`.

### Purchasing Backend V2 Endpoints

Context endpoints are mounted under `/api/context`:

- `GET /today-summary`
- `GET /items`
- `GET /waste-history/{item}`
- `GET /weather`
- `POST /order-metadata`
- `GET /order-metadata`
- `GET /analytics`
- `GET /similar`
- `GET /item/{name}/profile`

SDK endpoints are mounted under `/api`:

- `POST /score`
- `POST /learn`
- `GET /fingerprint`
- `GET /trajectory`
- `GET /history`
- `GET /evolution/variants`
- `GET /evolution/patterns`

Response shapes:

- `GET /api/context/today-summary` returns `{ date, day_of_week, weather, events }`.
- `GET /api/context/items` returns an array of item records from `apps/purchasing/backend/app/items.json`.
- `GET /api/context/waste-history/{item}` returns `{ item, waste_pct, count }`.
- `GET /api/context/weather` returns cached weather fields including `temperature_f`, `precipitation_prob`, `wind_mph`, `weather_factor`, `source`.
- `POST /api/context/order-metadata` requires `decision_id` and stores arbitrary order metadata by decision id. It returns `{ decision_id, metadata }`.
- `GET /api/context/order-metadata` returns the order metadata map.
- `GET /api/context/analytics` returns analytics cache or a default object with `contrast_card`, `counterfactual`, `category_accuracy`, `day_of_week`, `event_impact`, `waste_cost_analysis`, `ae_impact`, `portfolio_summary`.
- `GET /api/context/similar` requires query params `category`, `expected_demand`, `day_of_week`, `weather_forecast`, `event_flag`, `historical_waste`, `supplier_lead_time`, optional `n`. It returns `{ similar, count }`, where each similar row includes `order_id`, `item`, `category`, `day_of_week`, `is_event_day`, `quantity_lbs`, `waste_pct`, `stockout_occurred`, `is_correct`, `similarity`.
- `GET /api/context/item/{name}/profile` returns `{ item, waste_history, waste_avg, waste_trend, ae_rules, ae_managed }` or `{ error, name }`.
- `GET /api/evolution/variants` returns `{ engine, domain, variants }`. The SDK `EvolutionPanel` shape differs from raw backend variant rows; adapt in frontend.
- `GET /api/history` returns `{ engine, decisions }`.
- `POST /api/score` accepts `{ category, factors, context? }` and returns scorer result plus `engine`.
- `POST /api/learn` accepts `{ decision_id, actual_action, outcome?, context? }` and returns learn result plus `reward`, `previous_reward`, `reward_multiplier`, `engine`.
- `GET /api/fingerprint` returns fingerprint result plus `engine`.
- `GET /api/trajectory` returns trajectory result plus `engine`.

### Data Shapes

`analytics_cache.json` top-level keys:

- `source`
- `generated_from_seed`
- `contrast_card`
- `counterfactual`
- `category_accuracy`
- `day_of_week`
- `event_impact`
- `waste_cost_analysis`
- `ae_impact`
- `portfolio_summary`

`contrast_card` has aggregate stats, not exact chart curves:

- `basis`
- `aligned`: `count`, `correct`, `accuracy`, `total_cost_dollars`
- `misaligned`: `count`, `correct`, `accuracy`, `total_cost_dollars`
- `neutral`: `count`, `correct`, `accuracy`, `total_cost_dollars`

`items.json` item fields:

- `item_id`
- `name`
- `display_name`
- `emoji`
- `category`
- `unit`
- `par_level`
- `default_quantity_lbs`
- `on_hand_qty`
- `unit_price`
- `supplier`
- `event_sensitivity`
- `usage_range`
- `supplier_lead_time`
- `source`

`purchasing_seed_v2.json` order fields:

- `order_id`
- `item`
- `display_name`
- `category`
- `quantity_lbs`
- `day_of_week`
- `date`
- `is_event_day`
- `event_type`
- `expected_demand`
- `day_of_week_factor`
- `weather_forecast`
- `event_flag`
- `historical_waste`
- `supplier_lead_time`
- `action_taken`
- `is_correct`
- `waste_pct`
- `waste_cost_dollars`
- `stockout_occurred`
- `stockout_cost_dollars`
- `total_cost_dollars`

`evolution_fixtures.json` contains `{ variants }`. Raw variant rows include:

- `id`
- `event_type`
- `variant_id`
- `artifact_type`
- `triggered_by`
- `description`
- `before_state`
- `after_state`
- `graph_context`
- `metadata`
- `impact`
- `magnitude`
- `timestamp`
- `timestamp_epoch`
- `source_copilot`
- `source_rule`
- `match`
- `warm_start_prior`

`waste_history.json` maps item names to arrays of waste percentages. Every known item has a short numeric series.

### Purchasing Preset Contract

Categories:

- `protein`
- `produce`
- `dairy`
- `dry_goods`
- `beverages`

Actions:

- `order_as_planned`
- `order_more`
- `order_less`
- `skip`

Factor names:

- `expected_demand`
- `day_of_week`
- `weather_forecast`
- `event_flag`
- `historical_waste`
- `supplier_lead_time`

### Existing Package/Config Constraints

Discovery found no existing Purchasing frontend package/config files:

- `apps/purchasing/frontend/package.json` missing
- `apps/purchasing/frontend/vite.config.ts` missing
- `apps/purchasing/frontend/tsconfig.json` missing
- `apps/purchasing/frontend/tailwind.config.js` missing
- `apps/purchasing/frontend/postcss.config.js` missing

Therefore, a strict src-only rebuild cannot currently compile. Keep package/config stable if they are restored before implementation. If they remain absent, request explicit approval to create minimal package/config files before source implementation.

## 3. Files To Replace Or Create Under `src`

Replace/create only files under `apps/purchasing/frontend/src` during source implementation:

- `main.tsx`
- `App.tsx`
- `theme.css`
- `api.ts`
- `types.ts`
- `screens/DashboardScreen.tsx`
- `screens/OrderScreen.tsx`
- `screens/AnalysisScreen.tsx`
- `screens/InventoryScreen.tsx`
- `screens/PerformanceScreen.tsx`
- `components/ParLevelMonitor.tsx`
- `components/ParLevelBar.tsx`
- `components/WasteSparkline.tsx`
- `components/AEStatusBar.tsx`
- `components/AEManagedBadge.tsx`
- `components/OrderCard.tsx`
- `components/WeatherWidget.tsx`
- `components/EventBadge.tsx`
- `components/OrderContext.tsx`
- `components/CostAnalysis.tsx`
- `components/SimilarOrdersPanel.tsx`
- `components/EngineAssessment.tsx`
- `components/ContrastCard.tsx`
- `components/CounterfactualCard.tsx`
- `components/ProfileArchetype.tsx`
- `components/IgnoringCostCard.tsx`
- `components/DayOfWeekChart.tsx`
- `components/CategoryAccuracyChart.tsx`
- `components/EventImpactCard.tsx`
- `components/WasteCostCard.tsx`
- `components/ItemProfile.tsx`
- `components/CategoryEmoji.tsx`

## 4. Forbidden Files

Do not modify:

- `apps/purchasing/backend/**`
- `copilot_sdk/frontend/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/scoring/**`
- `apps/trading/**`
- `apps/dataops/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`
- git metadata

Package/config files are also out of scope unless the user explicitly approves creating missing minimal frontend package/config files.

## 5. API Client Contract

`api.ts` owns all HTTP behavior and snake_case to camelCase normalization. Components should consume camelCase app types and should not individually translate backend field names.

Preserve:

```ts
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8020";
```

Functions:

- `getAnalytics(): Promise<Analytics>`
- `getItems(): Promise<Item[]>`
- `getTodaySummary(): Promise<TodaySummary>`
- `getWeather(): Promise<Weather>`
- `getWasteHistory(item: string): Promise<WasteHistory>`
- `getItemProfile(name: string): Promise<ItemProfile>`
- `getSimilarOrders(input, n?: number): Promise<{ similar: SimilarOrder[]; count: number }>`
- `getOrderMetadata(): Promise<Record<string, OrderMetadata>>`
- `saveOrderMetadata(payload: OrderMetadata & Record<string, unknown>): Promise<{ decisionId: string; metadata: OrderMetadata }>`
- `getEvolutionVariants(): Promise<{ variants: Variant[]; domain?: string; engine?: Record<string, unknown> }>`
- `getHistory(): Promise<HistoryDecision[]>`
- `getFingerprint(): Promise<FingerprintResponse>`
- `getTrajectory(): Promise<TrajectoryResponse>`
- `scoreOrder(payload): Promise<ScoreResponse>`
- `learnOrder(decisionId: string, action: string, outcome?: string, context?: Record<string, unknown>): Promise<LearnResponse>`

Rules:

- No `localStorage`.
- No `sessionStorage`.
- Normalize unknown/missing numeric fields to `null` or safe display defaults at the API boundary.
- Preserve backend factor names when calling `/api/score` and `/api/context/similar`.

## 6. Types Contract

`types.ts` should define stable app-level types:

- `Analytics`
- `Item`
- `TodaySummary`
- `Weather`
- `WasteHistory`
- `ItemProfile`
- `Variant`
- `OrderMetadata`
- `HistoryDecision`
- `JoinedOrder`
- `ScoreResponse`
- `LearnResponse`
- `FingerprintResponse`
- `TrajectoryResponse`
- `SimilarOrder`
- `OrderFormState`

`JoinedOrder` should combine history decision, stored order metadata, item catalog details, waste history, item profile, and any matching seed-style fields where available.

Use normalized camelCase in UI-facing types, but retain clear API helpers for snake_case query and POST payloads.

## 7. App Contract

Tabs:

1. Dashboard
2. Order
3. Analysis
4. Inventory
5. Performance

Dashboard is default.

`App.tsx` owns:

- Active tab state.
- Selected item state.
- Lightweight trajectory/IKS state for shell header.
- Top-level callbacks for item selection and navigation.

Wrap the app in SDK `CopilotShell`:

- `name="Purchasing Copilot"`
- compact purchasing-specific `icon`
- stable tab ids
- `iks` from trajectory when available, otherwise a safe default

Selected item state drives `OrderScreen`. Dashboard item/order clicks set selected item and navigate to Order.

## 8. Dashboard Contract

Fetch in parallel on mount:

- `getItems()`
- `getTodaySummary()`
- `getHistory()`
- `getOrderMetadata()`
- `getAnalytics()`
- `getEvolutionVariants()`

Then fetch waste history for items needing order. A practical heuristic is items where `onHandQty < parLevel`, ordered by largest par gap and/or highest historical waste.

Render:

- Weather/Event/Cover header using `WeatherWidget` and `EventBadge`.
- `ParLevelMonitor`.
- `IgnoringCostCard`.
- `AEStatusBar`.
- Today's completed orders using SDK `DecisionHistory` and `OrderCard`.
- `Order Something Else` button.

Interactions:

- Item/order clicks set selected item and navigate to Order.
- `Order Something Else` navigates to Order with no preselected item.

## 9. Order Contract

Order workflow:

- Accept preselected item from App or allow item dropdown.
- Fetch item profile, weather, waste history.
- User provides `expected_demand` only.
- Compute five auto factors:
  - `day_of_week`
  - `weather_forecast`
  - `event_flag`
  - `historical_waste`
  - `supplier_lead_time`
- Combine with user input to score all six Purchasing factors:
  - `expected_demand`
  - `day_of_week`
  - `weather_forecast`
  - `event_flag`
  - `historical_waste`
  - `supplier_lead_time`

Screen sections:

1. Item selector / selected item summary.
2. `OrderContext` showing auto-computed factors.
3. `WeatherWidget` and `EventBadge`.
4. `CostAnalysis` showing stockout vs waste, risk ratio, and the 53x thesis where supported.
5. AE suggestion if a variant/item rule matches.
6. `Score This Order`.

After score:

1. `EngineAssessment`.
2. `SimilarOrdersPanel`.
3. SDK `ScoreResultCard`.

Confirm flow:

- `ScoreResultCard.onConfirm` calls `learnOrder`.
- `onOverride` calls `learnOrder` with selected action.
- Store order metadata after score or after confirm, but ensure enough fields for Dashboard cards:
  - `decisionId`
  - item identity and display fields
  - quantity/unit/cost estimates
  - auto-computed factors
  - score action and confidence
  - waste/stockout estimates
  - AE rule ids if any
- Do not pass `centroidDelta`; backend does not provide enough stable detail for it.

## 10. Analysis Contract

Exact rendering order:

1. `ContrastCard`
2. `ProfileArchetype`
3. SDK `FingerprintPanel`
4. `CounterfactualCard`
5. `CategoryAccuracyChart`
6. `DayOfWeekChart`
7. `EventImpactCard`
8. `WasteCostCard`

`ContrastCard`:

- Anchor copy: `89% accuracy WITH fingerprint, 38% WITHOUT. Same owner.`
- Use `analytics.contrastCard`.
- Backend currently supplies aggregate aligned/misaligned stats, not exact curves. If curves are needed, derive conservative approximate curves from aggregate stats and label them as derived in code comments.

`ProfileArchetype`:

- Use fingerprint factors by highest weight.
- Named archetype `THE HISTORIAN` when `historical_waste` is the top factor.
- Keep wording grounded in available analytics/fingerprint values.

`FingerprintPanel`:

- Use actual SDK prop contract.
- Provide Purchasing display names and interpretations.
- Guard missing/empty fingerprint data.

## 11. Inventory Contract

Fetch:

- `getItems()`
- `getEvolutionVariants()`
- waste history for all 20 items in parallel
- item profiles as needed for expanded items

Render:

- Category summary table.
- Items grouped by category.
- Expandable `ItemProfile`.
- `ParLevelBar` with dollar amounts.
- `WasteSparkline` for each item.
- `AEManagedBadge` where `aeManaged` is true.
- SDK `EvolutionPanel` showing all 3 variants after mapping backend variant rows to SDK `EvolutionVariant` shape.

Raw evolution fixture rows use `event_type` values like `promotion_approved` and `promotion_rejected`; map these to SDK statuses such as `promoted`, `rejected`, or `shadow`.

## 12. Performance Contract

Fetch:

- `getTrajectory()`
- `getAnalytics()`

Render:

- Stats row using trajectory and `analytics.portfolioSummary`.
- SDK `TrajectoryChart`.
- Cost impact from `analytics.wasteCostAnalysis`.
- Category trends from `analytics.categoryAccuracy`.
- Event impact from `analytics.eventImpact`.
- AE impact from `analytics.aeImpact`.

Use safe empty states when trajectory points or analytics sections are missing.

## 13. Visual And UX Constraints

Theme:

- Green accent in `theme.css`.
- AE brand badges use purple `#7c3aed`.
- Use existing SDK CSS variables where possible.
- Desktop-first layout with responsive fallback.

Interaction and ordering:

- Par level bars include dollar amounts.
- Contrast Card is first on Analysis.
- Engine Assessment appears before Similar Orders.
- Similar Orders appears before confirmation.
- No `localStorage`.
- No `sessionStorage`.
- No backend fixture generation in frontend.

Content:

- Keep the UI operational and dense enough for repeated ordering work.
- Do not build a landing page.
- Do not use external fonts.

## 14. Implementation Sequence

Prompt 2:

1. Resolve package/config blocker. If package/config files remain absent, request explicit approval to create minimal Vite/React/Tailwind/TypeScript config files before source implementation.
2. Replace/create `src/main.tsx`, `src/api.ts`, `src/types.ts`, `src/theme.css`, `src/App.tsx`.
3. Build Dashboard components and `DashboardScreen`.
4. Add compile-safe placeholders for Order, Analysis, Inventory, and Performance if needed.
5. Run typecheck/build if package exists.

Prompt 3:

1. Implement `OrderScreen`.
2. Implement `OrderContext`, `CostAnalysis`, `SimilarOrdersPanel`, `EngineAssessment`, `WeatherWidget`, `EventBadge`.
3. Wire score/learn/order metadata flow.
4. Validate order workflow type contracts.

Prompt 4:

1. Implement Analysis, Inventory, and Performance.
2. Implement remaining components:
   - `ContrastCard`
   - `CounterfactualCard`
   - `ProfileArchetype`
   - charts/cards
   - `ItemProfile`
   - SDK `EvolutionPanel` integration
3. Run final typecheck/build/backend/root tests.

## 15. Validation Commands

From `apps/purchasing/frontend`:

```powershell
npm install
npx tsc --noEmit
npm run build
```

From repo root:

```powershell
python -m pytest tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -v --timeout=120
```

Do not start live Vite/backend servers or run Playwright unless the user confirms the live stack is running.

## 16. Residual Risks And Mitigations

- Purchasing frontend package/config files are missing. Mitigation: do not start source implementation until package/config scope is clarified.
- Backend analytics contrast card has aggregate stats only, not exact curves. Mitigation: derive clearly conservative display curves or avoid claiming exact trend curves.
- Backend evolution variants do not match SDK `EvolutionPanel` directly. Mitigation: map raw variant rows to SDK `EvolutionVariant` in frontend.
- `order_metadata` stores arbitrary payloads. Mitigation: `api.ts` and `types.ts` should define a stable frontend metadata shape while safely accepting older records.
- SDK prop shapes may change. Mitigation: re-read SDK frontend components immediately before implementation.
