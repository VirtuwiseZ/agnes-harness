@echo off
chcp 65001 >nul
title AGH Physics-Agent - Test Runner
cd /d "%~dp0"
echo ==========================================================
echo    Starting AGH Test Environment on Port 4180...
echo ==========================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-test-runner.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Process exited with code: %errorlevel%
    pause
)
