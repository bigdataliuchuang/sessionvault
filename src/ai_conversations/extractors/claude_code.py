"""Extractor for Claude Code conversations."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from ..models import Conversation, Message
from ..paths import get_claude_code_dir
from .base import BaseExtractor

logger = logging.getLogger("ai_conversations.claude_code")


def _decode_project_dir(dirname: str) -> str:
    """Decode Claude Code directory name back to project path.

    Encoding is simply: / → -
    Note: This is ambiguous when path segments contain hyphens.
    Prefer reading 'cwd' from the JSONL data when available.
    """
    return "/" + dirname.lstrip("-").replace("-", "/")


class ClaudeCodeExtractor(BaseExtractor):
    tool_name = "claude-code"

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        base_dir = get_claude_code_dir()
        if not base_dir.exists():
            return

        since_dt = self._parse_since(since) if since else None

        for project_dir in sorted(base_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            if project_dir.name == "memory":
                continue

            # Use directory name as initial project hint (may be imprecise)
            project_hint = _decode_project_dir(project_dir.name)

            for jsonl_file in sorted(project_dir.glob("*.jsonl")):
                try:
                    file_mtime = jsonl_file.stat().st_mtime
                    if since_dt:
                        mtime = datetime.fromtimestamp(file_mtime)
                        if mtime < since_dt:
                            continue

                    conv = self._parse_session(jsonl_file, project_hint)
                    if not conv or conv.message_count == 0:
                        continue
                    conv.file_mtime = file_mtime

                    if project and project.lower() not in conv.project.lower():
                        continue

                    yield conv
                except Exception as e:
                    logger.warning(f"Error parsing {jsonl_file.name}: {e}")
                    continue

    def _parse_session(self, jsonl_path: Path, project_hint: str) -> Optional[Conversation]:
        """Parse a single JSONL session file into a Conversation."""
        session_id = jsonl_path.stem
        messages = []
        title = ""
        timestamps = []
        project_path = project_hint  # fallback

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

                    # Read cwd from any entry that has it (most reliable source)
                    if "cwd" in entry and entry["cwd"]:
                        project_path = entry["cwd"]

                    if entry_type == "ai-title":
                        title = self.extract_text(entry.get("title", ""))
                        continue

                    if entry_type not in ("user", "assistant"):
                        continue

                    msg_data = entry.get("message", {})
                    if not isinstance(msg_data, dict):
                        continue

                    role = msg_data.get("role", entry_type)
                    content = self.extract_text(msg_data.get("content", ""))
                    if not content.strip():
                        continue

                    ts = entry.get("timestamp", "")
                    timestamps.append(ts)

                    messages.append(Message(
                        conversation_id="",
                        role=role,
                        content=content,
                        timestamp=ts,
                        sequence=len(messages),
                    ))
        except (OSError, PermissionError):
            return None

        if not messages:
            return None

        conv_id = self.make_id(self.tool_name, session_id)
        for msg in messages:
            msg.conversation_id = conv_id

        if not title and messages:
            for msg in messages:
                if msg.role == "user":
                    title = msg.content[:100].replace("\n", " ")
                    break

        return Conversation(
            id=conv_id,
            tool=self.tool_name,
            project=project_path,
            session_id=session_id,
            title=title,
            started_at=timestamps[0] if timestamps else "",
            ended_at=timestamps[-1] if timestamps else "",
            message_count=len(messages),
            messages=messages,
        )

    @staticmethod
    def _parse_since(since: str) -> Optional[datetime]:
        """Parse 'Nd' duration or ISO date string."""
        if since.endswith("d"):
            try:
                days = int(since[:-1])
                return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(since)
        except ValueError:
            return None
