"""AI客户端"""
import time
from typing import List, Dict, Optional
from openai import OpenAI

from src.utils.logger import get_logger
from src.utils.config import get_config
from src.ai.prompts import get_system_prompt

logger = get_logger("ai")

class AIClient:
    """AI客户端（支持DeepSeek和通义千问）"""
    
    def __init__(self):
        self.config = get_config()
        self.provider = self.config.get_env("AI_PROVIDER", "deepseek")
        self.max_retries = 3
        self.retry_delays = [1, 3, 5]  # 递增延迟
        
        # 初始化客户端
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        if self.provider == "deepseek":
            api_key = self.config.get_env("DEEPSEEK_API_KEY")
            base_url = self.config.get_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            self.model = "deepseek-chat"
        elif self.provider == "qwen":
            api_key = self.config.get_env("QWEN_API_KEY")
            base_url = self.config.get_env("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            self.model = "qwen-plus"
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")
        
        if not api_key or api_key == "your_api_key_here":
            raise ValueError(f"请配置{self.provider.upper()}_API_KEY")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"AI客户端初始化完成: {self.provider}")
    
    def chat(self, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
        """发送聊天请求"""
        # 添加系统提示词
        full_messages = [
            {"role": "system", "content": get_system_prompt()}
        ] + messages
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=500
                )
                
                reply = response.choices[0].message.content.strip()
                logger.info(f"AI回复成功: {reply[:50]}...")
                return reply
                
            except Exception as e:
                logger.warning(f"AI调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error("AI调用连续失败，降级回复")
                    return self._fallback_reply()
        
        return None
    
    def _fallback_reply(self) -> str:
        """降级回复"""
        fallback_messages = [
            "抱歉，我现在有点累了，稍后再聊吧~",
            "emmm...我需要休息一下",
            "不好意思，我暂时无法回复",
        ]
        import random
        return random.choice(fallback_messages)
    
    def simple_chat(self, message: str) -> Optional[str]:
        """简单对话（无上下文）"""
        messages = [{"role": "user", "content": message}]
        return self.chat(messages)


# 全局AI客户端实例
_ai_client = None

def get_ai_client() -> AIClient:
    """获取AI客户端实例"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
