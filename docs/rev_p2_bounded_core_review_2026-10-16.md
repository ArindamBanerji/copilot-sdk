**VERDICT: FAIL — 3 P1, 3 P2, 4 P3 findings.**

The protocol signatures, capability gates, memory implementation, and basic wrapper delegation are sound. Three correctness failures remain in namespace composition and AGE retention.

No files were modified. The session-state entry requested in Step 5 is provided below for later use.

The recorded full-suite baselines pass the precheck. This review additionally ran **202 focused test cases by direct invocation: 202 passed**. These invocations bypass pytest collection/hooks and are **not a fresh full-suite run**. Additional database-free probes reproduced the findings below; live AGE integration tests were inspected but not rerun.

**Precheck**

| Check | Result | Evidence |
|---|---|---|
| SC-A | PASS | SDK `REV-P2a-FIXER`: PASS; prior findings closed. |
| SC-B | PASS | Platform `REV-FIX-P2b`: PASS WITH OBSERVATIONS; prior R01–R03 closed; zero P1/P2. |
| SC-C | PASS | SDK `IMPL-BOUNDED-WRAPPERS-P2c`: DONE. |
| SC-D | PASS | Recorded SDK: **4,719 passed, 1 xfailed**. Platform: **804 passed**, zero failed/skipped. |

Several checklist examples differ from the reviewed P1 contract. I assessed conformance against the actual protocol:

- Its four methods are `query_decisions`, **`count_decisions`**, `aggregate_decisions`, and `get_decision_changes`. There is no public `feed_event`.
- `as_of_generation` is a **current-generation fence**, not a historical snapshot selector.
- Metrics are `count`, `correct_count`, and `avg_confidence`.
- Results use `DecisionPageResult`, `DecisionAggregate`, and `DecisionChangePage`.
- AGE activation uses a persisted per-domain marker, not `BOUNDED_AGE_ACTIVATED`.
- The implementation uses `bounded_projection_migration.py`; no migration `007` or platform `graph/production.py` was found.

**Findings**

File references:

- [namespace.py](C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects/copilot-sdk/copilot_sdk/graph/namespace.py:27)
- [age_graph_store.py](C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects/ci-platform/ci_platform/graph/age_graph_store.py:786)
- [age_client.py](C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects/ci-platform/ci_platform/graph/age_client.py:346)
- [bounded_projection_migration.py](C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects/ci-platform/ci_platform/graph/bounded_projection_migration.py:55)
- [factory.py](C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/kaggle_experiments/claude_projects/copilot-sdk/copilot_sdk/graph/factory.py:271)

| # | Severity | Check | File / line | Finding | Recommendation |
|---|---|---|---|---|---|
| R1 | **P1** | C3, H3 | `namespace.py:27,88,103,712,757` | Namespace validation and rewriting descend into opaque `options_factors` and `learning_metadata`. Valid payloads can be rejected or silently changed. | Rewrite only declared routing fields; preserve opaque projection fields. Add direct-read and feed regressions. |
| R2 | **P1** | C3, G1, H3 | `namespace.py:54`; `age_graph_store.py:43,786` | Namespace produces physical domains such as `arm::scoring`; AGE’s domain validator rejects `:`. The bounded AGE/namespace composition cannot operate with this format. | Agree on a shared safe physical-domain representation across activation, reads, writes, and feeds. Test actual cross-repo composition. |
| R3 | **P1** | G1, H1 | `age_graph_store.py:3917–3932`; `age_client.py:523` | Retention candidate IDs still pass through the legacy scalar decoder. A valid string ID `"null"` becomes `None` and is removed from the candidate list. | Use identity-preserving decoding for retention IDs; test archival and tombstones for adversarial string IDs. |
| R4 | **P2** | E2–E3, G3 | `bounded_projection_migration.py:55`; `factory.py:271` | Duplicate activation markers are reported as “not activated.” The factory interprets this as permission to downgrade to legacy AGE, despite the documented promise that corrupt readiness propagates. | Distinguish absent activation from corrupt activation with explicit exception types. Add duplicate-marker coverage. |
| R5 | **P2** | G4 | `age_client.py:346–385` | If pool creation succeeds but `pool.wait()` fails, the exception handler drops the pool reference without closing it. | Close the partially initialized pool before clearing the reference. Retain a failure-path resource test. |
| R6 | **P2** | J3 | `tests/test_bounded_projection_wrappers.py:260–320` | Factory tests cover activated, absent-marker, and corrupt-domain-anchor cases, but do not exercise an actual bounded-adapter `ImportError`. | Add a test retaining the legacy adapter while making the bounded adapter import fail. |
| R7 | **P3** | I1 | SDK `docs/session_state.md:11052` | The repository records 18/18 but cannot map those checks to the original CHECK-01–20. | Keep the two-check gap as a downstream verification observation, as requested. Do not invent omitted check numbers. |
| R8 | **P3** | INV-4 | `bounded_projection.py:32,36` | New compiler manifests `COLLECTIONS` and `GROUPS` are mutable module-global dictionaries. Other reviewed files also contain existing mutable globals. | Freeze compiler manifests; distinguish permitted infrastructure registries from prohibited mutable application state. |
| R9 | **P3** | J1 | Wrapper test file | There are 34 real cases, but the requested group counts total **40**, and actual group distribution differs. | Maintain a semantic coverage matrix rather than claiming the requested group counts were met. |
| R10 | **P3** | E4, F2–F5, G3 | Review/implementation terminology | Several checklist expectations describe APIs or activation mechanisms absent from the accepted implementation contract. | Align downstream review criteria with P1 and the recorded marker-based activation design. |

