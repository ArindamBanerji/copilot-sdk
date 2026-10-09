# DSTORE migration review and fix

## SUMMARY

- Task changes: **87 files**, including new files; **0 files deleted**. Counts compare the working tree captured at task start, not HEAD (which already had extensive user changes).
- Source/rule lines removed: **400**; added: **561**, excluding this generated report and appended session entry. No legacy backend file was deleted.
- Before, latest recorded full suite: **3971 passed / 1 failed / 260 skipped**, AGE-RUNTIME-DIAGNOSTIC-2 (2026-10-02T19:59:41-07:00). The preceding AGE-RUNTIME-FIX was 3972/0/260. A fresh baseline was started but interrupted after collection/initial tests before source edits; it is not reported as a completed baseline.
- After full suite: **3981 passed / 0 failed / 260 skipped / 3 expected failures**. Command: `python -m pytest tests/ -q --timeout=120`, with JUnit output added. `GRAPH_DSN` unset, `AGE_TEST_DSN=postgresql://localhost:59999/nonexistent`, matching the recorded outage baseline. No live AGE validation is claimed.
- Per-file mypy: **84 files checked, 0 failures**; see `.codex_tmp/dstore_migrate/mypy.json`. App files are checked with their own backend directory in MYPYPATH to resolve their isolated `app` package. The requested command/config is used for every changed Python file. Existing Any-return annotations in touched files were made explicit; no error suppressions added.
- Additional checks: 152 focused scoring/investigation/state tests; 12 RL wiring tests; Trading and Purchasing investigation integration each 8 passed; DataOps governance HTTP 24 passed. B2/delayed-entrant snapshot, clone isolation and projection-count smoke checks passed (`experiment_smoke.log`).
- First completed post-change suite: 3980 passed / 1 failed / 260 skipped / 3 xfailed (553.34s). The remaining legacy positional db_path placeholder in tests/rl/test_rl_wiring.py was removed and graph identity asserted. The final full rerun is the After result above; the first run is preserved in after_first.log/xml.
- Baseline inventory: 17 files with DecisionStore text; 108 files with SQLiteGraphStore/sqlite_store text, including 83 test files. This is substantially larger than the design estimate.
- Deferred table contains **105 file-level items**, grouped into required AGE protocol rollout, legacy SQLite consumers/deletion, durable outbox, and existing-data import. Next: **DSTORE-MIGRATE-2**.
- Unexpected: legacy SDK storage.py is already absent; DataOps governance is app-local; AGEGraphStore is in age_graph_store.py; GraphStore required-member additions would change runtime write dispatch; persistence_outbox.py is another scoring SQL dependency.
- Additional `dataops_governance`: 24 passed, 98 warnings in 10.35s
- Additional `trading_investigation`: 8 passed, 24 warnings in 4.73s
- Additional `purchasing_investigation`: 8 passed, 24 warnings in 10.50s

## CHANGES MADE

| File | What changed | Lines affected (current; additions/removals) |
| --- | --- | --- |
| AGENTS.md | Persist standing rule: no new legacy persistence dependencies | 1-10; +10/-0 |
| apps/dataops/backend/app/dataops_governance.py | Replace local SQL holdouts/outcomes with graph records; preserve verification and source filtering | 6-6, 9-9, 12-12, 18-20, 26-26, 28-30, 36-36, 68-74, 78-86, 94-94, 99-100, 106-108, 110-110, 120-120, 196-201; +39/-46 |
| apps/dataops/backend/app/main.py | Share selected graph with investigation K store; remove local K connection; update scorer call/governance wiring | 9-9, 122-123, 782-782, 783-783, 1060-1060; +4/-15 |
| apps/purchasing/backend/app/main.py | Share selected graph with investigation K store; remove local K connection; update scorer call/governance wiring | 9-9, 151-152, 979-979; +3/-13 |
| apps/purchasing/backend/app/routers/queue.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 223-223; +1/-1 |
| apps/purchasing/backend/cli.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 5-5, 67-67, 523-523; +3/-2 |
| apps/purchasing/backend/tests/conftest_helpers.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 22-22; +1/-1 |
| apps/purchasing/backend/tests/test_investigation_integration.py | Use graph-backed fixture/seeding and read-only state assertions | 3-3, 20-21, 31-31, 82-82, 91-91; +4/-8 |
| apps/purchasing/backend/tests/test_purchasing_config_migration.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 150-150; +1/-1 |
| apps/purchasing/backend/tests/test_trust_analysis.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 14-14; +1/-1 |
| apps/s2p_differentiation/engine.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 11-11, 95-95, 134-134, 182-182; +3/-3 |
| apps/trading/backend/app/cli_sdk.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 10-10, 117-117, 718-718, 741-741, 746-746; +5/-4 |
| apps/trading/backend/app/main.py | Share selected graph with investigation K store; remove local K connection; update scorer call/governance wiring | 9-9, 140-141, 616-616; +3/-13 |
| apps/trading/backend/app/services/trading_materialization.py | Rename nonpersistent static decision-row adapter to avoid misleading legacy name | 23-23, 69-69; +2/-2 |
| apps/trading/backend/tests/conftest_helpers.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 3-3, 36-36, 105-105, 115-115; +4/-3 |
| apps/trading/backend/tests/test_investigation_integration.py | Use graph-backed fixture/seeding and read-only state assertions | 3-3, 20-21, 31-31, 82-82, 91-91; +4/-8 |
| apps/trading/backend/tests/test_options_scored_factors.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 146-146, 161-161; +2/-2 |
| apps/trading/backend/tests/test_regime_analytics.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 14-14, 111-111; +2/-2 |
| apps/trading/backend/tests/test_trading_config_migration.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 131-131; +1/-1 |
| copilot_sdk/backend/scoring_router.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 171-171; +1/-1 |
| copilot_sdk/graph/__init__.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 10-10, 25-25; +2/-0 |
| copilot_sdk/graph/memory_store.py | Implement four scoring-state methods on dict-backed governance records; correct equal-time latest-centroid selection | 362-385, 1538-1538; +25/-1 |
| copilot_sdk/graph/protocol.py | Stage four scoring methods in runtime-checkable ScoringPersistenceStore | 13-36; +24/-0 |
| copilot_sdk/graph/scoring_persistence.py | Scoring persistence adapter/contracts: upsert, domains, tenants, copy isolation, errors | 1-64; +64/-0 |
| copilot_sdk/scoring/investigation.py | Replace raw K SQL with GraphStore persistence; preserve bounds, update counts and production rejection | 13-14, 466-466, 468-477, 481-489, 492-492, 494-495, 497-497, 519-520, 522-526, 528-528; +33/-43 |
| copilot_sdk/scoring/scorer.py | Remove from_preset db_path; memory for dev/test; load accepts graph/profile | 284-284, 309-309, 313-313, 2222-2223, 2225-2225; +4/-17 |
| experiments/jm_extracted/render_ci_failuremodes_v6.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 13-13, 95-95, 97-97, 107-107; +4/-4 |
| experiments/vld/c1_c6_campaign_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 30-30, 83-84, 107-107; +4/-3 |
| experiments/vld/vld_cons_pd_decision_features_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 4-4, 10-10, 49-49, 116-116; +2/-5 |
| experiments/vld/vld_conservation_characterization_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 10-10, 47-47, 81-81; +2/-6 |
| experiments/vld/vld_conservation_lag_c5_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 19-19, 23-23, 319-319, 344-344; +2/-5 |
| experiments/vld/vld_conservation_perdecision_signals_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 4-4, 11-11, 46-46, 104-104; +2/-5 |
| experiments/vld/vld_decision_complexity_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 33-33, 273-273, 305-305; +3/-2 |
| experiments/vld/vld_delayed_entrant_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 65-68, 125-125, 151-151, 186-187, 191-191, 316-316, 328-328; +11/-7 |
| experiments/vld/vld_gate_calibration_f2_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 15-15, 87-87, 120-120; +3/-2 |
| experiments/vld/vld_looped_depth_c7_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 30-30, 201-201, 260-260; +3/-2 |
| experiments/vld/vld_moat_b2_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 105-108, 177-177, 185-185, 199-199, 203-204, 209-209, 377-380; +14/-9 |
| experiments/vld/vld_rl_ctrl2c_constrained_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 18-18, 50-50; +2/-1 |
| experiments/vld/vld_rl_ctrl2c_redesign_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 23-23, 63-63, 139-139, 182-182, 225-225; +4/-10 |
| experiments/vld/vld_rl_ctrl_enrichment_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 11-11, 82-82; +2/-1 |
| experiments/vld/vld_rl_ctrl_fork_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 11-11, 19-19, 130-130, 375-375, 379-380; +4/-7 |
| scripts/budget_accuracy_frontier.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 9-9, 29-29, 210-210, 225-225, 236-236, 247-247; +6/-7 |
| scripts/d1_recursion_trace_v1.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 8-8, 42-43, 45-45, 161-161, 185-185; +6/-7 |
| scripts/demo_warm_start.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 64-64, 67-67; +0/-2 |
| scripts/discovery_demo.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 25-26; +2/-2 |
| scripts/evolve_demo.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 3-3, 28-28, 31-31, 34-34, 51-51; +4/-4 |
| scripts/k_learning_conservation_interaction.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 5-5, 11-11, 33-33, 118-119; +3/-6 |
| scripts/k_learning_curve_cross_copilot.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 11-12, 18-18, 96-96, 99-99, 339-339, 343-344, 431-431; +7/-9 |
| scripts/k_learning_curve_experiment.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 9-10, 16-16, 50-50, 54-54, 304-304, 307-308; +5/-8 |
| scripts/k_learning_curve_extended.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 10-11, 16-16, 53-53, 57-57, 302-302, 304-305; +6/-8 |
| scripts/k_learning_distribution_sensitivity.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 5-5, 10-10, 30-30, 138-138; +2/-5 |
| scripts/routing_variant_risk_sensitive.py | Replace disposable K SQLite shims/SQL snapshots/copies with memory GraphStore; update scorer calls and type annotations | 8-8, 14-14, 37-37, 183-183; +2/-5 |
| scripts/transfer_demo.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 29-29; +1/-1 |
| tests/backend/test_score_responsiveness.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 20-20; +1/-1 |
| tests/evolution/test_evolve_integration.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 14-14; +0/-1 |
| tests/evolution/test_integration.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 51-51; +1/-1 |
| tests/evolution/test_ledger_domain.py | Replace disposable SQLite fixtures with InMemoryGraphStore | 7-7, 64-64; +2/-2 |
| tests/evolution/test_variant_event_order.py | Replace disposable SQLite fixtures with InMemoryGraphStore | 6-6, 10-10; +2/-2 |
| tests/graph/test_decision_metadata.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 88-88; +0/-1 |
| tests/graph/test_protocol_v2_conformance.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 3-3, 219-219, 242-242, 286-286, 320-320, 427-427, 441-441, 3053-3053; +8/-7 |
| tests/graph/test_scoring_persistence.py | Scoring persistence adapter/contracts: upsert, domains, tenants, copy isolation, errors | 1-104; +104/-0 |
| tests/rl/test_rl_wiring.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 2-3, 32-32, 148-148, 153-153, 162-162; +5/-3 |
| tests/scoring/conftest.py | Shared scorer fixture uses InMemoryGraphStore; annotate numpy return for per-file mypy | 3-3, 10-10, 31-31, 38-38, 53-53; +5/-4 |
| tests/scoring/test_dataops_preset.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 1-1, 31-31, 80-80, 249-249; +4/-3 |
| tests/scoring/test_presets.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 53-53, 61-61; +2/-2 |
| tests/scoring/test_purchasing_preset.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 1-1, 55-55, 108-108, 313-313; +4/-3 |
| tests/scoring/test_scorer.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 23-23, 80-80, 89-89, 94-94, 97-97, 108-108, 125-125, 868-868; +4/-8 |
| tests/scoring/test_trading_preset.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 1-1, 53-53, 106-106, 254-254; +4/-3 |
| tests/test_age_unification_invariants.py | Five gates (two enforced, three strict expected failures with explicit deferrals) | 11-11, 38-80; +44/-0 |
| tests/test_archetype_router.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 87-87; +1/-1 |
| tests/test_bitemporal_scorer.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 193-193, 218-218; +0/-2 |
| tests/test_category_mappings.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 85-85, 132-132; +0/-2 |
| tests/test_conservation_formula.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 54-54; +0/-1 |
| tests/test_investigation.py | Replace raw K SQL with GraphStore persistence; preserve bounds, update counts and production rejection | 3-3, 47-47, 98-99, 690-691; +5/-14 |
| tests/test_measurement_state.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 15-15; +1/-1 |
| tests/test_plateau_preset_config.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 93-93, 124-124; +0/-2 |
| tests/test_platform_router.py | Replace disposable SQLite fixtures with InMemoryGraphStore | 10-10, 33-34; +3/-3 |
| tests/test_polarity.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 104-104; +1/-1 |
| tests/test_scorer_construction.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 17-17, 20-20, 23-23; +2/-3 |
| tests/test_switching_cost_router.py | Replace disposable SQLite fixtures with InMemoryGraphStore | 98-98, 103-103; +2/-2 |
| tests/test_trading_domain_config.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 209-209; +1/-1 |
| tests/test_warm_start_demo.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 26-26; +0/-1 |
| tests/test_weekly_report.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior; make existing Any returns explicit for requested per-file mypy | 3-3, 39-39, 105-105; +2/-2 |
| tests/transfer/test_scorer_warm_start.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 13-13; +0/-1 |
| tests/vld_validation_report.py | Remove scorer db_path argument; retain injected GraphStore/profile behavior | 252-252; +1/-1 |
| docs/dstore_migration_findings.md | Findings, exhaustive inventories, deferred work, verification | new file |
| docs/session_state.md | Append DSTORE-MIGRATE-REVIEW-FIX entry | append only |

## DELETIONS

| File | Reason |
| --- | --- |
| None | storage.py was absent at task start. SQLite backend and backend-specific tests are retained until their durable consumers are migrated. Disposable SQLiteDecisionStore classes were removed from experiment files, not entire files. |

## NOT FIXED

Line numbers below refer to the current working tree. This is an explicit incomplete migration, not a claim that the two-backend target is achieved. Three target gates are strict expected failures so removal work remains visible. All remaining Python backend references are also listed in Appendix E.

| File | Line | What needs fixing | Why deferred |
| --- | --- | --- | --- |
| apps/dataops/backend/tests/conftest.py | 11 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_dataops_backend.py | 228 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 19 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 438 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 11 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest_helpers.py | 7 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 316 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 421 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/regime_experiment/experiment.py | 22 | Migrate/remove remaining SQLite backend reference(s) | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/s2p_differentiation/engine.py | 20 | Migrate/remove remaining SQLite backend reference(s) | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/trading/backend/tests/conftest_helpers.py | 10 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_bundle_wiring.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_regime_replay.py | 9 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 433 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 17 | Migrate/remove remaining SQLite backend reference(s) | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| copilot_sdk/backend/health_builder.py | 12 | Migrate/remove remaining SQLite backend reference(s) | Health must identify the still-supported legacy backend truthfully until removal. |
| copilot_sdk/demo/bundle.py | 14 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/graph/__init__.py | 12 | Migrate/remove remaining SQLite backend reference(s) | Public export retained while existing durable tools still import it. |
| copilot_sdk/graph/dual_write_store.py | 19 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| copilot_sdk/graph/factory.py | 15 | Migrate/remove remaining SQLite backend reference(s) | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/sqlite_store.py | 393 | Migrate/remove remaining SQLite backend reference(s) | Backend still required by durable consumers; deleting it now breaks imports and recovery tools. |
| copilot_sdk/migrate/__main__.py | 91 | Migrate/remove remaining SQLite backend reference(s) | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 20 | Migrate/remove remaining SQLite backend reference(s) | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| examples/build_your_own/engine.py | 3 | Migrate/remove remaining SQLite backend reference(s) | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| integrity/architecture_scan.py | 78 | Migrate/remove remaining SQLite backend reference(s) | Existing backend selection/compatibility consumer retained for coordinated durable SQLite cutover. |
| scripts/phase3_dual_parity_v2.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 46 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 13 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v2.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v4.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v5.py | 5 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 6 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_read_diff.py | 5 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 18 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/sqlite_copilot_audit.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/backend/test_coalesced_reads.py | 15 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_graph_access_health.py | 13 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scorer_proxy.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scoring_router.py | 21 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/demo/test_bundle.py | 5 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/evolution/test_evolution_store.py | 4 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_ledger_domain.py | 63 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_selection_snapshot.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 25 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_correctness_conformance.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_decision_metadata.py | 3 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_domain_required_conformance.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_evolution_event_links.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_no_amend_policy.py | 14 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol_v2_conformance.py | 16 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 5 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 13 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_write_outcome_extended.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_scorer_governed.py | 14 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_storage.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_archive_reader.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_cross_copilot_transfer.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_dual_write_store.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_entity_enrichment.py | 19 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_factory_dual_write.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_five_domain_completeness.py | 14 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_gate_preseed_initialization.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_generate_decision_id.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_global_queries.py | 6 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graph_entity_links.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_production_boundary.py | 16 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graphstore_consolidation.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_historical_checkpoint_import.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_conformance.py | 13 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_jm_rl_cross_copilot.py | 111 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 15 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_l5_centroid_storage.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 8 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_legacy_signal_filter.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_outbox_sqlite.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_preseed_gap_supersession.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_quality_axis.py | 10 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_reconcile_archive.py | 14 | Migrate/remove remaining SQLite backend reference(s) | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_rule38_factory_compliance.py | 11 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_session_regression.py | 63 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_situation_analyzer.py | 24 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_store_parity.py | 13 | Migrate/remove remaining SQLite backend reference(s) | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_transfer_pattern.py | 9 | Migrate/remove remaining SQLite backend reference(s) | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_worker_process_safety.py | 12 | Migrate/remove remaining SQLite backend reference(s) | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/vld_validation_report.py | 7 | Migrate/remove remaining SQLite backend reference(s) | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/graph/protocol.py | 16 | Promote staged extension into required GraphStore members | Requires coordinated external AGE implementation; runtime ProtocolV2GraphStore dispatch would otherwise reject AGE. |
| ../ci-platform/ci_platform/graph/age_sdk_adapter.py | 11 | Implement/delegate four native scoring methods | Explicit user instruction forbids changing external AGE implementation; SDK governance bridge is used meanwhile. |
| copilot_sdk/scoring/persistence_outbox.py | 128 | Replace durable local SQL failure queue | Queue is used when graph persistence is unavailable; writing it to that same unavailable graph or memory loses recovery guarantees. |
| apps/dataops/backend/app/dataops_governance.py | 30 | Import historical dataops_holdout/outcome data before deployment | Existing local databases are untouched; migration needs explicit source selection, idempotency and reconciliation. |
| copilot_sdk/scoring/investigation.py | 489 | Import historical k_utility tables before deployment | New protocol state uses namespaced governance records. This code change does not rewrite existing production databases. |

