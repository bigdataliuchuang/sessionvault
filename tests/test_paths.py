"""Tests for cross-platform path detection."""

import platform
from unittest.mock import patch

from ai_conversations.paths import (
    get_app_support_dir,
    get_claude_code_dir,
    get_codex_sessions_dir,
    get_cursor_dir,
    get_antigravity_dir,
    get_data_dir,
)


class TestAppSupportDir:
    def test_macos(self):
        with patch("ai_conversations.paths.platform") as mock:
            mock.system.return_value = "Darwin"
            result = get_app_support_dir()
            assert "Library" in str(result)
            assert "Application Support" in str(result)

    def test_linux(self):
        with patch("ai_conversations.paths.platform") as mock, \
             patch.dict("os.environ", {"XDG_CONFIG_HOME": "/home/user/.config"}):
            mock.system.return_value = "Linux"
            result = get_app_support_dir()
            assert str(result) == "/home/user/.config"

    def test_windows(self):
        with patch("ai_conversations.paths.platform") as mock, \
             patch.dict("os.environ", {"APPDATA": "C:\\Users\\user\\AppData\\Roaming"}):
            mock.system.return_value = "Windows"
            result = get_app_support_dir()
            assert "AppData" in str(result)


class TestToolPaths:
    def test_claude_code_uses_home(self):
        result = get_claude_code_dir()
        assert ".claude" in str(result)
        assert "projects" in str(result)

    def test_codex_uses_home(self):
        result = get_codex_sessions_dir()
        assert ".codex" in str(result)
        assert "sessions" in str(result)

    def test_cursor_uses_app_support(self):
        result = get_cursor_dir()
        assert "Cursor" in str(result)

    def test_antigravity_uses_app_support(self):
        result = get_antigravity_dir()
        assert "Antigravity" in str(result)

    def test_data_dir_uses_home(self):
        result = get_data_dir()
        assert ".sessionvault" in str(result)
