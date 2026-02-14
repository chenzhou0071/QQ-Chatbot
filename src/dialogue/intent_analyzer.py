"""意图分析器"""
import re
import time
from typing import Optional, Dict, List, Any

from src.dialogue.dialogue_state import IntentResult, Topic
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("intent_analyzer")


class CounterQuestionDetector:
    """反问检测器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.question_stack: List[Dict[str, Any]] = []
        self.stack_size: int = config.get("stack_size", 3)
        
        # 反问模式
        self.patterns = [
            r"你呢\??",
            r"那你呢\??",
            r"你.*怎么样\??",
            r"你.*呢\??",
            r"你.*如何\??",
            r"你觉得呢\??",
            r"你说呢\??",
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        
        logger.info("反问检测器初始化完成")
    
    def detect(self, message: str) -> Optional[Dict[str, Any]]:
        """检测是否为反问
        
        Args:
            message: 用户消息
            
        Returns:
            反问信息或None
        """
        # 检查是否匹配反问模式
        if not self._match_pattern(message):
            return None
        
        # 检查问题栈是否为空
        if not self.question_stack:
            logger.debug("反问模式匹配，但问题栈为空")
            return None
        
        # 获取最近的问题
        original = self.question_stack[-1]
        
        # 检查时间间隔（超过5分钟的问题不算）
        if time.time() - original["timestamp"] > 300:
            logger.debug("反问检测：问题已过期")
            self.question_stack.pop()
            return None
        
        logger.info(f"检测到反问，原问题: {original['question']}")
        
        return {
            "is_counter": True,
            "original_question": original["question"],
            "context": original.get("context", []),
            "timestamp": original["timestamp"]
        }
    
    def register_question(self, question: str, context: Optional[List[str]] = None) -> None:
        """注册机器人发出的问题
        
        Args:
            question: 问题内容
            context: 上下文信息
        """
        self.question_stack.append({
            "question": question,
            "context": context or [],
            "timestamp": time.time()
        })
        
        # 只保留最近N个问题
        if len(self.question_stack) > self.stack_size:
            self.question_stack.pop(0)
        
        logger.debug(f"注册问题: {question}")
    
    def _match_pattern(self, message: str) -> bool:
        """检查消息是否匹配反问模式
        
        Args:
            message: 消息内容
            
        Returns:
            是否匹配
        """
        return any(pattern.search(message) for pattern in self.compiled_patterns)


class SarcasmDetector:
    """讽刺识别器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.threshold: float = config.get("threshold", 0.6)
        self.use_ai_verification: bool = config.get("use_ai_verification", True)
        
        # 讽刺特征
        self.punctuation_features = ["~", "。。。", "...", "!!!", "？？？"]
        self.tone_words = ["呵", "切", "哟", "哦~", "嗯呢", "呵呵", "哈哈哈哈"]
        self.reverse_patterns = [
            re.compile(r"(真|太|好|棒|厉害).{0,5}(呢|呀|呗|哦)", re.IGNORECASE),
            re.compile(r"可真.{2,4}呢", re.IGNORECASE),
            re.compile(r"(不愧是|果然是).{2,8}", re.IGNORECASE)
        ]
        
        logger.info("讽刺检测器初始化完成")
    
    def detect(self, message: str, context: str = "") -> Dict[str, Any]:
        """检测讽刺
        
        Args:
            message: 消息内容
            context: 上下文
            
        Returns:
            检测结果
        """
        score = 0.0
        reasons = []
        
        # 1. 标点符号检测
        if any(p in message for p in self.punctuation_features):
            score += 0.25
            reasons.append("punctuation")
        
        # 2. 语气词检测（提高权重）
        if any(w in message for w in self.tone_words):
            score += 0.35
            reasons.append("tone_words")
        
        # 3. 反向模式检测
        if any(pattern.search(message) for pattern in self.reverse_patterns):
            score += 0.35
            reasons.append("reverse_pattern")
        
        # 阈值判断
        is_sarcastic = score >= self.threshold
        
        if is_sarcastic:
            logger.info(f"检测到讽刺: {message[:30]}... (置信度: {score:.2f})")
        
        return {
            "is_sarcastic": is_sarcastic,
            "confidence": min(score, 1.0),
            "reasons": reasons
        }


