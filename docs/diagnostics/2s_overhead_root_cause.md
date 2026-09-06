# Purchasing 2-Second HTTP Overhead Root Cause

## Problem Statement

Purchasing HTTP requests measured about 2,050 ms even when endpoint handler execution measured about 0.53 ms. The narrow distribution suggested a fixed wait outside the handler. The experiments below were run on Windows on 2026-09-04 against a Purchasing Uvicorn process bound to `127.0.0.1:8020` without `--reload`.

The result is conclusive: requests addressed to `localhost` resolve to IPv6 `::1` first. Nothing is listening on `::1:8020`, and this Windows host takes approximately 2,050 ms to reject that connection. Python then retries the IPv4 result, `127.0.0.1`, where Uvicorn responds immediately. The delay is not in FastAPI, Purchasing middleware, AGE/PostgreSQL, file loading, or endpoint handlers.

## Phase 0: Code-Path Audit

| File | Per-request blocking I/O? | Finding |
|---|---:|---|
| `apps/purchasing/backend/app/main.py` | Endpoint-dependent | Middleware is registered at lines 454-467. Graph stores and the scorer proxy are constructed during app creation at lines 479-511, not recreated by universal middleware. `/health` does graph-backed IKS work at lines 882-895, but the same fixed delay also affects static endpoints and bare FastAPI. |
| `apps/purchasing/backend/app/services/purchasing_control.py` | No universal blocking I/O | `PurchasingEvidenceMiddleware.dispatch` awaits the downstream app at line 99, computes in-memory evidence headers, and only buffers JSON response bodies for a small claim-route subset at line 108. It performs no network connection or sleep. Other service methods can perform SQLite/graph I/O, but are not called on every route. |
| `copilot_sdk/tenant_middleware.py` | No | Lines 17-28 parse headers, set/reset a context variable, and await the downstream ASGI app. No file or network I/O. |
| `copilot_sdk/backend/scorer_proxy.py` | Graph I/O only when invoked | The graph store is created once in `__init__` at line 26. `_scorer()` caches `_scorer_instance` at lines 31-41; it does not recreate the scorer or call `create_graph_store` per request. Scorer methods may query the shared graph store, but health/static/bare comparisons eliminate this as the universal delay. |
| `copilot_sdk/config.py` | N/A | The requested path does not exist because `copilot_sdk.config` is a package. The implementation is `copilot_sdk/config/graph_config.py`. |
| `copilot_sdk/config/graph_config.py` | File I/O when `load()` is called | `GraphConfig.load` begins at line 89 and `_read_file` opens TOML at lines 178-199. It performs no network I/O. App construction calls it; the universal request middleware does not. |
| `copilot_sdk/graph/factory.py` | Connection possible at store construction | `create_graph_store` begins at line 129. AGE adapter construction occurs at lines 303-305 and can establish/use a database connection depending on the adapter. This construction is not on every request in `FreshScorerProxy`. |
| `apps/purchasing/backend/app/graph_status.py` | Connection possible only on creation | `create_purchasing_active_graph_store` begins at line 353 and invokes the selected factory at line 396. `create_app` invokes it once at startup (`main.py:479-483`). |
| `apps/purchasing/backend/app/context_router.py` | Small cached file read | `/items` at lines 252-265 checks `items.json` and uses `load_cached_json`; it has no graph/network call. Its 2.06-second `localhost` time versus 0-20 ms over IPv4 makes it the clean application control. |
| `copilot_sdk/backend/conservation_router.py` | Graph/scorer access when called | `/conservation/status` at lines 44-55 resolves its state provider and computes status. It is endpoint-specific and cannot explain equal delay on `/items` or bare FastAPI. |
| `copilot_sdk/backend/self_computation_router.py` | Graph access when called | `_gs()` at lines 53-54 returns the supplied shared store. Self endpoints such as `centroid_timeline` (line 145) and `accuracy_by_category` (line 413) query it; no store is created by `_gs()`. |

## Experiment Results

### A: Endpoint Comparison

All requests in Experiment A used `http://localhost:8020`. A warm request preceded each displayed series. `avg=-1` means the warm request returned an HTTP error and the supplied harness skipped its timed samples; it is not a latency result.

#### Run 1

