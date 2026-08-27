# SCAN-E Pre-BATCH-1 Architecture Audit

## Gate Summary

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Tensor dimensions aligned | WARN | Presets define dimensions at `copilot_sdk/scoring/presets/trading.py:40-62`; AGE stores caller-supplied shapes at `../ci-platform/ci_platform/graph/age_graph_store.py:1522-1533` |
| R2 | L2 default everywhere | WARN | Executable default is L2 at `../graph-attention-engine-v50/gae/profile_scorer.py:160-176`; stale DK wording remains at `docs/design/blogs/new_docs/math_synopsis_v20.md:235` |
| R3 | No production hardcoded `sslmode=disable` | FAIL | Shared AGE client hardcodes it at `../ci-platform/ci_platform/graph/age_client.py:44-48` |
| R4 | SOC-only auth | PASS | SOC auth middleware at `../gen-ai-roi-demo-v4-v50/backend/app/main.py:66-79`; auth bypass policy at `../gen-ai-roi-demo-v4-v50/backend/app/auth/dependencies.py:38-58` |
| R5 | Lock is serialization, not deadlock | PASS | Non-reentrant locks at `copilot_sdk/scoring/mutation_lock.py:12-25`; S2P explicitly describes queue semantics at `../s2p-copilot/backend/app/routers/s2p.py:2182-2187` |
| R6 | All middleware header-only | FAIL | SOC PII middleware consumes and rebuilds response bodies at `../gen-ai-roi-demo-v4-v50/backend/app/middleware/pii_redaction.py:65-106`; DataOps enrichment is correctly handler-level at `copilot_sdk/backend/scoring_router.py:201-227` |
| R7 | PW infrastructure landed | PASS | Workers override at `e2e/playwright.config.ts:6`; retry logic at `e2e/fixtures/copilot-fixture.ts:15-54`; PW gate at `demo.py:1053-1071` |
| R8 | AGE runtime-state migration and ignore coverage | PASS | AGE checkpoint APIs exist at `../ci-platform/ci_platform/graph/age_graph_store.py:3036-3213`; runtime patterns are ignored at `.gitignore:46-50`, `../s2p-copilot/.gitignore:17-20`, and `../gen-ai-roi-demo-v4-v50/.gitignore:83-86` |
| R9 | All backend suites pass at stated counts | WARN | DataOps collected 336 tests and previously passed; current parallel full-suite run ended in PowerShell out-of-memory before producing reliable counts |
| R10 | Four frontend builds clean | WARN | S2P typecheck completed; the sequential build check timed out during Trading after `apps/s2p/frontend` returned exit 0 |

### R1 Details

The verified preset dimensions are:

- Trading: 5 × 4 × 10 — `copilot_sdk/scoring/presets/trading.py:40-62`
- Purchasing: 5 × 4 × 7 — `copilot_sdk/scoring/presets/purchasing.py:33-59`
- DataOps: 6 × 5 × 6 — `copilot_sdk/scoring/presets/dataops.py:32-57`
- S2P: 5 × 5 × 8 — `copilot_sdk/scoring/presets/s2p.py:30-57`
- SOC: 6 × 4 × 6 — `copilot_sdk/scoring/presets/soc.py:30-56`

S2P frontend and backend both expose eight factors, including `environmental_risk`, at `apps/s2p/frontend/src/types.ts:17-26` and `../s2p-copilot/backend/app/domains/s2p/config.py:38-48`.

No E2/E3 dimension requirement was found in the executable preset contracts. However, AGE accepts a caller-provided `shape` rather than enforcing each preset’s dimensions at `../ci-platform/ci_platform/graph/age_graph_store.py:1522-1533`; therefore full code=docs=frontend=AGE equivalence is not proven.

### R2 Details

GAE’s actual default is L2 at `../graph-attention-engine-v50/gae/profile_scorer.py:160-176` and `:278`.

The documentation remains internally inconsistent: it calls DiagonalKernel the v6.0 default at `docs/design/blogs/new_docs/math_synopsis_v20.md:235`, while later retaining L2 as the production default at `:361` and `:381`.

### R6 Details

DataOps now keeps the middleware header-only at `apps/dataops/backend/app/main.py:894-911`. Its `abstention_warning` is injected through the score handler at `copilot_sdk/backend/scoring_router.py:201-227` and wired at `apps/dataops/backend/app/main.py:719-731`.

S2P’s score-body middleware was removed; its frozen-twin value is now added in the handler at `../s2p-copilot/backend/app/routers/s2p.py:2249-2254` and `:2342-2343`.

SOC still has a distinct optional PII-redaction middleware that consumes `body_iterator` at `../gen-ai-roi-demo-v4-v50/backend/app/middleware/pii_redaction.py:65-106`. Thus the stated “all middleware is header-only” prerequisite is not true across all five copilots.

## Overall

FAIL — 2 confirmed blockers (R3, R6) and 2 unverified gates (R9, R10).

