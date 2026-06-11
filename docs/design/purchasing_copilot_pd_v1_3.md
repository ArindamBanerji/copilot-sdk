# Purchasing Copilot — Product Definition v1.3
## Purchasing That Learns Your Kitchen

**Version:** 1.3 · **Date:** May 29, 2026
**Supersedes:** v1.2 (May 29, 2026)
**Changes v1.2 → v1.3:** Applied feedback from 3-LLM purchasing mini-poll
(Grok, Gemini, GPT). Factor display names simplified: "Price Position" → "What
They Charge", "Delivery Reliability" → "Whether They Show Up." Value reframed:
$45-75K → "1-3 points of recoverable leakage" ($15-45K). $28K departure given
component breakdown. Fake precision softened in buyer-facing scenarios. Jargon
("centroid geometry", "DK weight") scrubbed from buyer text, retained in engineering
specs. Chain learning promoted as top multi-location angle. Day 1 timing softened.
Weekly recovered-dollar report added as product requirement.
**Authority:** Purchasing Copilot PD v1.1 (architecture) + CI Blog v13 (positioning) +
food service industry research (May 2026) + implementation scan (May 29, 2026).

---

## §1 — The Problem Nobody Has Solved for Independent Restaurants

Every food ordering tool helps you PLACE orders. None of them learn from the
OUTCOMES.

BlueCart sends orders. MarketMan tracks costs. Upserve logs invoices. All valuable.
All static. Order #10,000 is processed with exactly the same logic as order #1.

Meanwhile, your head chef has spent 8 years learning that your salmon supplier
pads quotes 8% in November. That you need 40% more protein the week before
Thanksgiving, not the week of. That rainy Tuesdays kill lunch but spike Thursday
dinner. That avocados from Supplier A arrive bruised 30% of the time in August.
That the Friday night private event always generates a Saturday waste spike because
nobody adjusts the Sunday reorder.

None of this is in any system. It's in her head. When she leaves, it leaves.

The National Restaurant Association confirms: food cost is 28-35% of revenue for
most restaurants. A 3-percentage-point improvement in food cost control translates
to $15-45K/year in recovered profit for a $1.5M-revenue operation (1-3 points
off food cost) — without touching menu prices or reducing portions.

**What we build:** purchasing that learns from every verified order, discovers
patterns across your suppliers, your menu, and your local market, proves when
auto-approval is safe to expand, and gets measurably better every quarter.
After 1,000 verified orders, your system knows your suppliers and your kitchen
better than any individual ever could — and unlike that individual, it never
leaves, never forgets, and every new chef starts with everything the previous
chef ever learned.

---

## §2 — Four Buyer Personas

### Marco — Owner, $3.2M Italian Restaurant, Chicago

Rosa managed purchasing for 9 years. She knew every supplier. She knew the
produce distributor inflates quotes in July because of driver shortages. She
knew the pasta supplier gives volume breaks if you order Tuesdays. She knew
that rainy weekends need 20% less protein but 30% more comfort pasta. She
left for a catering company. Marco spent $28K in the first 6 months with her replacement — $8K in price
creep nobody challenged, $7K in over-ordering, $5K in missed credits, $4K in
poor substitutions, $4K in stockout losses.

**What he'd pay for:** "Something that captures what Rosa knew, from the
orders themselves. So the next Rosa starts with everything."

### Lisa — Operations Director, Café Chain, 4 Locations, Seattle

Four locations. Four different purchasing coordinators who don't share
knowledge. Location A negotiated Net-30 with all suppliers. Location B
gets 2% early-pay discounts from the same suppliers. Neither knows.
Coffee prices moved 12% in Q1 — did suppliers pass through the market
increase or add margin? Lisa can't answer without building a four-location
spreadsheet from scratch, every time.

**What she'd pay for:** "One system that knows what all four locations know,
consolidates that knowledge, and tells me when a price increase is the market
vs my supplier."

### Rafael — F&B Director, $28M Hotel, Miami

Oversees purchasing for restaurant, bar, banquet, and room service. $4.2M
annual food and beverage spend. He has a purchasing coordinator who is
competent but not exceptional. The purchasing decisions that matter — which
supplier to lock in before hurricane season, when to bulk-buy lobster, which
new supplier is worth qualifying — require institutional knowledge he doesn't
have time to build manually.

**What he'd pay for:** "Proof that purchasing is getting better every quarter —
and the system to show my GM why the food cost is improving."

### Karen — Restaurant Consultant, 12 Clients/Year

Sees the same patterns across every kitchen she walks into: stale par levels,
trusted suppliers with mediocre measured performance, seasonal patterns nobody
has quantified. She finds $40-120K/year per engagement. Returns 18 months later
and finds $80K of it back. Her core observation: "The best kitchen managers are
10x better at purchasing than average. But they're one person. And nobody has
built a tool that captures what makes them 10x."

**What she'd pay for:** "Your findings persist after I leave. Client doesn't need
me back in 18 months. I earn monitoring revenue instead."

---

## §3 — 23 Scenarios of Change

Organized into 6 clusters. Each scenario has a BEFORE (recognizable pain)
and AFTER (uniquely enabled by our architecture).

### Cluster A: Foundation (Table Stakes + Order Intelligence)

**M1: "I Can't See My Food Cost by Category"** [TABLE STAKES]
BEFORE: QuickBooks shows invoices. MarketMan shows cost per item — today.
Nobody can answer: "What did we spend on protein last quarter, across which
suppliers, at what price trend?" Without this view, every innovation feature
has no context.
AFTER: "You spent $86K on protein across 6 suppliers last quarter. Supplier A:
$34K, beef at $6.84/lb average (up 4.2% from Q3). Supplier B: $22K, poultry
at $3.21/lb (down 1.1%). Your protein cost % is 9.8% of revenue — industry
benchmark for your format is 10-11%. You're well-positioned."

**M2: "My Deliveries Don't Match My Orders"** [TABLE STAKES]
BEFORE: Invoice says 40 lbs salmon. Delivery was 36 lbs. Driver was in a hurry.
Nobody caught it. $28 lost on one delivery. 8 deliveries/week, 15% discrepancy
rate: $1,400/month in unverified losses.
AFTER: Auto-match catches 80% clean at delivery confirmation. The 20% with
discrepancies are queued: "Invoice: 40 lbs × $14.20 = $568. Received: 36 lbs
(4 lb short). Standard for this supplier: ships 3-6% under in summer months
(N=34). Recommend: credit request or adjust next order." After learning:
the supplier's under-delivery pattern is auto-flagged before it becomes
routine.

