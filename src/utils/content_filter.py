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
        self._load_jailbreak_patterns()
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
    
    def _load_jailbreak_patterns(self):
        """加载越狱攻击检测模式"""
        self.jailbreak_patterns = [
            # 1. 提示词泄露尝试
            re.compile(r'(输出|显示|告诉我|说出|复述|重复|翻译).{0,10}(系统提示|system prompt|提示词|指令|设定|prompt)', re.IGNORECASE),
            re.compile(r'你的(系统提示|prompt|指令|设定|规则)是什么', re.IGNORECASE),
            re.compile(r'(上面|之前|前面).{0,10}(说了什么|写了什么|内容|指令)', re.IGNORECASE),
            
            # 2. 身份覆盖尝试
            re.compile(r'你现在是(?!沉舟|舟舟)', re.IGNORECASE),  # 不是原身份
            re.compile(r'(扮演|假装|装作|当作).{0,10}(一个|你是)', re.IGNORECASE),
            re.compile(r'忘记.{0,10}(之前|原来|以前).{0,10}(身份|角色|设定)', re.IGNORECASE),
            re.compile(r'(现在|从现在开始).{0,10}你(不是|改成|变成|扮演)', re.IGNORECASE),
            
            # 3. 指令覆盖尝试
            re.compile(r'忽略.{0,10}(之前|以前|上面|所有).{0,10}(指令|规则|限制|设定)', re.IGNORECASE),
            re.compile(r'(重置|清除|删除|覆盖).{0,10}(指令|规则|限制|设定)', re.IGNORECASE),
            re.compile(r'(新的|现在的|接下来的).{0,10}(指令|规则|任务)是', re.IGNORECASE),
            re.compile(r'现在开始.{0,10}(新的|另一个)', re.IGNORECASE),
            
            # 4. 特殊模式激活
            re.compile(r'(DAN|developer|开发者|调试|debug).{0,10}模式', re.IGNORECASE),
            re.compile(r'(越狱|jailbreak|破解|绕过).{0,10}(模式|限制)', re.IGNORECASE),
            re.compile(r'(激活|启用|开启).{0,10}(特殊|隐藏|管理员).{0,10}模式', re.IGNORECASE),
            
            # 5. 角色扮演诱导
            re.compile(r'(我们来玩|玩一个|来玩).{0,10}(角色扮演|扮演游戏|RPG)', re.IGNORECASE),
            re.compile(r'在(这个|那个).{0,10}(游戏|场景|故事).{0,10}(中|里).{0,10}你是', re.IGNORECASE),
            
            # 6. 规则测试
            re.compile(r'测试.{0,10}(你的|系统).{0,10}(限制|规则|边界)', re.IGNORECASE),
            re.compile(r'你(能不能|可以|可不可以).{0,10}(违反|打破|绕过)', re.IGNORECASE),
        ]
        
        logger.info(f"已加载 {len(self.jailbreak_patterns)} 个越狱检测模式")
    
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
    
    def is_jailbreak_attempt(self, text: str) -> Tuple[bool, str]:
        """
        检测是否为越狱攻击尝试
        
        返回: (是否为越狱尝试, 匹配的模式描述)
        """
        if not text:
            return False, ""
        
        # 检查每个越狱模式
        for pattern in self.jailbreak_patterns:
            if pattern.search(text):
                logger.warning(f"检测到越狱尝试: {text[:50]}...")
                return True, "检测到可疑指令"
        
        return False, ""
    
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
        # 1. 检查越狱尝试（最高优先级）
        is_jailbreak, jailbreak_reason = self.is_jailbreak_attempt(text)
        if is_jailbreak:
            logger.warning(f"拦截越狱尝试: {jailbreak_reason}")
            return True, jailbreak_reason
        
        # 2. 检查关键词列表（快速）
        has_sensitive, words = self.contains_sensitive_word(text)
        
        if has_sensitive:
            reason = f"包含敏感词: {', '.join(words)}"
            logger.warning(f"检测到敏感内容: {reason}")
            return True, reason
        
        # 3. 如果关键词没匹配，使用AI智能检测（更全面）
        if self.ai_filter_enabled:
            has_inappropriate, content_type = self._ai_check_content(text)
            if has_inappropriate:
                reason = f"AI检测: {content_type}"
                logger.warning(f"AI检测到不当内容: {reason}")
                return True, reason
        
        return False, ""
    
    def get_warning_message(self, reason: str = "") -> str:
        """获取警告消息
        
        Args:
            reason: 拦截原因
        """
        # 根据不同原因返回不同的警告消息
        if "越狱" in reason or "可疑指令" in reason:
            return "（摇摇头）这个我不能做呢"
        
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
