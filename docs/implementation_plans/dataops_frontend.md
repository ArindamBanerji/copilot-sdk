# DataOps Copilot Frontend Implementation Plan

## 1. Executive Summary

Build the DataOps Copilot frontend under `apps/dataops/frontend`.

DataOps is the enterprise-tier copilot UI. It should emphasize graph visibility, autonomous AgentEvolver behavior, conservation what-if controls, and audit evidence. The app uses shared SDK frontend components through relative imports from `../../../copilot_sdk/frontend` and keeps DataOps-specific screens, API wrappers, types, and components inside `apps/dataops/frontend`.

No backend or SDK files are part of this rebuild. The backend contracts already exist under `apps/dataops/backend` and shared routers under `copilot_sdk/backend`.

## 2. Source Contracts From Prompt 0

### SDK Frontend Components

Use SDK components from `copilot_sdk/frontend/index.ts`.

`CopilotShell`
- Props: `name`, `icon`, `tabs`, `activeTab`, `onTabChange`, `iks`, optional `iksDelta`, `children`.
- DataOps app contract: `name="DataOps Copilot"`, `icon="DO"` or another short DataOps-safe symbol string, five tabs.

`ScoreResultCard`
- Props: `result`, `onConfirm`, `onOverride`, optional `iksDelta`, `rewardLine`, `centroidDelta`.
- `result` expects camelCase frontend fields: `decisionId`, `action`, `actionIndex`, `confidence`, `probabilities`, `category`, optional `factors`, `actionNames`.
- Backend scoring response is snake_case, so `api.ts` must normalize `decision_id` to `decisionId` and `action_index` to `actionIndex`.
- Do not pass `centroidDelta` unless a future DataOps prompt explicitly requires it.

`FingerprintPanel`
- Props: `factors`, optional `signalLabel`, `noiseLabel`, `perCategoryPrecision`, `decisionsAnalyzed`.
- Factor shape: `name`, `displayName`, `weight`, `sigma`, `interpretation`, optional `category`.

`TrajectoryChart`
- Props: `points`, `currentIks`, `currentWinRate`, optional `switchingCostLine`, optional `annotations`, `narrative`, `decisionsTotal`, `daysActive`.
- Backend trajectory is snake_case and must be normalized in `api.ts`.

`ConservationSlider`
- Props: `currentThreshold`, `conservationProduct`, `conservationThreshold`, `penaltyRatio`, `status`, `onDrag`, `narrative`.
- `status` is `GREEN`, `AMBER`, or `RED`.

`EvolutionPanel`
- Props: `variants`, optional `title`.
- SDK variant status values are `promoted`, `rejected`, `shadow`, `created`.
- Backend evolution variants use `event_type`, so `api.ts` must map `promotion_approved` to `promoted` and `promotion_rejected` to `rejected` for SDK display.

`IKSBadge`
- Props: `value`, optional `delta`, optional `size`.

### DataOps Backend Context And AE Responses

Base API default for this frontend: `http://localhost:8030`.

Context router:
- `GET /api/context/pipelines` returns `{ source, pipelines }`.
- `GET /api/context/alerts` returns `{ source, alerts }`.
- `GET /api/context/system/{name}` returns `{ source, system }` or `{ source, error, name }`.
- `GET /api/context/alert/{id}` returns `{ source, alert }` or `{ source, error, alert_id }`.
- `GET /api/context/alert/{id}/deps` returns blast radius data: `source`, `alert_id`, `system`, `affected_system`, `tree`, `downstream_tree`, `total_affected`, `max_criticality`, `min_sla`, `engine`.
- `GET /api/context/alert/{id}/recurrence` returns `source`, `alert_id`, `system`, `category`, `prior_count`, `recurrence_frequency`.
- `GET /api/context/alert/{id}/factors` returns `source`, `alert_id`, `factors`, `all_auto_computed`. Each factor has `value`, `source`, `detail`.
- `POST /api/context/alert-metadata` requires `decision_id` and returns `{ stored, decision_id, metadata }`.
- `GET /api/context/alert-metadata` returns `{ metadata }`.