R5 concerns shared AGE infrastructure used by P2; this review does not establish that P2 introduced that failure path.

The strongest reproductions were:

| Probe | Observed result |
|---|---|
| Namespace journal payload `options_factors={"domain":"customer-value"}` | Query and feed raise `RuntimeError` about namespace bounds. |
| Namespace journal payload `options_factors={"domain":"arm::customer-value"}` | Query and feed silently return `"customer-value"`. |
| Namespace scoring payload `learning_metadata={"verifier":{"domain":"customer-value"}}` | Query and feed reject the payload. |
| Namespaced AGE bounded read using `arm::scoring` | AGE raises unsupported-domain `ValueError` before connection use. |
| Retention with newest ID `"z"`, older ID `"null"`, `keep_recent=1` | Returns **0 archived**, although one record should be archived. |
| Readiness with one domain anchor and two activation markers | Produces the factory’s legacy-fallback error text. |
| Pool whose `wait()` raises | Pool remains unclosed, including after awaiting client close. |

The namespace/AGE probe bypassed adapter construction to isolate domain validation; it was not a live activation test.

**File architecture summary**

Paths below are relative to their named repository. Line counts reflect the inspected working tree.

| Repository / file | Lines | Main responsibility | Attribution |
|---|---:|---|---|
| SDK `copilot_sdk/graph/protocol.py` | 694 | Graph protocols; runtime-checkable `BoundedProjectionStore` | P1 context |
| SDK `copilot_sdk/graph/query.py` | 246 | Filters, projections, cursors, pages, aggregates, change pages, exceptions | P1; unchanged by P2c |
| SDK `copilot_sdk/graph/memory_store.py` | 3,147 | `InMemoryGraphStore`; normalization, bounded reads, aggregates, generations, event snapshots | P2a |
| SDK `copilot_sdk/graph/capabilities.py` | 32 | `require_bounded_projection_store`, `has_bounded_projection` | P2c new |
| SDK `copilot_sdk/graph/legacy_signal_filter.py` | 341 | Legacy filter and bounded variant | P2c modified |
| SDK `copilot_sdk/graph/tenant_store.py` | 395 | Tenant wrappers; filter injection and governed-write stamping | P2c modified |
| SDK `copilot_sdk/graph/namespace.py` | 786 | Physical/logical domain views; bounded page/feed reconstruction | P2c modified |
| SDK `copilot_sdk/graph/factory.py` | 286 | Backend loading, capability-aware wrappers, AGE activation fallback | P2c modified |
| SDK `copilot_sdk/graph/__init__.py` | 68 | Public exports | P2c modified |
| SDK `copilot_sdk/graph/production.py` | 132 | Production identity/readiness boundary | Supporting context |
| Platform `ci_platform/graph/age_client.py` | 1,524 | Connections, transactions, bounded decoding, SQL/Cypher safety | P2b modified |
| Platform `ci_platform/graph/age_graph_store.py` | 4,648 | GraphStore operations; transactional mutation/feed hooks | P2b modified |
| Platform `ci_platform/graph/age_sdk_adapter.py` | 902 | Legacy and bounded SDK adapters; shared result construction | P2b modified |
| Platform `ci_platform/graph/bounded_projection.py` | 272 | Function-based compiler, manifests, normalization, predicates, aggregates | P2b |
| Platform `ci_platform/graph/bounded_projection_migration.py` | 266 | Activation, backfill, advisory locks, generations, events, bounded reads | P2b |

| Test file | Lines | Coverage |
|---|---:|---|
| SDK `tests/test_bounded_projection_wrappers.py` | 320 | Wrapper policy, composition, guards, factory, capabilities |
| SDK `tests/test_bounded_capability_compatibility.py` | 130 | Runtime membership, exports/import order, composed-store compatibility |
| SDK `tests/test_bounded_projection_contract.py` | 663 | Actual P2a memory contract tests; requested `test_bounded_projection_memory.py` does not exist |
| Platform `tests/test_bounded_projection.py` | 64 | Compiler validation and normalization |
| Platform `tests/test_bounded_projection_age.py` | 223 | Live bounded reads, generations, feeds, aggregates, injection cases |
| Platform `tests/test_bounded_projection_migration.py` | 75 | Activation, backfill, rollback, domain independence |
| Platform `tests/test_bounded_projection_fixer.py` | 173 | String identity, nonfinite values, literal-aware safety regressions |

