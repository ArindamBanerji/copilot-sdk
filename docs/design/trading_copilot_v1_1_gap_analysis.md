# Trading Copilot v1.1 — Feature Gap Analysis

Date: 2026-08-17  
Scope: exact repository paths supplied in the review request; no product code changed.

## Source-integrity finding

The requested file `product/trading_copilot_product_definition_v1_1.md` is present, but its contents begin `SOC Copilot — Design Document v5.8` and contain 6,492 lines. It is not a standalone Trading v1.1 product definition. Its Trading-specific material is an enhancement layer in §15 (lines 6445–6492), sourced from `trading_copilot_addendum_FINAL_v1.md`. The addendum itself names a different base file, `trading_copilot_product_definition_v1.md`, which is not one of the authoritative paths supplied here.

Accordingly, this report does not invent a missing Trading base manifest. The manifest below is split into: (a) requirements actually extractable from §15 and the final addendum, and (b) Trading demo requirements from `demo_scenarios_and_usecases_v2_7.md`, explicitly marked as supplementary rather than silently treated as PD text.

Evidence labels in this document mean:

- **LIVE**: backend implementation, endpoint, frontend surface, and tests were found, and the reviewed contract is supported.
- **PARTIAL**: implementation exists, but a material part of the stated contract or maturity claim is absent/unverified.
- **GAP**: no matching implementation was found.
- **MAP-TRACKED**: not complete and covered by an open or forward MAP item.
- **MAP-MISSING**: not complete and no matching MAP item was found.

The checkout contains 1,226 backend test definitions under `apps/trading/backend/tests/` and 286 `it`/`test` call sites under `e2e/trading/` (the latter is a source-count sanity measure, not a claim that every call is a unique test definition). The MAP’s older snapshot reports 1,138 Trading backend tests.

## 1. Feature/Capability Manifest

### 1.1 Trading requirements actually present in the supplied PD file and final addendum

