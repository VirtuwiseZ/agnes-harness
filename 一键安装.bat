@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 一键安装与环境配置
cd /d "%~dp0"

echo ==========================================================
echo    AI 物理科研工作站 - 正在启动一键安装向导...
echo ==========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [错误] 安装过程遇到问题，请参考上方提示或查看 docs/INSTALL_GUIDE.md
    pause
    exit /b %errorlevel%
)

echo.
echo 按任意键退出安装向导...
pause >nul
