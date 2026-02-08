# 部署文档

## 环境准备

### 1. 安装NTQQ

1. 下载NTQQ客户端（新版QQ）
2. 安装并登录你的机器人QQ账号
3. 保持NTQQ运行

### 2. 安装NapCat

1. 访问 NapCat 官网：https://napneko.github.io/
2. 下载 **NapCat.Shell.Windows.Node.zip**（Windows Shell 版本）
3. 解压到项目的 `napcat` 目录
4. 运行 `napcat.bat` 启动 NapCat
5. 首次启动需要扫码登录机器人QQ账号
6. 配置 WebSocket 服务（默认端口 3001）

### 3. 安装Python环境

1. 下载Python 3.9+：https://www.python.org/downloads/
2. 安装时勾选"Add Python to PATH"
3. 验证安装：
   ```bash
   python --version
   ```

## 项目部署

### 1. 获取项目代码

```bash
git clone <repository_url>
cd qq-chatbot
```

### 2. 运行安装脚本

```bash
install.bat
```

脚本会自动：
- 创建Python虚拟环境
- 安装所有依赖包
- 生成配置文件模板

### 3. 配置机器人

#### 编辑 config/config.yaml

```yaml
bot:
  qq_number: "你的机器人QQ号"
  admin_qq: "管理员QQ号"
  target_group: "目标群号"

keywords:
  - "天气"
  - "时间"
  # 添加更多关键词...
```

#### 编辑 config/.env

```env
# 选择AI提供商
AI_PROVIDER=deepseek

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 或使用通义千问
# AI_PROVIDER=qwen
# QWEN_API_KEY=sk-xxxxxxxxxxxxx
```

### 4. 启动机器人

```bash
run.bat
```

## 验证部署

### 1. 检查日志

查看 `data/logs/bot-YYYY-MM-DD.log`，确认：
- NoneBot2启动成功
- 连接到NapCat成功
- AI客户端初始化成功

### 2. 测试功能

1. **@触发测试**：在群里@机器人，看是否回复
2. **关键词测试**：发送包含关键词的消息
3. **私聊测试**：管理员私聊机器人

## 开机自启（可选）

### 使用nssm注册Windows服务

1. 下载nssm：https://nssm.cc/download
2. 解压到项目目录
3. 以管理员身份运行CMD：

```bash
cd qq-chatbot
nssm install QQBot

# 在弹出的窗口中配置：
# Path: C:\path\to\qq-chatbot\venv\Scripts\python.exe
# Startup directory: C:\path\to\qq-chatbot
# Arguments: src/bot.py
```

4. 启动服务：
```bash
nssm start QQBot
```

## 常见问题

### Q: NoneBot2无法连接到NapCat

**解决方案**：
1. 确认NapCat已启动且WebSocket服务开启
2. 检查端口是否正确（默认3001）
3. 查看NapCat日志

### Q: AI调用失败

**解决方案**：
1. 检查API密钥是否正确
2. 确认账户余额充足
3. 检查网络连接

### Q: 机器人不回复消息

**解决方案**：
1. 确认配置文件中的QQ号和群号正确
2. 检查功能开关是否开启
3. 查看日志文件排查问题

### Q: 数据库错误

**解决方案**：
1. 删除 `data/bot.db`
2. 重启机器人（会自动重建数据库）

## 更新机器人

```bash
git pull
venv\Scripts\activate
pip install -r requirements.txt --upgrade
```

## 卸载

1. 停止机器人
2. 如果注册了服务：
   ```bash
   nssm stop QQBot
   nssm remove QQBot confirm
   ```
3. 删除项目目录
