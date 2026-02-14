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
    
    def __init__(self) -> None:
        self.config = get_config()
        self.provider: str = self.config.get_env("AI_PROVIDER", "deepseek")
        
        # 从配置文件读取参数
        self.max_retries: int = self.config.get("ai.max_retries", 3)
        self.retry_delays: List[int] = self.config.get("ai.retry_delays", [1, 3, 5])
        self.default_temperature: float = self.config.get("ai.temperature", 0.7)
        self.max_tokens: int = self.config.get("ai.max_tokens", 500)
        
        # 初始化客户端
        self._init_client()
    
    def _init_client(self) -> None:
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
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: Optional[float] = None, 
             search_context: Optional[str] = None, 
             chat_type: str = "group", 
             sender_qq: Optional[str] = None) -> Optional[str]:
        """发送聊天请求
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数，None则使用默认值
            search_context: 联网搜索的上下文信息
            chat_type: 聊天类型，"group" 为群聊，"private" 为私聊
            sender_qq: 发送者的 QQ 号，用于识别管理员
            
        Returns:
            AI回复内容，失败返回None
        """
        # 使用默认温度
        if temperature is None:
            temperature = self.default_temperature
        
        # 添加系统提示词
        system_prompt = get_system_prompt(chat_type, sender_qq)
        
        # 如果有搜索上下文，添加到系统提示词中
        if search_context:
            system_prompt += f"\n\n【实时信息】\n以下是联网搜索获取的实时信息，请基于这些信息回答，但保持你的人设和语气：\n{search_context}"
        
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=self.max_tokens
                )
                
                reply = response.choices[0].message.content.strip()
                logger.debug(f"AI回复成功: {reply[:50]}...")
                return reply
            
            except ConnectionError as e:
                logger.warning(f"AI连接失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.debug(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error("AI连接持续失败，降级回复")
                    return self._fallback_reply()
            
            except TimeoutError as e:
                logger.warning(f"AI请求超时 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    time.sleep(delay)
                else:
                    logger.error("AI请求持续超时，降级回复")
                    return self._fallback_reply()
            
            except ValueError as e:
                logger.error(f"AI请求参数错误: {e}", exc_info=True)
                return self._fallback_reply()
            
            except KeyError as e:
                logger.error(f"AI响应格式错误: {e}", exc_info=True)
                return self._fallback_reply()
                
            except Exception as e:
                logger.error(f"AI调用未知错误 (尝试 {attempt + 1}/{self.max_retries}): {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    time.sleep(delay)
                else:
                    logger.critical("AI调用连续失败，降级回复")
                    return self._fallback_reply()
        
        return None
    
    def _fallback_reply(self) -> str:
        """降级回复
        
        Returns:
            降级回复消息
        """
        fallback_messages = [
            "抱歉，我现在有点累了，稍后再聊吧~",
            "emmm...我需要休息一下",
            "不好意思，我暂时无法回复",
        ]
        import random
        return random.choice(fallback_messages)
    
    def simple_chat(self, message: str) -> Optional[str]:
        """简单对话（无上下文）
        
        Args:
            message: 用户消息
            
        Returns:
            AI回复内容
        """
        messages = [{"role": "user", "content": message}]
        return self.chat(messages)


# 全局AI客户端实例
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """获取AI客户端实例
    
    Returns:
        AIClient实例
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
