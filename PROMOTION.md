# SessionVault 推广文案

## Reddit (r/ChatGPTCoding, r/ClaudeAI, r/cursor)

### 标题
I built SessionVault - unify your AI coding conversations across Claude Code, Codex, and Cursor

### 正文
Hey everyone! 👋

I've been juggling between Claude Code, Codex, and Cursor for a while, and kept losing track of conversations. "What did I discuss about that feature last week?" "Which tool did I use for that bug fix?"

So I built **SessionVault** - a tool that unifies all your AI coding conversations into one place.

**What it does:**
- 🔄 Syncs conversations from Claude Code, Codex CLI/App, Cursor, and Antigravity
- 🔍 Full-text search across all tools (FTS5 engine)
- 🤖 MCP integration - search your history directly from Cursor/Claude Code
- 🌐 Web UI with dark theme, charts, and export
- 💻 Terminal UI for quick access
- 📦 Cross-platform (macOS/Windows/Linux)

**Quick start:**
```bash
pip install sessionvault
sessionvault sync
sessionvault search "that feature I discussed"
sessionvault web  # opens web UI
```

**GitHub:** https://github.com/bigdataliuchuang/sessionvault

It's Apache 2.0 licensed, so feel free to contribute! Would love feedback on what tools to add next.

---

## Twitter/X

### 帖子 1 (功能介绍)
```
🔐 Introducing SessionVault

Tired of losing track of conversations across Claude Code, Codex, and Cursor?

I built a tool that:
✅ Syncs all your AI coding conversations
✅ Full-text search across tools
✅ MCP integration (search from Cursor/Claude Code)
✅ Web UI + Terminal UI
✅ Cross-platform

pip install sessionvault

#AI #Coding #OpenSource
```

### 帖子 2 (技术亮点)
```
Built SessionVault in Python:

• 4 tool extractors (Claude Code, Codex, Cursor, Antigravity)
• FTS5 full-text search
• MCP server for AI tool integration
• Rich progress bars
• Plugin system
• REST API

All with 26 tests passing ✅

github.com/bigdataliuchuang/sessionvault
```

---

## Hacker News (Show HN)

### 标题
Show HN: SessionVault – Unified conversation manager for AI coding tools

### 正文
I built SessionVault to solve a problem I face daily: managing conversations across multiple AI coding tools.

**The problem:**
I use Claude Code, Codex, and Cursor daily. When I need to revisit a previous discussion, I have to remember which tool I used and dig through its history. There's no unified search.

**The solution:**
SessionVault extracts conversations from all tools into a unified SQLite database with FTS5 full-text search. It also provides an MCP server so you can search your history directly from Cursor or Claude Code.

**Features:**
- Sync from Claude Code, Codex CLI/App, Cursor
- Full-text search with FTS5
- MCP integration
- Web UI and Terminal UI
- Cross-platform
- Plugin system

**Tech stack:** Python, SQLite, FastAPI, Textual, MCP SDK

**GitHub:** https://github.com/bigdataliuchuang/sessionvault

---

## V2EX

### 标题
[开源] SessionVault - 统一管理 Claude Code / Codex / Cursor 的对话历史

### 正文
大家好，分享一个我最近做的开源项目。

**问题背景：**
同时用 Claude Code、Codex、Cursor 三个 AI 编程工具，对话分散在各处，想找之前讨论过的内容很麻烦。

**解决方案：**
SessionVault 把三个工具的对话统一提取到 SQLite 数据库，支持全文搜索。

**主要功能：**
- 同步 Claude Code、Codex、Cursor 的对话
- FTS5 全文搜索
- MCP 集成（在 Cursor/Claude Code 里直接搜索历史）
- Web UI（暗色主题、图表、导出）
- 终端 UI
- 跨平台支持

**使用方法：**
```bash
pip install sessionvault
sessionvault sync
sessionvault search "关键词"
sessionvault web
```

**GitHub：** https://github.com/bigdataliuchuang/sessionvault

Apache 2.0 协议，欢迎贡献！

---

## README Badge（添加到 README）

```markdown
[![PyPI version](https://img.shields.io/pypi/v/sessionvault.svg)](https://pypi.org/project/sessionvault/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
```
