# D1 / D2 / Fig-1–3 production notes

Date: September 14, 2026. New computation random_state=42; original KE-1/B1 seeds preserved.

## Input gate

KE-1 summary contains endpoints only. Exact checkpoint files supply ten points per domain at N=50–500; DataOps uses k_learning_curve_results.json. Each domain has one training seed, not multi-seed uncertainty. No N=0 point is fabricated.
B1 JSON is indexed by copilot / D250 / arm1_incumbent, arm2_cold_start, arm3_replay, arm4_migration. Checkpoints carry global decision_count and entrant live_decisions.
Original GAP-2 script scripts/gap2_abstention_curve.py selects the best signal at 75% on evaluation data and ranks the evaluation cohort to derive its thresholds. final_d_min is its post-investigation d_min. A fresh three-way rerun was required and completed; only its untouched test curve appears in Fig-3.
S2P trace sources: prepaper v10 S2P-SC2 and sibling s2p-copilot/backend/app/vld_preseed.py and evidence_provider.py. The actual clause is bulk-volume pass-through, not commodity-index entitlement. No absent clause is invented.

## D1

See recursion_trace_example.md. The executed K-only trace uses explicit planted K5=.62, a B=3 acquisition and simulated verification, then a changed B=2 next decision against a frozen-K counterfactual. ΔK=[.02,.02,0,0,0,.04,0,0], Δμ=0. The .200/.100 discrepancy is base versus K-weighted Q. Tier: REAL_COMPONENT geometry + SIMULATED verification, PLANTED FIXTURE evidence/start. The production callback's flip bonus, external verification and lack of conservation enforcement in this local demonstration are disclosed.

## D2

All wall-clock estimates are ILLUSTRATIVE. MAP v20 ($7B manufacturer) assumes SOC 1200, S2P 486, Purchasing 231, DataOps 106, Trading 19 verified outcomes/week. Weeks=N/rate. Divergence is the first observed strictly >1pp learn-minus-frozen routing_quality gap, not a statistically significant or sustained divergence. Checkpoint spacing limits temporal resolution.
S2P's N=50 gap is exactly +1pp and does not qualify; N=100 is negative; first >1pp is N=150.
weeks_to_plateau uses MAP's assumed N=500 planning horizon, explicitly not a measured five-domain plateau. Extended DataOps routing is .630 at 500, .640 at 1000, .630 at 2000; that separate single-seed run supports near-plateau language only for DataOps.

| Copilot | N divergence | Verified/week assumption | Weeks divergence | Weeks to assumed N500 |
|---|---:|---:|---:|---:|
| SOC | 50 | 1200 | 0.041667 | 0.416667 |
| Purchasing | 50 | 231 | 0.216450 | 2.164502 |
| S2P | 150 | 486 | 0.308642 | 1.028807 |
| DataOps | 50 | 106 | 0.471698 | 4.716981 |
| Trading | 50 | 19 | 2.631579 | 26.315789 |

B1 versus KE-1: SOC B1 final=.786 at N1000, KE-1=.810 at N500; DataOps=.5875 versus .630. Different seeds, horizon and evaluation cohorts (B1 fixed 1000 cases, KE-1 changing 50-case samples) prevent an exact endpoint replication claim. Divergence points use KE-1 exclusively.

## Fig-1

Exact final lifts: SOC +12pp, Trading +12pp, Purchasing +21pp, DataOps +19pp, S2P +3pp. All saved learning-arm checkpoint hurts are zero. This metric is synthetic action degradation versus surface on that evaluation cohort, not a no-degradation guarantee. S2P's −2pp at N100 and −3pp at N250 are circled. All five frozen baselines move because evaluation samples change despite fixed K. No smoothing, extrapolation or invented bands. The chart shows the 500-decision observation horizon, not an established five-domain plateau.

## Fig-2

Global-N axis runs 0–1000; entrant curves start at D250. Replay and migration exactly match incumbent from entry onward, so three curves overlap. Different widths and open markers expose the coincident lines without numerical offsets. 0 decisions to parity means no NEW verifications after entry; it excludes replay computation and migration engineering.
The requested SOC 525 and DataOps 575 numbers are JOINT parity (routing_quality AND action_accuracy within 1pp), elapsed since entry. Markers are therefore at global N775/N825. Routing-only first parity is 475 for SOC and 200 for DataOps; these metrics are not interchanged. DataOps joint parity is transient and not sustained through the horizon; at N1000 its cold arm is .5675 versus incumbent .5875 (−2.0pp routing_quality). The full tail is plotted and subsequent >1pp gaps shaded.

## Fig-3

New protocol: 500 train / 500 threshold-selection / 500 evaluation, five seeds per domain; signal fixed in advance to final_d_min. Numeric thresholds are selection-set quantiles, locked before generation of the test cohort. Split fingerprints are disjoint; K is frozen for selection/test. Original decision generator, B=2 recurrence and K rule are reused; all labels and evidence remain simulated.
X plots actual test coverage, not enforced test-set quantiles. Callouts refer to the selection-set 75% target. Y is action_accuracy on accepted decisions, distinct from routing_quality; category is supplied. Baseline is the same B=2 policy acting on every case, not budget-zero single-pass. Bands are descriptive paired-seed bootstrap intervals; five seeds and geometry-derived truth limit inference.

| Copilot | Original lift at 75% | Held-out coverage at 75% target | New action_accuracy lift | Lift 95% interval |
|---|---:|---:|---:|---:|
| DataOps | +9.49pp | 74.04% | +10.98pp | [9.74, 12.17]pp |
| Purchasing | +15.20pp | 74.56% | +13.36pp | [12.24, 14.62]pp |
| SOC | +8.48pp | 73.64% | +8.92pp | [7.08, 11.28]pp |

The +9.5–15.2pp exploratory range is not exactly replicated: fresh held-out lifts span +8.92–13.36pp. All remain positive. SOC accepted cases have zero observed errors at this threshold, hence its five-seed bootstrap accuracy interval degenerates to [1,1]; this is not proof of zero population risk. Threshold uncertainty and five-seed bootstrap are descriptive, not deployment guarantees.

## Reproduction

Run mypy on each new script with pyproject.toml before executing. Run python -B scripts/d1_recursion_trace_v1.py; python -B scripts/gap2_abstention_heldout_v1.py; python -B scripts/generate_d1_d2_paper_figures_v1.py. Source hashes and machine-readable plotting values are in d1_d2_figures_audit_v1.json. Charts: whitegrid, #FAFAFA, sans-serif, 11pt axis labels, 14pt main titles, 10×6 inches, 300dpi PNG and editable-text SVG.
Only new scripts and outputs were authored. No git commands or edits to pre-existing sources.
