# P42 DI NL Query Extension Plan

Date: 2026-06-14

## Executive Verdict

READY_FOR_IMPLEMENTATION: YES

P42 can be implemented as an additive extension to the existing deterministic
`NLQueryRouter`. The current router has a stable constructor-free class shape,
`query(question: str, graph_store: Any) -> dict[str, Any]`, deterministic intent
classification, graph-store decision-list access, and safe unknown/empty
fallbacks. P42 does not need GraphStore protocol changes, scorer changes, raw DB
queries, external API calls, or LLM parsing.

Key evidence:

- `NLQueryRouter` currently has no explicit constructor and exposes `query(question, graph_store)` returning dictionaries (`copilot_sdk/di/nl_query.py:8`, `copilot_sdk/di/nl_query.py:11`).
- Existing classification is deterministic keyword matching (`copilot_sdk/di/nl_query.py:22`).
- Existing decision access is through `get_verified_decisions` and `get_all_decisions` on the provided store (`copilot_sdk/di/nl_query.py:55`).
- GraphStore already exposes `get_decision`, `get_decisions`, `get_all_decisions`, and `get_verified_decisions` (`copilot_sdk/graph/protocol.py:39`, `copilot_sdk/graph/protocol.py:42`, `copilot_sdk/graph/protocol.py:50`, `copilot_sdk/graph/protocol.py:53`).
- SQLiteGraphStore returns decision dictionaries with category, factors, recommended action, confidence, metadata, and created_at (`copilot_sdk/graph/sqlite_store.py:2843`).
- Verified decision rows add actual action, correctness, verified_at, and context (`copilot_sdk/graph/sqlite_store.py:2869`).

## Current NL Router

### Constructor

`NLQueryRouter` has no explicit `__init__`; callers instantiate it with
`NLQueryRouter()` today. Preserve this behavior. If P42 adds pattern injection,
make it optional, for example `NLQueryRouter(patterns: Sequence[QueryPattern] |
None = None)`, so existing construction remains valid.

Evidence: class starts directly with `query()` and no constructor
(`copilot_sdk/di/nl_query.py:8`).

### Query Signature

Current signature:

```python
query(self, question: str, graph_store: Any) -> dict[str, Any]
```

The implementation normalizes the question, handles empty strings safely, then
classifies and executes (`copilot_sdk/di/nl_query.py:11`).

P42 should preserve this signature. If direct decision-list querying is needed,
add an optional keyword-only argument only after preserving the existing
positional API, for example:

```python
query(self, question: str, graph_store: Any = None, *, decisions: list[dict[str, Any]] | None = None) -> dict[str, Any]
```

Preferred implementation: continue to accept `graph_store` and use a private
decision reader so existing callers do not change.

### Existing Intents

Existing intents and keyword families:

- `source_reliability`: confidence, trust, reliable, reliability (`copilot_sdk/di/nl_query.py:24`)
- `freshness`: fresh, freshness, stale, late (`copilot_sdk/di/nl_query.py:26`)
- `recurrence`: recurring, recurrence, repeat, again (`copilot_sdk/di/nl_query.py:28`)
- `impact`: impact, blast, downstream, affected (`copilot_sdk/di/nl_query.py:30`)
- `metric`: metric, revenue, answer, how much, what was (`copilot_sdk/di/nl_query.py:32`)
- `unknown`: fallback (`copilot_sdk/di/nl_query.py:34`)

P42 must not shadow these high-priority existing intents. The safest design is:

1. Let current `_classify_intent()` run first.
2. If it returns a known existing intent, execute existing behavior.
3. Only run extended query patterns when existing classification returns
   `unknown`, or when an extended pattern has explicit opt-in keywords that do
   not collide with the existing intent families.

### Existing Return Shape

Known intent return shape:

```python
{
  "intent": intent,
  "answer": answer,
  "evidence": evidence,
  "query_template": template,
}
```

Evidence: existing `_execute()` returns these fields (`copilot_sdk/di/nl_query.py:47`).

