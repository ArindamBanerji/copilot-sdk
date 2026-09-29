# Astra SDK post-SS review

Review date: 2026-09-27. Verdict: **FINDINGS**.

Review-only: no production code or tests were edited. This report covers the current working tree, not just committed HEAD. Validation logs are under `.codex_tmp/astra_sweep_*.txt`.

## Scope and attribution

The session history and the prompt do not describe identical batches. The history records SS-05 as Purchasing evidence/learning, SS-06 as Purchasing controls, and SS-07 as the remaining Purchasing evidence work plus Trading trust/IKS. It does **not** record the broader Trading main batch listed under SS-07 in this review request. I reviewed both the recorded changes and those explicitly listed Trading files. Findings in unchanged Trading files below are **remaining gaps**, not claims that FIX-SDK introduced them.

The working tree also contains earlier materializer, health, and Purchasing mypy changes. Those were distinguished from the SS changes. SS-01 belongs to ci-platform and is outside this SDK review.

## Findings by severity

### P1 — correctness / required response contract

#### R01 — Failed investigation evidence can change the decision
- **FILE:** `apps/purchasing/backend/app/evidence_providers.py:154`; downstream `copilot_sdk/scoring/investigation.py:252`.
- **FUNCTION:** `FactorEvidenceProvider.read_payload` → `PurchasingEvidenceProvider.read_evidence` → `VLDInvestigator.investigate`.
- **SEVERITY:** P1.
- **ISSUE:** The new provider availability flags disappear before the HTTP investigation response, and failed evidence is treated as acquired.
- **DETAIL:** A failed `_domain_context` read produces value `0.5`, confidence `0.0`, `data_available=false`, and `degraded=true`. The investigator checks only whether the payload is None. It ignores these flags, labels the step `acquired`, and uses the neutral value unless the exact source string is gated. Purchasing's configured gated sources do not include `MISSING_DATA:neutral:historical_waste`. A read-only fault-injection probe changed historical_waste from 0.8 to 0.5 and flipped action 1 → 0 on a graph exception. Neither InvestigationStep nor the response carries the provider flags. Unavailable evidence must remain distinguishable through the trace/HTTP model and must not be used as an acquired observation.
- **SS-PROMPT:** SS-06/SS-07, P1-014.
- **COVERAGE GAP:** Existing tests stop at `read_payload` or `_domain_context`; they do not exercise the investigator with degraded provider evidence.

#### R02 — Healthy Purchasing conservation is always unavailable on the graph-reader branch
- **FILE:** `apps/purchasing/backend/app/routers/learning_beats.py:166` (especially 187–206).
- **FUNCTION:** `_stats`.
- **SEVERITY:** P1.
- **ISSUE:** Successful conservation reads do not reset `conservation_available` to true.
- **DETAIL:** When the scorer lacks `get_conservation_status`, the code initializes availability to false, reads graph statuses successfully, and leaves availability false. The final expression consequently replaces the successful state with UNAVAILABLE. CompoundingScorer exposes `get_conservation_state`, not the method checked here, making this relevant to the real binding. The query also passes `DOMAIN` as a string to a method expecting a list of domains; InMemoryGraphStore iterates that string into characters. An initialized, healthy in-memory store returned `verified_available=true`, `conservation_available=false`, `degraded=true`. Pass the domain collection correctly and mark a successful read available; do not overwrite a valid conservation status merely because a different section failed.
- **SS-PROMPT:** SS-05/SS-07, P1-023.
- **COVERAGE GAP:** Both SS-07 learning tests use a graph that fails; neither covers a successful graph-based conservation read.

#### R03 — Purchasing numeric fields become null or disappear during outages
- **FILE:** `apps/purchasing/backend/app/routers/evidence.py:27`, `:126`; `apps/purchasing/backend/app/routers/learning_beats.py:73`, `:166`.
- **FUNCTION:** `evidence_summary`, `conservation_proof`, `hero`, `ramp`, `_stats`.
- **SEVERITY:** P1.
- **ISSUE:** Handler boundaries do not convert unavailable numeric helper results to numeric defaults.
- **DETAIL:** HTTP probes returned `iks_score: 1.5 → null` when trajectory failed and `q: 1.0 → null` when the verified counter failed. Learning hero changes `iks: 1.5` into an absent key because `response_model_exclude_none=True`; ramp permits null IKS. These fields already allow null in some no-data states, but the campaign's explicit outage contract requires numeric defaults plus separate availability flags. Preserve legitimate no-data semantics separately; on these failed reads emit the required numeric default and section availability. The proof regression test currently asserts `q is None`, locking in the wrong outage contract.
- **SS-PROMPT:** SS-05/SS-07, P1-020/P1-021/P1-022/P1-023.

