# copilot-sdk Frontend Shared Components Plan

## 1. Executive Summary

Create `copilot_sdk/frontend` as a standalone React/Vite preview package for shared copilot UI components.

The package will provide eight reusable, domain-agnostic, props-driven components:

- `IKSBadge`
- `CopilotShell`
- `FingerprintPanel`
- `TrajectoryChart`
- `ScoreResultCard`
- `DecisionHistory`
- `EvolutionPanel`
- `ConservationSlider`

Domain apps will import these components by relative path for Loom. Components must not fetch from backends, import Python/backend code, or contain hardcoded Trading/Purchasing/DataOps/SOC content. The Vite preview page is the acceptance harness and may use mock domain data to demonstrate all components.

This is an approved frontend expansion of the SDK scope. `CLAUDE.md` currently describes the SDK as having "No UI", so this plan intentionally confines UI work to `copilot_sdk/frontend` and keeps backend/scoring protocols untouched.

## 2. Source Contracts from Prompt 0

### Repo and Tooling State

- `copilot_sdk/frontend` exists but is empty.
- No root `package.json` was found.
- No frontend `package.json` was found.
- No Vite, TypeScript, Tailwind, or PostCSS config was found.
- Python package config is `pyproject.toml`; frontend tooling should stay local to `copilot_sdk/frontend`.
- Backend router baseline passed in discovery: `python -m pytest tests\backend -q --timeout=120` returned `25 passed`.

### CLAUDE.md Rules

- Ground claims in source.
- Keep changes surgical.
- Verify after changes.
- Do not use git.
- SDK boundary discipline remains important: do not import from app-specific SOC/S2P/domain internals.
- `CLAUDE.md` says the SDK has "No UI"; this plan treats frontend work as a separately approved package slice under `copilot_sdk/frontend`.

### Backend Field Shapes for Props and Mock Data

These shapes are used only for TypeScript prop definitions and preview mock data. Frontend components must not import backend modules or fetch.

#### Score

`POST /score` returns:

- `decision_id: string`
- `action: string`
- `action_index: number`
- `confidence: number`
- `probabilities: number[]`
- `category: string`
- `factors: Record<string, number>`
- `engine`

#### Learn / Reward

`POST /learn` returns:

- `decision_id: string`
- `iks_before: number`
- `iks_after: number`
- `centroid_delta: number`
- `decisions_total: number`
- `outcome: string`
- `reward: number`
- `previous_reward: number | null`
- `reward_multiplier: number`
- `engine`

#### Fingerprint

`GET /fingerprint` returns:

- `factors: Array<{ name: string; sigma: number; weight: number; interpretation: string }>`
- `overall_win_rate: number`
- `per_category_precision: Record<string, number>`
- `decisions_analyzed: number`
- `engine`

#### Trajectory

`GET /trajectory` returns:

- `points: Array<{ decisions: number; iks: number; win_rate: number; timestamp: number }>`
- `current_iks: number`
- `current_win_rate: number`
- `decisions_total: number`
- `days_active: number`
- `engine`

#### History

`GET /history` returns:

- `decisions: Array<Record<string, unknown>>`
- `engine`

Decision rows may include:

- `decision_id`
- `domain`
- `category`
- `recommended_action`
- `recommended_index`
- `confidence`
- `probabilities`
- `factors`
- `factor_vector`
- `created_at`

#### Conservation

`GET /conservation/status` returns:

- `engine`
- `domain`
- `verified_count`
- `correct_count`
- `total_decisions`
- `penalty_ratio`
- `signal`
- `theta_min`
- `headroom`
- `status`
- `passed`

`POST /conservation/what-if` returns:

- `engine`
- `domain`
- `inputs: { alpha: number; q: number; V: number; theta_min: number | null }`
- `signal`
- `theta_min`
- `headroom`
- `status`
- `passed`

#### Evolution

`GET /evolution/variants` returns:

- `engine`
- `domain`
- `variants: Array<{ id; variant_id; event_type; artifact_type; description; impact; magnitude; timestamp; timestamp_epoch; metadata }>`

`GET /evolution/patterns` returns:

- `engine`
- `domain`
- `patterns: Array<{ variant_id; source_copilot; source_rule; warm_start_prior; artifact_type; description }>`
- `summary: { variants_generated; variants_promoted; variants_rejected; variants_rolled_back; shadow_batches; shadow_started; by_artifact_type; avg_shadow_win_rate; total_shadow_decisions }`

## 3. Files to Create

Core required files:

- `copilot_sdk/frontend/package.json`
- `copilot_sdk/frontend/tsconfig.json`
- `copilot_sdk/frontend/vite.config.ts`
- `copilot_sdk/frontend/index.html`
- `copilot_sdk/frontend/copilot-theme.css`
- `copilot_sdk/frontend/IKSBadge.tsx`
- `copilot_sdk/frontend/CopilotShell.tsx`
- `copilot_sdk/frontend/FingerprintPanel.tsx`
- `copilot_sdk/frontend/TrajectoryChart.tsx`
- `copilot_sdk/frontend/ScoreResultCard.tsx`
- `copilot_sdk/frontend/DecisionHistory.tsx`
- `copilot_sdk/frontend/EvolutionPanel.tsx`
- `copilot_sdk/frontend/ConservationSlider.tsx`
- `copilot_sdk/frontend/index.ts`
- `copilot_sdk/frontend/preview.tsx`