Supplemental existing-test changes were inspected in `test_graphstore_namespace.py` (372 lines), `test_legacy_signal_filter.py` (714), `test_graph_production_boundary.py` (248), and platform `test_age_graph_store.py` (2,627).

**Checklist results**

| Check | Rating | Assessment |
|---|---|---|
| A1 | OK | Memory implements all four actual protocol methods. Exact signature comparison passed. |
| A2 | OK | AGE adapter implements the same four signatures exactly. |
| A3 | OK | All bounded wrappers delegate reads/counts/aggregates/changes to their primary; they do not reproduce storage/query logic. |
| A4 | OK | Protocol is runtime-checkable; runtime membership checks work. |
| B1 | OK | Required capability failure raises `RuntimeError`. |
| B2 | OK | Boolean helper directly uses `isinstance`. |
| B3 | OK | Both helpers are publicly re-exported. |
| C1 | OK | Bounded legacy-filter constructor checks bounded primary membership. |
| C2 | OK | Bounded tenant constructor checks membership; governed writes stamp tenant metadata and preserve the V2 signature. |
| C3 | **P1** | Cursor and watermark preservation work; opaque payload preservation and AGE composition fail—R1/R2. |
| C4 | OK | Each bounded wrapper subclasses its legacy counterpart. |
| D1 | OK | Legacy signal wrapper blocks `query_decisions`. |
| D2 | OK | Blocks `aggregate_decisions`. |
| D3 | OK | Blocks `get_decision_changes`. |
| D4 | OK | Tenant legacy wrapper has the same guards. |
| D5 | OK | Namespace legacy wrapper has the same guards. |
| D6 | OK | All guards raise `AttributeError`. |
| E1 | OK | `_tenant_store` checks bounded capability. |
| E2 | OK | Bounded primary selects bounded wrappers. |
| E3 | **P2** | Non-bounded primary selects legacy wrappers correctly, but corrupt activation can reach that fallback—R4. |
| E4 | **P3** | No environment-variable gate; persisted activation marker is the recorded design—R10. |
| E5 | OK | Missing bounded-adapter import returns `None`, allowing the available legacy AGE adapter. Missing all ci-platform support still cannot supply AGE. |
| F1 | OK | Cursor pagination and `next_cursor` implemented. |
| F2 | OK | Implements the actual generation-fence semantics; stale generation raises `DecisionGenerationChanged`. |
| F3 | OK | Actual contract metrics implemented, including count and average confidence. Generic sum is not a contract metric. |
| F4 | OK | Returns `DecisionChangePage` with ordered events and watermarks. |
| F5 | OK | Internal mutation-event emission increments per-domain generations. No public `feed_event` is required. |
| F6 | OK | Generation/read/write coordination uses an instance `RLock`. |
| G1 | **P1** | Core bounded compiler is sound; domain composition and retention identity failures remain—R2/R3. |
| G2 | OK | Tenant predicates are compiled from the injected tenant filter. |
| G3 | **P2** | Same-graph migration supplies anchors, activation, canonical fields, and events; corrupt activation classification is wrong—R4. |
| G4 | **P2** | Normal checkout/return uses context management; partial initialization leaks—R5. |
| G5 | OK | Generation checks and reads execute under the coordinated transaction/lock mechanism. |
| H1 | OK | AGE constructs the actual SDK result classes; no duplicate incompatible public dataclasses. |
| H2 | OK | Same SDK filter/page/projection types and signatures. |
| H3 | **P1** | Legacy/tenant pass-through is correct; namespace transformation violates opacity—R1. |
| H4 | OK | Cross-repo imports exist, but inspected import structure avoids a circular initialization dependency. Compiler remains SDK-independent. |
| I1 | **P3** | Documented assertions assessed; original two-check mapping unavailable—R7. |
| J1 | **P3** | 34 substantive cases exist; requested group counts are not met literally—R9. |
| J2 | OK | Governed tenant stamping is tested at wrapper-test line 139. |
| J3 | **P2** | Activation cases exist; actual `ImportError` fallback is not tested—R6. |
| J4 | OK | Added composed memory-store compatibility test is present. |
| J5 | OK | Empty, single-page, multi-page, tied-key, cursor/fence, and invalid-page cases exist. |
| J6 | OK | Injection coverage includes quoting, backslashes, dollar delimiters, and syntax-like bound data. |

Namespace construction additionally requires the V2 interface used by its parent. That is a stronger construction requirement than bounded membership alone, and is enforced at runtime.

**Documented P2c self-verification**

The session entry contains a prose list, not numbered CHECK-01–20. The following is an assessment of its documented assertions, grouped into 18 review rows; these are **not reconstructed original check numbers**.