**P1: "I'm Over-Ordering and I Don't Know It"**
BEFORE: Par levels set 2 years ago. Consumption changed. Kitchen manager
orders to comfort level, not consumption model. Weekly waste: 12% protein,
18% produce. At a $1.5M restaurant: $45K/year in food cost that never
hits a plate.
AFTER: "Salmon par: 60 lbs (set March 2024). Learned consumption: 44 lbs/week
(± 8 lbs weather-adjusted). Current overstock: 18 lbs at $14.20 = $255 excess
this cycle. Recommend par adjustment to 50 lbs. Q4 seasonal adjustment: +15%
(holiday menu)."

**P2: "My Par Levels Are From a Different Menu"**
BEFORE: Menu changed 14 months ago. Consumption model didn't follow. Capacitor
syndrome: stale par levels from a business that no longer exists.
AFTER: System tracks consumption from verified orders. Par levels update from
actual throughput: "Burrata consumption: 8 lbs/week (menu added March 2024).
Current par: 14 lbs (stale from initial estimate). Recommended: 10 lbs.
You've been carrying $60 in excess per cycle for 14 months."

**P3: "Auto-Approve Is Stuck at $200"**
BEFORE: Chef approves all orders manually. 35-40 line items / week. 40 minutes
daily on routine approvals that are always approved anyway.
AFTER: Week 6 (800 verified orders): system proves $400 is safe for repeat
items from top 8 suppliers. Conservation law: α·q·V ≥ θ_min — mathematical
proof, not a promise. Daily review: 40 → 12 line items. Month 4: $600. Month 8:
$1,200 for suppliers with 12+ month verified history. If accuracy dips, system
pauses ITSELF.

**P4: "The Same Overcharge Every November"**
BEFORE: Every November, the seafood distributor quotes lobster 12-18% above
summer pricing. Always approved because "it's seasonal." Pattern cost: $6,200/year.
Chef who knew this retired.
AFTER: System knows: "Lobster pricing: June-August baseline $18.40/lb. November
average: $21.80 (+18.5% premium, N=24 orders across 3 years). Current quote:
$22.10 — at high end of seasonal range. Recommend: request price justification
or reduce order quantity." Pattern survived personnel change — lives in centroid
geometry, not in anyone's head.

### Cluster B: Supplier Intelligence

**P5: "My Best Chef Left. $30K in Waste."**
BEFORE: Rosa managed purchasing for 9 years. Replacement Carlos has same
suppliers, same access. He approves the salmon supplier's inflated November
quotes. He doesn't know the produce distributor has been slow-delivery in
August for 3 years. He doesn't know which items need 3-week lead times before
major holidays. $30K in avoidable waste and overcharges, first 6 months.
AFTER: 1,200 verified orders compiled into centroid geometry + DK precision
weights. Carlos starts Day 1 with everything Rosa built. System warns: "This
supplier's August delivery performance: OTIF 68% (vs annual 91%). Order 5 days
early. N=12 summers."

**I1: "The Supplier Trust Trap"** [HERO SCENARIO]
BEFORE: You trust your seafood supplier's price quotes because you've worked
with them for 7 years. They're your first call when you're building a seasonal
menu. This feels like good relationship management.
AFTER: Signal-confidence inversion reveals from 600 verified orders: their
QUOTED PRICES are the noisiest predictor of correct order outcomes (σ=0.29,
weight 8%). Whether they show up on time — which nobody checks at order time —
is the cleanest signal (σ=0.06, weight 97%).

The factor you check first (the quote) predicts least. The factor you never
check (3-year delivery OTIF by month and season) predicts most. Every
independent restaurant has at least one trust trap.

**3-beat demo:**
Beat 1: Supplier Scorecard. "Good supplier. 7-year relationship. OTIF 88%.
Revenue $340K/year." [Buyer nods.]
Beat 2: Click "Trust Analysis." Radar chart. Expected (blue): what they charge
is large, whether they show up is small. Actual (red): what they charge is tiny
(weight 8%), whether they show up on time is dominant (weight 97%). Shapes
inverted. [Pause 3 seconds.]
Beat 3: "The factor you check first — what they charge — predicts your outcomes
least. The factor you never check — whether they show up complete and on time —
predicts most. You've been watching the wrong thing for 7 years."

**I2: "The Price Memory"**
BEFORE: You negotiated $12.40/lb for salmon in October. Six months later,
same supplier quotes $14.20. You accept — you forgot the negotiation, the
chef who negotiated left, the PO reference is buried in QuickBooks.
AFTER: "Last negotiated rate: $12.40/lb (PO-2847, October 2025, 6-month
lock). Current quote: $14.20 (+14.5%). This supplier's pattern: raises 8-12%
after 6 months if not challenged (N=4 negotiations). Recommend: reference
PO-2847 in re-quote request."

**P6: "6 Produce Suppliers Doing the Same Job"**
BEFORE: 6 produce distributors. Three added during COVID. Relationship overhead:
$18K/year. Pricing inconsistency across suppliers for identical items.
AFTER: System identifies 4 behavioral duplicates from 800 verified orders:
"Suppliers A, C, E: delivery r=0.94. Pricing ±1.8%. Quality defect rate
identical within confidence. Consolidate to A+B. Savings: $11K/year in
relationship overhead + volume pricing improvement."

**P7: "The Supplier That Was Fine Until It Wasn't"**
BEFORE: Produce distributor: A-rated, on-time 93%. Misses a critical delivery
before a large event. Post-mortem: OTIF declining 4 months (93→79%), exception
rate doubled 3 months ago, quote response time doubled 2 months ago. Three
signals in three data sources, each below alarm threshold individually.
AFTER: Two months before the failure: "Three signals declining simultaneously.
Pattern consistent with capacity constraint or financial stress. Confidence: 0.71.
Recommend: qualify backup produce supplier before high-volume season."

### Cluster C: Cross-System Discovery

**M8: "Is This the Market or My Supplier?"**
BEFORE: Your chicken supplier raises prices 11%. Is this commodity pass-through
or markup? You can't answer without 3 hours with a spreadsheet pulling USDA PPI
data, your invoice history, and your contract terms.
AFTER: Real-time decomposition: "Broiler price (USDA PPI): +7.8%. Supplier
historical markup on pass-throughs: +1.9% (N=18). Current markup: +1.3% —
within historical range. Verdict: legitimate pass-through, accept." Or: "USDA
component: +3.1%. Supplier adding +7.9% on top. Their historical pass-through
markup: 2-3%. Excess: +4.9% ($340 this order). Recommend: challenge or switch
to Supplier B (tracking USDA more accurately)."

**I4: "The Invisible Correlation"**
BEFORE: Coffee bean prices seem to move randomly. You never know when to lock
in pricing.
AFTER: Cross-graph discovers: your coffee supplier's price increases correlate
r=0.88 with Brazilian Real/USD exchange rate (weekly, 3-week lead), NOT with
arabica spot prices (r=0.21). "Coffee quote +9%. BRL/USD moved -8.2% (3 weeks
ago). This is currency-driven, not commodity-driven. Pattern is predictable:
BRL weakening → supplier raises prices ~3 weeks later. Hedge: lock in orders
when BRL strengthens." A discovery a human COULD make but practically NEVER WOULD.