| ID / vocabulary | Capability extracted from source | Priority / maturity | Source reference | Dependencies |
|---|---|---|---|---|
| OBS-1 | Observation-only presentation: every displayed line is a past-tense observation about the trader’s own verified decisions, carrying sample size N; no forward directive or market claim. | Hard product/regulatory invariant | Supplied PD §15, lines 6449–6453; addendum lines 8–16 | Verified outcomes, evidence counts, UI copy controls |
| REG-1 | No personalized compensation, discretion, execution, broker/account access, or trading instruction; counsel signoff is a hard gate. | Hard gate | Supplied PD §15, lines 6455–6457; addendum lines 18–23 | Legal review, endpoint surface audit |
| F16 | Selection-adjusted evidence gate: BH-FDR, deflated Sharpe, discover-70/confirm-30 split, and a “23 hypotheses tested” badge. | Addendum capability; NEAR in demo vocabulary | Supplied PD §15, lines 6459–6465; addendum lines 25–32 | Shared evidence-gate SDK; real fixtures; claim registry |
| EVID-1 | Shared evidence-gate SDK as a first-class build item. | Build requirement | Same references as F16 | F16 implementation and all Trading evidence surfaces |
| AUTO-1 | Abstention/autonomy throttle, including “won’t” positioning rather than a capability limitation claim. | Addendum capability; NEAR for regime-break beat | Supplied PD §15, lines 6459–6465; addendum lines 25–32 | Regime classifier, Hurst/tail/volatility signals, conservative UI |
| B1–B8 | Upgrade volatility mathematics to the B1–B8 quantitative substrate. The supplied sources explicitly identify realized-volatility, Hurst/regime, block-bootstrap, tail-dependence, model-free IV/VRP, and implied-correlation/dispersion constructs; B3 is not defined in the supplied Trading source. | Quant enhancement; mostly NEAR in demo material | Supplied PD §15, lines 6459–6465; addendum lines 25–32; MAP C-OSS-1Q and C-TRD-VOL | Quant package, provenance, real fixtures, claim/evidence gate |
| T1/T3/T20 | Preserve the T1 mirror, T3 Friday, and T20 VIX paths, routed through the claim gate; the earlier “kill T3/T20” decision is superseded. | Preserved; not a kill decision | Supplied PD §15, lines 6467–6469; addendum lines 33–35 | F16 gate, existing scenario routes |
| BELIEF-1 | Pre-trade belief capture. | ARCH / pending build specification | Supplied PD §15, lines 6471–6473; addendum lines 37–38 | Belief schema, signed persistence, observation-only treatment |
| CF-1 | Counterfactual replay with signed `.jmt` artifact. | ARCH / extension | Supplied PD §15, lines 6471–6473; addendum lines 39–40 | Counterfactual engine, signing/key lifecycle, Judgment Memory |
| DIST-1 | Parasitic distribution connector specification. | ARCH / extension | Supplied PD §15, lines 6471–6473; addendum lines 41 | Connector contract, local-first data handling |
| JM-1 | Judgment Memory with the properties stated by the addendum. | ARCH / extension | Supplied PD §15, lines 6471–6473; addendum lines 41 | Persistent decision history, provenance, signed replay |
| SAFE-2 | OSS build must have no reachable order/execution/broker-write endpoint; required tests include `test_no_execution_endpoint` and `test_byod_is_observation_only`. | Hard OSS safety gate | Supplied PD §15, lines 6475–6479; addendum lines 43–45 | Packaging boundary, route audit, negative tests |
| SAFE-4 | Local raw trade rows must not leave the machine; required test is `test_no_trade_data_egress`. | Hard local-first safety gate | Supplied PD §15, lines 6475–6479; addendum lines 46–47 | Import/storage boundary, network-egress audit |
| COMP-1 | Compounding is product-defined but not to be claimed LIVE until the RL-loop-equivalent path is end-to-end. The addendum gives weights: outcome 0.3, R-multiple 0.3, execution quality 0.4, with prototype tensor `(5,3,6)`. | Designed, explicitly not LIVE | Supplied PD §15, lines 6481–6483; addendum lines 49–50 | Verified outcomes, scorer state, later score, measured improvement |
| TRD-S3/S7 | Autonomy throttle is NEAR; re-convergence is ARCH and only becomes LIVE after regime-indexed experiment. | NEAR / ARCH | Supplied PD §15, lines 6481–6483; demo §Trading additions, lines 470–505 | C-TRD-SIT, C-REGIME, EXP-REGIME |

### 1.2 Supplementary Trading manifest extracted from the demo scenarios document

The demo document is not the missing base PD, but it is the repository’s explicit scenario manifest. It names T1–T20 and the following v2.7 Trading beats. These are included because the request specifically requires demo coverage.