AE router:
- `GET /api/ae/recommendation/{alert_id}` returns `alert_id`, `has_recommendation`, `recommendations`, `count`, `source`, `engine`.
- Only `promotion_approved` variants are eligible for recommendations.
- Recommendation fields include `id`, `variant_id`, `artifact_type`, `description`, `impact`, `confidence`, `match_reason`.
- `GET /api/ae/impact` returns `auto_resolved_count`, `accuracy`, `active_rules`, `rejected_rules`, `breakdown`, `rejected_example`, `engine`.
- `GET /api/ae/pattern-origin` returns `engine`, `source`, `narrative`, `chain`, `patterns`, `rejected`.
- `GET /api/ae/incident` returns `incident_id`, `title`, `estimated_cost`, `primary_alert_id`, `affected_systems`, `affected_datasets`, `fingerprint_insight`, `engine`.
- `GET /api/ae/conservation-history` returns `events` and `engine`. Events include `event_id`, `timestamp`, `requested_action`, `status`, `reason`, `metrics`.

Shared scoring router:
- `POST /api/score` request: `{ category, factors, context? }`.
- `POST /api/learn` request: `{ decision_id, actual_action, outcome, context? }`.
- `GET /api/fingerprint` returns `factors`, `overall_win_rate`, `per_category_precision`, `decisions_analyzed`, `engine`.
- `GET /api/trajectory` returns `points`, `current_iks`, `current_win_rate`, `decisions_total`, `days_active`, `engine`.
- `GET /api/history` returns `{ engine, decisions }` if needed later.

### Conservation Field Mapping

`GET /api/conservation/status` returns:
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

`POST /api/conservation/what-if` request:
- `alpha`
- `q`
- `V`
- optional `theta_min`

`POST /api/conservation/what-if` response:
- `engine`
- `domain`
- `inputs`
- `signal`
- `theta_min`
- `headroom`
- `status`
- `passed`

`ConservationSlider` mapping:
- `currentThreshold`: frontend-controlled slider value, initialized from `theta_min` when available or a safe default.
- `conservationProduct`: backend `signal`.
- `conservationThreshold`: backend `theta_min`.
- `penaltyRatio`: backend `penalty_ratio`.
- `status`: backend `status`.
- `onDrag`: calls `POST /api/conservation/what-if`, passing the dragged threshold as `theta_min` plus safe `alpha`, `q`, and `V` values derived from current state or defaults.

### DataOps Preset

Categories:
- `schema_change`
- `volume_anomaly`
- `quality_anomaly`
- `freshness_violation`
- `pipeline_failure`
- `transform_drift`

Actions:
- `auto_approve`
- `investigate`
- `escalate_to_owner`
- `pause_downstream`
- `refer_to_specialist`

Action display labels:
- Auto approve
- Investigate
- Escalate to owner
- Pause downstream
- Refer to specialist

Factors:
- `impact_scope`
- `source_reliability`
- `recurrence_frequency`
- `downstream_urgency`
- `data_freshness`
- `business_criticality`

Factor display labels:
- Impact scope
- Source reliability
- Recurrence frequency
- Downstream urgency
- Data freshness
- Business criticality

### Package And Config Pattern

Use the existing Trading/Purchasing frontend package pattern:
- React 18.
- ReactDOM.
- Recharts.
- Vite 6.
- TypeScript.
- Tailwind.
- PostCSS.
- `build`: `tsc --noEmit && vite build`.
- `typecheck`: `tsc --noEmit`.
- Tailwind content includes app source and SDK frontend: `../../../copilot_sdk/frontend/**/*.{ts,tsx}`.
- TypeScript includes `src` and `../../../copilot_sdk/frontend`.

## 3. Files To Create

Package/config:
- `apps/dataops/frontend/package.json`
- `apps/dataops/frontend/vite.config.ts`
- `apps/dataops/frontend/tsconfig.json`
- `apps/dataops/frontend/tailwind.config.js`
- `apps/dataops/frontend/postcss.config.js`
- `apps/dataops/frontend/index.html`

Core source:
- `apps/dataops/frontend/src/main.tsx`
- `apps/dataops/frontend/src/App.tsx`
- `apps/dataops/frontend/src/theme.css`
- `apps/dataops/frontend/src/api.ts`
- `apps/dataops/frontend/src/types.ts`

Screens:
- `apps/dataops/frontend/src/screens/DashboardScreen.tsx`
- `apps/dataops/frontend/src/screens/TriageScreen.tsx`
- `apps/dataops/frontend/src/screens/InsightScreen.tsx`
- `apps/dataops/frontend/src/screens/EvidenceScreen.tsx`
- `apps/dataops/frontend/src/screens/CurveScreen.tsx`

