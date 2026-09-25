# Demo Scenarios v2.9 — Trading & Purchasing Additions

**Surgical delta to:** `demo_scenarios_and_usecases_v2_8.md`  
**Date:** September 13, 2026  
**Requested deliverable:** `demo_scenarios_v29_trading_purchasing_additions.md`  
**Basis:** the supplied v2.8 document and `prompt_for_fable_v28_extension.md`. Experiment results and implementation inventories below are **reported by the supplied prompt**, not independently reproduced. No repository, experiment logs, model checkpoints, or companion architecture documents were supplied.

**Recommendation:** add four distinct ARCH beats, retain the reported preseed routes as regression targets, and repair the older scripts before staging. The strongest defensible story is **verified-outcome-grounded evidence selection, an inspectable investigation trace, and bounded authority**. The supplied experiments do not establish that within-decision recurrence routes better than static planning.

**How to apply:** insert §§1–4 below as the final four beat blocks in v2.8 §4.17, immediately before `### VLD integration notes`. Append §5 to those notes. Apply §§6–9 at the explicit anchors stated there. Append §10 beneath the updated VLD-GUARD block. These are additions and targeted replacements; do not replace the source document with this delta. The original 94-scenario catalog counts stay unchanged: these are investigation overlays, not four newly shipped scenarios.

| Delta section | Destination in v2.8 | Operation |
|---|---|---|
| §§1–4 | §4.17, after VLD-S2P-1 | Add four beat blocks |
| §5 | §4.17 integration notes; §4.12/§4.13 bridge anchors | Append bridges |
| §6 | §0.1 Room 16; §0.3 Room 16 rows and caveat | Replace Room 16 framing; add domain answers |
| §7 | `### VLD preseed additions (v2.8)` under §5 | Replace shared VLD preseed requirements and extend all five domains |
| §8 | §7.2 Loom insertion table and beats-config paragraph | Append two cuts; replace unsafe warm-up convention |
| §9 | §4.17 shared introduction and existing five beats; §2.5; §4.18; document control | Targeted corrections and replacement text |
| §10 | §4.18, after VLD-GUARD | Add authoring compliance matrix and release checks |

**Interpretation rules used throughout this delta**

- All four new beats remain **ARCH**. “What audience sees” is a storyboard contract; it is not a report of a working endpoint or successful runtime replay.
- Keep `PLANTED FIXTURE`, `ROADMAP`, and `ROUTING ACCURACY: not yet measured for this deployment` visible throughout each trace and comparison. Offline experiment results are a separate evidence class, labeled `REPORTED OFFLINE EXPERIMENT`; they are not fixture values or customer measurements.
- All proposed raw evidence in §7 is synthetic. Required action transitions and routes must be obtained from the actual frozen scorer and recorded trace before staging a computed replay. No hand-entered margins, fabricated learned weights, or edited route outputs.
- Dimension indices are **zero-based**, following the factor lists in the supplied prompt. Display human-readable factor names, never bare indices, to buyers.
- The supplied R0–R5 list contains **six labels**, not five. Use “R0 baseline plus five recurrence levels.” Distinguish recurrence levels from older delivery milestones with the prefixes `REC-` and `BUILD-`; neither prefix renames the original taxonomy.
- ARCH classification also preserves Trading's observation-only constraint: all Trading scenes are historical, synthetic replays, with no trade execution or current market recommendation.

## §1: VLD-TRD-1 — “The Position Wasn’t Alone”

**Insert in §4.17. Story:** portfolio exposure changes the investigation order before the historical execution assessment changes. This is the positive, supported-provider story; it does not imply that Trading's unvisited factors are unimportant.

| Field | Value |
|---|---|
| **Surface** | Trading **Analysis** → new `InvestigationTracePanel`, opened from a selected historical trade beside the existing Trust Radar. Add a portfolio-evidence drawer; proposed UI, not an existing tab. |
| **API** | `POST /api/trading/investigate`. Request is anchored to a decision, historical trade, frozen portfolio snapshot and `as_of` time. Route target: **dim 2 `position_sizing` → dim 1 `market_regime`**. |
| **Class** | **ARCH**. The prompt reports both dimension providers; Decision→Trade attachment, portfolio correlation traversal and temporal filtering remain unbuilt. |
| **What audience sees** | (0) A synthetic historical `trend_following` case has single-pass action `strong_execution`. Its thesis looks attractive, but the trace lists position sizing as the first selected evidence dimension. (1) The portfolio read reveals three other positions sharing exposure with this trade. Their identities are reached by the portfolio provider's entity traversal, labeled `CONTENT-KEYED / PREREQUISITE`; Q selected the **dimension**, not each position. Evidence is admitted into the documented factor transformation. (2) After re-scoring, market regime is the next selected dimension. Its historical evidence completes the assessment. The reported preseed's final target is `partial_execution`; the trace must locate the actual flip at the step where it occurs. (3) The panel halts at the configured budget and displays the original and investigated assessment. |
| **Caption** | *The historical setup looked strong. The portfolio changed the assessment.* |
| **Spoken** | “In this planted historical case, the score selected portfolio exposure first. That read connected the trade to three positions already on the book. It then checked the market regime, and the assessment ended at partial execution. The trace shows the selected order and the records behind it. Correlation supplied the evidence; the scorer selected when to request it.” |
| **Silence beat** | **SILENCE 8.** Pause for five seconds when `1 · Position sizing → three linked positions` appears above the still-unread thesis entry. Keep the roadmap and provenance badges visible. Resume: “The first check was the portfolio.” |
| **DoD / Honesty** | Preserve `VLD-TRD-1` as the reported regression ID; introduce the expanded portfolio fixture with a versioned suffix, rather than claiming those edges existed in the original seed. Replay must produce route `[2,1]`, final `strong_execution → partial_execution`, actual intermediate actions, evidence references and Q ordering. No assertion that every volatile case checks risk first. No investment return, risk reduction or timing claim. Routing accuracy remains unmeasured for deployment. Where the configured budget covers every eligible read, say exhaustive retrieval could also inspect them all; otherwise say unvisited reads remain. |

**Internal validation contrast:** use the same frozen scorer and policy on a paired portfolio snapshot with reduced shared exposure. Preserve the thesis inputs and log all changed exposure inputs. A different order is a **test target**, not a promised result; show it only if Q actually changes the ranking. A source named `portfolio_engine` does not independently establish why that dimension won.

**Optional regime contrast:** connect to TRD-S1 only after a paired calm/volatile replay proves a route difference. The given Q formula does not itself establish regime-indexed K or a general “thesis in calm / risk-reward in volatility” policy. `risk_reward` and `thesis_strength` have no registered evidence providers in the supplied inventory, so that suggested contrast needs additional wiring.

## §2: VLD-TRD-2 — “The Check It Never Made”

**Insert in §4.17. Story:** an apparently reasonable investigation ends with a visible evidence blind spot. The distinction from TRD-1 is **coverage failure and missing evidence**, not another successful portfolio flip.

