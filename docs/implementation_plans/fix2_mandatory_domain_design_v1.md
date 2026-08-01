# Fix 2 Part 1 — Mandatory Domain Contract Design

## §1 Executive Summary

The contract audit found five methods requiring hardening:

- Group B: `write_outcome`, `get_decision`, `get_decision_links`, and
  `query_context` currently accept an omitted domain.
- Group C: `query_similar` has no domain parameter.
- Group D: `get_transfer_patterns`, `get_latest_conservation_statuses`, and
  `get_iks_trajectory` intentionally support cross-domain aggregation and are
  unchanged in this phase.

The protocol, AGE store, SQLite store, InMemory store, and AGE adapter will
use a required keyword-only `domain: str` for the five Group B/C methods.
Each implementation will reject a non-string or blank domain and scope its
read/write operation to that domain. This phase deliberately breaks callers
that omit domain; Part 2 updates them across the four application repos and
their tests.

The AST caller audit covered Python files under `copilot-sdk`, `ci-platform`,
`s2p-copilot`, and `gen-ai-roi-demo-v4-v50`, excluding only the protocol and
the five contract implementations/adapters themselves. It found **320
omitted-domain calls**: 234 in `copilot-sdk`, 14 in `ci-platform`, 60 in
`s2p-copilot`, and 12 in SOC. The count includes tests and application code;
Part 2 must update every listed call.

## §2 Protocol Gap Inventory

### Group A — domain already required

All of the following protocol methods already require a domain and remain
unchanged: `write_decision`, `get_decisions`, `get_all_decisions`,
`get_archived_decisions`, `get_verified_decisions`, `count_verified`,
`count_verified_decisions`, `count_correct`, `count_decisions`, `save_centroids`,
`load_latest_centroids`, `get_centroid_checkpoints`, `archive_old_decisions`,
`count_archived`, `write_entity_enrichment`, `read_entity_enrichment`,
`list_entity_enrichments`, `write_governed_decision`, `write_observation`,
`append_evidence_receipt`, `write_conservation_status`, `write_fingerprint`,
`write_centroid_checkpoint`, `write_evolution_event`, `link_entity`,
`archive_decisions`, `domain_scoped_reset`, and all `L5LearningStore` methods
whose domain is domain-specific (`copilot-sdk/copilot_sdk/graph/protocol.py:19-28,51-137,179-253,255-285,326-419`).

### Group B — optional domain, to become required

| Method | Current signature | Evidence | New contract |
|---|---|---|---|
| `write_outcome` | `domain: str \| None = None` | `copilot-sdk/copilot_sdk/graph/protocol.py:30-47` | `*, domain: str` |
| `get_decision` | `domain: str \| None = None` | `.../protocol.py:49` | `domain: str` |
| `get_decision_links` | `domain: str \| None = None` | `.../protocol.py:153-159` | `*, domain: str` |
| `query_context` | `domain: str \| None = None` | `.../protocol.py:161-167` | `*, domain: str` |

### Group C — domain absent, to be added

| Method | Current signature | Evidence | New contract |
|---|---|---|---|
| `query_similar` | `(entity_id: str, limit: int)` | `copilot-sdk/copilot_sdk/graph/protocol.py:169` | `(entity_id: str, limit: int, *, domain: str)` |

### Group D — intentionally cross-domain, unchanged

| Method | Current behavior | Boundary |
|---|---|---|
| `get_transfer_patterns` | Optional source/target filters | Explicit `source_domain` and `target_domain` when supplied; omitted means reviewed all-transfer aggregation (`protocol.py:287-303`) |
| `get_latest_conservation_statuses` | Optional domain list | Explicit `domains` list when supplied; omitted means aggregate latest status across domains (`protocol.py:312-316`) |
| `get_iks_trajectory` | Optional domain list and time range | Explicit domain list/time bounds when supplied; omitted means aggregate trajectory (`protocol.py:318-324`) |

These methods are reporting/transfer boundaries rather than single-domain
Decision reads. They remain unchanged under DD7; a future API can introduce a
separate reviewed cross-domain report contract.

## §3 Store Consistency Matrix

