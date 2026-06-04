"""Sync subcommand."""

import logging
import sys

from ..db import Database
from ..extractors import EXTRACTORS

logger = logging.getLogger("ai_conversations")


def cmd_sync(args):
    """Sync conversations from AI tools to local database."""
    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.table import Table
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False

    db = Database()
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
                    console.print(f"  [red]Error: {e}[/red]")
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
                logger.error(f"Error syncing {tool_name}: {e}")
                errors += 1
                continue

            logger.info(f"  -> {count} new, {skipped} skipped")
            total += count

        db.close()

        if errors:
            logger.warning(f"Done with {errors} error(s). {total} conversations synced.")
        else:
            logger.info(f"Done. {total} conversations synced.")

    db.close()