| Field | Value |
|---|---|
| **Surface** | Trading **Analysis** → `InvestigationTracePanel`, with an “Unvisited evidence” drawer and a separately labeled diagnostic replay. Connect to TRD-CERTIFICATE's evidence-boundary story. |
| **API** | Main replay: `POST /api/trading/investigate`, reported route **dim 2 `position_sizing` → dim 3 `timing_quality`, returning `None`**. Diagnostic: a separate proposed sandbox replay admitting dim 9 `options_iv_percentile`; no invented production endpoint or silent provider addition. |
| **Class** | **ARCH**. Dim 3 has no provider in the reported registry. Neither dim 8 nor dim 9 has one. A legacy missing-provider attempt must be distinguished from an eligible evidence read. |
| **What audience sees** | (0) A synthetic historical `income_strategy` case starts at `strong_execution`. (1) Position-sizing evidence changes it to `partial_execution`. (2) The reported legacy route attempts timing quality and receives no evidence. Display `UNAVAILABLE / NO EVIDENCE ADMITTED`; do not change the factor vector or action merely because `None` arrived. (3) Halt with the coverage gap visible. The inventory lists options delta exposure and IV percentile as unavailable through the current provider configuration, independently of any learning-coverage status. (4) Open a separate `MANUAL EVIDENCE REPLAY — NOT POLICY-SELECTED` card: a planted historical IV percentile is admitted through a proposed adapter and the scorer is run again. The desired diagnostic is a further assessment change; publish the actual result, including no change if that is what the scorer produces. |
| **Caption** | *An investigation can finish with an important check still missing.* |
| **Spoken** | “This planted replay checked position sizing first. Its next attempt returned no evidence, and the trace kept that gap visible. The options check was never made. This separate replay asks what the missing IV evidence would have changed; it does not show that the policy selected it. In the supplied offline Trading experiment, 24 of 50 category–dimension pairs received no learning updates. That is a coverage limit we need to measure, not hide.” |
| **Silence beat** | **SILENCE 9.** Pause for five seconds with `2 · Timing quality — unavailable` beside `IV percentile — not queried / provider absent`. Let the missing check remain visible before opening the manual replay. |
| **DoD / Honesty** | Keep the reported `VLD-TRD-2` result `[2,3(None)]`, `strong_execution → partial_execution`, as a legacy regression target. In a provider-aware policy, dim 3 should be excluded before dispatch; the new trace may therefore differ and must carry a different policy version. Never force an unavailable dimension to preserve the choreography. The diagnostic read is a new episode with its own costs and badges. It cannot be counted as part of the original two-attempt budget, credited to Q, or represented as an automatic starvation cure. |

**The options action change is gated:** high IV percentile alone does not establish a worse trade. Plant an explicitly described historical strategy and evidence transformation consistent with that strategy; require a faithful scorer counterfactual. If admitting IV leaves the action unchanged, show changed support or the remaining uncertainty, or withhold the action-change vignette. Do not assign a favorable or unfavorable options interpretation by hand.

**Optional technical extension:** after the options provider and a legally reachable learned-K checkpoint exist, replace the manual card with a **separate** matched comparison of unit K and learned K under the same scorer geometry, candidates and budget. Show “learned K selected IV first” only if the recorded Q ranking proves it. Greedy learning cannot be presumed to teach a factor that receives no updates. The reported Thompson/UCB coverage improvement came with poorer Trading routing; it is not a ready-made production fix.

## §3: VLD-PUR-1 — “Demand Wasn’t the Limiting Factor”

**Insert in §4.17. Story:** a real demand increase within the synthetic scene fails to justify a larger order because usable shelf life constrains supply. The differentiator is the **event check followed by the waste check**, with category-specific priorities demonstrated only where supported by replay.

| Field | Value |
|---|---|
| **Surface** | Purchasing **Analysis** → selected P1 Smart Ordering case → `InvestigationTracePanel` beside an order-evidence drawer. This placement is a proposed integration with the existing ordering surface. |
| **API** | `POST /api/purchasing/investigate`. Bind to a historical order and item. Reported fixture alias: `VLD-PUR-DEMAND-SPIKE`. Route target: **dim 5 `event_flag` → dim 4 `waste_risk`**. |
| **Class** | **ARCH**. `waste_tracker` is reported registered; the event evidence adapter, Decision→Order attachment and historical cutoff are not established. |
| **What audience sees** | (0) A protein order starts at `order_more` because the current factor state supports increased demand. (1) The selected event read confirms the scheduled service and expected covers; no cancellation is manufactured to make the ending easy. (2) Re-scoring selects waste risk next. Lot expiry, usable inventory, storage limits and the next feasible delivery show that increasing **this delivery** would strand perishables. (3) The assessment ends at `order_less`, as targeted by the reported seed. The trace identifies which read caused the change. It does not claim the later service demand vanished. (4) The evidence drawer links the relevant prior verified deliveries and waste outcomes to the retained snapshot used after the manager handoff. |
| **Caption** | *The event was real. This delivery would not keep.* |
| **Spoken** | “The first check confirmed the event. The next checked whether the extra stock would still be usable. In this planted case, the order changed from more to less for this delivery. The next manager can inspect the delivery and waste records behind that assessment. The investigation is designed to carry retained knowledge into a new order.” |
| **Silence beat** | **SILENCE 10.** Pause for five seconds when the second row reveals `expiry before service` directly below `event confirmed`. Resume: “More demand did not make this delivery usable.” |
| **DoD / Honesty** | Canonical beat ID `VLD-PUR-1` maps explicitly to the existing seed ID. The event read cannot run until an adapter for dim 5 exists; having F2 Event Intel elsewhere in the product does not prove an investigation provider is registered. Enforce route `[5,4]` and target `order_more → order_less` through the actual scorer, with no hardcoded event→waste branch. Persist source-to-factor transformation and category. No order placement, spoilage savings, manager ramp-time or guaranteed next-decision improvement is claimed. Both standing provenance/accuracy badges remain visible. |

**Category contrast for a technical cut:** pair this protein fixture with a dry-goods fixture whose replay places `cost_deviation` first. Use one real learned checkpoint with category-specific provenance, and log differences in the food data. Label this an illustrative category comparison, not an isolated causal test of K. To isolate K, hold category, geometry and evidence fixed and compare legal K checkpoints separately. Never say “protein always checks waste first”: this main beat explicitly checks the event first.

## §4: VLD-PUR-2 — “The Handoff Kept the Delivery History”

**Insert in §4.17. Story:** the incoming manager can inspect why an apparently routine supplier order becomes unsuitable and what retained evidence supported the sequence. This is **continuity plus delivery feasibility**, distinct from PUR-1's event/shelf-life conflict.

| Field | Value |
|---|---|
| **Surface** | Purchasing **Analysis** → P1 Smart Ordering case → `InvestigationTracePanel`; evidence drawer links to P5 Supplier Scorecard. Close beside PUR-HERO / The Handoff, without implying that the full continuity feature is already LIVE. |
| **API** | `POST /api/purchasing/investigate`. Reported fixture alias: `VLD-PUR-VENDOR-CASCADE`. Route target: **dim 4 `waste_risk` → dim 3 `supplier_lead_time`**. Alternative-supplier lookup is a proposed content-keyed follow-up through `supplier_scorecard`. |
| **Class** | **ARCH**. Lead-time evidence registration, Decision→Order linkage, supply-chain traversal and as-of history filtering are build requirements. |
| **What audience sees** | (0) A dairy order at the manager handoff starts at `order_as_planned`. (1) Waste evidence establishes how long the current usable stock can cover service; the scorer then selects supplier lead time. (2) A timestamped delivery record and supplier history show that this order cannot arrive within the usable-stock/service window. The final target becomes `skip` **for this order**, not “stop supplying the kitchen.” (3) Only after the assessment, an optional `CONTENT-KEYED / ALTERNATIVE-SUPPLIER LOOKUP` lists approved alternatives and their known delivery windows. This is a separately costed follow-up, not a hidden third VLD read or an automatically placed replacement order. (4) The drawer shows the prior manager's verified delivery records, their dates, the frozen retained snapshot and the incoming manager's access to that evidence. |
| **Caption** | *The manager changed. The delivery record remained inspectable.* |
| **Spoken** | “This planted replay checked usable stock first, then whether this supplier could arrive in time. It ended at skip for this order. The delivery evidence is linked to verified records from before the manager changed. The alternative-supplier list is an ordinary lookup, labeled separately. Everything in this kitchen turns over. This record doesn't.” |
| **Silence beat** | **SILENCE 11.** Pause for five seconds on the second row: `supplier arrival after service cutoff`, with the prior manager's verified delivery record visible beneath it. Resume: “The incoming manager can see what was retained.” |
| **DoD / Honesty** | Map `VLD-PUR-2` to the reported vendor-cascade seed without silently renaming its stored ID. Replay route `[4,3]` and final `order_as_planned → skip`; log actual intermediate actions. Prior delivery outcomes must predate the case and actually contribute to either scorer state or admitted evidence as documented. A visible old note alone is not proof of learned judgment. The alternative supplier must be approved for this item/site and is never invented to guarantee resolution. Keep ARCH, fixture and unmeasured-routing badges visible. |

