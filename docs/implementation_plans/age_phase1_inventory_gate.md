# AGE Phase 1 Inventory Freshness and Canonical Vocabulary Gate

Date: 2026-07-19

## Scope and evidence

This is a read-only Phase 1 gate diagnostic. Runtime facts are from
LIVE-AGE-2026-07-19: PostgreSQL+AGE at localhost:5433, database soc_copilot,
graph soc_graph, queried through ag_catalog.ag_label and cypher() reads.
Source facts cite file:line. The Phase 1 gate requires Protocol v2 definition,
SOC inventory, vocabulary reconciliation, and conformance specifications before
implementation; migration is forbidden before Phases 1 and 2 complete.
docs/judgment_memory_v2_7.md:769-788, :1175-1180

## PART A - LIVE AGE INVENTORY

The snapshot found 43 user vertex labels and 30 user edge labels. Internal
_ag_label_vertex and _ag_label_edge are excluded. Props are keys from up to
five sampled rows; "-" means zero live rows. Domain? means sampled properties
included domain, not that every row was proved partitioned.

### Vertices

| Label | Count | Sample properties | Domain? |
|---|---:|---|---|
| Alert | 866 | alert_id, category, severity, status, timestamp_epoch | no |
| AlertCategory | 0 | - | no |
| AlertType | 0 | - | no |
| AnalystArchetype | 0 | - | no |
| Asset | 226 | asset_id, asset_type, criticality, hostname | no |
| AttackPattern | 9 | category, mitre_id, pattern_id, tactic | no |
| BehaviorHistory | 0 | - | no |
| Campaign | 403 | campaign_id, confidence, severity, trigger_rule | no |
| CampaignSeed | 208 | campaign_id, category, seed_key, status | no |
| CentroidCheckpoint | 1015 | category, centroids, created_at, decision_id, domain | yes |
| Checkpoint | 0 | - | no |
| DataClass | 0 | - | no |
| DataQualityAlert | 20 | alert_id, category, factors_json, is_correct, system_name | no |
| Decision | 6253 | action, category, confidence, correct, decision_id, factor_vector, outcome | no |
| DecisionContext | 0 | - | no |
| DecisionDistanceLog | 2139 | decision_id, logged_at_epoch, pattern_history_value | no |
| DecisionEntityLink | 216 | decision_id, edge_type, entity_id | no |
| DeploymentState | 1 | bootstrap_mu, bootstrap_shape, gae_version | no |
| Entity | 0 | - | no |
| EvidenceReceipt | 216 | actor, chain_index, decision_id, domain, payload_hash, previous_hash | yes |
| EvolutionEvent | 142 | action, category, correct, event_type, triggered_by | no |
| L5Centroid | 17 | action, category, domain, vector_json | yes |
| L5ConservationState | 5 | V, alpha, domain, q, status, theta_min | yes |
| L5DKWeight | 4 | domain, n_decisions_used, weight_json | yes |
| L5DKWeightArchive | 102 | archive_id, domain, n_decisions_used, weight_json | yes |
| Location | 0 | - | no |
| Outcome | 1015 | actual_action, decision_id, domain, is_correct, verified_at | yes |
| PhishingCampaign | 0 | - | no |
| PipelineSystem | 9 | business_criticality, name, owner, status | no |
| Playbook | 0 | - | no |
| ProfileSnapshot | 51 | counts, decision_count, mu, timestamp_epoch | no |
| SLA | 0 | - | no |
| ShadowDecision | 1500 | ai_action, ai_correct, analyst_action, decision_id | no |
| TestAlert | 0 | - | no |
| TestDecision | 0 | - | no |
| TestIntegrity | 0 | - | no |
| TestNode | 0 | - | no |
| TestSetBehavior | 0 | - | no |
| ThreatIndicator | 9 | indicator, indicator_type, severity, source | no |
| ThreatIntel | 5 | context, severity, source, type, value | no |
| TravelContext | 0 | - | no |
| TravelRecord | 0 | - | no |
| User | 231 | department, name, risk_level, user_id | no |

