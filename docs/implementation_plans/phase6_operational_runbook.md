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
uses `_build_graph_env()` and `env.update()` to inject explicit AGE graph
environment variables for all five copilots. Operators still need to set the
parent environment before running standalone scripts such as the census,
seeder, or warm-start tool.

## Step 1: Baseline Census

Run the census before starting or mutating the backends:

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
```

Record the complete console output. The July 30 live baseline was:

| Copilot | Decisions | Conservation | Checkpoints | Fingerprints | Receipts | Conservation/J6 |
|---|---:|---:|---:|---:|---:|---|
| SOC | 4862 | 1 | 0 | 0 | 0 | RED, non-scorable / blocked |
| S2P | 25111 | 1 | 50 | 1 | 163 | GREEN, α=1.0 / ready |
| Trading | 1582 | 101 | 0 | 138 | 101 | GREEN, α=1.0 / ready |
| Purchasing | 1101 | 1 | 0 | 2 | 1 | GREEN, α=1.0 / ready |
| DataOps | 722 | 1 | 50 | 2 | 1 | GREEN, α=1.0 / ready |

All five domains had AGE/soc_graph and ProtocolV2 infrastructure. Domain
anchors existed for all five domains. The platform verdict was `READY`.

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
python demo.py --dump
```

`demo.py --status` must show `AGE/PostgreSQL UP`, the shared `soc_graph`
line, and a `LIVE` graph proof. `demo.py --dump` must show all five
infrastructure layers as `ok` and a present conservation status; this is the
Rule #78 live startup gate. Keep the saved dump JSON in the evidence package.
The launcher does not run preseed when
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

> **SOC LIMITATION:** All current demo alerts route to
> `refer_to_analyst` via the composite gate (confidence < 0.65, margin <
> 0.3). This is a non-scorable action. SOC outcome cycles will:
> - write a conservation snapshot (`CALIBRATING`, alpha=0);
> - not write fingerprints, evidence receipts, or checkpoints; and
> - not update centroids or learning state.
>
> SOC J6 artifacts require scorable actions (`escalate`, `investigate`,
> `suppress`, or `monitor`) with sufficient confidence to pass the composite
> gate. With the current demo alert set, this is not achievable.

SOC uses `POST /api/alert/analyze` with the `ProcessAlertRequest` payload
`{"alert_id":"...","deployment_version":"v3.1","simulate_failure":false}`.
It uses `POST /api/alert/outcome` with the `OutcomeRequest` payload
`{"alert_id":"...","decision_id":"...","outcome":"correct","analyst_action":"..."}`.
The alert ID must come from the live queue; do not invent one. Note: the SOC
queue returns alerts with field `id`, not `alert_id`; the fallback below
handles both names.

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

### 3.5b Mid-Session Instrumentation Checkpoint

Run `--dump` after the score/learn cycles and before seeding or warm-start:

```powershell
python demo.py --dump
```

The saved JSON is the pre-seed baseline. Compare it with the post-seed dump in
Step 7 to verify that seeding and warm-start produced the expected new
artifacts.

## Step 4: Verify Artifacts Generated

Run the census again:

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
```

Four domains (S2P, Trading, Purchasing, and DataOps) should have at least one
conservation snapshot, fingerprint, and evidence receipt. SOC will have a
conservation snapshot (`CALIBRATING`) but will not have fingerprints, receipts,
or checkpoints because of the non-scorable limitation documented in Step 3.1.

Checkpoints require successful consolidated learns and may not appear after a
single cycle. S2P and DataOps have pre-existing legacy checkpoints. All five
domains should have domain anchors. If a non-SOC artifact is absent, inspect
that backend's console for 503/422 responses and repeat its score/learn loop
with a fresh decision. The shared graph census remains authoritative for
counts.

Compare the census with a platform dump:

```powershell
python demo.py --dump
```

The diagnostics should show scorer state, conservation, and artifact counts
matching the census for all five copilots.

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

> **CLAIM 4 DEPENDENCY:** Claim 4 requires validated transfers from SOC to
> S2P and SOC to DataOps. These warm-start transfers require a SOC Fingerprint
> as the source. However, SOC cannot produce a Fingerprint because all demo
> alerts route to non-scorable actions (see the Step 3.1 limitation).
>
> Options:
> a. If SOC has a pre-existing Fingerprint from a prior session where learning
>    was enabled, the warm-start commands can succeed. Check the census first.
> b. If SOC has no Fingerprint, SOC→S2P and SOC→DataOps cannot be proven with
>    the current demo data. Claim 4 can be partially proven with
>    Trading→Purchasing only.
> c. Producing a SOC Fingerprint requires SOC learning to be enabled
>    (`soc/config.py:66`) and alerts to produce scorable actions. That requires
>    demo configuration changes beyond this runbook.

Check SOC's fingerprint count before attempting the SOC transfers:

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN 2>&1 | Select-String 'FINGERPRINTS'
```

If SOC fingerprints equal zero, skip the SOC→S2P and SOC→DataOps commands and
document Claim 4 as `PARTIAL`. If a SOC Fingerprint is available, run both
required proof edges:

```powershell
python scripts/trigger_warm_start.py --apply --source soc --target s2p --age-dsn $env:GRAPH_DSN --graph-name soc_graph
python scripts/trigger_warm_start.py --apply --source soc --target dataops --age-dsn $env:GRAPH_DSN --graph-name soc_graph
python scripts/trigger_warm_start.py --verify --age-dsn $env:GRAPH_DSN --graph-name soc_graph
```

## Step 7: Final Census

```powershell
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN
python demo.py --dump
```

The final census should show:

- all five Decision domains with decisions;
- conservation snapshots for all five domains (SOC may be `CALIBRATING`);
- domain anchors for all five domains;
- Fingerprints for at least four domains (SOC may be zero);
- Evidence receipts for at least four domains (SOC may be zero);
- checkpoints for at least two domains (S2P and DataOps pre-existing);
- `$604K` DomainContext entities;
- nonzero TransferPatterns, at minimum Trading→Purchasing; and
- if a SOC Fingerprint was available, SOC→S2P and SOC→DataOps transfers.

## Step 8: Run Claim Proof (P6.6)

The proof runner uses `GraphConfig.load()` and refuses an AGE connection unless
the supplied DSN matches the five configured domains. Execute it only with
AGE integration explicitly enabled:

```powershell
$env:AGE_INTEGRATION = "1"
New-Item -ItemType Directory -Force -Path out | Out-Null
python scripts/phase6_claim_proof.py --execute --age-dsn $env:GRAPH_DSN --graph-name soc_graph --report out/phase6_claims.json
```

Expected results depend on SOC Fingerprint availability:

- If SOC has a Fingerprint, all 8 claims should pass.
- If SOC has no Fingerprint, Claims 1–3 and 5–8 should pass; Claim 4 is
  `PARTIAL` (Trading→Purchasing proven, SOC→S2P and SOC→DataOps
  `NOT_PROVEN`).
- Claim 3 requires the `$604K` seed from Step 5.
- Claim 5 reports per-copilot learned-value totals.

## Step 9: Demo Status

```powershell
python demo.py --status | Tee-Object -FilePath out/demo_status.txt
```

Expected lines include:

```text
Shared judgment graph  soc_graph  domains: soc,s2p,trading,purchasing,dataops
Graph proof             LIVE ✓  decisions=<n> domains=<n> transfer_edges=<n>
```

## Step 9.5: Platform Diagnostics

Run the full diagnostics check:

```powershell
python demo.py --diagnose
```

Expected: all five copilots show infrastructure `ok`. S2P, Trading,
Purchasing, and DataOps show conservation `GREEN`. SOC shows conservation
`RED`/`CALIBRATING`, which is expected for the non-scorable demo alert path.
J6 readiness should be `ready` for the four GREEN copilots.

Also run a final dump for the evidence package:

```powershell
python demo.py --dump
```

This final dump is the Phase 6 completion evidence.

## Step 10: Stop and Record

```powershell
Copy-Item out/phase6_claims.json out/phase6_claims_final.json
python scripts/graph_census_v2.py --dsn $env:GRAPH_DSN | Tee-Object -FilePath out/graph_census_final.txt
python demo.py --dump
python demo.py --stop
```

Keep the final `--dump` JSON together with
`out/phase6_claims_final.json`, `out/graph_census_final.txt`, and
`out/demo_status.txt` in the Phase 6 evidence package. If the backends must
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
- **SOC conservation `CALIBRATING` with alpha=0:** this is expected. SOC's
  composite gate routes all demo alerts to `refer_to_analyst`; the
  conservation snapshot records alpha=0 and `CALIBRATING`. This is not an
  error: SOC has not processed scorable outcomes through the shared learning
  path.
- **Conservation always `RED` for a copilot with many decisions:** check
  alpha, which is category coverage. If alpha is 0, the copilot has verified
  decisions but `count_categories_with_n` is returning 0. This was fixed July
  30 by using the verified Decision predicate rather than only a
  `HAS_OUTCOME` predicate.
- **Diagnostics endpoint timed out (S2P):** S2P has approximately 25K
  decisions. The diagnostics timeout is now 30 seconds. If it still times
  out, check the AGE connection pool and query performance.
- **`demo.py --dump` shows `VERDICT: NOT READY`:** inspect the three issue
  categories: `blocking` (real issues), `expected_limitations` (SOC's
  non-scorable gaps), and `pending_operations` (Phase 6 steps not yet run).
  Only `blocking` items prevent `READY`.
- **Outbox has pending items:** these may be historical failed writes from
  prior sessions. Items exceeding `max_retries=10` are marked `abandoned` and
  excluded from pending. If manual cleanup is required, delete rows from
  `~/.ci-platform/<domain>/outbox.db` only after preserving the database as an
  audit copy.

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
- `demo.py --dump`: complete platform-state JSON snapshot containing all five
  copilots' diagnostics, census, and integrity results.
- `demo.py --diagnose`: console diagnostics with READY/NOT READY status.
- `copilot_sdk/diagnostics/platform_dump.py`: platform dump module with census
  integration and verdict categorization.
