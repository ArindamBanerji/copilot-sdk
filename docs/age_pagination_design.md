# AGE Pagination Design

## Problem Statement

`LegacySignalFilteringGraphStore` removes paths containing positively identified legacy signal decisions after asking AGE for one bounded result set. The AGE backend currently caps `query_context`, `contextual_judgment`, and `promotion_basis` at 100 raw paths, and each direction of `decision_movement` at 50 raw rows. If legacy paths fill those caps, valid paths beyond the first batch are never considered. The wrapper has no page arguments to request the next batch.

The design must preserve the existing public GraphStore/wrapper interfaces and native result shapes while paging inside the AGE implementation and filtering each page in the wrapper. Pagination must be bounded. Before production implementation, however, the project must resolve the path-level deterministic-order constraint documented below: the current graph model does not expose a guaranteed unique business key for every path or relationship returned by these traversals.

## Diagnostic Findings (from Phase 1)

Required prerequisites were present in `docs/session_state.md`:

- `FIX-CHAIN-1B-FIXER-2` is recorded complete.
- `REV-CHAIN-1B-FIXER-2` records the two AGE P2 findings: capped composite reads lose later visible paths, and AGE checkpoint writes discard the filtered count.
- `AGE-FIX-CHAIN-1B` records a Phase 1 halt at Option D because the current methods expose no paging arguments.
- Latest recorded test baseline: 4,179 passed, 0 failures.

Files located/read for this design:

- `../ci-platform/ci_platform/graph/age_graph_store.py`
- `../ci-platform/ci_platform/graph/age_client.py`
- `../ci-platform/ci_platform/graph/age_sdk_adapter.py`
- `copilot_sdk/copilot_sdk/graph/protocol.py`
- `copilot_sdk/copilot_sdk/graph/legacy_signal_filter.py`
- `copilot_sdk/copilot_sdk/graph/factory.py`
- `copilot_sdk/copilot_sdk/graph/dual_write_store.py`
- `copilot_sdk/copilot_sdk/backend/traversal_router.py`
- `copilot_sdk/copilot_sdk/di/query_providers.py`
- AGE tests: `../ci-platform/tests/test_age_graph_store.py`, `../ci-platform/tests/test_age_sdk_adapter.py`
- SDK tests: `tests/test_legacy_signal_filter.py`

AGE `query_context()` returns decoded path objects (`p`). `contextual_judgment()` and `promotion_basis()` also return decoded paths. `decision_movement()` returns dictionaries containing `decision`, `relationship`, `evidence`, and `direction`. No affected query currently has `ORDER BY` or `SKIP`; their `LIMIT`s are fixed literals (100, or 50 in each movement direction).

AGE `query_similar()` currently accepts a variable limit but no offset. The wrapper has a separate AGE path that issues `RETURN s ORDER BY s.created_at, s.decision_id SKIP {offset} LIMIT {size}`. This is evidence in this repository for that literal `SKIP`/`LIMIT` syntax and for a deterministic decision ordering when `decision_id` breaks timestamp ties. It does not establish a unique path/relationship key for the four traversal queries.

`AGEGraphStoreAdapter` delegates all five methods directly to `AGEGraphStore`; it adds no query or pagination behavior. `AGEClient.run_query(query, parameters=None)` accepts parameters, but `AGEGraphStore._run_query()` currently passes a complete Cypher string and `None`. The existing wrapper pagination uses bounded integer literals. This design follows that local pattern and does not require adding query-parameter plumbing.

Dual-write reads use the SQLite primary through the wrapper's `_reader()` path. The AGE pagination path therefore applies to the direct AGE adapter, not to dual-write's SQLite-primary reads. SQLite, InMemory, the GraphStore protocol, and consumer code remain unchanged.

## Design Decisions

### 4A. Deterministic Ordering (per query, with before/after Cypher)

**Important constraint:** the candidate `ORDER BY` clauses below sort on existing properties and are deterministic when their complete key tuple is unique. They are not proven to be a total ordering for every possible matched path. The graph permits generic intermediate nodes and relationships; the queries do not require each to carry a unique property. Multiple paths can share the listed endpoint properties, and `decision_movement` relationships have no universal relationship identifier in the matched pattern. No unique path key is guaranteed by the source inspected.

Therefore the clauses below are concrete ordering candidates, not approval to ship offset pagination. Before implementation, establish a total stable tie-breaker using AGE-supported existing identity (with repository evidence and tests), or get an explicit design decision that permits an alternative. Do not treat insertion order, a timestamp alone, or these non-unique tuples as a deterministic cursor. No new node properties, labels, relationships, or indexes are proposed.

