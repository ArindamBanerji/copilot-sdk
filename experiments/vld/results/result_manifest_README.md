# Result manifest — paper v7.3

1101 rows: 617 source-derived metrics and 484 paper numeric-claim occurrences. All 40 pre-existing experiment JSONs were parsed; inventory and hashes below.

## Metric contract

- **routing_quality**: informative reads / total actual reads; source oracle determines informativeness.
- **category_accuracy**: count(predicted category == true category) / evaluated decisions.
- **action_accuracy**: count(predicted final action == verified action) / evaluated decisions; label_source specifies synthetic verification.

These metrics routinely disagree. In paper §4.4 / RI-1, Static+K leads routing (60.8% versus RNN+K 56.6%), but RNN+K leads action accuracy (78.2% versus 75.2%). Routing quality is not category accuracy. A routing lift in pp is 100 times a difference; a relative lift is 100 times a ratio minus one.

## Provenance and coverage

Source-derived rows retain JSON pointers (or CSV row numbers) in label_source. The fixture column identifies the actual fixture or exported geometry plus synthetic generator. KE/RI/RV use real_centroids_v1.json; detailed generator protocol and seed provenance remain in the cited result artifact. PAPER-EXTERNAL uses ../gen-ai-roi-demo-v4-v50/backend/support/setup/zero_day_decisions_v5.json. N_train is per seed; N_test is pooled endpoint evaluation count unless a row explicitly describes episodes. Fixed K arms share the stream without updates. Offline training budgets do not equal evaluation acquisition budgets.

PAPER-CLAIM rows preserve each numeric occurrence plus its full line, including ranges and ratios. They are an exhaustive claim ledger, not additional experiment results. UNVERIFIED means no independent result mapping for that line has been established; it is not an evidence tier upgrading the claim. ILLUSTRATIVE timing/dollar assumptions and PLANTED FIXTURE walkthrough arithmetic are retained separately. Equations and tensor dimensions are configuration facts, not accuracy estimates. Bibliographic dates and structural numbers may appear in the conservative line ledger but are never treated as measurements. Changelog repeats are excluded.

Astra CSVs are explicitly paper-table transcriptions, not fresh experimental confirmation. No raw execution provenance for the 57:0 count was recovered here. Claims such as 15 configurations / 375 cells, twelve killed alternatives, the naive-abstention 86% / 17.6% / 21.6%, the walkthrough 0.624375 threshold and calendar estimates remain claim-ledger entries unless separately sourced. This manifest exposes unresolved provenance rather than inventing it.

## Conflicts and unsupported equivalences

1. KE-1/all-five/routing_relative_lift_pct: headline and §5 give +17–43%; §4.1 and §8 give +5–43%. Saved endpoints give 4.84–43.18%. SAME experiment and metric; S2P omitted by the headline range.
2. KE-1/all-five/action_lift_pp: headline/§2 give +14–32pp; §4.1 endpoints give 6.0–32.0pp (S2P +6pp). SAME cohort and metric.
3. KE-1/R2 taxonomy: '+3–21%' in §4.4 conflates percentage points with relative percentages; the endpoint routing gaps span +3–21pp, while relative lifts span +5–43%.
4. KE-1/§5 absolute ranges 46–63% (without K) and 59–81% (with K) do not match the §4.1 five-copilot endpoint ranges 44–69% and 63–81%. No separate cohort is identified there.
5. ASTRA/B3 saves:hurts: 57:0 is supported by the transcribed domain counts. 114:1 is not an equivalent raw count ratio; no documented smoothing/accounting derivation was found. Do not substitute it for saves or hurts.
6. GAP-2/dataops/final_d_min/coverage=0.9/action_accuracy_on_acted: §4.2 claims 81.3%, saved JSON gives 82.4889%. Corresponding reported lift also needs recalculation.
7. GAP-2/dataops/final_d_min/coverage=0.5/action_accuracy_on_acted: §4.2 claims 94.0%, saved JSON gives 98.0800%. Corresponding reported lift also needs recalculation.
8. GAP-2/purchasing/final_d_min/coverage=0.9/action_accuracy_on_acted: §4.2 claims 83.6%, saved JSON gives 81.5111%. Corresponding reported lift also needs recalculation.
9. GAP-2/purchasing/final_d_min/coverage=0.5/action_accuracy_on_acted: §4.2 claims 98.0%, saved JSON gives 100.0000%. Corresponding reported lift also needs recalculation.
10. GAP-2/soc/final_d_min/coverage=0.9/action_accuracy_on_acted: §4.2 claims 95.6%, saved JSON gives 97.6889%. Corresponding reported lift also needs recalculation.
11. RI-7/category-adaptive/starvation_rate: §4.1 implies zero starvation on all five copilots. Saved final rates are 0% for Trading, DataOps and SOC, 1.1429% Purchasing and 0.5% S2P; Trading 74.8% routing / 0% starvation is supported. The saved keep verdict is false under its full preregistered criterion.

## Differences that are not conflicts

- §9 full-fixture majority is 163/543 = 30.02%; the held-out training-majority control is 46/143 = 32.17%. Different cohorts.
- §9 VLD 372/543 = 68.51% and held-out VLD 98/143 = 68.53% use different cohorts. Neither is informative-read routing_quality.
- Historical VLD action accuracy 31.31% uses all 543 fixture-vote labels; held-out L3 is 26.57%, held-out L2 is 30.77%. Different cohort/budget.
- The old external harness calls centroid-teacher agreement action_accuracy. This manifest renames that metric teacher_action_agreement and maps fixture_action_accuracy to action_accuracy. Those fixture labels are synthetic votes, not customer-verified outcomes.
- GAP-2 synthetic post-investigation calibration is not the historical 543-alert SOC cohort; its own protocol explicitly denies a matched causal comparison with naive B7.
- The 57:0 B3 constructed cohort differs from the frontier B2 cohort; neither can be substituted for the other.
- Raw and normalized Q results have distinct experiment IDs; changing normalization is not a contradictory measurement.

## Parsed JSON inventory

