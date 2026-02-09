# QQ聊天机器人

基于 NoneBot2 + NapCat 的智能QQ聊天机器人，支持群聊互动、语义记忆和联网搜索。

## ✨ 功能特性

### 核心功能
- ✅ **@触发回复**：群成员@机器人时智能回复
- ✅ **关键词触发**：检测关键词自动回复（支持固定回复）
- ✅ **名字触发**：提到机器人名字时主动回复
- ✅ **智能判断**：AI判断是否需要参与对话
- ✅ **定时任务**：早安/晚安问候、随机话题
- ✅ **B站链接解析**：自动识别并解析B站视频/番剧链接

### 记忆系统（三层架构）
- ✅ **短期记忆**：内存缓存，最近30条消息，30分钟超时
- ✅ **长期记忆**：SQLite数据库，永久保存所有聊天记录
- ✅ **语义记忆**：Chroma向量数据库，智能搜索相关历史对话

### 群友管理（新增）
- ✅ **自动收集**：群友发言时自动记录信息
- ✅ **智能昵称**：AI推测简短昵称，管理员确认
- ✅ **生日管理**：设置生日，自动发送祝福
- ✅ **备注系统**：记录群友信息，AI对话时参考
- ✅ **退群通知**：群友退群时自动通知
- ✅ **信息查询**：查询群友详细信息和活跃度

### 增强功能
- ✅ **联网搜索**：实时获取网络信息（阿里云搜索API）
- ✅ **上下文理解**：记住对话历史，智能关联
- ✅ **人设系统**：可自定义机器人性格和说话风格

## 🚀 快速开始

### 1. 环境要求

- Windows 10/11
- Python 3.9+
- NapCat（已包含在项目中）

### 2. 安装

```bash
# 运行安装脚本（自动创建虚拟环境并安装依赖）
install.bat
```

### 3. 配置

#### 编辑 `config/config.yaml`

```yaml
bot:
  qq_number: "你的机器人QQ号"
  admin_qq: "管理员QQ号"
  target_group: "目标群号"

personality:
  name: "沉舟"
  nickname: "舟舟"
```

#### 编辑 `config/.env`

```env
# AI模型（DeepSeek）
DEEPSEEK_API_KEY=sk-xxxxx

# 联网搜索和向量模型（阿里云）
DASHSCOPE_API_KEY=sk-xxxxx
```

### 4. 启动

```bash
# 方式1：一键启动（推荐）
start_all.bat

# 方式2：分步启动
start_napcat.bat    # 先启动NapCat
start_bot.bat       # 再启动机器人
```

### 5. 停止

```bash
stop_all.bat
```

## 📁 项目结构

```
QQ Chatbot/
├── config/                    # 配置文件
│   ├── config.yaml           # 主配置
│   ├── config.yaml.example   # 配置模板
│   ├── .env                  # 环境变量（API密钥）
│   └── .env.example          # 环境变量模板
│
├── src/                      # 源代码
│   ├── bot.py               # 程序入口
│   ├── ai/                  # AI模块
│   │   ├── client.py        # DeepSeek客户端
│   │   ├── prompts.py       # 提示词管理
│   │   └── nickname_analyzer.py # 昵称分析器
│   ├── memory/              # 记忆系统 ⭐
│   │   ├── context.py       # 短期记忆（内存缓存）
│   │   ├── database.py      # 长期记忆（SQLite）
│   │   ├── vector_store.py  # 语义记忆（Chroma）
│   │   ├── memory_manager.py # 统一管理器
│   │   └── member_db.py     # 群友信息数据库
│   ├── plugins/             # 功能插件
│   │   ├── chat_handler.py  # 聊天处理
│   │   ├── bilibili.py      # B站链接解析
│   │   └── member_manager.py # 群友管理
│   ├── plugins/             # 插件
│   │   └── chat_handler.py  # @触发处理
│   ├── triggers/            # 触发器
│   │   ├── keyword.py       # 关键词触发
│   │   ├── name.py          # 名字触发
│   │   ├── smart.py         # 智能触发
│   │   └── scheduler.py     # 定时任务
│   └── utils/               # 工具
│       ├── config.py        # 配置管理
│       ├── logger.py        # 日志系统
│       ├── helpers.py       # 工具函数
│       └── web_search.py    # 联网搜索
│
├── data/                     # 数据目录
│   ├── bot.db               # SQLite数据库
│   ├── chroma/              # 向量数据库
│   └── logs/                # 日志文件
│
├── docs/                     # 文档
│   ├── DEPLOYMENT.md        # 部署文档
│   ├── WEB_SEARCH.md        # 搜索功能文档
│   └── VECTOR_MEMORY.md     # 向量记忆文档
│
├── napcat/                   # NapCat（QQ协议）
│
├── install.bat              # 安装脚本
├── start_all.bat            # 一键启动
├── start_bot.bat            # 启动机器人
├── start_napcat.bat         # 启动NapCat
├── stop_all.bat             # 停止所有
└── requirements.txt         # Python依赖
```

