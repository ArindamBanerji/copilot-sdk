# RL and Evolution Architecture

This document records the verified boundary between judgment and learning for
the five copilots. The implementation anchors are the SDK scorer, evolution
gate, app-owned evolvers, and the SOC boundary memo.

## 1. Overview

The judgment core selects the live action from centroid distance and softmax.
It is the authoritative decision path. RL and evolution are a procedural
memory sidecar: they compute reward after verified outcomes, explore variants
in shadow, and gate promotion. They do not replace the centroid-selected
action.

The architecture preserves four guarantees: G1, action selection is not
reward maximization; G2, conservation is live and fail-closed; G3, promotion
requires measurable improvement and sufficient evidence; and G4, variant
state and outcomes are auditable and domain-scoped. See
`rl_consolidated_verification_and_design.md` §§0, 2, 8 and the SOC boundary
memo §6.

## 2. Architecture

```text
verified input -> scorer -> centroid distance + softmax -> recommended action
                         |
                         +-> learn() -> reward / exploration / credit sidecar
                                           |
                                           +-> variant proposal -> shadow test
                                                               -> conservation gate
                                                               -> promotion
```

- `Scorer` performs action selection from learned centroids. Reward is not an
  action selector.
- `learn()` records verified feedback and runs the reward, exploration, and
  credit sidecar. It does not rewrite the action returned for the decision.
- `Evolution` proposes active/shadow variants, shadow-tests them, and
  promotes only when the gate accepts sufficient data, superiority,
  accuracy, variance, and conservation.

The SDK gate is fail-closed: missing, unknown, or unsafe conservation state
blocks promotion. Production Decision data continues to use the configured
GraphStore/AGE path; the in-memory variant ledger is evolution metadata, not a
substitute for production Decision storage.

## 3. Per-Copilot Configuration

| Copilot | Evolver | Variants | Reward fn | Penalty ratio | UCB c |
|---|---|---:|---|---:|---:|
| SOC | standalone SOC evolver plus RL sidecar (outside this SDK) | SOC-configured | SOC reward registry | 20 | 1.0 |
| S2P | standalone S2P evolver (separate repo) | S2P-configured | `GradedFinancialRewardFunction` | 5 | 1.414 |
| Trading | live custom `TradingAgentEvolver` with SDK gate parity | 10 (5 active + 5 shadow) | `PnLRewardFunction` | 3 | 1.414 |
| Purchasing | live SDK `PromptVariantEvolver` | 12 (6 active + 6 shadow) | `WasteReductionRewardFunction` | 3 | 1.414 |
| DataOps | live SDK `PromptVariantEvolver` | 4 (2 active + 2 shadow) | `GradedFinancialRewardFunction` | 10 | 1.414 |

The SDK values are sourced from the domain presets and each app’s
`evolution/evolver_config.py`. Trading keeps its domain-specific factor
variant generator while exposing the same startup registration, provider,
outcome, and gate semantics.

## 4. Conservation Contract

`ConservationStateProvider` is a synchronous callable evaluated at promotion
time. It returns a state containing at least a status; `overallSafe`, domain,
counts, source, timestamp, and reason are carried for telemetry.

SDK copilots use `ScorerBackedProvider` or the app’s scorer-backed adapter.
SOC uses `CachedAsyncProvider` to turn its asynchronous learning-health source
into a timestamped synchronous snapshot. `GREEN` (or another safe phase) must
be positively established; `UNKNOWN`, `AMBER`, `RED`, stale, missing, or
provider-error states block promotion. No caller supplies a literal safe state
as a production fallback.

## 5. G1 Boundary (SOC)

SOC uses Option A strict, reached through Option C immediately:
`RL_EXPLORATION_ENABLED=False` in production, with exploration retained as a
proposal/shadow-learning signal. It must not override `selected_action` on a
live decision. The centroid action remains authoritative, and promotion is
the governed path for adoption. The authoritative decision and verification
memo are `soc_g1_boundary_decision_memo.md` §§3 and 6-9.

## 6. Decisions

- **D1 — SOC UCB:** keep `c=1.0` as the intentional SOC override; the SDK
  default remains 1.414.
- **D2 — Trading custom evolver:** keep it because factor-weight generation
  and regime checks are domain-specific; require interface parity with the
  SDK registration, provider, outcome, and telemetry contract.
- **D3 — SOC `rl_engine.py`:** active as a learning sidecar, not authoritative
  for promotion or live action selection.

## 7. Test Matrix

`tests/test_rl_evolution_matrix.py` parameterizes the live SDK copilot apps:
Trading, Purchasing, and DataOps. It verifies startup registration and
identity, AST literal-state absence, AMBER blocking, GREEN promotion,
superiority, variance, sample sufficiency, verified outcome statistics, and
G1 action/probability invariance using real scorers and stores. SOC and S2P
remain covered by their own application repositories and boundary tests.

The consolidated matrix names the broader five-copilot acceptance set:
T-STARTUP, T-NOLIT, T-AMBER, T-GREEN, T-SUP, T-VAR, T-SAMP, T-OUTCOME,
T-G1, and the SOC-specific T-G1-SOC-AUDIT.
