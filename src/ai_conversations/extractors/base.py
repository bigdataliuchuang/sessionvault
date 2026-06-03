"""Base class for all tool extractors."""

import hashlib
from abc import ABC, abstractmethod
from typing import Generator, Optional

from ..models import Conversation


class BaseExtractor(ABC):
    """Abstract base for extracting conversations from AI tools."""

    tool_name: str = ""

    @abstractmethod
    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        """Yield Conversation objects from the tool's local storage.

        Args:
            since: Only extract sessions modified after this date (ISO string or 'Nd' duration).
            project: Only extract sessions from this project path (partial match).
        """
        ...

    @staticmethod
    def make_id(tool: str, session_id: str) -> str:
        """Generate a deterministic internal ID from tool + session_id."""
        raw = f"{tool}:{session_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # Content types to skip (tool calls, system messages, etc.)
    SKIP_TYPES = {"tool_use", "tool_result", "tool_call", "function_call", "function_result"}

    @staticmethod
    def extract_text(content) -> str:
        """Extract plain text from various content formats.

        Handles: str, list of content blocks, nested dicts with 'text' fields.
        Skips tool_use, tool_result, function_call blocks to keep index lean.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    # Skip tool-related blocks
                    block_type = item.get("type", "")
                    if block_type in BaseExtractor.SKIP_TYPES:
                        continue
                    # Skip items with tool-related names
                    if "tool_use_id" in item or "tool_call_id" in item:
                        continue
                    # Common patterns: {"type": "text", "text": "..."}, {"text": "..."}
                    if "text" in item and isinstance(item["text"], str):
                        parts.append(item["text"])
                    elif "content" in item:
                        parts.append(BaseExtractor.extract_text(item["content"]))
            return "\n".join(parts)
        if isinstance(content, dict):
            # Skip tool-related blocks at dict level
            block_type = content.get("type", "")
            if block_type in BaseExtractor.SKIP_TYPES:
                return ""
            if "text" in content and isinstance(content["text"], str):
                return content["text"]
            if "content" in content:
                return BaseExtractor.extract_text(content["content"])
        return str(content) if content else ""
