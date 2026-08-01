# Link-Decision-to-Entity Domain Contract Completion

## §1 Contract Consistency Matrix

The audit found repository drift from the prompt's stated protocol state.
`GraphStore` does not declare `link_decision_to_entity`; the protocol test
explicitly asserts that this legacy helper is not protocol required
(`copilot-sdk/tests/graph/test_protocol.py:164-166`). This plan completes the
concrete-store contract without widening the public `GraphStore` protocol.

| Implementation | Domain parameter | Required | Domain stored/used | Domain validated | Status |
|---|---|---:|---|---:|---|
| `GraphStore` protocol | Absent (`protocol.py:1-428`; absence asserted at `tests/graph/test_protocol.py:164-166`) | N/A | N/A | N/A | CONFORMANT to current narrow design; prompt context is stale |
| AGE store | `domain: str`, keyword-only (`ci-platform/ci_platform/graph/age_graph_store.py:2656-2663`) | Yes | Decision predicate and edge/fallback properties (`.../age_graph_store.py:2664-2691,2736-2743`) | Rejects blank domain (`.../age_graph_store.py:2664-2666`) | CONFORMANT |
| AGE SDK adapter | `domain: str`, keyword-only (`ci-platform/ci_platform/graph/age_sdk_adapter.py:539-546`) | Yes | Forwards `domain=domain` (`.../age_sdk_adapter.py:547-552`) | Delegates to AGE | CONFORMANT |
| SQLite store | Absent; derives from Decision/store (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:2752-2762`) | No | Inserts domain into `decision_entity_edges` (`.../sqlite_store.py:2764-2771`) | No explicit validation | GAP |
| InMemory store | Absent; derives from Decision/store (`copilot-sdk/copilot_sdk/graph/memory_store.py:1755-1763`) | No | Stores domain on `_edges` (`.../memory_store.py:1764-1771`) | No explicit validation | GAP |

Target: both concrete stores accept required keyword-only `domain: str`,
reject blank domains, preserve the supplied domain, and reject a supplied
domain conflicting with an existing Decision. The legacy behavior of creating
a link record when the Decision is absent is retained for compatibility.

## §2 Caller Audit

The repository-wide Python scan found these relevant references. AGE and the
S2P enrichment production caller already pass domain; the omitted-domain
concrete calls must be updated.

| Caller | File:Line | Passes domain? | Domain value | Store/double | Classification |
|---|---:|---:|---|---|---|
| AGE adapter delegation | `ci-platform/ci_platform/graph/age_sdk_adapter.py:547-552` | Yes | forwarded | AGE | implementation |
| AGE tests | `ci-platform/tests/test_age_graph_store.py:1860,1875-1877,1892-1893` | Yes | `soc` | AGE | tests |
| AGE adapter test | `ci-platform/tests/test_age_sdk_adapter.py:641-649` | Yes | `soc` | adapter | test |
| S2P invoice route | `s2p-copilot/backend/app/routers/s2p.py:808-819` | Yes | `s2p` | ProtocolV2 store | production |
| S2P enrichment | `s2p-copilot/backend/app/services/situation_graph_enrichment.py:133-157` | Yes | `DOMAIN` (`s2p`) | GraphStore | production |
| S2P evidence tests | `s2p-copilot/backend/tests/test_evidence_graph_query.py:44-49,80-85` | No | `s2p` | app store | tests |
| S2P traversal tests | `s2p-copilot/backend/tests/test_situation_traversals.py:67,83` | No | `s2p` | InMemory | tests |
| SDK link tests | `copilot-sdk/tests/test_graph_entity_links.py:167,182` | No | store domains | SQLite/InMemory | tests |
| SDK consolidation tests | `copilot-sdk/tests/test_graphstore_consolidation.py:243,262` | No | store domains | InMemory/SQLite | tests |
| SDK situation tests | `copilot-sdk/tests/test_situation_analyzer.py:449,470` | No | `test` | InMemory | tests |
| SDK protocol-v2 test | `copilot-sdk/tests/graph/test_protocol_v2_conformance.py:2670-2671` | No | `test` | SQLite | test |
| S2P concurrent test double | `s2p-copilot/backend/tests/test_graph_links.py:215-240` | No | `s2p` | stateful double | test double |
| S2P guard doubles | `s2p-copilot/backend/tests/test_s2p_audit_export.py:58-66`; `test_s2p_active_age_phase_b.py:266-276` | N/A | `s2p` | test doubles | declarations |
| SDK cross-copilot double | `copilot-sdk/tests/test_cross_copilot_integration.py:131` | N/A | test-specific | test double | declaration |

There are 13 omitted-domain concrete call locations: two evidence calls,
two traversal calls, two SDK graph-link calls, two consolidation calls, two
situation-analyzer calls, two protocol-v2 calls, and the concurrent S2P
double's call at `test_graph_links.py:240`. Definitions of test doubles are
updated only where their callers receive the new keyword.

## §3 Schema Impact

### SQLite

The link table is `decision_entity_edges`; it already declares
`domain TEXT NOT NULL DEFAULT ''` (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:565-572`).
The migration loop includes this table (`.../sqlite_store.py:712-729`), and
`_ensure_domain_column` adds a missing domain column and fills blank/NULL rows
with the configured store domain (`.../sqlite_store.py:958-970`). A domain
index is also created (`.../sqlite_store.py:970`). No new schema migration
or `ALTER TABLE` is needed.

