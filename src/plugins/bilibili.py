"""B站链接解析插件"""
import re
import json
import requests
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.exception import IgnoredException

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("bilibili")
config = get_config()

# 正则表达式 - 更宽松的匹配
REG_BV = re.compile(r'BV[0-9A-Za-z]{10}')  # BV号固定12位
REG_AV = re.compile(r'av(\d+)', re.IGNORECASE)
REG_B23 = re.compile(r'(b23\.tv|bili2233\.cn)[/\\\\]+(\w+)')  # 支持 / 和 \ 以及转义的 \/
REG_SS = re.compile(r'ss(\d+)', re.IGNORECASE)
REG_EP = re.compile(r'ep(\d+)', re.IGNORECASE)
REG_MD = re.compile(r'md(\d+)', re.IGNORECASE)

def extract_bili_url_from_json(message: str) -> str:
    """从QQ JSON卡片中提取B站链接"""
    try:
        # 匹配 [CQ:json,data=...] 格式
        json_match = re.search(r'\[CQ:json,data=(.+?)\]', message, re.DOTALL)
        if not json_match:
            return None
        
        json_str = json_match.group(1)
        # HTML 解码
        json_str = json_str.replace('&#44;', ',').replace('&#91;', '[').replace('&#93;', ']')
        
        # 解析 JSON
        data = json.loads(json_str)
        
        # 提取 qqdocurl
        if 'meta' in data and 'detail_1' in data['meta']:
            qqdocurl = data['meta']['detail_1'].get('qqdocurl', '')
            if qqdocurl:
                logger.debug(f"[B站解析] 从JSON提取到链接: {qqdocurl}")
                return qqdocurl
    except Exception as e:
        logger.debug(f"[B站解析] JSON解析失败: {e}")
    
    return None

# B站解析插件（优先级最高，但不阻断其他触发器）
bilibili_matcher = on_message(priority=3, block=False)

@bilibili_matcher.handle()
async def handle_bilibili(bot: Bot, event: GroupMessageEvent):
    """处理B站链接"""
    try:
        # 检查功能是否开启
        if not config.get("features.bilibili_parse", True):
            return  # 功能未开启，直接返回
        
        # 检查是否是目标群
        if str(event.group_id) != config.target_group:
            return  # 非目标群，直接返回
        
        message = str(event.get_message())
        
        # 快速预检查：只有包含B站关键词时才进行详细检查
        # 这样可以避免对图片、普通文字等消息进行不必要的正则匹配
        if not any(keyword in message for keyword in ['bilibili', 'b23.tv', 'BV', 'av', 'ss', 'ep', 'md', '哔哩哔哩']):
            return  # 不包含B站关键词，直接返回让其他插件处理
        
        # 调试：记录原始消息
        logger.debug(f"[B站解析] 原始消息: {message[:200]}")
        
        # 先尝试从 QQ JSON 卡片中提取链接
        json_url = extract_bili_url_from_json(message)
        if json_url:
            message = message + " " + json_url  # 将提取的链接添加到消息中
        
        # 检测是否包含B站链接
        has_bili_link = (
            REG_BV.search(message) or 
            REG_AV.search(message) or 
            REG_B23.search(message) or 
            REG_SS.search(message) or 
            REG_EP.search(message) or 
            REG_MD.search(message)
        )
        
        # 如果没有B站链接，让其他插件处理
        if not has_bili_link:
            return  # 未检测到B站链接，直接返回
        
        # 有B站链接，解析
        logger.info(f"[B站解析] 检测到B站链接，阻断其他触发器")
        
        # 按优先级检测链接类型并解析
        parsed = False
        
        # 1. 优先处理BV号
        if REG_BV.search(message):
            bv_match = REG_BV.search(message).group()
            logger.info(f"[B站解析] 匹配到BV号: {bv_match}")
            await parse_video(bot, event, bv_match, 'bv')
            parsed = True
        
        # 2. 处理AV号
        elif REG_AV.search(message):
            av_match = REG_AV.search(message).group(1)
            logger.info(f"[B站解析] 匹配到AV号: av{av_match}")
            await parse_video(bot, event, av_match, 'av')
            parsed = True
        
        # 3. 处理短链接
        elif REG_B23.search(message):
            logger.info(f"[B站解析] 匹配到短链接")
            await parse_short_link(bot, event, message)
            parsed = True
        
        # 4. 处理番剧
        elif REG_SS.search(message) or REG_EP.search(message) or REG_MD.search(message):
            logger.info(f"[B站解析] 匹配到番剧链接")
            await parse_bangumi(bot, event, message)
            parsed = True
        
        # 如果成功解析，阻止事件继续传播（已经通过 block=True 实现）
        if parsed:
            logger.info(f"[B站解析] 解析完成，已阻断其他触发器")
        else:
            logger.warning(f"[B站解析] 未能解析B站链接")
            
    except Exception as e:
        logger.error(f"[B站解析] 处理失败: {e}")
        # 解析失败时，让事件继续传播
        return

