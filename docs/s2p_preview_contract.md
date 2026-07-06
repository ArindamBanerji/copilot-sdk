# S2P Preview Contract

## 1. Scope

S2P Preview is the frozen investor summary surface hosted inside the SOC demo on port 5173. It exists to show a stable, summary-level view of S2P value stories for investor demos.

S2P Product is the authoritative source-to-pay application hosted on port 5177. New S2P features, workflow changes, and product-depth panels belong in the Product first.

Preview panels are not updated by default when the Product changes. A Preview change requires an explicit decision, this contract document update, and an updated staleness date for any affected panel.

## 2. Panel -> Endpoint Map

Last updated date: 2026-07-06.

| Panel | Endpoint(s) | Provenance default | Last updated |
|---|---|---|---|
| FinancialImpactPanel | `/api/s2p/financial-impact` | `context` | 2026-07-06 |
| WorkingCapitalPanel | `/api/s2p/suppliers/payment-strategy`, `/api/s2p/suppliers/payment-portfolio` | `context` | 2026-07-06 |
| DisruptionSimPanel | `/api/s2p/simulation/scenarios`, `/api/s2p/simulation/impact-summary` | `context` | 2026-07-06 |
| CompliancePanel | `/api/s2p/compliance/report` | `context` | 2026-07-06 |
| ProcessFusionPanel | `/api/s2p/insight/process-signals`, `/api/s2p/insight/cross-graph` | `context` with API override from cross-graph provenance | 2026-07-06 |
| NoveltyPanel | `/api/s2p/novelty/status` | `context` | 2026-07-06 |
| TrendCorrelationPanel | `/api/s2p/suppliers/trends`, `/api/s2p/suppliers/early-warnings` | `sample` | 2026-07-06 |

## 3. Shared vs Preview-Only Endpoints

| Endpoint | Usage |
|---|---|
| `/api/s2p/financial-impact` | Shared by Preview and Product |
| `/api/s2p/suppliers/payment-strategy` | Shared by Preview and Product |
| `/api/s2p/novelty/status` | Shared by Preview and Product |
| `/api/s2p/insight/process-signals` | Shared by Preview and Product |
| `/api/s2p/insight/cross-graph` | Shared by Preview and Product |
| `/api/s2p/simulation/scenarios` | Shared by Preview and Product |
| `/api/s2p/simulation/impact-summary` | Shared by Preview and Product |
| `/api/s2p/suppliers/early-warnings` | Shared by Preview and Product |
| `/api/s2p/compliance/report` | Preview-only |
| `/api/s2p/suppliers/payment-portfolio` | Preview-only |
| `/api/s2p/suppliers/trends` | Preview-only |

## 4. Provenance Rules

All Preview headline metrics must carry a `ProvenanceBadge`.

Static defaults are allowed because most S2P backend endpoints do not currently return provenance fields. The default tier is `context` for most panels. `TrendCorrelationPanel` defaults to `sample` because supplier trend data is fixture-backed.

If an API response includes provenance metadata, the API-provided value overrides the static default. Supported override fields are `provenance` and `source`.

`ProcessFusionPanel` uses real provenance from the cross-graph endpoint when available.

No `sample` headline may render without a visible sample badge. This is required for F-25 compliance.

## 5. Staleness Tracking

Panel staleness is tracked by the `Last updated` column in the panel map above. Any Preview panel behavior, endpoint, or displayed headline metric change must update that date.

Features in Product that are not part of the frozen Preview contract include:

- `SituationPanel`
- `FinancialImpactWidget`
- Product triage scoring workflow
- Product evidence and reasoning panels
- Product-specific Playwright specs under `copilot-sdk/e2e/s2p/`

These Product features should not be copied into Preview unless an explicit Preview expansion decision is made.

## 6. PW Spec Ownership

Preview Playwright specs live in:

`gen-ai-roi-demo-v4-v50/frontend/tests/e2e/`

Product Playwright specs live in:

`copilot-sdk/e2e/s2p/`

Preview specs should assert frozen investor-summary behavior. Product specs should assert authoritative S2P application behavior.

## 7. Change Rules

Adding a Preview panel requires:

- An explicit decision to expand the frozen Preview surface.
- A new row in this contract document.
- Endpoint ownership recorded in the shared vs preview-only table.
- Provenance default and API override behavior documented.
- Playwright coverage in the Preview spec directory.

Changing an existing Preview panel requires:

- Updating this contract document.
- Updating the affected panel's staleness date.
- Preserving visible provenance badges for all headline metrics.

No new Preview panels should be added unless explicitly decided. The default destination for new S2P functionality is the Product.
