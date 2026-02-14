# 对话智能增强系统设���文档

**创建日期**: 2026-02-12
**作者**: Claude + 用户协作设计
**状态**: 设计阶段

---

## 一、概述

### 1.1 目标

提升QQ聊天机器人的核心对话能力，使其能够：

1. **理解复杂对话**: 处理反问、讽刺、话题切换、矛盾信息等复杂场景
2. **主动发起对���**: 从被动响应转变为主动互动，在适当时机破冰、插话
3. **增强上下文理解**: 更好地维护对话状态和话题连贯性

### 1.2 设计原则

- **非侵入式**: 在现有架构基础上扩展，不破坏已有功能
- **模块化**: 各组件独立，便于测试和维护
- **可配置**: 所有关键参数可调，支持运行时修改
- **渐进式**: 分阶段实施，每个阶段可独立交付

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        现有系统                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  触发器层     │ ──→  │  记忆系统     │ ──→  │   AI客户端    │  │
│  │ (@/关键词/   │      │  (三层架构)   │      │  (DeepSeek)  │  │
│  │  智能判断)   │      │              │      │              │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    新增: 对话智能模块                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    意图分析器                               │ │
│  │  - 反问检测    - 讽刺识别    - 话题追踪    - 矛盾检测       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   上下文增强器                               │ │
│  │  - 对话状态机  - 话题索引    - 反问历史                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  主动对话引擎                               │ │
│  │  - 冷场检测    - 氛围分析    - 话题生成    - 插话判断       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

新增 `src/dialogue/` 目录：

```
src/dialogue/
├── __init__.py
├── intent_analyzer.py      # 意图分析器
├── context_enhancer.py      # 上下文增强器
├── proactive_engine.py       # 主动对话引擎
├── mood_analyzer.py         # 氛围分析器
├── topic_tracker.py         # 话题追踪器
└── dialogue_state.py         # 对话状态定义
```

---

## 三、核心组件设计

### 3.1 意图分析器 (`intent_analyzer.py`)

#### 3.1.1 功能概述

分析用户消息的深层意图，为AI生成提供额外的理解维度。

#### 3.1.2 反问检测

**实现方式**:
```python
class CounterQuestionDetector:
    def __init__(self):
        self.question_stack = []  # 存储最近的问题
        self.patterns = [
            r"你呢\??",
            r"那你呢\??",
            r"你.*怎么样\??",
            r"你.*呢\??"
        ]

    def detect(self, message: str) -> Optional[Dict]:
        """检测是否为反问

        Returns:
            {
                "is_counter": True,
                "original_question": "你平时玩什么游戏",
                "context": ["游戏讨论"]
            }
        """
        if not self._match_pattern(message):
            return None

        original = self.question_stack.pop()
        return {
            "is_counter": True,
            "original_question": original["question"],
            "context": original["context"]
        }

    def register_question(self, question: str, context: List[str]):
        """机器人发问时注册"""
        self.question_stack.append({
            "question": question,
            "context": context,
            "timestamp": time.time()
        })
        # 只保留最近3个问题
        if len(self.question_stack) > 3:
            self.question_stack.pop(0)
```

**集成点**: 在 `ai_client.chat()` 返回回复后，检测回复中包含问句时注册。

#### 3.1.3 讽刺识别

