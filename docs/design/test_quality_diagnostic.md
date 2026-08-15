# Test Quality Diagnostic

Audit date: 2026-08-15  
Scope: read-only analysis of live-backend dependencies, production
monkeypatch hooks, and skip hygiene. No source or test fixes were made.

## Executive summary

The reported SDK result is 2,975 passed, 1 failed, and 10 skipped. The quality
problem is structural:

- one preseed unit test is not self-contained because an indirect helper still
  performs a real HTTP GET;
- five telemetry tests are live-backend integration tests mixed into the
  ordinary SDK test suite;
- four Protocol-V2 tests are empty placeholders hidden by a module-level skip;
- one SOC AGE projection test is a deliberately deferred data-backfill gate;
- SOC production exposes two compatibility seams specifically for tests to
  monkeypatch;
- 497 SDK test lines and 1,271 SOC test lines contain monkeypatch usage.

The correct response is dependency injection and explicit test-tier separation,
not adding more monkeypatches or making live tests skip more quietly.

## 1. Broken and skipped test root causes

| Test(s) | Why it fails/skips | Actual need | Proper fix |
|---|---|---|---|
| test_preseed_idempotent | test_preseed_demo_data.py:199-217 patches load_seed, check_health, check_already_seeded, verify_domain, and api_post, but seed_domain calls has_regime_checkpoint for an already-seeded Trading domain (preseed_all_copilots.py:366-390). That helper performs api_get (lines 180-188). | One complete preseed client covering health, trajectory, checkpoint, POST, and verification. | Define and inject a PreseedClient protocol/service. Production receives the HTTP implementation; the unit test receives an in-memory stateful client. Do not add another monkeypatch for has_regime_checkpoint. |
| Five evolution telemetry tests | test_evolution_telemetry.py:105-143 calls 127.0.0.1 ports 8001, 8002, 8010, 8020, and 8030. _summary skips on connection failure at lines 105-112. | Five real app factories/providers/stores with isolated state. | Convert to in-process app-factory/TestClient contract tests, or move to an explicitly marked integration suite. Do not mix port availability with unit status. |
| Four Protocol-V2 service tests | test_protocol_v2_service_layer.py:6-29 has a module-level skip and every body is pass. | Canonical outcome commit, pending-sync/outbox, V timing, and replay idempotency. | Implement the service contract, then remove the skip. Use real SQLite/in-memory stores and a stateful outbox fixture; keep AGE process tests separate. |
| SOC backfill test | test_soc_age_projection_contract.py:255-257 explicitly requires canonical SOC Outcome backfill data and a backfill design. | Migration/backfill contract, mixed embedded/canonical AGE fixture, and exactly-once V counting. | Design and implement the backfill fixture/migration, then unskip. Do not replace it with a synthetic assertion or mocked graph write. |

The preseed failure is an incomplete test double, not a business-logic failure:
the Trading-only checkpoint branch escaped the test's patch bundle and leaked
to the configured endpoint.

The first two telemetry tests are self-contained: the normalizer uses a real
PromptVariantEvolver, and the endpoint test builds FastAPI with an in-memory
GraphStore. Only the five _summary(port) tests are live-backend tests.

## 2. Production monkeypatch hooks

| Hook | Why it exists | Test usage | Injection replacement |
|---|---|---|---|
| triage.py:92-93, compute_factor_vector = _compute_factor_vector | Backward-compatible router alias for replacing factor-vector behavior. | test_ae_integration, test_cold_start_guards, test_d06_unmapped, test_rl_triage_integration, and test_sentinel_integration. test_d06_unmapped.py:76 replaces it with a failing function. | Define a FactorVectorProvider protocol and inject it into the triage service/route dependencies. The default wraps the real implementation; harnesses pass a complete deterministic provider with provenance and validation. |
| triage.py:362-368, _soc_learning_enabled | Legacy reconciliation of module LEARNING_ENABLED, domain config, and environment state. | test_rl_feature_flags.py, test_soc_dk_l5.py, and test_soc_learning_live.py patch config/env and both route/config globals. | Inject a LearningPolicy or SocRuntimeConfig at app construction. It owns environment/config resolution and exposes enabled(). Tests instantiate enabled/disabled policies instead of mutating imported globals. |

These are production compatibility hooks, not merely test fixtures: their
source comments explicitly mention backward-compatible or legacy
route-level monkeypatch support.

## 3. Monkeypatch debt characterization

The exact count of lines containing monkeypatch is:

- SDK: 497 lines across 38 files;
- SOC: 1,271 lines across 60 files.

Using current collection baselines of 2,976 SDK tests and 2,262 SOC tests,
files containing monkeypatch usage contain approximately 627 SDK tests (21.1%)
and 929 SOC tests (41.1%). This is an upper bound: not every test in those
files uses the fixture, and environment/clock patches are less problematic
than production-interface patches.

### Dominant targets

The simple setattr target parser is noisy for multiline calls, but the
dominant normalized targets are:

| Rank | Target | Approximate setattr lines | Debt |
|---:|---|---:|---|
| 1 | gate | 76 SOC | Gate state/event and policy seams are not injected. |
| 2 | triage | 42 SOC | Route globals, graph client, factor provider, state, and event bus are mutable. |
| 3 | soc_config | 35 SOC | Feature flags and learning policy are mutable module configuration. |
| 4 | runner | 32 SOC | Subprocess/background execution lacks an executor seam. |
| 5 | gae_state | 29 SOC | Scorer, store, guarded update, and learning state access lack complete runtime injection. |

