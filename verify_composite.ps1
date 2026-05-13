# ============================================================
# COMPOSITE VERIFICATION — AE-SDK + GRAPH-TPC + S2P-CT+PVG+SUP
# Run AFTER all 3 Codex prompts have landed and been committed.
# Date: May 13, 2026
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " COMPOSITE VERIFICATION — 3 Codex Shipments" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()

# ----------------------------------------------------------
# 1. SDK ROOT (expect 327)
# ----------------------------------------------------------
Write-Host "--- SDK ROOT ---" -ForegroundColor Yellow
cd "$env:CLAUDE_SDK"
$sdk_result = python -m pytest tests\ -q --timeout=120 2>&1
$sdk_last = ($sdk_result | Select-Object -Last 5) -join " "
Write-Host $sdk_last
if ($sdk_last -notmatch "327 passed") {
    $errors += "SDK ROOT: expected 327 passed, got: $sdk_last"
}

# ----------------------------------------------------------
# 2. SDK EVOLUTION MODULE (expect 44 — includes generation failure + gate fixes)
# ----------------------------------------------------------
Write-Host "`n--- SDK EVOLUTION MODULE ---" -ForegroundColor Yellow
$evo_result = python -m pytest tests\evolution\ -v --timeout=120 2>&1
$evo_last = ($evo_result | Select-Object -Last 5) -join " "
Write-Host $evo_last
if ($evo_last -notmatch "44 passed") {
    $errors += "EVOLUTION: expected 44 passed, got: $evo_last"
}

# ----------------------------------------------------------
# 3. SDK GRAPH STORE EVOLUTION (expect 8)
# ----------------------------------------------------------
Write-Host "`n--- GRAPH STORE EVOLUTION ---" -ForegroundColor Yellow
$gse_result = python -m pytest tests\graph\test_graph_store_evolution.py -v --timeout=120 2>&1
$gse_last = ($gse_result | Select-Object -Last 5) -join " "
Write-Host $gse_last

# ----------------------------------------------------------
# 4. SDK GRAPH CONTRACT (expect ~22)
# ----------------------------------------------------------
Write-Host "`n--- GRAPH CONTRACT ---" -ForegroundColor Yellow
$gc_result = python -m pytest tests\graph\test_contract.py tests\graph\test_contract_cross.py -v --timeout=120 2>&1
$gc_last = ($gc_result | Select-Object -Last 5) -join " "
Write-Host $gc_last

# ----------------------------------------------------------
# 5. SDK EVOLUTION ROUTER (expect 10)
# ----------------------------------------------------------
Write-Host "`n--- EVOLUTION ROUTER ---" -ForegroundColor Yellow
$er_result = python -m pytest tests\backend\test_evolution_router.py -v --timeout=120 2>&1
$er_last = ($er_result | Select-Object -Last 5) -join " "
Write-Host $er_last

# ----------------------------------------------------------
# 6. TRADING BE (expect 33)
# ----------------------------------------------------------
Write-Host "`n--- TRADING BACKEND ---" -ForegroundColor Yellow
$trd_result = python -m pytest apps\trading\backend\tests\ -q --timeout=120 2>&1
$trd_last = ($trd_result | Select-Object -Last 5) -join " "
Write-Host $trd_last
if ($trd_last -notmatch "33 passed") {
    $errors += "TRADING: expected 33 passed, got: $trd_last"
}

# ----------------------------------------------------------
# 7. PURCHASING BE (expect 40)
# ----------------------------------------------------------
Write-Host "`n--- PURCHASING BACKEND ---" -ForegroundColor Yellow
$pur_result = python -m pytest apps\purchasing\backend\tests\ -q --timeout=120 2>&1
$pur_last = ($pur_result | Select-Object -Last 5) -join " "
Write-Host $pur_last
if ($pur_last -notmatch "40 passed") {
    $errors += "PURCHASING: expected 40 passed, got: $pur_last"
}

# ----------------------------------------------------------
# 8. DATAOPS BE (expect 129)
# ----------------------------------------------------------
Write-Host "`n--- DATAOPS BACKEND ---" -ForegroundColor Yellow
$dop_result = python -m pytest apps\dataops\backend\tests\ -q --timeout=120 2>&1
$dop_last = ($dop_result | Select-Object -Last 5) -join " "
Write-Host $dop_last
if ($dop_last -notmatch "129 passed") {
    $errors += "DATAOPS: expected 129 passed, got: $dop_last"
}

