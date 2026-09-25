# VLD centroid and preseed gap analysis — 2026-09-11

Status: **design only; no implementation**. Scope: the supplied offline export, read-only local SQLite snapshots, production scoring/provider source, and numerical experiments run during this audit. No live AGE connection or application startup was used.

## 1. Decision and scope

The proposed profile explanation is only partly right about runtime differences, and wrong about the immediate cause:

- **The Trading and Purchasing checkpoints really contain identical action rows.** The export loads them correctly. The demo-bundle generator groups vectors by category, then copies the same mean into every action slot: copilot-sdk/scripts/regenerate_demo_bundles.py:322 and :336.
- **The export is incomplete as an application-startup snapshot.** Apps subsequently restore L5 centroids. Trading has six such rows; Purchasing has none locally. S2P also changes after L5 restoration. The export explicitly omits startup restoration: copilot-sdk/tests/vld_validation_report.py:186 and :207. Runtime restoration: copilot-sdk/apps/trading/backend/app/main.py:474; copilot-sdk/apps/purchasing/backend/app/main.py:581; s2p-copilot/backend/app/main.py:249.
- Five of the six differentiated-copilot flip contracts have concrete solutions against the supplied category tensors with unchanged provider evidence. **Original SOC-2 cannot satisfy all three requirements** with threat-intelligence read 2 returning None followed by history read 3. Section 5 supplies a numerical infeasibility certificate and a feasible, explicitly revised identity-evidence story.
- These are **geometry-compatible demo fixtures**, not an estimate of routing accuracy, a paper-quality dataset, or proof of live-app readiness. S2P must be pinned and retuned against the selected post-startup snapshot before rollout.

All paths below are relative to the workspace root. Line references refer to source as inspected on this audit. Numerical findings are recomputations using those sources, not embedded source constants unless stated.

Input: copilot-sdk/real_centroids_v1.json  
SHA-256: 074a20de5515b5945f92235f46b904c3454104ea4b54752aade0a92e707e63d6

### Correct computation contract

1. Select all_category_mu[scenario.category], not the top-level mu slice. The latter is explicitly the first category: copilot-sdk/tests/extract_real_centroids.py:5; actual routing slices at copilot-sdk/copilot_sdk/backend/investigation_router.py:142.
2. Use sigma=ones and tau=0.1 for this export. Score with squared Euclidean distance and softmax(-distance/tau), then top-two probability margin: copilot-sdk/copilot_sdk/scoring/investigation.py:66 and :76.
3. Unit sigma does **not** make Q leverage-only. With K absent, the exact formula is:

    Q_k = 0.01 + |mu[a1,k] - mu[a2,k]| + |(v_k - mu[a1,k])^2 - (v_k - mu[a2,k])^2|

   a1/a2 are recomputed from the current probabilities. Already attempted dimensions receive -1. Source: copilot-sdk/copilot_sdk/scoring/investigation.py:95 and :102.
4. Recompute Q after each attempted read. None consumes budget and marks the dimension attempted, but produces no successful trace step: copilot-sdk/copilot_sdk/scoring/investigation.py:131 and :138.
5. Gated sources update v_k = confidence * raw_value + (1-confidence) * v_k; other sources overwrite the dimension. Source: copilot-sdk/copilot_sdk/scoring/investigation.py:143. SOC gates identity_graph/threat_intel at gen-ai-roi-demo-v4-v50/backend/app/main.py:236; DataOps gates schema_registry/dependency_graph at copilot-sdk/apps/dataops/backend/app/main.py:943; S2P supplies no gates at s2p-copilot/backend/app/main.py:324.
6. All flip proposals below require an explicit budget=2 and no K weights. This is the existing router's supported request contract, not a proposed production modification: copilot-sdk/copilot_sdk/backend/investigation_router.py:65.

The supplied diagnostic snippets omit Q's centroid-separation term, freeze the first Q ordering for both hops, omit source gating, and use the wrong category for some cases. They should not be used to accept replacement seeds.

## 2. Trading and Purchasing: root cause and actual construction

### 2.1 Profiles and persistence

| Profile | No injected graph store | When a store is injected |
| --- | --- | --- |
| test | Creates InMemoryGraphStore; then reads checkpoints and falls back to the preset only if absent | Reads the supplied store's checkpoint; no test-specific centroid tensor |
| development | Uses SQLiteGraphStore at db_path | Reads the supplied store's checkpoint |
| production | Raises: a store must be injected | Requires AGE-backed storage; rejects SQLite/InMemory primary; reads the supplied store's checkpoint |

Source: copilot-sdk/copilot_sdk/scoring/scorer.py:269, :282, :287, :294, :301 and :320. The latest checkpoint's nonempty factor_names_hash can force fallback if it mismatches the current schema (:327); otherwise the preset bootstrap is used only when centroids is None (:338). Empty legacy hashes in these two databases do not trigger rejection.

The application path is FreshScorerProxy → CompoundingScorer.from_preset(graph_store=..., profile=...), not a different geometry-producing profile. Source: copilot-sdk/copilot_sdk/backend/scorer_proxy.py:31; Trading construction copilot-sdk/apps/trading/backend/app/main.py:375; Purchasing construction copilot-sdk/apps/purchasing/backend/app/main.py:515.

The sweep copies each SQLite database opened with mode=ro into an in-memory store, injects that store, and checks tensor equality with the loaded checkpoint. Source: copilot-sdk/tests/vld_validation_report.py:173, :177, :188 and :195. extract_real_centroids.py delegates to this collector (:15 and :19).

### 2.2 Direct read-only database results

The actual table is **centroid_checkpoints**, not checkpoints. The actual loader uses it at copilot-sdk/copilot_sdk/graph/sqlite_store.py:2906.