#### R04 — Measurement-state HTTP response still exposes unavailable IKS as null
- **FILE:** `copilot_sdk/scoring/measurement_state.py:89`; `copilot_sdk/backend/scoring_router.py:438`, `:498`.
- **FUNCTION:** `compute_measurement_state`, `measurement_payload`, `create_measurement_state_router.prefixed_measurement_state`.
- **SEVERITY:** P1.
- **ISSUE:** The internal None sentinel reaches HTTP without a typed default.
- **DETAIL:** The state correctly changes to `degraded`, but both HTTP paths serialize the dataclass directly. A probe with sufficient verified data returned `iks:1.25` when healthy and `iks:null`, `iks_available:false` on trajectory failure. The nullable response annotation permits this, so mypy/Pydantic do not enforce the requested type-preserving degraded contract. Convert the internal failure sentinel at all HTTP/materialized boundaries while retaining `iks_available=false`; do not alter unrelated cold-start semantics.
- **SS-PROMPT:** SS-03, P1-055.
- **COVERAGE GAP:** The SS-03 test checks the helper's state and flags, not the serialized numeric field.

#### R05 — Cohort store construction failures bypass the new degraded response
- **FILE:** `apps/purchasing/backend/app/routers/cohort_status_router.py:21`; `apps/dataops/backend/app/routers/cohort_status_router.py:21`.
- **FUNCTION:** `create_cohort_status_router.get_cohort_status` in both apps.
- **SEVERITY:** P1.
- **ISSUE:** The graph-store factory runs outside the guarded read boundary.
- **DETAIL:** Query failures inside CohortStatusService become CohortReadError and receive an explicit degraded response, but a connection failure opening the store escapes before that handler. A Purchasing TestClient probe with a factory raising ConnectionError returned HTTP 500. DataOps has the same ordering. Normalize connection failures from store acquisition through the same unavailable path (or an explicit 503), without catching unrelated programming errors.
- **SS-PROMPT:** SS-04 and SS-06 cohort-read fixes.
- **COVERAGE GAP:** Existing tests supply an already-constructed broken store, never a failing factory.

### P2 — observability gaps

#### R06 — Pause-artifact exception handlers still omit warnings
- **FILE:** `copilot_sdk/scoring/scorer.py:1045`, `:1078`, `:1095`.
- **FUNCTION:** `CompoundingScorer.learn`, conservation-pause branch.
- **SEVERITY:** P2.
- **ISSUE:** Warnings are appended for false returns but not for raised snapshot/checkpoint/fingerprint failures.
- **DETAIL:** The three outer catches only log. In particular, checkpoint argument computation and fingerprint calculation can fail before a persistence helper returns its bool. A probe making all three paths raise returned the normal paused result with no warnings field. Append the corresponding artifact warning in each exception branch while preserving the pause decision. This does not imply an accepted outcome was lost.
- **SS-PROMPT:** SS-03, P2-016.
- **COVERAGE GAP:** The pause regression test patches persistence helpers to return False; it does not exercise these exceptions.

#### R07 — Evolution persistence status is discarded by both callers
- **FILE:** `copilot_sdk/evolution/ledger.py:34`; callers `copilot_sdk/evolution/evolver.py:135` and `copilot_sdk/evolution/prompt_evolver.py:432`.
- **FUNCTION:** `InMemoryEvolutionLedger.append`, `AgentEvolver._record`, `PromptVariantEvolver._emit_lifecycle_event`.
- **SEVERITY:** P2.
- **ISSUE:** The new False return never reaches an evolution/learn result.
- **DETAIL:** Both production callers ignore append's bool. Therefore a failed durable write, including failed outbox recording, still leaves an in-memory event and a normal-looking evolution result. `CompoundingScorer._run_evolution` returns true when no exception escapes, so no learn warning is added. A probe confirmed _record returns None after append logs a failed write. Carry partial-persistence metadata through these callers without undoing committed learning.
- **SS-PROMPT:** SS-03, P2-011/P2-024.
- **COVERAGE GAP:** The new ledger test checks append directly; the evolution test injects a history-read exception, not a ledger failure inside a successful evolution run.

