# Purchasing Playwright Test Slowness Diagnosis

Measured locally on 2026-09-04 against the Purchasing Vite dev server on port 5175 and backend on port 8020. The three timing runs were separate Playwright invocations. Values are wall-clock observations, not synthetic estimates.

## Test lifecycle

- The Purchasing project uses a 30 s test timeout, one retry, one worker by default, and `http://127.0.0.1:5175` as its base URL (`e2e/playwright.config.ts:5-9`, `e2e/playwright.config.ts:32-37`).
- Each Playwright test receives a fresh isolated browser context and page from the built-in `page` fixture. The local fixture only changes `page.goto` to default to `domcontentloaded` (`e2e/fixtures/copilot-fixture.ts:39-45`). Dashboard tests explicitly call `page.goto("/")`; there is no page reuse or `beforeEach` navigation (`e2e/purchasing/dashboard.spec.ts:4-6`).
- Before every normal Purchasing test, the automatic fixture calls `/health`, then concurrently primes `/api/fingerprint` and `/api/conservation/status` (`e2e/fixtures/copilot-fixture.ts:46-71`). The base-Playwright probes deliberately excluded this fixture to isolate page work.
- Once per Playwright invocation, global setup opens all four configured frontends concurrently and waits for `domcontentloaded` plus `main` (`e2e/global-setup.ts:5-10`, `e2e/global-setup.ts:16-34`). This affects command wall time, but is not repeated for each test in a multi-test invocation.
- `waitForScreenReady` waits first for the screen marker and then for zero unfinished panel markers (`e2e/helpers/ui.ts:36-39`).

## Time Budget (per test)

| Segment | Run 1 | Run 2 | Run 3 (retry) | Mean |
|---|---:|---:|---:|---:|
| Navigate + initial bundle/DOM load | 1,638 ms | 2,464 ms | 1,615 ms | 1,906 ms |
| DOM content loaded (already satisfied after `goto`) | 8 ms | 8 ms | 8 ms | 8 ms |
| Network idle | 4 ms | 3 ms | 10,529 ms | 3,512 ms |
| Screen ready | 5,663 ms | 5,604 ms | 29 ms | 3,765 ms |
| Panel ready | 1,954 ms | 1,973 ms | 10 ms | 1,312 ms |
| Assertion | 36 ms | 49 ms | 6 ms | 30 ms |
| **Test-body total** | **9,303 ms** | **10,101 ms** | **12,197 ms** | **10,534 ms** |
| Playwright list-reporter test duration | 9.9 s | 10.6 s | 12.5 s | 11.0 s |

Run 3's first attempt timed out at 30 s in `networkidle`; its retry produced the values above. On the two stable-shaped runs, 7.6 s of the 9.3-10.1 s body was spent waiting for screen-ready and panel-ready. Assertion cost was negligible. Reporter-minus-body overhead was about 0.3-0.6 s, so browser context/page creation is not the missing 7-8 s.

## Network Budget

The original requested probe timed out twice because the page never became network-idle. A diagnostic-only revision capped that wait at 15 s and printed the requests even when idle was not reached.

| Measurement | Run 1 | Run 2 |
|---|---:|---:|
| API request count | 241 | 30 |
| Sum of request durations (requests overlap) | 96,032 ms | 73,419 ms |
| Wall time | 16,917 ms | 10,147 ms |
| Network idle reached | No | Yes |
| Screen ready reached | Yes | Yes |

The request-duration sum is load, not wall time: many requests run concurrently. Run 1 issued approximately 170 repeated `/api/purchasing/economic/roi-summary` calls after initial loading, generally one every 30-60 ms. Run 2 did not enter that prolonged loop, but still issued two near-identical initial waves due to React development StrictMode and showed slow responses under concurrency.

Slowest completed endpoints in run 2 were:

- `/api/self/decisions`: 7,478 ms (second wave), 4,473 ms (first wave)
- `/api/self/audit-trail`: 6,330 ms and 3,630 ms
- `/api/self/accuracy-alerts`: 5,706 ms and 2,612 ms
- `/api/self/rule-lifecycle/active`: 5,696 ms and 2,917 ms
- `/api/context/today-summary`: 4,565 ms and 1,214 ms
- `/api/trajectory`: 4,396 ms for one completed copy; another remained incomplete at reporting

