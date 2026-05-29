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

Session initialization and resumption MCP for Claude Code. Scaffolds on first
run, briefs on return.

## When triggered

Call the MCP tool:

```
Tool: daddyshome
Arguments: { "project_path": "<cwd>" }  // optional, defaults to cwd
```

If the MCP server is not running, see [reference/manual-fallback.md](reference/manual-fallback.md).

## First run (no `.claude/` or `CLAUDE.md` in project root)

1. Scan codebase for project context (token-conscious)
2. Create `.claude/` directory
3. Write `settings.json` — scoped auto-mode
4. Write `CLAUDE.md` — from template with auto-filled placeholders
5. Create `MEMORY.md` + `ERRORS.md` (project-level)
6. Update `~/.claude/MEMORY.md` (global)
7. `git init` if no `.git/` present
8. Scan for PRD/implementation plan → generate `.claude/mvp/` structure
9. Print structured briefing

## Returning run (`.claude/` or `CLAUDE.md` exists)

1. Read `MEMORY.md` for last session context
2. Check MVP statuses + soft gate warnings
3. Print structured briefing

## After briefing: activate skills

Immediately activate, behaving as if these were given (no user prompt needed):

- `activate caveman mode`
- `activate grill-me mode`

Activation is automatic on every `daddyshome` run.

## References

- Briefing output format (first run + returning) → [reference/briefing-format.md](reference/briefing-format.md)
- MVP gate logic + task tracking → [reference/mvp-gates.md](reference/mvp-gates.md)
- Manual fallback when MCP is down → [reference/manual-fallback.md](reference/manual-fallback.md)
- Installation + files owned → [reference/installation.md](reference/installation.md)
