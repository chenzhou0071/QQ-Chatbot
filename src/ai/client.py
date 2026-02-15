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
             sender_qq: Optional[str] = None,
             enable_auto_search: bool = True) -> Optional[str]:
        """发送聊天请求
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数，None则使用默认值
            search_context: 联网搜索的上下文信息
            chat_type: 聊天类型，"group" 为群聊，"private" 为私聊
            sender_qq: 发送者的 QQ 号，用于识别管理员
            enable_auto_search: 是否启用自动搜索（当AI无法回答时）
            
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
                
                # 检查是否需要自动搜索
                if enable_auto_search and not search_context and self._should_auto_search(reply, messages):
                    logger.info("检测到AI无法回答，尝试联网搜索")
                    # 获取用户的最后一条消息
                    user_message = None
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            user_message = msg.get("content")
                            break
                    
                    if user_message:
                        # 导入 web_search（避免循环导入）
                        from src.utils.web_search import get_web_search_client
                        web_search_client = get_web_search_client()
                        
                        # 执行搜索
                        search_result = web_search_client.search(user_message)
                        if search_result:
                            logger.info("搜索成功，使用搜索结果重新生成回复")
                            # 递归调用，但禁用自动搜索避免无限循环
                            return self.chat(
                                messages=messages,
                                temperature=temperature,
                                search_context=search_result,
                                chat_type=chat_type,
                                sender_qq=sender_qq,
                                enable_auto_search=False  # 禁用自动搜索
                            )
                        else:
                            logger.warning("搜索失败，返回原始回复")
                
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
    
    def _should_auto_search(self, reply: str, messages: List[Dict[str, str]]) -> bool:
        """判断AI回复是否表明需要联网搜索
        
        Args:
            reply: AI的回复内容
            messages: 对话消息列表
            
        Returns:
            是否需要自动搜索
        """
        # 检测AI回复中的"不知道"、"不了解"等关键词
        uncertain_keywords = [
            "不知道", "不清楚", "不了解", "不太清楚", "不太了解",
            "不确定", "不太确定", "没听说过", "不太懂",
            "我不知道", "我不清楚", "我不了解", "我不确定",
            "无法回答", "无法告诉", "不能回答",
            "需要查一下", "需要搜索", "需要联网"
        ]
        
        # 如果回复包含这些关键词，需要搜索
        if any(keyword in reply for keyword in uncertain_keywords):
            logger.debug(f"检测到不确定关键词: {reply[:50]}...")
            return True
        
        # 如果回复包含"抱歉"、"对不起"等道歉词，可能是无法回答
        apology_keywords = ["抱歉", "对不起", "不好意思", "很遗憾"]
        if any(keyword in reply for keyword in apology_keywords):
            logger.debug(f"检测到道歉关键词: {reply[:50]}...")
            return True
        
        return False
    
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
