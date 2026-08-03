# DataOps Copilot Design v1.7
**Date:** May 20, 2026 · **Supersedes:** v1.5 (May 12)
**Changes (v1.6):** §29-§41 NEW — Data Intelligence product definition
layer. Reframes from "better DataOps" to "Data Intelligence" — data
that learns about itself. 6-level hierarchy. 5 buyer personas. 22
scenarios (7 market + 15 innovation). 6 category-defining capabilities.
Data Intelligence Map visualization. Competitive update. 12 demo
moments. Engineering specs for Level 5-6. 11 MAP items (DI-1→DI-11).
§1-§28 unchanged from v1.5.
**Changes (v1.5):** §17 rewritten (ONE store invariant, 13 capabilities).
§27 NEW (SDK Architecture). §28 NEW (Standing Rules 29-35). GS-PROMOTE.
**Changes (v1.4):** Process-Tech Fusion throughout. Real SAP + Celonis.
§25 Enterprise Connectors. §26 Process-Tech competitive positioning.
**Changes (v1.3):** §19-§22 Operational Evolution. Transformation graph.
**Changes (v1.2):** BUILT state. 51 tests. D-1→D-6. SAP named. IKS 19.0.

---

*§1-§28: Engineering design unchanged from v1.5. Full v1.5 text is
the authoritative source for these sections. Key sections:*

*§1 Process-Tech Fusion headline. §4 Architecture (26 endpoints).*
*§5 DomainConfig (6,5,6)=180. §6 Graph Schema (SAP+Celonis+Transform).*
*§13 Pre-seeded (IKS 19.0). §16 Storyboard (5-act, $1.62M).*
*§17 ONE Store (13 capabilities). §18 Self-Computation (3 levels).*
*§25 Enterprise Connectors. §26 Process-Tech Fusion quantified.*
*§27 SDK Architecture. §28 Standing Rules (35).*

---

*DataOps Copilot Design v1.7 · May 20, 2026*
*BUILT: 149 tests, 26 endpoints, D-1→D-6, OE-1→OE-5, IKS 19.0.*
*Enterprise: real SAP (api.sap.com) + real Celonis (Developer Portal).*
*Process-Tech Fusion: WHERE→WHY→WHAT→LEARN→TRANSFER.*
*$1.62M/yr DataOps, $680K/yr S2P. 67% cost reduction. 55% fewer alerts.*
*ONE store (GraphStore). RL shipped. 35 standing rules.*

---

## §29-§41 — Data Intelligence: Product Definition Layer

**Added v1.6 (May 20, 2026).** Reframes DataOps from "better data
quality monitoring" to "Data Intelligence" — a new category where
data learns about itself. Contains: the category shift, 6-level
intelligence hierarchy, 5 buyer personas, 22 scenarios (7 market +
15 innovation), 6 category-defining capabilities, Data Intelligence
Map visualization, competitive update (Databricks/Alation 2026),
12 demo moments, engineering specs for Level 5-6, and 11 MAP items
(DI-1 through DI-11). The engineering design (§1-§28) is unchanged.

**The shift:** "Your data gets smarter every day."

---


## §29 — The Shift

### What We've Been Saying (Too Small)

"We detect data quality issues AND learn from triage outcomes AND
prove automation is safe." This is a better version of Monte Carlo.
It's technically correct. It wins feature comparisons. It doesn't
create a category.

### What We Should Be Saying (The Category)

**"Your data gets smarter every day."**

Every piece of data in an organization has an intelligence profile
that nobody tracks: how reliable is this source, what does it
combine well with, who uses it most effectively, what is it NOT
good at, what ADDITIONAL data would make it more valuable.

Today, data is a passive asset that needs maintenance. Tools clean
it, monitor it, catalog it, query it. The data itself remains
unchanged from Day 1 to Day 1,000.

**We make the data itself accumulate intelligence.**

Day 1: Raw transaction table. IKS = 0. Nobody knows which columns
are reliable, what this data combines with, or what it's worth.

Day 90: The system learned — from verified outcomes, not rules —
that Column A (customer_id) is 99.9% reliable, Column F
(satisfaction_score) is 72% consistent (the sales team enters it
inconsistently), and this table combined with shipping data
predicts churn 23pp better than either alone. Nobody asked for
this discovery. The graph found it.

Day 180: IKS = 74. The data now KNOWS its own reliability profile,
its best combinations, its consumption patterns, its seasonal
variations, and its economic value. It SUGGESTS: "Adding weather
data (free API) would improve demand prediction by 15pp. Estimated
value: $180K/year in better inventory decisions."

**The data didn't change. The INTELLIGENCE ABOUT the data compounded.**

This is the shift: from data-as-infrastructure to data-as-
intelligence. From maintaining pipes to growing a brain.

### Why This Is a Category, Not a Feature

| What exists | What it does | What it doesn't do |
|---|---|---|
| Data catalogs (Alation, Collibra) | Describe data assets | Learn which assets are reliable from verified use |
| Data quality (Monte Carlo, Sifflet) | Detect anomalies | Learn which anomalies matter from triage outcomes |
| Data integration (Fivetran, Airbyte) | Move data between systems | Discover which combinations create value |
| Process mining (Celonis) | Show bottleneck locations | Explain WHY, fix, learn, transfer |
| Data platform (Databricks, Snowflake) | Store + compute | Reason about what the data MEANS for decisions |
| BI (Tableau, Power BI) | Visualize data | Know how RELIABLE the visualization is |
| **Data Intelligence (us)** | **Data that learns about itself** | — |

### The Positioning Statement

"Databricks stores your data. Celonis shows your processes. Monte
Carlo monitors quality. Alation catalogs assets. We make your
data INTELLIGENT — it learns its own reliability, discovers its
own combinations, corrects its own errors, and tells you what
additional data would make it more valuable. After 1,000 verified
decisions, your data estate has an IQ score. It never had one
before."

---

## §30 — The 6-Level Intelligence Hierarchy

Every competitor operates at Level 1-2. We operate at Level 6.
The levels are sequential — each requires all previous levels.

### Level 1: Detection (Table Stakes)

"Your data has a problem."

Schema changed. Pipeline failed. Row count dropped. Freshness
stale. Every monitoring tool does this. Monte Carlo, Anomalo,
Sifflet, Databricks data quality monitoring. It's necessary.
It's not sufficient. It's where every data quality product stops.

### Level 2: Understanding (Emerging)

"Your data has a problem BECAUSE..."

Databricks Unity Catalog lineage. Some root cause attribution.
"The schema change in Table A caused the downstream failure in
Pipeline B." Better than Level 1 but still reactive — tells you
what happened, not what to do or whether it matters.

### Level 3: Self-Correction (Nobody Has This)

"The system FIXED it, because it's seen this pattern before."

After 500 verified data corrections, centroids encode: "Schema
changes from Vendor X always require pre-join filter adjustment."
Month 1: detect and alert. Month 6: detect, recommend fix, wait
for approval. Month 12: detect and auto-fix known patterns.
Conservation law proves each expansion step is safe.

**Mechanism:** Centroid learning (ProfileScorer) + conservation
law (α·q·V ≥ θ_min) + AgentEvolver (pattern promotion/rejection).
**Built?** YES — core loop is 8/8 complete in v1.5.
**Demo moment:** "Six months ago: 3-hour investigation. Today:
auto-fixed in 4 minutes. Same pattern, 8th occurrence."

**What makes this impossible for competitors:** They don't have
a verified outcome loop. Monte Carlo detects. Engineers fix.
The fix is not captured as a training signal. The NEXT time the
same pattern occurs, the same engineer investigates from scratch.

### Level 4: Self-Computation (Nobody Has This)

"The system knows WHY it recommended this fix, and whether to
trust its own recommendation."

The platform reasons about its own decision quality. "My
recommendation is based on 3 similar past fixes with 87%
confidence. The factor I'm most uncertain about is
source_reliability (σ=0.28). If this factor were more reliable,
my confidence would be 94%."

Self-computation INCLUDES process-tech fusion: "The bottleneck
is 42 minutes BECAUSE of a schema change that increased join
fanout 9×. The fix reduces it to 4 minutes. I know this because
I've resolved 3 similar schema-induced bottlenecks."

**Also:** The system that ADMITS FAILURE. AgentEvolver shadow-
tested auto-resolving ALL recurring timeouts. 45% accuracy.
Rejected. The system doesn't just learn what works — it learns
what DOESN'T work and refuses to promote it. No competitor
shadow-tests operational rules and rejects the failures.

**Mechanism:** Self-computation (§18 in v1.5) + AgentEvolver
shadow-test + reject. SC-9 (self-explanation) + SC-10
(self-prediction) shipped.
**Built?** PARTIALLY — SC-9, SC-10 shipped. OE-1→OE-5 shipped.
**Demo moment:** "The system tried a rule. Tested it on 15
decisions. 45%. Rejected. The system that admits failure is the
system you trust."

### Level 5: Democratization (Nobody Has This)

"Anyone can ask, and the answer knows how trustworthy it is."

A business user asks: "What was revenue last month?"

Every other platform: "$4.2M"

Our platform: "$4.2M (confidence 94%). The 6% uncertainty comes
from 3 invoices not yet matched. SAP data is 99% reliable for
this query. Salesforce contributes 40% at 87% reliability. If
you need exact numbers, wait for invoice matching (est. 2 days).
Note: $180K below last quarter — decrease from APAC region where
we changed suppliers."

This answer requires DiagonalKernel (per-source reliability),
cross-graph (connecting revenue to supplier changes), and
conservation (confidence quantification). The non-technical user
gets an answer that's not just RIGHT but TRUSTWORTHY — they know
HOW right it is and WHY.

**Also: integration-as-intelligence.** A non-technical user says
"connect my QuickBooks to my supplier spreadsheet." The system
auto-discovers join keys, computes per-source trust weights,
shows the combined view WITH quality annotations, and after 100
verified uses suggests: "Your spreadsheet delivery dates are
wrong 29% of the time. Adding UPS tracking would improve
supplier reliability by 34pp." This is integration that REASONS
about its own quality — not plumbing.

**Mechanism:** NL Query Engine (DI-3) + Source Profiler (DI-1) +
DiagonalKernel weights + cross-graph traversal.
**Built?** NO — requires DI-1 (source profiler) and DI-3 (NL
engine). Architecture designed. Implementation ~7 weeks.
**Demo moment:** Side-by-side. Left: Databricks Genie answers
"$4.2M." Right: we answer "$4.2M (94% confidence, SAP 99%,
Salesforce 87%, 3 unmatched invoices)." Same question. One answer
is a number. The other is INTELLIGENCE.

### Level 6: Data Strategy (Nobody Has This)

"Your data tells you what ADDITIONAL data would make it more
valuable."

Cross-graph discovery + economic valuation:

"Three data combinations you're not exploiting:
1. Customer orders × weather data = seasonal demand prediction
   (+15pp accuracy, free API). Value: $180K/year.
2. Supplier quality × commodity indices = procurement timing.
   Value: $200K/year.
3. Sales pipeline × industry benchmarks = deal confidence.
   Value: $90K/year.

Two data gaps worth filling:
1. Shipping transit data: improves delivery prediction +34pp.
   Cost to acquire: $12K/year. ROI: 15×.
