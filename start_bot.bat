@echo off
chcp 65001 >nul
echo ========================================
echo QQ聊天机器人启动
echo ========================================
echo.

echo [1/4] 激活虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

echo.
echo [2/4] 检查依赖...
python -c "import chromadb" 2>nul
if errorlevel 1 (
    echo 正在安装 chromadb...
    pip install chromadb>=0.4.22 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [3/4] 创建数据目录...
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\chroma" mkdir data\chroma

echo.
echo [4/4] 启动机器人...
echo ========================================
python src/bot.py

