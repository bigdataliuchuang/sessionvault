"""CLI entry point for sessionvault."""

import argparse
import sys

from ..logging import setup_logging
from .sync import cmd_sync
from .search import cmd_search, cmd_sessions, cmd_projects, cmd_stats, cmd_export
from .serve import cmd_serve


def cmd_tui(args):
    """Launch terminal UI."""
    from ..tui.app import run_tui
    run_tui()


def cmd_web(args):
    """Launch web UI."""
    from ..web.app import run_web
    run_web(host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        prog="sessionvault",
        description="Unified conversation manager for AI coding tools",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    subparsers = parser.add_subparsers(dest="command")

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync conversations from AI tools")
    p_sync.add_argument("--tool", default=None, help="Comma-separated tools to sync (default: all)")
    p_sync.add_argument("--since", default=None, help="Only sync sessions after this date (e.g. 7d, 2026-01-01)")
    p_sync.add_argument("--project", default=None, help="Only sync sessions from this project")
    p_sync.add_argument("--dry-run", action="store_true", help="Preview without writing")
    p_sync.set_defaults(func=cmd_sync)

    # search
    p_search = subparsers.add_parser("search", help="Search conversations")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--tool", default=None, help="Filter by tool")
    p_search.add_argument("--project", default=None, help="Filter by project")
    p_search.add_argument("--date", default=None, help="Filter by date range (e.g. 2026-06 or 2026-01-01:2026-06-01)")
    p_search.add_argument("--role", default=None, help="Filter by role (user/assistant)")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    p_search.set_defaults(func=cmd_search)

    # sessions
    p_sessions = subparsers.add_parser("sessions", help="List conversation sessions")
    p_sessions.add_argument("--tool", default=None, help="Filter by tool")
    p_sessions.add_argument("--project", default=None, help="Filter by project")
    p_sessions.add_argument("--date", default=None, help="Filter by date range")
    p_sessions.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")
    p_sessions.set_defaults(func=cmd_sessions)

    # export
    p_export = subparsers.add_parser("export", help="Export a session as Markdown")
    p_export.add_argument("session_id", help="Session ID to export")
    p_export.add_argument(
        "--obsidian",
        action="store_true",
        default=False,
        help="Export as Obsidian-compatible markdown with YAML frontmatter",
    )
    p_export.add_argument(
        "--output",
        default=None,
        help="Output directory for Obsidian export (default: current directory)",
    )
    p_export.set_defaults(func=cmd_export)

    # projects
    p_projects = subparsers.add_parser("projects", help="List all projects")
    p_projects.add_argument("--tool", default=None, help="Filter by tool")
    p_projects.set_defaults(func=cmd_projects)

    # stats
    p_stats = subparsers.add_parser("stats", help="Show statistics")
    p_stats.set_defaults(func=cmd_stats)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start MCP server")
    p_serve.set_defaults(func=cmd_serve)

    # tui
    p_tui = subparsers.add_parser("tui", help="Launch terminal UI")
    p_tui.set_defaults(func=cmd_tui)

    # web
    p_web = subparsers.add_parser("web", help="Launch web UI")
    p_web.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    p_web.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