**Continuity control:** replay the same case and frozen snapshot before/after changing only manager identity and authorized access context. The retained evidence, ranking and assessment should remain invariant when manager identity is not a scorer input. If the actual policy conditions on manager identity, disclose and test that contract instead. This verifies retained state; it does not measure better replacement-manager performance or weeks saved.

**Supplier reliability and price-memory depth cards:** §7 provides a synthetic on-time history of 17/50 and a matched historical unit-price comparison. These are potential evidence sources, not automatic reasons for the route `[4,3]`. “Reliability before demand” requires a separately replayed `[1,2]` comparison. `price_memory_index` (dim 6) remains an unavailable investigation input until a provider exists; any manual price replay is labeled exactly like the options diagnostic in TRD-2. Do not conflate supplier delivery reliability with trust in a supplier's data feed.

## §5: VLD Integration Notes

**Append these entries to §4.17 `### VLD integration notes`.** Add the corresponding bracketed cross-reference immediately below §4.12 and §4.13's headings.

| Bridge | Placement and presenter text | Scope |
|---|---|---|
| **TRD-CLAIM-GATE / TRD-CERTIFICATE → VLD-TRD-1** | After the evidence-gated mirror: “The mirror establishes what this historical record supports. This architecture preview shows which evidence the scorer would request for an individual case.” | Statistical claim admission and evidence selection are different functions; one does not validate the other. |
| **VLD-TRD-1 → TRD-S1 / TRD-V7** | “The portfolio read gives the regime and exposure views a concrete place in the investigation trace.” | Preserve each parent beat's class. No claim that its analytics are already investigation providers. No claim of fast regime reconvergence. |
| **VLD-TRD-2 → TRD-CERTIFICATE / TRD-GATE-DIVIDEND** | “An unsupported check belongs on the record, just as an unsupported finding belongs outside the claim gate.” | No options diagnostic P&L, no blanket conclusion that missing evidence is harmless. |
| **PUR-HERO open → VLD-PUR-1** | After gated I1: “Now take one order. Which evidence should the investigation request before changing it?” | Keep the signal reliability / invoice-variance profile naming; no accusation of supplier misconduct. |
| **VLD-PUR-2 → PUR-HERO / The Handoff** | “Here are the decisions, delivery records and retained snapshot the next manager can inspect.” Then the existing continuity close. | Provenance supports the retention story; a causal performance claim needs a separate baseline. |
| **VLD-PUR-2 → PUR-REFUSAL / PUR-PROOF-LEDGER** | “The investigation can change an assessment. The authority gate determines whether an action may be emitted.” | Keep the gate separate from Q and halt logic. No automatically placed order or VLD savings figures. |

**Shared technical bridge — RGI:** “CI calls this Recursive Graph Improvement, or RGI: a governed, verified-outcome-grounded instance of RSI, bounded at L3, with L5 excluded by design. This preview uses a frozen retained snapshot during the investigation; updates from verified outcomes belong to the between-decision learning path.”

Use the full expansion **Recursive Self-Improvement** only when defining the established field term RSI, never as the name of CI's mechanism. Architectural L3/L5 boundaries are distinct from `REC-R3`/`REC-R5`; their detailed authority model is not supplied here. This definition is the required positioning, not fresh evidence that every proposed loop is implemented or gated. AE may propose routing **parameter** variants through the stated governance path; structure evolution and automatic authority expansion are not implied.

## §6: Room 16 Updates

**Replace only row 16 of §0.1 with:**

| # | Room | Kill-shot beat | The line | Class |
|---|---|---|---|---|
| 16 | Score-conditioned investigation | VLD-SOC-1; domain alternatives VLD-TRD-1 / VLD-PUR-1; coverage/continuity deep cuts VLD-TRD-2 / VLD-PUR-2 | “The trace shows which evidence was selected first, what it changed, and what remained unchecked. The priority comes from the retained scorer state; the records let you inspect it.” | **ARCH**. NEAR requires the branch-policy prototype, trajectory store and beat-specific domain wiring. LIVE additionally requires the matched deployment evaluation specified in §9. |

**Replace the Room-16 framing note immediately below that map with:**

> The demonstration establishes an inspectable, scorer-conditioned order on a labeled fixture. A fixed checklist, a static scorer-conditioned plan and an adaptive scorer-conditioned policy are different comparators. The supplied experiment favored static planning on routing, while RNN had higher final accuracy; this does not establish an adaptive-routing advantage. The product hypothesis concerns the value of the retained, verified-outcome-grounded substrate and its governance. Evaluate routing policy separately.

**Replace the three existing Room-16 rows in §0.3; then append four domain rows:**

| Room | When they say… | You say… |
|---|---|---|
| 16. Investigation | “Our agents investigate too.” | “Then compare the evidence priority, its recorded basis, and the stopping behavior. This preview makes all three inspectable. Whether that improves decisions at the same budget is an empirical question.” |
| 16. Investigation | “We have graph-based reasoning.” | “Graph access is useful here too. Our proposed contribution is a scorer-conditioned choice of what to retrieve, with an evidence trace and a bounded action gate. Graph access alone does not establish the value of that choice.” |
| 16. Investigation | “We use RAG with reasoning.” | “Iterative retrieval can also change its next query. Our comparison asks whether priority derived from this deployment's verified decisions improves results under the same evidence budget. We need to demonstrate that, rather than infer it from the architecture.” |
| 16. Trading | “We already measure portfolio correlation.” | “Keep that source. In this planted historical replay, the score selected the portfolio check first and the retrieved exposure changed the assessment. The trace connects the source to the decision.” |
| 16. Trading | “Does checking more factors solve the problem?” | “Coverage and routing quality are different. Our supplied experiment reduced unvisited Trading pairs with exploration, but routing worsened. This preview shows an unchecked options factor explicitly; it doesn't promise that more reads solve it.” |
| 16. Purchasing | “Our purchasing system stores supplier history.” | “That history is an input. This preview shows when delivery evidence was requested, how it changed this order's assessment, and which verified records the incoming manager can inspect.” |
| 16. Purchasing | “An ordering rule can check demand and waste.” | “It can. Here you can inspect why the event check preceded the waste check for this case. A static plan may work just as well; the comparison must use the same evidence and budget.” |

**Replace the standing caveat beneath the original three rows with:**

> “These Trading and Purchasing domain paths are an architecture preview. The supplied materials report investigation preseeds and offline experiments; this document does not establish that the production entity links, historical filters, providers and trace surface are shipped. We will show the implementation status and distinguish a computed fixture replay from a proposed storyboard.”

Remove the universal claims that graph retrieval is necessarily one read, agents without this mechanism use a fixed checklist, or another system cannot produce learned priorities. No named competitor product is run, no competitor performance is asserted, and no claim of exclusivity is inferred from the supplied material.

## §7: §5 Preseed Additions

**At §5's `### VLD preseed additions (v2.8)`, rename the heading `### VLD preseed additions (v2.9)` and replace its existing bullets with this section's requirements.** Apply the corresponding existing-domain replacements from §9. Leave the non-VLD preseed requirements intact.

### 7.1 Canonical factor and provider contract

Use this mapping to validate fixture IDs before running them. “Reported” means listed in the supplied prompt, not code-inspected in this review.

| Copilot | Dim | Factor | Reported provider / gap |
|---|---:|---|---|
| Trading | 0 | thesis_strength | No provider listed |
| Trading | 1 | market_regime | correlation_engine |
| Trading | 2 | position_sizing | portfolio_engine |
| Trading | 3 | timing_quality | No provider listed; reported TRD-2 attempt returns None |
| Trading | 4 | risk_reward | No provider listed |
| Trading | 5 | catalyst_proximity | event_scanner |
| Trading | 6 | portfolio_concentration | No provider listed |
| Trading | 7 | sector_exposure | portfolio_engine |
| Trading | 8 | options_delta_exposure | No provider listed; proposed options adapter |
| Trading | 9 | options_iv_percentile | No provider listed; proposed options adapter |
| Purchasing | 0 | cost_deviation | invoice_analytics |
| Purchasing | 1 | supplier_reliability | supplier_scorecard |
| Purchasing | 2 | expected_demand | demand_forecast |
| Purchasing | 3 | supplier_lead_time | No provider listed; new supplier delivery adapter |
| Purchasing | 4 | waste_risk | waste_tracker |
| Purchasing | 5 | event_flag | No provider listed; new event adapter |
| Purchasing | 6 | price_memory_index | No provider listed; new matched-price-history adapter |

