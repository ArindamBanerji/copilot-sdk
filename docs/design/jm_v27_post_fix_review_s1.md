# JM v2.7 Post-Fix Review S1 — Graph Model + Protocol Completeness

Review date: 2026-08-01
Scope: adversarial, read-only review of the JM v2.7 graph model and Protocol v2.
Classification: IMPLEMENTED means the contract, the three SDK stores, the AGE store, and available live evidence agree; PARTIAL means at least one of those surfaces is incomplete, conditional, or not proven; MISSING means no implementation was found.

## §1 EXECUTIVE SUMMARY

The graph is materially populated and the core decision/outcome/conservation path is implemented. The review does not support a fully canonical JM v2.7 graph claim: Rule has no writer and no live nodes; the three Observation edges are not created by AGE; several procedural Rule edges have no writer; and SQLite/InMemory represent Domain and DomainContext as columns/edge records rather than canonical node writers.

Strict node result: 4 IMPLEMENTED / 8 PARTIAL / 1 MISSING out of 13.
Edge result: the design header says 18, but its enumerated lists contain 20 source-target edge patterns (3 + 8 + 3 + 3 + 3). On the enumerated 20: 9 IMPLEMENTED / 3 PARTIAL / 8 MISSING. The table below reports all 20 rather than silently dropping two.
Protocol v2 result: 14 IMPLEMENTED / 0 PARTIAL / 0 MISSING across Protocol, InMemory, SQLite, and AGE. This does not mean every canonical node/edge property is guaranteed by every method.
Lifecycle: CONFORMANT for the tested write/count contract; AGE retains a legacy d.outcome fallback in addition to status predicates.
Blockers: 1 closed / 3 partial / 2 open; therefore 5 of 6 are not fully closed.

The validation report confirms all five domain anchors, all five domains for Outcome/ConservationStatus/CentroidCheckpoint, zero NULL-domain Decisions, and the intentionally different SOC hash-chain audit model (jm_v27_validation_report_v1.md:35-45, :75-88, :108-114). It also explicitly says complete path closure is not proven (jm_v27_validation_report_v1.md:150-156) and that full SDK/S2P/CI suite evidence remains incomplete (jm_v27_validation_report_v1.md:158-177).

## §2 NODE LABEL INVENTORY (Part A)

Canonical required properties are taken from judgment_memory_v2_7.md:222-340. The live evidence below is the read-only soc_graph census/query executed during this review; the census implementation opens the AGE connection and runs the canonical census sections at scripts/graph_census_v2.py:15-30 and :37-48.

