# Demo Scenarios Catalog — v5

**What this is.** The over-arching library of demo scenarios to choose from when scripting Loom demos. Not
Loom scripts, not pre-assembled shows — a tagged catalog. Each scenario is a self-contained unit: a story
(named person + company + stakes + two-beat turn + gut-punch), the shipped surface it runs on, its class,
the claim a Playwright test would assert, rough duration, and the rooms/messages it serves. Downstream:
scenarios → PW tests (validate) → MAP addendum (plant/build the gaps) → Loom scripts (mix, match, select).

**How to read a scenario.**
- **Class** — `LIVE` (renders on the pinned preseed today) · `PLANT` (endpoint exists, data must be seeded)
  · `BUILD` (needs code first) · `ROADMAP` (mockup, future value, told in future tense) · `EXPERIMENT`
  (a measured result shown as a caption, not a live metric).
- **PW-claim** — what a Playwright/API test asserts renders, so step 2 is mechanical.
- **Rooms** — VC · CISO · CFO · CPO · COO · CDO · PM/risk · CTO · audit · dev.
- **Two-beat turn** — (setup silence: what's on screen before) → (reveal: what changes). The flash lives here.

**Honesty riders (every scenario).** Numbers are illustrative-from-preseed unless tagged MEASURED/EXPERIMENT;
roadmap is future tense and labeled; the decision is centroid-distance, never "RL"; *signals* transfer,
judgment is per-copilot; planted data carries a `sample`/planted marker and never appears in a headline
metric. Magnitude on live decisions is always pilot-only.

**The cast (reuse for coherence; new firms welcome for range).** Sarah Chen (SOC Lead, Meridian Health) ·
David Okoye (AP Mgr, Halden Manufacturing) · Marta Ruiz (GM, Brightline Hospitality, $600M multi-concept food-service) · Marcus Bell (PM,
Kesler Capital) · Priya Rao (Head of Data, Northwind Logistics). Extended cast for segment range: a
hospital-payer, a bank, a retailer, an insurer, a mid-market SaaS — introduced where noted.

**Validation tiers carried from the API check (2026-09-17):** LIVE now = evidence ledger, compounding curve,
RSI rejection. PLANT = policy-conflict, cross-graph query, gate-band transition, checkpoint rollback,
frozen-twin init. BUILD = switching-cost endpoint (404). SOC on port 8001; routes corrected:
`/api/soc/graph/prebuilt-queries`, `/api/soc/checkpoint/list`, `/api/learning/frozen-twin`.

---
# SOC — Meridian Health (Sarah Chen, SOC Lead)

### SOC-01 · "The Analyst Who Gave Notice" · LIVE · ~2:30 · rooms: CISO, CFO, VC
- **Stakes:** Sarah's best analyst, Tom, quit Friday. Twelve years of "this pattern is nothing, that one is a breach" walks out with him; the next hire relearns it on live alerts.
- **Turn:** *(setup)* the learning-state panel for a normal system — what Tom knew, about to vanish, blank. *(reveal)* Tom's 847 verified escalation decisions are already in the geometry — the centroid support and per-category weights his calls shaped, still here Monday.
- **Gut-punch:** "When your best analyst leaves, a bundled copilot loses what they knew. This kept it — Tom's judgment is still triaging alerts, and he doesn't work here anymore."
- **Dollar:** analyst $95K/yr loaded; ~14 months for a hire to replicate at Meridian's volume ≈ **$111K ramp saved** (ILLUSTRATIVE).
- **Surface:** Executive Narrative / Compounding → ContinuityPanel; `/api/soc/centroid-support`, `/api/soc/learning-state`. **PW-claim:** learning-state renders verified-decision count > 0 and per-category weights non-empty after preseed.
- **Silence:** on the retained-judgment figure.

### SOC-02 · "The Alert With No Precedent" · LIVE · ~2:30 · rooms: CISO, VC, CTO
- **Stakes:** 2 a.m., a privileged service identity issuing bulk device-management commands — MFA clean, device clean, nothing like it in the history. A retrieval tool is blindest exactly here.
- **Turn:** *(setup)* the "similar past cases" sidebar renders — empty, nothing; hold 3s. *(reveal)* the score resolves and ESCALATE-high-confidence appears beside the emptiness — it acted without a precedent.
- **Gut-punch:** "A retrieval system recalls. This one reasons — so it catches the thing that never happened, and tells you it's new instead of pretending it's routine."
- **Surface:** Alert Triage → NoPrecedentSidebar, DiscoveryBanner, ScoreResultCard; `POST /api/alert/analyze`. **PW-claim:** for the planted no-precedent alert, sidebar shows "similar cases: none" AND action=ESCALATE with confidence rendered.
- **Class note:** the escalate is LIVE; the specific no-precedent alert is planted (see MAP list). Silence: after ESCALATE lands beside empty.

### SOC-03 · "It Rejected 35 of Its Own Ideas" · LIVE · ~2:30 · rooms: CISO, VC, audit · [RSI]
- **Stakes:** "What if the AI learns the wrong thing?" — the objection that kills the deal.
- **Turn:** *(setup)* "47 tested" on the Runtime Evolution tab. *(reveal)* "12 promoted / **35 rejected**" — 18 failed correctness, 11 failed conservation, 6 failed variance; each rejection has a reason and an audit row.
- **Gut-punch:** "It has a higher bar for itself than you have for your vendors — it rejected 74% of its own ideas and shows you why each failed. It's not that it learns; it's that it stops when it shouldn't."
- **Caption (EXPERIMENT):** a naive "better-than-production" gate at a 10-decision window: 59% power / 44% false-promote. This gate: z-test, 1,000-decision window → 80.6% power / 4.9% false-promote (GATE-STAT).
- **Surface:** Runtime Evolution → PromotionDashboard, RejectionMomentPanel; `/api/evolution/recent-events`. **PW-claim:** promoted + rejected counts render with per-rejection reasons.

### SOC-04 · "It Paused Itself" · PLANT · ~2:00 · rooms: CISO, risk · [RSI]
- **Stakes:** the deepest fear isn't a wrong call — it's a wrong call made silently at scale.
- **Turn:** *(setup)* the learning-health band sits GREEN while the queue flows. *(reveal)* fire simulate_failure — recent verified accuracy drops, the band slides GREEN→AMBER→RED, auto-pause flips on, alerts route to humans. It stopped itself.
- **Gut-punch:** "A script can't say 'not yet.' This did — the moment its own record said it shouldn't be trusted."
- **Surface:** Compounding → learning-health band, failure-sim trigger; `/api/soc/learning-health`, `/api/eval/simulate-failure`. **PW-claim:** health status transitions GREEN→AMBER/RED and auto_pause_active flips true on simulate_failure. **Plant:** a reproducible-on-demand transition (not a static AMBER).
- **Note:** the band (GREEN/AMBER/RED) is the shipped model — the motion is the beat.

### SOC-05 · "Two Alerts, Separately Nothing" · ROADMAP · ~3:00 · rooms: CISO, CTO, VC
- **Stakes:** two green low-severity alerts — a privileged account updated an Intune policy (routine); the same credential surfaced in a leak-forum toolkit (low severity). Neither alone clears any threshold.
- **Turn:** *(setup)* both auto-closing, green. *(reveal)* cross-graph attention connects identity × threat-intel × device-management: "the leaked credential is the same identity that just pushed policy to 40 endpoints — separately routine, together lateral movement." Escalated with the cross-graph path shown.
- **Gut-punch:** "No SIEM queried this, no rule fires, no RAG retrieves it — the question was never asked. The graph attended one domain to another. That's discovery, not retrieval."
- **Surface:** Alert Triage → DiscoveryBanner + cross-graph; `/api/discoveries`. **PW-claim (when built):** discovery renders linking ≥2 domains. Told future tense, "architecture preview," planted fixture.

### SOC-06 · "The AI Said Auto-Close. Policy Said Escalate. Policy Wins." · PLANT · ~2:00 · rooms: CISO, audit
- **Stakes:** a CISO's non-negotiable — the AI must never override a hard policy, and every conflict must be defensible.
- **Turn:** *(setup)* the AI recommends auto-close, high confidence. *(reveal)* a policy-conflict banner fires: this asset class requires human escalation regardless of AI confidence → action is overridden to ESCALATE, logged with the rule cited.
- **Gut-punch:** "The system is confident and it still defers to your policy — and writes down exactly why. That's the difference between automation and governance."
- **Surface:** Alert Triage → policy-conflict banner; `/api/alert/policy-check`, `/api/alert/policy-history`. **PW-claim:** for the planted conflict alert, policy-check returns a conflict and the resolution shows policy overriding AI. **Plant:** an alert where policy overrides the AI recommendation.

### SOC-07 · "Every Decision, Chained" · LIVE · ~2:00 · rooms: CISO, audit, CTO
- **Stakes:** the model-risk reviewer was promised "explainable AI" by four vendors and got SHAP plots.
- **Turn:** *(setup)* the evidence room — a list of decisions. *(reveal)* each carries a SHA-256 chain hash; run verify → "chain intact, no records reordered or tampered"; export the CSV.
- **Gut-punch:** "This isn't an explanation of the model. It's a tamper-evident record of every decision it made — and your auditor can verify it themselves."
- **Surface:** Governance Evidence → evidence room; `/api/audit/verify`, `/api/audit/decisions?format=csv`. **PW-claim:** verify returns verified=true; CSV downloads with a hash column. LIVE now.

### SOC-08 · "The Baseline We Froze in January" · PLANT · ~2:30 · rooms: CISO, VC
- **Stakes:** "prove it's getting better, not just different."
- **Turn:** *(setup)* one curve. *(reveal)* a frozen twin pinned at January's geometry beside the live system; the live one pulls away — the gap is the compounding, measured on Meridian's own alerts.
- **Gut-punch:** "The distance between those lines is the thing no vendor can fake — measured on your alerts, and every decision widens it."
- **Surface:** Performance → FrozenTwinComparisonPanel; `/api/learning/frozen-twin`. **PW-claim:** two series render (live vs frozen) with a positive gap. **Plant:** initialize the frozen-twin comparison. Divergence labeled MODELED/PILOT-TARGET.

### SOC-09 · "Same Alert, Two Shifts" · LIVE · ~1:30 · rooms: CISO
- **Stakes:** triage quality tracks who's on shift and how tired they are — the audit says so.
- **Turn:** *(setup)* the same planted alert at 02:00. *(reveal)* the same alert at 14:00 — identical recommendation, identical six factor contributions, side by side.
- **Gut-punch:** "A rule is consistent too — but it never learned that consistency from your decisions. This did, and it can show you the verified decision that shaped it."
- **Surface:** Alert Triage → ScoreResultCard (deterministic); `POST /api/alert/analyze`. **PW-claim:** the same alert scored twice returns identical action + factor contributions.

### SOC-10 · "Roll It Back" · PLANT · ~2:00 · rooms: audit, risk, CTO
- **Stakes:** a verified decision turns out to have been mis-verified. A fine-tuned model can't un-learn one example.
- **Turn:** *(setup)* the checkpoint timeline. *(reveal)* create checkpoint → verify → roll back one step; the geometry restores; a bad restore returns a checksum error (409).
- **Gut-punch:** "Provenance tells you which document a fact came from. This tells you which verified decision moved the judgment — and lets you undo that one."
- **Surface:** checkpoint timeline; `/api/soc/checkpoint/rollback`, `/api/soc/restore-centroid`. **PW-claim:** rollback restores prior state; bad restore → 409. **Plant:** a checkpoint+verify+rollback sequence in the preseed.

# S2P — Halden Manufacturing (David Okoye, AP Manager)

### S2P-01 · "The Rule That Kept Saying No" · LIVE · ~2:30 · rooms: CFO, CPO, VC
- **Stakes:** David's threshold rule kicked a 5.2%-over-PO invoice to manual review — the 47th this quarter. But copper rose 4.8% and the contract allows pass-through; the rule is wrong, and each wrong rejection is a supplier paid late.
- **Turn:** *(setup)* the LEFT column resolves — the rule: "5.2% > 5.0% → REJECT, route to manual"; hold 3s, the room sees David's every day. *(reveal)* the RIGHT column fills line by line: "copper +4.8% (30d); contract §7.3 allows pass-through to 110%; 5.2% ≤ 5.28% → ACCEPT, 0.91," citing the clause.
- **Gut-punch:** "A rule fires on a number. Judgment reasons about why — and David stops paying good suppliers late."
- **Surface:** Exception Triage → RuleVsReasoningPanel, SituationPanel; `POST /api/s2p/score`. **PW-claim:** for the invoice fixture, rule-column=REJECT and reasoning-column=ACCEPT with the contract clause cited.

### S2P-02 · "Before David's First Invoice" · LIVE · ~2:00 · rooms: CFO, CPO, VC · [day-zero]
- **Stakes:** every competitor says "give us your data and six months." David's CFO gave him 30 days.
- **Turn:** *(setup)* a cold system, zero decisions. *(reveal)* it triages its first invoice on compiled expert geometry — 90.6% accuracy, zero training labels; caption: full-feature RF (400 labels) 72.0% / budget-matched RF 39.2% / VLD (0 labels, 2 reads) 37.8%.
- **Gut-punch:** "Most vendors need six months of your data. This was useful before David's first invoice arrived — the compounding starts with the first verified decision."
- **Surface:** Exception Triage → ScoreResultCard; `POST /api/s2p/score`. **PW-claim:** first-decision score renders with a confidence and zero prior decisions. Caption EXPERIMENT (geometry-derived; SOC fixture for the RF comparison).

### S2P-03 · "When Paying More Is the Right Call" · PLANT · ~2:00 · rooms: CFO, COO
- **Stakes:** a container stuck at port, demurrage $1,200/day; the optimization tool says "clear it now." But it's slow-moving stock and the warehouse already holds $2.3M of slow-movers.
- **Turn:** *(setup)* the optimizer's answer: clear immediately. *(reveal)* situation analysis reads the manifest against inventory + markdown history + working capital: "hold 3 days, demurrage $3,600; clearing costs $14,200 in carry + markdown; net save $10,600."
- **Gut-punch:** "Every optimization tool would have cleared that container — they optimize a number. This reasons about a situation, and sometimes the right answer is to pay more."
- **Surface:** Exception Triage → SituationPanel, CounterfactualCard; `POST /api/s2p/score`. **PW-claim:** the fixture returns HOLD with the working-capital reasoning. **Plant:** the container/inventory context.

### S2P-04 · "Earned Autonomy, Week Over Week" · LIVE · ~2:30 · rooms: CFO, audit · [RSI]
- **Stakes:** David's CFO: "how much can we auto-approve, and how do you know it's safe?" One bad auto-approval is a write-off.
- **Turn:** *(setup)* the conservation ledger at week 1: 5% auto, cold-start. *(reveal)* week 4: 23% (200 verified, 89%, GREEN); week 8: 41% (450 verified, 91%, GREEN) — each step earned, the 20:1 asymmetric ratio enforced by the gate.
- **Gut-punch:** "David tells his CFO: 41% auto-approved, here's the proof — 450 decisions, 91%, GREEN eight weeks, and it pauses itself if accuracy drops. No vendor can show that ledger."
- **Dollar:** 41% at 91% = 194 invoices untouched; ~71 analyst-hours ≈ **$2,840** + suppliers paid 9 days faster (ILLUSTRATIVE).
- **Surface:** Performance → S2PConservationProjection, AuthorityPanel; `/api/conservation/status`. **PW-claim:** ledger renders week-over-week auto-approve % with accuracy and GREEN status (needs preseed).

### S2P-05 · "The Queue That Shrank" · PLANT · ~2:00 · rooms: CFO, CPO
- **Stakes:** every competitor promises "faster processing" — the queue stays the same size. David's is shrinking.
- **Turn:** *(setup)* January: 847 exceptions. *(reveal)* the extinction timeline: "price variance <3% on commodity-indexed POs: 200 in Jan → 0 in April — auto-approved after 150 verified decisions proved the class safe, conservation GREEN throughout." Now: 312.
- **Gut-punch:** "Decision ten-thousand isn't handled like decision one. It stopped asking about the 535 David always approves — and can name each class it retired and the decision that earned it."
- **Surface:** Evidence → ExceptionExtinctionTimeline, RuleLifecyclePanel; `/api/s2p/compliance/report`. **PW-claim:** extinction timeline shows a class going N→0 with the earning decision. **Plant:** the extinction history.

### S2P-06 · "The Rule It Kept Manual" · PLANT · ~1:30 · rooms: CFO, audit
- **Stakes:** the counter-case to S2P-05 — does it retire rules recklessly?
- **Turn:** *(setup)* a class it evaluated for auto-approval. *(reveal)* it stayed manual — accuracy never cleared the bar; the panel shows the attempts and the reason it was kept human.
- **Gut-punch:** "It retires the rules it earned and keeps the ones it didn't — and names both. Restraint you can audit."
- **Surface:** Evidence → RuleLifecyclePanel; `/api/s2p/compliance/report`. **PW-claim:** a rule renders in a "kept-manual" state with the failed-bar reason. **Plant:** the counter-case.

### S2P-07 · "Spend One Read on Easy, Three on Hard" · ROADMAP · ~2:00 · rooms: CFO, CTO
- **Stakes:** every system investigates every invoice the same amount — easy ones waste time, hard ones get too little.
- **Turn:** *(setup)* a $900 utility bill and a $38K contested capex invoice both show "2 reads." *(reveal)* the controller re-budgets: utility → 1 read, resolved; capex → 3 reads, and the third (a change-order clause) flips the decision. Caption: +6.8 pts quality at 1.43 reads vs 2.0, 0% false pauses, 100% poison (RL-CTRL-2C).
- **Gut-punch:** "Effort finally follows stakes — and the safety gate never moved. The RL sets the budget; it never touches the decision."
- **Surface:** Exception Triage → InvestigationTracePanel (budget strip); **BUILD/ROADMAP** — controller measured, not in the production path. Future tense. **PW-claim (when built):** budget strip shows differing read counts per invoice. Honesty: two copilots, in-distribution.

### S2P-08 · "The $50K Needs More Confidence Than the $500" · PLANT · ~2:30 · rooms: CFO, CISO, audit
- **Stakes:** three people in one room — CFO wants throughput, security wants a floor, audit wants a defensible record. Every vendor answers one.
- **Turn:** *(setup)* an invoice with a confidence band (delta_1 + post-investigation margin). *(reveal)* the dollar rule: $500 auto at 0.70; $50K needs 0.90; at 0.80 threshold, 67% auto-acted at 99.2%. Each role sees its number on one screen.
- **Gut-punch:** "One confidence signal, three owners. Finance sets the dollars, security sets the floor, audit gets a number per decision. Nobody had to lose."
- **Surface:** Performance → ConfidenceBandPanel, AuthorityPanel; `/api/s2p/preview/conservation`. **PW-claim:** confidence band renders per invoice; dollar-threshold routing shows different bars. **Plant/BUILD:** band exists; dollar-threshold slider to build. Honesty: AUC 0.875 S2P (geometry-derived), per-copilot ECE up to 0.082 → recalibrate before absolute thresholds. K14 cross-ref: S2P has the highest surface-label noise of any copilot (92%); confidence thresholds require geometry-derived calibration, not surface-label calibration — at this noise rate, compounding reverses (K14 Part 2).

### S2P-09 · "The Version We Froze in March" · PLANT · ~2:00 · rooms: CFO, VC
- **Stakes:** "how do I know the improvement is real and not a story?"
- **Turn:** *(setup)* one performance curve. *(reveal)* a twin pinned at day-one config; the live system pulls away on Halden's own invoices; the gap is the compounding.
- **Gut-punch:** "The distance between those two lines is the thing you're buying — measured on your decisions, not asserted."
- **Surface:** Performance → FrozenTwinComparisonPanel; `/api/learning/frozen-twin`. **PW-claim:** two series with a positive gap. **Plant:** twin init. Divergence MODELED/PILOT-TARGET.

# Purchasing — Brightline Hospitality (Marta Ruiz, Regional GM)

### PUR-01 · "The GM Who Just Started" · LIVE · ~2:30 · rooms: COO, CPO, VC
- **Stakes:** Marta onboards yet another store GM — the last took seven weeks to stop over-ordering perishables. Every handoff, the store relearns the same lessons and food cost bleeds.
- **Turn:** *(setup)* the incoming GM's blank order screen. *(reveal)* the system already knows — the prior GM's verified delivery outcomes: "this supplier arrives late 1 in 3; this lot expires before your Saturday event." Day one, not week seven.
- **Gut-punch:** "Everything in this kitchen turns over — staff, suppliers, seasons. The judgment doesn't. That's what you're buying."
- **Dollar:** 7 weeks ramp ≈ $47K/store/turnover; 40 loc × 1.8/yr ≈ **$3.4M/yr** ramp cost, cut to 12 days (MODELED/PILOT-TARGET).
- **Surface:** Order/Performance → SupplierScorecardPanel, ContinuityClosePanel; `/api/score`, `/api/purchasing/proof-ledger`. **PW-claim:** supplier history renders for a GM with zero own decisions (needs preseed). Ramp contrast labeled MODELED.

### PUR-02 · "The Trust Trap" · LIVE · ~2:30 · rooms: COO, VC
- **Stakes:** Marta's team trusts the supplier they've used longest — if that trust is misplaced, they're ordering wrong from the vendor they trust most.
- **Turn:** *(setup)* the supplier signal profile. *(reveal)* on Brightline's own verified orders, the most-trusted supplier factor is the noisiest predictor (highest σ), and it survived correction (partial-pooling + out-of-sample + evidence floor).
- **Gut-punch:** "The supplier you trust most is costing you most — and only your own orders could have told you. That's the mirror, about you."
- **Surface:** Analysis → TrustRadarPanel, GatedSignalReliabilityPanel; `/api/fingerprint`. **PW-claim:** trust radar renders with a most-trusted factor flagged high-σ (needs preseed). Silence: step back from screen.

### PUR-03 · "It Gave Up Its Own Authority" · PLANT · ~2:00 · rooms: COO, risk · [RSI]
- **Stakes:** auto-ordering is only safe if it stops when the person it's learning from goes off the rails.
- **Turn:** *(setup)* the health band GREEN during normal ordering. *(reveal)* a new GM's decisions drift; recent accuracy falls; the band moves and auto-approve pauses itself, routing orders back to human review. No human asked it to stop.
- **Gut-punch:** "It gave up its own authority — because its recent decisions degraded. The most important thing an autonomous system can do is know when not to act."
- **Surface:** Performance → SelfPausePanel, health band; `/api/conservation/status`. **PW-claim:** on drift injection, self-pause activates. **Plant:** the drift→pause transition.

### PUR-04 · "The Quiet Week" · LIVE · ~2:00 · rooms: COO, CFO
- **Stakes:** every vendor's ROI is a marketing estimate; Marta needs dollars she can defend, including the honest zeros.
- **Turn:** *(setup)* the proof ledger. *(reveal)* two curves — the proof curve (gated dollars, allowed to fall: "$0 this week, coverage 94%") and the competence curve (rising even when dollars fall), each with a plain-language why.
- **Gut-punch:** "Every dollar we claim, we can defend — including the weeks we claim zero. Theirs is a marketing estimate; ours subtracts what you'd have caught anyway."
- **Surface:** Performance → ProofLedgerPanel; `/api/purchasing/proof-ledger`. **PW-claim:** proof_curve and competence_curve both render; a $0 week shows competence still rising. LIVE.

### PUR-05 · "Two Stores, Same Menu, Different Judgment" · PLANT · ~2:00 · rooms: COO, VC
- **Stakes:** "is the learning real, or just more data?"
- **Turn:** *(setup)* two food-cost curves. *(reveal)* the learning store's waste drops 6.2%→3.8%; the frozen store holds at 5.9% — same menu, suppliers, seasonality; the difference is 500 verified reorder decisions.
- **Gut-punch:** "Same menu. Same suppliers. Different judgment. The store that learned saves **$2,400/week** in waste — and the gap is still growing."
- **Surface:** Performance → FrozenTwinComparisonPanel; `/api/learning/frozen-twin`. **PW-claim:** two divergent waste curves. **Plant:** twin init. MODELED.

### PUR-06 · "Demand Wasn't the Limiting Factor" · ROADMAP · ~2:30 · rooms: COO, CTO
- **Stakes:** a protein order ahead of a confirmed 180-cover event (baseline 120). More demand looks like "order more."
- **Turn:** *(setup)* the order screen, event confirmed. *(reveal)* the investigation checks the event first, then waste risk — lot expiry, usable stock, next delivery — and lands on "order less for this delivery." The read order (event → waste) is scorer-conditioned, on screen.
- **Gut-punch:** "Next quarter, Marta will see it check the event, then check whether the extra stock would even keep — in that order, because the second question depended on the first. More demand didn't make this delivery usable."
- **Surface:** Analysis/Order → InvestigationTracePanel; `POST /api/purchasing/investigate` (not built). **ROADMAP.** Future tense, planted fixture.

# Trading — Kesler Capital (Marcus Bell, PM)

### TRD-01 · "Your Favorite Setup Is Your Worst Setup" · LIVE · ~3:00 · rooms: PM/risk, VC
- **Stakes:** Marcus believes his momentum setup is his edge. If it's noise — or tail risk he's not paid for — he's sizing up into what blows up his book at the next regime break.
- **Turn:** *(setup)* his factors listed in his own confidence order, momentum on top; hold 2s. *(reveal)* the Trust Radar resolves on his 1,800 verified decisions and the ranking inverts — his #1 is his noisiest (highest σ), survived correction (23 tested, 3 powered, 1 held). Calm-regime Sharpe 2.1 → 1.2 after clustering.
- **Gut-punch:** "Nobody could have told Marcus this — not a dashboard, not a coach. Only his own verified decisions could. A journal records; a mirror reflects."
- **Dollar:** on a $200M book, 2.1→1.2 Sharpe ≈ **$18M**/yr risk-adjusted return he thought he had (ILLUSTRATIVE FROM SAMPLE).
- **Surface:** Analysis → TrustRadarPanel, ClaimGateBadge; `/api/fingerprint`. **PW-claim:** trust radar renders; most-trusted factor flagged highest-σ; claim-gate shows FDR+held-out. Silence: after the inversion.

### TRD-02 · "The Autonomy Throttle" · PLANT · ~2:00 · rooms: PM/risk · [RSI]
- **Stakes:** how RL trading systems die — trained on calm, blown up in crisis, no notion of their own competence boundary.
- **Turn:** *(setup)* the health band GREEN mid-session. *(reveal)* local-Hurst + tail-dependence detect a regime break; the band moves AMBER; the system says "the regime is breaking; I'm reducing my own autonomy until I re-converge."
- **Gut-punch:** "A reward-maximizer overfits your calm regime and can't stop itself. This reduced its own autonomy because it detected the break. No reward-maximizer can do that."
- **Surface:** Performance → AutonomyThrottlePanel, health band; `/api/conservation/status`, `/api/trading/regime-analytics`. **PW-claim:** on a regime-break fixture, autonomy reduces and band → AMBER. **Plant:** regime-break tags + transition.

### TRD-03 · "The Certificate" · LIVE · ~2:30 · rooms: PM/risk, VC
- **Stakes:** most "AI trading journals" always have an insight — which means none can tell you when you're genuinely clean.
- **Turn:** *(setup)* the claim gate running. *(reveal)* "23 detectors, 1,847 decisions, none survive correction (Benjamini-Hochberg FDR, deflated Sharpe, discover-on-70%/confirm-on-30%) — you're genuinely clean," plus an edge-boundary map.
- **Gut-punch:** "A journal that always talks can't do this. Ours refuses the findings that don't survive correction — so when it says you're clean, that means something."
- **Surface:** Analysis/Performance → CertificatePanel, ClaimGateBadge; `/api/self/accuracy-by-category`. **PW-claim:** claim-gate renders the detector count and a "none survive"/certified state.

### TRD-04 · "The Position Wasn't Alone" · ROADMAP · ~2:00 · rooms: PM/risk, CTO
- **Stakes:** a trade with a strong-looking thesis — but a setup that looks great in isolation can be a concentration bomb.
- **Turn:** *(setup)* the trade under review, thesis on top. *(reveal)* the investigation checks position sizing first — three other positions already share this exposure — then regime; lands at "partial execution." The read order (portfolio → regime) is scorer-conditioned; the thesis stays unread above it.
- **Gut-punch:** "Next quarter, Marcus will see the first check wasn't the thesis — it was the portfolio. Correlation supplied the evidence; the scorer chose when to ask for it."
- **Surface:** Analysis → InvestigationTracePanel; `POST /api/trading/investigate` (not built). **ROADMAP.**

### TRD-05 · "The Cold Start vs. The Warm Start" · ROADMAP · ~2:30 · rooms: PM/risk, VC · [⭐ vision]
- **Stakes:** every RL trading system relearns from zero after a regime break — the failure that kills them.
- **Turn:** *(setup)* a regime break (March 2020 replay on real history). *(reveal)* two curves — a cold-start learner relearning from zero vs the system re-initializing from the nearest prior regime's geometry and re-converging faster (γ>1). Two curves diverge at the break.
- **Gut-punch:** "When the world breaks, a cold-start agent starts over. This kept the geometry from the last vol spike and came back faster. An architectural answer, not a tuning trick."
- **Surface:** Performance → ReConvergencePanel; **ROADMAP.** Honesty: γ UNTESTED live; say "faster (γ≈1.2 in simulation; magnitude pilot-only)" — never the unsourced "3×."

### TRD-06 · "The Code Is Free. The Judgment Isn't." · LIVE · ~2:00 · rooms: VC, CTO, dev
- **Stakes:** Trading is the open-source copilot — the room's first question is "if it's open source, what's the moat?"
- **Turn:** *(setup)* "Everything I showed is Apache 2.0 — fork it tonight." *(reveal)* the fingerprint panel: Marcus's 1,800 decisions encoded in 200 centroid values; a fork starts at zero — zero decisions, zero learned weights, zero noise fingerprint.
- **Gut-punch:** "You can copy the code. You can't copy the 200 centroid values. The clock starts the day you begin — and your competitor starts that many decisions behind."
- **Surface:** Analysis → FingerprintPanel; `/api/fingerprint`. **PW-claim:** fingerprint renders 10 factors with earned weights. Honesty: observation-only (no broker execution path, by design).

# DataOps — Northwind Logistics (Priya Rao, Head of Data)

### DO-01 · "Which Data Can You Actually Trust?" · PLANT · ~3:00 · rooms: CDO, CTO
- **Stakes:** Priya's agents consume 200 tables the catalog all labels "governed"; an agent trusts a stale metadata field the same as verified SAP, and a bad decision propagates across ten pipelines.
- **Turn:** *(setup)* the freshness source sits at 0.71 — the trust everyone assumed; hold. *(reveal)* verified decisions arrive where that field led wrong; the score drops to 0.23 live on screen; the DK weight shifts, conservation ticks toward AMBER.
- **Gut-punch:** "Every other data-quality score is a label somebody typed. This one is a measurement — and it's the autonomy license your agents have been missing."
- **Surface:** Dashboard/Insight → SourceProfilePanel, EarnedProofPanel; `/api/dataops/trust`. **PW-claim:** a source's trust score changes after verified outcomes are applied. **Plant/BUILD:** live what-if perturbation (~2-3d); DataOps learning loop confirm (DD-0). Silence: after 0.71→0.23.

### DO-02 · "The Source That Lost Its Trust" · LIVE · ~2:30 · rooms: CDO
- **Stakes:** the catalog still says "governed," but an Airflow metadata feed started returning stale timestamps two weeks ago; three pipelines trust it, and a data product shipped wrong numbers.
- **Turn:** *(setup)* the SourceTrustCard. *(reveal)* SAP 0.94; Airflow metadata 0.23 (dropped from 0.71 after 15 verified wrong outcomes) — the score moved because outcomes proved it unreliable, not because a tag changed.
- **Gut-punch:** "Monte Carlo tells you the pipeline broke. We tell you which source broke it, and how much to trust it now — earned from 500 decisions."
- **Dollar:** that feed → three wrong data products in Q2, **$180K** client penalty; flagged at decision 15, six weeks before (ILLUSTRATIVE).
- **Surface:** Dashboard → SourceProfilePanel, SourceCompoundingPanel; `/api/dataops/trust`. **PW-claim:** per-source trust scores render with differentiated values.

### DO-03 · "Twelve Years in Six Numbers" · LIVE · ~2:00 · rooms: CDO, VC
- **Stakes:** twelve years of institutional knowledge — which patterns matter, which sources to trust. If Priya leaves, it vanishes.
- **Turn:** *(setup)* the fingerprint panel. *(reveal)* 180 centroid checkpoints; `data_freshness: 1.00 (cleanest); recurrence: 0.52 (noisiest)` — twelve years of pattern recognition in 6 numbers, visible to her replacement day one.
- **Gut-punch:** "That is what I learned over twelve years. The system figured it out from 500 decisions in three months — and it'll still be here when I'm not."
- **Surface:** Insight → FingerprintPanel, CentroidTimelinePanel; `/api/fingerprint`, `/api/self/centroid-history`. **PW-claim:** fingerprint renders a 6-factor profile + checkpoint count.

### DO-04 · "The Rule That Proved Itself Wrong" · LIVE · ~2:00 · rooms: CDO, audit · [RSI]
- **Stakes:** an AE-proposed rule ("auto-resolve partition-count alerts from SAP") was promoted after 30 correct applications — then accuracy dropped.
- **Turn:** *(setup)* the rule lifecycle, promoted at decision 30 (93%). *(reveal)* decision 50, accuracy 85%, alert fires → the system demotes its own rule and returns those alerts to manual; the audit trail shows every step.
- **Gut-punch:** "Most systems promote rules and forget them. This tracked the rule through 50 decisions, measured its degradation, and demoted it — without a human asking. That's governance."
- **Surface:** Evidence → RuleLifecyclePanel, RuleGenealogyTree; `/api/self/rule-lifecycle`. **PW-claim:** a rule renders promoted→demoted with per-step reasons. (Rule-lifecycle confirmed on DataOps; the 404 is Trading/Purchasing.)

### DO-05 · "The Question the LLM Got Wrong" · EXPERIMENT · ~2:30 · rooms: CDO, CTO, VC · [K14]
- **Stakes:** Priya evaluates a vendor's AI data-quality agent; it reads "schema change in SAP MATKL field" and says "routine — auto-approve." But the change caused a 9× join fanout silently degrading seven systems.
- **Turn:** *(setup)* LEFT: "LLM surface assessment: routine, approve." *(reveal)* RIGHT: "Investigation traversed schema → join → 7 downstream → 3 critical. Escalate." The investigation found what the surface hid — it reasons from the graph, not the description.
- **Gut-punch:** "We tested this. On 50 DataOps scenarios, an LLM reviewing surface evidence agreed with the correct answer **12%** of the time. The investigation: **76%**. The harder the decision, the wider the gap."
- **Surface:** Triage → ProcessSignalsPanel, DependencyTree; `POST /api/score`. **PW-claim:** investigation escalates the fixture the surface-view would approve. K14 numbers as caption (240 real judgments, n=49 DataOps; Sep 2026). Add: "at that noise level the system would have *unlearned* (reverses at 92%)."

### DO-06 · "The Data Estate in January vs. Now" · LIVE · ~2:00 · rooms: CDO, VC
- **Stakes:** "trust scores are just another number unless I can see them change."
- **Turn:** *(setup)* trust at deployment — all sources 0.45–0.65, undifferentiated. *(reveal)* after 500 verified decisions — SAP 0.94, Airflow 0.23, three promoted, two demoted; the shape of earned trust.
- **Gut-punch:** "In January these all looked the same. Five hundred decisions later, your data estate told you what to trust. No label did that."
- **Surface:** Insight → SourceCompoundingPanel, CentroidTimelinePanel. **PW-claim:** trust distribution renders differentiated after preseed. LIVE.

### DO-07 · "Your Data Tells You What to Buy" · ROADMAP · ~2:30 · rooms: CDO, CFO, VC
- **Stakes:** Northwind spends $2.4M/yr on data subscriptions; the CFO wants to cut 30%, but nobody knows which sources drive better decisions.
- **Turn:** *(setup)* the Intelligence Map — every source a node. *(reveal)* bright = high trust (SAP, verified sensors); dim = the $180K market-research feed unused in 6 months; a gold line connects the SAP delivery feed to a $12K weather API — together they predict spoilage 3 days earlier ($340K prevented).
- **Gut-punch:** "The $180K feed is dim — cut it. The $12K weather API has a gold line to your SAP data; together worth $340K. Your data tells you what data to buy, ranked by ROI."
- **Surface:** Insight → IntelligenceMapPanel, AcquisitionAdvisorPanel; `/api/di/acquisition-advice`. **ROADMAP** (Q1 2027). Numbers ROADMAP-ILLUSTRATIVE.

### DO-08 · "Ask It Like a Person" · ROADMAP · ~1:30 · rooms: CDO
- **Stakes:** analysts write SQL; nobody knows how reliable the underlying data is — 4.2% from a 0.23-trust source looks identical to 4.2% from a 0.94-trust source.
- **Turn:** *(setup)* Priya types "APAC invoice exception rate, and how confident should I be?" *(reveal)* "4.2% (confidence 94% — SAP, trust 0.94). Including Airflow-derived: 5.7% (confidence 47% — trust 0.23). Recommend the SAP-only figure."
- **Gut-punch:** "Every BI tool gives you a number. This one tells you how much to believe it — earned from outcomes, not a metadata tag."
- **Surface:** Dashboard → NLQueryPanel; `/api/dataops/nl/query`. **ROADMAP.**

# Platform & cross-domain (one engine, five copilots)

### PLAT-01 · "Which Clocks Does Your System Run?" · CONCEPTUAL · ~1:00 · rooms: VC, CTO
- **Turn:** four clocks overlaid on a live dashboard — State (what's true now), Event (what happened), Decision (how the reasoning evolved), Insight (what connects across domains nobody queried). "Every SIEM runs State and Event. We run all four — and the third and fourth are where judgment emerges."
- **Gut-punch:** "Ask your next vendor which clocks they run. Most run one or two. The moat is in the third and fourth."
- **Surface:** conceptual overlay. **PW-claim:** n/a (framing). Class: CONCEPTUAL.

### PLAT-02 · "A Fix Born in Security Informs Procurement" · LIVE · ~2:30 · rooms: VC, CISO, CFO
- **Stakes:** Sarah (SOC) and David (S2P), same Tuesday. A vendor-portal credential flagged in SOC at 07:12; that vendor's invoice hits S2P at 2 p.m. In every enterprise these teams never talk — the invoice gets paid.
- **Turn:** *(setup)* the S2P invoice looks routine. *(reveal)* CrossCopilotSignalBanner: "signal from SOC-4417: vendor identity compromised, 07:12 today" — the S2P score re-runs and routes to hold.
- **Gut-punch:** "Nobody emailed anyone. A signal born in security changed a procurement decision the same afternoon. That's what one engine buys you."
- **Surface:** S2P → CrossCopilotSignalBanner; `/api/purchasing/chain/transfer`, `/api/platform/cross-signals`. **PW-claim:** cross-signal banner renders and changes the S2P action. Honesty (F-26): *signals* transfer; judgment is per-copilot — never "shared judgment."

### PLAT-03 · "Five Systems, Five Self-Corrections" · LIVE · ~2:00 · rooms: VC, CISO, risk · [RSI]
- **Turn:** a montage — SOC rejected 35 of its own ideas; S2P earned autonomy week over week; Purchasing paused itself on drift; Trading throttled autonomy on a regime break; DataOps demoted its own rule. Same RSI machinery, five domains.
- **Gut-punch:** "This isn't a feature in one product. Every copilot improves itself and governs the improvement — the answer to 'what if it learns the wrong thing?' in five domains at once."
- **Surface:** quick cuts across five Runtime-Evolution/Performance surfaces. **PW-claim:** each copilot's self-correction surface renders (composite of SOC-03/04, S2P-04, PUR-03, TRD-02, DO-04).

### PLAT-04 · "Five Curves, One Graph" + "The Moat That Builds Itself" · LIVE + MEASURED · ~3:00 · rooms: VC, CFO
- **Turn:** *(setup)* five trajectory charts. *(reveal)* all five climbing — different domains, different factor spaces, same architecture, each conservation GREEN. Then the moat: SOC routing gap 19.6 ± 5.4 pp, 0/5 seeds parity, labels are the asset. "A competitor can copy the code; they can't copy the 1,800 verified decisions in your graph."
- **Gut-punch:** "This isn't a moat I'm asking you to believe in. It's one I can measure. 19 percentage points. Five copilots. One architecture. Every decision widens it."
- **Dollar:** aggregate compounding dividend across the five reference firms ≈ **$4.2M/yr** (MODELED/PILOT-TARGET).
- **Surface:** five Dashboard/Performance curves + moat caption; `/api/metrics/compounding` per copilot. **PW-claim:** each copilot's curve renders non-empty; moat/switching-cost value renders. Moat MEASURED (B2/EXP-1).

### PLAT-05 · "Two Questions for Your Next Vendor" · CONCEPTUAL · ~1:30 · rooms: VC, CISO, CDO · [K14]
- **Turn:** direct to the room: "Ask your next vendor two questions. One: after ten thousand decisions, show me the compounding curve. Two: how do you validate it got smarter — an LLM judge, or ground truth? We tested that — on investigation-dependent decisions an LLM judge agreed 12% of the time; our geometry-derived check, 76%. The blind spot and the value are the same set."
- **Gut-punch:** "Those two questions disqualify every vendor we've tested. If your next meeting can answer them, talk to that vendor. We'll still be here — compounding."
- **Surface:** none. CONCEPTUAL. K14 stated as experiment (n=240, Sep 2026).

### PLAT-06 · "Where It Doesn't Work" · EXPLORATORY · ~2:00 · rooms: VC, buyer
- **Stakes:** buyers have been burned by "AI for everything"; VCs price TAM. A vendor that can't say where it fails can't say where it fits.
- **Turn:** *(setup)* two Brightline decisions — a par-level reorder and a multi-site contract renewal. *(reveal)* the applicability measure: reorder is shallow, one read, small gain; multi-enterprise procurement (conditional fraction 0.213→0.279, chain length 1→2) → compounding gain +6.0→+16.4 pts. Same copilot.
- **Gut-punch:** "We can tell you before deployment which of your decision queues will compound and which won't. Most vendors find out after the pilot. We tell you on the scoping call."
- **Surface:** `/api/platform/domain-applicability`. **PW-claim:** applicability data renders per domain. EXPLORATORY (n=5–6; descriptive) — "predictor, not proof."

### PLAT-07 · "Whose Moat Is It?" · LIVE + MEASURED · ~2:00 · rooms: VC, CFO, buyer · [dual-room]
- **Turn:** the geometry export on screen (μ, K, ledger, JSON). To the buyer: "This is yours. The engine is Apache-2.0. You can leave with your judgment." To the VC: "Nobody else can *use* it without your verified stream — 19.6 ± 5.4 pp gap, ~50% of the labeled stream to close."
- **Gut-punch:** "No lock-in to us. Total lock-in to your own history. That's the only moat a buyer will thank you for."
- **Surface:** geometry export + `SwitchingCost`; `/api/soc/centroid-export`, `/api/metrics/switching-cost` (**BUILD** — 404). **PW-claim:** export downloads; switching-cost renders decisions_accumulated + equivalent_calendar. Honesty: non-transferable, not un-copyable (state migration collapses it).

# The Machine (architect / CTO / technical VC — domain-skinned, not abstract)

### MACH-01 · "One Decision Through the Whole Machine" · LIVE + EXPERIMENT · ~3:00 · rooms: CTO, VC
- **Turn:** Sarah's 2 a.m. alert (SOC-02) run end to end — factor vector → routing picks the decisive read → enrichment → re-score → conservation → emit. The eight blocks light up as the decision moves; four readouts emerge from the one trace: which evidence, how much, the better action, how sure. Caption: strip the trajectory features and confidence collapses to AUC 0.642 (ablation).
- **Gut-punch:** "Four features on a competitor's quote. One mechanism here — and you validate it once."
- **Surface:** Alert Triage trace; `POST /api/alert/analyze`. **PW-claim:** the decision trace renders the read sequence + a confidence. Honesty: readouts 1–2 are controls on the loop, 3–4 measured from it.

### MACH-02 · "Reshape, Not Retrieve" · LIVE · ~2:00 · rooms: CTO, VC
- **Turn:** the same alert three ways — READ (RAG) returns nothing (no precedent); ROUTE (agents) dispatches; RESHAPE decides and reshapes the boundary from the verified outcome — with the definitional test on screen (boundary reshapes from verified outcomes; procedure class invariant).
- **Gut-punch:** "Excluded by the mathematics, not by marketing. A retriever updates what it fetches; this updates the surface that decides."
- **Surface:** SOC no-precedent + a category-test overlay. **PW-claim:** the no-precedent path renders (shares SOC-02).

### MACH-03 · "Show Me the Parameter That Moved" · PLANT · ~2:00 · rooms: CTO, VC
- **Turn:** *(setup)* decision N verified. *(reveal)* a single K entry moves (0.100→0.200); decision N+1 reads the contract-clause factor first and lands a different action; Δμ shown = 0 (nothing else moved). Three rows.
- **Gut-punch:** "One verified outcome. One weight. One different decision. That's the whole definition — on screen, not in a slide."
- **Surface:** recursion trace (planted fixture, real update rule). **PW-claim:** a K delta renders and the subsequent decision's read order changes. **Plant:** the N→N+1 recursion fixture.

### MACH-04 · "Five Hundred Decisions, Not Five Million" · LIVE · ~1:30 · rooms: VC, CTO
- **Turn:** a 6×4×6 geometry (144 cells) beside a rented model's parameter count; the curve plateaus at ~500 verified decisions, and the exhibit is the geometry moving in that window.
- **Gut-punch:** "A 175-billion-parameter model has more capacity and zero judgment memory. A 144-cell geometry has less capacity and all of it — and it moves in hundreds of your decisions, not millions."
- **Surface:** compounding curve + heatmap. **PW-claim:** geometry dimensions render; curve reaches plateau. Honesty: low-d is the design (auditable, cheap, data-efficient).

### MACH-05 · "The Retraction List" · CONCEPTUAL · ~2:00 · rooms: VC, CISO, audit
- **Turn:** one screen: everything the program tested and withdrew — B1 moat retracted (design flaw → B2); 57:0 requalified to 1,184:0 boundary / 0:2,282 misleading; L4 cross-domain transfer null; "saves reads" retracted; μ-specificity SOC-only; γ untested. Each with the experiment that killed it.
- **Gut-punch:** "Ask your next vendor for their retraction list. A self-improving system that has never withdrawn a claim has never tested one."
- **Surface:** none. CONCEPTUAL (MEASURED sources). Frame as boundary characterization, never "failures."

# The Pilot (enterprise buying committee — the buy-side vision)

### PILOT-01 · "Your First 90 Days" · ILLUSTRATIVE · ~1:30 · rooms: CFO, buyer, all
- **Turn:** a three-column card — what you supply (decision stream + verified outcomes; no labels, no training corpus) · when the curve diverges (SOC ~2–3 days, S2P ~3–4, Purchasing ~1 week, DataOps ~2–3 weeks, Trading ~3 months) · what you own at day 90 (your geometry, your K, your ledger).
- **Gut-punch:** "You don't hand us data and wait six months. You verify decisions you were already making — and the curve is yours by week two."
- **Surface:** DayZeroReadinessPanel; `/api/purchasing/day-0-readiness`. **PW-claim:** readiness card renders ready/coverage/not_yet. ILLUSTRATIVE (D2 latency).

### PILOT-02 · "The Month the Verifications Stopped" · PLANT · ~2:00 · rooms: buyer, CFO
- **Stakes:** "what happens when my team stops feeding it?" — the second-most common objection.
- **Turn:** *(setup)* the compounding curve climbing. *(reveal)* a hiring freeze — nobody verifies for three weeks; the curve goes flat, not down; conservation holds; the geometry freezes at its last quality; verifications resume, the curve resumes.
- **Gut-punch:** "The gate stops it acting when it shouldn't; sparse verification stops it learning — never degrading. You can pause the loop without losing the judgment."
- **Surface:** compounding curve with a verification gap; **PLANT/BUILD** the gap fixture. **PW-claim:** curve flatlines during the gap, resumes after. Honesty: slow world-drift while frozen is a stated envelope boundary.

### PILOT-03 · "Open the Three Artifacts" · LIVE · ~2:00 · rooms: audit, CDO, CTO
- **Turn:** three tables opened in sequence — centroids μ (what a good decision looks like here), noise fingerprint σ (which factors are signal), routing memory K (which evidence proved decisive) — each with the timestamp of the verified decision that last moved it.
- **Gut-punch:** "These aren't views of a model. They are the decision. Your reviewer can read the substrate without a statistician — there's nothing behind it."
- **Surface:** FingerprintPanel, CentroidTimelinePanel; `/api/self/centroid-history`. **PW-claim:** μ/σ/K render with last-moved timestamps. Honesty: exported σ is uniform pre-compounding — show K and μ moving, tell σ honestly.

### PILOT-04 · "Bring Your Own Numbers" · MODELED · ~1:30 · rooms: buyer, CFO
- **Turn:** the readiness card + a volume input → projected divergence week and a MODELED dividend, both tagged. "Put your volume in. Watch which week the curve leaves the flat line."
- **Gut-punch:** "No vendor can hand you your magnitude on day one — including us. But we'll show you the week it starts."
- **Surface:** ROI/readiness input; `/api/roi/calculate`, day-0-readiness. **PW-claim:** input produces a projected divergence week. MODELED/PILOT-TARGET; never a customer-specific ROI.

# Fork It Tonight (open-source developers — Trading reference app)

### FORK-01 · "Clone It, Run the Gate, See Your Fingerprint" · LIVE · ~3:00 · rooms: dev
- **Turn:** clone GAE + SDK + trading copilot → run the conservation gate on your own trade log → your fingerprint (10 factors, earned weights; zero decisions = flat line) → read the promotion gate's z-test → the tensor-shape contract for contributing a copilot (situations × actions × factors).
- **Gut-punch:** "The code is free. The judgment isn't. Fork it tonight — and start your own clock."
- **Surface:** OSS repo + `/api/fingerprint`, `/api/gae/*`. **PW-claim:** fingerprint + gate render on a fresh clone. Honesty: observation-only (no broker execution path, by design) — say it in the first minute.

# Suggested playlists (starting points — the Loom step mixes, matches, selects)

Each is a ~15–20 min room-specific sequence drawn from the catalog. Not fixed — a menu. Every playlist:
opens with a cold-open hook (below), builds through the compounding + governance beats, shows one
labeled roadmap, and closes on a LIVE proof (never on roadmap).

**Cold opens per playlist:**
CISO/SOC — "After ten thousand decisions, show me how your system got smarter."
CFO/S2P — "Your AP team rejected 47 good invoices this quarter. Each one was a rule doing its job."
COO/Purchasing — "Every time a store manager leaves, seven weeks of judgment walks out the door."
PM/Trading — "Your favorite setup. Your best year. Your noisiest signal. They're the same thing."
CDO/DataOps — "Every data catalog says 'governed.' None can tell you which data earned it."
VC/Platform — "Five domains. One engine. The intelligence is firm-specific. The architecture is domain-agnostic."
CTO/Machine — "Four features on a competitor's quote. One mechanism here — and you validate it once."
Risk/audit — "Ask your next vendor for their retraction list."
Buyer/Pilot — "You don't hand us data and wait six months."
Dev/Fork — "The code is free. The judgment isn't. Fork it tonight."

- **CISO / SOC** — SOC-01 (analyst who left) → SOC-02 (no precedent) → SOC-06 (policy wins) → SOC-03 (rejected 35) → SOC-04 (paused itself) → SOC-05 (two alerts, ROADMAP) → SOC-07 (chained) close.
- **CFO / S2P** — S2P-01 (the rule) → S2P-02 (day zero) → S2P-04 (earned autonomy) → S2P-05 (queue shrank) → S2P-08 ($50K vs $500) → S2P-07 (adaptive effort, ROADMAP) → S2P-09 (frozen twin) close.
- **COO / Purchasing** — PUR-01 (new GM) → PUR-02 (trust trap) → PUR-05 (two stores) → PUR-03 (gave up authority) → PUR-06 (demand wasn't the limit, ROADMAP) → PUR-04 (quiet week, proof close). ~18 min.
- **PM / Trading** — TRD-01 (favorite setup) → TRD-02 (throttle) → TRD-03 (certificate) → TRD-04 (position wasn't alone, ROADMAP) → TRD-05 (re-convergence, ROADMAP) → TRD-06 (code is free) close.
- **CDO / DataOps** — DO-01 (which data) → DO-02 (source lost trust) → DO-03 (twelve years in six numbers) → DO-04 (rule proved itself wrong) → DO-05 (K14) → DO-07 (what to buy, ROADMAP) → DO-06 (Jan vs now) close.
- **VC / Platform** — PLAT-01 (clocks) → SOC-02 / S2P-01 / PUR-01 (3-opener montage, LIVE) → PLAT-05 (two questions, K14) → PLAT-03 (five self-corrections) → PLAT-04 (five curves + moat) close; optional PLAT-06 (where it doesn't work).
- **CTO / The Machine** — MACH-01 (one decision through the machine) → MACH-02 (reshape not retrieve) → MACH-03 (parameter that moved) → DO-05/PLAT-05 (K14) → MACH-04 (500 not 5M) → MACH-05 (retraction list) or PLAT-07 (whose moat) close.
- **Risk / audit** — MACH-05 (retraction list, as "what we withdrew") → SOC-06 (policy wins) → SOC-03 (rejected 35) → SOC-04 (paused itself) → PILOT-03 (three artifacts) → SOC-10 (roll it back) → SOC-07 (chained) close.
- **Buying committee / The Pilot** — PILOT-01 (first 90 days) → PLAT-06 (where it doesn't work) → S2P-08 ($50K vs $500) → PILOT-02 (verifications stopped) → PLAT-07 (whose moat, buyer read) → PILOT-04 (bring your numbers) close.
- **Developers / Fork** — FORK-01 → TRD-06 (code is free) → TRD-03 (certificate) → TRD-01 (mirror).
- **3-minute short cut (any domain, LinkedIn/email)** — cold line → the domain's hero LIVE beat → its RSI beat → the napkin number → close. E.g. SOC: SOC-02 → SOC-03 → SOC-01 dollar → one line.

# Class rollup (for the MAP addendum — what's LIVE vs needs work)

- **LIVE now (record immediately):** SOC-01, SOC-02*, SOC-03, SOC-07, SOC-09; S2P-01, S2P-02, S2P-04; PUR-01, PUR-02, PUR-04; TRD-01, TRD-03, TRD-06; DO-02, DO-03, DO-04, DO-05, DO-06; PLAT-02, PLAT-03, PLAT-04(curves), MACH-01, MACH-02, MACH-04, MACH-05, PILOT-01, PILOT-03, FORK-01. (*SOC-02's escalate is LIVE; its no-precedent alert needs planting.)
- **PLANT (endpoint exists, seed the data):** SOC-02 (no-precedent alert), SOC-04 (gate transition), SOC-06 (policy conflict), SOC-08 (frozen-twin init), SOC-10 (checkpoint sequence); S2P-03 (container context), S2P-05 (extinction history), S2P-06 (kept-manual case), S2P-09 (twin init); PUR-03 (drift→pause), PUR-05 (twin init); TRD-02 (regime tags); DO-01 (live perturbation); MACH-03 (recursion fixture); PILOT-02 (verification-gap fixture).
- **BUILD (code first):** PLAT-06 (`/api/platform/domain-applicability` — endpoint not yet built); PLAT-07 / MACH (switching-cost endpoint `/api/metrics/switching-cost` — 404); S2P-07 & S2P-08 dollar-threshold routing UI + budget strip; DO-01 live what-if perturbation; PILOT-02 verification-gap curve; the four investigation-trace ROADMAP surfaces (SOC-05, S2P-07, PUR-06, TRD-04) if promoted from mockup.
- **ROADMAP (mockup, future tense):** SOC-05, S2P-07, PUR-06, TRD-04, TRD-05, DO-07, DO-08.
- **EXPERIMENT/CONCEPTUAL (caption-backed, no live metric):** DO-05, PLAT-01, PLAT-05, PLAT-06, MACH-05.

**Route corrections carried:** SOC on 8001; `/api/soc/graph/prebuilt-queries`, `/api/soc/checkpoint/list`, `/api/learning/frozen-twin`.

*Catalog v5 · 47 scenarios (7 reviewed fixes from v4: DO-03 in CDO playlist, S2P-08 K14 cross-ref, across SOC(10) S2P(9) Purchasing(6) Trading(6) DataOps(8) Platform(7) Machine(5) Pilot(4) Fork(1) · one RSI beat per domain · K14 in DataOps + Platform + Machine · mirror opens Trading & Purchasing · roadmap mockups labeled throughout. Next: the consolidated PW + code-buildout list for the MAP addendum.*
