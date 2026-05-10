<#
.SYNOPSIS
Starts, stops, or checks the Copilot demo platform.

.DESCRIPTION
Launches the Trading, Purchasing, and DataOps copilot backends and frontends
from this repository. By default all three copilots are selected. Use the
domain switches to select a subset. The script can also stop known demo ports,
show status, build frontends, run optional DataOps graph seeding, and preseed
the running backend APIs.

.PARAMETER stop
Stops processes listening on the known demo ports only.

.PARAMETER status
Shows backend/frontend port status and backend /health details when reachable.

.PARAMETER trading
Selects the Trading copilot only, or includes Trading in a selected subset.

.PARAMETER purchasing
Selects the Purchasing copilot only, or includes Purchasing in a selected subset.

.PARAMETER dataops
Selects the DataOps copilot only, or includes DataOps in a selected subset.

.PARAMETER graph
Attempts to enable DataOps AGE graph mode and seed the graph before backend start.

.PARAMETER preseed
Runs scripts/preseed_all_copilots.py after selected backends become healthy.

.PARAMETER noBrowser
Does not open frontend browser tabs after startup.

.PARAMETER build
Runs npm run build for selected frontends before starting servers.

.EXAMPLE
.\demo.ps1
Starts all three copilots and opens browser tabs.

.EXAMPLE
.\demo.ps1 -dataops -graph -preseed
Starts DataOps with graph mode and runs DataOps preseed after health check.

.EXAMPLE
.\demo.ps1 -status
Shows status for all copilots.

.EXAMPLE
.\demo.ps1 -stop
Stops processes bound to the known demo ports.
#>

param(
    [switch]$stop,
    [switch]$status,
    [switch]$trading,
    [switch]$purchasing,
    [switch]$dataops,
    [switch]$graph,
    [switch]$preseed,
    [switch]$noBrowser,
    [switch]$build
)

$ErrorActionPreference = "Stop"

$SDK_ROOT = $PSScriptRoot
$CI_PLATFORM = Join-Path (Split-Path $SDK_ROOT) "ci-platform"

$Copilots = @(
    [PSCustomObject]@{
        Name = "trading"
        Display = "Trading"
        BackendPort = 8010
        FrontendPort = 5174
        BackendPath = Join-Path $SDK_ROOT "apps\trading\backend"
        FrontendPath = Join-Path $SDK_ROOT "apps\trading\frontend"
        Color = "Red"
        PreseedFlag = "--trading-only"
    },
    [PSCustomObject]@{
        Name = "purchasing"
        Display = "Purchasing"
        BackendPort = 8020
        FrontendPort = 5175
        BackendPath = Join-Path $SDK_ROOT "apps\purchasing\backend"
        FrontendPath = Join-Path $SDK_ROOT "apps\purchasing\frontend"
        Color = "Green"
        PreseedFlag = "--purchasing-only"
    },
    [PSCustomObject]@{
        Name = "dataops"
        Display = "DataOps"
        BackendPort = 8030
        FrontendPort = 5176
        BackendPath = Join-Path $SDK_ROOT "apps\dataops\backend"
        FrontendPath = Join-Path $SDK_ROOT "apps\dataops\frontend"
        Color = "Magenta"
        PreseedFlag = "--dataops-only"
    }
)

function Write-Info($Message) {
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Warn($Message) {
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Test-Port($Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        return ($null -ne $connections)
    } catch {
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $async = $client.BeginConnect("127.0.0.1", [int]$Port, $null, $null)
            $connected = $async.AsyncWaitHandle.WaitOne(500, $false)
            if ($connected) {
                $client.EndConnect($async)
            }
            $client.Close()
            return [bool]$connected
        } catch {
            return $false
        }
    }
}

function Get-PortProcessIds($Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        return @($connections | Select-Object -ExpandProperty OwningProcess -Unique)
    } catch {
        $ids = @()
        $lines = netstat -ano -p tcp | Select-String "LISTENING"
        foreach ($line in $lines) {
            $text = $line.ToString().Trim()
            if ($text -match "[:.]$Port\s+.*\s+LISTENING\s+(\d+)$") {
                $ids += [int]$Matches[1]
            }
        }
        return @($ids | Select-Object -Unique)
    }
}

function Stop-PortProcess($Port, $Label) {
    $processIds = Get-PortProcessIds $Port
    if ($processIds.Count -eq 0) {
        Write-Host "$Label port $Port is not in use."
        return
    }

    foreach ($processId in $processIds) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            Write-Host "Stopping $Label on port $Port (PID $processId, $($process.ProcessName))..."
            Stop-Process -Id $processId -Force -ErrorAction Stop
        } catch {
            Write-Warn "Could not stop $Label on port $Port (PID $processId): $($_.Exception.Message)"
        }
    }
}

function Stop-AllCopilots {
    Write-Info "Stopping Copilot demo ports..."
    foreach ($copilot in $Copilots) {
        Stop-PortProcess $copilot.BackendPort "$($copilot.Display) backend"
        Stop-PortProcess $copilot.FrontendPort "$($copilot.Display) frontend"
    }
    Write-Info "Stop command complete."
}

