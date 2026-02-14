# API参考文档

## 核心API

### 记忆管理器 (MemoryManager)

#### `add_message(chat_type, role, content, sender_id, sender_name)`
添加消息到三层记忆系统

**参数**:
- `chat_type` (str): 聊天类型 ("group" | "private")
- `role` (str): 角色 ("user" | "assistant")
- `content` (str): 消息内容
- `sender_id` (str): 发送者QQ号
- `sender_name` (str): 发送者昵称

**示例**:
```python
memory_manager.add_message(
    chat_type="group",
    role="user",
    content="你好",
    sender_id="123456",
    sender_name="张三"
)
```

#### `get_context_for_ai(chat_type, current_query)`
获取AI所需的完整上下文

**返回**: List[Dict[str, str]] - 消息列表

---

### 意图分析器 (IntentAnalyzer)

#### `analyze(message, sender_id, context)`
分析消息意图

**返回**: IntentResult对象
- `type`: 意图类型
- `is_counter_question`: 是否为反问
- `is_sarcastic`: 是否讽刺
- `topic`: 当前话题
- `confidence`: 置信度

---

### 主动对话引擎 (ProactiveEngine)

#### `check_and_generate(group_id, mood)`
检查是否需要主动发言并生成话题

**返回**: Optional[str] - 话题内容或None

---

## 配置API

### 配置管理器 (Config)

#### `get(key, default)`
获取配置值，支持点号路径

**示例**:
```python
config.get("dialogue_intelligence.intent.enabled", False)
```

---

## 完整API文档

详见各模块的源代码文档字符串。
