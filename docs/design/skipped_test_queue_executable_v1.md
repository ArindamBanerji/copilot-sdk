# Skipped-Test Queue — Executable (scanned against the code mirror, 2026-08-11)
**For:** Codex / coding sessions. **Source:** the Aug-11 skipped-test queue (6 items, 9 tests, ~12-15d). This makes it executable and folds in code-scan findings. **Rule (unchanged, now enforced — see §4):** no skip without a queue ID; no queue ID without a skip; the ship PR removes the skip.

> **How to use:** I don't have the "SDK rows 1-8 / SOC PW rows 36-37" → test-name table, so each item gives a **grep anchor** to LOCATE the skipped test; add/verify its queue-ID skip reason, build, then remove the skip in the same PR (VERIFY).

---

## 1. Scan findings that change the queue (read first)
1. **PROTO-V2 is REUSE, not greenfield — likely < 3-5d.** The persistence outbox already exists and passes tests: `copilot_sdk/scoring/persistence_outbox.py` (`PersistenceOutbox`: `record_failure → drain → replay`, retry/abandon at `MAX_RETRIES=10`, schema-versioning, idempotency keys), wired into `CompoundingScorer._outbox`, with `test_persistence_outbox.py`, `test_outbox_decision_evolution.py`, and **`test_learn_finds_replayed_decision`** already exercising fail→queue→replay→learn. PROTO-V2's *new* work is the **Protocol-v2 service layer** over it: formal commit semantics, pending-sync status, **delayed V-increment**, and a replay **worker** (vs the current manual `drain()`). **Reuse surface:** `persistence_outbox.py`, `CompoundingScorer._outbox`, `drain()`, the store `write_*` methods.
2. **SOC-WRITE-PATH's write side already exists.** `write_evolution_event(...)` (TRIGGERED_EVOLUTION edges, shadow-batch params) is implemented on the stores. The *new* work is the **read-only projection** that verifies the triggered-evolution write — a thin verifier, not the write path.
3. **SHADOW-MAP's shadow infra already exists.** `ShadowDecision` nodes are real (V-SHADOW-SYNTHETIC data, ~1,500 nodes feeding the F9 analyst-benchmarking route) and `app.services.shadow_runner.fill_shadow_outcome` exists. The *new* work is the **ShadowDecision→Observation promotion rules** + mapping — not the shadow machinery.
4. **The V-integrity cluster.** PROTO-V2 (delayed V-increment), SOC-BACKFILL (no double-count on V), and the conservation `q` (binary over the *verified* count — `conservation_utils.py`, `rl_design_v4`) all touch one invariant: **V = distinct verified decisions, counted once.** Do not build these against divergent V-increment semantics — see §2.

