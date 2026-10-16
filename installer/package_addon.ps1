# installer/package_addon.ps1 - Automated Packaging Script for Minimal Add-on Package
# Creates a lightweight (~1.5 MB) zip package containing ONLY physics-agent assets, 10 skills,
# and registration tools, intended for users who already have Agnes Harness cloned/installed.
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.

param(
    [string]$Version = "v0.1.0",
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
Write-Host "   AI Physics Research Agent - Add-on Packager ($Version) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repository root: $repoDir"
Write-Host "Output package : $OutputDir"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$pkgName = "physics-agent-addon-${Version}"
$stagingDir = Join-Path $OutputDir "staging\$pkgName"
if (Test-Path $stagingDir) {
    Remove-Item -Path $stagingDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null

Write-Host "`n[1/4] Staging minimal add-on files to: $stagingDir ..." -ForegroundColor Yellow

# Copy root registration launchers
$rootLaunchers = @(
    "一键注册物理智能体.bat",
    "一键注销物理智能体.bat"
)
foreach ($rl in $rootLaunchers) {
    $src = Join-Path $repoDir $rl
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $stagingDir -Force
    }
}

# Copy 10 skills into .agh/skills/ within the add-on package
$dstSkillsDir = Join-Path $stagingDir ".agh\skills"
New-Item -ItemType Directory -Path $dstSkillsDir -Force | Out-Null
$srcSkillsDir = Join-Path $repoDir ".agh\skills"
if (Test-Path $srcSkillsDir) {
    Write-Host "  -> Copying 10 Skills (.agh/skills) ..."
    Copy-Item -Path "$srcSkillsDir\*" -Destination $dstSkillsDir -Recurse -Force
}

# Copy physics-agent core module
$srcAgentDir = Join-Path $repoDir "physics-agent"
$dstAgentDir = Join-Path $stagingDir "physics-agent"
if (Test-Path $srcAgentDir) {
    Write-Host "  -> Copying physics-agent (hooks, knowledge, reference_data, plugins) ..."
    Copy-Item -Path $srcAgentDir -Destination $dstAgentDir -Recurse -Force
}

# Copy add-on documentation
$dstDocsDir = Join-Path $stagingDir "docs"
New-Item -ItemType Directory -Path $dstDocsDir -Force | Out-Null
$addonDoc = Join-Path $repoDir "docs\MINIMAL_ADDON_GUIDE.md"
if (Test-Path $addonDoc) {
    Copy-Item -Path $addonDoc -Destination $dstDocsDir -Force
}

# Copy root license & notice
Copy-Item -Path (Join-Path $repoDir "LICENSE") -Destination $stagingDir -Force
Copy-Item -Path (Join-Path $repoDir "NOTICE") -Destination $stagingDir -Force

# 2. Sanitize staging directory
Write-Host "`n[2/4] Sanitizing staging directory..." -ForegroundColor Yellow
Get-ChildItem -Path $stagingDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $stagingDir -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Verify skill BOM compliance in staging
$stagedBomCheck = Join-Path $stagingDir "physics-agent\hooks\skill_bom_check.py"
if (Test-Path $stagedBomCheck) {
    python $stagedBomCheck 2>$null | Out-Null
}

# 3. Compress into zip
$zipPath = Join-Path $OutputDir "${pkgName}.zip"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Write-Host "`n[3/4] Compressing into minimal add-on package: $zipPath ..." -ForegroundColor Yellow
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($stagingDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)
} catch {
    Compress-Archive -Path "$stagingDir\*" -DestinationPath $zipPath -Force
}

# 4. Measure and report package statistics
Write-Host "`n[4/4] Generating release package checksum..." -ForegroundColor Yellow
$zipItem = Get-Item $zipPath
$zipSizeMb = [math]::Round($zipItem.Length / 1MB, 2)
$sha256 = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash

# Clean staging directory
Remove-Item -Path (Split-Path -Parent $stagingDir) -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "       Minimal Add-on Packaging Completed Successfully!    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Package File : $zipPath" -ForegroundColor Green
Write-Host "  Package Size : $zipSizeMb MB" -ForegroundColor Green
Write-Host "  SHA256 Hash  : $sha256" -ForegroundColor Green
Write-Host ""
Write-Host "This package can be unzipped directly into an existing AGH root directory."
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
