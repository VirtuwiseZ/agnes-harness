@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 服务启动与多环境调度器
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start.ps1" %*
if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动服务遇到异常。
    echo 若尚未安装，请双击运行 一键安装.bat 或 图形化安装.bat。
    echo 若需排查环境，请双击运行 环境自检.bat。
    echo.
    pause
    exit /b %errorlevel%
)