**P8: "The Pattern Nobody Queried"**
BEFORE: Your POS has 3 years of sales data. Your ordering history is in
QuickBooks. Your supplier delivery records are in email threads. Nobody
connects them.
AFTER: "Your chicken wing consumption r=0.84 with local sports team home games
(3-week forward). Next home game: 18 days. Current wing par: 80 lbs.
Recommended: increase to 110 lbs. Time to analyze: automatic. Time previously:
3 hours of manual correlation work."

**P9: "The Data Quality Excuse"**
BEFORE: "First, clean your data. 6 months. Our POS doesn't export cleanly.
Our QBO is a mess." Every software vendor says this.
AFTER: Deploy Day 1 on whatever data exists. DiagonalKernel learns which
sources to trust from verified outcomes: "POS sales data: weight 91% (clean,
consistent). QBO invoices: weight 78% (occasional rounding). Supplier lead
time promises: weight 11% (rarely accurate). Proceed without cleaning —
the system will work around the noise." The messier the data, the MORE
we outperform tools that treat all sources equally.

### Cluster D: System Self-Governance

**I3: "The System That Warns About Itself"**
BEFORE: New kitchen manager starts. Nobody monitors whether their purchasing
decisions match the established pattern.
AFTER: 50 decisions in, conservation law signals AMBER: "Override quality
changing. 7 of last 18 overrides have lower accuracy than established
pattern. Possible new preference profile emerging." System pauses auto-approve
expansion. Alerts owner: "New manager's decisions diverge from Rosa's learned
pattern. Recommend: 2-week supervised period before resuming auto-approve
expansion. Not a performance flag — the system needs to re-calibrate."

**I5: "The Format That Costs $2K/Month"**
BEFORE: 19% of invoices from Supplier X require manual correction. Nobody
investigates why. It's just how it is.
AFTER: System discovers: Supplier X changed their invoice format 3 months ago.
92% of corrections are the same field mapping (unit from "case" to "lbs").
AgentEvolver tests a parsing rule → conservation gate passes → promoted.
Manual corrections: 19% → 2%. Savings: $2K/month in coordinator time.
Next format change at any supplier: recognized and routed before becoming
a 3-month problem.

**I7: "The Proof Your Bank Needs"**
BEFORE: Restaurant owner applying for credit line expansion. Bank: "How do
you manage food cost risk?" Answer: "We're careful. Rosa was really good."
AFTER: "IKS = 62 from 1,400 verified purchase decisions. Auto-approve at 38%
with mathematical safety proof. Conservation GREEN for 140 consecutive days.
Full hash-chained audit trail showing every override reason and outcome."
IKS and conservation become bankable — quantified operational intelligence
that demonstrates purchasing competency beyond "trust me."

### Cluster E: Disruption & Transfer

**P10: "Same Supply Shock, Same Scramble"**
BEFORE: 2025 avian flu shock: 8 weeks of scramble, $22K in emergency sourcing
and substitutions. 2026 second wave: same 8 weeks, same cost.
AFTER: Second shock: 2 weeks, $4K. System accumulated disruption-response
patterns from the first event. Third shock: 4 days, $800. Re-convergence is
mathematically faster each time (γ > 1). The system absorbed the institutional
knowledge from handling the first shock — so the second shock is faster, and
the third is routine.

**I8: "The Location That Taught Six Others"**
BEFORE: Chicago location learned that their produce supplier raises prices
3 weeks before the end of each harvest cycle. Miami location (same supplier)
doesn't know. They overpay every cycle.
AFTER: Pattern promoted via AgentEvolver. Miami benefits Day 1: "Warning:
Supplier X end-of-cycle pricing premium (from Chicago, N=18 cycles). Lock
in current pricing within 3 weeks." One location's 2-year learning →
all locations on Day 1. Chain IKS grows faster than any individual location.

### Cluster F: Food Service Intelligence (New — v1.2)

These three scenarios are native to food service — they don't exist in the
manufacturing or S2P domains. They emerge from the `weather_forecast`,
`event_flag`, and `day_of_week` factors in the DomainConfig.

**F1: "The Weather Nobody Checked"**
BEFORE: Saturday forecast: heavy rain. Nobody adjusts. Kitchen over-ordered
by 35%. $480 in proteins and produce wasted. This happened 14 times last year.
AFTER: Thursday morning, before the Saturday order: "3-day weather forecast:
heavy rain Saturday. Your rain-day demand pattern: -28% covers, -35% protein,
-12% produce (from your last 2 years of rainy Saturdays). Recommended order: protein 65% of
standard, produce 88%. Estimated waste saved: $340."
The weather_forecast factor weight (DK: 94%) reflects that this is your most
reliable demand signal — cleaner than your intuition about the weekend.

**F2: "The Event We Forgot"**
BEFORE: Local marathon Sunday. Nobody flagged it. Bar ordered for a normal
Sunday. Marathon runners flooded brunch service. 40-minute waits. 86'd items.
$1,200 in lost revenue from turned tables.
AFTER: "Community calendar: Local Marathon (12,000 runners) — Sunday, 9am
finish. Your marathon event pattern (from past events): covers up significantly,
protein and egg orders need to roughly double. Recommend: double protein order, egg delivery Saturday.
Alert: this event is not tagged in your calendar — add for future learning."
The system learns which event types actually move YOUR demand vs which are
noise — from your verified outcomes, not from theory.

**F3: "Your Pars Are Static. Your Demand Isn't."**
BEFORE: Par levels set once, applied uniformly every day of the week. Tuesday
lunch wastes 18% protein. Friday dinner runs out. Same par level, different
demand. Nobody has quantified the day-of-week structure in ordering.
AFTER: After 90 days of verified orders: "Day-of-week demand profile learned.
Tuesday lunch: 62% of Friday dinner demand. Recommend: two-tier ordering —
Tue-Thu at 70% of Fri-Sat par. This adjustment reduces weekly protein waste by
an estimated $180 and eliminates Friday 86's. Based on your last 48 weeks of
verified orders."
Day-of-week turns out to be the second-most reliable demand signal
for most restaurants — right after weather.

*Pitch note:* Do not lead with "Tuesday is not Friday" as a standalone line —
owners know this and it sounds obvious. Lead with the waste number and the
dynamic par solution. Better opener: "Stop ordering Tuesday like it's Friday."

---

## §4 — Technology Value → Business Value

