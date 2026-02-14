@echo off
chcp 65001 >nul
:menu
cls
echo ========================================
echo 对话智能功能开关
echo ========================================
echo.
echo 当前配置文件: config\config.yaml
echo.
echo 请选择操作:
echo.
echo 1. 启用所有对话智能功能
echo 2. 禁用所有对话智能功能
echo 3. 仅启用意图分析
echo 4. 仅启用对话状态机
echo 5. 仅启用主动对话
echo 6. 查看当前配置
echo 0. 退出
echo.
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto enable_all
if "%choice%"=="2" goto disable_all
if "%choice%"=="3" goto enable_intent
if "%choice%"=="4" goto enable_state
if "%choice%"=="5" goto enable_proactive
if "%choice%"=="6" goto show_config
if "%choice%"=="0" exit /b 0
goto menu

:enable_all
echo.
echo 正在启用所有功能...
call venv\Scripts\activate.bat
python -c "
import yaml
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['dialogue_intelligence']['intent']['enabled'] = True
config['dialogue_intelligence']['state_machine']['enabled'] = True
config['dialogue_intelligence']['proactive']['enabled'] = True
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
print('✓ 已启用所有对话智能功能')
"
pause
goto menu

:disable_all
echo.
echo 正在禁用所有功能...
call venv\Scripts\activate.bat
python -c "
import yaml
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['dialogue_intelligence']['intent']['enabled'] = False
config['dialogue_intelligence']['state_machine']['enabled'] = False
config['dialogue_intelligence']['proactive']['enabled'] = False
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
print('✓ 已禁用所有对话智能功能')
"
pause
goto menu

:enable_intent
echo.
echo 正在启用意图分析...
call venv\Scripts\activate.bat
python -c "
import yaml
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['dialogue_intelligence']['intent']['enabled'] = True
config['dialogue_intelligence']['state_machine']['enabled'] = False
config['dialogue_intelligence']['proactive']['enabled'] = False
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
print('✓ 已启用意图分析')
"
pause
goto menu

:enable_state
echo.
echo 正在启用对话状态机...
call venv\Scripts\activate.bat
python -c "
import yaml
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['dialogue_intelligence']['intent']['enabled'] = False
config['dialogue_intelligence']['state_machine']['enabled'] = True
config['dialogue_intelligence']['proactive']['enabled'] = False
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
print('✓ 已启用对话状态机')
"
pause
goto menu

:enable_proactive
echo.
echo 正在启用主动对话...
call venv\Scripts\activate.bat
python -c "
import yaml
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config['dialogue_intelligence']['intent']['enabled'] = False
config['dialogue_intelligence']['state_machine']['enabled'] = False
config['dialogue_intelligence']['proactive']['enabled'] = True
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
print('✓ 已启用主动对话')
"
pause
goto menu

:show_config
echo.
call check_config.bat
goto menu
