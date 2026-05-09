# Trading Frontend v2 Rebuild Implementation Plan

## 1. Executive Summary

Rebuild `apps/trading/frontend/src` from scratch as a Trading-specific frontend for the existing Trading Backend v2. Preserve the existing backend, SDK, package, Vite, TypeScript, Tailwind, and npm configuration unless a minimal compatibility fix is proven necessary during implementation.

The rebuilt app will use shared SDK frontend components through relative imports from `copilot_sdk/frontend`, while all Trading-specific screens, API normalization, types, and visual components will live only under `apps/trading/frontend/src`.

No backend, SDK, Purchasing, DataOps, GAE/SOC/S2P, or ci-platform files are in scope.

## 2. Source Contracts From Prompt 0

### SDK Frontend Components

`copilot_sdk/frontend/index.ts` exports:
- `IKSBadge` and `IKSBadgeProps`
- `CopilotShell`, `CopilotShellProps`, `CopilotShellTab`
- `DecisionHistory`, `DecisionHistoryProps`
- `FingerprintPanel`, `FactorItem`, `FingerprintCategory`, `FingerprintPanelProps`
- `TrajectoryChart`, `Annotation`, `TrajectoryChartProps`, `TrajectoryPoint`
- `ScoreResultCard`, `CentroidDelta`, `RewardLine`, `ScoreResult`, `ScoreResultCardProps`
- `EvolutionPanel`
- `ConservationSlider`

Important prop contracts:
- `CopilotShell`: `name`, `icon`, `tabs`, `activeTab`, `onTabChange`, `iks`, optional `iksDelta`, and `children`.
- `DecisionHistory`: `decisions`, `renderCard`, optional `title`, `emptyMessage`, `maxVisible`.
- `ScoreResultCard`: `result`, `onConfirm`, `onOverride`, optional `iksDelta`, `rewardLine`, `centroidDelta`.
- `TrajectoryChart`: `points`, `currentIks`, `currentWinRate`, optional `switchingCostLine`, optional `annotations`, `narrative`, `decisionsTotal`, `daysActive`.
- `FingerprintPanel`: `factors`, optional `signalLabel`, `noiseLabel`, `perCategoryPrecision`, `decisionsAnalyzed`.

### Trading Backend V2 Endpoints

Context endpoints are mounted under `/api/context`:
- `GET /market-snapshot`
- `GET /ticker/{ticker}`
- `GET /portfolio-summary`
- `GET /analytics`
- `GET /similar`
- `POST /trade-metadata`
- `GET /trade-metadata`

Existing SDK endpoints remain under `/api`:
- `/score`
- `/learn`
- `/fingerprint`
- `/trajectory`
- `/history`

`/api/context/ticker/{ticker}` returns the ticker cache entry as-is. Unknown tickers return `{ ticker, price: null, change_30d_pct: null, volume: null, source: "unknown" }`.

`/api/context/analytics` returns `analytics_cache.json` or a safe empty analytics object with the same top-level sections.