| Innovation | Technology | Buyer Sees | Scenarios |
|---|---|---|---|
| Centroid learning | Verified orders move learned vectors | "Par levels update themselves. Overcharges caught." | P1, P2, P4, M2 |
| Conservation law | Mathematical quality invariant | "Proof that $600 auto-approve is safe. System pauses itself." | P3, I3 |
| DiagonalKernel | Per-factor noise fingerprint | "Works with messy POS + QuickBooks from Day 1." | P9 |
| Cross-graph attention | Discovers patterns across data sources | "Connected invoice history to commodity data to local events." | P7, P8, M8, I4 |
| Re-convergence (γ>1) | Recovery faster after each disruption | "Second avian flu shock: 2 weeks, not 8." | P10 |
| Judgment memory | Per-factor σ learned from verified outcomes | "When Rosa left, system kept everything she knew." | P4, P5, I1 |
| Signal-confidence inversion | Trusted factor = noisiest predictor | "The factor you trust most is the one that lies to you." | I1, P9 |
| Price memory | Episodic + judgment + decision support | "System remembers every negotiated rate at the moment of order." | I2 |
| Personnel quality detection | Conservation detects quality change | "System flagged that new manager's decisions differ." | I3 |
| Weather intelligence | Learned weather-demand pattern | "Learned rain means -28% covers. Adjusted before the storm." | F1 |
| Event intelligence | Learned event-demand pattern | "Marathon Sunday: automatically adjusted 4 days before." | F2 |
| Day-of-week model | Learned daily demand profile | "Tuesday is not Friday. Two-tier par reduces waste 18%." | F3 |
| AgentEvolver | Self-tuning within conservation bounds | "Format fix: $2K/month saved. Transferred to all locations." | I5, I8 |
| IKS as bankable asset | Quantified institutional knowledge | "Proof for bank: purchasing improving every quarter." | I7 |

---

## §5 — Differentiation & Positioning

### The Competitive Test

| Question | BlueCart | MarketMan | Upserve | Us |
|---|---|---|---|---|
| After 1,000 orders, show improvement | Can't | Can't | Can't | Here it is |
| Prove $600 auto-approve is safe | "Set threshold" | Same | Same | Theorem + audit trail |
| When my chef leaves, what survives? | Order history | Cost data | None | 1,200 verified decisions — every pattern Rosa learned |
| Which suppliers are behaviorally identical? | Can't | Can't | Can't | Behavioral clustering |
| My POS data is messy — works Day 1? | "Export clean CSV" | Same | Same | Learns trust from Day 1 |
| Is this price increase the market or supplier? | Can't | Can't | Can't | Decomposition: market + markup |
| SupplierCo declining — warn 2 months early? | Can't | Can't | Can't | Cross-system trend detection |
| Which factor is my trust trap? | Can't | Can't | Can't | Signal-confidence inversion |
| System remembers negotiated prices? | Search manually | Same | Same | Auto-surfaces at decision point |
| Rainy Saturday → adjust before I ask? | Can't | Can't | Can't | Weather factor, automatic |

### Positioning Statement

**The hero one-liner (validated 9-10/10 across 3 LLMs):**
> *"BlueCart stores the order. We store the leverage."*

BlueCart, MarketMan, and Upserve manage purchasing PROCESS. We improve
purchasing DECISIONS. They handle the mechanics — sending orders, tracking
costs, logging invoices. None of them learn which decisions produce better
outcomes. We are the brain sitting on top of the brawn they already have.

After 12 months, the system encodes your suppliers, your kitchen, your local
demand patterns. Switching means starting over. That's the moat at independent
restaurant scale.

**The elevator pitch for Marco:** "After 1,000 orders, this system knows your
kitchen better than anyone who's ever worked for you — and it never leaves."

**The CFO pitch for Rafael:** "1-3 points off food cost. In a $28M hotel F&B
operation, that's $84-280K. The system proves it's getting there every quarter."

BlueCart, MarketMan, and Upserve manage purchasing PROCESS. We improve
purchasing DECISIONS. They're Clock 1 — same logic on Day 365 as Day 1.
We're Clock 3 — calibrated to YOUR suppliers, YOUR kitchen, YOUR local
demand patterns.

After 12 months, 315 learned values (140 category patterns + 175 factor weights)
encode your operation's purchasing reality. Switching means starting over.
That's the moat at independent restaurant scale.

**The elevator pitch for Marco:** "After 1,000 orders, this system knows your
kitchen better than anyone who's ever worked for you — and it never leaves."

---

## §6 — Unlocks (Quantified for $1.5M Annual Revenue Restaurant)

| # | Unlock | Scenarios | KPI | Y1 Value |
|---|---|---|---|---|
| 1 | Over-order detection + par level intelligence | P1, P2 | Food cost % reduction | $20-40K |
| 2 | Overcharge detection + price memory | P4, I2, M8 | Overpayment $ caught | $15-30K |
| 3 | Auto-approve expansion with proof | P3, I3 | Owner/chef time freed | $12-22K |
| 4 | Knowledge survives personnel change | P5, I1 | Ramp time, mistake cost | $20-45K |
| 5 | Supplier consolidation | P6 | Overhead + volume pricing | $8-15K |
| 6 | Early warning on supplier decline | P7 | Disruption cost avoided | $10-25K |
| 7 | Cross-system discovery + commodity decomposition | P8, M8, I4 | Re-quoting, markup detection | $10-20K |
| 8 | Weather intelligence | F1 | Waste from rain-day over-ordering | $5-12K |
| 9 | Event intelligence | F2 | 86's and overstock from events | $5-10K |
| 10 | Day-of-week model | F3 | Protein and produce waste reduction | $8-18K |
| 11 | Faster disruption recovery | P10 | Recovery cost reduction | $8-20K |
| 12 | Self-tuning + format fix | I5, I8 | Coordinator time savings | $5-12K |
| 13 | IKS as bankable asset | I7 | Credit terms improvement | $3-8K |
| | **PORTFOLIO** | | | **$129-277K** |

**Pricing:** $299-799/month ($3.6-9.6K/year). ROI at $499/month: 22-46×.

---

## §7 — Architecture & Feature Sets

### 7.1 DomainConfig (IMPLEMENTED ✅)

**5 categories × 4 actions × 7 factors = 140 centroid values + 175 DK weights = 315 total**

**Categories (C=5) — ORDER IS PERMANENT:**

| Index | Category | Description | Volume |
|---|---|---|---|
| 0 | protein | Meat, poultry, seafood, eggs | 35% |
| 1 | produce | Fruits, vegetables, fresh herbs | 25% |
| 2 | dairy | Milk, cream, cheese, butter | 15% |
| 3 | dry_goods | Pantry, canned, frozen, dry staples | 15% |
| 4 | beverages | Non-alcoholic, coffee, juice, mixers | 10% |

**Actions (A=4) — ORDER IS PERMANENT:**

