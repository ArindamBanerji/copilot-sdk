# Judgment-History Surface — Design, Findings & Execution Plan (for Codex)
### design v3 · document (A) of two · supersedes v2 (`jm_judgment_history_surface_design_v2.md`)

**Date:** 2026-08-06
**What changed v2→v3:** embedded the full findings context (my scans **and** the 4 LLM reviews) so the doc is self-standing; added an **executable execution plan** (§6) with per-phase tasks, deliverables, gates, and rollback. Verify-first is preserved as the P-1 gate.
**Status:** review-backed (Grok, GPT, Claude/Opus, Gemini); **built from a read-only Drive mirror — every code claim is a hypothesis until Codex confirms it.** You have full source access.

---

## 0. What this is and how to use it
This is the complete design for the judgment-history surface: the **findings** that motivate it (§2), the **decisions** (§4), the **model** (§5), and an **executable plan** (§6). It is structured so you can do both jobs in order:
1. **Verify first (P-1).** Confirm each decision (§4) and model point (§5) against the real code — mark **CONFIRMED** (`file:line`) / **CONTRADICTED** (what the code does) / **GAP**. Close the open items (§7) by running the read-only scans (§8). Produce the verification report (§12).
2. **Then execute (P0–P2)** per §6, only after P-1's contracts are frozen and no decision is left CONTRADICTED.
Do not implement before P-1 closes. If a scan must touch data, use a disposable graph and revert. **Ends at P2** — the store migration is program B (§9).

