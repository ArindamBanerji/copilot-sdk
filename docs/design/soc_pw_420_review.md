# SOC Playwright 420/420 review

## Result

The source inventory found 21 skip annotations, representing 12 runtime
skipped test cases once describe-level guards and multiline conditions are
counted by test case. The healthy-stack run completed all 420 scheduled
tests. No skip is a trivially safe stale skip. No test files were changed.

| Test name | File | Skip class | Reason | Action |
|---|---|---|---|---|
| POST `/api/s2p/score` × 10 scenarios | `frontend/tests/e2e/checklist.spec.ts:205` | D | S2P runs on a separate service and the test is intentionally excluded from the SOC checklist. | kept |
| `test_eval_result_displays_accuracy` | `frontend/tests/e2e/feature01_eval.spec.ts:50` | C | The test does not upload a file or run an evaluation; the accuracy result is only created after that missing feature flow. | kept |
| S2P preview has `(5,5,7)` tensor | `frontend/tests/e2e/cross_tab_consistency.spec.ts:177` | D | The S2P preview-config availability guard skipped this read-only contract in the observed run. | kept |
| scored invoice exposes seven numeric contribution rows | `frontend/tests/e2e/s2p_contribution_chart.spec.ts:42-46` | D | Writes through an explicitly isolated `S2P_API_URL`; default configuration intentionally provides no write target. | kept |
| verified outcome increments conservation once | `frontend/tests/e2e/s2p_evidence_receipt.spec.ts:65-69` | D | Same isolated S2P write-target and live-write safety gate. | kept |
| correct outcome receipt includes PD audit fields | `frontend/tests/e2e/s2p_receipt_fields.spec.ts:78-79` | D | Receipt writes require an explicit isolated S2P target and opt-in live-write flag. | kept |
| incorrect outcome receipt has zero amount recovered | `frontend/tests/e2e/s2p_receipt_fields.spec.ts:78-79` | D | Receipt writes require an explicit isolated S2P target and opt-in live-write flag. | kept |
| evidence compliance endpoint remains available | `frontend/tests/e2e/s2p_receipt_fields.spec.ts:78-79` | D | It is inside the receipt-write describe block, so the safety guard skips it with the write tests. | kept |
| supplier lead-time renders contractual and actual Q4 values | `frontend/tests/e2e/s2p_polish.spec.ts:15` | D | Requires the S2P preview backend to render Supplier Intelligence; unavailable state is handled as an intentional skip. | kept |
| domain applicability panel is visible in Tab 6 | `frontend/tests/e2e/s2p_polish.spec.ts:26` | C | The current S2P frontend contains no Domain Applicability panel; this is missing functionality, not a stale guard. | kept |
| domain applicability remains visible when S2P backend is unavailable | `frontend/tests/e2e/s2p_polish.spec.ts:49` | D | Deliberately requires a controlled outage with SOC up and S2P down; unsafe to enable in the normal full stack. | kept |
| persisted enrichment can be read back with provenance | `frontend/tests/e2e/s2p_supplier_enrichment_api.spec.ts:88` | D | Depends on the non-dry-run enrichment call returning a supplier in the current backend state. | kept |

The other conditional annotations are not stale skips in the observed
baseline: P77 has live fallback routes in the SOC backend (`/soc/factor-analysis`,
`/metrics/confidence-trajectory`, and `/soc/accuracy-trajectory`), the SOC
health guard passes when the service is healthy, and the remaining cross-tab
guards are data/service-availability protections.

## Current failures

| Test | Observed result | Diagnosis | Action |
|---|---|---|---|
| `cross_tab_consistency.spec.ts:17` — X1 conservation status matches Tab 5 and Tab 7 | Expected `GREEN`, received `RED` | `/api/soc/tab/5/content` reports `health_status=RED`, while `/api/soc/evidence-room` reports `conservation.status=GREEN` with an `iks_fallback` reason. This is a backend snapshot inconsistency, not a stale skip. | kept failing; no safe test-only fix |
| `decision_flow.spec.ts:189` — `learning_loop_validates_20_decisions` | Convergence `decision_count` did not increase by the required 12 | The UI workflow completed without the expected GAE convergence updates. The assertion is against live backend state, and the test mutates/resets alerts; the failure is a state/update integration issue requiring backend or workflow investigation. | kept failing; no safe test-only fix |
| `s2p_centroid_explorer_ui_flow.spec.ts:62` — second scored decision refreshes centroid explorer | Failed on the initial attempt and retry | The test passed the two-invoice guard, but changing invoices did not reliably remove the prior decision ID before the second score. The describe block has one retry, but both attempts failed; this is currently reproducible stale-result behavior, not safely dismissible as a flake. | kept failing; product-flow fix required |

## Flake

Flake candidate: `s2p_centroid_explorer_ui_flow.spec.ts` — it is the only E2E
source with an explicit retry (`test.describe.configure({ retries: 1 })` at
line 38). The healthy-stack run failed both attempts at the second-decision
transition, so the evidence does not support accepting it as a one-off flake.
No retry/configuration change is safe.

## Verification

- `python demo.py --status` and direct health checks showed SOC, Trading,
  Purchasing, DataOps, and S2P backends/frontends healthy.
- Full run: `npx playwright test --reporter=line`; Playwright scheduled 420
  tests and completed in 27.3 minutes.
- Full-run result: 405 passed, 3 failed, 12 skipped.
- A focused rerun of `cross_tab_consistency.spec.ts` reproduced X1 with
  `GREEN` versus `RED` and additionally exposed the existing non-canonical
  `cloud_misconfiguration` audit category in the current persisted data.
- No source changes were made, so TypeScript and mypy gates were not needed.

Before: 407 passed, 1 flake, 12 skipped.

After: 405 passed, 3 failed, 12 skipped. No skips were removed and no source
files changed. The two-count difference from the reported baseline is caused
by the live run surfacing the two additional deterministic failures alongside
the centroid retry failure.

Target: 420/420 not reached. Remaining skips are documented classes B/C/D;
class A count is zero. No fixes were applied because the failures require
backend/state or product-flow changes rather than a trivially safe edit.