| # | Label | Protocol | InMemory | SQLite | AGE | Missing Props |
|---:|---|---|---|---|---|---|
| 1 | Decision | IMPLEMENTED — write_decision and governed writer (protocol.py:19-28, :191-209) | IMPLEMENTED — _decisions and write_decision (memory_store.py:327-347, :433-478) | IMPLEMENTED — decisions table and writer (sqlite_store.py:407-429, :995-1054) | IMPLEMENTED — CREATE Decision (age_graph_store.py:558-628; governed properties at :709-794) | Generic writers do not guarantee all governed fields (source, scorer/preset/schema versions and explicit indices); those are guaranteed only by the governed path/metadata. Live: present with five domains (jm_v27_validation_report_v1.md:35-40). |
| 2 | Outcome | IMPLEMENTED — write_outcome (protocol.py:30-48) | PARTIAL — outcome record is stored, but no independent outcome_id, reward, verifier, or override-reason fields are guaranteed (memory_store.py:549-601) | PARTIAL — outcomes table stores the event, while several canonical fields are materialized on decisions (sqlite_store.py:431-439, :1159-1245) | PARTIAL — node/edge are created, but identity is decision_id and canonical optional fields are conditional (age_graph_store.py:886-969) | Canonical outcome_id, reward, verifier, and override_reason are not guaranteed as dedicated event properties by all three stores (judgment_memory_v2_7.md:239-243). Live Outcome nodes exist for all five domains (jm_v27_validation_report_v1.md:41-45). |
| 3 | FactorVector | PARTIAL — no standalone protocol writer; embedded in governed decision/observation (protocol.py:191-225) | PARTIAL — vector is embedded in decisions and a separate observation-vector dict (memory_store.py:330-334, :455-472, :644-652) | PARTIAL — embedded decision JSON and observation_factor_vectors, not a FactorVector table (sqlite_store.py:412-413, :604-612) | PARTIAL — AGE creates the canonical node/edge only when factor extraction yields values (age_graph_store.py:611-619, :665-705) | InMemory/SQLite do not guarantee factor_names_hash, shape, and schema_version in their separate vector records; required schema is judgment_memory_v2_7.md:245-249. Live supplemental query found FactorVector nodes, but the census script does not enumerate this label (graph_census_v2.py:19-30). |
| 4 | Observation | IMPLEMENTED — write_observation (protocol.py:211-226) | IMPLEMENTED — _observations plus observation entity/vector structures (memory_store.py:330-334, :603-653) | IMPLEMENTED — observations, entity-edge, and factor-vector tables (sqlite_store.py:581-612, :1247-1321) | IMPLEMENTED — CREATE Observation (age_graph_store.py:1013-1053) | No lifecycle status is present, as required. The three canonical Observation edges are a separate edge gap (see §3). Required fields are judgment_memory_v2_7.md:251-259. |
| 5 | Domain / DomainAnchor | PARTIAL — no public domain-node writer in the protocol; domain is a partition parameter | PARTIAL — store has a configured domain scalar, not Domain nodes (memory_store.py:327-330) | PARTIAL — domain is a required column, not a Domain table (sqlite_store.py:407-410) | PARTIAL — _ensure_domain_anchor creates Domain (age_graph_store.py:1055-1075) | AGE anchor creation omits tensor_shape, penalty_ratio, environment, and owner; canonical fields are judgment_memory_v2_7.md:265-268. Live all five anchors are present (jm_v27_validation_report_v1.md:38-40). |
| 6 | DomainContext | PARTIAL — no dedicated protocol writer; reached through link_entity (protocol.py:338-345) | PARTIAL — links are dict records; no DomainContext node structure (memory_store.py:347, :1017-1046) | PARTIAL — decision_entity_edges represents the relation; no DomainContext table (sqlite_store.py:571-579, :1958-2020) | IMPLEMENTED for link_entity: creates DomainContext and ABOUT (age_graph_store.py:1978-2040) | AGE does not materialize attributes or updated_at; required fields are judgment_memory_v2_7.md:270-273. Live supplemental query found DomainContext nodes; standard census only reports context counts (graph_census_v2.py:24-25). |
| 7 | EvolutionEvent | IMPLEMENTED — write_evolution_event (protocol.py:283-297) | PARTIAL — writer and storage exist, but canonical status is not a dedicated field (memory_store.py:345-349, :817-871) | PARTIAL — table/writer exist, but schema has no canonical status column (sqlite_store.py:512-528, :1862-1915) | PARTIAL — node writer exists, but no status property or procedural Rule edge is created (age_graph_store.py:1684-1737) | Canonical status is required by judgment_memory_v2_7.md:282-288. Live EvolutionEvent nodes exist, but canonical Rule relationships are absent (see §3). |
| 8 | Rule | MISSING — no Rule writer in Protocol v2 | MISSING — no Rule storage/writer | MISSING — no Rule table/writer | MISSING — no CREATE Rule path found | Canonical Rule fields are therefore all missing (judgment_memory_v2_7.md:290-294). Live supplemental query returned Rule: 0. |
| 9 | TransferPattern | PARTIAL — write_transfer_pattern exists (protocol.py:299-315) | PARTIAL — writer/storage exist (memory_store.py:346, :873-950) | PARTIAL — table/writer exist (sqlite_store.py:655-670, :1639-1740) | PARTIAL — node and domain edges exist (age_graph_store.py:1739-1836, :1130-1171) | The canonical every-node domain rule is not satisfied: TransferPattern has source_domain/target_domain, not a single domain property (judgment_memory_v2_7.md:224, :296-301). Its EvolutionEvent edge is conditional and live count was 0. |
| 10 | EvidenceReceipt | IMPLEMENTED — append_evidence_receipt (protocol.py:228-238) | IMPLEMENTED — receipt chain dicts (memory_store.py:335-336, :655-703) | IMPLEMENTED — evidence_receipts table/writer (sqlite_store.py:614-628, :1323-1404) | IMPLEMENTED for SDK graph audit (age_graph_store.py:1506-1674) | SOC intentionally does not use graph EvidenceReceipt nodes; its hash-chain is authoritative (jm_v27_validation_report_v1.md:108-114). Thus the universal live-graph claim is partial even though the SDK contract is implemented. |
| 11 | CentroidCheckpoint | IMPLEMENTED — write_centroid_checkpoint (protocol.py:267-281) | IMPLEMENTED — protocol checkpoint dict (memory_store.py:339, :777-815) | IMPLEMENTED — centroid_checkpoints table/writer (sqlite_store.py:441-459, :1553-1638) | IMPLEMENTED — node writer and checkpoint edges (age_graph_store.py:1356-1427, :1103-1125) | No required-property gap found in the protocol-v2 writer; required fields are judgment_memory_v2_7.md:320-325. Live all five domains are present (jm_v27_validation_report_v1.md:41-43). |
| 12 | Fingerprint | IMPLEMENTED — write_fingerprint (protocol.py:255-265) | IMPLEMENTED — _fingerprints and writer (memory_store.py:338, :745-775) | IMPLEMENTED — fingerprints table/writer (sqlite_store.py:644-653, :1485-1552) | IMPLEMENTED — node and domain-summary edge (age_graph_store.py:1273-1326, :1080-1098) | No required-property gap found in the writers; required fields are judgment_memory_v2_7.md:327-330. |
| 13 | ConservationStatus | IMPLEMENTED — write_conservation_status (protocol.py:240-253) | IMPLEMENTED — _conservation_snapshots and writer (memory_store.py:337, :704-743) | IMPLEMENTED — conservation_snapshots table/writer (sqlite_store.py:630-642, :1405-1484) | IMPLEMENTED — node and domain-summary edge (age_graph_store.py:1176-1241, :1080-1098) | No required-property gap found; counts_scope is explicitly verified_only in AGE (age_graph_store.py:1199-1202). Live all five domains are present (jm_v27_validation_report_v1.md:41-42). |

