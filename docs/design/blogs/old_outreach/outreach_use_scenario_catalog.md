# Compounding Intelligence — Use Scenario Catalog
## Every Scenario, Structured for Impact

**Date:** May 21, 2026 · **Version:** 1.0
**Purpose:** Single reference for all outreach use scenarios.
**Structure per scenario:** Domain → Industry Data → Problem →
Without → With → Why Nobody Else → One-Liner.
**Selection:** Top scenarios per copilot chosen for: recognizable
pain, quantifiable impact, architectural uniqueness, memorability.

---

## DATAOPS (5 scenarios)

---

### DO-1: THE ALERT TREADMILL

**Domain:** DataOps · **Buyer:** CDO, Head of Data Engineering
**Industry data:** Gartner: poor data quality costs organizations
$12.9M/year on average. 73% of data leaders rank data quality as
the primary barrier to AI success (Gartner 2025). 59% of
organizations don't measure data quality regularly.

**THE PROBLEM:** An $800M industrial manufacturer runs SAP S/4HANA,
Celonis, Snowflake, and Databricks. Monte Carlo monitors data
quality. 2,400 alerts per day. 45% are noise — schema version
bumps, partition changes, expected seasonal drops. 160 data
engineers investigate all 2,400 because the system can't
distinguish signal from noise. Annual exception cost: $12.9M.

**WITHOUT:** Engineers spend 40% of time on triage. Same patterns
every month. Monte Carlo detects anomalies but doesn't learn which
ones MATTER from triage outcomes. Alert count stays flat: 2,400/day
in January, 2,400/day in December. The system never gets smarter.

**WITH:** Month 3: system learned which patterns are noise from
1,500 verified triage outcomes. Auto-resolve 35%. Month 6: 48%.
Month 12: 55%. Alerts: 2,400 → 1,080/day. Exception cost: $12.9M
→ $4.3M. Engineers reclaimed: equivalent of adding 22 headcount.
Conservation law proves each expansion step — the system pauses
itself if quality dips. Every fix prevents future alerts. Every
transfer multiplies the value of every past fix.

**WHY NOBODY ELSE:** Monte Carlo detects. Engineers fix. The fix
is discarded — not fed back into the detection model. Next month,
same alert, same investigation. Databricks learns data PATTERNS
(statistical). We learn from triage OUTCOMES (judgment). Building
an outcome loop into Monte Carlo is a 2-year architectural rebuild.

**ONE-LINER:** *"2,400 alerts/day for 18 months. Same number.
Your system has amnesia."*

---

### DO-2: THE CONSULTANT WHO LEFT

**Domain:** DataOps · **Buyer:** CDO, CFO
**Industry data:** 42% of enterprises scrapped AI initiatives last
year — 2.5× increase (S&P Global). 95% of custom GenAI tools never
reached production (MIT NANDA).

**THE PROBLEM:** CDO hired a consultant. 3-month engagement. Found
$4.2M/year in data quality exception costs. Actionable
recommendations. Implemented them. Consultant left. 12 months
later: $3.9M. The savings didn't stick because the findings lived
in the consultant's slides, not in any system the engineers use
daily.

**WITHOUT:** Consultant's findings evaporate within 12 months.
$45K engagement repeated every 18 months. Same findings each time.
"We've been doing this dance for 5 years," the CDO says. No system
captures the consultant's knowledge. The slides sit in SharePoint.

**WITH:** Deploy. System learns which data sources to trust from Day
1. DiagonalKernel computes per-source reliability from verified
outcomes — not from rules or consultant interviews. After 500
verified decisions: "SAP master data: 99% reliable. Salesforce
opportunity stages: 72% — sales team inconsistent." These findings
are encoded in centroid geometry. They don't evaporate. They
compound. IKS = 54 at 6 months. Every quarter, the savings are
larger than the previous quarter. No consultant needed again.

**WHY NOBODY ELSE:** The consultant's knowledge is judgment — which
data to trust, which patterns matter, which fixes work. No data
quality tool captures judgment. They capture rules. Rules are
static. Judgment compounds. Our centroid geometry IS judgment
accumulated from verified outcomes.

**ONE-LINER:** *"The consultant found $4.2M. Left. It came back.
Our system doesn't leave."*

---

### DO-3: THE DATA INTELLIGENCE MAP

**Domain:** DataOps · **Buyer:** CDO, VP Data Platform, VC
**Industry data:** Companies spent $1.5 trillion on AI in 2025
(Gartner). 60% report little to no value from AI investments.

**THE PROBLEM:** $5B manufacturer. 45 data pipelines, 12 source
systems, 40 data engineers. Nobody can answer: "Which of our data
sources is actually reliable? What does our data combine well with?
What additional data would make our decisions better?" The data
estate is a black box. Engineers know pieces. Nobody sees the whole.

**WITHOUT:** Data catalog (Alation/Collibra) describes what exists.
Doesn't know what's RELIABLE. Monitoring (Monte Carlo) catches
anomalies. Doesn't know which MATTER. Integration (Fivetran) moves
data. Doesn't know which COMBINATIONS create value. Each tool sees
one dimension. Nobody sees the intelligence.

**WITH:** Day 1: scattered gray dots on the Intelligence Map. No
connections. IKS = 0. Month 6: clusters forming. Finance data
bright (well-verified). Supply chain data has red lines
(contradictions between SAP and supplier self-reports). First gold
dotted line: "Connect shipping transit data → delivery prediction
+34pp. Cost: $12K/year. ROI: 17×." Month 12: dense, alive,
pulsing network. $1.2M in unrealized value from 3 undiscovered
data combinations. Every data asset has a reliability profile,
consumption pattern, and economic value estimate. New employees see
the ENTIRE intelligence of the organization's data on one screen.

**WHY NOBODY ELSE:** The Intelligence Map requires: (a) per-source
trust weights from verified outcomes (DiagonalKernel), (b) cross-
graph correlation discovery (cross-graph attention), (c) economic
valuation of potential combinations. No platform has all three. A
data catalog describes. We ILLUMINATE.

**ONE-LINER:** *"Day 1: your data is silent. Month 12: it glows
with intelligence."*

---

### DO-4: CROSS-GRAPH — THE $604K NOBODY SAW

**Domain:** DataOps · **Buyer:** CDO, COO, VP Data Platform
**Industry data:** The 1-10-100 rule (Sirius Decisions): $1 to
verify at entry, $10 to clean later, $100 if ignored. In modern
real-time stacks, bad data multiplies costs per connected system.

**THE PROBLEM:** A major manufacturer. SAP S/4HANA pipeline. Celonis
shows a 42-minute bottleneck in invoice matching — 70% of pipeline
runtime. SAP shows 340 purchase orders affected. Neither system
explains WHY. Neither recommends a fix. The direct cost is
$8,400/day. But the cascade multiplier is 2.4× — 7 downstream
systems affected. Total exposure: $604K/month.

**WITHOUT:** Celonis shows WHERE the bottleneck is. SAP shows WHAT
is affected. Nobody connects them. An engineer spends 3 hours
investigating, discovers the root cause manually: MATKL_V2 schema
change increased join fanout 9×. Supplier Aster invoices are 3.1×
slower because they use 94% of the new material codes. This finding
requires SAP supplier data + Celonis activity timing + operational
schema change data. No single system has all three.

**WITH:** Cross-graph traversal in 4 seconds: "Bottleneck BECAUSE
MATKL_V2 schema change → 9× fanout. Supplier Aster: 94% new codes
= 3.1× slower. Fix: pre-join filter. Estimated: 42 → 4 min.
Confidence: 0.87 (based on 3 similar past fixes). Conservation:
GREEN." Three weeks later, billing_api has the same pattern.
Auto-resolved in 15 minutes. 12× faster.

**WHY NOBODY ELSE:** The $604K finding requires computation across
THREE systems simultaneously: SAP transactions × Celonis process
activities × operational schema changes. No competitor puts all
three in one graph with one learning engine. Adding SAP data to
Celonis doesn't give you learning. Adding Celonis to Monte Carlo
doesn't give you reasoning.

**ONE-LINER:** *"$604K/month. Celonis saw where. SAP saw what.
Neither saw why. We did."*

---

### DO-5: THE TRUST LAYER EVERY AGENT NEEDS

**Domain:** DataOps (Platform) · **Buyer:** CTO, VP Data, VC
**Industry data:** Databricks State of AI Agents 2026: multi-agent
systems grew 327%. 80% of databases now built by AI agents. By
2028, 33% of enterprise applications will include agentic AI
(Gartner).

