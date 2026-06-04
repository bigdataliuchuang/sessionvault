export const meta = {
  name: 'sessionvault-polish',
  description: 'Polish SessionVault: GitHub Actions, CHANGELOG, CONTRIBUTING, Obsidian export, Web UI charts, TUI shortcuts',
  phases: [
    { title: 'CI/CD', detail: 'GitHub Actions workflow for tests' },
    { title: 'Docs', detail: 'CHANGELOG and CONTRIBUTING' },
    { title: 'Features', detail: 'Obsidian export, charts, shortcuts' },
  ],
};

// Phase 1: CI/CD
phase('CI/CD');
const githubActions = await agent('Create GitHub Actions CI/CD workflow for SessionVault. Write to /Users/liuchuang/Projects/personal/github/ai-conversations/.github/workflows/ci.yml. The workflow should: 1) Run on push to main and PRs, 2) Test on Python 3.9, 3.10, 3.11, 3.12, 3.13, 3) Install dependencies, 4) Run pytest, 5) Build package. Also create /Users/liuchuang/Projects/personal/github/ai-conversations/.github/workflows/publish.yml for PyPI publishing on release.', {label: 'github-actions', phase: 'CI/CD'});

// Phase 2: Documentation
phase('Docs');
const docs = await parallel([
  () => agent('Create CHANGELOG.md for SessionVault at /Users/liuchuang/Projects/personal/github/ai-conversations/CHANGELOG.md. Document v0.1.0 release with all features: 4 tool extractors, FTS5 search, MCP server, Web UI, TUI, cross-platform support, rich progress bar.', {label: 'changelog', phase: 'Docs'}),
  () => agent('Create CONTRIBUTING.md for SessionVault at /Users/liuchuang/Projects/personal/github/ai-conversations/CONTRIBUTING.md. Include: how to set up dev environment, how to run tests, how to add new extractors, code style, PR process.', {label: 'contributing', phase: 'Docs'}),
]);

// Phase 3: Features
phase('Features');
const features = await parallel([
  () => agent('Add Obsidian export to SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/cli/search.py, add an export_obsidian function that exports conversations to Obsidian-compatible markdown format with frontmatter (tags, dates, tool). Add --obsidian flag to the export command. Update cli/main.py to add the flag.', {label: 'obsidian-export', phase: 'Features'}),
  () => agent('Add charts/statistics visualization to SessionVault Web UI. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/web/app.py, add a simple HTML chart using CSS bars (no external JS libs) showing: conversations per tool, messages per day trend. Add a /api/stats/extended endpoint that returns daily counts.', {label: 'web-charts', phase: 'Features'}),
  () => agent('Improve TUI shortcuts in SessionVault. In /Users/liuchuang/Projects/personal/github/ai-conversations/src/ai_conversations/tui/app.py, add: j/k for up/down navigation, / for search focus, Enter to open detail, Escape to go back, r to refresh, o to export. Update BINDINGS and add key handlers.', {label: 'tui-shortcuts', phase: 'Features'}),
]);

// Summary
return `Polish complete: GitHub Actions, CHANGELOG, CONTRIBUTING, Obsidian export, Web charts, TUI shortcuts`;
