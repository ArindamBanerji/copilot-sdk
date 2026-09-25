# A1 — Conservation-gate reconciliation

Date: September 14, 2026  
Scope: code inspection, four-point arithmetic check, and analysis of existing KE-5 data only. No experiment sweep or source changes.

**Verdict: the canonical GREEN formula is broken as an accuracy floor.** It exactly reproduces the paper's inverse-square threshold and permits GREEN with one correct decision out of 500. The SDK also implements a separate recent-accuracy learning veto, which mitigates that particular history after a full recent window exists. These are different rules; neither the paper nor KE-5 establishes a single, consistently enforced safety gate.

References below use paths relative to `copilot-sdk`; `../graph-attention-engine-v50` is the sibling GAE repository. Code is authoritative. The v7.3 printed formula and KE-5 source/results were available. `vld_paper_experiments_request_v2.md` was not located in the workspace filename search; the supplied A1 prompt defines this task. MAP v20 was available as `docs/design/map_vld_addendum_v20 (1).md`.

## 1. Gate as implemented

### 1.1 Canonical calibration status: the rule actually used by KE-5

In `../graph-attention-engine-v50/gae/calibration.py:194–198`:

```python
def compute_theta_min(alpha: float, V: float) -> float:
    if alpha <= 0 or V <= 0:
        return float("inf")
    return 23.53 / (alpha * V)
```

In the same file, lines 233–248:

```python
signal = alpha * q * V
if signal >= 2 * theta_min:
    status = 'GREEN'
elif signal >= theta_min:
    status = 'AMBER'
else:
    status = 'RED'
# The returned passed flag uses signal >= theta_min, not GREEN alone.
```

For positive α and V:

```text
GREEN iff α × q × V ≥ 47.06 / (α × V)
      iff q ≥ 47.06 / (α × V)²
```

AMBER-or-GREEN, including the returned `passed=True`, instead requires `q ≥ 23.53 / (α × V)²`. Comparisons precede rounding of the returned display fields.

**Constants:** 23.53 is a literal in `calibration.py:198`. Its executable implementation contains no confidence level, target harm rate, or derivation of that number. **47.06 is exactly 2 × 23.53**, arising from the GREEN multiplier at line 236. It is not an independent estimate or safety calibration. The separate, deprecated `_derive_theta_min` API at lines 153–191 computes `eta * n_half**2 / t_max_days`, approximately 0.4667 with its defaults. That historical convergence-budget constant is not what `compute_theta_min` or KE-5 uses.

`conservation_status` at `calibration.py:440–474` supplies the actual meanings:

```python
alpha = max(0.0, min(1.0, categories_with_data / total_categories))
q = correct_count / verified_count
V = float(verified_count)
theta_min = compute_theta_min(alpha, V)
return check_conservation(alpha, q, V, theta_min)
```

| Symbol | Executable meaning and units | Source |
|---|---|---|
| α | Fraction of configured categories represented by verified data; dimensionless. SDK coverage counts categories with at least one eligible verified decision. It is not the learning rate or analyst override fraction. | `calibration.py:470`; `copilot_sdk/scoring/scorer.py:57–64,2655–2667` |
| q | Correct-count divided by verified-count; a dimensionless fraction over the supplied cumulative population. In the SDK, “correct” means a confirmed outcome or a truthy `is_correct` field, not an independently proven ground-truth property. | `calibration.py:471`; `scorer.py:2795–2811,2905–2914` |
| V / N_ver | Number of eligible verified decisions, including correct and overridden decisions; units are records/count, not records per day. The scorer filters benchmark-tagged decisions from its conservation population. | `calibration.py:472`; `scorer.py:2677–2682,2805–2808,2929–2938` |
| αqV | Coverage-weighted count of correct decisions, using the definitions above. No time normalization appears. | `calibration.py:233,470–473` |
| q_recent | Correct fraction over the last returned W eligible verified records, W=100 by default. This is separate from cumulative q. | `scorer.py:2245–2254,2778–2792` |

The low-level `check_conservation` docstring at `calibration.py:219–226` still calls α “override rate,” q “override quality,” and V “verified decisions per day.” Those descriptions are stale relative to the executable wrapper and SDK callers. `CalibrationProfile.learning_rate` also uses the symbol α in its documentation, but is a different quantity.

`penalty_ratio` and `window=400` are accepted by `conservation_status` but unused in its body. In particular, setting DataOps penalty_ratio=10 does not create a cost-sensitive accuracy threshold. The SDK does separately use penalty_ratio to scale incorrect-outcome centroid updates at `scorer.py:1085–1090`.

### 1.2 The SDK learning veto is different

