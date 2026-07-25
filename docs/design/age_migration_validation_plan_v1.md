# AGE Shared-Graph Migration End-to-End Validation Plan v1

Status: Proposed validation contract
Authority: Copilot SDK migration validation plan
Date: 2026-07-25
Scope: five copilots on the shared AGE graph `soc_graph`

This document is executable guidance. A result is not a pass unless the command
and assertion named here produce captured evidence. Commands are written for
PowerShell on Windows; replace `python` with the repository virtual-environment
interpreter when required. No validation command may target a production graph
for a test that creates, updates, archives, or deletes data.

## 1. Executive summary

This plan validates that the SQLite-to-AGE migration is behaviorally equivalent,
domain-isolated, restart-safe, observable, and reversible. It covers the shared
Decision graph, all five domain backends, the direct API paths, the SDK adapters,
the browser clients, and the operational scripts used at flip time.

Production-ready means every mandatory gate in section 7 passes against a named
AGE graph, with an evidence artifact containing command, environment summary,
timestamp, counts, and PASS/FAIL result. A skipped test is not a pass. A failed
or unavailable gate is a no-go.

The highest-risk claims are: exact domain partitioning across all reads and
writes; stable SOC V; no SQLite fallback; correct active/archive accounting;
concurrent writes from five copilots; latency at 33K Decision nodes; browser
behavior after flip; and a tested rollback path.

## 2. Validation areas

Every area below specifies the proof, current implementation, gap, pass
criteria, and owner. The cited files are the existing executable evidence.

### Area 1: Domain isolation

What to prove:

1. Every Decision read for domain X excludes every other domain.
2. A score plus learn in copilot A increases only A's counts and does not alter
   any B category, V, verified, correct, archive, or history result.
3. Every write has the caller's domain and every query uses an exact equality,
   never a NULL-as-SOC compatibility branch.

How to prove:

Run the existing SOC isolation suite:

```powershell
Set-Location gen-ai-roi-demo-v4-v50\backend
python -m pytest tests/test_soc_domain_isolation.py -v --timeout=60
```

The suite must report 10 passed. Its assertions cover the SOC baseline, four
foreign domains, category and outcome aggregates, SOC write stamping, the exact
predicate, archive selection, explorer output, mutation output, and
GraphSnapshot. [gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_isolation.py:138](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_isolation.py:138)

Then run one real five-domain cycle per domain on disposable AGE test graphs or
disposable domain partitions. For each domain, assert:

```text
count(Decision WHERE domain = D AND decision_id = generated_id) = 1
count(Decision WHERE domain != D AND decision_id = generated_id) = 0
count(Outcome for generated_id) = 1 after learn
```

The existing cycle gate already verifies the decision ID with the requested
domain and submits two learns per cycle. [scripts/phase_cycle_gate.py:7](../../scripts/phase_cycle_gate.py:7) [scripts/phase_cycle_gate.py:21](../../scripts/phase_cycle_gate.py:21) [scripts/phase_cycle_gate.py:25](../../scripts/phase_cycle_gate.py:25)

Exists today: 10 deterministic SOC tests and per-domain cycle verification.

Missing: Playwright isolation for each copilot and one simultaneous five-copilot
cycle test. The current SOC tests use a query-aware in-memory client, so they do
not prove AGE query execution or simultaneous transaction behavior.

Pass criteria: all 10 isolation tests pass; five real cycles pass; no generated
ID appears under another domain; no foreign ID appears in any returned list.

Owner: automated CI for the test suite; release operator for disposable AGE
multi-domain and simultaneous-cycle evidence.

### Area 2: V_soc stability

What to prove:

```text
V_soc = 4,862
```

after startup, restart, preseed, reset, and a score-plus-learn cycle. V counts
verified active SOC Decisions only; archived or foreign Decisions must not alter
it.

How to prove:

Run the read-only census before and after each lifecycle operation:

```powershell
Set-Location gen-ai-roi-demo-v4-v50\backend
python scripts/soc_domain_census.py
```

The census prints SOC totals, verified, correct, archived, and active values.
[gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:61) [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:92](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:92) [gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:121](../../../gen-ai-roi-demo-v4-v50/backend/scripts/soc_domain_census.py:121)

