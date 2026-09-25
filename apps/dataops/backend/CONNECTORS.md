# DataOps SAP and Celonis connectors

With no connector environment variables configured, the demo uses the bundled
SAP and Celonis samples without making HTTP requests. The dashboard health bar
and badges read `/api/context/enterprise-health`; SAP records and Celonis data
use the same application-owned connector instances. These context routes and
the existing enterprise routes are already mounted in `app/main.py`.

To enable live reads, set these variables before starting the DataOps backend:

| Variable | Purpose |
| --- | --- |
| `SAP_API_KEY` | SAP Business Accelerator Hub sandbox API key. |
| `SAP_BASE_URL` | Optional OData service root; defaults to `https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap`. |
| `CELONIS_LIVE=true` | Enable the public Developer Portal demo with its demo token. |
| `CELONIS_URL` | Optional Knowledge Model API root, ending in `/intelligence/api`. |
| `CELONIS_TOKEN` | Bearer token for a configured customer tenant. The public demo accepts a placeholder token. |

The Celonis demo root is
`https://16abf815-424c-413e-b92d-6c6f8fc633cd.remockly.com/intelligence/api`.
The connector uses `/knowledge-models`, `/{km_id}/kpis`, and `/{km_id}/data`
under that collection. The demo data request selects `MATERIALS.ACTIVITY`,
`AVG_EVENTS_PER_CASE`, and `FILTERED_COUNT` for
`open-purchase-requisition.purchase-requisition-km`.
See the [official Celonis demo contract](https://developer.celonis.com/process-intelligence-apis/knowledge-model-api/api-reference/try-it/).

SAP reads the OData V2 `A_PurchaseOrder`, `A_SupplierInvoice`, and
`A_BusinessPartner` collections with `APIKey`, `$format=json`, `$top`, and
`$skip`. These are read-only calls with a 10-second HTTP timeout.

Each distinct request is attempted once per connector lifetime. Validated
responses are retained in memory and written atomically to
`backend/data/connector_snapshots/`. Keys isolate the base URL, credential
identity, endpoint, and query parameters. Later reads reuse those responses;
restart the backend to make another live attempt. Snapshots do not overwrite
the checked-in samples. If a request fails, including TLS certificate failures,
the connector uses a matching captured response or its bundled sample. Missing
or corrupt samples produce empty data and unavailable health. Certificate
verification stays enabled; failures generate a warning without credentials.

Responses distinguish `*_live` from `*_cache` and include provenance:
`sandbox`, `external`, or `sample`. A successful network call to Remockly is
still sandbox data. Sample P2P process data is never returned for an unrelated
customer Knowledge Model. The process timeline remains the explicitly labeled
cached demo scenario: the KM demo's event-count KPIs are not duration metrics.
No measured financial savings are inferred from these sample records.

Verification from the SDK root, using the project Python environment:

```powershell
python -m pytest apps/dataops/backend/tests -q --timeout=120
```

For the component smoke test, start Vite from `apps/dataops/frontend`:

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5188 --strictPort
```

Then, from the SDK root:

```powershell
node apps/dataops/frontend/tests/dcel-panels.cjs
```

The smoke test uses the workspace's existing `e2e` Playwright installation and
mocked API responses; it requires no live SAP, Celonis, or graph service.
