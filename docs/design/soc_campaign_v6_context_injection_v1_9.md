# SOC Campaign v6.0 - Context Injection

**Version:** 1.9
**Date:** June 17, 2026
**Status:** Approved - implementation prompt after discovery patch / ready for design review
**Depends on:** Phase 3B (CLOSED/PASS_WITH_P3, M8=1.85ms)
**Evidence:** v6.0 read-only discovery scan (8 anchors, June 17)

---

## §0 - Campaign Arc

v6.0 is the culmination of the campaign performance arc. Each phase
solved one problem and unlocked the next:

```
Phase 1   -> stable identity (SHA-256, O(N))
1b-1      -> test authority reconciliation
1b-2      -> seed materialization + race safety
Phase 3   -> async materialization off the analyze hot path
Phase 3B  -> process-local materialized campaign cache/index
v6.0      -> analyst-visible campaign context + holdout clock
```

Phase 3B made campaign lookup fast enough for the hot path:

| Metric | Value |
|---|---|
| Campaign nodes | 259 |
| MEMBER_OF edges | 520 |
| CampaignSeed nodes | 104 distinct |
| CONTINUES edges | 0 |
| BELONGS_TO edges | 0 |
| M8 p95 hot path | 1.85ms |
| Backend tests | 1982 passed, 14 skipped |
| Campaign tests | 106 passed |
| Phase 3 async tests | 30 passed |

v6.0 uses that cache to make campaign context visible to the analyst
without adding AGE reads to the hot path. It also starts the holdout
clock for v7.0 by persisting `is_campaign_alert` and
`campaign_context_shown` on the Decision node.

---

## §1 - What v6.0 Does

### 1.1 Product Gap

Today the SOC analyst sees a score and recommendation for each alert,
but does not reliably see whether the alert is part of a larger
campaign. The campaign infrastructure exists, and `campaign_id` may be
written to the Decision node, but the live response does not provide a
buyer-visible campaign context payload.

The analyst sees:

```
Alert: Suspicious credential access from admin-jsmith
Recommendation: escalate_tier2 (confidence 0.82)
Factors: privileged_identity (0.9), asset_criticality (0.7), ...
```

What v6.0 should add:

```
Campaign Context:
  Active Campaign: L1-...
  5 members · 3 days active · credential_access
  This alert is part of an active multi-member campaign.
  Consider escalating the campaign, not just this alert.
```

### 1.2 Scope

v6.0 is read-only context injection. It does not change the scorer, add
campaign factors to the tensor, modify conservation or DK, create
CONTINUES/BELONGS_TO edges, or rewrite Campaign Phase 1/2/3 logic.

The recommendation remains campaign-unaware. The campaign context tells
the analyst that there is a pattern; the analyst still decides what to
do with it.

### 1.3 Commercial Narrative

| Without v6.0 | With v6.0 |
|---|---|
| Campaign detection exists but is mostly invisible | Campaign context visible to the analyst |
| Analyst treats each alert independently | Analyst sees "this is day 3 of a 5-member campaign" |
| No campaign escalation judgment | Advisory: "consider escalating the campaign, not just this alert" |
| SIEM-correlation parity | Differentiation: campaign context from verified operational decisions |

v6.0 also starts the override-rate clock for v7.0. The 90-day
measurement can only begin once campaign context is visible and the
treatment/control flags are queryable on persisted Decision nodes.

---

## §2 - Discovery Findings

The v1.9 discovery pass corrected several assumptions in v1.8.

### 2.1 Current Campaign Hot Path

`CampaignMatcher.check_alert(alert_id) -> Optional[str]` already returns
a `campaign_id` string for:

- materialized in-memory cache hits,
- pending provisional seed hits,
- AGE materialized fallback hits,
- inline materialization.

It returns `None` only for a true background miss, missing event, or
failure. Pending unmaterialized seeds currently return a provisional
campaign id through `_check_pending_seed`.

Important consequence: v6.0 must not change the `check_alert` return
type or assume that pending seeds return `None`. A separate pending
resolver is not needed just to retrieve a pending campaign id.

### 2.2 Seed-Key Derivation

Seed identity is module-level:

```python
make_campaign_seed_key(rule_type, derived_entity_key, category, time_bucket)
campaign_seed_candidate(event, window_seconds, rule_type="shared_entity")
```

