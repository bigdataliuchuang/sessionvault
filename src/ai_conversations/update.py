"""Auto-update checker for SessionVault."""

from __future__ import annotations

import json
import logging
import sys
import urllib.request
from importlib.metadata import version as get_version
from typing import Optional

logger = logging.getLogger("ai_conversations.update")

PYPI_JSON_URL = "https://pypi.org/pypi/sessionvault/json"
REQUEST_TIMEOUT = 5  # seconds


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of ints.

    Falls back to (0,) for unparseable versions so comparison still works
    (the inequality will just be wrong, which is acceptable for a
    best-effort notification).
    """
    try:
        # Strip common pre-release suffixes (e.g. "1.0.0rc1" -> "1.0.0")
        release = version_str.split("rc")[0].split("a")[0].split("b")[0]
        return tuple(int(part) for part in release.split("."))
    except (ValueError, AttributeError):
        return (0,)


def check_for_updates() -> Optional[str]:
    """Check PyPI for a newer version than the installed one.

    Returns a human-readable update message if a newer version exists,
    or ``None`` if the package is up to date or the check fails.

    The check is best-effort: any network or parsing error is silently
    swallowed so the CLI never fails because of a version check.
    """
    try:
        current = get_version("sessionvault")
    except Exception:
        # Package metadata not available (e.g. running from source).
        return None

    try:
        with urllib.request.urlopen(PYPI_JSON_URL, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            latest: str = data["info"]["version"]
    except Exception as exc:
        logger.debug("Update check failed (network): %s", exc)
        return None

    if _parse_version(latest) > _parse_version(current):
        return (
            f"Update available: {current} -> {latest}\n"
            f"  Run: pip install --upgrade sessionvault"
        )
    return None


def print_update_check() -> None:
    """Print an update notification to stderr if a newer version exists."""
    try:
        msg = check_for_updates()
        if msg:
            print(f"\n\033[33m{msg}\033[0m\n", file=sys.stderr)
    except Exception:
        # Defensive: the notification should never crash the CLI.
        pass
