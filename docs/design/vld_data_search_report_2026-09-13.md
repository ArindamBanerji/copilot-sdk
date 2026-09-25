# VLD-DATA-SEARCH — Datasets 4–7

Report date: **2026-09-13**, as requested. Repository snapshot inspected during this session; no historical checkout was used.

## Scope and evidence rules

Searched `copilot-sdk`, `gen-ai-roi-demo-v4-v50`, `s2p-copilot`, and `ci-platform`: design/product/outreach documents, source, tests, saved experiment results, and relevant sample data. Searches included nested experiment directories, SOC `backend/data`, and text/XML members of design ZIP/DOCX archives. The design ZIP's dollar-figure matches duplicate the unpacked positioning documents. Dependency/build/cache directories were excluded. Seven legacy PDFs under SOC `support/docs` were inventoried but not text-extracted because no PDF reader was installed; negative findings below apply to the searched text and data, not inaccessible PDF contents.

All source references below are **workspace-relative path:line**, using the files' current one-based line numbers. JSON paths identify aggregates computed from saved data. “Computed here” means read-only arithmetic, not a newly executed experiment. Historical experiment results were not rerun.

**GROUNDED** means measured evidence for the particular claimed outcome, not merely a number stored in code. **ILLUSTRATIVE** means stipulated positioning/sample assumptions. **PROJECTED** means a model calculation, whose inputs may themselves be illustrative. A real software component exercised with synthetic inputs does not establish operational outcomes.

| Dataset | Finding | Verdict | Tier for the principal finding |
|---|---|---|---|
| 4 — Value unit | Dollar origins and illustrative units found; no measured cross-copilot dollars-per-recovered-decision dataset | PARTIAL | ILLUSTRATIVE |
| 5 — Abstention | Zero-investigation path, synthetic no-read metrics, and separate SOC decision-abstention experiments found | PARTIAL | REAL_COMPONENT |
| 6 — Hard tail | 250-case constructed benchmark and synthetic situation distributions found; natural prevalence missing | PARTIAL | SIMULATED |
| 7 — Real-scorer ρ | SOC component/fixture category-recovery measurement found; operational post-observation branch-routing measurement missing | PARTIAL | REAL_COMPONENT |

## DATASET 4: VALUE UNIT

### Found: the ~$0.9M/year origin

The derivation is explicit in `copilot-sdk/docs/design/blogs/new_docs/graph_native_separation_block_v8.md:64–70`.

| Quantity | Exact source figure | Derivation / status |
|---|---:|---|
| Hypothetical distributor revenue | $5B | Illustrative scale; line 64 |
| Addressable spend | ~$3B | Assumption; line 64 |
| Invoice leakage | 1% = $30M/year | $3B × 0.01; assumption |
| Recoverable pool | 40% = $12M/year | $30M × 0.40; assumption |
| Static decision quality | 71.7% | Borrowed SOC curve, applied to procurement |
| Quality after 1,000 verified approvals | 78.9% | Borrowed SOC curve; procurement confirmation explicitly pending |
| Static recovery | ~$8.6M/year | $12M × 0.717 = **$8,604,000**; line 66 |
| Compounding recovery | ~$9.5M/year | $12M × 0.789 = **$9,468,000**; line 67 |
| Incremental recovery | **~$0.9M/year** | $12M × (0.789 − 0.717) = **$864,000/year**, rounded; line 68 |

**Classification: ILLUSTRATIVE**, with projected arithmetic. Line 70 explicitly calls it “Modeled and illustrative.” It is not $900,000 measured in a customer deployment, nor a VLD-specific value-per-read estimate.

The underlying 71.7%→78.9% curve is a **realistic 50-seed simulation**, not procurement outcomes: `copilot-sdk/docs/design/ci_blog_v16_1.md:356`; the SOC claim-status statement explicitly labels the figures controlled synthetic rather than realized customer outcomes at `copilot-sdk/docs/design/soc_copilot_design_v5_11.md:5942`. Thus “measured security-copilot curve” in the positioning text must retain that experimental qualification.

A second occurrence is `copilot-sdk/docs/design/blogs/new_docs/graph_native_reasoning_hero_v23.md:199–209`: the same $30M/$12M pool, ~$8.6M and ~$9.5M recovery, and **~$0.9M/year** gap. It calls the figure modeled and labels its graphic “modeled / illustrative — not a forecast.” Line 206 also mentions **~$117M/year** across all platform levers at the same $5B scale; no derivation of that broader figure is supplied in that passage. It must not be substituted for the single-pool compounding dividend.

### Found: the $1.62M/year origin

