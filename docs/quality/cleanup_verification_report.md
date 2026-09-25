# Cleanup verification — September 13, 2026

Scope: copilot-sdk; read-only frozen-file checks in gen-ai-roi-demo-v4-v50. No git commands used.

## Pre-check and disposition

| Item | Pre-check finding | Disposition |
|---|---|---|
| DataOps import | ALREADY RESOLVED. Both connectors already use the absolute ConnectorCache import. SDK collection succeeded; DataOps passed 412 tests. | No import or application source change needed. |
| TIER-5C delivery | ALREADY PRESENT: Trading 10/10 and Purchasing 7/7 providers, configs, router mounts, and tests. | Verify current delivery, including subsequent Tier-5D provider work. |
| TIER-5C verification report | No matching report dated September 13 was found under docs/design or docs/quality; no recent test_result artifact established completion. The September 12 Astra resweep is a different, older acceptance report. | Verification completed with SDK failures; details below. |
| Figure 7 / Astra CSV | Existing images found, but no matching Astra 57-save raw JSON aggregate or summary CSV. Current Figure 7 already cites a paper table. | FIXED: paper-sourced CSVs added; Astra pub12 refreshed from its CSV. |

**Final statuses:** DataOps import ALREADY RESOLVED; TIER-5C verification COMPLETED WITH SDK FAILURES (domain suites and frontend checks pass); Fig 7/Astra CSV gap FIXED.

The root-suite and DataOps runs started during the mandatory pre-check and are reused as final verification. Successful checks were not repeated merely to reproduce the prompt's filtered console output.

## DataOps import

No current ImportError, ModuleNotFoundError, or collection error was reproduced.

The previously reported failure was `ImportError: attempted relative import with no known parent package`, in `apps/dataops/backend/app/celonis_connector.py:15`, when `tests/test_substantiation_e2e.py` loaded the connector through `spec_from_file_location`. This is historical context, not a failure observed in this cleanup.

Current imports, already present before this task:

- `apps/dataops/backend/app/celonis_connector.py:15`
- `apps/dataops/backend/app/sap_connector.py:10`

Both contain:

```python
from apps.dataops.backend.app.connector_cache import ConnectorCache
```

Before any cleanup source change: **412 DataOps tests passed**. After cleanup: the source is unchanged, so the same successful run applies; no before/after increase is claimed. **Exact change made: none.**

## TIER-5C validation

### Commands and counts

Python: `C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/proj-envs/python_expts_venv/Scripts/python.exe`.

