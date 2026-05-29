# MVP gate logic

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
