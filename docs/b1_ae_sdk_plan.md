# B1 AE-SDK — Investigation Report
**Generated:** 2026-05-25 · **Repo:** copilot-sdk · **Baseline:** 654 passed, 1308 warnings

## Ready for Implementation
- NO — the requested B1 architecture assumes a fresh or separable evolution package, but `copilot_sdk/evolution` already exists and the current `GraphStore` protocol already requires evolution methods.
- The strongest blocker is protocol coupling: `GraphStore` declares `save_evolution_event()` and `get_evolution_events()` at `copilot_sdk/graph/protocol.py:78` and `copilot_sdk/graph/protocol.py:88`.
- Existing tests assert that coupling as desired behavior, especially `tests/graph/test_graph_store_evolution.py:25`.
- A reconciliation step is needed before implementation so the next prompt does not duplicate or break the current evolution surface.

## Existing Package Map
| File | Lines | Classes / Protocols | Key Methods / Constants | Imports / External Dependencies | Overlap With B1 Target |
|---|---:|---|---|---|---|
| `copilot_sdk/evolution/__init__.py` | 51 | none | exports `AgentEvolver`, `DefaultPromotionGate`, `DefaultShadowRunner`, `InMemoryEvolutionLedger`, prompt/variant helpers at `copilot_sdk/evolution/__init__.py:3` through `copilot_sdk/evolution/__init__.py:24` | SDK-only imports from `copilot_sdk.evolution.*` | Existing public package surface; B1 must preserve or intentionally migrate exports. |
| `copilot_sdk/evolution/protocol.py` | 84 | `EvolutionEvent`, `EvolutionRule`, `EvolutionLedger`, `ShadowRunner`, `PromotionGate` | `EVOLUTION_EVENT_TYPES` at `copilot_sdk/evolution/protocol.py:10`; event validation at `copilot_sdk/evolution/protocol.py:31`; protocols at `copilot_sdk/evolution/protocol.py:38`, `:48`, `:67`, `:78` | stdlib dataclasses, datetime, typing | B1 asked for `protocols.py`; current file is singular `protocol.py` and already contains several requested protocols except `EvolutionStore` and `VariantSelector`. |
| `copilot_sdk/evolution/evolver.py` | 244 | `PlateauConfig`, `AgentEvolver` | constructor at `copilot_sdk/evolution/evolver.py:28`; `register_rule()` at `:43`; `evolve()` at `:49`; history at `:106`; promoted rules at `:113`; plateau logic at `:151` | imports `DefaultPromotionGate`, `InMemoryEvolutionLedger`, protocol types, `DefaultShadowRunner` at `copilot_sdk/evolution/evolver.py:10` through `:13` | Existing coordinator overlaps strongly with requested `agent_evolver.py`, but shadow is synchronous in `evolve()` at `copilot_sdk/evolution/evolver.py:90`. |
| `copilot_sdk/evolution/ledger.py` | 70 | `InMemoryEvolutionLedger` | optional `graph_store` constructor at `copilot_sdk/evolution/ledger.py:17`; `append()` at `:25`; `get_events()` at `:42`; `get_promoted_rules()` at `:59` | SDK protocol import only at `copilot_sdk/evolution/ledger.py:9` | Existing ledger is append-only but persists through GraphStore-style `save_evolution_event()` at `copilot_sdk/evolution/ledger.py:30`, conflicting with separate `EvolutionStore`. |
| `copilot_sdk/evolution/shadow.py` | 102 | `DefaultShadowRunner` | `min_decisions` constructor at `copilot_sdk/evolution/shadow.py:13`; `run_shadow()` at `:16`; variant prediction at `:91` | stdlib json/logging/typing | B1 wants fire-and-forget shadow comparison; current runner is synchronous batch evaluation and returns metrics. |
| `copilot_sdk/evolution/gate.py` | 59 | `DefaultPromotionGate` | thresholds in constructor at `copilot_sdk/evolution/gate.py:10` through `:18`; `evaluate()` at `:20`; conservation status default at `:29`; checks at `:33` through `:39` | stdlib statistics/typing | Overlaps with promotion evaluator, but current conservation gate is not fail-closed because missing status defaults to GREEN. |
| `copilot_sdk/evolution/autonomous_promotion.py` | 132 | `PromotionDecision`, `AutonomousPromotionGate` | actions at `copilot_sdk/evolution/autonomous_promotion.py:11` through `:13`; GREEN-only docstring at `:24`; `min_shadow_batches=3`, `min_win_rate=0.7` at `:28` and `:29`; `evaluate()` at `:36`; non-GREEN block at `:48` | stdlib dataclasses/typing | This is closer to fail-closed GREEN promotion than `DefaultPromotionGate`, but not the B1 four-gate evaluator. |
| `copilot_sdk/evolution/context_selector.py` | 87 | `SelectionContext`, `ContextAwareSelector` | `exploration_bonus=1.0` at `copilot_sdk/evolution/context_selector.py:22`; `select()` at `:26`; scoring at `:41`; category bonus at `:73` | stdlib time/dataclasses/typing | Selector exists but is not UCB1 with `exploration_c=sqrt(2)`. |
| `copilot_sdk/evolution/credit_attribution.py` | 77 | `StepRecord`, `StepCredit`, `StepCreditAssigner` | `HALF_LIFE=24*60*60` at `copilot_sdk/evolution/credit_attribution.py:10`; `CHAIN_DISCOUNT=0.85` at `:11`; `assign()` at `:37` | stdlib time/dataclasses/typing | Extra capability not in original B1 file list. |
| `copilot_sdk/evolution/prompt_evolver.py` | 369 | `_VariantStatsLike`, `PromptEvolverConfig`, `PromptVariantEvolver` | UCB config at `copilot_sdk/evolution/prompt_evolver.py:24`; B1-like thresholds at `:27` through `:31`; `get_variant()` at `:72`; promotion check at `:144`; promotion implementation at `:181` | stdlib math/dataclasses/typing plus SDK protocol/store imports at `copilot_sdk/evolution/prompt_evolver.py:9` and `:10` | Existing prompt-specific evolver is substantial and should remain distinct from generic AgentEvolver. |
| `copilot_sdk/evolution/variant_store.py` | 182 | `VariantSpec`, `VariantStats`, `CategoryVariantStats`, `InMemoryVariantStore` | statuses at `copilot_sdk/evolution/variant_store.py:10`; registration at `:66`; outcome stats at `:111`; status update at `:123` | stdlib copy/dataclasses/typing | Extra store layer; overlaps with variant lifecycle but not requested `EvolutionStore`. |
| `copilot_sdk/evolution/toy_rules.py` | 147 | `ConfidenceBoundaryRule`, `FactorWeightRule`, `ActionBiasRule` | helpers at `copilot_sdk/evolution/toy_rules.py:10`, `:19`, `:29`, `:44`; rule classes at `:52`, `:75`, `:123` | stdlib random/dataclasses/typing | Useful tests/demo rules; outside original B1 spec. |
| `copilot_sdk/evolution/protocols.py` | absent | absent | absent | absent | B1 target file absent; current package uses `protocol.py`. |
| `copilot_sdk/evolution/agent_evolver.py` | absent | absent | absent | absent | B1 target file absent; current coordinator is `evolver.py`. |
| `copilot_sdk/evolution/promotion.py` | absent | absent | absent | absent | B1 target file absent; current gates are `gate.py` and `autonomous_promotion.py`. |
| `copilot_sdk/evolution/selector.py` | absent | absent | absent | absent | B1 target file absent; current selector is `context_selector.py`. |