**实现方式**:
```python
class SarcasmDetector:
    # 讽刺特征集
    FEATURES = {
        "punctuation": ["~", "。。。", "。。。", "!!!"],
        "tone_words": ["呵", "切", "哟", "哦~", "嗯呢"],
        "reverse_patterns": [
            r"(真|太|好|棒|厉害).{0,5}(呢|呀|呗|哦)",
            r"可真.{2,4}呢"
        ],
        "context_mismatch": ["positive_words", "negative_context"]
    }

    def detect(self, message: str, context: str) -> Dict:
        """检测讽刺

        Returns:
            {
                "is_sarcastic": True,
                "confidence": 0.75,
                "reason": "punctuation+mismatch"
            }
        """
        score = 0
        reasons = []

        # 1. 标点符号检测
        if any(p in message for p in self.FEATURES["punctuation"]):
            score += 0.3
            reasons.append("punctuation")

        # 2. 语气词检测
        if any(w in message for w in self.FEATURES["tone_words"]):
            score += 0.2
            reasons.append("tone_words")

        # 3. 语境矛盾检测（轻量级AI调用）
        mismatch_score = self._check_context_mismatch(message, context)
        if mismatch_score > 0.5:
            score += 0.4
            reasons.append("context_mismatch")

        # 阈值判断
        is_sarcastic = score >= 0.6
        return {
            "is_sarcastic": is_sarcastic,
            "confidence": min(score, 1.0),
            "reasons": reasons
        }

    def _check_context_mismatch(self, message: str, context: str) -> float:
        """调用AI轻量级检测语境矛盾"""
        prompt = f"""判断这条消息是否与语境矛盾：

语境：{context[:200]}
消息：{message}

只返回0-1之间的分数，表示矛盾程度。"""
        # 使用轻量级模型
        response = ai_client.simple_chat(prompt)
        return float(response.strip())
```

#### 3.1.4 话题追踪

**实现方式**:
```python
class TopicTracker:
    def __init__(self):
        self.current_topic: Optional[Topic] = None
        self.topic_history: List[Topic] = []
        self.switch_threshold = 3  # 连续3条不相关消息触发切换

    def update(self, message: str, sender_id: str) -> TopicStatus:
        """更新话题状态

        Returns:
            {
                "status": "maintaining" | "switching" | "new",
                "current_topic": "...",
                "confidence": 0.85
            }
        """
        keywords = self._extract_keywords(message)

        if self.current_topic is None:
            # 创建新话题
            self.current_topic = Topic(
                id=uuid.uuid4(),
                name=keywords[0] if keywords else "闲聊",
                keywords=keywords,
                start_time=time.time(),
                participants=[sender_id]
            )
            return {"status": "new", **self.current_topic.to_dict()}

        # 检查相关性
        relevance = self._calculate_relevance(keywords, self.current_topic.keywords)

        if relevance < 0.3:
            self.irrelevant_count += 1
            if self.irrelevant_count >= self.switch_threshold:
                # 触发话题切换
                return self._switch_topic(message, sender_id)
        else:
            self.irrelevant_count = 0
            self.current_topic.update(message, sender_id)

        return {"status": "maintaining", **self.current_topic.to_dict()}

    def _extract_keywords(self, message: str) -> List[str]:
        """提取关键词（优先使用AI，降级使用jieba）"""
        # 调用AI提取关键词
        prompt = f"""从这条消息中提取2-3个关键词：

消息：{message}

只返回关键词，用逗号分隔。"""
        result = ai_client.simple_chat(prompt)
        return [k.strip() for k in result.split(",")[:3]]

    def _calculate_relevance(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算关键词相关性"""
        # 简单的Jaccard相似度
        set1, set2 = set(keywords1), set(keywords2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0
```

#### 3.1.5 矛盾检测

**实现方式**:
```python
class ContradictionDetector:
    def __init__(self):
        self.vector_store = get_memory_manager().vector_store

    def check(self, statement: str, user_id: str) -> Optional[Dict]:
        """检测用户言论是否与历史矛盾

        Returns:
            {
                "has_contradiction": True,
                "conflicting_statement": "我特别喜欢吃火锅",
                "similarity": 0.85,
                "sentiment": "opposite"
            }
        """
        # 1. 提取当前陈述的核心主张
        claim = self._extract_claim(statement)

        # 2. 从向量数据库搜索历史主张
        results = self.vector_store.search(
            query=claim,
            filter={"user_id": user_id, "type": "claim"},
            n_results=3
        )

        if not results:
            return None

        # 3. 分析情感倾向是否矛盾
        for result in results:
            sentiment_diff = self._compare_sentiment(claim, result["content"])
            if sentiment_diff > 0.7:  # 情感差异大
                return {
                    "has_contradiction": True,
                    "conflicting_statement": result["content"],
                    "similarity": result["similarity"],
                    "sentiment": "opposite"
                }

        return None

    def _extract_claim(self, statement: str) -> str:
        """提取陈述的核心主张"""
        prompt = f"""提取这句话的核心观点（不超过15字）：

{statement}

只返回核心观点，不要解释。"""
        return ai_client.simple_chat(prompt)
```

