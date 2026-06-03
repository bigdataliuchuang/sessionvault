"""Tests for Cursor extractor."""

from ai_conversations.extractors.cursor import CursorExtractor


class TestCursorExtractor:
    def test_make_id_deterministic(self):
        id1 = CursorExtractor.make_id("cursor", "5abd2f9d-af25-4f7e-993c-ea70f072be06")
        id2 = CursorExtractor.make_id("cursor", "5abd2f9d-af25-4f7e-993c-ea70f072be06")
        assert id1 == id2

    def test_parse_bubble_user(self):
        bubble = {"type": 1, "text": "Hello"}
        msg = CursorExtractor._parse_bubble(bubble, "test-id", 0)
        assert msg is not None
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_parse_bubble_assistant(self):
        bubble = {"type": 2, "text": "Hi there!"}
        msg = CursorExtractor._parse_bubble(bubble, "test-id", 0)
        assert msg is not None
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_parse_bubble_unknown_type(self):
        bubble = {"type": 99, "text": "Something"}
        msg = CursorExtractor._parse_bubble(bubble, "test-id", 0)
        assert msg is None

    def test_parse_bubble_empty_content(self):
        bubble = {"type": 1, "text": ""}
        msg = CursorExtractor._parse_bubble(bubble, "test-id", 0)
        assert msg is None
