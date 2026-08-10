# RL Diagnostic Scan — Consolidated Results

Consolidated from the Part 1 SDK/reward/exploration scan and Part 2 gate/per-copilot/completeness scan. This is an implementation-first, read-only diagnostic. Detailed verbatim bodies remain available in [Part 1](rl_scan_part1_results.md) and [Part 2](rl_scan_part2_results.md).

## Executive findings

- UCB selection is implemented as `mean + c * sqrt(ln(max(N, 2)) / n_i)`, with SDK default `c=1.414` and SOC compatibility override `c=1.0` ([`prompt_evolver.py:351-369`](../../copilot_sdk/evolution/prompt_evolver.py:351), [`evolver.py:44`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44)).
- Thompson sampling is also present and conservation-bounded; no Q-learning, policy-gradient, actor-critic, DQN, PPO, SAC, Bellman, TD-error, or replay-buffer implementation was found ([`exploration.py:12-44`](../../copilot_sdk/rl/exploration.py:12)).
- SDK reward functions are used by `CompoundingScorer.learn()` as an RL sidecar, while recommendation remains centroid-distance scoring ([`scorer.py:871-882`](../../copilot_sdk/scoring/scorer.py:871), [`profile_scorer.py:408-413`](../../../graph-attention-engine-v50/gae/profile_scorer.py:408)).
- `RewardComputer` exists in the SDK but the active SDK scorer calls the configured reward function directly; the only production `RewardComputer(...)` construction found is the SOC standalone engine ([`scorer.py:1848-1871`](../../copilot_sdk/scoring/scorer.py:1848), [`rl_engine.py:531-544`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:531)).
- S2P promotion passes literal `conservation_state="GREEN"` rather than fetching current state ([`s2p_evolver.py:64-66`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:64)).
- Purchasing and DataOps expose configured active/shadow variant inventories but no production `PromptVariantEvolver(...)` instantiation was found in their app wiring ([Purchasing `main.py:689-696`](../../apps/purchasing/backend/app/main.py:689), [DataOps `main.py:742-747`](../../apps/dataops/backend/app/main.py:742)).

## 1. SDK and repository inventory

| Area | Implementation | Key evidence |
|---|---|---|
| SDK RL | Reward protocol/functions, Thompson exploration, presets, credit attribution | [`copilot_sdk/rl/reward.py:8-46`](../../copilot_sdk/rl/reward.py:8), [`reward_functions.py:8-63`](../../copilot_sdk/rl/reward_functions.py:8), [`exploration.py:12-53`](../../copilot_sdk/rl/exploration.py:12), [`presets.py:16-54`](../../copilot_sdk/rl/presets.py:16) |
| SDK evolution | AgentEvolver, PromptVariantEvolver, gates, shadow runner, ledger, variant store | [`evolver.py:16-105`](../../copilot_sdk/evolution/evolver.py:16), [`prompt_evolver.py:57-114`](../../copilot_sdk/evolution/prompt_evolver.py:57), [`gate.py:9-78`](../../copilot_sdk/evolution/gate.py:9), [`shadow.py:12-102`](../../copilot_sdk/evolution/shadow.py:12) |
| SDK scoring | Centroid scorer with optional RL/evolution orchestration | [`scorer.py:227-240`](../../copilot_sdk/scoring/scorer.py:227), [`scorer.py:313-339`](../../copilot_sdk/scoring/scorer.py:313) |
| SOC | Prompt evolution compatibility wrapper plus standalone reward/Thompson engine | [`evolver.py:160-178`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160), [`rl_engine.py:37-84`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:37) |
| S2P | PromptVariantEvolver, S2P reward and evolution service | [`s2p_evolver.py:19-24`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:19), [`reward.py:8-27`](../../../s2p-copilot/backend/app/domains/s2p/reward.py:8) |
| Trading | Custom TradingAgentEvolver with SDK shadow/gate primitives | [`trading_evolver.py:161-185`](../../apps/trading/backend/app/services/trading_evolver.py:161) |
| Purchasing | Configured VariantSpec inventory and router provider | [`evolver_config.py:18-179`](../../apps/purchasing/backend/app/evolution/evolver_config.py:18), [`main.py:689-696`](../../apps/purchasing/backend/app/main.py:689) |
| DataOps | Configured VariantSpec inventory and router provider | [`evolver_config.py:25-82`](../../apps/dataops/backend/app/evolution/evolver_config.py:25), [`main.py:742-747`](../../apps/dataops/backend/app/main.py:742) |
| GAE judgment core | Centroid distance, softmax over negative distances, centroid pull/push learning | [`profile_scorer.py:408-496`](../../../graph-attention-engine-v50/gae/profile_scorer.py:408), [`profile_scorer.py:788-988`](../../../graph-attention-engine-v50/gae/profile_scorer.py:788) |

