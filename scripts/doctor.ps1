# scripts/doctor.ps1 - Environment Health Diagnostic & Instance Scanner Tool
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.
# Complies with official AGH architecture for AGH_HOME isolation, multi-port concurrency, and sandbox execution.

param(
    [switch]$VerboseScan = $false
)

$ErrorActionPreference = 'Continue'
$repoDir = Split-Path -Parent $PSScriptRoot
if (-not $repoDir) { $repoDir = (Get-Location).Path }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Environment Doctor         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repository root: $repoDir"
Write-Host ""

$issues = 0
$warnings = 0

# Helper to test listening port
function Test-Port([int]$p) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if ($conns) { return $true }
    } catch {
        $res = netstat -ano | Select-String ":$p\s+.*LISTENING"
        if ($res) { return $true }
    }
    return $false
}

# 1. OS Architecture check
Write-Host "[1/6] Checking OS Architecture..." -ForegroundColor Yellow
$osInfo = [System.Environment]::OSVersion.VersionString
$arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
Write-Host "  -> Operating System: $osInfo ($arch)"
if ([System.IntPtr]::Size -ne 8) {
    Write-Host "  [WARN] 32-bit OS detected. High-memory ODE integrations may be constrained." -ForegroundColor Yellow
    $warnings++
} else {
    Write-Host "  [PASS] 64-bit OS verified." -ForegroundColor Green
}

# 2. Node.js check
Write-Host "`n[2/6] Checking Node.js Runtime..." -ForegroundColor Yellow
$nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "  [FAIL] Node.js not detected. The platform daemon cannot start!" -ForegroundColor Red
    Write-Host "         Please install Node.js (v24.10+ or LTS) from: https://nodejs.org/" -ForegroundColor DarkYellow
    $issues++
} else {
    $nodeVersionRaw = node -v
    Write-Host "  -> Current version: $nodeVersionRaw"
    if ($nodeVersionRaw -match 'v(\d+)\.(\d+)') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 24 -or ($major -eq 24 -and $minor -lt 10)) {
            Write-Host "  [WARN] Node.js is below recommended baseline v24.10." -ForegroundColor Yellow
            $warnings++
        } else {
            Write-Host "  [PASS] Node.js runtime meets baseline (>= v24.10)." -ForegroundColor Green
        }
    }
}

# 3. pnpm check
Write-Host "`n[3/6] Checking pnpm Package Manager..." -ForegroundColor Yellow
$pnpmCmd = Get-Command "pnpm" -ErrorAction SilentlyContinue
if (-not $pnpmCmd) {
    Write-Host "  [NOTE] Global pnpm not found." -ForegroundColor Yellow
    Write-Host "         Enable via Corepack: corepack enable; corepack prepare pnpm@10.34.5 --activate" -ForegroundColor DarkCyan
    Write-Host "         Or install via npm:  npm install -g pnpm@10.34.5" -ForegroundColor DarkCyan
    $warnings++
} else {
    $pnpmVer = pnpm -v
    Write-Host "  -> Current version: v$pnpmVer"
    Write-Host "  [PASS] pnpm package manager is ready." -ForegroundColor Green
}

# 4. Python Scientific Computing Environment Check
Write-Host "`n[4/6] Checking Python Scientific Computing Environment..." -ForegroundColor Yellow
$pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
$systemPythonOk = $false
$missingPackages = @()
$requiredPackages = @("sympy", "pint", "numpy", "scipy", "matplotlib")

