@echo off
chcp 65001 >nul
echo ========================================
echo 数据清理工具
echo ========================================
echo.
echo 警告：此操作将删除以下数据：
echo   - 聊天记录数据库 (data\bot.db)
echo   - 向量数据库 (data\chroma)
echo   - 日志文件 (data\logs)
echo.
echo 配置文件和代码不会被删除
echo.
set /p confirm="确认清理？(y/N): "

if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo 正在清理数据...

if exist "data\bot.db" (
    del /f /q "data\bot.db"
    echo ✓ 已删除数据库文件
)

if exist "data\chroma" (
    rmdir /s /q "data\chroma"
    mkdir "data\chroma"
    echo ✓ 已清理向量数据库
)

if exist "data\logs" (
    del /f /q "data\logs\*.log"
    echo ✓ 已清理日志文件
)

echo.
echo ========================================
echo 数据清理完成
echo ========================================
echo.
pause