| ID | Demo capability / scenario | Stated tier | Demo source | Dependencies |
|---|---|---|---|---|
| T1–T20 | Trading scenario catalog: mirror; Friday; regime; scale; execution; revenge; per-trader edge; stopped working; prove-before-real-money; unified history; transferred playbook; tariff shock; regime shift; revenge at VIX 32; edge rotation; premium IV/RV; correlation breakdown; earnings split; VIX mean reversion. | 19 ready; T17 deferred v1.1 in catalog | Demo lines 312–319 | Existing Trading surfaces plus the relevant quant/evidence paths |
| TR1 | BYOD CSV import, observation path, not a decision path. | LIVE | Demo lines 196–202 | `/api/trading/import/csv` |
| TR2 | Mirror: trust analysis and fingerprint with a 60-second refresh. | LIVE | Demo lines 196–202 | `/api/context/trust-analysis`, `/api/fingerprint` |
| TR3 | Edge drift and Rejection Moment at `/traders/{id}/edge`. | LIVE/near-live demo claim | Demo lines 196–202 | Edge analytics, rejection evidence |
| TRD-S1 | Regime-conditioned mirror. | NEAR | Demo lines 470–489 | C-TRD-SIT, regime-tagged history |
| TRD-S2 | Situational abstention. | NEAR | Demo lines 470–489 | C-TRD-SIT, abstention state |
| TRD-S3 | Autonomy throttle on regime break. | NEAR | Demo lines 470–489 | C-TRD-SIT, B2/B4/B6 signals |
| TRD-S4 | Regime-scoped rejection. | NEAR | Demo lines 470–489 | C-TRD-SIT, rejection evidence |
| TRD-S7 | Regime-indexed re-convergence. | ARCH | Demo lines 494–505 | C-REGIME and EXP-REGIME |
| TRD-V1 | Short-volatility illusion / clustering-adjusted Sharpe. | NEAR | Demo lines 470–489 | C-TRD-VOL, B4, evidence gate |
| TRD-V2 | VRP edge / insurance. | NEAR | Demo lines 470–489 | C-TRD-VOL, B1/B7 |
| TRD-V5 | Regime-conditioned rich/cheap. | NEAR | Demo lines 470–489 | C-TRD-VOL, regime labels |
| TRD-V6 | Dispersion follow-rate. | NEAR | Demo lines 470–489 | C-TRD-VOL, B8 |
| TRD-V7 | Effective-bets tail. | NEAR | Demo lines 470–489 | C-TRD-VOL, B6 |
| TRD-CLAIM-GATE | BH-FDR, deflated Sharpe, 70/30 split, 23-pattern badge. | NEAR | Demo lines 794–808 | F16 / shared evidence gate |
| TRD-CERTIFICATE | Clean-trader certificate: 23 detectors tested and none survive. | NEAR | Demo lines 794–808 | Claim gate, detector registry |
| TRD-GATE-DIVIDEND | Illustrative dollar/value dividend from evidence gating. | NEAR | Demo lines 794–808 | Claim gate, observation-only wording |
| TRD-D6 | Observation-only guard. | Required design rule | Demo lines 794–808 | SAFE-2, SAFE-4 |
| TRD-D7 | B1–B8 quantitative substrate and multi-primitive regime-break trigger. | Required design/build item | Demo lines 794–808 | B2 Hurst, B4 block bootstrap, B6 tail dependence |
| TRD-D3 | TradeZella positioning/integration direction. | Addendum positioning | Demo lines 794–808 | Distribution connector, local-first boundary |
| TRD-D8 | Fold T4/T14 into the updated positioning. | Scenario correction | Demo lines 794–808 | Observation-only copy and scenario evidence |

## 2. Feature Status Table

The table below uses the extracted manifest rather than assuming that every existing Trading panel satisfies the newer addendum contract. Test counts are repository search counts where a feature-specific count was not isolated; they should not be read as proof of semantic coverage.

