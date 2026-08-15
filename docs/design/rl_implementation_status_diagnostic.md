# RL / Evolution Implementation Status Diagnostic

Audit date: 2026-08-15

Scope: read-only comparison of the RL/evolution design documents with the
current SDK, SOC, S2P, Trading, Purchasing, and DataOps code. No production
code was changed for this audit. `copilot-sdk/CLAUDE.md` was read first;
behavioral conclusions below are based on source inspection, with the design
documents treated as intent rather than proof of implementation.

## Executive finding

The SDK primitives are substantially implemented: reward functions,
conservation-bounded Thompson sampling, UCB selection, promotion thresholds,
credit helpers, variant evolution, ledgers, and GraphStore V2 interfaces all
exist. The five-copilot production spine is not yet equivalent across domains.

The current tree is ahead of the older Phase-A scan in two places: Purchasing
and DataOps now construct a `PromptVariantEvolver` and inject a
`ScorerBackedProvider` (`apps/purchasing/backend/app/main.py:490-497`,
`apps/dataops/backend/app/main.py:645-652`), and S2P's wrapper accepts a
provider (`s2p-copilot/backend/app/services/s2p_evolver.py:24-32`). The main
remaining risks are:

1. promotion-time safety fallbacks still manufacture GREEN in SOC triage and
   Purchasing (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:371-395`,
   `copilot-sdk/apps/purchasing/backend/app/main.py:570-581`);
2. Trading's reusable default factory still installs an UNKNOWN provider,
   although the main application injects a live scorer-backed provider
   (`copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:438-453`,
   `copilot-sdk/apps/trading/backend/app/main.py:380-388`);
3. SDK prompt-variant statistics are held by `InMemoryVariantStore`, so
   promotion statistics are not durable unless an application supplies a
   persistence adapter (`copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:58-74`,
   `copilot-sdk/copilot_sdk/evolution/variant_store.py:58-111`);
4. the generic evolution router exposes read-only summary/inventory/history
   surfaces and does not provide a common verified-outcome or promotion
   trigger path (`copilot-sdk/copilot_sdk/backend/evolution_router.py:53-143`);
5. the four Protocol-V2 service-layer tests are explicit placeholders and
   remain module-skipped (`copilot-sdk/tests/graph/test_protocol_v2_service_layer.py:6-29`).

## 1. Design-document inventory

All nine RL/boundary documents below are present under
`copilot-sdk/docs/design`. The timestamps are filesystem last-write times;
the design content is dated 2026-08-08 unless otherwise stated.

| Document | Size / lines | Last write | Role |
|---|---:|---|---|
| `rl_architecture.md` | 5,338 bytes / 105 | 2026-08-08 16:17 | Base architecture, G1-G4, five-copilot matrix |
| `rl_consolidated_verification_and_design.md` | 29,971 / 286 | 2026-08-08 09:30 | Consolidated verification and current-state findings |
| `rl_consolidation_design_final.md` | 31,737 / 336 | 2026-08-08 08:24 | Finalized provider, wiring, telemetry, test, and work-package design |
| `rl_consolidation_verification.md` | 21,043 / 124 | 2026-08-08 08:18 | Phase-A evidence ledger and corrections |
| `rl_consolidation_work_package.md` | 14,269 / 118 | 2026-08-08 07:26 | Implementation work packages and estimates |
| `rl_diagnostic_scan_consolidated_results.md` | 16,705 / 114 | 2026-08-08 06:59 | Prior diagnostic scan consolidation |
| `rl_scan_part1_results.md` | 21,411 / 228 | 2026-08-08 06:47 | Prior scan: SDK primitives and wiring |
| `rl_scan_part2_results.md` | 23,079 / 212 | 2026-08-08 06:55 | Prior scan: application gaps and risks |
| `soc_g1_boundary_decision_memo.md` | 12,857 / 81 | 2026-08-08 09:19 | SOC exploration/action boundary decision memo |

The design baseline requires a procedural sidecar: centroid judgment remains
the action authority; reward, exploration, credit, and evolution learn from
verified outcomes. The four guarantees are action safety (G1), conservation
gating (G2), evidence-based promotion (G3), and auditable domain-scoped state
(G4). The finalized design calls for one SDK provider protocol with
per-application synchronous adapters (`rl_consolidation_design_final.md:9-54`),
five long-lived evolvers, registered variants, verified-outcome recording,
promotion triggers, and a common telemetry shape
(`rl_consolidation_design_final.md:68-117,124-206`).

There is a governance inconsistency: the final architecture records the SOC
G1 boundary as decided, while `soc_g1_boundary_decision_memo.md:1-18` still
labels the decision OPEN pending founder signoff. This must be resolved before
the implementation can be called governed production behavior.

## 2. Implementation inventory

### SDK RL module

There are 6 Python files and 405 lines under `copilot-sdk/copilot_sdk/rl`:

| File | Lines | Implemented surface |
|---|---:|---|
| `__init__.py` | 22 | Public exports |
| `credit.py` | 39 | Credit-assignment primitive |
| `exploration.py` | 132 | Conservation-bounded Thompson/Beta policy |
| `presets.py` | 78 | Per-copilot RL component assembly |
| `reward_functions.py` | 74 | Binary, GradedFinancial, PnL, WasteReduction |
| `reward.py` | 60 | Reward protocol and clipping/computation |

The four design reward functions are present. The policy samples Beta
posteriors only when conservation headroom permits it
(`copilot-sdk/copilot_sdk/rl/exploration.py:12-44,118-122`). The SOC-specific
standalone policy is also present and persists only when a store is supplied
(`gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:275-358,400-403`).

### SDK evolution module

There are 13 Python files and 1,955 lines under
`copilot-sdk/copilot_sdk/evolution`. The module contains the conservation
contract, `PromptVariantEvolver`, `AgentEvolver`, UCB selection, shadow runner,
promotion gate, event ledger, variant store, autonomous promotion, and credit
attribution helpers. `PromptEvolverConfig` exposes the provider seam and the
evolver resolves it at promotion time (`prompt_evolver.py:39-44,297-308`).

The current default variant store is explicitly in-memory
(`prompt_evolver.py:58-74`). GraphStore persistence exists for decisions,
evolution events, RL state, and ledger records, but it is not automatically the
store for prompt-variant aggregate statistics.

### Presets and application wiring

The five preset files exist: DataOps (100 lines), Purchasing (117), S2P (125),
SOC (125), and Trading (137). Their configured penalty ratios and plateau
values are present, but configuration presence is not equivalent to a complete
live outcome-to-promotion loop.

| Copilot | Current source evidence | Status |
|---|---|---|
| SOC | SDK evolver and compatibility bridge exist (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160-183,345-415`); standalone RL sidecar exists (`services/rl_engine.py:275-603`) | Partial. SDK config still has no conservation provider (`evolver.py:160-167`); normal promotion call omits explicit state (`routers/evolution.py:332-342`). |
| S2P | Singleton SDK evolver, initial registration, provider replacement, outcome recording, and promotion wrapper exist (`s2p-copilot/backend/app/services/s2p_evolver.py:24-91`); route passes current status (`routers/s2p_evolution.py:56-59`) | Provider seam is materially repaired, but promotion is still manually exposed and not automatically invoked after outcome recording. |
| Trading | Main factory injects `ScorerBackedProvider`, registers configured variants, and exposes verified-outcome callback (`apps/trading/backend/app/main.py:380-397`) | Main path is wired. Reusable `create_default_trading_evolver()` still defaults to UNKNOWN and must not be treated as a production-safe default (`services/trading_evolver.py:438-453`). |
| Purchasing | Runtime evolver, configured variants, and scorer-backed provider are created at startup (`apps/purchasing/backend/app/main.py:486-497`) | Startup/provider exists, but the generic router is read-only; no common verified evolution outcome or promotion trigger is evident. It also has unsafe GREEN fallbacks in a separate status helper (`main.py:570-581`). |
| DataOps | Runtime evolver, configured variants, and scorer-backed provider are created at startup (`apps/dataops/backend/app/main.py:641-652`) | Same outcome/trigger/telemetry integration gap as Purchasing; generic router wiring is read-only (`main.py:780-802`). |