#### R08 — Public bundle restore erases partial-restore counts
- **FILE:** `copilot_sdk/demo/bundle.py:40`.
- **FUNCTION:** `restore_bundle_if_empty`.
- **SEVERITY:** P2.
- **ISSUE:** The public API collapses the new restore report back to a bool.
- **DETAIL:** AGE _restore returns restored_count and skipped_count, but the public function returns only whether restored_count > 0. One successful row and many failed rows are indistinguishable from a complete restore to its caller. Trading/Purchasing/DataOps startup callers do not consume a partial-restore report either. Expose and retain the counts/completion state through the public/startup boundary, in addition to existing warning logs.
- **SS-PROMPT:** SS-03, P2-009.
- **COVERAGE GAP:** The new test calls private _restore; it does not test the launcher-facing API.

#### R09 — Learning-beats sibling endpoints discard availability
- **FILE:** `apps/purchasing/backend/app/routers/learning_beats.py:88`, `:103`, `:119`, `:133`.
- **FUNCTION:** `signal_gate`, `proof_ledger`, `self_pause`, `ramp`.
- **SEVERITY:** P2.
- **ISSUE:** Only hero carries the new helper availability flags to its response.
- **DETAIL:** Proof ledger converts None straight to []; the other handlers select only old fields from _stats and their response models lack availability fields. Fault injection returned a normal empty proof ledger, CALIBRATING signal gate, and self-pause with `paused=false` / “No manager drift detected,” without flags. Ramp says ACCUMULATING rather than distinguishing failed verified-history lookup (although its conservation string can say UNAVAILABLE). Propagate the relevant flags through every consumer/model, maintaining existing array/number types.
- **SS-PROMPT:** SS-05/SS-07, P1-022/P1-023.
- **COVERAGE GAP:** SS learning tests cover only hero.

#### R10 — Trust insights still turns a failed counter into an ordinary empty list
- **FILE:** `apps/purchasing/backend/app/routers/trust_router.py:74`.
- **FUNCTION:** `trust_insights`.
- **SEVERITY:** P2.
- **ISSUE:** The new None result from _decisions_total is silently collapsed to [].
- **DETAIL:** The trust-weights handler gained a degraded branch, but the insights sibling returns [] for both a count outage and genuinely insufficient data. A TestClient probe reproduced HTTP 200 with [] and no availability signal. Surface a compatible explicit failure signal; do not silently change the successful array contract.
- **SS-PROMPT:** SS-06, P1-026.
- **COVERAGE GAP:** The new test exercises trust-weights only.

#### R11 — DK-readiness flag confuses reaching the threshold with a failed read
- **FILE:** `apps/trading/backend/app/services/trust_analysis.py:47`, `:65`, `:175`.
- **FUNCTION:** `TrustAnalyzer.analyze`, `_decisions_until_dk`.
- **SEVERITY:** P2.
- **ISSUE:** None has two meanings but availability is derived only from non-None.
- **DETAIL:** _decisions_until_dk returns None both on exceptions and when the remaining count reaches zero. In variance mode (including Phase B with no weights), analyze reports `dk_readiness_available=false` for a successful threshold-reaching read. A seeded InMemoryGraphStore probe reproduced this. Use a distinct failure signal or return a numeric zero for the successful count; keep outage handling separate.
- **SS-PROMPT:** SS-07, P1-036.
- **COVERAGE GAP:** The SS test covers a broken store, not a healthy store at the threshold.

#### R12 — Trading domain-context outage still looks like missing evidence
- **FILE:** `apps/trading/backend/app/evidence_providers.py:83`.
- **FUNCTION:** `_domain_context` → `FactorEvidenceProvider.read_payload`.
- **SEVERITY:** P2.
- **ISSUE:** A failed graph read returns the same ({}, False) as absent context.
- **DETAIL:** The provider subsequently emits neutral/MISSING_DATA evidence without a graph-availability flag. Consumers cannot distinguish an outage from genuinely absent data. Carry a distinct failure sentinel through the provider and investigator; R01 describes the downstream consumer issue as well.
- **SS-PROMPT:** SS-07 as listed in the review request; unchanged from HEAD, not a verified campaign regression.

#### R13 — Trading trader profiles still silently empty on graph failure
- **FILE:** `apps/trading/backend/app/services/trader_profiles.py:79`.
- **FUNCTION:** `TraderProfileService._verified_decisions`.
- **SEVERITY:** P2.
- **ISSUE:** The broad exception handler returns [] with no availability state.
- **DETAIL:** list_traders/leaderboard become empty; individual profile and comparison payloads show empty counts with source=graphstore. An outage probe returned an ordinary empty trader list. Return an internal unavailable sentinel and preserve it through the mounted trader responses.
- **SS-PROMPT:** SS-07 requested broader Trading scope; unchanged from HEAD.