**THE PROBLEM:** AI agents are making autonomous decisions on data
they can't evaluate. Agent queries Table A — is it reliable? Which
columns? Under what conditions? No agent platform provides data
trust scores. Every agent trusts every data source equally. When
the data is wrong, the agent makes a wrong decision with high
confidence.

**WITHOUT:** Databricks Genie writes code on any table. Doesn't
know if the table is reliable. LangChain chain queries 4 sources.
Treats all equally. No agent has the ability to say "this source
is 94% reliable for trending analysis but NOT safe for financial
reporting because column 'amount' has 8% variance."

**WITH:** Trust API: `GET /api/dataops/trust/sap_s4hana` →
`{"overall_trust": 0.94, "conservation_status": "GREEN",
"safe_for_autonomous_use": true, "column_trust":
{"customer_id": 0.99, "satisfaction_score": 0.14}}`. Any agent —
Databricks, LangChain, custom — calls our API before consuming
data. The agent adjusts its confidence BEFORE it acts. Per-column,
per-source, per-consumer trust. Learned from verified outcomes,
not configured by rules.

**WHY NOBODY ELSE:** Every agent vendor (Databricks, LangChain,
CrewAI, AutoGen) needs a trust layer. None build one. Building it
requires: verified outcome loop → per-source DiagonalKernel
weights → conservation status. This is our entire architecture
repurposed as infrastructure. We're not just a copilot. We're the
trust layer.

**ONE-LINER:** *"80% of databases built by agents. Zero agents
know which data to trust. We fix that."*

---

## SOC — SECURITY OPERATIONS (4 scenarios)

---

### SOC-1: THE AMNESIA PROBLEM

**Domain:** SOC · **Buyer:** CISO, VP Security Operations
**Industry data:** Average SOC analyst handles 20-25 alerts per
shift. Mean investigation time: 35 minutes. Analyst turnover:
30%/year (Ponemon). Global shortage of 3.4 million cybersecurity
professionals (ISC²).

**THE PROBLEM:** Mid-cap financial services firm. 50 Tier 1 alerts
per day. Each takes 35 minutes. Five browser tabs — VirusTotal,
GreyNoise, Pulsedive, MITRE ATT&CK, internal wiki. The fusion
happens in the analyst's head. She builds pattern recognition over
3 years: "Source X and behavior Y together always mean Z."
Alert #10,000 is processed with the same logic as alert #1. The
system never learns.

**WITHOUT:** Analyst leaves (30% turnover). Replacement has the
same tools, same SIEM, same playbooks. Zero knowledge transfer.
The patterns she built over 3 years — which IOC combinations
matter, which sources are noisy, which alert types escalate —
gone. 6 months to rebuild. $180K in missed detections during ramp.

**WITH:** 5,000 triage decisions compiled into 315 geometric
values (140 centroids + 175 DiagonalKernel weights). Replacement
starts Day 1 with predecessor's judgment. Fingerprint shows which
factors are signal vs noise: "data_freshness: weight 100%
(cleanest). recurrence: weight 52% (noisiest)." 30.85 min/alert
saved — measured from production triage data. $523K–$2.8M/year
value depending on industry.

**WHY NOBODY ELSE:** CrowdStrike detects threats. Splunk
aggregates logs. Palo Alto runs playbooks. None of them learn from
YOUR analysts' triage decisions. None get better at scoring over
time. None preserve institutional judgment across personnel
transitions. The triage outcome is the most valuable signal in
security operations — and every competitor throws it away.

**ONE-LINER:** *"Your SOC has amnesia. Alert #10,000 = alert #1.
We cure that."*

---

### SOC-2: 30.85 MINUTES PER ALERT

**Domain:** SOC · **Buyer:** CISO, SOC Manager
**Industry data:** SANS 2025: average alert investigation time
25-45 minutes. 80% of analyst time is mechanical collection,
not analysis. Alert fatigue is the #1 cause of missed breaches.

**THE PROBLEM:** Analyst investigates a suspicious login anomaly.
Opens VirusTotal (IP reputation). Opens GreyNoise (known scanner
check). Opens Pulsedive (threat intelligence). Checks MITRE
ATT&CK mapping. Checks internal asset database. Checks previous
alerts from same source. 35 minutes. 80% was collection. 20% was
judgment. The 80% is the same every time.

**WITHOUT:** 50 alerts × 35 minutes = 29 hours/day. Team of 4
barely keeps up. When volume spikes (attack campaign, zero-day),
queue backs up. Lower-priority alerts get skipped. The one that
got skipped was the real attack.

**WITH:** System pre-fuses all sources via context graph. Cross-
references automatically. 4.15 minutes per alert. Savings: 30.85
minutes × 50 alerts = 25.7 hours/day recovered. Per year:
9,380 hours. At $75/hour = $703K in direct analyst time.
Plus: the system learned which combinations escalate — it catches
the alert the overwhelmed analyst would have skipped.

**WHY NOBODY ELSE:** SOAR tools (Palo Alto XSOAR, Splunk SOAR)
automate playbook STEPS. They don't learn which COMBINATIONS of
signals predict correct triage outcomes. We learn from the
DECISION, not just the DATA. Different architectural problem.

**ONE-LINER:** *"30.85 minutes saved per alert. Measured, not
modeled. Multiply by 50 alerts, 365 days."*

---

### SOC-3: THE STRYKER/HANDALA ATTACK

**Domain:** SOC · **Buyer:** CISO, Board Risk Committee
**Industry data:** Average dwell time (attacker in network before
detection): 10 days (Mandiant 2025). 82% of breaches involve the
human element (Verizon DBIR).

**THE PROBLEM:** A supply chain attack compromises a
medical device vendor's IT infrastructure. Devices function
normally. The attack vector is the infrastructure connecting
devices to care delivery. Downstream hospitals don't know they're
exposed through the vendor's supply chain. No individual system
fires an alert.

**WITHOUT:** Hospital's SOC sees vendor endpoints behaving
normally (no alerts generated). SIEM shows no anomalies.
The breach is INVISIBLE at the individual system level because
it's a supply chain attack — the signal is in the CORRELATION
between vendor endpoints and external threat intelligence, not
in any single data source.

**WITH:** Compounding system had 8 months of behavioral baselines
on vendor-connected endpoints. Cross-graph attention correlates:
endpoint behavior + external threat feed + network flow anomalies.
None crossed threshold individually. The COMBINATION crosses
threshold. "Vendor-connected endpoints showing patterns consistent
with known attack TTPs. Confidence: 0.73. No individual alert
fired. Cross-graph discovery flagged." Time to detection: 4 hours
(vs industry average 10 days). [SIMULATED]

**WHY NOBODY ELSE:** Supply chain attacks are invisible to single-
system detectors because no SINGLE signal fires. Detection
requires cross-graph computation across behavioral baselines,
threat intelligence, and network flows simultaneously. SIEM
aggregates but doesn't learn. EDR detects known patterns. Neither
discovers NEW patterns from the combination.

**ONE-LINER:** *"The attack was invisible to every system
individually. The graph saw the combination."*

---

### SOC-4: THE SYSTEM THAT ADMITS FAILURE

**Domain:** SOC · **Buyer:** CISO, Security Architect
**Industry data:** Gartner: by 2026, organizations using AI with
integrated trust/safety will see 50% fewer AI failures. The #1
fear of CISOs adopting AI: uncontrolled automation.

**THE PROBLEM:** CISO wants to automate Tier 1 triage but fears
false negatives — an automated system that incorrectly closes a
real alert. "If it auto-closes one real attack, I've lost my job."
Current: 0% automation. Every alert reviewed by a human.

**WITHOUT:** Binary choice: automate everything (unsafe) or
automate nothing (expensive). No middle ground. No proof that
automation is safe. "Set a threshold" — based on what? Gut feeling?

**WITH:** Conservation law: α·q·V ≥ θ_min. Auto-approve expands
from 0% → 15% → 35% → 55% over 12 months. Each step PROVEN safe
before execution. If accuracy dips → AMBER → expansion pauses.
Meanwhile, AgentEvolver tested "auto-close all recurring scanners."
Shadow-tested 15 decisions. 45% accuracy. REJECTED. Not promoted.
"The system that admits failure is the system I trust," the CISO
says.

**WHY NOBODY ELSE:** No competing security platform has a
mathematical proof of automation safety. They have configurations.
We have a theorem. And no platform shadow-tests its own operational
rules and REJECTS the ones that fail. That rejection IS the trust.

**ONE-LINER:** *"Shadow-tested. 45%. Rejected. The system that
admits failure is the system you trust."*

---

## PURCHASING (5 scenarios)

---
---

### PUR-1: THE TRUST TRAP