### Edges

| Label | Count | Sample endpoints / properties |
|---|---:|---|
| AFFECTS | 20 | DataQualityAlert -> PipelineSystem; created_at_epoch, system_name |
| APPLIED_PLAYBOOK | 0 | - |
| ASSIGNED_TO | 0 | - |
| ASSOCIATED_WITH | 0 | - |
| BY_ANALYST | 0 | - |
| CLASSIFIED_AS | 645 | Alert -> AttackPattern |
| CONTINUES | 67 | Campaign -> Campaign; created_at_epoch, gap_buckets, rule_type |
| DECIDED_ON | 6253 | Decision -> Alert |
| DETECTED_ON | 855 | Alert -> Asset |
| EMITTED_RECEIPT | 0 | - |
| FEEDS | 9 | PipelineSystem -> PipelineSystem; created_at_epoch, source_name, target_name |
| FOR_ALERT | 0 | - |
| HAD_CONTEXT | 0 | - |
| HANDLED_BY | 0 | - |
| HAS_CENTROID_CHECKPOINT | 0 | - |
| HAS_HISTORY | 0 | - |
| HAS_INDICATOR | 633 | Alert -> ThreatIndicator |
| HAS_OUTCOME | 0 | - |
| HAS_TRAVEL | 0 | - |
| INVOLVES | 855 | Alert -> User |
| IN_CATEGORY | 0 | - |
| MATCHES | 0 | - |
| MEMBER_OF | 694 | Alert -> Campaign |
| ORIGINATES_FROM | 0 | - |
| PART_OF | 0 | - |
| SHAPED_BY | 0 | - |
| STORES | 0 | - |
| SUBJECT_TO | 0 | - |
| SUPERSEDES | 4 | L5DKWeight -> L5DKWeightArchive |
| TRIGGERED_EVOLUTION | 0 | - |

The source AGE client writes legacy Decision/DecisionContext shapes and
TRIGGERED_EVOLUTION relationships from Decision or Alert paths.
../ci-platform/ci_platform/graph/age_client.py:827-935, :972-1012

## PART B - CANONICAL DIFF

JM v2.7 defines 13 canonical node labels and domain partitioning.
docs/judgment_memory_v2_7.md:307-340
It defines the canonical edge vocabulary in section 4.2.
docs/judgment_memory_v2_7.md:343-365

Five of 13 canonical labels physically exist. Physical presence is not semantic
conformance: HAS_OUTCOME and EMITTED_RECEIPT have zero live rows.

| Canonical label | Live AGE | Match? | Conflict | Resolution needed |
|---|---|---|---|---|
| Decision | 6253 | partial | no sampled domain/status; embedded outcome/vector | projection and forward canonical properties |
| Outcome | 1015 | partial | HAS_OUTCOME is zero | link forward; define V backfill |
| FactorVector | absent | no | vector embedded on Decision | projection, then node writes |
| Observation | absent | no | ShadowDecision is not automatically equivalent | decide evaluation semantics |
| Domain | absent | no | no shared domain node | define ownership/partition |
| DomainContext | absent | no | Alert/Asset/User/Campaign are legacy contexts | projection or dual labels |
| EvolutionEvent | 142 | partial | TRIGGERED_EVOLUTION is zero | repair forward path/history |
| Rule | absent | no | AttackPattern is not automatically Rule | set rule taxonomy |
| TransferPattern | absent | no | no transfer representation | add only with evidence |
| EvidenceReceipt | 216 | partial | EMITTED_RECEIPT is zero | link to Decision, verify chain |
| CentroidCheckpoint | 1015 | partial | HAS_CENTROID_CHECKPOINT is zero | canonical link and fields |
| Fingerprint | absent | no | DecisionDistanceLog is not fingerprint | distinct telemetry, forward snapshots |
| ConservationStatus | absent | no | L5ConservationState differs | projection or canonical writes |

