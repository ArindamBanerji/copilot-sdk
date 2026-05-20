# AE-SDK AgentEvolver Extraction Plan

## 1. Executive Summary

Current state: SOC has a prompt-variant evolver implemented as module-level state and module functions in `backend/app/services/evolver.py`; the state includes `PROMPT_STATS`, `CATEGORY_PROMPT_STATS`, `ACTIVE_PROMPTS`, `RECENT_PROMOTIONS`, and `WEIGHT_HISTORY` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:30`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:37`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:39`). The SDK already has a different domain-neutral rule evolver named `AgentEvolver`, with `register_rule`, `evolve`, history, promoted-rule, and reset methods (`copilot_sdk/evolution/evolver.py:27`, `copilot_sdk/evolution/evolver.py:43`, `copilot_sdk/evolution/evolver.py:49`, `copilot_sdk/evolution/evolver.py:106`, `copilot_sdk/evolution/evolver.py:113`, `copilot_sdk/evolution/evolver.py:116`).

Target state: add a reusable SDK prompt-variant evolution layer that preserves SOC's AE-CONTEXT prompt-selection behavior while using instance-local state, domain-supplied categories/templates/hooks, and the existing SDK evolution/event boundaries (`copilot_sdk/evolution/protocol.py:47`, `copilot_sdk/evolution/ledger.py:14`, `copilot_sdk/graph/protocol.py:79`). This should not replace the existing SDK rule-level `AgentEvolver` in the first implementation; it should add a distinct prompt-variant evolver that can coexist with the current rule evolver (`tests/evolution/test_evolver.py:43`, `tests/evolution/test_evolver.py:69`, `tests/evolution/test_evolver.py:149`).

Classification: `SCOPE_REPAIR_NEEDED`. The request is implementable, but the uploaded assumption that the SDK has no equivalent evolution surface is materially incomplete: the SDK already exports and tests a separate rule-level `AgentEvolver` (`copilot_sdk/evolution/__init__.py:3`, `tests/evolution/test_evolver.py:3`), while SOC's module implements category-aware prompt-variant UCB and global reset semantics (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:177`).

This document is plan-only. No SDK source files, tests, app files, SOC files, routers, GraphStore protocol files, or configuration files were changed.

The SOC repo is read-only reference input for this plan. Future SOC migration must be a separate prompt and must preserve existing router/function names while replacing internals through an SDK-backed adapter (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:310`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:651`).

Recommended implementation phases:

1. SDK prompt-variant dataclasses and in-memory store, no SOC changes.
2. SDK global/category UCB selection, outcome recording, reset, and tests.
3. SDK promotion/shadow abstractions and tests.
4. SOC adapter/wrapper migration preserving module-level API and fire-and-forget behavior.
5. GPT-5.5 SDK review, then SOC migration review.

## 2. Current SOC Architecture

SOC public interface:

- `get_prompt_variant(alert_type=None, *, category=None)` returns category-aware variants when possible, then legacy prompt variants (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:178`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:187`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:191`).
- `record_decision_outcome(...)` updates prompt stats, optional category stats, and weight history (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:234`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:253`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:286`).
- `check_for_promotion(alert_type)` computes same-family improvements and promotes when the candidate improves over active by more than 0.05 with at least 10 total samples (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:300`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:330`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:351`).
- `get_evolution_summary`, `get_variant_comparison`, `get_weight_history`, and `reset_evolver_state` provide SOC-facing summary and reset behavior (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:432`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:509`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:583`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:545`).

SOC state and AE-CONTEXT behavior:

- `PROMPT_STATS` is a module-global dict keyed by hardcoded SOC prompt ids such as `TRAVEL_CONTEXT_v1` and `PHISHING_RESPONSE_v1` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`).
- `CATEGORY_PROMPT_STATS` is a module-global nested dict keyed by category and prompt id (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`).
- Category-aware UCB is implemented by `_select_category_ucb_variant`, which calculates a mean plus exploration bonus using `math.sqrt(log_total / total)` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:112`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:132`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:134`).
- Category normalization imports SOC-specific category maps from `app.domains.soc.config` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:84`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:86`).
- SOC config still treats `services/evolver.py` prompt stat keys as the source for prompt variants (`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:595`, `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:596`).

