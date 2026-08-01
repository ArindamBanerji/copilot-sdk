# Fix 6: `soc_graph` Universal Startup Invariant

Status: design-ready; implementation is intentionally not included in this document.

## §1 Executive Summary

The five production configurations already resolve to `soc_graph` in the checked-in configuration: the defaults and all five copilot sections set `graph = "soc_graph"` (`copilot-sdk/graph_config.toml:1-39`). That is configuration evidence, not a runtime invariant. The current runtime has four enforcement weaknesses:

- Trading, Purchasing, and DataOps active graph wrappers authorize `soc_graph`, but also retain reviewed product graph allow-lists (`copilot-sdk/apps/trading/backend/app/graph_status.py:182-205`, `copilot-sdk/apps/purchasing/backend/app/graph_status.py:182-202`, `copilot-sdk/apps/dataops/backend/app/graph_status.py:173-196`).
- S2P has the same non-shared product allow-list (`s2p-copilot/backend/app/s2p_graph_status.py:199-224`).
- Trading and DataOps generic `_graph_store` paths resolve only the backend and omit the resolved DSN/graph from their factory calls (`copilot-sdk/apps/trading/backend/app/main.py:116-133`, `copilot-sdk/apps/dataops/backend/app/main.py:109-126`); Purchasing has the same omission (`copilot-sdk/apps/purchasing/backend/app/main.py:145-164`).
- SOC resolves the graph through a module-level GraphConfig in `db/neo4j.py`, but does not expose a named startup invariant (`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28-53`).

Decision: enforce a shared helper at every production startup boundary, including the active graph configuration validators and SOC’s AGE client boundary. The helper will require `graph == "soc_graph"` only for AGE/dual-write production paths; SQLite, InMemory, development fallback, and explicit disposable test AGE graphs remain available to tests and local tooling. The low-level factory remains flexible for migration and test callers, while every copilot startup passes the resolved graph explicitly and invokes the guard.

This provides continuous runtime enforcement and keeps the batch proof aligned with the same guard. It is a fail-fast `ValueError`/`GraphConfigError` path, not a warning or health-only check.

## §2 Current Graph Name Resolution

### 2.1 Trading

The generic helper loads only `GraphConfig.load("trading").backend` (`copilot-sdk/apps/trading/backend/app/main.py:116-126`) and calls the factory without `dsn` or `graph_name` (`:127-133`). The active path loads `GraphConfig` through `_load_trading_graph_config` and copies `graph_config.graph` into `TradingActiveGraphConfig.graph` (`copilot-sdk/apps/trading/backend/app/graph_status.py:79-109,129-149`). The active factory call does pass `graph_name=config.graph` (`:320-357`).

Trading’s validator treats `soc_graph` as a specially authorized shared graph, but also accepts `governed_copilot_graph` through `ALLOWED_PRODUCT_AGE_GRAPHS` (`copilot-sdk/apps/trading/backend/app/graph_status.py:17-18,182-205`). Test graphs are accepted only in explicit test mode and must begin with `protocol_v2_test` (`:192-200`).

| Copilot | GraphConfig call | Graph source | Passed to factory? | Active wrapper authorizes `soc_graph`? | Fallback omits graph? |
|---|---|---|---|---|---|
| Trading | `main.py:120`; active `graph_status.py:84,109` | `GraphConfig.graph`, copied at `graph_status.py:142-145` | Active: yes at `graph_status.py:351`; generic: no at `main.py:127-133` | Yes, only with `trading:soc_graph` authorization (`:183-190`) | Yes |

### 2.2 Purchasing

Purchasing’s generic helper loads only the backend (`copilot-sdk/apps/purchasing/backend/app/main.py:145-155`) and omits graph/DSN in its factory call (`:156-162`). The active config copies the resolved graph (`copilot-sdk/apps/purchasing/backend/app/graph_status.py:82-108,131-148`) and the active factory forwards it (`:375-386`).

The active validator has the same reviewed product allow-list and shared-graph authorization split as Trading (`copilot-sdk/apps/purchasing/backend/app/graph_status.py:182-202`).