**Do not alias away the schema conflict:** `signal_confidence` and `options_gamma_risk`, named in the Trading starvation prose, do not occur in the provided ten-factor list. Record them as unresolved experiment-schema labels. Do not silently map them to thesis strength, timing quality, delta exposure or IV percentile. The aggregate 24/50 is reportable as the supplied result; factor-specific claims require the run's exact dimension map and update counts. Provider coverage in the application and learning coverage in the experiment are separate inventories.

### 7.2 Fixtures, evidence and honest expectations

The values below are **proposed synthetic raw records**, not observed output from the named preseeds. They make each story concrete. The implementation must apply the real normalization and scorer to them; if the target route or action is not reproduced, revise the fixture transparently or the storyboard, never the computation. All fixtures carry stable IDs, version, content hash, category, action enum version and a common historical cutoff.

| Beat / seed | Required planted evidence | Required replay / limits |
|---|---|---|
| **VLD-TRD-1**, extended portfolio fixture | Synthetic instrument `SYN-ALPHA`; three held positions `SYN-BETA/GAMMA/DELTA`. Proposed same-window historical return correlations 0.82/0.76/0.71, with the underlying return series retained. Freeze holdings and the sizing inputs before the candidate trade. Attach a historical market-regime record. | Correlations are computed from the planted series, not typed badges. They are pairwise associations, not a calculation of effective bets or proof of risk reduction. Record the portfolio-engine mapping into dim 2, then dim 1. Target `[2,1]`, final strong→partial. |
| **VLD-TRD-2**, legacy + diagnostic | A separate historical income-strategy case; dim 2 evidence sufficient for the reported initial flip; dim 3 missing/unavailable. Proposed options diagnostic: IV percentile **94**, based on a declared historical window ending at cutoff, with an internally consistent synthetic options snapshot. | Legacy `[2,3(None)]`, strong→partial. No factor/action change from None. Diagnostic manually admits dim 9 in a new episode; an additional action flip is unverified until computed. IV percentile is not implied volatility of 94%, a probability of loss, or a recommendation. |
| **VLD-PUR-1** / `VLD-PUR-DEMAND-SPIKE` | Protein case: baseline **120** covers and a confirmed **180**-cover event. Proposed extra lot expires before that event; include lot quantities, existing usable stock, refrigerated capacity, service time and a separately documented later delivery opportunity. | Compute event_flag and waste_risk using their actual semantics. Target `[5,4]`, more→less for the selected delivery. Do not claim the alternative delivery is booked or guaranteed. |
| **VLD-PUR-2** / `VLD-PUR-VENDOR-CASCADE` | Dairy case: **12 hours** until service, supplier arrival **30 hours** away, expiry/usable-stock records establishing the gap. Proposed supplier on-time record: **17 on-time deliveries out of 50** eligible verified deliveries, hence 0.34. Plant two approved alternative-supplier records, with availability allowed to be unknown. | Target `[4,3]`, planned→skip for this order. “On time” and the 50-record cohort are defined explicitly. The 0.34 is a supplier delivery statistic; it is neither a K value nor data-source trust. Alternatives are content-keyed and separately costed. |
| **PUR-2 price-memory depth card** | Same item, grade, pack size, currency and delivery terms: proposed current unit price **22**, matched historical median **20** from **12** eligible prior invoices. | Raw deviation is 10%; this is not automatically the normalized price_memory_index. New dim 6 provider required. No causal K story, action flip or savings claim unless separately replayed. |
| **VLD-TRD-S1** | Budget=0 version with initial strong_execution. | Zero provider calls; identical vector/action; explicit budget-zero halt; unsupported dimensions stay visible. |
| **VLD-PUR-S1-STANDARD** | Budget=0 version with initial order_more. | Zero provider calls; identical vector/action; explicit budget-zero halt. |

**Mandatory control fixtures:** missing provider; unavailable evidence from an otherwise registered provider; successful query with an informative negative result; future-dated record; stale record; exhausted candidate set; budget zero; and a conservation-blocked emit. These distinguish evidence absence, negative evidence, policy choice and authority. Do not infer an “unresolvable” case solely from budget exhaustion.

### 7.3 Domain wiring that must be built

| Wiring item | Trading | Purchasing | Acceptance evidence |
|---|---|---|---|
| Decision attachment | `decision_id → trade_id → ticker → historical position` | `decision_id → order_id → item → supplier` | Stable tenant/account/site-scoped IDs; missing/ambiguous links return explicit unavailable status. No latest-record fallback. Imported observations do not become verified decisions by virtue of import. |
| Domain traversal | Candidate trade → portfolio as of case time → correlated positions via portfolio_engine | Item/order → approved supplier relationships → alternatives via supplier_scorecard | Actual edges/queries and source references recorded; labels distinguish content-keyed traversal from Q dimension selection. An analytics panel does not prove a traversable investigation path. |
| Historical cutoff | Historical trades, holdings, prices, returns, corporate/event records and verification times | Orders, supplier commitments, receipt/waste outcomes, invoices, event revisions and verification times | Require both event time and information-availability/verification time to be no later than the case cutoff. A later correction must not leak into the replay. |
| Historical learned state | Model/K snapshot trained only on outcomes available by cutoff | Same, including pre-handoff retained state | Snapshot provenance and training cutoff logged. Filtering evidence while using future-trained K is still leakage. |
| Missing providers | Register timing, options and any proposed thesis/risk readers explicitly | Register event, lead time and price memory explicitly | Report real registry coverage. Define provider eligibility and failure behavior; keep the legacy None trace separately versioned. |
| Source-to-factor mapping | Portfolio correlations can inform documented sizing/exposure factors | Shelf life, arrivals and prices map through documented normalization | Record changed dimensions and evidence lineage. If one read updates multiple factors, disclose all of them and any bundled source work. |

Historical correlation computation also needs a declared return frequency, lookback, missing-data treatment and minimum support. Historical supplier/price matching needs item/site/pack/terms scope and a declared cohort. Do not use current holdings, subsequently revised delivery promises or the eventual outcome of the case under investigation.

**Conservation configuration:** the supplied update reports penalty ratios of **Trading 2:1** and **Purchasing 3:1**. Record and verify the actual pinned configuration and the error directions those ratios weight; do not silently change application policy to match this document. These are reported model settings, not evidence that Trading decisions are inherently low-stakes. Each replay records the real emit-gate result independently of its investigation order.

### 7.4 Policy, budget and trace contract

Use the supplied Q equation, not the older dominant-factor or confidence-threshold dispatch story:

```text
Q_d = K_d * G_d
G_d = 1 / (100 * max(sigma_d^2, 0.001))
      + abs(mu[a1,d] - mu[a2,d])
      + abs((v[d] - mu[a1,d])^2 - (v[d] - mu[a2,d])^2)
```

The implementation must declare how a1/a2, category, K and variance are indexed; the prompt does not fully specify those contracts. Freeze learned μ, σ and K during each episode. Recompute Q after admitted evidence changes the case state, using the actual action pair. Record eligibility changes separately. This is a score-based priority heuristic, not a calibrated expected-value-of-information estimate or an optimality guarantee.

For any claim that learned K caused d to precede j, record the actual comparison `K_d G_d > K_j G_j`, the unit-K order and the real learned checkpoint. With positive weights, the crossing condition is `K_d/K_j > G_j/G_d`; actual K bounds and update rules determine whether it is reachable. Since those bounds and checkpoint values were not supplied, no specific K-dependent ordering is certified here. Do not plant arbitrary values such as K=0.9/0.3 and call them learned.

