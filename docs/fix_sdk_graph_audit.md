# FIX-SDK graph-store audit

Scope: all Python files under tests/, copilot_sdk/, and apps/. The full test-pattern superset was applied to all three trees. Supplemental scans covered Mock/MagicMock, hand-written Store/Graph classes, graph assignments, patches and monkeypatches.

## Category A — replaced normal graph data fixtures

13 store implementations in 13 files. All use InMemoryGraphStore public write/read methods; seeded subclasses only customize construction, never graph operations.

- `tests/test_gate_enforced_scorer.py`
- `tests/test_response_models.py`
- `tests/test_transfer_router.py`
- `tests/test_di_enrichment.py`
- `tests/test_demo_truth_guards.py`
- `tests/test_iks_service.py`
- `tests/backend/test_evolution_router.py`
- `apps/trading/backend/tests/test_trust_analysis.py`
- `apps/trading/backend/tests/test_regime_conditioned_learning.py`
- `apps/trading/backend/tests/test_execution_analysis.py`
- `apps/purchasing/backend/tests/test_iks_trust.py`
- `apps/purchasing/backend/tests/test_ss07_evidence_degraded.py`
- `apps/dataops/backend/tests/test_trust_perturbation.py`

## Category B — production mock/fallback removal

0. No production mock GraphStore fallback was found. DataOps explicitly configured offline topology fixtures are not an implicit production fallback. Trading _StaticDecisionStore adapts an actual materialized decision snapshot to a reader; it does not invent graph data or catch graph failures. ScenarioGraphStore classes belong to offline evaluation scripts, not app runtime.

## Exact requested-pattern hits

48 hits: 12 category C graph-test sites and 36 false positives. False positives are kept but are not counted as graph mocks.

| Location | Matched source | Classification / reason |
|---|---|---|
| `tests/backend/test_graph_access_health.py:63` | `with patch("ci_platform.graph.age_graph_store.AGEClient", autospec=True):` | C: AGE-specific adapter/health contract; memory backend cannot exercise AGE classification. |
| `tests/scoring/test_checkpoint_legacy.py:35` | `return CompoundingScorer(mock_preset, engine, graph_store=store, profile="test")` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_j6_persistence.py:44` | `return CompoundingScorer(mock_preset, engine, graph_store=store, profile="test")` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_outbox_decision_evolution.py:74` | `return CompoundingScorer(mock_preset, engine, graph_store=store, profile="test")` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_persistence_outbox.py:491` | `scorer = CompoundingScorer(mock_preset, engine, graph_store=store, profile="test")` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:156` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:170` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:218` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:233` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:249` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:272` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:503` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:539` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:546` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:560` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:588` | `monkeypatch.setattr(scorer.graph_store, "count_decisions", lambda _domain: 801)` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `tests/scoring/test_scorer.py:593` | `monkeypatch.setattr(scorer.graph_store, "archive_old_decisions", fail_archive)` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `tests/scoring/test_scorer.py:600` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:608` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:615` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:623` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:630` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:635` | `monkeypatch.setattr(graph_store, "count_verified", fail_count_verified)` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `tests/scoring/test_scorer.py:645` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:650` | `monkeypatch.setattr(graph_store, "write_decision", fail_write)` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `tests/scoring/test_scorer.py:657` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:689` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:698` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:752` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:1002` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:1015` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `tests/scoring/test_scorer.py:1052` | `scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)` | False positive: mocked preset, actual InMemoryGraphStore/SQLiteGraphStore. |
| `copilot_sdk/backend/health_builder.py:76` | `connected = True` | False positive: connected becomes true only after a successful real count_decisions probe. |
| `apps/dataops/backend/app/graph_queries.py:120` | `self._graph_connected = True` | False positive: real AGE client attachment/construction; configured AGE errors surface, no mock fallback. |
| `apps/dataops/backend/app/graph_queries.py:126` | `self._graph_connected = True` | False positive: real AGE client attachment/construction; configured AGE errors surface, no mock fallback. |
| `apps/dataops/backend/tests/test_graph_access_outages.py:26` | `with patch.object(app.state.graph_store, method, side_effect=OperationalError("AGE lost connection")):` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `apps/dataops/backend/tests/test_graph_access_outages.py:35` | `with patch.object(cast(FastAPI, client.app).state, "graph_store", None):` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `apps/dataops/backend/tests/test_graph_access_outages.py:42` | `with patch.object(cast(FastAPI, client.app).state.graph_store, "get_all_decisions", side_effect=ProgrammingError("bad SQL")):` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `apps/purchasing/backend/tests/test_health_outage_contract.py:22` | `with patch.object(app.state.graph_store, "count_decisions", side_effect=OperationalError("lost")):` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `apps/trading/backend/tests/test_cli_complete.py:109` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_cli_complete.py:401` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_cli_complete.py:434` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_cli_complete.py:472` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_cli_complete.py:505` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_cli_complete.py:538` | `self.connected = True` | False positive: IBKR network client test double, not a graph store. |
| `apps/trading/backend/tests/test_health_route_contract.py:26` | `with patch.object(cast(FastAPI, client.app).state.graph_store, "count_decisions", side_effect=OperationalError("offline")):` | C: deliberate connection/programming/persistence error injection or threshold setup for that error path. |
| `apps/trading/backend/tests/test_trading_registry.py:242` | `monkeypatch.setattr(scorer.graph_store, "get_all_decisions", forbidden)` | C: forbidden-read sentinel verifies materialized registry does not issue extra graph reads. |
| `apps/trading/backend/tests/test_trading_registry.py:243` | `monkeypatch.setattr(scorer.graph_store, "get_verified_decisions", forbidden)` | C: forbidden-read sentinel verifies materialized registry does not issue extra graph reads. |