Existing databases are already auto-migrated by `_ensure_migrations`; legacy
blank rows are assigned the configured store domain. The fix must not change
the existing uniqueness key `(decision_id, entity_id, domain)`
(`.../sqlite_store.py:934-950`).

### InMemory

Links are stored in `_edges: list[dict[str, Any]]`
(`copilot-sdk/copilot_sdk/graph/memory_store.py:327-354`). The current legacy
method already records domain, decision ID, entity ID, edge type, and creation
time (`.../memory_store.py:1755-1771`). Only the contract and validation need
to change; no new collection is required.

### AGE reference

AGE creates a relationship with domain in the property map and uses the
Decision domain in the match predicate
(`ci-platform/ci_platform/graph/age_graph_store.py:2670-2691`). Its fallback
`DecisionEntityLink` node also receives domain through `_link_props`
(`.../age_graph_store.py:2727-2743`).

## §4 Risk Analysis

### Backward compatibility

Adding a required keyword changes callers that omit domain; §2 identifies
them. Existing SQLite rows remain readable because the schema already has a
non-null domain and auto-migration fills legacy blanks
(`copilot-sdk/copilot_sdk/graph/sqlite_store.py:958-970`). Link readers select
named columns and return dictionaries (`.../sqlite_store.py:2780-2822`), while
InMemory removes the internal domain before returning public rows
(`copilot-sdk/copilot_sdk/graph/memory_store.py:1774-1788`).

### Cross-domain links

Both stores will reject blank domains. If a Decision exists, its stored domain
must equal the supplied domain; otherwise the method raises `ValueError`. If
no Decision exists, legacy link-record behavior remains, with the explicit
domain stored. This prevents relabeling an existing Decision without breaking
old fallback tests.

The stores are configured with domains (`SQLiteGraphStore.__init__` at
`copilot-sdk/copilot_sdk/graph/sqlite_store.py:379-395`; InMemory constructor
at `copilot-sdk/copilot_sdk/graph/memory_store.py:327-354`). We will not add a
separate `domain == self.domain` restriction: the existing Decision match is
the authoritative consistency check, and the readers remain scoped to their
configured domain.

### Test blast radius

The direct omitted-domain calls in §2 must be updated. Protocol narrowness
tests remain unchanged: adding this legacy helper to `GraphStore` would make
minimal structural stores fail and contradict
`copilot-sdk/tests/test_graphstore_consolidation.py:101-103`. New conformance
tests use real SQLite and InMemory stores; no mocks or monkeypatches are
needed.

## §5 Design Decisions

**DD1 — Required concrete parameter.** `domain: str` is required and
keyword-only in SQLite and InMemory, matching AGE and the adapter. The public
`GraphStore` protocol is not widened because the source intentionally keeps
this legacy helper outside the protocol (`copilot-sdk/tests/graph/test_protocol.py:164-166`).

**DD2 — Reject empty domain.** Both stores call `str(domain).strip()` and
raise `ValueError` for an empty result, matching AGE's validation
(`ci-platform/ci_platform/graph/age_graph_store.py:2664-2666`).

**DD3 — Validate existing Decision domain.** When a Decision is present, its
domain must equal the supplied domain; mismatch raises `ValueError`. Missing
Decisions retain legacy link-record behavior, with the explicit domain stored.

**DD4 — No new backfill.** Existing SQLite rows are handled by the existing
domain migration; this fix does not rewrite them.

**DD5 — Keep auto-migration.** No separate script is warranted because
`decision_entity_edges.domain` and its migration already exist
(`copilot-sdk/copilot_sdk/graph/sqlite_store.py:934-970`).