| Copilot | Decisions / verified in export | Checkpoints | Latest id / created_at | Largest within-category action-coordinate difference, all five checkpoints | Latest export equals SQLite / bundle |
| --- | --- | --- | --- | --- | --- |
| Trading | 800 / 223 | 5 | 5 / 1700720000.0 | 0.000000 | exact / exact |
| Purchasing | 801 / 457 | 5 | 5 / 1700720000.0 | 0.000000 | exact / exact |

Database paths: copilot-sdk/apps/trading/backend/data/trading.db and copilot-sdk/apps/purchasing/backend/data/purchasing.db. Export count/provenance references: copilot-sdk/real_centroids_v1.json:660 and :957. Database checks were executed during this audit with read-only SQLite connections. Bundle tensor references: copilot-sdk/demo/trading_demo_bundle.json:1085 and copilot-sdk/demo/purchasing_demo_bundle.json:845.

Repeated first-category vectors:
- Trading trend_following: [0.715, 0.7063, 0.665, 0.0888, 0.6438, 0.6183, 0.715, 0.5113, 0.4771, 0.4285].
- Purchasing protein: [0.66, 0.1945, 0.31, 0.505, 0.0483, 0.4617, 0.4975]. The purchasing showcase uses dry_goods, whose action rows are also identical.

The source is reproducible: build_centroids ignores action labels when accumulating category vectors (:323–325), computes a category mean (:330), and duplicates it over actions (:336). build_checkpoints stores this same tensor in all five checkpoints, with fixed decision counts 20/60/100/150/200 and synthetic timestamps (:340–360). Source: copilot-sdk/scripts/regenerate_demo_bundles.py. The latest tensor exactly matches both corresponding checked-in bundle and SQLite tensor. This establishes the data's identity; it does not establish which historical process imported that bundle.

The files named trading_bootstrap.json and purchasing_bootstrap.json are already differentiated: maximum coordinate spread across actions is 0.3747769490593749 and 0.4203318538340727, respectively. Their shapes are (5,4,10) and (5,4,7). The preset loaders read those files, migrate supported legacy shapes, and only return uniform 0.5 on load/validation errors: copilot-sdk/copilot_sdk/scoring/presets/trading.py:115 and :126; copilot-sdk/copilot_sdk/scoring/presets/purchasing.py:97 and :110. Switching profiles is therefore not the remedy for the collapsed stored checkpoints.

### 2.3 The missing L5 restore changes the diagnosis

Application startup reads get_centroids(domain) and overlays valid category/action vectors onto the checkpoint tensor. Sources: copilot-sdk/copilot_sdk/scoring/startup_restore.py:142; copilot-sdk/copilot_sdk/graph/sqlite_store.py:2602; copilot-sdk/copilot_sdk/scoring/scorer.py:706. The latter validates category/action, shape and finite values, then replaces individual rows at :728.

The following is a **local reconstruction of that overlay**, not a live AGE or whole-application run. Every local row inspected had valid category/action and dimension count.

| Copilot | L5 centroid rows | Action cells changed vs export | Maximum coordinate change | Effect relevant here |
| --- | --- | --- | --- | --- |
| trading | 6 | 4 | 0.486551 | trend_following has 3 unique action rows; poor_execution and skip_recommended remain identical |
| purchasing | 0 | 0 | 0.000000 | No overlay; all category/action rows remain collapsed |
| dataops | 3 | 1 | 0.450000 | Only schema_change/investigate changes; both showcase categories remain identical to the export |
| s2p | 6 | 6 | 0.160000 | price_variance auto_approve and hold_for_review change; both flip scenarios require a new routing check |

Trading's original scenarios after this overlay score as poor_execution (margin 0), poor_execution (margin 0), and partial_execution (margin 0.107494), respectively. The first two still tie poor_execution with skip_recommended. Thus startup restoration partly differentiates Trading, but cannot give a robust positive-margin win to either of these identical target rows. The export's uniform strong_execution answer was not a full startup result.

Purchasing has no local L5 centroid or L5 DK rows. Trading has 172 local L5 DK rows as well as six centroid rows; these are not equivalent to an exposed sigma vector. Sources for these queried tables: copilot-sdk/copilot_sdk/graph/sqlite_store.py:626 and :638. Live stores may differ.

### 2.4 Recommended centroid repair design

**[PROPOSED — not implemented]**

1. Export the selected runtime state after the same L5 restoration used at startup. Include checkpoint identity, L5 row identities/timestamps, effective centroid hash, category/action/factor labels, sigma/metric provenance and temperature. Keep the current export as a historical checkpoint-only artifact.
2. Fix future demo-bundle generation so a category mean cannot masquerade as four learned action prototypes. Use validated category/action-specific examples or explicit differentiated preset priors; label priors as priors. For an unsupported action, retain a declared prior rather than duplicate the category mean. Do not manufacture arbitrary action offsets to make a demo pass.
3. Replace obsolete collapsed demo checkpoints through a separately authorized reset/migration path and reconcile L5 overlays. A profile switch cannot bypass an existing usable checkpoint, and replacing checkpoint data alone does not replace L5 rows.
4. Require pairwise separation of all claimed winner rows in each showcase category, then rerun the actual surface/final-margin and Q-path checks. Separation is necessary, not sufficient.
5. Regenerate Trading/Purchasing preseed vectors only after that geometry is frozen. There are **no valid positive-margin vectors for their current collapsed checkpoint tensors**. For Trading after local L5 overlay, poor_execution and skip_recommended still cannot be unique winners. This follows directly from equal distances in investigation.py:69 and argmax/margin at :74 and :76.

## 3. Current SOC/DataOps/S2P scores against the supplied export

These are recalculated with each scenario's category, sigma=1, tau=0.1. Final actions/margins are the original sweep records, with the same real-provider evidence and production gates. Sources: copilot-sdk/tests/vld_validation_report.py:224–237; copilot-sdk/real_centroids_v1.json:1734, :2164 and :2359.