2. Competitor pricing: improves margin optimization $90K/year.
   Cost to acquire: $36K/year. ROI: 2.5×."

The data estate becomes a STRATEGIC ASSET that advises on its own
enhancement. Nobody does this because nobody has: (a) per-source
trust weights from verified outcomes, (b) cross-graph correlation
discovery, and (c) economic valuation of discovered combinations.

**Also: data monetization.** The system identifies when your
LEARNED DATA has external value. "Your anonymized procurement
patterns are more accurate than published benchmarks. Your
supplier reliability profiles outperform D&B for your industry.
Licensing opportunity: $120K/year." IKS becomes a monetizable
asset. Each curated data product gets its own IKS — showing
maturity: "Customer-360: IKS 72 (mature). ESG data: IKS 8
(still learning, many manual exceptions)."

**Also: agent-ready trust infrastructure.** Databricks says 80%
of databases are now built by AI agents. Those agents need to
know which data to TRUST. Our DiagonalKernel + conservation law
provides the trust layer: "This agent can safely auto-approve
data loads from Source A (conservation GREEN, 340 verified loads).
Source B requires human review (AMBER, quality inconsistent)."
We don't just build OUR copilot — we enable EVERY agent in the
enterprise to make trusted autonomous decisions. The trust layer
sits BETWEEN the data infrastructure and ANY agent using it.

**Mechanism:** Combination Discovery Engine (DI-5) + Data
Valuation Model (DI-6) + Acquisition Advisor (DI-8) + Source
Profiler (DI-1) + per-product IKS.
**Built?** NO — requires Phase C (~6 weeks). Architecture clear.
**Demo moment:** Gold dotted line on Intelligence Map: "Connect
weather API → demand prediction: +$180K/year. Free. Nobody asked.
The graph found it."

---

## §31 — Five Buyer Personas

### Clara — CDO, $800M Industrial Manufacturer

160 data engineers across 3 regions. SAP S/4HANA + Celonis +
Snowflake + Databricks. 2,400 data quality alerts/day. Monte
Carlo deployed — detects anomalies well but "the alert queue is
a treadmill." Engineers resolve the SAME patterns monthly because
the system doesn't learn from resolutions. She hired a consultant
to quantify data quality ROI — $4.2M/year in exception costs.
The consultant left. The $4.2M is back.

**What she'd pay for:** "A system that makes the $4.2M shrink
every quarter — automatically, provably, without the consultant."

**Demo moment that converts her:** The 24-week trajectory:
400 alerts → 180 alerts. $200K/month → $65K/month. Conservation
GREEN at every step. "Show me the math." Conservation law: here.

### Raj — Head of Data Engineering, $200M SaaS Company

12 data engineers. Databricks + dbt + Airflow + Fivetran. The
team spends 40% of their time on data quality issues — responding
to alerts, fixing pipelines, investigating root causes. He can't
hire more engineers (market is brutal). He needs the EXISTING
team to handle 2× the workload without 2× the headcount.

**What he'd pay for:** "Auto-resolve the 60% of alerts that are
repetitive so my engineers focus on the 40% that require thinking."

**Demo moment that converts him:** Auto-approve expansion: 15% →
55% over 24 weeks. "Your 12 engineers just became 18 — without
hiring anyone." Conservation proof that expansion is safe.

### Sarah — Senior Data Engineer, Day-to-Day User

Gets 40 alerts/day. Knows immediately that 20 are noise — but has
to investigate all 40 because the system can't distinguish. Spends
4 hours/day on triage. Has 12 years of pattern knowledge in her
head — knows which pipelines break on Mondays, which vendors send
bad data in Q4, which schema changes matter. None of this is in
any system.

**What she'd pay for:** "A system that already knows what I know.
When I'm on vacation, the replacement doesn't need my brain."

**Demo moment that converts her:** The fingerprint.
"data_freshness: weight 1.00 (cleanest signal). recurrence: weight
0.52 (noisiest)." "That IS what I learned over 12 years. The
system figured it out from 500 decisions in 3 months."

### Michael — VP Data Platform, $2B Financial Services

Oversees 40 data engineers. Compliance pressure: regulators want
to see data quality audit trails. SOX, DORA, operational
resilience. His current stack (Databricks + Great Expectations +
Monte Carlo) gives him detection and validation — but no PROOF
that data quality is improving over time, no audit trail of
automated decisions, no mathematical guarantee of safety.

**What he'd pay for:** "A compliance-grade proof that our data
quality is getting better, not just being maintained."

**Demo moment that converts him:** Hash-chained evidence ledger.
Conservation track record: "GREEN for 180 consecutive days. Every
auto-approved data load traceable to evidence, confidence score,
and conservation state." Regulators accept this.

### Diana — CFO, $500M Consumer Goods

Quarterly close takes 14 days. SAP says $127.3M. Salesforce says
$131.1M. Stripe says $129.4M. Every quarter: 3 days to reconcile.
Same 5 root causes. The data engineering team explains it after
the fact — but never PREVENTS it.

**What she'd pay for:** "Close in 7 days, not 14. Same 5 root
causes, fixed permanently. System that PREVENTS the discrepancy
instead of explaining it afterward."

**Demo moment that converts her:** "APAC: $3.1M currency timing
(7/12 prior instances, auto-approve — conservation proved safe).
Americas: $0.3M novel pattern (escalate to controller). The
system decomposed the gap in 2 hours, not 3 days. And the APAC
pattern will never require investigation again — it's a learned
auto-resolution."

---

## §32 — Top-Down Scenarios (Market-Driven)

From industry research (Databricks State of AI Agents 2026, Monte
Carlo market reports, Gartner Data Quality MQ, analyst briefings).

### Table-Stakes (must have, every competitor has variants)

**D-M1: "Alert Fatigue — 400/Day, 45% Noise"**
BEFORE: Monte Carlo generates 400 alerts/day. 45% are noise
(schema version bumps, partition count changes, expected seasonal
drops). Engineers investigate all 400 because the system can't
distinguish. 160 engineer-hours/day on triage.
AFTER: Month 3: system learned which patterns are noise from 1,500
verified triage outcomes. Noise correctly identified: 45% → auto-
resolved. Engineers triage 220 alerts/day. 88 hours freed.
Month 6: 180 alerts/day. 70 hours freed.

**D-M2: "Data Quality Metrics That Don't Improve"**
BEFORE: Dashboard shows: "Data quality score: 78%." Same number
for 18 months. Nobody can explain why it doesn't improve. New
rules get added, but old patterns persist.
AFTER: "Data quality score: 78% → 84% (6 months) → 89% (12
months). Improvement attributable to: 23 learned correction
patterns, 8 auto-resolved exception types, 3 root causes
eliminated at source." The TREND is the product, not the score.

### Tier 1: Problems competitors acknowledge but can't solve

**D-M3: "The Engineer Who Quit — All Her Patterns Left"**
BEFORE: Sarah built 12 years of pattern knowledge. Which pipelines
break Mondays. Which vendors send bad Q4 data. Which schema
changes cascade. She leaves. Replacement has the same tools.
None of Sarah's knowledge is in any system. 6 months of $180K
mistakes.
AFTER: IKS = 78. Sarah's 5,000 verified decisions compiled into
centroid geometry + DiagonalKernel weights. Replacement starts
Day 1 with everything Sarah accumulated. Fingerprint shows
which factors are signal vs noise — the knowledge that took
Sarah 12 years to build.

**D-M4: "Quarterly Close: 14 Days, Same 5 Root Causes"**
BEFORE: Every quarter. SAP says one number. Salesforce says
another. 3 days to decompose the gap. Same 5 root causes.
Nobody prevents them.
AFTER: 7/12 prior instances of Pattern A: auto-approve
(conservation proved safe 4 months ago). Pattern B: novel.
Escalate. The quarterly close drops from 14 to 7 days because
7 of the 12 standard root causes are handled automatically.

**D-M5: "Can't Hire Enough Data Engineers"**
BEFORE: 12 engineers, 40% of time on triage. Hiring market is
brutal. Can't get to 18. Projects backed up 6 months.
AFTER: Auto-resolve 55% of alerts. 12 engineers effectively
become 18. The capacity gain is proven by conservation law —
not a promise, a mathematical proof that the automation is safe.

### Tier 2: Problems competitors don't even recognize

**D-M6: "Business Users Locked Out of Their Own Data"**
BEFORE: Business user asks "what was revenue last month?" Two
options: wait 2 days for engineering to build a report, or look
at a dashboard that might be stale/wrong and has no confidence
indicator.
AFTER: Quality-aware natural language answer: "$4.2M (94%
confidence). SAP: 99% reliable. Salesforce: 87%. 3 unmatched
invoices. If you need exact: wait 2 days." The non-technical
user gets TRUSTWORTHY answers without engineering involvement.

**D-M7: "We Spent $400K on a Data Quality Project — It's Stale"**
BEFORE: 6-month cleanup initiative. Data quality improved from
72% to 91%. 12 months later: back to 79%. No system maintained
the gains. Told to do it again.
AFTER: Deploy. System learns which sources to trust from Day 1
(DiagonalKernel). Improvements stick because they're encoded in
centroid geometry, not in project documentation. IKS shows the
trend: quality investments are PERMANENT, not temporary.

---

## §33 — Bottom-Up Scenarios (Innovation-Driven)

These emerge from asking: "What does our architecture make possible
that nobody in the data industry has imagined?"

### From DiagonalKernel: Self-Aware Data

**D-I1: "Every Data Asset Knows Its Own Reliability"**
Every table, every column, every source has a learned reliability
profile. Not a static data quality rule — a MEASURED reliability
from verified outcomes.

"Table: customer_orders. Column reliability:
  customer_id:        σ=0.01, weight 99% (near-perfect)
  order_amount:       σ=0.04, weight 94% (occasional rounding)
  satisfaction_score: σ=0.31, weight 14% (sales team inconsistent)
  delivery_estimate:  σ=0.22, weight 28% (supplier self-reported)"

No catalog, no data quality tool, no monitoring platform produces
per-column reliability weights from OUTCOME-CONDITIONED variance.
This requires verified decisions that USE each column + DiagonalKernel
to compute which columns actually predicted correct outcomes.

**D-I2: "Metadata Trust — The Catalog That Knows It's Wrong"**
Data catalogs (Alation, Collibra) store metadata. They don't know
which metadata is RELIABLE. Our system learns: "SAP master data
for vendor addresses: 99% accurate. Salesforce opportunity stages:
72% — the sales team uses them inconsistently. When reconciling,
weight SAP over Salesforce."

DiagonalKernel on metadata trust. Nobody else does this because
nobody else has verified outcomes feeding back into metadata
quality assessment.

### From Cross-Graph: Self-Combining Data

**D-I3: "Combinations Nobody Queried"**
Cross-graph attention discovers value-creating data combinations
that nobody asked about:

"Your customer order data × shipping transit data × weather API =
demand prediction that's 23pp more accurate than orders alone.
Estimated value: $180K/year in inventory optimization."

This discovery happens AUTOMATICALLY from cross-graph sweeps.
The system tried 45 potential combinations. 3 had statistically
significant predictive power. The other 42 were noise — and the
system knows this because DiagonalKernel measured the variance.