Each suite ran from copilot-sdk using `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, and `--disable-warnings`. These options suppress bytecode/cache writes and warning detail; they do not disable test assertions.

| Scope | Test path | Timeout | Passed | Skipped | Failed / errors |
|---|---|---:|---:|---:|---:|
| SDK full run | tests/ | 120 s | 3,451 | 5 | 11 |
| SDK supplemental current contract tests | tests/rl/test_shared_control_contract.py | 120 s | 35 | 0 | 0 |
| Trading | apps/trading/backend/tests/ | 60 s | 1,452 | 0 | 0 |
| Purchasing | apps/purchasing/backend/tests/ | 60 s | 827 | 1 | 0 |
| DataOps | apps/dataops/backend/tests/ | 60 s | 412 | 0 | 0 |

**Total reported test executions: 6,194 — 6,177 passed, 6 skipped, 11 failed.** The four initial full suites account for 6,159 (6,142 passed, 6 skipped, 11 failed); the separately run current RL contract file adds 35 passing tests.

The SDK full run collected/executed 3,467 cases and completed in 1,192.78 s. The later collection found 3,502, a 35-case difference in this changing workspace. The current `tests/rl/test_shared_control_contract.py` file was therefore run separately: 35 passed. These are separate verification snapshots, not a claim of one atomic clean 3,502-test run. Trading completed in 350.42 s, Purchasing in 521.96 s, and DataOps in 153.66 s.

### SDK failures requiring follow-up

**The SDK suite is not green.** No import or collection errors were found, but the full run reports two independent problems:

1. `tests/test_type_checking.py:48::test_mypy_passes_with_config` fails because `copilot_sdk/rl/reward_protocol.py:85–86` passes an inferred `tuple[float, ...]` to `normalize_reward` and `ComputedReward`, whose contracts require `tuple[float, float]`. Exact mypy messages:
   - Line 85: `Argument 2 to "normalize_reward" has incompatible type "tuple[float, ...]"; expected "tuple[float, float]" [arg-type]`.
   - Line 86: `Argument 4 to "ComputedReward" has incompatible type "tuple[float, ...]"; expected "tuple[float, float]" [arg-type]`.
   The inference originates at line 83: `bounds = tuple(map(float, function.reward_range()))`. The 35 runtime RL contract tests pass; they do not resolve these static typing errors.
2. Ten aggregate tests in `tests/test_vld_integration.py` fail at `complete_rows()`, line 213, because the DataOps sweep is incomplete. Exact error (unstable object address omitted): `ValueError: malformed node or string on line 961: <ast.Starred object ...>`. `apps/dataops/backend/app/main.py:961` uses `gated_sources={"schema_registry", "dependency_graph", *CONNECTOR_GATED_SOURCES}`. `tests/vld_validation_report.py:wiring()` calls `ast.literal_eval` on that set and cannot evaluate the starred name. The Python application itself accepts this syntax; the DataOps app suite passes. Five DataOps-specific SDK checks skip after the sweep error.

The ten failed aggregate tests are: `test_all_copilots_centroid_shapes_valid`, `test_all_evidence_providers_implement_protocol`, `test_all_s1_scenarios_high_margin`, `test_no_investigation_hurts`, `test_all_flips_robust`, `test_ordered_reads_for_every_scenario`, `test_all_s1_explicit_budget_zero_and_no_auto_reads`, `test_s1_classifier_budget_check_reported`, `test_scorer_parity_sample_and_all_rows`, and `test_evidence_tier_labels_present`.

These are outside the requested minimal import correction. Neither the RL implementation nor the verification helper was changed. A follow-up should preserve the reward's two-element tuple type and teach the diagnostic helper to resolve the actual connector gate set without weakening the sweep checks or dropping connector provenance gates. **Full TIER-5C SDK sign-off remains blocked by these failures.**

The explicit SDK post-check also passed: `python -m pytest tests/ --collect-only -q -p no:cacheprovider --disable-warnings` reported **3,502 tests collected in 19.51s**, exit code 0. This is the current count, rather than the older 3,467 expectation.

Both frontend commands returned exit code 0 with no diagnostics:

```text
apps/trading/frontend: npx tsc --noEmit
apps/purchasing/frontend: npx tsc --noEmit
```

App suites run in separate processes, matching their existing `app` import layout. No combined-process import refactor was attempted.

### Provider and endpoint coverage

The registry keys and their ordering exactly match `real_centroids_v1.json`.

| Domain | Providers | Registered factors |
|---|---:|---|
| Trading | 10/10 | signal_alignment, market_regime, position_sizing, timing_quality, risk_reward_actual, emotional_indicator, signal_confidence, options_delta_exposure, options_iv_percentile, options_gamma_risk |
| Purchasing | 7/7 | expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index |

Both `main.py` files mount `create_investigation_router`. Both configs bind the registry and decision attachment, with DECIDED_ON, MEMBER_OF and CONTINUES topology.

The app suites include `test_investigation_integration.py`: mounted health endpoint, POST trace response, budgets 0/1/2, actual provider dispatch, immutable snapshot, and read-only investigation. The read-only check forbids scorer `learn()` and mutating `score()`, then compares centroid geometry, graph state and K table before/after. Endpoint checks use FastAPI TestClient; this is not a separately launched live-service certification.

### Nine-beat mapping

The mapping below establishes that corresponding tests/providers exist. DataOps-specific SDK runtime checks were skipped because of the collector error above; this report does not label those checks passed.

Exactly nine beat definitions were identified in v2.9 §4.17 (lines 1125–1240). Integration bridge mentions are not counted as additional beats.

| Beat | Corresponding provider / test evidence | Scope of alignment |
|---|---|---|
| VLD-SOC-1 | SOC `backend/app/evidence_provider.py` in gen-ai-roi-demo-v4-v50; SDK `test_soc_vld_soc1_real_flip` | Identity evidence and planted scorer trace. |
| VLD-SOC-2 | Same SOC provider; SDK `test_soc_vld_soc2_empty_branch` | Empty-first-read recovery control; does not establish the separately proposed verified-negative transform. |
| VLD-DO-1 | `apps/dataops/backend/app/evidence_provider.py`; SDK `test_dataops_do1_three_systems_real` | Existing evidence route [0,3]; expanded lineage and as-of narrative remain separate requirements. |
| VLD-DO-2 | Same DataOps provider; SDK `test_dataops_do2_known_pattern_real` | Existing [2,3] fixture; proposed broad-read/novelty controller is not certified by this test. |
| VLD-S2P-1 | Existing s2p-copilot `backend/app/evidence_provider.py`; SDK `test_s2p_supplier_it_knew_real` | Existing supplier fixture; exact v2.9 history cohort and temporal cutoffs are not established by provider presence. |
| VLD-TRD-1 | Trading `test_vld_beats.py::test_vld_trd_1_portfolio_concentration_provider_exists` and parametrized trace test | position_sizing dimension 2 exists; actual trace links tested without forcing Q order. |
| VLD-TRD-2 | Trading `test_vld_trd_2_check_prevention_provider_exists` and parametrized trace test | timing_quality dimension 3 and options_iv_percentile dimension 8 exist. Legacy provider-absence choreography is superseded. |
| VLD-PUR-1 | Purchasing `test_vld_pur_1_supplier_lead_time_provider_exists` and demand-spike trace test | Canonical event_flag dimension 3, historical_waste dimension 4, supplier_lead_time dimension 5. |
| VLD-PUR-2 | Purchasing `test_vld_pur_2_delivery_history_provider_exists` and vendor-cascade trace test | historical_waste and supplier_lead_time present; in-memory episode continuity links tested. |

SDK test names above are in `tests/test_vld_integration.py`. Trading and Purchasing beat tests are in their respective `apps/<domain>/backend/tests/test_vld_beats.py`.

**Wiring verification is not certification that all expanded v2.9 stories are live.** The demo remains ARCH in several places. Trading IV is dimension 8, not the document's legacy dimension 9. Purchasing event_flag is dimension 3 and supplier_lead_time is dimension 5; the document uses older indices/names. Existing tests deliberately use canonical schemas. Portfolio entity expansion, historical as-of filtering, proposed broader-read controllers and manager-handoff evidence semantics require their own acceptance evidence. Trace topology helpers return in-memory links; their existence does not establish persistent graph writes or additional fields in the frozen SDK response. No demo, source, fixture or test was edited to conceal these distinctions.

## Figure 7 and Astra data resolution

Two distinct artifacts were referenced in the request:

1. `experiments/vld/paper_charts/fig_7_budget_sensitivity.png` (also SVG): **Fig 7 sourced from paper §4.1's unnumbered “Budget sensitivity” table in ci_rgi_impact_core_v6.md**. The generator already parses that table in `scripts/generate_paper_charts.py:sensitivity()`. Its 15 saves:hurts labels match the table. The existing figure was visually checked and retained.
2. `experiments/vld/pub_charts/pub12_astra_57_0_summary.png`: B=3 Astra with/without results from the unnumbered §10.2 table in `ci_vld_architecture_prepaper_v10.md`. Refreshed from the new CSV with the same counts, percentage-point uplift labels, and explicit SIMULATED / paper-table provenance. Visually checked after rendering.

The requested `experiments/vld/generate_all_pub_charts.py` path does not exist. The actual file is `experiments/vld/scripts/generate_all_pub_charts.py`; it currently does not generate this Astra pub12. No unrelated generator was refactored.

New machine-readable sources:

- `experiments/vld/astra_57_0_summary.csv`: five B=3 rows; scenario counts, SP/VLD accuracy, saves, hurts, uplift in pp, source file/section and source SHA-256.
- `experiments/vld/astra_budget_sensitivity_summary.csv`: fifteen rows, five copilots × B=2/3/4; explicit paper source and SHA-256.

| Copilot | N at B=3 | SP accuracy | VLD accuracy | Saves | Hurts | Uplift |
|---|---:|---:|---:|---:|---:|---:|
| SOC | 50 | 0.100 | 0.180 | 4 | 0 | +8.0 pp |
| S2P | 50 | 0.300 | 0.540 | 12 | 0 | +24.0 pp |
| DataOps | 50 | 0.520 | 0.760 | 12 | 0 | +24.0 pp |
| Trading | 50 | 0.440 | 0.800 | 18 | 0 | +36.0 pp |
| Purchasing | 50 | 0.460 | 0.680 | 11 | 0 | +22.0 pp |
| Total | 250 | 0.364 | 0.592 | 57 | 0 | +22.8 pp |

Validation: CSV round-trip reads succeeded, row counts are 5 and 15, all B=3 counts agree across both source tables, and `50 × (VLD − SP) = saves − hurts` for each copilot. The aggregate is 91 to 148 correct decisions. No finite “114:1” ratio was inferred from zero hurts.

This is **paper-table transcription**, not recovered raw experimental data or a new experiment. The saved `case_studies_*_astra.md` reports and Stage-1 JSONs concern other cohorts and cannot substitute for this 57-save table. The budget frontier CSV contains accuracy/read metrics from a separate protocol and cannot yield these saves:hurts transitions. The source's constructed evidence reveals true factor values; natural-prevalence uplift remains unmeasured.

## Frozen source integrity

SHA-256 values were captured before work and compared after verification. **All checked files unchanged; 0 scorer/investigation files modified.**

| File (relative to copilot-sdk) | SHA-256 | Result |
|---|---|---|
| `../gen-ai-roi-demo-v4-v50/backend/app/services/triage.py` | `1edda7293dfd926d33a3b51dc0d1055c1b2e8b67b27f2cd491f7a41a01f73051` | unchanged |
| `copilot_sdk/situation/analyzer.py` | `9027bba73522c69704da839b98cd4bddf3def2b79d8cf9eb1f916cdd36ac6b32` | unchanged |
| `../gen-ai-roi-demo-v4-v50/backend/app/services/learning.py` | `43c8fec1f5d8faaecda092fc3b170756d209245b35ac8fc453ebdcbc62959628` | unchanged |
| `copilot_sdk/scoring/investigation.py` | `3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4` | unchanged |
| `../gen-ai-roi-demo-v4-v50/backend/app/services/investigation_router.py` | `7a7c321bf6632cb76daed88b8507a0bdc3218dd5105736210d73664cd5318dd0` | unchanged |
| `copilot_sdk/scoring/scorer.py` | `24ac9e49a070e0f9421fa0e3e7417a828c0ec88610ef906ce4987311c721b460` | unchanged |
| `../gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py` | `a502252e7ec5701e5596dc0c795bdc6a03407e0cb848915f5747fe3be900f15d` | unchanged |
| `../gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py` | `0acf8c204f877e2212f7f7a6abc5942b76a328d2556d584c1214482b58f194b6` | unchanged |
| `../graph-attention-engine-v50/gae/learning.py` | `f37ffa81c698aa0d08d4f61ac20d36c91474dd7ef7886f8e38ddfc0bd3c2ab1c` | unchanged |
| `copilot_sdk/backend/investigation_router.py` | `08f4df7ad872a6cf0dc53c0bd7250fe854ca7481e508aa592b35fe06440a744b` | unchanged |
| `../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | `4749142a9b85f1b2f941bc8c754e2cfa7c3b26df0ad744d99b129056a556e6c0` | unchanged |

The actual frozen SDK paths are `copilot_sdk/scoring/investigation.py` and `copilot_sdk/backend/investigation_router.py`. The prompt's `copilot_sdk/investigation/...` paths do not exist. The full investigator hash starts `3441dcbd...`; the prompt's abbreviated `3441dcdb...` transposes characters. The full stored investigator, router and scorer hashes match the supplied canonical full hashes.

## Files changed by this cleanup

- Created this report.
- Created the two source-attributed CSVs listed above.
- Regenerated only `experiments/vld/pub_charts/pub12_astra_57_0_summary.png`.
- **No application, SDK, test, or chart-generator source files modified.**

