"""全面测试脚本 - 测试所有核心功能"""
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
        print(f"       {details}")

# ============================================================================
# 1. 环境检查
# ============================================================================
print_section("1. 环境检查")

# 1.1 Python版本
print_subsection("1.1 Python版本")
import sys
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
test_result("Python版本", sys.version_info >= (3, 8), f"当前版本: {python_version}")

# 1.2 虚拟环境
print_subsection("1.2 虚拟环境")
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
test_result("虚拟环境", in_venv, "已激活" if in_venv else "未激活")

# 1.3 依赖包
print_subsection("1.3 依赖包")
required_packages = {
    "nonebot2": "nonebot",
    "nonebot-adapter-onebot": "nonebot.adapters.onebot",
    "openai": "openai",
    "requests": "requests",
    "pyyaml": "yaml",
    "chromadb": "chromadb",
}

for package_name, import_name in required_packages.items():
    try:
        __import__(import_name)
        test_result(package_name, True, "已安装")
    except ImportError:
        test_result(package_name, False, "未安装")

# ============================================================================
# 2. 配置检查
# ============================================================================
print_section("2. 配置检查")

# 2.1 配置文件
print_subsection("2.1 配置文件")
config_files = {
    "config/config.yaml": "主配置文件",
    "config/.env": "环境变量文件",
}

for file_path, desc in config_files.items():
    exists = Path(file_path).exists()
    test_result(desc, exists, file_path)

# 2.2 配置加载
print_subsection("2.2 配置加载")
try:
    from src.utils.config import get_config
    config = get_config()
    test_result("配置加载", True, "成功")
    
    # 检查关键配置
    bot_qq = config.bot_qq
    admin_qq = config.admin_qq
    target_group = config.target_group
    
    print(f"       Bot QQ: {bot_qq}")
    print(f"       Admin QQ: {admin_qq}")
    print(f"       Target Group: {target_group}")
    
except Exception as e:
    test_result("配置加载", False, str(e))
    config = None

# 2.3 API密钥
print_subsection("2.3 API密钥")
if config:
    deepseek_key = config.get_env("DEEPSEEK_API_KEY")
    dashscope_key = config.get_env("DASHSCOPE_API_KEY")
    
    test_result("DeepSeek API Key", 
                deepseek_key and deepseek_key != "your_api_key_here",
                "已配置" if deepseek_key and deepseek_key != "your_api_key_here" else "未配置")
    
    test_result("DashScope API Key", 
                dashscope_key and dashscope_key != "your_dashscope_api_key_here",
                "已配置" if dashscope_key and dashscope_key != "your_dashscope_api_key_here" else "未配置")

# 2.4 功能开关
print_subsection("2.4 功能开关")
if config:
    features = {
        "mention_reply": "@ 回复",
        "name_reply": "名字触发",
        "keyword_reply": "关键词回复",
        "smart_reply": "智能回复",
        "auto_chat": "主动聊天",
        "bilibili_parse": "B站解析",
    }
    
    for key, name in features.items():
        enabled = config.get(f"features.{key}", False)
        test_result(name, enabled, "已启用" if enabled else "已禁用")

# ============================================================================
# 3. 文件结构检查
# ============================================================================
print_section("3. 文件结构检查")

# 3.1 核心文件
print_subsection("3.1 核心文件")
core_files = {
    "src/bot.py": "Bot入口",
    "src/utils/config.py": "配置管理",
    "src/ai/client.py": "AI客户端",
    "src/ai/prompts.py": "提示词",
    "src/memory/memory_manager.py": "记忆管理",
    "src/utils/web_search.py": "联网搜索",
}

for file_path, desc in core_files.items():
    exists = Path(file_path).exists()
    test_result(desc, exists, file_path)

# 3.2 触发器文件
print_subsection("3.2 触发器文件")
trigger_files = {
    "src/triggers/__init__.py": "触发器初始化",
    "src/triggers/name.py": "名字触发器",
    "src/triggers/keyword.py": "关键词触发器",
    "src/triggers/smart.py": "智能触发器",
    "src/triggers/scheduler.py": "定时任务",
}

for file_path, desc in trigger_files.items():
    exists = Path(file_path).exists()
    test_result(desc, exists, file_path)

