# J6 Factor-Vector and Fingerprint Eligibility Diagnostic

Status: diagnostic only. No source or test files were changed.

## 1. Executive Summary

SOC can produce a usable fingerprint only when its verified Decision rows
contain compatible `factor_vector` values. `compute_fingerprint` does not
derive factor statistics from centroids, DK weights, or an in-memory W matrix;
it reads verified decisions from the graph and accepts only vectors whose
length equals the preset factor width ([fingerprint.py:27-50](../../copilot_sdk/scoring/fingerprint.py:27)).

The live probe reports a missing `factors` key, but does not report
`factor_vector`. That distinction is material. The normal SOC analyze path
stores `factor_vector`, and the bootstrap writer stores native factor vectors
([triage.py:728-728](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:728),
[triage.py:866-885](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:866),
[bootstrap_neo4j.py:141-150](../../../gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:141)).
The standalone verified seed and execute path explicitly write empty vectors
([seed_verified_decisions.py:103-125](../../../gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py:103),
[triage.py:1530-1546](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1530)).

**Critical outputs**

- `FINGERPRINT_USES_GRAPH_FACTORS: YES` — specifically graph-returned
  `factor_vector` values, not necessarily a `factors` mapping.
- `FINGERPRINT_USES_INMEMORY_STATE: NO` for fingerprint factor statistics.
- `SOC_CAN_PRODUCE_FINGERPRINT: NO with the current corpus if the reported
  missing-factor result means verified rows have absent or empty
  factor_vector values; YES if a corrected probe finds at least five
  six-element vectors.`
- `ROOT_CAUSE: the fingerprint eligibility filter uses factor_vector, while
  part of the SOC historical corpus was written with empty vectors and the
  live probe checked a different field.`
- `SMALLEST_FIX: first count verified SOC rows with a six-element
  factor_vector; then either invoke write-on-exist fingerprint emission if
  the count is at least five, or repair the authoritative seed/migration data
  before emitting.`

## 2. Factor Storage Per Copilot

The shared scorer builds a factor vector during `_predict`, puts it in decision
metadata, and writes it through either the governed V2 writer or legacy writer
([scorer.py:310-368](../../copilot_sdk/scoring/scorer.py:310)). The V2 protocol
explicitly accepts `factor_vector` and `factor_names`
([protocol.py:179-196](../../copilot_sdk/copilot_sdk/graph/protocol.py:179)).

| Copilot | Factor source and storage | Defaults when request is sparse | Evidence |
|---|---|---|---|
| SOC | Normal analyze computes a vector; execute writes `[]`; bootstrap generates vectors; `seed_verified` writes `[]`. | Normal factor computers; no usable vector on execute/seed path | [triage.py:559-587](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:559), [triage.py:1533-1543](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1533), [bootstrap_neo4j.py:125-150](../../../gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:125) |
| S2P | Route computes domain factors, then active store writes a governed vector. | `0.5` per named factor if metadata has no vector | [s2p.py:1885-1926](../../../s2p-copilot/backend/app/routers/s2p.py:1885), [s2p_graph_status.py:285-318](../../../s2p-copilot/backend/app/s2p_graph_status.py:285) |
| Trading | Shared scorer prediction and active store write a governed vector. | `0.5` per named factor in active writer | [scorer.py:331-358](../../copilot_sdk/scoring/scorer.py:331), [trading graph_status.py:263-297](../apps/trading/backend/app/graph_status.py:263) |
| Purchasing | Active writer computes domain factors and merges request overrides. | Computed factors plus `0.5` fallback through the merged mapping | [purchasing graph_status.py:253-259](../apps/purchasing/backend/app/graph_status.py:253), [purchasing graph_status.py:279-292](../apps/purchasing/backend/app/graph_status.py:279) |
| DataOps | Shared scorer prediction and active store write a governed vector. | `0.5` per named factor in active writer | [dataops graph_status.py:249-253](../apps/dataops/backend/app/graph_status.py:249), [dataops graph_status.py:273-286](../apps/dataops/backend/app/graph_status.py:273) |