## Router Map
- `create_evolution_router()` signature is `(graph_store_factory: Callable[[], Any] | str | None = None, domain: str = "unknown", ledger_provider: Callable[[], Any] | Any | None = None, variant_provider: Callable[[], list[dict[str, Any]]] | None = None) -> APIRouter`, as reported by the pre-check and declared at `copilot_sdk/backend/evolution_router.py:18`.
- Parameters:
  - `graph_store_factory` defaults to `None` at `copilot_sdk/backend/evolution_router.py:19`.
  - `domain` defaults to `"unknown"` at `copilot_sdk/backend/evolution_router.py:20`.
  - `ledger_provider` defaults to `None` at `copilot_sdk/backend/evolution_router.py:21`.
  - `variant_provider` defaults to `None` at `copilot_sdk/backend/evolution_router.py:22`.
- Backward compatibility:
  - A string first argument is treated as a legacy domain at `copilot_sdk/backend/evolution_router.py:24` through `:27`.
  - `ledger_provider` is mapped into `graph_store_factory` when no graph store factory is supplied at `copilot_sdk/backend/evolution_router.py:28` through `:29`.
  - Prefix is `/evolution` for legacy mounts and `/api/evolution` otherwise at `copilot_sdk/backend/evolution_router.py:31`.
- Evolver creation:
  - The router uses a per-router closure cache, `evolver_cache`, at `copilot_sdk/backend/evolution_router.py:32`.
  - `_get_evolver()` constructs `InMemoryEvolutionLedger(graph_store=graph_store)` at `copilot_sdk/backend/evolution_router.py:34` through `:38`.
  - It creates `AgentEvolver` with `DefaultShadowRunner()` and `DefaultPromotionGate()` at `copilot_sdk/backend/evolution_router.py:38` through `:42`.
  - There is no `evolver_factory` parameter in the current signature.
