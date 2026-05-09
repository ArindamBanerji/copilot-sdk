# Trading Copilot Frontend Implementation Plan

## 1. Executive Summary

Build the Trading Copilot frontend under `apps/trading/frontend` as a standalone React/Vite/TypeScript app. The app will use SDK shared frontend components from `copilot_sdk/frontend` through relative imports, while all trading-specific screens, labels, copy, and UI behavior stay inside `apps/trading/frontend`.

The frontend will talk to the existing Trading backend under `apps/trading/backend`, using the SDK scoring endpoints mounted at `/api` and app context endpoints mounted at `/api/context`. The Trading app will override SDK theme variables with a red accent in `src/theme.css`.

No SDK shared component, SDK backend, SDK scoring, or Trading backend files should be edited for this frontend implementation.

## 2. Source Contracts from Prompt 0

### SDK Component Prop Interfaces

The SDK component barrel exports all shared components and prop types from `copilot_sdk/frontend/index.ts`:

- `IKSBadge`, `IKSBadgeProps`
- `CopilotShell`, `CopilotShellProps`, `CopilotShellTab`
- `DecisionHistory`, `DecisionHistoryProps`
- `FingerprintPanel`, `FactorItem`, `FingerprintCategory`, `FingerprintPanelProps`
- `TrajectoryChart`, `Annotation`, `TrajectoryChartProps`, `TrajectoryPoint`
- `ScoreResultCard`, `CentroidDelta`, `RewardLine`, `ScoreResult`, `ScoreResultCardProps`
- `EvolutionPanel`, `EvolutionPanelProps`, `EvolutionVariant`
- `ConservationSlider`, `ConservationSliderProps`

Key prop shapes to preserve:

- `CopilotShellProps`: `name`, `icon`, `tabs`, `activeTab`, `onTabChange`, `iks`, `iksDelta`, `children`.
- `DecisionHistoryProps<T>`: `decisions`, `renderCard`, optional `title`, `emptyMessage`, `maxVisible`.
- `ScoreResultCardProps`: `result`, `onConfirm`, `onOverride`, optional `iksDelta`, `rewardLine`, `centroidDelta`.
- `ScoreResult`: camelCase fields including `decisionId`, `actionIndex`, `actionNames`, `action`, `confidence`, `probabilities`, `category`, optional `factors`.
- `RewardLine`: `reward`, optional `previousReward`, optional `rewardMultiplier`.
- `CentroidDelta`: `value`, optional `beforeLabel`, optional `afterLabel`.
- `FingerprintPanelProps`: `factors`, optional `signalLabel`, `noiseLabel`, `perCategoryPrecision`, `decisionsAnalyzed`.
- `FactorItem`: `name`, `displayName`, `weight`, `sigma`, `interpretation`, optional `category`.
- `TrajectoryChartProps`: `points`, `currentIks`, `currentWinRate`, optional `switchingCostLine`, optional `annotations`, `narrative`, `decisionsTotal`, `daysActive`.
- `TrajectoryPoint`: `decisions`, `iks`, `winRate`.
- `IKSBadgeProps`: `value`, optional `delta`, optional `size`.

### Trading Backend Response Shapes

SDK scoring endpoints are mounted under `/api` by the Trading backend:

- `POST /api/score` returns snake_case backend fields: `decision_id`, `action`, `action_index`, `confidence`, `probabilities`, `category`, `factors`, `engine`.
- `POST /api/learn` returns `decision_id`, `iks_before`, `iks_after`, `centroid_delta`, `decisions_total`, `outcome`, `reward`, `previous_reward`, `reward_multiplier`, `engine`.
- `GET /api/fingerprint` returns `factors`, `overall_win_rate`, `per_category_precision`, `decisions_analyzed`, `engine`.
- `GET /api/trajectory` returns trajectory data with snake_case fields, including `current_iks`, `current_win_rate`, `decisions_total`, `days_active`, and point `win_rate`.
- `GET /api/history` returns `engine` and `decisions`.

