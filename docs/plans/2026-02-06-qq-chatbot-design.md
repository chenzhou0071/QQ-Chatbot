# QQ聊天机器人设计文档

**日期**: 2026-02-06
**版本**: v1.0
**作者**: AI辅助设计

---

## 一、项目概述

### 1.1 项目目标

开发一个基于Python的QQ聊天机器人，主要部署在单个群聊中，具备智能对话能力，能够：

- **主动聊天**：定时发送早安、晚安、随机话题等
- **被动响应**：响应@消息、关键词触发、智能判断回复
- **管理员私聊**：仅管理员可私聊机器人，其他人的私聊被忽略
- **短期记忆**：维护对话上下文（10-20条消息），实现连贯对话

### 1.2 核心场景

**主要场景（群聊）**：
- 群成员@机器人时，智能回复
- 触发关键词时，自动回复
- 机器人主动发起话题，活跃群气氛
- 根据消息内容智能判断是否需要回复

**次要场景（私聊）**：
- 管理员私聊机器人，获得智能回复
- 用于测试、配置、查询等功能

**部署范围**：
- 仅在1个群中部署
- 单群设计，简化配置

### 1.3 暂不实���的功能

- ❌ 语音识别与发送
- ❌ 照片存储与检索
- ❌ 长期语义记忆（向量数据库）
- ❌ 多群管理
- ❌ 可视化界面

---

## 二、技术选型

### 2.1 核心技术栈

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| QQ协议 | **NapCat** | 基于NTQQ，风控风险低，稳定性好，社区活跃 |
| 机器人框架 | **NoneBot2** | Python生态成熟，插件丰富，开发简单 |
| AI API | **DeepSeek / 通义千问** | 性价比高，效果好，中文支持佳 |
| 数据库 | **SQLite** | 轻量级，零配置，适合单群小规模数据 |
| 定时任务 | **APScheduler** | 成熟稳定，支持cron表达式 |
| 运行环境 | **Python 3.9+** | 生态丰富，跨平台 |

### 2.2 技术架构图

```
┌─────────────────────────────────────────────────────┐
│                    QQ群聊/私聊                       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                    NapCat                           │
│           (QQ协议适配层)                            │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                  NoneBot2                           │
│           (事件驱动框架)                            │
└─────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  触发器模块  │  │  对话管理   │  │  定时任务   │
│             │  │   模块      │  │   模块      │
│ - @触发     │  │ - 上下文    │  │ - 早安      │
│ - 关键词    │  │ - 记忆管理  │  │ - 晚安      │
│ - 智能判断  │  │             │  │ - 随机话题  │
└─────────────┘  └─────────────┘  └─────────────┘
        ↓                ↓
┌─────────────────────────────────────┐
│            AI API 调用              │
│     (DeepSeek / 通义千问)           │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│          SQLite 数据库              │
│  - 对话上下文                        │
│  - 聊天记录（可选）                  │
│  - 关键词回复库（可选）              │
└─────────────────────────────────────┘
```

---

## 三、系统架构设计

### 3.1 分层架构

**第1层：基础设施层**
- NapCat：处理QQ协议、登录、消息收发
- NTQQ客户端：NapCat的依赖基础

**第2层：框架层**
- NoneBot2：事件驱动、插件管理、消息路由

**第3层：业务逻辑层**
- 触发器模块：判断何时响应
- 对话管理模块：维护短期记忆
- AI调用模块：与AI服务通信
- 定时任务模块：主动聊天

**第4层：数据持久层**
- SQLite：配置、上下文、日志

### 3.2 核心模块

#### 3.2.1 消息监听与路由模块

**职责**：
- 监听所有QQ消息事件（群聊、私聊）
- 判断消息类型和来源
- 路由到对应的处理器

**处理流程**：
```
收到消息
    ↓
判断消息类型
    ↓
├─ 私聊 → 检查发送者 → 管理员？→ 是：处理 / 否：忽略
└─ 群聊 → 检查群号 → 目标群？→ 是：触发器判断 / 否：忽略
```

#### 3.2.2 触发器模块

