$ErrorActionPreference = "Stop"
Set-Location "E:\agnes-harness"
$commit = "dab2e02c"
$dest = "E:\physics-agent-test-artifacts\ability-test-run-01\program-design\runtime"
if (!(Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }

$targets = @()
$targets += "program-design/runtime/atmosphere_data_0_150km.json"
$targets += "program-design/runtime/boundary_spec_space_diving.json"
$targets += "program-design/runtime/descent_model.py"
$targets += "program-design/runtime/node4_pending_note.md"
$targets += "program-design/runtime/problem_state_space_diving.json"
$targets += "program-design/runtime/report_space_diving.md"

foreach ($p in $targets) {
    $content = git show ("{0}:{1}" -f $commit, $p)
    $fileName = Split-Path $p -Leaf
    $targetPath = Join-Path $dest $fileName
    [System.IO.File]::WriteAllText($targetPath, $content)
    Write-Host ("wrote " + $fileName)
}
Write-Host "done"