| Scenario / category | Claimed surface → final | Actual surface → final | Surface / final margin |
| --- | --- | --- | --- |
| VLD-SOC-1 / credential_access | monitor → escalate | investigate → investigate | 0.408327 / 0.897667 |
| VLD-SOC-2 / malware_execution | monitor → escalate | investigate → investigate | 0.408549 / 0.408549 |
| VLD-SOC-S1 / malware_execution | escalate → escalate | escalate → escalate | 0.148869 / 0.148869 |
| VLD-DO-1 / pipeline_failure | investigate → escalate_to_owner | escalate_to_owner → escalate_to_owner | 0.295360 / 0.863769 |
| VLD-DO-2 / quality_anomaly | refer_to_specialist → escalate_to_owner | refer_to_specialist → escalate_to_owner | 0.617379 / 0.801407 |
| VLD-DO-S1 / pipeline_failure | auto_approve → auto_approve | auto_approve → auto_approve | 0.998559 / 0.998559 |
| VLD-S2P-1 / price_variance | hold_for_review → auto_approve | hold_for_review → hold_for_review | 0.552625 / 0.221034 |
| VLD-S2P-2 / price_variance | flag_leakage → auto_approve | flag_leakage → flag_leakage | 0.259059 / 0.395554 |
| VLD-S2P-S1 / price_variance | auto_approve → auto_approve | auto_approve → auto_approve | 0.874387 / 0.891548 |

Squared-distance vectors below use the action order listed for each copilot. They are computed from investigation.py:69 with unit sigma; distances are rounded to six decimals.

**soc action order:** escalate, investigate, suppress, monitor.

| Scenario | Distances in the action order above |
| --- | --- |
| VLD-SOC-1 | 0.690000, 0.175000, 0.370000, 0.272500 |
| VLD-SOC-2 | 0.485000, 0.145000, 0.582500, 0.235000 |
| VLD-SOC-S1 | 0.500000, 0.530000, 2.022500, 1.360000 |

**dataops action order:** auto_approve, investigate, escalate_to_owner, pause_downstream, refer_to_specialist.

| Scenario | Distances in the action order above |
| --- | --- |
| VLD-DO-1 | 0.492367, 0.822919, 0.281086, 0.350517, 0.546931 |
| VLD-DO-2 | 0.611817, 0.812790, 0.589809, 0.480411, 0.314414 |
| VLD-DO-S1 | 0.457322, 1.751321, 1.886411, 1.181117, 1.789888 |

**s2p action order:** auto_approve, hold_for_review, escalate_to_buyer, flag_leakage, refer_to_specialist.

| Scenario | Distances in the action order above |
| --- | --- |
| VLD-S2P-1 | 0.168800, 0.033374, 0.356700, 0.376200, 0.472200 |
| VLD-S2P-2 | 0.682800, 0.205014, 0.127500, 0.065000, 0.525000 |
| VLD-S2P-S1 | 0.000000, 0.270459, 0.917300, 0.890800, 1.126800 |

### Per-copilot failure explanation

- **SOC:** both flip seeds begin in investigate, not monitor. SOC-1 does read identity, but its original vector remains in investigate even after the gated update. SOC-2 reads dimensions 0 and 5, both empty, rather than its specified 2→3 path. Its original history-only second-hop contract is also geometrically infeasible under actual Q (section 5). The S1 vector places device_trust=0.8 far from the escalate centroid's 0.2, giving only a 0.148869 margin. Sources: gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:13, :33, :37 and :51; export :1734–1803.
- **DataOps:** DO-1 already scores escalate_to_owner, so there is no claimed investigate→escalate contrast. DO-2 is the sole original exact flip, but the sweep reads downstream_urgency then source_reliability, not recurrence then dependency. A matching final label alone therefore does not establish the demo story. Sources: copilot-sdk/apps/dataops/backend/app/vld_preseed.py:30, :35, :89 and :95; real factor dispatch copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38; original sweep trace recording copilot-sdk/tests/vld_validation_report.py:236 and :256.
- **S2P:** both original surface labels are correct, but Q chooses other dimensions. S2P-1 reads commodity context (None), then contract; supplier history is never admitted within two attempts. S2P-2 reads contract then supplier history rather than pricing benchmark then volume context. Sources: s2p-copilot/backend/app/vld_preseed.py:65, :79, :96 and :110; provider dispatch s2p-copilot/backend/app/evidence_provider.py:28; original Q values in the recomputation above.
- **Trading/Purchasing:** checkpoint collapse makes all four probabilities 0.25 and every margin zero for every input. The later partial Trading L5 restore changes that diagnosis as detailed in section 2.3, but does not separate its poor/skip targets.

## 4. Proposed vectors for the supplied category tensors

**[PROPOSED — not implemented]** These vectors were checked, at the exact decimal precision shown, through VLDInvestigator.investigate using each real provider class. Existing seed functions were called only in memory (SOC with graph_client=None; S2P with data_source=None; DataOps with an in-memory evidence source). Only copies/process-local scenario data were adjusted. No production file or database was written.

All flip rows use budget=2, K_weights=None, sigma=ones, tau=0.1 and current source gates. All satisfy surface and final margin >0.05. SOC-2 is a **revised contract** and is not counted as satisfying its original history narrative. SOC-1 uses one informative read; the second attempt returns None.

Canonical factor order:

- **soc:** 0=privileged_identity_context; 1=asset_criticality; 2=threat_intel_enrichment; 3=pattern_history; 4=time_anomaly; 5=device_trust.
- **dataops:** 0=impact_scope; 1=source_reliability; 2=recurrence_frequency; 3=downstream_urgency; 4=data_freshness; 5=business_criticality.
- **s2p:** 0=match_status; 1=amount_variance_ratio; 2=duplicate_score; 3=supplier_exception_history; 4=payment_terms_impact; 5=commodity_index_correlation; 6=tax_regulatory_compliance; 7=environmental_risk.