`CampaignAsyncState` cannot compute a seed key from an `alert_id` alone.
`CampaignMatcher` has the event and window context through
`_shared_entity_seed(event)`. If v6.0 adds a display-only pending
resolver, it belongs on `CampaignMatcher` or must receive a precomputed
`seed_key`. Triage must not independently rederive seed keys with a
parallel implementation.

### 2.3 Async State Reference

`triage.py` constructs a request-local `CampaignMatcher`, and that
matcher defaults to process-lifetime shared async state. The matcher is
still in scope after `check_alert()` returns.

Use `_camp_matcher.async_state` in triage wiring. Do not import
`_DEFAULT_CAMPAIGN_ASYNC_STATE` into triage unless there is no safe
matcher reference.

### 2.4 SituationContext Mismatch

The live `analyze_alert` response serializes
`app.services.situation.SituationAnalysis`:

```python
class SituationAnalysis(BaseModel):
    situation_type: str
    situation_confidence: float
    factors_detected: list[str]
    options_evaluated: list[OptionEvaluated]
    selected_option: str
    selection_reasoning: str
    decision_economics: DecisionEconomics
    mitre_technique: str = ""
    mitre_tactic: str = ""
```

`SituationAnalysis` has no `nodes`, `evidence_chain`, or `metadata`
field. The SDK `SituationContext` and `TraversalNode` objects do exist
and are used by `soc_situation_pattern.py`, but they are not currently
the object serialized as `response["situation_analysis"]`.

Therefore v1.8's assumed path
`situation_analysis.situation_context.nodes.append(...)` is wrong for
the current live response. v6.0 must either:

1. add a serializable `campaign_context` / `campaign_advisory` payload to
   the current `SituationAnalysis` response shape, or
2. intentionally introduce a compatible SituationContext-bearing wrapper
   and serialize it explicitly.

Do not claim "append a TraversalNode to `situation_analysis.situation_context`"
unless the implementation intentionally creates that object.

### 2.5 Decision-Node Persistence

The Decision node is created by inline AGE Cypher in `triage.py`. The
campaign id is added later through a separate `MATCH ... SET`:

```python
MATCH (d:Decision {decision_id: ...})
SET d.campaign_id = ...
```

`is_campaign_alert` and `campaign_context_shown` must be added at this
same post-campaign Decision update site, using the same `_S()`
serialization style. Persist them unconditionally for all arms:

| Case | is_campaign_alert | campaign_context_shown |
|---|---:|---:|
| isolated alert | false | false |
| campaign alert, treatment | true | true |
| campaign alert, control | true | false |

Do not rely only on response metadata.

### 2.6 Holdout Testability

Existing triage tests mock `neo4j_client.run_query()` and capture query
strings, so Decision-node persistence can be tested without live AGE.

Recommended tests:

- `test_rl_triage_integration.py`: persisted Decision flags and response
  metadata/payload.
- `test_soc_situation_pattern.py`: serializer/helper behavior if SDK
  `TraversalNode` or `SituationContext` helpers are used.
- `test_campaign_phase3_async.py`: async-state campaign context/cache
  data.

### 2.7 Hot-Path AGE Read Risk

Phase 3B cache-hit path avoids AGE campaign lookup and still fetches the
alert event once. Current cached materialized data is id-only:

```python
CampaignAsyncState.materialized_campaigns: dict[str, str]
CampaignAsyncState.pending_seed_campaigns: dict[str, str]
```

v6.0 must extend `CampaignAsyncState` with positive campaign context
metadata and read that cache only. No new AGE read may be added to the
hot path.

### 2.8 Materialization Context Source

`mark_materialized()` is called on AGE fallback hit and background
materialization success, but it stores only `campaign_id`. The richest
context is available inside `_materialize_alert()` before it returns,
where the `Campaign` object has:

- `campaign_id`
- `category`
- `first_seen`
- `last_seen`
- `alert_count`
- `trigger_rule` / `rule_type`
- `derived_entity_key`
- `time_bucket`
- `member_alert_ids`

Use `campaign.alert_count` or `len(campaign.member_alert_ids)` for the
initial member count. Do not double-count initial members; there is no
clear current post-materialization join increment path in `check_alert`.

---

## §3 - Architecture Choice

### 3.1 Cache Extension

Keep the Phase 3B cache-extension approach:

1. Extend `CampaignAsyncState` to cache positive campaign context
   properties at materialization time.