Extra live labels require classification as SOC-specific, projection,
dual-write, or test artifact before cross-domain use.
docs/soc_age_schema_compatibility_spec_v1.md:260-283

## PART C - SOC VOCABULARY CONFLICTS

| Conflict | Section 4 expectation | SOC reality | SDK migration impact |
|---|---|---|---|
| Outcome | Outcome plus HAS_OUTCOME | 1015 nodes, zero edges; Decision embeds outcome/correct | prevent V double counting |
| FactorVector | node plus HAS_FACTOR_VECTOR | no label; vector embedded | no canonical factor traversal |
| EvidenceReceipt | node plus EMITTED_RECEIPT | 216 nodes, zero edges | audit records orphaned from Decisions |
| Evolution lineage | Decision -> TRIGGERED_EVOLUTION -> event | 142 events, zero edges | procedural lineage incomplete |
| DomainContext | typed, partitioned context | no label; legacy Alert/User/Asset/Campaign | cross-domain context unsafe |
| Domain partition | domain on every canonical node | sampled Decision/Alert/Campaign/Event lack it | no safe universal domain filter |

The compatibility specification anticipated the embedded outcome/vector, audit,
and evolution issues. docs/soc_age_schema_compatibility_spec_v1.md:88-96,
:285-317, :343-385

## PART D - PROTOCOL V2 METHOD COVERAGE

Protocol V2 declares these additions. copilot_sdk/graph/protocol.py:150-280
Both stores expose all 11. This is interface coverage, not proof that their
semantics are identical; that requires live AGE conformance.

| Method | Protocol | SQLiteGraphStore | AGEGraphStoreAdapter | Conformance |
|---|---|---:|---:|---|
| write_governed_decision | yes | 1013 | 43 | SQLite and AGE |
| write_observation | yes | 1157 | 93 | SQLite and AGE |
| append_evidence_receipt | yes | 1233 | 149 | SQLite and AGE |
| write_conservation_status | yes | 1315 | 123 | SQLite and AGE |
| write_fingerprint | yes | 1395 | 169 | SQLite and AGE |
| write_centroid_checkpoint | yes | 1463 | 189 | SQLite and AGE |
| write_evolution_event | yes | 1549 | 217 | SQLite and AGE |
| link_entity | yes | 1645 | 245 | SQLite and AGE |
| archive_decisions | yes | 2844 | 375 | SQLite and AGE |
| domain_scoped_reset | yes | 2925 | 389 | SQLite and AGE |
| count_verified_decisions | yes | 1906 | 279 | SQLite and AGE |

## PART E - CONFORMANCE TEST STATUS

The module has 88 test functions. tests/graph/test_protocol_v2_conformance.py:359-3225
The recorded local baseline was 34 passed and 53 skipped; this diagnostic did
not execute it. docs/implementation_plans/age_protocol_v2_skip_triage.md:34-46
AGE tests skip unless AGE_INTEGRATION=1, AGE_TEST_DSN, and a non-SOC
protocol_v2_test graph are supplied. tests/graph/test_protocol_v2_conformance.py:42-57

