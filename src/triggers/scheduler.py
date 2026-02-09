"""定时任务模块"""
import random
from nonebot import require, get_bot
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.helpers import random_choice
from src.memory.member_db import get_member_db

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

logger = get_logger("scheduler")
config = get_config()
member_db = get_member_db()

async def send_group_message(message: str):
    """发送群消息"""
    try:
        bot = get_bot()
        target_group = config.target_group
        await bot.send_group_msg(group_id=int(target_group), message=message)
        logger.info(f"[定时任务] 发送消息: {message}")
    except Exception as e:
        logger.error(f"[定时任务] 发送失败: {e}")

# 早安任务
@scheduler.scheduled_job("cron", hour=9, minute=0, id="morning_greeting")
async def morning_greeting():
    """早安问候"""
    if not config.get("auto_chat.morning.enabled", True):
        return
    
    messages = config.get("auto_chat.morning.messages", ["大家早安！☀️"])
    message = random_choice(messages)
    await send_group_message(message)

# 晚安任务
@scheduler.scheduled_job("cron", hour=23, minute=0, id="night_greeting")
async def night_greeting():
    """晚安问候"""
    if not config.get("auto_chat.night.enabled", True):
        return
    
    messages = config.get("auto_chat.night.messages", ["大家晚安！🌙"])
    message = random_choice(messages)
    await send_group_message(message)

# 随机话题
@scheduler.scheduled_job("interval", hours=2, id="random_topic")
async def random_topic():
    """随机话题"""
    if not config.get("auto_chat.random_topic.enabled", True):
        return
    
    # 概率判断
    probability = config.get("auto_chat.random_topic.probability", 0.3)
    if random.random() > probability:
        logger.info("[定时任务] 随机话题未触发（概率）")
        return
    
    topics = config.get("auto_chat.random_topic.topics", ["今天天气不错呢"])
    topic = random_choice(topics)
    await send_group_message(topic)

# 生日提醒
@scheduler.scheduled_job("cron", hour=9, minute=0, id="birthday_reminder")
async def birthday_reminder():
    """生日提醒"""
    if not config.get("member_management.birthday_reminder", True):
        return
    
    # 获取今天生日的群友
    birthday_members = member_db.get_today_birthdays()
    
    if not birthday_members:
        logger.info("[定时任务] 今天没有群友生日")
        return
    
    # 为每个过生日的群友发送祝福
    for member in birthday_members:
        nickname = member.get('nickname') or member.get('group_card') or member.get('qq_name') or member['qq_id']
        
        message = f"""🎂✨ 生日快乐 ✨🎂

今天是{nickname}的生日！
祝{nickname}生日快乐，心想事成！🎉
愿你在新的一岁里，
健康快乐，万事顺意！🌟

大家一起来祝福{nickname}吧~ 🎈"""
        
        await send_group_message(message)
        logger.info(f"[定时任务] 已发送生日祝福: {nickname}")

logger.info("定时任务已加载")