Capture `V_soc`, `correct_soc`, active SOC decisions, archived SOC decisions,
and the category histogram in the report. Assert `V_soc == 4862` after each
operation and assert that a new verified cycle changes it only by the expected
number of newly verified SOC Decisions.

Exists today: the census queries and the GraphSnapshot source methods. The
isolation suite checks SOC-only counts in a fixture.

Missing: an automated lifecycle regression that runs preseed, restart, reset,
score, learn, and re-census; no current test proves 4,862 across the full
`demo.py` lifecycle.

Pass criteria: every checkpoint equals 4,862, except an explicitly recorded
delta caused by the test's own verified event; the category histogram changes
only for the test category; no foreign or archived row contributes.

Owner: automated runner; operator reviews the census artifact.

### Area 3: Full platform launch

What to prove:

1. All five copilots start successfully.
2. Every health endpoint responds HTTP 200 with a healthy/ready payload.
3. Every process reports AGE as its selected backend and the expected graph
   name; no process silently falls back to SQLite.
4. Stop removes all child processes cleanly.

How to prove:

Run the demo lifecycle in a disposable environment:

```powershell
Set-Location copilot-sdk
python demo.py --no-browser
python demo.py --status
python demo.py --verify
python demo.py --stop
```

For each copilot assert: process is running after the launch command; the configured
health URL returns 200; the response backend field is `age`; the graph field is
`soc_graph`; and `--stop` returns success with no owned process remaining.
The launcher defines `--stop`, `--status`, `--verify`, and `--no-browser`.
[demo.py:1111](../../demo.py:1111) [demo.py:1138](../../demo.py:1138) [demo.py:1141](../../demo.py:1141)
The existing phase scripts obtain domain configuration and API paths from
`phase_config.py`. [scripts/phase_cycle_gate.py:5](../../scripts/phase_cycle_gate.py:5) [scripts/phase_flip_verify.py:5](../../scripts/phase_flip_verify.py:5)

Exists today: `demo.py --status` is the operational status entry point supplied
by the platform.

Missing: one automated launch-health-verify-stop test that asserts all five
processes and backend selections.

Pass criteria: five health checks pass, five AGE backend checks pass, verify
passes, and stop leaves no owned process.

Owner: release operator today; validation runner after implementation.

### Area 4: Cross-domain write safety

What to prove:

For each domain D and generated decision ID X:

```text
Decision(X).domain == D
Outcome(X).domain == D
count(Decision WHERE decision_id = X AND domain != D) == 0
count(Outcome WHERE decision_id = X AND domain != D) == 0
```

How to prove:

Run the existing per-domain gate:

```powershell
Set-Location copilot-sdk
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "<disposable-dsn>"
$env:AGE_TEST_GRAPH = "<disposable-graph>"
python scripts/phase_cycle_gate.py --domain soc --cycles 40
```

Repeat for `trading`, `purchasing`, `dataops`, and `s2p`, using each domain's
configured API and graph. The gate posts score/learn requests and checks the
domain-qualified Decision count. [scripts/phase_cycle_gate.py:8](../../scripts/phase_cycle_gate.py:8) [scripts/phase_cycle_gate.py:21](../../scripts/phase_cycle_gate.py:21) [scripts/phase_cycle_gate.py:25](../../scripts/phase_cycle_gate.py:25)

After the sequential runs, start one concurrent task per copilot and assert the
same predicates while all five tasks overlap. Use unique IDs per domain and a
single report row per task.

Exists today: 40-cycle per-domain gate.

Missing: simultaneous multi-copilot cycles and a cross-domain assertion over
all five outputs.

Pass criteria: all five sequential gates pass and the concurrent run produces
no cross-domain Decision, Outcome, receipt, or count.

Owner: automated validation runner.

### Area 5: Performance

What to prove:

At the migrated 33,048-node graph, the SOC score path has p50 and p95 latency
no greater than the approved pre-migration baseline. The current baseline
target supplied for this migration is 193 ms at the 250-node benchmark point;
the report must record the workload and percentile rather than claiming a
different magnitude.

Also prove both indexes exist on the physical AGE Decision relation:

```text
index(decision_domain_idx) exists
index(decision_archived_idx) exists
EXPLAIN scoped Decision query uses the domain index or documents planner choice
```

How to prove:

Create or verify indexes with:

```powershell
Set-Location copilot-sdk
python scripts/create_age_indexes_v2.py
```

The script creates domain and archived indexes using AGE-compatible strategies
and lists the resulting PostgreSQL indexes. [scripts/create_age_indexes_v2.py:1](../../scripts/create_age_indexes_v2.py:1) [scripts/create_age_indexes_v2.py:41](../../scripts/create_age_indexes_v2.py:41) [scripts/create_age_indexes_v2.py:93](../../scripts/create_age_indexes_v2.py:93)

Run a new benchmark script with 250 representative SOC score requests and
record p50, p95, p99, errors, graph size, and query plans. Assert p95 is at or
below the approved baseline and error rate is zero.

Exists today: index creation script.

Missing: formal repeatable latency benchmark and a recorded 33K-node baseline
comparison.

Pass criteria: both indexes verified; p95 <= 193 ms for the named 250-request
workload, unless an approved baseline artifact supersedes that target; zero
errors and no unbounded query plan.

Owner: automated benchmark; operator approves any baseline change.

### Area 6: Playwright coverage

What to prove:

For each copilot tab, browser-visible health, score, learn, history, category,
and conservation values come from its AGE domain. SOC must show only SOC
categories and decisions. S2P, Trading, Purchasing, and DataOps must each show
their own domain data after flip.

How to prove:

Run the repository's Playwright commands for each app after the five backends
are started. Each spec must assert:

```text
response.status == 200
response.backend == "age"
response.graph == "soc_graph"
every returned decision.domain == expected_domain
every displayed category is in the seeded expected-domain category set
```

Use stable `data-testid` selectors. The SDK testing rules prohibit
position-dependent selectors. [CLAUDE.md:48](../../CLAUDE.md:48)

Exists today: no post-flip Playwright proof is established by the migration
plan.

Missing: all five post-flip specs, including negative foreign-domain assertions
and score-to-learn browser flows.

Pass criteria: every required spec passes with no skipped post-flip test and no
foreign Decision/category visible.

Owner: automated browser suite.

### Area 7: AGE-gated test suite

What to prove:

All 73 AGE-gated SDK tests, 11 CI AGE-gated tests, and 10 S2P live-AGE tests
pass when AGE is available. Feature-gated tests remain separately reported and
cannot be counted as AGE validation.

How to prove:

SDK protocol and migration command:

```powershell
Set-Location copilot-sdk
$env:AGE_INTEGRATION = "1"
$env:AGE_TEST_DSN = "<non-default-disposable-dsn>"
$env:AGE_TEST_GRAPH = "protocol_v2_test_validation"
python -m pytest tests/graph/test_protocol_v2_conformance.py tests/graph/test_soc_age_projection_contract.py tests/test_migration_live_age.py -q --timeout=900 -rs
```

The conformance fixture requires AGE integration, a non-default DSN, and a
graph name beginning `protocol_v2_test`. [tests/graph/test_protocol_v2_conformance.py:44](../../tests/graph/test_protocol_v2_conformance.py:44) [tests/graph/test_protocol_v2_conformance.py:50](../../tests/graph/test_protocol_v2_conformance.py:50) [tests/graph/test_protocol_v2_conformance.py:58](../../tests/graph/test_protocol_v2_conformance.py:58)

Run the CI and S2P commands from their repositories with their documented AGE
variables, and capture a zero-failure summary. Never run destructive tests
against `soc_graph`.

Exists today: test modules and AGE fixtures.

Missing: one scripted runner that sets validated variables, allocates disposable
graphs, runs all three repositories, and rejects skipped AGE tests.

Pass criteria: all expected AGE tests pass; observed AGE skip count is zero;
feature-pending count is reported separately; no test targets `soc_graph`.

Owner: automated validation runner.

### Area 8: Destructive test safety

What to prove:

No test mutates the shared production graph. Destructive AGE tests may run only
when explicitly enabled and only against a disposable graph. Every destructive
scenario has a non-destructive in-memory equivalent.

How to prove:

Run the SOC stress suite without the destructive flag and assert collection is
skipped, not executed against AGE:

```powershell
Set-Location gen-ai-roi-demo-v4-v50\backend
Remove-Item Env:TEST_DESTRUCTIVE_AGE -ErrorAction SilentlyContinue
python -m pytest tests/test_graph_contract_stress.py -q -rs --timeout=60
```

