# GraphStore Consolidation Plan

## 1. Executive Summary

The current graph-store architecture is close to the desired shape but still has fragmentation at the capability boundary.

Evidence:
- `copilot_sdk.graph.protocol.GraphStore` is `@runtime_checkable` and currently requires the core persistence methods through `save_evolution_event` and `close` (`copilot_sdk/graph/protocol.py:8-77`).
- `SupportsDecisionEntityLinks` is a separate bolt-on runtime protocol with only `link_decision_to_entity` (`copilot_sdk/graph/protocol.py:79-90`).
- `SQLiteGraphStore` implements core GraphStore plus `link_decision_to_entity` and `get_decision_links` (`copilot_sdk/graph/sqlite_store.py:14-231`).
- `InMemoryGraphStore` implements core GraphStore plus `link_decision_to_entity`, `get_decision_links`, and `reset` (`copilot_sdk/graph/memory_store.py:12-171`).
- `AGEGraphStore` implements the core GraphStore protocol plus AGE-specific query helpers, but does not implement decision-entity link read/write methods (`ci_platform/graph/age_graph_store.py:15-335`).
- `AGEGraphStoreAdapter` is a one-to-one delegating wrapper around `AGEGraphStore` and does not add behavior (`ci_platform/graph/age_sdk_adapter.py:10-111`).
- S2P has a private `_S2PGraphStore` subclass whose only purpose is preserving the public `S2P-` decision-id prefix (`s2p-copilot/backend/app/main.py:42-58`).

Target architecture:
- Exactly three canonical concrete GraphStore implementations:
  - `SQLiteGraphStore` in `copilot-sdk`.
  - `InMemoryGraphStore` in `copilot-sdk`.
  - `AGEGraphStore` in `ci-platform`.
- S2P uses a canonical SDK store with a supported decision-id prefix mechanism instead of a private GraphStore subclass.
- Entity link methods become regular optional methods on canonical concrete stores, but are not required by the runtime `GraphStore` protocol until old-shape compatibility can be retired.
- `SupportsDecisionEntityLinks` is deprecated first, then removed after consumers migrate away from importing it.

Selected approach: **Approach 2 - narrow protocol plus wide implementations**.

Why:
- It preserves existing runtime structural compatibility. A compatibility script showed that a store with the old core method set and no entity-link methods still returns `old-shape structural isinstance: True` for `GraphStore`.
- It avoids adding required members to `@runtime_checkable GraphStore`, which would break old-shape structural stores.
- It still lets canonical stores converge on a wider concrete API.
- It has a smaller blast radius than a base-class migration and avoids protocol churn while S2P and ci-platform consolidate.

## 2. Current Inventory

### Protocols and Exports

| Item | Location | Classification | Evidence |
| --- | --- | --- | --- |
| `GraphStore` | `copilot_sdk/graph/protocol.py` | Canonical public runtime protocol | Runtime checkable at lines 8-9; required methods lines 12-77 |
| `SupportsDecisionEntityLinks` | `copilot_sdk/graph/protocol.py` | Duplicate/bolt-on capability protocol | Runtime checkable at lines 79-90 |
| SDK graph exports | `copilot_sdk/graph/__init__.py` | Public SDK export surface | Exports `GraphStore`, `InMemoryGraphStore`, `SQLiteGraphStore` at lines 3-15 |

### Implementations and Adapters