## DESIGN VERIFICATION

| Claim | Status | Evidence / amendment |
| --- | --- | --- |
| DecisionStore in scoring/storage.py is importable; owns decisions/centroids/archive | AMENDED | File absent before edits; no SDK DecisionStore import exists. Historical class contents/schema cannot be verified from a nonexistent current file. Seven same-named experiment shims are unrelated disposable connections. |
| SQLiteGraphStore exists, about 167KB | CONFIRMED | copilot_sdk/graph/sqlite_store.py:393; 167,948 bytes at review. Retained pending durable cutover. |
| InMemoryGraphStore stays | CONFIRMED | copilot_sdk/graph/memory_store.py:327; dictionary-backed, deep-copy isolation; now default for development as well as test. |
| AGEGraphStore in ci_platform/graph/age_client.py | AMENDED | Implementation is ../ci-platform/ci_platform/graph/age_graph_store.py:94. age_client.py provides AGEClient; SDK uses age_sdk_adapter.py:11. None of these files changed. |
| KUtilityStore raw decision_store.conn, table and production guard | CONFIRMED | Baseline investigation.py:462-537. Reads conn/_conn, creates table, selects category rows, upserts weight/count; explicit production profile rejected SQLite connections. Replaced with GraphStore methods via scoring extension bridge. |
| DataOpsGovernance in SDK scoring; production guard rejects SQLite | AMENDED | Actual apps/dataops/backend/app/dataops_governance.py:25-48. Guard checked evolution-event callables, not backend identity; SQLiteGraphStore exposes these and could pass. It still opened SQLite unconditionally. Now checks AGE primary for production and uses graph holdout/outcome records. |
| from_preset db_path creates SQLite for dev | CONFIRMED | Baseline scorer.py:284,317-326; parameter/branch removed and callers updated. load() now accepts graph_store/profile. App/CLI db_path and factory parameters are distinct retained APIs. |
| c1_c6 campaign references SQLiteDecisionStore | CONFIRMED | Baseline experiments/vld/c1_c6_campaign_v1.py:82-83; migrated along with other disposable shims, snapshots, clone/projection operations and connection cleanup. |
| Approximately 10-15 affected test files | AMENDED | 83 baseline test files reference SQLiteGraphStore/sqlite_store; detailed inventory below. |
| _S2PGraphStore, DemoGraphStore, AGEGraphStoreAdapter might inherit SQLite | AMENDED | No SQLiteGraphStore subclass exists in this repo. _S2PGraphStore absent. scripts/evolve_demo.py:19 uses InMemoryGraphStore. External AGEGraphStoreAdapter wraps AGEGraphStore, with no SQLite inheritance. Consolidation plan describes historical state. |
| save_decision -> write_decision; save_outcome -> write_outcome | CONFIRMED | GraphStore declares write_decision/write_outcome; scorer already uses injected graph persistence and imports no legacy DecisionStore. |
| save_centroids -> write_outcome_and_update_centroid | AMENDED | GraphStore itself declares save_centroids; protocol-v2 adds governed checkpoint operations. Proposed method name is not a required GraphStore member. |
| load_latest_centroids -> read_centroids | AMENDED | GraphStore declares load_latest_centroids, not read_centroids. Current scorer calls it directly. |
| get_decision/get_verified_decisions/get_all_decisions/count_verified/count_correct equivalents | CONFIRMED | Existing GraphStore declarations cover these methods and enforce domain arguments. |
| count_categories_with_n is on GraphStore | AMENDED | It is on ProtocolV2GraphStore (subprotocol), not the base GraphStore contract. |
| get_centroid_checkpoints needs review | CONFIRMED | Already on GraphStore, with include_v2/filters; memory fixture exposed equal-timestamp latest-selection bug, corrected without deleting coverage. |
| Phase A required protocol additions are nonbreaking | AMENDED | Runtime-checkable GraphStore is inherited by ProtocolV2GraphStore; scorer.py uses isinstance for governed persistence. Four required methods cannot be added safely without prohibited external AGE changes. Staged ScoringPersistenceStore plus governance bridge preserves dispatch. |
| Implement AGE methods in this pass | AMENDED | Step 9 explicitly prohibits it; no ci-platform edits. The SDK bridge writes existing domain-scoped governance records and propagates failures, with no local fallback. |
| Phase B all consumers can use memory | AMENDED | Scorer/dev and disposable K/test fixtures migrated. Persistent factory/CLI/archive/restart consumers need AGE or reviewed migration tooling; replacing them with memory would lose state. |
| Phase C delete storage.py/sqlite_store.py and direct tests | AMENDED | storage.py already gone; SQLite deletion/direct-test deletion deferred as a coordinated step. Tests mixing protocol and schema/recovery behavior were preserved. |
| Phase D five architectural gates/full tests/mypy | CONFIRMED | All five added; two enforce current state, three strict xfails identify unresolved target state. Full test and per-file type results are reported, without treating xfails as completed migration. |
| Only two backends remain after this pass | AMENDED | Two backends are the standing target. SQLite and dual-write factory paths remain explicitly documented; this pass does not claim elimination. |

## NEW ARCHITECTURAL GATES

1. `test_no_decision_store_class_exists` — enforced.
2. `test_no_sqlite_graphstore_exists` — strict xfail, durable migration blockers.
3. `test_no_decision_store_import_anywhere` — enforced, AST scanning copilot_sdk/ and apps/.
4. `test_no_sqlite_graphstore_import_anywhere` — strict xfail, remaining imports.
5. `test_no_raw_sqlite3_in_scoring` — strict xfail, durable failure outbox.

## RISKS AND SURPRISES

- No data cutover is performed. Existing K SQLite files and dataops_holdout/outcome databases remain untouched and are not automatically read by the new consumers. Import/reconcile them before deploying against historical production data.
- K state was cumulative by category/dimension, not individual investigation episode. The new episode_id slot uses category for this consumer; metadata records last_episode_id and n_updates. Bounds remain 0.1–3.0, initial weight 0.5; repeated dimensions increment counts repeatedly.
- Holdout saves upsert by domain/decision; source_id maps to holdout_group. Re-registration preserves verdict, tier, verified_at and outcome_receipt_id. It now returns the row actually registered rather than the first row in a sorted source group.
- The bridge namespaces record keys including tenant identity, preserves deep-copy boundaries, and filters before limiting. It uses existing save_governance/list_governance and scans domain governance state; native indexed AGE methods are the follow-up scalability target. It does not introduce cross-process atomic increment/transaction guarantees. External age_graph_store.py:145 currently saves generic state using DELETE followed by CREATE in separate queries: a failure between them can remove the prior record. Native transactional upserts and concurrent update-count semantics require follow-up before relying on multi-writer guarantees.
- Local SQLite outbox is intentionally independent of the failing graph backend. A replacement requires a separately durable queue design, not merely the four new methods.
- Runtime guards now validate an AGE primary for production K/governance. App K stores share their already validated selected graph. Standalone K callers retain the prior explicit-profile guard convention.
- Full experiment campaigns, legacy database imports, and live AGE integration were not executed. Type checks and unit/integration behavior are not substitutes for scientific campaign reruns or production data reconciliation.
- Existing changed files were preserved. The task snapshot and task-only diff provide attribution; no reset, commit, or branch switch was performed.

## STORAGE REVIEW

`copilot_sdk/scoring/storage.py` does not exist in the starting working tree. Thus there are no current classes, functions, constants or aliases in that file to preserve, and no legacy SDK DecisionStore import to migrate. The same-name experiment classes contained only __init__ opening an in-memory SQLite connection; they were removed and consumers now construct InMemoryGraphStore.

### K utility operations and schema

Baseline schema: category TEXT NOT NULL, dimension INTEGER NOT NULL, weight REAL DEFAULT 0.5, n_updates INTEGER DEFAULT 0, PRIMARY KEY(category,dimension). Constructor CREATE/commit removed. SELECT by category becomes get_k_utilities(domain, category, limit=d). UPSERT becomes save_k_utility with weight in utility and accumulated count in metadata. Experiment SQL readers/snapshots/copies/projectors were ported; tests/vld_validation_report.py still inspects historical tables read-only and is listed as deferred.

### DataOps holdout operations and schema

Baseline schema: decision_id TEXT PRIMARY KEY; source_id, decision_class, evidence_tier TEXT NOT NULL; factor_vector, score_payload, verdict TEXT JSON; verified_at REAL; outcome_receipt_id TEXT. CREATE/ALTER/commit removed. Source-filtered ordered SELECT becomes get_holdout_decisions plus sorting by verified_at/decision_id. INSERT/ON CONFLICT and UPDATE verification become save_holdout_decision while preserving prior verification metadata. Provenance and abstention read the same graph records. No other direct dataops_holdout SQL consumer was found outside this module; HTTP consumers keep their shapes.

## INVENTORY SCOPE

The following appendices record every matching line in tracked and nonignored untracked repository Python sources captured before edits (git ls-files -co --exclude-standard). Build/vendor/cache/.git and agent scratch artifacts are excluded. Duplicate search patterns are merged by line. Baseline line numbers explain the original migration surface; Appendix E/deferred table use current lines. Raw SQL outside scoring is classified separately rather than assuming all SQLite is scoring persistence.

### Appendix A — DecisionStore references before edits

| File | Line | Usage | Migration action |
| --- | --- | --- | --- |
| apps/trading/backend/app/services/trading_materialization.py | 23 | class definition (local shim, not legacy SDK) | Rename static row adapter (not persistence) |
| apps/trading/backend/app/services/trading_materialization.py | 69 | instantiation/reference | Rename static row adapter (not persistence) |
| experiments/vld/c1_c6_campaign_v1.py | 82 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/c1_c6_campaign_v1.py | 83 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_cons_pd_decision_features_v1.py | 49 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_cons_pd_decision_features_v1.py | 119 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_conservation_lag_c5_v1.py | 319 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_conservation_lag_c5_v1.py | 347 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_conservation_perdecision_signals_v1.py | 46 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_conservation_perdecision_signals_v1.py | 107 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_decision_complexity_v1.py | 272 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_delayed_entrant_v1.py | 148 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_gate_calibration_f2_v1.py | 86 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_looped_depth_c7_v1.py | 200 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_moat_b2_v1.py | 173 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_rl_ctrl2c_constrained_v1.py | 49 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_rl_ctrl_enrichment_v1.py | 81 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 130 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 382 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 383 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/budget_accuracy_frontier.py | 28 | import | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/budget_accuracy_frontier.py | 209 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_cross_copilot.py | 95 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_cross_copilot.py | 345 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_cross_copilot.py | 346 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_experiment.py | 49 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_experiment.py | 310 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_experiment.py | 311 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_extended.py | 52 | class definition (local shim, not legacy SDK) | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_extended.py | 306 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |
| scripts/k_learning_curve_extended.py | 307 | instantiation/reference | Remove disposable SQL shim/use InMemoryGraphStore |

### Appendix B — SQLiteGraphStore references before edits

