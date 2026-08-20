# Create a copilot in 5 minutes

This is the L-CDK open-source developer cut. It creates a small, runnable
copilot project with a typed tensor configuration, a health endpoint, an
observation-only score surface, four starter screens, and a smoke test.

## 1. Install the SDK

```powershell
pip install copilot-sdk
```

The generator uses only the Python standard library. The generated backend
uses FastAPI, which is available through the SDK development extras when you
want to run it locally:

```powershell
pip install "copilot-sdk[dev]"
```

## 2. Create `copilot.yaml`

```yaml
name: "line-check-copilot"
domain: "inventory"
tensor:
  categories: 5
  actions: 4
  factors: 3
penalty_ratio: 3.0
accent_color: "#4CAF50"
ports:
  backend: 8040
  frontend: 5178
conservation:
  eta_confirm: 0.05
  eta_override: 0.01
  q_window: 400
factors:
  - name: "demand_signal"
    type: "numeric"
  - name: "supplier_reliability"
    type: "categorical"
  - name: "delivery_window"
    type: "numeric"
```

The tensor counts and factor definitions are validated before any files are
written. Names are converted to safe lowercase project identifiers.

## 3. Generate the project

From the SDK checkout, or from an installed SDK:

```powershell
python scripts/create_copilot.py --config copilot.yaml --output apps/line-check
```

The same generator is available as a module:

```powershell
python -m copilot_sdk.scaffold --config copilot.yaml --output my-copilot
```

Generated files include:

```text
my-copilot/
  backend/app/main.py
  backend/app/config.py
  backend/tests/test_smoke.py
  frontend/src/CopilotShell.tsx
  frontend/src/screens/{Dashboard,Analysis,Performance,LogDecision}Screen.tsx
  copilot.yaml
```

## 4. Run the smoke test

```powershell
cd my-copilot
python -m pytest backend/tests
```

## 5. Run the starter backend

```powershell
uvicorn backend.app.main:app --reload --port 8040
```

Open `/health` to confirm the generated domain identity. The starter
`/api/score` response is deliberately observation-only; connect real factors,
human verification, and measured outcomes before making product claims.

## What this cut does not do

The scaffold is a starting point, not a domain preset. It does not provide
calibrated centroids, customer evidence, financial impact, or autonomous
execution. Those are application responsibilities and should be added with
the SDK protocols and the evidence rules of the target domain.