- Endpoints:
  - `GET /variants` is defined at `copilot_sdk/backend/evolution_router.py:45`.
  - `GET /history` is defined at `copilot_sdk/backend/evolution_router.py:71`.
  - `GET /promoted` is defined at `copilot_sdk/backend/evolution_router.py:84`.
- Provider behavior:
  - `variant_provider` is invoked by `_provided_variants()` at `copilot_sdk/backend/evolution_router.py:95` through `:101`.
  - Legacy variants use `provider().run_query("")` when available at `copilot_sdk/backend/evolution_router.py:104` through `:118`.
- Module-global state:
  - No module-global evolver is visible; the mutable cache is closure-local at `copilot_sdk/backend/evolution_router.py:32`.

## GraphStore Coupling
- `GraphStore` protocol methods:
  - `write_decision()` at `copilot_sdk/graph/protocol.py:12`.
  - `write_outcome()` at `copilot_sdk/graph/protocol.py:23`.
  - `get_decision()` at `copilot_sdk/graph/protocol.py:32`.
  - `get_decisions()` at `copilot_sdk/graph/protocol.py:35`.
  - `get_all_decisions()` at `copilot_sdk/graph/protocol.py:43`.
  - `get_verified_decisions()` at `copilot_sdk/graph/protocol.py:46`.
  - `count_verified()` at `copilot_sdk/graph/protocol.py:49`.
  - `count_correct()` at `copilot_sdk/graph/protocol.py:52`.
  - `count_decisions()` at `copilot_sdk/graph/protocol.py:55`.
  - `save_centroids()` at `copilot_sdk/graph/protocol.py:58`.
  - `load_latest_centroids()` at `copilot_sdk/graph/protocol.py:68`.
  - `get_centroid_checkpoints()` at `copilot_sdk/graph/protocol.py:71`.
  - `save_evolution_event()` at `copilot_sdk/graph/protocol.py:78`.
  - `get_evolution_events()` at `copilot_sdk/graph/protocol.py:88`.
  - `archive_old_decisions()` at `copilot_sdk/graph/protocol.py:95`.
  - `count_archived()` at `copilot_sdk/graph/protocol.py:98`.
  - `close()` at `copilot_sdk/graph/protocol.py:101`.
- Evolution-specific protocol methods:
  - `save_evolution_event()` and `get_evolution_events()` are required protocol members, not optional defaults, because they are abstract protocol method declarations at `copilot_sdk/graph/protocol.py:78` through `:93`.
- SQLite coupling:
  - `SQLiteGraphStore` creates `evolution_events` in the main schema at `copilot_sdk/graph/sqlite_store.py:104` through `:112`.
  - Columns are `id`, `domain`, `event_type`, `rule_name`, `variant_id`, `metadata`, and `timestamp` at `copilot_sdk/graph/sqlite_store.py:105` through `:111`.
  - `_ensure_migrations()` includes `evolution_events` in its domain migration loop at `copilot_sdk/graph/sqlite_store.py:152` through `:159`.
  - `_create_indexes()` creates `idx_evolution_events_domain` at `copilot_sdk/graph/sqlite_store.py:175`.
  - `save_evolution_event()` inserts rows at `copilot_sdk/graph/sqlite_store.py:501` through `:524`.
  - `get_evolution_events()` filters by domain, optional rule name, and limit at `copilot_sdk/graph/sqlite_store.py:526` through `:559`.
  - Metadata serialization uses `json.dumps(metadata or {}, sort_keys=True)` at `copilot_sdk/graph/sqlite_store.py:521`.
- In-memory coupling:
  - `InMemoryGraphStore` has `_evolution_events` at `copilot_sdk/graph/memory_store.py:26`.
  - `save_evolution_event()` appends event dicts at `copilot_sdk/graph/memory_store.py:211` through `:228`.
  - `get_evolution_events()` filters by domain and optional rule name, with a limit, at `copilot_sdk/graph/memory_store.py:230` through `:239`.
  - `reset()` clears `_evolution_events` at `copilot_sdk/graph/memory_store.py:305` through `:311`.
- Coupling assessment:
  - This directly conflicts with B1’s rule that `EvolutionStore` is separate from `GraphStore`.
  - The implementation-specific storage can be reused, but the public protocol shape needs a staged compatibility plan.