| Copilot | GraphConfig call | Graph source | Passed to factory? | Active wrapper authorizes `soc_graph`? | Fallback omits graph? |
|---|---|---|---|---|---|
| Purchasing | `main.py:150`; active `graph_status.py:85,108` | `GraphConfig.graph`, copied at `graph_status.py:141-144` | Active: yes at `graph_status.py:382`; generic: no at `main.py:156-162` | Yes, only with `purchasing:soc_graph` authorization (`:183-189`) | Yes |

### 2.3 DataOps

DataOps’ generic helper loads only the backend (`copilot-sdk/apps/dataops/backend/app/main.py:109-117`) and omits the graph/DSN in the factory call (`:118-124`). Its active configuration copies the graph (`copilot-sdk/apps/dataops/backend/app/graph_status.py:80-106,127-145`) and the active factory forwards it (`:324-335`).

DataOps permits `governed_copilot_graph` and, additionally, a non-shared live AGE test path (`copilot-sdk/apps/dataops/backend/app/graph_status.py:173-196`). Test graphs are explicitly constrained to `protocol_v2_test*` (`:181-189`).

| Copilot | GraphConfig call | Graph source | Passed to factory? | Active wrapper authorizes `soc_graph`? | Fallback omits graph? |
|---|---|---|---|---|---|
| DataOps | `main.py:113`; active `graph_status.py:83,106` | `GraphConfig.graph`, copied at `graph_status.py:137-144` | Active: yes at `graph_status.py:331`; generic: no at `main.py:118-124` | Yes, only with `dataops:soc_graph` authorization (`:174-180`) | Yes |

### 2.4 S2P

`build_s2p_scorer` loads `GraphConfig.load("s2p", profile=...)` and forwards both `dsn` and `graph_name` (`s2p-copilot/backend/app/main.py:114-126`). The module-level startup path creates the active config, creates the active store, and aliases enrichment to the scorer’s store (`:160-180`), so the shadow/enrichment split is no longer a second production store.

S2P’s active config loads GraphConfig at `s2p_graph_status.py:81-109`, copies `graph_config.graph` at `:164-175`, and forwards `graph_name=config.graph` at `:345-355`. Its validator still accepts `S2P_ALLOWED_PRODUCT_AGE_GRAPHS` in addition to the shared graph (`:199-224`).

| Copilot | GraphConfig call | Graph source | Passed to factory? | Active wrapper authorizes `soc_graph`? | Fallback omits graph? |
|---|---|---|---|---|---|
| S2P | `main.py:115`; `s2p_graph_status.py:84` | `GraphConfig.graph`, copied at `s2p_graph_status.py:164-175` | Yes at `main.py:122` and `s2p_graph_status.py:349` | Yes, with `s2p:soc_graph` authorization (`s2p_graph_status.py:199-209`) | No graph omission found in the selected factory paths |

### 2.5 SOC

SOC resolves `GraphConfig.load("soc")` at module import and stores the result in `_GRAPH_CONFIG` (`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28-31`). The AGE client receives `_GRAPH_CONFIG.dsn` and `_GRAPH_CONFIG.graph` (`:45-53`). `main.py` imports that client during startup (`gen-ai-roi-demo-v4-v50/backend/app/main.py:163-177`) and verifies the graph through the client, but the graph name is not surfaced as a named invariant (`:200-221`).

| Copilot | GraphConfig call | Graph source | Passed to factory? | Active wrapper authorizes `soc_graph`? | Fallback omits graph? |
|---|---|---|---|---|---|
| SOC | `db/neo4j.py:29` | `_GRAPH_CONFIG.graph` at `db/neo4j.py:52-53` | Yes, to AGE client | N/A; direct SOC AGE client | No alternate client path found |

## §3 Authorization Audit

### 3.1 Existing authorization

