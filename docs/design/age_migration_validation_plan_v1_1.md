# AGE Shared-Graph Migration End-to-End Validation Plan v1.1

Status: Proposed authoritative validation contract
Supersedes: `docs/design/age_migration_validation_plan_v1.md`
Authority: Copilot SDK migration validation review
Date: 2026-07-25
Scope: five copilots on the shared AGE graph `soc_graph`

This plan is self-contained and executable. A result is a PASS only when the
named command, assertion, and evidence artifact exist. No test that mutates,
archives, or deletes data may target `soc_graph`. All AGE-mutating checks use a
disposable graph named by the run.

## 1. Executive summary

This plan validates domain isolation, conservation accounting, AGE/SQLite
behavioral equivalence, startup configuration, migration integrity, concurrent
writes, performance, browser behavior, and rollback. Production-ready means
all mandatory criteria in section 7 pass in one comprehensive report, with no
unexpected skips, failures, or unowned blockers.

The principal risks are raw writes without a domain, divergent V computation
paths, scorer-state contention, cold-start score drift, silent SQLite fallback,
wrong-graph writes, index/query-plan regression, browser data leakage, and an
unrehearsed flip-back during an AGE incident.

### 1.1 Canonical V_soc reconciliation

`V_soc` is not a permanent hardcoded number. It is the verified, active SOC
Decision count returned by the read-only census at the beginning of each
validation run. The July 25, 2026 live census value is 4,862.

The parent PF-1 snapshot value 4,899 came from a different graph snapshot: it
combined 4,862 formerly-NULL verified rows with 37 already-tagged verified
rows. The current graph has zero NULL-domain Decisions and 4,862 verified
Decisions with `domain='soc'`; the graph evolved between those snapshots. The
two populations must not be added together.

The authoritative baseline is therefore:

```text
census_baseline = soc_domain_census.py verified SOC count at run start
V_soc(t) >= census_baseline
```

Every increase above `census_baseline` must equal a recorded verification event
from this run. Non-SOC activity must produce zero SOC increase. A run records
the baseline and event ledger before any preseed, reset, score, or learn action.

## 2. Validation areas

Each area defines proof, existing evidence, the remaining gap, pass criteria,
and execution ownership.

### Area 1: Domain isolation

Prove that every Decision read for domain D excludes all other domains and that
score/learn activity in D changes only D's counts, categories, history, archive,
and conservation values.

Run:

```powershell
Set-Location gen-ai-roi-demo-v4-v50\backend
python -m pytest tests/test_soc_domain_isolation.py -v --timeout=60
```

Assert the suite reports 10 passed, including foreign-domain counts, category
and outcome aggregates, the exact predicate, archive query, explorer result,
mutation result, and GraphSnapshot. [gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_isolation.py:138](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_isolation.py:138)

For each of `soc`, `trading`, `purchasing`, `dataops`, and `s2p`, use a
disposable AGE graph and assert:

```text
count(Decision WHERE domain=D AND decision_id=X) == 1
count(Decision WHERE domain<>D AND decision_id=X) == 0
count(Outcome for X) == 1 after the domain's learn operation
```

Exists: SOC's 10-test isolation suite. Gap: no five-domain browser assertion
and no simultaneous AGE read test. Owner: automated suite plus release runner.

Pass: all 10 tests pass; all five domains satisfy the three assertions; no
foreign Decision ID appears in any domain response.

### Area 2: V_soc stability and implementation parity

The gate is reconciliation-based, never hard equality to 4,862:

```text
census_baseline = census verified SOC count before lifecycle actions
V_census_after >= census_baseline
V_census_after - census_baseline == sum(recorded SOC verification events)
V_census_after == V_store
V_census_after does not change after non-SOC score/learn activity
```

Capture the baseline and each checkpoint with:

```powershell
Set-Location gen-ai-roi-demo-v4-v50\backend
python scripts/soc_domain_census.py
```

The census contains domain counts, verified counts, correct counts, and archive
checks. [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61) [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:92](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:92) [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:121](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:121)

At every checkpoint also call the exact store function used by the scorer:

```python
store.count_verified("soc")
```

