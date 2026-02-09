"""群友信息数据库操作"""
from datetime import datetime
from typing import Optional, List, Dict
from src.memory.database import get_database
from src.utils.logger import get_logger

logger = get_logger("member_db")

class MemberDatabase:
    """群友信息数据库管理"""
    
    def __init__(self):
        self.db = get_database()
    
    def add_or_update_member(self, qq_id: str, qq_name: str = None, 
                            group_card: str = None, nickname: str = None,
                            avatar_url: str = None) -> bool:
        """添加或更新群友信息"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取当前本地时间
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 检查是否已存在
                cursor.execute("SELECT qq_id FROM group_member WHERE qq_id = ?", (qq_id,))
                exists = cursor.fetchone()
                
                if exists:
                    # 更新信息
                    update_fields = ["last_active = ?", "message_count = message_count + 1"]
                    params = [now]
                    
                    if qq_name:
                        update_fields.append("qq_name = ?")
                        params.append(qq_name)
                    if group_card:
                        update_fields.append("group_card = ?")
                        params.append(group_card)
                    if nickname:
                        update_fields.append("nickname = ?")
                        params.append(nickname)
                    if avatar_url:
                        update_fields.append("avatar_url = ?")
                        params.append(avatar_url)
                    
                    params.append(qq_id)
                    
                    sql = f"UPDATE group_member SET {', '.join(update_fields)} WHERE qq_id = ?"
                    cursor.execute(sql, params)
                    logger.info(f"更新群友信息: {qq_id}")
                else:
                    # 新增群友
                    cursor.execute("""
                        INSERT INTO group_member 
                        (qq_id, qq_name, group_card, nickname, avatar_url, first_seen, last_active, message_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (qq_id, qq_name, group_card, nickname, avatar_url, now, now))
                    logger.info(f"新增群友: {qq_id}")
                
                return True
        except Exception as e:
            logger.error(f"添加/更新群友失败: {e}")
            return False
    
    def get_member(self, qq_id: str) -> Optional[Dict]:
        """获取群友信息"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM group_member WHERE qq_id = ?", (qq_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"获取群友信息失败: {e}")
            return None
    
    def set_nickname(self, qq_id: str, nickname: str, confirmed: bool = True) -> bool:
        """设置昵称"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE group_member 
                    SET nickname = ?, nickname_confirmed = ?, updated_at = ?
                    WHERE qq_id = ?
                """, (nickname, 1 if confirmed else 0, now, qq_id))
                logger.info(f"设置昵称: {qq_id} -> {nickname}")
                return True
        except Exception as e:
            logger.error(f"设置昵称失败: {e}")
            return False
    
    def set_birthday(self, qq_id: str, birthday: str) -> bool:
        """设置生日"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE group_member 
                    SET birthday = ?, updated_at = ?
                    WHERE qq_id = ?
                """, (birthday, now, qq_id))
                logger.info(f"设置生日: {qq_id} -> {birthday}")
                return True
        except Exception as e:
            logger.error(f"设置生日失败: {e}")
            return False
    
    def set_remark(self, qq_id: str, remark: str) -> bool:
        """设置备注"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE group_member 
                    SET remark = ?, updated_at = ?
                    WHERE qq_id = ?
                """, (remark, now, qq_id))
                logger.info(f"设置备注: {qq_id}")
                return True
        except Exception as e:
            logger.error(f"设置备注失败: {e}")
            return False
    
    def mark_leave(self, qq_id: str) -> bool:
        """标记退群"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE group_member 
                    SET is_active = 0, leave_time = ?, updated_at = ?
                    WHERE qq_id = ?
                """, (now, now, qq_id))
                logger.info(f"标记退群: {qq_id}")
                return True
        except Exception as e:
            logger.error(f"标记退群失败: {e}")
            return False
    
    def get_today_birthdays(self) -> List[Dict]:
        """获取今天生日的群友"""
        try:
            today = datetime.now().strftime("%m-%d")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM group_member 
                    WHERE birthday = ? AND is_active = 1
                """, (today,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取今日生日失败: {e}")
            return []
    
    def get_all_active_members(self) -> List[Dict]:
        """获取所有在群成员"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM group_member 
                    WHERE is_active = 1
                    ORDER BY message_count DESC
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取群友列表失败: {e}")
            return []
    
    def get_unconfirmed_nicknames(self) -> List[Dict]:
        """获取未确认昵称的群友"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM group_member 
                    WHERE nickname_confirmed = 0 AND nickname IS NOT NULL AND is_active = 1
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取未确认昵称失败: {e}")
            return []


# 全局实例
_member_db = None

def get_member_db() -> MemberDatabase:
    """获取群友数据库实例"""
    global _member_db
    if _member_db is None:
        _member_db = MemberDatabase()
    return _member_db
