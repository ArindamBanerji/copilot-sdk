# SOC Campaign v6.0 - Context Injection

**Version:** 1.10
**Date:** June 17, 2026
**Status:** Approved - split implementation prompts after design review
**Depends on:** Phase 3B (CLOSED/PASS_WITH_P3, M8=1.85ms)
**Evidence:** v6.0 discovery scan + v1.9 design review

---

## §0 - Campaign Arc

v6.0 makes the campaign system visible. Earlier phases closed identity,
race safety, async materialization, and read-path latency:

```
Phase 1   -> stable identity (SHA-256, O(N))
1b-1      -> test authority reconciliation
1b-2      -> seed materialization + race safety
Phase 3   -> async materialization off the analyze hot path
Phase 3B  -> process-local materialized campaign cache/index
v6.0      -> analyst-visible campaign context + holdout clock
```

Phase 3B closeout established the performance room v6.0 must preserve:

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

v6.0 uses the Phase 3B process-local cache to expose campaign context
without adding AGE reads to the hot path. It also starts the 90-day
holdout clock by persisting `is_campaign_alert` and
`campaign_context_shown` on Decision nodes.

---

## §1 - Product Intent

### 1.1 What the Analyst Should See

The current SOC response gives a recommendation for an alert. It does
not provide a buyer-visible, structured campaign context even though
campaign nodes and MEMBER_OF edges exist.

v6.0 adds a visible advisory payload:

```json
{
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

### 1.2 Advisory-Only Boundary

v6.0 is read-only context injection:

- no scorer/ProfileScorer change;
- no tensor expansion;
- no conservation/DK mutation;
- no frontend change;
- no GraphStore protocol/store change;
- no CONTINUES;
- no BELONGS_TO;
- no new AGE reads on the campaign hot path;
- no `check_alert()` return-type change.

The recommendation remains campaign-unaware. The context tells the
analyst there is a pattern; it does not change the model decision.

### 1.3 Commercial Narrative

| Without v6.0 | With v6.0 |
|---|---|
| Campaign detection exists but is mostly invisible | Campaign context visible to the analyst |
| Analyst treats each alert independently | Analyst sees "this is day 3 of a 5-member campaign" |
| No campaign escalation judgment | Advisory: "consider escalating the campaign, not just this alert" |
| SIEM-correlation parity | Differentiation: campaign context from verified operational decisions |

The holdout clock is the commercial asset for v7.0. It measures whether
analysts escalate differently when campaign context is visible.

---

## §2 - Discovery-Corrected Architecture

### 2.1 check_alert Pending Behavior

`CampaignMatcher.check_alert(alert_id) -> Optional[str]` already returns
a `campaign_id` string for:

- materialized cache hits;
- pending provisional seed hits;
- AGE materialized fallback hits;
- inline materialization.

It returns `None` only for true background miss/no event/failure.
Pending unmaterialized seeds return a provisional id through
`_check_pending_seed`.

Design rule: do not change the `check_alert()` return type or make
pending behavior more expansive. v6.0 may classify a non-null
`check_alert()` result as `is_campaign_alert=true`, but it must not add a
new display-only resolver that causes extra Decision `campaign_id`
persistence. If richer pending display is needed later, add it to
`CampaignMatcher`, where event/window seed derivation exists.

### 2.2 Seed-Key Ownership

Seed identity is module-level:

```python
make_campaign_seed_key(rule_type, derived_entity_key, category, time_bucket)
campaign_seed_candidate(event, window_seconds, rule_type="shared_entity")
```

`CampaignAsyncState` cannot compute a seed key from `alert_id` alone.
`CampaignMatcher` owns the event/window context via
`_shared_entity_seed(event)`. Triage must not duplicate this derivation.

### 2.3 Async State Reference

`triage.py` constructs `_camp_matcher = CampaignMatcher(...)` and then
calls `_campaign_id = await _camp_matcher.check_alert(alert_id)`.

Use `_camp_matcher.async_state` for campaign context payload construction.
Do not import `_DEFAULT_CAMPAIGN_ASYNC_STATE` into triage unless the
matcher reference is unavailable.

### 2.4 Response Shape

The live `analyze_alert` response serializes:

```python
"situation_analysis": situation_analysis.model_dump()
```

`SituationAnalysis` has no `nodes`, `evidence_chain`, or `metadata`
field. SDK `SituationContext` and `TraversalNode` exist in
`soc_situation_pattern.py` / `copilot_sdk.situation`, but they are not
the live serialized `situation_analysis` object.

v6.0 implementation must choose the concrete path:

1. preferred: add a top-level serializable `campaign_context` payload to
   the existing `analyze_alert` response dict; or
2. intentionally introduce and serialize a compatible context object.

The implementation prompt below chooses option 1. Do not append directly
to `situation_analysis.situation_context`; that path does not exist.

### 2.5 Decision-Node Persistence

The Decision node is created in `triage.py` with inline AGE Cypher. The
campaign id is added afterward by direct `MATCH ... SET`.

v6.0 must persist these properties on every analyzed Decision node:

```cypher
d.is_campaign_alert = true|false
d.campaign_context_shown = true|false
```

Rows:

| Case | is_campaign_alert | campaign_context_shown |
|---|---:|---:|
| isolated alert | false | false |
| campaign alert, treatment | true | true |
| campaign alert, control | true | false |

Response metadata alone is insufficient. Tests must inspect the captured
Decision-node write query.

### 2.6 Cache Context Source

Current `CampaignAsyncState` caches ids only:

```python
pending_seed_campaigns: dict[str, str]
materialized_campaigns: dict[str, str]
```

v6.0 extends this with positive campaign context metadata. The source
label for visible campaign context is always `graph_store_cached`, not
`graph_store`.

No AGE campaign-property query is allowed in the v6.0 hot path.

### 2.7 Rich Context Capture Point

The richest context exists inside `CampaignMatcher._materialize_alert()`
while the `Campaign` object is in scope. That object has:

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
initial member count. Do not double-count initial members. There is no
current post-materialization join increment path in `check_alert()`.

---

## §3 - Implementation Packages

v1.9 was one package. v1.10 splits the work to reduce blast radius.

### Package A - Cache Context + Holdout Utility

Allowed files:

- `backend/app/domains/soc/campaigns.py`
- `backend/app/domains/soc/campaign_holdout.py`
- `backend/tests/test_campaign_v6_context.py`
- `backend/tests/test_campaign_holdout.py`
- `backend/tests/test_campaign_phase3_async.py` only if needed for cache-state assertions

Goals:

- add `CampaignContext`;
- extend `CampaignAsyncState` with positive campaign context cache;
- populate cache where rich `Campaign` data is available;
- keep `mark_materialized(campaign_id)` compatibility;
- add deterministic `banner_suppressed(alert_id, holdout_pct=15)`;
- add payload-builder unit tests that do not require triage wiring.

Non-goals:

- no triage wiring;
- no Decision-node writes;
- no scorer/frontend/GraphStore changes.

### Package B - Triage Response + Decision Flags

Allowed files:

- `backend/app/routers/triage.py`
- `backend/tests/test_rl_triage_integration.py`
- `backend/tests/test_campaign_v6_context.py` if needed for response payload tests

Goals:

- use `_camp_matcher.async_state`;
- build top-level `campaign_context` payload after Step 5b;
- attach payload to the actual response dict;
- persist `is_campaign_alert` and `campaign_context_shown` unconditionally
  at the Decision `MATCH ... SET` site;
- preserve existing `campaign_id` write semantics;
- verify captured query strings include holdout flags.

Non-goals:

- no cache implementation changes beyond consuming Package A APIs;
- no response wrapper refactor unless the blocker guard triggers.

### Package C - Manual / Live Validation

No code changes. Re-run M8/M9/M10-style validation and verify Decision
properties on live data.

---

## §4 - Package A Design

### 4.1 CampaignContext

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
```

`CampaignAsyncState` gains:

```python
campaign_contexts: dict[str, CampaignContext]
mark_materialized_with_context(campaign: Campaign | CampaignContext | dict) -> None
get_campaign_context(campaign_id: str | None) -> CampaignContext | None
```

`mark_materialized_with_context()` must also update
`materialized_campaigns[campaign_id]`.

### 4.2 Payload Builder

Package A should provide a serializable builder, either in `campaigns.py`
or a small campaign-domain helper:

```python
def build_campaign_context_payload(
    *,
    campaign_id: str | None,
    async_state: CampaignAsyncState | None,
    alert_id: str,
    show_context: bool,
) -> dict[str, Any]:
    ...
```

Builder contract:

- no AGE reads;
- no scorer calls;
- no triage imports;
- returns `is_campaign_alert` and `campaign_context_shown`;
- uses `source="graph_store_cached"`;
- returns `campaign=None` and `advisory=None` for isolated or suppressed
  visible-context cases as appropriate;
- cold cache degrades to campaign_id-only payload;
- member_count `< 3` or missing uses "emerging pattern" language;
- member_count `>= 3` uses "active campaign" advisory language.

### 4.3 Holdout Helper

```python
def banner_suppressed(alert_id: str, holdout_pct: int = 15) -> bool:
    ...
```

Use a stable hash. Do not use randomness or time.

---

## §5 - Package B Design

### 5.1 Triage Order