---

### 3.2 上下文增强器 (`context_enhancer.py`)

#### 3.2.1 对话状态机

**状态定义** (`dialogue_state.py`):
```python
from enum import Enum

class DialogueState(Enum):
    OPENING = "opening"       # 对话开启
    MAINTAINING = "maintaining"  # 维持话题
    SWITCHING = "switching"   # 话题切换
    CLOSING = "closing"       # 对话结束

class StateMachine:
    def __init__(self):
        self.current_state = DialogueState.OPENING
        self.state_duration = 0
        self.message_count = 0

    def transition(self, intent: Dict, message_interval: float) -> DialogueState:
        """状态转换逻辑"""
        self.message_count += 1

        if self.current_state == DialogueState.OPENING:
            if self.message_count >= 2:
                return DialogueState.MAINTAINING

        elif self.current_state == DialogueState.MAINTAINING:
            if intent.get("topic_switching"):
                return DialogueState.SWITCHING
            if message_interval > 300:  # 5分钟无消息
                return DialogueState.CLOSING

        elif self.current_state == DialogueState.SWITCHING:
            # 切换状态维持2轮后进入维持
            if self.message_count % 2 == 0:
                return DialogueState.MAINTAINING

        elif self.current_state == DialogueState.CLOSING:
            return DialogueState.OPENING  # 重新开启

        return self.current_state
```

**Prompt模板增强**:
```python
def get_state_aware_prompt(state: DialogueState, base_prompt: str) -> str:
    """根据对话状态调整prompt"""

    state_instructions = {
        DialogueState.OPENING: """
【当前状态】对话刚开启
- 主动建立连接，问候或回应
- 表达友好和开放态度
- 可以提出开放性问题
""",
        DialogueState.MAINTAINING: """
【当前状态】深入讨论
- 保持话题连贯性
- 回顾之前的对话内容
- 可以追问细节或表达看法
""",
        DialogueState.SWITCHING: """
【当前状态】话题切换
- 自然过渡，不要突兀
- 可以总结上一话题
- 引入新话题时要平滑
""",
        DialogueState.CLOSING: """
【当前状态】对话收尾
- 总结对话要点
- 表达结束意愿
- 保持友好态度
"""
    }

    return base_prompt + state_instructions.get(state, "")
```

#### 3.2.2 话题索引

**数据结构**:
```python
@dataclass
class Topic:
    id: str
    name: str
    keywords: List[str]
    start_time: float
    last_active: float
    participants: List[str]
    summary: str
    key_points: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)

    def update(self, message: str, participant: str):
        """更新话题信息"""
        self.last_active = time.time()
        if participant not in self.participants:
            self.participants.append(participant)
        # 定期更新summary（每5条消息）
        # ...
```

**话题切换过渡**:
```python
def generate_switching_prompt(old_topic: Topic, new_topic: Topic) -> str:
    """生成话题切换的过渡prompt"""
    return f"""
【话题切换】
上一个话题：{old_topic.name}
  - 参与者：{', '.join(old_topic.participants)}
  - 要点：{'; '.join(old_topic.key_points[:3])}

新话题：{new_topic.name}

过渡要求：
- 自然地从旧话题过渡到新话题
- 可以简单总结一下之前的讨论
- 不要突兀地直接切换
- 保持对话连贯性
"""
```

---

### 3.3 主动对话引擎 (`proactive_engine.py`)

#### 3.3.1 冷场检测器

