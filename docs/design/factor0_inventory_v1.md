# Factor-0 / travel-match reference inventory

**Inventory date:** 2026-08-15  
**Scope:** `copilot-sdk`, `gen-ai-roi-demo-v4-v50`, `s2p-copilot`, `ci-platform`, and `graph-attention-engine-v50`  
**Status:** diagnostic only; no code was changed.

## 1. Executive summary

The live SOC factor-0 contract is `privileged_identity_context` at tensor index
0. This is established independently by the SOC configuration
(`gen-ai-roi-demo-v4-v50/backend/app/domains/soc/config.py:118-127`), the live
factor computer (`.../domains/soc/factors.py:64-73`), and the SDK SOC preset
(`copilot-sdk/copilot_sdk/scoring/presets/soc.py:15-55`).

The scan found **551 matching lines in 132 files**:

| Repository | Matching lines | Files |
|---|---:|---:|
| `copilot-sdk` | 187 | 28 |
| `gen-ai-roi-demo-v4-v50` | 296 | 71 |
| `s2p-copilot` | 12 | 8 |
| `ci-platform` | 7 | 5 |
| `graph-attention-engine-v50` | 49 | 20 |
| **Total** | **551** | **132** |

Primary classification of matching lines (a line can contain more than one
term, but is assigned one primary disposition):

| Classification | Lines |
|---|---:|
| RUNTIME | 22 |
| CONFIG | included with runtime/config file inventory below |
| FIXTURE | 9 |
| TEST | 44 |
| COMMENT | 31 |
| SEED | 46 |
| DOCS | 361 |
| CENTROID | 18 |
| ALIAS | 16 |
| PROVENANCE | 4 |

The large DOCS count includes historical/archive documents and generated
graph reports. It is not evidence that those phrases are active runtime API
contracts.

## 2. Canonical state and design decisions

The two supplied design documents agree on the following:

* `privileged_identity_context` is the canonical factor-0 identifier.
* `travel_match` is retired as the factor-0 identifier, although it remains
  in residual data, aliases, historical documents, and compatibility code.
* `TravelMatchFactor` is not in the active SOC factor configuration. The class
  remains in `domains/soc/factors.py:159-221` and needs a separate deletion or
  retention decision after all references are classified.
* The factor-0 semantic change is substantive: travel/location evidence is not
  equivalent to privileged identity, MFA, title, and device-context evidence.
  Existing evaluation values and μ₀ centroids therefore cannot be declared
  semantically validated merely because their key is renamed.

## 3. Complete source inventory

The following is the complete file/line inventory from the scan. Line lists are
the exact matching lines; the tag after each file is the primary class for the
listed references. `GEN` denotes generated graph artifacts, which should not be
treated as source contracts.

### `copilot-sdk` (187 lines, 28 files)

| File | Matching lines | Class |
|---|---|---|
| `copilot_sdk/framework/provenance.py` | 218 | PROVENANCE |
| `tests/test_migration_live_age.py` | 282 | TEST |
| `docs/design/soc_factor0_reconciliation_pass_v1.md` | 1,12,14-16,21,23,29,31,34,45,49-52,61,63,65,67,71,77,79-81,87,98-99,108,110 | DOCS/ALIAS/CENTROID |
| `docs/design/factor0_design_review.md` | 1,18,23,32,58,68,78-84,94,105,113,117,120,126,149 | DOCS/CENTROID |
| `docs/design/soc_copilot_design_v5_10.md` | 4,553,718-719,1045,1105,1316,1319,1326,1399,1687,1728,1844,1864-1869,1907,2106,2196,2963,3190,3220,3274,4842,4882-4883,5403,5428,5593,5595-5596,5945,6052-6054,6229,6272,6283,6288,6290,6294,6502,6507,6757,6784 | DOCS/CENTROID |
| `docs/design/trading_copilot_product_definition_v1_1.md` | 553,718-719,1045,1105,1316,1319,1326,1399,1687,1728,1844,1864-1869,1907,2106,2196,2963,3190,3220,3274,4842,4882-4883,5403,5428,5593,5595-5596,5998,6009,6014,6016,6020,6029 | DOCS/CONFIG |
| `docs/design/cga_arxiv_short_v7_6.md` | 190,249 | DOCS |
| `docs/design/CI_PLATFORM_INSIGHTS_v39.md` | 311,1174,1194 | DOCS |
| `docs/design/ci_reviews_and_addenda/soc_review_consolidation_v1.md` | 75 | DOCS |
| `docs/design/ci_reviews_and_addenda/demo_scenarios_soc_additions_v1.md` | 69 | DOCS |
| `docs/design/s2p_copilot_unified_v1_3.md` | 207 | DOCS/FIXTURE |
| `docs/design/s2p_fix_b_whatif_phase_e_results_v1.md` | 189 | DOCS/FIXTURE |
| `docs/design/math_synopsis_v18.md` | 1256,1272 | DOCS/CENTROID |
| `docs/dk_runtime_execution_plan_v3.md` | 338,343,405 | DOCS |
| `docs/dk_runtime_execution_plan_v4.md` | 458,463,525 | DOCS |
| `docs/dk_runtime_execution_plan_v5.md` | 530,535,597 | DOCS |
| `docs/dk_runtime_execution_plan_v5_4.md` | 965,970,1032 | DOCS |
| `docs/dk_runtime_execution_plan_v6.md` | 1006,1011,1073 | DOCS |
| `docs/dk_runtime_execution_plan_v6_1.md` | 1014,1019,1081 | DOCS |
| `docs/dk_runtime_execution_plan_v6_3.md` | 1074,1079,1141 | DOCS |
| `docs/dk_runtime_execution_plan_v6_4.md` | 1117,1122,1184 | DOCS |
| `docs/dk_runtime_execution_plan_v6_6.md` | 1731,1736,1798 | DOCS |
| `docs/dk_runtime_execution_plan_v6_7.md` | 1807,1812,1874 | DOCS |
| `docs/dk_runtime_execution_plan_v6_8.md` | 1915,1920,1982 | DOCS |
| `docs/implementation_plans/p43_di_combination_discovery_plan.md` | 135,623 | DOCS |
| `CODE_GRAPH_REVIEW.md` | 135 | DOCS/PROVENANCE |

