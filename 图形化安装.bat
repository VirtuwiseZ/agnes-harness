@echo off
chcp 65001 >nul
title AI 物理科研工作站 - 图形化安装向导
cd /d "%~dp0"

if exist "installer\AI_Physics_Agent_Setup.exe" (
    start "" "installer\AI_Physics_Agent_Setup.exe"
    exit /b 0
)

echo ==========================================================
echo   未检测到已编译的安装包，正在为您自动构建 Setup.exe...
echo ==========================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "installer\build_installer.ps1"

if exist "installer\AI_Physics_Agent_Setup.exe" (
    echo.
    echo 正在启动图形化安装向导...
    start "" "installer\AI_Physics_Agent_Setup.exe"
    exit /b 0
) else (
    echo [错误] 编译图形化安装程序失败，请检查编译环境或使用 一键安装.bat。
    pause
    exit /b 1
)
