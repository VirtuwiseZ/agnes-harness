@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 运行环境自检
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\doctor.ps1"
echo.
echo 按任意键关闭自检窗口...
pause >nul
