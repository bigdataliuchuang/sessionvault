"""Health check subcommand for SessionVault."""

import importlib
import sqlite3
import sys

from ..config import get_config
from ..paths import (
    get_claude_code_dir,
    get_codex_sessions_dir,
    get_cursor_dir,
    get_cursor_state_db,
    get_antigravity_dir,
    get_data_dir,
    get_db_path,
)


# Each entry: (label, check_callable)
# check_callable returns (ok: bool, detail: str)

def _check_tool_dirs():
    """Check which AI tool data directories exist."""
    tools = [
        ("Claude Code", get_claude_code_dir()),
        ("Codex sessions", get_codex_sessions_dir()),
        ("Cursor", get_cursor_dir()),
        ("Cursor state DB", get_cursor_state_db()),
        ("Antigravity IDE", get_antigravity_dir()),
    ]
    results = []
    for label, path in tools:
        exists = path.exists()
        status = "found" if exists else "NOT FOUND"
        results.append((exists, f"{label}: {path} ({status})"))
    return results


def _check_database():
    """Verify the SessionVault database is accessible and schema is valid."""
    db_path = get_db_path()
    results = []

    # 1. Does the database file exist?
    if not db_path.exists():
        results.append((False, f"Database file not found: {db_path}"))
        return results

    results.append((True, f"Database file exists: {db_path}"))

    # 2. Can we open it and run a basic query?
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        results.append((False, f"Cannot open database: {e}"))
        return results

    # 3. Check required tables exist
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    except sqlite3.Error as e:
        results.append((False, f"Cannot query sqlite_master: {e}"))
        conn.close()
        return results

    required_tables = {"conversations", "messages"}
    missing = required_tables - tables
    if missing:
        results.append((False, f"Missing tables: {', '.join(sorted(missing))}"))
    else:
        results.append((True, "Required tables present: conversations, messages"))

    # 4. Check FTS5 virtual table
    has_fts = "messages_fts" in tables
    if has_fts:
        results.append((True, "FTS5 virtual table messages_fts present"))
    else:
        results.append((False, "FTS5 virtual table messages_fts missing"))

    # 5. Quick record counts
    try:
        n_conv = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        n_msg = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        results.append((True, f"Records: {n_conv} conversations, {n_msg} messages"))
    except sqlite3.Error as e:
        results.append((False, f"Cannot count records: {e}"))

    # 6. Integrity check
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity == "ok":
            results.append((True, "Integrity check passed"))
        else:
            results.append((False, f"Integrity check failed: {integrity}"))
    except sqlite3.Error as e:
        results.append((False, f"Cannot run integrity check: {e}"))

    conn.close()
    return results


def _check_dependencies():
    """Check if optional dependencies are installed."""
    deps = [
        ("rich", "rich"),
        ("mcp", "mcp"),
        ("textual", "textual"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
    ]
    results = []
    for label, module_name in deps:
        try:
            mod = importlib.import_module(module_name)
            version = getattr(mod, "__version__", "unknown")
            results.append((True, f"{label} {version}"))
        except ImportError:
            results.append((False, f"{label} -- NOT INSTALLED"))
    return results


def cmd_doctor(args):
    """Run health checks and print a report."""
    try:
        from rich.console import Console
        from rich.table import Table
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False

    sections = [
        ("Tool Data Directories", _check_tool_dirs),
        ("Database", _check_database),
        ("Dependencies", _check_dependencies),
    ]

    all_ok = True

    if HAS_RICH:
        console = Console()
        console.print()

        for title, check_fn in sections:
            results = check_fn()
            table = Table(title=title, show_header=True, header_style="bold cyan")
            table.add_column("Status", justify="center", width=8)
            table.add_column("Detail")

            for ok, detail in results:
                icon = "[green]  OK  [/green]" if ok else "[red] FAIL [/red]"
                table.add_row(icon, detail)
                if not ok:
                    all_ok = False

            console.print(table)
            console.print()

        if all_ok:
            console.print("[bold green]All checks passed.[/bold green]")
        else:
            console.print("[bold yellow]Some checks failed. See details above.[/bold yellow]")
    else:
        # Plain output fallback
        for title, check_fn in sections:
            print(f"\n=== {title} ===")
            for ok, detail in check_fn():
                icon = "OK  " if ok else "FAIL"
                print(f"  [{icon}] {detail}")
                if not ok:
                    all_ok = False

        print()
        if all_ok:
            print("All checks passed.")
        else:
            print("Some checks failed. See details above.")

    sys.exit(0 if all_ok else 1)
