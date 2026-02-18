@echo off
chcp 65001 >nul
title QQ Bot 管理系统

echo.
echo ================================================
echo           QQ Bot 管理系统 - 启动中
echo ================================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境，请先运行 install.bat 安装
    pause
    exit /b 1
)

echo [1/2] 启动 NapCat...
start "NapCat" cmd /k "cd napcat\napcat && napcat.bat"
timeout /t 2 /nobreak >nul

echo [2/2] 启动 Web 管理界面...
start "Web管理" cmd /k "call venv\Scripts\activate.bat && python web\app.py"
timeout /t 3 /nobreak >nul

echo.
echo ================================================
echo              启动完成！
echo ================================================
echo.
echo 1. NapCat 已启动（扫码登录QQ）
echo 2. Web 管理界面已启动
echo.
echo 访问地址: http://localhost:5000
echo.
echo 提示：
echo - 在 Web 界面可以启动/停止 Bot
echo - 在 Web 界面可以查看实时日志
echo - 在 Web 界面可以修改配置
echo.
echo 按任意键打开 Web 管理界面...
pause >nul

start http://localhost:5000

exit
