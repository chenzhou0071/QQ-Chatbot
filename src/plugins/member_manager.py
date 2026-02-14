"""群友管理插件"""
import re
from datetime import datetime
from nonebot import on_message, on_notice, on_command
from nonebot.adapters.onebot.v11 import (
    Bot, GroupMessageEvent, GroupDecreaseNoticeEvent,
    Message, MessageSegment
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.memory.member_db import get_member_db
from src.ai.nickname_analyzer import get_nickname_analyzer

logger = get_logger("member_manager")
config = get_config()
member_db = get_member_db()
nickname_analyzer = get_nickname_analyzer()

# 监听群消息，自动收集群友信息
member_collector = on_message(priority=1, block=False)

@member_collector.handle()
async def collect_member_info(bot: Bot, event: GroupMessageEvent):
    """自动收集群友信息"""
    # 检查功能是否开启
    if not config.get("member_management.auto_collect", True):
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        return
    
    qq_id = str(event.user_id)
    qq_name = event.sender.nickname
    group_card = event.sender.card or event.sender.nickname
    
    # 获取头像URL
    avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_id}&s=640"
    
    # 检查是否已存在
    member = member_db.get_member(qq_id)
    
    if member:
        # 更新信息
        member_db.add_or_update_member(qq_id, qq_name, group_card, avatar_url=avatar_url)
    else:
        # 新群友，推测昵称
        nickname, need_confirm = nickname_analyzer.analyze(qq_name, group_card)
        
        # 添加到数据库
        member_db.add_or_update_member(qq_id, qq_name, group_card, nickname, avatar_url)
        
        # 设置昵称确认状态
        if nickname:
            member_db.set_nickname(qq_id, nickname, confirmed=not need_confirm)
            
            # 如果需要确认，私聊管理员
            if need_confirm:
                await notify_admin_confirm_nickname(bot, qq_id, group_card or qq_name, nickname)


async def notify_admin_confirm_nickname(bot: Bot, qq_id: str, name: str, nickname: str):
    """通知管理员确认昵称"""
    try:
        admin_qq = config.admin_qq
        message = f"""【昵称确认】
群友：{name}（QQ：{qq_id}）
我推测的昵称是：{nickname}

请回复正确的昵称，或回复"确认"表示同意"""
        
        await bot.send_private_msg(user_id=int(admin_qq), message=message)
        logger.info(f"已通知管理员确认昵称: {qq_id}")
    except Exception as e:
        logger.error(f"通知管理员失败: {e}")


# 监听群成员减少（退群/被踢）
from nonebot.adapters.onebot.v11 import NoticeEvent

member_leave = on_notice(priority=5, block=False)

