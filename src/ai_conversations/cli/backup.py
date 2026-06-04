"""Backup and restore subcommands for SessionVault database."""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from ..config import get_config

BACKUP_DIR_NAME = "sessionvault-backups"


def _get_backup_dir() -> Path:
    """Return the backup directory path."""
    return Path.home() / BACKUP_DIR_NAME


def _get_db_path() -> Path:
    """Return the path to the database file."""
    return get_config().db_path


def _timestamp() -> str:
    """Return a filesystem-safe timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def cmd_backup(args):
    """Create a timestamped backup of the database."""
    db_path = _get_db_path()
    backup_dir = _get_backup_dir()

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        print("Run 'sessionvault sync' to create it first.", file=sys.stderr)
        sys.exit(1)

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f"data_{_timestamp()}.db"

    try:
        shutil.copy2(str(db_path), str(backup_file))
    except OSError as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Backup created: {backup_file}")
    db_size = db_path.stat().st_size
    print(f"Database size: {db_size:,} bytes")


def cmd_restore(args):
    """Restore the database from a backup file."""
    backup_dir = _get_backup_dir()

    if not backup_dir.exists():
        print(f"Error: No backup directory found at {backup_dir}", file=sys.stderr)
        print("Create a backup first with: sessionvault backup", file=sys.stderr)
        sys.exit(1)

    if args.file:
        # Restore from a specific file
        backup_file = Path(args.file)
        if not backup_file.exists():
            print(f"Error: Backup file not found: {backup_file}", file=sys.stderr)
            sys.exit(1)
    else:
        # Restore from the latest backup
        backups = sorted(backup_dir.glob("data_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            print(f"Error: No backups found in {backup_dir}", file=sys.stderr)
            print("Create a backup first with: sessionvault backup", file=sys.stderr)
            sys.exit(1)
        backup_file = backups[0]

    db_path = _get_db_path()

    # Confirm unless --force
    if not args.force:
        print(f"Restoring from: {backup_file}")
        print(f"This will replace: {db_path}")
        try:
            answer = input("Continue? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if answer not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    try:
        shutil.copy2(str(backup_file), str(db_path))
    except OSError as e:
        print(f"Error restoring backup: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Restored from: {backup_file}")


def cmd_list_backups(args):
    """List available backups."""
    backup_dir = _get_backup_dir()

    if not backup_dir.exists():
        print(f"No backups found. Directory does not exist: {backup_dir}")
        print("Create a backup first with: sessionvault backup")
        return

    backups = sorted(backup_dir.glob("data_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not backups:
        print(f"No backups found in {backup_dir}")
        return

    print(f"Backups ({len(backups)}):\n")
    for i, backup in enumerate(backups):
        stat = backup.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        marker = " <-- latest" if i == 0 else ""
        print(f"  {backup.name:<30}  {mtime}  {size:>12,} bytes{marker}")
