# RL / Evolution Consolidation — Phase B Design Finalization

Status: design-only. No implementation code or source changes were made.

This design is grounded in the Phase A verification report and the work package. The judgment core remains centroid geometry: action selection is centroid distance plus softmax at `graph-attention-engine-v50/gae/profile_scorer.py:408-496`, while centroid learning is pull/push at `:790-990`. Reward, exploration, and evolution remain procedural sidecars; the scorer’s sidecar runs after centroid learning at `copilot-sdk/copilot_sdk/scoring/scorer.py:663-794,871-888`.

The design obeys the judgment-memory constraints: production Decision reads/writes remain GraphStore/AGE-backed, domain-scoped, and non-substituting (`copilot-sdk/docs/design/judgment_memory_v2_9.md:73-91`).

## 1. Live-Conservation Contract

### Decision

Use **one SDK-level contract/protocol with per-application providers**.

This is not one SDK implementation that knows how to calculate every domain’s conservation state. Phase A found different canonical sources: SOC’s async learning-health service (`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`), S2P’s synchronous graph/calibration getter (`s2p-copilot/backend/app/routers/s2p.py:937-952`), Trading’s synchronous graph/calibration getter (`copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218`), and scorer-backed generic providers for Purchasing/DataOps (`copilot-sdk/apps/purchasing/backend/app/main.py:699-705`; `copilot-sdk/apps/dataops/backend/app/main.py:678-683`).

The SDK already provides the correct injection seam, `PromptEvolverConfig.conservation_state_provider`, at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:39-43`; promotion resolves the provider when no explicit state is supplied at `:285-301`. The gate already accepts safe string/mapping forms and rejects unknown state at `copilot-sdk/copilot_sdk/evolution/gate.py:62-78`.

### Contract shape

The following is the design contract, not implementation code:

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
    """Return the current domain provider result synchronously."""
```

The protocol belongs in the SDK evolution/conservation interface layer, not in `copilot_sdk/scoring/` as a domain implementation. The SDK must remain domain-neutral (`copilot-sdk/CLAUDE.md:22-28,39-47`). Each app owns its provider adapter.

### Contract rules

1. `status` is always present. `GREEN`, `AMBER`, `RED`, and `CALIBRATING` are normal states; `UNKNOWN` is an error/availability state.
2. `overallSafe` is `True` only when the provider has positively established GREEN. It must be `False` for AMBER, RED, CALIBRATING, or UNKNOWN. This preserves the gate’s fail-closed behavior (`copilot-sdk/copilot_sdk/evolution/gate.py:62-78`).
3. The provider is synchronous at promotion time. An async source must be refreshed into a domain-owned, bounded-lifetime snapshot before promotion is called. SOC’s current `LearningHealthMonitor.evaluate()` is async (`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`), so SOC requires an adapter/cache seam; it must not call an async function from a synchronous provider by silently returning GREEN.
4. Provider failure returns `UNKNOWN` with `overallSafe=False` or raises to the promotion caller. It must never return a literal GREEN fallback. This closes the current S2P defect at `s2p-copilot/backend/app/services/s2p_evolver.py:64-66` and Trading’s UNKNOWN-default wiring gap at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:49-50,391-398`.
5. The state must carry domain and source metadata for telemetry. It must not contain unscoped cross-domain counts; all graph-derived counts remain domain-scoped under the judgment-memory goals (`copilot-sdk/docs/design/judgment_memory_v2_9.md:82-88`).
6. The provider is the sole promotion-time source. Callers may not pass `conservation_state="GREEN"`; the SDK evolver should be invoked without an explicit state so `_resolve_conservation_state()` uses the configured provider (`copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:151-160,285-301`).

### Provider mapping

| Copilot | Provider adapter design | Synchronous promotion seam |
|---|---|---|
| SOC | Maintain a short-lived, explicitly timestamped snapshot populated by the existing `LearningHealthMonitor.evaluate()` service; stale/error snapshots become UNKNOWN. | Adapter around `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`; current promotion call is `.../routers/evolution.py:332-342` and must stop omitting live state by relying on the configured provider. |
| S2P | Adapt `_current_conservation_status(request)` into an app-owned provider object; return status plus counts/source. | Existing sync getter `s2p-copilot/backend/app/routers/s2p.py:937-952`; replace literal at `.../services/s2p_evolver.py:64-66`. |
| Trading | Inject a closure over `_current_conservation_status(graph_store_factory, domain)` into `TradingAgentEvolver`. | Existing getter `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218`; default factory seam `.../services/trading_evolver.py:391-398`. |
| Purchasing | Adapt the scorer-backed conservation payload used by the generic conservation router. | `copilot-sdk/apps/purchasing/backend/app/main.py:699-705`. |
| DataOps | Adapt the scorer-backed conservation payload used by the generic conservation router. | `copilot-sdk/apps/dataops/backend/app/main.py:678-683`. |

## 2. Canonical Wiring Template

### Design objective

Every copilot has one long-lived evolver instance, configured variants registered before serving traffic, one live provider, verified-outcome recording, an explicit promotion trigger, and the same summary contract. The SDK supports registration and outcome recording through `PromptVariantEvolver.register_variants()` and `.record_outcome()` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:57-123`; S2P already follows the first two steps at `s2p-copilot/backend/app/services/s2p_evolver.py:18-24`.

