"""数据库操作"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from src.utils.logger import get_logger

logger = get_logger("database")

class Database:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 对话上下文表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_context (
                    chat_type TEXT PRIMARY KEY,
                    messages TEXT,
                    message_count INTEGER DEFAULT 0,
                    last_active DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 聊天记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_type TEXT,
                    sender_id TEXT,
                    sender_name TEXT,
                    message_type TEXT,
                    message_content TEXT,
                    is_bot INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 关键词回复表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_reply (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE,
                    reply_type TEXT,
                    reply_content TEXT,
                    priority INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 群友信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_member (
                    qq_id TEXT PRIMARY KEY,
                    qq_name TEXT,
                    group_card TEXT,
                    nickname TEXT,
                    nickname_confirmed INTEGER DEFAULT 0,
                    birthday TEXT,
                    remark TEXT,
                    avatar_url TEXT,
                    is_active INTEGER DEFAULT 1,
                    first_seen DATETIME,
                    last_active DATETIME,
                    leave_time DATETIME,
                    message_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_log_sender 
                ON chat_log(sender_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_log_type 
                ON chat_log(chat_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_log_created 
                ON chat_log(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_group_member_active 
                ON group_member(is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_group_member_birthday 
                ON group_member(birthday)
            """)
            
            logger.info("数据库初始化完成")


# 全局数据库实例
_database = None

def get_database() -> Database:
    """获取数据库实例"""
    global _database
    if _database is None:
        from src.utils.config import get_config
        config = get_config()
        _database = Database(config.database_path)
    return _database