**Budget convention proposed for v2.9:** B=2 means at most two evidence-request attempts, including failed attempts. A bundle of provider queries is not free: record underlying request count and cost as well. Capture separately attempted reads, successful reads, admitted observations, exclusions and unvisited candidates. If the runtime uses different accounting, document it and update the caption; never relabel an attempt as a free read to preserve a scene.

Under provider-aware eligibility, an unregistered dimension is excluded without issuing a request. Under the legacy TRD-2 behavior, the failed dispatch attempt is visible and consumes its configured cost. A successful “no relevant records found” query may admit negative evidence only with adequate query coverage and a defined transform. `None`/unavailable supplies no such evidence. Re-scoring the same vector with the same frozen scorer must not invent an action flip.

Do not hardcode “halt after two” if the real policy halts earlier. Preseed must establish the actual stopping path. Store the runtime halt reason and all concurrently reached limits. Map budget exhaustion, unavailable/exhausted candidates, residual stopping, instability/flip limit, timeout and emit refusal distinctly. A halt can mean incomplete evidence; it does not mean certainty. Conservation is an emit-gate snapshot within the episode under the stated design, not the branch selector or evidence of routing accuracy.

**Persisted trace requirements (schema requirements, not a claim that these field names already exist):**

- Case/entity IDs; synthetic provenance; case and verification cutoffs; model/K/normalizer/provider/policy versions; category and exact action enums.
- Initial candidate inventory and eligibility; per-candidate Q components; selected dimension and tie-break; consumed cost; source record IDs; query coverage; availability status; admitted changes; raw evidence reference.
- Initial and per-step action/scores, exact flip step, halt reason, emit-gate outcome, and single-pass comparison on the identical initial state.
- Learning-support counts by category/dimension, with zero support distinguished from missing counters. Counterfactual/manual replay parent ID and independent budget.
- Engineering view may show formula quantities. Buyer view shows check order, evidence, assessment change, unresolved checks, budget and halt; no centroid/DK/σ/v_t/margin jargon or calibrated-confidence implication.

Persist append-only audit traces as the explicit allowed write; keep authoritative scorer, decision/outcome state and source graph unchanged during investigation. This resolves v2.8's simultaneous “read-only graph” and “persist trajectory in AGE” requirements. Never feed a fixture trace into customer verification metrics or the learning path.

### 7.5 Work packages and acceptance

| Package | Owner | Definition of done |
|---|---|---|
| SDK domain investigation wiring | **Session A** | Entity bindings, historical cutoffs, provider eligibility and transforms implemented for the four routes; truthful missing-provider behavior; existing score/learn APIs retain their semantics. |
| Shared trace and record mode | **Session A**, **Session C** for SOC parity | Persisted traces drive InvestigationTracePanel and recorded cuts; badges survive transitions, empty states and manual comparisons. Frozen model state remains unchanged. |
| Fixture and claim review | **Content + A/C** | Manifest links routes, computed numbers and legal K snapshots; missing evidence is shown honestly; scripts match actual traces and class status. |

Effort is **not estimated** without repository discovery; these are coherent packages, not claimed one-day wiring tasks. During implementation, include targeted backend checks plus Playwright coverage for an atomic investigation and the full mirror→trace→diagnostic/handoff flow. Review both line-by-line correctness and architecture/product conformance, including blast radius across the shared SDK and SOC surface. Report measured request latency, case/graph size, connection mode and rendering overhead separately from unmeasured analyst-time benefit.

## §8: §7.2 Loom Additions

**Append to the existing §7.2 insertion table.** Reconcile names explicitly: the requested **L-TRADING** is the existing **L-TRADER**; **L-PURCHASING** is the existing **L-PUR**. Preserve those existing config identifiers; do not accidentally create duplicate cuts.

| Requested label / canonical cut | Exact insertion | Timing and framing |
|---|---|---|
| **L-TRADING / L-TRADER** | Existing TR1 import → TR2 mirror, with TRD-CLAIM-GATE/TRD-CERTIFICATE where staged → **ROADMAP title card → VLD-TRD-1 / SILENCE 8 → optional VLD-TRD-2 / SILENCE 9** → existing TR3 edge drift and governed promotion/rejection close. | Core TRD-1 insertion: **75 seconds** planned video duration. TRD-2 deep cut: **90 seconds**. Full existing ~3-minute cut becomes ~5:45 if both are appended without trimming. These are editorial durations, never time saved by the product. |
| **L-PURCHASING / L-PUR** | PUR-HERO's gated I1 mirror → **ROADMAP title card → VLD-PUR-1 / SILENCE 10** → applicable ledger/refusal beat at its own class → **VLD-PUR-2 / SILENCE 11** → PUR-HERO / The Handoff close. | PUR-1 **75 seconds**, PUR-2 **90 seconds** planned. Full existing ~5-minute cut becomes ~7:45 without trimming. For a five-minute cut, retain one 75–90-second VLD insertion and deliberately trim the feature tour; do not pretend all additions fit unchanged. |

The short Trading cut favors TRD-1; the technical version includes the coverage failure. The short Purchasing cut favors PUR-2 because it earns the continuity close. Each beat has a silence moment, but a compressed cut may use one principal silence and move the other beat to an appendix. All simulated-user-data transitions explicitly return to planted data; importing the viewer's CSV does not make the VLD fixture their data.

**Replace the VLD beats-config paragraph beneath the insertion table with:**

> Every VLD entry carries `class: "ARCH"`, `badges: ["PLANTED_FIXTURE", "RHO_UNMEASURED"]`, a visible ROADMAP title, fixture/version reference, caption and silence cue. Preserve actual canonical cut IDs. Required new metadata must be implemented in the harness before it is assumed supported. Use an already persisted, deterministic trace for playback. If a POST investigation preflight is needed, invoke it explicitly with its actual method, body, fixture and isolated record-mode context; `/investigate` must not be placed in a path-only GET warm-up list. A retry must not update learning state, double-count metrics or execute actions. No prerecorded trace is presented as a fresh live endpoint result.

**Existing-cut corrections:** L-SOC retains its placement after E2 but uses the corrected SOC sequence in §9. L-DATAOPS retains its insertion locations and DD-0 banner; DO-2 is labeled a coverage/abstention preview until its policy exists. L-S2P retains the S14 insertion but uses a distinct receipt-first case and its corrected bridge. Optional L-VLD closes on the revised Room-16 answers; adding all four new beats requires a newly budgeted version, not the old four-minute label. ARCH-only cuts remain explicit architecture previews under the existing outreach rule.

## §9: Existing VLD Content Updates

### 9.1 Replace the shared §4.17 introduction

Replace the text from “All five share one new SDK surface and one API shape” through its Class bullet, leaving the individual beat headings below it, with:

> **All nine beats share an investigation trace contract.** The supplied update reports Q-based investigate endpoints, preseeds and offline experiments; it does not verify shipped production domain wiring or a deployed shared trace surface. The buyer panel displays evidence order, admitted records, changed assessment, unread evidence, consumed budget and halt reason. Internal views expose Q components and scorer quantities. Every planted preview carries PLANTED FIXTURE, ROADMAP and ROUTING ACCURACY: not yet measured for this deployment. A single-pass contrast uses exactly the same initial case, model and gate. Frozen learned state is read during the episode; only the append-only trace is written. All nine beats remain ARCH. Release requires the implementation and deployment evidence specified below.

This replaces stale absolute claims that no branch policy exists anywhere, no trajectory records exist, or only single-pass scoring runs. It also avoids treating reported experiments as proof that missing domain traversal is built.

### 9.2 Experiment interpretation to append after that introduction

| Copilot | Reported tensor | Routing change | Accuracy change | Starvation | Hurts |
|---|---|---:|---:|---:|---:|
| DataOps | 6×5×6 = 180 | +0.190 (+43% relative) | +0.320 | 8.3% | 0 |
| Purchasing | 5×4×7 = 140 | +0.210 (+41% relative) | +0.300 | 28.6% | 0 |
| Trading | 5×4×10 = 200 | +0.120 (+19% relative) | +0.140 | 48.0% | 0 |
| SOC | 6×4×6 = 144 | +0.120 (+17% relative) | +0.140 | 36.1% | 0 |
| S2P | 5×5×8 = 200 | +0.030 (+5% relative) | +0.060 | 22.5% | 0 |

