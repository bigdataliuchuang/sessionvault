"""Serve subcommand."""

import sys


def cmd_serve(args):
    """Start MCP server."""
    try:
        from ..server.mcp import run_server
        run_server()
    except ImportError:
        print("MCP support not installed. Install with: pip install 'sessionvault[mcp]'")
        sys.exit(1)
