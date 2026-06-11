# SOC Campaign Identity Architecture Decision

**Date:** June 9, 2026
**Status:** APPROVED — design-authority review applied (June 9, 2026)
**Scope:** Campaign graph semantics, identity model, and integration with CGA architecture
**Triggered by:** Performance investigation + source review of `triage.py` campaign correlation
**Authority:** MAP v5.44 + DK Runtime Execution Plan v6.8

---

## Synopsis

SOC Campaign identity is redesigned from content-addressed (hash of
sorted alert-id set → O(N²) graph bloat, 24 Campaign nodes for 25
same-stream alerts) to stable identity tuples (hash of rule_type +
type-prefixed derived_entity_key + category + epoch-aligned time_bucket
→ 1 Campaign node, O(N) MEMBER_OF edges, monotonic membership).

**Core decisions (all design-authority approved):**
- Campaign = mutable incident, bounded by rule + entity + window
- Identity key: `SHA256("L1:" ‖ rule ‖ "\x00" ‖ entity ‖ "\x00" ‖
  category ‖ "\x00" ‖ bucket)` — stable as members grow, null-byte
  delimiters prevent field-boundary collision
- Entity key type-prefixed: `"user:U1"` vs `"asset:U1"` — prevents
  cross-type collision
- Minimum 2 correlated alerts before Campaign materialization
- MERGE-based writes with uniqueness constraint — race-safe under
  concurrent alert storms
- Seed property written SYNC at Alert creation; MERGE-materialization
  runs ASYNC
- CONTINUES edges link consecutive-bucket campaigns for multi-day
  incident continuity
- At v5.x: enrichment only (async, off the analyze hot path)
- At v6.0: scorer input via factor index 2 (sync, O(1) identity
  lookup — fast enough because identity keys eliminate traversal)

**Two-level architecture:** Level 1 (entity-scoped, O(1), ships now)
and Level 2 (cross-entity attack chains, O(N) traversal, v6.0 F6).
Level 1 uses node label `Campaign`, Level 2 uses `AttackChain`. Hash
inputs prefixed with level to prevent aliasing.

**4 architectural tensions documented with explicit trade-offs:**
entity scope (L1 now / L2 later), scorer input (enrichment now /
scorer v6.0), time bucket (epoch-aligned fixed windows), seed
persistence (graph property + async query).

**Not affected:** Conservation law (V counts decisions, not campaigns),
L5 proof chain (campaigns are not L5 nodes), C9B validity, centroid
learning (until v6.0 factor integration — integrity note added).

**4 invariants, 13 tests, ~3d implementation effort.**

---

## 0. SOC Domain Quick Reference (for review context)

The SOC copilot processes security alerts. Key parameters:

```
Categories (C=6):  credential_access, lateral_movement, data_exfiltration,
                   insider_behavioral, cloud_infrastructure, malware_execution
Actions (A=4):     escalate, investigate, suppress, monitor
                   (refer_to_analyst is a gate output, not a scorer action)
Factors (d=6):     asset_criticality, time_anomaly, threat_intel_enrichment,
                   behavioral_deviation, pattern_history, identity_trust
Centroid tensor:   μ[c, a, :] = 6 × 4 × 6 = 144 values
```

The analyze route (`POST /api/alert/analyze`) scores an alert using
the ProfileScorer and returns an action recommendation. The outcome
route (`POST /api/alert/outcome`) records analyst feedback and
updates the centroid tensor. Campaign correlation currently runs
synchronously inside the analyze route.

**Current campaign-related source files:**

| File | Role |
|---|---|
| `backend/app/domains/soc/campaigns.py` | `CampaignCorrelationEngine`, `CampaignRepository`, `CampaignMatcher`, `make_campaign_id()` |
| `backend/app/routers/triage.py` (lines 695-715) | Campaign correlation call site in analyze route |
| `backend/app/domains/soc/config.py` | `SOCDomainConfig.get_campaign_config()` — campaign rules |

---

## 1. Architectural Context

### 1.1 Where Campaigns Sit in the CGA Architecture

The CGA architecture has five layers (Architecture Philosophy v4.3, §ARCH-01):

```
Layer 5: Control Plane     — Conservation law α·q·V ≥ θ_min
Layer 4: Live Context Graph — PostgreSQL + AGE: alerts, decisions, entities, campaigns
Layer 3: Mathematical Engine — P(a|f,c) = softmax(−d(f, μ) / τ)
Layer 2: Compiled Profiles  — Centroid tensor μ[c, a, :] = 144 values (SOC)
Layer 1: Domain Ontology    — DomainConfig, factors, actions, categories
```

Campaigns are **Layer 4 entities** — graph nodes representing correlated
alert streams. They are consumed by:

- **Layer 3 scoring (v6.0 planned):** `ThreatIntelEnrichmentFactor`
  (factor index 2) currently queries ThreatIntel nodes, not Campaign
  nodes. At v6.0, campaign MEMBER_OF edges will feed factor scoring
  (see §5.4, Tension 2). At v5.x, campaigns are enrichment only.
- **Layer 5 control** via conservation's verified decision count V:
  campaign-correlated decisions contribute to V as decisions (not
  because they are campaign-correlated — V counts all verified
  decisions regardless of campaign membership)
- **Feature F6 (Attack Chain Correlation):** the primary commercial
  feature that campaigns enable — "LLM sees one alert; graph sees the
  campaign" (SOC Copilot Design v5.7, §30.3)

### 1.2 The Compounding Intelligence Claim

The product's moat equation (Innovation Note v6, Eq. 13) is:

```
Moat = n × t × f

where:
  n = graph coverage (semantic domains connected)
  t = time in operation (decisions and discoveries accumulated)
  f = cross-graph search frequency (discovery sweep rate)
```

Campaigns contribute to two of three terms:

- **t (time):** each campaign is an accumulated correlation that a
  stateless competitor cannot have. Microsoft Security Copilot queries
  Sentinel per-alert; it cannot see that 5 alerts from the same source
  in 10 minutes constitute a coordinated campaign. The campaign node
  IS the accumulated institutional knowledge.

- **n (coverage):** campaigns create cross-entity relationships
  (User → Campaign → Alert → Asset). These are exactly the
  cross-domain attention surfaces that drive discovery scaling
  D(n) ∝ n^2.11 (Eq. 10).

A campaign implementation that creates 24 overlapping nodes for 25
same-stream alerts does not compound — it accumulates noise.
A campaign implementation that creates 1 evolving node for the same
25 alerts compounds correctly.

### 1.3 The Performance Context

The performance investigation (v6.8 §Performance Root Cause Analysis)
found that the analyze route makes 13+ graph operations per call.
Only 5 are instrumented; the other 8 (including campaign correlation)
account for 88% of total analyze time. Key numbers:

```
At 25 outcomes:   analyze avg = 3,688ms, instrumented = 706ms (12%)
At 250 outcomes:  analyze avg = 25,602ms, peak = 49,915ms
Growth rate:      ~170ms per additional outcome
Scorer itself:    0.25ms (sub-millisecond)
```

Campaign correlation flow in triage.py (lines 695-715):

```python
# Step 5b: Campaign correlation (F6) — currently SYNCHRONOUS
from app.domains.soc.campaigns import (
    CampaignCorrelationEngine, CampaignRepository, CampaignMatcher,
)
_camp_config = SOCDomainConfig.get_campaign_config()
_camp_engine = CampaignCorrelationEngine(_camp_config)
_camp_repo = CampaignRepository(neo4j_client)          # creates repo per request
_camp_matcher = CampaignMatcher(
    neo4j_client, _camp_config, _camp_engine, _camp_repo
)
_campaign_id = await _camp_matcher.check_alert(alert_id)  # ← graph queries here
if _campaign_id:
    await neo4j_client.run_query(                          # ← graph write here
        f"MATCH (d:Decision ...) SET d.campaign_id = ..."
    )
```

This creates a new `CampaignRepository` and `CampaignMatcher` per
request, runs graph queries to find/create campaigns, and writes
results synchronously before the analyze response returns.

### 1.4 Current Campaign Graph Schema

```
(Campaign {
    campaign_id: str,        # currently: hash of sorted alert-id set
    rule_type: str,          # temporal | technique | entity
    created_at: int,         # epoch ms
    alert_count: int,        # member count
    category: str,           # optional — not always set
    source_entity_id: str    # optional — used by _find_matching_campaign
})

(Alert)-[:MEMBER_OF]->(Campaign)
```

The `MEMBER_OF` edges connect alerts to their campaign. When a new
Campaign is created (because the alert set changed), ALL historical
members get new `MEMBER_OF` edges to the new Campaign. This is the
O(N²) edge growth pattern.

---

## 2. The Problem: Current Campaign Identity Is Unstable

### 2.1 Current Implementation

```python
# Current: make_campaign_id() hashes the sorted alert-id set
campaign_id = hash(sorted([a1, a2, a3, ...]))
```

When alert a3 arrives and correlates with [a1, a2]:
- The set changes from {a1, a2} to {a1, a2, a3}
- `campaign_id` changes
- A NEW Campaign node is created
- The old Campaign node with {a1, a2} remains in the graph

After 25 same-stream alerts, the graph contains up to 24 Campaign
nodes, each representing a historical snapshot of the correlation set.

### 2.2 The _find_matching_campaign Problem

```python
# Current: depends on Alert.source_entity_id
_find_matching_campaign(source_entity_id=...)
```

The diagnostic/live alert shape has `user_id`, `asset_id`,
`source_location` — but often no `source_entity_id`. When
`source_entity_id` is absent, `_find_matching_campaign()` cannot
find the existing campaign. Result: a new Campaign is always created.

### 2.3 Graph Shape Consequence

After 25 same-stream credential_access alerts from user U1:

**Current (broken):**
```
Campaign_v1 ←MEMBER_OF— Alert_1, Alert_2
Campaign_v2 ←MEMBER_OF— Alert_1, Alert_2, Alert_3
Campaign_v3 ←MEMBER_OF— Alert_1, Alert_2, Alert_3, Alert_4
...
Campaign_v24 ←MEMBER_OF— Alert_1 ... Alert_25
```
24 Campaign nodes. O(N²) MEMBER_OF edges. Growing graph mass.

**Intended:**
```
Campaign_001 ←MEMBER_OF— Alert_1, Alert_2, ..., Alert_25
```
1 Campaign node. O(N) MEMBER_OF edges. Stable identity.

---

## 3. Decision: Campaign Semantics

### 3.1 Verdict

```
CAMPAIGN_SEMANTICS: Mutable incident, bounded by rule + entity + window
```

A Campaign represents a **single evolving security incident** — a
coordinated stream of related alerts sharing a common entity, attack
category, and time window. As new alerts correlate, they join the
existing Campaign. The Campaign's identity is stable; its membership
grows.

This matches SOC operational reality: analysts think in incidents,
not in correlation snapshots. "Investigate campaign CAMP-2026-0042"
is actionable. "Investigate 24 overlapping correlation snapshots"
is not.

