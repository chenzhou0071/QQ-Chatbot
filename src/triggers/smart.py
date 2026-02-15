"""智能判断触发器"""
import time
import random
from typing import Optional
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at, contains_keyword, has_bilibili_link
from src.ai.client import get_ai_client
from src.ai.prompts import get_smart_reply_prompt
from src.memory.memory_manager import get_memory_manager
from src.utils.web_search import get_web_search_client
from src.utils.content_filter import get_content_filter

logger = get_logger("smart")
config = get_config()
ai_client = get_ai_client()
memory_manager = get_memory_manager()
web_search_client = get_web_search_client()
content_filter = get_content_filter()

# 记录上次触发时间
last_trigger_time: float = 0.0

# 智能判断触发器（优先级最低）
smart_matcher = on_message(priority=15, block=False)


@smart_matcher.handle()
async def handle_smart_reply(bot: Bot, event: GroupMessageEvent) -> None:
    """智能判断是否需要回复
    
    Args:
        bot: Bot实例
        event: 群消息事件
    """
    global last_trigger_time
    
    # 检查功能是否开启
    if not config.get("features.smart_reply", True):
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        return
    
    # 获取消息内容 - 使用 raw_message
    message_text = event.raw_message.strip()
    
    # 如果是@消息或包含关键词，跳过
    if is_at_bot(message_text, config.bot_qq):
        return
    
    if contains_keyword(message_text, config.keywords):
        return
    
    # 检查是否提到了名字（避免和名字触发器重复）
    personality = config.get("personality", {})
    name: str = personality.get("name", "沉舟")
    nickname: str = personality.get("nickname", "舟舟")
    if name in message_text or nickname in message_text:
        return
    
    # 如果消息中包含B站链接，跳过（已被B站解析插件处理）
    if has_bilibili_link(message_text):
        logger.debug("[群] 检测到B站链接，跳过智能触发")
        return
    
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    # 检查触发概率
    trigger_rate: float = config.get("smart_reply.trigger_rate", 0.5)
    if random.random() > trigger_rate:
        return
    
    # 检查最小间隔
    min_interval: int = config.get("smart_reply.min_interval", 30)
    current_time: float = time.time()
    if current_time - last_trigger_time < min_interval:
        logger.debug(f"[群] 距离上次触发不足{min_interval}秒，跳过")
        return
    
    logger.debug(f"[群] 智能判断: {message_text}")
    
    # 内容过滤检查
    if config.get("content_filter.enabled", True):
        should_ignore, reason = content_filter.should_ignore_message(message_text)
        if should_ignore:
            # 智能触发检测到敏感词，直接忽略不回复
            logger.debug(f"[群] 消息被过滤: {reason}")
            return
    
    # 调用AI判断是否需要回复
    prompt: str = get_smart_reply_prompt(message_text)
    decision: Optional[str] = ai_client.simple_chat(prompt)
    
    if not decision or "YES" not in decision.upper():
        logger.debug("[群] AI判断不需要回复")
        return
    
    logger.info("[群] AI判断需要回复")
    
    # 更新触发时间
    last_trigger_time = current_time
    
    # 检查是否需要联网搜索
    search_context: Optional[str] = None
    if web_search_client.should_search(message_text):
        logger.info("[群] 触发联网搜索")
        search_context = web_search_client.search(message_text)
        if search_context:
            logger.debug(f"[群] 搜索结果: {search_context[:100]}...")
    
    # 获取发送者信息
    sender_name: str = event.sender.card or event.sender.nickname
    sender_qq: str = str(event.user_id)
    
    # 添加用户消息到记忆系统
    memory_manager.add_message(
        chat_type="group",
        role="user",
        content=message_text,
        sender_id=sender_qq,
        sender_name=sender_name
    )
    
    # 获取上下文（包含相关记忆）
    context = memory_manager.get_context_for_ai("group", message_text)
    reply: Optional[str] = ai_client.chat(
        context, 
        search_context=search_context, 
        chat_type="group", 
        sender_qq=sender_qq
    )
    
    if reply:
        await smart_matcher.send(Message(reply))
        memory_manager.add_message("group", "assistant", reply)
        logger.info(f"[群] 智能回复: {reply}")
