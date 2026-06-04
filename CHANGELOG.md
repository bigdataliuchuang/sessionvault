# Changelog

All notable changes to SessionVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-04

### Added

#### Core

- **Unified conversation database** -- SQLite storage with incremental sync and deduplication by `(tool, session_id)`. Data stored at `~/.sessionvault/data.db`.
- **FTS5 full-text search** -- SQLite FTS5 virtual table with automatic sync triggers for insert, update, and delete. Supports filtering by tool, project, date range, and role.
- **Incremental sync with mtime tracking** -- Re-syncs conversations only when the source file has been modified, avoiding redundant database writes.

#### Extractors (4 tools)

- **Claude Code extractor** -- Reads JSONL session files from `~/.claude/projects/`. Decodes project directory names from dash-encoded paths (e.g., `-Users-liuchuang--claude` to `/Users/liuchuang/-claude`). Extracts user/assistant messages, session titles from `type: "ai-title"` entries, and timestamps.
- **Codex extractor** -- Reads rollout JSONL files from `~/.codex/sessions/` and `~/.codex/archived_sessions/`. Parses `session_index.jsonl` for thread titles. Handles multiple `payload.content` formats: plain strings, object arrays with `output_text` type, and deeply nested structures.
- **Cursor extractor** -- Reads from Cursor's SQLite `state.vscdb` database (`cursorDiskKV` table). Parses `composerData:` keys for conversation metadata and `bubbleId:` keys for individual messages. Associates projects via `workspaceStorage/*/workspace.json`.
- **Antigravity extractor** -- Reads from Antigravity IDE's `state.vscdb` database. Designed to gracefully return empty results when no data is present.

#### Cross-platform support

- **Automatic path detection** via `paths.py` -- resolves tool-specific data directories for macOS (`~/Library/Application Support`), Windows (`%APPDATA%`), and Linux (`~/.config`). Claude Code and Codex paths based on `$HOME` are platform-consistent.

#### MCP Server

- **MCP server** (`sessionvault serve`) -- stdio transport using the official `mcp` Python SDK (`FastMCP`). Registers 5 tools:
  - `search_conversations` -- full-text search with optional filters (tool, project, date range, role, limit)
  - `list_sessions` -- list sessions with filters
  - `get_session` -- retrieve full conversation content by session ID
  - `list_projects` -- list all projects with conversation counts
- Compatible with Cursor and Claude Code MCP configuration.

#### Web UI

- **Web UI** (`sessionvault web`) -- FastAPI-based local web interface with:
  - Full-text search with tool-tab filtering (Claude Code / Codex / Cursor)
  - Sortable session lists (newest-first or oldest-first toggle)
  - Session detail modal with full message history
  - Markdown export for individual sessions
  - Statistics dashboard (total conversations, messages, per-tool counts)
  - Dark theme with responsive layout

#### TUI

- **Terminal UI** (`sessionvault tui`) -- Textual-based interactive interface with:
  - Real-time search-as-you-type filtering
  - Session data table with row selection for detail view
  - Keyboard bindings: `/` search, `p` projects, `e` export, `q` quit
  - Markdown export of current results to `~/.sessionvault/export.md`

#### CLI

- **`sessionvault sync`** -- Sync conversations from AI tools with options:
  - `--tool <name>` -- comma-separated tool filter (claude-code, codex, cursor, antigravity)
  - `--since <duration>` -- sync only recent sessions (e.g., `7d`, `2026-01-01`)
  - `--project <path>` -- filter by project
  - `--dry-run` -- preview mode without writing
- **`sessionvault search <query>`** -- Full-text search with `--tool`, `--project`, `--date`, `--role`, `--limit` filters.
- **`sessionvault sessions`** -- List conversation sessions with optional filters.
- **`sessionvault projects`** -- List all projects with per-tool session counts.
- **`sessionvault stats`** -- Show total conversations, messages, and per-tool breakdown.
- **`sessionvault export <session-id>`** -- Export a session as Markdown with YAML frontmatter.

#### UX

- **Rich progress bar** -- During `sync`, displays a spinner, progress bar, and per-tool summary table (status, new count, skipped count) using `rich`. Falls back to plain logging when `rich` is not installed.

#### Packaging

- **Optional dependency groups** via `pyproject.toml`:
  - `sessionvault[mcp]` -- MCP server support (`mcp>=1.0.0`)
  - `sessionvault[tui]` -- Terminal UI (`textual>=0.40.0`)
  - `sessionvault[web]` -- Web UI (`fastapi>=0.100.0`, `uvicorn>=0.23.0`)
  - `sessionvault[all]` -- All optional features
  - `sessionvault[dev]` -- Development tools (`pytest>=7.0`, `rich>=13.0.0`)
- **Zero core dependencies** -- core sync/search uses only Python standard library (`sqlite3`, `json`, `pathlib`, `argparse`).

### Notes

- The `file_mtime` column on the `conversations` table tracks source file modification times for incremental sync decisions.
- FTS5 sync triggers automatically keep the search index consistent with message inserts, updates, and deletes.
- The Antigravity extractor is functional but currently returns empty results as the IDE's `ChatSessionStore.index` is empty in observed installations.
