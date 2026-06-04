"""Web UI for SessionVault using FastAPI."""

import json
from pathlib import Path

from ..db import Database

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SessionVault</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 20px; }
        .search-bar { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-bar input { flex: 1; padding: 10px 15px; border: 1px solid #30363d; border-radius: 6px; background: #161b22; color: #c9d1d9; font-size: 14px; }
        .search-bar button { padding: 10px 20px; border: none; border-radius: 6px; background: #238636; color: white; cursor: pointer; font-size: 14px; }
        .search-bar button:hover { background: #2ea043; }
        .filters { display: flex; gap: 10px; margin-bottom: 20px; }
        .filters select { padding: 8px 12px; border: 1px solid #30363d; border-radius: 6px; background: #161b22; color: #c9d1d9; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; padding: 15px; background: #161b22; border-radius: 6px; border: 1px solid #30363d; }
        .stat { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #58a6ff; }
        .stat-label { font-size: 12px; color: #8b949e; }
        .results { list-style: none; }
        .result-item { padding: 15px; margin-bottom: 10px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; cursor: pointer; }
        .result-item:hover { border-color: #58a6ff; }
        .result-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .result-tool { padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .tool-claude-code { background: #1f6feb33; color: #58a6ff; }
        .tool-codex { background: #23863633; color: #3fb950; }
        .tool-cursor { background: #da363333; color: #f85149; }
        .result-date { color: #8b949e; font-size: 12px; }
        .result-title { font-weight: 500; margin-bottom: 5px; }
        .result-project { color: #8b949e; font-size: 12px; }
        .result-preview { color: #8b949e; font-size: 13px; margin-top: 8px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; max-width: 800px; max-height: 80vh; overflow-y: auto; width: 90%; }
        .modal-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .modal-close { background: none; border: none; color: #8b949e; cursor: pointer; font-size: 20px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 6px; }
        .message-user { background: #1f6feb22; border-left: 3px solid #58a6ff; }
        .message-assistant { background: #23863622; border-left: 3px solid #3fb950; }
        .message-role { font-weight: bold; font-size: 12px; margin-bottom: 5px; }
        .message-content { white-space: pre-wrap; font-size: 13px; }
        .export-btn { margin-top: 15px; padding: 8px 16px; border: 1px solid #30363d; border-radius: 6px; background: #21262d; color: #c9d1d9; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 SessionVault</h1>
        <div class="stats" id="stats"></div>
        <div class="search-bar">
            <input type="text" id="search" placeholder="搜索对话..." autofocus>
            <button onclick="search()">搜索</button>
        </div>
        <div class="filters">
            <select id="tool-filter" onchange="filterChanged()">
                <option value="">所有工具</option>
                <option value="claude-code">Claude Code</option>
                <option value="codex">Codex</option>
                <option value="cursor">Cursor</option>
            </select>
            <select id="date-filter" onchange="filterChanged()">
                <option value="">所有时间</option>
                <option value="7d">最近 7 天</option>
                <option value="30d">最近 30 天</option>
                <option value="90d">最近 90 天</option>
            </select>
        </div>
        <ul class="results" id="results"></ul>
    </div>
    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title"></h2>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div id="modal-body"></div>
            <button class="export-btn" onclick="exportSession()">导出 Markdown</button>
        </div>
    </div>
    <script>
        let currentSessionId = '';
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat"><div class="stat-value">${data.total_conversations}</div><div class="stat-label">会话数</div></div>
                <div class="stat"><div class="stat-value">${data.total_messages}</div><div class="stat-label">消息数</div></div>
                ${Object.entries(data.by_tool).map(([t,c]) => `<div class="stat"><div class="stat-value">${c}</div><div class="stat-label">${t}</div></div>`).join('')}
            `;
        }
        async function search() {
            const query = document.getElementById('search').value;
            const tool = document.getElementById('tool-filter').value;
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&tool=${tool}&limit=30`);
            const data = await res.json();
            renderResults(data.results || []);
        }
        async function filterChanged() { await search(); }
        async function loadSessions() {
            const tool = document.getElementById('tool-filter').value;
            const res = await fetch(`/api/sessions?tool=${tool}&limit=30`);
            const data = await res.json();
            renderResults((data.sessions || []).map(s => ({...s, content: '', role: ''})));
        }
        function renderResults(results) {
            const el = document.getElementById('results');
            el.innerHTML = results.map(r => `
                <li class="result-item" onclick="showDetail('${r.session_id || r.id}')">
                    <div class="result-header">
                        <span class="result-tool tool-${r.tool}">${r.tool}</span>
                        <span class="result-date">${r.date || r.started_at?.slice(0,10) || ''}</span>
                    </div>
                    <div class="result-title">${r.title || 'untitled'}</div>
                    <div class="result-project">📁 ${r.project}</div>
                    ${r.content ? `<div class="result-preview">${r.content.slice(0,150)}...</div>` : ''}
                </li>
            `).join('');
        }
        async function showDetail(sessionId) {
            currentSessionId = sessionId;
            const res = await fetch(`/api/session/${sessionId}`);
            const data = await res.json();
            document.getElementById('modal-title').textContent = data.title || 'Untitled';
            document.getElementById('modal-body').innerHTML = `
                <p><strong>Tool:</strong> ${data.tool} | <strong>Project:</strong> ${data.project}</p>
                <p><strong>Started:</strong> ${data.started_at} | <strong>Messages:</strong> ${data.message_count}</p>
                <hr style="border-color:#30363d;margin:15px 0">
                ${(data.messages || []).map(m => `
                    <div class="message message-${m.role}">
                        <div class="message-role">${m.role} ${m.timestamp ? '· ' + m.timestamp : ''}</div>
                        <div class="message-content">${m.content}</div>
                    </div>
                `).join('')}
            `;
            document.getElementById('modal').classList.add('active');
        }
        function closeModal() { document.getElementById('modal').classList.remove('active'); }
        async function exportSession() {
            if (!currentSessionId) return;
            const res = await fetch(`/api/export/${currentSessionId}`);
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `session-${currentSessionId.slice(0,8)}.md`;
            a.click();
        }
        document.getElementById('search').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });
        loadStats(); loadSessions();
    </script>
</body>
</html>"""


def create_app():
    """Create the FastAPI web application."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, Response
    except ImportError:
        print("Web support not installed. Install with: pip install 'sessionvault[web]'")
        return None

    app = FastAPI(title="SessionVault")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML_TEMPLATE

    @app.get("/api/stats")
    async def stats():
        db = Database()
        result = db.get_stats()
        db.close()
        return result

    @app.get("/api/search")
    async def search(q: str, tool: str = "", limit: int = 20):
        db = Database()
        results = db.search(query=q, tool=tool or None, limit=limit)
        db.close()
        return {"results": results}

    @app.get("/api/sessions")
    async def sessions(tool: str = "", limit: int = 30):
        db = Database()
        result = db.list_sessions(tool=tool or None, limit=limit)
        db.close()
        return {"sessions": result}

    @app.get("/api/session/{session_id}")
    async def session(session_id: str):
        db = Database()
        result = db.get_session(session_id)
        db.close()
        if not result:
            return {"error": "not found"}
        return result

    @app.get("/api/export/{session_id}")
    async def export(session_id: str):
        db = Database()
        session = db.get_session(session_id)
        db.close()
        if not session:
            return Response("Not found", status_code=404)
        lines = [f"# {session['title']}\n"]
        lines.append(f"Tool: {session['tool']} | Project: {session['project']}\n")
        for msg in session.get("messages", []):
            ts = msg["timestamp"][:19] if msg["timestamp"] else ""
            lines.append(f"## [{msg['role']}] {ts}\n")
            lines.append(f"{msg['content']}\n")
        content = "\n".join(lines)
        return Response(
            content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=session-{session_id[:8]}.md"},
        )

    return app


def run_web(host: str = "127.0.0.1", port: int = 8080):
    """Launch the web server."""
    import uvicorn
    app = create_app()
    if app is None:
        import sys
        sys.exit(1)
    print(f"SessionVault Web UI running at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web()