**四种触发方式**：

1. **@触发**
   - 检测消息中是否@机器人
   - 优先级最高
   - 立即回复

2. **关键词触发**
   - 维护关键词列表（可配置）
   - 匹配即触发
   - 优先级中等

3. **智能判断触发**
   - 将消息发送给AI
   - AI判断是否需要回复
   - 优先级最低
   - 避免刷群，设置触发概率（如30%）

4. **主动触发**
   - 定时任务驱动
   - 不依赖群消息
   - 发送早安、晚安、随机话题

#### 3.2.3 对话管理模块

**职责**：
- 维护对话上下文（10-20条消息）
- 为私聊和群聊分别维护上下文
- 定期清理过期上下文

**数据结构**：
```json
{
  "messages": [
    {"role": "user", "name": "张三", "content": "你好", "time": "2026-02-06 10:00:00"},
    {"role": "assistant", "content": "你好呀！", "time": "2026-02-06 10:00:01"},
    {"role": "user", "name": "李四", "content": "今天天气？", "time": "2026-02-06 10:01:00"}
  ],
  "count": 3
}
```

**清理策略**：
- 消息数量超过20条时，删除最早的
- 超过30分钟无新消息，清空上下文
- AI回复失败时，不更新上下文

#### 3.2.4 AI调用模块

**职责**：
- 封装AI API调用（DeepSeek/通义千问）
- 处理API错误、重试、限流
- 格式化上下文和消息

**功能**：
- 支持多API切换
- 自动重试（递增延迟：1s → 3s → 5s）
- 连续失败降级（返回固定提示）
- 上下文窗口管理

#### 3.2.5 定时任务模块

**职责**：
- 管理所有定时任务
- 支持cron表达式和间隔调度
- 错峰执行，避免API压力

**任务类型**：

1. **每日早安**
   - 时间：每天09:00
   - 内容：随机选择早安消息

2. **每日晚安**
   - 时间：每天23:00
   - 内容：随机选择晚安消息

3. **随机话题**
   - 频率：每2小时
   - 概率：30%触发
   - 内容：随机选择话题（新闻、笑话、问题等）

4. **定时清理**
   - 频率：每小时
   - 内容：清理过期上下文

---

## 四、数据库设计

### 4.1 表结构

#### 4.1.1 对话上下文表（conversation_context）

存储私聊和群聊的对话上下文。

```sql
CREATE TABLE conversation_context (
    chat_type TEXT PRIMARY KEY,  -- 聊天类型: 'private' 或 'group'
    messages TEXT,                -- 消息列表(JSON数组)
    message_count INTEGER DEFAULT 0,
    last_active DATETIME,         -- 最后活跃时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**示例数据**：
```
chat_type: 'group'
messages: '[{"role":"user","name":"张三","content":"你好","time":"2026-02-06 10:00:00"}]'
message_count: 1
last_active: 2026-02-06 10:00:00
```

#### 4.1.2 聊天记录表（chat_log）

可选，用于日志和数据分析。

```sql
CREATE TABLE chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_type TEXT,              -- 'private' 或 'group'
    sender_id TEXT,              -- 发送者QQ号
    sender_name TEXT,            -- 发送者昵称
    message_type TEXT,           -- 'text' 或 'image'
    message_content TEXT,        -- 消息内容
    is_bot INTEGER DEFAULT 0,    -- 是否机器人发送
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.3 关键词回复表（keyword_reply）

可选，用于自定义关键词回复。

```sql
CREATE TABLE keyword_reply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE,         -- 关键词
    reply_type TEXT,             -- 'fixed' 或 'ai'
    reply_content TEXT,          -- 固定回复内容(reply_type='fixed'时)
    priority INTEGER DEFAULT 0,  -- 优先级
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 索引设计

```sql
-- 提升查询性能
CREATE INDEX idx_chat_log_sender ON chat_log(sender_id);
CREATE INDEX idx_chat_log_type ON chat_log(chat_type);
CREATE INDEX idx_chat_log_created ON chat_log(created_at);
```

---

## 五、配置设计

### 5.1 主配置文件（config.yaml）

```yaml
# 机器人基本信息
bot:
  qq_number: "123456789"          # 机器人QQ号
  admin_qq: "987654321"           # 管理员QQ号（私聊白名单）
  target_group: "111222333"       # 目标群号

