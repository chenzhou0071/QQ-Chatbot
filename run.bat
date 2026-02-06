@echo off
chcp 65001 >nul
echo ================================
echo QQ聊天机器人 - 启动中...
echo ================================
echo.

if not exist venv (
    echo 错误: 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python src/bot.py

pause
