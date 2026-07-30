# Phase 6 Design — TransferPattern, Global Queries, and Claim Proof

Status: design investigation only, 2026-07-29. This document proposes the
Phase 6 implementation and gate; it does not claim that Phase 6 is shipped.

## 1. Executive Summary

JM Phase 6 requires a pure shared-graph proof for the claims in JM §2:

- transfer traversal from a source copilot through a target copilot,
- cross-domain business discovery,
- global conservation and IKS trajectories,
- a `demo.py --status` indicator for the shared judgment graph, and
- a working graph query for every outreach claim, without fixtures, API
  stitching, or local-file substitution.

The current platform has the ingredients for the judgment snapshots:
`ConservationStatus` writes include `computed_at` and are linked to a `Domain`
anchor (`age_graph_store.py:1103-1166`), and V2 `CentroidCheckpoint` writes
include `iks`, `created_at`, and optional Decision links
(`age_graph_store.py:1271-1339`). However, there is no AGE `TransferPattern`
writer, no transfer-edge writer, and no global latest-snapshot query. The
current transfer implementation is a local JSON/in-memory registry
(`copilot_sdk/transfer/registry.py:61-78`, `131-169`) and the scorer warm-start
path consumes registry patterns rather than graph patterns
(`copilot_sdk/scoring/scorer.py:1093-1163`).

Recommendation: add a graph-native `TransferPattern` contract with deterministic
revision identities, retain factor-quality transfer and procedural rule
transfer as distinct `pattern_type` values, create an `EvolutionEvent` before
creating a validated pattern, add global snapshot query methods, then run the
§2 claim registry against live AGE.

Estimated implementation effort: 8–11 engineering days, excluding AGE
environment setup and data remediation.

## 2. §2 Claim Registry

The following are the eight claims listed in JM v2.7 §2
(`judgment_memory_v2_7.md:138-152`). A query draft is shown for each claim.
Queries use named parameters for readability; the AGE adapter must render them
using the repository's existing safe literalization convention before execution.

| # | Claim | Graph proof and draft query | Current status | Phase 6 work |
|---:|---|---|---|---|
| 1 | “One engine, one graph” | `MATCH (d:Decision) RETURN collect(DISTINCT d.domain) AS domains, count(d) AS decisions` plus a runtime assertion that every copilot's `GraphConfig.graph` is `soc_graph`. | PARTIAL: decisions exist in all five domains, but only 2 domain anchors are present. | Run P6.3a, then prove graph/config identity and five anchors. |
| 2 | “Cross-graph attention” | `MATCH (d1:Decision)-[:ABOUT]->(c:DomainContext)<-[:ABOUT]-(d2:Decision) WHERE d1.domain <> d2.domain RETURN d1.domain, d2.domain, c.entity_id, count(*)` | NOT PROVEN: no shared DomainContext topology is present. | Run P6.3b and require cross-domain ABOUT edges. |
| 3 | “$604K cross-graph finding” | `MATCH (sap:DomainContext {entity_type:'sap_change'})<-[:ABOUT]-(s:Decision), (sap)<-[:ABOUT]-(o:Decision) WHERE s.domain <> o.domain RETURN sap.entity_id, s, o, ...` | NOT PROVEN: zero monetary DomainContext entities. | Run P6.3b; require computed graph total 604000.0 USD. |
| 4 | “Pattern transfer SOC→S2P→DataOps” | `MATCH (tp:TransferPattern)-[:FROM_DOMAIN]->(src:Domain), (tp)-[:TO_DOMAIN]->(dst:Domain) WHERE src.name='soc' AND dst.name IN ['s2p','dataops'] RETURN tp` | NOT PROVEN: zero TransferPattern nodes. | Run P6.3c after P6.2; require validated edges. |
| 5 | “315 values that compound” | `MATCH (c:CentroidCheckpoint) RETURN count(c) AS checkpoints, count(DISTINCT c.factor_names_hash) AS geometries, collect(DISTINCT c.domain) AS domains` | PARTIAL: checkpoints exist only for S2P and DataOps. | Run P6.3a; require checkpoints for all five and derive values from shape. |
| 6 | “You can't fork judgment” | `MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome), (d)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt) RETURN d.domain, count(DISTINCT d), count(DISTINCT r)` plus provenance checks that canonical reads resolve only through GraphStore/AGE. | PARTIAL: decisions exist, but artifact and provenance coverage is incomplete. | Run P6.3a and the graph-only provenance gate. |
| 7 | “One traversal. One answer.” | `MATCH p=(src:Domain)-[*1..6]-(x)-[*1..6]-(dst:Domain) WHERE src.name='soc' AND dst.name='s2p' RETURN p LIMIT 20` with a constrained, canonical edge allowlist. | NOT PROVEN: no cross-domain topology is present. | Run P6.3b/P6.3c and require one AGE traversal. |
| 8 | “Conservation across copilots” | `MATCH (cs:ConservationStatus)-[:SUMMARIZES_DOMAIN]->(d:Domain) WITH d, cs ORDER BY cs.computed_at DESC, cs.status_id DESC WITH d, collect(cs)[0] AS latest RETURN d.name, latest.V, latest.q, latest.alpha, latest.status, latest.computed_at` | NOT PROVEN: zero conservation snapshots across all five domains. | Run P6.3a; require at least one snapshot per domain. |

The query for claim 8 must use `computed_at`; it must not infer recency from
`status_id`. The current scorer makes `status_id` deterministic per Decision
(`scorer.py:790-801`), so multiple snapshots can exist across Decisions.

## 3. TransferPattern Design

### 3.1 Current lifecycle and the missing graph event

There are currently three distinct fingerprint/transfer operations:

1. `CompoundingScorer.fingerprint()` computes factor quality from verified
   Decisions and optionally persists a `Fingerprint` node through
   `_persist_fingerprint` (`scorer.py:712-724`, `941-1020`). There is no
   `save_fingerprint()` or `load_fingerprint()` method on the scorer; the
   scorer reads verified Decisions and writes a fingerprint snapshot.
2. `copilot_sdk.backend.transfer.save_fingerprint()` exports a domain payload
   to `<domain>.json` (`backend/transfer.py:22-41`), and
   `load_fingerprints_with_warnings()` imports all JSON files
   (`backend/transfer.py:49-69`). This is file transfer, not graph transfer.
3. `CompoundingScorer.warm_start()` applies registry patterns to the target
   centroid tensor. It learns the target from the preset and source copilot
   metadata from each pattern (`scorer.py:1093-1139`). This is the first point
   where source and target are simultaneously known, but it currently writes
   only a legacy centroid save and warm-start metadata (`scorer.py:1139-1155`).

Therefore, a TransferPattern should be emitted at successful import/application
time, not merely when a source fingerprint is exported. The source domain is
the fingerprint/pattern provenance; the target domain is the receiving scorer's
`self._domain`. A source-only export cannot create the required two-domain
graph edges.

### 3.2 Two transfer semantics, one canonical node label

`TransferPattern` in JM §4.1 requires `source_rule`, `target_rule`, and
`factor_mapping` (`judgment_memory_v2_7.md:296-301`). The current in-memory
`TransferPattern` dataclass instead contains `source_copilot`, `pattern_type`,
`category`, `action`, `win_rate`, `centroid_delta`, and `confidence`
(`copilot_sdk/transfer/registry.py:13-24`). These are not identical concepts.

Use one canonical graph label with two explicit `pattern_type` values:

- `factor_quality_transfer`: derived from a source `Fingerprint`; maps source
  factor names/statistics to target factor names; `source_rule` and
  `target_rule` are null unless a rule was also involved.
- `procedural_rule_transfer`: derived from an `EvolutionEvent`; carries
  `source_rule`, `target_rule`, and any factor mapping used to adapt the rule.

Both are cross-copilot procedural/judgment provenance and need the same
`FROM_DOMAIN`, `TO_DOMAIN`, and `DERIVED_FROM` edges. They must not be merged
semantically: a low-sigma factor transfer is not evidence that an AgentEvolver
rule was promoted.

Proposed write contract (Protocol V2 extension):

```python
write_transfer_pattern(
    pattern_id: str,
    source_domain: str,
    target_domain: str,
    source_rule: str | None,
    target_rule: str | None,
    factor_mapping: dict[str, Any],
    confidence: float,
    validation_status: str,
    conservation_status: str,
    source_fingerprint_id: str | None = None,
    evolution_event_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None
```

The implementation must create `TransferPattern`, match or create the two
Domain anchors, and create exactly these canonical edges:

```cypher
MATCH (tp:TransferPattern {pattern_id: '...'}),
      (src:Domain {domain_id: 'source'}),
      (dst:Domain {domain_id: 'target'})
CREATE (tp)-[:FROM_DOMAIN]->(src)
CREATE (tp)-[:TO_DOMAIN]->(dst)
```

The `DERIVED_FROM` edge must be created only when an `EvolutionEvent` exists:

```cypher
MATCH (tp:TransferPattern {pattern_id: '...'}),
      (e:EvolutionEvent {event_id: '...'})
CREATE (tp)-[:DERIVED_FROM]->(e)
```

The AGE codebase uses MATCH-then-CREATE guarded edge patterns rather than
`MERGE`; the new writer must follow that convention. `EvolutionEvent` itself
already exists in Protocol V2 and in AGE, including `event_type`, `rule_name`,
`variant_id`, source fields, metrics, and `created_at`
(`protocol.py:270-284`, `age_graph_store.py:1593-1644`).

### 3.3 Idempotency and revisions

Use a deterministic content identity, not the registry's random
`XC-...-uuid` fallback (`registry.py:171-173`):

```text
pattern_id = TP-<sha256(source_domain | target_domain | pattern_type |
                         source_artifact_id | target_rule | canonical_mapping)[:32]>
```

Repeated import of the same source fingerprint and mapping is one idempotent
TransferPattern. A changed source fingerprint or mapping is a new immutable
revision, because the JM schema has `created_at` but no `updated_at`. The
logical relationship can be grouped by metadata `transfer_key`; the graph node
identity remains revision-specific. A conflicting payload under the same
`pattern_id` must fail closed, matching existing AGE idempotency behavior for
conservation, fingerprints, and evolution events.

### 3.4 Evolution-event dependency

`EvolutionEvent` is implemented, but no current code creates a
`TransferPattern` or transfer edges (`age_graph_store.py:1593-1644`; the
inspected file has no `TransferPattern` writer). A pattern could technically
be created without `DERIVED_FROM`, but that would fail JM §4.2 conformance.
For Phase 6 validated patterns, create a dedicated `EvolutionEvent` first
(for example `event_type='transfer_candidate'`) and require its ID when the
TransferPattern is written. Draft, unvalidated opportunities may remain in
the detector/registry and must not be advertised as graph-proven transfer.

## 3.5 Live Graph State (2026-07-29 census)

`graph_census_v2.py` was run against live `soc_graph` on 2026-07-29. This is
the Batch B baseline; it is not evidence that the Phase 6 claims pass.

| Artifact | SOC | S2P | Trading | Purchasing | DataOps | Census interpretation |
|---|---:|---:|---:|---:|---:|---|
| Decision nodes | 4862 | 25110 | 1480 | 1100 | 721 | Seed/history data exists |
| Conservation snapshots | 0 | 0 | 0 | 0 | 0 | J6 persistence has not run against live AGE |
| Centroid checkpoints | 0 | 161 | 0 | 0 | 120 | Only S2P/DataOps have live checkpoints |
| Domain anchors | yes | no | yes | no | no | Anchors depend on J6 artifact writes |
| Fingerprints | 0 | 0 | 1 | 0 | 0 | Trading has one fingerprint |
| Evidence receipts | 0 | 161 | 0 | 0 | 0 | Only S2P has receipts |
| Outcomes | 2 | 173 | 544 | 680 | 389 | Outcome history exists |
| Evolution events | 0 | 0 | 0 | 0 | 1 | One DataOps event |