2. Read enriched cache in v6.0.
3. Add zero new AGE reads on the hot path.
4. Preserve `check_alert() -> Optional[str]`.

### 3.2 Live Response Target

v6.0 must target the actual live response structure. The current
response contains:

```python
"situation_analysis": situation_analysis.model_dump()
```

Since current `SituationAnalysis` has no context node list, v6.0 should
add an explicit serializable payload, for example:

```json
{
  "situation_analysis": { "...existing fields": "..." },
  "campaign_context": {
    "is_campaign_alert": true,
    "campaign_context_shown": true,
    "source": "graph_store_cached",
    "campaign": {
      "campaign_id": "L1-...",
      "category": "credential_access",
      "first_seen": "2026-06-17T...",
      "member_count": 5,
      "status": "materialized"
    },
    "advisory": {
      "type": "campaign_advisory",
      "text": "Active 5-member campaign. Consider escalating the campaign, not just this alert."
    }
  }
}
```

If the implementation chooses to use SDK `TraversalNode` and
`SituationContext` as a normalized internal representation, it must
explicitly serialize that structure into the existing response payload.
It must not assume a hidden `situation_analysis.situation_context`
attribute exists.

### 3.3 Non-Goals

| Constraint | Why |
|---|---|
| No scorer changes | v6.0 is advisory context, not factor input |
| No tensor expansion | v7.0 scope |
| No conservation/DK mutation | Read-only display |
| No new AGE reads on hot path | Cache extension handles context |
| No new AGE writes except Decision flags | Campaign materialization unchanged |
| No check_alert return type change | Triage compatibility |
| No CONTINUES edges | Phase 4 |
| No BELONGS_TO edges | MEMBER_OF remains canonical |

---

## §4 - Implementation Design

### 4.1 Extend CampaignAsyncState

Add a non-frozen cached context object:

```python
@dataclass
class CampaignContext:
    campaign_id: str
    category: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    member_count: int | None = None
    trigger_rule: str | None = None
    rule_type: str | None = None
    derived_entity_key: str | None = None
    time_bucket: int | None = None
    status: str = "materialized"

class CampaignAsyncState:
    campaign_contexts: dict[str, CampaignContext] = field(default_factory=dict)

    def mark_materialized_with_context(self, campaign: Campaign | CampaignContext | dict) -> None:
        ...

    def get_campaign_context(self, campaign_id: str | None) -> CampaignContext | None:
        ...
```

Keep `mark_materialized(campaign_id)` for backward compatibility. The
new method must also update `materialized_campaigns`.

### 4.2 Context Payload Builder

Replace v1.8's assumed `_add_campaign_context(context: SituationContext, ...)`
with a builder that can work against the actual response shape:

```python
def build_campaign_context_payload(
    *,
    campaign_id: str | None,
    async_state: CampaignAsyncState | None,
    alert_id: str,
    show_context: bool,
) -> dict[str, Any]:
    """Return serializable campaign context and holdout flags.

    This function does not assume SituationAnalysis has nodes/evidence_chain/
    metadata. It does not perform AGE reads.
    """
```

Requirements:

- accept the actual response/context object or return a serializable
  payload for triage to attach;
- do not assume `.nodes`, `.evidence_chain`, or `.metadata` fields exist
  on `SituationAnalysis`;
- return/preserve `is_campaign_alert` and `campaign_context_shown` for
  Decision-node persistence;
- use `source="graph_store_cached"`;
- gracefully degrade if full campaign context fields are unavailable;
- add advisory data to the actual response payload;
- perform no AGE reads.

If SDK `TraversalNode` is used internally, convert it with `to_dict()`
before attaching it to the live response.

### 4.3 Triage Wiring

Current order:

1. Step 3 builds `situation_analysis`.
2. Step 5 writes the Decision node.
3. Step 5b creates `_camp_matcher` and calls `_camp_matcher.check_alert(alert_id)`.
4. The campaign id, when non-null, is written by a separate Decision
   `MATCH ... SET`.

v6.0 post-hoc plan:

```python
campaign_flags = {
    "is_campaign_alert": False,
    "campaign_context_shown": False,
}
campaign_context_payload = None

# after _campaign_id = await _camp_matcher.check_alert(alert_id)
campaign_context_payload = build_campaign_context_payload(
    campaign_id=_campaign_id,
    async_state=_camp_matcher.async_state,
    alert_id=alert_id,
    show_context=not banner_suppressed(alert_id) if _campaign_id else False,
)
campaign_flags = {
    "is_campaign_alert": bool(campaign_context_payload.get("is_campaign_alert")),
    "campaign_context_shown": bool(campaign_context_payload.get("campaign_context_shown")),
}
```

Persist flags at the same post-campaign Decision update site as
`campaign_id`. Do this unconditionally so isolated/control rows start the
holdout clock correctly.

Because `check_alert()` already returns pending campaign ids,
`get_pending_campaign_id()` is not required for the basic pending id. If
a display-only resolver remains useful, put it on `CampaignMatcher`, not
`CampaignAsyncState`, unless it receives a precomputed `seed_key`.

### 4.4 Graceful Degradation

| Scenario | Behavior |
|---|---|
| Isolated alert | `is_campaign_alert=false`, `campaign_context_shown=false`, no campaign advisory |
| Campaign id but cache cold | payload includes campaign_id only and a conservative advisory |
| Campaign id with cached context | full campaign properties and scaled advisory |
| Suppressed holdout arm | flags persist `true/false`; no visible campaign advisory |
| Async state unavailable | flags fall back safely; no exception to analyst |

### 4.5 Advisory Scaling

Advisory language must scale with evidence:

- member_count missing or `< 3`: "emerging pattern" language.
- member_count `>= 3`: "active campaign, consider escalating the campaign"
  language.
- never claim verified/confirmed savings or scorer causality.

---

## §5 - Holdout Clock

### 5.1 Why It Ships With v6.0

The v7.0 decision is only meaningful if v6.0 creates a causal
treatment/control dataset. The holdout cannot be reconstructed later.

### 5.2 Required Persistence

Persist these properties on the Decision node for every analyzed alert:

```cypher
d.is_campaign_alert = true|false
d.campaign_context_shown = true|false
```

Rows:

- isolated alert: `false / false`
- campaign alert treatment: `true / true`
- campaign alert control: `true / false`

`check_alert()` may already return pending campaign ids, so a pending
resolver is not always necessary. The holdout persistence must not depend
on response metadata.

### 5.3 Holdout Function

Create a deterministic helper:

```python
banner_suppressed(alert_id: str, holdout_pct: int = 15) -> bool
```

Use a stable hash, not randomness. Test:

- same alert id yields same result;
- `holdout_pct=0` never suppresses;
- `holdout_pct=100` always suppresses;
- about 15% suppression over a broad synthetic sample.

---

## §6 - Test Gates

### 6.1 Campaign Context Response Tests

Tests must verify:

- campaign context appears in the actual live serialized response
  structure, not necessarily `SituationContext.nodes`;
- advisory appears in the actual evidence/advisory response structure,
  not necessarily `evidence_chain` if absent;
- isolated alerts have no visible campaign advisory;
- suppressed campaign alerts persist treatment/control flags but do not
  show the visible advisory;
- `source` is `graph_store_cached`;
- partial/cold-cache context degrades to campaign_id-only payload.

### 6.2 Decision-Node Persistence Tests

Mandatory:

- Decision node SET query includes `is_campaign_alert`;
- Decision node SET query includes `campaign_context_shown`;
- campaign alert treatment persists `true/true`;
- campaign alert control persists `true/false`;
- isolated alert persists `false/false`;
- persistence uses the same direct Cypher mechanism and `_S()` style as
  the existing campaign-id write.

### 6.3 Hot-Path Tests

Mandatory:

- no AGE campaign-property read occurs on the hot path;
- cache-hit path uses `_camp_matcher.async_state` or equivalent shared
  state, not a second isolated async state;
- `check_alert` return type remains `Optional[str]`;
- materialized cache and pending-state behavior from Phase 3B remains
  unchanged.

### 6.4 Suggested Test Files

| File | Purpose |
|---|---|
| `backend/tests/test_campaign_v6_context.py` | payload builder, advisory scaling, cache degradation |
| `backend/tests/test_campaign_holdout.py` | deterministic holdout helper |
| `backend/tests/test_rl_triage_integration.py` | Decision-node flags and response payload wiring |
| `backend/tests/test_soc_situation_pattern.py` | SDK serialization helper if used |
| `backend/tests/test_campaign_phase3_async.py` | async-state cache metadata if extended there |

---

## §7 - Files Changed

