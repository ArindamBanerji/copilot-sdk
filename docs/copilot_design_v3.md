# Copilot Application Design Spec v3 (FINAL)
**Date:** May 8, 2026
**Status:** All decisions made. All prerequisites complete. Build ready.
**Rule:** Each copilot is a real application. GAE is visible, not hidden.
Every innovation demonstrated in 3+ copilots. No throwaway fixtures.

---

## §1 — The Loom: 7 Stories, 4 Applications, 8 Innovations

| Story | Application | Duration | What it proves |
|---|---|---|---|
| 1-3 | **SOC Copilot** (built) | ~8 min | Enterprise security triage. Full product. |
| 4 | **SOC Tab 6: S2P Preview** (built) | ~3 min | Same engine, different domain. Platform claim. |
| 5 | **Trading Copilot** (BUILD) | ~5 min | Personal decision scoring. Graded rewards. Engine internals. |
| 6 | **Purchasing Copilot** (BUILD) | ~5 min | Restaurant operations. AgentEvolver in purchasing. |
| 7 | **DataOps Copilot** (BUILD) | ~6 min | Pipeline triage. Conservation + AE + cross-copilot + re-convergence. |
| Close | Split screen | ~1 min | 4 fingerprints side by side. |

**Total:** ~28 minutes. 4 applications. 1 engine. 8 innovations.

### Innovation Coverage Matrix

| Innovation | SOC | S2P | Trading | Purchasing | DataOps |
|---|---|---|---|---|---|
| Compounding (IKS) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Conservation law | ✅ | ✅ | — | — | ✅ |
| Noise fingerprint (DK) | ✅ | — | ✅ | ✅ | ✅ |
| AgentEvolver | ✅ | ✅ | — | ✅ | ✅ |
| Cross-copilot transfer | ✅ source | ✅ inherits | — | — | ✅ 3-way |
| Re-convergence | — | — | — | — | ✅ |
| Graded rewards (RL) | ✅ | — | ✅ | ✅ | ✅ |
| Switching cost | ✅ | ✅ | ✅ | ✅ | ✅ |
| Engine internals | ✅ | — | ✅ | — | — |

**Every row has 3+ check marks.**

---

## §2 — Storyboard: What Happens On Screen

### Stories 1-3: SOC Copilot (BUILT — rehearse only)

| Moment | Screen | What's visible |
|---|---|---|
| 1.1 | Tab 1 | Discovery Banner: "jdoe — 3 alerts across credential_access + lateral_movement" |
| 1.2 | Tab 3 | Alert ALERT-CA-001: factor breakdown, DK weights, 62% escalate |
| 1.3 | Tab 3 | Click Confirm → centroid drifts. IKS ticks up. |
| 1.4 | Tab 7 | RL Reward panel: "severity 0.30 → η 0.019" |
| 2.1 | Tab 2 | Conservation what-if: drag to 90% → AMBER warning |
| 2.2 | Tab 7 | AgentEvolver: 11 variants, 1 rejected |
| 2.3 | Tab 7 | RL Exploration: epoch 3, margin 0.02, PAUSED |
| 2.4 | Tab 7 | Hash chain: verified, tamper-evident |
| 3.1 | Tab 1 | Discovery Banner above queue |
| 3.2 | Tab 3 | Model swap: L2 → Diagonal kernel, live comparison |

### Story 4: S2P Preview (BUILT — rehearse only)

| Moment | Screen | What's visible |
|---|---|---|
| 4.1 | Tab 6 | S2P invoice queue, Chen-Lin data, conservation GREEN |
| 4.2 | Tab 6 | Compounding curve: 62→81% trajectory |
| 4.3 | Tab 6 | Supplier Intelligence: 14 contractual / 21 actual Q4 |
| 4.4 | Tab 6 | Cross-copilot signals, warm-start evidence, chain credit |
| 4.5 | Tab 6 | Domain Applicability: 9 domains, 2 live, 3 specified, 4 designed |

**Transition:** "SOC and S2P share the same engine. But what if the
engine isn't just for enterprise security teams? What if anyone who
makes repeated decisions under uncertainty could use this?"

### Story 5: Trading Copilot (BUILD)

**The "aha":** Your conviction doesn't predict whether you'll be right.
Your research does. And the system learns MORE from your high-stakes trades.

