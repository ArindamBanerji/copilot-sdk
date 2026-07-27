# Canonical V_soc Definition

**Date:** July 26, 2026
**Version:** v1.4
**Status:** DECISION MADE (§3.1b: Option 1 — baseline the synthetic demo population, reseed under the ledger).
Baseline value will be **4,862 (seed v1)**; the note flips to **FINAL** once one deliverable lands — the
validation-runner check that a V change with no `baseline_reset` event is a NO-GO (§3.1b deliverable 3). Until
then documents cite **4,899 (provisional)**.
**Repo home (once final):** `copilot-sdk/docs/design/canonical_v_soc.md`
**Purpose:** One source of truth for V_soc. Every document cites this (§7); no document re-derives the number.

**v1.4 changes:** recorded the roadmap decision (§3.1b DECISION) — Option 1 accepted with three deliverables
(pin+hash the seed; reseed emits a `baseline_reset` ledger event; runner NO-GOs an unrecorded V change). The
baseline is **4,862 (seed v1, reset 2026-07-26)**, written into §1 as FINAL *only after* deliverable 3 exists,
because that check is what actually upholds §4 rule 3 for the reseed path — filing 4,862 before it would assert
a guarantee the code doesn't enforce. Fixed **§5** to AGE bracket syntax (`IN ['confirmed','overridden']`) with
a portability note, since §5 is the predicate all three V paths must match and the parenthesis form does not
parse in AGE.

**v1.3 changes:** §3.1a result in — current graph confirmed synthetic seed; reframed the roadmap decision from
the false "real vs synthetic" binary to "stable invariant vs unrecorded V mutation."
**v1.2 / v1.1:** scan results (4,862/0/all-backfill); baseline-vs-live separation and provisional marking.

---

## 0. Why this note is not "both numbers are fine"

The prior draft stated `V_soc = 4,899` and then said *"neither is the number — both are point-in-time
snapshots"* of the same population, attributing the 37-row gap to possible archival or cleaning. That defeats
the note's purpose twice:

1. A canonical value that resolves to *"4,862 or 4,899, both valid"* leaves the next author to pick one — which
   is the exact behavior (two documents picked 4,862) that made this note necessary.
2. It contradicts its own rule. A drop of 37 **verified** decisions is either a scoping error or a traceable,
   alarmed decrement (§4). It is never "the graph may have been cleaned." A verified-count that silently falls
   is the precise failure mode conservation exists to catch.

So this note does not average the two numbers or call them co-equal. It anchors on the value with the strongest
provenance, and treats the disagreeing value as a **claim requiring proof** (§3), not a snapshot to accept.

---

## 1. The baseline (the regression anchor)

```
V_soc_baseline = UNSET   (audited value was 4,899; §3.1 scans returned 4,862 — disposition pending §3.1a)
```

> **Status (v1.2):** the audited baseline was **4,899**, cross-checked by two methods (below). §3.1 has since
> re-measured the live graph and found **4,862**, with the 37-row difference *not present* in the current
> graph. The baseline is therefore **UNSET pending §3.1a**, which decides between two outcomes: (a) **4,862**,
> re-based with a documented reseed/removal, if §3.1a shows the current graph is real data; or (b) **blocked**,
> if §3.1a shows a seed/synthetic population that must be replaced before any baseline is set. Until §3.1a
> returns, documents continue to cite **4,899 (provisional)** — it remains the last *audited real* value — and
> switch to the §3.1a outcome once confirmed. **Do not adopt 4,862 before §3.1a.**

4,899 is the audited value because it has **two independent derivations that cross-check**, not one measurement:

| Source | Method | Arithmetic |
|---|---|---|
| **PF-1** | outcome-value distribution over SOC Decisions | correct 3,749 + incorrect 1,150 = **4,899** (null 1,354 excluded); total 6,253 ✓ |
| **PF-6** | domain census at audit time | tagged-verified 37 + null-domain-verified 4,862 = **4,899**; total 1,139 + 5,114 = 6,253 ✓ |