The schema distinction matters. The legacy AGE writer stores a JSON `factors`
property and can derive a vector from numeric factor entries
([age_graph_store.py:558-647](../../ci-platform/ci_platform/graph/age_graph_store.py:558)).
The governed writer stores explicit `factor_vector` and `factor_names`
([age_graph_store.py:709-794](../../ci-platform/ci_platform/graph/age_graph_store.py:709)).
The reader decodes both properties ([age_graph_store.py:3117-3144](../../ci-platform/ci_platform/graph/age_graph_store.py:3117)),
but fingerprint eligibility uses `factor_vector`.

## 3. SOC Decision Creation Path

### Normal analyze

The analyze route resolves the alert category, invokes SOC factor computers,
and calls the ProfileScorer with the computed vector
([triage.py:480-609](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:480)).
It flattens that vector into `fv_list` ([triage.py:728-728](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:728)) and
stores it on the Decision along with provenance, category, source, user,
confidence, and outcome ([triage.py:866-885](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:866)).
The referral gate may change the selected action to `refer_to_analyst`, but it
does so after vector construction ([triage.py:612-635](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:612)).
Thus non-scorable routing explains skipped learning artifacts, but does not by
itself prove that the Decision lacks a vector.

### Execute and outcome

The execute path obtains factor names for audit but explicitly creates a
Decision with `factor_vector: []` ([triage.py:1495-1504](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1495),
[triage.py:1524-1546](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1524)).
Those rows are not fingerprint-compatible. The outcome path reads stored
factor vectors when available and uses them for compound updates; missing
vectors are a separate non-learning condition. The SOC adapter constructs the
shared compound scorer ([scorer_adapter.py:15-30](../../../gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:15)).

## 4. SOC Bootstrap and Seed Analysis

The current code has distinct data producers:

1. `bootstrap_neo4j.py` generates each vector from the calibrated centroid plus
   bounded noise and stores a native list ([bootstrap_neo4j.py:125-150](../../../gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:125),
   [bootstrap_neo4j.py:202-226](../../../gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:202)).
2. `app/seed/decisions.py` generates six-factor vectors from SOC centroids plus
   noise ([decisions.py:32-62](../../../gen-ai-roi-demo-v4-v50/backend/app/seed/decisions.py:32),
   [decisions.py:99-107](../../../gen-ai-roi-demo-v4-v50/backend/app/seed/decisions.py:99)).
3. `scripts/seed_verified_decisions.py` sets `factor_vector: []` and writes
   that empty list into every seeded Decision ([seed_verified_decisions.py:103-125](../../../gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py:103),
   [seed_verified_decisions.py:131-152](../../../gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py:131)).

The legacy `seed_neo4j.py` is not an AGE source of truth: it aborts when
`GRAPH_BACKEND=age` ([seed_neo4j.py:10-15](../../../gen-ai-roi-demo-v4-v50/backend/seed_neo4j.py:10)).
The reported live key list therefore requires a corrected probe before it can
distinguish a missing `factors` mapping from a missing `factor_vector`.

## 5. Fingerprint Computation Requirements

`compute_fingerprint` accepts only list/tuple vectors with exact expected
width ([fingerprint.py:27-47](../../copilot_sdk/scoring/fingerprint.py:27),
[fingerprint.py:86-95](../../copilot_sdk/scoring/fingerprint.py:86)). It uses
those vectors and `is_correct` to compute sigmas, weights, win rate, and
category precision ([fingerprint.py:49-83](../../copilot_sdk/scoring/fingerprint.py:49)).
Fewer than five compatible rows returns sigma `0.5`, weight `0.0`, and
`insufficient data` ([fingerprint.py:32-47](../../copilot_sdk/scoring/fingerprint.py:32)).

The scorer supplies graph verified decisions directly to this function
([scorer.py:772-783](../../copilot_sdk/scoring/scorer.py:772)). Its persistence
method serializes the returned statistics; it does not substitute centroids or
DK weights ([scorer.py:1048-1128](../../copilot_sdk/scoring/scorer.py:1048)).