`CompoundingScorer.learn()` calls `_conservation_pause()` at `scorer.py:1008`. For normal operation with at least ten eligible verified decisions, the latter checks:

1. **Recent quality:** if at least W=100 recent records are available, pause when `recent_q < 0.75` by default (`scorer.py:2245–2268`). The preset can override both values.
2. **Volume signal:** pause when `alpha * effective_q * verified < compute_theta_min(alpha, verified)` (`scorer.py:2269–2299`). This uses **one θ**, not the calibration GREEN threshold of two θ.
3. **Dispersion adjustment:** `effective_q=q` ordinarily. If estimated dependence inflation exceeds 1.3, subtract the estimated effective standard error, floored at zero (`scorer.py:2274–2284`). The diagnostic uses up to the last 400 eligible records, starts at 20 records, and uses block=20, n_boot=200 (`scorer.py:2705–2735`). This is not a specified-confidence accuracy bound.
4. Conservation read failures pause learning after a retry (`scorer.py:2203–2227,2302–2315`).

Thus the normal learning-permission condition is approximately:

```text
(n_recent < W or q_recent ≥ t)
and α × q_effective × V ≥ 23.53 / (α × V)
W = 100, t = 0.75 by default
```

It cannot be reduced to a unique cumulative `q_required(α,V)`: history order, recent quality, dispersion, and preset configuration also matter.

The last-W population is the tail of the store-returned sequence. The inspected SQLite implementation orders verified records by **decision creation time and ID**, not verification arrival time (`copilot_sdk/graph/sqlite_store.py:2475–2489`). This distinction matters for backfilled verification.

### 1.3 Callers and status disagreements

| Path | Rule used | Meaning |
|---|---|---|
| `scripts/ke5_conservation_interaction.py:13–21`; `scripts/ri1_routing_k_interaction.py:273–279` | Calibration GREEN, two θ | Only this status permits that experiment's K update. |
| `copilot_sdk/backend/conservation_utils.py:79–86,246–247` | Calibration status/check | Supplies status payloads and L5 metrics; it does not itself execute or withhold an action. |
| `scorer.py:1008,2198–2300` | Recent-quality veto plus one-θ volume floor | Actual shared scorer learning-pause path. |
| `scorer.py:1573–1602` | First respects the learning veto; otherwise labels signal ≥ θ GREEN | Snapshot GREEN differs from calibration GREEN. |
| `scorer.py:749–750` | Reads the status-payload helper | The status display does not automatically include the separate recent-quality veto. |
| `copilot_sdk/conservation/global_gate.py:47–86` | Aggregates stored domain status labels | Transfer permission relies on what those snapshots mean; it supplies no new accuracy bound. |

A displayed calibration GREEN therefore must not be equated with shared scorer learning permission. Likewise, the primitive's `passed=True` includes AMBER.

## 2. Gate as printed, and discrepancies

The paper `docs/design/ci_rgi_impact_core_v7_3.md:810–813` prints:

> θ_min = 23.53 / (α · V), signal = α · q · V  
> α = covered_categories / total_categories, q = correct / verified, V = verified_count.  
> GREEN: signal ≥ 2θ_min (learning + action). AMBER: signal ≥ θ_min (action only). RED: abstain.

**The algebra and variable definitions match the calibration wrapper and KE-5.** Astra's inverse-square reduction is correct; this is not merely a typesetting error that hides a sane canonical formula.

The discrepancies are in enforcement and safety interpretation:

- The shared SDK learning path uses a one-θ volume test and a separate default 75%-recent-quality veto. The paper omits the latter, its minimum window, and bootstrap exceptions.
- The shared learning path does not use “GREEN only”: absent its other vetoes, one-θ AMBER-level signal can proceed.
- Calibration status computation alone does not implement the paper's universal “RED: abstain” action policy. The inspected shared `learn` path gates parameter updates; application action/emit policies need their own demonstrated wiring.
- The printed label “learning + action” overstates what this scalar status proves. Neither passing it nor seeing zero harms in a constructed fixture proves “cannot unlearn” or absence of harmful future decisions.
- The paper's “inert at this scale” KE-5 sentence at line 749 describes a result from the calibration/K harness, not a test of the current composite SDK learning veto.
- Internal documentation also needs reconciliation: the obsolete override-rate/per-day docstring conflicts with current covered-category/verified-count code.

## 3. Worked four-point table

The following values were computed by loading the actual GAE calibration module with bytecode writing disabled. For each row, θ came from `compute_theta_min`, and the analytical boundary was checked just below and above using `check_conservation`. This is the requested arithmetic grid, not an experiment sweep.