| Item | Status | Implementation evidence | Tests / MAP coverage |
|---|---|---|---|
| OBS-1 / TRD-D6 | PARTIAL | Many observation, evidence, journal, and analytics surfaces exist, but the required global past-tense/N/verified-decision invariant was not proven by a code-wide guard. | 1,226 BE / 286 E2E overall; no `test_byod_is_observation_only` found. MAP-MISSING as a complete guard item. |
| REG-1 | PARTIAL | Trading mounts domain routers and has no observed personalized execution requirement in the evidence path, but broker/account and order routes remain reachable. | SAFE-2 negative tests absent. MAP-MISSING as an explicit release gate. |
| F16 / TRD-CLAIM-GATE | GAP, MAP-MISSING | No `ClaimGate`, BH-FDR, deflated-Sharpe, discover/confirm split, or 23-hypothesis badge implementation found in Trading, SDK, or `ci_trading`. | No feature-specific tests found. MAP has related C-OSS-1Q ClaimRegistry work open, but no completed F16 item. |
| EVID-1 | GAP, MAP-MISSING | Evidence and provenance routers exist, but the shared selection-adjusted evidence-gate SDK was not found. | C-OSS-1Q steps 3d/3e remain open; no dedicated MAP item for the complete shared gate. |
| AUTO-1 / TRD-S2/S3/S4 | PARTIAL, MAP-TRACKED | Regime classifier, regime scoring/monitoring, situation routes, and promotion controls exist. Full abstention contract and multi-primitive regime-break behavior are not established. | MAP C-TRD-SIT is open/forward; demo tier NEAR. |
| B1–B8 substrate | PARTIAL, MAP-TRACKED | `ci_trading/quant` implements realized volatility, Hurst/regime, rolling statistics, effective correlation/tail dependence, block bootstrap/dispersion diagnostics, model-free IV/VRP, implied correlation/dispersion. B3 is not defined in the supplied source. | C-OSS-1Q real-fixture and ClaimRegistry steps open; C-TRD-VOL is open. |
| T1 / TR1 | LIVE | CSV import router is mounted; trust/evidence/journal and mirror-oriented panels are present. | P60 CSV import CLOSED/PASS; P53 Trust Radar CLOSED/PASS; demo calls TR1 LIVE. |
| T2 / TR2 | LIVE | `/api/context/trust-analysis` and fingerprint-related routes/surfaces are present; Trust Radar and evidence UI exist. | P53 CLOSED/PASS; broad suite count above. |
| T3 Friday | PARTIAL | Existing Trading analytics and Friday-related scenario support exist, but current claim-gate routing and observation-only proof are absent. | P51/P54/P63 are CLOSED/PASS; F16 is MAP-MISSING. |
| T4/T14 | PARTIAL | Regime classifier, analytics, status, and recommender routes exist; addendum’s revised observation-only positioning is not proven end-to-end. | P81/P84 CLOSED/PASS; C-TRD-SIT and C-REGIME remain forward. |
| T5/T7/T9/T13/T15/T16 | PARTIAL | Pattern, regime, journal, evidence, and factor panels provide related surfaces; complete scenario-specific contracts and newer wording guards were not isolated. | P55/P57/P63 CLOSED/PASS; no addendum-level evidence gate. |
| T6 / TR3 | PARTIAL | Execution analysis router, execution-quality UI, edge/rejection-related services, and tests exist. The exact demo receipt/observation contract was not proven. | P44 execution analysis CLOSED/PASS; P? no separate MAP item for full TR3 contract. |
| T8/T10/T11/T12 | PARTIAL | Trader history, journal, evidence, transfer/archetype, and counterfactual surfaces exist. Full product scenario acceptance is not documented in the exact PD source. | P57/P63/P87/P88 CLOSED/PASS; missing base-PD acceptance criteria. |
| T17 / TRD-V2 | PARTIAL, MAP-TRACKED | Model-free IV/VRP and VRP attribution code/cards exist, but demo says premium IV/RV is deferred and current VIX proxy/live evidence status is not equivalent to the full claim. | R2 VIX timing CLOSED/DROP_CONFIRMED in MAP, while C-TRD-VOL remains open; this is a MAP/demo status conflict. |
| T18 / TRD-V6 | PARTIAL, MAP-TRACKED | Correlation monitor, correlation panel, dispersion code, and quant integrations exist. Regime/evidence-gated follow-rate contract remains NEAR. | R3 marked DROP_CONFIRMED though MAP queue #171 still lists correlation; C-TRD-VOL open. |
| T19 | PARTIAL | Earnings subcategory and split-related surfaces/tests exist. New claim-gate routing and exact observation copy remain unverified. | R1 CLOSED/PASS; F16 MAP-MISSING. |
| T20 | PARTIAL | VIX timing service/router/panel exist and the MAP records R2 as DROP_CONFIRMED; addendum requires preservation through the claim gate, which is absent. | R2 CLOSED/PASS/DROP_CONFIRMED; F16 MAP-MISSING. |
| TRD-S1 | PARTIAL, MAP-TRACKED | Regime classifier and mirror/analytics surfaces exist, but regime-scoped historical evidence and situational tagging are not complete. | C-TRD-SIT open; demo NEAR. |
| TRD-S7 | GAP for full contract, MAP-TRACKED | `ReConvergencePanel` exists, but regime-indexed centroids/accessor, experiment, and cold-start comparison are not complete. | C-REGIME and EXP-REGIME open; demo ARCH. |
| TRD-V1 | PARTIAL, MAP-TRACKED | Volatility analytics and `VolSharpeCard` exist; clustering-adjusted Sharpe plus selection-adjusted proof is not established. | C-TRD-VOL open; demo NEAR. |
| TRD-V5 | PARTIAL, MAP-TRACKED | Regime/VRP analytics and cards exist; regime-conditioned rich/cheap claim gate is absent. | C-TRD-VOL open; demo NEAR. |
| TRD-V7 | PARTIAL, MAP-TRACKED | Tail-bets UI and tail-dependence quant functions exist; full effective-bets tail evidence contract is not proven. | C-TRD-VOL open; demo NEAR. |
| BELIEF-1 | GAP, MAP-MISSING | No pre-trade belief-capture model, route, UI, or signed artifact implementation found. | No matching MAP item found. |
| CF-1 | PARTIAL, MAP-MISSING | Generic counterfactual router/panel exists, but signed `.jmt` output and the addendum’s replay/security contract were not found. | No specific signed-JMT MAP item found. |
| DIST-1 | PARTIAL, MAP-MISSING | CSV import is present; no concrete TradeZella/Tradervue-style parasitic distribution connector was found. | No matching connector MAP item found. |
| JM-1 | PARTIAL, MAP-MISSING | Journal, graph, provenance, and evolution persistence provide pieces of Judgment Memory; the named property set and signed replay proof are absent. | No matching complete Judgment Memory item found. |
| SAFE-2 | GAP, MAP-MISSING | `broker_router.py` is mounted at `/api/broker` and exposes POST `/orders`; Alpaca/IBKR adapters and a CLI `order` command can place orders. | Required negative tests not found. This is a P0 OSS blocker. |
| SAFE-4 | PARTIAL, MAP-MISSING | CSV/import and local SQLite-oriented paths exist, but no explicit no-egress proof was found; `ci_platform` is an external package dependency. | `test_no_trade_data_egress` not found. |
| COMP-1 | PARTIAL, MAP-TRACKED | `main.py` wires outcome recording through `TradingAgentEvolver`; `record_verified_outcome` updates variant stats, and generic scorer learning updates scorer state. The addendum’s weighted three-signal measured compounding loop is not present. | P84/P86 CLOSED/PASS for evolution infrastructure; MAP C-GOV and C-TRD-SIT/C-TRD-VOL still forward for stronger gating. |