### 3.2 Formal Definition

**Definition 1 (Campaign Identity).** A campaign C is identified by
the tuple:

```
C.identity = (rule_type, derived_entity_key, category, time_bucket)
```

where:

- `rule_type ∈ {temporal, technique, entity, composite}` — which
  correlation rule detected the relationship
- `derived_entity_key` — the entity connecting the alerts (§3.3)
- `category` — the SOC alert category (credential_access, etc.)
- `time_bucket` — a configurable temporal window (e.g., 24h rolling
  or calendar day)

**Definition 2 (Campaign Identity Key).** The stable campaign
identifier is:

```
campaign_id = SHA256("L1:" ‖ rule_type ‖ "\x00" ‖ derived_entity_key ‖ "\x00" ‖ category ‖ "\x00" ‖ str(time_bucket))
```

The `L1:` prefix ensures Level 1 campaign IDs cannot alias with
Level 2 (AttackChain) IDs at v6.0 (see §3A Tension 1). The `\x00`
null byte delimiter prevents field-boundary collisions: without it,
`("temporal", "user:U1", "cred")` and `("temporal", "user:U", "1cred")`
hash identically. Null bytes cannot appear in any field value.

This hash is deterministic and stable: adding alert a26 to a stream
that already has [a1...a25] does not change the campaign_id because
the identity depends on the entity/rule/category/window, not on the
alert set.

**Definition 3 (Campaign Membership).** An alert A belongs to
campaign C if:

```
A.derived_entity_key = C.derived_entity_key
∧ resolve_category(A.alert_type) = C.category
∧ A.timestamp ∈ C.time_bucket
∧ ∃ rule ∈ C.rule_type : rule.matches(A)
```

Membership is monotonically increasing within a time bucket:
once an alert joins a campaign, it does not leave.

### 3.3 Source Entity Fallback

**Definition 4 (Derived Entity Key).** Given an alert A and its
security context ctx, the derived entity key is TYPE-PREFIXED to
prevent cross-type collision (e.g., user_id="12345" vs
asset_id="12345" must produce different keys):

```
derived_entity_key(A, ctx) =
    "entity:" + A.source_entity_id   if present
    else "user:" + ctx.user_id       if present
    else "user:" + A.user_id         if present
    else "asset:" + ctx.asset_id     if present
    else "asset:" + A.asset_id       if present
    else "loc:" + A.source_location  if present
    else ⊥  (campaign creation skipped)
```

**Canonicalization assumption:** Correlation quality depends on
consistent identifier population per deployment. If the same real
entity is keyed differently across alerts (one alert has
`source_entity_id`, another has only `user_id`), they produce
different keys → separate campaigns for the same entity. This is a
known limitation at v5.x.

**Known cross-prefix limitation:** If `source_entity_id` IS a user
ID (e.g., the SIEM assigns `source_entity_id = "U1"` which is also
the `user_id`), then `"entity:U1"` and `"user:U1"` are different
keys. This is intentional: `source_entity_id` is the SIEM's canonical
identity, which may differ from the graph's `user_id`. Treating them
as the same key would break deployments where source_entity_id
represents a composite identity (e.g., `"user:U1+asset:A3"`). The
v6.0 entity-resolution path (below) resolves this by canonicalizing
before keying.

**Mitigation (v6.0):** If an entity-resolution map exists (Entity
Resolution, ci-platform §entity_resolution.py), resolve to the
canonical SIEM entity before keying. At v5.x, the fallback chain is
acceptable because most SIEM deployments populate identifiers
consistently within a single data source.

When `derived_entity_key = ⊥`, the alert cannot be meaningfully
correlated. Campaign creation is skipped — the alert stands alone.

The fallback order reflects semantic strength:
- `source_entity_id` is canonical (SIEM-assigned entity identity)
- `user_id` is the most common available identifier
- `asset_id` captures device-based attacks
- `source_location` captures IP-based attacks
- `⊥` prevents meaningless grouping

### 3.4 Rejected Options

| Option | Description | Why rejected |
|---|---|---|
| **D: Immutable snapshots** | Keep current behavior — Campaign = frozen correlation set | Creates 24 Campaign nodes for 25 same-stream alerts. Graph bloat, confusing UI, O(N²) edge growth. Contradicts "the system detected a campaign" demo narrative. |
| **E: Defer campaign entirely** | Remove campaign from analyze. Implement later. | Campaign correlation is shipped (F6, Feature Briefing §2.9). Regression, not deferral. |
| **A: Fix fallback only** | Add derived_entity_key fallback but keep alert-set identity | Fixes `_find_matching_campaign` crash but same O(N²) proliferation returns at 100 alerts. |
| **C: Reuse by graph traversal** | Query for "compatible" campaigns via MEMBER_OF edges | Adds more O(N) queries to an already slow route. Symptom, not root cause. |

### 3.5 Competitive Context

Microsoft Security Copilot processes alerts individually via Sentinel
queries. It has no persistent campaign entity — each analysis is
stateless. The system cannot tell an analyst "this is the 5th alert
in campaign CAMP-2026-0042."

The "Four Clocks" framework (March 2026) identified campaign detection
as one of four dimensions where compounding intelligence beats
stateless AI. A SOC with 10,000 processed alerts has institutional
memory about which entities are repeatedly targeted, which patterns
recur, and which time windows see coordinated activity. Security
Copilot starts from zero on every query.

