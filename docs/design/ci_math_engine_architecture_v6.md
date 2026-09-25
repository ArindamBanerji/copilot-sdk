# The CI Math Engine — A Hardened Architecture (v6)

*Not the RGI/CI-VLD architecture. That architecture is the **dynamics** — the fast and slow loops, the
investigation trajectory, compounding over time, AgentEvolver's promote/demote cycle, the five copilots — the
program that runs on this engine. This document is the engine: the **statics** beneath the loops — the objects
it holds, the pure operations it exposes, the invariants that make those operations safe, and the contract by
which every output is certified. The loops decide **when** to score, enrich, gate, or evolve; the engine
defines **what** scoring, enrichment, gating, and calibration ARE, independent of any loop that calls them.
One capability, AgentEvolver, deliberately straddles the line — its proposal-and-gate primitives are engine,
its test-and-promote cycle is architecture — and the document is explicit about both halves.*

---

## 0. The organizing idea — chain of custody

A math engine is **hardened** when every number it emits carries a complete chain of custody:

> **object read → operation applied → invariant that protected it → tier that certifies it.**

Nothing the engine outputs may skip a link. The four layers of this document are the four links:
**State** (objects) · **Operations** (pure transforms) · **Invariants** (what holds by construction) ·
**Certification** (how each output is known to be right). This chain is what makes a tier a **property of the
engine**, settled once per operation, rather than a per-document negotiation.

**One decision, followed end to end.** Keep this example in mind through all four layers.

> *A SOC alert arrives: a privileged service account issued a bulk device-management command. The engine reads
> it as a factor vector `v` (§1: STATE). It applies `score` and gets "escalate," but the margin is thin — the
> decision sits near a boundary (§2: OPERATIONS). So `route` picks the next evidence (the account's recent role
> change), `enrich` folds it in, `score` runs again — now "escalate" is decisive. The decision form never
> changed while this happened, only the evidence did (§3: INVARIANT I1). An analyst later confirms the
> escalation; `update` nudges the "escalate" prototype toward this vector (§2). Because that confirmation is a
> verified human outcome, not the engine's own guess, it was allowed to move the geometry (§3: INVARIANT I5).
> And "escalate" is certified geometry-derived — real as a mechanism, its live magnitude still a pilot
> measurement (§4: CERTIFICATION).*

That single alert touches every object, three operations, two invariants, and one certification tier. A
hardened engine is one where you can always draw that chain.

The property that earns *hardened* above all is the **write-partition**: every object names who may write it;
no operation writes outside its lane. That partition — a construction, not a policy — lets the loops learn
aggressively while the decision procedure stays fixed.

---

## 1. STATE — the objects the engine holds

The engine's memory is a small, typed, inspectable set of objects. It divides cleanly into **evolving state**
(what the engine *learns* — changes with use) and **configured parameters** (what the engine *is set up with*
— fixed at approval or recalibration). A risk owner's first question — *what changes after I approve this?* —
is answered by the lifecycle column: only μ, K, σ, R, G move; everything else is fixed at approval.

**Dimensionality contract.** For one copilot instance, a single triple (n_c categories, n_a actions, d
factors) sizes every object; d is the same across μ, σ, DK, and every factor vector. Concrete shapes
(SOC 6×4×6, S2P 5×5×8 (post SH-05a), Trading 5×4×10, …) are a deployment parameter. **Low dimensionality is load-bearing,
not a limitation:** it is what makes each object auditable, each operation cheap, and a few hundred verified
outcomes enough to move the geometry — the "is this even AI at scale?" objection terminates here, because the
small geometry is the mechanism.