| Documented assertion | Review result |
|---|---|
| Legacy bounded construction | PASS |
| Tenant bounded construction | PASS |
| Namespace bounded/V2 construction | PASS |
| Negative attribute guards | PASS |
| Conditional wrapper selection | PASS |
| Fail-closed capability narrowing | PASS |
| Legacy AGE fallback behavior | **Qualified: R4** |
| Import-cycle checks | PASS |
| Runtime protocol membership | PASS |
| Composed end-to-end write/read | PASS for tested memory composition |
| Immutable filter preservation | PASS |
| Tenant conflict rejection | PASS |
| Exact four bounded signatures | PASS for memory, AGE, and all three wrappers |
| Exact governed-write V2 signature | PASS |
| Sorted/unique public exports | PASS |
| No public signature removals | No removal found in reviewed P2 surface |
| No `_StoreProxy` / wrapper `DecisionStore` references | PASS |
| Unchanged `query.py` hash | PASS; matches recorded `F881719A…98FF` |

The **two-check gap remains P3 informational**, per your clarification. Available evidence cannot establish whether those two original checks were merged, N/A, or skipped.

Wrapper cases distribute as follows:

| Group | Requested | Actual cases |
|---|---:|---:|
| A — Legacy | 7 | 5 |
| B — Tenant | 10 | 7 |
| C — Namespace | 8 | 5 |
| D — Guards | 6 | 9 |
| E — Factory | 5 | 7 |
| F — Capabilities | 4 | 1 combined case |
| **Total** | **40** | **34** |

Passing totals therefore do not prove the requested semantic matrix was covered. R1, R2, R4, and R6 identify concrete gaps.

**Architectural invariants**

Searches covered the reviewed P2 production files; module-level assignments were also inspected structurally.

| Invariant | Result | Evidence / scope |
|---|---|---|
| INV-1: no `_StoreProxy` | PASS | No matches in P2 production files. |
| INV-2: no `DecisionStore` wrapper imports | PASS | No matches in the three wrapper files. |
| INV-3: no SOC imports in S2P code | PASS, scoped | No such imports in P2 files. Shared AGE client contains existing SOC-specific queries; these are not SOC-module imports into S2P code. |
| INV-4: no mutable module globals | **VIOLATION** | New `bounded_projection.py:32,36` dictionaries. Existing examples include `memory_store.py:75,504`, `factory.py:31`, and the locked client registry at `age_client.py:1435`. Export lists are declarations, not application state. |
| INV-5: no static conservation JSON | PASS | No conservation JSON file loading/static-data source found in P2 files. |
| INV-6: platform data through GraphStore | PASS, scoped | P2 consumer-facing access remains through GraphStore adapters; compiler/migration are storage implementation internals. |
| INV-7: sqlite3 only in outbox | PASS, scoped | No `sqlite3` matches in P2 production files. |
| INV-8: scorer math frozen | PASS for recorded P2 scope | P2 does not claim scorer changes. The working tree contains separate scorer changes, so this is not a certification of all unrelated workspace edits. |

**Blast radius**

The static scan found **363 direct-import consumer files outside the identified P2 source/test change set**, across SDK, platform, and S2P. It handled absolute and relative Python imports. It does not prove every dynamically constructed import or transitive runtime dependency.

No removed import or public-signature break was detected in this inventory. That is a static compatibility assessment; these 363 consumers were not individually executed.

| Consumer file / family | Imports from | Breaking? | Action needed |
|---|---|---|---|
| SDK `copilot_sdk/scoring/scorer.py` | Memory, legacy namespace | Existing API preserved; bounded capability is deliberately unavailable through the legacy namespace | Future bounded consumers must explicitly choose the bounded variant after R1/R2. Preserve frozen math. |
| SDK `apps/s2p_differentiation/engine.py` and namespace-sharing tests | Memory / namespace | No existing signature break detected | Add AGE namespace integration coverage before using that composition. |
| SDK and S2P app startup/CLI files listed below | Factory | Conditional runtime exposure to R4/R5 | Fix factory/readiness/resource behavior centrally; downstream startup must require bounded capability where mandated. |
| AGE adapters, migration tools, retention users | AGE client/store/adapter | R3 affects retention; R5 affects initialization failure | Central fixes plus regression coverage. |
| Memory-backed examples, experiments, tests | Memory / graph exports | No import/signature break detected | No mandatory API update. |
| Graph-export consumers | `copilot_sdk.graph` | Exports are additive | No mandatory import update. |
| Parallel Phase 3 files | Factory / AGE exception types | No finding attributed to their uncommitted edits | Verify final consumer integration in REV-P4. |

The complete direct-import inventory is grouped below by directory and imported module. Every filename in a row shares the static assessment above. `graph` means SDK package re-exports; module basenames otherwise identify the source.