**D-I4: "Cross-Pipeline Dependency Nobody Mapped"**
"Your revenue pipeline and inventory pipeline both consume
supplier master data. When the supplier table schema changes,
BOTH break — but revenue breaks 2 days LATER because it has a
cache layer. In the last 6 months, this hidden dependency caused
4 production incidents averaging $12K each."

Nobody mapped this because it requires cross-graph attention
across pipeline execution histories + schema change events +
incident correlation. No single observability tool connects all
three.

### From Conservation Law: Self-Governing Data

**D-I5: "Auto-Approval That Expands Safely"**
Month 1: auto-approve 15% of data loads.
Month 3: conservation proves 35% is safe (500 verified loads,
accuracy 94.2%).
Month 6: 48% safe. Month 12: 55%.
Each expansion step proven by α·q·V ≥ θ_min. If quality dips →
AMBER → auto-approval pauses. No manual threshold tuning. The
mathematics governs the expansion.

**D-I6: "Per-Consumer Quality Routing"**
Same table serves Marketing (real-time freshness, lower quality
bar) and ML pipeline (daily batch, higher quality bar).

"Marketing's dashboard consumes customer_orders with 99.5%
uptime. Quality bar: latency < 1 hour, row count ≥ 90% of
yesterday. The ML pipeline consumes the same table with 98.2%
uptime but flags more issues — their quality bar includes
column-level distribution checks."

The system learns DIFFERENT quality standards per consumer from
their distinct verification patterns. Alerts route differently:
"This break matters for the ML pipeline but not for Marketing.
Route to ML team only."

Nobody does this because nobody tracks per-consumer quality
outcomes.

### From Data Valuation: Self-Valuating Data

**D-I7: "What Should I Buy Next?"**
The system becomes a data acquisition advisor:

"Your data estate has 3 unrealized value opportunities:

1. Add weather API (free): improves demand prediction +15pp.
   Estimated impact: $180K/year. ROI: infinite (free data).

2. Add competitor pricing ($36K/year): improves margin
   optimization by $90K/year. ROI: 2.5×.

3. Add shipping transit data ($12K/year): improves delivery
   prediction +34pp. Estimated impact: $200K/year. ROI: 17×.

Priority: #3 (highest ROI), then #1 (free), then #2."

This requires: (a) cross-graph to discover POTENTIAL combinations,
(b) DiagonalKernel to estimate reliability of the new source,
(c) verified outcome history to quantify the improvement, and
(d) economic model to estimate dollar impact.

**D-I8: "Data Monetization Discovery"**
"Your anonymized procurement patterns are more accurate than
published industry benchmarks for your segment. Licensing
opportunity: $120K/year."

"Your supplier reliability profiles, trained on 10,000 verified
deliveries, outperform D&B ratings for your industry. Potential:
package as a data product for similar manufacturers."

The system identifies when your LEARNED DATA (centroids, weights,
patterns) has external value. The IKS score becomes a monetizable
asset.

### From NL + Trust: Democratized Intelligence

**D-I9: "Connect My Data — No Engineering Required"**
Non-technical user: "Connect my QuickBooks to my supplier
spreadsheet."

System:
1. Parses both sources automatically
2. Discovers join keys (supplier_name ↔ vendor_name, fuzzy match)
3. Shows: "Matched 47/50 suppliers. 3 unmatched (spelling
   variants). Suggested matches: 'Acme Mfg' ↔ 'ACME
   Manufacturing Inc.' — accept?"
4. Computes per-source trust: "QuickBooks invoices: 98%.
   Spreadsheet delivery dates: 71% (last updated 3 weeks ago)."
5. Combined view WITH quality annotations on every field
6. After 100 verified uses: "Your spreadsheet delivery dates
   are wrong 29% of the time. Adding UPS tracking would improve
   supplier reliability factor by 34pp."

This is integration-as-intelligence, not integration-as-plumbing.
The system doesn't just CONNECT sources — it EVALUATES the
connection quality and suggests improvements.

**D-I10: "Quality-Aware Answers for Non-Technical Users"**
"How many customers do we have in APAC?"

Existing tools: "2,847"

Our platform: "2,847 from CRM (94% confidence). Note: 127
customers have no region tag — estimated 40 are APAC based on
billing address. Including estimates: ~2,887. CRM data was last
verified 3 days ago. Salesforce is the primary source (reliability
92%). The ERP customer list shows 2,910 — the difference comes
from 63 wholesale accounts that CRM categorizes differently."

Every claim has provenance. Every number has confidence. Every
source has a reliability weight. The non-technical user makes
BETTER decisions because they know how much to trust the answer.

### From Process-Tech Fusion: Self-Optimizing Processes

**D-I11: "The Fix That Transferred to 6 Pipelines"**
Schema bottleneck fixed in revenue pipeline. Same pattern detected
in billing_api 3 weeks later. Auto-resolved in 15 minutes (vs
3-hour investigation). Pattern promoted via AgentEvolver.

Over 6 months: the same pattern appeared in 6 different pipelines.
Each resolved faster than the last. Total savings from ONE learned
pattern: $340K/year.

No competitor transfers fixes between pipelines because no
competitor has the centroid geometry + AgentEvolver promotion
gate + conservation proof that the fix is safe to auto-apply.

### From Architecture: Three-Channel Improvement

**D-I12: "One Decision, Three Improvements"**
An engineer confirms a triage decision on a schema change alert.
This single verified decision simultaneously:

Channel 1: Pulls the schema_change centroid toward this factor
profile → future similar alerts score more accurately.

Channel 2: Enriches the context graph with a schema-change →
pipeline-failure edge → cross-graph discovery has more data
for pattern detection.

Channel 3: Updates DiagonalKernel weights for source_reliability
and recurrence → the noise fingerprint sharpens.

Three improvement channels from one 10-second confirmation.
Every competitor requires three separate systems (detection
tuning, lineage cataloging, metadata management) to achieve
what one verified decision does here. This is why the
compounding trajectory is exponential, not linear.

### From AgentEvolver: The System That Admits Failure

**D-I13: "Shadow-Tested, Measured, Rejected"**
AgentEvolver proposed: "Auto-resolve ALL recurring timeout alerts."
Shadow-tested on 15 decisions. Accuracy: 45%. Below threshold.
REJECTED. The rule was NOT promoted.

Meanwhile: "Auto-escalate first-time failures from trusted
sources when impact > 0.8." Shadow-tested. 73%. PROMOTED.

No competitor shadow-tests operational rules AND rejects the
failures. Databricks agents execute code. They don't measure
whether the code WORKED, reject it if not, and report the
rejection to the user. "The system that admits failure is the
system you trust."

### From Conservation Law: Agent-Ready Trust Infrastructure

**D-I14: "The Trust Layer Every Agent Needs"**
Databricks reports 80% of databases are now built by AI agents.
Multi-agent systems grew 327% in 4 months. But NONE of those
agents know which data sources to TRUST.

Agent A queries a table. Is the data reliable? How reliable?
Which columns? Under what conditions? No agent knows.

Our platform provides the trust layer:
"Source A (SAP transactions): DK weight 0.94. Conservation
GREEN. 340 verified loads. Safe for autonomous agent use.
Source B (spreadsheet uploads): DK weight 0.14. Conservation
AMBER. Quality inconsistent. Require human review before
agent consumption.
Source C (third-party feed): DK weight 0.71. Conservation
GREEN for trending analysis only. NOT safe for financial
reporting (column 'amount' has 8% variance)."

This isn't just OUR copilot using trusted data. It's EVERY
agent in the enterprise — Databricks agents, LangChain agents,
custom agents — consuming our trust scores before making
autonomous decisions. We become the trust infrastructure layer
that sits between the data platform and the agent layer.

**The business model insight:** Every agent vendor (Databricks,
LangChain, CrewAI, AutoGen) needs a trust layer. None of them
build one. We provide it. This is a PLATFORM play, not a
copilot play.

### From IKS: Data-as-a-Product Intelligence

**D-I15: "Every Data Product Gets an IQ Score"**
Each curated data product — customer-360, supplier-scorecard,
revenue-forecast — gets its own IKS score showing the maturity
of the system's knowledge about that product:

"customer-360: IKS 72 (mature). 3,400 verified decisions.
DiagonalKernel: customer_id reliable (weight 0.98),
satisfaction_score noisy (weight 0.14). Auto-approve rate:
62%. Conservation GREEN 180 days."

"esg-data: IKS 8 (still learning). 120 verified decisions.
Many manual exceptions. Conservation AMBER — quality
inconsistent across reporting periods."

Data consumers (dashboards, ML models, agents) can CHECK the
IKS before consuming. "Is this data product mature enough
for my autonomous pipeline?" → IKS 72, GREEN → yes.
→ IKS 8, AMBER → no, require human validation.

The IKS PER PRODUCT is the metric that makes data-as-a-product
real. Every organization talks about treating data as a product.
Nobody can MEASURE the maturity of a data product. We can.
Because we have verified outcomes feeding back into per-product
centroid geometry.

---

## §34 — The Data Intelligence Map (Visualization)

### The Mind-Blowing Demo Moment

A single visualization that shows the INTELLIGENCE of the data
estate — not the data itself, but what the SYSTEM HAS LEARNED
about the data.

### Design

A network graph where:

- **Each data asset is a node.** Tables, sources, pipelines.
  Size = volume. Brightness = reliability (from DK weights).
  Dim nodes = unreliable data. Bright nodes = trusted data.

- **Lines between assets = discovered correlations.** Found by
  cross-graph attention. Thickness = correlation strength.
  Color = value: green = value-creating, gray = neutral,
  red = contradictory.

- **Pulsing = active learning.** Nodes pulse when verified
  decisions are updating their reliability profile RIGHT NOW.

- **Gold dotted lines = SUGGESTIONS.** Data combinations the
  system has identified but the organization hasn't connected.
  Label: "Connect weather API → demand prediction: +$180K/year."

- **IKS score per cluster.** Data domains (finance, supply chain,
  HR) each have an IKS showing maturity of the system's knowledge.

### The Transformation Over Time

**Day 1:** Scattered gray dots. No lines. A silent, passive data
estate. IKS = 0 everywhere. The screen looks empty.

**Month 1:** First lines appearing between SAP and pipeline data.
Some nodes brightening as DiagonalKernel learns reliability. A
few dim nodes identified: "This spreadsheet is 71% reliable."
IKS = 12.

**Month 3:** Clusters forming. Finance data is a bright cluster
(heavily used, well-verified). Supply chain data has lines but
some red (contradictions between SAP and supplier self-reports).
First gold dotted line: "Connect shipping data → +$200K/year."
IKS = 34.

**Month 6:** Rich network. Bright clusters where the system has
learned most. New gold lines appearing with dollar values. One
cluster is PULSING — active learning from this morning's triage.
A dim node has a warning: "This source's reliability degraded
from 88% to 71% over 3 months. Investigate." IKS = 54.

**Month 12:** Dense, alive, pulsing. Every data asset has a
quality profile, consumption pattern, correlation map, and
economic value estimate. New employees see the ENTIRE intelligence
of the organization's data on one screen. The gold lines show
$1.2M in unrealized value from suggested data combinations.
IKS = 78.

