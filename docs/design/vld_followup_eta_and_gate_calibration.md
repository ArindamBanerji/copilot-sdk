# Two Follow-up Experiment Specs (from campaign findings)

Two cheap, mistake-proofed experiments. **Run F-2 (Purchasing gate calibration) FIRST** — it's the one
with operational teeth (a 34.8% clean-stream false-pause is a product blocker). Then F-1 (η-sweep).
Standing rules (both): reuse existing harnesses; **no git, no source-file modification** (new scripts +
results only; the frozen SDK files are call-not-modify); `random_state` swept as specified; deterministic
JSON + two-rebuild byte-identical check; mypy clean; **pre-register metric + decision rule in the header
before running**; **name the metric every time** (`routing_quality` / `category_accuracy` /
`action_accuracy` — do not mislabel, per the C5 metric-label error); tier every result (REAL_COMPONENT +
SIMULATED / GEOMETRY-DERIVED); STEP-0 read-gate before coding. **Report results + artifact paths only — no
reasoning-scratch in the output** (the C4/C5 response leaked path-formatting scratch; don't).

---

## F-2 (RUN FIRST) — Purchasing conservation-gate false-pause calibration
**Finding it addresses:** C5 showed Purchasing PAUSEs on **34.78% of clean-stream decisions** — a gate too
aggressive for Purchasing geometry. Likely mechanical: the gate's Check-A is a **fixed 75%/last-100-record
accuracy floor**, but Purchasing's *clean-stream* base accuracy may sit near/below 75%, so the gate fires
on normal operation, not degradation.

**STEP-0 (report before running):**
- Confirm the gate rule from code (`scorer.py` `_conservation_pause()` / Check-A): the exact threshold
  (0.75?), window (last 100?), and whether it is a **global constant** across copilots or already
  per-domain. Quote file:line.
- Measure each copilot's **clean-stream base accuracy** (no injected degradation) over the last-100 window
  at steady state. This is the diagnostic: if Purchasing's clean base ≈ or < 0.75, the false-pause is
  explained (the floor is above its normal operating point).

**Experiment:**
1. **Diagnose:** for all five copilots, report clean-stream base accuracy (mean ± SD, 3 seeds) vs the 0.75
   floor. Expected: Purchasing's clean base is closest to / below 0.75.
2. **Calibrate (in a NEW script — do NOT modify the gate source):** re-evaluate the gate on clean streams
   under a **per-domain floor** rule, `floor_d = clean_baseline_d − margin`, sweeping margin ∈ {0.05, 0.10,
   0.15}. Report the resulting clean-stream false-pause rate per copilot per margin.
3. **Re-check detection is preserved:** with the calibrated per-domain floor, re-run the C5 slow-drift +
   poison-25% conditions for Purchasing (+ SOC as a control) and confirm the gate **still detects** real
   degradation (detection lag not materially worse) — i.e., the calibration lowers false-pauses WITHOUT
   blinding the gate.

**Pre-registered decision rule:** "a per-domain floor at margin m is acceptable iff it brings every
copilot's clean-stream false-pause rate below [pick a threshold, e.g. 5%] AND preserves detection on
slow-drift + poison-25% (lag within ~1.5× of the global-floor lag)."

**Deliverables:** `experiments/vld/results/gate_calibration_f2.json` + a summary with: the clean-base-vs-0.75
table (all five), the false-pause-vs-margin table, and the detection-preservation check. **Do NOT modify the
gate in source** — this is a *calibration investigation* that recommends a floor rule; implementing it is a
separate authorized change.
**Paper impact:** turns "34.8% false-pause on Purchasing" (liability) into "the gate requires per-domain
calibration; a per-domain floor at margin m yields <X% false-pause while preserving detection" (a stronger,
honest safety claim). This finding is a **required disclosure** in the conservation section regardless of
outcome.

---

## F-1 — η-sweep: is the μ-learning bimodal split a domain property or an η artifact?
**Findings it addresses:** (a) **#1** S2P μ-learning showed **negative widening (−5.33pp)** under the
SOC-calibrated η — anomalous; (b) **#3** C2 found only **SOC judgment-specific (1/4 split)** — mechanism
unmeasured. Both may be η artifacts. This tests stability before anyone tries to *explain* the split.

**STEP-0 (report before running):**
- Confirm the μ-update learning rate parameter (η / `eta`) and where it's set for `ProfileScorer.update()`
  (`profile_scorer.py`) — confirm a new *script* can pass/sweep η **without modifying source**. If η is
  hard-coded and not settable from a script, report that (then F-1 is blocked pending a settable-η path —
  do NOT patch source).

**Experiment (μ+K learning, Arm 1 vs Arm 2, the C2/EXP-2 setup):**
- **Sweep η ∈ {0.5×, 1×, 2×, 4× the current default}** (report the actual values), on **{SOC, S2P} at
  minimum** (all five if cheap), **3 seeds each**. SOC is the **control**: it is the known judgment-specific
  copilot.
- For each (copilot, η, seed): report the **routing-gap widening** (μ+K gap − K-only gap) — the C2 metric.

**Pre-registered reads (hypotheses, NOT targets):**
- If **SOC stays judgment-specific (widening > +2pp) across all η** while **S2P's sign tracks η** (negative
  at low η, moving positive/negative as η changes) → the split is an **η artifact** for S2P; the paper notes
  the C2 result is η-sensitive and scopes the claim to "SOC judgment-specific under the tested η."
- If **S2P stays negative across all η** while SOC stays positive → S2P has a **real domain attractor**
  (μ-learning collapses toward a shared prototype); a genuine domain property worth a footnote + a future
  mechanism study.
- If **SOC itself is η-fragile** (widening vanishes at some η) → even the SOC judgment-specific claim is
  η-conditioned; report that honestly (it would narrow the headline).

**Deliverables:** `experiments/vld/results/eta_sweep_f1.json` + a summary table (copilot × η × widening,
mean±SD over seeds) and the one-line verdict against the three reads above.
**Paper impact:** determines whether C2's "SOC judgment-specific, others routing-only" is a **stable
finding** (scope the claim to SOC, name the mechanism open) or **η-sensitive** (add the η caveat).
**Do NOT** run a mechanism/explanation study for the split until F-1 confirms it's η/seed-stable — don't
explain a possible artifact.

---

## Order & why
1. **F-2 first** — operational blocker (false-pause) + required paper disclosure; cheap; per-domain floor is
   likely the fix.
2. **F-1 second** — disambiguates #1 and tests #3's stability in one sweep (SOC control built in); paper
   carries an η caveat on C2 until it returns.
Neither weakens a demonstrated capability: SOC judgment-specificity and the conservation *detection*
capability both stand; these experiments **bound and calibrate** them honestly.
