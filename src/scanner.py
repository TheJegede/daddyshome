"""
scanner.py — Token-conscious codebase and PRD scanning.

Strategy:
1. Filenames first — check names for PRD/plan signals before reading content
2. Shallow content scan — read only first 50 lines of candidate files
3. Full read only on confirmed matches
4. Hard skip list to avoid token waste
"""

import os
from pathlib import Path
from typing import Optional

# Files/dirs to always skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    "env", ".env", "logs", "tmp", ".terraform", "vendor",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
    ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".zip", ".tar",
    ".gz", ".lock", ".pyc", ".class", ".so", ".dll", ".exe",
    ".pdf", ".docx", ".xlsx", ".pptx",
}

# Strong signals in filename
PRD_NAME_SIGNALS = [
    "prd", "product_requirement", "product-requirement",
    "implementation", "impl_plan", "implementation_plan",
    "roadmap", "spec", "design_doc", "design-doc",
    "requirements", "planning", "project_plan", "project-plan",
    "brief", "overview", "architecture",
]

# Content patterns that signal a PRD/plan document
PRD_CONTENT_SIGNALS = [
    "mvp", "milestone", "phase ", "sprint", "epic",
    "user story", "acceptance criteria", "feature list",
    "implementation plan", "technical spec", "product requirements",
    "objectives", "deliverable", "scope", "timeline",
]

# Project context signals
CONTEXT_NAME_FILES = ["package.json", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod"]
CONTEXT_DESC_FILES = ["README.md", "readme.md", "README.rst"]


def _should_skip(path: Path) -> bool:
    if path.name.startswith(".") and path.name not in {".claude"}:
        return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return False


def _name_score(filename: str) -> int:
    """Score a filename for PRD likelihood. Higher = more likely."""
    lower = filename.lower().replace("-", "_")
    score = 0
    for signal in PRD_NAME_SIGNALS:
        if signal in lower:
            score += 2
    if lower.endswith(".md") or lower.endswith(".txt"):
        score += 1
    return score


def _content_score(text: str) -> int:
    """Score first 50 lines for PRD signals."""
    lower = text.lower()
    score = 0
    for signal in PRD_CONTENT_SIGNALS:
        if signal in lower:
            score += 1
    return score


def scan_for_prd(project_path: Path, max_candidates: int = 5) -> Optional[str]:
    """
    Find and return the most likely PRD/implementation plan content.
    Token-conscious: name scoring first, shallow content scan second.
    Returns full content of best match, or None.
    """
    candidates = []

    for root, dirs, files in os.walk(project_path):
        # Prune skip dirs in-place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)

        for filename in files:
            file_path = root_path / filename
            if _should_skip(file_path):
                continue

            name_score = _name_score(filename)
            if name_score > 0:
                candidates.append((name_score, file_path))

    # Sort by name score descending, take top candidates
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:max_candidates]

    # If no name matches, do shallow content scan on .md files
    if not top:
        md_files = []
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in files:
                if filename.endswith(".md") or filename.endswith(".txt"):
                    md_files.append(Path(root) / filename)

        for file_path in md_files[:20]:  # Cap at 20 to limit token usage
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    snippet = "".join(f.readlines()[:50])
                score = _content_score(snippet)
                if score >= 2:
                    top.append((score, file_path))
            except Exception:
                continue

        top.sort(key=lambda x: x[0], reverse=True)
        top = top[:max_candidates]

    if not top:
        return None

    # Full read of best match
    _, best_file = top[0]
    try:
        return best_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def scan_codebase_context(project_path: Path) -> dict:
    """
    Extract project name, description, and focus from codebase.
    Checks package.json, pyproject.toml, README — in that order.
    Token-conscious: reads only what it needs.
    """
    context = {
        "name": project_path.name,
        "description": "",
        "focus": "",
    }

    # Try package.json
    pkg = project_path / "package.json"
    if pkg.exists():
        try:
            import json
            data = json.loads(pkg.read_text())
            context["name"] = data.get("name", context["name"])
            context["description"] = data.get("description", "")
        except Exception:
            pass

    # Try pyproject.toml
    if not context["description"]:
        pyproj = project_path / "pyproject.toml"
        if pyproj.exists():
            try:
                text = pyproj.read_text()
                for line in text.splitlines():
                    if line.startswith("name"):
                        context["name"] = line.split("=")[-1].strip().strip('"').strip("'")
                    if line.startswith("description"):
                        context["description"] = line.split("=")[-1].strip().strip('"').strip("'")
            except Exception:
                pass

    # Try README (first 30 lines only)
    if not context["description"]:
        for readme_name in ["README.md", "readme.md", "README.rst", "README.txt"]:
            readme = project_path / readme_name
            if readme.exists():
                try:
                    lines = readme.read_text(errors="ignore").splitlines()[:30]
                    # Use first non-empty, non-heading line as description
                    for line in lines:
                        stripped = line.strip().lstrip("#").strip()
                        if stripped and len(stripped) > 10:
                            context["description"] = stripped[:200]
                            break
                except Exception:
                    pass
                break

    # Detect tech focus from file extensions present
    focus_signals = []
    ext_counts: dict[str, int] = {}
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

    if ext_counts.get(".py", 0) > 2:
        focus_signals.append("Python")
    if ext_counts.get(".ts", 0) > 2 or ext_counts.get(".tsx", 0) > 2:
        focus_signals.append("TypeScript/React")
    if ext_counts.get(".js", 0) > 2:
        focus_signals.append("JavaScript")
    if (project_path / "template.yaml").exists() or (project_path / "serverless.yml").exists():
        focus_signals.append("AWS Serverless")
    if (project_path / "requirements.txt").exists():
        focus_signals.append("Python backend")

    context["focus"] = ", ".join(focus_signals) if focus_signals else "General development"

    return context
