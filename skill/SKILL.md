---
name: daddyshome
description: >
  Full project session initialization and resumption for Claude Code.
  Trigger this skill whenever the user says "daddyshome", "daddy's home",
  "/daddyshome", "initialize project", "set up my claude environment",
  "scaffold my project", or "resume session". On first run: creates .claude/,
  CLAUDE.md, MEMORY.md, ERRORS.md, settings.json (scoped auto-mode), git repo,
  and MVP structure parsed from PRD. On returning runs: loads context, checks
  MVP gates, verifies skills active, prints structured briefing. Always trigger
  this when starting or resuming any Claude Code session — even if user doesn't
  say "daddyshome" explicitly and just says "let's get started" or "continue
  where we left off."
---

# daddyshome

Session initialization and resumption MCP for Claude Code.

## What it does

**First run** (no `.claude/` or `CLAUDE.md` in project root):
1. Scan codebase for project context (token-conscious)
2. Create `.claude/` directory
3. Write `settings.json` — scoped auto-mode
4. Write `CLAUDE.md` — from template with auto-filled placeholders
5. Create `MEMORY.md` + `ERRORS.md` (project-level)
6. Update `~/.claude/MEMORY.md` (global)
7. `git init` if no `.git/` present
8. Scan for PRD/implementation plan → generate `.claude/mvp/` structure
9. Verify skills active (caveman, grill-me)
10. Print structured briefing

**Returning run** (`.claude/` or `CLAUDE.md` exists):
1. Read `MEMORY.md` for last session context
2. Check MVP statuses + soft gate warnings
3. Verify skills active
4. Print structured briefing

---

## Invoking the MCP

When `daddyshome` is triggered, call the MCP tool:

```
Tool: daddyshome
Arguments: { "project_path": "<cwd>" }  // optional, defaults to cwd
```

If MCP is not installed, follow the **Manual Fallback** section below.

---

## Briefing output format

**First run:**
```
🏠 Daddy's Home — FIRST RUN
──────────────────────────────────────────────────
Project: my-rag-pipeline
Path:     /Users/taiwo/projects/my-rag-pipeline
Date:     2025-01-15
──────────────────────────────────────────────────

Setup log:
✅ Created .claude/ directory
✅ Wrote .claude/settings.json (scoped auto-mode)
✅ Wrote CLAUDE.md
✅ Created MEMORY.md
✅ Created ERRORS.md
✅ Updated ~/.claude/MEMORY.md (global)
✅ git init
✅ Generated MVP structure: 3 MVPs generated:
  🔓 MVP 1: Core RAG Pipeline (8 tasks)
  🔒 MVP 2: API Layer (5 tasks)
  🔒 MVP 3: Frontend (6 tasks)

──────────────────────────────────────────────────
Active skills: caveman, grill-me (auto-activate on session start)
MVP location: .claude/mvp/
──────────────────────────────────────────────────
Ready. CLAUDE.md is live. Start building.
```

**Returning run:**
```
🏠 Daddy's Home
──────────────────────────────────────────────────
Project:      my-rag-pipeline
Initialized:  2025-01-10
Last session: 2025-01-14
──────────────────────────────────────────────────

Last session notes:
[last MEMORY.md session entry here]

MVP status:
  ✅ MVP 1: Core RAG Pipeline — complete
  🔄 MVP 2: API Layer — in progress (3/5 tasks)
  🔒 MVP 3: Frontend — locked

Warnings:
None

──────────────────────────────────────────────────
Active skills: caveman, grill-me (auto-activating now)
──────────────────────────────────────────────────
Ready. Pick up where you left off.
```

---

## Skill activation

After briefing prints, immediately activate skills by behaving as if these commands were given:
- `activate caveman mode`
- `activate grill-me mode`

No need for user to say this — activation is automatic on every `daddyshome` run.

---

## MVP gate logic

- MVP folder structure: `.claude/mvp/mvp-{N}/` with `tasks.md`, `status.json`, `notes.md`
- Task completion tracked by Claude counting `- [x]` checkboxes in `tasks.md`
- If previous MVP incomplete and current MVP active: print soft warning, use discretion on whether to proceed
- Claude is the task tracker — mark tasks complete by updating checkboxes in `tasks.md`

**Marking a task complete:**
```markdown
- [x] Set up LlamaParse integration   ← completed
- [ ] Connect to Bedrock               ← still open
```

**MVP status values:** `in_progress` | `complete` | `locked`

---

## Manual Fallback

If MCP server is not running, execute this sequence manually:

```bash
# 1. Check first-run vs returning
if [ -d ".claude" ] || [ -f "CLAUDE.md" ]; then
  echo "Returning session — reading context"
  # Read MEMORY.md, check .claude/mvp/ statuses
else
  echo "First run — scaffolding project"
  mkdir -p .claude/mvp
  # Write settings.json, CLAUDE.md, MEMORY.md, ERRORS.md
  git init
  # Scan for PRD and generate MVP structure
fi
```

Then manually apply the CLAUDE.md template and MVP structure as described above.

---

## Installation

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

---

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
