# Copilot E2E Tests

Playwright tests in this package expect the demo stack to be running externally:

- Trading: frontend `http://localhost:5174`, backend `http://localhost:8010`
- Purchasing: frontend `http://localhost:5175`, backend `http://localhost:8020`
- DataOps: frontend `http://localhost:5176`, backend `http://localhost:8030`

The Playwright config intentionally does not define `webServer`; use the repo launcher or your own terminal sessions to start the apps first.

## Setup

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
npm run test
```

Each test checks the matching backend `/health` endpoint before running and fails clearly when the live stack is not available.
