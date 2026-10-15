# sync-and-build-test.ps1 - Automated synchronization, compilation and launcher for AGH port 4180
# Designed for 100% pure ASCII execution to prevent PowerShell 5.1 CP936 encoding errors.
param(
    [switch]$Rebuild = $false
)

$ErrorActionPreference = 'Stop'
$repoDir = "E:\agnes-harness"
$testDir = "E:\agh-test"
$testHome = "C:\Users\StanleyZ\.agh-test"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AGH Test Environment - Asset Sync & Launcher (Port 4180) " -ForegroundColor Cyan
Write-Host "==========================================================`n" -ForegroundColor Cyan

# Step 1: Clean test workspace runtime task directories (Strict adherence to Section 5 isolation)
Write-Host "[1/7] Cleaning previous task runtime directories..." -ForegroundColor Yellow
Remove-Item "$testDir\physics-agent\runtime\historical-artillery-ballistics" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$testDir\physics-agent\runtime\jupiter-moon-gravity-assist-*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host " -> Runtime directories sanitized (zero prior answer contamination)." -ForegroundColor Green

# Step 2: Sync latest assets (Skills, Hooks, Knowledge, Plugins) from repo to test workspace
Write-Host "`n[2/7] Syncing latest assets from repo to test workspace: $testDir..." -ForegroundColor Yellow

# 2.1 Sync Skills
if (Test-Path "$repoDir\.agh\skills") {
    if (-not (Test-Path "$testDir\.agh\skills")) {
        New-Item -ItemType Directory -Path "$testDir\.agh\skills" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\.agh\skills\*" -Destination "$testDir\.agh\skills\" -Recurse -Force
    Write-Host " -> Skills copied successfully." -ForegroundColor Green
}

# 2.2 Sync Hooks (trace_visualizer.py, make_report_figures.py, quality checks)
if (Test-Path "$repoDir\physics-agent\hooks") {
    if (-not (Test-Path "$testDir\physics-agent\hooks")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\hooks" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\hooks\*" -Destination "$testDir\physics-agent\hooks\" -Recurse -Force
    Write-Host " -> Hooks copied successfully." -ForegroundColor Green
}

# 2.3 Sync Knowledge (delivery_template.md, physics methodology)
if (Test-Path "$repoDir\physics-agent\knowledge") {
    if (-not (Test-Path "$testDir\physics-agent\knowledge")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\knowledge" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\knowledge\*" -Destination "$testDir\physics-agent\knowledge\" -Recurse -Force
    Write-Host " -> Knowledge copied successfully." -ForegroundColor Green
}

# 2.4 Sync Plugins (orchestrator router)
if (Test-Path "$repoDir\physics-agent\plugins") {
    if (-not (Test-Path "$testDir\physics-agent\plugins")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\plugins" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\plugins\*" -Destination "$testDir\physics-agent\plugins\" -Recurse -Force
    Write-Host " -> Plugins copied successfully." -ForegroundColor Green
}

# 2.5 Deploy latest verified HTML report copy for reference verification
$captureReportDir = "$testDir\physics-agent\runtime\jupiter-moon-gravity-assist-capture"
if (-not (Test-Path $captureReportDir)) {
    New-Item -ItemType Directory -Path $captureReportDir -Force | Out-Null
}
Copy-Item -Path "$repoDir\research_report_jupiter-moon-gravity-assist-capture.html" -Destination "$captureReportDir\research_report_jupiter-moon-gravity-assist-capture.html" -Force
Write-Host " -> Deployed verified capture report copy to test runtime directory." -ForegroundColor Green

# Step 3: Strip UTF-8 BOM from all SKILL.md files in test workspace
Write-Host "`n[3/7] Checking and stripping UTF-8 BOM from SKILL.md files..." -ForegroundColor Yellow
$cleanCount = 0
$files = Get-ChildItem -Path "$testDir\.agh\skills" -Recurse -Filter "SKILL.md"
foreach ($file in $files) {
    $p = $file.FullName
    $bytes = [System.IO.File]::ReadAllBytes($p)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $cleanBytes = $bytes[3..($bytes.Length - 1)]
        [System.IO.File]::WriteAllBytes($p, $cleanBytes)
        $cleanCount++
        Write-Host " [STRIPPED BOM] $p" -ForegroundColor Magenta
    } else {
        Write-Host " [OK NO BOM]   $p" -ForegroundColor DarkGray
    }
}
Write-Host " -> BOM check completed ($cleanCount files cleaned)." -ForegroundColor Green

# Step 4: Clear stale LKG skill cache snapshots to force clean rescan
Write-Host "`n[4/7] Clearing stale LKG skill cache snapshots..." -ForegroundColor Yellow
if (Test-Path $testHome) {
    Get-ChildItem -Path $testHome -Recurse -Filter "*workspace-agnes*.json" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $testHome -Recurse -Filter "*skill*.lkg" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host " -> Stale skill cache removed." -ForegroundColor Green
}

# Step 5: STOP OLD TEST DAEMON ONLY (Port 4180 / $testHome - NEVER touch Port 4177!)
Write-Host "`n[5/7] Stopping old test daemon (port 4180 only)..." -ForegroundColor Yellow
try {
    $env:AGH_HOME = $testHome
    node "$repoDir\packages\cli\dist\local\agnes.mjs" daemon stop 2>$null
} catch {}
# Clean any leftover build-lock directories from prior interrupted builds
Remove-Item -Path "$repoDir\packages\cli\dist\local.build-lock" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host " -> Test daemon stopped (primary port 4177 preserved untouched)." -ForegroundColor Green

# Step 6: Check local CLI bundle readiness (Rebuild only if requested or bundle is missing)
Write-Host "`n[6/7] Checking local CLI bundle readiness..." -ForegroundColor Yellow
$bundlePath = "$repoDir\packages\cli\dist\local\agnes.mjs"
if ($Rebuild -or (-not (Test-Path $bundlePath))) {
    Write-Host " -> Compiling local bundle via pnpm build:local..." -ForegroundColor Yellow
    pnpm --filter @agnes/cli run build:local
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE"
    }
    Write-Host " -> Bundle compiled successfully." -ForegroundColor Green
} else {
    Write-Host " -> Bundle ready (rebuild skipped; pass -Rebuild to force recompile)." -ForegroundColor Green
}

# Step 7: Launch isolated Web service on port 4180
Write-Host "`n[7/7] Launching AGH Web Service on port 4180..." -ForegroundColor Yellow
$env:AGH_HOME = $testHome
$env:AGNES_PROFILE = "local-dev"
$env:AGNES_WEB_ORIGIN = "http://127.0.0.1:4180"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Service Ready! Open in your browser:" -ForegroundColor Green
Write-Host " -> http://127.0.0.1:4180" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host " In the web UI, select workspace: E:\agh-test" -ForegroundColor Cyan
Write-Host "==========================================================`n" -ForegroundColor Green

node "$repoDir\packages\cli\dist\local\agnes.mjs" serve --port 4180
