-- QQ聊天机器人数据库初始化脚本

-- 对话上下文表
CREATE TABLE IF NOT EXISTS conversation_context (
    chat_type TEXT PRIMARY KEY,
    messages TEXT,
    message_count INTEGER DEFAULT 0,
    last_active DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 聊天记录表
CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_type TEXT,
    sender_id TEXT,
    sender_name TEXT,
    message_type TEXT,
    message_content TEXT,
    is_bot INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 关键词回复表
CREATE TABLE IF NOT EXISTS keyword_reply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE,
    reply_type TEXT,
    reply_content TEXT,
    priority INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_chat_log_sender ON chat_log(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_log_type ON chat_log(chat_type);
CREATE INDEX IF NOT EXISTS idx_chat_log_created ON chat_log(created_at);