| Consumer directory | Consumer files | Imports from |
|---|---|---|
| `ci-platform/ci_platform/graph` | `__init__.py` | age_client, age_graph_store, age_sdk_adapter |
| `ci-platform/tests` | `test_age_client.py`, `test_age_cypher_compat.py`, `test_age_escaping.py`, `test_age_type_roundtrip.py`, `test_counter_store_live_age.py`, `test_counter_store_route_readiness.py`, `test_graph_backend_switcher.py` | age_client |
| same | `test_platform_state_transactions.py` | age_client, age_graph_store |
| same | `test_age_graph_store_v.py` | age_client, age_graph_store, graph |
| same | `conftest.py` | age_client, age_graph_store, memory_store |
| same | `test_age_checkpoint_count.py`, `test_age_evolution_event_link.py`, `test_age_graph_store_topology.py`, `test_domain_enforcement.py`, `test_g040_domain_isolation.py`, `test_soc_outcome_checkpoint_transaction.py` | age_graph_store |
| same | `test_age_sdk_adapter.py` | age_graph_store, age_sdk_adapter, graph |
| `copilot-sdk` | `demo.py` | age_client, age_graph_store |
| same | `conftest.py` | age_client, age_sdk_adapter |
| `copilot-sdk/apps/dataops/backend/app` | `graph_queries.py` | age_client |
| same | `graph_status.py`, `main.py` | factory |
| `copilot-sdk/apps/dataops/backend/tests` | `test_graph_queries.py` | age_client |
| same | `test_dataops_fixture_closure.py` | age_client, graph |
| same | `test_dataops_backend.py` | factory, graph |
| same | `test_bundle_wiring.py`, `test_cohort_status.py`, `test_trust_perturbation.py` | graph |
| same | `test_dataops_graph_status.py`, `test_dcel_connectors.py`, `test_di.py`, `test_di_enterprise_query.py`, `test_graph_config_injection.py`, `test_persisted_rule_lifecycle.py`, `test_source_trust.py`, `test_trust_endpoint.py` | memory_store |
| `copilot-sdk/apps/purchasing/backend` | `cli.py` | factory |
| `copilot-sdk/apps/purchasing/backend/app` | `graph_status.py`, `main.py` | factory |
| `copilot-sdk/apps/purchasing/backend/tests` | `conftest_helpers.py` | factory |
| same | `test_purchasing_backend.py` | factory, graph |
| same | `test_bundle_wiring.py`, `test_cohort_status.py`, `test_iks_trust.py`, `test_learning_beats.py`, `test_purchasing_control.py`, `test_purchasing_graph_status.py`, `test_ss07_evidence_degraded.py` | graph |
| same | `test_frozen_twin_curves.py`, `test_investigation_integration.py`, `test_match_queue.py`, `test_purchasing_factors.py`, `test_verify.py` | memory_store |
| `copilot-sdk/apps/regime_experiment` | `experiment.py` | factory |
| `copilot-sdk/apps/s2p_differentiation` | `engine.py` | memory_store |
| `copilot-sdk/apps/s2p_differentiation/tests` | `test_engine_graph_sharing.py` | memory_store, namespace |
| `copilot-sdk/apps/trading/backend/app` | `cli_sdk.py`, `graph_status.py` | factory |
| same | `main.py` | factory, memory_store |
| `copilot-sdk/apps/trading/backend/tests` | `conftest_helpers.py`, `test_regime_replay.py` | factory |
| same | `test_trading_backend.py` | factory, graph |
| same | `test_bundle_wiring.py`, `test_claim_gate.py`, `test_execution_analysis.py`, `test_live_rejection_provenance.py`, `test_regime_classifier.py`, `test_regime_conditioned_learning.py`, `test_rejection_summary.py` | graph |
| same | `test_trading_graph_status.py` | graph, legacy_signal_filter |
| same | `test_investigation_integration.py`, `test_output_equivalence.py`, `test_pre_scorer.py`, `test_promotion_engine.py`, `test_trading_evolver.py`, `test_trading_registry.py`, `test_trust_analysis.py` | memory_store |
| `copilot-sdk/copilot_sdk/backend` | `graph_access.py` | age_graph_store |
| same | `self_computation_router.py` | graph |
| `copilot-sdk/copilot_sdk/demo` | `preseed.py` | memory_store |
| `copilot-sdk/copilot_sdk/graph` | `production.py` | age_client, age_graph_store, age_sdk_adapter |
| `copilot-sdk/copilot_sdk/migrate` | `reconcile_archive.py`, `scratch_graph.py`, `sqlite_to_age.py`, `verify_state.py` | age_client |
| same | `__main__.py` | age_graph_store |
| `copilot-sdk/copilot_sdk/scoring` | `scorer.py` | memory_store, namespace |
| `copilot-sdk/copilot_sdk/testing` | `fixtures.py` | memory_store |
| `copilot-sdk/copilot_sdk/twin` | `service.py` | memory_store |
| `copilot-sdk/examples/build_your_own` | `engine.py` | factory |
| `copilot-sdk/examples/jm_reference` | `run.py` | factory |
| `copilot-sdk/experiments/jm_extracted` | `render_ci_failuremodes_v6.py` | memory_store |
| `copilot-sdk/experiments/vld` | `c1_c6_campaign_v1.py`, `vld_cons_pd_decision_features_v1.py`, `vld_conservation_characterization_v1.py`, `vld_conservation_lag_c5_v1.py`, `vld_conservation_perdecision_signals_v1.py`, `vld_decision_complexity_v1.py`, `vld_gate_calibration_f2_v1.py`, `vld_looped_depth_c7_v1.py`, `vld_rl_ctrl2c_constrained_v1.py`, `vld_rl_ctrl2c_redesign_v1.py`, `vld_rl_ctrl_enrichment_v1.py`, `vld_rl_ctrl_fork_v1.py` | memory_store |
| `copilot-sdk/integration/age_jm` | `test_phase_01_contracts.py` | age_graph_store |
| same | `conftest.py` | age_sdk_adapter |
| same | `test_phase_06_projections.py`, `test_phase_07_traversals.py`, `test_phase_10_cutover.py` | memory_store |
| `copilot-sdk/integrity` | `benchmark_fixture.py` | memory_store |
| `copilot-sdk/scripts` | `jm_stress_test.py`, `jm_v27_live_validation.py` | age_client |
| same | `phase6_claim_proof.py` | age_graph_store |
| same | `c9_live_age_smoke.py`, `phase3_dual_parity_v2.py`, `phase3_read_diff_v4.py`, `phase3_read_diff_v5.py`, `phase_read_diff.py`, `trigger_warm_start.py` | age_sdk_adapter |
| same | `phase3_read_diff_v2.py` | age_sdk_adapter, factory |
| same | `backfill_snapshot_after.py`, `demo_cross_copilot_finding.py`, `phase3_dual_write_smoke.py`, `pilot_report.py`, `preseed_demo_fixtures.py`, `seed_all_decisions.py`, `transfer_demo.py` | factory |
| same | `budget_accuracy_frontier.py`, `d1_recursion_trace_v1.py`, `evolve_demo.py`, `k_learning_conservation_interaction.py`, `k_learning_curve_cross_copilot.py`, `k_learning_curve_experiment.py`, `k_learning_curve_extended.py`, `k_learning_distribution_sensitivity.py`, `routing_variant_risk_sensitive.py` | memory_store |
| same | `multitenant_demo.py` | memory_store, tenant_store |
| `copilot-sdk/tests` | `age_probe.py`, `test_reconcile_archive.py` | age_client |
| same | `test_jm_conformance.py`, `test_store_parity.py` | age_graph_store, graph |
| same | `test_jm_rl_cross_copilot.py` | age_graph_store, memory_store |
| same | `test_age_unification_invariants.py`, `test_gate_preseed_initialization.py`, `test_graph_factory.py`, `test_historical_checkpoint_import.py`, `test_preseed_gap_supersession.py`, `test_rule38_factory_compliance.py`, `test_session_regression.py` | factory |
| same | `test_age_protocol_enforcement.py` | factory, graph |
| same | `test_archetype_generator.py`, `test_bitemporal_scorer.py`, `test_bounded_projection_types.py`, `test_bug_fixes.py`, `test_c_regime_day1.py`, `test_centroid_ablation.py`, `test_conservation_formula.py`, `test_consolidation.py`, `test_demo_truth_guards.py`, `test_di_enrichment.py`, `test_frozen_twin.py`, `test_gate_enforced_scorer.py`, `test_graph_entity_links.py`, `test_graph_platform_reset.py`, `test_graphstore_consolidation.py`, `test_iks_service.py`, `test_judgment_conflict.py`, `test_l5_centroid_storage.py`, `test_l5_conservation_storage.py`, `test_l5_dk_weight_storage.py`, `test_l5_dk_welford_storage.py`, `test_learn_context.py`, `test_learning_checkpoint_history.py`, `test_measured_transfer.py`, `test_outbox.py`, `test_outcome_protocol.py`, `test_platform_router.py`, `test_point_in_time_replay.py`, `test_promotion_engine.py`, `test_promotion_record_format.py`, `test_qualification.py`, `test_regime_reinit.py`, `test_response_models.py`, `test_rl_evolution_matrix.py`, `test_s2p_differentiation_namespace.py`, `test_shadow_scorer.py`, `test_side_store_removal.py`, `test_situation_analyzer.py`, `test_snapshot_after.py`, `test_snapshot_after_endpoint.py`, `test_transfer_governed_source.py`, `test_transfer_publication_order.py`, `test_transfer_router.py` | graph |
| same | `test_l5_protocol_extension.py` | graph, memory_store |
| same | `test_timestamp_consumers.py` | legacy_signal_filter, memory_store |
| same | `evolution_contract_helpers.py`, `graph_store_test_helpers.py`, `test_ae_framework.py`, `test_archetype_router.py`, `test_backend_conformance.py`, `test_category_mappings.py`, `test_convergence_metrics.py`, `test_cross_copilot_integration.py`, `test_cross_copilot_transfer.py`, `test_cross_signal_router.py`, `test_demo_shared_graph.py`, `test_entity_enrichment.py`, `test_evolution_telemetry.py`, `test_five_domain_completeness.py`, `test_frozen_twin_curves.py`, `test_gate_production_policy.py`, `test_generate_decision_id.py`, `test_global_queries.py`, `test_graph_signals.py`, `test_graph_state_protocol.py`, `test_investigation.py`, `test_jm_v27_validation.py`, `test_learn_locked_response.py`, `test_nl_query_extended.py`, `test_phase6_batch_b.py`, `test_preseed_contracts.py`, `test_quality_axis.py`, `test_read_diff_runner.py`, `test_rl_framework.py`, `test_scorer_construction.py`, `test_signal_store_isolation.py`, `test_soc_preset.py`, `test_ss03_observability.py`, `test_switching_cost_router.py`, `test_transfer.py`, `test_transfer_pattern.py`, `test_weekly_report.py`, `vld_validation_report.py` | memory_store |
| same | `test_tenant_isolation.py` | memory_store, tenant_store |
| `copilot-sdk/tests/backend` | `test_coalesced_reads.py`, `test_scorer_proxy.py` | factory |
| same | `test_diagnostics_models.py`, `test_evolution_router.py`, `test_graph_access_health.py`, `test_scoring_graph_outages.py`, `test_scoring_router.py`, `test_self_computation.py`, `test_self_computation_router.py`, `test_trust_traps_router.py` | graph |
| same | `test_l5_full_flow.py`, `test_self_computation_panels.py` | memory_store |
| `copilot-sdk/tests/demo` | `test_bundle.py` | factory, graph |
| `copilot-sdk/tests/evolution` | `test_evolution_store.py`, `test_graph_variant_store.py`, `test_ledger_domain.py`, `test_variant_replay_order.py`, `test_variant_status_sequence.py` | graph |
| same | `test_cross_loop_conservation.py`, `test_ledger.py`, `test_variant_event_order.py` | memory_store |
| `copilot-sdk/tests/graph` | `test_age_pool_stress.py`, `test_soc_age_projection_contract.py` | age_client |
| same | `test_age_p4a.py` | age_sdk_adapter |
| same | `test_graphstore_factory.py` | factory |
| same | `test_contract.py`, `test_contract_cross.py`, `test_graph_store_evolution.py`, `test_memory_store.py`, `test_protocol.py`, `test_protocol_v2_conformance.py` | graph |
| same | `test_decision_metadata.py` | graph, memory_store |
| same | `test_scoring_persistence.py` | graph, tenant_store |
| same | `test_correctness_conformance.py`, `test_domain_required_conformance.py`, `test_evolution_event_links.py`, `test_link_domain_conformance.py`, `test_no_amend_policy.py`, `test_verified_count_strict.py`, `test_write_outcome_extended.py` | memory_store |
| same | `test_namespace.py` | memory_store, namespace |
| `copilot-sdk/tests/integrity` | `test_counterfactual.py`, `test_innovation_claims.py`, `test_judgment_memory.py`, `test_product_truth.py` | memory_store |
| `copilot-sdk/tests/rl` | `test_rl_persistence.py`, `test_rl_wiring.py`, `test_shared_control_contract.py` | graph |
| `copilot-sdk/tests/scoring` | `conftest.py`, `test_archive_logging.py`, `test_checkpoint_legacy.py`, `test_conservation.py`, `test_fingerprint_dedup.py`, `test_j6_persistence.py`, `test_outbox_decision_evolution.py`, `test_persistence_outbox.py`, `test_scorer.py`, `test_scorer_governed.py`, `test_trust_traps.py` | graph |
| same | `test_cross_store_conformance.py`, `test_dk_runtime_learning.py`, `test_scorer_graph_bootstrap.py`, `test_startup_restore.py` | memory_store |
| `copilot-sdk/tests/scripts` | `test_seed_all_decisions.py` | memory_store |
| `copilot-sdk/tests/stress` | `conftest.py`, `helpers.py`, `test_archive_behavior.py`, `test_concurrent_scoring.py`, `test_data_consistency.py`, `test_multi_domain_isolation.py` | memory_store |
| `copilot-sdk/tests/transfer` | `test_registry.py` | graph |
| same | `test_scorer_warm_start.py` | memory_store |
| `s2p-copilot/backend/app` | `main.py`, `s2p_graph_status.py`, `s2p_shadow.py` | factory |
| `s2p-copilot/backend/app/migration` | `s2p_entity_migration.py` | age_client |
| `s2p-copilot/backend/app/routers` | `s2p_evidence.py` | age_graph_store |
| same | `s2p_preview.py` | memory_store |
| `s2p-copilot/backend/app/services` | `centroid_explorer.py`, `s2p_enrichment.py` | age_graph_store |
| `s2p-copilot/backend/demo` | `s2p_demo.py` | memory_store |
| `s2p-copilot/backend/scripts` | `verify_s2p_domain_isolation.py` | factory |
| `s2p-copilot/backend/tests` | `test_s2p_entity_migration.py` | age_client |
| same | `conftest.py` | age_client, age_graph_store, memory_store |
| same | `test_scaffold.py` | age_graph_store |
| same | `test_astra_s2p_b.py` | age_graph_store, memory_store |
| same | `test_s2p_retired_backend_guards.py` | factory |
| same | `test_s2p_graph.py`, `test_situation_graph_enrichment.py`, `test_situation_traversals.py` | graph |
| same | `test_audit.py`, `test_budget_persistence.py`, `test_s2p_audit_wiring.py` | legacy_signal_filter, memory_store |
| same | `ordered_evolution_store.py`, `test_centroid_explorer.py`, `test_centroid_import.py`, `test_compounding_ledger.py`, `test_domain_enforcement.py`, `test_evidence_receipt_wiring.py`, `test_extinction_contract.py`, `test_financial_router.py`, `test_graph_links.py`, `test_graphstore_consolidation.py`, `test_jm_rl_verification.py`, `test_l5_conservation_s2p_hook.py`, `test_l5_dk_s2p_hook.py`, `test_l5_full_flow_s2p.py`, `test_l5_startup_s2p.py`, `test_observation_wiring.py`, `test_proposal.py`, `test_response_materializer.py`, `test_s2p_active_age_phase_b.py`, `test_s2p_audit_export.py`, `test_s2p_auto_approve_gate.py`, `test_s2p_conservation_coverage.py`, `test_s2p_conservation_threshold.py`, `test_s2p_context_builder.py`, `test_s2p_enrichment.py`, `test_s2p_evolution_router.py`, `test_s2p_graph_reader.py`, `test_s2p_performance.py`, `test_s2p_score_endpoint.py`, `test_s2p_shadow_phase2.py`, `test_s2p_situation_pattern.py`, `test_s2p_timeout_regressions.py`, `test_shadow_retirement.py`, `test_supplier_intelligence.py` | memory_store |
| `s2p-copilot/scripts` | `seed_s2p_graph.py` | age_client |

