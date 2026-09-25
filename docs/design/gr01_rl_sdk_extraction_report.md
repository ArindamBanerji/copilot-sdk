# GR-01 + RL-SDK extraction report

Date: 2026-09-13. Scope: additive SDK contracts; no domain behavior migration.

## Pre-check and disposition

| Component | Before | Result |
|---|---|---|
| Domain-neutral GraphStore | ALREADY DONE | ALREADY DONE; existing protocol and implementations preserved |
| GraphStore adoption | Five copilots import `copilot_sdk.graph` | SOC, S2P, Trading, Purchasing, DataOps; no new wiring required for this extraction |
| RL control-plane primitives | PARTIAL | EXTRACTED missing mapping-based reward contract, explicit legacy adapter, capped causal credit and fail-closed budget proposals |
| Verified-outcome protocol | PARTIAL | EXTRACTED requested RL receipt schema and atomic-store contract; production adapter adoption remains PARTIAL under SH-06 |
| AGE boundary | UNDERSTOOD | No transport or persistence relocation needed |

The stop-if-all-done gate did not apply: the SDK already contained extensive RL and outcome code, but no `copilot_sdk.rl.OutcomeReceipt`, no receipt carrying all requested fields, and no atomic receipt/learning-intent contract. This is an extension of existing infrastructure, not a second extraction of GraphStore or the SOC engine.

### Graph evidence and compatibility

`copilot_sdk/graph/protocol.py:16` already defines the runtime-checkable, domain-neutral `GraphStore`. Its established vocabulary differs from the prompt's illustrative surface:

| Requested capability | Existing API |
|---|---|
| Save a decision | `write_decision` (line 19), returning decision ID |
| Load centroids | `load_latest_centroids` (line 162) |
| Save centroids | `save_centroids` (line 152); immutable v2 records use `write_centroid_checkpoint` (line 354) |
| Graph context | Optional `GraphTraversalStore.query_context(entity_id, max_depth, *, domain)` (line 250), returning context records |
| Health | App/factory/backend boundary; no required `GraphStore.health()` method |

No methods were added to the existing structural protocol: requiring traversal or replacing checkpoint signatures would break event-field stores and existing consumers. This task does not claim literal `save_decision`, `load_centroids`, or `health` aliases were added. `GraphStore` remains importable through both `copilot_sdk.graph` and `copilot_sdk.graph.protocol`.

Import evidence for the five copilots:

- Trading: `apps/trading/backend/app/main.py:92-93`.
- Purchasing: `apps/purchasing/backend/app/main.py:101-102`.
- DataOps: `apps/dataops/backend/app/main.py:89-90`.
- S2P: `../s2p-copilot/backend/app/graph/s2p_graph_reader.py:8`.
- SOC: `../gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:295` and `services/gae_state.py:272-273`. SOC also composes the AGE adapter in `services/graph_store_adapter.py`.

`../ci-platform/ci_platform/graph/age_client.py:110` owns AGE transport; its async facade executes synchronous psycopg work through threads. `age_graph_store.py` owns persistence, and `age_sdk_adapter.py:11` exposes the shared store boundary. GAE scoring stays behind the existing `CompoundingScorer` facade: `scoring/scorer.py:36-55` defaults to the sibling `graph-attention-engine-v50` checkout and imports `gae.profile_scorer.ProfileScorer`. No AGE transport, scorer behavior or domain traversal logic was moved into RL.

### Existing RL and outcome code

`copilot_sdk/rl/reward.py`, `credit.py`, `exploration.py`, `types.py`, reward functions, and domain presets already exist. They remain unchanged. In particular, the compatibility Thompson policy called by the frozen scorer is untouched; the new budget is an opt-in interface and does not retroactively establish bounds on that policy.

The mapping-based contract follows `docs/design/rl_sdk_design_v1.md` sections 3.2–3.5. SOC's `SOCBinaryReward` already provides `compute_reward`/`reward_range` (`../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:34-60`). S2P's graded function does likewise (`../s2p-copilot/backend/app/domains/s2p/reward.py:80-104`). Older action-pair implementations can use the new adapter. No reward formula was copied out of a domain repository.

`copilot_sdk/outcome/models.py:39` already defines `VerifiedOutcome`, with compatibility translation in `outcome/adapters.py`. Its canonical schema intentionally excludes RL reward fields. S2P also has a local, domain-specific receipt at `backend/app/models/outcome_receipt.py`. Neither model was replaced or altered. The new RL receipt complements the existing verified-decision model.

