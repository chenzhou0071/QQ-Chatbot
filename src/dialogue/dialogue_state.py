"""对话状态定义"""
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class DialogueStateEnum(Enum):
    """对话状态枚举"""
    OPENING = "opening"           # 对话开启
    MAINTAINING = "maintaining"   # 维持话题
    SWITCHING = "switching"       # 话题切换
    CLOSING = "closing"           # 对话结束


@dataclass
class IntentResult:
    """意图分析结果"""
    type: str  # "question", "counter_question", "sarcasm", "normal"
    topic: Optional[str] = None
    is_counter_question: bool = False
    is_sarcastic: bool = False
    has_contradiction: bool = False
    contradiction_info: Optional[Dict[str, Any]] = None
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class Topic:
    """话题数据结构"""
    id: str
    name: str
    keywords: List[str]
    start_time: float
    last_active: float
    participants: List[str] = field(default_factory=list)
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    message_count: int = 0
    
    @classmethod
    def create(cls, name: str, keywords: List[str], participant: str) -> 'Topic':
        """创建新话题"""
        now = datetime.now().timestamp()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            keywords=keywords,
            start_time=now,
            last_active=now,
            participants=[participant]
        )
    
    def update(self, message: str, participant: str) -> None:
        """更新话题信息"""
        self.last_active = datetime.now().timestamp()
        if participant not in self.participants:
            self.participants.append(participant)
        self.message_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class MoodResult:
    """氛围分析结果"""
    mood: str  # "excited", "calm", "quiet", "low"
    confidence: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DialogueContext:
    """对话上下文"""
    state: DialogueStateEnum
    message_count: int
    duration: float
    topic: Optional[Topic] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'state': self.state.value,
            'message_count': self.message_count,
            'duration': self.duration,
            'topic': self.topic.to_dict() if self.topic else None
        }
        return result
