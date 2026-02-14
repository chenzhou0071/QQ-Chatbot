# 脚本工具

本目录包含项目的辅助脚本工具。

## 📁 脚本列表

### test_features.bat
**功能**：测试对话智能功能是否正常

**使用**：
```bash
cd scripts
test_features.bat
```

**测试内容**：
- 意图分析器
- 对话状态机
- 上下文增强器
- 主动对话引擎

---

### check_config.bat
**功能**：检查配置文件，显示当前启用的功能

**使用**：
```bash
cd scripts
check_config.bat
```

**显示内容**：
- 基本配置（QQ号、群号）
- 对话智能配置
- AI配置
- 记忆配置

---

### toggle_features.bat
**功能**：交互式功能开关菜单

**使用**：
```bash
cd scripts
toggle_features.bat
```

**功能选项**：
1. 启用所有对话智能功能
2. 禁用所有对话智能功能
3. 仅启用意图分析
4. 仅启用对话状态机
5. 仅启用主动对话
6. 查看当前配置

---

### clean_data.bat
**功能**：清理数据文件（保留配置）

**使用**：
```bash
cd scripts
clean_data.bat
```

**清理内容**：
- 聊天记录数据库 (data\bot.db)
- 向量数据库 (data\chroma)
- 日志文件 (data\logs)

**注意**：配置文件和代码不会被删除

---

## 💡 使用建议

### 首次使用
1. 运行 `test_features.bat` 确认功能正常
2. 运行 `check_config.bat` 查看配置

### 调试问题
1. 运行 `check_config.bat` 检查配置
2. 查看日志文件 `data\logs\bot-*.log`

### 功能调整
1. 运行 `toggle_features.bat` 快速开关功能
2. 或手动编辑 `config\config.yaml`

### 重新开始
1. 运行 `clean_data.bat` 清理数据
2. 重新启动机器人

---

## 🔗 相关文档

- [主文档](../README.md)
- [对话智能文档](../docs/DIALOGUE_INTELLIGENCE.md)
- [配置示例](../config/config.yaml.example)
