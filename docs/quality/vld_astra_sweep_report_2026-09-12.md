# VLD-ASTRA-RESWEEP — acceptance report — 2026-09-12

**PAPER_READY=False. DEMO_READY=False.** Current revised showcase contracts pass **10/15**; exact action pairs match **12/15**; **7/10** claimed flips occur; observed hurts are **0**. The integration suite reports **23 passed, 8 failed**.

This is a fresh run of the existing tools against local data after the P0, WIRE, REGEN-2 and TEST-ALIGN changes. It is **not a live AGE or running-service certification**. The tools use real scorer/provider implementations, read-only SQLite snapshots, SOC bootstrap centroids, and startup-equivalent L5 centroid overlays. They still omit actual K injection, and miss SOC/Trading classifier wiring hidden in **kwargs helpers. Sources: copilot-sdk/tests/vld_validation_report.py:62, :141, :182 and :270.

Only this report and the authorized centroid export are deliverables. The VLD snapshot/collector scope is offline; the wider baseline suites did exercise configured AGE paths, including the failures recorded in Appendix A. No source fix, preseed tuning, provider replacement or test modification was performed. Source-hash verification and all baseline counts appear in the execution appendix.

Authority/readings:
- [Original Sep 11 sweep](vld_astra_sweep_report_2026-09-11.md).
- [Post-regeneration geometry snapshot](../design/vld_post_regen_geometry_snapshot_2026-09-11.md).
- [Centroid/preseed gap analysis](../design/vld_centroid_preseed_gap_analysis_2026-09-11.md).

Paths with line numbers below are relative to the workspace root. Numerical findings were produced by the current tools during this sweep, with supplementary read-only source/SQLite checks explicitly identified.

## 1 — Per-copilot scenario matrix

The main matrix reproduces the existing collector's **explicit budget=2** runs, including S1 rows. The separate S1 table uses the seed's explicit budget or the omitted-budget classifier path. Thus an S1 row can show attempted reads in the forced-budget matrix and correctly show zero reads in its actual S1 contract.

MATCH means exact current claimed surface and final actions. Full contract additionally requires the current narrative path, margin thresholds, and S1 budget/behavior. Sources: copilot-sdk/tests/vld_validation_report.py:253–305; integration assertions copilot-sdk/tests/test_vld_integration.py:47 and :68.

### soc

Tensor [6,4,6]; tau=0.1; sigma=[1,1,1,1,1,1]. L5 rows applied: 0. Seed/provider references are listed below the tables. The collector can mislabel a checkpoint-plus-L5 tensor as a bootstrap because it compares the post-restore tensor to the pre-restore checkpoint at vld_validation_report.py:222–223; use the hashes and overlay counts in section 4 instead.

| Scenario | Surface action | Surface margin | VLD action | VLD margin | Flip? | Claimed pair | MATCH | Successful steps / attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-SOC-1 | monitor | 0.11991623 | escalate | 0.18020368 | YES | monitor → escalate | YES | 1 / 2 |
| VLD-SOC-2 | monitor | 0.11968118 | escalate | 0.18011947 | YES | monitor → escalate | YES | 1 / 2 |
| VLD-SOC-S1 | escalate | 0.66401995 | escalate | 0.66401995 | NO | escalate → escalate | YES | 0 / 2 |

| Scenario | Attempted dimensions and evidence | Current narrative path | Narrative match | Full contract |
| --- | --- | --- | --- | --- |
| VLD-SOC-1 | 0 privileged_identity_context: 0.92000000 (c=0.92000000, identity_graph); 5 device_trust: None | 0 | YES | PASS |
| VLD-SOC-2 | 2 threat_intel_enrichment: None; 0 privileged_identity_context: 0.92000000 (c=0.92000000, identity_graph) | 2 → 0 | YES | PASS |
| VLD-SOC-S1 | 1 asset_criticality: None; 5 device_trust: None | S1: no reads under S1 budget | YES | PASS |

| Scenario | Successful vector updates | Seed source | Provider source |
| --- | --- | --- | --- |
| VLD-SOC-1 | 0: 0.00050000 → 0.84644000 | gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:10 | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75 |
| VLD-SOC-2 | 0: 0.29390000 → 0.86991200 | gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:30 | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75 |
| VLD-SOC-S1 | none | gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:53 | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75 |

### trading

Tensor [5,4,10]; tau=0.1; sigma=[1,1,1,1,1,1,1,1,1,1]. L5 rows applied: 6. Seed/provider references are listed below the tables. The collector can mislabel a checkpoint-plus-L5 tensor as a bootstrap because it compares the post-restore tensor to the pre-restore checkpoint at vld_validation_report.py:222–223; use the hashes and overlay counts in section 4 instead.

| Scenario | Surface action | Surface margin | VLD action | VLD margin | Flip? | Claimed pair | MATCH | Successful steps / attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-TRD-1 | strong_execution | 0.84733296 | partial_execution | 0.49094184 | YES | strong_execution → partial_execution | YES | 1 / 2 |
| VLD-TRD-2 | strong_execution | 0.98215159 | partial_execution | 0.42628282 | YES | strong_execution → partial_execution | YES | 1 / 2 |
| VLD-TRD-S1 | strong_execution | 0.98528817 | strong_execution | 0.98528817 | NO | strong_execution → strong_execution | YES | 0 / 2 |

| Scenario | Attempted dimensions and evidence | Current narrative path | Narrative match | Full contract |
| --- | --- | --- | --- | --- |
| VLD-TRD-1 | 2 position_sizing: None; 1 market_regime: 0.88000000 (c=0.90000000, correlation_engine) | 2 → 1 | YES | PASS |
| VLD-TRD-2 | 2 position_sizing: 0.85000000 (c=0.92000000, portfolio_engine); 3 timing_quality: None | 2 → 1 | NO | FAIL |
| VLD-TRD-S1 | 1 market_regime: None; 2 position_sizing: None | S1: no reads under S1 budget | YES | PASS |

| Scenario | Successful vector updates | Seed source | Provider source |
| --- | --- | --- | --- |
| VLD-TRD-1 | 1: 0.16810000 → 0.80881000 | copilot-sdk/apps/trading/backend/app/vld_preseed.py:10 | copilot-sdk/apps/trading/backend/app/evidence_provider.py:63 |
| VLD-TRD-2 | 2: 0.00660000 → 0.78252800 | copilot-sdk/apps/trading/backend/app/vld_preseed.py:27 | copilot-sdk/apps/trading/backend/app/evidence_provider.py:63 |
| VLD-TRD-S1 | none | copilot-sdk/apps/trading/backend/app/vld_preseed.py:43 | copilot-sdk/apps/trading/backend/app/evidence_provider.py:63 |

### purchasing

Tensor [5,4,7]; tau=0.1; sigma=[1,1,1,1,1,1,1]. L5 rows applied: 0. Seed/provider references are listed below the tables. The collector can mislabel a checkpoint-plus-L5 tensor as a bootstrap because it compares the post-restore tensor to the pre-restore checkpoint at vld_validation_report.py:222–223; use the hashes and overlay counts in section 4 instead.

| Scenario | Surface action | Surface margin | VLD action | VLD margin | Flip? | Claimed pair | MATCH | Successful steps / attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-PUR-DEMAND-SPIKE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | NO | order_more → order_less | NO | 2 / 2 |
| VLD-PUR-VENDOR-CASCADE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | NO | order_as_planned → skip | NO | 2 / 2 |
| VLD-PUR-S1-STANDARD | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | NO | order_as_planned → order_as_planned | YES | 2 / 2 |

| Scenario | Attempted dimensions and evidence | Current narrative path | Narrative match | Full contract |
| --- | --- | --- | --- | --- |
| VLD-PUR-DEMAND-SPIKE | 0 expected_demand: 0.80000000 (c=0.86000000, demand_forecast); 1 day_of_week: 0.50000000 (c=0.65000000, calendar) | 5 → 6 | NO | FAIL |
| VLD-PUR-VENDOR-CASCADE | 0 expected_demand: 0.40000000 (c=0.70000000, demand_forecast); 1 day_of_week: 0.50000000 (c=0.65000000, calendar) | 4 → 5 | NO | FAIL |
| VLD-PUR-S1-STANDARD | 0 expected_demand: 0.58000000 (c=0.70000000, demand_forecast); 1 day_of_week: 0.50000000 (c=0.65000000, calendar) | S1: no reads under S1 budget | YES | FAIL |