Components:
- `apps/dataops/frontend/src/components/PipelineGrid.tsx`
- `apps/dataops/frontend/src/components/AlertQueue.tsx`
- `apps/dataops/frontend/src/components/AlertCard.tsx`
- `apps/dataops/frontend/src/components/DependencyTree.tsx`
- `apps/dataops/frontend/src/components/FactorAutoFill.tsx`
- `apps/dataops/frontend/src/components/RecurrenceBadge.tsx`
- `apps/dataops/frontend/src/components/ActionPicker.tsx`
- `apps/dataops/frontend/src/components/AERecommendationBadge.tsx`
- `apps/dataops/frontend/src/components/AEImpactPanel.tsx`
- `apps/dataops/frontend/src/components/PatternOriginCard.tsx`
- `apps/dataops/frontend/src/components/ProfileArchetype.tsx`
- `apps/dataops/frontend/src/components/IncidentReplayCard.tsx`
- `apps/dataops/frontend/src/components/ConservationTimeline.tsx`
- `apps/dataops/frontend/src/components/DisruptionAnnotation.tsx`, only if useful.

## 4. Forbidden Files

Do not edit:
- `apps/dataops/backend/**`
- `copilot_sdk/frontend/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/scoring/**`
- `apps/trading/**`
- `apps/purchasing/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`

Do not use git operations.

## 5. Package / Tooling Contract

Create a React/Vite/TypeScript app.

`package.json`:
- `name`: `@copilot/dataops-frontend`
- `version`: `0.1.0`
- `private`: `true`
- `type`: `module`
- `scripts.typecheck`: `tsc --noEmit`
- `scripts.build`: `tsc --noEmit && vite build`
- `scripts.dev`: `vite --host 127.0.0.1 --port 5176`
- dependencies: `react`, `react-dom`, `recharts`
- devDependencies: `@types/react`, `@types/react-dom`, `@vitejs/plugin-react`, `autoprefixer`, `postcss`, `tailwindcss`, `typescript`, `vite`

`vite.config.ts`:
- Use `defineConfig`.
- Use React plugin.

`tsconfig.json`:
- Match Trading/Purchasing strict TypeScript pattern.
- Include `src` and `../../../copilot_sdk/frontend`.

`tailwind.config.js`:
- Content includes `./index.html`, `./src/**/*.{ts,tsx}`, and `../../../copilot_sdk/frontend/**/*.{ts,tsx}`.

`postcss.config.js`:
- Use `tailwindcss` and `autoprefixer`.

`index.html`:
- Root element `#root`.
- Module script `/src/main.tsx`.

## 6. API Client Contract

`apps/dataops/frontend/src/api.ts`:
- `BASE = import.meta.env.VITE_API_URL || "http://localhost:8030"`.
- Implement `apiGet` and `apiPost` with non-OK errors.
- Centralize snake_case to camelCase normalization in `api.ts`; do not scatter backend-shape normalization in components.
- No `localStorage` or `sessionStorage`.

Required API functions:
- `getHealth()`
- `getPipelines()`
- `getAlerts()`
- `getAlert(id: string)`
- `getAlertDeps(id: string)`
- `getAlertRecurrence(id: string)`
- `getAlertFactors(id: string)`
- `getAeRecommendation(alertId: string)`
- `getAeImpact()`
- `getPatternOrigin()`
- `getIncident()`
- `getConservationHistory()`
- `getConservationStatus()`
- `postConservationWhatIf(body)`
- `scoreAlert(body)`
- `learnAlert(body)`
- `saveAlertMetadata(body)`
- `getFingerprint()`
- `getTrajectory()`
- `getEvolutionVariants()`

Normalization requirements:
- `decision_id` -> `decisionId`
- `action_index` -> `actionIndex`
- `action_names` -> `actionNames`, if introduced locally.
- `current_iks` -> `currentIks`
- `current_win_rate` -> `currentWinRate`
- `decisions_total` -> `decisionsTotal`
- `days_active` -> `daysActive`
- `per_category_precision` -> `perCategoryPrecision`
- `decisions_analyzed` -> `decisionsAnalyzed`
- `event_type` -> `eventType`
- SDK `EvolutionPanel` variant `status`: `promotion_approved` -> `promoted`, `promotion_rejected` -> `rejected`, otherwise `created` or `shadow` if provided.

## 7. Types Contract

