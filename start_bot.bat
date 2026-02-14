@echo off
chcp 65001 >nul
echo ========================================
echo QQ聊天机器人启动
echo ========================================
echo.

echo [1/5] 激活虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

echo.
echo [2/5] 检查配置文件...
if not exist "config\config.yaml" (
    echo ❌ 配置文件不存在，正在从示例创建...
    copy config\config.yaml.example config\config.yaml
    echo ✓ 已创建配置文件，请编辑 config\config.yaml 后重新启动
    pause
    exit /b 1
)

if not exist "config\.env" (
    echo ❌ 环境变量文件不存在，正在从示例创建...
    copy config\.env.example config\.env
    echo ✓ 已创建环境变量文件，请编辑 config\.env 后重新启动
    pause
    exit /b 1
)

echo.
echo [3/5] 检查依赖...
python -c "import chromadb" 2>nul
if errorlevel 1 (
    echo 正在安装 chromadb...
    pip install chromadb>=0.4.22 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import jieba" 2>nul
if errorlevel 1 (
    echo 正在安装 jieba...
    pip install jieba>=0.42.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo [4/5] 创建数据目录...
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\chroma" mkdir data\chroma

echo.
echo [5/5] 启动机器人...
echo ========================================
echo.
echo 对话智能功能已启用:
echo   ✓ 意图分析 (反问检测、讽刺识别、话题追踪)
echo   ✓ 对话状态机 (智能状态转换)
echo   ✓ 主动对话 (冷场检测、自动破冰)
echo.
echo 按 Ctrl+C 停止机器人
echo ========================================
echo.
python src/bot.py


