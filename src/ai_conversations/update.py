"""Auto-update checker for SessionVault."""

import json
import urllib.request
from importlib.metadata import version as get_version


def check_for_updates() -> Optional[str]:
    """Check PyPI for latest version. Returns update message or None."""
    try:
        current = get_version("sessionvault")
        url = "https://pypi.org/pypi/sessionvault/json"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            latest = data["info"]["version"]
            if latest != current:
                return f"Update available: {current} → {latest}\n  pip install --upgrade sessionvault"
    except Exception:
        pass
    return None


def print_update_check():
    """Print update notification if available."""
    msg = check_for_updates()
    if msg:
        print(f"\n\033[33m⬆ {msg}\033[0m\n")
