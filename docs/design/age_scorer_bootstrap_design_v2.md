# AGE Scorer Bootstrap Design

## A. Current State

Trading, Purchasing, and DataOps construct a `CompoundingScorer` from their
domain preset and a graph store selected by `GraphConfig` / `create_graph_store`.
Their main modules still retain `db_path` and scoring database plumbing for
legacy startup, scoring-router compatibility, and test configuration.
`from_preset()` already accepts a GraphStore, loads its latest centroids, and
rejects incompatible factor-schema checkpoints. Decisions are already written
and read through `GraphStore`; the remaining startup gap is that verified
decision history is not replayed to reconstruct learning statistics.

S2P is split into its own repository. `build_s2p_scorer` receives a graph store,
the main module assigns the same object to `app.state.graph_store`, and routers
use `S2PGraphReader` for domain-bound GraphStore reads. Its learn route keeps
the `_ContextualRewardFunction` bridge and a lock around the live learning path.
Its graph contract already defines `Decision`, `Invoice`, supplier, category,
factor, and process nodes; `seed_graph.py` creates graph-shaped demo fixtures.

SOC is the reference implementation. `gae_state.init_learning_state()` loads
the shared AGE config, constructs a typed graph store, wraps it in the SOC
`GraphStoreAdapter`, and passes it to `SOCCompoundingScorerAdapter`. The adapter
delegates GraphStore calls to AGE while retaining SOC's legacy graph client for
query consumers. SOC persists learning/posterior state in AGE and restores it
at startup.

`scripts/preseed_all_copilots.py` currently performs HTTP score/learn calls.
It creates hundreds of calls, depends on mutable conservation gates and demo
mode, and has required timeout increases (10 to 30 seconds). It is unsuitable
as durable state initialization. The CI Platform `seed_dataops_graph.py` and
SOC graph-schema seed path demonstrate the desired direct, explicitly scoped
AGE writer pattern.

## B. Target Architecture

Extend `CompoundingScorer.from_preset()`'s existing graph path. It already
accepts `graph_store`, loads compatible centroids with
`load_latest_centroids()`, validates factor-schema hashes, and uses
`InMemoryGraphStore` when no store is supplied. The missing step is verified
decision replay: after centroid loading, call `get_verified_decisions(domain)`
and replay rows through the scorer's existing update semantics to rehydrate
learning counts and posterior state. Do not add a separate `from_graph()`
constructor; that would duplicate more than one hundred lines of existing
preset, profile, GraphStore, centroid, and RL wiring.

Application startup obtains one GraphStore, calls the extended `from_preset()`
with it, then publishes that same instance as `app.state.graph_store` and
`scorer.graph_store`.

Replace HTTP preseeding with `seed_all_decisions.py`, a direct GraphStore/AGE
writer. It writes governed decisions and outcomes in deterministic order and
can save an optional explicit centroid checkpoint. It bypasses no conservation
logic because it is controlled graph initialization, not simulated analyst
traffic. Tests use `InMemoryGraphStore` with the identical writer and bootstrap
contract, requiring neither SQLite nor HTTP.

S2P retains its graph-contract and reward bridge. Its main module calls the
same SDK bootstrap only after creating its S2P active graph store; score and
learn locking remain unchanged. SOC keeps `gae_state` and its adapter, but may
adopt the shared `from_preset()` replay internals once its adapter provides the same preset inputs.

## C. GraphStore Decision Schema

The required bootstrap input is already present in the protocol:

| Scorer need | GraphStore source |
| --- | --- |
| domain/category/action/confidence | `write_decision` fields; `get_all_decisions` rows |
| factor vector/names and source context | decision `factors` plus metadata / governed-decision fields |
| analyst result and correctness | `write_outcome`; `get_verified_decisions` rows |
| current tensor state | `load_latest_centroids(domain)` |
| durable updated tensor state | `save_centroids(domain, category, centroids, metadata)` |

Legacy `DecisionStore` columns map directly to a decision's category, action,
confidence, factors/vector, timestamp and metadata; outcome columns map to
`actual_action`, `is_correct`, verification time and override metadata. A
bootstrap implementation must normalize old dictionary shapes once in the SDK,
not in each copilot.

