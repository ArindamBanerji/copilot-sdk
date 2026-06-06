# GraphStore Factory Design Plan

Date: 2026-06-01

## Purpose

This plan defines how the SDK and copilots should eventually choose between the
local SQLite GraphStore and the canonical PostgreSQL+AGE GraphStore without
changing runtime behavior prematurely.

The factory is a coordination layer, not a migration by itself. Its first
implementation must preserve existing SQLite defaults, keep app-specific data
paths intact, and add explicit AGE opt-in with hard safety guards. S2P AGE
shadow and cutover remain separate later gates.

The first implementation slice is intentionally narrower than app adoption. It
may add the factory module and unit tests, but it must not rewire Trading,
Purchasing, DataOps, S2P, demo.py, or `CompoundingScorer.from_preset` unless a
later prompt explicitly scopes a no-behavior-change adoption slice.

## Gate status

- AGE Protocol v2 adapter completion gate: closed.
- SOC projection gate: PASS_WITH_P3 after live read-only projection tests
  passed with 8 passed, 3 skipped, 0 xfailed, and 0 failed.
- GraphStore factory design: allowed.
- GraphStore factory implementation: blocked pending this design review.
- S2P AGE shadow design: allowed.
- S2P AGE shadow implementation: blocked.
- S2P AGE migration: blocked.

## Current construction inventory

### copilot-sdk core scorer

`copilot_sdk/scoring/scorer.py`

- `CompoundingScorer.from_preset(domain, db_path=None, graph_store=None, ...)`
  creates `SQLiteGraphStore(db_path, domain=preset.name)` when `graph_store` is
  not supplied.
- If `db_path` is not supplied, it resolves through `CI_DATA_DIR` to
  `<CI_DATA_DIR>/<domain>.db`; otherwise it uses the caller-supplied path.
- Risk: medium. This is a broad default path used by tests and simple SDK
  callers. Factory adoption here must preserve the SQLite default exactly.

### copilot-sdk Trading app

`apps/trading/backend/app/main.py`

- Domain: `trading`.
- Current store: `SQLiteGraphStore(str(db_path), domain="trading",
  decision_id_prefix="TRD-")`.
- Path behavior: `_resolve_scoring_db()` uses explicit `db_path`, then
  `CI_DATA_DIR / "trading.db"`, then the app data directory.
- Store is passed through `FreshScorerProxy` and router factory lambdas.
- Risk: medium. Store creation is centralized in `_graph_store`, so later
  factory adoption is straightforward if default behavior remains SQLite.

### copilot-sdk Purchasing app

`apps/purchasing/backend/app/main.py`

- Domain: `purchasing`.
- Current store: `SQLiteGraphStore(str(db_path), domain="purchasing",
  decision_id_prefix="PUR-")`.
- Path behavior: `_resolve_scoring_db()` uses explicit `db_path`, then
  `CI_DATA_DIR / "purchasing.db"`, then the app data directory.
- Store is passed through `FreshScorerProxy` and router factory lambdas.
- Risk: medium. Same adoption pattern as Trading.

### copilot-sdk DataOps app

`apps/dataops/backend/app/main.py`

- Domain: `dataops`.
- Current store: `SQLiteGraphStore(str(db_path), domain="dataops",
  decision_id_prefix="DOPS-")`.
- Path behavior: `_resolve_scoring_db()` uses explicit `db_path`, then
  `CI_DATA_DIR / "dataops.db"`, then the app data directory.
- The app also has DataOps-specific graph query integrations and demo graph mode
  wiring outside the Protocol v2 GraphStore path.
- Risk: high. DataOps already has graph-adjacent behavior, so factory adoption
  must not conflate Protocol v2 AGE writes with legacy/demo DataOps graph mode.

### s2p-copilot backend

`s2p-copilot/backend/app/main.py`

- Domain: `s2p`.
- Current store: `SQLiteGraphStore(effective, domain="s2p",
  decision_id_prefix="S2P-")` inside `build_s2p_scorer`.
- Path behavior: module-level `DATA_DIR` uses `CI_DATA_DIR` or
  `backend/app/data`, and the app creates `DATA_DIR / "s2p.db"` at import time.
- The scorer is created at module import and stored on `app.state`.
- Risk: high. This is the future shadow/cutover target. Factory adoption must
  not switch S2P to AGE until a separate S2P AGE shadow design is reviewed.