| Item | Location | Classification | Evidence |
| --- | --- | --- | --- |
| `SQLiteGraphStore` | `copilot_sdk/graph/sqlite_store.py` | Canonical SDK persistent store | Class at line 14; core methods and entity links through line 231 |
| `InMemoryGraphStore` | `copilot_sdk/graph/memory_store.py` | Canonical SDK test/demo store | Class at line 12; dictionaries/lists initialized at lines 15-21 |
| `AGEGraphStore` | `ci_platform/graph/age_graph_store.py` | Canonical AGE store | Class at line 15; wraps `AGEClient` at line 19 |
| `AGEGraphStoreAdapter` | `ci_platform/graph/age_sdk_adapter.py` | Transitional adapter | Delegates to `AGEGraphStore`; constructor at lines 10-23; methods through line 111 |
| `_S2PGraphStore` | `s2p-copilot/backend/app/main.py` | Private duplicate subclass | Subclasses `InMemoryGraphStore` at line 42; only overrides `write_decision` at lines 45-58 |
| `DemoGraphStore` | `copilot-sdk/scripts/evolve_demo.py` | Demo-only subclass | Search found subclass of `InMemoryGraphStore` at line 19 |
| Test fakes | SDK, S2P, ci-platform tests | Test-only stores | Search found `MinimalGraphStore`, `FakeGraphStore`, and recording stores in tests |

### Method Coverage Matrix

| Method | SDK GraphStore | SQLiteGraphStore | InMemoryGraphStore | AGEGraphStore | AGEGraphStoreAdapter | _S2PGraphStore |
| --- | --- | --- | --- | --- | --- | --- |
| `write_decision` | Required | Yes | Yes | Yes | Delegates | Overrides for prefix, then delegates |
| `write_outcome` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `get_decision` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `get_decisions` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `get_verified_decisions` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `count_verified` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `count_correct` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `get_all_decisions` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `save_centroids` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `get_centroid_checkpoints` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `save_evolution_event` | Required | Yes | Yes | Yes | Delegates | Inherited |
| `link_decision_to_entity` | Not required; bolt-on protocol | Yes | Yes | No | No | Inherited |
| `get_decision_links` | Not in protocol | Yes | Yes | No | No | Inherited |
| `query_context` | Not in protocol | No | No | Yes | No | No |
| `query_similar` | Not in protocol | No | No | Yes | No | No |
| `reset` | Not in protocol | No | Yes | No | No | Inherited |
| `close` | Required | Yes | Yes | Yes | Delegates | Inherited |

## 3. Runtime Structural Compatibility

Current status:
- `GraphStore` is `@runtime_checkable` (`copilot_sdk/graph/protocol.py:8-9`).
- `SupportsDecisionEntityLinks` is also `@runtime_checkable` (`copilot_sdk/graph/protocol.py:79-80`).
- Existing tests explicitly protect old-shape structural compatibility: `tests/test_graph_entity_links.py:190-194` asserts a minimal old store still satisfies `GraphStore` while lacking `link_decision_to_entity`.

Compatibility result:
- The requested compatibility script returned `old-shape structural isinstance: True`.
- Therefore, adding `link_decision_to_entity` or `get_decision_links` as required members to `GraphStore` would be a breaking change for existing structural stores.

Preservation rule:
- Keep `GraphStore` narrow and do not add required entity-link methods to it in the first implementation wave.
- Add entity-link methods to canonical concrete stores where missing.
- Keep scorer-side capability checks as `getattr` against method names on the concrete object, which is already the pattern in `CompoundingScorer.learn` (`copilot_sdk/scoring/scorer.py:282-285`).

## 4. Target Architecture

Canonical implementations:
1. `copilot_sdk.graph.SQLiteGraphStore`
2. `copilot_sdk.graph.InMemoryGraphStore`
3. `ci_platform.graph.AGEGraphStore`

Adapter decision:
- Keep `AGEGraphStoreAdapter` for one release as a compatibility shim because it is exported from `ci_platform.graph.__init__` (`ci_platform/graph/__init__.py:10-13`) and covered by dedicated tests (`ci-platform/tests/test_age_sdk_adapter.py:80-224`).
- Mark it as deprecated in docs and tests after `AGEGraphStore` reaches direct SDK parity, including entity links.
- Do not rename it in the implementation wave; public rename/removal is deferred.

