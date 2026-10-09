# Backend readback contract — FIX-P4b-2

This is the memory-side contract for REV-P4a's inherited P2-1/P2-2 findings.
`tests/test_backend_conformance.py` is executable evidence for the record,
timestamp, null, ordering, filter and limit rules. It runs against a fresh memory
store through protocol interfaces. It is **not evidence of AGE conformance**.
AGE source and its SDK adapter were inspected but are unchanged in this task.

## Rules and boundaries

- Timestamp shape is field-specific and follows inspected AGE public
  projections: epoch-valued fields remain numeric, while ISO/string-valued
  fields remain strings; missing optional timestamps are `None`. Ordering and
  filters normalize timestamps internally without changing public readback.
- IDs are opaque strings. A missing legacy checkpoint/event ID is `None`;
  a read must not fabricate an identity or rewrite stored data. Generated ID
  prefixes/lengths are not a conformance requirement.
- Optional dictionary fields are present as `None`. Metadata and control-plane
  state are opaque caller-owned payloads, copied without recursively rewriting
  field names, dates or null conventions.
- Decisions: `created_at DESC, decision_id ASC`, with undated legacy decisions
  after dated decisions. Events:
  `timestamp DESC, event_id ASC`. Unbounded checkpoint reads are newest-first;
  bounded reads select the newest N and present that window chronologically,
  preserving existing chart consumers and the current shared backend behavior.
  Equal-time checkpoint IDs sort ascending; legacy checkpoints additionally use
  checkpoint capture time. Legacy checkpoint/event rows without IDs use canonical
  serialized content to resolve remaining ties. Identical rows are indistinguishable.
- Gate consumers explicitly sort verified decisions chronologically before
  selecting trailing degradation windows. Their calculation no longer depends
  on a backend's read presentation. Caller-supplied outcome arrays retain their
  order; timestamp-less legacy adapter rows retain their supplied order.
- The inherited private `_decision_page` hook retains chronological insertion
  order for the existing filtering wrapper's offset pagination. This private
  compatibility boundary is not the public decision-read contract. Replacing
  that wrapper with public protocol paging belongs to FIX-P4b-3.
- Read limits are applied after filters and ordering: zero is empty, a positive
  integer returns at most that many records, explicit `None` is unbounded.
  Event/checkpoint calls with no limit are unbounded.
- **Signature constraint:** `protocol.py` still declares `get_decisions(limit=400)`,
  `list_entity_enrichments(limit=500)` and `get_k_utilities(limit=100)`, with `int`
  annotations. This task forbids changing protocol signatures. Those defaults
  and signatures are retained, although memory now supports explicit `None` at
  runtime. Making omission universally unbounded and making `None` statically
  valid needs a coordinated protocol/adapter change. Tests pass `None` through
  `Any` to expose, rather than hide, this current annotation boundary.
- **Typed enrichment boundary:** `ProvenancedValue.computed_at` and
  `EntityEnrichmentRecord.computed_at` are explicitly `str` in shared dataclasses;
  both backends currently follow that contract. They remain unchanged. A literal
  "all timestamps are floats" contract requires a coordinated change to those
  shared record types and their producers/serializers, not an incompatible
  float masquerading as `str` in a read result.
- Graph traversal has additional inherited semantic differences described below.
  Bounded traversal depths and implicit safety caps are not removed by this task.

## Canonical dictionary schemas

### Decisions

All active decision readers expose the same keys:

`decision_id, domain, entity_id, category, category_index, recommended_action,
recommended_index, confidence, factors, factor_vector, probabilities, status,
metadata, created_at, factor_names, source, scorer_version, preset_version,
factor_schema_version, correct, outcome, verified_at_epoch, quality_signal,
override_comment, verified_by, analyst_action, final_action, was_override`.

Factors are a dictionary; vectors/probabilities/names are lists; indices are
integers; confidence and persistence times are floats. Missing governed fields
on basic writes and missing outcome annotations are `None`. Governed fields are
available at the top level even when the storage representation keeps them in
metadata. Existing metadata is preserved. `_sequence` is never public.

With a stored outcome, `get_decision(include_outcome=True)` and verified reads add
`actual_action, actual_index, is_correct, verified_at, outcome_metadata`.
Context is under `outcome_metadata.context`; it is not duplicated at the root.
Requesting an absent outcome leaves the decision unchanged, as protocol.py says.

