# Trading Copilot — Product Definition
## The System That Learns Your Trading Biases

**Version:** 1.0 · **Date:** May 20, 2026
**Audience:** Product definition for engineering, community, and investor.
**Buyer:** Individual trader — retail, semi-pro, or small prop desk.
The buyer IS the user. No enterprise sales cycle. No IT approval.
**License:** Apache 2.0 (open source core). Cloud tier for hosting.
**Authority:** CI Architecture v4 + Purchasing Copilot Product Def v1.1
(structure) + open-source trading ecosystem research (May 2026).
**Post-review fixes:** η_override 0.02→0.01 (calibration pending).
q_window 200→400 (theorem-validated). skip_recommended hypothetical
verification added. Existing codebase (5,3,6) migration path documented.
Pricing raised (Pro $150-300, Prop $2K-5K). Community governance fully
automated. Regime classifier AgentEvolver note. MAP items reference
existing screens/tests.

---

## §1 — The Problem Nobody Has Solved for Individual Traders

Every trading tool helps you EXECUTE trades. None of them help you
understand WHY some of your decisions are better than others.

TradingView gives you charts. Alpaca gives you execution. QuantConnect
gives you backtesting. Tradervue gives you a journal. All valuable.
All static. Trade #10,000 is evaluated with exactly the same insight
as trade #1.

Meanwhile, you've been trading for 3 years and you KNOW — somewhere
in the back of your mind — that your RSI oversold trades
underperform. That you overtrade on Fridays. That your position
sizing gets aggressive after a winning streak. That your best
setups are the boring ones you take reluctantly.

But you can't PROVE any of this. Your journal shows P&L by setup.
It doesn't show which signals you overtrust, which market conditions
degrade your judgment, or when a strategy is safe to scale from
paper to real money.

**What we build:** a decision quality layer that sits on top of
your existing trading stack, learns which of YOUR signals actually
predict YOUR outcomes, proves when a strategy is safe to scale,
and gets measurably better with every verified trade. Open source.
Self-hostable. Your data stays on your machine.

After 1,000 verified trades, 315 geometric values encode YOUR
trading reality — your biases, your strengths, your blind spots.
Nobody else has this. It never rationalizes a bad trade. And
unlike your memory, it never forgets that your "favorite setup"
has a 48% win rate while your "boring setup" runs at 71%.

---

## §2 — Three Trader Personas

### Alex — Retail Swing Trader, 2 Years Experience

Trades from a home office. $50K account. 8-12 trades/week. Uses
TradingView for charts, Alpaca for execution, a Google Sheet for
journaling. Profitable in Q3 2025, gave it all back in Q4.
Suspects he overtraded during the drawdown but can't prove it.
His "system" is 4 setups he learned from YouTube. He doesn't know
which ones actually work FOR HIM vs which ones worked for the
YouTuber.

**What he'd pay for:** "Show me which of my setups actually makes
money, and which ones I keep taking because they FEEL right."

### Priya — Semi-Pro Options Trader, 5 Years Experience

$200K account. 15-25 trades/week. Trades options spreads and
directional plays. Uses ThinkOrSwim for analysis, IBKR for
execution, Edgewonk for journaling. Consistently profitable but
plateaued — can't figure out how to scale from $200K to $500K
without increasing risk proportionally. She knows her edge exists
but can't quantify WHERE it comes from or how much more capital
each strategy can safely absorb.

**What she'd pay for:** "Prove which strategies can handle more
capital and which ones are already at capacity."

### Marcus — Small Prop Desk, 3 Traders

Runs a 3-person prop desk. $2M capital. Each trader has their own
style. Marcus suspects Trader B is taking too much risk on
momentum plays but can't prove it without being adversarial.
Trader A's journal shows she's the most profitable, but her
drawdowns are deeper and longer. Marcus wants to understand each
trader's decision quality independently, not just their P&L.

**What he'd pay for:** "Show me each trader's decision quality
profile — not just their returns, but which signals they trust
that they shouldn't, and where their edge actually comes from."

---

## §3 — 12 Scenarios of Change

### Cluster A: Signal Truth (Ship First)

**T1: "My Favorite Setup Is My Worst Setup"**
BEFORE: Alex's RSI oversold + MACD cross is his go-to. He takes
it 3× more often than any other setup. Win rate: 48% — below his
overall 54% average. His "boring" volume breakout + trend
confirmation runs at 71%. He doesn't know this because his
journal shows P&L by month, not by setup × outcome quality.
AFTER: Signal trust analysis: "RSI+MACD: σ=0.31 (noisy). DK
weight: 12%. Volume+trend: σ=0.09 (reliable). DK weight: 94%.
You take the RSI trade 3× more often than the one that works."
Radar chart: expected importance vs actual importance. The gap
IS the bias.

**T2: "I Overtrade After Winning Streaks"**
BEFORE: Alex's position sizing increases 40% after 3 consecutive
winners. His win rate in the 4th trade: 38% (vs 54% baseline).
He's giving back $2,800/year in "confidence trades." He can't
see this because his journal doesn't correlate sizing with
recent outcomes.
AFTER: "Position sizing anomaly detected: after 3+ winners,
your size increases 40% but your accuracy drops 16pp. Pattern
consistent with overconfidence bias. Estimated annual cost:
$2,800. Recommendation: cap post-streak sizing at baseline
until conservation proof passes."

**T3: "Friday Afternoons Are Killing Me"**
BEFORE: Priya's overall Sharpe: 1.8. Her Friday 2-4pm Sharpe:
0.3. She doesn't notice because Friday P&L is blended into
weekly results. $1,200/month in Friday afternoon losses.
AFTER: "Time-of-day analysis: your accuracy by period.
Mon-Thu 9:30-11: 62%. Mon-Thu 11-3: 51%. Fri 2-4pm: 39%.
Recommendation: reduce Friday afternoon sizing by 60% or
stop trading after 2pm Friday."

**T4: "Which Market Regime Am I Good At?"**
BEFORE: Priya is profitable overall but doesn't know she's
a trending-market specialist. In ranging markets, her returns
are -2% annualized. She's been trading ranging markets with
trending-market strategies and losing without realizing it.
AFTER: "Regime analysis: Trending (VIX < 18): your accuracy
67%, Sharpe 2.4. Ranging (VIX 18-28): accuracy 44%, Sharpe
-0.3. High-vol (VIX > 28): accuracy 52%, Sharpe 0.8. Your
edge is concentrated in trending markets. Current regime:
ranging. Recommendation: reduce exposure."

### Cluster B: Strategy Scaling (Emerges from A)

**T5: "Can I Scale This Strategy?"**
BEFORE: Priya's iron condor strategy is profitable but she
runs it at $20K notional. Can she go to $50K? $100K? She
backtested — it looks fine. But backtests don't account for
HER execution quality, HER entry timing, HER adjustment
decisions. She needs proof from HER actual trades, not
hypothetical ones.
AFTER: Conservation law applied to capital allocation:
"Iron condor strategy: GREEN. 340 verified trades. Accuracy
71%. Consistency: σ=0.08. Safe to increase from $20K to
$35K. At $50K: AMBER — insufficient history at that size
to prove safety. Paper-trade 30 trades at $50K sizing first."
The conservation law prevents scaling into unproven territory.

**T6: "My Backtested Strategy Failed Live"**
BEFORE: Alex backtested a mean-reversion strategy. Sharpe 2.1
in backtest. Live: Sharpe 0.4 after 3 months. Why? Backtest
doesn't model HIS execution — entry timing, slippage from
hesitation, early exits from fear, size adjustments from
emotion. The strategy is fine; his execution degrades it.
AFTER: "Strategy execution gap: theoretical fill $142.30,
your actual average entry $142.67 (+$0.37 slippage). 40% of
exits are >2 hours before planned hold time. Holding to plan
would have improved Sharpe from 0.4 to 1.6. Your execution
is the bottleneck, not the strategy."

### Cluster C: Trader Self-Knowledge (Month 3+)

**T7: "The Revenge Trade"**
BEFORE: After a loss, Alex takes a "recovery trade" within
30 minutes 65% of the time. These trades have a 34% win rate
(vs 54% baseline). He knows he shouldn't but does it anyway.
No tool quantifies the cost or catches it in real time.
AFTER: "Emotional pattern detected: trade within 30 minutes
of a loss. Historical accuracy: 34% (N=47). Estimated annual
cost: $4,200. Current status: you took a loss 12 minutes ago.
Conservation status for this category: RED — accuracy below
threshold. Recommendation: wait 60 minutes."

**T8: "Each Trader's Real Edge"** (Marcus — prop desk)
BEFORE: Trader A is most profitable but has the deepest
drawdowns. Trader B is steady but Marcus suspects excessive
risk. Trader C is new and Marcus doesn't know her strengths.
All three use the same tools. P&L reports don't explain WHY.
AFTER: Per-trader signal trust profile:
"Trader A: Edge is in high-conviction directional plays
(σ=0.07, weight 96%). Weakness: position sizing on earnings
(σ=0.34, weight 8%). Cut earnings sizing 50%.
Trader B: Edge is in mean-reversion (σ=0.09, weight 91%).
Risk flag: momentum trades have NEGATIVE expected value.
Eliminate momentum from B's mandate.
Trader C: Emerging edge in sector rotation (12 trades,
early signal). Assign sector rotation research to C."

### Cluster D: System Self-Governance

**T9: "The Strategy That Stopped Working"**
BEFORE: Priya's put credit spread strategy was profitable
for 18 months. Returns went negative 6 weeks ago. She's
still trading it because "it'll come back." But the market
regime changed (trending → ranging) and her strategy is
regime-dependent.
AFTER: Conservation law fires AMBER: "Put credit spread
strategy: accuracy dropped from 68% to 49% over 6 weeks.
Rolling q below θ_min. Auto-sizing paused for this strategy.
Recommendation: paper-trade until accuracy recovers above
threshold, or investigate regime dependency."

