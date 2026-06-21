# Creating A Copilot

This guide describes the build path for adding a new domain copilot on top of the SDK.

## Step 1: Define A Domain Preset

Create a preset with:

- `name`
- `shape` with categories, actions, and factors
- `penalty_ratio`
- learning rates such as `eta_confirm` and `eta_override`
- optional bootstrap centroids

The shape determines the tensor:

```text
categories x actions x factors
```

## Step 2: Register The Preset

Add the preset to `PRESET_REGISTRY` in `copilot_sdk.scoring.presets`.

The registry key is the public domain key used by:

```python
CompoundingScorer.from_preset("hr", graph_store=store)
```

## Step 3: Create Factor Computers

Each factor should have one responsible computer or adapter. Factor computers should:

- read domain context
- compute one normalized factor value
- attach provenance and substantiation metadata when surfaced
- avoid K3 sample data in production metrics

## Step 4: Mount Routers

Domain applications usually expose routers for:

- scoring
- learning outcomes
- conservation state
- evolution or discovery
- connector health
- evidence and substantiation

The SDK does not mount routers by itself. Application repos own FastAPI route wiring.

## Step 5: Add To Demo Startup

Demo startup needs:

- backend port
- frontend port
- preset key
- graph store path or AGE configuration
- connector environment variables
- Playwright target URL

Keep port allocation explicit so copilots can run side-by-side.

## Step 6: Write Tests

Minimum coverage:

- backend scoring contract
- outcome learning path
- conservation gate
- graph persistence
- frontend render path
- Playwright E2E for the user workflow

WIRE-01 reminder: every backend feature must have frontend wiring and Playwright coverage before it counts as shipped.

## Example: HR Copilot

Hypothetical preset:

```text
categories:
  attrition_risk, hiring_pipeline, performance_review, compliance_case

actions:
  auto_approve, manager_review, escalate_to_hrbp, hold_for_legal

factors:
  tenure_signal, engagement_delta, manager_load, policy_risk,
  comp_band_variance, hiring_urgency
```

Implementation outline:

1. Create `HRCopilotPreset` with a `(4, 4, 6)` shape.
2. Register it as `hr`.
3. Implement factor computers for the six factors.
4. Add routers for score, learn, conservation, and substantiation.
5. Add the backend/frontend ports to demo startup.
6. Add backend tests and Playwright E2E for one complete HR decision workflow.

## Design Guardrails

- Do not import app-specific domain modules into `copilot-sdk`.
- Keep domain logic in the domain application repo.
- Use `GraphStore` for decisions and outcomes.
- Use provenance and substantiation tiers on surfaced values.
- Add tests against real scorer and store paths rather than scorer/store mocks.