| Index | Action | Description |
|---|---|---|
| 0 | order_as_planned | Proceed with planned quantity |
| 1 | order_more | Increase quantity (demand spike anticipated) |
| 2 | order_less | Reduce quantity (waste risk or demand drop) |
| 3 | skip | Do not order this cycle (sufficient stock or demand absent) |

**Factors (d=7) — ORDER IS PERMANENT:**

| Index | Factor (code) | Display Name (UI/narrative) | What It Measures | Source |
|---|---|---|---|---|
| 0 | expected_demand | Expected Demand | Predicted covers × category consumption rate | POS history |
| 1 | day_of_week | Day of Week | Day-of-week demand multiplier (learned) | Timestamp |
| 2 | weather_forecast | Weather Forecast | 3-day forecast impact on demand (learned) | Weather API (free) |
| 3 | event_flag | Local Events | Local events, holidays, private bookings impact | Calendar + verified outcomes |
| 4 | historical_waste | Waste History | Category waste rate from verified orders | Order outcomes |
| 5 | supplier_lead_time | Whether They Show Up | Actual vs promised delivery lead time + OTIF history | Delivery verification |
| 6 | price_memory_index | What They Charge | Current price vs learned norms for supplier×category | Invoice history |

**Factor name mapping from v1.1:**
- v1.1 `quoted_price` → v1.2 `price_memory_index` (display: "What They Charge")
- v1.1 `delivery_history` → v1.2 `supplier_lead_time` (display: "Whether They Show Up")
- v1.1 `quality_history` → absorbed into `supplier_lead_time` (OTIF includes quality)
- v1.1 `order_frequency` → absorbed into `expected_demand` (POS velocity)
- v1.1 `market_correlation` → separate commodity decomposition (M8, v1.1 feature)
- v1.1 `volume_leverage` → absorbed into `price_memory_index` (volume pricing norms)
- v1.1 `data_confidence` → implicit in DiagonalKernel per-factor σ (not a factor itself)

**In scenarios and UI, always use Display Names.** In code, always use
Factor (code) names. The NL evidence templates (§11.1) use Display Names.

**Note on price_memory_index (factor 6):** This is the price intelligence
factor. High = price within learned norms. Low = anomalous spike or hidden
discount. Feeds scenarios I2, P4, M8 directly. Legacy migration path:
(5,4,6) → (5,4,7) is implemented via `_migrate_legacy_centroids()`.

**Hyperparameters:**
- penalty_ratio = 3.0 (ordering errors recoverable — composting beats stockout cost)
- η_confirm = 0.05, η_override = 0.01 (Gemini-derived, same as all copilots)
- τ = 0.1, q_window = 400

### 7.2 Feature Sets

**v1.0 (Day 1, open source / self-hosted):**

| Feature | Description | Scenario |
|---|---|---|
| F1: Spend Dashboard | Food cost % by category × supplier × period. POS + QBO. | M1 |
| F2: Delivery Match | Three-way match (order × delivery × invoice). 80% auto, 20% queue. | M2 |
| F3: Smart Order Queue | Prioritized by waste risk × demand signal × supplier risk. | P1-P4 |
| F4: Evidence Panel | NL evidence per order: "Rain Saturday: reduce protein 30%. Confidence 0.87." | F1, F2, F3 |
| F5: One-Click Verify | Confirm/override with reason. ProfileScorer.update(). Hash-chain write. | All |
| F6: Conservation Dashboard | GREEN/AMBER/RED per category. Auto-approve expansion with proof. | P3 |
| F7: Auto-Approve Engine | Conservation-gated auto-approval at item × supplier level. | P3 |
| F8: Par Level Intelligence | Learned par from consumption. Seasonal adjustments. Excess surfacing. | P1, P2 |
| F9: IKS Tracker | IKS 0→62 trajectory. Per-category breakdown. | I7 |
| F10: Supplier Scorecard | OTIF, pricing, exception rate, seasonal patterns. Price memory: last 5 rates. | P5, I2 |
| F11: Trust Analysis [HERO] | Radar chart: expected vs actual factor importance (DK weights). Trust trap. | I1 |

**v1.1 (Month 2-4):**

| Feature | Description | Scenario |
|---|---|---|
| F12: Weather Intelligence | weather_forecast factor wired to free API. Auto-adjust orders. | F1 |
| F13: Event Intelligence | event_flag wired to calendar + verified outcomes. Event demand model. | F2 |
| F14: Day-of-Week Model | day_of_week factor analytics dashboard. Two-tier par recommendations. | F3 |
| F15: Commodity Decomposition | Market vs supplier markup split. USDA PPI + FRED. M8 scenario. | M8 |
| F16: Cross-System Discovery | Weekly digest: patterns across POS × invoices × commodity × weather. | P8, I4 |
| F17: Supplier Consolidation | Behavioral clustering from verified orders. Duplicate identification. | P6 |
| F18: AgentEvolver | Self-tuning alert thresholds, format rules, par adjustment heuristics. | I5 |

**v2.0 (Month 6+):**

| Feature | Description | Scenario |
|---|---|---|
| F19: Disruption Recovery | L2 fallback, re-calibration, γ>1 recovery dashboard. | P10 |
| F20: Multi-Location Transfer | AgentEvolver pattern promotion across locations. | I8 |
| F21: Payment Timing Intelligence | Per-supplier payment behavior. Early-pay vs extend analysis. | New |
| F22: Audit & Export Pack | SOX-adjacent decision trail. Conservation proof. Override history. | I7 |

---

## §8 — What Ships When

| Version | What | Weeks | Scenarios | Key Features |
|---|---|---|---|---|
| **v0.1** | **Preview tab in demo** | **DONE** | **P1, P3, I1 partial** | **Domain config, basic queue, conservation, par levels** |
| **v1.0** | **Full copilot** | **8-12** | **M1, M2, P1-P7, I1, I2, I3** | **F1-F11: Spend, match, queue, evidence, verify, conservation, par, IKS, scorecard, trust** |
| **v1.1** | **+ Intelligence layer** | **14-18** | **+P8, P9, M8, I4, I5, F1, F2, F3** | **F12-F18: Weather, events, DoW, commodity, discovery, consolidation, AE** |
| **v2.0** | **+ Disruption + multi-location** | **20-28** | **+P10, I7, I8** | **F19-F22: Recovery, transfer, payment, audit** |

### 8.1 Day 1 Experience (Time to Value)

**First hour (Toast POS connected):**
"Connect Toast POS. Import 500 orders. In 20 minutes, the system
shows your first supplier fingerprint — which of your 30 suppliers
has the cleanest delivery record, which one's pricing is volatile,
and which factor you've been checking first that matters least.
The trust trap is visible before lunch."