Other significant SDK targets are preseed (24), demo (17), sqlite_to_age (15),
AGE connection helpers (14), and CompoundingScorer (8).

## 4. Live-backend references

The literal host scan found 16 SDK references and 13 SOC references, but the
raw total includes CORS strings, AGE DSNs, documentation, and fixture values.
The actionable live set is:

- five SDK HTTP tests in test_evolution_telemetry.py, dynamically using ports
  8001, 8002, 8010, 8020, and 8030;
- SOC integration tests requiring 127.0.0.1:8001, including
  test_cross_tab_consistency.py and test_soc_route_validation_runner.py;
- SOC/local-service tests using port 8000, including compounding-gate and
  visual-smoke tests.

AGE localhost:5432/5433 strings are database integration configuration and
should be explicitly marked, not counted as ordinary unit dependencies.
CORS localhost:5173-5177 strings are configuration assertions, not live
service calls.

The hygiene failure is a test requiring an independently running service and
turning absence into a skip, not the mere presence of a URL string.

## 5. Design principles

### 5A. Percentage affected by banning monkeypatch

Approximately 21.1% of SDK tests and 41.1% of SOC tests are in files using
monkeypatch. The likely direct rewrite estimate is lower: 10-20% of SDK tests
and 25-40% of SOC tests. The difference is environment/clock/external-connector
patches and unrelated tests sharing a file.

### 5B. Top five targets

The highest-value interfaces lacking injection seams are triage runtime
dependencies, SOC learning/config policy, GAE state/scorer/store access,
evolution gate/event state, and preseed/migration transport/persistence.

### 5C. Minimum viable change for all reported tests

Estimated effort: 2-4 engineering days.

1. Inject a complete stateful PreseedClient.
2. Convert the five telemetry checks to app-factory TestClient tests, or move
   them to an explicit integration tier.
3. Implement the Protocol-V2 service invariants before unskipping tests.
4. Keep the SOC backfill test pending until the canonical migration design and
   fixture exist.

### 5D. Prevention rule

Use three CI layers:

1. Strict unit, integration, and pending markers. Unit tests cannot open
   sockets or require external AGE.
2. AST/collection checks rejecting network calls, raw application localhost
   URLs, and connection-error skips in unmarked unit tests.
3. A production/test seam check rejecting new module aliases whose purpose is
   monkeypatch compatibility. Require a complete injected dependency instead.

Retain the existing prohibition on patching scorers, GraphStores, conservation
helpers, and audit chains. Any allowed external patch must carry an explicit
justification.

### 5E. Path to zero production hooks

1. Classify patches as environment, connector, clock, persistence, scorer,
   policy, or route-global.
2. Build protocols and complete fixtures for transport, scorer/state, GraphStore,
   event bus, factor vectors, learning policy, and executors.
3. Migrate the two SOC aliases first.
4. Migrate preseed and migration utilities to client objects.
5. Convert telemetry to app-factory contract tests plus explicit process-level
   integration tests.
6. Replace SOC route patch bundles with an injected TriageDependencies object.
7. Enforce the AST/marker gates in CI and retain only justified environment,
   clock, and unreachable paid/network connector patches.

## 6. Recommended order and estimates

| Order | Work | Estimate | Exit condition |
|---:|---|---:|---|
| 1 | Test markers and live-backend separation | 0.5-1 day | Default unit suite never opens backend sockets. |
| 2 | Preseed client injection | 0.5-1 day | Idempotence test covers checkpoint logic without HTTP or patching. |
| 3 | SOC factor-vector and learning-policy injection | 1.5-3 days | Both production hooks are removed and harnesses use complete dependencies. |
| 4 | Protocol-V2 service tests | 2-4 days | Four placeholders become meaningful passing tests. |
| 5 | SOC canonical outcome backfill | 2-5 days | Mixed data proves exactly-once V counting and skip is removed. |
| 6 | Broader monkeypatch migration | 5-10 days | Scorer/store/gate/runtime patches become protocols/stateful fixtures. |

Minimum for the six reported test quality issues: 2-4 days, excluding unresolved
backfill product design. Full cleanup to zero production hooks and materially
reduced test patching: 10-20 engineering days.

## 7. Prevention checklist

Every new test must answer:

- Is it unit, integration, or pending?
- Can it run without a backend process, socket, AGE instance, or external API?
- Does each test double own state and answer queries from that state?
- Does it patch a scorer, GraphStore, conservation helper, audit chain, or
  production module alias?
- If it calls live infrastructure, is the dependency explicit and excluded
  from the default unit command?
- Does a skip identify a missing implementation/design dependency rather than
  hide an environmental failure?
- Does the test prove behavior rather than merely prove a patched function was
  called?

## Review / exit summary

- Tests analyzed: 10 reported tests plus the SOC backfill gate.
- Production monkeypatch hooks: 2.
- Monkeypatch lines: SDK=497, SOC=1,271.
- Live-backend references: SDK=16 literal references, SOC=13 literal
  references; 5 actionable SDK HTTP tests plus identified SOC live tests after
  excluding CORS/DSN/configuration strings.
- Top targets: gate, triage, soc_config, runner, gae_state.
- Minimum fix: 2-4 engineering days.
- Full cleanup estimate: 10-20 engineering days.
