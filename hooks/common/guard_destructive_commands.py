#!/usr/bin/env python3
"""PreToolUse hook for Bash and PowerShell.

Asks for confirmation before genuinely destructive commands, even if a
permission rule would otherwise auto-allow them. Pure Python, no LLM call,
so it costs zero tokens to run. Both tools pass the shell command as
tool_input.command, so one script covers both.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import read_hook_input, write_hook_output

DANGEROUS = [
    re.compile(r"\brm\s+-rf\s+/(?:\s|$)"),
    re.compile(r"\bgit\s+push\b.*--force\b"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bgit\s+clean\s+-[a-z]*f"),
    re.compile(r"\bremove-item\b.*-recurse\b", re.IGNORECASE),
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
]


def main() -> None:
    data = read_hook_input()
    command = data.get("tool_input", {}).get("command", "")
    hit = next((p for p in DANGEROUS if p.search(command)), None)
    if hit is None:
        return
    write_hook_output({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"Matched destructive-command pattern: {hit.pattern}",
        }
    })


if __name__ == "__main__":
    main()
