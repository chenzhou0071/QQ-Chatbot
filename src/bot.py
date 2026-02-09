"""NoneBot2 机器人入口"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 配置日志过滤器，隐藏 IgnoredException 的详细堆栈
class IgnoreExceptionFilter(logging.Filter):
    def filter(self, record):
        # 如果是 IgnoredException 的错误日志，不显示
        if record.levelno == logging.ERROR:
            if 'IgnoredException' in str(record.msg) or 'IgnoredException' in str(record.exc_info or ''):
                return False
        return True

# 初始化 NoneBot
nonebot.init()

# 应用日志过滤器到所有处理器
for handler in logging.root.handlers:
    handler.addFilter(IgnoreExceptionFilter())

# 同时应用到 nonebot 的日志记录器
nonebot_logger = logging.getLogger("nonebot")
for handler in nonebot_logger.handlers:
    handler.addFilter(IgnoreExceptionFilter())

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