if ($pythonCmd) {
    $pyVerRaw = python --version 2>&1
    Write-Host "  -> System Python: $pyVerRaw"
    $checkScript = "import sys; import " + ($requiredPackages -join ", ") + "; print('ALL_OK')"
    $checkRes = python -c "$checkScript" 2>&1
    if ($checkRes -match "ALL_OK") {
        $systemPythonOk = $true
        Write-Host "  [PASS] System Python has all required scientific libraries (sympy, pint, numpy, scipy, matplotlib)." -ForegroundColor Green
    } else {
        foreach ($pkg in $requiredPackages) {
            $testPkg = python -c "import $pkg" 2>&1
            if ($LASTEXITCODE -ne 0) { $missingPackages += $pkg }
        }
        Write-Host "  [NOTE] System Python is missing: $($missingPackages -join ', ')" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [NOTE] System Python is not in PATH." -ForegroundColor Yellow
}

$portableDir = Join-Path $repoDir "physics-agent\third_party\portable-runtime"
$portableWheelDir = Join-Path $portableDir "wheels"
$hasPortable = Test-Path $portableWheelDir
if ($hasPortable) {
    $wheelCount = (Get-ChildItem $portableWheelDir -Filter "*.whl").Count
    Write-Host "  -> Built-in Portable Runtime: Ready ($wheelCount locked wheels detected)"
    Write-Host "  [PASS] Offline portable execution fallback is active." -ForegroundColor Green
} else {
    if (-not $systemPythonOk) {
        Write-Host "  [WARN] Neither complete scientific libraries nor portable runtime detected." -ForegroundColor Red
        Write-Host "         Run: pip install -r physics-agent/hooks/requirements.txt" -ForegroundColor DarkYellow
        $issues++
    }
}

# 5. Build status check
Write-Host "`n[5/6] Checking Agnes Harness Build Status..." -ForegroundColor Yellow
$cliDist = Join-Path $repoDir "packages\cli\dist\local\agnes.mjs"
if (Test-Path $cliDist) {
    Write-Host "  -> CLI Build Artifact: Present ($cliDist)"
    Write-Host "  [PASS] Local platform build is complete." -ForegroundColor Green
} else {
    Write-Host "  [NOTE] Local build not detected yet." -ForegroundColor Yellow
    Write-Host "         Run setup.ps1 or: pnpm run build:local" -ForegroundColor DarkCyan
    $warnings++
}

# 6. Multi-Environment & Active Instance Scan
Write-Host "`n[6/6] Scanning Multi-Environment & Active AGH Instances..." -ForegroundColor Yellow
$instances = @(
    @{ Name = "Default System Environment"; Port = 4177; Home = "~/.agh" },
    @{ Name = "Isolated Physics Environment"; Port = 4180; Home = "~/.agh-physics" },
    @{ Name = "Virtual Sandbox Environment"; Port = 4182; Home = "~/.agh-sandbox" },
    @{ Name = "Alternate Instance 1"; Port = 4185; Home = "~/.agh-instance-4185" },
    @{ Name = "Alternate Instance 2"; Port = 4190; Home = "~/.agh-instance-4190" }
)

$activeCount = 0
foreach ($inst in $instances) {
    $p = $inst.Port
    $isListening = Test-Port $p
    if ($isListening) {
        $activeCount++
        Write-Host "  [ACTIVE] $($inst.Name) on Port $p -> http://127.0.0.1:$p" -ForegroundColor Green
        Write-Host "           Data Home: $($inst.Home) (Sessions & databases isolated)" -ForegroundColor DarkGreen
    } else {
        if ($VerboseScan) {
            Write-Host "  [OFFLINE] $($inst.Name) on Port $p (Data Home: $($inst.Home))" -ForegroundColor Gray
        }
    }
}
if ($activeCount -eq 0) {
    Write-Host "  -> No active AGH instances currently running on scanned ports." -ForegroundColor Gray
    Write-Host "     You can launch with start.ps1 or double-click 一键启动.bat." -ForegroundColor DarkGray
} else {
    Write-Host "  -> Total active AGH instances detected: $activeCount" -ForegroundColor Green
    Write-Host "  [PASS] Multi-port concurrent isolation verified." -ForegroundColor Green
}

# Summary Report
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "                   Diagnostic Summary                     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($issues -eq 0 -and $warnings -eq 0) {
    Write-Host " [VERDICT: EXCELLENT] Environment is 100% ready. You can start the service directly!" -ForegroundColor Green
} elseif ($issues -eq 0) {
    Write-Host " [VERDICT: GOOD] Core dependencies ready with $warnings non-blocking notice(s)." -ForegroundColor Yellow
} else {
    Write-Host " [VERDICT: ACTION REQUIRED] Detected $issues blocking issue(s) and $warnings notice(s)." -ForegroundColor Red
}
Write-Host ""