# 功能开关
features:
  mention_reply: true             # @回复
  keyword_reply: true             # 关键词回复
  smart_reply: true               # 智能判断回复
  auto_chat: true                 # 主动聊天
  chat_log: true                  # 是否记录聊天日志

# 关键词列表
keywords:
  - "天气"
  - "时间"
  - "笑话"
  - "故事"
  - "新闻"
  - "早安"
  - "晚安"

# 智能判断配置
smart_reply:
  trigger_rate: 0.3               # 触发概率(30%)
  min_interval: 60                # 最小间隔(秒)

# 主动聊天配置
auto_chat:
  morning:
    enabled: true
    time: "09:00"
    messages:
      - "大家早安！☀️"
      - "早上好！新的一天开始了！"
      - "早安，今天也是充满希望的一天！"

  night:
    enabled: true
    time: "23:00"
    messages:
      - "大家晚安！🌙"
      - "晚安，好梦！"
      - "该休息啦，晚安！"

  random_topic:
    enabled: true
    interval: 2                   # 间隔(小时)
    probability: 0.3              # 触发概率
    topics:
      - "今天天气不错呢"
      - "有人想听笑话吗？"
      - "最近有什么有趣的事吗？"
      - "大家今天过得怎么样？"

# 对话配置
conversation:
  max_messages: 20                # 最大消息数量
  timeout_minutes: 30             # 超时时间(分钟)
```

### 5.2 环境配置文件（.env）

```env
# AI API配置
AI_PROVIDER=deepseek              # 或 qwen
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
QWEN_API_KEY=your_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com

# 数据库配置
DATABASE_PATH=data/bot.db

# 日志配置
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_DIR=data/logs
LOG_RETENTION_DAYS=30            # 日志保留天数
```

---

## 六、项目结构

```
qq-chatbot/
├── config/
│   ├── config.yaml               # 主配置文件
│   └── .env                      # 环境变量（API密钥）
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # 程序入口
│   │
│   ├── bot/                      # NoneBot2插件
│   │   ├── __init__.py
│   │   ├── handlers.py           # 消息处理器
│   │   └── matcher.py            # 事件匹配器
│   │
│   ├── ai/                       # AI模块
│   │   ├── __init__.py
│   │   ├── client.py             # AI客户端（DeepSeek/通义）
│   │   └── prompts.py            # 提示词模板
│   │
│   ├── memory/                   # 记忆管理
│   │   ├── __init__.py
│   │   ├── context.py            # 对话上下文管理
│   │   └── database.py           # SQLite操作
│   │
│   ├── triggers/                 # 触发器模块
│   │   ├── __init__.py
│   │   ├── mention.py            # @触发
│   │   ├── keyword.py            # 关键词触发
│   │   ├── smart.py              # 智能判断
│   │   └── scheduler.py          # 定时任务
│   │
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       ├── logger.py             # 日志工具
│       └── helpers.py            # 辅助函数
│
├── data/
│   ├── bot.db                    # SQLite数据库
│   └── logs/                     # 日志目录
│       ├── bot-2026-02-06.log
│       └── error-2026-02-06.log
│
├── requirements.txt              # Python依赖
├── .gitignore                    # Git忽略文件
├── README.md                     # 使用说明
├── run.bat                       # Windows启动脚本
└── install.bat                   # Windows安装脚本
```

---

## 七、核心流程设计

### 7.1 消息处理主流程

```
┌─────────────────┐
│   收到QQ消息    │
└────────┬────────┘
         ↓
┌─────────────────┐
│  判断消息类型   │
└────────┬────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌───────┐  ┌───────┐
│ 私聊  │  │ 群聊  │
└───┬───┘  └───┬───┘
    ↓          ↓
┌───────┐  ┌───────────┐
│检查   │  │ 检查群号  │
│发送者 │  └─────┬─────┘
└───┬───┘        ↓
    ↓      ┌───────────┐
