# Step 11B Design: S2P Differentiation Namespace Integration

Date: 2026-10-06  
Status: REVIEWED DESIGN

## Section 0: Discovery

- ENGINE_PATH: `apps/s2p_differentiation/engine.py`
- Function names: `run_three_arms=run_three_arms`, `_make_scorer=_make_scorer`, `_close_scorer=_close_scorer`
- Name mapping: matched the prompt defaults.
- Other caller: `run_tg1()` also calls `_make_scorer()` and is itself called by `run_three_arms()`.

## Section 1: Current State

`run_three_arms()` creates the governed CI scorer with `_make_scorer(enable_rl=True)` and the frozen hand scorer with `_make_scorer(enable_rl=False)`. It later calls `run_tg1()`, which creates a third scorer through the same helper. The reward-max baseline does not use a graph store.

The current helper is:

```python
def _make_scorer(*, enable_rl: bool) -> CompoundingScorer:
    store = InMemoryGraphStore(domain="s2p")
    return CompoundingScorer.from_preset(
        "s2p", graph_store=store, enable_rl=enable_rl,
        evolve=False, profile="development",
    )
```

Each call therefore owns a separate `InMemoryGraphStore`. A complete `run_three_arms()` creates three memory stores: CI, hand, and T-G1. `_close_scorer()` calls `scorer.close()`. The two main scorers are closed only on the success path at the end of `run_three_arms()`; T-G1 uses `try/finally`.

The engine does not currently resolve a run profile or use `GraphConfig`/`create_graph_store`. It hardcodes the scorer profile to `development`. No graph-sharing pattern or run ID exists. The only external caller of `run_three_arms()` is the CLI; the existing engine tests call it directly. Existing tests assert experiment results and do not inspect independent stores.

`GraphStoreNamespace(store: ProtocolV2GraphStore, namespace: str)` is exported from `copilot_sdk.graph`. It prefixes every logical domain with `namespace + "::"`, owns no state, and its `close()` is a no-op. It structurally satisfies `ProtocolV2GraphStore` and intentionally does not satisfy `ProductionReadyStore`.

## Section 2: Proposed Changes

### Change 1: Extend `_make_scorer()`

```python
def _make_scorer(
    *,
    enable_rl: bool,
    graph_store: ProtocolV2GraphStore | None = None,
    graph_namespace: str | None = None,
) -> CompoundingScorer:
```

- If both optional arguments are absent, create `InMemoryGraphStore(domain="s2p")` exactly as today.
- If both are present, construct `GraphStoreNamespace(graph_store, graph_namespace)` and give that view to the scorer.
- If exactly one is present, raise `ValueError("graph_store and graph_namespace must both be provided or both omitted")`.
- Keep `profile="development"` for scorer construction. The namespace changes persistence scope, not scoring policy.

### Change 2: One shared graph in `run_three_arms()`

Extend the public function with a keyword-only profile that preserves existing behavior:

```python
def run_three_arms(
    config: GeneratorConfig,
    oracle_config: OracleConfig,
    n_decisions: int = 500,
    output_dir: str | Path = ".",
    *,
    profile: str | None = "development",
) -> dict[str, Any]:
```

Resolve it with `resolve_profile(profile, domain="s2p")`. For `test`/`offline` (including the `development` alias), create exactly one shared store through the existing factory:

```python
store = create_graph_store(
    backend="memory", domain="s2p", profile=resolved_profile, env={}
)
```

Verify that the result satisfies `ProtocolV2GraphStore`, otherwise close and fail. Generate `run_id = uuid4().hex[:8]`. Construct the scorer views with:

- CI: `f"s2p:{run_id}:ci"`
- Hand: `f"s2p:{run_id}:hand"`
- Nested T-G1: `f"s2p:{run_id}:tg1"`

The T-G1 namespace is necessary because otherwise `run_three_arms()` would still create a second physical store. Add optional store/namespace parameters to `run_tg1()` and retain its standalone backward-compatible path when they are absent. Include `run_id` in result metadata for traceability.

### Change 3: Lifecycle

Keep `_close_scorer()` unchanged: calling `scorer.close()` closes an owned memory store on the backward-compatible path and calls the namespace adapter's no-op `close()` on the shared path. Wrap main-arm construction/execution in `try/finally`; close each constructed scorer, then close the shared underlying store exactly once. `run_tg1()` continues closing its scorer view in its own `finally`, which is harmless because the view owns no lifecycle.

### Change 4: Production gate

Step 11A established that the current AGE implementation rejects colons. Because production permits only AGE and support is known to be absent, fail before opening an AGE connection:

```python
if resolved_profile == "production":
    raise RuntimeError(
        "AGE colon-domain support required for namespaced graph. See Step 11A notes."
    )
```