| Scenario | Successful vector updates | Seed source | Provider source |
| --- | --- | --- | --- |
| VLD-PUR-DEMAND-SPIKE | 0: 0.80000000 → 0.80000000; 1: 0.50000000 → 0.50000000 | copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:63 | copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25 |
| VLD-PUR-VENDOR-CASCADE | 0: 0.40000000 → 0.40000000; 1: 0.50000000 → 0.50000000 | copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:108 | copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25 |
| VLD-PUR-S1-STANDARD | 0: 0.58000000 → 0.58000000; 1: 0.50000000 → 0.50000000 | copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:140 | copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25 |

### dataops

Tensor [6,5,6]; tau=0.1; sigma=[1,1,1,1,1,1]. L5 rows applied: 3. Seed/provider references are listed below the tables. The collector can mislabel a checkpoint-plus-L5 tensor as a bootstrap because it compares the post-restore tensor to the pre-restore checkpoint at vld_validation_report.py:222–223; use the hashes and overlay counts in section 4 instead.

| Scenario | Surface action | Surface margin | VLD action | VLD margin | Flip? | Claimed pair | MATCH | Successful steps / attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-DO-1 | investigate | 0.11983817 | escalate_to_owner | 0.95639628 | YES | investigate → escalate_to_owner | YES | 2 / 2 |
| VLD-DO-2 | refer_to_specialist | 0.70634656 | escalate_to_owner | 0.67379464 | YES | refer_to_specialist → escalate_to_owner | YES | 2 / 2 |
| VLD-DO-S1 | auto_approve | 0.99899631 | auto_approve | 0.99899631 | NO | auto_approve → auto_approve | YES | 0 / 2 |

| Scenario | Attempted dimensions and evidence | Current narrative path | Narrative match | Full contract |
| --- | --- | --- | --- | --- |
| VLD-DO-1 | 0 impact_scope: 0.90000000 (c=0.92000000, schema_registry); 3 downstream_urgency: 0.85000000 (c=0.88000000, dependency_graph) | 0 → 3 | YES | PASS |
| VLD-DO-2 | 2 recurrence_frequency: 0.65000000 (c=0.55000000, historical_alerts); 3 downstream_urgency: 0.88000000 (c=0.82000000, dependency_graph) | 2 → 3 | YES | PASS |
| VLD-DO-S1 | 0 impact_scope: None; 4 data_freshness: None | S1: no reads under S1 budget | YES | PASS |

| Scenario | Successful vector updates | Seed source | Provider source |
| --- | --- | --- | --- |
| VLD-DO-1 | 0: 0.12760000 → 0.83820800; 3: 0.67540000 → 0.82904800 | copilot-sdk/apps/dataops/backend/app/vld_preseed.py:11 | copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38 |
| VLD-DO-2 | 2: 0.91890000 → 0.65000000; 3: 0.31120000 → 0.77761600 | copilot-sdk/apps/dataops/backend/app/vld_preseed.py:12 | copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38 |
| VLD-DO-S1 | none | copilot-sdk/apps/dataops/backend/app/vld_preseed.py:13 | copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38 |

### s2p

Tensor [5,5,8]; tau=0.1; sigma=[1,1,1,1,1,1,1,1]. L5 rows applied: 6. Seed/provider references are listed below the tables. The collector can mislabel a checkpoint-plus-L5 tensor as a bootstrap because it compares the post-restore tensor to the pre-restore checkpoint at vld_validation_report.py:222–223; use the hashes and overlay counts in section 4 instead.

| Scenario | Surface action | Surface margin | VLD action | VLD margin | Flip? | Claimed pair | MATCH | Successful steps / attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-S2P-1 | hold_for_review | 0.88287659 | auto_approve | 0.90982841 | YES | hold_for_review → auto_approve | YES | 2 / 2 |
| VLD-S2P-2 | flag_leakage | 0.89089475 | flag_leakage | 0.89718343 | NO | flag_leakage → auto_approve | NO | 2 / 2 |
| VLD-S2P-S1 | auto_approve | 0.93648764 | auto_approve | 0.95217192 | NO | auto_approve → auto_approve | YES | 1 / 2 |

| Scenario | Attempted dimensions and evidence | Current narrative path | Narrative match | Full contract |
| --- | --- | --- | --- | --- |
| VLD-S2P-1 | 0 match_status: 0.95000000 (c=0.90000000, contract_db); 3 supplier_exception_history: 0.03000000 (c=0.82142857, supplier_history) | 0 → 3 | YES | PASS |
| VLD-S2P-2 | 0 match_status: 0.93000000 (c=0.90000000, contract_db); 1 amount_variance_ratio: 0.05000000 (c=0.82000000, pricing_benchmark) | 0 → 5 | NO | FAIL |
| VLD-S2P-S1 | 0 match_status: 0.98000000 (c=0.95000000, contract_db); 5 commodity_index_correlation: None | S1: no reads under S1 budget | YES | PASS |

| Scenario | Successful vector updates | Seed source | Provider source |
| --- | --- | --- | --- |
| VLD-S2P-1 | 0: 0.39060000 → 0.95000000; 3: 0.42670000 → 0.03000000 | s2p-copilot/backend/app/vld_preseed.py:65 | s2p-copilot/backend/app/evidence_provider.py:28 |
| VLD-S2P-2 | 0: 0.92370000 → 0.93000000; 1: 0.10100000 → 0.05000000 | s2p-copilot/backend/app/vld_preseed.py:100 | s2p-copilot/backend/app/evidence_provider.py:28 |
| VLD-S2P-S1 | 0: 0.94200000 → 0.98000000 | s2p-copilot/backend/app/vld_preseed.py:141 | s2p-copilot/backend/app/evidence_provider.py:28 |

### S1 contracts and classifier observations

Explicit budget=0 intentionally bypasses classification in the router, so situation=None is expected for SOC/Trading's explicit-budget seeds. A supplementary call to the actual SituationClassifier.classify confirms that both vectors would be classified S1 if budget were omitted and the real wired classifier were used. Source: copilot-sdk/copilot_sdk/backend/investigation_router.py:65–72; copilot-sdk/copilot_sdk/scoring/situation_classifier.py:104–129. These supplementary calls did not instantiate the live application.

| Copilot / S1 scenario | Surface margin | Actual S1 request budget | Reported situation | Actual S1 attempts | Fallback classification / budget | S1 contract |
| --- | --- | --- | --- | --- | --- | --- |
| soc / VLD-SOC-S1 | 0.66401995 | 0 | None (explicit zero budget) | 0 | S1 / 0 | PASS |
| trading / VLD-TRD-S1 | 0.98528817 | 0 | None (explicit zero budget) | 0 | S1 / 0 | PASS |
| purchasing / VLD-PUR-S1-STANDARD | 0.00000000 | 4 | S6 | 4 | S6 / 4 | FAIL |
| dataops / VLD-DO-S1 | 0.99899631 | 0 | S1 | 0 | S1 / 0 | PASS |
| s2p / VLD-S2P-S1 | 0.93648764 | 0 | S1 | 0 | S1 / 0 | PASS |

SOC's budget=0 is set at gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:59; Trading's at copilot-sdk/apps/trading/backend/app/vld_preseed.py:49. Purchasing's S1 case is S6 with budget=4 and margin=0, so its matching action label does not satisfy the S1 contract.

### Narrative authority versus stale test expectations

The revised preseed copy is authoritative for this resweep; stale expectations are preserved as test failures rather than silently rewritten.

