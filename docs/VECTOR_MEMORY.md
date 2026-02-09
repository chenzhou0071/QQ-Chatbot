# 向量记忆系统使用说明

## 功能介绍

向量记忆系统为机器人添加了"智能记忆"能力，可以理解对话的语义并进行模糊搜索。

### 三层记忆架构

```
1. 短期记忆（内存缓存）
   - 最近30条对话
   - 30分钟超时
   - 响应速度：5ms

2. 长期记忆（SQLite数据库）
   - 所有聊天记录
   - 永久保存
   - 精确查询

3. 语义记忆（Chroma向量库）⭐ 新增
   - 理解对话含义
   - 模糊搜索
   - 智能关联
```

---

## 实际效果

### 场景1：记住历史信息

**没有向量库：**
- 用户："上周说的那个餐厅叫什么？"
- 机器人："我不记得了" ❌

**有向量库：**
- 用户："上周说的那个餐厅叫什么？"
- 机器人自动搜索 → "是海底捞吗？" ✅

### 场景2：记住用户喜好

**没有向量库：**
- 一周前："我喜欢吃火锅"
- 今天："推荐个餐厅"
- 机器人："随便推荐" ❌

**有向量库：**
- 一周前："我喜欢吃火锅"
- 今天："推荐个餐厅"
- 机器人搜索记忆 → "你喜欢火锅，推荐海底捞" ✅

---

## 技术实现

### 使用阿里云 Embedding API

- **模型**：text-embedding-v1
- **API Key**：与联网搜索共用（DashScope）
- **向量维度**：1536
- **存储方式**：本地持久化（data/chroma/）

### 工作流程

```
用户发消息
    ↓
1. 保存到 SQLite（结构化）
    ↓
2. 调用阿里云API生成向量 → 保存到 Chroma
    ↓
3. AI回复前搜索相关记忆
    ↓
4. 带着记忆生成回复
```

---

## 配置说明

### config.yaml

```yaml
# 记忆配置
memory:
  vector_db:
    enabled: true                 # 是否启用向量数据库
    persist_dir: "data/chroma"    # 向量库存储路径
    search_results: 3             # 搜索返回结果数
```

### 环境变量（.env）

```env
# 阿里云API Key（与联网搜索共用）
DASHSCOPE_API_KEY=sk-xxxxx
```

---

## 安装步骤

### 1. 安装依赖

```bash
pip install chromadb>=0.4.22
```

或运行：

```bash
install.bat
```

### 2. 配置API Key

确保 `config/.env` 中已配置：

```env
DASHSCOPE_API_KEY=你的阿里云API密钥
```

### 3. 启动机器人

```bash
start_all.bat
```

首次启动会自动创建向量数据库目录。

---

## 数据存储

### 目录结构

```
data/
├── bot.db              # SQLite数据库
├── chroma/             # 向量数据库（新增）
│   ├── chroma.sqlite3
│   └── ...
└── logs/               # 日志文件
```

### 数据量估算

- 每条消息约 6KB（向量 + 元数据）
- 1000条消息 ≈ 6MB
- 10000条消息 ≈ 60MB

---

## 性能说明

### API调用

- **添加记忆**：每条消息调用1次 Embedding API
- **搜索记忆**：每次查询调用1次 Embedding API
- **响应时间**：约 200-500ms

### 成本估算（阿里云）

- text-embedding-v1：免费额度内
- 超出后按量计费（很便宜）

---

## 常见问题

### Q1：向量库初始化失败？

**原因**：API Key未配置或无效

**解决**：
1. 检查 `config/.env` 中的 `DASHSCOPE_API_KEY`
2. 确认API Key有效且有余额

### Q2：搜索不到历史记忆？

**原因**：
- 向量库未启用
- 相似度太低（distance > 0.5）

**解决**：
1. 确认 `memory.vector_db.enabled: true`
2. 增加 `search_results` 数量

### Q3：如何清空向量库？

**方法1**：删除目录
```bash
rmdir /s /q data\chroma
```

**方法2**：代码清空
```python
from src.memory.vector_store import get_vector_store
vector_store = get_vector_store()
vector_store.clear_all()
```

### Q4：可以关闭向量库吗？

可以，修改配置：

```yaml
memory:
  vector_db:
    enabled: false
```

机器人会退化为只有短期+长期记忆。

---

## 调试命令

### 查看记忆统计

```python
from src.memory.memory_manager import get_memory_manager
manager = get_memory_manager()
print(manager.get_stats())
```

输出示例：

```json
{
  "short_term": {
    "cached_chats": ["group", "private"],
    "cache_size": 2,
    "cache_limit": 10
  },
  "vector_store": {
    "total_memories": 156,
    "collection_name": "chat_memory"
  }
}
```

---

## 注意事项

1. **API调用频率**：每条消息都会调用API，注意配额
2. **数据隐私**：向量数据存储在本地，但生成向量需要发送到阿里云
3. **磁盘空间**：向量库会随聊天增长，定期清理
4. **首次启动**：会下载依赖，可能较慢

---

## 更新日志

### v1.0.0 (2026-02-09)

- ✅ 集成 Chroma 向量数据库
- ✅ 使用阿里云 Embedding API
- ✅ 三层记忆系统
- ✅ 自动语义搜索
- ✅ 记忆注入到AI上下文