## 3. Addendum Delta

### Net-new or materially strengthened requirements

| Addendum item | Result | Finding |
|---|---|---|
| F16 selection-adjusted evidence gate | Gap | No BH-FDR/deflated-Sharpe/70-30/23-badge implementation found. |
| Shared evidence-gate SDK | Gap | Existing evidence/provenance services are not the specified shared gate. |
| Abstention/autonomy throttle | Partial | Regime/situation/throttle-related code exists, but the full addendum contract and multi-primitive trigger are not verified. |
| B1–B8 upgrade | Partial | Quant substrate is substantially present in `ci_trading/quant`; B3 is unresolved and integration/evidence gates remain open. |
| Clean-trader / D-null certificate | Gap | No clean-trader, D-null, or 23-detector certificate implementation found. |
| Pre-trade belief capture | Gap | No matching model, endpoint, or UI found. |
| Signed `.jmt` counterfactual | Partial | Generic counterfactual capability exists; signed artifact contract does not. |
| Parasitic distribution connector | Partial | CSV BYOD exists; named connector/spec implementation does not. |
| Judgment Memory properties | Partial | Journal/graph/provenance pieces exist; complete property proof is absent. |
| SAFE-2 no-execution OSS gate | Gap | Reachable broker-write routes and CLI order command directly conflict with the requirement. |
| SAFE-4 no-egress gate | Partial | No-egress test/proof not found. |
| Compounding honesty rule | Partial | Outcome and scorer paths exist, but source explicitly says not to claim LIVE; the weighted end-to-end metric is not wired. |

### Corrections or supersessions

