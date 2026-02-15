"""关键词触发器"""
from typing import Optional
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.exception import IgnoredException

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import contains_keyword, is_at_bot, remove_at
from src.ai.client import get_ai_client
from src.memory.memory_manager import get_memory_manager
from src.utils.web_search import get_web_search_client
from src.utils.content_filter import get_content_filter

logger = get_logger("keyword")
config = get_config()
ai_client = get_ai_client()
memory_manager = get_memory_manager()
web_search_client = get_web_search_client()
content_filter = get_content_filter()

# 关键词触发器（优先级低于@触发）
# block=False 允许智能触发器继续处理
keyword_matcher = on_message(priority=10, block=False)

@keyword_matcher.handle()
async def handle_keyword(bot: Bot, event: GroupMessageEvent):
    """处理关键词触发"""
    logger.debug(f"[群] 关键词触发器被调用")
    
    # 检查功能是否开启
    if not config.get("features.keyword_reply", True):
        logger.debug(f"[群] 关键词回复功能未开启")
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        logger.debug(f"[群] 非目标群: {event.group_id}")
        return
    
    # 获取消息内容 - 使用 raw_message
    message_text = event.raw_message.strip()
    logger.debug(f"[群] 原始消息: '{message_text}'")
    
    # 如果是@消息，跳过（已被mention_matcher处理）
    if is_at_bot(message_text, config.bot_qq):
        logger.debug(f"[群] 检测到@消息，跳过关键词触发")
        return
    
    message_text = remove_at(message_text)
    logger.debug(f"[群] 处理后消息: '{message_text}'")
    
    if not message_text:
        logger.debug(f"[群] 消息为空")
        return
    
    # 检查是否包含关键词
    keywords = config.keywords
    logger.debug(f"[群] 检查关键词: {keywords}")
    if not contains_keyword(message_text, keywords):
        logger.debug(f"[群] 消息中未包含关键词")
        return
    
    # 找到匹配，开始处理
    logger.info(f"[群] 关键词触发，开始处理: {message_text}")
    
    # 内容过滤检查
    if config.get("content_filter.enabled", True):
        should_ignore, reason = content_filter.should_ignore_message(message_text)
        if should_ignore:
            warning_msg = content_filter.get_warning_message()
            await keyword_matcher.send(Message(warning_msg))
            logger.warning(f"[群] 消息被过滤: {reason}")
            # 阻止后续触发器
            raise IgnoredException("消息被内容过滤器拦截")
    
    # 获取发送者信息
    sender_name = event.sender.card or event.sender.nickname
    sender_qq = str(event.user_id)
    
    # 检查是否是固定回复关键词
    fixed_replies = config.get("keyword_fixed_replies", {})
    reply = None
    matched_keyword = None
    
    for keyword, fixed_reply in fixed_replies.items():
        if keyword in message_text:
            reply = fixed_reply
            matched_keyword = keyword
            logger.info(f"[群] 固定回复触发: {keyword}")
            break
    
    # 如果不是固定回复，使用AI生成
    if not reply:
        # 检查是否需要联网搜索
        search_context = None
        if web_search_client.should_search(message_text):
            logger.info(f"[群] 触发联网搜索")
            search_context = web_search_client.search(message_text)
            if search_context:
                logger.info(f"[群] 搜索结果: {search_context[:100]}...")
        
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
        reply = ai_client.chat(context, search_context=search_context, chat_type="group", sender_qq=sender_qq)
    
    if reply:
        await keyword_matcher.send(Message(reply))
        
        # 只有AI生成的回复才保存到记忆系统
        if not matched_keyword:
            memory_manager.add_message("group", "assistant", reply)
        
        logger.info(f"[群] 关键词回复: {reply}")
        # 阻止后续触发器
        raise IgnoredException("关键词触发器已处理")