The generic factory requires explicit shared authorization for `soc_graph`; otherwise it raises at `_validate_age_graph_name` (`copilot-sdk/copilot_sdk/graph/factory.py:99-120,264-285`). Config-driven GraphConfig authorization is populated automatically as `domain:graph` (`copilot-sdk/copilot_sdk/graph/factory.py:147-169`). Dual-write performs the same shared-graph check (`:225-243`). This is a useful low-level safety boundary, but it is not a universal startup invariant because explicit factory callers can still use reviewed non-shared names and because the generic Trading/Purchasing/DataOps fallback calls do not forward their resolved graph.

### 3.2 GraphConfig resolution

GraphConfig’s environment specification maps generic SOC variables and domain-specific active variables to backend, DSN, graph, and domain fields (`copilot-sdk/copilot_sdk/config/graph_config.py:64-99`). The resolved graph is stripped at `:144`, and validation currently requires only a nonblank AGE graph (`:221-240`). The checked-in TOML sets `soc_graph` for defaults and all five copilot sections (`copilot-sdk/graph_config.toml:1-39`), but environment overrides remain possible.

### 3.3 Factory behavior

`create_graph_store` accepts explicit `graph_name` and defaults `profile="production"` (`copilot-sdk/copilot_sdk/graph/factory.py:123-143`). It validates presence and shared authorization but does not impose a universal exact-name rule. This flexibility is retained for migration tooling, read-only projections, disposable AGE graphs, and existing protocol tests.

## §4 Test Graph Isolation

Non-`soc_graph` names are used intentionally in tests and disposable integrations:

- SDK graph fixtures use `protocol_v2_test_<uuid>` (`copilot-sdk/tests/graph/conftest.py:20-34`), and protocol migration tests create `protocol_v2_test_migration_<uuid>` (`copilot-sdk/tests/graph/test_protocol_v2_conformance.py:182-183`).
- SDK factory/unit tests exercise `product_graph`, `age_test`, `dual_write_test`, and explicit graph names (`copilot-sdk/tests/graph/test_graphstore_factory.py:56-120,131-176`; `copilot-sdk/tests/test_factory_dual_write.py:33-157`).
- S2P live tests use `protocol_v2_test_s2p_active_*` (`s2p-copilot/backend/tests/conftest.py:53-68`), and phase-B tests use `protocol_v2_test_cutover*` (`s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py:308-353`). S2P status tests also deliberately exercise `random_product_graph` and `governed_copilot_graph` (`s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py:219-251,281-284`).
- SOC destructive graph tests use `soc_stress_test_<uuid>` (`gen-ai-roi-demo-v4-v50/backend/tests/conftest.py:46-56`).

The invariant therefore applies to copilot production startup only. SQLite and InMemory stores are exempt because they do not connect to the shared AGE graph. AGE test paths are exempt only when an explicit test profile/test-mode flag is active and the graph is a disposable `protocol_v2_test*` graph. Direct low-level factory tests remain unchanged; startup tests must exercise the new guard.

## §5 Invariant Design

### 5.1 Enforcement location

Chosen combination: a shared helper in `copilot_sdk.config.graph_config`, called at every production startup boundary:

1. Trading, Purchasing, and DataOps active graph config validators.
2. S2P active graph config validator and `build_s2p_scorer` GraphConfig path.
3. SOC’s `db/neo4j.py` immediately after loading the SOC GraphConfig.
4. Generic Trading/Purchasing/DataOps `_graph_store` paths after loading the complete GraphConfig, while also forwarding DSN and graph.
5. Phase 6 claim proof, using the same helper before its equality checks.

The helper is preferable to factory-only enforcement because the factory is also a migration/test API, and it is preferable to five independent checks because one message and one exemption policy must govern all copilots. Active validators remain call sites because they are the actual production wrapper boundary and can be constructed independently of FastAPI.

### 5.2 Scope and trigger

The guard fires when:

- backend is `age` or `dual_write`;
- profile is `production`; and
- the path is not explicitly in AGE test mode.

It does not fire for SQLite/InMemory, development profiles, or explicit disposable test mode. The guard requires exact `graph == "soc_graph"`; an extensible allow-list would recreate the current reviewed-product-graph escape hatch.

