@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 服务启动器
cd /d "%~dp0"

echo ==========================================================
echo    AI 物理科研工作站 - 正在启动本地服务...
echo ==========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动服务失败。若尚未安装，请先双击运行 一键安装.bat
    echo 或双击运行 环境自检.bat 诊断运行环境。
    echo.
    pause
    exit /b %errorlevel%
)