### s2p-copilot demo

`s2p-copilot/backend/demo/s2p_demo.py`

- Current store: in-memory SQLite with domain `s2p` and prefix `S2P-DEMO-`.
- Risk: low. Demo should stay SQLite unless a future demo-specific AGE story is
  explicitly designed.

### copilot-sdk demo launcher

`copilot-sdk/demo.py`

- Passes `CI_DATA_DIR` to backend processes and lets each backend choose its own
  database filename.
- Has existing AGE/SOC/DataOps graph-mode helpers that are not the Protocol v2
  GraphStore factory.
- Risk: high for accidental behavior drift. Factory implementation must not
  change demo defaults or reuse demo graph-mode DSNs as app write targets.

### ci-platform AGE adapter

`ci_platform/graph/age_sdk_adapter.py`

- `AGEGraphStoreAdapter(dsn, graph_name)` wraps `AGEGraphStore`.
- `dsn` is required when a store is not injected.
- Current default `graph_name` is `soc_graph`; a factory must not inherit this
  default for non-SOC writes.

`ci_platform/graph/age_client.py`

- Legacy AGE env names include `DATABASE_URL`, `AGE_GRAPH_NAME`, and
  `GRAPH_BACKEND`.
- `AGEClient` defaults can point at `soc_graph`; a factory must require explicit
  graph name for AGE and reject unsafe names before constructing the adapter.

### Tests

- Protocol v2 conformance tests instantiate Memory, SQLite, and AGE adapters
  directly.
- Scoring tests instantiate `CompoundingScorer.from_preset` and direct
  `SQLiteGraphStore` instances.
- Existing tests should keep direct construction where they test store behavior.
- Factory tests should be additive and must not force all test fixtures through
  the factory.
- `CompoundingScorer.from_preset` should not call the factory in the first
  implementation. Factory use should start at app composition boundaries or in
  dedicated factory unit tests, because scorer-internal backend selection would
  change a broad SDK default path.

## Proposed factory API

Proposed location for the first implementation:

- `copilot_sdk/graph/factory.py`

The public export from `copilot_sdk.graph` should be added only after the
factory implementation is reviewed. The first implementation can keep imports
explicit to avoid broad API claims.

Proposed API:

```python
def create_graph_store(
    *,
    domain: str,
    db_path: str | Path | None = None,
    decision_id_prefix: str = "",
    backend: str | None = None,
    dsn: str | None = None,
    graph_name: str | None = None,
    app_name: str | None = None,
    read_only: bool = False,
    allow_soc_graph: bool = False,
    env: Mapping[str, str] | None = None,
) -> GraphStore:
    ...
```

API rules:

- `domain` is required. The factory must not silently infer a write domain from
  `app_name`, `GRAPH_DOMAIN`, DSN, graph name, or current working directory.
- `GRAPH_DOMAIN`, if supplied through `env` or process env, is validation-only in
  the first implementation. If it is present and differs from `domain`, raise
  `ValueError`.
- `db_path` is explicit for SQLite. The factory may resolve `CI_DATA_DIR /
  f"{domain}.db"` only when `db_path is None`; app adoption should still prefer
  existing app path resolvers in the first no-behavior-change slices.
- `env` is an injectable mapping for tests. Production callers can omit it and
  use `os.environ`.
- The return value is only a `GraphStore` protocol object. The factory should not
  return tuples, backend metadata, or app-specific scorer objects.
- The returned store owns normal `GraphStore.close()` semantics. The factory does
  not wrap or suppress `close()`, and callers that already close stores must
  continue to do so.

Optional follow-up API after the first implementation:

```python
@dataclass(frozen=True)
class GraphStoreFactoryConfig:
    domain: str
    backend: str = "sqlite"
    db_path: str | Path | None = None
    decision_id_prefix: str = ""
    dsn: str | None = None
    graph_name: str | None = None
    app_name: str | None = None
    read_only: bool = False
    allow_soc_graph: bool = False
    env: Mapping[str, str] | None = None
```

The factory returns an object implementing `copilot_sdk.graph.protocol.GraphStore`.
For `backend="sqlite"` it returns `SQLiteGraphStore`. For `backend="age"` it
returns `ci_platform.graph.age_sdk_adapter.AGEGraphStoreAdapter`.