| File | Line | Usage | Migration action |
| --- | --- | --- | --- |
| apps/dataops/backend/tests/conftest.py | 11 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/conftest.py | 79 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/conftest.py | 94 | type annotation | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_dataops_backend.py | 228 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 231 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1529 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1531 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1539 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1541 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1549 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1551 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 19 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 160 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 170 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 438 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 440 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 11 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 98 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 104 | type annotation | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest_helpers.py | 7 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest_helpers.py | 21 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 316 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 319 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 805 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 808 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 827 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 830 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 978 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 984 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1007 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1009 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1017 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1019 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1027 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1029 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 421 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 423 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/regime_experiment/experiment.py | 22 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/regime_experiment/experiment.py | 120 | type annotation | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/regime_experiment/experiment.py | 121 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/s2p_differentiation/engine.py | 19 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/s2p_differentiation/engine.py | 178 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/trading/backend/tests/conftest_helpers.py | 9 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/conftest_helpers.py | 34 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/conftest_helpers.py | 113 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_regime_replay.py | 9 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_regime_replay.py | 13 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_regime_replay.py | 27 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 433 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 436 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 801 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 804 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 823 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 826 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 891 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 897 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 920 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 922 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 930 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 932 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 940 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 942 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 17 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 228 | test assertion/type check | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 507 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 509 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| copilot_sdk/backend/health_builder.py | 12 | import | Health must identify the still-supported legacy backend truthfully until removal. |
| copilot_sdk/backend/health_builder.py | 35 | test assertion/type check | Health must identify the still-supported legacy backend truthfully until removal. |
| copilot_sdk/demo/bundle.py | 14 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 156 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 159 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 165 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 166 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 168 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/graph/__init__.py | 11 | import | Public export retained while existing durable tools still import it. |
| copilot_sdk/graph/__init__.py | 25 | reference/string/comment | Public export retained while existing durable tools still import it. |
| copilot_sdk/graph/dual_write_store.py | 19 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| copilot_sdk/graph/dual_write_store.py | 61 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| copilot_sdk/graph/factory.py | 15 | import | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/factory.py | 191 | instantiation/reference | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/factory.py | 204 | instantiation/reference | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/sqlite_store.py | 393 | class definition (local shim, not legacy SDK) | Backend still required by durable consumers; deleting it now breaks imports and recovery tools. |
| copilot_sdk/graph/sqlite_store.py | 429 | reference/string/comment | Backend still required by durable consumers; deleting it now breaks imports and recovery tools. |
| copilot_sdk/migrate/__main__.py | 91 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 94 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 97 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 110 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 20 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 25 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 28 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 51 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 124 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/scoring/scorer.py | 317 | import | Migrated to memory/removed scorer SQLite branch |
| copilot_sdk/scoring/scorer.py | 325 | instantiation/reference | Migrated to memory/removed scorer SQLite branch |
| examples/build_your_own/engine.py | 3 | reference/string/comment | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/build_your_own/engine.py | 19 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/build_your_own/engine.py | 89 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 8 | reference/string/comment | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 24 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 70 | type annotation | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 89 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| integrity/architecture_scan.py | 78 | reference/string/comment | Existing backend selection/compatibility consumer retained for coordinated durable SQLite cutover. |
| scripts/phase3_dual_parity_v2.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_parity_v2.py | 27 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 46 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 49 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 102 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 13 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 52 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 102 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 10 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 49 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 96 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v2.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v2.py | 22 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v4.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v4.py | 22 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v5.py | 5 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v5.py | 23 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 6 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 13 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 23 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_read_diff.py | 5 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_read_diff.py | 12 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 18 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 30 | type annotation | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 32 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 72 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 88 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 89 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/sqlite_copilot_audit.py | 8 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 190 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 209 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 216 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 220 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/backend/test_coalesced_reads.py | 15 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 53 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 57 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 67 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_graph_access_health.py | 13 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_graph_access_health.py | 20 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scorer_proxy.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scorer_proxy.py | 37 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scoring_router.py | 21 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scoring_router.py | 320 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/demo/test_bundle.py | 5 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/demo/test_bundle.py | 85 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/demo/test_bundle.py | 184 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/evolution/test_evolution_store.py | 4 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_evolution_store.py | 35 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_ledger_domain.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_ledger_domain.py | 63 | reference/string/comment | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_ledger_domain.py | 64 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_selection_snapshot.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_selection_snapshot.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_selection_snapshot.py | 13 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 25 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 38 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 52 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 66 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 79 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 91 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 108 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 116 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 11 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_variant_event_order.py | 6 | import | Migrated to memory/removed scorer SQLite branch |
| tests/evolution/test_variant_event_order.py | 10 | instantiation/reference | Migrated to memory/removed scorer SQLite branch |
| tests/graph/test_correctness_conformance.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_correctness_conformance.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_decision_metadata.py | 3 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 48 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 61 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 72 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 78 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_domain_required_conformance.py | 8 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_domain_required_conformance.py | 15 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_evolution_event_links.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 11 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 20 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 63 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 68 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 89 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 104 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 123 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 11 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 23 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 33 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 46 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 227 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 16 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 43 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_no_amend_policy.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_no_amend_policy.py | 24 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 11 | reference/string/comment | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 21 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 173 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol_v2_conformance.py | 15 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 33 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 34 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 66 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 398 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 420 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 443 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 446 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 455 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 461 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 462 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 465 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 470 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 497 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 500 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 502 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 510 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 511 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 577 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 580 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 582 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 583 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 587 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 620 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 623 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 625 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 626 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 630 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 663 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 666 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 667 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 676 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 679 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 681 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 685 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 692 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 696 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 809 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 812 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 813 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 815 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 819 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 823 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 834 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 835 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 862 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 865 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 866 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 867 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 869 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 870 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 890 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 893 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 895 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 912 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 915 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 926 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 929 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 930 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 932 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 933 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 934 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 935 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 949 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 952 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 953 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 954 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 956 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 957 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 959 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 960 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 961 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 962 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 963 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1040 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1050 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1053 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1054 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1055 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1057 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1075 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1076 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1082 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1388 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1391 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1392 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1393 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1394 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1396 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1408 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1421 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1429 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1441 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1442 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1447 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1460 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1461 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1581 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1584 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1585 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1588 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1614 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1628 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1629 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1632 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1642 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1643 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1746 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1749 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1750 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1754 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1782 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1804 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1805 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1808 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1822 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1823 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1944 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1947 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1961 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1964 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1970 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1971 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1979 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1982 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1983 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1986 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2014 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2031 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2032 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2035 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2044 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2045 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2048 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2051 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2054 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2055 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2057 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2071 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2086 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2087 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2090 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2097 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2098 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2099 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2640 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2663 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2666 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2667 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2668 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2670 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2671 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2673 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2687 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2688 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2691 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2695 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2714 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2718 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2829 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2833 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2862 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2866 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2874 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2878 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2879 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2880 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2881 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2882 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2884 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2896 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2908 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2916 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2924 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2936 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2948 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2955 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2962 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2963 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2964 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2965 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2968 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2994 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2995 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3069 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3072 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3073 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3076 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3078 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3082 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3092 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3095 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3096 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3098 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3099 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3103 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3111 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3114 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3115 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3117 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3118 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3122 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3170 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3173 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3175 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3176 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3193 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3196 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3202 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3209 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3217 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3240 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3243 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3244 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3246 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3255 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3258 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3261 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3263 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3279 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3282 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3290 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3297 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3301 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3314 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3317 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3325 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3332 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3336 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3349 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3352 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3359 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3366 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3374 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3390 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3392 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3393 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3394 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3396 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3397 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3398 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 5 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 20 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 58 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 12 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 41 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 65 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 82 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 88 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 100 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 124 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 142 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 163 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 174 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 185 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 198 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 226 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 239 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 247 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 256 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 262 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 275 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 284 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 292 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 304 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 312 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 318 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 328 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 329 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 391 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 406 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 424 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 427 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 448 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 23 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 58 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 82 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_write_outcome_extended.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_write_outcome_extended.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/conftest.py | 9 | import | Migrated to memory/removed scorer SQLite branch |
| tests/scoring/conftest.py | 52 | instantiation/reference | Migrated to memory/removed scorer SQLite branch |
| tests/scoring/test_scorer.py | 23 | import | Migrated to memory/removed scorer SQLite branch |
| tests/scoring/test_scorer.py | 99 | test assertion/type check | Migrated to memory/removed scorer SQLite branch |
| tests/scoring/test_scorer_governed.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_scorer_governed.py | 83 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_storage.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 264 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 287 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 346 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 350 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 22 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 90 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 91 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 101 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 102 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 247 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_age_unification_invariants.py | 255 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_archive_reader.py | 7 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 63 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 76 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 85 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 112 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 123 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_cross_copilot_transfer.py | 9 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_cross_copilot_transfer.py | 13 | type annotation | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_cross_copilot_transfer.py | 146 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_dual_write_store.py | 10 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_dual_write_store.py | 155 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_entity_enrichment.py | 19 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 254 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 270 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 293 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 315 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 331 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 344 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 358 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 366 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 376 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 400 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 411 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 497 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_factory_dual_write.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_factory_dual_write.py | 50 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_factory_dual_write.py | 71 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_five_domain_completeness.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_five_domain_completeness.py | 32 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_gate_preseed_initialization.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 15 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 16 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 28 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 59 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_generate_decision_id.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 14 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 24 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 34 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 46 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 58 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 66 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 87 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_global_queries.py | 6 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 30 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graph_entity_links.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_entity_links.py | 179 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 23 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 59 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_production_boundary.py | 16 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_production_boundary.py | 78 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graphstore_consolidation.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graphstore_consolidation.py | 266 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graphstore_consolidation.py | 268 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_historical_checkpoint_import.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_historical_checkpoint_import.py | 14 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_conformance.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_jm_conformance.py | 46 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_jm_rl_cross_copilot.py | 111 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_rl_cross_copilot.py | 113 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 15 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 101 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 118 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 148 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 169 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_l5_centroid_storage.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 17 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 26 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 42 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 43 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 150 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 55 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 57 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 59 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 99 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 100 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 141 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 227 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 27 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 36 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 60 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 61 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 184 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 201 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 30 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 137 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 149 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 70 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 108 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 195 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_legacy_signal_filter.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_legacy_signal_filter.py | 17 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_outbox_sqlite.py | 9 | import | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 23 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 24 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 31 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 34 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 43 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 64 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 84 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 85 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 86 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 89 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 96 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 97 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 98 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 100 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 104 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 108 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 116 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 132 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 136 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 137 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 139 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 149 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 150 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 151 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 152 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 153 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 163 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 169 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 171 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 173 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 181 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 192 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 193 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 194 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 196 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 198 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 200 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 204 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 210 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 218 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 219 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 220 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_platform_router.py | 10 | import | Migrated to memory/removed scorer SQLite branch |
| tests/test_platform_router.py | 33 | type annotation | Migrated to memory/removed scorer SQLite branch |
| tests/test_platform_router.py | 34 | instantiation/reference | Migrated to memory/removed scorer SQLite branch |
| tests/test_preseed_gap_supersession.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_preseed_gap_supersession.py | 37 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_quality_axis.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_quality_axis.py | 142 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_reconcile_archive.py | 14 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_reconcile_archive.py | 15 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_rule38_factory_compliance.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_rule38_factory_compliance.py | 34 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_rule38_factory_compliance.py | 62 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_scorer_construction.py | 17 | reference/string/comment | Migrated to memory/removed scorer SQLite branch |
| tests/test_scorer_construction.py | 24 | test assertion/type check | Migrated to memory/removed scorer SQLite branch |
| tests/test_session_regression.py | 63 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_session_regression.py | 66 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_situation_analyzer.py | 24 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_situation_analyzer.py | 444 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_situation_analyzer.py | 465 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 33 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 75 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_store_parity.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_store_parity.py | 24 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_switching_cost_router.py | 98 | import | Migrated to memory/removed scorer SQLite branch |
| tests/test_switching_cost_router.py | 103 | instantiation/reference | Migrated to memory/removed scorer SQLite branch |
| tests/test_transfer_pattern.py | 9 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_transfer_pattern.py | 15 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_transfer_pattern.py | 116 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_worker_process_safety.py | 12 | import | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 46 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 61 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 73 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 97 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 134 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 152 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/vld_validation_report.py | 7 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/vld_validation_report.py | 224 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/vld_validation_report.py | 238 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |

### Appendix C — Raw SQLite outside sqlite_store.py before edits