## §3 EDGE TYPE INVENTORY (Part B)

The §4.2 heading says 18 edges, but it enumerates 20 source-target patterns. Duplicate relationship names are kept separate here because Observation and Decision have different required topology. Live counts below are from a read-only AGE query against soc_graph; the query mechanism follows the AGE preamble and cypher pattern in graph_census_v2.py:15-18 and :37-48.

| Edge | AGE Method | Line | Status |
|---|---|---:|---|
| Observation -[:IN_DOMAIN]-> Domain | None | — | MISSING — write_observation creates only the Observation node (age_graph_store.py:1013-1053). Live count: 0. |
| Observation -[:ABOUT]-> DomainContext | None | — | MISSING — no Observation-to-context Cypher in write_observation (age_graph_store.py:1032-1053). Live count: 0. |
| Observation -[:HAS_FACTOR_VECTOR]-> FactorVector | None | — | MISSING — vector is serialized as Observation properties, not a FactorVector node/edge (age_graph_store.py:1045-1049). Live count: 0. |
| Decision -[:IN_DOMAIN]-> Domain | write_decision → _link_decision_to_domain | 558-604, 649-663 | PARTIAL — Cypher exists, but live edge count was 0; write catches/logs edge failures (age_graph_store.py:598-609). |
| Decision -[:ABOUT]-> DomainContext | link_entity | 1978-2040 | IMPLEMENTED — live count 24. |
| Decision -[:HAS_FACTOR_VECTOR]-> FactorVector | _create_factor_vector_node | 665-705 | PARTIAL — Cypher exists but is conditional on factor extraction and live count was 0. |
| Decision -[:HAS_OUTCOME]-> Outcome | write_outcome | 941-968 | IMPLEMENTED — live count 1,964; report confirms SDK Decision→Outcome relationships (jm_v27_validation_report_v1.md:108-114). |
| Decision -[:EMITTED_RECEIPT]-> EvidenceReceipt | append_evidence_receipt | 1627-1652 | IMPLEMENTED — live count 359. |
| Decision -[:SNAPSHOT_AFTER]-> CentroidCheckpoint | _link_checkpoint_edges / checkpoint path | 1103-1125, 2617-2622 | IMPLEMENTED — live count 75. |
| Decision -[:USED_RULE]-> Rule | None | — | MISSING — no Rule writer or AGE edge creator found. |
| Decision -[:TRIGGERED_EVOLUTION]-> EvolutionEvent | None | — | MISSING — write_evolution_event only creates the event node (age_graph_store.py:1684-1737); live count 0. |
| EvolutionEvent -[:PROMOTED_RULE]-> Rule | None | — | MISSING — no Rule node/writer or promotion edge. |
| EvolutionEvent -[:ROLLED_BACK_RULE]-> Rule | None | — | MISSING — no Rule node/writer or rollback edge. |
| Rule -[:APPLIES_TO]-> DomainContext | None | — | MISSING — no Rule node/writer or applies-to edge. |
| CentroidCheckpoint -[:DERIVED_FROM]-> Decision | _link_checkpoint_edges | 1103-1125 | IMPLEMENTED — live count 75. |
| Fingerprint -[:SUMMARIZES_DOMAIN]-> Domain | _link_domain_summary | 1080-1098; called at 1320-1326 | IMPLEMENTED — live count 211. |
| ConservationStatus -[:SUMMARIZES_DOMAIN]-> Domain | _link_domain_summary | 1080-1098; called at 1235-1241 | IMPLEMENTED — live count 190. |
| TransferPattern -[:FROM_DOMAIN]-> Domain | _link_transfer_edges | 1130-1147 | IMPLEMENTED — live count 6. |
| TransferPattern -[:TO_DOMAIN]-> Domain | _link_transfer_edges | 1130-1158 | IMPLEMENTED — live count 6. |
| TransferPattern -[:DERIVED_FROM]-> EvolutionEvent | _link_transfer_edges | 1130-1171 | PARTIAL — conditional on evolution_event_id; live count 0. |