Elimination plan for `SupportsDecisionEntityLinks`:
- Phase 1: Keep it out of the package `__all__` export surface (`copilot_sdk/graph/__init__.py:8-15`) and stop recommending direct imports in new docs; keep the protocol available for backwards compatibility.
- Phase 2: Add tests proving `SQLiteGraphStore`, `InMemoryGraphStore`, and `AGEGraphStore` expose `link_decision_to_entity` and `get_decision_links`.
- Phase 3: Remove internal imports/usages of `SupportsDecisionEntityLinks` if any appear. Current search found its definition and test references, not production consumers.
- Phase 4: Deprecate the protocol in release notes. Remove only after external compatibility policy allows it.

## 5. Selected Design Approach

### Approach 1 - Base class

Description:
- Introduce a concrete or abstract base class with no-op/default implementations.

Pros:
- Shared default behavior can reduce duplication.

Cons:
- Structural stores currently rely on protocol duck typing, not inheritance.
- Requiring a base class would break third-party or repo-local structural stores.
- It introduces migration work in SDK, ci-platform, and S2P at once.

Decision: reject for this consolidation wave.

### Approach 2 - Narrow protocol plus wide implementations

Description:
- Keep `GraphStore` as the core runtime structural contract.
- Ensure all canonical concrete stores implement the wider operational method set.
- Use optional method discovery for capabilities not in the runtime protocol.

Pros:
- Preserves old-shape structural compatibility.
- Matches the existing `CompoundingScorer.learn` optional link behavior (`copilot_sdk/scoring/scorer.py:282-285`).
- Lets S2P remove its private subclass by using canonical store configuration instead of protocol changes.
- Smallest cross-repo blast radius.

Cons:
- Static typing does not force every optional method.
- Tests must enforce canonical implementation parity.

Decision: **selected**.

### Approach 3 - Two protocols

Description:
- Keep `GraphStore` and introduce a second `GraphStoreWithLinks` or `FullGraphStore`.

Pros:
- Makes optional link capability explicit.

Cons:
- The repo already has a second protocol, `SupportsDecisionEntityLinks`, and this would preserve fragmentation rather than consolidate it.
- It risks another partial adoption path.

Decision: reject as a long-term target. A temporary protocol can remain only as deprecated compatibility.

## 6. SDK Implementation Plan

### `copilot_sdk/graph/protocol.py`

Plan:
- Keep `GraphStore` unchanged in the first implementation wave.
- Keep `SupportsDecisionEntityLinks` available but annotate/document it as deprecated.
- Do not add `get_decision_links` or `link_decision_to_entity` to `GraphStore` yet.

Tests:
- Keep `tests/test_graph_entity_links.py:190-194` or equivalent old-shape compatibility test.
- Add a test asserting old-shape stores without link methods still satisfy `GraphStore`.
- Add a test asserting `SupportsDecisionEntityLinks` is no longer needed by SDK production code.

### `copilot_sdk/graph/sqlite_store.py`

Plan:
- Keep current link support: `link_decision_to_entity` at `sqlite_store.py:169-192` and `get_decision_links` at `sqlite_store.py:194-219`.
- Add/adjust tests that prove links round-trip and use fresh SQLite rows.
- Do not change `DecisionStore` schema beyond existing `decision_entity_edges` helper unless migration tests require it.

### `copilot_sdk/graph/memory_store.py`

Plan:
- Keep current in-memory edge support: `_edges` initialized at line 18; link/write methods at lines 132-153.
- Add parity tests against SQLite link behavior.
- Ensure `reset` continues clearing edges at lines 155-161.

### `copilot_sdk/scoring/scorer.py`

Plan:
- Keep `getattr(self._graph_store, "link_decision_to_entity", None)` behavior at lines 282-285.
- Do not require entity-link support through the `GraphStore` type.
- If desired, add a small helper like `_link_decision_to_entity_if_supported(...)` to centralize optional capability behavior, but this is optional.

Tests:
- Existing tests already cover old stores without link method (`tests/test_graph_entity_links.py:197-205`).
- Add canonical-store link tests to prove SDK stores link invoice ids during `learn`.

## 7. ci-platform Implementation Plan

### `ci_platform/graph/age_graph_store.py`