No required GraphStore method is missing. A compatibility check should reject a
checkpoint with a mismatched domain, tensor shape, action order, or factor-name
hash and then replay verified rows. Empty stores return a cold scorer with the
preset centroids and explicit cold-start state. S2P's graph contract already
has Decision nodes and `DECIDED_ON` / factor links. SOC's adapter maps GraphStore
operations to its typed AGE adapter and preserves its legacy client separately.

## D. Migration Path

1. **SDK graph bootstrap.** Change `copilot_sdk/scoring/scorer.py` and tests.
   Extend the existing `from_preset()` graph path with deterministic verified-
   row replay; retain existing checkpoint loading and validation. Affects all
   SDK domains and S2P; moderate risk because replay must not duplicate writes.
   Estimated delta: +8-12 tests (empty store, checkpoint load, incompatible
   checkpoint, verified replay, replay idempotency), 0 broken.

2. **Direct seed writer.** Add `scripts/seed_all_decisions.py` plus domain seed
   adapters using `copilot_sdk/graph/protocol.py`; use CI Platform's explicit
   AGE target/authorization pattern. Affects Trading, Purchasing, DataOps and
   S2P; SOC may retain `graph_schema.seed_graph`. Low runtime risk, high
   operational-value improvement. Depends on step 1 only for verification.
   Estimated delta: +5-8 tests (per-domain seed writer, idempotency), 0 broken.

3. **Startup wiring.** Update `apps/trading/backend/app/main.py`,
   `apps/purchasing/backend/app/main.py`, `apps/dataops/backend/app/main.py`,
   and `../s2p-copilot/backend/app/main.py` to create GraphStore first and
   call the extended `from_preset()`. Preserve S2P's contextual reward bridge and reader.
   SOC only receives an integration assessment, not adapter internals. Depends
   on step 1; moderate compatibility risk. Estimated delta: +4 tests (one per
   copilot startup wiring), 0 broken.

4. **Retire HTTP preseed.** Deprecate then remove calls to
   `scripts/preseed_all_copilots.py`; retain a temporary wrapper that points to
   the direct writer with a deprecation warning. Remove `COPILOT_PRESEED_MODE`
   from runtime bootstrap after release evidence. Depends on steps 2-3.
   Estimated delta: 0 new tests; remove roughly 3-5 preseed test fixtures.

5. **Migrate tests.** Replace HTTP setup with direct `InMemoryGraphStore`
   seeding in SDK/app tests; retain narrow API tests only for API behavior.
   Add cross-store conformance tests showing AGE-shaped and memory-shaped rows
   produce equal scorer state. Depends on all earlier steps. Estimated delta:
   +6-10 cross-store conformance tests; migrate roughly 10-15 existing tests
   from HTTP/SQLite setup to `InMemoryGraphStore`.

## E. Standing Rules

Rule #33 is preserved because conservation reads verified outcomes from the
live GraphStore; seeds are initialization data, not static conservation state.
Rule #35 is strengthened: scorer decisions, outcomes, and centroids share one
storage abstraction. Rule #21 is met because extending `from_preset()` is a
first-class scorer bootstrap path, not an HTTP bypass. Rule #6 is met because it removes the
preseed ceremony's source of timeouts and gate coupling. Rule #88 remains
unchanged: SQLite is not part of scorer persistence; any permitted outbox use
stays confined to `persistence_outbox.py`.

## F. What Not to Change

Do not add required GraphStore protocol methods, modify AGEClient transport,
alter conservation or reward mathematics, change SOC adapter internals, or
modify S2P's `_ContextualRewardFunction`. This design changes scorer startup
and controlled seeding only.

## G. Open Questions

1. Keep `from_preset` as a backwards-compatible convenience wrapper until all
   external callers migrate; decide deprecation after adoption telemetry.
2. Seed raw decisions/outcomes by default. Seed centroids only as an explicit,
   versioned checkpoint after parity validation.
3. Define cold AGE behavior: production should surface a declared cold-start
   state; test/demo profiles may use an authorized deterministic direct seed.
4. Confirm whether SOC should call the shared `from_preset()` replay internals or retain
   `gae_state` as the SOC-specific lifecycle wrapper around the same logic.
5. Prefer one shared writer with per-domain seed modules so schema conversion
   stays local while authorization, idempotency, and reporting stay uniform.
