"""名字触发器 - 当有人提到舟舟/沉舟时主动回复"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at
from src.ai.client import get_ai_client
from src.memory.context import get_context_manager
from src.utils.web_search import get_web_search_client

logger = get_logger("name")
config = get_config()
ai_client = get_ai_client()
context_manager = get_context_manager()
web_search_client = get_web_search_client()

# 名字触发器（优先级高于关键词，低于@触发）
name_matcher = on_message(priority=8, block=False)

@name_matcher.handle()
async def handle_name_mention(bot: Bot, event: GroupMessageEvent):
    """处理名字提及"""
    # 检查功能是否开启
    if not config.get("features.name_reply", True):
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
    
    # 获取配置的名字和昵称
    personality = config.get("personality", {})
    name = personality.get("name", "沉舟")
    nickname = personality.get("nickname", "舟舟")
    
    # 检查是否提到了名字或昵称
    if name not in message_text and nickname not in message_text:
        return
    
    logger.info(f"[群] 名字触发: {message_text}")
    
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
    
    # 添加用户消息到上下文
    context_manager.add_message("group", "user", message_text, sender_name)
    
    # 获取上下文并调用AI
    context = context_manager.format_for_ai("group")
    reply = ai_client.chat(context, search_context=search_context, chat_type="group", sender_qq=sender_qq)
    
    if reply:
        await name_matcher.send(Message(reply))
        context_manager.add_message("group", "assistant", reply)
        logger.info(f"[群] 名字回复: {reply}")