## Environment variables and defaults

Factory-level inputs:

- `GRAPH_BACKEND=sqlite|age`
- `GRAPH_DOMAIN`
- `GRAPH_DSN` or `AGE_DSN`
- `GRAPH_NAME` or `AGE_GRAPH_NAME`
- `CI_DATA_DIR` for SQLite path resolution where the caller asks the factory to
  resolve a default path.

Initial implementation rule:

- Function arguments win over env.
- If `backend` and `GRAPH_BACKEND` are unset, default to `sqlite`.
- `GRAPH_BACKEND=sqlite` preserves current local/test behavior.
- `GRAPH_BACKEND=age` requires explicit DSN and graph name.
- Invalid backend values raise `ValueError`.
- Canonical AGE env names are `GRAPH_DSN` and `GRAPH_NAME`.
- Transitional aliases are `AGE_DSN` and `AGE_GRAPH_NAME`.
- If both canonical and alias env names are present with different values, raise
  `ValueError` instead of choosing silently.
- If a function argument supplies `dsn` or `graph_name`, it overrides env and no
  env conflict is considered for that field.
- `DATABASE_URL` is not a factory input in the first implementation.
- `GRAPH_DOMAIN` does not replace the required `domain` argument. If present and
  different from `domain`, raise `ValueError`.
- The factory should expose a diagnostic string or log line identifying which
  source was used for backend, DSN, graph name, and SQLite path. DSN credentials
  must be redacted.

Compatibility note:

- `DATABASE_URL` is already used by SOC/ci-platform AGE code. The factory should
  not silently consume `DATABASE_URL` for app writes in its first implementation.
  Use `GRAPH_DSN`/`AGE_DSN` or an explicit `dsn` argument to avoid accidentally
  targeting SOC infrastructure.

App-specific overrides may be added later if needed:

- `S2P_GRAPH_BACKEND`
- `TRADING_GRAPH_BACKEND`
- `PURCHASING_GRAPH_BACKEND`
- `DATAOPS_GRAPH_BACKEND`

Those should be design-reviewed before use. The first factory should not require
them.

## SQLite behavior

SQLite remains the default backend.

Rules:

- Existing app path resolvers should continue to own filenames in the first app
  adoption phase.
- If `db_path` is supplied, the factory passes it to `SQLiteGraphStore` exactly.
- If `db_path` is omitted and the factory is asked to resolve a path, it may use
  `CI_DATA_DIR / f"{domain}.db"`; this helper behavior must be covered by tests.
- `decision_id_prefix` is passed through unchanged.
- SQLite mode must not import `ci-platform` or require AGE dependencies.

## AGE behavior and safety guards

AGE is the canonical product direction, but must be explicit opt-in.

Rules for `backend="age"`:

- `dsn` or `GRAPH_DSN`/`AGE_DSN` is required.
- `graph_name` or `GRAPH_NAME`/`AGE_GRAPH_NAME` is required.
- Blank graph names are rejected.
- `soc_graph` is rejected for non-SOC app writes.
- The generic app factory must not be the SOC projection fixture. `soc_graph`
  may be allowed only when the caller is explicitly read-only and passes
  `read_only=True` and `allow_soc_graph=True`; any future SOC runtime use needs
  its own reviewed prompt. This permission is never valid for S2P, Trading,
  Purchasing, or DataOps writes.
- Protocol v2 test graphs must start with `protocol_v2_test` when the caller is
  running test-mode AGE construction.
- Product graph names must not start with `protocol_v2_test`.
- Product graph names must be explicit and reviewed before use.
- The first factory implementation should not define a product graph allow-list;
  it should reject known unsafe names and require explicit graph names. Product
  graph allow-listing belongs in a later runtime cutover plan.
- The selected backend, domain, and graph name should be logged. DSN credentials
  must not be logged.
- Import failure for `ci_platform.graph.age_sdk_adapter` should raise a clear
  error explaining that AGE backend requires the sibling package/dependency.

The factory must not call `domain_scoped_reset`, archive, migration helpers, SOC
projection helpers, or any setup that mutates `soc_graph`.

## Domain isolation

The domain string remains the primary GraphStore partition key.

Initial domain mapping:

- S2P: `s2p`, prefix `S2P-`.
- Trading: `trading`, prefix `TRD-`.
- Purchasing: `purchasing`, prefix `PUR-`.
- DataOps: `dataops`, prefix `DOPS-`.
- SOC projection: `soc`, read-only only in this factory phase.

Rules:

- Factory callers must pass `domain`; the factory should not infer it from app
  names unless a reviewed app wrapper does so.
- Domain values for app writes are stable lowercase constants:
  `s2p`, `trading`, `purchasing`, and `dataops`.
- SOC write behavior is not part of the first factory implementation. SOC
  read-only projection remains owned by the SOC projection fixture.
- `count_decisions` and `count_verified_decisions` remain domain-scoped.
- SOC projection remains separate from app writes.
- AGE app writes must not target `soc_graph`.
- Cross-domain transfer/projection work remains outside the factory.

## Rollback strategy

Rollback is environment-level first:

- Set `GRAPH_BACKEND=sqlite` or unset `GRAPH_BACKEND`.
- Keep existing SQLite data paths intact.
- Do not delete AGE data during rollback.
- Do not auto-copy AGE data back to SQLite.

Split-brain controls:

- Before shadow mode, only one active write backend is allowed per app runtime.
- Shadow writes, dual writes, replay, and reconciliation require a separate S2P
  AGE shadow design.
- Factory adoption must not switch only scoring while conservation, evidence,
  audit, or evolution routes keep another store. App-level adoption must route
  every GraphStore consumer for that app through the same selected store factory.
- AGE data written during future shadow mode is retained for audit and parity
  analysis. Rollback to SQLite must not delete or rewrite AGE data.
- Cutover requires a parity report that compares Decision count, active V,
  Outcome status, EvidenceReceipt chain integrity, archive behavior, and reset
  guard behavior for the target domain.
- Backend selection diagnostics should report backend, domain, SQLite path or AGE
  graph name, and whether read-only mode is active.

## Test strategy

Factory unit tests before app adoption:

- `test_graphstore_factory_defaults_to_sqlite_when_backend_unset`.
- `test_graphstore_factory_sqlite_uses_explicit_db_path`.
- `test_graphstore_factory_sqlite_can_resolve_ci_data_dir`.
- `test_graphstore_factory_rejects_invalid_backend`.
- `test_graphstore_factory_age_requires_dsn`.
- `test_graphstore_factory_age_requires_graph_name`.
- `test_graphstore_factory_age_rejects_blank_graph_name`.
- `test_graphstore_factory_age_rejects_soc_graph_for_non_soc_write`.
- `test_graphstore_factory_age_allows_soc_graph_only_read_only_explicit`.
- `test_graphstore_factory_age_import_error_is_clear`.
- `test_graphstore_factory_graph_dsn_alias_conflict_raises`.
- `test_graphstore_factory_graph_name_alias_conflict_raises`.
- `test_graphstore_factory_graph_domain_conflict_raises`.
- `test_graphstore_factory_explicit_args_override_env`.
- `test_graphstore_factory_does_not_read_database_url`.
- `test_graphstore_factory_returns_graphstore_protocol`.
- `test_graphstore_factory_close_delegates_to_store`.

App default-behavior tests before AGE app opt-in:

- Trading `create_app()` still uses SQLite by default and respects `CI_DATA_DIR`.
- Purchasing `create_app()` still uses SQLite by default and respects
  `CI_DATA_DIR`.
- DataOps `create_app()` still uses SQLite by default and does not conflate demo
  graph mode with Protocol v2 AGE writes.
- S2P `build_s2p_scorer()` still uses SQLite by default and respects the caller
  path.
- Existing graph and scoring tests pass unchanged.

Validation commands for the implementation slice:

```powershell
python -m pytest tests/graph/test_protocol_v2_conformance.py -q --timeout=120
python -m pytest tests/graph/test_soc_age_projection_contract.py -q --timeout=120 -rs
python -m pytest tests/graph -q --timeout=120
python -m pytest tests/scoring -q --timeout=120
```

Live AGE/SOC tests should remain explicit and env-guarded. They are not required
for a SQLite-default factory unit slice unless AGE backend construction is
activated in the test.

## Migration sequence

Phase A: Factory design/review.

- Create and review this plan.
- No runtime code changes.

Phase B: Factory implementation with SQLite default only.