**实现方式**:
```python
class ColdDetector:
    def __init__(self, config: Dict):
        self.thresholds = {
            "mild": config.get("cold_threshold_mild", 300),    # 5分钟
            "moderate": config.get("cold_threshold_moderate", 600),  # 10分钟
            "severe": config.get("cold_threshold_severe", 1200)  # 20分钟
        }
        self.probabilities = {
            "mild": 0.2,
            "moderate": 0.5,
            "severe": 0.8
        }
        self.last_message_time: Dict[str, float] = {}

    def check(self, group_id: str) -> Optional[Dict]:
        """检查群是否冷场

        Returns:
            {
                "is_cold": True,
                "level": "moderate",
                "duration": 420,
                "probability": 0.5
            }
        """
        last_time = self.last_message_time.get(group_id, time.time())
        duration = time.time() - last_time

        if duration < self.thresholds["mild"]:
            return None

        # 判断冷场等级
        if duration < self.thresholds["moderate"]:
            level = "mild"
        elif duration < self.thresholds["severe"]:
            level = "moderate"
        else:
            level = "severe"

        return {
            "is_cold": True,
            "level": level,
            "duration": duration,
            "probability": self.probabilities[level]
        }

    def update_last_message(self, group_id: str):
        """更新最后消息时间"""
        self.last_message_time[group_id] = time.time()
```

#### 3.3.2 氛围分析器 (`mood_analyzer.py`)

**实现方式**:
```python
class MoodAnalyzer:
    def __init__(self):
        self.message_buffer: List[Dict] = []
        self.buffer_size = 50  # 保留最近50条消息用于分析

    def analyze(self, group_id: str) -> MoodResult:
        """分析当前群聊氛围

        Returns:
            MoodResult {
                mood: "excited" | "calm" | "quiet" | "low",
                confidence: 0.75,
                metrics: {
                    msg_rate: 8.5,  # 消息/分钟
                    positive_ratio: 0.65,
                    emoji_count: 12,
                    interaction_count: 5
                }
            }
        """
        if not self.message_buffer:
            return MoodResult(mood="quiet", confidence=0.5, metrics={})

        # 1. 计算消息频率
        recent_messages = self._get_recent_messages(minutes=5)
        msg_rate = len(recent_messages) / 5

        # 2. 情感分析（积极 vs 消极）
        positive_count = sum(1 for m in recent_messages if self._is_positive(m))
        positive_ratio = positive_count / len(recent_messages)

        # 3. 交互指标
        interaction_count = sum(1 for m in recent_messages if self._is_interaction(m))

        # 4. 综合判断
        mood = self._classify_mood(msg_rate, positive_ratio, interaction_count)

        return MoodResult(
            mood=mood,
            confidence=self._calculate_confidence(msg_rate, positive_ratio),
            metrics={
                "msg_rate": msg_rate,
                "positive_ratio": positive_ratio,
                "interaction_count": interaction_count
            }
        )

    def _classify_mood(self, msg_rate: float, positive_ratio: float,
                       interaction_count: int) -> str:
        """根据指标分类氛围"""
        if msg_rate > 10 and positive_ratio > 0.7:
            return "excited"
        elif msg_rate < 1:
            return "quiet"
        elif positive_ratio < 0.3:
            return "low"
        else:
            return "calm"

    def _is_positive(self, message: Dict) -> bool:
        """判断消息情感倾向"""
        text = message["content"]
        # 简单关键词匹配（可升级为AI分析）
        positive_words = ["哈哈", "笑死", "棒", "厉害", "爱", "喜欢"]
        negative_words = ["难过", "伤心", "烦", "讨厌", "累了"]

        positive_score = sum(1 for w in positive_words if w in text)
        negative_score = sum(1 for w in negative_words if w in text)

        return positive_score > negative_score

    def _is_interaction(self, message: Dict) -> bool:
        """判断是否为交互型消息"""
        return "@" in message["content"] or "回复" in message
```

#### 3.3.3 话题生成器