`/api/context/similar` query params:
- `category`
- `conviction`
- `research_depth`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`
- `n`, default `5`

Similar response:
```json
{
  "similar": [
    {
      "trade_id": "V2-001",
      "ticker": "NVDA",
      "thesis_type": "momentum",
      "timeframe": "swing",
      "research_depth": 0.92,
      "pnl_pct": 8.0,
      "outcome": "win",
      "is_correct": true,
      "similarity": 0.99
    }
  ],
  "count": 1
}
```

`/api/context/trade-metadata` stores arbitrary metadata keyed by `decision_id`; `decision_id` is required.

### Analytics Shape

`analytics_cache.json` includes:
- `source`
- `seed_file`
- `total_trades`
- `closed_trades`
- `open_positions`
- `category_counts`
- `thesis_counts`
- `contrast_card`
- `counterfactual`
- `calendar_heatmap`
- `thesis_breakdown`
- `regime_analysis`
- `research_impact`
- `portfolio_concentration`
- `rolling_10`
- `risk_management`
- `portfolio_summary`

The UI must treat every section as optional enough to render empty states, but should prefer the cache data when present.

### Seed V2 Shape

`trading_seed_v2.json` trade fields include:
- `trade_id`, `ticker`, `direction`, `category`, `thesis_type`, `timeframe`
- `research_checklist`, `research_depth`, `conviction`, `technical_signal`, `position_size`, `time_horizon`, `market_regime`
- `shares`, `entry_price`, `portfolio_value`, `stop_loss`, `target`, `rr_ratio`
- `exit_price`, `pnl_pct`, `pnl_dollars`, `hold_days`, `outcome`, `is_correct`
- `day_of_week`, `date`, `action_taken`, `vix_at_entry`

### Trading Preset Contract

Trading categories:
- `equity_long`
- `equity_short`
- `crypto_spot`
- `options`
- `etf`

Trading actions:
- `buy`
- `hold`
- `sell`

Trading factors, in canonical order:
- `conviction`
- `research_depth`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`

### Existing Frontend Package Constraints

`apps/trading/frontend/package.json` already includes React 18, Recharts, Vite 6, TypeScript 5.7, Tailwind, and scripts:
- `npm run typecheck` -> `tsc --noEmit`
- `npm run build` -> `tsc --noEmit && vite build`
- `npm run dev` -> Vite on `127.0.0.1:5174`

Keep package/config files stable unless implementation proves a minimal compatibility fix is required.

## 3. Files To Replace Or Create Under `src`

Replace/create only files under `apps/trading/frontend/src`:

- `main.tsx`
- `App.tsx`
- `theme.css`
- `api.ts`
- `types.ts`
- `screens/DashboardScreen.tsx`
- `screens/LogTradeScreen.tsx`
- `screens/AnalysisScreen.tsx`
- `screens/PerformanceScreen.tsx`
- `screens/TradeDetailScreen.tsx`
- `components/PortfolioSummary.tsx`
- `components/PortfolioConcentration.tsx`
- `components/CalendarHeatmap.tsx`
- `components/ThesisBreakdown.tsx`
- `components/TradeCard.tsx`
- `components/TickerLookup.tsx`
- `components/ResearchChecklist.tsx`
- `components/PositionSizer.tsx`
- `components/MarketContext.tsx`
- `components/ContrastCard.tsx`
- `components/CounterfactualCard.tsx`
- `components/SimilarTradesPanel.tsx`
- `components/EngineAssessment.tsx`
- `components/PriceSparkline.tsx`
- `components/ProfileArchetype.tsx`
- `components/DayOfWeekChart.tsx`
- `components/ResearchImpactChart.tsx`
- `components/RegimeChart.tsx`
- `components/RollingMetrics.tsx`
- `components/RiskManagementCard.tsx`
- `components/CategoryPerformance.tsx`
- `components/PaperBadge.tsx`

## 4. Forbidden Files

Do not modify:
- `apps/trading/backend/**`
- `copilot_sdk/frontend/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/scoring/**`
- `apps/purchasing/**`
- `apps/dataops/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`
- git metadata or package/config files unless a minimal compatibility issue is proven and approved by scope.

## 5. API Client Contract

`api.ts` owns all HTTP behavior and all snake_case to camelCase normalization. Components should consume camelCase app types and should not individually translate backend response keys.

Preserve:
```ts
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8010";
```