#### R14 — Trading cohort reader still collapses all failed reads to no cohorts
- **FILE:** `apps/trading/backend/app/services/cohort_status.py:145`.
- **FUNCTION:** `TradingCohortStatus._read_decisions`.
- **SEVERITY:** P2.
- **ISSUE:** Every reader exception is ignored and the final fallback is [].
- **DETAIL:** Unlike the changed Purchasing/DataOps counterparts, Trading never reports that all candidate readers failed. A probe returned a normal INSTRUMENT_VALIDATED/pending state with zero cohort counts and no degraded flag. Apply the same explicit unavailable contract while preserving valid empty cohorts.
- **SS-PROMPT:** SS-07 requested broader Trading scope; unchanged from HEAD.

#### R15 — Claim refresh does not expose stale/unavailable qualification
- **FILE:** `apps/purchasing/backend/app/services/purchasing_control.py:70`; `apps/trading/backend/app/services/claim_gate.py:93`.
- **FUNCTION:** `PurchasingClaimRegistry.refresh`, `TradingClaimRegistry.refresh_from_store`.
- **SEVERITY:** P2.
- **ISSUE:** Failed qualification reads leave the response-facing claim registry without any freshness/availability state.
- **DETAIL:** Purchasing logs and treats the failed query as no outcomes; Trading silently returns. Both retain previously observed claims if a prior refresh succeeded. Purchasing's new message “qualification remains unmeasured” is also inaccurate for that case. Preserve any intentionally retained evidence, but flag that its refresh is unavailable/stale and expose that state alongside claim metadata.
- **SS-PROMPT:** SS-06 claim refresh; Trading counterpart in requested SS-07 scope is unchanged.
- **COVERAGE GAP:** The Purchasing regression checks only that the warning was logged.

#### R16 — Trading promotion conservation failure is reported as real RED
- **FILE:** `apps/trading/backend/app/routers/promotion.py:85`.
- **FUNCTION:** `_conservation_status` → `evaluate_promotion`.
- **SEVERITY:** P2.
- **ISSUE:** A failed conservation read returns an unqualified RED/False result.
- **DETAIL:** The exception path fabricates `{status: RED, passed: false}` without logging or an availability flag, and evaluate_promotion returns it as conservation_status. It remains fail-closed, which is correct; the missing distinction is actual RED versus a failed read. Preserve blocking while adding explicit unavailability. The regime/detail path was also inspected: its None flows to an “unknown” conservation label and stays fail-closed, so it is not counted as an unsafe promotion finding.
- **SS-PROMPT:** SS-07 requested broader Trading scope; unchanged from HEAD.

### P3 — type-contract maintenance

#### R17 — Availability model fields remain nullable
- **FILE:** `apps/purchasing/backend/app/routers/learning_beats.py:17`; `copilot_sdk/backend/models.py:230` (`EvolutionVariantsResponse`).
- **FUNCTION:** `LearningHeroResponse`, `EvolutionVariantsResponse` declarations.
- **SEVERITY:** P3.
- **ISSUE:** New availability/degraded flags are declared bool | None, contrary to the requested boolean flag contract.
- **DETAIL:** The defaults are None, with response_model_exclude_none used to omit them. This exposes nullable flags in schema/type generation even though the intended emitted states are booleans. Use boolean-typed fields with appropriate healthy defaults and an explicit omission policy if preserving the legacy healthy field set is required. This is separate from the runtime numeric failures in R03.
- **SS-PROMPT:** SS-05/SS-06/SS-07.

## Positive checks and coverage assessment

| Area | Assessment |
|---|---|
| SS-02 transfer | Checkpoint failure is distinguishable from no checkpoint. Failed-read fallback strings differ from GREEN, so both exact-GREEN gates block. Source-store failures log domain context. No unsafe transfer execution found in these changed branches. |
| SS-03 fingerprint | Persistence failure propagates through FingerprintResult and the HTTP model. Accepted outcomes/core updates remain committed. |
| SS-03 weekly IKS | Internal failure is (None, None); report generation converts it to numeric zeros with iks_available=false, and WeeklyReportResponse retains the flag. |
| SS-04 DataOps | AE responses retain arrays/counts with degraded flags; live investigation reader failures do not silently select fixture data; the investigation loop records failed patterns. Cohort query failures are explicit, with the factory gap in R05. Seed write counts now include failed entries. |
| SS-05/06/07 Purchasing | Evidence arrays/counts and provider-level flags were added; several HTTP consumers and numeric defaults remain incomplete as detailed above. |
| SS-07 Trading IKS | safe_call(with_status=True) and _iks_state preserve a numeric 0.0 with iks_available=false on an exception. Both static and service registry entries use this path. |
| Tier 1 P1-054 | GateEnforcedScorer._conservation_state calls the scorer directly; graph exceptions are not caught and replaced with GREEN. _get_recent_outcomes likewise does not swallow connection errors. The explicit server preseed branch is separate. |
| FIX-SDK | The relative key_manifest import resolves locally. The persistence-outbox timer test now waits for actual completion with a bounded deadline and cancels the timer in finally. |