Two methods, computed differently, land on the same number and the same total — which is why 4,899 was the
audited anchor. Note the audit total was **6,253** nodes; §3.1's current graph holds **4,862** verified with no
null-domain remainder, i.e. a *different population size*. That population-size change is the core of the
§3.1a question: 4,862 is a legitimate new baseline only if the current population is real.

The baseline, once §3.1a sets it, is a **dated, immutable constant.** It never changes. What changes is the
live value (§2).

---

## 2. Baseline vs live — the distinction the draft collapsed

The draft was right that V is live and wrong that this dissolves the baseline. Both hold, once separated:

```
V_soc_baseline          = 4,899               # fixed constant, dated, never edited
V_soc(t)                = count_verified("soc") evaluated at time t     # live, moves as decisions verify
```

**The invariant that ties them (this is what gates check):**

```
V_soc(t) = V_soc_baseline
           + (SOC verifications recorded since the baseline date)
           - (SOC verified-decision removals recorded AND alarmed since the baseline date)
```

- A gate never asserts `V_soc(t) == V_soc_baseline` (that fails the moment one real verification lands — the
  bug the validation-plan draft carried).
- A gate asserts `V_soc(t) >= V_soc_baseline` **and** that every unit of the delta reconciles to a recorded
  event. (`V_soc_baseline` = 4,899 provisional; §3.1 confirms.)
- An *unexplained* delta in either direction is a NO-GO, not a re-baseline.

---

## 3. ⚠️ BLOCKING: reconcile 4,862 before this note is FINAL

The July-25 `B0` census returned **4,862** and reported *"zero NULL-domain rows, all tagged domain='soc'."*
Those two facts are mutually inconsistent with the audited total: if all SOC verified rows are now tagged
`domain='soc'`, a domain-scoped verified count must return **4,899**, not 4,862.

### 3.1 Two runnable scans settle this now (no roadmap dependency)

These do **not** depend on any provenance property and do not use `CASE WHEN` (AGE-unsupported). Run both; the
pair localizes the discrepancy.

```sql
-- (A) Total SOC verified — is the live number 4,899 or 4,862?
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.domain = 'soc'
    AND ( (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
       OR (d.status IS NULL AND d.outcome IS NOT NULL) )
  RETURN count(d) AS v_soc_total
$$) as (v_soc_total agtype);

-- (B) Are any verified SOC rows still NULL-domain (i.e. did the backfill miss them)?
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.domain IS NULL
    AND ( (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
       OR (d.status IS NULL AND d.outcome IS NOT NULL) )
  RETURN count(d) AS v_null_domain
$$) as (v_null_domain agtype);
```

**Interpretation — the pair (A, B) is conclusive on state, but see §3.1a before re-basing:**

| (A) v_soc_total | (B) v_null_domain | Meaning | Action | Baseline |
|---|---|---|---|---|
| **4,899** | **0** | all verified rows tagged; 4,862 was a sub-population count | drop the sub-population filter from the B0 census; mark note FINAL | **4,899** |
| **4,862** | **37** | backfill missed 37 rows (still NULL-domain) | re-tag the 37 (§3.3), re-run (A) → expect 4,899 | **4,899** after re-tag |
| **4,862** | **0** | the 37 pre-tagged rows are not in the current graph | **§3.1a decides disposition — do NOT re-base to 4,862 yet** | **pending §3.1a** |
| anything else | — | predicate or tagging wrong | do not finalize; reconcile first | — |

Note the second and third rows both show total = 4,862 but mean opposite things — that is exactly why (B) is
required and a single total query is not enough.

### 3.1 RESULT (2026-07-26) — landed in row 3, disposition pending §3.1a

```
Scan A: v_soc_total   = 4,862
Scan B: v_null_domain = 0
Scan C: domain_source = 'backfill' on all 4,862; zero NULL; zero archived.
```