Archived reads keep the existing archive schema and chronology:
`decision_id, domain, category, category_index, recommended_action,
recommended_index, confidence, factor_vector, probabilities, created_at,
actual_action, actual_index, is_correct, verified_at, archived_at,
archive_reason, metadata`. Missing outcomes have four explicit null fields.
Rows are ordered by creation time ascending, then ID, per existing archive
semantics. Changing active read order does not change retention selection.

### Checkpoints

Both legacy and v2 readback expose:
`checkpoint_id, domain, decision_id, category, action, centroids, decisions_count,
verified_count, iks, shape, factor_names_hash, quality_window_size,
quality_verified_count, quality_correct_count, rolling_accuracy,
quality_window_end, quality_policy_version, metadata, created_at,
decision_time_start, decision_time_end, checkpoint_time`.

Absent fields are `None`, not empty IDs or omitted keys. Centroids preserve the
written tensor representation. Legacy writes already capture checkpoint time,
default IKS to 0 and default decision count to the domain count; readback preserves
that stored information. V2 writes do not store a separate checkpoint time, so
that field is `None`. `created_at` is a numeric epoch; quality-window end and
checkpoint/window time properties retain their string representation when
present. Direct decision linkage takes precedence over metadata linkage.

### Learning state, events and other records

- Centroids: `category, action, vector_json, delta_norm, caused_by_decision_id,
  updated_at`; `vector_json` is a numeric list despite its legacy name.
- DK weights: `weight_json, n_decisions_used, computed_at, supersedes_id,
  created_at, domain, welford_state, n_confirmed, n_overridden, entity_group`.
  Tensor is nested numeric lists; supersedes ID is `str | None`; both times float.
- Conservation state: `id, domain, status, alpha, q, V, theta_min, product,
  categories_total, categories_with_data, baseline_product, relative_threshold,
  complacency_flag, caused_by_decision_id, old_status, updated_at`; `updated_at`
  is an ISO string.
- Conservation snapshots: `status_id, snapshot_id, counts_scope, domain, V, q,
  alpha, theta_min, verified_count, correct_count, status, policy_version,
  computed_at`; both ID aliases identify the same snapshot; counts scope is
  `verified_only`.
- Events: `event_id, domain, event_type, rule_name, variant_id, source_copilot,
  source_rule, metric, shadow_batch_size, min_shadow_batches, metadata, timestamp`.
  `timestamp` is a string. Legacy optional fields are null. Internal schema
  tags/ingestion timestamps are not part of this projection.
- Entity links: `decision_id, entity_id, edge_type, created_at`. Internal
  decision-to-evolution links are not entity links. Order is creation time
  descending, then decision ID, entity ID and edge type ascending.
- Fingerprints: `domain, fingerprint_id, fingerprint, factor_names, metadata`;
  `fingerprint` is the decoded factor-stats dictionary. Memory orders by stored
  creation time ascending and fingerprint ID ascending, capped at 500.
- Transfer patterns: `pattern_id, domain, source_domain, target_domain,
  pattern_type, source_rule, target_rule, factor_mapping, confidence,
  validation_status, conservation_status, source_fingerprint_id,
  evolution_event_id, metadata, created_at, similarity_score`. Optional references
  are null; mapping is a dictionary; creation time is float. Order is creation
  time ascending then pattern ID. Similarity uses metadata override or confidence.

## Inventory of every protocol read returning records

The AGE column describes the inspected implementation, not a hypothetical target.
Source: sibling `ci_platform/graph/age_graph_store.py` and `age_sdk_adapter.py`.