| Endpoint | Average ms | Five samples (ms) |
|---|---:|---|
| `/api/health` | 2228.1 | 2219.7, 2225.4, 2250.0, 2223.7, 2221.8 |
| `/health` | 2110.0 | 2102.5, 2088.1, 2119.3, 2100.5, 2139.7 |
| `/api/context/items` | 2058.9 | 2072.5, 2063.7, 2050.9, 2054.5, 2052.9 |
| `/api/inventory/summary` | 2071.1 | 2073.2, 2078.9, 2057.3, 2067.0, 2079.1 |
| `/api/conservation/status` | 2121.8 | 2120.7, 2094.0, 2128.2, 2143.0, 2123.1 |
| `/api/fingerprint` | 2055.7 | 2047.2, 2062.5, 2063.1, 2047.1, 2058.6 |
| `/api/self/centroid-timeline` | -1 | skipped after warm HTTP error |
| `/api/self/accuracy-by-category` | 2109.2 | 2070.1, 2114.3, 2123.3, 2139.5, 2098.7 |
| `/api/context/waste-history/chicken_breast` | 2068.4 | 2081.2, 2083.9, 2050.7, 2055.5, 2070.7 |
| `/api/context/order-metadata` | -1 | skipped after warm HTTP error |
| `/api/purchasing/waste/summary` | 2063.1 | 2057.4, 2063.9, 2045.5, 2085.3, 2063.3 |
| `/api/purchasing/fingerprint` | 2074.0 | 2068.4, 2082.0, 2077.6, 2073.5, 2068.4 |

A2 classified 10 successful endpoints slow and zero fast. The three-sample averages ranged from 2,059.5 ms (`/api/context/items`) to 2,208.4 ms (`/api/health`).

#### Run 2

| Endpoint | Average ms | Five samples (ms) |
|---|---:|---|
| `/api/health` | 2226.3 | 2214.4, 2197.6, 2222.2, 2230.6, 2266.7 |
| `/health` | 2109.7 | 2094.2, 2099.6, 2106.1, 2120.7, 2127.9 |
| `/api/context/items` | 2065.3 | 2050.8, 2073.4, 2068.4, 2072.5, 2061.2 |
| `/api/inventory/summary` | 2067.0 | 2088.8, 2070.8, 2053.3, 2075.9, 2046.2 |
| `/api/conservation/status` | 2150.5 | 2144.3, 2154.0, 2193.9, 2109.2, 2151.3 |
| `/api/fingerprint` | 2073.2 | 2080.5, 2071.2, 2076.2, 2060.9, 2077.3 |
| `/api/self/centroid-timeline` | -1 | skipped after warm HTTP error |
| `/api/self/accuracy-by-category` | 2113.3 | 2133.8, 2096.1, 2114.6, 2092.2, 2129.6 |
| `/api/context/waste-history/chicken_breast` | 2067.6 | 2066.8, 2054.8, 2064.0, 2049.7, 2102.6 |
| `/api/context/order-metadata` | -1 | skipped after warm HTTP error |
| `/api/purchasing/waste/summary` | 2069.6 | 2073.7, 2065.4, 2055.2, 2085.6, 2067.9 |
| `/api/purchasing/fingerprint` | 2061.7 | 2064.1, 2047.6, 2066.8, 2066.8, 2063.3 |

A2 classified 11 successful endpoints slow and zero fast; one previously failing endpoint responded during classification. A2 averages ranged from 2,061.7 to 2,263.6 ms.

#### Run 3