# 3.3 插件文件
print_subsection("3.3 插件文件")
plugin_files = {
    "src/plugins/chat_handler.py": "聊天处理",
    "src/plugins/member_manager.py": "群友管理",
    "src/plugins/bilibili.py": "B站解析",
    "src/plugins/proactive_chat.py": "主动对话",
}

for file_path, desc in plugin_files.items():
    exists = Path(file_path).exists()
    test_result(desc, exists, file_path)

# ============================================================================
# 4. 代码质量检查
# ============================================================================
print_section("4. 代码质量检查")

# 4.1 触发器加载顺序
print_subsection("4.1 触发器加载顺序")
bot_file = Path("src/bot.py")
if bot_file.exists():
    content = bot_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    trigger_lines = []
    plugin_line = -1
    
    for i, line in enumerate(lines, 1):
        if 'load_plugin("src.triggers.' in line:
            trigger_lines.append(i)
        if 'load_plugins("src/plugins")' in line:
            plugin_line = i
    
    if trigger_lines and plugin_line != -1:
        correct_order = all(t < plugin_line for t in trigger_lines)
        test_result("加载顺序", correct_order, 
                   f"触发器: 行{trigger_lines}, 插件: 行{plugin_line}")
    else:
        test_result("加载顺序", False, "未找到加载语句")

# 4.2 触发器 __init__.py
print_subsection("4.2 触发器 __init__.py")
init_file = Path("src/triggers/__init__.py")
if init_file.exists():
    content = init_file.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.split("\n") 
             if line.strip() and not line.strip().startswith("#")]
    
    is_clean = not lines or lines == ['__all__ = []'] or lines == ['"""触发器模块"""', '__all__ = []']
    test_result("__init__.py 清空", is_clean, 
               "已清空" if is_clean else f"包含内容: {lines[:3]}")

# 4.3 触发器 block 参数
print_subsection("4.3 触发器 block 参数")
import re

trigger_configs = {
    "name": {"priority": 8, "block": False},
    "keyword": {"priority": 10, "block": False},
    "smart": {"priority": 15, "block": False},
}

for trigger_name, expected in trigger_configs.items():
    trigger_file = Path(f"src/triggers/{trigger_name}.py")
    if trigger_file.exists():
        content = trigger_file.read_text(encoding="utf-8")
        match = re.search(r'on_message\(priority=(\d+),\s*block=(True|False)\)', content)
        
        if match:
            priority = int(match.group(1))
            block = match.group(2) == "True"
            
            correct = priority == expected["priority"] and block == expected["block"]
            test_result(f"{trigger_name} 触发器", correct,
                       f"priority={priority}, block={block}")
        else:
            test_result(f"{trigger_name} 触发器", False, "未找到配置")

# 4.4 IgnoredException 使用
print_subsection("4.4 IgnoredException 使用")
for trigger_name in ["name", "keyword"]:
    trigger_file = Path(f"src/triggers/{trigger_name}.py")
    if trigger_file.exists():
        content = trigger_file.read_text(encoding="utf-8")
        
        has_import = "from nonebot.exception import IgnoredException" in content
        has_raise = "raise IgnoredException" in content
        count = content.count("raise IgnoredException")
        
        correct = has_import and has_raise
        test_result(f"{trigger_name} IgnoredException", correct,
                   f"导入: {has_import}, 使用: {count}处")

# ============================================================================
# 5. 功能模块测试
# ============================================================================
print_section("5. 功能模块测试")

