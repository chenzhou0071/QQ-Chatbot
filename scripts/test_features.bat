@echo off
chcp 65001 >nul
echo ========================================
echo 对话智能功能测试
echo ========================================
echo.

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo 运行功能测试...
echo ========================================
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd())); print('测试 1/4: 意图分析器...'); from src.dialogue.intent_analyzer import get_intent_analyzer; analyzer = get_intent_analyzer(); print('  ✓ 意图分析器初始化成功'); print('\n测试 2/4: 对话状态机...'); from src.dialogue.state_machine import get_state_machine; sm = get_state_machine(); print('  ✓ 对话状态机初始化成功'); print('\n测试 3/4: 上下文增强器...'); from src.dialogue.context_enhancer import get_context_enhancer; ce = get_context_enhancer(); print('  ✓ 上下文增强器初始化成功'); print('\n测试 4/4: 主动对话引擎...'); from src.dialogue.proactive_engine import get_proactive_engine; pe = get_proactive_engine(); print('  ✓ 主动对话引擎初始化成功'); print('\n========================================'); print('所有功能测试通过！'); print('========================================')"

echo.
pause