| Scenario | Current narrative / expected attempts | Collector expectation | Observed attempts | Assessment |
| --- | --- | --- | --- | --- |
| VLD-TRD-1 | Empty candidate, then regime: 2(None)→1 | [1,3] | 2(None)→1 | Current narrative passes; integration expectation is stale |
| VLD-TRD-2 | Portfolio concentration, then regime: 2→1 | [2,1] | 2→3(None) | Real narrative mismatch, despite a correct final action |
| VLD-S2P-1 | Contract then supplier: 0→3 | [3,0], compared as a set | 0→3 | Current narrative passes; collector does not enforce its written order |
| VLD-S2P-2 | Contract then volume: 0→5 | [1,5] | 0→1 | Both current and legacy narratives fail; final action also fails |

Sources: copilot-sdk/apps/trading/backend/app/vld_preseed.py:16 and :33; s2p-copilot/backend/app/vld_preseed.py:78 and :114; copilot-sdk/tests/vld_validation_report.py:45 and :281–290. The snapshot independently names these revised paths at copilot-sdk/docs/design/vld_post_regen_geometry_snapshot_2026-09-11.md:239, :240, :271 and :272.

### Explicit and omitted budgets differ

The main matrix pins budget=2. DataOps DO-1 and S2P-1 receive S3/budget=1 when omitted, so their second narrative read is absent on that request path. DO-2 receives S6/budget=4 and performs additional reads. Source: current auto_response/auto_reads from vld_validation_report.py:277–279.

The collector misses the SOC/Trading classifiers entirely. Supplementary evaluation of their current vectors with the actual fallback classifier gives S6/budget=4 for both flip scenarios in each copilot, and S1/budget=0 for each S1 vector. Its purported “omitted-budget router” results for those two domains are therefore not faithful to current production wiring. Explicit budget=2 must be part of any claim made from the main matrix.

## 2 — Summary

| Copilot | Scenarios | Flips claimed | Flips actual | Action-pair match | Action mismatch | Current full contracts |
| --- | --- | --- | --- | --- | --- | --- |
| soc | 3 | 2 | 2 | 3 | 0 | 3/3 |
| trading | 3 | 2 | 2 | 3 | 0 | 2/3 |
| purchasing | 3 | 2 | 0 | 1 | 2 | 0/3 |
| dataops | 3 | 2 | 2 | 3 | 0 | 3/3 |
| s2p | 3 | 2 | 1 | 2 | 1 | 2/3 |
| TOTAL | 15 | 10 | 7 | 12 | 3 | 10/15 |

Five full-contract failures remain: VLD-TRD-2, all three Purchasing cases, and VLD-S2P-2. This is distinct from the eight pytest failures, which also include stale assertions and aggregate tests.

## 3 — K store and classifier status

Source inspection follows each helper expansion into the actual create_investigation_router call. All five applications are wired. These connections target a dedicated k_utility.db with a connection wrapper; they are not proof that verified decision history has trained K.

| Copilot | K wired | Local K rows / updated rows | K exercised by sweep | Classifier wired | Model loaded | Fallback | Wiring source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SOC | YES | 0 / 0 | NO | YES | NO | heuristic | gen-ai-roi-demo-v4-v50/backend/app/main.py:202 and :245 |
| Trading | YES | 0 / 0 | NO | YES | NO | heuristic | copilot-sdk/apps/trading/backend/app/main.py:132 and :561 |
| Purchasing | YES | 0 / 0 | NO | YES | NO | heuristic | copilot-sdk/apps/purchasing/backend/app/main.py:147 and :841 |
| DataOps | YES | 0 / 0 | NO | YES | NO | heuristic | copilot-sdk/apps/dataops/backend/app/main.py:108 and :949 |
| S2P | YES | 0 / 0 | NO | YES | NO | heuristic | s2p-copilot/backend/app/main.py:41 and :339 |

Read-only SQLite queries inspected the existing configured-default files:

- gen-ai-roi-demo-v4-v50/backend/data/k_utility.db
- copilot-sdk/apps/trading/backend/data/k_utility.db
- copilot-sdk/apps/purchasing/backend/data/k_utility.db
- copilot-sdk/apps/dataops/backend/data/k_utility.db
- s2p-copilot/backend/app/data/k_utility.db

Each contains the k_utility table and zero rows, including zero rows with n_updates>0. This describes the inspected local files, not remote deployment state or environment-overridden directories.

KUtilityStore returns a uniform 0.5 vector for an empty category at copilot-sdk/copilot_sdk/scoring/investigation.py:216–226. Multiplying every eligible Q by the same positive number preserves ordering. Thus omitting K has the same ordering for these empty local stores, but **does not count as exercising the production K connection**. The collector actually injects no K store (vld_validation_report.py:270), hardcodes k_store_exercised=False (:248), and looks for K data in the scoring database (:245), rather than the separate database introduced by WIRE.

All constructors use SituationClassifier() without model_path. The constructor only loads a model when an existing model path is supplied: copilot-sdk/copilot_sdk/scoring/situation_classifier.py:92–101. No trained classifier is loaded by the observed application wiring.

**Unexpected validation gap:** wiring() builds a dictionary from explicit AST keywords. A **kwargs expansion has arg=None, so the helper's k_store/classifier entries are not discovered (vld_validation_report.py:71–84). Its “K wired=False for all” and “SOC/Trading classifier=False” output is incorrect for current main.py. Merely removing the guard at :194 would not fix collection: the collector must inspect and inject the actual store and classifier configuration.

## 4 — Centroid differentiation and state fidelity

The current collection applies the same validated L5 centroid overlay used at startup, through restore_l5_centroids_for_export at copilot-sdk/tests/vld_validation_report.py:141–158. Hashes are SHA-256 of float64 tensor bytes. They identify geometry, not the JSON file.

| Copilot | Pre-restore tensor hash | Post-restore tensor hash | L5 rows total / applied |
| --- | --- | --- | --- |
| soc | e055e9f4733cfac11711dbdcf8e0c9de7b6b1ffd6f401ceadfe6bc9867af237a | e055e9f4733cfac11711dbdcf8e0c9de7b6b1ffd6f401ceadfe6bc9867af237a | 0 / 0 |
| trading | 2e5b594bb42e566947988ced423ca441d051fb9389b29a7bb105f7221c7d5968 | c672b63e2d0a672027d76d300306a336647c6a1838d02a231f10aa8735a4df72 | 6 / 6 |
| purchasing | 78acf27a75353d61047751e435b0482879e5c1e9c520db8e39515b37ee2857bd | 78acf27a75353d61047751e435b0482879e5c1e9c520db8e39515b37ee2857bd | 0 / 0 |
| dataops | 537b99b6c6064ad1db6bcdf7ae384eac7a4e3dee650918bd2d4f3058f4c8b4d6 | 7d03df393211484452ddbe258f2836314ab7f8f429027c3dd5bc0fd2f065622c | 3 / 3 |
| s2p | 683724c09ab902c049133e1ba09c7d9f8846de18dd809aa1c6d141366e26b3b1 | 38c5c5d09819dcadaf127a370906066c30b59ff7a778e43bd9957022434a4998 | 6 / 6 |

