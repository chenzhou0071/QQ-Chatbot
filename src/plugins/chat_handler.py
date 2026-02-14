"""聊天消息处理插件"""
from typing import Optional
from nonebot import on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message
from nonebot.rule import to_me

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import is_at_bot, remove_at, contains_keyword
from src.ai.client import get_ai_client
from src.memory.memory_manager import get_memory_manager
from src.utils.web_search import get_web_search_client
from src.utils.content_filter import get_content_filter
from src.dialogue.intent_analyzer import get_intent_analyzer
from src.dialogue.context_enhancer import get_context_enhancer
from src.dialogue.proactive_engine import get_proactive_engine

logger = get_logger("chat_handler")
config = get_config()
ai_client = get_ai_client()
memory_manager = get_memory_manager()
web_search_client = get_web_search_client()
content_filter = get_content_filter()

# 初始化意图分析器（如果启用）
intent_analyzer = None
if config.get("dialogue_intelligence.intent.enabled", False):
    try:
        intent_analyzer = get_intent_analyzer()
        logger.info("意图分析器已启用")
    except Exception as e:
        logger.error(f"意图分析器初始化失败: {e}")

# 初始化上下文增强器（如果启用）
context_enhancer = None
if config.get("dialogue_intelligence.state_machine.enabled", False):
    try:
        context_enhancer = get_context_enhancer()
        logger.info("上下文增强器已启用")
    except Exception as e:
        logger.error(f"上下文增强器初始化失败: {e}")

# 初始化主动对话引擎（如果启用）
proactive_engine = None
if config.get("dialogue_intelligence.proactive.enabled", False):
    try:
        proactive_engine = get_proactive_engine()
        logger.info("主动对话引擎已启用")
    except Exception as e:
        logger.error(f"主动对话引擎初始化失败: {e}")

# @触发回复
mention_matcher = on_message(rule=to_me(), priority=5, block=True)


