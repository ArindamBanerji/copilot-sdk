# Consolidated Graph Configuration v1

Status: design contract  
Date: 2026-07-25  
Scope: copilot-sdk, s2p-copilot, ci-platform, and gen-ai-roi-demo-v4-v50

## 1. Executive summary

Five copilots now share AGE infrastructure, but graph configuration is
distributed across generic environment variables, domain-prefixed variables,
demo launch dictionaries, and test-only gates. A missing variable can silently
select SQLite, select the wrong graph, skip a live test, or write to a graph
that was not authorized. The risk increases whenever another copilot is
flipped.

This document defines one typed TOML-backed configuration model and a staged
migration. Environment variables remain authoritative during the transition:
an explicit environment value wins over a file value, preserving current
deployments. The loader validates the selected domain, backend, DSN, graph,
domain binding, ID prefix, and shared-graph authorization before a store is
constructed.

The scope is all five copilot graph readers (SOC, Trading, Purchasing, DataOps,
and S2P), demo.py launch settings, phase scripts, and live/destructive test
gates. The implementation is incremental: Trading is wired first, then the
other SDK copilots, S2P, SOC, tests, demo.py, and phase tooling.

## 2. Complete environment-variable inventory

The inventory records every environment variable read or set by the specified
production files, launcher, phase configuration, and test gates. "Required"
means required when the corresponding mode is selected; otherwise the variable
is optional and its stated default applies.

### 2.1 Shared generic graph variables

The SDK graph-status modules use the same six generic names as a diagnostic
presence check; domain-prefixed variables are authoritative active-graph
settings (Trading: `copilot-sdk/apps/trading/backend/app/graph_status.py:20-26`,
Purchasing: `copilot-sdk/apps/purchasing/backend/app/graph_status.py:22-28`,
DataOps: `copilot-sdk/apps/dataops/backend/app/graph_status.py:21-27`, S2P:
`s2p-copilot/backend/app/s2p_graph_status.py:19-25`).

| Variable | Reader | Required/default | Meaning |
|---|---|---|---|
| `GRAPH_BACKEND` | tuples cited above | optional; no active-graph default | Legacy/generic backend presence indicator |
| `GRAPH_DSN` | tuples cited above | optional | Legacy/generic DSN presence indicator |
| `GRAPH_NAME` | tuples cited above | optional | Legacy/generic graph presence indicator |
| `GRAPH_DOMAIN` | tuples cited above | optional | Legacy/generic domain presence indicator |
| `AGE_DSN` | tuples cited above | optional | Legacy AGE DSN alias |
| `AGE_GRAPH_NAME` | tuples cited above | optional | Legacy AGE graph alias |

SOC reads `GRAPH_BACKEND` at
`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:16-28`; when it is `age`, the
AGE factory is selected at `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:499-515`.

### 2.2 Trading

Trading reads values at
`copilot-sdk/apps/trading/backend/app/graph_status.py:81-90`, validates them at
`:96-141`, and reads the shadow switch during construction at `:252-289`.

| Variable | Required/default | Meaning |
|---|---|---|
| `TRADING_ACTIVE_GRAPH_BACKEND` | optional; `sqlite` | Active backend |
| `TRADING_ACTIVE_AGE_DSN` | required when backend is `age`; no default | AGE DSN |
| `TRADING_ACTIVE_AGE_GRAPH` | required when backend is `age`; no default | AGE graph |
| `TRADING_ACTIVE_AGE_DOMAIN` | optional; `trading` | Domain binding |
| `TRADING_ACTIVE_AGE_TEST_MODE` | optional; false | Protocol test graph permission |
| `TRADING_SHARED_GRAPH_AUTHORIZED` | required for `trading:soc_graph`; otherwise optional | Shared graph authorization |
| `TRADING_SHADOW_AGE` | optional; false | Shadow switch |

### 2.3 Purchasing

Purchasing reads/validates settings at
`copilot-sdk/apps/purchasing/backend/app/graph_status.py:86-149` and consumes
shadow settings at `:302-334`.