| Moment | Screen | What's visible | Narrator |
|---|---|---|---|
| 5.1 | Journal | 40 pre-seeded trades. Win/loss icons. Research + conviction dots per trade. | "This is a trader's journal. 40 trades over 45 days." |
| 5.2 | Journal | Visual pattern: high-research ✓, high-conviction mixed | "The green checks cluster around deep research. High conviction? Random." |
| 5.3 | + Log | Trade ticket: NVDA, Buy, Research 4/5, Conviction 2/5, Long-term. Market context auto-filled. | "Let me log a new trade. I did the research on this one." |
| 5.4 | Score result | Buy 64%, Hold 22%, Sell 14%. Confirm button. | "System says buy with 64% confidence. I confirm." |
| 5.5 | Score result | IKS: 34→34.4. **Reward: +0.38. Last trade (QQQ): +0.05. "7× more."** | "Not all confirmations are equal. Higher stakes, deeper research — the system learned 7 times more." |
| 5.6 | Score result | **Centroid delta: research_depth +0.008, conviction +0.001.** | "Research moved 8× more than conviction. The centroid is physically encoding what the fingerprint discovered." |
| 5.7 | Insight | Fingerprint: research_depth 95% green, conviction 12% red. | "Research is your signal. Conviction? Noise." |
| 5.8 | Insight | Per-category: Equities 61%, Crypto 38%. | "Good at equities. Crypto? Your conviction lies to you there." |
| 5.9 | Curve | IKS 0→34 over 40 decisions. Switching cost at 67. | "A competitor needs 40 of YOUR trades to reach this point." |

### Story 6: Purchasing Copilot (BUILD)

**The "aha":** Weather doesn't affect your restaurant traffic as much as
you think. And the system WROTE ITSELF a rule about Friday produce.

| Moment | Screen | What's visible | Narrator |
|---|---|---|---|
| 6.1 | Orders | Thursday. 72°F. 20 orders. Waste sparklines per item. | "A restaurant's ordering dashboard. Every item shows its waste history." |
| 6.2 | Orders | Romaine: ⚠️ PATTERN badge. "Friday produce: 22% waste." | "The system learned this owner over-orders produce on Fridays." |
| 6.3 | Orders | **Expand → EvolutionOrigin: RULE-FRIDAY-PRODUCE. Shadow-tested 8 orders, 75% less waste. Promoted 2 weeks ago.** | "It didn't just detect the pattern. It wrote a rule. Shadow-tested on 8 orders. 75% better. Promoted. Same AgentEvolver as SOC." |
| 6.4 | Orders | Chicken wings: 4% waste, consistent. | "Proteins? 4% waste, like clockwork." |
| 6.5 | + Log | Order form: Friday, 35 lbs, demand 3/5. Weather auto-filled. | "Log tomorrow's wing order." |
| 6.6 | Score result | order_as_planned 58%. | "System says order as planned. I confirm." |
| 6.7 | Score result | IKS: 42→42.2. **Reward: +0.12. NFL Sunday stockout: +0.84. "7× more."** | "Routine order. But that NFL Sunday stockout? $2,400 lost. The system learned 7 times more from that." |
| 6.8 | Insight | historical_waste 92% green, weather 14% red, events 8% red. | "Past waste is signal. Weather? Noise. Events? Total blind spot." |
| 6.9 | Curve | IKS 42 over 20 orders. | "20 orders, IKS 42. Faster than 11 years of gut instinct." |

### Story 7: DataOps Copilot (BUILD)

**The "aha":** You trust reliable sources too much. First-time failures
from trusted systems are where you make mistakes. Same graph as SOC.
Same conservation law. Same AgentEvolver. Different domain.

