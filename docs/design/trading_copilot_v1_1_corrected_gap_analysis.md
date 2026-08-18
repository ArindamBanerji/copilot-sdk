# Trading Copilot v1.1 (corrected) — Feature Gap Analysis

Date: 2026-08-17  
PD version: v1.1 corrected (`trading_copilot_product_definition_v1_1_corrected.md`)  
Prior analysis: `trading_copilot_v1_1_gap_analysis.md` (run against the wrong/SOC file and therefore useful mainly as a v1.0 baseline)

## Summary

The corrected PD was verified: its first line is `# Trading Copilot — Product Definition` and its header says `Version: 1.1 · Date: August 17, 2026`.

Feature-level result for F1–F16:

- **LIVE: 11** — F1–F8, F10, F12, and F15 have substantial backend, route/UI, and test evidence.
- **PARTIAL: 4** — F9, F11, F13, and F14 have implementation but do not meet the full v1.1 contract.
- **GAP: 1** — F16 Claim Gate.

The most important v1.1 findings are:

- F16 is **GAP**: no `EvidenceGate`, `ClaimGate`, `evidence_gate`, or `claim_gate` implementation was found, and `/api/trading/gate/{claim_type}` is not registered.
- SAFE-2 is **FAIL/GAP**: production pattern/regime paths emit forward-directed language, and the application still mounts a reachable broker-write endpoint at `/api/broker/orders`.
- SAFE-4 is **not verifiable**: counsel sign-off is necessarily external, and no code evidence can establish that the hard gate has passed.
- The v1.1 `StrategyStatus` rename is not implemented as a named model. The old `StrategyShift` class was also not found, but `RegimeRecommender` still emits `action`/`recommendations` and allocation-shift language.
- The shared SDK contains production `reward` and `reward_raw` fields and implementation symbols. This violates the requested compatibility scan even though the Trading app’s `risk_reward` factor is a different concept.

Repository test counts from source inspection: **1,226** backend `def test_` definitions under `apps/trading/backend/tests/`; **286** `it`/`test` call sites under `e2e/trading/`. These are counts, not a test run. Feature-area counts appear below.

## Feature Status Table

Status means: LIVE requires implementation, route, frontend surface, and tests; PARTIAL means material contract gaps remain; GAP means no matching implementation. “Prior delta” compares with the earlier report’s v1.0/foundation findings, not with a verified corrected v1.1 implementation.