**实现方式**:
```python
class TopicGenerator:
    def __init__(self, config: Dict):
        self.topic_sources = {
            "user_interests": True,
            "trending": True,
            "preset": True
        }
        self.recent_topics: List[str] = []
        self.preset_topics = self._load_preset_topics()

    def generate(self, mood: str, active_users: List[str]) -> Optional[str]:
        """生成合适的主动话题

        Args:
            mood: 当前氛围
            active_users: 活跃用户列表

        Returns:
            话题字符串或None
        """
        # 1. 排除最近讨论过的话题
        candidates = self._filter_recent_topics()

        # 2. 根据氛围筛选
        mood_suitable = self._filter_by_mood(candidates, mood)

        # 3. 根据活跃用户兴趣排序
        ranked = self._rank_by_user_interest(mood_suitable, active_users)

        # 4. 随机选择（Top 3中随机）
        if ranked:
            return random.choice(ranked[:3])

        return None

    def _filter_by_mood(self, topics: List[str], mood: str) -> List[str]:
        """根据氛围筛选话题"""
        mood_type_map = {
            "excited": ["娱乐", "游戏", "梗", "热门"],
            "calm": ["兴趣", "爱好", "经历", "想法"],
            "quiet": ["问候", "日常", "轻松"],
            "low": ["温暖", "鼓励", "安慰"]
        }

        keywords = mood_type_map.get(mood, [])
        return [t for t in topics if any(kw in t for kw in keywords)]

    def _rank_by_user_interest(self, topics: List[str],
                                users: List[str]) -> List[str]:
        """根据用户兴趣排序话题"""
        member_db = get_member_db()
        user_interests = []

        for user_id in users:
            member = member_db.get_member(user_id)
            if member and member.get("remark"):
                # 从备注中提取兴趣标签
                interests = self._extract_interests(member["remark"])
                user_interests.extend(interests)

        # 按匹配度排序
        scored = [(t, self._calculate_match(t, user_interests))
                   for t in topics]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [t[0] for t in scored]

    def _load_preset_topics(self) -> List[str]:
        """加载预设话题库"""
        return [
            "最近有看到什么有趣的事情吗",
            "大家平时都喜欢做什么",
            "分享一个最近的小确幸",
            "有什么推荐的剧或动漫吗",
            "聊聊你最近在玩什么游戏",
            # ...
        ]
```

#### 3.3.4 插话判断器

**实现方式**:
```python
class InterjectionJudge:
    def __init__(self, config: Dict):
        self.config = config.get("proactive.interject", {})
        self.recent_actions: List[Dict] = []  # 最近主动发言记录

    def should_interject(self, context: Dict) -> float:
        """判断是否应该插话

        Args:
            context: {
                "is_mentioned": bool,
                "is_relevant": bool,
                "is_private_chat": bool,
                "recent_active_count": int,
                "mood": str
            }

        Returns:
            插话概率 (0-1)
        """
        # 基础概率
        base_probability = 0.0

        # 1. 被提到
        if context["is_mentioned"]:
            return self.config.get("when_mentioned", 0.8)

        # 2. 私聊对话不插话
        if context["is_private_chat"]:
            return 0.0

        # 3. 话题相关
        if context["is_relevant"]:
            base_probability += self.config.get("when_relevant", 0.4)

        # 4. 冷场时
        if context.get("is_cold"):
            base_probability += context.get("cold_probability", 0.6)

        # 5. 检查冷却时间
        if self._is_in_cooldown():
            return 0.0

        # 6. 检查最近发言频率
        if self._is_too_active():
            return 0.0

        return min(base_probability, 1.0)

    def record_action(self, action_type: str):
        """记录主动行为"""
        self.recent_actions.append({
            "type": action_type,
            "timestamp": time.time()
        })
        # 清理旧记录
        self._cleanup_old_actions()

    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期"""
        cooldown = self.config.get("cooldown", 600)
        if not self.recent_actions:
            return False

        last_action = self.recent_actions[-1]
        return (time.time() - last_action["timestamp"]) < cooldown

    def _is_too_active(self) -> bool:
        """检查最近是否太活跃"""
        max_messages = self.config.get("max_recent_messages", 3)
        recent_count = len([a for a in self.recent_actions
                           if a["type"] == "proactive_message"])
        return recent_count >= max_messages
```

---

## 四、数据流设计

### 4.1 主流程（消息处理）

