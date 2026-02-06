@echo off
chcp 65001 >nul
echo ================================
echo QQ聊天机器人 - 配置测试
echo ================================
echo.

if not exist venv (
    echo 错误: 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python test_config.py

pause