The suite gates on `GRAPH_BACKEND=age` and `TEST_DESTRUCTIVE_AGE=1`. [gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:24](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:24) [gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:30](../../../gen-ai-roi-demo-v4-v50/backend/tests/test_graph_contract_stress.py:30)

If the destructive suite is intentionally enabled, require all of:

```text
GRAPH_BACKEND == age
TEST_DESTRUCTIVE_AGE == 1
AGE_TEST_DSN is non-default
AGE_TEST_GRAPH is disposable and not soc_graph
```

Exists today: explicit guards.

Missing: 11 in-memory equivalents for the guarded destructive cases and a
static assertion that no destructive command contains `soc_graph`.

Pass criteria: safety guard passes; production graph is never mutated; all
11 equivalent tests pass; any enabled destructive run leaves its disposable
graph removable and records cleanup.

Owner: automated safety checks; operator approval for destructive runs.

### Area 9: Configuration completeness

What to prove:

1. An expected AGE backend cannot silently instantiate SQLite.
2. Missing or conflicting graph/domain variables fail before a write.
3. Every copilot names `GRAPH_BACKEND=age`, `GRAPH_NAME=soc_graph`, the expected
   domain, and a non-empty AGE DSN at startup.

How to prove:

For every app, run a config-negative matrix:

```text
GRAPH_BACKEND=age, GRAPH_NAME=soc_graph, valid AGE DSN -> startup PASS
GRAPH_BACKEND=age, missing DSN -> startup FAIL with named variable
GRAPH_BACKEND=sqlite, expected_backend=age -> startup FAIL, never write
wrong domain -> startup FAIL, never write
```

Then inspect the process startup report and issue one score request; assert the
selected backend and graph before accepting the response.

Exists today: graph configuration consolidation Steps 1-5, as supplied by the
migration status.

Missing: Steps 6-8, negative configuration tests, and a runtime fallback guard
for all five apps.

Pass criteria: all negative cases fail closed; all positive cases report AGE;
no SQLite file is created or opened in the AGE positive case.

Owner: automated config matrix.

### Area 10: Recovery and rollback

What to prove:

1. SQLite source databases remain intact after migration and validation.
2. Stopping AGE and restarting a copilot with its SQLite configuration restores
   score, learn, history, and counts from the preserved source.
3. AGE failure does not corrupt the source or cause partial silent writes.

How to prove:

Before migration, hash every source DB and record active, archived, verified,
correct, and Decision ID counts. After migration and after a forced AGE
connection failure, compare hashes and SQLite counts exactly. Restart one
copilot with `GRAPH_BACKEND=sqlite` and assert its health reports SQLite and its
history contains the pre-migration Decision IDs.

The migration tests create source SQLite databases and verify output topology;
the live fixture is explicitly separate from `soc_graph`. [tests/test_migration_live_age.py:83](../../tests/test_migration_live_age.py:83) [tests/test_migration_live_age.py:148](../../tests/test_migration_live_age.py:148)

Exists today: SQLite databases are retained and migration tests cover live
topology.

Missing: formal hash-before/hash-after rollback test and a forced AGE outage
restart test for one copilot.

Pass criteria: source hashes and counts are unchanged; SQLite restart is
successful; no partial AGE write is reported as committed.

Owner: automated disposable-environment test; operator reviews rollback report.

### Area 11: Data integrity

What to prove:

For each domain and for the union of domains:

```text
active + archived == migrated source total
verified AGE == verified SQLite
correct AGE == correct SQLite
all Decision IDs unique within the domain
all expected Outcome/receipt/checkpoint edges have one valid source node
orphan Decision and duplicate-ID counts == 0
```

How to prove:

Run the parity entry point:

```powershell
Set-Location copilot-sdk
python scripts/phase_dual_parity.py
```

This is the compatibility entry point for active and archived parity. [scripts/phase_dual_parity.py:1](../../scripts/phase_dual_parity.py:1)

Run the five-domain census and capture active/archive/verified/correct counts.
Run AGE conformance helpers that check outcome, receipt, checkpoint, entity,
and evolution topology. Assert every count and Decision ID set is equal to the
recorded source artifact.