and assert it equals the census value. The SDK scorer calls the graph store's
domain-scoped count during conservation calculation. [copilot_sdk/scoring/scorer.py:706](../../copilot_sdk/scoring/scorer.py:706) The AGE adapter forwards both count methods to AGE. [ci-platform/ci_platform/graph/age_sdk_adapter.py:288](../../../ci-platform/ci_platform/graph/age_sdk_adapter.py:288)

Known adapter discrepancy: the historical report that `count_verified(store,
'soc')` returned zero is a validation blocker until reproduced and fixed. A
disagreement between census and `store.count_verified("soc")` is FAIL; no waiver
is permitted. The report must record both values and the query path.

Lifecycle order and assertions:

```text
capture baseline
preseed -> V delta equals recorded verified events
restart -> V does not decrease
reset -> V changes only according to reset contract and event ledger
SOC score+learn -> delta equals SOC verifications
non-SOC score+learn -> SOC delta == 0
```

Exists: census and fixture-level isolation. Gap: lifecycle runner and live
store/census parity gate. Owner: automated runner.

Pass: all deltas are traceable; no decrease; no non-SOC increase; census and
store values are equal at every checkpoint.

### Area 3: Full platform launch

Prove all five copilots launch on AGE, expose healthy endpoints, report
`GRAPH_BACKEND=age` and `GRAPH_NAME=soc_graph`, and stop cleanly.

Run:

```powershell
Set-Location copilot-sdk
python demo.py --no-browser
python demo.py --status
python demo.py --verify
python demo.py --stop
```

The launcher defines these options. [demo.py:1111](../../demo.py:1111) [demo.py:1138](../../demo.py:1138) [demo.py:1141](../../demo.py:1141)

Assert five process records, five HTTP 200 health responses, backend `age`,
graph `soc_graph`, expected domain, and zero owned processes after stop.

Exists: launcher status and verify. Gap: one automated launch-health-stop
assertion across all five. Pass: all assertions and no SQLite fallback.
Owner: automated runner; operator reviews process evidence.

### Area 4: Cross-domain write safety and contention

For non-SOC SDK domains, the existing gate submits score/learn and verifies
domain-qualified Decision counts. [scripts/phase_cycle_gate.py:7](../../scripts/phase_cycle_gate.py:7) [scripts/phase_cycle_gate.py:21](../../scripts/phase_cycle_gate.py:21) [scripts/phase_cycle_gate.py:25](../../scripts/phase_cycle_gate.py:25)

Run it only for `trading`, `purchasing`, `dataops`, and `s2p`:

```powershell
Set-Location copilot-sdk
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "<disposable-dsn>"
$env:AGE_TEST_GRAPH = "<disposable-graph>"
python scripts/phase_cycle_gate.py --domain trading --cycles 40
python scripts/phase_cycle_gate.py --domain purchasing --cycles 40
python scripts/phase_cycle_gate.py --domain dataops --cycles 40
python scripts/phase_cycle_gate.py --domain s2p --cycles 40
```

SOC is explicitly exempt from this SDK gate: the SDK payload builder is not
SOC's production API. SOC write safety is proved by Area 1's live SOC API
cycle, its isolation suite, and the live learning-health/conservation endpoint.
The runner must report SOC as `soc_api_cycle`, never as an SDK `phase_cycle_gate`
result.

For every generated ID X assert:

```text
Decision(X).domain == caller_domain
Outcome(X).domain == caller_domain
count(X in any other domain) == 0
```

Add two contention tests in the same domain D, using two independent concurrent
score/learn tasks and distinct IDs. Assert:

```text
V_after - V_before == number_of_successful_verifications
no lost update
no torn response or 500
all generated Decisions have domain D
```

Then run one task per domain concurrently and repeat the cross-domain assertions.

Exists: sequential per-domain gate. Gap: same-domain contention, five-domain
overlap, and real SOC API cycle. Pass: all four SDK gates, SOC API cycle, same-
domain contention, and five-domain overlap pass with zero cross-talk.
Owner: automated runner.

### Area 5: Performance and indexes

