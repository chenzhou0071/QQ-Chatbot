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
                    target_group: '',
                    admin_name: '',
                    admin_relationship: '',
                    admin_description: ''
                },
                personality: {
                    name: '',
                    nickname: '',
                    background: '',
                    appearance: {
                        height: '',
                        hair: '',
                        features: '',
                        aura: ''
                    },
                    character: {
                        core: '',
                        traits: []
                    },
                    speaking_style: {
                        tone: '',
                        manner: '',
                        response: '',
                        emoji_usage: ''
                    }
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
            personalityTraits: '',  // 用于编辑的文本形式
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
            statusInterval: null,
            editingMember: null,  // 当前正在编辑的群友QQ号
            editingMemberData: {}  // 编辑中的群友数据
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
                    // 深度合并配置，确保所有字段都存在
                    this.config = this.mergeConfig(this.config, data.config);
                    this.env = data.env;
                    // 将traits数组转换为文本
                    if (this.config.personality.character && this.config.personality.character.traits) {
                        this.personalityTraits = this.config.personality.character.traits.join('\n');
                    }
                    this.showNotification('配置已加载', 'success');
                }
            } catch (error) {
                this.showNotification('加载配置失败: ' + error.message, 'error');
            }
        },
        
        // 深度合并配置对象
        mergeConfig(target, source) {
            const result = { ...target };
            for (const key in source) {
                if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                    result[key] = this.mergeConfig(result[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
            return result;
        },
        
        // 更新性格特质
        updateTraits() {
            // 将文本转换为数组
            this.config.personality.character.traits = this.personalityTraits
                .split('\n')
                .map(t => t.trim())
                .filter(t => t.length > 0);
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
        
        // 开始编辑群友
        startEditMember(member) {
            this.editingMember = member.qq;
            this.editingMemberData = {
                qq: member.qq,
                qq_name: member.qq_name || '',
                group_card: member.group_card || '',
                nickname: member.nickname || '',
                birthday: member.birthday || '',
                notes: member.notes || '',
                avatar_url: member.avatar_url || '',
                is_active: member.is_active !== undefined ? member.is_active : 1
            };
        },
        
        // 保存群友信息
        async saveMember() {
            try {
                const res = await fetch(`/api/members/${this.editingMemberData.qq}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.editingMemberData)
                });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('保存成功', 'success');
                    this.editingMember = null;
                    this.editingMemberData = {};
                    await this.loadMembers();  // 重新加载列表
                } else {
                    this.showNotification('保存失败: ' + data.error, 'error');
                }
            } catch (error) {
                this.showNotification('保存失败: ' + error.message, 'error');
            }
        },
        
        // 取消编辑
        cancelEdit() {
            this.editingMember = null;
            this.editingMemberData = {};
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
        },
        
        // 格式化日期
        formatDate(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr);
            const now = new Date();
            const diff = now - date;
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            
            if (days === 0) {
                const hours = Math.floor(diff / (1000 * 60 * 60));
                if (hours === 0) {
                    const minutes = Math.floor(diff / (1000 * 60));
                    return minutes === 0 ? '刚刚' : `${minutes}分钟前`;
                }
                return `${hours}小时前`;
            } else if (days === 1) {
                return '昨天';
            } else if (days < 7) {
                return `${days}天前`;
            } else {
                return date.toLocaleDateString('zh-CN');
            }
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
