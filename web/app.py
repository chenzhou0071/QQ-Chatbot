"""
QQ Bot Web管理界面 - Flask后端
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import subprocess
import threading
import yaml
import os
import time
import psutil
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qq-bot-secret-key-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 配置路径
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / 'config' / 'config.yaml'
ENV_PATH = BASE_DIR / 'config' / '.env'
LOG_DIR = BASE_DIR / 'data' / 'logs'
DB_PATH = BASE_DIR / 'data' / 'bot.db'


class BotManager:
    """Bot进程管理器"""
    
    def __init__(self):
        self.process = None
        self.log_thread = None
        self.running = False
        self.start_time = None
        self.log_buffer = []
        self.max_log_buffer = 1000
    
    def start(self):
        """启动bot"""
        if self.process is not None:
            return {'success': False, 'error': 'Bot已在运行'}
        
        try:
            # 激活虚拟环境并启动bot
            python_exe = str(BASE_DIR / 'venv' / 'Scripts' / 'python.exe')
            bot_script = str(BASE_DIR / 'src' / 'bot.py')
            
            self.process = subprocess.Popen(
                [python_exe, bot_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
            
            self.running = True
            self.start_time = datetime.now()
            
            # 启动日志监听线程
            self.log_thread = threading.Thread(target=self._stream_logs, daemon=True)
            self.log_thread.start()
            
            return {'success': True, 'message': 'Bot启动成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop(self):
        """停止bot"""
        if self.process is None:
            return {'success': False, 'error': 'Bot未运行'}
        
        try:
            self.running = False
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
            self.start_time = None
            return {'success': True, 'message': 'Bot已停止'}
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process = None
            return {'success': True, 'message': 'Bot已强制停止'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restart(self):
        """重启bot"""
        stop_result = self.stop()
        if not stop_result['success']:
            return stop_result
        time.sleep(2)
        return self.start()
    
    def get_status(self):
        """获取bot状态"""
        if self.process and self.running:
            try:
                # 获取进程信息
                proc = psutil.Process(self.process.pid)
                memory_info = proc.memory_info()
                cpu_percent = proc.cpu_percent(interval=0.1)
                
                uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
                
                return {
                    'running': True,
                    'pid': self.process.pid,
                    'uptime': str(uptime).split('.')[0],  # 去掉微秒
                    'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                    'cpu_percent': round(cpu_percent, 1)
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.running = False
                self.process = None
                return {'running': False}
        
        return {'running': False}
    
    def _stream_logs(self):
        """实时推送日志"""
        while self.running and self.process:
            try:
                line = self.process.stdout.readline()
                if line:
                    log_entry = {
                        'message': line.strip(),
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # 添加到缓冲区
                    self.log_buffer.append(log_entry)
                    if len(self.log_buffer) > self.max_log_buffer:
                        self.log_buffer.pop(0)
                    
                    # 推送到前端
                    socketio.emit('log', log_entry)
            except Exception as e:
                print(f"日志流错误: {e}")
                break
    
    def get_recent_logs(self, count=100):
        """获取最近的日志"""
        return self.log_buffer[-count:]


# 全局Bot管理器
bot_manager = BotManager()


# ==================== 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """启动bot"""
    result = bot_manager.start()
    return jsonify(result)

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """停止bot"""
    result = bot_manager.stop()
    return jsonify(result)

@app.route('/api/bot/restart', methods=['POST'])
def restart_bot():
    """重启bot"""
    result = bot_manager.restart()
    return jsonify(result)

@app.route('/api/bot/status')
def bot_status():
    """获取bot状态"""
    return jsonify(bot_manager.get_status())

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """配置管理"""
    if request.method == 'GET':
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 读取环境变量
            env_data = {}
            if ENV_PATH.exists():
                with open(ENV_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_data[key.strip()] = value.strip()
            
            return jsonify({
                'success': True,
                'config': config_data,
                'env': env_data
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    else:  # POST
        try:
            data = request.json
            
            # 保存YAML配置
            if 'config' in data:
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    yaml.dump(data['config'], f, allow_unicode=True, default_flow_style=False)
            
            # 保存环境变量
            if 'env' in data:
                with open(ENV_PATH, 'w', encoding='utf-8') as f:
                    for key, value in data['env'].items():
                        f.write(f"{key}={value}\n")
            
            return jsonify({'success': True, 'message': '配置已保存'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats/today')
def stats_today():
    """今日统计"""
    try:
        # 从数据库读取统计数据
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 今日消息数
        cursor.execute("""
            SELECT COUNT(*) FROM chat_log 
            WHERE date(created_at) = ? AND is_bot = 0
        """, (today,))
        messages_received = cursor.fetchone()[0]
        
        # 今日回复数
        cursor.execute("""
            SELECT COUNT(*) FROM chat_log 
            WHERE date(created_at) = ? AND is_bot = 1
        """, (today,))
        replies_sent = cursor.fetchone()[0]
        
        conn.close()
        
        trigger_rate = round(replies_sent / messages_received, 2) if messages_received > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'messages_received': messages_received,
                'replies_sent': replies_sent,
                'proactive_messages': 0,  # TODO: 从配置或日志中获取
                'trigger_rate': trigger_rate
            }
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'data': {
                'messages_received': 0,
                'replies_sent': 0,
                'proactive_messages': 0,
                'trigger_rate': 0
            }
        })

@app.route('/api/logs/recent')
def recent_logs():
    """获取最近日志"""
    count = request.args.get('count', 100, type=int)
    logs = bot_manager.get_recent_logs(count)
    return jsonify({'success': True, 'logs': logs})

@app.route('/api/members')
def get_members():
    """获取群友列表"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT qq_id, nickname, ai_nickname, birthday, notes, message_count, last_seen_at
            FROM group_member
            ORDER BY message_count DESC
        """)
        
        members = []
        for row in cursor.fetchall():
            members.append({
                'qq': row[0],
                'nickname': row[1],
                'ai_nickname': row[2],
                'birthday': row[3],
                'notes': row[4],
                'message_count': row[5],
                'last_seen': row[6]
            })
        
        conn.close()
        return jsonify({'success': True, 'members': members})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'members': []})


# ==================== WebSocket事件 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('connected', {'message': '已连接到服务器'})
    # 发送最近的日志
    logs = bot_manager.get_recent_logs(50)
    emit('initial_logs', {'logs': logs})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('客户端断开连接')


# ==================== 启动服务器 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("QQ Bot Web管理界面")
    print("=" * 50)
    print(f"访问地址: http://localhost:5000")
    print(f"按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
