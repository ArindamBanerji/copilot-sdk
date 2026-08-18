# gpt-5.3 — Demo Scenarios v2.7 × MAP v5.229 Coverage

Read-only diagnostic against:

- `docs/design/product/demo_scenarios_and_usecases_v2_7.md`
- `docs/design/master_action_plan_v5.229_addendum.md`
- `docs/design/master_action_plan_v5.228 (1).md`
- `docs/design/product/copilot_addenda/cross_platform_gap_analysis_memo_v1.md`

## Summary

The v5.229 addendum covers the principal v2.7 demo beats, but coverage is not uniformly LIVE. The existing v5.228 batches cover the shipped mirror, refusal, counterfactual, day-zero, staged-trust, DataOps, and storyboard surfaces. XPLAT-01 through XPLAT-16 add explicit delivery cards for the remaining cross-platform and per-copilot proof layers. The material residual risks are Trading SAFE-2/claim gating, SOC learning being disabled by default, Frozen Twin persistence and measured-vs-modelled labeling, DataOps abstention/holdout/value provenance, Purchasing proof/discovery contracts, and TRD-S7's separate regime experiment. `COVERED` below means an explicit MAP/XPLAT delivery item exists; `PARTIAL` means the item exists but its DoD does not yet satisfy the beat; `BLOCKED` means the item is present but an unresolved dependency prevents the beat from being honestly staged; `GAP` means no delivering item was found.

## Beat inventory and coverage

The table contains the unique named beats in §0.1, §2.x, and §4.x. Where a storyboard beat has an explicit named sub-beat, it is listed separately. Catalog-only scenario IDs in §3 that are not presented as demo beats are not silently treated as additional beat IDs.

