# QQ聊天机器人

基于 NoneBot2 + NapCat 的智能QQ聊天机器人，支持群聊互动和管理员私聊。

## 功能特性

- ✅ **@触发回复**：群成员@机器人时智能回复
- ✅ **关键词触发**：检测关键词自动回复
- ✅ **智能判断**：AI判断是否需要参与对话
- ✅ **对话记忆**：维护短期上下文（最多20条消息）
- ✅ **定时任务**：早安/晚安问候、随机话题
- ✅ **管理员私聊**：仅管理员可私聊机器人

## 快速开始

### 1. 环境要求

- Windows 10/11
- Python 3.9+
- NapCat（从 https://napneko.github.io/ 下载 Shell 版本）

### 2. 安装步骤

```bash
# 1. 克隆项目
git clone <repository_url>
cd qq-chatbot

# 2. 运行安装脚本
install.bat

# 3. 配置文件
# 编辑 config/config.yaml - 配置QQ号、群号等
# 编辑 config/.env - 配置AI API密钥
```

### 3. 配置说明

#### config/config.yaml

```yaml
bot:
  qq_number: "123456789"      # 机器人QQ号
  admin_qq: "987654321"       # 管理员QQ号
  target_group: "111222333"   # 目标群号
```

#### config/.env

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
```

### 4. 启动机器人

```bash
# 方式1：使用启动脚本
run.bat

# 方式2：手动启动
venv\Scripts\activate
python src/bot.py
```

## 项目结构

```
qq-chatbot/
├── config/              # 配置文件
│   ├── config.yaml      # 主配置
│   └── .env             # 环境变量
├── src/
│   ├── bot.py           # 程序入口
│   ├── ai/              # AI模块
│   ├── memory/          # 记忆管理
│   ├── plugins/         # NoneBot2插件
│   ├── triggers/        # 触发器
│   └── utils/           # 工具函数
├── data/                # 数据目录
│   ├── bot.db           # SQLite数据库
│   └── logs/            # 日志文件
├── requirements.txt     # Python依赖
├── install.bat          # 安装脚本
└── run.bat              # 启动脚本
```

## 常见问题

### Q: 如何获取API密钥？

- DeepSeek: https://platform.deepseek.com/
- 通义千问: https://dashscope.aliyuncs.com/

### Q: 机器人不回复消息？

1. 检查配置文件中的QQ号和群号是否正确
2. 查看日志文件 `data/logs/bot-*.log`
3. 确认NapCat已正常连接

### Q: 如何修改回复风格？

编辑 `src/ai/prompts.py` 中的 `SYSTEM_PROMPT`

## 开发计划

- [ ] 长期记忆（向量数据库）
- [ ] 多群支持
- [ ] Web管理界面
- [ ] 语音识别
- [ ] 图片识别

## 许可证

MIT License