### Ledger Persistence Signature/Domain Mismatch
- `InMemoryEvolutionLedger` accepts an optional persistence object named `graph_store` at `copilot_sdk/evolution/ledger.py:17` and stores it as `_graph_store` at `copilot_sdk/evolution/ledger.py:19`.
- On append, the ledger calls `_graph_store.save_evolution_event()` at `copilot_sdk/evolution/ledger.py:30`, but it passes `event.event_type`, `event.rule_name`, and `event.variant_id` positionally at `copilot_sdk/evolution/ledger.py:31` through `:33`.
- That call omits a domain argument entirely.
- The `GraphStore` protocol requires `save_evolution_event(domain, event_type, rule_name, variant_id, metadata)` with `domain` first at `copilot_sdk/graph/protocol.py:78` through `:85`.
- `SQLiteGraphStore.save_evolution_event()` also requires `domain` first at `copilot_sdk/graph/sqlite_store.py:501` through `:508`, then persists the fields into `(domain, event_type, rule_name, variant_id, metadata)` at `copilot_sdk/graph/sqlite_store.py:512` through `:521`.
- `create_evolution_router()` passes a real graph store into this ledger path: it resolves `graph_store = graph_store_factory()` at `copilot_sdk/backend/evolution_router.py:36` and then constructs `InMemoryEvolutionLedger(graph_store=graph_store)` at `copilot_sdk/backend/evolution_router.py:37`.
- Therefore current router-backed persistence is not merely coupled to GraphStore; it is signature/domain-incompatible when the raw graph store has the domain-aware signature.
- Risk:
  - evolution events may be stored with `domain=event_type`;
  - `event_type`, `rule_name`, and `variant_id` may shift into the wrong columns;
  - domain filtering in `get_evolution_events(domain, ...)` may miss events;
  - a future implementation could preserve broken persistence if it passes raw `GraphStore` directly to the ledger.
- Implementation implication: do not pass a raw GraphStore directly into `InMemoryEvolutionLedger` unless a compatibility adapter maps ledger events to `save_evolution_event(domain, event_type, rule_name, variant_id, metadata)`.

## Test Inventory
- Pre-check evolution file discovery used PowerShell equivalent: `Get-ChildItem tests -Recurse -File -Filter *.py | Where-Object { $_.FullName -like '*evolut*' }`.
- Existing evolution-related files:
  - `tests/backend/test_evolution_router.py` — 10 tests.
  - `tests/evolution/__init__.py` — 0 tests.
  - `tests/evolution/test_autonomous_promotion.py` — 11 tests.
  - `tests/evolution/test_context_selector.py` — 7 tests.
  - `tests/evolution/test_credit_attribution.py` — 8 tests.
  - `tests/evolution/test_evolve_integration.py` — 8 tests.
  - `tests/evolution/test_evolver.py` — 13 tests.
  - `tests/evolution/test_gate.py` — 10 tests.
  - `tests/evolution/test_integration.py` — 4 tests.
  - `tests/evolution/test_ledger.py` — 8 tests.
  - `tests/evolution/test_plateau.py` — 6 tests.
  - `tests/evolution/test_prompt_category_ucb.py` — 21 tests.
  - `tests/evolution/test_prompt_evolver_basic.py` — 13 tests.
  - `tests/evolution/test_prompt_promotion_gate.py` — 21 tests.
  - `tests/evolution/test_protocol.py` — 5 tests.
  - `tests/evolution/test_shadow.py` — 8 tests.
  - `tests/evolution/test_toy_rules.py` — 8 tests.
  - `tests/evolution/test_variant_store.py` — 13 tests.
  - `tests/graph/test_graph_store_evolution.py` — 8 tests.
  - `tests/test_graphstore_consolidation.py` — 11 tests in the file, including evolution/link parity tests.
- Total existing evolution-related test count from the path-based inventory: 182.
- Additional root consolidation coverage exists outside that path-based inventory, so future validation should treat the effective coupling inventory as at least 182 plus the root consolidation parity tests.
- GraphStore coupling assertions:
  - `tests/graph/test_graph_store_evolution.py:25` asserts `GraphStore` has `save_evolution_event`.
  - `tests/graph/test_graph_store_evolution.py:118` asserts `SQLiteGraphStore` satisfies the protocol after evolution extension.
  - `tests/test_graphstore_consolidation.py:221` asserts in-memory evolution/link parity.
  - `tests/test_graphstore_consolidation.py:239` asserts SQLite evolution/link parity.
  - `tests/test_graphstore_consolidation.py:224` and `:243` call the domain-aware store signature directly.
- Router shape assertions:
  - `tests/backend/test_evolution_router.py:36` asserts the factory returns an `APIRouter`.
  - `tests/backend/test_evolution_router.py:45` asserts `/api/evolution/variants`.
  - `tests/backend/test_evolution_router.py:62` asserts `/api/evolution/history`.
  - `tests/backend/test_evolution_router.py:71` asserts `/api/evolution/promoted`.
  - `tests/backend/test_evolution_router.py:85` through `:99` assert lazy graph store factory use.
  - `tests/backend/test_evolution_router.py:117` through `:130` assert one graph store per router instance.