This is a **DataOps Continental Tire demo trajectory**, not the preceding hypothetical distributor's compounding dividend.

| Source | Exact figure / significance | Classification |
|---|---|---|
| `copilot-sdk/docs/design/dataops_copilot_design_v1_9.md:24,35,2155,2186` | $1.62M storyboard/trajectory; line 35 says **$1.62M/yr DataOps**, alongside $680K/yr S2P | ILLUSTRATIVE end-state story |
| `copilot-sdk/docs/design/product/dataops_copilot_design_v1_9.md:24,35,2155,2186` | Duplicate product copy of those statements | Same evidence, not independent confirmation |
| `copilot-sdk/apps/dataops/backend/data/process_timeline.json:53–62` | `total_trajectory_per_year: 1620000`; `option_a_savings_per_year: 547000` | ILLUSTRATIVE; model source is `dataops_fixture` at line 10 and provenance is `sample` at line 86 |
| `copilot-sdk/apps/dataops/backend/data/celonis_process_data.json:68–88` | MATKL_V2 bridge recommendation **$547,000/year** (line 72); supplier-delta quarantine **$1,073,000/year** (line 78); total **$1,620,000/year** (line 83) | ILLUSTRATIVE sample data |
| `copilot-sdk/apps/dataops/backend/docs/autonomous_process_optimization.md:31–35` | $17.3M current exception cost, $7.1M target, $547K option A, $1.62M total trajectory | Sample/demo calibration |
| `copilot-sdk/docs/design/blogs/old_outreach/outreach_elevator_pitches_v4.md:550` | “DataOps ($1.62M/year saved)” | Repeats the story; no new measurement |
| `copilot-sdk/docs/design/CI_PLATFORM_INSIGHTS_v39.md:4410,4442` | “6 months, $1.62M/year saved” institutional-memory narrative | Design discussion, not realized savings |
| `copilot-sdk/docs/design/product_integrity_execution_strategy_v3_0.md:1523–1528` | Explicitly identifies $1.62M/yr as an end-state/after-N/target claim, never current-measured | Confirms illustrative status |

**Recoverable arithmetic:** $547,000 + $1,073,000 = **$1,620,000/year**. The two component amounts are stored constants; no measured cost study or formula deriving those two constants was found. This establishes an arithmetic reconciliation, not a historical first-author origin.

The separate exception-cost calibration provides **$47/investigation, 8,400 invoices/day, 12% current exceptions, 4.8% target exceptions** (`process_timeline.json:54–59`). At an assumed 365 days, those inputs calculate $17,292,240 and $6,916,896 annually. The file instead stores $17.3M and $7.1M. Neither that calculated difference nor the stored **$10.2M** difference equals $1.62M. Do not present exception-rate reduction as a derivation of the $1.62M trajectory.

### Per-copilot units and adjacent metrics

**A per-recovered-hard-case value table exists, but its author labels it “PLACEHOLDER — needs domain owner.”** Source: `copilot-sdk/docs/design/ci_vld_depth_memo_v13.md:775–783`.

| Copilot | Value per recovered hard case | Unit in source | Status |
|---|---:|---|---|
| SOC | 1.0 | missed-incident-equiv | ILLUSTRATIVE |
| DataOps | 0.6 | false-alert-equiv | ILLUSTRATIVE |
| S2P | 0.8 | leakage-$-equiv | ILLUSTRATIVE; not established dollars |
| Purchasing | 0.4 | margin-$-equiv | ILLUSTRATIVE; not established dollars |
| Trading | 0.3 | exec-quality-equiv | ILLUSTRATIVE |

**Reads saved does have a numerical per-copilot experiment.** RV-5 compares hierarchical fallback routing with flat RNN at the final 500-decision checkpoint, five seeds × 50 held-out cases per copilot. These are synthetic cases on exported geometry, with experiment-specific budgets. Source: `copilot-sdk/experiments/vld/rv5_hierarchical.json:3–29`, verdict at lines 1123457–1123488; readable summary at `copilot-sdk/experiments/vld/group_b_c_report.md:213`.

| Copilot | Flat reads/decision | Hierarchical reads/decision | Reads saved/decision | Accuracy change |
|---|---:|---:|---:|---:|
| DataOps | 2.000 | 1.784 | 0.216 | −4.4 percentage points |
| Trading | 2.000 | 1.952 | 0.048 | −3.6 pp |
| Purchasing | 2.000 | 1.944 | 0.056 | 0.0 pp |
| SOC | 2.000 | 1.816 | 0.184 | −15.6 pp |
| S2P | 2.000 | 2.000 | 0.000 | 0.0 pp |