Plan:
- Add `link_decision_to_entity(decision_id, entity_id, edge_type="DECIDED_ON")`.
- Add `get_decision_links(decision_id: str | None = None)`.
- Use AGE-safe Cypher patterns:
  - no `MERGE`;
  - no `$param` named parameters;
  - serialize values with `_S`, already exposed via `_S` at lines 39-40;
  - use `CREATE` for relationships, matching current `write_decision` style at lines 75-77.
- Prefer matching `Decision` by `decision_id` and entity by `entity_id`, with fallback behavior consistent with `write_decision`: if no entity exists, either create a standalone link record node or no-op with documented behavior. The plan preference is a `DecisionEntityLink` node if relationship creation cannot match both endpoints, because `get_decision_links` must still return evidence that the link was requested.
- Preserve `AGEGraphStore` core SDK protocol signatures, which ci-platform currently tests against SDK `GraphStore` (`ci-platform/tests/test_age_graph_store.py:94-134`).

Tests:
- Unit tests with fake AGE client for link creation query shape and no `MERGE`.
- Unit tests for `get_decision_links()` and `get_decision_links(decision_id)`.
- Direct SDK compatibility test proving `AGEGraphStore` still satisfies `GraphStore`.

### `ci_platform/graph/age_sdk_adapter.py`

Decision:
- Keep in place for one compatibility cycle.
- Add delegating `link_decision_to_entity` and `get_decision_links` only after `AGEGraphStore` has those methods.
- Mark as transitional/deprecated in docstring or docs, not removed.

Why:
- It is exported publicly (`ci_platform/graph/__init__.py:10-13`).
- Tests exercise import/export, protocol parity, delegation, and live behavior (`ci-platform/tests/test_age_sdk_adapter.py:80-277`).

## 8. S2P Implementation Plan

Current behavior:
- S2P imports `InMemoryGraphStore` and `CompoundingScorer` in `app/main.py:8-9`.
- `_S2PGraphStore` subclasses `InMemoryGraphStore` only to force a `S2P-` prefix into metadata decision ids (`app/main.py:42-58`).
- `build_s2p_scorer` injects `_S2PGraphStore()` into `CompoundingScorer.from_preset` (`app/main.py:61-67`).
- `app.state.graph_store` is assigned from `app.state.scorer.graph_store` (`app/main.py:70-71`).

Plan:
- Add a canonical SDK-supported decision-id prefix option to `InMemoryGraphStore`, for example `InMemoryGraphStore(decision_id_prefix="S2P-")`.
- Preserve default behavior when no prefix is supplied.
- Replace `_S2PGraphStore()` with `InMemoryGraphStore(decision_id_prefix="S2P-")`.
- Remove the private `_S2PGraphStore` class after tests prove public decision ids and metadata stay stable.
- Do not move S2P to SQLite in this wave. Existing S2P app uses `db_path=":memory:"` and an in-memory graph store (`app/main.py:62-65`), so changing persistence would be a behavior change.

Tests:
- S2P score endpoint still returns `decision_id` starting with `S2P-`.
- S2P outcome path can read the prefixed decision from `graph_store`.
- `app.state.graph_store` remains the same object as `app.state.scorer.graph_store`.
- S2P conservation router still uses the scorer graph store via `state_provider=lambda: app.state.scorer.graph_store` (`app/main.py:83-86`).

## 9. S2P Helper Consolidation Plan

Current duplicate/helper state:
- Shared helper module exists at `app/routers/s2p_data_helpers.py`, with `load_json`, `load_invoices`, and `load_suppliers` (`s2p_data_helpers.py:10-26`).
- `s2p_control_tower.py` imports `load_invoices`, but defines a local `_find_invoice` at lines 63-67.
- `s2p_insight.py` imports shared loaders, but defines local `_load_json` and `_find_invoice` at lines 31-43.
- `s2p_pvg.py` imports `load_invoices`, but defines local `_load_json` at lines 36-40.
- Canonical current `_find_invoice` behavior in `s2p.py` matches both `invoice_id` and `event_id`, skipping non-dict records (`s2p.py:36-44`).