## Supplemental legitimate doubles retained

- tests/test_situation_analyzer.py: read/write spy proves analysis performs exactly one read and no writes.
- tests/test_read_diff_runner.py: intentionally inconsistent primary/shadow results exercise mismatch and count-drift detection.
- tests/test_entity_enrichment.py, tests/test_graph_entity_links.py, tests/test_graphstore_consolidation.py, tests/test_l5_protocol_extension.py: minimal/default protocol and AGE-adapter capability contracts.
- tests/graph/test_graphstore_factory.py, tests/scripts/test_c9_live_age_smoke.py, apps/dataops/backend/tests/test_graph_queries.py: AGE factory, raw Cypher/readback, and topology client boundaries unsupported by memory stores.
- tests/scoring/test_dk_persistence.py: write-argument/deep-copy spy and failure injection for the learning-store protocol.
- tests/scoring/test_persistence_outbox.py, tests/scoring/test_startup_restore.py, tests/rl/test_rl_persistence.py: retry/order, missing capability, malformed state, and failure-path doubles.
- tests/backend/test_conservation_router.py, tests/test_conservation_utils.py: deliberately independent count-method answers/forbidden-read sentinels test legacy duck-typing and conservation formula semantics.
- tests/evolution/test_protocol.py, tests/evolution/test_ledger_domain.py: minimal runtime protocol and keyword-only signature contracts.
- tests/test_response_materializer.py and per-app test_materializer_invalidation.py: controlled mutation, read-count and concurrency sentinels test invalidation behavior.
- Per-app evidence/investigation provider tests: capability-specific get_vld_evidence, invalid numeric values, entity attachment arguments and call counts.
- Purchasing test_auto_order.py: alternate legacy row representations, including top-level provenance and status values; these exercise compatibility filtering rather than graph persistence.
- Broken/Failing/Unavailable stores and patched methods elsewhere remain deliberate outage, programming-error, missing-capability, or recovery fixtures. Real-store spies/subclasses are retained.

Evidence: `.codex_tmp/fix_sdk_extended_scan.txt` records supplemental class/patch scan hits. Exact requested-pattern matches are exhaustively listed above.
