# RL Diagnostic Scan — Part 1 Results

Read-only implementation scan completed 2026-08-08. The governing separation is the judgment-memory authority: judgment is centroid geometry; RL/evolution is procedural memory ([`judgment_memory_v2_9.md:108-118`](copilot-sdk/docs/design/judgment_memory_v2_9.md:108)). Code beats documentation per [`CLAUDE.md:1-4`](copilot-sdk/CLAUDE.md:1).

## 1. File inventory

The inventory below covers production Python implementing or wiring RL, rewards, exploration, evolution, shadow evaluation, promotion, or variant state. Tests and generated `graphify-out` artifacts were used only as corroboration, not counted as implementation.

| Path | Size | Purpose | Key symbols |
|---|---:|---|---|
| `copilot-sdk/copilot_sdk/rl/reward.py` | 1,583 | SDK reward protocol, clipping, asymmetric negative scaling | `RewardFunction`, `RewardComputer` ([`reward.py:8-46`](copilot-sdk/copilot_sdk/rl/reward.py:8)) |
| `copilot-sdk/copilot_sdk/rl/reward_functions.py` | 2,068 | Built-in binary, financial, P&L, and waste rewards | Four `compute()` implementations ([`reward_functions.py:8-63`](copilot-sdk/copilot_sdk/rl/reward_functions.py:8)) |
| `copilot-sdk/copilot_sdk/rl/exploration.py` | 4,571 | Conservation-bounded Thompson sampling and Beta posteriors | `ConservationBoundedThompson` ([`exploration.py:12-53`](copilot-sdk/copilot_sdk/rl/exploration.py:12)) |
| `copilot-sdk/copilot_sdk/rl/presets.py` | 2,370 | Trading/purchasing/DataOps/S2P RL component registry | `RL_PRESET_REGISTRY`, `get_rl_components()` ([`presets.py:16-54`](copilot-sdk/copilot_sdk/rl/presets.py:16)) |
| `copilot-sdk/copilot_sdk/rl/credit.py` | 1,341 | Factor credit attribution sidecar | `CreditAssigner` ([`credit.py:9-39`](copilot-sdk/copilot_sdk/rl/credit.py:9)) |
| `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py` | 15,622 | Prompt variant selection, UCB exploration, shadow/promotion callbacks | `PromptVariantEvolver`, `_select_ucb()` ([`prompt_evolver.py:57-114`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:57), [`prompt_evolver.py:344-373`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344)) |
| `copilot-sdk/copilot_sdk/evolution/evolver.py` | 9,489 | Generic procedural rule evolution | `AgentEvolver` ([`evolver.py:16-27`](copilot-sdk/copilot_sdk/evolution/evolver.py:16)) |
| `copilot-sdk/copilot_sdk/evolution/gate.py` | 3,106 | Generic promotion gate | `DefaultPromotionGate` ([`gate.py:9-78`](copilot-sdk/copilot_sdk/evolution/gate.py:9)) |
| `copilot-sdk/copilot_sdk/evolution/shadow.py` | 3,528 | Generic shadow-run contract/default runner | `DefaultShadowRunner` ([`shadow.py:12-102`](copilot-sdk/copilot_sdk/evolution/shadow.py:12)) |
| `copilot-sdk/copilot_sdk/evolution/ledger.py` | 3,910 | In-memory evolution event ledger | `InMemoryEvolutionLedger` ([`ledger.py:16-109`](copilot-sdk/copilot_sdk/evolution/ledger.py:16)) |
| `copilot-sdk/copilot_sdk/evolution/variant_store.py` | 6,212 | Variant specifications and global/category statistics | `VariantSpec`, `VariantStats`, `InMemoryVariantStore` ([`variant_store.py:10-58`](copilot-sdk/copilot_sdk/evolution/variant_store.py:10)) |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | 100,653 | Centroid scorer plus optional RL/evolution orchestration | `CompoundingScorer.learn()`, `_compute_rl_reward()` ([`scorer.py:663-674`](copilot-sdk/copilot_sdk/scoring/scorer.py:663), [`scorer.py:1848-1871`](copilot-sdk/copilot_sdk/scoring/scorer.py:1848)) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py` | 22,204 | SOC-era standalone reward computer and Thompson policy | `RewardComputer`, `ExplorationPolicy` ([`rl_engine.py:37-84`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:37), [`rl_engine.py:275-342`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275)) |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py` | 20,734 | SOC compatibility wrapper around SDK prompt evolution | `_UCB_EXPLORATION`, `_sdk_config()`, category UCB ([`evolver.py:44-45`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`evolver.py:160-167`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160), [`evolver.py:243-252`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:243)) |
| `s2p-copilot/backend/app/domains/s2p/reward.py` | 1,082 | S2P-specific graded financial reward | `S2PRewardFunction.compute()` ([`reward.py:8-27`](s2p-copilot/backend/app/domains/s2p/reward.py:8)) |
| `s2p-copilot/backend/app/domains/s2p/evolution/service.py` | 6,476 | S2P procedural evolution service | Evolution service definitions ([`service.py:1-160`](s2p-copilot/backend/app/domains/s2p/evolution/service.py:1)) |
| `s2p-copilot/backend/app/services/s2p_evolver.py` | 6,686 | S2P evolver integration | Evolver service definitions ([`s2p_evolver.py:1-194`](s2p-copilot/backend/app/services/s2p_evolver.py:1)) |
| `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py` | 15,530 | Trading shadow batches and promotion checks | `check_promotion()` ([`trading_evolver.py:265-317`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:265)) |
| `copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py` | 6,350 | Trading UCB/promotion defaults | `PromptEvolverConfig(exploration_constant=1.414)` ([`evolver_config.py:158-160`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:158)) |
| `copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py` | 7,325 | Purchasing UCB/promotion defaults | `PromptEvolverConfig` ([`evolver_config.py:176-178`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:176)) |
| `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py` | 3,676 | DataOps UCB/promotion defaults | `PromptEvolverConfig` ([`evolver_config.py:79-81`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:79)) |
| `s2p-copilot/backend/app/domains/s2p/evolver_config.py` | 2,449 | S2P UCB/promotion defaults | `PromptEvolverConfig` ([`evolver_config.py:94-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:94)) |
| `graph-attention-engine-v50/gae/profile_scorer.py` | 57,456 | Judgment scoring and centroid learning; not an RL policy | `ProfileScorer.score()`, `update()` ([`profile_scorer.py:408-413`](graph-attention-engine-v50/gae/profile_scorer.py:408), [`profile_scorer.py:788-800`](graph-attention-engine-v50/gae/profile_scorer.py:788)) |

The five copilot wiring is real for SDK-backed scorers: Trading, Purchasing, and DataOps call `CompoundingScorer.from_preset()` ([Trading `main.py:286`](copilot-sdk/apps/trading/backend/app/main.py:286), [Purchasing `main.py:329`](copilot-sdk/apps/purchasing/backend/app/main.py:329), [DataOps `main.py:461`](copilot-sdk/apps/dataops/backend/app/main.py:461)); S2P passes its reward function explicitly ([`s2p/main.py:142-145`](s2p-copilot/backend/app/main.py:142)); SOC deliberately disables SDK RL in its live adapter ([`scorer_adapter.py:24-27`](gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:24)). SOC nevertheless retains a standalone RL engine ([`rl_engine.py:37-44`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:37)).

## 2. Exploration

### `_select_ucb()` body

Verbatim implementation ([`prompt_evolver.py:344-373`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344)):

```python
    def _select_ucb(
        self,
        stats_by_variant: dict[str, _VariantStatsLike],
        active_ids: list[str],
    ) -> str | None:
        if not active_ids:
            return None
        total_all = 0
        for variant_id in active_ids:
            stats = stats_by_variant.get(variant_id)
            if stats is not None:
                total_all += max(int(stats.total), 0)
        if total_all <= 0:
            return active_ids[0]

        best_variant_id: str | None = None
        best_score = float("-inf")
        log_total = math.log(max(total_all, 2))
        for variant_id in active_ids:
            stats = stats_by_variant[variant_id]
            total = int(stats.total)
            if total <= 0:
                return variant_id
            mean = float(stats.success_rate)
            exploration = self._config.exploration_constant * math.sqrt(log_total / total)
            score = mean + exploration
            if score > best_score:
                best_variant_id = variant_id
                best_score = score
        return best_variant_id
```

Formula: **CONFIRMED, UCB1 variant**: `mean_i + c * sqrt(ln(max(N, 2)) / n_i)`. It uses total observations across active variants for `N`, clamps the logarithm floor to 2, and immediately selects an untried variant. This is not literally `ln(N)` when `N < 2`, but is the same UCB1 formula otherwise ([`prompt_evolver.py:351-369`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:351)).

Constants:

- SDK default: `c = 1.414` ([`prompt_evolver.py:27-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:27)).
- SOC compatibility wrapper: `c = 1.0`, passed into `PromptEvolverConfig` ([`evolver.py:44`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`evolver.py:160-165`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)).
- Trading, Purchasing, DataOps, and S2P configs: `c = 1.414` ([Trading `evolver_config.py:158-160`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:158), [Purchasing `evolver_config.py:176-178`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:176), [DataOps `evolver_config.py:79-81`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:79), [S2P `evolver_config.py:94-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:94)).

**Thompson:** PRESENT. The SDK has `ConservationBoundedThompson`; it samples Beta posteriors only when conservation is GREEN and exploration probability permits it ([`exploration.py:25-44`](copilot-sdk/copilot_sdk/rl/exploration.py:25), [`exploration.py:118-122`](copilot-sdk/copilot_sdk/rl/exploration.py:118)). SOC also has a standalone Beta-posterior Thompson policy ([`rl_engine.py:275-341`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275)).

**Epsilon-greedy / Boltzmann:** No named epsilon-greedy or Boltzmann exploration implementation was found in the production scan. SOC has an `epsilon_base` parameter, but its policy is random gating followed by Beta Thompson sampling, not epsilon-greedy action selection ([`rl_engine.py:278-290`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:278), [`rl_engine.py:299-341`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:299)). Softmax exists in the judgment scorer as probability normalization, not as a distinct exploration policy ([`profile_scorer.py:487-496`](graph-attention-engine-v50/gae/profile_scorer.py:487)).

SOC discrepancy resolved: **both values are true in different layers**. The SOC prompt-evolution wrapper overrides SDK UCB to `1.0`; the SDK default and the other four copilot evolution configs remain `1.414` ([`evolver.py:44`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`evolver.py:160-165`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160), [`prompt_evolver.py:27-29`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:27)).

## 3. Reward layer

### SDK `RewardComputer.compute_reward()` body

Verbatim ([`reward.py:32-46`](copilot-sdk/copilot_sdk/rl/reward.py:32)):

```python
    def compute_reward(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any] | None = None,
    ) -> float:
        raw = float(self._reward_function.compute(
            recommended_action,
            actual_action,
            outcome or {},
        ))
        clipped = _clamp(raw, -1.0, 1.0)
        if clipped < 0:
            return clipped * self._penalty_ratio
        return clipped
```

### SDK reward functions

`BinaryRewardFunction.compute()` ([`reward_functions.py:11-18`](copilot-sdk/copilot_sdk/rl/reward_functions.py:11)):

```python
    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any],
    ) -> float:
        del outcome
        return 1.0 if actual_action == recommended_action else -1.0