For this competitive advantage to hold, the campaign graph must be
clean (1 Campaign per incident, not 24 snapshots) and campaign
correlation must not degrade the system's response time below the
competitor's sub-second baseline.

### 3.6 Correlation Seed Mechanism (Invariant 2 Implementation)

The minimum-2-alert requirement uses a lightweight seed property.
**Race safety is critical:** in an alert storm (the exact condition
campaigns exist to catch), multiple alerts may discover the seed
concurrently. All mutation operations use MERGE (idempotent), not
CREATE.

**Prerequisites:**
- Uniqueness constraint on `Campaign.campaign_id` in the graph schema
- Seed property `campaign_seed_key` written SYNCHRONOUSLY at Alert
  node creation (free property set on an already-created node)
- Campaign materialization and MEMBER_OF edges use MERGE (idempotent)

```
Alert A1 arrives. derived_entity_key = "user:U1", category = credential_access.
  → No existing Campaign with matching identity key.
  → SYNC: SET A1.campaign_seed_key = SHA256(identity_tuple)
  → No Campaign node created yet.

Alert A2 arrives (possibly concurrent with A3). Same identity key.
  → Query: MATCH (a:Alert {campaign_seed_key: <key>}) WHERE a ≠ A2
  → Found A1 → two alerts share the identity tuple.
  → MERGE (c:Campaign {campaign_id: <key>})    ← idempotent, race-safe
    ON CREATE SET c.rule_type = ..., c.category = ..., c.created_at = ...
  → MERGE (A1)-[:MEMBER_OF]->(c)               ← idempotent
  → MERGE (A2)-[:MEMBER_OF]->(c)               ← idempotent
  → REMOVE A1.campaign_seed_key                 ← only after materialization

Alert A3 arrives (concurrent with A2). Same identity key.
  → MERGE finds existing Campaign (or creates if A3 runs first)
  → MERGE (A3)-[:MEMBER_OF]->(c)               ← idempotent
  → SET c.alert_count = <count MEMBER_OF edges> ← derived, not incremented
```

**Why MERGE, not CREATE:** If A2 and A3 both find A1's seed
concurrently and both run CREATE, duplicate Campaign nodes appear —
breaking Invariant 1. MERGE is idempotent: both tasks converge on
one node. The uniqueness constraint on `Campaign.campaign_id` is a
backstop.

**Seed write timing:** Written SYNCHRONOUSLY at Alert creation (not
in the async campaign task). If async, A2's task can run before A1's
seed exists → two seeds, no campaign until A3. Sync seed + async
MERGE-materialize closes both the race and the ordering gap.

**Orphaned seed cleanup:** If the backend crashes between
MERGE(Campaign) and REMOVE(campaign_seed_key), the seed persists.
Next alert finds both seed AND Campaign → harmless (MERGE is
idempotent), but the orphaned property accumulates. Mitigation:
periodic background task removes `campaign_seed_key` properties from
Alert nodes that already have a `MEMBER_OF` edge to a Campaign. Run
frequency: daily or on backend startup. Not blocking for v5.x —
orphaned seeds are inert properties, not broken state.

### 3.7 Migration of Existing Campaign Nodes

Existing Campaign nodes (from prior diagnostic runs or demos) are
on contaminated diagnostic graphs (soc_graph_diag_f3 through f8).
The C9B proof graph (`soc_graph_c9b`) and any production graph start
fresh. No migration is needed — new campaigns use the new identity
model from creation.

---

## 3A. Architectural Tensions Between Correctness and Performance

This section names the specific points where Goals 1 (architecturally
correct) and 2 (highly optimized) conflict, and documents the
resolution for each.

### Tension 1: Entity-Scoped vs Cross-Entity Campaigns

**Goal 1 says:** A real attack campaign (APT, ransomware, supply chain)
targets MULTIPLE entities. The Stryker/Handala case (Innovation Note
v6, §Innovation 7) involved 199,000 devices across 4 graph domains.
F6 (Attack Chain Correlation) is specifically about "linking alerts
via graph entities into multi-stage ATT&CK campaigns." Entity
separation (Invariant 4) creates 5 separate "campaigns" for 1 real
multi-entity campaign. That's architecturally incomplete.

**Goal 2 says:** Cross-entity campaign detection requires graph
traversal across entities — matching alerts by shared C2
infrastructure, MITRE technique, or temporal proximity. This is
expensive and grows with graph size.

**Resolution: Two-level campaign architecture.**

```
Level 1 (Entity Campaign):
  Scope:     Single derived_entity_key
  Identity:  hash(rule_type ‖ entity ‖ category ‖ time_bucket)
  Cost:      O(1) lookup by identity key — cheap
  Timing:    Async but fast — can be near-real-time
  Purpose:   "5 alerts from user U1 are related"

Level 2 (Attack Chain Campaign):
  Scope:     Cross-entity, cross-category
  Identity:  hash(technique ‖ C2_indicator ‖ time_window)
  Cost:      O(N) graph traversal — expensive
  Timing:    Batch/periodic (every 5 min or on-demand)
  Purpose:   "Users U1, U2, U3 are all targeted by the same APT"
  Ships:     v6.0 (gated by F6)
```

Level 1 is what this document specifies. Level 2 is the F6 vision
and requires graph attention mechanisms (Eq. 6,
CrossAttention(G_i, G_j)) that are architecturally different from
per-alert correlation. Level 1 campaigns become INPUTS to Level 2
detection — Level 2 can query "which Level 1 campaigns share
indicators?" without repeating per-alert correlation.