Additional SDK design references in the scan are the two supplied factor-0
documents above; their line-level residual inventory is authoritative for the
SOC cleanup decision.

### `gen-ai-roi-demo-v4-v50` (296 lines, 71 files)

#### Live runtime, configuration, aliases, provenance, seed, and tests

| File | Matching lines | Class |
|---|---|---|
| `backend/app/domains/soc/config.py` | 160 | CENTROID/COMMENT |
| `backend/app/domains/soc/factors.py` | 159,168,178,221 | RUNTIME |
| `backend/app/framework/provenance.py` | 218 | PROVENANCE |
| `backend/app/routers/evaluation.py` | 22 | ALIAS |
| `backend/app/routers/judgment.py` | 30 | ALIAS |
| `backend/app/services/simulation.py` | 118 | COMMENT |
| `backend/app/services/nl_templates.py` | 58 | RUNTIME/CONFIG |
| `backend/app/domains/soc/situations.py` | 149 | COMMENT |
| `backend/app/data/alert_pool.py` | 5,78,811 | SEED/COMMENT |
| `backend/app/data/soc_eval_scenarios.json` | 8,32,42,44,56,79,101,123,146,169,179,183,193,215,238,260,282,305,329,352,364,375,387,398,420,444,467,490,512,534,556,580,604,627,649,671,693,717,740,763,785,807 | FIXTURE/SEED |
| `backend/seed_neo4j.py` | 1422 | SEED |
| `frontend/src/components/tabs/AlertTriageTab.tsx` | 41,282,908,986 | RUNTIME/COMMENT |
| `frontend/src/components/tabs/SOCAnalyticsTab.tsx` | 81 | RUNTIME |
| `frontend/src/components/tabs/CompoundingTab.tsx` | 418,2860 | RUNTIME/SEED |
| `frontend/src/components/tabs/RuntimeEvolutionTab.tsx` | 96 | RUNTIME |
| `frontend/tests/e2e/checklist.spec.ts` | 118,247 | TEST/COMMENT |
| `frontend/tests/e2e/triage_write_path.spec.ts` | 134 | TEST |
| `backend/tests/test_eval1_soc.py` | 71 | TEST |
| `backend/tests/test_judg1_soc.py` | 65 | TEST |
| `backend/tests/test_privileged_identity_factor.py` | 66,71 | TEST |
| `backend/tests/test_refer_to_analyst.py` | 36,40 | TEST |
| `backend/tests/test_convergence_calendar.py` | 111 | TEST |
| `backend/tests/test_compounding_gate.py` | 71 | TEST |
| `backend/tests/test_nl_templates.py` | 60 | TEST |
| `backend/tests/test_audit_ci_platform.py` | 84 | TEST |
| `backend/tests/test_tab_content.py` | 1404 | TEST/CENTROID |
| `backend/tests/integration/test_w2_read_path.py` | 193 | TEST |

#### Product/design/archive documents

The following files contain the listed legacy factor names or travel scenarios;
all are DOCS unless noted as historical archive material:

`ARCHITECTURE.md:269`; `contracts/api_contracts.yaml:246` (CONFIG/API example);
`backend/CODE_GRAPH_REVIEW.md:534,1813`; `backend/CODEBASE.md:417,1103,1111`;
`backend/REVIEW.md:1160,1234-1235,1364,1371,1377,1389`;
`backend/REVIEW.part3.md:371,445-446,575,582,588,600`;
`backend/FEATURE07_DESIGN.md:36,56`; `docs/gae_design_v10.md:381`;
`docs/math_synopsis_v11.md:456,472`; `docs/PROJECT_STRUCTURE.md:172,546,624`;
`docs/project_status_and_plan_v4_part1.md:141`;
`docs/experiment_reference_catalog_v2.md:344`;
`docs/soc_copilot_design_v5_5_part1.md:463,604-605,796,856,1067,1070,1077,1150,1429,1467,1583,1603-1608,1646,1845,1935,2521,2748,2778,2832`;
`docs/soc_copilot_design_v5_5_part2.md:215,255,776,801,966,968-969`;
`docs/soc_copilot_design_v5_5_part3.md:60,71,76,78,82,91`;
`docs/archive/v3_design_document_v8.md:555,603,620`;
`docs/archive/v3_all_prompts.md:585,662,683`;
`docs/archive/v3_2_refactoring_and_s2p_domain_model_v1.md:135,381,478,714`;
`docs/archive/mvp_sprint_plan_v1.md:134`; `docs/archive/math_synopsis_v9.md:410,428,1040,1072`;
`docs/archive/math_synopsis_v9_1.md:659,677,1363,1395`;
`docs/archive/soc_copilot_design_v3.md:547,551,570,697,740,917,952-953,1159,1184,1328,1330-1331`;
`docs/archive/soc_copilot_design_v5_6_part1.md:82,586-587,787,853,1056,1375,1396,1438,1567,1610,1783,1873,2293,2569,2631`;
`docs/archive/soc_copilot_design_v5_6_part2.md:212,252-253,773,798,963,965-966`;
`docs/archive/temp/soc_copilot_design_v5_6_part2.md:212,252-253,773,798,963,965-966`;
`docs/archive/ci_platform_design_v3.md:164`; `docs/archive/session_continuation_v20.md:314,626`;
`docs/archive/product_strategy_v1.md:142,148,168,190`; `docs/archive/gap_analysis_v4.md:162`;
`docs/archive/experiments_catalog_v8_2_part1.md:201,333`;
`docs/archive/experiments_catalog_v8_2_part2.md:104`;
`docs/archive/experiments_catalog_v8_2_part3.md:1045`;
`docs/archive/soc_copilot_roadmap_v6.md:208`; `docs/archive/sprint55_blocker_prompts.md:198,243,833`;
`docs/archive/demo_blurb_v25.md:207`; `docs/archive/outreach/demo_blurb_v25_updated.md:278`;
`docs/archive/v2.5_v3_design_document_v2.md:293,330`;
`docs/gtm/gtm_pilot_playbook_v1.md:57,70,128,156`; `docs/gtm/gtm_microsoft_analysis_v1.md:79`;
`docs/gtm/gtm_dpa_template_v1.md:29`.

#### Generated SOC graph artifact

`graphify-out/graph.json:6226,6230,6232,6239,98892,99014,99101,99348-99349,99358,99369`
and `graphify-out/soc_triage_source_review_20260609_023852/backend_app_domains_soc_config.py:160`
are GEN/DOCS derivatives of source code, not independent runtime references.

### `s2p-copilot` (12 lines, 8 files)

* `backend/app/framework/provenance.py:50,218` — PROVENANCE/RUNTIME; this is
  S2P's own legacy explainer mapping and is not SOC factor configuration.
* `backend/tests/test_domain_isolation.py:263`,
  `backend/tests/test_s2p_domain_config.py:100`,
  `backend/tests/test_s2p_config.py:45` — TEST; the latter two explicitly
  verify that the retired factor is absent.
* `backend/CODE_GRAPH_REVIEW.md:187` — DOCS.
* `graphify-out/graph.json:4399,4403,4405,54018` and the two
  `graphify-out/cache/ast/*.json` matches — GEN.

### `ci-platform` (7 lines, 5 files)

* `ci_platform/audit/evidence_ledger.py:125` — RUNTIME payload example.
* `ci_platform/onboarding/deployment_qualification.py:29,49` — CONFIG/RUNTIME
  factor allow-list and metadata.
* `tests/test_evidence_ledger.py:13`,
  `tests/test_p28_enrichment_advisor.py:13`,
  `tests/test_sentinel_writeback.py:40,49` — TEST fixtures/assertions.

### `graph-attention-engine-v50` (49 lines, 20 files)

* `gae/calibration.py:112,537,559-571,860` and
  `gae/enrichment_advisor.py:14` — RUNTIME/CONFIG examples and default factor
  names; these are generic GAE factor vectors but use the old SOC vocabulary.
* `gae/ablation.py:39,132` and `gae/snr.py:189` — RUNTIME generic factor-0
  semantics/default naming.
