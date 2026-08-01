# JM Implementation Review — Part 2A

Review-only audit of domain scoping and domain stamping. Comments, type names, and intended architecture are not treated as enforcement unless the implementation demonstrates it.

## §1 EXECUTIVE SUMMARY

| Check | Result |
|---|---|
| Goal 4 — every query is domain-scoped | **PARTIAL** |
| Goal 5 — every write stamps domain | **PARTIAL** |
| Protocol-level domain enforcement | **NO** |
| Store-level domain enforcement | **NO** |
| Remaining unscoped/domain-optional reads | **5 domain-sensitive paths**, plus non-Decision artifact/idempotency reads listed in §4 |
| Remaining unstamped writes | **1 legacy relationship write**; no unstamped Decision node write was found |

The principal defect is that the public protocol still allows unscoped Decision access: `get_decision`, traversal reads, and `query_similar` do not require a domain (`copilot-sdk/copilot_sdk/graph/protocol.py:40-48,144-160`). The AGE implementation mirrors that optionality (`ci-platform/ci_platform/graph/age_graph_store.py:2015-2024,2668-2718,3074-3096`). Most domain-specific Decision queries and all primary Decision node writes are correctly constrained/stamped, but this is not a fail-closed contract.

## §2 GOAL 4: DOMAIN-SCOPED QUERIES

### §2.1 Protocol contract

`get_outcomes` is not declared in the protocol. Outcome data is returned through verified/archive Decision reads and `write_outcome`; its absence is itself an API-surface limitation, not evidence of scoping.

| Method | domain param? | Required? | Status |
|---|---:|---:|---|
| `get_decision` | Yes | **No**, `None` default | **GAP** — caller can omit domain (`protocol.py:40-41`). |
| `get_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:43-49`). |
| `get_all_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:51-52`). |
| `get_archived_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:54-56`). |
| `get_verified_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:58-59`). |
| `count_verified` | Yes | Yes | **CONFORMANT** (`protocol.py:61-62`). |
| `count_verified_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:64-65`). |
| `count_correct` | Yes | Yes | **CONFORMANT** (`protocol.py:67-68`). |
| `count_decisions` | Yes | Yes | **CONFORMANT** (`protocol.py:70-71`). |
| `load_latest_centroids` | Yes | Yes | **CONFORMANT** (`protocol.py:83-84`). |
| `get_centroid_checkpoints` | Yes | Yes | **CONFORMANT** (`protocol.py:86-92`). |
| `read_entity_enrichment` | Yes | Yes | **CONFORMANT** (`protocol.py:119-127`). |
| `list_entity_enrichments` | Yes | Yes | **CONFORMANT** (`protocol.py:129-137`). |
| `get_decision_links` | Yes | **No**, `None` default | **GAP** — unscoped traversal is permitted (`protocol.py:144-150`). |
| `query_context` | Yes | **No**, `None` default | **GAP** — unscoped context traversal is permitted (`protocol.py:152-158`). |
| `query_similar` | No | No | **GAP** — no domain argument exists (`protocol.py:160-161`). |
| `get_transfer_patterns` | Yes, source/target | **No** | **PARTIAL** — intentionally supports cross-domain transfer reads, but no required boundary (`protocol.py:305-310`). |
| `get_latest_conservation_statuses` | Yes, list | **No** | **PARTIAL** — omitted list means all domains (`protocol.py:312-316`). |
| `get_iks_trajectory` | Yes, list | **No** | **PARTIAL** — omitted list means all domains (`protocol.py:318-324`). |
| `get_centroids` | Yes | Yes | **CONFORMANT** (`protocol.py:371-372`). |
| `get_dk_weights` | Yes | Yes | **CONFORMANT** (`protocol.py:389-390`). |
| `get_conservation_state` | Yes | Yes | **CONFORMANT** (`protocol.py:412-416`). |
| `count_categories_with_n` | Yes | Yes | **CONFORMANT** (`protocol.py:418-419`). |

Write-side protocol review:

| Method | domain param? | Required? | Status |
|---|---:|---:|---|
| `write_decision` | Yes | Yes | **CONFORMANT** (`protocol.py:19-28`). |
| `write_outcome` | Yes | **No**, `None` default | **PARTIAL** — outcome stores can derive the Decision domain, but the protocol does not require the caller to assert it (`protocol.py:30-38`). |
| `save_centroids` | Yes | Yes | **CONFORMANT** (`protocol.py:73-81`). |
| `write_entity_enrichment` | Yes | Yes | **CONFORMANT** (`protocol.py:103-117`). |
| `write_governed_decision` | Yes | Yes | **CONFORMANT** (`protocol.py:179-197`). |
| `write_observation` | Yes | Yes | **CONFORMANT** (`protocol.py:199-214`). |
| `append_evidence_receipt` | Yes | Yes | **CONFORMANT** (`protocol.py:216-226`). |
| `write_conservation_status` | Yes | Yes | **CONFORMANT** (`protocol.py:228-241`). |
| `write_fingerprint` | Yes | Yes | **CONFORMANT** (`protocol.py:243-253`). |
| `write_centroid_checkpoint` | Yes | Yes | **CONFORMANT** (`protocol.py:255-269`). |
| `write_evolution_event` | Yes | Yes | **CONFORMANT** (`protocol.py:271-285`). |
| `write_transfer_pattern` | Source and target domains | Yes | **CONFORMANT** (`protocol.py:287-303`). |
| `link_entity` | Yes | Yes | **CONFORMANT** (`protocol.py:326-333`). |
| `archive_decisions` / `domain_scoped_reset` | Yes | Yes | **CONFORMANT** (`protocol.py:335-345`). |
| L5 update methods | Yes | Yes | **CONFORMANT** (`protocol.py:360-419`). |

### §2.2 InMemory store

The store records domain on writes (`copilot-sdk/copilot_sdk/graph/memory_store.py:461-477,564-574`) and most domain-specific reads filter explicitly. The following table covers every read method in the implementation that can return graph/state data.

| Method | Filters by domain? | Status |
|---|---:|---|
| `get_decision` | Only when caller supplies domain | **GAP** — `domain=None` returns the ID match without checking domain (`memory_store.py:1043-1049`). |
| `get_decisions`, `get_all_decisions` | Yes | **CONFORMANT** (`memory_store.py:1049-1064`). |
| `get_verified_decisions`, `count_verified`, `count_verified_decisions`, `count_correct`, `count_decisions`, `count_categories_with_n` | Yes | **CONFORMANT** (`memory_store.py:1066-1117`). |
| `get_centroids`, `get_dk_weights`, `get_conservation_state` | Yes | **CONFORMANT** (`memory_store.py:1149-1217,1282-1286`). |
| `load_latest_centroids`, `get_centroid_checkpoints` | Yes | **CONFORMANT** (`memory_store.py:1312-1361`). |
| `get_evolution_events` | Yes | **CONFORMANT** (`memory_store.py:1382-1391`). |
| `read_entity_enrichment`, `list_entity_enrichments` | Yes | **CONFORMANT** (`memory_store.py:1487-1529`). |
| `get_archived_decisions`, `count_archived` | Yes | **CONFORMANT** (`memory_store.py:1561-1590`). |
| `get_decision_links` | Always constrained to store `self.domain` | **CONFORMANT at store level** (`memory_store.py:1748-1769`). The public protocol still permits omission. |
| `query_context` | Usually constrained through store-domain edges, but direct root Decision lookup is only checked against caller domain when supplied | **PARTIAL** (`memory_store.py:1771-1803,1814-1844`). |
| `query_similar` | Candidates match source domain, but source lookup has no domain assertion | **PARTIAL** (`memory_store.py:1864-1889`). |
| `get_transfer_patterns` | Only if source/target filters are supplied | **PARTIAL** — omitted filters return all transfer domains (`memory_store.py:892-903`). |
| `get_latest_conservation_statuses` | Only if `domains` is supplied | **PARTIAL** — omitted filters return one latest row per domain (`memory_store.py:905-934`). |
| `get_iks_trajectory` | Only if `domains` is supplied | **PARTIAL** — omitted filters retain all domains (`memory_store.py:936-988`). |
| `load_rl_state` | Uses the instance’s fixed `self.domain` key | **CONFORMANT for an instance-scoped store** (`memory_store.py:1322-1327`). |

### §2.3 AGE store

Primary Decision reads are correctly domain-predicated. The table includes every public Cypher read family plus private/idempotency reads that can influence write decisions.