| Tests (all 88 listed) | SQLite status | AGE status | Skip condition |
|---|---|---|---|
| test_write_decision; test_v1_write_decision_generates_distinct_ids; test_v2_governed_decision_caller_id | not run | n/a | local |
| test_age_v2_governed_decision_caller_id; test_age_governed_decision_identical_replay_skips; test_age_governed_decision_conflict_raises | n/a | not run | AGE environment |
| test_write_outcome_confirmed; test_write_outcome_overridden; test_outcome_atomic; test_outcome_missing_decision | not run | n/a | local |
| test_age_write_outcome_confirmed; test_age_write_outcome_overridden; test_age_outcome_missing_decision; test_age_outcome_direct_duplicate_raises; test_age_outcome_non_pending_decision_raises; test_age_count_verified_after_outcome; test_age_outcome_no_orphan_on_duplicate | n/a | not run | AGE environment |
| test_write_observation; test_observation_not_in_V; test_observation_not_in_flywheel; test_count_verified_empty; test_count_verified_pending; test_count_verified_mixed; test_sqlite_status_migration_backfills_from_outcomes | not run | n/a | local |
| test_age_write_observation; test_age_observation_not_in_V; test_age_observation_not_in_flywheel; test_age_count_verified_empty; test_age_count_verified_pending; test_age_count_verified_status_based_without_outcomes | n/a | not run | AGE environment |
| test_evidence_receipt_chain; test_evidence_receipt_hash_json_parity | not run | n/a | local |
| test_age_evidence_receipt_chain; test_age_evidence_replay_same_intent_skips; test_age_evidence_replay_conflict_raises; test_age_evidence_missing_decision; test_age_evidence_no_decision_or_V_side_effect; test_age_evidence_receipt_concurrent_append; test_age_evidence_receipt_rollback_on_failure | n/a | not run | AGE environment |
| test_conservation_status_write; test_fingerprint_write_read; test_centroid_checkpoint; test_protocol_v2_checkpoint_does_not_break_legacy_centroid_load; test_evolution_event; test_entity_link | not run | n/a | local |
| test_age_conservation_status_write; test_age_conservation_status_duplicate_identical_skips; test_age_conservation_status_conflict_raises; test_age_fingerprint_write_read; test_age_fingerprint_duplicate_identical_skips; test_age_fingerprint_conflict_raises; test_age_centroid_checkpoint; test_age_centroid_checkpoint_duplicate_identical_skips; test_age_centroid_checkpoint_conflict_raises; test_age_evolution_event; test_age_evolution_event_duplicate_identical_skips; test_age_evolution_event_conflict_raises; test_age_entity_link; test_age_entity_link_duplicate_skips; test_age_entity_link_missing_decision_raises | n/a | not run | AGE environment |
| test_age_archive_pending; test_age_archive_verified_requires_confirmation; test_age_archive_verified_decreases_active_V; test_age_archive_cutoff_respected; test_age_archive_other_domain_isolation; test_age_domain_scoped_reset; test_age_domain_scoped_reset_rejects_unsafe_domain; test_age_transaction_rollback_preserves_domain_on_mid_reset_failure; test_age_preview_no_decision_write | n/a | not run | AGE environment |
| test_entity_link_migration_deduplicates_legacy_edges; test_legacy_link_decision_to_entity_duplicate_is_harmless; test_archive_pending; test_archive_verified; test_domain_scoped_reset; test_local_idempotent_replay_does_not_duplicate_class_a_records; test_v1_scorer_compatibility; test_outcome_direct_duplicate_raises; test_outcome_replay_identical_skips; test_outcome_replay_conflicting_errors; test_preview_no_decision_write; test_evidence_replay_same_intent_skips; test_evidence_replay_conflict_quarantines; test_governed_decision_conflict_quarantines; test_evolution_event_conflict_quarantines; test_outbox_quarantine_recorded | not run | n/a | local; several intentional pending |
| test_concurrent_cross_domain | pending | pending | AGE cross-domain concurrency pending |
| test_migration_replay | pending | pending | migration replay pending |
| test_outbox_replay_ordering | pending | pending | service/outbox pending |

The skip plan identifies unresolved cross-domain concurrency, migration replay,
service-layer accepted-pending-sync, and SOC projection tests.
docs/implementation_plans/age_protocol_v2_skip_triage.md:50-63

## PART F - RULE 38 COMPLIANCE

Rule 38 requires every copilot main path to use create_graph_store rather than
construct SQLiteGraphStore directly. docs/judgment_memory_v2_7.md:1116-1118

| Copilot | Default path | Factory active path? | Direct SQLite? | Fix needed |
|---|---|---|---|---|
| Trading | _graph_store creates SQLite | yes | yes | factory owns SQLite selection |
| Purchasing | _graph_store creates SQLite | yes | yes | factory owns SQLite selection |
| DataOps | _graph_store creates SQLite | yes | yes | factory owns SQLite selection |
| S2P | build_s2p_scorer fallback creates SQLite | yes | yes | factory owns SQLite selection |