Keep existing order:

1. Step 3 builds `situation_analysis`.
2. Step 5 creates the Decision node.
3. Step 5b creates `_camp_matcher` and calls `check_alert`.
4. Step 5c builds top-level `campaign_context` from `_campaign_id` and
   `_camp_matcher.async_state`.
5. Step 5d persists Decision flags.
6. Final response includes `"campaign_context": campaign_context_payload`.

### 5.2 Decision Persistence

Use the same direct Cypher style as the existing campaign id write.
Persist flags even when `_campaign_id` is `None`.

Do not rely on only the initial Decision CREATE unless campaign check is
moved earlier. The safer path is a post-campaign unconditional
`MATCH (d:Decision {decision_id: ...}) SET ...` update.

Preserve existing `d.campaign_id` behavior. If `_campaign_id` is non-null
today, it is already written; v6.0 does not expand that behavior.

### 5.3 Pending Semantics

Because pending provisional hits already return a campaign id, v6.0 can
show a provisional/cold-cache campaign payload from that id. If no
cached context exists, set `status` to `"provisional"` or `"unknown"` in
the payload rather than claiming materialized membership.

Do not add a new triage-side pending resolver that writes additional
campaign ids to Decision nodes.

---

## §6 - Test Gates

### Package A Tests

Required:

- `CampaignContext` cache stores campaign_id, category, first_seen,
  member_count, trigger_rule/rule_type, derived_entity_key, and time_bucket.
- background/materialization success populates context cache from rich
  `Campaign` data.
- cold-cache payload degrades to campaign_id-only.
- payload source is `graph_store_cached`.
- no AGE campaign-property read occurs.
- holdout helper is deterministic.
- holdout helper approximates 15% over a broad sample.
- `holdout_pct=0` never suppresses.
- `holdout_pct=100` always suppresses.
- `check_alert()` return type remains `Optional[str]`.
- existing Phase 3B cache/lifecycle tests still pass.

### Package B Tests

Required:

- actual live serialized response dict includes top-level
  `campaign_context` for campaign alerts.
- isolated alert response includes safe false/false flags and no visible
  campaign/advisory.
- treatment campaign alert returns true/true and visible advisory.
- suppressed campaign alert returns true/false and no visible advisory.
- Decision-node write query persists `is_campaign_alert`.
- Decision-node write query persists `campaign_context_shown`.
- captured query uses the same Decision `MATCH ... SET` style as
  existing campaign metadata.
- `_camp_matcher.async_state` or equivalent matcher-owned shared state is
  used; no second isolated singleton is imported into triage.
- no scorer/tensor/DK/conservation code is touched.

### Live Validation

After review:

- M8 p95 remains <= 5ms.
- CONTINUES count remains 0.
- BELONGS_TO count remains 0.
- Decision nodes show both holdout flags.

---

## §7 - Implementation Prompt A

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: SOC Campaign v6.0 Package A - campaign context cache + holdout utility.
TASK TYPE: Narrow backend domain implementation + tests.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50

DESIGN AUTHORITY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\soc_campaign_v6_context_injection_v1_10.md

NO GIT. Do not modify triage.py. Do not modify scorer, frontend,
GraphStore, conservation, DK, package/config, CONTINUES, or BELONGS_TO.

ALLOWED FILES:
- backend/app/domains/soc/campaigns.py
- backend/app/domains/soc/campaign_holdout.py
- backend/tests/test_campaign_v6_context.py
- backend/tests/test_campaign_holdout.py
- backend/tests/test_campaign_phase3_async.py only if needed

IMPLEMENT:
1. Add CampaignContext and positive campaign context cache to CampaignAsyncState.
2. Populate context cache where _materialize_alert has the rich Campaign object.
3. Keep mark_materialized(campaign_id) backward compatible.
4. Add build_campaign_context_payload with no AGE reads.
5. Add deterministic banner_suppressed.
6. Preserve check_alert() -> Optional[str].

TEST:
- cache context fields;
- cold-cache campaign_id-only payload;
- advisory scaling;
- holdout deterministic/rate/0/100;
- no AGE campaign-property read;
- Phase 3B async/cache tests still pass.

VALIDATION COMMANDS:
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
cd backend
python -m pytest tests/test_campaign_v6_context.py tests/test_campaign_holdout.py -v --timeout=60
python -m pytest tests/test_campaign_phase3_async.py tests/test_campaign_seed_materialization.py -q --timeout=120

FINAL OUTPUT:
READY:
FILES_MODIFIED:
FILES_CREATED:
CACHE_CONTEXT:
PAYLOAD_BUILDER:
HOLDOUT_HELPER:
HOT_PATH_AGE_READS:
CHECK_ALERT_RETURN_TYPE:
VALIDATION_RUN:
RESULTS:
SCOPE_CONTROL:
NEXT_STEP:
```

---

## §8 - Implementation Prompt B

```
/model gpt-5.3
Echo the current model name in the first line of output.