Functions:
- `getAnalytics(): Promise<Analytics>`
- `getHistory(): Promise<TradeHistoryDecision[]>`
- `getTradeMetadata(): Promise<Record<string, TradeMetadata>>`
- `getMarketSnapshot(): Promise<MarketSnapshot>`
- `getTicker(ticker: string): Promise<TickerData>`
- `getFingerprint(): Promise<FingerprintResponse>`
- `getTrajectory(): Promise<TrajectoryResponse>`
- `scoreTrade(payload): Promise<ScoreResponse>`
- `learnTrade(decisionId: string, action: string, outcome?: string): Promise<LearnResponse>`
- `saveTradeMetadata(payload: TradeMetadata): Promise<{ decisionId: string; metadata: TradeMetadata }>`
- `getSimilarTrades(input, n?: number): Promise<{ similar: SimilarTrade[]; count: number }>`

Rules:
- No `localStorage`.
- No `sessionStorage`.
- No fake backend data beyond empty-state UI fallbacks.
- Normalize unknown/missing numeric fields to `null` or safe display defaults at the API boundary.

## 6. Types Contract

`types.ts` should define stable app-level types:
- `Analytics`
- `TradeSeedV2`
- `TradeMetadata`
- `TradeHistoryDecision`
- `JoinedTrade`
- `TickerData`
- `MarketSnapshot`
- `ScoreResponse`
- `LearnResponse`
- `FingerprintResponse`
- `TrajectoryResponse`
- `SimilarTrade`
- `TradeFormState`

`JoinedTrade` should combine history decision, stored metadata, ticker context, and any matching seed-style fields where available. Screens should render against `JoinedTrade` where possible.

## 7. App Contract

`App.tsx` owns:
- Active tab state.
- Active trade ID state.
- Global trajectory/fingerprint lightweight state needed by shell/header.
- Top-level data refresh callbacks passed to screens.

Tabs:
1. Dashboard
2. Log Trade
3. Analysis
4. Performance
5. Trade Detail

Dashboard is default.

Wrap the app in SDK `CopilotShell`:
- `name="Trading Copilot"`
- `icon` should be compact and trading-specific.
- `tabs` should use stable ids.
- `iks` should come from trajectory/fingerprint when available or a safe default.

Header must include `PaperBadge`; because `CopilotShell` owns its internal header, place `PaperBadge` in the first visible content row or a compact app header band directly inside `CopilotShell`.

## 8. Dashboard Contract

Fetch in parallel on screen load:
- `getAnalytics()`
- `getHistory()`
- `getTradeMetadata()`
- `getMarketSnapshot()`

After metadata/analytics are available, fetch ticker data for open trades, including open seed positions where trade metadata exposes tickers.

Render:
- `PortfolioSummary`
- `PortfolioConcentration`
- `CalendarHeatmap`
- `ThesisBreakdown`
- SDK `DecisionHistory` using `TradeCard`
- `Log New Trade` button

Interactions:
- `TradeCard` click sets active trade ID and opens Trade Detail.
- `Log New Trade` switches to Log Trade tab.

## 9. Log Trade Contract

Screen sections:
1. `TickerLookup` with `PriceSparkline`.
2. Direction, thesis type, category, timeframe.
3. `ResearchChecklist`.
4. `PositionSizer` with exposure and R:R.
5. Conviction rating.
6. `Score This Trade`.

After score:
1. `EngineAssessment`
2. `SimilarTradesPanel`
3. SDK `ScoreResultCard`

Confirm flow:
- `ScoreResultCard.onConfirm` calls `learnTrade`.
- Show reward line from `LearnResponse`.
- Save rich trade metadata with `saveTradeMetadata`.
- Show optional centroid delta only if the backend supplies enough data.

Factor mapping:
- `research_depth = checked_count / 5`
- `conviction = conviction / 5`
- `technical_signal` computed from ticker `above_50ma`, `rsi`, and `change_30d_pct`
- `position_size = min(exposure_pct / 100, 1)`
- `time_horizon`: `intraday=0.1`, `swing=0.4`, `position=0.7`, `long=0.9`
- `market_regime` from SPY/VIX market snapshot context.

`action_taken` should be the recommended or overridden action: `buy`, `hold`, or `sell`.

## 10. Analysis Contract

