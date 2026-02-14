"""主动对话插件"""
import asyncio
from nonebot import require, get_bot
from nonebot.adapters.onebot.v11 import Bot, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.dialogue.proactive_engine import get_proactive_engine

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

logger = get_logger("proactive_chat")
config = get_config()

# 初始化主动对话引擎（如果启用）
proactive_engine = None
if config.get("dialogue_intelligence.proactive.enabled", False):
    try:
        proactive_engine = get_proactive_engine()
        logger.info("主动对话引擎已启用")
    except Exception as e:
        logger.error(f"主动对话引擎初始化失败: {e}")


@scheduler.scheduled_job("interval", seconds=60, id="proactive_check")
async def check_proactive():
    """定期检查是否需要主动发言"""
    if not proactive_engine:
        return
    
    try:
        # 获取bot实例
        bot = get_bot()
        
        # 获取目标群
        target_group = config.target_group
        
        if not target_group:
            return
        
        # 检查并生成主动消息
        message = proactive_engine.check_and_generate(
            group_id=target_group,
            mood="calm"  # 可以后续接入氛围分析
        )
        
        if message:
            # 发送消息
            await bot.send_group_msg(
                group_id=int(target_group),
                message=Message(message)
            )
            logger.info(f"发送主动消息: {message}")
            
    except Exception as e:
        logger.error(f"主动对话检查失败: {e}")


logger.info("主动对话插件已加载")
