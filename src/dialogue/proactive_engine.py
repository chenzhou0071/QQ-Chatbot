"""主动对话引擎"""
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("proactive_engine")


class ColdDetector:
    """冷场检测器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.thresholds = {
            "mild": config.get("thresholds", {}).get("mild", 300),        # 5分钟
            "moderate": config.get("thresholds", {}).get("moderate", 600), # 10分钟
            "severe": config.get("thresholds", {}).get("severe", 1200)     # 20分钟
        }
        self.probabilities = {
            "mild": config.get("probabilities", {}).get("mild", 0.2),
            "moderate": config.get("probabilities", {}).get("moderate", 0.5),
            "severe": config.get("probabilities", {}).get("severe", 0.8)
        }
        self.last_message_time: Dict[str, float] = {}
        
        logger.info("冷场检测器初始化完成")
    
    def check(self, group_id: str) -> Optional[Dict[str, Any]]:
        """检查群是否冷场
        
        Args:
            group_id: 群ID
            
        Returns:
            冷场信息或None
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
        
        logger.info(f"检测到冷场: {level} (持续 {duration:.0f}秒)")
        
        return {
            "is_cold": True,
            "level": level,
            "duration": duration,
            "probability": self.probabilities[level]
        }
    
    def update_last_message(self, group_id: str) -> None:
        """更新最后消息时间
        
        Args:
            group_id: 群ID
        """
        self.last_message_time[group_id] = time.time()


class InterjectionJudge:
    """插话判断器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cooldown: int = config.get("cooldown", 600)  # 冷却时间（秒）
        self.max_recent_messages: int = config.get("max_recent_messages", 3)
        self.when_mentioned: float = config.get("when_mentioned", 0.8)
        self.when_relevant: float = config.get("when_relevant", 0.4)
        self.when_cold: float = config.get("when_cold", 0.6)
        
        self.recent_actions: List[Dict[str, Any]] = []
        
        logger.info("插话判断器初始化完成")
    
    def should_interject(self, context: Dict[str, Any]) -> float:
        """判断是否应该插话
        
        Args:
            context: 上下文信息
            
        Returns:
            插话概率 (0-1)
        """
        # 基础概率
        base_probability = 0.0
        
        # 1. 被提到
        if context.get("is_mentioned"):
            return self.when_mentioned
        
        # 2. 私聊对话不插话
        if context.get("is_private_chat"):
            return 0.0
        
        # 3. 话题相关
        if context.get("is_relevant"):
            base_probability += self.when_relevant
        
        # 4. 冷场时
        if context.get("is_cold"):
            cold_prob = context.get("cold_probability", self.when_cold)
            base_probability += cold_prob
        
        # 5. 检查冷却时间
        if self._is_in_cooldown():
            logger.debug("在冷却期内，不插话")
            return 0.0
        
        # 6. 检查最近发言频率
        if self._is_too_active():
            logger.debug("最近太活跃，不插话")
            return 0.0
        
        return min(base_probability, 1.0)
    
    def record_action(self, action_type: str) -> None:
        """记录主动行为
        
        Args:
            action_type: 行为类型
        """
        self.recent_actions.append({
            "type": action_type,
            "timestamp": time.time()
        })
        # 清理旧记录（保留最近1小时）
        self._cleanup_old_actions()
        logger.debug(f"记录主动行为: {action_type}")
    
    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期
        
        Returns:
            是否在冷却期
        """
        if not self.recent_actions:
            return False
        
        last_action = self.recent_actions[-1]
        return (time.time() - last_action["timestamp"]) < self.cooldown
    
    def _is_too_active(self) -> bool:
        """检查最近是否太活跃
        
        Returns:
            是否太活跃
        """
        # 统计最近1小时的主动消息数
        recent_count = len([
            a for a in self.recent_actions
            if a["type"] == "proactive_message" and
            time.time() - a["timestamp"] < 3600
        ])
        return recent_count >= self.max_recent_messages
    
    def _cleanup_old_actions(self) -> None:
        """清理旧记录"""
        cutoff_time = time.time() - 3600  # 1小时前
        self.recent_actions = [
            a for a in self.recent_actions
            if a["timestamp"] > cutoff_time
        ]