### Five-step pseudocode

This is an execution template for a coding agent, not copy-paste implementation code.

```python
# apps/<copilot>/backend/app/evolution/evolver_runtime.py

class DomainEvolutionRuntime:
    evolver: PromptVariantEvolver
    conservation: ConservationStateProvider

    def __init__(
        self,
        *,
        variants: Sequence[VariantSpec],
        config: PromptEvolverConfig,
        conservation: ConservationStateProvider,
    ) -> None:
        # STEP 1: configure the live provider; no literal GREEN.
        config.conservation_state_provider = conservation
        self.conservation = conservation
        self.evolver = PromptVariantEvolver(config=config)

        # STEP 2: register all configured active/shadow variants exactly once.
        self.evolver.register_variants(list(variants))

    # STEP 3: invoke only after verified outcome and resolved variant_id.
    def record_verified_outcome(self, variant_id: str, success: bool, category: str) -> None:
        self.evolver.record_outcome(variant_id, success, category=category)

    # STEP 4: invoke from an explicit route or post-outcome hook.
    def promote_if_eligible(self) -> dict[str, Any] | None:
        return self.evolver.check_for_promotion()

    # STEP 5: map SDK summary plus live state to the unified endpoint.
    def summary(self) -> EvolutionSummary:
        return build_unified_summary(self.evolver.get_summary(), self.conservation())
```

### Application wiring sequence

1. In each application’s startup/factory, construct the provider from the app’s canonical scorer/learning-health source.
2. Construct exactly one runtime evolver and store it in application state. Do not instantiate a new evolver in every request. This is required because the generic router currently lazily creates an `AgentEvolver` when no factory is supplied (`copilot-sdk/copilot_sdk/backend/evolution_router.py:35-49`).
3. Register configured variants before the app reports ready. Purchasing and DataOps currently define variants/config but only pass a provider to the generic router (`copilot-sdk/apps/purchasing/backend/app/main.py:689-697`; `copilot-sdk/apps/dataops/backend/app/main.py:742-748`); those seams become runtime factories.
4. At the verified outcome boundary, resolve the selected variant ID, compute the existing reward/success result, then call the runtime recorder. S2P’s conditional bridge is the reference shape at `s2p-copilot/backend/app/routers/s2p.py:1029-1065,2355-2377`.
5. Trigger promotion only after sufficient outcome/shadow evidence. Trading’s explicit generate → shadow-test → promote route sequence is a valid custom form at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:144-167`; S2P currently exposes only a manual check at `s2p-copilot/backend/app/routers/s2p_evolution.py:55-57` and needs a post-outcome or scheduled trigger.
6. Mount or expose `GET /api/self/evolution/summary` and ensure the response is generated from the same runtime instance, not a static variant configuration projection.

### Trading exception

Trading retains `TradingAgentEvolver` because it generates factor-weight perturbations and applies regime-break logic (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:53-83,265-317`). It must nevertheless implement the same provider, outcome, registration, and telemetry interfaces. Behavioral parity is required; class identity is not.