- The observation-only wording is a positioning and safety correction applied across the product, not merely a new panel.
- “Can’t” is to be reframed as “won’t.” This is a copy/product-contract requirement; a code-wide compliance proof was not found.
- T1, T3, and T20 are explicitly preserved and routed through the claim gate. The earlier proposal to kill T3/T20 is superseded.
- T17’s premium IV/RV status remains deferred in the demo catalog even though lower-level IV/VRP code exists.
- The addendum explicitly says the compounding loop is designed, not built, and forbids a LIVE claim until end-to-end verification.

## 4. Verify-in-Code Results

### 4.1 Compounding loop

There is a real partial learning path:

1. `apps/trading/backend/app/main.py:400–405` defines `record_trading_outcome` and calls `trading_evolver.record_verified_outcome`.
2. `apps/trading/backend/app/services/trading_evolver.py:246–278` validates the variant, updates outcome counts, and delegates to the variant store.
3. The generic scoring router’s `/learn` path calls `scorer.learn()` before outcome recording, so the scorer’s centroids/state can change after learning.
4. Later scoring uses the scorer proxy/state wired in `main.py:329–364`.

This establishes outcome-to-state wiring, not the full addendum compounding claim. No verified three-signal reward-equivalent metric (0.3 outcome + 0.3 R-multiple + 0.4 execution quality), no `(5,3,6)` production tensor path, and no measurable later-quality improvement test was found. The correct maturity conclusion is **PARTIAL / designed-not-built**, consistent with the supplied §15 statement.

### 4.2 Banned vocabulary and reward field

The production scan of `apps/trading/backend/app/**/*.py`, excluding tests and comments, found no standalone `rl_`, `reward`, `policy`, or `reinforcement` hit. The matches containing `risk_reward_actual` and `risk_reward.py` are risk/reward analytics names, not RL vocabulary. The demo/design documents do use RL/reward terminology, including the compounding discussion; that is outside the requested production-app scan and should still be corrected or carefully bounded in user-facing documentation.

### 4.3 Honesty and maturity tiers

| Tier / claim | Code support |
|---|---|
| LIVE: T1 mirror / BYOD observation path | Substantially supported: CSV import, trust/evidence routes, panels, and MAP P53/P60 closure. SAFE-2/SAFE-4 still need boundary tests. |
| LIVE: 19 ready Trading scenarios | Not independently proven as a v1.1 claim because the supplied PD file is not the Trading base PD and scenario-level acceptance tests were not mapped one-to-one. |
| NEAR: TRD-S1–S4 and TRD-V1/V2/V5/V6/V7 | Quant and regime building blocks exist, but C-TRD-SIT/C-TRD-VOL and evidence-gate work remain open. NEAR is credible; LIVE is not. |
| NEAR: F16 / certificate / gate dividend | Not supported by current code; these are GAP despite the demo’s NEAR label. |
| ARCH: TRD-S7 re-convergence | Honest. Required regime-indexed accessor and experiment are open. |
| ARCH: belief capture, signed JMT, distribution connector, Judgment Memory extension | Honest; no implementation evidence found. |
| Compounding | Honest only when labeled designed/not-built or partial. Do not label LIVE. |

### 4.4 Cross-copilot and platform dependencies

- Trading imports and wires `ci_platform.copilot_core.EntityCache` and `EntityContextCacheAdapter` in `main.py:87`; the dependency is real and must be included or removed for standalone packaging.
- The domain quant package is in `copilot-sdk/ci_trading/quant/`, and Trading imports its realized-vol, regime, correlation, IV/VRP, dispersion, bootstrap, and integration functions. This dependency is present in the checkout.
- Shared SDK graph/scoring/evolution/counterfactual/conservation services are mounted by Trading’s `main.py` and provide useful infrastructure.
- The shared evidence gate is not satisfied. C-OSS-1Q still has real-fixture/ClaimRegistry work open.
- Regime-indexed centroid/accessor work is not complete. C-REGIME and EXP-REGIME remain forward, so TRD-S7 cannot be promoted from ARCH.
- MAP C-GOV says prompt-variant promotion is not yet conservation-gated. That is a cross-service governance risk for any claim that outcomes safely improve later behavior.

### 4.5 Demo scenario coverage