**First week (50 verified order reviews):**
"The radar chart sharpens for your top 5 suppliers. Price memory
reveals the first unchallenged increase: 'Supplier X quoted
$14.20/lb for salmon. Last negotiated: $12.40/lb (PO-2847,
October). This supplier's pattern: raises 8-12% after 6 months
if not challenged (N=4).' Your chef says: 'How did it know that?'
Answer: it remembered what Toast and QuickBooks stored but nobody
queried."

**Month 1 (200 verified orders):**
"Weather factor activates: 'Rain Saturday → protein -28%.
Adjusted before you asked.' Day-of-week profile learned:
'Tuesday is 62% of Friday. Two-tier par reduces weekly protein
waste by $180.' Conservation: first auto-approve candidate
identified. Your food cost dropped 1.2 points and you haven't
changed the menu."

**Why this matters for the pitch:** The buyer doesn't need 24 weeks
to see value. They need 1 hour to see the fingerprint, 1 week
to see price memory, and 1 month to see weather intelligence.
The 24-week trajectory is where compounding kicks in — but the
system earns attention on Day 1.

### 8.2 Weekly Recovered-Dollar Report (from LLM poll feedback)

**What Marco needs to keep paying after Day 1:** Not a dashboard.
Not a model explanation. A weekly money trail:

- "We found $412 this week."
- "We prevented $180 in waste."
- "We flagged $230 in price variance."
- "Net recovered this month: $1,820."

This is the retention mechanism. The system must produce a simple,
human-readable weekly report showing dollars found, waste prevented,
and supplier flags surfaced — tied to specific orders and suppliers.
If the owner can't see recovered dollars weekly, they cancel.

**Implementation:** Automated email or in-app digest every Monday.
Pulls from verified decisions + conservation log + price memory
alerts. No AI narration — just facts and dollars.

### 8.3 Chain Learning as Top Angle (from LLM poll feedback)

All three LLMs rated chain learning as the strongest multi-location
angle — Grok: "strongest angle in the entire deck." Gemini: "the
holy grail." GPT: "one location's scar tissue becomes every
location's warning system."

**For Lisa (4-location chain):** The pitch is not "this location
learned something." It's: "your best location's purchasing
discipline becomes the baseline for all four." Cross-location
benchmarking: same item, different supplier price. Same supplier,
different location performance. Waste differences by location.
Standardized purchasing playbooks for new managers.

**Pricing validated:** $799-1,200/month across 4 locations ($200-300
per store). All three LLMs confirmed this is an easy "yes" for an
ops director. Chain learning should be promoted from a buried
transfer scenario (I8) to a primary sales angle for multi-location
buyers.

---

## §9 — Backend Integrations

### Priority Order (revised v1.2)

| Priority | Integration | Why | Effort |
|---|---|---|---|
| **P0** | Toast POS | Primary order/sales data for restaurants. 110K+ US restaurants. Real-time sales, covers, item-level data. | 2w |
| **P0** | CSV/Excel Upload | Universal fallback. Any POS export. Zero integration friction. | 3d |
| **P1** | QuickBooks Online | Accounting layer — invoices, vendor records, payment history. 65% SMB market share. | 2w |
| **P2** | Lightspeed | Alternative POS (retail F&B, cafés, hotels). | 1w |
| **P2** | Square for Restaurants | SMB quick-service, cafés. | 1w |
| **P3** | Weather API (OpenMetro / NOAA) | Free. 3-day forecast. Feeds weather_forecast factor directly. | 3d |
| **P3** | USDA PPI / FRED | Free public data. Commodity context for M8 scenario. | 3d |
| **P4** | Gmail / Outlook | Quote email parsing (Claude API extraction). | 2w |
| **P4** | Xero | Accounting alternative (NZ/AU/UK heavy, growing US). | 1w |

### Toast POS Integration

```python
class ToastPOSConnector:
    """Toast API connector — Tier 1 source (trust weight 1.0).
    
    Auth: Toast partner OAuth 2.0.
    Endpoints: /orders, /menuItems, /restaurants/{guid}/orderHistory
    Webhooks: Order.Complete → trigger demand update
    Mock: if DEMO_MODE: return json.load(fixtures["pos_orders"])
    """
    def sync_order_history(self, since: datetime) -> list[SalesRecord]: ...
    def sync_menu_items(self) -> list[MenuItem]: ...
    def get_covers_by_day(self, start: date, end: date) -> dict[date, int]: ...
    def register_webhooks(self) -> None: ...
```

### Factor Source Mapping

| Factor (code) | Display Name | Primary Source | Fallback | Trust Weight |
|---|---|---|---|---|
| expected_demand | Expected Demand | Toast POS (covers × item velocity) | Manual estimate | 0.91 (Toast) / 0.45 (manual) |
| day_of_week | Day of Week | Order timestamp | Inherent | 1.00 |
| weather_forecast | Weather Forecast | OpenMetro API (free) | None | 0.82 (learned per location) |
| event_flag | Local Events | Google Calendar + verified outcomes | Manual calendar | 0.81 (calendar) / 0.34 (manual) |
| historical_waste | Waste History | Verified order outcomes | None | Learned from decisions |
| supplier_lead_time | Whether They Show Up | Delivery verification (QBO + manual) | Supplier promise | 0.11 (self-reported) |
| price_memory_index | What They Charge | QBO invoice history | CSV upload | 0.91 (QBO) / 0.71 (CSV) |

---

## §10 — Dataset Specifications

### DS1: Supplier Profiles (30 suppliers, food service archetypes)

| Archetype | Count | Purpose | Key behavior |
|---|---|---|---|
| Gold reliable | 5 | Baseline | OTIF 96%+, stable pricing |
| Seasonal premium | 2 | P4 scenario | +12-18% Nov-Dec seafood pricing |
| Declining | 2 | P7 scenario | OTIF dropping 2.5%/month |
| Trust trap | 2 | I1 scenario | Good rep, mediocre measured OTIF |
| Behavioral duplicates | 6 (3 pairs) | P6 scenario | Delivery r>0.93 |
| Commodity-linked | 3 | M8 scenario | Pricing tracks USDA PPI (r>0.82) |
| Price memory | 3 | I2 scenario | Raises 8-12% at 6-month mark |
| Format changer | 1 | I5 scenario | Changed invoice format 3 months ago |
| New / unproven | 3 | new_supplier orders | <4 months history |
| High-frequency basic | 3 | Dairy / dry goods | Daily or 3×/week delivery |

Each supplier has 24-month behavioral profile: monthly OTIF, pricing trend,
exception rate, lead time distribution, seasonal pattern.

### DS2: Order History (500 demo orders, 5K test orders, 24 months)

Category mix: protein 35%, produce 25%, dairy 15%, dry_goods 15%, beverages 10%.

