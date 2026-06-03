# AI Conversations Manager — 项目规范

## 1. 项目概述

**一句话描述：** 统一提取、管理、搜索多个 AI 编程工具的本地对话历史，并通过 MCP 协议让 AI 工具直接查询。

**解决的问题：**
- 用户在多个 AI 工具（Claude Code、Codex、Cursor、Antigravity）之间切换，对话分散在各处
- Token 用完了想换工具继续，没法快速找到之前聊了什么
- 没有统一的地方浏览、搜索所有对话历史

**目标用户：** 同时使用多个 AI 编程工具的开发者

---

## 2. 支持的工具

**核心原则：路径不写死，按操作系统自动检测。**

### 2.1 路径自动检测

```python
import platform, os, pathlib

def get_app_support_dir():
    """根据操作系统返回 Application Support 根目录"""
    system = platform.system()
    if system == "Darwin":
        return pathlib.Path.home() / "Library" / "Application Support"
    elif system == "Windows":
        return pathlib.Path(os.environ.get("APPDATA", ""))
    elif system == "Linux":
        return pathlib.Path.home() / ".config"
```

### 2.2 各工具存储路径（跨平台）

| 工具 | macOS | Windows | Linux | 格式 |
|---|---|---|---|---|
| Claude Code | `~/.claude/projects/` | `%USERPROFILE%\.claude\projects\` | `~/.claude/projects/` | JSONL |
| Codex CLI + App | `~/.codex/sessions/` | `%USERPROFILE%\.codex\sessions\` | `~/.codex/sessions/` | JSONL |
| Cursor | `~/Library/Application Support/Cursor/` | `%APPDATA%\Cursor\` | `~/.config/Cursor/` | SQLite |
| Antigravity | `~/Library/Application Support/Antigravity IDE/` | `%APPDATA%\Antigravity IDE\` | `~/.config/Antigravity IDE/` | SQLite |

**注意：** Claude Code 和 Codex 的路径基于 `HOME`（跨平台一致），Cursor/Antigravity 基于 OS 特定目录。

### 2.3 优先级
- Claude Code、Codex、Cursor：**P0**（首先实现）
- Antigravity：**P1**（用户确认是否使用后再做）

---

## 3. 产品功能

### 3.1 数据同步（Sync）

**命令：** `ai-conversations sync [选项]`

| 选项 | 说明 |
|---|---|
| `--tool <name>` | 指定同步哪个工具（`claude-code` / `codex` / `cursor` / `all`） |
| `--since <duration>` | 只同步最近 N 天的数据（如 `7d`、`30d`、`2026-01-01`） |
| `--dry-run` | 只预览，不写入 |
| `--project <path>` | 只同步指定项目路径 |

**行为：**
1. 读取指定工具的原始对话数据
2. 转换为统一格式
3. 写入 SQLite 数据库（`~/.ai-conversations/data.db`）
4. 增量同步：用 session_id 去重，只写新数据

### 3.2 搜索（Search）

**命令：** `ai-conversations search <关键词> [选项]`

| 选项 | 说明 |
|---|---|
| `--tool <name>` | 按工具过滤 |
| `--project <name>` | 按项目过滤 |
| `--date <range>` | 按日期过滤（如 `2026-06`、`2026-01-01:2026-06-01`） |
| `--role <role>` | 按角色过滤（`user` / `assistant`） |
| `--limit <n>` | 返回条数（默认 20） |

**输出示例：**
```
[2026-06-03] claude-code | /Users/liuchuang/Projects
  匹配："牙齿冷热酸甜及咬硬物时疼痛"
  → 用户询问牙齿疼痛的表现情况...

[2026-06-02] codex | /Users/liuchuang/Downloads/github/medical-data-governance
  匹配："牙齿"
  → 助手建议查看口腔科检查...
