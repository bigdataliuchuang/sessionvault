"""Sync subcommand."""

import logging
import sys

from ..db import Database
from ..extractors import EXTRACTORS

logger = logging.getLogger("ai_conversations")


def cmd_sync(args):
    """Sync conversations from AI tools to local database."""
    db = Database()
    tool_filter = [t.strip() for t in args.tool.split(",")] if args.tool else list(EXTRACTORS.keys())

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
