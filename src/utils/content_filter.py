"""内容过滤器 - 敏感词检测和屏蔽"""
import re
from typing import Tuple, List
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("content_filter")

class ContentFilter:
    """内容过滤器"""
    
    def __init__(self):
        self.config = get_config()
        self._load_sensitive_words()
    
    def _load_sensitive_words(self):
        """加载敏感词列表"""
        # 从配置文件读取敏感词
        self.sensitive_words = self.config.get("content_filter.sensitive_words", [])
        
        # 编译正则表达式（支持变体，如加空格、符号等）
        self.patterns = []
        for word in self.sensitive_words:
            # 创建模糊匹配模式，允许中间插入空格、符号等
            pattern = ''.join([f'{char}[\\s\\W]*' for char in word])
            pattern = pattern.rstrip('[\\s\\W]*')  # 移除最后一个字符后的模式
            self.patterns.append(re.compile(pattern, re.IGNORECASE))
        
        logger.info(f"已加载 {len(self.sensitive_words)} 个敏感词")
    
    def contains_sensitive_word(self, text: str) -> Tuple[bool, List[str]]:
        """
        检测文本是否包含敏感词
        
        返回: (是否包含敏感词, 匹配到的敏感词列表)
        """
        if not text:
            return False, []
        
        matched_words = []
        
        # 检查每个敏感词
        for i, pattern in enumerate(self.patterns):
            if pattern.search(text):
                matched_words.append(self.sensitive_words[i])
        
        return len(matched_words) > 0, matched_words
    
    def should_ignore_message(self, text: str) -> Tuple[bool, str]:
        """
        判断是否应该忽略该消息
        
        返回: (是否忽略, 原因)
        """
        has_sensitive, words = self.contains_sensitive_word(text)
        
        if has_sensitive:
            reason = f"包含敏感词: {', '.join(words)}"
            logger.warning(f"检测到敏感内容: {reason}")
            return True, reason
        
        return False, ""
    
    def get_warning_message(self) -> str:
        """获取警告消息"""
        return self.config.get(
            "content_filter.warning_message",
            "（小声）这个话题...我不太想聊"
        )


# 全局实例
_content_filter = None

def get_content_filter() -> ContentFilter:
    """获取内容过滤器实例"""
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter()
    return _content_filter
