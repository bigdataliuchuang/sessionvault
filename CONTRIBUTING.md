# Contributing to SessionVault

Thank you for considering contributing to SessionVault. This guide covers everything you need to get started.

---

## Development Environment Setup

### Prerequisites

- Python 3.9 or later
- Git

### Clone and install

```bash
git clone https://github.com/user/ai-conversations.git
cd ai-conversations

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# For full functionality (optional)
pip install -e ".[all]"
```

### Verify the install

```bash
sessionvault --help
```

---

## Running Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a single test file
pytest tests/test_claude_code.py -v

# Run a specific test class or method
pytest tests/test_claude_code.py::TestClaudeCodeExtractor::test_extract_from_temp_dir -v
```

Tests use `pytest` and `unittest.mock` (for patching filesystem paths). No external services are required.

---

## Project Structure

```
src/ai_conversations/
  extractors/
    base.py           # BaseExtractor ABC — all extractors inherit from this
    claude_code.py    # Claude Code JSONL extractor
    codex.py          # Codex JSONL extractor
    cursor.py         # Cursor SQLite extractor
    antigravity.py    # Antigravity SQLite extractor
  models.py           # Conversation and Message dataclasses
  paths.py            # Cross-platform path detection (pure computation, no I/O)
  config.py           # Configuration
  db.py               # SQLite database layer
  cli/                # CLI commands (sync, search, stats, export)
  server/mcp.py       # MCP server integration
  tui/                # Textual TUI
  web/                # FastAPI web UI
tests/
  test_claude_code.py
  test_codex.py
  test_cursor.py
  test_paths.py
```

---

## Adding a New Extractor

Each AI tool gets its own extractor module. Here is the step-by-step process.

### 1. Add path detection in `src/ai_conversations/paths.py`

Add a function that returns the tool's data directory as a `Path`, using OS-specific logic in `get_app_support_dir()` or `Path.home()` as appropriate.

```python
def get_newtool_dir() -> Path:
    """NewTool data directory."""
    return get_app_support_dir() / "NewTool"
```

### 2. Create the extractor module

Create `src/ai_conversations/extractors/newtool.py`. Inherit from `BaseExtractor` and implement the `extract` method.

```python
"""Extractor for NewTool conversations."""

import logging
from typing import Generator, Optional

from ..models import Conversation, Message
from ..paths import get_newtool_dir
from .base import BaseExtractor

logger = logging.getLogger("ai_conversations.newtool")


class NewToolExtractor(BaseExtractor):
    tool_name = "newtool"

    def extract(
        self,
        since: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Generator[Conversation, None, None]:
        data_dir = get_newtool_dir()
        if not data_dir.exists():
            return

        # TODO: iterate over the tool's data files, parse them,
        # and yield Conversation objects.
        # Use self.make_id(self.tool_name, session_id) for the conversation ID.
        # Use self.extract_text(content) to normalize content fields.
        # Use self.smart_title(text) to generate a meaningful title.
        ...
```

**Key methods from `BaseExtractor`:**

| Method | Purpose |
|---|---|
| `make_id(tool, session_id)` | Generate a deterministic 16-char hex ID |
| `smart_title(text, max_len=80)` | Extract a clean title, skipping generic/short strings |
| `extract_text(content)` | Normalize str, list-of-blocks, or dict content to plain text |
| `clean_codex_title(title)` | Strip garbled characters (Codex-specific) |

### 3. Register the extractor

In `src/ai_conversations/extractors/__init__.py`:

1. Import the new class
2. Add it to `__all__`
3. Add it to the `EXTRACTORS` registry dict

```python
from .newtool import NewToolExtractor

__all__ = [
    ...
    "NewToolExtractor",
]

EXTRACTORS = {
    ...
    "newtool": NewToolExtractor,
}
```

### 4. Add CLI support

Update the `--tool` option choices in `src/ai_conversations/cli/sync.py` (and `search.py` if applicable) to include `"newtool"`.

### 5. Write tests

Create `tests/test_newtool.py`. Follow the existing patterns:

- Use `tempfile.TemporaryDirectory` to create mock data files
- Use `unittest.mock.patch` to redirect path functions to the temp directory
- Test extraction, edge cases (empty sessions, missing files), and ID determinism

```python
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_conversations.extractors.newtool import NewToolExtractor


class TestNewToolExtractor:
    def test_extract_from_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock data files here
            ...

            extractor = NewToolExtractor()
            with patch("ai_conversations.extractors.newtool.get_newtool_dir", return_value=Path(tmpdir)):
                results = list(extractor.extract())

            assert len(results) >= 1
            conv = results[0]
            assert conv.tool == "newtool"

    def test_extract_missing_dir(self):
        extractor = NewToolExtractor()
        with patch("ai_conversations.extractors.newtool.get_newtool_dir", return_value=Path("/nonexistent")):
            results = list(extractor.extract())
        assert results == []
```

Run the new tests before submitting:

```bash
pytest tests/test_newtool.py -v
```

---

## Code Style

- **Python version:** Target 3.9+ (use `typing.Optional`, `typing.Generator` — no `X | Y` union syntax)
- **Type hints:** Use them on all public method signatures
- **Docstrings:** Module-level docstrings for every file; docstrings on public classes and methods
- **Logging:** Use `logging.getLogger("ai_conversations.<module>")` — not `print()`
- **Error handling:** Log warnings and continue (extractors should not crash on bad data); use `try/except` around I/O
- **Imports:** Standard library first, then third-party, then local. Use absolute imports from the package root (`from ..models import ...`)
- **Data models:** Use `@dataclass` from `dataclasses` (see `models.py`)
- **No external dependencies in core:** The `dependencies` list in `pyproject.toml` is intentionally empty. Optional features go under `[project.optional-dependencies]`

---

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`
2. **Write code** following the style guidelines above
3. **Add or update tests** for any changed or new functionality
4. **Run the full test suite** and confirm it passes:
   ```bash
   pytest tests/ -v
   ```
5. **Open a PR** against `main` with:
   - A clear title describing the change
   - A description of what was changed and why
   - Reference to any related issues
6. **Respond to review feedback** promptly

### PR checklist

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] New code has type hints and docstrings
- [ ] New extractor is registered in `__init__.py` and `EXTRACTORS` dict
- [ ] No new unconditional dependencies added to `pyproject.toml`
- [ ] Cross-platform path logic uses `paths.py` helpers (no hardcoded OS paths)

---

## Reporting Issues

Open an issue on GitHub with:

- The tool and OS you are using
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output (run with `--verbose` if available)
