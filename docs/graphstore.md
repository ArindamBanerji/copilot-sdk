# GraphStore

`GraphStore` is the SDK persistence protocol for decisions, outcomes, centroids, and graph-memory records.

## Core Protocol Methods

The core decision and learning contract includes these methods:

1. `write_decision(domain, category, action, confidence, factors, metadata=None) -> str`
2. `write_outcome(decision_id, actual_action, is_correct, metadata=None) -> None`
3. `get_decision(decision_id) -> dict | None`
4. `get_decisions(domain, category=None, limit=400) -> list[dict]`
5. `get_all_decisions(domain) -> list[dict]`
6. `get_verified_decisions(domain) -> list[dict]`
7. `count_verified(domain) -> int`
8. `count_correct(domain) -> int`
9. `count_decisions(domain) -> int`
10. `save_centroids(domain, category, centroids, metadata=None, **kwargs) -> None`
11. `load_latest_centroids(domain) -> Any | None`

Additional lifecycle and memory methods include:

- `get_centroid_checkpoints(...)`
- `archive_old_decisions(...)`
- `count_archived(...)`
- `close()`
- entity enrichment reads and writes

## Implementations

| Implementation | Module | Use |
|---|---|---|
| `SQLiteGraphStore` | `copilot_sdk.graph.sqlite_store` | Default file-based persistence |
| `InMemoryGraphStore` | `copilot_sdk.graph.memory_store` | Tests, demos, ephemeral runs |
| AGE-backed adapter | `ci-platform` integration | SOC production graph on PostgreSQL + AGE |

## Backend Selection

Applications commonly use a `GRAPH_BACKEND` environment variable:

| Value | Meaning |
|---|---|
| `sqlite` | File-backed SQLite store, default for SDK-local apps |
| `age` | PostgreSQL + AGE graph backend through adapter |
| `memory` | Ephemeral in-memory store for tests or demos |

The SDK factory defaults to SQLite unless an application explicitly opts into AGE or memory.

## SQLite Rules

- Rule #58: no raw `sqlite3` outside the migration/storage module.
- Rule #62: migration source of truth is the home DB under `~/.ci-platform/<domain>/`.
- Domain-scoped reset and migration logic should stay in the store layer.

## Decision Persistence

Scoring calls write decisions through `write_decision`. Learning calls write verified outcomes through `write_outcome`.

Typical flow:

```text
score() -> write_decision()
learn() -> write_outcome() -> centroid/conservation updates
```

## L5 Persistence

L5 persistence uses the graph store for:

- centroids
- DK weights
- conservation state
- centroid checkpoints
- decision/entity links
- evidence receipts and outbox records

The scorer should not treat memory-only state as the source of truth once a graph store is available.