The graph contains 39211 total nodes, zero monetary `DomainContext` entities,
zero `TransferPattern` nodes, and no complete five-domain artifact set. The
empty artifacts are expected because no copilot has run a live AGE `learn()`
cycle since J6 persistence shipped. Conservation, checkpoint, fingerprint,
receipt, and anchor creation therefore remain execution prerequisites, not
assumptions. P6.3a is mandatory before P6.4 or P6.6.

## 4. Global Query Design

### 4.1 Latest conservation per domain

Current `ConservationStatus` stores `computed_at` as an epoch timestamp and
stores `V`, `q`, `alpha`, `theta_min`, verified/correct counts, status, and
policy version (`age_graph_store.py:1116-1160`). Domain anchors are ensured
and linked by `SUMMARIZES_DOMAIN` (`age_graph_store.py:1028-1071`).

Add a typed global read method rather than duplicating Cypher in callers:

```python
get_latest_conservation_statuses(
    domains: list[str] | None = None,
) -> list[dict[str, Any]]
```

Draft query:

```cypher
MATCH (cs:ConservationStatus)-[:SUMMARIZES_DOMAIN]->(d:Domain)
WHERE d.name IN ['soc','s2p','trading','purchasing','dataops']
WITH d, cs
ORDER BY cs.computed_at DESC, cs.status_id DESC
WITH d, collect(cs)[0] AS latest
RETURN d.name AS domain,
       latest.V AS V, latest.q AS q, latest.alpha AS alpha,
       latest.theta_min AS theta_min, latest.status AS status,
       latest.computed_at AS computed_at,
       latest.policy_version AS policy_version
ORDER BY domain
```

The implementation must validate that `latest.domain = d.domain_id` and must
return an explicit missing-domain row or a documented empty result. It must
not substitute zero for a graph failure.

### 4.2 Global IKS trajectory

V2 checkpoints store `iks`, `created_at`, `decision_id` in metadata, category,
action, counts, shape, and factor-name hash (`age_graph_store.py:1271-1339`).
The current generic `get_centroid_checkpoints()` query orders by `created_at`
but filters `checkpoint_id IS NULL` (`age_graph_store.py:2501-2515`), which
selects legacy checkpoints and excludes V2 checkpoints. Phase 6 must use a
new V2-aware query and explicitly deduplicate the intentional legacy/V2 pair.

Proposed method:

```python
get_iks_trajectory(
    domains: list[str] | None = None,
    start: float | None = None,
    end: float | None = None,
) -> list[dict[str, Any]]
```

Draft query:

```cypher
MATCH (c:CentroidCheckpoint)
WHERE c.domain IN ['soc','s2p','trading','purchasing','dataops']
  AND c.iks IS NOT NULL
WITH c
ORDER BY c.domain, c.created_at ASC, c.checkpoint_id ASC
RETURN c.domain AS domain,
       c.created_at AS created_at,
       c.iks AS iks,
       c.decisions_count AS decisions_count,
       c.verified_count AS verified_count,
       c.checkpoint_id AS checkpoint_id,
       c.factor_names_hash AS factor_names_hash
```

The read contract must identify whether a row is V2 (`schema_version='protocol_v2'`)
or legacy and deduplicate only records representing the same decision and
checkpoint event. It must never drop a genuine V2 checkpoint merely because
its `checkpoint_id` is non-null.

### 4.3 Transfer traversal

After pattern persistence, the canonical traversal for a validated
procedural-rule transfer is:

```cypher
MATCH (tp:TransferPattern)-[:FROM_DOMAIN]->(src:Domain),
      (tp)-[:TO_DOMAIN]->(dst:Domain),
      (tp)-[:DERIVED_FROM]->(e:EvolutionEvent)
WHERE src.name = 'soc' AND dst.name = 's2p'
RETURN tp.pattern_id, tp.pattern_type, tp.confidence,
       tp.validation_status, e.event_id, e.event_type
ORDER BY tp.created_at DESC
```

The Phase 6 runner must execute this against AGE directly, without reading a
JSON registry or joining results from copilot APIs. A factor-quality transfer
cannot use this traversal until its provenance contract is resolved: current
code has no EvolutionEvent producer for a factor fingerprint transfer and the
JM schema does not define a Fingerprint-to-TransferPattern lineage edge.

## 5. `demo.py` Changes

### 5.1 Current `--status`

`cmd_status()` currently prints a boxed header, AGE/PostgreSQL and WSL2
connectivity, then one row per selected copilot containing backend/frontend
status, the health-response domain, and an `[AGE]` marker when configured
(`demo.py:566-595`). It checks AGE connectivity but does not query
`soc_graph`, count domains, or execute a cross-copilot traversal.

The launcher knows SOC and DataOps graph configuration objects and the AGE
graph environment (`demo.py:117-118`, `127-187`), but Trading, Purchasing,
and S2P entries do not independently expose graph metadata in the status
table. This is insufficient as a Phase 6 proof.

### 5.2 Proposed output

Add a static/configuration line immediately after AGE connectivity:

```text
  Shared judgment graph  soc_graph  domains: soc,s2p,trading,purchasing,dataops
```

Then, when AGE is reachable, run a read-only `graph_status` query and print:

```text
  Graph proof             LIVE  decisions=<n> domains=<5> transfer_edges=<n>
```