@member_leave.handle()
async def handle_member_leave(bot: Bot, event: NoticeEvent):
    """处理群友退群"""
    # 记录所有通知事件，用于调试
    logger.info(f"收到通知事件: {type(event).__name__}, 内容: {event}")
    
    # 只处理群成员减少事件
    if not isinstance(event, GroupDecreaseNoticeEvent):
        return
    
    logger.info(f"✅ 检测到群成员减少事件: 群{event.group_id}, 用户{event.user_id}, 操作者{event.operator_id}")
    
    # 检查功能是否开启
    if not config.get("member_management.leave_notification", True):
        logger.info("退群通知功能未开启")
        return
    
    # 检查是否是目标群
    if str(event.group_id) != config.target_group:
        logger.info(f"非目标群，跳过: {event.group_id} (目标群: {config.target_group})")
        return
    
    qq_id = str(event.user_id)
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    
    if not member:
        logger.warning(f"退群群友信息不存在: {qq_id}，使用默认信息")
        # 即使没有信息，也发送退群通知
        nickname = f"群友{qq_id[-4:]}"  # 使用QQ号后4位作为昵称
        avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_id}&s=640"
        leave_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = Message([
            MessageSegment.image(avatar_url),
            MessageSegment.text(f"\n\n👋 群友退群通知\n\n"),
            MessageSegment.text(f"QQ号：{qq_id}\n"),
            MessageSegment.text(f"退群时间：{leave_time}\n"),
            MessageSegment.text(f"备注：该用户未在群内发言，无详细信息")
        ])
        
        try:
            await bot.send_group_msg(group_id=event.group_id, message=message)
            logger.info(f"已发送退群通知（无历史记录）: {qq_id}")
        except Exception as e:
            logger.error(f"发送退群通知失败: {e}")
        return
    
    # 标记退群
    member_db.mark_leave(qq_id)
    
    # 计算在群天数
    first_seen = datetime.fromisoformat(member['first_seen'])
    days_in_group = (datetime.now() - first_seen).days
    
    # 发送退群通知
    nickname = member.get('nickname') or member.get('group_card') or member.get('qq_name') or qq_id
    avatar_url = member.get('avatar_url') or f"https://q1.qlogo.cn/g?b=qq&nk={qq_id}&s=640"
    
    leave_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = Message([
        MessageSegment.image(avatar_url),
        MessageSegment.text(f"\n\n👋 群友退群通知\n\n"),
        MessageSegment.text(f"昵称：{nickname}\n"),
        MessageSegment.text(f"QQ号：{qq_id}\n"),
        MessageSegment.text(f"退群时间：{leave_time}\n"),
        MessageSegment.text(f"在群天数：{days_in_group}天")
    ])
    
    try:
        await bot.send_group_msg(group_id=event.group_id, message=message)
        logger.info(f"已发送退群通知: {qq_id}")
    except Exception as e:
        logger.error(f"发送退群通知失败: {e}")


# 命令：设置生日
set_birthday_cmd = on_command("生日", permission=SUPERUSER, priority=1, block=True)

@set_birthday_cmd.handle()
async def set_birthday(bot: Bot, event, args: Message = CommandArg()):
    """设置群友生日"""
    # 解析参数
    text = args.extract_plain_text().strip()
    
    # 尝试提取@的QQ号
    at_segments = [seg for seg in args if seg.type == "at"]
    
    if at_segments:
        qq_id = str(at_segments[0].data["qq"])
        # 提取生日
        birthday_match = re.search(r'(\d{1,2})-(\d{1,2})', text)
        if not birthday_match:
            await set_birthday_cmd.finish("❌ 格式错误，请使用：/生日 @用户 MM-DD")
            return
        
        month = birthday_match.group(1).zfill(2)
        day = birthday_match.group(2).zfill(2)
        birthday = f"{month}-{day}"
    else:
        # 尝试解析 QQ号 生日
        parts = text.split()
        if len(parts) != 2:
            await set_birthday_cmd.finish("❌ 格式错误，请使用：/生日 @用户 MM-DD 或 /生日 QQ号 MM-DD")
            return
        
        qq_id = parts[0]
        birthday_match = re.match(r'(\d{1,2})-(\d{1,2})', parts[1])
        if not birthday_match:
            await set_birthday_cmd.finish("❌ 生日格式错误，请使用 MM-DD 格式")
            return
        
        month = birthday_match.group(1).zfill(2)
        day = birthday_match.group(2).zfill(2)
        birthday = f"{month}-{day}"
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    if not member:
        await set_birthday_cmd.finish(f"❌ 未找到该群友信息：{qq_id}")
        return
    
    # 设置生日
    if member_db.set_birthday(qq_id, birthday):
        nickname = member.get('nickname') or member.get('group_card') or qq_id
        await set_birthday_cmd.finish(f"✅ 已设置{nickname}的生日为{month}月{day}日")
    else:
        await set_birthday_cmd.finish("❌ 设置生日失败")


# 命令：设置备注
set_remark_cmd = on_command("备注", permission=SUPERUSER, priority=1, block=True)

