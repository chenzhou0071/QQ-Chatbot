@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo.
echo ========================================
echo Bot 状态诊断
echo ========================================
echo.

echo [1] 检查进程状态...
echo.
powershell -Command "Get-Process | Where-Object {$_.ProcessName -like '*python*'} | Select-Object ProcessName, Id, StartTime, @{Name='Memory(MB)';Expression={[math]::Round($_.WorkingSet64/1MB,2)}}"
echo.

echo [2] 检查最新日志（最后20行）...
echo.
powershell -Command "Get-Content data/logs/bot-2026-02-14.log -Tail 20 -Encoding UTF8"
echo.

echo [3] 检查错误日志...
echo.
if exist data\logs\error-2026-02-14.log (
    powershell -Command "Get-Content data/logs/error-2026-02-14.log -Tail 10 -Encoding UTF8"
) else (
    echo 今天没有错误日志
)
echo.

echo [4] 检查配置...
echo.
python -c "from src.utils.config import get_config; c=get_config(); print(f'Bot QQ: {c.bot_qq}'); print(f'Target Group: {c.target_group}'); print(f'AI Provider: {c.ai_provider}')"
echo.

echo [5] 检查数据库...
echo.
python -c "from src.memory.database import get_database; db=get_database(); import sqlite3; conn=sqlite3.connect('data/bot.db'); cursor=conn.cursor(); cursor.execute('SELECT COUNT(*) FROM group_member'); print(f'群友数: {cursor.fetchone()[0]}'); cursor.execute('SELECT COUNT(*) FROM chat_log'); print(f'聊天记录: {cursor.fetchone()[0]}'); cursor.execute('SELECT COUNT(*) FROM conversation_context'); print(f'对话上下文: {cursor.fetchone()[0]}'); conn.close()"
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
pause
