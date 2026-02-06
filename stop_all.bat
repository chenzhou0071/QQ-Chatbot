@echo off
chcp 65001 >nul
echo ========================================
echo QQ 聊天机器人 - 一键关闭
echo ========================================
echo.

echo 正在关闭所有程序...
echo.

taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
taskkill /F /IM QQ.exe 2>nul

echo.
echo ========================================
echo 已关闭所有程序
echo ========================================
echo.
pause