Allowed if needed for Tailwind/Vite:

- `copilot_sdk/frontend/tailwind.config.js`
- `copilot_sdk/frontend/postcss.config.js`

## 4. Forbidden Files

Do not modify:

- `copilot_sdk/backend/**`
- `copilot_sdk/scoring/**`
- `apps/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`
- root package/build config files outside `copilot_sdk/frontend`

## 5. Design Tokens Contract

`copilot-theme.css` must define CSS custom properties for:

- surface colors:
  - `--copilot-bg`
  - `--copilot-surface`
  - `--copilot-surface-muted`
  - `--copilot-border`
- primary/accent:
  - `--copilot-primary`
  - `--copilot-primary-contrast`
  - `--copilot-accent`
- semantic colors:
  - `--copilot-success`
  - `--copilot-warning`
  - `--copilot-danger`
  - `--copilot-info`
- text colors:
  - `--copilot-text`
  - `--copilot-text-muted`
  - `--copilot-text-subtle`
- spacing:
  - `--copilot-space-1`
  - `--copilot-space-2`
  - `--copilot-space-3`
  - `--copilot-space-4`
  - `--copilot-space-6`
  - `--copilot-space-8`
- typography:
  - `--copilot-font-sans`
  - `--copilot-font-mono`
  - `--copilot-text-xs`
  - `--copilot-text-sm`
  - `--copilot-text-base`
  - `--copilot-text-lg`
  - `--copilot-text-xl`
- radii:
  - `--copilot-radius-sm`
  - `--copilot-radius-md`
  - `--copilot-radius-lg`
- shadows:
  - `--copilot-shadow-sm`
  - `--copilot-shadow-md`
- fingerprint colors:
  - `--copilot-fingerprint-clean`
  - `--copilot-fingerprint-moderate`
  - `--copilot-fingerprint-noisy`
  - `--copilot-fingerprint-insufficient`
- chart colors:
  - `--copilot-chart-iks`
  - `--copilot-chart-win-rate`
  - `--copilot-chart-grid`

Components should use CSS variables for colors. Tailwind utilities may be used for spacing, layout, and responsive behavior.

## 6. Component Contracts

### IKSBadge

Props:

```ts
export interface IKSBadgeProps {
  value: number;
  label?: string;
  size?: "sm" | "md" | "lg";
  showInterpretation?: boolean;
  className?: string;
}
```

Behavior:

- Displays an Institutional Knowledge Score.
- Clamps display to `[0, 100]`.
- Shows an interpretation band when requested.
- Domain-agnostic label defaults to `IKS`.

### CopilotShell

Props:

```ts
export interface CopilotShellProps {
  title: string;
  subtitle?: string;
  domainLabel?: string;
  iks?: number;
  actions?: React.ReactNode;
  sidebar?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}
```

Behavior:

- Provides a desktop-first app frame.
- Optional sidebar and header actions.
- May render `IKSBadge` when `iks` is provided.
- Does not include navigation labels tied to any specific domain.

### FingerprintPanel

Props:

```ts
export interface FactorFingerprint {
  name: string;
  sigma: number;
  weight: number;
  interpretation: string;
}

export interface FingerprintPanelProps {
  factors: FactorFingerprint[];
  overallWinRate?: number;
  decisionsAnalyzed?: number;
  perCategoryPrecision?: Record<string, number>;
  title?: string;
  className?: string;
}
```

Behavior:

- Lists factors with sigma, weight, and interpretation.
- Uses fingerprint token colors by interpretation.
- Handles empty/insufficient data states.
- Does not hardcode factor names.

### TrajectoryChart

Props:

```ts
export interface TrajectoryPoint {
  decisions: number;
  iks: number;
  win_rate: number;
  timestamp?: number;
}

export interface TrajectoryChartProps {
  points: TrajectoryPoint[];
  currentIks?: number;
  currentWinRate?: number;
  decisionsTotal?: number;
  daysActive?: number;
  title?: string;
  className?: string;
}
```

Behavior:

- Uses Recharts only in this component.
- Displays IKS and win-rate trajectory.
- Handles empty point arrays.
- Uses chart color tokens.

### ScoreResultCard

Props:

```ts
export interface ScoreResultCardProps {
  decisionId: string;
  action: string;
  actionIndex?: number;
  confidence: number;
  probabilities?: number[];
  category: string;
  factors?: Record<string, number>;
  reward?: number;
  previousReward?: number | null;
  rewardMultiplier?: number;
  title?: string;
  className?: string;
}
```

Behavior:

- Shows the recommended action, category, confidence, and optional probabilities.
- Shows reward fields when provided.
- Does not assume action names or domain categories.