**Label separation:** Level 1 uses node label `Campaign`. Level 2
uses node label `AttackChain` (v6.0). The identity hash inputs are
prefixed with the level (`L1:` vs `L2:`) so the two identity spaces
cannot alias.

**Demo/blog scoping (from design-authority review):** The "graph
sees the campaign" / F6 attack-chain story is a Level 2 claim. At
v5.x, only Level 1 (single-entity incident grouping) ships. Demo
hero docs and blog copy must scope the campaign narrative to
single-entity incidents until v6.0, or use clearly-marked pre-seeded
Level 2 examples. Same label-what's-shipped discipline as the rest
of the doc set.

**Trade-off accepted:** Level 1 entity-scoped campaigns are
architecturally incomplete for multi-entity attack chains. This is
acceptable at v5.x because Level 2 (F6) is a v6.0 feature. Level 1
provides immediate value (single-entity incident grouping) without
the O(N) traversal cost. Level 2 adds cross-entity detection later
without redesigning Level 1.

### Tension 2: Enrichment-Only vs Scorer Input

**Goal 1 says:** If campaigns affect factor scoring (v6.0 plan),
campaign membership becomes decision-critical. The scorer's output
depends on whether an alert belongs to a campaign. The conservation
law's quality metric q(t) then depends on campaign-influenced
scoring. Campaign correlation cannot be async if the scorer needs it
before computing P(a|f,c).

**Goal 2 says:** Campaign correlation at ~500ms synchronous is
unacceptable. Moving it async removes the latency. But async means
the scorer can't use campaign data.

**Resolution: Phase-gated transition.**

```
v5.x (NOW):
  Campaign = enrichment only
  Scorer does NOT use campaign data
  Campaign correlation = async (post-response)
  Conservation law unaffected

v6.0 (F6):
  Campaign = scorer input via ThreatIntelEnrichmentFactor
  Factor index 2 reads Campaign MEMBER_OF edges
  Campaign correlation = synchronous BUT optimized:
    - Level 1 identity key lookup = O(1), <10ms
    - MEMBER_OF edge creation = single Cypher, ~80ms
    - Total campaign sync path: ~90ms (acceptable)
  Conservation law: campaign-influenced scoring monitored
```

The key insight: with stable identity keys, Level 1 campaign
correlation at v6.0 is an O(1) hash lookup + MERGE, not an O(N)
graph traversal. The current ~500ms cost is because `check_alert()`
does expensive graph traversal (`_find_matching_campaign` scans
Campaign nodes). The identity-key redesign makes sync campaign
correlation fast enough for scorer input at v6.0.

**Trade-off accepted:** At v5.x, campaign data is not available to
the scorer. ThreatIntelEnrichmentFactor uses ThreatIntel nodes only.
This is a feature gap, not a correctness gap — the scorer works
correctly without campaign data, it just doesn't benefit from campaign
correlation in factor scoring yet.

**v6.0 integrity requirement:** Once ThreatIntelEnrichmentFactor
reads Campaign MEMBER_OF edges, a campaign-correlation bug pollutes
the factor vector → flows into outcomes → pollutes centroid learning.
This is the same dual-representation / ghost-data hazard class the
platform already fought on the decision write path. The v6.0 sync
campaign path must inherit the same integrity discipline as the
decision write path: validated writes, no double-count, and
conservation monitoring of campaign-influenced scoring distributions.

### Tension 3: Time Bucket Semantics

**Goal 1 says:** A rolling window (e.g., "last 24h from now") is
the most correct model — it captures temporal proximity without
artificial boundaries. But rolling windows mean the time_bucket
component of the identity key changes every second, violating
identity stability.

**Goal 2 says:** Calendar day (midnight-to-midnight) is simple,
deterministic, and produces stable identity keys. But two alerts
2 minutes apart at midnight land in different campaigns.

**Resolution: Epoch-aligned fixed windows with configurable width.**

```
time_bucket = floor(alert_timestamp / window_width)

Type: int64 (NOT string — arithmetic comparison in CONTINUES edge
  query requires integer: c_prev.time_bucket = c_new.time_bucket - 1)

Default window_width: 86400 (24 hours, in seconds)
Configurable per deployment via DomainConfig

Example: window_width = 86400
  Alert at epoch 1718000000 → bucket 19884
  Alert at epoch 1718086399 → bucket 19884 (same day)
  Alert at epoch 1718086400 → bucket 19885 (next day)
```

This is deterministic (same alert always maps to same bucket),
stable (bucket doesn't slide), and configurable (SOC with 24/7
operations might use 8h shift-aligned windows). The midnight
boundary is a known compromise — documented for operators.

**Trade-off accepted:** Boundary artifacts exist. Two alerts 1
second apart at a bucket boundary land in different campaigns. This
is acceptable because: (a) Level 2 campaign detection (v6.0) uses
graph traversal that crosses time boundaries; (b) most attack
campaigns span hours, not seconds; (c) operators can tune
window_width to match their operational rhythm.

### Tension 4: Seed Persistence vs Query Cost

**Goal 1 says:** The correlation seed (first alert with a given
identity key, before a Campaign is materialized) must survive
backend restarts. If the seed is only in memory and the backend
restarts between alert A1 and A2, the campaign is lost.

**Goal 2 says:** Querying the graph for seed alerts (MATCH Alert
WHERE campaign_seed_key = X) adds another graph operation per alert.

**Resolution: Graph property + async background query.**