| Beat ID | Room | Class today | Required surface/API/component | Build dependency noted in v2.7 | MAP/XPLAT item | Status |
|---|---:|---|---|---|---|---|
| V1 | 5 | LIVE | Trading Analysis, Trust Radar/T1; `/api/fingerprint`, `/api/context/trust-analysis` | shipped mirror | B31/C-5 ST-3; DPW-1 | COVERED |
| COMP-1 | 2 | LIVE | DI-TIMELINE; `/api/dataops/cohort-status` | two-arm governed/frozen curve | B31/B32; XPLAT-01, XPLAT-05, XPLAT-07 | PARTIAL |
| V2 | 1–2 | LIVE | SOC Runtime Evolution; shadow/promote APIs and rejection log | C-2 rejection surfacing; SOC learning enabled for compounding | B31 C-2; XPLAT-03, XPLAT-07 | BLOCKED |
| V3 | 10 | LIVE | Purchasing/DataOps Performance; `RuleGenealogyTree` | shipped genealogy and seeded cross-copilot signal | B31/C-5; B27; XPLAT-03 | COVERED |
| V4 | 2 | LIVE | Any scoring surface; `/api/score` perturbation and F-26 refusal | C-3/SH-04 | B31 C-3; XPLAT-04, XPLAT-09 | COVERED |
| V5 | 8 | LIVE | SOC Compounding; `/api/eval/simulate-failure` | shipped refusal/red-team path | B31 C-5/ST-2 | COVERED |
| V6 | 11 | LIVE | Fresh-tenant view | C-4/SH-05 day-zero state | B31 C-4; XPLAT-13 | COVERED |
| V7 | 10 | LIVE | Closing montage and audit/proof narrative | demo preflight and labels | B30/B32; DEMO-01/02 | COVERED |
| TR1 | 5 | LIVE | Trading import; `/api/trading/import/csv` | observation-only BYOD path | C-OSS-1; XPLAT-15 | COVERED |
| TR2 | 5 | LIVE | Trading Analysis mirror | shipped fingerprint/trust analysis | C-5 ST-3 | COVERED |
| TR3 | 1 | LIVE | Trading Performance; edge endpoint and rejection log | C-2 rejection surfacing | B31 C-2; XPLAT-10 | COVERED |
| E1 | 1 | LIVE | SOC Runtime Evolution; shadow/promote APIs | seeded rule and shadow pass | B31 C-2; XPLAT-02, XPLAT-07 | PARTIAL |
| E2 | 6 | LIVE | SOC Alert Triage; `/api/soc/judgment/explain` | S14-C contrast for the enterprise cut | S14-C/B31; XPLAT-09 | PARTIAL |
| E3 | 1 | LIVE | SOC Compounding; promotion/rejection log | rejection reasons and learning profile | B31 C-2; XPLAT-03, XPLAT-07 | BLOCKED |
| E4 | 8 | LIVE | SOC Compounding; simulate-failure | shipped red-team path | B31 C-5/ST-2 | COVERED |
| E5 | 6 | LIVE | DataOps Insight → `ApplyFixModal`; cross-graph APIs | C-ENT-1 process export for full wedge | B41/C-ENT-1; XPLAT-11 | PARTIAL |
| E5b | 12–13 | LIVE | DataOps Dashboard/Insight; trust/products/intelligence-map APIs | gold-line rendering and evidence labels | B34/DataOps items; XPLAT-12 | PARTIAL |
| E6 | 9/15 | LIVE | SOC Executive Narrative or S2P Performance; learning-state APIs | verified-outcome continuity proof | XPLAT-03, XPLAT-14 | PARTIAL |
| E7 | 10 | LIVE | SOC Evidence Room; ServiceNow/Sentinel write-back | connector/demo preflight | B32; DEMO-01 | COVERED |
| E8 | 11 | LIVE | SOC Evidence Room; evidence-ledger export | hash-chain/provenance | B29/B32; XPLAT-03 | COVERED |
| DM-1 | 1 | LIVE | Trading Performance/SOC Runtime Evolution; rejection log table | confirm rejection reasons are surfaced | B31 C-2; XPLAT-07, XPLAT-10 | PARTIAL |
| CF-1 | 2 | NEAR | Scoring surface; perturbation plus F-26 refusal | SH-04 counterfactual inspector | B31 C-3; XPLAT-09 | COVERED |
| S14-CONTRAST | 6 | NEAR | S2P Exception Triage; computed rule-vs-SituationPanel columns | S14-C, same-invoice $ impact | B31 S14-C; XPLAT-04 | COVERED |
| DZ-1 | 11 | NEAR | Fresh-tenant view | instrument-validated → accumulating → measured | B31 C-4; XPLAT-13 | COVERED |
| ST-1 | 1 | LIVE | SOC Compounding; `/api/soc/interventions` | shipped | B31 C-5 | COVERED |
| ST-2 | 8 | LIVE | SOC Compounding; simulate-failure | shipped | B31 C-5 | COVERED |
| ST-3 | 5 | LIVE | Trading/Purchasing Analysis; fingerprint | shipped | B31 C-5 | COVERED |
| ST-4 | 10 | LIVE | SOC Evidence Room; Sentinel/ServiceNow | shipped | B31 C-5 | COVERED |
| ST-5 | 6 | LIVE | S2P Exception Triage | content rewrite | B31 S14-C | COVERED |
| BYOD-1 | 5/10/12/6 | NEAR | Importer on `write_observation`, not `write_decision` | Purchasing/DataOps/S2P importer remains mixed | C-OSS-1; XPLAT-03, XPLAT-11, XPLAT-12 | PARTIAL |
| TRD-S3 | 3 | NEAR | Trading Performance; regime break → AMBER/autonomy throttle | C-TRD-SIT Step 2; SAFE-2 prerequisite | B34; XPLAT-15, XPLAT-10 | BLOCKED |
| TRD-V1 | 4 | NEAR | Trading Performance; clustering-adjusted Sharpe | C-TRD-VOL/B4 | B35; XPLAT-10 | COVERED |
| TRD-V2 | 4 | NEAR | Trading Performance; VRP/tail-dependence analysis | C-TRD-VOL/B7+B1 | B35; XPLAT-10 | COVERED |
| TRD-S1 | 3 | NEAR | Trading Performance; regime-conditioned mirror | C-TRD-SIT 3a and tags | B34 | COVERED |
| TRD-S2 | 3 | NEAR | Trading scoring; per-regime abstention/day-zero | C-TRD-SIT 3a | B34; XPLAT-10 | PARTIAL |
| TRD-S4 | 3 | NEAR | Trading Performance; regime-scoped rejection | C-TRD-SIT 3a | B34; XPLAT-10 | PARTIAL |
| TRD-V5 | 4 | NEAR | Trading Performance; regime-conditioned rich/cheap | C-TRD-VOL | B35 | COVERED |
| TRD-V6 | 4 | NEAR | Trading Performance; dispersion follow-rate | C-TRD-VOL | B35 | COVERED |
| TRD-V7 | 4 | NEAR | Trading Performance; effective bets in tail | C-OSS-1Q | B35 | COVERED |
| TRD-S7 | 3b | ARCH | Trading Performance/Runtime-Evolution curve overlay | C-REGIME P4 + EXP-REGIME on 2020/2022 history | B37–40; XPLAT-14 | BLOCKED |
| ENT-1 | 6 | NEAR | DataOps/S2P cross-graph fusion; process export | C-ENT-1; no ERP write-back | B41; XPLAT-11 | COVERED |
| DI-PROOF | 12 | NEAR | DataOps TrustCard live what-if | perturbation + restore + provenance | XPLAT-12 | PARTIAL |
| DI-TRUST | 12 | LIVE | DataOps TrustCard; `/api/dataops/trust` | shipped source-derived trust | existing DI items; XPLAT-12 for evidence labels | COVERED |
| DI-SOURCE | 12 | LIVE | DataOps source profile; trust/consumers APIs | shipped endpoints | existing DI-1; XPLAT-12 | COVERED |
| DI-PRODUCT | 13 | LIVE | DataOps Products panel; `/api/di/products` | shipped endpoint; provenance guard | existing DI-1; XPLAT-12 | COVERED |
| DI-GOLD | 12 | NEAR | DataOps Intelligence Map; combinations/acquisition APIs | gold lines FDR/holdout gated | DI-GOLD-FE; XPLAT-12 | PARTIAL |
| DI-TIMELINE | 2/12 | LIVE | DataOps CentroidTimelinePanel | shipped centroid history | B32; XPLAT-12 | COVERED |
| DI-ADMITS-FAILURE | 12 | LIVE | DataOps Evidence; genealogy/accuracy APIs | shipped | existing SC-12/13; XPLAT-12 | COVERED |
| DI-DIRTY-DATA | 12 | LIVE | DataOps TrustCard | shipped same surface as DI-TRUST | existing DI-1; XPLAT-12 | COVERED |
| DI-AGENT-TRUST | 14 | LIVE | DataOps source trust card | gateway-safe language and evidence | XPLAT-12 | PARTIAL |
| DI-ABSTAIN | 14 | NEAR | `/v1/trust/verify`; evidence + abstain | verified-decision loop and insufficient-data gate | XPLAT-12 | BLOCKED |
| DI-GATEWAY | 14 | NEAR | Agent Trust Gateway/MCP | corrected trust/read-only contract | XPLAT-12 | BLOCKED |
| DI-FIRSTVS6TH | 12 | NEAR | DataOps learning/time-to-green panel | measured learning and transfer | XPLAT-12, XPLAT-14 | BLOCKED |
| DI-TWIN | 12 | NEAR | DataOps frozen-vs-live control | RL-PERSIST/shared Frozen Twin | XPLAT-01, XPLAT-12 | BLOCKED |
| DIFF-1 | 2/3 | NEAR | Governed-vs-reward-max differentiation surface | faithful baseline, regime shift, poisoned-rule fixtures | B30/B31; XPLAT-02, DEMO-02 | PARTIAL |
| L-CDK-1 | 10 | NEAR | GAE quickstart/conservation gate | public SDK drop | C-OSS-2; XPLAT-16 | PARTIAL |
| L-CDK-2 | 10 | NEAR | YAML domain configuration | public SDK drop | C-OSS-2; XPLAT-16 | PARTIAL |
| L-CDK-3 | 10 | NEAR | SDK-level governed toggle; email/reading skins | public SDK drop | C-OSS-2; XPLAT-16 | PARTIAL |
| TRD-CLAIM-GATE | 3/4 | NEAR | Trading Analysis/Performance; FDR/deflated-Sharpe badge | Claim Gate and held-out confirmation | XPLAT-10, XPLAT-15 | BLOCKED |
| TRD-CERTIFICATE | 3/4 | NEAR | Trading Analysis/Performance; clean-trader certificate | Claim Gate | XPLAT-10 | BLOCKED |
| TRD-GATE-DIVIDEND | 3/4 | NEAR | Trading Performance; withheld-findings replay | Claim Gate + source-derived magnitude | XPLAT-10 | BLOCKED |
| PUR-CONTINUITY | 15 | NEAR | Purchasing Analysis/Performance; continuity close | PUR-HERO plus verified outcome continuity | XPLAT-03, XPLAT-11, XPLAT-14 | PARTIAL |
| PUR-PROOF-LEDGER | 15 | NEAR | Purchasing Performance; proof/competence curves | F23 proof ledger and honest-$0 attribution | XPLAT-11 | BLOCKED |
| PUR-NOT-YET | 15 | LIVE | Purchasing Analysis/Performance; abstention/quiet week | evidence floor and partial pooling | XPLAT-11 | PARTIAL |
| PUR-REFUSAL | 15 | NEAR | Purchasing auto-approve; conservation self-pause | promotion/autonomy state machine | XPLAT-02, XPLAT-11 | BLOCKED |
| PUR-RAMP | 15 | NEAR | Purchasing Performance; time-to-competence | re-convergence metric and persisted series | XPLAT-11, XPLAT-14 | BLOCKED |
| S2P-LEDGER | 6 | LIVE | S2P Performance AutonomyLedger | two-arm frozen comparison | XPLAT-05, XPLAT-06 | PARTIAL |
| S2P-EXTINCT | 6 | NEAR | S2P Performance promotion lifecycle | proposal + promotion state machine | XPLAT-04, XPLAT-02, XPLAT-06 | BLOCKED |
| S2P-TWIN | 6 | NEAR | S2P Performance frozen/live curves | RL-PERSIST/shared Frozen Twin | XPLAT-01, XPLAT-06 | BLOCKED |
| S2P-WHATIF | 6 | NEAR | S2P Exception Triage counterfactual inspector | per-factor boundary/magnitude | XPLAT-09 | COVERED |
| S2P-DAY0 | 6 | NEAR | S2P fresh-tenant readiness | Day-0 qualification | XPLAT-13 | COVERED |
| S2P-CONFIDENCE | 6 | LIVE | S2P Performance/triage confidence band | always-visible panel | XPLAT-06 | PARTIAL |
| SOC-CONTROL | 8 | NEAR | SOC Tab 2 Runtime Evolution control room | verified outcomes change later score; learning ON | XPLAT-07 | BLOCKED |
| SOC-LADDER | 8 | NEAR | SOC Tab 4/Tab 3 per-class ladder | persisted five-rung state and veto | XPLAT-02, XPLAT-08 | BLOCKED |
| SOC-TWIN | 8 | NEAR | SOC Compounding frozen/live curves | RL-PERSIST/shared Frozen Twin | XPLAT-01, XPLAT-07 | BLOCKED |
| SOC-NOPRECEDENT | 8 | LIVE | SOC Triage no-precedent sidebar | explicit evidence/novelty state | XPLAT-09 | COVERED |
| SOC-WHATIF | 8 | NEAR | SOC Triage counterfactual inspector | per-factor action-boundary explanation | XPLAT-09 | COVERED |
| SOC-DAY0 | 8 | NEAR | Fresh-tenant SOC readiness view | source coverage/connector readiness | XPLAT-13 | COVERED |
| SOC-FRONTIER | 8 | LIVE | SOC Compounding coverage and Recovery Half-Life | two-arm frozen comparison | XPLAT-01, XPLAT-07, XPLAT-14 | PARTIAL |
| SOC-GAUNTLET | 8 | LIVE | SOC Triage scripted five perturbations | packaged benchmark and E2E | XPLAT-09, DEMO-02 | PARTIAL |

