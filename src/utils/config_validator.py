"""配置验证器"""
from typing import Dict, Any, List, Tuple
from src.utils.logger import get_logger

logger = get_logger("config_validator")


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            (是否通过, 错误列表, 警告列表)
        """
        self.errors = []
        self.warnings = []
        
        # 验证必需字段
        self._validate_required_fields(config)
        
        # 验证字段类型
        self._validate_field_types(config)
        
        # 验证字段范围
        self._validate_field_ranges(config)
        
        # 验证依赖关系
        self._validate_dependencies(config)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_required_fields(self, config: Dict[str, Any]) -> None:
        """验证必需字段"""
        required_fields = [
            ('bot.qq_number', '机器人QQ号'),
            ('bot.admin_qq', '管理员QQ号'),
            ('bot.target_group', '目标群号'),
        ]
        
        for field_path, field_name in required_fields:
            if not self._get_nested_value(config, field_path):
                self.errors.append(f"缺少必需配置: {field_name} ({field_path})")
    
    def _validate_field_types(self, config: Dict[str, Any]) -> None:
        """验证字段类型"""
        type_checks = [
            ('bot.qq_number', str, 'QQ号必须是字符串'),
            ('bot.admin_qq', str, '管理员QQ号必须是字符串'),
            ('bot.target_group', str, '目标群号必须是字符串'),
            ('ai.temperature', (int, float), 'AI温度参数必须是数字'),
            ('ai.max_tokens', int, 'max_tokens必须是整数'),
            ('conversation.max_messages', int, 'max_messages必须是整数'),
            ('conversation.timeout_minutes', int, 'timeout_minutes必须是整数'),
        ]
        
        for field_path, expected_type, error_msg in type_checks:
            value = self._get_nested_value(config, field_path)
            if value is not None and not isinstance(value, expected_type):
                self.errors.append(f"{error_msg} (当前类型: {type(value).__name__})")
    
    def _validate_field_ranges(self, config: Dict[str, Any]) -> None:
        """验证字段范围"""
        range_checks = [
            ('ai.temperature', 0.0, 1.0, 'AI温度参数必须在0.0-1.0之间'),
            ('ai.max_tokens', 1, 4000, 'max_tokens必须在1-4000之间'),
            ('conversation.max_messages', 1, 100, 'max_messages必须在1-100之间'),
            ('memory.vector_db.search_results', 1, 20, 'search_results必须在1-20之间'),
            ('memory.vector_db.similarity_threshold', 0.0, 1.0, '相似度阈值必须在0.0-1.0之间'),
        ]
        
        for field_path, min_val, max_val, error_msg in range_checks:
            value = self._get_nested_value(config, field_path)
            if value is not None:
                try:
                    if not (min_val <= float(value) <= max_val):
                        self.errors.append(f"{error_msg} (当前值: {value})")
                except (ValueError, TypeError):
                    pass  # 类型错误已在类型检查中处理
    
    def _validate_dependencies(self, config: Dict[str, Any]) -> None:
        """验证依赖关系"""
        # 如果启用向量数据库，检查相关配置
        if config.get('memory', {}).get('vector_db', {}).get('enabled'):
            if not config.get('memory', {}).get('vector_db', {}).get('persist_dir'):
                self.warnings.append("启用了向量数据库但未配置persist_dir，将使用默认路径")
        
        # 如果启用主动对话，检查相关配置
        if config.get('dialogue_intelligence', {}).get('proactive', {}).get('enabled'):
            if not config.get('dialogue_intelligence', {}).get('proactive', {}).get('check_interval'):
                self.warnings.append("启用了主动对话但未配置check_interval，将使用默认值")
        
        # 检查API密钥（通过环境变量）
        import os
        if not os.getenv('DEEPSEEK_API_KEY') and not os.getenv('QWEN_API_KEY'):
            self.errors.append("未配置AI API密钥 (DEEPSEEK_API_KEY 或 QWEN_API_KEY)")
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """获取嵌套配置值
        
        Args:
            config: 配置字典
            path: 点号分隔的路径，如 'bot.qq_number'
            
        Returns:
            配置值或None
        """
        keys = path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """验证配置，如果失败则抛出异常
        
        Args:
            config: 配置字典
            
        Raises:
            ConfigValidationError: 配置验证失败
        """
        is_valid, errors, warnings = self.validate(config)
        
        # 输出警告
        for warning in warnings:
            logger.warning(f"配置警告: {warning}")
        
        # 如果有错误，抛出异常
        if not is_valid:
            error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ConfigValidationError(error_msg)
        
        logger.info("配置验证通过")


def validate_config(config: Dict[str, Any]) -> None:
    """验证配置的便捷函数
    
    Args:
        config: 配置字典
        
    Raises:
        ConfigValidationError: 配置验证失败
    """
    validator = ConfigValidator()
    validator.validate_and_raise(config)