### DecisionHistory

Props:

```ts
export interface DecisionHistoryItem {
  decision_id: string;
  category?: string;
  recommended_action?: string;
  confidence?: number;
  created_at?: number;
  [key: string]: unknown;
}

export interface DecisionHistoryProps {
  decisions: DecisionHistoryItem[];
  title?: string;
  emptyLabel?: string;
  className?: string;
}
```

Behavior:

- Renders a compact table/list of decisions.
- Handles empty state.
- Does not assume domain-specific columns beyond common decision fields.

### EvolutionPanel

Props:

```ts
export interface EvolutionVariant {
  id?: string;
  variant_id?: string;
  event_type?: string;
  artifact_type?: string;
  description?: string;
  impact?: string;
  magnitude?: number;
  timestamp?: string;
  timestamp_epoch?: number;
  metadata?: Record<string, unknown>;
}

export interface EvolutionPattern {
  variant_id?: string;
  source_copilot?: string;
  source_rule?: string;
  warm_start_prior?: Record<string, unknown>;
  artifact_type?: string;
  description?: string;
}

export interface EvolutionSummary {
  variants_generated?: number;
  variants_promoted?: number;
  variants_rejected?: number;
  variants_rolled_back?: number;
  shadow_batches?: number;
  shadow_started?: number;
  by_artifact_type?: Record<string, number>;
  avg_shadow_win_rate?: number;
  total_shadow_decisions?: number;
}

export interface EvolutionPanelProps {
  variants?: EvolutionVariant[];
  patterns?: EvolutionPattern[];
  summary?: EvolutionSummary;
  title?: string;
  className?: string;
}
```

Behavior:

- Shows evolution variants and patterns in domain-neutral language.
- Handles empty state.
- Does not hardcode artifact names.

### ConservationSlider

Props:

```ts
export interface ConservationStatus {
  signal?: number | null;
  theta_min?: number | null;
  headroom?: number | null;
  status?: string;
  passed?: boolean;
}

export interface ConservationSliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  status?: ConservationStatus;
  onChange?: (value: number) => void;
  className?: string;
}
```

Behavior:

- Controlled slider for what-if inputs.
- Displays conservation status/headroom when provided.
- Does not perform API calls.

## 7. Domain-Agnostic Rules

- No hardcoded Trading/Purchasing/DataOps/SOC labels in reusable components.
- Domain-specific text is allowed only in `preview.tsx` mock data or props passed into components.
- No `fetch`, `XMLHttpRequest`, websocket, backend imports, or Python imports.
- No `localStorage` or `sessionStorage`.
- No external fonts.
- Use CSS variables for component colors.
- Use Recharts only in `TrajectoryChart`.
- Every component should have a default export.
- Prop and data types should be named exports.
- `index.ts` should barrel-export every component and type.

## 8. Implementation Sequence

### Prompt 2: Base Components

Create:

- package tooling:
  - `package.json`
  - `tsconfig.json`
  - `vite.config.ts`
  - `index.html`
  - `tailwind.config.js`
  - `postcss.config.js`
- design tokens:
  - `copilot-theme.css`
- components:
  - `IKSBadge.tsx`
  - `CopilotShell.tsx`
  - `DecisionHistory.tsx`
  - `FingerprintPanel.tsx`
- partial barrel:
  - `index.ts`

Validation after Prompt 2:

- `npm install`
- `npx tsc --noEmit`
- `npm run build` if a script exists
- `python -m pytest tests/ -q --timeout=120`

### Prompt 3: Remaining Components and Preview

Create/update:

- `TrajectoryChart.tsx`
- `ScoreResultCard.tsx`
- `EvolutionPanel.tsx`
- `ConservationSlider.tsx`
- `preview.tsx`
- final `index.ts`

Preview must render all 8 components with mock data and import `copilot-theme.css`.

Validation after Prompt 3:

- `npx tsc --noEmit`
- `npm run build`
- `python -m pytest tests/ -q --timeout=120`

Do not keep `vite` running in Codex. A manual preview command can be documented but should only be started if requested.

## 9. Validation Commands

From `copilot_sdk/frontend`:

```powershell
npm install
npx tsc --noEmit
npm run build
```

From repo root:

```powershell
python -m pytest tests/ -q --timeout=120
```

Optional manual preview, only when requested:

```powershell
cd copilot_sdk/frontend
npx vite --host 127.0.0.1 --port 5174
```

## 10. Open Risks / Decisions

- Tailwind config is required if implementation uses Tailwind utilities. Keep it frontend-local.
- Vite preview should not run persistently in Codex.
- Recharts type compatibility should be validated by `npx tsc --noEmit` and `npm run build`.
- Domain-specific text in preview mock data is allowed; it is not allowed inside reusable components.
- The SDK scope note in `CLAUDE.md` says "No UI"; this plan assumes the user’s task explicitly authorizes `copilot_sdk/frontend` as a scoped standalone package.
- There is no existing frontend package manager setup, so implementation must create frontend-local tooling without touching root package config.
