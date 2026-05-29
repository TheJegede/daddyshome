# Manual fallback (MCP not running)

If the MCP server is not running, execute this sequence manually:

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

Then manually apply the CLAUDE.md template and MVP structure as described in
[briefing-format.md](briefing-format.md) and [mvp-gates.md](mvp-gates.md).
