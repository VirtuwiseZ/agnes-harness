# commit-latest-batch.ps1 - Automated multi-batch commit for all latest audited assets
# Designed for 100% pure ASCII execution to prevent PowerShell 5.1 CP936 encoding errors.
$ErrorActionPreference = 'Stop'

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Executing 4-Batch Audited Commits for Latest Assets   " -ForegroundColor Cyan
Write-Host "==========================================================`n" -ForegroundColor Cyan

# Step 0: Clean temporary probe scripts and previous obsolete commit scripts (Category B)
Write-Host "[0/5] Cleaning temporary probe scripts and obsolete runners..." -ForegroundColor Yellow
$tempFiles = @(
    "build_and_check_artillery.py",
    "build_artillery_result.txt",
    "build_jupiter_capture_report.py",
    "find_task_slug.py",
    "check_capture_html.py",
    "commit-all-audited.ps1",
    "commit-fixes.ps1",
    "commit-return-btn.ps1",
    "commit-round.ps1",
    "commit-shortfall.ps1"
)
foreach ($f in $tempFiles) {
    if (Test-Path $f) {
        Remove-Item -Path $f -Force -ErrorAction SilentlyContinue
        Write-Host " -> Removed temporary file: $f" -ForegroundColor DarkGray
    }
}

# Step 1: Commit Batch 1 - Visualizer layout restoration & clean links
Write-Host "`n[1/5] Committing Batch 1: Visualizer layout & self-healing alignment..." -ForegroundColor Yellow
git add physics-agent/hooks/trace_visualizer.py
git add research_report_jupiter-moon-gravity-assist-capture.html

if (Test-Path "dev-notes\commit_msg_batch1.txt") {
    git commit -F "dev-notes\commit_msg_batch1.txt"
    Remove-Item -Path "dev-notes\commit_msg_batch1.txt" -Force
    Write-Host " -> Batch 1 committed successfully." -ForegroundColor Green
} else {
    Write-Host " -> Skipped Batch 1 (no changes or message missing)." -ForegroundColor DarkGray
}

# Step 2: Commit Batch 2 - Dual-path delivery protocol & generic skills
Write-Host "`n[2/5] Committing Batch 2: Generic dual-path delivery protocol..." -ForegroundColor Yellow
git add physics-agent/knowledge/delivery_template.md
git add .agh/skills/physics-agent-governance/SKILL.md
git add .agh/skills/physics-report-writing/SKILL.md

if (Test-Path "dev-notes\commit_msg_batch2.txt") {
    git commit -F "dev-notes\commit_msg_batch2.txt"
    Remove-Item -Path "dev-notes\commit_msg_batch2.txt" -Force
    Write-Host " -> Batch 2 committed successfully." -ForegroundColor Green
} else {
    Write-Host " -> Skipped Batch 2 (no changes or message missing)." -ForegroundColor DarkGray
}

# Step 3: Commit Batch 3 - Development audit log, .gitignore & test archive
Write-Host "`n[3/5] Committing Batch 3: Development audit log & configuration..." -ForegroundColor Yellow
git add .gitignore
git add *.bat
git add dev-notes/self-tests/08/test8-*.md
git add dev-notes/self-tests/06/research_report_*.html

if (Test-Path "dev-notes\commit_msg_batch3.txt") {
    git commit -F "dev-notes\commit_msg_batch3.txt"
    Remove-Item -Path "dev-notes\commit_msg_batch3.txt" -Force
    Write-Host " -> Batch 3 committed successfully." -ForegroundColor Green
} else {
    Write-Host " -> Skipped Batch 3 (no changes or message missing)." -ForegroundColor DarkGray
}

# Step 4: Commit Batch 4 - Competition guidelines & presentation materials
Write-Host "`n[4/5] Committing Batch 4: Competition guidelines & roadshow slides..." -ForegroundColor Yellow
git add dev-notes/competition/*.md

if (Test-Path "dev-notes\commit_msg_batch4.txt") {
    git commit -F "dev-notes\commit_msg_batch4.txt"
    Remove-Item -Path "dev-notes\commit_msg_batch4.txt" -Force
    Write-Host " -> Batch 4 committed successfully." -ForegroundColor Green
} else {
    Write-Host " -> Skipped Batch 4 (no changes or message missing)." -ForegroundColor DarkGray
}

# Clean any residual commit message text files
Remove-Item -Path "dev-notes\commit_msg_*.txt" -Force -ErrorAction SilentlyContinue

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " All batches committed! Recent Git Log:" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
git log -4 --oneline
Write-Host "`nCurrent Git Status:" -ForegroundColor Cyan
git status
