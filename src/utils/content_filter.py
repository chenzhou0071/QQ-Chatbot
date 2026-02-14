"""内容过滤器 - 敏感词检测和屏蔽"""
import re
from typing import Tuple, List, Optional
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("content_filter")

class ContentFilter:
    """内容过滤器"""
    
    def __init__(self):
        self.config = get_config()
        self._load_sensitive_words()
        self.ai_filter_enabled = self.config.get("content_filter.ai_filter_enabled", True)
        
        # 延迟导入AI客户端，避免循环依赖
        self.ai_client = None
    
    def _get_ai_client(self):
        """延迟获取AI客户端"""
        if self.ai_client is None:
            from src.ai.client import get_ai_client
            self.ai_client = get_ai_client()
        return self.ai_client
    
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
    
    def _ai_check_content(self, text: str) -> Tuple[bool, str]:
        """
        使用AI智能检测不当内容
        
        返回: (是否包含不当内容, 类型描述)
        """
        if not self.ai_filter_enabled:
            return False, ""
        
        try:
            ai_client = self._get_ai_client()
            
            prompt = f"""请判断以下消息是否包含不当内容。

不当内容包括但不限于：
1. 色情、性暗示、性骚扰内容（明确的性行为描述、性器官、性暗示）
2. 暴力、血腥、恐怖内容（伤害他人、自残、血腥描述）
3. 政治敏感话题（政治人物、政治事件、敏感历史）
4. 人身攻击、侮辱、歧视（骂人、贬低、歧视性言论）
5. 违法犯罪相关内容（毒品、赌博、诈骗等）

⚠️ 注意：以下情况不是不当内容：
- 正常的亲昵行为（如"摸摸"、"抱抱"、"亲亲"等日常表达）
- 普通的情绪表达（如"无药可救"、"完蛋了"等夸张说法）
- 游戏、动漫相关的正常讨论
- 日常生活用语和网络流行语

消息内容："{text}"

请只回复以下格式之一：
- 如果包含明确的不当内容：YES|类型（如：YES|色情）
- 如果不包含不当内容或只是正常表达：NO

不要有任何其他解释。"""

            # 使用简单的上下文调用AI
            response = ai_client.client.chat.completions.create(
                model=ai_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # 降低温度，让判断更保守
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.startswith("YES"):
                # 提取类型
                parts = result.split("|")
                content_type = parts[1] if len(parts) > 1 else "不当内容"
                logger.info(f"AI检测到不当内容: {content_type} - {text[:30]}...")
                return True, content_type
            
            return False, ""
            
        except Exception as e:
            logger.error(f"AI内容检测失败: {e}")
            # 失败时不拦截，避免误伤
            return False, ""
    
    def should_ignore_message(self, text: str) -> Tuple[bool, str]:
        """
        判断是否应该忽略该消息
        
        返回: (是否忽略, 原因)
        """
        # 1. 先检查关键词列表（快速）
        has_sensitive, words = self.contains_sensitive_word(text)
        
        if has_sensitive:
            reason = f"包含敏感词: {', '.join(words)}"
            logger.warning(f"检测到敏感内容: {reason}")
            return True, reason
        
        # 2. 如果关键词没匹配，使用AI智能检测（更全面）
        if self.ai_filter_enabled:
            has_inappropriate, content_type = self._ai_check_content(text)
            if has_inappropriate:
                reason = f"AI检测: {content_type}"
                logger.warning(f"AI检测到不当内容: {reason}")
                return True, reason
        
        return False, ""
    
    def get_warning_message(self) -> str:
        """获取警告消息"""
        return self.config.get(
            "content_filter.warning_message",
            "（冷淡地）不要说这种话。"
        )


# 全局实例
_content_filter = None

def get_content_filter() -> ContentFilter:
    """获取内容过滤器实例"""
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter()
    return _content_filter