┌───────┐  │ 是否目标群│
│管理员?│  └─────┬─────┘
└───┬───┘        ↓
    ↓       ┌────────┐
   是/否   │ 是/否  │
    ↓       ↓        ↓
┌──────┐ ┌────┐  ┌────┐
│处理  │ │忽略│  │触发│
│回复  │ │    │  │器  │
└──────┘ └────┘  └─┬──┘
                   ↓
           ┌───────┴───────┐
           │  @触发？      │
           ├─ 是 → 处理   │
           │  否 ↓        │
           │  关键词？    │
           ├─ 是 → 处理   │
           │  否 ↓        │
           │  智能判断？  │
           └─ 是 → 处理   │
           │  否 → 忽略   │
           └──────────────┘
```

### 7.2 AI回复流程

```
┌──────────────┐
│ 触发器激活   │
└──────┬───────┘
       ↓
┌──────────────┐
│ 加载上下文   │
│ (最近N条)    │
└──────┬───────┘
       ↓
┌──────────────┐
│ 构建AI请求   │
│ - 系统提示   │
│ - 历史消息   │
│ - 当前消息   │
└──────┬───────┘
       ↓
┌──────────────┐
│ 调用AI API   │
└──────┬───────┘
       ↓
   ┌───┴───┐
   ↓       ↓
┌────┐  ┌────┐
│成功│  │失败│
└─┬──┘  └─┬──┘
  ↓       ↓
┌────┐  ┌─────┐
│发送│  │重试 │
│回复│  │降级 │
└─┬──┘  └─────┘
  ↓
┌──────────────┐
│ 更新上下文   │
└──────────────┘
```

### 7.3 定时任务流程

```
┌──────────────┐
│ 定时器触发   │
└──────┬───────┘
       ↓
┌──────────────┐
│ 任务类型判断 │
└──────┬───────┘
       ↓
   ┌───┴────┬────────┐
   ↓        ↓        ↓
┌────┐  ┌────┐  ┌────┐
│早安│  │晚安│  │话题│
└─┬──┘  └─┬──┘  └─┬──┘
  ↓       ↓       ↓
┌────┐  ┌────┐  ┌────┐
│随机│  │随机│  │判断│
│选择│  │选择│  │概率│
│消息│  │消息│  └─┬──┘
└─┬──┘  └─┬──┘    ↓
  ↓       ↓    ┌────┐