If AGE is unavailable, print `UNAVAILABLE` rather than zero. The static line
may be printed without starting any backend because GraphConfig/environment
metadata is already loaded during launcher initialization; live counts and
transfer-edge proof require AGE connectivity. Backend health rows remain
unchanged.

## 6. Implementation Plan

| Step | Work | Depends | Effort | Exit gate |
|---:|---|---|---:|---|
| P6.0 | Add Protocol V2 transfer write/read contracts and typed result models; define `pattern_type`, revision identity, and domain validation. | None | 1 day | Protocol conformance signatures documented and tested. |
| P6.1 | Implement AGE/SQLite/InMemory TransferPattern persistence where local adapters are needed; create Domain anchors and canonical transfer edges with guarded MATCH-then-CREATE. | P6.0 | 2 days | Idempotent node/edge topology tests. |
| P6.2 | Add the factor-quality TransferPattern producer at the successful warm-start application boundary; keep JSON import/export as non-authoritative migration compatibility. Add procedural EvolutionEvent lineage only when a real AgentEvolver producer exists. | P6.1 | 2–3 days | Source/target/domain, deterministic hash, partial-failure, and provenance tests; no synthetic rule event. |
| P6.3 | Add latest conservation and V2-aware IKS global query methods; add deduplication and explicit unavailable/error behavior. | P6.0 | 1–2 days | Five-domain snapshot/trajectory query tests. |
| P6.3a | Start AGE and all five backends, run at least five score/learn cycles per domain, rerun `graph_census_v2.py`, and remediate until every domain has decisions, conservation, checkpoint, anchor, fingerprint, and receipt artifacts. | P6.3 | 0.5 day | Census has no empty required artifact cell and exactly five anchors. |
| P6.3b | Define and seed the canonical $604K scenario with `scripts/seed_604k_scenario.py`; create SAP, Celonis, and operations DomainContext nodes and cross-domain ABOUT edges. | P6.3a | 1 day | Claim 3 computes 604000.0 USD from graph data. |
| P6.3c | Trigger at least one real warm-start import from a fingerprinted source domain and verify P6.2 TransferPattern emission. | P6.3a | 0.25 day | Census has a validated TransferPattern and canonical edges. |
| P6.4 | Implement the resolved $604K and 315-value mappings and the eight §2 claim queries using the concrete AGE-safe contracts in §8.2.4. | P6.1, P6.3, P6.3a, P6.3b, P6.3c | 2–3 days | Every claim returns graph-backed evidence from live AGE only, with explicit unavailable failure. |
| P6.5 | Add `demo.py --status` static shared-graph indicator and optional live graph proof line. | P6.3, P6.4 | 0.5 day | Status output contract tests; unavailable state is explicit. |
| P6.6 | Run five-domain AGE integration, provenance, idempotency, no-fixture, and Playwright/demo gates. | P6.2–P6.5, P6.3a–P6.3c | 2 days | JM Phase 6 gate: every §2 claim has a working query. |

## 7. Test Plan

1. **Protocol/store conformance:** every adapter accepts the transfer contract,
   rejects invalid domains, and preserves deterministic IDs.
2. **Topology:** write one factor-quality and one procedural TransferPattern;
   assert `FROM_DOMAIN`, `TO_DOMAIN`, and `DERIVED_FROM` point to the correct
   nodes. Repeat the write and assert no duplicate edges.
3. **Revision behavior:** repeat the same source artifact/mapping and assert
   one node; change the source fingerprint revision and assert a new immutable
   pattern with the same logical `transfer_key`.
4. **Lifecycle:** warm-start from SOC into S2P and assert successful applied
   patterns have both domains, target category/action mapping, and validation
   status. Require EvolutionEvent provenance only for procedural transfers;
   factor-quality transfers must not fabricate rule metadata.
5. **Global conservation:** seed mixed-domain snapshots with out-of-order
   timestamps and assert latest-per-domain selection; inject a graph error and
   assert an explicit failure rather than zero rows.
6. **Global IKS:** seed legacy and V2 checkpoints, assert chronological V2
   trajectory and intentional duplicate handling, including equal timestamps.
7. **Claim registry:** run every §2 query against a clean shared AGE graph;
   reject fixture files, API response joins, hardcoded monetary totals, and
   missing domain anchors.
8. **Demo:** test `--status` with AGE up, AGE down, and no backends. Static
   shared-graph configuration remains visible; live proof says unavailable
   when AGE cannot be reached.
9. **Five-domain isolation:** ensure a transfer query is cross-domain only
   through explicit TransferPattern edges and that ordinary Decision reads
   remain domain-scoped.

## 8. Open Questions / Blockers

**Status: superseded.** The historical questions below are retained for
traceability only. Their resolved implementation decisions are authoritative
in §8.2; none of the entries below remains an open blocker.

The original eight questions are closed below as locked, revised, or deferred
decisions. The decisions are deliberately narrower than the proposals where
the current code does not support the proposed semantics.

1. **Canonical value schema — DEFERRED TO BATCH B.** The inspected JM and AGE
   files do not define the SAP/Celonis/operations properties needed to prove
   `$604K` (`judgment_memory_v2_7.md:138-152`). No claim query may be marked
   passing until those properties and their owners are specified.

2. **“315 values” meaning — DEFERRED TO BATCH B.** The number is not mapped
   to a current node/property contract. It must be defined before the claim
   registry can be approved; a count inferred from factor vectors or
   checkpoints would be an unsupported interpretation.

3. **Factor transfer rule fields — REVISED.** `pattern_type` remains an
   extensibility field, but Batch A implements only `factor_quality_transfer`.
   `procedural_rule_transfer` is deferred until an AgentEvolver producer exists.
   The registry currently has `pattern_type` but no rule fields at all
   (`copilot_sdk/transfer/registry.py:13-24`, `:45-58`), while the only current
   transfer detector compares fingerprints/factor sigma (`copilot_sdk/backend/transfer.py:72-138`).
   The JM schema lists `source_rule` and `target_rule` but does not state their
   nullability (`judgment_memory_v2_7.md:296-301`). They must be explicitly
   nullable for factor-quality records in the JM contract; inventing a rule
   name would create false procedural provenance. Procedural records require
   non-null rule identity and genuine EvolutionEvent lineage.

