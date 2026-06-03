"""Extractor for Antigravity IDE conversations.

Note: Antigravity IDE (a Cursor/VS Code fork) stores chat data differently:
- ChatSessionStore.index is typically empty (no local chat history)
- trajectorySummaries is protobuf-encoded, not plain JSON
- Workspace databases use ItemTable only (no cursorDiskKV)

This extractor checks for readable chat data. If none is found,
it yields nothing (the user should be informed via CLI output).
"""

import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from ..models import Conversation, Message
from ..paths import get_antigravity_dir
from .base import BaseExtractor


class AntigravityExtractor(BaseExtractor):
    tool_name = "antigravity"

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        db_path = self._get_state_db()
        if not db_path.exists():
            return

        since_dt = self._parse_since(since) if since else None

        # Antigravity uses ItemTable (not cursorDiskKV like Cursor)
        # Check if there's any readable chat data
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            # Check ChatSessionStore.index
            row = conn.execute(
                "SELECT value FROM ItemTable WHERE key = 'chat.ChatSessionStore.index'"
            ).fetchone()
            if row and row[0]:
                try:
                    index = json.loads(row[0])
                    entries = index.get("entries", {})
                    if entries:
                        # If entries exist, try to extract them
                        for session_id, session_data in entries.items():
                            conv = self._parse_session_entry(
                                session_id, session_data, conn, since_dt, project
                            )
                            if conv and conv.message_count > 0:
                                yield conv
                except (json.JSONDecodeError, TypeError):
                    pass
        finally:
            conn.close()

    def _get_state_db(self) -> Path:
        return get_antigravity_dir() / "User" / "globalStorage" / "state.vscdb"

    def _parse_session_entry(
        self,
        session_id: str,
        session_data: dict,
        conn: sqlite3.Connection,
        since_dt: Optional[datetime],
        project: Optional[str],
    ) -> Optional[Conversation]:
        """Try to parse a session entry from ChatSessionStore.index."""
        # This is speculative - we don't know the exact schema
        # Antigravity may not store full conversation data here
        return None

    @staticmethod
    def _parse_since(since: str) -> Optional[datetime]:
        if since.endswith("d"):
            try:
                return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(since)
        except ValueError:
            return None