| Beat | Can run today? | Reason |
|---|---|---|
| TR1 BYOD observation | Yes, with boundary caveat | `/api/trading/import/csv` and import tests exist; explicit no-egress proof is absent. |
| TR2 mirror | Substantially yes | Trust-analysis/fingerprint surfaces and P53 evidence exist. |
| TR3 edge drift / Rejection Moment | Partial | Related edge, rejection, and execution surfaces exist; exact demo acceptance/receipt was not proven. |
| TRD-S1/S2/S3/S4 | Partial / NEAR | Regime and situation infrastructure exists; C-TRD-SIT remains open. |
| TRD-V1/V2/V5/V6/V7 | Partial / NEAR | Quant cards and functions exist; C-TRD-VOL, real-fixture, and claim-gate work remains. |
| TRD-S7 | No for full beat | Re-convergence UI exists, but regime-indexed experiment and accessor are open. |
| TRD-CLAIM-GATE / CERTIFICATE / GATE-DIVIDEND | No | No matching implementation found. |

### 4.6 Open-source readiness

The current combined checkout is not SAFE-2-ready. `main.py:572` mounts `broker_router`; `broker_router.py:208` exposes POST `/orders`, and the Alpaca/IBKR adapters plus CLI order command can place orders. That directly violates the stated OSS requirement for no reachable broker-write endpoint. The required negative tests were not found.

No embedded API secret was found in the reviewed Trading code; broker credentials are read from environment variables. That is positive but insufficient. Standalone packaging also needs a deliberate treatment of the `ci_platform` import and a local-data/no-egress proof. Existing SQLite/local import paths are compatible with a local-first direction, but they do not prove that no raw rows can leave the process or machine.

## 5. MAP Reconciliation

### Covered or substantially covered MAP work

P48–P63 cover the older Trading foundation: domain config, Alpaca connector/regime recommender, yfinance, factor set, CLI, trust radar, pattern detector, journal, IBKR, CSV import, PyPI, and evidence/NL. P78–P86 cover outbox replay, proof, SDK docs, regime classifier, read-only realtime score, agent evolver, and OSS evolution infrastructure. R1, R4, and R6 are recorded CLOSED/PASS; R2 and R3/R5 are recorded DROP_CONFIRMED despite related code and later queue entries.

These closures explain the strong baseline and the broad code/test surface, but they do not close the v1.1 addendum deltas.

### Open, forward, or internally inconsistent MAP work

- **P83 TRD-PROMOTION-ENGINE** remains open and is conservation-gated; this is relevant to safe promotion but is not the F16 evidence gate.
- **C-OSS-1Q** has open real-fixture reproduction and ClaimRegistry migration steps.
- **C-TRD-SIT** is open for situational tagging, autonomy throttle, and per-regime read-layer stats.
- **C-TRD-VOL** is open for clustering-adjusted Sharpe, VRP/insurance, regime-conditioned rich/cheap, dispersion follow-rate, and effective-bets tail.
- **C-REGIME / EXP-REGIME** are open for regime-indexed centroids/accessor and the re-convergence experiment.
- R2/R3/R5 are marked DROP_CONFIRMED in the historical table while the post-P85 queue still lists corresponding #171, #173, and #176 work. This status inconsistency should be resolved before using MAP closure as acceptance evidence.

### MAP-missing findings

No matching MAP item was found for the complete F16/shared evidence gate, clean-trader/D-null certificate, pre-trade belief capture, signed `.jmt` counterfactual, parasitic distribution connector, complete Judgment Memory extension, SAFE-2 execution-route removal, or SAFE-4 no-egress proof. These are the highest-value reconciliation findings because the addendum made them explicit while the older MAP audit could not have covered them.

## 6. Recommended MAP Additions

