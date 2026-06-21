# SOC Campaign v6.0 — Context Injection

**Version:** 1.8
**Date:** June 17, 2026
**Status:** Approved — discovery pass before implementation
**Depends on:** Phase 3B (CLOSED/PASS_WITH_P3, M8=1.85ms)
**Evidence:** v6.0 discovery scan (8 areas, June 17)

---

## §0 — Campaign Arc (Context for Reviewer)

v6.0 is the culmination of the campaign performance arc. Each
phase solved one problem and unlocked the next:

```
Phase 1   → stable identity (SHA-256, O(N))
            151 Campaign nodes, 506 MEMBER_OF edges
            CLOSED

1b-1      → test authority reconciliation
            6 stale tests fixed, 52 passed
            CLOSED

1b-2      → seed materialization + race safety
            Advisory lock + MATCH-then-CREATE
            Zero duplicates, zero CONTINUES/BELONGS_TO
            BUT: 215ms p95 vs 5ms budget (43x over)
            CLOSED_FOR_CORRECTNESS / PERFORMANCE_TRIGGERED

Phase 3   → async materialization (create_task)
            Write moved off hot path
            BUT: read still 6.9ms p95 (over budget)
            CLOSED / PASS_WITH_P3

Phase 3B  → materialized campaign cache/index
            Second AGE read eliminated on cache hits
            M8 p95 = 1.85ms (3.15ms headroom)
            CLOSED / PASS_WITH_P3

v6.0      → THIS DOCUMENT
            Make campaign context VISIBLE to the analyst
            Uses Phase 3B's cache (zero AGE reads)
            + holdout clock for v7.0 measurement
```

**Current graph state (Phase 3B closeout):**

| Metric | Value |
|---|---|
| Campaign nodes | 259 |
| MEMBER_OF edges | 520 |
| CampaignSeed nodes | 104 (distinct) |
| CONTINUES edges | 0 |
| BELONGS_TO edges | 0 |
| M8 p95 (hot path) | 1.85ms |
| Backend tests | 1982 passed, 14 skipped |
| Campaign tests | 106 passed |
| Phase 3 async tests | 30 passed |

**What Codex built (the code v6.0 extends):**

| File | What it does | v6.0 touches? |
|---|---|---|
| `campaigns.py` | CampaignCorrelationEngine, CampaignRepository, CampaignMatcher, CampaignAsyncState | YES — add CampaignContext + cache methods |
| `triage.py` | SOC analyze route (Step 3: situation, Step 5b: campaign check) | YES — add Step 5c post-hoc |
| `soc_situation_pattern.py` | Situation context builder (TraversalNode, SituationContext) | YES — add _add_campaign_context |
| `test_campaign_*.py` | 106 campaign tests + 30 Phase 3 async tests | NO — v6.0 adds new test file |

---

## §1 — What v6.0 Does

### 1.1 The Product Gap

Today the SOC analyst sees a score and recommendation for each
alert, but has NO visibility into whether the alert is part of
a larger campaign. The campaign infrastructure exists (259
Campaign nodes, 520 MEMBER_OF edges) but is invisible to the
analyst — campaign_id is written to the decision node in AGE
and never surfaced.

The analyst sees:

```
Alert: Suspicious credential access from admin-jsmith

Recommendation: escalate_tier2 (confidence 0.82)
Factors: privileged_identity (0.9), asset_criticality (0.7), ...
```

What they DON'T see:

```
Campaign Context:
  ██ Active Campaign: CAMP-2026-06-15-cred-xyz
     5 members · 3 days active · credential_access
     "This alert is part of an active multi-member campaign.
      Consider escalating the campaign, not just this alert."
```

### 1.2 What v6.0 Delivers

v6.0 adds a campaign TraversalNode to the SOC situation context.
The analyst sees campaign membership as advisory context alongside
the scoring recommendation.

**v6.0 is read-only context injection.** It does NOT change the
scorer, does NOT add campaign factors to the tensor, does NOT
modify conservation or DK. The recommendation stays campaign-
unaware. The campaign context tells the analyst "there's a
pattern here — you decide what to do with it."

### 1.3 Why This Matters Commercially

| Without v6.0 | With v6.0 |
|---|---|
| Campaign detection exists but is invisible | Campaign context visible to the analyst |
| Analyst treats each alert independently | Analyst sees "this is day 3 of a 5-member campaign" |
| No campaign escalation judgment | Advisory: "consider escalating the campaign, not just this alert" |
| Competitor parity (SIEM correlation exists everywhere) | Differentiation: campaign context from verified operational decisions |

