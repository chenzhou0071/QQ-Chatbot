"""对话上下文管理"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.memory.database import get_database
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("context")

class ContextManager:
    """对话上下文管理器"""
    
    def __init__(self):
        self.db = get_database()
        self.config = get_config()
        self.max_messages = self.config.get("conversation.max_messages", 20)
        self.timeout_minutes = self.config.get("conversation.timeout_minutes", 30)
    
    def get_context(self, chat_type: str) -> List[Dict]:
        """获取对话上下文"""
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
        
        # 限制消息数量
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]
        
        # 保存到数据库
        self._save_context(chat_type, messages)
        
        logger.info(f"[{chat_type}] 添加消息: {role} - {content[:50]}...")
    
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
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_context WHERE chat_type = ?", (chat_type,))
        
        logger.info(f"[{chat_type}] 上下文已清空")
    
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
