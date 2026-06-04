# SessionVault

统一提取、管理、搜索多个 AI 编程工具的本地对话历史。

**支持工具：** Claude Code · Codex CLI / App · Cursor · Antigravity

---

## 功能

- **一键同步** — 从各工具本地存储提取对话，统一存入 SQLite
- **全文搜索** — FTS5 引擎，秒级搜索所有历史对话
- **MCP 集成** — 在 Cursor / Claude Code 里直接搜索历史对话
- **跨平台** — macOS / Windows / Linux 自动检测路径

## 安装

```bash
pip install sessionvault
```

如果需要 MCP 功能：

```bash
pip install sessionvault[mcp]
```

如果需要完整功能（MCP + TUI + Web UI）：

```bash
pip install sessionvault[all]
```

## 快速开始

### 1. 同步数据

```bash
# 同步所有工具
sessionvault sync

# 只同步某个工具
sessionvault sync --tool claude-code
sessionvault sync --tool codex
sessionvault sync --tool cursor

# 只同步最近 7 天
sessionvault sync --since 7d

# 预览不写入
sessionvault sync --dry-run
```

### 2. 搜索对话

```bash
# 搜索关键词
sessionvault search "牙齿"

# 按工具过滤
sessionvault search "医疗数据" --tool codex

# 按项目过滤
sessionvault search "导诊" --project medical
```

### 3. 查看统计

```bash
sessionvault stats
sessionvault projects
sessionvault sessions
```

### 4. 导出会话

```bash
sessionvault export <session-id>
```

## MCP 集成

在 Cursor 或 Claude Code 里直接搜索你的历史对话。

### Cursor 配置

编辑 `~/.cursor/mcp.json`，添加：

```json
{
  "mcpServers": {
    "sessionvault": {
      "command": "python3",
      "args": ["-m", "ai_conversations.mcp_server"]
    }
  }
}
```

> 如果 Cursor 找不到 `python3`，改成绝对路径，如 `/usr/bin/python3` 或 `/opt/anaconda3/bin/python3`

### Claude Code 配置

在 `~/.claude/.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "sessionvault": {
      "command": "python3",
      "args": ["-m", "ai_conversations.mcp_server"]
    }
  }
}
```

### 使用方式

配置完成后，在 Cursor / Claude Code 里直接问：

- "搜索我之前讨论过的医疗数据治理相关对话"
- "列出我所有工具的项目"
- "我在 Codex 里讨论过什么？"

AI 会自动调用 `sessionvault` 工具搜索并返回结果。

## 数据来源

| 工具 | 数据位置 | 格式 |
|---|---|---|
| Claude Code | `~/.claude/projects/` | JSONL |
| Codex CLI + App | `~/.codex/sessions/` | JSONL |
| Cursor | `~/Library/Application Support/Cursor/` | SQLite |
| Antigravity | `~/Library/Application Support/Antigravity IDE/` | SQLite |

路径会根据操作系统自动适配（macOS / Windows / Linux）。

## 项目结构

```
sessionvault/
├── pyproject.toml
├── src/ai_conversations/
│   ├── cli.py              # CLI 入口
│   ├── db.py               # SQLite 数据库
│   ├── models.py           # 数据模型
│   ├── paths.py            # 跨平台路径检测
│   ├── mcp_server.py       # MCP 服务端
│   └── extractors/
│       ├── base.py         # 基类
│       ├── claude_code.py  # Claude Code
│       ├── codex.py        # Codex
│       ├── cursor.py       # Cursor
│       └── antigravity.py  # Antigravity
└── tests/
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v
```

## License

MIT