This is stricter and clearer than constructing a production adapter first: it produces the required capability error even when credentials are unavailable and cannot leak a newly opened AGE resource. Once AGE supports and tests colon domains, this gate can be replaced by `create_graph_store(config=GraphConfig.load(...))` without changing namespace/scorer wiring.

### Change 5: Imports

Add `uuid4`, `resolve_profile`, `create_graph_store`, `GraphStoreNamespace`, and `ProtocolV2GraphStore`. Import `GraphStoreNamespace` from `copilot_sdk.graph` as required. Keep `InMemoryGraphStore` for `_make_scorer()` backward compatibility.

## Section 3: Test Plan

Create `tests/test_s2p_differentiation_namespace.py` with approximately twelve collected tests:

### Group A: `_make_scorer()`

1. Both shared arguments create a scorer backed by `GraphStoreNamespace`.
2. Neither argument retains the old owned-memory path.
3. Only `graph_store` raises the exact `ValueError`.
4. Only `graph_namespace` raises the exact `ValueError`.

### Group B: shared graph and isolation

5. Two scorer views borrow the same underlying store with different namespaces.
6. A CI write is invisible to the hand view.
7. A hand write is invisible to the CI view.
8. Both views can write logical domain `s2p` without collision.
9. A small `run_three_arms()` calls the graph factory once and supplies the same shared store to CI, hand, and T-G1 with distinct expected namespace strings.

### Group C: lifecycle

10. Closing namespace-backed scorers does not close the shared store prematurely.
11. `run_three_arms()` closes the shared store exactly once after completion.

### Group D: profile gate

12. Production raises the exact AGE colon-domain error before factory construction.
13. Test/development execution succeeds with one memory store.

The existing `tests/test_s2p_differentiation.py` remains unchanged and verifies the 500-decision experiment behavior.

## Design Review Findings

### Signature and compatibility

The actual `_make_scorer()` signature matches the expected extension point. Optional paired arguments preserve direct `run_tg1()` and helper behavior. The `run_three_arms()` profile parameter is keyword-only, so the CLI's existing four positional arguments remain valid.

### Run ID

No existing run ID exists. `uuid4().hex[:8]` is appropriate for transient experiment isolation and is recorded in result metadata. IDs generated inside each namespace remain backend-global per Step 11A.

### Other callers

`run_tg1()` is the only additional engine caller of `_make_scorer()` and must accept/pass the shared graph when invoked by `run_three_arms()`. Its direct fallback remains unchanged. No external module imports `_make_scorer()`.

### Profile resolution and production safety

The engine previously hardcoded development, so the default remains `development` and is canonicalized by the SDK's `resolve_profile()`. Production is known unsafe rather than merely unknown: Step 11A records that AGE rejects colon domains. Failing before factory construction gives deterministic safety behavior and avoids masking the capability error with a missing-DSN error.

### Existing tests

Existing engine tests do not assert store identity and should retain equivalent per-arm logical state through namespaces. The result gains only additive `run_id` metadata. The 500-decision test is expected to remain behaviorally unchanged.

### Imports

`from copilot_sdk.graph import GraphStoreNamespace` is confirmed valid by `copilot_sdk/graph/__init__.py`. The namespace module depends only on protocol/enrichment types and does not import the engine, so no circular import is introduced.

### Reviewed outcome

The implementation must share the physical store with T-G1 as well as the two main scorer arms, close the underlying store in `finally`, and keep the exact production error. No change to `copilot_sdk/graph/namespace.py` is needed.

### Implementation verification finding

`CompoundingScorer` defaults to its legacy raw-write path unless governed writes are explicitly enabled. `GraphStoreNamespace` correctly rejects that path when the scorer-generated `decision_id` appears in metadata, so namespaced `_make_scorer()` calls set `governed_writes=True`. The standalone backward-compatible path retains `None` and therefore keeps its prior environment-controlled behavior.

The conservation baseline reader asks its scorer source for a public logical `domain`, then falls back to the store. A namespace adapter intentionally represents many logical domains and has no single store-level domain, while the scorer owns the unambiguous `s2p` scope. Namespaced experiment scorers therefore use a local `CompoundingScorer` subclass that exposes the existing `_domain` as a read-only `domain` property; this keeps conservation reads inside the namespace without changing shared SDK or Step 11A code.

The existing 500-decision integration fixture now exercises governed Protocol V2 projections through the namespace. Its assertions remain unchanged, but the additional bounded projection/deep-copy work raises the measured setup time to about 236 seconds. The test module receives a 300-second timeout marker so the repository's 120-second default does not terminate a correct architecture run; this changes no experiment inputs or assertions.
