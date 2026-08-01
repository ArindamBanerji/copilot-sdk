# Decision-Correctness Recording — Systemic Architecture

**Date:** 2026-07-31
**For:** coding session + architecture sign-off
**Supersedes:** the A/B/C/D options in `correctness_divergence_note.md` — those are storage-topology
patches; the real divergence is one layer up (no shared write contract). This note fixes that layer.
**Grounding:** every claim below is from raw post-sync source (`triage.py` mod 2026-07-31 21:55,
`age_graph_store.py`, `scorer.py`, `protocol.py`).

---

## 1. What the source actually shows (not property-vs-edge — two write paths)

The note frames the problem as "correctness stored as a property (SOC) vs an edge (SDK)." True, but that's
a *consequence*. The root cause, from source:

**SOC outcome write** — `triage.py:1782`, through `neo4j_client` (direct AGEClient), raw Cypher:
```
MATCH (d:Decision {decision_id: ...}) WHERE d.domain='soc'
SET d.outcome=..., d.correct='true'/'false', d.verified_at_epoch=..., d.quality_signal=...
```
Audit: `triage.py:1816` calls `framework.audit.record_outcome()` → a **hash-chain written back as Decision
properties** (`d.outcome_entry_hash`, `d.outcome_chain_index`). No Outcome node. No `HAS_OUTCOME` edge.

**SDK outcome write** — `scorer.learn()` → `GraphStore.write_outcome()`:
creates an **Outcome node** with `o.is_correct`, a **`HAS_OUTCOME` edge**, and an **EvidenceReceipt** node.
Sets `d.status` but **not** `d.correct`.

So the divergence is not one fact stored two ways — it is **two independent write pipelines with different
audit models and no shared contract.** `count_correct` breaking on SOC is the first place that divergence
became load-bearing; it will not be the last (any cross-copilot proof, trajectory reader, or audit export
that assumes one shape breaks on the other).

| | SOC | SDK (Trading/Purch/DataOps/S2P) |
|---|---|---|
| Write entry point | `neo4j_client` raw Cypher (`triage.py`) | `GraphStore.write_outcome()` |
| Correctness location | `d.correct` (property) | `o.is_correct` (Outcome node) |
| Audit chain | hash-chain on Decision props | Outcome + EvidenceReceipt nodes |
| Live rows | 4,862 `d.correct` / 0 edges | 0 `d.correct` / 1,890 edges |