These reductions are measured **within the synthetic harness**, not realized analyst time or dollar savings. Only Purchasing meets the experiment's per-copilot no-accuracy-loss/strictly-fewer-reads gate; the overall verdict is do not keep. “Errors avoided” is available as benchmark saves/hurts in Dataset 6, not a measured annual operating metric.

Additional value/time material found:

- **S2P $680K/year**: explicitly modeled as **$500M spend × 0.136%**. **Purchasing $15K–$45K**: modeled as a **$1.5M restaurant × 1–3 percentage points food-cost improvement**. Sources: `copilot-sdk/docs/design/blogs/old_outreach/outreach_elevator_pitches_v4.md:1056,1067–1068`. These are PROJECTED from illustrative inputs.
- **SOC 30.85 minutes/alert**, CI **[29.90, 31.81]**, **30 personas**: reported as SANS-calibrated CL-ECON-MEASURED in `copilot-sdk/docs/design/soc_copilot_design_v5_11.md:589`. `copilot-sdk/docs/design/blogs/cga_production_paper_v9_4.md:452` references a **44-minute baseline**, SANS survey **N=422**, and ROI **$829K healthcare / $2.79M FinServ / $523K midmarket per year at 200 alerts/day**. These documents label the time claim measured, but no underlying timed analyst-session dataset establishing these numbers as customer outcomes was located. Treat it as a source-reported calibrated result; realized dollars remain unsubstantiated.
- **SOC/shared frozen ROI calculator**: assumes **$85/hour, 44 minutes unassisted, 200 alerts/day, 365 days/year, 4% auto-approval**, plus **15 minutes saved per assisted alert**, **8% duplicate triage**, and an **8-hour daily coverage gap**. Formulas are in `copilot-sdk/copilot_sdk/framework/economics.py:19–69`, mirrored in SOC `backend/app/framework/economics.py`. PROJECTED, not a time study.
- **SOC tab ROI** separately uses **decisions/day × 365 × 0.25 hours × $75/hour** (`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3389–3413`). Its methodology text cites SANS/Hackett, but that attribution is not an independently verified source dataset in this search. Do not merge its $75 rate with the calculator's $85 rate.
- **DataOps time/headcount narratives**: 400 alerts/day, 45% noise, 160 engineer-hours/day; subsequent 220 and 180 alerts/day and claimed 88/70 hours freed (`dataops_copilot_design_v1_9.md:388–396`); 12 engineers, 40% time on triage, 55% auto-resolution, “effectively become 18” (lines 430–435). ILLUSTRATIVE. The first time calculation is inconsistent: at 160/400 = 0.4 hours/alert, 220 remaining alerts imply **72 hours freed**, not 88. No measured staffing dataset was found.

**Origin story:** ~$0.9M is a rounded $864K modeled incremental-capture dividend using a borrowed simulated SOC quality curve; $1.62M is a separate sample DataOps trajectory reconciled by two stipulated recommendation amounts. Neither is a grounded per-copilot VLD value unit.

**VERDICT: PARTIAL**  
**TIER: ILLUSTRATIVE** — for the dollar/value-unit claims; reads-saved results are component/harness evidence.  
**RECOMMENDED CLAIM:** The repositories provide illustrative economic scenarios and synthetic per-copilot read-efficiency measurements, but do not establish realized dollar value per VLD decision.

## DATASET 5: ABSTENTION / RISK COVERAGE

### Runtime: S1 declines investigation, not the final decision

The requested import `from copilot_sdk.scoring.investigation import SituationClassifier` fails. The classifier exists in **`copilot_sdk/scoring/situation_classifier.py:91`**; this was confirmed by read-only import/introspection with bytecode writing disabled.

Current fallback (`situation_classifier.py:122–129`):

- Precision-weighted nearest-centroid distance `d_min < 0.05` → **S1**.
- `d_min > 0.5` → **S6**.
- Otherwise → **S3**.
- Fallback confidence is the constant **0.5**, not an empirically calibrated probability.
- Runtime budgets are **S1=0, S2=3, S3=1, S4=2, S5=3, S6=4** (lines 11–18).
- No fitted model is loaded by the current default `SituationClassifier()` calls; without a supplied model the fallback never emits S2/S4/S5.

Current application wiring supplies that classifier in DataOps `copilot-sdk/apps/dataops/backend/app/main.py:956`, Purchasing `.../apps/purchasing/backend/app/main.py:848`, Trading `.../apps/trading/backend/app/main.py:140–141`, SOC `gen-ai-roi-demo-v4-v50/backend/app/main.py:211`, and S2P `s2p-copilot/backend/app/main.py:346`. Older reports saying SOC/Trading lacked a classifier describe earlier wiring.