At the 33,048-Decision graph, run 250 representative SOC score requests and
record p50, p95, p99, errors, graph size, and query plans. The explicit p95 gate
is:

```text
p95 <= 193 ms
error_count == 0
```

The 193 ms value is the approved pre-migration baseline for the 250-request
workload. If the workload changes, create a new signed baseline before changing
this threshold; an unrecorded baseline is not a pass.

Verify indexes:

```powershell
Set-Location copilot-sdk
python scripts/create_age_indexes_v2.py
```

Assert `decision_domain_idx` and `decision_archived_idx` exist on the physical
AGE Decision relation and capture EXPLAIN output for scoped active/archive
queries. The index script creates and lists those indexes. [scripts/create_age_indexes_v2.py:1](../../scripts/create_age_indexes_v2.py:1) [scripts/create_age_indexes_v2.py:41](../../scripts/create_age_indexes_v2.py:41) [scripts/create_age_indexes_v2.py:93](../../scripts/create_age_indexes_v2.py:93)

Exists: index creation. Gap: formal benchmark and plan artifact. Pass: index
existence, p95 <= 193 ms for the named workload, zero errors, and a recorded
plan. Owner: automated benchmark.

### Area 6: Playwright coverage

Prove every post-flip tab displays only its AGE domain's data, categories,
history, score, learn, and conservation values. Assert HTTP 200, backend `age`,
graph `soc_graph`, and expected-domain Decision/category values.

Run every app's Playwright suite after launch. Trading must run serially:

```powershell
Set-Location copilot-sdk\apps\trading\frontend
npx playwright test --workers=1
```

Run equivalent repository commands for SOC, S2P, Purchasing, and DataOps with
their documented spec roots. Use `data-testid`, not positional selectors; this
is required by the SDK testing rules. [CLAUDE.md:48](../../CLAUDE.md:48)

Exists: no established post-flip browser proof. Gap: all five suites and
foreign-domain negative assertions. Pass: all required specs pass, zero skips,
and no foreign data renders. Owner: automated browser suite.

### Area 7: AGE-gated test suite

Run SDK AGE conformance, SOC projection, and migration tests with:

```powershell
Set-Location copilot-sdk
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "<non-default-disposable-dsn>"
$env:AGE_TEST_GRAPH = "protocol_v2_test_validation"
python -m pytest tests/graph/test_protocol_v2_conformance.py tests/graph/test_soc_age_projection_contract.py tests/test_migration_live_age.py -q --timeout=900 -rs
```

The conformance fixture requires integration, a non-default DSN, and a graph
prefix. [tests/graph/test_protocol_v2_conformance.py:44](../../tests/graph/test_protocol_v2_conformance.py:44) [tests/graph/test_protocol_v2_conformance.py:50](../../tests/graph/test_protocol_v2_conformance.py:50) [tests/graph/test_protocol_v2_conformance.py:58](../../tests/graph/test_protocol_v2_conformance.py:58)

Run CI and S2P AGE gates with their repository variables. Unexpected AGE skips
are failures; the seven explicitly feature-pending SDK tests are reported as
pending and are not counted as AGE passes.

Exists: test modules. Gap: one cross-repository runner with skip rejection.
Pass: expected AGE tests pass, unexpected skip count zero, and no test targets
`soc_graph`. Owner: automated runner.

### Area 8: Destructive test safety

Prove no production graph mutation. The SOC stress suite requires both AGE and
`TEST_DESTRUCTIVE_AGE=1`. [gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:24](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:24) [gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:30](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:30)

Run with the flag absent and assert guarded skip. If enabled, require:

```text
GRAPH_BACKEND == age
TEST_DESTRUCTIVE_AGE == 1
AGE_TEST_DSN is non-default
AGE_TEST_GRAPH is disposable and not soc_graph
```

Exists: guards. Gap: 11 in-memory equivalents and static production-graph
target scan. Pass: no production mutation, all equivalents pass, disposable
graph cleanup succeeds. Owner: automated safety gate and operator approval.

### Area 9: Configuration completeness

Prove AGE-positive startup cannot fall back to SQLite and wrong or missing
domain/graph variables fail before writes. Test this matrix for all five:

```text
GRAPH_BACKEND=age, valid DSN, graph=soc_graph, expected backend=age -> PASS
GRAPH_BACKEND=age, missing DSN -> named startup failure
backend=sqlite, expected_backend=age -> fail closed, no write
wrong domain or graph -> fail closed, no write
```

Exists: configuration consolidation Steps 1-5. Gap: Steps 6-8 and negative
matrix. Pass: all positive processes report AGE and all negative cases fail
before mutation. Owner: automated config matrix.

### Area 10: Recovery, rollback, and flip-back of reads

Rollback is an emergency-only test mode, not a default. Set
`CI_ALLOW_SQLITE_FALLBACK=1` explicitly in the rollback process; expected-backend
AGE fail-closed behavior remains the normal policy.

Before migration hash every SQLite DB and record counts and Decision IDs. Then:

```powershell
$env:CI_ALLOW_SQLITE_FALLBACK = "1"
$env:GRAPH_BACKEND = "sqlite"
python <copilot-start-command> --domain <D>
```

Assert SQLite health, preserved IDs/counts, and unchanged source hashes. Force
AGE connection failure, then perform the actual incident operation: un-flip
reads for a copilot already serving AGE, restart it with SQLite plus the
explicit override, and assert all read endpoints return the SQLite snapshot.
Afterward restore AGE configuration and assert AGE reads return the same
pre-incident IDs/counts.

The live migration tests create SQLite sources and verify output topology.
[tests/test_migration_live_age.py:83](../../tests/test_migration_live_age.py:83) [tests/test_migration_live_age.py:148](../../tests/test_migration_live_age.py:148)

Exists: retained SQLite sources and live migration topology tests. Gap: forced
outage, read flip-back, and hash-before/hash-after test. Pass: source unchanged,
SQLite emergency reads work, AGE restoration works, and no partial write is
reported committed.

The validation runner must be cross-platform: Python orchestration and
`subprocess`/HTTP clients are the portable implementation. PowerShell snippets
in this document are operator examples only; CI must provide equivalent
Windows, Linux, and macOS command adapters and use `pathlib`/`sys.executable`.

### Area 11: Data integrity and archive parity

For each domain and the union assert:

```text
active + archived == source total
verified AGE == verified SQLite
correct AGE == correct SQLite
Decision ID sets equal and unique
Outcome, receipt, checkpoint, entity, and evolution edges have valid sources
orphan and duplicate counts == 0
```

Run:

```powershell
Set-Location copilot-sdk
python scripts/phase_dual_parity.py
```

This is the active/archive parity entry point. [scripts/phase_dual_parity.py:1](../../scripts/phase_dual_parity.py:1)

Then run census and AGE conformance topology checks. Existing evidence includes
the migration tests and census; the gap is scheduled post-flip parity and an
ongoing orphan/duplicate monitor.

Pass: exact count/ID/edge parity and zero orphan/duplicate findings. Owner:
automated parity runner and operator sign-off.

### Area 12: Ungoverned write prevention

This adversarial area proves the failure mode that motivated the domain retrofit.

First run a read-only census and assert:

```text
count(Decision WHERE domain IS NULL) == 0
```

The census explicitly reports NULL-domain rows and SOC-domain rows.
[gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61) [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:83](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:83)

Next invoke every known raw/unguarded Decision write path in a disposable graph.
For each attempted write assert one of:

```text
write raises a domain-governance error before creating a node
OR created node has domain == caller domain
```

Assert no path creates a Decision with missing domain, and assert the write is
visible in exactly one domain. Exercise the raw path with governed writes on;
silence or an untagged row is FAIL. Do not weaken the production path to make
this test pass.

Exists: SOC predicate and write-stamping isolation test. Gap: explicit raw-path
adversarial attempt and zero-NULL live census gate. Pass: both assertions for
every known raw writer. Owner: automated adversarial test.

### Area 13: Behavioral output equivalence

Counts and IDs alone do not prove behavior. For a fixed, versioned sample of
score requests, execute each request against equivalent SQLite and AGE states
from the same source snapshot. Assert:

```text
action_AGE == action_SQLite
confidence_AGE == confidence_SQLite within 1e-9
probabilities_AGE == probabilities_SQLite within 1e-9 per element
factor vector and category mapping are equal
```

Run the sample before flip, after AGE startup, and after restart. Include cold
start (no in-memory scorer state) and warm start. Any mismatch is a blocker,
even when count/ID parity passes.

Existing migration tests prove structural output topology, not score output.
[tests/test_migration_live_age.py:271](../../tests/test_migration_live_age.py:271)
Gap: fixed request corpus and dual-backend score comparison. Pass: every field
matches tolerance on every sample, with zero errors. Owner: automated parity
runner.

## 3. Validation runner design

Implement a future `scripts/validate_age_migration.py`; this document does not
add it. It must be cross-platform Python, invoked with:

```text
python scripts/validate_age_migration.py --level smoke --report out/age-validation.json
python scripts/validate_age_migration.py --level standard --report out/age-validation.json
python scripts/validate_age_migration.py --level comprehensive --report out/age-validation.json
```

Use `sys.executable`, `pathlib`, subprocess argument arrays (never shell-only
syntax), and an OS adapter for environment setup. PowerShell, Bash, and CI YAML
wrappers may call the same Python runner.

Required options: `--level`, `--report`, `--domains`, `--age-dsn`, `--graph`,
and `--test-graph`. Refuse AGE-mutating levels without a disposable test graph,
with `test_graph == soc_graph`, or with missing DSN. Redact credentials.

Smoke runs health, census baseline, V/store parity, NULL-domain census,
read-only isolation, and duplicate/orphan checks. It must not score, learn,
archive, reset, or delete the shared graph.

Standard runs smoke, disposable AGE-gated SDK/CI/S2P/SOC tests, per-domain
cycles, SOC API cycle, contention, parity, census, configuration-negative, and
destructive safety checks. Unexpected AGE skips are failures.

Comprehensive runs standard plus five-copilot launch, Playwright (Trading with
`--workers=1`), concurrent five-domain and same-domain contention, performance,
behavioral score parity, rollback flip-back, and full integrity checks.

The report must contain run ID, timestamps, level, redacted DSN, graph names,
area statuses, commands, assertions, stdout references, durations, baseline
and V checkpoints, event ledger, counts, parity results, score samples,
latencies, rollback hashes, skip classifications, and overall status.

Overall PASS requires `failed == 0`, `blocked == 0`, unexpected `skipped == 0`,
and every required area for the selected level PASS.

## 4. Validation schedule

Smoke runs after every `demo.py` launch and before a demo is presented.
Standard runs before graph-code commits, migrations, flips, or reset changes.
Comprehensive runs before release, demo recording, and any AGE index/query-plan
change. Post-flip smoke is daily; standard parity is per deployment;
comprehensive is monthly and before each release candidate.

## 5. Existing coverage map

These are conservative area-level estimates, not production metrics:

| Area | Existing coverage | Priority gap |
|---|---:|---|
| Domain isolation | 70% | live five-domain and browser proof |
| V and store parity | 35% | baseline/event reconciliation and adapter parity |
| Full launch | 25% | automated five-process cycle |
| Cross-domain writes | 50% | SOC API, same-domain contention, overlap |
| Performance | 35% | executable benchmark at explicit threshold |
| Playwright | 0% post-flip | all five suites; Trading serial workers |
| AGE suite | 65% | unified cross-repo runner and skip rejection |
| Destructive safety | 55% | 11 in-memory equivalents |
| Configuration | 55% | negative matrix and fallback proof |
| Rollback | 20% | override, outage, and read flip-back |
| Data integrity | 60% | ongoing parity/monitor |
| Ungoverned writes | 20% | adversarial raw writer test |
| Output equivalence | 0% | fixed SQLite/AGE score corpus |

The weighted planning estimate is 39%. It must not be presented as a measured
production metric; the validation artifact replaces it with evidence.

## 6. Implementation order

1. Build the cross-platform runner schema, refusal rules, redaction, and
   baseline/event ledger.
2. Add census baseline, `store.count_verified("soc")` parity, NULL-domain
   adversarial checks, and read-only isolation.
