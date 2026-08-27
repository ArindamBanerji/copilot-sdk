# Compounding Intelligence — Product Suite Feature & Value Catalog (Complete)

Seven components, inventoried from code ground truth: two platform components (**GAE**, **copilot-sdk**)
and five copilots (**SOC, Trading, Purchasing, DataOps, S2P**). Same engine, different domains —
patterns learned in one carry to the next. Each feature below is listed with what it does and why it
matters.

*Conventions: features are shipped unless tagged **(in progress)** = partially built, **(spec)** =
designed but not yet implemented in code, or **(unverified)** = present by design, location
unconfirmed. Where code and a PD disagree, code is treated as ground truth and the discrepancy is
noted.*

---

## 0. Platform Capabilities — What Makes This a Platform

The five copilots are not five products. They are one engine, on one governed graph, under one
conservation law, with one evidence backbone. **These platform capabilities are the moat** — the
reason the whole is worth more than the parts, the reason a buyer's investment compounds instead of
plateauing, and the reason switching away gets more expensive every week. Everything in §1–§10 sits
on top of these six.

| # | Platform capability | Why it's the moat |
|---|---|---|
| 0.1 | **One shared knowledge graph** | Institutional judgment accumulates in one auditable place and survives staff turnover |
| 0.2 | **Cross-domain transfer** | Judgment learned in one domain warm-starts the next — faster time-to-value, cross-copilot signals |
| 0.3 | **One conservation law, everywhere** | A single, provable safety guarantee across every copilot and every learning loop |
| 0.4 | **Provenance & substantiation backbone** | Every number carries its evidence — auditable, falsifiable, never overclaimed |
| 0.5 | **Robust to bad teaching** | Validated defenses against adversarial and noisy human input — the #1 fear, answered |
| 0.6 | **The compounding moat (IKS)** | Accumulated firm-specific judgment is a measurable asset a competitor can't copy |

### 0.1 One shared knowledge graph — institutional judgment in one place

- All five copilots read/write **one governed graph** (33,048 nodes); cross-type links — event × judgment, entity × judgment, one domain × another — are **native traversals**, not brittle integrations.
- Domain-scoped isolation (prefixed IDs `TRD-/PUR-/DOPS-/S2P-`, shared-graph pair authorization, SOC domain predicates) keeps each copilot's data separate on the shared substrate.
- **Moat:** the graph is a queryable knowledge *asset*, not plumbing — judgment accumulates in one place, survives staff turnover, and is the substrate that makes cross-domain discovery and transfer possible.
- *Evidence: shared-AGE migration across all five copilots; domain isolation verified in code.*

### 0.2 Cross-domain transfer — judgment learned once accelerates the next

- A converged copilot's centroid geometry **warm-starts** a related deployment/location (conservation-gated); a shared pattern registry stores reusable transfer patterns.
- Cross-domain traversal lets a signal in one copilot inform another (e.g., a DataOps issue warning security or procurement; the cross-domain "$604K finding" (illustrative demo figure) from a live traversal).
- **Moat:** new deployments start *warm*, not cold, and a discovery in one domain compounds into another — five separate tools structurally cannot do this.
- **Honest scope:** warm-start *acceleration*, conservation-mediated — **not** a magnitude claim. The earlier "+28pp cross-deployment" figure did not reproduce and is retracted; position as time-to-value.
- *Evidence: warm-start + transfer registry + cross-domain traversal in the SDK; chain-transfer and cross-copilot signals shipped.*

### 0.3 One conservation law governs every loop

- The **same** law — α·q·V ≥ θ_min — gates scoring, exploration, **and** scorer/prompt evolution across all five copilots. One law, not five.
- When verified-oversight quality degrades, the system **auto-pauses**; autonomy expands only above the threshold.
- **Moat:** a buyer reasons about safety **once**, platform-wide — the CISO/CFO "how do you *know* it's safe to automate more?" has a single provable answer.
- The law is also the **transfer mechanism**: warm-start value exists *because* conservation gates what a warm start may do.
- *Evidence: conservation validated and deployed ×5 (math_synopsis v20); prompt-variant promotion routed through the same gate as scorer promotion.*

### 0.4 Provenance & substantiation backbone — every number carries its evidence

- **Evidence-tier gate** assigns maturity to every claim; **provenance labels** mark each value fixture / graph / scorer and context / learned / unavailable.
- A hard rule keeps **`sample` data out of headline metrics**; **tamper-evident SHA-256 audit chains** (SOC, S2P) make every decision verifiable.
- The **frozen twin** proves learning (live vs immutable day-zero); a **claim registry** blocks selection-adjusted (cherry-picked) claims.
- The per-factor noise fingerprint (σ) is **diagnostic-only** (σ⊥μ proved first-order exact) — used for signal-confidence inversion and trust-trap detection, **never** as a scoring weight.
- **Moat:** in a market of unfalsifiable AI claims, "every number carries its evidence" is a differentiator a technical buyer can verify; every action is explainable, traceable, auditor-ready.
- *Evidence: evidence-gate, provenance module, audit verify-chain, frozen-twin, claim-gate in code.*

### 0.5 Robust to bad teaching — the governed learning sidecar

- Core learning is **supervised prototype learning from verified decisions** — not RL. (Scorer-integrated RL was tested 4 ways / 6+ strategies and **closed** as no better than a uniform rate; action selection is not reward-maximizing.)
- RL and self-evolution run as a **conservation-gated sidecar**: shadow-test → promote → rollback.
- **Adversarial rollback (AE-DECISION, validated):** under 20% poisoning, non-recovery **57% → 14%** (−42.5pp, 3/3 seeds), centroid drift ~−60%, recovery in one decision.
- **OOD abstention (SA-ABSTAIN, validated):** per-decision abstention, **100% OOD detection at <5% false positives** — complements conservation (aggregate) with per-category defense.
- **Moat:** the #1 fear of "AI that learns from your people" — bad or adversarial input corrupting it — has *validated* answers here: detect the unseen and abstain, roll poisoned learning back automatically.
- *Evidence: math_synopsis v20 (AE-DECISION, SA-ABSTAIN validated; scorer-RL closed); sidecar evolver + shadow-runner in code.*

### 0.6 The compounding moat — IKS & switching cost

- An **Institutional Knowledge Score** tracks accumulated judgment over time; switching-cost analysis quantifies what leaving forfeits.
- The judgment is **firm-specific** — learned from *your* verified decisions, living in centroids and a σ-fingerprint that mean nothing to a competitor's deployment.
- **Moat:** makes compounding **visible** and turns judgment into a measurable, defensible asset — the retention argument, and the CFO's "grows every week, can't be re-bought off the shelf." Every day widens the gap.
- *Evidence: IKS services across copilots; switching-cost analysis in SOC.*

---

## 1. GAE — Graph Attention Engine (platform)

The open-source (Apache 2.0) mathematical substrate: centroid learning, kernel weighting, conservation
monitoring, and evaluation. Every copilot runs on it.