**Domain:** Purchasing (Food Service) · **Buyer:** Restaurant Owner
**Industry data:** National Restaurant Association: food cost is
28-35% of revenue. 1-3 point improvement = $15-45K/year for $1.5M
restaurant. 70% of independent restaurants have ONE person
handling all purchasing.

**THE PROBLEM:** Marco, $3.2M Italian restaurant, Chicago. Rosa
handles purchasing. 9 years experience. 30 suppliers. She always
checks what the supplier charges first — it feels like due
diligence. She trusts her salmon supplier because she's worked
with them for 7 years. Nobody has ever measured whether her trust
is correctly placed.

**WITHOUT:** Rosa trusts her salmon supplier's quotes (she checks
them carefully). She rarely checks whether they show up on
time (seems fine). Nobody knows that what they charge is the
NOISIEST predictor of order outcomes (weight 8%) while whether
they show up complete and on time is the CLEANEST signal
(weight 97%). She's been trusting the wrong signal for 7 years.

**WITH:** 800 verified orders later, the trust analysis radar
reveals it: what they charge at weight 8% (tiny slice). Whether
they show up on time at weight 97% (dominant). The expected
importance and actual importance are INVERTED.

Beat 1: Supplier scorecard for salmon supplier. OTIF 89%.
Nothing alarming. [Buyer nods.]
Beat 2: Click Trust Analysis. Radar chart appears. Expected (blue)
and actual (red) shapes are inverted. [3-second pause.]
Beat 3: "The factor you check first is the one that predicts
least. The factor you ignore predicts most."

**WHY NOBODY ELSE:** No food ordering tool learns which supplier factors actually
predict good outcomes from verified orders. BlueCart sends
orders. MarketMan tracks costs. Upserve logs invoices. None
learn WHICH FACTORS matter from your actual results. The
trust trap — your expectations inverted from reality — is a
genuinely novel finding category.

**ONE-LINER:** *"The factor you trust most is the one that
lies to you."*

---

### PUR-2: THE PRICE MEMORY

**Domain:** Purchasing (Food Service) · **Buyer:** Owner, Head Chef
**Industry data:** Average supplier price increase acceptance
rate without challenge: 87% (Spend Matters 2025). Restaurants
lose $4-8K/year in unchallenged increases.

**THE PROBLEM:** Marco's Italian restaurant. Rosa negotiated
$12.40/lb for salmon in October. Six months later, same supplier
quotes $14.20. Rosa can't remember the negotiation — she left
for a catering company. The PO reference is buried in QuickBooks.
New chef Miguel accepts the 14.5% increase.

**WITHOUT:** Every negotiated price lives in Toast POS and QBO
history — but nobody queries it at the moment of decision.
Suppliers raise prices 8-12% after 6 months knowing the chef
who negotiated has moved on. $4-8K/year in unchallenged increases
at a $1.5M restaurant.

**WITH:** "Last negotiated rate: $12.40/lb (PO-2847, October 2025,
6-month lock). Current quote: $14.20 (+14.5%). This supplier's
pattern: raises 8-12% after 6 months if not challenged (N=4
negotiations). Recommend: reference PO-2847 in re-quote request."

The system remembers EVERY negotiated price, EVERY supplier's
pricing behavior, and surfaces it at the EXACT moment of decision.
Episodic memory (specific events) + judgment memory (patterns) +
decision support (recommendation). Combined.

**WHY NOBODY ELSE:** Toast POS stores orders. QBO stores invoices. Neither connects
invoice history → supplier pricing behavior → negotiation
leverage → decision recommendation at the moment you need it.
That chain requires learning from verified outcomes, connecting
data across systems, and surfacing it in plain language when
the order is placed. No ordering system does this.

**ONE-LINER:** *"The system remembers every negotiation. Your
supplier hopes you forgot. You didn't."*

---

### PUR-3: THE $28K DEPARTURE

**Domain:** Purchasing (Food Service) · **Buyer:** Owner, CFO
**Industry data:** Cost of replacing a key restaurant employee:
1.5-2× salary (SHRM). Average ramp for replacement chef: 3-6
months. 80% of purchasing knowledge at independent restaurants
is undocumented — it's in the chef's head.

**THE PROBLEM:** Marco's restaurant. Rosa managed purchasing for
9 years. She knew: the produce distributor inflates quotes in
July because of driver shortages. The pasta supplier gives
volume breaks if you order Tuesdays. Rainy weekends need 20%
less protein but 30% more comfort pasta. She left for a catering
company. Miguel has the same Toast POS, same QBO, same supplier
contacts. None of Rosa's knowledge.

**WITHOUT:** Miguel doesn't know the salmon supplier raises
prices after 6 months. He doesn't know rainy Saturdays need 28%
less protein. He doesn't know the produce distributor's July
inflation pattern. $28K in avoidable mistakes over 6 months — $8K in price creep,
$7K in over-ordering, $5K in missed credits, $4K in poor
substitutions, $4K in stockout losses. Marco considers a
restaurant consultant ($15K).

**WITH:** Rosa's 1,200 verified decisions — every pattern she learned
about suppliers, seasonality, weather, and pricing — compiled
into 315 learned values. Miguel starts Day 1 with everything
Rosa accumulated. System:
"Salmon supplier raises 8-12% after 6 months if not challenged
(N=4). Reference October pricing." "Rain Saturday: protein -28%,
produce -12% (N=23 rainy Saturdays)." Miguel performs at Rosa's
level from Month 1. $28K → $0.

**WHY NOBODY ELSE:** No system captures PURCHASING knowledge.
Not order history — JUDGMENT. Which suppliers to push, which
weather patterns change demand, which "specials" are actually
high-waste. Our system IS accumulated purchasing judgment. 315 learned
values encoding 1,200 decisions. Portable. Permanent.
Personnel-independent.

**ONE-LINER:** *"Rosa left. 9 years of knowledge left with her.
With us: zero knowledge lost. Day 1."*

---

### PUR-4: THE PAR LEVEL TIME MACHINE

**Domain:** Purchasing (Food Service) · **Buyer:** Owner, Head Chef
**Industry data:** Restaurant food waste averages 4-10% of food
purchased (ReFED 2025). Par levels set during COVID supply chain
disruption are still active at 35% of restaurants.

**THE PROBLEM:** Marco's restaurant. During COVID supply
disruptions, Rosa ordered aggressively on proteins — par level:
120 lbs/week. Post-COVID consumption: 75 lbs/week. Nobody
adjusted par. Across 50 items, similar patterns add $12K in
excess inventory and $8K in spoilage annually. Meanwhile, Friday
dinner protein keeps running out — par for weekend was set when
the restaurant had 20 fewer seats.

**WITHOUT:** Toast POS shows sales. QBO shows invoices. Nobody
tracks consumption vs par by day-of-week or season. The chef
knows "we probably have too much of something" but can't prove
it without a manual audit. Friday 86's keep happening on items
where par is too LOW.

**WITH:** Month 3: "Protein: par 120 lbs/week (set Q2 2021).
Consumption: 75 ± 12 lbs/week. Recommended: 90. Excess cost:
$340/month in spoilage." "Friday protein: par covers 85% of
demand. Recommended: +25% for Fri-Sat." Day-of-week model:
"Tuesday demand is 62% of Friday. Two-tier ordering." Par levels
update from verified consumption, not from memory or crisis-era
decisions.

**WHY NOBODY ELSE:** BlueCart sends orders. It doesn't learn
consumption patterns from POS data, detect seasonal variations,
or recommend par adjustments from verified outcomes. Par level
intelligence requires: centroid learning on consumption patterns
+ day-of-week decomposition + weather adjustment + conservation
proof before auto-update.

**ONE-LINER:** *"Your par levels are from COVID. Consumption
changed. You're wasting $340/month. We show you."*

---

### PUR-5: THE SYSTEM THAT WARNS ABOUT ITSELF

**Domain:** Purchasing (Food Service) · **Buyer:** Owner
**Industry data:** Personnel-driven quality changes are the #1
undetected risk in restaurant operations. No ordering tool
detects when a new chef's decision quality differs from their
predecessor.

**THE PROBLEM:** New head chef starts at Marco's restaurant.
Marco assumes she'll ramp up. Nobody monitors whether her
ordering decisions are as good as Rosa's. She has different
supplier relationships, different waste tolerance, different
ideas about portion sizes. The system that learned from 1,200
decisions is now receiving decisions from a different
decision-maker.