```

### 3.3 MCP Server

**工具注册：**

| MCP 工具名 | 参数 | 说明 |
|---|---|---|
| `search_conversations` | `query`, `tool?`, `project?`, `date_range?`, `limit?` | 全文搜索对话 |
| `list_sessions` | `tool?`, `project?`, `date_range?`, `limit?` | 列出会话 |
| `get_session` | `session_id` | 获取某个会话的完整内容 |
| `list_projects` | `tool?` | 列出所有项目 |
| `export_session` | `session_id`, `format?` | 导出为 Markdown |

**MCP 配置方式（用户在 Cursor/Claude Code 设置里加）：**
```json
{
  "mcpServers": {
    "ai-conversations": {
      "command": "ai-conversations",
      "args": ["serve"]
    }
  }
}
```

### 3.4 Web UI（P2，后期）

本地网页界面，功能：
- 按工具/项目/日期筛选对话
- 全文搜索
- 查看完整对话内容
- 复制为 Markdown
- 统计面板（每个工具有多少对话、活跃天数等）

---

## 4. 数据模型

### 4.1 统一消息结构

```python
@dataclass
class Conversation:
    id: str              # 内部唯一 ID（hash of tool + session_id）
    tool: str            # "claude-code" / "codex" / "cursor"
    project: str         # 项目路径，如 "/Users/liuchuang/Projects"
    session_id: str      # 原生 session ID
    title: str           # 会话标题
    started_at: str      # ISO 时间戳
    ended_at: str        # ISO 时间戳
    message_count: int   # 消息数

@dataclass
class Message:
    conversation_id: str # 关联的会话 ID
    role: str            # "user" / "assistant"
    content: str         # 纯文本内容
    timestamp: str       # ISO 时间戳
    sequence: int        # 在会话中的顺序（从 0 开始）
```

### 4.2 SQLite 表结构

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    tool TEXT NOT NULL,
    project TEXT NOT NULL,
    session_id TEXT NOT NULL,
    title TEXT,
    started_at TEXT,
    ended_at TEXT,
    message_count INTEGER,
    synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool, session_id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT,
    sequence INTEGER
);

-- FTS5 全文搜索索引
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);

-- 索引
CREATE INDEX idx_conversations_tool ON conversations(tool);
CREATE INDEX idx_conversations_project ON conversations(project);
CREATE INDEX idx_conversations_started ON conversations(started_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);

-- FTS5 同步触发器（messages 表增删改时自动同步到 FTS 索引）
CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;

CREATE TRIGGER messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

---

## 5. 各工具提取逻辑

### 5.1 Claude Code Extractor

**数据源：** `~/.claude/projects/` 下每个子目录的 `.jsonl` 文件

**目录名 → 项目路径解码规则：** 目录名用 `-` 分隔路径段，原始路径中的 `-` 被编码为 `--`（双短杠）。解码算法：

```python
def decode_project_dir(dirname: str) -> str:
    """将 Claude Code 目录名还原为项目路径"""
    # 先把 -- 替换为占位符，再按 - 分割，最后还原
    return dirname.replace("--", "\x00").replace("-", "/").replace("\x00", "-")

