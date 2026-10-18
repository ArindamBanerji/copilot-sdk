# Copilot E2E Tests

Playwright tests in this package expect the demo stack to be running externally:

- Trading: frontend `http://127.0.0.1:5174`, backend `http://127.0.0.1:8010`
- Purchasing: frontend `http://127.0.0.1:5175`, backend `http://127.0.0.1:8020`
- DataOps: frontend `http://127.0.0.1:5176`, backend `http://127.0.0.1:8030`
- SOC: frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8001`
- S2P: frontend `http://127.0.0.1:5177`, backend `http://127.0.0.1:8002`

The Playwright config intentionally does not define `webServer`; use the repo launcher or your own terminal sessions to start the apps first.

## Setup

Run these commands from this `e2e` directory so the local Playwright runner and
the test package resolve to the same installation.

```powershell
npm install
npx playwright install chromium
npm run typecheck
```

## Run

```powershell
npm run test:trading
npm run test:purchasing
npm run test:dataops
npm run test:demo-cuts
npm run test
```

To rebuild a clean, pinned five-copilot demo state and capture the outreach
dashboard surfaces at 1440x900, run:

```powershell
npm run capture:screenshots
```

The command uses `demo.py --kill-all` followed by the launcher's checked
`--preseed` restart, then writes full-page PNGs under `../screenshots/<copilot>`
and a run manifest to `../screenshots/manifest.json`. Every capture defaults to
`illustrative_preseed`; use `measured` only for a real experiment or metric
readout. If the already-preseeded stack is running, `npm run
capture:screenshots:only` reruns only the Playwright capture.

Each test checks the matching backend `/health` endpoint before running and fails clearly when the live stack is not available.