┌────┐  ┌────┐  │触发│
│发送│  │发送│  │/跳过│
│消息│  │消息│  └────┘
└────┘  └────┘
```

---

## 八、错误处理与稳定性

### 8.1 风险点与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| AI API超时/失败 | 无法回复 | 递增重试(1s→3s→5s)，连续3次失败降级 |
| API限流/余额不足 | 大量失败 | 监控API状态，切换备用API |
| 消息发送失败 | QQ风控 | 敏感词过滤，长度限制，失败日志 |
| 上下文太长 | API拒绝 | 限制20条，超时清理，异常重置 |
| 定时任务冲突 | API压力 | 错峰执行，随机延迟，队列管理 |
| NapCat崩溃 | 离线 | 日志监控，看门狗重启 |
| 数据库损坏 | 数据丢失 | 定期备份，异常恢复 |

### 8.2 日志设计

**日志级别**：
- **DEBUG**：详细调试信息（开发阶段）
- **INFO**：关键操作（消息收发、定时任务）
- **WARNING**：可恢复异常（API重试、消息过滤）
- **ERROR**：严重错误（API连续失败、NapCat断连）

**日志格式**：
```
[2026-02-06 10:00:00] [INFO] [群] 收到@消息: "你好"
[2026-02-06 10:00:01] [INFO] [群] 调用AI，上下文3条消息
[2026-02-06 10:00:02] [INFO] [群] AI回复成功: "你好呀！"
[2026-02-06 10:00:03] [WARNING] [私聊] API调用失败，重试中(1/3)
[2026-02-06 10:00:05] [ERROR] [私聊] API连续失败3次，降级回复
```

**日志管理**：
- 按日期分割：`logs/bot-2026-02-06.log`
- 错误日志单独：`logs/error-2026-02-06.log`
- 自动清理：保留最近30天

---

## 九、安全与隐私

### 9.1 数据安全

- **API密钥保护**：`.env`文件不提交git，加入`.gitignore`
- **管理员权限**：私聊仅管理员可使用，防止滥用
- **敏感词过滤**：发送前检查违禁词，避免风控
- **数据备份**：定期备份SQLite数据库

### 9.2 QQ安全

- **小号测试**：先用QQ小号测试，避免主号风控
- **频率控制**：避免高频发消息，模仿真人行为
- **内容合规**：不发送违规内容，遵守社区规范

---

## 十、实施计划

### 10.1 阶段划分

**阶段1：环境搭建（1-2天）**
- 安装NTQQ、NapCat
- 配置NapCat，实现QQ登录
- 安装Python、NoneBot2
- 创建项目结构
- 配置基础环境

**阶段2：基础对话功能（3-5天）**
- 搭建NoneBot2项目框架
- 实现消息监听与路由
- 接入AI API（DeepSeek/通义）
- 实现群聊@回复
- 实现管理员私聊回复
- 实现对话上下文管理

**阶段3：扩展功能（3-5天）**
- 关键词触发
- 智能判断回复
- 定时任务（主动聊天）
- 配置文件管理
- 日志系统

**阶段4：测试与优化（2-3天）**
- 功能测试
- 稳定性测试（24小时运行）
- 性能优化
- 错误处理完善

**阶段5：部署与文档（1-2天）**
- Windows服务配置（开机自启）
- 编写部署文档
- 编写使用手册
- 最终验收

**总计：约2-3周**

### 10.2 里程碑

| 阶段 | 里程碑 | 验收标准 |
|------|--------|---------|
| 阶段1 | 环境就绪 | NapCat登录成功，NoneBot2运行 |
| 阶段2 | 基础对话 | @机器人能回复，有上下文记忆 |
| 阶段3 | 功能完整 | 所有触发方式正常工作 |
| 阶段4 | 稳定运行 | 24小时无崩溃，错误处理完善 |
| 阶段5 | 部署完成 | 开机自启，文档齐全 |

---

## 十一、后续扩展方向

### 11.1 功能增强

- **长期记忆**：接入Graphiti/Chroma向量数据库
- **语音功能**：语音识别与发送
- **图片识别**：理解图片内容，支持视觉对话
- **多群管理**：支持在多个群中部署，独立配置
- **插件系统**：支持第三方插件扩展功能

### 11.2 智能化提升

- **情感分析**：识别群成员情绪，智能调节回复
- **个性化回复**：记住不同成员的喜好
- **主动学习**：从群聊中学习新知识
- **统计功能**：群活跃度分析、话题统计

### 11.3 运维增强

- **Web管理界面**：可视化配置和监控
- **远程控制**：管理员远程管理机器人
- **多账号支持**：支持多个QQ账号同时运行
- **云部署**：支持Linux服务器部署

---

## 十二、参考资源

### 12.1 官方文档

- [NoneBot2文档](https://nonebot.dev/)
- [NapCat文档](https://github.com/NapNeko/NapCatQQ)
- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)

### 12.2 示例项目

- NoneBot2官方示例
- NapCat使用案例
- QQ机器人开源项目

---

## 附录

### A. 配置示例

完整的`config.yaml`和`.env`示例见第五章。

### B. 数据库初始化SQL

```sql
-- 创建数据库表
CREATE TABLE IF NOT EXISTS conversation_context (
    chat_type TEXT PRIMARY KEY,
    messages TEXT,
    message_count INTEGER DEFAULT 0,
    last_active DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
```

### C. 依赖列表

```
# requirements.txt
nonebot2[fastapi]>=2.3.0
nonebot-adapter-onebot>=2.4.0
httpx>=0.27.0
openai>=1.0.0  # DeepSeek兼容OpenAI API
apscheduler>=3.10.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

---

**文档结束**