# 示例：
# -Users-liuchuang-Projects              → /Users/liuchuang/Projects
# -Users-liuchuang--claude               → /Users/liuchuang/-claude
# -Users-liuchuang-Downloads-github-medical-data-governance → /Users/liuchuang/Downloads/github/medical-data-governance
```

**读取逻辑：**
1. 遍历 `~/.claude/projects/*/` 下所有 `.jsonl` 文件
2. 逐行解析 JSON，只取 `type = "user"` 和 `type = "assistant"` 的行
3. `type = "ai-title"` 的行作为会话标题
4. `sessionId` 字段为会话 ID
5. `timestamp` 字段为时间
6. `message.role` 为角色，`message.content` 为内容（可能是字符串或数组，数组时取 `text` 拼接）

**忽略的类型：** `mode`、`permission-mode`、`file-history-snapshot`、`attachment`、`system`

### 5.2 Codex Extractor

**数据源：**
- `~/.codex/session_index.jsonl`（会话索引，含 `thread_name` 标题）
- `~/.codex/sessions/<年>/<月>/<日>/rollout-*.jsonl`（完整对话）
- `~/.codex/archived_sessions/`（归档对话）

**读取逻辑：**
1. 先读 `session_index.jsonl`，建立 `{session_id → thread_name}` 映射
2. 用文件名中的 UUID 匹配 session_index 的 `id`
3. 解析 rollout JSONL：
   - `type = "session_meta"` → 提取 `payload.cwd` 作为项目路径
   - `type = "event_msg"` + `payload.role = "user"` → 用户消息
   - `type = "response_item"` + `payload.role = "assistant"` → 助手消息
4. 文件名中的时间戳作为 `started_at`

**注意：** `payload.content` 可能是多种格式：
- 纯字符串 → 直接使用
- 对象数组 → 取 `type="output_text"` 的 `text` 字段拼接
- 嵌套结构 → 递归提取所有 `text` 字段并拼接
- 实现时需处理以上所有情况

### 5.3 Cursor Extractor

**数据源：** `<app_support>/Cursor/User/globalStorage/state.vscdb`
> `<app_support>` 由路径检测模块自动确定（macOS: `~/Library/Application Support`，Windows: `%APPDATA%`，Linux: `~/.config`）

**读取逻辑：**
1. 连接 SQLite，从 `cursorDiskKV` 表读取
2. `key LIKE 'composerData:%'` → 会话元数据（`composerId` = session_id，`text` = 用户输入，`conversation` 数组 = 消息列表）
3. `key LIKE 'bubbleId:<composerId>:%'` → 单条消息（type 映射待验证，实现时先 `SELECT DISTINCT type` 确认）
4. 项目路径：遍历 `<app_support>/Cursor/User/workspaceStorage/*/workspace.json`，匹配 `folder` 字段与 composerData 中的上下文关联

**复杂度注意：**
- `cursorDiskKV` 有 **129593** 行，需要高效查询
- `bubbleId` 数量巨大（**55960** 条），需要批量读取
- `conversation` 数组可能很深嵌套，需要递归提取文本
- 空内容的 bubble 需要跳过

### 5.4 Antigravity Extractor（P1）

**数据源：** `<app_support>/Antigravity IDE/User/globalStorage/state.vscdb`
> `<app_support>` 由路径检测模块自动确定（macOS: `~/Library/Application Support`，Windows: `%APPDATA%`，Linux: `~/.config`）

**状态：** 当前 `chat.ChatSessionStore.index` 为空，待确认用户是否使用过此工具。

**如果用过：** 结构类似 Cursor（VS Code fork），用类似逻辑提取。

---

## 6. 项目结构

```
ai-conversations/
├── SPEC.md                         # 本文件
├── README.md                       # 用户文档
├── pyproject.toml                  # 项目配置 + 依赖
├── src/
│   └── ai_conversations/
│       ├── __init__.py
│       ├── cli.py                  # CLI 入口（sync / search / serve）
│       ├── db.py                   # SQLite 数据库操作
│       ├── models.py               # 数据模型（Conversation, Message）
│       ├── paths.py                # 跨平台路径检测（各工具数据目录）
│       ├── mcp_server.py           # MCP 服务端
│       └── extractors/
│           ├── __init__.py
│           ├── base.py             # BaseExtractor 抽象类
│           ├── claude_code.py
│           ├── codex.py
│           ├── cursor.py
│           └── antigravity.py
├── tests/
│   ├── test_claude_code.py
│   ├── test_codex.py
│   ├── test_cursor.py
│   └── fixtures/                   # 测试用的 sample 数据
└── web/                            # P2: Web UI
```

---

## 7. 技术栈

| 组件 | 技术 | 理由 |
|---|---|---|
| 语言 | **Python 3.9+** | 标准库自带 json、sqlite3、pathlib，CLI 核心功能零外部依赖 |
| CLI | **Click** 或 **argparse** | argparse 零依赖，Click 更友好 |
| MCP SDK | **mcp**（官方 Python SDK） | Anthropic 官方维护 |
| 数据库 | **SQLite**（内置） | FTS5 全文搜索，无需安装 |
| 测试 | **pytest** | 标准选择 |
| 打包 | **pip + pyproject.toml** | `pip install ai-conversations` |
| Web UI（P2）| **FastAPI + Vue/React** | 后期再定 |

**外部依赖最小化原则：**
- 核心功能只依赖 `mcp` SDK（MCP 服务必须的）
- 其余全部用标准库
- 可选依赖用 `extras_require`（如 Web UI 的 FastAPI）

---

## 8. 安装与使用

### 安装

```bash
pip install ai-conversations
```

### 命令行使用

```bash
# 全量同步
ai-conversations sync