function Test-PathOrWarn($Path, $Label) {
    if (Test-Path $Path) {
        return $true
    }
    Write-Warn "$Label not found: $Path"
    return $false
}

function Get-Health($Port) {
    try {
        return Invoke-RestMethod -Uri "http://localhost:$Port/health" -TimeoutSec 2 -ErrorAction Stop
    } catch {
        return $null
    }
}

function Show-Status {
    $selected = Get-SelectedCopilots
    Write-Info "Copilot platform status"
    foreach ($copilot in $selected) {
        $backendUp = Test-Port $copilot.BackendPort
        $frontendUp = Test-Port $copilot.FrontendPort
        $backendText = if ($backendUp) { "UP" } else { "DOWN" }
        $frontendText = if ($frontendUp) { "UP" } else { "DOWN" }
        Write-Host "$($copilot.Display): backend $($copilot.BackendPort) $backendText | frontend $($copilot.FrontendPort) $frontendText" -ForegroundColor $copilot.Color

        if ($backendUp) {
            $health = Get-Health $copilot.BackendPort
            if ($health) {
                $domain = if ($health.domain) { $health.domain } else { "unknown" }
                $statusText = if ($health.status) { $health.status } else { "unknown" }
                $graphSource = if ($health.graph_source) { " graph=$($health.graph_source)" } elseif ($health.graphSource) { " graph=$($health.graphSource)" } else { "" }
                Write-Host "  health: domain=$domain status=$statusText$graphSource"
            } else {
                Write-Warn "$($copilot.Display) backend port is open, but /health did not respond."
            }
        }
    }
}

function Start-Backend($Copilot) {
    if (-not (Test-PathOrWarn $Copilot.BackendPath "$($Copilot.Display) backend path")) {
        throw "$($Copilot.Display) backend path missing."
    }
    $mainPath = Join-Path $Copilot.BackendPath "app\main.py"
    if (-not (Test-PathOrWarn $mainPath "$($Copilot.Display) backend app.main")) {
        throw "$($Copilot.Display) backend main.py missing."
    }
    if (Test-Port $Copilot.BackendPort) {
        Write-Host "$($Copilot.Display) backend already running on port $($Copilot.BackendPort)."
        return
    }

    Write-Host "Starting $($Copilot.Display) backend on port $($Copilot.BackendPort)..." -ForegroundColor $Copilot.Color
    Start-Process -FilePath "python" `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$($Copilot.BackendPort)") `
        -WorkingDirectory $Copilot.BackendPath `
       
}

function Wait-ForHealth($Copilot) {
    Write-Host "Waiting for $($Copilot.Display) backend health..."
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        $health = Get-Health $Copilot.BackendPort
        if ($health -and $health.status -eq "ok") {
            Write-Host "$($Copilot.Display) backend healthy." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Warn "$($Copilot.Display) backend did not become healthy on port $($Copilot.BackendPort)."
    return $false
}

function Start-Frontend($Copilot) {
    if (-not (Test-PathOrWarn $Copilot.FrontendPath "$($Copilot.Display) frontend path")) {
        throw "$($Copilot.Display) frontend path missing."
    }
    $packagePath = Join-Path $Copilot.FrontendPath "package.json"
    if (-not (Test-PathOrWarn $packagePath "$($Copilot.Display) frontend package.json")) {
        throw "$($Copilot.Display) frontend package.json missing."
    }
    $envPath = Join-Path $Copilot.FrontendPath ".env"
    if (-not (Test-Path $envPath)) {
        Write-Warn "$($Copilot.Display) frontend .env missing; frontend defaults must provide API URL."
    }
    if (Test-Port $Copilot.FrontendPort) {
        Write-Host "$($Copilot.Display) frontend already running on port $($Copilot.FrontendPort)."
        return
    }

    Write-Host "Starting $($Copilot.Display) frontend on port $($Copilot.FrontendPort)..." -ForegroundColor $Copilot.Color
    Start-Process -FilePath "npx" `
        -ArgumentList @("vite", "--port", "$($Copilot.FrontendPort)", "--host", "127.0.0.1") `
        -WorkingDirectory $Copilot.FrontendPath `
       
}