4. **Revision retention — LOCKED: immutable content-addressed revisions.**
   The registry's fallback ID is random (`copilot_sdk/transfer/registry.py:73-78`,
   `:171-173`), so Phase 6 must replace it for graph records with a canonical
   content hash over source/target domains, pattern type, source artifact
   identity, mapping, and semantic payload. AGE treats an identical existing
   payload as idempotent and raises on a conflicting identifier for
   ConservationStatus, Fingerprint, CentroidCheckpoint, and EvolutionEvent
   (`age_graph_store.py:1103-1166`, `:1194-1269`, `:1271-1339`, `:1593-1644`).
   Therefore timestamp-based identity or in-place overwrite is rejected.
   A retention/archive policy is still required because changed content creates
   a new immutable node.

5. **V2 checkpoint reader — REVISED: evolve the existing read contract, do
   not create an unrelated parallel method.** The AGE implementation filters
   `checkpoint_id IS NULL`, orders by `created_at`, and therefore excludes V2
   checkpoints (`age_graph_store.py:2501-2515`). The same method is used by
   scorer trajectory and many existing callers (`scorer.py:1058-1066`; see
   the reader inventory in §9). Add an explicit V2/all-kind option to the
   existing contract while preserving the legacy default, or add a named
   trajectory method backed by that option. A separate store-only method would
   duplicate the protocol split and leave current callers silently on legacy
   data.

6. **Five-domain live environment — REVISED.** The proof runner must call
   `GraphConfig.load(domain, profile="production")` for each domain, not parse
   TOML ad hoc. The TOML maps all five domains to `soc_graph`
   (`graph_config.toml:8-54`), and the loader validates the domain/backend/graph
   and requires DSN for AGE (`graph_config.py:64-157`, `:221-243`). A backend is
   not required, but the runner still needs AGE DSN/credentials and graph name
   through the config environment. `demo.py --status` currently checks AGE and
   backend health only; it does not perform shared-graph proof queries
   (`demo.py:566-595`).

7. **Evolution event source — REVISED.** Do not create
   `event_type="transfer_applied"` for every warm-start. `write_evolution_event`
   requires `rule_name` and `variant_id` (`protocol.py:270-284`), and AGE stores
   them as required properties without an enum (`age_graph_store.py:1593-1644`).
   `warm_start()` knows the target preset and source copilot metadata, and can
   partially apply patterns, but has no rule name, variant ID, shadow batch, or
   AgentEvolver result (`scorer.py:1106-1157`). Factor transfers therefore do
   not get a synthetic EvolutionEvent or `DERIVED_FROM` edge. Procedural
   transfers get that edge only after a real AgentEvolver producer supplies the
   required context. This is a Batch B provenance blocker, not permission to
   write fake events.

8. **Authority transition — REVISED.** JSON remains a compatibility input in
   Batch A, but is explicitly non-authoritative. `SharedPatternRegistry` loads
   its optional JSON file on construction (`registry.py:61-68`, `:131-151`),
   and `warm_start()` consumes registry patterns and applies them to the target
   (`scorer.py:1106-1129`). The graph currently has no TransferPattern protocol
   method or AGE writer (`protocol.py:163-308`; `age_graph_store.py` has no such
   implementation). Batch B must add a graph read/write contract and make the
   proof runner authoritative from AGE; only then may JSON be demoted to
   migration fallback. Divergence between graph and JSON must be reported, not
   silently reconciled.

### 8.1 — Locked Design Decisions

The following are the decisions that are implementation-ready for Batch A:

| Decision | Evidence | Alternative considered | Risk |
|---|---|---|---|
| Emit a transfer audit record only after a pattern is successfully applied; one record per applied pattern, not one per request. | `warm_start()` resolves the target from the preset and obtains source-filtered patterns (`scorer.py:1106-1113`); it computes `applied_transfer_patterns` before changing centroids (`scorer.py:1115-1132`), and the registry records target metadata (`registry.py:99-123`). | Emit at request entry or create one batch record. Rejected because partial application is possible and failed patterns must not be recorded as applied. | A crash after centroid mutation but before graph write can leave an unrecorded application; use the outbox/transaction design in Batch B. |
| Use one TransferPattern label with `pattern_type`, but implement only `factor_quality_transfer` now. | Registry has `pattern_type` (`registry.py:13-24`); current detector is fingerprint/factor based (`backend/transfer.py:72-138`); no AgentEvolver transfer producer was found. | Implement two producers immediately. Rejected because procedural context does not exist. | Future procedural schema may need an authority migration. |
| Permit null rule fields only for factor-quality records after the JM schema is amended; require rule fields for procedural records. | JM names rule fields (`judgment_memory_v2_7.md:296-301`), but registry lacks them (`registry.py:13-24`). | Use synthetic rule names. Rejected as false provenance. | JM authority update is a prerequisite for a fully canonical factor record. |
| Use deterministic content hashes for immutable pattern revisions. | AGE idempotency/conflict behavior is explicit for existing artifact writers (`age_graph_store.py:1103-1166`, `:1194-1269`, `:1271-1339`, `:1593-1644`). | Timestamp IDs or overwrite. Rejected because retries would duplicate or mutate audit history. | High transfer volume requires retention and archival. |
| Preserve legacy checkpoint reads by default and add an explicit all/V2-aware read mode to the existing checkpoint contract. | AGE excludes V2 with `checkpoint_id IS NULL` (`age_graph_store.py:2501-2515`); scorer and many tests call the existing method. | A separate store-only `get_v2_checkpoints()` method. Rejected as parallel protocol drift unless compatibility prevents an optional mode. | Existing callers could change behavior if the default is altered; default must remain legacy until migrated. |
| Use `GraphConfig.load()` plus direct AGE connectivity for the proof runner. | All five TOML sections use `soc_graph` (`graph_config.toml:8-54`); loader is standalone and validates AGE requirements (`graph_config.py:64-157`, `:221-243`). | Start all five backends or parse TOML manually. Rejected because it adds runtime dependencies and bypasses canonical validation. | Missing DSN/credentials must produce explicit unavailable, never zero. |
| Do not create a synthetic EvolutionEvent for a factor transfer; create event lineage only for genuine procedural transfers. | Protocol requires rule/variant fields (`protocol.py:270-284`); warm-start lacks them (`scorer.py:1106-1157`). | Use `transfer_applied` with fabricated rule/variant values. Rejected as misleading audit data. | Factor lineage requires a future JM-approved provenance edge or an explicit semantic event contract. |
| Keep JSON as non-authoritative compatibility input until graph persistence/readback and the Phase 6 proof pass. | JSON is loaded by the registry (`registry.py:61-68`, `:131-151`) and consumed by warm-start (`scorer.py:1106-1129`); no graph transfer contract exists yet. | Make the graph authoritative immediately. Rejected because there is no current graph reader/writer. | Temporary graph/JSON divergence must be surfaced and resolved before gate closure. |