| Requirement | Finding |
|---|---|
| `FINGERPRINT_USES_GRAPH_FACTORS` | YES: graph-returned `factor_vector`, exact preset width |
| `FINGERPRINT_USES_INMEMORY_STATE` | NO for fingerprint factor statistics |
| Raw vectors needed by warm-start | NO after fingerprint creation; transfer consumes factor names and sigma/weight statistics ([transfer.py:101-165](../../copilot_sdk/copilot_sdk/backend/transfer.py:101)) |
| SOC required inputs now | NO if current verified rows have absent/empty vectors; not proven by a probe that only inspected `factors` |

## 6. IKS Computation Path

`IKSService` reads verified Decisions from the graph and computes a trajectory
from them and the preset shape ([iks_service.py:26-36](../../copilot_sdk/copilot_sdk/scoring/iks_service.py:26),
[iks_service.py:45-51](../../copilot_sdk/copilot_sdk/scoring/iks_service.py:45)).
The scorer's `_compute_iks` obtains verified/correct counts, invokes the
fingerprint method for one component, and computes category coverage from
verified decisions ([scorer.py:1376-1417](../../copilot_sdk/scoring/scorer.py:1376)).
Consequently SOC can have a non-null IKS from volume, accuracy, trajectory,
and coverage while its fingerprint remains `insufficient data`.

## 7. Decision Property Comparison

| Property | SOC normal analyze | SOC execute / `seed_verified` | Shared S2P/Trading/Purchasing/DataOps |
|---|---|---|---|
| `category` | Resolved SOC category | Present in seed/execute | Passed to governed writer |
| `factors` mapping | Not the canonical direct-analyze property | Not guaranteed | Legacy writer can store it |
| `factor_vector` | Computed vector | Explicitly empty | Prediction or active-store fallback vector |
| `factor_names` | Not present in direct SOC CREATE | Not present | Governed writer receives preset names |
| outcome correctness | Added/updated by outcome handling | Seed can contain outcome/correct fields | Shared learner writes outcome |

Evidence for shared vector/name persistence is [scorer.py:331-358](../../copilot_sdk/scoring/scorer.py:331);
active-store behavior is shown by [trading graph_status.py:263-297](../apps/trading/backend/app/graph_status.py:263),
[purchasing graph_status.py:253-289](../apps/purchasing/backend/app/graph_status.py:253),
[dataops graph_status.py:249-283](../apps/dataops/backend/app/graph_status.py:249),
and [s2p_graph_status.py:285-318](../../../s2p-copilot/backend/app/s2p_graph_status.py:285).

## 8. Warm-Start Requirements

The warm-start script reads the latest source `Fingerprint`, parses
`factor_names` and `factor_stats`, and creates a source-to-target mapping
([trigger_warm_start.py:16-29](../../scripts/trigger_warm_start.py:16),
[trigger_warm_start.py:50-104](../../scripts/trigger_warm_start.py:50)).
The transfer detector compares source/target sigmas and shared factor names
([transfer.py:101-138](../../copilot_sdk/copilot_sdk/backend/transfer.py:101)).
Raw Decision vectors are not needed by the target once the source fingerprint
exists. An `insufficient data` fingerprint is not sufficient because its
weights are zero ([fingerprint.py:32-47](../../copilot_sdk/copilot_sdk/scoring/fingerprint.py:32)).

If SOC has a valid fingerprint, it is sufficient for SOC→S2P and SOC→DataOps.
If it has zero compatible vectors, those transfers cannot be proven by merely
adding a write-on-exist emission.

## 9. Root Cause

The fingerprint path filters graph verified Decisions by exact
`factor_vector` width, while historical SOC writers include empty-vector
paths; the live probe also checked `factors`, a different field. Therefore
write-on-exist cannot create a usable SOC fingerprint until vector eligibility
is verified or repaired.

## 10. Fix Options

### a. Write-on-exist alone

Conditionally sufficient. If a corrected eligibility census finds at least five
six-element verified vectors, the existing fingerprint computation is ready
and write-on-exist emission is sufficient. If not, it will continue to emit an
`insufficient data` result.

### b. Seed-data fix

Required if compatible rows are fewer than five. The concrete defective seed
is `seed_verified_decisions.py`, which deliberately writes empty vectors
([seed_verified_decisions.py:103-139](../../../gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py:103)).
Repair the historical writer or perform a governed backfill only from an
authoritative per-decision factor source.