## 3. Telemetry Schema

### Canonical endpoint

All five copilots expose:

`GET /api/self/evolution/summary`

The response is the finalized form of the work-package target (`copilot-sdk/docs/design/rl_consolidation_work_package.md:66-75`):

```json
{
  "domain": "s2p",
  "schema_version": 1,
  "evolution_enabled": true,
  "conservation_state": "GREEN",
  "active_variant": {
    "id": "invoice_matching_v1",
    "family": "invoice_matching",
    "version": 1
  },
  "inventory": {
    "active": [
      {"id": "invoice_matching_v1", "family": "invoice_matching", "version": 1}
    ],
    "shadow": [
      {"id": "invoice_matching_v2", "family": "invoice_matching", "version": 2}
    ]
  },
  "variant_stats": [
    {
      "variant_id": "invoice_matching_v2",
      "family": "invoice_matching",
      "version": 2,
      "status": "shadow",
      "successes": 42,
      "failures": 8,
      "total": 50,
      "success_rate": 0.84
    }
  ],
  "recent_events": [
    {
      "event_type": "variant_generated|shadow_completed|promoted|rejected",
      "variant_id": "invoice_matching_v2",
      "reason": "insufficient_improvement|conservation|variance|promoted",
      "timestamp": "2026-08-08T00:00:00Z",
      "metrics": {
        "accuracy": 0.84,
        "baseline_accuracy": 0.79,
        "improvement_pp": 5.0,
        "variance_pp": 1.2,
        "decisions_tested": 50,
        "batches": 3
      }
    }
  ]
}
```

`schema_version` is a new additive field. The remaining top-level fields are the work-package contract; their data exists in different forms today.

### Field provenance: existing versus new

| Field | Status | Current evidence / adapter source |
|---|---|---|
| `domain` | Existing in multiple paths | Generic router returns it at `copilot-sdk/copilot_sdk/backend/evolution_router.py:57-59`; S2P adds it at `copilot-sdk/apps/../s2p_evolver.py:83-84`. |
| `evolution_enabled` | New normalized field | Existing routes expose evolution data but no uniform enabled field; generic variants shape is `.../backend/evolution_router.py:51-64`. |
| `conservation_state` | Existing but non-uniform | Trading active/proposals expose it at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:117-142`; S2P has live status elsewhere at `s2p-copilot/backend/app/routers/s2p.py:937-952`; a single summary field is new. |
| `active_variant` | Existing in Trading, derivable in SDK/S2P | Trading returns `variant` at `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:117-125`; SDK summary exposes status per variant at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`. |
| `inventory.active/shadow` | New normalized shape | S2P has registered variant payloads at `s2p-copilot/backend/app/services/s2p_evolver.py:88-93`; Purchasing/DataOps have configured payloads but no live evolver at `copilot-sdk/apps/purchasing/backend/app/evolution/evolver_config.py:182-195` and `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:85-98`. |
| `variant_stats` | Existing in SDK/S2P, new normalized name | SDK fields are `successes`, `failures`, `total`, `success_rate` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`; S2P wraps that summary at `.../s2p_evolver.py:69-85`. |
| `recent_events` | Existing under different names | SOC graph event endpoints return events at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:674-707,782-789`; generic router returns `events` at `copilot-sdk/copilot_sdk/backend/evolution_router.py:66-77`; normalized event types/reason/metrics are new. |
| `reason` and `metrics` | Existing in gate/custom Trading results, new uniform event fields | SDK gate returns reason/metrics at `copilot-sdk/copilot_sdk/evolution/gate.py:43-57`; Trading returns reason, batches, variance, and average improvement at `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:303-317`. |
| `schema_version` | New | Required to evolve the union without breaking five clients. |

### Per-copilot delta