| Method/query | Cypher includes domain? | Status |
|---|---:|---|
| `_l5_upsert_current` existing/update/delete/edge queries | Yes when identity contains `domain`; callers use domain identity | **CONFORMANT** (`age_graph_store.py:81-185,2287-2290,2421-2447`). |
| `_ensure_domain_anchor` | Exact domain anchor lookup | **CONFORMANT** (`age_graph_store.py:1028-1050`). |
| `_get_conservation_status_payload(status_id)` | No | **GAP** — lookup is only by `status_id` (`age_graph_store.py:1214-1221`). |
| `_get_fingerprint_payload(fingerprint_id)` | No | **GAP** — lookup is only by `fingerprint_id` (`age_graph_store.py:1293-1299`). |
| `_get_centroid_checkpoint_payload(checkpoint_id)` | No | **GAP** — lookup is only by `checkpoint_id` (`age_graph_store.py:1387-1393`). |
| `_get_evolution_event_payload(event_id)` | No | **GAP** — lookup is only by `event_id` (`age_graph_store.py:1897-1903`). |
| `write_transfer_pattern` existing-pattern check | No | **PARTIAL** — idempotency read is only by `pattern_id` (`age_graph_store.py:1725-1731`); the later transfer read is filterable. |
| `get_decision` | Optional `WHERE d.domain`; absent when `domain=None` | **GAP** (`age_graph_store.py:2015-2027`). |
| `get_decisions` | Yes | **CONFORMANT** (`age_graph_store.py:2029-2049`). |
| `get_verified_decisions`, `count_verified`, `count_verified_decisions`, `count_correct` | Yes | **CONFORMANT** (`age_graph_store.py:2051-2122`). |
| `count_decisions`, `count_categories_with_n` | Yes | **CONFORMANT** (`age_graph_store.py:2124-2153`). |
| `get_centroids`, `get_dk_weights`, `get_conservation_state` | Yes | **CONFORMANT** (`age_graph_store.py:2194-2251,2310-2376,2451-2518`). |
| `get_all_decisions`, `get_archived_decisions` | Yes | **CONFORMANT** (`age_graph_store.py:2520-2556`). |
| `load_latest_centroids`, `get_centroid_checkpoints`, `get_evolution_events` | Yes | **CONFORMANT** (`age_graph_store.py:2599-2609,2765-2803`). |
| `get_transfer_patterns` | Only when source/target filters supplied | **PARTIAL** — `WHERE true` permits cross-domain transfer results when both filters are omitted (`age_graph_store.py:1791-1821`). |
| `get_latest_conservation_statuses` | Only when `domains` supplied | **PARTIAL** — omitted list returns all domain summaries (`age_graph_store.py:1823-1845`). |
| `get_iks_trajectory` | Only when `domains` supplied | **PARTIAL** — omitted list returns all domains (`age_graph_store.py:1847-1895`). |
| `get_decision_links` | Optional predicate only | **GAP** — both relationship queries omit `WHERE` when domain is omitted (`age_graph_store.py:2668-2718`). |
| `query_context` | Optional predicate only | **GAP** — `WHERE n.domain=...` is emitted only when domain is supplied (`age_graph_store.py:3074-3096`). |
| `query_similar` | Candidate has `s.domain = d.domain` | **PARTIAL** — candidates stay in the source domain, but the source Decision lookup has no caller-supplied domain boundary (`age_graph_store.py:3098-3109`). |

### §2.4 AGE SDK adapter

The adapter forwards required domains correctly for the required-domain methods, but it preserves the optionality of the unsafe legacy methods. `get_decision` forwards `domain=None` unchanged (`ci-platform/ci_platform/graph/age_sdk_adapter.py:268-269`); traversal forwards an omitted domain (`:530-553`); and `query_similar` has no domain argument (`:555-556`). Required Decision/count/learning reads pass domain through (`:271-322,347-385,420-435,509-516`).

**AGE SDK adapter status: PARTIAL.** It does not invent a new omission, but it also does not enforce a domain before delegating.

### §2.5 Per-copilot remaining findings