The duplicate initial waves are consistent with the explicit `React.StrictMode` wrapper (`apps/purchasing/frontend/src/main.tsx:6-10`). More importantly, the runaway ROI traffic has a direct code cause: `useData` reruns whenever its `loader` identity changes (`apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx:41-44`), while `NotYetPanel` passes a new inline loader on every render (`apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx:82-86`). The request resolves, updates state, rerenders, creates a new function, and triggers the effect again.

The dashboard itself also blocks screen-ready on a broad initial `Promise.all`, then makes per-low-item waste-history requests before clearing loading (`apps/purchasing/frontend/src/screens/DashboardScreen.tsx:103-155`). The ready marker is not rendered until that work completes (`apps/purchasing/frontend/src/screens/DashboardScreen.tsx:163-178`).

## Bundle Budget

All runs fetched 94 JavaScript/TSX/CSS/Vite resources.

The requested listener sampled `request().timing()` at the `response` event, before `responseEnd` was populated, so its per-resource values were negative and unusable. Its page-load observations were 3,849 ms and 22,717 ms. The listener was corrected temporarily to sample at `requestfinished`; two corrected runs measured:

| Measurement | Corrected run 1 | Corrected run 2 |
|---|---:|---:|
| `page.goto` to load | 12,645 ms | 2,554 ms |
| Resources fetched | 94 | 94 |

Corrected run 1's slowest resources were `copilot_sdk/frontend/index.ts` (10,215 ms), `DashboardScreen.tsx` (10,214 ms), and `OrderScreen.tsx` (10,156 ms). Corrected run 2's slowest resources were `DataTrustBadge.tsx` (251 ms), `ParLevelPanel.tsx` (246 ms), and `SpendSummaryPanel.tsx` (232 ms). This large warm/load-dependent variance confirms that Vite dev-mode module serving is a material secondary cost, but it does not explain the deterministic post-load request loop.

## Root Cause

The primary cause is **B + C, amplified by E**:

1. **Primary: repeated and duplicated API work.** An unstable inline `loader` prop creates a render/fetch loop for `/api/purchasing/economic/roi-summary`; the probe observed 241 API calls and no network-idle in one run. React StrictMode doubles mount effects in the dev build, explaining the paired initial request waves.
2. **Primary visible wait: screen/panel readiness.** In normal-shaped runs, the missing 7-8 s is almost exactly the 5.6 s screen-ready wait plus the 2.0 s panel-ready wait. Those markers are coupled to completion of large concurrent API batches.
3. **Secondary: Vite dev-mode module serving.** Ninety-four modules took 2.6-12.6 s in corrected runs and reached 22.7 s in an original page-load observation. This is highly variable and worsens cold or saturated runs.
4. **Not primary: Playwright per-test overhead.** The measured gap outside the test body was only about 0.3-0.6 s. The once-per-command global warmup can make isolated one-test invocations look much slower, especially when unrelated frontends are unavailable, but it does not explain each test's body time in the 10-test suite.

## Recommended Fix (ranked by impact)

1. **Stabilize the `NotYetPanel` loader** (for example, pass a module-level function or memoized callback) and add a regression test asserting one ROI-summary request per mount. This removes the unbounded request loop and restores reliable `networkidle` behavior.
2. **Reduce dashboard startup fan-out:** share/deduplicate requests, avoid fetching below-the-fold panels before the dashboard readiness gate, and make StrictMode effects abortable/idempotent. Do not remove StrictMode merely to hide duplicate-unsafe effects.
3. **Run E2E against a production build/preview server or ensure Vite dependency pre-bundling/warmup is complete before timing.** Also scope global setup to the selected project so an isolated Purchasing run does not warm unrelated frontends.
4. After the request loop and startup fan-out are fixed, increase safe worker concurrency above the current default of one (`e2e/playwright.config.ts:8`) and remeasure. Parallelism will reduce suite wall time but should not be used to mask per-test latency or backend saturation.

## Measurement notes

- The first attempted run before starting the externally managed stack was discarded: no configured port was listening, global setup timed out, and the probe hit the 30 s test timeout.
- The third timing invocation was flaky: its first attempt timed out at `networkidle`; the successful retry is reported.
- No production source file was modified during this diagnosis.