Source orders: copilot-sdk/real_centroids_v1.json:8, :983 and :1347; source extraction copilot-sdk/tests/vld_validation_report.py:191.

| Scenario | Exact proposed surface vector | Surface → final | Margin before → after | Attempted dimensions |
| --- | --- | --- | --- | --- |
| VLD-SOC-1 | [0.0005, 0.7288, 0.693, 0.1188, 0.563, 0.2283] | monitor → escalate | 0.119916 → 0.180204 | 0 → 5 (None) |
| VLD-SOC-2 (revised) | [0.2939, 1, 0.2585, 0.0832, 0.6491, 0.2751] | monitor → escalate | 0.119681 → 0.180119 | 2 (None) → 0 |
| VLD-DO-1 | [0.1276, 0.3236, 0.5006, 0.6754, 0.6225, 0.8266] | investigate → escalate_to_owner | 0.119838 → 0.956396 | 0 → 3 |
| VLD-DO-2 | [0.7108, 0.5718, 0.9189, 0.3112, 0.7742, 0.971] | refer_to_specialist → escalate_to_owner | 0.706347 → 0.673795 | 2 → 3 |
| VLD-S2P-1 | [0.6552, 0.2758, 0.0466, 0.4499, 0.3821, 0.6834, 0.8112, 0.5] | hold_for_review → auto_approve | 0.655354 → 0.115444 | 3 → 0 |
| VLD-S2P-2 | [1, 0.7189, 0.0224, 0.2106, 0.5567, 0.3456, 0.9385, 0.5] | flag_leakage → auto_approve | 0.199744 → 0.871300 | 1 → 5 |

### Evidence values and Q ordering

Each row below is the Q ordering **before** that attempt, with previously attempted dimensions omitted. Parentheses contain the selected Q value. Raw, confidence and effective values distinguish actual provider facts from gated vector updates. Sources: investigation.py:106–109 and :143–150; current seed/provider citations under each scenario below.

| Scenario / attempt | Q order, highest first | Selected Q / gap to runner-up | Raw value / confidence / source | Effective factor value |
| --- | --- | --- | --- | --- |
| VLD-SOC-1 / 1 | 0 > 2 > 5 > 3 > 1 > 4 | 0.729600 / 0.243800 | 0.920000 / 0.920000 / identity_graph | 0.846440 |
| VLD-SOC-1 / 2 | 5 > 2 > 1 > 4 > 3 | 0.283350 / 0.014350 | None; no update | 0.228300 |
| VLD-SOC-2 / 1 | 2 > 0 > 5 > 3 > 1 > 4 | 0.514900 / 0.020020 | None; no update | 0.258500 |
| VLD-SOC-2 / 2 | 0 > 5 > 3 > 1 > 4 | 0.494880 / 0.019940 | 0.920000 / 0.920000 / identity_graph | 0.869912 |
| VLD-DO-1 / 1 | 0 > 1 > 2 > 3 > 4 > 5 | 1.008484 / 0.230288 | 0.900000 / 0.920000 / schema_registry | 0.838208 |
| VLD-DO-1 / 2 | 3 > 1 > 4 > 5 > 2 | 0.314549 / 0.020004 | 0.850000 / 0.880000 / dependency_graph | 0.829048 |
| VLD-DO-2 / 1 | 2 > 3 > 4 > 1 > 5 > 0 | 0.453615 / 0.027227 | 0.650000 / 0.550000 / historical_alerts | 0.650000 |
| VLD-DO-2 / 2 | 3 > 4 > 1 > 5 > 0 | 0.426388 / 0.109290 | 0.880000 / 0.820000 / dependency_graph | 0.777616 |
| VLD-S2P-1 / 1 | 3 > 6 > 0 > 2 > 5 > 4 > 1 > 7 | 0.431532 / 0.014939 | 0.030000 / 0.821429 / supplier_history | 0.030000 |
| VLD-S2P-1 / 2 | 0 > 5 > 1 > 6 > 4 > 2 > 7 | 0.355696 / 0.025656 | 0.950000 / 0.900000 / contract_db | 0.950000 |
| VLD-S2P-2 / 1 | 1 > 6 > 5 > 4 > 3 > 0 > 2 > 7 | 0.337560 / 0.019804 | 0.050000 / 0.820000 / pricing_benchmark | 0.050000 |
| VLD-S2P-2 / 2 | 5 > 0 > 3 > 6 > 4 > 2 > 7 | 0.492640 / 0.129040 | 0.820000 / 0.780000 / demand_forecast | 0.820000 |

The gap column concerns routing stability, not action margin. No claim of robustness to arbitrary centroid changes is made. The S2P L5 counterexample in section 6 shows why tensor/version pinning is necessary.

### Exact seed changes and narrative constraints

**SOC-1:** replace only surface_factors at gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:13 with the table's vector. Keep dimension 0 evidence at :17 unchanged: raw 0.92, confidence 0.92, identity_graph. The initial vector expresses almost no observed privileged identity context, while other surface indicators are mixed. Identity admission supplies the missing context. The second attempted dimension is device_trust, returning None in this offline showcase. Do not describe this as two informative reads.

**SOC-2 revised:** replace the vector at the same seed file :33, add dimension 0 identity evidence as specified in section 5, and revise the story from history recovery to identity recovery. Dimension 2 remains absent/None. This is a deliberate contract change, not a silent retuning of the original history-only example.

**DO-1:** replace its factors at copilot-sdk/apps/dataops/backend/app/vld_preseed.py:35 using the canonical order. Keep schema_changes.order_ingestion.downstream_impact=9 (:50) and dependency value/confidence=0.85/0.88 (:58) unchanged. The real provider calculates raw impact=max(surface_impact, fanout/10)=0.9 at copilot-sdk/apps/dataops/backend/app/evidence_provider.py:86–92. First read flips investigate→escalate_to_owner with margin 0.926889; second read reinforces it to 0.956396. The narrative must not claim that the second read is necessary to cross the action boundary.

