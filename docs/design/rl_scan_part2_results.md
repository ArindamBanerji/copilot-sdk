# RL Diagnostic Scan — Part 2 Results

Read-only implementation scan completed 2026-08-08. The authority requires judgment memory to remain centroid geometry and procedural evolution to remain separate ([`judgment_memory_v2_9.md:66-75`](copilot-sdk/docs/design/judgment_memory_v2_9.md:66)); implementation was treated as authoritative under [`CLAUDE.md:1-4`](copilot-sdk/CLAUDE.md:1).

## 1. Gate + Shadow (Task D)

### `DefaultPromotionGate.evaluate()` — verbatim

Source: [`copilot-sdk/copilot_sdk/evolution/gate.py:22-54`](copilot-sdk/copilot_sdk/evolution/gate.py:22).

```python
    def evaluate(
        self,
        shadow_results: dict[str, Any],
        conservation_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        total = int(shadow_results.get("total") or 0)
        accuracy = float(shadow_results.get("accuracy") or 0.0)
        baseline_accuracy = float(shadow_results.get("baseline_accuracy") or 0.0)
        superiority_pp = round((accuracy - baseline_accuracy) * 100.0, 4)
        batches = [float(value) for value in shadow_results.get("batch_accuracies", [])]
        variance = pstdev(batches) if len(batches) > 1 else 0.0

        checks = {
            "sufficient_data": bool(shadow_results.get("sufficient")) and total >= self.min_shadow_decisions,
            "superiority": superiority_pp >= self.superiority_threshold_pp,
            "accuracy_floor": accuracy >= self.accuracy_floor,
            "conservation": self._is_conservation_safe(conservation_state),
            "variance": variance <= 0.10,
        }
        promoted = all(checks.values())
        failed_checks = [name for name, passed in checks.items() if not passed]
        reason = "promoted" if promoted else self._reason(checks)
        return {
            "promoted": promoted,
            "reason": reason,
            "failed_checks": failed_checks,
            "checks": checks,
            "accuracy": round(accuracy, 4),
            "baseline_accuracy": round(baseline_accuracy, 4),
            "superiority_pp": superiority_pp,
            "total": total,
            "variance": round(variance, 4),
        }
```

Gate defaults are superiority `5.0` percentage points, accuracy floor `0.70`, and minimum shadow decisions `10` ([`gate.py:9-20`](copilot-sdk/copilot_sdk/evolution/gate.py:9)). It computes population standard deviation over `batch_accuracies` and requires `variance <= 0.10` ([`gate.py:30-40`](copilot-sdk/copilot_sdk/evolution/gate.py:30)).

Conservation is fail-closed: `None`, malformed values, or missing recognized fields return false; a string must be `GREEN`, while dict `status/state/phase` accepts `GREEN`, `VERIFIED`, or `ACTIVE`, and `overallSafe/overall_safe=True` also passes ([`gate.py:62-78`](copilot-sdk/copilot_sdk/evolution/gate.py:62)). This is broader than a literal GREEN-only contract in the generic SDK gate.

### `DefaultShadowRunner.run_shadow()` — verbatim

Source: [`copilot-sdk/copilot_sdk/evolution/shadow.py:16-67`](copilot-sdk/copilot_sdk/evolution/shadow.py:16).

```python
    def run_shadow(
        self,
        variant: Any,
        decisions: list[dict[str, Any]],
        baseline: Any | None = None,
    ) -> dict[str, Any]:
        total = len(decisions)
        sufficient = total >= self.min_decisions
        if not sufficient:
            return {
                "sufficient": False,
                "total": total,
                "correct": 0,
                "baseline_correct": 0,
                "accuracy": 0.0,
                "baseline_accuracy": 0.0,
                "errors": 0,
            }

        correct = 0
        baseline_correct = 0
        errors = 0
        for decision in decisions:
            normalized = self._normalize_decision(decision)
            actual = self._actual_action(normalized)
            try:
                if self._predict(variant, normalized) == actual:
                    correct += 1
            except Exception as exc:
                logger.warning("Variant shadow evaluation failed: %s", exc)
                errors += 1
            try:
                baseline_action = (
                    self._predict(baseline, normalized)
                    if baseline is not None
                    else self._baseline_action(normalized)
                )
                if baseline_action == actual:
                    baseline_correct += 1
            except Exception as exc:
                logger.warning("Baseline shadow evaluation failed: %s", exc)
                errors += 1

        return {
            "sufficient": True,
            "total": total,
            "correct": correct,
            "baseline_correct": baseline_correct,
            "accuracy": round(correct / total, 4) if total else 0.0,
            "baseline_accuracy": round(baseline_correct / total, 4) if total else 0.0,
            "errors": errors,
        }
```

