# B31 Hero Moments Runbook

This runbook describes the live runner in `scripts/hero_moments.py`.
It is intentionally limited to `scripts/` and documentation; the requested
scope does not permit editing `demo.py`, application backends, or tests.

## Beats

| CLI beat | Storyboard mapping | Proof required |
|---|---|---|
| `c2` | C-2 / score→learn | A real score, a real learn/outcome receipt, and a measured before/after state. |
| `c3` | C-3 / counterfactual and twin | Frozen Twin endpoint plus a non-zero delta exposed by the backend. |
| `c4` | C-4 / day-zero and authority | A live promotion-check response reporting advancement. |
| `c5` | C-5 / staged trust and refusal | Conservation state is actually RED and promotion is actually blocked. |

The storyboard’s named net-new items are DM-1, CF-1, DZ-1, and ST-5. The
runner keeps the requested `c2`–`c5` API names while returning the actual
backend status. It never converts an unavailable endpoint or an absent delta
into a success claim.

## Usage

```text
python scripts/hero_moments.py --copilot trading --port 8010 --beat c2
python scripts/hero_moments.py --copilot trading --port 8010 --beat c3 --json
python scripts/hero_moments.py --all --json
```

`--all` runs C2–C5 for SOC, S2P, Trading, Purchasing, and DataOps using the
standard local ports. `*_URL` environment variables override those URLs.

Each result contains `status`, `message`, `before`, `after`, `evidence`, and
`events`. Statuses are `measured`, `completed`, `available`, `blocked`,
`unsupported`, `inconclusive`, or `unavailable`. Only `measured` is a measured
hero claim; `completed` means the operation happened but its requested metric
was not exposed.

## Scope limitation

The user-required scope forbids modifying `demo.py` and `tests/`, so this
session does not add a `demo.py --hero` flag or HM-01–HM-12 test module.
The runner is standalone and can be called by a future demo integration once
that scope is opened. Repeated C2 runs submit a new live decision unless the
backend’s own outcome path deduplicates the supplied hero context; the runner
reports state rather than claiming idempotency it cannot verify.