#### `query_context`

Returned value: variable-length path `p`, rooted at `e.entity_id` and ending at generic node `n`. Root `e.entity_id` is constant for one call; the query guarantees `domain` on all path vertices, but no unique property on every endpoint/intermediate node.

Current Cypher:

```python
rows = self._run_query(
    f"""
    MATCH p = (e {{entity_id: {self._S(entity_id)}}})-[*1..{hop_count}]-(n)
    WHERE e.domain = {literal} AND n.domain = {literal}
      AND size([v IN nodes(p) WHERE properties(v)['domain'] = {literal} | v]) = length(p) + 1
    RETURN p
    LIMIT 100
    """
)
```

Candidate paged form (valid only after the total-key constraint is resolved):

```cypher
MATCH p = (e {entity_id: <escaped entity_id>})-[*1..<safe hops>]-(n)
WHERE e.domain = <escaped domain> AND n.domain = <escaped domain>
  AND size([v IN nodes(p) WHERE properties(v)['domain'] = <escaped domain> | v]) = length(p) + 1
RETURN p
ORDER BY e.entity_id, n.domain, n.entity_id, n.decision_id, n.event_id, n.rule_id, length(p)
SKIP <safe skip> LIMIT <safe limit>
```

These are all properties/functions already evidenced in this query family (`entity_id`, `domain`, `decision_id`, `event_id`, `rule_id`; `length(p)` already appears in its predicate). The tuple does not distinguish two paths with the same endpoints and length. Every intermediate node/relationship would need to contribute to a unique path key for the clause to be sufficient; no such generic key was found.

#### `decision_movement`

Returned value: one row per direct relationship in each direction, projected as `d`, `r`, and `e`. `d.decision_id` is fixed by the request. Evidence node `e` and relationship `r` are generic and need not have a unique business key or timestamp.

Current Cypher, outbound and inbound respectively:

```python
for direction, pattern in (
    ("outbound", f"(d:Decision {{decision_id: {decision_literal}}})-[r]->(e)"),
    ("inbound", f"(e)-[r]->(d:Decision {{decision_id: {decision_literal}}})"),
):
    linked = self._run_query(f"""
        MATCH {pattern}
        WHERE d.domain = {domain_literal}
          AND (e.domain = {domain_literal} OR e.domain IS NULL)
        RETURN d, r, e
        LIMIT 50
    """)
```

Candidate paged form, applied separately to both patterns:

```cypher
MATCH (d:Decision {decision_id: <escaped decision_id>})-[r]->(e)
WHERE d.domain = <escaped domain>
  AND (e.domain = <escaped domain> OR e.domain IS NULL)
RETURN d, r, e
ORDER BY e.domain, e.decision_id, e.entity_id, e.event_id, e.rule_id, r.timestamp, r.chain_index
SKIP <direction-specific safe skip> LIMIT <safe limit>
```

Use the same clause for inbound after substituting its existing `MATCH`. The candidate uses existing properties found in AGE decision, context, event, rule, and relationship writes. They are optional across these generic nodes and relationships and can tie (including parallel relationships), so this is not a total key. A stable unique relationship/path tie-breaker must be established before implementation. The existing wrapper output dictionary and `direction` values remain unchanged.

#### `contextual_judgment`

Returned value: path `p` ending at `j:Decision`; decision nodes have a `decision_id`, while the other endpoint `e` is selected by `entity_group` or `entity_id`. The query may produce more than one path for a decision.

Current Cypher:

```python
rows = self._run_query(f"""
    MATCH p=(e)-[*1..3]-(j:Decision)
    WHERE j.domain = {self._S(domain_value)}
      AND j.category = {self._S(str(category))}
      AND (e.entity_group = {self._S(str(entity_group))}
           OR e.entity_id = {self._S(str(entity_group))})
    RETURN p LIMIT 100
""")
```

Candidate paged form (total-key constraint still applies):

```cypher
MATCH p=(e)-[*1..3]-(j:Decision)
WHERE j.domain = <escaped domain>
  AND j.category = <escaped category>
  AND (e.entity_group = <escaped group> OR e.entity_id = <escaped group>)
RETURN p
ORDER BY j.created_at, j.decision_id, e.entity_group, e.entity_id, length(p)
SKIP <safe skip> LIMIT <safe limit>
```