@set_remark_cmd.handle()
async def set_remark(bot: Bot, event, args: Message = CommandArg()):
    """设置群友备注"""
    text = args.extract_plain_text().strip()
    
    # 解析 QQ号 备注内容
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        await set_remark_cmd.finish("❌ 格式错误，请使用：/备注 QQ号 备注内容")
        return
    
    qq_id = parts[0]
    remark = parts[1]
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    if not member:
        await set_remark_cmd.finish(f"❌ 未找到该群友信息：{qq_id}")
        return
    
    # 设置备注
    if member_db.set_remark(qq_id, remark):
        nickname = member.get('nickname') or member.get('group_card') or qq_id
        await set_remark_cmd.finish(f"✅ 已添加{nickname}的备注信息")
    else:
        await set_remark_cmd.finish("❌ 设置备注失败")


# 命令：查询群友信息
query_member_cmd = on_command("查询", priority=1, block=True)

@query_member_cmd.handle()
async def query_member(bot: Bot, event, args: Message = CommandArg()):
    """查询群友信息"""
    # 尝试提取@的QQ号
    at_segments = [seg for seg in args if seg.type == "at"]
    
    if at_segments:
        qq_id = str(at_segments[0].data["qq"])
    else:
        text = args.extract_plain_text().strip()
        if not text:
            await query_member_cmd.finish("❌ 请指定要查询的群友")
            return
        qq_id = text
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    if not member:
        await query_member_cmd.finish(f"❌ 未找到该群友信息")
        return
    
    nickname = member.get('nickname') or member.get('group_card') or member.get('qq_name') or qq_id
    
    # 判断是群聊还是私聊
    is_private = hasattr(event, 'message_type') and event.message_type == 'private'
    is_admin = str(event.user_id) == config.admin_qq
    
    if is_private and is_admin:
        # 私聊管理员，显示完整信息
        first_seen = member.get('first_seen', '未知')
        if first_seen != '未知':
            first_seen = datetime.fromisoformat(first_seen).strftime("%Y-%m-%d")
        
        last_active = member.get('last_active', '未知')
        if last_active != '未知':
            last_active_dt = datetime.fromisoformat(last_active)
            minutes_ago = int((datetime.now() - last_active_dt).total_seconds() / 60)
            if minutes_ago < 60:
                last_active = f"{minutes_ago}分钟前"
            elif minutes_ago < 1440:
                last_active = f"{minutes_ago // 60}小时前"
            else:
                last_active = f"{minutes_ago // 1440}天前"
        
        nickname_status = "已确认" if member.get('nickname_confirmed') else "未确认"
        birthday = member.get('birthday') or '未设置'
        remark = member.get('remark') or '无'
        
        reply = f"""【群友完整信息 - {nickname}】
👤 QQ号：{qq_id}
📝 QQ昵称：{member.get('qq_name', '未知')}
🏷️ 群名片：{member.get('group_card', '未知')}
💭 昵称：{nickname}（{nickname_status}）
🎂 生日：{birthday}
📌 备注：{remark}
💬 发言次数：{member.get('message_count', 0)}次
📅 首次出现：{first_seen}
⏰ 最后活跃：{last_active}"""
    else:
        # 群聊，显示基础信息（不含生日）
        last_active = member.get('last_active', '未知')
        if last_active != '未知':
            last_active_dt = datetime.fromisoformat(last_active)
            minutes_ago = int((datetime.now() - last_active_dt).total_seconds() / 60)
            if minutes_ago < 60:
                last_active = f"{minutes_ago}分钟前"
            elif minutes_ago < 1440:
                last_active = f"{minutes_ago // 60}小时前"
            else:
                last_active = f"{minutes_ago // 1440}天前"
        
        first_seen = member.get('first_seen', '未知')
        if first_seen != '未知':
            first_seen = datetime.fromisoformat(first_seen).strftime("%Y-%m-%d")
        
        reply = f"""【群友信息 - {nickname}】
📝 群名片：{member.get('group_card', '未知')}
💬 发言次数：{member.get('message_count', 0)}次
⏰ 最后活跃：{last_active}
📅 加入时间：{first_seen}"""
    
    await query_member_cmd.finish(reply)


# 命令：设置昵称
set_nickname_cmd = on_command("昵称", permission=SUPERUSER, priority=1, block=True)