### c. SOC triage factor storage

Not required for normal analyze: that path already stores `factor_vector`
([triage.py:559-587](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:559),
[triage.py:866-885](../../../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:866)).
The execute path must either store a real vector or remain explicitly excluded
from fingerprint training because it currently writes `[]`.

### d. Eligibility validation

The diagnostic must count verified rows with exact vector width and verify that
`is_correct` and category data are present. A count of the `factors` property
alone is insufficient.

## 11. Recommendation — Smallest Safe Fix

1. Run a read-only SOC eligibility census reporting, separately, the presence
   and widths of `factors` and `factor_vector`, plus the count of verified rows
   accepted by `_compatible_decisions`.
2. If compatible rows are at least five, invoke the existing fingerprint
   persistence from the write-on-exist path. No seed rewrite is required.
3. If compatible rows are below five, correct the authoritative seed/migration
   source. Prefer the existing six-factor generation in `app/seed/decisions.py`
   or bootstrap, but only when tied to the corresponding Decision and outcome.
   Do not assign one centroid or random values to unrelated historical rows.
4. Keep execute and empty-vector seed rows out of fingerprint training unless
   repaired with real per-decision vectors.
5. Verify `decisions_analyzed >= 5`, nonzero factor weights, and a source
   fingerprint that `trigger_warm_start.py` can parse.

## 12. Reading Log

| File | Evidence read |
|---|---|
| `copilot-sdk/copilot_sdk/scoring/fingerprint.py` | Full computation, compatibility filter, fallback threshold, sigmas, weights, and category precision: lines 1-122 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | `from_preset`, score persistence, fingerprint, `_persist_fingerprint`, and `_compute_iks`: lines 210-470, 772-784, 1048-1128, 1376-1418 |
| `copilot-sdk/copilot_sdk/scoring/iks_service.py` | Full graph-backed IKS summary and verified-decision normalization: lines 1-73 |
| `copilot-sdk/copilot_sdk/backend/transfer.py` | Full fingerprint import/detection and factor-stat mapping: lines 1-165 |
| `copilot-sdk/scripts/trigger_warm_start.py` | Full source fingerprint lookup, registry construction, warm-start, and verification: lines 1-157 |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py` | Score/Learn models, score route, and metadata forwarding: lines 46-110, 284-299 |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | Legacy/V2 decision signatures including factor fields: lines 1-28, 179-214 |
| `ci-platform/ci_platform/graph/age_graph_store.py` | Factor serialization, governed writer, verified reads, JSON decoding: lines 558-647, 709-794, 2015-2069, 3117-3168 |
| `s2p-copilot/backend/app/routers/s2p.py` | S2P factor computation, scorer call, vector response, learn paths: lines 1335-1405, 1872-2010, 2068-2290 |
| `s2p-copilot/backend/app/s2p_graph_status.py` | S2P vector fallback and governed write: lines 268-320 |
| `copilot-sdk/apps/trading/backend/app/graph_status.py` | Trading vector fallback and governed write: lines 246-300 |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py` | Purchasing factor merge and governed write: lines 236-292 |
| `copilot-sdk/apps/dataops/backend/app/graph_status.py` | DataOps vector fallback and governed write: lines 232-286 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | SOC analyze and execute Decision writes: lines 480-635, 728-885, 1490-1570 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py` | SOC compound scorer construction/delegation: lines 1-30 and persistence bridge |
| `gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py` | Bootstrap vector generation and AGE CREATE payload: lines 1-20, 78-152, 155-239 |
| `gen-ai-roi-demo-v4-v50/backend/app/seed/decisions.py` | SOC synthetic vector generation: lines 17-64, 99-107 |
| `gen-ai-roi-demo-v4-v50/backend/scripts/seed_verified_decisions.py` | Empty-vector seed and CREATE query: lines 73-153 |
| `gen-ai-roi-demo-v4-v50/backend/seed_neo4j.py` | Legacy Neo4j guard under AGE: lines 1-15 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py` | SOC factor names and six-factor shape: lines 35-66, 92-130 |