The `campaign_seed_key` property is written to the Alert node during
seeding (which already creates the Alert node — no additional graph
write). The seed query (MATCH Alert WHERE campaign_seed_key = X) is
performed as part of the async campaign correlation task, not on
the synchronous analyze path. If the backend restarts, the seed
property persists in the graph and the next alert can still find it.

```
Cost at v5.x (async):  0ms on analyze path (seed query is async)
Cost at v6.0 (sync):   ~80ms (one indexed point lookup)
```

**Trade-off accepted:** Between backend restart and the next
matching alert's async campaign task, the seed exists in the graph
but is not in any memory cache. The async task will find it. No
campaign is lost.

### Summary of Tensions

| Tension | Goal 1 (correct) | Goal 2 (fast) | Resolution |
|---|---|---|---|
| Entity scope | Cross-entity campaigns needed | Cross-entity traversal is O(N) | Two-level: L1 entity-scoped (now), L2 cross-entity (v6.0) |
| Scorer input | Campaign data should inform scoring | Sync campaign correlation too slow | Phase-gated: enrichment at v5.x, scorer input at v6.0 (fast with identity keys) |
| Time bucket | Rolling window most correct | Rolling window breaks identity stability | Epoch-aligned fixed windows, configurable width |
| Seed persistence | Must survive restarts | Graph query adds cost | Graph property (free write) + async query (off hot path) |

---

## 4. Graph Invariants

### 4.1 Campaign Node Invariants

**Invariant 1 (Uniqueness).** For any given
`(rule_type, derived_entity_key, category, time_bucket)` tuple,
at most one Campaign node exists in the graph.

```
∀ C1, C2 : C1.identity = C2.identity → C1 = C2
```

**Invariant 2 (Minimum Correlation).** A Campaign node is created
only when at least 2 alerts share the same identity tuple. The first
matching alert is stored as a correlation seed; the Campaign node
is materialized when the second alert matches.

```
|{A : A ∈ C}| ≥ 2  for every Campaign node C in the graph
```

**Invariant 3 (Monotonic Membership).** Within a time bucket,
campaign membership only grows. Alerts are never removed from a
Campaign.

```
A ∈ C(t) → A ∈ C(t') for all t' > t within the same time_bucket
```

**Invariant 4 (Entity Separation — Level 1 only).** Alerts with
different `derived_entity_key` values never share a Level 1 Campaign,
even if they share category and time_bucket. Cross-entity correlation
is Level 2 (v6.0, F6).

```
A1.derived_entity_key ≠ A2.derived_entity_key → ¬∃ C_L1 : A1 ∈ C_L1 ∧ A2 ∈ C_L1
```

Note: Level 2 (Attack Chain) campaigns CAN span entities. Level 1
campaigns become inputs to Level 2 detection. See §3A Tension 1.

### 4.2 Expected Graph Shapes

| Scenario | Expected shape |
|---|---|
| 25 same-stream alerts (same user, category, window) | 1 Campaign, 25 MEMBER_OF edges |
| 25 alerts from 5 different users, same category | Up to 5 Campaigns, ~5 members each |
| 25 alerts across 3 categories from same user | Up to 3 Campaigns (one per category) |
| 25 unrelated alerts | 0 Campaign nodes (no 2 alerts share identity) |

### 4.3 Boundary Behavior

**Time bucket boundary:** A campaign in window W1 and a new alert in
window W2 (e.g., next calendar day) create a new Campaign node. The
epoch-bucket model is deterministic and race-free — this is worth
keeping (Tension 3).

**CONTINUES edge for multi-day incidents:** To preserve the "one
evolving incident" story across day boundaries without abandoning
the deterministic bucket model, consecutive-bucket campaigns sharing
`(rule_type, derived_entity_key, category)` are linked:

```cypher
MERGE (c_new:Campaign {campaign_id: <new_bucket_key>})
WITH c_new
MATCH (c_prev:Campaign)
  WHERE c_prev.rule_type = c_new.rule_type
    AND c_prev.derived_entity_key = c_new.derived_entity_key
    AND c_prev.category = c_new.category
    AND c_prev.time_bucket = c_new.time_bucket - 1
MERGE (c_new)-[:CONTINUES]->(c_prev)
```

This gives:
- **Storage:** per-bucket (deterministic, race-free)
- **Logical incident:** reconstructable as one chain via CONTINUES
  for UI display and for Level 2 input
- **Query:** "show me the full incident" = follow CONTINUES chain

```
Day 1:  Campaign{bucket=19884} ←MEMBER_OF— A1, A2, A3
                    ↑
                [:CONTINUES]
                    |
Day 2:  Campaign{bucket=19885} ←MEMBER_OF— A4, A5, A6
                    ↑
                [:CONTINUES]
                    |
Day 3:  Campaign{bucket=19886} ←MEMBER_OF— A7, A8
```

**Category mismatch:** Same entity, different category → different
Campaign. A user generating both credential_access and
lateral_movement alerts produces two separate campaigns. This
preserves category-level analysis integrity.

**Late-arriving alerts:** An alert with a timestamp in a past bucket
MERGEs into the correct historical campaign deterministically. The
identity key is computed from the alert's own timestamp, not from
"now." This is well-defined by the epoch-aligned model.

---

## 5. Integration with CGA Framework

### 5.1 Relationship to Conservation Law

The conservation law α(t)·q(t)·V(t) ≥ θ_min (Eq. 7, CGA arxiv v7.2)
governs the learning signal. Campaign membership does NOT affect V
directly — V counts verified decisions, not campaign-correlated
decisions. Campaign correlation is enrichment metadata on Decision
nodes, not a separate verification pathway.