**DO-2:** replace its factors at copilot-sdk/apps/dataops/backend/app/vld_preseed.py:95. Keep recurrence=0.65, confidence=0.55, prior_count=8 (:104), and dependency=0.88, confidence=0.82 (:111). History revises the surface recurrence estimate **downward** from 0.9189 to 0.65; it leaves refer_to_specialist in place, reducing its margin from 0.706347 to 0.443244. The new upstream dependency then flips the action with margin 0.673795. Describe this as a familiar-looking case whose historical match is weaker than the surface suggests, followed by the new dependency discovery; do not say history raises the recurrence factor. All supporting provider evidence remains unchanged.

**S2P-1, export-v1 contract:** replace the factor map at s2p-copilot/backend/app/vld_preseed.py:72. Keep supplier exception_value=0.03 with 23/28 verified prior confidence (:79), and contract coverage=0.95/confidence=0.90 (:87). Supplier history leaves hold_for_review with margin 0.554751; contract then produces auto_approve at 0.115444. S2P does not gate these sources, so confidence does not damp either value. Provider mappings: s2p-copilot/backend/app/evidence_provider.py:89 and :122.

**S2P-2, export-v1 contract:** replace the factor map at s2p-copilot/backend/app/vld_preseed.py:103. Keep variance_normalized=0.05/confidence=0.82 (:111) and contract_context_score=0.82/confidence=0.78 (:117). The actual path is pricing benchmark on dimension 1, then volume/contract context on dimension 5. Dimension 5's canonical factor is commodity_index_correlation, despite the provider's demand_forecast source name; provider mapping at s2p-copilot/backend/app/evidence_provider.py:177. This is not a separate match_status/contract read on dimension 0. Intermediate action is hold_for_review at margin 0.076559, then auto_approve at 0.871300.

Changes to descriptions, raw alert metadata and factor maps must preserve domain meaning. These are constructed fixtures; factor-extraction-from-raw-alert consistency was not established by this numeric design and must be checked during implementation rather than assumed from a passing vector-only test.

### S1 proposals

| Scenario | Vector | Surface margin | Budget contract |
| --- | --- | --- | --- |
| VLD-SOC-S1 | [0.75, 0.8, 0.9, 0.55, 0.6, 0.2] | 0.664020 | Explicit budget=0 for demo; SOC has no classifier |
| VLD-DO-S1 | [0.1148601779890048, 0.5414560929201857, 0.23465565901226745, 0.530987929219016, 0.9007745072142764, 0.32200758172461463] | 0.998996 | Omit budget: existing fallback detects S1 and selects 0 |
| VLD-S2P-S1 | [0.95, 0.05, 0.02, 0.03, 0.5, 0.8, 0.95, 0.5] | 0.874387 | Omit budget: existing fallback detects S1 and selects 0 |

SOC's replacement is the malware_execution escalate centroid; DataOps' is the pipeline_failure auto_approve centroid. S2P's existing S1 vector already works and is retained. At these vectors d_min=0 for the export, so a wired fallback classifier selects S1. Source: copilot-sdk/copilot_sdk/scoring/situation_classifier.py:122. SOC's main supplies no classifier (gen-ai-roi-demo-v4-v50/backend/app/main.py:224), so changing its vector alone does not eliminate the two default attempts. Explicit budget=0 expresses a demo-controlled budget, not a learned S1 detection claim.

Trading and Purchasing cannot satisfy their requested high-margin S1 contracts against the collapsed export. Trading's partial L5 overlay still cannot uniquely select skip_recommended. Do not fabricate S1 vectors before repairing and freezing the geometry.

### Explicit budget is part of the demo contract

When budget is omitted, the router consults the classifier before default_budget. Source: copilot-sdk/copilot_sdk/backend/investigation_router.py:65–72. For the proposed vectors, the fallback classifications are:


| Scenario | Fallback classification if wired | Budget selected |
| --- | --- | --- |
| VLD-SOC-1 | S6 | 4 |
| VLD-SOC-2 | S6 | 4 |
| VLD-DO-1 | S3 | 1 |
| VLD-DO-2 | S6 | 4 |
| VLD-S2P-1 | S3 | 1 |
| VLD-S2P-2 | S3 | 1 |

SOC does not wire this classifier and defaults to two. DataOps and S2P wire the fallback. In particular, both S2P flip examples would receive only one attempt if the caller omitted budget. Pin budget=2 for these demonstration contracts; otherwise the claimed two-read result is not the request the application executes.

## 5. SOC-2 feasibility boundary and revised design

### Original contract: infeasible

Hold fixed malware_execution, sigma=1, tau=0.1, K absent, budget=2, first attempted dimension 2 returning None, second attempted dimension 3 being the only update. Require surface monitor and final escalate to be unique winners.

This is infeasible for **any surface vector in [0,1]^6 and any final history value in [0,1]**, not merely a failed random search. The certificate uses the actual Q formula at copilot-sdk/copilot_sdk/scoring/investigation.py:95–109 and the malware_execution tensor in copilot-sdk/real_centroids_v1.json:44.

Method:
1. Enumerate the three possible runners-up to monitor and the 2^6 signs of 2*v_k - mu_monitor,k - mu_runner,k: 192 linear regions.
2. Within each region, Q is affine. Enforce Q_2 ≥ every other Q and Q_3 ≥ every remaining Q after excluding dimension 2. This allows ties, so it is a relaxation of the exact tie-breaking policy.
3. Enforce the runner-up order. Maximize a shared squared-distance advantage delta for monitor at the surface and escalate after changing only dimension 3.
4. A strictly positive probability margin requires strictly positive distance advantages. The maximum delta over all regions is **-0.146000** when the final history value is free in [0,1]. With the existing history value 0.90, it is **-0.152000**. No positive-margin solution exists.