### SDK tests

The filename-based RL/evolution inventory found 313 `test_` functions across
the matching SDK test files. This includes 53 direct RL tests, 47 direct
evolution tests, 13 Graph protocol tests, 98 Graph Protocol-V2 conformance
tests, and the broader router/telemetry/wiring tests. Counts are an inventory,
not a claim that all tests ran in this diagnostic.

### GraphStore and Protocol V2

`copilot_sdk/graph/protocol.py:16-190` defines the legacy `GraphStore` and
`GraphTraversalStore` protocols. `ProtocolV2GraphStore` extends the contract
with governed decisions, observations, evidence receipts, conservation
status, fingerprints, checkpoints, evolution events, entity links, archival,
and reset operations (`graph/protocol.py:195-285`). In-memory and SQLite
implementations contain substantial V2 methods; `DualWriteStore` requires both
backends to satisfy `ProtocolV2GraphStore` (`graph/dual_write_store.py:34-60`).
The unresolved part is the application service layer and complete AGE-backed
operational coverage, not the absence of a protocol declaration.

## 3. Gap analysis

| ID | Design intent | Implementation reality | Gap / consequence |
|---|---|---|---|
| G1 | Synchronous provider returns status, `overallSafe`, domain, counts, source, timestamp; async sources use bounded snapshots | SDK protocol exists (`evolution/conservation_contract.py:17-40`); `CachedAsyncProvider` rejects an awaitable and returns UNKNOWN on failure, with a TTL cache (`:90-124`) | Contract is available, but SOC does not configure it. Provider payload normalization is also weaker than the design: the cached adapter drops most source fields and uses an internal timestamp. |
| G2 | Every copilot promotion reads a live provider and UNKNOWN fails closed | S2P, Purchasing, DataOps, and the main Trading app inject providers; SOC does not; Trading's default factory is UNKNOWN | Five-copilot parity is incomplete. A safe default must be fail-closed without any alternate helper manufacturing GREEN. |
| G3 | SOC exploration is proposal/shadow-only at G1; it cannot overwrite the selected action | SOC triage still contains an exploration path whose effective action can be replaced when the exploration flag is enabled (prior architecture evidence: `routers/triage.py:700-703`; runtime gate status at `triage.py:362-368`) | G1 remains a runtime configuration and code-path risk until the production flag is hard-disabled and an assertion proves exploration cannot alter the live action. |
| G4 | Reward functions Binary, GradedFinancial, PnL, WasteReduction | All four SDK classes exist (`copilot_sdk/rl/reward_functions.py`) | Primitive complete; per-copilot binding and verified-outcome coverage remain incomplete, especially Purchasing/DataOps. |
| G5 | Thompson/Beta, conservation-bounded exploration, and UCB selection | Both SDK and SOC implementations exist (`copilot_sdk/rl/exploration.py`; `services/rl_engine.py:275-358`; `evolution/prompt_evolver.py:344-369`) | Algorithmic primitive complete; SOC live-action boundary and posterior persistence are not fully proven. |
| G6 | Finite-difference factor attribution plus chain credit | SOC has factor attribution and async chain-credit helpers (`services/rl_engine.py:406-537`); SDK has credit modules | Helpers exist, but the diagnostic found no uniform five-copilot wiring contract proving attribution is consumed by promotion decisions. |
| G7 | Persistent posterior/variant statistics (design moved from DuckDB to PostgreSQL) | Prompt evolution defaults to `InMemoryVariantStore` (`prompt_evolver.py:58-74`); GraphStore persistence is separate | Restart loses aggregate prompt-variant statistics unless each app supplies and hydrates a durable store. This is a concrete persistence gap. |
| G8 | SOC async learning health must become a timestamped synchronous provider | Learning-health source is async; SOC `_sdk_config()` has no provider (`services/evolver.py:160-167`) | Promotion sees missing state and fails closed, but the intended live GREEN/AMBER/RED gate is not connected. |
| G9 | Evolution gate: 5pp superiority, 0.70 floor, 10 minimum shadow decisions, variance and conservation checks | SDK gate defaults and checks exist (`evolution/gate.py:12-65`); PromptVariantEvolver blocks missing/unsafe conservation (`prompt_evolver.py:224-262`) | SDK gate is substantially complete. Trading intentionally uses lower custom thresholds; that exception needs parity tests so it does not weaken G4. |
| G10 | Verified outcomes drive stats, then an explicit promotion trigger runs | S2P records outcomes but its promotion endpoint is manual (`s2p_evolver.py:67-89`; `routers/s2p_evolution.py:56-59`). Generic SDK router exposes only GET surfaces (`backend/evolution_router.py:53-143`) | Automatic post-outcome/scheduled promotion is missing or not uniform. Purchasing/DataOps domain outcomes currently feed operational services, not clearly the variant store. |
| G11 | One long-lived evolver with startup registration in every copilot | Main paths now create/register evolvers for all five; Trading main path does so explicitly (`apps/trading/backend/app/main.py:380-390`) | Improved from the prior scan. Factory-level safety and runtime identity tests are still needed; generic fallback construction can create an unrelated AgentEvolver (`backend/evolution_router.py:39-51`). |
| G12 | Common telemetry: active variant, inventory, stats, events, conservation, rejection reason | Generic summary normalizes inventory and provider state but history for PromptVariantEvolver is empty (`backend/evolution_router.py:82-96,115-143`) | Telemetry is not yet a complete union schema with recent lifecycle/rejection events for SDK prompt evolvers. S2P and Trading expose separate shapes. |
| G13 | Protocol-V2 service layer commits outcomes, reports pending sync, and updates V only after canonical commit | Four tests are `pass` placeholders under a module-level skip (`tests/graph/test_protocol_v2_service_layer.py:6-29`) | API/service orchestration, outbox fallback, replay ordering, and conservation-V timing must be implemented and tested. |
| G14 | G1 boundary memo and architecture have one authoritative decision | Memo remains OPEN while final design treats the boundary as decided | Governance/documentation gap; implementation acceptance cannot be unambiguous until resolved. |