## 1. Scope and the reframe
- **In scope:** the judgment-history **surface** (P0–P2) **+ a quality axis** → centroid history that is consistent, correct, and *credible* across all 5 copilots.
- **Out of scope:** moving the 4 SQLite copilots to AGE (that's the existing AGE migration program, **B**).
- **The reframe (from the reviews):** the defect that matters is **credibility, not consistency**. Five identical endpoints showing unlabeled geometric drift are consistent and still don't prove the moat. The quality axis is the higher-value half of this work.

## 2. FINDINGS CONTEXT
### 2a. My findings (from read-only Drive-mirror scans A+B; `[PROVEN]` = source-confirmed in the mirror, `[UNPROVEN]` = needs a runtime check)
- **Three data models for "centroid history," not one** `[PROVEN]`: (a) `CentroidCheckpoint` rows via `get_centroid_checkpoints(domain)` — S2P explorer, Trading, Purchasing, DataOps-shared; (b) **SOC** = `Decision.centroid_delta_norm` per-decision *drift feed* via AGE Cypher, with **no checkpoint writer at all** (`framework_router.py:129-153`; `graph_schema.py:98`); (c) **DataOps** custom `/api/context/centroid-history` derives Initial/Current snapshots from *decision averages*. Converging means reconciling three data sources, not three routes.
- **Store split** `[PROVEN]`: only SOC on AGE; S2P/Trading/Purchasing/DataOps on `SelectedGraphStore` (AGE-with-SQLite-fallback → defaults to SQLite, which the authority calls "test-only").
- **`SNAPSHOT_AFTER` is a stated JM requirement** (`judgment_memory_v2_7.md:107-115, 320-357`) but **implemented by 0 of 5** `[PROVEN]`. SOC is PARTIAL (canonical substrate, flat feed); the other four NO.
- **Namespace trap** `[PROVEN structure / UNPROVEN impact]`: `load_latest_centroids` selects `checkpoint_id IS NULL`; the V2 `write_centroid_checkpoint` writes non-null ids the loader skips. The scorer has **both** paths (`scorer.py:1516` legacy, `1802/1839` V2), so source can't prove centroids reset on restart. **The restart test decides.** Criterion: count null-id rows per domain — 0 = vestigial (drop the filter); many = load-bearing "latest" pointer. (S2P's calibration work uses the null-id `save_centroids` as the reference.)
- **Enablement inconsistent by construction** `[PROVEN]`: SOC disabled (`soc/config.py:66`, env `SOC_LEARNING_ENABLED`), S2P frozen (`s2p/config.py:91`), Trading/Purchasing/DataOps always-on → 2 static + 3 evolving histories.
- **Live probe** `[PROVEN]`: Trading/Purchasing **200**; SOC **503** (learning off → no data; ~12 PW failures); S2P **404**; DataOps shared route **timed out** (possible hang).
- **Three store implementations, not two** `[PROVEN]`: AGE, SQLite, **InMemory** — and InMemory **already diverges** (doesn't reproduce the null-id filter), which is why no unit test caught the trap.
- **DI-TIMELINE dependency** `[PROVEN]`: the DataOps custom route feeds the **shipped** `CentroidTimelinePanel` demo beat → any retirement must not regress it.
- Conservation-V inconsistency shares the same store root; the authority also requires AGE≡SQLite conservation semantics (`:197-216, 465-480`) — **never tested** `[UNPROVEN]`.
- Blast radius ~21 consumers (12 BE + 9 FE); ~163 PW tests but **soft** (`checklist.spec.ts ~110` is file-level/incidental). Two copies of `judgment_memory_v2_7.md` in the repo.

### 2b. The 4 LLM reviews (findings + the consensus)
- **Grok — ENDORSE-WITH-CHANGES:** make "stop after P2" a first-class gate; **shared scorer/SDK coupling breaks per-copilot independence** (`load_latest_centroids` is shared); upside = queryable DK/IKS + domain-as-label; restart + connection-density as hard gates.
- **GPT — MAJOR-REVISION (persistence correctness):** **dual-write is non-atomic → unsafe rollback** (use an event journal, *for the migration*); **"latest by timestamp" is unsafe → monotonic logical key**; the learning update must be **one atomic transaction**; **split the conformance suite** (temporary parity + **permanent** invariant/concurrency); **synthetic-demo provenance**; a **P-1 contract-freeze** gate; cleanliness reframe **"one SEMANTIC authority ≠ one PHYSICAL implementation everywhere"** → keep a non-semantic in-memory unit fake.
- **Claude/Opus — ENDORSE (P0–P2) / MAJOR-REVISION (P3–P5), codebase-aware:** **R1 the migration truncates history at cutover** (covers new writes only; existing checkpoints ~351/228/221/215 live in SQLite → the compounding demo regresses) → **backfill + assert history depth**; **R2 the store migration is already a scoped program** (this design was understating it ~3×) → **don't own it**; **R3 latency is measured** (S2P ~7.2s) → caching is a gate; **R4 the outbox collides with §12b** (learn/outcome is fail-closed, never queued — `test_learn_remains_fail_closed`) → don't route learn/outcome through it; **R5 don't unify enablement** (SOC shadow + S2P freeze are deliberate) → unify the empty-state; **R6 SOC's `centroid_delta_norm` can't be reproduced retroactively** → keep it as a projection, history from writer-install; **R7 conformance suite must be permanent + cover InMemory**; **R8 "no SQLite in the tree" is impossible** (outbox + `demo/bundle.py:55-60` are SQLite by design) → scope to "no SQLite *GraphStore*"; **VALUE: the design proves centroids MOVE, not IMPROVE → add a QUALITY AXIS** (per-checkpoint quality + counterfactual replay + attribution).
- **Gemini — ENDORSE-WITH-CHANGES:** **MVS = P0+P1+P2** ("100% of demo consistency at 25% of cost"); **PgBouncer + per-copilot pool limits** before AGE traffic (top risk = WSL2 single-instance connection exhaustion / demo collapse); **domain-keyed feature flags** (`JM_READ_STORE`/`JM_WRITE_STORE`) for the shared scorer; **keep an InMemoryGraphStore for unit tests**; DI-TIMELINE via a backward-compat **view** gated on **Playwright visual snapshots**; **specify the SOC drift formula** (Euclidean vs cosine + normalization); upside = a 1-min cross-domain transfer demo beat + `/api/self/trust-traps` + decision-rollback what-if.
- **4/4 CONSENSUS (locked):** endorse P0–P2; **defer the migration**; **keep SQLite + an InMemory unit fake** (the v2 "delete SQLite everywhere" is OFF); per-domain feature flags; PgBouncer before consolidation; preserve DI-TIMELINE via a view + visual snapshot; add a **quality axis**; **close the math-invariant list** before building. Resolved divergence: dual-write-vs-outbox is the migration program's call (out of scope here).

## 3. Sources (you have access)
`judgment_memory_v2_7.md` (authority; **two copies** — confirm they agree) · `math_synopsis_v18.md` (invariant list + distance/quality formulas — **I did not read this**; several items below depend on it) · the AGE migration program doc (**B**) · `persistence_outbox.py` + §12b + `test_learn_remains_fail_closed` · `copilot_sdk/demo/bundle.py` · the store impls (AGE/SQLite/InMemory) + the `GraphStore` protocol · the ~21 consumers · the 3 frontend timeline components + `CentroidTimelinePanel`.

## 4. Design decisions — verify each (status · VERIFY)
- **D1 Route** — one `/api/self/centroid-history`; "evolution"→AgentEvolver. *[assumed]* · VERIFY it exists; SOC/S2P can adopt with back-compat aliases; nothing else owns it.
- **D2 Shape** — one `CentroidHistoryResponse`; drift/per-cell as derived views. *[assumed]* · VERIFY current fields; SOC drift + DataOps `{snapshots,factor_names}` fold in without loss (→V7).
- **D3 Model + identity** — `CentroidCheckpoint` + `SNAPSHOT_AFTER`; **"latest" = monotonic logical sequence key, not timestamp**. *[open]* · VERIFY schema; sequence field present or added; what "latest" keys on today (→V1,V4).
- **D4 Stores** — AGE canonical for product; **keep SQLite + InMemory unit fake**; unit tests→InMemory, integration/CI→ephemeral AGE. *[settled by reviews]* · VERIFY InMemory divergence + what makes it conformant (→V13).
- **D5 Enablement** — do **not** unify; unify only the empty-state contract. *[source-claimed]* · VERIFY the flags + that nothing assumes uniform enablement.
- **D6 Atomic learning txn** — for AGE-authoritative copilots (SOC), the coupled writes succeed/fail together. *[open]* · VERIFY current SOC learn path + the true coupled set (→V5).
- **D7 SOC drift as projection** — keep `centroid_delta_norm` derived from checkpoints; SOC history begins at writer-install. *[open]* · VERIFY the exact reproduction formula (→V2).
- **D8 Quality axis** — per-checkpoint quality + attribution + counterfactual-replay endpoint. *[open — feasibility]* · VERIFY the data supports it (→V12).
- **D9 Per-copilot isolation** — domain feature flags + 5-copilot regression gate. *[settled by reviews]* · VERIFY the shared coupling point + flag insertion (→V10).

## 5. Target model — specifics to confirm
- **Checkpoint identity:** proposed `domain / scorer_version / centroid_scope / checkpoint_seq` (+ uniqueness). Confirm/correct against the real schema (V4).
- **Namespace:** drop the `checkpoint_id IS NULL` special-case **only if** V1 shows it vestigial; else migrate null→deterministic sequence ids.
- **Canonical writer:** confirm which of `save_centroids` / `write_centroid_checkpoint` the loader actually reads (the trap) and standardize on it.
- **Outbox:** do **not** route learn/outcome through it (§12b fail-closed) — confirm (V6).

## 6. EXECUTION PLAN (executable; each phase = tasks · deliverable · gate · rollback)
**Order:** P-1 (verify+freeze) → P0 → P1 → P2. Gates are hard; a failed gate stops the next phase.

**P-1 — Verify & freeze contracts (design gate; no product code).**
- Tasks: run scans §8; answer V1–V13 (§7); freeze the contracts — checkpoint schema + logical-sequence identity, the `SNAPSHOT_AFTER` edge, the atomic-txn boundary, the `CentroidHistoryResponse` schema (incl. quality/attribution/provenance fields), the empty-state contract, and the **SOC drift formula** (from V2).
- Deliverable: the verification report (§12) + a frozen-contract addendum.
- Gate: every V-item answered; no decision left CONTRADICTED without a chosen correction; contracts signed off.

**P0 — Fix all broken surfaces (~1–2d, independent of the model work).**
- Tasks: **restart test on all 5** (V1) → set the namespace decision; **SOC 503→empty** "no history yet"; **S2P 404→route** (wired to the shared handler); **DataOps timeout→root-cause fix** (V8); contract tests for empty/disabled/frozen/populated; a **5-copilot smoke matrix**.
- Deliverable: all 5 centroid-history surfaces return 200 with the empty-state contract.
- Gate: 5-copilot smoke green; no 503/404/timeout. Rollback: per-surface, independent.

**P1 — Foundation (~3–4d).**
- Tasks: shared `/api/self/centroid-history` handler + `CentroidHistoryResponse` over **current** stores (store-agnostic `get_centroid_checkpoints`); wire SOC + S2P (back-compat aliases); namespace fix per V1 (logical-sequence identity or null→id migration); **permanent conformance suite** parameterized over AGE/SQLite/InMemory (split: temporary AGE↔SQLite parity + permanent invariant/concurrency/restart/idempotency; assertions = the V3 math-invariant list); make **InMemory conformant** (V13); **PgBouncer + per-copilot pool limits** benchmarked under a Playwright-style concurrent load (V11); **domain feature flags** `JM_READ_STORE`/`JM_WRITE_STORE` (V10).
- Deliverable: one endpoint + one shape live on all 5 (reading each copilot's current store); conformance green; pool gate passed; flags in place.
- Gate: conformance suite green on all three stores; pool benchmark passes under concurrent load; **full 5-copilot regression green**. Rollback: feature flags revert reads to prior handler.

**P2 — Model + quality axis (~1wk).**
- Tasks: **SOC checkpoint writer + `SNAPSHOT_AFTER`** at write-time (atomic txn, D6/V5); **SOC drift projection** (V2 formula), history from writer-install; **DataOps custom route → backward-compat view** + Playwright visual-snapshot gate (V7); **quality axis** — per-checkpoint quality metric + attribution + **counterfactual-replay endpoint** + synthetic-demo provenance fields (D8/V12); frontend = one canonical response model + one shared client + small per-copilot presentation adapters; **JM v2.8 writeback + dedupe** the two authority copies.
- Deliverable: all 5 on one model/shape with real lineage; quality axis live and rendering; DI-TIMELINE visually unchanged; authority updated.
- Gate: quality metric + counterfactual replay return correct values on seeded verified decisions; DI-TIMELINE visual snapshot matches; 5-copilot regression green.

**Stop line:** ends at P2. No migration, no SQLite deletion, no fleet AGE cutover — those are program B (§9).

**Test-failure approach (all phases):** triage A/B/C/D (A shape/route, B stale-assertion, C behavior-coupled, **D unexplained → candidate real regression, handled first**); the conformance suite is the discriminator; per-phase green gate + anti-mask review (nothing deleted/weakened/echoed to pass); triage the soft ~163 PW count down before planning.

## 7. OPEN VERIFICATION ITEMS (close in P-1)
V1 restart / null-id counts per domain (learn→restart→load: learned vs bootstrap?) · V2 SOC drift formula (metric + normalization) · V3 math-invariant list from `math_synopsis_v18` (= conformance assertions) · V4 checkpoint schema + write/load paths · V5 atomic learning txn (current SOC path) · V6 §12b fail-closed + outbox is SQLite · V7 DI-TIMELINE field contract (schema diff) · V8 DataOps timeout cause · V9 program-B state + whether it covers the depth requirement · V10 consumers + shared coupling point + flag insertion · V11 pool config + Playwright connection math + PgBouncer presence · V12 quality-axis feasibility (rolling accuracy + replay computable?) · V13 InMemory conformance.

## 8. Interim scans requested (read-only, scoped; report each with `file:line`)
- **Scan A — checkpoint model:** schema, identity, the two writer paths, the loader's selection, per-domain null-id counts. (V1,V4)
- **Scan B — learn/txn path:** SOC verify→learn→persist, transaction boundaries, §12b/outbox. (V5,V6)
- **Scan C — surfaces:** the 5 routes/handlers/shapes, the `CentroidTimelinePanel` field contract, the DataOps timeout. (V7,V8,D1,D2)
- **Scan D — math:** the invariant list + the SOC drift formula + quality/IKS definitions from `math_synopsis_v18`. (V2,V3,V12)
- **Scan E — ops:** pool config, Playwright worker/connection math, PgBouncer; the consumer list + coupling; InMemory divergence. (V10,V11,V13)
- **Scan F — program B:** the migration program's current scope + backfill handling. (V9)

## 9. Handoff to the existing AGE migration program (B)
The store migration is program B — do not re-derive its resolved decisions (order, batching, rollback, `V`-lock, pending-decision handling). This design's **single requirement** to it:
> Centroid history must survive migration with **depth preserved** — backfill existing checkpoints so the learning-journey timeline does not truncate at read-cutover; the migration's parity gate asserts history **depth** (row count + earliest sequence), not only equivalence on new writes.

Confirm (V9) whether B already satisfies this or needs the requirement added.

## 10. Corrections baked in (from the reviews) — confirm each against the code
Logical-sequence identity not timestamp · atomic learning txn · keep SQLite + InMemory unit fake · don't unify enablement (unify empty-state) · DataOps route as a view + visual-snapshot gate · quality axis + counterfactual replay + attribution · SOC drift as a projection, history from writer-install · SOC drift formula frozen in P-1 · permanent conformance suite over all stores · PgBouncer + pool gate · per-domain feature flags + 5-copilot regression · synthetic-demo provenance fields · backfill/depth requirement to program B · math-invariant list from `math_synopsis_v18` · outbox NOT used for learn/outcome.

## 11. Value-upside
- **In scope now (cheap, high-credibility):** per-checkpoint quality, counterfactual replay, attribution (P2).
- **Post-MVS / needs the unified graph (with program B):** a 1-min cross-domain transfer demo beat, `/api/self/trust-traps`, lineage-driven decision-rollback / what-if, an explicit `TransferPattern` artifact (0 `DomainContext` nodes exist today).

## 12. What to produce back (verification report → then execute)
1. Verdict per decision (D1–D9) + per model point (§5): CONFIRMED (`file:line`) / CONTRADICTED (what the code does) / GAP. 2. Answers to V1–V13 with evidence + the scan that produced each. 3. Prioritized corrections, each traceable to a finding. 4. Detailed-design guidance per phase (the contracts to freeze, the gaps to fill, the build order). 5. Risk register with severity. 6. Go/adjust recommendation for P0–P2. Then we iterate the design to v4 from your report and schedule implementation.
