# Demo Scenarios Doc — Trading Additions (v1)
*Additions/edits to `demo_scenarios_and_usecases_v2_5.md` (fileId 1bhVPHleQAlj7-5-QO22WUHt8CZENkwrZ).*
**Scoping note — read first:** the demo doc is **already well-evolved on trading** and I'm not duplicating it. It already: leads room 3 with **TRD-S3 autonomy throttle** (§0.1/§4.6), ships the vol beats **TRD-V1/V2/V5/V7** (§4.6, incl. clustering-adjusted Sharpe, VRP, effective-bets-in-a-tail = the B4/B7/B5/B6 math), folds **T17→TRD-V5** and **T18→TRD-V7**, and carries **TRD-S7 re-convergence** (§4.7) as labeled ARCH. These additions are only the **genuinely-missing** pieces from the GPT+Gemini consolidation. **Nothing is cut** (gate/reframe, never delete).

---

## D1. NEW hero moment — "The Claim Gate" (the selection-adjusted evidence gate). *Add as §4.12.*
The single biggest missing beat. The demo has the **Rejection Moment (DM-1)** — the AE rejects self-improvement *variants*. It does **not** have the gate applied to **claims/insights**: the mirror refusing to show a *finding* that doesn't survive multiple-comparisons correction. These are distinct and both belong.
- **The beat:** the mirror ran ~25 detectors on this trader; before any "expensive truth" reaches the screen it passes a **selection-adjusted evidence gate** — Benjamini–Hochberg FDR across all detectors that fired, deflated Sharpe on any per-slice Sharpe, **discovered on the older 70% of history, confirmed on the held-out recent 30%.** On-screen badge: *"23 patterns tested · 3 had power to conclude · 1 survived correction."*
- **The line (room 5 / decision-intelligence kill-shot upgrade):** *"Every journal will find you a 'favorite setup is your worst.' Ours tells you whether that finding survives the fact that we tested twenty-three of them. The gate is the product."*
- **Why it's the point:** it's **the conservation law applied to claims instead of autonomy** — the same thesis, a new surface; and it's the business-model moat (an engagement-monetized tool won't suppress its own daily insight). Class **NEAR** (the FDR/deflated-Sharpe/split are analytics over the tagged decisions already required in §5). Surface: Trading **Analysis** (beside the Trust Radar) + a badge on **Performance**.

## D2. Gate the T1 cold-mirror hero so it survives the teardown. *Edit V1/TR2 (§2.1/§2.4), §3 T1, §0.1 room 5.*
T1 ("your favorite setup is your worst") is the LIVE hero — and it's the exact false-discovery shape a skeptical quant attacks (≈25 detectors × few-hundred trades → 1–2 fake truths for a leak-free trader). Don't drop it — **gate it** and let the gate become the flex.
- **New V1 caption:** *"Your favorite setup is your worst — and it survived correction."*
- **New V1 spoken (append):** *"…and before you ask if that's a fluke: we tested twenty-three patterns on you, three had the power to conclude anything, and this is the one that held after correction. It's not the loudest number — it's the true one."*
- This turns the strongest teardown against the hero into the hero's proof. Pairs with D1.

## D3. Add TradeZella as the 2026 mirror foil. *Add a row to §0.3 and a note to §0.1 room 5.*
The competitive tear-down lines cover TensorTrade (room 3) and generic "decision intelligence" (room 5) but **not TradeZella + Zella AI** — the 2026 entrant already marketing "not a bot / AI trading partner / memory that compounds / 500+ broker imports." The mirror is now **category-entry, not differentiation.**
- **§0.3 new line — room 5 (when they say "TradeZella already does an AI trading journal"):** *"Good — that proves the category. The difference is what happens when the data's thin: TradeZella always has an insight for you; ours refuses the ones that don't survive correction, and it reduces its own autonomy when the regime breaks. A journal that always talks can't do either."*
- Re-lead room 5 on **the gate (D1) + abstention (TRD-S3)**, with the mirror as the opener, not the moat.