```python
async def enhanced_chat_handler(bot: Bot, event: GroupMessageEvent):
    """增强的聊天处理流程"""

    # 1. 基础信息提取
    message_text = extract_message_text(event)
    sender_info = extract_sender_info(event)

    # 2. 意图分析
    intent_result = intent_analyzer.analyze(
        message=message_text,
        context=memory_manager.get_recent_context()
    )

    # 3. 状态更新
    current_state = state_machine.transition(
        intent=intent_result,
        message_interval=get_message_interval()
    )

    # 4. 上下文增强
    enhanced_context = context_enhancer.enrich(
        base_context=memory_manager.get_context_for_ai(),
        intent=intent_result,
        state=current_state
    )

    # 5. AI生成回复
    reply = ai_client.chat(
        context=enhanced_context,
        intent_hints=intent_result,
        chat_type="group",
        sender_qq=sender_info["qq"]
    )

    # 6. 发送回复
    if reply:
        await send_message(reply)

        # 7. 更新记忆和状态
        memory_manager.add_message("assistant", reply)
        state_machine.record_reply(reply)

        # 8. 如果回复包含问句，注册到反问检测器
        if is_question(reply):
            counter_question_detector.register_question(
                question=reply,
                context=[current_state.topic]
            )
```

### 4.2 后台流程（主动对话）

```python
async def proactive_loop():
    """后台主动对话循环"""

    while True:
        await asyncio.sleep(config.get("proactive.check_interval", 60))

        # 1. 检查群消息时间
        cold_result = cold_detector.check(config.target_group)

        # 2. 分析氛围
        mood_result = mood_analyzer.analyze(config.target_group)

        # 3. 判断是否需要主动
        should_act = False
        action_probability = 0.0

        if cold_result and cold_result["is_cold"]:
            should_act = True
            action_probability = cold_result["probability"]

        # 氛围因素调整
        if mood_result.mood in ["excited", "calm"]:
            action_probability *= 1.2  # 提高主动概率

        # 4. 决策
        if should_act and random.random() < action_probability:
            # 生成话题
            topic = topic_generator.generate(
                mood=mood_result.mood,
                active_users=get_active_users()
            )

            if topic:
                # 生成消息
                message = generate_proactive_message(topic, mood_result.mood)

                # 发送
                await send_message(message)

                # 记录行为
                interjection_judge.record_action("proactive_message")
```

### 4.3 数据结构

```python
# 意图分析结果
@dataclass
class IntentResult:
    type: str  # "question", "counter_question", "sarcasm", "normal"
    topic: Optional[str]
    is_counter_question: bool = False
    is_sarcastic: bool = False
    has_contradiction: bool = False
    contradiction_info: Optional[Dict] = None
    confidence: float = 0.5

# 对话状态
@dataclass
class DialogueState:
    current_state: DialogueState
    message_count: int
    duration: float
    topic: Optional[Topic]

# 氛围分析结果
@dataclass
class MoodResult:
    mood: str  # "excited", "calm", "quiet", "low"
    confidence: float
    metrics: Dict[str, Any]
```

---

## 五、配置设计

### 5.1 配置文件 (`config/config.yaml`)

```yaml
# 对话智能模块配置
dialogue_intelligence:
  # 意图分析
  intent:
    enabled: true
    counter_question:
      enabled: true
      stack_size: 3  # 保留最近几个问题
    sarcasm_detection:
      enabled: true
      threshold: 0.6  # 置信度阈值
      use_ai_verification: true  # 使用AI二次确认
    topic_tracking:
      enabled: true
      switch_threshold: 3  # 几条不相关消息后切换
    contradiction_detection:
      enabled: true
      similarity_threshold: 0.7

  # 对话状态
  state_machine:
    enabled: true
    state_prompts: true  # 是否根据状态调整prompt

  # 主动对话
  proactive:
    enabled: true
    check_interval: 60  # 检查间隔（秒）

    # 冷场检测
    cold_detection:
      enabled: true
      thresholds:
        mild: 300      # 5分钟
        moderate: 600  # 10分钟
        severe: 1200   # 20分钟
      probabilities:
        mild: 0.2
        moderate: 0.5
        severe: 0.8

    # 氛围分析
    mood_analysis:
      enabled: true
      buffer_size: 50
      analysis_window: 300  # 分析最近5分钟

    # 话题生成
    topic_generation:
      enabled: true
      sources:
        user_interests: true
        trending: true
        preset: true
      recent_exclusion_hours: 24

    # 插话判断
    interject:
      cooldown: 600  # 冷却时间（秒）
      max_recent_messages: 3
      when_mentioned: 0.8
      when_relevant: 0.4
      when_cold: 0.6
```