These are the supplied K-learning results using production centroids in an offline experiment. For rate metrics, +0.120 is **+12 percentage points**, not +12% relative. “Hurts=0” is a reported experiment statistic whose unit and denominator were not provided; it is not proof that no future decision can be harmed. The non-starved 52% of Trading pairs is not “52% that works,” nor is starvation the fraction of trades left uninvestigated.

| Variant | Reported routing | Reported accuracy |
|---|---:|---:|
| Static | 57.8% | 73.6% |
| RNN | 56.3% | 77.6% |
| GRU | 48.8% | 69.2% |
| LSTM | 47.0% | 66.4% |

**Precise conclusion:** Static exceeded RNN routing by **1.5 percentage points**; RNN exceeded Static accuracy by **4.0 points** in the reported comparison. Neither universal Static superiority nor an adaptive-routing advantage follows. No sample sizes, uncertainty intervals or matched ablation details were supplied. This comparison must not be conflated with the Trading-specific greedy/bandit table, where 73.6% denotes **routing**, not Static accuracy.

The supplied Trading exploration comparison reports greedy starvation/routing **48% / 73.6%**, Thompson **0% / 53.0%**, UCB **0% / 65.0%**. Coverage improved while routing fell by **20.6** and **8.6** points respectively. The reported greedy K curve approaches a plateau around **500 decisions**, with the cited starvation series **19%→14% at 2,000**; its aggregation is unspecified and must not replace Trading's 48% figure. Continued data collection alone is not evidence of unbounded compounding under unchanged greedy selection.

Between-decision K learning (`REC-R2`) is the stronger supported design direction, but the table does not prove that an RNN is necessary to implement it. A static planner can in principle consume an updated K snapshot between decisions. Test that baseline before crediting the benefit to the recurrent architecture. Remaining priorities are legal K learning, evidence access, coverage and governance; route variant is an independently tested choice.

### 9.3 Existing beat audit and exact replacements

**VLD-SOC-1:** keep Surface and ARCH. Replace its Audience sees, Spoken and DoD/Honesty rows with the following:

| Field | Replacement |
|---|---|
| Audience sees | A planted mixed-indicator alert retains content-keyed `lateral_movement` dispatch. Q, computed over eligible evidence dimensions, selects the identity-related auth read first. That read admits the documented credential evidence and the actual scorer determines the action change. A linked campaign/pivot traversal is shown as a disclosed content-keyed subread or a separately budgeted read. Do not claim a second Q-selected lateral-movement check unless its own recorded Q selection exists. Display actual budget and halt. |
| Spoken | “In this planted alert, the retained score selected the auth check first. The record shows what came back and what changed the assessment. Any linked campaign lookup is labeled separately. This demonstrates the proposed order; it does not establish that adaptive routing beats a static plan.” |
| DoD / Honesty | Replace the 0.9-versus-0.3 dominant-factor rationale with logged Q components and the chosen dimension. The old 0.04/0.31 margins may appear only if actually reproduced. Resolve the old inconsistency between a one-read step list and a trace claiming two investigations. `conservation GREEN` appears only from the configured emit gate. SOC learning may remain off during frozen-state routing. |

Add optional engineering presenter note: “The supplied SOC experiment left 36.1% of category–dimension pairs without learning updates.” Do not imply that this alert's chosen dimension was starved without its per-pair counter.

**VLD-SOC-2:** retain Surface/API/Class, but replace its Audience sees, Spoken and DoD/Honesty rows:

| Field | Replacement |
|---|---|
| Audience sees | Case A, the main recovery scene: the auth query executes successfully over a documented window and returns a **verified negative finding**, admitted through a defined factor transform. Re-score, record Q for remaining eligible dimensions, then select the process-tree read if it wins. The process read finds the planted injection and the actual scorer determines the final action. Case B, the missing-evidence control: the auth source is unavailable/None, so no factor or action change is attributed to it; the next selection may follow candidate exclusion alone. Both attempts and failures remain visible. |
| Spoken | “The first check found no credential-reuse evidence in its covered window. After that finding was admitted, this replay selected the process check. The trace shows the change of direction. A static plan could select the same two checks; this case demonstrates a legible recovery, not a measured routing advantage.” |
| DoD / Honesty | Exactly two evidence attempts at B=2, with the final re-score numbered as a computation rather than a third read. Do not infer a flip from `None`, or say the halt controller chose the next branch. Re-score/Q select; halt logic decides whether to continue. Remove the claim that one wrong-first case proves ρ<½: a single failure does not estimate a routing rate. At full evidence budget, exhaustive retrieval could inspect the same evidence. |

The reported SOC model values and the negative-evidence transform are not supplied, so the action-flip trajectory remains a fixture acceptance condition. A fixed precomputed order may match it; compare the remaining-candidate ranking at S0 with that after admission before calling it adaptive rerouting.

**VLD-DO-1:** keep the surface and DD-0 classification. Replace its Audience sees, Spoken and DoD/Honesty rows:

| Field | Replacement |
|---|---|
| Audience sees | A planted billing_api case has competing schema-change and upstream-failure hypotheses. Bind those hypotheses to the actual DataOps factor/action schema; do not assume their names are action centroids. Log Q for the eligible evidence dimensions and the adapter that maps the winner to schema-history retrieval. Admit the MATKL_V2 record, re-score and halt according to policy. The downstream lineage expansion to three systems is visibly CONTENT-KEYED / PREREQUISITE and separately costed. |
| Spoken | “This planted replay selected schema history first, and that read found the migration. The downstream lineage view shows the affected systems. The trace separates the scorer-selected check from the ordinary lineage lookup.” |
| DoD / Honesty | Retained-state provenance replaces unsupported pipeline-specific learning claims. Factor-level weights do not automatically rank systems: either specify and validate a factor-to-system impact aggregation, or show affected systems without a learned ranking. The result recommends a fix; the VLD trace does not execute ERP write-back. Decision→Pipeline attachment and as-of evidence remain required. |

Technical note: DataOps' reported K gains are the largest in this five-copilot table, but DD-0 and the production wiring gates remain. Its 8.3% starvation figure belongs in the coverage view, not in a claim that every source is learned.

**VLD-DO-2:** replace subtitle “centroid distance as the routing signal” with **“coverage-aware investigation and abstention — policy extension”**. Replace its API, Audience sees, Spoken and DoD/Honesty rows:

| Field | Replacement |
|---|---|
| API | `POST /api/dataops/investigate`; Q ranks available dimensions. A separate proposed coverage/abstention controller must be specified if the scene dispatches a broad-read bundle. |
| Audience sees | Two planted cases contrast a supported history match with sparse or conflicting support. Q selects eligible dimensions; a broad-read fallback, if built, is labeled as a separate controller action and charged for its underlying reads. If the resulting support is insufficient, emit the actual review/referral action. Show “similar resolved cases: none” only from a query with a stated similarity criterion, window and cutoff. |
| Spoken | “The stored cases gave limited support for this combination. This architecture preview shows the additional checks and the point where it would refer the case for review. The broader-read policy needs its own implementation and evaluation.” |
| DoD / Honesty | Retire hand-pinned 0.62/0.93 values and the claim that low softmax margin itself implements broad-vs-deep routing in the supplied Q equation. A softmax score is not automatically calibrated confidence, and a large top-two margin does not establish proximity to known data. Define absolute support/distance, match criteria and calibration separately. No claim that a “new cause” or absence of precedent follows from margin alone. |

This scene stays in the catalog as an explicitly broader ARCH design. It must not be staged as evidence that the currently described Q mechanism already provides novelty detection or broad-read dispatch.