v6.0 also starts the **override-rate clock** for v7.0. The
90-day measurement ("do analysts escalate more when they see
campaign context?") can only begin once campaign context is
visible. v6.0 is the prerequisite for the strongest commercial
claim: "the system LEARNED that campaigns matter."

---

## §2 — Architecture

### 2.1 Discovery Findings

The scan revealed the current structure:

```
check_alert(alert_id) → Optional[str]   (campaign_id or None)

CampaignAsyncState stores:
  pending_seeds: set[str]                (seed keys)
  pending_seed_campaigns: dict[str, str] (seed_key → campaign_id)
  materialized_campaigns: dict[str, str] (campaign_id → campaign_id)

Campaign nodes in AGE have:
  campaign_id, first_seen, category      (from AGE queries)

Situation context builder:
  backend/app/services/soc_situation_pattern.py
  Uses TraversalNode, SituationContext

triage.py:
  Gets campaign_id string (line 887)
  Writes campaign_id to decision node (line 891)
  Does NOT add campaign context to situation_context
```

**Key finding:** check_alert returns just a campaign_id string.
The CampaignAsyncState cache stores campaign_id strings only —
no size, age, category. AGE Campaign nodes DO have these
properties, but reading them adds ~1-3ms (an AGE query).

### 2.2 The Architecture Choice

**Extend CampaignAsyncState to cache campaign properties at
materialization time. v6.0 reads from the enriched cache.
Zero additional AGE queries on the hot path.**

```
BEFORE v6.0:
  check_alert → campaign_id (string) → triage writes to decision node
  situation_context has NO campaign info

AFTER v6.0:
  check_alert → campaign_id (string)
  ↓
  CampaignAsyncState.get_campaign_context(campaign_id)
  → {campaign_id, first_seen, category, member_count} from CACHE
  ↓
  situation_context.nodes.append(TraversalNode(type="campaign"))
  ↓
  Analyst sees campaign context in evidence panel
```

The cache extension is the critical design choice. When
`mark_materialized` is called (after background AGE write
completes), store the campaign properties alongside the
campaign_id. v6.0 reads from this enriched cache — not from AGE.

### 2.3 Why Cache Extension, Not AGE Read

| Option | Latency | Risk |
|---|---|---|
| AGE read for campaign properties | +1-3ms (pooled query) | Consumes Phase 3B's 3.15ms headroom |
| **Cache extension** | **~0ms** (in-memory dict lookup) | **Zero latency impact** |
| check_alert returns structured object | ~0ms but changes return type | Breaking change to triage.py |

Cache extension preserves the `Optional[str]` return type of
check_alert (no breaking change to triage.py) and adds zero
latency to the hot path.

### 2.4 What v6.0 Does NOT Do

| Constraint | Why |
|---|---|
| No scorer changes | v6.0 is advisory context, not factor input |
| No tensor expansion | v7.0 scope (needs override-rate evidence) |
| No conservation/DK mutation | Read-only display |
| No new AGE writes | Campaign materialization unchanged |
| No check_alert return type change | triage.py compatibility |
| No CONTINUES edges | Phase 4 scope |
| No new AGE reads on hot path | Cache extension handles it |

---

## §3 — Implementation

### 3.1 Extend CampaignAsyncState (~15 lines)

```python
# backend/app/domains/soc/campaigns.py
# Add to CampaignAsyncState:

@dataclass  # NOT frozen — member_count is mutated by increment_member_count
class CampaignContext:
    """Cached campaign properties for v6.0 context injection."""
    campaign_id: str
    category: str
    first_seen: str       # ISO timestamp
    member_count: int = 0  # updated on each MEMBER_OF addition

class CampaignAsyncState:
    # ... existing fields ...
    campaign_contexts: dict[str, CampaignContext] = field(
        default_factory=dict)

    def mark_materialized_with_context(
        self, campaign_id: str, category: str,
        first_seen: str, member_count: int = 0,
    ) -> None:
        """Cache campaign properties at materialization time."""
        if campaign_id:
            self.materialized_campaigns[str(campaign_id)] = str(campaign_id)
            self.campaign_contexts[str(campaign_id)] = CampaignContext(
                campaign_id=str(campaign_id),
                category=category,
                first_seen=first_seen,
                member_count=member_count,
            )

    def get_campaign_context(self, campaign_id: str) -> CampaignContext | None:
        """Read cached campaign properties. Returns None if not cached."""
        return self.campaign_contexts.get(str(campaign_id))

    def increment_member_count(self, campaign_id: str) -> None:
        """Called ONLY for post-materialization joins (alerts that
        join AFTER the initial materialization). Do NOT call for
        edges created DURING materialization — those are counted
        in mark_materialized_with_context's member_count param."""
        ctx = self.campaign_contexts.get(str(campaign_id))
        if ctx:
            ctx.member_count += 1
```

**member_count discipline:** The initial member_count is SET
(not accumulated) at materialization time from the authoritative
MEMBER_OF edge count. `increment_member_count` is ONLY for
post-materialization joins. This prevents double-counting.

**Where to call `mark_materialized_with_context`:** In the
background materialization path, AFTER the AGE write succeeds.
The campaign properties (category, first_seen) are already
available in the `seed` dict at materialization time (scan 7,
lines 548-552). Member count comes from the MEMBER_OF edge
count written during materialization.

**Backward compatibility:** The existing `mark_materialized(campaign_id)`
method stays. `mark_materialized_with_context` is additive.
If v6.0 calls `get_campaign_context` and gets None (campaign
materialized before v6.0, or cache cold), it falls back to
showing campaign_id only (no properties).

### 3.2 Add Campaign Context to Situation Context Builder (~25 lines)

```python
# backend/app/services/soc_situation_pattern.py
# Add campaign context node after alert/event nodes:

# Imports at TOP of this file (NOT inside the function):
#   from typing import Any
#   from app.domains.soc.campaign_holdout import banner_suppressed

def _add_campaign_context(
    context: SituationContext,
    campaign_id: str | None,
    async_state: CampaignAsyncState | None,
    alert_id: str | None = None,
) -> dict[str, bool]:
    """Add campaign TraversalNode to situation context if available.

    RETURNS the holdout flags {"is_campaign_alert", "campaign_context_shown"}
    so the CALLER (triage.py) can persist them to the DECISION NODE — that
    persistence is the v7.0 measurement contract (§5.2), NOT context.metadata,
    which is ephemeral. Isolated alert → {"is_campaign_alert": False, ...}.

    alert_id is needed for the holdout clock (§5.2)."""
    # Resolve campaign id: materialized (from check_alert) OR provisional-pending.
    # Provisional read is in-memory (zero AGE) — see Codex discovery step 7.
    cid = campaign_id
    if not cid and async_state is not None and alert_id:
        cid = async_state.get_pending_campaign_id(alert_id)  # str | None
    if not cid:
        return {"is_campaign_alert": False, "campaign_context_shown": False}

    # Holdout clock (§5.2): decide shown/suppressed for THIS alert.
    shown = (not banner_suppressed(alert_id)) if alert_id else True
    flags = {"is_campaign_alert": True, "campaign_context_shown": shown}

    # Display-side log on context.metadata IF it exists (for the API response).
    # This is NOT the measurement contract — the caller persists `flags` to the
    # decision node. Guarded so a SituationContext without .metadata can't throw.
    meta = getattr(context, "metadata", None)
    if isinstance(meta, dict):
        meta.update(flags)

    if not shown:
        return flags  # control arm: no node, no advisory — but flags still returned

    properties: dict[str, Any] = {"campaign_id": cid}
    source = "graph_store_cached"  # NOT "graph_store" — cache mirror, may lag AGE

    # Try enriched cache first (zero AGE cost)
    if async_state:
        cached = async_state.get_campaign_context(cid)
        if cached:
            properties.update({
                "category": cached.category,
                "first_seen": cached.first_seen,
                "member_count": cached.member_count,
                "age_days": _campaign_age_days(cached.first_seen),
            })

    context.nodes.append(TraversalNode(
        id=f"campaign:{cid}",
        type="campaign",
        label="Active Campaign",
        properties=properties,
        depth=1,
        source=source,
    ))

    # Advisory evidence note — SCALED to evidence level
    n = properties.get("member_count")
    if n is None or n < 3:
        # Emerging / pending — don't oversell a 2-alert coincidence
        advisory = ("This alert may be part of an emerging pattern"
                    + (f" ({n} members so far)." if n else "."))
    else:
        # Established campaign — escalation advisory warranted
        advisory = (f"Active {n}-member campaign. "
                    "Consider escalating the campaign, not just this alert.")

    age_days = properties.get("age_days")
    age_text = ("started today" if age_days is not None and age_days < 1
                else f"{age_days} days active" if age_days is not None
                else "")
    member_text = f"{n} members" if n else ""
    category_text = properties.get("category", "")
    label_parts = [p for p in [member_text, age_text, category_text] if p]

    context.evidence_chain.append({
        "type": "campaign_advisory",
        "source": source,
        "label": f"campaign context · {' · '.join(label_parts)}" if label_parts
                 else "campaign context",
        "advisory": advisory,
    })

    return flags

def _campaign_age_days(first_seen: str) -> int:
    """Days since campaign first_seen."""
    from datetime import datetime, timezone
    try:
        fs = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - fs).days)
    except (ValueError, TypeError):
        return 0
```

### 3.3 Wire Into Triage / Situation Builder (~10 lines)

**CRITICAL TIMING DISCOVERY from the scan:**

triage.py's flow runs:
```
Step 3 (line 502):  situation_analysis = analyze_situation(...)
Step 5b (line 867): _campaign_id = await check_alert(alert_id)
```

Campaign check happens AFTER situation analysis. So the situation
builder at Step 3 does NOT have campaign_id yet. Option W1
(pass campaign_id to the situation builder) doesn't work as a
parameter to the initial call.

**Solution: Post-hoc campaign context addition.**

After BOTH steps complete, append the campaign node to the
existing situation context:

```python
# In triage.py, AFTER Step 5b (line ~894):

# NOTE: imports go at TOP of triage.py, not inside the conditional.
# from app.services.soc_situation_pattern import _add_campaign_context
# from app.domains.soc.campaigns import _DEFAULT_CAMPAIGN_ASYNC_STATE
#   (use the async_state the CampaignMatcher already holds if one exists —
#    see Codex discovery step 6 — do not create a second reference.)

# Step 5c: Add campaign context to situation (v6.0)
# CALL ALWAYS (do NOT guard on _campaign_id): _add_campaign_context resolves
# materialized OR pending campaign id internally, so pending-seed alerts still
# get the provisional banner AND get logged in the holdout. It returns the
# holdout flags for decision-node persistence below.
campaign_flags = {"is_campaign_alert": False, "campaign_context_shown": False}
_ctx = getattr(situation_analysis, "situation_context", None)  # actual attr per discovery step 4
if _ctx is not None:
    campaign_flags = _add_campaign_context(
        _ctx,
        _campaign_id,                       # may be None for a pending seed
        _DEFAULT_CAMPAIGN_ASYNC_STATE,      # or the matcher's existing async_state
        alert_id=alert_id,
    )

# Step 5d: PERSIST holdout flags to the DECISION NODE (the v7.0 measurement
# contract — §5.2). Write them at the SAME site that writes campaign_id to the
# decision node (~line 891, per discovery step 8). context.metadata is ephemeral
# and is NOT the measurement contract — the decision node is what the 90-day
# retrospective queries.
#   decision_node_props["is_campaign_alert"]      = campaign_flags["is_campaign_alert"]
#   decision_node_props["campaign_context_shown"] = campaign_flags["campaign_context_shown"]
# (Use the actual property-write mechanism discovered at the line-891 write site.)
```

This is cleaner than moving campaign check before situation
analysis (which would change the triage flow) or having the
situation builder call check_alert itself (which couples the
builder to the campaign matcher).

**Why post-hoc is safe:** SituationContext.nodes is a mutable
list. Appending a campaign TraversalNode after initial
construction is the same pattern used by other context
enrichment steps. The situation_context is not frozen or
serialized until the final response.

**The Codex prompt must discover the exact attribute path:**

```
# Does situation_analysis have a situation_context attribute?
grep -n "situation_context\|SituationContext" \
  backend/app/services/situation.py
grep -n "situation_analysis\." \
  backend/app/routers/triage.py
```

If situation_analysis doesn't directly carry situation_context,
the context may be in a different attribute or constructed
separately. Discovery step resolves this.

### 3.4 Graceful Degradation

| Scenario | Behavior |
|---|---|
| No campaign match (isolated alert) | No campaign node in context. No advisory note. |
| Campaign match but no cached context (cold cache) | Campaign node with campaign_id only. No size/age/category. Advisory note still present. |
| Campaign match with cached context | Full campaign node with all properties. Advisory note with details. |
| CampaignAsyncState unavailable | No campaign node. Silent degradation. |
| Campaign properties partially available | Show what exists, omit what doesn't. |

The analyst NEVER sees an error from campaign context. The worst
case is "campaign node with just an ID" — which is still more
information than the current state (nothing).

---

## §4 — What the Analyst Sees

### 4.1 Isolated Alert (No Campaign)

No change from current behavior. No campaign node in the
situation context. The evidence panel shows the alert analysis
without campaign context.

### 4.2 Campaign Alert (Full Context)

```
Alert: Suspicious credential access from admin-jsmith

Situation Context:
  ┌ Alert Node
  │  type: credential_access
  │  severity: high
  │  source: graph_store
  │
  ├ Campaign Node                              ← NEW (v6.0)
  │  ██ Active Campaign: CAMP-2026-06-15-cred
  │     5 members · 3 days active
  │     category: credential_access
  │     source: graph_store_cached
  │
  ├ Entity Node
  │  admin-jsmith (privileged user)
  │
  └ Asset Node
     dc-prod-01 (domain controller)

Evidence Chain:
  ... existing evidence ...
  ██ Campaign Advisory:                        ← NEW (v6.0)
     "This alert is part of an active multi-member campaign.
      Consider escalating the campaign, not just this alert."

Recommendation: escalate_tier2 (confidence 0.82)
  (scorer is campaign-UNAWARE — recommendation unchanged)
```

### 4.3 The Demo Moment

```
Act 1: Fire first alert → isolated, no campaign context
       (pending seed created in background)

Act 2: Fire second related alert → pending match found
       Campaign node appears: campaign_id visible
       Properties may be cold-cache (no category/age yet)
       Advisory: "This alert is part of an active campaign"
       (background materialization in progress)

Act 3: Fire third related alert → materialized match
       Campaign node has full context:
       "3 members · credential_access · started today"
       Advisory: "Consider escalating the campaign"
       (cache populated after materialization completed)

Act 4: Analyst sees the pattern building in real time
       "The system grouped these alerts and is telling you
        there's a coordinated campaign"
```

**Timing note:** Between Acts 2 and 3, background materialization
completes (~215ms). Act 2 shows the pending-provisional path
(campaign_id only). Act 3 shows the fully-cached path (all
properties). If the demo fires alerts faster than 215ms, Acts
2 AND 3 may both show the pending path — the full context
appears on the NEXT alert after materialization completes.
This is honest and acceptable for the demo.

**Demo script timing:** For a controlled demo showing all 4 acts,
add a 500ms pause between alert fires. This ensures Act 3 sees
the fully-materialized campaign (background write completes in
~215ms). Document this in the demo runbook.

---

## §5 — Product Integrity

### 5.1 Registry Additions

| ID | Type | Claim | Enforcement |
|---|---|---|---|
| C-20 | CANONICAL | "Campaign context is advisory — the analyst decides, not the system" | v6.0 displays campaign info but does NOT change the recommendation |
| F-22 | FORBIDDEN | Campaign context presented as scorer input when it is display-only | v6.0 campaign node is in situation_context, not factor vector |
| F-23 | FORBIDDEN | Cached campaign properties presented as live graph truth | source="graph_store_cached"; member_count is an approximation reconciled against AGE |

### 5.2 Holdout Clock (Ships WITH v6.0)

The v7.0 override-rate measurement MUST start at v6.0 deploy.
It cannot be retrofitted — data without the holdout flag is
confounded and unusable.

**The confound:** Comparing campaign vs isolated alert override
rates measures "campaigns are different" (trivially true by
construction), NOT "showing campaign context changes analyst
behavior" (the v7.0 hypothesis).

**The fix: banner holdout.**

```python
# backend/app/domains/soc/campaign_holdout.py
import hashlib

def banner_suppressed(alert_id: str, holdout_pct: int = 15) -> bool:
    """Deterministic per-alert holdout. Stable across retries.
    
    NOTE: 15% may need adjustment. With 259 campaigns and 15%,
    the control arm gets ~39 campaigns. Detecting a 10pp lift
    at p<0.05 requires ~150+ alerts per arm. Review after 30
    days: if campaign alert volume is low, increase to 25%.
    Cost of 25%: 10% more analysts miss campaign context.
    Cost of 15% with insufficient power: 90 days of useless data."""
    h = int(hashlib.sha256(alert_id.encode()).hexdigest(), 16)
    return (h % 100) < holdout_pct
```

Wire into `_add_campaign_context` — see §3.2 for the canonical, complete
implementation. The holdout-relevant behavior it guarantees:

```python
# (excerpt — full function in §3.2)
# - resolves materialized OR pending campaign id (so pending alerts log too)
# - shown = not banner_suppressed(alert_id)
# - RETURNS {"is_campaign_alert": bool, "campaign_context_shown": bool}
#   for the CALLER to persist to the DECISION NODE
# - control arm (suppressed): returns flags, adds NO node / NO advisory
```

**Data contract (CRITICAL — this is where v1.5 was wrong):** the holdout flags
must be persisted to the **DECISION NODE in AGE**, at the same write site that
stores `campaign_id` (triage ~line 891). They must NOT live only on
`situation_context.metadata`, which is ephemeral response context and is NOT
queried by the 90-day retrospective. Every persisted SOC decision node carries:
- `is_campaign_alert: bool`
- `campaign_context_shown: bool`

`_add_campaign_context` returns these flags; triage Step 5d writes them to the
decision node (§3.3). If they land only on `context.metadata`, the v7.0 clock
has zero queryable data and the measurement silently fails.

**Provisional-pending dependency:** the resolver calls
`async_state.get_pending_campaign_id(alert_id)` — a NEW method on
`CampaignAsyncState` (Codex discovery step 7) that reads `pending_seed_campaigns`
in-memory (zero AGE). It exists only if discovery step 0 shows `check_alert`
returns `None` for pending seeds. If `check_alert` already returns pending ids,
`get_pending_campaign_id` returns `None`/is a no-op and the materialized path is used.

**Single-worker assumption:** The holdout is deterministic per-alert (sha256), so
it's consistent across workers. No shared state needed.

### 5.3 What v6.0 Preserves

- Scorer tensor shape: (6,4,6) = 144 UNCHANGED
- DK weights: UNCHANGED (no campaign factors)
- Conservation formula: UNCHANGED (no new learning)
- check_alert return type: `Optional[str]` UNCHANGED
- Phase 3B hot-path budget: ≤ 5ms preserved (cache read is ~0ms)
- triage.py campaign_id write: UNCHANGED (still writes to decision node)
- CONTINUES edges: 0 (Phase 4 only)
- BELONGS_TO edges: 0 (MEMBER_OF is canonical)

---

## §6 — Test Gates

**Context builder tests:**

- Campaign alert: situation context includes TraversalNode type="campaign"
- Isolated alert: NO campaign node in situation context
- Campaign node properties: campaign_id, category, first_seen,
  member_count, age_days (when cached context available)
- Campaign node with cold cache: only campaign_id present (graceful)
- Campaign advisory evidence entry present for campaign alerts
- Campaign advisory absent for isolated alerts
- source="graph_store_cached" on campaign node (F-23)

**Cache extension tests:**

- mark_materialized_with_context stores campaign properties
- get_campaign_context returns stored properties
- get_campaign_context returns None for unknown campaign_id
- increment_member_count increases count
- Existing mark_materialized still works (backward compat)

**Integration tests:**

- triage.py adds campaign context POST-HOC (after Step 5b)
- Full analyze path produces campaign context when campaign exists
- Full analyze path works when no campaign exists (no crash)
- Campaign context has correct campaign_id from check_alert
- Timing verification (CODE REVIEW, not unit test): confirm
  _add_campaign_context is called AFTER check_alert, not during
  analyze_situation. Verify by reading triage.py line order.

**Cold-cache / pending-path tests:**

- Pending match (seed not yet materialized): campaign node has
  campaign_id only (no category/age/member_count)
- After materialization completes: campaign node has full properties
- Advisory note present in BOTH pending and materialized states
  (different detail level is acceptable)

**Advisory scaling tests:**

- member_count < 3: advisory says "emerging pattern" (not "consider escalating")
- member_count ≥ 3: advisory says "Active N-member campaign"
- member_count None (cold cache): advisory says "emerging pattern" without count
- age_days < 1: label says "started today" (not "0 days active")

**Holdout clock tests:**

- banner_suppressed is deterministic (same alert_id → same result)
- ~15% suppression over 1000 random alert_ids (tolerance ±3%)
- holdout_pct=0 → never suppressed
- holdout_pct=100 → always suppressed
- When suppressed: is_campaign_alert=True in metadata, campaign_context_shown=False
- When suppressed: NO campaign node in context, NO advisory
- When NOT suppressed: campaign node + advisory present as normal
- is_campaign_alert and campaign_context_shown ALWAYS logged (both arms)
- **DECISION-NODE PERSISTENCE (the measurement contract):** after a full analyze
  of a campaign alert, the persisted decision node carries `campaign_context_shown`
  and `is_campaign_alert` — query the decision node (not just the API response).
  This is the test that protects the 90-day clock; if it's only on
  `situation_context.metadata`, this test FAILS and the holdout is a no-op.
- Pending-seed alert: `is_campaign_alert=True` is logged AND a provisional node
  appears (when not suppressed), proving the provisional-pending resolver is wired.
- Holdout metadata survives SituationContext.to_dict() serialization
  (verify is_campaign_alert and campaign_context_shown appear in the
  API response metadata — separate from, and in addition to, decision-node persistence)

**Performance tests (unit-level, not live AGE):**

- _add_campaign_context with cached context: < 0.1ms
  (verify it's an in-memory dict lookup, not an AGE query)
- _add_campaign_context with no campaign: < 0.01ms (early return)

**Regression tests:**

- All existing SOC tests pass
- Phase 3 async tests pass (30)
- Campaign suite (106) passes
- soc_situation_pattern existing tests pass

---

## §7 — Execution Plan

### 7.1 Files Changed

```
Modify:
  backend/app/domains/soc/campaigns.py
    - Add CampaignContext dataclass (~10 lines)
    - Add mark_materialized_with_context to CampaignAsyncState (~15 lines)
    - Add get_campaign_context to CampaignAsyncState (~3 lines)
    - Add increment_member_count (~4 lines)
    - Add get_pending_campaign_id(alert_id) -> str | None to CampaignAsyncState
      (ONLY if discovery step 0 shows check_alert returns None for pending seeds;
       reads pending_seed_campaigns in-memory, zero AGE) (~4 lines)
    - Call mark_materialized_with_context in background
      materialization path (replace mark_materialized call)

  backend/app/services/soc_situation_pattern.py
    - Add _add_campaign_context module-level function (~40 lines) — RETURNS
      holdout flags dict for decision-node persistence
    - Add _campaign_age_days helper (~5 lines)
    - Imports at file top: `from typing import Any`,
      `from app.domains.soc.campaign_holdout import banner_suppressed`,
      CampaignAsyncState (type hints)
    - Does NOT change existing builder function signatures

  backend/app/routers/triage.py
    - After Step 5b (~line 894): call _add_campaign_context ALWAYS (Step 5c),
      capture returned flags
    - Step 5d: persist is_campaign_alert + campaign_context_shown to the
      DECISION NODE at the same site that writes campaign_id (~line 891)
    - Import _add_campaign_context from soc_situation_pattern
    - Import _DEFAULT_CAMPAIGN_ASYNC_STATE from campaigns (or reuse the
      matcher's existing async_state — discovery step 6)
    - Does NOT change Step 3 or Step 5b timing

Create:
  backend/app/domains/soc/campaign_holdout.py
    - banner_suppressed(alert_id, holdout_pct=15) -> bool (sha256 mod 100)

  backend/tests/test_campaign_v6_context.py
    - All test gates from §6 (incl. decision-node persistence)

  backend/tests/test_campaign_holdout.py
    - banner_suppressed determinism + suppression-rate gates

Do NOT modify:
  - scorer / ProfileScorer
  - conservation / DK
  - GraphStore protocol
  - copilot-sdk (TraversalNode/SituationContext already imported)
  - frontend (v6.0 is API/context only — frontend consumes
    existing situation_context rendering)
  - check_alert return type (stays Optional[str])
  - Situation builder function signatures (context added post-hoc)
  - Step 3 (analyze_situation) timing
  - Step 5b (check_alert) timing
```

### 7.2 Blast Radius

| Change | Files | Risk |
|---|---|---|
| CampaignContext dataclass | campaigns.py | ZERO — additive |
| CampaignAsyncState extension | campaigns.py | LOW — additive methods, existing methods unchanged |
| Situation pattern extension | soc_situation_pattern.py | LOW — additive parameter + function |
| triage.py post-hoc wiring | triage.py | LOW — ~5 lines after Step 5b, campaign_id already available |
| Tests | 1 new file | ZERO — additive |
| **Total** | **3 modified + 3 new** | **LOW** |

### 7.3 Effort

```
Cache extension (CampaignAsyncState):   ~30 min
Situation context builder:              ~45 min
triage.py wiring:                       ~15 min
Tests:                                  ~1.5h
Verification:                           ~30 min
Total:                                  ~4.5h (0.75d)
```

### 7.4 Execution Sequencing

Implementation is preceded by a read-only discovery pass.
The design has enough moving parts (pending-seed derivation,
SituationContext attribute path, decision-node write mechanism)
that Codex must confirm exact names before writing code.

```
Prompt 1: Read-only discovery pass (no code changes)
  → Answer 8 implementation anchors (§8.1)
  → Report exact names, paths, mechanisms
  → Roadmap reviews report before approving Prompt 2

Prompt 2: Implementation (§8.2)
  → Patched with exact names from Prompt 1
  → Code changes + tests

Prompt 3: GPT-5.5 review
  → Code review pass on Prompt 2 output

Prompt 4: Live validation / M8 recheck (§9)
  → Manual, not Codex
```

**Why discovery first:** v6.0 depends on several exact repo
facts that must be discovered, not assumed:

| Anchor | Risk if assumed wrong |
|---|---|
| check_alert pending behavior | v6.0 Act 2 unreachable (demo breaks) |
| Seed-key derivation location | get_pending_campaign_id put on wrong class |
| Async state ref in triage | Second reference to same singleton |
| SituationContext attribute path | Post-hoc append targets wrong object |
| Decision-node write mechanism | Holdout flags land on response only (90-day clock is a no-op) |
| Holdout testability | Tests pass but don't verify decision-node persistence |
| Hot-path AGE reads | v6.0 adds latency, consuming Phase 3B headroom |
| mark_materialized call site | Properties not available → cache extension fails |

---

## §8 — Codex Prompts

### 8.1 Prompt 1: Read-Only Discovery (Run First)

```
WORKING DIRECTORY: gen-ai-roi-demo-v4-v50
ACTIVATE:
  & "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
TASK: Campaign v6.0 — read-only discovery pass. NO code changes.
TASK TYPE: Report exact implementation anchors.

RULE: Do NOT create, modify, or delete any file. Read only.

Anchor 1 — check_alert pending behavior:
  grep -n "async def check_alert\|def check_alert" \
    backend/app/domains/soc/campaigns.py
  Read full method body. Trace return paths.
  REPORT: does check_alert return campaign_id or None for
  a PENDING (un-materialized) seed? Exact return statement + line.

Anchor 2 — Seed-key derivation location:
  grep -rn "def.*seed_key\|make_campaign_seed_key\|_compute_seed" \
    backend/app/domains/soc/campaigns.py
  Read each method. REPORT: method name, class, parameters.
  Can CampaignAsyncState call this, or does it need
  CampaignMatcher context? Where should get_pending_campaign_id go?

Anchor 3 — Async state reference in triage.py:
  grep -n "CampaignMatcher\|async_state\|_DEFAULT_CAMPAIGN_ASYNC_STATE" \
    backend/app/routers/triage.py
  Read lines 870-900. REPORT: how is CampaignMatcher constructed?
  Does it expose .async_state? What variable holds it after Step 5b?

Anchor 4 — SituationContext attribute path:
  grep -n "def analyze_situation" backend/app/services/situation.py
  Read return type + return statement.
  grep -n "situation_analysis\." backend/app/routers/triage.py
  grep -rn "class SituationContext" backend/app/ copilot_sdk/ --include="*.py"
  Read class definition. REPORT: exact attribute path
  (situation_analysis.X), field names (.nodes, .evidence_chain
  or actual name, .metadata or absent).

Anchor 5 — Decision-node write mechanism:
  grep -n "campaign_id\|SET d\.\|write.*decision\|Decision" \
    backend/app/routers/triage.py
  Read lines 885-905. REPORT: exact line, mechanism (Cypher SET /
  dict / write_decision()), code snippet. Can bool properties be
  added using the same mechanism?

Anchor 6 — Holdout testability:
  grep -rn "Decision\|decision_node\|mock.*decision" \
    backend/tests/test_campaign_*.py backend/tests/test_triage*.py \
    --include="*.py" | head -20
  REPORT: do tests mock decision-node writes? What pattern?

Anchor 7 — Hot-path AGE reads:
  grep -n "cypher\|execute.*query\|neo4j\|ag_catalog" \
    backend/app/domains/soc/campaigns.py | head -30
  Read _check_materialized_campaign_cache method body.
  REPORT: cache-hit path has zero AGE reads? Fallback on miss?
  Would _add_campaign_context trigger any AGE read?

Anchor 8 — mark_materialized call site:
  grep -n "mark_materialized\b" backend/app/domains/soc/campaigns.py
  Read 10 lines of context around each call.
  REPORT: what variables are in scope? category, first_seen,
  member_count available? Can mark_materialized be replaced with
  mark_materialized_with_context without additional AGE reads?

OUTPUT FORMAT:
  === v6.0 DISCOVERY REPORT ===
  ANCHOR 1: [findings]
  ANCHOR 2: [findings]
  ...
  ANCHOR 8: [findings]
  === RECOMMENDATIONS ===
  [any implementation plan adjustments]
  === END DISCOVERY REPORT ===

EXIT: All 8 anchors reported. ZERO files changed.
```

### 8.2 Prompt 2: Implementation (After Discovery Approved)

**Before running:** Patch this prompt with exact names from the
Prompt 1 discovery report. Replace every `<actual ...>` placeholder
and illustrative name (e.g., `_seed_key`, `situation_context`,
`_DEFAULT_CAMPAIGN_ASYNC_STATE`) with the ACTUAL names Codex
reported. Do NOT run this prompt with assumed names.

```
WORKING DIRECTORY: gen-ai-roi-demo-v4-v50
  (campaign code + triage + situation pattern all in this repo)
  (TraversalNode / SituationContext imported from copilot-sdk —
   no SDK changes needed, just imports)
ACTIVATE:
  & "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
TASK: Campaign v6.0 — add campaign context to SOC situation context.
TASK TYPE: Cache extension + post-hoc context addition + tests.

Stage 1 (discovery — verify BEFORE implementing):
  0. GATE — Does check_alert return campaign_id for PENDING seeds?
     grep -n "pending_seed_campaigns\|return None\|return campaign_id\|def .*seed_key\|seed_key\|_async_state\|async_state" \
       backend/app/domains/soc/campaigns.py
     (a) For a PENDING (un-materialized) seed, does check_alert return
         the campaign_id or None?
     (b) Confirm the EXACT seed-key method name (e.g. _seed_key,
         seed_key_for, _compute_seed_key) and the async-state attribute
         name on the class that owns check_alert. The snippets below
         assume `self._seed_key(...)` and `self._async_state` — replace
         with the ACTUAL names found here.
     IF check_alert returns None for pending: add get_pending_campaign_id
     to CampaignAsyncState (do NOT change check_alert — see step 7):
       def get_pending_campaign_id(self, alert_id) -> str | None:
           seed_key = <actual seed-key derivation>(alert_id)
           return self.pending_seed_campaigns.get(seed_key)
     Zero AGE reads (in-memory). Without it, v6.0's Act 2 is unreachable.

  1. Confirm check_alert returns Optional[str]:
     grep -n "async def check_alert" \
       backend/app/domains/soc/campaigns.py

  2. Confirm CampaignAsyncState structure + mark_materialized call site:
     grep -n "class CampaignAsyncState\|mark_materialized\|materialized_campaigns" \
       backend/app/domains/soc/campaigns.py

  3. CRITICAL — Confirm triage.py timing:
     grep -n "analyze_situation\|check_alert\|situation_analysis\|_campaign_id" \
       backend/app/routers/triage.py
     VERIFY: situation_analysis is built BEFORE _campaign_id is
     computed. If so, campaign context must be added POST-HOC
     (after both steps complete), not as a parameter to the
     situation builder.

  4. Find the situation_context object AND its fields:
     grep -n "situation_context\|\.situation\|SituationContext" \
       backend/app/routers/triage.py
     grep -n "def analyze_situation" \
       backend/app/services/situation.py
     FIND: which attribute of the return value holds the
     SituationContext. Common patterns:
       situation_analysis.situation_context
       situation_analysis.context
       situation_analysis (if it IS a SituationContext)
     ALSO confirm the SituationContext field names the code appends to:
     grep -n "class SituationContext\|nodes\|evidence_chain\|metadata" \
       backend/app/services/soc_situation_pattern.py   # or the SDK module that defines it
     CONFIRM SituationContext has: .nodes (list), .evidence_chain (or the
     ACTUAL name), and whether it has .metadata. If a field name differs,
     use the real one. If .metadata does NOT exist, the display-side log
     is skipped (the getattr guard handles it) — the DECISION-NODE
     persistence (step 8) is what matters for the measurement.

  5. Confirm what properties the seed dict carries at materialization:
     grep -n "seed\[.campaign_id.\]\|seed\[.category.\]\|first_seen\|member" \
       backend/app/domains/soc/campaigns.py

  6. Confirm _DEFAULT_CAMPAIGN_ASYNC_STATE exists AND check
     whether triage.py already has an async state reference:
     grep -n "_DEFAULT_CAMPAIGN_ASYNC_STATE\|default.*async.*state\|async_state\|camp.*state" \
       backend/app/domains/soc/campaigns.py \
       backend/app/routers/triage.py
     If triage.py already references the async state (e.g.,
     through the CampaignMatcher instance at line 884), use
     THAT reference. Do not create a second reference.

  7. CRITICAL — provisional-pending read is a SEPARATE method:
     If discovery step 0 shows check_alert returns None for
     pending seeds, do NOT modify check_alert's return behavior.
     Instead, create a separate method:
       def get_pending_campaign_id(self, alert_id) -> str | None
     Call this from _add_campaign_context, NOT from check_alert.
     Reason: triage.py writes campaign_id to the decision node
     when check_alert returns non-None (line 891). Changing
     check_alert to return pending campaign_ids would cause
     triage to write unverified pending IDs to decision nodes.
     The provisional read is for DISPLAY only (context injection),
     not for persistence (decision node writes).
     NOTE: get_pending_campaign_id needs seed-key derivation
     (rule_type, entity_key, category, bucket). This context
     may only exist on CampaignMatcher, not CampaignAsyncState.
     Put the method where the derivation context lives, or have
     triage.py pre-resolve using the matcher it already has
     (line 884) and pass the resolved ID to _add_campaign_context.

  8. CRITICAL — Find the DECISION-NODE write site (holdout persistence):
     grep -n "campaign_id\|decision_node\|write.*decision\|set.*propert\|MATCH.*Decision\|CREATE.*Decision" \
       backend/app/routers/triage.py
     FIND the exact place (~line 891) where campaign_id is written to the
     decision node in AGE. The holdout flags is_campaign_alert and
     campaign_context_shown MUST be written to the decision node at THIS
     SAME site (Step 5d), using the same property-write mechanism.
     This is the v7.0 measurement contract — the 90-day retrospective
     queries the DECISION NODE, not situation_context.metadata. If the
     flags land only on context.metadata, the holdout produces NO
     queryable data and silently fails. Identify the mechanism (decision
     props dict, a write_decision call, a Cypher SET) and add the two
     boolean properties to it.

Modify:
  backend/app/domains/soc/campaigns.py
    - Add CampaignContext dataclass (campaign_id, category,
      first_seen, member_count)
    - Add mark_materialized_with_context() to CampaignAsyncState
    - Add get_campaign_context() to CampaignAsyncState
    - Add increment_member_count() to CampaignAsyncState
    - Add get_pending_campaign_id(alert_id) -> str | None to
      CampaignAsyncState (ONLY if discovery step 0 → check_alert returns
      None for pending; reads pending_seed_campaigns in-memory, zero AGE)
    - In the background materialization path: call
      mark_materialized_with_context instead of mark_materialized
      (pass category, first_seen from the seed dict)
    - In MEMBER_OF edge creation: call increment_member_count
    - Keep existing mark_materialized (backward compat)

  backend/app/services/soc_situation_pattern.py
    - Add _add_campaign_context(context, campaign_id, async_state, alert_id)
      as a MODULE-LEVEL function (not tied to a builder class)
    - It RETURNS {"is_campaign_alert": bool, "campaign_context_shown": bool}
      (the caller persists these to the decision node — §3.3 Step 5d)
    - It resolves materialized OR pending campaign id internally
    - alert_id param needed for holdout clock (banner_suppressed)
    - Add _campaign_age_days(first_seen) helper
    - Imports at file TOP: `from typing import Any`,
      `from app.domains.soc.campaign_holdout import banner_suppressed`,
      CampaignAsyncState (type hints)

  backend/app/routers/triage.py
    - AFTER campaign check (Step 5b, ~line 894):
      Step 5c: call _add_campaign_context ALWAYS (no `if _campaign_id` guard
        — it resolves pending internally), capture the returned flags
      Step 5d: persist is_campaign_alert + campaign_context_shown to the
        DECISION NODE at the campaign_id write site (~line 891, discovery
        step 8) — see §3.3 for the exact pattern
    - Import _add_campaign_context from soc_situation_pattern
    - Import _DEFAULT_CAMPAIGN_ASYNC_STATE from campaigns (or reuse the
      matcher's existing async_state — discovery step 6)

Create:
  backend/app/domains/soc/campaign_holdout.py
    - banner_suppressed(alert_id, holdout_pct=15) → bool
    - Deterministic per-alert (sha256 mod 100), stable

  backend/tests/test_campaign_v6_context.py
    - Test gates from §6

  backend/tests/test_campaign_holdout.py
    - banner_suppressed is deterministic (same input → same result)
    - ~15% suppression rate over 1000 random alert_ids
    - holdout_pct=0 → never suppressed
    - holdout_pct=100 → always suppressed

NON-NEGOTIABLES:
  - check_alert return type stays Optional[str] — do NOT change
  - Zero new AGE reads on the hot path (cache only)
  - source="graph_store_cached" (NOT "graph_store") for campaign
    context — it's a cache mirror, may lag AGE (F-23)
  - Advisory SCALES with evidence: <3 members → "emerging pattern";
    ≥3 members → "active campaign, consider escalating"
  - member_count SET at materialization (from edge count), only
    INCREMENT for post-materialization joins. No double-counting.
  - Campaign context added POST-HOC (after both situation analysis
    AND campaign check complete) — do NOT change the timing of
    either Step 3 or Step 5b in triage.py
  - HOLDOUT ships with v6.0: banner_suppressed() + is_campaign_alert +
    campaign_context_shown written to the DECISION NODE (the measurement
    contract), NOT only to situation_context.metadata. 15% holdout.
    Cannot be retrofitted.
  - _add_campaign_context is called ALWAYS (no `if _campaign_id` guard);
    it resolves materialized-or-pending id internally and returns the
    holdout flags for the caller to persist to the decision node.
  - Campaign node type="campaign", source="graph_store_cached"
  - Advisory evidence entry type="campaign_advisory"
  - Isolated alerts: NO campaign node, NO advisory (flags returned with
    is_campaign_alert=False)
  - Scorer UNCHANGED — no tensor, no DK, no conservation changes
  - No CONTINUES edges. No BELONGS_TO edges.
  - Existing mark_materialized method stays (backward compat)
  - Single-worker assumption: state the assumption explicitly in
    a code comment. Production upgrade (shared cache/outbox) noted.
  - All existing campaign tests (106) pass
  - All Phase 3 async tests (30) pass

RUN (Codex scope — automated tests only; use the repo's configured test
runner, do NOT invoke pytest literally):
  <repo configured runner> backend/tests/test_campaign_v6_context.py  (verbose, 60s timeout)
  <repo configured runner> backend/tests/test_campaign_holdout.py     (verbose, 60s timeout)
  <repo configured runner> backend/tests/test_campaign_*.py           (verbose, 60s timeout)
  <repo configured runner> backend/tests/                             (quiet, 300s timeout)

EXIT: Campaign context visible in situation_context for campaign alerts.
No campaign context for isolated alerts. Pending-seed alerts get a
provisional node (when not suppressed) AND log is_campaign_alert.
A persisted campaign decision NODE carries campaign_context_shown +
is_campaign_alert (decision-node persistence test passes — the holdout
is NOT a no-op). check_alert return type unchanged. Post-hoc wiring
verified (campaign context added after Step 5b, not during Step 3).
All existing tests pass.
```

---

## §9 — Manual / Live Validation (NOT Codex)

```powershell
# Activate
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"

# Start SOC diagnostic backend
cd "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
python .\demo.py --soc --diag-mode --diag-graph-name soc_graph --diag-backend-port 8001 --age-use-pool

# In a separate terminal:

# 1. Analyze an alert known to be in a campaign:
#    (use the diagnostic /api/soc/analyze or triage endpoint)
curl -s localhost:8001/api/soc/analyze -X POST \
  -H "Content-Type: application/json" \
  -d '{"alert_id": "ALT-JDOE-001"}' | python -m json.tool

# 2. Check situation_context.nodes for type="campaign":
#    Should see: campaign_id (always)
#    Should see: category, first_seen, member_count, age_days
#      (if materialized and cached — may be absent on cold cache)

# 3. Check evidence_chain for type="campaign_advisory":
#    Should see: advisory note about escalating the campaign

# 4. Analyze an isolated alert (not in any campaign):
#    Should see: NO campaign node, NO advisory note

# 5. M8 RE-VERIFICATION (MANDATORY):
#    Run the Phase 3B M8 measurement AFTER v6.0 is deployed.
#    Campaign hot-path must remain ≤ 5ms at p95.
#    The campaign context addition should add ~0ms (cache lookup).
#    If M8 regresses, the cache is not being used correctly.
#
#    Expected: M8 p95 ≈ 1.85ms (same as Phase 3B closeout)
#    Acceptable: M8 p95 ≤ 3ms (some overhead from context assembly)
#    FAIL: M8 p95 > 5ms (investigate — AGE read may have leaked in)
```

---

## §10 — v7.0: The Measurement Is the Asset

v6.0 + the holdout clock is the narrative win. The v7.0 tensor
change is a thesis-validation experiment, not a roadmap commitment.

### 10.1 Why the Measurement Matters More Than the Tensor

If the 90-day holdout shows "analysts escalated X% more when
shown learned campaign context," that is a MEASURED, CAUSAL
statement of the CGA thesis — and it's a narrative asset EVEN
IF the tensor never changes. It proves the system's compiled
intelligence MATTERS to human decisions.

### 10.2 Why the Tensor May Weaken Differentiation

v6.0's "we advise, you decide" (C-20) is the defensible moat.
v7.0's campaign-aware recommendation converts that into
"we auto-escalate campaigns" — which is the commoditized SIEM
behavior every competitor already has. The tensor change trades
a differentiated position for a common one.

### 10.3 Decision Gate (After ≥90 Days)

```
treatment = campaign alerts where campaign_context_shown == True
control   = campaign alerts where campaign_context_shown == False
lift      = escalation_rate(treatment) - escalation_rate(control)

lift significant & positive
  AND treatment escalation accuracy ≥ control accuracy
    → v7.0 CANDIDATE (not automatic)
    (accuracy check prevents the perverse outcome where
     showing context makes analysts over-escalate incorrectly)

lift ≈ 0 OR treatment accuracy < control accuracy
    → STOP (stay advisory — this is a
       finding, not a failure)
```

Even with positive lift, v7.0 requires ALL of:
- Circularity guard (train on banner-OFF cohort)
- Enrichment-loop math (N_recovery, DK gate, θ_min recheck)
- Honest scoring-not-compounding framing
- A customer specifically asking for auto-escalation

Without all four: stay advisory permanently. That's the stronger,
more differentiated, more honest position.

---

## §11 — Relationship to Other Documents

| Document | Relationship |
|---|---|
| soc_campaign_scorer_integration_v1_0.md | v6.0 = Option Z (context injection). v7.0 = Option X (tensor expansion, deferred). |
| campaign_phase3_async_v1_4.md | v6.0 depends on Phase 3B's cache infrastructure |
| campaign_phase3_gates_v1_0.md | M8 must remain ≤ 5ms after v6.0 |
| product_integrity_execution_strategy_v2_4.md | C-20, F-22 additions |
| soc_campaign_identity_architecture_v1_3.md | Phase 1 identity = the campaign_id v6.0 displays |

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 17, 2026 | Initial design. Based on discovery scan (Finding B: check_alert returns Optional[str], cache has IDs only, AGE has properties). Architecture: extend CampaignAsyncState to cache properties at materialization (zero AGE reads on hot path). Add campaign TraversalNode to soc_situation_pattern. Advisory evidence note. CampaignContext dataclass. Graceful degradation. C-20 + F-22 registry additions. Codex prompt with discovery verification + NON-NEGOTIABLES. ~0.5d effort. |
| v1.1 | June 17, 2026 | **Review pass — 6 fixes.** (1) CRITICAL: triage.py timing discovered — situation_analysis built at Step 3, campaign_id computed at Step 5b. Option W1 (parameter passing) doesn't work. Changed to post-hoc campaign context addition (append after both steps complete). (2) Demo moment sequence corrected for pending/cold-cache reality: Act 2 shows campaign_id only (pending), Act 3 shows full context (after materialization). (3) Test gates: M8 moved to manual validation (§9), added post-hoc timing test, added cold-cache/pending-path tests. (4) Codex prompt: 6 discovery steps (added timing verification + _DEFAULT_CAMPAIGN_ASYNC_STATE + situation_context attribute path). NON-NEGOTIABLES: added "POST-HOC — do NOT change Step 3 or Step 5b timing." (5) §7.1 files: soc_situation_pattern adds module-level function (no signature changes to existing builders). triage.py adds ~5 lines after Step 5b. (6) §9 manual validation: M8 re-verification added with expected/acceptable/fail thresholds. |
| v1.2 | June 17, 2026 | **Final review pass.** (1) §7.2 blast radius: "parameter passing" → "post-hoc wiring" (matches §3.3 architecture). (2) §6 integration test: timing verification reclassified from unit test to code review (can't unit-test line ordering). (3) §3.3 code: imports noted as file-top, not conditional-inline. (4) §8 discovery step 4: added analyze_situation return type check (grep situation.py) — Codex must use actual attribute name, not assumed `situation_context`. |
| v1.3 | June 17, 2026 | **Review consolidated (4 fixes + holdout + narrative).** (1) Fix 1 GATE: discovery step 0 added — check whether check_alert returns campaign_id or None for pending seeds. If None, pull provisional-pending read into v6.0 scope. (2) Fix 2: member_count set at materialization, increment only for post-materialization joins (no double-count). (3) Fix 3: source="graph_store_cached" (F-23 added). Advisory scales with evidence: <3 members → "emerging pattern", ≥3 → "active campaign." age_days<1 → "started today." (4) Holdout clock ships WITH v6.0: banner_suppressed() (sha256, 15%, deterministic) + is_campaign_alert + campaign_context_shown on every decision metadata. Cannot be retrofitted. (5) v7.0 reframed: measurement is the narrative asset, tensor expansion is a thesis-validation experiment gated on positive causal lift + circularity guard + customer ask + honest framing. Staying advisory (C-20) is the stronger position unless all 4 gates pass. (6) campaign_holdout.py + test file added to Codex create list. |
| v1.4 | June 17, 2026 | **Final executable pass.** (1) §0 Campaign Arc added: full Phase 1→1b-1→1b-2→Phase 3→3B→v6.0 context with graph state, test counts, and file map showing what v6.0 extends. (2) §4.2 + §6: source="graph_store" → "graph_store_cached" (consistent with F-23, was missed in display example + test gate). (3) §3.2: _add_campaign_context signature includes alert_id param (needed by holdout). Holdout logic integrated directly into the canonical function (not a separate wiring step). (4) §3.3: triage.py passes alert_id to _add_campaign_context. (5) §6: advisory scaling tests added (emerging < 3, active ≥ 3, age_days < 1 → "started today"). Holdout tests added (deterministic, ~15%, both arms log metadata, suppressed → no node). (6) §8 Codex prompt: _add_campaign_context signature updated with alert_id + holdout integration. (7) Version: 1.4, status: Roadmap-approved — pending implementation review. |
| v1.5 | June 17, 2026 | **A+ review — 5 corrections + 3 suggestions applied.** (1) CampaignContext explicitly NOT frozen (comment added — mutated by increment_member_count). (2) Holdout import moved to file top (not inside function body). (3) Discovery step 6 expanded: check if triage.py already has async state reference. Step 7 added: provisional-pending read is a SEPARATE METHOD (get_pending_campaign_id), NOT a change to check_alert's return behavior — prevents triage.py from writing pending IDs to decision nodes. (4) Holdout 15% power note: review after 30 days, increase to 25% if campaign volume is low. (5) Demo timing: 500ms pause between alert fires for controlled demo. (6) Holdout metadata serialization test added (verify to_dict() doesn't filter keys). (7) v7.0 decision gate: accuracy check added — treatment accuracy must ≥ control accuracy (prevents over-escalation false positives). |
| v1.6 | June 17, 2026 | **Execution-readiness pass — 4 Codex-blocking gaps closed.** (1) CRITICAL — holdout persistence fixed: flags now written to the DECISION NODE (the 90-day measurement contract), not only ephemeral situation_context.metadata. _add_campaign_context RETURNS {is_campaign_alert, campaign_context_shown}; triage Step 5d persists them at the campaign_id write site (~line 891). v1.5 routed them only to context.metadata → clock would have had zero queryable data (silent no-op). (2) Provisional-wiring reconciled: _add_campaign_context is now called ALWAYS (no `if _campaign_id` guard) and resolves materialized-OR-pending id internally via get_pending_campaign_id — so pending-seed alerts get the provisional banner AND get logged (v1.5's guard skipped them). (3) Discovery hardened for Codex: step 0 also confirms seed-key method + async_state attribute names; step 4 confirms SituationContext fields (.nodes/.evidence_chain/.metadata actual names); step 8 ADDED to locate the decision-node write site for holdout persistence. (4) RUN uses repo-configured runner (not literal pytest); typing.Any import noted at file top; EXIT adds decision-node persistence check. Files-changed + NON-NEGOTIABLES updated to match. |
| v1.7 | June 17, 2026 | **Final review — 3 fixes.** (1) Discovery step 7: added seed-key derivation note — get_pending_campaign_id needs rule_type/entity_key/category/bucket context that may only exist on CampaignMatcher, not CampaignAsyncState. Codex puts the method where derivation context lives, or triage.py pre-resolves using its existing matcher (line 884). (2) §7.2 blast radius: "3 modified + 1 new" → "3 modified + 3 new" (campaign_holdout.py + 2 test files). (3) §7.3 effort: "~3h (0.5d)" → "~4.5h (0.75d)" (holdout module + tests + decision-node persistence adds ~1.5h). |
| v1.7 | June 17, 2026 | **Final review — 3 fixes.** (1) Discovery step 7: seed-key derivation note. (2) §7.2: "3 modified + 1 new" → "3 modified + 3 new". (3) §7.3: "~3h" → "~4.5h". |
| v1.8 | June 17, 2026 | **Execution sequencing added per reviewer.** (1) Status: "Execution-ready" → "Approved — discovery pass before implementation." (2) §7.4 added: 4-prompt execution sequence (discovery → implementation → GPT-5.5 review → live validation). Risk table for each anchor if assumed wrong. (3) §8 split: §8.1 = Prompt 1 (read-only discovery, 8 anchors, zero edits, structured report format) + §8.2 = Prompt 2 (implementation, patched with discovery results — "do NOT run with assumed names"). |