| Feature | Status | Evidence | Backend test definitions / frontend evidence | Delta from prior |
|---|---|---|---|---|
| **F1 Trade Import** | LIVE | `app/routers/data_import.py` defines `/api/trading/import/csv`, `/api/trading/import/broker`, trade listing/detail, and market refresh routes. Broker adapters and CSV normalization are present. | Import/CSV/broker keyword slice: 109 definitions across 74 files. Import UI and data surfaces are present. | Revalidated; prior CSV/import CLOSED/PASS finding holds. |
| **F2 Signal Trust Dashboard** | LIVE | Trust analysis service/router plus `TrustRadarPanel.tsx`; MAP P53 records the dual-mode DK radar and TrustAnalyzer. | Trust/radar slice: 26 definitions across 5 files; frontend radar panel present. | Revalidated; prior P53 CLOSED/PASS finding holds. |
| **F3 Decision Quality Scorer** | LIVE | Shared scorer and Trading factor registry are wired through `main.py`; factor modules include signal alignment, regime, sizing, timing, risk/reward, emotional indicator, and confidence. | Score/factor slice: 199 definitions across 50 files; scoring and factor UI/types present. | Revalidated; prior factor/scorer evidence holds. F16 does not gate its claims yet. |
| **F4 Pattern Detector** | LIVE for v1.0 detector capability; PARTIAL for v1.1 safety | `app/services/pattern_detector.py` implements behavioral/statistical detectors and annualized cost payloads; `PatternDetectionPanel.tsx` exists. | Pattern slice: 62 definitions across 10 files. | Prior P55 CLOSED/PASS holds, but v1.1 observation-only conversion exposes violations in generated recommendation text. |
| **F5 Conservation Dashboard** | LIVE for conservation display; PARTIAL for complete promotion contract | Conservation routers/services, GREEN/AMBER/RED state, promotion panels, and strategy safety logic exist. | Conservation slice: 39 definitions across 16 files; `PromotionPanel`/`PromotionDashboard` present. | Prior P56 DROP_CONFIRMED finding holds for existing dashboard. MAP P83 promotion-engine work remains open. |
| **F6 IKS** | LIVE | IKS service, Trading registry wiring, `/api/trading/iks`, and frontend state/display are present. | IKS slice: 2 definitions across 3 files; route and registry evidence present. | Prior P58 DROP_CONFIRMED finding holds. |
| **F7 Trade Journal** | LIVE | `app/routers/journal.py`, `journal_query.py`, `JournalScreen.tsx`, filtering, aggregate stats, reflection/tag routes. | Journal slice: 64 definitions across 11 files; journal screen/query components present. | Prior P57 CLOSED/PASS finding holds. |
| **F8 CLI** | LIVE for shipped CLI surface | `cli_sdk.py` and `cli.py` provide import, score, trust, conservation, patterns, export, backup, restore, and related commands; package metadata exists. | CLI slice: 357 definitions across 51 files. | Prior P61/P62 findings hold: full CLI was confirmed shipped. |
| **F9 Real-Time Decision Support** | PARTIAL | `pre_score_router.py`, `prescore.py`, `pre_scorer.py`, `PreScorePanel.tsx`, and market-data services exist. However, response fields include action-like values (`skip`, `reduce`, `hold`) and the v1.1 observation-only gate is absent. | Pre-score slice: 62 definitions across 6 files; `PreScorePanel.tsx` present. | Prior P82 CLOSED/PASS proves read-only scoring, not v1.1 language compliance or F16 gating. |
| **F10 Regime Classifier** | LIVE for classifier; PARTIAL for v1.1 output contract | `regime_classifier.py`, `regime_router.py`, regime history/analytics/status routes, and regime panels are wired. | Regime slice: 172 definitions across 35 files; multiple regime panels. | Prior P81 CLOSED/PASS holds. Regime response paths still contain recommendation/action output. |
| **F11 Strategy Promotion Engine** | PARTIAL | `promotion_engine.py`, `promotion.py`, `promotion_router.py`, state machine, dashboard, and promotion tests exist. MAP P83 remains open for the full paper→small→full contract. | Promotion slice: 70 definitions across 6 files; promotion dashboards present. | Prior analysis recognized existing promotion infrastructure; current MAP still does not support a clean CLOSED claim. |
| **F12 AgentEvolver** | LIVE for evolution infrastructure; PARTIAL for v1.1 boundary | `trading_evolver.py`, evolution router, variant generator, shadow tests, promotion gates, and evolution UI are present. It tunes variants/thresholds, but observation-only and claim-gate constraints are not globally enforced. | Evolver/evolution slice: 41 definitions across 7 files; evolution panels/controls present. | Prior P84/P86 CLOSED/PASS holds for infrastructure, not the new safety contract. |
| **F13 Multi-Trader Dashboard** | PARTIAL | `social.py` exposes trader/profile/compare/edge routes and frontend social-related state exists, but no complete prop-desk dashboard with aggregate performance and edge transfer contract was verified. | Social/multi/cross slice: 38 definitions across 21 files; endpoint evidence exists, full dashboard acceptance not proven. | Prior analysis did not establish F13 as complete; current code supports partial social surfaces. |
| **F14 Cross-Trader Insights** | PARTIAL | Analytics has `/cross-insights` and social comparison routes. Opt-in anonymized network intelligence and proprietary-tier controls were not verified end-to-end. | Same social/multi/cross slice: 38 definitions across 21 files. | Prior analysis noted cross-insights-related routes but did not prove the PD contract; remains partial. |
| **F15 Broker Execution Analysis** | LIVE as analytics capability; PARTIAL for v1.1 safety boundary | `execution_analysis.py`, `execution_router.py`, `ExecutionQualityCard.tsx`, and broker comparison logic exist; MAP R4 CLOSED/PASS. The separate broker-write surface creates a SAFE-2 packaging conflict. | Execution slice: 27 definitions across 21 files; execution UI present. | Prior R4 CLOSED/PASS finding holds; new SAFE-2 requirement changes release classification. |
| **F16 Claim Gate** | GAP | No `EvidenceGate`, `ClaimGate`, `evidence_gate`, or `claim_gate` class/function found in Trading or SDK. No `/api/trading/gate/{claim_type}` route found. `ClaimRegistry` exists, but it prevents silent tier migration; it is not the PD’s N/p-value/conservation gate. | Claim/gate keyword slice: 11 definitions across 10 files, but these are ClaimRegistry, promotion, or unrelated gates; no F16 tests/UI. | Net-new v1.1 gap; prior report correctly predicted F16 was absent. |

