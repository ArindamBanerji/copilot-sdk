# Phase 6 Operational Runbook

This runbook executes P6.3a, P6.3b, P6.3c, and P6.6 against the live
`soc_graph` AGE graph. Commands are PowerShell commands for Windows 11.
The runbook uses `--no-reseed` so the launcher does not reset or replace the
existing live graph.

## Prerequisites

Open PowerShell at the SDK root:

```powershell
Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
```

The launcher starts PostgreSQL when AGE is unavailable, but the explicit check
below is useful before running it. The repository's launcher uses PostgreSQL
17 on WSL2 at port 5433 and resolves the WSL2 NAT address dynamically:

```powershell
wsl -d Ubuntu-24.04 -u root -- bash -c "pg_ctlcluster 17 main start; su -c 'pg_isready -h 127.0.0.1 -p 5433' postgres"
$ip = (wsl -u root hostname -I).Trim().Split()[0]
$env:GRAPH_DSN = "host=$ip port=5433 dbname=soc_copilot user=postgres password=postgres sslmode=disable"
$env:GRAPH_BACKEND = "age"
$env:GRAPH_NAME = "soc_graph"
$env:AGE_GRAPH_NAME = "soc_graph"
```

Use the project environment used by the SDK tests:

```powershell
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
```

The five fixed graph policies are `soc`, `s2p`, `trading`, `purchasing`, and
`dataops`; `graph_config.toml` maps each to AGE and `soc_graph`. The launcher
injects the SOC and DataOps graph environment and the other apps inherit the
shared DSN/environment before loading their domain-specific `GraphConfig`.

## Step 1: Baseline Census