| Copilot | Category | Action × factor shape | Max pairwise coordinate diff | Requested status | Min pairwise coordinate diff |
| --- | --- | --- | --- | --- | --- |
| soc | credential_access | 4 × 6 | 0.70000000 | DIFF | 0.20000000 |
| soc | malware_execution | 4 × 6 | 0.70000000 | DIFF | 0.25000000 |
| soc | lateral_movement | 4 × 6 | 0.65000000 | DIFF | 0.20000000 |
| soc | data_exfiltration | 4 × 6 | 0.75000000 | DIFF | 0.20000000 |
| soc | insider_threat | 4 × 6 | 0.70000000 | DIFF | 0.25000000 |
| soc | cloud_infrastructure | 4 × 6 | 0.70000000 | DIFF | 0.20000000 |
| trading | trend_following | 4 × 10 | 0.52655098 | DIFF | 0.00000000 |
| trading | mean_reversion | 4 × 10 | 0.03000000 | DIFF | 0.00000000 |
| trading | event_driven | 4 × 10 | 0.02500000 | DIFF | 0.00000000 |
| trading | income_strategy | 4 × 10 | 0.00000000 | IDENTICAL | 0.00000000 |
| trading | scalp_intraday | 4 × 10 | 0.00000000 | IDENTICAL | 0.00000000 |
| purchasing | protein | 4 × 7 | 0.00000000 | IDENTICAL | 0.00000000 |
| purchasing | produce | 4 × 7 | 0.00000000 | IDENTICAL | 0.00000000 |
| purchasing | dairy | 4 × 7 | 0.00000000 | IDENTICAL | 0.00000000 |
| purchasing | dry_goods | 4 × 7 | 0.00000000 | IDENTICAL | 0.00000000 |
| purchasing | beverages | 4 × 7 | 0.00000000 | IDENTICAL | 0.00000000 |
| dataops | schema_change | 5 × 6 | 0.89036258 | DIFF | 0.48935436 |
| dataops | volume_anomaly | 5 × 6 | 1.00000000 | DIFF | 0.41883369 |
| dataops | quality_anomaly | 5 × 6 | 0.96288733 | DIFF | 0.40204390 |
| dataops | freshness_violation | 5 × 6 | 0.99000000 | DIFF | 0.36736337 |
| dataops | pipeline_failure | 5 × 6 | 0.87667251 | DIFF | 0.24104814 |
| dataops | transform_drift | 5 × 6 | 0.78156957 | DIFF | 0.33794958 |
| s2p | price_variance | 5 × 8 | 0.58933017 | DIFF | 0.30000000 |
| s2p | quantity_mismatch | 5 × 8 | 0.60000000 | DIFF | 0.30000000 |
| s2p | duplicate_risk | 5 × 8 | 0.60000000 | DIFF | 0.30000000 |
| s2p | contract_gap | 5 × 8 | 0.60000000 | DIFF | 0.30000000 |
| s2p | format_compliance | 5 × 8 | 0.60000000 | DIFF | 0.30000000 |

The requested DIFF label uses max_diff>0.01. It does not establish that every action is distinct: Trading trend_following still has identical poor_execution and skip_recommended rows. Two Trading categories and all five Purchasing categories remain entirely collapsed. The regenerated bundle files alone have not replaced these stored checkpoint states.

Trading's post hash c672b63e2d0a… and S2P's 38c5c5d09819… match the supplied post-regeneration snapshot. The TRD-2/S2P-2 read mismatches therefore occur under the documented tensor identities; they are not explained by an unobserved centroid-version change in this collection.

The exporter still cannot certify live AGE, a loaded classifier model, current K learning, or every non-centroid startup state. It explicitly labels live_age_validated=False at copilot-sdk/tests/extract_real_centroids.py:23. Export execution and final artifact checks are recorded in the appendix.

## 5 — Acceptance-gate verdict

The standalone report crashes before printing its gates. The flags below are calculated independently from its successful structured collector output, corrected source wiring, and the **current** narratives.

A full flip contract requires the exact claimed action pair, both surface and final margins >0.05, and the narrative evidence path including intentional empty reads. A full S1 contract requires the claimed action, surface margin>0.3, zero budget and zero attempts; explicit-zero-budget seeds need not emit a classifier label. PAPER_READY requires all 15 full contracts, stable flip margins and zero hurts. DEMO_READY adds K-store and classifier wiring across all five copilots, as requested. These labels concern the supplied showcase gate only, not empirical paper validity.

| Flag | Value | Evidence |
| --- | --- | --- |
| ALL_FLIPS_MATCH | False | 7/10 claimed flips match; Purchasing's two and S2P-2 do not |
| ALL_MARGINS_STABLE | False | Purchasing's two claimed flips have margin 0; all seven successful flips exceed 0.05 |
| K_STORE_EXERCISED | False | Collector injects no K store; inspected K tables are empty |
| CLASSIFIER_MODEL_LOADED | False | All five production constructors use the fallback |
| K_STORE_WIRED_ALL | True | Source helper expansion confirms 5/5 |
| CLASSIFIER_WIRED_ALL | True | Source helper expansion confirms 5/5 |
| HURTS | 0 | No initially seed-correct action becomes incorrect in the budget=2 matrix |
| FULL_CONTRACTS | 10/15 | Action + current narrative + applicable margin/S1 budget requirements |
| ALL_NARRATIVE_READS_MATCH | False | Four flip stories fail: TRD-2, both Purchasing flips, S2P-2 |
| ALL_S1_CONTRACTS_PASS | False | Purchasing's S1 has margin 0, S6, budget 4 |
| PAPER_READY | False | Five scenarios fail their full contracts |
| DEMO_READY | False | Wiring is present, but full showcase contracts do not all pass |
| LIVE_AGE_VALIDATED | False | Existing tool scope is local offline snapshots |

| Copilot | Full contracts | Showcase status under pinned requests | Remaining gate |
| --- | --- | --- | --- |
| SOC | 3/3 | READY for inspected geometry/evidence and explicit budget contracts | Shared tooling must validate actual wiring before a production certification |
| Trading | 2/3 | BLOCKED | TRD-2's second read is empty timing, not regime |
| Purchasing | 0/3 | BLOCKED | Collapsed geometry prevents flips and high-margin S1 |
| DataOps | 3/3 | READY for inspected geometry/evidence and budget=2 flips | Shared tooling fidelity; omitted budgets change narrative coverage |
| S2P | 2/3 | BLOCKED | S2P-2 stays flag_leakage and misses volume context |

No copilot receives a live-production certification from these offline tools. “READY” above is deliberately scoped to the component/showcase contract that was actually exercised.

## 6 — Comparison with Sep 11

| Measure | Sep 11 original | Sep 12 resweep | Assessment |
| --- | --- | --- | --- |
| Exact action-pair matches | 5/15 | 12/15 | Improved |
| Claimed flips achieved | 1/10 | 7/10 | Improved, with revised Trading targets |
| Successful flips with final margin>0.05 | 1 | 7 | Improved |
| Full current contracts | Original action count was not full-contract readiness | 10/15 | Now separates narrative and S1 behavior |
| S1 high-margin/no-read contracts | Only S2P fully met the original behavior | SOC, Trading, DataOps and S2P pass | Improved; Purchasing still fails |
| K store wiring | 0/5 | 5/5 in production source | Improved; collector detection/exercise not updated |
| Learned K data in inspected stores | None reported | 0 rows in all five dedicated stores | No demonstrated improvement |
| Classifier wiring | 3/5 | 5/5 | Improved; fallback only |
| Classifier models loaded | 0/5 | 0/5 | Unchanged |
| L5 centroid overlay in export | Omitted | Applied with hashes and row counts | Improved |
| Trading geometry | All categories collapsed in export | Partially differentiated by L5; two categories still collapsed | Improved but incomplete |
| Purchasing geometry | All categories collapsed | All categories collapsed | Expected blocker unchanged |
| Integration suite | 14 passed / 17 failed | 23 passed / 8 failed | Improved; residual failures include stale harness expectations |
| Report generator | Completed its report and gates | Crashes on renamed Trading test reference | Tooling regression after TEST-ALIGN |
| Hurts | 0 | 0 | Unchanged |
| PAPER_READY / DEMO_READY | False / False | False / False | Acceptance gate remains open |

Original evidence: copilot-sdk/docs/quality/vld_astra_sweep_report_2026-09-11.md:267–286, :335–351 and :358–386. This is not a same-contract efficacy comparison: Trading's targets changed from poor_execution/skip_recommended to partial_execution; its S1 changed to strong_execution. SOC-2 changed from history recovery to identity recovery. These are disclosed narrative revisions, not proof of improvement against the original untouched task set.

## 7 — Remaining blockers and unexpected findings

### Per-copilot blockers

