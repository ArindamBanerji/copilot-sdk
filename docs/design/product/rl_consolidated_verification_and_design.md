# RL / Evolution Consolidated Verification and Final Design

**Phase:** A verification + B design finalization  
**Status:** Design-only record; no implementation changes are included.  
**Supersedes for handoff:** `rl_consolidation_verification.md` and `rl_consolidation_design_final.md` as the single working reference. The two source documents remain available for detailed history.

## 0. Executive decision

Use a shared SDK conservation-state contract with per-copilot synchronous providers. Keep centroid judgment and procedural RL/evolution separate. Every copilot must converge on one evolution spine:

1. one long-lived evolver;
2. active/shadow variants registered at startup;
3. live conservation provider, never a literal state;
4. verified-outcome recording;
5. common summary/history telemetry.

The canonical judgment core remains centroid-based: action probabilities are centroid distance plus softmax at `graph-attention-engine-v50/gae/profile_scorer.py:408-496`; centroid learning is pull/push at `:790-990`. The SDK scorer reward path is a learning/evolution sidecar at `copilot-sdk/copilot_sdk/scoring/scorer.py:663-794,871-888`. SOC’s separate action-affecting RL exploration hook is governed by the strict G1 decision recorded below: production exploration is disabled immediately, and the permanent design keeps live decisions centroid-authoritative (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:684-703`; decision authority `docs/design/soc_g1_boundary_decision_memo.md:60-64`).

The design must also preserve the judgment-memory constraints: production Decision reads/writes use GraphStore/AGE, are domain-scoped, and do not silently substitute another store (`copilot-sdk/docs/design/judgment_memory_v2_9.md:73-91`).

## 1. Phase A — Verified current state

| Finding | Status | Evidence |
|---|---|---|
| UCB1 formula: `success_rate + c * sqrt(ln(max(N,2)) / n_i)` | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:344-369` computes `log(max(total,2))`, mean, and `c * sqrt(log/n)`. |
| SDK exploration constant is 1.414 | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29`. |
| SOC overrides UCB constant to 1.0 | CONFIRMED | `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44,160-166`. |
| Conservation-bounded Thompson/Beta policy exists | CONFIRMED | `copilot-sdk/copilot_sdk/rl/exploration.py:12-25,27-44,118-122`. AMBER/RED suppress exploration. |
| Reward clips to [-1,1] and scales negative values by penalty ratio | CONFIRMED | `copilot-sdk/copilot_sdk/rl/reward.py:32-46`. |
| Binary, GradedFinancial, PnL, and WasteReduction functions exist | CONFIRMED | `copilot-sdk/copilot_sdk/rl/reward_functions.py:8-63`. |
| Penalty ratios: SOC 20, S2P 5, Trading 3, Purchasing 3, DataOps 10 | CONFIRMED | `copilot-sdk/copilot_sdk/scoring/presets/soc.py:58-60`; `.../s2p.py:60-62`; `.../trading.py:65-68`; `.../purchasing.py:62-64`; `.../dataops.py:60-62`. |
| Default gate: 5pp, 0.70 floor, 10 minimum shadow decisions | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/gate.py:12-20,30-57`. Unknown/missing conservation fails closed at `:62-78`. |
| SDK PlateauConfig defaults: 10 / 0.2 / 50 | CONFIRMED for SDK | `copilot-sdk/copilot_sdk/evolution/evolver.py:16-20`. SOC/S2P override to 11/55 at `copilot-sdk/copilot_sdk/scoring/presets/soc.py:76-80` and `.../s2p.py:78-82`; DataOps uses 12/60 at `.../dataops.py:78-82`. |
| `conservation_state_provider` hook exists | CONFIRMED | `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:39-43,285-301`. |
| All five production copilots already have complete live wiring | CONTRADICTED | S2P passes literal GREEN at `s2p-copilot/backend/app/services/s2p_evolver.py:64-66`; Trading’s default provider is UNKNOWN at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:49-50,391-398`; Purchasing/DataOps mount generic GET-only routers rather than runtime evolvers at `copilot-sdk/apps/purchasing/backend/app/main.py:689-697` and `copilot-sdk/apps/dataops/backend/app/main.py:742-748`. |
| Judgment core is separate from RL/evolution | GAP / SOC-specific contradiction requires resolution | Canonical centroid path: `graph-attention-engine-v50/gae/profile_scorer.py:408-496`. The SDK scorer sidecar runs after learning at `copilot-sdk/copilot_sdk/scoring/scorer.py:871-888`, but SOC’s triage flow calls RL exploration at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:684-691` and can overwrite `selected_action` at `:692-703`. |

### 1A. Phase A elevation — SOC G1 action-flow audit and boundary decision

**Decision recorded: Option A — strict G1, reached through Option C immediately.** The founder memo selects immediate production flag-off, followed by permanent removal of the live-action override; future exploration is proposal/shadow-only unless a separately governed, per-domain, stakes-aware policy explicitly authorizes an exception (`docs/design/soc_g1_boundary_decision_memo.md:52-64`).

**Phase A status: RESOLVED for design; implementation verification remains a gate.** G1 is defined strictly: the live SOC decision must remain the centroid-selected action. The production flag must be false before WP-0/WP-5 acceptance, and the final test must prove that no live decision uses `decision_method == "gae_scoring_explored"` (`docs/design/soc_g1_boundary_decision_memo.md:66-75`).

The SOC flow has three distinct RL touchpoints:

| Touchpoint | Truth | Evidence |
|---|---|---|
| Exploration proposal | Action-affecting, not merely post-decision | The flow first has `_scoring_result.probabilities`, then calls `get_exploration_policy().propose(...)` at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:654-691`. If exploration returns an action and learning is enabled, it assigns that action to `selected_action` at `:692-703`. |
| Reward computation | Post-outcome learning hook | The verified outcome path computes `RewardComputer().compute(...)` only after `action_name` and `correct_bool` are available at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1937-1950`. |
| Posterior update | Post-outcome learning hook | The flow reads recorded exploration fields and updates the posterior with `correct_bool` at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2015-2037`. |

**Verified truth:** the reward computation and posterior update are post-outcome hooks, but the exploration proposal is not. It is downstream of centroid scoring and can change the action that proceeds to routing. Therefore the sentence “SOC’s `rl_engine.py` calls are post-decision learning hooks” is contradicted by implementation. The narrower statement “SOC’s canonical baseline probabilities come from centroid scoring, while SOC may apply a separate conservation-bounded exploration override” is supported by `triage.py:654-703`.

**Required implementation gate:**

1. Immediately set the production `RL_EXPLORATION_ENABLED` flag false and verify the flag fully gates the override; the memo requires confirmation of the production configuration path and absence of a second override path (`docs/design/soc_g1_boundary_decision_memo.md:66-75`).
2. Permanently route RL proposals to learning/shadow evaluation rather than assigning them to live `selected_action`; the centroid action remains authoritative at `triage.py:697-703`.
3. Add a SOC-specific regression with fixed centroid probabilities asserting that a live decision never has `decision_method == "gae_scoring_explored"` and that changing SOC RL reward/exploration configuration does not change the recommended action or probabilities (`docs/design/soc_g1_boundary_decision_memo.md:74-75`).
4. Preserve the future governed-policy direction: shadow-only by default for security/high-stakes domains; any live exploration opt-in requires customer-visible, per-domain, stakes-aware governance (`docs/design/soc_g1_boundary_decision_memo.md:52-58`).

## 2. Phase A — U1: Live conservation source

### Resolution

The platform needs **one SDK contract/protocol with per-app providers**, not one domain-blind SDK getter. The sources are not uniform: SOC uses an async learning-health service, while S2P, Trading, Purchasing, and DataOps have synchronous graph/scorer-derived seams.

The SDK gate already accepts safe string/mapping forms and rejects unknown state at `copilot-sdk/copilot_sdk/evolution/gate.py:62-78`. Promotion resolves an explicit argument or the configured provider at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:151-160,285-301`.

| Copilot | Canonical source | Sync at promotion? | Current wiring truth |
|---|---|---:|---|
| SOC | `LearningHealthMonitor.evaluate(graph_client)` at `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`; exposed at `.../routers/framework_router.py:747-750` | No; async | GAP. SOC config has no provider at `.../services/evolver.py:160-167`, and normal promotion omits state at `.../routers/evolution.py:332-342`. Build a timestamped synchronous snapshot adapter; stale/error state is UNKNOWN. |
| S2P | `_current_conservation_status(request)` at `s2p-copilot/backend/app/routers/s2p.py:937-952` | Yes | GAP in wiring. It is used to pause outcome recording at `:1042-1045`, but promotion hard-codes GREEN at `.../services/s2p_evolver.py:64-66`. |
| Trading | `_current_conservation_status(graph_store_factory, domain)` at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218` | Yes | GAP in default injection. The custom evolver accepts a provider at `.../services/trading_evolver.py:161-169`, but the factory uses UNKNOWN at `:391-398`. |
| Purchasing | Scorer-backed helper at `copilot-sdk/apps/purchasing/backend/app/main.py:538-556`; generic router receives `scorer_proxy` at `:699-705` | Yes | GAP. The source feeds conservation endpoints, not a live evolver. |
| DataOps | Scorer-backed generic provider at `copilot-sdk/apps/dataops/backend/app/main.py:678-683` | Yes | GAP. No production PromptVariantEvolver is constructed. |

### Contract

The following is design pseudocode:

```python
class ConservationState(TypedDict, total=False):
    status: Literal["GREEN", "AMBER", "RED", "CALIBRATING", "UNKNOWN"]
    overallSafe: bool
    domain: str
    verified_count: int
    correct_count: int
    total_decisions: int
    penalty_ratio: float
    source: str
    observed_at: str
    reason: str | None


class ConservationStateProvider(Protocol):
    def __call__(self) -> ConservationState: ...


def get_live_conservation_state() -> ConservationState:
    """Synchronously return the current provider result."""
```

Contract rules:

- `status` is always present; CALIBRATING and UNKNOWN are not safe.
- `overallSafe` is true only for positively established GREEN.
- Provider failure returns UNKNOWN/false or raises; it never returns literal GREEN.
- The provider is synchronous at promotion time. SOC must adapt its async health source into an explicit, timestamped snapshot rather than calling async code from a sync path.
- Domain/source/timestamp metadata are required for telemetry; graph counts remain domain-scoped.
- Promotion callers invoke `check_for_promotion()` without a literal state so the configured provider is authoritative.

The contract type belongs in an SDK-neutral evolution/conservation interface layer. The SDK is a public domain-neutral package and must not import app/domain internals (`copilot-sdk/CLAUDE.md:22-28,39-47`).

## 3. Phase A — U2: Outcome-recording path

| Copilot | Status | Evidence and required action |
|---|---|---|
| SOC | PARTIAL/GAP | `record_decision_outcome()` exists at `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340-354` and is called from evaluation processing at `.../routers/evolution.py:332-342`. Verified audit outcomes are separate at `.../framework/audit.py:149-172`; a verified-outcome bridge is required. |
| S2P | CONDITIONAL | `record_triage_outcome()` is at `s2p-copilot/backend/app/services/s2p_evolver.py:48-61`; verified `/outcome` invokes the bridge at `s2p-copilot/backend/app/routers/s2p.py:2266-2276,2355-2377`. It skips when `variant_id` is absent or learning is paused at `:1029-1062`. |
| Trading | GAP | Custom evolver records shadow results at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:212-263`, but no verified `record_outcome` path exists. Build it. |
| Purchasing | GAP | `EventPlanner.record_outcome()` at `copilot-sdk/apps/purchasing/backend/app/services/event_planner.py:73+` records planner metrics, not evolution variant statistics; route call is `.../routers/event_router.py:31-33`. Build the evolution bridge. |
| DataOps | GAP | Configured variants exist at `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:85-124`, but no production evolution outcome recorder was found. Build it. |

## 4. Phase A — U3: Promotion trigger

| Copilot | Current trigger | Truth / design action |
|---|---|---|
| SOC | Per alert processing at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:332-342`; separate admin evaluation at `.../routers/admin.py:419-498` | Active but not live-provider-backed. Repair provider wiring. |
| S2P | Manual GET `/promotion-check` at `s2p-copilot/backend/app/routers/s2p_evolution.py:55-57` | Exposed but not automatic and uses literal GREEN. Add post-verified-outcome or scheduled trigger. |
| Trading | POST generate, shadow-test, promote at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:144-167` | Active manual sequence. Preserve it; add verified outcome recording and live provider. |
| Purchasing | Generic GET-only variants/history/promoted router at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`, mounted at `copilot-sdk/apps/purchasing/backend/app/main.py:689-697` | No live promotion trigger. Add explicit route or controlled post-outcome hook. |
| DataOps | Same generic GET-only router at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`, mounted at `copilot-sdk/apps/dataops/backend/app/main.py:742-748` | No live promotion trigger. Add explicit route or controlled post-outcome hook. |

## 5. Phase A — U4: Telemetry inventory

| Copilot | Existing surface | Existing fields |
|---|---|---|
| SOC | `/evolution/variant-history`, `/evolution/summary`, `/soc/evolution/rejection-summary`, `/evolution/recent-events`, `/evolution/weight-history` at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839` | Events/history/count; rejection totals/breakdown/provenance; weight history/total/filter. |
| S2P | `/api/s2p/evolution/variants`, `/promotion-check`, `/shadow-results`, `/promoted` at `s2p-copilot/backend/app/routers/s2p_evolution.py:38-71` | `total`, `variants`, SDK `variant_count`, `active_count`, per-variant stats, `categories`, `domain`, `families` at `.../services/s2p_evolver.py:69-85`. |
| Trading | `/api/trading/evolution/log`, `/rejection-summary`, `/active`, `/proposals` at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:65-142` | Log, rejection totals/breakdown, active variant/adjustments/state/bounds, proposal list/provenance/note/state. |
| Purchasing | Generic `/api/evolution/variants`, `/history`, `/promoted` at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86` | Domain, variants, active/promoted rules, counts, events, promoted list. |
| DataOps | Same generic surface at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86` | Same generic fields plus configured payload metadata at `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:101-118`. |

## 6. Phase B — Canonical wiring template

Every app follows this design sequence. It is pseudocode, not implementation:

```python
class DomainEvolutionRuntime:
    evolver: PromptVariantEvolver
    conservation: ConservationStateProvider

    def __init__(self, variants, config, conservation):
        # 1. Configure provider; no literal GREEN.
        config.conservation_state_provider = conservation
        self.conservation = conservation
        self.evolver = PromptVariantEvolver(config=config)

        # 2. Register all active/shadow variants once at startup.
        self.evolver.register_variants(list(variants))

    # 3. Call only from verified outcome path.
    def record_verified_outcome(self, variant_id, success, category):
        self.evolver.record_outcome(variant_id, success, category=category)

    # 4. Call from explicit route or post-outcome hook.
    def promote_if_eligible(self):
        return self.evolver.check_for_promotion()

    # 5. Map runtime summary and live state to common telemetry.
    def summary(self):
        return build_unified_summary(self.evolver.get_summary(), self.conservation())
```

SDK registration/outcome capabilities are at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:57-123`. S2P is the reference for startup registration at `s2p-copilot/backend/app/services/s2p_evolver.py:18-24`; Trading is the reference for a justified custom gate at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:265-317`.

The generic router currently creates a lazy empty `AgentEvolver` if no factory is supplied (`copilot-sdk/copilot_sdk/backend/evolution_router.py:35-49`). Purchasing and DataOps must replace that configuration-only projection with an app-owned runtime factory.

## 7. Phase B — Unified telemetry schema

All five expose:

`GET /api/self/evolution/summary`

```json
{
  "domain": "s2p",
  "schema_version": 1,
  "evolution_enabled": true,
  "conservation_state": "GREEN",
  "active_variant": {"id": "invoice_matching_v1", "family": "invoice_matching", "version": 1},
  "inventory": {
    "active": [{"id": "invoice_matching_v1", "family": "invoice_matching", "version": 1}],
    "shadow": [{"id": "invoice_matching_v2", "family": "invoice_matching", "version": 2}]
  },
  "variant_stats": [{
    "variant_id": "invoice_matching_v2", "family": "invoice_matching", "version": 2,
    "status": "shadow", "successes": 42, "failures": 8, "total": 50, "success_rate": 0.84
  }],
  "recent_events": [{
    "event_type": "variant_generated|shadow_completed|promoted|rejected",
    "variant_id": "invoice_matching_v2",
    "reason": "insufficient_improvement|conservation|variance|promoted",
    "timestamp": "2026-08-08T00:00:00Z",
    "metrics": {"accuracy": 0.84, "baseline_accuracy": 0.79, "improvement_pp": 5.0,
                "variance_pp": 1.2, "decisions_tested": 50, "batches": 3}
  }]
}
```

`schema_version` is new. The other concepts exist but require normalization: SDK stats at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`, generic event/history fields at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`, SOC graph-backed events at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839`, and Trading gate metrics at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:303-317`.

Per-copilot changes:

- **SOC:** adapter over graph lifecycle events and prompt stats; include a timestamped conservation snapshot (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839`).
- **S2P:** adapter over `get_evolution_summary()` and live provider (`s2p-copilot/backend/app/services/s2p_evolver.py:69-85`).
- **Trading:** map custom log/rejection/active/proposal results (`copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:65-142`); do not use the hard-coded GREEN dashboard field at `.../state/compute_helpers.py:175-192`.
- **Purchasing/DataOps:** runtime-backed inventory/stats, replacing configuration-only generic responses at `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-64`.

## 8. Phase B — Test matrix

Parameterize over `soc`, `s2p`, `trading`, `purchasing`, and `dataops`. Tests must use real scorer/GraphStore/AGE paths where applicable; the SDK standing rules forbid fake scorers, stores, writes, and conservation helpers (`copilot-sdk/CLAUDE.md:81-99`). External connectors may be mocked under the stated exceptions at `:101-111`.

| ID | Concrete assertion | Guarantee | Infrastructure |
|---|---|---|---|
| T-STARTUP | Exactly one runtime evolver exists after startup; registered IDs equal configured active+shadow IDs; repeated requests preserve object identity. | Wiring/G2/G4 | App factory, runtime identity probe, configured variant provider. |
| T-NOLIT | AST scan finds zero app calls passing literal `conservation_state=` and zero literal GREEN/AMBER/RED promotion sources. | G2 | Static AST scan per app. |
| T-AMBER | Candidate satisfies all other thresholds; provider returns AMBER; promotion is false with `conservation`/`conservation_not_green`; active ID unchanged. | G2 | Real evolver/store plus complete provider state fixture. |
| T-GREEN | GREEN plus required samples/batches and threshold improvement promotes candidate, retires prior active, and emits `promoted`. | G2/G4 | Real gate/evolver; Trading custom path normalized through adapter. |
| T-SUP | Improvement below superiority threshold rejects with `superiority`/`insufficient_improvement`; no active mutation. | G4 | Real gate and deterministic metrics. |
| T-VAR | Variance over cap rejects with `variance`/`unstable_improvement`; no promotion. | G4 | Real shadow/gate metrics. |
| T-SAMP | Samples/batches below configured minimum reject with `sufficient_data`/`insufficient_batches`. | G4 | Per-copilot config and real gate. |
| T-OUTCOME | Verified outcome increments selected variant total and exactly one success/failure counter; telemetry reflects it. | Feedback/G4 | Real outcome route, scorer, GraphStore/AGE fixture. |
| T-G1 | For SDK-based copilots, changing only reward-function configuration leaves fixed-input recommended action and probabilities unchanged; learning sidecar records reward without changing action selection. | G1 | Real ProfileScorer/CompoundingScorer; no scorer mock. |
| T-G1-SOC-AUDIT | With production `RL_EXPLORATION_ENABLED == False`, assert no live decision has `decision_method == "gae_scoring_explored"`; with fixed centroid probabilities, changing SOC RL reward/exploration configuration leaves the recommended action and probabilities unchanged. Trace `triage.py:654-703` to prove the override is disabled and no second override path exists. | G1 / Phase A gate | Real SOC triage, real ProfileScorer/CompoundingScorer, real conservation-health path, deterministic configuration; no fake scorer or conservation helper. This must pass before cross-copilot T-G1 acceptance. |

Additional WP-4 parity assertions: all summaries have exactly the required top-level keys, `schema_version == 1`, matching domain, and event types limited to generated/shadow/promoted/rejected. The work-package target is at `copilot-sdk/docs/design/rl_consolidation_work_package.md:66-87`.

## 9. Phase B — Decisions

### D1 — SOC UCB constant

**Keep `c=1.0`; document as an intentional SOC override.** SDK default is 1.414 at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29`; SOC sets 1.0 at `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44,160-166`. Do not change without an exploration-quality evaluation, as required by the work package (`copilot-sdk/docs/design/rl_consolidation_work_package.md:45-50,106-109`).

### D2 — Trading custom evolver

**Keep it. Require interface parity.** Factor-weight generation is domain-specific at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:53-83`; custom regime, batch, improvement, conservation, and variance checks are at `:265-317`. It must consume the WP-0 provider, register variants, add verified outcome recording, and emit WP-4 telemetry. Rewriting onto the SDK evolver is out of scope (`copilot-sdk/docs/design/rl_consolidation_work_package.md:114-115`).

### D3 — SOC standalone `rl_engine.py`

**Active alongside the SDK-backed evolver; not authoritative for promotion.** Its reward/exploration/credit services are used by SOC (`gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275-365,538-603`; `.../routers/triage.py:684-691,1940-1942,2028-2032`). It contains no promotion gate/evolver path. SOC prompt-variant promotion is authoritative through `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:374-414` and `.../routers/evolution.py:332-342`. Under the strict G1 decision, its exploration proposal is not allowed to replace live `selected_action`; production flag-off is immediate and permanent architecture routes proposals to learning/shadow (`docs/design/soc_g1_boundary_decision_memo.md:60-64`).

## 10. Execution plan WP-0 through WP-6

| WP | Scope and source seams | Dependencies | Tests | Estimate / acceptance |
|---|---|---|---|---|
| WP-0 | Define SDK provider contract around `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:39-43,285-301`; wire app provider adapters at SOC `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`, S2P `s2p-copilot/backend/app/routers/s2p.py:937-952`, Trading `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218`, Purchasing `copilot-sdk/apps/purchasing/backend/app/main.py:699-705`, DataOps `copilot-sdk/apps/dataops/backend/app/main.py:678-683`. Also verify the immediate production `RL_EXPLORATION_ENABLED=False` path required by strict G1. | First | T-NOLIT, provider shape, fail-closed T-AMBER, T-G1-SOC-AUDIT flag/path checks | **1.0–1.5d plus SOC flag verification**, expanded for SOC async snapshot, Trading default injection, and strict G1. Acceptance: all five sync providers, no GREEN fallback, UNKNOWN/CALIBRATING blocked, production SOC exploration disabled. |
| WP-1 | Replace S2P literal at `s2p-copilot/backend/app/services/s2p_evolver.py:64-66`; preserve route at `.../routers/s2p_evolution.py:55-57`. | WP-0 | S2P T-STARTUP, T-NOLIT, T-AMBER, T-GREEN, T-OUTCOME | **0.5d**. Acceptance: promotion uses provider and outcome contract remains intact. |
| WP-2 | Instantiate live evolvers and register variants in Purchasing `copilot-sdk/apps/purchasing/backend/app/main.py:689-697`, config `.../evolution/evolver_config.py:174-195`; DataOps `copilot-sdk/apps/dataops/backend/app/main.py:742-748`, config `.../evolution/evolver_config.py:77-124`; build missing outcome/trigger paths. | WP-0; coordinate schema with WP-4 | Full gate/outcome/telemetry tests for both | **2.0–3.0d**, expanded from wiring-only because U2/U3 are absent. Acceptance: one runtime evolver, registered variants, verified outcome loop, trigger, provider, summary. |
| WP-3 | Register Trading variants and inject provider at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:161-190,391-398`; preserve custom checks `:265-317`; add verified outcome path. | WP-0 | T-STARTUP, all gate tests, shadow→promote, T-OUTCOME | **1.5–2.0d**, expanded beyond registration. Acceptance: live provider, registered variants, outcome stats, common telemetry. |
| WP-4 | Add `/api/self/evolution/summary` adapters over SDK `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`, generic router `.../backend/evolution_router.py:51-86`, SOC `gen-ai.../routers/evolution.py:716-839`, S2P `.../s2p_evolution.py:38-71`, Trading `.../evolution_router.py:65-142`, and Purchasing/DataOps mounts. | WP-0; final runtime state from WP-1/2/3 | Schema/event parity and Rejection Moment tests | **1.5–2.0d**, expanded to five adapters. Acceptance: identical top-level schema with live state, inventory, stats, and reason-coded events. |
| WP-5 | Verify RL registry `copilot-sdk/copilot_sdk/rl/presets.py:16-53`, reward functions `.../reward_functions.py:8-63`, scorer sidecar `.../scorer.py:871-888`, domain presets, and SOC engine `gen-ai.../services/rl_engine.py:37-80,275-365`. | Strict G1 decision is fixed: production flag-off and permanent proposal/shadow routing must be verified before final parity. | T-G1-SOC-AUDIT, T-G1, T-OUTCOME, exact function/ratio assertions, full matrix | **1.5–2.0d plus SOC G1 verification**, expanded because SOC is outside SDK registry and its exploration hook can alter action. Acceptance: production never emits `gae_scoring_explored`; fixed-input action/probabilities are invariant to RL config; then cross-copilot G1 passes. |
| WP-6 | Create `copilot-sdk/docs/design/rl_architecture.md` from the verified anchors and final design. | WP-0 through WP-5 | Final matrix and documentation/source audit | **0.5–1.0d**. Acceptance: no stale literal-GREEN, no false “no RL references” claim, documented G1 boundary and D1-D3. |

### Recommended coding prompt grouping

1. **Prompt 1:** WP-0 only; contract and provider semantics first.
2. **Prompt 2:** WP-1 + WP-2 after WP-0; separate S2P/Purchasing/DataOps files.
3. **Prompt 3:** WP-3 after WP-0; Trading remains custom.
4. **Prompt 4:** WP-4 after schema approval; adapter work can overlap WP-2/WP-3, final integration waits for runtime state.
5. **Prompt 5:** WP-5; reward tests can begin early, final parity waits for WP-1–WP-4.
6. **Prompt 6:** WP-6 final documentation/audit.

**Total post-Phase-B estimate:** **8.5–12.0 engineering days plus the SOC G1 audit**, increased from the original 5–6d estimate because Phase A found missing verified-outcome loops in three copilots, non-live provider wiring in SOC/Trading/S2P, five telemetry adapters rather than one shared existing surface, and an action-affecting SOC exploration hook that must be resolved before G1 is accepted.

## 11. Readiness checklist

| WP | Design complete? | Dependencies resolved? | Test specification ready? | Effort |
|---|---:|---:|---:|---:|
| WP-0 | Yes | Ready to implement first | Yes | 1.0–1.5d |
| WP-1 | Yes | WP-0 required | Yes | 0.5d |
| WP-2 | Yes | WP-0 plus domain outcome decisions | Yes | 2.0–3.0d |
| WP-3 | Yes | WP-0 plus Trading outcome design | Yes | 1.5–2.0d |
| WP-4 | Yes | Runtime state from WP-1/2/3 for final integration | Yes | 1.5–2.0d |
| WP-5 | Conditional | Strict G1 is decided; production flag-off and no-override verification must pass | Yes, with SOC G1 gate | 1.5–2.0d + SOC verification |
| WP-6 | Yes | WP-0–5 | Yes | 0.5–1.0d |