async def parse_video(bot: Bot, event: GroupMessageEvent, vid_id: str, vid_type: str):
    """解析视频"""
    try:
        # 提取视频ID
        if vid_type == 'bv':
            bvid = vid_id
        else:  # av
            avid = int(vid_id)
            bvid = av_to_bv(avid)
            if not bvid:
                logger.error(f"[B站解析] AV号转换失败: av{avid}")
                return
        
        logger.info(f"[B站解析] 开始解析视频: {bvid}")
        
        # 调用B站API
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data['code'] != 0:
            logger.error(f"[B站解析] API错误 (code={data['code']}): {data.get('message', '未知错误')}")
            # 如果视频不存在，不发送任何消息
            return
        
        info = data['data']
        
        # 格式化输出
        output = format_video_info(info, bvid)
        
        # 发送消息
        await send_bili_message(bot, event, output, info.get('pic'))
        
    except requests.RequestException as e:
        logger.error(f"[B站解析] 网络请求失败: {e}")
    except Exception as e:
        logger.error(f"[B站解析] 视频解析失败: {e}", exc_info=True)

async def parse_short_link(bot: Bot, event: GroupMessageEvent, message: str):
    """解析短链接"""
    try:
        match = REG_B23.search(message)
        if not match:
            return
            
        short_url = f"https://{match.group(1)}/{match.group(2)}"
        
        logger.info(f"[B站解析] 短链接: {short_url}")
        
        # 获取重定向后的真实链接
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(short_url, allow_redirects=True, timeout=10, headers=headers)
        real_url = response.url
        
        logger.info(f"[B站解析] 重定向到: {real_url}")
        
        # 从真实链接中提取BV号
        bv_match = REG_BV.search(real_url)
        if bv_match:
            bvid = bv_match.group()
            logger.info(f"[B站解析] 从短链接提取BV号: {bvid}")
            await parse_video(bot, event, bvid, 'bv')
        else:
            logger.warning(f"[B站解析] 短链接未找到BV号: {real_url}")
            
    except requests.RequestException as e:
        logger.error(f"[B站解析] 短链接请求失败: {e}")
    except Exception as e:
        logger.error(f"[B站解析] 短链接解析失败: {e}", exc_info=True)

async def parse_bangumi(bot: Bot, event: GroupMessageEvent, message: str):
    """解析番剧"""
    try:
        # 提取番剧ID
        epid = None
        ssid = None
        
        if REG_EP.search(message):
            epid = REG_EP.search(message).group(1)
        elif REG_MD.search(message):
            mdid = REG_MD.search(message).group(1)
            # 通过MD号获取SS号
            ssid = await md_to_ss(mdid)
            if not ssid:
                return
        else:
            ssid = REG_SS.search(message).group(1)
        
        # 如果有SS号但没有EP号，获取第一集的EP号
        if ssid and not epid:
            epid = await ss_to_ep(ssid)
            if not epid:
                return
        
        logger.info(f"[B站解析] 番剧: ep{epid}")
        
        # 调用B站API
        url = f"https://api.bilibili.com/pgc/view/web/season?ep_id={epid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data['code'] != 0:
            logger.error(f"[B站解析] API错误: {data.get('message', '未知错误')}")
            return
        
        info = data['result']
        
        # 格式化输出
        output = format_bangumi_info(info)
        
        # 发送消息
        await send_bili_message(bot, event, output, info.get('cover'))
        
    except Exception as e:
        logger.error(f"[B站解析] 番剧解析失败: {e}")