| Moment | Screen | What's visible | Narrator |
|---|---|---|---|
| 7.1 | Dashboard | 9 systems. Billing 🔴, Payment ⚠️, rest ✅. | "Pipeline dashboard. 9 systems, 2 need attention." |
| 7.2 | Dashboard | Alert queue: Billing HIGH, Payment HIGH, Warehouse LOW auto-resolved. | "Recurring warehouse timeout auto-resolved — the system knows that one." |
| 7.3 | Dashboard | **Conservation slider at 40%. GREEN. Drag to 75% → AMBER.** | "Same conservation law as SOC. Same math. Different penalty — 10:1 for pipelines. Not safe yet. Pull it back." |
| 7.4 | Triage | Billing: pipeline_failure, 4 downstream, blast radius tree. | "Billing API. First-time failure. 4 downstream pipelines." |
| 7.5 | Triage | **All 6 factors AUTO-FILLED from graph.** | "All 6 factors computed from the graph. The engineer picks the action, not the factors." |
| 7.6 | Triage | 5 action buttons. | "Trusted source — you might auto-approve. But..." |
| 7.7 | Score result | pause_downstream 52%. Confirm. | "System says pause downstream. I confirm." |
| 7.8 | Score result | IKS: 28→28.6. **Reward: +0.62. Recurring warehouse: +0.08. "5× more."** | "First-time trusted-source failure. The system learned 5 times more." |
| 7.9 | Insight | recurrence 93% green, source_reliability 15% red. | "Recurrence is signal. Source reliability? Noise. 0 for 4 on first-time trusted failures." |
| 7.10 | Evidence | **3 AE variants: 2 promoted, 1 rejected (45% win rate).** | "Three variants. Two promoted. One rejected — auto-resolving ALL recurring timeouts masks config drift. Same AgentEvolver. Same safety gate." |
| 7.11 | Evidence | **PatternOrigin: SOC→S2P→DataOps chain. Warm-start 0.757.** | "SOC learned campaign escalation. S2P inherited it. DataOps inherited it. Three copilots. Same pattern. Nobody programmed the connection." |
| 7.12 | Curve | **Disruption dip: 78→61, recovery to 74 in 200 decisions (initial took 400). "2× faster."** | "SAP restructure. 6 configs changed. Recovery was twice as fast — the pre-disruption centroids were still partially valid." |
| 7.13 | Dashboard | "Same graph. Same ci-platform. Same AGEClient as SOC." | "THIS is the platform." |

### Closing

| Moment | Screen | Narrator |
|---|---|---|
| 8.1 | 4 FingerprintPanels side by side | **SOC:** threat_intel=signal, device_trust=noise. **Trading:** research=signal, conviction=noise. **Purchasing:** waste=signal, weather=noise. **DataOps:** recurrence=signal, reliability=noise. |
| 8.2 | Domain table | "9 domains. 4 built. Same engine. Same SDK. Same conservation. Same AgentEvolver. Same pattern transfer." |

---

## §3 — Architecture

### GAE Visible, Not Hidden

```
copilot-sdk/
  ├── copilot_sdk/
  │   ├── scoring/               ← CompoundingScorer (was compounding-scorer)
  │   │     score(), learn(),      wraps GAE ProfileScorer
  │   │     fingerprint(), trajectory()
  │   │     presets/               3 domains (trading, purchasing, dataops)
  │   │     verification/          price, waste, weather
  │   │
  │   ├── backend/               ← SDK routers (NEW — prompt #1)
  │   │     scoring_router         wraps copilot_sdk.scoring
  │   │     conservation_router    imports gae.calibration (DIRECT)
  │   │     evolution_router       imports gae.evolution (DIRECT)
  │   │
  │   └── frontend/              ← 8 shared React components (prompt #3)
  │
  └── apps/                      ← 3 domain copilots (prompts #4-9)
      ├── trading/
      ├── purchasing/
      └── dataops/
```

### Per-Copilot Dependencies

| Copilot | copilot_sdk.scoring | GAE Evolution | GAE Conservation | GAE Convergence | ci-platform |
|---|---|---|---|---|---|
| Trading | ✅ | — | — | — | — |
| Purchasing | ✅ | ✅ (AE rules) | — | — | — |
| DataOps | ✅ | ✅ (full panel) | ✅ (slider) | ✅ (disruption) | ✅ (graph) |
| SOC | direct GAE | ✅ | ✅ | — | ✅ |

### Repo Structure (6 repos, not 9)

```
claude_projects/
├── graph-attention-engine-v50/      ← Math. Apache 2.0. 1,237 tests.
│   ├── gae/evolution.py             ← EXTRACTED from SOC ✅
│   ├── gae/convergence.py           ← EXTENDED ✅
│   └── gae/calibration.py           ← conservation_status ADDED ✅
├── ci-platform/                     ← Graph infra. Apache 2.0. 174 tests.
│   └── scripts/seed_dataops_graph.py ← NEW (prompt #2)
├── copilot-sdk/                     ← Shared + apps. Apache 2.0.
│   ├── copilot_sdk/
│   │   ├── scoring/                 ← CompoundingScorer. 79 tests. ✅ MIGRATED
│   │   ├── backend/                 ← 3 router factories. NEW (prompt #1)
│   │   └── frontend/               ← 8 components. NEW (prompt #3)
│   ├── apps/
│   │   ├── trading/                 ← Trade journal. NEW (prompts #4-5)
│   │   ├── purchasing/              ← Order management. NEW (prompts #6-7)
│   │   └── dataops/                 ← Pipeline triage. NEW (prompts #8-9)
│   └── tests/
│       └── scoring/                 ← 79 scoring tests. ✅ MIGRATED
├── gen-ai-roi-demo-v4-v50/          ← SOC Copilot. Proprietary. 1,572+280 tests.
└── s2p-copilot/                     ← S2P backend. 141 tests.
```

