# VLD comprehensive architecture, implementation and test audit — 2026-09-12

## 1. Executive summary

**Production-paper readiness: NO for all five copilots. Full v2.8 demo readiness: NO for all five specified beats.** The factor-acquisition primitive works on deliberately constructed fixtures, but the platform does not yet have one verified end-to-end VLD architecture. The most serious findings concern oracle output in the SOC demo path, scoring-baseline mismatch, missing persisted/empty-read traces and emit eligibility, and acceptance tooling that can agree with itself while missing the demo contract.


| Severity | Unique findings |
| --- | --- |
| P0 — blocks a stated paper/demo claim | 16 |
| P1 — fix before production ship | 16 |
| P2 — documentation/maintenance debt | 1 |
| COSMETIC | 0 |
| TOTAL | 33 |
Severity applies to the stated claim or surface, not automatically to a security exploit or the entire platform. Missing planned capabilities are marked as gaps, not regressions. Findings F01–F33 are counted once; repeated gap-matrix references are not additional findings.

**Top five paper risks:** oracle branch/action leakage (F26); unfaithful production scoring/contrast (F11/F13); unavailable held-out score-keyed evidence and fair comparators (F23); incomplete trajectories and invalid propensities (F02/F20); incomplete production-state replay and gates (F31/F32).

**Top five demo risks:** missing provenance/accuracy badges and shared panel (F27); original beat narratives differ from seeds (F29/F30); no VLD Loom cut manifests (F28); no conservation emit eligibility (F14); test success does not certify story/read-order/default-budget behavior (F32/F33).


| Copilot | Current narrow seed action pairs | Original narrative/production limitations | Paper | Demo |
| --- | --- | --- | --- | --- |
| SOC | 3/3 | SDK seeds differ from v2.8; separate UI path can force oracle output | BLOCKED | BLOCKED |
| Trading | 3/3 | Repaired geometry and 2→1 reads; omitted budget selects S3/1 read; no VLD UI | BLOCKED | BLOCKED |
| Purchasing | 3/3 | Collapsed checkpoint repaired; two story read orders still differ; S1 override hides S3 classifier | BLOCKED | BLOCKED |
| DataOps | 3/3 | Narrow factor replay works; domain endpoint metric/source differs; original DO2 absent | BLOCKED | BLOCKED |
| S2P | 2/3 | S2P2 remains flag_leakage; K empty; original receipt-first/history claim absent | BLOCKED | BLOCKED |
**v2.8 inventory:** 37 explicitly enumerated requirements: **3 BUILT, 14 PARTIAL, 15 NOT BUILT, 5 BLOCKED** (§19). The three BUILT entries are currently satisfied wording/claim guards, not proof that a complete beat is built. This denominator covers the requested VLD portions of §4.17, §4.18, §5 and §7.2, not the entire unrelated 94-scenario catalog.

### Scope, evidence and execution discipline

The audit inspected the SDK, SOC and S2P implementation trees, the located demo_scenarios_and_usecases_v2_8.md, the four requested diagnosis/snapshot documents, the Sep12 resweep, architecture v3/v4 and implementation-design generations where relevant, and the located math-synopsis v18/v20 material. Historical reports were used as context, then checked against current files. No web source or live AGE measurement is used as evidence here.

No git command or source/test/preseed/evidence-provider edit was performed. The sole authored deliverable is this document; the existing centroid JSON was read, not re-exported. Numerical checks used current local checkpoint/L5 rows opened with SQLite mode=ro and the existing SOC bootstrap export, plus current provider/seed implementations. Replay used actual package imports; Trading/Purchasing app/__init__.py imports main.py, so those imports executed application construction/registration side effects. Consequently this audit does **not** assert a byte-for-byte no-side-effect guarantee for all runtime databases. It does verify unchanged source hashes and performed no explicit database mutation or seed-to-path write. A future strictly isolated harness should import side-effect-free modules.

Fresh test evidence is the direct in-memory execution of 30 existing SDK test functions, all passing, plus independent boundary probes and 15 scenario replays. Full pytest/app/e2e suites were not rerun in this source-audit pass. The Sep12 baseline counts are historical and cannot be used to certify the changed checkout. There is no claim here that the prior baseline failures have been fixed.

### Current local geometry and fixture replay

The replay manually reproduced SQLite's maximum normalized (created_at,id) checkpoint selection and L5 category/action overlay without constructing CompoundingScorer. This is a **read-side numerical reconstruction**, not a full startup-equivalence test. Sources: copilot-sdk/copilot_sdk/graph/sqlite_store.py:2906–2923 and :2602–2621; copilot-sdk/copilot_sdk/scoring/scorer.py:320–339, :706–730. All primary rows below use unit sigma, tau=.1, explicit budget2 and production source-gating sets. S1 requests must instead use their declared/default budget0; forced-budget S1 rows are diagnostic only.

| Domain | Checkpoint / L5 rows | Post-overlay tensor SHA-256 | Category/action separation |
| --- | --- | --- | --- |
| soc | SOC export / 0 | e055e9f4733cfac11711dbdcf8e0c9de7b6b1ffd6f401ceadfe6bc9867af237a | credential_access:4 unique; malware_execution:4 unique; lateral_movement:4 unique; data_exfiltration:4 unique; insider_threat:4 unique; cloud_infrastructure:4 unique |
| trading | 6 / 6 | d8a2de4b29f10273258ac65335ebc3b4c8ad4159a8b4f89a1d8d7a0872ddfaea | trend_following:4 unique; mean_reversion:4 unique; event_driven:4 unique; income_strategy:4 unique; scalp_intraday:4 unique |
| purchasing | 6 / 0 | 67e1212e8699bd31d8bab12b7f6d790d1c6514d872b0116ac84a514ce85da174 | protein:4 unique; produce:4 unique; dairy:4 unique; dry_goods:4 unique; beverages:4 unique |
| dataops | 219 / 3 | 7d03df393211484452ddbe258f2836314ab7f8f429027c3dd5bc0fd2f065622c | schema_change:5 unique; volume_anomaly:5 unique; quality_anomaly:5 unique; freshness_violation:5 unique; pipeline_failure:5 unique; transform_drift:5 unique |
| s2p | 174 / 6 | 38c5c5d09819dcadaf127a370906066c30b59ff7a778e43bd9957022434a4998 | price_variance:5 unique; quantity_mismatch:5 unique; duplicate_risk:5 unique; contract_gap:5 unique; format_compliance:5 unique |

Current Trading and Purchasing checkpoint IDs are **6**, and all their action rows are differentiated in all five categories. The collapse diagnosis is historical. All 27 category slices in this replay have distinct action rows. This necessary geometric condition is not evidence of learned predictive quality.

| Scenario / category | Surface → final | Margins before → after | Attempted dimensions / raw evidence | Action pair | Automatic classifier / budget |
| --- | --- | --- | --- | --- | --- |
| VLD-SOC-1 / credential_access | monitor → escalate | 0.119916 → 0.180204 | 0:0.9200 @0.920 identity_graph; 5:None | MATCH | S6 / 4 |
| VLD-SOC-2 / malware_execution | monitor → escalate | 0.119681 → 0.180119 | 2:None; 0:0.9200 @0.920 identity_graph | MATCH | S6 / 4 |
| VLD-SOC-S1 / malware_execution | escalate → escalate | 0.664020 → 0.664020 | 1:None; 5:None | MATCH | S1 / 0 |
| VLD-TRD-1 / trend_following | strong_execution → partial_execution | 0.507773 → 0.843481 | 2:0.5500 @0.900 portfolio_engine; 1:0.8800 @0.900 correlation_engine | MATCH | S3 / 1 |
| VLD-TRD-2 / trend_following | strong_execution → partial_execution | 0.787262 → 0.991906 | 2:0.8500 @0.920 portfolio_engine; 1:0.7800 @0.880 correlation_engine | MATCH | S3 / 1 |
| VLD-TRD-S1 / trend_following | strong_execution → strong_execution | 0.823506 → 0.823506 | 5:None; 0:None | MATCH | S1 / 0 |
| VLD-PUR-DEMAND-SPIKE / produce | order_more → order_less | 0.194334 → 0.234353 | 5:0.2000 @0.900 lead_time_tracker; 4:0.5097 @0.650 vendor_tracker | MATCH | S3 / 1 |
| VLD-PUR-VENDOR-CASCADE / dry_goods | order_as_planned → skip | 0.455501 → 0.758882 | 4:0.7200 @0.900 vendor_tracker; 3:0.2365 @0.650 event_calendar | MATCH | S3 / 1 |
| VLD-PUR-S1-STANDARD / dry_goods | order_more → order_more | 0.596476 → 0.596476 | 5:0.2000 @0.880 lead_time_tracker; 3:0.5000 @0.800 event_calendar | MATCH | S3 / 1 |
| VLD-DO-1 / pipeline_failure | investigate → escalate_to_owner | 0.119838 → 0.956396 | 0:0.9000 @0.920 schema_registry; 3:0.8500 @0.880 dependency_graph | MATCH | S3 / 1 |
| VLD-DO-2 / quality_anomaly | refer_to_specialist → escalate_to_owner | 0.706347 → 0.673795 | 2:0.6500 @0.550 historical_alerts; 3:0.8800 @0.820 dependency_graph | MATCH | S6 / 4 |
| VLD-DO-S1 / pipeline_failure | auto_approve → auto_approve | 0.998996 → 0.998996 | 0:None; 4:None | MATCH | S1 / 0 |
| VLD-S2P-1 / price_variance | hold_for_review → auto_approve | 0.882877 → 0.909828 | 0:0.9500 @0.900 contract_db; 3:0.0300 @0.821 supplier_history | MATCH | S3 / 1 |
| VLD-S2P-2 / price_variance | flag_leakage → flag_leakage | 0.890895 → 0.897183 | 0:0.9300 @0.900 contract_db; 1:0.0500 @0.820 pricing_benchmark | MISMATCH | S6 / 4 |
| VLD-S2P-S1 / price_variance | auto_approve → auto_approve | 0.936488 → 0.952172 | 0:0.9800 @0.950 contract_db; 5:None | MATCH | S1 / 0 |

Current action pairs: **14/15 match**, **9/10 claimed flips occur**, all actual flip final margins exceed .05, and **0 hurts relative to fixture terminal labels**. Respecting each current seed's prose and S1 request gives only **12/15 narrow full contracts**: Purchasing's two claimed second reads do not occur, and S2P2 does not flip. These are not the full original v2.8 contracts. Correctness is fixture-label-relative, not verified production outcome accuracy. Evidence availability by scenario is reported in §18.

## 2. Audit 1 — Investigation pipeline correctness

The shared engine is a score-conditioned **factor-acquisition** loop. It is not an SA-pattern traversal controller. Its semantics are reproducible from the following code; the alternative SOC/DataOps pattern loops are discussed separately.

