"""对话上下文管理"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import OrderedDict

from src.memory.database import get_database
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("context")

class ContextManager:
    """对话上下文管理器（优化版：内存缓存）"""
    
    def __init__(self):
        self.db = get_database()
        self.config = get_config()
        self.max_messages = self.config.get("conversation.max_messages", 30)  # 增加到30条
        self.timeout_minutes = self.config.get("conversation.timeout_minutes", 30)
        
        # 内存缓存（LRU）- 核心优化
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._cache_size = 10  # 缓存最近10个会话
    
    def get_context(self, chat_type: str) -> List[Dict]:
        """获取对话上下文（带缓存）"""
        # 1. 先查缓存
        if chat_type in self._cache:
            cache_data = self._cache[chat_type]
            
            # 检查是否超时
            last_active = datetime.fromisoformat(cache_data['last_active'])
            if datetime.now() - last_active <= timedelta(minutes=self.timeout_minutes):
                # 更新LRU顺序
                self._cache.move_to_end(chat_type)
                logger.debug(f"[{chat_type}] 缓存命中")
                return cache_data['messages']
            else:
                # 超时，清除缓存
                logger.info(f"[{chat_type}] 上下文已超时，清空")
                del self._cache[chat_type]
                self.clear_context(chat_type)
                return []
        
        # 2. 缓存未命中，查数据库
        logger.debug(f"[{chat_type}] 缓存未命中，查询数据库")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT messages, last_active FROM conversation_context WHERE chat_type = ?",
                (chat_type,)
            )
            row = cursor.fetchone()
            
            if not row:
                return []
            
            # 检查是否超时
            last_active = datetime.fromisoformat(row["last_active"])
            if datetime.now() - last_active > timedelta(minutes=self.timeout_minutes):
                logger.info(f"[{chat_type}] 上下文已超时，清空")
                self.clear_context(chat_type)
                return []
            
            messages = json.loads(row["messages"])
            
            # 3. 加入缓存
            self._update_cache(chat_type, messages, row["last_active"])
            
            return messages
    
    def add_message(self, chat_type: str, role: str, content: str, name: Optional[str] = None):
        """添加消息到上下文"""
        messages = self.get_context(chat_type)
        
        # 构建消息
        message = {
            "role": role,
            "content": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if name:
            message["name"] = name
        
        messages.append(message)
        
        # 限制消息数量（保留最近的）
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]
        
        # 更新缓存和数据库
        now = datetime.now().isoformat()
        self._update_cache(chat_type, messages, now)
        self._save_context(chat_type, messages)
        
        logger.info(f"[{chat_type}] 添加消息: {role} - {content[:50]}...")
    
    def _update_cache(self, chat_type: str, messages: List[Dict], last_active: str):
        """更新缓存"""
        self._cache[chat_type] = {
            'messages': messages,
            'last_active': last_active
        }
        self._cache.move_to_end(chat_type)
        
        # LRU淘汰：超过缓存大小时移除最旧的
        if len(self._cache) > self._cache_size:
            removed_key = next(iter(self._cache))
            self._cache.popitem(last=False)
            logger.debug(f"[{removed_key}] 从缓存中淘汰")
    
    def _save_context(self, chat_type: str, messages: List[Dict]):
        """保存上下文到数据库"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO conversation_context 
                (chat_type, messages, message_count, last_active, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                chat_type,
                json.dumps(messages, ensure_ascii=False),
                len(messages),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
    
    def clear_context(self, chat_type: str):
        """清空上下文"""
        # 清除缓存
        if chat_type in self._cache:
            del self._cache[chat_type]
            logger.debug(f"[{chat_type}] 从缓存中清除")
        
        # 清除数据库
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_context WHERE chat_type = ?", (chat_type,))
        
        logger.info(f"[{chat_type}] 上下文已清空")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息（用于调试）"""
        return {
            'cached_chats': list(self._cache.keys()),
            'cache_size': len(self._cache),
            'cache_limit': self._cache_size
        }
    
    def format_for_ai(self, chat_type: str) -> List[Dict]:
        """格式化上下文供AI使用"""
        messages = self.get_context(chat_type)
        
        # 转换为AI API格式
        formatted = []
        for msg in messages:
            ai_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            # 如果是群聊，添加发送者名称
            if "name" in msg and msg["role"] == "user":
                ai_msg["content"] = f"[{msg['name']}]: {msg['content']}"
            
            formatted.append(ai_msg)
        
        return formatted


# 全局上下文管理器实例
_context_manager = None

def get_context_manager() -> ContextManager:
    """获取上下文管理器实例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