## v1.1-Specific Findings

### F16 Claim Gate

The PD requires every claim-bearing endpoint to check claim-type-specific N thresholds, multiple-comparison-adjusted p-values, and non-RED conservation status, returning an abstention response when the gate is not met. The codebase has related infrastructure:

- `copilot_sdk/substantiation/registry.py` contains `ClaimRegistry`, claim tiers, and explicit no-silent-promotion behavior.
- Conservation status is available through shared graph/scoring services.
- Evidence and provenance routers are mounted in Trading.

However, those pieces are not the F16 service. No claim-type threshold table, p-value correction gate, abstention response, or `/api/trading/gate/{claim_type}` route was found. F16 is therefore **GAP/MAP-tracked only through PD T16b**, not implemented.

### SAFE-2 observation-only end-to-end tests

The required tests (`test_no_execution_endpoint`, `test_byod_is_observation_only`, and the MAP’s response/template grep) were not found. More importantly, the production code contains direct violations:

- `app/services/pattern_detector.py:537,640,747` emits “reduce size,” “skip,” and “Reduce size or require confirmation.”
- `app/services/regime_classifier.py:120` emits “Hold sizing … until conservation is green.”
- `app/services/regime_recommender.py` produces `action` values `avoid`, `reduce`, `hold`, and `increase`, and includes “allocation shift action.”
- `app/routers/regime.py` and `app/routers/regime_router.py` emit `recommendation` values and action values such as `increase`, `reduce`, and `hold`.
- `e2e/trading/execution.spec.ts:51` contains “Switch to ibkr to save about $1,200/year.”
- `app/evolution/evolver_config.py:44` contains “skip threshold.”

Some matches are non-directive implementation language or validation errors (`must be numeric`, `hold-period`, `cancel_futures`, field/type names). They do not remove the true violations above. SAFE-2 is **FAIL** until all claim-bearing response/template paths are converted to measured observations and the negative test suite exists.

### SAFE-4 counsel sign-off

SAFE-4 is an external hard gate: legal counsel must review the observation-only invariant, disclaimers, and data architecture before public launch. Code inspection cannot establish counsel approval. No repository artifact named for counsel sign-off or a release-blocking approval record was found. Status: **UNVERIFIABLE / release blocked pending external evidence**.

### StrategyStatus versus StrategyShift

Neither a `StrategyStatus` class nor a `StrategyShift` class was found in the Trading app or SDK. The code instead uses:

- `RegimeRecommender` with `recommendations`, `action`, and `sizing_recommendation` fields;
- `conservation_status` in multiple service/router payloads;
- regime router helper outputs containing `direction`/action values.

Therefore the renamed observation-only model is not present, and the old directive-shaped behavior remains in production. The absence of the old class does not count as completion of the rename.

### CorrelationMonitor B5/B6 spectral upgrade

The upgrade is present in the quant package, but the naming/documentation is mixed:

- `ci_trading/quant/correlation.py` implements `effective_correlation` (B5) and `tail_dependence` (B6), with the module docstring explicitly describing the upgrade over Pearson.
- Trading `app/services/correlation.py` imports and calls `ci_trading.quant.CorrelationMonitor`.
- The same service retains legacy Pearson matrix helpers and a comment identifying them as legacy.

Conclusion: **B5/B6 implementation exists and is wired, with legacy Pearson fallback/helpers retained**. It is not a pure “Pearson v1.0 only” implementation, but production behavior and tests should prove that the upgraded path is selected for all claim-bearing correlation output.

### C.3 rule 4 and I9/I10

The PD’s C.3 rule requires pattern alerts to be observations, not actions. The pattern detector currently violates that rule as shown above. I9/I10 are design scenarios for abstention and earned evidence; without F16 they are not executable as specified. I9 can be approximated by existing insufficient-data paths, but the claim-type N=50 gate and explicit claim abstention are missing.

### §13 Q5 four-pillar regulatory posture

The four pillars are represented in the PD: observation-only output, local-first data, self-governing engine limited to the observation layer, and counsel sign-off. Code partially supports local SQLite/import and conservation/evolver boundaries, but:

- observation-only output fails on concrete strings and action fields;
- `/api/broker/orders` remains reachable;
- no F16 gate limits claim display;
- counsel sign-off cannot be verified from code.

The four-pillar posture is therefore **design-complete but implementation-incomplete**.

## Observation-Only Compliance Scan

### Confirmed forward-directive violations

| Location | Finding |
|---|---|
| `apps/trading/backend/app/services/pattern_detector.py:537,640` | “reduce size or skip” output directed at the trader. |
| `apps/trading/backend/app/services/pattern_detector.py:747` | `recommendation` field: “Reduce size or require confirmation …”. |
| `apps/trading/backend/app/services/regime_classifier.py:120` | “Hold sizing …” directive. |
| `apps/trading/backend/app/services/regime_recommender.py:12,69–110,306+` | `avoid/reduce/hold/increase` action vocabulary and recommendation/sizing output. |
| `apps/trading/backend/app/routers/regime.py:103–109` | `hold`, `increase`, and `reduce` action values. |
| `apps/trading/backend/app/routers/regime_router.py:75,84,103–109` | Recommendation field and action values. |
| `apps/trading/e2e/execution.spec.ts:51` | “Switch to ibkr …” in an execution response fixture. |
| `apps/trading/frontend/src/types.ts:181,200,238,306,687` | Frontend contract types retain `action`/`recommendation` fields with directive values. |

### Non-directive or ambiguous matches

Matches such as `must be numeric`, `hold-period`, `cancel_futures(wait=False)`, `skip_recommended` as a domain action label, and `reduce` used as a JavaScript array operation are not by themselves user-directed advice. They still require allowlisting or structured filtering if SAFE-2 literally greps all response/template text.

### Compliance conclusion

SAFE-2 is not merely untested; it currently fails on production strings and response schemas. A simple grep-only test will also need semantic exclusions for validation messages, field names, and technical vocabulary, or it will produce false positives. The safer design is to remove directive-shaped fields from claim-bearing API responses and use an explicit observation schema.

## MAP Coverage

### Item-count discrepancy

The corrected PD says “27 MAP items,” but its Appendix A labels **T1–T29 plus T16b, SAFE-2, and SAFE-4**, which is 32 labels if counted literally. The same appendix says “25 original + SAFE-2 + T16b,” which explains 27 but excludes T26–T29 and does not consistently account for SAFE-4. This is a documentation inconsistency that should be fixed before using the count as a release gate.

### Cross-reference