3. Add disposable AGE allocation and SDK/CI/S2P AGE suite orchestration.
4. Add real SOC API cycle, four non-SOC SDK cycles, same-domain contention,
   and five-domain concurrent writes.
5. Add configuration-negative and destructive safety gates.
6. Add active/archive parity, duplicate/orphan checks, and scheduled monitor.
7. Add fixed-sample SQLite/AGE score output equivalence.
8. Add explicit 193 ms p95 benchmark and index-plan evidence.
9. Add rollback with `CI_ALLOW_SQLITE_FALLBACK=1`, forced outage, and read
   flip-back/restore.
10. Add five Playwright suites, with Trading `--workers=1`.
11. Make comprehensive output a release gate.

## 7. Production-ready pass criteria

All criteria below must pass in one comprehensive report:

1. Five health endpoints return 200 and identify AGE plus `soc_graph`.
2. Census has zero NULL-domain Decisions and no unknown domains.
3. `census_baseline` is recorded at run start; every later V satisfies
   `V_census >= census_baseline`, and the delta equals the event ledger.
4. `V_census == store.count_verified("soc")` at every checkpoint.
5. Non-SOC activity produces zero SOC V increase.
6. All 10 SOC isolation tests pass with zero skips.
7. Four non-SOC 40-cycle gates and the real SOC API cycle pass.
8. Same-domain contention increments V exactly once per successful verification,
   with no lost update, torn read, or 500.
9. Five-domain concurrency has zero cross-domain Decision, Outcome, receipt,
   category, or count leakage.
10. Every known raw writer rejects or correctly stamps domain; NULL-domain count
    remains zero after the adversarial attempts.
11. Active/archive/verified/correct counts, IDs, and topology match SQLite.
12. Fixed score samples match SQLite action, confidence, probabilities, factors,
    and category mapping within stated tolerances.
13. Domain and archived indexes exist; p95 <= 193 ms for 250 SOC requests and
    error count is zero.
14. All required AGE tests pass with no unexpected skips; pending feature tests
    are separately reported.
15. All five post-flip Playwright suites pass; Trading uses `--workers=1` and
    no foreign data renders.
16. Configuration negatives fail closed and AGE-positive processes do not open
    SQLite.
17. Destructive tests cannot target `soc_graph`; disposable cleanup succeeds.
18. With explicit `CI_ALLOW_SQLITE_FALLBACK=1`, one AGE-serving copilot can
    flip reads to SQLite during forced AGE failure and then restore AGE reads.
19. Source SQLite hashes/counts remain unchanged through migration and rollback.
20. The evidence report is retained with redacted credentials and operator signoff.

Any failure, unexplained skip, adapter/census disagreement, ungoverned write,
score mismatch, or missing evidence is NO-GO. A smoke or standard PASS cannot
waive a comprehensive failure.

## 8. Review finding disposition

1. Blocker 1 resolved: canonical live census baseline supersedes conflicting
   historical 4,899 snapshot; discrepancy is explained in section 1.1.
2. Blocker 2 resolved: V uses `>= census_baseline` plus traceable event deltas.
3. Blocker 3 resolved: Area 12 tests NULL-domain absence and raw-write behavior.
4. Finding 4 resolved: Area 13 compares actual score outputs, not only counts.
5. Finding 5 resolved: census and scorer store count are equal mandatory gates;
   the known adapter discrepancy is an explicit blocker.
6. Finding 6 resolved: Area 4 adds same-domain contention and exact V delta.
7. Finding 7 resolved: SOC is explicitly exempted from SDK cycle gate and uses
   its actual API plus learning-health/conservation proof.
8. Finding 8 resolved: rollback requires explicit emergency
   `CI_ALLOW_SQLITE_FALLBACK=1`.
9. Finding 9 resolved: p95 threshold is explicitly 193 ms for 250 requests.
10. Finding 10 resolved: rollback tests AGE-to-SQLite read flip-back and AGE
    restoration, not merely process restart.
11. Finding 11 resolved: runner is cross-platform Python; shell snippets are
    operator examples.
12. Finding 12 resolved: Trading Playwright command requires `--workers=1`.
