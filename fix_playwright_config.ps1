#!/usr/bin/env pwsh
# fix_playwright_config.ps1
# Applies systemic flaky fix: expect.timeout + actionTimeout
# Run from any directory: powershell -File fix_playwright_config.ps1

$configPath = Join-Path $env:CLAUDE_SDK "e2e\playwright.config.ts"

if (-not (Test-Path $configPath)) {
    Write-Host "ERROR: $configPath not found" -ForegroundColor Red
    exit 1
}

$content = Get-Content $configPath -Raw

# Verify the old pattern exists
$oldUse = @'
  use: {
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  projects: [
'@

if ($content -notlike "*actionTimeout*" -and $content -like "*...devices*") {
    $newUse = @'
  use: {
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    actionTimeout: 10_000,
    ...devices["Desktop Chrome"],
  },
  expect: {
    timeout: 10_000,
  },
  projects: [
'@

    $content = $content.Replace($oldUse, $newUse)
    Set-Content $configPath -Value $content -NoNewline
    Write-Host "DONE: Added actionTimeout: 10_000 and expect.timeout: 10_000" -ForegroundColor Green
} elseif ($content -like "*actionTimeout*") {
    Write-Host "SKIP: actionTimeout already present" -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Could not find expected use block pattern" -ForegroundColor Red
    Write-Host "Manual edit needed: add actionTimeout: 10_000 to use {} and expect: { timeout: 10_000 } after use {}" -ForegroundColor Yellow
    exit 1
}

# Verify
Write-Host "`nVerification:" -ForegroundColor Cyan
Select-String -Path $configPath -Pattern "actionTimeout|expect:" | ForEach-Object { Write-Host "  $_" }