Promotion and shadow flow:

- The SOC promotion gate is separate from `evolver.py`; it defines thresholds `DELTA_MIN`, `Q_FLOOR`, `SIGMA_MAX`, `MIN_SHADOW_SAMPLES`, and `MIN_SHADOW_BATCHES` (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:39`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:40`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:41`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:42`).
- `evaluate_promotion` requires SHADOW status, enough samples, win-rate threshold, Q floor, conservation approval, minimum batches, and variance limit (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:111`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:126`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:135`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:143`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:151`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:165`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:181`).
- Triage schedules shadow comparison with `asyncio.create_task` after the main response path, preserving fire-and-forget semantics (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:651`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:654`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`).
- `maybe_shadow_compare` catches its own errors because it is used in a fire-and-forget path (`gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:96`, `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:103`, `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:107`).

Evolution ledger and events:

- SOC's `backend/app/framework/evolution_ledger.py` is a compatibility shim that re-exports from `gae.evolution` (`gen-ai-roi-demo-v4-v50/backend/app/framework/evolution_ledger.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/framework/evolution_ledger.py:8`, `gen-ai-roi-demo-v4-v50/backend/app/framework/evolution_ledger.py:14`).
- SOC shadow flush records `SHADOW_RESULT` evolution events through the GAE ledger path (`gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:187`, `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:231`).

Level 1 / Level 2 separation:

- SOC `evolver.py` contains prompt/rule stats and imports SOC config/registry modules, but it does not import `ProfileScorer` or centroid APIs in the inspected implementation (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:570`).
- SOC `promotion_gate.py` documents that it reads learning health and does not mutate Level 1 scorer/centroid state (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:5`).
- Triage uses the Level 1 `ProfileScorer` for scoring before the fire-and-forget evolution hook (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:147`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:226`, `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`).

## 3. Current SDK Evolution Architecture

Existing SDK evolution package:

- `copilot_sdk/evolution/evolver.py` defines a rule-level `AgentEvolver` and `PlateauConfig` (`copilot_sdk/evolution/evolver.py:16`, `copilot_sdk/evolution/evolver.py:27`).
- The SDK `AgentEvolver` depends on an `EvolutionLedger`, `ShadowRunner`, and `PromotionGate`, all injectable at construction (`copilot_sdk/evolution/evolver.py:28`, `copilot_sdk/evolution/evolver.py:31`, `copilot_sdk/evolution/evolver.py:32`, `copilot_sdk/evolution/evolver.py:33`).
- The SDK rule evolver's core API is `register_rule`, `get_active_rules`, and `evolve(rule_name, decisions, conservation_state=None, seed=None)` (`copilot_sdk/evolution/evolver.py:43`, `copilot_sdk/evolution/evolver.py:46`, `copilot_sdk/evolution/evolver.py:49`).
- SDK tests assert that the current `AgentEvolver` promotes generated rule variants, records event sequences, and keeps active rules on reset (`tests/evolution/test_evolver.py:69`, `tests/evolution/test_evolver.py:108`, `tests/evolution/test_evolver.py:149`).

SDK protocols and storage:

- `EvolutionLedger`, `ShadowRunner`, and `PromotionGate` are explicit protocols (`copilot_sdk/evolution/protocol.py:47`, `copilot_sdk/evolution/protocol.py:66`, `copilot_sdk/evolution/protocol.py:77`).
- `InMemoryEvolutionLedger` stores events instance-locally and can optionally persist events to a GraphStore (`copilot_sdk/evolution/ledger.py:14`, `copilot_sdk/evolution/ledger.py:17`, `copilot_sdk/evolution/ledger.py:25`, `copilot_sdk/evolution/ledger.py:33`).
- GraphStore already has `save_evolution_event(event_type, rule_name, variant_id, metadata=None)` (`copilot_sdk/graph/protocol.py:79`).
- SDK memory and SQLite graph stores implement `save_evolution_event` (`copilot_sdk/graph/memory_store.py:167`, `copilot_sdk/graph/sqlite_store.py:187`).

