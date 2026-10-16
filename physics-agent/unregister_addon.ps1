# physics-agent/unregister_addon.ps1 - Add-on Uninstaller
# Non-destructively removes ONLY the 10 Physics Agent skills, leaving all user/third-party skills intact.
param([switch]$Force = $false)
$ErrorActionPreference = 'Stop'
$aghRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$skillsRoot = Join-Path $aghRoot ".agh\skills"
$physicsSkills = @(
    "physics-agent-orchestrator", "physics-agent-governance", "physics-state-check",
    "physics-pipeline", "physics-defense-lines", "physics-auditability",
    "physics-report-charting", "physics-report-writing", "physics-permission-shortfall",
    "physics-doc-parsing"
)
Write-Host "Removing Physics Agent skills from $skillsRoot ..." -ForegroundColor Yellow
foreach ($s in $physicsSkills) {
    $target = Join-Path $skillsRoot $s
    if (Test-Path $target) {
        Remove-Item -Path $target -Recurse -Force
        Write-Host "  -> Removed: $s" -ForegroundColor DarkGray
    }
}
Write-Host "[DONE] Physics Agent successfully unregistered. All third-party skills preserved." -ForegroundColor Green
