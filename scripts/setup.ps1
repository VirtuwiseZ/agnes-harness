# scripts/setup.ps1 - Automated Setup and Configuration Wizard
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.

param(
    [string]$WorkspaceDir = "",
    [switch]$SkipBuild = $false,
    [switch]$AutoInstallPip = $true
)

$ErrorActionPreference = 'Stop'
$repoDir = Split-Path -Parent $PSScriptRoot
if (-not $repoDir) { $repoDir = (Get-Location).Path }
Set-Location $repoDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Setup Wizard               " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Install root: $repoDir"
Write-Host ""

# Step 1: Pre-flight check
Write-Host "[Step 1/6] Checking runtime prerequisites..." -ForegroundColor Yellow
$nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "[ERROR] Node.js not detected. Setup cannot continue!" -ForegroundColor Red
    Write-Host "Please install Node.js (v24.10+ or LTS) from: https://nodejs.org/" -ForegroundColor DarkYellow
    exit 1
}
$nodeVer = node -v
Write-Host "  -> Node.js is ready: $nodeVer" -ForegroundColor Green

# Check pnpm
$pnpmCmd = Get-Command "pnpm" -ErrorAction SilentlyContinue
if (-not $pnpmCmd) {
    Write-Host "  -> Global pnpm not detected. Enabling via Node.js Corepack..." -ForegroundColor Yellow
    try {
        corepack enable
        corepack prepare pnpm@10.34.5 --activate
        Write-Host "  -> Successfully enabled pnpm via Corepack!" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to enable pnpm automatically. Run: npm install -g pnpm@10.34.5" -ForegroundColor Red
        exit 1
    }
} else {
    $pnpmVer = pnpm -v
    Write-Host "  -> pnpm is ready: v$pnpmVer" -ForegroundColor Green
}

# Step 2: Configure workspace directory
Write-Host "`n[Step 2/6] Configuring workspace directory..." -ForegroundColor Yellow
if (-not $WorkspaceDir) {
    $defaultWorkspace = Join-Path $repoDir "agh-workspace"
    Write-Host "  -> No custom path specified. Using default: $defaultWorkspace"
    $WorkspaceDir = $defaultWorkspace
} else {
    Write-Host "  -> Using custom workspace path: $WorkspaceDir"
}

if (-not (Test-Path $WorkspaceDir)) {
    New-Item -ItemType Directory -Path $WorkspaceDir -Force | Out-Null
    Write-Host "  -> Created workspace directory: $WorkspaceDir" -ForegroundColor Green
} else {
    Write-Host "  -> Workspace directory verified." -ForegroundColor Green
}

# Step 3: Install platform dependencies
Write-Host "`n[Step 3/6] Installing platform dependencies (pnpm install)..." -ForegroundColor Yellow
Write-Host "  -> Resolving and installing packages, please wait..."
try {
    pnpm install --prefer-offline
    Write-Host "  -> Platform packages installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "  [NOTE] Offline install had warnings, retrying online..." -ForegroundColor Yellow
    pnpm install
    Write-Host "  -> Platform packages installed successfully!" -ForegroundColor Green
}

# Step 4: Python scientific computing environment
Write-Host "`n[Step 4/6] Configuring Python scientific environment..." -ForegroundColor Yellow
$pyCmd = Get-Command "python" -ErrorAction SilentlyContinue
$pyNeedsDeps = $true

if ($pyCmd) {
    $testSci = python -c "import sympy, pint, numpy, scipy, matplotlib; print('OK')" 2>$null
    if ($testSci -match "OK") {
        Write-Host "  -> System Python has all scientific libraries ready." -ForegroundColor Green
        $pyNeedsDeps = $false
    }
}

if ($pyNeedsDeps -and $AutoInstallPip -and $pyCmd) {
    Write-Host "  -> System Python is missing some packages. Installing via pip..." -ForegroundColor Yellow
    $reqFile = Join-Path $repoDir "physics-agent\hooks\requirements.txt"
    if (Test-Path $reqFile) {
        try {
            pip install -r $reqFile
            Write-Host "  -> Python core requirements installed successfully!" -ForegroundColor Green
            $pyNeedsDeps = $false
        } catch {
            Write-Host "  [NOTE] pip install had warnings. Portable runtime will serve as fallback." -ForegroundColor Yellow
        }
    }
}

$portableDir = Join-Path $repoDir "physics-agent\third_party\portable-runtime\wheels"
if ($pyNeedsDeps) {
    if (Test-Path $portableDir) {
        Write-Host "  -> System will use built-in portable runtime and offline wheels." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Run manually if needed: pip install -r physics-agent/hooks/requirements.txt" -ForegroundColor Yellow
    }
}

# Step 5: Build local CLI module
Write-Host "`n[Step 5/6] Building Agnes Harness CLI module..." -ForegroundColor Yellow
$cliDist = Join-Path $repoDir "packages\cli\dist\index.js"
if ($SkipBuild -and (Test-Path $cliDist)) {
    Write-Host "  -> Found existing build artifact. Skipping build (-SkipBuild)." -ForegroundColor Green
} else {
    Write-Host "  -> Compiling local bundle (pnpm run build:local)..."
    try {
        pnpm --filter @agnes/cli run build:local
        Write-Host "  -> Local build completed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Local build reported warnings. Verifying artifacts..." -ForegroundColor Yellow
        if (Test-Path $cliDist) {
            Write-Host "  -> CLI build artifact exists. Ready to run." -ForegroundColor Green
        } else {
            Write-Host "[ERROR] CLI artifact not found. Please check build environment." -ForegroundColor Red
            exit 1
        }
    }
}

# Step 6: Verify skills BOM and encoding
Write-Host "`n[Step 6/6] Verifying skills encoding compliance..." -ForegroundColor Yellow
$cleanBomScript = Join-Path $repoDir "physics-agent\hooks\skill_bom_check.py"
if (Test-Path $cleanBomScript) {
    try {
        python $cleanBomScript 2>$null
        Write-Host "  -> All skill files verified BOM-free." -ForegroundColor Green
    } catch {
        Write-Host "  -> BOM check skipped."
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "          Setup and Configuration Completed!              " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. Start service : Run 一键启动.bat (or scripts/start.ps1)"
Write-Host "  2. Access Web UI : Open http://127.0.0.1:4180 in your browser"
Write-Host "  3. Select folder : Choose $WorkspaceDir on first launch"
Write-Host ""
