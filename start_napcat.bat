@echo off
chcp 65001 >nul
echo ========================================
echo 启动 NapCat
echo ========================================
echo.
echo 机器人账号：3966049171
echo WebUI 地址：http://127.0.0.1:6099/webui
echo.
echo 启动中...
echo.

cd /d "%~dp0napcat"
start napcat.bat

echo.
echo NapCat 已启动！
echo.
echo 下一步：
echo 1. 浏览器会自动打开 WebUI
echo 2. 使用 Token 登录或扫码
echo 3. 在 WebUI 中配置 WebSocket
echo    地址：ws://127.0.0.1:3001
echo 4. 机器人已在运行，配置后即可使用
echo.
pause