| File | Line | Operation/reference | Migration target/action |
| --- | --- | --- | --- |
| apps/dataops/backend/app/dataops_governance.py | 6 | import sqlite3 | Migrated K/governance raw SQL |
| apps/dataops/backend/app/dataops_governance.py | 35 | self._db = sqlite3.connect(str(db_path), check_same_thread=False) | Migrated K/governance raw SQL |
| apps/dataops/backend/app/main.py | 9 | import sqlite3 | Migrated K/governance raw SQL |
| apps/dataops/backend/app/main.py | 125 | self.conn = sqlite3.connect(path, check_same_thread=False) | Migrated K/governance raw SQL |
| apps/purchasing/backend/app/main.py | 9 | import sqlite3 | Migrated K/governance raw SQL |
| apps/purchasing/backend/app/main.py | 154 | self.conn = sqlite3.connect(path, check_same_thread=False) | Migrated K/governance raw SQL |
| apps/purchasing/backend/app/services/purchasing_control.py | 8 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| apps/purchasing/backend/app/services/purchasing_control.py | 178 | self._db = sqlite3.connect(self.path, check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| apps/purchasing/backend/tests/test_investigation_integration.py | 3 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| apps/purchasing/backend/tests/test_investigation_integration.py | 21 | conn = sqlite3.connect(":memory:", check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| apps/trading/backend/app/cli_sdk.py | 16 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| apps/trading/backend/app/cli_sdk.py | 598 | conn = sqlite3.connect(backup_path) | Separate SQLite service/store; outside four-method scoring migration |
| apps/trading/backend/app/main.py | 9 | import sqlite3 | Migrated K/governance raw SQL |
| apps/trading/backend/app/main.py | 143 | self.conn = sqlite3.connect(path, check_same_thread=False) | Migrated K/governance raw SQL |
| apps/trading/backend/tests/test_investigation_integration.py | 3 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| apps/trading/backend/tests/test_investigation_integration.py | 21 | conn = sqlite3.connect(":memory:", check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/backend/signal_store.py | 9 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/backend/signal_store.py | 31 | sqlite3.connect(":memory:", check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/backend/signal_store.py | 47 | db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/evolution/variant_store.py | 10 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/evolution/variant_store.py | 204 | self._connection = sqlite3.connect( | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/graph/outbox.py | 6 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/graph/outbox.py | 22 | self._connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 17 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 99 | with sqlite3.connect(db_path) as conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 106 | with sqlite3.connect(db_path) as conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 179 | with sqlite3.connect(db_path) as conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 755 | with sqlite3.connect(db_path) as conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 799 | with sqlite3.connect(db_path) as source_conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migrate/sqlite_to_age.py | 1015 | with sqlite3.connect(source_db) as source_conn: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migration/rehearsal.py | 6 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/migration/rehearsal.py | 40 | with sqlite3.connect(path) as connection: | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/outbox/store.py | 6 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/outbox/store.py | 22 | self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/outcome/ledger.py | 7 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/outcome/ledger.py | 21 | self._connection = sqlite3.connect(self.db_path, check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/pilot/transfer.py | 12 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/pilot/transfer.py | 50 | self._connection = sqlite3.connect(db_path, check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/promotion/core.py | 6 | import sqlite3 | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/promotion/core.py | 117 | self._connection = sqlite3.connect(db_path, check_same_thread=False) | Separate SQLite service/store; outside four-method scoring migration |
| copilot_sdk/scoring/investigation.py | 481 | self.conn: Any = conn | Migrated K/governance raw SQL |
| copilot_sdk/scoring/investigation.py | 482 | self.conn.execute( | Migrated K/governance raw SQL |
| copilot_sdk/scoring/investigation.py | 493 | self.conn.commit() | Migrated K/governance raw SQL |
| copilot_sdk/scoring/investigation.py | 496 | rows: Any = self.conn.execute( | Migrated K/governance raw SQL |
| copilot_sdk/scoring/investigation.py | 527 | self.conn.execute( | Migrated K/governance raw SQL |
| copilot_sdk/scoring/investigation.py | 537 | self.conn.commit() | Migrated K/governance raw SQL |
| copilot_sdk/scoring/persistence_outbox.py | 8 | import sqlite3 | Durable scoring failure queue; deferred |
| copilot_sdk/scoring/persistence_outbox.py | 128 | connection = sqlite3.connect(self.db_path, timeout=30.0) | Durable scoring failure queue; deferred |
| experiments/jm_extracted/render_ci_failuremodes_v6.py | 13 | import sqlite3 | Disposable experiment state migrated |
| experiments/jm_extracted/render_ci_failuremodes_v6.py | 95 | conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_cons_pd_decision_features_v1.py | 9 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_cons_pd_decision_features_v1.py | 51 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_conservation_characterization_v1.py | 48 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_conservation_characterization_v1.py | 50 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_conservation_lag_c5_v1.py | 22 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_conservation_lag_c5_v1.py | 321 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_conservation_perdecision_signals_v1.py | 10 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_conservation_perdecision_signals_v1.py | 48 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_rl_ctrl2c_redesign_v1.py | 66 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_rl_ctrl2c_redesign_v1.py | 68 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 18 | import sqlite3 | Disposable experiment state migrated |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 132 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| integrity/architecture_scan.py | 73 | ("copilot-sdk/copilot_sdk/backend/signal_store.py", 'sqlite3.connect(":memory:", check_same_thread=False)'), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 74 | ("copilot-sdk/copilot_sdk/backend/signal_store.py", "db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 76 | ("copilot-sdk/copilot_sdk/evolution/variant_store.py", "self._connection = sqlite3.connect("), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 77 | ("copilot-sdk/copilot_sdk/graph/outbox.py", "self._connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 78 | ("copilot-sdk/copilot_sdk/graph/sqlite_store.py", "self._conn: sqlite3.Connection \| None = sqlite3.connect("), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 79 | ("copilot-sdk/copilot_sdk/migration/rehearsal.py", "with sqlite3.connect(path) as connection:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 80 | ("copilot-sdk/copilot_sdk/outbox/store.py", "self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 81 | ("copilot-sdk/copilot_sdk/outcome/ledger.py", "self._connection = sqlite3.connect(self.db_path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 82 | ("copilot-sdk/copilot_sdk/pilot/transfer.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 83 | ("copilot-sdk/copilot_sdk/promotion/core.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 84 | ("copilot-sdk/copilot_sdk/scoring/persistence_outbox.py", "connection = sqlite3.connect(self.db_path, timeout=30.0)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 86 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 87 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 88 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 89 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 90 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as source_conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 91 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(source_db) as source_conn:"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 93 | ("copilot-sdk/apps/dataops/backend/app/dataops_governance.py", "self._db = sqlite3.connect(str(db_path), check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 94 | ("copilot-sdk/apps/dataops/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 95 | ("copilot-sdk/apps/purchasing/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 96 | ("copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py", "self._db = sqlite3.connect(self.path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 97 | ("copilot-sdk/apps/trading/backend/app/cli_sdk.py", "conn = sqlite3.connect(backup_path)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 98 | ("copilot-sdk/apps/trading/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 99 | ("s2p-copilot/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 100 | ("s2p-copilot/backend/app/services/proposal_service.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 101 | ("gen-ai-roi-demo-v4-v50/backend/app/main.py", "self.conn = sqlite3.connect(path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 102 | ("gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py", "self._audit = sqlite3.connect(self.db_path, check_same_thread=False)"), | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 131 | title="No raw sqlite3.connect in production", | Separate SQLite service/store; outside four-method scoring migration |
| integrity/architecture_scan.py | 136 | message="raw sqlite3.connect bypasses the GraphStore boundary", | Separate SQLite service/store; outside four-method scoring migration |
| scripts/age_migration_benchmark.py | 11 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/age_migration_benchmark.py | 24 | conn = sqlite3.connect(path) | Legacy backend conformance/tooling; retained |
| scripts/age_pf_blockers.py | 9 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/age_pf_blockers.py | 63 | with sqlite3.connect(db_path) as sconn: | Legacy backend conformance/tooling; retained |
| scripts/age_v35_review_checks.py | 6 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/age_v35_review_checks.py | 64 | conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True) | Legacy backend conformance/tooling; retained |
| scripts/d1_recursion_trace_v1.py | 8 | import sqlite3 | Disposable experiment state migrated |
| scripts/d1_recursion_trace_v1.py | 42 | conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/k_learning_conservation_interaction.py | 10 | import sqlite3 | Disposable experiment state migrated |
| scripts/k_learning_conservation_interaction.py | 35 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/k_learning_curve_cross_copilot.py | 16 | import sqlite3 | Disposable experiment state migrated |
| scripts/k_learning_curve_cross_copilot.py | 97 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/k_learning_curve_experiment.py | 14 | import sqlite3 | Disposable experiment state migrated |
| scripts/k_learning_curve_experiment.py | 51 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/k_learning_curve_extended.py | 14 | import sqlite3 | Disposable experiment state migrated |
| scripts/k_learning_curve_extended.py | 54 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/k_learning_distribution_sensitivity.py | 9 | import sqlite3 | Disposable experiment state migrated |
| scripts/k_learning_distribution_sensitivity.py | 32 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/phase3_cycle_gate_v3.py | 131 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/phase3_cycle_gate_v3.py | 138 | conn = sqlite3.connect(outbox_path) | Legacy backend conformance/tooling; retained |
| scripts/phase3_dual_write_e2e_v4.py | 138 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/phase3_dual_write_e2e_v4.py | 141 | oconn = sqlite3.connect(OUTBOX_PATH) | Legacy backend conformance/tooling; retained |
| scripts/phase3_dual_write_e2e_v5.py | 3 | import sqlite3 as sqlite3_mod | Legacy backend conformance/tooling; retained |
| scripts/phase3_reset_v3.py | 6 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/phase3_reset_v3.py | 43 | conn_sq = sqlite3.connect(CORRECT_DB) | Legacy backend conformance/tooling; retained |
| scripts/phase3_verify_v3.py | 3 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/phase3_verify_v3.py | 26 | sq = sqlite3.connect(SQLITE_PATH) | Legacy backend conformance/tooling; retained |
| scripts/phase_dual_write_e2e.py | 32 | with sqlite3.connect(cfg['outbox_path']) as outbox: | Legacy backend conformance/tooling; retained |
| scripts/phase_verify.py | 14 | with sqlite3.connect(cfg["db_path"]) as source: | Legacy backend conformance/tooling; retained |
| scripts/refresh_demo_centroid_checkpoints.py | 13 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/refresh_demo_centroid_checkpoints.py | 216 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| scripts/routing_variant_risk_sensitive.py | 13 | import sqlite3 | Disposable experiment state migrated |
| scripts/routing_variant_risk_sensitive.py | 39 | self.conn = sqlite3.connect(":memory:") | Disposable experiment state migrated |
| scripts/sqlite_copilot_audit.py | 16 | import sqlite3 | Legacy backend conformance/tooling; retained |
| scripts/sqlite_copilot_audit.py | 74 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| scripts/sqlite_copilot_audit.py | 267 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_graph_store_evolution.py | 4 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/graph/test_graph_store_evolution.py | 11 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_graph_store_evolution.py | 93 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_conformance.py | 7 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_conformance.py | 102 | with sqlite3.connect(db_path) as conn: | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_conformance.py | 1003 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_conformance.py | 2603 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_service_layer.py | 161 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/graph/test_protocol_v2_service_layer.py | 163 | connection = sqlite3.connect(str(Path(directory) / "outbox.sqlite")) | Legacy backend conformance/tooling; retained |
| tests/graph/test_sqlite_store.py | 3 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/graph/test_sqlite_store.py | 30 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/graph/test_sqlite_store.py | 346 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/scoring/test_persistence_outbox.py | 3 | import sqlite3 | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 91 | with sqlite3.connect(outbox_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 114 | with sqlite3.connect(outbox_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 136 | with sqlite3.connect(outbox.db_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 152 | with sqlite3.connect(outbox_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 220 | with sqlite3.connect(outbox_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_persistence_outbox.py | 305 | with sqlite3.connect(outbox_path) as connection: | Durable scoring failure queue; deferred |
| tests/scoring/test_storage.py | 3 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/scoring/test_storage.py | 228 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_age_unification_invariants.py | 228 | if path.exists() and ("import sqlite3" in _source(path) or "import aiosqlite" in _source(path)) | Legacy backend conformance/tooling; retained |
| tests/test_centroid_refresh.py | 2 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_centroid_refresh.py | 64 | conn = sqlite3.connect(db) | Legacy backend conformance/tooling; retained |
| tests/test_centroid_refresh.py | 104 | conn = sqlite3.connect(db) | Legacy backend conformance/tooling; retained |
| tests/test_centroid_refresh.py | 112 | conn = sqlite3.connect(db) | Legacy backend conformance/tooling; retained |
| tests/test_dual_write_outbox.py | 3 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_dual_write_outbox.py | 63 | connection = sqlite3.connect(path) | Legacy backend conformance/tooling; retained |
| tests/test_graphstore_consolidation.py | 4 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_graphstore_consolidation.py | 91 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_integrity_scanner.py | 75 | (1, ".py", "connection = sqlite3.connect('local.db')\n"), | Legacy backend conformance/tooling; retained |
| tests/test_integrity_scanner.py | 135 | "extra_connection = sqlite3.connect('unexpected.db')\n", | Legacy backend conformance/tooling; retained |
| tests/test_investigation.py | 3 | import sqlite3 | Migrated K/governance raw SQL |
| tests/test_investigation.py | 104 | conn = sqlite3.connect(tmp_path / "k.sqlite3") | Migrated K/governance raw SQL |
| tests/test_l5_dk_welford_storage.py | 4 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_l5_dk_welford_storage.py | 110 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_learn_context.py | 4 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_learn_context.py | 165 | connection = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_migration_live_age.py | 11 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_migration_live_age.py | 93 | conn = sqlite3.connect(path) | Legacy backend conformance/tooling; retained |
| tests/test_migration_live_age.py | 252 | conn = sqlite3.connect(source) | Legacy backend conformance/tooling; retained |
| tests/test_migration_resilience.py | 5 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_migration_resilience.py | 16 | conn = sqlite3.connect(path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 3 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 104 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 138 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 644 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 706 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 790 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 839 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 856 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 882 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 908 | conn = sqlite3.connect(db_path) | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 1006 | with sqlite3.connect(db_path) as source: | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 1028 | with sqlite3.connect(db_path) as source: | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 1049 | with sqlite3.connect(db_path) as source: | Legacy backend conformance/tooling; retained |
| tests/test_sqlite_to_age_migration.py | 1066 | with sqlite3.connect(db_path) as source: | Legacy backend conformance/tooling; retained |
| tests/vld_validation_report.py | 25 | import sqlite3 | Legacy backend conformance/tooling; retained |
| tests/vld_validation_report.py | 242 | with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection: | Legacy backend conformance/tooling; retained |

### Appendix D — db_path usages before edits

| File | Line | Usage | What it selects / action |
| --- | --- | --- | --- |
| apps/dataops/backend/app/dataops_governance.py | 25 | def __init__(self, db_path: str \| Path, graph_store: Any, scorer: Any, conservation: Any, *, profile: str \| None = None) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/dataops_governance.py |
| apps/dataops/backend/app/dataops_governance.py | 35 | self._db = sqlite3.connect(str(db_path), check_same_thread=False) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| apps/dataops/backend/app/dataops_governance.py | 48 | self._outcomes = GraphOutcomeLedger(graph_store, "dataops") if age_events else OutcomeLedger(":memory:" if str(db_path) == ":memory:" else str(Path(db_path).with_name("dataops_outc | Constructor: OutcomeLedger; separate service or retained legacy fixture |
| apps/dataops/backend/app/main.py | 227 | def _graph_store(db_path: str \| Path, *, graph_config: GraphConfig \| None = None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/main.py |
| apps/dataops/backend/app/main.py | 231 | db_path=str(db_path), | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| apps/dataops/backend/app/main.py | 414 | db_path: str \| Path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/main.py |
| apps/dataops/backend/app/main.py | 427 | return _graph_store(db_path, graph_config=graph_config) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _graph_store |
| apps/dataops/backend/app/main.py | 430 | def _resolve_scoring_db(db_path: str \| Path \| None) -> str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/main.py |
| apps/dataops/backend/app/main.py | 431 | if db_path is not None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/main.py |
| apps/dataops/backend/app/main.py | 432 | resolved = Path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path |
| apps/dataops/backend/app/main.py | 682 | db_path: str \| Path \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/app/main.py |
| apps/dataops/backend/app/main.py | 705 | scoring_db = _resolve_scoring_db(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _resolve_scoring_db |
| apps/dataops/backend/app/main.py | 882 | db_path=scoring_db, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: app.include_router, create_scoring_router |
| apps/dataops/backend/tests/conftest.py | 90 | app = create_app(db_path=dataops_data_dir / "test_dataops.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_bundle_wiring.py | 18 | with TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_bundle_wiring.py | 23 | db_path = tmp_path / "startup_bundle.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_bundle_wiring.py |
| apps/dataops/backend/tests/test_bundle_wiring.py | 24 | with TestClient(create_app(db_path=db_path)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_bundle_wiring.py | 27 | store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="DOPS-") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_dataops_backend.py | 216 | db_path = tmp_path / "dataops_seeded.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 217 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 221 | assert _count_decisions(db_path, "dataops") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/dataops/backend/tests/test_dataops_backend.py | 222 | assert _count_verified(db_path, "dataops") == expected_verified | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/dataops/backend/tests/test_dataops_backend.py | 223 | assert _count_correct(db_path, "dataops") == expected_correct | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_correct |
| apps/dataops/backend/tests/test_dataops_backend.py | 230 | db_path = tmp_path / "dataops_populated.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 231 | store = SQLiteGraphStore(db_path, domain="dataops") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_dataops_backend.py | 237 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 240 | assert _count_decisions(db_path, "dataops") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/dataops/backend/tests/test_dataops_backend.py | 251 | db_path = data_dir / "dataops.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 252 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/dataops/backend/tests/test_dataops_backend.py | 253 | assert _count_decisions(db_path, "dataops") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/dataops/backend/tests/test_dataops_backend.py | 254 | assert _count_verified(db_path, "dataops") == _fixture_outcome_counts(DATAOPS_SEED_PATH)[0] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/dataops/backend/tests/test_dataops_backend.py | 264 | with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 276 | db_path = tmp_path / "fallback.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 277 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 280 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/dataops/backend/tests/test_dataops_backend.py | 281 | assert _count_decisions(db_path, "dataops") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/dataops/backend/tests/test_dataops_backend.py | 287 | with TestClient(create_app(db_path=tmp_path / "l5-status.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 326 | with TestClient(app_main.create_app(db_path=tmp_path / "ordered.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 540 | client = TestClient(create_app(db_path=tmp_path / "fresh_dataops.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 586 | client = TestClient(create_app(db_path=tmp_path / "fresh_audit_dataops.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 632 | create_app(db_path=tmp_path / "seeded_pattern_origin.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 1311 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 1366 | client = TestClient(create_app(db_path=tmp_path / "fresh_variants_dataops.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_backend.py | 1528 | def _count_decisions(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 1531 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_dataops_backend.py | 1538 | def _count_verified(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 1541 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_dataops_backend.py | 1548 | def _count_correct(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_backend.py |
| apps/dataops/backend/tests/test_dataops_backend.py | 1551 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 154 | def _run_startup_probe(db_path: Path, *, demo: bool) -> dict[str, object]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_fixture_closure.py |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 162 | db_path = Path(__import__('sys').argv[1]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_fixture_closure.py |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 163 | app = create_app(db_path=db_path, demo_bundle_path=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_fixture_closure.py |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 170 | store = SQLiteGraphStore(str(db_path), domain='dataops', decision_id_prefix='DOPS-') | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_fixture_closure.py |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 195 | [sys.executable, "-c", code, str(db_path)], | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: subprocess.run, str |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 35 | client = TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 57 | client = TestClient(create_app(db_path=tmp_path / "dataops.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 184 | db_path=tmp_path / "dataops.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 278 | sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 348 | db_path=tmp_path / "dataops.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 437 | def _sqlite_decision_count(db_path: Path) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/dataops/backend/tests/test_dataops_graph_status.py |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 440 | store = SQLiteGraphStore(db_path, domain="dataops") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/dataops/backend/tests/test_demo_investigation_import.py | 21 | app = import_module("app.main").create_app(db_path=dataops_data_dir / "k14.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_evolution_dataops.py | 104 | client = TestClient(create_app(db_path=tmp_path / "fresh_dataops_variants.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/dataops/backend/tests/test_graph_config_injection.py | 73 | db_path=dataops_data_dir / "injection.db", demo_bundle_path=False, | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/app/main.py | 227 | def from_environment(cls, db_path: str \| Path \| None) -> "PurchasingPathConfig": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 228 | if db_path is not None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 229 | resolved: str \| Path = db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 260 | def _graph_store(db_path: str \| Path, *, backend: str \| None = None, profile: str \| None = None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 285 | db_path=str(db_path), | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| apps/purchasing/backend/app/main.py | 310 | def _resolve_scoring_db(db_path: str \| Path \| None) -> str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 311 | return PurchasingPathConfig.from_environment(db_path).scoring_db | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: PurchasingPathConfig.from_environment |
| apps/purchasing/backend/app/main.py | 560 | db_path: str \| Path \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/app/main.py |
| apps/purchasing/backend/app/main.py | 582 | scoring_db = _resolve_scoring_db(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _resolve_scoring_db |
| apps/purchasing/backend/app/main.py | 923 | db_path=scoring_db, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: app.include_router, create_scoring_router |
| apps/purchasing/backend/app/routers/queue.py | 223 | _SCORER = CompoundingScorer.from_preset(DOMAIN, db_path=":memory:") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/purchasing/backend/cli.py | 49 | def _store(db_path: Path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/cli.py |
| apps/purchasing/backend/cli.py | 56 | db_path=str(db_path.expanduser()), | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| apps/purchasing/backend/cli.py | 62 | def _scorer(db_path: Path) -> CompoundingScorer: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/cli.py |
| apps/purchasing/backend/cli.py | 63 | resolved = str(db_path.expanduser()) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, db_path.expanduser |
| apps/purchasing/backend/cli.py | 64 | store = _store(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store |
| apps/purchasing/backend/cli.py | 66 | DOMAIN, db_path=resolved, graph_store=store, profile=_cli_profile() | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/purchasing/backend/cli.py | 296 | def cli(ctx: click.Context, db_path: Path) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/cli.py |
| apps/purchasing/backend/cli.py | 299 | ctx.obj = {"db_path": db_path.expanduser()} | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.expanduser |
| apps/purchasing/backend/cli.py | 317 | result = _scorer(ctx.obj["db_path"]).score( | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _scorer(ctx.obj['db_path']).score, _scorer |
| apps/purchasing/backend/cli.py | 345 | result = _scorer(ctx.obj["db_path"]).learn(decision_id, actual_action, outcome=outcome) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _scorer(ctx.obj['db_path']).learn, _scorer |
| apps/purchasing/backend/cli.py | 362 | store = _store(ctx.obj["db_path"]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store |
| apps/purchasing/backend/cli.py | 393 | payload = asdict(_scorer(ctx.obj["db_path"]).trajectory()) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _scorer(ctx.obj['db_path']).trajectory, _scorer |
| apps/purchasing/backend/cli.py | 403 | payload = asdict(_scorer(ctx.obj["db_path"]).fingerprint()) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _scorer(ctx.obj['db_path']).fingerprint, _scorer |
| apps/purchasing/backend/cli.py | 417 | db_path = ctx.obj["db_path"] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/cli.py |
| apps/purchasing/backend/cli.py | 419 | backup_dir = db_path.expanduser().parent / "backup" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.expanduser |
| apps/purchasing/backend/cli.py | 425 | store = _store(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store |
| apps/purchasing/backend/cli.py | 462 | store = _store(ctx.obj["db_path"]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store |
| apps/purchasing/backend/tests/conftest.py | 97 | db_path = tmp_path / "purchasing_test.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/conftest.py |
| apps/purchasing/backend/tests/conftest.py | 98 | store = SQLiteGraphStore(str(db_path), domain="purchasing", decision_id_prefix="PUR-") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/conftest.py | 100 | app = create_app(db_path=db_path, demo_bundle_path=False, profile="test") | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/conftest_helpers.py | 22 | scorer = CompoundingScorer.from_preset(domain, db_path=db, graph_store=store, profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/purchasing/backend/tests/test_alert_engine.py | 137 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_alert_engine.py | 144 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_alert_engine.py | 151 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_alert_engine.py | 158 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 18 | with TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 23 | db_path = tmp_path / "startup_bundle.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_bundle_wiring.py |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 24 | with TestClient(create_app(db_path=db_path)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 27 | store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="PUR-") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_chain_demo.py | 66 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_chain_demo.py | 82 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_commodity.py | 34 | return TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_cross_discovery.py | 91 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_cross_discovery.py | 98 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_delivery_coordinator.py | 67 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_delivery_coordinator.py | 74 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_economic_model.py | 87 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_event_planner.py | 63 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_event_planner.py | 70 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_event_planner.py | 79 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_event_planner.py | 87 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_evolution_purchasing.py | 170 | client = TestClient(create_app(db_path=tmp_path / "fresh_purchasing.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_menu_engineer.py | 74 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_menu_engineer.py | 83 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_menu_engineer.py | 91 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_multi_unit.py | 100 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_multi_unit.py | 107 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_par_optimizer.py | 13 | return TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_pos_router.py | 10 | return TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_predictive_par.py | 79 | app = create_app(db_path=":memory:", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_predictive_par.py | 88 | app = create_app(db_path=":memory:", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_predictive_par.py | 153 | app = create_app(db_path=":memory:", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_predictive_par.py | 170 | app = create_app(db_path=":memory:", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_active_age_live.py | 33 | client = TestClient(create_app(db_path=tmp_path / "unused.sqlite", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 116 | app_main.create_app(db_path=tmp_path / "prod-defaults.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 304 | db_path = tmp_path / "purchasing_seeded.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 305 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 309 | assert _count_decisions(db_path, "purchasing") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 310 | assert _count_verified(db_path, "purchasing") == expected_verified | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 311 | assert _count_correct(db_path, "purchasing") == expected_correct | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_correct |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 318 | db_path = tmp_path / "purchasing_populated.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 319 | store = SQLiteGraphStore(db_path, domain="purchasing") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 325 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 328 | assert _count_decisions(db_path, "purchasing") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 389 | db_path = data_dir / "purchasing.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 390 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 391 | assert _count_decisions(db_path, "purchasing") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 392 | assert _count_verified(db_path, "purchasing") == _fixture_outcome_counts(DATA_DIR / "purchasing_seed_v2.json")[0] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 402 | with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 414 | db_path = tmp_path / "fallback.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 415 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 418 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 419 | assert _count_decisions(db_path, "purchasing") == 20 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 425 | with TestClient(create_app(db_path=tmp_path / "l5-status.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 459 | with TestClient(app_main.create_app(db_path=tmp_path / "ordered.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 691 | client = TestClient(create_app(db_path=tmp_path / "fresh_purchasing.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 749 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 807 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 808 | store = SQLiteGraphStore(db_path, domain="purchasing") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 822 | assert _graph_store(str(db_path)).count_verified("purchasing") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _graph_store, str |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 829 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 830 | store = SQLiteGraphStore(db_path, domain="purchasing") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 851 | assert _graph_store(str(db_path)).count_correct("purchasing") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _graph_store, str |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 900 | client = TestClient(create_app(db_path=tmp_path / "fresh_variants_purchasing.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 977 | def _seed_verified_history(db_path: Path, total: int) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 984 | store = SQLiteGraphStore(db_path, domain="purchasing") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1006 | def _count_decisions(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1009 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1016 | def _count_verified(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1019 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1026 | def _count_correct(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_backend.py |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1029 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_purchasing_config_migration.py | 150 | scorer = CompoundingScorer.from_preset("purchasing", db_path=str(tmp_path / "purchasing.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 34 | client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 57 | client = TestClient(create_app(db_path=tmp_path / "purchasing.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 184 | db_path=tmp_path / "purchasing.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 214 | db_path=tmp_path / "purchasing.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 248 | db_path=tmp_path / "purchasing.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 278 | db_path=tmp_path / "active.sqlite", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 289 | sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 420 | def _sqlite_decision_count(db_path: Path) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_purchasing_graph_status.py |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 423 | store = SQLiteGraphStore(db_path, domain="purchasing") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/purchasing/backend/tests/test_qbo_connector.py | 16 | return TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/purchasing/backend/tests/test_trust_analysis.py | 13 | db_path = os.path.join(str(tmp_path), "trust.db") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/purchasing/backend/tests/test_trust_analysis.py |
| apps/purchasing/backend/tests/test_trust_analysis.py | 14 | scorer = CompoundingScorer.from_preset("purchasing", db_path=db_path, profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/purchasing/backend/tests/test_weather_factor.py | 55 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/regime_experiment/experiment.py | 120 | def _new_scorer(db_path: str) -> tuple[CompoundingScorer, SQLiteGraphStore]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/regime_experiment/experiment.py |
| apps/regime_experiment/experiment.py | 121 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/s2p_differentiation/engine.py | 181 | db_path=str(path), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/app/cli_sdk.py | 91 | def _db_path(db_path: str \| None = None) -> str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 92 | return os.path.expanduser(db_path or DEFAULT_DB_PATH) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: os.path.expanduser |
| apps/trading/backend/app/cli_sdk.py | 95 | def _get_scorer(db_path: str \| None = None) -> CompoundingScorer: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 96 | path = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 105 | db_path=path, | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| apps/trading/backend/app/cli_sdk.py | 116 | DOMAIN, db_path=path, graph_store=store, profile=profile | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/app/cli_sdk.py | 221 | def init_sdk(db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 223 | path = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 229 | "db_path": path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 239 | def score_sdk(category: str, factors: str \| dict[str, Any], db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 243 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 251 | def decide_sdk(category: str, factors: str \| dict[str, Any], db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 255 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 286 | def learn_sdk(decision: str, action: str, db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 289 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 320 | def record_sdk(category: str, factors: str \| dict[str, Any], action: str, db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 325 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 372 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 378 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 434 | def conservation_sdk(db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 436 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 459 | def status_sdk(db_path: str \| None = None, output_format: str = "json") -> dict[str, Any] \| str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 461 | path = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 470 | trust = trust_sdk(db_path=path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: trust_sdk |
| apps/trading/backend/app/cli_sdk.py | 489 | "db_path": path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 499 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 503 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 533 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 540 | path = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 544 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 568 | def backup_sdk(backup_path: str \| None = None, db_path: str \| None = None) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 570 | src = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 571 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 589 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 609 | dest = _db_path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _db_path |
| apps/trading/backend/app/cli_sdk.py | 623 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/cli_sdk.py |
| apps/trading/backend/app/cli_sdk.py | 638 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/app/cli_sdk.py | 808 | f"DB:           {payload['db_path']}", | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: '\n'.join |
| apps/trading/backend/app/cli_sdk.py | 856 | return _run_json_command(lambda: init_sdk(args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, init_sdk |
| apps/trading/backend/app/cli_sdk.py | 860 | return _run_json_command(lambda: score_sdk(args.category, args.factors, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, score_sdk |
| apps/trading/backend/app/cli_sdk.py | 864 | return _run_json_command(lambda: decide_sdk(args.category, args.factors, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, decide_sdk |
| apps/trading/backend/app/cli_sdk.py | 868 | return _run_json_command(lambda: learn_sdk(args.decision, args.action, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, learn_sdk |
| apps/trading/backend/app/cli_sdk.py | 872 | return _run_json_command(lambda: record_sdk(args.category, args.factors, args.action, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, record_sdk |
| apps/trading/backend/app/cli_sdk.py | 877 | lambda: trust_sdk(args.category, args.db_path, args.format), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, trust_sdk |
| apps/trading/backend/app/cli_sdk.py | 883 | return _run_json_command(lambda: conservation_sdk(args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, conservation_sdk |
| apps/trading/backend/app/cli_sdk.py | 888 | lambda: status_sdk(args.db_path, args.format), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, status_sdk |
| apps/trading/backend/app/cli_sdk.py | 895 | lambda: journal_sdk(args.limit, args.db_path, args.format), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, journal_sdk |
| apps/trading/backend/app/cli_sdk.py | 901 | return _run_json_command(lambda: export_sdk(args.format, args.output, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, export_sdk |
| apps/trading/backend/app/cli_sdk.py | 905 | return _run_json_command(lambda: backup_sdk(args.backup_path, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, backup_sdk |
| apps/trading/backend/app/cli_sdk.py | 909 | return _run_json_command(lambda: restore_sdk(args.backup_path, args.confirm, args.db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, restore_sdk |
| apps/trading/backend/app/cli_sdk.py | 920 | db_path=args.db_path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_json_command, import_sdk |
| apps/trading/backend/app/main.py | 198 | def _graph_store(db_path: str \| Path, *, profile: str \| None = None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/main.py |
| apps/trading/backend/app/main.py | 223 | db_path=str(db_path), | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| apps/trading/backend/app/main.py | 234 | def _resolve_scoring_db(db_path: str \| Path \| None) -> str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/main.py |
| apps/trading/backend/app/main.py | 235 | if db_path is not None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/main.py |
| apps/trading/backend/app/main.py | 236 | resolved = Path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path |
| apps/trading/backend/app/main.py | 383 | db_path: str \| Path \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/app/main.py |
| apps/trading/backend/app/main.py | 400 | scoring_db = _resolve_scoring_db(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _resolve_scoring_db |
| apps/trading/backend/app/main.py | 437 | logger.info("PRIMARY_PATH: %s", getattr(primary, "_db_path", getattr(primary, "db_path", None))) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr, getattr |
| apps/trading/backend/app/main.py | 560 | db_path=scoring_db, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: app.include_router, create_scoring_router |
| apps/trading/backend/cli.py | 1005 | if getattr(args, "db_path", None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr |
| apps/trading/backend/cli.py | 1013 | for name in ("db_path", "category", "factors") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: any |
| apps/trading/backend/cli.py | 1024 | if getattr(args, "db_path", None) or getattr(args, "category", None) or getattr(args, "format", None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr |
| apps/trading/backend/cli.py | 1030 | if getattr(args, "db_path", None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr |
| apps/trading/backend/cli.py | 1036 | if getattr(args, "db_path", None) or getattr(args, "format", None): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr |
| apps/trading/backend/tests/conftest.py | 90 | app = create_app(db_path=tmp_path / "trading_test.db", demo_bundle_path=False, profile="test") | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/conftest_helpers.py | 35 | scorer = CompoundingScorer.from_preset(domain, db_path=db, graph_store=store, profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/conftest_helpers.py | 114 | scorer = CompoundingScorer.from_preset(domain, db_path=db, graph_store=store, profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/test_analytics.py | 46 | return TestClient(create_app(db_path=tmp_path / "trading_analytics.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_bundle_wiring.py | 18 | with TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_bundle_wiring.py | 23 | db_path = tmp_path / "startup_bundle.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_bundle_wiring.py |
| apps/trading/backend/tests/test_bundle_wiring.py | 24 | with TestClient(create_app(db_path=db_path)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_bundle_wiring.py | 27 | store = SQLiteGraphStore(str(db_path), domain=DOMAIN, decision_id_prefix="TRD-") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_cli_sdk.py | 44 | def db_path(): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 65 | def _decisions(db_path: str) -> list[dict]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 66 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/tests/test_cli_sdk.py | 73 | def _verified(db_path: str) -> list[dict]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 74 | scorer = _get_scorer(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _get_scorer |
| apps/trading/backend/tests/test_cli_sdk.py | 81 | def test_init_creates_db(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 82 | result = init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 84 | assert Path(db_path).exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).exists, Path |
| apps/trading/backend/tests/test_cli_sdk.py | 85 | assert result["db_path"] == db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 91 | def test_init_idempotent(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 92 | first = init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 93 | second = init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 95 | assert first["db_path"] == second["db_path"] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 101 | def test_score_valid(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 102 | result = score_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 110 | def test_score_invalid_category(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 112 | score_sdk("forex", _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 118 | def test_score_invalid_factor_name(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 123 | score_sdk(_category(), factors, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 129 | def test_score_factor_out_of_range(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 134 | score_sdk(_category(), factors, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 140 | def test_score_nan_factor(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 145 | score_sdk(_category(), factors, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 151 | def test_score_inf_factor(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 156 | score_sdk(_category(), factors, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 162 | def test_score_read_only_no_decision(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 163 | score_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 165 | assert _decisions(db_path) == [] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 168 | def test_decide_creates_decision(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 169 | result = decide_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: decide_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 171 | decisions = _decisions(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 177 | def test_learn_records_outcome(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 178 | decision = decide_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: decide_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 180 | result = learn_sdk(decision["decision_id"], decision["action"], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: learn_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 182 | verified = _verified(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verified |
| apps/trading/backend/tests/test_cli_sdk.py | 191 | db_path, decision_id, action = seed_paused_scorer(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 193 | result = learn_sdk(decision_id, action, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: learn_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 201 | def test_record_creates_both(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 202 | result = record_sdk(_category(), _all_factors(), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 206 | assert len(_decisions(db_path)) == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: len, _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 207 | assert len(_verified(db_path)) == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: len, _verified |
| apps/trading/backend/tests/test_cli_sdk.py | 211 | db_path, _decision_id, _action = seed_paused_scorer(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 212 | preview = score_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 214 | result = record_sdk(_category(), _all_factors(), preview["action"], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 223 | def test_record_self_confirm_warning(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 224 | preview = score_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 226 | result = record_sdk(_category(), _all_factors(), preview["action"], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 232 | def test_record_no_warning_when_different(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 233 | preview = score_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: score_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 236 | result = record_sdk(_category(), _all_factors(), actual, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 242 | def test_trust_pre_transition(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 243 | result = trust_sdk(db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: trust_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 249 | def test_conservation_initial(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 250 | result = conservation_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: conservation_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 258 | def test_journal_empty(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 259 | result = journal_sdk(db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: journal_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 264 | def test_journal_after_records(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 265 | record_sdk(_category(), _all_factors(0.55), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 266 | record_sdk(_category(), _all_factors(0.60), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 267 | record_sdk(_category(), _all_factors(0.65), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 269 | result = journal_sdk(db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: journal_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 276 | def test_journal_returns_newest(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 278 | record_sdk(_category(), _all_factors(0.50 + idx * 0.01), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 280 | all_ids = [row["decision_id"] for row in _decisions(db_path)] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 281 | result = journal_sdk(limit=3, db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: journal_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 286 | def test_status_composition(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 287 | record_sdk(_category(), _all_factors(), _actions()[0], db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: record_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 289 | result = status_sdk(db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: status_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 295 | assert result["db_path"] == db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 298 | def test_db_path_override(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 299 | result = init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 301 | assert result["db_path"] == db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 302 | assert Path(db_path).exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).exists, Path |
| apps/trading/backend/tests/test_cli_sdk.py | 310 | assert result["db_path"] == "test.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 338 | def test_export_json(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 340 | decide_sdk(_category(), _all_factors(value), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: decide_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 343 | result = export_sdk(format="json", output_path=str(output), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: export_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 351 | def test_export_csv(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 353 | decide_sdk(_category(), _all_factors(value), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: decide_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 356 | result = export_sdk(format="csv", output_path=str(output), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: export_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 364 | def test_export_empty(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 367 | result = export_sdk(format="json", output_path=str(output), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: export_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 373 | def test_backup_creates_file(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 374 | init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 377 | result = backup_sdk(backup_path=str(backup), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: backup_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 379 | assert result["backed_up"] == db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 383 | def test_restore_requires_confirm(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 384 | init_sdk(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: init_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 385 | backup = backup_sdk(backup_path=str(tmp_path / "backup.db"), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: backup_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 387 | result = restore_sdk(backup["backup_path"], confirm=False, db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: restore_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 392 | def test_restore_with_confirm(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 393 | decide_sdk(_category(), _all_factors(), db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: decide_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 394 | backup = backup_sdk(backup_path=str(tmp_path / "backup.db"), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: backup_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 395 | Path(db_path).write_text("not sqlite", encoding="utf-8") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).write_text, Path |
| apps/trading/backend/tests/test_cli_sdk.py | 397 | result = restore_sdk(backup["backup_path"], confirm=True, db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: restore_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 399 | assert result["restored_to"] == db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 400 | assert len(_decisions(db_path)) == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: len, _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 403 | def test_import_csv_basic(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 412 | result = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: import_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 416 | assert len(_decisions(db_path)) == 2 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: len, _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 419 | def test_import_dedup(db_path, tmp_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 427 | first = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: import_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 428 | second = import_sdk(source="csv", file_path=str(csv_path), db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: import_sdk |
| apps/trading/backend/tests/test_cli_sdk.py | 433 | assert len(_decisions(db_path)) == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: len, _decisions |
| apps/trading/backend/tests/test_cli_sdk.py | 446 | def test_import_unknown_broker(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_cli_sdk.py |
| apps/trading/backend/tests/test_cli_sdk.py | 448 | import_sdk(source="broker", broker="nonexistent", db_path=db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: import_sdk |
| apps/trading/backend/tests/test_journal.py | 67 | app = create_app(db_path=tmp_path / "trading_journal.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_journal_query.py | 125 | app = create_app(db_path=tmp_path / "trading_journal_query.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_options_scored_factors.py | 146 | scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/test_options_scored_factors.py | 161 | scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/test_regime_analytics.py | 102 | client = TestClient(create_app(db_path=tmp_path / "regime_analytics.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_regime_analytics.py | 111 | scorer = CompoundingScorer.from_preset("trading", db_path=tmp_path / "zero_writes.db", profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/test_regime_replay.py | 46 | app = create_app(db_path=path, demo_bundle_path=False, profile="test") | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_situation_analyzer.py | 60 | client = TestClient(create_app(db_path=tmp_path / "situation.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_situation_judgment.py | 56 | client = TestClient(create_app(db_path=tmp_path / "situation-judgment.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_active_age_live.py | 36 | client = TestClient(create_app(db_path=tmp_path / "unused.sqlite", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 157 | app_main.create_app(db_path=tmp_path / "prod-defaults.db", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 421 | db_path = tmp_path / "trading_seeded.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 422 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 426 | assert _count_decisions(db_path, "trading") == 40 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/trading/backend/tests/test_trading_backend.py | 427 | assert _count_verified(db_path, "trading") == expected_verified | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/trading/backend/tests/test_trading_backend.py | 428 | assert _count_correct(db_path, "trading") == expected_correct | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_correct |
| apps/trading/backend/tests/test_trading_backend.py | 435 | db_path = tmp_path / "trading_populated.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 436 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 442 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 445 | assert _count_decisions(db_path, "trading") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/trading/backend/tests/test_trading_backend.py | 506 | db_path = data_dir / "trading.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 507 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/trading/backend/tests/test_trading_backend.py | 508 | assert _count_decisions(db_path, "trading") == 40 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/trading/backend/tests/test_trading_backend.py | 509 | assert _count_verified(db_path, "trading") == _fixture_outcome_counts(DATA_DIR / "trading_seed_v2.json")[0] | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_verified |
| apps/trading/backend/tests/test_trading_backend.py | 519 | with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 531 | db_path = tmp_path / "fallback.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 532 | with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 535 | assert db_path.exists() | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| apps/trading/backend/tests/test_trading_backend.py | 536 | assert _count_decisions(db_path, "trading") == 40 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _count_decisions |
| apps/trading/backend/tests/test_trading_backend.py | 542 | with TestClient(create_app(db_path=tmp_path / "l5-status.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 579 | with TestClient(app_main.create_app(db_path=tmp_path / "ordered.db", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 741 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_backend.py | 803 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 804 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 818 | assert _graph_store(str(db_path)).count_verified("trading") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _graph_store, str |
| apps/trading/backend/tests/test_trading_backend.py | 825 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 826 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 847 | assert _graph_store(str(db_path)).count_correct("trading") == 1 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _graph_store, str |
| apps/trading/backend/tests/test_trading_backend.py | 890 | def _seed_verified_history(db_path: Path, total: int) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 897 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 919 | def _count_decisions(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 922 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 929 | def _count_verified(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 932 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_backend.py | 939 | def _count_correct(db_path: Path, domain: str) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_backend.py |
| apps/trading/backend/tests/test_trading_backend.py | 942 | store = SQLiteGraphStore(db_path, domain=domain) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_trading_config_migration.py | 131 | scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| apps/trading/backend/tests/test_trading_evidence.py | 159 | app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test") | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_evidence.py | 167 | app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test") | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_evolver.py | 191 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_evolver.py | 215 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 38 | client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 61 | client = TestClient(create_app(db_path=tmp_path / "trading.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 240 | db_path=tmp_path / "trading.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 357 | sqlite_client = TestClient(create_app(db_path=sqlite_db, demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 417 | db_path=tmp_path / "trading.db", | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_trading_graph_status.py | 506 | def _sqlite_decision_count(db_path: Path) -> int: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: apps/trading/backend/tests/test_trading_graph_status.py |
| apps/trading/backend/tests/test_trading_graph_status.py | 509 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| apps/trading/backend/tests/test_vol_analytics.py | 19 | return TestClient(create_app(db_path=tmp_path / "trading_vol_analytics.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| apps/trading/backend/tests/test_volatility_scenarios.py | 67 | client = TestClient(create_app(db_path=tmp_path / "volatility.db", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| copilot_sdk/backend/diagnostics_models.py | 478 | outbox_path=str(getattr(outbox, "db_path")) if outbox is not None and getattr(outbox, "db_path", None) is not None else None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: getattr, getattr |
| copilot_sdk/backend/scorer_proxy.py | 20 | db_path: str \| Path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/backend/scorer_proxy.py |
| copilot_sdk/backend/scorer_proxy.py | 25 | self._db_path = str(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| copilot_sdk/backend/scorer_proxy.py | 26 | self.graph_store = graph_store_factory(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: graph_store_factory |
| copilot_sdk/backend/scoring_router.py | 144 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/backend/scoring_router.py |
| copilot_sdk/backend/scoring_router.py | 171 | domain, db_path=db_path, profile=profile | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| copilot_sdk/backend/signal_store.py | 27 | def __init__(self, db_path: str = ":memory:", *, profile: str \| None = None) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/backend/signal_store.py |
| copilot_sdk/backend/signal_store.py | 28 | self.db_path = db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/backend/signal_store.py |
| copilot_sdk/backend/signal_store.py | 32 | if db_path == ":memory:" else None | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/backend/signal_store.py |
| copilot_sdk/backend/signal_store.py | 35 | Path(db_path).parent.mkdir(parents=True, exist_ok=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).parent.mkdir, Path |
| copilot_sdk/backend/signal_store.py | 47 | db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/demo/bundle.py | 267 | if str(getattr(store, "db_path", "")) == ":memory:": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, getattr |
| copilot_sdk/demo/startup.py | 13 | def startup_lock(db_path: str) -> Iterator[None]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/demo/startup.py |
| copilot_sdk/demo/startup.py | 15 | if db_path == ":memory:": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/demo/startup.py |
| copilot_sdk/demo/startup.py | 18 | with file_lock(str(Path(db_path).resolve()) + ".startup.lock"): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).resolve, Path |
| copilot_sdk/evolution/variant_store.py | 201 | def __init__(self, db_path: str \| Path) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/evolution/variant_store.py |
| copilot_sdk/evolution/variant_store.py | 202 | self.db_path = str(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| copilot_sdk/evolution/variant_store.py | 205 | self.db_path, | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/graph/factory.py | 52 | db_path: str \| Path \| None, | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/factory.py | 56 | if db_path is not None: | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/factory.py | 57 | return db_path | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/factory.py | 117 | db_path: str \| Path \| None = None, | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/factory.py | 180 | db_path=db_path, | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/factory.py | 200 | db_path=db_path, | Factory/backend configuration variable; no DecisionStore creation |
| copilot_sdk/graph/sqlite_store.py | 372 | def _write_lock_key(db_path: str) -> str: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/graph/sqlite_store.py | 373 | if db_path == ":memory:": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/graph/sqlite_store.py | 374 | return f"memory:{id(db_path)}" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: id |
| copilot_sdk/graph/sqlite_store.py | 375 | return str(Path(db_path).expanduser().resolve()) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).expanduser, Path |
| copilot_sdk/graph/sqlite_store.py | 378 | def _write_lock_for(db_path: str) -> threading.RLock: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/graph/sqlite_store.py | 379 | key = _write_lock_key(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _write_lock_key |
| copilot_sdk/graph/sqlite_store.py | 396 | def __init__(self, db_path: str \| Path, domain: str = "graph", decision_id_prefix: str = "") -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/graph/sqlite_store.py | 397 | self.db_path = str(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| copilot_sdk/graph/sqlite_store.py | 401 | self._write_lock = _write_lock_for(self.db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _write_lock_for |
| copilot_sdk/graph/sqlite_store.py | 403 | self.db_path, | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/graph/sqlite_store.py | 413 | nullcontext() if self.db_path == ":memory:" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/graph/sqlite_store.py | 414 | else file_lock(str(Path(self.db_path).resolve()) + ".schema.lock") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(self.db_path).resolve, Path |
| copilot_sdk/graph/sqlite_store.py | 417 | if self.db_path != ":memory:": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/graph/sqlite_store.py |
| copilot_sdk/migrate/reconcile_archive.py | 28 | data_dir = Path(getattr(sqlite_store, "db_path", ".")).parent | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path, getattr |
| copilot_sdk/migrate/sqlite_to_age.py | 90 | def _read_verified_decisions(db_path: str, domain: str \| None = None) -> list[dict[str, Any]]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 99 | with sqlite3.connect(db_path) as conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/migrate/sqlite_to_age.py | 104 | def _read_outcomes(db_path: str) -> dict[str, dict[str, Any]]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 106 | with sqlite3.connect(db_path) as conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/migrate/sqlite_to_age.py | 175 | db_path: str, domain: str, *, all_decisions: bool = False | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 179 | with sqlite3.connect(db_path) as conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/migrate/sqlite_to_age.py | 183 | raise ValueError(f"decisions table missing in {db_path}") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: ValueError |
| copilot_sdk/migrate/sqlite_to_age.py | 754 | def _sqlite_level1_summary(db_path: str, domain: str) -> dict[str, Any]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 755 | with sqlite3.connect(db_path) as conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/migrate/sqlite_to_age.py | 779 | db_path: str, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 785 | sqlite_summary = _sqlite_level1_summary(db_path, domain) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _sqlite_level1_summary |
| copilot_sdk/migrate/sqlite_to_age.py | 796 | db_path: str, conn: psycopg.Connection, graph_name: str, domain: str | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 799 | with sqlite3.connect(db_path) as source_conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/migrate/sqlite_to_age.py | 904 | db_path: str, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/migrate/sqlite_to_age.py |
| copilot_sdk/migrate/sqlite_to_age.py | 911 | decisions = _read_verified_decisions(db_path, domain) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_verified_decisions |
| copilot_sdk/outbox/cli.py | 22 | def _store_for(domain: str, db_path: str \| None) -> OutboxStore: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/cli.py |
| copilot_sdk/outbox/cli.py | 23 | return OutboxStore(db_path or _default_db_path(domain)) | Constructor: OutboxStore; separate service or retained legacy fixture |
| copilot_sdk/outbox/cli.py | 26 | def status_command(domain: str, db_path: str \| None = None) -> dict[str, int \| str]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/cli.py |
| copilot_sdk/outbox/cli.py | 29 | store = _store_for(domain, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store_for |
| copilot_sdk/outbox/cli.py | 41 | def process_command(domain: str, db_path: str \| None = None) -> dict[str, int \| str]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/cli.py |
| copilot_sdk/outbox/cli.py | 44 | store = _store_for(domain, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store_for |
| copilot_sdk/outbox/cli.py | 64 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/cli.py |
| copilot_sdk/outbox/cli.py | 68 | store = _store_for(domain, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store_for |
| copilot_sdk/outbox/cli.py | 79 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/cli.py |
| copilot_sdk/outbox/cli.py | 83 | store = _store_for(domain, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _store_for |
| copilot_sdk/outbox/cli.py | 126 | result = status_command(args.domain, args.db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: status_command |
| copilot_sdk/outbox/cli.py | 128 | result = process_command(args.domain, args.db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: process_command |
| copilot_sdk/outbox/cli.py | 130 | result = replay_command(args.domain, args.from_offset, args.db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: replay_command |
| copilot_sdk/outbox/cli.py | 132 | result = dead_letters_command(args.domain, args.db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: dead_letters_command |
| copilot_sdk/outbox/store.py | 18 | def __init__(self, db_path: str \| Path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outbox/store.py |
| copilot_sdk/outbox/store.py | 19 | self.db_path = Path(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path |
| copilot_sdk/outbox/store.py | 20 | self.db_path.parent.mkdir(parents=True, exist_ok=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: self.db_path.parent.mkdir |
| copilot_sdk/outbox/store.py | 22 | self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/outbox/worker.py | 44 | with file_lock(str(self._store.db_path.resolve()) + ".dispatch.lock"): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, self._store.db_path.resolve |
| copilot_sdk/outbox/worker.py | 85 | with file_lock(str(self._store.db_path.resolve()) + ".dispatch.lock"): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, self._store.db_path.resolve |
| copilot_sdk/outcome/ledger.py | 17 | def __init__(self, db_path: str \| os.PathLike[str] = ":memory:") -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outcome/ledger.py |
| copilot_sdk/outcome/ledger.py | 18 | self.db_path = str(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| copilot_sdk/outcome/ledger.py | 19 | if self.db_path != ":memory:": | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/outcome/ledger.py |
| copilot_sdk/outcome/ledger.py | 20 | Path(self.db_path).parent.mkdir(parents=True, exist_ok=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(self.db_path).parent.mkdir, Path |
| copilot_sdk/outcome/ledger.py | 21 | self._connection = sqlite3.connect(self.db_path, check_same_thread=False) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/pilot/transfer.py | 49 | def __init__(self, db_path: str = ":memory:") -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/pilot/transfer.py |
| copilot_sdk/pilot/transfer.py | 50 | self._connection = sqlite3.connect(db_path, check_same_thread=False) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/pilot/transfer.py | 253 | db_path: str = ":memory:", | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/pilot/transfer.py |
| copilot_sdk/pilot/transfer.py | 262 | self.store = store or MeasuredTransferStore(db_path) | Constructor: MeasuredTransferStore; separate service or retained legacy fixture |
| copilot_sdk/promotion/core.py | 114 | def __init__(self, db_path: str = ":memory:", *, profile: str \| None = None) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: copilot_sdk/promotion/core.py |
| copilot_sdk/promotion/core.py | 117 | self._connection = sqlite3.connect(db_path, check_same_thread=False) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/scoring/persistence_outbox.py | 43 | def __init__(self, domain: str, db_path: Path \| None = None) -> None: | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 48 | self.db_path = Path( | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 49 | db_path | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 54 | self.db_path.parent.mkdir(parents=True, exist_ok=True) | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 56 | self.db_path = ( | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 59 | self.db_path.parent.mkdir(parents=True, exist_ok=True) | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 60 | with file_lock(str(self.db_path.resolve()) + ".lock"), self._connection() as connection: | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 128 | connection = sqlite3.connect(self.db_path, timeout=30.0) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| copilot_sdk/scoring/persistence_outbox.py | 149 | with file_lock(str(self.db_path.resolve()) + ".lock"): | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 217 | with file_lock(str(self.db_path.resolve()) + ".lock"), self._connection() as connection: | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 244 | with file_lock(str(self.db_path.resolve()) + ".lock"): | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/persistence_outbox.py | 367 | with file_lock(str(self.db_path.resolve()) + ".lock"), self._connection() as connection: | Independent durable failed-artifact SQLite queue, intentionally retained pending queue redesign |
| copilot_sdk/scoring/scorer.py | 284 | db_path: Optional[str] = None, | Removed scorer API/local SQLite creation; memory now used for uninjected dev/test |
| copilot_sdk/scoring/scorer.py | 319 | if db_path is None: | Removed scorer API/local SQLite creation; memory now used for uninjected dev/test |
| copilot_sdk/scoring/scorer.py | 322 | db_path = str(data_dir / f"{domain}.db") | Removed scorer API/local SQLite creation; memory now used for uninjected dev/test |
| copilot_sdk/scoring/scorer.py | 325 | SQLiteGraphStore(db_path, domain=preset.name), | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| copilot_sdk/scoring/scorer.py | 2236 | def load(cls, path: str \| Path, db_path: Optional[str] = None) -> "CompoundingScorer": | Removed scorer API/local SQLite creation; memory now used for uninjected dev/test |
| copilot_sdk/scoring/scorer.py | 2238 | scorer = cls.from_preset(state["domain"], db_path=db_path) | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| examples/jm_reference/run.py | 78 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: examples/jm_reference/run.py |
| examples/jm_reference/run.py | 83 | temporary_db = db_path is None | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: examples/jm_reference/run.py |
| examples/jm_reference/run.py | 84 | if db_path is None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: examples/jm_reference/run.py |
| examples/jm_reference/run.py | 85 | db_path = str(Path(tempfile.mkdtemp(prefix=f"jm_{label}_")) / f"{label}.db") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: examples/jm_reference/run.py |
| examples/jm_reference/run.py | 89 | store = SQLiteGraphStore(db_path, domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| examples/jm_reference/run.py | 93 | outbox_path = str(Path(db_path).with_name(f"{label}_outbox.db")) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).with_name, Path |
| examples/jm_reference/run.py | 208 | Path(db_path).unlink(missing_ok=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: Path(db_path).unlink, Path |
| examples/trading_clone/run.py | 25 | db_path: str \| None = None, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: examples/trading_clone/run.py |
| examples/trading_clone/run.py | 30 | return _run_reference_experiment(label, gen_config, oracle_config, db_path, mode=mode) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _run_reference_experiment |
| experiments/vld/vld_rl_ctrl_fork_v1.py | 378 | CompoundingScorer.from_preset(preset_name, db_path=str(Path(tmp) / f"{copilot}.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| integrity/architecture_scan.py | 74 | ("copilot-sdk/copilot_sdk/backend/signal_store.py", "db = self._memory if self._memory is not None else sqlite3.connect(self.db_path, timeout=30)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 80 | ("copilot-sdk/copilot_sdk/outbox/store.py", "self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 81 | ("copilot-sdk/copilot_sdk/outcome/ledger.py", "self._connection = sqlite3.connect(self.db_path, check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 82 | ("copilot-sdk/copilot_sdk/pilot/transfer.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 83 | ("copilot-sdk/copilot_sdk/promotion/core.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 84 | ("copilot-sdk/copilot_sdk/scoring/persistence_outbox.py", "connection = sqlite3.connect(self.db_path, timeout=30.0)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 85 | # SQLite-to-AGE migration source reads (four db_path and two source connections). | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 86 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 87 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 88 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 89 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as conn:"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 90 | ("copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py", "with sqlite3.connect(db_path) as source_conn:"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 93 | ("copilot-sdk/apps/dataops/backend/app/dataops_governance.py", "self._db = sqlite3.connect(str(db_path), check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 100 | ("s2p-copilot/backend/app/services/proposal_service.py", "self._connection = sqlite3.connect(db_path, check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| integrity/architecture_scan.py | 102 | ("gen-ai-roi-demo-v4-v50/backend/app/services/authority_ladder.py", "self._audit = sqlite3.connect(self.db_path, check_same_thread=False)"), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: integrity/architecture_scan.py |
| scripts/age_pf_blockers.py | 60 | def get_sqlite_decision_ids(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/age_pf_blockers.py |
| scripts/age_pf_blockers.py | 63 | with sqlite3.connect(db_path) as sconn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| scripts/age_pf_blockers.py | 82 | print(f"    Error reading {db_path}: {e}") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: print |
| scripts/age_pf_blockers.py | 137 | db_path = find_sqlite(domain) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/age_pf_blockers.py |
| scripts/age_pf_blockers.py | 138 | if db_path is None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/age_pf_blockers.py |
| scripts/age_pf_blockers.py | 144 | print(f"\n  {domain}: {db_path}") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: print |
| scripts/age_pf_blockers.py | 145 | sqlite_ids = get_sqlite_decision_ids(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: get_sqlite_decision_ids |
| scripts/age_v35_review_checks.py | 48 | def db_path(domain: str) -> Path: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/age_v35_review_checks.py |
| scripts/age_v35_review_checks.py | 75 | path = db_path(domain) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path |
| scripts/demo_warm_start.py | 64 | db_path=str(db_dir / f"{SOURCE_COPILOT}.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/demo_warm_start.py | 68 | db_path=str(db_dir / f"{TARGET_COPILOT}.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/discovery_demo.py | 25 | trading = CompoundingScorer.from_preset("trading", db_path=":memory:") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/discovery_demo.py | 26 | s2p = CompoundingScorer.from_preset("s2p", db_path=":memory:") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/evolve_demo.py | 47 | db_path = str(Path(tmp) / f"{domain}.db") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/evolve_demo.py |
| scripts/evolve_demo.py | 50 | db_path=db_path, | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/k_learning_curve_cross_copilot.py | 341 | CompoundingScorer.from_preset(preset_name, db_path=str(Path(tmp) / f"{copilot}.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/k_learning_curve_experiment.py | 306 | db_path=str(Path(tmp) / "dataops.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/k_learning_curve_extended.py | 304 | CompoundingScorer.from_preset("dataops", db_path=str(Path(tmp) / "dataops.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| scripts/phase_config.py | 33 | "trading": {"prefix": "TRD-", "db_path": SDK_ROOT / "apps/trading/backend/data/trading.db", "port": 8010, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/phase_config.py |
| scripts/phase_config.py | 34 | "purchasing": {"prefix": "PUR-", "db_path": SDK_ROOT / "apps/purchasing/backend/data/purchasing.db", "port": 8020, "score_path": "/api/score", "learn_path": "/api/learn", "score_pa | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/phase_config.py |
| scripts/phase_config.py | 35 | "dataops": {"prefix": "DOPS-", "db_path": SDK_ROOT / "apps/dataops/backend/data/dataops.db", "port": 8030, "score_path": "/api/score", "learn_path": "/api/learn", "score_payload_fn | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/phase_config.py |
| scripts/phase_config.py | 38 | "db_path": os.path.abspath( | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/phase_config.py |
| scripts/phase_config.py | 71 | db_path=str(Path(configured_path) if configured_path else cfg["db_path"]), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: cfg.update, str |
| scripts/phase_config.py | 75 | cfg["checkpoint_path"] = str(Path(cfg["db_path"]).parent / "phase_cycle_checkpoint.json") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, Path |
| scripts/phase_config.py | 76 | cfg["outbox_path"] = str(Path(cfg["db_path"]).parent / f"{selected}_dual_write_outbox.db") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str, Path |
| scripts/phase_dual_write_e2e.py | 13 | store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); baseline=store.count_decisions(cfg["domain"]); store.close() | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| scripts/phase_dual_write_e2e.py | 23 | store=SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]); delta=store.count_decisions(cfg["domain"])-baseline; store.close() | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| scripts/phase_read_diff.py | 12 | primary = SQLiteGraphStore(cfg["db_path"], domain=cfg["domain"], decision_id_prefix=cfg["prefix"]) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| scripts/phase_verify.py | 14 | with sqlite3.connect(cfg["db_path"]) as source: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| scripts/preseed_demo_fixtures.py | 125 | db_path=root / "apps/purchasing/backend/data/purchasing.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| scripts/preseed_demo_fixtures.py | 136 | store = create_graph_store(domain="dataops", db_path=root / "apps/dataops/backend/data/dataops.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| scripts/preseed_demo_fixtures.py | 184 | store = create_graph_store(domain="purchasing", db_path=root / "apps/purchasing/backend/data/purchasing.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| scripts/refresh_demo_centroid_checkpoints.py | 31 | db_path: Path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/refresh_demo_centroid_checkpoints.py |
| scripts/refresh_demo_centroid_checkpoints.py | 40 | db_path=ROOT / "apps" / "purchasing" / "backend" / "data" / "purchasing.db", | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: DomainConfig |
| scripts/refresh_demo_centroid_checkpoints.py | 51 | db_path=ROOT / "apps" / "trading" / "backend" / "data" / "trading.db", | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: DomainConfig |
| scripts/refresh_demo_centroid_checkpoints.py | 207 | db_path: Path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/refresh_demo_centroid_checkpoints.py |
| scripts/refresh_demo_centroid_checkpoints.py | 216 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| scripts/refresh_demo_centroid_checkpoints.py | 226 | "db_path": str(db_path), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| scripts/refresh_demo_centroid_checkpoints.py | 239 | "db_path": str(db_path), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: str |
| scripts/refresh_demo_centroid_checkpoints.py | 303 | db_path=cfg.db_path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: refresh_database_from_bundle |
| scripts/sqlite_copilot_audit.py | 69 | def audit_sqlite(domain, db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/sqlite_copilot_audit.py |
| scripts/sqlite_copilot_audit.py | 71 | print(f"\n  path: {db_path}") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: print |
| scripts/sqlite_copilot_audit.py | 72 | print(f"  size: {os.path.getsize(db_path) / 1024:.0f} KB") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: print, os.path.getsize |
| scripts/sqlite_copilot_audit.py | 74 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| scripts/sqlite_copilot_audit.py | 264 | db_path = find_db("s2p") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/sqlite_copilot_audit.py |
| scripts/sqlite_copilot_audit.py | 265 | if db_path: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/sqlite_copilot_audit.py |
| scripts/sqlite_copilot_audit.py | 267 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| scripts/sqlite_copilot_audit.py | 341 | db_path = find_db(domain) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/sqlite_copilot_audit.py |
| scripts/sqlite_copilot_audit.py | 342 | if db_path is None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/sqlite_copilot_audit.py |
| scripts/sqlite_copilot_audit.py | 350 | stats = audit_sqlite(domain, db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: audit_sqlite |
| scripts/transfer_demo.py | 28 | db_path = Path(tempfile.mkdtemp()) / "s2p-transfer-demo.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: scripts/transfer_demo.py |
| scripts/transfer_demo.py | 29 | scorer = CompoundingScorer.from_preset("s2p", db_path=str(db_path)) | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/backend/test_diagnostics_models.py | 46 | db_path = "outbox.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/backend/test_diagnostics_models.py |
| tests/backend/test_diagnostics_models.py | 84 | db_path = "outbox.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/backend/test_diagnostics_models.py |
| tests/backend/test_score_responsiveness.py | 20 | scorer = CompoundingScorer.from_preset(domain, db_path=str(tmp_path / "score.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/backend/test_scorer_proxy.py | 36 | def _graph_store(db_path: str \| Path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/backend/test_scorer_proxy.py |
| tests/backend/test_scorer_proxy.py | 37 | store = SQLiteGraphStore(str(db_path), domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/backend/test_scoring_router.py | 318 | def __init__(self, db_path: Path) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/backend/test_scoring_router.py |
| tests/backend/test_scoring_router.py | 320 | self.graph_store = SQLiteGraphStore(db_path, domain="test") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/evolution/test_evolve_integration.py | 14 | db_path=str(tmp_path / f"{domain}.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/evolution/test_integration.py | 51 | scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/graph/test_decision_metadata.py | 47 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_decision_metadata.py |
| tests/graph/test_decision_metadata.py | 48 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_decision_metadata.py | 60 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_decision_metadata.py |
| tests/graph/test_decision_metadata.py | 61 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_decision_metadata.py | 71 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_decision_metadata.py |
| tests/graph/test_decision_metadata.py | 72 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_decision_metadata.py | 78 | reopened = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_decision_metadata.py | 88 | db_path=str(tmp_path / "s2p.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/graph/test_graph_store_evolution.py | 10 | def _sqlite_events(db_path): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_graph_store_evolution.py |
| tests/graph/test_graph_store_evolution.py | 11 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_graph_store_evolution.py | 67 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_graph_store_evolution.py |
| tests/graph/test_graph_store_evolution.py | 68 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_graph_store_evolution.py | 78 | events = _sqlite_events(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _sqlite_events |
| tests/graph/test_graph_store_evolution.py | 88 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_graph_store_evolution.py |
| tests/graph/test_graph_store_evolution.py | 89 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_graph_store_evolution.py | 93 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_graph_store_evolution.py | 113 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_graph_store_evolution.py |
| tests/graph/test_graph_store_evolution.py | 114 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_graph_store_evolution.py | 118 | events = _sqlite_events(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _sqlite_events |
| tests/graph/test_graphstore_factory.py | 30 | db_path = tmp_path / "explicit.db" | Factory/backend configuration variable; no DecisionStore creation |
| tests/graph/test_graphstore_factory.py | 31 | store = create_graph_store(profile="test", backend="sqlite", domain="trading", db_path=db_path, env={}) | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/graph/test_graphstore_factory.py | 34 | assert store.db_path == str(db_path) | Factory/backend configuration variable; no DecisionStore creation |
| tests/graph/test_graphstore_factory.py | 47 | assert store.db_path == str(tmp_path / "purchasing.db") | Factory/backend configuration variable; no DecisionStore creation |
| tests/graph/test_graphstore_factory.py | 226 | store = create_graph_store(profile="test", backend="sqlite", domain="test", db_path=":memory:") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/graph/test_protocol_v2_conformance.py | 94 | db_path: Path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_protocol_v2_conformance.py |
| tests/graph/test_protocol_v2_conformance.py | 102 | with sqlite3.connect(db_path) as conn: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_protocol_v2_conformance.py | 1002 | db_path = tmp_path / "legacy.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_protocol_v2_conformance.py |
| tests/graph/test_protocol_v2_conformance.py | 1003 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_protocol_v2_conformance.py | 1040 | store = SQLiteGraphStore(db_path, domain="test") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_protocol_v2_conformance.py | 2602 | db_path = tmp_path / "legacy-links.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_protocol_v2_conformance.py |
| tests/graph/test_protocol_v2_conformance.py | 2603 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_protocol_v2_conformance.py | 2640 | store = SQLiteGraphStore(db_path, domain="test") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_protocol_v2_conformance.py | 3052 | scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.sqlite"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/graph/test_sqlite_store.py | 29 | def _columns(db_path, table: str) -> set[str]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 30 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_sqlite_store.py | 99 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 100 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_sqlite_store.py | 255 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 256 | SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_sqlite_store.py | 258 | assert "domain" in _columns(db_path, "decisions_archive") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _columns |
| tests/graph/test_sqlite_store.py | 327 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 328 | alpha = SQLiteGraphStore(db_path, domain="alpha") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_sqlite_store.py | 329 | beta = SQLiteGraphStore(db_path, domain="beta") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_sqlite_store.py | 345 | db_path = tmp_path / "old.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 346 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/graph/test_sqlite_store.py | 391 | store = SQLiteGraphStore(db_path, domain="legacy") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/graph/test_sqlite_store.py | 393 | assert "domain" in _columns(db_path, "decisions") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _columns |
| tests/graph/test_sqlite_store.py | 394 | assert "domain" in _columns(db_path, "outcomes") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _columns |
| tests/graph/test_sqlite_store.py | 395 | assert "domain" in _columns(db_path, "centroid_checkpoints") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _columns |
| tests/graph/test_sqlite_store.py | 396 | assert {"decision_time_start", "decision_time_end", "checkpoint_time"} <= _columns(db_path, "centroid_checkpoints") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _columns |
| tests/graph/test_sqlite_store.py | 423 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/graph/test_sqlite_store.py |
| tests/graph/test_sqlite_store.py | 424 | stores = [SQLiteGraphStore(db_path) for _ in range(3)] | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/scoring/test_conservation.py | 115 | scorer._outbox = PersistenceOutbox("mock", db_path=tmp_path / "outbox.db") | Constructor: PersistenceOutbox; separate service or retained legacy fixture |
| tests/scoring/test_dataops_preset.py | 77 | db_path = tmp_path / "dataops.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_dataops_preset.py |
| tests/scoring/test_dataops_preset.py | 79 | scorer = CompoundingScorer.from_preset("dataops", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_dataops_preset.py | 247 | db_path = tmp_path / "dataops_smoke.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_dataops_preset.py |
| tests/scoring/test_dataops_preset.py | 248 | scorer = CompoundingScorer.from_preset("dataops", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_persistence_outbox.py | 136 | with sqlite3.connect(outbox.db_path) as connection: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/scoring/test_presets.py | 53 | scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_presets.py | 61 | scorer = CompoundingScorer.from_preset("s2p", db_path=str(tmp_path / "s2p.db"), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_purchasing_preset.py | 105 | db_path = tmp_path / "purchasing.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_purchasing_preset.py |
| tests/scoring/test_purchasing_preset.py | 107 | scorer = CompoundingScorer.from_preset("purchasing", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_purchasing_preset.py | 311 | db_path = tmp_path / "purchasing_smoke.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_purchasing_preset.py |
| tests/scoring/test_purchasing_preset.py | 312 | scorer = CompoundingScorer.from_preset("purchasing", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_purchasing_preset.py | 324 | if db_path.exists(): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| tests/scoring/test_purchasing_preset.py | 325 | os.remove(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: os.remove |
| tests/scoring/test_scorer.py | 80 | db_path=str(tmp_path / "scorer.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_scorer.py | 95 | db_path=str(tmp_path / "scorer.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_scorer.py | 110 | db_path=str(tmp_path / "scorer.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_scorer.py | 128 | db_path=str(tmp_path / "scorer.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_scorer.py | 872 | restored = CompoundingScorer.load(export_path, db_path=str(tmp_path / "restored.sqlite")) | Scorer reload forwarded db_path to from_preset; now explicit graph_store/profile |
| tests/scoring/test_storage.py | 227 | db_path = tmp_path / "old.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_storage.py |
| tests/scoring/test_storage.py | 228 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/scoring/test_storage.py | 264 | migrated = SQLiteGraphStore(db_path, domain="mock") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/scoring/test_storage.py | 286 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_storage.py |
| tests/scoring/test_storage.py | 287 | store = SQLiteGraphStore(db_path, domain="mock") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/scoring/test_trading_preset.py | 103 | db_path = tmp_path / "trading.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_trading_preset.py |
| tests/scoring/test_trading_preset.py | 105 | scorer = CompoundingScorer.from_preset("trading", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_trading_preset.py | 252 | db_path = tmp_path / "trading_smoke.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/scoring/test_trading_preset.py |
| tests/scoring/test_trading_preset.py | 253 | scorer = CompoundingScorer.from_preset("trading", db_path=str(db_path), profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/scoring/test_trading_preset.py | 265 | if db_path.exists(): | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: db_path.exists |
| tests/scoring/test_trading_preset.py | 266 | os.remove(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: os.remove |
| tests/test_archetype_router.py | 87 | scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), graph_store=store, profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_bitemporal_scorer.py | 193 | db_path=str(tmp_path / "s2p.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_bitemporal_scorer.py | 219 | db_path=str(tmp_path / "s2p.sqlite"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_category_mappings.py | 85 | db_path=str(tmp_path / "trading.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_category_mappings.py | 133 | db_path=str(tmp_path / "trading.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_chain_transfer.py | 188 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 200 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 215 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 226 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 239 | client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 251 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 266 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_chain_transfer.py | 289 | with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as client: | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_conservation_formula.py | 54 | db_path=str(tmp_path / f"{domain}.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_evolution_telemetry_age.py | 96 | test_app = app_module.create_app(db_path=":memory:", demo_bundle_path=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_evolution_telemetry_age.py |
| tests/test_experiment_age_integration.py | 85 | app = module.create_app(db_path=":memory:", demo_bundle_path=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_experiment_age_integration.py |
| tests/test_factory_dual_write.py | 31 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 45 | create_graph_store(profile="test", backend="dual_write", domain="trading", db_path=tmp_path / "trading.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 49 | store = create_graph_store(profile="test", backend="sqlite", domain="trading", db_path=tmp_path / "trading.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 66 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 81 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 94 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 112 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 125 | db_path=tmp_path / f"{domain}.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_factory_dual_write.py | 165 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_factory.py | 20 | backend="sqlite", domain="test", db_path=tmp_path / "test.db", profile="test" | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_factory.py | 33 | backend="dual_write", domain="trading", db_path=tmp_path / "trading.db" | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_factory.py | 47 | create_graph_store(domain="trading", db_path=tmp_path / "trading.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_factory.py | 55 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_production_boundary.py | 39 | create_graph_store(backend=backend, domain="trading", db_path=path, profile="production") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graph_production_boundary.py | 46 | store = create_graph_store(backend=backend, domain="trading", profile=profile, db_path=tmp_path / "test.db") | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_graphstore_consolidation.py | 90 | def _sqlite_events(db_path: Path) -> list[dict]: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_graphstore_consolidation.py |
| tests/test_graphstore_consolidation.py | 91 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_graphstore_consolidation.py | 267 | db_path = tmp_path / "graph.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_graphstore_consolidation.py |
| tests/test_graphstore_consolidation.py | 268 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/test_graphstore_consolidation.py | 275 | events = _sqlite_events(db_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _sqlite_events |
| tests/test_l5_dk_welford_storage.py | 109 | db_path = tmp_path / "old-dk.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_l5_dk_welford_storage.py |
| tests/test_l5_dk_welford_storage.py | 110 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_l5_dk_welford_storage.py | 137 | store = SQLiteGraphStore(db_path) | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/test_learn_context.py | 164 | db_path = tmp_path / "legacy.sqlite" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_learn_context.py |
| tests/test_learn_context.py | 165 | connection = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_learn_context.py | 195 | store = SQLiteGraphStore(db_path, domain="mock") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/test_legacy_signal_filter.py | 129 | db_path=tmp_path / "factory.db", dsn="postgres://test", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_measurement_state.py | 15 | return CompoundingScorer.from_preset("trading", db_path=":memory:", profile="test") | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_outbox_worker.py | 318 | db_path = tmp_path / "cli_status.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_outbox_worker.py |
| tests/test_outbox_worker.py | 319 | store = OutboxStore(db_path) | Constructor: OutboxStore; separate service or retained legacy fixture |
| tests/test_outbox_worker.py | 327 | result = status_command("trading", str(db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: status_command, str |
| tests/test_outbox_worker.py | 338 | db_path = tmp_path / "cli_process.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_outbox_worker.py |
| tests/test_outbox_worker.py | 339 | store = OutboxStore(db_path) | Constructor: OutboxStore; separate service or retained legacy fixture |
| tests/test_outbox_worker.py | 346 | result = process_command("trading", str(db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: process_command, str |
| tests/test_plateau_preset_config.py | 93 | db_path=str(tmp_path / "custom.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_plateau_preset_config.py | 125 | db_path=str(tmp_path / "legacy.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_platform_router.py | 33 | def _graph_store(db_path: str \| Path) -> SQLiteGraphStore: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_platform_router.py |
| tests/test_platform_router.py | 34 | store = SQLiteGraphStore(str(db_path), domain="trading") | Direct SQLiteGraphStore constructor; retained durable/schema consumer (see NOT FIXED) |
| tests/test_polarity.py | 104 | "purchasing", db_path=str(tmp_path / "pol_test.db"), profile="test" | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_rule38_factory_compliance.py | 31 | db_path=tmp_path / f"{domain}.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_rule38_factory_compliance.py | 44 | db_path=tmp_path / "trading.db", | Graph factory: path selects SQLite/dual-write primary only; AGE/memory select from configuration; retained |
| tests/test_scorer_construction.py | 20 | db_path=str(tmp_path / "trading.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_sqlite_to_age_migration.py | 103 | db_path = tmp_path / "source.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 104 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 134 | return db_path | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 137 | def _add_archive_rows(db_path: Path, rows: list[tuple]) -> None: | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 138 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 166 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 167 | decisions = _read_verified_decisions(str(db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_verified_decisions, str |
| tests/test_sqlite_to_age_migration.py | 173 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 174 | decisions = _read_verified_decisions(str(db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_verified_decisions, str |
| tests/test_sqlite_to_age_migration.py | 179 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 180 | outcomes = _read_outcomes(str(db_path)) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_outcomes, str |
| tests/test_sqlite_to_age_migration.py | 185 | db_path = _make_db(tmp_path, with_outcomes=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 186 | assert _read_outcomes(str(db_path)) == {} | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_outcomes, str |
| tests/test_sqlite_to_age_migration.py | 237 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 243 | result = run_migration("trading", str(db_path), "dsn", "graph", dry_run=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 267 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 275 | result = run_migration("trading", str(db_path), "dsn", conn.graph, verify=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 284 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 286 | records = _read_migration_records(str(db_path), "trading") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 288 | assert _verify_level1(str(db_path), conn, conn.graph, "trading")["passed"] is True | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level1, str |
| tests/test_sqlite_to_age_migration.py | 293 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 295 | records = _read_migration_records(str(db_path), "trading") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 298 | assert _verify_level1(str(db_path), conn, conn.graph, "trading")["passed"] is False | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level1, str |
| tests/test_sqlite_to_age_migration.py | 304 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 320 | result = run_migration("trading", str(db_path), "dsn", conn.graph, verify=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 329 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 331 | records = _read_migration_records(str(db_path), "trading") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 333 | assert _verify_level2(str(db_path), conn, conn.graph, "trading")["passed"] is True | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level2, str |
| tests/test_sqlite_to_age_migration.py | 338 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 340 | assert _write_batch(conn, _read_migration_records(str(db_path), "trading"), conn.graph)["written"] == 4 | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 342 | assert _verify_level2(str(db_path), conn, conn.graph, "trading")["passed"] is True | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level2, str |
| tests/test_sqlite_to_age_migration.py | 347 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 349 | records = _read_migration_records(str(db_path), "trading") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 352 | assert _verify_level2(str(db_path), conn, conn.graph, "trading")["passed"] is False | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level2, str |
| tests/test_sqlite_to_age_migration.py | 358 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 377 | result = run_migration("trading", str(db_path), "dsn", conn.graph, verify=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 387 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 424 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 443 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 468 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 478 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 495 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 505 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 538 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 550 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 583 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 595 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 628 | result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 643 | db_path = tmp_path / "empty.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 644 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 649 | run_migration("trading", str(db_path), "dsn", "graph", dry_run=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 705 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 706 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 724 | return _read_migration_records(str(db_path), "trading", all_decisions=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 754 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 755 | assert all(record["decision"]["status"] != "pending" for record in _read_migration_records(str(db_path), "trading")) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 756 | pending = next(record for record in _read_migration_records(str(db_path), "trading", all_decisions=True) if record["decision"]["decision_id"] == "d3") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 789 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 790 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 796 | record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 838 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 839 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 846 | result = run_migration("trading", str(db_path), "dsn", age.graph, verify=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 855 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 856 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 867 | record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 881 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 882 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 893 | record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 907 | db_path = tmp_path / "compound.db" | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 908 | conn = sqlite3.connect(db_path) | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 926 | result = _verify_level2(str(db_path), age, age.graph, "trading") | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _verify_level2, str |
| tests/test_sqlite_to_age_migration.py | 996 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 998 | db_path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1005 | active_records = _read_migration_records(str(db_path), "trading", all_decisions=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 1006 | with sqlite3.connect(db_path) as source: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 1019 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1021 | db_path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1028 | with sqlite3.connect(db_path) as source: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 1045 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1046 | _add_archive_rows(db_path, [_archive_row(1, "a1"), _archive_row(2, "a2", actual_action=None, is_correct=None)]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1048 | active = _read_migration_records(str(db_path), "trading", all_decisions=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _read_migration_records, str |
| tests/test_sqlite_to_age_migration.py | 1049 | with sqlite3.connect(db_path) as source: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 1057 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1059 | db_path, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1066 | with sqlite3.connect(db_path) as source: | Raw SQLite connection (not DecisionStore); see raw-SQL inventory |
| tests/test_sqlite_to_age_migration.py | 1076 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1077 | _add_archive_rows(db_path, [_archive_row(1, "broken", actual_action="buy", is_correct=None)]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1081 | result = run_migration("trading", str(db_path), "dsn", age.graph, include_archived=True, verify=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 1089 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1090 | _add_archive_rows(db_path, [_archive_row(1, "d1")]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1096 | result = run_migration("trading", str(db_path), "dsn", "graph", include_archived=True, verify=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 1104 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1105 | _add_archive_rows(db_path, [_archive_row(1, "a1")]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1119 | "trading", str(db_path), "dsn", age.graph, all_decisions=True, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 1128 | "trading", str(db_path), "dsn", age.graph, all_decisions=True, | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 1138 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_sqlite_to_age_migration.py |
| tests/test_sqlite_to_age_migration.py | 1139 | _add_archive_rows(db_path, [_archive_row(1, "a1")]) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: _add_archive_rows |
| tests/test_sqlite_to_age_migration.py | 1142 | first = run_migration("trading", str(db_path), "dsn", conn.graph, all_decisions=True, include_archived=True, verify=False) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_sqlite_to_age_migration.py | 1143 | second = run_migration("trading", str(db_path), "dsn", conn.graph, all_decisions=True, include_archived=True, verify=False, resume=True) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: run_migration, str |
| tests/test_trading_domain_config.py | 209 | "trading", db_path=str(tmp_path / "p48_test.db"), profile="test" | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_trading_evolver_wiring_age.py | 40 | return create_app(db_path=":memory:", demo_bundle_path=False) | App configuration path, not a backend itself; graph factory/config and separate app services consume it |
| tests/test_verify_state.py | 304 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_verify_state.py |
| tests/test_verify_state.py | 317 | str(db_path), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: sqlite_to_age.run_migration, str |
| tests/test_verify_state.py | 333 | db_path = _make_db(tmp_path) | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: tests/test_verify_state.py |
| tests/test_verify_state.py | 353 | str(db_path), | Path definition/helper/CLI assertion; does not itself instantiate a backend. Context: sqlite_to_age.run_migration, str |
| tests/test_warm_start_demo.py | 26 | db_path=str(tmp_path / "trading.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/test_weekly_report.py | 38 | db_path=str(tmp_path / "weekly.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/transfer/test_scorer_warm_start.py | 13 | db_path=str(tmp_path / "s2p.db"), | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |
| tests/vld_validation_report.py | 252 | scorer = CompoundingScorer.from_preset(domain, db_path=":memory:", graph_store=store, | CompoundingScorer.from_preset: SQLite in development, memory in test; db_path removed from this call |

### Appendix E — Remaining backend references after edits

| File | Line | Usage | Reason/follow-up |
| --- | --- | --- | --- |
| apps/dataops/backend/tests/conftest.py | 11 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/conftest.py | 79 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/conftest.py | 94 | type annotation | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/dataops/backend/tests/test_dataops_backend.py | 228 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 231 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1529 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1531 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1539 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1541 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1549 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_backend.py | 1551 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 19 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 160 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_fixture_closure.py | 170 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 438 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/dataops/backend/tests/test_dataops_graph_status.py | 440 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 11 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 98 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest.py | 104 | type annotation | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest_helpers.py | 7 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/conftest_helpers.py | 21 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 316 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 319 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 805 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 808 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 827 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 830 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 978 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 984 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1007 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1009 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1017 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1019 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1027 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_backend.py | 1029 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 421 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/purchasing/backend/tests/test_purchasing_graph_status.py | 423 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/regime_experiment/experiment.py | 22 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/regime_experiment/experiment.py | 120 | type annotation | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/regime_experiment/experiment.py | 121 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/s2p_differentiation/engine.py | 20 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/s2p_differentiation/engine.py | 179 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| apps/trading/backend/tests/conftest_helpers.py | 10 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/conftest_helpers.py | 35 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/conftest_helpers.py | 114 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_bundle_wiring.py | 10 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 27 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 34 | type annotation | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_bundle_wiring.py | 35 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| apps/trading/backend/tests/test_regime_replay.py | 9 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_regime_replay.py | 13 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_regime_replay.py | 27 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 433 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 436 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 801 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 804 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 823 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 826 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 891 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 897 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 920 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 922 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 930 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 932 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 940 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_backend.py | 942 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 17 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 228 | test assertion/type check | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 507 | import | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| apps/trading/backend/tests/test_trading_graph_status.py | 509 | instantiation/reference | App fixture/health/startup tests retain database seeding or backend assertions; coordinate with factory/config cutover. |
| copilot_sdk/backend/health_builder.py | 12 | import | Health must identify the still-supported legacy backend truthfully until removal. |
| copilot_sdk/backend/health_builder.py | 35 | test assertion/type check | Health must identify the still-supported legacy backend truthfully until removal. |
| copilot_sdk/demo/bundle.py | 14 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 156 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 159 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 165 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 166 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/demo/bundle.py | 168 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| copilot_sdk/graph/__init__.py | 12 | import | Public export retained while existing durable tools still import it. |
| copilot_sdk/graph/__init__.py | 27 | reference/string/comment | Public export retained while existing durable tools still import it. |
| copilot_sdk/graph/dual_write_store.py | 19 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| copilot_sdk/graph/dual_write_store.py | 61 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| copilot_sdk/graph/factory.py | 15 | import | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/factory.py | 191 | instantiation/reference | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/factory.py | 204 | instantiation/reference | Explicit SQLite and dual-write configurations still have durable consumers; require coordinated configuration and data cutover. |
| copilot_sdk/graph/sqlite_store.py | 393 | class definition (local shim, not legacy SDK) | Backend still required by durable consumers; deleting it now breaks imports and recovery tools. |
| copilot_sdk/graph/sqlite_store.py | 429 | reference/string/comment | Backend still required by durable consumers; deleting it now breaks imports and recovery tools. |
| copilot_sdk/migrate/__main__.py | 91 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 94 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 97 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/__main__.py | 110 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 20 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 25 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 28 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 51 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| copilot_sdk/migrate/reconcile_archive.py | 124 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| examples/build_your_own/engine.py | 3 | reference/string/comment | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/build_your_own/engine.py | 19 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/build_your_own/engine.py | 89 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 8 | reference/string/comment | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 24 | import | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 70 | type annotation | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| examples/jm_reference/run.py | 89 | instantiation/reference | Full scoring experiment backend and database artifacts retained; require experiment/retained-artifact parity review. This pass ports K-only experiment stores, not these independent scoring baselines. |
| integrity/architecture_scan.py | 78 | reference/string/comment | Existing backend selection/compatibility consumer retained for coordinated durable SQLite cutover. |
| scripts/phase3_dual_parity_v2.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_parity_v2.py | 27 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 46 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 49 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v2.py | 102 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 13 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 52 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v4.py | 102 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 10 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 49 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_dual_write_e2e_v5.py | 96 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v2.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v2.py | 22 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v4.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v4.py | 22 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v5.py | 5 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase3_read_diff_v5.py | 23 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 6 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 13 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_dual_write_e2e.py | 23 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_read_diff.py | 5 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/phase_read_diff.py | 12 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 18 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 30 | type annotation | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 32 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 72 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 88 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/shadow_live_test.py | 89 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| scripts/sqlite_copilot_audit.py | 8 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 190 | reference/string/comment | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 209 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 216 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| scripts/sqlite_copilot_audit.py | 220 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/backend/test_coalesced_reads.py | 15 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 53 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 57 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_coalesced_reads.py | 67 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_graph_access_health.py | 13 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_graph_access_health.py | 20 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scorer_proxy.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scorer_proxy.py | 37 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scoring_router.py | 21 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/backend/test_scoring_router.py | 320 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/demo/test_bundle.py | 5 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/demo/test_bundle.py | 85 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/demo/test_bundle.py | 184 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/evolution/test_evolution_store.py | 4 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_evolution_store.py | 35 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_ledger_domain.py | 63 | reference/string/comment | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/evolution/test_selection_snapshot.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_selection_snapshot.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_selection_snapshot.py | 13 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 25 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 38 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 52 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 66 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 79 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 91 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 108 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_sqlite_variant_store.py | 116 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 11 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/evolution/test_summary_snapshot.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_correctness_conformance.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_correctness_conformance.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_decision_metadata.py | 3 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 48 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 61 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 72 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_decision_metadata.py | 78 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_domain_required_conformance.py | 8 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_domain_required_conformance.py | 15 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_evolution_event_links.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 11 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 20 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_evolution_event_links.py | 63 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 68 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 89 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 104 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graph_store_evolution.py | 123 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 11 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 23 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 33 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 46 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_graphstore_factory.py | 227 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 16 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_link_domain_conformance.py | 43 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_no_amend_policy.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_no_amend_policy.py | 24 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 11 | reference/string/comment | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 21 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol.py | 173 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_protocol_v2_conformance.py | 16 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 34 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 35 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 67 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 399 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 421 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 444 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 447 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 456 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 462 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 463 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 466 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 471 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 498 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 501 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 503 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 511 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 512 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 578 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 581 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 583 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 584 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 588 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 621 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 624 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 626 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 627 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 631 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 664 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 667 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 668 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 677 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 680 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 682 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 686 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 693 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 697 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 810 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 813 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 814 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 816 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 820 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 824 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 835 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 836 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 863 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 866 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 867 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 868 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 870 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 871 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 891 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 894 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 896 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 913 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 916 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 927 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 930 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 931 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 933 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 934 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 935 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 936 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 950 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 953 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 954 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 955 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 957 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 958 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 960 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 961 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 962 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 963 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 964 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1041 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1051 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1054 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1055 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1056 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1058 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1076 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1077 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1083 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1389 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1392 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1393 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1394 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1395 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1397 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1409 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1422 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1430 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1442 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1443 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1448 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1461 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1462 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1582 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1585 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1586 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1589 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1615 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1629 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1630 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1633 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1643 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1644 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1747 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1750 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1751 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1755 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1783 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1805 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1806 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1809 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1823 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1824 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1945 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1948 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1962 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1965 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1971 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1972 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1980 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1983 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1984 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 1987 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2015 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2032 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2033 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2036 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2045 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2046 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2049 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2052 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2055 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2056 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2058 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2072 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2087 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2088 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2091 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2098 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2099 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2100 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2641 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2664 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2667 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2668 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2669 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2671 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2672 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2674 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2688 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2689 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2692 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2696 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2715 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2719 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2830 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2834 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2863 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2867 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2875 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2879 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2880 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2881 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2882 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2883 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2885 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2897 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2909 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2917 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2925 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2937 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2949 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2956 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2963 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2964 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2965 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2966 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2969 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2995 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 2996 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3070 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3073 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3074 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3077 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3079 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3083 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3093 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3096 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3097 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3099 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3100 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3104 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3112 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3115 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3116 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3118 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3119 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3123 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3171 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3174 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3176 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3177 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3194 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3197 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3203 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3210 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3218 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3241 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3244 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3245 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3247 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3256 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3259 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3262 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3264 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3280 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3283 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3291 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3298 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3302 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3315 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3318 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3326 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3333 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3337 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3350 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3353 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3360 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3367 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3375 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3391 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3393 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3394 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3395 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3397 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3398 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_conformance.py | 3399 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 5 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 20 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_protocol_v2_service_layer.py | 58 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 12 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 41 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 65 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 82 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 88 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 100 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 124 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 142 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 163 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 174 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 185 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 198 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 226 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 239 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 247 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 256 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 262 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 275 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 284 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 292 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 304 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 312 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 318 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 328 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 329 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 391 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 406 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 424 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 427 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_sqlite_store.py | 448 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 23 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 58 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_verified_count_strict.py | 82 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/graph/test_write_outcome_extended.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/graph/test_write_outcome_extended.py | 19 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_scorer_governed.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_scorer_governed.py | 83 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/scoring/test_storage.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 264 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 287 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 346 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/scoring/test_storage.py | 350 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_archive_reader.py | 7 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 63 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 76 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 85 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 112 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_archive_reader.py | 123 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_cross_copilot_transfer.py | 9 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_cross_copilot_transfer.py | 13 | type annotation | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_cross_copilot_transfer.py | 146 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_dual_write_store.py | 10 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_dual_write_store.py | 155 | instantiation/reference | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_entity_enrichment.py | 19 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 254 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 270 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 293 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 315 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 331 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 344 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 358 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 366 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 376 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 400 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 411 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_entity_enrichment.py | 497 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_factory_dual_write.py | 9 | import | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_factory_dual_write.py | 50 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_factory_dual_write.py | 71 | test assertion/type check | Dual-write/read-diff parity or migration tool; memory cannot substitute restart durability/parity evidence. |
| tests/test_five_domain_completeness.py | 14 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_five_domain_completeness.py | 32 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_gate_preseed_initialization.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 15 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 16 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 28 | type annotation | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_gate_preseed_initialization.py | 59 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_generate_decision_id.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 14 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 24 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 34 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 46 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 58 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 66 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_generate_decision_id.py | 87 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_global_queries.py | 6 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 12 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 30 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_global_queries.py | 114 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graph_entity_links.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_entity_links.py | 179 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 23 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_factory.py | 59 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_production_boundary.py | 16 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graph_production_boundary.py | 78 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_graphstore_consolidation.py | 7 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graphstore_consolidation.py | 266 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_graphstore_consolidation.py | 268 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_historical_checkpoint_import.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_historical_checkpoint_import.py | 14 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_conformance.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_jm_conformance.py | 46 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_jm_rl_cross_copilot.py | 111 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_rl_cross_copilot.py | 113 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 15 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 101 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 118 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 148 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_jm_v27_validation.py | 169 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_l5_centroid_storage.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 17 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 26 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 42 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 43 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_centroid_storage.py | 150 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 55 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 57 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 59 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 99 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 100 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 141 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_conservation_storage.py | 227 | reference/string/comment | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 9 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 27 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 36 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 60 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 61 | test assertion/type check | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 184 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_weight_storage.py | 201 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 30 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 137 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_l5_dk_welford_storage.py | 149 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 8 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 70 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 108 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_learn_context.py | 195 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_legacy_signal_filter.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_legacy_signal_filter.py | 17 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_outbox_sqlite.py | 9 | import | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 23 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 24 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 31 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 34 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 43 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 64 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 84 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 85 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 86 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 89 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 96 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 97 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 98 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 100 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 104 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 108 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 116 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 132 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 136 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 137 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 139 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 149 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 150 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 151 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 152 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 153 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 163 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 169 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 171 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 173 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 181 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 192 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 193 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 194 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 196 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 198 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 200 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 204 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 210 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 218 | type annotation | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 219 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_outbox_sqlite.py | 220 | reference/string/comment | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_preseed_gap_supersession.py | 10 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_preseed_gap_supersession.py | 37 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_quality_axis.py | 10 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_quality_axis.py | 142 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_reconcile_archive.py | 14 | import | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_reconcile_archive.py | 15 | instantiation/reference | Reads/reconciles historical SQLite data; needs a reviewed archive import/cutover rather than fresh memory. |
| tests/test_rule38_factory_compliance.py | 11 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_rule38_factory_compliance.py | 34 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_rule38_factory_compliance.py | 62 | test assertion/type check | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_session_regression.py | 63 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_session_regression.py | 66 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_situation_analyzer.py | 24 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_situation_analyzer.py | 444 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_situation_analyzer.py | 465 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 7 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 33 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_snapshot_after.py | 75 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_store_parity.py | 13 | import | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_store_parity.py | 24 | instantiation/reference | Mixed contract tests include raw schema, failure, reopen or process semantics; preserve coverage until durable backend replacement. |
| tests/test_transfer_pattern.py | 9 | import | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_transfer_pattern.py | 15 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_transfer_pattern.py | 116 | instantiation/reference | Existing SQLite contract/parity/fixture coverage retained with its backend; migrate remaining cases with factory/backend removal. |
| tests/test_worker_process_safety.py | 12 | import | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 46 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 61 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 73 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 97 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 134 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/test_worker_process_safety.py | 152 | instantiation/reference | Cross-process/restart durability and queued-write recovery cannot be reproduced with process-local memory. |
| tests/vld_validation_report.py | 7 | reference/string/comment | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/vld_validation_report.py | 224 | import | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |
| tests/vld_validation_report.py | 238 | instantiation/reference | Persisted demo/checkpoint restore or historical validation; migrate export/restore semantics before removing backend. |