**Confirmed (state):** every current SOC verified Decision was written by the backfill. The 37 rows PF-6
recorded as pre-tagged (`domain='soc'`, no `domain_source`) are **not in the current graph** — had they been
absorbed, some rows would carry `domain_source=NULL` and the total would be 4,899.

**NOT yet confirmed (cause), and cause decides the baseline.** "The 37 are gone" is consistent with *two*
histories the scans cannot distinguish — both leave the current graph identical:

1. **Targeted removal** — 37 specific verified decisions deleted from an otherwise-continuous graph.
   → a §4 rule-3 decrement; re-base to 4,862 is legitimate *if the 37 IDs and the reason are recorded.*
2. **Graph reseed / population replacement** — the pre-audit graph (6,253 nodes) replaced wholesale by a reseed
   creating a *new* fixed population, which the backfill then tagged. → **not a 37-row decrement of the audited
   dataset; a different dataset.** 4,899 and 4,862 then describe *different graphs*, and 4,862 is a baseline
   only if the reseeded population is the one the platform actually runs on.

The re-base proposal named the reseed (history 2) as "most likely." **If history 2 holds, "documented
decrement" (history 1) is the wrong label** — a reseed is a baseline discontinuity, not a conservation event,
and it raises a question a decrement does not: *is the reseeded graph real, or synthetic?*

### 3.1a — the check that must run before re-basing (blocks the 4,862 decision)

The scans see only the current graph, so they cannot tell removal from reseed, or real data from seed. One
provenance scan does — and it is the principle this whole note guards: **never baseline conservation on
synthetic data.**

```sql
-- Outcome distribution of the CURRENT 4,862, vs PF-1's REAL split (correct 3,749 / incorrect 1,150 / null 1,354).
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain = 'soc'
  RETURN d.outcome AS outcome_value, count(*) AS n ORDER BY n DESC
$$) as (outcome_value agtype, n agtype);

-- Provenance tier: real verified-decision data, or a sample/seed tier?
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision) WHERE d.domain = 'soc'
  RETURN d.provenance AS tier, count(*) AS n
$$) as (tier agtype, n agtype);
```

| Current-graph evidence | History | Disposition | Baseline |
|---|---|---|---|
| outcome split ≈ PF-1 proportions, real provenance tier | reseed **of real data**, or genuine removal from real data | §4 rule-3 event; record reseed/removal cause + date | **4,862** (re-based, documented) |
| outcome split flat/synthetic, or provenance = `sample`/seed | current graph is a **seed/dev population**, not production | **do NOT baseline.** Reseed from real data (or locate the real graph) first | **neither — blocked** |

**Why this is not pedantry:** if the 4,862 are seed rows and we bless 4,862 as the baseline, every downstream V
gate is anchored to synthetic data and "V agrees across scorer/store/census" becomes agreement about a
meaningless number — worse than the original ambiguity. The 37-row question is small; the *"is this graph
real"* question it exposed is not.

### 3.1a RESULT (2026-07-26) — landed in row 2 (seed population), and it exposed a *third* thing

```
IDs:          SYN-DEC-* ("synthetic decision"), DEC-JDOE-* (demo user "John Doe")
Provenance:   NULL on all rows        Source: NULL on all rows
Timestamps:   clustered Mar–Jun 2025  (seed window, not live operations)

Outcome distribution vs PF-1 (real audit):
  outcome     PF-1     current    delta
  correct     3,749    3,712      -37
  incorrect   1,150    1,150       0
  null        1,354        0      (verified-only graph)
```

**Confirmed:** the current population is **synthetic seed data**, and the missing 37 are **all from the
`correct` bucket** (3,749 − 37 = 3,712; `incorrect` matches exactly). The seed was built to replicate PF-1's
distribution but reproduced 37 fewer `correct` rows — those are the pre-tagged 37 that didn't survive the
reseed. Per the §3.1a table this is **row 2: do not baseline as-is.**