@set_nickname_cmd.handle()
async def set_nickname(bot: Bot, event, args: Message = CommandArg()):
    """设置群友昵称"""
    text = args.extract_plain_text().strip()
    
    # 尝试提取@的QQ号
    at_segments = [seg for seg in args if seg.type == "at"]
    
    if at_segments:
        qq_id = str(at_segments[0].data["qq"])
        # 提取昵称
        nickname = text.strip()
        if not nickname:
            await set_nickname_cmd.finish("❌ 请输入昵称")
            return
    else:
        # 解析 QQ号 昵称
        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            await set_nickname_cmd.finish("❌ 格式错误，请使用：/昵称 @用户 昵称 或 /昵称 QQ号 昵称")
            return
        
        qq_id = parts[0]
        nickname = parts[1]
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    if not member:
        await set_nickname_cmd.finish(f"❌ 未找到该群友信息：{qq_id}")
        return
    
    # 设置昵称
    if member_db.set_nickname(qq_id, nickname, confirmed=True):
        await set_nickname_cmd.finish(f"✅ 已设置昵称为：{nickname}")
    else:
        await set_nickname_cmd.finish("❌ 设置昵称失败")


# 命令：统计
stats_cmd = on_command("统计", priority=1, block=True)

@stats_cmd.handle()
async def show_stats(bot: Bot, event):
    """显示群友活跃度统计"""
    members = member_db.get_all_active_members()
    
    if not members:
        await stats_cmd.finish("❌ 暂无群友数据")
        return
    
    # 取前10名
    top_members = members[:10]
    
    reply = "【群友活跃度排行榜】\n\n"
    for i, member in enumerate(top_members, 1):
        nickname = member.get('nickname') or member.get('group_card') or member.get('qq_name') or member['qq_id']
        count = member.get('message_count', 0)
        reply += f"{i}. {nickname}：{count}条消息\n"
    
    reply += f"\n总群友数：{len(members)}人"
    
    await stats_cmd.finish(reply)


logger.info("群友管理插件已加载")


# 测试命令：模拟退群通知
test_leave_cmd = on_command("测试退群", permission=SUPERUSER, priority=1, block=True)

@test_leave_cmd.handle()
async def test_leave_notification(bot: Bot, event, args: Message = CommandArg()):
    """测试退群通知功能"""
    text = args.extract_plain_text().strip()
    
    if not text:
        await test_leave_cmd.finish("❌ 请提供QQ号，例如：/测试退群 123456789")
        return
    
    qq_id = text
    
    # 获取群友信息
    member = member_db.get_member(qq_id)
    if not member:
        await test_leave_cmd.finish(f"❌ 未找到该群友信息：{qq_id}")
        return
    
    # 计算在群天数
    first_seen = datetime.fromisoformat(member['first_seen'])
    days_in_group = (datetime.now() - first_seen).days
    
    # 发送退群通知
    nickname = member.get('nickname') or member.get('group_card') or member.get('qq_name') or qq_id
    avatar_url = member.get('avatar_url') or f"https://q1.qlogo.cn/g?b=qq&nk={qq_id}&s=640"
    
    leave_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 判断是群聊还是私聊
    if hasattr(event, 'group_id'):
        group_id = event.group_id
    else:
        group_id = int(config.target_group)
    
    message = Message([
        MessageSegment.image(avatar_url),
        MessageSegment.text(f"\n\n👋 群友退群通知（测试）\n\n"),
        MessageSegment.text(f"昵称：{nickname}\n"),
        MessageSegment.text(f"QQ号：{qq_id}\n"),
        MessageSegment.text(f"退群时间：{leave_time}\n"),
        MessageSegment.text(f"在群天数：{days_in_group}天")
    ])
    
    try:
        await bot.send_group_msg(group_id=group_id, message=message)
        logger.info(f"已发送测试退群通知: {qq_id}")
        await test_leave_cmd.finish("✅ 测试退群通知已发送")
    except Exception as e:
        logger.error(f"发送测试退群通知失败: {e}")
        await test_leave_cmd.finish(f"❌ 发送失败: {e}")

