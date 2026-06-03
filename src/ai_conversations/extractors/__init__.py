"""Extractors for various AI coding tools."""

from .base import BaseExtractor
from .claude_code import ClaudeCodeExtractor
from .codex import CodexExtractor
from .cursor import CursorExtractor
from .antigravity import AntigravityExtractor

__all__ = [
    "BaseExtractor",
    "ClaudeCodeExtractor",
    "CodexExtractor",
    "CursorExtractor",
    "AntigravityExtractor",
]

# Registry for dynamic lookup
EXTRACTORS = {
    "claude-code": ClaudeCodeExtractor,
    "codex": CodexExtractor,
    "cursor": CursorExtractor,
    "antigravity": AntigravityExtractor,
}
