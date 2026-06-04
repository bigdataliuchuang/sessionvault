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
        .tabs { display: flex; gap: 5px; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .tab { padding: 8px 16px; border: 1px solid #30363d; border-radius: 6px 6px 0 0; background: #161b22; color: #8b949e; cursor: pointer; font-size: 13px; border-bottom: none; }
        .tab:hover { color: #c9d1d9; }
        .tab.active { background: #0d1117; color: #58a6ff; border-bottom: 2px solid #58a6ff; }
        .sort-btn { padding: 8px 16px; border: 1px solid #30363d; border-radius: 6px; background: #161b22; color: #8b949e; cursor: pointer; font-size: 13px; margin-left: auto; }
        .sort-btn:hover { color: #c9d1d9; border-color: #58a6ff; }
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
        /* Charts */
        .charts-section { display: none; margin-bottom: 20px; }
        .charts-section.active { display: block; }
        .charts-toggle { padding: 8px 16px; border: 1px solid #30363d; border-radius: 6px; background: #161b22; color: #8b949e; cursor: pointer; font-size: 13px; margin-bottom: 15px; }
        .charts-toggle:hover { color: #c9d1d9; border-color: #58a6ff; }
        .charts-toggle.active { color: #58a6ff; border-color: #58a6ff; }
        .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        @media (max-width: 768px) { .chart-grid { grid-template-columns: 1fr; } }
        .chart-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
        .chart-card h3 { color: #58a6ff; font-size: 14px; margin-bottom: 15px; }
        /* Horizontal bar chart */
        .hbar { display: flex; flex-direction: column; gap: 8px; }
        .hbar-row { display: flex; align-items: center; gap: 10px; }
        .hbar-label { width: 110px; font-size: 12px; color: #8b949e; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .hbar-track { flex: 1; height: 22px; background: #21262d; border-radius: 4px; overflow: hidden; position: relative; }
        .hbar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; display: flex; align-items: center; padding-left: 8px; font-size: 11px; font-weight: bold; color: #fff; min-width: 30px; }
        .hbar-fill.tool-claude-code { background: #1f6feb; }
        .hbar-fill.tool-codex { background: #238636; }
        .hbar-fill.tool-cursor { background: #da3633; }
        .hbar-fill.tool-default { background: #8b949e; }
        /* Vertical bar chart */
        .vbar { display: flex; align-items: flex-end; gap: 2px; height: 140px; padding-top: 10px; }
        .vbar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; position: relative; }
        .vbar-bar { width: 100%; max-width: 30px; border-radius: 3px 3px 0 0; transition: height 0.6s ease; position: relative; }
        .vbar-bar:hover { opacity: 0.85; }
        .vbar-bar .tooltip { display: none; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: #30363d; color: #c9d1d9; padding: 4px 8px; border-radius: 4px; font-size: 11px; white-space: nowrap; z-index: 10; }
        .vbar-bar:hover .tooltip { display: block; }
        .vbar-date { font-size: 10px; color: #8b949e; margin-top: 6px; writing-mode: vertical-lr; text-orientation: mixed; max-height: 70px; overflow: hidden; }
        .vbar-empty { color: #8b949e; font-size: 13px; text-align: center; padding: 40px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 SessionVault</h1>
        <div class="stats" id="stats"></div>
        <button class="charts-toggle" onclick="toggleCharts()" id="charts-toggle">📊 统计图表</button>
        <div class="charts-section" id="charts-section">
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>对话数 / 工具</h3>
                    <div class="hbar" id="chart-tool-bar"></div>
                </div>
                <div class="chart-card">
                    <h3>每日对话趋势</h3>
                    <div id="chart-daily-conv"></div>
                </div>
                <div class="chart-card" style="grid-column: 1 / -1;">
                    <h3>每日消息趋势</h3>
                    <div id="chart-daily-msg"></div>
                </div>
            </div>
        </div>
        <div class="search-bar">
            <input type="text" id="search" placeholder="搜索对话..." autofocus>
            <button onclick="search()">搜索</button>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="switchTab('all', this)">全部</button>
            <button class="tab" onclick="switchTab('claude-code', this)">🔵 Claude Code</button>
            <button class="tab" onclick="switchTab('codex', this)">🟢 Codex</button>
            <button class="tab" onclick="switchTab('cursor', this)">🔴 Cursor</button>
            <button class="sort-btn" onclick="toggleSort()" id="sort-btn">⬇ 最新在前</button>
        </div>
        <div id="tab-content">
            <ul class="results" id="results-all"></ul>
            <ul class="results" id="results-claude-code" style="display:none"></ul>
            <ul class="results" id="results-codex" style="display:none"></ul>
            <ul class="results" id="results-cursor" style="display:none"></ul>
        </div>
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
        let currentTab = 'all';
        let sortAsc = false; // false = newest first (desc), true = oldest first (asc)
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat"><div class="stat-value">${data.total_conversations}</div><div class="stat-label">会话数</div></div>
                <div class="stat"><div class="stat-value">${data.total_messages}</div><div class="stat-label">消息数</div></div>
                ${Object.entries(data.by_tool).map(([t,c]) => `<div class="stat"><div class="stat-value">${c}</div><div class="stat-label">${t}</div></div>`).join('')}
            `;
        }
        function switchTab(tool, btn) {
            currentTab = tool;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            // Hide all, show selected
            document.querySelectorAll('.results').forEach(el => el.style.display = 'none');
            document.getElementById('results-' + tool).style.display = 'block';
            // Load data for this tab
            loadToolSessions(tool);
        }
        async function loadToolSessions(tool) {
            const url = tool === 'all' ? '/api/sessions?limit=50' : `/api/sessions?tool=${tool}&limit=50`;
            const res = await fetch(url);
            const data = await res.json();
            let sessions = (data.sessions || []).map(s => ({...s, content: '', role: ''}));
            // Sort by date
            sessions.sort((a, b) => {
                const da = a.date || a.started_at || '';
                const db = b.date || b.started_at || '';
                return sortAsc ? da.localeCompare(db) : db.localeCompare(da);
            });
            renderToolResults(tool, sessions);
        }
        function toggleSort() {
            sortAsc = !sortAsc;
            const btn = document.getElementById('sort-btn');
            btn.textContent = sortAsc ? '⬆ 最旧在前' : '⬇ 最新在前';
            loadToolSessions(currentTab);
        }
        function renderToolResults(tool, results) {
            const el = document.getElementById('results-' + tool);
            el.innerHTML = results.map(r => `
                <li class="result-item" onclick="showDetail('${r.session_id || r.id}')">
                    <div class="result-header">
                        <span class="result-tool tool-${r.tool}">${r.tool}</span>
                        <span class="result-date">${r.date || r.started_at?.slice(0,10) || ''}</span>
                    </div>
                    <div class="result-title">${r.title || 'untitled'}</div>
                    <div class="result-project">📁 ${r.project}</div>
                </li>
            `).join('');
        }
        async function search() {
            const query = document.getElementById('search').value;
            if (!query) { loadToolSessions(currentTab); return; }
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&tool=${currentTab === 'all' ? '' : currentTab}&limit=30`);
            const data = await res.json();
            const results = (data.results || []).map(r => ({...r, session_id: r.session_id}));
            renderToolResults(currentTab, results);
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
        loadStats(); loadToolSessions('all');

        let chartsVisible = false;
        let chartsLoaded = false;
        function toggleCharts() {
            chartsVisible = !chartsVisible;
            const section = document.getElementById('charts-section');
            const btn = document.getElementById('charts-toggle');
            section.classList.toggle('active', chartsVisible);
            btn.classList.toggle('active', chartsVisible);
            if (chartsVisible && !chartsLoaded) loadExtendedStats();
        }
        async function loadExtendedStats() {
            const res = await fetch('/api/stats/extended');
            const data = await res.json();
            renderToolBar(data.by_tool || {});
            renderDailyChart('chart-daily-conv', data.daily_conversations || [], 'date', 'count');
            renderDailyChart('chart-daily-msg', data.daily_messages || [], 'date', 'count');
            chartsLoaded = true;
        }
        function renderToolBar(byTool) {
            const el = document.getElementById('chart-tool-bar');
            const entries = Object.entries(byTool);
            if (!entries.length) { el.innerHTML = '<div class="vbar-empty">No data</div>'; return; }
            const max = Math.max(...entries.map(e => e[1]));
            const toolColors = {'claude-code': 'tool-claude-code', 'codex': 'tool-codex', 'cursor': 'tool-cursor'};
            el.innerHTML = entries.map(([tool, count]) => {
                const pct = max > 0 ? (count / max * 100) : 0;
                const cls = toolColors[tool] || 'tool-default';
                return `<div class="hbar-row">
                    <span class="hbar-label" title="${tool}">${tool}</span>
                    <div class="hbar-track"><div class="hbar-fill ${cls}" style="width:${Math.max(pct, 5)}%">${count}</div></div>
                </div>`;
            }).join('');
        }
        function renderDailyChart(elId, items, dateKey, countKey) {
            const el = document.getElementById(elId);
            if (!items.length) { el.innerHTML = '<div class="vbar-empty">No data</div>'; return; }
            // Show last 30 days max
            const data = items.slice(-30);
            const max = Math.max(...data.map(d => d[countKey]));
            const barColor = elId.includes('conv') ? '#58a6ff' : '#3fb950';
            // Limit visible labels to avoid clutter
            const skipFactor = data.length > 15 ? Math.ceil(data.length / 12) : 1;
            el.innerHTML = '<div class="vbar">' + data.map((d, i) => {
                const pct = max > 0 ? (d[countKey] / max * 100) : 0;
                const dateLabel = (d[dateKey] || '').slice(5); // MM-DD
                const showDate = i % skipFactor === 0 || i === data.length - 1;
                return `<div class="vbar-col">
                    <div class="vbar-bar" style="height:${Math.max(pct, 2)}%;background:${barColor}">
                        <span class="tooltip">${d[dateKey]}: ${d[countKey]}</span>
                    </div>
                    ${showDate ? `<span class="vbar-date">${dateLabel}</span>` : ''}
                </div>`;
            }).join('') + '</div>';
        }
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

    @app.get("/api/stats/extended")
    async def stats_extended():
        db = Database()
        result = db.get_extended_stats()
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