Exists today: dual parity entry point, migration topology tests, and domain
census.

Missing: post-flip scheduled parity and an ongoing duplicate/orphan monitor.

Pass criteria: exact count and ID equality, zero orphan/duplicate findings, and
no unexplained parity drift.

Owner: automated parity runner; operator signs the artifact.

## 3. Validation runner design

Add a future operational runner at `scripts/validate_age_migration.py`. This is
design only; this plan does not add the script.

### Interface

```powershell
python scripts/validate_age_migration.py --level smoke --report out/age-validation.json
python scripts/validate_age_migration.py --level standard --report out/age-validation.json
python scripts/validate_age_migration.py --level comprehensive --report out/age-validation.json
```

Required options:

```text
--level {smoke,standard,comprehensive}
--report PATH
--domains soc,trading,purchasing,dataops,s2p (default all five)
--age-dsn VALUE or AGE_TEST_DSN environment variable
--graph NAME (default soc_graph for read-only checks)
--test-graph NAME (required for AGE-mutating tests; never soc_graph)
```

The runner must refuse to start if an AGE-mutating level has no disposable
`--test-graph`, if `--test-graph == soc_graph`, or if required DSN variables are
missing. It must redact DSN passwords in console and report output.

### Smoke level

Run in this order:

1. Verify five health endpoints and assert HTTP 200, backend `age`, graph
   `soc_graph`, and expected domain.
2. Run a read-only five-domain census and assert no unknown domain and
   `V_soc == 4862`.
3. Run the SOC isolation test suite and assert 10 passed, 0 failed, 0 skipped.
4. Run a read-only graph query asserting duplicate Decision IDs and orphan
   Outcome nodes are zero.

Smoke may run against the shared graph only for read-only checks. It must not
score, learn, archive, reset, or delete.

### Standard level

Run smoke, then:

1. Allocate or verify a disposable AGE test graph.
2. Set `AGE_INTEGRATION=1`, `AGE_TEST_DSN`, and a test graph name.
3. Run SDK AGE conformance, SOC projection, and migration tests.
4. Run CI and S2P AGE-gated suites with their repository-specific variables.
5. Run `phase_dual_parity.py` and five-domain census.
6. Run one 40-cycle gate per domain and `phase_flip_verify.py` per domain.
7. Run the configuration-negative matrix and destructive safety guard.

Standard must reject any unexpected skip. It may report the seven feature-gated
tests separately as `not_applicable_pending`, never as PASS.

### Comprehensive level

Run standard, then:

1. Start all five copilots and run all post-flip Playwright specs.
2. Run concurrent score-plus-learn tasks across all five domains.
3. Run the 33K-node latency benchmark and query-plan checks.
4. Run rollback/restart and source hash comparison.
5. Run full active/archive parity and orphan/duplicate checks.

### Evidence report

The report must be JSON and human-readable Markdown with:

```text
schema_version
run_id
started_at, completed_at
level
domains
age_dsn_redacted
graph_name, test_graph_name
git_revision (read-only metadata if available; no runner git operation)
areas: [{id, name, status, commands, assertions, stdout_ref, duration_ms}]
counts: {passed, failed, skipped, blocked}
decision_counts_by_domain
v_soc_checkpoints
latency_percentiles
rollback_hashes
overall_status
```

`overall_status` is PASS only when every required area for the selected level is
PASS and `failed == 0`, `blocked == 0`, and unexpected `skipped == 0`.

## 4. Validation schedule

Smoke runs on every `demo.py` start, after processes report healthy and before
the demo is presented.

Standard runs before any commit touching graph schema, graph store, migration,
domain predicates, backend selection, or reset behavior.

Comprehensive runs before every release, migration flip, customer demo
recording, or change to AGE indexes, query plans, or browser contracts.

After a production flip, schedule read-only smoke daily, standard parity on
each deployment, and comprehensive monthly and before every release candidate.

## 5. Existing coverage map

Percentages below measure executable proof of the required assertions, not the
number of files. They are intentionally conservative.

