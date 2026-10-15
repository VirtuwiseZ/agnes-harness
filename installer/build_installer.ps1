# installer/build_installer.ps1 - Automated Compiler for Windows .exe Installer & Uninstaller
# Uses built-in Microsoft .NET Framework C# compiler (csc.exe), requiring no extra SDK.
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir = Split-Path -Parent $scriptDir
if (-not $repoDir) { $repoDir = (Get-Location).Path }
Set-Location $repoDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Building Windows .exe Setup " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repo Root: $repoDir"
Write-Host "Installer Directory: $scriptDir"

# 1. Locate C# compiler (csc.exe)
$cscCandidates = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)
$cscPath = ""
foreach ($c in $cscCandidates) {
    if (Test-Path $c) {
        $cscPath = $c
        break
    }
}
if (-not $cscPath) {
    $found = Get-Command "csc.exe" -ErrorAction SilentlyContinue
    if ($found) { $cscPath = $found.Source }
}

if (-not $cscPath) {
    Write-Host "[ERROR] C# compiler (csc.exe) not found on this system." -ForegroundColor Red
    exit 1
}
Write-Host "  -> Using C# Compiler: $cscPath" -ForegroundColor Green

# 2. Ensure application icon exists
$iconPath = Join-Path $scriptDir "app.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "  -> Generating application icon (app.ico)..." -ForegroundColor Yellow
    $genIconScript = Join-Path $scriptDir "generate_icon.py"
    if (Test-Path $genIconScript) {
        python $genIconScript
    }
}
if (-not (Test-Path $iconPath)) {
    Write-Host "[WARN] app.ico not found. Binaries will compile without custom icon." -ForegroundColor Yellow
    $iconArg = ""
} else {
    Write-Host "  -> Icon verified: $iconPath" -ForegroundColor Green
    $iconArg = "/win32icon:`"$iconPath`""
}

# 3. Compile Uninstall.exe
Write-Host "`n[1/2] Compiling native Uninstaller (Uninstall.exe)..." -ForegroundColor Yellow
$uninstSrc = Join-Path $scriptDir "src\UninstallProgram.cs"
$uninstOut = Join-Path $scriptDir "Uninstall.exe"
$uninstArgs = @(
    "/nologo",
    "/target:winexe",
    "/optimize+",
    "/out:`"$uninstOut`"",
    "/r:System.dll",
    "/r:System.Drawing.dll",
    "/r:System.Windows.Forms.dll"
)
if ($iconArg) { $uninstArgs += $iconArg }
$uninstArgs += "`"$uninstSrc`""

& $cscPath $uninstArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Compilation of Uninstall.exe failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
$uninstSize = (Get-Item $uninstOut).Length
Write-Host "  [PASS] Successfully compiled: $uninstOut ($uninstSize bytes)" -ForegroundColor Green

# 4. Compile AI_Physics_Agent_Setup.exe
Write-Host "`n[2/2] Compiling Graphical Installer (AI_Physics_Agent_Setup.exe)..." -ForegroundColor Yellow
$setupSrc = Join-Path $scriptDir "src\SetupProgram.cs"
$setupOut = Join-Path $scriptDir "AI_Physics_Agent_Setup.exe"
$setupArgs = @(
    "/nologo",
    "/target:winexe",
    "/optimize+",
    "/out:`"$setupOut`"",
    "/r:System.dll",
    "/r:System.Drawing.dll",
    "/r:System.Windows.Forms.dll",
    "/r:System.Core.dll",
    "/r:Microsoft.CSharp.dll"
)
if ($iconArg) { $setupArgs += $iconArg }
$setupArgs += "`"$setupSrc`""

& $cscPath $setupArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Compilation of AI_Physics_Agent_Setup.exe failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
$setupSize = (Get-Item $setupOut).Length
Write-Host "  [PASS] Successfully compiled: $setupOut ($setupSize bytes)" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "          Installer Build Completed Successfully!         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Generated binaries:"
Write-Host "  - Installer  : $setupOut" -ForegroundColor Green
Write-Host "  - Uninstaller: $uninstOut" -ForegroundColor Green
Write-Host ""