**The demo moment:** Show Day 1 (empty), then animate to Month 12
(rich, alive). "This is what happens when your data gets smarter
every day."

### Technical Implementation

React + D3 force-directed graph. Data from:
- Node brightness: DiagonalKernel per-source weights
- Lines: cross-graph correlation discoveries
- Gold dotted: data combination value estimates
- Pulsing: real-time centroid update feed
- IKS: IKSService per-domain breakdown

This visualization is a HERO screen — the Data Intelligence Map.
It replaces the generic "pipeline dashboard" as the first thing
a buyer sees. The pipeline dashboard says "here are your systems."
The Intelligence Map says "here is what your data KNOWS."

---

## §35 — Competitive Update (2026)

### New Competitors Since v1.5

**Databricks Agent Bricks + Genie Code (March 2026)**

Databricks launched agentic data quality monitoring that "learns
expected data patterns" and Genie Code for autonomous multi-step
data tasks. Multi-agent systems grew 327% on their platform. Over
80% of databases now built by AI agents.

Gap: Databricks learns data PATTERNS (statistical — expected row
counts, schema expectations). They don't learn from TRIAGE
OUTCOMES (judgment — which anomalies matter, which are noise,
which fixes work). When an engineer resolves an alert in
Databricks, that resolution is NOT fed back into the detection
model. There's no centroid evolution, no conservation law, no
signal trust learning. Genie Code writes code; it doesn't learn
WHICH CODE WORKED from verified outcomes.

They have Level 1-2 intelligence (detection + some understanding).
We have Level 1-6 (through data strategy).

**Numbers Station → Alation (May 2025 acquisition)**

Alation acquired Numbers Station ($17M+) to power agentic
capabilities — agents that "find data, interpret it, analyze it,
generate meaningful outputs." Dynamic knowledge graph. Multi-agent
coordination. Conversational analytics.

Gap: Numbers Station learns to QUERY better (better SQL
generation from each interaction). We learn to DECIDE better
(which data quality actions produce correct outcomes). They
optimize the analytics pipeline. We optimize the decision
pipeline. They make FINDING data easier. We make TRUSTING
data possible. They build a knowledge graph of metadata. We
build a knowledge graph of JUDGMENT — what the organization
has learned about its data from thousands of verified decisions.

### Updated Competitive Matrix

```
                    Detect  Understand  Self-     Self-    Democra-  Data
                    issues  root cause  correct   compute  tize      strategy

Monte Carlo         ✅      ⚠️ partial   ❌        ❌       ❌         ❌
Databricks DQ       ✅      ✅ lineage   ❌        ❌       ⚠️ Genie   ❌
Alation+Numbers     ⚠️      ⚠️          ❌        ❌       ✅ NL      ❌
Sifflet             ✅      ⚠️          ❌        ❌       ❌         ❌
Great Expectations  ✅      ❌          ❌        ❌       ❌         ❌
Anomalo             ✅      ⚠️          ❌        ❌       ❌         ❌
Celonis             ❌ diff  ✅ process  ❌        ❌       ⚠️        ❌
Us                  ✅      ✅          ✅        ✅       ✅         ✅
```

Level 3+ is empty for every competitor. This IS the category gap.

---

## §36 — Six Capabilities That Define the Category

These six capabilities together constitute "Data Intelligence"
as a category. Any ONE of them is impressive. All SIX together
are category-defining. Remove any one and the value collapses.

### H1: Self-Aware Data

Every data asset learns its own reliability profile from verified
outcomes. DiagonalKernel computes per-column, per-source precision
weights. No data quality tool does this because none has a verified
outcome loop feeding back into per-source trust computation.

**Demo sentence:** "Your SAP data is 99% reliable. Your Salesforce
data is 87%. Your spreadsheet is 71%. The system learned this from
YOUR decisions, not from rules."

### H2: Self-Combining Data

Cross-graph attention discovers value-creating data combinations
nobody asked about. The system tried 45 potential combinations, 3
had statistically significant predictive power, 42 were noise.

**Demo sentence:** "Your customer data combined with shipping data
predicts churn 23pp better than either alone. Nobody asked for this
discovery. The graph found it."

### H3: Self-Correcting Data

Centroid learning + conservation law enables data that fixes its
own recurring problems. After 500 verified corrections, known
patterns auto-resolve. Conservation proves each expansion is safe.

**Demo sentence:** "Six months ago, this schema change would have
caused a 3-hour investigation. Today the system auto-fixed it in
4 minutes because it's seen this pattern 8 times before."

### H4: Self-Governing Data

Conservation law provides mathematical proof of automation safety.
Per-consumer quality routing learns different standards for
different data consumers. The data governs its own quality
expansion without human threshold tuning.

**Demo sentence:** "Auto-approval expanded from 15% to 55% over
24 weeks. Every expansion step proven by conservation law. Zero
incidents from auto-approved data loads."

### H5: Self-Valuating Data

Cross-graph discovery + economic modeling identifies unrealized
value in the data estate. "Adding weather data would improve
demand prediction by 15pp. Value: $180K/year. Cost: free API."
The data tells you what ADDITIONAL data would make it more
valuable.

**Demo sentence:** "Your data estate has $1.2M in unrealized
value from 3 data combinations you haven't connected yet. Here
they are, ranked by ROI."

### H6: Agent-Ready Trust Infrastructure

Every AI agent — Databricks Genie, LangChain chains, custom
pipelines — needs to know which data to trust before making
autonomous decisions. No agent platform provides this. Our
DiagonalKernel weights + conservation status = the universal
trust layer for any agent consuming enterprise data.

**Demo sentence:** "This Databricks agent queries 4 tables.
Our trust layer tells it: Table A is 94% reliable (GREEN,
safe for autonomous use). Table D is 14% reliable (AMBER,
require human review). The agent adjusts its confidence
accordingly — BEFORE it makes a decision."

---

## §37 — Demo Moments That Create the Category

### The Hierarchy Moment (first 60 seconds)

Show the 6-level hierarchy. "Every competitor is here [point to
Level 1-2]. We are here [point to Level 6]. The gap isn't
incremental. It's architectural. Let me show you."

### The Fingerprint Moment (Sarah's conversion)

Show the DiagonalKernel weights. "data_freshness is your most
reliable signal. recurrence is noise. This is what Sarah learned
in 12 years. The system learned it from 500 decisions in 3
months. When Sarah leaves, this stays."

### The Trust Trap Moment (nobody has this)

"The data source your team trusts most — Salesforce opportunity
stages — is your NOISIEST source (σ=0.31, weight 14%). The source
they rarely check — SAP transaction logs — is your most reliable
(σ=0.04, weight 94%). The factor you trust most is the one that
lies to you."

### The Discovery Moment (Level 6)

Gold dotted line on the Intelligence Map. "Your customer order
data combined with weather data predicts demand 15pp better than
either alone. Free API. $180K/year. Nobody asked for this. The
graph found it."

### The Trajectory Moment (the closer)

The 24-week curve: 400 → 180 alerts. $200K → $65K/month. IKS
0 → 74. Auto-approve 15% → 55%. "This trajectory is impossible
with any other platform. Not because we're better at detection
— because detection is Level 1. We're at Level 6."

### The Conservation Moment (trust builder)

"At every step, the system PROVES the expansion is safe. GREEN
for 180 days. Every auto-approved data load is traceable. Your
regulator can audit every decision. Show me another platform
that provides mathematical proof of safety."

### The Intelligence Map Moment (category definer)

Day 1 → Month 12 animation. "This is what happens when your
data gets smarter every day. Every bright node is a trusted
source. Every line is a discovered correlation. Every gold link
is unrealized value. Your data estate went from silent to
intelligent in 12 months."

### The Agent Trust Moment (platform play)

"Your Databricks agent queries 4 tables before making a decision.
Our trust API tells it: Table A is 94% reliable (GREEN). Table D
is 14% (AMBER, require human review). The agent adjusts its
confidence BEFORE it acts. Without this trust layer, the agent
trusts every table equally — and makes bad decisions on bad data.
We're not just a copilot. We're the trust infrastructure that
every agent needs."

### The Three-Channel Moment (architecture proof)

"Watch what happens when the engineer confirms this one decision.
[Click confirm.] Centroid shifted — better scoring next time.
Graph enriched — new pattern edge created. DiagonalKernel updated
— source reliability sharpened. Three improvements. One click.
Ten seconds. This is why the trajectory compounds."

### The Admits Failure Moment (trust builder)

"The system tried to auto-resolve recurring timeouts. Shadow-
tested on 15 decisions. 45% accuracy. [Shows red REJECTED badge.]
Not promoted. Meanwhile, auto-escalating first-time failures:
73%. [Shows green PROMOTED badge.] The system that admits failure
is the system you trust."

### The Data Product IKS Moment (data-as-product)

"Your customer-360 data product: IKS 72, GREEN, 3,400 verified
decisions. Any agent can consume it autonomously. Your ESG data
product: IKS 8, AMBER, 120 decisions. Still learning. Require
human review. THIS is what data-as-a-product actually looks like
— not a label in a catalog, but a MEASURED maturity score from
verified outcomes."

---

## §38 — Integration Specifications

### J.1 Current (Built + Designed in v1.5)

| System | Status | How it feeds intelligence |
|---|---|---|
| **SAP S/4HANA** | Designed (§25) | Transaction data → factor computers. PO/invoice context enriches every scoring decision. |
| **Celonis** | Designed (§25) | Process data → bottleneck attribution. Activity timing → root cause reasoning. |
| **Graph (AGE/SQLite)** | Built | Decision memory. Centroid checkpoints. Cross-graph traversal. |

### J.2 Needed for Data Intelligence (Level 5-6)

| System | Purpose | Effort | Priority |
|---|---|---|---|
| **NL Query Engine** | Quality-aware natural language answers (Level 5). "What was revenue?" → "$4.2M (94% confidence)." | 3-4w | P1 |
| **Source Profiler** | Per-source, per-column reliability from DK weights. Feeds Intelligence Map. | 1-2w | P1 |
| **Combination Discovery Engine** | Cross-graph sweeps for value-creating data combinations. Gold lines on Intelligence Map. | 3-4w | P2 |
| **Data Valuation Model** | Economic value estimation per data combination. Dollar amounts on gold lines. | 2-3w | P2 |
| **External Data Catalog** | Weather APIs, commodity feeds, industry benchmarks — the "what to connect" library. | 2w | P2 |
| **Snowflake/Databricks Connector** | Read metadata + query results for the NL engine. | 1-2w | P1 |
| **dbt Connector** | Transformation graph enrichment. Model run history + test results → intelligence. | 1w | P2 |
| **Airflow Connector** | DAG execution history → pipeline intelligence. Scheduling patterns. | 1w | P2 |

### J.3 Intelligence Map Data Sources

| Map element | Source | Implementation |
|---|---|---|
| Node brightness | DiagonalKernel per-source weights | DK weights from CompoundingScorer fingerprint |
| Node size | Data volume (row count, table size) | From Snowflake/Databricks metadata |
| Line thickness | Correlation strength from cross-graph | Cross-graph attention scores |
| Line color | Value: green=positive, red=contradictory | From combination discovery engine |
| Gold dotted lines | Suggested new connections | Combination discovery + valuation model |
| Pulsing | Real-time centroid updates | WebSocket feed from learn() events |
| IKS per cluster | Per-domain IKS breakdown | IKSService with domain grouping |

