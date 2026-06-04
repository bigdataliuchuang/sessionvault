"""Search, sessions, projects, stats, export subcommands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..db import Database


def cmd_search(args):
    """Search conversations."""
    db = Database()
    results = db.search(
        query=args.query,
        tool=args.tool,
        project=args.project,
        date_range=args.date,
        role=args.role,
        limit=args.limit,
    )
    db.close()

    if not results:
        print("No results found.")
        return

    for r in results:
        ts = r["timestamp"][:10] if r["timestamp"] else "?"
        content = r["content"][:120].replace("\n", " ")
        print(f"[{ts}] {r['tool']}")
        print(f"  Project: {r['project']}")
        if r["title"]:
            print(f"  Title: {r['title'][:80]}")
        print(f"  {r['role']}: {content}")
        print()


def cmd_sessions(args):
    """List conversation sessions."""
    db = Database()
    sessions = db.list_sessions(
        tool=args.tool,
        project=args.project,
        date_range=args.date,
        limit=args.limit,
    )
    db.close()

    if not sessions:
        print("No sessions found.")
        return

    for s in sessions:
        ts = s["started_at"][:10] if s["started_at"] else "?"
        title = (s["title"] or "untitled")[:60]
        print(f"[{ts}] {s['tool']}")
        print(f"  Project: {s['project']}")
        print(f"  {title} ({s['message_count']} msgs)")
        print()


def cmd_export(args):
    """Export a session as Markdown."""
    db = Database()
    session = db.get_session(args.session_id)
    db.close()

    if not session:
        print(f"Session not found: {args.session_id}")
        return

    if getattr(args, "obsidian", False):
        export_obsidian(session, output_dir=getattr(args, "output", None))
        return

    print("---")
    print(f"tool: {session['tool']}")
    print(f"project: {session['project']}")
    print(f"session_id: {session['session_id']}")
    print(f"started_at: {session['started_at']}")
    print(f"title: {session['title']}")
    print(f"message_count: {session['message_count']}")
    print("---")
    print()

    for msg in session.get("messages", []):
        ts = msg["timestamp"][:19] if msg["timestamp"] else ""
        print(f"## [{msg['role']}] {ts}")
        print(msg["content"])
        print()


def export_obsidian(session: dict, output_dir: str | None = None) -> Path:
    """Export a session to Obsidian-compatible markdown with YAML frontmatter.

    The generated file includes:
    - YAML frontmatter with tags (tool, project), dates, and session metadata.
    - A chronological message transcript formatted for readability.

    Args:
        session: Full session dict from Database.get_session().
        output_dir: Optional directory to write the file into.  When *None*
            the current working directory is used.

    Returns:
        The Path of the written file.
    """
    tool = session.get("tool", "unknown")
    project = session.get("project", "unknown")
    session_id = session.get("session_id", "unknown")
    title = session.get("title") or "untitled"
    started_at = session.get("started_at", "")
    ended_at = session.get("ended_at", "")
    message_count = session.get("message_count", 0)

    # Sanitise the title so it is a safe filename / Obsidian note name.
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
    safe_title = safe_title[:80] or "untitled"

    # Build a date prefix for the filename (YYYY-MM-DD).
    date_prefix = started_at[:10] if started_at else datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix} {safe_title}.md"

    dest = Path(output_dir) if output_dir else Path.cwd()
    dest.mkdir(parents=True, exist_ok=True)
    filepath = dest / filename

    # --- Build the markdown content ---
    lines: list[str] = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"title: \"{title}\"")
    lines.append(f"tool: {tool}")
    lines.append(f"project: \"{project}\"")
    lines.append(f"session_id: \"{session_id}\"")
    lines.append(f"started_at: \"{started_at}\"")
    if ended_at:
        lines.append(f"ended_at: \"{ended_at}\"")
    lines.append(f"message_count: {message_count}")
    lines.append("tags:")
    lines.append(f"  - {tool}")
    lines.append(f"  - conversation")
    lines.append(f"  - \"{project}\"")
    lines.append("---")
    lines.append("")

    # Header
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> Tool: **{tool}** | Project: **{project}** | Messages: **{message_count}**")
    if started_at:
        lines.append(f"> Started: {started_at}" + (f" | Ended: {ended_at}" if ended_at else ""))
    lines.append("")

    # Message transcript
    lines.append("---")
    lines.append("")
    for msg in session.get("messages", []):
        ts = msg["timestamp"][:19] if msg["timestamp"] else ""
        role = msg.get("role", "unknown")
        role_display = role.capitalize()
        lines.append(f"## {role_display}" + (f"  ({ts})" if ts else ""))
        lines.append("")
        lines.append(msg.get("content", ""))
        lines.append("")

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")

    print(f"Exported to Obsidian note: {filepath}")
    return filepath


def cmd_projects(args):
    """List all projects."""
    db = Database()
    projects = db.list_projects(tool=args.tool)
    db.close()

    if not projects:
        print("No projects found.")
        return

    for p in projects:
        print(f"  {p['tool']:15s} | {p['session_count']:4d} sessions | {p['project']}")


def cmd_stats(args):
    """Show statistics."""
    db = Database()
    stats = db.get_stats()
    db.close()

    print(f"Total conversations: {stats['total_conversations']}")
    print(f"Total messages: {stats['total_messages']}")
    print(f"\nBy tool:")
    for tool, count in stats["by_tool"].items():
        print(f"  {tool:15s}: {count} conversations")
