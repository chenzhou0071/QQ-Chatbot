"""辅助函数"""
import random
from typing import List

def random_choice(items: List[str]) -> str:
    """随机选择一个元素"""
    if not items:
        return ""
    return random.choice(items)

def is_at_bot(message: str, bot_qq: str) -> bool:
    """检查消息是否@了机器人"""
    return f"[CQ:at,qq={bot_qq}]" in message

def remove_at(message: str) -> str:
    """移除消息中的@"""
    import re
    return re.sub(r'\[CQ:at,qq=\d+\]', '', message).strip()

def contains_keyword(message: str, keywords: List[str]) -> bool:
    """检查消息是否包含关键词"""
    message_lower = message.lower()
    return any(keyword.lower() in message_lower for keyword in keywords)
