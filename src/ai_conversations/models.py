"""Data models for conversations and messages."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    """A single message within a conversation."""
    conversation_id: str
    role: str               # "user" / "assistant"
    content: str            # plain text content
    timestamp: str          # ISO timestamp
    sequence: int           # order within conversation (0-based)


@dataclass
class Conversation:
    """A conversation session from an AI tool."""
    id: str                 # internal unique ID (hash of tool + session_id)
    tool: str               # "claude-code" / "codex" / "cursor"
    project: str            # project path
    session_id: str         # native session ID from the tool
    title: str              # conversation title
    started_at: str         # ISO timestamp
    ended_at: str           # ISO timestamp
    message_count: int
    file_mtime: Optional[float] = None  # source file modification time
    messages: List[Message] = field(default_factory=list)
