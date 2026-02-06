# API配置指南

## DeepSeek

### 1. 注册账号

访问：https://platform.deepseek.com/

### 2. 获取API密钥

1. 登录后进入控制台
2. 点击"API Keys"
3. 创建新的API密钥
4. 复制密钥（只显示一次）

### 3. 配置

编辑 `config/.env`：

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 4. 定价

- 输入：¥1/百万tokens
- 输出：¥2/百万tokens

**预估成本**：
- 单次对话：约0.001-0.005元
- 每天100次对话：约0.1-0.5元
- 每月：约3-15元

### 5. 特点

- ✅ 性价比极高
- ✅ 中文效果好
- ✅ 响应速度快
- ✅ 兼容OpenAI API

---

## 通义千问

### 1. 注册账号

访问：https://dashscope.aliyuncs.com/

### 2. 获取API密钥

1. 登录阿里云
2. 进入DashScope控制台
3. 创建API Key
4. 复制密钥

### 3. 配置

编辑 `config/.env`：

```env
AI_PROVIDER=qwen
QWEN_API_KEY=sk-xxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 4. 定价

**qwen-plus**：
- 输入：¥0.4/百万tokens
- 输出：¥1.2/百万tokens

**qwen-turbo**（更便宜）：
- 输入：¥0.3/百万tokens
- 输出：¥0.6/百万tokens

### 5. 特点

- ✅ 阿里云生态
- ✅ 中文优化
- ✅ 稳定可靠
- ✅ 多模型选择

---

## 切换AI提供商

### 方法1：修改配置文件

编辑 `config/.env`：

```env
# 切换到DeepSeek
AI_PROVIDER=deepseek

# 或切换到通义千问
AI_PROVIDER=qwen
```

### 方法2：双API配置（推荐）

同时配置两个API，作为备用：

```env
AI_PROVIDER=deepseek

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 通义千问配置（备用）
QWEN_API_KEY=sk-xxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

当主API失败时，可快速切换。

---

## API使用优化

### 1. 控制Token消耗

**减少上下文长度**：

```yaml
conversation:
  max_messages: 10  # 从20减少到10
```

**降低触发频率**：

```yaml
smart_reply:
  trigger_rate: 0.2  # 从0.3降低到0.2
```

### 2. 监控API使用

查看日志中的API调用次数：

```bash
findstr "AI回复成功" data\logs\bot-*.log | find /c /v ""
```

### 3. 设置预算提醒

在API提供商控制台设置：
- 每日消费上限
- 余额不足提醒

### 4. 优化提示词

更短的提示词 = 更少的Token消耗

---

## 常见问题

### Q: API密钥无效

**检查**：
1. 密钥是否正确复制
2. 是否有多余的空格
3. 密钥是否已过期

### Q: API调用失败

**可能原因**：
1. 网络问题
2. 余额不足
3. API限流
4. 服务器故障

**解决方案**：
1. 检查网络连接
2. 查看账户余额
3. 降低调用频率
4. 切换备用API

### Q: 如何降低成本

**建议**：
1. 减少上下文长度
2. 降低智能判断触发率
3. 使用更便宜的模型
4. 关闭不必要的功能

### Q: 哪个API更好

**DeepSeek**：
- 性价比最高
- 适合预算有限

**通义千问**：
- 稳定性更好
- 适合商业使用

**建议**：先用DeepSeek，如有需要再切换
