# Vite proxy analysis

Audit date: 2026-09-05. The test compared `127.0.0.1:8020` (the Purchasing Uvicorn backend) with `127.0.0.1:5175` (the Purchasing Vite development server). Two sequential/concurrent samples were collected. No application configuration or source was changed.

## Summary

**Vite is not a serialization bottleneck because Purchasing does not configure a Vite API proxy.**

`apps/purchasing/frontend/vite.config.ts` defines:

```ts
"import.meta.env.VITE_API_URL": JSON.stringify(`http://${HOST}:8020`)
```

and has only `server.host`; it has no `server.proxy`, `target`, `rewrite`, or `changeOrigin` setting. The Purchasing frontend API module also uses `VITE_API_URL` with a direct `:8020` fallback.

Port 5175 is serving the Purchasing Vite page, but `/api/*` is not forwarded. `GET http://127.0.0.1:5175/api/health` returned `200 text/html`, 560 bytes, containing the Vite client and `<title>Purchasing Copilot</title>`. In contrast, direct `:8020` returned `200 application/json` with `Server: uvicorn` and a 1,929-byte health payload. Therefore the apparent fast proxy timings are Vite SPA fallback responses, not API results, and cannot be used to calculate proxy overhead.

## Vite configuration

| Copilot | API configuration |
|---|---|
| Purchasing | No proxy. `VITE_API_URL` is `http://127.0.0.1:8020`. |
| DataOps | `/api` proxy target `http://127.0.0.1:8030`. |
| Trading | Has an `/api` proxy configuration. |
| S2P | No proxy stanza in its Vite config; API URL is direct `:8002`. |

The hypothesis would apply to DataOps/Trading only after measuring their configured Vite ports and backend ports. It does not apply to the active Purchasing frontend at port 5175.

## Sequential: direct backend versus port 5175

Each endpoint was requested three times in each of two runs (six samples per destination). Direct rows are valid Uvicorn JSON responses. Port-5175 rows are invalid comparison data because they are the same 560-byte Vite HTML fallback.

| Endpoint | Direct `:8020` mean | Port `:5175` mean | Interpretation |
|---|---:|---:|---|
| `/api/health` | 380.4 ms | 24.2 ms | Vite HTML fallback, not health JSON. |
| `/api/context/items` | 24.3 ms | 18.2 ms | Vite HTML fallback, not context JSON. |
| `/api/fingerprint` | 11.5 ms | 20.6 ms | Vite HTML fallback, not fingerprint JSON. |
| `/api/conservation/status` | 65.3 ms | 18.4 ms | Vite HTML fallback, not conservation JSON. |
| `/api/self/accuracy-by-category` | 174.4 ms | 18.2 ms | Vite HTML fallback, not accuracy JSON. |

No sequential proxy overhead can be computed because the response identity, content type, and body size differ. The valid direct endpoint mean across the five endpoint means is 131.2 ms; it is backend work, not proxy work.

## Concurrent: direct backend versus port 5175

Five endpoints were fetched concurrently, three times per run, for two runs.

| Destination | Wall time, six runs | Mean parallelism | Validity |
|---|---|---:|---|
| Direct `:8020` | 342.7, 377.2, 461.8, 454.3, 649.0, 1,063.4 ms | 3.11× | Valid backend JSON responses. |
| Port `:5175` | 22.6, 28.5, 35.2, 48.9, 52.7, 53.5 ms | 3.82× | Invalid: five Vite HTML fallback responses. |

The direct backend is demonstrably concurrent: its parallelism ratio is well above 1.0. There is no evidence of serialization at port 5175, but more importantly there is no API proxy there to test.

## POST `/api/score`

The requested body was `{"item": "chicken_breast", "quantity": 10}`.

| Destination | Six timings | Response |
|---|---|---|
| Direct `:8020` | 11.1–147.6 ms; 52.2 ms mean | `422 Unprocessable Entity`: this body does not satisfy the backend score request schema. No decision was created. |
| Port `:5175` | 6.6–32.4 ms; 15.3 ms mean | `404 Not Found`: no `/api/score` proxy route exists. |

This POST comparison does not exercise scoring work or a Vite proxy. A valid direct score request would persist a decision, so it was not substituted for the specified invalid payload during this read-only diagnostic.

## Verdict

**Proxy adds: not measurable; no Purchasing Vite proxy exists.**

**Serializes: no evidence.** The direct Uvicorn endpoint handled five heterogeneous API requests at mean 3.11× parallelism. Port 5175 cannot be assessed as a proxy because it did not forward any tested `/api/*` request.

## Impact on Playwright tests

Purchasing Playwright/browser traffic should use the API URL injected by Vite (`http://127.0.0.1:8020`), not assume that `:5175/api/*` is a working backend route. Requests mistakenly made relative to the Vite origin can appear to succeed with HTTP 200 while receiving the frontend HTML document. Tests should assert JSON content type or response shape, not status code alone.

The direct timings also show backend-side variability: `/api/health` and `/api/self/accuracy-by-category` were materially slower than fingerprint/context endpoints, and concurrent direct runs ranged from 343 ms to 1,063 ms wall time. That variability should be investigated at the backend/graph layer separately from Vite.

## Recommended action

Do not add or tune a Purchasing Vite proxy to address the reported 19 s score latency. Instrument and time the direct `:8020` request path instead.

If a same-origin proxy is intentionally introduced later, add `server.proxy['/api']` with target `http://127.0.0.1:8020`, then repeat this experiment using response-content validation. For the existing proxy hypothesis, run the equivalent test against DataOps or Trading, whose Vite configs actually declare `/api` proxies.
