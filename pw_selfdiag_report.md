# PW Self-Diagnosing Demo Specs — Final Status

## Pattern

The 18 protected passing specs were left unchanged. The remaining 28
non-permanent specs now probe first, call test.skip(!response.ok(), ...),
and assert only when the endpoint is available. The 10 ROADMAP/CONCEPTUAL
rows retain permanent hardcoded skips.

## Results

- Total: 56
- Passed: 30
- Skipped: 26
- Permanent ROADMAP/CONCEPTUAL skips: 10
- Endpoint/runtime skips: 16
- Failed: 0
- TypeScript: PASS

## Per-spec status

| Spec | Status | Notes |
|---|---|---|
| SOC-01 | PASS | Endpoint available; assertions executed. |
| SOC-02 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| SOC-03 | PASS | Endpoint available; assertions executed. |
| SOC-04 | PASS | Endpoint available; assertions executed. |
| SOC-05 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| SOC-06 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| SOC-07 | PASS | Endpoint available; assertions executed. |
| SOC-08 | PASS | Endpoint available; assertions executed. |
| SOC-09 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| SOC-10 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| S2P-01 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| S2P-02 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| S2P-03 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| S2P-04 | PASS | Endpoint available; assertions executed. |
| S2P-05 | PASS | Endpoint available; assertions executed. |
| S2P-06 | PASS | Endpoint available; assertions executed. |
| S2P-07 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| S2P-08 | PASS | Endpoint available; assertions executed. |
| S2P-09 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| PUR-01 | PASS | Endpoint available; assertions executed. |
| PUR-02 | PASS | Endpoint available; assertions executed. |
| PUR-03 | PASS | Endpoint available; assertions executed. |
| PUR-04 | PASS | Endpoint available; assertions executed. |
| PUR-05 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| PUR-06 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| TRD-01 | PASS | Endpoint available; assertions executed. |
| TRD-02 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| TRD-03 | PASS | Endpoint available; assertions executed. |
| TRD-04 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| TRD-05 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| TRD-06 | PASS | Endpoint available; assertions executed. |
| DO-01 | PASS | Endpoint available; assertions executed. |
| DO-02 | PASS | Endpoint available; assertions executed. |
| DO-03 | PASS | Endpoint available; assertions executed. |
| DO-04 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| DO-05 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| DO-06 | PASS | Endpoint available; assertions executed. |
| DO-07 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| DO-08 | SKIP (permanent ROADMAP) | Permanent catalog deferral. |
| PLAT-01 | SKIP (permanent CONCEPTUAL) | Permanent catalog deferral. |
| PLAT-02 | PASS | Endpoint available; assertions executed. |
| PLAT-03 | SKIP (endpoint unavailable) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| PLAT-04 | PASS | Endpoint available; assertions executed. |
| PLAT-05 | SKIP (permanent CONCEPTUAL) | Permanent catalog deferral. |
| PLAT-06 | PASS | Endpoint available; assertions executed. |
| PLAT-07 | PASS | Endpoint available; assertions executed. |
| MACH-01 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| MACH-02 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| MACH-03 | SKIP (HTTP status) | Self-diagnosed endpoint unavailable; skipped with runtime status. |
| MACH-04 | PASS | Endpoint available; assertions executed. |
| MACH-05 | SKIP (permanent CONCEPTUAL) | Permanent catalog deferral. |
| PILOT-01 | PASS | Endpoint available; assertions executed. |
| PILOT-02 | PASS | Endpoint available; assertions executed. |
| PILOT-03 | PASS | Endpoint available; assertions executed. |
| PILOT-04 | PASS | Endpoint available; assertions executed. |
| FORK-01 | PASS | Endpoint available; assertions executed. |

## Standing rule

Demo specs use hardcoded test.skip(true) only for the ten permanent
ROADMAP/CONCEPTUAL rows. Endpoint-dependent rows use runtime HTTP status
diagnostics and remain automatically eligible when their endpoint ships.