| Endpoint | Average ms | Five samples (ms) |
|---|---:|---|
| `/api/health` | 2223.4 | 2237.4, 2224.5, 2197.3, 2227.3, 2230.7 |
| `/health` | 2102.2 | 2098.1, 2083.1, 2113.9, 2095.3, 2120.7 |
| `/api/context/items` | 2062.2 | 2036.7, 2087.4, 2081.3, 2065.2, 2040.4 |
| `/api/inventory/summary` | 2065.2 | 2058.9, 2059.9, 2077.2, 2075.3, 2054.7 |
| `/api/conservation/status` | 2139.5 | 2123.7, 2142.9, 2124.8, 2133.0, 2173.0 |
| `/api/fingerprint` | 2047.5 | 2045.8, 2050.7, 2036.8, 2043.9, 2060.5 |
| `/api/self/centroid-timeline` | 2112.0 | 2126.8, 2096.5, 2100.1, 2120.8, 2115.7 |
| `/api/self/accuracy-by-category` | 2125.9 | 2108.2, 2151.0, 2125.9, 2113.4, 2131.0 |
| `/api/context/waste-history/chicken_breast` | 2062.4 | 2075.5, 2061.1, 2052.9, 2060.4, 2062.1 |
| `/api/context/order-metadata` | -1 | skipped after warm HTTP error |
| `/api/purchasing/waste/summary` | 2081.2 | 2068.3, 2070.5, 2126.8, 2074.6, 2065.7 |
| `/api/purchasing/fingerprint` | 2054.1 | 2059.7, 2036.2, 2056.3, 2062.9, 2055.2 |

A2 classified 10 successful endpoints slow and zero fast. A2 averages ranged from 2,060.4 to 2,223.8 ms.

### B: Bare vs Full FastAPI

The first bare-server run produced `/bare/health` samples of 2069.0 and 2067.4 ms before later samples timed out because the parent diagnostic invocation was interrupted while its child server was still active. The two successful bare responses are sufficient for the isolation: a new FastAPI app with no Purchasing middleware, no graph, and a constant dictionary handler still paid the same approximately 2.07-second delay when addressed as `localhost:8099`.

In the same run, the full server measured:

- `/api/health`: average 2212.6 ms (2233.0, 2214.5, 2232.6, 2187.9, 2195.1)
- `/api/context/items`: average 2068.3 ms (2075.6, 2089.0, 2014.1, 2097.6, 2065.2)

The later bare repetitions were invalidated by the orphaned port-8099 child and are not treated as evidence. This operational issue is confined to the temporary diagnostic harness.

### C: TestClient vs HTTP

| Run | Endpoint | TestClient average ms | HTTP `localhost` average ms |
|---:|---|---:|---:|
| 1 | `/api/health` | 310.6 | 2225.2 |
| 1 | `/api/context/items` | 9.3 | 2067.7 |
| 1 | `/api/inventory/summary` | 10.3 | 2060.4 |
| 1 | `/api/conservation/status` | 83.7 | 2134.6 |
| 2 | `/api/health` | 257.5 | 2225.5 |
| 2 | `/api/context/items` | 7.0 | 2062.1 |
| 2 | `/api/inventory/summary` | 9.2 | 2059.3 |
| 2 | `/api/conservation/status` | 71.8 | 2146.1 |

TestClient bypasses TCP name/address connection. Its fast static endpoints prove the delay is outside the ASGI middleware/handler stack. `/api/health` and conservation have additional real computation, but their HTTP totals still contain the same approximately 2-second transport penalty.

### D: Timeout Constants and PostgreSQL Connectivity

Two scans returned the same relevant result:

- No `timeout=2`, `connect_timeout=2`, or `sleep(2)` was found in the Purchasing production request path.
- Hits were demo sleeps, test constants, migration tooling, and the temporary scanner itself.
- Installed driver: psycopg 3.3.3.
- Active graph DSN targeted `172.22.74.149:5433` (credentials redacted).
- Run 1 TCP connection attempts: 16 ms, 16 ms, 0 ms.
- Run 2 produced the same conclusion: the database was reachable without a 2-second connection wait.

Graph configuration loading only reads local environment/TOML. Graph store creation can connect to AGE, but it occurs during app construction and the active store/scorer are reused. PostgreSQL is therefore neither the universal delay nor the fixed timeout source.

### E: Network Stack Isolation

#### Run 1

| Probe | Samples |
|---|---|
| Raw socket to `127.0.0.1` | 10, 10, 6 ms |
| `http.client` to `127.0.0.1` | 18, 5, 9 ms |
| `urllib` to `127.0.0.1` | 16, 14, 0 ms |
| `localhost` `/api/health` | average 2248.8 ms; 2250.7, 2216.5, 2279.2 |
| `127.0.0.1` `/api/health` | average 159.8 ms; 153.7, 172.1, 153.6 |

#### Run 2

