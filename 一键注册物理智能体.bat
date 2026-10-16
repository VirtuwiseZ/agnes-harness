@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 增量技能与插件注册向导
cd /d "%~dp0"

echo ==========================================================
echo   正在自动向当前 Agnes Harness 基座注册物理智能体...
echo ==========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "physics-agent\register_addon.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [错误] 注册过程遇到异常，请检查上方提示。
    pause
    exit /b %errorlevel%
)

echo.
echo 按任意键关闭本窗口...
pause >nul