### Port Allocation (all from .env)

| App | Default Port |
|---|---|
| SOC backend | 8001 |
| SOC frontend | 5173 |
| S2P backend | 8002 |
| Trading Copilot | 8010 |
| Purchasing Copilot | 8020 |
| DataOps Copilot | 8030 |
| PostgreSQL+AGE | 5433 |

### Per-Copilot Accent Colors

```css
SOC:         --copilot-primary: #2563eb (blue)
Trading:     --copilot-primary: #dc2626 (red)
Purchasing:  --copilot-primary: #059669 (green)
DataOps:     --copilot-primary: #7c3aed (purple)
```

---

## §4 — copilot-sdk Shared Layer

### Backend: 3 Router Factories

| Router | GAE import | Endpoints | Mounted by |
|---|---|---|---|
| `create_scoring_router` | `copilot_sdk.scoring` (local) | score, learn (+reward), fingerprint, trajectory, history | All |
| `create_conservation_router` | `gae.calibration` (direct) | conservation/status, conservation/what-if | DataOps |
| `create_evolution_router` | `gae.evolution` (direct) | evolution/variants, evolution/patterns | Purchasing, DataOps |

Each response includes `"engine"` field crediting the GAE component.

### Frontend: 8 Shared Components

| Component | Props | Used by |
|---|---|---|
| `FingerprintPanel` | factors[], signalLabel, noiseLabel, domainContext | All 3 |
| `TrajectoryChart` | points[], currentIks, narrative, switchingCostLine, annotations[] | All 3 |
| `ScoreResultCard` | result, actionNames, onConfirm, onOverride, rewardLine, centroidDelta | All 3 |
| `DecisionHistory` | decisions[], renderCard | All 3 |
| `CopilotShell` | name, icon, tabs[], activeTab, iks | All 3 |
| `IKSBadge` | value, delta? | All 3 |
| `EvolutionPanel` | variants[], title | Purchasing, DataOps |
| `ConservationSlider` | currentThreshold, product, threshold, penaltyRatio, onDrag | DataOps |

### Design Tokens: `copilot-theme.css`

```css
:root {
  --copilot-bg: #fafafa;
  --copilot-card: #ffffff;
  --copilot-border: #e5e7eb;
  --copilot-primary: #2563eb;
  --copilot-success: #059669;
  --copilot-warning: #d97706;
  --copilot-danger: #dc2626;
  --copilot-text: #1a1a1a;
  --copilot-text-secondary: #6b7280;
  --copilot-font: 'Inter', system-ui, sans-serif;
  --copilot-font-mono: 'JetBrains Mono', monospace;
  --copilot-radius-sm: 6px;
  --copilot-radius-md: 10px;
  --copilot-signal: #059669;
  --copilot-moderate: #d97706;
  --copilot-noise: #dc2626;
}
```

### Graded Reward (Spec Correction)

Reward formula per domain. Higher-stakes decisions → more learning.

| Domain | Key factors | High example | Low example |
|---|---|---|---|
| Trading | position_size × research_depth × time_horizon | 0.38 (NVDA concentrated) | 0.05 (QQQ small ETF) |
| Purchasing | waste_cost or stockout_revenue_loss | 0.84 (NFL Sunday -$2,400) | 0.12 (routine Tuesday) |
| DataOps | business_criticality × impact_scope | 0.62 (first-time trusted) | 0.08 (recurring warehouse) |

Learn response returns: `reward`, `previous_reward`, `reward_multiplier`.

---

## §5 — Trading Copilot

**User:** Retail trader tracking decision quality.
**Tier:** Personal (scoring only, no conservation, no AE).
**Factors:** 2 self-reported (research, conviction) + 4 auto/hidden.

### 4 Screens

