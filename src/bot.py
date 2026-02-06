"""NoneBot2 机器人入口"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 配置 WebSocket 服务端（监听 3001 端口）
@driver.on_startup
async def _():
    from nonebot.log import logger
    logger.info("OneBot V11 WebSocket 服务端已启动，监听端口: 3001")
    logger.info("等待 NapCat 连接到 ws://127.0.0.1:8080/onebot/v11/ws")

# 加载插件
nonebot.load_plugins("src/plugins")
nonebot.load_plugins("src/triggers")

if __name__ == "__main__":
    nonebot.run()