**Batch boundary:** Batch A can implement the transfer protocol/store schema,
content-addressed idempotency, checkpoint read mode, GraphConfig-based global
queries, and explicit factor/procedural provenance contracts. Batch B owns
warm-start emission, graph-authoritative reads, EvolutionEvent lineage,
claim-property mapping, demo proof output, and the five-domain live gate.

## 9. Reading Log

All requested files were read completely before this design was written.

| File | Evidence ranges used |
|---|---|
| `copilot-sdk/docs/design/judgment_memory_v2_7.md` | §2 `:138-152`; §4.1 `:220-341`; §4.2 `:343-375`; Phase 6 `:905-919`; §12a `:962-1024`; §12b `:1028-1046` |
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | fingerprint `:712-724`; persistence coordinator `:726-886`; checkpoint/trajectory `:1026-1068`; warm-start `:1093-1163`; checkpoint writer `:1360-1432` |
| `copilot-sdk/copilot_sdk/graph/protocol.py` | GraphStore `:16-138`; traversal `:140-160`; Protocol V2 `:163-308`; L5 definitions `:312-382` |
| `ci-platform/ci_platform/graph/age_graph_store.py` | domain anchor/summary edges `:1028-1101`; conservation `:1103-1192`; fingerprint `:1194-1269`; checkpoint `:1271-1367`; evolution `:1593-1660`; legacy/V2 checkpoint reads `:2323-2352`, `:2501-2515` |
| `copilot-sdk/demo.py` | graph config and copilot registry `:102-187`; health/status helpers `:197-226`, `:566-595`; diagnostic contract `:407-437` |
| `copilot-sdk/copilot_sdk/transfer/registry.py` | TransferPattern and registry `:13-24`, `:61-78`, `:99-129`, `:131-173` |
| `copilot-sdk/copilot_sdk/backend/transfer.py` | JSON export/import `:22-69`; transfer detection `:72-138` |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py` | warm-start request/application path `:110-145`; registry pattern selection `:343-362` |
| `copilot-sdk/copilot_sdk/config/graph_config.py` | standalone load `:64-157`; validation `:221-243` |
| `copilot-sdk/graph_config.toml` | five copilot sections and shared graph `:8-54` |

DESIGN_DOCUMENT: `copilot-sdk/docs/implementation_plans/phase6_design.md`

## 8.2 Batch B Implementation Specification (locked closure)

This section supersedes the unresolved/deferred wording in section 8. Batch B
may not mark a claim proven unless the query below returns its stated evidence
from the shared AGE graph. AGE restrictions apply: literals are inlined, no
`MERGE`, no `datetime()`, no `CASE WHEN`, and no fixture/API joins.

### 8.2.1 Canonical meaning of the $604K claim

JM v2.7 §2 calls this exactly the "$604K cross-graph finding" and classifies
it as a demo claim requiring SAP x Celonis x operations traversal
(`judgment_memory_v2_7.md:138-152`). It is a scenario outcome, not a platform
constant. The graph contract is therefore:

* `DomainContext` has `entity_id`, `entity_type`, `domain`, `source_system`,
  `value_amount`, `value_currency`, `value_basis`, and `metadata`.
* Monetary contexts use entity types `sap_change`, `celonis_process`, and
  `operations_context`. `value_amount` is a non-negative numeric amount in
  `value_currency`; `value_basis` identifies the period and metric.
* Existing `link_entity` only accepts the four identity arguments and does not
  create or update DomainContext properties (`age_graph_store.py:1453-1539`).
  The Batch B seed/materialization step must create these properties before
  creating the `ABOUT` edges. It must reject missing currency, basis, or a
  negative amount.
* `$604K` is computed, never inserted as a literal. The proof query sums the
  distinct monetary contexts participating in one cross-domain finding:

```cypher
MATCH (sap:DomainContext {entity_type: 'sap_change'})<-[:ABOUT]-(s:Decision),
      (sap)<-[:ABOUT]-(o:Decision),
      (cel:DomainContext {entity_type: 'celonis_process'}),
      (ops:DomainContext {entity_type: 'operations_context'})
WHERE s.domain <> o.domain
  AND cel.entity_id = sap.metadata_celonis_entity_id
  AND ops.entity_id = sap.metadata_operations_entity_id
  AND sap.value_currency = 'USD'
  AND cel.value_currency = 'USD'
  AND ops.value_currency = 'USD'
