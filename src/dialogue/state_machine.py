"""对话状态机"""
import time
from typing import Dict, Any, Optional

from src.dialogue.dialogue_state import DialogueStateEnum, DialogueContext
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("state_machine")


class StateMachine:
    """对话状态机"""
    
    def __init__(self):
        self.config = get_config()
        self.current_state: DialogueStateEnum = DialogueStateEnum.OPENING
        self.state_start_time: float = time.time()
        self.message_count: int = 0
        self.last_message_time: float = time.time()
        
        # 状态转换配置
        self.opening_messages_threshold: int = 2  # 开启状态需要几条消息进入维持
        self.closing_timeout: int = 300  # 5分钟无消息进入结束状态
        
        logger.info("对话状态机初始化完成")
    
    def transition(self, intent_result: Optional[Dict[str, Any]] = None) -> DialogueStateEnum:
        """状态转换
        
        Args:
            intent_result: 意图分析结果
            
        Returns:
            新状态
        """
        current_time = time.time()
        message_interval = current_time - self.last_message_time
        self.last_message_time = current_time
        self.message_count += 1
        
        old_state = self.current_state
        
        # 状态转换逻辑
        if self.current_state == DialogueStateEnum.OPENING:
            # 开启状态：收到足够消息后进入维持状态
            if self.message_count >= self.opening_messages_threshold:
                self.current_state = DialogueStateEnum.MAINTAINING
                self.state_start_time = current_time
                logger.info("状态转换: OPENING -> MAINTAINING")
        
        elif self.current_state == DialogueStateEnum.MAINTAINING:
            # 维持状态：检测话题切换或超时
            if intent_result and intent_result.get("status") == "switching":
                self.current_state = DialogueStateEnum.SWITCHING
                self.state_start_time = current_time
                logger.info("状态转换: MAINTAINING -> SWITCHING (话题切换)")
            elif message_interval > self.closing_timeout:
                self.current_state = DialogueStateEnum.CLOSING
                self.state_start_time = current_time
                logger.info("状态转换: MAINTAINING -> CLOSING (超时)")
        
        elif self.current_state == DialogueStateEnum.SWITCHING:
            # 切换状态：维持2轮后回到维持状态
            state_duration = current_time - self.state_start_time
            if state_duration > 30 or self.message_count % 2 == 0:  # 30秒或2条消息后
                self.current_state = DialogueStateEnum.MAINTAINING
                self.state_start_time = current_time
                logger.debug("状态转换: SWITCHING -> MAINTAINING")
        
        elif self.current_state == DialogueStateEnum.CLOSING:
            # 结束状态：收到新消息重新开启
            self.current_state = DialogueStateEnum.OPENING
            self.message_count = 1
            self.state_start_time = current_time
            logger.info("状态转换: CLOSING -> OPENING (重新开启)")
        
        return self.current_state
    
    def get_context(self, topic: Optional[str] = None) -> DialogueContext:
        """获取当前对话上下文
        
        Args:
            topic: 当前话题
            
        Returns:
            对话上下文
        """
        current_time = time.time()
        duration = current_time - self.state_start_time
        
        from src.dialogue.dialogue_state import Topic
        topic_obj = None
        if topic:
            topic_obj = Topic.create(topic, [], "")
        
        return DialogueContext(
            state=self.current_state,
            message_count=self.message_count,
            duration=duration,
            topic=topic_obj
        )
    
    def reset(self) -> None:
        """重置状态机"""
        self.current_state = DialogueStateEnum.OPENING
        self.message_count = 0
        self.state_start_time = time.time()
        self.last_message_time = time.time()
        logger.info("状态机已重置")


# 全局实例（每个聊天类型一个）
_state_machines: Dict[str, StateMachine] = {}


def get_state_machine(chat_type: str = "group") -> StateMachine:
    """获取状态机实例
    
    Args:
        chat_type: 聊天类型
        
    Returns:
        StateMachine实例
    """
    global _state_machines
    if chat_type not in _state_machines:
        _state_machines[chat_type] = StateMachine()
    return _state_machines[chat_type]