### 5.3 Failure behavior

Raise `GraphConfigError` (a `ValueError` subclass) with the domain, resolved graph, and required graph in the message. The active wrappers may translate it to their existing domain-specific configuration error at their current boundary. Startup must fail before AGE store/client construction.

### 5.4 Startup forwarding

The generic `_graph_store` helpers will load the complete GraphConfig, retain their existing explicit SQLite test fallback, and pass `dsn=config.dsn` and `graph_name=config.graph` to `create_graph_store`. S2P already forwards both fields (`s2p-copilot/backend/app/main.py:116-125`). SOC already forwards both fields to its AGE client (`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:51-53`).

## §6 Claim Proof Alignment

The proof runner currently loads all five production configs, requires one graph, requires one matching DSN, and creates one AGE store (`copilot-sdk/scripts/phase6_claim_proof.py:176-188`). The implementation will call the shared invariant for each production config before the existing set-equality checks. It will retain the explicit `--graph-name` argument check and will reject any non-`soc_graph` CLI value. Thus the batch proof and runtime startup use the same exact invariant; the proof remains useful as an operational cross-domain check rather than becoming the only enforcement point.

## §7 Blast Radius

| Change | Files affected | Tests affected | Risk |
|---|---|---|---|
| Add shared production AGE graph guard | `copilot_sdk/config/graph_config.py` | GraphConfig tests; new invariant tests | Existing direct `GraphConfig.load` tests with alternate production graphs could fail if the guard is placed inside `load`; therefore the guard is an explicit method, not an unconditional `load` side effect. |
| Enforce active wrapper startup | Trading/Purchasing/DataOps `graph_status.py`, S2P `s2p_graph_status.py` | Active graph status/phase-B tests | Existing product-like tests intentionally assert reviewed alternate graphs; retain those as lower-level policy tests or update them to assert test/development scope, while production startup tests must use `soc_graph`. |
| Forward complete config in generic fallbacks | Trading/Purchasing/DataOps `main.py` | Backend/startup/fallback tests | Test environments that provide only partial generic AGE variables must continue using the existing explicit test fallback; production must fail closed. |
| Surface SOC invariant | SOC `app/db/neo4j.py`, optionally `app/main.py` | SOC startup/config tests | Import-time failure behavior must remain fail-fast; no legacy Neo4j path may be reintroduced. |
| Align Phase 6 runner | `copilot-sdk/scripts/phase6_claim_proof.py` | Claim proof/unit tests | Must preserve dry-run behavior and DSN redaction. |
| Add integration/conformance coverage | `copilot-sdk/tests/test_soc_graph_invariant.py` plus per-app startup tests if needed | New tests only initially | Importing app modules can have startup side effects; prefer direct config/validator tests and subprocess-isolated startup checks. |

The current non-shared graph references are intentional test/tooling references, not all production failures. The primary production blast radius is the three active wrapper validators plus S2P active validation and generic fallback forwarding.

## §8 Design Decisions

| ID | Decision | Rationale |
|---|---|---|
| DD1 | Use a shared helper plus explicit startup-boundary calls; do not impose the exact name in the low-level factory. | Covers all five runtime paths while preserving migration, projection, and disposable AGE test callers. |
| DD2 | Enforce only for AGE and dual-write production paths. | SQLite/InMemory are local/test backends; dual-write still has an AGE graph that must be shared. |
| DD3 | Exempt only explicit test mode/profile and development profile. | Prevents test graph isolation from being confused with production topology; no implicit environment-based bypass. |
| DD4 | Require exact `soc_graph`. | The JM requirement is one named physical graph; the current reviewed allow-list is not a universal invariant. |
| DD5 | Fail fast with `GraphConfigError`/existing wrapper configuration errors. | A warning would permit writes to the wrong graph and invalidate the census. |
| DD6 | Keep the factory’s existing `shared_graph_authorization` check. | It remains a lower-level authorization control and protects direct callers, while the startup guard adds exact-name topology enforcement. |
| DD7 | Update generic fallback calls to pass resolved `dsn` and `graph_name`. | A guard without explicit forwarding would leave configuration provenance incomplete. |
| DD8 | Update Phase 6 proof to invoke the same helper. | Runtime and batch evidence must use identical policy. |
| DD9 | Preserve non-shared test/tool graphs. | Existing protocol and live integration tests require disposable graph isolation; they must use explicit test mode and remain outside production startup. |