SDK router and scorer usage:

- `create_evolution_router` lazily builds an SDK rule `AgentEvolver` for API routes (`copilot_sdk/backend/evolution_router.py:18`, `copilot_sdk/backend/evolution_router.py:32`, `copilot_sdk/backend/evolution_router.py:34`).
- The router exposes `/variants`, `/history`, and `/promoted` for the current rule-evolution API (`copilot_sdk/backend/evolution_router.py:45`, `copilot_sdk/backend/evolution_router.py:71`, `copilot_sdk/backend/evolution_router.py:84`).
- `CompoundingScorer` imports and registers the existing SDK rule evolver with toy rules when evolution is enabled (`copilot_sdk/scoring/scorer.py:719`, `copilot_sdk/scoring/scorer.py:733`, `copilot_sdk/scoring/scorer.py:740`, `copilot_sdk/scoring/scorer.py:742`).
- Existing SDK router tests verify that `/api/evolution/variants` can accept a `variant_provider`, and that separate router instances keep distinct evolver closures (`tests/backend/test_evolution_router.py:93`, `tests/backend/test_evolution_router.py:98`, `tests/backend/test_evolution_router.py:125`, `tests/backend/test_evolution_router.py:137`).
- DataOps also has a separate fixture-backed operational AE router, not an SDK prompt evolver: it defines local fixture defaults and operational rule endpoints in app code (`apps/dataops/backend/app/ae_router.py:1`, `apps/dataops/backend/app/ae_router.py:17`, `apps/dataops/backend/app/ae_router.py:24`, `apps/dataops/backend/app/ae_router.py:418`, `apps/dataops/backend/app/ae_router.py:443`). This must remain app/domain code unless a later DataOps migration is explicitly approved.

SDK gaps relative to SOC:

- The SDK rule evolver has no `get_prompt_variant`, `record_decision_outcome`, `CATEGORY_PROMPT_STATS`, legacy alert-type positional behavior, or SOC-style reset semantics in the inspected API (`copilot_sdk/evolution/evolver.py:43`, `copilot_sdk/evolution/evolver.py:49`, `copilot_sdk/evolution/evolver.py:116`; `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:78`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:128`).
- SDK `ContextAwareSelector` has context-aware scoring, but it is not the SOC `CATEGORY_PROMPT_STATS` UCB formula; it combines UCB/win-rate with phase, evidence, category, and failure adjustments (`copilot_sdk/evolution/context_selector.py:19`, `copilot_sdk/evolution/context_selector.py:31`, `copilot_sdk/evolution/context_selector.py:37`, `copilot_sdk/evolution/context_selector.py:43`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:112`).

## 4. SOC-Specific vs Generic Inventory