`apps/dataops/frontend/src/types.ts` should define defensive, frontend-stable types:
- `Health`
- `PipelineSystem`
- `DataOpsAlert`
- `AlertDetail`
- `BlastRadius`
- `DependencyNode`
- `FactorValue`
- `FactorMap`
- `FactorAutoFillResponse`
- `RecurrenceResponse`
- `AERecommendation`
- `AERecommendationResponse`
- `AEImpact`
- `PatternOrigin`
- `PatternOriginStep`
- `Incident`
- `ConservationHistory`
- `ConservationEvent`
- `ConservationState`
- `ConservationWhatIfRequest`
- `ScoreResponse`
- `LearnResponse`
- `FingerprintResponse`
- `TrajectoryResponse`
- `EvolutionVariant`
- `AlertMetadataPayload`

All backend-originated optional fields should be optional in TypeScript unless tests or router code prove they are mandatory.

## 8. App Contract

`App.tsx`:
- Uses `CopilotShell`.
- Five tabs: Dashboard, Triage, Insight, Evidence, Curve.
- Dashboard is default.
- Keep `selectedAlertId` in React state.
- Dashboard alert click sets `selectedAlertId` and switches to Triage.
- Triage Back returns to Dashboard.
- Load health on mount.
- Show fixture mode banner when `health.graphSource === "fixture"`.
- Load trajectory on mount or safely in Curve to provide IKS; if unavailable, use safe default `0`.
- No `localStorage` or `sessionStorage`.

## 9. Dashboard Contract

`DashboardScreen.tsx` fetches:
- `getPipelines`
- `getAlerts`
- `getConservationStatus`
- `getAeImpact`
- `getConservationHistory`

Render:
- `PipelineGrid`
- compact `AEImpactPanel`
- `AlertQueue`
- SDK `ConservationSlider`
- `ConservationTimeline`

Dashboard behavior:
- Alert click calls `onSelectAlert(alert.alertId)` and navigates to Triage.
- Pipeline grid uses `PipelineSystem` fields: `displayName`, `status`, `slaMinutes`, `businessCriticality`, `sourceReliability`, `owner`, `alertCount`, `activeAlertCount`, `upstreamCount`, `downstreamCount`.
- Alert queue uses `DataOpsAlert` fields: `alertId`, `dataset`, `system`, `category`, `severity`, `status`, `actionTaken`, `isCorrect`, `recurrenceCount`, `factors`.

Interactive conservation what-if:
- `ConservationSlider.onDrag` posts to `/api/conservation/what-if`.
- The dragged slider value is sent as `theta_min`.
- Use safe defaults for `alpha`, `q`, and `V` if the backend status response does not provide them.
- Update frontend conservation state from the what-if response.

## 10. Triage Contract

`TriageScreen.tsx` fetches for `selectedAlertId`:
- `getAlert`
- `getAlertDeps`
- `getAlertFactors`
- `getAlertRecurrence`
- `getAeRecommendation`

Render:
- Back button.
- Alert header.
- `AERecommendationBadge`, if recommendation exists.
- `DependencyTree`.
- `FactorAutoFill`.
- `RecurrenceBadge`.
- `ActionPicker`.

Factor policy:
- User does not input factor values.
- All six factors are auto-computed from `/api/context/alert/{id}/factors`.
- Score payload factor keys must be exactly:
  - `impact_scope`
  - `source_reliability`
  - `recurrence_frequency`
  - `downstream_urgency`
  - `data_freshness`
  - `business_criticality`

Score/learn flow:
- User chooses or accepts an action through `ActionPicker`.
- `scoreAlert` posts `{ category, factors, context }`.
- Save alert metadata after scoring with at least `decision_id`, `alert_id`, `dataset`, `system`, `category`, `severity`, `factors`, `selected_action`, `ae_recommendation`, and `blast_radius`.
- Render `ScoreResultCard`.
- `ScoreResultCard.result.actionNames` must be the DataOps action display labels.
- Confirm calls `learnAlert({ decision_id, actual_action, outcome: "confirmed", context })`.
- Override calls `learnAlert` with the override action value.
- Do not pass `centroidDelta`.

## 11. Insight Contract

`InsightScreen.tsx` fetches:
- `getFingerprint`
- `getIncident`

Render:
- `ProfileArchetype`
- SDK `FingerprintPanel`
- `IncidentReplayCard`