Trading context endpoints are mounted under `/api/context`:

- `GET /api/context/market-snapshot` returns cached SPY/VIX/sector/source market context.
- `GET /api/context/ticker/{ticker}` returns known ticker cache entries or an unknown shape with `source: "unknown"` and `price: null`.
- `GET /api/context/portfolio-summary` returns cached portfolio summary fields such as total trades, win rate, best/worst category, exposure, cash buffer, and source.
- `POST /api/context/trade-metadata` stores metadata keyed by `decision_id`.
- `GET /api/context/trade-metadata` returns all metadata.

### Trading Preset Contract

Categories:

- `equity_long`
- `equity_short`
- `crypto_spot`
- `options`
- `etf`

Actions:

- `buy`
- `hold`
- `sell`

Factors:

- `conviction`
- `research_depth`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`

### SDK Frontend Tooling Pattern

The SDK frontend package uses React, ReactDOM, Recharts, Vite, TypeScript, Tailwind, PostCSS, and Autoprefixer. Scripts are:

- `typecheck`: `tsc --noEmit`
- `build`: `tsc --noEmit && vite build`
- `dev`: `vite --host 127.0.0.1 --port 5174`

The Trading frontend should copy/adapt this pattern. Because the Trading app will have its own `node_modules` and imports SDK components that use Recharts, the Trading app package must include `recharts` directly.

### Relative Import Path

Direct imports from Trading app files to SDK shared components should use:

- From `apps/trading/frontend/src/App.tsx`: `../../../../copilot_sdk/frontend`
- From `apps/trading/frontend/src/screens/*.tsx`: `../../../../../copilot_sdk/frontend`
- From `apps/trading/frontend/src/components/*.tsx`: `../../../../../copilot_sdk/frontend`

Implementation should keep imports consistent and avoid adding SDK wrapper files unless a later prompt explicitly expands allowed files.

## 3. Files to Create

- `apps/trading/frontend/package.json`
- `apps/trading/frontend/vite.config.ts`
- `apps/trading/frontend/tsconfig.json`
- `apps/trading/frontend/tailwind.config.js`
- `apps/trading/frontend/postcss.config.js`
- `apps/trading/frontend/index.html`
- `apps/trading/frontend/src/main.tsx`
- `apps/trading/frontend/src/App.tsx`
- `apps/trading/frontend/src/theme.css`
- `apps/trading/frontend/src/api.ts`
- `apps/trading/frontend/src/screens/JournalScreen.tsx`
- `apps/trading/frontend/src/screens/LogTradeScreen.tsx`
- `apps/trading/frontend/src/screens/InsightScreen.tsx`
- `apps/trading/frontend/src/screens/CurveScreen.tsx`
- `apps/trading/frontend/src/components/TradeCard.tsx`
- `apps/trading/frontend/src/components/MarketContext.tsx`
- `apps/trading/frontend/src/components/TradeTicketForm.tsx`

## 4. Forbidden Files

Do not modify:

- `copilot_sdk/frontend/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/scoring/**`
- `apps/trading/backend/**`
- `apps/purchasing/**`
- `apps/dataops/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`
- Git metadata or repository history.

## 5. Package / Tooling Contract

Create a standalone React/Vite/TypeScript package under `apps/trading/frontend`.

`package.json` requirements:

- dependencies/dev dependencies must include React, ReactDOM, Recharts, Vite, `@vitejs/plugin-react`, TypeScript, React types, Tailwind, PostCSS, and Autoprefixer.
- include `recharts` directly because imported SDK shared components depend on it.
- scripts:
  - `typecheck`: `tsc --noEmit`
  - `build`: `tsc --noEmit && vite build`
  - `dev`: `vite --host 127.0.0.1 --port 5174`

Tailwind/PostCSS:

- Copy/adapt the SDK frontend Tailwind/PostCSS pattern.
- Tailwind content should scan:
  - `./index.html`
  - `./src/**/*.{ts,tsx}`
  - `../../../copilot_sdk/frontend/*.{ts,tsx}`
- This is required because the app compiles SDK TSX components from source.

API base:

- Use `import.meta.env.VITE_API_URL || "http://localhost:8010"`.
- Do not hardcode backend ports elsewhere.

Side effects:

- No `localStorage`.
- No `sessionStorage`.
- No backend fetches from SDK shared components.
- No SDK source edits.

## 6. App / Tab Contract

`src/App.tsx` should wrap the app in `CopilotShell`.

Tabs:

- `journal` -> Journal, default active tab.
- `log` -> Log Trade.
- `insight` -> Insight.
- `curve` -> Curve.

Shell props:

- `name`: `Trading Copilot`
- `icon`: a compact trading glyph or text symbol such as `$`
- `tabs`: the four tabs above.
- `activeTab`: local React state.
- `onTabChange`: local setter.
- `iks`: current IKS from trajectory state, with a safe default before data loads.
- `iksDelta`: derived from learn/trajectory state when available.

The Trading app may use trading-specific copy and labels. SDK shared components must remain read-only and domain-agnostic.

## 7. API Client Contract

Implement `src/api.ts`:

- `const BASE = import.meta.env.VITE_API_URL || "http://localhost:8010";`
- `apiGet<T>(path: string): Promise<T>`
- `apiPost<T>(path: string, body: unknown): Promise<T>`
- throw a descriptive `Error` on non-OK responses.
- try to parse backend error JSON when available.
- no global fetch monkeypatching.
- no localStorage/sessionStorage.

The API layer should include small mapping helpers where useful:

- backend score response snake_case -> SDK `ScoreResult` camelCase.
- backend learn response snake_case -> SDK `RewardLine`, `iksDelta`, and optional `CentroidDelta`.
- backend trajectory response snake_case -> SDK `TrajectoryChartProps` fields.

## 8. Journal Contract

`JournalScreen.tsx` should:

- fetch `/api/history` on mount.
- fetch `/api/context/trade-metadata` on mount.
- join records by `decision_id`.
- render `DecisionHistory` with `TradeCard`.
- include a `+ Log New Trade` button that switches active tab to Log Trade.
- show empty message `No trades logged yet.`
- fail open with a readable error and empty state rather than crashing.

The history response should be treated defensively because storage fields may vary. Use `decision_id`, `category`, `confidence`, `created_at`, `outcome`, and action fields when present, with fallbacks.

## 9. TradeCard Contract

`TradeCard.tsx` props:

- `trade`: history decision object.
- `metadata`: optional trade metadata object.

Behavior:

- show ticker from `metadata.ticker`, falling back to trade category.
- show direction icon from `metadata.direction`.
- show relative time from `created_at` when available.
- show confidence as a percentage when available.
- show outcome icon/state for correct, incorrect, or pending.
- show research and conviction dot indicators from metadata values `1` through `5`.
- left border should reflect outcome state.
- use CSS variables and Trading theme classes.

## 10. Log Trade Contract

`LogTradeScreen.tsx` and `TradeTicketForm.tsx` should implement the trading ticket flow.

Form state:

- `ticker`
- `direction`
- `category`
- `research`
- `conviction`
- `horizon`
- `thesis`

Market context:

- fetch `/api/context/market-snapshot`.
- render the compact context bar through `MarketContext`.

Factor mapping must exactly match TradingPreset:

- `conviction`: conviction slider `1..5` mapped to `0.2..1.0` by `value / 5`.
- `research_depth`: research slider `1..5` mapped to `0.2..1.0` by `value / 5`.
- `technical_signal`: hidden default `0.5`.
- `position_size`: hidden default `0.3`.
- `time_horizon`: `day -> 0.1`, `swing -> 0.4`, `long -> 0.8`.
- `market_regime`: from SPY change:
  - `> 0.2` -> `0.7`
  - `< -0.2` -> `0.3`
  - otherwise -> `0.5`

Submit flow:

- `POST /api/score` with `category` and mapped `factors`.
- map response to SDK `ScoreResult`:
  - `decision_id` -> `decisionId`
  - `action_index` -> `actionIndex`
  - `actionNames`: `["buy", "hold", "sell"]`
  - preserve `action`, `confidence`, `probabilities`, `category`, `factors`.
- after score succeeds, `POST /api/context/trade-metadata` with `decision_id`, `ticker`, `direction`, `thesis`, `research`, `conviction`, and `horizon`.
- show `ScoreResultCard` inline.

Confirm/override flow:

- `onConfirm(decisionId)` posts `/api/learn` with `decision_id`, `actual_action` from the recommended action, and outcome `confirmed`.
- `onOverride(decisionId, action)` posts `/api/learn` with the selected override action and outcome `overridden`.
- construct `RewardLine` from learn response:
  - `reward` -> `reward`
  - `previous_reward` -> `previousReward`
  - `reward_multiplier` -> `rewardMultiplier`
- construct `iksDelta` from `iks_after - iks_before` when both are numeric.
- construct `CentroidDelta` only when `centroid_delta` is present, using labels such as `Before` and `After`; omit otherwise.
- do not call backend from `ScoreResultCard` itself; backend calls live in the Trading app screen/component.

## 11. MarketContext Contract

`MarketContext.tsx` should:

- accept the backend market snapshot shape.
- render a compact SPY/VIX/sector bar.
- include source/cached state when useful.
- use CSS variables and app theme styles.
- avoid hardcoded business logic beyond displaying the backend snapshot.

## 12. Insight Contract

`InsightScreen.tsx` should:

- fetch `/api/fingerprint`.
- map returned factors into SDK `FactorItem[]`.
- pass `per_category_precision` to `perCategoryPrecision`.
- pass `decisions_analyzed` to `decisionsAnalyzed`.
- use trading-specific display names and interpretations only in this app-specific screen.

Factor display names:

- `conviction` -> `Conviction`
- `research_depth` -> `Research depth`
- `technical_signal` -> `Technical signal`
- `position_size` -> `Position size`
- `time_horizon` -> `Time horizon`
- `market_regime` -> `Market regime`

Use `FingerprintPanel` with trading-specific `signalLabel` and `noiseLabel` props. Loading, empty, and error states should be safe and readable.

## 13. Curve Contract

`CurveScreen.tsx` should:

- fetch `/api/trajectory`.
- map backend snake_case response to SDK `TrajectoryChartProps`:
  - `current_iks` -> `currentIks`
  - `current_win_rate` -> `currentWinRate`
  - `decisions_total` -> `decisionsTotal`
  - `days_active` -> `daysActive`
  - point `win_rate` -> `winRate`
- use `switchingCostLine={67}`.
- provide a trading narrative that references `decisionsTotal`.
- render safe loading, empty, and error states.
- render no chart if points are absent; let `TrajectoryChart` handle the empty state when possible.

## 14. Validation Commands

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

Do not leave a Vite dev server running during automated validation.

## 15. Manual Smoke

Manual smoke is optional after build validation:

1. Start the Trading backend on port `8010` using the app's backend instructions.
2. Start the frontend:

```powershell
cd apps/trading/frontend
npm run dev
```

3. Open the Vite URL.
4. Verify:
   - Journal loads and handles empty/history states.
   - Log Trade submits a score request.
   - Score result renders probabilities and recommended action.
   - Confirm sends learn and reveals reward/IKS delta.
   - Insight renders fingerprint data.
   - Curve renders trajectory data or safe empty state.

## Prompt Verification Pass

- Prompt 0 supplied actual SDK component props and backend response shapes.
- This plan does not require SDK component, SDK backend, SDK scoring, or Trading backend edits.
- Factor mapping exactly matches TradingPreset factor names.
- The package contract includes `recharts` directly.
- Tailwind/PostCSS are copied/adapted from the SDK frontend pattern.
- Validation includes frontend install/typecheck/build plus SDK root and Trading backend tests.
- Trading-specific screens stay inside `apps/trading/frontend`; SDK shared components remain domain-agnostic.