## 4. Bug and safety findings

### B1 — SOC literal GREEN fallbacks violate fail-closed conservation

`_soc_effective_conservation_status()` defaults missing health status to GREEN
and maps CALIBRATING to GREEN. It also maps AMBER/RED to GREEN while below the
calibration count (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:371-395`).
That may have been intended to preserve learning during calibration, but it is
not the design contract: UNKNOWN, CALIBRATING, AMBER, and RED must not be
represented as promotion-safe GREEN. This is a confirmed safety bug unless the
G1 boundary explicitly approves this behavior and it is excluded from
promotion-time conservation.

### B2 — Purchasing status helper has two fail-open GREEN defaults

When an override is a dict with no recognized value, the helper returns GREEN;
when the computed payload has no status, it also returns GREEN
(`copilot-sdk/apps/purchasing/backend/app/main.py:570-581`). Provider failures
return UNAVAILABLE in one branch, but malformed or incomplete successful
payloads can still become GREEN. This is a confirmed fail-open path.

### B3 — Trading factory safety differs by construction path

`TradingAgentEvolver` defaults its provider to `_default_conservation_state()`,
which returns UNKNOWN (`apps/trading/backend/app/services/trading_evolver.py:49-50,161-169`).
The main app correctly injects `ScorerBackedProvider`, but callers of
`create_default_trading_evolver()` receive the unsafe-to-use default
(`services/trading_evolver.py:438-453`). This is fail-closed for promotion but
not a live-provider implementation and can silently disable evolution.

### B4 — SOC provider mismatch is a silent fail-closed outage

`CachedAsyncProvider` intentionally rejects an awaitable returned by its sync
entry point (`copilot_sdk/evolution/conservation_contract.py:99-121`), which is
correct in isolation. SOC never installs an adapter around its async learning
health service (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:160-167`),
so normal promotion cannot observe live conservation and is blocked by the
gate. This is safer than fail-open, but is still a functional wiring defect.

