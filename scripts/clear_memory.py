"""清空记忆数据（保留群友数据库）"""
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '.')

from src.memory.database import get_database
from src.utils.logger import get_logger

logger = get_logger("clear_memory")

def clear_memory():
    """清空记忆数据"""
    print("=" * 60)
    print("清空记忆数据（保留群友数据库）")
    print("=" * 60)
    print()
    
    # 1. 清空SQLite数据库中的记忆表
    print("1. 清空SQLite数据库中的记忆表...")
    try:
        db = get_database()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 清空对话上下文
            cursor.execute("DELETE FROM conversation_context")
            context_count = cursor.rowcount
            print(f"   ✅ 已清空对话上下文表 (删除 {context_count} 条记录)")
            
            # 清空聊天记录
            cursor.execute("DELETE FROM chat_log")
            log_count = cursor.rowcount
            print(f"   ✅ 已清空聊天记录表 (删除 {log_count} 条记录)")
            
            # 可选：清空关键词回复（如果不需要保留自定义关键词）
            # cursor.execute("DELETE FROM keyword_reply")
            # keyword_count = cursor.rowcount
            # print(f"   ✅ 已清空关键词回复表 (删除 {keyword_count} 条记录)")
            
            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='chat_log'")
            
            print(f"   ✅ SQLite记忆数据清空完成")
            
    except Exception as e:
        print(f"   ❌ 清空SQLite记忆失败: {e}")
        logger.error(f"清空SQLite记忆失败: {e}", exc_info=True)
        return False
    
    # 2. 清空向量数据库
    print("\n2. 清空向量数据库...")
    chroma_dir = Path("data/chroma")
    
    if chroma_dir.exists():
        try:
            # 删除整个chroma目录
            shutil.rmtree(chroma_dir)
            print(f"   ✅ 已删除向量数据库目录: {chroma_dir}")
            
            # 重新创建空目录
            chroma_dir.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ 已重新创建空的向量数据库目录")
            
        except Exception as e:
            print(f"   ❌ 清空向量数据库失败: {e}")
            logger.error(f"清空向量数据库失败: {e}", exc_info=True)
            return False
    else:
        print(f"   ℹ️  向量数据库目录不存在，跳过")
    
    # 3. 验证群友数据是否保留
    print("\n3. 验证群友数据...")
    try:
        db = get_database()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM group_member")
            member_count = cursor.fetchone()['count']
            print(f"   ✅ 群友数据已保留 (共 {member_count} 条记录)")
            
    except Exception as e:
        print(f"   ⚠️  无法验证群友数据: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 记忆清空完成！")
    print("=" * 60)
    print("\n保留的数据:")
    print("  • 群友信息 (group_member 表)")
    print("  • 群友昵称、生日、备注等")
    print("\n已清空的数据:")
    print("  • 对话上下文 (conversation_context 表)")
    print("  • 聊天记录 (chat_log 表)")
    print("  • 向量记忆 (data/chroma/ 目录)")
    print()
    
    return True

if __name__ == "__main__":
    # 确认操作
    print("\n⚠️  警告：此操作将清空所有记忆数据（但保留群友数据库）")
    print("包括：对话上下文、聊天记录、向量记忆")
    print()
    
    confirm = input("确认清空记忆？(输入 yes 确认): ").strip().lower()
    
    if confirm == "yes":
        print()
        success = clear_memory()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ 操作已取消")
        sys.exit(0)