```

`GradedFinancialRewardFunction.compute()` ([`reward_functions.py:24-36`](copilot-sdk/copilot_sdk/rl/reward_functions.py:24)):

```python
    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any],
    ) -> float:
        if actual_action == recommended_action:
            recovered = _number(outcome.get("recovered"))
            at_risk = max(_number(outcome.get("at_risk")), 1.0)
            return _clamp(recovered / at_risk, -1.0, 1.0)

        cycle_time_hours = _number(outcome.get("cycle_time_hours"))
        return -min(1.0, max(cycle_time_hours, 0.0) / 24.0)
```

`PnLRewardFunction.compute()` ([`reward_functions.py:42-49`](copilot-sdk/copilot_sdk/rl/reward_functions.py:42)):

```python
    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any],
    ) -> float:
        del recommended_action, actual_action
        return _clamp(_number(outcome.get("pnl_bps")) / 100.0, -1.0, 1.0)
```

The prior scan omitted a fourth SDK function: `WasteReductionRewardFunction`, which returns the clamped negative waste percentage change ([`reward_functions.py:52-63`](copilot-sdk/copilot_sdk/rl/reward_functions.py:52)).

### Call graph and truth

1. `CompoundingScorer.from_preset()` constructs RL components for known domains by default (`enable_rl=True`) ([`scorer.py:227-240`](copilot-sdk/copilot_sdk/scoring/scorer.py:227), [`scorer.py:313-339`](copilot-sdk/copilot_sdk/scoring/scorer.py:313)).
2. During `learn()`, the scorer updates centroids and writes the outcome first, then calls `_compute_rl_reward()`; a non-null reward updates the explorer and assigns factor credit ([`scorer.py:782-809`](copilot-sdk/copilot_sdk/scoring/scorer.py:782), [`scorer.py:871-882`](copilot-sdk/copilot_sdk/scoring/scorer.py:871)).
3. `_compute_rl_reward()` calls the configured reward function directly and applies scorer-side negative scaling; it does **not** instantiate or call SDK `RewardComputer` ([`scorer.py:1848-1871`](copilot-sdk/copilot_sdk/scoring/scorer.py:1848)).
4. The only production `RewardComputer(...)` construction found is the standalone SOC engine ([`rl_engine.py:531-544`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:531)).

Therefore: reward does reach the SDK scorer’s `learn()` sidecar, but it does not determine `ProfileScorer.score()`’s centroid-distance recommendation. It is not accurate to say the reward layer is wholly disconnected from scoring, and it is not accurate to say `RewardComputer` is the SDK scorer’s active call path.

Penalty ratios used by the five copilot presets:

| Copilot | Ratio | Evidence |
|---|---:|---|
| SOC | 20.0 | [`soc.py:59-60`](copilot-sdk/copilot_sdk/scoring/presets/soc.py:59) |
| S2P | 5.0 | [`s2p.py:61-62`](copilot-sdk/copilot_sdk/scoring/presets/s2p.py:61) |
| Trading | 3.0 | [`trading.py:66-68`](copilot-sdk/copilot_sdk/scoring/presets/trading.py:66) |
| Purchasing | 3.0 | [`purchasing.py:63-64`](copilot-sdk/copilot_sdk/scoring/presets/purchasing.py:63) |
| DataOps | 10.0 | [`dataops.py:61-62`](copilot-sdk/copilot_sdk/scoring/presets/dataops.py:61) |

The SDK RL registry independently records Trading 3.0, Purchasing 3.0, DataOps 10.0, and S2P 5.0 ([`presets.py:16-33`](copilot-sdk/copilot_sdk/rl/presets.py:16)). The standalone SOC engine defaults to 20.0 ([`rl_engine.py:20-23`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:20)).

## 4. Judgment-core separation

**Overall status: CONTRADICTED if the claim is “scoring contains zero RL imports”; CONFIRMED if the claim is “the recommendation and centroid update are centroid geometry, not reward maximization.”**

The SDK scorer imports optional RL components when `enable_rl` is true ([`scorer.py:313-331`](copilot-sdk/copilot_sdk/scoring/scorer.py:313)), and its `learn()` method invokes reward/exploration/credit sidecars ([`scorer.py:871-882`](copilot-sdk/copilot_sdk/scoring/scorer.py:871)). A full production sweep of `copilot-sdk/copilot_sdk/scoring/` therefore found one RL import at [`scorer.py:319`](copilot-sdk/copilot_sdk/scoring/scorer.py:319), not zero.

The judgment core itself is centroid based. `ProfileScorer.score()` computes distances from the factor vector to category/action centroids and applies softmax to negative distance ([`profile_scorer.py:408-413`](graph-attention-engine-v50/gae/profile_scorer.py:408), [`profile_scorer.py:438-496`](graph-attention-engine-v50/gae/profile_scorer.py:438)). Its update implements pull/push centroid learning with effective `η`, including predicted-centroid push and ground-truth-centroid pull ([`profile_scorer.py:792-800`](graph-attention-engine-v50/gae/profile_scorer.py:792), [`profile_scorer.py:915-988`](graph-attention-engine-v50/gae/profile_scorer.py:915)). No reward is used in that score-distance calculation.

## 5. §3 validation ledger

### §3.1 SDK reward layer

| Prior finding | Status | Truth/evidence |
|---|---|---|
| `RewardComputer(reward_function, penalty_ratio)` | **CONFIRMED** | Constructor and positive-ratio normalization: [`reward.py:21-26`](copilot-sdk/copilot_sdk/rl/reward.py:21) |
| `compute_reward(recommended_action, actual_action, outcome) -> float` | **CONFIRMED** | Signature/body: [`reward.py:32-46`](copilot-sdk/copilot_sdk/rl/reward.py:32) |
| `RewardFunction` is a Protocol | **CONFIRMED** | [`reward.py:8-18`](copilot-sdk/copilot_sdk/rl/reward.py:8) |
| Binary, GradedFinancial, and PnL functions exist | **CONFIRMED** | [`reward_functions.py:8-49`](copilot-sdk/copilot_sdk/rl/reward_functions.py:8) |
| Those functions share `compute(recommended, actual, outcome) -> float` | **CONFIRMED** | [`reward_functions.py:11-18`](copilot-sdk/copilot_sdk/rl/reward_functions.py:11), [`reward_functions.py:24-36`](copilot-sdk/copilot_sdk/rl/reward_functions.py:24), [`reward_functions.py:42-49`](copilot-sdk/copilot_sdk/rl/reward_functions.py:42) |
| `penalty_ratio` is 20:1 SOC and 5:1 S2P | **CONFIRMED** | [`soc.py:59-60`](copilot-sdk/copilot_sdk/scoring/presets/soc.py:59), [`s2p.py:61-62`](copilot-sdk/copilot_sdk/scoring/presets/s2p.py:61) |
| The SDK reward layer has only the three listed functions | **CONTRADICTED** | `WasteReductionRewardFunction` is also implemented: [`reward_functions.py:52-63`](copilot-sdk/copilot_sdk/rl/reward_functions.py:52) |
| Reward reaches the scorer | **CONFIRMED with qualification** | Direct reward-function call from `learn()`, not SDK `RewardComputer`: [`scorer.py:871-882`](copilot-sdk/copilot_sdk/scoring/scorer.py:871), [`scorer.py:1848-1871`](copilot-sdk/copilot_sdk/scoring/scorer.py:1848) |

### §3.2 SDK exploration

| Prior finding | Status | Truth/evidence |
|---|---|---|
| `PromptEvolverConfig.exploration_constant=1.414` | **CONFIRMED** | [`prompt_evolver.py:26-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:26) |
| Listed promotion/shadow thresholds exist | **CONFIRMED** | [`prompt_evolver.py:29-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29) |
| `_select_ucb()` exists | **CONFIRMED** | [`prompt_evolver.py:344-348`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344) |
| Exploration is UCB1 | **CONFIRMED with implementation-specific floor** | [`prompt_evolver.py:351-369`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:351) |
| SDK `c ≈ √2` | **CONFIRMED** | [`prompt_evolver.py:27-29`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:27) |
| SOC uses `c=1.0` | **CONFIRMED** | [`evolver.py:44`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`evolver.py:160-165`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160) |
| No other exploration strategy exists | **CONTRADICTED** | SDK and SOC both implement conservation-bounded Thompson sampling: [`exploration.py:12-44`](copilot-sdk/copilot_sdk/rl/exploration.py:12), [`rl_engine.py:275-341`](gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275) |

### §3.6 tests / ground truth

| Prior finding | Status | Truth/evidence |
|---|---|---|
| SOC UCB can select lower-raw-rate/fewer-trials variant | **CONFIRMED** | Test sets A at 80/100 and B at 3/4 and expects B: [`test_prompt_category_ucb.py:64-71`](copilot-sdk/tests/evolution/test_prompt_category_ucb.py:64) |
| Trading promotion requires three batches | **CONFIRMED** | Implementation rejects below `MIN_SHADOW_BATCHES`: [`trading_evolver.py:273-280`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:273) |
| Trading promotion requires at least 5 percentage points | **CONFIRMED** | Each improvement is checked against `MIN_IMPROVEMENT_PP`: [`trading_evolver.py:281-287`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:281) |
| Trading promotion requires GREEN conservation | **CONFIRMED** | [`trading_evolver.py:288-294`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:288) |
| Trading promotion requires stability | **CONFIRMED** | Population standard deviation gate and reason: [`trading_evolver.py:295-302`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:295) |
| Listed reason codes exist | **CONFIRMED** | [`trading_evolver.py:275-300`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:275) |

