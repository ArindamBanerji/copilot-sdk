# RL Persistence Notes

## Purpose

RL-WIRE attached reward, credit, and exploration components through
`CompoundingScorer.from_preset()`.
RL-PERSIST gives the Thompson exploration posterior a concrete persistence path.
The goal is to preserve learned `alpha` and `beta` priors across scorer restarts.
The change is deliberately narrow and does not alter score generation.

## Why Posterior Persistence Matters

`ConservationBoundedThompson` updates action priors after feedback.
Without persistence, those priors reset whenever a scorer or process restarts.
Persisting the posterior lets supported stores retain exploration learning.
The persisted state is advisory RL state, not centroid state.
It should not be mixed with checkpoint history or exported as a trajectory.

## Dedicated RL State Storage

RL state uses a dedicated `rl_state` table in `SQLiteGraphStore`.
This avoids piggybacking on centroid checkpoint metadata.
Centroid checkpoints are append-oriented and represent scorer geometry over time.
Thompson priors are mutable state keyed by domain and state name.
They need an upsert model rather than an append-only checkpoint model.

## Concrete Store Only

Persistence was added to concrete stores only:

- `SQLiteGraphStore.save_rl_state(key, data)`
- `SQLiteGraphStore.load_rl_state(key)`
- `InMemoryGraphStore.save_rl_state(key, data)`
- `InMemoryGraphStore.load_rl_state(key)`

`GraphStore` Protocol is intentionally unchanged.
RL code discovers persistence by checking for concrete `load_rl_state` and
`save_rl_state` methods.
Stores without those methods continue to work as no-persistence stores.

## SQLite Schema

The SQLite table is:

```sql
CREATE TABLE IF NOT EXISTS rl_state (
    domain TEXT NOT NULL,
    key TEXT NOT NULL,
    data_json TEXT NOT NULL,
    updated_at REAL NOT NULL,
    PRIMARY KEY (domain, key)
);
```

The `domain` column scopes state to the store domain.
The `key` column identifies a state object such as `thompson_posteriors`.
The `data_json` column stores a JSON blob.
The `updated_at` column stores a real timestamp.
The primary key supports upsert by `(domain, key)`.

## Thompson Persistence

`ConservationBoundedThompson` now accepts optional `graph_store`.
No-store construction remains compatible with existing code.
On construction, it attempts to load `thompson_posteriors`.
The expected data shape matches `get_priors()`:

- `alpha`
- `beta`
- `conservation_status`

If stored `alpha` or `beta` values are corrupt or have the wrong length,
the policy falls back to uniform priors.
If persisted conservation status is missing or invalid, status remains `GREEN`.
After each successful `update()`, the policy attempts to persist `get_priors()`.
Persistence exceptions are swallowed so learning is never blocked by optional
RL-state storage.

## InMemory Store Behavior

`InMemoryGraphStore` stores RL state in an internal `(domain, key)` dictionary.
It deep-copies data on save and load, matching existing in-memory store patterns.
`reset()` clears RL state along with decisions, outcomes, checkpoints, and
evolution events.

## CreditAssigner Store Awareness

`CreditAssigner` now accepts optional `graph_store`.
It stores the reference but does not use it yet.
The current `assign()` behavior remains math-only and unchanged.
No `TRIGGERED_EVOLUTION` graph traversal was added.
Graph-backed chain credit remains future work.

## RL Presets

`get_rl_components()` now passes `graph_store` to:

- `CreditAssigner`
- `ConservationBoundedThompson`

This lets `CompoundingScorer.from_preset()` provide store-aware RL components
without changing scorer call sites.
The registry now includes:

- `trading -> PnLRewardFunction`
- `purchasing -> WasteReductionRewardFunction`
- `dataops -> GradedFinancialRewardFunction`
- `s2p -> GradedFinancialRewardFunction`

S2P was added because the SDK has a local `S2PPreset` with shape `(5, 5, 7)`
and a financial recovered/at-risk reward function can be instantiated and tested.

## exploration_used

`LearnResult.exploration_used` remains `False`.
Current scorer runtime does not use Thompson sampling to choose an alternate
action in the decision path.
It only updates Thompson posterior state after feedback.
Posterior update is not the same as exploration being used for a decision.
True exploration-use tracking is deferred until a real exploration/propose path
exists in scorer runtime.

## Tests

RL persistence tests cover:

- empty-store default priors
- posterior accumulation
- persistence roundtrip
- save failure non-blocking behavior
- wrong-size state fallback
- stores without RL methods
- no-store behavior
- CreditAssigner math with and without store
- preset graph_store propagation
- S2P reward mapping
- `exploration_used` remaining false for posterior-only updates

Graph tests cover:

- SQLite RL state roundtrip
- SQLite missing state
- SQLite upsert behavior
- SQLite domain isolation
- in-memory roundtrip and upsert
- in-memory domain isolation
- in-memory copy safety
- reset clearing RL state
- GraphStore Protocol remains free of RL methods

## Validation

The expected validation set is:

- `python -m pytest tests/graph/test_sqlite_store.py -v --timeout=120`
- `python -m pytest tests/rl/ -q --timeout=120`
- `python -m pytest tests/scoring/test_scorer.py -q --timeout=120`
- `python -m pytest tests/ -q --timeout=120`
- app backend regressions for Trading, Purchasing, and DataOps
- protocol cleanliness check for `GraphStore`
- docs line-count check

## Files Changed

- `copilot_sdk/graph/sqlite_store.py`
- `copilot_sdk/graph/memory_store.py`
- `copilot_sdk/rl/exploration.py`
- `copilot_sdk/rl/credit.py`
- `copilot_sdk/rl/presets.py`
- `tests/graph/test_sqlite_store.py`
- `tests/graph/test_memory_store.py`
- `tests/rl/test_rl_persistence.py`
- `tests/rl/test_presets.py`
- `tests/rl/test_rl_wiring.py`
- `docs/rl_persistence_notes.md`

## Intentionally Unchanged

- `copilot_sdk/graph/protocol.py`
- `copilot_sdk/rl/reward_functions.py`
- `copilot_sdk/rl/reward.py`
- `copilot_sdk/evolution/**`
- `copilot_sdk/backend/**`
- app backends
- frontend and package lock files

## Residual Risks

Thompson persistence is concrete-store only by design.
External graph store implementations will not persist RL state unless they add
compatible concrete `save_rl_state` and `load_rl_state` methods.
Credit assignment is store-aware but does not yet perform graph traversal.
`exploration_used` remains false until runtime exploration selection exists.
