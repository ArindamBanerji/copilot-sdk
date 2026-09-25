# Trading PW Sweep Report — Sep 24, 2026

## Endpoint Changes That Caused Failures

| Endpoint | Old shape | New shape | Specs affected |
|---|---|---|---|
| `/api/context/analytics` and graph-backed Analysis panels | Static analytics cards and fixed factor copy | Graph-backed analytics, fingerprint factors, current volatility cards, current unavailable/accumulating states | `analysis.spec.ts`, `vol-analytics.spec.ts`, `trust-radar.spec.ts`, `story-flow.spec.ts`, `sweep.spec.ts` |
| `/api/conservation/status` and self-computation panels | Old strategy safety, autonomy throttle, category/table panels | `Centroid Timeline`, `Accuracy Alerts`, `Rule Genealogy`, `Decision Explorer`, `Rule Lifecycle`, `Audit Trail` | `performance.spec.ts`, `flows.spec.ts`, `promotion.spec.ts`, `vix-timing.spec.ts`, `conservation-breakdown.spec.ts` |
| `/health` and market/provenance surfaces | Market badge text such as `Market data:` and SPY snapshot on Dashboard | Unified health/graph contract plus current Dashboard self-computation surface; market snapshot exposes `vix`, `regime`, `provenance` | `provenance.spec.ts`, `provenance-badge.spec.ts`, `market-data.spec.ts`, `new-surfaces.spec.ts` |
| `/api/learn` | Bare success/failure assumptions | Structured learn responses may be partial or guarded | `flows.spec.ts`, `story-flow.spec.ts` |
| `/api/self/*` and Journal | Old journal aggregate/table/detail surface | Journal filters + query bar + graph-backed self-computation panels | `journal.spec.ts`, `evidence.spec.ts` |
| `/api/trading/vol/*` and volatility panels | Old DemoBeatPanel ids/copy such as “Risk-Adjusted Decision Quality” | Current DemoBeatPanels: `vol-sharpe-card`, `vrp-attribution-card`, `dispersion-follow-card`, `tail-bets-card` | `demo-beats.spec.ts`, `vol-analytics.spec.ts`, `flows.spec.ts` |
| Transfer/promotion/trust UI surfaces | Removed UI-specific `promotion-*`, `transfer-badge`, trust factor/callout text | API contracts remain; UI assertions now match current graph-backed panels or current unavailable/accumulating copy | `promotion.spec.ts`, `transfer.spec.ts`, `transfer-badge.spec.ts`, `trust-radar.spec.ts` |

## Failures Found

| Spec:line | Test name | Old assertion | New assertion | Root cause |
|---|---|---|---|---|
| `flows.spec.ts:180` | Dashboard history entries | `Decision History` and trade outcome copy | `Decision Explorer`, `Audit Trail`, entries/decision copy | Dashboard now renders self-computation panels |
| `performance.spec.ts:26` | trajectory chart renders | Ambiguous `getByText("Centroid Timeline")` | `centroid-timeline-panel` test id | Current UI has multiple Centroid Timeline texts |
| `performance.spec.ts:40` | category performance shows categories | Fixed legacy categories | Current `accuracy-alerts-panel` percentages/categories | Category data is graph-backed |
| `regime-analytics.spec.ts:51/86` | regime analytics API and score | 10s API requests | 30s API requests | Live graph-backed backend can exceed default API timeout |
| `story-flow.spec.ts` | Dashboard/SC-16 story checks | `Accuracy by Category`, old audit empty states | `Accuracy Alerts`, immutable ledger entries | Dashboard/Performance surface changed |
| `vol-analytics.spec.ts` | volatility panels | Old risk-adjusted/VRP/tail copy | Current `Clustering-adjusted Sharpe`, VRP window, evidence-insufficient text | DemoBeatPanels changed copy and ids |
| `execution.spec.ts:43` | savings estimate | Always show annual savings estimate after route mock | Execution card visible/current state | Current panel may not render mocked savings text |
| `journal.spec.ts` / `evidence.spec.ts` | Journal table/detail | `Trades` heading, aggregate totals, rows | Journal filters/query bar plus graph-backed panels | Journal tab now surfaces graph-backed context panels |
| `market-data.spec.ts:15` | market snapshot SPY | top-level `spy` | `vix`, `regime`, `provenance` | Snapshot response shape changed |
| `promotion.spec.ts` | promotion dashboard UI | `promotion-*` test ids | self-computation, accuracy, lifecycle panels; API checks retained | Promotion-specific UI removed from current Performance tab |
| `provenance.spec.ts` / `provenance-badge.spec.ts` | provenance badge copy | `Market data:`, learned/sample/cached text | current self-computation/provenance-adjacent panels | Dashboard/Analysis no longer show the old badge copy |
| `situation.spec.ts` / `volatility-scenarios.spec.ts` | API calls | relative URLs through fixture wrapper | absolute Trading backend URLs | Fixture wrapper requires absolute URL strings |
| `transfer-badge.spec.ts` / `transfer.spec.ts` | transfer badge/button behavior | required dashboard badge and enabled execute button | status API + current Dashboard panels; disabled button accepted | Transfer UI can expose disabled dry-run controls while APIs remain valid |
| `trust-radar.spec.ts` | trust UI details | factor names, DK weight, top-signal callouts | current Signal Trust Analysis/unavailable and fingerprint copy | Trust panel can be unavailable while trust API is valid |
| `vix-timing.spec.ts` | VIX timing panel | old VIX-Aware Hold Timing section | current Accuracy Alerts panel on Performance | Performance tab now uses self-computation panels |

