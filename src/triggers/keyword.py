"""关键词触发器"""
from typing import Optional
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import contains_keyword, is_at_bot, remove_at
from src.ai.client import get_ai_client
from src.memory.context import get_context_manager

logger = get_logger("keyword")
config = get_config()
ai_client = get_ai_client()
context_manager = get_context_manager()

# 关键词触发器（优先级低于@触发）
keyword_matcher = on_message(priority=10, block=False)

@keyword_matcher.handle()
async def handle_keyword(bot: Bot, event: GroupMessageEvent):
    """处理关键词触发"""
    # 检查功能是否开启
    if not config.get("features.keyword_reply", True):
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        return
    
    # 获取消息内容
    message_text = str(event.get_message()).strip()
    
    # 如果是@消息，跳过（已被mention_matcher处理）
    if is_at_bot(message_text, config.bot_qq):
        return
    
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    # 检查是否包含关键词
    keywords = config.keywords
    if not contains_keyword(message_text, keywords):
        return
    
    logger.info(f"[群] 关键词触发: {message_text}")
    
    # 获取发送者信息
    sender_name = event.sender.card or event.sender.nickname
    
    # 添加用户消息到上下文
    context_manager.add_message("group", "user", message_text, sender_name)
    
    # 获取上下文并调用AI
    context = context_manager.format_for_ai("group")
    reply = ai_client.chat(context)
    
    if reply:
        await keyword_matcher.send(Message(reply))
        context_manager.add_message("group", "assistant", reply)
        logger.info(f"[群] 关键词回复: {reply}")