| Copilot/path | Status | Evidence |
|---|---|---|
| S2P framework `LearningState` query | **PARTIAL** | It queries `MATCH (ls:LearningState)` with no domain predicate at `s2p-copilot/backend/app/routers/framework_router.py:276-285`. This is not a `Decision` label, but it can return a shared graph’s arbitrary LearningState row and is not domain-safe state access. |
| DataOps graph queries | **CONFORMANT** | Every Cypher query in the file predicates the relevant node with `domain='dataops'`: pipelines `graph_queries.py:144-148,192-196`, alerts `:170-173,230-233,368-371`, and impact/urgency/recurrence `:493-496,512-515,532-535`. |
| DataOps enrichment | **CONFORMANT** | Query parameters include `domain='dataops'` (`graph_enrichment.py:51-60`); reads/updates predicate `existing.domain = $domain` (`:99-117`). |
| Trading regime classifier | **CONFORMANT** | Verified reads pass `self._domain` and have no unscoped retry (`regime_classifier.py:139-145`). |
| Trading active AGE wrapper | **PARTIAL** | The wrapper has no own read methods; `__getattr__` delegates all reads to the underlying store (`trading/backend/app/graph_status.py:310-311`). Thus required-domain methods remain scoped by the underlying store, but optional legacy reads are not rejected at the wrapper boundary. |
| Purchasing active AGE wrapper | **PARTIAL** | As with Trading, reads are delegated through `__getattr__` (`purchasing/backend/app/graph_status.py:302-303`), with no wrapper-level required-domain guard. |
| SOC `db/neo4j.py` | **CONFORMANT for Decision predicate helper** | The module’s `soc_decision_where` emits `alias.domain = 'soc'` (`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:20-25`). It has no Decision read method of its own; it initializes the GraphConfig-resolved AGE client (`:45-54`). |
| SOC triage | **CONFORMANT for Decision reads; PARTIAL for non-Decision graph context** | Every `MATCH (d:Decision)` query has `WHERE d.domain='soc'` (`triage.py:911-912,982-983,1080-1081,1204-1205,1565-1566,1779-1781,1834-1835,1852-1853,2301-2302,2439-2440`). Alert/user/asset context queries are not domain-predicated (`triage.py:434-441,2704-2720,3038-3048`), but those labels are not Decision records. |

## §3 GOAL 5: DOMAIN-STAMPED WRITES

### §3.1 Protocol contract

The protocol requires domain for every Decision/node-oriented write except `write_outcome`, whose `domain` is optional (`copilot-sdk/copilot_sdk/graph/protocol.py:30-38`). All governed Decision, observation, receipt, learning artifact, transfer, entity-link, archive, and reset writes declare required domain parameters (`protocol.py:179-345,360-419`).

**Protocol write status: PARTIAL.** The Decision creation methods are required-domain, but the outcome contract is not fail-closed and legacy implementation methods outside the protocol remain possible.

### §3.2 AGE store writes

| Method/write family | Cypher stamps domain? | Status |
|---|---:|---|
| `write_decision` | Yes, `domain` in Decision properties | **CONFORMANT** (`age_graph_store.py:558-585,861-884`). |
| `write_governed_decision` | Yes, `domain` in Decision properties | **CONFORMANT** (`age_graph_store.py:709-794`). |
| `write_outcome` | Yes, Outcome gets `domain: d.domain` | **PARTIAL** — storage stamps it, but caller domain is optional and Decision matching can omit domain (`age_graph_store.py:886-924`; `protocol.py:30-38`). |
| `write_observation` | Yes, `domain` in Observation properties | **CONFORMANT** (`age_graph_store.py:986-1026`). |
| `write_conservation_status` | Yes, `domain` in ConservationStatus properties | **CONFORMANT** (`age_graph_store.py:1149-1207`). |
| `write_fingerprint` | Yes, `domain` in Fingerprint properties | **CONFORMANT** (`age_graph_store.py:1240-1285`). |
| `write_centroid_checkpoint` / `save_centroids` | Yes, `domain` in checkpoint properties | **CONFORMANT** (`age_graph_store.py:1317-1379,2558-2597`). |
| `append_evidence_receipt` | Yes, receipt node and edge carry domain | **CONFORMANT** (`age_graph_store.py:1524-1607`). |
| `write_evolution_event` / `save_evolution_event` | Yes, event properties carry domain | **CONFORMANT** (`age_graph_store.py:1639-1690,2618-2638`). |
| `write_transfer_pattern` | Source and target domains are stored | **CONFORMANT for transfer semantics** (`age_graph_store.py:1692-1783`). |
| `link_entity` | DomainContext node and ABOUT edge carry domain | **CONFORMANT** (`age_graph_store.py:1927-2013`). |
| `link_decision_to_entity` | Legacy fallback edge has no domain property | **GAP** — optional domain only constrains the Decision match; `_link_props` omits domain and fallback creates `DecisionEntityLink` without it (`age_graph_store.py:2640-2666,2727-2741`). |
| Entity enrichment | Domain is passed to the underlying enrichment implementation | **CONFORMANT** (`age_graph_store.py:3170-3214`). |