**But "synthetic" is not the finding that matters — this is a demo platform; all data is synthetic by design,
and the scorer/conservation/referral system has always run on it.** So §3.1a's blanket "do not baseline seed
data" is too blunt for this platform. The finding that *does* matter is subtler and it is the reason 4,862
still cannot be baselined as-is:

> **A reseed just moved V_soc by 37 with no verification event, no removal event — nothing the conservation
> ledger recorded.** That is a demonstrated **unrecorded V mutation.** Baselining 4,862 today does not fix
> that; it freezes a number that the reseed process can silently move again next month, at which point every V
> gate re-anchors and "V agrees across scorer/store/census" passes on a value that drifted for exactly the
> reason conservation exists to forbid.

### 3.1b — the roadmap decision, reframed (do not present it as real-vs-synthetic)

The proposal framed roadmap's choice as *"protect a real production dataset OR protect the demo dataset the
platform runs on."* **That binary is false and would lead to the wrong answer.** Synthetic-ness was never the
hazard — an unrecorded mutation of V is. The demo dataset can absolutely be the operational truth and 4,862 can
absolutely be the baseline; the real question is:

> **Is the seed population a stable conservation invariant, or a process that silently regenerates V?**

That reframes the vote into an engineering condition roadmap can attach a *yes* to:

| Roadmap chooses | Condition that must hold | Baseline |
|---|---|---|
| **Baseline the demo dataset** (recommended, and matches how the platform actually runs) | The reseed is brought **under the ledger**: the seed script is pinned/versioned, a reseed is recorded as an explicit baseline-reset event (dated, with the new count), and the conservation gate treats an unrecorded population change as a NO-GO — not as a silent new normal. | **4,862**, documented as *synthetic, seed vN, reset-event recorded* |
| **Gate only real operational data** | Real operational SOC decisions must exist and be the graph the scorer runs on — which, for a demo platform, may be never. | **blocked** until real data exists |
| **Do nothing / baseline 4,862 as-is** | — | **rejected:** freezes a number the reseed can move again with no record; reintroduces the exact silent-drift failure this note was written to prevent |

**Recommendation to roadmap:** option 1. The demo dataset *is* the operational truth here, so gate it — but the
deliverable is not "write 4,862 into the note," it is "make a reseed a recorded event so V can never again move
by 37 without the ledger knowing." The number is downstream of that; once the reseed is under the ledger,
4,862 (or whatever the pinned seed produces) is a legitimate baseline. Until it is, 4,862 is a snapshot of an
unpinned process, and pinning it in a canonical note would make the note lie the next time the seed changes.

**One data point worth flagging to roadmap regardless of the vote:** the reseed *lost* 37 `correct` decisions
and kept `incorrect` exactly. If the seed script is nondeterministic in a way that preferentially drops
`correct` outcomes, that is a mild bias in the demo's own data (fewer correct → lower apparent accuracy), worth
a look independent of the baseline decision.

### 3.1b DECISION (2026-07-26) — Option 1 accepted; baseline gated on three deliverables

Roadmap call: **baseline the demo dataset, with the reseed brought under the ledger.** The demo population is
the operational truth (the scorer, conservation gate, and referral system all run on it), so it is what
conservation must protect — *provided a reseed can no longer move V without a record.* Three deliverables make
that real, and all three must exist before this note is marked FINAL:

1. **Pin the seed.** Version the seed script and hash its output; the seed version is part of the baseline
   identity (a baseline is `(count, seed_version)`, not a bare number).
2. **Reseed writes a ledger event.** `demo.py --reseed` — and any graph reset — emits
   `{event: "baseline_reset", v_before: N, v_after: M, date: <ISO>, seed_version: <hash>}`. A reseed is a
   *recorded* baseline discontinuity, never a silent one.
3. **Validation runner enforces it.** If V changed since the last checkpoint and **no** matching
   `baseline_reset` event exists → **NO-GO.** This is the mechanism that makes rule §4-3 real for the reseed
   case: an unrecorded population change fails the gate.

