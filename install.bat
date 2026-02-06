@echo off
chcp 65001 >nul
echo ================================
echo QQ聊天机器人 - 安装脚本
echo ================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建完成
) else (
    echo 虚拟环境已存在
)
echo.

echo [3/4] 安装依赖包...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.

echo [4/4] 初始化配置文件...
if not exist config\config.yaml (
    copy config\config.yaml.example config\config.yaml
    echo 已创建 config.yaml，请编辑配置
)
if not exist config\.env (
    copy config\.env.example config\.env
    echo 已创建 .env，请配置API密钥
)
echo.

echo ================================
echo 安装完成！
echo ================================
echo.
echo 下一步操作：
echo 1. 编辑 config\config.yaml 配置机器人信息
echo 2. 编辑 config\.env 配置API密钥
echo 3. 运行 run.bat 启动机器人
echo.
pause
