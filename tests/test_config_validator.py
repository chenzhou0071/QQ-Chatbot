"""配置验证器测试"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_validator import ConfigValidator, ConfigValidationError


class TestConfigValidator:
    """配置验证器测试类"""
    
    def test_valid_config(self, monkeypatch):
        """测试有效配置"""
        # Mock 环境变量
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key')
        
        config = {
            'bot': {
                'qq_number': '123456789',
                'admin_qq': '987654321',
                'target_group': '111222333'
            },
            'ai': {
                'temperature': 0.7,
                'max_tokens': 500
            }
        }
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate(config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """测试缺少必需字段"""
        config = {
            'bot': {
                'qq_number': '123456789'
                # 缺少 admin_qq 和 target_group
            }
        }
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate(config)
        
        assert is_valid is False
        assert len(errors) >= 2
        assert any('admin_qq' in e for e in errors)
        assert any('target_group' in e for e in errors)
    
    def test_invalid_type(self):
        """测试类型错误"""
        config = {
            'bot': {
                'qq_number': 123456789,  # 应该是字符串
                'admin_qq': '987654321',
                'target_group': '111222333'
            }
        }
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate(config)
        
        assert is_valid is False
        assert any('字符串' in e for e in errors)
    
    def test_out_of_range(self):
        """测试超出范围"""
        config = {
            'bot': {
                'qq_number': '123456789',
                'admin_qq': '987654321',
                'target_group': '111222333'
            },
            'ai': {
                'temperature': 1.5,  # 超出范围
                'max_tokens': 500
            }
        }
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate(config)
        
        assert is_valid is False
        assert any('0.0-1.0' in e for e in errors)
    
    def test_validate_and_raise(self):
        """测试抛出异常"""
        config = {
            'bot': {
                'qq_number': '123456789'
                # 缺少必需字段
            }
        }
        
        validator = ConfigValidator()
        
        with pytest.raises(ConfigValidationError):
            validator.validate_and_raise(config)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
