"""聊天消息处理插件"""
from nonebot import on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message
from nonebot.rule import to_me

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at, contains_keyword
from src.ai.client import get_ai_client
from src.memory.context import get_context_manager

logger = get_logger("chat_handler")
config = get_config()
ai_client = get_ai_client()
context_manager = get_context_manager()

# @触发回复
mention_matcher = on_message(rule=to_me(), priority=5, block=True)

@mention_matcher.handle()
async def handle_mention(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent):
    """处理@消息"""
    # 判断消息类型
    if isinstance(event, GroupMessageEvent):
        # 检查是否是目标群
        if str(event.group_id) != config.target_group:
            return
        chat_type = "group"
        sender_name = event.sender.card or event.sender.nickname
    else:
        # 检查是否是管理员
        if str(event.user_id) != config.admin_qq:
            logger.info(f"忽略非管理员私聊: {event.user_id}")
            return
        chat_type = "private"
        sender_name = event.sender.nickname
    
    # 获取消息内容
    message_text = str(event.get_message()).strip()
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    logger.info(f"[{chat_type}] 收到@消息: {sender_name}: {message_text}")
    
    # 添加用户消息到上下文
    context_manager.add_message(chat_type, "user", message_text, sender_name)
    
    # 获取上下文并调用AI
    context = context_manager.format_for_ai(chat_type)
    reply = ai_client.chat(context)
    
    if reply:
        # 发送回复
        await mention_matcher.send(Message(reply))
        
        # 添加机器人回复到上下文
        context_manager.add_message(chat_type, "assistant", reply)
        
        logger.info(f"[{chat_type}] AI回复: {reply}")