| Variable | Required/default | Meaning |
|---|---|---|
| `PURCHASING_ACTIVE_GRAPH_BACKEND` | optional; `sqlite` | Active backend |
| `PURCHASING_ACTIVE_AGE_DSN` | required when backend is `age`; no default | AGE DSN |
| `PURCHASING_ACTIVE_AGE_GRAPH` | required when backend is `age`; no default | AGE graph |
| `PURCHASING_ACTIVE_AGE_DOMAIN` | optional; `purchasing` | Domain binding |
| `PURCHASING_ACTIVE_AGE_TEST_MODE` | optional; false | Protocol test graph permission |
| `PURCHASING_SHARED_GRAPH_AUTHORIZED` | required for `purchasing:soc_graph`; otherwise optional | Shared graph authorization |
| `PURCHASING_SHADOW_AGE` | optional; false | Shadow switch |

### 2.4 DataOps

DataOps reads settings at
`copilot-sdk/apps/dataops/backend/app/graph_status.py:83-93`, validates at
`:99-142`, and passes factory arguments at `:253-283`.

| Variable | Required/default | Meaning |
|---|---|---|
| `DATAOPS_ACTIVE_GRAPH_BACKEND` | optional; `sqlite` | Active backend |
| `DATAOPS_ACTIVE_AGE_DSN` | required when backend is `age`; no default | AGE DSN |
| `DATAOPS_ACTIVE_AGE_GRAPH` | required when backend is `age`; no default | AGE graph |
| `DATAOPS_ACTIVE_AGE_DOMAIN` | optional; `dataops` | Domain binding |
| `DATAOPS_ACTIVE_AGE_TEST_MODE` | optional; false | Protocol test graph permission |
| `DATAOPS_ACTIVE_LIVE_AGE_TEST` | optional; false | Live AGE permission |
| `DATAOPS_SHARED_GRAPH_AUTHORIZED` | required for `dataops:soc_graph`; otherwise optional | Shared graph authorization |

### 2.5 S2P

S2P reads active/shared settings at
`s2p-copilot/backend/app/s2p_graph_status.py:94-116`, validates at
`:128-165`, and consumes shadow/factory settings at `:275-304`.

| Variable | Required/default | Meaning |
|---|---|---|
| `S2P_ACTIVE_GRAPH_BACKEND` | optional; `sqlite` | Active backend |
| `S2P_ACTIVE_AGE_DOMAIN` | optional; `s2p` | Domain binding |
| `S2P_ACTIVE_AGE_DSN` | required when backend is `age`; no default | AGE DSN |
| `S2P_ACTIVE_AGE_GRAPH` | required when backend is `age`; no default | AGE graph |
| `S2P_ACTIVE_AGE_TEST_MODE` | optional; false | Protocol test graph permission |
| `S2P_SHADOW_AGE` | optional; false | Shadow switch |
| `S2P_SHARED_GRAPH_AUTHORIZED` | required for `s2p:soc_graph`; otherwise optional | Shared graph authorization |

### 2.6 SOC and platform settings

SOC direct-client credentials are read at
`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28,46-48`; HTTP and narrative
settings are read at `gen-ai-roi-demo-v4-v50/backend/app/main.py:50-54,180-194,412-417`.