| PD item(s) | MAP coverage | MAP state in `master_action_plan_v5.228 (1).md` | Current reconciliation |
|---|---|---|---|
| T1 / TRD-DOMAIN-CONFIG | Present as P48/#150 | DONE | Implemented; MAP closure and code agree. |
| T2 / TRD-ALPACA-CONNECTOR | Present as P49/#151 | DONE, merged with regime recommender | Implemented; scope is combined. |
| T3 / TRD-YFINANCE | Present as P50/#152 | CLOSED/PASS | Implemented. |
| T4 / TRD-SIGNAL-FACTORS | Present as P51/#153 | DROP_CONFIRMED after pre-check | Implemented by existing factor surface; “drop” means no new work. |
| T5 / TRD-CLI-CORE | Present as P52/#154 | CLOSED/PASS | Implemented. |
| T6 / TRD-TRUST-RADAR | Present as P53/#155 | CLOSED/PASS | Implemented. |
| T7 / TRD-REMAINING-FACTORS | Present as P54/#156 | CLOSED/PASS | Implemented. |
| T8 / TRD-PATTERN-DETECTOR | Present as P55/#157 | CLOSED/PASS | v1.0 detector implemented; v1.1 SAFE-2 delta remains open. |
| T9 / TRD-CONSERVATION | Present as P56/#158 | DROP_CONFIRMED | Existing conservation dashboard found. |
| T10 / TRD-JOURNAL | Present as P57/#159 | CLOSED/PASS | Implemented. |
| T11 / TRD-IKS | Present as P58/#160 | DROP_CONFIRMED | Existing IKS stack found. |
| T12 / TRD-IBKR | Present as P59/#161 | CLOSED/PASS | Implemented. |
| T13 / TRD-CSV-IMPORT | Present as P60/#162 | CLOSED/PASS | Implemented. |
| T14 / TRD-CLI-FULL | Present as P61/#163 | DROP_CONFIRMED | Existing full CLI; P62 carried package consolidation. |
| T15 / TRD-PYPI | Present as P62/#164 | CLOSED/PASS | Implemented. |
| T16 / TRD-EVIDENCE-NL | Present as P63/#165 | CLOSED/PASS | Templates exist, but v1.1 observation-only scan finds violations. |
| T16b / TRD-CLAIM-GATE | Present in PD Appendix A | **Not found as a corresponding MAP row** | MAP-MISSING as a distinct F16 implementation item; C-OSS-1Q ClaimRegistry is related but not equivalent. |
| SAFE-2 / TRD-OBS-ONLY-TESTS | Present in PD Appendix A | **Not found as a corresponding MAP row** | MAP-MISSING; P0 release blocker. |
| SAFE-4 / TRD-COUNSEL-GATE | Present in PD Appendix A | **Not found as a corresponding MAP row** | MAP-MISSING in the supplied MAP; external hard gate. |
| T17 / TRD-REGIME-CLASSIFIER | Present as P81/#166 | CLOSED/PASS | Implemented; v1.1 output contract remains partial. |
| T18 / TRD-REALTIME-SCORE | Present as P82/#167 | CLOSED/PASS | Read-only pre-score implemented; directive-shaped fields remain. |
| T19 / TRD-PROMOTION-ENGINE | Present as P83/#168 | OPEN | Partial implementation; not safe to call fully closed. |
| T20 / TRD-AGENT-EVOLVER | Present as P84/#169 | CLOSED/PASS | Evolution infrastructure implemented. |
| T21 / TRD-MULTI-TRADER | Present in PD Appendix A | **No matching closed MAP row found** | MAP-MISSING or only future-scope text; social partial code exists. |
| T22 / TRD-CROSS-INSIGHTS | Present as #174 | Open/future | MAP-tracked; implementation partial. |
| T23 / TRD-EXECUTION-ANALYSIS | Present as R4 and #175 | R4 CLOSED/PASS; queue still lists #175 | Status inconsistency; analytics exists, v1.1 safety boundary unresolved. |
| T24 / TRD-OPTIONS-FACTORS | Present as R5 and #176 | R5 DROP_CONFIRMED; queue still lists #176 | Status inconsistency; code exists. |
| T25 / TRD-TRADINGVIEW-HOOK | Present as R6 and #177 | R6 CLOSED/PASS; queue still lists #177 | Status inconsistency; code exists. |
| T26 / TRD-REGIME-RECOMMEND | Present as P85/#170 | Pre-check required / possibly superseded by P49 | Code exists, but rename/observation-only contract is not complete. |
| T27 / TRD-CORRELATION-MONITOR | Present as R3 and #171 | R3 DROP_CONFIRMED; queue still lists #171 | B5/B6 code is present; MAP status inconsistent. |
| T28 / TRD-EARNINGS-SUBCAT | Present as R1 and #172 | CLOSED/PASS; queue still lists #172 | Code/tests exist; status duplication. |
| T29 / TRD-VIX-TIMING | Present as R2 and #173 | DROP_CONFIRMED; queue still lists #173 | Code/tests exist; status duplication. |

