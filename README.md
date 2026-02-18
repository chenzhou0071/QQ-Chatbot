# QQ 聊天机器人

一个基于 NoneBot2 和 NapCat 的智能 QQ 群聊机器人，支持 Web 管理界面。

## ✨ 特性

- 🎭 **完全自定义人设** - 在 Web 界面自定义 Bot 的性格、外貌、说话风格
- 🧠 **三层记忆系统** - 短期记忆、长期记忆、语义记忆
- 💬 **智能对话** - 上下文理解、连续对话、主动插话
- 🌐 **联网搜索** - 自动联网获取实时信息
- 👥 **群友管理** - 记录群友信息、昵称、生日、备注
- 🎯 **多种触发方式** - @触发、名字触发、关键词触发、智能判断
- 🖥️ **Web 管理界面** - 实时日志、配置管理、Bot 控制

## 🚀 快速开始

### 1. 安装依赖

双击运行 `install.bat`，会自动：
- 创建 Python 虚拟环境
- 安装所有依赖包
- 初始化配置文件

### 2. 配置

编辑 `config/config.yaml` 和 `config/.env`：

```yaml
# config/config.yaml
bot:
  qq_number: '你的Bot QQ号'
  admin_qq: '管理员QQ号'
  target_group: '目标群号'
```

```env
# config/.env
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 3. 启动

双击运行 `启动.bat`，会自动：
- 启动 NapCat（扫码登录 QQ）
- 启动 Web 管理界面
- 打开浏览器访问 http://localhost:5000

在 Web 界面中点击"启动 Bot"即可开始使用！

## 📖 使用说明

### Web 管理界面

访问 http://localhost:5000 可以：

- **仪表盘** - 查看 Bot 状态、今日统计、实时日志
- **配置管理** - 修改 Bot 配置、AI 配置、人设配置
- **群友管理** - 查看和编辑群友信息
- **实时日志** - 查看 Bot 运行日志

### 触发方式

1. **@触发** - 在群里 @Bot
2. **名字触发** - 消息中包含 Bot 的名字或昵称
3. **关键词触发** - 配置的关键词（如"帮助"、"功能"）
4. **智能判断** - Bot 会根据上下文智能判断是否回复

### 人设自定义

在 Web 界面的"配置管理"页面，可以完全自定义：

- 基本信息（名字、昵称、背景故事）
- 外貌特征（身高、发型、五官、气质）
- 性格设定（核心性格、性格特质）
- 说话风格（语气、方式、回应风格）
- 管理员关系（管理员名字、关系描述）

## 🛠️ 技术栈

- **框架**: NoneBot2 + NapCat
- **AI**: DeepSeek / 阿里云通义千问
- **数据库**: SQLite + ChromaDB
- **Web**: Flask + Vue 3 + Socket.IO

## 📁 项目结构

```
QQ Chatbot/
├── config/              # 配置文件
├── data/                # 数据文件（数据库、日志）
├── src/                 # 源代码
│   ├── ai/             # AI 相关
│   ├── memory/         # 记忆系统
│   ├── plugins/        # 插件
│   ├── triggers/       # 触发器
│   └── utils/          # 工具函数
├── web/                 # Web 管理界面
│   ├── static/         # 静态资源
│   ├── templates/      # HTML 模板
│   └── app.py          # Flask 应用
├── napcat/             # NapCat 相关文件
├── 启动.bat            # 一键启动脚本
└── install.bat         # 安装脚本
```

## ⚠️ 注意事项

1. 需要 Python 3.11+
2. 需要有效的 AI API Key（DeepSeek 或阿里云）
3. 首次启动需要扫码登录 QQ
4. Bot 只在配置的目标群中工作

## 📝 更新日志

### v2.0.0 (2026-02-18)
- ✨ 新增 Web 管理界面
- ✨ 支持完全自定义人设
- ✨ 增强智能触发器（上下文理解）
- ✨ 新增群友管理功能
- 🎨 优化界面设计
- 🐛 修复连续对话检测

## 📄 许可证

MIT License
