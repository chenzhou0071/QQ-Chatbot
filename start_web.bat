@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo 启动 QQ Bot Web 管理界面
echo ========================================
echo.

echo [1/2] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [2/2] 启动 Web 服务器...
echo.
echo ========================================
echo Web 管理界面已启动
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python web\app.py

pause