1. **Trading — TRD-2 does not read its claimed regime evidence.** It flips after portfolio evidence, but Q recomputation chooses timing dimension 3 next, where evidence is None. After the first read, Q_3=0.108880, Q_6=0.092792 and Q_1=0.085024; regime is not the next choice. Source algorithm: copilot-sdk/copilot_sdk/scoring/investigation.py:131–139; expected story: copilot-sdk/apps/trading/backend/app/vld_preseed.py:33. Snapshot :240 reports 2→1 and final margin 0.575971; the current real loop yields 2→3 and 0.42628282.
2. **Purchasing — expected collapse remains.** Both flip vectors and S1 score with margin zero. Loading a differentiated bundle artifact into a file is not the same as loading it into the scorer's selected store. No preseed-only vector change can separate identical action rows. Sources: current category table and vld_validation_report.py:211–226; scoring distances at investigation.py:66–80.
3. **S2P — S2P-2 still does not flip.** After contract evidence, Q_1=0.1998, Q_3=0.18, Q_6=0.17168 and Q_5=0.16. The second read is pricing, not volume. It remains flag_leakage with margin 0.89718343. Current narrative: s2p-copilot/backend/app/vld_preseed.py:114; snapshot prediction :272 instead reports 0→5 and auto_approve.
4. **SOC and DataOps — no pinned-scenario contract blocker found**, but actual production K/classifier injection and live stores are not exercised by the sweep. Omitted budgets also differ from the pinned two-read demonstrations.

### Shared validation gaps

- **Stale TRD-1 assertion:** current narrative 2(None)→1 is satisfied, while integration test_trading_thesis_reversal_real still requires {1,3} at copilot-sdk/tests/test_vld_integration.py:116–118. NARRATIVE_DIMS is stale at vld_validation_report.py:47.
- **Stale S2P dimensions:** collector expects [1,5] for S2P-2 and does not encode its revised [0,5] contract (vld_validation_report.py:50). Updating this expectation alone would not fix the actual 0→1 execution or missing flip.
- **Report generation crash:** vld_validation_report.py:530–531 references removed test_thesis_reversal_flips_enter_to_reduce_or_hedge. Current test is test_thesis_reversal_flips_strong_to_partial at copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:106. The full stdout/stderr, including traceback, is retained below. No stale source was edited.
- **Wiring detection/injection gap:** **kwargs helpers evade AST detection; actual K is never passed to the reconstructed router. See section 3. Correcting the printed boolean alone would not validate the runtime connection.
- **Readiness predicate is incomplete:** vld_validation_report.py:406 and :416 build paper/demo flags from action matches, final margins and hurts, without requiring narrative, S1 behavior or actual wiring. It exposes some additional flags separately at :414–415 but does not include them in readiness. This report uses the user's stricter acceptance definition.
- **Aligned domain tests still use different geometry controls:** Trading's concentration test supplies dimension-specific sigma [0.2,0.08,0.05,…] at copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:125, whereas the production adapter falls back to ones. S2P's price-spike test injects K=[5,0.1,0.1,0.1,0.1,6,0.1,0.1] at s2p-copilot/backend/tests/test_s2p_evidence.py:91 and uses its domain-config geometry through :140–149. Its own comment at :81–85 acknowledges the no-K harness stays flag_leakage. Actual local K stores are empty and yield uniform 0.5, so passing that tuned test does not demonstrate the current production flip.
- **Snapshot provenance label:** applying L5 can make the collector label a restored checkpoint as a bootstrap at vld_validation_report.py:222–223. The recorded tensor hashes/row counts are the reliable distinction.
- **K learning remains unexercised:** all inspected local K tables are empty. This is not repaired merely by constructing the K store.

No remediation was applied. These findings identify the next changes needed to close the acceptance gate; passing domain tests alone is insufficient.

## Appendix A — Baseline and tool execution results

All six requested suites were run with the configured python_expts_venv interpreter. The commands retained the requested pytest timeout; -B, PYTHONDONTWRITEBYTECODE=1 and -p no:cacheprovider suppressed Python/pytest caches. Existing tests retained their own fixture/temp-storage behavior. Baselines ran in separate processes, and the VLD tools ran while the broader baselines completed; final export hashes were checked against the collected scenario state.

| Suite / command target | Passed | Failed | Skipped | Errors | Exit |
| --- | --- | --- | --- | --- | --- |
| SDK: python -m pytest tests/ -q --timeout=120 | 3423 | 10 | 0 | 1 | 1 |
| Trading: python -m pytest apps/trading/backend/tests/ -q --timeout=120 | 1335 | 0 | 0 | 0 | 0 |
| Purchasing: python -m pytest apps/purchasing/backend/tests/ -q --timeout=120 | 741 | 0 | 1 | 0 | 0 |
| DataOps: python -m pytest apps/dataops/backend/tests/ -q --timeout=120 | 382 | 0 | 0 | 0 | 0 |
| SOC backend: python -m pytest tests/ -q --timeout=120 | 2456 | 0 | 16 | 0 | 0 |
| S2P backend: python -m pytest tests/ -q --timeout=120 | 1845 | 0 | 0 | 0 | 0 |
| Dedicated VLD integration: tests/test_vld_integration.py -v --timeout=180 | 23 | 8 | 0 | 0 | 1 |

The dedicated integration run is also included in SDK root coverage; it is not an additional set of unique tests. All five copilot backend suites completed without failures. Seventeen skipped tests are not counted as passed.

### SDK failures outside the eight VLD diagnostics

| Test / fixture | Full-suite observation | Isolated follow-up | Disposition |
| --- | --- | --- | --- |
| tests/test_evolution_telemetry.py::test_summary_event_types_valid | psycopg.OperationalError: server closed the connection unexpectedly, during an EvolutionEvent query | 1 passed, 16 warnings in 20.34s | Not reproduced in isolation; full-suite failure retained |
| tests/test_rl_evolution_matrix.py::test_t_outcome[purchasing] | Expected after == before + 1; actual 1 == (1 + 1) was false | 1 passed, 4 warnings in 3.85s | Not reproduced in isolation; cause not established |
| tests/graph/conftest.py:48, age_test_graph teardown; reported against tests/transfer/test_warm_start.py::test_input_centroids_are_not_mutated | Connection closed unexpectedly while executing LOAD 'age' during session teardown | No dedicated fixture-teardown rerun | Baseline error retained; not a centroid-mutation assertion failure |

Sources: copilot-sdk/tests/test_evolution_telemetry.py:131 and :157; copilot-sdk/tests/test_rl_evolution_matrix.py:188; copilot-sdk/tests/graph/conftest.py:48. The AGE telemetry failure trace also goes through ci-platform/ci_platform/graph/age_client.py:481. Captured logs include persistence-outbox permission warnings, but the recorded failing exceptions are the AGE connection closure and the outcome-count assertion; those warnings are not assigned as the cause.

No full-suite clean rerun was claimed. Passing isolated cases does not clear the original failures or prove their cause. These three baseline observations are additional acceptance risks beyond the five unsatisfied showcase contracts in section 7.

### Per-test VLD results

| Test | Observed result |
| --- | --- |
| test_soc_real_centroid_shape | PASSED |
| test_soc_vld_soc1_real_flip | PASSED |
| test_soc_vld_soc2_empty_branch | PASSED |
| test_soc_s1_real_margin | PASSED |
| test_soc_contrast_values | PASSED |
| test_trading_real_centroid_shape | PASSED |
| test_trading_thesis_reversal_real | FAILED |
| test_trading_concentration_risk_real | FAILED |
| test_trading_s1_no_investigation | PASSED |
| test_purchasing_real_centroid_shape | PASSED |
| test_purchasing_demand_spike_real | FAILED |
| test_purchasing_vendor_cascade_real | FAILED |
| test_purchasing_s1_conservation | FAILED |
| test_dataops_real_centroid_shape | PASSED |
| test_dataops_do1_three_systems_real | PASSED |
| test_dataops_do2_known_pattern_real | PASSED |
| test_dataops_s1_conservation | PASSED |
| test_s2p_real_centroid_shape | PASSED |
| test_s2p_supplier_it_knew_real | PASSED |
| test_s2p_price_spike_real | FAILED |
| test_s2p_s1_conservation | PASSED |
| test_all_copilots_centroid_shapes_valid | PASSED |
| test_all_evidence_providers_implement_protocol | PASSED |
| test_all_s1_scenarios_high_margin | FAILED |
| test_no_investigation_hurts | PASSED |
| test_all_flips_robust | FAILED |
| test_real_router_matches_real_investigator[soc] | PASSED |
| test_real_router_matches_real_investigator[trading] | PASSED |
| test_real_router_matches_real_investigator[purchasing] | PASSED |
| test_real_router_matches_real_investigator[dataops] | PASSED |
| test_real_router_matches_real_investigator[s2p] | PASSED |

