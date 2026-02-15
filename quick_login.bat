@echo off
chcp 65001 >nul

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo.
echo ========================================
echo QQ机器人快速登录
echo ========================================
echo.
echo 正在停止当前进程...

taskkill /F /IM QQ.exe 2>nul
taskkill /F /IM python.exe 2>nul

timeout /t 2 /nobreak >nul

echo.
echo 正在启动NapCat（快速登录模式）...
echo.

cd napcat\napcat
start "NapCat" launcher.bat -q 3966049171

timeout /t 5 /nobreak >nul

cd /d "%ROOT_DIR%"

echo.
echo 正在启动Bot...
echo.

start "Bot" /D "%ROOT_DIR%" cmd /c "call venv\Scripts\activate.bat && python src\bot.py"

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 提示：
echo - NapCat 和 Bot 已在后台运行
echo - 如需查看日志，运行 scripts\watch_log.bat
echo - 如需停止，关闭 NapCat 和 Bot 窗口
echo.
echo 如果登录失败，请手动扫码：
echo 1. 打开 napcat\napcat\cache\qrcode.png
echo 2. 用手机QQ扫描二维码
echo 3. 授权登录
echo.
pause