| Item | Evidence | Classification | Migration treatment |
| --- | --- | --- | --- |
| Hardcoded SOC prompt ids and initial stats | `PROMPT_STATS` defines `TRAVEL_CONTEXT_v1`, `TRAVEL_CONTEXT_v2`, `PHISHING_RESPONSE_v1`, and `PHISHING_RESPONSE_v2` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`) | SOC-specific seed data | Move into SOC adapter configuration; SDK accepts injected `VariantSpec` seeds. |
| Module-global category stats | `CATEGORY_PROMPT_STATS` is a module-global `defaultdict` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`) | Generic behavior, bad storage shape | Move to instance-local `VariantStore` in SDK. |
| Category-aware UCB | `_select_category_ucb_variant` calculates UCB with mean plus exploration bonus (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:112`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:134`) | Generic | Preserve exact semantics in SDK with configurable exploration constant. |
| SOC category resolver | `_normalize_category` imports SOC constants (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:86`) | SOC-specific | Replace with domain-supplied resolver hook. |
| Legacy alert-type positional behavior | Tests call `get_prompt_variant("anomalous_login")` and no-arg fallback (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:34`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`) | SOC compatibility | Preserve in SOC wrapper; SDK can support `context_key` plus keyword `category`. |
| Outcome recording | `record_decision_outcome` updates global and category stats (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:234`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:253`) | Generic | SDK method updates global and category stats through instance store. |
| Promotion threshold in `evolver.py` | Improvement threshold `> 0.05` and candidate sample threshold `>= 10` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:330`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340`) | Generic default from SOC | Move to config defaults for SOC adapter. |
| Promotion gate thresholds | `DELTA_MIN`, `Q_FLOOR`, `SIGMA_MAX`, sample and batch constants (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:42`) | Generic gate mechanics, SOC defaults | Extract to configurable SDK gate; SOC adapter supplies current values. |
| Fire-and-forget shadow integration | Triage uses `asyncio.create_task(maybe_shadow_compare(...))` (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`) | Generic integration pattern | Preserve in SOC; SDK exposes async-safe shadow runner, does not force await. |
| Evolution ledger shim | SOC shim re-exports `gae.evolution` (`gen-ai-roi-demo-v4-v50/backend/app/framework/evolution_ledger.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/framework/evolution_ledger.py:14`) | SOC integration detail | SDK uses existing `EvolutionLedger`; SOC adapter bridges old GAE ledger if needed. |
| Narrative and impact calculators | Hardcoded anomalous-login/phishing narratives and cost constants (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:368`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:395`) | SOC-specific presentation | Keep in SOC adapter or presentation layer, not SDK core. |
| Reset behavior | Reset restores initial stats, clears category stats, and resets registry/shadow/promotion components (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:545`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:553`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:567`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:570`) | Generic reset plus SOC integration | SDK reset clears instance stats; SOC wrapper reset also resets SOC registry/shadow/gate. |
| Level 1 scorer reads | Promotion gate reads learning health but documents no Level 1 mutation (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:65`) | Integration boundary | SDK gate receives health/conservation inputs from caller; no ProfileScorer import. |

## 5. Target SDK Architecture

Use the existing `copilot_sdk.evolution` package and avoid replacing the current rule-level `AgentEvolver` API that is already tested (`copilot_sdk/evolution/__init__.py:3`, `tests/evolution/test_evolver.py:43`). Add a domain-agnostic prompt-variant layer in new files with unambiguous names:

- `copilot_sdk/evolution/prompt_evolver.py`: `PromptAgentEvolver` or `PromptVariantEvolver`, a prompt-variant class distinct from the existing rule-level `AgentEvolver`.
- `copilot_sdk/evolution/variant_store.py`: `VariantStore` protocol and `InMemoryVariantStore`.
- `copilot_sdk/evolution/config.py`: `AgentEvolverConfig`, threshold config, resolver config, and optional hook types.
- `copilot_sdk/evolution/promotion_gate.py` or extension to `gate.py`: SOC-compatible prompt promotion gate config.

Target dataclasses:

- `AgentEvolverConfig`: categories, default variant id, exploration constant, promotion thresholds, shadow thresholds, optional category resolver, optional lifecycle hooks.
- `VariantSpec` / `PromptVariant`: id, domain category, family, version, template or payload, status, metadata.
- `VariantStats`: successes, total, success rate, optional failures, weight history.
- `CategoryStats`: category -> variant id -> `VariantStats`.
- `ShadowResult` and `PromotionResult`: promotion/shadow output structures aligned with SDK protocol style (`copilot_sdk/evolution/protocol.py:66`, `copilot_sdk/evolution/protocol.py:77`).

Target properties:

- Domain-agnostic: no SOC imports, SOC category constants, SOC alert field names, SOC prompt ids, or SOC route imports in SDK core (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`).
- Instance-local: replace `PROMPT_STATS`, `CATEGORY_PROMPT_STATS`, `ACTIVE_PROMPTS`, `RECENT_PROMOTIONS`, and `WEIGHT_HISTORY` globals with fields on the evolver/store instance (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:30`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:37`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:39`).
- Level 1 / Level 2 separation: SDK evolver must not import or mutate `ProfileScorer`, `CompoundingScorer`, centroids, or Level 1 learning state. Existing SDK scoring currently imports the rule evolver from scoring setup (`copilot_sdk/scoring/scorer.py:719`), so prompt-variant extraction must not add reverse coupling into scoring.
- FastAPI-free: SDK evolver should be testable without routers; the current SDK router is a thin wrapper around the existing rule evolver (`copilot_sdk/backend/evolution_router.py:18`, `copilot_sdk/backend/evolution_router.py:45`).
- App/domain routers stay adapter consumers. For example, DataOps AE endpoints currently read local fixtures and generate operational lifecycle payloads in app code (`apps/dataops/backend/app/ae_router.py:74`, `apps/dataops/backend/app/ae_router.py:367`, `apps/dataops/backend/app/ae_router.py:418`).