The router consults the classifier **only when the request omits a budget**, then uses its recommended budget: `copilot-sdk/copilot_sdk/backend/investigation_router.py:74–81`. An explicit budget bypasses that choice.

`VLDInvestigator.investigate` clamps budget to ≥0, computes the surface action, skips the loop at zero, then **still predicts and returns a final action** (`copilot-sdk/copilot_sdk/scoring/investigation.py:214,234–241,329–343`). Therefore S1/B=0 is a no-read path. It is not evidence that the system withholds an uncertain action.

The reviewed scorer and scoring/conservation routers contain no dedicated VLD decision-abstention rate or acted-only accuracy. Conservation status uses verified/correct/total decision counts; `q = correct_count / verified_count` in `copilot-sdk/copilot_sdk/backend/conservation_utils.py:89–95`. This is verified-outcome accuracy, not accuracy on all arriving decisions or a separately defined acted set. Source inspection of the status endpoint is at `copilot-sdk/copilot_sdk/backend/conservation_router.py:44–62`; no live service was queried.

### Saved metrics: three different meanings

**1. RV-4 “S1 abstain calibration” is a no-investigation rate on constructed easy cases.**

The 27 top-level JSON files in `copilot-sdk/experiments/vld` were searched for `abstain/acted/skipped/s1_count`. The substantive top-level match is **`rv4_risk_sensitive_results.json`**. Nested matches also include narrative strings, which are not abstention measurements.

The older RV-4 harness constructs 20 extra easy cases per checkpoint, with full=surface, no informative dimensions, and scorer-defined truth. It chooses zero budget when surface margin ≥**0.70**. Its metric is **no-read cases / 20 easy cases**, not correctness conditional on decision abstention (`copilot-sdk/scripts/routing_variant_risk_sensitive.py:33–34,65–84,163–178`).

| Copilot | Adaptive-budget S1 no-read rate | Final-checkpoint equivalent count across 5 × 20 easy cases | JSON line |
|---|---:|---:|---:|
| SOC | 0.52 = 52% | 52/100 | 61789 |
| DataOps | 1.00 = 100% | 100/100 | 61825 |
| S2P | 0.44 = 44% | 44/100 | 61861 |
| Purchasing | 0.48 = 48% | 48/100 | 61897 |
| Trading | 0.67 = 67% | 67/100 | 61933 |

Counts are reconstructed from the equal-size final-checkpoint seed averages. Uniform-fixed and risk-fixed have the same rates; Thompson+risk rates are **59%, 100%, 41%, 43%, 52%**, respectively. Source: that JSON's summary, lines 61779–61957; `copilot-sdk/experiments/vld/rv4_ke45_report.md:7–15`. Overall verdict: **KILL_OR_QUALIFY**. This margin-based experiment is distinct from the current distance-based S1 fallback and from the differently named `rv4_risk_sensitive.json` experiment.

RV-5 also permits deriving S1 no-read rates at its final checkpoint: **DataOps 4/250=1.6%, Trading 6/250=2.4%, Purchasing 7/250=2.8%, SOC 0/250, S2P 0/250**. These are synthetic distribution counts, not calibrated abstention; the exact aggregation and source anchors appear in Dataset 6.

**2. SOC has genuine decision-abstention experiments with acted-only accuracy.**

`gen-ai-roi-demo-v4-v50/backend/data/sprint/b7_abstain_disagreement.json:2–15`:

| Metric | Saved value |
|---|---:|
| Eligible synthetic fixture alerts | **543** = 469 + 74 |
| Abstained | **469** |
| Abstention rate | **0.8637200736648251 = 86.372007%** |
| Committed / action coverage | **74 / 13.627993%** |
| Accuracy on committed actions | **0.17567567567567569 = 13/74 = 17.567568%** |
| Single-pass accuracy on the same committed subset | **0.21621621621621623 = 16/74 = 21.621622%** |
| Paired accuracy difference | **−0.04054054054054054 = −4.054054 pp** |
| Category-routing ρ on committed subset | **0.7432432432432432 = 55/74** |
| Saved verdict | **ARCH: this option does not recover positive action value** |

Code explicitly skips disagreeing route/scoring geometries and computes accuracy only over retained cases: `gen-ai-roi-demo-v4-v50/backend/scripts/sprint/sprint_lib.py:269–310`. Thus **yes**, acted-only accuracy exists in an offline experiment. It must not be compared directly with an all-alert accuracy without naming the different denominator. If abstentions are counted as unsuccessful outcomes, correct committed actions / all eligible cases is **13/543 = 2.394107%**; this arithmetic is not the JSON's `accuracy`.

