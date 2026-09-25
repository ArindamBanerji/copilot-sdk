# Sweep 6 — Playwright Demo Integrity Report

Date: September 18, 2026
Scope: copilot-sdk/e2e/demo/**/*.spec.ts — static, read-only review.

## Summary

**56 tests exist, but 56 passing tests are not 56 verified demo stories.**

- Read all 56 files in full: **30 SMOKE, 20 SHAPE, 6 STORY** by strongest assertion.
- The six STORY classifications mean an outcome/comparison is asserted, not that the complete catalog claim is proved. They are SOC-05, SOC-09, SOC-10, TRD-05, PLAT-02 and MACH-03. Some assert a materially weaker or different outcome.
- **0/56 specs use a page/browser fixture or assert rendered UI.** These are API tests executed by Playwright, not validation that the demo panels render.
- **18 specs send POST requests; 13 invoke domain-state mutations**, including one temporary simulation. Twelve can leave domain/demo state behind. **Spec-level cleanup: 0/13.** SOC-04 has server-side in-memory snapshot restoration, which is not an asserted end-to-end cleanup guarantee.
- **38/56 use availability-based skips; 18 do not.** No permanent `test.skip(true)` remains. All 56 import from `@playwright/test`.
- **Catalog ID alignment: 56/56**, exactly one spec per catalog ID, no missing or extra IDs. This is structural alignment, not semantic coverage.
- The historical artifact `pw_final_results.txt` ends with **56 passed (27.6s)**. This audit did **not** rerun the suite, send live mutation requests, reseed or restart anything. Current runtime pass/fail status is not claimed.

### Evidence and classification method

Read `docs/session_state.md` first, all demo specs, `e2e/playwright.config.ts`, `e2e/global-setup.ts`, the relevant design review/current run artifact, and backend handlers needed to distinguish read-only POSTs from mutations.

The original catalog was not present at `docs/design/demo_scenarios_catalog_v5.md`. Reviewed the accessible original at:

`G:\MY Drive\public-files\gen-ai-roi\claude_projects\design\blogs\ci_core\demo_scenarios_catalog_v5.md`

That catalog, not the simplified regeneration prompts or stale class labels, supplies the story claims below. Recommendations are proposed checks, not changes implemented by this audit.

Classification applies to the strongest meaningful response assertion:

- **SMOKE:** only HTTP success/root existence/nonempty serialization. Counting five locally constructed request records does not validate five API bodies.
- **SHAPE:** named fields, types, cardinality, identity tags and basic numeric validity. Positive confidence alone does not establish cold start; positive decision count alone does not establish a regime break.
- **STORY:** a scenario-related outcome or relationship is asserted. A weak bound such as entrant gap >= 0 or an invalid causal comparison is still recorded as a partial STORY assertion, with its defect explicitly identified.
- Classification is not a test-quality score. There are **no full on-screen story proofs** in this suite; six partial STORY checks must not be reported as six complete catalog demonstrations.

`toBeDefined()` allows null, false, zero and empty arrays. Root truthiness plus serialized value != "{}" allows `[]`, nonempty error objects, zero-valued result objects and many unavailable-state responses. These are static counterexamples, not claims that those bodies were returned during the historical run.

| Group | Specs | SMOKE | SHAPE | STORY |
|---|---:|---:|---:|---:|
| SOC | 10 | 5 | 2 | 3 |
| S2P | 9 | 4 | 5 | 0 |
| PUR | 6 | 4 | 2 | 0 |
| TRD | 6 | 3 | 2 | 1 |
| DO | 8 | 4 | 4 | 0 |
| PLAT | 7 | 4 | 2 | 1 |
| MACH | 5 | 1 | 3 | 1 |
| PILOT | 4 | 4 | 0 | 0 |
| FORK | 1 | 1 | 0 | 0 |
| **Total** | **56** | **30** | **20** | **6** |

## Assertion Strength Matrix

Links identify the reviewed files; L numbers locate the strongest assertion or the start of its assertion block. “Gap” compares it with the original catalog, not merely the regenerated endpoint contract.