Run the census before starting or mutating the backends:

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
```

Record the complete console output. The known baseline is that all five
Decision domains exist, while conservation snapshots are absent, only S2P and
DataOps have checkpoints, only Trading has a Fingerprint, only S2P has evidence
receipts, anchors are incomplete, and TransferPattern/$604K entities are
absent.

## Step 2: Start All 5 Backends

Start all five backend processes without browsers and without reseeding:

```powershell
python demo.py --no-browser --no-reseed --health-timeout 180
```

The launcher starts these backend ports:

| Copilot | Port |
|---|---:|
| SOC | 8001 |
| S2P | 8002 |
| Trading | 8010 |
| Purchasing | 8020 |
| DataOps | 8030 |

The launcher waits up to 60 seconds for AGE-dependent backends and 30 seconds
for the others; `--health-timeout 180` overrides both. Verify the launcher
and AGE status:

```powershell
python demo.py --status
curl.exe http://127.0.0.1:8001/health
curl.exe http://127.0.0.1:8002/health
curl.exe http://127.0.0.1:8010/health
curl.exe http://127.0.0.1:8020/health
curl.exe http://127.0.0.1:8030/health
```

`demo.py --status` must show `AGE/PostgreSQL UP`, the shared `soc_graph`
line, and a `LIVE` graph proof. The launcher does not run preseed when
`--preseed` is omitted; `--no-reseed` also prevents bundle restore and fixture
seeding. That is intentional for this live census run.

## Step 3: Score/Learn Cycles (P6.3a)

The shared SDK request models are:

```json
{"category":"<category>","factors":{}}
```

for score, and:

```json
{"decision_id":"<score decision_id>","actual_action":"<score action>","outcome":"confirmed"}
```

for learn. `is_correct` is not a field in the shared `LearnRequest`; the
server derives correctness by comparing `actual_action` with the stored
recommendation. The PowerShell snippets below capture the score response and
send its actual `decision_id` and `action` to learn.

### 3.1 SOC

SOC uses `POST /api/alert/analyze` with the `ProcessAlertRequest` payload
`{"alert_id":"...","deployment_version":"v3.1","simulate_failure":false}`.
It uses `POST /api/alert/outcome` with the `OutcomeRequest` payload
`{"alert_id":"...","decision_id":"...","outcome":"correct","analyst_action":"..."}`.
The alert ID must come from the live queue; do not invent one.

```powershell
$queue = curl.exe -s http://127.0.0.1:8001/api/alerts/queue | ConvertFrom-Json
$alerts = @($queue.alerts ?? $queue.items ?? $queue.queue)
if ($alerts.Count -lt 5) { throw "SOC queue has fewer than 5 usable alerts" }
for ($i = 0; $i -lt 5; $i++) {
    $alertId = [string]($alerts[$i].alert_id ?? $alerts[$i].id)
    $analysis = curl.exe -s -X POST http://127.0.0.1:8001/api/alert/analyze `
      -H "Content-Type: application/json" `
      -d (@{alert_id=$alertId; deployment_version="v3.1"; simulate_failure=$false} | ConvertTo-Json -Compress) | ConvertFrom-Json
    $recommendation = $analysis.recommendation
    if (-not $recommendation.decision_id) { throw "SOC analyze returned no decision_id for $alertId" }
    curl.exe -s -X POST http://127.0.0.1:8001/api/alert/outcome `
      -H "Content-Type: application/json" `
      -d (@{alert_id=$alertId; decision_id=[string]$recommendation.decision_id; outcome="correct"; analyst_action=[string]$recommendation.action} | ConvertTo-Json -Compress)
}
curl.exe http://127.0.0.1:8001/health
curl.exe http://127.0.0.1:8001/api/soc/learning-health
```

### 3.2 S2P

S2P uses `POST /api/s2p/score`. Its required `ScoreRequest` fields are
`event_id`, `category`, `amount`, and `supplier_id`; the optional fields are
omitted below. It uses `POST /api/learn`, whose `LearnRequest` fields are
`decision_id`, `actual_action`, `outcome`, optional `context`, `reason_code`,
and `variant_id`.

```powershell
for ($i = 1; $i -le 5; $i++) {
    $score = curl.exe -s -X POST http://127.0.0.1:8002/api/s2p/score `
      -H "Content-Type: application/json" `
      -d (@{event_id="phase6-s2p-$i"; category="price_variance"; amount=1000.0; supplier_id="phase6-supplier-$i"} | ConvertTo-Json -Compress) | ConvertFrom-Json
    if (-not $score.decision_id) { throw "S2P score returned no decision_id" }
    curl.exe -s -X POST http://127.0.0.1:8002/api/learn `
      -H "Content-Type: application/json" `
      -d (@{decision_id=[string]$score.decision_id; actual_action=[string]$score.action; outcome="confirmed"} | ConvertTo-Json -Compress)
}
curl.exe http://127.0.0.1:8002/health
curl.exe http://127.0.0.1:8002/api/conservation/status
```

### 3.3 Trading

Trading mounts the shared scoring router at `/api`. Its exact request models
are the same shared SDK models described above. Empty `factors` is valid; the
scorer supplies the preset's neutral value `0.5` for omitted factors.

```powershell
for ($i = 1; $i -le 5; $i++) {
    $score = curl.exe -s -X POST http://127.0.0.1:8010/api/score `
      -H "Content-Type: application/json" `
      -d (@{category="trend_following"; factors=@{}} | ConvertTo-Json -Compress) | ConvertFrom-Json
    if (-not $score.decision_id) { throw "Trading score returned no decision_id" }
    curl.exe -s -X POST http://127.0.0.1:8010/api/learn `
      -H "Content-Type: application/json" `
      -d (@{decision_id=[string]$score.decision_id; actual_action=[string]$score.action; outcome="confirmed"} | ConvertTo-Json -Compress)
}
curl.exe http://127.0.0.1:8010/health
curl.exe http://127.0.0.1:8010/api/conservation/status
```

### 3.4 Purchasing

Purchasing also mounts the shared scoring router at `/api`; use its actual
preset category `protein` and the same shared score/learn models.

```powershell
for ($i = 1; $i -le 5; $i++) {
    $score = curl.exe -s -X POST http://127.0.0.1:8020/api/score `
      -H "Content-Type: application/json" `
      -d (@{category="protein"; factors=@{}} | ConvertTo-Json -Compress) | ConvertFrom-Json
    if (-not $score.decision_id) { throw "Purchasing score returned no decision_id" }
    curl.exe -s -X POST http://127.0.0.1:8020/api/learn `
      -H "Content-Type: application/json" `
      -d (@{decision_id=[string]$score.decision_id; actual_action=[string]$score.action; outcome="confirmed"} | ConvertTo-Json -Compress)
}
curl.exe http://127.0.0.1:8020/health
curl.exe http://127.0.0.1:8020/api/conservation/status
```

### 3.5 DataOps

DataOps mounts the shared scoring router at `/api`; use its actual preset
category `schema_change` and the same shared score/learn models.

```powershell
for ($i = 1; $i -le 5; $i++) {
    $score = curl.exe -s -X POST http://127.0.0.1:8030/api/score `
      -H "Content-Type: application/json" `
      -d (@{category="schema_change"; factors=@{}} | ConvertTo-Json -Compress) | ConvertFrom-Json
    if (-not $score.decision_id) { throw "DataOps score returned no decision_id" }
    curl.exe -s -X POST http://127.0.0.1:8030/api/learn `
      -H "Content-Type: application/json" `
      -d (@{decision_id=[string]$score.decision_id; actual_action=[string]$score.action; outcome="confirmed"} | ConvertTo-Json -Compress)
}
curl.exe http://127.0.0.1:8030/health
curl.exe http://127.0.0.1:8030/api/conservation/status
```

The five endpoint pairs are therefore:

| Copilot | Score endpoint | Learn/outcome endpoint | Port |
|---|---|---|---:|
| SOC | `POST /api/alert/analyze` | `POST /api/alert/outcome` | 8001 |
| S2P | `POST /api/s2p/score` | `POST /api/learn` | 8002 |
| Trading | `POST /api/score` | `POST /api/learn` | 8010 |
| Purchasing | `POST /api/score` | `POST /api/learn` | 8020 |
| DataOps | `POST /api/score` | `POST /api/learn` | 8030 |

## Step 4: Verify Artifacts Generated

Run the census again:

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
```

After successful learn/outcome cycles, all five domains should have at least
one conservation snapshot, checkpoint, domain anchor, fingerprint, and
evidence receipt. If a domain is absent, inspect that backend's console for
503/422 responses and repeat its score/learn loop with a fresh decision. The
SOC endpoint's artifact status is checked through its `learning-health` route;
the shared graph census remains authoritative for counts.

## Step 5: Seed the $604K Scenario (P6.3b)

The seeder requires existing Decisions in `soc`, `trading`, `s2p`, and
`dataops`, because it finds one Decision per linked domain before creating
ABOUT edges. The baseline census already contains those domains; if any is
missing, finish Step 3 first.

Apply the entities and edges:

```powershell
python scripts/seed_604k_scenario.py --apply --age-dsn $env:GRAPH_DSN --graph-name soc_graph
```

The command must report zero missing Decisions. Verify with the exact proof:

```powershell
python scripts/seed_604k_scenario.py --verify --age-dsn $env:GRAPH_DSN --graph-name soc_graph
```

Expected output includes `PASS: computed_value=604000.0` and at least two
distinct domains. A missing Decision exits with code 1 and identifies the
domain that needs more learn cycles.

## Step 6: Trigger Warm-Start (P6.3c)

The current census has a Trading Fingerprint, so the first runnable pair is
Trading → Purchasing:

```powershell
python scripts/trigger_warm_start.py --apply --source trading --target purchasing --age-dsn $env:GRAPH_DSN --graph-name soc_graph
python scripts/trigger_warm_start.py --verify --source trading --target purchasing --age-dsn $env:GRAPH_DSN --graph-name soc_graph
```

The script reads the latest source Fingerprint from AGE, builds a registry
from its factor names/statistics, calls `CompoundingScorer.warm_start()`, and
verifies the resulting TransferPattern. Missing source fingerprints are
reported as `NOT_PROVEN` and exit 1.

Claim 4 specifically requires validated transfers from SOC to S2P and
DataOps. After Step 3 has produced a SOC Fingerprint, run both required
proof edges:

```powershell
python scripts/trigger_warm_start.py --apply --source soc --target s2p --age-dsn $env:GRAPH_DSN --graph-name soc_graph
python scripts/trigger_warm_start.py --apply --source soc --target dataops --age-dsn $env:GRAPH_DSN --graph-name soc_graph
python scripts/trigger_warm_start.py --verify --age-dsn $env:GRAPH_DSN --graph-name soc_graph
```

## Step 7: Final Census

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
```

The final census should show all five Decision domains, conservation,
checkpoints, Fingerprints, EvidenceReceipts, and Domain anchors; the $604K
DomainContext entities should be present; and TransferPatterns should be
nonzero. Claim 4's required source/target rows must include SOC→S2P and
SOC→DataOps.

## Step 8: Run Claim Proof (P6.6)

The proof runner uses `GraphConfig.load()` and refuses an AGE connection unless
the supplied DSN matches the five configured domains. Execute it only with
AGE integration explicitly enabled:

```powershell
$env:AGE_INTEGRATION = "1"
New-Item -ItemType Directory -Force -Path out | Out-Null
python scripts/phase6_claim_proof.py --execute --age-dsn $env:GRAPH_DSN --graph-name soc_graph --report out/phase6_claims.json
```

Expected result is eight `PASS` lines after both SOC transfers and the $604K
seed exist. Claim 3 is `NOT_PROVEN` until the seed exists. Claim 4 remains
`NOT_PROVEN` if only Trading→Purchasing was run. Claim 5 reports computed
per-copilot totals and explicitly notes that the historical 315 value is
stale; it passes only when all five current domain totals are present.

## Step 9: Demo Status

```powershell
python demo.py --status | Tee-Object -FilePath out/demo_status.txt
```

Expected lines include:

```text
Shared judgment graph  soc_graph  domains: soc,s2p,trading,purchasing,dataops
Graph proof             LIVE ✓  decisions=<n> domains=<n> transfer_edges=<n>
```

## Step 10: Stop and Record

```powershell
python demo.py --stop
Copy-Item out/phase6_claims.json out/phase6_claims_final.json
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN | Tee-Object -FilePath out/graph_census_final.txt
```

Keep `out/phase6_claims_final.json`, `out/graph_census_final.txt`, and
`out/demo_status.txt` with the Phase 6 evidence package. If the backends must
remain available while collecting evidence, defer `--stop` until after the
operator has copied the outputs.

## Troubleshooting

- **AGE connection failed:** run `wsl -u root hostname -I`, rebuild
  `$env:GRAPH_DSN` with that address and `sslmode=disable`, then verify with
  `wsl ... pg_isready -h 127.0.0.1 -p 5433`.
- **Backend health fails:** run `python demo.py --status`, inspect the backend
  console opened by the launcher, and restart only the failed backend with
  `python demo.py --<copilot> --no-browser --no-reseed`.
- **Score returns 503:** check AGE connectivity and the backend's GraphConfig;
  the production scorer requires an injected AGE-backed GraphStore.
- **Learn returns 422:** verify the captured score `action` is sent as
  `actual_action`, and that the score category is one of the preset categories.
- **Learn returns 404:** use the exact `decision_id` returned by the immediately
  preceding score/analyze response.
- **Missing conservation after learn:** inspect scorer logs for the J6
  persistence coordinator and verify that the learn call reached the shared
  scorer path; the census is the graph-side check.
- **Warm-start `NOT_PROVEN`:** the source domain has no Fingerprint. Run more
  score/learn cycles for that source and confirm its Fingerprint count in the
  census before retrying.
- **Claim 4 remains `NOT_PROVEN`:** run both `soc -> s2p` and `soc -> dataops`
  warm-start commands; a Trading→Purchasing transfer alone does not satisfy
  the claim's locked pass condition.

## Evidence Basis

- `demo.py`: `COPILOTS`, `cmd_start`, `cmd_status`, and AGE DSN resolution.
- `copilot_sdk/backend/scoring_router.py`: shared `ScoreRequest` and
  `LearnRequest`, `/score`, `/learn`, and `/health` routes.
- `s2p-copilot/backend/app/routers/s2p.py`: S2P `ScoreRequest`, `LearnRequest`,
  and `/api/s2p/score` plus `/api/learn` routes.
- `gen-ai-roi-demo-v4-v50/backend/app/models/schemas.py` and
  `backend/app/routers/triage.py`: SOC analyze/outcome request models/routes.
- `scripts/seed_604k_scenario.py`: required Decision domains, apply/verify
  behavior, and the 604000.0 proof.
- `scripts/trigger_warm_start.py`: source Fingerprint loading and warm-start
  execution.
- `scripts/phase6_claim_proof.py`: eight claim queries, AGE integration gate,
  and report output.
