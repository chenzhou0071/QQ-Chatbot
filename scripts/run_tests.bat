@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   运行单元测试
echo ========================================
echo.

cd /d "%~dp0.."

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    
    echo 运行所有测试...
    echo.
    pytest tests/ -v --tb=short
    
    echo.
    echo ========================================
    echo   测试完成
    echo ========================================
    pause
) else (
    echo 错误: 未找到虚拟环境
    echo 请先运行 install.bat
    pause
)
