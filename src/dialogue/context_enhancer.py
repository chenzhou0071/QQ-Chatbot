"""上下文增强器"""
from typing import List, Dict, Any, Optional

from src.dialogue.dialogue_state import DialogueStateEnum, IntentResult, DialogueContext
from src.dialogue.state_machine import get_state_machine
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("context_enhancer")


class ContextEnhancer:
    """上下文增强器"""
    
    def __init__(self):
        self.config = get_config()
        self.state_prompts_enabled: bool = self.config.get(
            "dialogue_intelligence.state_machine.state_prompts", True
        )
        logger.info("上下文增强器初始化完成")
    
    def enrich(self,
               base_context: List[Dict[str, str]],
               intent_result: Optional[IntentResult] = None,
               chat_type: str = "group",
               topic_status: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """丰富上下文
        
        Args:
            base_context: 基础上下文（来自记忆系统）
            intent_result: 意图分析结果
            chat_type: 聊天类型
            topic_status: 话题状态
            
        Returns:
            增强后的上下文
        """
        enhanced_context = base_context.copy()
        
        # 获取状态机
        state_machine = get_state_machine(chat_type)
        
        # 更新状态
        current_state = state_machine.transition(topic_status)
        
        # 如果启用状态感知prompt
        if self.state_prompts_enabled:
            state_prompt = self._build_state_prompt(
                current_state,
                intent_result,
                topic_status
            )
            
            if state_prompt:
                # 在上下文开头插入状态提示
                enhanced_context.insert(0, {
                    "role": "system",
                    "content": state_prompt
                })
                logger.debug(f"[{chat_type}] 添加状态提示: {current_state.value}")
        
        return enhanced_context
    
    def _build_state_prompt(self,
                           state: DialogueStateEnum,
                           intent_result: Optional[IntentResult] = None,
                           topic_status: Optional[Dict[str, Any]] = None) -> str:
        """构建状态感知prompt
        
        Args:
            state: 当前状态
            intent_result: 意图分析结果
            topic_status: 话题状态
            
        Returns:
            状态提示文本
        """
        prompts = []
        
        # 1. 状态指令
        state_instructions = {
            DialogueStateEnum.OPENING: """【对话状态：开启】
- 这是对话的开始，保持友好和开放
- 可以主动问候或回应
- 语气要温和自然，符合你的害羞性格""",
            
            DialogueStateEnum.MAINTAINING: """【对话状态：深入讨论】
- 对话正在进行中，保持话题连贯
- 可以回顾之前的对话内容
- 适当追问细节或表达自己的看法
- 保持温柔内敛的语气""",
            
            DialogueStateEnum.SWITCHING: """【对话状态：话题切换】
- 话题正在转换，注意过渡自然
- 可以简单总结一下之前的话题
- 不要突兀地切换，保持对话流畅
- 用温和的方式引入新话题""",
            
            DialogueStateEnum.CLOSING: """【对话状态：收尾】
- 对话即将结束
- 可以总结要点或表达结束意愿
- 保持友好态度，留下好印象"""
        }
        
        prompts.append(state_instructions.get(state, ""))
        
        # 2. 话题信息
        if topic_status:
            topic_name = topic_status.get("topic", {}).get("name")
            if topic_name:
                prompts.append(f"\n【当前话题】{topic_name}")
            
            # 话题切换提示
            if topic_status.get("status") == "switching":
                old_topic = topic_status.get("old_topic")
                if old_topic:
                    prompts.append(f"【提示】话题从「{old_topic}」切换到「{topic_name}」，注意自然过渡")
        
        # 3. 意图提示
        if intent_result:
            if intent_result.is_counter_question:
                prompts.append("\n【提示】用户在反问你之前的问题，请回答你自己的情况")
            
            if intent_result.is_sarcastic:
                prompts.append(f"\n【提示】用户可能在使用讽刺语气，请理解真实意图并委婉回应")
        
        return "\n".join(prompts)
    
    def get_topic_switching_prompt(self, old_topic: str, new_topic: str) -> str:
        """生成话题切换的过渡prompt
        
        Args:
            old_topic: 旧话题
            new_topic: 新话题
            
        Returns:
            过渡提示
        """
        return f"""【话题切换指引】
上一个话题：{old_topic}
新话题：{new_topic}

过渡要求：
- 自然地从旧话题过渡到新话题
- 可以简单回应一下之前的讨论
- 不要突兀地直接切换
- 保持对话的连贯性和你温柔的性格"""


# 全局实例
_context_enhancer: Optional[ContextEnhancer] = None


def get_context_enhancer() -> ContextEnhancer:
    """获取上下文增强器实例
    
    Returns:
        ContextEnhancer实例
    """
    global _context_enhancer
    if _context_enhancer is None:
        _context_enhancer = ContextEnhancer()
    return _context_enhancer