| Screen | SDK components | Domain-specific |
|---|---|---|
| Journal (default) | DecisionHistory, CopilotShell, IKSBadge | TradeCard (ticker, direction, research/conviction dots, outcome) |
| Log Trade | ScoreResultCard (rewardLine + centroidDelta) | TradeTicketForm, MarketContext (auto SPY/VIX) |
| Insight | FingerprintPanel | Trading interpretations via props |
| Curve | TrajectoryChart | Trading narrative via props |

### Backend

```
Mounts: create_scoring_router("trading")
Context: /api/context/market-snapshot, /api/context/ticker/{ticker}, /api/context/portfolio-summary
MarketDataClient: Real Yahoo Finance + warm cache fallback. Not a JSON mock.
```

---

## §6 — Purchasing Copilot

**User:** Restaurant owner making daily ordering decisions.
**Tier:** Personal + AE rules (scoring + evolution).
**Factors:** 1 self-reported (demand) + 5 auto.

### 4 Screens

| Screen | SDK components | Domain-specific |
|---|---|---|
| Today's Orders (default) | DecisionHistory, CopilotShell, IKSBadge | OrderCard (emoji, quantity, waste sparkline, PatternBadge + EvolutionOrigin), WeatherWidget |
| Log Order | ScoreResultCard (rewardLine) | OrderForm (item, quantity, day, demand, events), auto-context |
| Insight | FingerprintPanel | Purchasing interpretations via props |
| Curve | TrajectoryChart | Purchasing narrative via props |

### Backend

```
Mounts: create_scoring_router("purchasing") + create_evolution_router("purchasing")
Context: /api/context/today-summary, /api/context/items, /api/context/waste-history/{item}, /api/context/weather
WeatherAdapter: Real Open-Meteo + cache. Already built in copilot_sdk.scoring.verification.
3 AE rule seeds: RULE-FRIDAY-PRODUCE (promoted), RULE-EVENT-PROTEIN (promoted), RULE-DAIRY-AUTO (rejected).
```

---

## §7 — DataOps Copilot

**User:** Data engineer triaging data quality alerts.
**Tier:** Enterprise (scoring + conservation + evolution + convergence + graph).
**Factors:** 0 self-reported + 6 auto-computed from graph. User only picks action.

### 5 Screens

| Screen | SDK components | Domain-specific |
|---|---|---|
| Dashboard (default) | CopilotShell, IKSBadge, ConservationSlider | PipelineGrid (9 systems), AlertQueue (sorted by impact, recurring auto-resolved) |
| Triage (from alert) | ScoreResultCard (rewardLine) | AlertContext, DependencyTree (blast radius from FEEDS), RecurrenceBadge, ActionPicker (5 buttons), FactorAutoFill |
| Insight | FingerprintPanel | DataOps interpretations |
| Evidence | EvolutionPanel | VariantDetail, PatternOriginCard (SOC→S2P→DataOps chain) |
| Curve | TrajectoryChart (annotations) | Disruption dip + recovery annotation |

### Backend

```
Mounts: create_scoring_router("dataops") + create_conservation_router("dataops") + create_evolution_router("dataops")
Context: /api/context/pipelines, /api/context/alerts, /api/context/system/{name}, /api/context/alert/{id}/deps, /api/context/alert/{id}/recurrence
ALL context endpoints use REAL AGEClient graph queries. No fixtures.
3 AE variant seeds + 1 pattern origin chain + disruption trajectory (~600 decisions).
```

### ci-platform Graph Schema (NEW)

```
Nodes: PipelineSystem, DataQualityAlert
Edges: FEEDS (system→system), AFFECTS (alert→system), CASCADES (alert→alert)
Seeding: seed_dataops_graph.py — 9 systems, ~15 FEEDS, 20 alerts
Same database as SOC. Different node labels. Same AGEClient.
```

---

## §8 — Build Sequence

### Prerequisites (COMPLETE ✅)

| Task | Status |
|---|---|
| EvolutionLedger → GAE | ✅ +22 tests |
| Convergence verify + extend | ✅ +12 tests |
| CompoundingScorer → copilot_sdk.scoring | ✅ 79 tests migrated |
| Directory structure (apps/) | ✅ Created |
| Git v5.75 tag + push (5 repos) | ✅ |

### Build (14 items → Loom)

