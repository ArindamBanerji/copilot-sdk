# RL Wiring Notes

## Purpose

The existing `copilot_sdk.rl` package provides reward functions, a conservation-bounded
exploration policy, and a credit assignment helper.
Those pieces are now wired through `CompoundingScorer.from_preset()`.
This keeps reinforcement-learning setup at the same boundary that already knows the
domain preset, tensor shape, graph store, and GAE scorer.

## Wiring Boundary

`CompoundingScorer.from_preset()` is the only runtime wiring point.
The scorer still accepts explicit `reward_function`, `credit_assigner`, and
`exploration_policy` overrides.
When `enable_rl=True`, default components are provided for supported domains.
When `enable_rl=False`, no default RL components are attached.

## Domain Mapping

| Domain | Reward Function | Rationale |
|---|---|---|
| `trading` | `PnLRewardFunction` | Trading feedback is driven by realized execution outcome such as basis-point P&L. |
| `purchasing` | `WasteReductionRewardFunction` | Purchasing feedback should reward reduced waste. |
| `dataops` | `GradedFinancialRewardFunction` | DataOps feedback uses recovered value and at-risk value style outcomes. |

The registry also constructs:

- `ConservationBoundedThompson`
- `CreditAssigner`

The exploration policy is sized from the live preset action count.
The credit assigner does not require a graph store in the current implementation.

## enable_rl Behavior

`enable_rl` defaults to `True`.
Supported domains receive default RL components unless a caller supplies explicit
components.
Explicit caller-supplied components take precedence over registry defaults.
Unsupported domains continue to construct without RL components.
`enable_rl=False` preserves the old no-default-RL behavior.

## Reward Separation

The router-visible reward path remains separate.
`scoring_router._signed_reward()` is display/API reward logic for `/learn` responses.
The RL reward functions are learning reward logic consumed by `CompoundingScorer.learn()`.
This change does not rename, replace, or modify `_signed_reward()`.

## Learning Flow

On `learn()`:

1. The scorer performs its existing GAE update.
2. If an RL reward function exists, `_compute_rl_reward()` computes `reward_raw`.
3. The returned `reward` is scaled by the preset penalty ratio.
4. If an exploration policy exists, it receives `update(predicted_index, reward_raw)`.
5. If a credit assigner exists, it receives the contributing preset factor names.

The `score()` path is unchanged.
RL components are not consulted when generating a score.

## Conservation-Bounded Exploration

`ConservationBoundedThompson` retains its own conservation status controls.
The scorer wiring does not bypass existing scorer conservation pause behavior.
The current `learn()` path updates exploration priors from observed reward.
Action selection through exploration remains separate from the deterministic score path.

## Failure Behavior

RL setup is additive.
If registry setup raises during `from_preset()`, scorer construction continues with
missing default RL components disabled.
Explicit caller-supplied components are preserved.
This prevents optional RL wiring from taking down domain scorer initialization.
The failure is logged through the scorer logger.

## Files Changed

- `copilot_sdk/rl/presets.py`
- `copilot_sdk/scoring/scorer.py`
- `tests/rl/test_presets.py`
- `tests/rl/test_rl_wiring.py`
- `docs/rl_wiring_notes.md`

## Files Intentionally Unchanged

- `copilot_sdk/rl/reward_functions.py`
- `copilot_sdk/rl/reward.py`
- `copilot_sdk/rl/exploration.py`
- `copilot_sdk/rl/credit.py`
- `copilot_sdk/rl/__init__.py`
- `copilot_sdk/backend/scoring_router.py`
- graph and evolution packages
- app backends

## Validation

The implementation should be validated with:

- targeted RL wiring tests
- full RL package tests
- scorer regression tests
- preset regression tests
- SDK root tests
- app backend regressions

Validation results must be reported by the implementation run.