Profile archetype guidance:
- Top factor comes from highest fingerprint weight.
- Suggested mappings:
  - `impact_scope` -> The Blast Radius Operator
  - `source_reliability` -> The Source Skeptic
  - `recurrence_frequency` -> The Pattern Historian
  - `downstream_urgency` -> The SLA Defender
  - `data_freshness` -> The Freshness Sentinel
  - `business_criticality` -> The Business Impact Guard

Fingerprint labels:
- `signalLabel="YOUR GRAPH SIGNAL"`
- `noiseLabel="YOUR BLIND SPOTS"`

## 12. Evidence Contract

`EvidenceScreen.tsx` fetches:
- `getEvolutionVariants`
- `getPatternOrigin`
- `getAeImpact`

Render:
- full `AEImpactPanel`
- SDK `EvolutionPanel`
- `PatternOriginCard`

Evidence behavior:
- Show promoted and rejected variants.
- Preserve rejected variant visibility for audit evidence.
- Pattern origin should render SOC -> S2P -> DataOps chain and warm-start prior if present.

## 13. Curve Contract

`CurveScreen.tsx` fetches:
- `getTrajectory`

Render:
- SDK `TrajectoryChart`.
- `switchingCostLine={undefined}` or omit it; DataOps prompt specifies null/no switching line.
- Include disruption annotation at decision `301`.
- Narrative should explain enterprise learning curve and post-disruption recovery.

Trajectory normalization:
- `points[].win_rate` -> `points[].winRate`.
- `current_iks` -> `currentIks`.
- `current_win_rate` -> `currentWinRate`.
- `decisions_total` -> `decisionsTotal`.
- `days_active` -> `daysActive`.

## 14. Visual / UX Constraints

- Purple accent:
  - `--copilot-primary: #7c3aed`
  - use compatible purple light/surface variables where needed.
- Import SDK theme from `../../../copilot_sdk/frontend/copilot-theme.css`.
- AE suggestions must be visible on Dashboard and Triage.
- Graph/fixture source must be visible.
- No external fonts.
- No `localStorage` or `sessionStorage`.
- Desktop-first operational layout.
- Keep text dense, scan-friendly, and enterprise oriented.
- Avoid landing-page composition. First screen is the operational Dashboard.

## 15. Validation Commands

From `apps/dataops/frontend`:

```powershell
npm install
npx tsc --noEmit
npm run build
```

From repo root:

```powershell
python -m pytest apps/dataops/backend/tests/ -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

Do not run live Vite/backend servers or Playwright unless the user explicitly confirms the live stack is running.

## Prompt Sequence

Prompt 2: Base Dashboard
- Create package/config.
- Create `main.tsx`, `theme.css`, `api.ts`, `types.ts`, `App.tsx`.
- Implement Dashboard and components:
  - `PipelineGrid`
  - `AlertQueue`
  - `AlertCard`
  - compact `AEImpactPanel`
  - `ConservationTimeline`
- Add placeholder Triage, Insight, Evidence, and Curve screens only if needed to compile.
- Validate with install, typecheck, build, DataOps backend tests, and root SDK tests.

Prompt 3: Triage Workflow
- Implement `TriageScreen`.
- Implement:
  - `DependencyTree`
  - `FactorAutoFill`
  - `RecurrenceBadge`
  - `ActionPicker`
  - `AERecommendationBadge`
- Wire score, metadata save, learn/override, and `ScoreResultCard`.
- Validate with typecheck, build, DataOps backend tests, and root SDK tests.

Prompt 4: Insight, Evidence, Curve
- Implement `InsightScreen`, `EvidenceScreen`, and `CurveScreen`.
- Implement:
  - `ProfileArchetype`
  - `IncidentReplayCard`
  - full `AEImpactPanel`
  - `PatternOriginCard`
  - `DisruptionAnnotation`, if useful.
- Integrate SDK `FingerprintPanel`, `EvolutionPanel`, and `TrajectoryChart`.
- Final validation with typecheck, build, DataOps backend tests, and root SDK tests.

## Risks And Guardrails

- Backend and SDK responses use snake_case; SDK frontend components expect camelCase. Normalize only in `api.ts`.
- `ConservationSlider.currentThreshold` is frontend state because backend status has `theta_min` but no direct `currentThreshold`.
- `/api/ae/recommendation/{alert_id}` already filters to `promotion_approved`; frontend should not show rejected variants as recommendations.
- Evolution audit should still display rejected variants on Evidence.
- DataOps `apps/dataops/frontend` currently lacks package/config files; creation is required before typecheck/build can run.
- No backend or SDK edits are needed for the frontend rebuild.
