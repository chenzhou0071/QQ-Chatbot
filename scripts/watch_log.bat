@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo 实时监控Bot日志...
echo 按 Ctrl+C 停止
echo.

powershell -Command "Get-Content data\logs\bot-2026-02-14.log -Wait -Tail 20 -Encoding UTF8"
