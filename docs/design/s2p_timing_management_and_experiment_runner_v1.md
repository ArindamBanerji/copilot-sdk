# S2P Timing Management — The Experiment Enabler v1

**Date:** 2026-08-04
**Why this exists:** the v2 root-cause experiment matrix cannot run until the timing is managed — Codex either hangs on a single request or gets its shell command killed before the suite finishes. This spec makes the experiments runnable. Companion to `s2p_score_context_rootcause_design_v2.md`.

## Two distinct problems (credit the analysis in playwright_timeouts.txt)
- **Problem A — request hang:** an individual score/learn takes 10–120s (backend stall), so Playwright's response wait times out. Raising the wait to 30/60/120s only *masks* it.
- **Problem B — suite exceeds Codex's shell timeout:** the full S2P run takes >15 min, so Codex kills the command before it completes. Not fixed by raising Playwright waits.

**The reordering that matters:** the uploaded plan puts "raise the known-slow waits" as Layer 1 and the backend fix as Layer 3 (later). For *experimentation* that's backwards. Raising waits to 60–120s makes each slow test *longer*, which makes Problem B **worse**. The **backend fast-fail guardrail** turns 10–120s hangs into ~2s fast-fails — which fixes Problem A at the source (no long waits needed) **and** shrinks total suite runtime enough that sharding fixes Problem B. One change, both problems. Do it first.

---

## Layer 1 — Backend fast-fail guardrail  *(the enabler; ship FIRST)*
F1 is done (context failure → `None`, HTTP 200). Add a short server-side deadline so **any** slow S2P graph op fast-fails instead of riding the long session `statement_timeout`. The variance trace shows it's not only `query_context` — invoice linking (30.7s), cache invalidation (11.5s), and cross-copilot signal (10.7s) also stall, because in AGE mode they all hit the unindexed / entity-less `soc_graph`. So the deadline must cover the graph-op callers, not just context.

**LOCATE:** `age_client.py` query execution (no per-query timeout param — session default is long); the S2P graph-op callers in `s2p.py`: `_resolve_graph_context`, `_link_decision_to_invoice` / `link_decision_to_entity`, `apply_cache_invalidation_event`, the cross-copilot signal fetch.

**CHANGE:** set a short `statement_timeout` (~2500ms) for S2P graph reads/writes — `SET LOCAL statement_timeout = '2500ms'` in the query's session/transaction, or a per-connection option (since `run_query` has no timeout arg). Wrap each caller so a timeout **degrades** (empty/None, like F1) rather than 500-ing. Keep authoritative writes (the outcome write) on their normal path — only the *enrichment/link/cache* graph ops get the short deadline.

**VERIFY:** in AGE mode, no single score/learn exceeds ~3s (fast-fail, no hang); in SQLite mode nothing regresses (ops already fast). The per-request times in the trace collapse from 10–43s to <3s.

**EFFECT:** Problem A solved at the source (Playwright waits can stay at 30s), and the suite runtime drops enough that Layer 2 sharding keeps every Codex command well under the shell timeout.

---

## Layer 2 — Sharded runner  *(Problem B)*
Never run the full S2P suite in one Codex command. Split into shards that each finish comfortably under Codex's shell timeout (with Layer 1, expect 2–4 min each). The Phase-1→6 Codex prompt in `playwright_timeouts.txt` is the right vehicle — use it as-is. Policy:
- `--workers=1` for backend-heavy specs (score/learn/flows); `--workers=2` only for UI-only specs.
- Per-test timeout: 90_000ms normal, 180_000ms backend-heavy (headroom for a genuine cold start; the guardrail makes it rarely needed).
- `--global-timeout`: 600_000 normal shards, 900_000 backend-heavy.
- `--reporter=line` (or dot); capture each shard's result separately.
- Do NOT run Trading.

Suggested shard groups: (1) score endpoint/API specs; (2) preview/polish specs; (3) situation-analyzer + rule-vs-reasoning (the context-content specs); (4) `flows.spec.ts` alone, `--workers=1`.

---

## Layer 3 — Targeted waits  *(minimal, after Layers 1–2)*
Keep the 30_000ms default. With the guardrail, requests either succeed <3s or fast-fail, so most waits need no change. Raise only a *proven* cold-path wait to 60_000ms max, commented with a reference to the variance trace. Never blanket >60s (it re-creates Problem B). Prefer response predicates over sleeps; add failure messages that name the stalled phase where possible.

---

## The v2 experiment matrix — now runnable, as sharded + guardrailed commands
Run each with **Layer 1 guardrail on** and **`AGE_TIMING=1`**. Because requests now fast-fail, each of these completes fast and stays under the Codex shell timeout.

| # | What | Command shape | Decides |
|---|---|---|---|
| X1 | **PW in SQLite mode** | backend launched `S2P_ACTIVE_GRAPH_BACKEND=sqlite`; run the Layer-2 shards | **Passes → FIX-A** (data is in SQLite; failing runs were AGE-mode). |
| X2 | **PW in active-AGE mode** | backend `S2P_ACTIVE_GRAPH_BACKEND=age` → `soc_graph`; run the shards | No hangs (guardrail); context-content specs (situation-analyzer) fail on empty context → confirms AGE lacks entities. |
| X3 | **Store probe (no PW, seconds)** | call `store.query_context('S2P-INV-0003', 2, domain='s2p')` against the SQLite store and the AGE store | SQLite returns neighbors fast; AGE 0/timeout → direct proof of the data-location split. |
| X4 | **AGE anchor timing** | one score in AGE mode with `AGE_TIMING=1` | Time is in the label-less anchor scan, not traversal → "scanning for an absent node," not hub fan-out. |
| X5 | **Failing-run config** | read the PW `webServer` launch env + demo/launch script | Confirms the failing suite ran active-AGE → turns FIX-A from "indicated" to "confirmed." |

---

## Order of operations
1. **Layer 1 guardrail** — ship first; it's the enabler (fixes A, shrinks the suite for B).
2. **Layer 2 sharded runner** — add via the `playwright_timeouts.txt` Codex prompt.
3. **Run X1–X5** (sharded, guardrailed, `AGE_TIMING` on).
4. **Decide FIX-A vs FIX-B** per the v2 decision tree: X1 passes + X5 = active-AGE → FIX-A (run/point S2P context at SQLite); active-AGE required → FIX-B (migrate the entity subgraph into `soc_graph` + Appendix-A split-read).

## One caution on the uploaded plan
Its Layer-1 "increase only known slow API waits" and its treatment of the backend stalls as deferred Layer-3 work will *stabilize the harness but keep the suite slow* — and 60–120s waits actively fight Problem B. Keep the sharded-runner and wait-discipline parts of that plan (they're excellent), but move the **backend fast-fail guardrail ahead of the wait-raising** — it's what makes the waits unnecessary and the shards short. The 30–43s stalls it flags for "later" are the same root cause v2 identifies (AGE reads against an entity-less `soc_graph`); the guardrail bounds them now, and FIX-A/FIX-B removes them.

## Provenance
Two-problem split, sharded-runner mechanics, and the variance figures are from `playwright_timeouts.txt`. The backend fast-fail guardrail, the SQLite-vs-AGE mode experiment, and the root cause are from the v2 design + Claude/Codex scans. `run_query` has no per-query timeout param (confirmed earlier), so the deadline is `SET LOCAL statement_timeout` / a connection option, not a call argument.
