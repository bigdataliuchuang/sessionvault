"""Tests for Claude Code extractor."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_conversations.extractors.claude_code import ClaudeCodeExtractor, _decode_project_dir


class TestDecodeProjectDir:
    def test_simple_path(self):
        assert _decode_project_dir("-Users-liuchuang-Projects") == "/Users/liuchuang/Projects"

    def test_path_with_double_dash(self):
        # -- appears when a / precedes a - in the original path
        # Directory: -Users-liuchuang--claude
        # Decoded naively: /Users/liuchuang/-claude (but ambiguous)
        result = _decode_project_dir("-Users-liuchuang--claude")
        # - replaces /, so -- becomes //
        assert "/Users/liuchuang" in result

    def test_complex_path(self):
        # Directory name uses - for /
        result = _decode_project_dir("-Users-liuchuang-Downloads-github")
        assert result.startswith("/Users/liuchuang")


class TestClaudeCodeExtractor:
    def test_extract_text_string(self):
        assert ClaudeCodeExtractor.extract_text("hello") == "hello"

    def test_extract_text_list(self):
        content = [{"type": "text", "text": "hello"}, {"type": "text", "text": "world"}]
        assert ClaudeCodeExtractor.extract_text(content) == "hello\nworld"

    def test_extract_text_empty(self):
        assert ClaudeCodeExtractor.extract_text("") == ""
        assert ClaudeCodeExtractor.extract_text(None) == ""
        assert ClaudeCodeExtractor.extract_text([]) == ""

    def test_make_id_deterministic(self):
        id1 = ClaudeCodeExtractor.make_id("claude-code", "abc-123")
        id2 = ClaudeCodeExtractor.make_id("claude-code", "abc-123")
        assert id1 == id2
        assert len(id1) == 16

    def test_make_id_different_sessions(self):
        id1 = ClaudeCodeExtractor.make_id("claude-code", "abc-123")
        id2 = ClaudeCodeExtractor.make_id("claude-code", "def-456")
        assert id1 != id2

    def test_extract_from_temp_dir(self):
        """Test extraction with a mock JSONL file that includes cwd."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "-test-project"
            project_dir.mkdir()

            session_file = project_dir / "test-session-id.jsonl"
            entries = [
                {"type": "mode", "mode": "normal", "sessionId": "test-session-id"},
                {
                    "type": "user",
                    "message": {"role": "user", "content": "Hello AI"},
                    "sessionId": "test-session-id",
                    "timestamp": "2026-06-03T10:00:00Z",
                    "cwd": "/test/project",
                },
                {
                    "type": "assistant",
                    "message": {"role": "assistant", "content": "Hello! How can I help?"},
                    "sessionId": "test-session-id",
                    "timestamp": "2026-06-03T10:00:05Z",
                    "cwd": "/test/project",
                },
            ]
            with open(session_file, "w") as f:
                for entry in entries:
                    f.write(json.dumps(entry) + "\n")

            extractor = ClaudeCodeExtractor()
            with patch("ai_conversations.extractors.claude_code.get_claude_code_dir", return_value=Path(tmpdir)):
                results = list(extractor.extract())

            assert len(results) == 1
            conv = results[0]
            assert conv.tool == "claude-code"
            assert conv.session_id == "test-session-id"
            assert conv.project == "/test/project"  # Read from cwd field
            assert conv.message_count == 2
            assert conv.messages[0].role == "user"
            assert conv.messages[0].content == "Hello AI"
            assert conv.messages[1].role == "assistant"
            assert conv.messages[1].content == "Hello! How can I help?"

    def test_extract_empty_session_skipped(self):
        """Sessions with no user/assistant messages should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "-test-project"
            project_dir.mkdir()

            session_file = project_dir / "empty-session.jsonl"
            with open(session_file, "w") as f:
                f.write(json.dumps({"type": "mode", "mode": "normal", "sessionId": "empty"}) + "\n")

            extractor = ClaudeCodeExtractor()
            with patch("ai_conversations.extractors.claude_code.get_claude_code_dir", return_value=Path(tmpdir)):
                results = list(extractor.extract())

            assert len(results) == 0