The missing Observation edges are consistent with the node writer’s current shape, but they are not canonical §4.2 topology. The Rule/procedural edges are not merely absent from the current census; no AGE construction path was found.

## §4 PROTOCOL v2 METHODS (Part C)

All 14 requested methods are present in the Protocol v2 contract and all three implementations. The AGE adapter also exposes the base GraphStore methods and forwards required arguments; structural adapter tests check method presence and signatures (ci-platform/tests/test_age_sdk_adapter.py:261-291).

| # | Method | Protocol:Line | InMemory:Line | SQLite:Line | AGE:Line | Gap |
|---:|---|---:|---:|---:|---:|---|
| 1 | write_decision | 19 | 433 | 995 | 558 | None at method level; canonical-property caveat in §2. |
| 2 | write_outcome | 30 | 549 | 1159 | 886 | None at method level; event-property caveat in §2. |
| 3 | write_observation | 211 | 603 | 1247 | 1013 | None at method level; canonical Observation edges missing in §3. |
| 4 | count_decisions | 80 | 1135 | 2212 | 2157 | None. |
| 5 | count_verified_decisions | 74, 359 | 1117 | 2231 | 2127 | None; lifecycle predicate reviewed in §5. |
| 6 | append_evidence_receipt | 228 | 655 | 1323 | 1506 | None for SDK graph audit; SOC intentionally uses hash-chain audit. |
| 7 | write_conservation_status | 240 | 704 | 1405 | 1176 | None. |
| 8 | write_fingerprint | 255 | 745 | 1485 | 1273 | None. |
| 9 | write_centroid_checkpoint | 267 | 777 | 1553 | 1356 | None. |
| 10 | write_evolution_event | 283 | 817 | 1862 | 1684 | Partial semantic gap: no Rule links/status. |
| 11 | link_entity | 338 | 1017 | 1958 | 1978 | None for Decision→DomainContext; Observation links remain absent. |
| 12 | archive_decisions | 347 | 1624 | 3208 | 2916 | None at method level. |
| 13 | domain_scoped_reset | 356 | 1667 | 3289 | 2973 | AGE is intentionally forbidden on shared soc_graph (age_graph_store.py:3000-3007); see blocker 5. |
| 14 | close | 110 | 1963 | 3336 | 3155 | None. |

