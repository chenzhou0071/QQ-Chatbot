"""意图分析器测试"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dialogue.intent_analyzer import CounterQuestionDetector, SarcasmDetector, TopicTracker


class TestCounterQuestionDetector:
    """反问检测器测试"""
    
    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return CounterQuestionDetector({'stack_size': 3})
    
    def test_detect_counter_question(self, detector):
        """测试反问检测"""
        # 先注册一个问题
        detector.register_question("你喜欢什么游戏？")
        
        # 测试反问
        result = detector.detect("你呢？")
        assert result is not None
        assert result['is_counter'] is True
    
    def test_no_counter_question_without_context(self, detector):
        """测试没有上下文时不检测为反问"""
        result = detector.detect("你呢？")
        assert result is None
    
    def test_question_stack_limit(self, detector):
        """测试问题栈大小限制"""
        # 注册4个问题
        for i in range(4):
            detector.register_question(f"问题{i}")
        
        # 应该只保留最近3个
        assert len(detector.question_stack) == 3


class TestSarcasmDetector:
    """讽刺检测器测试"""
    
    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return SarcasmDetector({'threshold': 0.6})
    
    def test_detect_sarcasm_with_punctuation(self, detector):
        """测试标点符号讽刺"""
        result = detector.detect("哇~真厉害呢...")
        assert result['is_sarcastic'] is True
        assert result['confidence'] >= 0.6
    
    def test_detect_sarcasm_with_tone_words(self, detector):
        """测试语气词讽刺"""
        result = detector.detect("呵呵呵，真厉害呢")
        assert result['is_sarcastic'] is True
    
    def test_normal_message(self, detector):
        """测试正常消息"""
        result = detector.detect("你好厉害啊")
        assert result['is_sarcastic'] is False


class TestTopicTracker:
    """话题追踪器测试"""
    
    @pytest.fixture
    def tracker(self):
        """创建追踪器实例"""
        return TopicTracker({'switch_threshold': 3})
    
    def test_create_new_topic(self, tracker):
        """测试创建新话题"""
        result = tracker.update("今天天气真好", "user1")
        assert result['status'] == 'new'
        assert tracker.current_topic is not None
    
    def test_maintain_topic(self, tracker):
        """测试维持话题"""
        tracker.update("今天天气真好", "user1")
        result = tracker.update("是啊，阳光明媚", "user2")
        assert result['status'] == 'maintaining'
    
    def test_switch_topic(self, tracker):
        """测试话题切换"""
        tracker.update("今天天气真好", "user1")
        
        # 发送3条不相关消息
        tracker.update("我喜欢吃火锅", "user2")
        tracker.update("火锅真好吃", "user3")
        result = tracker.update("推荐个火锅店", "user1")
        
        assert result['status'] == 'switching'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