class TopicGenerator:
    """话题生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recent_topics: List[str] = []
        self.recent_exclusion_hours: int = config.get("recent_exclusion_hours", 24)
        self.preset_topics = self._load_preset_topics()
        
        logger.info(f"话题生成器初始化完成，预设话题数: {len(self.preset_topics)}")
    
    def generate(self, mood: str = "calm", active_users: Optional[List[str]] = None) -> Optional[str]:
        """生成合适的主动话题
        
        Args:
            mood: 当前氛围
            active_users: 活跃用户列表
            
        Returns:
            话题字符串或None
        """
        # 1. 排除最近讨论过的话题
        candidates = self._filter_recent_topics()
        
        if not candidates:
            logger.warning("没有可用的话题")
            return None
        
        # 2. 根据氛围筛选
        mood_suitable = self._filter_by_mood(candidates, mood)
        
        if not mood_suitable:
            # 如果没有合适的，使用所有候选
            mood_suitable = candidates
        
        # 3. 随机选择（Top 3中随机）
        selected = random.choice(mood_suitable[:3])
        
        # 4. 记录已使用的话题
        self._record_topic(selected)
        
        logger.info(f"生成话题: {selected[:30]}...")
        return selected
    
    def _filter_recent_topics(self) -> List[str]:
        """排除最近讨论过的话题
        
        Returns:
            候选话题列表
        """
        return [t for t in self.preset_topics if t not in self.recent_topics]
    
    def _filter_by_mood(self, topics: List[str], mood: str) -> List[str]:
        """根据氛围筛选话题
        
        Args:
            topics: 话题列表
            mood: 氛围
            
        Returns:
            筛选后的话题列表
        """
        mood_keywords = {
            "excited": ["游戏", "好玩", "有趣", "分享"],
            "calm": ["最近", "平时", "喜欢", "推荐"],
            "quiet": ["大家", "怎么样", "在吗", "聊聊"],
            "low": ["还好吗", "怎么了", "加油"]
        }
        
        keywords = mood_keywords.get(mood, [])
        if not keywords:
            return topics
        
        # 筛选包含关键词的话题
        filtered = [t for t in topics if any(kw in t for kw in keywords)]
        
        return filtered if filtered else topics
    
    def _record_topic(self, topic: str) -> None:
        """记录已使用的话题
        
        Args:
            topic: 话题
        """
        self.recent_topics.append(topic)
        # 只保留最近10个
        if len(self.recent_topics) > 10:
            self.recent_topics.pop(0)
    
    def _load_preset_topics(self) -> List[str]:
        """加载预设话题库
        
        Returns:
            话题列表
        """
        return [
            # 轻松闲聊类
            "嗯...大家最近都在忙什么呀",
            "那个...有人在吗",
            "今天...过得怎么样",
            "呀...好安静",
            
            # 兴趣爱好类
            "最近有看到什么有趣的事情吗",
            "大家平时都喜欢做什么呢",
            "有什么推荐的剧或动漫吗",
            "聊聊你最近在玩什么游戏吧",
            
            # 分享类
            "分享一个最近的小确幸吧",
            "今天有什么开心的事吗",
            "最近有什么新发现吗",
            
            # 日常类
            "今天天气还不错呢",
            "大家都吃饭了吗",
            "周末有什么计划吗",
            
            # 温暖类
            "大家...还好吗",
            "要不要休息一下",
            "记得多喝水哦",
        ]


class ProactiveEngine:
    """主动对话引擎（主类）"""
    
    def __init__(self):
        self.config = get_config()
        self.proactive_config = self.config.get("dialogue_intelligence.proactive", {})
        
        # 初始化各个组件
        self.cold_detector: Optional[ColdDetector] = None
        self.interjection_judge: Optional[InterjectionJudge] = None
        self.topic_generator: Optional[TopicGenerator] = None
        
        # 根据配置初始化
        if self.proactive_config.get("cold_detection", {}).get("enabled", True):
            self.cold_detector = ColdDetector(
                self.proactive_config.get("cold_detection", {})
            )
        
        if self.proactive_config.get("interject", {}).get("enabled", True):
            self.interjection_judge = InterjectionJudge(
                self.proactive_config.get("interject", {})
            )
        
        if self.proactive_config.get("topic_generation", {}).get("enabled", True):
            self.topic_generator = TopicGenerator(
                self.proactive_config.get("topic_generation", {})
            )
        
        logger.info("主动对话引擎初始化完成")
    
    def check_and_generate(self, group_id: str, mood: str = "calm") -> Optional[str]:
        """检查是否需要主动发言并生成内容
        
        Args:
            group_id: 群ID
            mood: 当前氛围
            
        Returns:
            主动消息内容或None
        """
        if not self.cold_detector or not self.topic_generator or not self.interjection_judge:
            return None
        
        # 1. 检查冷场
        cold_result = self.cold_detector.check(group_id)
        
        if not cold_result:
            return None
        
        # 2. 判断是否应该插话
        context = {
            "is_cold": True,
            "cold_probability": cold_result["probability"],
            "is_private_chat": False,
            "is_mentioned": False,
            "is_relevant": False
        }
        
        probability = self.interjection_judge.should_interject(context)
        
        if probability == 0 or random.random() > probability:
            logger.debug(f"插话概率 {probability:.2f}，不发言")
            return None
        
        # 3. 生成话题
        topic = self.topic_generator.generate(mood=mood)
        
        if topic:
            # 记录行为
            self.interjection_judge.record_action("proactive_message")
            logger.info(f"生成主动消息: {topic}")
        
        return topic
    
    def update_message_time(self, group_id: str) -> None:
        """更新群消息时间
        
        Args:
            group_id: 群ID
        """
        if self.cold_detector:
            self.cold_detector.update_last_message(group_id)


# 全局实例
_proactive_engine: Optional[ProactiveEngine] = None


def get_proactive_engine() -> ProactiveEngine:
    """获取主动对话引擎实例
    
    Returns:
        ProactiveEngine实例
    """
    global _proactive_engine
    if _proactive_engine is None:
        _proactive_engine = ProactiveEngine()
    return _proactive_engine