---

## §39 — MAP Queue Items (for MAP v5.111+)

These items should be added to the Master Action Plan. Format
follows MAP v5.110 conventions. IDs use DI- prefix. Tier
placement is relative to existing MAP priorities.

### Placement Recommendation

DataOps Level 5-6 items begin AFTER current DataOps Loom demo
is recorded (the Continental Tire story uses built Level 1-3
features). Phase A (Source Profiler + Intelligence Map v1) can
run parallel with S2P Tier 3 and Purchasing Phase 1 since it
touches a different domain. Phase B-C follow sequentially.

### Existing DataOps Items (from v1.5, for reference)

| # | ID | What | Effort | Status |
|---|---|---|---|---|
| — | D-CEL | SAP + Celonis real connectors + frontend (v1.5 §22) | 1.5d | QUEUED |
| — | SC-9→SC-16 | Self-computation capabilities | ~11d | PARTIALLY SHIPPED |
| — | OE-1→OE-5 | Operational evolution | — | ✅ SHIPPED |
| — | STORY-PW | Playwright verification spec | 0.5d | QUEUED |

### DI Phase A: Data Intelligence Foundation (~4 weeks)
**Placement: MAP Tier 4.5 (after Loom recorded, parallel with S2P Tier 3)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| DI-1 | **SOURCE-PROFILER** | Per-source, per-column reliability profiles from DK weights. SourceProfile + ColumnProfile + ConsumerProfile dataclasses (§40.1). 6 new API endpoints. Every data asset gets a trust card. Trust API for external agents (§40.5). | 2w | SDK+DataOps | — | Ready (§40.1 spec) |
| DI-2 | **INTELLIGENCE-MAP-V1** | Force-directed graph visualization. Nodes = sources (brightness = DK trust). Lines = discovered correlations. React + D3 (§40.4 spec). WebSocket for pulsing. Day 1 → Month 12 animation. | 2w | DataOps FE | DI-1 | Ready (§40.4 spec) |

### DI Phase B: Democratization (~4 weeks)
**Placement: MAP Tier 5.5 (after Phase A, parallel with Purchasing Phase 1.1)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| DI-3 | **NL-QUERY-ENGINE** | Quality-aware NL answers. Classify → SQL → execute → enrich (source attribution + reliability + confidence + freshness + anomaly context) → respond. Confidence computation (§40.2). Claude API or local LLM for SQL generation. | 3w | SDK+DataOps | DI-1 | Ready (§40.2 spec) |
| DI-4 | **PROMPT-INTEGRATOR** | "Connect my QuickBooks to my spreadsheet." Auto-discover join keys (fuzzy match). Per-source trust weights on combined view. Quality annotations per field. Suggest improvements after 100 verified uses. | 1w | DataOps | DI-1 | Ready |

### DI Phase C: Data Strategy (~6 weeks)
**Placement: MAP Tier 6.5 (after Phase B)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| DI-5 | **COMBINATION-DISCOVERY** | Cross-graph sweeps for value-creating data combinations. Internal pairs (Pearson/Spearman, p<0.05). External candidates (residual reduction). Rank by ROI. CombinationCandidate dataclass (§40.3). | 3w | SDK+DataOps | DI-1 | Ready (§40.3 spec) |
| DI-6 | **DATA-VALUATION** | Economic value estimation per discovered combination. improvement_pp × decisions/year × avg_decision_value. Dollar amounts on Intelligence Map gold lines. | 2w | DataOps | DI-5 | Ready |
| DI-7 | **INTELLIGENCE-MAP-V2** | Add gold dotted lines (suggestions with $ labels), pulsing (real-time centroid updates via WebSocket), IKS per cluster (domain breakdown). Per-product IKS badges. | 1w | DataOps FE | DI-2+DI-5 | Ready |
| DI-8 | **ACQUISITION-ADVISOR** | "What external data should I buy?" Ranked by ROI. External data catalog (weather, commodity, industry benchmarks). Data monetization discovery: "Your learned profiles outperform D&B — licensing opportunity." | 2w | DataOps | DI-6 | Ready |

### DI Phase D: Connectors (~3 weeks)
**Placement: Parallel with Phase B-C (independent)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| DI-9 | **SNOWFLAKE-META** | Snowflake metadata connector. Table stats (row count, size), column profiles (null rate, distinct), query history (who queries what). Feeds Source Profiler node size + NL engine SQL generation. | 1w | SDK | — | Ready |
| DI-10 | **DBT-CONNECTOR** | dbt model run history + test results → intelligence graph. Model freshness, test pass rates, compilation errors. Each dbt model becomes a node in Intelligence Map. | 1w | SDK | — | Ready |
| DI-11 | **AIRFLOW-CONNECTOR** | DAG execution history → pipeline intelligence. Run durations, failure rates, scheduling patterns, task-level metrics. Each DAG becomes a node in Intelligence Map. | 1w | SDK | — | Ready |

### Scenario Coverage by Phase

| Phase | Items | Scenarios Covered | Level |
|---|---|---|---|
| Built (v1.5) | D-CEL, OE-1→5, SC-9→10 | D-M1-M5, D-I5, D-I11, D-I12, D-I13 | 1-4 |
| Phase A | DI-1, DI-2 | +D-I1 (self-aware), D-I2 (metadata trust), D-I14 (agent trust), D-I15 (product IKS) | +5 partial |
| Phase B | DI-3, DI-4 | +D-M6 (democratization), D-M7 (sticky quality), D-I9 (prompt integration), D-I10 (quality-aware NL) | +5 |
| Phase C | DI-5, DI-6, DI-7, DI-8 | +D-I3 (self-combining), D-I4 (cross-pipeline), D-I6 (per-consumer), D-I7 (acquisition), D-I8 (monetization) | +6 |

### Critical Path

```
SOURCE-PROFILER (DI-1, 2w) ─── UNBLOCKS ALL LEVEL 5-6
  │
  ├── INTELLIGENCE-MAP-V1 (DI-2, 2w) ──→ MAP-V2 (DI-7, 1w)
  │                                         ↑
  ├── NL-QUERY-ENGINE (DI-3, 3w)           │
  │                                         │
  ├── PROMPT-INTEGRATOR (DI-4, 1w)         │
  │                                         │
  └── COMBINATION-DISCOVERY (DI-5, 3w)     │
        └── DATA-VALUATION (DI-6, 2w) ─────┘
              └── ACQUISITION-ADVISOR (DI-8, 2w)

CONNECTORS (DI-9, DI-10, DI-11) ── PARALLEL, NO DEPENDENCIES
```

**Fastest path to hero demo moment:**
DI-1 (2w) → DI-2 (2w) = Intelligence Map v1 in ~4 weeks.
"Your data estate, visualized by what the system has LEARNED."

**Fastest path to Level 5 demo:**
DI-1 (2w) → DI-3 (3w) = Quality-aware NL answers in ~5 weeks.
"$4.2M (94% confidence). SAP 99% reliable. Salesforce 87%."

**Fastest path to Level 6 demo:**
DI-1 → DI-5 → DI-6 → DI-7 = Gold lines on Intelligence Map in ~9 weeks.
"Your data tells you what additional data to buy. Ranked by ROI."

### MAP v5.111 Integration Note

To integrate into MAP v5.111, add:

1. **Prerequisite:** D-CEL (1.5d) + STORY-PW (0.5d) + Loom recorded
   BEFORE any DI- items begin. The Loom uses built Level 1-3
   features. DI- items extend to Level 5-6.

2. New tier: **"Tier 4.5: DataOps Data Intelligence Phase A"**
   (DI-1, DI-2) between existing Tier 4 and Tier 5.
   Runs parallel with S2P Tier 3 (different domain).

3. New tier: **"Tier 5.5: DataOps Democratization Phase B"**
   (DI-3, DI-4) between existing Tier 5 and Tier 6.
   Runs parallel with Purchasing Phase 1.1.

4. New tier: **"Tier 6.5: DataOps Data Strategy Phase C"**
   (DI-5, DI-6, DI-7, DI-8) after Tier 6.

5. Merge DI-9, DI-10, DI-11 into existing Tier 6 (cross-platform)
   as parallel connector work.

6. Update §2 platform state: add DataOps test count progression.

7. Update §6 scenario coverage: add DataOps Level 5-6 rows.

8. Add Intelligence Map to demo lineup:
   - After Loom: "DataOps hero demo (Continental Tire) — Level 1-3"
   - After Phase A: "Intelligence Map demo — Level 5 preview"
   - After Phase C: "Full Data Intelligence demo — Level 6"

**Total new items: 11.** Combined with existing DataOps items
(D-CEL, SC-9→SC-16, STORY-PW), total DataOps forward queue: ~20 items.

**First action after Loom: DI-1 (SOURCE-PROFILER). 2 weeks.
Unblocks all Level 5-6 features.**

### Cross-Copilot Dependencies

| DI Item | Benefits other copilots? | How? |
|---|---|---|
| DI-1 (Source Profiler) | ALL copilots | Per-source trust is domain-agnostic. SOC gets per-SIEM trust. Purchasing gets per-QuickBooks trust. |
| DI-3 (NL Query Engine) | ALL copilots | Quality-aware NL pattern reusable. S2P gets "What's my invoice exception rate?" with confidence. |
| DI-5 (Combination Discovery) | S2P, Purchasing | Cross-graph sweeps find procurement × supplier × commodity combinations. |
| DI-14 (Agent Trust API) | PLATFORM | Universal trust layer. Every copilot's DK weights feed the trust API. External agents consume it. |

### Phasing Relative to Other Copilots

```
CURRENT (Loom demo):
  DataOps Loom → SOC fly-through → S2P preview → Purchasing preview

AFTER DI PHASE A (~4 weeks):
  DataOps: Intelligence Map v1 demo (Level 5 preview)
  Purchasing: Phase 0 complete
  Trading: Product definition complete

AFTER DI PHASE B (~8 weeks):
  DataOps: Quality-aware NL demo (Level 5 full)
  Purchasing: Phase 1 in progress
  Trading: Phase 0 complete

AFTER DI PHASE C (~14 weeks):
  DataOps: Full Data Intelligence demo (Level 6)
  → Gold lines, acquisition advisor, per-product IKS
  → Category-defining demo: "Your data gets smarter every day"
  Purchasing: Phase 1 complete
  Trading: Phase 1 in progress
```

---


---


## §39A — The Reification Gap

DataOps Level 1-3 is COMPLETE (OE-1→OE-5, SC-9/SC-10, 261 backend tests).
The CompoundingScorer computes per-factor DK weights, conservation tracks
per-source reliability, AgentEvolver discovers operational rules, and the
graph stores every verified decision with source attribution.

None of this is SURFACED as "data intelligence." The machinery exists.
The presentation doesn't. This addendum defines 6 immediate items (SC-TRUST
through SC-DIGEST) that reify what's already computed, plus execution-ready
MAP addendums for DI-1 and DI-2.