| Feature | What it does | Value |
|---|---|---|
| Scoring-kernel protocol | Defines how any scoring method plugs into the engine | Kernel-agnostic core — new scoring math drops in without touching copilots |
| L2 kernel | Scores by Euclidean distance to learned centroids | The robust, validated production scorer |
| Diagonal kernel | Scores with per-factor diagonal weights | Weights each factor by how much it actually predicts outcomes — the basis of the trust fingerprint |
| Profile scorer | Scores a factor vector against category centroids | The core "how close is this to what worked before" computation |
| Profile-scorer factory | Builds configured scorers | One construction path, consistent config across domains |
| Factor-computer protocol | Defines domain factor computation | Each domain expresses its own signals through one interface |
| Factor-vector assembly | Combines factor outputs into a scorable vector | Turns raw domain signals into a decision the engine can judge |
| DK estimator | Estimates diagonal-kernel weights from outcomes | Learns which factors matter, per category, from verified decisions |
| Coordinate-descent estimator | Fits weights by coordinate descent | Stable weight estimation even when factors are correlated |
| Covariance estimator | Computes covariance state | Captures factor interactions the diagonal view misses |
| Novelty tracker | Tracks how novel a decision is | Powers the "we've never seen this" no-precedent / day-zero trigger |
| Nearest-neighbor novelty | Computes NN-based novelty | Quantifies how far a case is from anything known |
| Shrinkage schedules | Fixed and ramped learning-rate shrinkage | Fast early learning that stabilizes as evidence accrues — no overfitting to the last decision |
| Judgment computation | Converts score state into a judgment result | The score becomes an actionable recommendation plus confidence |
| Referral engine | Routes decisions to referral rules | Sends the right cases to a human automatically |
| Override detector | Detects human override behavior | Learns from disagreement — the strongest teaching signal |
| Theta-min computation | Computes the conservation threshold | Sets the safety floor automation must clear |
| Conservation check | Tests α·q·V ≥ θ_min | The go/no-go safety gate on every decision |
| Conservation status | Computes phase status | Says whether the system is calibrating, safe, or must pause |
| Breach window | Computes sustained-breach windows | Catches real quality drops, not one-off blips |
| Optimal tau | Computes the decision threshold | Sets each action's score cutoff from data, not guesswork |
| Transfer prior | Computes a transfer prior | Seeds a new deployment from a related one's learned judgment |
| Conservation state machine | Tracks calibrate → learn → pause transitions | Governs the safety lifecycle |
| Conservation monitor | Monitors conservation state continuously | Always-on safety oversight |
| OLS monitor | Monitors override lift | Tracks whether the model is beating human overrides |
| Var-Q monitor | Monitors oversight-quality variance | Watches the stability of human verification quality |
| Convergence metrics | Half-life, steady-state MSE, asymptotic error, reconvergence ratio | Quantifies how fast and how well the model learns and re-stabilizes after a shift |
| Convergence predictions | Predicts decisions / weeks to competence | Tells a buyer "you'll see competence in ~N weeks" |
| Evaluation runner | Runs scenarios and reports calibration error (ECE) | Measures whether the system's confidence is honest |
| SNR reporting | Per-category signal-to-noise | Shows which categories have learnable signal vs pure noise |
| Kernel selector | Recommends a scoring kernel | Picks the right scoring math per domain automatically |
| Ablation runner | Runs component ablations | Proves which components actually contribute — honest self-testing |
| Bootstrap calibration | Builds calibration and enriched priors | Usable judgment before large data accrues |
| Batch promotion gate | Validates batch composition and promotion | Prevents biased batches from corrupting learning |
| State persistence | Saves and loads scorer state | Learned judgment survives restarts |
| Evolution ledger | Records and summarizes evolution events | An audit trail of how the engine changed |
| Two-phase policies | Decision-count / manual / rolling-accuracy phase control | Controls when the system shifts from watching to acting |
| DomainConfig & presets | Tensor, learning, and domain configuration | One engine configured to any domain by data, not code forks |
| CLI | Packaged command-line operations | Run and inspect the engine without a UI |
| Packaged examples *(in progress)* | Example scorer/config material | Faster onboarding for open-source adopters |
| Design validation scenarios *(spec)* | Validation requirements from the design doc | The acceptance bar the engine is held to |

---

## 2. copilot-sdk — Shared Copilot Runtime (platform)

The shared runtime every copilot inherits: scoring, routers, evolution, learning-signal, graph,
evidence, transfer, pilot, and infra. A copilot is largely a domain preset plus screens over this.

| Feature | What it does | Value |
|---|---|---|
| DomainShape | Represents category / action / factor dimensions | Expresses any domain's decision space in one structure |
| DomainPreset | Stores a domain's scoring configuration | A copilot is "just" a preset over the shared engine |
| CompoundingScorer | Scores and learns from decisions | The shared brain every copilot runs on |
| Scorer proxy | Exposes score / learn / state / diagnostics | Uniform access to the scorer across copilots |
| Scoring router (+ endpoints) | Mounts score, learn, fingerprint, trajectory, health, diagnostics, history, measurement-state | Every copilot exposes the same scoring/learning surface for free |
| Measurement-state router | Returns a copilot's measurement state | Shows honestly whether a copilot is calibrating or measuring |
| Conservation router | Mounts conservation status + what-if | Exposes the safety gate and lets you ask "what if I automate more" |
| Counterfactual router | Mounts counterfactual scoring | Perturb a factor, see the score move — explainability that isn't theater |
| Self-computation router | Centroid history, replay, lineage, diagnostics, trust-traps, rollback, decisions, audit-trail, decision-flow | The platform reasoning about itself, fully surfaced |
| Archetype router | List / current / get / apply a starting judgment profile | A new tenant starts from a sensible prior, not cold |
| Discovery router | Sweep, digest, alerts, cross-system | Finds cross-signal patterns and cross-copilot links |
| Data-intelligence router | Profile, source, combination, acquisition, valuation, intelligence-map, query, search, catalog | The reusable data-intelligence surface |
| Evolution router | Variants, history, promoted, summary, record-outcome, check-promotion | The AgentEvolver control surface — see what it tried, promoted, and rejected |
| Report router | Weekly report | Automatic weekly value/activity summary |
| Transfer router | Status, opportunities, demo, execute | Surface and act on cross-domain transfer opportunities |
| Self-transfer router | Transfers, transfer | Move judgment between a copilot's own categories |
| Variant store | In-memory and SQLite variant stores | Durable record of evolution variants |
| Evolution ledger | Stores evolution events | Event history for self-improvement |
| Evolution protocols | Event / rule / ledger / store / selector / shadow / promotion interfaces | Clean, swappable evolution components |
| Shadow runner | Executes variants in shadow mode | Test changes against live decisions with zero risk |
| Prompt-variant evolver | Generates and manages prompt variants (UCB1) | Improves prompts/routing automatically via bandit search |
| Agent evolver | Coordinates the propose → shadow → gate → promote loop | The deployment improves its own operation without retraining the model |
| Promotion engine | Manages staged promotion | Runs paper → small → full style graduated autonomy |
| Promotion policies | S2P, SOC, Trading, Purchasing, DataOps policies | Each domain gets its own safe-promotion rules |
| Verified outcome | A human-verified decision receipt | The ground-truth unit the system learns from |
| Outcome processor | Idempotently processes outcomes | Safe, replay-proof ingestion |
| Outcome ledger | Persists verified outcomes | Durable record of what actually happened |
| Outcome router | Process, get, count | API to submit and audit outcomes |
| Outcome adapters *(in progress)* | Bridges legacy reward records to verified outcomes | Migrates old data without loss |
| Reward compatibility layer *(in progress)* | Legacy reward functions during migration | Nothing breaks mid-migration (core learning path is supervised, not RL) |
| Frozen Snapshot | Immutable day-zero scorer/kernel/conservation/IKS state + checksum | A tamper-proof "day one" to compare against |
| Frozen Twin | Compares immutable day-zero vs live scoring | Proves the system actually learned — "here's what day one would have said" |
| Frozen Twin store | Persists snapshots across restarts | The learning proof survives restarts |
| Frozen Twin router | Status, drift, parallel-score, freeze | Surfaces the learning delta live |
| Evidence gate | Assigns evidence maturity tiers | Never claims more certainty than the evidence supports |
| Pilot qualification | Pilot-readiness and transfer qualification | Tells you when a deployment is ready to trust |
| Situation analyzer | Builds situation context | Decisions are scored in context, not in a vacuum |
| Regime detector | Detects regime state | The copilot knows what environment it's in |
| Regime conditioner | Applies regime-specific context | Judgment adapts to conditions |
| Per-regime centroids | Tracks centroids per regime | Separate learned judgment per environment — non-stationarity handled |
| Transfer registry | Stores reusable transfer patterns | A library of what transfers across domains |
| Cross-domain traversal | Traverses cross-copilot relationships | Walk relationships across copilots on one graph |
| Warm start | Applies transferred centroids | New deployments start warm instead of cold |
| GraphStore protocol | Defines shared graph operations | One storage interface, many backends |
| Graph store backends | In-memory, SQLite, AGE, Protocol-V2, dual-write | Run isolated, durable, or on the shared enterprise graph, with safe migration |
| Outbox | Persists pending writes for replay | No lost writes; reliable replay |
| Scaffold generator + CLI | Generates a new copilot from YAML | Stand up a new domain copilot in minutes, not months |
| Enterprise ROI calculator | Aggregates financial impact across copilots | Rolls per-copilot value into one portfolio number for the buyer |
| Demo/infra tooling | Demo runner, preseed, truth-preflight, hero-moments, loom-gauntlet | Reproducible, provenance-checked demonstrations |
| Shared frontend components | Reusable TSX components + providers under `copilot_sdk/frontend/` (TrajectoryChart, ConservationProjection, etc.) | Consistent UI across copilots |
| Framework router (shared) | One shared framework router in the SDK; S2P adds a domain adapter (not just per-app copies) | Reduces drift between copilots |