| Proposed item | Scope | Priority | Dependencies | Estimate |
|---|---|---|---|---|
| TRD-F16-EVIDENCE-GATE | Shared ClaimGate SDK: BH-FDR, deflated Sharpe, 70/30 discover-confirm split, 23-hypothesis badge, ClaimRegistry migration, real fixtures, API/UI wiring. | P0 / demo and pilot | C-OSS-1Q, provenance, quant substrate | 1–2 weeks |
| TRD-SAFE-OSS | Remove or isolate broker-write routes/CLI from OSS profile; add `test_no_execution_endpoint` and `test_byod_is_observation_only`. | P0 / release blocker | Packaging profile, route audit, counsel gate | 3–5 days |
| TRD-SAFE-EGRESS | Prove raw imported rows remain local; add `test_no_trade_data_egress`; document ci-platform boundary. | P0 / release blocker | Local storage and import architecture | 3–5 days |
| TRD-CLEAN-CERT | Implement clean-trader/D-null certificate over the 23-detector registry and wire observation-only presentation. | P1 / demo | TRD-F16-EVIDENCE-GATE | 3–5 days |
| TRD-AUTO-ABSTAIN | Complete situation tagging and autonomy throttle, including B2+B6+B4 regime-break trigger and explicit abstention state. | P1 / pilot | C-TRD-SIT, B1–B8 | 1 week |
| TRD-VOL-EVIDENCE | Complete TRD-V1/V2/V5/V6/V7 with real fixtures, provenance, day-zero handling, and claim-gate routing. | P1 / pilot | C-TRD-VOL, TRD-F16 | 1–2 weeks |
| TRD-REGIME-RECONVERGENCE | Complete accessor/R-axis/regime-indexed centroids and cold-start experiment; promote S7 only on result. | P1 / pilot | C-REGIME, EXP-REGIME | 2–3 weeks |
| TRD-BELIEF-JMT | Specify and implement belief capture plus signed `.jmt` counterfactual replay and Judgment Memory properties. | P2 / v1.1 or roadmap | Key management, CF engine, local-first policy | 2–4 weeks |
| TRD-DISTRIBUTION | Implement a concrete parasitic connector contract, beginning with a local/export-only adapter. | P2 / roadmap | SAFE-4, TradeZella positioning decision | 1–2 weeks |
| TRD-COMPOUNDING-PROOF | Wire outcome/R-multiple/execution-quality signals, later-score measurement, and a regression test demonstrating improvement without a premature LIVE claim. | P1 / pilot | Scorer, variant store, evidence gate, conservation | 1–2 weeks |

## 7. Priority Queue

### Demo-blocking

1. Add and wire TRD-F16-EVIDENCE-GATE; current claim-gate/certificate/gate-dividend beats are GAP/MAP-MISSING.
2. Close TRD-SAFE-OSS before showing any OSS or observation-only demo; the reachable POST `/api/broker/orders` route is a direct contradiction.
3. Close TRD-SAFE-EGRESS and add the explicit no-egress proof.
4. Resolve the R2/R3/R5 DROP-versus-queue inconsistencies so demo claims have a reliable MAP status.

### Pilot-blocking

5. Complete C-TRD-SIT for abstention and autonomy throttle.
6. Complete C-TRD-VOL with real fixtures, provenance, and F16 routing.
7. Complete the outcome-to-later-score compounding proof, retaining the designed/not-built honesty label until the test passes.

### v1.1

8. Implement the clean-trader/D-null certificate.
9. Resolve T17’s IV/RV status: either satisfy the full contract or keep it explicitly deferred despite existing IV/VRP primitives.
10. Complete regime-indexed re-convergence only after C-REGIME/EXP-REGIME evidence.

### Roadmap

11. Pre-trade belief capture.
12. Signed `.jmt` counterfactual replay and full Judgment Memory property set.
13. Parasitic distribution connector and the associated open-source/local-first boundary.

## Bottom line

The older MAP’s broad Trading foundation is real and well tested, but its “zero gaps” conclusion cannot be carried forward to the supplied v1.1 materials. The highest-priority gaps are the addendum’s F16 evidence gate, the clean-trader certificate, and the explicit OSS safety gates. Quant and regime building blocks are present, but remain PARTIAL/NEAR because the MAP’s integration, real-fixture, evidence, and regime-indexing work is still open. The product’s own honesty rule is correct: the compounding loop should remain **designed/not-built**, not LIVE.