The surface itself was constrained to the normalized range used by the seeds; outside-range synthetic inputs were not considered. The proof concerns this frozen tensor and routing formula, not every possible SOC model. Without the Q-order constraints, monitor→escalate can be achieved by changing history; the obstruction is the joint scoring-and-routing contract.

### Revised feasible contract

**[PROPOSED]** Keep the empty threat-intelligence first read. Follow it with identity context:

- category: malware_execution
- vector: [0.2939, 1.0, 0.2585, 0.0832, 0.6491, 0.2751]
- dimension 2: None
- dimension 0: value=0.92, confidence=0.92, source=identity_graph
- current history dimension 3 can remain registered, but is not read within this two-attempt budget
- observed result: monitor 0.119681 → escalate 0.180119; Q attempts 2→0; one successful trace step

Use a revised narrative such as: “Anomalous DNS activity has no matching threat-intelligence evidence; identity investigation then links the server activity to a high-risk privileged identity.” Add corresponding identity facts to the intended seed contract, instead of presenting the new process-local value as if the original history-only graph already supplied it. Current SOC-2 facts are just its Alert and Asset at gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:39; the existing SOC-1 identity/campaign example is at :19.

The in-memory validation used the real register_showcase_evidence function and SOCEvidenceProvider, with the proposed dimension-0 entry. No production seed/provider was edited. If the original historical-recovery story is mandatory, leave this scenario **blocked** and change a separately specified routing/evidence contract or model; do not claim that scalar seed tuning satisfies all three original requirements. Arbitrary K multipliers are not a demonstrated learned routing solution.

## 6. Post-startup S2P warning: export-specific designs must stay versioned

The local S2P L5 overlay replaces price_variance auto_approve and hold_for_review. Restore code is active at s2p-copilot/backend/app/main.py:249; row application is copilot-sdk/copilot_sdk/scoring/scorer.py:728. Other target rows stay unchanged.

Rechecking the section-4 S2P candidates with that reconstructed post-L5 tensor and the same real provider gives:


| Candidate | Post-L5 surface → final | Margin before → after | Actual attempted dimensions | Result |
| --- | --- | --- | --- | --- |
| VLD-S2P-1 | hold_for_review → auto_approve | 0.709165 → 0.752714 | 0 → 3 | Final flip survives; order reverses to contract then supplier |
| VLD-S2P-2 | flag_leakage → flag_leakage | 0.255528 → 0.214384 | 0 → 6 | Flip and narrative fail |

S2P-1's contract-first intermediate auto_approve margin is only 0.011689. A final robust margin must not conceal that intermediate fragility. S2P-2 instead reads contract then compliance and stays flag_leakage. The section-4 vectors must therefore **not** be shipped as a validated post-startup S2P design.

A supplementary search against local post-L5 S2P geometry sampled one million vectors per case with unchanged evidence, minimum action margins 0.08, minimum Q-selection gaps 0.01, and narrative constraints (S2P-1 surface history >0.15 and match >0.4; S2P-2 surface variance >0.3 and context <0.65). It found S2P-1 candidates, but no S2P-2 candidate satisfying the full ordered path 1→5. This is a bounded-search result, **not an infeasibility proof**. Resolve the authoritative startup snapshot, then perform constrained synthesis for that snapshot before any implementation prompt claims all S2P requirements are met.

DataOps' local L5 change is confined to schema_change/investigate and does not affect the two showcase categories. SOC still has no offline learned checkpoint in this export. Live AGE and further startup calibration remain unverified for every copilot.

## 7. Sigma and scorer-metric parity, all five copilots

| Copilot | sigma used here | Correct for current VLD adapter? | Learned/runtime limitation |
| --- | --- | --- | --- |
| SOC | ones(6) | Yes: exported adapter fallback | No local learned snapshot; no exposed learned sigma demonstrated |
| Trading | ones(10) | Yes: exported adapter fallback | L5 DK state exists; it is not an exposed sigma attribute |
| Purchasing | ones(7) | Yes: exported adapter fallback | No local L5 centroid/DK state; nonunit sigma cannot separate identical action rows |
| DataOps | ones(6) | Yes: exported adapter fallback | Kernel/DK restoration is separate from the exported sigma |
| S2P | ones(8) | Yes: exported adapter fallback | Post-L5 centroids differ; unit sigma does not resolve snapshot mismatch |

The adapter looks only for scorer/underlying sigma or _sigma of shape (d,), otherwise returns ones: copilot-sdk/copilot_sdk/backend/investigation_router.py:170. The collector records this fallback per domain at copilot-sdk/tests/vld_validation_report.py:209–213 and in export provenance :288, :660, :957, :1320 and :1705.

Do not call these vectors “learned sigma.” The regular GAE scorer supports a factor mask, variance-learning effective DK weights, and scoring-kernel dispatch at graph-attention-engine-v50/gae/profile_scorer.py:447–480. It can refresh a diagonal kernel from a covariance estimator's per-factor sigma at :621–653. That does not expose the same sigma vector to VLD's current attribute-only reader.

**[PROPOSED]** Preserve unit sigma when validating the currently deployed VLD adapter. Separately specify metric parity before surfacing learned uncertainty: identify the authoritative covariance/weights, category conditioning, normalization, shrinkage, factor masks and temperature, then ensure the exported VLD metric reproduces the intended scorer distances. For an eligible unnormalized positive diagonal precision w, sigma_k=1/sqrt(w_k) is only a mathematical conversion; current clipping, masking, normalization and category-dependent behavior must also match. Changing sigma changes both action probabilities and Q, so every seed must be revalidated.

A common per-dimension sigma cannot rescue identical action centroids: it weights equal squared distances equally. Action-specific uncertainty would be a different model and is not present in VLDInvestigator.