| Spec | Current level | Strongest assertion | Catalog claim | Gap |
|---|---|---|---|---|
| [SOC-01](../../e2e/demo/soc/soc-01-analyst-left.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Retained analyst knowledge, verified decisions and category weights | Trust-score existence proves neither retention nor verified support. |
| [SOC-02](../../e2e/demo/soc/soc-02-no-precedent.spec.ts) L7 | SHAPE | recommendation, gae_scoring, no_precedent defined | Zero similar cases; high-confidence ESCALATE | no_precedent=false and any recommendation pass. |
| [SOC-03](../../e2e/demo/soc/soc-03-rejected-35.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Promoted and rejected variants with rejection reasons | No counts or reasons checked. |
| [SOC-04](../../e2e/demo/soc/soc-04-paused-itself.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Accuracy degradation triggers self-pause | Does not inspect AMBER, auto-pause, or a transition. |
| [SOC-05](../../e2e/demo/soc/soc-05-two-alerts.spec.ts) L14 | STORY | kill_chain_detected=true; critical; shared_entities.length > 0 | Two individually benign alerts become a cross-graph kill chain | Meaningful outcome; individual benignness, distinct source domains and UI missing. |
| [SOC-06](../../e2e/demo/soc/soc-06-policy-wins.spec.ts) L7 | SHAPE | recommendation, referral, should_refer defined | Policy overrides AI auto-close to escalate | false should_refer passes; no override direction checked. |
| [SOC-07](../../e2e/demo/soc/soc-07-chained.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Verified hash chain and CSV with hash column | verified=false passes; no export request. |
| [SOC-08](../../e2e/demo/soc/soc-08-frozen-twin.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Live and frozen trajectories separate positively | No series or gap checked. |
| [SOC-09](../../e2e/demo/soc/soc-09-same-alert.spec.ts) L12 | STORY | Same recommendation.action and factor_vector on two calls | Deterministic action and factor contributions | Both missing factor vectors compare equal; shared state not pinned. |
| [SOC-10](../../e2e/demo/soc/soc-10-rollback.spec.ts) L13 | STORY | status=rolled_back; same checkpoint ID; frozen=true | Verified change followed by exact geometry restoration | Asserts receipt, never changed/restored geometry; leaves scorer frozen. |
| [S2P-01](../../e2e/demo/s2p/s2p-01-rule-said-no.spec.ts) L7 | SHAPE | action defined; confidence > 0; factors defined | Rule rejects copper invoice but reasoning accepts clause 7.3 | Any action with positive confidence passes. |
| [S2P-02](../../e2e/demo/s2p/s2p-02-day-zero.spec.ts) L7 | SHAPE | confidence > 0; factors defined | Useful first decision on a zero-history system | New event ID does not make shared scorer cold-start. |
| [S2P-03](../../e2e/demo/s2p/s2p-03-paying-more.spec.ts) L7 | SHAPE | action and confidence defined | HOLD because port costs less than working capital | No HOLD or cost comparison; request context alone is not proof it was used. |
| [S2P-04](../../e2e/demo/s2p/s2p-04-earned-autonomy.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Weekly auto-approval rises while accuracy and gate remain healthy | Static conservation response is not earned autonomy. |
| [S2P-05](../../e2e/demo/s2p/s2p-05-queue-shrank.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Exception class shrinks from N to zero | No class or extinction checked. |
| [S2P-06](../../e2e/demo/s2p/s2p-06-kept-manual.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Class remains manual because it failed an approval bar | Identical smoke coverage to S2P-05. |
| [S2P-07](../../e2e/demo/s2p/s2p-07-budget-strip.spec.ts) L9 | SHAPE | controller=adaptive; safety_lambda defined | Easy case uses one read, hard case three | Configuration tag is not exercised budget behavior. |
| [S2P-08](../../e2e/demo/s2p/s2p-08-confidence-band.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Larger dollar amounts require more confidence | No bands, amount boundaries or K14 calibration checked. |
| [S2P-09](../../e2e/demo/s2p/s2p-09-frozen-twin.spec.ts) L7 | SHAPE | frozen_available and current_vs_frozen defined | Positive live-vs-frozen compounding gap | false availability and null comparison pass. |
| [PUR-01](../../e2e/demo/purchasing/pur-01-new-gm.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | New GM inherits previous GM's supplier judgment | Fingerprint alone does not identify a new GM or supplier history. |
| [PUR-02](../../e2e/demo/purchasing/pur-02-trust-trap.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Most-trusted supplier factor is highest-noise | No factor ordering or sigma checked. |
| [PUR-03](../../e2e/demo/purchasing/pur-03-gave-up-authority.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Verified drift causes autonomous pause | GREEN or RED both pass; no drift applied. |
| [PUR-04](../../e2e/demo/purchasing/pur-04-quiet-week.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Zero-dollar week still has increasing competence | Calls conservation, not proof ledger. |
| [PUR-05](../../e2e/demo/purchasing/pur-05-two-stores.spec.ts) L7 | SHAPE | available and status defined | Learning and frozen stores show divergent waste curves | available=false/NOT_INITIALIZED pass. |
| [PUR-06](../../e2e/demo/purchasing/pur-06-demand-limit.spec.ts) L9 | SHAPE | steps and final_action defined | Event first, waste next, leads to lower order | Neutral factor vector and empty steps can pass. |
| [TRD-01](../../e2e/demo/trading/trd-01-favorite-setup.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Most-trusted factor is noisiest with corrected claim support | Neither inversion, ten factors nor claim gate checked. |
| [TRD-02](../../e2e/demo/trading/trd-02-throttle.spec.ts) L7 | SHAPE | Nonempty regimes; total_decisions > 0 | Regime break reduces autonomy to AMBER | Positive dataset count is not a break-to-throttle transition. |
| [TRD-03](../../e2e/demo/trading/trd-03-certificate.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Claim gate certifies no detector survived correction | Category accuracy is not a certificate. |
| [TRD-04](../../e2e/demo/trading/trd-04-position-alone.spec.ts) L9 | SHAPE | steps and final_action defined | Portfolio exposure checked before regime; partial execution | No exposure, order or partial action checked. |
| [TRD-05](../../e2e/demo/trading/trd-05-cold-warm.spec.ts) L10 | STORY | gap.accuracy_pp >= 0 | Warm geometry reconverges faster after regime break | Even zero gap passes; static incumbent/entrant is a different experiment. |
| [TRD-06](../../e2e/demo/trading/trd-06-code-free.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Ten earned factors and geometry distinguish learned system from fork | No factors, earned weights or baseline checked. |
| [DO-01](../../e2e/demo/dataops/do-01-which-data.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Verified wrong outcomes reduce source trust | No before/after comparison; endpoint is simulated overlay. |
| [DO-02](../../e2e/demo/dataops/do-02-source-lost-trust.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Per-source trust values differ | Identical or empty trust collections pass. |
| [DO-03](../../e2e/demo/dataops/do-03-twelve-years.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Six-factor fingerprint and centroid checkpoint history | Does not count factors or request history. |
| [DO-04](../../e2e/demo/dataops/do-04-rule-wrong.spec.ts) L7 | SHAPE | rules is array; optional evolution/promotion fields | Rule promotes then demotes with reasons | Empty rules pass; lifecycle branch optional and transitions unchecked. |
| [DO-05](../../e2e/demo/dataops/do-05-llm-wrong.spec.ts) L15 | SHAPE | surface_action, final_action, action_changed, steps defined | Surface approves while investigation escalates hidden blast radius | Equal actions and action_changed=false pass. |
| [DO-06](../../e2e/demo/dataops/do-06-jan-vs-now.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Trust distribution differentiates after verified learning | Decision-list existence is not trust distribution. |
| [DO-07](../../e2e/demo/dataops/do-07-what-to-buy.spec.ts) L7 | SHAPE | recommendations or advice defined | ROI-ranked data acquisition advice with supporting sources | Empty recommendations pass; no ROI/ranking/evidence checks. |
| [DO-08](../../e2e/demo/dataops/do-08-ask-person.spec.ts) L7 | SHAPE | answer and source_attribution defined | Quality-aware metric answer contrasts high/low trust data | Different question; refusal or empty attribution passes. |
| [PLAT-01](../../e2e/demo/platform/plat-01-clocks.spec.ts) L7 | SHAPE | concept_id=four-clocks; four content entries | Four Clocks conceptual framing | Structure does not verify editorial text or overlay. |
| [PLAT-02](../../e2e/demo/platform/plat-02-cross-signal.spec.ts) L9 | STORY | Serialized list contains pw-test-entity | SOC fact changes S2P action and banner | Same-app list match can use an older signal; no S2P request. |
| [PLAT-03](../../e2e/demo/platform/plat-03-five-corrections.spec.ts) L18 | SMOKE | Five collected bodies; each defined | Five self-correction surfaces | Fingerprint availability tests a different property. |
| [PLAT-04](../../e2e/demo/platform/plat-04-five-curves.spec.ts) L8 | SMOKE | Five locally constructed request-status entries | Five trajectories plus moat metric | Never reads any response body; count is fixed by loop. |
| [PLAT-05](../../e2e/demo/platform/plat-05-two-questions.spec.ts) L7 | SHAPE | concept_id=two-questions; two content entries | Conceptual compounding/validation questions | Content schema not approved claims or framing. |
| [PLAT-06](../../e2e/demo/platform/plat-06-where-not.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Exploratory per-domain applicability comparison | No five-domain metric validation or honesty label. |
| [PLAT-07](../../e2e/demo/platform/plat-07-whose-moat.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Exportable customer geometry and measured switching cost | Zero decisions/calendar duration pass; no export. |
| [MACH-01](../../e2e/demo/machine/mach-01-through-machine.spec.ts) L10 | SHAPE | Investigation trace defined OR analyze factor_vector defined | Complete ordered decision pipeline and confidence | Empty trace or fallback vector passes; investigation failure hidden. |
| [MACH-02](../../e2e/demo/machine/mach-02-reshape.spec.ts) L7 | SHAPE | no_precedent and recommendation defined | No precedent causes escalation, not retrieval | False novelty and arbitrary action pass. |
| [MACH-03](../../e2e/demo/machine/mach-03-parameter-moved.spec.ts) L22 | STORY | after readOrder != before; equal result skips | Verified outcome changes K alone, then route/action | Changes alert input; compares category as part of read order; no verified outcome or K assertion. |
| [MACH-04](../../e2e/demo/machine/mach-04-500-not-5m.spec.ts) L7 | SMOKE | Root truthy; serialized body != {} | Small geometry and learning plateau near 500 decisions | No dimensions, sample count or plateau. |
| [MACH-05](../../e2e/demo/machine/mach-05-retraction.spec.ts) L7 | SHAPE | concept_id=retraction-list; nonempty entries | Transparent catalog retractions and evidence | Any unrelated retraction list passes. |
| [PILOT-01](../../e2e/demo/pilot/pilot-01-first-90.spec.ts) L8 | SMOKE | Root truthy; serialized body != {} | Ready / needs coverage / pending readiness card | Health liveness is unrelated to readiness. |
| [PILOT-02](../../e2e/demo/pilot/pilot-02-verifications-stopped.spec.ts) L7 | SMOKE | Root defined; serialized body != {} | Verification gap flatlines competence, resumes afterward | No timestamps, gap or slope examined. |
| [PILOT-03](../../e2e/demo/pilot/pilot-03-three-artifacts.spec.ts) L8 | SMOKE | Root truthy; serialized body != {} | Observable mu, sigma and K with last-moved times | Only centroid-history root checked. |
| [PILOT-04](../../e2e/demo/pilot/pilot-04-bring-numbers.spec.ts) L8 | SMOKE | Root truthy; serialized body != {} | Buyer input computes modeled divergence week | Conservation GET never exercises ROI inputs. |
| [FORK-01](../../e2e/demo/fork/fork-01-clone-run.spec.ts) L8 | SMOKE | Root truthy; serialized body != {} | Fresh clone runs gate and renders initial fingerprint | Queries an already running learned service. |

## SMOKE Specs That Need STORY Assertions — Priority List

All 30 need stronger coverage if their passes are to count as demo evidence. This list is exhaustive for the SMOKE class.

| Priority | Specs | Required evidence |
|---|---|---|
| First: safety and audit | SOC-04, SOC-07, PUR-03, TRD-03 | Actual pause transition, successful chain verification/export, drift-triggered loss of autonomy, certified detector outcome. |
| First: learning and trust | SOC-03, S2P-04, S2P-05, S2P-06, DO-01, PUR-02, TRD-01 | Rejection reasons, earned autonomy, extinction, kept-manual failure bar, verified trust movement, trust/noise inversion. |
| Next: business proof and comparisons | SOC-08, PUR-04, PLAT-04, PILOT-02, PILOT-04 | Twin gap, zero-dollar/positive-competence contrast, five actual curves, verification-gap flatline/recovery, buyer-input ROI projection. |
| Next: retention and artifacts | SOC-01, PUR-01, TRD-06, DO-02, DO-03, DO-06, MACH-04, PILOT-01, PILOT-03, FORK-01 | Verified institutional history, differentiated factors/sources, checkpoint/artifact provenance, curve plateau, readiness and a genuinely fresh clone. |
| Next: platform contracts | S2P-08, PLAT-03, PLAT-06, PLAT-07 | Amount-dependent confidence routing, actual self-corrections, exploratory applicability fields/labels and nonzero switching-cost/export evidence. |

Do not merely replace root existence with field existence. For example, `expect(body.verified).toBeDefined()` still passes when verification failed. Require the intended boolean/value, a meaningful fixture and the corresponding rendered evidence.

## Mutation Safety Analysis

### Counting rule

“Mutates” counts business/learning/demo state, including transient scorer mutation, not request logs, UUID generation or caches. The table includes all 18 POST-using specs so read-only POSTs are not incorrectly counted as writers. The other 38 specs are GET-only; they make no explicit domain mutation request, but read shared mutable data and are not snapshot-isolated.

| Spec | Mutates? | What | Cleanup? | Parallel-safe? |
|---|---|---|---|---|
| SOC-02 | Yes | Analyze creates pending SOC decision, audit entry and confidence snapshot. | None. | Not isolated; counts/audit/trajectory consumers observe writes. |
| SOC-04 | Yes, transient | Scores/updates 20 synthetic failures and forces simulated AMBER in a scorer snapshot. | No spec cleanup; handler restores in-memory scorer state in finally. | Handler takes scorer lock; cross-request isolation/restoration is not asserted. Do not assume all readers share the lock. |
| SOC-05 | No domain write | Cross-correlate loads two alerts and computes a response. | Not needed. | Read-only with stable alert fixtures. |
| SOC-06 | Yes | Analyze persists pending decision/audit for policy-conflict alert. | None. | Not isolated from shared SOC state. |
| SOC-09 | Yes | Two analyze writes for the same alert. | None. | Determinism comparison has no pinned model/context across calls. |
| SOC-10 | Yes | Creates checkpoint and decision; rollback changes centroids/counts and freezes scorer. | None; rollback is the operation under test, not cleanup. | Unsafe alongside learning/other rollback; leaves frozen state for later runs. |
| S2P-01 | Yes on admitted score path | Persists procurement scoring decision for fixed invoice ID. | None. | Backend locks writes; test state is not isolated or cleaned. |
| S2P-02 | Yes on admitted score path | Scores another event on the same warm S2P scorer. | None. | Cannot establish zero-history setup; existing/concurrent decisions defeat premise. |
| S2P-03 | Yes on admitted score path | Persists container-invoice score. | None. | Shared counts/cache/graph; backend write lock is not test isolation. |
| DO-01 | Yes | Decrements shared source's in-memory trust overlay, clamped to [0,1]. | None; reset endpoint exists but is not called. | Same source reused; retries/repeated runs accumulate changes. |
| DO-05 | No explicit learning write | SDK read-only scoring/investigation using frozen centroids and K reads. | Not needed for learning state. | Reads may observe external changes before snapshot; provider caches are incidental. |
| DO-08 | No explicit domain write | DI query reads/ranks source profiles; service also has caching/logging. | Not needed for domain state. | Answer depends on shared profile snapshot; not a learning mutation. |
| PLAT-02 | Yes | Adds signal to router-local in-memory store. | None; no delete path in reviewed router. | Fixed entity ID makes stale-signal success possible; app-local store does not prove transfer. |
| MACH-01 | Yes | Analyze writes before read-only investigate. | None. | Shared SOC writes; fallback masks investigation failure. |
| MACH-02 | Yes | Analyze writes another pending no-precedent decision. | None. | Shared SOC state; no isolated fixture lifecycle. |
| MACH-03 | Yes | Analyze writes pending decision between read-only investigations of two different alerts. | None. | Neither K-only isolation nor verified outcome; shared state can change independently. |
| PUR-06 | No explicit learning write | SDK read-only investigation. | Not needed for learning state. | Requires stable evidence/model to make ordered-read claims. |
| TRD-04 | No explicit learning write | SDK read-only investigation. | Not needed for learning state. | Same snapshot limitation as PUR-06. |

**Totals:** 18 POST specs; 13 mutating specs; 12 leave uncleaned persistent/process-lifetime domain state; 1 transient simulation with server-side in-memory restoration. **0/13 implement their own cleanup.** Do not count an analysis request as a verified learning outcome.

### Source trace supporting the mutation classifications

Paths in this subsection are relative to the common `claude_projects` parent.

- SOC analyze: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1030` writes a Decision with `status='pending'` and `outcome=null`; audit recording starts at line 1080 and confidence snapshot follows. The MACH-03 comment “Verified outcome probe” is false for this call.
- SOC investigate: `.../routers/triage.py:454` is a read-only shadow investigation, not a verification endpoint.
- SOC correlation: `.../routers/discoveries_router.py:191` reads alerts, computes shared entities/pattern and returns the correlation; no decision/learning write occurs in that function.
- SOC simulation: `.../routers/evolution.py:621` snapshots the scorer, injects updates, explicitly sets AMBER and restores in `finally`. Snapshot helpers are at lines 52/72; `services/gae_state.py:58` supplies the scorer lock. This is not evidence that the live gate independently detected degradation or stayed paused afterward.
- SOC rollback: `.../routers/framework_router.py:516` delegates to `app/framework/checkpoint.py:101`; the latter restores centroids/counts and calls `scorer.freeze()` at line 162. The spec never restores the prior freeze state. Existing decision/audit records are not undone by centroid rollback.
- S2P score: `s2p-copilot/backend/app/routers/s2p.py:2155` performs write admission checks and invoice/domain locking, then calls `scorer.score` at line 2227. Its response explicitly says `learning_applied=False`; scoring is not verification.
- DataOps perturbation: `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:50` changes an in-memory demo overlay. Lines 68–75 label it simulated; line 77 provides service reset and line 117 exposes the reset route. It is not a verified-outcome learning demonstration.
- SDK investigation: `copilot-sdk/copilot_sdk/backend/investigation_router.py:58` reads centroids/K and calls the investigator; `_make_score_fn` at line 146 uses frozen-model/read-only scoring. No K update or outcome submission occurs in that handler.
- DI query: `copilot-sdk/copilot_sdk/di/query_service.py:215` performs query computation/cache handling; its source-reliability branch ranks profiles rather than updating the scorer.
- Cross signals: `copilot-sdk/copilot_sdk/backend/cross_signal_router.py:25` creates a store per router factory. Publishing writes at lines 31–36; list reads that same store. The spec does not contact a receiving copilot.

### Ordering, retries and parallelism

`e2e/playwright.config.ts:7` enables one retry; line 8 defaults global workers to one, with per-demo-project workers also set to one. Thus the default run is serialized, but **serialization is not state isolation**. A second run starts from the first run's changes. Raising workers can overlap projects, including SOC readers/writers in both the machine/platform and SOC projects; separate test runners or user activity can also overlap.

Concrete risks:

1. SOC-10 leaves the shared scorer frozen, altering later learning behavior even with a single worker. A skip/error between create/analyze/rollback has no finally cleanup either.
2. DO-01 repeatedly degrades the same `sap_s4hana` overlay. It can reach zero; a smoke pass persists even when further degradation no longer changes trust.
3. PLAT-02 never checks the newly returned signal ID. A stale `pw-test-entity` record can satisfy the assertion even if the newest successful publish is not represented in the list.
4. Analyze/score retries add decisions and audit evidence; fixed input IDs do not make the tests observational or restore graph counts.
5. A newly named S2P event is still scored by a preseeded, shared model. S2P-02 cannot establish day zero through payload naming.
6. SOC-09 compares two separate mutable-context evaluations; pin input/model/evidence versions to distinguish true nondeterminism from state change.

Recommended isolation: disposable seeded instances/snapshots for mutating stories, unique run-scoped IDs, explicit verified-outcome setup where learning is claimed, and `finally` restoration of original state including freeze flags. Do not reset or unfreeze a shared environment blindly; preserve its initial state.

## Self-Diagnosing Compliance

| Check | Observed |
|---|---:|
| Spec files / test declarations | 56 / 56 |
| Imports from @playwright/test | 56 |
| Permanent test.skip(true) calls | 0 |
| Files with an availability skip | 38 |
| Files without any test.skip | 18 |
| Direct test.skip(!response.ok())-style calls | 43 |
| Aggregate availability skips (PLAT-03/04) | 2 |
| Content-dependent skips (MACH-03) | 2 |
| Total test.skip calls | 47 |

The 38 guarded files comprise 36 direct-probe files and two aggregate-probe files. Multiple requests account for more skip calls than files.

The 18 unguarded specs are:

SOC-01, SOC-03, SOC-07; S2P-04; PUR-01, PUR-02, PUR-04; TRD-01, TRD-03, TRD-06; DO-02, DO-03, DO-06; MACH-04; PILOT-01, PILOT-03, PILOT-04; FORK-01.

Each of those asserts HTTP success rather than skipping. This contradicts a blanket “every spec is self-diagnosing” claim, but **failing on a required endpoint regression is appropriate release-test behavior**. Do not weaken them just to make skip patterns uniform.

Other issues:

- The 38 availability guards treat any non-2xx response alike: missing route, malformed payload, authorization failure and server regression can all become skips. This is availability-aware, not a reliable diagnosis of missing features.
- A connection refusal/timeout rejects the awaited request before the skip is reached; no transport-exception handling exists in these specs. “Endpoint down auto-skips” is not universally true.
- MACH-01 has a primary analyze guard but a weaker factor-vector fallback on investigation failure. It can pass while the required investigation surface is broken.
- MACH-03 skips both absent traces and unchanged traces, then asserts that traces differ. A regression to identical order therefore avoids failure; seeded required behavior should fail, not auto-skip.
- DO-04 can skip only after retrieving a rule whose lifecycle request fails. With zero rules it passes without making that request.
- `response.ok()` accepts all 2xx, not exactly 200. This is useful for POST 201, but should not be described as an exact-200 contract.
- Require an expected pass/skip manifest in CI. Separate optional-environment skips from unexpected 4xx/5xx failures and missing required fixture evidence.

## Catalog Alignment Verification

### One-to-one ID inventory

| Directory | Catalog IDs | Spec files | Missing IDs | Extra/duplicate IDs |
|---|---:|---:|---:|---:|
| soc | 10 | 10 | 0 | 0 |
| s2p | 9 | 9 | 0 | 0 |
| purchasing | 6 | 6 | 0 | 0 |
| trading | 6 | 6 | 0 | 0 |
| dataops | 8 | 8 | 0 | 0 |
| platform | 7 | 7 | 0 | 0 |
| machine | 5 | 5 | 0 | 0 |
| pilot | 4 | 4 | 0 | 0 |
| fork | 1 | 1 | 0 | 0 |
| **Total** | **56** | **56** | **0** | **0** |

Every ID maps to one test and one filename. No catalog scenario is missing a file. The v5 footer still says “47 scenarios” while listing the above groups, which sum to 56.

### Material semantic substitutions

| Spec | Current check | Original catalog claim |
|---|---|---|
| PILOT-04 | GET conservation status | Buyer inputs produce a projected divergence week through ROI/readiness calculation. This is not a proof-ledger/export story either. |
| TRD-05 | Static incumbent/entrant gap >= 0 | Cold/warm reconvergence curves after a regime break; faster warm recovery with properly qualified gamma. |
| PLAT-03 | Five fingerprint responses | Five self-correction surfaces: rejection/pause, earned autonomy, drift pause, regime throttle and rule demotion. |
| PLAT-04 | Five conservation HTTP statuses; no bodies read | Five nonempty compounding curves plus switching-cost/moat evidence. |
| PUR-04 | Conservation object | Proof and competence curves, including a $0 week with competence still rising. |
| PILOT-01 | Generic health | Day-zero readiness with ready/coverage/pending distinctions. |
| MACH-03 | Different alert profiles and category-tagged trace strings | Same-input routing/action change caused only by a verified K update, with mu unchanged. |
| S2P-07 | Static controller/configuration fields | One actual read on an easy decision versus three on a hard one. |
| DO-08 | Highest-trust-source question | Quality-aware business metric answer with high/low-trust source contrast. |
| PLAT-01/05, MACH-05 | Versioned concept JSON shape | Editorial framing/retraction content; catalog has no executable empirical claim for these. |

These are semantic mismatches despite correct IDs. They should not be fixed by silently redefining the original story to match an easier endpoint.

Catalog classes describe the older plan, not proof of current product capability: shipped endpoints may replace ROADMAP status, but a passing schema test does not certify the story. Conversely, editorial content can legitimately have a content/UI test without being counted as measured product behavior.

### UI coverage limitation

All 56 specs use `request`, not `page`. `e2e/global-setup.ts:16` warms four frontend URLs and waits for a `main` element, but catches navigation/readiness errors as warnings and does not assert any scenario panel. It is not a substitute for story navigation, visible values, error/empty-state checks or screenshots. Playwright's configured screenshots-on-failure do not create scenario screenshots for these request-only tests.

## Recommended Assertion Strengthening (Per Spec)

These are explicit proposed acceptance checks. Where supporting product contracts/fixtures are absent, report that dependency; do not fabricate success data or loosen the story to get a green result. Every UI claim also needs a corresponding visible-panel assertion.

Fixture numbers from the catalog are illustrative unless explicitly measured. Use fixture metadata for expected values, require provenance labels, and avoid hardcoding illustrative magnitudes as universal production results.

| Spec | Proposed stronger assertions |
|---|---|
| SOC-01 | Assert verified_count > 0 and nonempty per-category learned weights; render retained knowledge for a new analyst with no personal history. |
| SOC-02 | Require no_precedent=true, zero similar cases, ESCALATE and the fixture's declared confidence threshold; verify the no-precedent panel. |
| SOC-03 | Require both counts > 0, count conservation, and a reason per rejection; require 47/12/35 only for a fixture explicitly seeded with those counts. |
| SOC-04 | Assert the simulated response's AMBER/provenance and verify unchanged real state after the demo; separately exercise real verified degradation in an isolated server and assert GREEN -> AMBER plus auto-pause. |
| SOC-05 | Assert each alert alone is non-escalated, distinct evidence domains and a shared entity support the combined critical escalation; verify discovery rendering and an unrelated-pair negative control. |
| SOC-06 | Require should_refer=true, rule ID/reason, original AI auto-close and final policy escalation; link the override to its audit receipt. |
| SOC-07 | Require verified=true for a nonempty decision chain; download CSV, check content type, hash column and matching decision IDs; test tamper rejection in an isolated fixture. |
| SOC-08 | Require initialized twin, two nonempty time-aligned series, positive live-minus-frozen improvement, checkpoint provenance and visible MODELED/PILOT-TARGET label. |
| SOC-09 | Require both vectors present, expected dimensionality and finite values, then equal action/contributions under a pinned model and identical input; compare rendered outputs and clean up decisions. |
| SOC-10 | Snapshot geometry/counts/freeze state, apply a verified update and assert geometry changed, roll back and compare exact snapshot values; test invalid restore separately and restore original freeze state in finally. |
| S2P-01 | Use the copper fixture; assert rule REJECT versus final ACCEPT, contract clause 7.3 and evidence citation; require correctly sized finite factors and rendered reasoning. |
| S2P-02 | Use a fresh isolated domain instance; assert zero prior verified decisions and initial geometry before scoring; require positive bounded confidence and valid factors. |
| S2P-03 | Use the seeded container; require HOLD, recognized container context, demurrage-versus-working-capital calculation and supporting reasoning; assert fixture-derived savings, not arbitrary production totals. |
| S2P-04 | Assert nonempty weekly auto-approval/accuracy history, increased autonomy under the configured accuracy bar and GREEN conservation; verify the performance chart. |
| S2P-05 | Select a seeded class; require startCount > 0, endCount=0, ordered timeline and an earning decision ID; render extinction timeline. |
| S2P-06 | Require a kept_manual class, failed threshold metric/reason and no auto-approval for that class; verify failed-bar display. |
| S2P-07 | Run easy/hard fixtures through the production investigation path; assert allocated and consumed reads 1/3, halt reason, and unchanged decision-policy boundary; show budget strip and provenance. |
| S2P-08 | Require four ordered bands, monotone thresholds and boundary routing for $500/$50K examples; assert k14_noise_rate and geometry-calibration/provenance label. |
| S2P-09 | Require frozen_available=true, nonempty aligned live/frozen series and positive gap; verify checkpoint origin and modeled-divergence caption. |
| PUR-01 | Assert new GM own-decision count zero while verified supplier history from prior GM is nonempty; render continuity panel and modeled ramp-time caption. |
| PUR-02 | Require finite learned weights/noise, match most-trusted factor to highest-sigma flag, check correction/held-out support and render trust inversion. |
| PUR-03 | Capture GREEN baseline, apply controlled verified degradation on an isolated instance, require AMBER/self-pause and human routing, then restore state. |
| PUR-04 | Read proof ledger; require both ordered curves, a $0 proof week with increasing competence and coverage/explanation; verify both curves on screen. |
| PUR-05 | Require initialized frozen twin, matched period/menu conditions and two nonempty waste curves with learning-store waste below frozen; keep illustrative savings labeled. |
| PUR-06 | Use event/expiry fixture; require event -> waste evidence order, usable-stock evidence and reduced-order recommendation, with nonempty rendered trace. |
| TRD-01 | Require ten factor entries, trusted-factor/highest-sigma inversion, FDR and held-out support; verify trust radar and claim gate labels. |
| TRD-02 | Use regime-break fixture; require Hurst/tail-dependence markers followed by GREEN -> AMBER and reduced autonomy, with timestamps linking cause and response. |
| TRD-03 | Require detector count > 0, corrected survivors=0, certified state and the configured correction/held-out evidence; assert CertificatePanel rendering. |
| TRD-04 | Use correlated-position fixture; require portfolio -> regime trace, shared exposure evidence, partial execution and thesis unread at that point; render trace. |
| TRD-05 | Replay the same regime break for cold/warm initializations; require two trajectories, matched evaluation budget, shorter warm reconvergence time and honest simulation gamma label; do not substitute static accuracy gap. |
| TRD-06 | Require ten finite earned-factor weights with supporting verified decisions and documented 200-value geometry; contrast a zero-history clone, retaining observation-only disclaimer. |
| DO-01 | For overlay contract assert trust_after < trust_before and simulation=true, then reset; prove the catalog learning claim separately with real verified outcomes and linked trust/weight changes. |
| DO-02 | Require at least two named sources with finite unequal trust values and nonzero verified support; show expected degraded source below trusted source. |
| DO-03 | Require exactly six finite factors and nonempty timestamped centroid history/count; check visible checkpoint count and fingerprint profile. |
| DO-04 | Require seeded target rule, chronologically ordered promoted -> demoted transitions, per-step reason/accuracy evidence and manual-routing result; keep empty-state coverage as a separate test. |
| DO-05 | Require fixture-specific APPROVE -> ESCALATE action mapping, action_changed=true, nonempty schema/join/downstream evidence and critical-system references; verify side-by-side display and K14 provenance. |
| DO-06 | Compare initial/current source trust snapshots, require learned dispersion and nonzero verification support; render differentiated after-state and time labels. |
| DO-07 | Require nonempty ranked recommendations with source IDs, costs, incremental value and evidence; verify ranking formula and IntelligenceMap/Advisor rendering with illustrative labels. |
| DO-08 | Ask the catalog metric/confidence question using a seeded supported query; require computed metric, nonempty source attribution, finite trust/confidence and quality-aware recommendation; test insufficient-data refusal separately. |
| PLAT-01 | Assert exact four clock names/order and approved descriptions; render overlay and label conceptual. Do not count this as empirical compounding evidence. |
| PLAT-02 | Publish a unique signal, retain returned ID, verify exact record at receiving S2P, compare score before/after to HOLD and banner; assert F-26 caption and clean up/isolate signal store. |
| PLAT-03 | Exercise SOC rejection/pause, S2P earned autonomy, Purchasing pause, Trading throttle and DataOps demotion; assert their actual UI surfaces and reuse substantive per-domain fixtures. |
| PLAT-04 | Read five nonempty time-ordered compounding series and conservation states plus nonzero switching-cost evidence; assert chart lines and provenance, not five HTTP responses. |
| PLAT-05 | Assert approved questions and qualified K14 captions, citation/sample provenance and rendered caption card; keep editorial verification distinct from experiment reproduction. |
| PLAT-06 | Require five distinct domains, finite conditional fractions/chain lengths/gains and EXPLORATORY/static-placeholder labels; verify display without converting descriptive placeholders into measured prediction. |
| PLAT-07 | Require positive accumulated verified decisions and consistent elapsed-time calculation; verify customer export of geometry/ledger and clearly attributed moat experiment rather than fabricated live measurement. |
| MACH-01 | Require nonempty ordered route/read/enrich/rescore/gate/emit trace with finite confidence and referenced evidence; fail required investigation errors instead of falling back to a factor vector. |
| MACH-02 | Share verified SOC-02 fixture assertions: no_precedent=true, no similar cases, ESCALATE and high confidence; render no-precedent reasoning. |
| MACH-03 | Use identical input twice, submit an actual verified outcome, prove K delta with unchanged mu and other state, compare factor identifiers only, and assert required route/action change; fail unmet seeded causality instead of skipping. |
| MACH-04 | Assert configured geometry dimensions/size and measured learning curve plateau under a predeclared tolerance; render both and qualify sample/domain-specific counts. |
| MACH-05 | Check each approved catalog retraction, its withdrawn/corrected/hypothesis status and experiment reference; show complete editorial list without presenting pending experiments as results. |
| PILOT-01 | Call readiness contract and require the three structured categories, coverage bars and blockers; assert readiness card rather than process health. |
| PILOT-02 | Require >7-day verification gap, equal competence across it within tolerance, positive post-resumption change and graph gap label; verify rendered curve. |
| PILOT-03 | Require nonempty mu/sigma/K artifacts, dimensions, provenance and last-moved timestamps; acknowledge uniform/unlearned sigma rather than inventing variation; open each artifact view. |
| PILOT-04 | Submit two controlled ROI/readiness input sets, assert valid projected divergence week and expected sensitivity, and require MODELED/PILOT-TARGET label; never claim customer-specific realized ROI. |
| FORK-01 | Run disposable clean-instance setup; require zero verified history, ten baseline factors, initial gate state and fingerprint UI; separately demonstrate earned weights after verified learning. |

### Negative controls that distinguish real coverage from another smoke suite

- Return `verified=false`: SOC-07 must fail.
- Return `rules=[]`: the DO-04 story test must fail; a separate empty-state contract test may pass.
- Return equal investigation actions with `action_changed=false`: DO-05 must fail for its known divergent fixture.
- Return `available=false` or `frozen_available=false`: the twin story tests must fail or report missing required setup, not count as proven stories.
- Return five HTTP 200 responses with `{}`: PLAT-03/04 must not pass their story claims.
- Remove both factor vectors: SOC-09 must fail before comparing equality.
- Hold K and factor order constant while changing only alert category: MACH-03 must not count that as a learned routing change.
- Keep the scorer GREEN through the controlled degradation: the actual pause-transition test must fail.
- Disable the investigation endpoint while analyze still works: MACH-01's full-trace test must fail, not use its present fallback.
- Remove only the newly published signal while retaining an old matching entity: PLAT-02 must fail.

No negative-control injection was performed on live systems during this review.

## Ranked Findings

Priorities below concern release/demo evidence integrity, not newly established production-security vulnerabilities.

### P1-01 — Safety stories pass without proving any safety transition

**Locate:** `e2e/demo/soc/soc-04-paused-itself.spec.ts:7`, `e2e/demo/purchasing/pur-03-gave-up-authority.spec.ts:7`, `e2e/demo/trading/trd-02-throttle.spec.ts:7`.

**Evidence:** SOC-04/PUR-03 inspect only a nonempty root; TRD-02 checks regime data/count. SOC's simulation explicitly sets AMBER and restores the snapshot (`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:621`), so even checking that response alone would not prove independent production gate activation.

**Impact:** Disabled pause/throttle behavior can coexist with passing safety demos. Require isolated verified degradation, before/after state, automatic-routing consequence and honest simulation labels.

### P1-02 — MACH-03 cannot establish K causality and can misidentify category changes as read-order changes

**Locate:** `e2e/demo/machine/mach-03-parameter-moved.spec.ts:3`, lines 13, 15, 20–22.

**Evidence:** `readOrder` appends `alert_category` to factor/pattern identifiers; the second request uses a different alert. The intervening analyze writes `outcome=null`, not a verified outcome. No K snapshot/delta or unchanged mu assertion exists. `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py:112` includes the supplied alert category in trace items.

**Counterexample:** Same factor sequence with category A versus B yields unequal comparison strings even when K and route order are unchanged. Equal trace results are skipped rather than failed.

**Impact:** A green test can substantiate the wrong causal claim. Use the same input, real verification, explicit K delta, invariant mu and factor-only sequence comparison.

### P1-03 — SOC-10 leaves the shared scorer frozen and proves only a rollback receipt

**Locate:** `e2e/demo/soc/soc-10-rollback.spec.ts:4`, lines 8–15; `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:145`, line 162.

**Evidence:** The test creates a checkpoint, analyzes once, rolls back and asserts `frozen=true`. It neither verifies learning changed geometry nor compares restored geometry. There is no finally block restoring the previous freeze state or cleanup of artifacts.

**Impact:** Running the suite changes later learning behavior, including on the demo environment. Use a disposable instance or full scoped restoration; test state equality rather than response receipt.

### P2-01 — Fifty specs stop at SMOKE/SHAPE; valid empty/negative states masquerade as demo proof

**Locate:** `e2e/demo/soc/soc-07-chained.spec.ts:7`, `e2e/demo/dataops/do-04-rule-wrong.spec.ts:9`, `e2e/demo/dataops/do-05-llm-wrong.spec.ts:15`, `e2e/demo/s2p/s2p-09-frozen-twin.spec.ts:7`, `e2e/demo/purchasing/pur-05-two-stores.spec.ts:7`.

**Evidence:** 30 root-only checks; 20 shape/sanity checks. Empty genealogy passes, non-divergence passes, unavailable twins pass. SOC-09's optional vector comparison additionally admits two missing vectors.

**Impact:** Missing data or broken story behavior need not fail tests. Preserve separate empty-state coverage, but require positive seeded evidence for the story tests listed above.

### P2-02 — Correct catalog IDs conceal materially different assertions

**Locate:** `e2e/demo/pilot/pilot-04-bring-numbers.spec.ts:5`, `e2e/demo/trading/trd-05-cold-warm.spec.ts:4`, `e2e/demo/platform/plat-03-five-corrections.spec.ts:4`, `e2e/demo/platform/plat-04-five-curves.spec.ts:5`.

**Evidence:** ROI becomes conservation; reconvergence becomes static gap; self-correction becomes fingerprint; curves become HTTP statuses. The matrix documents further weakened claims.

**Impact:** 56/56 structural traceability overstates scenario coverage. Restore original acceptance criteria rather than changing titles alone.

### P2-03 — None of the 56 specs validates the demo UI

**Locate:** All `e2e/demo/**/*.spec.ts`; `e2e/global-setup.ts:16`.

**Evidence:** Zero page usage; global setup's warmup catches failures and does not inspect scenario components.

**Impact:** Blank panels, wrong labels and stale on-screen values can coexist with 56 passing API tests. Add actual browser navigation/visible value assertions for render claims; keep API tests as a separate layer.

### P2-04 — Availability skips and fallbacks hide regressions

**Locate:** `e2e/demo/machine/mach-01-through-machine.spec.ts:8`, `e2e/demo/machine/mach-03-parameter-moved.spec.ts:20`, and 38 availability-guarded files.

**Evidence:** Required endpoint 422/500 responses are skipped like absent features; unchanged MACH-03 traces skip; failed investigation can fall back to an unrelated factor vector. Transport errors are not caught at all.

**Impact:** A “no failures” run may have lost required coverage. Fail unexpected errors/content regressions and enforce a release pass/skip manifest.

### P2-05 — PLAT-02 can pass from stale local data without any cross-copilot transfer

**Locate:** `e2e/demo/platform/plat-02-cross-signal.spec.ts:4`, line 9; `copilot_sdk/backend/cross_signal_router.py:25`.

**Evidence:** Both calls use Trading; the fixed string is searched anywhere in serialized JSON. The POST response's signal ID is ignored, stores are factory-local, and S2P is never contacted.

**Impact:** The claimed “SOC signal changes S2P action” is completely untested. Assert exact new ID end to end, score change and banner, with isolated cleanup.

### P2-06 — Repeated scoring and demo mutations have no spec-owned cleanup

**Locate:** `e2e/demo/dataops/do-01-which-data.spec.ts:4`, `e2e/demo/s2p/s2p-02-day-zero.spec.ts:4`, `e2e/playwright.config.ts:7`, plus mutation table.

**Evidence:** Thirteen mutation-invoking specs, zero cleanup blocks; retries enabled. DO-01 can saturate a shared overlay; score/analyze append evidence; day-zero uses a warm shared scorer. SOC-04's backend snapshot restoration is a limited exception, not suite isolation.

**Impact:** Results and demo state depend on run history. Add fixture lifecycles, unique IDs and disposable state, preserving initial conditions.

### P3-01 — Universal self-diagnosing compliance is inaccurately claimed

**Locate:** `e2e/demo/soc/soc-01-analyst-left.spec.ts:5` and the 18-file list above.

**Evidence:** Those files assert HTTP success without any skip. Only 38 files implement availability-based skipping.

**Impact:** Documentation/expectations are inconsistent. Document an intentional strict-required versus optional-environment policy instead of automatically weakening strict tests.

### P3-02 — Catalog metadata and conceptual coverage need separate accounting

**Locate:** Original catalog v5 footer and PLAT-01/05/MACH-05 sections; corresponding concept specs at their line 7 assertion blocks.

**Evidence:** Footer says 47 despite 56 scenario headers. Conceptual framing has no empirical PW claim; JSON length/identity checks do not validate approved editorial content or measured results.

**Impact:** Inventory totals and “all stories proven” claims become misleading. Track 56 IDs, content/UI verification separately from product/experiment validation, and retain measurement/provenance qualifiers.

### Recommended order

1. Isolate mutations and repair rollback cleanup before adding more stateful assertions.
2. Restore safety, audit and K-causality acceptance criteria.
3. Fix wrong-story substitutions and required-fixture assertions.
4. Add browser-level rendering checks and exact end-to-end signal verification.
5. Separate smoke/schema/empty-state/content checks from story release gates; enforce expected skips and provenance.

## Verification and Change Accounting

- 56 files and 56 test declarations inspected; directory counts match the catalog's 56 IDs.
- All 56 imports use `@playwright/test`; zero permanent skips and zero page-based scenario tests.
- Historical 56/0/0 evidence was read, not reproduced by this audit.
- Frozen source SHA-256 prefixes checked: `investigation.py 3441dcbd`, `investigation_router.py 08f4df7a`, `scorer.py 24ac9e49`.
- No source/spec/session-state edits, no git, no service mutation or restart.
- **0 existing files modified; 1 new report created:** `docs/quality/sweep_6_pw_integrity_report.md`.

PW integrity sweep complete. Specs analyzed: 56. SMOKE: 30 | SHAPE: 20 | STORY: 6.
Mutating specs: 13 (spec-owned cleanup: 0/13; one server-restored transient simulation).
Catalog alignment: 56/56 IDs; complete UI story verification: 0/56.
Ranked findings: P1 3 | P2 6 | P3 2.