## §5 DECISION LIFECYCLE (Part D)

### D1 — creation status

CONFORMANT. InMemory writes status pending (memory_store.py:461-477); SQLite inserts pending (sqlite_store.py:1028-1050); AGE governed decisions set status pending (age_graph_store.py:770-794).

### D2 — outcome transition

CONFORMANT. InMemory sets correct and status to confirmed/overridden (memory_store.py:585-601); SQLite computes the same status and updates both columns (sqlite_store.py:1177-1228); AGE computes the same status and sets both d.status and d.correct in the same Cypher operation (age_graph_store.py:912-951).

### D3 — verified counting

CONFORMANT with a documented legacy compatibility predicate. InMemory counts confirmed/overridden or an outcome record (memory_store.py:1117-1126); SQLite counts only confirmed/overridden rows (sqlite_store.py:2231-2243); AGE counts confirmed/overridden and retains a legacy d.outcome fallback (age_graph_store.py:2127-2142). The outcome-aligned correctness model is explicitly validated (jm_v27_validation_report_v1.md:75-88).

### D4 — Observation lifecycle exclusion

CONFORMANT. InMemory Observation records contain domain/content/timestamps but no status (memory_store.py:603-653); SQLite’s observation table has no status column (sqlite_store.py:581-592); AGE’s Observation CREATE has no status (age_graph_store.py:1036-1051). This matches the design requirement that preview/read observations are excluded from V (judgment_memory_v2_7.md:414-421).

## §6 BLOCKER STATUS (Part E)

