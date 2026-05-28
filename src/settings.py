"""
settings.py — Write .claude/settings.json with scoped auto-mode.

Scoped auto-mode policy:
- Auto-approve: file reads, file writes, bash (non-destructive), git ops
- Require confirmation: network calls, destructive bash, deployments, migrations
"""

import json
from pathlib import Path


SETTINGS = {
    "autoMode": {
        "enabled": True,
        "environment": {
            "allowedTools": [
                "read_file",
                "write_file",
                "list_directory",
                "search_files",
                "execute_bash",
                "git_status",
                "git_diff",
                "git_log",
                "git_add",
                "git_commit",
            ],
            "requireConfirmation": [
                "web_fetch",
                "web_search",
                "mcp__*",
            ],
        },
    },
    "permissions": {
        "allow": [
            "Bash(git *)",
            "Bash(ls *)",
            "Bash(cat *)",
            "Bash(find *)",
            "Bash(grep *)",
            "Bash(mkdir *)",
            "Bash(cp *)",
            "Bash(mv *)",
            "Bash(touch *)",
            "Bash(echo *)",
            "Bash(pwd)",
            "Bash(python *)",
            "Bash(python3 *)",
            "Bash(pip *)",
            "Bash(pip3 *)",
            "Bash(npm *)",
            "Bash(node *)",
            "Bash(yarn *)",
            "Read(*)",
            "Write(*)",
        ],
        "deny": [
            "Bash(rm -rf *)",
            "Bash(sudo rm *)",
            "Bash(curl * | bash)",
            "Bash(wget * | bash)",
            "Bash(git push --force *)",
            "Bash(DROP TABLE *)",
            "Bash(truncate *)",
        ],
    },
    "env": {
        "DISABLE_PROMPT_CACHING": "false",
    },
    "includeCoAuthoredBy": True,
    "cleanupPeriodDays": 30,
}


def write_settings_json(claude_dir: Path) -> None:
    """Write settings.json to .claude/ directory."""
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps(SETTINGS, indent=2))
