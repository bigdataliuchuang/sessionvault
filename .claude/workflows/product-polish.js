export const meta = {
  name: 'sessionvault-product-polish',
  description: 'Complete product polish: version, help, error handling, backup, export, performance, plugin system, API, monitoring',
  phases: [
    { title: 'CLI', detail: 'Version, help, error handling' },
    { title: 'Data', detail: 'Backup, export, encryption' },
    { title: 'Performance', detail: 'Cursor optimization, caching' },
    { title: 'Extensibility', detail: 'Plugin system, API, webhooks' },
    { title: 'Operations', detail: 'Statistics, error reporting, auto-update' },
  ],
};

// Phase 1: CLI improvements
phase('CLI');
const cli = await parallel([
  () => agent('Add --version flag to SessionVault CLI. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/main.py, add --version argument that prints version from __init__.py. Also add a help command that shows available commands and examples.', {label: 'version-help', phase: 'CLI'}),
  () => agent('Improve error handling in SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/sync.py, add better error messages when: 1) tool data directory not found, 2) database locked, 3) permission denied. Use rich for colorful error output.', {label: 'error-handling', phase: 'CLI'}),
  () => agent('Add sessionvault doctor command to SessionVault. Create a new file /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/doctor.py that checks: 1) if tool data directories exist, 2) if database is healthy, 3) if all dependencies are installed. Register in cli/main.py.', {label: 'doctor-command', phase: 'CLI'}),
]);

// Phase 2: Data safety
phase('Data');
const data = await parallel([
  () => agent('Add backup/restore commands to SessionVault. Create /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/backup.py with: 1) backup command that copies data.db to ~/sessionvault-backups/ with timestamp, 2) restore command that restores from backup, 3) list command that shows available backups. Register in cli/main.py.', {label: 'backup-restore', phase: 'Data'}),
  () => agent('Add JSON/CSV export to SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/search.py, extend the export command to support --format json/csv/markdown. Update cli/main.py to add --format flag.', {label: 'export-formats', phase: 'Data'}),
]);

// Phase 3: Performance
phase('Performance');
const perf = await parallel([
  () => agent('Optimize Cursor extractor in SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/extractors/cursor.py, add batch processing: load all bubbles in one query instead of per-composer. Add progress indicator during extraction. Skip sessions with 0 messages early.', {label: 'cursor-optimize', phase: 'Performance'}),
  () => agent('Add query caching to SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/db.py, add a simple LRU cache for search results. Cache key = hash of query+filters. Invalidate on sync.', {label: 'query-cache', phase: 'Performance'}),
]);

// Phase 4: Extensibility
phase('Extensibility');
const ext = await parallel([
  () => agent('Add plugin system to SessionVault. Create /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/plugins.py with: 1) plugin registry, 2) load plugins from ~/.sessionvault/plugins/, 3) each plugin is a Python file with extract() function. Update extractors/__init__.py to load external plugins.', {label: 'plugin-system', phase: 'Extensibility'}),
  () => agent('Add REST API to SessionVault Web UI. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/web/app.py, add endpoints: GET /api/export/json, GET /api/export/csv, GET /api/backup/create, GET /api/doctor. These should return JSON responses.', {label: 'rest-api', phase: 'Extensibility'}),
]);

// Phase 5: Operations
phase('Operations');
const ops = await parallel([
  () => agent('Add usage statistics to SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/db.py, add a stats table that tracks: sync_count, search_count, last_sync_time, total_queries. Update sync and search commands to increment counters.', {label: 'usage-stats', phase: 'Operations'}),
  () => agent('Add auto-update check to SessionVault. Create /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/update.py that: 1) checks PyPI for latest version, 2) compares with current version, 3) prints update notification. Add to CLI startup.', {label: 'auto-update', phase: 'Operations'}),
]);

return `Product polish complete: CLI, Data safety, Performance, Extensibility, Operations`;