class TopicTracker:
    """话题追踪器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.current_topic: Optional[Topic] = None
        self.topic_history: List[Topic] = []
        self.switch_threshold: int = config.get("switch_threshold", 3)
        self.irrelevant_count: int = 0
        
        logger.info("话题追踪器初始化完成")
    
    def update(self, message: str, sender_id: str) -> Dict[str, Any]:
        """更新话题状态
        
        Args:
            message: 消息内容
            sender_id: 发送者ID
            
        Returns:
            话题状态
        """
        keywords = self._extract_keywords(message)
        
        if self.current_topic is None:
            # 创建新话题
            topic_name = keywords[0] if keywords else "闲聊"
            self.current_topic = Topic.create(topic_name, keywords, sender_id)
            logger.info(f"创建新话题: {topic_name}")
            return {"status": "new", "topic": self.current_topic.to_dict()}
        
        # 检查相关性
        relevance = self._calculate_relevance(keywords, self.current_topic.keywords)
        
        if relevance < 0.3:
            self.irrelevant_count += 1
            logger.debug(f"不相关消息计数: {self.irrelevant_count}/{self.switch_threshold}")
            
            if self.irrelevant_count >= self.switch_threshold:
                # 触发话题切换
                return self._switch_topic(message, sender_id, keywords)
        else:
            self.irrelevant_count = 0
            self.current_topic.update(message, sender_id)
            logger.debug(f"维持话题: {self.current_topic.name}")
        
        return {"status": "maintaining", "topic": self.current_topic.to_dict()}
    
    def _switch_topic(self, message: str, sender_id: str, keywords: List[str]) -> Dict[str, Any]:
        """切换话题
        
        Args:
            message: 消息内容
            sender_id: 发送者ID
            keywords: 关键词列表
            
        Returns:
            话题状态
        """
        # 保存旧话题到历史
        if self.current_topic:
            self.topic_history.append(self.current_topic)
            # 只保留最近10个话题
            if len(self.topic_history) > 10:
                self.topic_history.pop(0)
        
        # 创建新话题
        topic_name = keywords[0] if keywords else "新话题"
        old_topic_name = self.current_topic.name if self.current_topic else "无"
        self.current_topic = Topic.create(topic_name, keywords, sender_id)
        self.irrelevant_count = 0
        
        logger.info(f"话题切换: {old_topic_name} -> {topic_name}")
        
        return {
            "status": "switching",
            "topic": self.current_topic.to_dict(),
            "old_topic": old_topic_name
        }
    
    def _extract_keywords(self, message: str) -> List[str]:
        """提取关键词（简化版，使用规则）
        
        Args:
            message: 消息内容
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（可以后续升级为AI提取）
        # 移除标点和停用词
        import jieba
        
        stopwords = {'的', '了', '是', '在', '我', '你', '他', '她', '它', '们',
                    '这', '那', '有', '和', '就', '不', '都', '而', '及', '与',
                    '吗', '呢', '吧', '啊', '哦', '嗯', '哈'}
        
        words = jieba.lcut(message)
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        
        # 返回前3个关键词
        return keywords[:3]
    
    def _calculate_relevance(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算关键词相关性（Jaccard相似度）
        
        Args:
            keywords1: 关键词列表1
            keywords2: 关键词列表2
            
        Returns:
            相似度 (0-1)
        """
        if not keywords1 or not keywords2:
            return 0.0
        
        set1, set2 = set(keywords1), set(keywords2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_current_topic(self) -> Optional[Topic]:
        """获取当前话题
        
        Returns:
            当前话题或None
        """
        return self.current_topic


class IntentAnalyzer:
    """意图分析器（主类）"""
    
    def __init__(self):
        self.config = get_config()
        self.intent_config = self.config.get("dialogue_intelligence.intent", {})
        
        # 初始化各个检测器
        self.counter_question_detector: Optional[CounterQuestionDetector] = None
        self.sarcasm_detector: Optional[SarcasmDetector] = None
        self.topic_tracker: Optional[TopicTracker] = None
        
        # 根据配置初始化
        if self.intent_config.get("counter_question", {}).get("enabled", True):
            self.counter_question_detector = CounterQuestionDetector(
                self.intent_config.get("counter_question", {})
            )
        
        if self.intent_config.get("sarcasm_detection", {}).get("enabled", True):
            self.sarcasm_detector = SarcasmDetector(
                self.intent_config.get("sarcasm_detection", {})
            )
        
        if self.intent_config.get("topic_tracking", {}).get("enabled", True):
            self.topic_tracker = TopicTracker(
                self.intent_config.get("topic_tracking", {})
            )
        
        logger.info("意图分析器初始化完成")
    
    def analyze(self, message: str, sender_id: str = "", context: str = "") -> IntentResult:
        """分析消息意图
        
        Args:
            message: 消息内容
            sender_id: 发送者ID
            context: 上下文
            
        Returns:
            意图分析结果
        """
        result = IntentResult(type="normal")
        
        # 1. 反问检测
        if self.counter_question_detector:
            counter_result = self.counter_question_detector.detect(message)
            if counter_result:
                result.is_counter_question = True
                result.type = "counter_question"
                result.confidence = 0.9
                logger.debug("意图: 反问")
        
        # 2. 讽刺检测
        if self.sarcasm_detector:
            sarcasm_result = self.sarcasm_detector.detect(message, context)
            if sarcasm_result["is_sarcastic"]:
                result.is_sarcastic = True
                result.type = "sarcasm"
                result.confidence = sarcasm_result["confidence"]
                logger.debug("意图: 讽刺")
        
        # 3. 话题追踪
        if self.topic_tracker and sender_id:
            topic_result = self.topic_tracker.update(message, sender_id)
            if topic_result.get("topic"):
                result.topic = topic_result["topic"]["name"]
        
        # 4. 判断是否为问句
        if self._is_question(message) and result.type == "normal":
            result.type = "question"
        
        return result
    
    def register_bot_question(self, question: str, context: Optional[List[str]] = None) -> None:
        """注册机器人发出的问题
        
        Args:
            question: 问题内容
            context: 上下文
        """
        if self.counter_question_detector:
            self.counter_question_detector.register_question(question, context)
    
    def get_current_topic(self) -> Optional[str]:
        """获取当前话题名称
        
        Returns:
            话题名称或None
        """
        if self.topic_tracker and self.topic_tracker.current_topic:
            return self.topic_tracker.current_topic.name
        return None
    
    def _is_question(self, message: str) -> bool:
        """判断是否为问句
        
        Args:
            message: 消息内容
            
        Returns:
            是否为问句
        """
        # 简单的问句判断
        question_marks = ['?', '？', '吗', '呢', '吧']
        question_words = ['什么', '怎么', '为什么', '哪', '谁', '几', '多少', '如何']
        
        return (any(mark in message for mark in question_marks) or
                any(word in message for word in question_words))


# 全局实例
_intent_analyzer: Optional[IntentAnalyzer] = None


def get_intent_analyzer() -> IntentAnalyzer:
    """获取意图分析器实例
    
    Returns:
        IntentAnalyzer实例
    """
    global _intent_analyzer
    if _intent_analyzer is None:
        _intent_analyzer = IntentAnalyzer()
    return _intent_analyzer