## GAP and PARTIAL report

No row was classified `GAP`: every named beat has either a v5.228 batch, a modified v5.228 item, or an explicit v5.229 XPLAT card. The following rows remain `PARTIAL` or `BLOCKED` and therefore are not fully covered for an honest LIVE demo.

| Beat(s) | What's missing | Copilot/repo | Proposed fix | Priority |
|---|---|---|---|---|
| COMP-1, S2P-LEDGER, SOC-FRONTIER | A two-arm governed/frozen comparison with measured labels; current single-arm primitives are insufficient | DataOps, S2P, SOC; shared SDK | Complete XPLAT-01, XPLAT-05, XPLAT-07, then XPLAT-14 | Blocks LIVE compounding claims |
| V2, E1, E3, DM-1, SOC-CONTROL | SOC learning is disabled by default; later-score movement is not proven in the demo profile | SOC repo + shared verified-outcome path | Enable and prove the profile per v2.7, or recut learning beats to Trading/S2P/DataOps/Purchasing; complete XPLAT-03/XPLAT-07 | Blocks LIVE VC/enterprise beats |
| E2, S14-CONTRAST | Existing SituationPanel is present, but the computed two-column contrast and full receipt are not guaranteed | S2P frontend | Finish B31 S14-C and mount the XPLAT-04 proposal/evidence receipt | Blocks NEAR enterprise beat |
| E5, ENT-1 | Real process-mining export ingestion and the full where→what→why→which-decision path | DataOps/S2P | Complete B41/C-ENT-1 and preserve the no-ERP-write-back guard | NEAR room 6 |
| E5b, DI-GOLD, DI-PROOF, DI-AGENT-TRUST | Gold-line rendering, FDR/30-day holdout labels, restore/provenance affordance, and safe gateway wording | DataOps | Complete XPLAT-12 plus DI-GOLD-FE; keep dollars off the hero path until gated | LIVE/NEAR data rooms |
| E6, PUR-CONTINUITY | A verified later score and defensible dollars of retained judgment are not yet proven | SOC/Purchasing/S2P | Complete XPLAT-03 and XPLAT-14; use measured/modelled labels | Blocks continuity close |
| BYOD-1 | Only Trading/SOC imports are present; other copilots lack the safe observation importer | Purchasing, DataOps, S2P | Add CSV→score→learn on `write_observation`; XPLAT-03, XPLAT-11, XPLAT-12 | NEAR; not a current LIVE blocker |
| TRD-S3, TRD-S2, TRD-S4 | SAFE-2 is a prerequisite; regime-conditioned outputs and abstention need the safety/claim contract | Trading | Ship XPLAT-15, then XPLAT-10 and retain B34 read-layer scope | Blocks NEAR room 3 |
| TRD-S7 | Regime-indexed judgment memory and EXP-REGIME evidence are absent | Trading/SDK | Complete B37–40/C-REGIME P4 and XPLAT-14; label ARCH until experiment passes | Blocks strongest technical NEAR beat |
| TRD-CLAIM-GATE, TRD-CERTIFICATE, TRD-GATE-DIVIDEND | Evidence Gate, FDR/holdout, and safe observation-only publication path are not complete | Trading | Complete XPLAT-10 after XPLAT-15 and SH-01 | Blocks NEAR rooms 3–4 |
| PUR-PROOF-LEDGER, PUR-REFUSAL, PUR-RAMP | Proof ledger, autonomy state, and time-to-competence persistence are absent or generic | Purchasing | Complete XPLAT-02, XPLAT-03, XPLAT-11, XPLAT-14 | Blocks NEAR room 15 |
| PUR-NOT-YET, S2P-CONFIDENCE | The narrative exists, but evidence-floor/always-visible product surfaces are not fully contracted | Purchasing/S2P | Extend XPLAT-11/XPLAT-06 with explicit abstention and UI acceptance tests | LIVE honesty guard |
| S2P-EXTINCT, S2P-TWIN | Proposal-centered lifecycle and immutable baseline are not available together | S2P/shared SDK | Complete XPLAT-01, XPLAT-02, XPLAT-04, XPLAT-05, XPLAT-06 | Blocks NEAR S2P arc |
| SOC-LADDER, SOC-TWIN | Persisted per-class authority and immutable twin are absent; RED veto is not proven in the actual triage path | SOC/shared SDK | Complete XPLAT-01, XPLAT-02, XPLAT-07, XPLAT-08 | Blocks NEAR SOC autonomy proof |
| SOC-GAUNTLET, SOC-FRONTIER | Decision path is available, but packaged benchmark/two-arm evidence is not | SOC | Complete XPLAT-09 and XPLAT-14 with E2E evidence | NEAR packaged proof |

## Scenario class progression

Counts below are for the 80 unique named beat rows in the coverage table. `Today` uses the class explicitly stated in v2.7; `After addendum` assumes queued XPLAT acceptance criteria pass, while TRD-S7 remains NEAR until the separate EXP-REGIME result is accepted. This is a delivery projection, not a claim that queued work is already shipped.

| Class | Today | After addendum | Delta |
|---|---:|---:|---:|
| LIVE | 38 | 79 | +41 |
| NEAR | 41 | 1 | -40 |
| ARCH | 1 | 0 | -1 |

The projected post-addendum state still has one NEAR beat—TRD-S7—because its v2.7 contract explicitly requires C-REGIME P4 plus a passing real-history experiment. If “after addendum” is interpreted as MAP cards merely being created rather than completed, the current status column is the correct state and no class should be promoted.