Plan:
- Move canonical invoice lookup into `s2p_data_helpers.py`:
  - `find_invoice(event_id_or_invoice_id: str) -> dict[str, Any] | None`
  - iterate over `load_invoices()`;
  - skip non-dicts defensively;
  - match `invoice_id` first, then `event_id`, preserving `s2p.py:36-44`.
- Replace local `_find_invoice` helpers in `s2p.py`, `s2p_control_tower.py`, and `s2p_insight.py` with imports from `s2p_data_helpers.py`.
- Replace local JSON helpers only when they read files under the same `data` directory and have identical fallback semantics. Keep specialized Celonis candidate-path logic in router-local code if it is not identical.

Tests:
- Unit test for `find_invoice` by `invoice_id`.
- Unit test for `find_invoice` by `event_id`.
- Endpoint tests for score, control tower classify, insight summary, and similar invoices.

## 10. DataOps Fixture Cache Plan

Current read pattern:
- `ae_router._load_json` reads and parses `DATA_DIR / name` on every call (`apps/dataops/backend/app/ae_router.py:66-71`).
- `_variants()` calls `_load_json("evolution_fixtures.json", {"variants": []})` (`ae_router.py:82-90`).
- Recommendation and pattern-origin endpoints also read `evolution_fixtures.json` directly through `_load_json` (`ae_router.py:290` and `352`).
- AE endpoints preserve fixture source reporting in two forms: recommendation responses pass through `alert_payload.get("source", "fixture")` (`ae_router.py:285`, `312`), while pattern/lifecycle fixture endpoints return literal `"source": "fixture"` (`ae_router.py:378`, `420`, `436`).

Plan:
- Add a small module-local fixture cache in `ae_router.py`, for example `_JSON_CACHE: dict[str, Any]`.
- Implement `reset_ae_fixture_cache()` for tests and reload behavior.
- `_load_json` should cache successful parsed payloads by filename and return the same data shape as today.
- Endpoints must continue returning `"source": "fixture"` exactly where they do now.
- Tests should use `reset_ae_fixture_cache()` after monkeypatching `DATA_DIR`, because existing DataOps tests monkeypatch `ae_router.DATA_DIR` in `apps/dataops/backend/tests/conftest.py:53-58`.

Tests:
- `_load_json` reads a fixture once across repeated calls.
- `reset_ae_fixture_cache()` forces reload from changed `DATA_DIR`.
- `/api/ae/rule-lifecycle`, `/api/ae/pattern-origin`, and recommendation endpoints still report source fixture and same payload shape.

## 11. Architectural Adherence Checks

ARCH-1: Protocol compatibility
- `GraphStore` remains runtime-checkable and old-shape structural stores still pass.
- No required entity-link members are added to `GraphStore` in the first wave.

ARCH-2: Canonical implementation count
- Only three production concrete GraphStores remain after S2P cleanup: SDK SQLite, SDK InMemory, ci-platform AGE.
- `_S2PGraphStore` is removed.

ARCH-3: Optional link capability
- Link methods are implemented on canonical stores but discovered optionally by callers.
- `SupportsDecisionEntityLinks` is deprecated, not expanded.

ARCH-4: Adapter containment
- `AGEGraphStoreAdapter` remains only as a compatibility shim and delegates all behavior.
- New behavior belongs in `AGEGraphStore`, not the adapter.

ARCH-5: S2P domain isolation
- S2P continues to use S2P preset/config/reward only.
- No SOC imports or SOC tensor constants are introduced.

ARCH-6: DataOps fixture behavior
- Caching does not alter response source fields or fixture fallback behavior.
- Cache reset is test-visible.

ARCH-7: Graph/store persistence safety
- AGE changes use `AGEClient` and its `_S` serialization path.
- No AGE `MERGE` or named `$param` syntax is introduced.

ARCH-8: Review gate
- Before implementation, run a GPT-5.5 architecture review on this plan.
- After implementation, run a GPT-5.5 review for line-by-line and architecture/system integrity.

## 12. Test Plan

