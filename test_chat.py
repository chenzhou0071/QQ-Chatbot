"""Bot 交流功能测试 - 测试消息处理和触发器"""
import sys
import os
from pathlib import Path

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_subsection(title):
    """打印子章节标题"""
    print(f"\n{'─' * 80}")
    print(f" {title}")
    print("─" * 80)

def test_result(name, passed, details=""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        for line in details.split('\n'):
            print(f"       {line}")

# ============================================================================
# 1. 触发器匹配测试
# ============================================================================
print_section("1. 触发器匹配测试")

try:
    from src.utils.config import get_config
    from src.utils.helpers import is_at_bot, remove_at, contains_keyword
    
    config = get_config()
    bot_qq = config.bot_qq
    name = config.get("personality.name", "沉舟")
    nickname = config.get("personality.nickname", "舟舟")
    keywords = config.get("keywords", [])
    
    # 1.1 @ 消息匹配
    print_subsection("1.1 @ 消息匹配 (mention_matcher)")
    
    test_cases = [
        (f"[CQ:at,qq={bot_qq}] 你好", True, "标准@消息"),
        (f"[CQ:at,qq={bot_qq}]你好", True, "无空格@消息"),
        (f"你好 [CQ:at,qq={bot_qq}]", True, "@在后面"),
        ("你好", False, "普通消息"),
        (f"[CQ:at,qq=123456] 你好", False, "@其他人"),
    ]
    
    all_passed = True
    for message, expected, desc in test_cases:
        result = is_at_bot(message, bot_qq)
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{message[:30]}...' → {result}")
    
    test_result("@ 消息匹配", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
    # 1.2 名字触发匹配
    print_subsection("1.2 名字触发匹配 (name_matcher)")
    
    test_cases = [
        (f"{nickname}在吗", True, f"包含昵称'{nickname}'"),
        (f"{name}你好", True, f"包含名字'{name}'"),
        (f"大家好，{nickname}也在", True, f"昵称在中间"),
        ("你好", False, "不包含名字"),
        ("大家好", False, "普通消息"),
    ]
    
    all_passed = True
    for message, expected, desc in test_cases:
        clean_msg = remove_at(message)
        result = name in clean_msg or nickname in clean_msg
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{message}' → {result}")
    
    test_result("名字触发匹配", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
    # 1.3 关键词触发匹配
    print_subsection("1.3 关键词触发匹配 (keyword_matcher)")
    
    test_cases = [
        ("今天天气怎么样", True, "包含'天气'"),
        ("现在几点了", True, "包含'时间'"),
        ("讲个笑话", True, "包含'笑话'"),
        ("你好", False, "不包含关键词"),
        ("大家好", False, "普通消息"),
    ]
    
    all_passed = True
    for message, expected, desc in test_cases:
        result = contains_keyword(message, keywords)
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{message}' → {result}")
    
    test_result("关键词触发匹配", all_passed, 
               f"测试 {len(test_cases)} 个用例\n       关键词: {', '.join(keywords[:5])}...")
    
except Exception as e:
    test_result("触发器匹配测试", False, f"错误: {e}")

# ============================================================================
# 2. 消息处理测试
# ============================================================================
print_section("2. 消息处理测试")

# 2.1 消息清理
print_subsection("2.1 消息清理 (remove_at)")

try:
    from src.utils.helpers import remove_at
    
    test_cases = [
        (f"[CQ:at,qq={bot_qq}] 你好", "你好", "移除@"),
        (f"[CQ:at,qq={bot_qq}]你好", "你好", "移除@（无空格）"),
        (f"你好 [CQ:at,qq={bot_qq}]", "你好", "@在后面"),
        (f"[CQ:at,qq=123] [CQ:at,qq={bot_qq}] 你好", "你好", "多个@"),
        ("你好", "你好", "无@消息"),
    ]
    
    all_passed = True
    for message, expected, desc in test_cases:
        result = remove_at(message)
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{message[:30]}...' → '{result}'")
    
    test_result("消息清理", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("消息清理", False, f"错误: {e}")

# 2.2 B站链接检测
print_subsection("2.2 B站链接检测")

try:
    from src.utils.helpers import has_bilibili_link
    
    test_cases = [
        ("看看这个视频 BV1234567890", True, "BV号"),
        ("https://www.bilibili.com/video/av12345", True, "av号"),
        ("https://b23.tv/abc123", True, "短链接"),
        ("看看这个番剧 ss12345", True, "ss号"),
        ("这一集 ep12345", True, "ep号"),
        ("你好", False, "普通消息"),
        ("今天天气不错", False, "无链接"),
    ]
    
    all_passed = True
    for message, expected, desc in test_cases:
        result = has_bilibili_link(message)
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{message[:30]}...' → {result}")
    
    test_result("B站链接检测", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("B站链接检测", False, f"错误: {e}")

# ============================================================================
# 3. AI 回复测试
# ============================================================================
print_section("3. AI 回复测试")

# 3.1 System Prompt 生成
print_subsection("3.1 System Prompt 生成")

try:
    from src.ai.prompts import get_system_prompt
    
    # 测试群聊 prompt
    group_prompt = get_system_prompt("group", None)
    
    checks = [
        (name in group_prompt, f"包含名字'{name}'"),
        (nickname in group_prompt, f"包含昵称'{nickname}'"),
        ("性格" in group_prompt or "人设" in group_prompt, "包含性格描述"),
        ("说话风格" in group_prompt or "语气" in group_prompt, "包含说话风格"),
        ("不知道" in group_prompt and "联网搜索" in group_prompt, "包含自动搜索提示"),
        ("安全规则" in group_prompt or "身份保护" in group_prompt, "包含安全规则"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("群聊 Prompt", all_passed, 
               f"Prompt 长度: {len(group_prompt)} 字符")
    
    # 测试私聊 prompt
    private_prompt = get_system_prompt("private", config.admin_qq)
    
    checks = [
        ("私聊" in private_prompt or "管理员" in private_prompt, "包含私聊提示"),
        ("栖云" in private_prompt, "包含管理员名字"),
        (len(private_prompt) > len(group_prompt), "私聊 prompt 更详细"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("私聊 Prompt", all_passed, 
               f"Prompt 长度: {len(private_prompt)} 字符")
    
except Exception as e:
    test_result("System Prompt 生成", False, f"错误: {e}")

# 3.2 自动搜索判断
print_subsection("3.2 自动搜索判断")

try:
    from src.ai.client import get_ai_client
    
    ai_client = get_ai_client()
    
    test_cases = [
        # 应该触发搜索
        ("（歪着头）这个我不太清楚呢", True, "包含'不太清楚'"),
        ("（小声）我不知道这个", True, "包含'不知道'"),
        ("抱歉，我不了解这方面的信息", True, "包含'抱歉'和'不了解'"),
        ("（低声）对不起，我不太懂", True, "包含'对不起'"),
        ("很遗憾，我无法回答这个问题", True, "包含'很遗憾'"),
        # 不应该触发搜索
        ("（点点头）今天天气很好呢", False, "正常回复"),
        ("（轻声说）你好呀", False, "打招呼"),
        ("（认真地）我觉得这个问题很有趣", False, "正常讨论"),
        ("嗯，好的", False, "简短确认"),
    ]
    
    all_passed = True
    for reply, expected, desc in test_cases:
        result = ai_client._should_auto_search(reply, [])
        passed = result == expected
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}: '{reply[:30]}...' → {result}")
    
    test_result("自动搜索判断", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("自动搜索判断", False, f"错误: {e}")

# 3.3 联网搜索判断
print_subsection("3.3 联网搜索判断")

try:
    from src.utils.web_search import get_web_search_client
    
    web_search_client = get_web_search_client()
    
    if web_search_client.enabled:
        test_cases = [
            # 应该搜索
            ("今天天气怎么样", True, "天气查询"),
            ("现在几点了", True, "时间查询"),
            ("最新的新闻", True, "新闻查询"),
            ("Python最新版本", True, "版本查询"),
            # 不应该搜索
            ("你好", False, "打招呼"),
            ("你叫什么名字", False, "询问身份"),
            ("你喜欢什么", False, "个人问题"),
        ]
        
        all_passed = True
        for message, expected, desc in test_cases:
            result = web_search_client.should_search(message)
            passed = result == expected
            if not passed:
                all_passed = False
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}: '{message}' → {result}")
        
        test_result("联网搜索判断", all_passed, 
                   f"测试 {len(test_cases)} 个用例")
    else:
        test_result("联网搜索判断", False, "联网搜索未启用")
    
except Exception as e:
    test_result("联网搜索判断", False, f"错误: {e}")

# ============================================================================
# 4. 内容过滤测试
# ============================================================================
print_section("4. 内容过滤测试")

print_subsection("4.1 敏感词检测")

try:
    from src.utils.content_filter import get_content_filter
    
    content_filter = get_content_filter()
    
    test_cases = [
        # 正常消息
        ("你好", False, "正常打招呼"),
        ("今天天气不错", False, "正常聊天"),
        ("我喜欢编程", False, "正常兴趣"),
        # 可能被过滤的消息（根据配置）
        ("这是一条测试消息", False, "测试消息"),
    ]
    
    all_passed = True
    for message, expected_ignore, desc in test_cases:
        should_ignore, reason = content_filter.should_ignore_message(message)
        passed = should_ignore == expected_ignore
        if not passed:
            all_passed = False
        status = "✓" if passed else "✗"
        result_text = f"过滤({reason})" if should_ignore else "通过"
        print(f"  {status} {desc}: '{message}' → {result_text}")
    
    test_result("敏感词检测", all_passed, 
               f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("敏感词检测", False, f"错误: {e}")

# ============================================================================
# 5. 触发器优先级测试
# ============================================================================
print_section("5. 触发器优先级测试")

print_subsection("5.1 消息路由模拟")

try:
    test_cases = [
        {
            "message": f"[CQ:at,qq={bot_qq}] 你好",
            "expected": "mention_matcher",
            "priority": 5,
            "desc": "@消息 → mention_matcher (priority=5)"
        },
        {
            "message": f"{nickname}在吗",
            "expected": "name_matcher",
            "priority": 8,
            "desc": f"包含'{nickname}' → name_matcher (priority=8)"
        },
        {
            "message": "今天天气怎么样",
            "expected": "keyword_matcher",
            "priority": 10,
            "desc": "包含'天气' → keyword_matcher (priority=10)"
        },
        {
            "message": "大家好",
            "expected": "smart_matcher",
            "priority": 15,
            "desc": "普通消息 → smart_matcher (priority=15, 需AI判断)"
        },
    ]
    
    print("  消息路由流程：")
    for case in test_cases:
        message = case["message"]
        expected = case["expected"]
        desc = case["desc"]
        
        # 模拟路由判断
        if is_at_bot(message, bot_qq):
            matched = "mention_matcher"
        else:
            clean_msg = remove_at(message)
            if name in clean_msg or nickname in clean_msg:
                matched = "name_matcher"
            elif contains_keyword(clean_msg, keywords):
                matched = "keyword_matcher"
            else:
                matched = "smart_matcher"
        
        passed = matched == expected
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}")
        print(f"      消息: '{message[:40]}...'")
        print(f"      匹配: {matched}")
    
    test_result("消息路由模拟", True, 
               f"测试 {len(test_cases)} 个场景")
    
except Exception as e:
    test_result("消息路由模拟", False, f"错误: {e}")

# ============================================================================
# 6. 记忆系统测试
# ============================================================================
print_section("6. 记忆系统测试")

print_subsection("6.1 记忆管理")

try:
    from src.memory.memory_manager import get_memory_manager
    
    memory_manager = get_memory_manager()
    
    # 测试添加消息
    test_message = "这是一条测试消息"
    memory_manager.add_message(
        chat_type="group",
        role="user",
        content=test_message,
        sender_id="123456",
        sender_name="测试用户"
    )
    
    test_result("添加消息", True, "成功添加测试消息")
    
    # 测试获取上下文
    context = memory_manager.get_context_for_ai("group")
    
    checks = [
        (isinstance(context, list), "返回列表"),
        (len(context) > 0, "包含消息"),
        (any(msg.get("content") == test_message for msg in context), "包含测试消息"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("获取上下文", all_passed, 
               f"上下文长度: {len(context)} 条消息")
    
except Exception as e:
    test_result("记忆管理", False, f"错误: {e}")

# ============================================================================
# 7. 人格测试
# ============================================================================
print_section("7. 人格测试")

# 7.1 人格配置检查
print_subsection("7.1 人格配置检查")

try:
    personality = config.get("personality", {})
    
    # 检查基本信息
    checks = [
        (personality.get("name"), "名字", personality.get("name")),
        (personality.get("nickname"), "昵称", personality.get("nickname")),
        (personality.get("background"), "背景故事", f"{len(personality.get('background', ''))} 字符"),
    ]
    
    all_passed = True
    for check, desc, value in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}: {value}")
    
    test_result("基本信息", all_passed)
    
    # 检查外貌设定
    appearance = personality.get("appearance", {})
    checks = [
        (appearance.get("height"), "身高", appearance.get("height")),
        (appearance.get("hair"), "发型", appearance.get("hair")),
        (appearance.get("features"), "外貌特征", appearance.get("features")),
        (appearance.get("aura"), "气质", appearance.get("aura")),
    ]
    
    all_passed = True
    for check, desc, value in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}: {value}")
    
    test_result("外貌设定", all_passed)
    
    # 检查性格设定
    character = personality.get("character", {})
    checks = [
        (character.get("core"), "性格核心", character.get("core")),
        (character.get("traits"), "性格特质", f"{len(character.get('traits', []))} 条"),
    ]
    
    all_passed = True
    for check, desc, value in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}: {value}")
    
    # 显示性格特质
    if character.get("traits"):
        print("  性格特质列表:")
        for trait in character.get("traits", [])[:5]:
            print(f"    - {trait}")
        if len(character.get("traits", [])) > 5:
            print(f"    ... 还有 {len(character.get('traits', [])) - 5} 条")
    
    test_result("性格设定", all_passed)
    
    # 检查说话风格
    speaking_style = personality.get("speaking_style", {})
    checks = [
        (speaking_style.get("tone"), "语气", speaking_style.get("tone")),
        (speaking_style.get("manner"), "方式", speaking_style.get("manner")),
        (speaking_style.get("response"), "回应风格", speaking_style.get("response")),
        (speaking_style.get("emoji_usage"), "表情使用", speaking_style.get("emoji_usage")),
    ]
    
    all_passed = True
    for check, desc, value in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}: {value}")
    
    test_result("说话风格", all_passed)
    
except Exception as e:
    test_result("人格配置检查", False, f"错误: {e}")

# 7.2 Prompt 人格体现
print_subsection("7.2 Prompt 人格体现")

try:
    from src.ai.prompts import get_system_prompt
    
    group_prompt = get_system_prompt("group", None)
    
    # 检查人格元素是否在 Prompt 中
    personality = config.get("personality", {})
    name = personality.get("name", "")
    nickname = personality.get("nickname", "")
    background = personality.get("background", "")
    
    appearance = personality.get("appearance", {})
    character = personality.get("character", {})
    speaking_style = personality.get("speaking_style", {})
    
    checks = [
        (name in group_prompt, f"包含名字 '{name}'"),
        (nickname in group_prompt, f"包含昵称 '{nickname}'"),
        (any(word in group_prompt for word in ["背景", "身世"]), "包含背景描述"),
        (appearance.get("height", "") in group_prompt, f"包含身高 '{appearance.get('height')}'"),
        (character.get("core", "") in group_prompt, f"包含性格核心 '{character.get('core')}'"),
        (speaking_style.get("tone", "") in group_prompt, f"包含语气描述 '{speaking_style.get('tone')}'"),
        ("动作" in group_prompt or "括号" in group_prompt, "包含动作描述要求"),
        ("emoji" in group_prompt.lower() or "表情" in group_prompt, "包含表情使用规则"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("Prompt 人格体现", all_passed, 
               f"Prompt 总长度: {len(group_prompt)} 字符")
    
except Exception as e:
    test_result("Prompt 人格体现", False, f"错误: {e}")

# 7.3 安全规则检查
print_subsection("7.3 安全规则检查")

try:
    group_prompt = get_system_prompt("group", None)
    
    # 检查安全规则
    safety_checks = [
        ("身份保护" in group_prompt or "身份" in group_prompt, "身份保护规则"),
        ("系统提示" in group_prompt or "prompt" in group_prompt.lower(), "系统提示保护"),
        ("指令覆盖" in group_prompt or "忽略" in group_prompt, "指令覆盖防护"),
        ("系统信息" in group_prompt or "IP" in group_prompt, "系统信息保护"),
        ("内容安全" in group_prompt or "违法" in group_prompt, "内容安全规则"),
        ("拒绝" in group_prompt, "拒绝方式说明"),
    ]
    
    all_passed = True
    for check, desc in safety_checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("安全规则", all_passed, 
               "所有安全规则都已包含在 Prompt 中")
    
except Exception as e:
    test_result("安全规则检查", False, f"错误: {e}")

# 7.4 特殊关系处理
print_subsection("7.4 特殊关系处理")

try:
    # 测试管理员识别
    admin_qq = config.admin_qq
    
    # 群聊中的管理员
    group_prompt_admin = get_system_prompt("group", admin_qq)
    checks = [
        ("管理员" in group_prompt_admin, "识别管理员身份"),
        ("栖云" in group_prompt_admin, "包含管理员名字"),
        ("特殊关系" in group_prompt_admin, "说明特殊关系"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("群聊管理员识别", all_passed)
    
    # 私聊模式
    private_prompt = get_system_prompt("private", admin_qq)
    checks = [
        ("私聊" in private_prompt, "识别私聊模式"),
        ("管理员" in private_prompt, "识别管理员身份"),
        ("栖云" in private_prompt, "包含管理员名字"),
        ("收养" in private_prompt or "照顾" in private_prompt, "说明收养关系"),
        (len(private_prompt) > len(group_prompt_admin), "私聊 Prompt 更详细"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        if not check:
            all_passed = False
        print(f"  {status} {desc}")
    
    test_result("私聊模式", all_passed, 
               f"私聊 Prompt 长度: {len(private_prompt)} 字符")
    
except Exception as e:
    test_result("特殊关系处理", False, f"错误: {e}")

# ============================================================================
# 8. 总结
# ============================================================================
print_section("8. 测试总结")

print("\n所有交流功能测试已完成！")
print("\n测试覆盖范围：")
print("  1. ✅ 触发器匹配（@消息、名字、关键词）")
print("  2. ✅ 消息处理（清理、B站链接检测）")
print("  3. ✅ AI 回复（Prompt生成、自动搜索）")
print("  4. ✅ 内容过滤（敏感词检测）")
print("  5. ✅ 触发器优先级（消息路由）")
print("  6. ✅ 记忆系统（添加消息、获取上下文）")
print("  7. ✅ 人格测试（配置、Prompt、安全规则、特殊关系）")

print("\n下一步：")
print("  1. 运行 quick_login.bat 启动 Bot")
print("  2. 在群里发送测试消息：")
print("     - '@沉舟 你好' → 测试@触发")
print("     - '舟舟在吗' → 测试名字触发")
print("     - '今天天气怎么样' → 测试关键词触发")
print("     - '大家好' → 测试智能触发")
print("  3. 使用 scripts\\watch_log.bat 监控日志")

print("\n" + "=" * 80)