- Add `copilot_sdk/graph/factory.py`.
- Add unit tests for default SQLite behavior and AGE guard validation.
- Do not switch any app to AGE.
- Do not change `CompoundingScorer.from_preset`.
- Do not change Trading, Purchasing, DataOps, S2P, or demo.py construction sites.

Phase C: No-behavior-change app adoption.

- Optionally update one app at a time to call the factory while leaving
  `GRAPH_BACKEND` unset in default runs.
- Prove app tests and graph/scoring tests pass unchanged.

Phase D: S2P AGE shadow design.

- Design shadow write/read behavior, diagnostics, rollback, and reconciliation.
- Do not implement shadow mode during factory implementation.

Phase E: S2P AGE shadow implementation.

- Explicit opt-in only.
- No cutover claim.

Phase F: S2P AGE cutover.

- Only after shadow parity, replay/reconciliation, operational runbook, and
  review.

Phase G: Trading, Purchasing, and DataOps AGE planning.

- Later domain-specific rollout.
- DataOps requires extra care because of existing graph-mode code and
  DataOps/SOC partition semantics.

Phase H: Cross-copilot proof.

- Prove governed live judgment-memory graph behavior across copilots.

Blocked phases:

- GraphStore factory implementation is blocked until this design is reviewed.
- S2P AGE shadow implementation is blocked until shadow design is reviewed.
- S2P AGE migration remains blocked.

## SOC projection interaction

SOC projection gate status is PASS_WITH_P3.

Resolved for read-only projection compatibility:

- FactorVector names/schema projection from ordered `SOC_FACTORS`.
- DataQualityAlert / PipelineSystem deny-by-default partition safety.

Deferred SOC items:

- Outcome double-count/backfill.
- `TRIGGERED_EVOLUTION` forward writes.
- ShadowDecision-to-Observation mapping.
- SOC route migration/canonicalization.

These deferred items do not block GraphStore factory design. They do block SOC
canonical route migration claims and may affect future SOC runtime factory use.
The factory must not treat SOC projection read-only permission as permission for
S2P or SDK app writes to `soc_graph`.

## Risks and mitigations

Risk: accidental AGE writes to `soc_graph`.

- Mitigation: reject `soc_graph` unless `read_only=True` and
  `allow_soc_graph=True`.

Risk: default behavior drift in apps/tests.

- Mitigation: SQLite default when `GRAPH_BACKEND` is unset and app tests that
  prove `CI_DATA_DIR` behavior remains unchanged.

Risk: split-brain between SQLite and AGE.

- Mitigation: factory supports one active write backend only; shadow/dual-write
  behavior is a separate design.

Risk: `ci-platform` import coupling.

- Mitigation: import AGE adapter lazily only when `backend="age"` and raise a
  clear error if unavailable.

Risk: S2P module-import construction makes env-driven switches hard to reason
about.

- Mitigation: do not switch S2P in the factory implementation slice; require
  S2P shadow design before runtime AGE opt-in.

Risk: demo graph mode env names conflict with factory env names.

- Mitigation: document and test factory env names separately; do not reuse demo
  DataOps graph mode as Protocol v2 app write configuration.

## Implementation prompt outline

Next implementation prompt scope after this plan is reviewed:

- Add `copilot_sdk/graph/factory.py`.
- Implement `create_graph_store(...)` with SQLite default and AGE guard
  validation.
- Add factory unit tests only.
- Do not update app runtime construction.
- Do not update `CompoundingScorer.from_preset`.
- Do not implement S2P AGE shadow mode.
- Do not switch any app to AGE.
- Do not mutate `soc_graph`.
- Do not change SOC routes, production routes, frontend, Playwright, factory/SOC
  projection beyond this factory module, or migration code.

## Open questions

- Should the factory be exported from `copilot_sdk.graph` immediately or kept as
  `copilot_sdk.graph.factory.create_graph_store` until app adoption?
- What product AGE graph names are allowed for non-test writes?
- Should `CompoundingScorer.from_preset` eventually call the factory when
  `graph_store` is omitted, or should factory use stay at app composition
  boundaries?
- How should backend-selection diagnostics be surfaced in FastAPI health/status
  responses without leaking DSN credentials?
- Should app-specific backend env overrides be introduced during app adoption,
  or should app composition keep passing explicit factory arguments?