## 6. Domain Configuration Design

Domain configuration should supply the data currently hardcoded in SOC:

- Categories can come from a domain preset shape or caller-supplied list. SDK `DomainShape` already has `category_names` (`copilot_sdk/scoring/config.py:13`, `copilot_sdk/scoring/config.py:19`).
- SOC-specific alert-type-to-category mapping should be supplied as a resolver hook because current SOC normalization imports `ALERT_TYPE_CATEGORY_MAP` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:84`).
- Prompt/rule variants should be injected as `VariantSpec` records; SOC prompt variants currently come from `PROMPT_STATS`, `ACTIVE_PROMPTS`, SOC config, and the GAE variant registry (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:30`, `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:603`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:144`).
- Thresholds should be configurable: promotion delta, Q floor, sigma max, min shadow samples, min shadow batches, UCB exploration constant, and any candidate sample floor (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:42`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:42`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340`).
- Lifecycle hooks should be optional: `on_variant_selected`, `on_outcome_recorded`, `on_shadow_result`, `on_promoted`, `on_rejected`, and persistence hooks. SDK already models event persistence through `EvolutionLedger.append` (`copilot_sdk/evolution/ledger.py:25`).

## 7. GraphStore / Event Store Integration

Recommended first extraction: use an in-memory/instance `VariantStore` first and optionally emit lifecycle events through the existing SDK `EvolutionLedger`. Do not add GraphStore protocol methods in the first prompt.

Evidence for this recommendation:

- GraphStore already has a generic `save_evolution_event` method (`copilot_sdk/graph/protocol.py:79`).
- `InMemoryEvolutionLedger.append` can persist events through a provided graph store without changing the protocol (`copilot_sdk/evolution/ledger.py:25`, `copilot_sdk/evolution/ledger.py:33`).
- SDK memory and SQLite stores already implement `save_evolution_event` (`copilot_sdk/graph/memory_store.py:167`, `copilot_sdk/graph/sqlite_store.py:187`).

Future persistence can add a dedicated `VariantStore` backed by GraphStore or SQLite if product requirements demand queryable variant state. That should be a separate prompt after the SDK in-memory semantics are proven.

## 8. Promotion Gate Design

Extract SOC promotion semantics into configurable SDK gate logic:

- Preserve the SOC simple prompt-family promotion check from `evolver.py`: compare candidate success rate against active success rate, require improvement over 0.05, and require at least 10 candidate samples (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:327`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:330`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:340`).
- Preserve SOC shadow promotion thresholds as configuration defaults for the SOC adapter: delta, Q floor, sigma max, min shadow samples, min shadow batches, and disagreement/rollback values (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:45`).
- Promotion evaluation can read health and conservation inputs passed by caller, but SDK gate must not import `ProfileScorer` or mutate Level 1 state. SOC's current promotion gate reads learning-health components in helper functions and documents no mutation (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:1`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:65`).
- Category-aware selection affects selection; promotion remains global unless a future SOC migration explicitly changes current behavior. SOC migration tests assert that promotion still uses global stats after category stats updates (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:156`).

## 9. AE-CONTEXT Preservation

The SDK design must preserve these SOC-tested behaviors:

- `get_prompt_variant(category=None)` supports keyword category and no-arg fallback (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:178`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`).
- SOC wrapper preserves legacy positional `alert_type` behavior (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:34`).
- Category selection can differ from global selection (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:78`).
- Category-aware selection must use UCB, not raw success rate only (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:132`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:134`).
- No category stats should fall back to legacy/global behavior (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:109`).
- Recording an outcome updates both global and category stats when category is present (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:128`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:141`).
- Reset clears category stats (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:177`).

## 10. SOC Migration Plan

Phase 1: SDK prompt-variant core. Add SDK dataclasses, in-memory store, selection/outcome/reset semantics, and unit tests. Do not modify SOC, SDK scoring, SDK backend router, or app AE routers.

Phase 2: SDK promotion and shadow interfaces. Add configurable prompt promotion gate and shadow result handling. Use existing `EvolutionLedger` where events are needed (`copilot_sdk/evolution/ledger.py:25`).

Phase 3: SOC adapter. Update SOC `backend/app/services/evolver.py` internals to configure the SDK prompt evolver with SOC prompt variants, category resolver, thresholds, and legacy presentation helpers while preserving function names imported by routers (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:310`, `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:313`, `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:315`, `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:322`).