RETURN sap.entity_id AS finding_id,
       sum(DISTINCT sap.value_amount)
       + sum(DISTINCT cel.value_amount)
       + sum(DISTINCT ops.value_amount) AS computed_value,
       collect(DISTINCT s.domain) AS source_domains,
       collect(DISTINCT o.domain) AS other_domains
```

The claim passes only when one row has all three entity types, at least two
Decision domains, and `computed_value = 604000.0` (numeric equality from graph
data, not a query constant). If the approved scenario seed does not produce
that value, the claim is `NOT_PROVEN`, not coerced to pass. Current product
documents contain other value stories (for example DataOps $180K/$200K/$90K),
but no authoritative $604K seed; Batch B must add the approved scenario data
through the graph seed contract before the gate.

### 8.2.2 Canonical meaning of 315 values

JM §1.1 and §2 mean 315 learned values **per copilot**, not a five-copilot
total (`judgment_memory_v2_7.md:138-152`). The current preset shapes are:

| Domain | C | A | D | centroid C x A x D | DK D | current total |
|---|---:|---:|---:|---:|---:|---:|
| soc | 6 | 4 | 6 | 144 | 6 | 150 |
| s2p | 5 | 5 | 8 | 200 | 8 | 208 |
| trading | 5 | 4 | 10 | 200 | 10 | 210 |
| purchasing | 5 | 4 | 7 | 140 | 7 | 147 |
| dataops | 6 | 5 | 8 | 240 | 8 | 248 |

The formula is `learned_values = product(shape) + D`. Therefore 315 is a
stale narrative number under the current presets; no current copilot has 315.
The proof reports the computed value and fails the legacy-number assertion
unless a future approved preset actually yields 315.

`CentroidCheckpoint.shape` is the authoritative tensor shape; the node also
stores `decisions_count`, `verified_count`, and `factor_names_hash`
(`age_graph_store.py:1271-1367`). The AGE proof query is:

```cypher
MATCH (c:CentroidCheckpoint)
WHERE c.shape IS NOT NULL AND c.domain IN ['soc','s2p','trading','purchasing','dataops']
RETURN c.domain AS domain, c.shape AS shape,
       c.factor_names_hash AS factor_names_hash,
       size(c.shape) AS rank
ORDER BY domain, c.created_at DESC
```

The runner parses the stored shape list, computes its product, obtains D from
the stored factor-name list or the preset contract, and returns
`product(shape)+D`. It must not compare a hardcoded 315 to a count of nodes.

### 8.2.3 P6.2 warm-start emission

The insertion point is immediately after successful centroid assignment at
`copilot_sdk/scoring/scorer.py:1130-1132`, before the checkpoint save. At that
point `applied_transfer_patterns`, the target domain, target preset shape,
blend score, and graph store are available (`scorer.py:1115-1141`). For each
applied pattern, write one `TransferPattern` with:

* `source_domain`: `pattern.metadata['source_domain']`, otherwise
  `pattern.source_copilot`;
* `target_domain`: `self._domain`;
* `pattern_type`: `factor_quality_transfer`;
* `source_fingerprint_id`: required metadata key
  `source_fingerprint_id`; absent means the graph emission is skipped and the
  result records `unproven_missing_source_fingerprint`;
* `factor_mapping`: canonical sorted JSON mapping source factor names to
  target names, from `pattern.metadata['factor_mapping']`; absent means `{}`
  and validation status `partial`;
* `confidence`: the already adjusted `pattern.confidence`;
* `conservation_status`: latest target-domain status if available, otherwise
  the explicit string `unavailable` (never GREEN);
* `source_rule`, `target_rule`, and `evolution_event_id`: `None` for this
  factor-quality pattern. No synthetic procedural event is allowed.

The deterministic identity is:

```text
TP-<sha256(
  source_domain + '|' + target_domain + '|' + pattern_type + '|' +
  source_fingerprint_id + '|' + (target_rule or '') + '|' +
  canonical_json(factor_mapping)
)[:32]>
```

The input fields are normalized strings and canonical JSON with sorted keys
and compact separators. A pattern that fails graph validation is not emitted;
other patterns continue. The return payload adds `emitted`, `skipped`, and
`emission_errors` so applying three of five remains explicit. Graph access is
already available as `self._graph_store`; no new parameter is needed.

### 8.2.4 Complete claim registry

The following table is the implementation contract. A missing row is a failed
claim, never a zero-valued success.

| # | Exact JM claim | AGE proof and pass condition | Data requirement |
|---:|---|---|---|
| 1 | One engine, one graph | `MATCH (d:Decision) RETURN count(DISTINCT d) AS n, collect(DISTINCT d.domain) AS domains`; pass when graph is `soc_graph`, all five domains appear, and no configured domain uses another graph | Five-domain GraphConfig and live Decision rows |
| 2 | Cross-graph attention | `MATCH (a:Decision)-[:ABOUT]->(e:DomainContext)<-[:ABOUT]-(b:Decision) WHERE a.domain <> b.domain RETURN count(DISTINCT e.entity_id) AS shared`; pass when `shared > 0` and both domains are returned | Shared DomainContext with two domain-scoped Decision edges |
| 3 | $604K cross-graph finding | Query in 8.2.1; pass only on computed `604000.0` with SAP/Celonis/operations evidence | Approved monetary scenario seed |
| 4 | Pattern transfer SOC->S2P->DataOps | `MATCH (tp:TransferPattern)-[:FROM_DOMAIN]->(s:Domain), (tp)-[:TO_DOMAIN]->(t:Domain) WHERE s.name='soc' AND t.name IN ['s2p','dataops'] RETURN count(tp) AS n`; pass when each destination has a validated pattern and required provenance | TransferPattern plus Domain anchors and edges |
| 5 | 315 values that compound | Query in 8.2.2; pass when computed per-domain totals equal the current preset formula and are reported, with legacy 315 marked stale | CentroidCheckpoint shape and factor names |
| 6 | You cannot fork judgment | `MATCH (d:Decision) WHERE d.domain IN ['soc','s2p','trading','purchasing','dataops'] RETURN count(DISTINCT d.decision_id) AS ids, count(d) AS rows`; pass when `ids = rows`, domains are exact, and no SQLite source participates | Unique shared-graph Decision IDs |
| 7 | One traversal, one answer | `MATCH (s:Decision)-[:ABOUT]->(e:DomainContext)<-[:ABOUT]-(t:Decision) WHERE s.domain <> t.domain RETURN s.domain AS source, t.domain AS target, e.entity_id AS entity`; pass when one AGE query returns the complete cross-domain row | DomainContext ABOUT topology |
| 8 | Conservation across copilots | `MATCH (cs:ConservationStatus)-[:SUMMARIZES_DOMAIN]->(d:Domain) RETURN d.name AS domain, cs.status AS status, cs.V AS V, cs.computed_at AS computed_at ORDER BY d.name, computed_at DESC`; pass when each domain has a latest snapshot, non-null V/status, and latest selection is deterministic | At least one snapshot per domain; zero-snapshot domains are `UNAVAILABLE` and fail the live gate |

Queries use inline literals and avoid unsupported AGE constructs. The claim
runner requires `AGE_INTEGRATION=1`; it never reads fixtures or backend API
responses.

### 8.2.5 P6.5 `demo.py --status`

After the existing AGE connectivity row (`demo.py:566-595`), print exactly:

```text
  Shared judgment graph  soc_graph  domains: soc,s2p,trading,purchasing,dataops
  Graph proof             LIVE      decisions=<n> domains=<n> transfer_edges=<n>