Embedded patterns (ground truth):
- Seasonal protein premium: November (seafood +15%), August (produce stress)
- Weather events: 18 rain days, demand drop 22-35%
- Local events: 6 high-impact events (sports finals, marathons, festivals)
- Day-of-week structure: Tuesday 62% of Friday, Wednesday 71%, weekend 110-140%
- Personnel change: Month 14 (different approval/ordering patterns)
- Supplier 8 OTIF decline: months 16-20 (93→74%)
- Supply disruption: Month 9 (avian flu — egg shortage, 6-week recovery)
- 3 embedded duplicate invoices
- 28 delivery quantity discrepancies
- Format change: Supplier 12, month 21

### DS3: Commodity / Market Data (24 months, real public data)

| Index | Source | Purpose |
|---|---|---|
| USDA PPI Poultry | fred.stlouisfed.org | M8 chicken pricing decomposition |
| USDA PPI Beef | fred.stlouisfed.org | M8 beef pricing decomposition |
| Arabica coffee futures | Nasdaq Data Link (free tier) | I4 correlation scenario |
| Baltic Dry Index | Public | Package/shipping correlation |
| OpenMetro historical | openmeteo.com | F1 weather intelligence |

**Download once. Real data. No synthesis needed.**

### DS4: POS Sales Records (24 months, synthetic but realistic)

Daily covers by day-of-week, event-adjusted, weather-adjusted.
Item-level velocity per category. Used to compute expected_demand factor.
Seasonal variation: summer +15% covers, January -22%, event days +40-80%.

---

## §11 — Engineering Specifications

### 11.1 NL Evidence Templates

**Jargon-to-kitchen-language mapping (mandatory for all customer-facing text):**

| Never say | Always say |
|---|---|
| "Centroid geometry" | "Everything the system learned from your orders" |
| "DK weight 94%" | "Your most reliable signal" |
| "N=23 rainy Saturdays" | "23 rainy Saturdays" (drop the N=) |
| "σ=0.07" | "Very reliable" or "consistent" |
| "Price Position" or "price_memory_index" | "What they charge" |
| "Delivery Reliability" or "supplier_lead_time" | "Whether they show up on time" |
| "Factor vector" | "Decision factors" |
| "Conservation law GREEN" | "Auto-approve is safe for this supplier" |
| "η_confirm = 0.05" | Never shown to operators |
| "DiagonalKernel weights" | "How much the system trusts each signal" |

**The trust trap vocabulary (I1) must use kitchen language:**

Not: "quoted_price has σ=0.29, DK weight 8% vs delivery_history σ=0.06, weight 97%"

Use: "What they charge — the thing you check first — is your least reliable
signal. Whether they show up on time — which nobody checks at order time —
predicts your outcomes better than any other factor. You've been watching the
wrong number."

```python
class PurchasingTemplateEngine:
    """Deterministic evidence templates for purchasing decisions."""

    PROTEIN = (
        "{item} from {supplier}: {quantity} {unit} at ${price}/{unit}. "
        "{price_context}. "       # "Within historical range ±3%."
        "{demand_context}. "      # "Weather: rain Saturday → demand -28%."
        "{recommendation}."
    )

    PRODUCE = (
        "{item} from {supplier}: {quantity} {unit}. "
        "{supplier_otif_context}. "  # "August OTIF: 68%. Order 5 days early."
        "{waste_context}. "           # "Historical waste rate: 14% (high)."
        "{recommendation}."
    )

    DAIRY = (
        "{item} from {supplier}: {quantity} {unit} at ${price}/{unit}. "
        "{par_context}. "          # "Par: 8 units. Recommended: 6 (demand -15% this week)."
        "{recommendation}."
    )

    DRY_GOODS = (
        "{item} from {supplier}: {quantity} {unit}. "
        "{consumption_context}. "  # "30-day consumption: 42 units. Par aligned."
        "{recommendation}."
    )

    BEVERAGES = (
        "{item} from {supplier}: {quantity} {unit} at ${price}/{unit}. "
        "{event_context}. "        # "Marathon Sunday: +45% demand. Adjust."
        "{recommendation}."
    )

    # Trust trap template (I1 hero — uses plain language, not code names)
    TRUST_ANALYSIS = (
        "Factor trust analysis for {supplier}:\n"
        "  {display_name}: σ={sigma:.2f}, DK weight {weight:.0%} — {label}.\n"
        "  Most trusted: {top_factor_display} (weight {top_weight:.0%}).\n"
        "  Least trusted: {bottom_factor_display} (weight {bottom_weight:.0%}).\n"
        "  {inversion_note}."  # "You check what they charge first. The system ignores it."
    )

    # Price memory template (I2)
    PRICE_MEMORY = (
        "Last negotiated: ${last_price}/{unit} ({po_ref}, {date}). "
        "Current quote: ${current_price} ({delta}%). "
        "{pattern}."  # "This supplier raises 8-12% at 6-month mark (N=4)."
    )
```

### 11.2 API Endpoints

| Endpoint | Method | Purpose | Phase |
|---|---|---|---|
| /api/purchasing/spend | GET | Spend dashboard by category × supplier × period | v1.0 |
| /api/purchasing/match | GET/POST | Delivery match queue + resolution | v1.0 |
| /api/purchasing/queue | GET | Prioritized order queue | v1.0 |
| /api/purchasing/score | POST | Score an order | v1.0 |
| /api/purchasing/verify | POST | Confirm/override + reason code | v1.0 |
| /api/purchasing/conservation | GET | Conservation status per category | v1.0 |
| /api/purchasing/iks | GET | IKS score and trend | v1.0 |
| /api/purchasing/par-levels | GET | Par level recommendations | v1.0 |
| /api/purchasing/supplier/{id} | GET | Supplier scorecard + price memory | v1.0 |
| /api/purchasing/trust/{id} | GET | Trust analysis (DK weights radar) | v1.0 |
| /api/purchasing/weather | GET | Current forecast + demand adjustment | v1.1 |
| /api/purchasing/events | GET | Upcoming events + demand impact | v1.1 |
| /api/purchasing/commodity/decompose | POST | Market vs markup analysis | v1.1 |
| /api/purchasing/discovery/digest | GET | Weekly cross-system discoveries | v1.1 |
| /api/purchasing/evolution/log | GET | AgentEvolver history | v1.1 |

---

## §12 — Open Questions (Updated v1.2)

1. **Toast vs Square first?** Toast has 110K+ restaurant customers and the
   richest data model. Square is higher volume (more cafés/SMB). Recommend:
   Toast first (richer data → better factors), Square fast-follow.

2. **Google Calendar integration for event_flag?** Free API, read-only scope.
   Biggest event_flag data source. Alternative: manual event entry in UI.
   Recommend: optional Google Calendar OAuth in v1.0, mandatory in v1.1.