## Additions

| New file | Contract / behavior |
|---|---|
| `copilot_sdk/rl/reward_protocol.py` | Runtime-checkable mapping-based `RewardFunction`; `LegacyRewardAdapter`; pure, versioned reward computation with finite range validation and normalization |
| `copilot_sdk/rl/outcome_receipt.py` | Immutable `OutcomeReceipt`, bounded legacy dual-read, and `OutcomeReceiptStore` atomic persistence protocol |
| `copilot_sdk/rl/temporal_credit.py` | `TemporalCreditAssigner`: deterministic causal discount, duplicate rejection and aggregate chain-credit cap |
| `copilot_sdk/rl/conservation_budget.py` | `ExplorationBudget`: category-scoped, fail-closed exploration proposal using the conservation fraction |
| `tests/rl/test_shared_control_contract.py` | Contract and compatibility regression tests |
| `docs/design/gr01_rl_sdk_extraction_report.md` | This report |

The only existing source file edited is `copilot_sdk/rl/__init__.py`, with additive imports/exports. `rl.RewardFunction` retains its original identity and signature; the new contract is exported as `rl.MappingRewardFunction`, also available as `rl.reward_protocol.RewardFunction`. The existing `exploration.py` stays intact; its opt-in companion is exported as `rl.ExplorationBudget`. No router mounts were necessary.

### Receipt and migration semantics

The receipt contains `domain`, `decision_id`, `actor`, `evidence`, `verification`, `learning_effect`, computed normalized `reward`, `provenance`, and `schema_version`. Nested mappings/sequences are immutable, serialized dictionaries are detached, and nonfinite data is rejected. Verification requires explicit `verified=True` and a `verification_id`; a numeric reward never implies verification.

The receipt identity is SHA-256 of the domain/decision tuple. Retries and subsequent verification identifiers for the same decision therefore cannot mint another learning identity. A separate full-payload hash detects conflicting replays. A conforming store returns the original result for identical replay and rejects a changed payload; corrections require a separate future amendment policy.

`read_outcome_receipt` prefers an `outcome_receipt` envelope and rejects malformed or cross-domain canonical data without downgrading to legacy fields. A normalized legacy envelope with `reward_raw` is accepted only before an explicit timezone-aware cutoff, with explicit raw range and the same actor/evidence/verification fields. Raw reward and range are preserved in provenance. This is a schema adapter, not a generic parser for every existing router payload. Per-router field mapping remains SH-06 work.

`OutcomeReceiptStore` specifies atomic persistence of the receipt **and its durable learning/ledger intents**, conflict rejection, and idempotent replay. Learning consumers must atomically deduplicate intent IDs with their effects. No concrete store is asserted to implement this new protocol yet, and no arbitrary scorer callback is invoked by these additions.

**Existing exactly-once limitation:** `OutcomeProcessor.process` in `copilot_sdk/outcome/processor.py` checks its ledger, applies learning, then appends the receipt, using a process-local lock. A crash before append or separate processor instances can repeat learning. The ledger's unique receipt identity alone does not make the scorer side effect crash-atomic. That behavior was deliberately not changed in this protocol-only task. End-to-end exactly-once learning must not be claimed until SH-06 adapters implement and test the new atomic contract.

### Confinement

Temporal credit is `reward * discount**delay`, proportionally scaled when its sum exceeds `reward * chain_budget` (default chain budget 0.5). Invalid or duplicate causal entries are rejected explicitly rather than silently credited. Results are proposals to put in `learning_effect`; no scorer or ledger is mutated.

Exploration is `epsilon_firm_star * (1 - min(1, consumed_budget / allowed_budget))`, with `epsilon_firm_star <= 0.125`. A snapshot must explicitly be valid, GREEN, unpaused, category-matched, and supported by sufficient evidence, with valid budgets. Missing/invalid data, RED, and AMBER return zero. Freshness/evidence validation is supplied by the governance caller. The returned admission proposal is neither an action replacement nor an atomic reservation of concurrent exploration budget.

## Intentional exclusions

- Domain reward interpretation and SOC RL engine behavior remain in their repositories.
- No scorer, investigation code, outcome processor, app router, domain adapter, or graph implementation was changed.
- No automatic adoption of the new receipt or budget; per-copilot SH-06 wiring is separate.
- No claim that the complete RL SDK design orchestration, AGE/SQLite atomic receipt adapters, or learning transaction migration has shipped.

## Backward compatibility validation