| Probe | Samples |
|---|---|
| Raw socket to `127.0.0.1` | 9, 41, 16 ms |
| `http.client` to `127.0.0.1` | 16, 18, 13 ms |
| `urllib` to `127.0.0.1` | 20, 12, 16 ms |
| `localhost` `/api/health` | average 2228.8 ms; 2259.8, 2218.0, 2208.6 |
| `127.0.0.1` `/api/health` | average 161.8 ms; 152.2, 178.4, 154.9 |

Additional address-family probe:

- `socket.getaddrinfo("localhost", 8020)` returned `::1` first, then `127.0.0.1`.
- Direct connect to `::1:8020`: `ConnectionRefusedError` after **2049.9 ms**.
- Direct connect to `127.0.0.1:8020`: connected in **0.0 ms**.
- `urllib.request.proxy_bypass("localhost")` was false, but the proxy map was empty; no proxy was involved.
- Windows hosts file lines 19-21 map IPv4 localhost and leave the IPv6 line commented, yet Windows still synthesizes/resolves `localhost` to `::1` first.

## Root Cause Determination

The 2 seconds are spent in the client-side TCP connection attempt to IPv6 loopback, before the request reaches Uvicorn or any FastAPI middleware:

1. The client asks for `localhost`.
2. Windows returns `::1` before `127.0.0.1`.
3. Uvicorn is listening only on `127.0.0.1:8020`.
4. The connect to `::1:8020` waits approximately 2,050 ms and fails.
5. The client retries `127.0.0.1:8020`; the request then completes normally.

This is a fixed TCP connect failure/retry delay, not an application timeout, database connection, or file scan. There is no Purchasing backend source line that adds it. The exact triggering address choice was demonstrated at temporary probe `scripts/network_test.py:52-57`; the machine configuration is `C:\Windows\System32\drivers\etc\hosts:19-21`, and the server launch used an IPv4-only bind. Importantly, the actual Purchasing frontend already avoids the issue by defaulting to `http://127.0.0.1:8020` at `apps/purchasing/frontend/src/api.ts:56`.

## Evidence Chain

1. **Endpoint independence:** static, graph-backed, health, and fingerprint routes all show the same fixed floor when called through `localhost`.
2. **Framework independence:** bare FastAPI with no Purchasing code reproduces approximately 2.07 seconds.
3. **ASGI elimination:** TestClient executes `/api/context/items` and `/api/inventory/summary` in roughly 7-10 ms while HTTP through `localhost` takes roughly 2.06 seconds.
4. **Client-library elimination:** raw socket, `http.client`, and `urllib` all complete quickly when explicitly using IPv4.
5. **Database elimination:** PostgreSQL connects in 0-16 ms and no per-request 2-second production timeout exists.
6. **Direct reproduction:** a socket connect to `::1:8020` alone takes 2049.9 ms and fails; the following IPv4 connect takes 0.0 ms.
7. **Exact removal:** substituting `127.0.0.1` for `localhost` removes approximately 2.05 seconds without any backend change.

## Recommended Fix

Use numeric IPv4 loopback in every local client URL: change `http://localhost:<backend-port>` to `http://127.0.0.1:<backend-port>`. For the original diagnostic/client, the single change is:

```text
http://localhost:8020  ->  http://127.0.0.1:8020
```

Do not change Purchasing middleware, scorer lifetime, graph configuration, or PostgreSQL timeouts; none causes this delay.

Blast radius is low and favorable. This changes only local loopback address selection and bypasses the slow failed IPv6 attempt. It is safe for all copilots whose development servers are bound to IPv4 loopback. The repository's Purchasing frontend and most E2E tests already use `127.0.0.1`, so production application code needs no fix. Any environment intentionally serving only on IPv6 must instead bind Uvicorn to `::1` or a dual-stack address; that is not this environment.

## Exit Summary

```text
2s overhead diagnosis complete.
  Experiments run: 11 suites/runs (A x3, B x1 usable, C x2, D x2, E x2, direct address-family probe x1)
  Root cause: localhost resolves to ::1 first; IPv6 connect refusal costs ~2,050ms before IPv4 fallback
  File:line: C:\Windows\System32\drivers\etc\hosts:19-21 (environment); no Purchasing source line adds delay
  Recommended fix: use http://127.0.0.1:8020 for local clients (and equivalent IPv4 loopback URLs for other copilots)
  0 source files modified (diagnostic report only).
```