* `tests/test_ablation.py:12,17,28,79`,
  `tests/test_calibration.py:438,445,457,796,902,913,915`,
  `tests/test_diagonal_kernel.py:26,99,107,123,141`,
  `tests/test_kernels.py:335,344`, `tests/test_judgment.py:35`,
  `tests/test_harness_validation.py:50`, and
  `tests/test_soc_integration.py:13,441` — TEST/fixture factor order.
* `docs/math_synopsis_v14.md:1006,1022`,
  `docs/design/math_synopsis_v15.md:1145,1161`,
  `docs/gae_design_v10_6.md:418`, and `CODEBASE.md:348` — DOCS/CENTROID.
* `graphify-out/GRAPH_REPORT.md:170,242`, `graphify-out/graph.json:124,130,6316,6322,12841,12847`, and the three `graphify-out/cache/ast/*.json` matches — GEN.

## 4. External-contract assessment

### API responses

The router scan found no active response serializer emitting `travel_match` as
the canonical response key. The only router hits are the two legacy alias maps:

* `backend/app/routers/evaluation.py:22`
* `backend/app/routers/judgment.py:30`

These are still external compatibility surfaces because older payloads or
persisted evaluation data can be translated through them. They must not be
removed without proving that all persisted readers use the canonical key.

### Frontend

The SOC frontend has one active data-key mapping at
`AlertTriageTab.tsx:41`, mapping the old key to the displayed canonical label,
plus a comment at line 282. It also contains travel-domain UI/situation terms
(`TravelContext`, `travel_login_anomaly`, and travel analytics), which are not
necessarily factor-0 identifiers. The E2E checklist and diagnostic text still
assert/display “Travel Match”; these are test/UI contracts and should be
updated or explicitly retained as historical compatibility behavior.

### Persisted/serialized data

Yes. `backend/app/data/soc_eval_scenarios.json` contains 42 matching lines,
including factor values and factor-name arrays. `contracts/api_contracts.yaml`
also documents a request example with `travel_match`. Existing graph/data
records may outlive source changes; source inventory alone does not prove that
old records have been migrated.

## 5. Compatibility recommendation

Use a **bounded alias deprecation window**, not an immediate hard cutover:

1. Make `privileged_identity_context` canonical for new writes and responses.
2. Continue accepting `travel_match` on input only, with explicit legacy
   provenance/semantic-version metadata.
3. Emit a deprecation signal and measure remaining legacy reads.
4. Re-author or explicitly label travel-derived evaluation fixtures before
   rekeying them as identity-context evidence.
5. Remove the aliases only after persisted-data and client-read checks are
   clean. A versioned endpoint is preferable if external clients cannot be
   inventoried.

Do not silently rename travel-derived values: the supplied design review says
their semantics are not equivalent.

## 6. Dependency graph and risk flags

Recommended order:

1. Decide whether the JSON scenarios remain historical or are re-authored.
2. Add/verify semantic-version or legacy provenance for retained records.
3. Update tests and fixtures to the canonical factor name (or mark legacy
   compatibility tests deliberately).
4. Update the two router aliases and provenance dispatch together; verify both
   canonical and legacy input paths.
5. Review μ₀/factor-0 centroid comments and re-derive them if identity-context
   evidence is unavailable.
6. Remove or re-scope `TravelMatchFactor` only after zero runtime imports and
   instantiations are demonstrated.
7. Update active docs, archive labels, generated graph artifacts, and UI text
   according to their retention policy.

Highest-risk references:

* `evaluation.py:22` and `judgment.py:30`: removing them can break old input.
* `soc_eval_scenarios.json`: a blind key rename can falsely claim semantic
  validation.
* `factors.py:159-221`: the class is source code even though it is not active
  configuration; deletion needs an import/instantiation check.
* `config.py:160` and the duplicated SDK/GAE centroid documentation: labels
  can align while μ₀ still encodes travel priors.
* `AlertTriageTab.tsx:41` and E2E assertions: UI/test contracts may fail after
  a display-key change.
* CI-platform and GAE factor vectors: these are cross-repo consumers and need
  a decision on whether the old name is generic vocabulary or SOC-specific.

## 7. Scan reproducibility

The inventory searched only `.py`, `.md`, `.json`, `.ts`, `.tsx`, `.yaml`, and
`.yml` files and excluded `.git`, `__pycache__`, `node_modules`, and `dist`.
The search terms were case-insensitive:

`travel_match`, `TravelMatchFactor`, `travel_anomaly`, `travel anomaly`,
`frequent traveler`, `travel-match`, `factor-0`, `factor_0`, `factor 0`, and
`factor zero`.

Generated graph artifacts are included in the counts because they are tracked
repository files, but are explicitly marked GEN and should be regenerated only
after source changes. No code files were modified by this diagnostic.