| α | V | θ_min | Continuous q required for calibration GREEN | Four decimals | Accuracy percentage | Minimum integer correct count |
|---:|---:|---:|---:|---:|---:|---:|
| 0.5 | 50 | 0.941200 | 0.07529600 | 0.0753 | 7.529600% | 4/50 |
| 0.5 | 500 | 0.094120 | 0.00075296 | 0.0008 | 0.075296% | 1/500 |
| 1.0 | 50 | 0.470600 | 0.01882400 | 0.0188 | 1.882400% | 1/50 |
| 1.0 | 500 | 0.047060 | 0.00018824 | 0.0002 | 0.018824% | 1/500 |

The unadjusted **one-θ SDK volume condition alone** has half these thresholds: 0.03764800, 0.00037648, 0.00941200, and 0.00009412 respectively. These are not the full learning gate.

At V=50 the default 100-record recent-quality check has not become enforceable. At V=500 it additionally requires at least 75 correct records among the last 100, assuming the default configuration and an available full history. That is not “cumulative q ≥ 0.75”: a 75/100 recent segment only implies cumulative q ≥ 75/500=0.15. Other conditions still apply.

## 4. Verdict and direct counterexample

**Broken as a canonical accuracy floor.** Even the V=50 thresholds are well below a plausible 50–90% quality floor. With increasing V, the boundary shrinks as (1/V^2); collecting more mostly incorrect labels can make the volume status easier to pass.

Direct calls to the implemented `conservation_status` with 500 verified decisions, one correct decision, penalty_ratio=10, and six total categories returned:

| Covered categories | α | q | signal | Returned θ_min (rounded) | Status |
|---:|---:|---:|---:|---:|---|
| 3 | 0.5 | 0.002 | 0.5 | 0.0941 | GREEN |
| 6 | 1.0 | 0.002 | 1.0 | 0.0471 | GREEN |

This uses valid counts and no overridden threshold.

**Important limit on that verdict:** the normal SDK learning veto would reject the same 1/500 history once its default recent window is available: no 100-record subset could have recent accuracy above 1%. The 75% recent rule is a meaningful empirical check, but it does not repair the canonical GREEN computation, protect the sub-100 regime in the same way, or supply a statistically calibrated no-degradation guarantee. The code implements inconsistent status and permission paths, not one reconciled sane safety floor.

## 5. Initialization and verification during a pause

### Initialization

- `compute_theta_min` returns infinity for nonpositive α or V (`calibration.py:196–197`).
- `conservation_status` returns signal=0, θ=infinity, RED, passed=False when total_decisions or verified_count is zero, or required category-count inputs are missing/invalid (`calibration.py:454–469`). A zero-count direct call reproduced this.
- The shared SDK **bypasses** learning conservation at V=0 and V=1–9, returning no pause in explicit cold-start/bootstrap modes (`scorer.py:2229–2241`; minimum ten at line 64). The display reports COLD_START/BOOTSTRAP with passed=True (`scorer.py:782–785`), not ordinary GREEN.
- Server-side preseed mode also bypasses the pause (`scorer.py:2199–2201`); a client preseed flag is not sufficient (`scorer.py:1005–1007`).
- Zero coverage with positive counts is also represented as CALIBRATING by the L5 metrics helper (`conservation_utils.py:228–245`). These explicit modes must not be silently collapsed into the calibration function's status labels.

### Does verification continue while learning is blocked?

**In KE-5, yes. In the normal shared learn route, not automatically.**

The experiment performs the episode and increments `support` and `train_correct` before evaluating the gate. Only the K-update branch is conditional (`scripts/ri1_routing_k_interaction.py:263–284`). Thus V advances on all 500 synthetic verifications even if K cannot change.

In production's shared `CompoundingScorer.learn`, the pause is evaluated at line 1008 and returns at line 1074. The centroid update is at line 1092, and the verified outcome is written at **line 1113**, after that return. The HTTP learn route also returns immediately for a blocked result at `copilot_sdk/backend/scoring_router.py:298–299`, before its optional outcome-recorder callback at lines 301–309. A pause snapshot/checkpoint does not record the newly supplied outcome as a verified decision.

Consequently, repeated submissions through that same blocked learn path cannot by themselves refresh the quality window or V. Separate outcome persistence exists—for example `ProtocolV2OutcomeService.learn/_commit` at `copilot_sdk/graph/outcome_service.py:46–69,106–108` writes outcomes independently—but its use for recovery while the shared learner is paused is not established by that route. The paper must not assume the KE-5 verification lifecycle is already the shared production lifecycle.

## 6. Why KE-5 was inert

