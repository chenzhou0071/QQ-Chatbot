@echo off
chcp 65001 >nul
echo ========================================
echo 配置文件检查
echo ========================================
echo.

call venv\Scripts\activate.bat

python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); from src.utils.config import get_config; print('正在检查配置...\n'); config = get_config(); print('【基本配置】'); print(f'  机器人QQ: {config.bot_qq}'); print(f'  管理员QQ: {config.admin_qq}'); print(f'  目标群号: {config.target_group}'); print('\n【对话智能配置】'); intent_enabled = config.get(\"dialogue_intelligence.intent.enabled\", False); state_enabled = config.get(\"dialogue_intelligence.state_machine.enabled\", False); proactive_enabled = config.get(\"dialogue_intelligence.proactive.enabled\", False); print(f'  意图分析: {\"✓ 已启用\" if intent_enabled else \"✗ 未启用\"}'); print(f'  对话状态机: {\"✓ 已启用\" if state_enabled else \"✗ 未启用\"}'); print(f'  主动对话: {\"✓ 已启用\" if proactive_enabled else \"✗ 未启用\"}'); print('\n【AI配置】'); ai_provider = config.get_env(\"AI_PROVIDER\", \"deepseek\"); print(f'  AI提供商: {ai_provider}'); print(f'  最大重试: {config.get(\"ai.max_retries\", 3)}'); print(f'  温度参数: {config.get(\"ai.temperature\", 0.7)}'); print('\n【记忆配置】'); vector_enabled = config.get(\"memory.vector_db.enabled\", False); print(f'  向量数据库: {\"✓ 已启用\" if vector_enabled else \"✗ 未启用\"}'); print('\n========================================'); print('配置检查完成'); print('========================================')"

echo.
pause