**On FINAL:** once (1)–(3) exist, write into §1:
`V_soc_baseline = 4,862  (seed v1, baseline_reset 2026-07-26; synthetic demo population)` and flip the status
to FINAL. Until then the baseline is **UNSET** and documents cite `4,899 (provisional; canonical §3.1b
pending)` — see §1.

**Why 4,862 is not written into §1 yet (the one caveat on the "don't need" list):** the three deliverables are
not paperwork — deliverable 3 is the *only* thing that upholds this note's §4 rule 3 for the reseed path. If
4,862 is filed as FINAL before the runner check exists, the note asserts a conservation guarantee the code does
not yet enforce, and the next reseed silently violates it. So: the decision is made and recorded here now
(unblocking everything downstream), but the **FINAL flip waits on deliverable 3 landing** — that is the single
remaining gate, and it is small.

### 3.2 The 37-row sub-population — resolved by the §3.1 RESULT (was roadmap Q1)

**Superseded by the scan result.** §3.1 found **all 4,862 carry `domain_source='backfill'` and zero carry
`domain_source=NULL`** — so the 37 pre-tagged rows are not in the current graph, and there is **no second
sub-population to distinguish.** The `domain_source`-vs-fallback question below is therefore moot for the
*current* graph, and §6's sampling rule collapses to a single population (§6).

It stops being moot only if §3.1a returns "blocked / seed population" and the graph is later reseeded from real
data — at which point the pre-tagged/backfilled distinction may re-appear and this guidance applies again.
Retained for that case:

The distinction assumed a `domain_source='backfill'` provenance stamp. **§3.1 Scan C confirms the stamp
exists** (all 4,862 carry it), so if two sub-populations ever co-exist again they are separable by
`d.domain_source='backfill'` vs `IS NULL`. Fallbacks if a future graph lacks the stamp: a saved `decision_id`
list (most durable), or a `verified_at`/`created_at` timestamp cutoff (weaker — misclassifies a late-verified
pre-tagged row).

### 3.3 If the backfill missed 37 (row 2 above), re-tag before finalizing

```sql
SELECT * FROM cypher('soc_graph', $$
  MATCH (d:Decision)
  WHERE d.domain IS NULL
    AND ( (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
       OR (d.status IS NULL AND d.outcome IS NOT NULL) )
  SET d.domain = 'soc', d.domain_source = 'retrofit_reconcile'
  RETURN count(d) AS retagged
$$) as (retagged agtype);
```

Distinct `domain_source` value so the reconciliation is itself auditable and reversible.

### 3.4 Rule until resolved

Documents use `V_soc_baseline = 4,899`. **4,862 is never adopted by default** — only as the *proven* result of a
recorded 37-row removal (row 3). The burden of proof is on the lower number.

---

## 4. The gate rule

```
1. V_soc(t) >= V_soc_baseline                          (never == ; see §2. baseline = 4,899 provisional, §3.1)
2. every increment traces to a recorded SOC verification event
3. every decrement traces to a recorded AND alarmed removal event   (a drop is never "cleaning")
4. scorer-side V == store.count_verified("soc") == census V   at every checkpoint
```

**Why rule 4 is not redundant** (this program has already been bitten by it): V_soc is computed by *three*
different code paths, and they have disagreed in production —

- the **census script** (direct property query),
- the **store adapter** `count_verified("soc")` — which was found returning **0** because it was edge-based
  (counted `HAS_OUTCOME` edges that SOC does not have), and
- the **SOC scorer**, which runs on `InMemoryGraphStore` and computed V from process-local state, not AGE.

A note that pins the *number* but not the *predicate* lets these three keep disagreeing while each looks fine
alone. Rule 4 forces them to equal each other and equal §1. The predicate they must all implement is §5.

---

## 5. The V predicate (so "count_verified" is unambiguous)

All three paths in rule 4 MUST implement this exact predicate — property-based, no edge dependency. Shown in
**AGE Cypher** (square-bracket list literals), matching every runnable query in this note:

```
V = count(DISTINCT d.decision_id) WHERE d.domain = 'soc' AND (
        (d.status IS NOT NULL AND d.status IN ['confirmed','overridden'])
     OR (d.status IS NULL     AND d.outcome IS NOT NULL)
    )
```

- **Syntax note:** AGE requires `IN ['...']` (square brackets); Neo4j-style `IN ('...')` (parentheses) will not
  parse in AGE. Non-Cypher implementations (a Python filter, a SQL adapter) use their native list form, but the
  membership set is exactly `['confirmed','overridden']` — do not paraphrase it.
- The two branches are complementary (`IS NOT NULL` vs `IS NULL`), so a decision **cannot** be counted twice —
  by construction, not by a test.
- `HAS_OUTCOME` edges exist for the **audit-chain traversal claim**, not for V. Counting edges to derive V is
  the exact mistake that produced the `count_verified → 0` bug. Do not reintroduce it.
- `d.outcome IS NOT NULL` was verified against live data (PF-1) to mean *terminally verified* — values are
  `correct`/`incorrect`, no `pending`/sentinel. If a future writer introduces a non-terminal `outcome` value,
  this predicate must narrow to an allow-list, and this note updates.

---

## 6. Sampling rule for scoping changes

**Per the §3.1 RESULT, there is currently one sub-population:** all 4,862 SOC Decisions carry
`domain_source='backfill'`; the 37 pre-tagged rows are not in the graph. So a scoping-validation sample is
drawn from the single backfilled population — there is no second cohort to include.

**This simplification is contingent on §3.1a.** If §3.1a returns "blocked / seed population" and the graph is
later reseeded from real data, a pre-tagged cohort may re-appear, and the original rule returns: sample **both**
sub-populations, because rows that already carry `domain='soc'` are the highest-signal rows for a scoping bug
(they're the ones a mis-scoped query drops first). Identify them by `domain_source` (Scan C confirms the stamp
exists), else by saved ID list, else by timestamp cutoff — one discriminator, not a new one per use.

---

## 7. How to cite this note (so nobody re-derives)

In any document that references the number, write **only** this, and link the note:

> V_soc baseline = 4,899 (canonical; see `canonical_v_soc.md`). Live gate: `V_soc(t) ≥ 4,899`, delta
> reconciled to recorded verification/removal events; scorer == store == census.

Until §3.1 is run, append "*(provisional pending canonical §3.1)*" to the citation. Once §3.1 confirms
`(4,899, 0)`, drop that phrase everywhere — that is the only edit finalization pushes to citing documents.

Do **not** restate the derivation, the 4,862 sub-term, or the predicate in the citing document — those live
here and change here only.

---

## 8. Documents that must cite this note (not re-derive)