TASK: SOC Campaign v6.0 Package B - triage response payload + Decision holdout flags.
TASK TYPE: Narrow backend router wiring + tests.

WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50

DESIGN AUTHORITY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\docs\design\soc_campaign_v6_context_injection_v1_10.md

PREREQUISITE:
Package A reviewed and passed.

NO GIT. Do not modify scorer, frontend, GraphStore, conservation, DK,
package/config, CONTINUES, or BELONGS_TO.

ALLOWED FILES:
- backend/app/routers/triage.py
- backend/tests/test_rl_triage_integration.py
- backend/tests/test_campaign_v6_context.py only if needed

IMPLEMENT:
1. After Step 5b, build top-level campaign_context using _campaign_id
   and _camp_matcher.async_state.
2. Attach campaign_context to the actual response dict.
3. Persist is_campaign_alert and campaign_context_shown unconditionally
   to the Decision node at the same post-campaign MATCH/SET mechanism as
   campaign_id.
4. Preserve existing campaign_id write semantics.
5. Do not add AGE campaign-property reads.

BLOCKER GUARD:
If Codex cannot attach campaign_context to the live response dict without
changing the scorer or adding AGE reads, STOP and report:
BLOCKED_RESPONSE_SHAPE_DECISION_REQUIRED

TEST:
- response includes campaign_context for treatment campaign alert;
- suppressed campaign alert has flags but no visible campaign/advisory;
- isolated alert false/false with no visible advisory;
- Decision SET query persists is_campaign_alert and campaign_context_shown;
- _camp_matcher.async_state is used or equivalent matcher-owned state;
- no scorer/tensor/DK/conservation changes.

VALIDATION COMMANDS:
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
cd backend
python -m pytest tests/test_rl_triage_integration.py tests/test_campaign_v6_context.py -q --timeout=120
python -m pytest tests/test_campaign_api.py tests/test_campaign_engine.py tests/test_campaign_frontend.py tests/test_campaign_matcher.py tests/test_campaign_schema.py tests/test_campaign_seed_materialization.py tests/test_campaign_phase3_async.py tests/test_campaign_v6_context.py tests/test_campaign_holdout.py -q --timeout=180
python -m pytest tests/ -q --timeout=300

FINAL OUTPUT:
READY:
FILES_MODIFIED:
FILES_CREATED:
RESPONSE_PAYLOAD:
DECISION_NODE_HOLDOUT:
TRIAGE_ASYNC_STATE:
PENDING_SEMANTICS:
HOT_PATH_AGE_READS:
VALIDATION_RUN:
RESULTS:
FULL_BACKEND_RESULT:
SCOPE_CONTROL:
NEXT_STEP:
```

---

## §9 - Manual / Live Validation

After Package A and B pass review, manually validate:

```powershell
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python .\demo.py --soc --diag-mode --diag-graph-name soc_graph --diag-backend-port 8001 --age-use-pool
```

Validate:

1. campaign alert response contains top-level `campaign_context`;
2. campaign context source is `graph_store_cached`;
3. isolated alert has false/false flags and no visible advisory;
4. suppressed campaign alert has true/false flags and no visible advisory;
5. Decision node carries `is_campaign_alert` and `campaign_context_shown`;
6. M8 remains <= 5ms p95;
7. CONTINUES remains 0;
8. BELONGS_TO remains 0.

---

## §10 - v7.0 Gate

v6.0 plus holdout is the measurement asset. v7.0 tensor expansion is not
automatic.

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

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.8 | June 17, 2026 | Execution sequencing added: discovery prompt plus implementation prompt split. |
| v1.9 | June 17, 2026 | Discovery-based corrections for check_alert pending behavior, seed-key ownership, async-state reference, SituationAnalysis response mismatch, Decision-node holdout persistence, cache id-only limitation, and rich materialization context source. |
| v1.10 | June 17, 2026 | Design review patch. Kept v1.9's SituationAnalysis correction, but made the executable strategy explicit: top-level `campaign_context` payload is the preferred response shape. Clarified pending semantics so v6.0 does not add new display-only campaign_id persistence beyond existing check_alert behavior. Split implementation into Package A (cache context + holdout utility), Package B (triage response + Decision flags), and Package C (live validation). Replaced vague validation language with exact pytest commands. Preserved zero AGE reads, no scorer/tensor/DK/conservation scope, no CONTINUES/BELONGS_TO, and added blocker guard for unsafe response-shape wiring. |
