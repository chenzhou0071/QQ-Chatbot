"""通义 Web-Search 联网搜索工具"""
import json
import requests
from typing import Optional
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("web_search")

class WebSearchClient:
    """通义 Web-Search 客户端（使用通义千问的联网搜索功能）"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.get_env("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        if not self.api_key or self.api_key == "your_dashscope_api_key_here":
            logger.warning("未配置 DASHSCOPE_API_KEY，联网搜索功能将不可用")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Web-Search 客户端初始化完成")
    
    def search(self, query: str) -> Optional[str]:
        """执行联网搜索（使用通义千问的 enable_search 参数）"""
        if not self.enabled:
            logger.warning("联网搜索功能未启用")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 优化查询语句，让搜索更精准
            optimized_query = query
            if "时间" in query or "几点" in query:
                optimized_query = f"现在的准确时间是几点？{query}"
            elif "天气" in query:
                optimized_query = f"今天实时天气情况：{query}"
            
            # 使用通义千问的联网搜索功能
            payload = {
                "model": "qwen-plus",
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个实时信息查询助手。当用户询问时间时，请直接告诉用户当前的准确时间（小时和分钟）。当用户询问天气时，请告诉具体的天气状况和温度。请用简短、直接的方式回答，不要解释概念。"
                        },
                        {
                            "role": "user",
                            "content": optimized_query
                        }
                    ]
                },
                "parameters": {
                    "result_format": "message",
                    "enable_search": True
                }
            }
            
            logger.info(f"开始联网搜索: {optimized_query}")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code != 200:
                logger.error(f"搜索请求失败: {response.status_code}, {response.text}")
                return None
            
            result = response.json()
            
            if 'output' in result and 'choices' in result['output']:
                choices = result['output']['choices']
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    result_text = message.get('content', '')
                    
                    if result_text:
                        logger.info(f"搜索成功: {result_text[:100]}...")
                        return result_text
                    else:
                        logger.warning("搜索未返回内容")
                        return None
            else:
                logger.error(f"搜索响应格式错误: {result}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("搜索请求超时")
            return None
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None
    
    def should_search(self, message: str) -> bool:
        """判断是否需要联网搜索"""
        if not self.enabled:
            return False
        
        # 1. 先检查明确的关键词（快速判断）
        search_keywords = [
            "天气", "气温", "温度", "下雨", "晴天", "阴天",
            "时间", "几点", "现在", "日期", "星期",
            "新闻", "热搜", "最新", "今天",
            "笑话", "段子",
            "股票", "金价", "油价",
            "汇率", "美元", "人民币"
        ]
        
        if any(keyword in message for keyword in search_keywords):
            logger.debug(f"关键词匹配，触发搜索: {message[:30]}...")
            return True
        
        # 2. 使用AI智能判断是否需要实时信息
        return self._ai_should_search(message)
    
    def _ai_should_search(self, message: str) -> bool:
        """使用AI判断是否需要联网搜索"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""判断以下问题是否需要联网搜索获取实时信息。

需要联网搜索的情况：
1. 询问最新版本、最新消息、最新动态
2. 询问当前价格、实时数据
3. 询问今天/最近发生的事件
4. 询问需要时效性的信息（如天气、时间、新闻）
5. 询问最新的技术、产品、游戏更新
6. 询问"现在"、"目前"、"最新"相关的问题

不需要联网搜索的情况：
1. 闲聊、打招呼
2. 询问概念、原理、历史知识
3. 请求写作、翻译等创作任务
4. 个人情感、意见类问题

问题："{message}"

请只回复：
- 需要搜索：YES
- 不需要搜索：NO

不要有任何其他内容。"""

            payload = {
                "model": "qwen-plus",
                "input": {
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {
                    "result_format": "message",
                    "temperature": 0.3,
                    "max_tokens": 10
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'output' in result and 'choices' in result['output']:
                    content = result['output']['choices'][0].get('message', {}).get('content', '').strip()
                    
                    if content == "YES":
                        logger.info(f"AI判断需要搜索: {message[:30]}...")
                        return True
                    else:
                        logger.debug(f"AI判断不需要搜索: {message[:30]}...")
                        return False
            
            # 判断失败时，保守策略：不搜索
            return False
            
        except Exception as e:
            logger.debug(f"AI判断搜索失败: {e}")
            # 失败时不搜索，避免过度调用
            return False


# 全局实例
_web_search_client = None

def get_web_search_client() -> WebSearchClient:
    """获取 Web-Search 客户端实例"""
    global _web_search_client
    if _web_search_client is None:
        _web_search_client = WebSearchClient()
    return _web_search_client