**VLD-S2P-1:** keep Surface/Class, update the API row to describe the **S2P Context Builder / Traversal Context** and required as-of supplier matcher; no native graph traversal claim without runtime query evidence. Replace Audience sees, Spoken and DoD/Honesty:

| Field | Replacement |
|---|---|
| Audience sees | A separate planted Supplier Aster dual-mismatch case starts with both price and quantity questions unresolved. Pre-cutoff verified history provides a derived prior, proposed fixture counts 31 partial-delivery and 10 pricing-error cases (3.1× within that defined cohort). Record how that prior enters the scored state or learned snapshot. Q must then independently select the evidence dimension mapped to the goods receipt. Receipt evidence is admitted; the actual action enum and halt are computed. No uncounted contract read occurs first. |
| Spoken | “In this planted case, the supplier history was an input to the score, and the score selected the receipt first. That receipt resolved the mismatch in this fixture. The comparator shown here is our declared contract-first baseline; a receipt-first static plan could make the same selection.” |
| DoD / Honesty | History ratio, Q order and resulting action must all be replayed. A 3.1× ratio alone neither proves Q priority nor the correct action. `partial_delivery` may be a cause label; `accept-with-adjustment` must be validated against the actual action enum, not invented as an API result. Invoice adjustment is not automatic execution. Include the cost of history acquisition and prerequisites. “One fewer read” is allowed only when observed against a named internal baseline with the same initial information and stopping rule; never generalized to all rule engines. |

Replace the entire VLD-S2P-1↔S14 integration-note paragraph with:

> “The S14 case showed a contract-aware assessment. Now this separate dual-mismatch case starts before either mismatch document has been checked. Its retained score selects the receipt first. The history lookup is a labeled prerequisite, and the trace records the selected evidence order.” Preserve S2P-FIX-1's scoped comparison with the displayed threshold baseline. Retire the additive claim that rules cannot read contracts or know which document to request second.

The supplied S2P routing gain is +0.030, the smallest in this comparison; that is a reason for measured positioning, not an invented explanation of diminishing returns. Supplier-specific conditional state, action mappings and query cutoffs remain to be verified.

**Adjacent S14 surgical correction:** in §4.2.1 replace the “killer detail” quote and the repeated “Rules don't read contracts” payoff with: “The displayed threshold-only baseline rejected this fixture. The contract-aware assessment used additional evidence and reached a different result.” Retain applicable computed fixture provenance. Do not carry S14's time or dollar examples into the VLD order strip. This correction scopes the specific comparator without rebuilding the non-VLD S14 beat.

### 9.4 Replace the VLD silence paragraph in §2.5

The existing VLD passage has no SILENCE 7 heading. Replace the text beginning “After you say ‘Today it says go look…’” through “Honesty during the silence” with:

> **SILENCE 7: The Investigation Order (VLD-SOC-1; recovery variant VLD-SOC-2).** Say: “Here is a planted preview of the investigation order.” Reveal the persisted trace if available; otherwise identify it as a storyboard. Pause for five seconds when the selected auth check and its admitted evidence appear. For SOC-2, pause on the successfully queried negative result and subsequent process check; unavailable evidence uses the distinct missing-source control. Resume: “The record shows what was selected, what came back and why the next selection was eligible.” Do not say a rule always reads both or that a changed direction proves better routing. Keep PLANTED FIXTURE, ROADMAP and the deployment routing-accuracy badge visible throughout. If asked about the numbers: “These are fixture values. The offline results are separate, and deployment routing accuracy has not been established.”

Append SILENCE 8–11 from §§1–4 here by reference, preserving their IDs. Replace “The three silence beats” with “Silence beats”; the source has accumulated more than three.

### 9.5 K reachability, recurrence and claim-status audit

| Beat | Can the K-dependent claim currently be certified? | Required correction |
|---|---|---|
| SOC-1 | **No.** 0.9/0.3 are described as factor weights, not authenticated K checkpoints; full Q absent. | Compute/log complete Q. A dominant input is not automatically the selected dimension. |
| SOC-2 | **No.** No post-admission vector, legal K or remaining-candidate ranking supplied. | Distinguish admitted negative evidence from None; verify reranking rather than narrating it. |
| DO-1 | **No.** No complete factor/action map, pipeline-conditioned state or Q trace supplied. | Ground adapter selection and retained-state attribution. |
| DO-2 | **Not a K reachability question yet.** The proposed broad/deep controller is absent from the given formula. | Specify that separate policy before claiming the behavior. |
| S2P-1 | **No.** A supplier ratio does not specify K or Q. | Trace history→state→Q→receipt; enforce historical cutoff. |
| TRD-1 / TRD-2 | **No new K story certified.** Reported routes are regression targets; expanded evidence and options contrast are proposed. | Produce legal snapshot/eligibility manifests; distinguish policy selection from manual replay. |
| PUR-1 / PUR-2 | **No new K story certified.** Provider gaps precede the ranking question. | Build missing providers, then replay actual Q and action transitions. |

An unreachable or absent K snapshot blocks the claim, not the entire design document. The record must include update rule, initialization, bounds/clipping, category indexing, verified support and checkpoint hash. Unit K does not by itself mean an untrained scorer: μ/σ can already carry learned information. Likewise, an adaptive loop with frozen K can still recompute Q as v changes; frozen learning state is not a frozen case state.

**Taxonomy replacement for any new terminology note:** `REC-R0 static baseline; REC-R1 within-decision; REC-R2 between-decision K learning; REC-R3 cross-episode; REC-R4 cross-copilot; REC-R5 temporal`. Existing “R3 Ψ”, “R4 shadow-run”, “R5 analyst measurement” and “R1 audit” references become `BUILD-R3`, `BUILD-R4`, `BUILD-R5` and `BUILD-R1` locally to avoid collisions. The prompt does not operationally distinguish R2 from R3; do not assign a shipped cross-episode mechanism from its name. RGI's architectural L5 exclusion is unrelated to a temporal recurrence level labeled R5. Cross-copilot signals are not shared cross-copilot judgment geometry.

### 9.6 Replace all ten VLD-GUARD paragraphs in §4.18

1. **GUARD-1 — Class:** all nine beats ARCH. NEAR requires `BUILD-R3` Ψ prototype, E-1 trajectory persistence, surfaced trace and beat-specific provider/entity/cutoff work. Retain the original LIVE gate: `BUILD-R4` shadow-run must show **Δ_depth > 0 against the declared rule-based routing baseline on real cases**; an offline benchmark does not satisfy it. Extend the matched study to include **static planning on the same learned substrate**, adaptive Q, single-pass and full retrieval where affordable. Predefine the Δ_depth measure, primary task-quality/cost measure, budget and uncertainty assessment. Do not promote an “adaptive is better” claim if the static comparator matches or wins.
2. **GUARD-2 — Language:** VLD is investigation, trace, route, re-score, admit and halt. No reasoning/thinking/deliberating language or RL label for its primary mechanism. Use RGI for CI's named mechanism; RSI only as the field reference. Customer microcopy avoids “self” for CI's mechanism.
3. **GUARD-3 — Provenance/status:** PLANTED FIXTURE, ROADMAP and ROUTING ACCURACY: not yet measured for this deployment remain visible. Reported offline experiments are explicitly separate from fixture computation and production readiness. Retire stale assertions of universal branch-policy or trace-record nonexistence; state verified status per component.
4. **GUARD-4 — Attribution:** category dispatch, entity resolution, supplier/portfolio/lineage walks and evidence-directed expansions are CONTENT-KEYED / PREREQUISITE unless their own Q-selected step is demonstrated. Manual comparisons are NOT POLICY-SELECTED. Count their costs.
5. **GUARD-5 — Value/time:** no VLD time-savings figures. Analyst benefit is a pilot question. Editorial video durations and instrumented API latency are clearly distinguished from analyst-time savings.
6. **GUARD-6 — Learning:** no “next time it routes better.” Freeze learned state within a beat. Between-decision K learning requires its actual verified-outcome update path; it does not inherently require AgentEvolver to evolve routing parameters. The AE→routing path is a separate ARCH claim. Zero-support pairs and the reported greedy plateau limit the compounding story.
7. **GUARD-7 — Budget:** display attempted, admitted and unvisited reads plus halt reason. If all eligible evidence fits, acknowledge that full retrieval can inspect it too. No accuracy or speed advantage inferred from a chosen order alone. No hidden third read, free bundle, or rerun outside the labeled budget.
8. **GUARD-8 — Numbers:** all scene values are computed from and linked to labeled planted data. Proposed numbers are acceptance inputs until replayed. Experiment results carry experiment provenance; do not call them fixture outputs. No measured customer ROI, unsupported confidence calibration, or literal fake node count.
9. **GUARD-9 — Buyer language:** no centroid/DK/σ/v_t/margin or raw Q equation on buyer panels. Show check order, supporting records, changed assessment, unresolved checks and halt. Internal views retain full quantities. Do not relabel a raw margin as calibrated confidence.
10. **GUARD-10 — Competition:** no competitor API/product execution or named performance claim. Describe the internal baseline exactly; avoid universal statements about what other agents, graphs, rule engines or retrieval systems cannot do.