# ----------------------------------------------------------
# 9. S2P BE (expect 325)
# ----------------------------------------------------------
Write-Host "`n--- S2P BACKEND ---" -ForegroundColor Yellow
cd "$env:CLAUDE_S2P\backend"
$s2p_result = python -m pytest tests\ -q --timeout=120 2>&1
$s2p_last = ($s2p_result | Select-Object -Last 5) -join " "
Write-Host $s2p_last
if ($s2p_last -notmatch "325 passed") {
    $errors += "S2P: expected 325 passed, got: $s2p_last"
}

# ----------------------------------------------------------
# 10. FRONTEND TYPECHECKS (all 4 copilots)
# ----------------------------------------------------------
Write-Host "`n--- FRONTEND TYPECHECKS ---" -ForegroundColor Yellow
cd "$env:CLAUDE_SDK"

$fe_apps = @("s2p", "trading", "purchasing", "dataops")
foreach ($app in $fe_apps) {
    Write-Host "  $app..." -NoNewline
    cd "apps\$app\frontend"
    $tc = npx tsc --noEmit 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAIL" -ForegroundColor Red
        $errors += "FRONTEND $app typecheck failed"
    }
    cd "$env:CLAUDE_SDK"
}

# ----------------------------------------------------------
# 11. FRONTEND BUILDS (S2P specifically — has new components)
# ----------------------------------------------------------
Write-Host "`n--- S2P FRONTEND BUILD ---" -ForegroundColor Yellow
cd "apps\s2p\frontend"
$build = npm run build 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  S2P build OK" -ForegroundColor Green
} else {
    Write-Host "  S2P build FAIL" -ForegroundColor Red
    $errors += "S2P frontend build failed"
}
cd "$env:CLAUDE_SDK"

# ----------------------------------------------------------
# 12. E2E TYPECHECK (covers all copilot specs including new S2P)
# ----------------------------------------------------------
Write-Host "`n--- E2E TYPECHECK ---" -ForegroundColor Yellow
cd e2e
$e2e_tc = npx tsc --noEmit 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  E2E typecheck OK" -ForegroundColor Green
} else {
    Write-Host "  E2E typecheck FAIL" -ForegroundColor Red
    $errors += "E2E typecheck failed"
}
cd "$env:CLAUDE_SDK"

# ----------------------------------------------------------
# 13. ARCHITECTURAL INVARIANTS
# ----------------------------------------------------------
Write-Host "`n--- ARCHITECTURAL INVARIANTS ---" -ForegroundColor Yellow

# 13a. No SOC imports in SDK evolution module
Write-Host "  No SOC imports in evolution..." -NoNewline
$soc_evo = Select-String -Path copilot_sdk\evolution\*.py -Pattern "from.*soc|from.*gen_ai_roi|from app\." -ErrorAction SilentlyContinue
if ($soc_evo) {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "SOC imports found in SDK evolution: $($soc_evo.Line)"
} else {
    Write-Host " OK" -ForegroundColor Green
}

# 13b. No domain vocabulary in evolution module
Write-Host "  No domain vocabulary in evolution..." -NoNewline
$vocab_evo = Select-String -Path copilot_sdk\evolution\*.py -Pattern "credential_access|lateral_movement|invoice|supplier|ticker|portfolio" -ErrorAction SilentlyContinue
if ($vocab_evo) {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "Domain vocabulary in evolution: $($vocab_evo.Line)"
} else {
    Write-Host " OK" -ForegroundColor Green
}

# 13c. No SOC imports in S2P new routers
Write-Host "  No SOC imports in S2P routers..." -NoNewline
cd "$env:CLAUDE_S2P\backend"
$soc_s2p = Select-String -Path app\routers\s2p_control_tower.py,app\routers\s2p_pvg.py,app\routers\s2p_suppliers.py -Pattern "from app\.domains\.soc|credential_access|lateral_movement" -ErrorAction SilentlyContinue
if ($soc_s2p) {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "SOC imports in S2P routers: $($soc_s2p.Line)"
} else {
    Write-Host " OK" -ForegroundColor Green
}
cd "$env:CLAUDE_SDK"

# 13d. No SOC vocabulary in graph contracts
Write-Host "  No SOC vocabulary in graph contracts..." -NoNewline
$soc_gc = Select-String -Path apps\*\backend\app\graph_contract.py -Pattern "credential_access|lateral_movement|threat_intel" -ErrorAction SilentlyContinue
if ($soc_gc) {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "SOC vocabulary in graph contracts: $($soc_gc.Line)"
} else {
    Write-Host " OK" -ForegroundColor Green
}

