# start-test-runner.ps1 - Automated setup and launcher for AGH port 4180
param(
    [switch]$Rebuild = $false
)
$ErrorActionPreference = 'Stop'
$repoDir = "E:\agnes-harness"
$testDir = "E:\agh-test"
$testHome = "C:\Users\StanleyZ\.agh-test"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AGH Physics-Agent - Test Runner on Port 4180          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Sync all skills, hooks, knowledge and plugins from repo to test workspace
Write-Host "`n[1/6] Syncing skills, hooks, knowledge and plugins to test workspace: $testDir..." -ForegroundColor Yellow

# 1.1 Sync Skills
if (Test-Path "$repoDir\.agh\skills") {
    if (-not (Test-Path "$testDir\.agh\skills")) {
        New-Item -ItemType Directory -Path "$testDir\.agh\skills" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\.agh\skills\*" -Destination "$testDir\.agh\skills\" -Recurse -Force
    Write-Host " -> Skills copied successfully." -ForegroundColor Green
}

# 1.2 Sync Hooks (renderers, verifiers, quality check)
if (Test-Path "$repoDir\physics-agent\hooks") {
    if (-not (Test-Path "$testDir\physics-agent\hooks")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\hooks" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\hooks\*" -Destination "$testDir\physics-agent\hooks\" -Recurse -Force
    Write-Host " -> Hooks copied successfully." -ForegroundColor Green
}

# 1.3 Sync Knowledge (physics methodology, delivery template)
if (Test-Path "$repoDir\physics-agent\knowledge") {
    if (-not (Test-Path "$testDir\physics-agent\knowledge")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\knowledge" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\knowledge\*" -Destination "$testDir\physics-agent\knowledge\" -Recurse -Force
    Write-Host " -> Knowledge copied successfully." -ForegroundColor Green
}

# 1.4 Sync Plugins (orchestrator router)
if (Test-Path "$repoDir\physics-agent\plugins") {
    if (-not (Test-Path "$testDir\physics-agent\plugins")) {
        New-Item -ItemType Directory -Path "$testDir\physics-agent\plugins" -Force | Out-Null
    }
    Copy-Item -Path "$repoDir\physics-agent\plugins\*" -Destination "$testDir\physics-agent\plugins\" -Recurse -Force
    Write-Host " -> Plugins copied successfully." -ForegroundColor Green
}

# 1.5 Isolate runtime: remove any pre-computed problem answers to ensure 100% autonomous testing
Remove-Item -Path "$testDir\physics-agent\runtime\historical-artillery-ballistics" -Recurse -Force -ErrorAction SilentlyContinue

# Step 2: Strip UTF-8 BOM from all SKILL.md files
Write-Host "`n[2/6] Checking and stripping UTF-8 BOM from SKILL.md files..." -ForegroundColor Yellow
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

# Step 3: Clear stale LKG cache snapshots to force clean rescan
Write-Host "`n[3/6] Clearing stale LKG skill cache snapshots..." -ForegroundColor Yellow
if (Test-Path $testHome) {
    Get-ChildItem -Path $testHome -Recurse -Filter "*workspace-agnes*.json" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $testHome -Recurse -Filter "*skill*.lkg" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host " -> Stale cache removed." -ForegroundColor Green
}

# Step 4: Stop any old test daemon first (Port 4180 / $testHome ONLY - NEVER touch Port 4177!)
Write-Host "`n[4/6] Stopping old test daemon (port 4180 only)..." -ForegroundColor Yellow
try {
    $env:AGH_HOME = $testHome
    node "$repoDir\packages\cli\dist\local\agnes.mjs" daemon stop 2>$null
} catch {}
# Clean any leftover build-lock directories from prior interrupted builds
Remove-Item -Path "$repoDir\packages\cli\dist\local.build-lock" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host " -> Test daemon stopped (primary port 4177 preserved untouched)." -ForegroundColor Green

# Step 5: Check local CLI bundle readiness (Rebuild only if requested or missing)
Write-Host "`n[5/6] Checking local CLI bundle readiness..." -ForegroundColor Yellow
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

# Step 6: Start isolated Web service on port 4180
Write-Host "`n[6/6] Launching AGH Web Service on port 4180..." -ForegroundColor Yellow
$env:AGH_HOME = $testHome
$env:AGNES_PROFILE = "local-dev"
$env:AGNES_WEB_ORIGIN = "http://127.0.0.1:4180"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Service Ready! Open in your browser:" -ForegroundColor Green
Write-Host " -> http://127.0.0.1:4180" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host " In the web UI, select workspace: E:\agh-test" -ForegroundColor Cyan
Write-Host "==========================================================`n" -ForegroundColor Green

node "$repoDir\packages\cli\dist\local\agnes.mjs" serve --port 4180