### §3.3 SQLite store writes

Every `INSERT` statement inspected includes a domain column or domain-bearing source value: Decisions/outcomes (`copilot-sdk/copilot_sdk/graph/sqlite_store.py:1110-1119,1168-1176`), receipts/learning artifacts (`:1326-1335,1406-1414,1477-1485,1558-1567`), transfers/events/outbox (`:1644-1655,1874-1884,2010-2027,2042-2050`), L5/RL state (`:2224-2234,2325-2337,2435-2442,2531-2540,2571-2578`), enrichment (`:2958-2962`), and archive copies (`:3103-3118,3170-3186`).

**SQLite write status: CONFORMANT.** The implementation includes domain in every INSERT column list relevant to graph/state records.

### §3.4 InMemory store writes

| Method/write family | Stores domain? | Status |
|---|---:|---|
| Decisions and governed Decisions | Yes | **CONFORMANT** (`memory_store.py:461-477,522-546`). |
| Outcomes and observations | Yes | **CONFORMANT** (`memory_store.py:549-574,576-620`). |
| Evidence, conservation, fingerprint, centroid, evolution | Yes | **CONFORMANT** (`memory_store.py:628-830,1288-1380`). |
| Transfer patterns | Source/target domains stored | **CONFORMANT** (`memory_store.py:846-890`). |
| Entity enrichment | Domain is part of the storage key/record | **CONFORMANT** (`memory_store.py:1393-1485`). |
| `link_entity` | Domain stored and checked | **CONFORMANT** (`memory_store.py:990-1017`). |
| Legacy `link_decision_to_entity` | Derives/stores Decision domain | **CONFORMANT at memory store level** (`memory_store.py:1730-1746`). |
| Archive/reset/outbox | Domain retained and filtered | **CONFORMANT** (`memory_store.py:359-431,1531-1559,1596-1721`). |

### §3.5 Scorer write paths

| Path | Domain passed? | Status |
|---|---:|---|
| Decision persistence | Yes, `domain=self._domain` for governed writes and positional `self._domain` for legacy writes | **CONFORMANT** (`scorer.py:343-368`). |
| `write_outcome` | Yes, `domain=self._domain` | **CONFORMANT in current scorer** (`scorer.py:678-684`). |
| `_persist_conservation_snapshot` | Yes, payload and call use `self._domain` | **CONFORMANT** (`scorer.py:862-885`). |
| `_persist_fingerprint` | Yes, payload and call use `self._domain` | **CONFORMANT** (`scorer.py:1229-1247`). |
| `_save_centroids_checkpoint` | Yes for legacy and V2 calls | **CONFORMANT** (`scorer.py:1727-1737,1755-1768`). |
| `_persist_learning_artifacts` coordinator | Uses domain-scoped Decision load and delegates to domain-bearing artifact methods | **CONFORMANT** (`scorer.py:923-936,944-1005`). |
| `capture_existing_state` | Delegates to the same domain-bearing persistence methods and uses domain-scoped counts | **CONFORMANT** (`scorer.py:1034-1095`). |

### §3.6 Per-copilot remaining findings