**3. “ABSTENTION IMPROVES” can mean abstain on everything.**

`gen-ai-roi-demo-v4-v50/backend/data/sprint/combined_dual_abstain.json:18–37` selects a SOC margin threshold of **0.1**, abstaining on **543/543 = 100%**, with **0 committed** and utility **−1.0 per case** under its SOC penalty model. Its stored accuracy **0.0** is an empty-set convention; empirical acted-only accuracy is **undefined**.

The file separately stores always-act dual-centroid accuracy **0.22283609576427257** and utilities (lines 2–16). Its strategy evaluator separately computes committed accuracy and the matched single-pass subset (`backend/scripts/sprint/combined_dual_abstain.py:97–132`). This is utility optimization on a synthetic fixture, not evidence of useful high-accuracy coverage.

Synthetic abstention sweeps also exist in `copilot-sdk/scripts/vld_validation_sims_v3.py:474–514` and `vld_validation_sims_v4.py:487–534`; they calculate committed accuracy and penalized utility. Their presence alone does not supply a deployed abstention rate.

### Can the paper quantify “knows what it doesn't know”?

**Not as a demonstrated operational capability.** There is no located operational risk–coverage curve, calibrated abstention threshold, or favorable held-out action-accuracy/coverage result supporting that sentence. S1 means an easy case requiring no extra reads; B7 withholds most cases while underperforming its matched comparator on retained actions.

**VERDICT: PARTIAL**  
**TIER: REAL_COMPONENT** — code paths and fixture experiments; no operational calibration.  
**RECOMMENDED CLAIM:** The implementation can skip investigation and offline experiments can defer decisions, but calibrated selective action accuracy on operational data remains unestablished.

## DATASET 6: HARD-TAIL DETAIL

### What 57:0 / +22.8% actually means

The exact table appears in `copilot-sdk/docs/design/ci_vld_architecture_prepaper_v10.md:944–960`, also v9 at lines 1208–1224. It is **250 Astra-generated scenarios, 50 per copilot, at B=3 graph reads per decision**. Correct actions are determined by enriched centroid geometry (`v10:924–928`), not independently observed operational outcomes.

| Copilot | N | Single-pass correct | VLD correct | Saves | Hurts | Absolute uplift |
|---|---:|---:|---:|---:|---:|---:|
| SOC | 50 | 5/50 = 10% | 9/50 = 18% | 4 | 0 | +8 pp |
| S2P | 50 | 15/50 = 30% | 27/50 = 54% | 12 | 0 | +24 pp |
| DataOps | 50 | 26/50 = 52% | 38/50 = 76% | 12 | 0 | +24 pp |
| Trading | 50 | 22/50 = 44% | 40/50 = 80% | 18 | 0 | +36 pp |
| Purchasing | 50 | 23/50 = 46% | 34/50 = 68% | 11 | 0 | +22 pp |
| **Total** | **250** | **91/250 = 36.4%** | **148/250 = 59.2%** | **57** | **0** | **+22.8 pp** |

Counts/aggregate accuracies are reconstructed from the source's 50-case denominators. **+22.8% in the source is a 22.8-percentage-point increase**, not a 22.8% relative increase; relative uplift is **57/91 = 62.637363%**.

**57:0** counts wrong→right versus right→wrong transitions. The table also displays **114:1**; that is not an ordinary empirical saves/hurts ratio because the observed hurts denominator is zero. The displayed finite ratio has no derivation in the cited table; use raw counts.

Zero hurts means **0/91 initially correct cases degraded** (or 0/250 when normalized over every scenario), not a universal no-harm guarantee. Version 10 explicitly restricts the claim to the constructed suite at line 123. The inline caveat is prescribed in `copilot-sdk/docs/design/ci_vld_prepaper_v8_fixlist_and_drafts.md:20–23`: natural-prevalence uplift is unmeasured.

Budget sensitivity, same source `v10:970–978`: at B=2/B=3/B=4, saves are SOC **0/4/13**, S2P **6/12/14**, DataOps **8/12/15**, Trading **13/18/22**, Purchasing **11/11/11**, with zero reported hurts.

**Artifact distinction:** the exact headline table is source-reported; no separate matching 57-save JSON run aggregate was identified. Other saved with-without reports describe a different evaluation: `copilot-sdk/experiments/vld/results/case_studies_soc_astra.md:1–13` labels itself **PLANTED POSITIVE CONTROL**, reporting **43 saves, 0 hurts, 2 both-wrong out of 45 multi-hop cases**. Those counts cannot be substituted for the B=3 250-case table.

### What fraction is hard?

