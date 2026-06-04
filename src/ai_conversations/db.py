"""SQLite database operations with FTS5 full-text search."""

import sqlite3
from pathlib import Path
from typing import List, Optional

from .models import Conversation, Message

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    tool TEXT NOT NULL,
    project TEXT NOT NULL,
    session_id TEXT NOT NULL,
    title TEXT,
    started_at TEXT,
    ended_at TEXT,
    message_count INTEGER,
    file_mtime REAL,
    synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool, session_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT,
    sequence INTEGER
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);

CREATE INDEX IF NOT EXISTS idx_conversations_tool ON conversations(tool);
CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project);
CREATE INDEX IF NOT EXISTS idx_conversations_started ON conversations(started_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
"""


class Database:
    """SQLite database for storing and searching conversations."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            from .config import get_config
            db_path = get_config().db_path
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def conversation_exists(self, tool: str, session_id: str) -> bool:
        """Check if a conversation already exists (for incremental sync)."""
        row = self.conn.execute(
            "SELECT 1 FROM conversations WHERE tool = ? AND session_id = ?",
            (tool, session_id)
        ).fetchone()
        return row is not None

    def needs_sync(self, tool: str, session_id: str, file_mtime: float) -> bool:
        """Check if a conversation needs re-sync based on file modification time."""
        row = self.conn.execute(
            "SELECT file_mtime FROM conversations WHERE tool = ? AND session_id = ?",
            (tool, session_id)
        ).fetchone()
        if not row:
            return True  # New conversation
        if row[0] is None:
            return True  # No mtime recorded
        # Re-sync if file is newer (with 0.001 tolerance)
        return file_mtime > row[0] + 0.001

    def save_conversation(self, conv: Conversation):
        """Save a conversation and all its messages."""
        self.conn.execute(
            """INSERT OR REPLACE INTO conversations
               (id, tool, project, session_id, title, started_at, ended_at, message_count, file_mtime)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (conv.id, conv.tool, conv.project, conv.session_id,
             conv.title, conv.started_at, conv.ended_at, conv.message_count,
             getattr(conv, 'file_mtime', None))
        )
        self.conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?", (conv.id,)
        )
        for msg in conv.messages:
            self.conn.execute(
                """INSERT INTO messages (conversation_id, role, content, timestamp, sequence)
                   VALUES (?, ?, ?, ?, ?)""",
                (msg.conversation_id, msg.role, msg.content, msg.timestamp, msg.sequence)
            )
        self.conn.commit()

    def search(
        self,
        query: str,
        tool: Optional[str] = None,
        project: Optional[str] = None,
        date_range: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 20,
    ) -> List[dict]:
        """Full-text search across all messages."""
        sql = """
            SELECT c.id, c.tool, c.project, c.session_id, c.title,
                   c.started_at, m.role, m.content, m.timestamp
            FROM messages_fts f
            JOIN messages m ON m.id = f.rowid
            JOIN conversations c ON c.id = m.conversation_id
            WHERE messages_fts MATCH ?
        """
        params: list = [query]

        if tool:
            sql += " AND c.tool = ?"
            params.append(tool)
        if project:
            sql += " AND c.project LIKE ?"
            params.append(f"%{project}%")
        if date_range:
            if ":" in date_range:
                start, end = date_range.split(":", 1)
                sql += " AND c.started_at >= ? AND c.started_at <= ?"
                params.extend([start, end])
            else:
                sql += " AND c.started_at >= ?"
                params.append(date_range)
        if role:
            sql += " AND m.role = ?"
            params.append(role)

        sql += " ORDER BY m.timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def list_sessions(
        self,
        tool: Optional[str] = None,
        project: Optional[str] = None,
        date_range: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List conversation sessions with optional filters."""
        sql = "SELECT * FROM conversations WHERE 1=1"
        params: list = []

        if tool:
            sql += " AND tool = ?"
            params.append(tool)
        if project:
            sql += " AND project LIKE ?"
            params.append(f"%{project}%")
        if date_range:
            if ":" in date_range:
                start, end = date_range.split(":", 1)
                sql += " AND started_at >= ? AND started_at <= ?"
                params.extend([start, end])
            else:
                sql += " AND started_at >= ?"
                params.append(date_range)

        sql += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get a full conversation with all messages."""
        conv_row = self.conn.execute(
            "SELECT * FROM conversations WHERE id = ? OR session_id = ?",
            (session_id, session_id)
        ).fetchone()
        if not conv_row:
            return None

        conv = dict(conv_row)
        msg_rows = self.conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY sequence",
            (conv["id"],)
        ).fetchall()
        conv["messages"] = [dict(r) for r in msg_rows]
        return conv

    def list_projects(self, tool: Optional[str] = None) -> List[dict]:
        """List all distinct projects."""
        sql = "SELECT DISTINCT project, tool, COUNT(*) as session_count FROM conversations"
        params: list = []
        if tool:
            sql += " WHERE tool = ?"
            params.append(tool)
        sql += " GROUP BY project, tool ORDER BY session_count DESC"
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> dict:
        """Get overall statistics."""
        total_conv = self.conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        total_msg = self.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        by_tool = self.conn.execute(
            "SELECT tool, COUNT(*) as count FROM conversations GROUP BY tool"
        ).fetchall()
        return {
            "total_conversations": total_conv,
            "total_messages": total_msg,
            "by_tool": {row["tool"]: row["count"] for row in by_tool},
        }

    def get_extended_stats(self) -> dict:
        """Get extended statistics with daily breakdowns for charting."""
        # Conversations per tool
        by_tool = self.conn.execute(
            "SELECT tool, COUNT(*) as count FROM conversations GROUP BY tool ORDER BY count DESC"
        ).fetchall()

        # Daily conversation counts
        daily_conversations = self.conn.execute(
            """SELECT DATE(started_at) as day, COUNT(*) as count
               FROM conversations
               WHERE started_at IS NOT NULL
               GROUP BY day ORDER BY day"""
        ).fetchall()

        # Daily message counts
        daily_messages = self.conn.execute(
            """SELECT DATE(m.timestamp) as day, COUNT(*) as count
               FROM messages m
               WHERE m.timestamp IS NOT NULL
               GROUP BY day ORDER BY day"""
        ).fetchall()

        # Daily message counts per tool
        daily_tool_messages = self.conn.execute(
            """SELECT DATE(m.timestamp) as day, c.tool, COUNT(*) as count
               FROM messages m
               JOIN conversations c ON c.id = m.conversation_id
               WHERE m.timestamp IS NOT NULL
               GROUP BY day, c.tool
               ORDER BY day"""
        ).fetchall()

        # Top projects
        top_projects = self.conn.execute(
            """SELECT project, COUNT(*) as count
               FROM conversations
               GROUP BY project ORDER BY count DESC LIMIT 10"""
        ).fetchall()

        # Messages per role
        by_role = self.conn.execute(
            "SELECT role, COUNT(*) as count FROM messages GROUP BY role"
        ).fetchall()

        return {
            "by_tool": {row["tool"]: row["count"] for row in by_tool},
            "daily_conversations": [{"date": row["day"], "count": row["count"]} for row in daily_conversations],
            "daily_messages": [{"date": row["day"], "count": row["count"]} for row in daily_messages],
            "daily_tool_messages": [
                {"date": row["day"], "tool": row["tool"], "count": row["count"]}
                for row in daily_tool_messages
            ],
            "top_projects": [{"project": row["project"], "count": row["count"]} for row in top_projects],
            "by_role": {row["role"]: row["count"] for row in by_role},
        }
