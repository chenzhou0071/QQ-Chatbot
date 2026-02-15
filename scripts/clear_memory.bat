@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo.
echo ========================================
echo 清空机器人记忆数据
echo ========================================
echo.
echo 此脚本将清空：
echo   - 对话上下文
echo   - 聊天记录
echo   - 向量记忆
echo.
echo 保留的数据：
echo   - 群友信息
echo   - 群友昵称、生日、备注
echo.
echo ========================================
echo.

python scripts/clear_memory.py

echo.
pause