## 🎯 使用示例

### 触发方式

1. **@触发**：`@沉舟 你好`
2. **名字触发**：`舟舟在吗`
3. **关键词触发**：`帮助`、`功能`、`/help`
4. **智能触发**：机器人自动判断是否回复

### 固定回复

- 发送 `帮助` 或 `/help` → 显示功能列表
- 发送 `功能` → 显示详细功能

### 群友管理命令（管理员）

**设置生日**：
- 群里：`/生日 @用户 12-25`
- 私聊：`/生日 QQ号 12-25`

**设置备注**（私聊）：
- `/备注 QQ号 喜欢摄影，经常分享风景照`

**设置昵称**：
- 群里：`/昵称 @用户 秋雪`
- 私聊：`/昵称 QQ号 秋雪`

**查询信息**：
- 群里：`/查询 @用户`（显示基础信息）
- 私聊：`/查询 QQ号`（显示完整信息含生日备注）

**活跃度统计**：
- `/统计`（显示发言排行榜）

### 语义记忆示例

```
用户A（一周前）："我喜欢吃火锅"
用户B（今天）："推荐个餐厅"
机器人：搜索记忆 → "记得有人说喜欢火锅，推荐海底捞"
```

## ⚙️ 配置说明

### 记忆系统配置

```yaml
conversation:
  max_messages: 30          # 短期记忆消息数
  timeout_minutes: 30       # 超时时间
  cache_size: 10            # 缓存会话数

memory:
  vector_db:
    enabled: true           # 是否启用向量数据库
    search_results: 5       # 搜索返回结果数
```

### 群友管理配置

```yaml
member_management:
  auto_collect: true        # 自动收集群友信息
  birthday_reminder: true   # 生日提醒
  reminder_time: "09:00"    # 提醒时间
  leave_notification: true  # 退群通知
  save_avatar: true         # 保存头像
```

### 功能开关

```yaml
features:
  mention_reply: true       # @回复
  keyword_reply: true       # 关键词回复
  name_reply: true          # 名字触发
  smart_reply: true         # 智能判断
  auto_chat: true           # 定时消息
  bilibili_parse: true      # B站链接解析
```

## 🔧 常见问题

### Q1: 如何获取API密钥？

- **DeepSeek**: https://platform.deepseek.com/
- **阿里云**: https://dashscope.aliyuncs.com/

### Q2: 机器人不回复？

1. 检查 NapCat 是否连接成功
2. 查看日志：`data/logs/bot-*.log`
3. 确认配置文件中的QQ号和群号正确

### Q3: 向量数据库初始化失败？

检查 `config/.env` 中的 `DASHSCOPE_API_KEY` 是否配置

### Q4: 如何关闭向量数据库？

修改 `config/config.yaml`：
```yaml
memory:
  vector_db:
    enabled: false
```

### Q5: 如何清空向量数据库？

删除 `data/chroma` 目录

## 📊 性能说明

- **响应速度**：短期记忆 5ms，向量搜索 200-500ms
- **内存占用**：约 200-500MB
- **磁盘占用**：1000条消息约 6MB（向量库）

## 📝 开发计划

- [x] 三层记忆系统
- [x] 联网搜索
- [x] 向量语义记忆
- [ ] 图片收发
- [ ] 语音识别
- [ ] 多群支持
- [ ] Web管理界面

## 📄 许可证

MIT License
