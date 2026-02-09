@echo off
chcp 65001 >nul
echo ========================================
echo QQ 聊天机器人 - 一键启动
echo ========================================
echo.

echo [1/2] 启动机器人...
start "QQ机器人" cmd /k "cd /d %~dp0 && start_bot.bat"
timeout /t 3 /nobreak >nul

echo [2/2] 启动 NapCat...
start "NapCat" cmd /k "cd /d %~dp0napcat && napcat.bat"

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 机器人窗口：QQ机器人
echo NapCat窗口：NapCat
echo.
echo 等待 NapCat 启动后：
echo 1. 访问 http://127.0.0.1:6099/webui
echo 2. 使用 Token 登录
echo 3. 扫码登录 QQ（3966049171）
echo 4. 在群里测试：@沉舟 你好
echo.
pause