**Required fixer prompts**

1. **FIX-REV-P2-NAMESPACE — SDK + platform; R1/R2**
   - Preserve opaque projection payloads through namespace reads and feeds.
   - Establish compatible, collision-safe physical-domain handling across both stores and migration.
   - Add memory/AGE composition tests covering journal/scoring/full payloads, cursor preservation, generation fences, feeds, tenant isolation, and namespace isolation.

2. **FIX-REV-P2-AGE-LIFECYCLE — platform + SDK factory tests; R3–R6**
   - Preserve retention decision IDs without legacy JSON/null coercion.
   - Distinguish missing activation from corrupt readiness.
   - Close partially initialized pools on failure.
   - Test actual bounded-import fallback and activation corruption.
   - Include live AGE archive/feed regressions and rerun the relevant suites.

R8 can be closed alongside the compiler work. R7/R9/R10 need explicit downstream verification/documentation tracking. **REV-P4 should not treat bounded core acceptance as unblocked until the P1 fixes are reviewed.**

The proposed session entry, **not appended because this review is read-only**, is:

```text
=== REV-P2 (REVIEW-BOUNDED-CORE) ===
date: 2026-10-16
model: astra+high
scope: P2a (memory_store) + P2b (AGE adapter) + P2c (wrappers/factory)
repos: copilot-sdk + ci-platform
verdict: FAIL
findings: 3 P1, 3 P2, 4 P3
P1: R1 opaque namespace payload rejection/rewriting;
    R2 AGE rejects namespace physical domains;
    R3 retention corrupts/drops valid string decision IDs
P2: R4 duplicate activation markers permit legacy fallback;
    R5 partial pool initialization leaks;
    R6 actual bounded-adapter ImportError fallback lacks regression coverage
P3: R7 original 20-check mapping unavailable;
    R8 mutable compiler manifests;
    R9 requested test-group counts total 40 versus 34 actual cases;
    R10 checklist terminology differs from accepted P1/activation contract
self-verify gap: Assessed documented assertions against code.
    Original CHECK-01 through CHECK-20 unavailable; two-check gap retained
    as informational downstream verification observation per user direction.
blast radius: 363 statically identified direct-import consumer files outside
    P2 change set across SDK/platform/S2P; no removed import/signature break
    detected; namespace, retention, readiness and pool behavior need fixes.
suite: Recorded full suites: SDK 4719 passed, 1 xfailed;
    platform 804 passed. Fresh direct-case checks: SDK 183 passed,
    platform compiler 19 passed. No fresh full pytest/live AGE suite run.
next: FIX-REV-P2-NAMESPACE and FIX-REV-P2-AGE-LIFECYCLE, then re-review.
    Bounded core acceptance remains blocked for REV-P4.
```