Unknown/empty return shape:

```python
{
  "intent": "unknown",
  "answer": "...",
  "evidence": [],
}
```

Evidence: empty question fallback (`copilot_sdk/di/nl_query.py:13`) and unknown
intent fallback (`copilot_sdk/di/nl_query.py:36`).

P42 `QueryResult.to_dict()` should preserve at least `intent`, `answer`, and
`evidence`; extended fields can be additive:

```python
{
  "intent": "aggregation",
  "answer": "...",
  "evidence": [...],
  "query_template": "python:AggregationPattern",
  "metadata": {...},
  "result": {...},
}
```

### Current Fallback Behavior

Empty question: asks the user to ask a DataOps question
(`copilot_sdk/di/nl_query.py:13`).

Unknown query: returns no evidence and says it could not map the question
(`copilot_sdk/di/nl_query.py:36`).

P42 should preserve both.

### Existing Tests

No dedicated `test_nl_query.py` currently exists. DI tests cover profiler and
router surfaces:

- `tests/test_di_profiler.py`
- `tests/test_di_router.py`

`test_di_router.py` proves DI profile router behavior, profile cache behavior,
and DataOps app mounting (`tests/test_di_router.py:46`, `tests/test_di_router.py:52`,
`tests/test_di_router.py:99`, `tests/test_di_router.py:151`).

P42 should add dedicated tests in `tests/test_nl_query_extended.py` and avoid
modifying `tests/test_di_profiler.py`.

## Decision Data Contract

P42 patterns operate on lists of Python decision dictionaries. They must not
issue raw DB queries.

### Minimum Fields

Required behavior must be tolerant of missing fields. Patterns should use:

- `decision_id`: `decision["decision_id"]` or metadata fallback.
- `category`: `decision["category"]` or metadata fallback.
- `recommended_action`: `decision["recommended_action"]` or action fallback.
- `confidence`: numeric if present.
- `created_at`: numeric epoch, ISO string, or metadata fallback.
- `source/entity fields`: `source_id`, `source_ids`, `supplier_id`, `supplier`,
  `source`, `system`, `entity_id`, including metadata fallbacks.
- `correctness`: `is_correct`, `correct`, verified outcomes, or recommended vs
  actual action when both exist.

Evidence:

- Current NL decision payload already extracts `decision_id`, `category`,
  `source_ids`, `confidence`, and numeric factors (`copilot_sdk/di/nl_query.py:78`).
- SQLite decision dictionaries include `decision_id`, `domain`, `entity_id`,
  `category`, `factors`, `factor_vector`, `recommended_action`, `confidence`,
  `metadata`, and `created_at` (`copilot_sdk/graph/sqlite_store.py:2852`).
- Verified rows add `actual_action`, `actual_index`, `is_correct`, `verified_at`,
  `context`, and `outcome_metadata` (`copilot_sdk/graph/sqlite_store.py:2872`).

### Timestamp Normalization

Implement helper:

```python
normalize_timestamp(decision: dict[str, Any]) -> datetime | None
```

Candidate fields, in priority order:

1. `created_at`
2. `timestamp`
3. `decision_time`
4. `verified_at`
5. `metadata.created_at`
6. `metadata.timestamp`

Accepted formats:

- epoch seconds as int/float
- ISO 8601 string, including trailing `Z`
- timezone-naive datetimes interpreted as UTC
- timezone-aware datetimes converted to UTC

Missing or invalid timestamps return `None`. Time-window patterns should report
`metadata["missing_timestamp_count"]` and avoid treating missing timestamps as
inside the window.

### Correctness Normalization

Implement helper:

```python
normalize_correctness(decision: dict[str, Any]) -> bool | None
```

Priority:

1. explicit boolean-like `is_correct`
2. explicit boolean-like `correct`
3. `outcome` in `confirmed` / `correct` / `success` => `True`
4. `outcome` in `override` / `incorrect` / `failure` => `False`
5. if `actual_action` and `recommended_action` both exist, compare equality
6. otherwise `None`

