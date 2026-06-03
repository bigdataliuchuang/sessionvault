"""Extractor for Cursor conversations."""

import json
import logging
import os
import sqlite3
from collections import defaultdict

logger = logging.getLogger("ai_conversations.cursor")
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional

from ..models import Conversation, Message
from ..paths import get_cursor_state_db, get_cursor_workspace_storage_dir
from .base import BaseExtractor


class CursorExtractor(BaseExtractor):
    tool_name = "cursor"

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        db_path = get_cursor_state_db()
        if not db_path.exists():
            return

        since_dt = self._parse_since(since) if since else None

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            # Load project resolution data from ItemTable
            composer_project_map = self._load_composer_project_map(conn)

            # Pre-load ALL bubbles grouped by composer_id
            bubbles_by_composer = self._load_all_bubbles(conn)

            # Process composers one by one
            cursor = conn.execute(
                "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
            )
            for row in cursor:
                try:
                    composer_id = row["key"].replace("composerData:", "")
                    data = json.loads(row["value"])

                    conv = self._parse_composer(
                        composer_id, data, composer_project_map,
                        bubbles_by_composer.get(composer_id, [])
                    )
                    if not conv:
                        continue

                    if since_dt and conv.started_at:
                        try:
                            conv_dt = datetime.fromisoformat(conv.started_at.replace("Z", "+00:00"))
                            if conv_dt < since_dt:
                                continue
                        except ValueError:
                            pass

                    if project and project.lower() not in conv.project.lower():
                        continue

                    if conv.message_count > 0:
                        yield conv
                except Exception as e:
                    logger.warning(f"Error parsing composer {row['key'][:50]}: {e}")
                    continue
        finally:
            conn.close()

    def _load_composer_project_map(self, conn: sqlite3.Connection) -> Dict[str, str]:
        """Build composer_id → project_path mapping from ItemTable.

        Uses two keys:
        - glass.localAgentProjectMembership.v1: {composer_id: project_id}
        - glass.localAgentProjects.v1: [{id, workspace: {uri: {fsPath}}}]
        """
        result = {}

        # Step 1: membership (composer_id → project_id)
        membership = self._load_item_json(conn, "glass.localAgentProjectMembership.v1")
        if not isinstance(membership, dict):
            membership = {}

        # Step 2: projects (project_id → path)
        projects_raw = self._load_item_json(conn, "glass.localAgentProjects.v1")
        project_map = {}  # project_id → path
        if isinstance(projects_raw, list):
            for p in projects_raw:
                pid = p.get("id", "")
                ws = p.get("workspace", {})
                path = ws.get("uri", {}).get("fsPath", "")
                if pid and path:
                    project_map[pid] = path

        # Step 3: chain them
        for composer_id, project_id in membership.items():
            if project_id in project_map:
                result[composer_id] = project_map[project_id]

        # Also load workspaceMetadata.entries as fallback
        ws_meta = self._load_item_json(conn, "workspaceMetadata.entries")
        if isinstance(ws_meta, dict):
            entries = ws_meta.get("entries", [])
        elif isinstance(ws_meta, list):
            entries = ws_meta
        else:
            entries = []
        self._ws_metadata = {}
        for entry in entries:
            wid = entry.get("workspaceId", "")
            uri = entry.get("folderUri", "")
            if wid and uri:
                self._ws_metadata[wid] = uri.replace("file://", "")

        return result

    @staticmethod
    def _load_item_json(conn: sqlite3.Connection, key: str):
        """Load and parse a JSON value from ItemTable."""
        row = conn.execute(
            "SELECT value FROM ItemTable WHERE key = ?", (key,)
        ).fetchone()
        if not row or not row[0]:
            return None
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return None

    def _load_all_bubbles(self, conn: sqlite3.Connection) -> Dict[str, List[dict]]:
        """Load all bubbleId entries grouped by composer_id in one query."""
        result = defaultdict(list)
        cursor = conn.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'bubbleId:%'"
        )
        for row in cursor:
            key = row["key"]
            parts = key.split(":", 2)
            if len(parts) != 3:
                continue
            composer_id = parts[1]
            try:
                bubble = json.loads(row["value"])
                if isinstance(bubble, dict):
                    result[composer_id].append(bubble)
            except (json.JSONDecodeError, TypeError):
                continue
        return dict(result)

    def _parse_composer(
        self,
        composer_id: str,
        data: dict,
        composer_project_map: Dict[str, str],
        bubbles: List[dict],
    ) -> Optional[Conversation]:
        """Parse a single composer session."""
        messages = []
        timestamps = []

        # Priority 1: glass membership map (most reliable)
        project_path = composer_project_map.get(composer_id, "")

        # Priority 2: allAttachedFileCodeChunksUris with .git detection
        if not project_path:
            project_path = self._infer_project_from_uris(data)

        # Priority 3: context.fileSelections
        if not project_path:
            project_path = self._infer_project_from_file_selections(data)

        # Priority 3: workspaceFolder field
        if not project_path:
            wf = data.get("workspaceFolder", "")
            if isinstance(wf, str) and wf:
                project_path = wf

        if not project_path:
            project_path = "unknown"

        # Parse messages
        conversation = data.get("conversation", [])
        if isinstance(conversation, list) and conversation:
            for i, item in enumerate(conversation):
                if not isinstance(item, dict):
                    continue
                msg = self._parse_conversation_item(item, i)
                if msg:
                    messages.append(msg)
                    if msg.timestamp:
                        timestamps.append(msg.timestamp)

        if not messages and bubbles:
            for i, bubble in enumerate(bubbles):
                msg = self._parse_bubble(bubble, composer_id, i)
                if msg:
                    messages.append(msg)

        messages = [m for m in messages if m.content.strip()]
        if not messages:
            return None

        for i, msg in enumerate(messages):
            msg.sequence = i

        conv_id = self.make_id(self.tool_name, composer_id)
        for msg in messages:
            msg.conversation_id = conv_id

        title = ""
        for msg in messages:
            if msg.role == "user":
                title = msg.content[:100].replace("\n", " ")
                break

        return Conversation(
            id=conv_id,
            tool=self.tool_name,
            project=project_path,
            session_id=composer_id,
            title=title,
            started_at=timestamps[0] if timestamps else "",
            ended_at=timestamps[-1] if timestamps else "",
            message_count=len(messages),
            messages=messages,
        )

    @staticmethod
    def _infer_project_from_file_selections(data: dict) -> str:
        """Infer project path from context.fileSelections."""
        ctx = data.get("context", {})
        if not isinstance(ctx, dict):
            return ""
        selections = ctx.get("fileSelections", [])
        if not isinstance(selections, list):
            return ""
        for sel in selections:
            if not isinstance(sel, dict):
                continue
            uri = sel.get("uri", sel.get("path", ""))
            if isinstance(uri, str) and uri.startswith("file://"):
                path = uri.replace("file://", "")
                parent = os.path.dirname(path)
                if parent and parent != "/":
                    return parent
        return ""

    @staticmethod
    def _infer_project_from_uris(data: dict) -> str:
        """Infer project path from allAttachedFileCodeChunksUris by walking up to find .git."""
        uris = data.get("allAttachedFileCodeChunksUris", [])
        if not uris:
            return ""

        paths = [u.replace("file://", "") for u in uris if isinstance(u, str) and u.startswith("file://")]
        if not paths:
            return ""

        # Walk up from first file to find project root
        PROJECT_MARKERS = {".git", "package.json", "pyproject.toml", "pom.xml", "Cargo.toml", "go.mod", "build.gradle"}
        d = os.path.dirname(paths[0]) if paths else ""
        for _ in range(15):
            if not d:
                break
            try:
                if set(os.listdir(d)) & PROJECT_MARKERS:
                    return d
            except (PermissionError, OSError):
                break
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent

        # Fallback: common path
        try:
            return os.path.commonpath(paths) if len(paths) > 1 else os.path.dirname(paths[0])
        except ValueError:
            return ""

    @staticmethod
    def _parse_conversation_item(item: dict, index: int) -> Optional[Message]:
        """Parse an item from the conversation array."""
        role = item.get("role", "")
        if role not in ("user", "assistant"):
            return None

        content = BaseExtractor.extract_text(item.get("content", ""))
        if not content.strip():
            return None

        ts = item.get("timestamp", item.get("createdAt", ""))

        return Message(
            conversation_id="",
            role=role,
            content=content,
            timestamp=str(ts) if ts else "",
            sequence=index,
        )

    @staticmethod
    def _parse_bubble(bubble: dict, composer_id: str, index: int) -> Optional[Message]:
        """Parse a bubbleId entry."""
        bubble_type = bubble.get("type", 0)
        if bubble_type == 1:
            role = "user"
        elif bubble_type == 2:
            role = "assistant"
        else:
            return None

        content = ""
        for field in ("text", "content", "richText"):
            val = bubble.get(field)
            if val and isinstance(val, str):
                content = BaseExtractor.extract_text(val)
                if content.strip():
                    break

        if not content.strip():
            return None

        ts = bubble.get("timestamp", bubble.get("createdAt", ""))

        return Message(
            conversation_id="",
            role=role,
            content=content,
            timestamp=str(ts) if ts else "",
            sequence=index,
        )

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