- P16 / no domain leakage tests:
  - `tests/evolution/test_protocol.py:81` through `:98` scans `copilot_sdk/evolution` for domain vocabulary, `from app.`, `gen_ai_roi`, and `soc`.
  - `tests/evolution/test_prompt_category_ucb.py:227` through `:232` checks no SOC imports in `prompt_evolver`.
  - `tests/evolution/test_prompt_category_ucb.py:240` and `:242` check no `ProfileScorer` and no centroid references in `prompt_evolver`.
  - `tests/evolution/test_prompt_evolver_basic.py:145` and `:147` check no `ProfileScorer` and no centroid references.
  - `tests/evolution/test_prompt_promotion_gate.py:278` and `:280` check no `ProfileScorer` and no centroid references.
- Shadow tests:
  - `tests/evolution/test_shadow.py:32` covers insufficient decisions.
  - `tests/evolution/test_shadow.py:41` covers variant accuracy.
  - `tests/evolution/test_shadow.py:96` covers variant exception logging.
- Gate tests:
  - `tests/evolution/test_gate.py:17` covers promotion when checks pass.
  - `tests/evolution/test_gate.py:46` covers RED conservation blocking.
  - `tests/evolution/test_gate.py:53` currently asserts AMBER conservation passes.

## Gap Analysis
### Table A: Requested Features
| Requested Feature | Exists? | Location | Gap |
|---|---|---|---|
| EvolutionLedger Protocol | YES | `copilot_sdk/evolution/protocol.py:48` | Exists as `EvolutionLedger`; no separate `EvolutionStore`. |
| VariantSelector Protocol | NO | none found | `ContextAwareSelector` exists at `copilot_sdk/evolution/context_selector.py:19`, but no runtime-checkable selector protocol. |
| PromotionEvaluator Protocol | PARTIAL | `PromotionGate` at `copilot_sdk/evolution/protocol.py:78` | Name and semantics differ from requested `PromotionEvaluator`. |
| ShadowRunner Protocol | YES | `copilot_sdk/evolution/protocol.py:67` | Existing runner is synchronous metrics runner, not fire-and-forget comparison. |
| EvolutionStore separate from GraphStore | NO | GraphStore evolution methods at `copilot_sdk/graph/protocol.py:78` and `:88` | Main architectural mismatch. |
| Ledger persistence compatibility | NO | Ledger call at `copilot_sdk/evolution/ledger.py:30` through `:33`; GraphStore signature at `copilot_sdk/graph/protocol.py:78` through `:85` | Need to reconcile ledger event persistence with domain-aware GraphStore signature or introduce an adapter/dual protocol. |
| Router-backed persistence | PARTIAL/BROKEN | Router passes graph store to ledger at `copilot_sdk/backend/evolution_router.py:36` through `:37` | Implementation prompt must not pass raw GraphStore directly into ledger unless wrapped/adapted. |
| UCB1VariantSelector exploration_c=√2 | PARTIAL | `PromptEvolverConfig.exploration_constant=1.414` at `copilot_sdk/evolution/prompt_evolver.py:24` | Prompt-specific UCB exists; no generic `UCB1VariantSelector` class. |
| DefaultPromotionEvaluator four-gate | PARTIAL | `DefaultPromotionGate` at `copilot_sdk/evolution/gate.py:9`; prompt thresholds at `copilot_sdk/evolution/prompt_evolver.py:27` through `:31` | Current default gate has similar checks but wrong fail-closed behavior and different threshold names. |
| DefaultShadowRunner fire-and-forget/stale pruning | NO | `DefaultShadowRunner.run_shadow()` at `copilot_sdk/evolution/shadow.py:16` | Current shadow is synchronous batch scoring; SOC reference has fire-and-forget semantics at `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:96`. |
| AgentEvolver coordinator | YES | `copilot_sdk/evolution/evolver.py:27` | Existing coordinator lacks requested file name and fire-and-forget shadow behavior. |
| Conservation fail-closed in promotion | PARTIAL | `AutonomousPromotionGate` blocks non-GREEN at `copilot_sdk/evolution/autonomous_promotion.py:48`; `DefaultPromotionGate` defaults missing to GREEN at `copilot_sdk/evolution/gate.py:29` | Default B1 path needs fail-closed behavior. |
| Evolution router with evolver_factory param | NO | router signature at `copilot_sdk/backend/evolution_router.py:18` | Router has graph/ledger/variant providers but no `evolver_factory`. |
| Domain-agnostic zero SOC refs | YES | no SOC import pre-check; scan test at `tests/evolution/test_protocol.py:81` | Current package passes import discipline baseline. |
| P16 separation no ProfileScorer | PARTIAL | tests at `tests/evolution/test_prompt_category_ucb.py:240` and `:242` | Existing tests cover prompt evolver; broader B1 modules need similar guards. |