| Copilot/path | Status | Evidence |
|---|---|---|
| S2P legacy `domains/s2p/graph.py` | **CONFORMANT / no write surface** | The file contains only `get_s2p_decision`; its query requires `d.domain='s2p'` (`s2p-copilot/backend/app/domains/s2p/graph.py:50-71`). No write method remains in the file. |
| DataOps local metadata write | **PARTIAL** | It stamps `stored["domain"] = DOMAIN` and `provenance="demo"` before writing JSON (`copilot-sdk/apps/dataops/backend/app/context_router.py:1603-1615`), but this is not a governed graph write. |
| Trading active wrapper | **CONFORMANT for writes** | `write_decision` rejects non-trading domains and delegates with `domain=DOMAIN` (`copilot-sdk/apps/trading/backend/app/graph_status.py:246-289`). |
| Purchasing active wrapper | **CONFORMANT for writes** | `write_decision` rejects non-purchasing domains and delegates with `domain=DOMAIN` (`copilot-sdk/apps/purchasing/backend/app/graph_status.py:236-281`). |
| SOC triage Decision creation | **CONFORMANT** | Both analyzed/executed Decision CREATE paths include `domain: 'soc'` (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:866-876,1530-1545`). Subsequent Decision updates are also domain-filtered, as listed in §2.5. |

## §4 REMAINING GAPS

### High severity

| Gap | Evidence | Risk |
|---|---|---|
| Optional/unscoped `get_decision` | `copilot-sdk/copilot_sdk/graph/protocol.py:40-41`; AGE implementation `ci-platform/ci_platform/graph/age_graph_store.py:2015-2027`; memory implementation `copilot-sdk/copilot_sdk/graph/memory_store.py:1043-1049` | A caller can omit domain and retrieve a Decision by ID without a domain assertion. |
| Optional unscoped traversal | `protocol.py:144-160`; AGE `age_graph_store.py:2668-2718,3074-3096`; memory `memory_store.py:1771-1803` | Context/link reads can cross the intended boundary when the caller does not supply domain. |
| `query_similar` has no domain contract | `protocol.py:160-161`; AGE `age_graph_store.py:3098-3109`; memory `memory_store.py:1864-1889` | Same-domain candidate filtering is relative to an unscoped source lookup, not an asserted caller domain. |
| S2P `LearningState` read has no domain predicate | `s2p-copilot/backend/app/routers/framework_router.py:276-285` | A shared graph can return arbitrary LearningState state; it is not a Decision label, but it remains domain-unscoped learning state. |

### Medium severity

| Gap | Evidence | Risk |
|---|---|---|
| AGE private artifact idempotency reads omit domain | `age_graph_store.py:1214-1221,1293-1299,1387-1393,1897-1903` | Colliding artifact IDs can cause cross-domain existing-record comparison before a write. |
| AGE transfer-pattern existing lookup omits source/target domain | `age_graph_store.py:1725-1731` | Colliding pattern IDs can be compared across transfer domains. |
| Cross-domain summaries are opt-in only at call level | Protocol `protocol.py:305-324`; AGE `age_graph_store.py:1791-1895`; memory `memory_store.py:892-988` | Transfer, conservation, and IKS reads intentionally support multi-domain results but are not fail-closed when filters are omitted. |
| Legacy `link_decision_to_entity` edge is unstamped | `age_graph_store.py:2640-2666,2727-2741` | Relationship records can lose the domain partition even though the Decision node is checked. |

No remaining unstamped `Decision` node CREATE was found in the reviewed AGE, SQLite, InMemory, scorer, S2P legacy, Trading, Purchasing, or SOC triage paths. The remaining write gap is the legacy relationship fallback, not a Decision node.

## §5 READING LOG

All listed files were read fully before targeted line inspection.

| File | Read range |
|---|---:|
| `copilot-sdk/docs/design/age_unification_gaps_v1.md` | 1-817 |
| `copilot-sdk/docs/design/jm_implementation_review_part1a_v1.md` | 1-218 |
| `copilot-sdk/docs/design/jm_implementation_review_part1b_v1.md` | 1-144 |
| `copilot-sdk/CLAUDE.md` | 1-139 |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | 1-419 |
| `copilot-sdk/copilot_sdk/graph/memory_store.py` | 1-1978 |
| `ci-platform/ci_platform/graph/age_graph_store.py` | 1-3214 |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py` | 1-596 |
| `s2p-copilot/backend/app/routers/framework_router.py` | 1-819 |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py` | 1-604 |
| `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py` | 1-131 |
| `copilot-sdk/apps/trading/backend/app/services/regime_classifier.py` | 1-198 |
| `copilot-sdk/apps/trading/backend/app/graph_status.py` | 1-456 |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py` | 1-474 |
| `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py` | 1-56 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | 1-3177 |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py` | 1-3436 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | 1-2157 |
| `s2p-copilot/backend/app/domains/s2p/graph.py` | 1-71 |
| `copilot-sdk/apps/dataops/backend/app/context_router.py` | 1-1620 |

The requested literal path `ci_platform/ci_platform/graph/age_graph_store.py` does not exist in this checkout; the corresponding full file is at `ci-platform/ci_platform/graph/age_graph_store.py`.

READY: YES