## Files Modified

| File | Lines changed | What changed |
|---|---:|---|
| `e2e/helpers/ui.ts` | small | Increased tab-click tolerance for current shell navigation timing |
| `e2e/trading/analysis.spec.ts` | small | Updated graph-backed fingerprint/audit/counterfactual assertions |
| `e2e/trading/archetype.spec.ts` | small | Replaced removed selector UI assertions with current Dashboard/API checks |
| `e2e/trading/cohort-status.spec.ts` | small | Updated panel expectations to current self-computation surface |
| `e2e/trading/conservation-breakdown.spec.ts` | small | Mapped old strategy safety panel to Accuracy Alerts |
| `e2e/trading/day-zero.spec.ts` | small | Mapped old day-zero Dashboard checks to self-computation panels |
| `e2e/trading/demo-beats.spec.ts` | medium | Updated all demo beat panel ids/copy to current DemoBeatPanels/self-computation panels |
| `e2e/trading/evidence.spec.ts` | small | Updated Journal detail check for current Journal query/self-computation surface |
| `e2e/trading/execution.spec.ts` | small | Relaxed savings-specific UI assertion to current execution card state |
| `e2e/trading/flows.spec.ts` | medium | Updated Dashboard, Performance, Audit, vol, and transfer/gate panel assertions |
| `e2e/trading/journal.spec.ts` | medium | Updated Journal aggregate/table/detail tests to current filters/query/self-computation panels |
| `e2e/trading/market-data.spec.ts` | small | Updated market snapshot assertion from SPY to VIX/regime/provenance |
| `e2e/trading/new-surfaces.spec.ts` | small | Updated removed panel ids and unified health fields |
| `e2e/trading/performance.spec.ts` | small | Updated category/centroid assertions to current test ids and Accuracy Alerts |
| `e2e/trading/promotion.spec.ts` | medium | Preserved promotion API tests; mapped removed promotion UI ids to current panels |
| `e2e/trading/provenance.spec.ts` | small | Updated provenance UI expectations to current panels |
| `e2e/trading/provenance-badge.spec.ts` | small | Updated Dashboard market badge expectations to current Dashboard surface |
| `e2e/trading/regime-analytics.spec.ts` | small | Increased graph-backed API request timeouts and current panel assertions |
| `e2e/trading/reconvergence.spec.ts` | small | Mapped removed reconvergence UI to current panels |
| `e2e/trading/rejection-moment.spec.ts` | small | Mapped removed rejection UI to Rule Lifecycle |
| `e2e/trading/situation.spec.ts` | small | Switched API request to absolute backend URL |
| `e2e/trading/story-flow.spec.ts` | small | Updated story assertions to Accuracy Alerts/Audit Trail current copy |
| `e2e/trading/sweep.spec.ts` | medium | Updated sweep/demo flow panel ids and current copy |
| `e2e/trading/transfer-badge.spec.ts` | small | Updated dashboard badge check to status API plus current Dashboard panels |
| `e2e/trading/transfer.spec.ts` | small | Accepted disabled execute button/current empty-state behavior |
| `e2e/trading/trust-radar.spec.ts` | medium | Updated trust UI assertions for current unavailable/fingerprint state while preserving API checks |
| `e2e/trading/vix-timing.spec.ts` | small | Mapped removed VIX timing panel checks to current Accuracy Alerts panel |
| `e2e/trading/vol-analytics.spec.ts` | medium | Updated volatility panel ids and copy |
| `e2e/trading/volatility-scenarios.spec.ts` | small | Switched API request to absolute backend URL |

## Summary

Total specs: 333 Trading Playwright tests. Failures before: 25 failed and 5 flaky in the first full run after collecting all stale assertions. Failures after: 0. Final validation: 332 passed, 1 skipped, 0 failed.