| Variable | Required/default | Meaning |
|---|---|---|
| `NEO4J_URI` | required only for Neo4j backend; no default | Neo4j URI |
| `NEO4J_USER` | optional; `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | required only for Neo4j backend; no default | Neo4j password |
| `CORS_ORIGINS` | optional; application default | Browser origin allow-list |
| `PORT` | optional; `8001` startup default | SOC HTTP port |
| `NARRATIVE_PROVIDER` | optional; `template` | Narrative provider |
| `BACKEND_PORT` | optional; written by SOC startup from `PORT` | Persisted SOC port marker (`gen-ai-roi-demo-v4-v50/backend/app/main.py:180-190`) |

### 2.7 demo.py launch variables

DSNs and repository paths are derived at `copilot-sdk/demo.py:82-103`, and
SOC/DataOps overrides are defined at `copilot-sdk/demo.py:105-148`.

| Variable | Required/default | Meaning |
|---|---|---|
| `CLAUDE_SOC` | optional; repo-relative SOC path | SOC checkout override |
| `CLAUDE_S2P` | optional; repo-relative S2P path | S2P checkout override |
| `DEMO_NO_RESEED` | optional; child value `1` only with `--no-reseed` | Suppress fixture/bundle writes |
| `SOC_LEARNING_ENABLED` | optional; set in SOC diagnostic child environment | SOC learning switch |
| `AGE_USE_POOL` | optional; diagnostic AGE pool switch | AGE connection-pool selection |
| `VITE_S2P_API_URL` | optional; launcher sets SOC frontend URL | Frontend integration URL |
| `VITE_API_URL` | optional; launcher sets S2P frontend URL | Frontend integration URL |

The child environment is copied at `copilot-sdk/demo.py:729-739`; consolidation
must preserve inheritance and use setdefault semantics for defaults.

### 2.8 Phase-script variables

`scripts/phase_config.py` defines the domain argument and fallback at
`copilot-sdk/scripts/phase_config.py:47-55`, SQLite override at `:57-62`, AGE
aliases at `:62-64`, and per-domain API base at `:64`.

| Variable | Required/default | Meaning |
|---|---|---|
| `MIGRATION_DOMAIN` | optional; `trading` | Default phase domain |
| `MIGRATION_SQLITE_PATH` | optional; domain path | Explicit SQLite source |
| `GRAPH_DSN` / `AGE_DSN` | optional; empty | AGE DSN aliases |
| `GRAPH_NAME` / `AGE_GRAPH_NAME` | optional; `soc_graph` | Graph aliases |
| `<DOMAIN>_API_BASE` | optional; `http://127.0.0.1:<port>` | Concrete names include `TRADING_API_BASE`, `PURCHASING_API_BASE`, `DATAOPS_API_BASE`, and `S2P_API_BASE` |

### 2.9 Test skip and safety variables

S2P active-live keys are defined at
`s2p-copilot/backend/tests/test_s2p_active_age_live.py:20-26` and checked at
`:44-52`; parallel keys are at
`s2p-copilot/backend/tests/test_s2p_active_age_parallel.py:22-27,43-51`.
S2P shadow-live keys are at
`s2p-copilot/backend/tests/test_s2p_shadow_live_age.py:16-25,39-47`.
ci-platform live gates use `AGE_INTEGRATION` at
`ci-platform/tests/test_age_client.py:5,15-18,399-403`, graph overrides and
DSN fallbacks at `ci-platform/tests/test_counter_store_live_age.py:87-92` and
`ci-platform/tests/test_counter_store_route_readiness.py:244-248`, and
`AGE_D2_LIVE_GATE` at `ci-platform/tests/test_age_graph_store_v.py:291-299`.
SOC's destructive safety gate is at
`gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:29-32`.

| Variable | Required/default | Meaning |
|---|---|---|
| `S2P_ACTIVE_LIVE_AGE_TEST` | optional; unset skips | Active live AGE opt-in |
| `S2P_ACTIVE_PARALLEL_AGE_TEST` | optional; unset skips | Parallel AGE opt-in |
| `S2P_SHADOW_LIVE_AGE_TEST` | optional; unset skips | Shadow-live opt-in |
| `S2P_AGE_DSN` | required for shadow-live | Shadow DSN |
| `S2P_AGE_GRAPH` | required for shadow-live | Shadow graph |
| `S2P_AGE_TEST_MODE` | required for shadow-live | Shadow test mode |
| `AGE_INTEGRATION` | optional; `0` | ci-platform live integration gate |
| `AGE_COUNTER_P2C_GRAPH` | optional; scratch default | Counter P2C graph |
| `AGE_COUNTER_P2D_GRAPH` | optional; scratch default | Counter P2D graph |
| `DATABASE_URL` | optional DSN fallback | Counter test DSN fallback |
| `AGE_D2_LIVE_GATE` | optional; `0` | AGE D2 live gate |
| `TEST_DESTRUCTIVE_AGE` | optional; unset | Destructive SOC AGE opt-in |

**Inventory total: 63 unique names/patterns**, counting `<DOMAIN>_API_BASE` as
one pattern and counting DSN/graph aliases separately.

## 3. Duplication map

There are 10 duplicated concepts:

1. Backend: `GRAPH_BACKEND` versus each active backend variable.
2. DSN: `GRAPH_DSN`, `AGE_DSN`, each active AGE DSN, and S2P shadow DSN.
3. Graph: `GRAPH_NAME`, `AGE_GRAPH_NAME`, each active graph, and shadow graph.
4. Domain: generic domain versus active domain.
5. Test mode: active test modes versus S2P shadow test mode.
6. Shared authorization: one differently prefixed name per copilot.
7. Shadow mode: Trading, Purchasing, and S2P switches.
8. Live-test opt-ins: DataOps and three S2P test gates.
9. API endpoint selection: demo ports versus phase API-base overrides.
10. Runtime safety: reseed, destructive, integration, D2, and live AGE gates.

The loader normalizes these concepts to one typed field each and exposes a
source-aware diagnostic report.

## 4. Proposed TOML format

Create `copilot-sdk/graph_config.toml`; secrets and operator DSNs remain
environment-only.

```toml
[defaults]
dsn = ""
graph = "soc_graph"
backend = "sqlite"
age_test_mode = false

[copilot.soc]
domain = "soc"
backend = "age"
prefix = "SOC-"

[copilot.trading]
domain = "trading"
backend = "age"
prefix = "TRD-"
authorized = "trading:soc_graph"
active_test_mode = false
shadow_age = false
port = 8010

[copilot.purchasing]
domain = "purchasing"
backend = "age"
prefix = "PUR-"
authorized = "purchasing:soc_graph"
active_test_mode = false
shadow_age = false
port = 8020

[copilot.dataops]
domain = "dataops"
backend = "age"
prefix = "DOPS-"
authorized = "dataops:soc_graph"
active_test_mode = false
live_age_test = false
port = 8030

[copilot.s2p]
domain = "s2p"
backend = "age"
prefix = "S2P-"
authorized = "s2p:soc_graph"
active_test_mode = false
shadow_age = false
port = 8002

[soc]
neo4j_uri = ""
neo4j_user = "neo4j"
neo4j_password = ""
cors_origins = []
narrative_provider = "template"
port = 8001

[test]
destructive_age = false
scratch_graph_prefix = "soc_graph_test_"
age_integration = false
age_d2_live_gate = false

[test.s2p]
live_age = false
parallel_age = false
shadow_live_age = false

[phase]
domain = "trading"
sqlite_path = ""
api_base = ""
```

The fields cover every inventory entry: backend, DSN, graph, domain, test and
shadow/live gates, authorization, prefix, ports, SOC credentials, and phase
overrides. DSN and credentials are required only in the selected backend
mode; authorization is required for `soc_graph`. Production TOML contains no
secret values.

## 5. Loader design

Add `copilot-sdk/copilot_sdk/config/graph_config.py`:

```python
@dataclass(frozen=True)
class GraphConfig:
    domain: str
    backend: Literal["sqlite", "age", "dual_write"]
    dsn: str | None
    graph: str
    prefix: str
    authorized: str | None
    active_test_mode: bool
    shadow_age: bool
    live_age_test: bool
    port: int | None

    @classmethod
    def load(cls, domain: str = "trading") -> "GraphConfig": ...
```

`load()` searches the new loader override `GRAPH_CONFIG_PATH` first (defined by
this contract and implemented in `copilot-sdk/copilot_sdk/config/graph_config.py`), then the SDK-root TOML, then a
repo-relative template. It parses with `tomllib`, selects the domain table,
and applies environment overrides; environment wins over file values. The
loader raises stable actionable errors for missing AGE DSN/graph, domain
mismatch, missing shared authorization, or invalid backend.

Each SDK graph-status module calls `GraphConfig.load(domain)` once and passes
typed values to the existing factory. Existing status response keys remain
unchanged. SOC uses the loader for its AGE branch while retaining Neo4j
fallback credentials during migration.

## 6. Test configuration

Tests use the typed object plus a helper `is_live_age_configured(domain)` that
checks DSN, graph, domain, backend, and the domain live opt-in. It replaces
repeated all-keys checks while preserving explicit skip reasons.

The test section supplies scratch graph prefixes and non-secret defaults. Every
live test asserts its graph begins with the scratch prefix and is not
`soc_graph`. Destructive AGE remains an environment-only safety control; the
`TEST_DESTRUCTIVE_AGE` gate is documented at
`gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:29-32` and
is never enabled by a production TOML file.

## 7. demo.py integration