| Method | Protocol | AGE | SQLite | InMemory | Adapter |
|---|---|---|---|---|---|
| `write_outcome` | OPTIONAL | OPTIONAL | OPTIONAL | OPTIONAL | OPTIONAL forwarding |
| `get_decision` | OPTIONAL | OPTIONAL predicate | OPTIONAL `WHERE` | OPTIONAL filter | OPTIONAL forwarding |
| `get_decision_links` | OPTIONAL | OPTIONAL predicates | OPTIONAL, defaults to `self.domain` | OPTIONAL, defaults to `self.domain` | OPTIONAL forwarding |
| `query_context` | OPTIONAL | OPTIONAL node predicate | OPTIONAL decision checks | OPTIONAL decision checks | OPTIONAL forwarding |
| `query_similar` | ABSENT | ABSENT from signature; query only preserves source `d.domain` | ABSENT; source lookup is unscoped | ABSENT; source lookup is unscoped | ABSENT forwarding |

### AGE evidence

- `write_outcome` accepts optional domain and conditionally builds the
  Decision predicate (`ci-platform/ci_platform/graph/age_graph_store.py:886-977`).
- `get_decision` conditionally emits `WHERE d.domain = ...`
  (`.../age_graph_store.py:2049-2061`).
- `get_decision_links` only adds domain clauses when provided
  (`.../age_graph_store.py:2689-2754`).
- `query_context` only adds its `n.domain` predicate when provided
  (`.../age_graph_store.py:3097-3120`).
- `query_similar` has no domain parameter and only relates candidates to the
  source domain (`.../age_graph_store.py:3121-3134`).

### InMemory evidence

- `write_outcome` checks the Decision domain only when domain is non-None
  (`copilot-sdk/copilot_sdk/graph/memory_store.py:549-607`).
- `get_decision` returns by ID when domain is omitted
  (`.../memory_store.py:1068-1072`).
- `get_decision_links` treats a missing domain as the store domain
  (`.../memory_store.py:1781-1802`).
- `query_context` filters Decision rows only when domain is supplied and uses
  unscoped internal lookups (`.../memory_store.py:1804-1895`).
- `query_similar` finds its source by ID and candidates by source domain, but
  has no caller-supplied domain (`.../memory_store.py:1897-1932`).

### SQLite evidence