---

## 3. SOC Copilot — Security Operations

Learns from every analyst triage decision so the alert queue reflects your firm's real threat history.
*Ground truth: live categories are the six code categories below; the PD's malware_delivery / phishing
are design-only.*

| Feature | What it does | Value |
|---|---|---|
| Domain model | Tensor (6,4,6); penalty ratio 20:1 | A high asymmetric penalty encodes security's real cost curve — a missed true threat costs far more than a false alarm |
| Decision factors (6) | privileged_identity_context, asset_criticality, threat_intel_enrichment, pattern_history, time_anomaly, device_trust | Scores each alert on the dimensions that actually separate real incidents from noise |
| Threat categories (6) | credential_access, malware_execution, lateral_movement, data_exfiltration, insider_threat, cloud_infrastructure | Judgment specialized per attack type |
| Factor orchestrator | Runs factor computers and preserves provenance | Every score is traceable to its inputs |
| Pattern-history factor | Accumulates historical alert evidence | "Have we seen this, and what happened" built into the score |
| Threat-intel factor | Enriches alerts from threat intelligence | External context without analyst pivoting |
| Triage router | Analyze, decide, health | Score an alert and record the analyst's decision in one flow — the learning loop |
| Alert router | List and retrieve alerts | The working queue |
| Learning control | Controls shadow / learning state | Safely turns compounding on (SOC ships learning-off by default) |
| Framework router | Graph, scorer, shadow, checkpoint, intervention controls | Full operational control surface |
| Conservation service | Computes conservation state and veto | Auto-pauses risky autonomy |
| Learning service | Applies verified learning | Every confirmed decision sharpens the model |
| Shadow service | Runs parallel shadow decisions | Test the model silently against analysts before trusting it |
| IKS service | Computes institutional knowledge | Quantifies accumulated SOC judgment |
| NL template engine | Renders evidence explanations | Plain-English "why" for each alert |
| Referral service | Routes decisions to review | Right cases to humans, automatically |
| Authority ladder | Per-class authority + conservation veto | The copilot earns autonomy class by class — and loses it if quality drops |
| No-precedent detector | Identifies novel alerts | Flags "not yet" instead of guessing on the unseen |
| What-if inspector | Per-factor decision boundaries | "Change this factor and the decision flips here" — real explainability |
| Cross-alert campaign detection | Stable campaign identity + CONTINUES-edge temporal chaining links related alerts into one campaign | Slow, multi-signal attacks surface as one campaign, not 500 separate alerts |
| Frontend surfaces | Triage / Intelligence / Learning / Settings screens; Control Room; Authority-Ladder, No-Precedent, What-If panels | The analyst-facing surfaces for all of the above |
| Demo: SOC-LADDER | Earned authority + conservation veto | The "autonomy is earned, not granted" proof moment |
| Frozen-twin (day-zero vs live) | Real frozen/live comparison service wired | Proof the system learned — what day one would have said |
| No-precedent / frontier | No-precedent detector + coverage-at-safety panel | Abstains honestly on the unseen instead of guessing |

**Value:** frees roughly 30 minutes per alert. *"Your SOC has amnesia — alert #10,000 is scored like alert #1. Ours compounds."*

---

## 4. Trading Copilot

Observation-only, execution-quality analysis (strong / partial / poor-exec / skip), not directional
buy/sell. *Ground truth: live tensor is (5,4,10)=200 — the PD's 5×4×7 core plus the v1.1 options
extension.*

| Feature | What it does | Value |
|---|---|---|
| Domain model | Tensor (5,4,10); penalty ratio 3:1 | Cost model fits trading, where both misses and false alarms hurt |
| Strategy categories (5) | trend_following, mean_reversion, event_driven, income_strategy, scalp_intraday | Judgment specialized per strategy type |
| Decision factors (10) | signal_alignment, market_regime, position_sizing, timing_quality, risk_reward_actual, emotional_indicator, signal_confidence, options_delta_exposure, options_iv_percentile, options_gamma_risk | Scores execution on the dimensions that predict outcomes, including options Greeks |
| Trade import | CSV and broker imports | Works with real fills from Alpaca / IBKR / CSV |
| Trade journal | Entries, reflections, tags, query | Structured, searchable record of decisions and reasoning |
| Signal-trust dashboard | Displays per-signal trust (trust radar) | "My favorite setup is my worst setup" — reveals which signals you over-trust |
| Decision-quality scorer | Scores trade execution quality | Learns your real edge, not self-reported tags |
| Pattern detector | Detects recurring trade patterns | Surfaces the setups and habits that drive outcomes |
| Conservation dashboard | Displays per-strategy safety state | Shows which strategies are safe to scale |
| IKS | Computes institutional knowledge | Accumulated trading judgment, quantified |
| Claim gate | Gates selection-adjusted performance claims | Prevents cherry-picked / overfit metrics — honest numbers only |
| Regime classifier | Classifies market regimes | The copilot knows the current environment |
| Regime mirror / abstention / throttle / rejection | Behavior by regime; abstains under uncertainty; reduces authority after a regime break; scopes rejections | Adapts to non-stationary markets instead of applying a static playbook |
| Promotion engine | Generate / shadow / promote / apply / rollback variants | Safe self-improvement with a rollback path |
| Volatility analytics (+ endpoints) | Sharpe, VRP, rich/cheap, dispersion, tail-bets | The volatility-offensive suite: "is your Sharpe a clustering artifact," "edge or insurance" — worth 4–5× more in volatile markets (modeled) |
| Correlation monitor | Computes correlation and concentration | Catches correlation breakdown before it hits the book |
| Broker router | Status, account, positions, orders, sync | Reads real broker state when broker credentials are configured |
| Observation-only execution gate | Blocks live order execution by default (`TRADING_EXECUTION_ENABLED=false`) | **Enforced** — the copilot analyzes; it does not trade your account unless explicitly enabled |
| Execution analyzer | Compares broker execution outcomes | Measures actual execution quality against intent |
| TradingView webhook | Receives and inspects external events | Ingests external signals |
| Social trader surfaces | List, compare, score-as-another-trader | Benchmark your judgment against other profiles |
| Frontend surfaces | Analysis / Dashboard / Journal / Log-Trade / Performance / Trade-Detail screens; regime, volatility, claim, certificate, dividend, rejection panels | The trader-facing surfaces for all of the above |
| Scenarios T1–T20 *(in progress)* | Signal, scaling, self-knowledge, governance, preservation, volatility scenarios | The documented proof scenarios |