**Natural/operational S4/S5/S6 prevalence: NOT FOUND.** Version 10 explicitly lists real operational with-without data as **OPEN**, needed to measure situation prevalence and uplift (`ci_vld_architecture_prepaper_v10.md:1169`).

Three existing fractions answer different questions:

1. **Constructed Astra mixture:** each 50-case suite has **30 strong (60%), 10 moderate (20%), 5 flat (10%), 5 ρ=0.50 instrument checks (10%)** (`v10:938–942`). Thus 45/50 are non-flat cases by construction. “Strong,” “moderate,” and “non-flat” are not an observed S4/S5/S6 prevalence estimate.
2. **Earlier synthetic S1–S6 generator:** default weights are **S1 20%, S2 10%, S3 25%, S4 25%, S5 10%, S6 10%**, giving **S4+S5+S6 = 45%** (`copilot-sdk/experiments/vld/scripts/vld_experiments_v2.py:74–85`). Saved Round-v3 totals confirm **100/50/125/125/50/50 out of 500** in each of its two shapes: `gen-ai-roi-demo-v4-v50/backend/pub_charts/vld_experiments_v3_results.json:55–119` and its second shape. This is an imposed experimental mixture.
3. **Current fallback classifier on RV-5 synthetic exported-geometry cases:** actual saved situation counts exist, but are not production traffic.

The following RV-5 table is **computed here** by summing `results[copilot].HIERARCHICAL.seed_runs[*].checkpoints[-1].situation_counts`: final checkpoint 500, **5 seeds × 50 cases = 250 cases per copilot**.

| Copilot | S1 | S2 | S3 | S4 | S5 | S6 | S4+S5+S6 fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| DataOps | 4 | 0 | 200 | 0 | 0 | 46 | **46/250 = 18.4%** |
| Trading | 6 | 0 | 244 | 0 | 0 | 0 | **0/250 = 0%** |
| Purchasing | 7 | 0 | 243 | 0 | 0 | 0 | **0/250 = 0%** |
| SOC | 0 | 0 | 204 | 0 | 0 | 46 | **46/250 = 18.4%** |
| S2P | 0 | 0 | 250 | 0 | 0 | 0 | **0/250 = 0%** |

Source file: `copilot-sdk/experiments/vld/rv5_hierarchical.json`; per-domain hierarchical seed-run sections begin at **107808, 340908, 575013, 789896, 1010030**, respectively. Counters are emitted by `copilot-sdk/scripts/ri5_rich_k_state.py:261–271`. Across **all 10 checkpoint evaluations per seed** (2,500 synthetic evaluations per domain), S6 counts are **545/2/0/498/6**, respectively, and S1 counts **14/60/83/0/0**. Neither aggregation estimates natural prevalence, and the all-checkpoint observations are not independent operational decisions.

S2/S4/S5 zeros reflect the **fallback's inability to emit those labels**. A zero here cannot mean those kinds of hard cases never occur. RV-5 also uses experimental budgets **S1=0, S2=1, S3=2, S4=3, S5=2, S6=1**, unlike runtime budgets; see `rv5_hierarchical.json:25–28` and `copilot-sdk/scripts/ri5_rich_k_state.py:27`.

Finally, the depth memo supplies **assumed** all-decision hard-tail fractions: **SOC 18%, DataOps 22%, S2P 15%, Purchasing 20%, Trading 12%**. Its assumed conditional fractions within that tail are **70%, 60%, 40%, 20%, 15%**, respectively (`copilot-sdk/docs/design/ci_vld_depth_memo_v13.md:775–783`). These are illustrative model parameters, not measured classifier distributions.

### Can we say “+Y% on the X% that are genuinely hard”?

**No operational X is established.** The defensible Y is **+22.8 pp on this constructed 250-scenario suite**. Multiplying it by an assumed tail fraction, a generator's 45%, or RV-5 fallback frequencies would combine different populations and protocols. A production claim needs a predeclared hard-case definition, a representative denominator, and paired outcomes within that same slice.

**VERDICT: PARTIAL**  
**TIER: SIMULATED**  
**RECOMMENDED CLAIM:** On 250 constructed Astra scenarios at B=3, the source reports 57 corrections and zero degradations, raising accuracy from 36.4% to 59.2%; natural hard-tail prevalence and operational uplift remain unmeasured.

## DATASET 7: ρ ON REAL SCORER (O-1)

### Distinguish three quantities

- **ρ as routing success:** fraction of correct branch/category choices, depending on the experiment's truth definition.
- **r as correlation:** association across conditions; **r=0.986 is not a 98.6% routing success rate**.
- **Q-ranking correlations:** association between a dimension ranking and a synthetic counterfactual improvement; neither category recovery nor operational branch accuracy.