## D4. NEW beat — "The Certificate" (D-null / the clean trader). *Add to §4.6 or beside §4.3 Day-Zero.*
For a disciplined trader with no leak, the mirror returns "you're fine" — honest but unshareable, a real adoption risk. Give it a shareable, honest artifact (an output of the D1 gate):
- **What shows:** *"23 detectors, 1,847 decisions, none survive correction — you're genuinely clean,"* plus an **edge-boundary map** (regime capacity, factor independence in stress, excess-confidence margin — your best-calibrated zone). Class **NEAR** (same gate machinery). This is the honest non-empty mirror; it also demos the product's integrity (it will say "nothing here").

## D5. NEW beat — "The Gate's Dividend" (the offense version of the refusal). *Add to §4.6.*
Pairs with D1/the throttle. *"Over 90 days the gate withheld 22 findings that didn't survive correction; replayed, acting on them would have cost −$18.4K."* Makes the refusal concrete and monetized — the trading analog of the Rejection Moment's "the rejections are the point." Class **NEAR**. ⚠️ magnitude illustrative (§4.6 honesty guard).

## D6. Observation-only tightening (legal). *Edit the §4.6 honesty guard + the TRD-V5 line.*
The §4.6 guard already flags magnitudes as illustrative. **Add one rule to it:** *"No beat states a present-tense market call; every line is a past-tense observation about the trader's own decisions. Never weld a market fact to a personalized claim in one sentence."* Then fix the one line that violates it: **TRD-V5** currently reads *"IV is rich at the 85th pct for this regime…"* — drop the market call, keep only the personalized history: *"in regimes like this one, you've faded rich IV and been wrong 60% of the time (N=..)."* (This mirrors the product-def doc's dominant fix; the demo is 90% clean already.)

## D7. Name the B1–B8 quant substrate + harden TRD-S3's trigger. *Edit §4.6.*
The vol beats already *use* the math; **name the shipped package** once for the quant-room credibility: *"TRD-V1/V2/V7 are computed by the shipped B1–B8 quant library (Yang-Zhang, Hurst, block-bootstrap, basket-variance, stress-tail-dependence, model-free VRP) on the trader's own book — not textbook."* And harden the room-3 kill-shot against the teardown: **TRD-S3's trigger** = a **multi-primitive** regime break (B2 Hurst flip + B6 tail-dependence spike) with an on-screen **block-bootstrap p-value (B4)**, so "θ_min is arbitrary / it's a lagging vol spike" doesn't land.

## D8. Make the T4/T14 → TRD-S1 merge explicit. *Edit §3 Trading catalog.*
§4.6 already states T17→TRD-V5 and T18→TRD-V7. The §3 master catalog still lists T4 (Regime Analysis) and T14 (Regime Shift) as standalone; note they **fold into TRD-S1** (the regime-conditioned mirror) at demo time, so the catalog and §4.6 agree. Nothing removed — T4/T14 remain as catalog-depth; TRD-S1 is the demoed beat.

## D9. Preseed additions the new beats need. *Add rows to §5.*
- A **discover/confirm split** in the trading history (older 70% / held-out recent 30%) — D1/D2 need it.
- **≥1 detector that fires but fails FDR** on the sample trader — D1 (the gate visibly rejecting) and D4 (the certificate) need a real "did not survive" example.
- A **hypotheses-tested counter** ("23 tested / 3 powered / 1 survived") surfaced from the gate — D1/D2/D4 badges read from it.

---
### Extensions — noted here, primary home is the product-def doc
Pre-trade **belief capture** (conviction + planned invalidation at entry — the only real data moat), the signed **".jmt" proof-of-edge artifact**, and **parasitic distribution** (read their TradeZella/Tradervue CSV) are product/roadmap items → they belong in `trading_copilot_product_definition` (see its additions doc). Light demo hooks only: the .jmt is a natural **shareable-artifact** beat for the trader self-serve cut (word-of-mouth), and the BYOD beat (TR1) can note "imports your TradeZella export," not just a broker CSV.