`demo.py` loads the selected domain config, then translates typed values to
the existing domain-prefixed child environment. It continues to use
`os.environ.copy()` at `copilot-sdk/demo.py:729-739` and uses setdefault for
per-copilot defaults. This preserves operator overrides and avoids races from
writing a runtime file. `DEMO_NO_RESEED` remains a child-only launch control;
frontend URL variables remain launch-time values.

## 8. Phase-script integration

`scripts/phase_config.py` already owns domain paths, ports, endpoint paths,
and payload builders at `copilot-sdk/scripts/phase_config.py:30-68`. It should
call `GraphConfig.load(domain)` for graph fields and retain only phase-specific
fields locally. Existing migration/path/API overrides at
`copilot-sdk/scripts/phase_config.py:47-68` remain supported. A print-config
mode must redact DSNs and show each value's source.

## 9. Migration path

1. Add TOML, loader, validation, redaction, and unit tests.
2. Wire Trading graph_status and run its status/SQLite smoke tests.
3. Wire Purchasing and DataOps, preserving authorization and live gates.
4. Wire S2P active graph status and test skip helper; keep enrichment primary
   store behavior unchanged.
5. Wire SOC AGE selection and startup diagnostics; keep direct SOC query layer.
6. Wire demo.py with loader defaults and setdefault emission.
7. Wire phase_config and scripts; dry-run every domain.
8. After two releases, make missing AGE configuration a hard error while
   retaining SQLite environment fallback for development.

Environment names remain supported throughout steps 1-7. Rollback is
configuration-only: remove `GRAPH_CONFIG_PATH` or restore the prior backend
environment and restart. No data migration depends on the loader.

Planned blast-radius files (29): the TOML and loader; four SDK graph-status
modules; SOC `neo4j.py` and `main.py`; `demo.py`; `phase_config.py`; three S2P
live test modules; five ci-platform gate modules; the SOC stress test; SDK
graph/config/factory tests; and loader/TOML/phase unit tests. The implementer
must not edit outside this set without a design update.

## 10. Implementation order

Step 1 is independently deployable (loader and tests only). Step 2 is
independently deployable (Trading opt-in). Steps 3-5 are independently
deployable per copilot. Step 6 is launcher-only; Step 7 is tooling-only.
Step 8 is the breaking change and requires a deprecation announcement.

Every step must prove effective config parity with the old environment,
preserve domain/graph authorization, and run a store-type and ID-prefix smoke
test. Explicit AGE must never silently fall back to SQLite.

## 11. Risks

* File/environment drift: source-aware diagnostics and a CI load-all-domains
  check mitigate it.
* Cross-repository paths: one SDK loader and explicit search order mitigate it.
* Secrets in TOML: prohibited; redact DSNs and credentials.
* Test flags leaking into production: test profile is rejected by production.
* Alias disagreement: warn on conflicting generic/domain values and fail on
  domain mismatch.
* Wrong-graph writes: validate exact domain and authorization before factory
  construction and log domain/backend/graph with a redacted DSN.
* Incomplete adoption: CI requires every graph-status module to call the
  loader.

## 12. Reading log

* `copilot-sdk/apps/trading/backend/app/graph_status.py:1-382`.
* `copilot-sdk/apps/purchasing/backend/app/graph_status.py:1-419`.
* `copilot-sdk/apps/dataops/backend/app/graph_status.py:1-367`.
* `s2p-copilot/backend/app/s2p_graph_status.py:1-437`.
* `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:1-554`.
* `gen-ai-roi-demo-v4-v50/backend/app/main.py:1-507`.
* `copilot-sdk/demo.py:1-1230`.
* `copilot-sdk/scripts/phase_config.py:1-89`.
* `s2p-copilot/backend/tests/test_s2p_active_age_live.py:1-220`.
* `s2p-copilot/backend/tests/test_s2p_active_age_parallel.py:1-170`.
* `s2p-copilot/backend/tests/test_s2p_shadow_live_age.py:1-250`.
* `ci-platform/tests/test_counter_store_live_age.py:1-270`.
* `ci-platform/tests/test_counter_store_route_readiness.py:1-485`.
* `ci-platform/tests/test_age_client.py:1-540`.
* `ci-platform/tests/test_age_graph_store_v.py:1-320`.
* `gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:1-240`.

The citations in sections 2-8 are the authoritative evidence for every
environment variable and override in this contract.
