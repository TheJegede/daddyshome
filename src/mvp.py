"""
mvp.py — Generate and track MVP structure from PRD content.

Structure per MVP:
.claude/mvp/
├── mvp-1/
│   ├── tasks.md      # Claude-generated checklist
│   ├── status.json   # machine-readable status
│   └── notes.md      # free-form notes
├── mvp-2/            # locked until mvp-1 complete
└── ...
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


STATUS_LOCKED = "locked"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETE = "complete"


def _extract_mvp_sections(prd_content: str) -> list[dict]:
    """
    Parse PRD content into MVP sections.
    Looks for: MVP 1/2/3, Phase 1/2/3, Milestone 1/2/3, Sprint 1/2/3
    Returns list of {number, title, content} dicts.
    """
    sections = []

    # Patterns to detect MVP/phase/milestone headings
    heading_pattern = re.compile(
        r"^#{1,4}\s*(?:MVP|Phase|Milestone|Sprint|Stage)\s*(\d+)[:\s-]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(heading_pattern.finditer(prd_content))

    if matches:
        for i, match in enumerate(matches):
            number = int(match.group(1))
            title = match.group(2).strip() or f"MVP {number}"
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(prd_content)
            content = prd_content[start:end].strip()
            sections.append({"number": number, "title": title, "content": content})
    else:
        # No explicit sections found — treat entire PRD as MVP 1
        sections.append({"number": 1, "title": "Initial MVP", "content": prd_content})

    return sections


def _generate_tasks_from_content(content: str, mvp_number: int, title: str) -> str:
    """
    Generate a tasks.md from MVP section content.
    Extracts bullet points, numbered lists, feature descriptions.
    Claude will refine these — this is the structural scaffold.
    """
    lines = []
    lines.append(f"# MVP {mvp_number}: {title}")
    lines.append(f"\n**Status:** In Progress\n")
    lines.append("## Tasks\n")

    # Extract existing bullet points or numbered lists
    task_pattern = re.compile(r"^[\s]*[-*•]\s+(.+)$|^[\s]*\d+\.\s+(.+)$", re.MULTILINE)
    task_matches = task_pattern.findall(content)

    extracted_tasks = []
    for m in task_matches:
        task = (m[0] or m[1]).strip()
        if task and len(task) > 5:
            extracted_tasks.append(task)

    if extracted_tasks:
        for task in extracted_tasks:
            lines.append(f"- [ ] {task}")
    else:
        # No structured tasks found — extract key sentences as tasks
        sentences = re.split(r"[.!?]\s+", content)
        task_sentences = [
            s.strip()
            for s in sentences
            if len(s.strip()) > 20 and len(s.strip()) < 200
        ][:10]

        for sentence in task_sentences:
            lines.append(f"- [ ] {sentence}")

        if not task_sentences:
            lines.append(f"- [ ] Define and implement {title}")
            lines.append(f"- [ ] Test and validate {title}")
            lines.append(f"- [ ] Document {title}")

    lines.append("\n## Notes\n")
    lines.append("<!-- Add implementation notes here -->\n")

    return "\n".join(lines)


def generate_mvp_structure(mvp_dir: Path, prd_content: str, project_name: str) -> str:
    """
    Parse PRD and scaffold .claude/mvp/ directory.
    First MVP unlocked, rest locked.
    Returns summary string.
    """
    mvp_dir.mkdir(parents=True, exist_ok=True)
    sections = _extract_mvp_sections(prd_content)

    created = []
    for i, section in enumerate(sections):
        num = section["number"]
        title = section["title"]
        mvp_folder = mvp_dir / f"mvp-{num}"
        mvp_folder.mkdir(exist_ok=True)

        # Generate tasks.md
        tasks_content = _generate_tasks_from_content(
            section["content"], num, title
        )
        (mvp_folder / "tasks.md").write_text(tasks_content)

        # Generate notes.md
        (mvp_folder / "notes.md").write_text(
            f"# MVP {num}: {title} — Notes\n\n<!-- Free-form notes here -->\n"
        )

        # Write status.json
        status = STATUS_IN_PROGRESS if i == 0 else STATUS_LOCKED
        total_tasks = tasks_content.count("- [ ]")
        status_data = {
            "mvp": num,
            "title": title,
            "status": status,
            "total_tasks": total_tasks,
            "completed_tasks": 0,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }
        (mvp_folder / "status.json").write_text(json.dumps(status_data, indent=2))

        lock_indicator = "🔓" if status == STATUS_IN_PROGRESS else "🔒"
        created.append(f"  {lock_indicator} MVP {num}: {title} ({total_tasks} tasks)")

    return f"{len(sections)} MVPs generated:\n" + "\n".join(created)


def load_mvp_status(mvp_dir: Path) -> tuple[list[str], list[str]]:
    """
    Read all MVP status files and return display lines + warnings.
    Auto-updates task completion by counting checkboxes in tasks.md.
    """
    if not mvp_dir.exists():
        return [], []

    lines = []
    warnings = []

    mvp_folders = sorted(
        [d for d in mvp_dir.iterdir() if d.is_dir() and d.name.startswith("mvp-")],
        key=lambda d: int(d.name.split("-")[1]) if d.name.split("-")[1].isdigit() else 999,
    )

    if not mvp_folders:
        return ["  No MVP structure found"], []

    prev_complete = True  # Track if previous MVP is done (gate logic)

    for folder in mvp_folders:
        status_file = folder / "status.json"
        tasks_file = folder / "tasks.md"

        if not status_file.exists():
            continue

        try:
            status_data = json.loads(status_file.read_text())
        except Exception:
            continue

        num = status_data.get("mvp", "?")
        title = status_data.get("title", "Untitled")
        status = status_data.get("status", STATUS_LOCKED)

        # Recount tasks from tasks.md (source of truth)
        if tasks_file.exists():
            tasks_text = tasks_file.read_text()
            total = tasks_text.count("- [ ]") + tasks_text.count("- [x]")
            completed = tasks_text.count("- [x]")

            # Auto-detect completion
            if total > 0 and completed == total and status != STATUS_COMPLETE:
                status = STATUS_COMPLETE
                status_data["status"] = STATUS_COMPLETE
                status_data["completed_tasks"] = completed
                status_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                status_file.write_text(json.dumps(status_data, indent=2))
            else:
                status_data["total_tasks"] = total
                status_data["completed_tasks"] = completed
                status_file.write_text(json.dumps(status_data, indent=2))
        else:
            total = status_data.get("total_tasks", 0)
            completed = status_data.get("completed_tasks", 0)

        # Build status line
        if status == STATUS_COMPLETE:
            icon = "✅"
            status_label = "complete"
        elif status == STATUS_IN_PROGRESS:
            icon = "⚠️ " if not prev_complete else "🔄"
            status_label = f"in progress ({completed}/{total} tasks)"
        else:
            icon = "🔒"
            status_label = "locked"

        lines.append(f"  {icon} MVP {num}: {title} — {status_label}")

        # Gate warning: previous incomplete, this one somehow unlocked
        if not prev_complete and status == STATUS_IN_PROGRESS:
            warnings.append(
                f"MVP {num} is active but previous MVP is incomplete. "
                f"Complete prior MVP before proceeding."
            )

        prev_complete = status == STATUS_COMPLETE

    return lines, warnings