3. **Weather API: OpenMetro vs NOAA?** Both free. OpenMetro is newer, has
   better API ergonomics. NOAA is authoritative but complex. Recommend:
   OpenMetro for v1.0 (3-day hourly forecast, JSON, no key needed).

4. **Pricing model:** $299-499/month for 1 location, $799-1,200/month for
   chains (2-5 locations). Per-location pricing scales naturally.

5. **Multi-location timing:** I8 (chain learning transfer) is v2.0 in the
   coding sequence. But Lisa's chain persona is a v1.0 buyer — she'll pay
   for the single-location learning even before transfer is built. Don't
   defer Lisa for I8.

6. **S2P overlap boundary — CONFIRMED:** ERP complexity, not revenue. QBO/Toast
   → Purchasing copilot. SAP Business One/NetSuite → Purchasing with richer
   connectors. SAP S/4HANA → S2P. A $5M restaurant group on QBO is a
   Purchasing buyer. A $15M restaurant on NetSuite is an edge case — use
   connector complexity as the tie-breaker.

7. **Manufacturing use case deferred, not abandoned:** The PD v1.1
   manufacturing scenarios (Midwest Steel, Chen-Lin lead times, tariff shocks)
   are valid for a FUTURE purchasing-for-manufacturers vertical. The food
   service domain is built first because: (a) it's implemented, (b) faster
   compounding, (c) cleaner factors, (d) distinct buyer from S2P. When the
   food service copilot reaches product-market fit, the manufacturing vertical
   gets a v2.x PD using the same architecture.

---

## APPENDIX A — MAP Queue Items

### Phase 0: Foundation (STATUS: LARGELY DONE)

| # | ID | What | Effort | Status |
|---|---|---|---|---|
| P1 | **PUR-DOMAIN-CONFIG** | (5,4,7) food service preset | — | ✅ DONE |
| P2 | **PUR-SYNTH-DATA** | 30 supplier profiles (food service archetypes) + 500 demo orders | 2d | **ACTIVE** |
| P3 | **PUR-CENTROIDS** | Bootstrap centroids with migration from (5,4,6) | — | ✅ DONE (migration code exists) |
| P4 | **PUR-PREVIEW-API** | Preview endpoints — scan needed to confirm | — | Likely partial |
| P5 | **PUR-PREVIEW-TAB** | Preview tab in demo | — | Likely partial |

### Phase 1: Full Copilot v1.0

| # | ID | What | Effort |
|---|---|---|---|
| P6a | **PUR-TOAST-CONNECTOR** | Toast POS API. Order history, covers, item velocity. Webhooks. | 2w |
| P6 | **PUR-QBO-CONNECTOR** | QuickBooks Online API. Invoices, vendors, payment history. | 2w |
| P7 | **PUR-FACTORS** | 7 factor computers (§11.2 spec). Likely partially done. | 1w |
| P8 | **PUR-SPEND-DASH** | F1: Food cost dashboard by category × supplier × period. | 3d |
| P9 | **PUR-MATCH-ENGINE** | F2: Three-way match (order × delivery × invoice). | 1w |
| P10 | **PUR-ORDER-QUEUE** | F3+F4: Smart queue + NL evidence templates (§11.1). | 1.5w |
| P11 | **PUR-VERIFY** | F5: Confirm/override + reason code + hash-chain write. | 1w |
| P12 | **PUR-CONSERVATION** | F6+F7: Conservation dashboard + auto-approve engine. | 3d |
| P13 | **PUR-PAR-LEVELS** | F8: Par level intelligence from consumption + seasonality. | 1w |
| P14 | **PUR-IKS-SCORECARD** | F9+F10: IKS + supplier scorecard + price memory index. | 1.5w |
| P15 | **PUR-TRUST-ANALYSIS** | F11: Trust radar chart [HERO]. Expected vs actual DK weights. | 1w |

### Phase 1.1: Intelligence Layer

| # | ID | What | Effort |
|---|---|---|---|
| P16 | **PUR-WEATHER** | F12: Weather API integration (OpenMetro). weather_forecast factor wired. | 1w |
| P17 | **PUR-EVENTS** | F13: Event calendar integration + demand model. event_flag wired. | 1w |
| P18 | **PUR-DOW-MODEL** | F14: Day-of-week analytics dashboard. Two-tier par. | 3d |
| P19 | **PUR-COMMODITY** | F15: USDA PPI + FRED feeds + decomposition endpoint. | 1w |
| P20 | **PUR-DISCOVERY** | F16: Weekly cross-system discovery digest. | 2w |
| P21 | **PUR-CONSOLIDATION** | F17: Behavioral clustering for supplier consolidation. | 1w |
| P22 | **PUR-AGENT-EVOLVER** | F18: AgentEvolver with purchasing variant dimensions. | 2w |

### New MAP Items (v1.2)

| MAP# | ID | Effort | What |
|---|---|---|---|
| #108 | PUR-DOMAIN-REFRAME | ✅ DONE | This document — PD v1.2 written |
| #109 | PUR-TOAST-CONNECTOR | 2w | Added as P6a — higher priority than QBO |

### AE Variant Dimensions (P22)

Purchasing AgentEvolver will have:
- `order_quantity_threshold`: how much to adjust before flagging (±15% vs ±20%)
- `weather_sensitivity`: when to trigger weather adjustment (forecast confidence ≥0.70 vs ≥0.80)
- `event_lead_time`: how far in advance to adjust for events (3 days vs 5 days)
- `price_memory_alert`: how much price deviation before surfacing memory (8% vs 12%)

---

## Scenario Coverage by Phase

| Phase | Scenarios Covered | Count |
|---|---|---|
| v0.1 (now) | P1, P3, I1 (partial) | 3/23 |
| v1.0 | +M1, M2, P2, P4-P7, I2, I3 | 13/23 |
| v1.1 | +P8, P9, M8, I4, I5, F1, F2, F3 | 21/23 |
| v2.0 | +P10, I7, I8 | 23/23 |

---

*Purchasing Copilot Product Definition v1.3 · May 29, 2026*
*23 scenarios (5 clusters A-E + Cluster F food service). 22 features.*
*Tensor: 5×4×7 = 140 centroids + 175 DK weights. Domain: food service.*
*Buyers: Marco (restaurant), Lisa (café chain), Rafael (hotel F&B), Karen (consultant).*
*Connector priority: Toast POS → QBO → Weather API → USDA.*
*Hero: I1 — Supplier Trust Trap. Hero line: "The factor you trust most is the one that lies to you."*
*Manufacturing vertical: deferred to v2.x — same architecture, different domain config.*
*MAP items: P1 ✅, P3 ✅, P6a new (Toast). First active action: PUR-SYNTH-DATA (P2, 2d).*