| Object | Lifecycle | Meaning | **Write lane** |
|---|---|---|---|
| `μ` — centroids | **evolving** (every verified outcome) | prototypes of a good decision per (category, action) | **`update` only** |
| `K` — routing memory | **evolving** (every verified outcome) | which evidence proved decisive, per category | **`update` only** |
| `σ` — noise fingerprint | **evolving** (recomputed from R) | per-factor outcome-conditioned variance | **`separate` (diagnostic) only** |
| `R` — verified record | **growing** (append-only, hash-chained) | the outcomes that certify everything | **verification only, append-only** |
| `G` — graphs | **refreshed** (point-in-time) | evidence substrate (State/Event/Decision/Insight clocks) | **ingestion / `enrich`** |
| `C` — candidate pool | **evolving** (proposals awaiting a gate) | variant rules AE proposes, before promotion | **`propose` writes; only a cleared gate promotes → μ/config** |
| `DK` — scoring metric | **configured** (calibration) | per-factor scoring weights (L2 = identity default) | **`calibrate` only** |
| `τ` — temperature | **configured** (calibration) | confidence calibration | **`calibrate` only** |
| `floor` — θ_min | **configured** (fixed at approval) | conservation threshold, derived from ρ and tensor shape | **`calibrate` / approval only** |
| `ρ` — penalty ratio | **configured** (fixed at approval) | asymmetric cost: wrong-auto-action vs wrong-escalation (SOC 20:1, S2P 5:1, Trading 2:1, Purchasing 3:1, DataOps 10:1) | **fixed at approval** |
| `η`, `ε` | **configured** (fixed at approval) | learning rate (η_confirm 0.05 / η_override 0.01) and enrich-blend | **fixed at approval** |
| `W_short`, `m_rate` | **configured** (fixed at approval) | rate-detector window (20) and multiplier (0.85×) — the third gate layer (G-RATE) | **fixed at approval** |
| `m_rel` | **configured** (fixed at approval) | relative-trigger multiplier (0.7×) — the second gate layer (G-REL) | **fixed at approval** |
| `a*(·)` — decision form | **fixed** — architectural invariant | `argmin` over μ under DK | **NOBODY — I1** |

The load-bearing rows:
- **`a*` has no write lane.** The rule that turns a factor vector into an action is written by no operation. It
  is what a risk owner approves, and no learning layer can reach it.
- **`σ` is diagnostic, not a scoring weight.** It measures where factors are signal vs noise (surfacing the
  *trust trap*: the factor a team trusts most is often its noisiest predictor). It feeds `route` and human
  diagnostics but is walled off from `DK`, the metric that scores. Why walled off, not merely unused: I2 (§3).
- **`ρ` (penalty ratio) is the core safety knob.** It shapes θ_min: "41% auto-approve" is safe at 5:1 and
  reckless at 1:1. It is fixed at approval, in the same lane as the floor.
- **`C` (candidate pool) is where AE proposals live** until the promotion gate clears them — never a direct
  write to μ. (The *cycle* that fills and drains C is architecture, §5; the *pool* is engine state.)

*Simple example of the write-partition.* When the analyst confirms the SOC escalation, exactly one thing
changes: `update` nudges one cell of `μ`. DK, τ, floor, ρ, and the decision form `a*` are untouched — a single,
nameable, auditable move you can point back to the alert that caused it, and roll back.

---

## 2. OPERATIONS — the pure transforms the engine exposes

Each operation is a function with a signature and a contract, defined **independent of the loop that calls it**.

**`score(v, Θ) → (a, p, m)`** — nearest-prototype decision. `a = argmin_a ‖v − μ[c,a]‖²_DK`; confidence
`p = softmax(−d²/τ)`; margin `m`. Reads μ, DK, τ; writes nothing. The action is a *distance*, never a reward
maximization — reward lives only in the learning lane.
*Example:* the SOC vector scores closest to "escalate" but barely (`m` small) → the loop investigates first.

**`route(v, Θ) → k*`** — acquisition score. `Q(k; v) = K_{c,k} · ( σ_k^{-1} + |∂d_a/∂v_k| + |μ[a₁,k] −
μ[a₂,k]| )`; next read `k* = argmax_k Q`. The three terms: **precision** (`σ_k^{-1}` — reliable factors read
first), **leverage** (how much reading k moves the decision), **discriminative** (how much k separates the two
leading actions). Read off Θ — no separately trained acquisition model. Reads K, σ, μ; writes nothing.
*Example:* Q ranks "recent role change" highest → read next.

