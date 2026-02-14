# 技术栈与实现细节

## 📚 目录

- [核心框架](#核心框架)
- [模块技术实现](#模块技术实现)
- [第三方服务](#第三方服务)
- [数据存储](#数据存储)
- [开发工具](#开发工具)
- [性能优化技术](#性能优化技术)

---

## 🎯 核心框架

### 1. NoneBot2 (v2.3.0+)

**用途**: 异步机器人框架

**技术特点**:
- 基于 Python asyncio 的异步事件驱动
- 插件化架构，支持热加载
- 内置依赖注入系统
- 完善的中间件机制

**使用场景**:
- 消息路由与分发
- 事件处理与响应
- 插件生命周期管理
- WebSocket 连接管理

**核心代码**:
```python
# src/bot.py
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
nonebot.load_plugins("src/plugins")
```

---

### 2. NapCat

**用途**: QQ协议实现

**技术特点**:
- 基于 NTQQ 的协议适配
- WebSocket 服务端
- OneBot V11 标准协议

**通信方式**:
```
QQ客户端 ← → NapCat ← → NoneBot2 (ws://127.0.0.1:8080)
```

---

## 🧩 模块技术实现

### 对话智能模块 (dialogue/)

#### 1. 意图分析器 (intent_analyzer.py)

**核心技术**:

| 功能 | 技术实现 | 算法/库 |
|------|---------|---------|
| 反问检测 | 正则表达式匹配 | Python `re` |
| 讽刺识别 | 规则评分系统 | 自定义算法 |
| 话题追踪 | 关键词提取 + 相似度计算 | `jieba` + Jaccard |
| 中文分词 | jieba分词 | `jieba.lcut()` |

**关键算法**:
```python
# Jaccard 相似度
def calculate_relevance(keywords1, keywords2):
    set1, set2 = set(keywords1), set(keywords2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0
```

**依赖库**:
- `jieba>=0.42.1` - 中文分词
- `re` (内置) - 正则表达式

---

#### 2. 对话状态机 (state_machine.py)

**核心技术**:

| 组件 | 技术实现 |
|------|---------|
| 状态定义 | Python Enum |
| 状态转换 | 有限状态机 (FSM) |
| 状态持久化 | 内存存储 |

**状态转换逻辑**:
```python
from enum import Enum

class DialogueStateEnum(Enum):
    OPENING = "opening"
    MAINTAINING = "maintaining"
    SWITCHING = "switching"
    CLOSING = "closing"

# 转换规则
OPENING → (2条消息后) → MAINTAINING
MAINTAINING → (话题切换) → SWITCHING → MAINTAINING
MAINTAINING → (5分钟无消息) → CLOSING
```

---

#### 3. 主动对话引擎 (proactive_engine.py)

**核心技术**:

| 功能 | 技术实现 | 算法 |
|------|---------|------|
| 冷场检测 | 时间戳比较 | `time.time()` |
| 概率控制 | 随机数生成 | `random.random()` |
| 冷却机制 | 时间窗口限流 | 滑动窗口 |
| 话题生成 | 预设库 + 随机选择 | 加权随机 |

**关键实现**:
```python
# 冷场检测
duration = time.time() - last_message_time
if duration >= threshold:
    probability = level_probability[level]
    if random.random() < probability:
        generate_topic()
```

---

### 记忆系统 (memory/)

#### 1. 短期记忆 (context.py)

**核心技术**:

| 组件 | 技术实现 | 数据结构 |
|------|---------|----------|
| 缓存机制 | LRU Cache | `OrderedDict` |
| 超时管理 | 时间戳检查 | `datetime` |
| 消息限制 | 滑动窗口 | List切片 |

**性能优化**:
```python
from collections import OrderedDict

class ContextManager:
    def __init__(self):
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._cache_size = 10  # 最多缓存10个会话
    
    def _update_cache(self, chat_type, messages, last_active):
        self._cache[chat_type] = {'messages': messages, 'last_active': last_active}
        self._cache.move_to_end(chat_type)  # LRU更新
        
        # 淘汰最旧的
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
```

**依赖**:
- `collections.OrderedDict` (内置)
- `datetime` (内置)

---

#### 2. 长期记忆 (database.py)

**核心技术**:

| 组件 | 技术实现 |
|------|---------|
| 数据库 | SQLite3 |
| 连接管理 | Context Manager |
| 事务处理 | 自动提交/回滚 |
| 索引优化 | B-Tree索引 |

**数据库设计**:
```sql
-- 聊天记录表
CREATE TABLE chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_type TEXT,
    sender_id TEXT,
    sender_name TEXT,
    message_content TEXT,
    is_bot INTEGER,
    created_at DATETIME
);

-- 索引优化
CREATE INDEX idx_chat_log_sender ON chat_log(sender_id);
CREATE INDEX idx_chat_log_created ON chat_log(created_at);
```

**依赖**:
- `sqlite3` (内置)

---

#### 3. 语义记忆 (vector_store.py)

**核心技术**:

| 组件 | 技术实现 | 服务商 |
|------|---------|--------|
| 向量数据库 | Chroma | 本地持久化 |
| Embedding | text-embedding-v1 | 阿里云 DashScope |
| 相似度搜索 | 余弦相似度 | Chroma内置 |
| 向量维度 | 1536维 | 阿里云模型 |

**工作流程**:
```python
# 1. 生成向量
embedding = dashscope_embedding(text)  # 调用阿里云API

# 2. 存储到Chroma
collection.add(
    embeddings=[embedding],
    documents=[text],
    metadatas=[metadata],
    ids=[chat_id]
)

# 3. 语义搜索
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"chat_type": "group"}
)
```

**依赖**:
- `chromadb>=0.4.22` - 向量数据库
- `httpx>=0.27.0` - HTTP客户端（调用API）

---

#### 4. 群友数据库 (member_db.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 数据存储 | SQLite |
| 自动收集 | 事件监听 |
| 生日提醒 | 定时任务 |
| 活跃度统计 | SQL聚合查询 |

**数据表设计**:
```sql
CREATE TABLE group_member (
    qq_id TEXT PRIMARY KEY,
    nickname TEXT,
    ai_nickname TEXT,
    birthday TEXT,  -- MM-DD格式
    remark TEXT,
    message_count INTEGER,
    last_active DATETIME
);
```

---

### AI客户端 (ai/)

#### 1. AI客户端 (client.py)

**核心技术**:

| 组件 | 技术实现 | 协议 |
|------|---------|------|
| API调用 | OpenAI SDK | HTTP/REST |
| 流式响应 | 支持 | SSE |
| 重试机制 | 指数退避 | 自定义 |
| 降级策略 | 预设回复 | 自定义 |

**支持的AI提供商**:
- **DeepSeek**: `deepseek-chat`
- **通义千问**: `qwen-plus`

**重试策略**:
```python
retry_delays = [1, 3, 5]  # 秒
for attempt in range(max_retries):
    try:
        response = client.chat.completions.create(...)
        return response
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(retry_delays[attempt])
        else:
            return fallback_reply()
```

**依赖**:
- `openai>=1.0.0` - OpenAI SDK

---

#### 2. 提示词管理 (prompts.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 人设系统 | 模板字符串 |
| 动态注入 | 字符串拼接 |
| 上下文增强 | 条件组装 |

**Prompt结构**:
```python
system_prompt = f"""
【基础人设】
你是{name}，性格{traits}

【群友信息】
{member_info}

【对话状态】
{state_hint}

【意图提示】
{intent_hint}
"""
```

---

### 触发器系统 (triggers/)

#### 1. 触发器优先级

**核心技术**:

| 触发器 | 技术实现 | 优先级 |
|--------|---------|--------|
| @触发 | NoneBot `to_me()` | 5 (最高) |
| 关键词 | 字符串匹配 | 10 |
| 名字触发 | 正则表达式 | 15 |
| 智能触发 | AI判断 | 20 (最低) |

**实现方式**:
```python
# @触发
mention_matcher = on_message(rule=to_me(), priority=5, block=True)

# 关键词触发
keyword_matcher = on_message(priority=10, block=False)

# 智能触发
smart_matcher = on_message(priority=20, block=False)
```

---

#### 2. 定时任务 (scheduler.py)

**核心技术**:

| 组件 | 技术实现 | 库 |
|------|---------|-----|
| 定时调度 | APScheduler | `nonebot-plugin-apscheduler` |
| Cron表达式 | 标准Cron | APScheduler |
| 异步执行 | asyncio | Python内置 |

**示例**:
```python
from nonebot_plugin_apscheduler import scheduler

@scheduler.scheduled_job("cron", hour=8, minute=0)
async def morning_greeting():
    await bot.send_group_msg(group_id=xxx, message="早安~")
```

**依赖**:
- `nonebot-plugin-apscheduler>=0.4.0`

---

### 功能插件 (plugins/)

#### 1. B站链接解析 (bilibili.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 链接识别 | 正则表达式 |
| API调用 | HTTP请求 |
| 数据解析 | JSON解析 |

**正则模式**:
```python
patterns = [
    r'bilibili\.com/video/(BV\w+)',
    r'b23\.tv/(\w+)',
    r'bilibili\.com/bangumi/play/(ep\d+)'
]
```

**依赖**:
- `httpx>=0.27.0` - HTTP客户端

---

#### 2. 群友管理 (member_manager.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 命令解析 | NoneBot `on_command` |
| 权限控制 | 装饰器 |
| 数据查询 | SQL |

**命令注册**:
```python
birthday_cmd = on_command("生日", priority=5)

@birthday_cmd.handle()
async def handle_birthday(bot: Bot, event: Event):
    # 处理逻辑
    pass
```

---

### 工具层 (utils/)

#### 1. 联网搜索 (web_search.py)

**核心技术**:

| 组件 | 技术实现 | 服务商 |
|------|---------|--------|
| 搜索API | Web-Search MCP | 阿里云 DashScope |
| 关键词检测 | 字符串匹配 | 自定义 |
| 结果格式化 | 文本处理 | 自定义 |

**API调用**:
```python
import httpx

response = httpx.post(
    "https://dashscope.aliyuncs.com/api/v1/services/web-search",
    headers={"Authorization": f"Bearer {api_key}"},
    json={"query": query}
)
```

**依赖**:
- `httpx>=0.27.0`

---

#### 2. 内容过滤 (content_filter.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 敏感词检测 | Trie树 / 字符串匹配 |
| 规则引擎 | 正则表达式 |
| 黑名单 | Set查找 |

**实现**:
```python
class ContentFilter:
    def __init__(self):
        self.sensitive_words = set(['敏感词1', '敏感词2'])
    
    def should_ignore(self, message: str) -> bool:
        return any(word in message for word in self.sensitive_words)
```

---

#### 3. 配置管理 (config.py)

**核心技术**:

| 功能 | 技术实现 | 格式 |
|------|---------|------|
| 配置文件 | YAML解析 | `.yaml` |
| 环境变量 | dotenv | `.env` |
| 热更新 | 文件监听 | 可选 |

**配置加载**:
```python
import yaml
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("config/.env")

# 加载YAML配置
with open("config/config.yaml") as f:
    config = yaml.safe_load(f)
```

**依赖**:
- `pyyaml>=6.0` - YAML解析
- `python-dotenv>=1.0.0` - 环境变量

---

#### 4. 日志系统 (logger.py)

**核心技术**:

| 功能 | 技术实现 |
|------|---------|
| 日志框架 | Python logging |
| 日志分割 | RotatingFileHandler |
| 格式化 | Formatter |
| 多级别 | DEBUG/INFO/WARNING/ERROR |

**配置**:
```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

# 文件处理器
handler = RotatingFileHandler(
    "data/logs/bot.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logger.addHandler(handler)
```

---

## 🌐 第三方服务

### 1. DeepSeek API

**用途**: AI对话生成

**技术规格**:
- 模型: `deepseek-chat`
- 协议: OpenAI兼容
- 接口: REST API
- 认证: Bearer Token

**费用**:
- 按Token计费
- 约 ¥0.001/1K tokens

---

### 2. 阿里云 DashScope

**用途**: Embedding + 联网搜索

**服务**:
| 服务 | 模型/API | 用途 |
|------|---------|------|
| Embedding | text-embedding-v1 | 向量生成 |
| Web-Search | web-search | 联网搜索 |

**技术规格**:
- 向量维度: 1536
- QPS限制: 5
- 月度额度: 2000次免费

---

## 💾 数据存储

### 1. SQLite

**版本**: 3.x

**用途**:
- 长期记忆存储
- 群友信息管理
- 对话上下文持久化

**特点**:
- 无需独立服务
- 文件型数据库
- 支持事务
- 轻量级

**文件位置**: `data/bot.db`

---

### 2. Chroma

**版本**: 0.4.22+

**用途**: 向量数据库

**技术特点**:
- 本地持久化
- 支持余弦相似度搜索
- 内置元数据过滤
- Python原生支持

**存储位置**: `data/chroma/`

**数据量估算**:
- 每条消息: ~6KB
- 1000条: ~6MB
- 10000条: ~60MB

---

## 🛠️ 开发工具

### 1. Python 环境

**版本**: 3.9+

**包管理**: pip

**虚拟环境**: venv

---

### 2. 依赖管理

**文件**: `requirements.txt`

**核心依赖**:
```txt
nonebot2[fastapi]>=2.3.0
nonebot-adapter-onebot>=2.4.0
nonebot-plugin-apscheduler>=0.4.0
httpx>=0.27.0
openai>=1.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
requests>=2.31.0
chromadb>=0.4.22
jieba>=0.42.1
```

---

### 3. 版本控制

**工具**: Git

**平台**: GitHub

**分支策略**: 主分支开发

---

## ⚡ 性能优化技术

### 1. 缓存策略

| 层级 | 技术 | 命中率 |
|------|------|--------|
| L1 | LRU内存缓存 | >90% |
| L2 | SQLite查询缓存 | >70% |
| L3 | 向量数据库 | 按需 |

---

### 2. 异步编程

**技术**: Python asyncio

**优势**:
- 非阻塞I/O
- 高并发处理
- 资源利用率高

**示例**:
```python
async def handle_message(bot: Bot, event: Event):
    # 异步处理
    result = await async_function()
    await bot.send(result)
```

---

### 3. 连接池

**数据库连接**: Context Manager

**HTTP连接**: httpx连接池

---

### 4. 索引优化

**SQLite索引**:
```sql
CREATE INDEX idx_chat_log_sender ON chat_log(sender_id);
CREATE INDEX idx_chat_log_created ON chat_log(created_at);
```

**查询优化**:
- 使用索引列
- 避免全表扫描
- 限制返回行数

---

## 📊 技术选型理由

### 为什么选择 NoneBot2？
- ✅ 成熟的异步框架
- ✅ 活跃的社区支持
- ✅ 丰富的插件生态
- ✅ 完善的文档

### 为什么选择 SQLite？
- ✅ 零配置
- ✅ 轻量级
- ✅ 可靠性高
- ✅ 适合单机部署

### 为什么选择 Chroma？
- ✅ Python原生
- ✅ 本地部署
- ✅ 易于集成
- ✅ 性能优秀

### 为什么选择 DeepSeek？
- ✅ 性价比高
- ✅ 中文能力强
- ✅ API稳定
- ✅ OpenAI兼容

---

## 🔄 技术演进路线

### 已完成
- ✅ 基础对话功能
- ✅ 三层记忆系统
- ✅ 对话智能引擎
- ✅ 向量语义搜索

### 进行中
- 🔄 性能优化
- 🔄 功能完善
- 🔄 文档补充

### 计划中
- 📅 多模态支持（图片、语音）
- 📅 分布式部署
- 📅 知识图谱
- 📅 联邦学习

---

## 📚 相关文档

- [项目概览](PROJECT_OVERVIEW.md)
- [系统架构](ARCHITECTURE.md)
- [API参考](API_REFERENCE.md)
- [部署文档](DEPLOYMENT.md)

---

**最后更新**: 2026-02-14
**文档版本**: v1.0.0