async def md_to_ss(mdid: str) -> str:
    """MD号转SS号"""
    try:
        url = f"https://api.bilibili.com/pgc/review/user?media_id={mdid}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data['code'] == 0:
            return str(data['result']['media']['season_id'])
    except Exception as e:
        logger.error(f"[B站解析] MD转SS失败: {e}")
    return None

async def ss_to_ep(ssid: str) -> str:
    """SS号转EP号（获取第一集）"""
    try:
        url = f"https://api.bilibili.com/pgc/web/season/section?season_id={ssid}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data['code'] == 0:
            episodes = data['result']['main_section']['episodes']
            if episodes:
                ep_url = episodes[0]['share_url']
                return ep_url.split('ep')[-1]
    except Exception as e:
        logger.error(f"[B站解析] SS转EP失败: {e}")
    return None

def av_to_bv(avid: int) -> str:
    """AV号转BV号"""
    try:
        table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
        tr = {table[i]: i for i in range(58)}
        s = [11, 10, 3, 8, 4, 6]
        xor = 177451812
        add = 8728348608
        
        x = (avid ^ xor) + add
        r = list('BV1  4 1 7  ')
        for i in range(6):
            r[s[i]] = table[x // (58 ** i) % 58]
        
        return ''.join(r)
    except Exception as e:
        logger.error(f"[B站解析] AV转BV失败: {e}")
        return None

def format_number(num: int) -> str:
    """格式化数字"""
    if num < 10000:
        return str(num)
    return f"{num/10000:.1f}万"

def format_video_info(info: dict, bvid: str) -> str:
    """格式化视频信息"""
    stat = info['stat']
    owner = info['owner']
    
    output = f"【{info['title']}】\n"
    output += f"🔗 https://www.bilibili.com/video/{bvid}\n"
    output += f"👤 作者：{owner['name']}\n"
    output += f"📊 播放：{format_number(stat['view'])} | 弹幕：{format_number(stat['danmaku'])}\n"
    output += f"👍 点赞：{format_number(stat['like'])} | 💰 投币：{format_number(stat['coin'])}\n"
    output += f"⭐ 收藏：{format_number(stat['favorite'])} | 💬 评论：{format_number(stat['reply'])}"
    
    return output

def format_bangumi_info(info: dict) -> str:
    """格式化番剧信息"""
    stat = info['stat']
    rating = info.get('rating', {})
    
    output = f"【{info['title']}】\n"
    
    if rating:
        output += f"⭐ 评分：{rating.get('score', 'N/A')} / {format_number(rating.get('count', 0))}人\n"
    
    output += f"📺 {info['new_ep']['desc']}\n"
    output += f"🔗 {info['link']}\n"
    output += f"📊 播放：{format_number(stat['views'])} | 弹幕：{format_number(stat['danmakus'])}\n"
    output += f"👍 点赞：{format_number(stat.get('likes', 0))} | 💰 投币：{format_number(stat.get('coins', 0))}\n"
    output += f"📌 追番：{format_number(stat['favorites'])} | ⭐ 收藏：{format_number(stat.get('favorite', 0))}"
    
    return output

async def send_bili_message(bot: Bot, event: GroupMessageEvent, text: str, image_url: str = None):
    """发送B站解析消息"""
    try:
        show_image = config.get("bilibili.show_image", True)
        
        messages = []
        
        # 添加图片
        if show_image and image_url:
            messages.append(MessageSegment.image(image_url))
        
        # 添加文字
        messages.append(MessageSegment.text(text))
        
        await bot.send_group_msg(
            group_id=event.group_id,
            message=Message(messages)
        )
        
        logger.info(f"[B站解析] 发送成功")
        
    except Exception as e:
        logger.error(f"[B站解析] 发送失败: {e}")

logger.info("B站解析插件已加载")
                                                 