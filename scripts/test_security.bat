@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   安全防护测试
echo ========================================
echo.

cd /d "%~dp0.."

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python scripts\test_security.py
) else (
    echo 错误: 未找到虚拟环境
    echo 请先运行 install.bat
    pause
)