The generic shadow runner does **not** compute `improvement_pp`, `variance`, or `batch_accuracies`; it returns candidate/baseline counts, accuracies, and errors ([`shadow.py:59-67`](copilot-sdk/copilot_sdk/evolution/shadow.py:59)). Trading computes improvement and stores per-batch results around this runner ([`trading_evolver.py:234-263`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:234)).

### SDK `AgentEvolver.evolve()` and reason codes

The prior lifecycle finding is **CONFIRMED**. The implementation is: missing baseline → plateau check → generate → record/start shadow → shadow run → gate → activate and record promotion or record rejection ([`evolver.py:49-105`](copilot-sdk/copilot_sdk/evolution/evolver.py:49)). Plateau defaults are `window=10`, `min_improvement_rate=0.2`, `cooldown=50` ([`evolver.py:16-24`](copilot-sdk/copilot_sdk/evolution/evolver.py:16)).

Complete reason/status set found in the SDK generic and prompt paths:

- `not_registered`, `generation_failed`, `plateau_cooldown` ([`evolver.py:57-65`](copilot-sdk/copilot_sdk/evolution/evolver.py:57), [`evolver.py:71-87`](copilot-sdk/copilot_sdk/evolution/evolver.py:71), [`evolver.py:211-228`](copilot-sdk/copilot_sdk/evolution/evolver.py:211)).
- Generic gate: `promoted`, or first failed check among `sufficient_data`, `superiority`, `accuracy_floor`, `conservation`, `variance`; fallback `rejected` ([`gate.py:41-60`](copilot-sdk/copilot_sdk/evolution/gate.py:41)).
- Prompt promotion: `conservation` for blocked promotion; successful prompt result has no explicit `reason` key ([`prompt_evolver.py:232-255`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:232), [`prompt_evolver.py:268-288`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:268).
- Trading custom path: `regime_break_deferred`, `insufficient_batches`, `insufficient_improvement`, `conservation_not_green`, `unstable_improvement`, `variant_not_found`, and `promotable` ([`trading_evolver.py:265-317`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:265), [`trading_evolver.py:319-345`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:319)).

## 2. Per-copilot matrix (Task E)

| Copilot | Evolver class | Config source | exploration_c | promotion_min | improvement_pp | Live/shadow/disabled | Active variants | Shadow variants |
|---|---|---|---:|---:|---:|---|---:|---:|
| SOC | `PromptVariantEvolver` compatibility wrapper | `services/evolver.py` | 1.0 | 10 samples | 5 pp / 0.05 rate | Live outcome recording and promotion checks; conservation argument omitted by the main triage caller | 2 initial | 2 initial |
| S2P | `PromptVariantEvolver` | `services/s2p_evolver.py` + `domains/s2p/evolver_config.py` | 1.414 | 50 samples | 0.05 rate | Live registered variants, shadow recording, and promotion-check route | 4 | 4 |
| Trading | Custom `TradingAgentEvolver`, containing SDK `AgentEvolver` | `services/trading_evolver.py` plus config inventory | 1.414 in config-only inventory; not used by custom batch gate | 50 in config-only inventory | 5 pp custom gate | Live evolution router/service; candidates are shadow-tested before promotion | 5 configured; runtime starts empty | 5 configured; runtime starts empty |
| Purchasing | No production `PromptVariantEvolver(...)` instantiation found; configured `VariantSpec` provider | `app/evolution/evolver_config.py` | 1.414 | 50 | 0.05 rate | Configured inventory exposed through evolution router; live evolver execution **GAP** | 6 configured | 6 configured |
| DataOps | No production `PromptVariantEvolver(...)` instantiation found; configured `VariantSpec` provider | `app/evolution/evolver_config.py` | 1.414 | 50 | 0.05 rate | Configured inventory exposed through evolution router; live evolver execution **GAP** | 2 configured | 2 configured |

Evidence for the matrix:

- SOC constructs the SDK prompt evolver with `_sdk_config()` and uses `_UCB_EXPLORATION=1.0` ([`soc evolver.py:39-44`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:39), [`soc evolver.py:160-178`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)). Its initial stats contain four variants and its active map selects two (`TRAVEL_CONTEXT_v2`, `PHISHING_RESPONSE_v1`); the builder marks the remaining two shadow ([`soc evolver.py:21-34`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:21), [`soc evolver.py:101-129`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:101)).
- SOC is live in the triage path: it records an outcome and calls promotion checking after each evaluated decision ([`evolution.py:332-342`](gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:332)). However, that caller invokes `check_for_promotion(alert_type)` without a conservation argument ([`evolution.py:374-388`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:374)); `_sdk_config()` supplies no conservation provider ([`evolver.py:160-167`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160). The generic gate therefore fail-closes if no other provider is injected ([`gate.py:62-67`](copilot-sdk/copilot_sdk/evolution/gate.py:62)).
- S2P instantiates and registers initial variants at module load ([`s2p_evolver.py:19-24`](s2p-copilot/backend/app/services/s2p_evolver.py:19)); its config has `1.414`, `0.05`, and `50` ([`evolver_config.py:92-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:92)). The source contains four active and four shadow statuses ([`evolver_config.py:5-89`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:5)).
- S2P discrepancy: **CONFIRMED hard-coded**. `check_promotion()` passes `conservation_state="GREEN"` directly ([`s2p_evolver.py:64-66`](s2p-copilot/backend/app/services/s2p_evolver.py:64)). The public promotion-check route calls that wrapper ([`s2p_evolution.py:55-57`](s2p-copilot/backend/app/routers/s2p_evolution.py:55)). It is not fetched from a live conservation provider in this path.
- Trading custom service constructs `DefaultShadowRunner(min_decisions=1)`, a custom gate, and an SDK `AgentEvolver` ([`trading_evolver.py:171-185`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:171)). The router creates the service when no service is supplied ([`evolution_router.py:51-62`](copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:51)). Its configured Prompt variants are five active/five shadow ([`trading_evolver_config.py:24-153`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:24), [`trading_evolver_config.py:156-161`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:156)).
- Trading custom constants are `MIN_SHADOW_BATCHES=3`, `MIN_IMPROVEMENT_PP=5.0`, `MAX_VARIANCE_PP=10.0`, `MIN_MULTIPLIER=0.1`, and `MAX_MULTIPLIER=2.0` ([`trading_evolver.py:21-25`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:21)). Runtime candidate state starts with no active variant and an empty variant map ([`trading_evolver.py:186-190`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:186)).
- Purchasing and DataOps each wire `create_evolution_router()` with a `variant_provider`, not a `PromptVariantEvolver` instance ([Purchasing `main.py:689-696`](copilot-sdk/apps/purchasing/backend/app/main.py:689), [DataOps `main.py:742-747`](copilot-sdk/apps/dataops/backend/app/main.py:742)). Their inventories are six active/six shadow and two active/two shadow respectively ([Purchasing `evolver_config.py:18-171`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:18), [DataOps `evolver_config.py:25-74`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:25)).

### SDK vs per-copilot `promotion_min_samples`

**CONFIRMED discrepancy.** SDK `PromptEvolverConfig` defaults to `10`, while S2P, Trading, Purchasing, and DataOps configs explicitly set `50` ([`prompt_evolver.py:29-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29), [S2P `evolver_config.py:92-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:92), [Trading `evolver_config.py:156-161`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:156), [Purchasing `evolver_config.py:174-179`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:174), [DataOps `evolver_config.py:77-82`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:77)). SOC explicitly sets `10` in its wrapper ([`evolver.py:160-166`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)). These values apply to PromptVariantEvolver candidate statistics; the Trading custom service separately requires three batches and five-point improvement ([`trading_evolver.py:273-302`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:273)).

## 3. Completeness sweep (Task G)

**Status: CONFIRMED — no additional algorithmic RL family found.** A production Python sweep across all five repositories found zero implementation hits for Q-learning, policy gradients, actor-critic, DQN, PPO, SAC, Bellman, TD error, advantage function, value function, replay buffer, or discount factor. The actual mechanisms are UCB, conservation-bounded Thompson/Beta sampling, reward functions, credit attribution, centroid learning, shadow evaluation, and evolution gates ([SDK Thompson `exploration.py:12-53`](copilot-sdk/copilot_sdk/rl/exploration.py:12), [SDK UCB `prompt_evolver.py:344-373`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344), [SDK credit `credit.py:9-39`](copilot-sdk/copilot_sdk/rl/credit.py:9)).

Terms such as `softmax` are judgment-score normalization, not a missing RL policy; the scorer computes softmax over negative centroid distances ([`profile_scorer.py:487-496`](graph-attention-engine-v50/gae/profile_scorer.py:487)). Generic `shadow_mode` is decision marking/audit infrastructure, not a separate RL algorithm ([`framework/shadow_mode.py:35-42`](copilot-sdk/copilot_sdk/framework/shadow_mode.py:35)).

## 4. Constants table (Task H)

| Constant | SDK default | SOC | S2P | Trading | Purchasing | DataOps |
|---|---:|---:|---:|---:|---:|---:|
| `exploration_constant` | 1.414 | 1.0 wrapper | 1.414 | 1.414 config; custom runtime gate is not UCB | 1.414 | 1.414 |
| `promotion_improvement_threshold` | 0.05 | 0.05 | 0.05 | 0.05 config; custom runtime requires 5 pp | 0.05 | 0.05 |
| `promotion_min_samples` | 10 | 10 | 50 | 50 config | 50 | 50 |
| `shadow_delta_min` | 0.05 | 0.05 inherited | 0.05 inherited | 0.05 inherited/config | 0.05 inherited | 0.05 inherited |
| `shadow_q_floor` | 0.80 | 0.80 inherited | 0.80 inherited | 0.80 inherited/config | 0.80 inherited | 0.80 inherited |
| `shadow_sigma_max` | 0.10 | 0.10 inherited | 0.10 inherited | 0.10 inherited/config | 0.10 inherited | 0.10 inherited |
| `shadow_min_samples` | 50 | 50 inherited | 50 inherited | custom runner min decisions=1 | 50 inherited | 50 inherited |
| `shadow_min_batches` | 3 | 3 inherited | 3 inherited | custom batch gate=3 | 3 inherited | 3 inherited |
| `penalty_ratio` | n/a | 20.0 | 5.0 | 3.0 | 3.0 | 10.0 |
| `PlateauConfig.plateau_window` | 10 | 10 if SDK `AgentEvolver` used | 10 inherited | 10 in nested SDK evolver | 10 if instantiated | 10 if instantiated |
| `PlateauConfig.min_improvement_rate` | 0.2 | 0.2 if SDK `AgentEvolver` used | 0.2 inherited | 0.2 in nested SDK evolver | 0.2 if instantiated | 0.2 if instantiated |
| `PlateauConfig.plateau_cooldown` | 50 | 50 if SDK `AgentEvolver` used | 50 inherited | 50 in nested SDK evolver | 50 if instantiated | 50 if instantiated |

SDK defaults are defined at [`prompt_evolver.py:27-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:27) and [`evolver.py:17-24`](copilot-sdk/copilot_sdk/evolution/evolver.py:17). Per-copilot penalty ratios are [`soc.py:59-60`](copilot-sdk/copilot_sdk/scoring/presets/soc.py:59), [`s2p.py:61-62`](copilot-sdk/copilot_sdk/scoring/presets/s2p.py:61), [`trading.py:66-68`](copilot-sdk/copilot_sdk/scoring/presets/trading.py:66), [`purchasing.py:63-64`](copilot-sdk/copilot_sdk/scoring/presets/purchasing.py:63), and [`dataops.py:61-62`](copilot-sdk/copilot_sdk/scoring/presets/dataops.py:61).

## 5. §3 validation ledger (§3.3, §3.4, §3.5)

### §3.3 SDK `AgentEvolver`

| Prior finding | Status | Evidence/truth |
|---|---|---|
| `PlateauConfig` is `window=10`, `min_improvement_rate=0.2`, `cooldown=50` | **CONFIRMED** | [`evolver.py:16-24`](copilot-sdk/copilot_sdk/evolution/evolver.py:16) |
| `AgentEvolver.evolve()` checks registration first | **CONFIRMED** | [`evolver.py:57-65`](copilot-sdk/copilot_sdk/evolution/evolver.py:57) |
| Plateau check occurs before variant generation | **CONFIRMED** | [`evolver.py:67-69`](copilot-sdk/copilot_sdk/evolution/evolver.py:67) |
| Lifecycle is generate → shadow → gate → promote/reject | **CONFIRMED** | [`evolver.py:71-105`](copilot-sdk/copilot_sdk/evolution/evolver.py:71) |

### §3.4 SDK gate and shadow

| Prior finding | Status | Evidence/truth |
|---|---|---|
| `DefaultPromotionGate.evaluate` enforces conservation GREEN | **CONTRADICTED (state truth)** | It fail-closes on missing state and accepts string GREEN or dict `GREEN/VERIFIED/ACTIVE`, plus `overallSafe=True`; it is not strictly GREEN-only ([`gate.py:62-78`](copilot-sdk/copilot_sdk/evolution/gate.py:62)). |
| Gate enforces improvement and variance | **CONFIRMED** | Superiority, accuracy floor, and variance checks are [`gate.py:30-43`](copilot-sdk/copilot_sdk/evolution/gate.py:30). |
| Gate enforces batches | **CONFIRMED with qualification** | Generic gate enforces total decisions, not batch count; `min_shadow_decisions=10` is [`gate.py:12-20`](copilot-sdk/copilot_sdk/evolution/gate.py:12), while PromptVariantEvolver enforces sample count but not generic batch count ([`prompt_evolver.py:201-212`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:201)). |
| `DefaultShadowRunner.run_shadow` computes candidate vs baseline accuracy | **CONFIRMED** | [`shadow.py:35-67`](copilot-sdk/copilot_sdk/evolution/shadow.py:35) |
| Generic shadow computes improvement_pp/variance | **CONTRADICTED (state truth)** | Those fields are absent from the generic return; Trading computes improvement and batch variance outside it ([`shadow.py:59-67`](copilot-sdk/copilot_sdk/evolution/shadow.py:59), [`trading_evolver.py:239-255`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:239)). |

### §3.5 Per-copilot evolvers

| Prior finding | Status | Evidence/truth |
|---|---|---|
| Trading has custom `TradingAgentEvolver` and `TradingVariantGenerator` | **CONFIRMED** | [`trading_evolver.py:53-73`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:53), [`trading_evolver.py:161-185`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:161) |
| Trading constants are 3 batches, 5 pp, 10 pp variance, multipliers 0.1–2.0 | **CONFIRMED** | [`trading_evolver.py:21-25`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:21) |
| S2P uses PromptVariantEvolver and `S2P_EVOLVER_CONFIG` | **CONFIRMED** | [`s2p_evolver.py:10-24`](s2p-copilot/backend/app/services/s2p_evolver.py:10) |
| S2P promotion conservation is hard-coded GREEN | **CONFIRMED** | [`s2p_evolver.py:64-66`](s2p-copilot/backend/app/services/s2p_evolver.py:64) |
| SOC uses PromptVariantEvolver with UCB 1.0 | **CONFIRMED** | [`evolver.py:160-178`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160) |
| DataOps uses Prompt config with UCB 1.414 and min samples 50 | **CONFIRMED for configuration** | [`dataops/evolver_config.py:77-82`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:77) |
| Trading uses Prompt config with UCB 1.414 and min samples 50 | **CONFIRMED for configuration; custom runtime is separate** | [`trading/evolver_config.py:156-161`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:156), [`trading_evolver.py:171-185`](copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:171) |
| Purchasing config values were unavailable | **CONTRADICTED (state truth)** | Full config is present: UCB 1.414, threshold 0.05, min samples 50 ([`purchasing/evolver_config.py:174-179`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:174)). |
| SDK default min samples 10 vs Trading/DataOps 50 | **CONFIRMED and expanded** | S2P and Purchasing also set 50; only SDK and SOC wrapper use 10 ([`prompt_evolver.py:29-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29), [`s2p/evolver_config.py:92-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:92), [`purchasing/evolver_config.py:174-179`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:174)). |

## 6. Discrepancy resolutions

- **SOC UCB `1.0` vs SDK `1.414`: CONFIRMED as a layer difference.** The SOC compatibility wrapper passes `_UCB_EXPLORATION=1.0` into its `PromptEvolverConfig` ([`evolver.py:44`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44), [`evolver.py:160-165`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160)); SDK default remains `1.414` ([`prompt_evolver.py:27-29`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:27)).
- **S2P `conservation_state="GREEN"`: CONFIRMED hard-coded in the wrapper.** The promotion route calls `check_promotion()`, which passes literal GREEN rather than obtaining current conservation ([`s2p_evolution.py:55-57`](s2p-copilot/backend/app/routers/s2p_evolution.py:55), [`s2p_evolver.py:64-66`](s2p-copilot/backend/app/services/s2p_evolver.py:64)).
- **`promotion_min_samples=10` vs `50`: CONFIRMED intentional per-config divergence in code, but no explanatory runtime policy was found.** SDK/SOC use 10; S2P/Trading/Purchasing/DataOps use 50 ([`prompt_evolver.py:29-36`](copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29), [`soc/evolver.py:160-166`](gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160), [S2P `evolver_config.py:92-96`](s2p-copilot/backend/app/domains/s2p/evolver_config.py:92), [Trading `evolver_config.py:156-161`](copilot-sdk/apps/trading/backend/app/evolution/evolver_config.py:156), [Purchasing `evolver_config.py:174-179`](copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:174), [DataOps `evolver_config.py:77-82`](copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:77)).