SDK:
- `tests/graph/test_protocol.py`: prove `GraphStore` required methods are unchanged.
- `tests/test_graph_entity_links.py`: preserve old-shape structural compatibility and learn-without-link behavior.
- `tests/graph/test_graph_store_links.py` or existing link tests: prove SQLite and InMemory link write/read parity.
- `tests/scoring/...`: prove `CompoundingScorer.learn` links invoice ids when link support exists and tolerates missing support.

ci-platform:
- `tests/test_age_graph_store.py`: add link method presence, signature, query-shape, and read behavior tests.
- `tests/test_age_sdk_adapter.py`: add adapter delegation tests if adapter gains link methods.
- Existing protocol signature tests must still pass.

S2P:
- `backend/tests/test_s2p_score_endpoint.py`: preserve `S2P-` decision ids and graph context behavior.
- Tests around outcome/learn path: verify prefixed decisions are retrievable and learnable.
- Helper tests for `find_invoice` matching `invoice_id` and `event_id`.
- Endpoint tests for control tower and insight routes after helper import consolidation.

DataOps:
- `apps/dataops/backend/tests/test_dataops_backend.py`: preserve AE endpoint source/payload behavior.
- Add cache/reset tests around `ae_router._load_json` or public cache helper.
- Ensure tests that monkeypatch `ae_router.DATA_DIR` call reset before assertions.

Cross-repo architecture:
- Test that SDK does not import S2P/SOC app modules.
- Test that S2P does not define a production `class .*GraphStore`.
- Test that ci-platform `AGEGraphStore` has direct SDK parity without requiring adapter use.

## 13. Validation Commands

SDK:
```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python -m pytest tests/ -q --timeout=120
python -m pytest apps\dataops\backend\tests\ -q --timeout=120
```

S2P:
```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend"
python -m pytest tests/ -q --timeout=120
```

ci-platform:
```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform"
python -m pytest tests/ -q --timeout=120
```

Compatibility:
```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python "$env:TEMP\_graphstore_compat.py"
```

## 14. Risks / Deferred Follow-ups

AGEGraphStoreAdapter purpose:
- Purpose is currently compatibility/export/delegation, not behavior. Removing it immediately would break public exports and tests. Keep for one release.

External old-shape stores:
- Runtime compatibility is proven for a local minimal old store. External stores may exist, so `GraphStore` must stay narrow until a deprecation window completes.

S2P canonical store behavior:
- The private `_S2PGraphStore` only preserves a public decision-id prefix. The replacement must prove `S2P-` IDs and metadata are identical before removing the subclass.

DataOps cache invalidation:
- Fixture caching can make monkeypatched test data stale unless a reset function is included and tests use it.

Protocol deprecation:
- Do not remove `SupportsDecisionEntityLinks` in the same wave that adds AGE link methods. Deprecate first, remove later.

## Baseline Results

- SDK tests: `489 passed, 978 warnings`.
- DataOps backend tests: `129 passed, 258 warnings`.
- S2P backend tests: `394 passed, 790 warnings`; pytest cache write warnings occurred under the repo-root `.pytest_cache`.
- ci-platform tests: `244 passed, 11 skipped, 510 warnings`.

## Prompt Verification Pass

1. All GraphStore implementations/adapters inventoried: SDK SQLite, SDK InMemory, ci-platform AGE, ci-platform adapter, S2P private subclass, and test/demo stores.
2. Protocol runtime structural compatibility tested: old-shape store without link methods still satisfies `GraphStore`.
3. S2P private store understood: it only prefixes decision ids before delegating to `InMemoryGraphStore`.
4. Duplicate helper locations known: `s2p.py`, `s2p_control_tower.py`, `s2p_insight.py`, `s2p_pvg.py`, and shared `s2p_data_helpers.py`.
5. DataOps fixture read pattern known: `ae_router._load_json` reads fixture JSON directly and repeatedly.
6. Baselines attempted and passed.
7. Plan does not require SOC or GAE source changes.
8. Plan requires GPT-5.5 architecture review before implementation.
