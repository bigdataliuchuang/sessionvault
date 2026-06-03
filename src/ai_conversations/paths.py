"""Cross-platform path detection for AI tool data directories.

Pure path computation — no filesystem I/O.
"""

import os
import platform
from pathlib import Path


def get_app_support_dir() -> Path:
    """Return the OS-specific Application Support directory.

    macOS:   ~/Library/Application Support
    Windows: %APPDATA%
    Linux:   ~/.config
    """
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support"
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", ""))
    else:
        return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def get_claude_code_dir() -> Path:
    """Claude Code stores data under ~/.claude/projects/ on all platforms."""
    return Path.home() / ".claude" / "projects"


def get_codex_sessions_dir() -> Path:
    """Codex session files."""
    return Path.home() / ".codex" / "sessions"


def get_codex_session_index() -> Path:
    """Codex session index file."""
    return Path.home() / ".codex" / "session_index.jsonl"


def get_codex_archived_sessions_dir() -> Path:
    """Codex archived sessions."""
    return Path.home() / ".codex" / "archived_sessions"


def get_cursor_dir() -> Path:
    """Cursor data directory (OS-specific)."""
    return get_app_support_dir() / "Cursor"


def get_cursor_state_db() -> Path:
    """Cursor's global state SQLite database."""
    return get_cursor_dir() / "User" / "globalStorage" / "state.vscdb"


def get_cursor_workspace_storage_dir() -> Path:
    """Cursor workspace storage directory."""
    return get_cursor_dir() / "User" / "workspaceStorage"


def get_antigravity_dir() -> Path:
    """Antigravity IDE data directory (OS-specific)."""
    return get_app_support_dir() / "Antigravity IDE"


def get_antigravity_state_db() -> Path:
    """Antigravity's global state SQLite database."""
    return get_antigravity_dir() / "User" / "globalStorage" / "state.vscdb"


def get_data_dir() -> Path:
    """Our own data directory for storing the unified database."""
    return Path.home() / ".ai-conversations"


def get_db_path() -> Path:
    """Path to our SQLite database."""
    return get_data_dir() / "data.db"
