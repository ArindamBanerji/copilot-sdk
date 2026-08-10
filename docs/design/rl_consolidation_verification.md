# RL Consolidation Verification — Phase A

Status: read-only verification. No implementation changes were made.

Authority reviewed: `rl_consolidation_work_package.md`, `judgment_memory_v2_9.md`, the consolidated RL scan, the SDK standing rules, the S2P standing rules, the SOC backend standing rules, and the repository graph report (`copilot-sdk/graphify-out/GRAPH_REPORT.md:1-10`).

The key architectural result is unchanged: centroid scoring is judgment memory; reward/evolution is a procedural sidecar. The SDK primitives exist, but the five production copilots do not yet share one complete, live conservation/outcome/promotion/telemetry loop.

## 1. §0.3 validation ledger

| Finding | Status | Evidence |
|---|---|---|
| V-1. SDK exploration is UCB1: `success_rate + c * sqrt(ln(max(N,2)) / n_i)` | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344-369` computes non-negative total trials, `log_total = math.log(max(total_all, 2))`, and `mean + exploration`, where exploration is `c * sqrt(log_total / total)`. A zero-trial variant is returned immediately at `:364-366`. |
| V-2. SDK default `c=1.414`; SOC overrides to `1.0` | CONFIRMED | SDK default: `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29`. SOC override and use: `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44,160-166`. |
| V-3. Conservation-bounded Thompson/Beta sampling exists | CONFIRMED | `copilot-sdk/copilot_sdk/rl/exploration.py:12-25` defines `ConservationBoundedThompson`; `:27-44` freezes exploration for AMBER/RED and samples Beta values only when allowed; `:118-122` implements the Beta sample. This is a real SDK policy, but it is not evidence that every copilot wires a live provider into it. |
| V-4. Reward clips to `[-1,1]` and multiplies negative values by `penalty_ratio` | CONFIRMED | `copilot-sdk/copilot_sdk/rl/reward.py:32-46`. Positive values return the clipped value; negative values return the clipped value times the validated positive penalty ratio. |
| V-5. Four reward functions exist: Binary, GradedFinancial, PnL, WasteReduction | CONFIRMED | `copilot-sdk/copilot_sdk/rl/reward_functions.py:8-19,21-37,39-50,52-63`. |
| V-6. Penalty ratios are SOC=20, S2P=5, Trading=3, Purchasing=3, DataOps=10 | CONFIRMED | `copilot-sdk/copilot_sdk/scoring/presets/soc.py:58-60`; `.../s2p.py:60-62`; `.../trading.py:65-68`; `.../purchasing.py:62-64`; `.../dataops.py:60-62`. |
| V-7. Default gate requires 5 percentage points, a 0.70 accuracy floor, and 10 shadow decisions | CONFIRMED | Defaults: `copilot-sdk/copilot_sdk/evolution/gate.py:12-20`. Evaluation checks sufficient data, superiority, floor, conservation, and variance at `:30-57`. The gate is fail-closed for missing/unknown conservation at `:62-78`. |
| V-8. Plateau defaults are window=10, improvement rate=0.2, cooldown=50 | CONFIRMED for SDK defaults | `copilot-sdk/copilot_sdk/evolution/evolver.py:16-20`. Important override: SOC and S2P presets use 11/55 (`copilot-sdk/copilot_sdk/scoring/presets/soc.py:76-80`; `.../s2p.py:78-82`), while DataOps uses 12/60 (`.../dataops.py:78-82`). |
| V-9. `conservation_state_provider` exists on `PromptEvolverConfig` | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:43`; resolution is explicit state first, then provider, with provider failure becoming unavailable state at `:285-301`. |
| V-10. Per-copilot wiring matrix in the work package | CONTRADICTED in part | S2P does use the SDK evolver but passes literal `"GREEN"` (`s2p-copilot/backend/app/services/s2p_evolver.py:18-24,64-66`). Trading has a provider hook but its default factory leaves it at an UNKNOWN provider (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:49-50,161-185`; `.../routers/evolution_router.py:51-62`). Purchasing and DataOps expose configured variant payloads through a generic router but do not construct a production `PromptVariantEvolver` (`copilot-sdk/apps/purchasing/backend/app/main.py:689-697`; `copilot-sdk/apps/dataops/backend/app/main.py:742-748`; generic fallback `copilot-sdk/copilot_sdk/backend/evolution_router.py:37-49`). |
| V-11. Judgment core is separated from RL/evolution | CONFIRMED for action selection; CONTRADICTED if interpreted as “no RL references anywhere in scoring” | Profile scoring is centroid-distance/softmax action selection at `graph-attention-engine-v50/gae/profile_scorer.py:408-496`, and centroid pull/push learning is at `:790-990`. The SDK scorer’s learn sidecar computes reward and updates optional exploration/credit components only after centroid learning at `copilot-sdk/copilot_sdk/scoring/scorer.py:663-794,871-888`; it does not replace the centroid action path. |

## 2. U1 — Live conservation source

### Resolution

The provider pattern is **(b): per-app providers sharing a compatible status contract**, not one universal SDK getter. The SDK supplies the provider seam, but each app computes or obtains its own state. The SDK resolver accepts a supplied state or calls the configured provider at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:285-301`; the promotion gate accepts string or mapping forms and rejects unknown state at `copilot-sdk/copilot_sdk/evolution/gate.py:62-78`.

| Copilot | Canonical getter | Synchronous? | Shape | Used by evolver? |
|---|---|---:|---|---|
| SOC | `LearningHealthMonitor.evaluate(graph_client)` at `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:232-249`; exposed by `framework_router.py:747-750` | No; async | Health mapping containing computed signal/components and a `status` such as GREEN/AMBER/RED; status is used in the SOC triage path at `.../routers/triage.py:2056-2071` | GAP. The SOC SDK config supplies `exploration_constant` but no conservation provider (`.../services/evolver.py:160-167`). Its normal call invokes promotion without a state (`.../routers/evolution.py:332-342`), so SDK fail-closed behavior sees no live state. |
| S2P | `_current_conservation_status(request)` at `s2p-copilot/backend/app/routers/s2p.py:937-952` | Yes | Status string from GAE calibration; errors become `UNKNOWN` | GAP in the evolver seam. The status getter is used to pause outcome recording (`.../routers/s2p.py:1042-1045`), but `check_promotion()` hard-codes GREEN at `s2p-copilot/backend/app/services/s2p_evolver.py:64-66`. |
| Trading | `_current_conservation_status(graph_store_factory, domain)` at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218` | Yes | Mapping containing counts plus status/conservation fields | GAP in the default service wiring. The custom evolver has a provider field (`.../services/trading_evolver.py:161-169`) and consumes it at `:288-309`, but `create_default_trading_evolver()` uses the UNKNOWN default at `:391-398`; the router does not replace it (`.../routers/evolution_router.py:51-62`). |
| Purchasing | `_conservation_status()` at `copilot-sdk/apps/purchasing/backend/app/main.py:538-556`; generic conservation router uses `scorer_proxy` at `:699-705` | Yes | String helper or generic conservation payload, depending on caller | GAP. The getter is wired to the conservation endpoint, not a PromptVariantEvolver; evolution wiring only supplies variants to the generic router at `:689-697`. |
| DataOps | Generic conservation router calls `scorer_proxy` at `copilot-sdk/apps/dataops/backend/app/main.py:678-683` | Yes | Generic conservation status payload | GAP. No production PromptVariantEvolver is constructed; the evolution router only receives a variant provider at `.../main.py:742-748`. |
| SDK | `PromptEvolverConfig.conservation_state_provider` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:43`, resolved at `:285-301` | Depends on app provider | String, mapping, or provider-defined object accepted by gate | CONFIRMED as an extension seam; not a canonical live source. |

### Exact S2P seam

The safe integration seam is `s2p-copilot/backend/app/services/s2p_evolver.py:64-66`: replace the literal GREEN input with a provider backed by the S2P graph/calibration path represented by `s2p-copilot/backend/app/routers/s2p.py:937-952`. The provider must preserve fail-closed `UNKNOWN` behavior and must not reuse `cached_conservation_state_provider`, which returns counts rather than a status at `s2p-copilot/backend/app/routers/s2p.py:929-934`.

## 3. U2 — Outcome-recording path

| Copilot | Path exists? | Method | Called from | Resolution |
|---|---|---|---|---|
| SOC | Partial | `record_decision_outcome(decision_id, prompt_variant, success, ...)` at `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340-354` | Called from the alert/evolution processing path at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:332-342` | GAP for the required **verified-outcome** loop. The actual audit outcome API is separate at `.../framework/audit.py:149-172`; the cited evolution call records `eval_result["overall_passed"]`, not the later verified audit outcome. |
| S2P | Yes, conditional | `record_triage_outcome()` at `s2p-copilot/backend/app/services/s2p_evolver.py:48-61` | The verified `/api/s2p/outcome` path calls `_record_evolver_outcome_if_allowed` at `s2p-copilot/backend/app/routers/s2p.py:2266-2276,2355-2377`; the bridge requires `variant_id`, non-paused conservation, and a reward at `:1029-1062` | CONFIRMED but incomplete for calls that omit `variant_id`; those are explicitly skipped at `:1037-1040`. |
| Trading | No | No `record_outcome` method in `TradingAgentEvolver`; it records shadow results through `shadow_test` and stores them in `_results` at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:212-263` | No verified decision-to-variant outcome call found in the Trading backend | GAP; WP-2 must build the feedback path. |
| Purchasing | No for evolution | `EventPlanner.record_outcome()` at `copilot-sdk/apps/purchasing/backend/app/services/event_planner.py:73+` records planner usage/waste, not evolver variant statistics | `/events` outcome route at `copilot-sdk/apps/purchasing/backend/app/routers/event_router.py:31-33` | GAP; this is not an evolution feedback loop. |
| DataOps | No | No production evolver outcome recorder found in the DataOps backend; configured variants are payload definitions at `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:85-124` | No verified-outcome-to-variant call found | GAP; WP-2 must build it. |

**U2 conclusion:** Purchasing and DataOps definitely need the path built. Trading also needs it. SOC needs a verified-outcome bridge rather than merely its existing evaluation-time recorder. S2P has the closest implementation but its variant identifier is optional and promotion is not triggered afterward.

## 4. U3 — Promotion trigger

| Copilot | Trigger type | Location | Active? |
|---|---|---|---:|
| SOC | Per alert-processing decision: record outcome, then call promotion check | `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:332-342` | Yes, but conservation state is omitted; the SDK gate therefore fails closed unless another path supplies state. SOC also has a separate admin promotion evaluation route at `.../routers/admin.py:419-498`. |
| S2P | Manual GET promotion-check only | `s2p-copilot/backend/app/routers/s2p_evolution.py:55-57` calls `check_promotion()`; the wrapper hard-codes GREEN at `.../services/s2p_evolver.py:64-66` | Exposed, not automatic. No call follows the verified outcome path at `.../routers/s2p.py:2355-2377`. |
| Trading | Explicit API sequence: POST generate → POST shadow-test → POST promote | `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:144-167`; checks are enforced in `.../services/trading_evolver.py:265-317` | Yes, manually active. |
| Purchasing | None for live evolution | Generic router has only GET variants/history/promoted at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`; Purchasing mounts it at `copilot-sdk/apps/purchasing/backend/app/main.py:689-697` | No. |
| DataOps | None for live evolution | Same generic GET-only router at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`, mounted at `copilot-sdk/apps/dataops/backend/app/main.py:742-748` | No. |

**U3 conclusion:** Purchasing and DataOps need triggers added. S2P needs an automatic post-outcome or scheduled trigger, and the trigger must use live conservation. SOC has an active per-decision call but it is not live-provider-backed. Trading has manual triggers, not an automatic verified-outcome trigger.

## 5. U4 — Telemetry surface

| Copilot | Endpoint(s) | Response fields |
|---|---|---|
| SOC | `/evolution/recent`, `/evolution/variant-history`, `/evolution/summary`, `/soc/evolution/rejection-summary`, `/evolution/recent-events`, `/evolution/weight-history` at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:674-787,796-839` | Recent: `events`; variant history: `variant_id`, `events`, `count`; recent events: `events`, `count`, `limit`; rejection summary: `total_tested`, `total_promoted`, `total_rejected`, `rejection_breakdown`, `rejected_variants`, `provenance`; weight history: `history`, `total`, `alert_type_filter`. Aggregate summary is graph-backed through `:732-738`. |
| S2P | `/api/s2p/evolution/variants`, `/promotion-check`, `/shadow-results`, `/promoted` at `s2p-copilot/backend/app/routers/s2p_evolution.py:38-71` | Variants: `total`, `variants`, `sdk_summary`; SDK summary: `variant_count`, `active_count`, `variants`, `categories` plus S2P `domain` and `families` at `s2p-copilot/backend/app/services/s2p_evolver.py:69-85`; promotion: `promotion`; shadow/promoted shapes are delegated to the service. |
| Trading | `/api/trading/evolution/log`, `/rejection-summary`, `/active`, `/proposals` at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:65-142` | Log is a list of variant/parameter entries; rejection summary: `total_tested`, `total_promoted`, `total_rejected`, `rejection_breakdown`, `rejected_variants`, `provenance`; active: `variant`, `parameter_adjustments`, `conservation_state`, `bounds`; proposals: `proposals`, `provenance`, `note`, `conservation_state`. |
| Purchasing | Generic `/api/evolution/variants`, `/history`, `/promoted`, mounted at `copilot-sdk/apps/purchasing/backend/app/main.py:689-697` | Variants: `domain`, `variants`, `active_rules`, `promoted_rules`, `total_active`, `total_promoted`; history: `domain`, `events`, `count`; promoted: `domain`, `promoted` (`copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`). |
| DataOps | Generic `/api/evolution/variants`, `/history`, `/promoted`, mounted at `copilot-sdk/apps/dataops/backend/app/main.py:742-748` | Same generic fields as Purchasing (`copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`); configured variant payload fields are defined at `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:101-118`. |
| SDK | No standalone HTTP telemetry endpoint | `PromptVariantEvolver.get_summary()` returns `variant_count`, `active_count`, per-variant `id`, `family`, `version`, `status`, `successes`, `failures`, `total`, `success_rate`, and `categories` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`. |

### Union schema for WP-4

The target union should normalize these fields:

`domain`, `variant_id`/`id`, `family`, `version`, `status`, `active`, `promoted`, `successes`, `failures`, `total`, `success_rate`, `batches`, `improvement_pp`, `variance_pp`, `conservation_state`, `promotion_status`, `promotion_reason`, `rejection_breakdown`, `events`, `count`, `provenance`, and `last_updated`.

The union is not currently implemented as one schema. Evidence is the incompatible SDK summary (`copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`), generic router shape (`copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`), and Trading-specific dashboard shape (`copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:170-192`).

## 6. Work-package readiness

| WP | Ready? | Blockers from U1-U4 |
|---|---|---|
| WP-0 | Yes | Phase A verification is complete. The SDK primitives and separation boundary are confirmed (`copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344-369`; `graph-attention-engine-v50/gae/profile_scorer.py:408-496`). |
| WP-1 | Conditional | Proceed only after choosing the shared provider contract. S2P currently has a synchronous status getter but the evolver passes literal GREEN (`s2p-copilot/backend/app/services/s2p_evolver.py:64-66`). |
| WP-2 | No | U2/U3 are incomplete: Trading lacks verified outcome recording; Purchasing/DataOps lack both outcome recording and triggers; S2P lacks automatic promotion. Evidence: `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:212-263`; `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`; `s2p-copilot/backend/app/routers/s2p_evolution.py:55-57`. |
| WP-3 | No | Trading has custom manual generation/shadow/promotion and an UNKNOWN default provider (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:161-189,265-317`; `.../services/trading_evolver.py:391-398`). Registration/provider semantics must be decided before wiring. |
| WP-4 | Yes, schema work | Endpoint inventory is sufficient to define the union, but adapters are required because the current shapes differ (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839`; `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`). |
| WP-5 | Yes | Reward functions and per-domain penalty ratios are confirmed (`copilot-sdk/copilot_sdk/rl/reward_functions.py:8-63`; `copilot-sdk/copilot_sdk/scoring/presets/soc.py:58-60`; `.../dataops.py:60-62`). Actual per-copilot bindings still need runtime wiring verification. |
| WP-6 | No | Requires completion of provider, outcome, trigger, and telemetry work, then cross-copilot verification. |

## 7. Corrections to the work package

1. **SOC is not proven to use a live conservation provider in its SDK prompt evolver.** The SOC learning-health source is async and real (`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:240-260`), but `_sdk_config()` does not set `conservation_state_provider` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160-167`), and the normal promotion call omits state (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:332-342`).

2. **Trading’s provider hook exists but is not live by default.** `TradingAgentEvolver` accepts a provider (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:161-169`), yet the default factory uses `_default_conservation_state()` (`:49-50,391-398`) and the router does not inject `_current_conservation_status` (`copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:51-62`).