## 8. Recommended implementation sequence and acceptance gates

**[PROPOSED — implementation deferred]**

1. **P0 — fix snapshot fidelity first.** Amend a future extraction/sweep implementation to reconstruct the entire selected startup state, including validated L5 centroid overlays, and record which store is authoritative. Export both pre-restore and post-restore hashes. Do not describe local SQLite or SOC preset state as live AGE state. Preserve the current export and this report as versioned evidence.
2. **P0 — remove collapsed demo geometry at its source.** Redesign the category/action centroid generation and regenerate only explicitly designated demo data. Reconcile stale checkpoints and L5 rows; never silently erase learned production state. Require unique target prototypes and correct action/factor schemas before tuning Trading/Purchasing.
3. **P0 — settle the SOC-2 contract.** Adopt the exact revised identity-evidence design or retain the history story as blocked. The original contract has no vector-only solution under this tensor/Q formula.
4. **P0 — apply vector proposals only to the matching frozen geometry.** SOC-1 and the revised SOC-2 are bootstrap-snapshot designs. DataOps proposals match the local showcase categories before and after the inspected L5 overlay. Section-4 S2P vectors match export-v1 only; synthesize and validate their replacements against post-startup S2P before deployment.
5. **P1 — pin request budgets and demo copy.** Two-read flips send budget=2. S1 demonstrations use the explicit or fallback budget contract stated above. Distinguish attempts from successful reads; show DO-1's first-read flip and DO-2's history-downward correction accurately. Do not infer “no investigation” from an empty successful-step list.
6. **P1 — re-run full real-provider acceptance.** For each of 15 scenarios, assert exact action pair, required read dimensions/order, provider non-None/None behavior, source gating, margin thresholds, attempts, successful steps and no-hurt condition. Include post-startup centroid hash and the actual router request. Check raw-alert metadata/factor extraction consistency, not just hand-entered vectors.
7. **P2 — evaluate learned sigma/metric alignment separately.** Do not combine metric changes with seed tuning without a new versioned baseline. Record all claims that remain fixture-only.
8. **Release gate:** retain PAPER_READY=False and DEMO_READY=False until the corrected sweep runs against the authoritative state and all unresolved contracts pass. Even passing tuned demonstration cases alone is not evidence of out-of-sample paper performance.

### Deliverable status

| Contract | Design status |
| --- | --- |
| Trading, both flips and S1 | Blocked by prototype collapse/partial L5 collapse; no honest positive-margin vectors supplied |
| Purchasing, both flips and S1 | Blocked by fully collapsed checkpoint geometry |
| SOC-1 | Exact candidate validated against supplied bootstrap tensor and unchanged real evidence |
| SOC-2 original | Infeasible under original 2→3 route; certificate provided |
| SOC-2 revised | Exact candidate validated with proposed identity evidence and real provider |
| DataOps both flips | Exact candidates validated; local L5 overlay leaves their categories unchanged |
| S2P both flips on export-v1 | Exact candidates validated, but not a post-startup release design |
| S2P post-startup | Needs authoritative snapshot and renewed synthesis; v1 S2P-2 candidate fails |
| SOC/DataOps/S2P S1 | Vectors and explicit/fallback budget requirements specified |

## 9. Reproduction and audit evidence

Run from the workspace root using the configured Python environment. The code below is documentation for read-only analysis; it does not create test or production files.

### 9.1 Reproduce the candidate checks with real providers

Run the following separately for DOMAIN equal to soc, dataops and s2p so their app packages cannot collide. It uses the exact proposed vectors and production provider implementations. The SOC-2 registry change is process-local proposed data. DataOps source loading reads fixtures; S2P data_source=None avoids its path-based file-writing mode.

```python
import json,sys,numpy as np
from pathlib import Path
from dataclasses import asdict
root=Path.cwd();dom='soc'  # repeat in fresh processes for 'dataops' and 's2p'
sdk=root/'copilot-sdk';backend=(root/'gen-ai-roi-demo-v4-v50/backend' if dom=='soc' else root/'s2p-copilot/backend' if dom=='s2p' else sdk/'apps/dataops/backend')
sys.path[:0]=[str(backend),str(sdk/'tests'),str(sdk)]
from vld_validation_report import load_showcases,wiring,record_reads
from copilot_sdk.scoring.investigation import VLDInvestigator
from copilot_sdk.scoring.situation_classifier import SituationClassifier
x=json.loads((sdk/'real_centroids_v1.json').read_text());cand=json.loads(r'''{"VLD-SOC-1":[0.0005,0.7288,0.693,0.1188,0.563,0.2283],"VLD-SOC-2":[0.2939,1,0.2585,0.0832,0.6491,0.2751],"VLD-SOC-S1":[0.75,0.8,0.9,0.55,0.6,0.2],"VLD-DO-1":[0.1276,0.3236,0.5006,0.6754,0.6225,0.8266],"VLD-DO-2":[0.7108,0.5718,0.9189,0.3112,0.7742,0.971],"VLD-S2P-1":[0.6552,0.2758,0.0466,0.4499,0.3821,0.6834,0.8112,0.5],"VLD-S2P-2":[1,0.7189,0.0224,0.2106,0.5567,0.3456,0.9385,0.5]}''');info=x['copilots'][dom];runtime=wiring(dom)
rows,source,key,cls=load_showcases(dom);out={}
for row in rows:
 name=row[key];sc=x['scenarios'][dom][name];mu=np.array(info['all_category_mu'][sc['category']])
 if name=='VLD-DO-S1':cand[name]=mu[0].tolist()
 if name=='VLD-S2P-S1':cand[name]=sc['factor_vector']
 v=np.array(cand[name]);inv=VLDInvestigator(mu,np.ones(len(v)),info['factor_names'])
 if 'surface_factors' in row:row['surface_factors']=v.tolist()
 else:row['factors']=dict(zip(info['factor_names'],v.tolist()))
 if name=='VLD-SOC-2':
  from app.evidence_provider import register_showcase_evidence
  register_showcase_evidence(name,{0:{'value':.92,'confidence':.92,'source':'identity_graph'},3:dict(row['evidence'][3])})
 provider=cls(source,name)
 trace,reads=record_reads(provider,lambda:inv.investigate(name,sc['category'],v,provider,budget=2,gated_sources=set(runtime['gated_sources'])))
 z=v.copy();enriched=set();path=[]
 for read in reads:
  k=read['dimension'];a,p=inv.score(z);q=inv.compute_Q(z,p,enriched);e=read['evidence']
  if e:
   c=e['confidence'] if e['source'] in runtime['gated_sources'] else 1;z[k]=c*e['value']+(1-c)*z[k]
  path.append({'dim':k,'Q':q.tolist(),'order':np.argsort(-q).tolist(),'q_gap':float(q[k]-np.max(np.delete(q,k))),'evidence':e,'effective':float(z[k])})
  enriched.add(k)
 a,p=inv.score(v);assessment=SituationClassifier().classify(v,mu,np.ones(len(v)),p,inv.compute_Q(v,p))
 out[name]={'vector':v.tolist(),'surface_action':info['action_names'][trace.surface_action],'final_action':info['action_names'][trace.final_action],'surface_margin':trace.surface_margin,'final_margin':trace.final_margin,'steps':len(trace.steps),'path':path,'classifier_if_wired':asdict(assessment),'trace':asdict(trace)}
print(json.dumps(out))

```

