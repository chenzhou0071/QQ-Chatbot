@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo 启动 QQ 机器人
echo ========================================
echo.

echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [2/3] 检查配置...
if not exist "config\config.yaml" (
    echo ❌ 配置文件不存在: config\config.yaml
    pause
    exit /b 1
)

if not exist "config\.env" (
    echo ❌ 环境变量文件不存在: config\.env
    pause
    exit /b 1
)

echo [3/3] 启动 Bot...
echo.
echo ========================================
echo Bot 正在运行...
echo 按 Ctrl+C 停止
echo ========================================
echo.

python src\bot.py

pause
