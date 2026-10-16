@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 增量技能注销向导
cd /d "%~dp0"

echo ==========================================================
echo   正在从当前 Agnes Harness 中安全注销物理智能体技能...
echo ==========================================================
echo.

if not exist "physics-agent\unregister_addon.ps1" (
    echo [提示] 尚未检测到注销脚本。正在自动生成...
    powershell -NoProfile -ExecutionPolicy Bypass -File "physics-agent\register_addon.ps1" -CheckOnly
)

powershell -NoProfile -ExecutionPolicy Bypass -File "physics-agent\unregister_addon.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [错误] 注销过程遇到异常，请检查上方提示。
    pause
    exit /b %errorlevel%
)

echo.
echo 按任意键关闭本窗口...
pause >nul