```

The first line is configuration-only and is printed without backends. The
second line runs one read-only AGE query for Decision/domain counts and one
TransferPattern edge count; it requires AGE connectivity but not running
copilot servers. When AGE is unavailable, print:

```text
  Graph proof             UNAVAILABLE (AGE not reachable)
```

Never print zero for an unavailable graph. `transfer_edges=0` is valid when
P6.2 has not emitted a validated pattern.

### 8.2.6 P6.6 five-domain live gate

The gate requires AGE reachable, `graph_config.toml` resolving all five
domains to the same DSN and `soc_graph`, and all five backend health endpoints
responding. It then runs the eight claim queries, latest conservation query,
transfer idempotency query, and domain-isolation query. Playwright is required
only for the comprehensive release run; the AGE claim gate itself does not
require browsers. A domain with zero checkpoints, transfers, or conservation
snapshots returns explicit `UNAVAILABLE` and fails P6.6 rather than passing
with an empty result. Every failure includes domain, query name, and AGE error.

## 8.3 Remaining Deferred Items

1. Physical archival/deletion policy for `TransferPattern` nodes is deferred
   to the retention review; Phase 6 keeps immutable revisions indefinitely and
   exposes them through the graph query.
2. Procedural-rule TransferPatterns and `DERIVED_FROM EvolutionEvent` remain
   deferred until a real AgentEvolver transfer producer and JM-approved rule
   fields exist. Factor-quality records must not fabricate that provenance.
3. Application-specific SOC/S2P warm-start endpoint tests are required in the
   Batch B implementation test plan; the SDK scorer tests alone are
   insufficient evidence for those adapters.

No other Batch B blocker remains. The decisions above are the authority for
P6.2, P6.4, P6.5, and P6.6 implementation.

## 10. Pre-Gate Verification Checklist

P6.6 must not be attempted until every item below passes:

- [ ] `graph_census_v2.py` shows Decisions in all five domains.
- [ ] `graph_census_v2.py` shows at least one ConservationStatus per domain.
- [ ] `graph_census_v2.py` shows at least one CentroidCheckpoint per domain.
- [ ] `graph_census_v2.py` shows exactly five Domain anchors.
- [ ] `graph_census_v2.py` shows at least one Fingerprint per domain.
- [ ] `graph_census_v2.py` shows at least one EvidenceReceipt per domain.
- [ ] `graph_census_v2.py` shows at least one TransferPattern.
- [ ] `graph_census_v2.py` shows monetary DomainContext entities.
- [ ] All five copilot backends are started and healthy.
- [ ] `phase6_claim_proof.py --dry-run` reports eight valid queries.
- [ ] `phase6_claim_proof.py --execute` reports at least six PASS; claims 3
      and 4 require P6.3b and P6.3c respectively.
- [ ] `demo.py --status` shows the Shared judgment graph line.
- [ ] `demo.py --status` shows Graph proof LIVE with non-zero counts.

## 11. Operational Sequence for P6.6

Run this sequence in order; each verification is a hard gate:

1. Start AGE: `wsl -u root pg_ctlcluster 17 main start`.
2. Capture the baseline: `python scripts/graph_census_v2.py`.
3. Start all five backends: `python demo.py --no-browser`.
4. Confirm five healthy services: `python demo.py --status`.
5. For each SDK copilot, execute five `/api/score` plus `/api/learn` cycles;
   for SOC use its `/api/alert/analyze` plus outcome flow. This is P6.3a and
   must trigger J6 artifact persistence.
6. Rerun `python scripts/graph_census_v2.py`; remediate empty artifact cells.
7. Run `python scripts/seed_604k_scenario.py --apply`.
8. Rerun the census and verify monetary entities and the 604000.0 aggregate.
9. Run `python scripts/trigger_warm_start.py --domain trading` against a
   fingerprinted source/target pair.
10. Rerun the census and verify TransferPattern count is greater than zero.
11. Run `python scripts/phase6_claim_proof.py --execute`.
12. Run `python demo.py --status` and retain the output as gate evidence.
13. Stop services: `python demo.py --stop`.
14. Review the report: all eight claims PASS, census complete, and shared
    graph proof LIVE.