Evidence: apps/trading/backend/app/main.py:67,104;
apps/purchasing/backend/app/main.py:77,128;
apps/dataops/backend/app/main.py:49,91;
../s2p-copilot/backend/app/main.py:11,89. Active factory paths:
apps/trading/backend/app/graph_status.py:247-258;
apps/purchasing/backend/app/graph_status.py:302-313;
apps/dataops/backend/app/graph_status.py:249-261;
../s2p-copilot/backend/app/s2p_graph_status.py:273-285.

## PART G - OPEN QUESTIONS

The compatibility specification records these seven open questions.
docs/soc_age_schema_compatibility_spec_v1.md:649-657

| # | Question | Current answer | Blocks Phase 2? |
|---:|---|---|---|
| 1 | DomainContext dual labels or projections? | no accepted choice | yes |
| 2 | Do historical outcomes receive receipts? | forward policy only | yes for audit/backfill scope |
| 3 | What is ShadowDecision? | 1500 live rows; not automatically Observation | yes |
| 4 | FactorVector names/schema for history? | not defined | yes |
| 5 | ProfileSnapshot dual-label or separate checkpoints? | both labels exist | yes |
| 6 | Missing TRIGGERED_EVOLUTION repair policy? | zero live rows | yes |
| 7 | DataQualityAlert/PipelineSystem ownership? | sampled rows lack domain | yes |

## PART H - V-TRANSITION RULE

V is locked to verified decisions. docs/judgment_memory_v2_7.md:978-990
SOC has embedded Decision outcome/correct fields, separate Outcome nodes, and
zero HAS_OUTCOME edges. The documented transition warns that embedded and
canonical forms must never count twice. docs/soc_age_schema_compatibility_spec_v1.md:285-317

Proposed acceptance decision: in projection mode V counts unique Decision IDs
with embedded outcome non-null. In canonical-forward mode V counts unique
Decision IDs with status confirmed or overridden and exactly one linked Outcome.
Mixed-mode queries select one source per Decision ID, never sum both. Historical
backfill is domain-scoped, idempotent, and marked as backfill. This proposal
requires Phase 1 acceptance.

## PART I - PHASE 1 GATE VERDICT

PHASE_1_COMPLETE: PARTIALLY

The inventory is refreshed and Protocol v2 interfaces exist, but reconciliation
is not accepted. Five canonical labels exist, eight are absent, Outcome and
EvidenceReceipt canonical edges are empty, seven decisions are open, full live
AGE conformance has not been demonstrated, and Rule 38 is unmet in all four
SDK default paths.

REMAINING_DECISIONS:

1. Accept Domain and DomainContext projection/partition policy.
2. Accept the one-source-per-Decision V transition rule.
3. Classify ShadowDecision and FactorVector historical schema policy.
4. Decide canonical forward links for Outcome, receipts, checkpoints,
   conservation, and evolution.
5. Decide SOC compatibility projection or dual-label and evolution repair.
6. Accept DataOps context ownership before cross-domain claims.

BLOCKING_ISSUES:

1. Canonical vocabulary is not reconciled with live SOC data.
2. Isolated AGE conformance has not been demonstrated.
3. Rule 38 is non-compliant for all four SDK default paths.
4. Migration replay and service/outbox conformance remain pending.

RECOMMENDED_NEXT_STEPS:

1. Accept the seven compatibility decisions without mutating SOC schema.
2. Add and accept the SOC projection contract tests named in the compatibility
   specification. docs/soc_age_schema_compatibility_spec_v1.md:605-634
3. Run isolated AGE conformance on a non-SOC test graph.
4. Complete Rule 38 factory routing and pending replay/service conformance.
5. Only then authorize Phase 2 completion; S2P Phase 3 migration remains
   forbidden until the gate passes. docs/judgment_memory_v2_7.md:1175-1180

