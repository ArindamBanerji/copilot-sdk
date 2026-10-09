# Persistence rules

DecisionStore is deprecated. Do not add DecisionStore dependencies or revive
`copilot_sdk/scoring/storage.py`. All scoring persistence must use GraphStore
protocol methods. InMemoryGraphStore is the test/development backend; AGE is
the production backend. Do not add SQLiteGraphStore consumers.

SQLite removal is in progress. Existing durable migration/archive consumers
are tracked in `docs/dstore_migration_findings.md`; preserve their data semantics
until migrated. Stage required runtime protocol changes with the AGE adapter.