### Recommended new MAP entries

The existing MAP has related infrastructure but should add explicit, separately gated items for:

1. **TRD-F16-EVIDENCE-GATE** — claim-type thresholds, multiple-comparison correction, conservation check, abstention payload, `/api/trading/gate/{claim_type}`, and tests.
2. **TRD-SAFE-2-OBS-ONLY** — response/template scan plus removal of directive-shaped production outputs and broker-write routes from the OSS profile.
3. **TRD-SAFE-4-COUNSEL-RELEASE-GATE** — external approval artifact and release automation that refuses public packaging without it.
4. **TRD-STRATEGY-STATUS** — replace recommendation/action/allocation-shift payloads with the observation-only `StrategyStatus` schema.
5. **TRD-COMPOUNDING-CLAIM-GATE** — ensure later claims use verified outcome state only after F16 eligibility.
6. **TRD-MAP-COUNT-CLEANUP** — reconcile the 27-versus-32 item count and duplicate R/queue statuses.

## Recommendations

### P0 — before public release or v1.1 demo claims

1. Implement T16b/F16 as a real service and mount `/api/trading/gate/{claim_type}`. Route accuracy, edge, regime, scaling, and promotion claims through it.
2. Remove or isolate `/api/broker/orders` and the order CLI from the observation-only/OSS profile. Add the negative endpoint test required by SAFE-2.
3. Replace `recommendation`, `action`, `sizing_recommendation`, “reduce,” “increase,” “hold sizing,” “skip,” and “switch broker” user-facing outputs with measured observation schemas.
4. Add SAFE-2 tests that scan API response bodies and NL templates, with an explicit allowlist for technical validation messages and data labels.
5. Obtain and record SAFE-4 counsel sign-off; do not treat code completion as legal approval.

### P1 — pilot readiness

6. Implement `StrategyStatus` with `conservation_status` and observation-only fields; remove the old directive-shaped regime recommender contract even though the literal `StrategyShift` class is already absent.
7. Complete F11 promotion semantics and make promotion checks consume F16 eligibility as well as conservation.
8. Verify the B5/B6 upgraded correlation path is always selected for production claim output and add a test preventing accidental fallback to legacy Pearson-only output.
9. Complete F13/F14 acceptance criteria for aggregate desk and anonymized opt-in cross-trader insights.

### P2 — compatibility and roadmap

10. Rename or isolate shared SDK `reward`/`reward_raw` production fields and RL reward modules if the compatibility policy bans those names. The current scan found 6 Trading-app hits and 57 SDK hits; examples include `copilot_sdk/scoring/scorer.py:111,1115–1156,2207–2216`, `backend/models.py:76`, and `backend/scoring_router.py:483–485,838`.
11. Resolve duplicate MAP statuses for R1–R6 and the #171–#177 queue.
12. Clarify the PD’s MAP count and whether T26–T29 and SAFE-4 are included in the advertised 27.

## Bottom line

The corrected v1.1 PD changes the release conclusion materially. The v1.0 foundation is broadly implemented and well tested, but v1.1 is not release-complete: F16 is absent, SAFE-2 currently fails on real output strings and a reachable broker-write endpoint, SAFE-4 is unverified, and the StrategyStatus rename has not been carried into code. The quant B5/B6 upgrade and most older Trading features are present, but those facts do not satisfy the new evidence-gating and regulatory contract.