`j.decision_id` provides a stable key between distinct decisions; `created_at` is an established Decision property. Multiple different paths can still end at the same decision and share endpoint values and path length. This clause alone cannot order such paths uniquely.

#### `promotion_basis`

Returned value: path `p` from generic node `r` whose `rule_id`, `source_rule`, or `target_rule` matches the requested rule, to generic node `j` in the domain or with a null domain. Neither variable is constrained to a label or unique key.

Current Cypher:

```python
rows = self._run_query(f"""
    MATCH p=(r)-[*0..3]-(j)
    WHERE r.domain = {self._S(domain_value)}
      AND (r.rule_id = {self._S(str(rule_id))}
           OR r.source_rule = {self._S(str(rule_id))}
           OR r.target_rule = {self._S(str(rule_id))})
      AND (j.domain = {self._S(domain_value)} OR j.domain IS NULL)
    RETURN p LIMIT 100
""")
```

Candidate paged form (total-key constraint still applies):

```cypher
MATCH p=(r)-[*0..3]-(j)
WHERE r.domain = <escaped domain>
  AND (r.rule_id = <escaped rule_id>
       OR r.source_rule = <escaped rule_id>
       OR r.target_rule = <escaped rule_id>)
  AND (j.domain = <escaped domain> OR j.domain IS NULL)
RETURN p
ORDER BY r.rule_id, r.source_rule, r.target_rule, j.decision_id, j.event_id, j.rule_id, length(p)
SKIP <safe skip> LIMIT <safe limit>
```

The candidate fields exist on some matching nodes but are not required on all. Multiple paths can tie. A generic unique node/path identity is not available from the current method contract or query. Establish a total key before using offset pages.

### 4B. SKIP/LIMIT Parameterization (per query)

Use internal integer arguments and interpolate only after strict integer conversion and clamping, following `LegacySignalFilteringGraphStore.query_similar()`. Do not interpolate caller strings. The repository's `AGEGraphStore._run_query()` takes a single complete Cypher string; `AGEClient` can bind a parameter mapping, but no affected call currently passes parameters. Literal bounded integers minimize plumbing and match the existing wrapper pattern.

| Traversal | Default page limit | Hard page maximum | Skip default | Hard total scan cap in wrapper |
|---|---:|---:|---:|---:|
| `query_context` | 100 | 100 | 0 | 1,000 raw paths |
| `contextual_judgment` | 100 | 100 | 0 | 1,000 raw paths |
| `promotion_basis` | 100 | 100 | 0 | 1,000 raw paths |
| `decision_movement` outbound | 50 | 50 | 0 | 500 raw rows per direction |
| `decision_movement` inbound | 50 | 50 | 0 | 500 raw rows per direction |

The current page size equals the existing hard cap, preserving the first-call batch size. The wrapper may make at most ten page requests for each traversal/direction; no unbounded loop is permitted. Each skip must also be clamped to the corresponding maximum scan bound (900 for 100-row pages; 450 for 50-row pages). A page request never asks for more than the existing cap.

Use inline safe integer literals, for example `SKIP {safe_skip} LIMIT {safe_limit}`. Keep `LIMIT` after `SKIP`, matching the existing wrapper query. Empty page, or a page shorter than requested, means backend exhaustion. If exactly full pages reach the total scan cap, stop at the cap without making an eleventh call.

### 4C. Method Signature Changes (per method)

These changes apply only to internal AGE backend methods and their adapter forwarding methods. `GraphStore`, `GraphTraversalStore`, `ProtocolV2GraphStore`, and public wrapper signatures do not change.

| Method | Current AGE signature | Proposed internal signature |
|---|---|---|
| `query_context` | `query_context(self, entity_id: str, hops: int = 2, *, domain: str) -> List[Dict[str, Any]]` | `query_context(self, entity_id: str, hops: int = 2, *, domain: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]` |
| `decision_movement` | `decision_movement(self, domain: str, decision_id: str) -> List[Dict[str, Any]]` | `decision_movement(self, domain: str, decision_id: str, *, outbound_skip: int = 0, inbound_skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]` |
| `contextual_judgment` | `contextual_judgment(self, domain: str, entity_group: str, category: str) -> List[Dict[str, Any]]` | `contextual_judgment(self, domain: str, entity_group: str, category: str, *, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]` |
| `promotion_basis` | `promotion_basis(self, domain: str, rule_id: str) -> List[Dict[str, Any]]` | `promotion_basis(self, domain: str, rule_id: str, *, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]` |

