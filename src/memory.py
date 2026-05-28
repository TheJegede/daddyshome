"""
memory.py — Read and append to MEMORY.md files.
Project-level: {project_path}/MEMORY.md
Global: ~/.claude/MEMORY.md
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

GLOBAL_CLAUDE_DIR = Path.home() / ".claude"
GLOBAL_MEMORY_PATH = GLOBAL_CLAUDE_DIR / "MEMORY.md"

GLOBAL_MEMORY_TEMPLATE = """\
# ~/.claude/MEMORY.md — Global Decision Log

Tracks cross-project learnings and session history.

---

## Project History

<!-- daddyshome appends entries here -->

---

## Cross-Project Learnings

<!-- Log patterns, recurring fixes, architecture decisions that span projects -->

"""


def read_memory(project_path: Path, max_lines: int = 30) -> Optional[str]:
    """
    Read last N lines of MEMORY.md for briefing.
    Returns snippet or None.
    """
    memory_path = project_path / "MEMORY.md"
    if not memory_path.exists():
        return None

    try:
        lines = memory_path.read_text(errors="ignore").splitlines()
        # Find last session entry
        session_start = None
        for i, line in enumerate(reversed(lines)):
            if line.startswith("## Session") or line.startswith("### Session"):
                session_start = len(lines) - i - 1
                break

        if session_start is not None:
            snippet = "\n".join(lines[session_start:session_start + max_lines])
        else:
            # Fall back to last N lines
            snippet = "\n".join(lines[-max_lines:])

        return snippet.strip() if snippet.strip() else None
    except Exception:
        return None


def append_memory(project_path: Path, entry: str) -> None:
    """Append an entry to project MEMORY.md."""
    memory_path = project_path / "MEMORY.md"
    if not memory_path.exists():
        return

    try:
        existing = memory_path.read_text()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        memory_path.write_text(existing + f"\n\n<!-- [{now}] -->\n{entry}\n")
    except Exception:
        pass


def read_global_memory(max_lines: int = 20) -> Optional[str]:
    """Read last N lines of global MEMORY.md."""
    if not GLOBAL_MEMORY_PATH.exists():
        return None
    try:
        lines = GLOBAL_MEMORY_PATH.read_text(errors="ignore").splitlines()
        return "\n".join(lines[-max_lines:]).strip() or None
    except Exception:
        return None


def append_global_memory(entry: str) -> None:
    """Append entry to global ~/.claude/MEMORY.md."""
    GLOBAL_CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    if not GLOBAL_MEMORY_PATH.exists():
        GLOBAL_MEMORY_PATH.write_text(GLOBAL_MEMORY_TEMPLATE)

    try:
        existing = GLOBAL_MEMORY_PATH.read_text()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        GLOBAL_MEMORY_PATH.write_text(existing + f"\n- [{now}] {entry}")
    except Exception:
        pass