### Table B: Extra Files
| File | Purpose | Overlap/Conflict Risk |
|---|---|---|
| `autonomous_promotion.py` | Opt-in GREEN-only autonomous promotion gate with `PromotionDecision`. | Useful for fail-closed semantics; not identical to B1 four-gate evaluator. |
| `context_selector.py` | Context-aware selector with exploration bonus and failure downweighting. | May conflict with a new generic `selector.py` unless naming/export strategy is clear. |
| `credit_attribution.py` | Time-decayed chain credit attribution. | Extra domain-neutral feature; likely leave as-is. |
| `prompt_evolver.py` | Prompt variant selection, UCB, stats, and promotion lifecycle. | Large existing subsystem; should remain separate from generic AgentEvolver. |
| `variant_store.py` | In-memory prompt variant registry and outcome stats. | Could support B1, but not a replacement for `EvolutionStore`. |
| `toy_rules.py` | Demo/test evolution rules. | Low risk if preserved. |
| `gate.py` | Current default promotion gate. | Needs fail-closed reconciliation if it remains B1 default. |
| `protocol.py` | Current protocol definitions. | B1 requested `protocols.py`; duplicating would confuse public API. |

## Architecture Decisions
### Q1: EvolutionStore Separation
- Recommendation: C) dual-protocol.
- Rationale:
  - Immediate removal from `GraphStore` would break tests that assert protocol coupling, especially `tests/graph/test_graph_store_evolution.py:25`.
  - Keeping only GraphStore violates the B1 rule that `EvolutionStore` is separate from GraphStore.
  - Current ledger persistence also does not match the domain-aware GraphStore signature: the ledger omits domain at `copilot_sdk/evolution/ledger.py:30` through `:33`, while GraphStore requires domain first at `copilot_sdk/graph/protocol.py:78` through `:85`.
  - A dual-protocol/adaptor path can introduce `EvolutionStore` in `copilot_sdk/evolution/protocol.py` or a compatibility `protocols.py`, adapt ledgers to prefer it, and leave GraphStore methods temporarily as compatibility implementation methods.
  - The adapter should map ledger/evolver event records to `SQLiteGraphStore.save_evolution_event(domain, event_type, rule_name, variant_id, metadata)` rather than passing raw GraphStore through.
  - Do not extend the GraphStore protocol further; treat the existing evolution methods as compatibility surface until a deprecation path is explicit.
  - Existing implementation methods in SQLite and memory stores can satisfy `EvolutionStore` structurally without changing persistence immediately.
- Recommended implementation choice:
  - Change the ledger to accept an `EvolutionStore`-shaped persistence object or wrap GraphStore with an `EvolutionStoreAdapter`.
  - Prefer passing a domain-aware adapter from `create_evolution_router()` so router-backed persistence keeps app/domain filtering correct.

### Q2: What Needs Building
- Files to create:
  - Prefer no new duplicate `agent_evolver.py` until naming decision is settled.
  - Add `copilot_sdk/evolution/protocols.py` only as a compatibility alias or migration target if desired.
  - Add `copilot_sdk/evolution/promotion.py` if replacing or wrapping `gate.py` with fail-closed B1 semantics.
  - Add `copilot_sdk/evolution/selector.py` if generic UCB selector is distinct from `ContextAwareSelector` and prompt UCB.
- Files to modify:
  - `copilot_sdk/evolution/protocol.py` to add `EvolutionStore` and selector/promotion protocols if keeping singular file.
  - `copilot_sdk/evolution/ledger.py` to accept `EvolutionStore` rather than graph-store-specific naming.
  - `copilot_sdk/evolution/ledger.py` or equivalent call site to stop using no-domain positional persistence calls.
  - `copilot_sdk/evolution/gate.py` or a new `promotion.py` to fail closed.
  - `copilot_sdk/backend/evolution_router.py` to add optional `evolver_factory` without breaking existing parameters and to pass a domain-aware `EvolutionStore` adapter when persistence is enabled.
  - A new adapter file may be appropriate if the adapter is more than a tiny local wrapper.
  - Tests under `tests/graph/` and `tests/test_graphstore_consolidation.py` need migration or compatibility coverage if GraphStore protocol methods are deprecated.
- Files not to modify:
  - Do not further pollute `copilot_sdk/graph/protocol.py`.
- Implementation guard:
  - No direct `graph_store` should be passed to the ledger unless the object conforms to the ledger's expected signature or is wrapped in a domain-aware adapter.
- Files to leave as-is:
  - `prompt_evolver.py`, `variant_store.py`, `credit_attribution.py`, and `toy_rules.py` should remain unless public exports are reorganized.
