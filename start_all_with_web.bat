@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo 一键启动 QQ Bot + Web 管理界面
echo ========================================
echo.

echo [1/2] 启动 Web 管理界面...
start "QQ Bot Web管理界面" cmd /k "call venv\Scripts\activate.bat && python web\app.py"

timeout /t 3 /nobreak >nul

echo [2/2] 打开浏览器...
start http://localhost:5000

echo.
echo ========================================
echo 启动完成！
echo Web管理界面: http://localhost:5000
echo 在Web界面中控制Bot的启动和停止
echo ========================================
echo.

pause
