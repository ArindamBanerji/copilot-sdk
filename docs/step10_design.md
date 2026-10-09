# Step 10 Design: AGE Protocol Enforcement

Date: 2026-10-06  
Status: REVIEWED DESIGN

## Current state

The graph factory accepts only `memory` and `age`. It resolves configuration through `GraphConfig`, requires the shared graph for production, and calls `validate_production_store()` for a factory-created production AGE store. The application composition roots can still receive stores from their active-store factories, however, and do not currently validate the final store assigned to `app.state.graph_store` against both production protocols.

| Copilot | Store creation | Profile variable | Final graph store variable |
|---|---|---|---|
| Trading | `create_app()` resolves `active_graph_store`, otherwise `_graph_store()` uses `create_graph_store(config=GraphConfig.load(...))`; `FreshScorerProxy` exposes the selected store. | `resolved_profile` | `app.state.graph_store = scorer_proxy.graph_store` and `app.state.trading_selected_graph_store` |
| Purchasing | `create_app()` resolves `active_graph_store`, otherwise `_graph_store()` uses `create_graph_store(config=GraphConfig.load(...))`; `FreshScorerProxy` exposes the selected store through `GateEnforcedScorer`. | `resolved_profile` | `app.state.graph_store = scorer_proxy.graph_store` and `app.state.purchasing_selected_graph_store` |
| DataOps | `create_app()` loads or accepts `graph_config`, then `_selected_graph_store_factory()` chooses the active store or calls `create_graph_store()`. | `graph_config.profile` | `app.state.graph_store = selected_graph_store` and `app.state.dataops_selected_graph_store` |

## Gaps found

1. `validate_production_store()` verifies the factory-created AGE primary and destination, but no reusable application-boundary guard checks the final injected/wrapped store for both `ProductionReadyStore` and `ProtocolV2GraphStore`.
2. The three composition roots assign the final store without a production protocol assertion. Explicit test/offline memory stores must remain valid.
3. `build_graph_health()` identifies AGE through `ProductionReadyStore`, but its response does not state the governed-memory protocol version or expose the production marker as a boolean.
4. Existing health payload consumers use key-based assertions or selected fields. The proposed fields are additive and do not alter existing status, readiness, or HTTP-code semantics.

## Proposed changes

| File | Change | Risk | Rationale |
|---|---|---|---|
| `copilot_sdk/graph/factory.py` | Add `assert_production_graph(store, profile)`. Resolve the profile with the existing `resolve_profile()` function; return outside production; in production require structural membership in both `ProductionReadyStore` and `ProtocolV2GraphStore`, otherwise raise a clear `RuntimeError` naming missing capabilities. | Low | Keeps runtime store enforcement beside factory construction, avoids a config-to-graph import dependency, and catches injected application stores that bypass factory production validation. |
| `copilot_sdk/backend/health_builder.py` | Import `ProtocolV2GraphStore`. Add `protocol_version` (`v2`/`v1`) and `production_ready` (runtime marker membership) for the resolved primary store. Missing stores report `v1` and `False`. | Low | Adds explicit operational evidence without changing existing readiness rules. |
| `apps/trading/backend/app/main.py` | Import `assert_production_graph` beside `create_graph_store`; call it immediately after `app.state.graph_store` is assigned, using `resolved_profile`. | Low | Enforces the contract on the final scorer-owned store while leaving test/offline startup unchanged. |
| `apps/purchasing/backend/app/main.py` | Import `assert_production_graph` beside `create_graph_store`; call it immediately after `app.state.graph_store` is assigned, using `resolved_profile`. | Low | Enforces the contract after the gate/scorer composition has selected its store. |
| `apps/dataops/backend/app/main.py` | Import `assert_production_graph` beside `create_graph_store`; call it immediately after `app.state.graph_store` is assigned, using `graph_config.profile`. | Low | Uses the already validated canonical profile attached to DataOps `GraphConfig`. |
| `tests/test_age_protocol_enforcement.py` | Add focused helper, health-field, wrapper, profile-guard, and three-app source-wiring tests. | Low | Verifies fail-closed production behavior, non-production compatibility, response fields, and all composition-root calls. |

## Health response

Current responses include `graph_backend`, connectivity, readiness, graph identity/status, and cutover evidence. The response will retain those keys and add:

```json
{
  "protocol_version": "v2",
  "production_ready": true
}
```

`protocol_version` is `"v2"` only when the resolved primary satisfies `ProtocolV2GraphStore`; otherwise it is `"v1"`. `production_ready` is the result of `isinstance(primary, ProductionReadyStore)`. These are capability facts and do not replace the live connectivity probe or `ready` calculation.

## Test plan

The new test module will cover approximately fifteen collected cases:

1. A marker-bearing `InMemoryGraphStore` test double satisfies both protocols and passes the production assertion.
2. Production rejects ordinary `InMemoryGraphStore` and reports the missing production marker.
3. Production rejects a marker-only store and reports missing Protocol V2.
4. Production rejects a Protocol V2 memory store without the production marker.
5. Test and offline profiles accept `InMemoryGraphStore` without inspecting production capabilities.
6. The `development` profile alias remains a non-production no-op through canonical profile resolution.
7. Health for `InMemoryGraphStore` reports `v2` and `production_ready=False`.
8. Health for a dual-protocol test double reports `v2` and `production_ready=True`.
9. Health for a minimal plain-store test double reports `v1` and `production_ready=False`.
10. Health for a marker-only store reports `v1` and `production_ready=True`, reflecting structural marker semantics independently from V2.
11. Health with no store reports `v1` and `production_ready=False`.
12. Health follows `GraphStoreWrapper.graph_primary` when classifying both fields.
13. Parameterized source-wiring checks cover Trading, Purchasing, and DataOps imports, immediate assertion calls, and their correct profile expressions.

Existing health tests and app suites remain regression coverage for response compatibility and dev/test startup.

## Design Review Findings

### Circular imports

Placing the helper in `copilot_sdk.graph.factory` introduces no circular import. The factory already imports `GraphStore` and `resolve_profile`; adding the two runtime-checkable protocols stays within the graph layer. Putting it in `copilot_sdk.config` would make configuration depend on graph protocols and would be the riskier direction.

### Profile resolution

The helper will call the same `resolve_profile()` used by the factory. Trading and Purchasing pass their existing normalized `resolved_profile`; DataOps passes `graph_config.profile`, already canonicalized by `GraphConfig.__post_init__` and checked by `create_app()`.

### In-memory tests

The guard returns before capability inspection for `test`, `offline`, and the canonical `development` alias. Existing app fixtures configure test profiles, so their in-memory stores remain valid. Tests that deliberately inject memory under production should now fail closed, which is the required behavior.

### Health compatibility

The health change adds two scalar keys and does not remove or reinterpret existing keys. Existing consumers observed in the repository select individual keys rather than compare the complete dictionary, so the additive change is backward compatible.

### Import blast radius

Many modules import `create_graph_store` from the factory, but adding a named export does not change those imports. Only the three composition roots import the new helper. No `__all__` exists in `factory.py`, so no export list needs modification.

### Reviewed outcome

No design blocker remains. The implementation will keep the helper protocol-only, preserve the factory's existing destination validation, avoid changes to store creation, and enforce the final application store immediately after assignment.