# 只同步 Claude Code 和 Codex，最近 7 天
ai-conversations sync --tool claude-code,codex --since 7d

# 搜索
ai-conversations search "牙齿" --tool codex

# 列出会话
ai-conversations sessions --tool cursor --project medical

# 导出某个会话为 Markdown
ai-conversations export <session-id> --format markdown

# 启动 MCP server
ai-conversations serve
```

### MCP 配置（Cursor / Claude Code）

在工具的 MCP 设置中添加：
```json
{
  "mcpServers": {
    "ai-conversations": {
      "command": "ai-conversations",
      "args": ["serve"]
    }
  }
}
```

使用时在对话中直接问：
- "搜索我之前在 Codex 讨论过的医疗数据治理相关对话"
- "我在 Claude Code 里讨论过的牙齿问题是什么结论？"
- "列出我所有工具中关于 xxx 项目的对话"

---

## 9. 待确认问题

以下问题需要用户确认后才能开始实现：

### Q1: 数据存储位置
- **选项 A：** `~/.ai-conversations/`（默认，用户主目录下）
- **选项 B：** 项目目录下（如 `~/Projects/ai-conversations/data/`）
- **选项 C：** 让用户通过配置文件指定

### Q2: Antigravity
- 用户确认使用过 Antigravity IDE。
- **现状：** Antigravity 不像 Cursor 那样把聊天记录存在本地可读格式里（ChatSessionStore.index 为空，trajectorySummaries 是 protobuf 编码）。
- Extractor 已写好，能读就读，没有数据就返回空。
- 后续如果 Antigravity 改变存储方式，可以扩展 extractor。

### Q3: Cursor 数据的项目路径关联
- Cursor 的 composerData 不直接包含项目路径，需要通过 workspaceStorage 里的 workspace.json 间接关联。
- 如果关联不上，显示为 "unknown-project" 可以接受吗？

### Q4: 消息内容处理
- **只保留纯文本**（用户消息 + 助手回复的文字部分）
- 工具调用（tool_use）、文件变更、代码 diff、截图全部跳过
- 这样可以吗？

### Q5: Codex CLI vs Codex.app
- 两者共享 `~/.codex/` 存储，统一处理。
- 如果用户同时用两者，同一会话不会重复（因为 session_id 相同）。
- 确认这样处理？

### Q6: 排除规则
- 是否需要排除某些对话？比如：
  - 空对话（只有系统消息，没有用户消息）
  - 非常短的对话（如只有 1-2 条消息的闲聊）
  - 特定项目/路径

### Q7: Web UI 优先级
- P2 的 Web UI 是否需要？
- 如果需要，是同步开发还是先出 CLI + MCP 再加？

~~### Q8: 平台支持~~
~~已解决：首版即支持 macOS / Windows / Linux，路径通过 `paths.py` 自动检测。~~

---

## 10. 开发计划

| 阶段 | 内容 | 预计工作量 |
|---|---|---|
| Phase 1 | Claude Code extractor + CLI sync/search | 半天 |
| Phase 2 | Codex extractor | 半天 |
| Phase 3 | Cursor extractor（最复杂） | 1 天 |
| Phase 4 | MCP Server | 半天 |
| Phase 5 | 测试 + README + 发布 | 半天 |
| Phase 6 | Antigravity（如有需要） | 半天 |
| Phase 7 | Web UI（如需要） | 2-3 天 |

**总预计：3-5 天（不含 Web UI）**