| Copilot | Required design delta |
|---|---|
| SOC | Add a summary adapter over graph-backed lifecycle events and prompt stats; include the cached live conservation snapshot. Existing source endpoints are at `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839`. |
| S2P | Add canonical summary route backed by the module evolver, map `get_evolution_summary()` (`s2p-copilot/backend/app/services/s2p_evolver.py:69-85`), and include live provider state. |
| Trading | Map custom `evolution_log`, rejection summary, active variant, and provider state from `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:65-142`; do not use the hard-coded GREEN dashboard field currently at `.../state/compute_helpers.py:175-192`. |
| Purchasing | Replace configuration-only projection with runtime-evolver inventory/stats and add the canonical route. Current generic response is only `domain`, `variants`, active/promoted rules, and counts (`copilot-sdk/copilot_sdk/backend/evolution_router.py:51-64`). |
| DataOps | Same runtime wiring and canonical route as Purchasing; preserve configured metadata fields from `copilot-sdk/apps/dataops/backend/app/evolution/evolver_config.py:101-118`. |

## 4. Test Matrix

The matrix is parameterized over `COPILOTS = [soc, s2p, trading, purchasing, dataops]`. Tests use the real app/evolver/provider/store fixtures wherever the standing rules require it: no fake scorer, GraphStore, AGE write, or conservation helper (`copilot-sdk/CLAUDE.md:81-99`). External connectors may be mocked, and an isolated test provider may be used only as a complete stateful contract fixture, not as a replacement for the production conservation helper (`copilot-sdk/CLAUDE.md:101-111`).

| ID | Concrete assertion | Guarantee | Parametrization | Infrastructure |
|---|---|---|---|---|
| T-STARTUP | After app startup, `evolution_runtime.evolver` is non-null; its registered variant IDs equal the configured active+shadow IDs; constructing/serving five requests does not create a second evolver object. | Wiring / G2-G4 | One app factory fixture per copilot; assert Trading custom runtime through its common adapter. | App factory, configured variant provider, runtime identity probe; no network required for the pure startup portion. |
| T-NOLIT | AST scan of app evolution code finds zero calls passing a literal string to `conservation_state=` and zero assignments of a literal GREEN/AMBER/RED as the promotion source. | G2 | Scan each copilot app tree; allow test fixtures only when explicitly marked. | AST/static scan; do not rely only on grep because aliases and keyword calls matter. |
| T-AMBER | Set the real provider’s test state to AMBER, seed a candidate meeting all non-conservation thresholds, call the copilot promotion entry point, assert `promoted is False` and reason is `conservation` or `conservation_not_green`; assert active variant ID is unchanged. | G2 | Same scenario across five adapters. | Real evolver + complete provider fixture; real variant store; no scorer/store monkeypatch. |
| T-GREEN | Set provider to GREEN, seed required samples/batches and improvement at or above the configured threshold, invoke promotion, assert `promoted is True`, candidate status becomes active, prior active status becomes retired, and event type is `promoted`. | G2 + G4 | Use each copilot’s configured threshold; Trading uses its custom gate path. | Real evolver/store; deterministic shadow decisions or complete shadow fixture; provider state fixture. |
| T-SUP | Seed candidate improvement below 5pp / configured superiority threshold, assert not promoted and reason is `superiority` or `insufficient_improvement`; active ID unchanged. | G4 | SDK-based copilots use `DefaultPromotionGate`; Trading uses custom reason mapping. | Real gate/evolver; deterministic metrics. |
| T-VAR | Seed batch variance above the cap, assert not promoted and reason is `variance` or `unstable_improvement`; no active-state mutation. | G4 | SDK gate and Trading custom gate; normalize reason in telemetry only, not raw internal result. | Real shadow/gate metrics; no persistence bypass. |
| T-SAMP | Seed below required sample count or batch count, assert not promoted and reason is `sufficient_data` or `insufficient_batches`; no event claiming promotion. | G4 | SDK `promotion_min_samples` and Trading `MIN_SHADOW_BATCHES`; use per-copilot config. | Real configuration and gate. |
| T-OUTCOME | Select a known variant, submit one verified outcome through the real copilot outcome route, then assert that variant’s total increments by one, success/failure increments correctly, and telemetry reflects the new stats. | Feedback loop / G4 | S2P uses `/api/s2p/outcome`; SOC uses verified audit outcome; Trading/Purchasing/DataOps use their domain outcome route. | Real scorer/GraphStore/AGE test fixture per standing rules; external connector mocks only. |
| T-G1 | Score fixed factor input/action configuration twice with reward-function configuration changed only in the learning sidecar; assert recommended action and score probabilities are identical before learning. Then call learn and assert reward sidecar activity is recorded without an action-selection change. | G1 | Run against all five presets, including SOC’s standalone sidecar and SDK RL registry. | Real `ProfileScorer`/`CompoundingScorer`; reward config swap only; no scorer mock. |