However, campaigns indirectly affect the conservation law through the
`ThreatIntelEnrichmentFactor` (factor index 2). Campaign-correlated
alerts produce higher threat_intel_enrichment scores, which may shift
the scorer's action distribution. The conservation law monitors
whether this distribution shift degrades learning signal quality.

### 5.2 Relationship to L5 Persistence

Campaign nodes are NOT L5 nodes. The L5 node types are:
- L5Centroid (centroid state)
- L5DKWeight (DK estimation state)
- L5ConservationState (conservation state)

Campaigns are standard graph entities — they have MEMBER_OF edges to
Alert nodes but no L5 lifecycle (no SHAPED_BY, no TRIGGERED_BY). The
`_l5_upsert_current()` method does not apply to Campaign nodes.

Campaign nodes may be freely created and linked without affecting
the L5 proof chain. C9B proof validity is independent of campaign
semantics.

### 5.3 Relationship to the Moat

The moat equation Moat = n × t × f gains from campaigns in two ways:

1. **Temporal accumulation (t):** Each campaign is a persisted
   correlation that embodies institutional memory. A customer who has
   processed 10,000 alerts over 6 months has campaigns that encode
   which entities are repeatedly targeted, which attack patterns
   recur, and which time windows see coordinated activity. A
   competitor starting fresh has none of this.

2. **Graph coverage (n):** Campaign nodes create entity bridges:
   `User → Campaign → Alert → Asset`. These bridges are the
   cross-domain surfaces for Level 2 discovery attention
   (Eq. 6: CrossAttention(G_i, G_j)). More campaigns = more
   attention surfaces = more discovery potential = larger n.

**The scaling implication:** With stable campaign identity, each new
alert in an existing stream adds 1 MEMBER_OF edge to an existing
Campaign. With unstable identity, each new alert creates a new
Campaign + N MEMBER_OF edges (copying historical membership).
Stable identity scales as O(N). Unstable scales as O(N²).

At 10,000 alerts/month in related streams, stable identity produces
~10,000 MEMBER_OF edges (one per alert). Unstable identity produces
up to N×(N-1)/2 ≈ 50M edges (each new Campaign copies all historical
members). The graph becomes unusable at the unstable rate.

### 5.4 Relationship to Factor Scoring

`ThreatIntelEnrichmentFactor` (SOC Copilot Design v5.7, §5.3)
currently computes campaign association via:

```cypher
MATCH (ti:ThreatIntel)-[:ASSOCIATED_WITH]->(a:Alert)
WHERE a.timestamp > datetime() - duration({days: 30})
RETURN ti AS threat_intel, count(a) AS alert_count
-- NOTE: variable was previously named "campaign" which is misleading.
-- This queries ThreatIntel nodes, NOT Campaign nodes.
```

This query is independent of the Campaign identity model — it queries
ThreatIntel nodes, not Campaign nodes. Campaign nodes are a separate
correlation mechanism (F6) that feeds the UI and referral rules, not
the factor vector directly.

Future integration (v6.0+): factor index 2 may also consider Campaign
MEMBER_OF edges for enrichment scoring. This would connect campaign
identity directly to the scoring loop. Stable identity is a
prerequisite for this integration.

---

## 6. Decision: Campaign Correlation Is Enrichment, Not Decision-Critical

### 6.1 Synchronous vs Asynchronous

Campaign correlation is **enrichment only**. It is NOT required for:
- The scorer's action recommendation
- The confidence computation
- The audit chain
- The C9B proof

Campaign correlation MAY be performed:
- Asynchronously after the analyze response returns
- Via `asyncio.create_task()` (fire-and-forget, like Sentinel write-back)
- Written to the Decision node as `d.campaign_id` post-response

**Async error handling:** `asyncio.create_task()` silently swallows
exceptions. If the campaign MERGE fails (AGE down, constraint
violation), there is no retry and no error log unless the task adds
`task.add_done_callback()` with an error logger. Implementation must
include a done-callback that logs campaign correlation failures at
WARNING level. Campaign correlation can silently fail without any
signal otherwise — acceptable for enrichment, but the operator must
be able to detect systematic failures via logs.

### 6.2 Performance Implication

Moving campaign correlation off the synchronous analyze path removes
~500ms+ from the analyze route. Combined with the other uninstrumented
operations identified in the performance root cause analysis, this
contributes to reducing analyze latency from 25s (at 250 decisions)
toward the <1s target.

### 6.3 UI Implication

The UI must handle a "campaign pending" state: the analyze response
may return without `campaign_id`. On subsequent load or polling, the
`campaign_id` appears on the Decision node. This is acceptable for
Tab 3 (Campaign Detail Panel) — the panel already loads asynchronously.

### 6.4 Decision.campaign_id Consumer Audit

**Architectural question (from review):** `campaign_id` is written to
the Decision node. If any code reads `Decision.campaign_id` for
something beyond display, campaign correlation is not purely enrichment.

**Current consumers of `Decision.campaign_id` (triage.py source review):**

| Consumer | What it does | Enrichment? |
|---|---|---|
| Analyze response JSON | Returns `campaign_id` in response body | Yes — display |
| Decision node property | Stored as `d.campaign_id` | Yes — metadata |
| Tab 3 Campaign Detail Panel (UI) | Groups decisions by campaign_id | Yes — display |

**No current consumer uses `campaign_id` for:**
- Scoring (factor vector computation)
- Conservation law (α, q, V computation)
- Audit chain (hash chain is decision-level, not campaign-level)
- Referral rules (R1-R7 use sequence_count, cross_category_count)
- L5 persistence (centroid, DK, conservation)