**`enrich(v, e, G) → v'`** — admit evidence and re-extract. `v' = (1−ε)v + ε·A(s, G⊕e, Θ)`. Reads the graph;
writes the working vector `v'` only — never Θ.

**`update(Θ, v, y) → Θ'`** — the compounding move. On verified y ∈ {+1,−1}: `μ ← μ + η·y·(v − μ)` (LVQ;
asymmetric — η_confirm 0.05 on confirm, η_override 0.01 on override, ratio set by ρ). **`K` accumulates by an
EMA over which read last flipped a decision to a verified-correct action:** `K_{c,k} ← (1−λ)K_{c,k} + λ·[k was
decisive]`, so factors that repeatedly prove decisive rise in the routing score. Reads R; writes **only** μ, K.
The only operation that reshapes the decision geometry, strictly in its lane.
*Property — re-convergence (I6, §3):* because `update` re-initializes from prior geometry, it re-converges
faster after a regime it has seen before.

**`separate(Θ) → σ`** — the diagnostic. Per-factor outcome-conditioned variance from R. Reads R; writes σ.
Feeds `route` and human diagnostics; **never** the scoring metric.
*Example:* over hundreds of alerts, `separate` shows "device_trust" — rated highest by analysts — is the
noisiest predictor. `DK` is unchanged; a diagnostic, not a re-weighting.

**`gate(R, floor, ρ, W_short, m_rate) → {GREEN, AMBER, RED}`** — conservation, a **three-layer** test:
`allow iff G-ABS(R) ∧ G-REL(R) ∧ G-RATE(R)`; it pauses if **any** layer fires. Each protects a different
regime, and all three are required (A1-R1/R2, measured):
 - **G-ABS (absolute floor)** — `α·q·V ≥ θ_min` (coverage × rolling verified accuracy over 400 decisions ×
   volume). Protects **cold-start**. *Measured:* the floor clears in ~3 decisions (V_clear ≈ 3, range 3.0–3.3 across copilots) — the window it uniquely protects is small.
 - **G-REL (relative trigger)** — pauses when rolling accuracy falls below a fraction of its **long** rolling
   baseline (the 400-decision window). Protects against **sustained drift**.
 - **G-RATE (rate detector, the third layer)** — pauses when the accuracy of the **last `W_short`=20
   decisions** falls below **`m_rate`=0.85×** the long baseline. Protects against **sudden drops**. *Measured:*
   86.7% detection at 0.87% false-pause, mean lag 19.67 decisions.
 The state: **GREEN** = all three pass (may act); **AMBER** = a layer fired below floor (auto-action pauses,
 learning continues); **RED** = sustained degradation past the recovery threshold, **or hash-chain integrity
 failure** (auto-action *and* learning pause; integrity → RED is I5 enforcing itself). Reads R and the
 configured constants; writes nothing in Θ. A property of the running system's own record, not the current
 decision.
 *Example:* a poison stream drives accuracy below the floor → AMBER via G-ABS; a *sudden* steady-state drop the
 floor has long cleared and the long baseline averages away → AMBER via G-RATE.

> **Why three layers, not two (the measured gap that earned G-RATE).** The engine was designed with two gate
> layers — G-ABS and G-REL. A characterization experiment (A1-R1) measured a gap neither covers: a **sudden**
> accuracy drop in steady state is invisible to G-REL, because G-REL compares against a *rolling* long baseline
> and a sudden drop **averages into its own baseline** — even a multi-point drop dilutes to <2pp across the
> 400-decision window before the ratio would trip; and G-ABS has long since cleared (V_clear ≈ 3). So neither
> sees the step. A1-R2 closed the gap with **G-RATE**: a short window (`W_short`=20) against the long baseline
> at `m_rate`=0.85×, not averaged into its own baseline, so it catches the step. Three-layer coverage is
> *established*, not asserted — the gap was measured, the fix was measured (86.7% detection, 0.87%
> false-pause), and the three-layer gate covers every threat cell A1 tested. The 0.85× multiplier is the
> operating point: low false-pause (0.87% vs 7.67% at 0.90×) at the cost of a longer lag (19.67 vs 12.33) — a
> safety-first tradeoff, stated, not free.