**WITHOUT:** 3 months of undetected quality drift. Auto-approve
expanded to 38% based on Rosa's accuracy. New chef's accuracy:
lower (she's learning the kitchen). The auto-approve level is
TOO HIGH for her current skill. Nobody notices until a $3K
spoilage event from over-ordering proteins for a rainy weekend
she didn't check the forecast for.

**WITH:** 50 decisions in, conservation law fires AMBER: "Override
quality changing. 8 of last 20 overrides have lower accuracy than
established pattern." Auto-approve expansion PAUSES. Alert to
Marco: "Your new chef's ordering decisions differ from Rosa's
established pattern. Recommend: 2-week supervised period before
resuming auto-approve." No other tool detects personnel-driven
quality changes. The system monitors its OWN learning quality.

**WHY NOBODY ELSE:** This requires the system to detect a HUMAN quality change —
not a data quality change. The system that LEARNED from Rosa
must detect when the new chef makes systematically different
decisions. No restaurant tool monitors whether the new person's
ordering judgment matches the established pattern. We do.

**ONE-LINER:** *"New chef started. The system noticed before
you did."*

---

## TRADING (5 scenarios)

---

### TRD-1: MY FAVORITE SETUP IS MY WORST SETUP

**Domain:** Trading · **Buyer:** Individual Trader (retail, semi-pro)
**Industry data:** Behavioral finance: traders overtrade familiar
setups by 2-4× regardless of performance (Odean, 1999). Disposition
effect: traders hold losers 1.5× longer than winners (Shefrin &
Statman, 1985).

**THE PROBLEM:** Alex, retail swing trader. $50K account. 8-12
trades/week. His RSI oversold + MACD cross is his go-to. He takes
it 3× more often than any other setup. It feels right — familiar,
well-researched, he learned it from a course.

**WITHOUT:** Trading journal shows P&L by month. Doesn't show P&L
by setup × market regime × time of day. Alex doesn't know his RSI
setup has a 48% win rate — below his 54% overall average. His
"boring" volume breakout + trend confirmation runs at 71%. He
takes the bad trade 3× more often than the good one. Cost: $3,600/year.

**WITH:**
```
$ ci-trading trust --show-radar

Signal Trust Analysis (847 verified trades):
  Volume+Trend:   weight 94% (σ=0.09) — YOUR BEST SIGNAL
  MACD crossover: weight 71% (σ=0.14) — reliable
  RSI oversold:   weight 12% (σ=0.31) — NOISE

You take RSI trades 3× more than Volume+Trend.
Estimated annual cost of this preference: $3,600.
```

Open source. Self-hosted. Data stays on his machine.
`pip install ci-trading`.

**WHY NOBODY ELSE:** Tradervue shows P&L by tag. It doesn't
compute per-signal, outcome-conditioned variance that reveals
which signals PREDICT his outcomes vs which are noise. Edgewonk
tags psychology manually — unreliable self-report. We measure
signal trust from verified trade outcomes. Automated. Objective.

**ONE-LINER:** *"My favorite setup is my worst setup. The system
showed me in 10 minutes."*

---

### TRD-2: VOLATILE MARKETS AMPLIFY YOUR BIAS

**Domain:** Trading · **Buyer:** Individual Trader, Prop Desk Manager
**Industry data:** CBOE: average VIX in 2025 was 22.4, highest since
2020. Retail trading volume increases 40% during volatility spikes
(Nasdaq). 78% of retail traders lose money during high-VIX periods
(FINRA).

**THE PROBLEM:** Tariff uncertainty. Geopolitical tension. VIX at
32. Markets moving 3% daily. Priya, semi-pro options trader, $200K
account. In calm markets (VIX 15), her biases cost 5% annually. In
volatile markets (VIX 32), the SAME biases cost 30%. A revenge
trade at VIX 15 loses $340. At VIX 32, same revenge trade loses
$1,200. Position sizing drift at VIX 15: $200/event. At VIX 32:
$1,100/event.

**WITHOUT:** No trading tool adjusts risk assessment by regime.
Priya doesn't know her per-regime accuracy: trending markets 67%,
volatile markets 38%. She runs trending strategies in volatile
markets. Gives back $4,800 in 6 weeks before noticing the regime
changed.

**WITH:** Week 1 of regime shift: "Your trending accuracy in
volatile markets: 38% (N=47). Sizing AMBER — conservation law
frozen. Your income strategy accuracy in volatile markets: 62%
(N=31). Recommendation: switch strategies or reduce exposure 60%."
Conservation law prevents scaling into strategies where HER data
says she underperforms. Tariff shock: "Your panic-sell timing: 22%
correct. 4/5 prior tariff events recovered in 14 days. Hold."

**WHY NOBODY ELSE:** No trading tool computes per-REGIME, per-
TRADER accuracy from verified outcomes. Risk management tools use
MARKET volatility. We measure TRADER performance by regime. The
system doesn't say "the market is volatile." It says "YOU
underperform in volatile markets by 29pp." Different question.
Different architecture.

**ONE-LINER:** *"Volatile markets amplify your edge AND your
bias. We separate them."*

---

### TRD-3: THE REVENGE TRADE AT VIX 32

**Domain:** Trading · **Buyer:** Individual Trader
**Industry data:** 65% of retail traders exhibit revenge trading
behavior (Barber & Odean, 2013). Average cost of revenge trading:
$4,200/year for a $50K account.

**THE PROBLEM:** Alex takes a loss on his RSI trade. 8 minutes
later, he's in another trade. "This one will make it back." Win
rate on these revenge trades: 34% (vs 54% baseline). In calm
markets: costs $340/trade. In volatile markets (VIX 32): costs
$1,200/trade. He takes 3 revenge trades during a volatile week.
$3,600 in one week.

**WITHOUT:** Edgewonk lets Alex TAG his trades as "revenge" — but
self-reporting is 40% accurate (he doesn't admit it in the moment).
No tool auto-detects the pattern from trade spacing and sizing.

**WITH:** "Decision Context: trade within 8 minutes of loss.
VIX 32 — volatile regime. Your accuracy in this pattern: 22%
in volatile markets (N=12). Estimated cost: $1,180. Conservation:
RED for this category." Framed as data, never judgment. "Decision
Context" not "Emotional Trading." Opt-out available. But the data
is clear.

**WHY NOBODY ELSE:** Auto-detection from trade spacing + sizing
anomalies + regime context. No manual tagging. No self-report.
The system computes it from the DATA — minutes since last trade,
size vs rolling average, consecutive wins/losses, market regime.
Tradervue can't do this because it doesn't have outcome-
conditioned pattern detection.

**ONE-LINER:** *"Revenge trade. VIX 32. Your accuracy: 22%.
The system caught it before you did."*

---

### TRD-4: PROVE IT BEFORE REAL MONEY

**Domain:** Trading · **Buyer:** Semi-Pro, Prop Desk Manager
**Industry data:** 92% of backtested strategies underperform live
(QuantConnect study, 2025). Average execution gap: 40% of
backtested Sharpe (accounting for slippage, timing, psychology).

**THE PROBLEM:** Priya backtested an iron condor strategy. Sharpe
2.1 in backtest. Can she go from $20K to $50K notional? Backtest
says yes. But backtests don't model HER execution — entry timing
hesitation, early exits from fear, adjustment panic during
volatile moves.

**WITHOUT:** Binary choice: backtest (doesn't model her execution)
or go live with real money (risky on unproven strategy). No middle
ground. No proof that SHE can execute this strategy at scale.

**WITH:** Conservation-gated promotion:

```
$ ci-trading conservation --strategy iron_condor

Iron Condor Strategy:
  Status: GREEN
  Verified trades: 340
  Accuracy: 71%  (threshold: 58%)
  Consistency: σ=0.08

  Current sizing: $20K notional
  Safe to increase: $35K (conservation proven)
  $50K: AMBER — insufficient history at that size.
  Recommendation: paper-trade 30 at $50K sizing first.
```

Not "the backtest says it works." The conservation law says "YOUR
execution of this strategy, verified over 340 trades, supports
scaling to $35K. $50K requires 30 more verified trades." Math,
not hope.

**WHY NOBODY ELSE:** QuantConnect backtests strategies. We
evaluate the TRADER executing the strategy. Backtests assume
perfect execution. We measure ACTUAL execution quality — entry
timing, exit discipline, sizing consistency, hold duration. The
conservation law governs scaling based on YOUR data, not
hypothetical data.

**ONE-LINER:** *"The backtest says yes. Your execution data says:
not yet. Here's what's needed."*

---

### TRD-5: THE STRATEGY THAT DIED

**Domain:** Trading · **Buyer:** Semi-Pro, Prop Desk Manager
**Industry data:** Average strategy half-life: 18 months before
edge degrades (AQR, 2024). 60% of traders continue running
degraded strategies for 3+ months before noticing.

**THE PROBLEM:** Priya's put credit spread strategy was profitable
for 18 months. Returns went negative 6 weeks ago. She's still
trading it because "it'll come back." But the market regime
changed — trending → volatile. Her strategy is regime-dependent
and she doesn't know it.

**WITHOUT:** Trading journal shows declining P&L but doesn't
explain WHY. No regime attribution. Priya blames "bad luck" or
"choppy market." Continues allocating capital. Gives back $6,200
over 3 months before finally stopping.

**WITH:** Week 2 of degradation: "Put credit spread strategy:
accuracy dropped from 68% to 49% over 6 weeks. Rolling q below
θ_min. Conservation: AMBER. Auto-sizing paused. Regime change
detected: trending → volatile. Your strategy is regime-dependent.
Volatile-market accuracy: 41% (N=23). Recommendation: paper-trade
until accuracy recovers OR investigate regime dependency."

**WHY NOBODY ELSE:** Strategy degradation + regime attribution +
conservation response. Three capabilities required simultaneously.
No trading journal detects strategy death. No risk tool attributes
it to regime change. No platform pauses sizing automatically.
Conservation law + regime classifier + centroid learning. Combined.

**ONE-LINER:** *"Your strategy died 6 weeks ago. The system
caught it at week 2."*

---

## S2P — SOURCE-TO-PAY (4 scenarios)

---

### S2P-1: THE INVOICE BOTTLENECK

**Domain:** S2P · **Buyer:** CPO, VP Procurement
**Industry data:** Average invoice processing cost: $15-40 per
invoice (IOFM). 15% exception rate is industry standard. Average
exception resolution: 45 minutes.

**THE PROBLEM:** $500M annual spend. 50,000 invoices/year. 15%
exception rate = 7,500 exceptions. Each takes 45 minutes to
resolve. 5,625 hours/year on exception triage. Same 5 root causes
every quarter. Cycle time: 14.3 days.

**WITHOUT:** Coupa manages the workflow. SAP stores the
transactions. Celonis shows the bottleneck: "Match Invoice to GR"
takes 42 minutes — 70% of cycle time. But nobody explains WHY.
Nobody recommends a fix. Nobody transfers the fix to other
invoice types. Same bottleneck, same investigation, every quarter.

**WITH:** Cross-graph: "Bottleneck BECAUSE schema change (MATKL_V2)
increased join fanout 9×. Supplier Aster invoices 3.1× slower
(94% new codes). Fix: pre-join filter. 42 → 4 minutes."
Exception rate: 15% → 7.5% (24 weeks). Auto-approve: 20% → 55%.
Cycle time: 14.3 → 7.1 days. Leakage caught: $680K/year.

**WHY NOBODY ELSE:** Invoice exceptions aren't a DATA problem.
They're a PROCESS problem visible through transaction data. The
system that connects process mining (Celonis) + ERP (SAP) +
operational learning (us) wins. Coupa manages process. We improve
decisions. Different problem.

**ONE-LINER:** *"Same 5 root causes. Every quarter. For 18
months. We fixed them permanently."*

---

### S2P-2: THE LEAKAGE NOBODY COUNTS

**Domain:** S2P · **Buyer:** CPO, CFO
**Industry data:** 2-5% of procurement spend is leakage (Hackett
Group). On $500M spend: $10-25M walking out the door. 80% of
organizations don't measure procurement leakage.

**THE PROBLEM:** $500M spend. Contract says $4.28/unit. Invoice
says $4.52. Difference: $0.24 × 5,000 units = $1,200. One
invoice. Nobody checks — it's within the "close enough" threshold.
Across 50,000 invoices/year with an average 0.8% overpayment
rate: $680K/year in leakage. Nobody counts it because nobody
connects contract terms → invoice amounts → supplier patterns
across 50,000 transactions.

**WITHOUT:** AP team processes invoices. Three-way match catches
obvious errors (wrong PO, wrong quantity). Pricing variance below
5% is accepted by default. Suppliers learn the tolerance and
price accordingly. $680K/year walks out the door.

**WITH:** System learns per-supplier pricing patterns from
verified invoices: "SupplierCo: average overprice 1.2% (N=340).
Contract rate: $4.28. This invoice: $4.52 (+5.6%). Above
supplier's pattern AND above contract. Flag." After 2,000
verified invoices, the system distinguishes legitimate price
increases (market-driven) from supplier creep (behavioral). The
$680K leakage is caught because centroid geometry learned what
"normal" looks like for EACH supplier.

**WHY NOBODY ELSE:** Three-way match catches ERRORS. We catch
PATTERNS. A 1.2% consistent overprice across 340 invoices is
not an error — it's a behavior. No AP automation tool learns
per-supplier pricing behavior from verified outcomes. They
match documents. We learn intent.

**ONE-LINER:** *"$680K/year in leakage. Not errors — patterns.
Nobody else catches patterns."*

---

### S2P-3: THE WORKING CAPITAL UNLOCK

**Domain:** S2P · **Buyer:** CFO, Treasury
**Industry data:** Average DPO: 45-60 days. Optimal DPO varies
by supplier relationship. 2% early-pay discounts are worth
36.7% annualized.

**THE PROBLEM:** $500M spend. Some suppliers offer 2/10 Net 30
(2% discount for payment within 10 days). Others penalize late
payment. Treasury applies ONE payment policy. Misses early-pay
discounts ($340K/year capturable). Pays some suppliers too early
who don't offer discounts (opportunity cost: $120K/year in
float).

**WITHOUT:** AP pays per policy. Nobody analyzes per-supplier
payment optimization. The data exists in SAP — payment terms,
discount schedules, supplier performance. Nobody connects it to
working capital strategy.

**WITH:** System learns per-supplier payment sensitivity from
verified outcomes: "Early-pay Supplier W: captures $340K/year in
discounts. Extend Supplier Z: no impact on relationship, improves
DPO 8 days." Per-supplier payment strategy optimized from verified
outcomes, not from blanket policy.

**WHY NOBODY ELSE:** Treasury management systems optimize CASH
FLOW. We optimize SUPPLIER-SPECIFIC payment strategy from
verified outcomes — which suppliers respond to early pay, which
don't care, which penalize. This requires centroid learning on
payment outcomes per supplier. Static rules can't adapt.

**ONE-LINER:** *"$340K in uncaptured discounts. You have the
data. Nobody connected it."*

---

### S2P-4: THREE SYSTEMS, ONE ANSWER

**Domain:** S2P · **Buyer:** CPO, CDO, CTO
**Industry data:** Average enterprise has 15-20 procurement-
related systems (Spend Matters). Data reconciliation across
systems consumes 30% of procurement analytics team time.

**THE PROBLEM:** SAP says $127.3M in spend. Celonis process
mining shows 14.3-day cycle time. Monte Carlo flags 400 data
quality alerts. Three systems, three perspectives, ZERO cross-
system insights. "Why is the cycle time 14.3 days?" requires
manually connecting SAP transaction data + Celonis process
activities + data quality patterns. Takes a team 3 days.

**WITHOUT:** Each system has its own dashboard. Each tells part
of the story. Nobody tells the WHOLE story. The $604K/month
exposure from the cross-graph scenario was invisible to all
three systems individually.

**WITH:** One context graph. SAP transactions + Celonis process
activities + operational alerts + verified decisions. Cross-graph
attention traverses ALL simultaneously. "Cycle time is 14.3 days
BECAUSE Match Invoice to GR takes 42 minutes BECAUSE MATKL_V2
schema change BECAUSE Supplier Aster uses 94% new codes." 4
seconds. Not 3 days.

**WHY NOBODY ELSE:** Adding SAP data to Celonis doesn't give you
learning. Adding Celonis to Monte Carlo doesn't give you
reasoning. Cross-graph computation requires ALL data in ONE graph
with ONE learning engine. This is an architectural prerequisite,
not a feature. You can't add it incrementally.

**ONE-LINER:** *"Three systems. Three perspectives. Zero insight.
One graph. Complete answer. 4 seconds."*

---

## CROSS-COPILOT THEMES

Three themes appear across ALL copilots, proving platform coherence:

### Theme 1: THE AMNESIA PROBLEM
Every copilot solves the same structural problem: decision systems
that don't learn from outcomes.

| Domain | Amnesia looks like | We cure it with |
|---|---|---|
| DataOps | Same alerts, same investigation, every month | Centroid learning from triage outcomes |
| SOC | Alert #10,000 = alert #1 | 315 geometric values from 5,000 decisions |
| Purchasing | Coordinator leaves, knowledge leaves | Centroid geometry survives personnel |
| Trading | Journal shows P&L, not WHY | DiagonalKernel reveals signal trust |
| S2P | Same exceptions, same root causes, 18 months | Cross-graph learns exception patterns |

### Theme 2: THE TRUST TRAP
Every copilot reveals that the most trusted signal is often the
noisiest.

| Domain | What they trust | What actually predicts |
|---|---|---|
| DataOps | The data catalog | DiagonalKernel per-source weights |
| SOC | The severity rating | Cross-graph behavioral correlation |
| Purchasing | The quoted price (6%) | Delivery history (100%) |
| Trading | RSI+MACD (12%) | Volume+Trend (94%) |
| S2P | Three-way match | Per-supplier pricing behavior |

### Theme 3: THE CONSERVATION PROOF
Every copilot proves automation safety with the same theorem.

| Domain | What's proven safe | Formula |
|---|---|---|
| DataOps | Auto-resolve 55% of alerts | α·q·V ≥ θ_min |
| SOC | Auto-close 55% of Tier 1 | Same formula |
| Purchasing | Auto-approve $2,500 threshold | Same formula |
| Trading | Scale from $20K to $35K | Same formula |
| S2P | Auto-approve 55% of invoices | Same formula |

*One theorem. Five domains. Mathematical safety guaranteed.*

---

**QUICK REFERENCE: ALL ONE-LINERS**

| ID | One-Liner |
|---|---|
| DO-1 | "2,400 alerts/day for 18 months. Same number. Your system has amnesia." |
| DO-2 | "The consultant found $4.2M. Left. It came back. Our system doesn't leave." |
| DO-3 | "Day 1: your data is silent. Month 12: it glows with intelligence." |
| DO-4 | "$604K/month. Celonis saw where. SAP saw what. Neither saw why. We did." |
| DO-5 | "80% of databases built by agents. Zero agents know which data to trust." |
| SOC-1 | "Your SOC has amnesia. Alert #10,000 = alert #1. We cure that." |
| SOC-2 | "30.85 minutes saved per alert. Measured, not modeled." |
| SOC-3 | "The attack was invisible to every system individually. The graph saw the combination." |
| SOC-4 | "Shadow-tested. 45%. Rejected. The system that admits failure is the system you trust." |
| PUR-1 | "The factor you trust most is the one that lies to you." |
| PUR-2 | "The system remembers every negotiation. Your supplier hopes you forgot." |
| PUR-3 | "Rosa left. 9 years of knowledge left with her. With us: zero lost. Day 1." |
| PUR-4 | "Par from COVID. Kitchen from 2026. You're wasting $340/month. We show you." |
| PUR-5 | "New chef started. The system noticed before you did." |
| PUR-6 | "Rain Saturday. Protein -28%. Adjusted before you asked." |
| PUR-7 | "Marathon Sunday. Protein +80%. System remembered." |
| PUR-8 | "Tuesday is not Friday. Two-tier par. Waste gone." |
| TRD-1 | "My favorite setup is my worst setup." |
| TRD-2 | "Volatile markets amplify your edge AND your bias. We separate them." |
| TRD-3 | "Revenge trade. VIX 32. Your accuracy: 22%. Caught before you did." |
| TRD-4 | "The backtest says yes. Your execution data says: not yet." |
| TRD-5 | "Your strategy died 6 weeks ago. The system caught it at week 2." |
| TRD-6 | "Not less trading. DIFFERENT trading. ROTATE to your edge." |
| TRD-7 | "Premium is rich. Your edge is on. The system proves it from YOUR trades." |
| TRD-8 | "5 positions. 1 bet. Correlation collapsed. You didn't know." |
| TRD-9 | "Stop guessing direction. Trade the vol. Your straddles: 68%. Directional: 39%." |
| S2P-1 | "Same 5 root causes. Every quarter. 18 months. Fixed permanently." |
| S2P-2 | "$680K/year in leakage. Not errors — patterns." |
| S2P-3 | "$340K in uncaptured discounts. You have the data. Nobody connected it." |
| S2P-4 | "Three systems. Three perspectives. Zero insight. One graph. 4 seconds." |

---

*Use Scenario Catalog v1.0 · May 21, 2026*
*23 scenarios across 5 copilots. 3 cross-copilot themes.*
*Structure: Domain → Industry Data → Problem → Without → With →*
*Why Nobody Else → One-Liner.*
*"One theorem. Five domains. Mathematical safety guaranteed."*

---

## APPENDIX: COMPLETE SCENARIO INDEX (All 82 Scenarios)

The 23 scenarios above are the hero selection for outreach. Below
is the COMPLETE index across all product definitions. Full
narratives live in the source documents. This appendix is the
registry — every scenario with: ID, title, one-line problem,
one-line transformation, and one-liner.

### DataOps — 22 Scenarios
**Source:** DataOps Copilot Design v1.6, §32-§33

**Market-driven (D-M):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| D-M1 | Alert Fatigue | 2,400 alerts/day, 45% noise, engineers investigate all | 55% auto-resolved, 1,080/day, conservation-proven | "Your system has amnesia" |
| D-M2 | Metrics Don't Improve | Data quality 78% for 18 months straight | 78→84→89% with attribution to 23 learned patterns | "The TREND is the product, not the score" |
| D-M3 | Engineer Who Quit | Sarah's 12 years of pattern knowledge walks out | IKS=78, replacement inherits 5,000 decisions Day 1 | "She left. Her knowledge didn't." |
| D-M4 | Quarterly Close 14 Days | SAP vs Salesforce vs Stripe, 3 days to reconcile | 7/12 root causes auto-resolved, close in 7 days | "Same 5 root causes. Every quarter. Fixed." |
| D-M5 | Can't Hire Enough | 12 engineers, 40% on triage, can't get to 18 | Auto-resolve 55%, 12 engineers = 18 effective | "12 engineers just became 18" |
| D-M6 | Business Users Locked Out | Wait 2 days for engineering to answer "what was revenue?" | "$4.2M (94% confidence). SAP 99%. Salesforce 87%." | "The answer knows how trustworthy it is" |
| D-M7 | Data Quality Project Stale | $400K cleanup: 72→91%. 12 months later: 79% | Improvements encoded in geometry, not slides. Permanent. | "The cleanup that doesn't un-clean" |

**Innovation-driven (D-I):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| D-I1 | Self-Aware Data | Nobody knows per-column reliability quantitatively | customer_id: 99%, satisfaction_score: 14% — learned from outcomes | "Your data knows its own IQ" |
| D-I2 | Metadata Trust | Catalog doesn't know which metadata is reliable | SAP addresses 99%, Salesforce stages 72% — DK-measured | "The catalog that knows it's wrong" |
| D-I3 | Combinations Nobody Queried | Nobody tested which data sources combine well | Orders × shipping × weather = demand +23pp. Auto-discovered. | "The graph found $180K nobody asked about" |
| D-I4 | Cross-Pipeline Dependency | Revenue + inventory both break on supplier schema change | Hidden 2-day-lag dependency discovered from 50 correlated incidents | "Nobody mapped it. The graph did." |
| D-I5 | Auto-Approval Expands | 15% auto-approve stuck, no proof to expand | 15→35→48→55% over 24 weeks, each step conservation-proven | "Math, not configuration" |
| D-I6 | Per-Consumer Quality Routing | Same quality bar for Marketing dashboard and ML pipeline | Different quality standards learned per consumer from their verification patterns | "This break matters for ML. Not for Marketing." |
| D-I7 | Data Acquisition Advisor | Don't know what external data to buy | "Add weather API (free): +$180K/yr. Shipping data ($12K): +$200K/yr." ROI-ranked. | "Your data tells you what to buy next" |
| D-I8 | Data Monetization | Don't know internal data has external value | "Your supplier profiles outperform D&B. Licensing: $120K/yr." | "Your data is worth more than you think" |
| D-I9 | Prompt Integration | Non-technical user can't connect data sources | "Connect QuickBooks to spreadsheet" → auto-discover joins + trust weights | "Integration as intelligence, not plumbing" |
| D-I10 | Quality-Aware NL | BI tool answers "$4.2M" with no confidence indicator | "$4.2M (94%). SAP 99%, Salesforce 87%, 3 pending invoices." | "The answer, plus how much to trust it" |
| D-I11 | Fix Transferred to 6 Pipelines | Same schema pattern in 6 pipelines, investigated separately each time | Pattern promoted, auto-resolved in 15 min (vs 3 hours). 6 pipelines. | "$340K/year from ONE learned pattern" |
| D-I12 | One Decision Three Improvements | Separate systems needed for scoring, lineage, metadata | One verify click → centroid + graph + DK weights update simultaneously | "One click. Three improvements. Ten seconds." |
| D-I13 | System Admits Failure | No tool shadow-tests its own rules and rejects failures | Auto-resolve timeouts: 45% → REJECTED. Auto-escalate first-time: 73% → PROMOTED. | "45%. Rejected. Trust earned." |
| D-I14 | Agent Trust Layer | 80% of databases built by agents, zero trust layer | Trust API: per-source, per-column reliability for any agent | "The layer every agent needs" |
| D-I15 | Data Product IKS | "Data-as-a-product" is a label, not a measurement | Customer-360: IKS 72 (mature). ESG: IKS 8 (learning). Per-product maturity. | "Data-as-a-product, measured." |

---

### SOC — 10 Scenarios
**Source:** SOC Copilot Design v5.7, CI Blog v13, Storyboard v9

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| SOC-S1 | Alert Triage Improvement | 35 min/alert, 80% is mechanical collection | 4.15 min/alert, pre-fused context, 30.85 min saved | "30.85 minutes. Measured." |
| SOC-S2 | Knowledge Preservation | Analyst leaves, 3 years of patterns gone | 315 geometric values encode 5,000 decisions. Inheritable. | "She left. Her judgment stayed." |
| SOC-S3 | Auto-Approve Expansion | 0% automation, CISO fears false negatives | 0→15→35→55%, conservation-proven, system pauses if quality dips | "Not a configuration. A theorem." |
| SOC-S4 | Named Profile | No system captures per-analyst decision fingerprint | THE PATTERN MATCHER. data_freshness=signal, recurrence=noise. | "Your analyst's fingerprint, quantified." |
| SOC-S5 | Incident Replay | $50K breach, post-mortem says "we should have caught it" | Re-score historical alert against current weights: "would have scored 89.2%" | "The $50K you'd have caught" |
| SOC-S6 | Cross-Copilot Transfer | SOC patterns don't transfer to DataOps or S2P | warm_start 0.757: SOC→S2P→DataOps pattern transfer Day 1 | "Security taught procurement." |
| SOC-S7 | Re-Convergence | Disruption, recovery takes same time each occurrence | γ>1: each recovery faster. 3 months→2 weeks→3 days. | "Recovery accelerates" |
| SOC-S8 | Self-Tuning | Alert thresholds require manual calibration | AgentEvolver tunes evidence ordering, routing, thresholds autonomously | "47 improvements. No consultant." |
| SOC-S9 | Supply Chain Attack | Supply-chain attack: invisible to individual systems | Cross-graph: endpoint behavior + threat intel + network flows. Combined signal. | "Invisible individually. Graph saw it." |
| SOC-S10 | System Admits Failure | No security tool rejects its own automation rules | Shadow-test: 45% accuracy → REJECTED. Not promoted. Trust earned. | "The AI that says 'I was wrong'" |

---

### Purchasing — 23 Scenarios
**Source:** Purchasing Copilot Product Definition v1.2, §3

**Table stakes + Order Intelligence (Cluster A):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| M1 | Food Cost Visibility | No aggregated food cost view by category/supplier | "Protein 34% of spend. Supplier A: $12.40/lb. B: $14.20. Same spec." | "See your food cost. Actually." |
| M2 | Delivery Matching | 15-20% discrepancies, 20 min each to resolve | Auto-match 80%, discrepancy queue, learning from patterns | "Catches the pattern, not just the error" |
| P1 | Over-Ordering | 18% protein waste on Tuesdays, nobody noticed | Same-day flag: "Tuesday demand 62% of Friday. Reduce protein 35%." | "Tuesday is not Friday" |
| P2 | Par Levels from COVID | Set during 2021 shortages, waste every week | Consumption-learned par: 120→90 lbs. Spoilage drops $340/month. | "Par from COVID. Kitchen from 2026." |
| P3 | Auto-Approve Stuck | $200 threshold for 3 years, 40 reviews/day | Conservation proves $600 safe. 40→15 reviews/day. Self-pauses. | "Proof, not a threshold" |
| P4 | Same Overcharge Every November | Salmon supplier +12-18% every Nov, accepted every time | Pattern survives chef departure. "Reference October pricing." | "Every November. For 5 years. Fixed." |
| P5 | Best Chef Left | $28K in avoidable mistakes over 6 months | 1,200 verified decisions. Miguel inherits Day 1. | "Rosa left. Her knowledge didn't." |
| I1 | Trust Trap [HERO] | Checking what they charge first (weight 8%) | Radar reveals whether they show up at weight 97%. Inverted. | "Trusts the lie. Ignores the truth." |
| I2 | Price Memory | Forgot the October negotiation, accepted 14.5% increase | "Last negotiated: $12.40/lb (PO-2847). Recommend: re-quote." | "Your supplier hoped you forgot" |

**Supplier Intelligence (Cluster B):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| P6 | 6 Produce Suppliers Same Job | 6 produce distributors, 3 from COVID. $18K/year overhead. | Behavioral duplicates: delivery r=0.94. Consolidate 6→2. $11K saved. | "6 suppliers. 3 pairs are twins." |
| P7 | Supplier Declining 3 Signals | OTIF declining 4 months, exceptions doubled, quotes slow | Cross-system: OTIF + exceptions + pricing. 2 months early warning. | "3 whispers. One shout." |

**Cross-System Discovery (Cluster C):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| M8 | Market or My Supplier? | Chicken +11%. Commodity pass-through or markup? | "USDA PPI: +7.8%. Supplier markup: +1.3% (historical 1.9%). Legitimate." | "Market or markup? Now you know." |
| I4 | Invisible Correlation | Coffee prices seem random, can't time lock-ins | r=0.88 with BRL/USD exchange rate (3-week lead), not arabica spot (r=0.21) | "The correlation nobody would find" |
| P8 | Pattern Nobody Queried | 3 years POS + QBO + supplier data, nobody connects | "Chicken wing demand r=0.84 with home games (3-week forward). Increase 30 lbs." | "Your data knew. Nobody asked." |
| P9 | Data Quality Excuse | "First clean your POS data. 6 months." Every vendor. | DK learns trust from Day 1. Toast POS: 91%. Manual: 45%. | "Works with your messy data. Day 1." |

**System Self-Governance (Cluster D):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| I3 | System Warns About Itself | New chef, nobody monitors ordering quality change | Conservation AMBER: "8/20 overrides lower accuracy." Auto-pauses. | "New chef. System noticed first." |
| I5 | Format Costs $2K/Month | 19% of invoices from Supplier X need manual correction | Format change discovered, parsing rule promoted, 19%→2%. | "$2K/month. 3 months. Nobody looked." |
| I7 | Proof for Bank | Bank asks "how do you manage food cost risk?" Answer: "We're careful." | "IKS=52. Conservation GREEN 140 days. Hash-chained audit trail." | "Bankable intelligence" |

**Disruption & Transfer (Cluster E):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| P10 | Same Supply Shock | 2025 avian flu: 8 weeks scramble, $22K. 2026 second wave: same. | Second shock: 2 weeks, $4K. Third: 4 days, $800. γ>1. | "Same shock. 10× faster." |
| I8 | Location Taught Six Others | Chicago learned produce supplier inflates end-of-harvest. Miami doesn't know. | Pattern promoted. Miami: "Warning. Lock in pricing within 3 weeks." | "One location's learning. All Day 1." |

**Food Service Intelligence (Cluster F — new v1.2):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| F1 | Weather Nobody Checked | Rain Saturday, nobody adjusted. 35% protein wasted. $480. 14× last year. | "Rain Saturday: protein -28%, produce -12% (N=23). Adjusted Thursday." | "Rain Saturday. Adjusted before you asked." |
| F2 | Event We Forgot | Marathon Sunday. Nobody flagged. 86'd items. $1,200 lost revenue. | "Marathon: protein +80%, eggs +120%. Adjust by Saturday delivery." | "Marathon Sunday. System remembered." |
| F3 | Tuesday Is Not Friday | Uniform ordering. Tuesday wastes 18% protein. Friday runs out. | "Day-of-week model: Tue 62% of Fri. Two-tier par. Waste -$180/week." | "Tuesday is not Friday." |

---

### Trading — 20 Scenarios
**Source:** Trading Copilot Product Definition v1.0, §3 + §3.5

**Signal Truth (Cluster A):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T1 | Favorite Setup Worst Setup | RSI+MACD at 48%, taken 3× more than 71% setup | Trust radar: RSI weight 12% (noise), Volume weight 94% (signal) | "My favorite setup is my worst setup" |
| T2 | Overtrade After Winning | Sizing +40% after 3 wins, 4th trade accuracy 38% | "Post-streak sizing: +40%, accuracy -16pp. Cost: $2,800/yr." | "Confidence trade. It costs $2,800/yr." |
| T3 | Friday Afternoons | Overall Sharpe 1.8. Friday 2-4pm Sharpe 0.3. | "Fri 2-4pm accuracy: 39%. Reduce 60% or stop at 2pm." | "Friday afternoons are killing you" |
| T4 | Which Regime | Profitable overall but -2% in ranging markets | "Trending: 67%. Ranging: 44%. Current: ranging. Reduce." | "Your edge has a regime" |

**Strategy Scaling (Cluster B):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T5 | Can I Scale | Iron condor at $20K, can she go to $50K? | Conservation: "GREEN at $35K. AMBER at $50K. Paper-trade 30 more." | "The math says: not yet" |
| T6 | Backtest Failed Live | Backtest Sharpe 2.1, live Sharpe 0.4 | "Execution gap: $0.37 slippage, 40% early exits. Hold to plan: Sharpe 1.6." | "Your execution is the bottleneck" |

**Trader Self-Knowledge (Cluster C):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T7 | Revenge Trade | Trade within 30 min of loss, 34% win rate | "12 minutes since loss. Historical accuracy: 34%. Cost: $4,200/yr." | "Revenge. 34%. $4,200/year." |
| T8 | Each Trader's Edge | Marcus can't quantify 3 traders' individual edges | Per-trader signal trust. "A: directional. B: mean-reversion. C: emerging sector rotation." | "Three traders. Three edges. Quantified." |

**System Self-Governance (Cluster D):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T9 | Strategy Stopped Working | Put spreads negative 6 weeks, "it'll come back" | Conservation AMBER week 2. "Regime changed. Strategy regime-dependent." | "Strategy died at week 2. You noticed at week 8." |
| T10 | Prove Before Real Money | Backtest or go live, no middle ground | Paper→small→full pipeline. Each gate conservation-proven. | "Proven, not hoped" |

**Knowledge Preservation (Cluster E):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T11 | Lost 3 Years of Patterns | Switched brokers, history split across 3 platforms | Import all, unified graph, 3 years preserved in geometry | "3 years. 3 platforms. 1 graph." |
| T12 | Playbook Nobody Wrote | Trader A leaving, 8,000 trades of intuition | IKS=74. Centroid geometry + DK weights. Mathematical encoding. | "8,000 trades. Encoded. Transferred." |

**Volatility (Cluster F — added post-review):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T13 | Tariff Shock Survivor | April 2025: panic sold at bottom, -12% | "Tariff accuracy: 31%. Panic-sell: 22%. 4/5 recover in 14 days. HOLD." | "Same emotions. Different outcome." |
| T14 | Regime Shift | Trending strategies in volatile market, -$4,800 in 6 weeks | Week 1: "Trending accuracy in volatile: 38%. Switch or reduce 60%." | "Wrong strategy for the weather" |
| T15 | Revenge at VIX 32 | Revenge trade costs $340 at VIX 15, $1,200 at VIX 32 | "VIX 32. Revenge accuracy: 22%. Conservation: RED." | "Same bias. 3× the damage." |

**Volatility Offense (Cluster G — making money FROM volatility):**

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| T16 | Volatile-Market Edge | VIX spikes, every tool says "reduce." Misses strategies that WORK better at high VIX. | "Income strategies: INCREASE 40% (accuracy 71% at VIX 32 vs 58% at VIX 15). ROTATE, don't reduce." | "Not less trading. DIFFERENT trading." |
| T17 | Premium Selling Timing | Sells premium in calm AND volatile markets at same sizing. At IV/RV < 1.2: 49%. At IV/RV > 1.5: 78%. | "IV/RV 1.72. Your premium edge IS ON. Increase allocation 30%. Conservation: GREEN." | "Premium is rich. Your edge is on." |
| T18 | Correlation Breakdown | 5 "diversified" positions. VIX 30 → correlation 0.3 → 0.7. Effective exposure: 3×. | "Correlation alert: 0.32 → 0.71. Diversification collapsed. Your concentrated accuracy: 34%." | "5 positions. 1 bet. You didn't know." |
| T19 | Earnings Vol Edge | Directional earnings plays: 39%. Straddles: 68%. Takes directional 4× more. $4,200/yr. | "You're a volatility trader, not a direction trader. Straddles only this season." | "Stop guessing direction. Trade the vol." |
| T20 | VIX Mean-Reversion Timing | Shorts VIX after spikes — right idea, wrong timing. Entry too early. | "Entry accuracy: 44% (early). 3-day hold: 71%. Wait for 2-day confirm." | "Right direction. Wrong timing. Fixed." |

---

### S2P — 16 Scenarios
**Source:** S2P Product Definition v1.3, MAP v5.110 §6

| ID | Title | Problem | With | One-liner |
|---|---|---|---|---|
| S1 | Exception Rate Drops | Exception rate: 15% for 18 months | 15→11→7% over 12 months. System learned which are noise. | "The rate that actually drops" |
| S2 | Auto-Approve Expansion | 20% auto-approve, stuck | 20→35→48→55%. Conservation-proven at each step. | "Proof at every step" |
| S3 | Disruption Recovery | Tariff shock: 3 months to recover each time | 3 months→2 weeks→3 days. γ>1. Re-convergence. | "Recovery accelerates" |
| S4 | Dirty Data Handled | "Clean your data first. 6 months." | DK learns trust Day 1. SAP: 94%. Spreadsheet: 23%. Thrives on mess. | "Your worst data is our best signal" |
| S5 | Pattern Nobody Queried | 3 years of procurement data, nobody connects it | Cross-graph discovers supplier × process × timing patterns | "Your data knew. Nobody asked." |
| S6 | Expertise Walks Out | Senior buyer leaves, 15 years of supplier knowledge gone | IKS=67. 3,000 verified decisions in centroid geometry. | "She left. Her judgment stayed." |
| S7 | Supplier Consolidation | 47 suppliers, should be 16. $180K overhead. | Behavioral clustering from verified orders. 47→16. | "47 suppliers. 31 redundant." |
| S8 | Lead Time Wrong | Supplier says 7 days. Actual: 12. Nobody tracks. | Per-supplier lead time from verified deliveries vs quoted. | "They say 7. Reality says 12." |
| S9 | Auto-Pause | Quality dip, automation doesn't stop | Conservation AMBER → auto-pause. System protects itself. | "It stopped before you asked" |
| S10 | Consultant Findings Evaporate | $45K engagement. $180K found. 12 months: $140K back. | Findings encoded in geometry. Don't evaporate. Compound. | "The consultant who never leaves" |
| S11 | Fine Until Wasn't | Supplier A-rated, then missed critical delivery | 3 signals declining simultaneously. 2-month early warning. | "Three whispers. One shout." |
| S12 | Working Capital | Blanket payment policy misses per-supplier optimization | Per-supplier payment sensitivity. $340K early-pay captured. | "$340K in uncaptured discounts" |
| S13 | Self-Tuning | Manual threshold calibration for every rule | AgentEvolver shadow-tests + promotes/rejects. 47 improvements. | "47 improvements. Zero consultant hours." |
| S14 | Situation Reasoning | System recommends but can't explain WHY | "Because 3 similar invoices from this supplier were overcharges (N=34)." | "Not just what. Why." |
| S15 | Values Caution | Fear of AI making bad autonomous decisions | Conservation law: mathematical proof. System that admits 45% = rejected. | "Designed to be cautious" |
| S16 | Process-Tech Fusion | Celonis shows where, SAP shows what, nobody connects | WHERE→WHY→WHAT→PROVE→TRANSFER in one graph. 4 seconds. | "Three systems. One answer." |

---

### SCENARIO COUNTS

| Copilot | Market | Innovation | Volatility | Food Service | Total |
|---|---|---|---|---|---|
| DataOps | 7 | 15 | — | — | 22 |
| SOC | — | 10 | — | — | 10 |
| Purchasing | 3 | 8+8=16 | — | 3 | 23 |
| Trading | — | 12 | 8 | — | 20 |
| S2P | — | 16 | — | — | 16 |
| **TOTAL** | **10** | **69** | **8** | **3** | **91** |

23 hero scenarios in the main catalog (§§ above).
91 total scenarios in this appendix.
Full narratives in source documents.

---

*Use Scenario Catalog v1.0 · May 21, 2026*
*23 hero scenarios + 91-scenario complete index.*
*5 copilots. 3 cross-copilot themes. 30 one-liners.*
*"One theorem. Five domains. Mathematical safety guaranteed."*
