# VLD-S2P-K-RANGE: reachable K analysis

Date: 2026-09-12  
Authority: [E2E design §4.5](vld_e2e_architecture_design_2026-09-12.md#45-decision-q5--verified-feedback-k-lifecycle-and-credit-assignment); user-specified MAP v14 S2P-SC2 issue.  
Scope: read-only experiment against the supplied centroid export and S2P preseed. This document is the only file created by this task. No git commands, source edits, application startup, database writes, or persisted K updates were performed. Python was invoked directly from the requested virtual environment with `-B` to prevent bytecode writes.

## Finding and recommendation

**Yes: VLD-S2P-2 flips from flag_leakage to auto_approve with K entirely inside [0.1, 3.0]. All seven requested configurations pass.** Their final margin is **0.893492315669**, and their surface margin is **0.890894753779**. K=[5,0.1,0.1,0.1,0.1,6,0.1,0.1] is unnecessary for this exported geometry.

Recommend **K=[0.5,0.5,0.5,0.5,0.5,1.0,0.5,0.5]** for S2P-SC2: only dimension 5 changes from the initial uniform 0.5 state. It preserves the intended 0 → 5 read order and has room above the measured routing boundary. The smaller **K5=0.70** also passes; **K5=0.64** is the first passing value on the idealized +0.02 grid from 0.5. These are demonstrated values for the frozen snapshot, not robustness guarantees for changed geometry or evidence.

Suggested demo wording:

> With uniform K=0.5, the two-read investigation selects contract coverage then price benchmarking and remains flag_leakage. With dimension 5 weighted at 1.0 and all other dimensions at 0.5, it selects contract coverage then volume context and flips to auto_approve. These custom weights are within the production bounds; this comparison demonstrates routing sensitivity, not a verified production-learning history.

## Inputs and execution contract

- Snapshot: `copilot-sdk/real_centroids_v1.json`, `copilots.s2p.all_category_mu.price_variance` (5 actions × 8 factors). The scenario's category selects the centroid slice.
- Surface vector loaded from the current preseed's factor map: `[0.9237, 0.101, 0.0568, 0.0, 0.6731, 0.0, 0.3416, 0.2494]`.
- Action order: `auto_approve, hold_for_review, escalate_to_buyer, flag_leakage, refer_to_specialist`.
- Sigma: `[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`; tau=0.1; explicit budget=2; no gated sources; no external `score_fn`. These match the export's unit-sigma fallback and the S2P investigation factory's ungated evidence wiring.
- Evidence: `seed_vld_s2p_showcase({})` builds the real preseed payload entirely in memory; `S2PEvidenceProvider(payload, "VLD-S2P-2")` supplies reads. No expected-action field is passed to the scorer.
- Both `VLDInvestigator.investigate()` and the module-level `investigate(..., k_weights=K)` were executed; serialized traces were identical for every run, including bisection probes.
- Environment: Python 3.11.4, NumPy 1.25.0, interpreter `C:/Users/baner/CopyFolder/IoT_thoughts/python-projects/proj-envs/python_expts_venv/Scripts/python.exe`.
- Scope of “production”: exported production centroid geometry, production provider code, and bounded K. This was not a mounted HTTP test or a live-state re-export. Export metadata says `live_age_verified=false`, describes preset construction plus six startup L5 rows, and identifies sigma as a unit-vector fallback. Classifier-selected budgets, current database K, effective metric changes, and future §4.5 learning behavior are outside this experiment.

| Dimension | Factor |
| --- | --- |
| 0 | match_status |
| 1 | amount_variance_ratio |
| 2 | duplicate_score |
| 3 | supplier_exception_history |
| 4 | payment_terms_impact |
| 5 | commodity_index_correlation |
| 6 | tax_regulatory_compliance |
| 7 | environmental_risk |

The relevant evidence is dim 0: contract_db, value=0.93, confidence=0.90; dim 5: demand_forecast, value=0.82, confidence=0.78; dim 1: pricing_benchmark, value=0.05, confidence=0.82. Because the factory specifies no gated sources, values replace their selected coordinates directly; confidence does not damp them.

## Full requested K sweep

Margin means top probability minus second-highest probability, not action correctness. Flip means terminal action differs from surface action; every passing row below specifically reaches auto_approve. Dimensions are attempted in the displayed order; all reads in these runs were acquired.

| Config | Full K vector | Surface action | VLD action | Flip | Final margin | Attempted dims |
| --- | --- | --- | --- | --- | ---: | --- |
| K_A | `[3.0, 0.1, 0.1, 0.1, 0.1, 3.0, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K_B | `[2.5, 0.1, 0.1, 0.1, 0.1, 3.0, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K_C | `[3.0, 0.1, 0.1, 0.1, 0.1, 2.5, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K_D | `[2.0, 0.1, 0.1, 0.1, 0.1, 2.0, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K_E | `[1.5, 0.1, 0.1, 0.1, 0.1, 1.5, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K_F | `[0.5, 0.1, 0.1, 0.1, 0.1, 3.0, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 5 → 0 |
| K_G | `[3.0, 0.1, 0.1, 0.1, 0.1, 0.5, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| legacy_5_6 | `[5.0, 0.1, 0.1, 0.1, 0.1, 6.0, 0.1, 0.1]` | flag_leakage | auto_approve | yes | 0.893492315669 | 0 → 5 |
| uniform_0.5 | `[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]` | flag_leakage | flag_leakage | no | 0.897183434541 | 0 → 1 |
| no_K | None | flag_leakage | flag_leakage | no | 0.897183434541 | 0 → 1 |

K_A–K_G all satisfy the numerical bounds. The legacy row is an out-of-range control. Uniform K and no K produce the same ordering because a uniform positive multiplier does not change argmax Q.

For 0 → 5 traces, the intermediate action remains flag_leakage with margin 0.894477329375, then flips after dim 5. For 5 → 0 traces (K_F), dim 5 already flips the action with margin 0.889007431891; dim 0 then brings the final margin to 0.893492315669. Thus this provider/scorer does not require a preceding contract read to admit volume context. The final enriched vector is `[0.93,0.101,0.0568,0.0,0.6731,0.82,0.3416,0.2494]`.

### Q values before and after each requested read

Vectors are ordered by dimensions 0–7. Q-before uses the pre-read vector and already-attempted mask. Q-after recomputes from the post-read vector and adds the just-attempted dimension to that mask. A masked Q is -1. Values below are rounded to 12 decimal places; threshold calculations use float64 without this rounding. The final Q-after is diagnostic: no third read was executed.

| Config | Read / dimension | Q before | Q after |
| --- | --- | --- | --- |
| K_A | 1 / 0 | `[1.422660000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` |
| K_A | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_B | 1 / 0 | `[1.185550000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` |
| K_B | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_C | 1 / 0 | `[1.422660000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.400000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.400000000000, 0.017168000000, 0.001000000000]` |
| K_C | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.400000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_D | 1 / 0 | `[0.948440000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.320000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.320000000000, 0.017168000000, 0.001000000000]` |
| K_D | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.320000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_E | 1 / 0 | `[0.711330000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.240000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.240000000000, 0.017168000000, 0.001000000000]` |
| K_E | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.240000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_F | 1 / 5 | `[0.237110000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.480000000000, 0.017168000000, 0.001000000000]` | `[0.264386838417, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_F | 2 / 0 | `[0.264386838417, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |
| K_G | 1 / 0 | `[1.422660000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.080000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.080000000000, 0.017168000000, 0.001000000000]` |
| K_G | 2 / 5 | `[-1.000000000000, 0.019980000000, 0.006682000000, 0.018000000000, 0.011462000000, 0.080000000000, 0.017168000000, 0.001000000000]` | `[-1.000000000000, 0.027576296868, 0.004486823545, 0.033782500000, 0.002849346541, -1.000000000000, 0.012804910817, 0.001000000000]` |

## Threshold search

### K0=3.0, every other non-dim5 K=0.1

All requested probes K5=2.5,2.0,1.5,1.0,0.5 pass, so the search continued below 0.5. K5=0.1 fails. Fifty bisection iterations on [0.1,3.0] bracket the transition at:

- Last failing lower bound: **0.12487499999999893**
- First passing upper bound: **0.12487500000000151**
- Analytic boundary: **K5=0.124875**, with a **strictly greater** condition for the desired branch.

The unweighted surface Q is `[0.474220000000, 0.199800000000, 0.066820000000, 0.180000000000, 0.114620000000, 0.160000000000, 0.171680000000, 0.010000000000]`. The two leading actions are flag_leakage and escalate_to_buyer. After dim 0 is read they remain the leading pair, and the unmasked Q values do not change. The largest remaining competitor is dim 1:

```text
Q1 = 0.1998 × 0.1 = 0.01998
Q5 = 0.16 × K5
select dim5 iff 0.16 × K5 > 0.01998
therefore K5 > 0.124875
```

At equality, NumPy argmax selects the earlier dimension 1; the decimal equality probe also failed. In continuous real values this is an infimum, not an attained minimum. K5=0.124874 fails; 0.124876 passes. K0=3 keeps dim 0 first throughout the reachable K5 range (its initial weighted Q is 1.42266, whereas dim 5 is at most 0.48). This gives a single monotone switch, rather than relying on bisection without checking the routing geometry.

### Does K0 need to exceed 0.5?

**No.** K_F (K0=0.5,K5=3, others=0.1) passes with reads 5 → 0. K0=0.1,K5=3, others=0.1 also passes. Even K0=K5=0.5 with the other weights at 0.1 passes with reads 0 → 5.

A cleaner initialization comparison keeps **every non-dim5 weight at 0.5**. Here dim 1 competes at Q1=0.0999, so:

```text
0.16 × K5 > 0.1998 × 0.5
K5 > 0.624375
```

Fifty bisection iterations yield failing lower bound **0.6243749999999985** and passing upper bound **0.624375000000001**. Decimal K5=0.624375 fails; 0.624376 passes. K5=0.62 fails, 0.64 passes. With K0=0.5, dim 5 overtakes dim 0 for the first read above K5=1.4819375; tested larger values continue to flip via 5 → 0.

### Additional probes

All rows start at flag_leakage with surface margin 0.890894753779. “Other K” covers dimensions 1,2,3,4,6,7.

| Probe | K0 | K5 | Other K | VLD action | Flip | Final margin | Dims |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| K0_3_K5_2.5 | 3 | 2.5 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K0_3_K5_2 | 3 | 2 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K0_3_K5_1.5 | 3 | 1.5 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K0_3_K5_1 | 3 | 1 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K0_3_K5_0.5 | 3 | 0.5 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| K0_3_K5_0.1 | 3 | 0.1 | 0.1 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| K0_0.5_K5_3 | 0.5 | 3 | 0.1 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| K0_0.1_K5_3 | 0.1 | 3 | 0.1 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| only_dim5_0.5 | 0.5 | 0.5 | 0.5 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| only_dim5_1 | 0.5 | 1 | 0.5 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| only_dim5_1.5 | 0.5 | 1.5 | 0.5 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| only_dim5_2 | 0.5 | 2 | 0.5 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| only_dim5_2.5 | 0.5 | 2.5 | 0.5 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| only_dim5_3 | 0.5 | 3 | 0.5 | auto_approve | yes | 0.893492315669 | 5 → 0 |
| threshold_0.124874 | 3 | 0.124874 | 0.1 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| threshold_0.124876 | 3 | 0.124876 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| threshold_0.624374 | 0.5 | 0.624374 | 0.5 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| threshold_0.624376 | 0.5 | 0.624376 | 0.5 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| lattice_0.62 | 0.5 | 0.62 | 0.5 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| lattice_0.64 | 0.5 | 0.64 | 0.5 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| recommended_0.7 | 0.5 | 0.7 | 0.5 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| recommended_1.0 | 0.5 | 1 | 0.5 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| floor_others_initial_0_5 | 0.5 | 0.5 | 0.1 | auto_approve | yes | 0.893492315669 | 0 → 5 |
| boundary_decimal | 3 | 0.124875 | 0.1 | flag_leakage | no | 0.897183434541 | 0 → 1 |
| boundary_decimal | 0.5 | 0.624375 | 0.5 | flag_leakage | no | 0.897183434541 | 0 → 1 |

## Learning effort and claim limits

Under the requested back-of-envelope model, a positive update to a selected dimension adds 0.02 from an initial 0.5, capped at 3.0. For a target above initialization, use `ceil((target-0.5)/0.02)`; for a strict boundary choose the next passing grid value.

| Target for dim 5 | Full +0.02 positive updates to dim 5 | Interpretation |
| --- | ---: | --- |
| Strictly above 0.624375 | 7 → K5=0.64 | First passing grid value with other K fixed at 0.5 |
| 0.70 | 10 | Smaller passing candidate |
| 1.00 | 25 | Recommended demo setting |
| 1.50 | 50 | Passes; volume context read first |
| 2.00 | 75 | Passes |
| 2.50 | 100 | Passes |
| 3.00 | 125 | Cap; unnecessary for this flip |

These are **credited positive updates to dimension 5**, not guaranteed totals of verified decisions. If each independent verified decision supplies one full positive dim-5 update and every other weight stays fixed, the counts coincide. At contribution rate f, the rough required decision count is N/f, before negative updates or publication gates. If other weights also learn, the routing boundary moves; locally the competition is K5 > 1.24875 × K1.

The lower 0.124875 threshold assumes a different state: K0=3 costs about 125 positive dim-0 updates, while the six other weights start at 0.5 and must be driven down to 0.1 (about 80 negative updates per dimension at -0.005). K5=0.5 already exceeds that threshold. Positive updates alone cannot produce the specified 0.1 weights. This is why the uniform-background recommendation is preferable for a learning-effort narrative. Counts per dimension cannot be added into an exact decision total without specifying which dimensions each eligible trace updates.

The existing [KUtilityStore updater](../../copilot_sdk/scoring/investigation.py) differs from the simplified model: a correct trace adds 0.02 per step, doubled to 0.04 when that step flips; incorrect traces subtract 0.005. A hypothetical sequence of four credited flipping steps could move K5 from 0.5 to 0.66. This does not establish a valid operational training path, and the new [§4.5 design](vld_e2e_architecture_design_2026-09-12.md#45-decision-q5--verified-feedback-k-lifecycle-and-credit-assignment) explicitly removes the raw flip bonus, scales credit by predictive utility, excludes synthetic/preseed cases from production K, and requires committed outcomes and checkpoint lineage. With its default maximum +0.02 contribution, seven updates is an optimistic lower bound, and 25 is only an idealized estimate for K5=1.0; smaller rewards require more events.

There is also an acquisition constraint: this invoice at uniform K reads dims 0 and 1, so it does not generate any dim-5 step to reward. Repeating this same cold-start showcase cannot by itself bootstrap K5. Other eligible decisions that acquire useful dim-5 evidence (or an authorized exploration policy) are needed. Searching the current SDK and S2P app source found no `.update_weights(` production caller. No lifecycle was exercised here, and no number of actual verified decisions is claimed to have occurred.

## Validation and provenance

The experiment independently recomputed squared-distance softmax probabilities for every scored vector and compared them with the investigator. Additional boundary/recommendation runs independently recomputed Q and checked each selected argmax. Every run checked equality between module-wrapper and class traces. A–G, the legacy/control cases, all coarse probes, 100 bisection probes, equality probes, and decimal/grid-neighbor probes completed successfully.

The following SHA-256 values identify the input snapshot. These files were hashed before and after the main sweep and remained identical during that sweep. They are not generated outputs.

| Input relative to workspace | SHA-256 |
| --- | --- |
| `copilot-sdk/real_centroids_v1.json` | `1d782457bfbf8349d7cedfa531a30b3007c1e9e08b378068a9e826d437215863` |
| `copilot-sdk/copilot_sdk/scoring/investigation.py` | `c711d8d624c07c3c4a2f405db048d22c73d50d283e3b328b9fe3fb733ad510ce` |
| `s2p-copilot/backend/app/vld_preseed.py` | `a370d16962432c9e424b42fb8584f0b029e06d9251d6cd9384bf1d3f4d1f2c26` |
| `s2p-copilot/backend/app/evidence_provider.py` | `7c3db1d38591bb89ad24bff3d9ee3282eea25bce7df7425aaab1a5ebef547ba9` |
| `s2p-copilot/backend/app/domains/s2p/config.py` | `be523ae44b7f00f8a5d4a49f9a08b024c8730623717b996a56398ee81dd19745` |
| `s2p-copilot/backend/app/main.py` | `beb2094079b6af9ff06f01556f8ecf6cbd82be48aaa4b2720b64aecc0921d001` |

During final verification, the scoring file changed independently of this task to SHA-256 `abb110252520e8354577769174b694da61f49f2a6702f5726d2cc156723e7aaa`. The embedded reproduction was rerun against that version. The 24 sweep/control/probe traces retained identical actions, flips, dimensions, Q values, and evidence; only margin rounding changed (maximum absolute difference below 5e-15), leaving every displayed margin unchanged. The threshold and additional-probe reproduction also passed. The table above retains the original measured snapshot hash; no source change was made by this task.

Relevant implementation references: [preseed](../../../s2p-copilot/backend/app/vld_preseed.py), [evidence provider](../../../s2p-copilot/backend/app/evidence_provider.py), [S2P factory](../../../s2p-copilot/backend/app/main.py), [investigator/Q/K updater](../../copilot_sdk/scoring/investigation.py), and [shared router](../../copilot_sdk/backend/investigation_router.py).

## Reproduction (no source file required)

Run from `copilot-sdk`. Paste the Python block below into a PowerShell single-quoted here-string, then pipe it to the requested venv interpreter as `python.exe -B -`. It writes JSON only to stdout and uses the preseed solely in memory. The first JSON object contains the complete sweep traces, including unrounded Q before/after; the second contains bisection brackets, trials, and additional probes. No test helper needs to be saved.

```python
import sys, json, hashlib, platform
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path('../s2p-copilot/backend').resolve()))
from app.vld_preseed import seed_vld_s2p_showcase
from app.evidence_provider import S2PEvidenceProvider
from copilot_sdk.scoring.investigation import VLDInvestigator, investigate
from dataclasses import asdict

sdk = Path.cwd()
paths = [sdk/'real_centroids_v1.json', sdk/'copilot_sdk/scoring/investigation.py', sdk.parent/'s2p-copilot/backend/app/vld_preseed.py', sdk.parent/'s2p-copilot/backend/app/evidence_provider.py', sdk.parent/'s2p-copilot/backend/app/domains/s2p/config.py', sdk.parent/'s2p-copilot/backend/app/main.py']
hashes = {str(p.relative_to(sdk.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
s = json.loads(paths[0].read_text(encoding='utf-8'))['copilots']['s2p']
data = seed_vld_s2p_showcase({})
row = next(r for r in data['invoices'] if r['invoice_id']=='VLD-S2P-2')
names, actions = s['factor_names'], s['action_names']
v = np.array([row['factors'][n] for n in names])
mu, sigma = np.array(s['all_category_mu'][row['category']]), np.array(s['sigma'])
inv = VLDInvestigator(mu, sigma, names, tau=s['tau'])
def run(label, k):
    provider = S2PEvidenceProvider(data, row['invoice_id'])
    t = inv.investigate(row['invoice_id'], row['category'], v, provider, budget=2, K_weights=k, gated_sources=set())
    wrapped = investigate(factors=v, category=row['category'], budget=2,
        evidence_provider=S2PEvidenceProvider(data,row['invoice_id']), mu=mu, sigma=sigma,
        tau=s['tau'],factor_names=names,k_weights=k,gated_sources=set(),decision_id=row['invoice_id'])
    assert wrapped == asdict(t)
    enriched, steps = set(), []
    for step in t.steps:
        _, pb = inv.score(step.v_before)
        qb = inv.compute_Q(step.v_before, pb, enriched, k)
        assert step.dimension == int(np.argmax(qb))
        enriched.add(step.dimension)
        _, pa = inv.score(step.v_after)
        qa = inv.compute_Q(step.v_after, pa, enriched, k)
        steps.append(dict(dimension=step.dimension, factor=step.factor_name, source=step.evidence_source,
            value=step.evidence_value, confidence=step.evidence_confidence, status=step.status,
            action_before=actions[step.action_before], action_after=actions[step.action_after],
            margin_before=step.margin_before, margin_after=step.margin_after,
            q_before=qb.tolist(), q_after=qa.tolist(), v_after=step.v_after))
    # Independent distance/softmax oracle for every scored vector.
    for vector in [v]+[st.v_after for st in t.steps]:
        d = np.sum((np.asarray(vector)-mu)**2 / np.maximum(sigma**2,0.001), axis=1)
        p = np.exp(-(d-d.min())/s['tau']); p /= p.sum()
        a, actual = inv.score(vector)
        assert a == int(np.argmin(d))
        np.testing.assert_allclose(actual,p,rtol=1e-13,atol=1e-15)
    return dict(label=label, k=k, surface_action=actions[t.surface_action], action=actions[t.final_action],
        flip=t.surface_action!=t.final_action, target_flip=actions[t.final_action]=='auto_approve',
        surface_margin=t.surface_margin, margin=t.final_margin, dims=[st.dimension for st in t.steps], steps=steps)
def weights(k0,k5,other=0.1):
    k=[other]*8; k[0]=k0; k[5]=k5; return k
configs = [('K_A',3,3),('K_B',2.5,3),('K_C',3,2.5),('K_D',2,2),('K_E',1.5,1.5),('K_F',0.5,3),('K_G',3,0.5)]
runs=[run(label,weights(k0,k5)) for label,k0,k5 in configs]
runs += [run('legacy_5_6',weights(5,6)),run('uniform_0.5',[0.5]*8),run('no_K',None)]
runs += [run('K0_3_K5_'+str(k5),weights(3,k5)) for k5 in [2.5,2,1.5,1,0.5,0.1]]
runs += [run('K0_'+str(k0)+'_K5_3',weights(k0,3)) for k0 in [0.5,0.1]]
runs += [run('only_dim5_'+str(k5),weights(0.5,k5,0.5)) for k5 in [0.5,1,1.5,2,2.5,3]]
print(json.dumps(dict(python=platform.python_version(),numpy=np.__version__,hashes=hashes,
    category=row['category'],factors=names,actions=actions,vector=v.tolist(),mu=mu.tolist(),
    sigma=sigma.tolist(),tau=s['tau'],provenance=s.get('provenance'),runs=runs)))
assert hashes == {str(p.relative_to(sdk.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

_, p = inv.score(v)
base_q = inv.compute_Q(v,p)
post0=v.copy();post0[0]=0.93
_, p0=inv.score(post0)
post_q=inv.compute_Q(post0,p0,{0})
def boundary(k0, other):
    lo, hi = 0.1, 3.0
    assert not run('lo',weights(k0,lo,other))['target_flip']
    assert run('hi',weights(k0,hi,other))['target_flip']
    trials=[]
    for i in range(50):
        mid=(lo+hi)/2
        flips=run('bisect',weights(k0,mid,other))['target_flip']
        trials.append([mid,flips])
        if flips: hi=mid
        else: lo=mid
    analytical=other*post_q[1]/post_q[5]
    return dict(k0=k0,other=other,lo=lo,hi=hi,analytical=analytical,
        below=run('boundary_below',weights(k0,lo,other)),
        above=run('boundary_above',weights(k0,hi,other)),
        at_decimal=run('boundary_decimal',weights(k0,round(analytical,6),other)),
        trials=trials)
boundaries=[boundary(3,0.1),boundary(0.5,0.5)]
extra=[run(label,weights(k0,k5,other)) for label,k0,k5,other in [
    ('threshold_0.124874',3,0.124874,0.1),('threshold_0.124876',3,0.124876,0.1),
    ('threshold_0.624374',0.5,0.624374,0.5),('threshold_0.624376',0.5,0.624376,0.5),
    ('lattice_0.62',0.5,0.62,0.5),('lattice_0.64',0.5,0.64,0.5),
    ('recommended_0.7',0.5,0.7,0.5),('recommended_1.0',0.5,1,0.5),
    ('floor_others_initial_0_5',0.5,0.5,0.1)]]
# Independent Q oracle, including top-two transition after evidence.
for result in extra:
    enriched=set()
    for step in result['steps']:
        vector=v if not enriched else np.asarray(result['steps'][0]['v_after'])
        a,p=inv.score(vector); ranked=np.argsort(p)[::-1]; aa,bb=ranked[:2]
        q=(1/np.maximum(sigma**2,0.001)/100 + np.abs(mu[aa]-mu[bb]) +
           np.abs((vector-mu[aa])**2-(vector-mu[bb])**2))*np.asarray(result['k'])
        for dim in enriched:q[dim]=-1
        np.testing.assert_allclose(q,step['q_before'],rtol=1e-14,atol=1e-15)
        enriched.add(step['dimension'])
print(json.dumps(dict(base_q=base_q.tolist(),post0_q=post_q.tolist(),boundaries=boundaries,extra=extra)))

```