**`propose(Θ, R) → C`** — variant generation (AgentEvolver's **engine half**). Proposes candidate rule variants
to the candidate pool `C`; **writes only C, never μ or the live config.** A candidate leaves C only when the
promotion gate — a reuse of `gate`, the *same* bar as a human-verified update — clears it. *AgentEvolver is
deliberately split across the engine/architecture line, and both halves matter:* `propose` (generate a
candidate) and `gate` (judge it) are the **engine primitives** — the mechanism, and the reason the
self-governance thread ("rejected 35 of its own ideas") has a mathematical foundation; the **cycle** that
shadow-tests a candidate over time and then promotes or demotes it is the **architecture dynamic** (§5). The
engine says *what a proposal is and what bar it must clear*; the architecture says *when to test one and how
long to watch before promoting*. Neither half alone is AgentEvolver.

**`calibrate(R, Θ) → {DK', τ', floor'}`** — offline, authorized configuration. Reads R (plus a held-out split
for τ); writes DK, τ, floor. **Fires only at deployment setup or scheduled recalibration — never during the
decision stream — and requires explicit human authorization.** The L2 default for DK, the per-domain floor fit
(DataOps 0.669, Trading 0.766, …), and temperature calibration for τ all live here. This is why DK/τ/floor sit
in the calibration lane, not the compounding lane: they change *offline and authorized*, never *online and
automatic*.

**`attend(G_i, G_j) → discovery`** — cross-graph. `softmax(E_i E_jᵀ / √d)·V_j`: **`route`'s operator family,
applied between graph domains rather than within one. The mathematical object is identical; only the
application context differs. It is an engine operation.** Reads two graphs; writes discoveries to G.
*Example:* attending the identity graph to the threat-intel graph surfaces that the escalated account's
credential also appeared in a leak-forum toolkit this week — a connection no single-domain query would ask for.

*(There is no `certify` operation — certification is a standing contract, §4. `propose`/`calibrate` write only
their own lanes; nothing but a cleared `gate` moves a candidate into μ or config.)*

---

## 3. INVARIANTS — what holds by construction (why "hardened")

**I1 — Decision-form invariance (the write-partition).** `a* = argmin‖v−μ‖²_DK` is written by no operation.
`update` moves μ,K; `calibrate` sets DK,τ,floor; nothing rewrites the form. "The system compounds" and "the
decision procedure the firm approved never changes" are simultaneously true by construction. *The invariant
that makes self-improvement approvable.*

**I2 — σ⊥μ separation.** The expected centroid update is σ-independent: `E[Δμ] = η·(GT − μ)`, no σ under
unbiased labels. Learning (moves μ) and enrichment (reduces σ) are independent to first order; coupling runs
only through a bounded boundary-mislabeling channel (~1% at production noise). *Why `separate` can be
diagnostic-only, and why a deployment that fits DK from σ (§4) must re-characterize this coupling — the default
L2 keeps DK σ-independent; deviating has a named cost.*

**I3 — A0: acquisition, not depth.** With G, Θ frozen and `enrich` inert, `score∘enrich` reduces to a fixed
map — iterating over unchanged evidence cannot improve the decision. Depth is *acquisition* (`route`+`enrich`),
never loop count. *Bounds what iteration alone can claim.*

**I4 — Conservation is exogenous to the loop.** `gate` reads R, never the current decision or any parameter the
loop optimizes — this holds for all three layers (G-ABS, G-REL, G-RATE), each reading only the verified record.
The loop cannot optimize around the gate. *What makes the gate a guarantee, not a knob.*

**I5 — Append-only certified record.** R is hash-chained and append-only; `update` and `propose`-promotion fire
only on entries in R (human-verified outcomes), never on the system's own guess. A hash-chain failure forces
`gate` → RED. *The anchor a self-improving loop needs and cannot generate itself; the hash chain is a
tamper-evidence integrity input, not a learning input.*

**I6 — Re-convergence.** `update` re-initializes from prior geometry, so after a regime break the system
re-converges faster than it first converged: γ = N₁/N₂ > 1 ⟺ ε_firm > 0.125 (four structural proof paths;
γ ≈ 1.2 in calibrated simulation, magnitude pilot-only). A property of `update`'s mathematics alone, not of any
loop. *Institutional memory is an asset against change, not a liability — but conditional on the firm's own
error clearing the threshold.*

The invariants compose: I5 supplies certified signal, I1 confines where it may write, I4 governs when it may
act, I2 keeps the two learning engines separable, I3 bounds what iteration claims, I6 makes accumulated
geometry pay off after a shock. Remove any one and a specific failure opens.

---

## 4. CERTIFICATION — how every output is known to be right

Certification is a **property of an operation**, assigned once, inherited by every result that operation
produces. It has **two axes** — they answer different questions and are not redundant:

**Axis A — the tier ladder: *what does the result certify?***

| Tier | Correctness signal | What it certifies |
|---|---|---|
| **T-arch** | holds by construction (an invariant) | architectural guarantees (I1–I6) — no measurement |
| **T-geom** | geometry-derived: nearest-centroid over exported geometry — deterministic, reproducible, synthetic | mechanism/capability of `score`, `route`, `separate` |
| **T-real** | real-component: exported production geometry drives the result | that a mechanism runs on the firm's actual geometry (`update` curves; external real data) |
| **T-sim** | simulated: streams, adversaries, competitors built for the test | envelope and safety (`gate` under poison; moat vs a constructed entrant) |
| **T-pilot** | verified human outcomes from a live deployment | **magnitude** on live decisions — the only tier that certifies it |

**Axis B — the K-taxonomy: *what generated the correctness signal?*** (a cross-reference, not a tier)

| K | What it is | Admissible? |
|---|---|---|
| K1 (oracle-behavioral) | a parametric oracle generates controlled responses | yes → supports T-geom |
| K2 (factor-vector oracle) | LLM generates inputs, a math oracle labels correctness | yes → supports T-geom |
| K3 (demo-population) | an LLM generates **both** inputs and decisions | **REJECTED — not a valid signal for any tier** |
| K4 (scraped-external) | real external data validates context | yes → supports T-real |

**The bright line (a certification *rule*, not a tier).** The engine's contract **forbids K3 — an LLM-judged
correctness signal — for any tier**, because it certifies the generator's competence, not the engine's
learning, and is blind precisely on investigation-dependent decisions. The measured cost of violating this
rule *is* K14: on investigation-dependent decisions an LLM judge agrees with ground truth ~12% of the time,
the geometry-derived check ~76%. That gap is the bright line, measured — and it is why the engine's certified
signals are K1/K2 (→ T-geom) for mechanism and verified human outcomes (→ T-pilot, above K4) for magnitude.

**The standing table — each operation's tier.** Any result about an operation inherits its tier:

| Operation | Certified at | Note |
|---|---|---|
| `score` | T-geom | zero-learning accuracy geometry-derived; live magnitude → T-pilot |
| `route` | T-geom, in-distribution | learned routing overfits out-of-distribution → stays in-dist |
| `update` | T-real (curves) + T-geom; I6 T-arch | compounding curves on exported geometry; live magnitude → T-pilot |
| `separate` | T-geom | signal-confidence inversion; diagnostic, not scoring |
| `gate` (3 layers) | T-real + T-sim | floors real-component; poison + sudden-drop detection simulated (A1-R1/R2, 90-cell factorial, 3-seed, three-layer coverage established) |
| `propose` (generation) | T-sim | variant rejection/promotion characterized in simulation |
| `calibrate` | T-real | per-domain floors fit on real-component geometry |
| `attend` | T-geom / T-sim | discovery scaling simulated; magnitude → T-pilot |
| I1–I6 | **T-arch** | proven / by-construction; no measurement claims |

**The rule that ends the per-doc argument.** A new result is certified by *which operation it is a result
about*, at that operation's tier — not re-argued per document. **Magnitude on live decisions is always
T-pilot, never synthesized** — whichever operation produced it. Internal documents state the tier plainly
("T-geom," "characterized negative"); external documents translate the register ("measured on exported
geometry," "boundary defined") but **never** the tier itself.

---

## 5. THE BOUNDARY — what is NOT in the engine (and why)

These belong to the RGI/CI-VLD architecture (the dynamics):

- **The fast loop** (within-decision investigation: `route`→`enrich`→`score`, iterated to a halt) — a
  *sequencing* of engine operations.
- **The slow loop** (compounding across decisions) — the *repeated application* of `update` over a stream.
- **The enrichment controller** (spend one read when confident, more when hard) — a *policy over* `route`'s
  budget. Its offline RL training (Fitted-Q) is a *calibration procedure that produces a policy parameter*,
  analogous to how `calibrate` produces DK/τ/floor — neither engine nor architecture, but the training step
  that configures the controller. Certified where its evidence sits (T-geom + T-sim, in-distribution).
- **AgentEvolver's promote/demote cycle — the architecture half** (its engine half, `propose`+`gate`, is in
  §2). The cycle shadow-tests a candidate from `C` over N decisions, then promotes (writes the cleared variant
  into μ/config) or demotes — a **sequencing of `score` and `gate` over time.** The engine provides the
  proposal primitive and the bar; the architecture provides the *selection over time*. This split is why the
  self-governance thread is both **grounded** (the rejection is `gate` applied to `C`, an engine fact) and
  **temporal** (the 35 rejections happen across a shadow window, an architecture fact).
- **The four readouts** (which evidence / how much / better action / confidence) — *outputs of the loop*
  reading the engine after it has run.
- **The copilots** — five parameterizations of the same engine (different n_c, n_a, d, ρ, reward).

**The test for engine vs architecture:** a **noun-operation on state with a contract** is the engine; a **verb
that sequences operations over time toward a decision** is the architecture. The engine is the instruction set
and registers; the RGI architecture is the program that runs on them.

---

*This is the standing definition every downstream document references. A capability doc cites the operations;
a math doc cites the invariants; any claim cites its tier from §4 — settled once, here. Where a document and
this engine disagree on an object, an operation's contract, or a tier, the engine is canonical.*

---

### Changelog v5 → v6
Added Purchasing ρ (3:1) to penalty ratio list. Added `m_rel` (G-REL 0.7× multiplier) to
state table. V_clear precision (range 3.0–3.3). S2P tensor annotated (post SH-05a).

### Changelog v4 → v5
`gate` is now a **three-layer** operation: `allow iff G-ABS ∧ G-REL ∧ G-RATE`. Added **G-RATE** (short-window
rate detector, W_short=20, m_rate=0.85×) as the third layer, with the measured rolling-window blindness as the
reason it exists (A1-R1 measured the gap; A1-R2 measured the fix — 86.7% detection at 0.87% false-pause). Added
W_short/m_rate to STATE (fixed-at-approval); I4 now covers all three layers; certification table updated.

### Changelog v3 → v4
Made the **AgentEvolver engine/architecture duality first-class and explicit on both sides**: `propose`+`gate`
named as its engine half (§2, the self-governance foundation), the shadow-test→promote/demote cycle as its
architecture half (§5), intro flags that one capability straddles the line by design. K-taxonomy correction
(K3 rejected, separate axis, bright line as a rule) and all v3 additions retained.

### Changelog v2 → v3 (from review)
Added: `calibrate` and `propose` operations; the candidate pool `C`, `ρ`, `η`, `ε` as state objects;
lifecycle column (evolving vs configured); dimensionality contract + "low-d is load-bearing"; K-accumulation
rule (EMA); I6 re-convergence; `gate` three states (GREEN/AMBER/RED) + hash-chain→RED; `route` Q-terms named.
Corrected: K-taxonomy is a **separate axis** from the tier ladder, **K3 is REJECTED** (not T-geom), the bright
line is a **rule not a tier**, and K14 is its measured cost. Made assertive: `attend` is engine. Resolved:
AE promote/demote is architecture (grounded via `propose`+`gate`); σ-in-DK is a calibration option with a named
I2 cost.