Coverage is not complete at HTTP boundaries. The new tests frequently validate helpers alone, inject all reads failing together, or assert the new flag without checking every existing field. Examples are documented against the corresponding findings. DataOps' AE test exercises impact; cohort and investigation tests largely cover service/helper failures rather than all response paths. No new tests were written during this review.

### Graph mock audit

The exact requested regex scan found **39 matching lines** under tests/ and apps/ Python files. Twelve are legitimate outage/forbidden-read/AGE-adapter sites; the other 27 are false positives such as a mocked preset supplied alongside a real graph store. Raw matches: `.codex_tmp/astra_sweep_mock_scan.txt`.

The 13 FIX-SDK replacements were inspected. They construct InMemoryGraphStore directly or subclasses that call super().__init__, and seed data through write_decision/write_outcome/save_centroids. No normal graph fixture in these replacements remains an uninitialized Mock/MagicMock. Legitimate failure doubles are retained to make graph errors reproducible.

Replacement files:
- tests/test_gate_enforced_scorer.py
- tests/test_response_models.py
- tests/test_transfer_router.py
- tests/test_di_enrichment.py
- tests/test_demo_truth_guards.py
- tests/test_iks_service.py
- tests/backend/test_evolution_router.py
- apps/trading/backend/tests/test_trust_analysis.py
- apps/trading/backend/tests/test_regime_conditioned_learning.py
- apps/trading/backend/tests/test_execution_analysis.py
- apps/purchasing/backend/tests/test_iks_trust.py
- apps/purchasing/backend/tests/test_ss07_evidence_degraded.py
- apps/dataops/backend/tests/test_trust_perturbation.py

Retained graph fault/adapter sites occur in tests/backend/test_graph_access_health.py, tests/scoring/test_scorer.py, and the per-app health/graph-access/trading-registry tests. They are not classified as replacement regressions.

## Validation

All requested validation commands completed successfully. No test-count regression from the supplied baseline was observed.

| Check | Passed | Failed | Skipped | Baseline passed | Duration |
|---|---:|---:|---:|---:|---|
| SDK root | 3,771 | 0 | 0 | 3,771 | 29m 31s |
| Trading | 1,478 | 0 | 0 | 1,478 | 10m 49s |
| Purchasing | 858 | 0 | 1 | 858 | 13m 47s |
| DataOps | 451 | 0 | 0 | 451 | 3m 43s |
| **Total** | **6,558** | **0** | **1** | **6,558** | — |

Purchasing's single skip matches the prior recorded baseline. It was not removed or bypassed. SDK mypy: **PASS — no issues found in 292 source files**.

Commands executed from the SDK root:

```text
python -m pytest tests/ -q --timeout=120
python -m pytest apps/trading/backend/tests/ -q --timeout=120
python -m pytest apps/purchasing/backend/tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ -q --timeout=120
python -m mypy copilot_sdk/ --config-file pyproject.toml
```

Logs: `.codex_tmp/astra_sweep_root.txt`, `astra_sweep_trading.txt`, `astra_sweep_purchasing.txt`, `astra_sweep_dataops.txt`, and `astra_sweep_mypy.txt`, all under `.codex_tmp/`. A supplementary read-only collection check confirmed 3,771 tests. Fault-injection probes described above were run in separate Python processes using in-memory stores/controlled failure doubles; they did not modify source or test files.

The five P1 review findings are uncovered correctness/contract gaps, **not failing tests in this validation run**. Test success does not establish full degraded-path coverage.

Mypy scope caveat: pyproject.toml sets follow_imports=skip and has ignore_errors=true overrides for copilot_sdk.backend.* and copilot_sdk.framework.*. A successful prescribed run does not prove that all backend return contracts are type checked.

## Verdict

**FINDINGS: 5 P1, 11 P2, 1 P3.** The campaign improves many failure paths, but it is not clean: degraded-state propagation is incomplete, some outage responses violate the requested numeric contract, and Purchasing has a healthy-path conservation regression. The broader Trading batch named in the request is not evidenced as completed in this working tree. Fixes are described for review only; none were applied.
