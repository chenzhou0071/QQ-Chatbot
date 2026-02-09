"""统一记忆管理器"""
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

from src.memory.context import get_context_manager
from src.memory.database import get_database
from src.memory.vector_store import get_vector_store
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("memory_manager")

class MemoryManager:
    """统一记忆管理器（三层记忆系统）"""
    
    def __init__(self):
        self.config = get_config()
        self.context_manager = get_context_manager()
        self.db = get_database()
        
        # 向量库（可选）
        self.vector_enabled = self.config.get("memory.vector_db.enabled", True)
        if self.vector_enabled:
            try:
                self.vector_store = get_vector_store()
                logger.info("向量数据库已启用")
            except Exception as e:
                logger.error(f"向量数据库初始化失败: {e}")
                self.vector_enabled = False
        else:
            logger.info("向量数据库未启用")
    
    def add_message(self,
                    chat_type: str,
                    role: str,
                    content: str,
                    sender_id: str = "",
                    sender_name: str = ""):
        """添加消息（三层存储）"""
        timestamp = datetime.now()
        
        # 1. 短期记忆（内存缓存）
        self.context_manager.add_message(chat_type, role, content, sender_name)
        
        # 2. 长期记忆（SQLite）
        self._save_to_database(chat_type, sender_id, sender_name, content, role, timestamp)
        
        # 3. 语义记忆（向量库）- 只存储用户消息
        if self.vector_enabled and role == "user" and content.strip():
            self._save_to_vector(chat_type, sender_id, sender_name, content, timestamp)
    
    def _save_to_database(self, chat_type, sender_id, sender_name, content, role, timestamp):
        """保存到SQLite"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_log 
                    (chat_type, sender_id, sender_name, message_type, message_content, is_bot, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    chat_type,
                    sender_id,
                    sender_name,
                    "text",
                    content,
                    1 if role == "assistant" else 0,
                    timestamp.isoformat()
                ))
        except Exception as e:
            logger.error(f"保存到数据库失败: {e}")
    
    def _save_to_vector(self, chat_type, sender_id, sender_name, content, timestamp):
        """保存到向量库"""
        try:
            # 生成唯一ID
            chat_id = hashlib.md5(
                f"{chat_type}_{sender_id}_{timestamp.isoformat()}_{content[:20]}".encode()
            ).hexdigest()
            
            self.vector_store.add_memory(
                chat_id=chat_id,
                content=content,
                sender_id=sender_id,
                sender_name=sender_name,
                chat_type=chat_type,
                timestamp=timestamp.isoformat()
            )
        except Exception as e:
            logger.error(f"保存到向量库失败: {e}")
    
    def search_related_memories(self, 
                                query: str, 
                                chat_type: str,
                                n_results: int = None) -> str:
        """搜索相关记忆并格式化"""
        if not self.vector_enabled:
            return ""
        
        # 从配置读取搜索结果数
        if n_results is None:
            n_results = self.config.get("memory.vector_db.search_results", 5)
        
        try:
            memories = self.vector_store.search_memory(query, n_results, chat_type)
            
            if not memories:
                return ""
            
            # 格式化为上下文
            context_parts = ["[相关记忆]"]
            for mem in memories:
                # 只显示相似度高的记忆（距离小于0.5）
                if mem['distance'] < 0.5:
                    context_parts.append(
                        f"- {mem['sender_name']}: {mem['content']} ({mem['timestamp'][:10]})"
                    )
            
            if len(context_parts) == 1:  # 只有标题，没有有效记忆
                return ""
            
            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return ""
    
    def get_context_for_ai(self, chat_type: str, current_query: str = "") -> List[Dict]:
        """获取AI所需的完整上下文"""
        # 1. 获取短期记忆
        messages = self.context_manager.format_for_ai(chat_type)
        
        # 2. 如果有查询且启用向量库，搜索相关长期记忆
        if current_query and self.vector_enabled:
            related_memories = self.search_related_memories(current_query, chat_type)
            if related_memories:
                # 在消息开头插入相关记忆
                messages.insert(0, {
                    "role": "system",
                    "content": related_memories
                })
                logger.info(f"[{chat_type}] 注入相关记忆")
        
        return messages
    
    def get_stats(self) -> Dict:
        """获取记忆统计"""
        stats = {
            'short_term': self.context_manager.get_cache_stats(),
        }
        
        if self.vector_enabled:
            stats['vector_store'] = self.vector_store.get_stats()
        
        return stats


# 全局实例
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """获取记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
