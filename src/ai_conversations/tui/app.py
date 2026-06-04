"""Terminal UI for SessionVault using Textual."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Label, Static

from ..db import Database


class SessionVaultTUI(App):
    """Terminal UI for browsing and searching AI conversations."""

    TITLE = "SessionVault"
    SUB_TITLE = "AI Conversation Manager"
    CSS_PATH = "style.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "focus_search", "Search", show=True),
        Binding("p", "show_projects", "Projects", show=True),
        Binding("e", "export", "Export", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_results = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-container"):
            yield Input(placeholder="Search conversations...", id="search-input")
            yield Label("Tool: all | Project: all", id="filters")
            yield DataTable(id="results-table")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Date", "Tool", "Project", "Title", "Msgs")
        table.cursor_type = "row"
        # Load initial data
        self.load_sessions()

    def load_sessions(self, tool=None, project=None, limit=50):
        sessions = self.db.list_sessions(tool=tool, project=project, limit=limit)
        self.current_results = sessions
        table = self.query_one("#results-table", DataTable)
        table.clear()
        for s in sessions:
            ts = s["started_at"][:10] if s["started_at"] else "?"
            title = (s["title"] or "untitled")[:50]
            table.add_row(ts, s["tool"], s["project"].split("/")[-1], title, str(s["message_count"]))

    def on_input_changed(self, event: Input.Changed):
        query = event.value.strip()
        if not query:
            self.load_sessions()
            return
        results = self.db.search(query=query, limit=30)
        self.current_results = results
        table = self.query_one("#results-table", DataTable)
        table.clear()
        for r in results:
            ts = r["timestamp"][:10] if r["timestamp"] else "?"
            title = (r.get("title", "") or "untitled")[:50]
            content = r["content"][:60].replace("\n", " ")
            table.add_row(ts, r["tool"], r["project"].split("/")[-1], content, "1")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.row_index < len(self.current_results):
            item = self.current_results[event.row_index]
            session_id = item.get("session_id", item.get("id", ""))
            if session_id:
                self.show_detail(session_id)

    def show_detail(self, session_id: str):
        session = self.db.get_session(session_id)
        if not session:
            return
        # Build detail text
        lines = [
            f"Tool: {session['tool']}",
            f"Project: {session['project']}",
            f"Title: {session['title']}",
            f"Started: {session['started_at']}",
            f"Messages: {session['message_count']}",
            "",
        ]
        for msg in session.get("messages", [])[:50]:  # Limit to 50 messages
            ts = msg["timestamp"][:19] if msg["timestamp"] else ""
            lines.append(f"[{msg['role']}] {ts}")
            lines.append(msg["content"][:500])
            lines.append("")
        text = "\n".join(lines)
        # Show in a popup or new screen
        self.push_screen(DetailScreen(text, session_id))

    def action_focus_search(self):
        self.query_one("#search-input").focus()

    def action_show_projects(self):
        projects = self.db.list_projects()
        lines = [f"{p['tool']:15s} | {p['session_count']:4d} | {p['project']}" for p in projects]
        self.push_screen(DetailScreen("\n".join(lines), ""))

    def action_export(self):
        # Export current results to markdown
        if not self.current_results:
            return
        lines = ["# SessionVault Export\n"]
        for item in self.current_results[:20]:
            session_id = item.get("session_id", item.get("id", ""))
            session = self.db.get_session(session_id)
            if session:
                lines.append(f"## {session['title']}")
                lines.append(f"Tool: {session['tool']} | Project: {session['project']}")
                lines.append("")
                for msg in session.get("messages", [])[:20]:
                    lines.append(f"**[{msg['role']}]** {msg['content'][:200]}")
                    lines.append("")
        text = "\n".join(lines)
        # Save to file
        from pathlib import Path
        export_path = Path.home() / ".sessionvault" / "export.md"
        export_path.write_text(text, encoding="utf-8")
        self.notify(f"Exported to {export_path}")


class DetailScreen(Static):
    """Simple detail view screen."""

    def __init__(self, text: str, session_id: str):
        super().__init__(text)
        self.session_id = session_id


def run_tui():
    """Launch the TUI."""
    try:
        app = SessionVaultTUI()
        app.run()
    except ImportError:
        print("TUI support not installed. Install with: pip install 'sessionvault[tui]'")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    run_tui()
