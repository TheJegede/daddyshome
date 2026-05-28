# daddyshome

Claude Code MCP — one command to initialize or resume any project session.

## What it does

Say `daddyshome` (or `/daddyshome`) in Claude Code. That's it.

**First run** scaffolds:
- `.claude/settings.json` — scoped auto-mode (no confirmation for safe ops, confirmation for destructive/network)
- `CLAUDE.md` — your rules template with project context auto-filled from codebase scan
- `MEMORY.md` + `ERRORS.md` — decision and failure logs
- `~/.claude/MEMORY.md` — global session history
- `.git/` — if not already initialized
- `.claude/mvp/` — MVP structure parsed from your PRD/implementation plan

**Returning run** prints a briefing:
- Last session summary from `MEMORY.md`
- MVP gate status (with soft warnings for incomplete gates)
- Auto-activates caveman + grill-me skills

---

## Install

```bash
# 1. Install Python package
cd daddyshome
pip install -e .

# 2. Add MCP server to Claude Code config
# Edit ~/.claude/claude_desktop_config.json (or your Claude Code MCP settings):
```

```json
{
  "mcpServers": {
    "daddyshome": {
      "command": "python",
      "args": ["/absolute/path/to/daddyshome/src/server.py"],
      "type": "stdio"
    }
  }
}
```

```bash
# 3. Install the skill
# Copy skill/SKILL.md to your Claude skills directory:
cp skill/SKILL.md /path/to/your/skills/daddyshome/SKILL.md
```

---

## Usage

```
# In Claude Code terminal or chat:
daddyshome
daddy's home
/daddyshome
```

That's it.

---

## Project structure after first run

```
your-project/
├── .claude/
│   ├── settings.json       # scoped auto-mode config
│   ├── .daddyshome         # marker file (first-run detection)
│   └── mvp/
│       ├── mvp-1/
│       │   ├── tasks.md    # Claude tracks checkboxes here
│       │   ├── status.json # auto-updated by daddyshome
│       │   └── notes.md
│       └── mvp-2/          # locked until mvp-1 complete
│           ├── tasks.md
│           ├── status.json
│           └── notes.md
├── CLAUDE.md               # your rules + project context
├── MEMORY.md               # decision log
└── ERRORS.md               # failure log
```

---

## MVP task tracking

Claude tracks tasks by reading checkboxes in `.claude/mvp/mvp-{N}/tasks.md`.

Mark tasks done:
```markdown
- [x] Set up LlamaParse integration   ← done
- [ ] Connect Bedrock embedding model  ← open
```

When all tasks in MVP N are `[x]`, MVP N+1 unlocks automatically on next `daddyshome` run.

---

## Files

```
daddyshome/
├── src/
│   ├── server.py     # MCP server entry point
│   ├── scanner.py    # codebase + PRD scanner
│   ├── mvp.py        # MVP structure generator + status tracker
│   ├── settings.py   # settings.json writer
│   ├── memory.py     # MEMORY.md read/write
│   └── briefing.py   # briefing helpers
├── skill/
│   └── SKILL.md      # Claude skill wrapper
├── pyproject.toml
└── README.md
```

---

## Requirements

- Python 3.10+
- `mcp>=1.0.0`
- Claude Code with MCP support