# 5.1 AI客户端
print_subsection("5.1 AI客户端")
try:
    from src.ai.client import get_ai_client
    ai_client = get_ai_client()
    test_result("AI客户端初始化", True, f"提供商: {ai_client.provider}")
    
    # 检查自动搜索功能
    has_auto_search = hasattr(ai_client, '_should_auto_search')
    test_result("自动搜索功能", has_auto_search, "已实现" if has_auto_search else "未实现")
    
    if has_auto_search:
        # 测试自动搜索判断
        test_cases = [
            ("（歪着头）这个我不太清楚呢", True),
            ("（小声）我不知道这个", True),
            ("抱歉，我不了解", True),
            ("（点点头）今天天气很好呢", False),
        ]
        
        all_passed = True
        for reply, expected in test_cases:
            result = ai_client._should_auto_search(reply, [])
            if result != expected:
                all_passed = False
                break
        
        test_result("自动搜索判断", all_passed, 
                   f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("AI客户端初始化", False, str(e))

# 5.2 联网搜索
print_subsection("5.2 联网搜索")
try:
    from src.utils.web_search import get_web_search_client
    web_search_client = get_web_search_client()
    test_result("联网搜索初始化", True, 
               f"已启用" if web_search_client.enabled else "未启用")
    
    # 测试搜索判断
    if web_search_client.enabled:
        test_cases = [
            ("今天天气怎么样", True),
            ("现在几点了", True),
            ("你好", False),
        ]
        
        all_passed = True
        for message, expected in test_cases:
            result = web_search_client.should_search(message)
            if result != expected:
                all_passed = False
                break
        
        test_result("搜索判断", all_passed, f"测试 {len(test_cases)} 个用例")
    
except Exception as e:
    test_result("联网搜索初始化", False, str(e))

# 5.3 记忆管理
print_subsection("5.3 记忆管理")
try:
    from src.memory.memory_manager import get_memory_manager
    memory_manager = get_memory_manager()
    test_result("记忆管理初始化", True, "成功")
    
    # 检查向量数据库
    vector_enabled = config.get("memory.vector_db.enabled", False) if config else False
    test_result("向量数据库", vector_enabled, 
               "已启用" if vector_enabled else "已禁用")
    
except Exception as e:
    test_result("记忆管理初始化", False, str(e))

# 5.4 内容过滤
print_subsection("5.4 内容过滤")
try:
    from src.utils.content_filter import get_content_filter
    content_filter = get_content_filter()
    test_result("内容过滤初始化", True, "成功")
    
    # 测试敏感词检测
    test_message = "这是一条正常的消息"
    should_ignore, reason = content_filter.should_ignore_message(test_message)
    test_result("敏感词检测", not should_ignore, "正常消息未被过滤")
    
except Exception as e:
    test_result("内容过滤初始化", False, str(e))

# 5.5 辅助函数
print_subsection("5.5 辅助函数")
try:
    from src.utils.helpers import is_at_bot, remove_at, contains_keyword, has_bilibili_link
    
    # 测试 is_at_bot
    result = is_at_bot("[CQ:at,qq=3966049171] 你好", "3966049171")
    test_result("is_at_bot", result == True, f"结果: {result}")
    
    # 测试 remove_at
    result = remove_at("[CQ:at,qq=3966049171] 你好")
    test_result("remove_at", result == "你好", f"结果: '{result}'")
    
    # 测试 contains_keyword
    result = contains_keyword("今天天气怎么样", ["天气", "时间"])
    test_result("contains_keyword", result == True, f"结果: {result}")
    
    # 测试 has_bilibili_link
    result = has_bilibili_link("看看这个视频 BV1234567890")
    test_result("has_bilibili_link", result == True, f"结果: {result}")
    
except Exception as e:
    test_result("辅助函数", False, str(e))

# ============================================================================
# 6. 数据库检查
# ============================================================================
print_section("6. 数据库检查")

# 6.1 数据目录
print_subsection("6.1 数据目录")
data_dirs = {
    "data": "数据根目录",
    "data/logs": "日志目录",
    "data/chroma": "向量数据库目录",
}

for dir_path, desc in data_dirs.items():
    exists = Path(dir_path).exists()
    test_result(desc, exists, dir_path)

# 6.2 数据库文件
print_subsection("6.2 数据库文件")
db_file = Path("data/bot.db")
if db_file.exists():
    size = db_file.stat().st_size
    test_result("SQLite数据库", True, f"大小: {size:,} 字节")
    
    # 检查数据库内容
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        test_result("数据库表", len(tables) > 0, f"表数量: {len(tables)}")
        
        # 检查群友记录
        if "members" in tables:
            cursor.execute("SELECT COUNT(*) FROM members")
            count = cursor.fetchone()[0]
            test_result("群友记录", count >= 0, f"记录数: {count}")
        
        # 检查聊天记录
        if "chat_history" in tables:
            cursor.execute("SELECT COUNT(*) FROM chat_history")
            count = cursor.fetchone()[0]
            test_result("聊天记录", count >= 0, f"记录数: {count}")
        
        conn.close()
        
    except Exception as e:
        test_result("数据库检查", False, str(e))
else:
    test_result("SQLite数据库", False, "文件不存在")

# 6.3 日志文件
print_subsection("6.3 日志文件")
log_dir = Path("data/logs")
if log_dir.exists():
    log_files = list(log_dir.glob("*.log"))
    test_result("日志文件", len(log_files) > 0, f"文件数: {len(log_files)}")
    
    if log_files:
        latest = max(log_files, key=lambda p: p.stat().st_mtime)
        test_result("最新日志", True, f"{latest.name}")
else:
    test_result("日志文件", False, "日志目录不存在")

# ============================================================================
# 7. NapCat 配置检查
# ============================================================================
print_section("7. NapCat 配置检查")

# 7.1 NapCat 目录
print_subsection("7.1 NapCat 目录")
napcat_dirs = {
    "napcat/napcat": "NapCat 根目录",
    "napcat/napcat/config": "配置目录",
    "napcat/napcat/cache": "缓存目录",
}

for dir_path, desc in napcat_dirs.items():
    exists = Path(dir_path).exists()
    test_result(desc, exists, dir_path)

# 7.2 NapCat 配置文件
print_subsection("7.2 NapCat 配置文件")
napcat_config = Path("napcat/napcat/config/onebot11_3966049171.json")
if napcat_config.exists():
    test_result("OneBot配置", True, napcat_config.name)
    
    try:
        import json
        with open(napcat_config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 检查关键配置
        network = config_data.get("network", {})
        ws_clients = network.get("websocketClients", [])
        
        if ws_clients:
            # 检查第一个WebSocket客户端配置
            ws_config = ws_clients[0]
            enable = ws_config.get("enable", False)
            url = ws_config.get("url", "")
            
            test_result("WebSocket配置", enable, 
                       f"已启用, URL: {url}")
        else:
            test_result("WebSocket配置", False, "未配置WebSocket客户端")
        
    except Exception as e:
        test_result("配置解析", False, str(e))
else:
    test_result("OneBot配置", False, "文件不存在")

# ============================================================================
# 8. 启动脚本检查
# ============================================================================
print_section("8. 启动脚本检查")

# 8.1 启动脚本
print_subsection("8.1 启动脚本")
scripts = {
    "quick_login.bat": "快速登录",
    "install.bat": "安装脚本",
    "scripts/watch_log.bat": "日志监控",
    "scripts/diagnose_bot.bat": "诊断脚本",
}

for script_path, desc in scripts.items():
    exists = Path(script_path).exists()
    test_result(desc, exists, script_path)

# 8.2 quick_login.bat 检查
print_subsection("8.2 quick_login.bat 检查")
quick_login = Path("quick_login.bat")
if quick_login.exists():
    content = quick_login.read_text(encoding="utf-8")
    
    # 检查是否激活虚拟环境
    has_venv = "venv\\Scripts\\activate" in content or "call venv" in content
    test_result("激活虚拟环境", has_venv, 
               "已包含" if has_venv else "未包含")
    
    # 检查是否启动NapCat
    has_napcat = "launcher.bat" in content
    test_result("启动NapCat", has_napcat, 
               "已包含" if has_napcat else "未包含")
    
    # 检查是否启动Bot
    has_bot = "python src/bot.py" in content or "python src\\bot.py" in content
    test_result("启动Bot", has_bot, 
               "已包含" if has_bot else "未包含")

# ============================================================================
# 9. 总结
# ============================================================================
print_section("9. 测试总结")

print("\n所有测试已完成！")
print("\n如果所有测试都通过，可以运行以下命令启动Bot：")
print("  quick_login.bat")
print("\n如果有测试失败，请根据提示修复问题。")
print("\n常见问题：")
print("  1. 依赖包未安装 → 运行 install.bat")
print("  2. API密钥未配置 → 编辑 config/.env")
print("  3. 配置文件缺失 → 复制 config.yaml.example")
print("  4. 虚拟环境未激活 → 运行 venv\\Scripts\\activate.bat")
print("\n" + "=" * 80)