| Result | Bytes | SHA-256 | Top-level fields |
|---|---:|---|---|
| experiments/vld/budget_accuracy_frontier.json | 68764897 | `26e56d19a8bb60a5e1453edf81c52bf738ee91eb39a1c20d72b70fdf06f5a672` | protocol, source_hashes_before, copilots, rows, checks, source_hashes_after |
| experiments/vld/data/dataops_stage1.json | 861992 | `9c2b488d9f4bb5aab35bd797316dc58d3186e08318f47ba4fefd8b80fd1cf362` | _header, _spec, _stage, provenance, _generation_contract, _scoring_contract, _reconciliations, _evaluation_contract |
| experiments/vld/data/purchasing_stage1.json | 720113 | `bc00bc78c2b4f87867752c9dbdaf0fb87800fbf63b76ab3799f97d22883c9788` | _header, _spec, _stage, provenance, _design_notes, _proxy_scoring_contract, _evaluation_contract, _validation |
| experiments/vld/data/s2p_stage1.json | 925199 | `ddbe8dce7d9e9185caf1c2af35fb8679858d7cc7f068b7dc22acf0a305a112d0` | _header, _spec, _stage, provenance, _generation_notes, _evaluation_contract, scenarios, _validation |
| experiments/vld/data/soc_stage1.json | 1413641 | `af9710f3b058f22724395043a6ab63efc518951788973df790bffc83aa29bd20` | _header, _spec, _stage, provenance, _generation_notes, _scoring_reference, _rho_contract, _evaluation_contract |
| experiments/vld/data/trading_stage1.json | 804651 | `e1898bcc03bdf2f77e562a6697f82c1bf861dd816fc9406b16c69d658e643e8d` | _header, _spec, _stage, provenance, _generation_contract, scenarios, _validation_summary |
| experiments/vld/gap1_adaptive_halting.json | 30186803 | `8a392bd2736fbb0ccb8f5df7d0401ef0e842a06c0ba4ef7bc28f666b2f9176af` | experiment, protocol, source_hashes_before, copilots, rows, checks, headline, source_hashes_after |
| experiments/vld/gap2_abstention_curve.json | 15422224 | `24efe59776b9231dfa8ec19648a3e4915f5c6a7eca7f67d8060cbd8b5f4b095e` | experiment, evidence_tier, protocol, export_provenance, centroid_sha256, source_hashes_before, expected_hash_note, copilots |
| experiments/vld/k_learning_curve_cross_copilot_summary.json | 11159 | `8c47fa4cd75b55f0b955fcceeb884de122701024c2af64aa95de65b0c0b89fed` | protocol, copilots, cross_copilot |
| experiments/vld/k_learning_curve_dataops_extended.json | 72604 | `6acc6b4dbe1028c9c3650419054fac8ee2cc9402d8d12f10fe7447eee742f705` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, dimension_sources, total_decisions |
| experiments/vld/k_learning_curve_purchasing.json | 25436 | `5990c5297f6de547fa9882e8d908cc1abb1a5c59ea51df54c482c6c42948f23c` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, tensor_shape, tensor_cells |
| experiments/vld/k_learning_curve_results.json | 26853 | `a36b76d6f3d4080869e6257638987ce16911759d4860c73f5335298e8895c52e` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, dimension_sources, total_decisions |
| experiments/vld/k_learning_curve_s2p.json | 28554 | `5b1d0151c98fc45f574499e207b88fa89f2dd3ffc5ed535e42d221dc3d716300` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, tensor_shape, tensor_cells |
| experiments/vld/k_learning_curve_soc.json | 28509 | `8404919da9c556123161287bf06f2802c24be57134073b36cbde9578d4139691` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, tensor_shape, tensor_cells |
| experiments/vld/k_learning_curve_trading.json | 33376 | `16d4936ff2f8e45b62b35f70db074c638b143aed671cccab78a6a799aecb2872` | copilot, geometry_hash, centroid_source, category_names, action_names, factor_names, tensor_shape, tensor_cells |
| experiments/vld/ke4_distribution_sensitivity.json | 1159254 | `99cbb0c77c4da0a7e218cf749bf349c1840049c581d6d49666b1ff5e7976ab14` | protocol, results, summary, verdict |
| experiments/vld/ke4_distribution_sensitivity_results.json | 248898 | `5aaf07f011dfa21130df91034f90ad43a6bcf474edec6fb9486584b606643035` | protocol, results, summary, verdict |
| experiments/vld/ke5_conservation_interaction.json | 1218993 | `25861bdae77e4ff8da12d14d266912d9ed3b3f8fcb60112b0a6e87abb1c1dd8a` | protocol, results, summary |
| experiments/vld/ke5_conservation_interaction_results.json | 190373 | `4f10f9025551d77b873435ad8bf83ccba9a08a77149afb29359a70ff3e1509f5` | protocol, runs, summary |
| experiments/vld/q_term_ablation.json | 36765517 | `047170eaa1f32a944c3cb9a9bf2b9a8d78b7e4f080ecb3aacb5cfc13886cb76a` | experiment, protocol, source_hashes_before, variants, cohorts, rows, comparisons, post2_verdict |
| experiments/vld/q_term_ablation_normalized.json | 75440267 | `c3c498ce29ca6d61aa1ee8da37288a54cf757f454a23fc081f9d18105ff3f247` | experiment, protocol, source_hashes_before, results, cohorts, rows, representative_decision, normalization_summary |
| experiments/vld/results/external_baseline.json | 238253 | `e7e63dc33616ab4e41ad464bbb6ed52c94a2263b768b4d2574179032c39140b2` | fi_routing, fixture_size, historical_reproduction, label_diagnostics, linucb, majority, protocol, recommended_paper_claim |
| experiments/vld/results/external_baseline_full.json | 194463 | `58f7f7199d88cbcd91d3f72265429abc003e823e5fda61b3f9492295afc231fa` | list |
| experiments/vld/results/external_baseline_full_audit.json | 326964 | `145d6db3e8a3e19ee1918c0f67b4a5144c3cf3fb2be791f40807bd5d9cdb7c87` | workspace_integrity_at_task_end, protocol_version, adaptive_scalar_sensitivity_complete, banked_policy_matched_feature_comparison, limitation, script_sha256, seed, preregistered_ranges |
| experiments/vld/ri1_routing_k_interaction.json | 2770861 | `0db824e06fe9aa96567941db0ce7c2024087416166d2850837a5d89c5d09ab5d` | design, protocol, results, interaction_effect |
| experiments/vld/ri2_ucb_sweep.json | 6282159 | `51b625045cb5ce657817e1461a92d65c7046f59e78f83948598988c35e0f5e64` | protocol, results, pareto_frontier |
| experiments/vld/ri3_hybrid.json | 6261867 | `4edb2cda3189a296e9eb8def3a90efd7dec92fb49b67eaddc9a939a8dd20e553` | protocol, results |
| experiments/vld/ri4_cross_copilot_transfer.json | 1901616 | `c902da9d80a0f3ffd7515a7fc8fa5568cce53a7d18ec282037bcf32fb76ff0c5` | protocol, results |
| experiments/vld/ri5_rich_k_state.json | 52318219 | `19f6d380887c2878a7b254bc595f819abf0da1c03c710edc71a85816dc188d5a` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/ri6_temporal_decay.json | 13903137 | `68390b0566a337bfdc06a56c3aaacaf585a01485635b9b6124ae1d366ba3fe2b` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/ri7_category_conditional.json | 52234246 | `fb1735f5f113eddf3653af200b7667f71d06dd8ddf288f05ca3a513fd2fccc51` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/ri8_sequence_aware.json | 26706687 | `dba4bf360c3b95725cdcfec763bb0f40c72ad45d8c2938b5784080e434f592ae` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/ri9_regime_indexed.json | 13035976 | `f53ba027c75ce06c90d7a0644faa71b3f3e63308465258e296d68f69800445e9` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/rv0_gru_ablation_results.json | 87259 | `db667e1da0b1e1aec840694be3e6f0e8b9ac42b214be708c4a039b31dc03697e` | variants, copilot, budget, seeds, total_decisions, checkpoint_interval, evaluation_scenarios_per_checkpoint, factor_names |
| experiments/vld/rv1_bandit_results.json | 47864 | `91f11697b02886051fe02d966587089670c786fe2a2570099afdc90756e6e1f4` | variants, copilots, budget, seeds, total_decisions, checkpoint_interval, evaluation_scenarios_per_checkpoint, results |
| experiments/vld/rv4_risk_sensitive.json | 87861603 | `ea52255dc48dc7810e6a1249275758cf679573f8e81622c2f0ec73d765d317c9` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/rv4_risk_sensitive_results.json | 1869079 | `fa147ef148485c831845c55877f25ffd6cbe989ec40c94017322f027d71b4887` | protocol, results, summary |
| experiments/vld/rv5_hierarchical.json | 34645688 | `be42aa3cdd755fed86bf9ce09b26846895d3d63c2b02bd86071de752a4d253eb` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/rv8_adaptive_q.json | 13372235 | `36057ab90e505406ce763ba710a087aab2cdb04bb440c8dc04b09714d0f2706a` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |
| experiments/vld/rv9_mcts.json | 10074966 | `64d897c5c54b9ff41212d942ef2d1acf4d8effe3de0955351eacc2a64f562f8a` | experiment, protocol, notes, configs, results, verdict, source_hashes_before, source_hashes_after |

