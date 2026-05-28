#!/usr/bin/env python3
"""
daddyshome MCP Server
Scaffolds and resumes Claude Code project sessions.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not found. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

from scanner import scan_for_prd, scan_codebase_context
from mvp import generate_mvp_structure, load_mvp_status
from settings import write_settings_json
from memory import read_memory, append_memory, read_global_memory, append_global_memory
from briefing import build_briefing

app = Server("daddyshome")

CLAUDE_MD_TEMPLATE = """\
# CLAUDE.md

## 1. DEFAULTS
**Session Initialization:**
At the start of every new session, automatically activate the "caveman mode" skill.

**Grill me (Challenge assumptions):**
Automatically activate the "grill me" skill. Whenever I make specific suggestions, architectural propositions, or logical assumptions, grill me. Stress-test my ideas to expose potential flaws. Never take my initial propositions at face value.

**Ask clarifying questions constantly:**
Avoid assumptions at all costs. Before executing any complex logic or system design, ask clarifying questions to ensure we are entirely on the same page.

**Kill the filler:**
Never open responses with filler phrases like "Great question!", "Of course!", "Certainly!", or similar warmups. Start every response with the actual answer.

**Match length to the task:**
Match response length to task complexity. Simple questions get direct, short answers. Complex tasks get full, detailed responses.

**Show options before acting:**
Before any significant task, show me 2-3 ways you could approach this work. Wait for me to choose before proceeding.

**Admit uncertainty before it costs me:**
If you are uncertain about any fact, statistic, date, or piece of technical information: say so explicitly before including it.

**Who I am and what I know:**
* **About me:** [YOUR_NAME]
* **Role:** [YOUR_ROLE — e.g. Senior Backend Engineer, AI Engineer]
* **Background in:** [YOUR_BACKGROUND — e.g. Computer Science, 5 years Python]
* **Strong in:** [YOUR_STRENGTHS — e.g. REST APIs, PostgreSQL, Docker]
* **Instruction:** Adjust the depth of every response to match this. Never over-explain what I already know. Never skip context I need.

**Current project context:**
* **Project:** {PROJECT_NAME}
* **Description:** {PROJECT_DESCRIPTION}
* **Focus:** {PROJECT_FOCUS}
* **Rule:** Apply this context to every task. When something doesn't fit, flag it before proceeding.

**Lock your tech stack:**
* [YOUR_STACK — e.g. Cloud: AWS Lambda / GCP Cloud Run]
* [YOUR_STACK — e.g. Language: Python 3.11 / TypeScript]
* [YOUR_STACK — e.g. Framework: FastAPI / Next.js]
* [YOUR_STACK — e.g. DB: PostgreSQL / Redis]

---

## 2. BEHAVIOR
**Stay in scope:**
Only modify files, functions, and lines of code directly related to the current task.

**Ask before big changes:**
Before making any change that significantly alters content I've already created: stop. Describe exactly what you're about to change and why. Wait for confirmation.

**Confirm before anything destructive:**
Before deleting files, overwriting code, dropping database records, or removing dependencies: stop. List exactly what will be affected. Ask for explicit confirmation.

**Hard stops for production:**
The following require explicit in-session confirmation: deploying or pushing to any environment, running migrations or schema changes, sending any external API call, executing any command with irreversible side effects.

**Always show what changed:**
After any coding task, end with:
* Files changed: (list every file touched)
* What was modified: (one line per file)
* Files intentionally not touched: (list)
* Follow-up needed: (list)

---

## 3. MEMORY + STACK
**MEMORY.md decision log:**
Maintain `MEMORY.md` in this project. After any significant decision, add an entry: What was decided / Why / What was rejected and why. Read `MEMORY.md` at the start of every session.

**ERRORS.md failure log:**
Maintain `ERRORS.md`. When an approach takes more than 2 attempts, log it: What didn't work / What worked instead / Note for next time. Check `ERRORS.md` before suggesting approaches to similar tasks.

**Auto-Activate Skills:**
At the start of every session, automatically activate: caveman mode, grill-me mode.

---

## 4. KARPATHY'S CORE RULES
1. **Ask, don't assume.** If something is unclear, ask before writing a single line.
2. **Simplest solution first.** Always implement the simplest thing that could work.
3. **Don't touch unrelated code.** If a file or function is not directly part of the current task, do not modify it.
4. **Flag uncertainty explicitly.** If you are not confident about an approach or technical detail, say so before proceeding.
"""

MEMORY_TEMPLATE = """\
# MEMORY.md — Decision Log

**Project:** {PROJECT_NAME}
**Initialized:** {DATE}

---

## Sessions

<!-- daddyshome appends session summaries here -->

---

## Decisions

<!-- Log format: [DATE] What was decided | Why | What was rejected -->

"""

ERRORS_TEMPLATE = """\
# ERRORS.md — Failure Log

**Project:** {PROJECT_NAME}
**Initialized:** {DATE}

---

## Logged Failures

<!-- Log format:
### [DATE] Short description
- What didn't work:
- What worked instead:
- Note for next time:
-->