## 2. Exploration and reward conclusions

### Exploration

**Status: CONFIRMED — UCB1 variant.** The exact formula is:

```text
score_i = success_rate_i + exploration_constant * sqrt(log(max(total_all, 2)) / total_i)
```

The implementation immediately selects an untried variant and otherwise maximizes the score ([`prompt_evolver.py:344-373`](../../copilot_sdk/evolution/prompt_evolver.py:344)). SDK default `exploration_constant=1.414` and SOC override `1.0` are explicit ([`prompt_evolver.py:27-29`](../../copilot_sdk/evolution/prompt_evolver.py:27), [`evolver.py:160-165`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)). Trading, S2P, Purchasing, and DataOps configs use `1.414` ([Trading `evolver_config.py:156-161`](../../apps/trading/backend/app/evolution/evolver_config.py:156), [S2P `evolver_config.py:92-96`](../../../s2p-copilot/backend/app/domains/s2p/evolver_config.py:92)).

**Thompson: PRESENT.** The SDK samples Beta posteriors only when conservation is GREEN and exploration is allowed ([`exploration.py:25-44`](../../copilot_sdk/rl/exploration.py:25)); SOC has a separate Beta-posterior policy ([`rl_engine.py:275-341`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275)). Named epsilon-greedy and Boltzmann exploration were not found. Softmax is used for centroid scoring, not as a separate exploration policy ([`profile_scorer.py:487-496`](../../../graph-attention-engine-v50/gae/profile_scorer.py:487)).

### Reward layer

`RewardComputer.compute_reward()` clips raw reward to `[-1,1]` and multiplies negative values by `penalty_ratio` ([`reward.py:32-46`](../../copilot_sdk/rl/reward.py:32)). Implemented functions are Binary, GradedFinancial, PnL, and an additional WasteReduction function ([`reward_functions.py:8-63`](../../copilot_sdk/rl/reward_functions.py:8)).