Phase 4: SOC shadow/promotion adapter. Keep triage fire-and-forget scheduling unchanged unless a direct SDK hook makes the internals cleaner (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`; `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:192`).

Phase 5: SOC migration validation and review. Run SOC backend tests covering evolver migration, promotion gate, shadow runner, triage, and evolution routes.

Backward compatibility requirements:

- SOC module functions keep existing names and response shapes because routers call module-level functions directly (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:313`, `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:315`, `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:322`).
- `reset_evolver_state` must continue resetting SOC registry, shadow runner, promotion gate, GAE state, category stats, and demo weight history until those integrations have SDK equivalents (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:545`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:570`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:578`).

## 11. What Does NOT Change

- `ProfileScorer` is not modified; SOC scoring continues to call it in triage (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:147`).
- `CompoundingScorer.learn` and Level 1 centroid learning are not modified; the SDK prompt evolver must not touch scorer/centroid state (`copilot_sdk/scoring/scorer.py:719`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:1`).
- Conservation behavior is unchanged; the SOC promotion gate currently consumes conservation status as a caller-provided condition (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:151`).
- SOC triage business flow and fire-and-forget semantics remain unchanged (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`).
- Promotion thresholds stay config-equivalent to SOC defaults (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:330`).
- No frontend changes are part of SDK extraction.
- No cross-repo source changes are made in this plan prompt.

## 12. Test Plan

SDK tests:

- `test_variant_registration_and_selection`: verifies injected variants can be selected.
- `test_no_arg_global_ucb_fallback`: verifies no-arg selection uses global stats.
- `test_category_aware_ucb_differs_from_global`: ports SOC behavior from migration test (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:78`).
- `test_category_ucb_not_raw_success_rate`: ports SOC UCB invariant (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`).
- `test_cold_start_fallback_to_global`: ports no-category fallback (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:109`).
- `test_record_outcome_updates_global_and_category_stats`: ports SOC outcome invariants (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:128`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:141`).
- `test_reset_clears_global_and_category_stats`: ports reset behavior without SOC globals (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:177`).
- `test_promotion_gate_thresholds`: verifies SOC-equivalent improvement, floor, sample, batch, and variance thresholds.
- `test_shadow_result_handling`: verifies shadow output can update lifecycle state without FastAPI.
- `test_instance_isolation`: two SDK evolvers do not share stats, replacing SOC module globals (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`).
- `test_level_1_boundary`: import scan or behavioral test ensures prompt evolver does not import `ProfileScorer`, `CompoundingScorer`, or centroid modules.

SOC migration tests:

- SOC wrapper returns same `get_prompt_variant` behavior for no-arg, category, and positional alert-type calls (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:34`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`).
- SOC wrapper preserves category-aware UCB and reset behavior (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:177`).
- Triage still schedules fire-and-forget shadow comparison and does not await it (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:192`).
- Promotion gate behavior remains unchanged for thresholds and conservation conditions (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:126`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:151`).

## 13. Implementation Sequence

1. Prompt 1: SDK prompt-variant dataclasses, `InMemoryVariantStore`, basic registration/selection/reset tests.
2. Prompt 2: SDK global/category UCB selection, outcome recording, AE-CONTEXT preservation tests.
3. Prompt 3: SDK prompt promotion gate, shadow result abstractions, lifecycle event hooks, tests.
4. Prompt 4: SOC adapter/migration plan or implementation preserving module function API and fire-and-forget semantics.
5. Prompt 5: GPT-5.5 SDK line-by-line and architecture review.
6. Prompt 6: GPT-5.5 SOC migration review.

## 14. Risks and Mitigations

- Hidden SOC coupling: `evolver.py` imports SOC config and variant registry paths (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:144`). Mitigation: adapter supplies resolvers and registry hooks.
- Global mutable state copied into SDK: SOC state is module-global (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`). Mitigation: SDK store is instance-local and has isolation tests.
- AE-CONTEXT regression: category UCB has explicit SOC tests (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:78`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`). Mitigation: port tests before SOC migration.
- Promotion threshold drift: SOC thresholds exist in two places (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:330`, `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:38`). Mitigation: central SDK config with SOC default adapter.
- Fire-and-forget drift: triage currently uses `asyncio.create_task` (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`). Mitigation: SOC migration keeps scheduling point unless separately approved.
- Level 1 / Level 2 violation: promotion gate reads learning state today (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:65`). Mitigation: SDK gate receives health inputs from caller and never imports scorers.
- GraphStore overreach: SDK already has generic evolution events (`copilot_sdk/graph/protocol.py:79`). Mitigation: no new protocol change in first extraction.
- Router response drift: SOC routers call module-level functions (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:313`). Mitigation: wrapper preserves response shapes and names.
- Reset mismatch: SOC reset coordinates multiple subsystems (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:570`). Mitigation: keep SOC wrapper reset orchestration until those services are SDK-backed.

