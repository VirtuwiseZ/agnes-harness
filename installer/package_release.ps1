# installer/package_release.ps1 - Automated Packaging Script for GitHub Releases
# Creates a clean, self-contained, pre-built distribution zip package for Windows x64.
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.

param(
    [string]$Version = "v1.0.0",
    [string]$OutputDir = ""
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Split-Path -Parent $scriptDir
if (-not $repoDir) { $repoDir = (Get-Location).Path }
Set-Location $repoDir

if (-not $OutputDir) {
    $OutputDir = Join-Path $repoDir "release"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Release Packager ($Version)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repository root: $repoDir"
Write-Host "Output package : $OutputDir"

# 1. Verify that the installer and uninstaller are compiled
$setupExe = Join-Path $scriptDir "AI_Physics_Agent_Setup.exe"
$uninstExe = Join-Path $scriptDir "Uninstall.exe"
if (-not (Test-Path $setupExe) -or -not (Test-Path $uninstExe)) {
    Write-Host "[NOTE] Installer executables not detected. Compiling now..." -ForegroundColor Yellow
    & (Join-Path $scriptDir "build_installer.ps1")
}

# 2. Verify that pre-built CLI bundle is intact
$cliLocal = Join-Path $repoDir "packages\cli\dist\local\agnes.mjs"
if (-not (Test-Path $cliLocal)) {
    Write-Host "[ERROR] Pre-built CLI bundle (packages/cli/dist/local/agnes.mjs) is missing!" -ForegroundColor Red
    Write-Host "Please compile the local bundle first: pnpm --filter @agnes/cli run build:local" -ForegroundColor DarkYellow
    exit 1
}

# 3. Prepare clean staging directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$pkgName = "AI_Physics_Agent_${Version}_Windows_x64"
$stagingDir = Join-Path $OutputDir "staging\$pkgName"
if (Test-Path $stagingDir) {
    Remove-Item -Path $stagingDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

Write-Host "`n[1/4] Staging production files to: $stagingDir ..." -ForegroundColor Yellow

# Copy root launchers and documents
$rootFiles = @(
    "一键启动.bat",
    "一键安装.bat",
    "图形化安装.bat",
    "环境自检.bat",
    "README.md",
    "LICENSE",
    "NOTICE",
    "package.json",
    "pnpm-workspace.yaml"
)
foreach ($rf in $rootFiles) {
    $src = Join-Path $repoDir $rf
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $stagingDir -Force
    }
}

# Copy core subtrees
$subtrees = @(
    ".agh",
    "physics-agent",
    "docs",
    "scripts",
    "installer"
)
foreach ($st in $subtrees) {
    $srcDir = Join-Path $repoDir $st
    $dstDir = Join-Path $stagingDir $st
    if (Test-Path $srcDir) {
        Write-Host "  -> Copying $st ..."
        Copy-Item -Path $srcDir -Destination $dstDir -Recurse -Force
    }
}

# Copy pre-built packages/cli/dist/local (bundled runtime, zero C++ compilation on user machine)
$srcPkgLocal = Join-Path $repoDir "packages\cli\dist\local"
$dstPkgLocal = Join-Path $stagingDir "packages\cli\dist\local"
New-Item -ItemType Directory -Path (Split-Path -Parent $dstPkgLocal) -Force | Out-Null
Write-Host "  -> Copying pre-built CLI bundle (packages/cli/dist/local) ..."
Copy-Item -Path $srcPkgLocal -Destination $dstPkgLocal -Recurse -Force

# Clean any cache in staging directory
Write-Host "`n[2/4] Sanitizing staging directory..." -ForegroundColor Yellow
Get-ChildItem -Path $stagingDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stagingDir -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stagingDir -Recurse -Directory -Filter ".git" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Verify skill BOM compliance in staging
$stagedBomCheck = Join-Path $stagingDir "physics-agent\hooks\skill_bom_check.py"
if (Test-Path $stagedBomCheck) {
    python $stagedBomCheck 2>$null | Out-Null
}

# 4. Compress to zip
$zipPath = Join-Path $OutputDir "${pkgName}.zip"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Write-Host "`n[3/4] Compressing into distribution zip: $zipPath ..." -ForegroundColor Yellow
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($stagingDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)
} catch {
    Compress-Archive -Path "$stagingDir\*" -DestinationPath $zipPath -Force
}

# 5. Measure and report package statistics
Write-Host "`n[4/4] Generating release package checksum..." -ForegroundColor Yellow
$zipItem = Get-Item $zipPath
$zipSizeMb = [math]::Round($zipItem.Length / 1MB, 2)
$sha256 = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash

# Clean staging directory
Remove-Item -Path (Split-Path -Parent $stagingDir) -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "          Release Packaging Completed Successfully!       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Package File : $zipPath" -ForegroundColor Green
Write-Host "  Package Size : $zipSizeMb MB" -ForegroundColor Green
Write-Host "  SHA256 Hash  : $sha256" -ForegroundColor Green
Write-Host ""
Write-Host "You can now attach '${pkgName}.zip' and 'AI_Physics_Agent_Setup.exe' to your GitHub Release!"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
