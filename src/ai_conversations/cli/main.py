"""CLI entry point for sessionvault."""

import argparse
import sys

from .. import __version__
from ..logging import setup_logging
from .sync import cmd_sync
from .search import cmd_search, cmd_sessions, cmd_projects, cmd_stats, cmd_export
from .serve import cmd_serve
from .doctor import cmd_doctor
from .backup import cmd_backup, cmd_restore, cmd_list_backups

HELP_TEXT = """\
SessionVault - Unified conversation manager for AI coding tools

Usage:
  sessionvault <command> [options]

Available Commands:
  sync        Sync conversations from AI tools
  search      Search conversations by keyword, tool, project, or date
  sessions    List conversation sessions
  projects    List all projects
  doctor      Check health of tool directories, database, and dependencies
  stats       Show statistics
  export      Export a session as Markdown
  backup      Backup database to ~/sessionvault-backups/
  restore     Restore database from a backup
  list        List available backups
  serve       Start MCP server
  tui         Launch terminal UI
  web         Launch web UI
  help        Show this help message

Examples:
  sessionvault sync                              # Sync all tools
  sessionvault sync --tool cursor --since 7d     # Sync Cursor sessions from last 7 days
  sessionvault search "authentication"           # Search for authentication-related conversations
  sessionvault search "auth" --tool codex        # Search only in Codex sessions
  sessionvault sessions --project my-app         # List sessions for a specific project
  sessionvault projects --tool cursor            # List projects with Cursor sessions
  sessionvault doctor                            # Check health of installation
  sessionvault stats                             # Show overall statistics
  sessionvault export abc123                     # Export session as Markdown
  sessionvault export abc123 --format json       # Export session as JSON
  sessionvault export abc123 --format csv        # Export session as CSV
  sessionvault export abc123 --obsidian          # Export as Obsidian-compatible Markdown
  sessionvault backup                            # Backup database to ~/sessionvault-backups/
  sessionvault restore                           # Restore latest backup
  sessionvault list                              # List available backups
  sessionvault serve                             # Start the MCP server
  sessionvault tui                               # Launch terminal UI
  sessionvault web --port 9090                   # Launch web UI on port 9090

Options:
  -v, --verbose    Enable debug logging
  -h, --help       Show help message
  --version        Show version information
"""


def cmd_tui(args):
    """Launch terminal UI."""
    from ..tui.app import run_tui
    run_tui()


def cmd_web(args):
    """Launch web UI."""
    from ..web.app import run_web
    run_web(host=args.host, port=args.port)


def cmd_help(args):
    """Show help with available commands and examples."""
    print(HELP_TEXT)


def main():
    parser = argparse.ArgumentParser(
        prog="sessionvault",
        description="Unified conversation manager for AI coding tools",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
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
    p_export = subparsers.add_parser("export", help="Export a session as Markdown, JSON, or CSV")
    p_export.add_argument("session_id", help="Session ID to export")
    p_export.add_argument(
        "--format",
        choices=["markdown", "json", "csv"],
        default=None,
        help="Output format: markdown (default), json, or csv",
    )
    p_export.add_argument(
        "--obsidian",
        action="store_true",
        default=False,
        help="Export as Obsidian-compatible markdown with YAML frontmatter",
    )
    p_export.add_argument(
        "--output",
        default=None,
        help="Output directory or file path for export (default: stdout, or current directory for --obsidian)",
    )
    p_export.set_defaults(func=cmd_export)

    # projects
    p_projects = subparsers.add_parser("projects", help="List all projects")
    p_projects.add_argument("--tool", default=None, help="Filter by tool")
    p_projects.set_defaults(func=cmd_projects)

    # stats
    p_stats = subparsers.add_parser("stats", help="Show statistics")
    p_stats.set_defaults(func=cmd_stats)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check health of tool directories, database, and dependencies")
    p_doctor.set_defaults(func=cmd_doctor)

    # backup
    p_backup = subparsers.add_parser("backup", help="Backup database to ~/sessionvault-backups/")
    p_backup.set_defaults(func=cmd_backup)

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore database from a backup")
    p_restore.add_argument("file", nargs="?", default=None, help="Specific backup file to restore from (default: latest)")
    p_restore.add_argument("-f", "--force", action="store_true", help="Restore without confirmation prompt")
    p_restore.set_defaults(func=cmd_restore)

    # list
    p_list = subparsers.add_parser("list", help="List available backups")
    p_list.set_defaults(func=cmd_list_backups)

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

    # help
    p_help = subparsers.add_parser("help", help="Show help with available commands and examples")
    p_help.set_defaults(func=cmd_help)

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)