The six individual scenario failures are TRD-1 (stale narrative assertion), TRD-2 (real narrative mismatch), Purchasing's two flips and S1, and S2P-2 (real action and narrative mismatch). The other two failures aggregate the S1-margin and flip-robustness gaps. Section 1 records each expected/actual action pair, margin, flip and read path; the raw generator output below supplies its original per-case diagnostics.

### Tool completion

| Operation | Result |
| --- | --- |
| python tests/vld_validation_report.py 2>&1 | Exit 1; printed all scenario matrices, then failed in the mock/substitution inventory on a renamed test |
| Existing collect_all(), serialized without print_report | Exit 0; all five domains and 15 scenarios returned; no worker errors |
| python tests/extract_real_centroids.py > real_centroids_v1.json | Exit 0; valid complete JSON; all five copilots and 15 scenarios |
| Export versus scenario collection | All five post_restore_hash values identical |
| Read-only K-store checks | Five existing dedicated K databases, each with zero rows and zero updated rows |
| Supplementary classifier/Q checks | Actual existing classes evaluated without application startup or source changes |

### Export artifact

- Path: copilot-sdk/real_centroids_v1.json
- Extracted timestamp from artifact: 2026-09-12T16:35:45.828784+00:00
- Size: 69657 bytes
- complete: true; errors: {}; scenarios: 15
- Previous file SHA-256: d81e2b17d83b20169a34bf5272886f0e808ba56e6ada86ad4a875054258be1d0
- Current file SHA-256: be3a242656b7375132f21b48b4b2f56ffcd3097fca940e6b1496ef845b6b2303

The JSON file hash includes metadata and current scenario content; use section 4's tensor hashes when comparing geometry. The current post-restore hashes agree with the report collection for all five copilots.

### Source integrity

A before/after inventory hashed every Python file under the three requested repositories, excluding .git, node_modules, __pycache__, .venv and venv. All **2,178** file/path inventories and aggregate hashes matched. This is a Python-source verification; it is not a claim that test temporary storage or all non-Python runtime artifacts were inventoried.

| Repository | Python files | Before/after aggregate SHA-256 | Match |
| --- | --- | --- | --- |
| copilot-sdk | 1173 | 595615cce89a7f8d0fb3c24d4f6ce2fd993f6d6f4e8165ea25b1f47d06f81b05 | YES |
| gen-ai-roi-demo-v4-v50 | 713 | 37def2228848beb29c70d4d557cbd4ee7f06c0cda0fdc605f18d1a4bcac88ae8 | YES |
| s2p-copilot | 292 | 4754a8f209d6eb9f52f10a3d91fdf82e014547e285ea7fb5ea3159b316d2c31b | YES |

| VLD core file | Before/after SHA-256 | Match |
| --- | --- | --- |
| copilot-sdk/copilot_sdk/scoring/investigation.py | a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a | YES |
| copilot-sdk/copilot_sdk/backend/investigation_router.py | f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90 | YES |

No git commands, source edits, test edits, preseed edits or provider edits were made. The permitted centroid export was overwritten and this report was created. Production wiring was read, not changed. Existing tests were run with their existing configuration; the VLD tools used isolated snapshot/outbox handling as implemented.

## Appendix B — Complete validation-generator stdout/stderr

This is the complete captured output of the requested report command, including its terminal traceback. It is preserved as diagnostic evidence. Its wiring booleans, legacy narrative expectations, bootstrap labels, and historical “baseline” text must not override the corrected findings and actual execution counts above. The generator never reached its gate-printing section on this run.

<details>
<summary>Full output — python tests/vld_validation_report.py 2&gt;&amp;1 — exit 1</summary>

~~~~text
# VLD-ASTRA-SWEEP — offline real-component validation

Generated: 2026-09-12T04:42:59.770906+00:00

Scope: real CompoundingScorer and EvidenceProvider code with local checkpoint snapshots and real showcase seed functions. No live AGE or running-app state is certified. Ground truth below means the preseed's claimed action, not an independently verified outcome. All scenario matrix runs request budget=2; omitted-budget router behavior is shown separately.

Authority note: MAP VLD Addendum v12 was not found. The supplied sweep prompt defines the gate; the historical mock audit is `copilot-sdk/docs/quality/frontend_wiring_and_mock_audit.md:21`.

## 1 — Per-copilot scenario matrix

### soc

Centroids: **real preset bootstrap prior**, shape [6, 4, 6]; 0 checkpoints, 0 decisions, 0 verified. L5 rows applied: 0/0; pre/post hashes: e055e9f4733c / e055e9f4733c. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `None`; latest checkpoint: `None`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay.

Evidence scope: real registered showcase evidence; no backing graph/data client; unregistered reads are offline-unavailable. Identical action centroids by category: `{"credential_access": false, "malware_execution": false, "lateral_movement": false, "data_exfiltration": false, "insider_threat": false, "cloud_infrastructure": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-SOC-1 | monitor | 0.11991623 | escalate | 0.18020368 | True | monitor -> escalate | True | privileged_identity_context(0.0005->0.8464) |
| VLD-SOC-2 | monitor | 0.11968118 | escalate | 0.18011947 | True | monitor -> escalate | True | privileged_identity_context(0.2939->0.8699) |
| VLD-SOC-S1 | escalate | 0.66401995 | escalate | 0.66401995 | False | escalate -> escalate | True | none |

**VLD-SOC-1** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:10`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": {"confidence": 0.92, "source": "identity_graph", "value": 0.92}, "1": null, "2": null, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 5, "empty": true}]`. Narrative dimensions: [0]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=escalate. Fragile at <=0.05: False; below 0.02: False.

**VLD-SOC-2** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:30`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": {"confidence": 0.92, "source": "identity_graph", "value": 0.92}, "1": null, "2": null, "3": {"confidence": 0.85, "source": "historical_db", "value": 0.9}, "4": null, "5": null}`

Attempted order: `[{"dim": 2, "empty": true}, {"dim": 0, "empty": false}]`. Narrative dimensions: [2, 0]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=escalate. Fragile at <=0.05: False; below 0.02: False.

**VLD-SOC-S1** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:53`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": null, "1": null, "2": null, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 1, "empty": true}, {"dim": 5, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=0, attempts=0, final=escalate. Fragile at <=0.05: False; below 0.02: False.

### trading

Centroids: **real preset bootstrap prior**, shape [5, 4, 10]; 5 checkpoints, 800 decisions, 223 verified. L5 rows applied: 6/6; pre/post hashes: 2e5b594bb42e / c672b63e2d0a. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\data\trading.db`; latest checkpoint: `{'id': 5, 'created_at': 1700720000.0, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay.

Evidence scope: real registered showcase evidence; no backing graph/data client; unregistered reads are offline-unavailable. Identical action centroids by category: `{"trend_following": false, "mean_reversion": false, "event_driven": false, "income_strategy": true, "scalp_intraday": true}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-TRD-1 | strong_execution | 0.84733296 | partial_execution | 0.49094184 | True | strong_execution -> partial_execution | True | market_regime(0.1681->0.8088) |
| VLD-TRD-2 | strong_execution | 0.98215159 | partial_execution | 0.42628282 | True | strong_execution -> partial_execution | True | position_sizing(0.0066->0.7825) |
| VLD-TRD-S1 | strong_execution | 0.98528817 | strong_execution | 0.98528817 | False | strong_execution -> strong_execution | True | none |

