# AGE graph health audit

Audit date: 2026-09-05. This audit used read-only PostgreSQL/AGE queries against the live WSL2 database (`soc_copilot`, graph `soc_graph`). No graph schema or graph data was modified.

## Summary

`soc_graph` contains **632,005 nodes** and **22,001 edges**. The suspected increase is real in the live graph, but it is not a broad increase in scoring data: **571,825 nodes (90.5% of all nodes) are `EvolutionEvent`**. Of those, **571,728 belong to `purchasing`** and **571,690 are `proof_record` events**.

`EvolutionEvent` occupies 330.9 MB, the largest relation in `soc_graph`; `Decision` is second at 161.7 MB. The live database holds 191 AGE graphs, including many retained `protocol_v2_test_*` and stress-test graphs, and is 867 MB in total. This catalog-wide accumulation is a separate retention concern from the `soc_graph` node increase.

There is no evidence that steady-state `POST /api/score` performs an unindexed scan of all 632K nodes. The scorer is cached and its prediction is in-memory. Its persistence path does a narrow `Decision` lookup then a write. The measured matching lookup was 1.9–2.4 ms. The slow query found is the evolution-history page query: 371–392 ms for 100 purchasing events, because it filters and orders 571K unindexed `EvolutionEvent` rows. It is not called by the score route shown in the current source.

The observed 19 s score latency therefore cannot be explained by the measured AGE reader queries alone. It needs request-level tracing around the live application, its serial mutation lock, outbound/context work, and graph writes. The data growth and missing event indexes are still urgent because diagnostics/evolution reads will degrade and the retained events substantially increase database footprint.

## Node/edge inventory

The AGE catalog has 96 labels including the two internal aggregate labels; this is **55 application node labels** and **39 edge labels**.

### Nodes

| Label | Count |
|---|---:|
| EvolutionEvent | 571,825 |
| Decision | 36,776 |
| Outcome | 5,401 |
| Observation | 3,667 |
| ConservationStatus | 3,113 |
| CentroidCheckpoint | 2,712 |
| EvidenceReceipt | 1,544 |
| ShadowDecision | 1,500 |
| Fingerprint | 997 |
| Alert | 868 |
| Campaign | 718 |
| DecisionEntityLink | 538 |
| EntityEnrichment | 528 |
| CampaignSeed | 448 |
| FactorVector | 396 |
| PromotionState | 209 |
| User | 231 |
| Asset | 226 |
| DomainContext | 141 |
| ProfileSnapshot | 51 |
| L5Centroid | 33 |
| DataQualityAlert | 20 |
| ThreatIndicator | 10 |
| AttackPattern | 9 |
| PipelineSystem | 9 |
| TransferPattern | 6 |
| Domain | 5 |
| L5ConservationState | 5 |
| L5DKWeight | 4 |
| EvolutionState | 4 |
| Entity | 2 |
| PosteriorState | 2 |
| ThreatIntel | 5 |
| DecisionDistanceLog | 1 |
| DeploymentState | 1 |
| All remaining node labels | 0 (20 labels) |

The displayed nonzero node rows sum to 632,005. `EvolutionEvent` alone is 571,825 nodes, so it exceeds the reported 494K historical increase by itself; it is the clear source of the growth hypothesis.

### Edges

| Edge | Count |
|---|---:|
| DECIDED_ON | 6,185 |
| SUMMARIZES_DOMAIN | 4,112 |
| HAS_OUTCOME | 2,781 |
| EMITTED_RECEIPT | 1,544 |
| DERIVED_FROM | 1,227 |
| SNAPSHOT_AFTER | 1,227 |
| MEMBER_OF | 1,086 |
| DETECTED_ON | 855 |
| INVOLVES | 855 |
| CLASSIFIED_AS | 645 |
| HAS_INDICATOR | 633 |
| Remaining nonzero edges | 851 |
| Edge labels with zero rows | 19 labels |

Total edges: 22,001. All edge tables have the AGE-provided `start_id` and `end_id` B-tree indexes.

## Index coverage

There are 139 indexes in `soc_graph`. They are almost entirely structural: each label table has its `id` primary-key index and every edge table has endpoint indexes.

The only non-structural property indexes found are:

```sql
CREATE INDEX decision_domain_idx
  ON soc_graph."Decision"
  USING btree (ag_catalog.agtype_access_operator(..., '"domain"'));

CREATE INDEX decision_archived_idx
  ON soc_graph."Decision"
  USING btree (ag_catalog.agtype_access_operator(..., '"archived"'));
```

| Query property | Index present? | Consequence |
|---|---|---|
| `Decision.domain` | Yes | Domain filtering has a usable property index. |
| `Decision.archived` | Yes | Active/archived filtering has a usable property index. |
| `Decision.decision_id` | No | Governed idempotency/get-by-id reads must rely on the domain filter then inspect candidates. |
| `Decision.status`, `created_at`, `category` | No | Verified/history/category reads need filtering and, where used, sorting without a matching property index. |
| `Outcome.decision_id` | No | Outcome identity cannot use a property index; relationship endpoint indexes still help traversals. |
| `CentroidCheckpoint.domain`, `created_at`, `checkpoint_id` | No | Startup and history reads filter/sort without matching property indexes. |
| `L5Centroid.domain`, `category`, `action` | No | Current cardinality is tiny, so impact is negligible now. |
| `EvolutionEvent.domain`, `event_type`, `timestamp`, `event_id` | No | The 571K-row purchasing event history is scanned and sorted for event pages and proof reads. |

## Query performance

Timings are direct live AGE calls, one execution each, over the WSL2 connection. They are diagnostic measurements, not a load test.