Expected implementation files:

| File | Expected change |
|---|---|
| `backend/app/domains/soc/campaigns.py` | extend `CampaignAsyncState` with campaign context metadata |
| `backend/app/domains/soc/campaign_holdout.py` | deterministic holdout helper |
| `backend/app/routers/triage.py` | attach actual response payload and persist Decision flags |
| `backend/app/services/soc_situation_pattern.py` | optional helper/serializer only if aligned with live response |
| `backend/tests/test_campaign_v6_context.py` | new unit tests |
| `backend/tests/test_campaign_holdout.py` | new holdout tests |
| `backend/tests/test_rl_triage_integration.py` | Decision-node persistence tests |

Clarifications:

- `soc_situation_pattern.py` may provide a serializer/helper, but v6
  wiring must match actual `SituationAnalysis` response serialization.
- `triage.py` must add fields to the actual response payload, not to a
  nonexistent `situation_context` path.
- `campaigns.py` cache context extension remains required.
- No scorer, conservation, DK, frontend, GraphStore protocol, CONTINUES,
  or BELONGS_TO changes.

---

## §8 - Prompt 2: Implementation Prompt, Discovery-Patched

Use this prompt only after reading this v1.9 document.

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: SOC Campaign v6.0 - context injection and holdout clock.
TASK TYPE: Narrow backend implementation + tests.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50

DESIGN AUTHORITY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\soc_campaign_v6_context_injection_v1_9.md

READ FIRST:
Read the full design document above. Do not implement from v1.8.

NO GIT:
Do not run git status, git diff, git add, git commit, git checkout,
git reset, or any git command.

STRICT SCOPE:
- Do not change scorer/ProfileScorer.
- Do not change conservation/DK.
- Do not change GraphStore protocol/stores.
- Do not change frontend.
- Do not add CONTINUES.
- Do not add BELONGS_TO.
- Do not add AGE reads to the campaign hot path.
- Do not change check_alert return type.

DISCOVERY-PATCHED ANCHORS:
- pending behavior: check_alert already returns pending provisional
  campaign_id.
- pending resolver owner: CampaignMatcher only if needed; not
  CampaignAsyncState from alert_id alone.
- async state reference in triage: use _camp_matcher.async_state.
- situation context path: none currently; implementation must use actual
  SituationAnalysis serialization or add an explicit campaign_context
  payload.
- decision persistence site: triage post-campaign Decision SET site,
  currently the same site as d.campaign_id.
- mark_materialized replacement site: background success and
  _materialize_alert rich Campaign object area.

IMPLEMENTATION:
1. Extend CampaignAsyncState with positive campaign context metadata.
   Existing materialized_campaigns remains id-only compatibility cache.
   Add CampaignContext and get/mark helpers.

2. Populate context metadata from the richest safe place:
   inside _materialize_alert() while the Campaign object is still in
   scope, or immediately after successful background materialization if
   the Campaign object is returned internally. Preserve public
   check_alert() -> Optional[str].

3. Add deterministic campaign_holdout.py:
   banner_suppressed(alert_id, holdout_pct=15) -> bool.

4. Add a serializable campaign context payload builder. It must:
   - not assume SituationAnalysis has nodes/evidence_chain/metadata;
   - use source="graph_store_cached";
   - return or include is_campaign_alert and campaign_context_shown;
   - gracefully degrade to campaign_id-only;
   - never perform AGE reads;
   - produce buyer-visible advisory text scaled by evidence.

5. Wire triage post-hoc:
   - Step 3 situation_analysis is already built before campaign check.
   - Step 5b computes _campaign_id via _camp_matcher.check_alert(alert_id).
   - Step 5c builds campaign_context payload using _camp_matcher.async_state.
   - Step 5d persists is_campaign_alert and campaign_context_shown to the
     Decision node at the same mechanism/site as campaign_id.
   - Attach the campaign_context payload to the actual live response.

6. Persist holdout flags unconditionally:
   - isolated alert: false / false
   - campaign alert treatment: true / true
   - campaign alert control: true / false
   Do not rely only on response metadata.

BLOCKER GUARD:
If Codex cannot find a safe place to attach campaign context to the live
response object without changing the scorer or adding AGE reads, STOP
and report:
BLOCKED_RESPONSE_SHAPE_DECISION_REQUIRED