No design decision remains unresolved.

## §9 Implementation Plan

### Step 1 — Shared guard

Change `copilot-sdk/copilot_sdk/config/graph_config.py`:

- Add a small public guard (for example `require_shared_graph`) accepting backend, graph, profile, test-mode, and domain.
- Validate nonblank values and exact `soc_graph` only for production AGE/dual-write non-test paths.
- Raise `GraphConfigError` with actionable values.
- Do not change ordinary `GraphConfig.load` semantics or the factory’s explicit graph API.

Tests: positive production `soc_graph`; negative alternate/blank graph; regression SQLite, development, and explicit test-mode exemptions.

### Step 2 — Active validators

Change:

- `copilot-sdk/apps/trading/backend/app/graph_status.py`
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py`
- `copilot-sdk/apps/dataops/backend/app/graph_status.py`
- `s2p-copilot/backend/app/s2p_graph_status.py`

Call the shared guard after existing backend/domain/DSN/graph validation and before the existing product allow-list branch. Keep protocol-v2 test handling unchanged. For production AGE, `soc_graph` becomes the only accepted product graph; the old `governed_copilot_graph` allow-list must no longer authorize a copilot startup.

Tests: existing test-mode graphs remain accepted; non-shared production graphs fail with the shared invariant message; `soc_graph` with the existing domain authorization succeeds.

### Step 3 — Generic startup paths

Change:

- `copilot-sdk/apps/trading/backend/app/main.py`
- `copilot-sdk/apps/purchasing/backend/app/main.py`
- `copilot-sdk/apps/dataops/backend/app/main.py`
- `s2p-copilot/backend/app/main.py`
- `gen-ai-roi-demo-v4-v50/backend/app/main.py`/`app/db/neo4j.py` as needed to expose the resolved invariant.

Ensure every production AGE/dual-write factory/client call receives the GraphConfig DSN and graph. Keep SQLite test fallback and app state aliases intact. S2P must retain one scorer/enrichment store (`s2p-copilot/backend/app/main.py:167-175`). SOC must retain AGE-only startup and bootstrap verification (`gen-ai-roi-demo-v4-v50/backend/app/main.py:200-221`).

Tests: per-copilot startup resolution and negative non-shared graph startup tests, preferably isolated from module import side effects.

### Step 4 — Claim proof

Change `copilot-sdk/scripts/phase6_claim_proof.py:176-188` to invoke the shared guard for all five production configs and enforce the requested CLI graph is `soc_graph`. Preserve DSN equality and one-graph checks.

### Step 5 — New invariant tests

Create `copilot-sdk/tests/test_soc_graph_invariant.py` with 11 tests (or equivalent parametrized coverage):

1. AGE production accepts `soc_graph`.
2. AGE production rejects another graph.
3. AGE production rejects blank/omitted graph.
4. SQLite allows any graph metadata.
5. Test-profile AGE allows a disposable protocol-v2 graph.
6–10. Trading, Purchasing, DataOps, S2P, and SOC startup/config paths resolve and accept `soc_graph`.
11. All five production GraphConfigs resolve the same graph and DSN (when configured), mirroring Phase 6.

Use real config objects and stateful stores/test doubles only; do not mock module imports or patch production functions. Add app-repo tests if the SDK-only file cannot safely import a startup module.

### Step 6 — Verification

Run, in order:

```text
python -m pytest copilot-sdk/tests/test_soc_graph_invariant.py -v --timeout=60
python -m pytest copilot-sdk/tests/ -q --timeout=300
python -m pytest copilot-sdk/apps/trading/backend/tests/ -q --timeout=120
python -m pytest copilot-sdk/apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest copilot-sdk/apps/dataops/backend/tests/ -q --timeout=120
python -m pytest s2p-copilot/backend/tests/ -q --timeout=300
python -m pytest gen-ai-roi-demo-v4-v50/backend/tests/ -q --timeout=300
python -m pytest ci-platform/tests/ -q --timeout=120
python copilot-sdk/scripts/phase6_claim_proof.py --dry-run --graph-name soc_graph
```

For SDK code changes, run the repository-required `graphify update .` after tests. If AGE is available, run the requested `--execute` claim proof with the operator-supplied DSN.

## §10 Risk Analysis

| Risk | What could go wrong | Mitigation |
|---|---|---|
| Wrong scope | A factory-level exact-name check breaks migration or protocol tests. | Keep exact enforcement at startup boundaries; retain factory authorization and explicit test mode. |
| Missed startup path | A generic fallback still constructs a store without the resolved graph. | Add explicit DSN/graph forwarding and static scan for every `create_graph_store`/AGE client call. |
| Test graph rejection | Live AGE tests use disposable names. | Require explicit test mode and preserve `protocol_v2_test*` checks. |
| Alternate production deployment | A deployment using `governed_copilot_graph` fails at startup. | This is intended fail-fast behavior; update deployment config to `soc_graph` and matching authorization. |
| Dual-write ambiguity | SQLite primary may appear to bypass the graph invariant. | Apply the guard to dual-write’s AGE graph while preserving local outbox mechanics only where the selected profile explicitly permits it. |
| SOC import behavior | Adding a second check changes import/startup exception type. | Reuse the existing `GraphConfigError` path and preserve AGE-only fail-fast semantics. |
| Claim-proof drift | Batch proof could validate a different policy than runtime. | Call the same helper before existing DSN/graph equality checks. |
| Environment leakage | One test’s graph env affects another startup test. | Use function-scoped env isolation and subprocess isolation for module-level startup imports. |

## §11 Reading Log

Fully read before design:

- `copilot-sdk/docs/implementation_plans/jm_gap_closure_plan_v1.md` (§7 Fix 6)
- `copilot-sdk/docs/design/jm_implementation_review_part2b_v1.md` (§2.1 and related Goal 6 evidence)
- `copilot-sdk/CLAUDE.md`
- `ci-platform/CLAUDE.md`
- `s2p-copilot/CLAUDE.md`
- `gen-ai-roi-demo-v4-v50/CLAUDE.md`
- `copilot-sdk/apps/trading/backend/app/main.py`
- `copilot-sdk/apps/trading/backend/app/graph_status.py`
- `copilot-sdk/apps/purchasing/backend/app/main.py`
- `copilot-sdk/apps/purchasing/backend/app/graph_status.py`
- `copilot-sdk/apps/dataops/backend/app/main.py`
- `copilot-sdk/apps/dataops/backend/app/graph_status.py`
- `s2p-copilot/backend/app/main.py`
- `s2p-copilot/backend/app/s2p_graph_status.py`
- `gen-ai-roi-demo-v4-v50/backend/app/main.py`
- `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py`
- `copilot-sdk/copilot_sdk/config/graph_config.py`
- `copilot-sdk/copilot_sdk/graph/factory.py`
- `copilot-sdk/graph_config.toml`
- `copilot-sdk/scripts/phase6_claim_proof.py`

Additional test-isolation scan:

- `copilot-sdk/tests/graph/conftest.py`
- `copilot-sdk/tests/graph/test_graphstore_factory.py`
- `copilot-sdk/tests/graph/test_protocol_v2_conformance.py`
- `copilot-sdk/tests/test_factory_dual_write.py`
- `copilot-sdk/tests/test_graph_config.py`
- `s2p-copilot/backend/tests/conftest.py`
- `s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py`
- `s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py`
- `gen-ai-roi-demo-v4-v50/backend/tests/conftest.py`

DESIGN_READY: YES
