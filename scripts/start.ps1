# scripts/start.ps1 - Service Launcher
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.

param(
    [int]$Port = 4180,
    [string]$WorkspaceDir = "",
    [switch]$NoBrowser = $false
)

$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
if (-not $repoDir) { $repoDir = (Get-Location).Path }
Set-Location $repoDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Service Launcher (Port $Port)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify build artifact
$cliDist = Join-Path $repoDir "packages\cli\dist\index.js"
if (-not (Test-Path $cliDist)) {
    Write-Host "[NOTE] Build artifact not detected. Running setup wizard first..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "setup.ps1")
}

# 2. Determine workspace directory
if (-not $WorkspaceDir) {
    $WorkspaceDir = Join-Path $repoDir "agh-workspace"
}
if (-not (Test-Path $WorkspaceDir)) {
    New-Item -ItemType Directory -Path $WorkspaceDir -Force | Out-Null
}

# 3. Determine isolated user data directory
$appHome = Join-Path $env:USERPROFILE ".agh-physics"
if (-not (Test-Path $appHome)) {
    New-Item -ItemType Directory -Path $appHome -Force | Out-Null
}
$env:AGH_HOME = $appHome

# 4. Sync skills and assets to workspace
Write-Host "[1/3] Syncing workspace skills and assets..." -ForegroundColor Yellow
$targetSkillsDir = Join-Path $WorkspaceDir ".agh\skills"
if (-not (Test-Path $targetSkillsDir)) {
    New-Item -ItemType Directory -Path $targetSkillsDir -Force | Out-Null
}
$sourceSkills = Join-Path $repoDir ".agh\skills"
if (Test-Path $sourceSkills) {
    Copy-Item -Path "$sourceSkills\*" -Destination $targetSkillsDir -Recurse -Force
}

$targetAgentDir = Join-Path $WorkspaceDir "physics-agent"
if (-not (Test-Path $targetAgentDir)) {
    New-Item -ItemType Directory -Path $targetAgentDir -Force | Out-Null
}
$sourceAgent = Join-Path $repoDir "physics-agent"
if (Test-Path $sourceAgent) {
    Copy-Item -Path "$sourceAgent\hooks" -Destination $targetAgentDir -Recurse -Force
    Copy-Item -Path "$sourceAgent\knowledge" -Destination $targetAgentDir -Recurse -Force
    Copy-Item -Path "$sourceAgent\plugins" -Destination $targetAgentDir -Recurse -Force
}
Write-Host "  -> Core assets synced successfully." -ForegroundColor Green

# 5. Check and manage port
Write-Host "[2/3] Checking port $Port and managing daemon..." -ForegroundColor Yellow
try {
    node packages/cli/dist/index.js daemon stop 2>$null | Out-Null
} catch {}

$occupied = $false
try {
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conns) { $occupied = $true }
} catch {
    $netstat = netstat -ano | Select-String ":$Port "
    if ($netstat) { $occupied = $true }
}

if ($occupied) {
    Write-Host "  -> Port $Port currently in use. Stopping old instance..." -ForegroundColor Yellow
    node packages/cli/dist/index.js daemon stop 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

# 6. Start daemon service
Write-Host "[3/3] Starting AI Physics Research Agent service..." -ForegroundColor Yellow
$startResult = node packages/cli/dist/index.js daemon start --port $Port 2>&1
Write-Host "  -> $startResult" -ForegroundColor Green

$url = "http://127.0.0.1:$Port"
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "               Service Ready                              " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Web URL         : $url" -ForegroundColor Green
Write-Host "  Workspace       : $WorkspaceDir"
Write-Host "  Data Home       : $appHome"
Write-Host "==========================================================" -ForegroundColor Cyan

# 7. Open browser
if (-not $NoBrowser) {
    Write-Host "Opening browser..." -ForegroundColor Yellow
    Start-Sleep -Milliseconds 600
    Start-Process $url
}
Write-Host "You can stop the service anytime by running: node packages/cli/dist/index.js daemon stop`n"