@mention_matcher.handle()
async def handle_mention(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent) -> None:
    """处理@消息
    
    Args:
        bot: Bot实例
        event: 消息事件（群消息或私聊消息）
    """
    # 判断消息类型
    if isinstance(event, GroupMessageEvent):
        # 检查是否是目标群
        if str(event.group_id) != config.target_group:
            return
        chat_type = "group"
        sender_name: str = event.sender.card or event.sender.nickname
        sender_qq: str = str(event.user_id)
        
        # 更新主动对话引擎的消息时间
        if proactive_engine:
            proactive_engine.update_message_time(str(event.group_id))
    else:
        # 检查是否是管理员
        if str(event.user_id) != config.admin_qq:
            logger.debug(f"忽略非管理员私聊: {event.user_id}")
            return
        chat_type = "private"
        sender_name: str = event.sender.nickname
        sender_qq: str = str(event.user_id)
    
    # 获取消息内容
    message_text: str = str(event.get_message()).strip()
    message_text = remove_at(message_text)
    
    if not message_text:
        return
    
    logger.info(f"[{chat_type}] 收到@消息: {sender_name}: {message_text}")
    
    # 内容过滤检查
    if config.get("content_filter.enabled", True):
        should_ignore, reason = content_filter.should_ignore_message(message_text)
        if should_ignore:
            warning_msg = content_filter.get_warning_message()
            await mention_matcher.send(Message(warning_msg))
            logger.debug(f"[{chat_type}] 消息被过滤: {reason}")
            return
    
    # 意图分析（如果启用）
    intent_result = None
    topic_status = None
    if intent_analyzer:
        try:
            # 获取最近上下文
            recent_context = memory_manager.get_context_for_ai(chat_type)
            context_str = "\n".join([f"{m['role']}: {m['content']}" for m in recent_context[-3:]])
            
            intent_result = intent_analyzer.analyze(
                message=message_text,
                sender_id=sender_qq,
                context=context_str
            )
            
            logger.debug(f"[{chat_type}] 意图分析: {intent_result.type}, 话题: {intent_result.topic}")
            
            # 如果检测到讽刺，在日志中记录
            if intent_result.is_sarcastic:
                logger.info(f"[{chat_type}] 检测到讽刺语气 (置信度: {intent_result.confidence:.2f})")
            
            # 如果检测到反问，在日志中记录
            if intent_result.is_counter_question:
                logger.info(f"[{chat_type}] 检测到反问")
            
            # 获取话题状态（用于状态机）
            if intent_analyzer.topic_tracker:
                topic_status = {
                    "status": "maintaining",
                    "topic": intent_analyzer.topic_tracker.current_topic.to_dict() if intent_analyzer.topic_tracker.current_topic else None
                }
                
        except Exception as e:
            logger.error(f"[{chat_type}] 意图分析失败: {e}")
    
    # 检查是否需要联网搜索
    search_context: Optional[str] = None
    if web_search_client.should_search(message_text):
        logger.info(f"[{chat_type}] 触发联网搜索")
        search_context = web_search_client.search(message_text)
        if search_context:
            logger.debug(f"[{chat_type}] 搜索结果: {search_context[:100]}...")
    
    # 添加用户消息到记忆系统（三层存储）
    memory_manager.add_message(
        chat_type=chat_type,
        role="user",
        content=message_text,
        sender_id=sender_qq,
        sender_name=sender_name
    )
    
    # 获取上下文（包含相关记忆）
    context = memory_manager.get_context_for_ai(chat_type, message_text)
    
    # 使用上下文增强器（如果启用）
    if context_enhancer:
        try:
            context = context_enhancer.enrich(
                base_context=context,
                intent_result=intent_result,
                chat_type=chat_type,
                topic_status=topic_status
            )
            logger.debug(f"[{chat_type}] 上下文已增强")
        except Exception as e:
            logger.error(f"[{chat_type}] 上下文增强失败: {e}")
    
    # 如果有意图分析结果但没有上下文增强器，添加意图提示
    elif intent_result:
        intent_hint = _build_intent_hint(intent_result)
        if intent_hint:
            # 在上下文开头添加意图提示
            context.insert(0, {
                "role": "system",
                "content": intent_hint
            })
    
    reply: Optional[str] = ai_client.chat(
        context, 
        search_context=search_context, 
        chat_type=chat_type, 
        sender_qq=sender_qq
    )
    
    if reply:
        # 发送回复
        await mention_matcher.send(Message(reply))
        
        # 添加机器人回复到记忆系统
        memory_manager.add_message(
            chat_type=chat_type,
            role="assistant",
            content=reply
        )
        
        logger.info(f"[{chat_type}] AI回复: {reply}")
        
        # 如果回复包含问句，注册到反问检测器
        if intent_analyzer and _is_question(reply):
            try:
                current_topic = intent_analyzer.get_current_topic()
                intent_analyzer.register_bot_question(
                    question=reply,
                    context=[current_topic] if current_topic else []
                )
                logger.debug(f"[{chat_type}] 注册问题: {reply[:30]}...")
            except Exception as e:
                logger.error(f"[{chat_type}] 注册问题失败: {e}")


def _build_intent_hint(intent_result) -> Optional[str]:
    """构建意图提示
    
    Args:
        intent_result: 意图分析结果
        
    Returns:
        意图提示文本或None
    """
    hints = []
    
    if intent_result.is_counter_question:
        hints.append("【提示】用户在反问你之前提出的问题，请回答你自己的情况。")
    
    if intent_result.is_sarcastic:
        hints.append(f"【提示】用户可能在使用讽刺语气 (置信度: {intent_result.confidence:.0%})，请理解其真实意图并恰当回应。")
    
    if intent_result.topic:
        hints.append(f"【当前话题】{intent_result.topic}")
    
    return "\n".join(hints) if hints else None


def _is_question(text: str) -> bool:
    """判断文本是否包含问句
    
    Args:
        text: 文本内容
        
    Returns:
        是否包含问句
    """
    question_marks = ['?', '？', '吗', '呢', '吧']
    question_words = ['什么', '怎么', '为什么', '哪', '谁', '几', '多少', '如何']
    
    return (any(mark in text for mark in question_marks) or
            any(word in text for word in question_words))
