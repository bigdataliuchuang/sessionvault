"""Search, sessions, projects, stats, export subcommands."""

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