| # | Item | Effort | Depends | Prompt |
|---|---|---|---|---|
| 1 | copilot-sdk backend (3 routers + reward) | 3d | Prerequisites ✅ | ✅ Ready |
| 2 | ci-platform DataOps schema + seeding | 3d | — | Needs writing |
| 3 | copilot-sdk frontend (8 components + tokens) | 4d | #1 | Needs writing |
| 4 | Trading backend | 2d | #1 | Needs writing |
| 5 | Trading frontend | 4d | #3, #4 | Needs writing |
| 6 | Purchasing backend | 2d | #1 | Needs writing |
| 7 | Purchasing frontend | 4d | #3, #6 | Needs writing |
| 8 | DataOps backend | 4d | #1, #2 | Needs writing |
| 9 | DataOps frontend | 6d | #3, #8 | Needs writing |
| 10 | Outcome pre-seeding (3 domains) | 1.5d | #4, #6, #8 | Needs writing |
| 11 | Integration testing | 2d | #5, #7, #9, #10 | Process |
| 12 | P3 display fixes | 2h | — | Deferred |
| 13 | Rehearsal | 1d | #11, #12 | Process |
| 14 | LOOM recording | 1d | #13 | — |

**Critical path:** #1→#3→#5→#7→#9→#11→#14 = ~25d
**Total effort:** ~38.5d. **Calendar:** ~6 weeks.

---

## §9 — Decisions Register (21 decisions, all resolved)

| # | Decision | Choice |
|---|---|---|
| 1 | Desktop first | ✅ |
| 2 | Ports configurable from .env | ✅ |
| 3 | Design tokens | Tailwind + copilot-theme.css |
| 4 | Pre-seeding | 1 script per domain |
| 5 | SDK imports | Local (scoring in same repo). Only GAE via sys.path. |
| 6 | Market data | Real MarketDataClient with warm cache |
| 7 | DataOps graph | Real ci-platform queries. No fixtures. |
| 8 | Graph seeding | Separate script, same DB, different node labels |
| 9 | DataOps factors | All 6 auto-computed from graph context |
| 10 | SDK frontend | 8 shared components |
| 11 | Conservation | SOC + DataOps only (enterprise tier) |
| 12 | AgentEvolver | SOC + Purchasing (rules) + DataOps (full panel) |
| 13 | Cross-copilot transfer | SOC → S2P → DataOps three-way chain |
| 14 | Graded rewards | ALL copilots. DomainPreset.compute_reward(). |
| 15 | Centroid delta | Trading only (most pedagogical) |
| 16 | Re-convergence | DataOps trajectory annotation |
| 17 | GAE visibility | GAE exposed directly. CompoundingScorer = scoring only. |
| 18 | GAE extraction | EvolutionLedger + conservation + reconvergence ✅ DONE |
| 19 | Accent colors | SOC blue, Trading red, Purchasing green, DataOps purple |
| 20 | Repo structure | 3 apps INSIDE copilot-sdk as apps/ subdirectories |
| 21 | CompoundingScorer location | Moved into copilot-sdk as copilot_sdk.scoring ✅ DONE |

---

## §10 — What This Proves

| Claim | Evidence | Visible in |
|---|---|---|
| Same engine, any domain | 4 copilots, 1 engine, same FingerprintPanel | Closing: 4 fingerprints |
| Platform, not a tool | Shared SDK, shared graph, shared protocol | All apps |
| Learns from decisions | IKS trajectory in all 4 apps | Stories 5.9, 6.9, 7.12 |
| Finds your noise | Fingerprint "aha" in 3 new copilots | Stories 5.7, 6.8, 7.9 |
| Graph-connected | DataOps queries SAME database as SOC | Story 7.13 |
| Enterprise-grade | Conservation law fires in SOC AND DataOps | Stories 2.1, 7.3 |
| Self-improving | AgentEvolver in SOC + Purchasing + DataOps | Stories 2.2, 6.3, 7.10 |
| Pattern transfer | SOC → S2P → DataOps three-way chain | Stories 4.4, 7.11 |
| Learns proportionally | Graded rewards in ALL 4 copilots | Stories 1.4, 5.5, 6.7, 7.8 |
| Recovers from disruption | DataOps trajectory: dip + 2× faster recovery | Story 7.12 |
| Engine internals visible | Centroid delta table in Trading | Story 5.6 |
| Personal scale too | Trading Copilot for one trader. Same math. | Story 5 |

---

*Copilot Application Design Spec v3 (FINAL) · May 8, 2026*
*4 applications. 7 stories. 8 innovations. 21 decisions.*
*All prerequisites complete. Build ready.*
*~38.5 days to Loom. ~6 weeks calendar.*
*"The platform isn't shared components — it's shared PROPERTIES."*