**T10: "Prove It Before Real Money"**
BEFORE: Alex wants to try a new breakout strategy. His
options: backtest (doesn't model his execution), paper
trade (no pressure, different psychology), or go live
with small size (still real money on unproven strategy).
AFTER: Conservation-gated promotion: "Paper-trade this
strategy. After 50 paper trades, if accuracy ≥ 58% and
consistency σ ≤ 0.15, the system will promote to live with
2% sizing. After 100 live trades maintaining accuracy,
promote to 5%. Each expansion is proven, not hoped."

### Cluster E: Knowledge Preservation

**T11: "I Lost 3 Years of Pattern Recognition"**
BEFORE: Alex switched brokers. His trade history is split
across two platforms and a spreadsheet. The patterns he
built over 3 years are fragmented. He can't query "what's
my win rate on breakouts in trending markets on tech stocks"
without manually assembling data from 3 sources.
AFTER: Import from Alpaca + IBKR + CSV. All trades unified
in one context graph. 3 years of patterns preserved in
centroid geometry. Cross-broker analysis immediately
available. The system doesn't care where the trade executed
— it cares about the decision quality.

**T12: "The Playbook Nobody Wrote Down"**
BEFORE: Marcus's Trader A is leaving the prop desk. Her
"playbook" is intuition built from 8,000 trades. She
can't articulate it. Marcus can't transfer it to the
replacement.
AFTER: IKS = 74. Trader A's 8,000 verified trades
compiled into centroid geometry + DK weights. The
replacement starts with Trader A's signal trust profile,
strategy performance by regime, execution quality
benchmarks. Not a document — a mathematical encoding of
what made her profitable.

### Cluster F: Volatility Defense (Timely — VIX Environment)

**T13: "The Tariff Shock Survivor"**
BEFORE: April 2025 tariff shock. Portfolio -12%. Panic sell at
bottom. Recovery missed.
AFTER: "Your tariff-event accuracy: 31%. Panic-sell timing: 22%
correct. 4/5 prior tariff events recovered in 14 days. Hold."
Trader holds. Recovery captured. +$6,400 vs panic.

**T14: "Regime Shift — Trending to Volatile"**
BEFORE: Trader keeps running trending strategies in volatile
market. Accuracy drops 67% → 38%. Doesn't notice for 6 weeks.
Gives back $4,800.
AFTER: Week 1 of shift: "Your trending accuracy in volatile:
38%. Sizing AMBER. Switch to income strategies (62%) or reduce
60%." $4,800 kept.

**T15: "The Revenge Trade at VIX 32"**
BEFORE: Calm market revenge trade: -$340. Volatile market
(VIX 32) revenge trade: -$1,200. Three in one week: -$3,600.
AFTER: "Decision Context: 8 min since loss. VIX 32. Your
accuracy in this pattern at high VIX: 22%. Conservation: RED."

### Cluster G: Volatility Offense (Making Money FROM Volatility)

*The defensive angle (Cluster F) says "survive your biases."
The offensive angle says "HERE is where YOUR edge is in volatile
markets." Most tools reduce exposure when VIX rises. We show
you where to INCREASE it — based on YOUR verified history.*

**T16: "Your Volatile-Market Edge"**
BEFORE: VIX spikes. Every tool says "reduce exposure." Trader
reduces everything uniformly. Misses the strategies where she
EXCELS in volatile conditions. She's a better premium seller
at VIX 30 than at VIX 15 — but she doesn't know this.
AFTER: "Regime shift: volatile (VIX 32).
  Strategy reallocation based on YOUR regime data:
  — Income strategies: INCREASE 40% (your accuracy 71% at
    VIX 25-35, vs 58% at VIX < 20. Edge LARGER in volatility)
  — Trend following: DECREASE 60% (38% accuracy at high VIX)
  — Mean reversion: HOLD (54%, regime-independent)
  Net: you're ROTATING to where YOUR edge lives, not reducing."

**T17: "Premium Selling at the Right Time"**
BEFORE: Priya sells options premium in calm AND volatile markets
at the same sizing. Calm: IV/RV < 1.2, thin premium, 49%
accuracy. Volatile: IV/RV > 1.5, rich premium, 78% accuracy.
No tool tells her the difference.
AFTER: "IV/RV ratio: 1.72 (premium is rich). Your short premium
  accuracy at IV/RV > 1.5: 78% (N=34). At IV/RV < 1.2: 49%.
  Your premium selling EDGE IS ON. Conservation: GREEN.
  Recommendation: increase premium allocation 30%.
  This is YOUR historically best environment."

**T18: "Correlation Breakdown — Your Real Exposure"**
BEFORE: Alex holds 5 "diversified" positions. VIX crosses 30.
Correlations spike from 0.3 to 0.7. His 5 positions are now
1 concentrated bet. Effective exposure: 3× what he thinks.
AFTER: "Correlation alert: cross-correlation 0.32 → 0.71 in
  5 days. Diversification collapsed. Effective position: 3.2×
  intended. Your concentrated-position accuracy: 34% (N=8).
  Options: reduce 2 positions, add VIX hedge (your VIX call
  spread accuracy: 67%, N=12), or hold with awareness."

**T19: "Earnings Volatility — Your ACTUAL Edge"**
BEFORE: Earnings season. Alex takes directional bets (calls/puts).
Win rate: 39%. He also plays straddles occasionally. Win rate:
68%. He takes directional 4× more often. $4,200/year lost.
AFTER: "76 verified earnings trades: Directional: 39% (N=53).
  Straddles: 68% (N=23). You're an earnings VOLATILITY trader,
  not a direction trader. This season: straddles only.
  Conservation: RED for directional earnings."

**T20: "VIX Mean-Reversion — Your Timing"**
BEFORE: VIX mean-reverts historically. Trader shorts VIX after
spikes. Good idea, poor execution: enters too early, holds too
long.
AFTER: "18 VIX trades: entry accuracy (peaked?): 44% (too early).
  3-day hold: 71%. 1-day hold: 39%. Recommendation: wait for
  2-day decline confirmation. Hold minimum 3 days. Projected
  adjusted accuracy: 68%."

---

## §3.5 — Volatility Trading: The Architectural Advantage

### Why Our System Is Uniquely Valuable in Volatile Markets

Most trading tools treat volatility as RISK. We treat it as
INFORMATION. The difference:

| Approach | What it says at VIX 32 | Result |
|---|---|---|
| Risk management | "Reduce all exposure 50%" | Misses the strategies that WORK better at high VIX |
| Our system | "ROTATE: income +40%, trending -60%, reversion hold" | Captures the volatile-market edge |

**The architectural reason nobody else can do this:**

Per-regime, per-trader accuracy requires the full stack:
1. DiagonalKernel — learns which signals predict YOUR outcomes
   in EACH regime separately
2. Conservation law — proves regime-specific scaling is safe
3. Centroid learning — your volatile-market centroids DIFFER
   from calm-market centroids (the system learns both)
4. Judgment memory — remembers your earnings plays, VIX timing,
   correlation exposure across regimes

No competing tool has verified outcome data segmented by regime
feeding back into per-signal trust weights.

**The pitch:** "Every tool says 'reduce exposure' when VIX spikes.
We say 'HERE is where your edge lives in volatile markets. ROTATE
to it.' Not less trading. DIFFERENT trading. Proven from YOUR
verified trades."

### Volatility Value Multiplier

| Capability | Calm (VIX 15) | Volatile (VIX 32) | Multiplier |
|---|---|---|---|
| Signal trust analysis | Nice to know | Edge vs bias = survival | 3× |
| Conservation sizing | Prevents oversize | Prevents blowup | 5× |
| Regime strategy rotation | Minor optimization | $4,800 kept + edge captured | 4× |
| Premium selling timing | Low premium, low edge | Rich premium, YOUR edge ON | 6× |
| Correlation detection | Low risk | Portfolio collapse risk | 10× |
| Earnings vol edge | Small seasonal | Elevated IV = larger edge | 3× |
| **Platform value** | **$16-26K/year** | **$64-130K/year** | **4-5×** |

### Volatility Engineering Specifications

**Phasing:** T13-T15 (defense) use existing factors — no new code.
T16, T18, T19 need new services (v1.0 achievable). T17, T20 need
options/VIX-specific data (v1.1 — after options factor extension).

**RegimeRecommender service (T16):**

```python
class RegimeRecommender:
    """Translates per-regime accuracy into allocation
    recommendations. Uses verified trade history segmented
    by regime × category.
    """
    def recommend(self, current_regime: str,
                  regime_accuracy: dict[str, dict[str, float]]
                  ) -> list[StrategyShift]:
        """
        regime_accuracy: {
          "trend_following": {"trending": 0.67, "volatile": 0.38},
          "income_strategy": {"trending": 0.58, "volatile": 0.71},
          ...
        }
        Returns ranked shifts:
          [StrategyShift("income_strategy", +0.40, reason="..."),
           StrategyShift("trend_following", -0.60, reason="...")]
        
        Logic: for each category, compare current-regime accuracy
        to baseline. If above baseline → INCREASE. If below → DECREASE.
        Magnitude proportional to accuracy delta.
        Conservation gate: only recommend increases for categories
        with conservation GREEN in the current regime.
        """
        ...

@dataclass
class StrategyShift:
    category: str
    allocation_change_pct: float  # +40 = increase 40%
    current_regime_accuracy: float
    baseline_accuracy: float
    conservation_status: str      # must be GREEN to increase
    reason: str
```

**CorrelationMonitor service (T18):**

```python
class CorrelationMonitor:
    """Monitors cross-position correlation. Alerts when
    diversification collapses.
    
    Data: daily returns for all open positions (from yfinance).
    Window: 20-day rolling correlation matrix.
    Alert: when avg pairwise correlation > 0.6 (configurable).
    """
    def check_correlation(self, positions: list[str]
                          ) -> CorrelationAlert | None:
        # Fetch 20-day returns for each position
        # Compute pairwise Pearson correlation matrix
        # Average off-diagonal elements
        # If avg > threshold → alert
        ...

@dataclass
class CorrelationAlert:
    avg_correlation: float        # current average
    baseline_correlation: float   # 60-day baseline
    effective_multiplier: float   # how much real exposure exceeds intended
    concentrated_accuracy: float  # trader's accuracy when correlated
    recommendations: list[str]    # "reduce 2 positions", "add VIX hedge"
```

**EarningsSubcategory classifier (T19):**

```python
def classify_earnings_trade(trade: NormalizedTrade) -> str:
    """Split event_driven into directional vs volatility.
    
    Directional: single-leg calls or puts around earnings.
    Volatility: straddles, strangles, iron condors around earnings.
    """
    if trade.asset_type == "option":
        if trade.strategy_tag in ["straddle", "strangle", "iron_condor"]:
            return "event_volatility"
        else:
            return "event_directional"
    else:
        return "event_directional"  # equity = directional bet
```

**IV/RV ratio (v1.1 — options extension):**

```python
class IVRVFactor:
    """v1.1: Implied vs Realized volatility ratio.
    Requires options data (py_vollib or broker API).
    
    v1.0: Not available. T17 uses regime_accuracy proxy:
    "Your premium selling accuracy at VIX > 25" (from
    market_regime factor, NOT from IV/RV directly).
    
    v1.1: True IV/RV from options chain data.
    IV = at-the-money implied vol (from broker).
    RV = 20-day realized vol (from yfinance).
    Ratio > 1.5 = premium is rich. < 1.0 = premium is cheap.
    """
    def compute(self, ticker: str) -> float:
        # v1.1 implementation
        ...
```

**v1.0 vs v1.1 capability map:**

| Scenario | v1.0 (equity traders) | v1.1 (options extension) |
|---|---|---|
| T16 (regime rotation) | ✅ Uses regime_accuracy | ✅ Same |
| T17 (premium timing) | ⚠️ Proxy: VIX-level accuracy | ✅ True IV/RV ratio |
| T18 (correlation) | ✅ CorrelationMonitor | ✅ Same |
| T19 (earnings vol) | ✅ Subcategory classifier | ✅ Same + Greeks |
| T20 (VIX timing) | ⚠️ Basic entry/hold analysis | ✅ VIX term structure |

---

## §4 — Technology Value → Business Value

| Innovation | Technology | Trader Sees | Scenarios |
|---|---|---|---|
| DiagonalKernel | Per-signal noise fingerprint | "Which of MY indicators actually predict MY outcomes" | T1, T4, T16 |
| Signal-confidence inversion | Trusted signal = noisiest | "My favorite setup is my worst setup" | T1, T19 |
| Conservation law | Mathematical quality invariant | "Proof that scaling from $20K to $35K is safe" | T5, T9, T10, T14 |
| Centroid learning | Verified decisions move vectors | "System gets better with every trade I log" | All |
| Judgment memory | Fourth cognitive type | "After 1,000 trades, it knows MY biases" | T2, T3, T7, T15 |
| AgentEvolver | Self-tuning within safety bounds | "Alert thresholds and position limits auto-calibrate" | T9 |
| Re-convergence | Recovery faster after disruption | "After the regime change, system re-calibrates in 2 weeks" | T9, T13 |
| Two-phase learning | Phase 1: patterns. Phase 2: which matter | "New trader inherits departing trader's 8,000-trade profile" | T8, T12 |
| Regime-conditioned DK | Per-regime signal weights | "Your income edge is LARGER at VIX 32 than at VIX 15" | T16, T17, T20 |
| Correlation monitoring | Cross-position covariance | "Your 5 positions are now 1 bet. Effective exposure: 3×" | T18 |
| IV/RV awareness | Implied vs realized vol ratio | "Premium is rich. Your edge is ON. Increase allocation." | T17 |
| Earnings regime detection | Event volatility classification | "You're a volatility trader, not a direction trader" | T19 |

---

## §5 — Differentiation & Positioning

### The Competitive Test

| Question | Tradervue | Edgewonk | QuantConnect | TradingView | Us |
|---|---|---|---|---|---|
| Which of my signals is noise? | Can't | Basic stats | Backtest only | Can't | Per-signal DK weights from YOUR outcomes |
| After 1,000 trades, show the improvement curve | P&L chart | P&L chart | Equity curve | Can't | Decision quality curve (accuracy, not just returns) |
| Prove I can scale this strategy | Can't | Can't | Backtest says yes | Can't | Conservation law on YOUR execution data |
| Detect my emotional trading patterns | Tag manually | Tag manually | Can't | Can't | Auto-detected from trade spacing/sizing anomalies |
| When my strategy stops working, warn me | Can't | Can't | Drawdown alert | Can't | Conservation AMBER with regime attribution |
| Transfer a trader's pattern recognition | Can't | Can't | Code the strategy | Can't | 315 values encoding 8,000 trades |
| Open source? | No | No | Yes (LEAN) | No | Yes (Apache 2.0) |
| My data stays on my machine? | No (cloud) | No (cloud) | Optional | No | Yes (self-hosted default) |

### Competitive Positioning

Tradervue and Edgewonk are **trade journals** — they record what
happened. We analyze WHY it happened and what to do about it.

QuantConnect LEAN is **algorithmic infrastructure** — it executes
strategies. We evaluate the TRADER executing the strategy.

TradingView is **charting and analysis** — it shows the market.
We show the trader TO the trader.

We're not replacing any of these. We're the **decision quality
layer** that sits on top of all of them:

```
Your existing stack (unchanged):
  TradingView (charts) → Alpaca/IBKR (execution) → yfinance (data)

Our layer (NEW — what nobody has):
  Import trades → Score decisions → Learn signal trust →
  Prove strategy safety → Detect degradation → Transfer patterns
```

---

## §6 — Open Source Strategy

### Why Open Source Is Right for Trading (Specifically)

| Factor | Why OSS wins |
|---|---|
| **Trust** | Traders are extremely skeptical of black boxes. "I can read every line that evaluates my signals." |
| **Data sovereignty** | "My trading data stays on MY machine." Self-hostable by default. No cloud dependency. |
| **Adoption friction** | `pip install ci-trading` → import trades → see results in 10 minutes. No signup. No credit card. |
| **Moat preservation** | The code is NOT the moat. The 315 centroid+weight values encoding YOUR patterns are. Open-sourcing the engine costs nothing strategically. |
| **Community** | Traders will contribute factor computers for their own indicators. RSI factor, VWAP factor, options Greeks factor — community-driven, like HuggingFace models. |
| **GAE alignment** | GAE is already Apache 2.0. Trading copilot built on GAE inherits and validates this strategy. |

### Business Model

| Tier | Price | What |
|---|---|---|
| **Core (OSS)** | Free | Self-hosted. All scoring, learning, conservation, signal trust. Local data. Community factors. CLI + web UI. |
| **Cloud** | $30–50/month | Hosted instance. Auto-sync from Alpaca/IBKR. Market data feeds. Backup. Mobile alerts. |
| **Pro** | $150–300/month | Anonymized cross-trader signal insights ("RSI works for 23% of swing traders in trending markets"). Strategy marketplace. Advanced conservation analytics. Multi-trader dashboard (Marcus). |
| **Prop Desk** | $2,000–5,000/month | Multi-trader profiles. Per-trader risk limits governed by conservation. Aggregate pattern transfer. Compliance export. (Marcus manages $2M — $5K/month is 0.3% of capital, trivial if the system prevents one bad month.) |

### What's Open Source vs Proprietary

| Layer | License | Rationale |
|---|---|---|
| GAE (ProfileScorer, DiagonalKernel, conservation) | Apache 2.0 (existing) | Core engine — already open |
| Trading factor computers | Apache 2.0 | Community contributions |
| TradingDomainConfig + centroids | Apache 2.0 | Domain config |
| Import connectors (Alpaca, IBKR, CSV) | Apache 2.0 | Reduce friction |
| CLI + local web UI | Apache 2.0 | Self-hosted experience |
| Cloud hosting infrastructure | Proprietary | Revenue layer |
| Cross-trader anonymized insights | Proprietary | Network effect moat |
| Prop desk multi-trader dashboard | Proprietary | Enterprise upsell |

### Community-Driven Factor Computers

The factor computer protocol is simple: `compute(entity_id, context) → float`. Traders contribute their own:

```python
# community/factors/vwap_deviation.py
class VWAPDeviationFactor(FactorComputer):
    """Entry price vs VWAP. Measures execution quality."""
    def compute(self, entity_id, context) -> float:
        entry = context["entry_price"]
        vwap = context["vwap_at_entry"]
        deviation = abs(entry - vwap) / vwap
        return max(0.0, 1.0 - min(deviation * 20, 1.0))
```

After 500 trades with this factor, DiagonalKernel tells the trader
whether VWAP deviation actually predicts THEIR outcomes. Community
factors get rated by predictive power across users (anonymized).

---

## §7 — Architecture & Feature Sets

### 7.1 Product Architecture

**Decision quality layer, not trading platform.** We don't provide
charts, execution, data, or signals. We evaluate the QUALITY of
decisions made using the trader's existing stack.

**Existing codebase (apps/trading/, port 8010/5174):**
The SDK already has a trading copilot prototype with 36 BE tests,
red accent, and 5 screens: Dashboard, Log Trade (with
ReasoningPanel SC-9), Analysis, Performance (with
ConservationProjection SC-10). Existing tensor: (5, 3, 6).

This product definition EXTENDS the prototype, not replaces it:

| Dimension | Existing | Product Def | Migration |
|---|---|---|---|
| Categories (C) | 5 (same names) | 5 (unchanged) | None |
| Actions (A) | 3 (strong/partial/poor) | 4 (+skip_recommended) | Add row to centroids |
| Factors (d) | 6 | 7 (+signal_confidence) | Add column to centroids |
| Tensor | (5,3,6) = 90 | (5,4,7) = 140 | Pad existing values |
| Screens | 5 existing | Extend existing | Add components, don't rebuild |
| Tests | 36 BE | 36 + new | Update tensor shape assertions |

**Screen extensions (leverage existing):**
- Dashboard → keep, add pattern indicator badges
- Log Trade → keep, add "Skip" action button + reasoning
- Analysis → extend with Trust Analysis radar (F2 hero)
- Performance → extend with Pattern Detector panel (F4)
- NEW: CLI (F8) — no existing equivalent

**Centroid migration:** Existing 90 values are preserved. New
skip_recommended row initialized from domain heuristics (§10.5).
New signal_confidence column initialized at 0.5 (neutral).
Migration is additive — no existing centroid value changes.

### 7.2 Factor Space

**5 categories × 4 actions × 7 factors = 140 centroid values**
**+ 175 DK weights = 315 total geometric values**

**Categories (C=5) — trade types:**

| Index | Category | Description |
|---|---|---|
| 0 | trend_following | Momentum, breakout, trend continuation |
| 1 | mean_reversion | Oversold bounce, regression to mean |
| 2 | event_driven | Earnings, news, catalysts |
| 3 | income_strategy | Options selling, dividends, yield |
| 4 | scalp_intraday | <1 hour holds, quick in-and-out |

**Actions (A=4) — decision outcomes:**

| Index | Action | Description |
|---|---|---|
| 0 | strong_execution | Entry, sizing, hold, exit all aligned with plan |
| 1 | partial_execution | Some elements deviated from plan |
| 2 | poor_execution | Significant deviation (early exit, wrong size, revenge) |
| 3 | skip_recommended | System recommends NOT taking this trade |

**Factors (d=7) — decision quality indicators:**

| Index | Factor | What It Measures | Source |
|---|---|---|---|
| 0 | signal_alignment | Did entry match the trader's stated signals? | TA-Lib indicators vs entry |
| 1 | market_regime | Current regime vs trader's strength profile | VIX, trend/range classifier |
| 2 | position_sizing | Size consistent with strategy/account rules? | Trade size vs account/vol |
| 3 | timing_quality | Entry/exit timing vs plan and optimal | Trade timestamps vs plan |
| 4 | risk_reward_actual | Actual R:R vs planned R:R | Entry/stop/target vs outcome |
| 5 | emotional_indicator | Revenge, FOMO, overconfidence signals | Trade spacing, sizing anomalies |
| 6 | signal_confidence | Which TA signals predict THIS trader's outcomes | DK weights on indicators |

### 7.3 Feature Specifications — v1.0 (Day 1, open source)

**F1: Trade Import**
Import from Alpaca API, IBKR API, CSV, or manual entry.
Normalize all trades to common schema: ticker, direction,
entry_price, exit_price, size, timestamps, strategy_tag.
Historical import: up to 5 years of trade history.
*Engineering: Alpaca SDK + IBKR TWS API + CSV parser. ~3 days.*

**F2: Signal Trust Dashboard** [HERO FEATURE]
Radar chart: expected signal importance (trader's belief) vs
actual signal importance (DK weights from verified outcomes).
Per-setup breakdown: "RSI+MACD: weight 12%. Volume+trend:
weight 94%." Table: all setups ranked by DK-weighted accuracy.
*Engineering: DiagonalKernel weight visualization. React + D3. ~1 week.*

**F3: Decision Quality Scorer**
Each trade scored by ProfileScorer across 7 factors. Evidence:
"Signal alignment: 0.82 (strong entry). Timing: 0.45 (entered
20 min late). Emotional: 0.30 (revenge pattern — loss 8 min ago).
Overall: hold_for_review. This trade matches your overtrade-after-
loss pattern."
*Engineering: Factor computers + ProfileScorer + NL templates. ~1 week.*

**F4: Pattern Detector**
Auto-detects behavioral patterns: overtrading after wins/losses,
time-of-day performance, regime-dependent accuracy, sizing drift.
"After 3+ winners, your sizing increases 40% but accuracy drops
16pp." Dashboard shows all detected patterns with statistical
significance and estimated annual cost.
*Engineering: Statistical pattern detection on trade history. ~1 week.*

**F5: Conservation Dashboard (Strategy Safety)**
Per-strategy GREEN/AMBER/RED. "Trend_following: GREEN. 340 trades.
Accuracy 67%. Safe to increase sizing 20%." "Mean_reversion:
AMBER. Accuracy dropped 12pp in 6 weeks. Sizing frozen."
Strategy promotion path: paper → small live → full live, each
gate governed by conservation law.
*Engineering: ConservationMonitor per strategy category. ~3 days.*

**F6: IKS (Institutional Knowledge Score)**
"IKS = 0 at install. IKS = 34 after 500 trades. IKS = 71 after
2,000 trades." Shows how much the system has learned about YOUR
trading patterns. Per-category breakdown.
*Engineering: IKSService (exists). Wire to TradingDomainConfig. ~0.5 day.*

**F7: Trade Journal (Replaces Tradervue)**
Chronological trade log with factor scores, evidence, P&L.
Filter by: setup, category, regime, date range, outcome.
"Show me all mean_reversion trades in ranging markets last
quarter" → instant answer with aggregate stats.
*Engineering: Trade log UI + query interface. ~3 days.*

**F8: CLI (Command Line Interface)**
```bash
ci-trading import --broker alpaca --days 365
ci-trading score --trade-id TRD-1847
ci-trading trust --show-radar
ci-trading conservation --strategy trend_following
ci-trading patterns --min-significance 0.05
```
For technical traders who prefer terminal over web UI.
*Engineering: Click/Typer CLI wrapping API. ~2 days.*

### 7.4 Features — v1.1 (Month 2-4)

**F9: Real-Time Decision Support**
Live market data (yfinance) + factor scoring on potential trades
BEFORE execution. "You're about to take an RSI oversold trade.
Your historical accuracy on this setup: 48%. Market regime:
ranging (your worst). Recommendation: skip or reduce size 50%."
*Engineering: yfinance streaming + pre-trade scoring. ~2 weeks.*

**F10: Regime Classifier**
Automatic market regime detection (trending/ranging/volatile)
from VIX, price action, breadth. Maps to trader's per-regime
performance. "Current: ranging. Your edge in ranging: negative.
Recommended strategies: income_strategy only."
*Engineering: VIX + trend classifier + historical mapping. ~1 week.*

**F11: Strategy Promotion Engine**
Paper-trade → small-live → full-live pipeline. Each transition
requires conservation proof. "Paper: 50 trades, accuracy 62%,
σ=0.12. Promote to live at 2% sizing? [PROMOTE] [CONTINUE PAPER]"
*Engineering: ConservationMonitor + promotion state machine. ~1 week.*

**F12: AgentEvolver (Self-Tuning Alerts)**
Auto-calibrates alert thresholds, pattern sensitivity, regime
boundaries from verified outcomes. "Revenge trade detection
window adjusted from 30 min to 45 min based on your patterns."
*Engineering: AgentEvolver with trading variant dimensions. ~2 weeks.*

### 7.5 Features — v2.0 (Month 6+)

**F13: Multi-Trader Dashboard** (Marcus — prop desk)
Per-trader profiles. Aggregate desk performance. Transfer
patterns across traders. "Trader A's iron condor edge →
suggested for Trader C."

**F14: Cross-Trader Insights** (Pro tier, proprietary)
Anonymized: "Swing traders using RSI: 23% profitable in ranging
markets. Volume-based entries: 61% profitable across all regimes."
Opt-in data contribution for community intelligence.

**F15: Broker Execution Analysis**
Compare fill quality across brokers. "Alpaca: avg slippage
$0.12. IBKR: avg slippage $0.04. On your trading frequency,
switching saves $1,200/year."

---

## §8 — Integration Ecosystem

### 8.1 Day 1 Integrations (all open source / free)

| Integration | Library/API | Purpose | Effort |
|---|---|---|---|
| **Alpaca** | `alpaca-py` (free, paper+live) | Trade import + execution data | 2d |
| **yfinance** | `yfinance` (free, no key) | Historical prices, market data | 1d |
| **pandas-ta** | `pandas-ta` (free, 130+ indicators) | Factor computers for any TA signal | 2d |
| **CSV import** | Built-in | Universal fallback (any broker export) | 0.5d |

### 8.2 Month 1-3 Integrations

| Integration | Library/API | Purpose | Effort |
|---|---|---|---|
| **Interactive Brokers** | `ib_insync` | IBKR trade import (serious traders) | 3d |
| **FRED** | `fredapi` (free) | VIX, rates, macro for regime classifier | 1d |
| **Tradier** | REST API | Alternative broker | 1d |
| **TradingView webhooks** | Webhook receiver | Signal capture from TV alerts | 1d |

### 8.3 Month 3+ Integrations

| Integration | Library/API | Purpose | Effort |
|---|---|---|---|
| **ThinkOrSwim** | CSV export (no API) | TD Ameritrade import | 0.5d |
| **Webull** | Limited API | Popular retail broker | 1d |
| **Options data** | `py_vollib` | Greeks computation for options factors | 2d |

### 8.4 Open-Source Dependencies (all Apache/MIT/BSD)

```
numpy           # Core math
pandas          # Data handling
pandas-ta       # 130+ technical indicators
yfinance        # Market data (Yahoo Finance)
alpaca-py       # Alpaca broker API
ib_insync       # Interactive Brokers API
fredapi         # FRED economic data
fastapi         # Local web API
click           # CLI framework
plotly / d3     # Visualization
```

No proprietary dependencies. Everything runs offline after
initial data pull. Self-contained.

---

## §9 — Dataset Specifications

### DS1: Synthetic Trade History (2,000 trades, 18 months)

| Category | % | Count | Archetype behavior |
|---|---|---|---|
| trend_following | 35% | 700 | 58% win rate in trending, 41% in ranging |
| mean_reversion | 25% | 500 | 62% win rate overall, regime-independent |
| event_driven | 15% | 300 | Bimodal: big wins + big losses |
| income_strategy | 15% | 300 | High win rate (78%), small losses large |
| scalp_intraday | 10% | 200 | 52% win rate, high frequency |

**Embedded behavioral patterns (ground truth):**
- Overtrading after 3+ wins (sizing +40%, accuracy -16pp)
- Friday afternoon degradation (accuracy -15pp after 2pm)
- Revenge trades within 30 min of loss (accuracy 34%)
- Regime-dependent edge (trending: +18pp, ranging: -13pp)
- Position sizing drift over time (gradual increase)
- One "dead" strategy (profitable months 1-12, negative 13-18)

**Market alignment for demo:** Synthetic trades MUST align with
real market data (DS2). Generator reads yfinance prices and
creates plausible trades at real market conditions: "On 2025-03-15,
SPY at $512, RSI(14) = 28 (oversold), trader entered long at
$512.30." For development, synthetic/real mismatch is acceptable.
For demo, alignment is required — ensures the trust radar and
pattern detector produce realistic findings.

### DS2: Market Data (18 months, real data)

| Data | Source | Granularity |
|---|---|---|
| SPY, QQQ, IWM | yfinance | Daily OHLCV |
| VIX | yfinance | Daily close |
| 20 popular tickers | yfinance | Daily OHLCV |
| FRED rates | fredapi | Weekly |

Real data, free, downloadable. No synthesis needed.

### DS3: Technical Indicators (computed from DS2)

RSI(14), MACD(12,26,9), Bollinger(20,2), ATR(14), VWAP,
SMA(20,50,200), EMA(9,21), volume ratio, momentum(10).
Computed via pandas-ta on DS2 prices. Stored in
`data/indicators/` as CSV per ticker.

---

## §10 — Engineering Specifications

### 10.1 TradingDomainConfig

```python
class TradingDomainConfig:
    domain = "trading"
    
    categories = {
        0: "trend_following",
        1: "mean_reversion",
        2: "event_driven",
        3: "income_strategy",
        4: "scalp_intraday",
    }
    
    actions = {
        0: "strong_execution",
        1: "partial_execution",
        2: "poor_execution",
        3: "skip_recommended",
    }
    
    factors = [
        "signal_alignment",      # 0
        "market_regime",         # 1
        "position_sizing",       # 2
        "timing_quality",        # 3
        "risk_reward_actual",    # 4
        "emotional_indicator",   # 5
        "signal_confidence",     # 6
    ]
    
    penalty_ratio = 3.0   # Lower than purchasing (5:1) or SOC (20:1).
                           # Trading errors are recoverable (stop loss).
                           # But still asymmetric: system prefers
                           # missing a trade over taking a bad one.
    η_confirm = 0.05
    η_override = 0.01     # Same as all copilots. A trader overriding
                           # a "skip" because "this one feels different"
                           # is the NOISIEST signal — slow learning
                           # protects. Calibration experiment pending
                           # with pilot data: if trader override quality
                           # q̄_worst is demonstrably higher than SOC
                           # analysts, re-derive per Gemini method (v14).
    τ = 0.1
    q_window = 400        # Theorem-validated (math_synopsis v14).
                           # Active traders (8-12/week) reach full
                           # convergence in ~8-10 months. Semi-pro
                           # (15-25/week) in ~4-5 months. Reducing to
                           # 200 requires re-derivation of θ_min
                           # variance bounds — deferred to pilot.
    tensor_shape = (5, 4, 7)  # 140 centroid values
```

### 10.2 Factor Computers

```python
class SignalAlignmentFactor(FactorComputer):
    """Index 0. Did entry price align with stated signals?
    Uses pandas-ta to compute indicator values at entry time.
    Compares actual entry vs signal-optimal entry.
    """
    def compute(self, entity_id, context) -> float:
        signals = context.get("tagged_signals", [])
        if not signals:
            return 0.5  # no signals tagged
        confirmed = sum(1 for s in signals if s["confirmed"])
        return confirmed / len(signals)

class MarketRegimeFactor(FactorComputer):
    """Index 1. Trader's historical accuracy in current regime.
    Regime from classify_regime(). Returns trader's accuracy in
    the CURRENT regime — high = trader is good here.
    """
    def compute(self, entity_id, context) -> float:
        regime = context.get("current_regime", "unknown")
        accuracy = context.get("regime_accuracy", {}).get(regime, 0.5)
        return accuracy

class PositionSizingFactor(FactorComputer):
    """Index 2. Is position size consistent with strategy rules?
    Compares trade size to rolling average and account-based limit.
    High = size is within norms. Low = oversized or undersized.
    """
    def compute(self, entity_id, context) -> float:
        size = context.get("position_size_pct", 0)  # % of account
        rolling_avg = context.get("avg_position_size_pct", 2.0)
        max_allowed = context.get("max_position_size_pct", 5.0)
        
        if size > max_allowed:
            return 0.1  # hard violation
        ratio = size / rolling_avg if rolling_avg > 0 else 1.0
        # 1.0 = exactly average. Penalize deviation in either direction.
        deviation = abs(ratio - 1.0)
        return max(0.0, 1.0 - min(deviation, 1.0))

class TimingQualityFactor(FactorComputer):
    """Index 3. Entry/exit timing vs plan.
    Compares actual timestamps to planned timestamps.
    Also penalizes trades at bad times (Friday afternoon, etc.)
    if pattern detector has flagged those periods.
    """
    def compute(self, entity_id, context) -> float:
        score = 1.0
        
        # Entry timing: actual vs planned (if plan exists)
        entry_delay_min = context.get("entry_delay_minutes", 0)
        if entry_delay_min > 30:
            score -= 0.3  # late entry
        elif entry_delay_min > 10:
            score -= 0.1
        
        # Exit timing: early exit penalty
        hold_pct = context.get("hold_time_vs_plan_pct", 1.0)
        if hold_pct < 0.5:
            score -= 0.3  # exited at less than half planned hold
        elif hold_pct < 0.8:
            score -= 0.1
        
        # Time-of-day penalty (from pattern detector)
        tod_accuracy = context.get("time_of_day_accuracy", None)
        if tod_accuracy is not None and tod_accuracy < 0.40:
            score -= 0.2  # trading in a historically bad window
        
        return max(0.0, score)

class RiskRewardActualFactor(FactorComputer):
    """Index 4. Actual R:R vs planned R:R.
    Measures whether the trade delivered the intended risk/reward.
    """
    def compute(self, entity_id, context) -> float:
        planned_rr = context.get("planned_risk_reward", None)
        actual_rr = context.get("actual_risk_reward", 0)
        
        if planned_rr is None:
            # No plan: use absolute R-multiple
            return min(max((actual_rr + 1.0) / 3.0, 0.0), 1.0)
        
        # With plan: how close to planned R:R?
        if planned_rr <= 0:
            return 0.5
        ratio = actual_rr / planned_rr
        # ratio=1.0 = hit plan exactly. >1 = exceeded. <0 = loss.
        return min(max((ratio + 0.5) / 2.0, 0.0), 1.0)

class EmotionalIndicatorFactor(FactorComputer):
    """Index 5. Detects revenge, FOMO, overconfidence patterns.
    Uses trade spacing and sizing anomalies.
    Displayed as 'Decision Context' in UI (never 'emotional').
    """
    def compute(self, entity_id, context) -> float:
        minutes_since_last = context.get("minutes_since_last_trade", 999)
        last_was_loss = context.get("last_trade_was_loss", False)
        sizing_vs_avg = context.get("size_vs_rolling_avg", 1.0)
        consecutive_wins = context.get("consecutive_wins", 0)
        
        score = 1.0
        if last_was_loss and minutes_since_last < 30:
            score -= 0.4  # revenge pattern
        if consecutive_wins >= 3 and sizing_vs_avg > 1.3:
            score -= 0.3  # overconfidence
        if context.get("entry_at_day_extreme", False):
            score -= 0.2  # FOMO
        
        return max(0.0, score)

class SignalConfidenceFactor(FactorComputer):
    """Index 6. Meta-factor: how reliable are the trader's
    tagged signals for THIS category? Uses DK weights accumulated
    from verified trades. High = signals predict well for this
    setup type. Low = signals are noise for this category.
    """
    def compute(self, entity_id, context) -> float:
        category = context.get("category_index", 0)
        dk_weights = context.get("dk_weights_by_category", {})
        weights = dk_weights.get(category, [])
        if not weights:
            return 0.5  # no data yet
        # Average DK weight for signals tagged on this trade
        tagged = context.get("tagged_signal_indices", [])
        if not tagged:
            return 0.5
        relevant = [weights[i] for i in tagged if i < len(weights)]
        return float(np.mean(relevant)) if relevant else 0.5
```

### 10.3 Context Schema

The `context` dict passed to all factor computers has this schema.
Built by the trade ingestion pipeline from NormalizedTrade + market
data + historical patterns.

```python
@dataclass
class TradeContext:
    """Context assembled for each trade before factor computation."""
    
    # Identity
    trade_id: str
    ticker: str
    category_index: int           # auto-classified or manual
    
    # Signal alignment (factor 0)
    tagged_signals: list[dict]     # [{"name": "rsi_14", "confirmed": True}, ...]
    tagged_signal_indices: list[int]  # indices into indicator registry
    
    # Market regime (factor 1)
    current_regime: str            # "trending", "ranging", "volatile"
    regime_accuracy: dict          # {"trending": 0.67, "ranging": 0.44, ...}
    vix_at_entry: float
    
    # Position sizing (factor 2)
    position_size_pct: float       # % of account
    avg_position_size_pct: float   # rolling 50-trade average
    max_position_size_pct: float   # from trader config (default 5%)
    
    # Timing quality (factor 3)
    entry_delay_minutes: float     # 0 if no plan
    hold_time_vs_plan_pct: float   # 1.0 if no plan
    time_of_day_accuracy: Optional[float]  # from pattern detector
    
    # Risk/reward (factor 4)
    planned_risk_reward: Optional[float]  # from trade plan
    actual_risk_reward: float      # (exit - entry) / (entry - stop)
    
    # Emotional/decision context (factor 5)
    minutes_since_last_trade: int
    last_trade_was_loss: bool
    size_vs_rolling_avg: float     # current_size / avg_size
    consecutive_wins: int
    entry_at_day_extreme: bool     # within 1% of day high/low
    
    # Signal confidence (factor 6)
    dk_weights_by_category: dict   # {category_idx: [weight_per_signal]}
```

### 10.4 Regime Classifier

```python
def classify_regime(vix: float, trend_strength: float) -> str:
    """Classify current market regime.
    
    Args:
        vix: Current VIX level
        trend_strength: ADX(14) or equivalent. >25 = trending.
    
    Returns:
        "trending", "ranging", or "volatile"
    
    Thresholds calibrated from SPY 2020-2025 regime analysis:
        VIX < 20 + ADX > 25  → trending
        VIX < 20 + ADX ≤ 25  → ranging
        VIX 20-30            → ranging (elevated uncertainty)
        VIX > 30             → volatile
    
    v1.0: Fixed thresholds (above).
    v1.1: AgentEvolver (F12) tunes regime boundaries per trader
    based on verified outcomes in each regime. Some traders thrive
    at VIX 25 — conditions that are "ranging" by these defaults but
    "trending" by their experience. The system will learn this.
    """
    if vix > 30:
        return "volatile"
    if vix > 20:
        return "ranging"
    if trend_strength > 25:
        return "trending"
    return "ranging"
```

### 10.5 Initial Centroids (μ₀)

20 cells (5 categories × 4 actions). Key cells specified. Generate
remaining from domain heuristics in coding session.

**trend_following × strong_execution:**
`[0.90, 0.85, 0.80, 0.85, 0.80, 0.95, 0.80]`
Signals confirmed, good regime, right size, good timing, R:R
close to plan, no emotional flags, signals predict well.

**trend_following × poor_execution:**
`[0.40, 0.85, 0.50, 0.35, 0.20, 0.40, 0.80]`
Signals may have confirmed (regime was right) but sizing wrong,
timing bad, R:R poor, emotional flags present. Regime is good
but trader executed poorly.

**mean_reversion × strong_execution:**
`[0.85, 0.70, 0.80, 0.80, 0.85, 0.90, 0.75]`
Signals confirmed, regime moderate (mean-reversion less
regime-dependent), proper sizing, good timing, hit R:R target.

**event_driven × skip_recommended:**
`[0.30, 0.30, 0.50, 0.50, 0.50, 0.25, 0.40]`
Signals don't confirm, bad regime for this trader, emotional
flags (FOMO on news), signals historically unreliable for events.

**scalp_intraday × partial_execution:**
`[0.70, 0.60, 0.70, 0.55, 0.60, 0.70, 0.65]`
Most things moderate — scalps are inherently partial because
holding period is so short that timing precision matters more.

**income_strategy × strong_execution:**
`[0.80, 0.75, 0.85, 0.90, 0.75, 0.95, 0.70]`
Income strategies (options selling) value position sizing and
emotional discipline highly. Timing less critical (premium
decay is gradual). No emotional flags = strong execution.

*Full 20-cell specification: generate remaining 14 cells using
the pattern: strong_execution has all factors >0.75,
poor_execution has timing/emotional <0.40, skip has signals
<0.35 + emotional <0.30.*

### 10.6 NL Evidence Templates

```python
class TradingTemplateEngine:
    """Deterministic evidence templates for trade decisions."""
    
    TREND_FOLLOWING = (
        "{ticker} {direction}. {signal_summary}. "
        "Regime: {regime} (your accuracy: {regime_acc:.0%}). "
        "{sizing_note}. {timing_note}. "
        "Decision context: {emotional_summary}. "
        "Score: {action} ({confidence:.0%})."
    )
    
    MEAN_REVERSION = (
        "{ticker} {direction}. RSI: {rsi_value:.0f} "
        "({rsi_signal}). {signal_summary}. "
        "Regime: {regime}. "
        "{sizing_note}. {rr_note}. "
        "Score: {action} ({confidence:.0%})."
    )
    
    EVENT_DRIVEN = (
        "{ticker} {direction}. Event: {event_type}. "
        "Your event-driven accuracy: {event_acc:.0%}. "
        "{sizing_note}. {emotional_summary}. "
        "Score: {action} ({confidence:.0%})."
    )
    
    SCALP = (
        "{ticker} {direction}. Hold: {hold_min:.0f} min. "
        "Timing: {timing_quality}. Size: {sizing_note}. "
        "Score: {action} ({confidence:.0%})."
    )
    
    INCOME = (
        "{ticker} {strategy_type}. Premium: ${premium:.2f}. "
        "DTE: {dte}. Delta: {delta:.2f}. "
        "Account risk: {account_risk:.1%}. "
        "{sizing_note}. Score: {action} ({confidence:.0%})."
    )
    
    # Signal trust template (hero)
    TRUST_ANALYSIS = (
        "Signal trust for {category}:\n"
        "  {signal_name}: σ={sigma:.2f}, DK weight {weight:.0%} "
        "({trust_label})\n"
        "  Most trusted: {top_signal} ({top_weight:.0%})\n"
        "  Least trusted: {bottom_signal} ({bottom_weight:.0%})\n"
        "  You take {overused_signal} {overuse_ratio:.1f}× more "
        "often than {underused_signal} — but it performs worse."
    )
    
    # Pattern detection template
    PATTERN_ALERT = (
        "Pattern: {pattern_name}. "
        "Your accuracy when this pattern is present: {pattern_acc:.0%} "
        "(vs {baseline_acc:.0%} baseline). "
        "Estimated annual cost: ${annual_cost:,.0f}. "
        "{recommendation}."
    )
    
    # Conservation template
    CONSERVATION_STATUS = (
        "Strategy: {category}. Status: {status}. "
        "{n_trades} verified trades. Accuracy: {accuracy:.0%}. "
        "{expansion_note}."
    )
```

### 10.7 API Endpoints

| Endpoint | Method | Purpose | Phase |
|---|---|---|---|
| /api/trading/import | POST | Import trades from broker/CSV | v1.0 |
| /api/trading/trades | GET | Trade journal (filtered) | v1.0 |
| /api/trading/trades/{id} | GET | Single trade with factor scores | v1.0 |
| /api/trading/score | POST | Score a trade (or potential trade) | v1.0 |
| /api/trading/trust | GET | Signal trust analysis (DK weights) | v1.0 |
| /api/trading/trust/{category} | GET | Per-category trust breakdown | v1.0 |
| /api/trading/patterns | GET | Detected behavioral patterns | v1.0 |
| /api/trading/conservation | GET | Per-strategy GREEN/AMBER/RED | v1.0 |
| /api/trading/conservation/{cat} | GET | Single strategy detail | v1.0 |
| /api/trading/iks | GET | IKS score and trend | v1.0 |
| /api/trading/regime | GET | Current regime + trader accuracy | v1.0 |
| /api/trading/analytics | GET | P&L by setup/category/regime/period | v1.0 |
| /api/trading/prescore | POST | Pre-trade decision support | v1.1 |
| /api/trading/promotion | GET/POST | Strategy promotion pipeline | v1.1 |
| /api/trading/evolution | GET | AgentEvolver history | v1.1 |
| /api/trading/export | GET | Full data export (CSV/JSON) | v1.0 |
| /api/trading/backup | POST | Backup centroids + weights | v1.0 |
| /api/trading/restore | POST | Restore from backup | v1.0 |

### 10.3 CLI Design

```bash
# Install
pip install ci-trading

# First use
ci-trading init                          # creates ~/.ci-trading/
ci-trading connect alpaca --paper        # OAuth flow
ci-trading import --days 365             # import last year

# Daily use
ci-trading dashboard                     # opens local web UI
ci-trading score                         # score today's trades
ci-trading trust                         # show signal trust analysis
ci-trading patterns                      # show detected patterns
ci-trading conservation                  # show strategy safety

# Advanced
ci-trading export --format csv           # export all data
ci-trading backup                        # backup centroids + weights
ci-trading restore --from backup.json    # restore profile
```

---

## §11 — Value Model

### Individual Trader ($50K account)

| Scenario | Annual cost of the problem | System prevents | Net value |
|---|---|---|---|
| T1: Wrong setup preference | $3,600 (overtrades bad setup) | Redirect to proven setup | $2,000-3,000 |
| T2: Post-win overtrading | $2,800 | Cap post-streak sizing | $1,500-2,500 |
| T3: Time-of-day weakness | $1,200/month × 12 | Reduce/stop bad windows | $8,000-12,000 |
| T7: Revenge trades | $4,200 | Real-time warning | $2,500-3,500 |
| T6: Execution gap | Variable | Quantify and improve | $2,000-5,000 |
| **TOTAL** | | | **$16,000-26,000** |

At $0/month (OSS, self-hosted): infinite ROI.
At $50/month (cloud, $600/year): ROI = 27-43×.

### Prop Desk ($2M capital, 3 traders)

| Scenario | Annual cost | System prevents | Net value |
|---|---|---|---|
| T8: Per-trader edge identification | $50-100K (suboptimal mandates) | Right trader × right strategy | $30-60K |
| T12: Trader departure knowledge loss | $80-200K (ramp time) | IKS transfer | $40-100K |
| T9: Dead strategy detection | $20-50K (continued allocation) | Conservation AMBER | $15-35K |
| **TOTAL** | | | **$85-195K** |

At $5,000/month ($60K/year): ROI = 1.4-3.3×. At $2,000/month ($24K/year): ROI = 3.5-8×.

---

## §12 — Coding Sequence

### Phase 0: Proof of Concept (~2 weeks)

| Step | What | Days | Prereq |
|---|---|---|---|
| 0.1 | TradingDomainConfig (§10.1) | 1 | None |
| 0.2 | Alpaca connector (import trades) | 2 | 0.1 |
| 0.3 | yfinance market data integration | 1 | 0.1 |
| 0.4 | pandas-ta signal factor computers (3 of 7) | 2 | 0.1 |
| 0.5 | CLI: init + import + score + trust | 2 | 0.2-0.4 |
| 0.6 | Signal trust radar (F2, web UI) | 3 | 0.4 |

### Phase 1: Full v1.0 (~6 weeks)

| Step | What | Weeks | Prereq |
|---|---|---|---|
| 1.1 | Remaining 4 factor computers | 1 | Phase 0 |
| 1.2 | Pattern detector (F4) | 1 | Phase 0 |
| 1.3 | Conservation dashboard (F5) | 0.5 | 0.1 |
| 1.4 | Trade journal view (F7) | 0.5 | Phase 0 |
| 1.5 | IKS tracker (F6) | 0.5 | 0.1 |
| 1.6 | IBKR connector | 0.5 | 0.2 |
| 1.7 | CSV import (universal fallback) | 0.5 | 0.1 |
| 1.8 | Full CLI (F8) | 0.5 | 1.1-1.5 |
| 1.9 | PyPI package (`pip install ci-trading`) | 0.5 | 1.8 |

### Phase 1.1: Decision Support (~4 weeks)

| Step | What | Weeks | Prereq |
|---|---|---|---|
| 1.1.1 | Regime classifier (F10) | 1 | Phase 1 |
| 1.1.2 | Real-time pre-trade scoring (F9) | 2 | 1.1.1 |
| 1.1.3 | Strategy promotion engine (F11) | 1 | Phase 1 |
| 1.1.4 | AgentEvolver trading (F12) | 2 | Phase 1 |

**First coding action: TradingDomainConfig (0.1). 1 day.**

---

## §13 — Open Questions

1. **Verification model:** Trading outcomes are continuous (P&L),
   not binary (correct/incorrect). How to define "verified" for
   centroid updates? Options: (a) binary win/loss, (b) R-multiple
   thresholds, (c) execution quality score vs plan. Recommend (c)
   for richest signal.
2. **Category assignment:** Auto-categorize by strategy tag (trader
   labels) or by trade characteristics (duration, instrument,
   setup)? Auto-categorization reduces friction; manual tagging
   is more accurate. Recommend: auto-classify with manual override.
3. **Emotional indicator ethics:** Flagging "revenge trade" or
   "FOMO" is sensitive. Frame as data, not judgment: "This trade
   matches a pattern associated with lower outcomes in your
   history." Never use the word "emotional" in the UI.
4. **Options support:** Options have richer factor space (Greeks,
   IV, spread structure). Separate DomainConfig or extended factors?
   Recommend: v1.0 equity-only, v1.1 adds options factors (d=10).
5. **Regulatory:** Is this investment advice? No — it's pattern
   analysis on the trader's OWN data. Like a trade journal with
   statistics. Add disclaimer. Consult counsel before launch.
6. **Community governance — DECIDED:** Fully automated acceptance
   criteria for community factor PRs. All must pass: (a) factor
   returns float [0,1] ✅, (b) computes in <100ms ✅, (c) passes
   3 statistical tests on synthetic data (non-constant output,
   responds to context changes, output distribution in [0,1]) ✅,
   (d) docstring present ✅, (e) type hints pass mypy ✅. If all
   automated checks pass, PR is auto-merged. Human review ONLY
   for factors that modify core protocols, touch security/privacy,
   or introduce new dependencies. Permissionless contribution with
   automated quality gates — like HuggingFace model uploads.

---

## §14 — Why Open Source Makes This the Fastest Copilot to Ship

| Advantage | Impact |
|---|---|
| No data integration | yfinance + Alpaca are free, no contracts needed |
| No enterprise sales | Trader installs it themselves |
| No fixture complexity | Real market data (yfinance), real trades (Alpaca paper) |
| Community factor computers | TA-Lib has 130+ indicators ready to wrap |
| PyPI distribution | `pip install ci-trading` — no Docker, no deploy |
| Self-hosted default | No cloud infrastructure needed for v1.0 |
| GAE already open source | Core engine exists and is tested (1,237 tests) |

**Estimated time from start to `pip install ci-trading`:** ~4 weeks.
The fastest path to a shipped product in the entire copilot portfolio.

---

## APPENDIX A — MAP Queue Items (Screens & Prompts)

### TRD Phase 0: Proof of Concept (~2 weeks)
**Placement: MAP Tier 3 (after Purchasing Phase 0)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| T1 | **TRD-DOMAIN-CONFIG** | TradingDomainConfig: C=5, A=4, d=7, tensor (5,4,7)=140. penalty_ratio=3.0. η_override=0.01. q_window=400. **Migration:** Extends existing (5,3,6) prototype — categories unchanged, actions expand 3→4 (add skip_recommended), factors expand 6→7 (add signal_confidence). Existing 36 tests need tensor shape update (~0.5d within this item). §10.1 copy-paste ready. | 1d | SDK | — | Ready |
| T2 | **TRD-ALPACA-CONNECTOR** | Alpaca trade import. `alpaca-py` SDK. OAuth. Paper + live. Historical import up to 5 years. Normalize to common trade schema. | 2d | SDK | T1 | Ready |
| T3 | **TRD-YFINANCE** | yfinance market data integration. Daily OHLCV for traded tickers. VIX. Auto-pull on import. No API key needed. | 1d | SDK | T1 | Ready |
| T4 | **TRD-SIGNAL-FACTORS** | 3 initial factor computers: signal_alignment (pandas-ta), market_regime (VIX classifier), emotional_indicator (trade spacing/sizing). | 2d | SDK | T1+T3 | Ready |
| T5 | **TRD-CLI-CORE** | CLI: `ci-trading init`, `import`, `score`, `trust`, `conservation`. Click/Typer framework. | 2d | SDK | T2+T4 | Ready |
| T6 | **TRD-TRUST-RADAR** | F2: Signal trust radar chart. Expected vs actual factor importance. The hero screen. **Extends existing Analysis screen** (already has fingerprint + decision explorer). Add radar as new component. React + D3. | 3d | SDK | T4 | Ready |

### TRD Phase 1: Full v1.0 (~6 weeks)
**Placement: MAP Tier 4 (parallel with Purchasing Phase 1)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| T7 | **TRD-REMAINING-FACTORS** | 4 remaining factor computers: position_sizing, timing_quality, risk_reward_actual, signal_confidence. | 1w | SDK | T4 | Ready |
| T8 | **TRD-PATTERN-DETECTOR** | F4: Auto-detect behavioral patterns (overtrading, time-of-day, regime, sizing drift, revenge). Statistical significance + annual cost estimate per pattern. | 1w | SDK | Phase 0 | — |
| T9 | **TRD-CONSERVATION** | F5: Per-strategy GREEN/AMBER/RED. Strategy promotion path: paper→small→full. Sizing freeze on AMBER. | 3d | SDK | T1 | — |
| T10 | **TRD-JOURNAL** | F7: Trade journal view. Chronological log with factor scores, evidence, P&L. Filter by setup/category/regime/date. Query interface. | 3d | SDK | Phase 0 | — |
| T11 | **TRD-IKS** | F6: IKS tracker. Wire to TradingDomainConfig. Per-category breakdown. | 0.5d | SDK | T1 | — |
| T12 | **TRD-IBKR** | Interactive Brokers connector. `ib_insync`. Trade import + historical. | 3d | SDK | T2 | — |
| T13 | **TRD-CSV-IMPORT** | Universal CSV import. Flexible column mapping. Header detection. Supports ThinkOrSwim, Webull, any broker export. | 2d | SDK | T1 | — |
| T14 | **TRD-CLI-FULL** | Full CLI (F8): all commands + `export`, `backup`, `restore`. Man page. | 3d | SDK | T7-T11 | — |
| T15 | **TRD-PYPI** | Package and publish to PyPI. `pip install ci-trading`. README, LICENSE, setup.py. | 2d | SDK | T14 | — |
| T16 | **TRD-EVIDENCE-NL** | NL evidence templates for all 5 categories. "Signal alignment: 0.82 (strong entry). Timing: 0.45 (entered 20 min late). Emotional: 0.30 (revenge pattern)." | 3d | SDK | T7 | — |

### TRD Phase 1.1: Decision Support (~4 weeks)

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| T17 | **TRD-REGIME-CLASSIFIER** | F10: Market regime detection (trending/ranging/volatile). VIX + price action + breadth. Maps to per-regime trader performance. | 1w | SDK | Phase 1 | — |
| T18 | **TRD-REALTIME-SCORE** | F9: Pre-trade decision support. "You're about to take RSI oversold. Your accuracy: 48%. Regime: ranging (your worst). Skip or reduce." | 2w | SDK | T17 | — |
| T19 | **TRD-PROMOTION-ENGINE** | F11: Paper→small→full pipeline. Conservation-gated transitions. State machine with audit trail. | 1w | SDK | T9 | — |
| T20 | **TRD-AGENT-EVOLVER** | F12: Self-tuning alert thresholds, pattern sensitivity, regime boundaries. Conservation-gated promotion. | 2w | SDK | Phase 1 | — |

### TRD Phase 1.2: Volatility Trading (~3 weeks)
**Placement: After Phase 1.1 (requires regime classifier)**

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| T26 | **TRD-REGIME-RECOMMEND** | RegimeRecommender service (§3.5 spec). Per-regime accuracy → allocation shift recommendations. Conservation gate: only recommend increases for GREEN categories. Scenarios T16. | 1w | SDK | T17 | Ready |
| T27 | **TRD-CORRELATION-MONITOR** | CorrelationMonitor service (§3.5 spec). 20-day rolling cross-position correlation. Alert at avg > 0.6. Effective exposure multiplier. Concentrated-position accuracy lookup. Scenario T18. | 1w | SDK | Phase 1 | Ready |
| T28 | **TRD-EARNINGS-SUBCAT** | Earnings subcategory classifier (§3.5 spec). Split event_driven into event_directional vs event_volatility. Per-subcategory accuracy. "You're a volatility trader." Scenario T19. | 3d | SDK | Phase 1 | Ready |
| T29 | **TRD-VIX-TIMING** | VIX entry/hold analysis. Per-hold-period accuracy for VIX trades. "Your 3-day hold: 71%. 1-day: 39%. Wait for confirmation." Scenario T20. | 3d | SDK | T17 | Ready |

### TRD Phase 2.0: Multi-Trader + Network + Options (long-term)

| # | ID | What | Effort | Repo | Dep | Status |
|---|---|---|---|---|---|---|
| T21 | **TRD-MULTI-TRADER** | F13: Multi-trader dashboard. Per-trader profiles. Aggregate desk performance. Edge transfer across traders. | 3w | SDK | Phase 1 | — |
| T22 | **TRD-CROSS-INSIGHTS** | F14: Anonymized cross-trader signal insights. Opt-in network. "RSI works for 23% of swing traders in trending markets." Proprietary tier. | 4w | SDK | T15 | — |
| T23 | **TRD-EXECUTION-ANALYSIS** | F15: Broker fill quality comparison. Slippage analysis. "Switching from Alpaca to IBKR saves $1,200/year on your frequency." | 1w | SDK | Phase 1 | — |
| T24 | **TRD-OPTIONS-FACTORS** | Extended d=10 factor space for options. Greeks, IV/RV ratio, spread structure, theta decay. Enables true IV/RV for T17 (currently VIX proxy). Separate TradingOptionsDomainConfig. | 2w | SDK | Phase 1 | — |
| T25 | **TRD-TRADINGVIEW-HOOK** | TradingView webhook receiver. Capture TV alerts as signal events. Correlate with execution quality. | 1w | SDK | Phase 1 | — |

### Scenario Coverage by Phase

| Phase | Items | Scenarios Covered | Demonstrable |
|---|---|---|---|
| Phase 0 | T1-T6 | T1, T4 (partial) | 2/20 |
| Phase 1 | T7-T16 | +T2, T3, T5, T7, T11, T13-T15 (defense, existing factors) | 10/20 |
| Phase 1.1 | T17-T20 | +T4, T6, T9, T10, T14 (full regime) | 14/20 |
| Phase 1.2 | T26-T29 | +T16, T18, T19, T20 (volatility offense) | 18/20 |
| Phase 2.0 | T21-T25 | +T8, T12, T17 (true IV/RV with options) | 20/20 |

### Critical Path

```
TRD-DOMAIN-CONFIG (T1, 1d) ─── UNBLOCKS EVERYTHING
  │
  ├── TRD-ALPACA (T2, 2d) ──── TRD-IBKR (T12)
  │                              TRD-CSV (T13)
  ├── TRD-YFINANCE (T3, 1d) ─── market data for all factors
  │
  ├── TRD-SIGNAL-FACTORS (T4, 2d) ─── TRD-TRUST-RADAR (T6, 3d)
  │                                    TRD-REMAINING-FACTORS (T7)
  │
  └── TRD-CLI-CORE (T5, 2d) ── TRD-CLI-FULL (T14) ── TRD-PYPI (T15)

  TRD-TRUST-RADAR (T6) = Phase 0 hero screen
  TRD-PYPI (T15) = `pip install ci-trading` moment
```

**Total new MAP items: 25.** First action: T1 (TRD-DOMAIN-CONFIG, 1 day).

---

## APPENDIX B — Design Integrations (Third-Party Ecosystem)

### B.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ci-trading                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ProfileScr│  │DiagKernel│  │Conserv.  │  │AgentEvolve│  │
│  │(GAE)     │  │(GAE)     │  │(GAE)     │  │(SDK)      │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│         ▲            ▲            ▲              ▲         │
│         │            │            │              │         │
│  ┌──────┴────────────┴────────────┴──────────────┴──────┐  │
│  │              Factor Computer Layer                    │  │
│  │  signal_alignment │ market_regime │ emotional_ind.   │  │
│  │  position_sizing  │ timing        │ risk_reward      │  │
│  │  signal_confidence│ [community]   │ [community]      │  │
│  └──────┬────────────┬────────────┬──────────────┬──────┘  │
│         │            │            │              │         │
└─────────┼────────────┼────────────┼──────────────┼─────────┘
          │            │            │              │
   ┌──────┴──┐  ┌──────┴──┐  ┌─────┴───┐  ┌──────┴──────┐
   │ Brokers │  │ Market  │  │ Tech    │  │ Community   │
   │         │  │ Data    │  │ Indic.  │  │ Factors     │
   └─────────┘  └─────────┘  └─────────┘  └─────────────┘
```

### B.2 Broker Integrations

| Broker | Library | Auth | Data Available | Effort | Priority |
|---|---|---|---|---|---|
| **Alpaca** | `alpaca-py` | OAuth 2.0 | Trades, positions, account, orders. Paper + live. REST + WebSocket. | 2d | **P0** |
| **Interactive Brokers** | `ib_insync` | TWS/Gateway | Trades, positions, executions, historical. Most feature-rich API. | 3d | **P1** |
| **Tradier** | REST API | OAuth | Trades, positions, options chains. Simple API. | 1d | P2 |
| **TD Ameritrade / Schwab** | CSV export only | N/A | Export → CSV → our import. No live API for retail. | 0.5d | P2 |
| **Webull** | Limited REST | OAuth | Basic trade data. Limited history. | 1d | P3 |
| **Robinhood** | Unofficial only | — | No official API. CSV export workaround. | 0.5d | P3 |

**Trade schema (normalized across all brokers):**

```python
@dataclass
class NormalizedTrade:
    trade_id: str               # unique across brokers
    broker: str                 # "alpaca", "ibkr", "csv"
    ticker: str                 # normalized symbol
    direction: str              # "long" or "short"
    entry_price: float
    exit_price: Optional[float] # None if position open
    size: float                 # shares or contracts
    entry_time: datetime
    exit_time: Optional[datetime]
    strategy_tag: Optional[str] # user-assigned setup label
    asset_type: str             # "equity", "option", "future"
    fees: float                 # commissions + fees
    pnl: Optional[float]       # realized P&L
    notes: Optional[str]       # free-text trade notes
```

### B.3 Market Data Integrations

| Source | Library | Data | Cost | Update | Effort |
|---|---|---|---|---|---|
| **yfinance** | `yfinance` | OHLCV (any ticker), splits, dividends | Free | Daily/real-time | 1d |
| **FRED** | `fredapi` | VIX, rates, PPI, employment, yield curve | Free (API key) | Daily-monthly | 0.5d |
| **Alpha Vantage** | `alpha_vantage` | OHLCV + technicals + fundamentals | Free tier (5/min) | Real-time | 1d |
| **Polygon.io** | `polygon` | Tick-level, options, crypto | $29/month | Real-time | 2d |
| **Quandl/Nasdaq** | `quandl` | Commodity indices, macro, alternatives | Free tier | Daily | 0.5d |

**v1.0 uses yfinance only (free, no key, sufficient for daily data).**
Real-time feeds (Polygon, Alpha Vantage) add in v1.1 for pre-trade scoring.

### B.4 Technical Indicator Engine

| Library | Indicators | License | Integration |
|---|---|---|---|
| **pandas-ta** | 130+ (RSI, MACD, BB, ATR, VWAP, etc.) | MIT | `import pandas_ta as ta; df.ta.rsi()` |
| **TA-Lib** (C library) | 200+ | BSD | Faster but requires C compilation |
| **finta** | 80+ | LGPL | Pure Python alternative |

**Design: pandas-ta is default (pure Python, pip-installable).
TA-Lib as optional accelerator for high-frequency users.**

Each indicator becomes a potential factor computer input:

```python
# Factor computer consults trader's tagged signals
# and computes alignment score

INDICATOR_REGISTRY = {
    "rsi_14": lambda df: ta.rsi(df.close, length=14),
    "macd_12_26_9": lambda df: ta.macd(df.close)["MACD_12_26_9"],
    "bbands_20_2": lambda df: ta.bbands(df.close, length=20, std=2),
    "atr_14": lambda df: ta.atr(df.high, df.low, df.close, length=14),
    "vwap": lambda df: ta.vwap(df.high, df.low, df.close, df.volume),
    "sma_50": lambda df: ta.sma(df.close, length=50),
    "ema_21": lambda df: ta.ema(df.close, length=21),
    "volume_ratio": lambda df: df.volume / df.volume.rolling(20).mean(),
    # Community can add any indicator via PR
}
```

### B.5 Signal Capture Integrations

| Source | Method | Data | Priority |
|---|---|---|---|
| **TradingView webhooks** | HTTP webhook endpoint | Alert signals (ticker, direction, indicator, timeframe) | P2 |
| **Discord/Telegram bots** | Bot API | Signal channel messages (parsed) | P3 |
| **Manual signal log** | CLI/UI | Trader tags which signals drove each entry | P0 (built-in) |

**The key insight:** We don't GENERATE signals. We EVALUATE which
signals the trader already uses actually predict their outcomes.
Signal capture is about RECORDING what the trader saw at entry,
not about computing signals ourselves (pandas-ta does that for
the evaluation layer).

### B.6 Export/Interop Integrations

| Target | Format | Purpose |
|---|---|---|
| **CSV export** | Standard CSV | Portfolio analysis tools, tax software |
| **JSON API** | REST | Custom dashboards, external tools |
| **Quantconnect LEAN** | LEAN format | Import factor scores into backtests |
| **Jupyter notebooks** | pandas DataFrames | Advanced analysis by quantitative traders |

---

## APPENDIX C — Design Details

### C.1 Verification Model for Trading

Trading outcomes are CONTINUOUS (P&L), unlike SOC/Purchasing
(binary correct/incorrect). The centroid update model needs
adaptation.

**Decision: Multi-signal verification.**

Each trade produces THREE verification signals:

| Signal | Type | How computed | Weight |
|---|---|---|---|
| **Outcome** | Binary | Win (P&L > 0) or loss (P&L ≤ 0) | 0.3 |
| **R-multiple** | Continuous | P&L / initial_risk. R ≥ 1.0 = good. | 0.3 |
| **Execution quality** | Continuous | Composite of: entry vs plan, exit vs plan, hold time vs plan, size vs plan. Range [0,1]. | 0.4 |

Execution quality gets the highest weight because it measures
the DECISION, not the MARKET OUTCOME. A well-executed losing
trade is more informative than a poorly-executed winning trade.

```python
def compute_verification_score(trade: NormalizedTrade,
                                plan: TradePlan) -> float:
    """Returns [0, 1] verification score for centroid update."""
    
    outcome = 1.0 if trade.pnl > 0 else 0.0
    
    r_mult = min(trade.pnl / plan.initial_risk, 2.0) / 2.0
    r_score = max(0.0, (r_mult + 1.0) / 2.0)  # normalize to [0,1]
    
    entry_quality = 1.0 - min(
        abs(trade.entry_price - plan.planned_entry) / plan.planned_entry, 0.1) * 10
    exit_quality = 1.0 - min(
        abs(trade.exit_price - plan.planned_exit) / plan.planned_exit, 0.1) * 10
    hold_quality = 1.0 - min(
        abs(trade.hold_minutes - plan.planned_hold_minutes) / plan.planned_hold_minutes, 1.0)
    size_quality = 1.0 - min(
        abs(trade.size - plan.planned_size) / plan.planned_size, 0.5) * 2
    
    execution = 0.25 * (entry_quality + exit_quality + hold_quality + size_quality)
    
    return 0.3 * outcome + 0.3 * r_score + 0.4 * execution
```

**TradePlan is optional.** If the trader doesn't log a plan,
execution quality defaults to 0.5 (neutral) and the system
learns from outcome + R-multiple only. Logging plans unlocks
the richest signal — incentive to use the system fully.

**skip_recommended verification.** When the system recommends
skipping a trade and the trader follows the recommendation,
there's no trade outcome to verify. The system tracks the
HYPOTHETICAL outcome using market data (yfinance):

```python
def verify_skip(skip_event: SkipEvent) -> float:
    """Verify a skip_recommended decision using what WOULD
    have happened if the trade was taken.
    
    Uses yfinance to compute hypothetical P&L based on the
    planned entry, stop, and target from the trade setup.
    """
    planned = skip_event.planned_trade
    market_data = yfinance_fetch(planned.ticker,
                                 planned.entry_time,
                                 planned.entry_time + planned.hold_duration)
    
    # Would the entry have triggered?
    if not would_have_filled(market_data, planned.entry_price):
        return 0.5  # entry never triggered — skip is neutral
    
    # Compute hypothetical outcome
    hypo_exit = simulate_exit(market_data, planned.stop, planned.target)
    hypo_pnl = (hypo_exit - planned.entry_price) * planned.size
    
    # Skip was correct if hypothetical P&L was negative
    if hypo_pnl < 0:
        return 1.0  # "You skipped this. It would have lost $340. Correct."
    else:
        return 0.0  # "You skipped this. It would have made $220. Missed opportunity."
```

"You skipped this RSI trade. SPY moved -2.3% in the next 4 hours.
Your planned entry would have hit the stop at -$340. Skip was
correct." This turns every skip into a verified learning signal.
Without hypothetical tracking, skip_recommended trades are a dead
zone in centroid geometry.

### C.2 Category Assignment

**Auto-classification with manual override:**

```python
def classify_trade(trade: NormalizedTrade, 
                   indicators: dict) -> int:
    """Auto-assign category from trade characteristics."""
    
    hold_minutes = (trade.exit_time - trade.entry_time).total_seconds() / 60
    
    # Scalp/intraday: < 60 min hold
    if hold_minutes < 60:
        return 4  # scalp_intraday
    
    # Event-driven: entry within 2 hours of earnings/news
    if trade.notes and any(k in trade.notes.lower() 
                           for k in ["earnings", "news", "catalyst", "event"]):
        return 2  # event_driven
    
    # Income strategy: options selling, covered calls, credit spreads
    if trade.asset_type == "option" and trade.direction == "short":
        return 3  # income_strategy
    
    # Mean reversion: entry against recent trend (RSI oversold/overbought)
    rsi = indicators.get("rsi_14_at_entry", 50)
    if rsi < 30 and trade.direction == "long":
        return 1  # mean_reversion
    if rsi > 70 and trade.direction == "short":
        return 1  # mean_reversion
    
    # Default: trend following
    return 0  # trend_following
```

Trader can override: `ci-trading retag TRD-1847 --category mean_reversion`

### C.3 Emotional Indicator Design

Sensitive feature. Three design rules:

1. **Frame as data, never judgment.** "This trade matches a pattern
   associated with 34% win rate in your history" — NOT "This is an
   emotional trade."
2. **User controls the label.** The factor is `emotional_indicator`
   internally but displayed as "Decision Context" in the UI.
3. **Opt-out available.** `ci-trading config --disable-pattern-detection`
   turns off behavioral pattern detection entirely.

**Detection heuristics (all computed from trade data, no self-report):**

| Pattern | Detection rule | Label in UI |
|---|---|---|
| Revenge | Trade within 30 min of a loss, same direction | "Quick re-entry after loss" |
| Overconfidence | Size > 1.3× rolling avg after 3+ wins | "Elevated sizing after winning streak" |
| FOMO | Entry at day's high/low | "Entry at daily extreme" |
| Tilt | 3+ trades in 1 hour (vs avg 1-2/day) | "Elevated trade frequency" |
| Drawdown chase | Increasing size during drawdown period | "Size increase during drawdown" |

### C.4 Conservation Law Adaptation for Trading

The conservation law α·q·V ≥ θ_min applies but with trading-specific
semantics:

| Parameter | SOC/Purchasing | Trading |
|---|---|---|
| α | Fraction auto-approved | Fraction of capital in auto-sized positions |
| q | Rolling verified accuracy | Rolling execution quality score (§C.1) |
| V | Decision volume | Number of trades in q_window |
| θ_min | 23.53/(α×V) | Same formula — domain-agnostic |

**What conservation governs in trading:**
- Auto-sizing: can the system automatically set position size? (α)
- Strategy promotion: can a strategy move from paper to live? (q gate)
- Sizing expansion: can a strategy increase from 2% to 4% of capital? (q gate)

**AMBER triggers:**
- Execution quality drops below threshold for 20+ consecutive trades
- Strategy accuracy drops below category baseline by 10pp
- New trader's pattern diverges from established (T9 scenario)

### C.5 Data Storage Architecture (Self-Hosted)

```
~/.ci-trading/
├── config.yaml              # broker connections, preferences
├── centroids.json           # 140 centroid values (portable)
├── dk_weights.json          # 175 DK precision weights (portable)
├── trades.db                # SQLite: all normalized trades
├── indicators.db            # SQLite: cached indicator values
├── patterns.json            # detected behavioral patterns
├── conservation_state.json  # per-strategy GREEN/AMBER/RED
├── evolution_log.json       # AgentEvolver history
├── backup/
│   └── 2026-05-20.json      # full state backup (portable)
└── community_factors/
    └── vwap_deviation.py    # user-installed community factors
```

**Everything is local.** No cloud dependency. No telemetry.
Backups are JSON files the trader can move to another machine.
`ci-trading backup` → `ci-trading restore --from backup.json`.

---

## APPENDIX D — Top-Down & Bottom-Up Scenario Analysis

### D.1 Top-Down: Market-Driven Scenarios

**Sources:** Behavioral finance research (Kahneman, Thaler, Odean),
trade journal user reviews (Tradervue G2, Edgewonk forums),
retail trading surveys (FINRA 2025, Schwab 2026).

**Tier 1 — Universal (every active trader has these):**

| Pain Point | Frequency | Tools solve? | Our architecture? |
|---|---|---|---|
| **Don't know which setups actually work** | 90%+ | Journal shows P&L by tag (after the fact) | Per-signal DK weights from verified outcomes (predictive) |
| **Overtrade in bad conditions** | 80%+ | No tool detects this | Time/regime/emotional pattern detection |
| **Can't scale without more risk** | 75%+ | Backtest only (not YOUR execution) | Conservation law on YOUR trade data |
| **Knowledge is in my head, not a system** | 70%+ | Journal records events, not patterns | Centroid geometry + DK weights encode patterns |
| **Revenge/emotional trading** | 65%+ | Self-reported tags (unreliable) | Auto-detected from trade spacing/sizing |
| **Backtest ≠ live performance** | 60%+ | No tool quantifies the execution gap | Planned vs actual comparison per trade |

**Tier 2 — Common (40-60%):**

| Pain Point | Frequency | Our architecture? |
|---|---|---|
| **Strategy stopped working, didn't notice** | 55% | Conservation AMBER + regime attribution |
| **Can't transfer knowledge to a partner/team** | 40% | IKS + centroid export + multi-trader |
| **Data split across brokers/platforms** | 40% | Unified import + common schema |
| **Don't know my regime strengths** | 35% | Regime classifier + per-regime accuracy |

**Table-stakes scenarios (must have even though they aren't innovations):**

**M1: "I Need a Decent Trade Journal"**
Every trader journals. Most use spreadsheets. Tradervue costs
$50/month. We need a solid journal view (F7) that matches or
exceeds Tradervue just to be taken seriously. The journal is the
"open the app daily" feature. Without it, signal trust analysis
has no context.

**M2: "Show Me My P&L by Setup"**
Basic analytics: P&L by strategy tag, by ticker, by time period,
by direction. Tradervue does this well. We must match it. The
INSIGHT layer (DK weights, patterns, conservation) sits ON TOP
of basic analytics.

### D.2 Bottom-Up: Innovation-Driven Scenarios

**From Signal-Confidence Inversion (the hero):**

**I1: "The Signal Trust Trap"**
Your RSI oversold + MACD cross is your go-to. DK weight: 12%
(noisy). Volume breakout + trend confirmation: DK weight: 94%
(reliable). You take the RSI trade 3× more often.

No trading tool computes per-signal, outcome-conditioned variance
for INDIVIDUAL traders. This is genuinely novel. The closest
analog is factor-model attribution in quantitative finance — but
those are computed on PORTFOLIO returns, not on INDIVIDUAL
DECISION QUALITY.

**I2: "Your Strength Has a Regime"**
You're a trending-market specialist. Ranging markets: negative
expectancy. You don't know this because your journal doesn't
separate by regime. System discovers it from 300+ trades cross-
referenced with VIX/regime classification.

**From Conservation Law:**

**I3: "Mathematical Proof of Strategy Safety"**
"Can I go from $20K to $50K on this strategy?" Backtest says
yes. But backtest uses perfect entries. Your entries have $0.37
average slippage, 40% of exits are early. Conservation law on
YOUR execution data: "Safe to $35K. Insufficient history at
$50K. Paper-trade 30 more."

No trading tool provides mathematical scaling proofs based on
the trader's own execution quality.

**I4: "The Strategy That Died — Caught Early"**
Put credit spreads profitable for 18 months. Returns went
negative 6 weeks ago. Conservation AMBER fires with regime
attribution: "Regime changed from trending to ranging.
Your put spread accuracy is regime-dependent. Sizing frozen."

**From Judgment Memory:**

**I5: "1,000 Trades, Encoded"**
After 1,000 verified trades, 315 geometric values encode:
which signals predict your outcomes (DK weights), what your
edge looks like per category (centroids), how consistent you
are (conservation history), what patterns degrade your
performance (behavioral profiles). This is judgment memory
for trading — the fourth cognitive type applied to an
individual's decision quality.

**I6: "The Trader Who Left — Her Edge Preserved"**
Marcus's Trader A leaves. 8,000 trades compiled into centroid
geometry. The replacement starts with Trader A's signal trust
profile, per-regime accuracy, execution benchmarks. Not a
document. A mathematical encoding of what made her profitable.

**From Process-Tech Fusion:**

**I7: "The Execution Gap Quantified"**
Backtest Sharpe: 2.1. Live Sharpe: 0.4. Where's the gap?
"Entry slippage: -$0.37 avg. Early exits: 40% of trades.
Holding to plan: Sharpe would be 1.6. Your execution is the
bottleneck, not the strategy." Process (execution quality) ×
Tech (factor scoring) = actionable insight.

**From AgentEvolver:**

**I8: "The Alert System That Tuned Itself"**
Revenge trade detection window started at 30 min. After 200
verified post-loss trades, AgentEvolver adjusted to 45 min
(better matches YOUR recovery time). Alert threshold for
sizing anomaly: started at 1.3× avg, tuned to 1.5× (your
normal sizing variance is higher than average).

### D.3 Overlap Analysis: Trading vs Other Copilots

| Scenario | In other copilots? | Why different for trading? |
|---|---|---|
| I1 Signal trust trap | Purchasing I1 | Same SCI mechanism but applied to TECHNICAL INDICATORS, not supplier data. Per-INDICATOR weights. |
| I2 Regime-dependent edge | DataOps (process regime) | Similar concept but trading regimes are MARKET-driven (VIX), not PROCESS-driven (bottleneck). |
| I3 Strategy scaling proof | Purchasing P3 (auto-approve) | Same conservation law but governs CAPITAL ALLOCATION, not approval thresholds. |
| I5 1,000 trades encoded | All (IKS) | Same IKS but the FACTORS are personal behavioral indicators, not organizational data quality. |
| I7 Execution gap | No equivalent | UNIQUE to trading. The gap between backtest and live is a trading-specific phenomenon. |
| I8 Self-tuning alerts | All (AgentEvolver) | Same mechanism. Different variant dimensions (trade spacing, sizing thresholds). |

**3 truly unique:** I2 (regime-dependent edge), I7 (execution gap
quantification), and the overall framing of factors as PERSONAL
BEHAVIORAL indicators rather than organizational data quality.

---

## APPENDIX E — Competitive Positioning (Detailed)

### E.1 Direct Competitors

**Tradervue** ($30-50/month, SaaS)
- Strengths: Clean UI. Good P&L analytics. Tag-based filtering.
  Community sharing. MFE/MAE analysis.
- Weaknesses: Static analysis only. No learning. No signal trust.
  No pattern detection. No conservation law. No self-tuning.
  Cloud-only (data leaves your machine).
- Our advantage: Everything Tradervue does (journal + analytics) +
  signal trust + pattern detection + conservation + learning.
  Open source. Self-hosted.

**Edgewonk** ($170 one-time, desktop)
- Strengths: Desktop app (local data). Custom analytics.
  Psychology-aware (tilt meter). Trade plan templates.
- Weaknesses: No per-signal trust analysis. No auto-pattern
  detection (manual tagging only). No conservation law. No
  learning from outcomes. No community factor ecosystem.
  Desktop-only (no CLI, no API).
- Our advantage: Auto-detection vs manual tagging. DK weights
  vs static analytics. Open source vs proprietary. CLI + API.

**QuantConnect LEAN** (free OSS + cloud tiers)
- Strengths: Full algorithmic trading engine. Backtesting +
  live trading. Open source. Large community. Multi-asset.
- Weaknesses: Designed for ALGORITHMIC traders, not discretionary.
  No decision quality analysis. No behavioral pattern detection.
  No conservation law for manual trading. No signal trust for
  human signals.
- Our advantage: We evaluate the TRADER's decision quality.
  LEAN evaluates the ALGORITHM's performance. Complementary,
  not competitive — LEAN users can import our factor scores
  into their backtests.

**TradingView** ($15-60/month, web)
- Strengths: Best charting platform. Massive community. Pine
  Script for custom indicators. Social trading. Alerts.
- Weaknesses: Shows the MARKET. Doesn't show the TRADER to the
  trader. No decision quality analysis. No outcome tracking.
  No learning.
- Our advantage: We sit ON TOP of TradingView. Trader uses TV
  for analysis → executes via broker → we evaluate the decision.
  TV webhook integration captures which TV signals drove the entry.

### E.2 Competitive Matrix

```
                    Records  Analyzes  Learns  Proves   Open
                    Trades   Quality   Signal  Safety   Source
                                      Trust

Tradervue           ✅       ⚠️ basic   ❌      ❌       ❌
Edgewonk            ✅       ⚠️ manual  ❌      ❌       ❌
QuantConnect LEAN   ✅ algo  ✅ algo    ❌      ❌       ✅
TradingView         ❌       ❌        ❌      ❌       ❌
ci-trading          ✅       ✅ auto    ✅      ✅       ✅
```

### E.3 Positioning Statements

**For retail swing traders (Alex):**
"Tradervue shows your P&L. We show you WHY — which signals you
overtrust, which conditions degrade your judgment, and when a
strategy is safe to scale. Open source. Your data stays on your
machine."

**For semi-pro traders (Priya):**
"Edgewonk records your psychology. We measure it from the data,
automatically. After 500 trades, the system knows your regime
strengths, your execution gaps, and mathematically which strategies
can handle more capital."

**For prop desk managers (Marcus):**
"Each trader's edge, quantified. Which signals Trader A should
trust. Which setups Trader B should avoid. When Trader C's
strategy stops working. All from verified trades, not self-reports.
Transfer knowledge when traders leave."

**For the open-source community:**
"Every factor computer is a contribution. pandas-ta has 130+
indicators. Each one becomes a testable hypothesis: does THIS
indicator predict MY outcomes? Community builds the factor library.
DiagonalKernel evaluates it personally for each trader."

### E.4 Why Competitors Can't Replicate

1. **ProfileScorer + DiagonalKernel** — the per-signal trust
   analysis requires the GAE scoring architecture. Building this
   from scratch is 18+ months of math + engineering. GAE has
   1,237 tests and 175+ experiments validating it.
2. **Conservation law** — the mathematical proof of strategy
   safety. Novel. Published (arxiv). Not an incremental feature.
3. **The three-channel improvement** — one verified trade
   simultaneously improves scoring (centroid), discovery (graph),
   and data quality (DK weights). This is architectural.
4. **Community factor ecosystem** — once 100+ traders contribute
   factor computers, the library IS the moat. Network effect.

---

*Trading Copilot Product Definition v1.0 · May 20, 2026*
*20 scenarios. 7 clusters. 15+ features. $16-26K/year (calm) ·*
*$64-130K/year (volatile). Open source. Apache 2.0.*
*Tensor: 5×4×7 = 140 centroids + 175 DK weights = 315 values.*
*3 trader personas. 9 integrations (all open source/free).*
*License: Apache 2.0 (core). Cloud + Pro tiers for revenue.*
*25 MAP items (T1-T25). 5 appendices.*
*Top-down: 10 market scenarios. Bottom-up: 8 innovation scenarios.*
*3 unique: regime edge, execution gap, personal behavioral factors.*
*Competitive: Tradervue records. We reveal. QuantConnect backtests.*
*We evaluate. TradingView shows markets. We show you to yourself.*
*Hero line: "My favorite setup is my worst setup."*
*First coding action: TRD-DOMAIN-CONFIG. `pip install ci-trading` ~4 weeks.*