**Value:** *"Tradervue records, Edgewonk tags, QuantConnect backtests — none measure which signals predict YOUR outcomes from verified trades."*

---

## 5. Purchasing Copilot

Food-service purchasing that speaks kitchen language and learns from next-day inventory outcomes.

| Feature | What it does | Value |
|---|---|---|
| Domain model | Tensor (5,4,7); penalty ratio 3:1 | Cost model tuned to stockout-vs-waste trade-offs |
| Categories (5) | protein, produce, dairy, dry_goods, beverages | Judgment specialized per purchasing category |
| Decision factors (7) | expected_demand, day_of_week, weather_forecast, event_flag, historical_waste, supplier_lead_time, price_memory_index | Scores order decisions on the dimensions that actually predict stockouts and waste |
| Ordering & auto-order | Order + QBO-bill queues (`queue`); auto-order status/enable/disable/audit/evaluate (`auto_order`); 3-way invoice match + queue (`match`) | The ordering loop end-to-end, with governed auto-ordering and invoice-leakage catch |
| Par & POS | Par recommendations + status per category (`par`); POS daily sales + profile (`pos`) | Right levels from real sell-through, not guesswork |
| Supplier intelligence | Supplier signal + stats (`signal`); scorecards + IKS (`scorecard`); trust weights + insights (`trust`/`trust_weights`); IKS + scorecard (`iks`) | See which suppliers actually perform, and how far to trust each signal |
| Spend & economics | Spend summary / by-category / by-supplier / alerts / cost-per-cover (`spend`); economic model + ROI (`economic`) | Where the money goes, and the ROI of acting |
| Menu engineering | Menu analysis / alerts / summary (`menu`) | Turns purchasing data into menu-level margin |
| Multi-unit & chain | Multi-unit dashboard / compare / transfer-opportunities (`multi_unit`); chain validate / transfer / status (`chain`) | One dashboard across locations; warm-start a new unit from an existing one |
| Events & delivery | Event plan / history / record (`event`); delivery today / week / consolidation (`delivery`) | Order to the event calendar; consolidate deliveries |
| Commodity pricing | Commodity prices / index / indices / status (`commodity`) | Price memory grounded in real commodity moves |
| Discovery | Purchasing discovery insights + digest (`discovery`) | Surfaces cross-order findings no single report shows |
| Verify & evidence | Verify decision + reason codes (`verify`); evidence summary / decisions / audit-trail / conservation-proof / health (`evidence`); factor display (`factor_display`) | Every recommendation carries reason codes + provenance |
| Regime | Current purchasing situation / regime (`regime`) | Orders adapt to day / weather / event conditions |
| QBO accounting | Vendors / bills / POs / payments / price-history / lead-times / status (`qbo`) | Works from the books the operator already keeps |
| Alerts & cohort | Purchasing alerts (`alert`); cohort status (`cohort_status`) | Surfacing + cohort visibility |
| Control router | Proof ledger, handoff pack, day-zero, legal exposure, frozen twin, promotion, discovery gate, yield-quote audit | Governance and proof surfaces for kitchen managers and owners |
| Compounding ledger | Stores proof and competence state | Makes competence-building visible over time |
| Supplier intelligence | Composes supplier profiles and behavioral metrics | See which suppliers actually perform |
| Supplier-profile accumulator | Accumulates supplier events | Builds supplier history from real orders |
| Synthetic invoice generator | Generates invoice/supplier fixtures | Realistic data for demo and cold-start |
| Regime service | Computes the purchasing situation (day/weather/event) | Orders adapt to the actual conditions |
| Evidence service | Computes evidence and proof states | Every recommendation carries its provenance |
| Frozen Twin service | Compares current vs day-zero scoring | Proof the copilot learned |
| Promotion service | Advances purchasing decision classes | Ordering autonomy earned in stages |
| Signal gate | Gates supplier signals by evidence | Doesn't trust a signal until it's earned |
| QBO connector | Reads QuickBooks Online data (live OAuth; mock fallback) | Works with the books the operator already keeps |
| Frontend surfaces | Analysis / Dashboard / Inventory / Order / Performance screens; beat panels (MirrorOpen, GatedSignalReliability, ProofLedger, SelfPause, TimeToCompetence, NotYet, ContinuityClose) | Kitchen-facing surfaces + proof beats |
| Demo beats | PUR-HERO, PUR-GATE, PUR-PROOF-LEDGER, PUR-REFUSAL, PUR-RAMP, PUR-NOT-YET | Mirror-open, gated reliability, proof curve, self-pause, ramp, day-zero moments |
| PD scenarios P1–P10, S1–S16 *(in progress)* | Foundation, supplier, cross-system, disruption, autonomy, continuity scenarios | The documented scenario library |

**Value:** modeled $190–365K/year for a $15M operator. *"Procurify manages POs, ProcureDesk matches invoices — neither learns which decisions produce better outcomes."*

---

## 6. DataOps Copilot

Data-system monitoring, root-cause triage, self-computation, discovery, and data-product intelligence.

| Feature | What it does | Value |
|---|---|---|
| Domain model | Tensor (6,5,6); penalty ratio 10:1 | High penalty reflects the cost of a bad auto-approve on data quality |
| Categories (6) | schema_change, volume_anomaly, quality_anomaly, freshness_violation, pipeline_failure, transform_drift | Judgment specialized per data-incident type |
| Decision factors (6) | impact_scope, source_reliability, recurrence_frequency, downstream_urgency, data_freshness, business_criticality | Scores triage on the dimensions that separate alerts that matter from noise |
| Context router | Pipeline, alert, system, decision, process context | The triage cockpit's context |
| AE router | Recommendation, impact, pattern, rule, incident, conservation, transfer | Turns triage reasoning into operational fixes and prevented alerts |
| DI router | Profiles, acquisitions, intelligence-map | The data-intelligence surface |
| DI-enrichment router | Source consumers, trust, products | Who uses a source and how much to trust it |
| DI gateway | Trust/verify for external agents | Other agents can ask "can I trust this source" |
| DI: data valuation | Estimates a source's value/ROI from improvement, cost, decision volume, domain (`di/valuation.py`) — **BUILT** | Puts a dollar figure on a data source |
| DI: acquisition advisor | Ranks prospective external sources + recommends acquisitions (`di/acquisition.py`) — **BUILT** | Tells you which data to buy next |
| DI: combination discovery | Finds factor combinations with lift + confidence from decision records — **BUILT** | Surfaces value no single source holds |
| DI: intelligence map v2 | Source nodes, dependency edges, IKS badges, suggestions (`di/intelligence_map.py`) — **BUILT** | The data-intelligence map |
| DI: source profiler | Profiles connector-source trust, freshness, quality, schema (`di/profiler.py`) — **BUILT** | Earned trust per source, not a hand-typed label |
| DI: query service | Approved NL questions → query plan + aggregation + evidence (`di/query_service.py`) — **BUILT** | "What's reliable?" answered with provenance |
| DI: prompt integrator | Parses NL DI requests into an allowlisted query plan (`di/claude_parser.py`) — **PARTIAL** | Guard-railed natural-language access |
| DI: perturbation | Controlled DI perturbations for diagnostics/demo (`di/perturbation.py`) — **PARTIAL** | Stress-tests the DI surface |
| Governance router | Claims, abstention, holdouts, provenance, promotion, frozen-twin | Full governance surface |
| Enterprise router | Enterprise health and process data | Enterprise-stack visibility |
| DI demo beats | Earned-trust, acquisition, abstention, gateway, source-compounding, frozen-twin | The buyer-facing DI proof moments |
| Graph config / AGE store | Centralized graph config + AGE access | Runs on the shared enterprise graph |
| Graph client | Reads pipelines, alerts, systems, dependencies, recurrence, factors | Full graph-backed context |
| Graph enricher | Writes domain-scoped enrichment | Improves the graph without crossing domain boundaries |
| Governance service | Tracks claims, holdouts, abstention, provenance, promotion, twin | The engine behind the governance surface |
| Celonis connector *(live + cache fallback)* | Reads knowledge models, KPIs, process data | Real process-mining input |
| SAP connector *(live + cache fallback)* | Reads POs, invoices, suppliers | Real ERP input |
| Frontend surfaces | Curve / Dashboard / Evidence / Insight / Triage screens; SourceTrust, IntelligenceMap, FrozenTwin, AgentTrustGateway, AcquisitionAdvisor, SourceCompounding, Governance panels | The DI-facing surfaces |
| H1 self-aware data | Fingerprints + per-source trust | Reveals the "most trusted" source is often the least reliable predictor |
| H2 self-combining data | Discovers cross-source combinations | Surfaces issues no single catalog holds |
| H3 self-correcting data *(in progress)* | Self-correction + enrichment | The pipeline improves itself over time |
| H4 self-governing data | Conservation + abstention governance | Safe autonomy on data operations |
| H5 self-valuating data | Valuation + acquisition advice | Turns data quality into an economic decision |
| H6 agent-ready trust | Trust verification for agents | Makes the graph a trust layer other agents can build on |
| Demo: DI-TWIN | DataOps frozen-twin comparison | Proof the copilot learned |