The math synopsis also uses ρ for cross-source correlation and Fisher/weight-rank correspondence; those are unrelated to O-1 (`copilot-sdk/docs/design/math_synopsis_v18.md:1085,2253–2255`). The claims registry's S2P covariance ρ≈0.43 and >0.60 factor pairs likewise are not VLD routing evidence (`gen-ai-roi-demo-v4-v50/docs/claims_registry_v6.md:237–241`).

### Sim-1 r=0.986: controlled instrument calibration

`copilot-sdk/docs/design/vld_graph_reasoning_architecture_v4.md:262–273` gives:

| Controlled ρ | VLD accuracy | Breadth | Random | VLD − random |
|---|---:|---:|---:|---:|
| 0.30 | 0.586 | 0.688 | 0.680 | −0.094 |
| 0.50 | 0.684 | 0.698 | 0.685 | −0.001 |
| 0.70 | 0.825 | 0.667 | 0.674 | +0.151 |
| 0.90 | 0.955 | 0.695 | 0.686 | +0.269 |

Its **correlation(Δ, ρ−0.5) = 0.986** calibrates the constructed instrument. The document explicitly says it does not confirm the value model on real data.

The matching two-branch Sim-1 implementation is **`copilot-sdk/scripts/vld_validation_sims.py`**, rather than assuming every similarly named v4 file is the same experiment:

- Synthetic binary outcomes and branch-A/branch-B evidence; ρ controls surface informativeness (`37–49`).
- **8 dimensions**, distractor **0.4**, ρ from **0.30 to 1.00 in 0.05 steps** (15 settings), RNG **42**, **B=1** (`229–267`).
- Function default **2,000 cases/setting**; main entry point requests **3,000 cases/setting** (`456`). The cited document does not preserve a separate run manifest proving which count generated its rounded table.
- Computes **Pearson correlation** through `np.corrcoef(ρ−0.5, accuracy_VLD−accuracy_random)` (`304–308`), not per-decision Spearman routing quality.

This is **SIMULATED**, with a purpose-built centroid scorer. The later six-branch scripts use a different chance baseline and must not be conflated with this experiment.

### A real-component measurement exists: SOC Phase 1b

**Found:** `gen-ai-roi-demo-v4-v50/backend/data/rho_measurement_report.json`, corroborated by `backend/docs/session_state.md:96–166` (recorded September 8). This supersedes an unqualified “no ρ measurement exists,” but it does not close the original operational O-1 question.

| Metric | Exact saved value | Source line |
|---|---:|---:|
| Evaluated / score-keyed alerts | **543 / 543** | 66–80 |
| Underlying fixture decision rows | **4,862** | 77 |
| VLD category recovery, original and stripped alerts | **0.6850828729281768 = 372/543** | 64–65 |
| Majority category recovery | **0.3001841620626151 = 163/543** | 61–62 |
| Expected uniform random category recovery | **0.16666666666666666 = 1/6** | 63 |
| Content comparator | **1.0**, label-informed diagnostic | 60; caveat 14 |
| VLD final-action accuracy | **0.31307550644567217 = 170/543** | 8 |
| Single-pass final-action accuracy | **0.5377532228360957 = 292/543** | 7 |
| Final-action accuracy difference | **−0.22467771639042355 = −22.467772 pp** | 17 |

Computed category-recovery improvement over majority is **209/543 = 0.3848987108655617**, or **+38.489871 pp**, approximately **2.2822×** the majority baseline. This is a routing/category result, while the same artifact's action comparison is negative.

The report also stores breadth/content/majority/random **final-action** accuracies **0.2596685082872928 / 0.3683241252302026 / 0.425414364640884 / 0.3406998158379374** (lines 3–6). Do not compare those to category ρ as though they were the same metric.

Margin quartiles (lines 28–51) give category recovery:
**64/136 = 0.47058823529411764**, **70/136 = 0.5147058823529411**, **106/136 = 0.7794117647058824**, **132/135 = 0.9777777777777777**. These are useful fixture diagnostics, not a measured operational hard-tail distribution or abstention calibration.

### What geometry, data and truth were actually used?

`gen-ai-roi-demo-v4-v50/backend/scripts/measure_rho.py:129–171` builds **`SOCDomainConfig().build_profile_scorer()`**, uses `FixtureFactorProvider` and `FixtureGraphStore`, and compares the route selected from **v0, before investigation**, to the alert's **category**. It separately evaluates stripped category/alert-type fields (lines 179–197). The majority category is selected from the evaluation fixture itself (line 137), not from an independent training split.

The saved report explicitly states (`rho_measurement_report.json:11–15`):