## Numeric paper-line ledger

| Line | Section | Classification | Tokens (original units) |
|---:|---|---|---|
| 14 | Headline | UNVERIFIED | +17 |
| 14 | Headline | UNVERIFIED | 43% |
| 14 | Headline | UNVERIFIED | +14 |
| 14 | Headline | UNVERIFIED | 32 |
| 14 | Headline | UNVERIFIED | 5 |
| 14 | Headline | UNVERIFIED | 5 |
| 16 | Headline | UNVERIFIED | 1 |
| 19 | Headline | UNVERIFIED | 15 |
| 47 | 1. The only axis left | UNVERIFIED | 1 |
| 61 | 2. What RGI is | UNVERIFIED | 10,000 |
| 65 | 2. What RGI is | UNVERIFIED | +14 |
| 65 | 2. What RGI is | UNVERIFIED | 32 |
| 119 | 3. Judgment memory | UNVERIFIED | 500 |
| 149 | 3. Judgment memory | UNVERIFIED | 10,000 |
| 149 | 3. Judgment memory | UNVERIFIED | 1 |
| 158 | 3. Judgment memory | UNVERIFIED | 6× |
| 158 | 3. Judgment memory | UNVERIFIED | 4× |
| 158 | 3. Judgment memory | UNVERIFIED | 6 |
| 158 | 3. Judgment memory | UNVERIFIED | 144 |
| 158 | 3. Judgment memory | UNVERIFIED | 144 |
| 159 | 3. Judgment memory | UNVERIFIED | 6 |
| 160 | 3. Judgment memory | UNVERIFIED | 4 |
| 160 | 3. Judgment memory | UNVERIFIED | 6 |
| 162 | 3. Judgment memory | UNVERIFIED | 500 |
| 162 | 3. Judgment memory | UNVERIFIED | +43% |
| 163 | 3. Judgment memory | UNVERIFIED | 175B |
| 173 | 4.1 It compounds | UNVERIFIED | 500 |
| 173 | 4.1 It compounds | UNVERIFIED | 1 |
| 179 | 4.1 It compounds | UNVERIFIED | 50 |
| 179 | 4.1 It compounds | UNVERIFIED | 0.42 |
| 179 | 4.1 It compounds | UNVERIFIED | 0.40 |
| 179 | 4.1 It compounds | UNVERIFIED | 0.56 |
| 179 | 4.1 It compounds | UNVERIFIED | 0.52 |
| 180 | 4.1 It compounds | UNVERIFIED | 250 |
| 180 | 4.1 It compounds | UNVERIFIED | 0.56 |
| 180 | 4.1 It compounds | UNVERIFIED | 0.42 |
| 180 | 4.1 It compounds | UNVERIFIED | 0.72 |
| 180 | 4.1 It compounds | UNVERIFIED | 0.58 |
| 181 | 4.1 It compounds | UNVERIFIED | 500 |
| 181 | 4.1 It compounds | UNVERIFIED | 0.63 |
| 181 | 4.1 It compounds | UNVERIFIED | 0.44 |
| 181 | 4.1 It compounds | UNVERIFIED | 0.90 |
| 181 | 4.1 It compounds | UNVERIFIED | 0.58 |
| 183 | 4.1 It compounds | UNVERIFIED | 500 |
| 186 | 4.1 It compounds | UNVERIFIED | 500 |
| 186 | 4.1 It compounds | UNVERIFIED | 2,000 |
| 188 | 4.1 It compounds | UNVERIFIED | 500 |
| 192 | 4.1 It compounds | UNVERIFIED | 0.630 |
| 192 | 4.1 It compounds | UNVERIFIED | 0.440 |
| 192 | 4.1 It compounds | UNVERIFIED | 0.900 |
| 192 | 4.1 It compounds | UNVERIFIED | 0.580 |
| 192 | 4.1 It compounds | UNVERIFIED | +43% |
| 193 | 4.1 It compounds | UNVERIFIED | 0.720 |
| 193 | 4.1 It compounds | UNVERIFIED | 0.510 |
| 193 | 4.1 It compounds | UNVERIFIED | 0.820 |
| 193 | 4.1 It compounds | UNVERIFIED | 0.520 |
| 193 | 4.1 It compounds | UNVERIFIED | +41% |
| 194 | 4.1 It compounds | UNVERIFIED | 0.750 |
| 194 | 4.1 It compounds | UNVERIFIED | 0.630 |
| 194 | 4.1 It compounds | UNVERIFIED | 0.920 |
| 194 | 4.1 It compounds | UNVERIFIED | 0.780 |
| 194 | 4.1 It compounds | UNVERIFIED | +19% |
| 195 | 4.1 It compounds | UNVERIFIED | 0.810 |
| 195 | 4.1 It compounds | UNVERIFIED | 0.690 |
| 195 | 4.1 It compounds | UNVERIFIED | 0.860 |
| 195 | 4.1 It compounds | UNVERIFIED | 0.720 |
| 195 | 4.1 It compounds | UNVERIFIED | +17% |
| 196 | 4.1 It compounds | UNVERIFIED | 0.650 |
| 196 | 4.1 It compounds | UNVERIFIED | 0.620 |
| 196 | 4.1 It compounds | UNVERIFIED | 0.840 |
| 196 | 4.1 It compounds | UNVERIFIED | 0.780 |
| 196 | 4.1 It compounds | UNVERIFIED | +5% |
| 198 | 4.1 It compounds | UNVERIFIED | +5% |
| 198 | 4.1 It compounds | UNVERIFIED | +43% |
| 202 | 4.1 It compounds | UNVERIFIED | 8 |
| 202 | 4.1 It compounds | UNVERIFIED | 48% |
| 203 | 4.1 It compounds | UNVERIFIED | 48% |
| 204 | 4.1 It compounds | UNVERIFIED | 74.8% |
| 204 | 4.1 It compounds | UNVERIFIED | 0% |
| 207 | 4.1 It compounds | UNVERIFIED | 57 |
| 207 | 4.1 It compounds | UNVERIFIED | 0 |
| 207 | 4.1 It compounds | UNVERIFIED | 250 |
| 208 | 4.1 It compounds | UNVERIFIED | 50 |
| 208 | 4.1 It compounds | UNVERIFIED | 57 |
| 210 | 4.1 It compounds | UNVERIFIED | +22.8pp |
| 210 | 4.1 It compounds | UNVERIFIED | 57 |
| 210 | 4.1 It compounds | UNVERIFIED | 0, |
| 211 | 4.1 It compounds | UNVERIFIED | 114 |
| 211 | 4.1 It compounds | UNVERIFIED | 1 |
| 224 | 4.1 It compounds | UNVERIFIED | 13 |
| 224 | 4.1 It compounds | UNVERIFIED | 0, |
| 224 | 4.1 It compounds | UNVERIFIED | 4 |
| 225 | 4.1 It compounds | UNVERIFIED | 13 |
| 225 | 4.1 It compounds | UNVERIFIED | 18 |
| 225 | 4.1 It compounds | UNVERIFIED | 22 |
| 226 | 4.1 It compounds | UNVERIFIED | 10 |
| 226 | 4.1 It compounds | UNVERIFIED | 4 |
| 226 | 4.1 It compounds | UNVERIFIED | 11 |
| 227 | 4.1 It compounds | UNVERIFIED | 2 |
| 232 | 4.1 It compounds | UNVERIFIED | 0 |
| 232 | 4.1 It compounds | UNVERIFIED | 0 |
| 232 | 4.1 It compounds | UNVERIFIED | 4 |
| 232 | 4.1 It compounds | UNVERIFIED | 0 |
| 232 | 4.1 It compounds | UNVERIFIED | 13 |
| 232 | 4.1 It compounds | UNVERIFIED | 0 |
| 233 | 4.1 It compounds | UNVERIFIED | 6 |
| 233 | 4.1 It compounds | UNVERIFIED | 0 |
| 233 | 4.1 It compounds | UNVERIFIED | 12 |
| 233 | 4.1 It compounds | UNVERIFIED | 0 |
| 233 | 4.1 It compounds | UNVERIFIED | 14 |
| 233 | 4.1 It compounds | UNVERIFIED | 0 |
| 234 | 4.1 It compounds | UNVERIFIED | 8 |
| 234 | 4.1 It compounds | UNVERIFIED | 0 |
| 234 | 4.1 It compounds | UNVERIFIED | 12 |
| 234 | 4.1 It compounds | UNVERIFIED | 0 |
| 234 | 4.1 It compounds | UNVERIFIED | 15 |
| 234 | 4.1 It compounds | UNVERIFIED | 0 |
| 235 | 4.1 It compounds | UNVERIFIED | 13 |
| 235 | 4.1 It compounds | UNVERIFIED | 0 |
| 235 | 4.1 It compounds | UNVERIFIED | 18 |
| 235 | 4.1 It compounds | UNVERIFIED | 0 |
| 235 | 4.1 It compounds | UNVERIFIED | 22 |
| 235 | 4.1 It compounds | UNVERIFIED | 0 |
| 236 | 4.1 It compounds | UNVERIFIED | 11 |
| 236 | 4.1 It compounds | UNVERIFIED | 0 |
| 236 | 4.1 It compounds | UNVERIFIED | 11 |
| 236 | 4.1 It compounds | UNVERIFIED | 0 |
| 236 | 4.1 It compounds | UNVERIFIED | 11 |
| 236 | 4.1 It compounds | UNVERIFIED | 0 |
| 239 | 4.1 It compounds | UNVERIFIED | 250 |
| 240 | 4.1 It compounds | ILLUSTRATIVE | 500 |
| 240 | 4.1 It compounds | ILLUSTRATIVE | $7B |
| 244 | 4.1 It compounds | ILLUSTRATIVE | 400 |
| 244 | 4.1 It compounds | ILLUSTRATIVE | 1,200 |
| 244 | 4.1 It compounds | ILLUSTRATIVE | 2 |
| 244 | 4.1 It compounds | ILLUSTRATIVE | -3 |
| 244 | 4.1 It compounds | ILLUSTRATIVE | 1 |
| 245 | 4.1 It compounds | ILLUSTRATIVE | 108 |
| 245 | 4.1 It compounds | ILLUSTRATIVE | 486 |
| 245 | 4.1 It compounds | ILLUSTRATIVE | 3 |
| 245 | 4.1 It compounds | ILLUSTRATIVE | -4 |
| 245 | 4.1 It compounds | ILLUSTRATIVE | 1 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | 66 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | 231 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | 5 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | -8 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | 2 |
| 246 | 4.1 It compounds | ILLUSTRATIVE | -3 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | 25 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | 106 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | 2 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | -3 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | 5 |
| 247 | 4.1 It compounds | ILLUSTRATIVE | -6 |
| 248 | 4.1 It compounds | ILLUSTRATIVE | 4 |
| 248 | 4.1 It compounds | ILLUSTRATIVE | 19 |
| 248 | 4.1 It compounds | ILLUSTRATIVE | 3 |
| 248 | 4.1 It compounds | ILLUSTRATIVE | 6 |
| 253 | 4.1 It compounds | ILLUSTRATIVE | 90 |
| 262 | 4.1 It compounds | ILLUSTRATIVE | 500 |
| 262 | 4.1 It compounds | ILLUSTRATIVE | 90 |
| 263 | 4.1 It compounds | UNVERIFIED | 2 |
| 263 | 4.1 It compounds | UNVERIFIED | -4 |
| 270 | 4.1 It compounds | UNVERIFIED | 1.0 |
| 284 | 4.1 It compounds | PLANTED FIXTURE | $47,200 |
| 285 | 4.1 It compounds | PLANTED FIXTURE | $42,000 |
| 285 | 4.1 It compounds | PLANTED FIXTURE | 12.4% |
| 287 | 4.1 It compounds | PLANTED FIXTURE | 0.5 |
| 287 | 4.1 It compounds | PLANTED FIXTURE | 0.474 |
| 288 | 4.1 It compounds | PLANTED FIXTURE | 0.200 |
| 290 | 4.1 It compounds | PLANTED FIXTURE | 0.82 |
| 292 | 4.1 It compounds | PLANTED FIXTURE | 1.0 |
| 292 | 4.1 It compounds | PLANTED FIXTURE | 0.5 |
| 293 | 4.1 It compounds | PLANTED FIXTURE | 0.16 |
| 293 | 4.1 It compounds | PLANTED FIXTURE | 1.0 |
| 293 | 4.1 It compounds | PLANTED FIXTURE | 0.1998 |
| 293 | 4.1 It compounds | PLANTED FIXTURE | 0.5 |
| 297 | 4.1 It compounds | PLANTED FIXTURE | 0.624375 |
| 297 | 4.1 It compounds | PLANTED FIXTURE | +0.02 |
| 298 | 4.1 It compounds | PLANTED FIXTURE | 0.5 |
| 298 | 4.1 It compounds | PLANTED FIXTURE | 1.0 |
| 298 | 4.1 It compounds | PLANTED FIXTURE | 25 |
| 301 | 4.1 It compounds | PLANTED FIXTURE | 25 |
| 308 | 4.1 It compounds | PLANTED FIXTURE | 0 |
| 315 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 90% |
| 315 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.9% |
| 315 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 81.3% |
| 315 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +3.4 |
| 316 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 75% |
| 316 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.9% |
| 316 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 87.4% |
| 316 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +9.5 |
| 317 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 50% |
| 317 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.9% |
| 317 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 94.0% |
| 317 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +16.1 |
| 318 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 90% |
| 318 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.0% |
| 318 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 83.6% |
| 318 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +6.6 |
| 319 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 75% |
| 319 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.0% |
| 319 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 92.2% |
| 319 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +15.2 |
| 320 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 50% |
| 320 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 77.0% |
| 320 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 98.0% |
| 320 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +21.0 |
| 321 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 90% |
| 321 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 91.5% |
| 321 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 95.6% |
| 321 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +4.1 |
| 322 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 75% |
| 322 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 91.5% |
| 322 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 100.0% |
| 322 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +8.5 |
| 323 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 50% |
| 323 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 91.5% |
| 323 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 100.0% |
| 323 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +8.5 |
| 329 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 90% |
| 329 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 10% |
| 329 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | +3 |
| 329 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 7pp |
| 334 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 86% |
| 335 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 17.6% |
| 335 | 4.2 Governed autonomy (heading missing) | UNVERIFIED | 21.6% |
| 352 | 4.3 The right evidence | UNVERIFIED | 2 |
| 354 | 4.3 The right evidence | UNVERIFIED | 2 |
| 356 | 4.3 The right evidence | UNVERIFIED | 6 |
| 356 | 4.3 The right evidence | UNVERIFIED | 91.7% |
| 357 | 4.3 The right evidence | UNVERIFIED | 10 |
| 357 | 4.3 The right evidence | UNVERIFIED | 90.7% |
| 358 | 4.3 The right evidence | UNVERIFIED | 6 |
| 358 | 4.3 The right evidence | UNVERIFIED | 84.4% |
| 359 | 4.3 The right evidence | UNVERIFIED | 8 |
| 359 | 4.3 The right evidence | UNVERIFIED | 84.1% |
| 360 | 4.3 The right evidence | UNVERIFIED | 7 |
| 360 | 4.3 The right evidence | UNVERIFIED | 79.8% |
| 362 | 4.3 The right evidence | UNVERIFIED | 80 |
| 362 | 4.3 The right evidence | UNVERIFIED | 92% |
| 362 | 4.3 The right evidence | UNVERIFIED | 5 |
| 365 | 4.3 The right evidence | UNVERIFIED | 80 |
| 365 | 4.3 The right evidence | UNVERIFIED | 92% |
| 365 | 4.3 The right evidence | UNVERIFIED | 20 |
| 365 | 4.3 The right evidence | UNVERIFIED | 33% |
| 371 | 4.3 The right evidence | UNVERIFIED | 2 |
| 372 | 4.3 The right evidence | UNVERIFIED | 2.2 |
| 372 | 4.3 The right evidence | UNVERIFIED | 2.7 |
| 372 | 4.3 The right evidence | UNVERIFIED | +5 |
| 372 | 4.3 The right evidence | UNVERIFIED | 10pp |
| 375 | 4.3 The right evidence | UNVERIFIED | 100% |
| 386 | 4.4 The graph is its own memory | UNVERIFIED | 51.9% |
| 386 | 4.4 The graph is its own memory | UNVERIFIED | 60.8% |
| 386 | 4.4 The graph is its own memory | UNVERIFIED | +8.9pp |
| 387 | 4.4 The graph is its own memory | UNVERIFIED | 46.5% |
| 387 | 4.4 The graph is its own memory | UNVERIFIED | 56.6% |
| 387 | 4.4 The graph is its own memory | UNVERIFIED | +10.1pp |
| 388 | 4.4 The graph is its own memory | UNVERIFIED | 46.2% |
| 388 | 4.4 The graph is its own memory | UNVERIFIED | 50.6% |
| 388 | 4.4 The graph is its own memory | UNVERIFIED | +4.4pp |
| 389 | 4.4 The graph is its own memory | UNVERIFIED | 46.0% |
| 389 | 4.4 The graph is its own memory | UNVERIFIED | 48.6% |
| 389 | 4.4 The graph is its own memory | UNVERIFIED | +2.6pp |
| 392 | 4.4 The graph is its own memory | UNVERIFIED | 78.2% |
| 393 | 4.4 The graph is its own memory | UNVERIFIED | 75.2% |
| 393 | 4.4 The graph is its own memory | UNVERIFIED | 3pp |
| 397 | 4.4 The graph is its own memory | UNVERIFIED | 60.8% |
| 404 | 4.4 The graph is its own memory | UNVERIFIED | 60.8% |
| 406 | 4.4 The graph is its own memory | UNVERIFIED | +3 |
| 406 | 4.4 The graph is its own memory | UNVERIFIED | 21% |
| 406 | 4.4 The graph is its own memory | UNVERIFIED | 0 |
| 415 | 4.4 The graph is its own memory | UNVERIFIED | 0 |
| 416 | 4.4 The graph is its own memory | UNVERIFIED | +2.2pp |
| 416 | 4.4 The graph is its own memory | UNVERIFIED | −14.4pp |
| 417 | 4.4 The graph is its own memory | UNVERIFIED | −31pp |
| 417 | 4.4 The graph is its own memory | UNVERIFIED | 15× |
| 418 | 4.4 The graph is its own memory | UNVERIFIED | 36pp |
| 419 | 4.4 The graph is its own memory | UNVERIFIED | 6 |
| 421 | 4.4 The graph is its own memory | UNVERIFIED | 15 |
| 421 | 4.4 The graph is its own memory | UNVERIFIED | 5 |
| 421 | 4.4 The graph is its own memory | UNVERIFIED | 5 |
| 421 | 4.4 The graph is its own memory | UNVERIFIED | 375 |
| 435 | 5. The Q equation | UNVERIFIED | 1 |
| 435 | 5. The Q equation | UNVERIFIED | 100 |
| 435 | 5. The Q equation | UNVERIFIED | 0.001 |
| 437 | 5. The Q equation | UNVERIFIED | 1.0 |
| 442 | 5. The Q equation | UNVERIFIED | 1.0 |
| 449 | 5. The Q equation | UNVERIFIED | 500 |
| 451 | 5. The Q equation | UNVERIFIED | 46 |
| 451 | 5. The Q equation | UNVERIFIED | 63% |
| 451 | 5. The Q equation | UNVERIFIED | 59 |
| 451 | 5. The Q equation | UNVERIFIED | 81% |
| 452 | 5. The Q equation | UNVERIFIED | +17 |
| 452 | 5. The Q equation | UNVERIFIED | 43% |
| 456 | 5.1 Q term ablation | UNVERIFIED | 7 |
| 457 | 5.1 Q term ablation | UNVERIFIED | 0,1 |
| 457 | 5.1 Q term ablation | UNVERIFIED | 5 |
| 458 | 5.1 Q term ablation | UNVERIFIED | 575 |
| 458 | 5.1 Q term ablation | UNVERIFIED | 115,000 |
| 461 | 5.1 Q term ablation | UNVERIFIED | 575 |
| 461 | 5.1 Q term ablation | UNVERIFIED | 115K |
| 463 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 464 | 5.1 Q term ablation | UNVERIFIED | 0.01 |
| 464 | 5.1 Q term ablation | UNVERIFIED | 0.01 |
| 464 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 464 | 5.1 Q term ablation | UNVERIFIED | 0.01 |
| 464 | 5.1 Q term ablation | UNVERIFIED | 10.0 |
| 470 | 5.1 Q term ablation | UNVERIFIED | 70.5% |
| 470 | 5.1 Q term ablation | UNVERIFIED | +4.6pp |
| 470 | 5.1 Q term ablation | UNVERIFIED | 5 |
| 471 | 5.1 Q term ablation | UNVERIFIED | 65.1% |
| 471 | 5.1 Q term ablation | UNVERIFIED | −0.8pp |
| 472 | 5.1 Q term ablation | UNVERIFIED | 69.3% |
| 472 | 5.1 Q term ablation | UNVERIFIED | +0.2pp |
| 476 | 5.1 Q term ablation | UNVERIFIED | 1 |
| 477 | 5.1 Q term ablation | UNVERIFIED | 70.5% |
| 477 | 5.1 Q term ablation | UNVERIFIED | 65.1% |
| 477 | 5.1 Q term ablation | UNVERIFIED | 69.3% |
| 481 | 5.1 Q term ablation | UNVERIFIED | 2 |
| 482 | 5.1 Q term ablation | UNVERIFIED | −0.8pp |
| 485 | 5.1 Q term ablation | UNVERIFIED | 3 |
| 485 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 492 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 499 | 5.1 Q term ablation | UNVERIFIED | 1 |
| 499 | 5.1 Q term ablation | UNVERIFIED | 100 |
| 504 | 5.1 Q term ablation | UNVERIFIED | 1.5 |
| 505 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 507 | 5.1 Q term ablation | UNVERIFIED | 500 |
| 510 | 5.1 Q term ablation | UNVERIFIED | 1.0 |
| 510 | 5.1 Q term ablation | UNVERIFIED | 0.01 |
| 516 | 5.1 Q term ablation | UNVERIFIED | +1.4pp |
| 520 | 5.1 Q term ablation | UNVERIFIED | 0.6 |
| 520 | 5.1 Q term ablation | UNVERIFIED | 19pp |
| 521 | 5.1 Q term ablation | UNVERIFIED | 30 |
| 521 | 5.1 Q term ablation | UNVERIFIED | 37% |
| 527 | 5.2 The trained-router headroom is small and uncharacterized | UNVERIFIED | +1.4pp |
| 531 | 5.2 The trained-router headroom is small and uncharacterized | UNVERIFIED | +1.4pp |
| 547 | 6. One engine, five copilots | UNVERIFIED | 1 |
| 550 | 6. One engine, five copilots | UNVERIFIED | 0.05 |
| 550 | 6. One engine, five copilots | UNVERIFIED | 0.01 |
| 551 | 6. One engine, five copilots | UNVERIFIED | 0.1 |
| 551 | 6. One engine, five copilots | UNVERIFIED | 3.0 |
| 551 | 6. One engine, five copilots | UNVERIFIED | +0.02 |
| 551 | 6. One engine, five copilots | UNVERIFIED | −0.005 |
| 552 | 6. One engine, five copilots | UNVERIFIED | 23.53 |
| 555 | 6. One engine, five copilots | UNVERIFIED | 6× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 4× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 6, |
| 555 | 6. One engine, five copilots | UNVERIFIED | 5× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 4× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 10, |
| 555 | 6. One engine, five copilots | UNVERIFIED | 5× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 4× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 7, |
| 555 | 6. One engine, five copilots | UNVERIFIED | 6× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 5× |
| 555 | 6. One engine, five copilots | UNVERIFIED | 6, |
| 556 | 6. One engine, five copilots | UNVERIFIED | 5× |
| 556 | 6. One engine, five copilots | UNVERIFIED | 5× |
| 556 | 6. One engine, five copilots | UNVERIFIED | 8 |
| 579 | 6. One engine, five copilots | UNVERIFIED | 6 |
| 579 | 6. One engine, five copilots | UNVERIFIED | 10 |
| 584 | 6. One engine, five copilots | UNVERIFIED | 175B |
| 585 | 6. One engine, five copilots | UNVERIFIED | 6× |
| 585 | 6. One engine, five copilots | UNVERIFIED | 4× |
| 585 | 6. One engine, five copilots | UNVERIFIED | 6 |
| 599 | 7. Open source | UNVERIFIED | 1 |
| 610 | 7. Open source | UNVERIFIED | 1 |
| 619 | 7. Open source | UNVERIFIED | 250 |
| 619 | 7. Open source | UNVERIFIED | 500 |
| 621 | 7. Open source | ILLUSTRATIVE | +15.0pp |
| 621 | 7. Open source | ILLUSTRATIVE | +21.0pp |
| 621 | 7. Open source | ILLUSTRATIVE | 1 |
| 621 | 7. Open source | ILLUSTRATIVE | 2 |
| 621 | 7. Open source | ILLUSTRATIVE | -3 |
| 622 | 7. Open source | ILLUSTRATIVE | +14.0pp |
| 622 | 7. Open source | ILLUSTRATIVE | +19.0pp |
| 622 | 7. Open source | ILLUSTRATIVE | 2 |
| 622 | 7. Open source | ILLUSTRATIVE | -3 |
| 622 | 7. Open source | ILLUSTRATIVE | 5 |
| 622 | 7. Open source | ILLUSTRATIVE | -6 |
| 623 | 7. Open source | ILLUSTRATIVE | +12.0pp |
| 623 | 7. Open source | ILLUSTRATIVE | +12.0pp |
| 623 | 7. Open source | ILLUSTRATIVE | 3 |
| 623 | 7. Open source | ILLUSTRATIVE | 5 |
| 624 | 7. Open source | ILLUSTRATIVE | +9.0pp |
| 624 | 7. Open source | ILLUSTRATIVE | +12.0pp |
| 624 | 7. Open source | ILLUSTRATIVE | 3 |
| 624 | 7. Open source | ILLUSTRATIVE | 6 |
| 625 | 7. Open source | ILLUSTRATIVE | −3.0pp |
| 625 | 7. Open source | ILLUSTRATIVE | +3.0pp |
| 625 | 7. Open source | ILLUSTRATIVE | 4 |
| 625 | 7. Open source | ILLUSTRATIVE | 1 |
| 627 | 7. Open source | ILLUSTRATIVE | $7B |
| 635 | 7. Open source | UNVERIFIED | +3pp |
| 636 | 7. Open source | UNVERIFIED | +19pp |
| 636 | 7. Open source | UNVERIFIED | +21pp |
| 656 | 8. What this changes | UNVERIFIED | +5 |
| 656 | 8. What this changes | UNVERIFIED | 43% |
| 656 | 8. What this changes | UNVERIFIED | 500 |
| 657 | 8. What this changes | UNVERIFIED | 1 |
| 666 | 8. What this changes | UNVERIFIED | +3 |
| 666 | 8. What this changes | UNVERIFIED | +21pp |
| 668 | 8. What this changes | UNVERIFIED | 500 |
| 674 | 8. What this changes | UNVERIFIED | 500 |
| 676 | 8. What this changes | UNVERIFIED | 1 |
| 685 | 9. The routing category | UNVERIFIED | 543 |
| 686 | 9. The routing category | UNVERIFIED | 68.5% |
| 686 | 9. The routing category | UNVERIFIED | 30.0% |
| 686 | 9. The routing category | UNVERIFIED | +38.5pp |
| 689 | 9. The routing category | UNVERIFIED | 31.3% |
| 689 | 9. The routing category | UNVERIFIED | 53.8% |
| 695 | 9. The routing category | UNVERIFIED | 2026 |
| 696 | 9. The routing category | UNVERIFIED | 2024 |
| 698 | 9. The routing category | UNVERIFIED | 26 |
| 714 | 9. The routing category | UNVERIFIED | 0.1 |
| 714 | 9. The routing category | UNVERIFIED | 3.0 |
| 744 | 10. What we are *not* claiming | UNVERIFIED | 2 |
| 745 | 10. What we are *not* claiming | ILLUSTRATIVE | $0.9M |
| 745 | 10. What we are *not* claiming | ILLUSTRATIVE | $1.62M |
| 747 | 10. What we are *not* claiming | UNVERIFIED | 86% |
| 749 | 10. What we are *not* claiming | UNVERIFIED | 10.2 |
| 750 | 10. What we are *not* claiming | UNVERIFIED | 0.1 |
| 750 | 10. What we are *not* claiming | UNVERIFIED | 3.0 |
| 751 | 10. What we are *not* claiming | UNVERIFIED | 0 |
| 751 | 10. What we are *not* claiming | UNVERIFIED | −14.4pp |
| 752 | 10. What we are *not* claiming | UNVERIFIED | −31pp |
| 752 | 10. What we are *not* claiming | UNVERIFIED | 15× |
| 752 | 10. What we are *not* claiming | UNVERIFIED | 36pp |
| 754 | 10. What we are *not* claiming | UNVERIFIED | +4.6pp |
| 755 | 10. What we are *not* claiming | UNVERIFIED | −0.8pp |
| 756 | 10. What we are *not* claiming | UNVERIFIED | 575 |
| 778 | 11. Where this stands | UNVERIFIED | 80 |
| 778 | 11. Where this stands | UNVERIFIED | 92% |
| 798 | Appendix A: Equation Reference | DEMONSTRATED | 1 |
| 798 | Appendix A: Equation Reference | DEMONSTRATED | 100 |
| 798 | Appendix A: Equation Reference | DEMONSTRATED | 0.001 |
| 800 | Appendix A: Equation Reference | DEMONSTRATED | 1.0 |
| 803 | Appendix A: Equation Reference | DEMONSTRATED | 0.1 |
| 803 | Appendix A: Equation Reference | DEMONSTRATED | 3.0 |
| 804 | Appendix A: Equation Reference | DEMONSTRATED | +0.02 |
| 804 | Appendix A: Equation Reference | DEMONSTRATED | −0.005 |
| 808 | Appendix A: Equation Reference | DEMONSTRATED | 0.05 |
| 808 | Appendix A: Equation Reference | DEMONSTRATED | 0.01 |
| 808 | Appendix A: Equation Reference | DEMONSTRATED | +1 |
| 808 | Appendix A: Equation Reference | DEMONSTRATED | −1 |
| 811 | Appendix A: Equation Reference | DEMONSTRATED | 23.53 |
| 813 | Appendix A: Equation Reference | DEMONSTRATED | 2 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 6 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 4 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 6 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 144 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 20 |
| 819 | Appendix B: Tensor Shapes | REAL_COMPONENT | 1 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 6 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 6 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 180 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 10 |
| 820 | Appendix B: Tensor Shapes | REAL_COMPONENT | 1 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 8 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 200 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 821 | Appendix B: Tensor Shapes | REAL_COMPONENT | 1 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 4 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 7 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 140 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 3 |
| 822 | Appendix B: Tensor Shapes | REAL_COMPONENT | 1 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 5 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 4 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 10 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 200 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 2 |
| 823 | Appendix B: Tensor Shapes | REAL_COMPONENT | 1 |
| 830 | Appendix C: Evidence Tiers | UNVERIFIED | 57 |
| 830 | Appendix C: Evidence Tiers | UNVERIFIED | 0 |
| 830 | Appendix C: Evidence Tiers | UNVERIFIED | 1 |
| 831 | Appendix C: Evidence Tiers | ILLUSTRATIVE | $0.9M |
| 831 | Appendix C: Evidence Tiers | ILLUSTRATIVE | $1.62M |

Paper SHA-256: `3ad133245b0b6c0e0ea5a391e4b76fa22394c444b54d2340bd27eced59dd35c1`
## C1 / Fig-2b protocol

The new C1 rows use the same ordered 400/143 split. RF/SVM/LinUCB receive the two most frequent advertised dimensions from banked VLD first-two-pattern traces across all 543 alerts, as requested. That selector uses no labels but does use the held-out feature distribution (transductive selection). FI uses the original training RF importance ranking. The adaptive VLD sensitivity admits only two scalar observations via a declared adapter over the original category router; it is not the banked six-surface-feature investigation loop. Original VLD reference bars remain separate; RF(all features) is the final, hatched reference group. See external_baseline_full_audit.json for all traces and exact protocol. Action fitting keeps the original centroid-teacher targets; reported action accuracy uses the historical synthetic fixture votes. Teacher agreement is separately named.

Regenerate: `python -B scripts/build_result_manifest.py`