- Scoring: \(p_a=\operatorname{softmax}(-\sum_k (v_k-\mu_{a,k})^2/\max(\sigma_k^2,0.001)/\tau)\). Sigma is a length-d vector, not a covariance matrix. Scoring uses tau, not tau².
- With a1/a2 the current top-two actions, \(Q_k=K_k[1/(100\max(\sigma_k^2,0.001))+|\mu_{a1,k}-\mu_{a2,k}|+|(v_k-\mu_{a1,k})^2-(v_k-\mu_{a2,k})^2|]\). Omit K multiplication when absent. Attempted dimensions receive −1 before weighting.
- A gated source updates only the selected coordinate: \(v'_k=c\,\mathrm{clip}(e_k)+(1-c)v_k\). Other sources replace it regardless of confidence. This is source-dependent confidence blending, not the full-vector re-extraction of the SOC pattern loop.
- All actions in the **selected category** are re-scored after an informative read. The category does not change in this SDK loop.
- Step flip = action_before != action_after; final action_changed compares terminal versus surface. No margin threshold is required. A tiny-margin flip counts, and two opposing flips can leave final action_changed=False.
- Argmax(Q) selects the lowest index on exact dimension ties. Action ties use np.argmax; compute_Q's argsort top-two tie ordering is a separate convention.
- None consumes one attempt, marks that dimension exhausted, and leaves v unchanged. No successful step is appended.
- There is no early stop after N unchanged actions. Valid positive-Q runs end at the requested attempts or after every dimension has been tried.

Sources: copilot-sdk/copilot_sdk/scoring/investigation.py:66–81, :95–111, :124–180. Core input arrays are copied; no graph or centroid write occurs in investigate().


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F01 — P1 | copilot-sdk/copilot_sdk/scoring/investigation.py:95, :106–111; copilot-sdk/docs/design/vld_centroid_preseed_gap_analysis_2026-09-11.md:23–32; copilot-sdk/docs/design/math_synopsis_v18.md:438 | **Q is an additive heuristic, not the proposed sigma × separation / tau equation.** Paper readers cannot equate the deployed selector with the prompt's equation or a proved value-of-information rule. Neither tau nor tau² divides Q; tau only affects P and thus the winning pair. | Version the actual equation and its coefficients; register ablations against cost-aware/content-rule/breadth comparators. Do not change it to the prompt equation without validation. | Basic Q behavior tested at copilot-sdk/tests/test_investigation.py:84–129; no independent numerical equation oracle or utility validation. Reference: §5 R3, §4.17 |
| F02 — P0 | copilot-sdk/copilot_sdk/scoring/investigation.py:12–37, :138–141, :155; copilot-sdk/copilot_sdk/backend/investigation_router.py:105; gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py:10–26 | **SDK drops empty attempts and cannot supply an E-1 trajectory.** SOC-2's wrong first read disappears from the SDK response, and successful steps are renumbered. SDK traces omit candidate reads, selection quantities, costs, timestamps, policy version and halt reason. No investigated episode is persisted by these handlers. | Record every attempt, including empty/error results, with stable attempt index and E-1 metadata; persist immutable episode records after the read-only computation and link verified outcomes. Reuse the richer SOC model where applicable. | Skipping None is explicitly tested at copilot-sdk/tests/test_investigation.py:153; complete persisted replay is untested. Reference: §4.17 SOC-2; §5 E-1; GUARD-3 |
| F03 — P1 | copilot-sdk/copilot_sdk/scoring/investigation.py:52–64, :98–111, :143–145, :182–187 | **Numerical validation is incomplete.** Finite input vectors are checked, but NaN/Inf centroid/sigma/tau/K state is not. NaN evidence becomes 1.0 through Python min/max rather than being rejected. A JSON serialization error can occur after the handler's exception boundary when margins are NaN. | Require finite parameters, positive finite tau, nonnegative finite sigma with an explicit floor policy, finite bounded K, A>=2 and d>=1; reject malformed evidence before clamping finite out-of-range values. | Fresh numerical probes reproduced NaN probabilities and NaN→1 evidence. Existing shape checks cover only valid exported tensors (tests/test_vld_integration.py:58). Reference: — |
| F04 — P0 | copilot-sdk/copilot_sdk/scoring/investigation.py:131–170; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:82–129; copilot-sdk/apps/dataops/backend/app/services/investigation_loop.py:87–133 | **SDK has no residual or oscillation halt.** The shared loop stops on budget or nonpositive Q/exhausted dimensions, not on C4. SOC/DataOps pattern loops do have C4-like controls, so claiming this capability absent everywhere is also wrong. An empty SDK read leaves v unchanged; it cannot itself produce the action reversal scripted in v2.8. | Choose and version a common stopping contract. Preserve selector-only/empty-read continuations where another productive read remains; record halt reason and flip count. Reconcile the impossible empty-read action-change script. | SOC residual and exact max-flips tests exist at backend/tests/test_investigation_loop.py:237, :423; shared C4 tests do not. Reference: §5 C4; §4.17 SOC-2; architecture v4 §2.3 |
## 3. Audit 2 — Shared investigation router

POST **/api/investigation/investigate** accepts nonempty decision_id/category strings, a nonempty float list, optional integer budget, and use_K=True. The response includes surface/final action indices and margins, situation/confidence, steps, action_changed and contrast. GET /api/investigation/health reports object availability, not live source health. A model-free wired classifier reports classifier_loaded=False. Sources: copilot-sdk/copilot_sdk/backend/investigation_router.py:16–36, :50–119.

When budget is omitted, a supplied classifier allocates it; without a classifier the default is 2. Explicit budgets bypass classification. K is read once per request and multiplies Q only; it does not change scoring distances. Empty K yields uniform 0.5, which preserves positive-Q ordering and zero/nonzero halts. Each request constructs its own VLDInvestigator; the handler returns its trace but neither logs nor persists an episode. Contrast is always constructed on a successful response, including budget0, but is only the same engine's initial/final comparison (F11).


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F05 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:16–21, :65–82, :97; copilot-sdk/copilot_sdk/scoring/investigation.py:125, :131–141 | **Budget_used reports allocated budget; explicit budgets bypass classification.** A request budget=1000 reports 1000 even when a two-factor provider was called twice. Negative budgets silently become zero. Metadata is unsuitable for cost comparisons; explicit budget also suppresses situation output. | Separate budget_limit, attempts_used, successful_reads and cost_used. Validate 0<=budget<=configured cap, keep situation assessment independent of overrides, and freeze demo request budgets explicitly. | Existing budget test only checks budget=1 (tests/test_investigation.py:322). Fresh budget0/1/1000 probes recorded actual reads. Reference: §5, GUARD-7 |
| F06 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:54–111; gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:96–125 | **Provider/K errors abort the request and leak exception details.** K read failures and general provider errors become 503, ValueError becomes 400 even if it arose internally, and partial traces are lost. SOC graph exceptions instead collapse to None, making outage indistinguishable from no evidence. | Use typed input/provider/store errors, retain an error attempt and partial trace, return opaque public diagnostics plus a correlation ID. Explicitly select fail-closed versus shadow-degraded behavior for K. | No core provider-throws/K-unavailable request test; existing test_router_no_evidence only covers legitimate None at tests/test_investigation.py:313. Reference: — |
| F07 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:16–36, :50–52; gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:453–555; copilot-sdk/apps/dataops/backend/app/main.py:963–973; s2p-copilot/backend/app/main.py:339–348 | **There are incompatible API contracts, not a single domain-parametric public endpoint.** All five mount /api/investigation/investigate. SOC and DataOps additionally expose different /api/{domain}/investigate handlers. The shared result uses integer actions and dictionaries without schema version/action vocabulary; the domain paths return other result shapes. No S2P domain alias was found. | Publish versioned request/response types and explicit aliases/adapters. Include action vocabulary, geometry/policy IDs and shadow/emit status. Test the exact frontend request against each production mount. | Core router schema smoke tests exist; the real integration harness calls an unmounted handler directly (tests/vld_validation_report.py:279–288). Reference: §4.17 API |
## 4. Audit 3 — Evidence providers across five copilots

All five implement read_evidence(decision_id, dimension, factor_name) → dict(value, confidence, source, …) or None. Structural protocol conformance is real; semantic factor alignment and live evidence coverage are separate questions. SDK InvestigationStep retains only value/confidence/source plus vectors, losing extra evidence IDs, clauses, affected-system names and provenance.

| Copilot | Supported canonical dimensions | Actual source and unsupported behavior | Gated source names |
| --- | --- | --- | --- |
| SOC | 0 identity, 1 asset, 2 intel, 3 history, 4 time, 5 device | Registry first, then optional get_vld_evidence/map/async AGE run_query; unknown lookup returns None. Async get_vld_evidence is discarded rather than awaited. | identity_graph, threat_intel |
| Trading | All 10 canonical factors; aliases map thesis/correlation/momentum concepts | Registry first; optional accessor/map. No native market/portfolio read implementation in this provider. Unknown/unavailable returns None. | correlation_engine, portfolio_engine |
| Purchasing | All 7: demand, day, weather, event, waste/vendor risk, lead time, price/substitution | Order/supplier dictionaries or JSON loader. Unknown factor/order returns None; many missing numeric fields default to 0.5. | vendor_tracker, lead_time_tracker |
| DataOps | All 6: impact, source, recurrence, downstream, freshness, business criticality | Fixture dictionaries/files, schema/history/dependency helpers. Missing matching data returns None; some fall back to alert factors. | schema_registry, dependency_graph |
| S2P | All 8: match, amount variance, duplicate, supplier history, terms, commodity, compliance, environment | Showcase dictionaries or synthetic invoice/supplier JSON; unknown invoice/factor returns None. Several supplier-present paths emit fixed defaults. | None |

Sources: SOC evidence_provider.py:14–21, :75–126; Trading evidence_provider.py:6–29, :63–97; Purchasing evidence_provider.py:25–46, :197–233; DataOps evidence_provider.py:38–60, :201–278; S2P evidence_provider.py:28–59, :272–347. Full paths are in the evidence references below and §19 legend.

Returned finite values/confidences are clamped to [0,1]. **This is not finite-value validation:** NaN follows min/max semantics (F03), and arbitrary float conversions can throw. Every non-None normal return includes a source; a source label is not authenticated provenance. Gating intentionally differs by deployment; S2P overwrites even low-confidence supplier history, DataOps historical_alerts is ungated (e.g. DO2 confidence .55), and unknown sources are ungated. These choices need source-trust policy tests rather than a blanket assertion that every provider gates identically.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F08 — P1 | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:51–60, :81–88; copilot-sdk/apps/trading/backend/app/evidence_provider.py:67–97; copilot-sdk/apps/dataops/backend/app/evidence_provider.py:201–242; copilot-sdk/apps/purchasing/backend/app/main.py:608, :843–845; s2p-copilot/backend/app/main.py:231, :341–343 | **Real provider classes mostly serve planted/static evidence, without per-read planted provenance.** A real class is not proof of live evidence. SOC/Trading registry entries override the backing source. Purchasing and S2P application VLD factories are wired to showcase dictionaries; DataOps loads fixture files. Source names such as contract_db or identity_graph do not disclose planted origin. | Carry origin, record IDs, version, as-of time and source health through evidence→trace→panel. Keep fixture and live providers selectable and testable, and measure ordinary non-showcase coverage. | All five provider suites test fixture reads; no end-to-end live-source coverage proof is present. Reference: §5 provenance; GUARD-3/8 |
| F09 — P1 | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:128–159, :163–194 | **SOC evidence normalization can convert counts/defaults into confident scores.** pattern_history returns similar_alerts_30d directly and then clips to [0,1], so 1 and 14 both become 1. Identity evidence uses campaign confidence rather than verified auth facts; graph queries use fixed confidence/default values. First-row selection has no declared temporal ordering. | Specify factor-specific calibrated transformations, distinguish missing/default/measured values, and compare AGE payloads with fixture semantics. Preserve confidence provenance and handle async adapters explicitly. | SOC provider tests at backend/tests/test_soc_evidence.py:73–103 use fake graph evidence; fresh/live count-to-factor equivalence is untested. Reference: — |
| F10 — P0 | s2p-copilot/backend/app/vld_preseed.py:84–89; s2p-copilot/backend/app/evidence_provider.py:95–119, :128–148 | **S2P's displayed 3.1 ratio and verified history are fixture assertions.** The 3.1 ratio is read as a literal, not computed from linked verified decisions. The non-showcase path labels total_invoices as verified_priors. Contract coverage is preferred over receipt evidence. This does not establish v2.8's receipt-first supplier-history mechanism. | Seed time-stamped verified outcomes, compute partial-delivery/pricing-error counts and ratio, distinguish invoice counts from verified outcomes, and bind receipt/contract branches to genuine evidence. | S2P tests check fixture outputs (backend/tests/test_s2p_evidence.py:21, :66); no count-derived ratio test. Reference: §4.17 S2P-1; §5 Supplier Aster; GUARD-8 |
## 5. Audit 4 — Scorer/investigation coupling

The shared adapter prefers scorer.gae_scorer, then _scorer, then the object itself (investigation_router.py:125–139). Category names are read from several objects; factor names may be supplied explicitly from each preset or hand-written in SOC. Sigma searches sigma/_sigma of shape (d,), otherwise returns ones; tau searches tau/temperature, otherwise .1 (:170–198). This is internal-attribute probing, not a stable metric snapshot API.

Current local replay uses unit sigma and tau=.1 for every domain, matching the shared adapter's fallback semantics. **Learned DK is neither sigma nor KUtilityStore.** Exporting ones faithfully reports the current VLD fallback, but does not establish parity with production's learned metric. A learned sigma should only be surfaced through a reviewed metric contract, with its meaning and calibration established; blindly substituting a noise estimate would change both scoring and Q.

The two domain loops use Euclidean norms, category-spanning selection and different confidence normalization. DataOps also has a heuristic signal-distance overlay. Thus three paths named investigation are not numerically interchangeable.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F11 — P0 | copilot-sdk/copilot_sdk/scoring/investigation.py:66–74; copilot-sdk/copilot_sdk/backend/investigation_router.py:55–62, :87–93; graph-attention-engine-v50/gae/profile_scorer.py:447–488; copilot-sdk/copilot_sdk/backend/scorer_proxy.py:78–84 | **Investigation scoring is not production scoring; contrast is not a faithful production baseline.** The shared engine reimplements a fixed-category diagonal squared-distance softmax. It bypasses factor masks, phase-2 DK/shrinkage and higher-level gates. Unit sigma is not an export of effective production DK weights. SOC's other path additionally compares within-category max probability initially with a final 24-cell softmax. | Expose an immutable public scoring snapshot containing effective metric/masks/tau/vocabulary; use one pure read-only scoring function for surface and final states. Compute the production comparator with matching inputs/information budget. Label margin growth as decisiveness, not correctness. | tests/test_vld_integration.py:235 compares the router to the same reimplementation, not production score_read_only. SOC unequal confidence denominators: investigation_loop.py:54, :166–170 versus services/investigation_router.py:73–86. Reference: §4.17 contrast; §5 contrast data |
| F12 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:142–167, :181–198; copilot-sdk/copilot_sdk/scoring/investigation.py:57–60 | **Unknown categories silently use another tensor; factor order has no semantic contract.** Unknown nonnumeric categories use index 0; numeric categories are clamped. A 2-D scorer ignores category. The response echoes the caller's category while scoring another one. Length matching does not prove factor-name order; generic factor_i fallbacks can return wrong/missing evidence. | Reject unknown categories, use explicit vocabulary/schema hashes, and validate provider factor order against the selected tensor. Resolve temperature zero explicitly rather than using truthiness fallback. | Fresh typo→index0 probe reproduced. No negative category/permuted-name test in tests/test_investigation.py. Reference: — |
| F13 — P0 | copilot-sdk/apps/dataops/backend/app/main.py:699–708; copilot-sdk/apps/dataops/backend/app/services/investigation_router.py:137–157; copilot-sdk/copilot_sdk/scoring/scorer.py:2696 | **DataOps domain endpoint can silently use bootstrap instead of its active scorer.** The pattern loop is constructed with CompoundingScorer. Its helper looks only for .centroids/.mu, while CompoundingScorer exposes .gae_scorer; it falls back to DataOpsPreset bootstrap. The shared SDK route unwraps correctly, so its passing result does not validate this domain endpoint. | Use the same explicit snapshot API in both loops. Fail visibly when state cannot be read; do not silently substitute priors. Test a non-bootstrap learned tensor through /api/dataops/investigate. | Pattern smoke tests exist (apps/dataops/backend/tests/test_investigation_patterns.py:86); no active-versus-bootstrap assertion. Reference: §4.17 DO-1/DO-2 |
## 6. Audit 5 — Conservation interaction

The complete shared request path is client → create_investigation_router handler → snapshot reads → optional classifier/K read → VLDInvestigator.investigate → response. It does **not** call CompoundingScorer.learn(), scorer.update(), or an action executor. There is therefore no VLD centroid-learning bypass to demonstrate through this endpoint.

Conservation enforcement in ordinary learning remains a different path: CompoundingScorer checks cold-start/bootstrap versus verified-data conservation before updates (copilot-sdk/copilot_sdk/scoring/scorer.py:2231–2295), and SOC learning evaluates nested conservation before its update path (gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2188–2299). This audit does not re-certify that entire unrelated learn chain.

No VLD-specific conservation snapshot is checked before or after the shared loop. SOC/DataOps rich result models expose not_evaluated_read_only, appropriately describing shadow status. The missing feature is governed **emission/execution**, not permission to inspect evidence under RED. Tests named S1 conservation mean conserving investigation budget; they do not test the conservation law.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F14 — P0 | copilot-sdk/copilot_sdk/backend/investigation_router.py:39–111; gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py:46; gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py:403; copilot-sdk/copilot_sdk/scoring/scorer.py:2231–2295 | **Conservation is absent from the SDK emit contract; domain loops explicitly do not evaluate it.** Returning a shadow recommendation under RED is not a bypass of learn(), since investigation never calls learn or executes an action. But the shared response has no eligibility/abstention status, and none of these VLD handlers implements the claimed frozen conservation emit gate. It cannot be promoted to an executable governed action contract. | Snapshot conservation with geometry, allow read-only investigation, attach final eligibility/abstention, and enforce it in any downstream executor. Keep learning enforcement separate. Test RED/UNKNOWN versus allowed cold-start/bootstrap states. | Fresh RED-tagged scorer probe still returns a normal response. Tests named s1_conservation test budget suppression, not conservation status. Reference: architecture v4 §2.3; §5 emit gate; SOC-1 GREEN-at-emit |
## 7. Audit 6 — KUtilityStore integrity

Schema: k_utility(category TEXT, dimension INTEGER, weight REAL DEFAULT .5, n_updates INTEGER DEFAULT 0, PRIMARY KEY(category,dimension)). Constructor runs CREATE TABLE IF NOT EXISTS and commits; there is no versioned migration. Reads fill a length-d vector with .5, overwrite in-range dimensions from rows, and ignore out-of-range stored dimensions.

For each successful trace step: correct → add .02 (double to .04 if step.flipped), cap at 3; incorrect → subtract .005, floor at .1. Rates are caller parameters. Only successful reads receive updates; empty/error reads cannot be credited or penalized. A final correct outcome does not identify which read caused improvement. Architecture v4 §2.4 explicitly treats step credit as an estimator needing counterfactual/exploration evidence, not an observed fact.

Sources: copilot-sdk/copilot_sdk/scoring/investigation.py:194–258; copilot-sdk/docs/design/vld_graph_reasoning_architecture_v4.md:96–107. All five local dedicated tables were read with SQLite mode=ro and contained zero rows during the replay. No deployed model-file constructor was found in the five mains.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F15 — P0 | copilot-sdk/copilot_sdk/scoring/investigation.py:216–258; s2p-copilot/backend/app/vld_preseed.py:114–125; s2p-copilot/backend/tests/test_s2p_evidence.py:80–96 | **K is wired but not learned; advertised weights are outside the learning range.** No production update_weights caller was found in the three repos; local dedicated K tables are empty. Normal updates stay in [0.1,3.0], while the claimed 'learned K' example uses 5 and 6 (and another test uses 8). The core accepts arbitrary injected weights, so those synthetic tests do not prove the deployed learning path. | Define verified-outcome linkage and identifiable credit assignment outside inference, then validate reachable bounded weights. Treat custom-K experiments as interventions, not learned production behavior; do not insert magic weights to pass a demo. | K unit updates/bounds tested at tests/test_investigation.py:195–230. Production learning→trace→K integration absent. Reference: GUARD-6; architecture v4 §2.4 |
| F16 — P1 | copilot-sdk/copilot_sdk/scoring/investigation.py:203–214, :236–258; copilot-sdk/apps/trading/backend/app/main.py:127–137; s2p-copilot/backend/app/main.py:36–46 | **K persistence lacks atomic learning, tenant/schema versioning and explicit lifecycle.** The key is category+dimension only. A shared connection uses check_same_thread=False without a K lock. Concurrent read-modify-write updates can lose weight changes while incrementing counters. Dimension reorder silently reinterprets historical weights; no versioned migration or explicit close is wired. | Use transactional atomic updates or a serialized store API; key by tenant/domain/policy/factor-schema, migrate explicitly, and close connections in app lifespan. Current read-only requests do not themselves exercise the update race. | Per-category isolation tested, concurrent updates/schema migration/lifespan untested (tests/test_investigation.py:217). Reference: — |
## 8. Audit 7 — SituationClassifier integrity

The ten features, in order, are margin, entropy, q_spread, q_entropy, p_max, p_second, q_max, q_mean, d_min and d_gap. d_min/d_gap use the same inverse-variance squared distances as SDK investigation. Inputs' derived features must be finite.

Budgets are **S1=0, S2=3, S3=1, S4=2, S5=3, S6=4**, not sequential 0–4. Fallback boundaries are d_min<.05 → S1, d_min>.5 → S6, otherwise S3, each with confidence=.5. Equal-to-.05 and equal-to-.5 are S3. S2/S4/S5 require a model prediction. A supplied existing path is loaded with joblib.load and expected to expose predict (optionally predict_proba) on a (1,10) array; unknown predicted labels fall back to default_budget. Missing model path silently leaves heuristic mode; corrupt model loading can raise at construction.

Sources: copilot-sdk/copilot_sdk/scoring/situation_classifier.py:11–31, :34–80, :92–129. All five current mains call SituationClassifier() without a model path. There is no evidence here of a trained classifier in production.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F17 — P1 | copilot-sdk/copilot_sdk/scoring/situation_classifier.py:11–30, :92–129 | **Fallback S1 means near a centroid, not a confident unique action.** Fallback emits only S1/S3/S6, with d_min<0.05 / middle / >0.5; it does not threshold margin. Identical centroids at v produce margin0 and S1 budget0. Current Purchasing S1 is actually classified S3; its explicit budget0 hides that. Model loading is trusted joblib with no schema/version verification. | Document the fallback precisely, add ambiguity/separation conditions for S1, validate model feature order/class labels and provenance, and test boundaries. Joblib files must come from a trusted deployment artifact source, not requests. | Near/far tests exist at tests/test_investigation.py:245, :267; degenerate/boundary/model-compatibility cases untested. Fresh identical-centroid probe reproduced S1 at margin0. Reference: — |
## 9. Audit 8 — Cross-copilot consistency

All five shared mounts have K and heuristic classifier objects, default_budget=2, explicit factor vocabularies and the common shared endpoint. SOC and DataOps additionally have independently implemented pattern endpoints. Only SOC has a located investigation UI, and it calls the SOC pattern endpoint rather than the shared one.

DataOps's graph story has **two schema worlds**: graph_contract.py:23–30 declares Decision→Alert→Pipeline, while graph_queries.py:179 reads DataQualityAlert→AFFECTS→PipelineSystem. Generic seed_graph.py:279–309 does create indirect Decision→Pipeline topology. That must not be described as entirely absent; its exact persisted VLD fixture usage remains unverified. Source evidence and the consistency matrix in §18 distinguish these layers.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F18 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:132–149; copilot-sdk/copilot_sdk/backend/scorer_proxy.py:31–41, :65–76; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:38–40, :64–92; copilot-sdk/apps/dataops/backend/app/main.py:704–708 | **Snapshot consistency differs across the loops.** Shared VLD copies mu and mutates only request-local v, which is good. However callers release the proxy lock before snapshot copying and sigma/K are read separately. SOC/DataOps pattern loops retain mutable scorer references across awaited reads, so concurrent learning can change geometry mid-episode. | Capture a single versioned geometry/metric/K/conservation snapshot under the scorer's lock. Pass immutable data to both loop families and record its hash. | Centroid nonmutation tested in SOC test_investigation_loop.py:301; concurrent learn/investigate snapshot coherence untested. Reference: Inference Side-Effect Contract; §5 frozen policy |
| F19 — P1 | copilot-sdk/apps/dataops/backend/app/services/investigation_loop.py:81–94; copilot-sdk/apps/dataops/backend/app/services/investigation_router.py:87–101, :169–179; gen-ai-roi-demo-v4-v50/backend/app/services/triage_providers.py:63–81 | **DataOps aggregation and route heuristics differ from the stated re-extraction mechanism.** DataOps takes elementwise maxima over surface and evidence, so evidence can never lower a factor. Its route distances are also minimized with hand-authored factor heuristics, not solely learned centroid distances. SOC re-extracts through a different evidence adapter; SDK overwrites one factor at a time. | Version each aggregation and route policy; justify monotonicity per factor or replace it with a common evidence transformation. Separate heuristic ablations from centroid-conditioned routing claims. | DataOps fixture smoke/narrative tests exist; counter-evidence requiring a downward update and heuristic-vs-centroid attribution are untested. Reference: §4.17 DO-1/DO-2; implementation v4 §2.4 |
| F20 — P0 | copilot-sdk/apps/dataops/backend/app/services/investigation_router.py:69–79, :160–166; gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py:315–321, :377 | **Logged propensities are not behavior-policy probabilities.** DataOps deterministically picks the first eligible category but logs its softmax score as propensity, and records only the selected candidate. SOC Stage1 picks a correct/ordered branch but logs 1/number_of_branches. These values cannot support inverse-propensity/off-policy estimates. | For deterministic selection log selected probability1, full eligible candidate set and no exploration support; only log stochastic propensities when sampling actually uses them. Reject OPE on unsupported actions. | Trace-field presence tested, probability-of-actual-selection semantics untested. Reference: E-1; architecture v4 §2.4 |
## 10. Audit 9 — Edge-case and boundary analysis

The following are fresh in-memory probes of the actual SDK classes, not pytest counts. No probe modified core source. Geometry was deliberately constructed to isolate each boundary.

| Case | Observed behavior | Existing coverage / consequence |
| --- | --- | --- |
| Budget0 | No reads, zero successful steps; surface=final | Covered by tests/test_investigation.py:168 and S1 fixtures |
| All evidence None | Attempts consume budget, no trace rows, unchanged vector/action | Covered at :153 and :313; missing-attempt telemetry remains F02 |
| Budget1000, d=2 | Reads [0,1] only; response budget_used=1000 | Dimension bound works; actual-use metadata wrong, F05 |
| Identical 2×2 centroids | P=[.5,.5], margin0, Q=[.01,.01], deterministic [0,1] reads | No NaN for finite data; no futility halt. Classifier at the centroid returns S1 despite margin0 |
| Single action | P=[1], margin1, Q=[.01,.01]; still investigates | Accepted but meaningless; no explicit A>=2 contract |
| Finite evidence2 / −1 | Clipped to1 /0 | Intended range clipping; finite-only check missing |
| NaN evidence | Becomes1.0 | Reproduced data-quality defect, F03 |
| NaN mu / sigma / tau | NaN probabilities/margins, action0 can be returned internally | Constructor accepts; HTTP serialization can fail later |
| Sigma0 | Precision floor1000; valid but saturated probabilities | Floor prevents division by zero; may overstate certainty |
| Tau0 | ValueError: tau must be positive | Correct core guard; router truthiness fallback may replace an exposed zero |
| Empty vector with d=2 | ValueError shape mismatch | Correct guard; HTTP list min_length and core shape complement one another |
| d=0 geometry | score can produce a tie, then argmax(empty Q) raises | Constructor must reject zero factors |
| A=0 geometry | max(empty logits) raises | Constructor must reject zero actions |
| Unknown category “typo” | Uses category index0 | Reproduced; F12 |
| RED-tagged scorer | Returns ordinary shared investigation response | Confirms absence of an emit gate; no learning performed |
| Provider raises / K connection fails | Handler converts to400 or503, no partial trace | Source trace at ROUTER:108–111; failure injection not included in the 30 existing functions |

Tie behavior, no-repeat dimensions, negative budget clamping and zero K behavior are source-traced at CORE:95–111, :125–141. There is no infinite loop for valid fixed d: range(budget) is finite and dimensions are exhausted. These observations do not imply a wall-clock deadline (F25).

## 11. Audit 10 — Test coverage and quality

The direct VLD/measurement/refresh inventory contains **19 Python files, 271 test-function definitions**, plus **7 SOC Playwright cases**. Definitions are not collected pytest cases: the shared integration file has 27 definitions, including a five-domain parameterization, yielding 31 cases in the prior sweep. The broad literal search also matches many unrelated “evidence” and “investigate” tests; §17 inventories those separately instead of inflating the VLD count.

Fresh validation executed the **30 existing functions** in tests/test_investigation.py with their existing geometry/client fixtures, replacing only the tmp_path-backed K connection with SQLite :memory:. All 30 passed. This was direct function execution, **not a fresh full pytest baseline** and not a claim that application startup/conftest behavior passed. It respects the intent to avoid authoring test files and persistent test databases. Source-defined test assertions were not edited.

The Sep12 resweep's 23P/8F VLD result and SDK baseline failures are historical; multiple seeds, checkpoints and harness expectations have since changed. They are not re-presented as current pass/fail counts.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F21 — P1 | copilot-sdk/tests/test_investigation.py:138–165, :168–171; copilot-sdk/tests/test_vld_integration.py:179–188, :227–244; copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:86–101; gen-ai-roi-demo-v4-v50/frontend/tests/e2e/investigation_panel.spec.ts:117–135 | **Tests cover implementations more strongly than independent contracts.** Highest-Q expected value is computed by the same Q function; flip test can pass without a flip; contrast test checks types only. Purchasing tests use custom geometry, sigma=.16, tau=.05 and K=100. S2P integration explicitly accepts the failed flip and excludes it from robustness. UI tests mock the backend. | Add independent equation/route/metric contracts, forced flip assertions, startup-equivalent endpoint tests, and honest negative-control labels. Keep synthetic unit fixtures, but never use them as production acceptance evidence. | 30 existing core test functions passed via in-memory execution in this audit. This does not close the independent coverage gaps. Reference: GUARD-1/3/8 |
## 12. Audit 11 — Documentation versus implementation

Math synopsis v18 Eq.4-final is softmax(−kernel_distance/tau), with squared L2/diagonal kernels and tau=.1 (copilot-sdk/docs/design/math_synopsis_v18.md:438–462). The root and product v18 copies and located blogs/new_docs/math_synopsis_v20.md contain **no VLD Q/K-update/confidence-gating section** under the searched VLD/Q_k/KUtility terms. It would be an invented citation to say the prompt's sigma×centroid_diff/tau is the synopsis's implemented equation. The actual Q is explicitly documented by the gap analysis at :23–32 and implemented at CORE:106–111.

Formula comparison: squared-distance action softmax matches the synopsis only when the effective metric and category agree; gated convex interpolation matches the gap analysis at :29; argmax flip detection has no confidence threshold. The SOC/DataOps pattern loops' norm-based softmax is different from squared L2 at fixed tau, even when the winner is unchanged.

The latest architecture v4 requires candidate/edge/cost/policy/outcome trajectories and distinguishes score-keyed branching from literal category routing. Implementation v4 also documents negative action-value results and geometry concerns; its positive “routing works” line does not override those caveats. The five v2.8 beats are explicitly ARCH. They are not acceptance evidence for a production paper.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F22 — P2 | copilot-sdk/docs/design/vld_implementation_design_v4.md:89–118, :413–452; copilot-sdk/docs/design/vld_centroid_propagation_diagnosis_2026-09-12.md:71–84; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:30, :86–89; copilot-sdk/scripts/refresh_demo_centroid_checkpoints.py:205 | **Authority documents describe different dates and implementations as current.** The implementation doc still says damping/re-extraction is unbuilt although reextract is default. Propagation diagnosis and prior sweep describe five collapsed checkpoints; current Trading/Purchasing have checkpoint6 with differentiated actions. The historical diagnoses were not necessarily wrong when written. | Mark old reports immutable historical snapshots, add geometry/source hashes and supersession links, and publish one current implementation/API matrix. Reconcile demo v2.8 with revised seed contracts through explicit approval of the narrative, not silent test edits. | Refresh regression tests exist at tests/test_centroid_refresh.py:122–184; documentation freshness checks absent. Reference: — |
| F23 — P0 | copilot-sdk/docs/design/vld_implementation_design_v4.md:417–452, :532–567; copilot-sdk/docs/design/vld_graph_reasoning_architecture_v4.md:219–240; gen-ai-roi-demo-v4-v50/backend/scripts/evaluate_multihop_stage1.py:3, :404–405 | **Existing routing/demo numbers do not establish production rho or depth value.** Category recovery after stripping labels is not within-category conditional routing accuracy. The design's gate beats majority/random but not the best content-rule comparator. Stage1 terminal labels can be assigned from correct-branch membership. Tuned 15-case flips and zero hurts do not supply adjudicated held-out outcomes or causal evidence of value. | Pre-register score-keyed cases, outcome/branch adjudication and time cutoffs; evaluate identical scoring/read-cost arms against best content rule/majority/breadth, with case-level splits and uncertainty. Label existing Stage1 experiments planted positive controls. | Rho/value-chain tests cover report arithmetic and synthetic controls; real held-out branch/outcome evaluation is absent. Reference: GUARD-1/3/5/7; architecture v4 §5 |
## 13. Audit 12 — Security and safety boundaries

Malicious evidence cannot cause **centroid drift inside the shared loop**: mu is copied and only a local v is updated (CORE:53, :124, :148–150). It can change a recommendation, saturate factors via permissive numeric coercion, or cause an error; downstream action authority remains a separate concern. Budgets do not permit infinite iteration, but request lists/strings have no maximum length and provider payloads have no explicit VLD size/deadline cap.

The SDK trace carries decision identifiers, source labels, factor names and full before/after vectors, not full raw provider dictionaries. Rich SOC traces additionally reveal evidence keys and graph edge/policy details. Such identifiers/context may be sensitive even without raw user names. Current handlers do not intentionally persist these traces; SOC uses PIIRedactionMiddleware, while equivalent cross-copilot VLD redaction is not established. Raw exception text in shared responses is another disclosure path (F06).

SOC AuthMiddleware is mounted; S2P mounts it when auth is enabled. Trading/Purchasing/DataOps use tenant-context middleware, which is not authentication. This is a code-boundary assessment, not a penetration test or assertion about external gateway protection.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F24 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:16–21, :53–76; copilot-sdk/copilot_sdk/config/tenant.py:21–40; gen-ai-roi-demo-v4-v50/backend/app/main.py:79–82; s2p-copilot/backend/app/main.py:307–311 | **VLD resource and tenant authorization is not enforced by the shared contract.** Caller supplies decision ID, category and vector independently; the shared handler does not bind them to an authorized stored decision. K keys and process-local registries have no tenant dimension. SOC has auth/PII middleware and S2P optional auth, so this is not a claim that all deployments are unauthenticated. | Bind request identity, tenant and decision ownership, validate category/schema against the record, and expose caller-supplied vectors only on an explicit engineering endpoint. Add cross-tenant evidence/K isolation tests; redact source/error identifiers. | No VLD cross-tenant/ownership tests found. Existing general tenant/auth tests do not exercise these stores and IDs. Reference: Inference safety; GUARD-3 |
## 14. Audit 13 — Performance

Let A=actions in the selected category, d=factors, b=min(requested budget,d), r=successful evidence reads. A shared score costs O(A·d), margin/top-two ranking O(A log A), Q O(d+A log A), and trace vectors O(r·d). For fixed geometry the loop is O(b·(A·d+A log A)) plus provider latency. At b=d, this can be O(A·d²); it is not quadratic in stored decision-history size because the core does not scan history. Trace storage can likewise be O(d²) when every dimension is read.

Core score evaluations for b attempted dimensions without an extra exhaustion iteration: **2+b+r** (surface + one before each attempt + one after each successful read + final). With all evidence present and Trading d=10,budget4: **10 core scores**, **11 through the shared router** because it scores once more for classification. Q is recomputed from scratch each attempt; it is not incrementally cached. If budget>d, one extra iteration may re-score before observing all Q entries=-1 and stopping.

The SOC/DataOps pattern loops search C×A centroids repeatedly. DataOps stacks all admitted vectors each pass (DO loop:84–85), costing O(b²·d) cumulatively; SOC re-extraction also revisits accumulated evidence. DataOps tree flattening and S2P deep copies add data-dependent work. No measured production latency percentile was produced in this audit. The bounded six-to-ten-factor NumPy work is not a proxy for live graph timing.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F25 — P1 | copilot-sdk/copilot_sdk/scoring/investigation.py:131–151; gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:110–125; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:74; copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:341–378 | **Read count is bounded, but wall-clock work is not.** No VLD-specific per-read/episode deadline or cancellation policy exists. A synchronous provider can hold a worker; a slow graph call can stall a domain async handler. Legacy pattern budgets count patterns while each pattern may read multiple nodes; reported read_cost is not a global enforced node/cost budget. | Add measured per-read/episode deadlines and provider cost accounting; enforce admission against remaining cost, bound payloads, and return an explicit timeout/halt record. Benchmark realistic graph latency separately from NumPy cost. | Budget unit tests exist; slow/hung-provider and cost-budget tests are absent. Reference: §5 C4; GUARD-7 |
## 15. Audit 14 — v2.8 demo-scenario gap analysis

The critical distinction is **a narrow fixture action flip versus the full specified beat**. Fresh local replays below show 14/15 action-pair matches and 9/10 flips. They do not show E-1 persistence, truthful branch attribution, a governed emit action, or a completed Loom.

The shared InvestigationTracePanel was not found. SOC's differently named InvestigationPanel is implemented and mounted; it renders per-step cards and a side-by-side action/confidence comparison. It is a partial starting point, not the specified shared surface. The S2P frontend is under copilot-sdk/apps/s2p, not s2p-copilot/frontend; both that tree and the three SDK domain frontends were searched. No VLD panel or cut manifest was found there.

SOC campaigns.py really creates locked adjacent-bucket CONTINUES edges. DataOps seed_graph.py really creates Decision→Alert→Pipeline edges. Neither fact establishes that the new VLD showcase identifiers have the exact persisted evidence paths required by v2.8. The absence statements below are specific to those contracts, not a denial of general graph infrastructure.

v2.8 itself has conflicting S2P wording: the main beat at :1065–1067 is receipt-first/one read, while the integration bridge at :1078 is contract→supplier→receipt. The present preseed implements contract→supplier. Choose one explicit contract before judging read order. Also, v2.8 SOC-2 requires a flip after an empty read; the shared loop deliberately leaves v unchanged on None. These script contradictions need design resolution, not fabricated trace rows.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F26 — P0 | gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:483–499; gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py:315–317, :336, :385–401 | **SOC Stage1 demo endpoint uses ground-truth routing and output overrides by default.** The endpoint calls run_stage1_investigation without force_correct=False. The default selects correct_branches and, if a trace exists, returns ground_truth_action and ground_truth_confidence. A rendered correct action therefore does not demonstrate that the scorer selected the route or final action. | Put oracle replay behind an explicitly labeled positive-control endpoint/mode; use non-oracle policy and actual computed output on the investigation demo. Add a fixture whose oracle and scorer disagree and assert the public mode cannot substitute oracle output. | Multihop tests assert expected labeled outcomes (backend/tests/test_multihop_wiring.py:102–142); no public-mode oracle-leakage regression test. Reference: SOC beats; GUARD-1/3/8 |
| F27 — P0 | gen-ai-roi-demo-v4-v50/frontend/src/components/InvestigationPanel.tsx:100–139, :211–261; gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/AlertTriageTab.tsx:910; gen-ai-roi-demo-v4-v50/frontend/src/lib/api.ts:181 | **SOC panel exists, but shared panel and honesty requirements are missing.** The SOC panel renders API traces and a contrast, but no PLANTED FIXTURE / ROUTING ACCURACY badges, content-keyed tags or taken-versus-dimmed alternatives. It exposes residual, propensity and distances in customer UI. It labels zero trace as convergence even when no pattern was available; it does not clear a previous result on alert change or protect against stale async responses. No shared InvestigationTracePanel or domain counterparts were found. | Build the shared versioned component, render required badges from provenance by default, show failed/empty attempts and alternatives, use buyer language, and bind async responses to the active case. Keep engineering details behind an engineering mode. | Seven SOC Playwright tests exist but mock API responses; no guard badges, alert-switch race or persisted replay test. Reference: §4.17 surface; GUARD-3/4/8/9 |
| F28 — P0 | copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_8.md:1253–1258; gen-ai-roi-demo-v4-v50/frontend/src/components/tabs/AlertTriageTab.tsx:910; copilot-sdk/copilot_sdk/backend/investigation_router.py:50 | **The four v2.8 VLD Loom insertions are not wired.** No VLD beat configuration containing ARCH, PLANTED_FIXTURE, RHO_UNMEASURED and API warmup entries was found across SDK/SOC/S2P frontends. Having a manually runnable SOC panel does not create L-SOC/L-DATAOPS/L-S2P/L-VLD sequencing or the silence moment. | Author four cut manifests only after endpoint/panel/fixture contracts are stable; pin request bodies/budgets, geometry/fixture IDs, silence cues and roadmap badges. Validate warmup URLs against mounted routes. | No VLD Loom configuration/sequence tests found. Reference: §7.2 all four insertion points |
| F29 — P0 | copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_8.md:1023–1067; gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:10–49; copilot-sdk/apps/dataops/backend/app/vld_preseed.py:26–35, :85–95; s2p-copilot/backend/app/vld_preseed.py:65–96 | **All five original v2.8 beat contracts remain incomplete despite current seed flips.** SOC-1 uses credential_access monitor→escalate, not lateral_movement investigate→escalate at .04→.31. SOC-2 is TI-empty→identity, not auth-empty→process. DO-2 is quality_anomaly refer_to_specialist→escalate, not resource_quota read-wide/referral plus a .93 sister case. S2P-1 is contract→supplier, not receipt-first accept-with-adjustment. DO-1 has MATKL_V2 evidence but not the complete graph/panel/handoff contract. | Explicitly choose between implementing original beats and publishing revised truthful beats. Pin categories, action vocabulary, step order, computed quantities, required evidence and frontend endpoint; never equate matching IDs with matching narratives. | Current fixture replays validate narrower seed actions; no end-to-end original beat acceptance tests. Reference: §4.17 all five beats |
| F30 — P0 | gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:20–49; gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1148–1212; copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:288–291; s2p-copilot/backend/app/services/s2p_context_builder.py:150–174; copilot-sdk/apps/dataops/backend/app/seed_graph.py:279–309; copilot-sdk/apps/dataops/backend/app/graph_contract.py:23–30; copilot-sdk/apps/dataops/backend/app/graph_queries.py:179 | **Required showcase topology, temporal eligibility and planted-record package are incomplete.** SOC campaign infrastructure exists, but its two showcase alerts are in different campaigns and the seed does not create the required shared Decision→Alert→Campaign→CONTINUES path. DataOps DOES build Decision→Alert→Pipeline edges in seed_graph.py; that is an indirect attachment, not absent infrastructure. Their persistence for the VLD billing_api case and use by investigation are not demonstrated; graph_queries.py also reads DataQualityAlert/PipelineSystem instead of the contract's Alert/Pipeline. Supplier matching filters supplier/category and sorts latest with no as-of cutoff. VLD seeds lack complete versioned S0/branch-set/adjudication/trajectory packages. | Materialize and validate the exact linked fixture records, make time cutoff part of matcher API, and add version/hash/PLANTED provenance plus held-out branch adjudication. Do not conflate separate Stage1 branch fixtures with these 15 showcase seeds. | Topology and fixture-key tests exist, but exact v2.8 cross-record/cutoff contracts are untested. Reference: §5 topology, fixtures and cutoff |
## 16. Audit 15 — Astra sweep fidelity

Current tooling has improved since the resweep: wiring() now recognizes _vld_k_router_kwargs and classifier helper expansion (tests/vld_validation_report.py:75–87), so the old “K unwired everywhere” printout is no longer a current finding. The missing old test-name reference also has changed; the previous generator crash is historical, not asserted to recur.

The current collector still uses SQLite snapshots, profile=test and enable_rl=False, plus only the L5 centroid overlay. Its temporary outbox wrapper is at :341–350. The integration suite imports that same collector rather than independently constructing production app state. Constructor equivalence is partial: startup_restore.py:42 and :47 also restore DK/conservation, and the application proxies construct with evolution/consolidation enabled (scorer_proxy.py:34–39). Those differences must be assessed separately from the invariant read-only nature of a VLD episode.

False positives: two Purchasing action flips can pass revised [5,4]/[4,3] assertions while violating the narrative; forced budget2 can hide a one-read classifier path; domain endpoint bootstrap/oracle behavior is not exercised; identical router/core calculations can agree while production metric differs. False negatives: a genuinely trained and deployed nonuniform K or different AGE geometry could change an offline result. **No such rescue is established locally:** K tables are empty and the custom S2P example is not evidence of reachable learned weights. Ordinary SOC non-showcase graph evidence can also be available live but absent from registry-only offline replay.

In particular, S2P-2's modified test is a useful negative-control assertion, but it cannot satisfy a contract that still claims flag_leakage→auto_approve.


| Finding / severity | Evidence (workspace-relative file:line) | Description and impact | Recommended fix | Coverage / v2.8 |
| --- | --- | --- | --- | --- |
| F31 — P0 | copilot-sdk/tests/vld_validation_report.py:194–285, :341–350; copilot-sdk/tests/test_vld_integration.py:17–22; copilot-sdk/copilot_sdk/scoring/startup_restore.py:142 | **Sweep tools do not reproduce complete application inference.** Report and integration share collect_all, which is good consistency but not independent verification. Local checkpoints plus L5 centroids are restored; full startup DK/state, live AGE, mounted middleware and the separate domain loops are not. K is not injected; K data is checked in scoring DB instead of dedicated K DB. Provenance calls post-L5 state bootstrap when unequal to checkpoint. | Make a read-only production snapshot adapter that captures the full metric and governance state, explicitly inject the dedicated K snapshot, and exercise the actual mounted route used by each UI. Separate fixture/component/live acceptance matrices. | Collector's own equality tests cannot detect omissions common to both paths; no live-endpoint equivalence test. Reference: §4.17 API; paper fidelity |
| F32 — P0 | copilot-sdk/tests/vld_validation_report.py:45–52, :293–302, :412–430; copilot-sdk/tests/test_vld_integration.py:179–188, :227–231 | **Sweep readiness and narrative tests can certify the wrong contract.** PAPER_READY uses action match, final margin and hurts; it reports but does not include narrative/S1 checks in the gate, and DEMO_READY does not require wiring. Purchasing expected dims were changed to actual [5,4]/[4,3] while seed text still says [5,6]/[4,5]. S2P-2 becomes an expected nonflip in integration and is excluded from robust-flip checks, but still claims auto_approve in seed/report. | Derive one versioned contract from independently reviewed narrative/adjudication, test ordered attempts, and include all required predicates in readiness. Report K-dependent scenarios as blocked until actual reachable K is validated; keep negative-control tests separate. | Existing tests now explicitly accept the S2P nonflip; fresh source audit and replays exposed Purchasing story mismatch. Reference: GUARD-1/7/8; acceptance-gate semantics |
| F33 — P1 | copilot-sdk/copilot_sdk/backend/investigation_router.py:65–72; copilot-sdk/tests/vld_validation_report.py:277–291; copilot-sdk/apps/trading/backend/app/vld_preseed.py:10–42; copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:176–188 | **Default classifier budgets can invalidate a forced-budget showcase.** All primary sweep cases force budget2. Current Trading TRD1/TRD2 and DO1/S2P1 classify S3 with budget1; their two-read narrative is not an automatic production behavior. Purchasing's S1 classifier is S3 despite an explicit fixture budget0. Passing forced requests does not establish fallback behavior. | Pin exact demo requests, make explicit overrides visible, and add default-budget route/action assertions separately. Avoid silently treating metadata budget as a request override; the endpoint does not load fixture metadata. | S1 budget checks exist; forced and automatic requests are collected but automatic non-S1 action/narrative parity is not an acceptance condition. Reference: GUARD-7; §5 request contract |

## 17. Test coverage matrix

The counts below are source-level test-function definitions, not a fresh pytest collection or coverage-percentage measurement. Categories are an audit classification of each test's primary purpose, based on names and assertions; they are not repository markers, and integration here does not imply live AGE. Parameterized cases can exceed definition counts. The 30 core functions are the only existing suite functions freshly executed in this audit; application and frontend rows are inspected coverage.

| File: first test line | Unit | Integration | Edge | Regression | Definitions | Audit areas touched |
| --- | --- | --- | --- | --- | --- | --- |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_evidence.py:48 | 5 | 2 | 1 | 6 | 14 | 3–4, 8, 14 |
| copilot-sdk/apps/dataops/backend/tests/test_investigation_patterns.py:42 | 8 | 1 | 1 | 2 | 12 | 1–2, 4–5, 9 |
| copilot-sdk/apps/dataops/backend/tests/test_multihop_evaluation.py:31 | 4 | 1 | 4 | 1 | 10 | 1, 9, 11, 14 |
| copilot-sdk/apps/purchasing/backend/tests/test_multihop_evaluation.py:31 | 5 | 2 | 3 | 2 | 12 | 1, 9, 11, 14 |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:20 | 4 | 2 | 1 | 6 | 13 | 3–4, 8, 14 |
| copilot-sdk/apps/trading/backend/tests/test_multihop_evaluation.py:30 | 5 | 2 | 4 | 1 | 12 | 1, 9, 11, 14 |
| copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:56 | 4 | 2 | 1 | 6 | 13 | 3–4, 8, 14 |
| copilot-sdk/tests/test_investigation.py:80 | 19 | 1 | 9 | 1 | 30 | 1–2, 6–7, 9 |
| copilot-sdk/tests/test_vld_integration.py:85 | 0 | 27 | 0 | 0 | 27 | 3–4, 8, 14–15 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_centroid_training.py:36 | 10 | 4 | 0 | 0 | 14 | 4, 8, 15 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_investigation_loop.py:126 | 12 | 0 | 6 | 2 | 20 | 1–2, 4–5, 9 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_evaluation.py:29 | 4 | 1 | 3 | 3 | 11 | 1, 9, 11, 14 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_wiring.py:31 | 10 | 2 | 0 | 1 | 13 | 1, 9, 11, 14 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rho_measurement.py:64 | 15 | 0 | 2 | 1 | 18 | 11, 14 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:68 | 5 | 1 | 3 | 3 | 12 | 3–4, 8, 14 |
| gen-ai-roi-demo-v4-v50/backend/tests/test_value_chain_experiments.py:22 | 9 | 0 | 1 | 2 | 12 | 11, 14 |
| s2p-copilot/backend/tests/test_multihop_evaluation.py:45 | 4 | 1 | 4 | 1 | 10 | 1, 9, 11, 14 |
| s2p-copilot/backend/tests/test_s2p_evidence.py:16 | 6 | 2 | 1 | 3 | 12 | 3–4, 8, 14 |
| copilot-sdk/tests/test_centroid_refresh.py:122 | 2 | 0 | 1 | 3 | 6 | 4, 8, 15 |

Total: **271 Python definitions across 19 files**. The additional seven browser cases are at gen-ai-roi-demo-v4-v50/frontend/tests/e2e/investigation_panel.spec.ts:229, :236, :246, :257, :264, :271 and :278. They cover panel/API-display behavior against intercepted responses (:117–135), not live scorer/evidence equivalence. The panel tests therefore cannot refute F26 or establish the five Loom contracts.

### Top ten missing independent regression contracts

| # | Untested contract | Code requiring coverage | Why current tests are insufficient |
| --- | --- | --- | --- |
| 1 | Production surface and investigation scores match under masks, learned DK, sigma and category | copilot-sdk/copilot_sdk/backend/investigation_router.py:132–180; graph-attention-engine-v50/gae/profile_scorer.py:447–488 | The core test compares its own metric; collector and integration share the same reconstruction (F11/F31). |
| 2 | Public SOC investigation cannot read oracle branch/action labels | gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:483–499; backend/app/services/multihop_scenarios.py:315–317, :385–392 | Labeled multihop assertions can pass because the handler supplies the answer (F26). |
| 3 | Empty, failed and selected attempts persist and replay with valid policy probabilities | copilot-sdk/copilot_sdk/scoring/investigation.py:138–170; apps/dataops/backend/app/services/investigation_router.py:69–79 | Current tests cover successful fields or in-memory traces, not a durable E-1 episode (F02/F20). |
| 4 | RED/UNKNOWN conservation yields non-emittable investigation results and cannot execute an action | copilot-sdk/copilot_sdk/backend/investigation_router.py:94–106; gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py:46 | No shared conservation contract is exercised. A fresh probe returned a normal result with a RED scorer (F14). |
| 5 | Concurrent learn/investigate holds one immutable geometry/K/governance snapshot | copilot-sdk/copilot_sdk/backend/scorer_proxy.py:31–41; gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:64–92 | Single-thread centroid nonmutation is weaker than episode snapshot coherence (F18). |
| 6 | Verified feedback atomically updates tenant-scoped K through reachable bounded values | copilot-sdk/copilot_sdk/scoring/investigation.py:216–258 | Unit arithmetic/bounds tests do not establish a production caller, credit assignment or concurrent persistence (F15/F16). |
| 7 | HTTP numeric validation rejects NaN/Inf, malformed geometry and evidence consistently | copilot-sdk/copilot_sdk/scoring/investigation.py:44–74, :143–150; copilot_sdk/backend/investigation_router.py:19–31 | Fresh probes expose behavior, but are not committed regression tests (F03). |
| 8 | Unknown category, permuted factor vocabulary and cross-tenant decision access are rejected | copilot-sdk/copilot_sdk/backend/investigation_router.py:19–31, :152–180 | Shape-only validation and synthetic IDs do not establish semantic/ownership checks (F12/F24). |
| 9 | Live graph/provider records obey source normalization, fixture provenance and as-of eligibility | gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:128–194; s2p-copilot/backend/app/services/s2p_context_builder.py:150–174 | Fixture/fake accessors do not test real historical record eligibility or live factor semantics (F08–F10/F30). |
| 10 | Actual default-budget endpoint plus UI satisfies ordered narrative, badges and Loom insertion | copilot-sdk/copilot_sdk/backend/investigation_router.py:65–72; gen-ai-roi-demo-v4-v50/frontend/src/components/InvestigationPanel.tsx:131–255 | Forced-budget numeric tests and mocked browser responses omit the full viewer contract (F27–F29/F32/F33). |

“Untested” here means no independent regression for the stated end-to-end invariant was found in the inspected inventory. It does not mean every individual operation lacks a unit test.

### Broad search inventory, including non-VLD matches

The requested literal search (`investigation|investigate|vld|evidence`, case-insensitive) found **195 Python test-named files** across the three repositories. This list intentionally retains false positives such as general evidence contracts; these are not added to the 271 VLD definition total. Two ancillary paths lie outside the specified tests directories. Locations below point to the first matching source line. A “direct” classification means the file names a VLD controller, classifier, store, multihop evaluator or sweep helper; centroid-refresh is separately included in the targeted matrix because of its coupling relevance.

<details>
<summary>All 195 literal-search matches</summary>

| File: first literal match | All test definitions in file | Classification |
| --- | --- | --- |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:730 | 108 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_evidence.py:8 | 14 | Direct VLD/measurement |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_fixture_closure.py:81 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_dataops_governance.py:11 | 24 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_di.py:44 | 9 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_di_enterprise_query.py:40 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_di_gateway.py:51 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/dataops/backend/tests/test_investigation_patterns.py:11 | 12 | Direct VLD/measurement |
| copilot-sdk/apps/dataops/backend/tests/test_multihop_evaluation.py:39 | 10 | Direct VLD/measurement |
| copilot-sdk/apps/purchasing/backend/tests/test_commodity.py:13 | 20 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_cross_discovery.py:85 | 12 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_evidence.py:52 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_learning_beats.py:22 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_multihop_evaluation.py:39 | 12 | Direct VLD/measurement |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_active_age_live.py:58 | 1 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_control.py:12 | 9 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:7 | 13 | Direct VLD/measurement |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_factors.py:23 | 50 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/purchasing/backend/tests/test_purchasing_graph_status.py:249 | 11 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_claim_gate.py:1 | 6 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_evidence.py:5 | 41 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_market_data_provider.py:12 | 24 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_market_refresh.py:5 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_multihop_evaluation.py:38 | 12 | Direct VLD/measurement |
| copilot-sdk/apps/trading/backend/tests/test_options_factors.py:8 | 36 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_p50_smoke.py:10 | 11 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_prescore.py:132 | 27 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_provenance_label.py:22 | 10 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_regime.py:14 | 27 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_regime_beats.py:15 | 12 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_regime_classifier.py:6 | 35 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_situation_judgment.py:33 | 4 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_subcategory.py:17 | 24 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_trading_backend.py:12 | 38 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:7 | 13 | Direct VLD/measurement |
| copilot-sdk/apps/trading/backend/tests/test_vix_timing.py:9 | 28 | Broad match; not counted as direct VLD |
| copilot-sdk/apps/trading/backend/tests/test_volatility_scenarios.py:34 | 7 | Broad match; not counted as direct VLD |
| copilot-sdk/integrity/test_product_truth.py:11 | 5 | Ancillary broad match |
| copilot-sdk/scripts/test_tab_inventory.py:174 | 55 | Ancillary broad match |
| copilot-sdk/tests/test_archetype_generator.py:110 | 18 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_demo_truth_preflight.py:40 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_di_query.py:157 | 29 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_dual_write_store.py:37 | 21 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_entity_enrichment.py:10 | 32 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_evidence_gate.py:1 | 15 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_integrity_scanner.py:39 | 9 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_investigation.py:11 | 30 | Direct VLD/measurement |
| copilot-sdk/tests/test_jm_rl_cross_copilot.py:130 | 21 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_l5_proof.py:64 | 16 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_measured_transfer.py:12 | 20 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_migration_live_age.py:78 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_migration_resilience.py:62 | 17 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_nl_query_extended.py:114 | 43 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_outcome_protocol.py:43 | 19 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_platform_dump.py:19 | 17 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_promotion_engine.py:113 | 19 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_qualification.py:12 | 18 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_response_models.py:236 | 4 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_rl_domain_rewards.py:39 | 5 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_rule72_sdk_enforcement.py:37 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_scorer_evolution.py:116 | 16 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_situation_analyzer.py:94 | 27 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_snapshot_after.py:12 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_snapshot_after_endpoint.py:12 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_soc_preset.py:26 | 17 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_sqlite_to_age_migration.py:65 | 57 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_substantiation.py:27 | 67 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_verify_state.py:29 | 14 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/test_vld_integration.py:3 | 27 | Direct VLD/measurement |
| copilot-sdk/tests/backend/test_evolution_router.py:213 | 14 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/backend/test_l5_full_flow.py:26 | 3 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/backend/test_scoring_router.py:528 | 44 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/backend/test_self_computation.py:24 | 6 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/backend/test_self_computation_router.py:21 | 19 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/discovery/test_patterns.py:40 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/evolution/test_autonomous_promotion.py:74 | 11 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/evolution/test_context_selector.py:56 | 7 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/evolution/test_toy_rules.py:77 | 8 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/graph/test_protocol.py:49 | 13 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/graph/test_protocol_v2_conformance.py:25 | 98 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/graph/test_soc_age_projection_contract.py:434 | 14 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/scoring/test_conservation.py:67 | 5 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/scoring/test_dataops_preset.py:119 | 15 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/scoring/test_j6_persistence.py:56 | 21 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/scoring/test_persistence_outbox.py:30 | 28 | Broad match; not counted as direct VLD |
| copilot-sdk/tests/scoring/test_trust_traps.py:17 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_integration.py:377 | 10 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_ae_sd_rl_seed.py:15 | 10 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_alert_pool.py:54 | 8 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_chain_contract.py:11 | 12 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_chain_wiring.py:15 | 13 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_chain_wiring_extended.py:15 | 13 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_audit_ci_platform.py:2 | 2 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_authority_ladder.py:92 | 14 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_centroid_export.py:153 | 10 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_centroid_training.py:71 | 14 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cluster_history.py:76 | 11 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_compliance_dashboard.py:23 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_conservation_extended.py:87 | 18 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_control_room.py:25 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_graph_discovery.py:369 | 33 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_repo_contracts.py:6 | 9 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_signals.py:47 | 7 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_cross_tab_consistency.py:43 | 14 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_decision_distance_log.py:79 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_dual_update_fix.py:102 | 11 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_econ1.py:26 | 7 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_eta_cap.py:25 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_eval_upload.py:147 | 33 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evidence_room.py:15 | 8 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evidence_room_conservation_fallback.py:5 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_evolution_ledger.py:160 | 47 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_factor_validation.py:59 | 5 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_flywheel_comparison.py:30 | 5 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_governance_report.py:57 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_investigation_loop.py:1 | 20 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_j6_state_capture.py:84 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_known_issues.py:102 | 1 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_learning_health.py:160 | 13 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_evaluation.py:19 | 11 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_multihop_wiring.py:7 | 13 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_nl_templates.py:256 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_p77_migration.py:98 | 21 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_progressive_learning.py:24 | 5 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_promotion_gate.py:134 | 52 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_quickfix_sweep.py:54 | 6 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_refer_to_analyst.py:28 | 12 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_reward_computer.py:35 | 16 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rho_measurement.py:1 | 18 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_display.py:112 | 9 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_full_pipeline.py:54 | 1 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_rl_triage_integration.py:299 | 29 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_sentinel_integration.py:311 | 15 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_servicenow_triage_integration.py:140 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_shadow_promotion.py:32 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_shadow_runner.py:143 | 34 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulation_eventloop.py:42 | 5 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_simulation_graphstore.py:22 | 1 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_c9b_l5_proof.py:323 | 18 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_c9b_seed_contract.py:51 | 4 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_dk_l5.py:241 | 25 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_domain_profile_pipeline.py:37 | 14 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:7 | 12 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_explainability.py:22 | 18 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_learning_live.py:26 | 3 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_soc_route_validation_runner.py:107 | 39 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_tab7_governance.py:20 | 8 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_tab_content.py:300 | 62 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_triage_c2_compliance.py:31 | 3 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_triage_outcome_contract.py:7 | 5 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_value_chain_experiments.py:1 | 12 | Direct VLD/measurement |
| gen-ai-roi-demo-v4-v50/backend/tests/test_variant_generator.py:10 | 65 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_visual_smoke.py:271 | 0 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/backend/tests/test_write_roundtrips.py:133 | 15 | Broad match; not counted as direct VLD |
| gen-ai-roi-demo-v4-v50/scratch/temp/runner_debug_20260610_154609/backend/tests/test_soc_route_validation_runner.py:107 | 26 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_age_phase_c_batch1.py:65 | 8 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_audit.py:7 | 10 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_centroid_explorer.py:249 | 24 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_compounding_ledger.py:40 | 25 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_domain_isolation.py:250 | 12 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_evidence_graph_query.py:40 | 6 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:1 | 10 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_evolver_conservation.py:41 | 4 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_governance.py:147 | 25 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:159 | 16 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:83 | 1 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_multihop_evaluation.py:20 | 10 | Direct VLD/measurement |
| s2p-copilot/backend/tests/test_outcome_receipt.py:295 | 38 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_proposal.py:28 | 19 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_pydantic_responses.py:150 | 5 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_rule72_enforcement.py:37 | 1 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_active_age_phase_b.py:45 | 12 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_audit_export.py:124 | 9 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_autonomy.py:26 | 21 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_auto_approve.py:191 | 20 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_auto_approve_gate.py:541 | 33 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_config.py:30 | 7 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_context_builder.py:267 | 27 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_control_tower.py:29 | 17 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_data_helpers.py:55 | 8 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_demo_beats.py:26 | 18 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_enrichment.py:627 | 46 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_evidence.py:6 | 12 | Direct VLD/measurement |
| s2p-copilot/backend/tests/test_s2p_evidence_templates.py:4 | 14 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_evolution_promotion.py:17 | 3 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_evolution_router.py:76 | 10 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_evolution_rule_templates.py:7 | 8 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_evolver.py:69 | 18 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_graph_status_phase_a.py:287 | 23 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_insight.py:181 | 30 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_preset_and_invoice_link.py:97 | 6 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_product_like_phase_c2.py:71 | 7 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_score_endpoint.py:256 | 55 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_situation_pattern.py:117 | 24 | Broad match; not counted as direct VLD |
| s2p-copilot/backend/tests/test_s2p_worked_example.py:197 | 5 | Broad match; not counted as direct VLD |

</details>

## 18. Cross-copilot consistency matrix

All five shared mounts construct a KUtilityStore and SituationClassifier, but **all five inspected dedicated K tables contain zero rows and all classifiers use the heuristic**. Object wiring is not learning or model deployment. The K constructor accepts a connection-bearing store wrapper; a separate SQLite connection is sufficient structurally, but supplies no verified-decision feedback by itself. Exact main.py construction sites: SOC:245–259; Trading:561–571; Purchasing:841–851; DataOps:949–959; S2P:339–348 (full paths below).

| Copilot | Production investigation/scorer coupling | Evidence in current factory | K database, current data | Classifier / budget | Tau / sigma | Conservation |
| --- | --- | --- | --- | --- | --- | --- |
| SOC | Shared SDK route unwraps scorer; SOC UI calls separate mutable-scoring pattern/Stage1 route | SOCEvidenceProvider, registry plus optional graph; showcase1 dimension0, showcase2 dimensions0/3 | gen-ai-roi-demo-v4-v50/backend/data/k_utility.db; 0 rows | Heuristic; shared default2 becomes S1=0/S3=1/S6=4 unless explicit. SOC1/2 classify S6. | Shared .1 fallback / ones; no verified learned-sigma parity | No shared emit eligibility; SOC result says not_evaluated_read_only |
| Trading | Shared proxy→underlying GAE centroid copy; full production metric not preserved | TradingEvidenceProvider registry plus optional accessor; both flip fixtures dimensions1/2 | copilot-sdk/apps/trading/backend/data/k_utility.db; 0 rows | Heuristic; TRD1/2 S3 budget1, seed request budget2; S1 explicit0 | Shared .1 fallback / ones | No shared emit eligibility |
| Purchasing | Shared proxy→underlying GAE centroid copy; current checkpoint differentiated | PurchasingEvidenceProvider constructed from showcase order/supplier dictionaries; all7 dimensions can return fixture/default values | copilot-sdk/apps/purchasing/backend/data/k_utility.db; 0 rows | Heuristic; flip cases S3 budget1 versus seed2; S1 also S3, explicitly overridden0 | Shared .1 fallback / ones | No shared emit eligibility |
| DataOps | Shared unwrapping works; separate /api/dataops/investigate can fall back to bootstrap | DataOpsEvidenceProvider fixture helpers; DO1 six dimensions, DO2 1/2/3/4, S1 1/2 | copilot-sdk/apps/dataops/backend/data/k_utility.db; 0 rows | Heuristic; DO1 S3 budget1, DO2 S6 budget4, S1 budget0 | Shared .1 fallback / ones; domain loop separately implemented | No shared emit eligibility; domain loop has read-only status |
| S2P | Shared direct CompoundingScorer→GAE centroid copy; collector lacks complete startup state | S2PEvidenceProvider showcase dictionaries; case1 all except5, case2 all8, S1 all except5 | s2p-copilot/backend/app/data/k_utility.db default, CI_DATA_DIR override; 0 rows at inspected path | Heuristic; case1 S3 budget1, case2 S6 budget4, S1 budget0 | Shared .1 fallback / ones; no gated sources in mount | No shared emit eligibility |

Full construction paths: gen-ai-roi-demo-v4-v50/backend/app/main.py:245–259; copilot-sdk/apps/trading/backend/app/main.py:561–571; copilot-sdk/apps/purchasing/backend/app/main.py:841–851; copilot-sdk/apps/dataops/backend/app/main.py:949–973; s2p-copilot/backend/app/main.py:339–348. Shared metric extraction is copilot-sdk/copilot_sdk/backend/investigation_router.py:132–180; budget selection :65–72; K default is copilot-sdk/copilot_sdk/scoring/investigation.py:216–232; classifier mapping is copilot-sdk/copilot_sdk/scoring/situation_classifier.py:11–30, :92–129. Fixture dimension coverage is a property of these planted cases, not a measured percentage of ordinary decisions.

S1 rows in §1 were also replayed with forced budget2 to inspect safety. Those forced reads are not the intended S1 request contract. The endpoint consumes the supplied budget; it does not discover a fixture's metadata budget. Purchasing's explicit S1 override should therefore remain visible in any demo or acceptance claim.

## 19. v2.8 gap inventory

Status semantics: **BUILT** means the narrow requirement is present/satisfied in inspected code; **PARTIAL** means some components exist; **NOT BUILT** means no implementation was found in the searched scope; **BLOCKED** means a complete beat cannot meet its contract because of listed dependencies. A planned component is not treated as a regression. Each row is a requirement, not an additional unique finding. The inventory has **37 rows: 3 BUILT, 14 PARTIAL, 15 NOT BUILT and 5 BLOCKED**.

Evidence abbreviations in this section:

| Alias | Workspace-relative path |
| --- | --- |
| demo | copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_8.md |
| CORE | copilot-sdk/copilot_sdk/scoring/investigation.py |
| ROUTER | copilot-sdk/copilot_sdk/backend/investigation_router.py |
| SOC seed | gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py |
| SOC panel | gen-ai-roi-demo-v4-v50/frontend/src/components/InvestigationPanel.tsx |
| SOC models | gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py |
| SOC policy | gen-ai-roi-demo-v4-v50/backend/app/services/investigation_router.py |
| SOC loop | gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py |
| SOC campaigns | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py |
| SOC multihop | gen-ai-roi-demo-v4-v50/backend/app/services/multihop_scenarios.py |
| Trading seed | copilot-sdk/apps/trading/backend/app/vld_preseed.py |
| Purchasing seed | copilot-sdk/apps/purchasing/backend/app/vld_preseed.py |
| DataOps main | copilot-sdk/apps/dataops/backend/app/main.py |
| DataOps seed | copilot-sdk/apps/dataops/backend/app/vld_preseed.py |
| DataOps seed_graph | copilot-sdk/apps/dataops/backend/app/seed_graph.py |
| graph_contract | copilot-sdk/apps/dataops/backend/app/graph_contract.py |
| DataOps pattern | copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py |
| DataOps evidence | copilot-sdk/apps/dataops/backend/app/evidence_provider.py |
| DataOps policy | copilot-sdk/apps/dataops/backend/app/services/investigation_router.py |
| DO loop | copilot-sdk/apps/dataops/backend/app/services/investigation_loop.py |
| S2P seed | s2p-copilot/backend/app/vld_preseed.py |
| S2P evidence | s2p-copilot/backend/app/evidence_provider.py |
| S2P context builder | s2p-copilot/backend/app/services/s2p_context_builder.py |

“Frontend census” means the inspected SDK shared frontend, Trading/Purchasing/DataOps/S2P app frontends under copilot-sdk/apps, and SOC frontend. No negative search can have a nonexistent definition's line number; the adjoining positive component/source anchors identify the actual available implementation. The S2P frontend is under copilot-sdk/apps/s2p, not s2p-copilot/frontend.

| Requirement | Status | Blocking dependency / qualification | Paper severity | Demo severity | Evidence file:line |
| --- | --- | --- | --- | --- | --- |
| §4.17 VLD-SOC-1 | BLOCKED | F02/F11/F14/F27/F29 | P0 | P0 | demo:1023–1027; SOC seed:10–26 |
| §4.17 VLD-SOC-2 | BLOCKED | F02/F04/F27/F29 | P0 | P0 | demo:1033–1037; SOC seed:30–49 |
| §4.17 VLD-DO-1 | BLOCKED | F13/F19/F27/F30 | P0 | P0 | demo:1043–1047; DataOps main:963–973 |
| §4.17 VLD-DO-2 + sister case | BLOCKED | F13/F19/F29 | P0 | P0 | demo:1053–1057; DataOps seed:85–95 |
| §4.17 VLD-S2P-1 | BLOCKED | F10/F14/F29/F30 | P0 | P0 | demo:1063–1067; S2P seed:65–96 |
| §4.17 Shared InvestigationTracePanel | NOT BUILT | Versioned API + E-1 | N/A | P0 | demo:1014; SOC panel:100 is a separate component; frontend census |
| §4.17 SOC per-step trace surface | PARTIAL | Missing badges, proper provenance and persisted trace | P1 | P0 | SOC panel:217–253 |
| §4.17 SOC-2 red empty read / alternatives dimmed | NOT BUILT | Record empty/candidate attempts | P1 | P0 | CORE:140–141; SOC panel:217–255 |
| §4.17/§5 Contrast strip + stored comparator | PARTIAL | Faithful baseline and persistence | P0 | P0 | ROUTER:87–93; SOC panel:191–194 |
| §5 E-1 AGE trajectory store | NOT BUILT | Versioned record + append/read adapter | P0 | P0 | CORE:29–37; SOC models:33–53; graph search only finds IKS trajectory |
| §5 frozen_branch_policy/R3 over SA | PARTIAL | Unify factor selector and pattern controllers; remove oracle path | P0 | P0 | SOC policy:13, :89; DataOps policy:61; CORE:134–138 |
| §5 C4 residual + budget + flip-count | PARTIAL | Absent from SDK; empty/selector read handling | P0 | P0 | CORE:131–170; SOC loop:97–129; DO loop:101–133 |
| §5 Constant conservation emit gate | NOT BUILT | Frozen eligibility snapshot and final abstention | P0 | P0 | ROUTER:94–106; SOC models:46 |
| §5 Structured S0 per beat | PARTIAL | Vectors exist; graph/time/schema snapshot incomplete | P0 | P1 | SOC seed:13; Trading seed:13; Purchasing seed:77; S2P seed:72 |
| §5 Available branch sets + planted evidence | PARTIAL | Stage1 has branch sets; showcase seeds do not share that contract | P0 | P1 | SOC multihop:315–321; SOC seed:18; Trading seed:22 |
| §5 Adjudicated productive branch | PARTIAL | Stage1 oracle labels are planted, not held-out adjudication | P0 | P1 | SOC multihop:315–317, :385 |
| §5 Fixture version + PLANTED provenance package | NOT BUILT | Immutable episode/fixture identifiers | P0 | P1 | SOC seed:20; S2P seed:179 supplies origin only |
| §5 SOC shared-campaign DECIDED_ON→MEMBER_OF→CONTINUES | PARTIAL | Infrastructure exists; showcase pair does not instantiate required chain | P1 | P0 | SOC campaigns:1212; SOC seed:26, :49 |
| §5 DataOps Decision→Pipeline attachment | PARTIAL | Generic indirect seed attachment exists; verify exact billing_api VLD persistence/use | P1 | P0 | DataOps seed_graph:279–309; graph_contract:23–27; DataOps pattern:288–291 |
| §5 DataOps MATKL_V2 fixture | PARTIAL | Scalar/dictionary fixture exists; persisted causal chain unproved | P1 | P1 | DataOps seed:26–75; DataOps evidence:70–97 |
| §5 DO-2 resource_quota≈0.62 / sister≈0.93 | NOT BUILT | Implement or explicitly revise the original beat | P1 | P0 | demo:913, :1055; DataOps seed:85–95 |
| §5 Supplier Aster computed 3.1 ratio | NOT BUILT | Verified per-outcome counts and provenance | P0 | P0 | S2P seed:89; S2P evidence:107 |
| §5 Supplier matcher as-of cutoff | NOT BUILT | Timestamp-aware matching contract | P0 | P0 | S2P context builder:150–174 |
| §4.18 GUARD-1 ARCH→NEAR→LIVE eligibility | PARTIAL | No complete R3/E1/R4; panel says shadow rather than ARCH | P0 | P0 | demo:1094; SOC panel:137 |
| §4.18 GUARD-2 Allowed wording | BUILT | Current inspected VLD panel copy conforms; no automated guard | N/A | N/A | demo:1096; SOC panel:136–139, :172 |
| §4.18 GUARD-3 PLANTED + rho-unmeasured badges | NOT BUILT | Common provenance badges | P0 | P0 | demo:1098; SOC panel:131–139 |
| §4.18 GUARD-4 Content-keyed labels | NOT BUILT | Per-step acquisition classification | P0 | P0 | demo:1100; SOC panel:217–255 |
| §4.18 GUARD-5 No validated time-savings claim | BUILT | Current VLD UI has no time-savings number; R5 still unmeasured | N/A | N/A | demo:1102; SOC panel:130–265 |
| §4.18 GUARD-6 No next-time learning claim / frozen state | PARTIAL | Copy does not promise learning; snapshot/K learning contracts incomplete | P1 | P1 | demo:1104; CORE:53; F15/F18 |
| §4.18 GUARD-7 Exhaustive-budget honesty | PARTIAL | Allocated/used budget distinction and presenter caveat absent | P0 | P0 | demo:1106; ROUTER:97; SOC panel:199 |
| §4.18 GUARD-8 Computed provenance-badged numbers | PARTIAL | Margins computed; ratio literal and oracle output paths remain | P0 | P0 | demo:1108; S2P seed:89; SOC multihop:385–392 |
| §4.18 GUARD-9 Buyer-language display | NOT BUILT | Engineering view separation | N/A | P1 | demo:1110; SOC panel:92–95, :222, :252 |
| §4.18 GUARD-10 No competitor execution/claimed benchmark | BUILT | No such calls/numbers found in VLD handlers/panel; policy not automatically enforced | N/A | N/A | demo:1112; ROUTER:53–111; SOC panel:130–265 |
| §7.2 L-SOC insertion + ARCH/badges/warmup | NOT BUILT | F27/F28; exact route and fixture contracts | N/A | P0 | demo:1253–1258; frontend census |
| §7.2 L-DATAOPS insertion + ARCH/badges/warmup | NOT BUILT | F27/F28; exact route and fixture contracts | N/A | P0 | demo:1254–1258; frontend census |
| §7.2 L-S2P insertion + ARCH/badges/warmup | NOT BUILT | F27/F28; exact route and fixture contracts | N/A | P0 | demo:1255–1258; frontend census |
| §7.2 L-VLD insertion + ARCH/badges/warmup | NOT BUILT | F27/F28; exact route and fixture contracts | N/A | P0 | demo:1256–1258; frontend census |

The three BUILT guards concern current inspected copy: no prohibited wording, no validated time-savings claim, and no competitor execution/benchmark claim. They are observations of the current surfaces, not automatic policy enforcement. Missing buyer-language styling is a demo issue; missing adjudication, source provenance, scoring parity and trajectories affect the scientific claim itself. The five original beat rows remain ARCH, not LIVE. A numeric factor flip alone does not promote them.

## 20. Recommended fix queue

Effort ranges are engineering estimates for a focused implementation plus tests; they are not delivery commitments. Parallel work is possible after the snapshot and trace contracts are pinned. No item below was implemented by this audit.

### Paper-blocking work

| Order | Work / findings | Effort | Dependencies and acceptance evidence |
| --- | --- | --- | --- |
| P-1 | Remove oracle selection/output from the public SOC mode; retain a labeled positive control (F26) | 1–2 days | First establish one adversarial fixture where scorer and label disagree; public result must equal computed action and actual selected branch. |
| P-2 | Pin a versioned architecture, metric, episode and claim contract (F01/F07/F22) | 2–3 days | Choose which endpoints/algorithm the paper evaluates. Name shared factor acquisition versus SOC/DataOps pattern control explicitly; distinguish runtime dates and artifacts. |
| P-3 | Build immutable production-equivalent scorer snapshots and faithful single-pass contrast (F11/F12/F13/F18) | 4–7 days | P-2. Include category, masks, effective DK, sigma, tau, geometry/K versions and governance state; prove equivalence through the actual mounted routes. |
| P-4 | Persist every candidate/attempt/outcome with valid policy probability and halt semantics (F02/F04/F20) | 4–7 days | P-2/P-3. Replay successful, empty, failed, budget and oscillation episodes; deterministic propensity is1, not a score or fictitious uniform sample. |
| P-5 | Add frozen conservation eligibility and final emit/abstain contract (F14) | 2–4 days | P-3. RED/UNKNOWN may be diagnosed read-only but cannot produce an executable/approved action; verify at integration boundaries. |
| P-6 | Create independently adjudicated, time-valid episodes and fair best-alternative comparators (F10/F23/F30) | 1–3 weeks, data dependent | P-3/P-4. Separate planted demo success from held-out score-keyed routing; report sample denominators, category split, costs, uncertainty, matched-information baselines and as-of provenance. |
| P-7 | Make sweep and integration measure the full pinned contract (F31/F32) | 2–4 days | P-2/P-3. Inject actual K/state, compare startup paths independently, check ordered reads plus S1/default budgets, and compute readiness from every required predicate. |
| P-8 | If claiming learned K, add verified feedback/credit assignment and reachable weights (F15/F16) | 5–10 days | P-4/P-6. No magic fixture weights. Demonstrate persistence, boundedness and held-out effect. Basic fixed-K mechanism experiments need not wait if they explicitly disclaim learned-K results. |

### Demo-blocking work

| Order | Work / findings | Effort | Dependencies and acceptance evidence |
| --- | --- | --- | --- |
| D-1 | Reconcile the five original beats and current narratives; pin actual request budgets and ordered reads (F29/F30/F33) | 2–3 days plus missing data work | P-2. Resolve receipt-first versus contract-first S2P prose; restore or revise DO2 resource-quota sister case; align Purchasing stories without testing self-edited expectations. |
| D-2 | Implement shared trace presentation, provenance/accuracy badges, empty/taken/dimmed branches and faithful contrast (F27) | 4–7 days | P-3/P-4/D-1. Render PLANTED FIXTURE and unmeasured routing labels; separate engineering quantities from buyer view; distinguish all halt reasons and clear stale results. |
| D-3 | Materialize the exact campaign/pipeline/supplier fixture packages (F10/F30) | 3–6 days | D-1 and temporal/provenance schema. Verify linked records for exact showcase IDs, including computed supplier counts/ratio and as-of cutoff. Existing generic topology alone is insufficient. |
| D-4 | Wire four VLD Loom insertions and preflight/warmup gates (F28) | 1–2 days | D-1/D-2/D-3. Add L-SOC, L-DATAOPS, L-S2P and standalone L-VLD manifests; check ARCH/NEAR/LIVE wording and actual backend response. |
| D-5 | Run browser-to-mounted-route acceptance with normal defaults and explicit demo overrides (F26/F27/F32/F33) | 2–4 days | P-1/P-7 and D-1–D-4. No intercepted oracle response as the sole proof; reject readiness when badges, ordered reads, S1 budgets or wiring are missing. |

### Production hardening and technical debt

| Priority | Work / findings | Effort | Dependencies / scope |
| --- | --- | --- | --- |
| P1 | Finite numeric and semantic input validation, category rejection and resource ownership (F03/F12/F24) | 2–4 days | Pinned request/metric contract; test NaN/Inf, malformed geometry, unknown category, factor permutation and tenant isolation. |
| P1 | Bound wall-clock evidence work; structured errors and source-health behavior (F06/F25) | 2–4 days | Episode trace contract; per-read/total deadline, cancellation and redacted diagnostics. |
| P1 | Atomic/versioned tenant-scoped K lifecycle and trusted model manifests (F16/F17) | 2–4 days | Separate K learning claim work from persistence hardening. Validate feature names, prediction labels and artifact provenance. |
| P1 | Clarify classifier S1 ambiguity and test automatic budget behavior (F17/F33) | 1–3 days | Do not infer confidence from closeness alone; test identical centroids and exact .05/.5 boundaries. |
| P1 | Specify DataOps aggregation and heuristic attribution (F19) | 2–4 days | Counter-evidence may need downward updates; compare centroid-only and heuristic policies on independently labeled episodes. |
| P1 | Add independent regression contracts and stop treating synthetic tests as deployment proof (F21) | 2–4 days initially | Top ten contracts in §17; continue alongside corresponding fixes. |
| P2 | Refresh design/status documents and attach artifact hashes to every result (F22) | 1–2 days | After chosen contract and current-state checks; preserve historical reports as historical. |

### Audit artifact and source integrity

Before/after hashing covered **2,817 .py/.ts/.tsx source files** across the three repositories, excluding .git, node_modules, __pycache__, virtual environments and build directories. The sorted source-hash-map digest was identical:

```text
57b47eb83b571f6c3b96d04db823c9c9e82fd5a838ff3813d56098e4a016b884
```

The two core file hashes remained:

```text
copilot-sdk/copilot_sdk/scoring/investigation.py
  a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a
copilot-sdk/copilot_sdk/backend/investigation_router.py
  f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90
```

The existing real_centroids_v1.json was not overwritten. Its observed SHA-256 was `1d782457bfbf8349d7cedfa531a30b3007c1e9e08b378068a9e826d437215863`. Current local Trading/Purchasing checkpoint6 and the numerical replay in §1 supersede historical collapse claims; the export alone does not prove full app state parity.

Validation limits remain material: no live AGE verification, no fresh complete pytest baseline, no browser run against a live application, no measured production latency or rho, and no guarantee that package import startup side effects left every runtime database unchanged. No source file was changed, no git command was used, and this Markdown report is the only authored deliverable.