**Value:** modeled $12.9M → $4.3M in 24 weeks. *"Monte Carlo detects, Databricks learns patterns, Alation catalogs, Celonis maps — we do all four, and learn from verified outcomes. Your data gets smarter every day."*

---

## 7. S2P Copilot — Source-to-Pay

Invoice and procurement decision triage, supplier intelligence, governance, and earned automation —
the most extensive backend in the suite. *Ground truth: live tensor is (5,5,8)=200; older PD text
referring to 5×5×7 is stale.*

| Feature | What it does | Value |
|---|---|---|
| Domain model | Tensor (5,5,8); penalty ratio 5:1 | Cost model tuned to procurement exception risk |
| Categories (5) | price_variance, quantity_mismatch, duplicate_risk, contract_gap, format_compliance | Judgment specialized per exception type (the PD's routine/high-value/compliance/sole-source/emergency categories are design-level) |
| Decision factors (8) | match_status, amount_variance_ratio, duplicate_score, supplier_exception_history, payment_terms_impact, commodity_index_correlation, tax_regulatory_compliance, environmental_risk | Scores each exception on the dimensions that predict good resolutions |
| Score router | score, learn, outcome, diagnostics, iks, learning-gate | The core score-and-learn loop |
| Auto-approve router | status, enable, disable, audit, evaluate | Earned auto-approval with a full audit trail |
| Autonomy router | promotion + twin status, advance, rollback, transfer, drift, freeze | Staged, reversible autonomy |
| Demo-beats router | extinction, frozen-twin, what-if, day-zero, confidence, rule-vs-reasoning | The buyer-facing proof moments |
| Evolution router | rules, variants, dimensions, proposal, promotion-check, reset, shadow-results, promoted | Self-improvement, fully surfaced |
| Evidence router | receipts, audit trail, chain integrity, audit pack, template, rules, compliance | Tamper-evident, regulator-ready provenance |
| Discovery router | alerts, disruptions, extended + supplier discoveries, propagation | Finds disruptions and their downstream spread |
| Early-warning router | patterns, warnings, trends, trend-signals | Sees supplier distress before it hits OTIF |
| Enrichment router | execution, summary, alerts, supplier | Enriches decisions with graph context |
| Centroid explorer | export, import, inspect, drift, DK-weights, ranking, contribution | The learned judgment is auditable and portable |
| Insight router | fingerprint, similarity, process context, cross-graph, process signals | Deep decision insight, incl. process signals |
| Ledger router | timeline, summary, IKS trajectory, conservation history | The compounding record over time |
| Novelty router | status, history, rate, auto-pause, triggered-decisions | Novel exceptions trigger caution, not a guess |
| Proposals router | create, retrieve, confirm, override, audit | Human-in-the-loop proposal workflow |
| Simulation router | scenarios, what-if, impact summary, simulation, batch | Rehearse decisions and disruptions before acting |
| Situation router | context for a decision | Every decision scored in its full context |
| Supplier router | profiles, history, clustering, declining suppliers, heatmaps, correlations | Complete supplier intelligence |
| Performance router | trajectory, what-if, summary | Track and interrogate performance over time |
| Preview router | isolated preview: queue, conservation, compounding, suppliers, config | A safe sandbox that never touches production learning |
| Process fusion | Combines procurement + process-mining signals | "Where → what → why → which decision" — the strongest wedge in the Celonis room |
| Payment router | strategy, portfolio, behavior | Captures early-pay discounts and protects OTIF |
| PVG router | variant, impact, leakage, cycle-time | Quantifies process-variant leakage |
| Control tower | Classifies intents, manages queues | Routes the right exception to the right path |
| Clustering router | clusters, similarity | Groups suppliers/exceptions for consolidation |
| Financial router | financial impact, trends | Puts a dollar figure on decisions |
| Compliance router | screening + reports (UFLPA / CSDDD / Scope-3) | Regulator-ready supply-chain compliance |
| Factor proposer | Analyzes and proposes new factors | The judgment model is extensible |
| Lead-time router | summaries, suppliers, alerts | Lead-time intelligence |
| Optimizer router | Exports and validates optimizer state | Feeds Gurobi / OR-Tools optimizers with learned parameters |
| Services | graph reader, supplier intelligence, supplier-profile accumulator, synthetic invoices, situation traversal | The engines behind the routers |
| Frontend surfaces | Dashboard / Evidence / Insight / Performance / Suppliers / Triage screens; FrozenTwin, WhatIf, DayZero, ExtinctionTimeline, ConfidenceBand panels | The procurement-facing surfaces |
| Scenarios | ROUTINE-01, SOLE-SOURCE-01, PRICE-SPIKE-01, LEARN-01, SANCTIONS-01, COMPOUND-01 | The documented decision scenarios |
| Demo beats | S2P-EXTINCT, S2P-TWIN, S2P-WHATIF, S2P-DAY0, S2P-CONFIDENCE | Exception extinction, learning proof, counterfactual, readiness, confidence-band moments |
| S2P CLI *(not built — HTTP routes only)* | (Planned) invoice generation, scoring, learning, reporting commands | HTTP score/learn routes exist today; a CLI is not built |

**Value:** modeled $680K/year in recovered leakage + $340K in early-pay discounts. *"Coupa doesn't learn, Ariba doesn't learn, Celonis doesn't fix — we learn, fix, prove safety, and transfer."*

---

## 8. Connectors, Data Sources & Delivery

The suite ships with **31 connectors**. Most run **live-with-fixture-fallback**: configured to the
customer's live systems per deployment (via environment), with fixtures for instant demo and day-zero.
This is why a new deployment demonstrates immediately and sharpens as real sources are wired.

| Component | Connector(s) | External system | Live/fixture | Value |
|---|---|---|---|---|
| Shared (copilot-sdk) | Snowflake, dbt, Airflow | Warehouse, transform, orchestration | live w/ fixture fallback | Any copilot reads the customer's existing data stack — warehouse metadata, transform lineage, pipeline freshness |
| SOC | Sentinel (OAuth), NVD, MITRE ATT&CK, GreyNoise, Pulsedive, CrowdStrike *(mock)* | SIEM + public threat intelligence | live (CrowdStrike mock) | Alerts are enriched with **live threat context** — SIEM signals plus real-world TI feeds — not static rules |
| Trading | Alpaca (market + orders), IBKR, YFinance, CSV, TradingView webhook | Broker + market data + signals | live (CSV/YF fixture-capable) | Real fills and market data from the trader's actual broker and feeds; live inbound signals |
| Purchasing | QBO (OAuth), Toast POS, FRED, weather *(MockWeather today; OpenMeteo pending)* | Accounting, POS, commodity, weather | live w/ fixture fallback | Reads the operator's actual books (QBO), POS sales (Toast), and commodity-price signals (FRED) |
| DataOps | SAP S/4HANA (OData), Celonis (process/KPI + EMS), Schema.org DQ benchmarks, + Snowflake/dbt/Airflow | ERP + process mining + warehouse stack | live w/ fixture fallback | Grounds triage in the customer's **real data + process stack** — SAP lineage, Celonis process reality |
| S2P | SEC EDGAR, openFDA, SupplierIntel (SEC+FDA) | Regulatory + supplier risk | live | Folds **live regulatory and supplier-risk intelligence** (enforcement actions, filings) into supplier scoring |

**Factor data sources (honest state).** Factors compute from three sources — the governed graph,
these connectors, and decision history — and **fall back to fixtures when a live source isn't yet
configured**. Today most factors resolve fixture-backed; the computation is real, the live-data wiring
is per-deployment. A handful of SOC factors (asset criticality, time anomaly) already resolve live
from the graph. (Note: the weather factor references OpenMeteo but currently runs on a fixture
provider — live weather wiring is pending.)

**Delivery (a real gap).** Outbound today is limited to **exports** — Purchasing audit export, S2P
centroid/optimizer export (JSON/CSV), Trading decision export — plus Trading's **live order execution**
via Alpaca. There is **no push-notification layer** (email / Slack / Teams / PagerDuty). For a
detect-and-score product, that's a roadmap gap: copilots surface decisions in-app but can't yet push
them to where teams work.

---

## 9. Enterprise & Trust Posture

Honest state from a code scan. The isolation, audit, and recovery foundations are real; identity,
tenancy, and hardening are partly built (strongest in SOC) and partly roadmap. This states what a
buyer can rely on today versus what's coming — the credible version, not a checklist of aspirations.

**Foundations in place**

| Capability | Status | Today |
|---|---|---|
| Data isolation | ✅ Present | Domain-scoped graph — SOC domain predicates, domain-prefixed decision IDs (TRD-/PUR-/DOPS-/S2P-), shared-graph pair authorization. Each copilot's data is separated on the shared graph. **The strongest enterprise capability.** |
| Tamper-evident audit | ✅ Present (SOC, S2P) | SHA-256 hash-chained decision/outcome records with chain verification, audit export, and epoch archival |
| Backup / restore / migration / rollback | ✅ Present | SQLite↔AGE migration, archive reconciliation, outbox replay, Trading CLI backup/restore, S2P entity migration |
| Health & observability | ✅ Present | `/health` endpoints, metrics routes, connector health checks, structured logging, hot-path caching |
| Secrets & config | ◐ Partial | Env / .env / config-module loading across all components. No Vault/KMS or rotation yet |

**Identity & access — real, but strongest in SOC (not yet suite-wide)**

| Capability | Status | Today |
|---|---|---|
| Authentication | ◐ Partial | SOC: SAML login + JWT cookie validation. Not uniform across the other components |
| Authorization / RBAC | ◐ Partial | SOC: admin-role enforcement on admin + mutation paths. No shared suite-wide permission model yet |
| SSO (SAML / OIDC) | ◐ Partial | SAML wired for SOC; no suite-wide SSO/OIDC |
| Multi-tenancy | ◐ Partial | Domain isolation is real; full tenant identity, lifecycle, and tenant-scoped policy are not yet built |

**Hardening & governance — roadmap**

| Capability | Status | Today |
|---|---|---|
| Encryption | ◐ Partial / priority | Some transport config exists but includes `sslmode=disable`; no app-level TLS termination or at-rest/field encryption. **Priority hardening item.** |
| PII governance | ◐ Partial | Deletion, archival, and audit hashing exist; no suite-wide PII classification, retention schedule, or right-to-be-forgotten workflow |
| Deployment bundle | ◐ Partial | Python packaging + setup/migration scripts; no unified Docker/compose/VPS bundle yet |
| API governance | ◐ Partial | FastAPI OpenAPI + typed routes; no consistent URL versioning or shared error envelope |
| Performance instrumentation | ◐ Partial | Benchmark + latency helpers + `cached_static` hot-path; no uniform p95/tracing dashboards |
| Inbound rate limiting / quotas | ✗ Absent | No inbound rate limiter or tenant quota (only outbound connector pacing). **Build item.** |

**Bottom line for a buyer:** the platform can *isolate* your data on a shared graph, *prove* what it
did (tamper-evident audit), and *recover* (backup/migration/rollback) today. Before a broad enterprise
rollout, the work that remains is **suite-wide caller auth + tenant-aware policy**, **inbound rate
limiting**, and **encryption hardening** — all tracked, none hand-waved.

---

## 10. Product vs Demo Instrumentation

A code classification separates what a customer operates from what only stages a demo. Of everything
scanned, **the overwhelming majority is product** — the demo layer is small and cleanly separable.

| Class | Count | What it is |
|---|---|---|
| **Product** | ~753 | Routers, services, screens, and panels a customer operates in normal use |
| **Demo instrumentation** | 29 | Sales/proof "beat" surfaces — not customer features |
| **Dev/infra** | ~268 | Migration, seeding, benchmarks, experiments, test tooling |

**The 29 demo-only items** (kept out of the product feature surface): the `*_beats.py` routers
(SOC `soc_demo_beats`, S2P `s2p_demo_beats`, DataOps `di_demo_beats`, Purchasing `learning_beats`,
Trading `regime_beats` + `volatility_beats`), the "beat"/proof panels (`PurchasingBeatPanels`,
`PurchasingProofPanel`, `EarnedProofPanel`, `DemoBeatPanels`, `ProvenanceBadge`, `FrozenTwinControlPanel`),
`backend/demo/s2p_demo.py`, and the SDK demo scripts (`hero_moments`, `loom_gauntlet`,
`demo_truth_preflight`, `demo_warm_start`, `demo_cross_copilot_finding`). Everything else in §1–§7 is
product.

*Status note (code-verified): the frozen-twin, no-precedent, and campaign capabilities above are
**built product** — only their "beat" presentation endpoints are demo surfaces. Trading's live order
execution is **blocked by default** (`TRADING_EXECUTION_ENABLED=false`); the copilot analyzes, it does
not trade your account unless you explicitly enable it.*

---

## 11. Personas & Jobs-to-be-Done

Who each copilot is for, and the one core job each persona hires it to do. Two roles recur on every
copilot — the **operator** who uses it daily and the **economic buyer** who signs for it — alongside
two cross-cutting roles at the platform level. The workflows in §11.2 trace one job end to end, with
each step mapped to a real feature from §0–§10.

### 11.1 Personas

| Copilot | Operator (daily user) | Economic buyer | What the buyer is actually buying |
|---|---|---|---|
| SOC | Tier 1–2 SOC analyst / triage lead | CISO / SOC manager | Analyst time back, provable safe auto-close, judgment that survives turnover |
| Trading | Active / prop trader, trading desk | Desk lead / risk lead / CIO | An execution-quality edge from *their own* verified trades, with behavioral guardrails and zero execution risk |
| Purchasing | Kitchen manager / buyer | Owner / operator / multi-unit GM | Margin (less waste, fewer stockouts), continuity across staff churn, a head start for each new location |
| DataOps | Data engineer / on-call / DQ analyst | Head of data / CDO | Fewer false alerts, knowing which sources to trust, data-quality cost down |
| S2P | AP / procurement exception handler | CPO / controller / VP procurement | Recovered leakage, early-pay capture, recurring root causes eliminated, regulator-ready compliance |

**Cross-cutting roles (platform level):**
- **Economic buyer — CFO / COO / CIO.** Buys the compounding moat (§0.6), one safety law across
  everything (§0.3), and one governed cross-domain graph (§0.1). The pitch is portfolio-level: value
  compounds and switching cost grows.
- **Technical evaluator — security / data architect.** Validates before purchase. Cares about the
  provenance backbone (§0.4), data isolation and the honest enterprise posture (§9), and the "what we
  don't claim" boundaries. This persona is *won by candor*, not by claims.

### 11.2 Jobs-to-be-Done — one workflow per copilot

Each workflow is one job, traced end to end. Feature names are the shipped ones from §1–§10.

**SOC — "Triage this alert, and make the whole queue smarter."**
1. Alert arrives, enriched from the graph and **live threat intel** (Sentinel, NVD, MITRE ATT&CK, GreyNoise, Pulsedive).
2. Scored on six factors against your verified triage history; the **trust-trap fingerprint** flags the factor the team over-trusts.
3. Related alerts fold into one **campaign** (stable identity + CONTINUES-edge chaining) — the slow multi-signal attack surfaces.
4. Analyst confirms or overrides; a **plain-language explanation** and **what-if** show exactly why the score would flip.
5. The decision lands on the **tamper-evident audit chain**, and (where learning is enabled) the model **learns** from it.
6. Over time the **authority ladder** earns conservation-gated auto-close per category, and the **frozen twin** proves it actually improved.
→ *Outcome: less time per alert, auto-close you can prove is safe, continuity through turnover.*

**Trading — "Learn which of my setups actually execute well."**
1. Import fills from **Alpaca / IBKR / CSV**.
2. The **execution-quality scorer** grades each trade (strong / partial / poor-exec / skip) against your verified outcomes.
3. The **signal-trust radar** reveals which signals you over-trust ("my favorite setup is my worst setup").
4. **Behavioral detection** flags tilt / FOMO / revenge; the **regime classifier** adapts edge and sizing to the market state.
5. The **volatility suite** tests whether your Sharpe is a clustering artifact and whether premium is edge or insurance.
6. **Conservation-gated promotion** scales paper → small → full only when quality clears — and live execution stays **blocked by default** (observation-only).
→ *Outcome: a real execution edge from your own trades, behavioral guardrails, no execution risk.*

**Purchasing — "Order the right amount and protect margin."**
1. **POS, weather, event, and commodity** signals build the order context (Toast, FRED, weather).
2. Scored **order-as-planned / more / less / skip** against verified next-morning inventory.
3. The **trust-trap fingerprint** shows the factor you lean on (weather) may be the one that misleads.
4. **Par intelligence + predictive par** recommend levels; **3-way match** catches invoice leakage.
5. **Waste tracking + menu engineering** turn the data into margin; **chain transfer** warm-starts a new location.
6. The owner sees the **proof ledger** (competence curve) and an **audit export**.
→ *Outcome: fewer stockouts and less waste, continuity across churn, a head start per new location.*

**DataOps — "Triage pipeline alerts and know which sources to trust."**
1. A pipeline alert arrives with graph-first context (**SAP, Celonis, Snowflake, dbt, Airflow**).
2. Scored on six factors against verified outcomes; **self-aware data** exposes per-source trust (the "most-trusted source is least reliable" insight).
3. **Cross-graph / combination discovery** finds cross-source issues; **NL query** answers "what's actually reliable?"
4. The analyst resolves; **operational evolution** turns that reasoning into a pipeline fix or a prevented alert.
5. **Data valuation + acquisition advisor** put a dollar figure on sources and recommend what to acquire next.
6. **Governance** holds the line — OOD **abstention**, the conservation gate, and a **frozen-twin** proof.
→ *Outcome: fewer false alerts, the right sources trusted, data-quality cost down, root-cause reduction.*

**S2P — "Stop the same exceptions recurring, and recover the leakage."**
1. An invoice / exception arrives; **process-tech fusion** weaves Celonis process-mining and SAP into the score.
2. Scored on eight factors against verified resolution outcomes; the **centroid explorer** keeps the judgment auditable.
3. **Supplier intelligence + early warning** flag distress before it hits OTIF; **SEC EDGAR / openFDA** feed regulatory risk.
4. **Payment strategy + working-capital** optimize DPO and early-pay; the **compliance module** screens UFLPA / CSDDD / Scope-3.
5. **Conservation-gated shadow auto-approve** acts only inside the safety bound; the **evidence chain** keeps it audit-ready.
6. The same five root causes get fixed permanently, and **disruption simulation** rehearses the next shock.
→ *Outcome: recovered leakage + early-pay capture, recurring root causes eliminated, regulator-ready.*

---

## 12. Differentiators vs Table-Stakes

Not every feature wins a deal. This separates the **differentiators** — defensible, validated, few or
no competitors, the reasons to buy *this* — from **table-stakes**, the parity capabilities every
serious competitor also has. Table-stakes still matter: their *absence* loses deals. But they don't
win them. The differentiators do.

**Legend:** ◆ Differentiator (moat) · ● Table-stakes (parity)

### 12.1 ◆ Differentiators (the moats)

All of §0 is differentiators by construction; the per-copilot ones are added below. Complete list,
with why each resists copying and where it lives.

| ◆ Differentiator | Where | Why it's defensible |
|---|---|---|
| Compounding centroid learning from verified outcomes | §0.1, §1–§7 | Requires the whole verified-decision loop on a governed graph — not a model you can fine-tune once |
| One conservation law (α·q·V ≥ θ_min), deployed ×5 | §0.3 | A *proved* safety bound applied platform-wide; competitors ship guardrails, not a conservation law |
| Provenance & substantiation backbone (evidence tiers, no-sample-in-headline, claim registry) | §0.4 | A discipline threaded through every surface — very hard to retrofit onto an existing product |
| σ noise-fingerprint / trust-trap (signal-confidence inversion) | §0.4, per-copilot | Outcome-conditioned variance, not feature importance — a different quantity than anyone else computes |
| σ⊥μ two-engine separation (proved, first-order exact) | §0.4 | Novel math; the fingerprint and judgment engines are provably separable |
| Robust-to-bad-teaching: governed sidecar + AE-DECISION rollback + SA-ABSTAIN | §0.5 | *Validated* adversarial defense (57%→14% non-recovery; 100% OOD detection) — evidence, not a promise |
| AgentEvolver: shadow-test + REJECT + conservation-gated rollback | §2, per-copilot | Self-improvement that can *refuse* and roll back — most "auto-tuning" cannot |
| Cross-domain warm-start transfer (conservation-gated) | §0.2 | Judgment learned in one domain accelerates the next — structurally impossible for single-domain tools |
| One governed knowledge graph across 5 copilots (cross-domain traversal + discovery) | §0.1 | The substrate for cross-domain findings no stitched-together stack can produce |
| Frozen-twin: day-zero vs live proof of learning | §0.4, SOC/S2P/Purchasing/DataOps | Verifiable "here's what day one would have said" — a proof, not a marketing curve |
| IKS + switching-cost quantification | §0.6 | Turns accumulated firm-specific judgment into a measurable moat that grows weekly |
| Operational evolution / self-computation (Level 3) | §6, §8 | The platform reasons about itself and fixes operations — beyond detect/automate |
| Tamper-evident SHA-256 decision audit chain | §0.4, SOC/S2P | Novel application: every automated decision is cryptographically verifiable |
| Named profiles from the fingerprint | per-copilot | Novel UX — "THE RESEARCHER / HISTORIAN / PATTERN MATCHER" from real variance |
| Multi-domain compounding SDK (one scorer protocol, 5 copilots) | §0, §2 | The platform play itself — one engine proven across five domains |
| S2P Process-Tech Fusion (Celonis + SAP + learning in one graph) | §7 | Domain moat: process-mining woven into the score, not bolted alongside |
| Volatility-offensive trading (per-regime, per-trader accuracy) | §4 | Domain moat: "rotate, don't reduce" grounded in the trader's own verified outcomes |

*Not on this list, on purpose:* the retracted claims — DiagonalKernel "+13pp over L2," γ>1
"recovery accelerates" in production, and the "+28pp" cross-deployment transfer magnitude. They are
withdrawn, not differentiators (see §0.2, §9.2, the science grounding). Cross-domain transfer stays a
differentiator as **warm-start acceleration**, without the magnitude claim.

### 12.2 ● Table-stakes (necessary, not differentiating)

Every serious competitor has some version of these. Ship them to clear the checklist — don't pitch
them as the reason to buy.

| ● Capability | Note |
|---|---|
| Integrations / connectors (CSV, Alpaca/IBKR, QBO, SAP, Celonis, Snowflake/dbt/Airflow, threat-intel feeds) | Everyone integrates. The moat is *learning which of those signals predict outcomes*, not the connection |
| Dashboards & per-copilot screens | Table-stakes UI |
| Alert queue / triage list | Every SOC/DataOps tool has one |
| Audit export & reporting (weekly report, JSON/CSV export) | Expected; note this is the only outbound path today (no push layer — see §8) |
| Natural-language explanation of a decision | Common; the *counterfactual faithfulness* behind it is the differentiator, not the prose |
| CRUD: journals, item/supplier profiles | Baseline record-keeping |
| Standard analytics (spend dashboard, correlation, regime *detection*) | Parity as features; the differentiator is scoring them against *verified outcomes* |
| A "score" / recommendation surface | Many tools score; scoring against *your verified decisions* is the moat |
| Health endpoints / basic observability | Operational baseline (§9) |

### 12.3 Rule of thumb (for the room)

- **Lead with §0** (the differentiators). Use table-stakes to pass the checklist, never to persuade.
- **Never dress a table-stakes feature as a differentiator.** "We integrate with SAP" is parity;
  "we learn which SAP-sourced signals predict outcomes" is the moat. Same connector, different claim.
- **Keep retracted claims out of the differentiator column entirely.** A withdrawn claim in a pitch is
  a credibility loss with the technical evaluator — the exact persona won by candor (§11.1).

---

## 13. Competitive Landscape

Every competitor here holds real strengths. The gap that matters is never that they have nothing — it's
that none of them **compound**. This is the honest map of where each stops.

### 13.1 Three generations of operational AI

- **Gen 1 — Faster playbooks (static).** SOAR (Torq, Swimlane, Tines), RPA (UiPath), rule-based
  data-quality. Day 365 = Day 1.
- **Gen 2 — AI analysts & agents (stateless).** AI-SOC (Dropzone, Prophet, 7AI, Command Zero),
  autonomous procurement (Zycus, Coupa, SAP Joule), learning-flavored DQ (Monte Carlo); the big
  platforms (CrowdStrike, Palo Alto, Microsoft) run sophisticated blends of Gen 1+2. Genuinely
  capable — and case #10,000 is handled like case #1.
- **Gen 3 — Compounding Intelligence.** A governed context graph + write-back from verified decisions
  + two levels of institutional judgment. Cannot be created by adding AI to a Gen 1/2 product.

### 13.2 Where each competitor stops

| Competitor | Real strength | Where it stops | What CI adds |
|---|---|---|---|
| Palantir AIP | Strong ontology + agent tooling | Agents built/deployed statically; execute predefined workflows | Runtime evolution + situation analysis + compounding |
| SAP Joule | 1,300+ skills, deep ERP | Ecosystem-locked; doesn't learn from production; can't reason across SAP/non-SAP | Cross-domain judgment that compounds |
| Zycus Merlin *(2026 Gartner S2P Leader)* | Autonomous contextual agents, tail-spend | Doesn't demonstrate learning firm judgment from verified outcomes under a conservation law | Provable decision #10,000 > #1; judgment survives the analyst's departure |
| Process-mining (Celonis) | Process graph, agent context, orchestration | Models the *process*, not how you *decide*; doesn't close-and-learn the fix | Sits on top; adds the compounding-judgment layer — "Celonis sees *where*, ERP sees *what*, fusion sees *why*" |
| Data-quality (Monte Carlo, Unity Catalog) | Breakage detection, lineage | No per-factor decision quality from outcomes; can't say which source to trust *for a decision* | Source-trust from verified outcomes; which data to buy next |
| LangChain / DIY | Flexibility, no lock-in | No governed infra, no runtime evolution, no accumulated context | Governed compounding loop; the human stops being the learning mechanism |
| Snowflake / Databricks | Data gravity | Read-path, not write-path — can store context, can't compound it | Write-path judgment that compounds |
| Agent-memory (Mem0, Zep, MAGMA, Letta) | Statefulness for agents (episodic/semantic/procedural) | No per-factor decision quality, no conservation law, no noise fingerprint, no cross-domain transfer | **Judgment memory — the 4th type** |

### 13.3 Four questions that separate them

Put these to any vendor that claims to learn:
1. After 10,000 decisions — show the compounding curve; is the *rate* of improvement itself rising?
2. When my best analyst leaves — does decision #10,001 reflect her judgment?
3. Faced with a case it hasn't earned — can it say "not yet" and abstain?
4. When the regime breaks — does it reduce its own autonomy, or keep firing?

None is answerable by retrieving a precedent, tuning toward last month's feedback, or maximizing one metric.

### 13.4 Read, route, or reshape (the graph-native axis)

There isn't one "graph" but three, and only one compounds:
- **READ** — a knowledge/context graph you traverse to *retrieve* (GraphRAG, Neo4j GraphRAG, LlamaIndex, Anthropic KG cookbook). Stops at retrieval; no write-back from outcomes.
- **ROUTE** — a graph of agents to *dispatch* work (LangGraph, CrewAI, AutoGen, Kimi K3). Stops at orchestration; state is conversation, not learned judgment.
- **RESHAPE** — a judgment graph (CI): decision-prototypes as learned geometry, reshaped from verified outcomes. Adds judgment memory, conservation-bounded autonomy (incl. the validated **42.5pp** adversarial-robustness result and the σ⊥μ separation), and compounding.

The pattern: READ treats the graph as a store; ROUTE as a topology; only RESHAPE rewrites it *from* verified decisions.

### 13.5 Four memory types — the judgment gap

Episodic (Mem0, Zep), Semantic (knowledge graphs), and Procedural (skill libraries) are the three the
field has built (CoALA; Sumers et al., 2023). The fourth, which none have, is **judgment memory** —
centroid geometry + noise fingerprint + conservation. Only judgment memory detects **signal-confidence
inversion**: the factor practitioners trust most is often the noisiest.

- **SOC:** device trust *feels* reliable; threat intel carries the signal.
- **Trading:** conviction *feels* certain; research depth carries the signal.
- **Purchasing:** weather *feels* relevant; historical waste carries the signal.
- **DataOps:** source reliability *feels* trustworthy; data freshness carries the signal.

---

*One property runs through all seven components: they learn from verified human decisions, prove
automation is safe before enabling it, and compound that judgment in a single governed graph.*
**"Your AI is as smart today as the day you installed it. Ours compounds."**
