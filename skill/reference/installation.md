# Installation

```bash
# Clone or copy daddyshome/ to your tools directory
cd /path/to/daddyshome
pip install -e .

# Add to Claude Code MCP config (~/.claude/claude_desktop_config.json or settings)
{
  "mcpServers": {
    "daddyshome": {
      "command": "python",
      "args": ["/path/to/daddyshome/src/server.py"],
      "type": "stdio"
    }
  }
}
```

Then in Claude Code, `/daddyshome` or saying "daddy's home" triggers this skill + MCP.

## Files owned by daddyshome

| File | Scope | Purpose |
|------|-------|---------|
| `.claude/settings.json` | Project | Auto-mode permissions |
| `.claude/.daddyshome` | Project | First-run marker + metadata |
| `.claude/mvp/mvp-{N}/tasks.md` | Project | Task checklist per MVP |
| `.claude/mvp/mvp-{N}/status.json` | Project | Machine-readable MVP status |
| `.claude/mvp/mvp-{N}/notes.md` | Project | Free-form notes |
| `CLAUDE.md` | Project | Behavior rules + context |
| `MEMORY.md` | Project | Decision log + session history |
| `ERRORS.md` | Project | Failure log |
| `~/.claude/MEMORY.md` | Global | Cross-project session history |
