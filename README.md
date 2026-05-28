# daddyshome

Claude Code MCP — one command to initialize or resume any project session.

Type `daddyshome` in Claude Code. That's it.

---

## What it does

**First run** (no `.claude/` or `CLAUDE.md` detected):

- Creates `.claude/settings.json` with scoped auto-mode
- Writes `CLAUDE.md` with your rules and auto-filled project context
- Creates `MEMORY.md` and `ERRORS.md` for decision and failure logging
- Updates `~/.claude/MEMORY.md` global session history
- Runs `git init` if no repo exists
- Scans for your PRD or implementation plan and generates `.claude/mvp/` structure
- Auto-activates caveman and grill-me skills

**Returning run** (`.claude/` or `CLAUDE.md` already exists):

- Reads last session from `MEMORY.md`
- Checks MVP gate status and warns if gates are incomplete
- Auto-activates skills
- Prints a structured briefing so you pick up exactly where you left off

---

## Install

### 1. Clone the repo

```powershell
git clone https://github.com/TheJegede/daddyshome
cd daddyshome
```

### 2. Set up your personal server.py

```powershell
copy src\server.template.py src\server.py
```

Open `src\server.py` and fill in your details in the `CLAUDE_MD_TEMPLATE` section:

```python
* **About me:** [YOUR_NAME]
* **Role:** [YOUR_ROLE]
* **Background in:** [YOUR_BACKGROUND]
* **Strong in:** [YOUR_STRENGTHS]
```

And your tech stack:

```python
* [YOUR_STACK — e.g. Cloud: AWS Lambda]
* [YOUR_STACK — e.g. Language: Python 3.11]
```

### 3. Run the installer

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The script will:
- Install Python dependencies
- Register the MCP server in your Claude Code config
- Install the skill to `~/.claude/skills/daddyshome/`
- Set up global `~/.claude/MEMORY.md`
- Verify everything loaded correctly

### 4. Restart Claude Code

Full quit and reopen. Then open any project and type:

```
daddyshome
```

---

## Usage

```
daddyshome
daddy's home
/daddyshome
```

All three work.

---

## MVP task tracking

daddyshome parses your PRD or implementation plan and scaffolds a gated MVP structure:

```
.claude/mvp/
├── mvp-1/
│   ├── tasks.md      # Claude tracks checkboxes here
│   ├── status.json   # auto-updated on each run
│   └── notes.md
└── mvp-2/            # locked until mvp-1 complete
    ├── tasks.md
    ├── status.json
    └── notes.md
```

Mark tasks done directly in `tasks.md`:

```markdown
- [x] Set up database schema
- [ ] Build API layer
```

When all tasks in MVP N are checked, MVP N+1 unlocks automatically on the next `daddyshome` run.

---

## Project structure after first run

```
your-project/
├── .claude/
│   ├── settings.json
│   ├── .daddyshome
│   └── mvp/
├── CLAUDE.md
├── MEMORY.md
└── ERRORS.md
```

---

## Requirements

- Windows (PowerShell installer)
- Python 3.10+
- Claude Code with MCP support

---

## Files

```
daddyshome/
├── src/
│   ├── server.template.py  # rename to server.py and fill in your details
│   ├── scanner.py          # token-conscious codebase + PRD scanner
│   ├── mvp.py              # MVP structure generator + status tracker
│   ├── settings.py         # settings.json writer
│   └── memory.py           # MEMORY.md read/write
├── skill/
│   └── SKILL.md            # Claude Code skill wrapper
├── install.ps1             # Windows installer
├── pyproject.toml
└── README.md
```