The adapter adds the same optional keyword-only arguments and forwards them unchanged. Defaults preserve the existing one-page behavior and old direct adapter/backend callers. Internally clamp page limit to `[1, 100]` or `[1, 50]` as applicable and skip to the method's scan ceiling. The wrapper's public `query_context(entity_id, max_depth, *, domain)`, `decision_movement(domain, decision_id)`, `contextual_judgment(domain, entity_group, category)`, and `promotion_basis(domain, rule_id)` signatures remain exactly as they are.

### 4D. Wrapper Pagination Strategy (algorithm, pseudocode)

The wrapper retains its current `_contains_legacy_decision()` predicate and native output filtering. No persistent cursor/cache is added.

```text
reader = existing AGE adapter reached through _reader()
page_cap = 100                 # or 50 for each movement direction
visible_cap = page_cap         # preserve current maximum visible output
raw_scan_cap = page_cap * 10   # hard bound
skip = 0
visible = []

while len(visible) < visible_cap and skip < raw_scan_cap:
    size = min(page_cap, raw_scan_cap - skip)
    rows = reader.method(existing_args, skip=skip, limit=size)
    for row in rows:
        if not _contains_legacy_decision(row):
            visible.append(row)  # keep original decoded/native shape
            if len(visible) == visible_cap:
                break
    skip += len(rows)           # advance by raw rows, including filtered rows
    if len(rows) < size:
        break                    # AGE result set exhausted
return visible
```

The loop is bounded to ten pages and filters every returned page before accumulating. A store with fewer rows than the old pre-filter cap returns the available visible subset. A result set with more legacy rows than the scan cap may still have later valid rows that this bounded algorithm does not reach; the scan cap is a deliberate resource bound and that truncation must be surfaced in internal logging/diagnostics if the existing response shape has no truncation field. Do not silently claim exhaustive traversal.

The hard guarantee is a maximum of 1,000 candidate paths for the 100-row methods and 500 candidates per movement direction. The output cap remains 100 paths per ordinary traversal and 50 rows per movement direction, retaining current maximum response sizes. Because the existing AGE order is unspecified, a strict guarantee that every call returns at least the same number of rows as one historical unspecified-order call cannot be proven. The deterministic-order prerequisite and bounded-scan truncation must be explicitly accepted before implementation.

### 4E. `decision_movement` Special Case

Keep outbound and inbound queries independent. The AGE method receives `outbound_skip`, `inbound_skip`, and a shared bounded `limit`; it executes the existing outbound pattern with its own skip and then the existing inbound pattern with its own skip. The adapter forwards those values.

The wrapper maintains a separate raw offset, visible list, and exhausted flag for each direction. It filters each directional page and stops that direction when it has 50 visible rows, receives fewer than requested, or reaches 500 raw rows. The other direction may continue. Finally concatenate outbound rows followed by inbound rows, matching today's method order and row shape. Retain each row's existing `direction` string. The result is at most 100 rows total, with a maximum of 50 per direction.

The proposed sort key (`e` identity candidates plus relationship timestamp/chain index) is not guaranteed unique for a generic endpoint and parallel edges. Resolve a stable per-edge/path ordering key before enabling offsets.

### 4F. Backward Compatibility Verification

- **GraphStore protocol:** no signature or return type changes. The optional traversal protocol and ProtocolV2 methods are untouched.
- **Wrapper public methods:** no new public arguments; returned lists and dictionaries retain their current shapes.
- **SQLite and InMemory:** no code changes. Their private read-view hooks continue to perform filtering locally and do not call AGE pagination.
- **AGE direct calls:** new internal parameters are optional and default to the current one-page limits and skip zero.
- **Consumers:** traversal router endpoints return the complete wrapper list and impose no smaller limit. `GraphEvidenceProvider.read_evidence()` calls `decision_movement()` and uses only `rows[0]`, returning `None` on empty; it does not paginate or assume 50 rows. No consumer performs its own offset loop.
- **Consumer locations:** `copilot_sdk/backend/traversal_router.py` directly exposes movement, contextual judgment, and promotion basis. `copilot_sdk/di/query_providers.py` uses movement as graph evidence. SDK `query_context` is exposed through `GraphTraversalStore` and consumed by wrapper/local implementations and tests; no router consumer was found. No direct app/ci-platform consumer of these four methods was found outside the AGE implementation/adapter.
- **Dual-write:** the SDK wrapper reads the SQLite primary. Existing dual-write query behavior is unchanged.
- **Result cardinality:** response maxima remain unchanged. Pagination can recover visible rows after earlier legacy rows, subject to the hard scan cap. Exact historical cardinality cannot be guaranteed because current AGE traversal ordering is unspecified; this and the total-key issue are release gates, not hidden assumptions.

