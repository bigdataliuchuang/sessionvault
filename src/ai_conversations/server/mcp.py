"""MCP server for querying AI conversations from within Cursor/Claude Code."""

import json
from typing import Optional

from ..db import Database


def run_server():
    """Start the MCP server."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("MCP SDK not installed. Install with: pip install 'ai-conversations[mcp]'")
        return

    mcp = FastMCP("ai-conversations")
    db = Database()

    @mcp.tool()
    def search_conversations(
        query: str,
        tool: Optional[str] = None,
        project: Optional[str] = None,
        date_range: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """Search across all AI tool conversations.

        Args:
            query: Search keywords
            tool: Filter by tool (claude-code / codex / cursor)
            project: Filter by project name (partial match)
            date_range: Filter by date (e.g. '2026-06' or '2026-01-01:2026-06-01')
            role: Filter by role (user / assistant)
            limit: Max results (default 20)
        """
        results = db.search(
            query=query, tool=tool, project=project,
            date_range=date_range, role=role, limit=limit,
        )
        if not results:
            return json.dumps({"results": [], "total": 0}, ensure_ascii=False)

        output = []
        for r in results:
            output.append({
                "tool": r["tool"],
                "project": r["project"],
                "session_id": r["session_id"],
                "title": r.get("title", ""),
                "date": r["timestamp"][:10] if r["timestamp"] else "",
                "role": r["role"],
                "content": r["content"][:500],
            })
        return json.dumps({"results": output, "total": len(output)}, ensure_ascii=False)

    @mcp.tool()
    def list_sessions(
        tool: Optional[str] = None,
        project: Optional[str] = None,
        date_range: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """List conversation sessions.

        Args:
            tool: Filter by tool (claude-code / codex / cursor)
            project: Filter by project name (partial match)
            date_range: Filter by date range
            limit: Max results (default 50)
        """
        sessions = db.list_sessions(tool=tool, project=project, date_range=date_range, limit=limit)
        if not sessions:
            return json.dumps({"sessions": [], "total": 0}, ensure_ascii=False)

        output = []
        for s in sessions:
            output.append({
                "tool": s["tool"],
                "project": s["project"],
                "session_id": s["session_id"],
                "title": s.get("title", "untitled"),
                "date": s["started_at"][:10] if s["started_at"] else "",
                "message_count": s["message_count"],
            })
        return json.dumps({"sessions": output, "total": len(output)}, ensure_ascii=False)

    @mcp.tool()
    def get_session(session_id: str) -> str:
        """Get the full content of a specific conversation.

        Args:
            session_id: The session ID to retrieve
        """
        session = db.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Session not found: {session_id}"}, ensure_ascii=False)

        messages = []
        for msg in session.get("messages", []):
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"][:19] if msg["timestamp"] else "",
            })

        output = {
            "tool": session["tool"],
            "project": session["project"],
            "session_id": session["session_id"],
            "title": session.get("title", ""),
            "started_at": session["started_at"],
            "message_count": session["message_count"],
            "messages": messages,
        }
        return json.dumps(output, ensure_ascii=False)

    @mcp.tool()
    def list_projects(tool: Optional[str] = None) -> str:
        """List all projects with conversation counts.

        Args:
            tool: Filter by tool (claude-code / codex / cursor)
        """
        projects = db.list_projects(tool=tool)
        if not projects:
            return json.dumps({"projects": [], "total": 0}, ensure_ascii=False)

        output = []
        for p in projects:
            output.append({
                "tool": p["tool"],
                "project": p["project"],
                "session_count": p["session_count"],
            })
        return json.dumps({"projects": output, "total": len(output)}, ensure_ascii=False)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