TESTS:
Add/update tests proving:
- actual live serialized response includes campaign context for campaign alerts;
- no campaign context/advisory is shown for isolated alerts;
- control arm persists campaign alert but suppresses visible context;
- Decision node persists is_campaign_alert and campaign_context_shown;
- no AGE campaign-property read occurs on the hot path;
- _camp_matcher.async_state or equivalent shared state is used;
- check_alert return type remains Optional[str];
- holdout helper is deterministic and approximately 15%;
- Phase 3B async/cache tests and campaign suite still pass.

VALIDATION:
Run targeted new tests, campaign tests, and full backend once. If full
backend times out, report timeout and targeted results.

FINAL OUTPUT:
READY:
FILES_MODIFIED:
FILES_CREATED:
CAMPAIGN_CONTEXT_PAYLOAD:
SITUATION_ANALYSIS_RESPONSE_PATCH:
TRIAGE_WIRING:
DECISION_NODE_HOLDOUT:
HOT_PATH_AGE_READS:
CHECK_ALERT_RETURN_TYPE:
TESTS_ADDED:
VALIDATION_RUN:
RESULTS:
SCOPE_CONTROL:
REMAINING_RISKS:
NEXT_STEP:
```

---

## §9 - Manual / Live Validation

After implementation and review, manually validate with SOC diagnostic
backend:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python .\demo.py --soc --diag-mode --diag-graph-name soc_graph --diag-backend-port 8001 --age-use-pool
```

Validate:

1. Campaign alert response contains `campaign_context`.
2. Campaign context source is `graph_store_cached`.
3. Isolated alert has no visible campaign advisory.
4. Decision node carries `is_campaign_alert` and
   `campaign_context_shown`.
5. M8 remains <= 5ms p95.
6. CONTINUES remains 0.
7. BELONGS_TO remains 0.

---

## §10 - v7.0: Measurement Is the Asset

v6.0 plus the holdout clock is the narrative win. v7.0 tensor expansion
is a thesis-validation experiment, not a roadmap commitment.

Decision gate after at least 90 days:

```
treatment = campaign alerts where campaign_context_shown == true
control   = campaign alerts where campaign_context_shown == false
lift      = escalation_rate(treatment) - escalation_rate(control)

lift significant and positive
  and treatment escalation accuracy >= control accuracy
    -> v7.0 candidate, not automatic

lift near 0 or treatment accuracy < control accuracy
    -> stay advisory
```

Even with positive lift, v7.0 requires circularity guard, enrichment-loop
math, DK/conservation gates, honest scoring-not-compounding framing, and
a customer asking for auto-escalation.

---

## §11 - Related Documents

| Document | Relationship |
|---|---|
| `soc_campaign_scorer_integration_v1_0.md` | v6.0 = context injection; v7.0 = tensor expansion candidate |
| `campaign_phase3_async_v1_4.md` | v6.0 depends on Phase 3B cache infrastructure |
| `campaign_phase3_gates_v1_0.md` | M8 must remain <= 5ms after v6.0 |
| `product_integrity_execution_strategy_v2_4.md` | advisory-not-scorer framing |
| `soc_campaign_identity_architecture_v1_3.md` | Phase 1 identity is the campaign_id v6.0 displays |

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.8 | June 17, 2026 | Execution sequencing added: discovery prompt plus implementation prompt split. |
| v1.9 | June 17, 2026 | Discovery-based corrections. Updated status. Corrected check_alert pending behavior: pending seeds already return provisional campaign_id. Corrected seed-key ownership: CampaignMatcher has event/window derivation context; CampaignAsyncState cannot compute seed key from alert_id alone. Corrected async-state reference: triage should use `_camp_matcher.async_state`. Corrected SituationContext assumption: live response serializes `SituationAnalysis`, which has no nodes/evidence_chain/metadata; v6 must attach an explicit serializable campaign_context payload or intentionally introduce a compatible serialized context. Corrected Decision-node holdout persistence: `is_campaign_alert` and `campaign_context_shown` must be written unconditionally at the post-campaign Decision SET site. Clarified cache context extension: current cache stores ids only; v6 must extend positive context metadata and add no AGE reads. Corrected mark_materialized context source: richest properties are available in `_materialize_alert()` while the Campaign object is in scope. Rewrote Prompt 2 with exact anchors and blocker guard `BLOCKED_RESPONSE_SHAPE_DECISION_REQUIRED`. |