**Principle:** No new math. No new scoring. No new graph schema. These items
wrap EXISTING scorer methods (`get_dk_weights`, `compute_fingerprint`,
`_compute_iks`, `_category_coverage`, evolution ledger reads) in endpoints
and UI components that make the intelligence VISIBLE.

---

## §39B — Immediate Items (use existing machinery)

### SC-TRUST: Source Trust Card (Dashboard tab)

**MAP ID:** SC-TRUST
**Tier:** 5.1 (immediate, before DI-1)
**Effort:** 1-2d
**Repo:** copilot-sdk (apps/dataops)
**Depends on:** Nothing — uses existing `get_dk_weights()` + `compute_fingerprint()`
**Tab:** Dashboard (add as top card)

**What:** One card showing per-source trust scores derived from DK weights.
Each pipeline system gets a trust score (0-1), status badge (GREEN/AMBER/RED),
verified count, and trend arrow. Click → drill into per-factor contribution.

**Why it matters:** Changes the narrative from "we monitor pipelines" to
"we measure which data you can trust." The Level 5 elevator pitch in one card.

**Endpoint:**
```
GET /api/dataops/intelligence/source-trust
Returns: [
  {source: "sap_mm_api", trust: 0.89, status: "GREEN", verified: 142, trend: "improving"},
  {source: "erp_connector", trust: 0.71, status: "AMBER", verified: 67, trend: "stable"},
  {source: "sftp_daily", trust: 0.43, status: "RED", verified: 23, trend: "declining"},
]
```

**Implementation:**
```
Backend:
  apps/dataops/backend/app/routers/intelligence_router.py (NEW)
    - compute_source_trust(scorer, domain) → list[SourceTrust]
    - Maps DK weight matrix to per-source trust via FACTOR_TO_SOURCE mapping:
        impact_scope → cross-system (all sources)
        source_reliability → the source itself
        recurrence_frequency → monitoring system
        downstream_urgency → consumer systems
        data_freshness → ingestion pipeline
        business_criticality → business context
    - Trust = weighted average of DK weights for factors associated with source
    - Status: trust ≥ 0.7 → GREEN, ≥ 0.4 → AMBER, else RED
    - Trend: compare current DK weights vs 50-decisions-ago checkpoint

Frontend:
  apps/dataops/frontend/src/components/SourceTrustCard.tsx (NEW)
    - Table: source name, trust bar, status badge, verified count, trend arrow
    - Click row → expand per-factor DK weight breakdown
    - Provenance label: "Trust scores from N verified decisions" (T-R)

Tests (~8):
  test_source_trust_endpoint_returns_all_sources
  test_trust_score_range_0_to_1
  test_status_thresholds (GREEN ≥ 0.7, AMBER ≥ 0.4)
  test_trend_computation_from_checkpoints
  test_factor_to_source_mapping_covers_all_factors
  test_empty_decisions_returns_neutral_trust
  test_provenance_label_present
  test_frontend_typecheck (npx tsc --noEmit)
```

---

### SC-IKS-ATTR: IKS Attribution (Insight tab)

**MAP ID:** SC-IKS-ATTR
**Tier:** 5.1
**Effort:** 2-3d
**Repo:** copilot-sdk (apps/dataops)
**Depends on:** Nothing — uses evolution ledger + centroid checkpoints + fingerprint history
**Tab:** Insight (add as panel below BottleneckPanel)

**What:** Causal attribution for IKS changes. "IKS went from 55 → 72. Why?"
Connects evolution events, schema changes, category coverage shifts, and
fingerprint stability changes to IKS deltas.

**Endpoint:**
```
GET /api/dataops/intelligence/iks-attribution?window=30
Returns: {
  current_iks: 72.1,
  period_start_iks: 55.3,
  attributions: [
    {period: "Week 3-4", iks_delta: +8.2,
     cause: "Rule promoted: pre-join filter for schema_change",
     evidence_type: "evolution_event", evidence_id: "EVT-042"},
    {period: "Week 5", iks_delta: +3.1,
     cause: "Schema change resolved (MATKL_V2 stabilized)",
     evidence_type: "schema_impact", evidence_id: "SI-017"},
    {period: "Week 6", iks_delta: -1.4,
     cause: "New category introduced (transform_drift)",
     evidence_type: "coverage_change", detail: "coverage 0.83 → 0.67"},
    {period: "Week 7-8", iks_delta: +6.9,
     cause: "source_reliability factor stabilized (σ 0.31 → 0.14)",
     evidence_type: "fingerprint_change"}
  ],
  unattributed_delta: 0.0
}
```

**Implementation:**
```
Backend:
  apps/dataops/backend/app/services/iks_attribution.py (NEW)
    - IKSAttribution dataclass (period, iks_delta, cause, evidence_type, evidence_id)
    - compute_iks_attribution(graph_store, scorer, domain, window_days) → list[IKSAttribution]
    - Algorithm:
      1. Get centroid checkpoints with IKS values over window
      2. Segment into periods where IKS changed significantly (|delta| > 1.0)
      3. For each period, check:
         a. Evolution events (rule promoted/rejected/rollback)
         b. Schema impact events (from OE-3 data)
         c. Category coverage changes (new categories activated)
         d. Fingerprint σ changes (factor stability shifts)
      4. Attribute each IKS delta to the strongest correlated event
      5. Any remaining delta → "organic learning" (more verified decisions)

Frontend:
  apps/dataops/frontend/src/components/IKSAttributionPanel.tsx (NEW)
    - Timeline visualization: vertical bar for each period
    - Color = positive (green) / negative (red) delta
    - Hover → cause + evidence link
    - Click → navigate to Evidence tab with evidence_id highlighted

Tests (~10):
  test_attribution_covers_full_delta (sum of deltas ≈ total IKS change)
  test_evolution_event_attributed (rule promotion → IKS increase)
  test_coverage_change_attributed (new category → IKS decrease)
  test_fingerprint_change_attributed (σ drop → IKS increase)
  test_empty_window_returns_empty
  test_unattributed_delta_bounded (≤ 20% of total)
```

---

### SC-FORECAST: Learning Forecast (Curve tab)

**MAP ID:** SC-FORECAST
**Tier:** 5.1
**Effort:** 1-2d
**Repo:** copilot-sdk (apps/dataops)
**Depends on:** Nothing — uses trajectory + conservation + verified rate
**Tab:** Curve (add below ConservationProjection)

**What:** Predicts WHEN the next milestone will be reached. "At current
learning rate, GREEN in 3 weeks. Verify 10 transform_drift decisions
to reach GREEN 2 weeks earlier."

**Endpoint:**
```
GET /api/dataops/intelligence/learning-forecast
Returns: {
  current_iks: 64.2,
  current_status: "AMBER",
  green_threshold: {iks: 72.0, verified_needed: 50, accuracy_needed: 0.68},
  forecast: {
    weeks_to_green: 3.2,
    bottleneck_category: "transform_drift",
    bottleneck_reason: "Only 8 verified decisions (need 20+ for stable σ)",
    acceleration_tip: "Verify 10 transform_drift decisions → GREEN ~1 week earlier"
  },
  learning_rate: {
    decisions_per_week: 15.4,
    accuracy_trend: "improving (+2pp/week)",
    coverage_trend: "stable (5/6 categories)"
  }
}
```

**Implementation:**
```
Backend:
  apps/dataops/backend/app/services/learning_forecast.py (NEW)
    - LearningForecast dataclass
    - compute_learning_forecast(scorer, graph_store, domain) → LearningForecast
    - Algorithm:
      1. Current IKS + conservation status
      2. Verified decision rate (decisions/week from last 30 days)
      3. Accuracy trend (rolling 50-decision window slope)
      4. Category with lowest coverage → bottleneck
      5. Linear projection: weeks_to_green = (green_iks - current_iks) / iks_per_week
      6. Bottleneck analysis: which category, if verified, accelerates most?

Frontend:
  apps/dataops/frontend/src/components/LearningForecastCard.tsx (NEW)
    - Current status badge + IKS number
    - "Estimated GREEN in: 3.2 weeks" with progress bar
    - Bottleneck callout with verification recommendation
    - Trend sparklines (decisions/week, accuracy, coverage)

Tests (~6):
  test_forecast_weeks_positive
  test_bottleneck_is_lowest_coverage_category
  test_acceleration_tip_references_bottleneck
  test_already_green_returns_zero_weeks
  test_no_decisions_returns_unknown
  test_trend_computation_from_recent_window
```

---

### SC-DIGEST: Daily Learning Digest (Dashboard tab)

**MAP ID:** SC-DIGEST
**Tier:** 5.1
**Effort:** 2d
**Repo:** copilot-sdk (apps/dataops)
**Depends on:** Nothing — uses fingerprint + evolution + conservation
**Tab:** Dashboard (add below SourceTrustCard)

**What:** "What did the system learn today?" Data-focused, not executive.
Shows verified decisions, factor changes, source promotions, rules promoted.

**Endpoint:**
```
GET /api/dataops/intelligence/digest?period=today
Returns: {
  period: "2026-07-31",
  decisions_verified: 4,
  factor_changes: [
    {name: "source_reliability", sigma_before: 0.31, sigma_after: 0.22,
     interpretation: "stabilizing"}
  ],
  source_status_changes: [
    {source: "sap_mm_api", from: "AMBER", to: "GREEN", cause: "15 consecutive correct"}
  ],
  rules_promoted: [
    {name: "auto-escalate quality_anomaly from erp_connector",
     accuracy: 0.73, shadow_decisions: 15}
  ],
  rules_rejected: [],
  iks_delta: +2.1,
  highlight: "source_reliability factor stabilized — sap_mm_api moved to GREEN"
}
```

**Implementation:**
```
Backend:
  apps/dataops/backend/app/services/learning_digest.py (NEW)
    - LearningDigest dataclass
    - compute_digest(scorer, graph_store, domain, period) → LearningDigest
    - Algorithm:
      1. Count decisions verified in period (from graph_store)
      2. Compare fingerprint now vs fingerprint at period start (σ deltas)
      3. Check evolution events in period (promoted/rejected rules)
      4. Compute source trust changes (from SC-TRUST data)
      5. Compute IKS delta over period
      6. Generate one-line highlight (most significant change)

Frontend:
  apps/dataops/frontend/src/components/LearningDigestCard.tsx (NEW)
    - Compact card with period selector (today / this week / this month)
    - Key metrics: decisions verified, IKS delta, rules promoted
    - Expandable sections for factor changes, source changes, rules
    - Highlight banner at top

Tests (~8):
  test_digest_covers_requested_period
  test_factor_changes_have_before_after
  test_source_changes_reference_trust_status
  test_rules_promoted_have_accuracy
  test_highlight_picks_most_significant
  test_empty_period_returns_zeros
  test_iks_delta_computed_correctly
  test_period_options (today, week, month)
```

---

## §39C — Foundation Items (gate Level 5-6)

### DI-1: Source Profiler (full spec)

**MAP ID:** DI-1 (SOURCE-PROFILER)
**Tier:** 4.5 (after Loom, parallel with S2P Tier 3)
**Effort:** 2w
**Repo:** copilot-sdk (SDK module + DataOps app)
**Depends on:** SC-TRUST (validates the factor→source mapping)

Full spec in PD v1.6 §40.1. Key addition from this addendum:

The Source Profiler is NOT new computation. It's a structured
extraction of what `get_dk_weights()`, `compute_fingerprint()`,
and `_category_coverage()` already compute. The Codex prompt
MUST reference these existing methods, not reinvent.

```
Prompt: P-DI1-SOURCE-PROFILER
  Repo: copilot-sdk
  Create:
    copilot_sdk/intelligence/__init__.py
    copilot_sdk/intelligence/source_profiler.py
      SourceProfile, ColumnProfile, ConsumerProfile dataclasses (§40.1)
      compute_source_profiles(graph_store, scorer, domain) → list[SourceProfile]
      Uses: scorer.get_dk_weights(), scorer.fingerprint(), graph_store.count_verified()
    copilot_sdk/intelligence/trust_api.py
      TrustQuery, TrustResponse for external agent consumption
  Modify:
    apps/dataops/backend/app/routers/intelligence_router.py (extend)
      6 new endpoints (§40.1)
  Create:
    apps/dataops/frontend/src/screens/IntelligenceScreen.tsx (NEW tab or extend Insight)
    apps/dataops/frontend/src/components/SourceProfileCard.tsx
    apps/dataops/frontend/src/components/ColumnProfileTable.tsx
  Tests: ~25 (backend) + ~8 (E2E)
  NON-NEGOTIABLES:
    - SourceProfile.trust_score is DK-derived, not hardcoded
    - ProvenanceBadge on all trust scores (T-R from verified decisions)
    - External trust API returns provenance tier with every score
    - No new scorer methods — use existing get_dk_weights() + fingerprint()
```

### DI-2: Intelligence Map v1

**MAP ID:** DI-2 (INTELLIGENCE-MAP-V1)
**Tier:** 4.5 (after DI-1)
**Effort:** 2w
**Repo:** copilot-sdk (DataOps frontend)
**Depends on:** DI-1

Full spec in PD v1.6 §40.4. Key addition:

```
Prompt: P-DI2-INTELLIGENCE-MAP
  Repo: copilot-sdk
  Create:
    apps/dataops/frontend/src/components/IntelligenceMap.tsx
      D3 force simulation (d3 is available in the React stack)
      Nodes: circle, radius = log(volume), opacity = trust_score
      Edges: line, strokeWidth = |correlation|
      Animation: Day 1 → Month 12 (d3.transition, 5s interpolation)
    apps/dataops/backend/app/routers/intelligence_router.py (extend)
      GET /api/dataops/intelligence/map → graph data for viz
      WS  /api/dataops/ws/learning-events → centroid update stream
  Tests: ~5 (E2E) + visual verification
  NON-NEGOTIABLES:
    - Node brightness = DK trust weight (from DI-1 SourceProfile)
    - Animation must work without WebSocket (static mode for demo)
    - No hardcoded node positions — force simulation computes layout
```

---

## §39D — MAP Addendum (paste into MAP v5.224+)

### New Tier: 5.1 — DataOps Self-Computation Reification

| # | ID | What | Effort | Dep | Status |
|---|---|---|---|---|---|
| — | **SC-TRUST** | Source Trust Card on Dashboard. DK weights → per-source trust. | 1-2d | — | READY |
| — | **SC-IKS-ATTR** | IKS Attribution. "WHY did accuracy improve?" | 2-3d | — | READY |
| — | **SC-FORECAST** | Learning Forecast. "WHEN will we reach GREEN?" | 1-2d | — | READY |
| — | **SC-DIGEST** | Daily Learning Digest. "What did the system learn today?" | 2d | SC-TRUST | READY |

**Total: ~8-9d. All use existing scorer methods. No new math.**

### Updated Tier 4.5: DataOps Intelligence Foundation

| # | ID | What | Effort | Dep | Status |
|---|---|---|---|---|---|
| — | **DI-1** | Source Profiler. Per-source, per-column trust from DK weights. 6 endpoints. Trust API. | 2w | SC-TRUST | READY (§40.1) |
| — | **DI-2** | Intelligence Map v1. D3 force-directed graph. Day 1 → Month 12. | 2w | DI-1 | READY (§40.4) |

### Execution Order

```
IMMEDIATE (Tier 5.1, ~9d):
  SC-TRUST (1-2d) ── unblocks SC-DIGEST + validates factor→source mapping
       │
       ├── SC-DIGEST (2d)
       │
  SC-IKS-ATTR (2-3d) ── independent
  SC-FORECAST (1-2d) ── independent

AFTER LOOM (Tier 4.5, ~4w):
  DI-1 (2w) ── unblocks ALL Level 5-6
       │
       └── DI-2 (2w) ── THE hero visual

LATER (Tier 5.5-6.5, ~9w):
  DI-3 → DI-4 → DI-5 → DI-6 → DI-7 → DI-8
  (unchanged from PD v1.6 §39)
```

### Cross-Reference to PD v1.6

| Addendum item | PD section | Relationship |
|---|---|---|
| SC-TRUST | §40.1 (Source Profiler) | **Prerequisite** — validates the factor→source mapping before DI-1 builds the full profiler |
| SC-IKS-ATTR | §29 (Self-Computation) | **Extension** — adds causal attribution to existing SC panels |
| SC-FORECAST | §29 (Self-Computation) | **Extension** — adds predictive layer to conservation projection |
| SC-DIGEST | §29 (Self-Computation) | **Extension** — adds temporal digest to existing dashboard |
| DI-1 | §40.1 | **Same item** — prompt now references existing scorer methods |
| DI-2 | §40.4 | **Same item** — unchanged |

---

## §39E — Codex Prompt: SC-TRUST (paste-ready)

```text
/model gpt-5.3
Echo the current model name in the first line of output.
TASK: SC-TRUST — Source Trust Card for DataOps Dashboard.
WORKING DIRECTORY:
C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk

RULES: Do NOT use git.

ACTIVATE:
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"

CONTEXT:
DataOps CompoundingScorer computes DK weights (per-category × per-factor importance).
These weights implicitly encode which data sources are reliable — a high-weight factor
means its source is discriminating well. This endpoint surfaces those weights as
per-source trust scores.

STEP 1 — Discovery:
  python -c "
import os
# Check existing intelligence router
for root, dirs, files in os.walk('apps/dataops/backend/app/routers'):
    for f in files:
        if f.endswith('.py') and 'intelligence' in f.lower():
            path = os.path.join(root, f)
            print(f'{path} ({sum(1 for _ in open(path))} lines)')

# Check DK weights availability
for root, dirs, files in os.walk('apps/dataops/backend/app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            src = open(path).read()
            if 'dk_weights' in src or 'get_dk_weights' in src:
                for i, line in enumerate(src.splitlines(), 1):
                    if 'dk_weights' in line or 'get_dk_weights' in line:
                        print(f'{path}:{i}: {line.strip()}')
"

  python -c "
# Verify scorer has get_dk_weights
from copilot_sdk.scoring.scorer import CompoundingScorer
print('get_dk_weights' in dir(CompoundingScorer))
print('fingerprint' in dir(CompoundingScorer))
"

STEP 2 — Implementation:

ALLOWED FILES — CREATE:
  apps/dataops/backend/app/routers/intelligence_router.py (if not exists)
  apps/dataops/backend/app/services/source_trust.py
  apps/dataops/backend/tests/test_source_trust.py
  apps/dataops/frontend/src/components/SourceTrustCard.tsx

ALLOWED FILES — MODIFY:
  apps/dataops/backend/app/main.py (mount intelligence router)
  apps/dataops/frontend/src/screens/DashboardScreen.tsx (add SourceTrustCard)
  apps/dataops/frontend/src/api.ts (add fetchSourceTrust)

FORBIDDEN:
  copilot_sdk/scoring/scorer.py — do NOT modify the scorer
  copilot_sdk/graph/ — do NOT modify GraphStore

FILE 1: apps/dataops/backend/app/services/source_trust.py

  FACTOR_TO_SOURCE = {
      "impact_scope": "cross_system",
      "source_reliability": "source_direct",
      "recurrence_frequency": "monitoring",
      "downstream_urgency": "consumer_systems",
      "data_freshness": "ingestion_pipeline",
      "business_criticality": "business_context",
  }

  PIPELINE_SYSTEMS = [
      "sap_mm_api", "erp_connector", "sftp_daily", "salesforce_api",
      "warehouse_etl", "data_lake_ingestion", "api_gateway",
      "batch_processor", "streaming_pipeline"
  ]

  @dataclass
  class SourceTrust:
      source: str
      trust: float           # 0.0 to 1.0, from DK weights
      status: str            # GREEN (≥0.7), AMBER (≥0.4), RED (<0.4)
      verified: int          # decisions involving this source
      trend: str             # "improving", "stable", "declining"
      dk_contribution: dict  # per-factor DK weight for this source

  def compute_source_trust(scorer, graph_store, domain) -> list[SourceTrust]:
      dk_weights = scorer.get_dk_weights()
      fingerprint = scorer.fingerprint(persist=False)
      # ... map DK weights to per-source trust via FACTOR_TO_SOURCE
      # ... compute trend from fingerprint history
      # ... return sorted by trust descending

FILE 2: intelligence_router.py endpoint

  @router.get("/intelligence/source-trust")
  def source_trust() -> list[dict]:
      # ... use _scorer_provider() to get CompoundingScorer
      # ... call compute_source_trust(scorer, graph_store, "dataops")
      # ... return with provenance label

FILE 3: SourceTrustCard.tsx

  - Table rows: source name, trust bar (width = trust%), status badge, trend arrow
  - Click row → expand per-factor breakdown
  - Footer: "Trust scores from N verified decisions" (provenance)

TESTS (~8):
  test_source_trust_returns_all_systems
  test_trust_range_0_to_1
  test_status_green_above_07
  test_status_amber_above_04
  test_status_red_below_04
  test_trend_from_fingerprint_history
  test_dk_contribution_per_source
  test_empty_decisions_returns_neutral

SUBSTANTIATION DECLARATION (Rule 66):
  Surfaced values: per-source trust scores (T-R from DK weights on verified decisions ██)
  Generated data: none
  Labeling: trust scores from verified decisions = real-pending(██)
  Magnitude guard: trust 0.89 is from DK weights on 142 verified decisions (T-R)

VALIDATION:
  python -m pytest apps/dataops/backend/tests/test_source_trust.py -v --timeout=60
  python -m pytest apps/dataops/backend/tests/ -q --timeout=120
  cd apps/dataops/frontend; npx tsc --noEmit; cd ../../..

EXIT: Source Trust Card renders on Dashboard. Trust scores derived from DK weights.
```

---

*DataOps Copilot Design v1.7 Addendum A · July 31, 2026*
*4 immediate items (SC-TRUST, SC-IKS-ATTR, SC-FORECAST, SC-DIGEST) — ~9d total.*
*All use existing scorer methods. No new math. No new graph schema.*
*SC-TRUST (1-2d) is the fastest path: one card changes the narrative.*
*DI-1 + DI-2 follow after Loom (~4w). Full Level 5-6 follows (~9w more).*

---

## §40 — Engineering Specifications (Level 5-6)

### L.1 Source Profiler (DI-1)

The foundation for all Level 5-6 features. Converts raw
DiagonalKernel weights into human/agent-readable trust profiles.