3. **S2P’s conservation gate is not live.** `check_promotion()` passes literal `"GREEN"` (`s2p-copilot/backend/app/services/s2p_evolver.py:64-66`). S2P does have a live status helper (`s2p-copilot/backend/app/routers/s2p.py:937-952`), so this is a wiring defect, not an absent source.

4. **Purchasing and DataOps configurations are not live evolvers.** Their `PromptEvolverConfig` objects and active/shadow `VariantSpec` definitions exist (`copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:174-195`; `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:77-98`), but their applications mount the generic GET-only router with a variant provider, not a configured evolver factory (`copilot-sdk/apps/purchasing/backend/app/main.py:689-697`; `copilot-sdk/apps/dataops/backend/app/main.py:742-748`).

5. **“Judgment-core separation” must not be stated as “scoring has no RL references.”** The action path remains centroid geometry, but the scorer intentionally has an RL reward/exploration/credit sidecar at `copilot-sdk/copilot_sdk/scoring/scorer.py:871-888`.

6. **Plateau values are not uniform across presets.** SDK defaults are 10/0.2/50 (`copilot-sdk/copilot_sdk/evolution/evolver.py:16-20`), while SOC/S2P and DataOps override window/cooldown (`copilot-sdk/copilot_sdk/scoring/presets/soc.py:76-80`; `.../s2p.py:78-82`; `.../dataops.py:78-82`).

## 8. Revised effort estimates

The work package should increase WP-2 from “wire existing loops” to a build-and-wire effort for **three** copilots: Trading, Purchasing, and DataOps. SOC needs a smaller verified-outcome bridge and live conservation-provider adapter; S2P needs provider replacement plus an automatic promotion trigger. WP-3 also requires Trading provider injection and a decision on whether its custom evolver or SDK `AgentEvolver` is authoritative. WP-4 requires five adapters into the union schema, not only one shared endpoint.

Recommended sequencing, based on the verified blockers:

1. Define the normalized conservation provider contract and fail-closed semantics.
2. Repair S2P and SOC provider seams.
3. Build verified outcome recording for Trading/Purchasing/DataOps and connect SOC’s audit outcome.
4. Add promotion triggers, with explicit manual/API fallback where automatic promotion is not desired.
5. Add telemetry adapters and validate the union schema.