function Start-GraphMode {
    if (-not $graph) {
        return
    }

    Write-Info "Preparing DataOps graph mode..."
    $graphDsn = "host=localhost port=5433 dbname=soc_graph user=postgres password=postgres"
    $env:GRAPH_DSN = $graphDsn

    try {
        $wslDistros = @(& wsl.exe -l -q 2>$null)
        if (-not ($wslDistros -match "Ubuntu-24.04")) {
            Write-Warn "WSL Ubuntu-24.04 not found. DataOps may fall back to fixtures."
        }
    } catch {
        Write-Warn "Could not check WSL: $($_.Exception.Message)"
    }

    try {
        $portProxy = netsh interface portproxy show v4tov4 | Select-String "5433"
        if (-not $portProxy) {
            Write-Warn "Portproxy for 5433 was not found. GRAPH_DSN may be unreachable."
        }
    } catch {
        Write-Warn "Could not check portproxy: $($_.Exception.Message)"
    }

    $seedScript = Join-Path $CI_PLATFORM "scripts\seed_dataops_graph.py"
    if (-not (Test-Path $seedScript)) {
        Write-Warn "Graph seed script not found: $seedScript"
        Remove-Item Env:\GRAPH_DSN -ErrorAction SilentlyContinue
        return
    }

    $pushedLocation = $false
    try {
        Push-Location $CI_PLATFORM
        $pushedLocation = $true
        python "scripts\seed_dataops_graph.py" --force
        if ($LASTEXITCODE -ne 0) {
            throw "seed_dataops_graph.py exited with code $LASTEXITCODE"
        }
        Write-Host "DataOps graph seed complete." -ForegroundColor Green
    } catch {
        Write-Warn "Graph setup failed: $($_.Exception.Message). Unsetting GRAPH_DSN for fixture fallback."
        Remove-Item Env:\GRAPH_DSN -ErrorAction SilentlyContinue
    } finally {
        if ($pushedLocation) {
            Pop-Location
        }
    }
}

function Start-PreSeed($SelectedCopilots) {
    if (-not $preseed) {
        return
    }

    $script = Join-Path $SDK_ROOT "scripts\preseed_all_copilots.py"
    if (-not (Test-PathOrWarn $script "preseed script")) {
        return
    }

    $selectedAll = ($SelectedCopilots.Count -eq $Copilots.Count)
    $args = @($script)
    if (-not $selectedAll) {
        foreach ($copilot in $SelectedCopilots) {
            $args += $copilot.PreseedFlag
        }
    }

    Write-Info "Running preseed script..."
    Push-Location $SDK_ROOT
    try {
        & python @args
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Preseed exited with code $LASTEXITCODE."
        }
    } catch {
        Write-Warn "Preseed failed: $($_.Exception.Message)"
    } finally {
        Pop-Location
    }
}

function Start-Builds($SelectedCopilots) {
    if (-not $build) {
        return
    }

    foreach ($copilot in $SelectedCopilots) {
        $packagePath = Join-Path $copilot.FrontendPath "package.json"
        if (-not (Test-PathOrWarn $packagePath "$($copilot.Display) frontend package.json")) {
            throw "$($copilot.Display) frontend package.json missing."
        }
        Write-Host "Building $($copilot.Display) frontend..." -ForegroundColor $copilot.Color
        Push-Location $copilot.FrontendPath
        try {
            npm run build
            if ($LASTEXITCODE -ne 0) {
                throw "$($copilot.Display) frontend build failed with code $LASTEXITCODE"
            }
        } finally {
            Pop-Location
        }
    }
}

function Open-Browsers($SelectedCopilots) {
    if ($noBrowser) {
        return
    }

    foreach ($copilot in $SelectedCopilots) {
        $url = "http://localhost:$($copilot.FrontendPort)"
        Write-Host "Opening $url"
        Start-Process $url
    }
}

function Get-SelectedCopilots {
    $selected = @()
    if (-not $trading -and -not $purchasing -and -not $dataops) {
        return @($Copilots)
    }
    if ($trading) {
        $selected += @($Copilots | Where-Object { $_.Name -eq "trading" })
    }
    if ($purchasing) {
        $selected += @($Copilots | Where-Object { $_.Name -eq "purchasing" })
    }
    if ($dataops) {
        $selected += @($Copilots | Where-Object { $_.Name -eq "dataops" })
    }
    return @($selected)
}

if ($stop) {
    Stop-AllCopilots
    return
}

if ($status) {
    Show-Status
    return
}

$selectedCopilots = Get-SelectedCopilots
Write-Info "Starting Copilot demo platform"
Write-Host "Selected: $($selectedCopilots.Display -join ', ')"

if ($graph) {
    Start-GraphMode
}

Start-Builds $selectedCopilots

foreach ($copilot in $selectedCopilots) {
    Start-Backend $copilot
}

$allHealthy = $true
foreach ($copilot in $selectedCopilots) {
    if (-not (Wait-ForHealth $copilot)) {
        $allHealthy = $false
    }
}

if (-not $allHealthy) {
    Write-Warn "One or more selected backends failed health checks. Frontends were not started."
    return
}

Start-PreSeed $selectedCopilots

foreach ($copilot in $selectedCopilots) {
    Start-Frontend $copilot
}

Start-Sleep -Seconds 2
Open-Browsers $selectedCopilots

Write-Info "Copilot demo platform is starting."
foreach ($copilot in $selectedCopilots) {
    Write-Host "$($copilot.Display): backend http://localhost:$($copilot.BackendPort) | frontend http://localhost:$($copilot.FrontendPort)" -ForegroundColor $copilot.Color
}
Write-Host "Status: .\demo.ps1 -status"
Write-Host "Stop:   .\demo.ps1 -stop"