### 4G. Blast Radius Map

Implementation production files:

**ci-platform**

- `ci-platform/ci_platform/graph/age_graph_store.py`: add safe internal skip/limit handling, add `ORDER BY` plus `SKIP`/`LIMIT` to the four traversal query forms, with separate offsets for movement. Do not proceed until stable total sort keys are established.
- `ci-platform/ci_platform/graph/age_sdk_adapter.py`: add optional internal pagination keywords and forward to the AGE backend.

**copilot-sdk**

- `copilot-sdk/copilot_sdk/graph/legacy_signal_filter.py`: only the AGE adapter branches for context, judgment, promotion basis, and movement page/filter/accumulate; keep local private read-view hooks and public method signatures unchanged.

Files that must not change:

- `copilot-sdk/copilot_sdk/graph/sqlite_store.py`
- `copilot-sdk/copilot_sdk/graph/memory_store.py`
- `copilot-sdk/copilot_sdk/graph/protocol.py`
- Consumer code, including traversal routers, scorers, and evidence providers
- AGE graph labels, relationship types, stored properties, and indexes

Test files to extend:

- **ci-platform:** `ci-platform/tests/test_age_graph_store.py` for exact query clauses, default/maximum page limits, offset clamping, and separate movement offsets; `ci-platform/tests/test_age_sdk_adapter.py` for keyword forwarding.
- **copilot-sdk:** `copilot-sdk/tests/test_legacy_signal_filter.py` for transport-aware multi-page filtering, ordering/page boundaries, bounded exhaustion, and direction-specific movement accumulation.

### Implementation Sequence (recommended order of changes)

1. Resolve the total deterministic key for every result row/path using only AGE-supported stable identity already available, or obtain explicit authorization for a different strategy. Verify ties and parallel paths are handled; do not start offset paging with the candidate clauses alone.
2. Add AGE internal safe skip/limit normalization and unit tests around method defaults, caps, and query generation. Keep the existing hard limit as the default page size.
3. Add optional pagination forwarding in `AGEGraphStoreAdapter`, with adapter tests.
4. Add AGE-specific page/filter/accumulate logic in `LegacySignalFilteringGraphStore`; keep SQLite/InMemory branches on their existing hooks.
5. Add multi-page and exhaustion regressions using the real AGE adapter/store query code with a SKIP/LIMIT-aware transport double. Include >100 legacy-before-visible context/judgment/promotion paths, >50 per movement direction, single-marker ordinary paths, exact page boundaries, and all-legacy exhaustion.
6. Review response truncation behavior for the hard scan cap and run the implementation's full validation in its own prompt.

### Risk Assessment

Primary blocker: deterministic offset pagination requires a total stable ordering key. The candidate existing business-property tuples are not unique for arbitrary paths/relationships and may tie. AGE's internal identity support was not established by the code inspected, and introducing new properties/indexes is prohibited. A subsequent implementation prompt must resolve this before coding.

Secondary risks: a fixed scan ceiling can stop before later valid rows when legacy paths dominate; concurrent graph mutations between offset pages can shift rows; offset pagination can become more expensive at larger offsets. The proposed 1,000/500 scan limits bound resource use but do not provide snapshot isolation across separate queries. Movement must keep direction offsets and exhaustion independent. No result-count/truncation field exists in the current public result shapes, so callers cannot distinguish scan-cap truncation without logs or a separately approved contract change.

### Test Strategy

Use the actual AGEGraphStore methods and adapter with a test transport that interprets each query's ordering, `SKIP`, and `LIMIT`; do not stub the composite method itself. Assert the generated Cypher preserves each original match/domain/hop/category/rule/direction predicate, includes the approved total sort key, and caps both page size and total requests. Seed more than one page of legacy paths before valid ordinary paths, verify only legacy-marked paths are filtered, and check output order and native shapes. For movement, independently exhaust one direction while continuing the other. Cover empty results, short final pages, exact page boundaries, maximum scan exhaustion, adapter defaults/forwarding, and unchanged local-backend behavior. No tests or validation commands were run for this read-only design prompt.