**VLD-TRD-1** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:10`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.9, "source": "correlation_engine", "value": 0.88}, "2": null, "3": {"confidence": 0.85, "source": "momentum_tracker", "value": 0.25}, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 2, "empty": true}, {"dim": 1, "empty": false}]`. Narrative dimensions: [1, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=partial_execution. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**VLD-TRD-2** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:27`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.88, "source": "correlation_engine", "value": 0.78}, "2": {"confidence": 0.92, "source": "portfolio_engine", "value": 0.85}, "3": null, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 2, "empty": false}, {"dim": 3, "empty": true}]`. Narrative dimensions: [2, 1]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=partial_execution. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**VLD-TRD-S1** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:43`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": null, "2": null, "3": null, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 1, "empty": true}, {"dim": 2, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=0, attempts=0, final=strong_execution. Fragile at <=0.05: False; below 0.02: False.

### purchasing

Centroids: **local SQLite checkpoint**, shape [5, 4, 7]; 5 checkpoints, 801 decisions, 457 verified. L5 rows applied: 0/0; pre/post hashes: 78acf27a7535 / 78acf27a7535. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\purchasing\backend\data\purchasing.db`; latest checkpoint: `{'id': 5, 'created_at': 1700720000.0, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay.

Evidence scope: real in-memory showcase seed; same source type supplied by application startup. Identical action centroids by category: `{"protein": true, "produce": true, "dairy": true, "dry_goods": true, "beverages": true}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-PUR-DEMAND-SPIKE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_more -> order_less | False | expected_demand(0.8000->0.8000); day_of_week(0.5000->0.5000) |
| VLD-PUR-VENDOR-CASCADE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_as_planned -> skip | False | expected_demand(0.4000->0.4000); day_of_week(0.5000->0.5000) |
| VLD-PUR-S1-STANDARD | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_as_planned -> order_as_planned | True | expected_demand(0.5800->0.5800); day_of_week(0.5000->0.5000) |

**VLD-PUR-DEMAND-SPIKE** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:63`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.86, "forecast_units": 320, "inventory_units": 38, "safety_stock_units": 90, "source": "demand_forecast", "value": 0.8}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.65, "source": "vendor_tracker", "value": 0.5}, "5": {"backlog_days": 21, "baseline_days": 5, "confidence": 0.9, "current_days": 21, "source": "lead_time_tracker", "stretch_pct": null, "value": 0.25}, "6": {"alternate_lead_days": 2, "alternate_vendor": "Rapid Components", "confidence": 0.8, "premium_pct": 0.08, "source": "vendor_catalog", "value": 0.82}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [5, 6]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed order_more -> order_less; actual order_as_planned -> order_as_planned.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-PUR-VENDOR-CASCADE** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:108`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.7, "source": "demand_forecast", "value": 0.4}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.88, "notes": "Two seal-failure incidents in the last 30 days.", "quality_incidents_30d": 2, "reliability_score": 0.28, "source": "vendor_tracker", "value": 0.72}, "5": {"backlog_days": null, "baseline_days": 7.0, "confidence": 0.85, "current_days": 9.8, "source": "lead_time_tracker", "stretch_pct": 0.4, "value": 0.72}, "6": {"confidence": 0.65, "source": "cost_benchmark", "value": 0.55}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [4, 5]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed order_as_planned -> skip; actual order_as_planned -> order_as_planned.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-PUR-S1-STANDARD** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:140`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.7, "source": "demand_forecast", "value": 0.58}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.65, "source": "vendor_tracker", "value": 0.2}, "5": {"confidence": 0.65, "source": "lead_time_tracker", "value": 0.2}, "6": {"confidence": 0.65, "source": "cost_benchmark", "value": 0.84}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: False; below 0.02: False.

**P0 S1 CONTRACT:** surface margin=0.00000000; omitted-budget allocation=4, situation=S6. Claimed high-margin/no-investigation behavior is not satisfied.

### dataops

Centroids: **real preset bootstrap prior**, shape [6, 5, 6]; 219 checkpoints, 720 decisions, 388 verified. L5 rows applied: 3/3; pre/post hashes: 537b99b6c606 / 7d03df393211. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\dataops\backend\data\dataops.db`; latest checkpoint: `{'id': 219, 'created_at': 1779171270.8414052, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay.

Evidence scope: real fixture loader plus in-memory showcase seed. Identical action centroids by category: `{"schema_change": false, "volume_anomaly": false, "quality_anomaly": false, "freshness_violation": false, "pipeline_failure": false, "transform_drift": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-DO-1 | investigate | 0.11983817 | escalate_to_owner | 0.95639628 | True | investigate -> escalate_to_owner | True | impact_scope(0.1276->0.8382); downstream_urgency(0.6754->0.8290) |
| VLD-DO-2 | refer_to_specialist | 0.70634656 | escalate_to_owner | 0.67379464 | True | refer_to_specialist -> escalate_to_owner | True | recurrence_frequency(0.9189->0.6500); downstream_urgency(0.3112->0.7776) |
| VLD-DO-S1 | auto_approve | 0.99899631 | auto_approve | 0.99899631 | False | auto_approve -> auto_approve | True | none |

**VLD-DO-1** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:11`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": {"change_type": "schema_expansion", "column": "MATKL_V2", "confidence": 0.92, "impacted_systems": ["pricing_engine", "inventory_sync", "billing_api"], "join_fanout_factor": 9.0, "source": "schema_registry", "value": 0.9}, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "degraded", "system": "order_ingestion", "value": 0.45}, "2": {"confidence": 0.85, "known_resolution": null, "pattern": null, "prior_count": 2, "source": "historical_alerts", "value": 0.5006}, "3": {"confidence": 0.88, "downstream_systems": ["pricing_engine", "inventory_sync", "billing_api"], "new_upstream_dependencies": [], "source": "dependency_graph", "upstream_systems": [], "value": 0.85}, "4": {"confidence": 0.82, "correlated_alerts": ["pricing_engine_latency", "inventory_sync_retries", "billing_api_errors"], "source": "alert_correlator", "value": 0.72}, "5": {"affected_systems": ["pricing_engine", "inventory_sync", "billing_api"], "affected_systems_count": 3, "confidence": 0.8, "source": "impact_analysis", "value": 0.84}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 3, "empty": false}]`. Narrative dimensions: [0, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=escalate_to_owner. Fragile at <=0.05: False; below 0.02: False.

**VLD-DO-2** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:12`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "degraded", "system": "billing_api", "value": 0.45}, "2": {"confidence": 0.55, "known_resolution": "Rebuild billing validation cache", "pattern": "billing_quality_drop", "prior_count": 8, "source": "historical_alerts", "value": 0.65}, "3": {"confidence": 0.82, "downstream_systems": ["revenue_mart", "customer_invoices"], "new_upstream_dependencies": ["data_lake_v2"], "source": "dependency_graph", "upstream_systems": ["payments_hourly"], "value": 0.88}, "4": {"confidence": 0.74, "correlated_alerts": ["revenue_mart_missing_rows", "invoice_export_retries"], "source": "alert_correlator", "value": 0.64}, "5": null}`

Attempted order: `[{"dim": 2, "empty": false}, {"dim": 3, "empty": false}]`. Narrative dimensions: [2, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=escalate_to_owner. Fragile at <=0.05: False; below 0.02: False.

**VLD-DO-S1** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:13`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "ok", "system": "staging_etl", "value": 0.92}, "2": {"confidence": 0.85, "known_resolution": null, "pattern": null, "prior_count": 0, "source": "historical_alerts", "value": 0.23465565901226745}, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 4, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S1, budget=0, attempts=0, final=auto_approve. Fragile at <=0.05: False; below 0.02: False.

### s2p

Centroids: **real preset bootstrap prior**, shape [5, 5, 8]; 174 checkpoints, 871 decisions, 160 verified. L5 rows applied: 6/6; pre/post hashes: 683724c09ab9 / 38c5c5d09819. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\data\s2p.db`; latest checkpoint: `{'id': 174, 'created_at': 1785586175.2645347, 'factor_names_hash': '7a56aae292b46ee04a0bb1d71aed2f6b4966478a3d3a4b5b143c80373fc49aa2'}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay.

Evidence scope: real in-memory showcase seed; same source type supplied by application startup. Identical action centroids by category: `{"price_variance": false, "quantity_mismatch": false, "duplicate_risk": false, "contract_gap": false, "format_compliance": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-S2P-1 | hold_for_review | 0.88287659 | auto_approve | 0.90982841 | True | hold_for_review -> auto_approve | True | match_status(0.3906->0.9500); supplier_exception_history(0.4267->0.0300) |
| VLD-S2P-2 | flag_leakage | 0.89089475 | flag_leakage | 0.89718343 | False | flag_leakage -> auto_approve | False | match_status(0.9237->0.9300); amount_variance_ratio(0.1010->0.0500) |
| VLD-S2P-S1 | auto_approve | 0.93648764 | auto_approve | 0.95217192 | False | auto_approve -> auto_approve | True | match_status(0.9420->0.9800) |

**VLD-S2P-1** — seed `s2p-copilot/backend/app/vld_preseed.py:65`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Partial delivery may auto-approve when verified supplier history is clean.", "confidence": 0.9, "contract_ref": "CTR-ASTER-PARTIAL", "coverage_score": 0.95, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-1", "source": "contract_db", "value": 0.95}, "1": {"confidence": 0.75, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-1", "source": "pricing_benchmark", "value": 0.1186}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-1", "source": "invoice_history", "value": 0.0}, "3": {"confidence": 0.8214285714285714, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-1", "partial_delivery_pricing_error_ratio": 3.1, "source": "supplier_history", "trust_score": 0.82, "value": 0.03, "verified_priors": 23}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-1", "payment_terms": "Net 45", "source": "payment_terms", "value": 0.82}, "5": null, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-1", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-1", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 3, "empty": false}]`. Narrative dimensions: [3, 0]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=auto_approve. Fragile at <=0.05: False; below 0.02: False.

**VLD-S2P-2** — seed `s2p-copilot/backend/app/vld_preseed.py:100`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Bulk pricing pass-through activates above 2x forecast volume.", "confidence": 0.9, "contract_ref": "CTR-MERIDIAN-BULK", "coverage_score": 0.93, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-2", "source": "contract_db", "value": 0.93}, "1": {"benchmark_delta_pct": 18.0, "confidence": 0.82, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-2", "sample_size": 41, "source": "pricing_benchmark", "value": 0.05}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-2", "source": "invoice_history", "value": 0.0568}, "3": {"confidence": 1.0, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-2", "source": "supplier_history", "trust_score": 0.926829268292683, "value": 0.07317073170731707, "verified_priors": 41}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-2", "payment_terms": "Net 60", "source": "payment_terms", "value": 0.82}, "5": {"confidence": 0.78, "dimension": 5, "explanation": "Rush order exceeds the 2x bulk-pricing threshold.", "factor_name": "commodity_index_correlation", "invoice_id": "VLD-S2P-2", "source": "demand_forecast", "value": 0.82, "volume_multiplier": 3.0}, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-2", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-2", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [1, 5]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=flag_leakage. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed flag_leakage -> auto_approve; actual flag_leakage -> flag_leakage.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[{"dimension": 5, "factor_name": "commodity_index_correlation", "current_final_factor": 0.0, "nearest_grid_factor": 0.46, "absolute_change": 0.46}]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-S2P-S1** — seed `s2p-copilot/backend/app/vld_preseed.py:141`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Standard matched invoice auto-approval.", "confidence": 0.95, "contract_ref": "CTR-NORTHSTAR-STANDARD", "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-S1", "source": "contract_db", "value": 0.98}, "1": {"confidence": 0.75, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-S1", "source": "pricing_benchmark", "value": 0.0716}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-S1", "source": "invoice_history", "value": 0.0253}, "3": {"confidence": 1.0, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-S1", "source": "supplier_history", "trust_score": 0.9875, "value": 0.0125, "verified_priors": 80}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-S1", "payment_terms": "Net 45", "source": "payment_terms", "value": 0.82}, "5": null, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-S1", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-S1", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 5, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S1, budget=0, attempts=0, final=auto_approve. Fragile at <=0.05: False; below 0.02: False.

## 2 — Summary

| Copilot | Scenarios | Flips claimed | Flips actual | Match | Mismatch | Fragile |
| --- | --- | --- | --- | --- | --- | --- |
| soc | 3 | 2 | 2 | 3 | 0 | 0 |
| trading | 3 | 2 | 2 | 3 | 0 | 0 |
| purchasing | 3 | 2 | 0 | 1 | 2 | 2 |
| dataops | 3 | 2 | 2 | 3 | 0 | 0 |
| s2p | 3 | 2 | 1 | 2 | 1 | 0 |
| TOTAL | 15 | 10 | 7 | 12 | 3 | 2 |

## 3 — K store and classifier status

| Copilot | K store wired | K has data (local) | Classifier wired | Model loaded | Fallback | Source |
| --- | --- | --- | --- | --- | --- | --- |
| soc | False | False | False | False | fixed default budget; no classifier | gen-ai-roi-demo-v4-v50/backend/app/main.py:245 |
| trading | False | False | False | False | fixed default budget; no classifier | copilot-sdk/apps/trading/backend/app/main.py:561 |
| purchasing | False | False | True | False | heuristic d_min classifier | copilot-sdk/apps/purchasing/backend/app/main.py:841 |
| dataops | False | False | True | False | heuristic d_min classifier | copilot-sdk/apps/dataops/backend/app/main.py:949 |
| s2p | False | False | True | False | heuristic d_min classifier | s2p-copilot/backend/app/main.py:339 |

Classifier heuristic: `copilot-sdk/copilot_sdk/scoring/situation_classifier.py:122`; model load: line 95. SOC/Trading have no classifier; high margin alone does not suppress their default budget. K updates require a connected SQL store (`copilot-sdk/copilot_sdk/scoring/investigation.py:194`).

## 4 — Mock divergence inventory

The only MockEvidenceProvider call sites found in SDK/app/SOC/S2P test directories use synthetic SDK d1/cat inputs. Those inputs have no real scenario join, so a numerical delta or substituted-test pass claim would be fabricated. All call sites are listed below, including the client fixture used by router tests.

| Copilot | Test/source | Dim/mock payload | Real value | Delta | Flag |
| --- | --- | --- | --- | --- | --- |
| SDK generic | test_investigate_reads_highest_Q_first (copilot-sdk/tests/test_investigation.py:142) | {expected: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_stops_at_budget (copilot-sdk/tests/test_investigation.py:148) | {i: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'} for i in range(6)} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_skips_none_evidence (copilot-sdk/tests/test_investigation.py:154) | {1: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_records_flips (copilot-sdk/tests/test_investigation.py:162) | {0: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}, 1: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_recomputes_Q_each_step (copilot-sdk/tests/test_investigation.py:189) | {i: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'} for i in range(6)} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_evidence_provider_protocol_runtime (copilot-sdk/tests/test_investigation.py:81) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | Protocol assertion passes for all five real classes; numeric comparison N/A |
| SDK generic | test_investigate_returns_trace (copilot-sdk/tests/test_investigation.py:133) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_contrast_strip (copilot-sdk/tests/test_investigation.py:169) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_gated_vs_raw_update (copilot-sdk/tests/test_investigation.py:182) | evidence | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_gated_vs_raw_update (copilot-sdk/tests/test_investigation.py:183) | evidence | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | evidence_factory; fixture consumers: test_router_health:294, test_router_investigate:300, test_router_contrast_fields:308, test_router_with_budget:322, test_router_action_changed_flag:328 (copilot-sdk/tests/test_investigation.py:287) | {0: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}, 1: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_router_no_evidence (copilot-sdk/tests/test_investigation.py:316) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |

The five domain evidence suites already use real provider classes. Their significant substitutions concern geometry, sigma, K weights, or S1 vectors; replacing a provider alone would leave those substitutions intact.

Traceback (most recent call last):
  File "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\tests\vld_validation_report.py", line 554, in <module>
    print_report(collect_all())
  File "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\tests\vld_validation_report.py", line 530, in print_report
    table(["Copilot", "Test", "Actual substitution", "Source"], [
                                                                ^
  File "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\tests\vld_validation_report.py", line 531, in <listcomp>
    [domain, name, gap, reference(BACKENDS[domain] / f"tests/test_{domain}_evidence.py", f"def {name}(")]
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\tests\vld_validation_report.py", line 58, in reference
    raise ValueError(f"Source contract changed: {path}: missing {needle!r}")
ValueError: Source contract changed: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\tests\test_trading_evidence.py: missing 'def test_thesis_reversal_flips_enter_to_reduce_or_hedge('

~~~~

</details>