---

## 六、测试策略

### 6.1 单元测试

```python
# tests/test_intent_analyzer.py
class TestIntentAnalyzer:
    def test_counter_question_detection(self):
        detector = CounterQuestionDetector()
        detector.register_question("你平时玩什么游戏", ["游戏"])

        result = detector.detect("你呢？")
        assert result["is_counter"] == True
        assert result["original_question"] == "你平时玩什么游戏"

    def test_sarcasm_detection(self):
        detector = SarcasmDetector()
        result = detector.detect("哇~你真聪明呢...", context="错误回答")
        assert result["is_sarcastic"] == True
        assert result["confidence"] > 0.6

    def test_topic_switching(self):
        tracker = TopicTracker()
        tracker.update("今天天气真好", "user1")

        # 连续不相关消息
        for _ in range(3):
            tracker.update("我饿了", "user2")

        result = tracker.update("吃什么好呢", "user3")
        assert result["status"] == "switching"
```

### 6.2 集成测试场景

**场景1：反问对话**
```
用户: "我最近在学Python"
机器人: "（好奇地）Python啊，你是用来做什么的呢？"
用户: "你呢？"
→ 预期：机器人回答自己的情况
```

**场景2：讽刺识别**
```
用户: "哇~你真聪明呢，居然能回答这种问题..."
机器人: （识别讽刺，委屈回应）
→ 预期：机器人理解讽刺，给出恰当反应
```

**场景3：冷场主动**
```
（群消息停止15分钟后）
→ 预期：机器人主动发起话题
```

---

## 七、实施计划

### 阶段一：意图分析器（1-2周）

- [ ] 实现反问检测
- [ ] 实现讽刺识别
- [ ] 单元测试
- [ ] 集成到现有聊天流程
- [ ] 验证测试

### 阶段二：上下文增强器（1-2周）

- [ ] 实现对话状态机
- [ ] 实现话题追踪
- [ ] 优化prompt模板
- [ ] 测试验证

### 阶段三：主动对话引擎（2-3周）

- [ ] 实现冷场检测
- [ ] 实现氛围分析
- [ ] 实现话题生成
- [ ] 实现插话判断
- [ ] 完整测试

### 阶段四：优化与调优（1周）

- [ ] 性能优化
- [ ] 人设调优
- [ ] 用户反馈收集
- [ ] 文档完善

**总计：5-8周**

---

## 八、风险与挑战

### 8.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI识别准确率不足 | 误判导致回复不当 | 设置合理阈值，允许一定误差，依赖情绪反应机制兜底 |
| 性能开销增加 | 响应延迟 | 使用异步处理，缓存机制，轻量级降级方案 |
| 主动消息过于频繁 | 引起用户反感 | 严格限制频率，提供配置开关 |

### 8.2 业务风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 人设不符 | 机器人性格不一致 | 所有主动行为必须符合人设，严格测试 |
| 话题不当 | 生成不合适话题 | 建立话题过滤机制，管理员可配置 |

---

## 九、成功指标

### 9.1 定量指标

- **反问识别准确率**: >80%
- **讽刺识别准确率**: >70%
- **话题切换响应时间**: <500ms
- **主动消息相关性**: >75%（用户认可度）
- **冷场破冰及时性**: 85%的冷场在15分钟内得到响应

### 9.2 定性指标

- 用户反馈：机器人"更聪明了"
- 对话流畅度：多轮对话更连贯
- 群氛围：机器人主动参与后群更活跃

---

## 十、后续扩展

- **情感记忆**: 记住用户的情感偏好
- **个性化**: 根据不同用户调整对话风格
- **多群适配**: 支持不同群的不同氛围策略
- **学习机制**: 从用户反馈中学习优化
- **语音支持**: 语音对话的情感分析
- **图片理解**: 结合图片的语境分析