**Implementation truth versus efficacy:** a working endpoint may be recorded as implemented while its benefit remains unvalidated. Retain the document's conservative ARCH/NEAR/LIVE release policy, but track `implementation status` and `comparative evidence status` separately so a failed superiority test is not confused with nonexistent functionality.

### 9.7 Document-control edits

- Change the source title to **Demo Scenarios & Use Cases — Consolidated · v2.9**, version to **2.9**, and update date to **September 13, 2026** when this delta is actually merged.
- Replace its “New in v2.8” line with: “**New in v2.9:** four Trading/Purchasing VLD beats; nine total ARCH investigation beats; domain wiring and preseed contracts; Room-16 and Loom extensions; Q, starvation, missing-evidence, experiment and terminology corrections.”
- Rename `## §4.18 v2.8 Fixer — Standing Guards and RL-Loop Class Precondition` to `## §4.18 Standing Guards and Learning-Loop Class Preconditions (v2.9)`. Rename its `FIX-7 — RL-loop precondition` heading to `FIX-7 — Learning-loop precondition`. Preserve the existing table's status until actual end-to-end evidence updates it; the supplied offline experiments alone do not close those gates.
- Update the italic provenance paragraph following §5 VLD preseeds to cite the two supplied documents, retain older companion filenames as unverified references, and say “all nine beats” and “deployment routing accuracy.” Do not present unread companion documents as reviewed authorities.
- Append this row to Document Control: `v2.9 | September 13, 2026 | Added VLD-TRD-1/2 and VLD-PUR-1/2; reconciled canonical factor/provider maps and seed aliases; added temporal/entity wiring, Loom and Room-16 deltas; corrected all existing VLD scripts for Q selection, missing evidence, budget accounting, reported static/RNN results, starvation, RGI terminology and deployment-truth guards.`

## §10: VLD Guard Compliance Checklist

**PASS below means the proposed written beat obeys the guard. It does not certify runtime behavior.** All four remain ARCH; runtime status is **NOT VERIFIED**. Shared guards in §9.6 are part of each beat's specification.

| Beat | Guard | Pass/fail | Note |
|---|---|---|---|
| VLD-TRD-1 | 1 · ARCH | PASS | Entity/correlation/cutoff wiring and replay remain gated. |
| VLD-TRD-1 | 2 · Language | PASS | Historical investigation/assessment vocabulary. |
| VLD-TRD-1 | 3 · Fixture/status | PASS | Standing fixture, roadmap and deployment-accuracy badges. |
| VLD-TRD-1 | 4 · Attribution | PASS | Q selects dimension; portfolio expansion is content-keyed. |
| VLD-TRD-1 | 5 · Time/value | PASS | No analyst-time, profit or risk-reduction claim. |
| VLD-TRD-1 | 6 · Learning | PASS | Frozen snapshot; paired order change is a test target. |
| VLD-TRD-1 | 7 · Budget | PASS | Counts all reads; full-retrieval caveat where applicable. |
| VLD-TRD-1 | 8 · Numbers | PASS | Three positions/correlations are planted; scores must compute. |
| VLD-TRD-1 | 9 · Buyer language | PASS | Plain exposure/check labels; raw Q in internal audit only. |
| VLD-TRD-1 | 10 · Competition | PASS | Internal comparisons only. |
| VLD-TRD-2 | 1 · ARCH | PASS | Missing timing/options providers are explicit. |
| VLD-TRD-2 | 2 · Language | PASS | Coverage gap and manual evidence replay. |
| VLD-TRD-2 | 3 · Fixture/status | PASS | Diagnostic and offline statistic have separate provenance. |
| VLD-TRD-2 | 4 · Attribution | PASS | Manual IV admission is NOT POLICY-SELECTED. |
| VLD-TRD-2 | 5 · Time/value | PASS | No trading outcome or saved-time claim. |
| VLD-TRD-2 | 6 · Learning | PASS | No automatic starvation cure or guaranteed next-case improvement. |
| VLD-TRD-2 | 7 · Budget | PASS | Legacy failed attempt visible; diagnostic is a new episode. |
| VLD-TRD-2 | 8 · Numbers | PASS | 48%=24/50 is reported update coverage, not failed trades. |
| VLD-TRD-2 | 9 · Buyer language | PASS | “Unavailable” and “not queried” stay distinct. |
| VLD-TRD-2 | 10 · Competition | PASS | No external performance comparison. |
| VLD-PUR-1 | 1 · ARCH | PASS | Event provider and historical order linkage are build items. |
| VLD-PUR-1 | 2 · Language | PASS | Evidence/check/order-assessment vocabulary. |
| VLD-PUR-1 | 3 · Fixture/status | PASS | Planted event, shelf life and roadmap clearly marked. |
| VLD-PUR-1 | 4 · Attribution | PASS | Event availability does not hardcode waste as the next check. |
| VLD-PUR-1 | 5 · Time/value | PASS | No spoilage savings or manager ramp-time claim. |
| VLD-PUR-1 | 6 · Learning | PASS | Retained snapshot; category contrast is illustrative. |
| VLD-PUR-1 | 7 · Budget | PASS | Two request attempts; no uncounted replacement order work. |
| VLD-PUR-1 | 8 · Numbers | PASS | Covers and expiry inputs synthetic; final action must replay. |
| VLD-PUR-1 | 9 · Buyer language | PASS | Usable stock, event and delivery labels. |
| VLD-PUR-1 | 10 · Competition | PASS | Acknowledges an ordering rule can inspect the same evidence. |
| VLD-PUR-2 | 1 · ARCH | PASS | Lead-time provider and supply-chain links remain required. |
| VLD-PUR-2 | 2 · Language | PASS | Retention and delivery evidence vocabulary. |
| VLD-PUR-2 | 3 · Fixture/status | PASS | Prior-manager history and proposed diagnostic labeled. |
| VLD-PUR-2 | 4 · Attribution | PASS | Alternative-supplier lookup content-keyed; price card manual. |
| VLD-PUR-2 | 5 · Time/value | PASS | No reduced onboarding time or prevented-loss figure. |
| VLD-PUR-2 | 6 · Learning | PASS | Continuity verifies retained state, not automatic future benefit. |
| VLD-PUR-2 | 7 · Budget | PASS | Supplier lookup outside the two-read trace separately costed. |
| VLD-PUR-2 | 8 · Numbers | PASS | 17/50=0.34 is an explicit synthetic delivery statistic. |
| VLD-PUR-2 | 9 · Buyer language | PASS | Delivery cutoff, assessment and source records. |
| VLD-PUR-2 | 10 · Competition | PASS | No named competitor or exclusivity assertion. |

**Before staging any computed beat, the acceptance record must show:** the actual route and flip step; immutable model-state comparison; complete provider/cutoff provenance; candidate and read-cost accounting; successful missing-evidence and budget-zero controls; actual halt and emit behavior; visible badges; and a script that matches the persisted trace. A manual or storyboard example remains labeled as such. Passing the authoring checklist does not satisfy these runtime gates.