| Protocol method(s) | AGE return shape / behavior observed | Memory contract / follow-up |
| --- | --- | --- |
| `get_decision`, `get_decisions`, `get_all_decisions`, `get_verified_decisions` | Decoded Decision properties; governed names/source/versions at root, basic factors/entity ID at root; merged outcome has no root context. Property sets vary by writer; raw graph conversion can add `_age_id`. Active lists sort oldest first. | Common decision projection above; preserve useful basic fields in governed readback; AGE must project the common superset, null optionals and remove internal properties. |
| `get_archived_decisions` | Decoded archived Decision plus outcome properties, including native archive/status fields. | Existing explicit archive projection above; AGE must use it. Archive order remains ascending. |
| `get_evolution`, `get_evolution_state`, `get_posterior`, `get_promotion`, `get_ledger`, `get_governance` | Decoded state dictionary or None. | Same opaque payload, independent copy; evolution alias preserved. |
| `list_evolutions`, `list_posteriors`, `list_promotions`, `list_ledgers`, `list_governance` | Dictionaries combining record key and decoded payload, ordered by update time descending. | Same records; deterministic storage-key ascending order. AGE needs this order. Caller-owned key fields remain payload data. |
| `load_latest_centroids` | Numeric array from latest checkpoint, or None. | Independent numeric array; deterministic checkpoint selection. |
| `get_centroid_checkpoints`, `load_latest_checkpoint_for_regime`, `get_decision_checkpoints` | Decoded checkpoint properties; omitted optional fields, missing legacy decision ID becomes empty string; checkpoint-time/count/IKS defaults differ. General bounded reads reverse newest N into ascending order; filters are ignored. | Common checkpoint schema above for all readers; chronological newest-N windows / descending unbounded reads; inclusive category/time filters across legacy and v2. AGE must align ties, nulls, types and filters. |
| `get_checkpoint_lineage` | Decision dictionary or None reached through checkpoint edge. | Same canonical decision as direct reader. |
| `read_entity_enrichment` | Metric name to `ProvenancedValue`, namespaced names when no namespace specified. | Same typed values and domain/type/ID/namespace filtering; opaque typed timestamp boundary above. |
| `list_entity_enrichments` | `EntityEnrichmentRecord` list, optional type/namespace filters and bounded limit. | Same dataclass fields; sort domain/type/entity/namespace/metric; explicit None now unbounded. AGE limit/order need verification in its port of these tests. |
| `get_decision_links` | Four-key entity-edge projection; creation time may be ISO or missing. | Four-key projection above; float or None timestamp, deterministic order; no artificial 100-row limit for explicit N. |
| `query_context` | Dictionaries containing native graph path `p`, including graph-native node/edge structures. | Existing portable `node, id, depth, properties` traversal records; embedded Decisions use normalized projection. AGE needs a shared path projection decision. |
| `query_similar` | Raw same-category Decision records, arbitrary query order, native limit clamp; adapter converts limit with int(). | Canonical Decisions in newest-first order; zero empty / None unbounded. Existing memory supplier matching and entity-ID root resolution are additional inherited semantics needing coordination. |
| `get_evolution_events` | Decoded event properties with ISO timestamp and additional schema/ingestion fields; event_type/rule_name/variant_id filters; timestamp-desc order without ID tie-break. | Event projection above, string timestamp, all three filters, timestamp-desc/ID-asc order. |
| `get_transfer_patterns` | Decoded TransferPattern, domain links resolved, similarity added; creation-time/ID ascending. | Same public fields listed above; optional references explicit None. AGE must remove any native-only properties. |
| `decision_movement` | `decision, relationship, evidence, direction`; ordered native edge IDs, pagination extras. | Existing memory context rows. Canonical traversal/evidence shape remains a coordinated AGE-SDK decision; not fabricated from nonexistent memory graph nodes. |
| `contextual_judgment` | Native path dictionaries (`p`). | Existing `{decision: normalized Decision}` rows, category/entity-group filtered; same traversal-shape follow-up. |
| `promotion_basis` | Native path dictionaries (`p`). | Existing `{evolution_event: normalized Event}` rows matched by rule; same traversal-shape follow-up. |
| `transfer_witness` | `transfer_pattern, source_domain, target_domain, from_edge, to_edge` containing graph records. | Existing `{transfer_pattern: canonical TransferPattern}` rows; native graph evidence projection requires coordination. |
| `list_fingerprints` | Five-key decoded projection listed above; query has no ORDER BY, cap 500. | Matched projection; AGE must add deterministic order before its cap. |
| `get_latest_conservation_statuses` | Decoded latest snapshot per domain, both ID aliases and counts_scope, float computed_at. | Adds missing aliases/counts scope at read time; domain ordering and supplied domain filtering. |
| `get_iks_trajectory` | Decoded checkpoints, domain/time filtered, per-decision deduplication preferring v2, domain/time/ID ascending. | Same selection, normalized checkpoint projection; fix direct decision-ID loss. |
| `get_centroids` | Six-key numeric projection above; updated_at from float updated_at_epoch. | Matched, converting stored ISO at read time. |
| `get_dk_weights` | Ten keys above; float computed_at, native created_at often ISO, string supersedes ID. | Matched key set, string ID, both timestamps float; AGE must normalize created_at. |
| `get_conservation_state` | Same fixed field set; string updated_at. | Same fields and ISO string `updated_at`. |
| `get_k_utilities`, `get_holdout_decisions` | No native AGE extension methods; current shared GraphScoringPersistence bridge uses governance records. | Existing bridge projections: key/record_type/id/domain/metadata plus episode_id/k/utility or decision_id/holdout_group, deterministic semantic-key order. Utility None limit supported by memory; native extension rollout remains separate. |