| Area | Covered today | Gap | Priority |
|---|---:|---|---|
| Domain isolation | 70% | no five-copilot PW or simultaneous AGE test | P0 |
| V_soc stability | 35% | no lifecycle regression at 4,862 | P0 |
| Full launch | 25% | no automated launch-health-stop cycle | P0 |
| Cross-domain writes | 55% | no simultaneous five-domain cycle | P0 |
| Performance | 25% | no formal 33K benchmark or plan evidence | P1 |
| Playwright | 0% post-flip | all five post-flip specs missing | P0 |
| AGE-gated suite | 65% | no unified env/skip-rejecting runner | P0 |
| Destructive safety | 55% | 11 in-memory equivalents missing | P1 |
| Configuration | 55% | Steps 6-8 and negative matrix missing | P0 |
| Recovery/rollback | 30% | no forced outage and hash test | P1 |
| Data integrity | 60% | no ongoing post-flip monitor | P0 |

Weighted by the 11 areas, existing end-to-end validation coverage is 43%.
This is a planning estimate, not a measured product metric; the runner must
replace it with report-backed evidence.

## 6. Implementation order

1. Define the validation report schema and runner refusal rules. Dependency:
   none. Scope: small, SDK repo. Test: unit-test level selection, redaction,
   missing variables, and production-graph refusal.
2. Implement smoke health, census, V, duplicate, orphan, and isolation checks.
   Dependency: step 1. Scope: medium, SDK plus backend. Test: disposable AGE
   read-only fixture and the 10 SOC isolation tests.
3. Implement AGE environment allocation and standard test orchestration.
   Dependency: step 1. Scope: medium, SDK/CI/S2P repositories. Test: all
   expected AGE tests pass with zero unexpected skips.
4. Add five-domain concurrent cycle and post-cycle assertions. Dependency:
   steps 2-3. Scope: medium. Test: generated IDs, domain and outcome edge
   assertions, repeated run for determinism.
5. Add config-negative and destructive safety gates. Dependency: step 1.
   Scope: medium across five app launchers. Test: no SQLite fallback and no
   shared-graph mutation.
6. Add parity, archive, rollback, and ongoing integrity checks. Dependency:
   steps 2-4. Scope: medium. Test: exact count/ID/hash equality.
7. Add the 33K benchmark and index-plan evidence. Dependency: stable AGE
   graph and step 2. Scope: medium. Test: repeated p50/p95/p99 runs and
   recorded EXPLAIN output.
8. Add all five post-flip Playwright suites. Dependency: steps 2-5. Scope:
   large, five app repositories. Test: browser health, score, learn, history,
   category, and domain-negative assertions.
9. Make comprehensive validation a release gate. Dependency: steps 1-8.
   Scope: small operational integration. Test: one clean report with all
   mandatory areas PASS and no unexpected skips.

## 7. Production-ready pass criteria

AGE migration is production-ready only when all assertions below are true in a
single comprehensive report:

1. Five health endpoints return 200 and identify AGE plus `soc_graph`.
2. Census reports exactly the approved five-domain totals and no unknown or
   NULL domain rows.
3. `V_soc == 4862` at startup, after restart, after preseed, and after reset;
   any test-created delta is explicitly reconciled.
4. All 10 SOC isolation tests pass with zero skips.
5. Five sequential 40-cycle gates pass.
6. One simultaneous five-domain cycle passes with zero foreign Decision,
   Outcome, receipt, or category results.
7. Active/archive/verified/correct counts and Decision ID sets match SQLite
   source artifacts exactly for every domain.
8. Duplicate Decision IDs and orphan graph nodes/edges are zero.
9. Domain and archived indexes exist and the benchmark p95 meets the approved
   baseline; errors are zero.
10. All required AGE-gated SDK, CI, S2P, and SOC tests pass; unexpected AGE
    skips are zero; seven feature-pending tests are reported separately.
11. All five post-flip Playwright suites pass and show only expected domain
    data.
12. Configuration-negative tests fail closed and no AGE-positive process opens
    SQLite.
13. Destructive tests are either guarded or run only on a named disposable
    graph; the production graph is untouched.
14. SQLite source hashes and counts remain unchanged, and a forced AGE outage
    can restart one copilot on SQLite with its history intact.
15. The JSON and Markdown validation artifacts are retained with redacted
    credentials, commands, assertions, outputs, and operator sign-off.

Any failed, blocked, unexplained, or unexpectedly skipped assertion is a
NO-GO. A successful smoke or standard run cannot waive a comprehensive failure.
