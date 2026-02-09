"""智能判断触发器"""
import re
import time
import random
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at, contains_keyword
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

# B站链接检测正则（与bilibili.py保持一致）
REG_BV = re.compile(r'BV[0-9A-Za-z]{10}')
REG_AV = re.compile(r'av(\d+)', re.IGNORECASE)
REG_B23 = re.compile(r'(b23\.tv|bili2233\.cn)')
REG_SS = re.compile(r'ss(\d+)', re.IGNORECASE)
REG_EP = re.compile(r'ep(\d+)', re.IGNORECASE)
REG_MD = re.compile(r'md(\d+)', re.IGNORECASE)

def has_bilibili_link(message: str) -> bool:
    """检测消息中是否包含B站链接（快速预检查+正则匹配）"""
    # 快速预检查：只有包含B站关键词时才进行正则匹配
    if not any(keyword in message for keyword in ['bilibili', 'b23.tv', 'BV', 'av', 'ss', 'ep', 'md', '哔哩哔哩']):
        return False
    
    return bool(
        REG_BV.search(message) or 
        REG_AV.search(message) or 
        REG_B23.search(message) or 
        REG_SS.search(message) or 
        REG_EP.search(message) or 
        REG_MD.search(message)
    )

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
    
    # 检查是否提到了名字（避免和名字触发器重复）
    personality = config.get("personality", {})
    name = personality.get("name", "沉舟")
    nickname = personality.get("nickname", "舟舟")
    if name in message_text or nickname in message_text:
        return
    
    # 如果消息中包含B站链接，跳过（已被B站解析插件处理）
    if has_bilibili_link(message_text):
        return
    
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    # 检查触发概率
    trigger_rate = config.get("smart_reply.trigger_rate", 0.5)
    if random.random() > trigger_rate:
        return
    
    # 检查最小间隔
    min_interval = config.get("smart_reply.min_interval", 30)
    current_time = time.time()
    if current_time - last_trigger_time < min_interval:
        return
    
    logger.info(f"[群] 智能判断: {message_text}")
    
    # 内容过滤检查
    if config.get("content_filter.enabled", True):
        should_ignore, reason = content_filter.should_ignore_message(message_text)
        if should_ignore:
            # 智能触发检测到敏感词，直接忽略不回复
            logger.warning(f"[群] 消息被过滤: {reason}")
            return
    
    # 调用AI判断是否需要回复
    prompt = get_smart_reply_prompt(message_text)
    decision = ai_client.simple_chat(prompt)
    
    if not decision or "YES" not in decision.upper():
        logger.info(f"[群] AI判断不需要回复")
        return
    
    logger.info(f"[群] AI判断需要回复")
    
    # 更新触发时间
    last_trigger_time = current_time
    
    # 检查是否需要联网搜索
    search_context = None
    if web_search_client.should_search(message_text):
        logger.info(f"[群] 触发联网搜索")
        search_context = web_search_client.search(message_text)
        if search_context:
            logger.info(f"[群] 搜索结果: {search_context[:100]}...")
    
    # 获取发送者信息
    sender_name = event.sender.card or event.sender.nickname
    sender_qq = str(event.user_id)
    
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
        await smart_matcher.send(Message(reply))
        memory_manager.add_message("group", "assistant", reply)
        logger.info(f"[群] 智能回复: {reply}")