# 13e. GraphStore Protocol has save_evolution_event
Write-Host "  GraphStore.save_evolution_event in Protocol..." -NoNewline
$gs_evo = python -c "from copilot_sdk.graph.protocol import GraphStore; import inspect; assert 'save_evolution_event' in [m[0] for m in inspect.getmembers(GraphStore)]; print('OK')" 2>&1
if ($gs_evo -match "OK") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "save_evolution_event not in GraphStore Protocol"
}

# 13f. SDK evolution module imports cleanly
Write-Host "  SDK evolution imports..." -NoNewline
$evo_import = python -c "
from copilot_sdk.evolution import AgentEvolver, EvolutionRule, DefaultPromotionGate
from copilot_sdk.evolution import InMemoryEvolutionLedger, DefaultShadowRunner
from copilot_sdk.evolution.protocol import EVOLUTION_EVENT_TYPES, EvolutionEvent
from copilot_sdk.graph.contract import GraphContract, NodeType, EdgeType
print('OK')
" 2>&1
if ($evo_import -match "OK") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAIL" -ForegroundColor Red
    $errors += "SDK evolution import failed: $evo_import"
}

# 13g. Graph contracts validate
Write-Host "  Graph contracts validate..." -NoNewline
$gc_valid = python -c "
import sys, os
base = os.getcwd()
for app in ['trading','purchasing','dataops']:
    sys.path.insert(0, os.path.join(base, 'apps', app, 'backend'))
# Use importlib to avoid app.* collision
import importlib.util
names = set()
for app in ['trading','purchasing','dataops']:
    spec = importlib.util.spec_from_file_location(
        f'{app}_gc',
        os.path.join(base, 'apps', app, 'backend', 'app', 'graph_contract.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Find the contract (uppercase constant)
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if hasattr(obj, 'validate') and hasattr(obj, 'graph_name'):
            errors = obj.validate()
            assert not errors, f'{obj.graph_name}: {errors}'
            assert obj.graph_name not in names, f'duplicate: {obj.graph_name}'
            names.add(obj.graph_name)
            print(f'  {obj.graph_name}: {obj.node_count}n/{obj.edge_count}e OK')
" 2>&1
Write-Host $gc_valid

# 13h. S2P new endpoints all respond (requires live server)
Write-Host "  S2P endpoints (requires live server)..." -NoNewline
$s2p_endpoints = python -c "
import urllib.request, json
base = 'http://localhost:8002'
endpoints = [
    '/api/s2p/control-tower/intents',
    '/api/s2p/control-tower/queue',
    '/api/s2p/pvg/variants',
    '/api/s2p/pvg/impact',
    '/api/s2p/pvg/leakage',
    '/api/s2p/pvg/cycle-time',
    '/api/s2p/suppliers',
    '/api/s2p/suppliers/clustering',
]
ok = 0
for ep in endpoints:
    try:
        r = urllib.request.urlopen(f'{base}{ep}', timeout=3)
        ok += 1
    except: pass
if ok == len(endpoints):
    print(f'ALL {ok}/{len(endpoints)} OK')
elif ok > 0:
    print(f'PARTIAL {ok}/{len(endpoints)}')
else:
    print('OFFLINE (start S2P backend to verify)')
" 2>&1
Write-Host " $s2p_endpoints" -ForegroundColor $(if ($s2p_endpoints -match "ALL") {"Green"} elseif ($s2p_endpoints -match "OFFLINE") {"DarkYellow"} else {"Red"})

# ----------------------------------------------------------
# 14. CROSS-REPO COHERENCE CHECKS
# ----------------------------------------------------------
Write-Host "`n--- CROSS-REPO COHERENCE ---" -ForegroundColor Yellow

# 14a. DataOps evolution router returns variants (P2 fix verification)
Write-Host "  DataOps evolution variants contract..." -NoNewline
$dop_evo = python -c "
import sys, os
sys.path.insert(0, os.path.join('$($env:CLAUDE_SDK)', 'apps', 'dataops', 'backend'))
from fastapi.testclient import TestClient
from app.main import create_app
app = create_app()
client = TestClient(app)
r = client.get('/api/evolution/variants')
data = r.json()
assert 'variants' in data, f'Missing variants key: {list(data.keys())}'
assert 'domain' in data, f'Missing domain key'
assert data['domain'] == 'dataops', f'Wrong domain: {data[\"domain\"]}'
print('OK')
" 2>&1
if ($dop_evo -match "OK") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAIL: $dop_evo" -ForegroundColor Red
    $errors += "DataOps variants contract broken: $dop_evo"
}

# 14b. S2P Control Tower has 5 intents
Write-Host "  S2P Control Tower 5 intents..." -NoNewline
cd "$env:CLAUDE_S2P\backend"
$ct5 = python -c "
import sys; sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
r = client.get('/api/s2p/control-tower/intents')
assert r.status_code == 200
assert len(r.json()) == 5, f'Expected 5 intents, got {len(r.json())}'
print('OK')
" 2>&1
if ($ct5 -match "OK") {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAIL: $ct5" -ForegroundColor Red
    $errors += "S2P CT intents != 5: $ct5"
}

# 14c. S2P PVG leakage uses AND rule
Write-Host "  S2P PVG leakage AND rule..." -NoNewline
$leak = python -c "
import sys; sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
r = client.get('/api/s2p/pvg/leakage')
data = r.json()
flagged = data.get('flagged_invoices', data.get('flagged', []))
for inv in flagged:
    vr = inv.get('variance_ratio', inv.get('amount_variance_ratio', 0))
    cc = inv.get('commodity_correlation', inv.get('commodity_index_correlation', 1))
    assert vr > 0.15, f'Variance {vr} <= 0.15'
    assert cc < 0.5, f'Commodity {cc} >= 0.5'
print(f'OK ({len(flagged)} flagged)')
" 2>&1
if ($leak -match "OK") {
    Write-Host " $leak" -ForegroundColor Green
} else {
    Write-Host " FAIL: $leak" -ForegroundColor Red
    $errors += "S2P leakage AND rule violated: $leak"
}
cd "$env:CLAUDE_SDK"

# ----------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " COMPOSITE VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$expected = @{
    "SDK root" = 327
    "Trading BE" = 33
    "Purchasing BE" = 40
    "DataOps BE" = 129
    "S2P BE" = 325
}