**Verdict:** `Decision.campaign_id` is currently read-only for display.
"Enrichment only" is accurate at v5.x. If a future feature (e.g.,
per-campaign accuracy panel, campaign-level conservation) reads
`campaign_id` for computation, that feature inherits the v6.0
integrity requirement from Tension 2 (P2-B).

---

## 7. Implementation Direction

### 7.1 Changes Required

| Component | Change | Effort |
|---|---|---|
| `make_campaign_id()` | Hash `"L1:" ‖ rule_type ‖ derived_entity ‖ category ‖ time_bucket` instead of sorted alert set | 0.5d |
| `derived_entity_key()` | New utility function with type-prefixed fallback chain (`"user:" + id`, etc.) | 15 min |
| `_find_matching_campaign()` | Match on identity tuple, not source_entity_id | 0.5d |
| `check_alert()` | MERGE on identity-keyed Campaign; MERGE MEMBER_OF edges; skip creation if single alert | 0.5d |
| Analyze route (triage.py:707) | Move campaign correlation to `asyncio.create_task()`. Seed write stays sync. | 15 min |
| Graph schema | Uniqueness constraint on `Campaign.campaign_id` + index on `Alert.campaign_seed_key` | 15 min |
| CONTINUES edge | MERGE consecutive-bucket campaigns with same (rule, entity, category) | 0.5d |
| Tests | 13 tests (§7.2) | 0.5d |

### 7.2 Required Tests

| # | Test | Invariant |
|---|---|---|
| 1 | 25 same-stream alerts → 1 Campaign, 25 MEMBER_OF | Uniqueness + Monotonic |
| 2 | 5 users × 5 alerts → 5 Campaigns | Entity Separation |
| 3 | 3 categories × same user → 3 Campaigns | Category Separation |
| 4 | campaign_id stable as members grow from 5 → 15 | Identity Stability |
| 5 | No source_entity_id → user_id fallback | Fallback Chain |
| 6 | No entity identifiers → no Campaign created | ⊥ Handling |
| 7 | Analyze returns before campaign correlation | Async Enrichment |
| 8 | Decision node has campaign_id after async write | Post-Response Write |
| 9 | Single alert → no Campaign node (seed only) | Minimum Correlation |
| 10 | Second matching alert → Campaign with both members | Materialization |
| 11 | Concurrent same-identity alerts → exactly 1 Campaign | Race Safety (P1-B) |
| 12 | Cross-type IDs (user:"X" vs asset:"X") → 2 Campaigns | Type-Prefix (P1-A) |
| 13 | Late-arriving alert (past timestamp) → correct historical Campaign | Epoch Determinism |

---

## 8. Design Authority Review — Answers (June 9, 2026)

| # | Question | Answer |
|---|---|---|
| Q1 | Mutable incident consistent with CGA lifecycle? | **Yes.** Layer-4 mutable entity, analogous to decision accumulation — not the immutable L5 audit nodes. |
| Q2 | derived_entity_key precedence correct? | **Yes with type-prefix.** Order is reasonable. Keying needs `"user:" + id` format (P1-A). Canonicalization via entity-resolution at v6.0. |
| Q3 | Any sync consumer needs campaign_id? | **No.** Audit, referral, conservation are all independent. Async enrichment is safe. |
| Q4 | Minimum correlation = 2 correct? | **Yes.** Singletons are noise. Seed mechanism is right — materialization must be race-safe (P1-B). |
| Q5 | time_bucket granularity? | **Configurable width, epoch-aligned.** No conservation constraint. Add CONTINUES edge (P2-A) for multi-day incident continuity. |
| Q6 | Any planned L5 lifecycle for campaigns? | **No, and keep it that way.** Campaigns are correlation metadata. Only coupling is v6.0 factor-scoring path (P2-B). C9B proof stays independent. |

---

## 9. Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 9, 2026 | Initial decision document. Campaign identity architecture. |
| v1.1 | June 9, 2026 | Design-authority review applied. P1-A: type-prefixed derived_entity_key. P1-B: MERGE-based race-safe materialization + uniqueness constraint + sync seed write. P2-A: CONTINUES edge for multi-day incidents. P2-B: v6.0 centroid-learning integrity note. P3: V-wording fix, L1/L2 hash domain separation, late-arriving-alert test, demo/blog scoping note, 3 new tests (11-13). |
| v1.2 | June 9, 2026 | Second review applied. Hash delimiter (\x00) prevents field collision (HIGH). time_bucket typed as int64 (MEDIUM). entity: vs user: cross-prefix documented as known limitation. Orphaned seed cleanup note. campaign_seed_key index added. Async done-callback error logging. ThreatIntel variable rename. Decision.campaign_id consumer audit (§6.4). Synopsis updated. |

**Design-authority disposition:** APPROVED with P1-A + P1-B applied.
Direction confirmed: mutable incident, stable identity, two-level
phasing, enrichment-only at v5.x.

**References:**
- DK Runtime Execution Plan v6.8 (§Performance Root Cause Analysis)
- SOC Copilot Design v5.7 (§5.3 ThreatIntelEnrichmentFactor, §30.3 F6)
- Architecture Philosophy v4.3 (§ARCH-01 Five Layers)
- Innovation Note v6 (§Innovation 7, §Innovation 8, Eq. 13)
- CGA arxiv short v7.2 (Eq. 6, Eq. 10, Eq. 13)
- Design-authority review: soc_campaign_identity_review_v1.md (June 9, 2026)
