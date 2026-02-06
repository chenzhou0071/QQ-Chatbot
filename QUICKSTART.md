# 快速开始指南

## 5分钟快速部署

### 前置条件

- ✅ Windows 10/11
- ✅ Python 3.9+ 已安装
- ✅ NTQQ客户端已安装并登录
- ✅ NapCat已安装并配置

### 步骤1：安装项目（2分钟）

```bash
# 1. 进入项目目录
cd qq-chatbot

# 2. 运行安装脚本
install.bat
```

等待依赖安装完成。

### 步骤2：配置机器人（2分钟）

#### 2.1 编辑 config/config.yaml

```yaml
bot:
  qq_number: "你的机器人QQ号"      # 必填
  admin_qq: "你的管理员QQ号"       # 必填
  target_group: "目标群号"         # 必填
```

#### 2.2 编辑 config/.env

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-你的API密钥    # 必填
```

**获取API密钥**：
- DeepSeek: https://platform.deepseek.com/
- 注册 → 创建API Key → 复制密钥

### 步骤3：测试配置（1分钟）

```bash
test.bat
```

如果看到 "✅ 所有测试通过！"，说明配置正确。

### 步骤4：启动机器人

```bash
run.bat
```

看到以下日志说明启动成功：
```
[INFO] NoneBot2 启动成功
[INFO] AI客户端初始化完成: deepseek
[INFO] 数据库初始化完成
```

### 步骤5：测试功能

1. **测试@回复**：在群里@机器人，发送"你好"
2. **测试关键词**：发送"天气"
3. **测试私聊**：管理员私聊机器人

---

## 常见问题

### Q: install.bat 报错

**解决**：
1. 确认Python已安装：`python --version`
2. 确认网络正常（需要下载依赖包）

### Q: test.bat 提示配置未完成

**解决**：
1. 检查 config.yaml 中的QQ号是否正确
2. 检查 .env 中的API密钥是否正确

### Q: 机器人不回复

**解决**：
1. 确认NapCat已启动
2. 查看日志：`data/logs/bot-*.log`
3. 确认群号配置正确

---

## 下一步

- 📖 阅读 [使用文档](docs/USAGE.md) 了解所有功能
- 🔧 阅读 [部署文档](docs/DEPLOYMENT.md) 配置开机自启
- 💰 阅读 [API文档](docs/API.md) 了解成本优化

---

## 获取帮助

遇到问题？
1. 查看日志文件
2. 阅读完整文档
3. 提交Issue
