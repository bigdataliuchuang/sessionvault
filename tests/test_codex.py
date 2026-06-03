"""Tests for Codex extractor."""

from ai_conversations.extractors.codex import CodexExtractor


class TestCodexExtractor:
    def test_extract_uuid(self):
        assert CodexExtractor._extract_uuid(
            "rollout-2026-05-09T16-33-06-019e0bde-6af0-7130-bac7-2cfbf19f2475.jsonl"
        ) == "019e0bde-6af0-7130-bac7-2cfbf19f2475"

    def test_extract_uuid_invalid(self):
        assert CodexExtractor._extract_uuid("not-a-valid-name.jsonl") is None

    def test_make_id_deterministic(self):
        id1 = CodexExtractor.make_id("codex", "019e0bde-6af0-7130-bac7-2cfbf19f2475")
        id2 = CodexExtractor.make_id("codex", "019e0bde-6af0-7130-bac7-2cfbf19f2475")
        assert id1 == id2
