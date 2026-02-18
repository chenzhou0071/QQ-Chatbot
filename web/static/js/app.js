// Vue应用
const { createApp } = Vue;

createApp({
    data() {
        return {
            currentPage: 'dashboard',
            botStatus: {
                running: false,
                uptime: '-',
                memory_mb: 0,
                cpu_percent: 0
            },
            config: {
                bot: {
                    qq_number: '',
                    admin_qq: '',
                    target_group: ''
                },
                personality: {
                    name: '',
                    nickname: ''
                },
                features: {
                    mention_reply: true,
                    keyword_reply: true,
                    name_reply: true,
                    smart_reply: true
                },
                smart_reply: {
                    trigger_rate: 0.5
                },
                ai: {
                    temperature: 0.7
                }
            },
            env: {
                DEEPSEEK_API_KEY: '',
                DASHSCOPE_API_KEY: ''
            },
            stats: {
                messages_received: 0,
                replies_sent: 0,
                proactive_messages: 0,
                trigger_rate: 0
            },
            logs: [],
            recentLogs: [],
            members: [],
            socket: null,
            autoScroll: true,
            statusInterval: null
        }
    },
    methods: {
        // Bot控制
        async startBot() {
            try {
                const res = await fetch('/api/bot/start', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('Bot启动成功', 'success');
                    await this.updateStatus();
                } else {
                    this.showNotification('启动失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('启动失败: ' + error.message, 'error');
            }
        },
        
        async stopBot() {
            try {
                const res = await fetch('/api/bot/stop', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('Bot已停止', 'success');
                    await this.updateStatus();
                } else {
                    this.showNotification('停止失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('停止失败: ' + error.message, 'error');
            }
        },
        
        async restartBot() {
            try {
                const res = await fetch('/api/bot/restart', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('Bot重启成功', 'success');
                    await this.updateStatus();
                } else {
                    this.showNotification('重启失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('重启失败: ' + error.message, 'error');
            }
        },
        
        async updateStatus() {
            try {
                const res = await fetch('/api/bot/status');
                const data = await res.json();
                this.botStatus = data;
            } catch (error) {
                console.error('更新状态失败:', error);
            }
        },
        
        // 配置管理
        async loadConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                if (data.success) {
                    this.config = data.config;
                    this.env = data.env;
                    this.showNotification('配置已加载', 'success');
                }
            } catch (error) {
                this.showNotification('加载配置失败: ' + error.message, 'error');
            }
        },
        
        async saveConfig() {
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        config: this.config,
                        env: this.env
                    })
                });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('配置已保存', 'success');
                } else {
                    this.showNotification('保存失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('保存失败: ' + error.message, 'error');
            }
        },
        
        // 统计数据
        async loadStats() {
            try {
                const res = await fetch('/api/stats/today');
                const data = await res.json();
                if (data.success) {
                    this.stats = data.data;
                }
            } catch (error) {
                console.error('加载统计失败:', error);
            }
        },
        
        // 群友列表
        async loadMembers() {
            try {
                const res = await fetch('/api/members');
                const data = await res.json();
                if (data.success) {
                    this.members = data.members;
                }
            } catch (error) {
                console.error('加载群友列表失败:', error);
            }
        },
        
        // 日志管理
        clearLogs() {
            this.logs = [];
            this.showNotification('日志已清空', 'success');
        },
        
        toggleAutoScroll() {
            this.autoScroll = !this.autoScroll;
        },
        
        scrollToBottom() {
            if (this.autoScroll && this.$refs.logContainer) {
                this.$nextTick(() => {
                    const container = this.$refs.logContainer;
                    container.scrollTop = container.scrollHeight;
                });
            }
        },
        
        // WebSocket
        connectWebSocket() {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('WebSocket已连接');
            });
            
            this.socket.on('connected', (data) => {
                console.log('服务器消息:', data.message);
            });
            
            this.socket.on('initial_logs', (data) => {
                this.logs = data.logs;
                this.recentLogs = data.logs;
                this.scrollToBottom();
            });
            
            this.socket.on('log', (data) => {
                this.logs.push(data);
                this.recentLogs.push(data);
                
                // 限制日志数量
                if (this.logs.length > 1000) {
                    this.logs.shift();
                }
                if (this.recentLogs.length > 100) {
                    this.recentLogs.shift();
                }
                
                this.scrollToBottom();
            });
            
            this.socket.on('disconnect', () => {
                console.log('WebSocket已断开');
            });
        },
        
        // 通知
        showNotification(message, type = 'info') {
            // 简单的通知实现
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
                color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 9999;
                animation: slideIn 0.3s;
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }
    },
    
    mounted() {
        // 初始化
        this.loadConfig();
        this.updateStatus();
        this.loadStats();
        this.loadMembers();
        this.connectWebSocket();
        
        // 定时更新状态
        this.statusInterval = setInterval(() => {
            this.updateStatus();
            if (this.currentPage === 'dashboard') {
                this.loadStats();
            }
        }, 2000);
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    },
    
    beforeUnmount() {
        // 清理
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}).mount('#app');
