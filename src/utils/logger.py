"""日志工具"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

class BotLogger:
    """机器人日志管理器"""
    
    def __init__(self, log_dir: str = "data/logs", retention_days: int = 30):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建logger
        self.logger = logging.getLogger("qq_bot")
        self.logger.setLevel(logging.INFO)
        
        # 清理旧日志
        self._cleanup_old_logs()
        
        # 添加处理器
        self._add_handlers()
    
    def _add_handlers(self):
        """添加日志处理器"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 普通日志
        info_handler = logging.FileHandler(
            self.log_dir / f"bot-{today}.log",
            encoding="utf-8"
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(self.formatter)
        
        # 错误日志
        error_handler = logging.FileHandler(
            self.log_dir / f"error-{today}.log",
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        
        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        
        self.logger.addHandler(info_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _cleanup_old_logs(self):
        """清理过期日志"""
        if not self.log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                # 从文件名提取日期
                date_str = log_file.stem.split("-", 1)[1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    self.logger.info(f"已删除过期日志: {log_file.name}")
            except (ValueError, IndexError):
                continue
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """获取logger实例"""
        if name:
            return logging.getLogger(f"qq_bot.{name}")
        return self.logger


# 全局logger实例
_bot_logger = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取logger"""
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = BotLogger()
    return _bot_logger.get_logger(name)