- Deterministic **synthetic SOC seed fixture**, not live production outcomes.
- Factor vectors from fixture decision rows keyed by alert ID, computable without AGE.
- Content comparator uses the label under test.
- Action truth is inferred by majority vote among “correct” fixture decisions.

Thus this is **REAL_COMPONENT + synthetic fixture data**, using configured geometry rather than a contemporaneous production-trained geometry snapshot. It is **category recovery at the initial state**, not independently adjudicated post-first-read branch utility. The corroborating session notes expressly say so (`session_state.md:163–166`).

A historical later note reports dual-centroid **ρ=0.6850828729281768, Δ=+0.07182320441988951**, with a **synthetic-training caveat** (`backend/docs/session_state.md:490`). This is not a universal result: the separately saved bootstrapped-centroid validation reports routed action accuracy **0.3775322283609576** versus **0.5193370165745856** single pass, Δ **−0.14180478821362802**, while retaining ρ **0.6850828729281768** (`backend/data/sprint/c_validate_best_bootstrapped.json:18–28`). These artifacts use different scoring geometry/protocols; do not merge them into one experiment or infer operational value from a positive routing score.

### Is original O-1 closed? Can we claim “ρ > comparator on real geometry”?

**Only with explicit qualification.** The original open question is “Is ρ > comparator for CI's real scorer?” (`copilot-sdk/docs/design/vld_graph_reasoning_architecture_v4.md:552`). Its operational R1 interpretation needs intermediate observations and independently labeled correct branches. The structural audit documents that missing data at `copilot-sdk/docs/design/soc_rho_structural_feasibility_audit_2026-09-08.md:5,40,414–444`. Its zero evaluable cases/null ρ refer to that stricter design, not the subsequent 543-case category proxy.

No saved independently adjudicated, post-first-read operational O-1 measurement was located. The strongest available statement is **ρ above majority on the SOC component's synthetic category-recovery fixture**, naming the denominator and the adverse final-action result.

Other code/results do not close the gap:

- `copilot-sdk/experiments/vld/data/*_stage1.json` and `experiments/vld/scripts/vld_universal_eval_v2.py:137–171` stratify on **`rho_planted`**, which is a fixture parameter, not measured production routing accuracy.
- `copilot-sdk/experiments/vld/scripts/vld_math_validation_v1.py:300–321` computes Spearman Q-versus-counterfactual-ΔP correlation. Saved mean values are **0.1761 (SOC-like), 0.0485 (Purchasing-like), 0.0729 (complex)** in `gen-ai-roi-demo-v4-v50/backend/pub_charts/vld_math_validation_results.json` under each shape's `q1_mean_r`. These are synthetic ranking measurements.
- Later exported-geometry routing experiments define routing quality as **informative reads / actual reads** against synthetic useful-dimension labels. Their geometry export includes preset/startup state, unit-sigma fallback and **live_age_verified=false** (`copilot-sdk/docs/design/ci_vld_architecture_prepaper_v10.md:1041,1309,1333–1346`). They are not another measurement of Phase-1b category ρ or operational O-1.

**VERDICT: PARTIAL**  
**TIER: REAL_COMPONENT** — with synthetic fixtures; Sim-1 itself is SIMULATED.  
**RECOMMENDED CLAIM:** On 543 synthetic SOC fixture alerts, the configured scorer/router recovered categories at 68.51% versus 30.02% for majority routing, while final-action accuracy fell from 53.78% to 31.31%; operational branch-routing ρ remains unmeasured.

## Post-checks and preservation

Only this new report was created. No git commands, source edits, experiment reruns, or application writes were performed. Python introspection used the requested virtual environment and `-B` to disable bytecode writes.

The three requested source hashes were captured before the search and matched exactly in the final verification:

| Source under copilot-sdk | SHA-256 before and after search |
|---|---|
| `copilot_sdk/scoring/investigation.py` | `3441dcbdb67a93e231ceda9827db36b46413e5d2fd29e750e3310caf1a2df6b4` |
| `copilot_sdk/backend/investigation_router.py` | `08f4df7ad872a6cf0dc53c0bd7250fe854ca7481e508aa592b35fe06440a744b` |
| `copilot_sdk/scoring/scorer.py` | `24ac9e49a070e0f9421fa0e3e7417a828c0ec88610ef906ce4987311c721b460` |

**POST-1: PASS** — the report exists and its first 30 lines were read back. **POST-2: PASS** — all three source hashes match their pre-search values. The four dataset sections and their verdict/tier/recommended-claim fields also passed a structure check. These checks verify report creation and preservation of the three named source files; they are not a repository-wide before/after hash audit.