Accuracy patterns should compute denominators only from rows with non-`None`
correctness and report `metadata["unknown_correctness_count"]`.

### Entity / Category Normalization

Implement helpers:

```python
entity_key(decision) -> str
category_key(decision) -> str
source_key(decision) -> str
```

Entity candidates:

- `supplier_id`
- `supplier`
- `source_id`
- first `source_ids[]`
- `source`
- `system`
- `entity_id`
- metadata equivalents

Category candidates:

- `category`
- `metadata.category`

Missing entity/category should become `"unknown"` and be counted in metadata.

### Missing-Field Behavior

All patterns must return safe, helpful responses:

- empty decision list: no exception, answer says no decision evidence is available.
- missing timestamps: time-window answer says how many rows were excluded.
- missing correctness: accuracy answer says accuracy cannot be computed for
  rows without verified/correctness fields.
- missing entities: multi-entity/comparison answer groups them under unknown.

## Query Pattern Design

Create:

```text
copilot_sdk/di/query_patterns.py
```

### QueryResult Type

Recommended dataclass:

```python
@dataclass(frozen=True)
class QueryResult:
    intent: str
    answer: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    query_template: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ...
```

`to_dict()` must always include `intent`, `answer`, and `evidence`. It should
include `query_template`, `result`, and `metadata` when non-empty.

This does not conflict with existing DI models; DI currently exports
`NLQueryRouter`, `ProfileConfig`, `SourceProfile`, and `BaseSourceProfiler` only
(`copilot_sdk/di/__init__.py:3`, `copilot_sdk/di/__init__.py:7`).

### QueryPattern Base / Protocol

Recommended protocol:

```python
class QueryPattern(Protocol):
    intent: str
    priority: int

    def matches(self, question: str) -> bool: ...
    def execute(self, question: str, decisions: list[dict[str, Any]]) -> QueryResult: ...
```

Patterns should be deterministic, side-effect free, and operate only on decision
dictionaries.

### MultiEntityPattern

Intent: `multi_entity`

Priority: 40

Matching keywords:

- `by supplier`
- `by source`
- `by system`
- `by entity`
- `which suppliers`
- `which sources`
- `per supplier`
- `per source`

Supported examples:

- "Which suppliers have the most decisions?"
- "Show decision volume by source."
- "Which systems are most affected?"

Unsupported examples:

- "Why did this exact decision happen?" (not entity aggregation)
- "Show raw supplier graph traversal" (not graph traversal)

Execution:

- Select entity dimension by keyword: supplier/source/system/entity.
- Group decisions by normalized entity key.
- Count decisions per group.
- Return top groups sorted by count desc, then key asc.
- Evidence: up to 5 representative decision payloads from largest groups.
- Metadata: `group_by`, `total_decisions`, `unknown_entity_count`.

Empty data:

- Answer: "No decision evidence is available to group by entity."
- Result: `{"groups": []}`

### TimeWindowPattern

Intent: `time_window`

Priority: 35

Matching keywords:

- `last 7 days`, `last 30 days`, `last 90 days`
- `this week`, `this month`
- `since`
- `between`
- `recent`
- `over time`

Supported examples:

- "How many decisions happened in the last 30 days?"
- "Show recent stale-source decisions."
- "Compare decisions this week."

Unsupported examples:

- Open-ended historical claims without a recognizable window.

Execution:

- Parse simple windows deterministically:
  - `last N day(s)`
  - `last N week(s)`
  - `last N month(s)` as 30-day months
  - `this week`
  - `this month`
- Filter rows with normalized timestamps inside the window.
- Aggregate count by day or category depending on keywords.
- Metadata: `window`, `start`, `end`, `missing_timestamp_count`.

Empty data:

- Answer names the window and says no timestamped evidence matched.

### AggregationPattern

Intent: `aggregation`

Priority: 30

Matching keywords:

- `count`
- `how many`
- `average`
- `avg`
- `sum`
- `total`
- `top`
- `most`
- `least`

Supported examples:

- "How many decisions by category?"
- "Average confidence by source."
- "Top categories by decision count."

Unsupported examples:

- Statistical tests, raw SQL, or arbitrary expressions.

Execution:

- Determine measure:
  - count decisions
  - average confidence
  - total/sum numeric factor if explicitly named and present
- Determine group:
  - category
  - action
  - source/entity
  - none
- Result includes aggregate rows.
- Evidence includes sample decisions contributing to the result.
- Metadata: `aggregation`, `group_by`, `measure`, `rows_considered`.

Empty data:

- Answer says no decision evidence is available to aggregate.

### ComparisonPattern

Intent: `comparison`

Priority: 25

Matching keywords:

- `compare`
- `versus`
- `vs`
- `difference between`
- `higher than`
- `lower than`
- `better than`

Supported examples:

- "Compare accuracy for supplier A vs supplier B."
- "Compare decision counts between ERP and CRM."
- "Which category has higher confidence?"

Unsupported examples:

- Comparisons that name no dimensions and no values.

Execution:

- Parse simple `A vs B` / `A versus B` terms.
- Match values against normalized entity/category/source/action fields.
- Compare counts, average confidence, or accuracy depending on keywords.
- Metadata: `left`, `right`, `metric`, `left_count`, `right_count`.

Empty data:

- Return safe message naming missing side(s).

### AccuracyPattern

Intent: `accuracy`

Priority: 45

Matching keywords:

- `accuracy`
- `correct`
- `incorrect`
- `error rate`
- `mistake`
- `override rate`
- `confirmed`

Supported examples:

- "What is accuracy by source?"
- "Which supplier has the highest error rate?"
- "Show correct vs incorrect decisions by category."

Unsupported examples:

- Accuracy claims for unverified decisions without correctness fields.

Execution:

- Use `normalize_correctness()`.
- Only rows with non-`None` correctness contribute to denominator.
- Group by category/source/entity if requested.
- Compute:
  - `accuracy = correct / known`
  - `error_rate = incorrect / known`
- Metadata: `known_correctness_count`, `unknown_correctness_count`, `group_by`.

Empty/missing correctness:

- Return answer: "No verified/correctness evidence is available to compute accuracy."
- Result rows empty or known count zero.

## Router Integration

### Registration

Modify `copilot_sdk/di/nl_query.py` to import default patterns from
`copilot_sdk.di.query_patterns`.

Recommended:

```python
class NLQueryRouter:
    def __init__(self, patterns: Sequence[QueryPattern] | None = None) -> None:
        self._patterns = sorted(patterns or default_patterns(), key=lambda p: p.priority, reverse=True)
```

No explicit constructor today means this remains backward compatible.

### Dispatch Order

Preserve existing intents:

1. Normalize empty question exactly as today.
2. Run existing `_classify_intent()`.
3. If existing intent is not `unknown`, execute existing behavior.
4. Otherwise read decisions once and try extended patterns by priority.
5. If no pattern matches, return existing unknown response.

This avoids shadowing current keyword behavior.

### Decision Reading

Keep current `_decisions(graph_store)` behavior as the base:

- Try `get_verified_decisions("dataops")`.
- Fall back to `get_all_decisions("dataops")`.
- Try no-arg form on `TypeError`.
- Ignore exceptions and continue safely.

Evidence: current reader already does this (`copilot_sdk/di/nl_query.py:55`).

Enhancement inside `nl_query.py` only:

- If `graph_store` is itself a list/tuple of dicts, treat it as direct decisions.
- If `graph_store` is `None`, return an empty list.

This gives tests and callers a safe way to query Python decision lists without
GraphStore changes.

### Domain-Specific Patterns Later

Future apps can instantiate `NLQueryRouter(patterns=[...])` with domain-specific
patterns, but P42 should ship only domain-neutral Data Intelligence patterns.

### No External API / No LLM Guarantee

All matching must use deterministic string matching and regular expressions.
No network calls, external API clients, model calls, or raw database queries.

## File Plan

Allowed implementation files:

- `copilot_sdk/copilot_sdk/di/nl_query.py`
- `copilot_sdk/copilot_sdk/di/query_patterns.py`
- `copilot_sdk/copilot_sdk/di/__init__.py`
- `copilot-sdk/tests/test_nl_query_extended.py`

Forbidden:

- `copilot_sdk/copilot_sdk/graph/*`
- `copilot_sdk/copilot_sdk/scoring/*`
- `tests/test_di_profiler.py`
- package files

## Test Plan

Create `tests/test_nl_query_extended.py`.

### Existing Intent Preservation

- `test_existing_source_reliability_intent_preserved`
- `test_existing_freshness_intent_preserved`
- `test_existing_recurrence_intent_preserved`
- `test_existing_impact_intent_preserved`
- `test_existing_metric_intent_preserved`
- `test_empty_question_fallback_preserved`
- `test_unknown_query_fallback_preserved`

These should assert current `intent`, `answer`, `evidence`, and `query_template`
behavior remains compatible.

### Pattern Unit Tests

Multi-entity:

- groups by supplier/source/system/entity.
- unknown entity grouped safely.
- empty data returns helpful answer.

Time-window:

- filters `last 30 days`.
- handles ISO timestamps and epoch timestamps.
- excludes missing/invalid timestamps and reports count.
- empty window returns safe answer.

Aggregation:

- counts by category.
- averages confidence by source.
- top categories sorted deterministically.
- no data returns safe result.

Comparison:

- compares `A vs B` by count.
- compares accuracy when correctness exists.
- missing side returns helpful answer.

Accuracy:

- computes accuracy and error rate from `is_correct`.
- uses `actual_action == recommended_action` fallback.
- excludes unknown correctness from denominator.
- no correctness returns safe unavailable message.

### Router Dispatch Tests

- `test_extended_patterns_run_only_after_existing_unknown`
- `test_pattern_priority_accuracy_before_aggregation`
- `test_decision_list_input_without_graphstore`
- `test_graphstore_decision_reader_unchanged`
- `test_pattern_metadata_present`

### No-GraphStore-Change Assurance

- Use fake stores implementing only existing methods.
- Assert no calls to raw DB or new GraphStore methods.
- Include a fake store that raises for unknown attributes.

## Validation Plan

Run from `copilot-sdk`:

```powershell
python -m pytest tests/test_nl_query_extended.py -q --timeout=120
python -m pytest tests/ -k "nl_query or di" -q --timeout=120
python -m pytest tests/test_di_profiler.py -q --timeout=120
python -m pytest tests/ -q --timeout=120
```

Baseline already run during discovery:

```powershell
python -m pytest tests/ -k "nl_query or di" -q --timeout=120
```

Result:

- `179 passed, 6 skipped, 1188 deselected`

Full SDK baseline was not run during this discovery pass; run it after the P42
implementation because the targeted DI/NL baseline was already green and the
task requested only discovery plus a plan document.

## Risks / No-Go Conditions

No-go if implementation cannot preserve:

- `NLQueryRouter()` construction with no args.
- `query(question, graph_store)` positional call shape.
- Existing five intents and unknown/empty fallback.
- Existing return fields: `intent`, `answer`, `evidence`, and known-intent
  `query_template`.

No-go if tests reveal:

- Extended patterns shadow existing high-priority intents.
- Current router cannot accept a fake GraphStore or decision list safely.
- `QueryResult` conflicts with existing exported DI types.
- P30 profiler exports regress.
- Implementation requires GraphStore protocol/scorer/package changes.

## Recommended Next Prompt Summary

Implement P42 with:

- `copilot_sdk/di/query_patterns.py` for `QueryResult`, helper normalizers, and
  five deterministic pattern classes.
- Additive `NLQueryRouter` constructor accepting optional patterns.
- Existing intent preservation before extended pattern dispatch.
- Optional direct decision-list support inside `nl_query.py`.
- Tests in `tests/test_nl_query_extended.py`.
- No graph/scorer/package changes.