## 15. Files to Modify in Future Implementation

SDK future files:

- `copilot_sdk/evolution/prompt_evolver.py` for the prompt-variant evolver.
- `copilot_sdk/evolution/variant_store.py` for instance-local stats.
- `copilot_sdk/evolution/config.py` for config dataclasses.
- `copilot_sdk/evolution/promotion_gate.py` or targeted additions to `copilot_sdk/evolution/gate.py`.
- `copilot_sdk/evolution/__init__.py` for exports after API review.

SDK tests:

- `tests/evolution/test_prompt_agent_evolver.py`
- `tests/evolution/test_prompt_category_ucb.py`
- `tests/evolution/test_prompt_promotion_gate.py`
- `tests/evolution/test_prompt_evolver_level_boundary.py`

SOC future migration files:

- `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py`
- `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py` only if wrapping gate config is needed.
- `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py` only if adapting shadow hooks is needed.
- SOC tests such as `backend/tests/test_evolver_migration.py`, `backend/tests/test_ae_integration.py`, `backend/tests/test_promotion_gate.py`, and `backend/tests/test_shadow_runner.py`.

Forbidden for this extraction unless separately approved:

- `ProfileScorer` and Level 1 scorer internals.
- `copilot_sdk/scoring/scorer.py` / `CompoundingScorer`, except no changes are expected for prompt-variant extraction.
- Conservation routers and conservation formulas.
- Frontend code.
- Any SOC changes during SDK-only prompts.

## 16. Reading Log

SDK:

- `CLAUDE.md`: repo rules and docs-vs-code truth, lines 5-8, 22-28, 39-47, 53.
- `copilot_sdk/evolution/evolver.py`: full file, especially `PlateauConfig`, `AgentEvolver`, `evolve`, history, promoted rules, reset, and plateau helpers, lines 16-244.
- `copilot_sdk/evolution/__init__.py`: exports, lines 3-38.
- `copilot_sdk/evolution/protocol.py`: event dataclasses and ledger/shadow/gate protocols, lines 10-84.
- `copilot_sdk/evolution/gate.py`: default promotion gate thresholds and evaluation, lines 9-53.
- `copilot_sdk/evolution/ledger.py`: in-memory ledger and optional GraphStore persistence, lines 14-70.
- `copilot_sdk/evolution/context_selector.py`: context-aware selector, lines 10-55.
- `copilot_sdk/evolution/shadow.py`: default shadow runner, lines 12-102.
- `copilot_sdk/evolution/autonomous_promotion.py`: autonomous promotion dataclass and gate, lines 9-79.
- `copilot_sdk/backend/evolution_router.py`: SDK evolution router, lines 18-119.
- `copilot_sdk/scoring/config.py`: `DomainShape`, `DomainPreset`, `PlateauConfig` reference, lines 10-51.
- `copilot_sdk/graph/protocol.py`: evolution event protocol method, lines 79-86.
- `copilot_sdk/graph/memory_store.py`: evolution event storage/reset, lines 25, 167-180, 212.
- `copilot_sdk/graph/sqlite_store.py`: SQLite evolution event storage, lines 187-221.
- `copilot_sdk/scoring/scorer.py`: existing SDK rule evolver integration, lines 710-750.
- `tests/evolution/test_evolver.py`: current SDK rule evolver tests, lines 1-176.
- `tests/backend/test_evolution_router.py`: SDK router instance/variant-provider tests, lines 1-35, 93-105, 125-141.
- `apps/dataops/backend/app/ae_router.py`: app-local fixture-backed operational AE endpoints, lines 1-80, 367-455.

SOC:

- `CLAUDE.md`: source-of-truth and read-only discipline, lines 5-16, 18-23, 102-131, 164-167.
- `backend/app/services/evolver.py`: full file, especially module globals, category UCB, public methods, promotion, summary, reset, and demo history, lines 1-656.
- `backend/app/services/promotion_gate.py`: full file, especially thresholds, Level 1 boundary docstring, evaluation flow, execution, rollback, reset, lines 1-465.
- `backend/app/services/shadow_runner.py`: shadow comparison/fire-and-forget support, lines 1-249.
- `backend/app/framework/evolution_ledger.py`: GAE re-export shim, lines 1-30.
- `backend/app/routers/triage.py`: scoring and fire-and-forget shadow scheduling, lines 26-43, 147-226, 651-672.
- `backend/app/routers/evolution.py`: module-function evolver integration, lines 280-335.
- `backend/app/domains/soc/config.py`: prompt variant config references to `services/evolver.py`, lines 595-610.
- `backend/tests/test_evolver_migration.py`: AE-CONTEXT and fire-and-forget tests, lines 1-224.
- `backend/tests/test_ae_integration.py`: evolution scan and integration tests, lines 1-220.

## Prompt Verification Pass

- SOC evolver interface is mapped through module functions in `backend/app/services/evolver.py` (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:178`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:234`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:300`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:545`).
- SOC-specific references are inventoried, including SOC categories, prompt ids, variant registry, narratives, and operational impact (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:83`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:144`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:368`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:395`).
- SDK existing evolution code is mapped, including rule `AgentEvolver`, protocols, ledger, router, GraphStore event support, and tests (`copilot_sdk/evolution/evolver.py:27`, `copilot_sdk/evolution/protocol.py:47`, `copilot_sdk/evolution/ledger.py:14`, `copilot_sdk/backend/evolution_router.py:18`, `copilot_sdk/graph/protocol.py:79`, `tests/evolution/test_evolver.py:43`).
- AE-CONTEXT behavior is explicitly preserved with category-aware UCB, no-arg fallback, legacy positional behavior, reset, and global promotion semantics (`gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:68`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:78`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:93`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:156`, `gen-ai-roi-demo-v4-v50/backend/tests/test_evolver_migration.py:177`).
- PROMPT_STATS and CATEGORY_PROMPT_STATS are planned as instance-local SDK state, replacing module globals (`gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:19`, `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:26`).
- Level 1 / Level 2 boundary is enforced by design: no ProfileScorer, CompoundingScorer, centroid, or conservation mutation in SDK prompt evolver (`gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:1`, `copilot_sdk/scoring/scorer.py:719`).
- Fire-and-forget triage behavior is preserved in SOC migration (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:663`).
- GraphStore decision is explicit: no first-prompt protocol change because `save_evolution_event` already exists (`copilot_sdk/graph/protocol.py:79`).
- Migration is phased and no source/test files were changed in this plan prompt.