### 9.2 Reproduce the SOC-2 original-contract infeasibility certificate

This linear program maximizes a shared signed squared-distance advantage. It permits Q ties, so impossibility for this relaxed system also excludes the strict routing contract. The seventh coordinate is the final history value; the eighth variable is delta. Expected best delta: approximately -0.146.

```python
import json, numpy as np,itertools
from pathlib import Path
from scipy.optimize import linprog
x=json.loads(Path('copilot-sdk/real_centroids_v1.json').read_text())
mu=np.array(x['copilots']['soc']['all_category_mu']['malware_execution'])
for raw in (None,):
 best=(-1e9,None);feasible=0
 for rival in (0,1,2):
  for signs in itertools.product((-1,1),repeat=6):
   signs=np.array(signs);diff=np.abs(mu[3]-mu[rival]);sums=mu[3]+mu[rival];qw=2*diff*signs;qc=.01+diff*(1-signs*sums)
   A=[];b=[]
   def add(w,c):A.append(np.r_[w,0,0]);b.append(c)
   for a in range(4):
    if a!=3:
     w=2*(mu[3]-mu[a]);c=(mu[a]**2-mu[3]**2).sum();A.append(np.r_[-w,0,1]);b.append(c)
    if a!=0:
     w=2*(mu[0]-mu[a]);c=(mu[a]**2-mu[0]**2).sum();wr=w[3];w[3]=0;A.append(np.r_[-w,-wr,1]);b.append(c)
    if a not in (3,rival):
     w=2*(mu[rival]-mu[a]);c=(mu[a]**2-mu[rival]**2).sum();add(-w,c)
   for k in range(6):
    w=np.zeros(6);w[k]=-2*signs[k];add(w,-signs[k]*sums[k])
   for top,exclude in [(2,[]),(3,[2])]:
    for k in range(6):
     if k==top or k in exclude:continue
     w=np.zeros(6);w[k]=qw[k];w[top]-=qw[top];add(w,qc[top]-qc[k])
   r=linprog([0]*7+[-1],A_ub=A,b_ub=b,bounds=[(0,1)]*7+[(None,None)],method='highs')
   if r.success:
    feasible+=1
    if r.x[-1]>best[0]:best=(float(r.x[-1]),{'rival':rival,'signs':signs.tolist(),'v':r.x[:-1].tolist()})
 print('SOC2 narrative LP raw',raw,'maxcommon_gap',best,'feasiblecells',feasible,'totalcells',192)

```

### 9.3 Verification performed

- Read the supplied export and collector/extractor source before analysis.
- Opened existing SQLite stores with mode=ro; compared every Trading/Purchasing checkpoint's action spread and latest export/bundle tensor equality.
- Reconstructed local L5 overlays using the validated-row semantics at scorer.py:706; did not call application startup.
- Recomputed all nine SOC/DataOps/S2P surface scores and squared-distance vectors.
- Ran deterministic randomized searches with seed 11092026, followed by constrained candidate refinement. Rechecked the exact rounded proposed vectors through the actual VLD loop and real evidence providers; unsuccessful optimizer outputs were rejected.
- Validated nine proposed snapshot scenarios (six flips including the revised SOC-2, three S1 cases). Successful-read counts include only non-None evidence; proposed S1 budget behavior was separately checked with the actual fallback classifier.
- Rechecked the S2P proposals with reconstructed L5 centroids and documented the divergent results.
- Ran the 192-region SOC-2 linear-program certificate at history=0.90, history=1.00 and a free history value in [0,1].
- No production, preseed, provider, test, export or database file was edited. Only this design Markdown was created. No git command or live AGE connection was used. No full pytest run was needed for this document-only task.

Observed core hashes at audit time:
- copilot-sdk/copilot_sdk/scoring/investigation.py: a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a
- copilot-sdk/copilot_sdk/backend/investigation_router.py: f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90

**Conclusion:** the immediate nine-flip failure is not solved by changing profile='test'. There is a proven demo-bundle centroid-collapse mechanism, a separate startup-state export omission, and several vectors whose Q paths do not match their narratives. This report supplies exact feasible designs for the stated frozen tensors, explicitly marks the SOC-2 contract revision, and leaves unresolved live-state requirements open rather than manufacturing successful seeds.