## 2. Ordering / dependency verification
- **PROTO-V2 ↔ SOC-BACKFILL — CONFIRM the shared V-increment contract before bundling.** Both touch how V increments (PROTO-V2 delays it on async commit; SOC-BACKFILL must not double-count it). Either build SOC-BACKFILL against PROTO-V2's committed V-increment semantics, or confirm they're genuinely independent (backfill = historical reconciliation; PROTO-V2 = forward commit). **Do not schedule SOC-BACKFILL as an independent bundle until this is confirmed.**
- **PROTO-V2 after RL-SDK #10 — confirmed correct.** Both touch `CompoundingScorer`'s persistence contract; sequencing avoids a double rework.
- **AGE-STRESS — elevate above "anytime."** It is the direct **diagnostic for the intermittent 30-43s S2P score-path stalls** under concurrent workers (pool-exhaustion: shared AGE instance, `AGE_POOL_MAX_SIZE=5`, no PgBouncer — per the perf-lock analysis). At 2d it de-risks the reliability story the S2P pilot rests on. **VERIFY the dependency claim:** confirm the "pool lifecycle fix done (v0.7.11-ci)" covers *shared-instance exhaustion*, not only single-graph disposal — if it doesn't, AGE-STRESS is blocked on the real pool fix, not merely enabled by it.
- **S2P-DOMAIN-PANEL — share a harness with the perf-lock fault-injection.** Its "S2P down" fault-injection is the same surface as fail-closed-under-pool-exhaustion; build one harness, not two.
- Independent, parallelizable across Codex sessions: **SOC-WRITE-PATH, SHADOW-MAP, S2P-DOMAIN-PANEL** (SOC-WRITE-PATH also quietly unblocks the demo's TRIGGERED_EVOLUTION credibility — consider pulling earlier than its 2d size suggests).

## 3. Executable per-item specs
**PROTO-V2** · SDK rows 1-4 (4 tests) · after RL-SDK #10 · confirm V-contract vs SOC-BACKFILL
- LOCATE: `grep -rn "PROTO-V2\|protocol.v2\|commit semantics\|delayed.*V.increment\|replay.*worker\|pending.sync" tests/` → the 4 skipped tests.
- REUSE: `persistence_outbox.py`, `CompoundingScorer._outbox`, `drain()`, store `write_*`.
- BUILD: Protocol-v2 service layer over the outbox — write→pending→confirmed commit semantics; pending-sync status surface; **V increments only on confirmed commit** (not on pending); background replay **worker**.
- VERIFY: the 4 skips removed + tests green; **V increments exactly once per verified decision across a fail→queue→replay cycle** (extend `test_learn_finds_replayed_decision`); no double-count.

**AGE-STRESS** · SDK row 5 (1 test) · dep: pool lifecycle fix (VERIFY scope, §2)
- LOCATE: `grep -rn "AGE-STRESS\|cross.domain.*concurrency\|concurrency.*stress\|disposable graph" tests/`.
- BUILD: cross-domain AGE concurrency stress harness — isolation, serialization, cleanup on a disposable graph; **exercise fail-closed under pool exhaustion** (shared instance, MAX_SIZE=5), not just isolation.
- VERIFY: skip removed + test green under concurrent workers; no 30-43s stall; pool exhaustion fails **closed**, does not hang.

**SOC-BACKFILL** · SDK row 6 (1 test) · dep: SOC-SEED-REDESIGN #9 + V-contract vs PROTO-V2 (§2)
- LOCATE: `grep -rn "SOC-BACKFILL\|canonical.*[Oo]utcome\|embedded.*canonical\|backfill" tests/`.
- BUILD: canonical SOC Outcome backfill — mixed embedded/canonical outcomes, idempotent, **no double-count on V**.
- VERIFY: skip removed + test green; V after backfill = distinct verified decisions (embedded+canonical de-duped).

**SOC-WRITE-PATH** · SDK row 7 (1 test) · independent
- LOCATE: `grep -rn "SOC-WRITE-PATH\|TRIGGERED_EVOLUTION\|forward.write\|read.only projection" tests/`.
- REUSE: `write_evolution_event(...)` / TRIGGERED_EVOLUTION already implemented.
- BUILD: the read-only projection that verifies the triggered-evolution write (a verifier over the evolution edges).
- VERIFY: skip removed + test green; the projection reproduces the write path's evolution edges.

**SHADOW-MAP** · SDK row 8 (1 test) · independent · 1d
- LOCATE: `grep -rn "SHADOW-MAP\|ShadowDecision\|Observation.*mapping\|promotion rule" tests/`.
- REUSE: `ShadowDecision` nodes + `shadow_runner.fill_shadow_outcome`.
- BUILD: ShadowDecision→Observation approved-mapping — define the promotion rules (when an approved shadow becomes an Observation), implement.
- VERIFY: skip removed + test green; approved shadows map to Observations per the rules.

**S2P-DOMAIN-PANEL** · SOC PW rows 36-37 (2 tests) · independent · share harness w/ perf-lock
- LOCATE: `grep -rn "S2P-DOMAIN-PANEL\|Domain Applicability\|Tab 6" tests/ e2e/` (Playwright/TS).
- BUILD: Domain Applicability panel render in Tab 6; fault-injection test with S2P down.
- VERIFY: both skips removed + tests green; panel renders; with S2P down the panel degrades **closed** (no hang), reusing the perf-lock fail-closed harness.

## 4. The skip-ID rule — operationalized
- **Format (every one of the 9 tests):** Python `@pytest.mark.skip(reason="<QUEUE-ID>: <what to build>")`; Playwright/TS `test.skip(/* <QUEUE-ID>: <what to build> */)`.
- **CI lint (add):** fail the build if any `skip`/`@pytest.mark.skip` lacks a `<QUEUE-ID>:` prefix, or references a QUEUE-ID with no open queue item. Enforces "no skip without a queue ID; no queue ID without a skip."
- **On ship:** the queue item's PR removes its skip(s) in the **same PR** (the VERIFY step). When a QUEUE-ID's last skip is removed, close the queue item.

## 5. What I could not close (needs the coding session / live repo)
- The exact row→test-name mapping (no source table here) — resolved by the LOCATE greps.
- The **AGE-STRESS pool-fix scope** (does v0.7.11-ci cover shared-instance exhaustion?) — one grep on the pool lifecycle code; gates whether AGE-STRESS is *enabled* or still *blocked*.
- The **PROTO-V2 ↔ SOC-BACKFILL V-increment contract** — confirm before bundling SOC-BACKFILL.

### 5a. Things to look out for (traps that don't show up as a red test)
These are failure modes the skipped tests won't necessarily catch — watch for them while building.
- **Silent V corruption (the load-bearing one).** V feeds the conservation law (`α·q·V ≥ θ_min`) and every "compounding" claim. A delayed/async commit (PROTO-V2), a backfill (SOC-BACKFILL), or an outbox replay can each double-count, drop, or mis-order a V-increment without failing an unrelated test. **Guard:** assert V == distinct-verified-decisions after every fail→queue→replay and every backfill; make V-increment idempotent on replay (the outbox already has idempotency keys — use them, don't add a second path).
- **Green-because-skipped ≠ done.** Removing a skip and having the test pass proves the test runs, not that the feature is correct — several of these tests are thin (a projection, a mapping). **Guard:** each ship PR adds at least one assertion on the *behavior*, not just the endpoint shape, before removing the skip.
- **Reuse drift.** PROTO-V2/SOC-WRITE-PATH/SHADOW-MAP build *on top of* existing code (outbox, `write_evolution_event`, ShadowDecision). Re-implementing instead of extending forks the persistence contract. **Guard:** if you're writing a second write-path or a second replay loop, stop — extend the existing one.
- **AGE-STRESS masking, not fixing.** A concurrency-stress test can pass by serializing everything (killing the concurrency it's meant to prove) or by widening the pool so exhaustion never triggers. **Guard:** the test must exercise *concurrent* workers against the shared instance and assert fail-**closed** under exhaustion — not just "no error."
- **Cross-adapter timestamp skew.** Checkpoint/decision timestamps are heterogeneous across stores (ISO vs numeric epoch; AGE vs SQLite vs memory). A replay/backfill that orders by a bare `created_at` can mis-order. **Guard:** order by the numeric `created_at_epoch`, not the raw timestamp (this bit the centroid-history surface already).
- **Fault-injection that leaks state.** The "S2P down" / disposable-graph tests can leave a poisoned pool or an un-cleaned graph that makes the *next* test flaky. **Guard:** teardown must dispose the graph and reset the pool; run the suite twice to catch order-dependence.
- **Skip-lint false confidence.** The CI lint (§4) enforces the *format* of the skip reason, not that the queue ID is real or open. **Guard:** the lint must check the ID against the live queue, or a closed-item ID will sail through.
- **Dependency assumed-done.** Two "done/existing" claims gate this queue — the pool-lifecycle fix (AGE-STRESS) and SOC-SEED-REDESIGN #9 (SOC-BACKFILL). Treat both as *verify-then-trust*; a wrong assumption here blocks the item after work has started, not before.