- Net new code estimate:
  - Small if dual-protocol wrappers are used: roughly 250-450 lines.
  - Larger if renaming to B1 exact filenames and preserving backward compatibility: roughly 500-900 lines plus tests.

### Q3: Router Mount Readiness
- Trading:
  - Already mounts current router with `graph_store_factory` and `variant_provider=lambda: []` at `apps/trading/backend/app/main.py:243` through `:249`.
  - Current router can mount, but B1 `evolver_factory` is absent.
- Purchasing:
  - Already mounts current router via legacy string-domain call and `ledger_provider` at `apps/purchasing/backend/app/main.py:281` through `:283`.
  - This relies on backward compatibility behavior at `copilot_sdk/backend/evolution_router.py:24` through `:31`.
- DataOps:
  - Already mounts current router with `graph_store_factory` and `_evolution_variants` at `apps/dataops/backend/app/main.py:257` through `:263`.
  - Also has an `ae_router` mounted at `apps/dataops/backend/app/main.py:266`, which may be a parallel app-specific surface.
- S2P:
  - `apps/s2p/backend/app/main.py` is absent from the checked path, so no mount was found.
- Are any apps already mounting it:
  - Yes: Trading, Purchasing, and DataOps.

### Q4: Promotion Thresholds
- Expected B1 thresholds:
  - `DELTA_MIN=0.05`.
  - `Q_FLOOR=0.80`.
  - `SIGMA_MAX=0.10`.
  - `MIN_SHADOW_SAMPLES=50`.
  - `MIN_SHADOW_BATCHES=3`.
  - Conservation fail-closed, `None` means no promotion.
- Actual values found:
  - `PromptEvolverConfig.shadow_delta_min = 0.05` at `copilot_sdk/evolution/prompt_evolver.py:27`.
  - `PromptEvolverConfig.shadow_q_floor = 0.80` at `copilot_sdk/evolution/prompt_evolver.py:28`.
  - `PromptEvolverConfig.shadow_sigma_max = 0.10` at `copilot_sdk/evolution/prompt_evolver.py:29`.
  - `PromptEvolverConfig.shadow_min_samples = 50` at `copilot_sdk/evolution/prompt_evolver.py:30`.
  - `PromptEvolverConfig.shadow_min_batches = 3` at `copilot_sdk/evolution/prompt_evolver.py:31`.
  - `DefaultPromotionGate.superiority_threshold_pp = 5.0`, `accuracy_floor = 0.70`, and `min_shadow_decisions = 10` at `copilot_sdk/evolution/gate.py:10` through `:18`.
  - `DefaultPromotionGate` defaults missing conservation to GREEN at `copilot_sdk/evolution/gate.py:29`, so it is not fail-closed.
  - `AutonomousPromotionGate` requires status GREEN at `copilot_sdk/evolution/autonomous_promotion.py:42` through `:49`.

### Q5: Test Delta
- Existing evolution-related test count: 182.
- B1 requested count: not specified numerically in this prompt, but expected coverage includes protocols, store separation, selector, promotion, shadow, AgentEvolver, router, and P16 guards.
- Net new tests needed:
  - `EvolutionStore` protocol tests.
  - Ledger tests proving it uses `EvolutionStore` and does not require `GraphStore`.
  - Ledger/router persistence tests proving events persist under the configured domain when backed by SQLiteGraphStore through an adapter.
  - Migration/compatibility tests proving old GraphStore-backed persistence still works during transition.
  - Fail-closed promotion tests for missing, unknown, AMBER, RED, and GREEN status.
  - Router tests for optional `evolver_factory` while preserving current endpoints.
  - Shadow fire-and-forget tests if B1 requires asynchronous comparison semantics.
  - Generic UCB selector tests if `UCB1VariantSelector` is added.
- Future validation should include:
  - `python -m pytest tests/test_graphstore_consolidation.py -v --timeout=120`.
  - Existing evolution tests under `tests/evolution/`.
  - `tests/backend/test_evolution_router.py`.
  - `tests/graph/test_graph_store_evolution.py`.
- Tests that need rewrite due current coupling:
  - `tests/graph/test_graph_store_evolution.py:25` directly asserts protocol coupling and would need to change under strict separation.
  - `tests/graph/test_graph_store_evolution.py:118` asserts SQLiteGraphStore satisfies the evolution-extended GraphStore protocol.
  - `tests/test_graphstore_consolidation.py:221` and `:239` assert GraphStore-level evolution parity and should remain covered by any compatibility plan.
  - `tests/evolution/test_gate.py:53` through `:57` asserts AMBER conservation passes, which may conflict with GREEN-only promotion.