Additional parity assertions for WP-4: every copilot’s summary has exactly the required top-level keys, `schema_version == 1`, `domain` matches the route, and every `recent_events[].event_type` is in the four-value enum. These are derived from the target schema and current heterogeneous surfaces at `copilot-sdk/docs/design/rl_consolidation_work_package.md:66-75` and `copilot-sdk/docs/design/rl_consolidation_verification.md:68-85`.

## 5. Decisions D1-D3

### D1 — SOC UCB `c=1.0` versus SDK default `1.414`

**Decision: keep `c=1.0` and document it as an intentional SOC domain override.**

The SDK default is `1.414` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:29`; SOC explicitly sets `_UCB_EXPLORATION = 1.0` and passes it into `PromptEvolverConfig` at `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:44,160-166`. The work package correctly says not to change exploration constants without an evaluation (`copilot-sdk/docs/design/rl_consolidation_work_package.md:45-50,106-109`). A future change requires a paired offline/live evaluation of exploration cost and promotion quality; WP-0/WP-5 must not alter the value.

### D2 — Trading custom evolver

**Decision: retain the custom `TradingAgentEvolver`, but require interface parity.**

It is justified by domain-specific factor perturbation (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:53-83`) and custom regime-break, batch, improvement, conservation, and variance checks (`:265-317`). Rewriting it onto the SDK evolver is explicitly out of scope (`copilot-sdk/docs/design/rl_consolidation_work_package.md:114-115`). It must consume the WP-0 provider and emit WP-4 telemetry through the common adapter. The current provider default is UNKNOWN (`.../services/trading_evolver.py:49-50,391-398`), and the current runtime starts with no registered variants (`.../services/trading_evolver.py:186-190`); both are WP-3 acceptance defects.

### D3 — SOC standalone `rl_engine.py`

**Decision: active alongside the SDK-backed evolver; not authoritative for promotion.**

The module is operationally used: its Thompson policy is defined at `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275-365`, its reward computer is instantiated at `:538-547`, and SOC triage calls its exploration proposal and posterior update at `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:684-687,2028-2032`. It is therefore not dead code.

It is not the authoritative prompt/variant promotion path: `rl_engine.py` contains reward, ledger, exploration, and credit services but no `check_for_promotion`, `AgentEvolver`, or promotion gate (`gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275-365,531-603`). SOC prompt-variant promotion is implemented by `services/evolver.py:374-414` and invoked by `routers/evolution.py:332-342`. The final architecture must document this as two sidecars with one promotion authority, and WP-5 must prove G1 so the standalone exploration behavior does not become an undocumented reward-based replacement for centroid action selection.

## 6. Execution Plan

Effort estimates are engineering days after Phase B. They include implementation, tests, mypy where Python changes occur, and app-level verification. They are larger than the original package where Phase A found missing loops.

### WP-0 — Shared live-conservation contract and provider interface