Exact rendering order:
1. `ContrastCard` first and visually dominant.
2. `ProfileArchetype`.
3. SDK `FingerprintPanel`.
4. `CounterfactualCard`.
5. `DayOfWeekChart`.
6. `ResearchImpactChart`.
7. `RegimeChart`.
8. `RiskManagementCard`.

`ContrastCard`:
- Use exact analytics curves if present.
- Otherwise derive approximate diverging curves from aggregate `aligned`, `neutral`, and `misaligned` stats.
- Recharts is allowed.

`ProfileArchetype`:
- Derive from analytics narrative: high research wins, conviction noisy, Mondays weak, Thursdays strong, crypto and mean reversion weaker, stops helpful.
- Keep wording grounded in available analytics values.

## 11. Performance Contract

Render:
- Summary stats from `analytics.portfolioSummary`.
- SDK `TrajectoryChart`.
- `RollingMetrics` from `rolling_10`.
- `CategoryPerformance` from `portfolio_concentration` and/or `category_counts`.
- `RiskManagementCard`.

Trajectory normalization:
- Convert backend `trajectory` response to SDK `TrajectoryPoint[]`.
- Use safe empty state when no points are available.
- Current IKS and current win rate should be derived from trajectory when possible, otherwise analytics summary.

## 12. Trade Detail Contract

Render:
- Back to Dashboard button.
- Full trade review from joined trade, metadata, and ticker data.
- Factor bars in canonical Trading order.
- Research checklist display.
- Entry, exit, stop, target, R:R, exposure, P&L, outcome, reward if available.
- Similar trades link/action can re-query with the trade factors and show `SimilarTradesPanel`.

If no active trade is selected, show an empty state with a return-to-dashboard action.

## 13. Visual And UX Constraints

Theme:
- Red accent in `theme.css`.
- Desktop-first layouts with responsive fallback.
- Use existing SDK CSS variables where possible.
- Avoid one-note palette; red should be an accent, not the entire UI.

Workflow:
- Research checklist is core UI, not a secondary detail.
- Engine assessment must appear before similar trades.
- Similar trades must appear before confirmation.
- Paper badge must be visible in the app header area.
- No localStorage/sessionStorage.
- No fake backend fixture generation in the frontend.
- Empty states may be used when endpoints return empty/default payloads.

Component guidance:
- Use charts for analytics comparisons where they improve scanning.
- Keep cards compact and operational, not landing-page styled.
- Text must fit in buttons/cards at desktop and mobile widths.

## 14. Implementation Sequence

1. Replace `types.ts` and `api.ts`.
2. Add `theme.css` tokens and layout utility classes.
3. Build app shell in `main.tsx` and `App.tsx`.
4. Build dashboard components and `DashboardScreen`.
5. Build trade form components and `LogTradeScreen`.
6. Build analytics components and `AnalysisScreen`.
7. Build performance screen.
8. Build trade detail screen.
9. Run typecheck/build and fix strict TypeScript issues.
10. Run backend/root Python tests to verify no accidental backend/core impact.

## 15. Validation Commands

From `apps/trading/frontend`:
```powershell
npm install
npx tsc --noEmit
npm run build
```

From repo root:
```powershell
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -v --timeout=120
```

Do not start live Vite or Playwright unless the user confirms.

## 16. Residual Risks And Mitigations

- SDK prop shapes may evolve; re-read `copilot_sdk/frontend/*.tsx` immediately before implementation.
- Backend history response shape may not contain all seed v2 fields; join with metadata and render missing values as empty states.
- `ScoreResultCard` owns its own confirmed state, so reward display may need to be passed after `learnTrade` resolves or rendered adjacent to the card.
- Package/config changes should be avoided; if import resolution from `copilot_sdk/frontend` fails, prove the issue before requesting a minimal config change.
- Do not assume analytics has chart-ready curves; derive conservative chart data from aggregate stats when exact curves are absent.