| Query shape from source | Time | Result / interpretation |
|---|---:|---|
| `Decision` verified-count by domain/status | 8.6 ms | 492 distinct purchasing decision IDs in the tested condition. |
| Verified `Decision` with optional `HAS_OUTCOME` traversal | 10.1 ms | 956 decision IDs in the tested condition. |
| `Decision {decision_id}` plus domain, absent ID | 1.8–2.4 ms | The governed score deduplication lookup is narrow in the current graph. |
| Latest `CentroidCheckpoint` for purchasing | 12.4–16.1 ms | One row, no matching property index. |
| `L5Centroid` by purchasing domain | 0.9 ms | Four rows. |
| Latest `ConservationStatus` by purchasing domain | 3.9 ms | One row. |
| `EvolutionEvent` by purchasing, ordered by timestamp, `LIMIT 100` | 371.7–385.3 ms | 100 rows after filtering/sorting 571,728 purchasing events. |
| `EvolutionEvent` by purchasing plus `proof_record`, ordered, `LIMIT 100` | 392.1 ms | Event-type predicate has no index benefit. |
| Group all `EvolutionEvent` by domain | 810.2 ms | Purchasing: 571,728; trading: 71; dataops: 18; s2p: 8. |
| Group all `EvolutionEvent` by type | 516.3 ms | `proof_record`: 571,690. |
| Duplicate `Decision.decision_id` audit | 134.8–162.4 ms | No duplicate groups. |

The route factory caches one `FreshScorerProxy`; `CompoundingScorer._predict()` calls `ProfileScorer.score()` in memory. A normal score then persists a decision. With governed writes enabled the store performs one `Decision {decision_id}` lookup followed by a `CREATE`; with the current environment `SCORER_GOVERNED_WRITES` is unset, so the legacy path also links a domain anchor and factor-vector node. Neither path calls `get_evolution_events()`.

The slow 0.39 s evolution query therefore matters to proof/evolution/diagnostic pages and any accidental call made during score response enrichment, but it is not sufficient to explain a 19 s score by itself.

## Data-volume growth

The `EvolutionEvent` table is the cause of the current graph expansion:

- 571,825 total event nodes; 571,728 are purchasing.
- 571,690 are `proof_record`, leaving only 135 non-proof events.
- Recent event payloads are `kind: "decision"` records with a purchasing decision ID and `evidence_provenance: "graphstore"`.
- `GraphProofLedger.record()` generates `proof:{domain}:{uuid4}` event IDs. It is intentionally append-only and has no identity check, so repeats cannot collapse into one event.
- `Decision` has 36,776 nodes. The proof-event-to-decision ratio is about 15.5:1, so this is not one bounded proof record per retained decision.

The live database also retains 191 AGE graphs, including a large population of `protocol_v2_test_*` and `soc_stress_test_*` graphs. Those graphs are not included in the `soc_graph` counts above but explain part of the 867 MB database footprint.

## Duplicate check

No duplicate `Decision` nodes with the same `decision_id` were found. The audit did observe 49 `EvolutionEvent` nodes without an `event_id`; this does not establish a duplicate event because a null identifier cannot be grouped as an identity. New proof events use a UUID event ID and are unique by construction.

## Missing indexes and recommendations

No changes were made. Before adding any index, collect application-level query timings and confirm the active workload. The highest-value candidates are:

1. `EvolutionEvent(domain, event_type, timestamp DESC)` for the measured proof/evolution history query.
2. `EvolutionEvent(event_id)` if exact event lookup/idempotency is part of the production contract.
3. `Decision(domain, decision_id)` for governed deduplication and `get_decision` lookups.
4. `Decision(domain, status, archived, created_at)` for verified/history scans and ordered decision pages.
5. `CentroidCheckpoint(domain, created_at DESC)` for startup and latest-checkpoint reads.
6. `L5Centroid(domain, category, action, updated_at_epoch DESC)` if centroid history grows beyond its current 33 rows.

The first recommendation addresses an already-measured 0.39 s query. The others are preventative or support existing history/startup paths; none alone is evidence for the observed 19 s score latency.

## Impact on `POST /api/score`

The current score route serializes requests under `mutation_lock_scope(domain)`, loads only cacheable context, obtains a cached scorer proxy, scores in memory, and persists a decision. It does not enumerate `EvolutionEvent` in the route or `CompoundingScorer.score()` path.

That means:

- The 632K-node graph is a real storage and diagnostic-query problem.
- Missing `EvolutionEvent` indexes make event/history paths slow, but do not demonstrate a 632K-node scan per score.
- The documented `Decision` lookup is presently low-millisecond because the domain index narrows it, even though `decision_id` lacks an index.
- A 19 s score should be traced at request scope: time scorer construction/cache misses, mutation-lock waiting, context enrichment, each AGE write/read, connection-pool acquisition, and any response enrichment hook. Capture query count and duration per request before changing indexes.

## Recommended actions

1. Treat proof-event growth as a retention/idempotency defect: establish a bounded retention policy or a compacted proof projection, and make proof recording idempotent using a stable business identity.
2. Preserve `soc_graph` as the product graph; separately retire disposable `protocol_v2_test_*` and stress-test graphs under an approved cleanup plan.
3. Add the event-history composite index only after a controlled maintenance plan and re-measure the 0.39 s query.
4. Add request-level timing around `POST /api/score` before changing score-path indexes. The evidence so far points away from a 553K-node full scan in the scorer.
5. Re-run this audit after any retention/index work and compare graph counts, relation sizes, and p50/p95 endpoint latency.