Write-Host "`nExpected test counts:"
foreach ($k in $expected.Keys) {
    Write-Host "  $k : $($expected[$k])"
}
Write-Host "  TOTAL: $($expected.Values | Measure-Object -Sum | Select-Object -ExpandProperty Sum) (+ ci-platform 224, GAE 1237, SOC 1572+280 unchanged)"

if ($errors.Count -eq 0) {
    Write-Host "`n  ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host "`n  Ready to tag." -ForegroundColor Green
} else {
    Write-Host "`n  $($errors.Count) CHECK(S) FAILED:" -ForegroundColor Red
    foreach ($e in $errors) {
        Write-Host "    - $e" -ForegroundColor Red
    }
    Write-Host "`n  INVESTIGATE before tagging." -ForegroundColor Red
}

Write-Host "`n--- GIT TAG SEQUENCE (execute if all green) ---" -ForegroundColor DarkYellow
Write-Host @"

cd "$env:CLAUDE_SDK"
git add -A
git commit -m "AE-SDK + GRAPH-TPC + S2P frontend: evolution protocols + graph contracts + CT+PVG+SUP components

AE-SDK: GraphStore.save_evolution_event(), evolution protocols, ledger, shadow,
gate (with failed_checks), AgentEvolver orchestrator, evolution_router factory.
DataOps wired to real SDK evolution. +57 SDK tests.

GRAPH-TPC: GraphContract protocol with Decision/DECIDED_ON validation.
Trading (7n/7e), Purchasing (7n/7e), DataOps (8n/8e) contracts + deterministic
seeds. Subprocess-isolated cross-domain tests. +21 SDK + 23 app tests.

S2P frontend: ControlTowerPanel, FinancialImpactCard, LeakageDetectionPanel,
CycleTimePanel, SupplierProfileCard, SupplierHeatmap, SupplierClusteringPanel.
E2E specs created (run manually)."
git tag v0.6.0-sdk

cd "$env:CLAUDE_S2P"
git add -A
git commit -m "S2P-CT+PVG+SUP: Control Tower 5 intents + Process Variant Graph + Suppliers full

Control Tower: intent classification, priority queue, 5 typed intents.
PVG: financial impact ($680K baseline), leakage detection (AND rule), cycle-time.
Suppliers: profiles, OTIF trends, behavioral clustering, category heatmap.
True median fix (P3). +45 tests (280→325)."
git tag v0.5.8-s2p

"@