### B5 — Promotion gate itself is fail-closed, but caller inputs remain too permissive

The SDK gate rejects `None`, malformed mappings, and non-GREEN statuses
(`copilot-sdk/copilot_sdk/evolution/gate.py:73-89`), and the prompt evolver
records a rejection rather than promoting (`prompt_evolver.py:224-262`). The
remaining defect is upstream: app helpers and caller-supplied explicit state
can bypass the intended sole-provider rule. The design requires callers to
omit literal promotion state and let the configured provider be authoritative.

### B6 — Mutation serialization is not demonstrably end-to-end for evolution

S2P has per-domain mutation decorators and explicit locks around scoring and
outcome routes (`s2p-copilot/backend/app/routers/s2p.py:2043-2085,2236,2372`; `routers/s2p_evolution.py:48-64`). The locks protect selected route mutations, but the module-level evolver mutation, graph receipt writes, and promotion check are not shown to share one transaction/lock scope. A promotion check can therefore observe stats before the corresponding canonical outcome/receipt commit completes. This is an integration race to close with a concurrency test, not proof that every current request races.

## 5. PROTO-V2 skipped-test dependencies

The explicit module-level skip is
`copilot-sdk/tests/graph/test_protocol_v2_service_layer.py:6`. It covers four
placeholder tests, all currently `pass`:

| Test | Dependency needed to unskip |
|---|---|
| `test_api_learn_committed` | A real service/API `learn` path that calls `write_outcome`, distinguishes canonical commit from acceptance, and returns a committed result only after the store transaction succeeds. |
| `test_api_learn_pending_sync` | AGE-unavailable/outbox fallback above GraphStore, returning `accepted_pending_sync` without pretending canonical persistence completed. |
| `test_pending_sync_no_V_increment` | Conservation-V accounting must be tied to canonical outcome commit, not request acceptance or outbox enqueue. |
| `test_replay_then_V_increments` | Outbox worker/replay must retry idempotently, commit the outcome, then increment V exactly once; duplicate/conflicting replay must preserve quarantine semantics. |

The V2 conformance file declares `PENDING`, `AGE_PENDING`, and a generic AGE
rollback marker (`tests/graph/test_protocol_v2_conformance.py:21-28`), but those
constants are not applied as decorators in the current file. Its SQLite V2
coverage is active; AGE tests depend on the AGE fixture/DSN and may skip at
runtime. One concurrency test is conditionally skipped at line 2998. Therefore
the direct “unskip” work is the four service-layer implementations above,
plus a real AGE test environment and service integration for full cross-store
coverage. Protocol declarations and substantial SQLite/AGE adapter methods
already exist (`copilot_sdk/graph/protocol.py:195-285`).

## 6. Recommended implementation order

1. **Resolve governance and safety semantics first (0.5–1 day).** Close the
   SOC G1 memo; decide whether calibration can ever be represented as GREEN;
   remove all promotion-time literal/default GREEN paths; add static and
   runtime tests for UNKNOWN/AMBER/RED/CALIBRATING.
2. **Finish the provider spine (1–1.5 days).** Add the SOC timestamped
   async-to-sync snapshot, make Trading's default factory require/inject a
   provider, and normalize every provider to status, `overallSafe`, domain,
   counts, source, observed timestamp, and reason.
3. **Make variant statistics durable (1–2 days).** Define a persistence
   adapter backed by the selected GraphStore/PostgreSQL path, hydrate at boot,
   and make outcome/promotion events idempotent and domain-scoped.
4. **Complete verified outcome and trigger wiring (2–3 days).** Connect each
   copilot's canonical outcome to its variant store; add an explicit safe
   post-outcome or scheduled promotion trigger. Keep Trading custom behavior,
   but map it to the common contract.
5. **Unify telemetry and concurrency boundaries (1.5–2 days).** Expose one
   summary/history schema with rejection reasons and conservation provenance;
   serialize outcome commit, stat update, and promotion evaluation at the
   appropriate domain transaction boundary.
6. **Implement the four V2 service-layer tests (1–2 days).** Build the API,
   outbox pending/replay, and V timing semantics; then run SQLite and AGE
   conformance with a real disposable AGE database.
7. **Run the five-copilot acceptance matrix (1–1.5 days).** Startup identity,
   no-literal safety, AMBER block, GREEN promotion, insufficient evidence,
   verified outcome, persistence restart, telemetry, and G1 action-authority
   tests.

Estimated remaining effort: approximately 7–12 engineering days, depending on
whether the existing GraphStore event schema can safely host variant aggregate
state or a dedicated PostgreSQL adapter is required. The high-risk items are
the SOC safety decision, persistence semantics, and V2 commit ordering.

## Review conclusion

The implementation is not yet “all five complete live RL/evolution loops.” The
SDK foundation and much of the application startup wiring are real, but the
current status should be recorded as **foundation complete; production parity,
fail-closed cleanup, durable variant state, and Protocol-V2 service semantics
incomplete**.

Inventory summary:

- Design documents read: 9
- SDK RL files: 6 files, 405 lines
- SDK evolution files: 13 files, 1,955 lines
- Gaps found: 14
- Confirmed/important bug findings: 6
- Direct PROTO-V2 service-layer dependencies: 4 skipped placeholder tests
- Recommended next step: resolve G1 semantics and remove fail-open GREEN paths,
  then wire the SOC/Trading provider spine before adding persistence and
  outcome-trigger parity.