Targeted contract plus existing RL/outcome tests: **80 passed** (35 new contract cases).

| Command | Result | Duration |
|---|---|---|
| `python -m pytest tests/ -q --timeout=120` | 3,486 passed, 11 failed, 5 skipped; diagnosis and follow-up below | 1,111.01 s |
| `python -m pytest apps/trading/backend/tests/ -q --timeout=60` | 1,452 passed | 371.81 s |
| `python -m pytest apps/purchasing/backend/tests/ -q --timeout=60` | 827 passed, 1 skipped | 557.04 s |
| `python -m pytest apps/dataops/backend/tests/ -q --timeout=60` | 412 passed | 199.03 s |

App suites were run in separate processes to preserve their independent `app` import namespaces. Their existing deprecation/runtime warnings are not failures. Purchasing's skipped case is `test_purchasing_active_age_live.py:31`, reason **AGE is not reachable**, confirmed with a focused `-rs` run. Live Purchasing AGE compatibility is therefore not established by this run.

The full SDK run was **not green**:

1. One failure was introduced here: mypy inferred a variable-length tuple for the new reward range. Fixed by explicitly unpacking the two bounds. Follow-up `python -m pytest tests/test_type_checking.py tests/rl/test_shared_control_contract.py -q --timeout=120`: **38 passed**, including the complete existing type-checking module and all 35 new contract cases (31.01 s).
2. Ten failures in `tests/test_vld_integration.py` share an independent fixture-loader error. `tests/vld_validation_report.py:102` calls `ast.literal_eval` on DataOps `gated_sources`, but `apps/dataops/backend/app/main.py:961` contains `{"schema_registry", "dependency_graph", *CONNECTOR_GATED_SOURCES}`. `literal_eval` cannot evaluate `ast.Starred`. A standard-library-only reproduction, explicitly confirming that no `copilot_sdk` module was imported, raises the same error. Neither affected file was edited in this extraction. No skip, monkeypatch, or source rewrite was added to hide these failures.

The SDK totals above are the actual full-run totals, not recomputed after the focused fix. The full suite was not repeated after the type-only correction. A final focused VLD run (`python -m pytest tests/test_vld_integration.py -q -rs --tb=short --timeout=120`) confirms **10 failed, 22 passed, 5 skipped** in 30.07 s. All ten failures and all five skips stem from the same DataOps AST parsing error. Thus the new contracts/typecheck pass, while the requested whole-SDK green gate remains unmet for this independent issue.

Shared imports pass for both GraphStore paths, legacy `RewardFunction`, new `OutcomeReceipt`, and `CompoundingScorer`. The requested `from copilot_sdk.scoring import ProfileScorer` check fails because that name was not exported before this task; the existing public scorer API is `CompoundingScorer`. The internal import `from copilot_sdk.scoring.scorer import ProfileScorer` succeeds and refers to GAE's class. No unrelated alias was introduced to disguise that pre-existing package-export mismatch.

Frozen source hashes were captured before edits and rechecked after all suites and follow-ups: **MATCH for all three**. The prompt's `copilot_sdk/investigation/...` paths do not exist; the actual files are in `scoring/` and `backend/`.

| File | SHA-256 before and after | Result |
|---|---|---|
| `copilot_sdk/scoring/scorer.py` | `24ac9e49a070e0f9421fa0e3e7417a828c0ec88610ef906ce4987311c721b460` | MATCH |
| `copilot_sdk/scoring/investigation.py` | `3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4` | MATCH |
| `copilot_sdk/backend/investigation_router.py` | `08f4df7ad872a6cf0dc53c0bd7250fe854ca7481e508aa592b35fe06440a744b` | MATCH |

## Frozen Twin / TIER-7 convergence

The shared execution plan specifies immutable manifest/hash, restart-safe storage, replay and diff for Frozen Twin (`docs/design/copilot_addenda/cross_platform_execution_plan.md`, Shared build decisions). Existing v2 checkpoints carry identity, domain, geometry, factor hash, quality-window metadata and decision links. Memory and SQLite stores reject conflicting checkpoint reuse (`memory_store.py:844`, `sqlite_store.py:1842`).

The new receipt uses the same conceptual boundary: stable identity, immutable payload, content hash and conflict rejection. TIER-7 can link receipt provenance to a frozen checkpoint without changing the authoritative scorer. This is interface convergence, not completion of a Frozen Twin replay/drift implementation; legacy `save_centroids` alone is not an immutability guarantee.
