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

# 记录最近回复的用户（用于连续对话检测）
recent_replies = {}  # {user_id: timestamp}

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
    
    # 获取发送者QQ
    sender_qq: str = str(event.user_id)
    current_time: float = time.time()
    
    # 检查是否是连续对话
    is_continuous = False
    continuous_window: int = config.get("smart_reply.continuous_window", 30)
    
    # 获取配置的名字和昵称
    personality = config.get("personality", {})
    bot_name: str = personality.get("name", "沉舟")
    bot_nickname: str = personality.get("nickname", "舟舟")
    
    # 检查消息是否在和bot对话
    # 1. 包含bot名字或昵称
    has_bot_name = bot_name in message_text or bot_nickname in message_text
    
    # 2. 疑问句特征
    question_marks = ['?', '？', '吗', '呢', '吧', '啊']
    question_words = ['什么', '怎么', '为什么', '哪', '谁', '几', '多少', '如何', '干嘛', '干什么']
    question_patterns = ['你在', '你是', '你会', '你有', '你觉得', '你想', '你知道']
    
    is_question = (
        any(mark in message_text for mark in question_marks) or
        any(word in message_text for word in question_words) or
        any(pattern in message_text for pattern in question_patterns)
    )
    
    # 只要满足其中一个条件就认为是在和bot对话
    is_talking_to_bot = has_bot_name or is_question
    
    # 只有在和bot对话时才检测连续对话
    if is_talking_to_bot:
        # 检查是否刚被名字触发过
        from src.triggers.name import recent_name_triggers
        if sender_qq in recent_name_triggers:
            time_since_name_trigger = current_time - recent_name_triggers[sender_qq]
            if time_since_name_trigger < continuous_window:
                is_continuous = True
                logger.info(f"[群] 检测到连续对话（名字触发后 {time_since_name_trigger:.1f}秒）")
        
        # 检查是否刚被智能触发回复过
        if not is_continuous and sender_qq in recent_replies:
            time_since_reply = current_time - recent_replies[sender_qq]
            if time_since_reply < continuous_window:
                is_continuous = True
                logger.info(f"[群] 检测到连续对话（上次回复后 {time_since_reply:.1f}秒）")
    
    # 如果不是连续对话，检查触发概率
    if not is_continuous:
        trigger_rate: float = config.get("smart_reply.trigger_rate", 0.5)
        if random.random() > trigger_rate:
            return
        
        # 检查最小间隔
        min_interval: int = config.get("smart_reply.min_interval", 30)
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
    
    # 如果是连续对话，跳过AI判断直接回复
    if is_continuous:
        logger.info("[群] 连续对话，直接回复")
    else:
        # 获取最近的对话历史作为上下文
        recent_messages = memory_manager.get_recent_messages("group", limit=5)
        context_text = ""
        if recent_messages:
            context_text = "\n最近的对话:\n"
            for msg in recent_messages[-5:]:  # 最多5条
                role = "Bot" if msg.get("role") == "assistant" else msg.get("sender_name", "用户")
                content = msg.get("content", "")
                context_text += f"{role}: {content}\n"
        
        # 调用AI判断是否需要回复（带上下文）
        prompt = f"""判断Bot是否需要回复这条群消息。

你是一个温柔内敛的女孩（名叫{bot_name}，昵称{bot_nickname}），偶尔会参与群聊。

{context_text}
当前消息: {message_text}

判断标准：
1. 如果消息是在和你对话、询问你、或期待你的回应 → 回复 "YES"
2. 如果消息提到了你之前说过的话题 → 回复 "YES"
3. 如果有人对你做亲密动作（摸头、抱抱、亲亲、戳戳等）→ 回复 "YES"
4. 如果有人在回应你刚才说的话 → 回复 "YES"
5. 如果群成员在聊一个有趣的话题，你也想说两句 → 可以回复 "YES"
6. 如果消息很简短（如"哈哈"、"好的"、"嗯嗯"）且不是在回应你 → 回复 "NO"
7. 如果是很私密的两人对话，不要打扰 → 回复 "NO"
8. 如果话题你不太懂或不感兴趣，保持安静 → 回复 "NO"

记住：你性格温和内敛，不要对所有消息都回复，但可以适当参与群聊。

只回复 "YES" 或 "NO"，不要有其他内容。
"""
        
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
        
        # 记录回复时间（用于连续对话检测）
        recent_replies[sender_qq] = time.time()
        logger.debug(f"[群] 记录智能回复: {sender_qq}")