## §6 Implementation Plan

### Step 1 — SQLite concrete contract

- **File:** `copilot-sdk/copilot_sdk/graph/sqlite_store.py`.
- **Change:** Change `link_decision_to_entity` to accept `*, domain: str`;
  normalize/reject blank domain; inspect the existing Decision and reject a
  conflicting domain; insert the supplied domain rather than deriving it
  (`.../sqlite_store.py:2752-2771`). Leave schema and uniqueness unchanged.
- **Must not change:** edge type default, duplicate handling, timestamps,
  reader output shape, or migration behavior.
- **Tests:** explicit-domain storage; omitted-domain `TypeError`; blank-domain
  `ValueError`; mismatched existing Decision `ValueError`; duplicate remains
  one row; missing-Decision legacy link remains writable with explicit domain.
- **Verify:** `mypy copilot_sdk/graph/sqlite_store.py`; then
  `python -m pytest tests/ -q --timeout=60 -k "link_decision or entity_link"`.

### Step 2 — InMemory concrete contract

- **File:** `copilot-sdk/copilot_sdk/graph/memory_store.py`.
- **Change:** Add required keyword-only `domain: str`; normalize/reject blank;
  reject a conflicting existing Decision; write supplied domain into the
  existing `_edges` record (`.../memory_store.py:1755-1771`).
- **Must not change:** `_edges` internal shape, public link output, duplicate
  behavior, or domain filtering.
- **Tests:** the same positive, negative, mismatch, and regression cases as
  SQLite using a real InMemory store.
- **Verify:** `mypy copilot_sdk/graph/memory_store.py`; then the targeted link
  test command above.

### Step 3 — Update concrete callers and stateful doubles

- **Files:** omitted-domain callers in §2, especially
  `s2p-copilot/backend/tests/test_evidence_graph_query.py`,
  `s2p-copilot/backend/tests/test_situation_traversals.py`, the five listed
  SDK test files, and `s2p-copilot/backend/tests/test_graph_links.py`.
- **Change:** pass audited domains explicitly. Update stateful test-double
  signatures to accept keyword-only `domain` and assert/store it rather than
  dropping it. Do not add permissive defaults to production stores.
- **Must not change:** S2P routing behavior, response shapes, entity IDs,
  edge types, or protocol-narrowness assertions.
- **Tests:** run each changed test file after its edit; retain negative tests
  for missing Decisions and duplicate links.
- **Verify:** `mypy` on each changed Python file followed by
  `python -m pytest <changed-file> -v --timeout=60`.

### Step 4 — New concrete-store conformance tests

- **File:** `copilot-sdk/tests/graph/test_link_domain_conformance.py`.
- **Change:** parameterize over real InMemory and SQLite stores. Seed a
  Decision through `write_decision`, link with explicit domain, inspect the
  stored SQLite row or link result, and cover missing/blank/mismatch failures
  plus duplicate/read regression.
- **Must not change:** no mocks, monkeypatches, or protocol widening.
- **Verify:** `python -m pytest tests/graph/test_link_domain_conformance.py -v --timeout=30`.

### Step 5 — Full validation

- `cd copilot-sdk; python -m pytest tests/ -q --timeout=120 -k "link or entity"`
- `cd s2p-copilot/backend; python -m pytest tests/ -q --timeout=300`
- `cd ci-platform; python -m pytest tests/ -q --timeout=120`
- Re-run the new conformance file and confirm protocol-narrowness tests were
  not weakened.

## §7 Reading Log

| File | Read scope |
|---|---|
| `copilot-sdk/CLAUDE.md` | Full, 1-139 |
| `ci-platform/CLAUDE.md` | Full, 1-120 |
| `copilot-sdk/docs/design/jm_implementation_review_part2a_v1.md` | Full, 1-256; §3.2 reviewed |
| `copilot-sdk/docs/implementation_plans/jm_gap_closure_plan_v1.md` | Full; Fix 5 reviewed |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | Full, 1-428 |
| `ci-platform/ci_platform/graph/age_graph_store.py` | Full, 1-3237; link path 2656-2743 |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py` | Full, 1-620; adapter path 539-552 |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | Full, 1-3501; schema/migrations 404-970; link path 2752-2822 |
| `copilot-sdk/copilot_sdk/graph/memory_store.py` | Full, 1-2003; constructor, decision, link, and reader paths reviewed |
| Caller/test files in §2 | Full files read; direct calls and test-double contracts audited |

DESIGN_READY: YES