1. `age_unification_gaps_v1_1.md` §11 (success criterion #5)
2. `age_migration_validation_plan_v1_1.md` §1.1 and Area 2
3. `soc_domain_scoping_v1_2.md` §1, §7
4. B-ADDENDUM architectural discussion note (referral-impact sample)
5. Any future referral impact analysis (R2/R7)
6. Any V_soc gate in the validation runner

When each adopts the §7 citation, delete its local number.

---

## 8.1 Roadmap responses

**Q1 — does `domain_source` exist?** Resolved procedurally in §3.2: run the provenance-count scan first. If 0,
adopt a fallback discriminator (saved ID list preferred; timestamp cutoff as last resort; retro-stamp if the
backfill predicate is reproducible). The note does not depend on the stamp existing — but §3's *primary*
reconciliation (scans A+B) doesn't need it at all, so this only gates the sub-population *distinction*, not the
baseline.

**Q2 — `CASE WHEN` is AGE-forbidden.** Accepted. §3.1 now uses the two-query form (A total, B null-domain
remainder), which is conclusive as a pair and uses only `count()` + `WHERE`. The three-query variant in the
roadmap message is equivalent; either is fine. No `CASE WHEN` anywhere in this note.

**Q3 — is `scorer == store == census` (rule 4) a hard gate or a monitored metric?**
Recommendation: **hard gate at release boundaries, monitored metric continuously.** Rationale — the three paths
have *already* disagreed in production (store adapter returned 0; scorer ran on in-memory state), so an
inequality is not a hypothetical to observe, it's a known failure to block. But evaluating three V computations
on every request is wasteful and can itself perturb timing. So:
- **Continuous:** log all three at a low cadence (startup, post-preseed, periodic) as a monitored metric; alert
  on any inequality.
- **Release gate (hard):** the comprehensive validation runner asserts equality and **fails the build** on any
  mismatch. No release with the three disagreeing.
This mirrors the existing posture elsewhere in the program (measure continuously, gate hard at the boundary),
and it avoids the false economy of a metric nobody blocks on. Final call is the roadmap session's; this is the
recommendation.

---

## Appendix A — the 37 pre-tagged verified decision_ids

**Not recoverable from the current graph.** §3.1 (Scan B=0, Scan C=all-backfill) established the 37 pre-tagged
rows are not present — there is nothing to enumerate here. If the original PF-6 audit saved these 37
`decision_id`s, record them here anyway: they are the evidence that would distinguish §3.1a history 1 (targeted
removal of *these specific* decisions) from history 2 (wholesale reseed). Their absence from any saved audit
artifact is itself weak evidence for reseed over targeted removal.

```
[ PF-6 saved list, if any — otherwise: none; the 37 are not in the current graph ]
```

---

## 9. Open items before FINAL

- [x] **§3.1 scans A+B+C run (2026-07-26).** Result: A=4,862, B=0, C=all `domain_source='backfill'`. Landed in
      row 3 — the 37 pre-tagged rows are not in the current graph.
- [x] **§3.1a real-vs-synthetic scan (2026-07-26):** current graph is **synthetic seed** (`SYN-DEC-*`,
      `DEC-JDOE-*`, null provenance, Mar–Jun 2025 window); outcome split = PF-1 minus 37 `correct`. Row 2.
- [x] **§3.1b roadmap decision (2026-07-26):** Option 1 — baseline the synthetic demo population with the
      reseed under the ledger. Baseline value = **4,862 (seed v1)**.
- [ ] **Deliverable 1 — pin the seed:** version the seed script, hash its output; baseline identity is
      `(4,862, seed_version_hash)`.
- [ ] **Deliverable 2 — reseed emits a ledger event:** `demo.py --reseed` / any reset writes
      `{event:"baseline_reset", v_before, v_after, date, seed_version}`.
- [ ] **Deliverable 3 — runner enforcement (THE FINAL GATE):** validation runner NO-GOs a V change with no
      matching `baseline_reset` event. *This is the only remaining blocker to FINAL* — it is what upholds §4
      rule 3 for the reseed path.
- [ ] **On deliverable 3 landing:** write `V_soc_baseline = 4,862 (seed v1, baseline_reset 2026-07-26,
      synthetic)` into §1, flip status to FINAL, convert §8 documents to the §7 citation with 4,862.
- [ ] Investigate the seed bias flagged in §3.1b (reseed dropped 37 `correct`, 0 `incorrect`) — independent of
      the baseline, does not block FINAL.
- [ ] Roadmap sign-off on §8.1 Q3 (rule 4 = hard gate at release, monitored continuously — recommended).
- [ ] Confirm SOC scorer, once AGE-backed (gaps-doc Blocker A / B1), computes §5 and equals 4,862 on first
      injection — or record the delta as a §4-rule-2 event. *(B1 has already shown scorer V = census V = 4,862;
      confirm it computes the §5 predicate, not a coincidentally-equal count.)*
- [ ] File at repo home; convert §8 documents to the §7 citation form **with the confirmed baseline**, and
      until then cite "4,899 (provisional; canonical §3.1b pending)".

*(§8.1 Q2 resolved in-document: §3.1 uses the two-query, `CASE WHEN`-free form. §8.1 Q1 / §3.2 superseded:
Scan C confirmed the stamp exists and the second sub-population is absent.)*
