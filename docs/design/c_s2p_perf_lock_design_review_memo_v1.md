# S2P Backend Variance (Score-Path Lock Stall) — Executable Design-Review Memo
**Date:** 2026-08-09 · memo on the S2P backend variance diagnosis (intermittent 30–43s stalls on the S2P score path under concurrent workers) · **S2P is the LEAD WEDGE** — this is a demo-credibility + first-pilot risk, not a single-copilot latency tail.
**Provenance tags:** `[SCAN 08-09]` = checked the live Drive code/artifacts this session · `[PRIOR SCAN]` = source-verified earlier (centroid-history / AGE-migration Codex scans) · `[DIAG]` = claim from the variance diagnosis, status marked · `[OPINION]`.

## Verdict
**Keep Option B deferred (it's premature AND it breaks a shipped invariant); do NOT accept the "WSL2-only, won't occur in prod" framing — the scan shows the stall is pool-related and prod-plausible.** Ship three cheap pre-raise mitigations now (fail-fast timeout, demo-staging, pool activation/size), and treat the durable fix as the **atomic-write** change already scoped elsewhere — coordinated with Commit 3 + WP-1, not a separate async project.

## PREMISE VERIFICATION (the diagnosis's assumptions, checked)
| Diagnosis says | Reality | Action |
|---|---|---|
| Root cause = a global `threading.Lock` serializing score + AGE write + cache-invalidation; a slow AGE write holds it 10–30s | `[DIAG]` plausible and consistent with head-of-line blocking. `[VERIFY]` confirm the lock's exact span in `s2p.py` (V1). | Keep — but the lock is only *immovable* because the writes aren't atomic (see root fix). |
| **"Stall is WSL2-specific; won't occur on real PostgreSQL"** | `[SCAN 08-09]` **Weakest link — likely false.** `demo.py` sets `AGE_USE_POOL=true` **`AGE_POOL_MAX_SIZE=5`** for every copilot, all 5 sharing one AGE instance. A June parity artifact shows `pool_available=false` / `connection_mode=warm_fallback` — the pool **silently fell back to a single warm connection**. Cold-start first call 639–855ms then 60–130ms warm. **No PgBouncer.** A single warm connection (or a 5-cap pool) under concurrent workers → acquisition waits = the 10–30s "connection stall." **This is a concurrency/config failure that occurs on real PostgreSQL too.** | **Do not accept-and-monitor on the WSL2 premise.** Verify pool activation NOW (V2); the "won't occur in prod" claim is unproven. |
| Lock scope CANNOT be reduced (4 P0 risks: restart-consistency, read-after-write, concurrent-overwrite, conservation-count) | `[OPINION + PRIOR SCAN]` **True *given non-atomic writes*.** 3 of the 4 (read-after-write, concurrent-overwrite, conservation-count) are exactly what a **DB transaction** provides. `run_transaction` **exists**; `learn()` is atomic **nowhere** today. The lock is a blunt substitute for transactional integrity. | The root fix is atomicity, which **dissolves 3 of the 4 objections** and lets the lock be narrowed. (Restart-consistency = the same loader crux the JM-history work fixes.) |
| Option B (async write queue): score returns, AGE write in background | `[PRIOR SCAN]` **Conflicts with §12b fail-closed.** learn/outcome is authoritative and **never queued** (`enqueue('outcome')` raises); queuing it behind local replay reintroduces the divergence §12b forbade. | **Defer B** — premature *and* invariant-breaking as described. |
| Baselines 0.51s seq / 1.7s concurrent | `[MEMORY]` **May not be at true scale.** S2P full dataset ≈ **25,892 decisions**; **B2 (density at true scale) is still pending**; the score path traverses that graph. At full scale, lock-hold windows lengthen and stalls get *more* frequent. | Treat the baselines as provisional until measured at 25,892-scale on real PG under concurrency. |

## Options — re-scored against §12b and the wedge stakes
| Option | Verdict |
|---|---|
| **A — accept + monitor** | **Insufficient alone.** The "prod-safe" basis is unproven (pool fallback is prod-real). Acceptable only for the *residual tail after* the P0 mitigations, and only with the honest caveat below. |
| **B — async write queue (~3d)** | **Defer.** Premature pre-raise AND conflicts with §12b (queues the authoritative outcome). If ever revisited, §12b must be reopened deliberately. |
| **C — per-category lock (~2d)** | **Skip.** Keeps P0 risks #1/#2 and does **not** eliminate the AGE stall — a stalled write still blocks its category. Low value. |
| **D — pool/PgBouncer tuning + measure (~0.5d)** | **Yes, but do it properly:** not just "measure B8" — **verify the pool actually activates** (not warm_fallback), **size it > 5**, and add **PgBouncer** (transaction-mode) before any multi-worker/all-AGE run. This is the first real mitigation, because the scan says the stall is pool-shaped. |

## Executable plan
### P0 — pre-raise, cheap, high-value (do these)
1. **[PERF-1] Verify pool activation (½d).** Instrument `connection_mode` / `pool_available` on the S2P health+`[S2P-PERF]` path. If S2P runs `warm_fallback` (single connection), that *is* the bug — fix the fallback or the pool isn't real. `LOCATE:` `age_graph_store.py` pool init + `AGE_USE_POOL`/`AGE_POOL_MAX_SIZE` handling.
2. **[PERF-2] Bounded acquisition + write timeout, fail-closed (½–1d).** Cap connection-acquire + AGE-write at ~2–3s; on timeout **fail closed** (consistent with §12b) and return a fast retriable error instead of holding the lock 10–30s. Converts a 30s demo-freeze into a clean error. **Highest value-per-effort item.**
3. **[PERF-3] Demo-staging for the S2P wedge (~0d).** Run the S2P demo **single-worker**, **warm the pool** (pre-execute the demo scores so no cold/fallback connection is hit live), and pin the pinned-preseed. Protects DIFF-1 / COMP-1 / the compounding curve from a live stall.
4. **[PERF-4] Size the pool + PgBouncer (½d).** Raise `AGE_POOL_MAX_SIZE` above 5 for concurrency and add PgBouncer (transaction-mode) before any all-AGE + multi-worker run (the 5-copilots-on-one-instance headroom is ~80/100).

### Root fix — post-raise, coordinated, NOT net-new
5. **[PERF-5] Make the score-write path atomic (`run_transaction`).** This is the same **D6** the JM-history/centroid program already scoped (learn is atomic nowhere). Atomic writes hand read-after-write / concurrent-overwrite / conservation-count to the DB → **the global lock can be narrowed or removed → the head-of-line blocking dissolves.** Do it in **one coordinated pass on the S2P score/write path together with Commit 3 (calibration persist) and WP-1 (conservation-bypass fix)** — all three touch the same lock-protected region; don't make three uncoordinated edits.

## VERIFY-FIRST — Codex diagnostic (run before building)
- **V1 — Lock span:** confirm the `threading.Lock` in `s2p.py` and exactly which steps it holds (score / save_centroids / cache-invalidation / write_decision).
- **V2 — Pool reality (the crux):** does S2P run `pool_available=true` today, or still `warm_fallback`? What's the effective pool size and is there an acquisition timeout? Is PgBouncer present anywhere?
- **V3 — Atomicity:** does the write path use `run_transaction`, or separate writes under the app lock? Confirm `run_transaction` can wrap the full score-write.
- **V4 — §12b:** confirm the outcome write is fail-closed (so PERF-2's timeout is consistent and B stays deferred).
- **V5 — Instrumentation read:** what does `[S2P-PERF]` show for the stalled step on a captured 30s event — connection-acquire, query, or scorer-rebuild? (Adjudicates pool vs scaling vs FreshScorerProxy before any build.)
- **V6 — True-scale baseline:** is 0.51s/1.7s measured at 25,892-decision scale (B2)? If not, re-measure under concurrency on real PG.

## Honesty caveat (state it plainly)
"Won't occur on real PostgreSQL" is **unverified and, on the scan evidence, unlikely** — the pool caps at 5, has a documented warm-fallback-to-single-connection history, and there's no PgBouncer. Until the S2P score path is **load-tested at 25,892-scale on real PostgreSQL under concurrency**, treat the stall as a live risk on the lead wedge, not a WSL2 artifact. The first pilot's load test is the gate before S2P becomes the live proof.

## One-line hand-off
*Defer B (premature + §12b conflict); reject the WSL2-only premise (the scan says pool-fallback, which is prod-real); ship PERF-1..4 now (verify/activate the pool, fail-fast timeout, demo-staging, size+PgBouncer); land the atomic-write root fix (PERF-5) in one pass with Commit 3 + WP-1; gate any "prod-safe" claim on a real-PG load test at 25,892-scale.*
