"""昵称分析器 - AI推测群友昵称"""
import re
from src.utils.logger import get_logger

logger = get_logger("nickname_analyzer")

class NicknameAnalyzer:
    """昵称分析器"""
    
    def analyze(self, qq_name: str, group_card: str) -> tuple[str, bool]:
        """
        分析并推测昵称
        
        返回: (推测的昵称, 是否需要确认)
        """
        # 优先使用群名片
        name = group_card if group_card else qq_name
        
        if not name:
            return None, True
        
        # 清理特殊字符
        name = self._clean_name(name)
        
        # 推测昵称
        nickname = self._guess_nickname(name)
        
        # 判断是否需要确认
        need_confirm = self._need_confirmation(name, nickname)
        
        logger.info(f"昵称分析: {name} -> {nickname} (需要确认: {need_confirm})")
        
        return nickname, need_confirm
    
    def _clean_name(self, name: str) -> str:
        """清理名字中的特殊字符"""
        # 移除常见后缀
        suffixes = ['同学', '老师', '大佬', '小朋友', '宝宝', '酱']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        # 移除数字和特殊符号
        name = re.sub(r'[-_\d\s]+$', '', name)
        name = re.sub(r'^[-_\d\s]+', '', name)
        
        # 移除emoji
        name = re.sub(r'[\U00010000-\U0010ffff]', '', name)
        
        return name.strip()
    
    def _guess_nickname(self, name: str) -> str:
        """推测昵称"""
        # 如果名字很短（2-3个字），直接使用
        if 2 <= len(name) <= 3:
            return name
        
        # 如果是4个字，可能是全名，取后两个字
        if len(name) == 4:
            # 检查是否是常见姓氏开头
            common_surnames = ['欧阳', '司马', '上官', '诸葛', '东方', '西门']
            for surname in common_surnames:
                if name.startswith(surname):
                    return name[2:]  # 复姓，取后两字
            return name[1:]  # 单姓，取后三字
        
        # 如果超过4个字，尝试提取核心部分
        if len(name) > 4:
            # 如果包含中文，取中间部分
            chinese_chars = re.findall(r'[\u4e00-\u9fff]+', name)
            if chinese_chars:
                main_part = chinese_chars[0]
                if 2 <= len(main_part) <= 3:
                    return main_part
                elif len(main_part) > 3:
                    return main_part[-2:]  # 取最后两个字
        
        # 默认取前3个字符
        return name[:3]
    
    def _need_confirmation(self, original: str, nickname: str) -> bool:
        """判断是否需要管理员确认"""
        # 如果原名很短且昵称相同，不需要确认
        if len(original) <= 3 and original == nickname:
            return False
        
        # 如果昵称只有1个字，需要确认
        if len(nickname) == 1:
            return True
        
        # 如果原名包含英文或数字，需要确认
        if re.search(r'[a-zA-Z0-9]', original):
            return True
        
        # 如果昵称是从长名字中提取的，需要确认
        if len(original) > 4:
            return True
        
        # 其他情况不需要确认
        return False


# 全局实例
_nickname_analyzer = None

def get_nickname_analyzer() -> NicknameAnalyzer:
    """获取昵称分析器实例"""
    global _nickname_analyzer
    if _nickname_analyzer is None:
        _nickname_analyzer = NicknameAnalyzer()
    return _nickname_analyzer
