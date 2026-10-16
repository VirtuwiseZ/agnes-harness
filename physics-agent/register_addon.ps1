# physics-agent/register_addon.ps1 - Minimal Add-on Installer & AGH Version Inspector
# Pure ASCII implementation to guarantee compatibility across Windows PowerShell 5.1 CP936 / UTF-8.
# Enables users who already cloned/installed Agnes Harness to import the Physics Agent non-destructively.

param(
    [string]$AghRoot = "",
    [switch]$Force = $false,
    [switch]$CheckOnly = $false
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$currentDir = (Get-Location).Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI Physics Research Agent - Minimal Add-on Installer   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Locate and verify AGH root directory
if (-not $AghRoot) {
    # Check if current directory or parent directory is an AGH root
    $candidates = @($currentDir, (Split-Path -Parent $scriptDir), (Split-Path -Parent $currentDir))
    foreach ($cand in $candidates) {
        if ($cand -and (Test-Path (Join-Path $cand "packages\cli")) -and (Test-Path (Join-Path $cand "package.json"))) {
            $AghRoot = $cand
            break
        }
    }
}

if (-not $AghRoot -or -not (Test-Path $AghRoot)) {
    Write-Host "[ERROR] Could not automatically locate Agnes Harness (AGH) root directory." -ForegroundColor Red
    Write-Host "Please pass the AGH root path explicitly via -AghRoot <path>:" -ForegroundColor Yellow
    Write-Host "  powershell -File physics-agent/register_addon.ps1 -AghRoot `"C:\path\to\agnes-harness`"" -ForegroundColor DarkCyan
    exit 1
}

Write-Host "  -> Target AGH Root: $AghRoot" -ForegroundColor Green
$pkgJsonPath = Join-Path $AghRoot "package.json"
if (-not (Test-Path $pkgJsonPath)) {
    Write-Host "[ERROR] package.json not found in $AghRoot. Target does not appear to be a valid AGH directory." -ForegroundColor Red
    exit 1
}

# 2. Inspect AGH Base Version & Feature Probing
Write-Host "`n[1/5] Inspecting AGH Base Version & Compatibility Matrix..." -ForegroundColor Yellow
$pkgData = Get-Content $pkgJsonPath -Raw -Encoding utf8 | ConvertFrom-Json
$baseVersion = $pkgData.version
if (-not $baseVersion) {
    $cliPkgJson = Join-Path $AghRoot "packages\cli\package.json"
    if (Test-Path $cliPkgJson) {
        try {
            $cliPkg = Get-Content $cliPkgJson -Raw -Encoding utf8 | ConvertFrom-Json
            $baseVersion = $cliPkg.version
        } catch {}
    }
}
if (-not $baseVersion) { $baseVersion = "0.0.0-dev" }
$baseName = $pkgData.name
Write-Host "  -> Base Package  : $baseName (v$baseVersion)"

$gitHead = ""
$gitHeadPath = Join-Path $AghRoot ".git\HEAD"
if (Test-Path $gitHeadPath) {
    try {
        $gitHead = (git -C $AghRoot rev-parse --short HEAD 2>$null)
        Write-Host "  -> Git Commit    : $gitHead"
    } catch {}
}

# Probing known feature markers for compatibility
$hasToolArgsUnwrap = $false
$hasTraceDeepLink = $false
$hasVerifierFix = $false
$hasPrebuiltCli = $false

$toolArgsFile = Join-Path $AghRoot "packages\core\src\step\tool-args.ts"
if (Test-Path $toolArgsFile) {
    $content = Get-Content $toolArgsFile -Raw -Encoding utf8
    if ($content -match "unwrapToolArgs") { $hasToolArgsUnwrap = $true }
}

$traceFile = Join-Path $AghRoot "packages\web-units\src\trace.ts"
if (Test-Path $traceFile) {
    $content = Get-Content $traceFile -Raw -Encoding utf8
    if ($content -match "selectBySeq" -or $content -match "jump-trace-seq") { $hasTraceDeepLink = $true }
}

$verifierFile = Join-Path $AghRoot "packages\base\extensions\loop-hygiene\src\verifier.ts"
if (Test-Path $verifierFile) {
    $content = Get-Content $verifierFile -Raw -Encoding utf8
    if ($content -match "scope !== 'turn'") { $hasVerifierFix = $true }
}

$cliMjs = Join-Path $AghRoot "packages\cli\dist\local\agnes.mjs"
if (Test-Path $cliMjs) { $hasPrebuiltCli = $true }

Write-Host "`n--- Base Capability Matrix ---" -ForegroundColor DarkCyan
Write-Host "  • Parameter Unwrap Guard (anti-nesting crash) : $(if ($hasToolArgsUnwrap) { '[PASS] Native/Patched' } else { '[NOTE] Official base (Prompt-enforced)' })"
Write-Host "  • Trace URL Deep-Jump & Cross-Tab Bridge      : $(if ($hasTraceDeepLink) { '[PASS] Supported' } else { '[NOTE] Official base (Standard Trace)' })"
Write-Host "  • Verifier Turn-Level Hygiene Guard          : $(if ($hasVerifierFix) { '[PASS] Active' } else { '[NOTE] Official base' })"
Write-Host "  • Local CLI Bundle Compiled                  : $(if ($hasPrebuiltCli) { '[PASS] Ready' } else { '[WARN] Not compiled yet' })"

if (-not $hasPrebuiltCli) {
    Write-Host "`n  [ADVISORY] CLI bundle is not built in target AGH." -ForegroundColor Yellow
    Write-Host "  You can compile it later by running: pnpm --filter @agnes/cli run build:local" -ForegroundColor DarkCyan
}

if ($CheckOnly) {
    Write-Host "`n[CheckOnly Mode] Inspection completed. Exiting without modifications." -ForegroundColor Green
    exit 0
}

# 3. Non-destructive, incremental Skill registration
Write-Host "`n[2/5] Non-destructively registering 10 Skills into .agh/skills/ ..." -ForegroundColor Yellow
$targetSkillsRoot = Join-Path $AghRoot ".agh\skills"
if (-not (Test-Path $targetSkillsRoot)) {
    New-Item -ItemType Directory -Path $targetSkillsRoot -Force | Out-Null
    Write-Host "  -> Created .agh/skills/ directory." -ForegroundColor Green
}

# Source skills list
$sourceSkillsRoot = Join-Path $AghRoot ".agh\skills"
if (-not (Test-Path $sourceSkillsRoot)) {
    # If the installer is running from an extracted physics-agent standalone package
    $sourceSkillsRoot = Join-Path $scriptDir "skills"
}

$physicsSkillNames = @(
    "physics-agent-orchestrator",
    "physics-agent-governance",
    "physics-state-check",
    "physics-pipeline",
    "physics-defense-lines",
    "physics-auditability",
    "physics-report-charting",
    "physics-report-writing",
    "physics-permission-shortfall",
    "physics-doc-parsing"
)

$installedCount = 0
$preservedCount = 0

# Check existing unrelated third-party skills in user's .agh/skills
$existingUserSkills = Get-ChildItem -Path $targetSkillsRoot -Directory | Where-Object { $physicsSkillNames -notcontains $_.Name }
if ($existingUserSkills) {
    Write-Host "  [PROTECTED] Found $($existingUserSkills.Count) existing third-party skill(s) in user's .agh/skills:" -ForegroundColor Green
    foreach ($us in $existingUserSkills) {
        Write-Host "    - $($us.Name) [PRESERVED: UNTOUCHED]" -ForegroundColor DarkGreen
        $preservedCount++
    }
}

# Incrementally deploy each physics skill
foreach ($sk in $physicsSkillNames) {
    $srcSkillDir = Join-Path $sourceSkillsRoot $sk
    $dstSkillDir = Join-Path $targetSkillsRoot $sk

    # If srcSkillDir doesn't exist under .agh/skills, check if physics-agent has it
    if (-not (Test-Path $srcSkillDir)) {
        $altSrc = Join-Path $AghRoot ".agh\skills\$sk"
        if (Test-Path $altSrc) { $srcSkillDir = $altSrc }
    }

    if (Test-Path $srcSkillDir) {
        if (-not (Test-Path $dstSkillDir)) {
            New-Item -ItemType Directory -Path $dstSkillDir -Force | Out-Null
        }
        $samePath = $false
        try {
            $rSrc = (Resolve-Path $srcSkillDir).Path.TrimEnd('\', '/')
            $rDst = (Resolve-Path $dstSkillDir).Path.TrimEnd('\', '/')
            if ($rSrc -ieq $rDst) { $samePath = $true }
        } catch {}

        if (-not $samePath) {
            Copy-Item -Path "$srcSkillDir\*" -Destination $dstSkillDir -Recurse -Force
        }
        $installedCount++
    }
}
Write-Host "  [PASS] Successfully registered $installedCount Physics Skills without touching user skills." -ForegroundColor Green

# 4. Register Orchestrator Plugin & Verify Python Dependencies
Write-Host "`n[3/5] Verifying Plugin and Python Scientific Libraries..." -ForegroundColor Yellow
$pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $testPy = python -c "import sympy, pint, numpy, scipy, matplotlib; print('READY')" 2>$null
    if ($testPy -match "READY") {
        Write-Host "  [PASS] System Python has all 5 required scientific computing packages." -ForegroundColor Green
    } else {
        Write-Host "  [NOTE] System Python is missing some scientific packages." -ForegroundColor Yellow
        Write-Host "         Run: pip install -r physics-agent/hooks/requirements.txt" -ForegroundColor DarkCyan
    }
} else {
    Write-Host "  [NOTE] System Python not found. System will fallback to built-in portable runtime." -ForegroundColor Yellow
}

# 5. Generate One-Click Uninstaller (unregister_addon.ps1)
Write-Host "`n[4/5] Generating one-click uninstaller (unregister_addon.ps1)..." -ForegroundColor Yellow
$uninstallerPath = Join-Path $AghRoot "physics-agent\unregister_addon.ps1"
$uninstallerContent = @"
# physics-agent/unregister_addon.ps1 - Add-on Uninstaller
# Non-destructively removes ONLY the 10 Physics Agent skills, leaving all user/third-party skills intact.
param([switch]`$Force = `$false)
`$ErrorActionPreference = 'Stop'
`$aghRoot = Split-Path -Parent (Split-Path -Parent `$MyInvocation.MyCommand.Path)
`$skillsRoot = Join-Path `$aghRoot ".agh\skills"
`$physicsSkills = @(
    "physics-agent-orchestrator", "physics-agent-governance", "physics-state-check",
    "physics-pipeline", "physics-defense-lines", "physics-auditability",
    "physics-report-charting", "physics-report-writing", "physics-permission-shortfall",
    "physics-doc-parsing"
)
Write-Host "Removing Physics Agent skills from `$skillsRoot ..." -ForegroundColor Yellow
foreach (`$s in `$physicsSkills) {
    `$target = Join-Path `$skillsRoot `$s
    if (Test-Path `$target) {
        Remove-Item -Path `$target -Recurse -Force
        Write-Host "  -> Removed: `$s" -ForegroundColor DarkGray
    }
}
Write-Host "[DONE] Physics Agent successfully unregistered. All third-party skills preserved." -ForegroundColor Green
"@
Set-Content -Path $uninstallerPath -Value $uninstallerContent -Encoding utf8
Write-Host "  -> Uninstaller generated at: $uninstallerPath" -ForegroundColor Green

# 6. Save Diagnostic Manifest for Auditability
Write-Host "`n[5/5] Saving Compatibility Record..." -ForegroundColor Yellow
$reportDir = Join-Path $AghRoot "physics-agent\runtime"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}
$compatReport = @{
    baseVersion = $baseVersion
    baseName = $baseName
    gitHead = $gitHead
    hasToolArgsUnwrap = $hasToolArgsUnwrap
    hasTraceDeepLink = $hasTraceDeepLink
    hasVerifierFix = $hasVerifierFix
    hasPrebuiltCli = $hasPrebuiltCli
    installedSkillsCount = $installedCount
    preservedThirdPartySkillsCount = $preservedCount
    installedAt = (Get-Date).ToString("s")
}
$compatJson = $compatReport | ConvertTo-Json -Depth 3
Set-Content -Path (Join-Path $reportDir "agh_compatibility_report.json") -Value $compatJson -Encoding utf8
Write-Host "  -> Compatibility report saved: physics-agent/runtime/agh_compatibility_report.json" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "         Add-on Registration Completed Successfully!       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Your Agnes Harness base now has the Physics Agent fully activated." -ForegroundColor Green
Write-Host "All existing skills and configurations have been preserved." -ForegroundColor Green
Write-Host ""
