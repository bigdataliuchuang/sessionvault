"""Sync subcommand."""

import logging
import sqlite3
import sys

from ..db import Database
from ..extractors import EXTRACTORS

logger = logging.getLogger("ai_conversations")


def _classify_error(tool_name, error):
    """Classify an exception into a user-friendly (message, hint, severity) tuple.

    Returns:
        (message, hint, severity) where severity is one of 'error', 'warning'.
    """
    if isinstance(error, FileNotFoundError):
        return (
            f"Data directory not found for {tool_name}",
            "Is the tool installed? You may need to run it at least once to create its data directory.",
            "error",
        )
    if isinstance(error, PermissionError):
        return (
            f"Permission denied reading {tool_name} data",
            "Check file permissions. You may need to adjust access with: chmod -R u+rw <tool_data_dir>",
            "error",
        )
    if isinstance(error, sqlite3.OperationalError) and "locked" in str(error):
        return (
            "Database is locked",
            "Another SessionVault process may be running. Close other instances or wait a moment and retry.",
            "error",
        )
    # Default: preserve the original error message
    return (
        f"Error syncing {tool_name}",
        str(error),
        "error",
    )


def cmd_sync(args):
    """Sync conversations from AI tools to local database."""
    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.table import Table
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False

    try:
        db = Database()
    except PermissionError as e:
        msg = f"Permission denied opening database: {e}"
        hint = "Check file permissions on ~/.sessionvault/data.db. You may need to adjust access."
        if HAS_RICH:
            console = Console()
            console.print(f"\n  [bold red]Permission denied[/bold red] opening database")
            console.print(f"  [dim]{msg}[/dim]")
            console.print(f"  [dim italic]{hint}[/dim italic]\n")
        else:
            logger.error(msg)
            logger.info(hint)
        sys.exit(1)
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            msg = "Database is locked"
            hint = "Another SessionVault process may be running. Close other instances or wait a moment and retry."
        else:
            msg = f"Database error: {e}"
            hint = "The database may be corrupt. Try deleting ~/.sessionvault/data.db and re-syncing."
        if HAS_RICH:
            console = Console()
            console.print(f"\n  [bold red]{msg}[/bold red]")
            console.print(f"  [dim italic]{hint}[/dim italic]\n")
        else:
            logger.error(msg)
            logger.info(hint)
        sys.exit(1)
    except OSError as e:
        msg = f"Cannot open database: {e}"
        hint = "Ensure ~/.sessionvault/ directory is accessible."
        if HAS_RICH:
            console = Console()
            console.print(f"\n  [bold red]Database error[/bold red]")
            console.print(f"  [dim]{msg}[/dim]")
            console.print(f"  [dim italic]{hint}[/dim italic]\n")
        else:
            logger.error(msg)
            logger.info(hint)
        sys.exit(1)

    tool_filter = [t.strip() for t in args.tool.split(",")] if args.tool else list(EXTRACTORS.keys())

    if HAS_RICH:
        console = Console()
        console.print()
        table = Table(title="SessionVault Sync", show_header=True, header_style="bold cyan")
        table.add_column("Tool", style="bold")
        table.add_column("Status", justify="right")
        table.add_column("New", justify="right", style="green")
        table.add_column("Skipped", justify="right", style="yellow")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            total = 0
            errors = 0
            for tool_name in tool_filter:
                if tool_name not in EXTRACTORS:
                    continue

                task = progress.add_task(f"Syncing {tool_name}...", total=None)
                extractor = EXTRACTORS[tool_name]()

                count = 0
                skipped = 0
                try:
                    for conv in extractor.extract(since=args.since, project=args.project):
                        file_mtime = getattr(conv, 'file_mtime', None)
                        if file_mtime and not db.needs_sync(conv.tool, conv.session_id, file_mtime):
                            skipped += 1
                            continue

                        if not args.dry_run:
                            db.save_conversation(conv)
                        count += 1
                        progress.update(task, advance=1, description=f"{tool_name}: {count} saved")
                except Exception as e:
                    msg, hint, _ = _classify_error(tool_name, e)
                    console.print(f"  [red]{msg}[/red]")
                    console.print(f"  [dim italic]{hint}[/dim italic]")
                    errors += 1
                    continue

                progress.update(task, completed=True, description=f"{tool_name}: done")
                table.add_row(tool_name, "✓" if not args.dry_run else "dry-run", str(count), str(skipped))
                total += count

        console.print()
        console.print(table)
        console.print()
        if errors:
            console.print(f"[yellow]Done with {errors} error(s). {total} conversations synced.[/yellow]")
        else:
            console.print(f"[green]Done. {total} conversations synced.[/green]")

        if total > 0 and not args.dry_run:
            db.increment_sync_stats()
    else:
        # Fallback without rich
        total = 0
        errors = 0
        for tool_name in tool_filter:
            if tool_name not in EXTRACTORS:
                logger.warning(f"Unknown tool: {tool_name}")
                continue

            logger.info(f"Syncing {tool_name}...")
            extractor = EXTRACTORS[tool_name]()

            count = 0
            skipped = 0
            try:
                for conv in extractor.extract(since=args.since, project=args.project):
                    file_mtime = getattr(conv, 'file_mtime', None)
                    if file_mtime and not db.needs_sync(conv.tool, conv.session_id, file_mtime):
                        skipped += 1
                        continue

                    if args.dry_run:
                        logger.info(f"  [dry-run] Would save: {conv.title[:60]} ({conv.message_count} msgs)")
                    else:
                        db.save_conversation(conv)
                    count += 1
            except Exception as e:
                msg, hint, _ = _classify_error(tool_name, e)
                logger.error(msg)
                logger.info(hint)
                errors += 1
                continue

            logger.info(f"  -> {count} new, {skipped} skipped")
            total += count

        db.close()

        if errors:
            logger.warning(f"Done with {errors} error(s). {total} conversations synced.")
        else:
            logger.info(f"Done. {total} conversations synced.")

        if total > 0 and not args.dry_run:
            db.increment_sync_stats()

    db.close()
