"""Extractor for Codex CLI / Codex.app conversations."""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Generator, Optional

from ..models import Conversation, Message
from ..paths import get_codex_sessions_dir, get_codex_session_index, get_codex_archived_sessions_dir
from .base import BaseExtractor

logger = logging.getLogger("ai_conversations.codex")


class CodexExtractor(BaseExtractor):
    tool_name = "codex"

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        # Build session index: id → thread_name
        index = self._load_session_index()

        since_dt = self._parse_since(since) if since else None

        # Scan both sessions/ and archived_sessions/
        for sessions_dir in [get_codex_sessions_dir(), get_codex_archived_sessions_dir()]:
            if not sessions_dir.exists():
                continue
            for jsonl_path in sorted(sessions_dir.rglob("rollout-*.jsonl")):
                try:
                    if since_dt:
                        mtime = datetime.fromtimestamp(jsonl_path.stat().st_mtime)
                        if mtime < since_dt:
                            continue

                    uuid = self._extract_uuid(jsonl_path.name)
                    if not uuid:
                        continue

                    file_mtime = jsonl_path.stat().st_mtime
                    conv = self._parse_session(jsonl_path, uuid, index.get(uuid, ""))
                    if not conv:
                        continue
                    conv.file_mtime = file_mtime

                    if project and project.lower() not in conv.project.lower():
                        continue

                    if conv.message_count > 0:
                        yield conv
                except Exception as e:
                    logger.warning(f"Error parsing {jsonl_path.name}: {e}")
                    continue

    def _load_session_index(self) -> Dict[str, str]:
        """Load session_index.jsonl → {session_id: thread_name}."""
        index_path = get_codex_session_index()
        result = {}
        if not index_path.exists():
            return result
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        sid = entry.get("id", "")
                        name = entry.get("thread_name", "")
                        if sid:
                            result[sid] = name
                    except json.JSONDecodeError:
                        continue
        except (OSError, PermissionError):
            pass
        return result

    @staticmethod
    def _extract_uuid(filename: str) -> Optional[str]:
        """Extract UUID from rollout filename like 'rollout-2026-05-09T16-33-06-019e0bde-...'.jsonl'"""
        # Remove 'rollout-' prefix and '.jsonl' suffix
        name = filename.replace("rollout-", "").replace(".jsonl", "")
        # Find UUID pattern (8-4-4-4-12 hex)
        match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", name, re.IGNORECASE)
        return match.group(1) if match else None

    def _parse_session(
        self, jsonl_path: Path, session_id: str, title: str
    ) -> Optional[Conversation]:
        """Parse a Codex rollout JSONL file."""
        messages = []
        project_path = ""
        timestamps = []

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    entry_type = entry.get("type", "")
                    payload = entry.get("payload", {})
                    if not isinstance(payload, dict):
                        payload = {}

                    ts = entry.get("timestamp", "")

                    if entry_type == "session_meta":
                        project_path = payload.get("cwd", "")
                        continue

                    if entry_type == "event_msg":
                        role = payload.get("role", "")
                        if role == "user":
                            content = self.extract_text(payload.get("content", ""))
                            if content.strip():
                                timestamps.append(ts)
                                messages.append(Message(
                                    conversation_id="",
                                    role="user",
                                    content=content,
                                    timestamp=ts,
                                    sequence=len(messages),
                                ))
                        continue

                    if entry_type == "response_item":
                        role = payload.get("role", "")
                        if role in ("user", "assistant"):
                            content = self.extract_text(payload.get("content", ""))
                            if content.strip():
                                timestamps.append(ts)
                                messages.append(Message(
                                    conversation_id="",
                                    role=role,
                                    content=content,
                                    timestamp=ts,
                                    sequence=len(messages),
                                ))
                        continue
        except (OSError, PermissionError):
            return None

        if not messages:
            return None

        conv_id = self.make_id(self.tool_name, session_id)
        for msg in messages:
            msg.conversation_id = conv_id

        # Clean title from session_index (may have garbled chars)
        if title:
            title = self.clean_codex_title(title)

        # Fallback to first meaningful user message
        if not title:
            for msg in messages:
                if msg.role != "user":
                    continue
                content = msg.content.strip()
                if not content or len(content) < 5:
                    continue
                # Skip system/environment messages
                if content.startswith("#"):
                    continue
                if content.startswith("<"):
                    continue
                if "AGENTS.md" in content:
                    continue
                if "environment_context" in content:
                    continue
                if "permissions instructions" in content:
                    continue
                title = content.replace("\n", " ").strip()[:80]
                break

        return Conversation(
            id=conv_id,
            tool=self.tool_name,
            project=project_path or "unknown",
            session_id=session_id,
            title=title,
            started_at=timestamps[0] if timestamps else "",
            ended_at=timestamps[-1] if timestamps else "",
            message_count=len(messages),
            messages=messages,
        )

    @staticmethod
    def _parse_since(since: str) -> Optional[datetime]:
        if since.endswith("d"):
            try:
                days = int(since[:-1])
                return (datetime.now() - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(since)
        except ValueError:
            return None