The active scorer path calls the reward function directly during `learn()`, then updates exploration and factor credit ([`scorer.py:871-882`](../../copilot_sdk/scoring/scorer.py:871)). It does not call SDK `RewardComputer` ([`scorer.py:1848-1871`](../../copilot_sdk/scoring/scorer.py:1848)). Full verbatim reward bodies are in [Part 1 §3](rl_scan_part1_results.md#3-reward-layer).

| Copilot | `penalty_ratio` | Evidence |
|---|---:|---|
| SOC | 20.0 | [`soc.py:59-60`](../../copilot_sdk/scoring/presets/soc.py:59) |
| S2P | 5.0 | [`s2p.py:61-62`](../../copilot_sdk/scoring/presets/s2p.py:61) |
| Trading | 3.0 | [`trading.py:66-68`](../../copilot_sdk/scoring/presets/trading.py:66) |
| Purchasing | 3.0 | [`purchasing.py:63-64`](../../copilot_sdk/scoring/presets/purchasing.py:63) |
| DataOps | 10.0 | [`dataops.py:61-62`](../../copilot_sdk/scoring/presets/dataops.py:61) |

## 3. Gate, shadow, and evolution

### Generic SDK gate

**Status: CONFIRMED with qualification.** `DefaultPromotionGate` checks sufficient data, superiority, accuracy floor, conservation, and variance, then returns the first failed reason ([`gate.py:22-60`](../../copilot_sdk/evolution/gate.py:22)). Defaults are 5 pp superiority, 0.70 accuracy floor, and 10 minimum shadow decisions ([`gate.py:12-20`](../../copilot_sdk/evolution/gate.py:12)). Conservation is fail-closed but accepts string GREEN, dict `status/state/phase` values `GREEN/VERIFIED/ACTIVE`, or `overallSafe=True` ([`gate.py:62-78`](../../copilot_sdk/evolution/gate.py:62)).

### Generic SDK shadow

**Status: CONFIRMED with qualification.** `DefaultShadowRunner` evaluates candidate and baseline predictions, counts correct results/errors, and returns both accuracies ([`shadow.py:16-67`](../../copilot_sdk/evolution/shadow.py:16)). It does not itself compute `improvement_pp`, batch variance, or batch accuracies; Trading adds those fields externally ([`trading_evolver.py:234-255`](../../apps/trading/backend/app/services/trading_evolver.py:234)). Full verbatim bodies are in [Part 2 §1](rl_scan_part2_results.md#1-gate--shadow-task-d).

### AgentEvolver

**Status: CONFIRMED.** `PlateauConfig` defaults to window 10, improvement rate 0.2, cooldown 50 ([`evolver.py:16-24`](../../copilot_sdk/evolution/evolver.py:16)). `AgentEvolver.evolve()` performs registration check → plateau check → generation → shadow → gate → promotion/rejection ([`evolver.py:49-105`](../../copilot_sdk/evolution/evolver.py:49)).

Reason families include `not_registered`, `generation_failed`, `plateau_cooldown`, `sufficient_data`, `superiority`, `accuracy_floor`, `conservation`, `variance`, and Trading-specific `regime_break_deferred`, `insufficient_batches`, `insufficient_improvement`, `conservation_not_green`, `unstable_improvement`, and `variant_not_found` ([`evolver.py:57-87`](../../copilot_sdk/evolution/evolver.py:57), [`gate.py:41-60`](../../copilot_sdk/evolution/gate.py:41), [`trading_evolver.py:265-345`](../../apps/trading/backend/app/services/trading_evolver.py:265)).

## 4. Per-copilot wiring

| Copilot | Evolver/runtime truth | Config | Variant inventory |
|---|---|---|---|
| SOC | Live `PromptVariantEvolver` compatibility wrapper; standalone RL engine also exists | UCB 1.0, promotion threshold 0.05, min samples 10 ([`evolver.py:160-178`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)) | 2 initial active, 2 initial shadow ([`evolver.py:21-34`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21)) |
| S2P | Live `PromptVariantEvolver`, initial registration at module load ([`s2p_evolver.py:19-24`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:19)) | UCB 1.414, threshold 0.05, min samples 50 ([`evolver_config.py:92-96`](../../../s2p-copilot/backend/app/domains/s2p/evolver_config.py:92)) | 4 active, 4 shadow ([`evolver_config.py:5-89`](../../../s2p-copilot/backend/app/domains/s2p/evolver_config.py:5)) |
| Trading | Live custom `TradingAgentEvolver`; nested SDK `AgentEvolver`, isolated shadow runner, custom gate ([`trading_evolver.py:171-185`](../../apps/trading/backend/app/services/trading_evolver.py:171)) | Custom: 3 batches, 5 pp, 10 pp variance, multiplier 0.1–2.0 ([`trading_evolver.py:21-25`](../../apps/trading/backend/app/services/trading_evolver.py:21)) | 5 configured active, 5 configured shadow; runtime starts with no variants ([`trading_evolver.py:186-190`](../../apps/trading/backend/app/services/trading_evolver.py:186)) |
| Purchasing | **GAP:** configured variant provider/router, no production PromptVariantEvolver instantiation found | UCB 1.414, threshold 0.05, min samples 50 ([`evolver_config.py:174-179`](../../apps/purchasing/backend/app/evolution/evolver_config.py:174)) | 6 active, 6 shadow configured ([`evolver_config.py:18-171`](../../apps/purchasing/backend/app/evolution/evolver_config.py:18)) |
| DataOps | **GAP:** configured variant provider/router, no production PromptVariantEvolver instantiation found | UCB 1.414, threshold 0.05, min samples 50 ([`evolver_config.py:77-82`](../../apps/dataops/backend/app/evolution/evolver_config.py:77)) | 2 active, 2 shadow configured ([`evolver_config.py:25-74`](../../apps/dataops/backend/app/evolution/evolver_config.py:25)) |

S2P’s conservation discrepancy is **CONFIRMED hard-coded**: the promotion wrapper passes literal GREEN and the public route calls that wrapper ([`s2p_evolver.py:64-66`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:64), [`s2p_evolution.py:55-57`](../../../s2p-copilot/backend/app/routers/s2p_evolution.py:55)). SOC’s UCB discrepancy is a compatibility-layer override, not a changed SDK default ([`evolver.py:44`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`prompt_evolver.py:27-29`](../../copilot_sdk/evolution/prompt_evolver.py:27)).

## 5. Completeness and judgment separation

**Completeness status: CONFIRMED — no additional algorithmic RL family found.** The production sweep found no Q-learning, policy gradient, actor-critic, DQN, PPO, SAC, Bellman, TD-error, advantage-function, value-function, replay-buffer, or discount-factor implementation. Existing mechanisms are UCB, Thompson/Beta sampling, reward functions, credit attribution, evolution, gates, shadows, and centroid learning ([`exploration.py:12-53`](../../copilot_sdk/rl/exploration.py:12), [`credit.py:9-39`](../../copilot_sdk/rl/credit.py:9)).

Judgment-core separation is **CONFIRMED for the recommendation algorithm, CONTRADICTED for a “zero RL imports in scoring” claim**. `ProfileScorer.score()` computes centroid distances and softmax over negative distances ([`profile_scorer.py:408-496`](../../../graph-attention-engine-v50/gae/profile_scorer.py:408)); `ProfileScorer.update()` performs centroid pull/push with effective learning rates ([`profile_scorer.py:788-988`](../../../graph-attention-engine-v50/gae/profile_scorer.py:788)). However, `scoring/scorer.py` imports optional RL components and invokes them as learning sidecars ([`scorer.py:313-331`](../../copilot_sdk/scoring/scorer.py:313), [`scorer.py:871-882`](../../copilot_sdk/scoring/scorer.py:871)).

## 6. Consolidated validation ledger

| Finding | Status | Evidence |
|---|---|---|
| `RewardComputer` protocol/signature exists | **CONFIRMED** | [`reward.py:8-46`](../../copilot_sdk/rl/reward.py:8) |
| Binary, GradedFinancial, PnL reward functions exist | **CONFIRMED** | [`reward_functions.py:8-49`](../../copilot_sdk/rl/reward_functions.py:8) |
| WasteReduction reward also exists | **CONFIRMED** | [`reward_functions.py:52-63`](../../copilot_sdk/rl/reward_functions.py:52) |
| SOC/S2P ratios are 20/5 | **CONFIRMED** | [`soc.py:59-60`](../../copilot_sdk/scoring/presets/soc.py:59), [`s2p.py:61-62`](../../copilot_sdk/scoring/presets/s2p.py:61) |
| UCB1 inference | **CONFIRMED with `max(N,2)` floor** | [`prompt_evolver.py:351-369`](../../copilot_sdk/evolution/prompt_evolver.py:351) |
| SDK UCB constant 1.414 | **CONFIRMED** | [`prompt_evolver.py:27-29`](../../copilot_sdk/evolution/prompt_evolver.py:27) |
| SOC UCB constant 1.0 | **CONFIRMED** | [`evolver.py:44`](../../../gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44) |
| Thompson sampling absent | **CONTRADICTED** | [`exploration.py:12-44`](../../copilot_sdk/rl/exploration.py:12) |
| AgentEvolver plateau values/lifecycle | **CONFIRMED** | [`evolver.py:16-24`](../../copilot_sdk/evolution/evolver.py:16), [`evolver.py:49-105`](../../copilot_sdk/evolution/evolver.py:49) |
| Generic gate enforces improvement/variance/conservation | **CONFIRMED with qualified conservation states** | [`gate.py:30-78`](../../copilot_sdk/evolution/gate.py:30) |
| Generic shadow computes candidate/baseline accuracy | **CONFIRMED** | [`shadow.py:35-67`](../../copilot_sdk/evolution/shadow.py:35) |
| Generic shadow computes improvement/batch variance | **CONTRADICTED** | Trading adds those metrics externally ([`trading_evolver.py:239-255`](../../apps/trading/backend/app/services/trading_evolver.py:239)) |
| Trading custom evolver/constants | **CONFIRMED** | [`trading_evolver.py:21-25`](../../apps/trading/backend/app/services/trading_evolver.py:21), [`trading_evolver.py:161-185`](../../apps/trading/backend/app/services/trading_evolver.py:161) |
| S2P PromptVariantEvolver wiring | **CONFIRMED** | [`s2p_evolver.py:19-24`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:19) |
| S2P conservation fetched dynamically | **CONTRADICTED — literal GREEN is passed** | [`s2p_evolver.py:64-66`](../../../s2p-copilot/backend/app/services/s2p_evolver.py:64) |
| Purchasing config unavailable | **CONTRADICTED** | [`evolver_config.py:174-179`](../../apps/purchasing/backend/app/evolution/evolver_config.py:174) |
| SDK min samples 10 vs copilot 50 | **CONFIRMED and expanded to S2P/Purchasing/DataOps** | [`prompt_evolver.py:29-36`](../../copilot_sdk/evolution/prompt_evolver.py:29), [`evolver_config.py:77-82`](../../apps/dataops/backend/app/evolution/evolver_config.py:77) |
| Additional deep RL family exists | **CONFIRMED absent** | No production hits; implemented exploration is documented at [`exploration.py:12-53`](../../copilot_sdk/rl/exploration.py:12) |

For the complete original Part 1 and Part 2 ledgers, see [Part 1 §5](rl_scan_part1_results.md#5-3-validation-ledger) and [Part 2 §5](rl_scan_part2_results.md#5-3-validation-ledger-33-34-35).

