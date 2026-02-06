"""智能判断触发器"""
import time
import random
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at, contains_keyword
from src.ai.client import get_ai_client
from src.ai.prompts import get_smart_reply_prompt
from src.memory.context import get_context_manager

logger = get_logger("smart")
config = get_config()
ai_client = get_ai_client()
context_manager = get_context_manager()

# 记录上次触发时间
last_trigger_time = 0

# 智能判断触发器（优先级最低）
smart_matcher = on_message(priority=15, block=False)

@smart_matcher.handle()
async def handle_smart_reply(bot: Bot, event: GroupMessageEvent):
    """智能判断是否需要回复"""
    global last_trigger_time
    
    # 检查功能是否开启
    if not config.get("features.smart_reply", True):
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        return
    
    # 获取消息内容
    message_text = str(event.get_message()).strip()
    
    # 如果是@消息或包含关键词，跳过
    if is_at_bot(message_text, config.bot_qq):
        return
    
    if contains_keyword(message_text, config.keywords):
        return
    
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    # 检查触发概率
    trigger_rate = config.get("smart_reply.trigger_rate", 0.3)
    if random.random() > trigger_rate:
        return
    
    # 检查最小间隔
    min_interval = config.get("smart_reply.min_interval", 60)
    current_time = time.time()
    if current_time - last_trigger_time < min_interval:
        return
    
    logger.info(f"[群] 智能判断: {message_text}")
    
    # 调用AI判断是否需要回复
    prompt = get_smart_reply_prompt(message_text)
    decision = ai_client.simple_chat(prompt)
    
    if not decision or "YES" not in decision.upper():
        logger.info(f"[群] AI判断不需要回复")
        return
    
    logger.info(f"[群] AI判断需要回复")
    
    # 更新触发时间
    last_trigger_time = current_time
    
    # 获取发送者信息
    sender_name = event.sender.card or event.sender.nickname
    
    # 添加用户消息到上下文
    context_manager.add_message("group", "user", message_text, sender_name)
    
    # 获取上下文并调用AI
    context = context_manager.format_for_ai("group")
    reply = ai_client.chat(context)
    
    if reply:
        await smart_matcher.send(Message(reply))
        context_manager.add_message("group", "assistant", reply)
        logger.info(f"[群] 智能回复: {reply}")