Count methods return integers and generated-ID methods return strings, so neither
is a dictionary read omitted from this inventory. Non-protocol RL state remains
an opaque copied dictionary; no new protocol surface is introduced.

## AGE-SDK #11 implementation checklist

1. Apply the canonical decision and archive projections, including governed
   root fields, retained basic factors/entity fields, explicit nulls and outcome
   nesting. Normalize backend-injected metadata consistently without rewriting
   user metadata; exclude `_age_id` and other private storage fields.
2. Apply checkpoint projection/defaults for legacy and v2, turn empty IDs into
   None, return all optional fields, normalize all time fields. Match existing
   memory legacy default count/IKS/capture time at write or projection boundary.
3. Preserve AGE's field-level time shapes: event and conservation timestamps
   remain strings; decision/checkpoint creation, DK and centroid epoch values
   remain numeric. Missing times remain None.
4. Implement newest-first decision/event ordering with ascending ID ties;
   retain chronological bounded checkpoint windows and descending unbounded
   checkpoint reads, adding stable ties. Align latest-checkpoint selectors, control-plane key order, fingerprint
   ordering and entity-link ordering. Apply ordering before limits.
5. Apply all checkpoint category/checkpoint-time/decision-time filters, to both
   legacy and v2 rows. Keep inclusive boundaries and exclude missing values when
   a time bound is requested. Preserve existing event filter conjunctions.
6. Remove minimum-one limit clamps; support zero, positive N and explicit None
   through native methods AND adapters (notably query_similar's int(None)).
   Make omitted kwargs limits unbounded. Coordinate the three declared defaults
   and int annotations separately before making omission universally unbounded.
7. Port this conformance suite to AGE's repository, retaining exact shape/type/
   null/order/filter assertions; test real persistence and reconnects there.
8. Resolve remaining traversal schemas/semantics and typed enrichment timestamp
   migration explicitly. These are documented gaps, not claimed fixed by the
   passing dictionary conformance cases. Stage native scoring extension methods
   as already required by REV-P4a P1-3; do not add concrete dispatch to consumers.

Storage writes, ID generation, replay comparisons, protocol.py and AGE source are
unchanged. Retention's old selection order is explicit so read-order changes do
not alter archived data. Existing tests were updated only where they asserted
the replaced public ordering or ISO timestamp contract; legacy backend assertions
remain strict and unchanged in meaning.

Regression follow-up: verified reads already contain independent projected copies;
an additional whole-list deepcopy was removed after the training regression
exposed its cost. Two timestamp-dependent fixtures now set explicit creation times
instead of assuming successive wall-clock calls differ. Bundle tests retain their
assertions but use epoch times and newest-first memory decisions; their AGE-specific
assertions remain unchanged pending AGE-SDK #11.

The user authorized the narrow gate-consumer follow-up in `composite_gate.py`
and `gate_enforced_scorer.py`. Eight additional regression cases verify recent
degradation and recovery under either backend ordering, deterministic ties,
unchanged readback, legacy untimed rows, explicit streams and empty input.
`scorer.py` and `compounding.py` remain untouched.

The user also authorized chronological normalization in the trust-trap diagnostic
consumer. Two regression cases verify identical recency evidence from oldest-first
and newest-first readers without mutating their rows. Full-suite follow-up found
and fixed null decision-time sorting and mixed ISO/epoch latest-checkpoint selection
inside the memory reader. Existing integration tests now use explicit chronology,
the four-key entity-link projection (while asserting stored entity type is retained),
and the consolidation boundary they intend to inspect. No assertions about learning,
conservation, batch boundaries or persistence success were removed.

The production gate-policy and HTTP 423 fixtures also set explicit increasing
decision times. Rapid writes can legitimately share a clock tick; opaque-ID
tie-breaking must not be mistaken for a fixture's intended degradation sequence.
The recovery fixture places newly verified recovery outcomes after existing rows.