```python
@dataclass
class SourceProfile:
    """Per-source intelligence profile learned from verified outcomes."""
    source_id: str            # "sap_s4hana", "salesforce_crm", etc.
    source_name: str
    overall_trust: float      # 0-1, weighted avg of column trusts
    conservation_status: str  # GREEN/AMBER/RED
    verified_decisions: int   # how many verified uses
    iks: float                # IKS for this source (0-100)
    
    columns: list[ColumnProfile]
    consumption_patterns: list[ConsumerProfile]
    
@dataclass
class ColumnProfile:
    column_name: str
    dk_weight: float          # from DiagonalKernel (0-1)
    sigma: float              # outcome-conditioned variance
    trust_label: str          # "reliable"/"moderate"/"noisy"
    trend: str                # "stable"/"improving"/"degrading"
    seasonal_pattern: str | None  # "Q4 noisy" if detected

@dataclass
class ConsumerProfile:
    consumer_id: str          # "marketing_dashboard", "ml_pipeline"
    quality_bar: dict         # {"freshness": "< 1hr", "completeness": "> 95%"}
    satisfaction_rate: float  # from verified outcomes per consumer
    last_issue: str | None
```

**API endpoints:**

| Endpoint | Method | Purpose |
|---|---|---|
| /api/dataops/sources | GET | All source profiles |
| /api/dataops/sources/{id} | GET | Single source with column profiles |
| /api/dataops/sources/{id}/consumers | GET | Per-consumer quality bars |
| /api/dataops/sources/{id}/trust | GET | Trust score for agent consumption |
| /api/dataops/products | GET | Data products with per-product IKS |
| /api/dataops/products/{id} | GET | Single product intelligence profile |

**How DK weights become source profiles:**

```python
def compute_source_profile(
    source_id: str,
    fingerprint: dict,
    decisions: list[dict],
    factor_to_source_map: dict
) -> SourceProfile:
    """
    Maps DiagonalKernel per-factor weights to per-source trust.
    
    The factor_to_source_map tells us which factors come from
    which source: {"source_reliability": "sap_s4hana",
    "data_freshness": "airflow_metadata", ...}
    
    Per-column profiles come from factor decomposition:
    each factor computer uses specific columns. The factor's
    DK weight propagates to its input columns.
    """
    ...
```

### L.2 NL Query Engine (DI-3)

Quality-aware natural language answers. The differentiator vs
Databricks Genie / Numbers Station: every answer includes
confidence, source attribution, and reliability weights.

**Architecture:**

```
User question (NL)
  → Query classifier (intent: metric / exploration / comparison)
  → SQL generator (Claude API or local LLM)
  → Query executor (Snowflake / Databricks / PostgreSQL)
  → Result enrichment:
      ├── Source attribution: which tables contributed
      ├── Reliability weighting: DK weights per source
      ├── Confidence computation: weighted reliability
      ├── Freshness check: data age per source
      ├── Anomaly context: any active alerts on these sources?
      └── Comparison context: same query last period + delta
  → Quality-aware response (NL + confidence + attribution)
```

**Confidence computation:**

```python
def compute_answer_confidence(
    sources_used: list[str],
    source_profiles: dict[str, SourceProfile],
    query_type: str
) -> float:
    """
    Weighted average of source trust scores.
    Each source's contribution weighted by its data volume
    fraction in the answer.
    
    For "what was revenue?":
      SAP contributes 60% of answer (trust 0.99) → 0.594
      Salesforce contributes 40% (trust 0.87) → 0.348
      Weighted confidence: 94.2%
    
    Adjustments:
      -5% if any source has active AMBER alert
      -10% if any source has freshness > 24 hours
      Flag if sources disagree > 5%
    """
    ...
```

**Response template:**

```python
QUALITY_AWARE_ANSWER = (
    "{answer_value} (confidence {confidence:.0%}). "
    "{source_attribution}. "  # "SAP: 99% reliable. Salesforce: 87%."
    "{freshness_note}. "      # "Data as of 2 hours ago."
    "{anomaly_note}. "        # "3 unmatched invoices pending."
    "{comparison_note}."      # "$180K below last quarter — APAC supplier change."
)
```

### L.3 Combination Discovery Engine (DI-5)

Automatically discovers value-creating data combinations.

**Algorithm:**

```python
def discover_combinations(
    source_profiles: list[SourceProfile],
    decision_history: list[dict],
    external_catalog: list[ExternalSource]
) -> list[CombinationCandidate]:
    """
    Phase 1: Internal combinations.
    For each pair of sources (A, B) with > 100 verified decisions:
      - Compute Pearson/Spearman correlation between factors
        derived from A and outcomes involving B
      - If |r| > 0.3 and p < 0.05: candidate combination
      - Estimate value: improvement_pp × decisions/year × avg_decision_value
    
    Phase 2: External combinations.
    For each external source in catalog:
      - Test correlation with existing factor residuals
      - "Does weather explain the variance in demand_prediction
        that our current factors can't?"
      - If residual_reduction > 10%: candidate
      - Estimate value: residual_reduction × current_error_cost
    
    Phase 3: Rank by ROI.
      - ROI = estimated_value / acquisition_cost
      - Free sources (weather, FRED) get ROI = infinity
    
    Returns ranked list with: source pair, correlation, p-value,
    estimated improvement, estimated annual value, acquisition cost, ROI.
    """
    ...
```

**Gold line data for Intelligence Map:**

```python
@dataclass
class CombinationCandidate:
    source_a: str
    source_b: str         # or external source name
    correlation: float
    p_value: float
    improvement_pp: float
    annual_value: float
    acquisition_cost: float  # 0 for free APIs
    roi: float
    description: str      # "Orders × weather → demand +15pp"
    status: str           # "discovered" / "validated" / "active"
```

### L.4 Intelligence Map Component (DI-2 + DI-7)

React + D3 force-directed graph. The hero visualization.

**Data flow:**

```
Source Profiler (DI-1) ──→ Node brightness + size
Cross-graph (built) ──→ Line connections + thickness
Combination Discovery (DI-5) ──→ Gold dotted lines + $ labels
CompoundingScorer.learn() ──→ WebSocket ──→ Pulse animation
IKSService ──→ Per-cluster IKS labels
```

**React component:**

```typescript
interface IntelligenceMapProps {
  sources: SourceProfile[];         // nodes
  correlations: Correlation[];      // solid lines
  suggestions: CombinationCandidate[];  // gold dotted lines
  learningEvents: LearningEvent[];  // pulsing
  iksByDomain: Record<string, number>;  // cluster labels
}

// D3 force simulation
// Node: circle, radius = log(row_count), opacity = dk_trust
// Edge: line, strokeWidth = |correlation|, color = value
// Gold dotted: dashed line, label = "$180K/yr"
// Pulse: CSS animation triggered by WebSocket message
// Cluster: convex hull with IKS badge

// Animation: Day1 → Month12 transition
// Use d3.transition() with 5-second interpolation
// Nodes fade in, lines appear sequentially, gold lines last
```

**WebSocket for real-time pulsing:**

```python
# In context_router.py
@router.websocket("/ws/learning-events")
async def learning_events(websocket: WebSocket):
    """
    Stream centroid update events for Intelligence Map pulsing.
    Each learn() call emits: {source_id, category, delta_norm}
    """
    await websocket.accept()
    while True:
        event = await learning_event_queue.get()
        await websocket.send_json(event)
```

### L.5 Trust API for External Agents (DI-1 extension)

REST API that any agent (Databricks, LangChain, custom) can
call to get trust scores before consuming data.

```
GET /api/dataops/trust/{source_id}
→ {
    "source": "sap_s4hana",
    "overall_trust": 0.94,
    "conservation_status": "GREEN",
    "verified_loads": 340,
    "safe_for_autonomous_use": true,
    "column_trust": {
      "customer_id": 0.99,
      "order_amount": 0.94,
      "satisfaction_score": 0.14
    },
    "conditions": "Safe for trending and reporting. NOT safe for
      financial close (3 unmatched invoices pending).",
    "last_verified": "2026-05-20T14:32:00Z"
  }

GET /api/dataops/trust/batch
POST body: {"sources": ["sap_s4hana", "salesforce_crm", "sheet_uploads"]}
→ Array of trust profiles (for agents querying multiple sources)
```

**Integration pattern for Databricks agents:**

```python
# In a Databricks notebook or agent
import requests

trust = requests.get(
    "https://ci-platform/api/dataops/trust/sap_s4hana"
).json()

if trust["safe_for_autonomous_use"]:
    # proceed with autonomous query
    df = spark.read.table("sap_orders")
else:
    # flag for human review
    raise AgentPauseException(
        f"Source {trust['source']} is {trust['conservation_status']}. "
        f"Trust: {trust['overall_trust']:.0%}. Require human review."
    )
```

---

## §41 — What This Changes About the Demo

### Current Demo (v1.5 Storyboard, Continental Tire)

Strong. 5 acts. Quantified. $1.62M trajectory. Process-Tech
Fusion. This doesn't change. It's the technical proof.

### NEW Demo Layer (Data Intelligence, for CDO/CFO audience)

**Before the Continental Tire story:** 60 seconds showing the
Data Intelligence Map.

"This is your data estate today [Day 1: scattered gray dots].
This is your data estate after 12 months with our platform
[Month 12: rich, bright, pulsing network with gold opportunity
lines totaling $1.2M]. Your data went from silent to intelligent.
Now let me show you HOW..."

[Continental Tire story follows — but now it's EVIDENCE for the
Intelligence Map, not the headline. The headline is: your data
gets smarter every day.]

**After the Continental Tire story:** 60 seconds on Level 6.

"That was Level 3 — self-correction. Let me show you Level 6.
[Gold dotted line appears] Your procurement data combined with
weather API predicts supply disruption 3 weeks earlier than your
current system. Free data. $200K/year value. Nobody asked for
this. The graph found it. THAT is data intelligence."

### The Positioning Sequence

1. **Hook:** Intelligence Map (Day 1 → Month 12). "Your data
   gets smarter every day."
2. **Proof:** Continental Tire (WHERE → WHY → WHAT → PROVE →
   TRANSFER). "$1.62M from one platform."
3. **Vision:** Level 6 data strategy. "Your data tells you what
   additional data to buy. Ranked by ROI."
4. **Close:** "Databricks stores data. Celonis shows processes.
   Monte Carlo monitors quality. We make data INTELLIGENT."

---

*DataOps Copilot Design v1.7 · May 20, 2026*
*Category: Data Intelligence (not "better DataOps").*
*Shift: from data-as-infrastructure to data-as-intelligence.*
*6-level hierarchy: Level 1-2 (everyone) → Level 6 (us only).*
*5 buyer personas. 7 market scenarios. 15 innovation scenarios.*
*6 category-defining capabilities: self-aware, self-combining,*
*self-correcting, self-governing, self-valuating, agent-ready.*
*The Data Intelligence Map: the mind-blowing visual.*
*Engineering specs: Source Profiler, NL Query Engine, Combination*
*Discovery, Intelligence Map, Trust API for external agents.*
*11 MAP items (DI-1 through DI-11) for Level 5-6.*
*"Your data gets smarter every day."*