| Blocker | Status | Evidence and finding |
|---|---|---|
| 1. AGEGraphStoreAdapter conformance | PARTIAL | The adapter has the GraphStore surface and forwards methods/signatures (age_sdk_adapter.py:30-121, :123-287, :289-623), and unit tests assert presence/signature (ci-platform/tests/test_age_sdk_adapter.py:261-291). However, the evidence is structural/fake-store and the review found no separate exhaustive live ProtocolV2 adapter assertion covering every canonical node/edge behavior. Method surface is implemented; runtime/live completeness is not fully proven. |
| 2. SOC AGE schema vs canonical vocabulary | PARTIAL / OPEN | Canonical design requires the 13 labels and 18-heading edge model (judgment_memory_v2_7.md:222-374). The live report confirms SOC’s audit is intentionally hash-chain and has no graph Outcome/EvidenceReceipt requirement (jm_v27_validation_report_v1.md:108-114), but it does not establish a complete SOC label/edge compatibility mapping. Supplemental live query found zero Rule nodes and zero canonical Rule edges. |
| 3. Conservation V definition: verified only | IMPLEMENTED | All store count paths are domain-scoped and verified-status based (memory_store.py:1117-1126; sqlite_store.py:2231-2243; age_graph_store.py:2127-2142). AGE count_correct is property-only (age_graph_store.py:2144-2155), and live validation proves outcome-aligned counts for SDK domains and all SOC triage Decisions (jm_v27_validation_report_v1.md:75-88). |
| 4. Preview/read write contamination | PARTIAL / OPEN | Required Observation writers exist in all stores (memory_store.py:603-653; sqlite_store.py:1247-1321; age_graph_store.py:1013-1053) and the design excludes observations from lifecycle (judgment_memory_v2_7.md:418-421). But complete route/path closure remains unproven: validation records only 33/47 independently evidenced paths (jm_v27_validation_report_v1.md:150-156). No evidence here proves every preview/read route uses write_observation rather than a Decision writer. |
| 5. Demo reset for AGE, domain-scoped | OPEN | AGE rejects domain_scoped_reset on soc_graph and permits it only on protocol_v2_test graphs/domains (age_graph_store.py:2973-3007). demo.py reset is record-freeze/preseed state, not an AGE domain reset (demo.py:1181-1199), so shared-graph demo reset is not closed. |
| 6. Demo bundle format | OPEN | Bundle restore requires a direct SQLite store (copilot_sdk/demo/bundle.py:43-62), writes SQLite tables directly (:73-133), and explicitly logs that AGE migration is required for graph parity (:139-142). This is not an AGE-native canonical bundle restore. |

## §7 TEST GAPS (Part F)

