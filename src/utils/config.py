"""配置管理"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class Config:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        
        # 加载环境变量
        load_dotenv("config/.env")
        
        # 加载配置文件
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号分隔的嵌套键）"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.getenv(key, default)
    
    @property
    def bot_qq(self) -> str:
        """机器人QQ号"""
        return self.get("bot.qq_number", "")
    
    @property
    def admin_qq(self) -> str:
        """管理员QQ号"""
        return self.get("bot.admin_qq", "")
    
    @property
    def target_group(self) -> str:
        """目标群号"""
        return self.get("bot.target_group", "")
    
    @property
    def keywords(self) -> list:
        """关键词列表"""
        return self.get("keywords", [])
    
    @property
    def database_path(self) -> str:
        """数据库路径"""
        return self.get_env("DATABASE_PATH", "data/bot.db")


# 全局配置实例
_config = None

def get_config() -> Config:
    """获取配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