Authoritative existing result: `experiments/vld/ke5_conservation_interaction.json`, specifically `protocol.conservation`, `results.*.seed_runs`, and `summary`. Its stored calibration SHA-256 is:

`8a3ea47dfd461ee000d978240c95ad135f61c0ab9504c858e3953d5618538f58`

It **exactly matches the current calibration source**. No experimental rerun was needed.

| Seed | Blocked decisions | Blocked factor updates | Last blocked decision |
|---:|---:|---:|---:|
| 20260913 | 11 | 22 | 11 |
| 20260914 | 13 | 26 | 13 |
| 20260915 | 8 | 16 | 8 |
| 20260916 | 9 | 18 | 9 |
| 20260917 | 10 | 20 | 10 |
| Mean | 10.2 | 20.4 | — |

**10.2 denotes decisions, not individual factor updates.** At budget two, those decisions account for 20.4 blocked factor updates.

Both arms finish at routing quality 0.580 and accuracy 0.796. Both primary N=350 and N=450 routing dips are 0.016 and 0.010; their reductions are zero. The supplementary fixed-cohort N=450 comparison differs by 0.002, which the report correctly treats separately from the primary result (`experiments/vld/group_a_d_report.md:147–162`).

By N=500, α=1 in every treated run, training q is 0.748–0.774, and signal is 374–387, while the GREEN boundary is only (2θ=0.09412). Once early category support accumulates, this gate becomes extremely permissive. **It is not awaiting a larger sample scale: increasing V makes the quality requirement still smaller.** No block occurs after decision 13 in any saved treated run.

KE-5 is informative about that specific K-only, frozen-geometry harness. It is inadequate evidence for the stronger safety claim because it:

- does not call `CompoundingScorer._conservation_pause`, so it omits the 75%-recent-quality veto, dispersion adjustment and production bootstrap behavior;
- continues synthetic verification while K is blocked, unlike the inspected shared learn path;
- tests an unused penalty_ratio argument, not a calibrated asymmetric-loss threshold;
- measures routing/accuracy fluctuations, without demonstrating that the gate detects a harmful update or rejects a persistently poor deployment.

The older `scripts/k_learning_conservation_interaction.py:65–90` and `ke5_conservation_interaction_results.json` belong to a different implementation: rolling accuracy compared directly with θ and an initial 50-decision bypass. They must not be substituted for the canonical run's 10.2 figure.

## 7. CISO-readable rationale and required assertion

A statistical defense of the printed/canonical GREEN rule is **not justified**. A correct gate should assert that recent, independently verified performance clears a predefined business-risk floor with an explicit allowance for sampling uncertainty, and that a proposed model update does not increase harmful decisions beyond an agreed tolerance. It should require enough representative evidence, keep collecting verification even when updates are paused, and distinguish permission to learn from permission to execute an action. More historical records should increase confidence in measured quality; they should not allow a system with almost every decision wrong to become GREEN. The SDK's recent 75% check is a useful empirical safeguard, but its percentage, window, uncertainty treatment and outcome costs still require justification; it is not proof that the system cannot degrade.

## Read-only verification and provenance

- Created only `experiments/vld/results/conservation_gate_reconciliation.md`.
- No source edits, git commands, experiment sweep, new script, CSV, JSON, or chart.
- The arithmetic checks loaded the actual calibration module with Python `-B`. Mypy used `--cache-dir=nul` to avoid cache output.
- Mypy under SDK `pyproject.toml`: `copilot_sdk/scoring/scorer.py` and `copilot_sdk/backend/conservation_utils.py` each passed.
- Read-only mypy found five existing `no-any-return` diagnostics in `../graph-attention-engine-v50/gae/calibration.py`, lines **698, 738, 739, 844, 874**, all reporting an Any return from a function annotated `ndarray[Any, Any]`. They are outside the inspected gate functions and were reported without fixes.
- Source-tree SHA-256 manifests (sorted relative Python-file paths plus file hashes; dependency/cache directories excluded) confirmed all 1,259 pre-existing SDK Python files and all 128 GAE Python files unchanged. Matching before/after digests: SDK `4f45acc0affdc8f63930d10e5bb9d954d14861671db8f7066f34a3cd13037e28`; GAE `d77dc4a128f57017975242c5d566a2f541787a4533d4d5706cfb36710608d96d`.
- Concurrent workspace activity added `experiments/vld/vld_delayed_entrant_v1.py` and `experiments/vld/results/delayed_entrant_catchup.json` during this review. A1 did not create, edit, or execute either file. The new Python file was excluded when comparing the pre-existing source manifest. A1 itself ran no experiment and created only this report; the workspace as a whole was not otherwise idle.