- **Files/seams:** SDK evolution configuration/provider interface at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:39-43,285-301`; gate compatibility at `copilot-sdk/copilot_sdk/evolution/gate.py:62-78`; app provider seams at SOC `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:215-249`, S2P `s2p-copilot/backend/app/routers/s2p.py:937-952`, Trading `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:199-218`, Purchasing `copilot-sdk/apps/purchasing/backend/app/main.py:699-705`, DataOps `copilot-sdk/apps/dataops/backend/app/main.py:678-683`.
- **Dependencies:** Phase B design only; first implementation WP. Must precede WP-1, WP-2, and WP-3.
- **Tests:** T-NOLIT, provider shape/UNKNOWN fail-closed assertions, T-AMBER provider portion.
- **Estimate:** 1.0–1.5d. Expanded because SOC’s source is async and Trading’s provider is not wired by default.
- **Acceptance:** one documented protocol; all five providers return synchronous normalized state; no provider has a GREEN fallback; `DefaultPromotionGate` rejects UNKNOWN/CALIBRATING.

### WP-1 — S2P provider defect

- **Files/seams:** `s2p-copilot/backend/app/services/s2p_evolver.py:18-24,64-66`; promotion route `s2p-copilot/backend/app/routers/s2p_evolution.py:55-57`; live status helper `s2p-copilot/backend/app/routers/s2p.py:937-952`.
- **Dependencies:** WP-0.
- **Tests:** T-STARTUP, T-NOLIT, T-AMBER, T-GREEN, and T-OUTCOME for S2P.
- **Estimate:** 0.5d.
- **Acceptance:** no literal conservation state; S2P promotion reads the provider; AMBER/UNKNOWN block; GREEN with valid evidence promotes; existing outcome route remains contract-compatible.

### WP-2 — Purchasing and DataOps complete spine

- **Files/seams:** Purchasing app mount `copilot-sdk/apps/purchasing/backend/app/main.py:689-705`, config `.../evolution/evolver_config.py:174-195`, event outcome route `.../routers/event_router.py:31-33`; DataOps app mount `copilot-sdk/apps/dataops/backend/app/main.py:678-683,742-748`, config `.../evolution/evolver_config.py:77-124`.
- **Dependencies:** WP-0; coordinate with WP-4 route contract. WP-2 must define each domain’s verified outcome identifier and promotion trigger before coding.
- **Tests:** T-STARTUP, T-OUTCOME, T-AMBER, T-GREEN, T-SUP, T-VAR, T-SAMP, and telemetry parity for both.
- **Estimate:** 2.0–3.0d total (1.0–1.5d each). **Scope expanded** from wiring-only: Phase A found no production evolver, no verified evolution outcome loop, and no promotion trigger.
- **Acceptance:** one runtime evolver per app; configured active/shadow variants registered at startup; real verified outcomes update stats; explicit trigger exists; live provider gates promotion; canonical summary endpoint is populated from runtime state.

### WP-3 — Trading registration and interface parity

- **Files/seams:** registration/runtime initialization `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:161-190`; provider factory `:391-398`; promotion checks `:265-317`; router factory/trigger surface `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:51-62,144-167`.
- **Dependencies:** WP-0. WP-4 schema should be agreed before adapter completion.
- **Tests:** T-STARTUP, T-AMBER, T-GREEN, T-SUP, T-VAR, T-SAMP; shadow→promote cycle; T-OUTCOME after adding verified outcome recording.
- **Estimate:** 1.5–2.0d. **Scope expanded** from registration: provider injection and outcome recording are also missing/unsafe by default.
- **Acceptance:** configured variants exist at boot; live provider is injected; custom gate preserves regime/batch/variance safety; verified outcomes update variant stats; telemetry maps custom reasons without weakening them.

### WP-4 — Telemetry parity

- **Files/seams:** SDK summary source `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:163-184`; generic router `copilot-sdk/copilot_sdk/backend/evolution_router.py:51-86`; SOC endpoints `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:716-839`; S2P `s2p-copilot/backend/app/routers/s2p_evolution.py:38-71`; Trading `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:65-142`; Purchasing/DataOps mounts `copilot-sdk/apps/purchasing/backend/app/main.py:689-697` and `copilot-sdk/apps/dataops/backend/app/main.py:742-748`.
- **Dependencies:** WP-0 for conservation field; WP-1/2/3 runtime state; can design adapters in parallel with WP-2/WP-3, but final integration follows them.
- **Tests:** all summary shape assertions; recent-event enum/reason/metrics parity; Rejection Moment equivalence.
- **Estimate:** 1.5–2.0d. **Scope expanded** from one endpoint addition to five adapters because existing response shapes differ materially.
- **Acceptance:** all five expose `GET /api/self/evolution/summary` with identical top-level schema, live conservation state, active/shadow inventory, stats, and recent reason-coded events.

### WP-5 — Reward bindings and test parity

- **Files/seams:** RL registry `copilot-sdk/copilot_sdk/rl/presets.py:16-53`; reward implementations `copilot-sdk/copilot_sdk/rl/reward.py:32-46` and `.../reward_functions.py:8-63`; scorer sidecar `copilot-sdk/copilot_sdk/scoring/scorer.py:871-888`; domain presets `copilot-sdk/copilot_sdk/scoring/presets/{soc,s2p,trading,purchasing,dataops}.py:58-68`; SOC standalone engine `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:37-80,275-365`.
- **Dependencies:** WP-0 through WP-4 for full parity; reward unit checks can run in parallel with WP-2/WP-3.
- **Tests:** T-G1, T-OUTCOME, all gate tests, and exact reward-function/ratio assertions. Add an explicit SOC/DataOps binding decision because the SDK registry contains Trading/Purchasing/DataOps/S2P but not SOC (`copilot-sdk/copilot_sdk/rl/presets.py:16-33`).
- **Estimate:** 1.5–2.0d. **Scope expanded** because SOC uses a separate active `rl_engine.py` and the registry does not list SOC.
- **Acceptance:** every domain’s intended reward function and ratio are explicit; learn sidecar updates reward/exploration/credit only; fixed-input action is invariant under reward configuration changes; all T-STARTUP through T-G1 pass.

### WP-6 — Architecture documentation and final audit

- **Files:** new `copilot-sdk/docs/design/rl_architecture.md`; source anchors `copilot-sdk/copilot_sdk/scoring/scorer.py:871-888`, `graph-attention-engine-v50/gae/profile_scorer.py:408-496`, and this design document.
- **Dependencies:** WP-0 through WP-5.
- **Tests:** documentation/source consistency review; rerun the complete matrix and inspect all five summary endpoints.
- **Estimate:** 0.5–1.0d.
- **Acceptance:** architecture document describes the G1 boundary, conservation contract, per-copilot provider map, reward bindings, D1-D3, and current telemetry schema with no stale literal-GREEN or “no RL references in scoring” claims.

### Parallelization and recommended coding prompts

| Prompt | Work packages | Constraint |
|---|---|---|
| Prompt 1 | WP-0 | Must land first; touches SDK contract and provider adapters. No app promotion changes before contract is agreed. |
| Prompt 2 | WP-1 + WP-2 | Can proceed in parallel after WP-0; separate S2P, Purchasing, and DataOps files. WP-2 remains the larger build scope. |
| Prompt 3 | WP-3 | Can proceed in parallel with WP-2 after WP-0; Trading custom implementation remains intact. |
| Prompt 4 | WP-4 | Adapter work can begin after schema approval and run alongside WP-2/WP-3, but final tests wait for runtime state. |
| Prompt 5 | WP-5 | Reward unit/binding analysis can run in parallel; full parity gate waits for WP-1 through WP-4. |
| Prompt 6 | WP-6 | Final documentation and audit only after all implementation work is complete. |

### Total estimate

Implementation after Phase B: **8.5–12.0 engineering days**, depending on whether the three missing verified-outcome paths require new domain receipt models and whether SOC’s async health snapshot already has a suitable lifecycle cache. This is higher than the original 5–6d estimate because Phase A found expanded WP-2/WP-3/WP-4 scope.

## 7. Implementation Readiness Checklist

| WP | Design complete? | Dependencies resolved? | Test spec ready? | Effort |
|---|---:|---:|---:|---:|
| WP-0 | Yes | Yes for design; implementation first | Yes: T-NOLIT, provider fail-closed, T-AMBER | 1.0–1.5d |
| WP-1 | Yes | WP-0 required | Yes: S2P startup/conservation/promotion/outcome | 0.5d |
| WP-2 | Yes | WP-0 and domain outcome decisions required | Yes: full gate + outcome + telemetry matrix | 2.0–3.0d |
| WP-3 | Yes | WP-0; Trading outcome design required | Yes: startup, shadow/promote, provider, outcome | 1.5–2.0d |
| WP-4 | Yes | Runtime state from WP-1/2/3 required for final integration | Yes: schema/event parity | 1.5–2.0d |
| WP-5 | Yes | Full parity depends on WP-0–4; reward binding gaps identified | Yes: T-OUTCOME and T-G1 plus exact bindings | 1.5–2.0d |
| WP-6 | Yes | WP-0–5 | Yes: final matrix and doc/source audit | 0.5–1.0d |

