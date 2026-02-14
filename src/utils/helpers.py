"""辅助函数"""
import re
import random
from typing import List, Optional

# B站链接检测正则（全局编译，避免重复编译）
_REG_BV = re.compile(r'BV[0-9A-Za-z]{10}')
_REG_AV = re.compile(r'av(\d+)', re.IGNORECASE)
_REG_B23 = re.compile(r'(b23\.tv|bili2233\.cn)')
_REG_SS = re.compile(r'ss(\d+)', re.IGNORECASE)
_REG_EP = re.compile(r'ep(\d+)', re.IGNORECASE)
_REG_MD = re.compile(r'md(\d+)', re.IGNORECASE)

# B站关键词（用于快速预检查）
_BILIBILI_KEYWORDS = ['bilibili', 'b23.tv', 'BV', 'av', 'ss', 'ep', 'md', '哔哩哔哩']


def random_choice(items: List[str]) -> str:
    """随机选择一个元素
    
    Args:
        items: 字符串列表
        
    Returns:
        随机选中的字符串，如果列表为空则返回空字符串
    """
    if not items:
        return ""
    return random.choice(items)


def is_at_bot(message: str, bot_qq: str) -> bool:
    """检查消息是否@了机器人
    
    Args:
        message: 消息内容
        bot_qq: 机器人QQ号
        
    Returns:
        是否@了机器人
    """
    return f"[CQ:at,qq={bot_qq}]" in message


def remove_at(message: str) -> str:
    """移除消息中的@
    
    Args:
        message: 消息内容
        
    Returns:
        移除@后的消息
    """
    return re.sub(r'\[CQ:at,qq=\d+\]', '', message).strip()


def contains_keyword(message: str, keywords: List[str]) -> bool:
    """检查消息是否包含关键词
    
    Args:
        message: 消息内容
        keywords: 关键词列表
        
    Returns:
        是否包含关键词
    """
    message_lower = message.lower()
    return any(keyword.lower() in message_lower for keyword in keywords)


def has_bilibili_link(message: str) -> bool:
    """检测消息中是否包含B站链接（优化版：快速预检查+正则匹配）
    
    Args:
        message: 消息内容
        
    Returns:
        是否包含B站链接
    """
    # 快速预检查：只有包含B站关键词时才进行正则匹配
    if not any(keyword in message for keyword in _BILIBILI_KEYWORDS):
        return False
    
    # 正则匹配
    return bool(
        _REG_BV.search(message) or 
        _REG_AV.search(message) or 
        _REG_B23.search(message) or 
        _REG_SS.search(message) or 
        _REG_EP.search(message) or 
        _REG_MD.search(message)
    )