"""


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="daddyshome",
            description=(
                "Initialize or resume a Claude Code project session. "
                "First run: scaffolds .claude/, CLAUDE.md, MEMORY.md, ERRORS.md, "
                "settings.json, git repo, and MVP structure from PRD. "
                "Returning run: loads context, checks MVP gates, activates skills, "
                "prints structured briefing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Absolute path to project root. Defaults to cwd.",
                    }
                },
                "required": [],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "daddyshome":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    project_path = Path(arguments.get("project_path", os.getcwd())).resolve()
    claude_dir = project_path / ".claude"
    claude_md = project_path / "CLAUDE.md"

    is_first_run = not claude_dir.exists() and not claude_md.exists()

    if is_first_run:
        result = await first_run(project_path, claude_dir, claude_md)
    else:
        result = await returning_run(project_path, claude_dir, claude_md)

    return [TextContent(type="text", text=result)]


async def first_run(project_path: Path, claude_dir: Path, claude_md: Path) -> str:
    steps = []
    errors = []

    # 1. Scan codebase for project context
    steps.append("🔍 Scanning codebase for project context...")
    context = scan_codebase_context(project_path)
    prd_content = scan_for_prd(project_path)

    project_name = context.get("name", project_path.name)
    project_description = context.get("description", "No description found.")
    project_focus = context.get("focus", "General development.")

    # 2. Create .claude/ directory
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "mvp").mkdir(exist_ok=True)
    steps.append("Created .claude/ directory")

    # 3. Write settings.json
    try:
        write_settings_json(claude_dir)
        steps.append("Wrote .claude/settings.json (scoped auto-mode)")
    except Exception as e:
        errors.append(f"settings.json: {e}")

    # 4. Write CLAUDE.md
    try:
        filled = CLAUDE_MD_TEMPLATE.format(
            PROJECT_NAME=project_name,
            PROJECT_DESCRIPTION=project_description,
            PROJECT_FOCUS=project_focus,
        )
        claude_md.write_text(filled)
        steps.append("Wrote CLAUDE.md")
    except Exception as e:
        errors.append(f"CLAUDE.md: {e}")

    # 5. Write MEMORY.md
    now = datetime.now().strftime("%Y-%m-%d")
    try:
        memory_path = project_path / "MEMORY.md"
        if not memory_path.exists():
            memory_path.write_text(
                MEMORY_TEMPLATE.format(PROJECT_NAME=project_name, DATE=now)
            )
            steps.append("Created MEMORY.md")
    except Exception as e:
        errors.append(f"MEMORY.md: {e}")

    # 6. Write ERRORS.md
    try:
        errors_path = project_path / "ERRORS.md"
        if not errors_path.exists():
            errors_path.write_text(
                ERRORS_TEMPLATE.format(PROJECT_NAME=project_name, DATE=now)
            )
            steps.append("Created ERRORS.md")
    except Exception as e:
        errors.append(f"ERRORS.md: {e}")

    # 7. Update global MEMORY.md
    try:
        append_global_memory(
            f"[{now}] New project initialized: {project_name} at {project_path}"
        )
        steps.append("Updated ~/.claude/MEMORY.md (global)")
    except Exception as e:
        errors.append(f"global MEMORY.md: {e}")

    # 8. git init
    git_dir = project_path / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init"], cwd=project_path, capture_output=True, check=True
            )
            steps.append("git init")
        except Exception as e:
            errors.append(f"git init: {e}")
    else:
        steps.append("Git repo already exists — skipped")

    # 9. Generate MVP structure
    if prd_content:
        try:
            mvp_result = generate_mvp_structure(
                claude_dir / "mvp", prd_content, project_name
            )
            steps.append(f"Generated MVP structure: {mvp_result}")
        except Exception as e:
            errors.append(f"MVP generation: {e}")
    else:
        steps.append("No PRD/implementation plan found — MVP structure skipped")
        steps.append("   → Create a PRD.md or implementation_plan.md and re-run")

    # 10. Write .daddyshome marker
    marker = claude_dir / ".daddyshome"
    marker.write_text(
        json.dumps(
            {
                "initialized": now,
                "project_name": project_name,
                "last_session": now,
            }
        )
    )

    # Build output
    setup_log = "\n".join(steps)
    error_log = "\n".join(f"{e}" for e in errors) if errors else "None"

    briefing = f"""
🏠 Daddy's Home — FIRST RUN
{"─" * 50}
Project: {project_name}
Path:     {project_path}
Date:     {now}
{"─" * 50}

Setup log:
{setup_log}

Errors:
{error_log}

{"─" * 50}
Active skills: caveman, grill-me (auto-activate on session start)
MVP location: .claude/mvp/
{"─" * 50}
Ready. CLAUDE.md is live. Start building.
"""
    return briefing.strip()


async def returning_run(project_path: Path, claude_dir: Path, claude_md: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    warnings = []

    # Read marker
    marker_path = claude_dir / ".daddyshome"
    marker = {}
    if marker_path.exists():
        try:
            marker = json.loads(marker_path.read_text())
        except Exception:
            pass

    project_name = marker.get("project_name", project_path.name)
    last_session = marker.get("last_session", "Unknown")
    initialized = marker.get("initialized", "Unknown")

    # Update last session date
    marker["last_session"] = now
    marker_path.write_text(json.dumps(marker, indent=2))

    # Read MEMORY.md for last session summary
    memory_snippet = read_memory(project_path)

    # Load MVP status
    mvp_status_lines, mvp_warnings = load_mvp_status(claude_dir / "mvp")
    warnings.extend(mvp_warnings)

    # Update global memory
    try:
        append_global_memory(
            f"[{now}] Resumed project: {project_name} at {project_path}"
        )
    except Exception:
        pass

    mvp_block = "\n".join(mvp_status_lines) if mvp_status_lines else "No MVP structure found"
    warning_block = "\n".join(f"⚠️  {w}" for w in warnings) if warnings else "None"
    memory_block = memory_snippet or "No previous session logged"

    briefing = f"""
🏠 Daddy's Home
{"─" * 50}
Project:      {project_name}
Initialized:  {initialized}
Last session: {last_session}
{"─" * 50}

Last session notes:
{memory_block}

MVP status:
{mvp_block}

Warnings:
{warning_block}

{"─" * 50}
Active skills: caveman, grill-me (auto-activating now)
{"─" * 50}
Ready. Pick up where you left off.
"""
    return briefing.strip()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())