| Gap | Has Test? | Test Needed |
|---|---|---|
| Generic Decision writer does not guarantee all §4.1 governed properties | Partial — protocol.py:19-28 versus governed contract at :191-209 | Parameterized store test asserting every canonical Decision property after generic and governed writes. |
| Outcome lacks dedicated outcome_id/reward/verifier/override-reason parity | Partial — judgment_memory_v2_7.md:239-243; memory_store.py:575-584; sqlite_store.py:1194-1209; age_graph_store.py:952-964 | Cross-store event-property conformance test with exact Outcome node/table payload. |
| FactorVector has no standalone protocol writer and no all-store canonical node | Partial — protocol.py:191-225; sqlite_store.py:604-612; age_graph_store.py:665-705 | Protocol/store test requiring a FactorVector record and all required hash/shape/schema fields. |
| Domain node writer absent outside AGE | No — memory_store.py:327-330; sqlite_store.py:407-410; AGE anchor at age_graph_store.py:1055-1075 | Five-store/domain-anchor conformance test, or explicitly document Domain as AGE-only and test that boundary. |
| DomainContext node writer absent outside AGE; fields incomplete | Partial — memory_store.py:1017-1046; sqlite_store.py:571-579; age_graph_store.py:2017-2040 | link_entity cross-store test that reads a canonical DomainContext payload and verifies attributes/updated_at policy. |
| EvolutionEvent status and Rule relations absent | No — age_graph_store.py:1684-1737 and no Rule writer found | Evolution lifecycle test for status plus promoted/rolled-back Rule edges. |
| TransferPattern lacks single domain property | No — judgment_memory_v2_7.md:224, :296-301; age_graph_store.py:1813-1827 | Schema contract test for the global domain invariant, or an approved exception test for source/target-domain nodes. |
| SOC EvidenceReceipt graph exception | Yes for audit model; no graph parity test — jm_v27_validation_report_v1.md:108-114 | Test /api/audit/verify hash-chain semantics and explicitly assert graph EvidenceReceipt is not required for SOC. |
| Observation IN_DOMAIN edge | No — age_graph_store.py:1013-1053 | AGE integration test writing an Observation and asserting the edge. |
| Observation ABOUT edge | No — age_graph_store.py:1032-1053 | AGE integration test with entity_id asserting Observation→DomainContext. |
| Observation HAS_FACTOR_VECTOR edge | No — age_graph_store.py:1045-1049 | AGE integration test with factor vector asserting a FactorVector node and edge. |
| Decision IN_DOMAIN live absence | Partial — age_graph_store.py:598-609, :649-663 | Live AGE test that writes a Decision, verifies the edge, and fails if the helper logs/ignores edge-creation failure. |
| Decision HAS_FACTOR_VECTOR live absence | Partial — age_graph_store.py:665-705 | Live AGE factor-vector persistence test with a known numeric vector and exact edge assertion. |
| Decision/outcome, receipt, checkpoint, summary, and transfer edges | Yes at broad validation surface; incomplete per-edge — jm_v27_validation_report_v1.md:108-114 | One AGE edge census assertion per source/target pattern, not only aggregate node counts. |
| TransferPattern DERIVED_FROM conditional path | No — age_graph_store.py:1130-1171 | Write an EvolutionEvent and linked TransferPattern, then assert the edge. |
| USED_RULE/TRIGGERED_EVOLUTION/PROMOTED/ROLLED_BACK/APPLIES_TO | No — no Rule writer or edge construction in age_graph_store.py; event writer is :1684-1737 | Rule/evolution graph integration suite covering every procedural edge. |
| Adapter complete ProtocolV2 runtime/live behavior | Partial structural tests — ci-platform/tests/test_age_sdk_adapter.py:261-291 | ProtocolV2 structural test plus live AGE execution of all 14 methods and representative edges. |
| Preview/read contamination | No complete route audit — judgment_memory_v2_7.md:418-421; jm_v27_validation_report_v1.md:150-156 | Route-level tests proving preview writes Observation and never Decision; include count/lifecycle assertions. |
| AGE domain reset on shared graph | No — age_graph_store.py:2973-3007 | Safe operator-level reset test using an explicit disposable AGE graph and a production refusal test for soc_graph. |
| AGE-native demo bundle parity | SQLite bundle tests exist (tests/demo/test_bundle.py:84-105), but bundle implementation is SQLite-only (copilot_sdk/demo/bundle.py:43-62, :139-142) | AGE bundle import/export test with domain scoping, Outcomes, checkpoints, receipts, and rollback on failure. |
| Full path closure | No — current report explicitly says 33/47 only (jm_v27_validation_report_v1.md:150-156) | Independent 47-path audit. |

## §8 READING LOG

Read fully before this review:

- copilot-sdk/docs/design/judgment_memory_v2_7.md — canonical §4.1 labels/properties, §4.2 edges, §5 lifecycle, §9 blockers, §12a Protocol v2.
- copilot-sdk/docs/validation/jm_v27_validation_report_v1.md — census, correctness, audit, blocker/scorecard, suite evidence, and verdict.
- copilot-sdk/CLAUDE.md.
- copilot-sdk/copilot_sdk/graph/protocol.py.
- copilot-sdk/copilot_sdk/graph/memory_store.py.
- copilot-sdk/copilot_sdk/graph/sqlite_store.py.
- ci-platform/ci_platform/graph/age_graph_store.py.
- ci-platform/ci_platform/graph/age_sdk_adapter.py.
- copilot-sdk/copilot_sdk/demo/bundle.py and copilot-sdk/demo.py for blocker 5/6 evidence.
- ci-platform/tests/test_age_sdk_adapter.py and the SDK graph/bundle conformance tests used as test evidence.

Read-only live evidence collected against soc_graph on 2026-08-01:

- Canonical census via scripts/graph_census_v2.py --dsn ... --graph soc_graph.
- Supplemental AGE label and source-target edge counts using the same LOAD age, search-path, and cypher pattern implemented at scripts/graph_census_v2.py:40-48.
- No source or test files were modified. The only write in this review is this document.

READY: YES — review document complete; implementation is not authorized by this review.