- `write_outcome` branches between an unscoped Decision lookup and a
  domain-qualified lookup (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:1159-1239`).
- `get_decision` omits `domain` from SQL when it is None
  (`.../sqlite_store.py:2143-2154`).
- `get_decision_links` defaults to the instance domain when no domain is
  supplied (`.../sqlite_store.py:2781-2822`).
- `query_context` performs unscoped root and linked Decision lookups and only
  conditionally compares the supplied domain (`.../sqlite_store.py:2824-2923`).
- `query_similar` uses an unscoped source lookup and has no domain argument
  (`.../sqlite_store.py:2925-2950`).

### AGE adapter evidence

The adapter mirrors the optionality and conditionally forwards domain:
`write_outcome` at `ci-platform/ci_platform/graph/age_sdk_adapter.py:84-121`,
`get_decision` at `:289-290`, `get_decision_links` at `:554-565`,
`query_context` at `:567-576`, and `query_similar` at `:579-580`.

## §4 Caller Audit

The audit used AST call analysis rather than text-only matching. A call was
classified as domain-bearing when it supplied `domain=` or the current
positional domain slot. Contract implementation calls were excluded from the
Part 2 caller count. The following are every omitted-domain call, grouped by
repository, method, file, and line. Definitions and the five implementation
files are not callers.

### `copilot-sdk` — 232 omitted calls

**`get_decision_links` (12):**

- `tests/test_graphstore_consolidation.py:247,252,269,274`
- `tests/test_graph_entity_links.py:169,174,184,189,201,207,220`
- `tests/graph/test_protocol_v2_conformance.py:2085`

**`get_decision` (117):**

- `apps/purchasing/backend/tests/test_purchasing_active_age_live.py:53,67`
- `apps/trading/backend/tests/test_multi_trader.py:148,163`
- `apps/trading/backend/tests/test_regime_throttle.py:74`
- `apps/trading/backend/tests/test_trading_active_age_live.py:56,67,82,96`
- `apps/trading/backend/tests/test_vol_analytics.py:154`
- `tests/test_dual_write_store.py:130`
- `tests/test_entity_enrichment.py:501`
- `tests/test_generate_decision_id.py:81`
- `tests/test_graphstore_consolidation.py:144,163,181,197,233`
- `tests/test_situation_analyzer.py:64`
- `tests/backend/test_scoring_router.py:136,243,294,424`
- `tests/graph/test_decision_metadata.py:32,41,55,65,80,100`
- `tests/graph/test_memory_store.py:31,99`
- `tests/graph/test_protocol_v2_conformance.py:458,494,495,505,525,544,548,562,573,586,607,628,649,686,724,776,801,932,933,959,960,961,1042,1043,1044,1270,1286,1298,1383,1429,2097,2233,2281,2307,2313,2314,2315,2334,2366,2406,2407,2408,2409,2428,2429,2540,2574,2575,2595,2706,2707,2708,2709,2740,2741,2742,2743,2744,2843,2847,3050,3072,3093,3112,3166,3180,3384,3388,3507`
- `tests/graph/test_sqlite_store.py:52,84`
- `tests/scoring/test_scorer.py:150,159,164,179,250`
- `tests/scoring/test_scorer_governed.py:84,93,115,132,133,144,156`
- `tests/scoring/test_storage.py:32,315,347`

**`query_context` (2):** `tests/test_situation_analyzer.py:451,472`.

**`write_outcome` (103):**

- `apps/purchasing/backend/tests/test_purchasing_backend.py:706,727,733,886`
- `apps/trading/backend/tests/test_pre_scorer.py:363`; `test_promotion_engine.py:367`; `test_regime_classifier.py:314`; `test_trading_backend.py:697,718,724,794`; `test_trust_analysis.py:114`
- `integrity/test_innovation_claims.py:116,135,143`
- `tests/test_conservation_formula.py:42`; `test_dual_write_store.py:59,80,100,191,218,233,242`; `test_entity_enrichment.py:499`; `test_judgment_conflict.py:286`; `test_learn_context.py:122`; `test_measurement_state.py:55`; `test_migration_live_age.py:284`; `test_response_models.py:232`; `test_weekly_report.py:94`
- `tests/backend/test_scoring_router.py:246,297`; `test_self_computation.py:45,46`; `test_self_computation_router.py:42,43`
- `tests/graph/test_memory_store.py:46,60,71,72,87,88,89,117,118,214,271`
- `tests/graph/test_protocol_v2_conformance.py:585,601,627,643,680,697,707,719,722,752,771,772,799,867,881,956,957,1392,1472,2302,2329,2349,2445,2700,2724,2725,2726,2727,2753,2880,3063,3066,3086,3105,3387`
- `tests/graph/test_sqlite_store.py:69,70,103,104,131,132,133,265,410,430`
- `tests/scoring/test_conservation.py:42`; `test_j6_persistence.py:165,199`; `test_persistence_outbox.py:138`; `test_scorer.py:827,846`; `test_storage.py:50,56,70,321,329`

### `ci-platform` — 14 omitted calls

- `get_decision`: `tests/test_age_sdk_adapter.py:369,739`
- `get_decision_links`: `tests/test_age_graph_store.py:1924`; `tests/test_age_graph_store_v.py:250`; `tests/test_age_sdk_adapter.py:644`
- `query_context`: `tests/test_age_graph_store.py:282`
- `query_similar`: `tests/test_age_graph_store.py:283`
- `write_outcome`: `tests/test_age_graph_store.py:364,385,2128`; `tests/test_age_graph_store_v.py:209,261`; `tests/test_age_sdk_adapter.py:329,740`

### `s2p-copilot` — 60 omitted calls

- `get_decision_links`: `backend/app/routers/s2p.py:810,836`; `app/routers/s2p_evidence.py:231`; `app/services/s2p_situation_pattern.py:158`; `app/services/situation_graph_enrichment.py:192`; `backend/tests/test_graph_links.py:88,108,144,291,330`; `test_s2p_graph_reader.py:84,118,170`; `test_situation_graph_enrichment.py:129,406`; `test_situation_traversals.py:334,340`
- `get_decision`: `backend/app/routers/s2p.py:1571,1636,2092,2211`; `app/routers/s2p_evidence.py:247`; `app/routers/s2p_explorer.py:339`; `app/routers/s2p_situation.py:142`; `app/services/centroid_explorer.py:192`; `app/services/s2p_context_builder.py:529`; `app/services/s2p_situation_pattern.py:143,165`; `app/services/situation_graph_enrichment.py:197`; `app/services/situation_traversals.py:647`; tests `test_graphstore_consolidation.py:72,90`, `test_s2p_active_age_live.py:79,111,150,193`, `test_s2p_active_age_parallel.py:125`, `test_s2p_active_age_phase_b.py:654,665,666`, `test_s2p_graph_reader.py:75,106,116,168`, `test_s2p_preset_and_invoice_link.py:61,93`, `test_s2p_shadow_live_age.py:126,165,215`, `test_situation_graph_enrichment.py:48,405`, `test_situation_traversals.py:203,216,237,388`
- `query_context`: `backend/app/routers/s2p.py:144`; `app/services/situation_traversals.py:433`; `tests/test_s2p_graph_reader.py:85`
- `query_similar`: `backend/app/services/situation_traversals.py:656`
- `write_outcome`: `backend/tests/test_s2p_enrichment.py:53`

### `gen-ai-roi-demo-v4-v50` — 12 omitted calls

- `get_decision`: `backend/tests/test_dual_update_fix.py:269`; `test_rl_triage_integration.py:170,187,201,221`; `tests/test_soc_triage_harness.py:24,41,51,58,66`; `test_triggered_evolution.py:153`
- `write_outcome`: `backend/tests/test_j6_state_capture.py:62`

The follow-up must also inspect positional and dynamically dispatched calls
after these edits; the AST count is the complete current Python call census,
not a substitute for test execution.

## §5 Cross-Domain Method Design

**Decision: DD7 / Option DD1 — leave Group D unchanged.** These methods are
explicitly aggregation/reporting APIs. `get_transfer_patterns` has source and
target domain filters; `get_latest_conservation_statuses` and
`get_iks_trajectory` accept domain lists. Their current omitted-filter
behavior means “all domains,” which is appropriate for reviewed cross-copilot
dashboards and transfer analysis. This phase does not silently reinterpret
those APIs as single-domain Decision reads.

A future hardening pass may add a separate `CrossDomainReport` protocol that
requires an explicit domain list, but making these parameters mandatory in
Fix 2 would break cross-copilot proof/report consumers outside the five
single-domain methods and is not required to close the Group B/C leak.

## §6 Design Decisions

**DD1 — Required domain.** All Group B/C methods use a required `domain: str`.
Where existing optional parameters precede it, domain is keyword-only:
`write_outcome(..., *, domain: str, ...)`,
`get_decision_links(..., *, domain: str, ...)`,
`query_context(..., *, domain: str, ...)`, and
`query_similar(..., *, domain: str)`. `get_decision` uses a required second
parameter. This avoids illegal Python signatures and makes the migration
call sites unambiguous.

**DD2 — Validate non-empty string.** Every changed implementation rejects
non-string or whitespace-only domains with `ValueError`. The AGE store uses
its existing safe-domain validator (`ci-platform/ci_platform/graph/age_graph_store.py:547-556`).
SQLite and InMemory add equivalent local validation before any read/write.

**DD3 — Match the requested domain.** Reads always use the supplied domain.
`write_outcome` must find/update the Decision in that domain; a Decision in a
different domain behaves as missing and raises the existing `KeyError`/write
failure. No implementation may fall back to its configured default domain.

**DD4 — AGE predicates.** AGE `get_decision`, `get_decision_links`,
`query_context`, and `query_similar` always include a validated domain
predicate. `write_outcome` always uses the domain-qualified Decision and
Outcome patterns. Queries remain literal-safe and use existing serialization;
no `$` placeholders or reserved aliases are introduced.

**DD5 — InMemory filters.** InMemory `get_decision`, links, context, and
similar queries use the supplied domain throughout root lookup, edge lookup,
candidate selection, and nested traversal. Internal helpers gain a domain
argument where needed; the public response shape remains unchanged.

**DD6 — SQLite filters.** SQLite always includes `domain = ?` in Decision,
edge, context, and similar lookups. Internal `_get_entity_links` calls gain a
domain argument. Existing schema/indexes remain unchanged.

**DD7 — Group D unchanged.** Cross-domain reporting methods retain optional
filters and their reviewed all-domain behavior.

**DD8 — No deprecation period.** Omitted domain must fail immediately with
Python `TypeError`. A compatibility default would preserve the exact
cross-domain leak this fix is intended to close. Part 2 updates all audited
callers in the same migration.

## §7 Implementation Plan Part 1 — Contract Layer

1. **Protocol:** change the five Group B/C signatures in
   `copilot-sdk/copilot_sdk/graph/protocol.py:30-47,49,153-169`; preserve
   Group A and Group D.
2. **AGE store:** change signatures at
   `ci-platform/ci_platform/graph/age_graph_store.py:886,2049,2689,3097,3121`;
   validate domain, remove optional branches, and add domain predicates.
3. **SQLite store:** change signatures at
   `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1159,2143,2781,2824,2925`;
   validate domain and thread it through every SQL/internal lookup.
4. **InMemory store:** change signatures at
   `copilot-sdk/copilot_sdk/graph/memory_store.py:549,1068,1781,1804,1897`;
   validate domain and thread it through all in-memory traversal helpers.
5. **AGE adapter:** change signatures at
   `ci-platform/ci_platform/graph/age_sdk_adapter.py:84,289,554,567,579`;
   require and forward domain unconditionally.
6. **Conformance tests:** add
   `copilot-sdk/tests/graph/test_domain_required_conformance.py` with real
   InMemory and SQLite stores. Cover omission `TypeError`, empty-domain
   `ValueError`, domain-only results, wrong-domain empty results, outcome
   writes, links, context, similar, and nested traversal.

Each step is a one-file edit boundary. Re-read the file, run mypy before its
targeted pytest command, and stop/revert if a new failure is introduced.

## §8 Implementation Plan Part 2 — Caller Updates

Part 2 updates the 320 omitted calls listed in §4, in this order:

1. **SDK core and tests:** update 234 calls in the SDK list, starting with
   `copilot-sdk/copilot_sdk` consumers and then graph/scoring/backend tests.
   Every store fixture must carry the domain used to seed its Decision.
2. **CI platform tests:** update 14 AGE/adapter test calls with the domain
   used by each fake graph (`soc` where the existing tests use SOC fixtures).
3. **S2P production first:** update application callers at
   `backend/app/routers/s2p.py`, evidence/explorer/situation routers, and
   services. Pass `domain="s2p"` or the existing `DOMAIN` constant. Then
   update the 42 S2P test calls listed in §4.
4. **SOC tests:** update the 12 calls in the SOC harness and triage tests to
   pass `domain="soc"`.
5. Run an AST audit again; only intentional negative tests that deliberately
   omit domain may remain, and those must call a concrete method through a
   type-erased test handle so the omission is explicitly tested.

Part 2 must not add defaults, alter Group D calls, or weaken the protocol.

## §9 Risk Analysis

| Risk | What could go wrong | Mitigation |
|---|---|---|
| Missed caller | Runtime `TypeError` or failed production route | Complete AST census, per-repo caller checklist, and full suites after Part 2 |
| Cross-domain read | A Decision from another copilot is returned | Required domain plus store-level predicate/filter tests with SOC and Trading data |
| Wrong test domain | Existing fixture becomes invisible or fails as missing | Derive domain from store constructor and seeded Decision in each caller update |
| AGE predicate regression | AGE query syntax or reserved alias breaks | Re-read generated Cypher; run AGE store tests and Rule #75 checks |
| Adapter omission | Contract appears hardened but AGE callers bypass it | Adapter conformance tests assert domain is forwarded to the fake underlying store |
| `query_similar` redesign | Source/candidate domain mismatch or empty results | Require domain, scope source and candidates, and add two-domain conformance data |
| Outcome write breakage | Existing scorer writes fail until Part 2 callers update | Expected staged failure is recorded; do not restore optional fallback |
| Group D over-hardening | Cross-copilot reports lose data | Leave Group D unchanged and add explicit tests documenting its aggregate semantics |
| Nested context leak | Root is scoped but neighbor lookup is not | Thread domain through every internal edge/Decision helper and test foreign-domain neighbors |

## §10 Reading Log

| File/resource | Scope |
|---|---|
| `copilot-sdk/docs/implementation_plans/jm_gap_closure_plan_v1.md` | Full file; §4 Fix 2 |
| `copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md` | Full file; §§2.1-2.5 and §4 |
| `copilot-sdk/CLAUDE.md` | Full file, 1-139 |
| `ci-platform/CLAUDE.md` | Full file, 1-120 |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | Full file, 1-428 |
| `ci-platform/ci_platform/graph/age_graph_store.py` | Full file; changed methods and validators audited |
| `copilot-sdk/copilot_sdk/graph/memory_store.py` | Full file; changed methods and traversal helpers audited |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | Full file; changed methods and SQL helpers audited |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py` | Full file; all five adapter methods audited |
| `copilot-sdk`, `ci-platform`, `s2p-copilot`, `gen-ai-roi-demo-v4-v50` | Repository-wide Python AST caller audit |

DESIGN_READY: YES