## Implementation Scope
- Files to CREATE:
  - `copilot_sdk/evolution/protocols.py` only if used as a compatibility re-export or new canonical protocol module.
  - `copilot_sdk/evolution/promotion.py` for B1 fail-closed promotion evaluator if not modifying `gate.py`.
  - `copilot_sdk/evolution/selector.py` for generic UCB selector if not extending `context_selector.py`.
  - `copilot_sdk/evolution/agent_evolver.py` only if a compatibility wrapper around existing `evolver.py` is chosen.
- Files to MODIFY:
  - `copilot_sdk/evolution/protocol.py` or new `protocols.py` for `EvolutionStore`.
  - `copilot_sdk/evolution/ledger.py` to use `EvolutionStore` naming/contract.
  - `copilot_sdk/evolution/ledger.py` or a ledger persistence adapter to fix the domain/signature mismatch.
  - `copilot_sdk/evolution/gate.py` or new `promotion.py` for fail-closed semantics.
  - `copilot_sdk/backend/evolution_router.py` for optional `evolver_factory` and domain-aware persistence adapter injection.
  - `tests/graph/test_graph_store_evolution.py` if GraphStore protocol pollution is corrected.
  - `tests/test_graphstore_consolidation.py` if compatibility assertions need to move from GraphStore coupling to EvolutionStore compatibility.
- Files ALREADY CORRECT:
  - `copilot_sdk/evolution/__init__.py` exports current public surface.
  - `copilot_sdk/evolution/shadow.py` is domain-neutral but not fire-and-forget.
  - `copilot_sdk/evolution/prompt_evolver.py` already has prompt UCB and threshold constants.
  - `copilot_sdk/evolution/variant_store.py` already provides in-memory variant lifecycle and stats.
- Tests to ADD:
  - EvolutionStore protocol and structural store tests.
  - Ledger persistence signature/domain tests.
  - Fail-closed promotion evaluator tests.
  - Router `evolver_factory` tests.
  - Router-backed persistence tests that verify domain-correct events.
  - Fire-and-forget shadow tests if new semantics are implemented.
  - Import discipline tests for any new modules.
- Tests ALREADY PASSING:
  - Root suite: 654 passed.
  - Evolution-related inventory: 182 tests.
- Estimated effort:
  - 1 focused reconciliation pass for protocol/store/router compatibility.
  - 1 implementation pass for B1-specific selector/promotion/shadow deltas.
  - 1 test migration pass for GraphStore protocol coupling.

## Risks
- Breaking changes to existing consumers:
  - Trading, Purchasing, and DataOps already mount the current router, so router signature or prefix changes are risky.
  - Purchasing uses legacy `create_evolution_router(DOMAIN, ledger_provider=...)`, shown at `apps/purchasing/backend/app/main.py:282`.
  - Existing graph tests assert GraphStore evolution methods, so strict removal would break tests.
  - Current ledger/router persistence can silently store events under wrong fields if raw domain-aware GraphStore is passed into the ledger.
- Downstream test updates needed:
  - GraphStore protocol tests need migration if `EvolutionStore` becomes canonical.
  - Root consolidation tests in `tests/test_graphstore_consolidation.py` need to be included in the compatibility plan.
  - Gate tests need updates if promotion becomes GREEN-only fail-closed.
  - Router tests need coverage for `evolver_factory` without breaking existing closure cache expectations.
  - Router-backed persistence tests need to prove domain-correct storage through the new adapter path.
- Cross-app compatibility concerns:
  - Trading/DataOps pass `graph_store_factory`, while Purchasing uses legacy domain plus ledger provider.
  - DataOps also mounts `ae_router`, so avoid endpoint collision or ambiguous evolution surfaces.
  - S2P main path was absent in this checkout, so S2P readiness cannot be proven from local files.

## Blockers
- `GraphStore` protocol is already polluted with evolution methods at `copilot_sdk/graph/protocol.py:78` and `copilot_sdk/graph/protocol.py:88`.
- Existing tests assert the current coupling, notably `tests/graph/test_graph_store_evolution.py:25`.
- Ledger persistence currently uses a no-domain positional call at `copilot_sdk/evolution/ledger.py:30` through `:33`, while GraphStore requires domain first at `copilot_sdk/graph/protocol.py:78` through `:85`.
- Router-backed persistence passes raw graph store into that ledger at `copilot_sdk/backend/evolution_router.py:36` through `:37`; this must be adapted before implementation is READY.
- Current `DefaultPromotionGate` does not fail closed because missing conservation defaults to GREEN at `copilot_sdk/evolution/gate.py:29`.
- Current router has no `evolver_factory` parameter, while B1 asks for router extension around evolver injection.
- The existing package has `protocol.py`, `evolver.py`, `gate.py`, and `context_selector.py`; introducing parallel B1 filenames without a compatibility plan would create confusing duplicate concepts.