A minimal fix (patch `count_correct`'s OR) leaves both pipelines intact and guarantees the next divergence.

---

## 2. The architectural model: one authoritative event, one derived read-model

Adopt an explicit **CQRS-style split** — it's the only framing that reconciles the two legitimate forces
pulling this apart (fast property counts vs. an immutable audit chain) instead of picking one:

- **Authoritative write-model = the outcome event + its audit chain.** This is the source of truth for *what
  happened*: actual_action, verified_at, override, reason, and the tamper-evident hash/receipt chain. It is
  append-only and never counted against directly.
- **Derived read-model = `d.status` + `d.correct` on the Decision node.** These are a **materialized
  projection** of the latest outcome event onto the decision, maintained *only* by the write path, for
  fast counting. They are never authoritative and never written independently.

Under this model, `d.correct` and `o.is_correct` stop being "two sources of truth in conflict." One is the
event; the other is its index. Counting reads the index; auditing reads the event. That is the whole fix,
and it dissolves the `count_verified`/`count_correct` asymmetry because **both counts read the same
read-model substrate by construction.**

This is also already the platform's implicit direction: `count_verified` was made property-based; `d.status`
is already a materialized projection of the outcome lifecycle. This note just makes the pattern **explicit,
uniform, and enforced** instead of half-applied.

---

## 3. The three structural commitments (this is the systemic part)

### C1 — One write contract, every copilot routed through it
`write_outcome(decision_id, actual_action, is_correct, ...)` on the GraphStore protocol becomes the **sole
sanctioned way** any copilot records an outcome. Its post-condition, enforced for every implementation:

1. append the authoritative outcome event + audit link (Outcome node + EvidenceReceipt for SDK; the
   hash-chain audit for SOC — **the audit *implementation* may differ per domain; the *contract* does not**);
2. materialize the read-model on the Decision **atomically in the same write**: `d.status ∈
   {confirmed, overridden}` **and** `d.correct = is_correct` (boolean);
3. never leave the read-model and the event disagreeing.

SOC's `triage.py:1782` block is refactored to call this contract (via the SOC GraphStore adapter) rather than
issue raw `neo4j_client` Cypher. SOC's *audit implementation* (hash-chain) is preserved behind the contract —
this is not a rewrite of SOC's audit model, it is routing SOC's write through the same door. The SDK
`write_outcome` gains one line: `SET d.correct = $is_correct` alongside the `d.status` it already sets.

**Why this and not just "patch the query":** the query is downstream of the write. As long as two write paths
exist, any reader that picks the "wrong" shape re-breaks. Unifying the *write* is what makes every *reader*
safe, permanently.

### C2 — Read-model is derived, never authored independently
`d.correct` is written **only** by `write_outcome`. No route, migration, or script sets it directly
(SOC's raw `SET d.correct` at `triage.py:1783` is exactly the anti-pattern this retires). This is the
invariant that prevents the drift that already bit `count_correct`: there is one writer, so there is nothing
to drift *from*.

### C3 — One count predicate family, property-only
`count_verified`, `count_correct`, and the `AGEProjection`/registry predicates all read the derived
read-model — Decision properties, no `HAS_OUTCOME` traversal anywhere. Concretely `count_correct` branch 1
becomes `... AND d.correct = true` (drop the `OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o)` and `o.is_correct`).
`count_verified` is already here; this brings `count_correct` alongside it and deletes the asymmetry at the
source.

---

## 4. Migration (bounded, reversible, one-time)

1. **Backfill the read-model on the 4 SDK domains** from the authoritative Outcome nodes:
   `MATCH (d:Decision)-[:HAS_OUTCOME]->(o) WHERE d.domain=$dom AND d.correct IS NULL
    SET d.correct = (o.is_correct = true)`. ~1,890 rows total (174+645+681+390). Idempotent
   (`d.correct IS NULL` guard), domain-scoped, tagged `source:'read_model_backfill'` for clean rollback.
   **Normalize to boolean at write time** (PF-7 class: `o.is_correct` may be `1`/`true` — coerce).
2. **SOC needs no backfill** — 4,862 `d.correct` rows already exist and are already boolean (PF-7 confirmed).
3. **Flip `count_correct` to property-only** (C3) *after* the backfill lands, guarded by the conformance
   test below.
4. **Route SOC's `triage.py` outcome write through the contract** (C1). This is the largest single change;
   stage it behind the existing dual-write→read-diff→flip pattern already used for the S2P migration, so
   SOC's raw path and the contract path run in parallel and are diffed before cutover.

**Blast radius is bounded and known:** 1,890 SDK rows + one SOC write-path refactor. No Outcome-node
creation on SOC (its audit stays hash-chain), so the flagship graph's shape is unchanged — this respects the
standing D5 decision that "SOC's audit chain is projection-based permanently" while still unifying the
*correctness read-model*.

---

## 5. Enforcement — the part that makes it stay fixed

The bug existed because nothing asserted the two counts read the same substrate. The architecture is only
real if these ship with it:

- **Conformance test (per domain):** for every copilot, `count_correct(d) ≤ count_verified(d)`, both queries
  contain no `HAS_OUTCOME`, and — where Outcome nodes exist — `d.correct == (latest o.is_correct)` for a
  sampled set. This is the test that would have caught the original drift.
- **Forbidden-pattern scanner (the E3 scanner already on the backlog):** flag any Cypher outside
  `write_outcome` that writes `d.correct`/`d.status`, and any counting query that traverses `HAS_OUTCOME`.
  Makes C2 and C3 mechanically enforced, not conventions.
- **Protocol post-condition test:** every GraphStore implementation's `write_outcome` leaves
  `d.correct == is_correct` and `d.status` set, asserted against InMemory/SQLite/AGE in the existing
  conformance suite.

---

## 6. Why the note's options don't survive the source read

| Note option | Verdict against source |
|---|---|
| A: property-only | Right substrate, but as stated it doesn't unify the **write path** — SOC still uses raw Cypher, SDK still uses `write_outcome`. Necessary, not sufficient. C1 is what completes it. |
| B: edge-only | Fights the grain: `count_verified` is already property-based, and it forces Outcome-node creation on SOC — contradicts the standing D5 decision and rewrites SOC audit for no gain. |
| C: dual-branch fix | The trap. Encodes the divergence permanently in the query; the drift that broke `count_correct` recurs the next time someone edits one branch. |
| D: both | Closest to right, but framed as a storage choice. Elevated here to C1–C3: the "both" is *event (authoritative) + property (derived)*, with a **single write contract** and **enforcement**, not just "write two places." |

The difference between D and this note is the difference between "write correctness in two places" and
"one contract owns the write; one substrate owns the count; a scanner owns the invariant." The first is a
bigger patch. The second is an architecture.

---

## 7. Sequencing

1. Land the **protocol post-condition** + **conformance test** (red — they fail today). Failing tests define
   the target.
2. SDK `write_outcome` sets `d.correct` (C1 SDK half). Backfill 1,890 SDK rows (§4.1).
3. Flip `count_correct` to property-only (C3). Conformance test goes green for SDK + SOC.
4. Ship the **forbidden-pattern scanner** (C2/C3 enforcement).
5. Route SOC `triage.py` through the contract (C1 SOC half), behind dual-write→read-diff→flip. Retire the
   raw `SET d.correct` at `triage.py:1783`.

Steps 1–3 fix the live `count_correct` undercount and are shippable this sprint. Steps 4–5 are what make it
systemic — they remove the *ability* to reintroduce the divergence. Do not stop at 3; stopping at 3 is the
minimal fix wearing an architecture's clothes.

---

## 8. Files read (raw, post-sync)

| File | mod (UTC) | Used for |
|---|---|---|
| `triage.py` | 2026-07-31 21:55 | SOC outcome-write path (:1782), SOC audit chain (:1816) |
| `age_graph_store.py` | 2026-07-30 08:12 | `count_correct`/`count_verified` bodies (:2071/:2105) |
| `scorer.py` | 2026-07-31 21:51 | SDK `write_outcome` call site, `d.status` set |
| `protocol.py` | 2026-07-29 14:50 | `write_outcome` contract surface |

**One unread dependency, flagged honestly:** `framework.audit.record_outcome` (SOC's hash-chain audit
writer) — I confirmed it's *called* at `triage.py:1824` and writes `d.outcome_entry_hash`/`d.outcome_chain_index`,
but I have not read its body. C1 says SOC's audit implementation is preserved behind the contract; confirm
`record_outcome` has no side effect that must stay coupled to the raw-Cypher block before moving the write.
