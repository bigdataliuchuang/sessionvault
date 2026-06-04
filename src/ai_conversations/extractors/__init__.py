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


def _load_external_plugins() -> None:
    """Merge external plugins into EXTRACTORS.

    Plugins live in ~/.sessionvault/plugins/.  Each is a .py file that
    exposes either an ``extract()`` function or an ``EXTRACTOR_CLASS``
    (see :mod:`ai_conversations.plugins` for details).
    """
    try:
        from ..plugins import load_plugins

        plugins = load_plugins()
        for name, extractor in plugins.items():
            if name in EXTRACTORS:
                # Do not allow plugins to shadow built-in extractors.
                continue
            EXTRACTORS[name] = extractor
    except Exception:
        # Plugins are optional; a broken plugin dir should not break the app.
        pass


_load_external_plugins()
